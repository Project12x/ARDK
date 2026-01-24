#!/usr/bin/env python3
"""
Composite Hero Pipeline.

1. Generate high-quality concept using Pollinations (GPT-4/Flux)
2. Use PixelLab to generate 8-way rotations from that concept
"""

import os
import time
import urllib.request
import urllib.parse
from pathlib import Path
from io import BytesIO
from PIL import Image
import sys

# Import PixelLab client
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))
from asset_generators.pixellab_client import PixelLabClient

API_KEY = os.environ.get("POLLINATIONS_API_KEY", "sk_pHTAsUugsKvRUwFfxzOnpStVkpROBgzM")
OUTPUT_DIR = Path("projects/epoch/res/sprites/hero_composite")

PROMPT = (
    "pixel art sprite of a 90s grunge skater adventurer, "
    "messy brown hair, red backwards cap, red plaid flannel shirt, blue baggy jeans, "
    "holding orange laser gun, side view, "
    "clean white background, 16-bit Sega Genesis style, "
    "high contrast, crisp edges"
)

def generate_concept(model: str = "gptimage-large") -> Path:
    """Generate the base concept image."""
    print(f"\n[1] Generating Concept ({model})...")
    
    encoded = urllib.parse.quote(PROMPT)
    # 512x768 is a good ratio for a tall sprite
    url = f"https://gen.pollinations.ai/image/{encoded}?width=512&height=768&model={model}&key={API_KEY}&seed=88"
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
            
        img = Image.open(BytesIO(data))
        
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        # Save raw high-res
        raw_path = OUTPUT_DIR / "concept_raw.png"
        img.save(raw_path)
        print(f"  [OK] Saved Raw: {raw_path} ({img.size})")
        
        # Downsample for PixelLab input (it expects sprites, not huge images)
        # PixelLab reference image should be roughly sprite-sized or slightly larger
        # Let's resize to 64x96 (2x genesis size) for good reference detail
        ref_img = img.resize((64, 96), Image.LANCZOS)
        ref_path = OUTPUT_DIR / "concept_ref.png"
        ref_img.save(ref_path)
        print(f"  [OK] Saved Reference: {ref_path} ({ref_img.size})")
        
        return ref_path
            
    except Exception as e:
        print(f"  [FAIL] {e}")
        return None

def generate_rotations(ref_path: Path):
    """Generate 8-way rotations using PixelLab."""
    print("\n[2] Generating Rotations (PixelLab)...")
    
    # Increase max calls to EXACTLY what happens (7 rotations + 1 original = 8)
    client = PixelLabClient(max_calls=8)
    
    # Load reference image and resize to target if needed
    ref_img = Image.open(ref_path)
    
    # Post-process concept ref to ensure it fits brilliantly in 64x64
    # Genesis sprite target is 32x48. 
    # Let's resize the reference to 32x48 first to establish scale
    ref_img = ref_img.resize((32, 48), Image.LANCZOS)
    
    # Create 64x64 canvas (required by PixelLab)
    # Paste 32x48 in center
    canvas = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    # Center horizontally: (64-32)/2 = 16
    # Center vertically: (64-48)/2 = 8
    canvas.paste(ref_img, (16, 8))
    
    # Use generate_directional_sprites (uses rotate endpoint internally)
    # This generates 4 or 8 directions from a reference image
    print("  Using 64x64 canvas with centered 32x48 sprite")
    
    results = client.generate_directional_sprites(
        reference_image=canvas,
        directions=8,
        width=64,
        height=64,
        from_direction="east"
    )
    
    # Results is a dictionary {direction_name: GenerationResult}
    if results:
        print(f"  [OK] Generated {len(results)} sprites")
        success_count = 0
        for direction, res in results.items():
            if res.success and res.image:
                # Post-process: Crop back to 32x48
                # We know we pasted at (16, 8)
                left = 16
                top = 8
                right = 16 + 32
                bottom = 8 + 48
                final_img = res.image.crop((left, top, right, bottom))
                
                # Save final 32x48
                save_path = OUTPUT_DIR / f"hero_{direction}.png"
                final_img.save(save_path)
                print(f"    Saved: {save_path.name}")
                success_count += 1
            else:
                print(f"    [FAIL] {direction}: {res.error}")
        
        return success_count > 0
    else:
        print(f"  [FAIL] No results returned")
        return False

if __name__ == "__main__":
    print("COMPOSITE HERO PIPELINE")
    
    # 1. Generate Concept ( Reuse if exists )
    ref_path = OUTPUT_DIR / "concept_ref.png"
    
    if not ref_path.exists():
        ref_path = generate_concept("gptimage-large")
    else:
        print(f"\n[1] Concept exists: {ref_path}")
    
    if ref_path and ref_path.exists():
        # 2. Generate Rotations
        # Use existing session lock if present (delete if stale)
        lock_file = Path(__file__).parent.parent / ".pixellab_session.lock"
        if lock_file.exists():
            print(f"  Removing stale lock file: {lock_file}")
            try:
                lock_file.unlink()
            except:
                pass
                
        generate_rotations(ref_path)
