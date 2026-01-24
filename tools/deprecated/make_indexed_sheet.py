#!/usr/bin/env python3
"""
NEON SURVIVORS - Indexed Color Sprite Sheet Generator
Creates a 4-color indexed PNG compatible with img2chr and NES constraints
"""

from PIL import Image
import os

# Exact NES palette colors (4 colors for sprites)
# These map to grayscale values for img2chr
PALETTE_COLORS = [
    (0, 0, 0),         # 0: Black (transparent) - grayscale 0
    (85, 85, 85),      # 1: Dark gray - grayscale 85
    (170, 170, 170),   # 2: Light gray - grayscale 170
    (255, 255, 255),   # 3: White - grayscale 255
]

def quantize_to_palette(color):
    """Map RGB color to nearest palette index"""
    r, g, b = color

    # If mostly black (dark colors)
    if r < 64 and g < 64 and b < 64:
        return 0

    # If very bright (white/light colors)
    elif r > 200 or g > 200 or b > 200:
        return 3

    # If cyan/blue-ish (medium-bright)
    elif b > g and b > r:
        return 2

    # If magenta/red-ish (medium)
    elif r > b and r > g:
        return 1

    # Default to dark gray
    else:
        return 1

def create_indexed_sprite_sheet():
    """
    Recreate sprite sheet with exactly 4 indexed colors
    suitable for img2chr conversion
    """

    # Load original sprites
    sprite_dir = "gfx/generated"

    # Create blank indexed image
    sheet = Image.new('P', (128, 128))

    # Set palette
    palette_data = []
    for color in PALETTE_COLORS:
        palette_data.extend(color)
    # Pad to 768 bytes (256 colors * 3 channels)
    palette_data.extend([0] * (768 - len(palette_data)))
    sheet.putpalette(palette_data)

    # Sprite layout (same as before)
    layout = {
        (0, 0, 2, 2): 'player_rad_dude.png',
        (2, 0, 1, 1): 'enemy_bit_drone.png',
        (3, 0, 2, 2): 'enemy_neon_skull.png',
        (0, 2, 1, 1): 'pickup_xp_gem.png',
        (1, 2, 1, 1): 'weapon_laser.png',
    }

    print("=" * 60)
    print("Creating 4-color indexed sprite sheet...")
    print("=" * 60)
    print()

    for (tile_x, tile_y, w_tiles, h_tiles), filename in layout.items():
        sprite_path = os.path.join(sprite_dir, filename)

        if not os.path.exists(sprite_path):
            print(f"[WARN] {filename} not found")
            continue

        # Load sprite as RGB
        sprite = Image.open(sprite_path).convert('RGB')
        pixels = sprite.load()

        # Quantize to 4-color palette
        indexed_sprite = Image.new('P', sprite.size)
        indexed_sprite.putpalette(palette_data)
        indexed_pixels = indexed_sprite.load()

        for y in range(sprite.height):
            for x in range(sprite.width):
                rgb = pixels[x, y]
                palette_idx = quantize_to_palette(rgb)
                indexed_pixels[x, y] = palette_idx

        # Paste onto sheet
        px_x = tile_x * 8
        px_y = tile_y * 8
        sheet.paste(indexed_sprite, (px_x, px_y))

        tile_idx = tile_y * 16 + tile_x
        print(f"[OK] {filename} -> Tile ${tile_idx:02X}")

    # Save indexed PNG
    output_path = "gfx/generated/neon_indexed_sheet.png"
    sheet.save(output_path)

    # Verify color count
    colors = set()
    pixels = sheet.load()
    for y in range(sheet.height):
        for x in range(sheet.width):
            colors.add(pixels[x, y])

    print()
    print("=" * 60)
    print(f"[SUCCESS] Indexed sprite sheet created!")
    print(f"  Output: {output_path}")
    print(f"  Size: 128x128 pixels")
    print(f"  Colors used: {len(colors)} (max 4)")
    print(f"  Palette indices: {sorted(colors)}")
    print("=" * 60)
    print()
    print("Next: Convert to CHR with img2chr")
    print(f"  img2chr {output_path} sprites.chr")
    print()

    return output_path

if __name__ == "__main__":
    create_indexed_sprite_sheet()
