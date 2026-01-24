#!/usr/bin/env python3
"""
NEON SURVIVORS - AI Asset Processing Pipeline
Converts AI-generated PNG assets to NES-compatible format

Usage:
    python tools/process_ai_assets.py --asset player_rad_90s
    python tools/process_ai_assets.py --asset items_projectiles
    python tools/process_ai_assets.py --all
"""

import argparse
import os
import sys
from PIL import Image

# NES palette (subset for testing - full palette in final version)
NES_PALETTE = {
    'black': (0, 0, 0),
    'white': (255, 255, 255),
    'magenta': (231, 51, 214),
    'cyan': (51, 214, 231),
    'red': (231, 51, 51),
    'green': (51, 231, 51),
    'blue': (51, 51, 231),
    'yellow': (231, 231, 51),
    'purple': (131, 51, 231),
    'orange': (231, 131, 51),
}

def quantize_to_nes_palette(color_rgb):
    """Map RGB color to nearest NES palette color index (0-3 for sprites)"""
    r, g, b = color_rgb

    # Brightness-based quantization for 4-color sprites
    brightness = (r + g + b) / 3

    if brightness < 64:
        return 0  # Black (transparent)
    elif brightness < 128:
        return 1  # Dark color (magenta/cyan)
    elif brightness < 192:
        return 2  # Medium color
    else:
        return 3  # White/bright

# Asset-specific processing configurations
ASSET_CONFIGS = {
    'player_rad_90s': {
        'sprite_size': 16,           # 16x16 individual sprites
        'target_size': (128, 128),   # Final output: 8x8 grid of 16x16 sprites
        'extract_count': 64,         # Extract 64 sprites (8x8 grid)
        'description': 'Player character sprites (16x16)'
    },
    'items_projectiles': {
        'sprite_size': 16,           # Items are likely 16x16
        'target_size': (128, 128),   # 8x8 grid
        'extract_count': 64,
        'description': 'Items, projectiles, and powerups'
    },
    'enemies_synthwave': {
        'sprite_size': 16,           # 16x16 enemies
        'target_size': (128, 128),   # 8x8 grid
        'extract_count': 64,
        'description': 'Enemy sprites (16x16)'
    },
    'background_cyberpunk': {
        'sprite_size': 16,           # 16x16 tiles for metatiles
        'target_size': (256, 240),   # Full NES screen resolution
        'extract_count': 256,        # Extract many tiles
        'description': 'Cyberpunk background tiles'
    }
}

