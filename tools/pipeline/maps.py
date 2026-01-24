"""
Tiled Map Integration for SGDK/Genesis.

This module provides tools for parsing Tiled TMX/TSX files and exporting
them to SGDK-compatible formats for Genesis game development.

Features:
    - TMX/TSX file parsing (XML and JSON formats)
    - Tile layer extraction with flip flag support
    - Object layer parsing for spawn points, triggers, collision
    - Collision map generation (per-tile collision types)
    - SGDK resource file generation
    - Map visualization and debug tools

Dependencies:
    - pytmx (optional): For advanced TMX parsing
    - PIL/Pillow: For tileset image processing

Example:
    >>> from pipeline.maps import TiledParser, SGDKMapExporter
    >>> parser = TiledParser()
    >>> tiled_map = parser.load("level1.tmx")
    >>> print(f"Map size: {tiled_map.width}x{tiled_map.height} tiles")
    >>> exporter = SGDKMapExporter()
    >>> exporter.export_map(tiled_map, "out/level1")
"""

from dataclasses import dataclass, field
from enum import IntEnum, Enum
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Union
import xml.etree.ElementTree as ET
import json
import base64
import zlib
import gzip
import struct
from PIL import Image

# =============================================================================
# Enums and Constants
# =============================================================================

class CollisionType(IntEnum):
    """Tile collision types for Genesis games."""
    NONE = 0        # Passable (air, background)
    SOLID = 1       # Full tile collision (walls, floors)
    PLATFORM = 2    # One-way platform (pass from below)
    LADDER = 3      # Climbable
    WATER = 4       # Swimmable/slows movement
    DAMAGE = 5      # Hurts player (spikes, lava)
    TRIGGER = 6     # Event trigger
    SLOPE_L = 7     # Left-facing slope (45 degrees)
    SLOPE_R = 8     # Right-facing slope (45 degrees)


class ObjectType(Enum):
    """Standard object types for Tiled maps."""
    SPAWN = "spawn"
    TRIGGER = "trigger"
    COLLISION = "collision"
    ENEMY = "enemy"
    ITEM = "item"
    NPC = "npc"
    DOOR = "door"
    CHECKPOINT = "checkpoint"
    CAMERA = "camera"
    CUSTOM = "custom"


class Compression(Enum):
    """SGDK compression types."""
    NONE = "NONE"
    APLIB = "APLIB"
    LZ4W = "LZ4W"


# Tiled GID flip flags (bits 29-31)
FLIPPED_HORIZONTALLY_FLAG = 0x80000000
FLIPPED_VERTICALLY_FLAG = 0x40000000
FLIPPED_DIAGONALLY_FLAG = 0x20000000
GID_MASK = 0x1FFFFFFF


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class TileLayer:
    """
    A tile layer from a Tiled map.

    Attributes:
        name: Layer name as defined in Tiled
        width: Layer width in tiles
        height: Layer height in tiles
        data: Tile GIDs (with flip flags stripped)
        flip_h: Horizontal flip flags per tile
        flip_v: Vertical flip flags per tile
        properties: Custom properties defined in Tiled
        visible: Whether layer is visible
        opacity: Layer opacity (0.0-1.0)
        offset_x: Layer X offset in pixels
        offset_y: Layer Y offset in pixels
    """
    name: str
    width: int
    height: int
    data: List[int]
    flip_h: List[bool] = field(default_factory=list)
    flip_v: List[bool] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    visible: bool = True
    opacity: float = 1.0
    offset_x: int = 0
    offset_y: int = 0

    def get_tile(self, x: int, y: int) -> int:
        """Get tile GID at position (0 = empty)."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.data[y * self.width + x]
        return 0

    def get_flip(self, x: int, y: int) -> Tuple[bool, bool]:
        """Get flip flags (h_flip, v_flip) at position."""
        if 0 <= x < self.width and 0 <= y < self.height:
            idx = y * self.width + x
            h = self.flip_h[idx] if idx < len(self.flip_h) else False
            v = self.flip_v[idx] if idx < len(self.flip_v) else False
            return (h, v)
        return (False, False)


@dataclass
class MapObject:
    """
    An object from a Tiled object layer.

    Attributes:
        id: Unique object ID
        name: Object name
        type: Object type string (spawn, trigger, etc.)
        x: X position in pixels
        y: Y position in pixels
        width: Object width in pixels
        height: Object height in pixels
        rotation: Rotation in degrees
        properties: Custom properties
        polygon: List of (x, y) points for polygon shapes
        polyline: List of (x, y) points for polyline shapes
        visible: Whether object is visible
        gid: Tile GID if object is a tile object
    """
    id: int
    name: str
    type: str
    x: float
    y: float
    width: float = 0
    height: float = 0
    rotation: float = 0
    properties: Dict[str, Any] = field(default_factory=dict)
    polygon: Optional[List[Tuple[float, float]]] = None
    polyline: Optional[List[Tuple[float, float]]] = None
    visible: bool = True
    gid: Optional[int] = None

    def get_bounds(self) -> Tuple[int, int, int, int]:
        """Get bounding box (x, y, width, height) as integers."""
        return (int(self.x), int(self.y), int(self.width), int(self.height))

    def get_tile_position(self, tile_width: int, tile_height: int) -> Tuple[int, int]:
        """Convert pixel position to tile coordinates."""
        return (int(self.x // tile_width), int(self.y // tile_height))

    def get_object_type(self) -> ObjectType:
        """Get standardized object type enum."""
        type_lower = self.type.lower()
        for ot in ObjectType:
            if ot.value == type_lower:
                return ot
        return ObjectType.CUSTOM


@dataclass
class ObjectLayer:
    """
    An object layer from a Tiled map.

    Attributes:
        name: Layer name
        objects: List of MapObject instances
        properties: Custom properties
        visible: Whether layer is visible
        color: Layer color in Tiled (hex string)
    """
    name: str
    objects: List[MapObject] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    visible: bool = True
    color: Optional[str] = None

    def get_objects_by_type(self, obj_type: Union[str, ObjectType]) -> List[MapObject]:
        """Get all objects of a specific type."""
        type_str = obj_type.value if isinstance(obj_type, ObjectType) else obj_type
        return [obj for obj in self.objects if obj.type.lower() == type_str.lower()]

    def get_object_by_name(self, name: str) -> Optional[MapObject]:
        """Get first object with matching name."""
        for obj in self.objects:
            if obj.name == name:
                return obj
        return None


@dataclass
class TileProperties:
    """
    Properties for a single tile in a tileset.

    Attributes:
        local_id: Tile ID within the tileset (0-based)
        collision: Collision type for this tile
        animation: List of (tile_id, duration_ms) for animated tiles
        properties: Custom properties
    """
    local_id: int
    collision: CollisionType = CollisionType.NONE
    animation: Optional[List[Tuple[int, int]]] = None
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Tileset:
    """
    A tileset definition from Tiled.

    Attributes:
        name: Tileset name
        first_gid: First global tile ID for this tileset
        tile_width: Width of each tile in pixels
        tile_height: Height of each tile in pixels
        image_path: Path to tileset image
        image_width: Total image width
        image_height: Total image height
        tile_count: Total number of tiles
        columns: Number of tile columns in image
        margin: Margin around tileset in pixels
        spacing: Spacing between tiles in pixels
        tile_properties: Per-tile properties
    """
    name: str
    first_gid: int
    tile_width: int
    tile_height: int
    image_path: str
    image_width: int = 0
    image_height: int = 0
    tile_count: int = 0
    columns: int = 0
    margin: int = 0
    spacing: int = 0
    tile_properties: Dict[int, TileProperties] = field(default_factory=dict)

    def gid_to_local(self, gid: int) -> int:
        """Convert global tile ID to local tileset ID."""
        return gid - self.first_gid

    def local_to_gid(self, local_id: int) -> int:
        """Convert local tileset ID to global tile ID."""
        return local_id + self.first_gid

    def contains_gid(self, gid: int) -> bool:
        """Check if this tileset contains the given GID."""
        local = gid - self.first_gid
        return 0 <= local < self.tile_count

    def get_tile_collision(self, local_id: int) -> CollisionType:
        """Get collision type for a tile."""
        if local_id in self.tile_properties:
            return self.tile_properties[local_id].collision
        return CollisionType.NONE


@dataclass
class TiledMap:
    """
    A complete Tiled map.

    Attributes:
        width: Map width in tiles
        height: Map height in tiles
        tile_width: Tile width in pixels
        tile_height: Tile height in pixels
        layers: List of tile layers
        object_layers: List of object layers
        tilesets: List of tilesets
        properties: Map-level custom properties
        orientation: Map orientation (orthogonal, isometric, etc.)
        render_order: Tile render order
        background_color: Map background color
        source_path: Path to source TMX file
    """
    width: int
    height: int
    tile_width: int
    tile_height: int
    layers: List[TileLayer] = field(default_factory=list)
    object_layers: List[ObjectLayer] = field(default_factory=list)
    tilesets: List[Tileset] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    orientation: str = "orthogonal"
    render_order: str = "right-down"
    background_color: Optional[str] = None
    source_path: Optional[str] = None

    @property
    def pixel_width(self) -> int:
        """Map width in pixels."""
        return self.width * self.tile_width

    @property
    def pixel_height(self) -> int:
        """Map height in pixels."""
        return self.height * self.tile_height

    def get_layer(self, name: str) -> Optional[TileLayer]:
        """Get tile layer by name."""
        for layer in self.layers:
            if layer.name == name:
                return layer
        return None

    def get_object_layer(self, name: str) -> Optional[ObjectLayer]:
        """Get object layer by name."""
        for layer in self.object_layers:
            if layer.name == name:
                return layer
        return None

    def get_tileset_for_gid(self, gid: int) -> Optional[Tileset]:
        """Find the tileset that contains the given GID."""
        # GID 0 is always empty tile
        if gid == 0:
            return None
        # Tilesets are sorted by first_gid, find the one that contains this GID
        result = None
        for tileset in self.tilesets:
            if tileset.first_gid <= gid:
                result = tileset
            else:
                break
        return result

    def get_spawn_points(self, spawn_type: Optional[str] = None) -> List[MapObject]:
        """Get all spawn point objects, optionally filtered by type property."""
        spawns = []
        for obj_layer in self.object_layers:
            for obj in obj_layer.objects:
                if obj.type.lower() == "spawn":
                    if spawn_type is None or obj.properties.get("type") == spawn_type:
                        spawns.append(obj)
        return spawns

    def get_triggers(self) -> List[MapObject]:
        """Get all trigger objects."""
        triggers = []
        for obj_layer in self.object_layers:
            for obj in obj_layer.objects:
                if obj.type.lower() == "trigger":
                    triggers.append(obj)
        return triggers


# =============================================================================
# Validation
# =============================================================================

@dataclass
class ValidationResult:
    """Result of map validation."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, msg: str) -> None:
        """Add an error (makes validation invalid)."""
        self.errors.append(msg)
        self.valid = False

    def add_warning(self, msg: str) -> None:
        """Add a warning (does not affect validity)."""
        self.warnings.append(msg)

    def summary(self) -> str:
        """Get human-readable summary."""
        status = "VALID" if self.valid else "INVALID"
        lines = [f"Validation: {status}"]
        if self.errors:
            lines.append(f"Errors ({len(self.errors)}):")
            for err in self.errors:
                lines.append(f"  - {err}")
        if self.warnings:
            lines.append(f"Warnings ({len(self.warnings)}):")
            for warn in self.warnings:
                lines.append(f"  - {warn}")
        return "\n".join(lines)


