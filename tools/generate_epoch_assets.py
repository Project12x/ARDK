"""
Generate complete EPOCH asset set using PixelLab SDK.
Uses existing SGDKFormatter for Genesis-compliant output.
"""
import pixellab
from PIL import Image
import os
import sys

# Add pipeline to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline.sgdk_format import SGDKFormatter

# Configuration
API_KEY = 'b68c2160-d218-4cfb-81f2-ccb619108419'
OUTPUT_DIR = '../projects/epoch/res/sprites'
TILESET_DIR = '../projects/epoch/res/tilesets'

# Initialize SGDK formatter (handles 16-color, magenta transparency, sizing)
formatter = SGDKFormatter()


def generate_asset(client, description, width, height, name):
    """Generate a single asset using PixelLab SDK."""
    print(f"  Generating {name}...")
    
    try:
        response = client.generate_image_pixflux(
            description=description,
            image_size={'width': width, 'height': height},
            no_background=True,
        )
        
        img = response.image.pil_image()
        print(f"    PixelLab: {img.size} {img.mode}")
        return img
        
    except Exception as e:
        print(f"    ERROR: {e}")
        return None


def main():
    print("=" * 60)
    print("EPOCH Asset Generator - Using PixelLab + SGDKFormatter")
    print("=" * 60)
    
    # Create output directories
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TILESET_DIR, exist_ok=True)
    
    client = pixellab.Client(secret=API_KEY)
    
    # Check balance first
    balance = client.get_balance()
    print(f"\nBalance: {balance}")  # Print raw for debugging
    
    assets = []
    
    # ==========================================================================
    # 1. HERO SPRITE (32x32)
    # ==========================================================================
    print("\n[1/4] HERO SPRITE")
    hero_raw = generate_asset(
        client,
        "pixel art game character, 90s rad dude, backwards red baseball cap, loose white t-shirt, long brown hair, blue jeans, white sneakers, holding laser rifle, side view facing right, retro game sprite",
        32, 32, "hero"
    )
    if hero_raw:
        # Format for SGDK (16 colors, indexed, magenta transparency)
        hero = formatter.format_sprite(hero_raw, (32, 32))
        print(f"    SGDK: {hero.size} {hero.mode} ({len(hero.getcolors(256))} colors)")
        
        # Create 4-frame sheet (128px minimum for SGDK)
        sheet = formatter.create_sprite_sheet([hero] * 4, frames_per_row=4, frame_size=(32, 32))
        sheet.save(os.path.join(OUTPUT_DIR, 'player.png'))
        assets.append('player.png')
        print(f"    Saved: {OUTPUT_DIR}/player.png")
    
    # ==========================================================================
    # 2. ENEMY SPRITE (32x32)
    # ==========================================================================
    print("\n[2/4] ENEMY SPRITE")
    enemy_raw = generate_asset(
        client,
        "pixel art alien monster enemy, purple skin, glowing green eyes, sharp teeth, small wings, side view facing left, retro game sprite",
        32, 32, "enemy"
    )
    if enemy_raw:
        enemy = formatter.format_sprite(enemy_raw, (32, 32))
        print(f"    SGDK: {enemy.size} {enemy.mode} ({len(enemy.getcolors(256))} colors)")
        
        sheet = formatter.create_sprite_sheet([enemy] * 4, frames_per_row=4, frame_size=(32, 32))
        sheet.save(os.path.join(OUTPUT_DIR, 'enemy.png'))
        assets.append('enemy.png')
        print(f"    Saved: {OUTPUT_DIR}/enemy.png")
    
    # ==========================================================================
    # 3. PROJECTILE SPRITE (16x16)
    # ==========================================================================
    print("\n[3/4] PROJECTILE SPRITE")
    proj_raw = generate_asset(
        client,
        "pixel art laser beam projectile, glowing blue energy, horizontal, simple game projectile",
        32, 32, "projectile"  # Generate at 32, resize to 16
    )
    if proj_raw:
        proj = formatter.format_sprite(proj_raw, (16, 16))
        print(f"    SGDK: {proj.size} {proj.mode} ({len(proj.getcolors(256))} colors)")
        
        # 8 frames to reach 128px
        sheet = formatter.create_sprite_sheet([proj] * 8, frames_per_row=8, frame_size=(16, 16))
        sheet.save(os.path.join(OUTPUT_DIR, 'projectile.png'))
        assets.append('projectile.png')
        print(f"    Saved: {OUTPUT_DIR}/projectile.png")
    
    # ==========================================================================
    # 4. BACKGROUND (256x224 Genesis resolution)
    # ==========================================================================
    print("\n[4/4] BACKGROUND")
    bg_raw = generate_asset(
        client,
        "pixel art wasteland background, post-apocalyptic desert, dark purple sky, ruined buildings, simple ground, retro 16-bit game style",
        256, 128, "background"  # Max PixelLab size
    )
    if bg_raw:
        # Background uses 16 colors but may be larger
        bg = formatter.format_sprite(bg_raw, (256, 128), maintain_aspect=False)
        print(f"    SGDK: {bg.size} {bg.mode} ({len(bg.getcolors(256))} colors)")
        bg.save(os.path.join(TILESET_DIR, 'background.png'))
        assets.append('background.png')
        print(f"    Saved: {TILESET_DIR}/background.png")
    
    # ==========================================================================
    # SUMMARY
    # ==========================================================================
    print("\n" + "=" * 60)
    print("GENERATION COMPLETE")
    print("=" * 60)
    print(f"Assets generated: {len(assets)}/4")
    for a in assets:
        print(f"  ✓ {a}")
    
    # Final balance
    balance = client.get_balance()
    print(f"\nRemaining: {balance.subscription.generations}/{balance.subscription.total} generations")


if __name__ == '__main__':
    main()

