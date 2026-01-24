"""
ARDK Tile Optimizers - Tile deduplication and optimization algorithms.

Provides:
- TileDeduplicator: Hash-based tile merging with flip detection
- SymmetryDetector: Analyze tiles for symmetry properties
- TileMapper: Generate tile maps with flip flags
"""

from .tile_deduplicator import (
    TileDeduplicator,
    TileFlags,
    TileRef,
    OptimizedTile,
    TileOptimizationResult,
)
from .symmetry_detector import (
    SymmetryDetector,
    SymmetryInfo,
)

__all__ = [
    'TileDeduplicator',
    'TileFlags',
    'TileRef',
    'OptimizedTile',
    'TileOptimizationResult',
    'SymmetryDetector',
    'SymmetryInfo',
]
