"""
Platform-specific color palettes.

Each palette is a list of 16 RGB tuples.
Index 0 is always the transparency color (magenta for Genesis).

Usage:
    from pipeline.palettes import get_genesis_palette, GENESIS_PALETTES

    # Get a predefined palette
    palette = get_genesis_palette("player_warm")

    # Use with SGDKFormatter
    from pipeline.sgdk_format import SGDKFormatter
    formatter = SGDKFormatter(target_palette=palette)
"""

from .genesis_palettes import (
    GENESIS_PALETTES,
    get_genesis_palette,
    snap_to_genesis_color,
    extract_palette,
    TRANSPARENT,
)

__all__ = [
    "GENESIS_PALETTES",
    "get_genesis_palette",
    "snap_to_genesis_color",
    "extract_palette",
    "TRANSPARENT",
]
