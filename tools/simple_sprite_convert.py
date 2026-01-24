#!/usr/bin/env python3
"""
Simple sprite converter for NES - handles magenta/cyan/white/black sprites directly.
No AI, no complex quantization - just direct color mapping.
"""

from PIL import Image
import os
import sys

# Direct color mapping for synthwave sprites
# Maps RGB to NES palette index (0-3)
def classify_color(r, g, b):
    """Classify a pixel as black(0), magenta(1), cyan(2), or white(3)"""
    brightness = (r + g + b) / 3

    # Black/transparent - very dark
    if brightness < 40:
        return 0

    # White - very bright
    if r > 200 and g > 200 and b > 200:
        return 3

    # Magenta - high R, low G, high B
    if r > 150 and g < 150 and b > 150:
        return 1

    # Cyan - low R, high G, high B
    if r < 150 and g > 150 and b > 150:
        return 2

    # Fallback based on which channel dominates
    if r > g and r > b:
        return 1  # Reddish -> magenta
    if g > r and b > r:
        return 2  # Cyan-ish
    if brightness > 180:
        return 3  # Bright -> white

    return 0  # Default to black

def convert_to_indexed(img):
    """Convert RGBA image to 4-color indexed with proper NES palette"""
    width, height = img.size
    pixels = img.load()

    # Create indexed image
    indexed = Image.new('P', (width, height))

    # Set NES-friendly palette
    # 0=Black, 1=Magenta, 2=Cyan, 3=White
    palette = [
        0, 0, 0,           # 0: Black
        255, 0, 255,       # 1: Magenta
        0, 255, 255,       # 2: Cyan
        255, 255, 255,     # 3: White
    ]
    # Pad to 256 colors
    palette.extend([0] * (256 * 3 - len(palette)))
    indexed.putpalette(palette)

    indexed_pixels = indexed.load()

    color_counts = {0: 0, 1: 0, 2: 0, 3: 0}

    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]

            # Transparent -> black
            if a < 128:
                idx = 0
            else:
                idx = classify_color(r, g, b)

            indexed_pixels[x, y] = idx
            color_counts[idx] += 1

    print(f"  Color distribution: black={color_counts[0]}, magenta={color_counts[1]}, cyan={color_counts[2]}, white={color_counts[3]}")

    return indexed

def indexed_to_chr(indexed_img):
    """Convert indexed PNG to CHR format"""
    width, height = indexed_img.size
    pixels = indexed_img.load()

    chr_data = bytearray()

    # Process 8x8 tiles
    for tile_y in range(0, height, 8):
        for tile_x in range(0, width, 8):
            plane0 = []
            plane1 = []

            for row in range(8):
                p0_byte = 0
                p1_byte = 0

                for col in range(8):
                    x = tile_x + col
                    y = tile_y + row

                    if x < width and y < height:
                        color = pixels[x, y]
                    else:
                        color = 0

                    bit0 = color & 1
                    bit1 = (color >> 1) & 1

                    p0_byte |= (bit0 << (7 - col))
                    p1_byte |= (bit1 << (7 - col))

                plane0.append(p0_byte)
                plane1.append(p1_byte)

            chr_data.extend(plane0)
            chr_data.extend(plane1)

    return bytes(chr_data)

def process_sprite(input_path, output_dir, sprite_name):
    """Process a single sprite from nobg PNG to CHR"""
    print(f"\nProcessing: {input_path}")

    img = Image.open(input_path).convert('RGBA')
    print(f"  Size: {img.size}")

    # Convert to indexed
    indexed = convert_to_indexed(img)

    # Save indexed PNG for debugging
    indexed_path = os.path.join(output_dir, f"{sprite_name}_indexed.png")
    indexed.save(indexed_path)
    print(f"  Saved: {indexed_path}")

    # Convert to CHR
    chr_data = indexed_to_chr(indexed)

    chr_path = os.path.join(output_dir, f"{sprite_name}.chr")
    with open(chr_path, 'wb') as f:
        f.write(chr_data)
    print(f"  Saved: {chr_path} ({len(chr_data)} bytes)")

    return chr_data

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_dir = os.path.join(base_dir, "gfx", "processed", "player_new")
    output_dir = os.path.join(base_dir, "gfx", "processed", "simple")
    sprites_chr = os.path.join(base_dir, "src", "game", "assets", "sprites.chr")

    os.makedirs(output_dir, exist_ok=True)

    # Process the nobg (no background) sprites which have the detail
    nobg_files = [
        "sprite_3_nobg.png",  # First good character frame
        "sprite_4_nobg.png",
        "sprite_5_nobg.png",
        "sprite_6_nobg.png",
    ]

    all_chr = bytearray()

    for i, filename in enumerate(nobg_files):
        input_path = os.path.join(input_dir, filename)
        if os.path.exists(input_path):
            chr_data = process_sprite(input_path, output_dir, f"frame_{i+1}")
            all_chr.extend(chr_data)
        else:
            print(f"Warning: {input_path} not found")

    # Pad to 8KB
    while len(all_chr) < 8192:
        all_chr.append(0)

    # Save combined sprites.chr
    with open(sprites_chr, 'wb') as f:
        f.write(all_chr)
    print(f"\nCreated: {sprites_chr} ({len(all_chr)} bytes)")

    print("\nDone! Now rebuild with compile.bat")
    print("\nNOTE: Update game palette to match:")
    print("  Sprite palette 0: $0F (black), $24 (magenta), $1C (cyan), $30 (white)")

if __name__ == "__main__":
    main()
