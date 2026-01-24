"""
SGDK Resource File (.res) Generator.

This module generates SGDK resource definition files that the `rescomp` tool
compiles into C headers and binary data. It provides a Python API for managing
sprites, tilesets, palettes, maps, music, and sound effects with proper
ordering and dependency tracking.

Why Use This Module:
    - Programmatically generate .res files from processed assets
    - Integrate with the pipeline's sprite detection and animation extraction
    - Ensure resources are ordered correctly (palettes before sprites that use them)
    - Validate resource names and avoid duplicates
    - Generate from directory structure with sensible defaults

Build Integration:
    1. Process sprites with unified_pipeline.py → generates PNG + metadata
    2. Use this module to create resources.res from the processed assets
    3. Run SGDK's rescomp: `rescomp resources.res`
    4. Include generated headers in your C code

Usage:
    >>> from pipeline.sgdk_resources import SGDKResourceGenerator
    >>>
    >>> gen = SGDKResourceGenerator()
    >>> gen.add_palette("pal_player", "res/sprites/player_pal.png")
    >>> gen.add_sprite("spr_player", "res/sprites/player.png", 4, 4)
    >>> gen.add_tileset("ts_level", "res/tiles/level.png")
    >>> gen.add_map("map_level", "ts_level", "res/maps/level.tmx")
    >>> gen.generate("res/resources.res")

Output Format (.res file):
    // Resources
    PALETTE pal_player "res/sprites/player_pal.png"
    SPRITE spr_player "res/sprites/player.png" 4 4 NONE 0 NONE NONE
    TILESET ts_level "res/tiles/level.png" NONE ALL
    MAP map_level ts_level "res/maps/level.tmx" NONE

SGDK Resource Types:
    PALETTE - Color palette (16 colors, extracted from indexed PNG)
    SPRITE  - Animated sprite with size, compression, and collision options
    TILESET - Background tiles with deduplication optimization
    MAP     - Tilemap referencing a tileset (TMX or image)
    IMAGE   - Raw indexed image data
    XGM     - Music in XGM format (converted from VGM/MIDI)
    WAV     - Sound effect (PCM or ADPCM compressed)
    BIN     - Raw binary data with alignment control

Reference:
    https://github.com/Stephane-D/SGDK/blob/master/bin/rescomp.txt

Phase Implementation:
    - Phase 2.1.1: Core SGDK resource file generation
"""

import os
import re
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from pathlib import Path


class Compression(Enum):
    """
    SGDK compression methods for tile/sprite data.

    Compression reduces ROM size but requires decompression at runtime.
    Choose based on your needs:
    - NONE: No compression, fastest load, largest ROM
    - APLIB: Best ratio, slower decompression (good for infrequent loads)
    - LZ4W: Good ratio, fast decompression (good for streaming)
    """
    NONE = "NONE"            # No compression (fastest load)
    APLIB = "APLIB"          # High compression ratio, slower decompress
    LZ4W = "LZ4W"            # Balanced ratio, fast decompress
    RLE = "RLE"              # Run-length encoding (legacy)
    LZKN = "LZKN"            # Legacy Konami-style (deprecated)


class SpriteOptimization(Enum):
    """
    Sprite tile optimization modes for VRAM savings.

    Optimization reduces unique tiles by detecting duplicates and
    flipped variants. Trade-off: smaller VRAM usage vs. slower load.
    """
    NONE = "NONE"            # No optimization (fastest load)
    ALL = "ALL"              # Full optimization (duplicates + H/V flips)
    DUPLICATE = "DUPLICATE"  # Only exact duplicate removal


class TilesetOptimization(Enum):
    """
    Tileset tile optimization modes.

    Similar to sprite optimization but for background tilesets.
    """
    NONE = "NONE"            # No optimization
    ALL = "ALL"              # Full optimization (duplicates + flips)
    DUPLICATE = "DUPLICATE"  # Only exact duplicate removal


