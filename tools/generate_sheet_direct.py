#!/usr/bin/env python3
"""
Direct 5-Direction Sprite Sheet Generation.

Strategy:
1. Use gptimage-large to generate a FULL sprite sheet in one pass.
   - Prompt: "orthogonal sprite sheet", "5 views", "white background".
2. Use FloodFillBackgroundDetector to slice the sheet into individual sprites.
3. Save raw sheet + extracted sprites.

Benefits:
- Consitent style across angles (same generation context).
- Low cost (1 API call).
- True orthogonal perspective via prompting.
"""

import sys
import os
import time
import requests
from pathlib import Path
from PIL import Image, ImageDraw
import collections
from typing import Tuple, Optional, List

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Output setup
OUTPUT_DIR = Path("projects/epoch/res/sprites/hero_sheet_gen")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# API Setup
API_KEY = os.environ.get("POLLINATIONS_API_KEY") 
BASE_URL = "https://gen.pollinations.ai/image/"

# =============================================================================
# Utilities (Extracted from tools/pipeline/processing.py)
# =============================================================================

class BoundingBox:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
    def __repr__(self): return f"BBox({self.x},{self.y},{self.w},{self.h})"

class FloodFillBackgroundDetector:
    """Robust background removal using Edge-Initiated Flood Fill."""
    
    def __init__(self, tolerance: int = 10):
        self.tolerance = tolerance

    def get_content_mask(self, img: Image.Image) -> Image.Image:
        w, h = img.size
        scratch = img.convert("RGBA")
        try:
            ImageDraw.floodfill(scratch, (0, 0), (0, 0, 0, 0), thresh=self.tolerance)
            ImageDraw.floodfill(scratch, (w-1, 0), (0, 0, 0, 0), thresh=self.tolerance)
            ImageDraw.floodfill(scratch, (0, h-1), (0, 0, 0, 0), thresh=self.tolerance)
            ImageDraw.floodfill(scratch, (w-1, h-1), (0, 0, 0, 0), thresh=self.tolerance)
        except Exception as e:
            pass
        scratch_alpha = scratch.split()[3]
        return scratch_alpha.point(lambda x: 255 if x > 0 else 0, mode='1')

    def detect(self, img: Image.Image) -> List[BoundingBox]:
        """Simple sprite slicer based on mask connectivity (Row/Col scanning)."""
        mask = self.get_content_mask(img)
        w, h = mask.size
        pixels = mask.load()
        
        # 1. Scan Y for rows
        rows = []
        in_content = False
        start_y = 0
        for y in range(h):
            row_has_content = any(pixels[x, y] for x in range(w))
            if row_has_content and not in_content:
                in_content = True
                start_y = y
            elif not row_has_content and in_content:
                in_content = False
                if (y - start_y) > 10: rows.append((start_y, y))
        if in_content: rows.append((start_y, h))
        
        # 2. Scan X in each row for sprites
        sprites = []
        for y1, y2 in rows:
            in_sprite = False
            start_x = 0
            for x in range(w):
                # Check column in this row strip
                col_has_content = False
                for y in range(y1, y2):
                    if pixels[x, y]:
                        col_has_content = True
                        break
                
                if col_has_content and not in_sprite:
                    in_sprite = True
                    start_x = x
                elif not col_has_content and in_sprite:
                    in_sprite = False
                    if (x - start_x) > 10:
                        # Find tight bounds
                        sprites.append(self._get_tight_bounds(mask, start_x, y1, x - start_x, y2 - y1))
            if in_sprite:
                 sprites.append(self._get_tight_bounds(mask, start_x, y1, w - start_x, y2 - y1))
                 
        return [s for s in sprites if s]

    def _get_tight_bounds(self, mask: Image.Image, x, y, w, h):
        pixels = mask.load()
        min_x, max_x = x + w, x
        min_y, max_y = y + h, y
        found = False
        for py in range(y, y + h):
            for px in range(x, x + w):
                if pixels[px, py]:
                    found = True
                    min_x = min(min_x, px)
                    max_x = max(max_x, px)
                    min_y = min(min_y, py)
                    max_y = max(max_y, py)
        if found: return BoundingBox(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)
        return None

# =============================================================================
# Palette & Quantization
# =============================================================================

# Epoch: Hero (Rad Dude) + Fenrir (Dog) - Shared palette
EPOCH_HERO_DOG = [
    (255, 0, 255),             # 0: Transparent (magenta)
    (0, 0, 0),                 # 1: Black (outline)
    (255, 255, 255),           # 2: White (highlight)
    (255, 218, 182),           # 3: Skin light
    (218, 182, 145),           # 4: Skin mid / Brown light (shared)
    (182, 145, 109),           # 5: Skin shadow / Brown mid
    (255, 72, 72),             # 6: Red light (flannel highlight)
    (218, 36, 36),             # 7: Red mid (flannel, cap)
    (145, 36, 36),             # 8: Red dark (flannel shadow)
    (72, 109, 182),            # 9: Blue light (jeans)
    (36, 72, 145),             # 10: Blue dark (jeans shadow)
    (109, 72, 36),             # 11: Brown dark (dog fur)
    (255, 182, 72),            # 12: Orange light (TOY GUN/GUITAR highlight)
    (255, 145, 0),             # 13: Orange mid (TOY GUN/GUITAR body)
    (182, 109, 0),             # 14: Orange dark (TOY GUN/GUITAR shadow)
    (109, 109, 109),           # 15: Gray (t-shirt, details)
]

