#!/usr/bin/env python3
"""
NES Dithering Module - Gradient-Aware Color Quantization
Part of the Agentic Retro Development Kit (ARDK)

This module provides NES-appropriate dithering algorithms that preserve
the perception of gradients while respecting the 4-color-per-sprite limit.

Dithering Methods:
  - ordered: Bayer matrix dithering (classic retro look, predictable patterns)
  - floyd:   Floyd-Steinberg error diffusion (smoother, but can be noisy)
  - none:    Nearest color only (sharp edges, no gradient simulation)

The NES PPU renders sprites at 256x240, so dithering patterns need to be
visible at that resolution. We use 2x2 or 4x4 Bayer matrices.

Usage:
    from nes_dither import dither_to_nes_palette, DITHER_ORDERED, DITHER_FLOYD

    # Dither an RGBA image to 4-color indexed
    indexed, palette = dither_to_nes_palette(img, method=DITHER_ORDERED)
"""

import numpy as np
from PIL import Image
from typing import List, Tuple, Optional

# Dithering method constants
DITHER_NONE = 'none'
DITHER_ORDERED = 'ordered'      # Bayer matrix
DITHER_FLOYD = 'floyd'          # Floyd-Steinberg
DITHER_ATKINSON = 'atkinson'    # Atkinson (lighter, Mac-style)

# NES Master Palette (2C02 PPU - NTSC)
NES_PALETTE = {
    0x00: (84, 84, 84),    0x01: (0, 30, 116),    0x02: (8, 16, 144),    0x03: (48, 0, 136),
    0x04: (68, 0, 100),    0x05: (92, 0, 48),     0x06: (84, 4, 0),      0x07: (60, 24, 0),
    0x08: (32, 42, 0),     0x09: (8, 58, 0),      0x0A: (0, 64, 0),      0x0B: (0, 60, 0),
    0x0C: (0, 50, 60),     0x0D: (0, 0, 0),       0x0E: (0, 0, 0),       0x0F: (0, 0, 0),
    0x10: (152, 150, 152), 0x11: (8, 76, 196),    0x12: (48, 50, 236),   0x13: (92, 30, 228),
    0x14: (136, 20, 176),  0x15: (160, 20, 100),  0x16: (152, 34, 32),   0x17: (120, 60, 0),
    0x18: (84, 90, 0),     0x19: (40, 114, 0),    0x1A: (8, 124, 0),     0x1B: (0, 118, 40),
    0x1C: (0, 102, 120),   0x1D: (0, 0, 0),       0x1E: (0, 0, 0),       0x1F: (0, 0, 0),
    0x20: (236, 238, 236), 0x21: (76, 154, 236),  0x22: (120, 124, 236), 0x23: (176, 98, 236),
    0x24: (228, 84, 236),  0x25: (236, 88, 180),  0x26: (236, 106, 100), 0x27: (212, 136, 32),
    0x28: (160, 170, 0),   0x29: (116, 196, 0),   0x2A: (76, 208, 32),   0x2B: (56, 204, 108),
    0x2C: (56, 180, 204),  0x2D: (60, 60, 60),    0x2E: (0, 0, 0),       0x2F: (0, 0, 0),
    0x30: (236, 238, 236), 0x31: (168, 204, 236), 0x32: (188, 188, 236), 0x33: (212, 178, 236),
    0x34: (236, 174, 236), 0x35: (236, 174, 212), 0x36: (236, 180, 176), 0x37: (228, 196, 144),
    0x38: (204, 210, 120), 0x39: (180, 222, 120), 0x3A: (168, 226, 144), 0x3B: (152, 226, 180),
    0x3C: (160, 214, 228), 0x3D: (160, 162, 160), 0x3E: (0, 0, 0),       0x3F: (0, 0, 0),
}

# 2x2 Bayer matrix (good for small sprites)
BAYER_2X2 = np.array([
    [0, 2],
    [3, 1]
]) / 4.0 - 0.5

# 4x4 Bayer matrix (better gradient representation)
BAYER_4X4 = np.array([
    [ 0,  8,  2, 10],
    [12,  4, 14,  6],
    [ 3, 11,  1,  9],
    [15,  7, 13,  5]
]) / 16.0 - 0.5

# 8x8 Bayer matrix (smoothest gradients, may be too fine for NES)
BAYER_8X8 = np.array([
    [ 0, 32,  8, 40,  2, 34, 10, 42],
    [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44,  4, 36, 14, 46,  6, 38],
    [60, 28, 52, 20, 62, 30, 54, 22],
    [ 3, 35, 11, 43,  1, 33,  9, 41],
    [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47,  7, 39, 13, 45,  5, 37],
    [63, 31, 55, 23, 61, 29, 53, 21]
]) / 64.0 - 0.5