@dataclass
class SpriteResource:
    """
    SGDK SPRITE resource definition.

    Represents a sprite with optional animation frames. The sprite sheet
    image should be organized in frames of (width × height) tiles each,
    arranged left-to-right, top-to-bottom.

    Attributes:
        name: C identifier name (e.g., "spr_player").
        path: Path to sprite sheet PNG (relative to project root).
        width: Frame width in 8×8 tiles (e.g., 4 for 32px wide).
        height: Frame height in 8×8 tiles (e.g., 4 for 32px tall).
        compression: Tile data compression method.
        time: Default animation frame duration in ticks (0 = no auto-anim).
        collision: Collision shape: NONE, BOX, or CIRCLE.
        optimization: Tile deduplication mode.
        animations: Optional animation metadata for comments.
    """
    name: str
    path: str
    width: int
    height: int
    compression: Compression = Compression.NONE
    time: int = 0
    collision: str = "NONE"
    optimization: SpriteOptimization = SpriteOptimization.NONE
    animations: List[Dict] = field(default_factory=list)

    def to_res_line(self) -> str:
        """Generate SGDK .res file line."""
        # SPRITE name "path" width height compression time collision optimization
        parts = [
            "SPRITE",
            self.name,
            f'"{self.path}"',
            str(self.width),
            str(self.height),
            self.compression.value,
            str(self.time),
            self.collision,
            self.optimization.value,
        ]
        return " ".join(parts)


@dataclass
class TilesetResource:
    """SGDK TILESET resource definition."""
    name: str
    path: str
    compression: Compression = Compression.NONE
    optimization: TilesetOptimization = TilesetOptimization.ALL

    def to_res_line(self) -> str:
        """Generate SGDK .res file line."""
        # TILESET name "path" compression optimization
        return f'TILESET {self.name} "{self.path}" {self.compression.value} {self.optimization.value}'


@dataclass
class PaletteResource:
    """SGDK PALETTE resource definition."""
    name: str
    path: str

    def to_res_line(self) -> str:
        """Generate SGDK .res file line."""
        # PALETTE name "path"
        return f'PALETTE {self.name} "{self.path}"'


@dataclass
class MapResource:
    """SGDK MAP resource definition."""
    name: str
    tileset_name: str        # Reference to TILESET resource
    path: str                # Path to map data (TMX or image)
    compression: Compression = Compression.NONE

    def to_res_line(self) -> str:
        """Generate SGDK .res file line."""
        # MAP name tileset "path" compression
        return f'MAP {self.name} {self.tileset_name} "{self.path}" {self.compression.value}'


@dataclass
class ImageResource:
    """SGDK IMAGE resource definition."""
    name: str
    path: str
    compression: Compression = Compression.NONE

    def to_res_line(self) -> str:
        """Generate SGDK .res file line."""
        # IMAGE name "path" compression
        return f'IMAGE {self.name} "{self.path}" {self.compression.value}'


@dataclass
class BinaryResource:
    """SGDK BIN resource definition for raw data."""
    name: str
    path: str
    alignment: int = 2       # Byte alignment (2 = word, 4 = long)
    salign: int = 0          # Section alignment
    fill: int = 0            # Fill value for padding

    def to_res_line(self) -> str:
        """Generate SGDK .res file line."""
        # BIN name "path" alignment salign fill
        return f'BIN {self.name} "{self.path}" {self.alignment} {self.salign} {self.fill}'


@dataclass
class XGMResource:
    """SGDK XGM music resource definition."""
    name: str
    path: str
    timing: int = 0          # 0 = auto, 50 = PAL, 60 = NTSC

    def to_res_line(self) -> str:
        """Generate SGDK .res file line."""
        # XGM name "path" timing
        return f'XGM {self.name} "{self.path}" {self.timing}'


@dataclass
class WAVResource:
    """SGDK WAV sound effect resource definition."""
    name: str
    path: str
    driver: str = "PCM"      # PCM, 2ADPCM, 4ADPCM
    out_rate: int = 0        # 0 = auto

    def to_res_line(self) -> str:
        """Generate SGDK .res file line."""
        # WAV name "path" driver out_rate
        return f'WAV {self.name} "{self.path}" {self.driver} {self.out_rate}'


