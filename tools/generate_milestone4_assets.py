#!/usr/bin/env python3
"""
Master Asset Generation Script for Milestone 4.

Generates:
1. Hero (Rad Dude) - 8-way views (or 5 + mirror)
2. Dog (Fenrir) - 8-way views (or 5 + mirror)
3. Enemy (Virus) - Single Omni-directional view
4. Background (Wasteland) - Seamless Tileset

SAFETY FEATURES:
- Generation caching (avoid re-generating on decode failure)
- Budget enforcement (max generations, max cost)
- Dry-run mode (preview without API calls)
- Confirmation prompts before generation
- Mirror optimization (5 unique + 3 mirrored)
"""

import sys
import os
import time
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

# Import Pipeline tools
try:
    from asset_generators.pixellab_client import PixelLabClient, generate_genesis_sprite
    from asset_generators.generation_safeguards import (
        SafetyConfig, GenerationCache, BudgetTracker,
        apply_mirror_optimization, get_unique_directions,
        dry_run_report, estimate_cost
    )
except ImportError as e:
    print(f"CRITICAL ERROR: Could not import pipeline tools: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_CONFIG = SafetyConfig(
    max_generations_per_run=5,
    max_cost_per_run=0.50,
    require_confirmation=True,
    cache_dir=".pixellab_cache",
    dry_run=False
)

# Output Directories
BASE_RES_DIR = Path("projects/epoch/res")
SPRITE_DIR = BASE_RES_DIR / "sprites"
TILESET_DIR = BASE_RES_DIR / "tilesets"

# Asset Definitions (The "Art Bible" manifest)
ASSETS_TO_GENERATE = [
    {
        "key": "player_hero",
        "name": "hero",
        "category": "player",
        "description": "90s skater kid, red backwards cap, red flannel shirt, baggy jeans, holding toy laser gun, pixel art",
        "type": "8way",  # Uses create_character_8_directions
        "use_mirror": True,  # Generate 5 unique, mirror 3
        "width": 32,
        "height": 32,
    },
    {
        "key": "companion_fenrir",
        "name": "fenrir",
        "category": "companion",
        "description": "scruffy black and brown terrier dog, small energetic dog, cute but tough, pixel art",
        "type": "8way",
        "use_mirror": True,
        "width": 32,
        "height": 32,
    },
    {
        "key": "enemy_virus",
        "name": "virus",
        "category": "enemy",
        "description": "floating cyber virus monster, glitch aesthetic, geometric shapes, purple and cyan neon, no face",
        "type": "single",
        "width": 32,
        "height": 32,
    },
    {
        "key": "bg_wasteland",
        "name": "wasteland_bg",
        "category": "background",
        "description": "seamless tileable texture, dark purple digital wasteland ground, glitch artifacts, sega genesis style",
        "type": "tileset",
        "width": 64,
        "height": 64,
    }
]

# =============================================================================
# LOGGING
# =============================================================================

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("AssetGen")

# =============================================================================
# GENERATION FUNCTIONS
# =============================================================================