def rgb_distance(c1: Tuple[int, int, int], c2: Tuple[int, int, int]) -> float:
    """Calculate perceptual color distance (simple Euclidean in RGB space)"""
    return ((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2 + (c1[2] - c2[2]) ** 2) ** 0.5


def rgb_to_nes_index(r: int, g: int, b: int) -> int:
    """Find closest NES palette color"""
    min_dist = float('inf')
    best_idx = 0x0F
    for idx, (pr, pg, pb) in NES_PALETTE.items():
        dist = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2
        if dist < min_dist:
            min_dist = dist
            best_idx = idx
    return best_idx


def extract_best_palette(img: Image.Image, num_colors: int = 4) -> List[int]:
    """
    Extract the best NES palette for an image using color frequency analysis.

    Returns list of NES color indices, with index 0 always being transparent (0x0F).
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    pixels = np.array(img)
    height, width = pixels.shape[:2]

    # Count NES color frequencies (ignoring transparent pixels)
    color_counts = {}
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[y, x]
            if a < 128:
                continue
            nes_idx = rgb_to_nes_index(r, g, b)
            color_counts[nes_idx] = color_counts.get(nes_idx, 0) + 1

    # Sort by frequency
    sorted_colors = sorted(color_counts.items(), key=lambda x: -x[1])

    # Build palette: index 0 = transparent, rest = most frequent colors
    palette = [0x0F]  # Transparent
    for idx, _ in sorted_colors:
        if idx != 0x0F and len(palette) < num_colors:
            palette.append(idx)

    # Pad if needed
    while len(palette) < num_colors:
        palette.append(0x0F)

    return palette


def find_closest_palette_index(r: int, g: int, b: int, palette: List[int]) -> int:
    """Find the index in palette closest to the given RGB color"""
    min_dist = float('inf')
    best_idx = 0
    for i, nes_idx in enumerate(palette):
        pr, pg, pb = NES_PALETTE[nes_idx]
        dist = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2
        if dist < min_dist:
            min_dist = dist
            best_idx = i
    return best_idx


def dither_ordered(img: Image.Image, palette: List[int],
                   matrix_size: int = 4, strength: float = 1.0) -> Image.Image:
    """
    Apply ordered (Bayer) dithering to image.

    Args:
        img: RGBA source image
        palette: List of 4 NES color indices
        matrix_size: 2, 4, or 8 for Bayer matrix size
        strength: Dithering strength (0.0-2.0, default 1.0)

    Returns:
        Indexed image with values 0-3
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # Select Bayer matrix
    if matrix_size == 2:
        bayer = BAYER_2X2
    elif matrix_size == 8:
        bayer = BAYER_8X8
    else:
        bayer = BAYER_4X4

    pixels = np.array(img, dtype=np.float32)
    height, width = pixels.shape[:2]

    # Get palette RGB values
    palette_rgb = np.array([NES_PALETTE[idx] for idx in palette], dtype=np.float32)

    # Create output
    indexed = Image.new('L', (width, height), 0)
    out_pixels = indexed.load()

    # Dither strength scales the threshold matrix
    dither_scale = 64.0 * strength  # Scale factor for color adjustment

    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[y, x]

            if a < 128:
                out_pixels[x, y] = 0  # Transparent
                continue

            # Get Bayer threshold for this pixel
            threshold = bayer[y % bayer.shape[0], x % bayer.shape[1]]

            # Adjust color based on threshold
            r_adj = r + threshold * dither_scale
            g_adj = g + threshold * dither_scale
            b_adj = b + threshold * dither_scale

            # Clamp
            r_adj = max(0, min(255, r_adj))
            g_adj = max(0, min(255, g_adj))
            b_adj = max(0, min(255, b_adj))

            # Find closest palette color
            out_pixels[x, y] = find_closest_palette_index(int(r_adj), int(g_adj), int(b_adj), palette)

    return indexed


def dither_floyd_steinberg(img: Image.Image, palette: List[int]) -> Image.Image:
    """
    Apply Floyd-Steinberg error diffusion dithering.

    This produces smoother gradients but can create noise in uniform areas.
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    pixels = np.array(img, dtype=np.float32)
    height, width = pixels.shape[:2]

    # Get palette RGB values
    palette_rgb = [NES_PALETTE[idx] for idx in palette]

    # Create output
    indexed = Image.new('L', (width, height), 0)
    out_pixels = indexed.load()

    # Error buffer
    error = np.zeros((height + 1, width + 1, 3), dtype=np.float32)

    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[y, x]

            if a < 128:
                out_pixels[x, y] = 0
                continue

            # Add accumulated error
            r = max(0, min(255, r + error[y, x, 0]))
            g = max(0, min(255, g + error[y, x, 1]))
            b = max(0, min(255, b + error[y, x, 2]))

            # Find closest palette color
            best_idx = find_closest_palette_index(int(r), int(g), int(b), palette)
            out_pixels[x, y] = best_idx

            # Calculate error
            pr, pg, pb = palette_rgb[best_idx]
            err_r = r - pr
            err_g = g - pg
            err_b = b - pb

            # Distribute error (Floyd-Steinberg pattern)
            # X * 7
            # 3 5 1  (all /16)
            if x + 1 < width:
                error[y, x + 1, 0] += err_r * 7 / 16
                error[y, x + 1, 1] += err_g * 7 / 16
                error[y, x + 1, 2] += err_b * 7 / 16
            if y + 1 < height:
                if x > 0:
                    error[y + 1, x - 1, 0] += err_r * 3 / 16
                    error[y + 1, x - 1, 1] += err_g * 3 / 16
                    error[y + 1, x - 1, 2] += err_b * 3 / 16
                error[y + 1, x, 0] += err_r * 5 / 16
                error[y + 1, x, 1] += err_g * 5 / 16
                error[y + 1, x, 2] += err_b * 5 / 16
                if x + 1 < width:
                    error[y + 1, x + 1, 0] += err_r * 1 / 16
                    error[y + 1, x + 1, 1] += err_g * 1 / 16
                    error[y + 1, x + 1, 2] += err_b * 1 / 16

    return indexed


def dither_atkinson(img: Image.Image, palette: List[int]) -> Image.Image:
    """
    Apply Atkinson dithering (lighter than Floyd-Steinberg).

    Only diffuses 6/8 of the error, which preserves more contrast.
    Good for high-contrast retro sprites.
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    pixels = np.array(img, dtype=np.float32)
    height, width = pixels.shape[:2]

    palette_rgb = [NES_PALETTE[idx] for idx in palette]

    indexed = Image.new('L', (width, height), 0)
    out_pixels = indexed.load()

    error = np.zeros((height + 2, width + 2, 3), dtype=np.float32)

    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[y, x]

            if a < 128:
                out_pixels[x, y] = 0
                continue

            r = max(0, min(255, r + error[y, x, 0]))
            g = max(0, min(255, g + error[y, x, 1]))
            b = max(0, min(255, b + error[y, x, 2]))

            best_idx = find_closest_palette_index(int(r), int(g), int(b), palette)
            out_pixels[x, y] = best_idx

            pr, pg, pb = palette_rgb[best_idx]
            err_r = (r - pr) / 8  # Only diffuse 6/8 total
            err_g = (g - pg) / 8
            err_b = (b - pb) / 8

            # Atkinson pattern:
            #     X 1 1
            #   1 1 1
            #     1
            if x + 1 < width:
                error[y, x + 1] += [err_r, err_g, err_b]
            if x + 2 < width:
                error[y, x + 2] += [err_r, err_g, err_b]
            if y + 1 < height:
                if x > 0:
                    error[y + 1, x - 1] += [err_r, err_g, err_b]
                error[y + 1, x] += [err_r, err_g, err_b]
                if x + 1 < width:
                    error[y + 1, x + 1] += [err_r, err_g, err_b]
            if y + 2 < height:
                error[y + 2, x] += [err_r, err_g, err_b]

    return indexed


def dither_to_nes_palette(
    img: Image.Image,
    palette: Optional[List[int]] = None,
    method: str = DITHER_ORDERED,
    matrix_size: int = 4,
    strength: float = 1.0
) -> Tuple[Image.Image, List[int]]:
    """
    Dither an image to NES 4-color palette.

    Args:
        img: Source image (RGBA)
        palette: Optional fixed NES palette indices (4 values)
        method: Dithering method (none, ordered, floyd, atkinson)
        matrix_size: For ordered dithering, Bayer matrix size (2, 4, 8)
        strength: Dithering strength for ordered method

    Returns:
        Tuple of (indexed image with values 0-3, palette indices used)
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # Extract or use provided palette
    if palette is None:
        palette = extract_best_palette(img, 4)

    # Apply dithering
    if method == DITHER_NONE:
        # Simple nearest-color quantization
        pixels = np.array(img)
        height, width = pixels.shape[:2]
        indexed = Image.new('L', (width, height), 0)
        out_pixels = indexed.load()
        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[y, x]
                if a < 128:
                    out_pixels[x, y] = 0
                else:
                    out_pixels[x, y] = find_closest_palette_index(r, g, b, palette)
    elif method == DITHER_ORDERED:
        indexed = dither_ordered(img, palette, matrix_size, strength)
    elif method == DITHER_FLOYD:
        indexed = dither_floyd_steinberg(img, palette)
    elif method == DITHER_ATKINSON:
        indexed = dither_atkinson(img, palette)
    else:
        raise ValueError(f"Unknown dithering method: {method}")

    return indexed, palette


def create_preview(indexed: Image.Image, palette: List[int]) -> Image.Image:
    """Create an RGB preview of the indexed image using NES colors"""
    width, height = indexed.size
    preview = Image.new('RGB', (width, height))

    in_pixels = indexed.load()
    out_pixels = preview.load()

    for y in range(height):
        for x in range(width):
            idx = in_pixels[x, y]
            nes_idx = palette[idx] if idx < len(palette) else 0x0F
            out_pixels[x, y] = NES_PALETTE[nes_idx]

    return preview


# =============================================================================
# Command-line interface
# =============================================================================

if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description='NES Dithering Tool - Convert images to 4-color NES palette',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Dithering Methods:
  none      - Simple nearest-color (sharp edges, no gradient simulation)
  ordered   - Bayer matrix dithering (classic retro look, default)
  floyd     - Floyd-Steinberg error diffusion (smoother gradients)
  atkinson  - Atkinson dithering (high contrast, lighter diffusion)

Examples:
  # Convert with ordered dithering (recommended for NES)
  python nes_dither.py sprite.png -o sprite_dithered.png --method ordered

  # Convert with specific palette
  python nes_dither.py sprite.png -o sprite.png --palette 0F,16,27,30

  # Compare all methods
  python nes_dither.py sprite.png -o output/ --compare
        """
    )

    parser.add_argument('input', help='Input image file')
    parser.add_argument('-o', '--output', required=True, help='Output file or directory')
    parser.add_argument('--method', choices=['none', 'ordered', 'floyd', 'atkinson'],
                        default='ordered', help='Dithering method')
    parser.add_argument('--palette', help='NES palette indices (e.g., 0F,16,27,30)')
    parser.add_argument('--matrix', type=int, choices=[2, 4, 8], default=4,
                        help='Bayer matrix size for ordered dithering')
    parser.add_argument('--strength', type=float, default=1.0,
                        help='Dithering strength (0.0-2.0)')
    parser.add_argument('--compare', action='store_true',
                        help='Generate comparison of all methods')
    parser.add_argument('--preview', action='store_true',
                        help='Save RGB preview alongside indexed output')

    args = parser.parse_args()

    # Load image
    try:
        img = Image.open(args.input).convert('RGBA')
    except Exception as e:
        print(f"Error loading image: {e}")
        sys.exit(1)

    # Parse palette
    palette = None
    if args.palette:
        try:
            palette = [int(x, 16) for x in args.palette.split(',')]
            if len(palette) != 4:
                print("Palette must have exactly 4 colors")
                sys.exit(1)
        except ValueError:
            print(f"Invalid palette format: {args.palette}")
            sys.exit(1)

    print(f"NES Dithering Tool")
    print(f"==================")
    print(f"Input: {args.input} ({img.size[0]}x{img.size[1]})")

    if args.compare:
        # Compare all methods
        import os
        os.makedirs(args.output, exist_ok=True)

        methods = [DITHER_NONE, DITHER_ORDERED, DITHER_FLOYD, DITHER_ATKINSON]

        for method in methods:
            indexed, pal = dither_to_nes_palette(img, palette, method,
                                                  args.matrix, args.strength)
            preview = create_preview(indexed, pal)

            out_path = os.path.join(args.output, f"{method}.png")
            preview.save(out_path)
            print(f"  {method}: {out_path}")

        print(f"\nPalette used: {', '.join(f'${x:02X}' for x in pal)}")
    else:
        # Single conversion
        indexed, pal = dither_to_nes_palette(img, palette, args.method,
                                              args.matrix, args.strength)

        # Save indexed image
        indexed.save(args.output)
        print(f"Output: {args.output}")

        if args.preview:
            preview = create_preview(indexed, pal)
            preview_path = args.output.replace('.png', '_preview.png')
            preview.save(preview_path)
            print(f"Preview: {preview_path}")

        print(f"Palette: {', '.join(f'${x:02X}' for x in pal)}")
        print(f"Method: {args.method}")