class SGDKResourceGenerator:
    """
    Generates complete SGDK resource (.res) files.

    Manages sprites, tilesets, palettes, maps, and other resources
    with proper ordering and dependency tracking.

    Example:
        gen = SGDKResourceGenerator()

        # Add resources
        gen.add_palette("pal_player", "res/sprites/player_pal.png")
        gen.add_sprite("spr_player", "res/sprites/player.png", 4, 4)
        gen.add_tileset("ts_level", "res/tiles/level.png")
        gen.add_map("map_level", "ts_level", "res/maps/level.tmx")

        # Generate .res file
        gen.generate("res/resources.res")
    """

    def __init__(self):
        self.palettes: List[PaletteResource] = []
        self.sprites: List[SpriteResource] = []
        self.tilesets: List[TilesetResource] = []
        self.maps: List[MapResource] = []
        self.images: List[ImageResource] = []
        self.binaries: List[BinaryResource] = []
        self.music: List[XGMResource] = []
        self.sounds: List[WAVResource] = []

        # Track names to avoid duplicates
        self._names: set = set()

    def _validate_name(self, name: str) -> str:
        """Validate and sanitize resource name."""
        # Convert to valid C identifier
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        if sanitized[0].isdigit():
            sanitized = '_' + sanitized

        if sanitized in self._names:
            raise ValueError(f"Duplicate resource name: {sanitized}")

        self._names.add(sanitized)
        return sanitized

    def _normalize_path(self, path: str) -> str:
        """Normalize path for SGDK (forward slashes)."""
        return path.replace('\\', '/')

    def add_palette(self, name: str, path: str) -> 'SGDKResourceGenerator':
        """
        Add a palette resource.

        Args:
            name: Resource name (will be prefixed in code)
            path: Path to palette image (PNG with indexed colors)

        Returns:
            Self for chaining
        """
        name = self._validate_name(name)
        path = self._normalize_path(path)
        self.palettes.append(PaletteResource(name=name, path=path))
        return self

    def add_sprite(
        self,
        name: str,
        path: str,
        width: int,
        height: int,
        compression: Compression = Compression.NONE,
        time: int = 0,
        collision: str = "NONE",
        optimization: SpriteOptimization = SpriteOptimization.NONE,
        animations: List[Dict] = None,
    ) -> 'SGDKResourceGenerator':
        """
        Add a sprite resource.

        Args:
            name: Resource name
            path: Path to sprite sheet image
            width: Sprite width in tiles (8px units)
            height: Sprite height in tiles (8px units)
            compression: Tile data compression
            time: Animation frame time (0 = no animation metadata)
            collision: Collision type (NONE, BOX, CIRCLE)
            optimization: Tile optimization mode
            animations: Optional animation sequence data

        Returns:
            Self for chaining

        Example:
            # 32x32 pixel sprite (4x4 tiles)
            gen.add_sprite("spr_player", "res/player.png", 4, 4)

            # With animation timing
            gen.add_sprite("spr_enemy", "res/enemy.png", 2, 2, time=8)
        """
        name = self._validate_name(name)
        path = self._normalize_path(path)
        self.sprites.append(SpriteResource(
            name=name,
            path=path,
            width=width,
            height=height,
            compression=compression,
            time=time,
            collision=collision,
            optimization=optimization,
            animations=animations or [],
        ))
        return self

    def add_tileset(
        self,
        name: str,
        path: str,
        compression: Compression = Compression.NONE,
        optimization: TilesetOptimization = TilesetOptimization.ALL,
    ) -> 'SGDKResourceGenerator':
        """
        Add a tileset resource.

        Args:
            name: Resource name
            path: Path to tileset image
            compression: Tile data compression
            optimization: Tile optimization (duplicate removal, etc.)

        Returns:
            Self for chaining
        """
        name = self._validate_name(name)
        path = self._normalize_path(path)
        self.tilesets.append(TilesetResource(
            name=name,
            path=path,
            compression=compression,
            optimization=optimization,
        ))
        return self

    def add_map(
        self,
        name: str,
        tileset_name: str,
        path: str,
        compression: Compression = Compression.NONE,
    ) -> 'SGDKResourceGenerator':
        """
        Add a map resource.

        Args:
            name: Resource name
            tileset_name: Name of tileset resource this map uses
            path: Path to map file (TMX or image)
            compression: Map data compression

        Returns:
            Self for chaining

        Note:
            The tileset must be added before calling generate().
        """
        name = self._validate_name(name)
        path = self._normalize_path(path)
        self.maps.append(MapResource(
            name=name,
            tileset_name=tileset_name,
            path=path,
            compression=compression,
        ))
        return self

    def add_image(
        self,
        name: str,
        path: str,
        compression: Compression = Compression.NONE,
    ) -> 'SGDKResourceGenerator':
        """
        Add an image resource.

        Args:
            name: Resource name
            path: Path to image file
            compression: Image data compression

        Returns:
            Self for chaining
        """
        name = self._validate_name(name)
        path = self._normalize_path(path)
        self.images.append(ImageResource(
            name=name,
            path=path,
            compression=compression,
        ))
        return self

    def add_binary(
        self,
        name: str,
        path: str,
        alignment: int = 2,
    ) -> 'SGDKResourceGenerator':
        """
        Add a raw binary resource.

        Args:
            name: Resource name
            path: Path to binary file
            alignment: Byte alignment (2 = word, 4 = long)

        Returns:
            Self for chaining
        """
        name = self._validate_name(name)
        path = self._normalize_path(path)
        self.binaries.append(BinaryResource(
            name=name,
            path=path,
            alignment=alignment,
        ))
        return self

    def add_music(
        self,
        name: str,
        path: str,
        timing: int = 0,
    ) -> 'SGDKResourceGenerator':
        """
        Add an XGM music resource.

        Args:
            name: Resource name
            path: Path to XGM/VGM file
            timing: 0 = auto, 50 = PAL, 60 = NTSC

        Returns:
            Self for chaining
        """
        name = self._validate_name(name)
        path = self._normalize_path(path)
        self.music.append(XGMResource(
            name=name,
            path=path,
            timing=timing,
        ))
        return self

    def add_sound(
        self,
        name: str,
        path: str,
        driver: str = "PCM",
        out_rate: int = 0,
    ) -> 'SGDKResourceGenerator':
        """
        Add a WAV sound effect resource.

        Args:
            name: Resource name
            path: Path to WAV file
            driver: PCM, 2ADPCM, or 4ADPCM
            out_rate: Output sample rate (0 = auto)

        Returns:
            Self for chaining
        """
        name = self._validate_name(name)
        path = self._normalize_path(path)
        self.sounds.append(WAVResource(
            name=name,
            path=path,
            driver=driver,
            out_rate=out_rate,
        ))
        return self

    def add_sprite_from_info(
        self,
        sprite_info: 'SpriteInfo',
        name: str = None,
        path: str = None,
    ) -> 'SGDKResourceGenerator':
        """
        Add a sprite from a SpriteInfo object (from pipeline processing).

        Args:
            sprite_info: SpriteInfo from pipeline detection
            name: Override name (default: from sprite_info)
            path: Override path (default: from sprite_info)

        Returns:
            Self for chaining
        """
        # Calculate tile dimensions
        width_tiles = (sprite_info.width + 7) // 8
        height_tiles = (sprite_info.height + 7) // 8

        return self.add_sprite(
            name=name or sprite_info.name or f"sprite_{len(self.sprites)}",
            path=path or sprite_info.source_path or "MISSING_PATH",
            width=width_tiles,
            height=height_tiles,
        )

    def add_animations_to_sprite(
        self,
        sprite_name: str,
        animations: List['AnimationSequence'],
    ) -> 'SGDKResourceGenerator':
        """
        Attach animation metadata to an existing sprite.

        Args:
            sprite_name: Name of sprite resource
            animations: List of AnimationSequence objects

        Returns:
            Self for chaining

        Note:
            This adds animation data that will be included as comments
            in the .res file. Full animation export requires the
            animation.py module for C header generation.
        """
        for sprite in self.sprites:
            if sprite.name == sprite_name:
                sprite.animations = [
                    {
                        'name': anim.name,
                        'frame_count': len(anim.frames),
                        'loop': anim.loop,
                        'duration': anim.frames[0].duration if anim.frames else 6,
                    }
                    for anim in animations
                ]
                return self

        raise ValueError(f"Sprite not found: {sprite_name}")

    def generate(self, output_path: str, include_header: bool = True) -> str:
        """
        Generate the complete .res file.

        Args:
            output_path: Path to write the .res file
            include_header: Include generation header comment

        Returns:
            Generated content string
        """
        lines = []

        # Header
        if include_header:
            lines.extend([
                "// =============================================================================",
                "// SGDK Resource File - Auto-generated",
                f"// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "// Generator: ARDK Pipeline (sgdk_resources.py)",
                "// ",
                "// DO NOT EDIT MANUALLY - Regenerate with unified_pipeline.py",
                "// =============================================================================",
                "",
            ])

        # Palettes first (sprites/images may depend on them)
        if self.palettes:
            lines.append("// Palettes")
            for pal in self.palettes:
                lines.append(pal.to_res_line())
            lines.append("")

        # Sprites
        if self.sprites:
            lines.append("// Sprites")
            for sprite in self.sprites:
                lines.append(sprite.to_res_line())
                # Add animation comments if present
                if sprite.animations:
                    for anim in sprite.animations:
                        loop_str = "loop" if anim.get('loop', True) else "one-shot"
                        lines.append(
                            f"// Animation: {anim['name']} - "
                            f"{anim['frame_count']} frames, "
                            f"{anim.get('duration', 6)} ticks, {loop_str}"
                        )
            lines.append("")

        # Tilesets (before maps)
        if self.tilesets:
            lines.append("// Tilesets")
            for tileset in self.tilesets:
                lines.append(tileset.to_res_line())
            lines.append("")

        # Maps
        if self.maps:
            lines.append("// Maps")
            for map_res in self.maps:
                lines.append(map_res.to_res_line())
            lines.append("")

        # Images
        if self.images:
            lines.append("// Images")
            for img in self.images:
                lines.append(img.to_res_line())
            lines.append("")

        # Music
        if self.music:
            lines.append("// Music (XGM)")
            for xgm in self.music:
                lines.append(xgm.to_res_line())
            lines.append("")

        # Sound effects
        if self.sounds:
            lines.append("// Sound Effects (WAV)")
            for wav in self.sounds:
                lines.append(wav.to_res_line())
            lines.append("")

        # Binary data
        if self.binaries:
            lines.append("// Binary Data")
            for bin_res in self.binaries:
                lines.append(bin_res.to_res_line())
            lines.append("")

        content = "\n".join(lines)

        # Write to file
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return content

    def get_summary(self) -> Dict[str, int]:
        """Get summary of registered resources."""
        return {
            'palettes': len(self.palettes),
            'sprites': len(self.sprites),
            'tilesets': len(self.tilesets),
            'maps': len(self.maps),
            'images': len(self.images),
            'music': len(self.music),
            'sounds': len(self.sounds),
            'binaries': len(self.binaries),
            'total': (
                len(self.palettes) + len(self.sprites) + len(self.tilesets) +
                len(self.maps) + len(self.images) + len(self.music) +
                len(self.sounds) + len(self.binaries)
            ),
        }

    def clear(self) -> 'SGDKResourceGenerator':
        """Clear all registered resources."""
        self.palettes.clear()
        self.sprites.clear()
        self.tilesets.clear()
        self.maps.clear()
        self.images.clear()
        self.binaries.clear()
        self.music.clear()
        self.sounds.clear()
        self._names.clear()
        return self


