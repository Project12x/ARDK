#!/usr/bin/env python3
"""
Background Removal for NES Sprite Extraction

NES sprites:
- Index 0 is ALWAYS transparent
- Only 3 actual colors available (indices 1, 2, 3)
- Need to identify and remove background before conversion

Methods:
1. Chroma key (remove specific color like green/magenta)
2. Edge detection (find sprite bounds, make outside transparent)
3. Brightness threshold (make dark pixels transparent)
"""

import sys
from PIL import Image
import argparse

def remove_background_chroma(img, chroma_color=(0, 0, 0), tolerance=30):
    """
    Remove background by chroma key (color matching)

    Args:
        img: PIL Image (RGB)
        chroma_color: RGB tuple of background color to remove
        tolerance: How close colors need to be to match (0-255)
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    pixels = img.load()
    width, height = img.size

    removed_count = 0
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]

            # Check if pixel is close to chroma color
            cr, cg, cb = chroma_color
            diff = abs(r - cr) + abs(g - cg) + abs(b - cb)

            if diff <= tolerance:
                pixels[x, y] = (0, 0, 0, 0)  # Make transparent
                removed_count += 1

    print(f"  Removed {removed_count}/{width*height} pixels ({100*removed_count/(width*height):.1f}%)")
    return img

def remove_background_brightness(img, threshold=50):
    """
    Remove dark pixels (assume dark = background)

    Good for sprites on black/dark backgrounds
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    pixels = img.load()
    width, height = img.size

    removed_count = 0
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            brightness = (r + g + b) / 3

            if brightness <= threshold:
                pixels[x, y] = (0, 0, 0, 0)  # Make transparent
                removed_count += 1

    print(f"  Removed {removed_count}/{width*height} pixels ({100*removed_count/(width*height):.1f}%)")
    return img

def remove_background_edges(img, margin=2):
    """
    Flood-fill from edges to remove background

    Assumes:
    - Background connects to image edges
    - Sprites are in the center, not touching edges
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    pixels = img.load()
    width, height = img.size

    # Get edge color (sample from corners)
    edge_color = pixels[0, 0][:3]  # Top-left corner
    print(f"  Edge color: RGB{edge_color}")

    # Flood fill from all edges
    to_check = set()

    # Add all edge pixels
    for x in range(width):
        to_check.add((x, 0))  # Top edge
        to_check.add((x, height-1))  # Bottom edge
    for y in range(height):
        to_check.add((0, y))  # Left edge
        to_check.add((width-1, y))  # Right edge

    visited = set()
    removed_count = 0
    tolerance = 40

    while to_check:
        x, y = to_check.pop()

        if (x, y) in visited:
            continue
        if x < 0 or x >= width or y < 0 or y >= height:
            continue

        visited.add((x, y))

        r, g, b, a = pixels[x, y]
        er, eg, eb = edge_color

        # Check if similar to edge color
        diff = abs(r - er) + abs(g - eg) + abs(b - eb)

        if diff <= tolerance:
            pixels[x, y] = (0, 0, 0, 0)  # Make transparent
            removed_count += 1

            # Check neighbors
            to_check.add((x+1, y))
            to_check.add((x-1, y))
            to_check.add((x, y+1))
            to_check.add((x, y-1))

    print(f"  Removed {removed_count}/{width*height} pixels ({100*removed_count/(width*height):.1f}%)")
    return img

def main():
    parser = argparse.ArgumentParser(description='Remove background from sprite images')
    parser.add_argument('input', help='Input PNG file')
    parser.add_argument('output', help='Output PNG file (with alpha)')
    parser.add_argument('--method', choices=['chroma', 'brightness', 'edges'], default='edges',
                       help='Background removal method')
    parser.add_argument('--threshold', type=int, default=50,
                       help='Brightness threshold (for brightness method)')
    parser.add_argument('--tolerance', type=int, default=30,
                       help='Color tolerance (for chroma method)')

    args = parser.parse_args()

    print(f"[REMOVING BACKGROUND] {args.input}")
    print(f"  Method: {args.method}")

    img = Image.open(args.input)
    print(f"  Original: {img.size[0]}x{img.size[1]} ({img.mode})")

    if args.method == 'chroma':
        # Remove black background by default
        img_clean = remove_background_chroma(img, chroma_color=(0, 0, 0), tolerance=args.tolerance)
    elif args.method == 'brightness':
        img_clean = remove_background_brightness(img, threshold=args.threshold)
    elif args.method == 'edges':
        img_clean = remove_background_edges(img)

    img_clean.save(args.output, 'PNG')
    print(f"  [OK] Saved: {args.output}")

if __name__ == '__main__':
    main()
