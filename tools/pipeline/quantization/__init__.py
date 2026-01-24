"""
Quantization module for perceptual color science and accelerated dithering.

This module provides:
- Perceptual color matching (CIEDE2000, CAM02-UCS)
- Optimal palette extraction via k-means clustering
- Numba-accelerated Floyd-Steinberg dithering

Phase: 0.7-0.8 (Foundation)

Usage:
    from tools.pipeline.quantization import (
        find_nearest_perceptual,
        extract_optimal_palette,
        floyd_steinberg_dither,
    )

Dependencies:
    Required: numpy, pillow
    Optional: colour-science (for CIEDE2000), numba (for JIT dithering)
"""

from .perceptual import (
    find_nearest_perceptual,
    find_nearest_rgb,
    extract_optimal_palette,
    rgb_to_lab,
    lab_to_rgb,
    calculate_color_distance,
    PerceptualQuantizer,
)

# Dithering algorithms (always available, numba optional for acceleration)
from .dither_numba import (
    floyd_steinberg_numba,
    ordered_dither_numba,
    atkinson_dither_numba,
    DitherEngine,
    DitherResult,
    dither_image,
    get_available_methods,
    get_bayer_matrix,
    is_numba_available,
    NUMBA_AVAILABLE,
)

__all__ = [
    # Perceptual color matching (Phase 0.7)
    'find_nearest_perceptual',
    'find_nearest_rgb',
    'extract_optimal_palette',
    'rgb_to_lab',
    'lab_to_rgb',
    'calculate_color_distance',
    'PerceptualQuantizer',

    # Dithering algorithms (Phase 0.8)
    'floyd_steinberg_numba',
    'ordered_dither_numba',
    'atkinson_dither_numba',
    'DitherEngine',
    'DitherResult',
    'dither_image',
    'get_available_methods',
    'get_bayer_matrix',
    'is_numba_available',

    # Feature flags
    'NUMBA_AVAILABLE',
]