# =============================================================================
# Convenience Functions
# =============================================================================

def generate_resources_from_directory(
    sprites_dir: str = None,
    tiles_dir: str = None,
    maps_dir: str = None,
    output_path: str = "res/resources.res",
    sprite_size: Tuple[int, int] = (4, 4),
) -> str:
    """
    Auto-generate a .res file from directory structure.

    Scans directories for assets and creates appropriate resource entries.

    Args:
        sprites_dir: Directory containing sprite PNGs
        tiles_dir: Directory containing tileset PNGs
        maps_dir: Directory containing map files (TMX)
        output_path: Output .res file path
        sprite_size: Default sprite size in tiles (width, height)

    Returns:
        Generated content string

    Example:
        generate_resources_from_directory(
            sprites_dir="res/sprites",
            tiles_dir="res/tiles",
            maps_dir="res/maps",
            output_path="res/resources.res"
        )
    """
    gen = SGDKResourceGenerator()

    # Process sprites
    if sprites_dir and os.path.isdir(sprites_dir):
        for filename in sorted(os.listdir(sprites_dir)):
            if filename.lower().endswith('.png'):
                name = os.path.splitext(filename)[0]

                # Check if it's a palette file
                if '_pal' in name.lower() or name.lower().endswith('_palette'):
                    pal_name = f"pal_{name.replace('_pal', '').replace('_palette', '')}"
                    gen.add_palette(pal_name, f"{sprites_dir}/{filename}")
                else:
                    spr_name = f"spr_{name}"
                    gen.add_sprite(
                        spr_name,
                        f"{sprites_dir}/{filename}",
                        sprite_size[0],
                        sprite_size[1],
                    )

    # Process tilesets
    if tiles_dir and os.path.isdir(tiles_dir):
        for filename in sorted(os.listdir(tiles_dir)):
            if filename.lower().endswith('.png'):
                name = os.path.splitext(filename)[0]
                ts_name = f"ts_{name}"
                gen.add_tileset(ts_name, f"{tiles_dir}/{filename}")

    # Process maps
    if maps_dir and os.path.isdir(maps_dir):
        for filename in sorted(os.listdir(maps_dir)):
            if filename.lower().endswith(('.tmx', '.png')):
                name = os.path.splitext(filename)[0]
                map_name = f"map_{name}"

                # Try to find matching tileset
                tileset_name = None
                for ts in gen.tilesets:
                    if name in ts.name or ts.name.replace('ts_', '') in name:
                        tileset_name = ts.name
                        break

                if tileset_name:
                    gen.add_map(map_name, tileset_name, f"{maps_dir}/{filename}")

    return gen.generate(output_path)


