#!/usr/bin/env python3
"""
NEON SURVIVORS - Sprite Generator
Generates NES-compatible sprites for testing and converts to CHR format
"""

from PIL import Image, ImageDraw
import os

# NES palette (simplified - actual NES has 54 colors)
NES_PALETTE = {
    'black': (0, 0, 0),
    'white': (255, 255, 255),
    'cyan': (0, 255, 255),
    'magenta': (255, 0, 255),
    'hot_pink': (255, 105, 180),
    'electric_blue': (125, 249, 255),
    'dark_purple': (72, 0, 255),
    'neon_green': (57, 255, 20),
    'orange': (255, 163, 0),
    'gray': (128, 128, 128),
    'dark_gray': (64, 64, 64),
    'light_gray': (192, 192, 192),
}

def create_rad_90s_player():
    """
    Create a rad 90s dude - baseball cap, sunglasses, shorts
    Style: Kid Chameleon, Bart Simpson, Skate or Die
    16x16 sprite
    """
    img = Image.new('RGB', (16, 16), NES_PALETTE['black'])
    pixels = img.load()

    # Define the sprite pixel by pixel
    # Format: (x, y): color
    sprite_data = {
        # Baseball cap (hot pink/magenta)
        (5, 2): 'magenta', (6, 2): 'magenta', (7, 2): 'magenta', (8, 2): 'magenta', (9, 2): 'magenta', (10, 2): 'magenta',
        (4, 3): 'magenta', (5, 3): 'magenta', (6, 3): 'magenta', (7, 3): 'magenta', (8, 3): 'magenta', (9, 3): 'magenta', (10, 3): 'magenta', (11, 3): 'magenta',
        (11, 4): 'hot_pink', (12, 4): 'hot_pink', (13, 4): 'hot_pink',  # Cap visor

        # Face/head (light skin tone approximation)
        (5, 4): 'orange', (6, 4): 'orange', (7, 4): 'orange', (8, 4): 'orange', (9, 4): 'orange', (10, 4): 'orange',
        (5, 5): 'orange', (6, 5): 'orange', (7, 5): 'orange', (8, 5): 'orange', (9, 5): 'orange', (10, 5): 'orange',

        # Sunglasses (black with cyan glow)
        (5, 5): 'black', (6, 5): 'cyan', (7, 5): 'cyan', (8, 5): 'cyan', (9, 5): 'cyan', (10, 5): 'black',
        (5, 6): 'black', (6, 6): 'black', (7, 6): 'black', (8, 6): 'black', (9, 6): 'black', (10, 6): 'black',

        # Mouth/lower face
        (6, 7): 'orange', (7, 7): 'orange', (8, 7): 'orange', (9, 7): 'orange',

        # Tank top/shirt (cyan)
        (5, 8): 'cyan', (6, 8): 'cyan', (7, 8): 'cyan', (8, 8): 'cyan', (9, 8): 'cyan', (10, 8): 'cyan',
        (4, 9): 'cyan', (5, 9): 'cyan', (6, 9): 'cyan', (7, 9): 'cyan', (8, 9): 'cyan', (9, 9): 'cyan', (10, 9): 'cyan', (11, 9): 'cyan',
        (3, 10): 'cyan', (4, 10): 'electric_blue', (5, 10): 'cyan', (6, 10): 'electric_blue', (7, 10): 'cyan', (8, 10): 'electric_blue', (9, 10): 'cyan', (10, 10): 'electric_blue', (11, 10): 'cyan', (12, 10): 'cyan',

        # Arms (skin)
        (2, 11): 'orange', (3, 11): 'orange', (12, 11): 'orange', (13, 11): 'orange',

        # Shorts (purple)
        (5, 11): 'dark_purple', (6, 11): 'dark_purple', (7, 11): 'dark_purple', (8, 11): 'dark_purple', (9, 11): 'dark_purple', (10, 11): 'dark_purple',
        (5, 12): 'dark_purple', (6, 12): 'dark_purple', (7, 12): 'dark_purple', (8, 12): 'dark_purple', (9, 12): 'dark_purple', (10, 12): 'dark_purple',

        # Legs (skin)
        (5, 13): 'orange', (6, 13): 'orange', (9, 13): 'orange', (10, 13): 'orange',
        (5, 14): 'orange', (6, 14): 'orange', (9, 14): 'orange', (10, 14): 'orange',

        # Shoes (white/sneakers)
        (4, 15): 'white', (5, 15): 'white', (6, 15): 'white', (9, 15): 'white', (10, 15): 'white', (11, 15): 'white',
    }

    for (x, y), color in sprite_data.items():
        pixels[x, y] = NES_PALETTE[color]

    return img

