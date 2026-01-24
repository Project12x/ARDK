"""
Aseprite Integration for ARDK Asset Pipeline.

Automate sprite export from Aseprite files, preserving layers, tags,
and metadata for seamless integration with retro game development.

Phase: 1.8 (Core Features)

Key Features:
- CLI-based export (requires Aseprite installation)
- JSON metadata parsing (works without Aseprite)
- Layer extraction (body, shadow, effects)
- Animation tag extraction
- SGDK-compatible output generation
- Batch processing support

Requirements:
- Aseprite installation (for export features)
- Or: Pre-exported JSON + sprite sheet (for parse-only mode)

Usage:
    from tools.pipeline.integrations import (
        AsepriteExporter,
        parse_aseprite_json,
        frames_to_animation_sequences,
    )

    # Full export (requires Aseprite)
    exporter = AsepriteExporter()
    if exporter.is_available():
        result = exporter.export_sheet("player.ase", "output/")
        print(f"Exported {result.frame_count} frames")

    # Parse existing JSON (no Aseprite needed)
    metadata = parse_aseprite_json("player.json")
    sequences = frames_to_animation_sequences(metadata)

Aseprite CLI Reference:
    https://www.aseprite.org/docs/cli/

MCP Server (optional):
    https://creati.ai/mcp/aseprite-mcp/
"""

import subprocess
import json
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Literal
from dataclasses import dataclass, field
from PIL import Image


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class AsepriteFrame:
    """Single frame from Aseprite export."""
    filename: str
    x: int
    y: int
    width: int
    height: int
    duration: int  # milliseconds
    index: int  # Frame number

    @property
    def rect(self) -> Tuple[int, int, int, int]:
        """Get (x, y, width, height) tuple."""
        return (self.x, self.y, self.width, self.height)

    @property
    def duration_frames(self) -> int:
        """Get duration in 60fps frames (rounded)."""
        return max(1, round(self.duration / 16.67))


@dataclass
class AsepriteTag:
    """Animation tag from Aseprite."""
    name: str
    start_frame: int
    end_frame: int
    direction: str  # "forward", "reverse", "pingpong"
    color: str  # Hex color

    @property
    def frame_count(self) -> int:
        """Number of frames in this tag."""
        return self.end_frame - self.start_frame + 1

    @property
    def is_looping(self) -> bool:
        """Determine if animation should loop based on name."""
        non_looping = ['attack', 'death', 'die', 'hit', 'hurt', 'cast', 'shoot']
        return not any(keyword in self.name.lower() for keyword in non_looping)


@dataclass
class AsepriteLayer:
    """Layer information from Aseprite."""
    name: str
    opacity: int  # 0-255
    blend_mode: str
    group: Optional[str] = None  # Parent group name

    @property
    def is_visible(self) -> bool:
        """Check if layer is effectively visible."""
        return self.opacity > 0


@dataclass
class AsepriteSlice:
    """Slice (region) information from Aseprite."""
    name: str
    x: int
    y: int
    width: int
    height: int
    pivot_x: Optional[int] = None
    pivot_y: Optional[int] = None
    color: Optional[str] = None


@dataclass
class AsepriteMetadata:
    """Complete metadata from Aseprite JSON export."""
    frames: List[AsepriteFrame]
    tags: List[AsepriteTag]
    layers: List[AsepriteLayer]
    slices: List[AsepriteSlice]
    image_path: str
    image_width: int
    image_height: int
    frame_width: int
    frame_height: int
    format: str  # "RGBA8888", "I8", etc.
    scale: int

    def get_tag(self, name: str) -> Optional[AsepriteTag]:
        """Get tag by name (case-insensitive)."""
        name_lower = name.lower()
        for tag in self.tags:
            if tag.name.lower() == name_lower:
                return tag
        return None

    def get_frames_for_tag(self, tag_name: str) -> List[AsepriteFrame]:
        """Get frames belonging to a tag."""
        tag = self.get_tag(tag_name)
        if not tag:
            return []
        return [f for f in self.frames if tag.start_frame <= f.index <= tag.end_frame]

    def get_layer(self, name: str) -> Optional[AsepriteLayer]:
        """Get layer by name."""
        for layer in self.layers:
            if layer.name == name:
                return layer
        return None