def sprite_to_res_entry(
    name: str,
    path: str,
    width_px: int,
    height_px: int,
    compression: str = "NONE",
    time: int = 0,
) -> str:
    """
    Quick helper to generate a single sprite resource line.

    Args:
        name: Sprite name
        path: Path to sprite image
        width_px: Sprite width in pixels
        height_px: Sprite height in pixels
        compression: Compression type
        time: Animation time

    Returns:
        Single SPRITE line for .res file
    """
    width_tiles = (width_px + 7) // 8
    height_tiles = (height_px + 7) // 8
    return f'SPRITE {name} "{path}" {width_tiles} {height_tiles} {compression} {time} NONE NONE'


# =============================================================================
# Test / Demo
# =============================================================================

if __name__ == "__main__":
    print("=== SGDK Resource Generator Test ===\n")

    gen = SGDKResourceGenerator()

    # Add sample resources
    gen.add_palette("pal_player", "res/sprites/player_pal.png")
    gen.add_palette("pal_enemies", "res/sprites/enemies_pal.png")

    gen.add_sprite("spr_player", "res/sprites/player.png", 4, 4, time=8)
    gen.add_sprite("spr_fenrir", "res/sprites/fenrir.png", 3, 3, time=6)
    gen.add_sprite("spr_enemy", "res/sprites/enemy.png", 2, 2, time=4)

    gen.add_tileset("ts_siege", "res/tiles/siege_tiles.png")
    gen.add_tileset("ts_wilds", "res/tiles/wilds_tiles.png")

    gen.add_map("map_siege", "ts_siege", "res/maps/siege_zone.tmx")
    gen.add_map("map_wilds", "ts_wilds", "res/maps/wilds_zone.tmx")

    gen.add_music("bgm_siege", "res/music/siege_theme.xgm")
    gen.add_sound("sfx_hit", "res/sfx/hit.wav")

    # Generate
    content = gen.generate("test_resources.res")
    print(content)

    # Summary
    print("\n=== Summary ===")
    summary = gen.get_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    # Cleanup test file
    if os.path.exists("test_resources.res"):
        os.remove("test_resources.res")

    print("\nTest complete!")
