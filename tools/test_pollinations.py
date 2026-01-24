#!/usr/bin/env python3
"""Quick Pollinations test with API key."""

import os
import urllib.request
import urllib.parse
from pathlib import Path
from io import BytesIO
from PIL import Image

API_KEY = "sk_pHTAsUugsKvRUwFfxzOnpStVkpROBgzM"
OUTPUT_DIR = Path("projects/epoch/res/sprites/hero_concepts")

PROMPT = (
    "90s grunge skater kid teenage boy, messy brown hair, "
    "red backwards baseball cap, red plaid flannel shirt, "
    "baggy blue jeans, holding orange toy laser gun, "
    "full body side view, pixel art sprite style, "
    "16-bit Sega Genesis quality, detailed shading"
)

# Models to try
MODELS = ["flux", "gptimage-large", "nanobanana"]

def generate(model: str):
    print(f"\n[{model}] Generating...")
    
    encoded = urllib.parse.quote(PROMPT)
    url = f"https://gen.pollinations.ai/image/{encoded}?width=512&height=768&model={model}&key={API_KEY}&seed=42"
    
    print(f"  URL length: {len(url)}")
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            content_type = resp.headers.get("Content-Type", "unknown")
            data = resp.read()
            
        print(f"  Content-Type: {content_type}")
        print(f"  Size: {len(data)} bytes")
        
        if content_type.startswith("image"):
            img = Image.open(BytesIO(data))
            
            # Save high-res
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            highres_path = OUTPUT_DIR / f"hero_{model}_highres.png"
            img.save(highres_path)
            print(f"  [OK] Saved: {highres_path.name} ({img.size})")
            
            # Downsample to 32x48
            sprite = img.resize((32, 48), Image.LANCZOS)
            sprite_path = OUTPUT_DIR / f"hero_{model}_32x48.png"
            sprite.save(sprite_path)
            print(f"  [OK] Saved: {sprite_path.name}")
            
            return True
        else:
            print(f"  [FAIL] Not an image: {data[:100]}")
            return False
            
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("POLLINATIONS MULTIMODAL TEST")
    print("=" * 50)
    
    results = {}
    for model in MODELS:
        results[model] = generate(model)
    
    print("\n" + "=" * 50)
    print("RESULTS")
    for m, ok in results.items():
        print(f"  {m}: {'[OK]' if ok else '[FAIL]'}")