def resize_for_nes(img, target_width=128, target_height=128):
    """
    Resize image to NES-friendly dimensions (multiples of 8)

    NES sprites are 8x8 tiles, so dimensions must be divisible by 8.
    Common sizes: 16x16, 32x32, 64x64, 128x128, 256x256
    """
    # Round to nearest multiple of 8
    new_width = ((target_width + 7) // 8) * 8
    new_height = ((target_height + 7) // 8) * 8

    return img.resize((new_width, new_height), Image.Resampling.NEAREST)

def extract_sprite_sheet(img, sprite_size=16, max_sprites=64):
    """
    Extract individual sprites from a larger image

    Args:
        img: PIL Image object
        sprite_size: Size of each sprite (8, 16, 32)
        max_sprites: Maximum number of sprites to extract

    Returns:
        List of PIL Image objects (individual sprites)
    """
    sprites = []
    img_width, img_height = img.size

    cols = img_width // sprite_size
    rows = img_height // sprite_size

    for row in range(min(rows, max_sprites // cols)):
        for col in range(cols):
            if len(sprites) >= max_sprites:
                break

            left = col * sprite_size
            top = row * sprite_size
            right = left + sprite_size
            bottom = top + sprite_size

            sprite = img.crop((left, top, right, bottom))
            sprites.append(sprite)

    return sprites

def create_indexed_4color(img):
    """
    Convert RGB image to 4-color indexed PNG for img2chr compatibility

    Process:
    1. Quantize to 4 colors
    2. Create palette with exactly 4 colors
    3. Convert to indexed mode
    """
    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # Get unique colors and map to 4-color palette
    pixels = list(img.getdata())
    color_map = {}
    palette_colors = [
        (0, 0, 0),        # 0: Black (transparent)
        (231, 51, 214),   # 1: Magenta
        (51, 214, 231),   # 2: Cyan
        (255, 255, 255)   # 3: White
    ]

    # Map each pixel to nearest palette color index
    indexed_pixels = []
    for pixel in pixels:
        idx = quantize_to_nes_palette(pixel)
        indexed_pixels.append(idx)

    # Create new indexed image
    indexed_img = Image.new('P', img.size)
    indexed_img.putdata(indexed_pixels)

    # Set palette
    palette_data = []
    for color in palette_colors:
        palette_data.extend(color)
    # Fill rest of palette with black
    palette_data.extend([0, 0, 0] * (256 - len(palette_colors)))
    indexed_img.putpalette(palette_data)

    return indexed_img

def process_asset(asset_name, input_dir='gfx/ai_output', output_dir='gfx/processed'):
    """
    Process a single AI-generated asset for NES

    Steps:
    1. Load PNG
    2. Extract sprites if needed (using config)
    3. Resize to NES dimensions
    4. Convert to 4-color indexed
    5. Save as _indexed.png (ready for img2chr)
    """
    input_path = os.path.join(input_dir, f'{asset_name}.png')
    output_path = os.path.join(output_dir, f'{asset_name}_indexed.png')

    if not os.path.exists(input_path):
        print(f'[ERROR] Asset not found: {input_path}')
        return False

    # Create output directory if needed
    os.makedirs(output_dir, exist_ok=True)

    print(f'[PROCESSING] {asset_name}.png')

    # Get asset-specific config
    config = ASSET_CONFIGS.get(asset_name)
    if config:
        print(f'  Config: {config["description"]}')
        print(f'  Sprite size: {config["sprite_size"]}x{config["sprite_size"]}')
        print(f'  Target output: {config["target_size"][0]}x{config["target_size"][1]}')

    try:
        # Load image
        img = Image.open(input_path)
        print(f'  Original size: {img.size[0]}x{img.size[1]} ({img.mode})')

        # Extract sprites if config specifies sprite extraction
        if config and img.size[0] > config['target_size'][0] * 2:
            print(f'  Extracting {config["extract_count"]} sprites from sheet...')
            sprites = extract_sprite_sheet(
                img,
                sprite_size=config['sprite_size'],
                max_sprites=config['extract_count']
            )
            print(f'  Extracted {len(sprites)} sprites')

            # Arrange extracted sprites into target grid
            target_width, target_height = config['target_size']
            sprites_per_row = target_width // config['sprite_size']

            # Create new image with target dimensions
            img_resized = Image.new('RGB', config['target_size'], (0, 0, 0))

            # Paste sprites into grid
            for i, sprite in enumerate(sprites[:config['extract_count']]):
                row = i // sprites_per_row
                col = i % sprites_per_row
                x = col * config['sprite_size']
                y = row * config['sprite_size']
                img_resized.paste(sprite, (x, y))

            print(f'  Arranged into {sprites_per_row}x{config["extract_count"]//sprites_per_row} grid')
        else:
            # Simple resize without extraction
            # Determine target size based on asset type
            if config:
                target_size = config['target_size']
            elif 'player' in asset_name or 'enemy' in asset_name:
                target_size = (128, 128)  # 16x16 sprite grid (8x8 sprites)
            elif 'background' in asset_name:
                target_size = (256, 240)  # Full NES screen
            elif 'title' in asset_name or 'logo' in asset_name:
                target_size = (256, 128)  # Title screen logo area
            elif 'item' in asset_name or 'vfx' in asset_name:
                target_size = (64, 64)    # Small sprites/effects
            else:
                target_size = (128, 128)  # Default

            img_resized = resize_for_nes(img, target_size[0], target_size[1])
            print(f'  Resized to: {img_resized.size[0]}x{img_resized.size[1]}')

        # Convert to 4-color indexed
        img_indexed = create_indexed_4color(img_resized)
        print(f'  Converted to indexed mode with 4 colors')

        # Save indexed PNG
        img_indexed.save(output_path, 'PNG')
        print(f'  [OK] Saved: {output_path}')
        print(f'  Ready for: img2chr {output_path} src/game/assets/{asset_name}.chr')

        return True

    except Exception as e:
        print(f'  [ERROR] Failed to process: {e}')
        return False

def batch_process_priority_assets():
    """Process the priority 1 assets needed for core gameplay"""
    priority_assets = [
        'player_rad_90s',        # Main player sprite
        'items_projectiles',     # Weapons and powerups
        'enemies_synthwave',     # Core enemies
    ]

    print('='*50)
    print('BATCH PROCESSING: Priority 1 Assets')
    print('='*50)
    print()

    success_count = 0
    for asset in priority_assets:
        if process_asset(asset):
            success_count += 1
        print()

    print('='*50)
    print(f'Processed {success_count}/{len(priority_assets)} assets')
    print('='*50)

def main():
    parser = argparse.ArgumentParser(
        description='Process AI-generated assets for NES compatibility'
    )
    parser.add_argument(
        '--asset',
        type=str,
        help='Process a specific asset (e.g., player_rad_90s)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Process all priority 1 assets'
    )

    args = parser.parse_args()

    if args.all:
        batch_process_priority_assets()
    elif args.asset:
        process_asset(args.asset)
    else:
        print('Usage: python tools/process_ai_assets.py --asset <name> or --all')
        print()
        print('Available assets in gfx/ai_output/:')
        ai_dir = 'gfx/ai_output'
        if os.path.exists(ai_dir):
            for filename in sorted(os.listdir(ai_dir)):
                if filename.endswith('.png'):
                    asset_name = filename[:-4]  # Remove .png
                    print(f'  - {asset_name}')

if __name__ == '__main__':
    main()