@dataclass
class AsepriteExportResult:
    """Result of Aseprite export operation."""
    sheet_path: Path
    json_path: Path
    metadata: AsepriteMetadata
    layers: List[str]
    tags: List[str]
    frame_count: int
    success: bool
    error: Optional[str] = None

    @property
    def image(self) -> Optional[Image.Image]:
        """Load the exported sprite sheet."""
        if self.sheet_path.exists():
            return Image.open(self.sheet_path)
        return None


# =============================================================================
# JSON PARSING
# =============================================================================

def parse_aseprite_json(json_path: str) -> AsepriteMetadata:
    """
    Parse Aseprite JSON export file.

    Works without Aseprite installation - just needs the JSON file.

    Args:
        json_path: Path to Aseprite JSON export

    Returns:
        AsepriteMetadata with all parsed information

    Example:
        metadata = parse_aseprite_json("player.json")
        for tag in metadata.tags:
            print(f"Animation: {tag.name} ({tag.frame_count} frames)")
    """
    with open(json_path, 'r') as f:
        data = json.load(f)

    # Parse frames
    frames_data = data.get('frames', {})
    frames = []

    # Handle both array and object formats
    if isinstance(frames_data, list):
        for i, frame_data in enumerate(frames_data):
            frame = _parse_frame(frame_data, i)
            frames.append(frame)
    else:
        for i, (name, frame_data) in enumerate(frames_data.items()):
            frame_data['filename'] = name
            frame = _parse_frame(frame_data, i)
            frames.append(frame)

    # Sort by index
    frames.sort(key=lambda f: f.index)

    # Parse meta
    meta = data.get('meta', {})

    # Parse tags
    tags = []
    for tag_data in meta.get('frameTags', []):
        tags.append(AsepriteTag(
            name=tag_data.get('name', ''),
            start_frame=tag_data.get('from', 0),
            end_frame=tag_data.get('to', 0),
            direction=tag_data.get('direction', 'forward'),
            color=tag_data.get('color', '#000000'),
        ))

    # Parse layers
    layers = []
    for layer_data in meta.get('layers', []):
        layers.append(AsepriteLayer(
            name=layer_data.get('name', ''),
            opacity=layer_data.get('opacity', 255),
            blend_mode=layer_data.get('blendMode', 'normal'),
            group=layer_data.get('group'),
        ))

    # Parse slices
    slices = []
    for slice_data in meta.get('slices', []):
        keys = slice_data.get('keys', [{}])
        key = keys[0] if keys else {}
        bounds = key.get('bounds', {})
        pivot = key.get('pivot', {})

        slices.append(AsepriteSlice(
            name=slice_data.get('name', ''),
            x=bounds.get('x', 0),
            y=bounds.get('y', 0),
            width=bounds.get('w', 0),
            height=bounds.get('h', 0),
            pivot_x=pivot.get('x'),
            pivot_y=pivot.get('y'),
            color=slice_data.get('color'),
        ))

    # Get image info
    size = meta.get('size', {})
    image_width = size.get('w', 0)
    image_height = size.get('h', 0)

    # Determine frame size from first frame
    frame_width = frames[0].width if frames else 0
    frame_height = frames[0].height if frames else 0

    return AsepriteMetadata(
        frames=frames,
        tags=tags,
        layers=layers,
        slices=slices,
        image_path=meta.get('image', ''),
        image_width=image_width,
        image_height=image_height,
        frame_width=frame_width,
        frame_height=frame_height,
        format=meta.get('format', 'RGBA8888'),
        scale=int(meta.get('scale', '1')),
    )


def _parse_frame(frame_data: Dict[str, Any], index: int) -> AsepriteFrame:
    """Parse single frame from JSON data."""
    frame_rect = frame_data.get('frame', {})
    return AsepriteFrame(
        filename=frame_data.get('filename', f'frame_{index}'),
        x=frame_rect.get('x', 0),
        y=frame_rect.get('y', 0),
        width=frame_rect.get('w', 0),
        height=frame_rect.get('h', 0),
        duration=frame_data.get('duration', 100),
        index=index,
    )


