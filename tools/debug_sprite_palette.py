"""
Debug sprite palettes - check index 0 transparency (ASCII-safe)
"""
from PIL import Image
import os

def analyze_sprite(path):
    """Analyze a sprite's palette for transparency issues"""
    if not os.path.exists(path):
        print(f"NOT FOUND: {path}")
        return
    
    img = Image.open(path)
    print(f"\n=== {os.path.basename(path)} ===")
    print(f"Size: {img.size}, Mode: {img.mode}")
    
    if img.mode == 'P':
        palette = img.getpalette()
        print(f"Index 0 (transparency): RGB({palette[0]}, {palette[1]}, {palette[2]})")
        print(f"Index 1: RGB({palette[3]}, {palette[4]}, {palette[5]})")
        print(f"Index 2: RGB({palette[6]}, {palette[7]}, {palette[8]})")
        
        # Check if index 0 is magenta (255,0,255)
        if palette[0] == 255 and palette[1] == 0 and palette[2] == 255:
            print("[OK] Index 0 is MAGENTA (correct transparency)")
        else:
            print("[FAIL] Index 0 is NOT MAGENTA - TRANSPARENCY BROKEN")
            
        # Count pixels using index 0
        pixels = list(img.getdata())
        zero_count = sum(1 for p in pixels if p == 0)
        print(f"Pixels using index 0: {zero_count} ({100*zero_count/len(pixels):.1f}%)")
    elif img.mode == 'RGBA':
        print("Mode is RGBA (needs conversion to indexed P)")
        # Check for transparent pixels
        pixels = list(img.getdata())
        transparent = sum(1 for p in pixels if p[3] == 0)
        magenta = sum(1 for p in pixels if p[0]==255 and p[1]==0 and p[2]==255)
        print(f"Transparent pixels (alpha=0): {transparent}")
        print(f"Magenta pixels: {magenta}")
    elif img.mode == 'RGB':
        print("Mode is RGB (no alpha)")
        pixels = list(img.getdata())
        magenta = sum(1 for p in pixels if p[0]==255 and p[1]==0 and p[2]==255)
        print(f"Magenta pixels: {magenta}")
    else:
        print(f"Unexpected mode: {img.mode}")

# Analyze sprites
sprites_dir = r"c:\Users\estee\Desktop\My Stuff\Code\Antigravity\SurvivorNES\projects\epoch\res\sprites"

analyze_sprite(os.path.join(sprites_dir, "hero_sheet_final.png"))
analyze_sprite(os.path.join(sprites_dir, "dog_sheet_32x32.png"))
analyze_sprite(os.path.join(sprites_dir, "dog_sheet_final.png"))
analyze_sprite(os.path.join(sprites_dir, "enemy.png"))