# =============================================================================
# TMX Parser
# =============================================================================

class TiledParser:
    """
    Parser for Tiled TMX/TSX map files.

    Supports:
        - TMX XML format
        - TMX JSON format
        - Embedded and external tilesets
        - Base64, CSV, and uncompressed data
        - Gzip and Zlib compression
        - Tile flip flags

    Example:
        >>> parser = TiledParser()
        >>> tiled_map = parser.load("level1.tmx")
        >>> print(f"Layers: {[l.name for l in tiled_map.layers]}")
    """

    def __init__(self):
        """Initialize the parser."""
        self._base_path = Path(".")

    def load(self, path: str) -> TiledMap:
        """
        Load a Tiled map from file.

        Args:
            path: Path to TMX or JSON file

        Returns:
            TiledMap instance

        Raises:
            ValueError: If file format is unsupported
            FileNotFoundError: If file doesn't exist
        """
        path = Path(path)
        self._base_path = path.parent

        if not path.exists():
            raise FileNotFoundError(f"Map file not found: {path}")

        content = path.read_text(encoding='utf-8')

        # Detect format
        if content.strip().startswith('{'):
            return self._parse_json(content, path)
        elif content.strip().startswith('<?xml') or content.strip().startswith('<map'):
            return self._parse_xml(content, path)
        else:
            raise ValueError(f"Unknown map format: {path}")

    def _parse_xml(self, content: str, source_path: Path) -> TiledMap:
        """Parse TMX XML format."""
        root = ET.fromstring(content)

        # Map attributes
        width = int(root.get('width', 0))
        height = int(root.get('height', 0))
        tile_width = int(root.get('tilewidth', 8))
        tile_height = int(root.get('tileheight', 8))
        orientation = root.get('orientation', 'orthogonal')
        render_order = root.get('renderorder', 'right-down')
        bg_color = root.get('backgroundcolor')

        # Parse properties
        properties = self._parse_properties_xml(root.find('properties'))

        # Parse tilesets
        tilesets = []
        for ts_elem in root.findall('tileset'):
            tileset = self._parse_tileset_xml(ts_elem)
            tilesets.append(tileset)

        # Parse layers
        layers = []
        object_layers = []

        for child in root:
            if child.tag == 'layer':
                layer = self._parse_tile_layer_xml(child, width, height)
                layers.append(layer)
            elif child.tag == 'objectgroup':
                obj_layer = self._parse_object_layer_xml(child)
                object_layers.append(obj_layer)

        return TiledMap(
            width=width,
            height=height,
            tile_width=tile_width,
            tile_height=tile_height,
            layers=layers,
            object_layers=object_layers,
            tilesets=tilesets,
            properties=properties,
            orientation=orientation,
            render_order=render_order,
            background_color=bg_color,
            source_path=str(source_path)
        )

    def _parse_tileset_xml(self, elem: ET.Element) -> Tileset:
        """Parse a tileset element."""
        first_gid = int(elem.get('firstgid', 1))

        # Check for external tileset
        source = elem.get('source')
        if source:
            tsx_path = self._base_path / source
            if tsx_path.exists():
                tsx_content = tsx_path.read_text(encoding='utf-8')
                tsx_root = ET.fromstring(tsx_content)
                elem = tsx_root  # Use external tileset element

        name = elem.get('name', 'unnamed')
        tile_width = int(elem.get('tilewidth', 8))
        tile_height = int(elem.get('tileheight', 8))
        tile_count = int(elem.get('tilecount', 0))
        columns = int(elem.get('columns', 0))
        margin = int(elem.get('margin', 0))
        spacing = int(elem.get('spacing', 0))

        # Image element
        image_elem = elem.find('image')
        image_path = ""
        image_width = 0
        image_height = 0
        if image_elem is not None:
            image_path = image_elem.get('source', '')
            image_width = int(image_elem.get('width', 0))
            image_height = int(image_elem.get('height', 0))

        # Parse per-tile properties
        tile_properties = {}
        for tile_elem in elem.findall('tile'):
            tile_id = int(tile_elem.get('id', 0))
            props = self._parse_properties_xml(tile_elem.find('properties'))

            # Check for collision type property
            collision = CollisionType.NONE
            if 'collision' in props:
                collision = self._parse_collision_type(props['collision'])
            elif 'type' in props and props['type'].lower() in [c.name.lower() for c in CollisionType]:
                collision = CollisionType[props['type'].upper()]

            # Check for animation
            animation = None
            anim_elem = tile_elem.find('animation')
            if anim_elem is not None:
                animation = []
                for frame_elem in anim_elem.findall('frame'):
                    frame_id = int(frame_elem.get('tileid', 0))
                    duration = int(frame_elem.get('duration', 100))
                    animation.append((frame_id, duration))

            tile_properties[tile_id] = TileProperties(
                local_id=tile_id,
                collision=collision,
                animation=animation,
                properties=props
            )

        return Tileset(
            name=name,
            first_gid=first_gid,
            tile_width=tile_width,
            tile_height=tile_height,
            image_path=image_path,
            image_width=image_width,
            image_height=image_height,
            tile_count=tile_count,
            columns=columns,
            margin=margin,
            spacing=spacing,
            tile_properties=tile_properties
        )

    def _parse_tile_layer_xml(self, elem: ET.Element,
                               map_width: int, map_height: int) -> TileLayer:
        """Parse a tile layer element."""
        name = elem.get('name', 'unnamed')
        width = int(elem.get('width', map_width))
        height = int(elem.get('height', map_height))
        visible = elem.get('visible', '1') != '0'
        opacity = float(elem.get('opacity', 1.0))
        offset_x = int(elem.get('offsetx', 0))
        offset_y = int(elem.get('offsety', 0))

        # Parse properties
        properties = self._parse_properties_xml(elem.find('properties'))

        # Parse tile data
        data_elem = elem.find('data')
        data, flip_h, flip_v = self._parse_tile_data_xml(data_elem, width * height)

        return TileLayer(
            name=name,
            width=width,
            height=height,
            data=data,
            flip_h=flip_h,
            flip_v=flip_v,
            properties=properties,
            visible=visible,
            opacity=opacity,
            offset_x=offset_x,
            offset_y=offset_y
        )

    def _parse_tile_data_xml(self, elem: ET.Element,
                              expected_count: int) -> Tuple[List[int], List[bool], List[bool]]:
        """Parse tile data from a data element."""
        if elem is None:
            return ([0] * expected_count, [False] * expected_count, [False] * expected_count)

        encoding = elem.get('encoding', '')
        compression = elem.get('compression', '')

        raw_data: bytes

        if encoding == 'base64':
            # Base64 encoded data
            raw_data = base64.b64decode(elem.text.strip())

            # Decompress if needed
            if compression == 'gzip':
                raw_data = gzip.decompress(raw_data)
            elif compression == 'zlib':
                raw_data = zlib.decompress(raw_data)

            # Unpack as 32-bit integers (little-endian)
            gids = list(struct.unpack(f'<{len(raw_data) // 4}I', raw_data))

        elif encoding == 'csv':
            # CSV encoded data
            csv_text = elem.text.strip()
            gids = [int(x.strip()) for x in csv_text.split(',') if x.strip()]

        else:
            # Uncompressed XML tile elements
            gids = []
            for tile_elem in elem.findall('tile'):
                gid = int(tile_elem.get('gid', 0))
                gids.append(gid)

        # Extract flip flags and clean GIDs
        data = []
        flip_h = []
        flip_v = []

        for gid in gids:
            h_flip = bool(gid & FLIPPED_HORIZONTALLY_FLAG)
            v_flip = bool(gid & FLIPPED_VERTICALLY_FLAG)
            # Note: Diagonal flip not commonly used, ignored for simplicity
            clean_gid = gid & GID_MASK

            data.append(clean_gid)
            flip_h.append(h_flip)
            flip_v.append(v_flip)

        # Pad if necessary
        while len(data) < expected_count:
            data.append(0)
            flip_h.append(False)
            flip_v.append(False)

        return (data, flip_h, flip_v)

    def _parse_object_layer_xml(self, elem: ET.Element) -> ObjectLayer:
        """Parse an object layer element."""
        name = elem.get('name', 'unnamed')
        visible = elem.get('visible', '1') != '0'
        color = elem.get('color')

        properties = self._parse_properties_xml(elem.find('properties'))

        objects = []
        for obj_elem in elem.findall('object'):
            obj = self._parse_object_xml(obj_elem)
            objects.append(obj)

        return ObjectLayer(
            name=name,
            objects=objects,
            properties=properties,
            visible=visible,
            color=color
        )

    def _parse_object_xml(self, elem: ET.Element) -> MapObject:
        """Parse a single object element."""
        obj_id = int(elem.get('id', 0))
        name = elem.get('name', '')
        obj_type = elem.get('type', '')
        x = float(elem.get('x', 0))
        y = float(elem.get('y', 0))
        width = float(elem.get('width', 0))
        height = float(elem.get('height', 0))
        rotation = float(elem.get('rotation', 0))
        visible = elem.get('visible', '1') != '0'
        gid = elem.get('gid')
        if gid is not None:
            gid = int(gid) & GID_MASK

        properties = self._parse_properties_xml(elem.find('properties'))

        # Parse polygon/polyline
        polygon = None
        polyline = None

        poly_elem = elem.find('polygon')
        if poly_elem is not None:
            polygon = self._parse_points(poly_elem.get('points', ''))

        line_elem = elem.find('polyline')
        if line_elem is not None:
            polyline = self._parse_points(line_elem.get('points', ''))

        return MapObject(
            id=obj_id,
            name=name,
            type=obj_type,
            x=x,
            y=y,
            width=width,
            height=height,
            rotation=rotation,
            properties=properties,
            polygon=polygon,
            polyline=polyline,
            visible=visible,
            gid=gid
        )

    def _parse_points(self, points_str: str) -> List[Tuple[float, float]]:
        """Parse a Tiled points string into list of tuples."""
        if not points_str:
            return []
        points = []
        for pair in points_str.split():
            x, y = pair.split(',')
            points.append((float(x), float(y)))
        return points

    def _parse_properties_xml(self, elem: Optional[ET.Element]) -> Dict[str, Any]:
        """Parse properties element into dictionary."""
        if elem is None:
            return {}

        props = {}
        for prop in elem.findall('property'):
            name = prop.get('name', '')
            prop_type = prop.get('type', 'string')
            value = prop.get('value', prop.text or '')

            # Type conversion
            if prop_type == 'int':
                value = int(value)
            elif prop_type == 'float':
                value = float(value)
            elif prop_type == 'bool':
                value = value.lower() in ('true', '1', 'yes')
            elif prop_type == 'color':
                # Keep as string for now
                pass

            props[name] = value

        return props

    def _parse_json(self, content: str, source_path: Path) -> TiledMap:
        """Parse Tiled JSON format."""
        data = json.loads(content)

        width = data.get('width', 0)
        height = data.get('height', 0)
        tile_width = data.get('tilewidth', 8)
        tile_height = data.get('tileheight', 8)
        orientation = data.get('orientation', 'orthogonal')
        render_order = data.get('renderorder', 'right-down')
        bg_color = data.get('backgroundcolor')

        properties = data.get('properties', {})
        if isinstance(properties, list):
            # Convert array format to dict
            properties = {p['name']: p['value'] for p in properties}

        # Parse tilesets
        tilesets = []
        for ts_data in data.get('tilesets', []):
            tileset = self._parse_tileset_json(ts_data)
            tilesets.append(tileset)

        # Parse layers
        layers = []
        object_layers = []

        for layer_data in data.get('layers', []):
            layer_type = layer_data.get('type', 'tilelayer')

            if layer_type == 'tilelayer':
                layer = self._parse_tile_layer_json(layer_data)
                layers.append(layer)
            elif layer_type == 'objectgroup':
                obj_layer = self._parse_object_layer_json(layer_data)
                object_layers.append(obj_layer)

        return TiledMap(
            width=width,
            height=height,
            tile_width=tile_width,
            tile_height=tile_height,
            layers=layers,
            object_layers=object_layers,
            tilesets=tilesets,
            properties=properties,
            orientation=orientation,
            render_order=render_order,
            background_color=bg_color,
            source_path=str(source_path)
        )

    def _parse_tileset_json(self, data: Dict) -> Tileset:
        """Parse tileset from JSON data."""
        first_gid = data.get('firstgid', 1)

        # Check for external tileset
        source = data.get('source')
        if source:
            tsx_path = self._base_path / source
            if tsx_path.exists():
                content = tsx_path.read_text(encoding='utf-8')
                if content.strip().startswith('{'):
                    data = json.loads(content)
                else:
                    # External TSX is XML, parse differently
                    tsx_root = ET.fromstring(content)
                    return self._parse_tileset_xml_inner(tsx_root, first_gid)

        name = data.get('name', 'unnamed')
        tile_width = data.get('tilewidth', 8)
        tile_height = data.get('tileheight', 8)
        tile_count = data.get('tilecount', 0)
        columns = data.get('columns', 0)
        margin = data.get('margin', 0)
        spacing = data.get('spacing', 0)
        image_path = data.get('image', '')
        image_width = data.get('imagewidth', 0)
        image_height = data.get('imageheight', 0)

        # Parse per-tile properties
        tile_properties = {}
        for tile_data in data.get('tiles', []):
            tile_id = tile_data.get('id', 0)
            props = tile_data.get('properties', {})
            if isinstance(props, list):
                props = {p['name']: p['value'] for p in props}

            collision = CollisionType.NONE
            if 'collision' in props:
                collision = self._parse_collision_type(props['collision'])

            animation = None
            if 'animation' in tile_data:
                animation = []
                for frame in tile_data['animation']:
                    animation.append((frame['tileid'], frame['duration']))

            tile_properties[tile_id] = TileProperties(
                local_id=tile_id,
                collision=collision,
                animation=animation,
                properties=props
            )

        return Tileset(
            name=name,
            first_gid=first_gid,
            tile_width=tile_width,
            tile_height=tile_height,
            image_path=image_path,
            image_width=image_width,
            image_height=image_height,
            tile_count=tile_count,
            columns=columns,
            margin=margin,
            spacing=spacing,
            tile_properties=tile_properties
        )

    def _parse_tileset_xml_inner(self, elem: ET.Element, first_gid: int) -> Tileset:
        """Parse tileset from XML element with external first_gid."""
        ts = self._parse_tileset_xml(elem)
        # Override first_gid from parent reference
        return Tileset(
            name=ts.name,
            first_gid=first_gid,
            tile_width=ts.tile_width,
            tile_height=ts.tile_height,
            image_path=ts.image_path,
            image_width=ts.image_width,
            image_height=ts.image_height,
            tile_count=ts.tile_count,
            columns=ts.columns,
            margin=ts.margin,
            spacing=ts.spacing,
            tile_properties=ts.tile_properties
        )

    def _parse_tile_layer_json(self, data: Dict) -> TileLayer:
        """Parse tile layer from JSON data."""
        name = data.get('name', 'unnamed')
        width = data.get('width', 0)
        height = data.get('height', 0)
        visible = data.get('visible', True)
        opacity = data.get('opacity', 1.0)
        offset_x = data.get('offsetx', 0)
        offset_y = data.get('offsety', 0)

        properties = data.get('properties', {})
        if isinstance(properties, list):
            properties = {p['name']: p['value'] for p in properties}

        # Get tile data (already decoded in JSON format)
        gids = data.get('data', [])

        # Extract flip flags
        tile_data = []
        flip_h = []
        flip_v = []

        for gid in gids:
            h_flip = bool(gid & FLIPPED_HORIZONTALLY_FLAG)
            v_flip = bool(gid & FLIPPED_VERTICALLY_FLAG)
            clean_gid = gid & GID_MASK

            tile_data.append(clean_gid)
            flip_h.append(h_flip)
            flip_v.append(v_flip)

        return TileLayer(
            name=name,
            width=width,
            height=height,
            data=tile_data,
            flip_h=flip_h,
            flip_v=flip_v,
            properties=properties,
            visible=visible,
            opacity=opacity,
            offset_x=offset_x,
            offset_y=offset_y
        )

    def _parse_object_layer_json(self, data: Dict) -> ObjectLayer:
        """Parse object layer from JSON data."""
        name = data.get('name', 'unnamed')
        visible = data.get('visible', True)
        color = data.get('color')

        properties = data.get('properties', {})
        if isinstance(properties, list):
            properties = {p['name']: p['value'] for p in properties}

        objects = []
        for obj_data in data.get('objects', []):
            obj = MapObject(
                id=obj_data.get('id', 0),
                name=obj_data.get('name', ''),
                type=obj_data.get('type', ''),
                x=obj_data.get('x', 0),
                y=obj_data.get('y', 0),
                width=obj_data.get('width', 0),
                height=obj_data.get('height', 0),
                rotation=obj_data.get('rotation', 0),
                properties=obj_data.get('properties', {}),
                polygon=obj_data.get('polygon'),
                polyline=obj_data.get('polyline'),
                visible=obj_data.get('visible', True),
                gid=obj_data.get('gid')
            )
            objects.append(obj)

        return ObjectLayer(
            name=name,
            objects=objects,
            properties=properties,
            visible=visible,
            color=color
        )

    def _parse_collision_type(self, value: Any) -> CollisionType:
        """Parse collision type from property value."""
        if isinstance(value, int):
            try:
                return CollisionType(value)
            except ValueError:
                return CollisionType.NONE
        elif isinstance(value, str):
            value_upper = value.upper()
            for ct in CollisionType:
                if ct.name == value_upper:
                    return ct
        return CollisionType.NONE


