#!/usr/bin/env python3
"""
Comprehensive Model Test Suite for ARDK

Tests:
1. Text-to-Image (backgrounds and sprites) across all working models
2. Image-to-Image (BFL Kontext and Pollinations)
3. Full conversion pipeline (NES, Genesis, cross-gen)

All outputs saved to Model_Test/ directory with organized subfolders.
"""

import sys
import os
import json
import time
import base64
import urllib.request
import hashlib
from pathlib import Path
from io import BytesIO
from datetime import datetime
from typing import Optional, Dict, List, Any

sys.path.insert(0, str(Path(__file__).parent))

from PIL import Image
from configs.api_keys import POLLINATIONS_API_KEY, BFL_API_KEY
from asset_generators.cross_gen_converter import CrossGenConverter

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
MODEL_TEST_DIR = PROJECT_ROOT / "Model_Test"
SOURCE_IMAGE = PROJECT_ROOT / "conversion_test_output" / "0_original.png"

# Text-to-image models to test
# Based on Pollinations pricing:
#   flux, zimage: 0.0002/image (cheapest)
#   turbo: 0.0003/image
#   seedream, kontext: 0.03-0.04/image
#   gptimage, nanobanana: token-based (more expensive)
TXT2IMG_MODELS = [
    'flux',           # 0.0002/image - CHEAPEST, best for pixel art
    'flux-pro',
    'flux-realism',
    'flux-anime',
    'turbo',          # 0.0003/image - fast
    'zimage',         # 0.0002/image - has 2x upscale built-in
    'seedream-3.0',
    'seedream-4.5-pro',
    'gptimage',
    'gptimage-large',
    'nanobanana',     # Gemini-based, good quality (transient errors possible)
]

# Image-to-image models (Pollinations)
IMG2IMG_MODELS = [
    'gptimage-large',
    'nanobanana',
]

# Test dimensions for backgrounds
BG_DIMENSIONS = [
    (320, 224),  # Genesis
    (256, 240),  # NES
    (512, 384),  # 4:3 scaled
]

# Sprite sheet dimensions
SPRITE_DIMENSIONS = (256, 256)

# Prompts - styled like original test image (cyberpunk background)
BG_PROMPT = "16-bit pixel art cyberpunk city background, neon pink and blue lights, night sky with stars, futuristic buildings, side-scrolling video game style, sega genesis graphics, clean pixel edges, no text"

SPRITE_PROMPT = "16-bit pixel art sprite sheet, 4x4 grid layout, robot enemy character, red glowing eyes, idle and walk animation frames, retro video game style, dark metal body, transparent background, game asset, clean pixels"

# ============================================================================
# UTILITIES
# ============================================================================