# =============================================================================
# ANIMATION CONVERSION
# =============================================================================

def frames_to_animation_sequences(metadata: AsepriteMetadata) -> List[Dict[str, Any]]:
    """
    Convert Aseprite metadata to animation sequences.

    Compatible with pipeline's AnimationSequence format.

    Args:
        metadata: Parsed Aseprite metadata

    Returns:
        List of animation sequence dicts

    Example:
        metadata = parse_aseprite_json("player.json")
        sequences = frames_to_animation_sequences(metadata)
        # sequences = [
        #     {'name': 'idle', 'frames': [...], 'loop': True},
        #     {'name': 'walk', 'frames': [...], 'loop': True},
        # ]
    """
    sequences = []

    for tag in metadata.tags:
        frames = metadata.get_frames_for_tag(tag.name)

        # Handle pingpong direction
        if tag.direction == 'pingpong' and len(frames) > 2:
            # Add reversed frames (excluding first and last to avoid doubles)
            frames = frames + frames[-2:0:-1]
        elif tag.direction == 'reverse':
            frames = list(reversed(frames))

        sequence = {
            'name': tag.name,
            'frames': [
                {
                    'sprite_index': f.index,
                    'duration': f.duration_frames,
                    'x': f.x,
                    'y': f.y,
                    'width': f.width,
                    'height': f.height,
                }
                for f in frames
            ],
            'loop': tag.is_looping,
            'total_duration_ms': sum(f.duration for f in frames),
        }
        sequences.append(sequence)

    return sequences


# =============================================================================
# ASEPRITE EXPORTER
# =============================================================================

SheetType = Literal['packed', 'horizontal', 'vertical', 'rows', 'columns']


