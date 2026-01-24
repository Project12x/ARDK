#!/usr/bin/env python3
"""
Quick sprite sheet inspection tool
Displays basic info about sprite sheet layout
"""

import sys
from PIL import Image
import os

def inspect_sheet(filepath):
    """Analyze a sprite sheet and provide layout info"""
    if not os.path.exists(filepath):
        print(f"ERROR: File not found: {filepath}")
        return

    img = Image.open(filepath)
    filename = os.path.basename(filepath)

    print(f"\n{'='*60}")
    print(f"SPRITE SHEET: {filename}")
    print(f"{'='*60}")
    print(f"Dimensions: {img.size[0]}x{img.size[1]} pixels")
    print(f"Mode: {img.mode}")
    print(f"File size: {os.path.getsize(filepath) / 1024:.1f} KB")
    print()

    # Calculate possible grid layouts
    print("Possible Grid Layouts:")
    for sprite_size in [8, 16, 32, 64]:
        cols = img.size[0] // sprite_size
        rows = img.size[1] // sprite_size
        total = cols * rows
        print(f"  {sprite_size}x{sprite_size} sprites: {cols}x{rows} grid = {total} sprites")

    # Check if there's transparency/alpha
    if img.mode in ('RGBA', 'LA', 'P'):
        print(f"\nAlpha channel: Present ({img.mode})")
    else:
        print(f"\nAlpha channel: None (RGB mode)")

    # Sample some pixels to understand color distribution
    pixels = img.getdata()
    unique_colors = set()
    sample_size = min(10000, len(list(pixels)))

    print(f"\nColor analysis (sampling {sample_size} pixels)...")
    for i, pixel in enumerate(pixels):
        if i >= sample_size:
            break
        unique_colors.add(pixel[:3] if len(pixel) >= 3 else pixel)

    print(f"Unique colors in sample: {len(unique_colors)}")
    if len(unique_colors) <= 10:
        print("Sample colors:")
        for color in list(unique_colors)[:10]:
            print(f"  RGB{color}")

    print(f"{'='*60}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Inspect all priority assets
        assets = [
            'gfx/ai_output/player_rad_90s.png',
            'gfx/ai_output/items_projectiles.png',
            'gfx/ai_output/enemies_synthwave.png'
        ]

        print("Inspecting priority assets...")
        for asset in assets:
            if os.path.exists(asset):
                inspect_sheet(asset)
            else:
                print(f"\nWARNING: {asset} not found")
    else:
        inspect_sheet(sys.argv[1])