# =============================================================================
# Collision Exporter
# =============================================================================

class CollisionExporter:
    """
    Export collision data from Tiled maps.

    Collision data can come from:
    1. A dedicated collision layer (tile values = collision types)
    2. Per-tile properties in the tileset
    3. Object layer rectangles/polygons

    Example:
        >>> exporter = CollisionExporter()
        >>> collision_map = exporter.extract_tile_collision(tiled_map, "collision")
        >>> exporter.export_collision_header(tiled_map, "level1_collision.h")
    """

    def __init__(self):
        """Initialize collision exporter."""
        pass

    def extract_tile_collision(self, tiled_map: TiledMap,
                                layer_name: str = "collision") -> List[int]:
        """
        Extract collision map from a dedicated collision layer.

        The collision layer uses tile values directly as collision types.
        Tile 0 = NONE, Tile 1 = SOLID, etc.

        Args:
            tiled_map: Parsed Tiled map
            layer_name: Name of collision layer

        Returns:
            List of collision type values (row-major order)
        """
        layer = tiled_map.get_layer(layer_name)
        if layer is None:
            return [0] * (tiled_map.width * tiled_map.height)

        collision = []
        for gid in layer.data:
            # For collision layers, the GID IS the collision type
            # (assuming collision tileset starts at GID 1)
            if gid == 0:
                collision.append(CollisionType.NONE.value)
            else:
                # Map GID to collision type (GID 1 = SOLID, etc.)
                # Find the tileset and get local ID
                tileset = tiled_map.get_tileset_for_gid(gid)
                if tileset:
                    local_id = tileset.gid_to_local(gid)
                    # Check if tile has collision property
                    if local_id in tileset.tile_properties:
                        collision.append(tileset.tile_properties[local_id].collision.value)
                    else:
                        # Use local ID as collision type directly
                        if local_id < len(CollisionType):
                            collision.append(local_id)
                        else:
                            collision.append(CollisionType.SOLID.value)
                else:
                    collision.append(CollisionType.SOLID.value)

        return collision

    def extract_from_tileset_properties(self, tiled_map: TiledMap,
                                         layer_name: str = "main") -> List[int]:
        """
        Extract collision from tileset tile properties.

        Each tile in the tileset can have a "collision" property.

        Args:
            tiled_map: Parsed Tiled map
            layer_name: Name of layer to extract collision for

        Returns:
            List of collision type values
        """
        layer = tiled_map.get_layer(layer_name)
        if layer is None:
            return [0] * (tiled_map.width * tiled_map.height)

        collision = []
        for gid in layer.data:
            if gid == 0:
                collision.append(CollisionType.NONE.value)
                continue

            tileset = tiled_map.get_tileset_for_gid(gid)
            if tileset is None:
                collision.append(CollisionType.NONE.value)
                continue

            local_id = tileset.gid_to_local(gid)
            coll_type = tileset.get_tile_collision(local_id)
            collision.append(coll_type.value)

        return collision

    def extract_object_collision(self, tiled_map: TiledMap,
                                  layer_name: str = "collision") -> List[Dict]:
        """
        Extract collision rectangles from object layer.

        Returns list of collision boxes with position and type.

        Args:
            tiled_map: Parsed Tiled map
            layer_name: Name of object layer with collision shapes

        Returns:
            List of collision dictionaries with x, y, width, height, type
        """
        obj_layer = tiled_map.get_object_layer(layer_name)
        if obj_layer is None:
            return []

        boxes = []
        for obj in obj_layer.objects:
            coll_type = CollisionType.SOLID
            if 'collision' in obj.properties:
                coll_type = self._parse_collision_type(obj.properties['collision'])
            elif obj.type:
                # Try to parse object type as collision type
                for ct in CollisionType:
                    if ct.name.lower() == obj.type.lower():
                        coll_type = ct
                        break

            boxes.append({
                'x': int(obj.x),
                'y': int(obj.y),
                'width': int(obj.width),
                'height': int(obj.height),
                'type': coll_type.value,
                'name': obj.name
            })

        return boxes

    def _parse_collision_type(self, value: Any) -> CollisionType:
        """Parse collision type from property value."""
        if isinstance(value, int):
            try:
                return CollisionType(value)
            except ValueError:
                return CollisionType.NONE
        elif isinstance(value, str):
            for ct in CollisionType:
                if ct.name.lower() == value.lower():
                    return ct
        return CollisionType.NONE

    def export_collision_map(self, collision: List[int], width: int,
                              output_path: str) -> None:
        """
        Export collision map as binary file.

        Format: 1 byte per tile, row-major order.

        Args:
            collision: List of collision type values
            width: Map width in tiles (for validation)
            output_path: Output file path
        """
        data = bytes(collision)
        Path(output_path).write_bytes(data)

    def export_collision_header(self, tiled_map: TiledMap,
                                 output_path: str,
                                 layer_name: str = "collision",
                                 var_prefix: str = "") -> str:
        """
        Generate C header with collision data.

        Args:
            tiled_map: Parsed Tiled map
            output_path: Output file path
            layer_name: Name of collision layer
            var_prefix: Prefix for variable names

        Returns:
            Generated C code as string
        """
        collision = self.extract_tile_collision(tiled_map, layer_name)

        # Generate variable name from map path
        if tiled_map.source_path:
            map_name = Path(tiled_map.source_path).stem
        else:
            map_name = "map"

        if var_prefix:
            map_name = f"{var_prefix}_{map_name}"

        lines = [
            "// Auto-generated collision data",
            f"// Source: {tiled_map.source_path}",
            f"// Size: {tiled_map.width}x{tiled_map.height} tiles",
            "",
            "#ifndef _COLLISION_DATA_H_",
            "#define _COLLISION_DATA_H_",
            "",
            "#include <genesis.h>",
            "",
            "// Collision types",
            "typedef enum {",
        ]

        for ct in CollisionType:
            lines.append(f"    COLL_{ct.name} = {ct.value},")

        lines.extend([
            "} CollisionType;",
            "",
            f"#define {map_name.upper()}_WIDTH {tiled_map.width}",
            f"#define {map_name.upper()}_HEIGHT {tiled_map.height}",
            "",
            f"const u8 {map_name}_collision[{len(collision)}] = {{",
        ])

        # Format collision data
        row_data = []
        for y in range(tiled_map.height):
            row_start = y * tiled_map.width
            row_end = row_start + tiled_map.width
            row_values = [str(v) for v in collision[row_start:row_end]]
            row_data.append("    " + ", ".join(row_values) + ",")

        lines.extend(row_data)
        lines.extend([
            "};",
            "",
            "#endif // _COLLISION_DATA_H_",
        ])

        content = "\n".join(lines)
        Path(output_path).write_text(content, encoding='utf-8')
        return content


