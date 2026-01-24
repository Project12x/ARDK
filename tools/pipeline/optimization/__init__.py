"""
Optimization Module.

Advanced sprite and tile optimization for retro game pipelines.
"""

from .tile_optimizer import (
    TileOptimizer,
    TileReference,
    TileTransform,
    OptimizedTileBank,
    OptimizationStats,
    BatchTileOptimizer,
)

__all__ = [
    'TileOptimizer',
    'TileReference',
    'TileTransform',
    'OptimizedTileBank',
    'OptimizationStats',
    'BatchTileOptimizer',
]