class AsepriteExporter:
    """
    Automate Aseprite sprite exports via CLI.

    Requires Aseprite to be installed and accessible via PATH,
    or specify the exe_path directly.

    Example:
        exporter = AsepriteExporter()

        # Check if Aseprite is available
        if exporter.is_available():
            # Export sprite sheet with metadata
            result = exporter.export_sheet(
                "characters/player.ase",
                "output/",
                sheet_type="horizontal",
                split_tags=True
            )

            # Access results
            print(f"Exported to: {result.sheet_path}")
            print(f"Tags: {result.tags}")
            for tag in result.metadata.tags:
                print(f"  {tag.name}: {tag.frame_count} frames")

        # Or use parse-only mode
        metadata = exporter.parse_existing_json("player.json")
    """

    # Common Aseprite installation paths
    DEFAULT_PATHS = [
        'aseprite',  # In PATH
        'Aseprite',  # Case variant
        r'C:\Program Files\Aseprite\Aseprite.exe',
        r'C:\Program Files (x86)\Aseprite\Aseprite.exe',
        r'C:\Program Files\Steam\steamapps\common\Aseprite\Aseprite.exe',
        '/Applications/Aseprite.app/Contents/MacOS/aseprite',
        '/usr/bin/aseprite',
        '/usr/local/bin/aseprite',
    ]

    def __init__(self, exe_path: Optional[str] = None):
        """
        Initialize exporter.

        Args:
            exe_path: Path to Aseprite executable. If None, searches common locations.
        """
        self.exe = exe_path or self._find_aseprite()
        self._available: Optional[bool] = None

    def _find_aseprite(self) -> str:
        """Find Aseprite executable in common locations."""
        for path in self.DEFAULT_PATHS:
            if shutil.which(path):
                return path
        return 'aseprite'  # Default, may not exist

    def is_available(self) -> bool:
        """
        Check if Aseprite CLI is available.

        Returns:
            True if Aseprite can be executed
        """
        if self._available is not None:
            return self._available

        try:
            result = subprocess.run(
                [self.exe, '--version'],
                capture_output=True,
                timeout=5
            )
            self._available = result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            self._available = False

        return self._available

    def get_version(self) -> Optional[str]:
        """Get Aseprite version string."""
        if not self.is_available():
            return None

        try:
            result = subprocess.run(
                [self.exe, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip()
        except subprocess.SubprocessError:
            return None

    def export_sheet(self,
                     input_path: str,
                     output_dir: str,
                     *,
                     scale: int = 1,
                     sheet_type: SheetType = 'packed',
                     split_layers: bool = False,
                     split_tags: bool = False,
                     trim: bool = False,
                     border_padding: int = 0,
                     shape_padding: int = 0,
                     inner_padding: int = 0) -> AsepriteExportResult:
        """
        Export Aseprite file to sprite sheet with metadata.

        Args:
            input_path: Path to .ase or .aseprite file
            output_dir: Output directory
            scale: Scale factor (1, 2, 4)
            sheet_type: Sheet layout type
            split_layers: Export each layer as separate sheet
            split_tags: Export each tag as separate sheet
            trim: Trim empty space from frames
            border_padding: Padding around entire sheet
            shape_padding: Padding around each frame
            inner_padding: Padding inside each frame

        Returns:
            AsepriteExportResult with paths and metadata

        Raises:
            FileNotFoundError: If input file doesn't exist
            RuntimeError: If Aseprite is not available
        """
        input_path = Path(input_path)
        output_dir = Path(output_dir)

        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        if not self.is_available():
            raise RuntimeError(
                "Aseprite is not available. Install Aseprite and ensure it's in PATH, "
                "or specify exe_path when creating AsepriteExporter."
            )

        output_dir.mkdir(parents=True, exist_ok=True)

        name = input_path.stem
        sheet_path = output_dir / f"{name}.png"
        json_path = output_dir / f"{name}.json"

        # Build command
        cmd = [
            self.exe, '-b',  # Batch mode (no UI)
            str(input_path),
            '--sheet', str(sheet_path),
            '--sheet-type', sheet_type,
            '--data', str(json_path),
            '--format', 'json-array',
            '--list-layers',
            '--list-tags',
            '--list-slices',
        ]

        if scale != 1:
            cmd.extend(['--scale', str(scale)])

        if split_layers:
            cmd.append('--split-layers')

        if split_tags:
            cmd.append('--split-tags')

        if trim:
            cmd.append('--trim')

        if border_padding > 0:
            cmd.extend(['--border-padding', str(border_padding)])

        if shape_padding > 0:
            cmd.extend(['--shape-padding', str(shape_padding)])

        if inner_padding > 0:
            cmd.extend(['--inner-padding', str(inner_padding)])

        # Execute
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                return AsepriteExportResult(
                    sheet_path=sheet_path,
                    json_path=json_path,
                    metadata=None,
                    layers=[],
                    tags=[],
                    frame_count=0,
                    success=False,
                    error=result.stderr or f"Aseprite exited with code {result.returncode}"
                )

        except subprocess.TimeoutExpired:
            return AsepriteExportResult(
                sheet_path=sheet_path,
                json_path=json_path,
                metadata=None,
                layers=[],
                tags=[],
                frame_count=0,
                success=False,
                error="Aseprite export timed out"
            )

        # Parse the generated JSON
        metadata = parse_aseprite_json(str(json_path))

        return AsepriteExportResult(
            sheet_path=sheet_path,
            json_path=json_path,
            metadata=metadata,
            layers=[layer.name for layer in metadata.layers],
            tags=[tag.name for tag in metadata.tags],
            frame_count=len(metadata.frames),
            success=True
        )

    def export_layers_separate(self,
                                input_path: str,
                                output_dir: str,
                                scale: int = 1) -> Dict[str, Path]:
        """
        Export each layer as a separate PNG file.

        Args:
            input_path: Path to .ase file
            output_dir: Output directory
            scale: Scale factor

        Returns:
            Dict mapping layer name to output path
        """
        input_path = Path(input_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            self.exe, '-b',
            str(input_path),
            '--save-as', str(output_dir / '{layer}.png'),
            '--split-layers'
        ]

        if scale != 1:
            cmd.extend(['--scale', str(scale)])

        subprocess.run(cmd, check=True, capture_output=True)

        return {p.stem: p for p in output_dir.glob('*.png')}

    def export_tags_separate(self,
                              input_path: str,
                              output_dir: str,
                              sheet_type: SheetType = 'horizontal',
                              scale: int = 1) -> Dict[str, AsepriteExportResult]:
        """
        Export each animation tag as a separate sprite sheet.

        Args:
            input_path: Path to .ase file
            output_dir: Output directory
            sheet_type: Sheet layout type
            scale: Scale factor

        Returns:
            Dict mapping tag name to export result
        """
        input_path = Path(input_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # First, get the tags from a full export
        temp_result = self.export_sheet(
            str(input_path),
            str(output_dir),
            scale=scale,
            sheet_type=sheet_type
        )

        if not temp_result.success:
            return {}

        results = {}

        # Export each tag separately
        for tag in temp_result.metadata.tags:
            tag_sheet = output_dir / f"{input_path.stem}_{tag.name}.png"
            tag_json = output_dir / f"{input_path.stem}_{tag.name}.json"

            cmd = [
                self.exe, '-b',
                str(input_path),
                '--sheet', str(tag_sheet),
                '--sheet-type', sheet_type,
                '--data', str(tag_json),
                '--format', 'json-array',
                '--tag', tag.name,
            ]

            if scale != 1:
                cmd.extend(['--scale', str(scale)])

            try:
                subprocess.run(cmd, check=True, capture_output=True, timeout=30)
                metadata = parse_aseprite_json(str(tag_json))
                results[tag.name] = AsepriteExportResult(
                    sheet_path=tag_sheet,
                    json_path=tag_json,
                    metadata=metadata,
                    layers=[],
                    tags=[tag.name],
                    frame_count=len(metadata.frames),
                    success=True
                )
            except subprocess.SubprocessError as e:
                results[tag.name] = AsepriteExportResult(
                    sheet_path=tag_sheet,
                    json_path=tag_json,
                    metadata=None,
                    layers=[],
                    tags=[tag.name],
                    frame_count=0,
                    success=False,
                    error=str(e)
                )

        return results

    def parse_existing_json(self, json_path: str) -> AsepriteMetadata:
        """
        Parse existing Aseprite JSON file (no Aseprite needed).

        Args:
            json_path: Path to JSON file

        Returns:
            AsepriteMetadata
        """
        return parse_aseprite_json(json_path)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def is_aseprite_available() -> bool:
    """Check if Aseprite CLI is available on this system."""
    return AsepriteExporter().is_available()


def extract_frames_from_sheet(sheet_path: str,
                               json_path: str) -> List[Image.Image]:
    """
    Extract individual frames from sprite sheet using JSON metadata.

    Args:
        sheet_path: Path to sprite sheet PNG
        json_path: Path to Aseprite JSON

    Returns:
        List of frame images
    """
    metadata = parse_aseprite_json(json_path)
    sheet = Image.open(sheet_path)

    frames = []
    for frame in metadata.frames:
        frame_img = sheet.crop((
            frame.x,
            frame.y,
            frame.x + frame.width,
            frame.y + frame.height
        ))
        frames.append(frame_img)

    return frames


def extract_tag_frames(sheet_path: str,
                        json_path: str,
                        tag_name: str) -> List[Image.Image]:
    """
    Extract frames for a specific animation tag.

    Args:
        sheet_path: Path to sprite sheet PNG
        json_path: Path to Aseprite JSON
        tag_name: Name of animation tag

    Returns:
        List of frame images for that tag
    """
    metadata = parse_aseprite_json(json_path)
    sheet = Image.open(sheet_path)

    tag_frames = metadata.get_frames_for_tag(tag_name)
    if not tag_frames:
        return []

    frames = []
    for frame in tag_frames:
        frame_img = sheet.crop((
            frame.x,
            frame.y,
            frame.x + frame.width,
            frame.y + frame.height
        ))
        frames.append(frame_img)

    return frames
