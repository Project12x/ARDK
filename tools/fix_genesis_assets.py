
import sys
from pathlib import Path
from PIL import Image

def fix_asset(path_str):
    path = Path(path_str)
    if not path.exists():
        print(f"File not found: {path}")
        return

    print(f"Processing {path.name}...")
    img = Image.open(path).convert("RGBA")
    
    # 0. Safety: Shift visible Magenta (255, 0, 255) to (254, 0, 255) to avoid conflict
    #    with Magic Pink transparency if we use it, or just for safety.
    pixels = img.load()
    width, height = img.size
    
    # Check for opacity (if min alpha is high, image is opaque)
    # If opaque, we assume Black (0,0,0) is meant to be the background.
    alpha_band = img.split()[3]
    if alpha_band.getextrema()[0] > 200:
        print(f"Warning: {path.name} appears fully opaque. Applying Black Chroma Key...")
        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]
                # If Black, make transparent
                if r < 10 and g < 10 and b < 10:
                     pixels[x, y] = (0, 0, 0, 0)
    
    # Shift any ACTUAL magenta pixels to safety?
    # NO: Assume pure magenta (255,0,255) IS transparency key if alpha is 255.
    # Also detect NEAR-magenta colors (common from AI generation)
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            # Chroma Key: Detect magenta-like colors (high R, low G, high B)
            if r > 200 and g < 50 and b > 200:
                 pixels[x, y] = (0, 0, 0, 0) # Force Transparent
            # Safety for "almost magenta" not needed if we key exact #FF00FF

    # 1. Create a blank palette image (P mode)
    # 16 colors max. Index 0 must be transparent/background.
    # We use classic Magenta (255, 0, 255) as Index 0 (Transparent)
    
    # Quantize foreground only to 15 colors
    # Create an image without alpha for quantization (on black background)
    rgb_img = Image.new("RGB", img.size, (0, 0, 0))
    rgb_img.paste(img, mask=img.split()[3])
    
    quantized_rgb = rgb_img.quantize(colors=15, method=2) # 15 colors + 1 reserved
    
    # Get the palette from the quantized image
    q_palette = quantized_rgb.getpalette() # [r, g, b, r, g, b, ...] typically 768 entries
    
    # Construct new palette: Index 0 = Magenta (Transparent), 1..15 = Quantized colors
    # SGDK default transparency is often Index 0.
    new_palette = [255, 0, 255] + q_palette[:45] # 15 * 3 = 45 values
    
    # Pad to 768 entries (256 colors * 3)
    new_palette += [0] * (768 - len(new_palette))
    
    # Create final indexed image
    final_img = Image.new("P", img.size)
    final_img.putpalette(new_palette)
    
    # Map pixels
    # If alpha < 128 -> Index 0
    # Else -> Nearest index from 1..15 (which matches the quantized map)
    # Since we quantized, the indices in quantized_rgb (0-14) map to our new indices (1-15)
    
    width, height = img.size
    pixels = final_img.load()
    q_pixels = quantized_rgb.load()
    alpha = img.split()[3].load()
    
    for y in range(height):
        for x in range(width):
            if alpha[x, y] < 128:
                pixels[x, y] = 0 # Transparent index
            else:
                # Quantized returned 0..14, we shift to 1..15
                pixels[x, y] = q_pixels[x, y] + 1

    # Save
    # Save Main Sprite
    final_img.save(path, transparency=0)
    print(f"Saved indexed {path.name} (Force Index 0 Transparent) Mode={final_img.mode}")
    
    # Save separate palette file (16x1) to appease rescomp if needed
    pal_img = Image.new("P", (16, 1))
    pal_img.putpalette(new_palette)
    # Fill colors
    pal_pixels = pal_img.load()
    for i in range(16):
        pal_pixels[i, 0] = i
    
    pal_path = path.parent / f"{path.stem}_palette.png"
    pal_img.save(pal_path)
    print(f"Saved palette {pal_path.name}")


def main():
    root = Path("projects/epoch/res/sprites")
    assets = [
        root / "player_8way_sheet.png",
        root / "tower.png",
        Path("projects/epoch/res/tilesets/background.png")
    ]
    
    for asset in assets:
        fix_asset(asset)

if __name__ == "__main__":
    main()