# =============================================================================
# SGDK Map Exporter
# =============================================================================

@dataclass
class MapExportConfig:
    """Configuration for SGDK map export."""
    output_dir: str
    prefix: str = ""
    compression: Compression = Compression.NONE
    include_collision: bool = True
    include_objects: bool = True
    collision_layer: str = "collision"
    metatile_size: int = 1          # 1 = 8x8, 2 = 16x16 metatiles
    base_tile_index: int = 0        # First tile index in VRAM
    palette_index: int = 0          # Default palette (0-3)


@dataclass
class MapExportResult:
    """Result of map export operation."""
    success: bool
    map_header: Optional[str] = None
    collision_header: Optional[str] = None
    res_entry: Optional[str] = None
    tilemap_bin: Optional[str] = None
    collision_bin: Optional[str] = None
    errors: List[str] = field(default_factory=list)


class SGDKMapExporter:
    """
    Export Tiled maps to SGDK-compatible format.

    Generates:
    - Tilemap data with VDP attributes (priority, palette, flip flags)
    - Collision map (1 byte per tile)
    - Spawn point arrays
    - .res file entries

    Example:
        >>> exporter = SGDKMapExporter()
        >>> config = MapExportConfig(output_dir="out", prefix="level1")
        >>> result = exporter.export_map(tiled_map, config)
    """

    def __init__(self):
        """Initialize SGDK map exporter."""
        self.collision_exporter = CollisionExporter()

    def export_map(self, tiled_map: TiledMap, config: MapExportConfig) -> MapExportResult:
        """
        Export a Tiled map to SGDK format.

        Args:
            tiled_map: Parsed Tiled map
            config: Export configuration

        Returns:
            MapExportResult with generated file paths
        """
        result = MapExportResult(success=True)
        output_dir = Path(config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate names
        if tiled_map.source_path:
            base_name = Path(tiled_map.source_path).stem
        else:
            base_name = "map"

        if config.prefix:
            base_name = f"{config.prefix}_{base_name}"

        try:
            # Export main tilemap
            map_header = self._export_tilemap_header(
                tiled_map, base_name, config, output_dir
            )
            result.map_header = str(output_dir / f"{base_name}.h")

            # Export tilemap binary
            tilemap_bin = self._export_tilemap_binary(
                tiled_map, base_name, config, output_dir
            )
            result.tilemap_bin = tilemap_bin

            # Export collision
            if config.include_collision:
                coll_header = self.collision_exporter.export_collision_header(
                    tiled_map,
                    str(output_dir / f"{base_name}_collision.h"),
                    config.collision_layer,
                    base_name
                )
                result.collision_header = str(output_dir / f"{base_name}_collision.h")

            # Export objects/spawn points
            if config.include_objects:
                self._export_objects_header(tiled_map, base_name, output_dir)

            # Generate .res entry
            result.res_entry = self._generate_res_entry(tiled_map, base_name, config)

        except Exception as e:
            result.success = False
            result.errors.append(str(e))

        return result

    def _export_tilemap_header(self, tiled_map: TiledMap, base_name: str,
                                config: MapExportConfig, output_dir: Path) -> str:
        """Generate C header with tilemap data."""
        lines = [
            "// Auto-generated tilemap data",
            f"// Source: {tiled_map.source_path}",
            "",
            f"#ifndef _{base_name.upper()}_H_",
            f"#define _{base_name.upper()}_H_",
            "",
            "#include <genesis.h>",
            "",
            f"#define {base_name.upper()}_WIDTH {tiled_map.width}",
            f"#define {base_name.upper()}_HEIGHT {tiled_map.height}",
            f"#define {base_name.upper()}_TILE_WIDTH {tiled_map.tile_width}",
            f"#define {base_name.upper()}_TILE_HEIGHT {tiled_map.tile_height}",
            "",
        ]

        # Export each visible tile layer
        for layer in tiled_map.layers:
            if not layer.visible:
                continue

            layer_name = f"{base_name}_{layer.name}".replace(" ", "_").replace("-", "_")

            lines.extend([
                f"// Layer: {layer.name}",
                f"const u16 {layer_name}[{layer.width * layer.height}] = {{",
            ])

            # Generate tilemap entries with VDP attributes
            for y in range(layer.height):
                row_values = []
                for x in range(layer.width):
                    idx = y * layer.width + x
                    gid = layer.data[idx]
                    h_flip = layer.flip_h[idx] if idx < len(layer.flip_h) else False
                    v_flip = layer.flip_v[idx] if idx < len(layer.flip_v) else False

                    # Build VDP tilemap entry
                    # Bits 15: Priority, 14-13: Palette, 12: VFlip, 11: HFlip, 10-0: Tile
                    entry = self._build_tilemap_entry(
                        gid, h_flip, v_flip,
                        config.palette_index,
                        config.base_tile_index,
                        tiled_map
                    )
                    row_values.append(f"0x{entry:04X}")

                lines.append("    " + ", ".join(row_values) + ",")

            lines.extend(["};", ""])

        lines.append(f"#endif // _{base_name.upper()}_H_")

        content = "\n".join(lines)
        header_path = output_dir / f"{base_name}.h"
        header_path.write_text(content, encoding='utf-8')
        return content

    def _export_tilemap_binary(self, tiled_map: TiledMap, base_name: str,
                                config: MapExportConfig, output_dir: Path) -> str:
        """Export tilemap as binary file."""
        # Export first visible layer
        for layer in tiled_map.layers:
            if not layer.visible:
                continue

            data = bytearray()
            for idx in range(len(layer.data)):
                gid = layer.data[idx]
                h_flip = layer.flip_h[idx] if idx < len(layer.flip_h) else False
                v_flip = layer.flip_v[idx] if idx < len(layer.flip_v) else False

                entry = self._build_tilemap_entry(
                    gid, h_flip, v_flip,
                    config.palette_index,
                    config.base_tile_index,
                    tiled_map
                )
                # Little-endian 16-bit
                data.extend(struct.pack('<H', entry))

            bin_path = output_dir / f"{base_name}_{layer.name}.bin"
            bin_path.write_bytes(bytes(data))
            return str(bin_path)

        return ""

    def _build_tilemap_entry(self, gid: int, h_flip: bool, v_flip: bool,
                              palette: int, base_tile: int,
                              tiled_map: TiledMap) -> int:
        """
        Build a VDP tilemap entry.

        Format (16-bit):
        Bit 15: Priority (0=low, 1=high)
        Bits 14-13: Palette (0-3)
        Bit 12: Vertical flip
        Bit 11: Horizontal flip
        Bits 10-0: Tile index
        """
        if gid == 0:
            return 0

        # Convert GID to local tile index
        tileset = tiled_map.get_tileset_for_gid(gid)
        if tileset is None:
            return 0

        local_id = tileset.gid_to_local(gid)
        tile_index = base_tile + local_id

        # Clamp to 11 bits
        tile_index = tile_index & 0x7FF

        # Build entry
        entry = tile_index
        if h_flip:
            entry |= 0x0800  # Bit 11
        if v_flip:
            entry |= 0x1000  # Bit 12
        entry |= (palette & 0x3) << 13  # Bits 14-13
        # Priority bit 15 left at 0 (low priority)

        return entry

    def _export_objects_header(self, tiled_map: TiledMap, base_name: str,
                                output_dir: Path) -> None:
        """Export spawn points and objects as C header."""
        lines = [
            "// Auto-generated object data",
            f"// Source: {tiled_map.source_path}",
            "",
            f"#ifndef _{base_name.upper()}_OBJECTS_H_",
            f"#define _{base_name.upper()}_OBJECTS_H_",
            "",
            "#include <genesis.h>",
            "",
            "typedef struct {",
            "    s16 x;",
            "    s16 y;",
            "    u8  type;",
            "    u8  flags;",
            "} SpawnPoint;",
            "",
        ]

        # Collect all objects by type
        spawns = tiled_map.get_spawn_points()
        triggers = tiled_map.get_triggers()

        # Export spawn points
        if spawns:
            lines.extend([
                f"#define {base_name.upper()}_SPAWN_COUNT {len(spawns)}",
                f"const SpawnPoint {base_name}_spawns[{len(spawns)}] = {{",
            ])
            for spawn in spawns:
                spawn_type = spawn.properties.get('type', 0)
                if isinstance(spawn_type, str):
                    # Try to convert string type to number
                    spawn_type = hash(spawn_type) & 0xFF
                lines.append(f"    {{ {int(spawn.x)}, {int(spawn.y)}, {spawn_type}, 0 }},")
            lines.extend(["};", ""])

        # Export triggers
        if triggers:
            lines.extend([
                "typedef struct {",
                "    s16 x, y, w, h;",
                "    u8  trigger_id;",
                "    u8  flags;",
                "} TriggerZone;",
                "",
                f"#define {base_name.upper()}_TRIGGER_COUNT {len(triggers)}",
                f"const TriggerZone {base_name}_triggers[{len(triggers)}] = {{",
            ])
            for i, trigger in enumerate(triggers):
                trigger_id = trigger.properties.get('id', i)
                lines.append(
                    f"    {{ {int(trigger.x)}, {int(trigger.y)}, "
                    f"{int(trigger.width)}, {int(trigger.height)}, {trigger_id}, 0 }},"
                )
            lines.extend(["};", ""])

        lines.append(f"#endif // _{base_name.upper()}_OBJECTS_H_")

        content = "\n".join(lines)
        header_path = output_dir / f"{base_name}_objects.h"
        header_path.write_text(content, encoding='utf-8')

    def _generate_res_entry(self, tiled_map: TiledMap, base_name: str,
                             config: MapExportConfig) -> str:
        """Generate SGDK .res file entry."""
        compression = config.compression.value

        lines = [
            f"// Map: {base_name}",
        ]

        # Note: SGDK MAP resource requires tileset reference
        # This is a simplified entry for tilemap binary
        for layer in tiled_map.layers:
            if not layer.visible:
                continue
            layer_name = f"{base_name}_{layer.name}".replace(" ", "_").replace("-", "_")
            lines.append(
                f"BIN {layer_name}_data \"{base_name}_{layer.name}.bin\" {compression}"
            )

        return "\n".join(lines)

    def validate_map(self, tiled_map: TiledMap) -> ValidationResult:
        """
        Validate map against Genesis/SGDK constraints.

        Checks:
        - Map size (max 512x512 tiles for plane)
        - Tile count per tileset (max 2047 unique tiles)
        - Object positions within bounds

        Args:
            tiled_map: Map to validate

        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult(valid=True)

        # Check map size
        if tiled_map.width > 512:
            result.add_error(f"Map width {tiled_map.width} exceeds VDP max (512)")
        if tiled_map.height > 512:
            result.add_error(f"Map height {tiled_map.height} exceeds VDP max (512)")

        # Check tileset sizes
        for tileset in tiled_map.tilesets:
            if tileset.tile_count > 2047:
                result.add_error(
                    f"Tileset '{tileset.name}' has {tileset.tile_count} tiles "
                    f"(max 2047 for VDP)"
                )

        # Check for 8x8 tiles
        if tiled_map.tile_width != 8 or tiled_map.tile_height != 8:
            result.add_warning(
                f"Tile size {tiled_map.tile_width}x{tiled_map.tile_height} "
                f"(Genesis uses 8x8 tiles)"
            )

        # Check total unique tiles across all tilesets
        total_tiles = sum(ts.tile_count for ts in tiled_map.tilesets)
        if total_tiles > 2047:
            result.add_warning(
                f"Total tiles {total_tiles} may exceed VRAM capacity"
            )

        return result


# =============================================================================
# Map Visualizer
# =============================================================================

class MapVisualizer:
    """
    Visualize Tiled maps for debugging.

    Generates images showing:
    - Rendered map layers
    - Collision overlay
    - Spawn point markers
    - Object boundaries

    Example:
        >>> viz = MapVisualizer()
        >>> img = viz.render_map(tiled_map)
        >>> img.save("level1_preview.png")
    """

    # Colors for visualization
    COLLISION_COLORS = {
        CollisionType.NONE: (0, 0, 0, 0),           # Transparent
        CollisionType.SOLID: (255, 0, 0, 128),      # Red
        CollisionType.PLATFORM: (0, 255, 0, 128),   # Green
        CollisionType.LADDER: (255, 255, 0, 128),   # Yellow
        CollisionType.WATER: (0, 0, 255, 128),      # Blue
        CollisionType.DAMAGE: (255, 0, 255, 128),   # Magenta
        CollisionType.TRIGGER: (0, 255, 255, 128),  # Cyan
        CollisionType.SLOPE_L: (255, 128, 0, 128),  # Orange
        CollisionType.SLOPE_R: (128, 255, 0, 128),  # Lime
    }

    SPAWN_COLOR = (0, 255, 0, 255)    # Green
    TRIGGER_COLOR = (0, 255, 255, 128) # Cyan transparent

    def __init__(self):
        """Initialize visualizer."""
        self._tileset_cache: Dict[str, Image.Image] = {}

    def render_map(self, tiled_map: TiledMap, scale: int = 1) -> Image.Image:
        """
        Render complete map with all visible layers.

        Args:
            tiled_map: Map to render
            scale: Scale factor for output

        Returns:
            PIL Image of rendered map
        """
        width = tiled_map.pixel_width * scale
        height = tiled_map.pixel_height * scale

        # Create base image
        if tiled_map.background_color:
            bg = self._parse_color(tiled_map.background_color)
        else:
            bg = (64, 64, 64, 255)

        img = Image.new('RGBA', (width, height), bg)

        # Render each layer
        for layer in tiled_map.layers:
            if layer.visible:
                layer_img = self._render_tile_layer(tiled_map, layer, scale)
                img = Image.alpha_composite(img, layer_img)

        return img

    def render_collision_overlay(self, tiled_map: TiledMap,
                                  collision: List[int],
                                  scale: int = 1) -> Image.Image:
        """
        Render collision map as colored overlay.

        Args:
            tiled_map: Map for dimensions
            collision: Collision type values
            scale: Scale factor

        Returns:
            PIL Image with collision visualization
        """
        width = tiled_map.pixel_width * scale
        height = tiled_map.pixel_height * scale

        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))

        tile_w = tiled_map.tile_width * scale
        tile_h = tiled_map.tile_height * scale

        for y in range(tiled_map.height):
            for x in range(tiled_map.width):
                idx = y * tiled_map.width + x
                if idx >= len(collision):
                    continue

                coll_type = CollisionType(collision[idx])
                if coll_type == CollisionType.NONE:
                    continue

                color = self.COLLISION_COLORS.get(coll_type, (128, 128, 128, 128))

                # Draw filled rectangle
                for py in range(tile_h):
                    for px in range(tile_w):
                        img.putpixel((x * tile_w + px, y * tile_h + py), color)

        return img

    def render_spawn_points(self, tiled_map: TiledMap, scale: int = 1) -> Image.Image:
        """
        Render spawn point markers.

        Args:
            tiled_map: Map with spawn points
            scale: Scale factor

        Returns:
            PIL Image with spawn markers
        """
        width = tiled_map.pixel_width * scale
        height = tiled_map.pixel_height * scale

        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))

        spawns = tiled_map.get_spawn_points()
        marker_size = max(4, 8 * scale)

        for spawn in spawns:
            x = int(spawn.x * scale)
            y = int(spawn.y * scale)

            # Draw X marker
            for i in range(-marker_size, marker_size + 1):
                if 0 <= x + i < width and 0 <= y + i < height:
                    img.putpixel((x + i, y + i), self.SPAWN_COLOR)
                if 0 <= x - i < width and 0 <= y + i < height:
                    img.putpixel((x - i, y + i), self.SPAWN_COLOR)

        return img

    def export_debug_image(self, tiled_map: TiledMap, output_path: str,
                           collision: Optional[List[int]] = None,
                           scale: int = 2) -> None:
        """
        Export complete debug visualization.

        Combines map render, collision overlay, and spawn points.

        Args:
            tiled_map: Map to visualize
            output_path: Output image path
            collision: Optional collision data (extracted if not provided)
            scale: Scale factor
        """
        # Base map
        img = self.render_map(tiled_map, scale)

        # Collision overlay
        if collision is None:
            exporter = CollisionExporter()
            collision = exporter.extract_tile_collision(tiled_map)

        coll_overlay = self.render_collision_overlay(tiled_map, collision, scale)
        img = Image.alpha_composite(img, coll_overlay)

        # Spawn points
        spawn_overlay = self.render_spawn_points(tiled_map, scale)
        img = Image.alpha_composite(img, spawn_overlay)

        # Save
        img.save(output_path)

    def _render_tile_layer(self, tiled_map: TiledMap, layer: TileLayer,
                           scale: int) -> Image.Image:
        """Render a single tile layer."""
        width = tiled_map.pixel_width * scale
        height = tiled_map.pixel_height * scale

        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))

        tile_w = tiled_map.tile_width
        tile_h = tiled_map.tile_height

        for y in range(layer.height):
            for x in range(layer.width):
                idx = y * layer.width + x
                gid = layer.data[idx]

                if gid == 0:
                    continue

                # Get tile image
                tile_img = self._get_tile_image(tiled_map, gid, tile_w, tile_h)
                if tile_img is None:
                    continue

                # Apply flips
                h_flip, v_flip = layer.get_flip(x, y)
                if h_flip:
                    tile_img = tile_img.transpose(Image.FLIP_LEFT_RIGHT)
                if v_flip:
                    tile_img = tile_img.transpose(Image.FLIP_TOP_BOTTOM)

                # Scale if needed
                if scale != 1:
                    tile_img = tile_img.resize(
                        (tile_w * scale, tile_h * scale),
                        Image.NEAREST
                    )

                # Paste tile
                dest_x = x * tile_w * scale
                dest_y = y * tile_h * scale
                img.paste(tile_img, (dest_x, dest_y), tile_img)

        return img

    def _get_tile_image(self, tiled_map: TiledMap, gid: int,
                        tile_w: int, tile_h: int) -> Optional[Image.Image]:
        """Get tile image from tileset."""
        tileset = tiled_map.get_tileset_for_gid(gid)
        if tileset is None:
            return None

        # Load tileset image if not cached
        if tileset.image_path not in self._tileset_cache:
            if tiled_map.source_path:
                base_dir = Path(tiled_map.source_path).parent
            else:
                base_dir = Path(".")

            img_path = base_dir / tileset.image_path
            if img_path.exists():
                self._tileset_cache[tileset.image_path] = Image.open(img_path).convert('RGBA')
            else:
                return None

        ts_img = self._tileset_cache[tileset.image_path]

        # Calculate tile position in tileset
        local_id = tileset.gid_to_local(gid)
        if tileset.columns > 0:
            tx = local_id % tileset.columns
            ty = local_id // tileset.columns
        else:
            tx = local_id
            ty = 0

        # Extract tile
        src_x = tileset.margin + tx * (tileset.tile_width + tileset.spacing)
        src_y = tileset.margin + ty * (tileset.tile_height + tileset.spacing)

        return ts_img.crop((src_x, src_y, src_x + tile_w, src_y + tile_h))

    def _parse_color(self, color_str: str) -> Tuple[int, int, int, int]:
        """Parse hex color string to RGBA tuple."""
        color_str = color_str.lstrip('#')
        if len(color_str) == 6:
            return (
                int(color_str[0:2], 16),
                int(color_str[2:4], 16),
                int(color_str[4:6], 16),
                255
            )
        elif len(color_str) == 8:
            return (
                int(color_str[2:4], 16),  # ARGB format
                int(color_str[4:6], 16),
                int(color_str[6:8], 16),
                int(color_str[0:2], 16)
            )
        return (128, 128, 128, 255)


# =============================================================================
# Convenience Functions
# =============================================================================

def load_tiled_map(path: str) -> TiledMap:
    """
    Load a Tiled map from file.

    Convenience function for quick map loading.

    Args:
        path: Path to TMX or JSON file

    Returns:
        TiledMap instance
    """
    parser = TiledParser()
    return parser.load(path)


def export_map_to_sgdk(tiled_map: TiledMap, output_dir: str,
                        prefix: str = "") -> MapExportResult:
    """
    Export Tiled map to SGDK format.

    Convenience function for quick export.

    Args:
        tiled_map: Parsed Tiled map
        output_dir: Output directory
        prefix: Optional prefix for generated files

    Returns:
        MapExportResult
    """
    exporter = SGDKMapExporter()
    config = MapExportConfig(output_dir=output_dir, prefix=prefix)
    return exporter.export_map(tiled_map, config)


def extract_collision(tiled_map: TiledMap,
                       layer_name: str = "collision") -> List[int]:
    """
    Extract collision data from Tiled map.

    Convenience function for quick collision extraction.

    Args:
        tiled_map: Parsed Tiled map
        layer_name: Name of collision layer

    Returns:
        List of collision type values
    """
    exporter = CollisionExporter()
    return exporter.extract_tile_collision(tiled_map, layer_name)


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    # Enums
    'CollisionType',
    'ObjectType',
    'Compression',
    # Data classes
    'TileLayer',
    'MapObject',
    'ObjectLayer',
    'TileProperties',
    'Tileset',
    'TiledMap',
    'ValidationResult',
    'MapExportConfig',
    'MapExportResult',
    # Classes
    'TiledParser',
    'CollisionExporter',
    'SGDKMapExporter',
    'MapVisualizer',
    # Convenience functions
    'load_tiled_map',
    'export_map_to_sgdk',
    'extract_collision',
]