def ensure_dirs():
    """Create all output directories."""
    dirs = [
        MODEL_TEST_DIR / "txt2img" / "backgrounds",
        MODEL_TEST_DIR / "txt2img" / "sprites",
        MODEL_TEST_DIR / "img2img" / "bfl",
        MODEL_TEST_DIR / "img2img" / "pollinations",
        MODEL_TEST_DIR / "conversions" / "nes",
        MODEL_TEST_DIR / "conversions" / "genesis",
        MODEL_TEST_DIR / "conversions" / "cross_gen",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def upload_catbox(image: Image.Image) -> Optional[str]:
    """Upload image to catbox.moe and return URL."""
    buffer = BytesIO()
    if image.mode != 'RGB':
        image = image.convert('RGB')
    image.save(buffer, format='PNG', optimize=True)
    image_data = buffer.getvalue()

    boundary = '----WebKitFormBoundary' + hashlib.md5(str(time.time()).encode()).hexdigest()[:16]
    body = b'\r\n'.join([
        f'--{boundary}'.encode(),
        b'Content-Disposition: form-data; name="reqtype"',
        b'',
        b'fileupload',
        f'--{boundary}'.encode(),
        b'Content-Disposition: form-data; name="fileToUpload"; filename="test.png"',
        b'Content-Type: image/png',
        b'',
        image_data,
        f'--{boundary}--'.encode(),
        b''
    ])

    req = urllib.request.Request(
        "https://catbox.moe/user/api.php",
        data=body,
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}', 'User-Agent': 'ARDK/1.0'},
        method='POST'
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return response.read().decode('utf-8').strip()
    except Exception as e:
        print(f"    Upload failed: {e}")
        return None


def image_to_base64(image: Image.Image) -> str:
    """Convert image to base64 data URL."""
    buffer = BytesIO()
    if image.mode != 'RGB':
        image = image.convert('RGB')
    image.save(buffer, format='PNG')
    b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{b64}"


def pollinations_txt2img(prompt: str, model: str, width: int, height: int, seed: int = None) -> Optional[Image.Image]:
    """Generate image using Pollinations text-to-image."""
    # Generate unique seed per model to avoid caching
    if seed is None:
        seed = hash(f"{model}{time.time()}") % 2147483647

    encoded_prompt = urllib.request.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?model={model}&width={width}&height={height}&nologo=true&seed={seed}"

    if POLLINATIONS_API_KEY:
        url += f"&token={POLLINATIONS_API_KEY}"

    headers = {'User-Agent': 'ARDK-ModelTest/1.0', 'Accept': 'image/*'}
    if POLLINATIONS_API_KEY:
        headers['Authorization'] = f'Bearer {POLLINATIONS_API_KEY}'

    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            content_type = response.headers.get('Content-Type', '')
            if 'image' not in content_type:
                return None
            return Image.open(BytesIO(response.read()))
    except Exception as e:
        print(f"    Error: {e}")
        return None


def pollinations_img2img(image: Image.Image, prompt: str, model: str, width: int, height: int) -> Optional[Image.Image]:
    """Transform image using Pollinations img2img."""
    # Upload image first
    image_url = upload_catbox(image)
    if not image_url:
        return None

    encoded_prompt = urllib.request.quote(prompt)
    url = f"https://gen.pollinations.ai/image/{encoded_prompt}?model={model}&width={width}&height={height}&nologo=true&image={image_url}"

    if POLLINATIONS_API_KEY:
        url += f"&token={POLLINATIONS_API_KEY}"

    headers = {'User-Agent': 'ARDK-ModelTest/1.0', 'Accept': 'image/*'}
    if POLLINATIONS_API_KEY:
        headers['Authorization'] = f'Bearer {POLLINATIONS_API_KEY}'

    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            content_type = response.headers.get('Content-Type', '')
            if 'image' not in content_type:
                return None
            img = Image.open(BytesIO(response.read()))
            # Resize to target if different
            if img.width != width or img.height != height:
                img = img.resize((width, height), Image.LANCZOS)
            return img
    except Exception as e:
        print(f"    Error: {e}")
        return None


def bfl_kontext(image: Image.Image, prompt: str, use_url: bool = True) -> Optional[Image.Image]:
    """Transform image using BFL Flux Kontext."""
    if not BFL_API_KEY:
        print("    BFL API key not set")
        return None

    # Prepare image data
    if use_url:
        image_data = upload_catbox(image)
        if not image_data:
            print("    Failed to upload image for BFL")
            # Fall back to base64
            image_data = image_to_base64(image)
            use_url = False
    else:
        image_data = image_to_base64(image)

    payload = {
        "prompt": prompt,
        "input_image": image_data,
    }

    headers = {
        'Content-Type': 'application/json',
        'accept': 'application/json',
        'x-key': BFL_API_KEY,
    }

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        "https://api.bfl.ai/v1/flux-kontext-pro",
        data=data,
        headers=headers,
        method='POST'
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode('utf-8'))

        task_id = result.get('id')
        polling_url = result.get('polling_url')

        if not task_id:
            print("    No task ID in BFL response")
            return None

        # Poll for result
        for poll_num in range(90):
            time.sleep(1)
            try:
                poll_req = urllib.request.Request(
                    polling_url,
                    headers={'x-key': BFL_API_KEY, 'accept': 'application/json'}
                )
                with urllib.request.urlopen(poll_req, timeout=30) as poll_resp:
                    poll_result = json.loads(poll_resp.read().decode('utf-8'))

                status = poll_result.get('status', 'Unknown')

                if status == 'Ready':
                    sample_url = poll_result.get('result', {}).get('sample')
                    if sample_url:
                        img_req = urllib.request.Request(sample_url)
                        with urllib.request.urlopen(img_req, timeout=60) as img_resp:
                            return Image.open(BytesIO(img_resp.read()))

                elif status == 'Error':
                    error = poll_result.get('error', 'Unknown error')
                    print(f"    BFL error: {error}")
                    # If URL failed, try base64
                    if use_url:
                        print("    Retrying with base64...")
                        return bfl_kontext(image, prompt, use_url=False)
                    return None

            except urllib.error.HTTPError as e:
                if e.code == 500 and use_url:
                    print(f"    BFL URL failed (500), retrying with base64...")
                    return bfl_kontext(image, prompt, use_url=False)
                print(f"    Poll error: {e}")
                return None

        print("    BFL timeout")
        return None

    except Exception as e:
        print(f"    BFL error: {e}")
        if use_url:
            print("    Retrying with base64...")
            return bfl_kontext(image, prompt, use_url=False)
        return None


