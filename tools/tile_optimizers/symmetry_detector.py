"""
Symmetry Detector - Analyze tiles for symmetry properties.

Detects:
- Horizontal symmetry (can use H-flip to recreate)
- Vertical symmetry (can use V-flip to recreate)
- Full symmetry (both H and V)
- Quadrant symmetry (can store 1/4 of tile)

Provides hints for generation prompts and tile optimization.
"""

from dataclasses import dataclass
from typing import List, Tuple
import numpy as np

try:
    from PIL import Image
except ImportError:
    raise ImportError("PIL required: pip install pillow")


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class SymmetryInfo:
    """Symmetry analysis result for a single tile."""
    horizontal_symmetric: bool = False
    vertical_symmetric: bool = False
    fully_symmetric: bool = False
    quadrant_symmetric: bool = False

    # Similarity scores (0.0 - 1.0)
    h_similarity: float = 0.0
    v_similarity: float = 0.0

    # Optimization hints
    can_use_half_storage: bool = False
    can_use_quarter_storage: bool = False

    def __str__(self) -> str:
        parts = []
        if self.fully_symmetric:
            parts.append("FULL")
        elif self.horizontal_symmetric:
            parts.append("H")
        elif self.vertical_symmetric:
            parts.append("V")
        else:
            parts.append("NONE")

        if self.quadrant_symmetric:
            parts.append("(quadrant)")

        return f"Symmetry: {' '.join(parts)}"


@dataclass
class ImageSymmetryReport:
    """Symmetry analysis for an entire image."""
    tile_analyses: List[Tuple[int, int, SymmetryInfo]]
    h_symmetric_count: int = 0
    v_symmetric_count: int = 0
    full_symmetric_count: int = 0
    total_tiles: int = 0

    @property
    def h_symmetric_percent(self) -> float:
        if self.total_tiles == 0:
            return 0.0
        return 100.0 * self.h_symmetric_count / self.total_tiles

    @property
    def v_symmetric_percent(self) -> float:
        if self.total_tiles == 0:
            return 0.0
        return 100.0 * self.v_symmetric_count / self.total_tiles

    def get_optimization_hints(self) -> List[str]:
        """Generate optimization hints based on analysis."""
        hints = []

        if self.h_symmetric_percent > 50:
            hints.append(f"{self.h_symmetric_percent:.0f}% tiles are H-symmetric - "
                        "consider designing for horizontal mirroring")

        if self.v_symmetric_percent > 50:
            hints.append(f"{self.v_symmetric_percent:.0f}% tiles are V-symmetric - "
                        "consider designing for vertical mirroring")

        if self.full_symmetric_count > self.total_tiles * 0.3:
            hints.append(f"{self.full_symmetric_count} tiles are fully symmetric - "
                        "significant storage savings possible")

        return hints


# =============================================================================
# Symmetry Detector
# =============================================================================

