#!/usr/bin/env python3
"""
Minimal test: Generate 1 sprite to verify image decoding works.
Uses generate_image_v2 (1 generation) instead of 8-way (8 generations).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from asset_generators.pixellab_client import PixelLabClient

OUTPUT_FILE = Path("test_single_sprite.png")

def main():
    print("=" * 50)
    print("SINGLE SPRITE TEST (1 generation)")
    print("=" * 50)
    
    client = PixelLabClient(max_calls=5)
    
    print("Generating single sprite...")
    result = client.generate_image_pixflux(
        description="pixel art skater kid, red cap, side view, 16-bit style",
        width=32,
        height=32,
        outline="single color black outline",
        shading="basic shading",
        detail="medium detail",
        no_background=True
    )
    
    if not result.success:
        print(f"[FAIL] {result.error}")
        return False
    
    if result.image:
        result.image.save(OUTPUT_FILE)
        print(f"[OK] Saved to {OUTPUT_FILE}")
        print(f"     Size: {result.image.size}")
        print(f"     Cost: ${result.cost_usd:.4f}")
        return True
    else:
        print("[FAIL] No image in result")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
