#!/usr/bin/env python3
"""
Stitch individual generated sprite frames into SGDK-ready sheets.
"""
from pathlib import Path
from PIL import Image
import sys

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
HERO_SRC_DIR = PROJECT_ROOT / "projects/epoch/res/sprites/hero_sheet_v5_small"
DOG_SRC_DIR = PROJECT_ROOT / "projects/epoch/res/sprites/dog_sheet_gen"
DEST_DIR = PROJECT_ROOT / "projects/epoch/res/sprites"

# Palette Definition (Must match genesis_palettes.py)
EPOCH_HERO_DOG = [
    (255, 0, 255),             # 0: Transparent (magenta)
    (0, 0, 0),                 # 1: Black (outline)
    (255, 255, 255),           # 2: White (highlight)
    (255, 218, 182),           # 3: Skin light
    (218, 182, 145),           # 4: Skin mid
    (182, 145, 109),           # 5: Skin shadow
    (255, 72, 72),             # 6: Red light
    (218, 36, 36),             # 7: Red mid
    (145, 36, 36),             # 8: Red dark
    (72, 109, 182),            # 9: Blue light
    (36, 72, 145),             # 10: Blue dark
    (109, 72, 36),             # 11: Brown dark
    (255, 182, 72),            # 12: Orange light
    (255, 145, 0),             # 13: Orange mid
    (182, 109, 0),             # 14: Orange dark
    (109, 109, 109),           # 15: Gray
]

def create_indexed_sheet(rgba_img: Image.Image) -> Image.Image:
    """Convert RGBA to P-Mode (Indexed) using strict palette."""
    # 1. Replace Alpha 0 with Magenta
    data = rgba_img.getdata()
    new_data = []
    magenta = (255, 0, 255, 255)
    
    for item in data:
        if item[3] == 0: # Transparent
            new_data.append(magenta)
        else:
            new_data.append(item)
            
    img_magenta = Image.new("RGBA", rgba_img.size)
    img_magenta.putdata(new_data)
    img_rgb = img_magenta.convert("RGB") # Drop alpha channel
    
    # 2. Create Palette Image (P mode)
    p_img = Image.new("P", (1, 1))
    
    # Flatten palette list of tuples to list of ints
    flat_palette = []
    for r, g, b in EPOCH_HERO_DOG:
        flat_palette.extend([r, g, b])
        
    # Pad to 256 colors (768 ints)
    while len(flat_palette) < 768:
        flat_palette.append(0)
        
    p_img.putpalette(flat_palette)
    
    # 3. Quantize/Map to Palette
    # Since we already pre-quantized in generation, we can just map.
    # However, to be safe, we use 'quantize' against the palette image.
    final = img_rgb.quantize(palette=p_img, dither=Image.NONE)
    return final

def stitch_sheet(src_dir, name_prefix, output_name):
    print(f"Stitching {output_name} from {src_dir}...")
    
    # ... (loading views 0-4 as before) ...
    # Hero v3 files -> hero_view_X_v3.png
    # Dog v4 / Hero v5 files -> view_X_v4.png
    
    is_v5_or_dog = "dog" in str(src_dir) or "v5" in str(src_dir)
    
    if is_v5_or_dog:
        suffix = "_v4.png"
        prefix = "view"
    else:
        suffix = "_v3.png"
        prefix = "hero_view"
    
    try:
        v0 = Image.open(src_dir / f"{prefix}_0{suffix}").convert("RGBA")
        v1 = Image.open(src_dir / f"{prefix}_1{suffix}").convert("RGBA")
        v2 = Image.open(src_dir / f"{prefix}_2{suffix}").convert("RGBA")
        v3 = Image.open(src_dir / f"{prefix}_3{suffix}").convert("RGBA")
        v4 = Image.open(src_dir / f"{prefix}_4{suffix}").convert("RGBA")
    except FileNotFoundError as e:
        print(f"  [FAIL] Missing source file: {e}")
        return

    # Create Mirrored
    # Logic Update: V5 appears to be Left-Facing (Front -> SW -> West -> NW -> Back)
    # Standard: [S, SE, E, NE, N, NW, W, SW]
    
    if is_v5_or_dog:
        # Input order is: v0(S), v1(SW/F-L), v2(W/L), v3(NW/B-L), v4(N)
        # We need to FLIP v1, v2, v3 to get SE, E, NE
        
        # South
        s = v0
        # South-East (flip SW)
        se = v1.transpose(Image.FLIP_LEFT_RIGHT)
        # East (flip W)
        e = v2.transpose(Image.FLIP_LEFT_RIGHT)
        # North-East (flip NW)
        ne = v3.transpose(Image.FLIP_LEFT_RIGHT)
        # North
        n = v4
        # North-West (Raw v3)
        nw = v3
        # West (Raw v2)
        w = v2
        # South-West (Raw v1)
        sw = v1
        
        ordered = [s, se, e, ne, n, nw, w, sw]
        
    else:
        # Legacy/Right-Facing Assumption (Front -> SE -> East -> NE -> Back)
        v5 = v3.transpose(Image.FLIP_LEFT_RIGHT) # NW
        v6 = v2.transpose(Image.FLIP_LEFT_RIGHT) # W
        v7 = v1.transpose(Image.FLIP_LEFT_RIGHT) # SW
        
        # Order: S, SE, E, NE, N, NW, W, SW
        ordered = [v0, v1, v2, v3, v4, v5, v6, v7]
    
    # Dimensions
    width, height = v0.size 
    sheet_w = width * 8
    sheet_h = height
    
    sheet = Image.new("RGBA", (sheet_w, sheet_h))
    
    for i, img in enumerate(ordered):
        sheet.paste(img, (i * width, 0))
    
    # Convert to Indexed
    final_sheet = create_indexed_sheet(sheet)
    
    out_path = DEST_DIR / output_name
    final_sheet.save(out_path)
    print(f"  [OK] Saved {out_path} ({sheet_w}x{sheet_h}) [Indexed]")

if __name__ == "__main__":
    stitch_sheet(HERO_SRC_DIR, "hero_view", "hero_sheet_final.png")
    stitch_sheet(DOG_SRC_DIR, "view", "dog_sheet_final.png")
