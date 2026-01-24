"""
Tile Deduplicator - Hash-based tile merging with flip detection.

Reduces CHR usage by 20-40% by:
- Finding identical tiles
- Detecting horizontal flip matches
- Detecting vertical flip matches
- Detecting 180-degree rotation matches (H+V flip)
- Tracking flip flags in tile map for rendering
"""

import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import numpy as np

try:
    from PIL import Image
except ImportError:
    raise ImportError("PIL required: pip install pillow")


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class TileFlags:
    """Flags for tile rendering (flip state)."""
    horizontal_flip: bool = False
    vertical_flip: bool = False

    def to_byte(self) -> int:
        """Convert flags to single byte for NES OAM/nametable."""
        # NES attribute: bit 6 = H flip, bit 7 = V flip
        result = 0
        if self.horizontal_flip:
            result |= 0x40
        if self.vertical_flip:
            result |= 0x80
        return result

    @staticmethod
    def from_byte(value: int) -> 'TileFlags':
        """Create flags from byte."""
        return TileFlags(
            horizontal_flip=bool(value & 0x40),
            vertical_flip=bool(value & 0x80),
        )


@dataclass
class TileRef:
    """Reference to a tile with flip flags."""
    tile_id: int
    flags: TileFlags = field(default_factory=TileFlags)
    x: int = 0
    y: int = 0


@dataclass
class OptimizedTile:
    """A unique tile after deduplication."""
    tile_id: int
    pixels: np.ndarray          # (tile_height, tile_width) indexed pixels
    hash: str                   # MD5 hash of pixel data
    reference_count: int = 1    # How many times this tile is used


@dataclass
class TileOptimizationResult:
    """Result of tile optimization."""
    unique_tiles: List[OptimizedTile]
    tile_map: List[TileRef]
    original_tile_count: int
    optimized_tile_count: int
    savings_percent: float
    flip_stats: Dict[str, int] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


# =============================================================================
# Tile Deduplicator
# =============================================================================