def create_bit_drone_enemy():
    """8x8 basic geometric drone enemy"""
    img = Image.new('RGB', (8, 8), NES_PALETTE['black'])
    pixels = img.load()

    sprite_data = {
        # Diamond/rhombus shape in cyan
        (3, 0): 'cyan', (4, 0): 'cyan',
        (2, 1): 'cyan', (3, 1): 'electric_blue', (4, 1): 'electric_blue', (5, 1): 'cyan',
        (1, 2): 'cyan', (2, 2): 'electric_blue', (3, 2): 'cyan', (4, 2): 'cyan', (5, 2): 'electric_blue', (6, 2): 'cyan',
        (1, 3): 'cyan', (2, 3): 'cyan', (3, 3): 'white', (4, 3): 'white', (5, 3): 'cyan', (6, 3): 'cyan',
        (1, 4): 'cyan', (2, 4): 'cyan', (3, 4): 'cyan', (4, 4): 'cyan', (5, 4): 'cyan', (6, 4): 'cyan',
        (2, 5): 'cyan', (3, 5): 'electric_blue', (4, 5): 'electric_blue', (5, 5): 'cyan',
        (2, 6): 'cyan', (3, 6): 'cyan', (4, 6): 'cyan', (5, 6): 'cyan',
        (3, 7): 'cyan', (4, 7): 'cyan',
    }

    for (x, y), color in sprite_data.items():
        pixels[x, y] = NES_PALETTE[color]

    return img

def create_neon_skull_enemy():
    """16x16 floating skull enemy"""
    img = Image.new('RGB', (16, 16), NES_PALETTE['black'])
    pixels = img.load()

    sprite_data = {
        # Skull outline (hot pink/magenta)
        (5, 2): 'magenta', (6, 2): 'hot_pink', (7, 2): 'hot_pink', (8, 2): 'hot_pink', (9, 2): 'hot_pink', (10, 2): 'magenta',
        (4, 3): 'magenta', (5, 3): 'hot_pink', (6, 3): 'hot_pink', (7, 3): 'hot_pink', (8, 3): 'hot_pink', (9, 3): 'hot_pink', (10, 3): 'hot_pink', (11, 3): 'magenta',
        (3, 4): 'magenta', (4, 4): 'hot_pink', (5, 4): 'hot_pink', (6, 4): 'hot_pink', (7, 4): 'hot_pink', (8, 4): 'hot_pink', (9, 4): 'hot_pink', (10, 4): 'hot_pink', (11, 4): 'hot_pink', (12, 4): 'magenta',
        (3, 5): 'magenta', (4, 5): 'hot_pink', (5, 5): 'hot_pink', (6, 5): 'hot_pink', (7, 5): 'hot_pink', (8, 5): 'hot_pink', (9, 5): 'hot_pink', (10, 5): 'hot_pink', (11, 5): 'hot_pink', (12, 5): 'magenta',

        # Eye sockets (cyan glow)
        (5, 6): 'cyan', (6, 6): 'electric_blue', (7, 6): 'cyan', (9, 6): 'cyan', (10, 6): 'electric_blue', (11, 6): 'cyan',
        (5, 7): 'cyan', (6, 7): 'cyan', (7, 7): 'cyan', (9, 7): 'cyan', (10, 7): 'cyan', (11, 7): 'cyan',

        # Nose hole
        (8, 8): 'magenta',

        # Teeth
        (5, 10): 'hot_pink', (6, 10): 'magenta', (7, 10): 'hot_pink', (8, 10): 'magenta', (9, 10): 'hot_pink', (10, 10): 'magenta',
        (5, 11): 'magenta', (6, 11): 'hot_pink', (7, 11): 'magenta', (8, 11): 'hot_pink', (9, 11): 'magenta', (10, 11): 'hot_pink',

        # Bottom jaw
        (4, 12): 'magenta', (5, 12): 'hot_pink', (6, 12): 'hot_pink', (7, 12): 'hot_pink', (8, 12): 'hot_pink', (9, 12): 'hot_pink', (10, 12): 'hot_pink', (11, 12): 'magenta',
    }

    for (x, y), color in sprite_data.items():
        pixels[x, y] = NES_PALETTE[color]

    return img

