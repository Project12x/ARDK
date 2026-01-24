#!/usr/bin/env python3
"""
NEON SURVIVORS - AI Asset Processing (Fixed Version)
Properly converts AI-generated PNG assets to NES-compatible indexed format
"""

import os
import sys
from PIL import Image
import argparse

def smart_quantize_4color(img):
    """
    Intelligently reduce image to 4 colors based on actual color distribution

    Instead of fixed brightness thresholds, this:
    1. Finds the most common colors in the image
    2. Clusters them into 4 groups
    3. Maps to NES-friendly palette
    """
    # Convert to RGB
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # Get all pixels
    pixels = list(img.getdata())

    # Find brightness range
    brightnesses = [(r+g+b)/3 for r,g,b in pixels]
    min_bright = min(brightnesses)
    max_bright = max(brightnesses)
    bright_range = max_bright - min_bright

    print(f"    Brightness range: {min_bright:.1f} - {max_bright:.1f}")

    # If image is too dark/uniform, adjust thresholds
    if bright_range < 50:
        print("    Warning: Low contrast image, adjusting thresholds")
        # Use percentiles instead of fixed values
        sorted_bright = sorted(brightnesses)
        threshold_1 = sorted_bright[len(sorted_bright)//4]
        threshold_2 = sorted_bright[len(sorted_bright)//2]
        threshold_3 = sorted_bright[3*len(sorted_bright)//4]
    else:
        # Normal thresholds based on range
        threshold_1 = min_bright + bright_range * 0.25
        threshold_2 = min_bright + bright_range * 0.50
        threshold_3 = min_bright + bright_range * 0.75

    print(f"    Using thresholds: {threshold_1:.1f}, {threshold_2:.1f}, {threshold_3:.1f}")

    # Map pixels to 4 color indices
    indexed_pixels = []
    color_counts = [0, 0, 0, 0]

    for r, g, b in pixels:
        brightness = (r + g + b) / 3

        if brightness <= threshold_1:
            idx = 0  # Darkest (will be transparent in NES)
        elif brightness <= threshold_2:
            idx = 1  # Dark-medium
        elif brightness <= threshold_3:
            idx = 2  # Medium-bright
        else:
            idx = 3  # Brightest

        indexed_pixels.append(idx)
        color_counts[idx] += 1

    # Show distribution
    total = len(pixels)
    print(f"    Color distribution:")
    print(f"      Index 0 (darkest):  {color_counts[0]:6d} ({100*color_counts[0]/total:5.1f}%)")
    print(f"      Index 1 (dark):     {color_counts[1]:6d} ({100*color_counts[1]/total:5.1f}%)")
    print(f"      Index 2 (bright):   {color_counts[2]:6d} ({100*color_counts[2]/total:5.1f}%)")
    print(f"      Index 3 (brightest):{color_counts[3]:6d} ({100*color_counts[3]/total:5.1f}%)")

    # Create indexed image
    indexed_img = Image.new('P', img.size)
    indexed_img.putdata(indexed_pixels)

    # Set NES-friendly palette
    palette = [
        0, 0, 0,          # 0: Black (transparent in NES)
        231, 51, 214,     # 1: Magenta
        51, 214, 231,     # 2: Cyan
        255, 255, 255     # 3: White
    ]
    # Pad to 256 colors
    palette.extend([0, 0, 0] * (256 - 4))
    indexed_img.putpalette(palette)

    return indexed_img

def process_asset_simple(input_path, output_path, target_size=(128, 128)):
    """
    Simple asset processing:
    1. Load image
    2. Resize to target size
    3. Convert to 4-color indexed
    4. Save
    """
    print(f"\n[PROCESSING] {os.path.basename(input_path)}")

    # Load
    img = Image.open(input_path)
    print(f"  Original: {img.size[0]}x{img.size[1]} ({img.mode})")

    # Resize to multiple of 8
    target_w = ((target_size[0] + 7) // 8) * 8
    target_h = ((target_size[1] + 7) // 8) * 8

    print(f"  Resizing to: {target_w}x{target_h}")
    img_resized = img.resize((target_w, target_h), Image.Resampling.LANCZOS)

    # Convert to 4 colors
    print(f"  Converting to 4-color indexed...")
    img_indexed = smart_quantize_4color(img_resized)

    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img_indexed.save(output_path, 'PNG')
    print(f"  [OK] Saved: {output_path}")

    return True

def main():
    parser = argparse.ArgumentParser(description='Process AI assets (fixed version)')
    parser.add_argument('input', help='Input PNG file')
    parser.add_argument('output', help='Output indexed PNG file')
    parser.add_argument('--size', default='128x128', help='Target size (e.g., 128x128)')

    args = parser.parse_args()

    # Parse size
    w, h = map(int, args.size.split('x'))

    process_asset_simple(args.input, args.output, (w, h))

if __name__ == '__main__':
    main()