# ============================================================================
# TEST FUNCTIONS
# ============================================================================

def test_txt2img_backgrounds():
    """Test text-to-image models for background generation."""
    print("\n" + "="*70)
    print("TEXT-TO-IMAGE: BACKGROUNDS")
    print("="*70)

    output_dir = MODEL_TEST_DIR / "txt2img" / "backgrounds"
    results = {}

    # Use Genesis resolution as primary test
    width, height = 320, 224

    for model in TXT2IMG_MODELS:
        print(f"\n  [{model}] {width}x{height}...", end=" ", flush=True)
        start = time.time()

        img = pollinations_txt2img(BG_PROMPT, model, width, height)
        elapsed = time.time() - start

        if img:
            # Check dimensions
            exact = (img.width == width and img.height == height)
            save_path = output_dir / f"bg_{model}_{width}x{height}.png"
            img.save(save_path)

            results[model] = {
                'success': True,
                'requested': (width, height),
                'actual': (img.width, img.height),
                'exact_match': exact,
                'elapsed': elapsed,
                'path': str(save_path),
            }

            dim_str = f"{img.width}x{img.height}"
            if exact:
                print(f"OK {dim_str} ({elapsed:.1f}s)")
            else:
                print(f"RESIZED {dim_str} ({elapsed:.1f}s)")
        else:
            results[model] = {'success': False, 'elapsed': elapsed}
            print(f"FAILED ({elapsed:.1f}s)")

        time.sleep(2)  # Rate limit

    return results


def test_txt2img_sprites():
    """Test text-to-image models for sprite sheet generation."""
    print("\n" + "="*70)
    print("TEXT-TO-IMAGE: SPRITE SHEETS")
    print("="*70)

    output_dir = MODEL_TEST_DIR / "txt2img" / "sprites"
    results = {}

    width, height = SPRITE_DIMENSIONS

    for model in TXT2IMG_MODELS:
        print(f"\n  [{model}] {width}x{height}...", end=" ", flush=True)
        start = time.time()

        img = pollinations_txt2img(SPRITE_PROMPT, model, width, height)
        elapsed = time.time() - start

        if img:
            save_path = output_dir / f"sprite_{model}_{width}x{height}.png"
            img.save(save_path)

            results[model] = {
                'success': True,
                'actual': (img.width, img.height),
                'elapsed': elapsed,
                'path': str(save_path),
            }
            print(f"OK {img.width}x{img.height} ({elapsed:.1f}s)")
        else:
            results[model] = {'success': False, 'elapsed': elapsed}
            print(f"FAILED ({elapsed:.1f}s)")

        time.sleep(2)

    return results


