#!/usr/bin/env python3
"""
Single Rotation Test (Low Cost).

1. Prepares canvas exactly like verify harness.
2. Calls PixelLab 'rotate' endpoint for ONE direction (North-West) only.
3. Saves result for quality check.
"""

from pathlib import Path
from typing import Tuple, Optional, List, Dict
from PIL import Image, ImageDraw
import collections
import os
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))
from tools.asset_generators.pixellab_client import PixelLabClient

OUTPUT_DIR = Path("projects/epoch/res/sprites/hero_composite")
CONCEPT_PATH = OUTPUT_DIR / "concept_ref.png"

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
        
        try:
            ImageDraw.floodfill(scratch, (0, 0), (0, 0, 0, 0), thresh=self.tolerance)
            ImageDraw.floodfill(scratch, (w-1, 0), (0, 0, 0, 0), thresh=self.tolerance)
            ImageDraw.floodfill(scratch, (0, h-1), (0, 0, 0, 0), thresh=self.tolerance)
            ImageDraw.floodfill(scratch, (w-1, h-1), (0, 0, 0, 0), thresh=self.tolerance)
        except Exception as e:
            print(f"      [SmartBg] Flood fill warning: {e}")
            
        scratch_alpha = scratch.split()[3]
        return scratch_alpha.point(lambda x: 255 if x > 0 else 0, mode='1')

def run_single_test():
    print("SINGLE ROTATION TEST (North-West)")
    print(f"Loading: {CONCEPT_PATH}")
    
    if not CONCEPT_PATH.exists():
        print(f"[FAIL] Missing concept file")
        return

    # 1. Prepare image (Same logic as verification)
    ref_img = Image.open(CONCEPT_PATH)
    
    # Auto-Crop
    detector = FloodFillBackgroundDetector(tolerance=20)
    mask = detector.get_content_mask(ref_img)
    bbox = mask.getbbox()
    if bbox:
        ref_img = ref_img.crop(bbox)
        print(f"[1] Auto-cropped to: {bbox}")
    
    # Resize to 48px height
    aspect_ratio = ref_img.width / ref_img.height
    target_h = 48
    target_w = int(target_h * aspect_ratio)
    ref_img = ref_img.resize((target_w, target_h), Image.LANCZOS)
    print(f"[2] Resized to {target_w}x{target_h}")

    # Center on 64x64 canvas
    canvas = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    x_pos = (64 - target_w) // 2
    y_pos = (64 - target_h) // 2
    canvas.paste(ref_img, (x_pos, y_pos))
    print(f"[3] Pasted on 64x64 canvas")
    
    # 2. Init Client
    print("\n[4] Initializing PixelLab Client...")
    client = PixelLabClient(max_calls=4) # Plenty for 1 call
    
    # 3. Call Rotate Endpoint Directly
    print("    Requesting rotation: east -> north-west")
    result = client.rotate(
        from_image=canvas,
        width=64,
        height=64,
        from_direction="east", # Side view
        to_direction="north-west"
    )
    
    if result.success and result.image:
        print("[SUCCESS] Rotation received!")
        save_path = OUTPUT_DIR / "test_rotation_nw.png"
        result.image.save(save_path)
        
        # Also save a cropped version for final preview
        # We know content is roughly in the center, but let's auto-crop again
        mask = detector.get_content_mask(result.image)
        bbox = mask.getbbox()
        if bbox:
            final = result.image.crop(bbox)
            final_path = OUTPUT_DIR / "test_rotation_nw_cropped.png"
            final.save(final_path)
            print(f"    Saved Final: {final_path} ({final.size})")
        
        print(f"    Saved Raw:   {save_path}")
    else:
        print(f"[FAIL] API Error: {result.error}")

if __name__ == "__main__":
    # Ensure no stale lock
    lock = Path(".pixellab_session.lock")
    if lock.exists(): lock.unlink()
        
    run_single_test()
