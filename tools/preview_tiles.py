#!/usr/bin/env python3
"""
CHR Tile Previewer
Quickly visualize different tile combinations without rebuilding ROM

Usage:
    python tools/preview_tiles.py src/game/assets/sprites.chr --tiles 0x75,0x76,0x85,0x86
"""

import argparse
from PIL import Image, ImageDraw

# NES palette colors (subset for preview)
NES_COLORS = {
    0x0F: (0, 0, 0),           # Black
    0x24: (252, 56, 228),      # Magenta
    0x1C: (0, 228, 252),       # Cyan
    0x30: (252, 252, 252),     # White
}

def decode_chr_tile(chr_data, tile_num):
    """
    Decode a single 8x8 NES tile

    Args:
        chr_data: Raw CHR file data
        tile_num: Tile index (0-255)

    Returns:
        List of 64 pixel values (0-3)
    """
    offset = tile_num * 16
    plane0 = chr_data[offset:offset+8]
    plane1 = chr_data[offset+8:offset+16]

    pixels = []
    for y in range(8):
        for x in range(8):
            bit0 = (plane0[y] >> (7-x)) & 1
            bit1 = (plane1[y] >> (7-x)) & 1
            pixel = bit0 | (bit1 << 1)
            pixels.append(pixel)

    return pixels

def render_tile(pixels, palette, scale=8):
    """
    Render 8x8 tile to PIL Image

    Args:
        pixels: List of 64 pixel values (0-3)
        palette: List of 4 NES color indices
        scale: Pixel scale factor

    Returns:
        PIL Image object
    """
    img = Image.new('RGB', (8 * scale, 8 * scale))
    draw = ImageDraw.Draw(img)

    for i, pixel_val in enumerate(pixels):
        x = (i % 8) * scale
        y = (i // 8) * scale
        color_idx = palette[pixel_val]
        color = NES_COLORS.get(color_idx, (128, 128, 128))

        draw.rectangle([x, y, x+scale-1, y+scale-1], fill=color)

    return img

def preview_metatile(chr_path, tiles, palette=None, scale=8):
    """
    Preview a 2x2 metatile (16x16 sprite)

    Args:
        chr_path: Path to CHR file
        tiles: List of 4 tile indices [TL, TR, BL, BR]
        palette: NES palette indices [0=transparent, 1-3=colors]
        scale: Pixel scale factor
    """
    if palette is None:
        palette = [0x0F, 0x24, 0x1C, 0x30]  # Default: Black, Magenta, Cyan, White

    with open(chr_path, 'rb') as f:
        chr_data = f.read()

    # Decode all 4 tiles
    tile_images = []
    for tile_num in tiles:
        pixels = decode_chr_tile(chr_data, tile_num)
        tile_img = render_tile(pixels, palette, scale)
        tile_images.append(tile_img)

    # Combine into 2x2 metatile
    metatile = Image.new('RGB', (16 * scale, 16 * scale))
    metatile.paste(tile_images[0], (0, 0))           # Top-left
    metatile.paste(tile_images[1], (8 * scale, 0))   # Top-right
    metatile.paste(tile_images[2], (0, 8 * scale))   # Bottom-left
    metatile.paste(tile_images[3], (8 * scale, 8 * scale))  # Bottom-right

    return metatile

def find_best_sprites(chr_path, min_density=0.3):
    """
    Scan CHR file for likely sprite candidates

    Args:
        chr_path: Path to CHR file
        min_density: Minimum % of non-zero pixels

    Returns:
        List of (tile_num, density, preview_text) tuples
    """
    with open(chr_path, 'rb') as f:
        chr_data = f.read()

    candidates = []
    num_tiles = len(chr_data) // 16

    for tile_num in range(num_tiles):
        pixels = decode_chr_tile(chr_data, tile_num)
        non_zero = sum(1 for p in pixels if p != 0)
        density = non_zero / 64.0

        if density >= min_density:
            # Generate ASCII preview
            preview = ""
            for i in range(0, 64, 8):
                row = pixels[i:i+8]
                preview += "".join([' ', '.', '+', '#'][p] for p in row) + "\n"

            candidates.append((tile_num, density, preview))

    return sorted(candidates, key=lambda x: x[1], reverse=True)

def main():
    parser = argparse.ArgumentParser(description='Preview CHR tiles')
    parser.add_argument('chr_file', help='CHR file to preview')
    parser.add_argument('--tiles', help='Comma-separated hex tile indices (e.g., 0x75,0x76,0x85,0x86)')
    parser.add_argument('--palette', help='Comma-separated hex palette (e.g., 0x0F,0x24,0x1C,0x30)')
    parser.add_argument('--scale', type=int, default=8, help='Pixel scale factor')
    parser.add_argument('--output', help='Output PNG file')
    parser.add_argument('--scan', action='store_true', help='Scan for sprite candidates')
    parser.add_argument('--min-density', type=float, default=0.3, help='Min density for scan')

    args = parser.parse_args()

    # Scan mode
    if args.scan:
        print(f"Scanning {args.chr_file} for sprites...")
        candidates = find_best_sprites(args.chr_file, args.min_density)

        print(f"\nFound {len(candidates)} candidates (>= {args.min_density*100:.0f}% filled):\n")
        for i, (tile_num, density, preview) in enumerate(candidates[:20]):
            print(f"Tile ${tile_num:02X} ({density*100:.0f}% filled):")
            for line in preview.strip().split('\n'):
                print(f"  {line}")
            print()

        # Suggest 2x2 metatiles
        print("\nSuggested 2x2 metatiles:")
        for i in range(0, min(len(candidates)-3, 40), 4):
            tiles = [candidates[i][0], candidates[i+1][0],
                     candidates[i+2][0], candidates[i+3][0]]
            avg_density = sum(candidates[i+j][1] for j in range(4)) / 4
            print(f"  ${tiles[0]:02X}, ${tiles[1]:02X}, ${tiles[2]:02X}, ${tiles[3]:02X} (avg {avg_density*100:.0f}%)")

        return

    # Preview mode
    if not args.tiles:
        parser.error("--tiles required (or use --scan)")

    # Parse tiles
    tile_strs = args.tiles.split(',')
    tiles = [int(t.strip(), 16 if t.strip().startswith('0x') else 10) for t in tile_strs]

    if len(tiles) != 4:
        parser.error("Need exactly 4 tiles for 2x2 metatile")

    # Parse palette
    if args.palette:
        pal_strs = args.palette.split(',')
        palette = [int(p.strip(), 16 if p.strip().startswith('0x') else 10) for p in pal_strs]
    else:
        palette = [0x0F, 0x24, 0x1C, 0x30]

    print(f"Previewing tiles: ${tiles[0]:02X}, ${tiles[1]:02X}, ${tiles[2]:02X}, ${tiles[3]:02X}")
    print(f"Palette: {', '.join(f'${p:02X}' for p in palette)}")

    # Generate preview
    img = preview_metatile(args.chr_file, tiles, palette, args.scale)

    # Output
    if args.output:
        img.save(args.output)
        print(f"Saved preview to {args.output}")
    else:
        img.show()

if __name__ == '__main__':
    main()
