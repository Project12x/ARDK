#!/usr/bin/env python3
"""
Zero-Cost Canvas Verification with Robust Auto-Crop.

Features:
- Embeds FloodFillBackgroundDetector for smart cropping (handles non-transparent backgrounds).
- Maximizes sprite resolution within 32x48 bounds.
- Centers on 64x64 canvas for PixelLab.
"""

from pathlib import Path
from typing import Tuple, Optional, List, Dict
from PIL import Image, ImageDraw
import collections

OUTPUT_DIR = Path("projects/epoch/res/sprites/hero_composite")
CONCEPT_PATH = OUTPUT_DIR / "concept_ref.png"
VERIFY_PATH = OUTPUT_DIR / "verify_input_canvas.png"

# =============================================================================
# Utilities (Extracted from tools/pipeline/processing.py)
# =============================================================================

class FloodFillBackgroundDetector:
    """Robust background removal using Edge-Initiated Flood Fill."""
    
    def __init__(self, tolerance: int = 10):
        self.tolerance = tolerance

    def detect_background_color(self, img: Image.Image) -> Optional[Tuple[int, int, int]]:
        pixels = img.load()
        w, h = img.size
        # Sample 4 corners
        corners = [(0, 0), (w-1, 0), (0, h-1), (w-1, h-1)]
        samples = []
        for x, y in corners:
            if img.mode == 'RGBA':
                r, g, b, a = pixels[x, y]
                if a == 0: samples.append((0, 0, 0, 0))
                else: samples.append((r, g, b, 255))
            else:
                samples.append(pixels[x, y])
        
        if not samples: return None
        
        # Check consistency
        first = samples[0]
        disagreements = 0
        for s in samples[1:]:
            dist = sum(abs(v1 - v2) for v1, v2 in zip(first, s)) if isinstance(first, tuple) else abs(first - s)
            if dist > 30: disagreements += 1
                
        if disagreements > 1: return None
        return collections.Counter(samples).most_common(1)[0][0]

    def get_content_mask(self, img: Image.Image) -> Image.Image:
        w, h = img.size
        scratch = img.convert("RGBA")
        
        # Flood fill from corners with Transparent (0,0,0,0)
        # This wipes out the background color
        try:
            ImageDraw.floodfill(scratch, (0, 0), (0, 0, 0, 0), thresh=self.tolerance)
            ImageDraw.floodfill(scratch, (w-1, 0), (0, 0, 0, 0), thresh=self.tolerance)
            ImageDraw.floodfill(scratch, (0, h-1), (0, 0, 0, 0), thresh=self.tolerance)
            ImageDraw.floodfill(scratch, (w-1, h-1), (0, 0, 0, 0), thresh=self.tolerance)
        except Exception as e:
            print(f"      [SmartBg] Flood fill warning: {e}")
            
        # Extract alpha channel to find what's left
        scratch_alpha = scratch.split()[3]
        return scratch_alpha.point(lambda x: 255 if x > 0 else 0, mode='1')

def verify_canvas():
    print("VERIFYING CANVAS PREP (ZERO COST)")
    
    if not CONCEPT_PATH.exists():
        print(f"[FAIL] Concept file not found: {CONCEPT_PATH}")
        return

    # 1. Load Concept
    print(f"[1] Loading concept: {CONCEPT_PATH}")
    ref_img = Image.open(CONCEPT_PATH)
    print(f"    Original Size: {ref_img.size}")
    
    # 2. Smart Crop using FloodFillBackgroundDetector
    print("[2] Detecting Content Bounds...")
    detector = FloodFillBackgroundDetector(tolerance=20)
    mask = detector.get_content_mask(ref_img)
    bbox = mask.getbbox()
    
    if bbox:
        # Crop the original image using the calculated mask bbox
        ref_img = ref_img.crop(bbox)
        print(f"    Auto-cropped to: {bbox} -> {ref_img.size}")
    else:
        print("    [WARNING] No content detected! Using full image.")

    # 3. Smart Resize to Maximize Resolution
    # We want height to be exactly 48px to fill the sprite height
    aspect_ratio = ref_img.width / ref_img.height
    target_h = 48
    target_w = int(target_h * aspect_ratio)
    
    ref_img = ref_img.resize((target_w, target_h), Image.LANCZOS)
    print(f"[3] Resized to {target_w}x{target_h} (Aspect Ratio preserved)")

    # 4. Create 64x64 Canvas (PixelLab Requirement)
    canvas_w, canvas_h = 64, 64
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    
    # 5. Center the Sprite
    x_pos = (canvas_w - target_w) // 2
    y_pos = (canvas_h - target_h) // 2
    canvas.paste(ref_img, (x_pos, y_pos))
    print(f"[4] Pasted at ({x_pos}, {y_pos}) on {canvas_w}x{canvas_h} canvas")
    
    # 6. Debug Guides
    debug_canvas = canvas.copy()
    draw = ImageDraw.Draw(debug_canvas)
    draw.rectangle([x_pos, y_pos, x_pos + target_w - 1, y_pos + target_h - 1], outline="red") # Content
    
    # Draw blue safety box (32x48 centered)
    safe_w, safe_h = 32, 48
    safe_x = (64 - safe_w) // 2
    safe_y = (64 - safe_h) // 2
    draw.rectangle([safe_x, safe_y, safe_x + safe_w - 1, safe_y + safe_h - 1], outline="blue")
    
    # 7. Save
    canvas.save(VERIFY_PATH)
    debug_path = OUTPUT_DIR / "verify_input_canvas_debug.png"
    debug_canvas.save(debug_path)
    
    print(f"\n[SUCCESS] Verification images saved:")
    print(f"  Input for API:   {VERIFY_PATH}")
    print(f"  Debug Guide:     {debug_path}")
    print("\nPlease inspect: content (red) should be maximized within safe area (blue).")

if __name__ == "__main__":
    verify_canvas()