def generate_8way_character(
    client: PixelLabClient,
    cache: GenerationCache,
    budget: BudgetTracker,
    asset: Dict[str, Any],
    config: SafetyConfig
) -> bool:
    """Generate 8-way character using create_character_8_directions."""
    name = asset["name"]
    desc = asset["description"]
    width = asset.get("width", 32)
    height = asset.get("height", 32)
    use_mirror = asset.get("use_mirror", False)
    
    logger.info(f"=== Generating 8-way: {name} ===")
    
    # Check cache first
    if cache.has_cached_images(desc, width, height):
        logger.info(f"  Found cached images - loading from cache")
        images = cache.load_images(desc, width, height)
        if images:
            # Save to output dir
            for direction, img in images.items():
                out_path = SPRITE_DIR / f"{name}_{direction}.png"
                img.save(out_path)
            logger.info(f"  Restored {len(images)} images from cache")
            return True
    
    # Check for cached response (can decode without re-generating)
    if cache.has_cached_response(desc, width, height):
        logger.info(f"  Found cached response - attempting decode")
        # TODO: Implement decode from cached response
        # For now, continue to regenerate
    
    # Budget check
    if not budget.can_generate():
        logger.error(f"  Budget exhausted - skipping {name}")
        return False
    
    # Dry run check
    if config.dry_run:
        logger.info(f"  [DRY RUN] Would generate 8-way for: {desc[:50]}...")
        return True
    
    # Cache request params
    cache.save_request(desc, width, height, {
        "type": "8way",
        "use_mirror": use_mirror,
    })
    
    # Generate
    logger.info(f"  Calling API: create_character_8_directions")
    result = client.create_character_8_directions(
        description=desc,
        width=width,
        height=height,
        outline="medium",
        shading="soft",
        detail="medium",
        view="side",
        max_poll_attempts=20,
        poll_interval=5.0
    )
    
    if not result.success:
        logger.error(f"  FAILED: {result.error}")
        return False
    
    # Record generation
    budget.record_generation(result.cost_usd)
    
    # Build images dict from result
    images = {}
    directions = result.metadata.get("directions", [])
    for img, dir_name in zip(result.images, directions):
        images[dir_name] = img
    
    # Cache raw response (for future decode retry)
    # Note: We can't easily cache the raw response here since we processed it
    # Instead, cache the decoded images
    cache.save_images(desc, width, height, images)
    
    # Apply mirroring if configured
    if use_mirror:
        logger.info(f"  Applying mirror optimization")
        images = apply_mirror_optimization(images)
    
    # Save to output dir
    for direction, img in images.items():
        # Normalize direction names for filenames
        dir_filename = direction.replace("-", "_")
        out_path = SPRITE_DIR / f"{name}_{dir_filename}.png"
        img.save(out_path)
    
    logger.info(f"  SUCCESS: Saved {len(images)} images for {name}")
    return True


def generate_single_sprite(
    client: PixelLabClient,
    cache: GenerationCache,
    budget: BudgetTracker,
    asset: Dict[str, Any],
    config: SafetyConfig
) -> bool:
    """Generate a single sprite."""
    name = asset["name"]
    desc = asset["description"]
    width = asset.get("width", 32)
    height = asset.get("height", 32)
    
    logger.info(f"=== Generating single sprite: {name} ===")
    
    # Check cache
    if cache.has_cached_images(desc, width, height):
        logger.info(f"  Found cached image - loading from cache")
        images = cache.load_images(desc, width, height)
        if images:
            out_path = SPRITE_DIR / f"{name}.png"
            list(images.values())[0].save(out_path)
            logger.info(f"  Restored from cache")
            return True
    
    # Budget check
    if not budget.can_generate():
        logger.error(f"  Budget exhausted - skipping {name}")
        return False
    
    # Dry run check
    if config.dry_run:
        logger.info(f"  [DRY RUN] Would generate: {desc[:50]}...")
        return True
    
    # Generate
    logger.info(f"  Calling API: generate_genesis_sprite")
    img = generate_genesis_sprite(
        client=client,
        description=desc,
        width=width,
        height=height,
        use_v2=True
    )
    
    if not img:
        logger.error(f"  FAILED: No image returned")
        return False
    
    # Record generation
    budget.record_generation(0.003)  # Estimate
    
    # Cache and save
    cache.save_images(desc, width, height, {"single": img})
    
    out_path = SPRITE_DIR / f"{name}.png"
    img.save(out_path)
    
    logger.info(f"  SUCCESS: Saved {out_path}")
    return True


