"""
Advanced Tile Optimization Engine.

Handles tile deduplication, flip detection, palette remapping, and VRAM budget tracking
for retro game platforms (Genesis, NES, SNES, etc.).

Usage:
    >>> from pipeline.optimization import TileOptimizer
    >>> optimizer = TileOptimizer(tile_width=8, tile_height=8, allow_mirror_x=True)
    >>> result = optimizer.optimize_image(sprite_image)
    >>> print(f"Reduced from {result.original_tile_count} to {result.unique_tile_count} tiles")
    >>> print(f"VRAM savings: {result.savings_bytes} bytes")
"""

from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from PIL import Image
from dataclasses import dataclass
from enum import IntEnum
import hashlib
import json


class TileTransform(IntEnum):
    """Tile transformation flags."""
    NORMAL = 0
    FLIP_H = 1  # Horizontal flip
    FLIP_V = 2  # Vertical flip
    FLIP_HV = 3  # Both flips (180° rotation)


@dataclass
class TileReference:
    """
    Reference to a tile in the optimized tile bank.

    Attributes:
        index: Index in unique tile list
        transform: Transformation to apply (flip H/V)
        palette: Palette index (for palette remapping)
    """
    index: int
    transform: TileTransform = TileTransform.NORMAL
    palette: int = 0

    @property
    def flip_h(self) -> bool:
        """Horizontal flip flag."""
        return self.transform in (TileTransform.FLIP_H, TileTransform.FLIP_HV)

    @property
    def flip_v(self) -> bool:
        """Vertical flip flag."""
        return self.transform in (TileTransform.FLIP_V, TileTransform.FLIP_HV)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'index': self.index,
            'flip_x': self.flip_h,
            'flip_y': self.flip_v,
            'palette': self.palette,
            'transform': self.transform.name,
        }


@dataclass
class OptimizationStats:
    """Statistics from tile optimization."""
    original_tile_count: int
    unique_tile_count: int
    duplicate_count: int
    h_flip_matches: int
    v_flip_matches: int
    hv_flip_matches: int
    savings_bytes: int
    savings_percent: float
    vram_used_bytes: int
    vram_used_percent: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'original_tiles': self.original_tile_count,
            'unique_tiles': self.unique_tile_count,
            'duplicates_removed': self.duplicate_count,
            'h_flip_matches': self.h_flip_matches,
            'v_flip_matches': self.v_flip_matches,
            'hv_flip_matches': self.hv_flip_matches,
            'savings_bytes': self.savings_bytes,
            'savings_percent': round(self.savings_percent, 2),
            'vram_used_bytes': self.vram_used_bytes,
            'vram_used_percent': round(self.vram_used_percent, 2),
        }

    def __str__(self) -> str:
        """Human-readable statistics."""
        return (
            f"Tile Optimization Results:\n"
            f"  Original Tiles: {self.original_tile_count}\n"
            f"  Unique Tiles: {self.unique_tile_count}\n"
            f"  Duplicates Removed: {self.duplicate_count}\n"
            f"  H-Flip Matches: {self.h_flip_matches}\n"
            f"  V-Flip Matches: {self.v_flip_matches}\n"
            f"  HV-Flip Matches: {self.hv_flip_matches}\n"
            f"  Savings: {self.savings_bytes} bytes ({self.savings_percent:.1f}%)\n"
            f"  VRAM Used: {self.vram_used_bytes} bytes ({self.vram_used_percent:.1f}%)"
        )


