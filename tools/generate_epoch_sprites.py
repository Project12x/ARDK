#!/usr/bin/env python3
"""
EPOCH Sprite Generator - Uses Asset Pipeline
Generates hero, fenrir, and enemy sprites for Genesis with shared palette.
"""

import sys
import os
from pathlib import Path

# Add tools directory to path
TOOLS_DIR = Path(__file__).parent
sys.path.insert(0, str(TOOLS_DIR))

from PIL import Image
from asset_generators.base_generator import PollinationsClient
from asset_generators.prompt_system import PromptBuilder

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent / "projects" / "epoch" / "res" / "sprites"

# Genesis palette constraints (15 colors + transparent)
GENESIS_PALETTE = {
    "transparent": (255, 0, 255),  # Magenta = transparent
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    # Hero colors (reds, browns, blues)
    "red_dark": (139, 0, 0),
    "red_light": (205, 92, 92),
    "flannel_red": (178, 34, 34),
    "brown_dark": (101, 67, 33),
    "brown_light": (139, 90, 43),
    "tan": (210, 180, 140),
    "skin": (255, 205, 148),
    "hair_brown": (139, 69, 19),
    "jeans_blue": (70, 130, 180),
    "jeans_dark": (47, 79, 79),
    "white_shoe": (245, 245, 245),
    "gray": (128, 128, 128),
}

# Enemy colors (synthwave cyber)
ENEMY_PALETTE = {
    "transparent": (255, 0, 255),
    "black": (0, 0, 0),
    "purple_dark": (75, 0, 130),
    "purple_mid": (138, 43, 226),
    "purple_light": (186, 85, 211),
    "cyan_dark": (0, 139, 139),
    "cyan_mid": (0, 255, 255),
    "cyan_light": (127, 255, 212),
    "pink_hot": (255, 20, 147),
    "red_glow": (255, 0, 0),
    "white": (255, 255, 255),
}


def generate_hero_sprite():
    """Generate 8-directional hero sprite sheet."""
    print("Generating Hero sprite...")
    
    client = PollinationsClient()
    builder = PromptBuilder("genesis")
    
    prompt = builder.sprite_prompt(
        description="""90s teenager character for action game:
        - Long brown hair flowing from under baseball cap
        - Red and black flannel shirt (plaid pattern)
        - Blue jeans with rolled cuffs
        - Black and white converse sneakers
        - Holding orange/yellow retro toy space gun
        - Confident pose, ready for action
        Style: 16-bit Sega Genesis, clean pixel art like Gunstar Heroes""",
        size=(32, 32),
        animation="8-directional idle"
    )
    
    # Generate base sprite
    image = client.generate_image(
        prompt=prompt,
        width=256,  # 8 frames × 32px
        height=32,
        model="flux"
    )
    
    if image:
        output_path = OUTPUT_DIR / "hero_sheet_new.png"
        image.save(output_path)
        print(f"  Saved: {output_path}")
        return image
    return None


def generate_fenrir_sprite():
    """Generate terrier dog companion sprite sheet."""
    print("Generating Fenrir sprite...")
    
    client = PollinationsClient()
    builder = PromptBuilder("genesis")
    
    prompt = builder.sprite_prompt(
        description="""Small terrier dog companion:
        - Yorkshire/Cairn terrier mix
        - Golden and brown fur with tan highlights
        - Perky ears, wagging tail
        - Loyal, alert expression
        - Small red bandana/collar
        Colors must match hero palette: browns, tans, reds
        Style: 16-bit Sega Genesis, cute but detailed like Sonic's Tails""",
        size=(32, 32),
        animation="walk cycle"
    )
    
    image = client.generate_image(
        prompt=prompt,
        width=256,  # 8 frames × 32px
        height=32,
        model="flux"
    )
    
    if image:
        output_path = OUTPUT_DIR / "fenrir_sheet_new.png"
        image.save(output_path)
        print(f"  Saved: {output_path}")
        return image
    return None


def generate_enemy_large():
    """Generate large enemy sprite (32x32)."""
    print("Generating Large Enemy sprite...")
    
    client = PollinationsClient()
    builder = PromptBuilder("genesis")
    
    prompt = builder.sprite_prompt(
        description="""Synthwave cyber virus enemy:
        - Corrupted digital creature made of glitchy data
        - Geometric crystalline form with sharp angles
        - Glowing neon purple core with cyan energy tendrils
        - Red glowing eyes/sensor
        - Menacing but stylized, like Tron meets virus
        Style: 16-bit Genesis, vibrant contrast""",
        size=(32, 32),
        animation="idle"
    )
    
    image = client.generate_image(
        prompt=prompt,
        width=32,
        height=32,
        model="flux"
    )
    
    if image:
        output_path = OUTPUT_DIR / "enemy_large_new.png"
        image.save(output_path)
        print(f"  Saved: {output_path}")
        return image
    return None


def generate_enemy_small():
    """Generate small enemy sprite (16x16)."""
    print("Generating Small Enemy sprite...")
    
    client = PollinationsClient()
    builder = PromptBuilder("genesis")
    
    prompt = builder.sprite_prompt(
        description="""Small synthwave cyber virus minion:
        - Simple geometric viral form
        - Floating digital spore/drone
        - Neon purple and cyan colors
        - Single glowing eye/core
        Style: 16-bit Genesis, simple but readable""",
        size=(16, 16),
        animation="idle"
    )
    
    image = client.generate_image(
        prompt=prompt,
        width=16,
        height=16,
        model="flux"
    )
    
    if image:
        output_path = OUTPUT_DIR / "enemy_small_new.png"
        image.save(output_path)
        print(f"  Saved: {output_path}")
        return image
    return None


def main():
    print("=" * 60)
    print("EPOCH Sprite Generator")
    print("=" * 60)
    print(f"Output directory: {OUTPUT_DIR}")
    print()
    
    # Generate all sprites
    hero = generate_hero_sprite()
    fenrir = generate_fenrir_sprite()
    enemy_large = generate_enemy_large()
    enemy_small = generate_enemy_small()
    
    print()
    print("=" * 60)
    print("Generation Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Review generated sprites in res/sprites/")
    print("2. Run fix_genesis_assets.py to optimize palettes")
    print("3. Update resources.res to use new sprites")
    print("4. Rebuild the ROM")


if __name__ == "__main__":
    main()