def test_img2img_pollinations(source_image: Image.Image):
    """Test Pollinations img2img models."""
    print("\n" + "="*70)
    print("IMAGE-TO-IMAGE: POLLINATIONS")
    print("="*70)

    output_dir = MODEL_TEST_DIR / "img2img" / "pollinations"
    results = {}

    prompt = "enhance detail, add texture and shading, preserve composition"
    width, height = 496, 480  # 2x NES upscale

    for model in IMG2IMG_MODELS:
        print(f"\n  [{model}] {source_image.width}x{source_image.height} -> {width}x{height}...", end=" ", flush=True)
        start = time.time()

        img = pollinations_img2img(source_image, prompt, model, width, height)
        elapsed = time.time() - start

        if img:
            save_path = output_dir / f"img2img_{model}.png"
            img.save(save_path)

            results[model] = {
                'success': True,
                'actual': (img.width, img.height),
                'elapsed': elapsed,
                'path': str(save_path),
            }
            print(f"OK {img.width}x{img.height} ({elapsed:.1f}s)")
        else:
            results[model] = {'success': False, 'elapsed': elapsed}
            print(f"FAILED ({elapsed:.1f}s)")

        time.sleep(2)

    return results


def test_img2img_bfl(source_image: Image.Image):
    """Test BFL Kontext img2img (URL and base64)."""
    print("\n" + "="*70)
    print("IMAGE-TO-IMAGE: BFL KONTEXT")
    print("="*70)

    output_dir = MODEL_TEST_DIR / "img2img" / "bfl"
    results = {}

    # BFL Kontext needs action-oriented edit instructions, not descriptive prompts
    prompt = "Upscale this pixel art image to higher resolution. Add fine details, texture, and smooth gradients while preserving the original composition and color palette. Enhance sharpness and add subtle shading to make it look like professional 16-bit video game art."

    # Test with URL first
    print(f"\n  [bfl-kontext-url] Trying URL method...", end=" ", flush=True)
    start = time.time()
    img = bfl_kontext(source_image, prompt, use_url=True)
    elapsed = time.time() - start

    if img:
        save_path = output_dir / f"bfl_kontext_url.png"
        img.save(save_path)
        results['bfl-kontext-url'] = {
            'success': True,
            'actual': (img.width, img.height),
            'elapsed': elapsed,
            'path': str(save_path),
        }
        print(f"OK {img.width}x{img.height} ({elapsed:.1f}s)")
    else:
        results['bfl-kontext-url'] = {'success': False, 'elapsed': elapsed}
        print(f"FAILED ({elapsed:.1f}s)")

    time.sleep(2)

    # Test with base64
    print(f"\n  [bfl-kontext-base64] Trying base64 method...", end=" ", flush=True)
    start = time.time()
    img = bfl_kontext(source_image, prompt, use_url=False)
    elapsed = time.time() - start

    if img:
        save_path = output_dir / f"bfl_kontext_base64.png"
        img.save(save_path)
        results['bfl-kontext-base64'] = {
            'success': True,
            'actual': (img.width, img.height),
            'elapsed': elapsed,
            'path': str(save_path),
        }
        print(f"OK {img.width}x{img.height} ({elapsed:.1f}s)")
    else:
        results['bfl-kontext-base64'] = {'success': False, 'elapsed': elapsed}
        print(f"FAILED ({elapsed:.1f}s)")

    return results