@dataclass
class OptimizedTileBank:
    """
    Result of tile optimization.

    Contains unique tiles, tile map for reconstruction, and statistics.
    """
    unique_tiles: List[Image.Image]
    tile_map: List[TileReference]
    grid_width: int  # Original grid dimensions
    grid_height: int
    tile_width: int
    tile_height: int
    stats: OptimizationStats

    @property
    def unique_tile_count(self) -> int:
        """Number of unique tiles."""
        return len(self.unique_tiles)

    def save_tiles(self, output_dir: str, prefix: str = "tile"):
        """
        Save unique tiles as individual images.

        Args:
            output_dir: Directory to save tiles
            prefix: Filename prefix for tiles
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for idx, tile in enumerate(self.unique_tiles):
            tile_path = output_path / f"{prefix}_{idx:04d}.png"
            tile.save(tile_path)

    def save_tile_map(self, output_path: str):
        """
        Save tile map to JSON file.

        Args:
            output_path: Path to save tile map JSON
        """
        tile_map_data = {
            'grid_width': self.grid_width,
            'grid_height': self.grid_height,
            'tile_width': self.tile_width,
            'tile_height': self.tile_height,
            'unique_tile_count': len(self.unique_tiles),
            'tile_map': [ref.to_dict() for ref in self.tile_map],
            'stats': self.stats.to_dict(),
        }

        with open(output_path, 'w') as f:
            json.dump(tile_map_data, f, indent=2)

    def reconstruct_image(self) -> Image.Image:
        """
        Reconstruct original image from optimized tiles.

        Useful for verifying optimization correctness.

        Returns:
            Reconstructed image
        """
        width = self.grid_width * self.tile_width
        height = self.grid_height * self.tile_height
        result = Image.new('RGBA', (width, height), (0, 0, 0, 0))

        for idx, tile_ref in enumerate(self.tile_map):
            row = idx // self.grid_width
            col = idx % self.grid_width
            x = col * self.tile_width
            y = row * self.tile_height

            # Get tile and apply transforms
            tile = self.unique_tiles[tile_ref.index].copy()

            if tile_ref.flip_h:
                tile = tile.transpose(Image.FLIP_LEFT_RIGHT)
            if tile_ref.flip_v:
                tile = tile.transpose(Image.FLIP_TOP_BOTTOM)

            result.paste(tile, (x, y))

        return result


class TileOptimizer:
    """
    Advanced Tile Optimization Engine.

    Features:
    - Tile deduplication (find identical tiles)
    - Flip detection (use H/V flip instead of storing duplicates)
    - Palette remapping (share tiles across sprites)
    - VRAM budget tracking (Genesis: 64KB, NES: 8KB CHR-ROM per bank)

    Usage:
        >>> optimizer = TileOptimizer(tile_width=8, tile_height=8)
        >>> result = optimizer.optimize_image(sprite_sheet)
        >>> print(result.stats)
    """

    # Platform VRAM limits (bytes)
    VRAM_LIMITS = {
        'genesis': 64 * 1024,      # 64KB VRAM
        'nes': 8 * 1024,           # 8KB CHR-ROM per bank
        'snes': 64 * 1024,         # 64KB VRAM
        'gameboy': 8 * 1024,       # 8KB tile data
        'gba': 96 * 1024,          # 96KB tile VRAM
    }

    def __init__(self,
                 tile_width: int = 8,
                 tile_height: int = 8,
                 allow_mirror_x: bool = True,
                 allow_mirror_y: bool = True,
                 platform: str = 'genesis',
                 vram_budget: Optional[int] = None):
        """
        Initialize tile optimizer.

        Args:
            tile_width: Tile width in pixels (typically 8)
            tile_height: Tile height in pixels (typically 8)
            allow_mirror_x: Allow horizontal flip for matching
            allow_mirror_y: Allow vertical flip for matching
            platform: Target platform for VRAM limits
            vram_budget: Override VRAM budget (bytes)
        """
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.allow_mirror_x = allow_mirror_x
        self.allow_mirror_y = allow_mirror_y
        self.platform = platform.lower()

        # Set VRAM budget
        if vram_budget is not None:
            self.vram_budget = vram_budget
        else:
            self.vram_budget = self.VRAM_LIMITS.get(self.platform, 64 * 1024)

        # Statistics tracking
        self._h_flip_count = 0
        self._v_flip_count = 0
        self._hv_flip_count = 0

    def optimize_image(self, img: Image.Image) -> OptimizedTileBank:
        """
        Optimize a sprite sheet by deduplicating tiles.

        Args:
            img: Input image to optimize

        Returns:
            OptimizedTileBank with unique tiles and tile map

        Example:
            >>> optimizer = TileOptimizer()
            >>> result = optimizer.optimize_image(sprite_sheet)
            >>> print(f"Saved {result.stats.savings_bytes} bytes")
        """
        # Convert to RGBA for consistent processing
        img = img.convert('RGBA')
        width, height = img.size

        # Pad to tile grid if needed
        padded_img, padded_width, padded_height = self._pad_to_grid(img, width, height)

        # Calculate grid dimensions
        grid_width = padded_width // self.tile_width
        grid_height = padded_height // self.tile_height
        total_tiles = grid_width * grid_height

        # Reset statistics
        self._h_flip_count = 0
        self._v_flip_count = 0
        self._hv_flip_count = 0

        # Extract and deduplicate tiles
        unique_tiles = []
        tile_map = []
        seen_hashes = {}  # Hash -> (index, transform)

        for row in range(grid_height):
            for col in range(grid_width):
                # Extract tile
                x = col * self.tile_width
                y = row * self.tile_height
                tile = padded_img.crop((x, y, x + self.tile_width, y + self.tile_height))

                # Try to find existing match
                tile_ref = self._find_tile_match(tile, unique_tiles, seen_hashes)

                if tile_ref is None:
                    # New unique tile
                    idx = len(unique_tiles)
                    unique_tiles.append(tile)
                    tile_hash = self._hash_tile(tile)
                    seen_hashes[tile_hash] = (idx, TileTransform.NORMAL)
                    tile_ref = TileReference(idx, TileTransform.NORMAL)

                tile_map.append(tile_ref)

        # Calculate statistics
        stats = self._calculate_stats(total_tiles, len(unique_tiles))

        return OptimizedTileBank(
            unique_tiles=unique_tiles,
            tile_map=tile_map,
            grid_width=grid_width,
            grid_height=grid_height,
            tile_width=self.tile_width,
            tile_height=self.tile_height,
            stats=stats,
        )

    def optimize_sprite_sheet(self, image_path: str) -> OptimizedTileBank:
        """
        Optimize a sprite sheet from file path.

        Args:
            image_path: Path to sprite sheet image

        Returns:
            OptimizedTileBank
        """
        img = Image.open(image_path)
        return self.optimize_image(img)

    def _pad_to_grid(self, img: Image.Image, width: int, height: int) -> Tuple[Image.Image, int, int]:
        """Pad image to tile grid alignment."""
        new_width = ((width + self.tile_width - 1) // self.tile_width) * self.tile_width
        new_height = ((height + self.tile_height - 1) // self.tile_height) * self.tile_height

        if new_width != width or new_height != height:
            padded = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))
            padded.paste(img, (0, 0))
            return padded, new_width, new_height

        return img, width, height

    def _hash_tile(self, tile: Image.Image) -> str:
        """Generate hash of tile pixels."""
        return hashlib.sha256(tile.tobytes()).hexdigest()

    def _find_tile_match(self,
                        tile: Image.Image,
                        unique_tiles: List[Image.Image],
                        seen_hashes: Dict[str, Tuple[int, TileTransform]]) -> Optional[TileReference]:
        """
        Find matching tile in unique tiles list.

        Checks for exact match, then horizontal flip, vertical flip, and both flips.

        Returns:
            TileReference if match found, None otherwise
        """
        # 1. Check exact match
        tile_hash = self._hash_tile(tile)
        if tile_hash in seen_hashes:
            idx, transform = seen_hashes[tile_hash]
            return TileReference(idx, transform)

        # 2. Check horizontal flip
        if self.allow_mirror_x:
            h_tile = tile.transpose(Image.FLIP_LEFT_RIGHT)
            h_hash = self._hash_tile(h_tile)
            if h_hash in seen_hashes:
                idx, _ = seen_hashes[h_hash]
                self._h_flip_count += 1
                return TileReference(idx, TileTransform.FLIP_H)

        # 3. Check vertical flip
        if self.allow_mirror_y:
            v_tile = tile.transpose(Image.FLIP_TOP_BOTTOM)
            v_hash = self._hash_tile(v_tile)
            if v_hash in seen_hashes:
                idx, _ = seen_hashes[v_hash]
                self._v_flip_count += 1
                return TileReference(idx, TileTransform.FLIP_V)

        # 4. Check both flips (180° rotation)
        if self.allow_mirror_x and self.allow_mirror_y:
            hv_tile = tile.transpose(Image.ROTATE_180)
            hv_hash = self._hash_tile(hv_tile)
            if hv_hash in seen_hashes:
                idx, _ = seen_hashes[hv_hash]
                self._hv_flip_count += 1
                return TileReference(idx, TileTransform.FLIP_HV)

        return None

    def _calculate_stats(self, original_count: int, unique_count: int) -> OptimizationStats:
        """Calculate optimization statistics."""
        duplicate_count = original_count - unique_count

        # Calculate bytes per tile (RGBA = 4 bytes per pixel)
        bytes_per_tile = self.tile_width * self.tile_height * 4

        # Calculate savings
        original_bytes = original_count * bytes_per_tile
        optimized_bytes = unique_count * bytes_per_tile
        savings_bytes = original_bytes - optimized_bytes
        savings_percent = (savings_bytes / original_bytes * 100) if original_bytes > 0 else 0.0

        # Calculate VRAM usage
        vram_used_percent = (optimized_bytes / self.vram_budget * 100) if self.vram_budget > 0 else 0.0

        return OptimizationStats(
            original_tile_count=original_count,
            unique_tile_count=unique_count,
            duplicate_count=duplicate_count,
            h_flip_matches=self._h_flip_count,
            v_flip_matches=self._v_flip_count,
            hv_flip_matches=self._hv_flip_count,
            savings_bytes=savings_bytes,
            savings_percent=savings_percent,
            vram_used_bytes=optimized_bytes,
            vram_used_percent=vram_used_percent,
        )

    def check_vram_budget(self, tile_count: int) -> Tuple[bool, int, int]:
        """
        Check if tile count fits within VRAM budget.

        Args:
            tile_count: Number of unique tiles

        Returns:
            (fits_in_budget, used_bytes, available_bytes)
        """
        bytes_per_tile = self.tile_width * self.tile_height * 4
        used_bytes = tile_count * bytes_per_tile
        fits = used_bytes <= self.vram_budget

        return fits, used_bytes, self.vram_budget

    def get_max_tiles_for_budget(self) -> int:
        """
        Get maximum number of tiles that fit in VRAM budget.

        Returns:
            Maximum tile count
        """
        bytes_per_tile = self.tile_width * self.tile_height * 4
        return self.vram_budget // bytes_per_tile


# =============================================================================
# Batch Processing
# =============================================================================

class BatchTileOptimizer:
    """
    Batch optimize multiple sprite sheets.

    Usage:
        >>> batch = BatchTileOptimizer(platform='genesis')
        >>> results = batch.optimize_directory('assets/sprites')
        >>> batch.print_summary()
    """

    def __init__(self, **optimizer_kwargs):
        """
        Initialize batch optimizer.

        Args:
            **optimizer_kwargs: Arguments passed to TileOptimizer
        """
        self.optimizer = TileOptimizer(**optimizer_kwargs)
        self.results: List[Tuple[str, OptimizedTileBank]] = []

    def optimize_directory(self, input_dir: str, pattern: str = "*.png") -> List[OptimizedTileBank]:
        """
        Optimize all images in directory.

        Args:
            input_dir: Directory containing sprite sheets
            pattern: Glob pattern for image files

        Returns:
            List of OptimizedTileBank results
        """
        input_path = Path(input_dir)
        image_files = list(input_path.glob(pattern))

        results = []
        for image_file in image_files:
            print(f"Optimizing {image_file.name}...")
            result = self.optimizer.optimize_sprite_sheet(str(image_file))
            results.append(result)
            self.results.append((image_file.name, result))
            print(f"  {result.stats.unique_tile_count} unique tiles "
                  f"({result.stats.savings_percent:.1f}% savings)")

        return results

    def print_summary(self):
        """Print summary of all optimizations."""
        if not self.results:
            print("No optimization results yet.")
            return

        total_original = sum(r.stats.original_tile_count for _, r in self.results)
        total_unique = sum(r.stats.unique_tile_count for _, r in self.results)
        total_savings = sum(r.stats.savings_bytes for _, r in self.results)

        print("\n" + "=" * 60)
        print("Batch Tile Optimization Summary")
        print("=" * 60)
        print(f"Files Processed: {len(self.results)}")
        print(f"Total Original Tiles: {total_original}")
        print(f"Total Unique Tiles: {total_unique}")
        print(f"Total Duplicates Removed: {total_original - total_unique}")
        print(f"Total Savings: {total_savings} bytes ({total_savings / 1024:.1f} KB)")
        print("=" * 60)

        for filename, result in self.results:
            print(f"\n{filename}:")
            print(f"  Tiles: {result.stats.original_tile_count} -> {result.stats.unique_tile_count}")
            print(f"  Savings: {result.stats.savings_bytes} bytes ({result.stats.savings_percent:.1f}%)")