def quantize_to_palette(img: Image.Image, palette: List[Tuple[int, int, int]]) -> Image.Image:
    """Snap every pixel to nearest color in palette."""
    img = img.convert("RGB")
    pixels = img.load()
    w, h = img.size
    
    # Pre-calculate simple map if possible, but for small sprites, 
    # per-pixel distance check is fast enough.
    
    for y in range(h):
        for x in range(w):
            r, g, b = pixels[x, y]
            
            # Find nearest
            best_color = palette[0]
            min_dist = float('inf')
            
            for pr, pg, pb in palette:
                # Weighted Euclidean distance (better perceptual match)
                dist = ((r - pr) * 0.30)**2 + ((g - pg) * 0.59)**2 + ((b - pb) * 0.11)**2
                if dist < min_dist:
                    min_dist = dist
                    best_color = (pr, pg, pb)
            
            pixels[x, y] = best_color
            
    return img

# =============================================================================
# Main Generation Logic
# =============================================================================

def generate_sheet():
    print("DIRECT 5-DIRECTION SHEET GEN (gptimage-large)")
    print("  + Perspective: ISOMETRIC / ORTHOGONAL")
    print("  + Content: Guitar, Jeans, Flannel")
    print("  + Palette: Genesis EPOCH_HERO_DOG")
    
    # Convert palette to HEX string for prompt guidance
    hex_palette = []
    for r, g, b in EPOCH_HERO_DOG:
        hex_palette.append(f"#{r:02X}{g:02X}{b:02X}")
    palette_prompt = ", ".join(hex_palette)
    
    # Output config
    OUTPUT_DIR_DOG = Path("projects/epoch/res/sprites/dog_sheet_gen")
    OUTPUT_DIR_DOG.mkdir(parents=True, exist_ok=True)

    prompt = (
        "Video game sprite sheet of a scruffy black and brown terrier dog companion. "
        "Small, energetic, cute but tough. "
        "Perspective: Orthogonal projection, flat 2D depth, no perspective distortion (Zombies Ate My Neighbors style). "
        "5 distinct character views arranged in a row: Front, Front-Right, Side, Back-Right, Back. "
        "Uniform height 32px (smaller than hero), white background, clean separation between sprites. "
        "Pixel art style, 16-bit Sega Genesis aesthetic. "
        f"Strictly use this color palette: {palette_prompt}"
    )
    
    encoded_prompt = requests.utils.quote(prompt)
    url = f"{BASE_URL}{encoded_prompt}?model=gptimage-large&width=1024&height=512&seed={int(time.time())}"
    
    headers = {}
    if API_KEY: headers["Authorization"] = f"Bearer {API_KEY}"
    
    print(f"Requesting URL: {url}")
    try:
        resp = requests.get(url, headers=headers, timeout=60)
        if resp.status_code == 200:
            print("  [OK] Image received")
            sheet_path = OUTPUT_DIR_DOG / "sheet_raw_dog.png"
            with open(sheet_path, "wb") as f:
                f.write(resp.content)
            
            # Process
            process_sheet(sheet_path, output_dir=OUTPUT_DIR_DOG, target_height=32)
            return True
        else:
            print(f"  [FAIL] Status {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"  [FAIL] Exception: {e}")
    return False

def process_sheet(sheet_path):
    print("\nProcessing Sprite Sheet...")
    img = Image.open(sheet_path)
    detector = FloodFillBackgroundDetector(tolerance=30)
    
    # 1. Detect Sprites
    bboxes = detector.detect(img)
    print(f"  Found {len(bboxes)} potential sprites")
    
    # 2. Extract and Save
    bboxes.sort(key=lambda b: b.x)
    
def pad_to_canvas(img: Image.Image, canvas_w: int = 32, canvas_h: int = 48) -> Image.Image:
    """Pad image to standard canvas size, aligning BOTTOM-CENTER."""
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    
    # Calculate position
    # Center horizontally
    x = (canvas_w - img.width) // 2
    # Align bottom
    y = canvas_h - img.height
    
    canvas.paste(img, (x, y))
    return canvas

def process_sheet(sheet_path, output_dir=OUTPUT_DIR, target_height=48):
    print("\nProcessing Sprite Sheet...")
    if not sheet_path.exists():
        print(f"  [FAIL] Sheet not found: {sheet_path}")
        return

    img = Image.open(sheet_path)
    detector = FloodFillBackgroundDetector(tolerance=30)
    
    # 1. Detect Sprites
    bboxes = detector.detect(img)
    print(f"  Found {len(bboxes)} potential sprites")
    
    # 2. Extract and Save
    # Sort by X position
    bboxes.sort(key=lambda b: b.x)
    
    valid_sprites = []
    
    for i, bbox in enumerate(bboxes):
        sprite = img.crop((bbox.x, bbox.y, bbox.x + bbox.w, bbox.y + bbox.h))
        
        # Filter tiny garbage (adjust for smaller dog)
        if sprite.width < 10 or sprite.height < 16:
            continue
            
        valid_sprites.append(sprite)
    
    print(f"  Extracted {len(valid_sprites)} valid sprites")
    
    # Save valid sprites
    for i, sprite in enumerate(valid_sprites):
        # Resize logic: Fit to target_height, keep aspect
        aspect = sprite.width / sprite.height
        target_h = target_height
        target_w = int(target_h * aspect)
        
        # Resize (Nearest neighbor to keep sharp edges)
        final = sprite.resize((target_w, target_h), Image.NEAREST)
        
        # Transparentize using MASK (prevent internal white loss)
        # We need a mask for the resized sprite.
        # Efficient way: Resize the mask too? 
        # Or re-detect on the resized sprite? 
        # Actually, sprite was cropped from a mask-detected region.
        # But resizing disrupts the exact pixel mapping.
        # Better: Re-run FloodFill on the single sprite to isolate background.
        # Since the sprite is rectangular crop, it has background corners.
        
        # 1. Create a mask for the resized sprite
        temp_detector = FloodFillBackgroundDetector(tolerance=30)
        mask = temp_detector.get_content_mask(final)
        # Resize mask to match final (if we detected before resize) -> No, detect on final.
        
        # 2. Apply mask
        final = final.convert("RGBA")
        datas = final.getdata()
        mask_data = mask.getdata()
        
        new_data = []
        for pixel_idx, item in enumerate(datas):
            # If mask is 0 (background), make transparent
            if mask_data[pixel_idx] == 0:
                new_data.append((0, 0, 0, 0))
            else:
                new_data.append(item)
        final.putdata(new_data)
        
        # Quantize to Genesis Palette
        final = quantize_to_palette(final, EPOCH_HERO_DOG)
        
        # Pad to standard canvas (Bottom-Center alignment)
        # Use target_height for canvas height (32 or 48)
        # Assuming width is always 32 standard tile width for now
        final = pad_to_canvas(final, 32, target_height)
        
        save_path = output_dir / f"view_{i}_v4.png"
        final.save(save_path)
        print(f"    Saved View {i}: {save_path.name} ({final.size}) -> Masked Transparency & Quantized & Aligned")

if __name__ == "__main__":
    # V5: Small Teenager Hero (User Request)
    OUTPUT_DIR_V5 = Path("projects/epoch/res/sprites/hero_sheet_v5_small")
    OUTPUT_DIR_V5.mkdir(parents=True, exist_ok=True)
    
    # Palette logic (ensure it's defined or imported)
    hex_palette = []
    for r, g, b in EPOCH_HERO_DOG:
        hex_palette.append(f"#{r:02X}{g:02X}{b:02X}")
    palette_prompt = ", ".join(hex_palette)

    prompt = (
        "Video game sprite sheet of a teenage hero with long hair. "
        "He is wearing a red flannel shirt and blue jeans. No sunglasses. "
        "He is holding a colorful plastic toy ray gun. "
        "Perspective: Orthogonal projection, flat 2D depth, no perspective distortion (Zombies Ate My Neighbors style). "
        "5 distinct character views arranged in a row: Front, Front-Right, Side, Back-Right, Back. "
        "Uniform height 32px, white background, clean separation between sprites. "
        "Pixel art style, 16-bit Sega Genesis aesthetic. "
        f"Strictly use this color palette: {palette_prompt}"
    )
    
    encoded_prompt = requests.utils.quote(prompt)
    url = f"{BASE_URL}{encoded_prompt}?model=gptimage-large&width=1024&height=512&seed={int(time.time())}"
    
    headers = {}
    if API_KEY: headers["Authorization"] = f"Bearer {API_KEY}"
    
    sheet_path = OUTPUT_DIR_V5 / "sheet_raw_v5.png"
    
    if sheet_path.exists():
        print("  [INFO] Sheet found, skipping generation (Zero Cost).")
        process_sheet(sheet_path, output_dir=OUTPUT_DIR_V5, target_height=32)
    else:
        print(f"Requesting URL: {url}")
        try:
            resp = requests.get(url, headers=headers, timeout=60)
            if resp.status_code == 200:
                print("  [OK] Image received")
                with open(sheet_path, "wb") as f:
                    f.write(resp.content)
                
                # Process: Target 32px height, saving to V5 folder. 
                process_sheet(sheet_path, output_dir=OUTPUT_DIR_V5, target_height=32)
            else:
                print(f"  [FAIL] Status {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"  [FAIL] Exception: {e}")