def create_xp_gem():
    """8x8 XP crystal gem"""
    img = Image.new('RGB', (8, 8), NES_PALETTE['black'])
    pixels = img.load()

    sprite_data = {
        # Diamond shape in magenta/pink
        (3, 0): 'magenta', (4, 0): 'magenta',
        (2, 1): 'magenta', (3, 1): 'hot_pink', (4, 1): 'hot_pink', (5, 1): 'magenta',
        (1, 2): 'magenta', (2, 2): 'hot_pink', (3, 2): 'white', (4, 2): 'hot_pink', (5, 2): 'hot_pink', (6, 2): 'magenta',
        (1, 3): 'magenta', (2, 3): 'hot_pink', (3, 3): 'hot_pink', (4, 3): 'hot_pink', (5, 3): 'hot_pink', (6, 3): 'magenta',
        (2, 4): 'magenta', (3, 4): 'hot_pink', (4, 4): 'hot_pink', (5, 4): 'magenta',
        (2, 5): 'magenta', (3, 5): 'hot_pink', (4, 5): 'hot_pink', (5, 5): 'magenta',
        (3, 6): 'magenta', (4, 6): 'magenta',
        (3, 7): 'magenta', (4, 7): 'magenta',
    }

    for (x, y), color in sprite_data.items():
        pixels[x, y] = NES_PALETTE[color]

    return img

def create_laser_projectile():
    """8x8 cyan laser bolt"""
    img = Image.new('RGB', (8, 8), NES_PALETTE['black'])
    pixels = img.load()

    sprite_data = {
        (2, 3): 'cyan', (3, 3): 'electric_blue', (4, 3): 'electric_blue', (5, 3): 'cyan',
        (2, 4): 'cyan', (3, 4): 'white', (4, 4): 'white', (5, 4): 'cyan',
        (1, 4): 'cyan', (6, 4): 'cyan',
    }

    for (x, y), color in sprite_data.items():
        pixels[x, y] = NES_PALETTE[color]

    return img

def save_sprite(img, name, output_dir):
    """Save sprite as PNG"""
    os.makedirs(output_dir, exist_ok=True)
    # Save at actual size
    img.save(os.path.join(output_dir, f"{name}.png"))
    # Also save scaled up 8x for easier viewing
    scaled = img.resize((img.width * 8, img.height * 8), Image.NEAREST)
    scaled.save(os.path.join(output_dir, f"{name}_8x.png"))
    print(f"Created {name}.png ({img.width}x{img.height})")

def main():
    output_dir = "gfx/generated"

    print("=" * 50)
    print("NEON SURVIVORS - Sprite Generator")
    print("=" * 50)
    print()

    # Generate all sprites
    sprites = {
        'player_rad_dude': create_rad_90s_player(),
        'enemy_bit_drone': create_bit_drone_enemy(),
        'enemy_neon_skull': create_neon_skull_enemy(),
        'pickup_xp_gem': create_xp_gem(),
        'weapon_laser': create_laser_projectile(),
    }

    for name, sprite in sprites.items():
        save_sprite(sprite, name, output_dir)

    print()
    print("=" * 50)
    print("Sprite generation complete!")
    print(f"Output directory: {output_dir}")
    print()
    print("Next steps:")
    print("1. Review sprites in gfx/generated/")
    print("2. Convert to CHR format using png2chr or NEXXT")
    print("3. Update src/game/assets/sprites.chr")
    print("=" * 50)

if __name__ == "__main__":
    main()