def test_conversions(source_image: Image.Image):
    """Test full conversion pipeline with multi-model support."""
    print("\n" + "="*70)
    print("CONVERSIONS: NES / GENESIS / CROSS-GEN (Multi-Model)")
    print("="*70)

    results = {}

    # Initialize converter with multi-model enabled
    converter = CrossGenConverter(
        debug=True,
        debug_dir=MODEL_TEST_DIR / "conversions" / "debug",
        multi_model=True,
    )

    # Test 1: NES conversion
    print("\n  [NES] Converting to NES...")
    start = time.time()
    nes_result = converter.adapt_to_platform(
        image=source_image,
        target_platform="nes",
        description="cyberpunk city background with neon lights",
    )
    elapsed = time.time() - start

    if nes_result.success:
        nes_img = nes_result.converted_image
        save_path = MODEL_TEST_DIR / "conversions" / "nes" / "nes_output.png"
        nes_img.save(save_path)
        results['nes'] = {
            'success': True,
            'size': (nes_img.width, nes_img.height),
            'elapsed': elapsed,
            'path': str(save_path),
        }
        print(f"    OK {nes_img.width}x{nes_img.height} ({elapsed:.1f}s)")
    else:
        results['nes'] = {'success': False, 'errors': nes_result.errors}
        nes_img = None
        print(f"    FAILED: {nes_result.errors}")

    # Test 2: Genesis direct conversion
    print("\n  [Genesis Direct] Converting to Genesis...")
    start = time.time()
    genesis_result = converter.adapt_to_platform(
        image=source_image,
        target_platform="genesis",
        description="cyberpunk city background with neon lights",
    )
    elapsed = time.time() - start

    if genesis_result.success:
        genesis_img = genesis_result.converted_image
        save_path = MODEL_TEST_DIR / "conversions" / "genesis" / "genesis_direct.png"
        genesis_img.save(save_path)
        results['genesis_direct'] = {
            'success': True,
            'size': (genesis_img.width, genesis_img.height),
            'elapsed': elapsed,
            'path': str(save_path),
        }
        print(f"    OK {genesis_img.width}x{genesis_img.height} ({elapsed:.1f}s)")
    else:
        results['genesis_direct'] = {'success': False, 'errors': genesis_result.errors}
        print(f"    FAILED: {genesis_result.errors}")

    # Test 3: Cross-gen NES -> Genesis
    if nes_img:
        print("\n  [Cross-Gen] NES -> 16-bit tier -> Genesis...")
        start = time.time()

        # Stage 1: Upscale to 16-bit tier
        tier_result = converter.upscale_to_16bit(
            image=nes_img,
            source_platform="nes",
            target_platform="16bit",
            description="cyberpunk city background with neon lights",
            scale_factor=2,
            tier_only=True,
        )

        if tier_result.success:
            tier_img = tier_result.converted_image
            tier_path = MODEL_TEST_DIR / "conversions" / "cross_gen" / "16bit_tier.png"
            tier_img.save(tier_path)
            print(f"    Stage 1 OK: {tier_img.width}x{tier_img.height}")

            # Stage 2: Adapt to Genesis
            genesis_upgrade = converter.adapt_to_platform(
                image=tier_img,
                target_platform="genesis",
                description="cyberpunk city background with neon lights",
            )

            elapsed = time.time() - start

            if genesis_upgrade.success:
                final_img = genesis_upgrade.converted_image
                save_path = MODEL_TEST_DIR / "conversions" / "cross_gen" / "genesis_from_nes.png"
                final_img.save(save_path)

                results['cross_gen'] = {
                    'success': True,
                    'size': (final_img.width, final_img.height),
                    'elapsed': elapsed,
                    'tier_path': str(tier_path),
                    'final_path': str(save_path),
                    'ai_model': tier_result.metadata.get('ai_model', 'unknown'),
                }
                print(f"    Stage 2 OK: {final_img.width}x{final_img.height} ({elapsed:.1f}s)")
            else:
                results['cross_gen'] = {'success': False, 'errors': genesis_upgrade.errors}
                print(f"    Stage 2 FAILED: {genesis_upgrade.errors}")
        else:
            elapsed = time.time() - start
            results['cross_gen'] = {'success': False, 'errors': tier_result.errors}
            print(f"    Stage 1 FAILED: {tier_result.errors}")
    else:
        results['cross_gen'] = {'success': False, 'errors': ['NES conversion failed']}
        print("    SKIPPED (NES failed)")

    return results


