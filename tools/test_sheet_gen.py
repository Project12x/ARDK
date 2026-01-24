#!/usr/bin/env python3
"""
Multimodal Sprite Sheet Generator with Smart Downscaling.

Generates 8-direction sprite sheets using Pollinations (Flux/GPT/NanoBanana)
and applies smart downscaling to convert "HD Pixel Art" (big blocks)
into native 1:1 game assets.
"""

import os
import math
import urllib.request
import urllib.parse
import numpy as np
from pathlib import Path
from io import BytesIO
from PIL import Image

API_KEY = os.environ.get("POLLINATIONS_API_KEY", "sk_pHTAsUugsKvRUwFfxzOnpStVkpROBgzM")
OUTPUT_DIR = Path("projects/epoch/res/sprites/hero_concepts/sheets")

PROMPT = (
    "sprite sheet of a 90s grunge skater adventurer, "
    "messy brown hair, red backwards cap, red flannel shirt, blue baggy jeans, "
    "holding orange laser gun. "
    "showing 8 directional rotation angles (front, back, side, diagonals), "
    "clean white background, 16-bit Sega Genesis pixel art style, "
    "uniform grid layout, high contrast"
)

def smart_downsample(img: Image.Image, target_h: int = 48) -> Image.Image:
    """
    Downsamples 'HD Pixel Art' (where 1 logical pixel = N real pixels)
    to actual 1:1 pixel art.
    """
    # 1. Convert to numpy to analyze pixel grid
    arr = np.array(img)
    
    # 2. Estimate logical pixel size (block size)
    # Simple heuristic: Look for smallest frequency of color changes
    # For now, we'll try to determine scaling factor based on target height
    # assuming the AI generated roughly the right proportions.
    
    w, h = img.size
    
    # Identify the character bounding box to ignore empty space
    # (Simplified: assume character fills most of the vertical space in a row)
    
    # Heuristic: If image is 1024 high and we want 48, scale is ~21.3
    # But usually AI generates a sheet. Let's assume the input is a single sprite for this logic,
    # or the sheet itself uses consistent block sizes.
    
    # Let's try to detect the "blockiness"
    # Calculate differences between adjacent pixels
    # If it's pixel art upscaled, patterns will repeat every N pixels.
    
    scale_factor = h / target_h
    # Round to nearest integer if close
    if abs(scale_factor - round(scale_factor)) < 0.1:
        scale_factor = round(scale_factor)
        
    new_w = int(w / scale_factor)
    new_h = int(h / scale_factor)
    
    print(f"  [Downsample] Scaling {w}x{h} -> {new_w}x{new_h} (Factor: {scale_factor:.2f})")
    
    # NEAREST is crucial for preserving the "crisp" pixel edges if it was integer scaled
    # LANCZOS is better if it was generated as a "painting of pixel art"
    
    # Let's try NEAREST first to see if it snaps to grid
    return img.resize((new_w, new_h), Image.NEAREST)

def generate_sheet(model: str):
    print(f"\n[{model}] Generating Sheet...")
    
    encoded = urllib.parse.quote(PROMPT)
    # Requesting larger image for a sheet
    width = 1024 if model == "flux" else 1024 # Some models limit to 1024
    height = 512 # Wide layout
    
    url = (
        f"https://gen.pollinations.ai/image/{encoded}"
        f"?width={width}&height={height}"
        f"&model={model}&key={API_KEY}&seed=55"
        f"&nologo=true" # Try to avoid watermarks if supported
    )
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
            
        img = Image.open(BytesIO(data))
        
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        img.save(OUTPUT_DIR / f"sheet_{model}_raw.png")
        print(f"  [OK] Saved Raw: {img.size}")
        
        # Determine likely sprite height in the sheet
        # This is tricky without CV. 
        # For this test, we'll just resize the whole sheet by a fixed factor 
        # to approximate 'game ready' assets.
        # Assuming AI makes character ~full height of row.
        
        # If sheet is 1024x512, and has 1 row of sprites...
        # A sprite 32x48 scaled up x16 is 512x768.
        # Let's try to downscale the whole sheet to fit 48px height if it's 1 row.
        
        # Simple test: Downscale entire sheet to 25% and 10%
        
        img_q = img.resize((img.width // 8, img.height // 8), Image.NEAREST)
        img_q.save(OUTPUT_DIR / f"sheet_{model}_pixel_x8.png")
        
        return True
            
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False

if __name__ == "__main__":
    print("MULTIMODAL SPRITE SHEET TEST")
    models = ["flux", "gptimage-large", "nanobanana"]
    for m in models:
        generate_sheet(m)
