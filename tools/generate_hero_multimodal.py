#!/usr/bin/env python3
"""
Multimodal Hero Sprite Generation

Generates the hero character using multiple AI providers:
1. PixelLab - Native retro dimensions (32x48 for Genesis quality)
2. Pollinations/Flux - 1024px then downsample to sprite size

Genesis sprite reference: Zombies Ate My Neighbors uses ~24x48 to 32x48 sprites.
"""

import sys
import os
import urllib.request
import urllib.parse
from pathlib import Path
from io import BytesIO

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from PIL import Image

# =============================================================================
# CONFIGURATION
# =============================================================================

OUTPUT_DIR = Path(__file__).parent.parent / "projects/epoch/res/sprites/hero_concepts"

# Better hero description based on Art Bible
HERO_DESCRIPTION = """
90s grunge skater teenager, messy shoulder-length brown hair, 
backwards red baseball cap, open red plaid flannel shirt over white t-shirt,
baggy blue jeans with wallet chain, bright orange toy laser blaster in hand,
confident stance, side profile view, full body,
16-bit Sega Genesis pixel art style like Zombies Ate My Neighbors,
clean black outlines, proper shading, detailed sprite
""".strip().replace('\n', ' ')

# Short version for URL encoding
HERO_PROMPT_SHORT = (
    "90s grunge skater kid, messy brown hair, red backwards cap, "
    "red flannel shirt, baggy jeans, orange toy gun, side view, "
    "16-bit Sega Genesis pixel art sprite, detailed, full body"
)

# Genesis-appropriate sizes
GENESIS_SPRITE_SIZE = (32, 48)  # Width x Height (like ZAMN characters)
FLUX_RENDER_SIZE = (768, 1152)   # 2:3 aspect ratio, downsamples to 32x48

# =============================================================================
# PROVIDERS
# =============================================================================

def generate_pixellab(output_path: Path) -> bool:
    """Generate using PixelLab at native retro dimensions."""
    try:
        from asset_generators.pixellab_client import PixelLabClient
        
        print("\n[PixelLab] Generating at native Genesis size...")
        print(f"  Size: {GENESIS_SPRITE_SIZE[0]}x{GENESIS_SPRITE_SIZE[1]}")
        
        client = PixelLabClient(max_calls=10)
        
        result = client.generate_image_pixflux(
            description=HERO_DESCRIPTION,
            width=GENESIS_SPRITE_SIZE[0],
            height=GENESIS_SPRITE_SIZE[1],
            outline="single color black outline",
            shading="soft shading",
            detail="high detail",
            no_background=True
        )
        
        if result.success and result.image:
            result.image.save(output_path)
            print(f"[OK] Saved: {output_path.name}")
            return True
        else:
            print(f"[FAIL] {result.error}")
            return False
            
    except Exception as e:
        print(f"[FAIL] PixelLab error: {e}")
        return False


def generate_pollinations_flux(output_path: Path, model: str = "flux") -> bool:
    """Generate using Pollinations at high res, then downsample."""
    try:
        print(f"\n[Pollinations/{model}] Generating at high resolution...")
        print(f"  Render size: {FLUX_RENDER_SIZE[0]}x{FLUX_RENDER_SIZE[1]}")
        print(f"  Target size: {GENESIS_SPRITE_SIZE[0]}x{GENESIS_SPRITE_SIZE[1]}")
        
        encoded_prompt = urllib.parse.quote(HERO_PROMPT_SHORT)
        seed = 42
        
        # Correct Pollinations API endpoint
        api_key = os.environ.get("POLLINATIONS_API_KEY", "")
        
        image_url = (
            f"https://gen.pollinations.ai/image/{encoded_prompt}"
            f"?width={FLUX_RENDER_SIZE[0]}&height={FLUX_RENDER_SIZE[1]}"
            f"&seed={seed}&model={model}"
        )
        if api_key:
            image_url += f"&key={api_key}"
        
        print(f"  URL: {image_url[:80]}...")
        
        req = urllib.request.Request(image_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=120) as response:
            content_type = response.headers.get('Content-Type', 'unknown')
            print(f"  Content-Type: {content_type}")
            data = response.read()
            print(f"  Response size: {len(data)} bytes")
            
            # Debug: check if it's actually an image
            if not data[:4] in [b'\x89PNG', b'\xff\xd8\xff', b'GIF8', b'RIFF']:
                print(f"  WARNING: Response doesn't look like an image. First 100 bytes:")
                print(f"  {data[:100]}")
        
        # Load and downsample
        img_high = Image.open(BytesIO(data))
        print(f"  Received: {img_high.size}")
        
        # Downsample with Lanczos for quality
        img_sprite = img_high.resize(GENESIS_SPRITE_SIZE, Image.LANCZOS)
        
        # Save both versions
        high_res_path = output_path.with_name(output_path.stem + "_highres.png")
        img_high.save(high_res_path)
        img_sprite.save(output_path)
        
        print(f"[OK] Saved high-res: {high_res_path.name}")
        print(f"[OK] Saved sprite: {output_path.name}")
        return True
        
    except Exception as e:
        print(f"[FAIL] Pollinations error: {e}")
        return False


def generate_pollinations_turbo(output_path: Path) -> bool:
    """Generate using Pollinations Turbo model (faster, different style)."""
    try:
        print("\n[Pollinations/Turbo] Generating...")
        
        encoded_prompt = urllib.parse.quote(HERO_PROMPT_SHORT)
        seed = 123
        
        image_url = (
            f"https://pollinations.ai/p/{encoded_prompt}"
            f"?width={FLUX_RENDER_SIZE[0]}&height={FLUX_RENDER_SIZE[1]}"
            f"&seed={seed}&model=turbo"
        )
        
        req = urllib.request.Request(image_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=120) as response:
            data = response.read()
        
        img_high = Image.open(BytesIO(data))
        img_sprite = img_high.resize(GENESIS_SPRITE_SIZE, Image.LANCZOS)
        
        high_res_path = output_path.with_name(output_path.stem + "_highres.png")
        img_high.save(high_res_path)
        img_sprite.save(output_path)
        
        print(f"[OK] Saved: {output_path.name}")
        return True
        
    except Exception as e:
        print(f"[FAIL] Turbo error: {e}")
        return False


# =============================================================================
# MAIN
# =============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Multimodal hero sprite generation")
    parser.add_argument("--provider", choices=["pixellab", "flux", "turbo", "all"], 
                        default="all", help="Provider to use")
    args = parser.parse_args()
    
    print("=" * 60)
    print("MULTIMODAL HERO SPRITE GENERATION")
    print("=" * 60)
    print(f"Description: {HERO_PROMPT_SHORT[:60]}...")
    print(f"Genesis size: {GENESIS_SPRITE_SIZE}")
    print()
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    if args.provider in ["pixellab", "all"]:
        results["pixellab"] = generate_pixellab(
            OUTPUT_DIR / "hero_pixellab.png"
        )
    
    if args.provider in ["flux", "all"]:
        results["flux"] = generate_pollinations_flux(
            OUTPUT_DIR / "hero_flux.png"
        )
    
    if args.provider in ["turbo", "all"]:
        results["turbo"] = generate_pollinations_turbo(
            OUTPUT_DIR / "hero_turbo.png"
        )
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    for provider, success in results.items():
        status = "[OK]" if success else "[FAIL]"
        print(f"  {provider}: {status}")
    print(f"\nOutput directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