class SymmetryDetector:
    """Detect symmetry properties in tiles and images."""

    def __init__(
        self,
        tile_width: int = 8,
        tile_height: int = 8,
        similarity_threshold: float = 0.95,
    ):
        """
        Initialize detector.

        Args:
            tile_width: Width of each tile
            tile_height: Height of each tile
            similarity_threshold: Threshold for considering tiles symmetric (0.0-1.0)
        """
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.threshold = similarity_threshold

    def analyze_tile(self, tile: np.ndarray) -> SymmetryInfo:
        """
        Analyze a single tile for symmetry.

        Args:
            tile: 2D numpy array of pixel indices

        Returns:
            SymmetryInfo with symmetry properties
        """
        # Compute flipped versions
        h_flip = np.fliplr(tile)
        v_flip = np.flipud(tile)

        # Check exact symmetry
        is_h_symmetric = np.array_equal(tile, h_flip)
        is_v_symmetric = np.array_equal(tile, v_flip)
        is_fully_symmetric = is_h_symmetric and is_v_symmetric

        # Compute similarity scores (for near-symmetric tiles)
        h_similarity = self._compute_similarity(tile, h_flip)
        v_similarity = self._compute_similarity(tile, v_flip)

        # Check quadrant symmetry (all 4 quadrants identical)
        is_quadrant_symmetric = False
        if is_fully_symmetric:
            is_quadrant_symmetric = self._check_quadrant_symmetry(tile)

        return SymmetryInfo(
            horizontal_symmetric=is_h_symmetric,
            vertical_symmetric=is_v_symmetric,
            fully_symmetric=is_fully_symmetric,
            quadrant_symmetric=is_quadrant_symmetric,
            h_similarity=h_similarity,
            v_similarity=v_similarity,
            can_use_half_storage=is_h_symmetric or is_v_symmetric,
            can_use_quarter_storage=is_quadrant_symmetric,
        )

    def analyze_image(self, image: Image.Image) -> ImageSymmetryReport:
        """
        Analyze entire image for tile symmetry.

        Args:
            image: PIL Image to analyze

        Returns:
            ImageSymmetryReport with per-tile and aggregate analysis
        """
        # Convert to indexed array
        if image.mode == 'P':
            arr = np.array(image)
        elif image.mode in ('RGB', 'RGBA'):
            arr = np.array(image.convert('L'))  # Grayscale for symmetry check
        else:
            arr = np.array(image.convert('L'))

        height, width = arr.shape
        tiles_x = width // self.tile_width
        tiles_y = height // self.tile_height

        analyses = []
        h_count = 0
        v_count = 0
        full_count = 0

        for ty in range(tiles_y):
            for tx in range(tiles_x):
                x = tx * self.tile_width
                y = ty * self.tile_height

                tile = arr[y:y + self.tile_height, x:x + self.tile_width]

                if tile.shape != (self.tile_height, self.tile_width):
                    continue

                info = self.analyze_tile(tile)
                analyses.append((x, y, info))

                if info.horizontal_symmetric:
                    h_count += 1
                if info.vertical_symmetric:
                    v_count += 1
                if info.fully_symmetric:
                    full_count += 1

        return ImageSymmetryReport(
            tile_analyses=analyses,
            h_symmetric_count=h_count,
            v_symmetric_count=v_count,
            full_symmetric_count=full_count,
            total_tiles=len(analyses),
        )

    def _compute_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute similarity ratio between two tiles (0.0 - 1.0)."""
        if a.shape != b.shape:
            return 0.0
        total = a.size
        matching = np.sum(a == b)
        return matching / total if total > 0 else 0.0

    def _check_quadrant_symmetry(self, tile: np.ndarray) -> bool:
        """Check if all 4 quadrants of tile are identical."""
        h, w = tile.shape
        half_h, half_w = h // 2, w // 2

        if half_h == 0 or half_w == 0:
            return False

        tl = tile[:half_h, :half_w]
        tr = tile[:half_h, half_w:]
        bl = tile[half_h:, :half_w]
        br = tile[half_h:, half_w:]

        # All quadrants should match (accounting for flips)
        return (np.array_equal(tl, np.fliplr(tr)) and
                np.array_equal(tl, np.flipud(bl)) and
                np.array_equal(tl, np.flipud(np.fliplr(br))))

    # -------------------------------------------------------------------------
    # Generation Hints
    # -------------------------------------------------------------------------

    def get_symmetry_prompt_hints(
        self,
        desired_symmetry: str = 'auto',
    ) -> str:
        """
        Get prompt hints for AI generation based on desired symmetry.

        Args:
            desired_symmetry: 'h', 'v', 'full', 'none', or 'auto'

        Returns:
            String to add to generation prompt
        """
        hints = {
            'h': """
SYMMETRY REQUIREMENT: Horizontal symmetry
- Design should be mirrored left-to-right
- Centerline should be visually distinct
- Left half defines the full design
""",
            'v': """
SYMMETRY REQUIREMENT: Vertical symmetry
- Design should be mirrored top-to-bottom
- Horizontal centerline is the mirror axis
""",
            'full': """
SYMMETRY REQUIREMENT: Full symmetry (4-way)
- Design should be mirrored both horizontally and vertically
- Only top-left quadrant needs unique detail
- Very tile-efficient for backgrounds
""",
            'none': """
SYMMETRY: Not required
- Asymmetric design is acceptable
- Focus on visual interest over efficiency
""",
            'auto': """
SYMMETRY HINTS:
- Consider using symmetric designs for repeating elements
- Symmetric tiles reduce memory usage
- For backgrounds: horizontal symmetry often looks good
- For characters: some asymmetry adds personality
""",
        }

        return hints.get(desired_symmetry, hints['auto'])


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    """Command-line interface for symmetry detection."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Analyze image tiles for symmetry'
    )
    parser.add_argument('input', help='Input image file')
    parser.add_argument('--tile-width', type=int, default=8)
    parser.add_argument('--tile-height', type=int, default=8)
    parser.add_argument('--verbose', '-v', action='store_true')

    args = parser.parse_args()

    # Load image
    image = Image.open(args.input)

    # Create detector
    detector = SymmetryDetector(
        tile_width=args.tile_width,
        tile_height=args.tile_height,
    )

    # Analyze
    report = detector.analyze_image(image)

    # Print report
    print(f"Symmetry Analysis Report")
    print(f"========================")
    print(f"Total tiles: {report.total_tiles}")
    print(f"H-symmetric: {report.h_symmetric_count} ({report.h_symmetric_percent:.1f}%)")
    print(f"V-symmetric: {report.v_symmetric_count} ({report.v_symmetric_percent:.1f}%)")
    print(f"Fully symmetric: {report.full_symmetric_count}")
    print()

    hints = report.get_optimization_hints()
    if hints:
        print("Optimization hints:")
        for hint in hints:
            print(f"  - {hint}")
    else:
        print("No significant symmetry detected.")

    if args.verbose:
        print("\nPer-tile analysis:")
        for x, y, info in report.tile_analyses:
            if info.horizontal_symmetric or info.vertical_symmetric:
                print(f"  ({x:3d}, {y:3d}): {info}")


if __name__ == '__main__':
    main()