class TileDeduplicator:
    """Find and merge duplicate tiles, including flipped versions."""

    def __init__(
        self,
        tile_width: int = 8,
        tile_height: int = 8,
        enable_h_flip: bool = True,
        enable_v_flip: bool = True,
        colors_per_palette: int = 4,
    ):
        """
        Initialize deduplicator.

        Args:
            tile_width: Width of each tile (usually 8)
            tile_height: Height of each tile (usually 8)
            enable_h_flip: Check for horizontal flip matches
            enable_v_flip: Check for vertical flip matches
            colors_per_palette: Number of colors in palette (for validation)
        """
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.enable_h_flip = enable_h_flip
        self.enable_v_flip = enable_v_flip
        self.colors_per_palette = colors_per_palette

    def optimize(
        self,
        image: Image.Image,
        palette: Optional[List[int]] = None,
    ) -> TileOptimizationResult:
        """
        Optimize image into unique tiles with mapping.

        Args:
            image: PIL Image to optimize (should be indexed or RGBA)
            palette: Optional palette for validation

        Returns:
            TileOptimizationResult with unique tiles and mapping
        """
        # Convert to indexed if needed
        indexed = self._to_indexed(image, palette)

        # Extract all tiles
        all_tiles = self._extract_tiles(indexed)

        if not all_tiles:
            return TileOptimizationResult(
                unique_tiles=[],
                tile_map=[],
                original_tile_count=0,
                optimized_tile_count=0,
                savings_percent=0.0,
                warnings=["No tiles extracted from image"],
            )

        # Deduplicate with flip detection
        unique_tiles: List[OptimizedTile] = []
        tile_map: List[TileRef] = []
        tile_hash_map: Dict[str, Tuple[int, TileFlags]] = {}

        flip_stats = {
            'direct_match': 0,
            'h_flip_match': 0,
            'v_flip_match': 0,
            'hv_flip_match': 0,
            'unique': 0,
        }

        for tile_info in all_tiles:
            x, y, pixels = tile_info
            match = self._find_match(pixels, tile_hash_map)

            if match is not None:
                tile_id, flags = match
                unique_tiles[tile_id].reference_count += 1

                if not flags.horizontal_flip and not flags.vertical_flip:
                    flip_stats['direct_match'] += 1
                elif flags.horizontal_flip and not flags.vertical_flip:
                    flip_stats['h_flip_match'] += 1
                elif not flags.horizontal_flip and flags.vertical_flip:
                    flip_stats['v_flip_match'] += 1
                else:
                    flip_stats['hv_flip_match'] += 1

            else:
                # New unique tile
                tile_id = len(unique_tiles)
                tile_hash = self._compute_hash(pixels)
                tile_hash_map[tile_hash] = (tile_id, TileFlags())

                unique_tiles.append(OptimizedTile(
                    tile_id=tile_id,
                    pixels=pixels.copy(),
                    hash=tile_hash,
                    reference_count=1,
                ))
                match = (tile_id, TileFlags())
                flip_stats['unique'] += 1

            tile_map.append(TileRef(
                tile_id=match[0],
                flags=match[1],
                x=x,
                y=y,
            ))

        # Calculate savings
        original_count = len(all_tiles)
        optimized_count = len(unique_tiles)
        savings = 100.0 * (1.0 - optimized_count / original_count) if original_count > 0 else 0.0

        return TileOptimizationResult(
            unique_tiles=unique_tiles,
            tile_map=tile_map,
            original_tile_count=original_count,
            optimized_tile_count=optimized_count,
            savings_percent=savings,
            flip_stats=flip_stats,
        )

    def _to_indexed(
        self,
        image: Image.Image,
        palette: Optional[List[int]] = None,
    ) -> np.ndarray:
        """Convert image to indexed pixel array."""
        if image.mode == 'P':
            # Already indexed
            return np.array(image)

        if image.mode not in ('RGB', 'RGBA'):
            image = image.convert('RGBA')

        arr = np.array(image)

        # Simple quantization to palette indices
        if image.mode == 'RGBA':
            # Use alpha for transparency (index 0)
            alpha = arr[:, :, 3]
            rgb = arr[:, :, :3]

            # Convert to grayscale for simple indexing
            gray = np.mean(rgb, axis=2)

            # Map to palette indices (0-3 for NES)
            indexed = np.zeros(gray.shape, dtype=np.uint8)

            # Index 0 = transparent
            indexed[alpha < 128] = 0

            # Remaining indices based on brightness
            visible = alpha >= 128
            gray_visible = gray[visible]

            if len(gray_visible) > 0:
                # Quantize visible pixels to indices 1-3
                min_g = np.min(gray_visible)
                max_g = np.max(gray_visible)
                if max_g > min_g:
                    normalized = (gray_visible - min_g) / (max_g - min_g)
                    indices = 1 + (normalized * (self.colors_per_palette - 2)).astype(np.uint8)
                    indices = np.clip(indices, 1, self.colors_per_palette - 1)
                else:
                    indices = np.ones_like(gray_visible, dtype=np.uint8)

                indexed[visible] = indices

            return indexed

        else:
            # RGB without alpha
            gray = np.mean(arr, axis=2)
            normalized = gray / 255.0
            indexed = (normalized * (self.colors_per_palette - 1)).astype(np.uint8)
            return indexed

    def _extract_tiles(
        self,
        indexed: np.ndarray,
    ) -> List[Tuple[int, int, np.ndarray]]:
        """Extract all tiles from indexed image."""
        height, width = indexed.shape
        tiles = []

        # Calculate tile grid
        tiles_x = width // self.tile_width
        tiles_y = height // self.tile_height

        for ty in range(tiles_y):
            for tx in range(tiles_x):
                x = tx * self.tile_width
                y = ty * self.tile_height

                tile_pixels = indexed[
                    y:y + self.tile_height,
                    x:x + self.tile_width
                ]

                if tile_pixels.shape == (self.tile_height, self.tile_width):
                    tiles.append((x, y, tile_pixels))

        return tiles

    def _find_match(
        self,
        pixels: np.ndarray,
        hash_map: Dict[str, Tuple[int, TileFlags]],
    ) -> Optional[Tuple[int, TileFlags]]:
        """Find matching tile in hash map, including flipped versions."""

        # Check direct match
        tile_hash = self._compute_hash(pixels)
        if tile_hash in hash_map:
            return hash_map[tile_hash]

        # Check horizontal flip
        if self.enable_h_flip:
            flipped_h = np.fliplr(pixels)
            h_hash = self._compute_hash(flipped_h)
            if h_hash in hash_map:
                orig_id, _ = hash_map[h_hash]
                return (orig_id, TileFlags(horizontal_flip=True))

        # Check vertical flip
        if self.enable_v_flip:
            flipped_v = np.flipud(pixels)
            v_hash = self._compute_hash(flipped_v)
            if v_hash in hash_map:
                orig_id, _ = hash_map[v_hash]
                return (orig_id, TileFlags(vertical_flip=True))

        # Check both flips (180 degree rotation)
        if self.enable_h_flip and self.enable_v_flip:
            flipped_hv = np.flipud(np.fliplr(pixels))
            hv_hash = self._compute_hash(flipped_hv)
            if hv_hash in hash_map:
                orig_id, _ = hash_map[hv_hash]
                return (orig_id, TileFlags(horizontal_flip=True, vertical_flip=True))

        return None

    def _compute_hash(self, pixels: np.ndarray) -> str:
        """Compute unique hash for tile pixels."""
        return hashlib.md5(pixels.tobytes()).hexdigest()

    # -------------------------------------------------------------------------
    # Output Generation
    # -------------------------------------------------------------------------

    def generate_chr(
        self,
        result: TileOptimizationResult,
        bits_per_pixel: int = 2,
    ) -> bytes:
        """
        Generate CHR data from optimized tiles.

        Args:
            result: TileOptimizationResult from optimize()
            bits_per_pixel: Bits per pixel (2 for NES, 4 for Genesis)

        Returns:
            bytes: CHR ROM data
        """
        chr_data = bytearray()

        for tile in result.unique_tiles:
            if bits_per_pixel == 2:
                # NES 2bpp format (16 bytes per tile)
                tile_bytes = self._tile_to_2bpp(tile.pixels)
            elif bits_per_pixel == 4:
                # Genesis/SNES 4bpp format (32 bytes per tile)
                tile_bytes = self._tile_to_4bpp(tile.pixels)
            else:
                raise ValueError(f"Unsupported bits_per_pixel: {bits_per_pixel}")

            chr_data.extend(tile_bytes)

        return bytes(chr_data)

    def generate_tilemap(
        self,
        result: TileOptimizationResult,
        width_tiles: int,
    ) -> Tuple[bytes, bytes]:
        """
        Generate tilemap and attribute data.

        Args:
            result: TileOptimizationResult from optimize()
            width_tiles: Width of tilemap in tiles

        Returns:
            Tuple of (tilemap_data, attribute_data)
        """
        tilemap = bytearray()
        attributes = bytearray()

        for ref in result.tile_map:
            tilemap.append(ref.tile_id & 0xFF)
            attributes.append(ref.flags.to_byte())

        return bytes(tilemap), bytes(attributes)

    def _tile_to_2bpp(self, pixels: np.ndarray) -> bytes:
        """Convert tile to NES 2bpp format."""
        plane0 = []
        plane1 = []

        for row in range(self.tile_height):
            p0_byte = 0
            p1_byte = 0
            for col in range(self.tile_width):
                color_idx = pixels[row, col] & 0x03
                p0_byte |= ((color_idx & 1) << (7 - col))
                p1_byte |= (((color_idx >> 1) & 1) << (7 - col))
            plane0.append(p0_byte)
            plane1.append(p1_byte)

        return bytes(plane0 + plane1)

    def _tile_to_4bpp(self, pixels: np.ndarray) -> bytes:
        """Convert tile to 4bpp format."""
        planes = [[], [], [], []]

        for row in range(self.tile_height):
            for plane_idx in range(4):
                byte_val = 0
                for col in range(self.tile_width):
                    color_idx = pixels[row, col] & 0x0F
                    bit = (color_idx >> plane_idx) & 1
                    byte_val |= (bit << (7 - col))
                planes[plane_idx].append(byte_val)

        # Interleave planes (varies by platform)
        result = []
        for row in range(self.tile_height):
            for plane_idx in range(4):
                result.append(planes[plane_idx][row])

        return bytes(result)


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    """Command-line interface for tile deduplication."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Optimize tiles with deduplication and flip detection'
    )
    parser.add_argument('input', help='Input image file')
    parser.add_argument('-o', '--output', help='Output CHR file')
    parser.add_argument('--tile-width', type=int, default=8)
    parser.add_argument('--tile-height', type=int, default=8)
    parser.add_argument('--no-h-flip', action='store_true', help='Disable H flip detection')
    parser.add_argument('--no-v-flip', action='store_true', help='Disable V flip detection')
    parser.add_argument('--report', action='store_true', help='Print optimization report')

    args = parser.parse_args()

    # Load image
    image = Image.open(args.input)

    # Create deduplicator
    dedup = TileDeduplicator(
        tile_width=args.tile_width,
        tile_height=args.tile_height,
        enable_h_flip=not args.no_h_flip,
        enable_v_flip=not args.no_v_flip,
    )

    # Optimize
    result = dedup.optimize(image)

    # Report
    if args.report or not args.output:
        print(f"Tile Optimization Report")
        print(f"========================")
        print(f"Original tiles:  {result.original_tile_count}")
        print(f"Unique tiles:    {result.optimized_tile_count}")
        print(f"Savings:         {result.savings_percent:.1f}%")
        print()
        print(f"Match breakdown:")
        for key, count in result.flip_stats.items():
            print(f"  {key}: {count}")

    # Output CHR
    if args.output:
        chr_data = dedup.generate_chr(result)
        with open(args.output, 'wb') as f:
            f.write(chr_data)
        print(f"\nWrote {len(chr_data)} bytes to {args.output}")


if __name__ == '__main__':
    main()