def generate_tileset(
    client: PixelLabClient,
    cache: GenerationCache,
    budget: BudgetTracker,
    asset: Dict[str, Any],
    config: SafetyConfig
) -> bool:
    """Generate a tileset."""
    name = asset["name"]
    desc = asset["description"]
    width = asset.get("width", 64)
    height = asset.get("height", 64)
    
    logger.info(f"=== Generating tileset: {name} ===")
    
    # Check cache
    if cache.has_cached_images(desc, width, height):
        logger.info(f"  Found cached tileset - loading from cache")
        images = cache.load_images(desc, width, height)
        if images:
            out_path = TILESET_DIR / f"{name}.png"
            list(images.values())[0].save(out_path)
            logger.info(f"  Restored from cache")
            return True
    
    # Budget check
    if not budget.can_generate():
        logger.error(f"  Budget exhausted - skipping {name}")
        return False
    
    # Dry run check
    if config.dry_run:
        logger.info(f"  [DRY RUN] Would generate tileset: {desc[:50]}...")
        return True
    
    # For tilesets, use the pixflux endpoint
    logger.info(f"  Calling API: generate_image_pixflux")
    result = client.generate_image_pixflux(
        description=desc,
        width=width,
        height=height,
        no_background=False  # Tilesets need background
    )
    
    if not result.success:
        logger.error(f"  FAILED: {result.error}")
        return False
    
    # Record generation
    budget.record_generation(result.cost_usd)
    
    # Cache and save
    img = result.image
    cache.save_images(desc, width, height, {"tileset": img})
    
    out_path = TILESET_DIR / f"{name}.png"
    img.save(out_path)
    
    logger.info(f"  SUCCESS: Saved {out_path}")
    return True

# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Generate game assets using PixelLab API")
    parser.add_argument("--dry-run", action="store_true", help="Preview without API calls")
    parser.add_argument("--no-confirm", action="store_true", help="Skip confirmation prompts")
    parser.add_argument("--max-gens", type=int, default=5, help="Max generations allowed")
    parser.add_argument("--max-cost", type=float, default=0.50, help="Max cost in USD")
    args = parser.parse_args()
    
    # Build config
    config = SafetyConfig(
        max_generations_per_run=args.max_gens,
        max_cost_per_run=args.max_cost,
        require_confirmation=not args.no_confirm,
        dry_run=args.dry_run
    )
    
    logger.info("=" * 60)
    logger.info("MASTER ASSET GENERATION")
    logger.info(f"  Dry run: {config.dry_run}")
    logger.info(f"  Max generations: {config.max_generations_per_run}")
    logger.info(f"  Max cost: ${config.max_cost_per_run:.2f}")
    logger.info("=" * 60)
    
    # Dry run report
    if config.dry_run:
        print(dry_run_report(ASSETS_TO_GENERATE, config))
        return
    
    # Confirmation prompt
    if config.require_confirmation:
        print("\nAssets to generate:")
        for i, asset in enumerate(ASSETS_TO_GENERATE, 1):
            print(f"  {i}. [{asset['type']}] {asset['name']}")
        
        est = estimate_cost(len(ASSETS_TO_GENERATE), 8)
        print(f"\nEstimated cost: ${est['estimated_cost_usd']:.4f}")
        print(f"Budget limit: ${config.max_cost_per_run:.2f}")
        
        response = input("\nProceed with generation? [y/N]: ").strip().lower()
        if response != 'y':
            print("Aborted.")
            return
    
    # Setup
    os.makedirs(SPRITE_DIR, exist_ok=True)
    os.makedirs(TILESET_DIR, exist_ok=True)
    
    cache = GenerationCache(config.cache_dir)
    budget = BudgetTracker(
        max_generations=config.max_generations_per_run,
        max_cost=config.max_cost_per_run
    )
    
    # Initialize client with generous call limit for polling
    client = PixelLabClient(max_calls=50)
    
    # Generate each asset
    success_count = 0
    for asset in ASSETS_TO_GENERATE:
        asset_type = asset.get("type", "single")
        
        if asset_type == "8way":
            success = generate_8way_character(client, cache, budget, asset, config)
        elif asset_type == "tileset":
            success = generate_tileset(client, cache, budget, asset, config)
        else:
            success = generate_single_sprite(client, cache, budget, asset, config)
        
        if success:
            success_count += 1
        
        # Check budget after each generation
        if not budget.can_generate():
            logger.warning("Budget exhausted - stopping")
            break
        
        # Rate limiting
        time.sleep(2.0)
    
    # Summary
    logger.info("=" * 60)
    logger.info(f"FINISHED: {success_count}/{len(ASSETS_TO_GENERATE)} assets generated")
    logger.info(f"Generations used: {budget.generations_used}/{budget.max_generations}")
    logger.info(f"Cost: ${budget.cost_used:.4f}/${budget.max_cost:.2f}")
    logger.info(f"Session cost: ${client.get_session_cost():.4f}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
