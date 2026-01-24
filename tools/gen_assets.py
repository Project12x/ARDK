
import sys

def create_chr(output_path):
    # Each tile is 16 bytes (8x8 pixels, 2bpp)
    data = bytearray(8192) # 8KB bank initialization

    def set_pixel(tile_idx, x, y, color):
        if 0 <= x < 8 and 0 <= y < 8:
            offset = tile_idx * 16
            if color & 1:
                data[offset + y] |= (1 << (7 - x))
            if color & 2:
                data[offset + 8 + y] |= (1 << (7 - x))

    def draw_pattern(tile_idx, pattern):
        for y, row in enumerate(pattern):
            for x, char in enumerate(row):
                if char != ' ':
                    set_pixel(tile_idx, x, y, int(char))

    # --- Game Assets (Indices 1-16) ---
    
    # Tile 1: Spaceship
    draw_pattern(1, [
        "   11   ",
        "   11   ",
        "  1221  ",
        " 122221 ",
        " 122221 ",
        "12233221",
        "12333321",
        " 112211 "
    ])

    # Tile 2: Enemy Drone
    draw_pattern(2, [
        "  1221  ",
        " 123321 ",
        "12311321",
        "12111121",
        "12311321",
        " 123321 ",
        "  1221  ",
        "   11   "
    ])

    # Tile 3: Projectile (Plasma Bolt)
    draw_pattern(3, [
        "   22   ",
        "  2332  ",
        " 233332 ",
        " 233332 ",
        "  2332  ",
        "   22   ",
        "        ",
        "        "
    ])

    # Tile 4: XP Gem
    draw_pattern(4, [
        "   33   ",
        "  3223  ",
        " 321123 ",
        " 321123 ",
        "  3223  ",
        "   33   ",
        "   33   ",
        "   33   "
    ])
    
    # Tile 5: Grid Horizontal
    for x in range(8): set_pixel(5, x, 7, 1)
    # Tile 6: Grid Vertical
    for y in range(8): set_pixel(6, 7, y, 1)
    # Tile 7: Grid Intersection
    for x in range(8): set_pixel(7, x, 7, 1)
    for y in range(8): set_pixel(7, 7, y, 1)

    # --- Font (ASCII 32-90) ---
    # Simplified 5x7 font centered in 8x8
    
    font_map = {
        'A': [" 111 ", "1   1", "1   1", "11111", "1   1", "1   1", "1   1"],
        'B': ["1111 ", "1   1", "1111 ", "1   1", "1   1", "1   1", "1111 "],
        'C': [" 1111", "1    ", "1    ", "1    ", "1    ", "1    ", " 1111"],
        'D': ["1111 ", "1   1", "1   1", "1   1", "1   1", "1   1", "1111 "],
        'E': ["11111", "1    ", "1    ", "1111 ", "1    ", "1    ", "11111"],
        'F': ["11111", "1    ", "1    ", "1111 ", "1    ", "1    ", "1    "],
        'G': [" 1111", "1    ", "1    ", "1  11", "1   1", "1   1", " 1111"],
        'H': ["1   1", "1   1", "1   1", "11111", "1   1", "1   1", "1   1"],
        'I': [" 111 ", "  1  ", "  1  ", "  1  ", "  1  ", "  1  ", " 111 "],
        'J': ["  111", "    1", "    1", "    1", "1   1", "1   1", " 111 "],
        'K': ["1   1", "1  1 ", "1 1  ", "11   ", "1 1  ", "1  1 ", "1   1"],
        'L': ["1    ", "1    ", "1    ", "1    ", "1    ", "1    ", "11111"],
        'M': ["1   1", "11 11", "1 1 1", "1   1", "1   1", "1   1", "1   1"],
        'N': ["1   1", "11  1", "1 1 1", "1  11", "1   1", "1   1", "1   1"],
        'O': [" 111 ", "1   1", "1   1", "1   1", "1   1", "1   1", " 111 "],
        'P': ["1111 ", "1   1", "1   1", "1111 ", "1    ", "1    ", "1    "],
        'Q': [" 111 ", "1   1", "1   1", "1   1", "1 1 1", "1  1 ", " 11 1"],
        'R': ["1111 ", "1   1", "1   1", "1111 ", "1 1  ", "1  1 ", "1   1"],
        'S': [" 1111", "1    ", "1    ", " 111 ", "    1", "    1", "1111 "],
        'T': ["11111", "  1  ", "  1  ", "  1  ", "  1  ", "  1  ", "  1  "],
        'U': ["1   1", "1   1", "1   1", "1   1", "1   1", "1   1", " 111 "],
        'V': ["1   1", "1   1", "1   1", "1   1", "1   1", " 1 1 ", "  1  "],
        'W': ["1   1", "1   1", "1   1", "1 1 1", "1 1 1", "1 1 1", " 1 1 "],
        'X': ["1   1", "1   1", " 1 1 ", "  1  ", " 1 1 ", "1   1", "1   1"],
        'Y': ["1   1", "1   1", " 1 1 ", "  1  ", "  1  ", "  1  ", "  1  "],
        'Z': ["11111", "    1", "   1 ", "  1  ", " 1   ", "1    ", "11111"],
        '0': [" 111 ", "1  11", "1 1 1", "11  1", "1   1", " 111 "], # Short
        '1': ["  1  ", " 11  ", "  1  ", "  1  ", "  1  ", " 111 "],
        '2': ["1111 ", "    1", "  11 ", " 1   ", "1    ", "11111"],
        '3': ["1111 ", "    1", "  11 ", "    1", "    1", "1111 "],
        '4': ["1  1 ", "1  1 ", "11111", "   1 ", "   1 ", "   1 "],
        '5': ["11111", "1    ", "1111 ", "    1", "    1", "1111 "],
        '6': [" 111 ", "1    ", "1111 ", "1   1", "1   1", " 111 "],
        '7': ["11111", "    1", "   1 ", "  1  ", "  1  ", "  1  "],
        '8': [" 111 ", "1   1", " 111 ", "1   1", "1   1", " 111 "],
        '9': [" 111 ", "1   1", " 1111", "    1", "   1 ", " 11  "],
        '-': ["     ", "     ", "     ", "11111", "     ", "     "],
        '.': ["     ", "     ", "     ", "     ", "     ", "  11 "],
        '!': ["  1  ", "  1  ", "  1  ", "  1  ", "     ", "  1  "],
    }

    # Map characters to ASCII indices
    # ASCII 'A' is 65. We want to place it at index 65 in CHR (or specific offset)
    # To keep it simple, we'll map strictly to ASCII codes where possible.
    
    for char, pattern in font_map.items():
        idx = ord(char)
        draw_pattern(idx, pattern)

    with open(output_path, 'wb') as f:
        f.write(data)
    
    print(f"Generated assets to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python gen_assets.py <output.chr>")
        sys.exit(1)
    
    create_chr(sys.argv[1])