def generate_report(all_results: Dict):
    """Generate a summary report."""
    print("\n" + "="*70)
    print("SUMMARY REPORT")
    print("="*70)

    report_lines = [
        "MODEL TEST SUITE REPORT",
        f"Generated: {datetime.now().isoformat()}",
        "="*60,
        "",
    ]

    # Text-to-image backgrounds
    if 'txt2img_backgrounds' in all_results:
        print("\nText-to-Image Backgrounds:")
        report_lines.append("TEXT-TO-IMAGE BACKGROUNDS")
        report_lines.append("-"*40)
        for model, data in all_results['txt2img_backgrounds'].items():
            status = "OK" if data.get('success') else "FAILED"
            dims = f"{data.get('actual', ('?','?'))[0]}x{data.get('actual', ('?','?'))[1]}" if data.get('success') else "N/A"
            print(f"  {model:<20} {status:<8} {dims}")
            report_lines.append(f"  {model}: {status} {dims}")
        report_lines.append("")

    # Text-to-image sprites
    if 'txt2img_sprites' in all_results:
        print("\nText-to-Image Sprites:")
        report_lines.append("TEXT-TO-IMAGE SPRITES")
        report_lines.append("-"*40)
        for model, data in all_results['txt2img_sprites'].items():
            status = "OK" if data.get('success') else "FAILED"
            dims = f"{data.get('actual', ('?','?'))[0]}x{data.get('actual', ('?','?'))[1]}" if data.get('success') else "N/A"
            print(f"  {model:<20} {status:<8} {dims}")
            report_lines.append(f"  {model}: {status} {dims}")
        report_lines.append("")

    # Img2img
    if 'img2img_pollinations' in all_results:
        print("\nImage-to-Image Pollinations:")
        report_lines.append("IMAGE-TO-IMAGE POLLINATIONS")
        report_lines.append("-"*40)
        for model, data in all_results['img2img_pollinations'].items():
            status = "OK" if data.get('success') else "FAILED"
            print(f"  {model:<20} {status}")
            report_lines.append(f"  {model}: {status}")
        report_lines.append("")

    if 'img2img_bfl' in all_results:
        print("\nImage-to-Image BFL:")
        report_lines.append("IMAGE-TO-IMAGE BFL")
        report_lines.append("-"*40)
        for model, data in all_results['img2img_bfl'].items():
            status = "OK" if data.get('success') else "FAILED"
            print(f"  {model:<20} {status}")
            report_lines.append(f"  {model}: {status}")
        report_lines.append("")

    # Conversions
    if 'conversions' in all_results:
        print("\nConversions:")
        report_lines.append("CONVERSIONS")
        report_lines.append("-"*40)
        for conv, data in all_results['conversions'].items():
            status = "OK" if data.get('success') else "FAILED"
            size = f"{data.get('size', ('?','?'))[0]}x{data.get('size', ('?','?'))[1]}" if data.get('success') else "N/A"
            print(f"  {conv:<20} {status:<8} {size}")
            report_lines.append(f"  {conv}: {status} {size}")

    # Save report
    report_path = MODEL_TEST_DIR / "test_report.txt"
    with open(report_path, 'w') as f:
        f.write('\n'.join(report_lines))
    print(f"\nReport saved: {report_path}")

    return report_path


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("="*70)
    print("ARDK MODEL TEST SUITE")
    print("="*70)
    print(f"Output: {MODEL_TEST_DIR}")
    print(f"Source: {SOURCE_IMAGE}")

    # Setup
    ensure_dirs()

    # Load source image
    if not SOURCE_IMAGE.exists():
        print(f"ERROR: Source image not found: {SOURCE_IMAGE}")
        return 1

    source_img = Image.open(SOURCE_IMAGE)
    print(f"Source loaded: {source_img.width}x{source_img.height}")

    # Also load NES version for img2img tests
    nes_path = PROJECT_ROOT / "conversion_test_output" / "1_nes_from_original.png"
    if nes_path.exists():
        nes_img = Image.open(nes_path)
        print(f"NES version loaded: {nes_img.width}x{nes_img.height}")
    else:
        nes_img = None
        print("NES version not found, will generate")

    all_results = {}

    # Run tests
    all_results['txt2img_backgrounds'] = test_txt2img_backgrounds()
    all_results['txt2img_sprites'] = test_txt2img_sprites()

    if nes_img:
        all_results['img2img_pollinations'] = test_img2img_pollinations(nes_img)
        all_results['img2img_bfl'] = test_img2img_bfl(nes_img)

    all_results['conversions'] = test_conversions(source_img)

    # Generate report
    generate_report(all_results)

    print("\n" + "="*70)
    print("TEST COMPLETE")
    print(f"All outputs in: {MODEL_TEST_DIR}")
    print("="*70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
