"""
Cross-Platform Asset Export for Multiple Retro Systems.

This module provides a unified interface for exporting sprites and assets
to multiple retro gaming platforms from a single source. It handles the
platform-specific constraints and formats automatically.

Supported Platforms:
    - Genesis/Mega Drive (SGDK): 4bpp tiles, 16-color palettes, VDP format
    - NES: 2bpp CHR tiles, 4-color palettes, fixed system palette
    - Game Boy: 2bpp tiles, 4-shade grayscale
    - Master System: 4bpp tiles, 16-color palettes from 64-color space
    - Game Gear: 4bpp tiles, 16-color palettes from 4096-color space

Key Features:
    - Single source image exports to multiple platforms
    - Automatic palette quantization per platform limits
    - Platform-specific tile format conversion
    - Unified API with platform-specific overrides
    - Batch export for entire asset directories

Design Philosophy:
    The pipeline is designed around "export once, target many" - you create
    your assets at the highest fidelity (Genesis 512-color space) and the
    exporter handles downsampling for more limited platforms.

Usage:
    >>> from pipeline.cross_platform import (
    ...     CrossPlatformExporter,
    ...     Platform,
    ...     ExportConfig,
    ... )
    >>>
    >>> # Create exporter
    >>> exporter = CrossPlatformExporter()
    >>>
    >>> # Export single sprite to multiple platforms
    >>> results = exporter.export_sprite(
    ...     "player.png",
    ...     platforms=[Platform.GENESIS, Platform.NES, Platform.GAMEBOY],
    ...     output_dir="exports/"
    ... )
    >>>
    >>> # Check results
    >>> for platform, files in results.items():
    ...     print(f"{platform.name}: {files}")

Platform Constraints Reference:
    | Platform    | Colors | Palette Size | Tile BPP | Tile Size |
    |-------------|--------|--------------|----------|-----------|
    | Genesis     | 512    | 16 × 4       | 4        | 8×8       |
    | NES         | 54     | 4 × 4        | 2        | 8×8       |
    | Game Boy    | 4      | 4 × 1        | 2        | 8×8       |
    | Master Sys  | 64     | 16 × 2       | 4        | 8×8       |
    | Game Gear   | 4096   | 16 × 2       | 4        | 8×8       |

Phase Implementation:
    - Phase 2.2.1: Cross-platform asset export variants
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any, Union
from enum import Enum, auto
from pathlib import Path
import os

# Optional PIL import for image processing
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class Platform(Enum):
    """Supported target platforms for asset export.

    Each platform has specific hardware constraints that affect how
    sprites and tiles are formatted.

    Attributes:
        GENESIS: Sega Genesis/Mega Drive (SGDK target)
        NES: Nintendo Entertainment System
        GAMEBOY: Nintendo Game Boy (original/Color in DMG mode)
        GAMEBOY_COLOR: Nintendo Game Boy Color (full color mode)
        MASTER_SYSTEM: Sega Master System
        GAME_GEAR: Sega Game Gear
    """
    GENESIS = auto()
    NES = auto()
    GAMEBOY = auto()
    GAMEBOY_COLOR = auto()
    MASTER_SYSTEM = auto()
    GAME_GEAR = auto()


@dataclass
class PlatformSpec:
    """Hardware specifications for a target platform.

    Contains all the constraints needed to properly export assets
    for a specific retro platform.

    Attributes:
        name: Human-readable platform name.
        bits_per_pixel: Tile color depth (2 or 4).
        palette_size: Colors per palette (4 or 16).
        num_palettes: Number of available palettes.
        total_colors: Total colors in hardware color space.
        tile_width: Tile width in pixels (always 8).
        tile_height: Tile height in pixels (always 8).
        color_format: Color encoding format string.
        max_sprites: Maximum hardware sprites.
        max_sprite_size: Maximum sprite dimension.
    """
    name: str
    bits_per_pixel: int
    palette_size: int
    num_palettes: int
    total_colors: int
    tile_width: int = 8
    tile_height: int = 8
    color_format: str = "rgb"
    max_sprites: int = 64
    max_sprite_size: int = 32


# Platform specifications database
PLATFORM_SPECS: Dict[Platform, PlatformSpec] = {
    Platform.GENESIS: PlatformSpec(
        name="Sega Genesis",
        bits_per_pixel=4,
        palette_size=16,
        num_palettes=4,
        total_colors=512,  # 9-bit RGB (3 bits per channel)
        color_format="bgr333",
        max_sprites=80,
        max_sprite_size=32,
    ),
    Platform.NES: PlatformSpec(
        name="Nintendo NES",
        bits_per_pixel=2,
        palette_size=4,
        num_palettes=4,
        total_colors=54,  # Fixed hardware palette
        color_format="nes_index",
        max_sprites=64,
        max_sprite_size=8,  # 8x16 with flag
    ),
    Platform.GAMEBOY: PlatformSpec(
        name="Nintendo Game Boy",
        bits_per_pixel=2,
        palette_size=4,
        num_palettes=1,
        total_colors=4,  # 4 shades of gray/green
        color_format="gray2",
        max_sprites=40,
        max_sprite_size=8,
    ),
    Platform.GAMEBOY_COLOR: PlatformSpec(
        name="Nintendo Game Boy Color",
        bits_per_pixel=2,
        palette_size=4,
        num_palettes=8,
        total_colors=32768,  # 15-bit RGB
        color_format="rgb555",
        max_sprites=40,
        max_sprite_size=8,
    ),
    Platform.MASTER_SYSTEM: PlatformSpec(
        name="Sega Master System",
        bits_per_pixel=4,
        palette_size=16,
        num_palettes=2,
        total_colors=64,  # 6-bit RGB (2 bits per channel)
        color_format="rgb222",
        max_sprites=64,
        max_sprite_size=8,
    ),
    Platform.GAME_GEAR: PlatformSpec(
        name="Sega Game Gear",
        bits_per_pixel=4,
        palette_size=16,
        num_palettes=2,
        total_colors=4096,  # 12-bit RGB (4 bits per channel)
        color_format="rgb444",
        max_sprites=64,
        max_sprite_size=8,
    ),
}


@dataclass
class ExportConfig:
    """Configuration for cross-platform export.

    Allows fine-tuning of the export process for specific needs.

    Attributes:
        platforms: List of target platforms.
        output_dir: Base directory for exported files.
        create_subdirs: Create platform-specific subdirectories.
        palette_index: Which palette slot to use (0-based).
        transparent_color: Color to treat as transparent (R, G, B).
        dither: Apply dithering when reducing colors.
        optimize_tiles: Enable tile deduplication.
        generate_headers: Generate C header files.
        prefix: Prefix for generated identifiers.
    """
    platforms: List[Platform] = field(default_factory=lambda: [Platform.GENESIS])
    output_dir: str = "exports"
    create_subdirs: bool = True
    palette_index: int = 0
    transparent_color: Tuple[int, int, int] = (255, 0, 255)  # Magenta
    dither: bool = False
    optimize_tiles: bool = True
    generate_headers: bool = True
    prefix: str = ""


@dataclass
class ExportResult:
    """Result of exporting an asset to a platform.

    Attributes:
        platform: Target platform.
        success: Whether export succeeded.
        tile_file: Path to exported tile data.
        palette_file: Path to exported palette data.
        header_file: Path to generated header (if any).
        tile_count: Number of tiles exported.
        colors_used: Number of colors in palette.
        warnings: Any warnings during export.
        error: Error message if failed.
    """
    platform: Platform
    success: bool
    tile_file: Optional[str] = None
    palette_file: Optional[str] = None
    header_file: Optional[str] = None
    tile_count: int = 0
    colors_used: int = 0
    warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None


class CrossPlatformExporter:
    """
    Export sprites and assets to multiple retro platforms.

    This class provides a unified interface for converting modern sprite
    images into platform-specific formats. It handles color quantization,
    tile conversion, and format-specific encoding automatically.

    The exporter follows a "highest fidelity first" approach:
    1. Parse source image
    2. Extract/quantize palette for each target platform
    3. Convert pixels to indexed format
    4. Encode tiles in platform-specific bit layout
    5. Generate output files and optional headers

    Example:
        >>> exporter = CrossPlatformExporter()
        >>>
        >>> # Export to all platforms
        >>> config = ExportConfig(
        ...     platforms=[Platform.GENESIS, Platform.NES, Platform.GAMEBOY],
        ...     output_dir="build/assets",
        ...     prefix="player"
        ... )
        >>> results = exporter.export_sprite("gfx/player.png", config)
        >>>
        >>> for result in results:
        ...     if result.success:
        ...         print(f"{result.platform.name}: {result.tile_count} tiles")
        ...     else:
        ...         print(f"{result.platform.name}: FAILED - {result.error}")
    """

    def __init__(self):
        """Initialize the cross-platform exporter."""
        self._color_cache: Dict[Platform, Dict[Tuple[int, int, int], int]] = {}

    def get_platform_spec(self, platform: Platform) -> PlatformSpec:
        """Get hardware specifications for a platform.

        Args:
            platform: Target platform enum.

        Returns:
            PlatformSpec with hardware constraints.
        """
        return PLATFORM_SPECS[platform]

    def export_sprite(
        self,
        image_path: str,
        config: ExportConfig = None,
        platforms: List[Platform] = None,
        output_dir: str = None,
    ) -> List[ExportResult]:
        """
        Export a sprite image to multiple platforms.

        Converts the source image to each target platform's format,
        handling color quantization and tile encoding automatically.

        Args:
            image_path: Path to source sprite image.
            config: Export configuration (optional).
            platforms: Override config platforms (convenience).
            output_dir: Override config output directory (convenience).

        Returns:
            List of ExportResult, one per target platform.

        Example:
            >>> results = exporter.export_sprite(
            ...     "player.png",
            ...     platforms=[Platform.GENESIS, Platform.NES]
            ... )
        """
        if not HAS_PIL:
            return [ExportResult(
                platform=Platform.GENESIS,
                success=False,
                error="PIL/Pillow not available"
            )]

        # Build config from arguments
        if config is None:
            config = ExportConfig()
        if platforms is not None:
            config.platforms = platforms
        if output_dir is not None:
            config.output_dir = output_dir

        # Load source image
        try:
            source = Image.open(image_path)
            if source.mode != 'RGBA':
                source = source.convert('RGBA')
        except Exception as e:
            return [ExportResult(
                platform=p,
                success=False,
                error=f"Failed to load image: {e}"
            ) for p in config.platforms]

        # Get base name for output files
        base_name = Path(image_path).stem
        if config.prefix:
            base_name = f"{config.prefix}_{base_name}"

        # Export to each platform
        results = []
        for platform in config.platforms:
            result = self._export_to_platform(
                source, platform, config, base_name
            )
            results.append(result)

        return results

    def _export_to_platform(
        self,
        source: 'Image.Image',
        platform: Platform,
        config: ExportConfig,
        base_name: str,
    ) -> ExportResult:
        """Export image to a specific platform format.

        Args:
            source: PIL Image (RGBA mode).
            platform: Target platform.
            config: Export configuration.
            base_name: Base name for output files.

        Returns:
            ExportResult with export details.
        """
        spec = PLATFORM_SPECS[platform]
        warnings = []

        # Create output directory
        if config.create_subdirs:
            out_dir = os.path.join(config.output_dir, platform.name.lower())
        else:
            out_dir = config.output_dir

        os.makedirs(out_dir, exist_ok=True)

        try:
            # Step 1: Quantize colors to platform palette
            palette, indexed = self._quantize_for_platform(
                source, platform, config.transparent_color, config.dither
            )

            # Check if we exceeded palette size
            if len(palette) > spec.palette_size:
                warnings.append(
                    f"Image has {len(palette)} colors, reduced to {spec.palette_size}"
                )
                # Re-quantize with forced limit
                palette, indexed = self._force_quantize(
                    source, platform, spec.palette_size,
                    config.transparent_color, config.dither
                )

            # Step 2: Convert to tiles
            tiles = self._image_to_tiles(indexed, spec)

            # Step 3: Optimize tiles if requested
            if config.optimize_tiles:
                tiles, tile_map = self._optimize_tiles(tiles)

            # Step 4: Encode in platform format
            tile_data = self._encode_tiles(tiles, platform)
            palette_data = self._encode_palette(palette, platform)

            # Step 5: Write output files
            tile_file = os.path.join(out_dir, f"{base_name}.tiles")
            palette_file = os.path.join(out_dir, f"{base_name}.pal")

            with open(tile_file, 'wb') as f:
                f.write(tile_data)
            with open(palette_file, 'wb') as f:
                f.write(palette_data)

            # Step 6: Generate header if requested
            header_file = None
            if config.generate_headers:
                header_file = os.path.join(out_dir, f"{base_name}.h")
                self._generate_header(
                    header_file, base_name, platform,
                    len(tiles), len(palette)
                )

            return ExportResult(
                platform=platform,
                success=True,
                tile_file=tile_file,
                palette_file=palette_file,
                header_file=header_file,
                tile_count=len(tiles),
                colors_used=len(palette),
                warnings=warnings,
            )

        except Exception as e:
            return ExportResult(
                platform=platform,
                success=False,
                error=str(e),
                warnings=warnings,
            )

    def _quantize_for_platform(
        self,
        source: 'Image.Image',
        platform: Platform,
        transparent: Tuple[int, int, int],
        dither: bool,
    ) -> Tuple[List[Tuple[int, int, int]], List[List[int]]]:
        """Quantize image colors to platform constraints.

        Args:
            source: Source image (RGBA).
            platform: Target platform for color space.
            transparent: Color to treat as transparent.
            dither: Whether to apply dithering.

        Returns:
            Tuple of (palette list, 2D indexed pixel array).
        """
        spec = PLATFORM_SPECS[platform]
        width, height = source.size

        # Collect unique colors (excluding transparent)
        colors: Dict[Tuple[int, int, int], int] = {}
        pixels = []

        for y in range(height):
            row = []
            for x in range(width):
                r, g, b, a = source.getpixel((x, y))

                # Handle transparency
                if a < 128 or (r, g, b) == transparent:
                    row.append(0)  # Index 0 = transparent
                    continue

                # Quantize to platform color space
                quantized = self._quantize_color((r, g, b), platform)

                if quantized not in colors:
                    colors[quantized] = len(colors) + 1  # +1 for transparent at 0

                row.append(colors[quantized])
            pixels.append(row)

        # Build palette (index 0 = transparent)
        palette = [transparent]  # Transparent color at index 0
        for color, _ in sorted(colors.items(), key=lambda x: x[1]):
            palette.append(color)

        return palette, pixels

    def _force_quantize(
        self,
        source: 'Image.Image',
        platform: Platform,
        max_colors: int,
        transparent: Tuple[int, int, int],
        dither: bool,
    ) -> Tuple[List[Tuple[int, int, int]], List[List[int]]]:
        """Force quantize to specific color count using PIL.

        Args:
            source: Source image.
            platform: Target platform.
            max_colors: Maximum palette size.
            transparent: Transparent color.
            dither: Apply dithering.

        Returns:
            Tuple of (palette, indexed pixels).
        """
        # Use PIL's quantize for color reduction
        dither_mode = Image.Dither.FLOYDSTEINBERG if dither else Image.Dither.NONE

        # Convert to RGB (drop alpha for quantization)
        rgb = source.convert('RGB')

        # Quantize
        quantized = rgb.quantize(
            colors=max_colors - 1,  # Reserve 1 for transparent
            dither=dither_mode
        )

        # Extract palette
        pal_data = quantized.getpalette()
        palette = [transparent]  # Index 0 = transparent

        for i in range(max_colors - 1):
            idx = i * 3
            if idx + 2 < len(pal_data):
                color = (pal_data[idx], pal_data[idx + 1], pal_data[idx + 2])
                # Quantize to platform color space
                palette.append(self._quantize_color(color, platform))

        # Build indexed pixels
        width, height = source.size
        pixels = []

        for y in range(height):
            row = []
            for x in range(width):
                r, g, b, a = source.getpixel((x, y))

                if a < 128 or (r, g, b) == transparent:
                    row.append(0)
                else:
                    # Get quantized index (+1 for transparent offset)
                    idx = quantized.getpixel((x, y)) + 1
                    row.append(min(idx, len(palette) - 1))
            pixels.append(row)

        return palette, pixels

    def _quantize_color(
        self,
        color: Tuple[int, int, int],
        platform: Platform,
    ) -> Tuple[int, int, int]:
        """Quantize a color to platform's color space.

        Args:
            color: RGB color tuple (0-255 per channel).
            platform: Target platform.

        Returns:
            Quantized RGB color tuple.
        """
        r, g, b = color
        spec = PLATFORM_SPECS[platform]

        if spec.color_format == "bgr333":
            # Genesis: 3 bits per channel (0-7), stored as 0-224 in steps of 32
            r = (r >> 5) << 5
            g = (g >> 5) << 5
            b = (b >> 5) << 5

        elif spec.color_format == "rgb222":
            # Master System: 2 bits per channel (0-3)
            r = (r >> 6) << 6
            g = (g >> 6) << 6
            b = (b >> 6) << 6

        elif spec.color_format == "rgb444":
            # Game Gear: 4 bits per channel (0-15)
            r = (r >> 4) << 4
            g = (g >> 4) << 4
            b = (b >> 4) << 4

        elif spec.color_format == "rgb555":
            # GBC: 5 bits per channel (0-31)
            r = (r >> 3) << 3
            g = (g >> 3) << 3
            b = (b >> 3) << 3

        elif spec.color_format == "gray2":
            # Game Boy: 2-bit grayscale
            gray = int(0.299 * r + 0.587 * g + 0.114 * b)
            gray = (gray >> 6) << 6
            r = g = b = gray

        elif spec.color_format == "nes_index":
            # NES: Find closest color in fixed palette
            # Simplified - just quantize to limited levels
            r = (r >> 6) << 6
            g = (g >> 6) << 6
            b = (b >> 6) << 6

        return (r, g, b)

    def _image_to_tiles(
        self,
        indexed: List[List[int]],
        spec: PlatformSpec,
    ) -> List[List[int]]:
        """Convert indexed image to 8×8 tiles.

        Args:
            indexed: 2D array of palette indices.
            spec: Platform specification.

        Returns:
            List of tiles, each tile is a flat list of 64 indices.
        """
        height = len(indexed)
        width = len(indexed[0]) if indexed else 0

        # Pad to tile boundaries
        pad_w = (8 - (width % 8)) % 8
        pad_h = (8 - (height % 8)) % 8

        if pad_w > 0:
            for row in indexed:
                row.extend([0] * pad_w)
            width += pad_w

        if pad_h > 0:
            for _ in range(pad_h):
                indexed.append([0] * width)
            height += pad_h

        # Extract tiles
        tiles = []
        for ty in range(height // 8):
            for tx in range(width // 8):
                tile = []
                for py in range(8):
                    for px in range(8):
                        y = ty * 8 + py
                        x = tx * 8 + px
                        tile.append(indexed[y][x])
                tiles.append(tile)

        return tiles

    def _optimize_tiles(
        self,
        tiles: List[List[int]],
    ) -> Tuple[List[List[int]], List[int]]:
        """Remove duplicate tiles and build tile map.

        Args:
            tiles: List of tile data.

        Returns:
            Tuple of (unique tiles, tile map indices).
        """
        unique = []
        tile_map = []
        seen: Dict[tuple, int] = {}

        for tile in tiles:
            key = tuple(tile)
            if key in seen:
                tile_map.append(seen[key])
            else:
                idx = len(unique)
                seen[key] = idx
                unique.append(tile)
                tile_map.append(idx)

        return unique, tile_map

    def _encode_tiles(
        self,
        tiles: List[List[int]],
        platform: Platform,
    ) -> bytes:
        """Encode tiles in platform-specific bit format.

        Args:
            tiles: List of tiles (each is 64 palette indices).
            platform: Target platform.

        Returns:
            Binary tile data.
        """
        spec = PLATFORM_SPECS[platform]
        data = bytearray()

        for tile in tiles:
            if spec.bits_per_pixel == 4:
                # 4bpp: 2 pixels per byte
                for i in range(0, 64, 2):
                    high = (tile[i] & 0x0F) << 4
                    low = tile[i + 1] & 0x0F
                    data.append(high | low)

            elif spec.bits_per_pixel == 2:
                # 2bpp: 4 pixels per byte (planar for NES/GB)
                if platform in (Platform.NES, Platform.GAMEBOY, Platform.GAMEBOY_COLOR):
                    # Planar format: separate bit planes
                    for row in range(8):
                        plane0 = 0
                        plane1 = 0
                        for px in range(8):
                            idx = tile[row * 8 + px] & 0x03
                            plane0 |= ((idx >> 0) & 1) << (7 - px)
                            plane1 |= ((idx >> 1) & 1) << (7 - px)
                        data.append(plane0)
                        data.append(plane1)
                else:
                    # Packed format
                    for i in range(0, 64, 4):
                        byte = 0
                        for j in range(4):
                            byte |= (tile[i + j] & 0x03) << (6 - j * 2)
                        data.append(byte)

        return bytes(data)

    def _encode_palette(
        self,
        palette: List[Tuple[int, int, int]],
        platform: Platform,
    ) -> bytes:
        """Encode palette in platform-specific format.

        Args:
            palette: List of RGB color tuples.
            platform: Target platform.

        Returns:
            Binary palette data.
        """
        spec = PLATFORM_SPECS[platform]
        data = bytearray()

        for r, g, b in palette:
            if spec.color_format == "bgr333":
                # Genesis: 0000BBB0GGG0RRR0 (big-endian)
                r3 = (r >> 5) & 0x07
                g3 = (g >> 5) & 0x07
                b3 = (b >> 5) & 0x07
                word = (b3 << 9) | (g3 << 5) | (r3 << 1)
                data.append((word >> 8) & 0xFF)
                data.append(word & 0xFF)

            elif spec.color_format == "rgb222":
                # Master System: 00BBGGRR
                r2 = (r >> 6) & 0x03
                g2 = (g >> 6) & 0x03
                b2 = (b >> 6) & 0x03
                data.append((b2 << 4) | (g2 << 2) | r2)

            elif spec.color_format == "rgb444":
                # Game Gear: XXXXBBBBGGGGRRRR (little-endian)
                r4 = (r >> 4) & 0x0F
                g4 = (g >> 4) & 0x0F
                b4 = (b >> 4) & 0x0F
                word = (b4 << 8) | (g4 << 4) | r4
                data.append(word & 0xFF)
                data.append((word >> 8) & 0xFF)

            elif spec.color_format == "rgb555":
                # GBC: 0BBBBBGGGGGRRRRR (little-endian)
                r5 = (r >> 3) & 0x1F
                g5 = (g >> 3) & 0x1F
                b5 = (b >> 3) & 0x1F
                word = (b5 << 10) | (g5 << 5) | r5
                data.append(word & 0xFF)
                data.append((word >> 8) & 0xFF)

            elif spec.color_format == "gray2":
                # Game Boy: 2-bit per color (pack 4 colors per byte)
                gray = int(0.299 * r + 0.587 * g + 0.114 * b)
                data.append((gray >> 6) & 0x03)

            elif spec.color_format == "nes_index":
                # NES: Just store index (would need palette lookup)
                gray = int(0.299 * r + 0.587 * g + 0.114 * b)
                data.append(gray >> 4)  # Simplified

        return bytes(data)

    def _generate_header(
        self,
        header_path: str,
        base_name: str,
        platform: Platform,
        tile_count: int,
        color_count: int,
    ) -> None:
        """Generate C header file for exported assets.

        Args:
            header_path: Path to write header.
            base_name: Base name for identifiers.
            platform: Target platform.
            tile_count: Number of tiles.
            color_count: Number of palette colors.
        """
        spec = PLATFORM_SPECS[platform]
        name_upper = base_name.upper().replace("-", "_")

        lines = [
            f"// Generated by CrossPlatformExporter",
            f"// Platform: {spec.name}",
            f"#ifndef {name_upper}_H",
            f"#define {name_upper}_H",
            "",
            f"#define {name_upper}_TILE_COUNT {tile_count}",
            f"#define {name_upper}_TILE_SIZE {8 * 8 * spec.bits_per_pixel // 8}",
            f"#define {name_upper}_PALETTE_SIZE {color_count}",
            f"#define {name_upper}_BPP {spec.bits_per_pixel}",
            "",
            f"extern const unsigned char {base_name}_tiles[];",
            f"extern const unsigned char {base_name}_palette[];",
            "",
            f"#endif // {name_upper}_H",
            "",
        ]

        with open(header_path, 'w') as f:
            f.write("\n".join(lines))

    def export_directory(
        self,
        input_dir: str,
        config: ExportConfig = None,
        pattern: str = "*.png",
    ) -> Dict[str, List[ExportResult]]:
        """Export all matching images in a directory.

        Args:
            input_dir: Directory containing source images.
            config: Export configuration.
            pattern: Glob pattern for image files.

        Returns:
            Dict mapping filename to list of ExportResults.
        """
        from glob import glob

        if config is None:
            config = ExportConfig()

        results: Dict[str, List[ExportResult]] = {}
        search_path = os.path.join(input_dir, pattern)

        for image_path in glob(search_path):
            file_name = os.path.basename(image_path)
            results[file_name] = self.export_sprite(image_path, config)

        return results


def export_multi_platform(
    image_path: str,
    platforms: List[Platform] = None,
    output_dir: str = "exports",
) -> List[ExportResult]:
    """Convenience function for quick multi-platform export.

    Args:
        image_path: Path to source image.
        platforms: Target platforms (default: Genesis, NES, Game Boy).
        output_dir: Output directory.

    Returns:
        List of ExportResult.

    Example:
        >>> results = export_multi_platform("player.png")
        >>> for r in results:
        ...     print(f"{r.platform.name}: {r.tile_count} tiles")
    """
    if platforms is None:
        platforms = [Platform.GENESIS, Platform.NES, Platform.GAMEBOY]

    exporter = CrossPlatformExporter()
    return exporter.export_sprite(
        image_path,
        platforms=platforms,
        output_dir=output_dir,
    )


def get_platform_info(platform: Platform) -> Dict[str, Any]:
    """Get human-readable platform information.

    Args:
        platform: Target platform.

    Returns:
        Dict with platform specifications.

    Example:
        >>> info = get_platform_info(Platform.GENESIS)
        >>> print(f"Max colors: {info['total_colors']}")
    """
    spec = PLATFORM_SPECS[platform]
    return {
        'name': spec.name,
        'bits_per_pixel': spec.bits_per_pixel,
        'palette_size': spec.palette_size,
        'num_palettes': spec.num_palettes,
        'total_colors': spec.total_colors,
        'tile_size': f"{spec.tile_width}x{spec.tile_height}",
        'max_sprites': spec.max_sprites,
        'max_sprite_size': spec.max_sprite_size,
        'color_format': spec.color_format,
    }
