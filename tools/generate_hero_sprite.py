#!/usr/bin/env python3
"""
Generate Hero and Dog Sprites for Neon Survivors.

This script generates both the Hero (Rad Dude) and Fenrir (Dog) using
the PixelLab API with proper Genesis constraints:

1. Shared palette (both share PLAYER palette slot)
2. 5-way directions (mirror 3 at runtime)
3. 32x32 sprite size
4. Genesis-compatible generation settings

Art Bible References:
- Hero: 90s grunge skater, red backwards cap, red flannel, baggy jeans, toy laser gun
- Dog: Scruffy black and brown terrier, small and energetic

SAFEGUARDS:
- Cache checking (avoids re-generation)
- Budget limits
- User confirmation
"""

import sys
import os
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(PROJECT_ROOT))

from asset_generators.pixellab_client import PixelLabClient
from asset_generators.generation_safeguards import (
    GenerationCache, BudgetTracker, SafetyConfig, apply_mirror_optimization
)

# Try to import Genesis palette utilities
try:
    from pipeline.palettes.genesis_palettes import (
        get_genesis_palette, snap_to_genesis_color, create_palette_image,
        export_palette_c, TRANSPARENT
    )
    HAS_PALETTE_TOOLS = True
except ImportError:
    HAS_PALETTE_TOOLS = False
    print("Warning: Genesis palette tools not available")

# =============================================================================
# CONFIGURATION
# =============================================================================

OUTPUT_DIR = PROJECT_ROOT / "projects" / "epoch" / "res" / "sprites"
CACHE_DIR = ".pixellab_cache"

# 5 unique directions (mirror the other 3 at runtime)
UNIQUE_DIRECTIONS = ["south", "south-west", "west", "north-west", "north"]

# Character definitions using Art Bible descriptions
CHARACTERS = {
    "hero": {
        "description": (
            "pixel art teenage character, full body side view, "
            "90s grunge skater kid, messy shoulder-length brown hair, "
            "red backwards baseball cap, open red plaid flannel shirt, "
            "white t-shirt underneath, baggy blue denim jeans, wallet chain, "
            "sneakers, holding bright orange toy laser blaster in right hand, "
            "confident pose, detailed sprite like Zombies Ate My Neighbors, "
            "16-bit Sega Genesis style, proper shading and highlights, "
            "clean black pixel outline, transparent background"
        ),
        "size": (32, 48),  # Genesis-proper tall sprite (like ZAMN)
        "palette_name": "epoch_hero_dog",
    },
    "fenrir": {
        "description": (
            "pixel art small dog, scruffy terrier, black and brown fur, "
            "energetic pose, cute but tough looking, short ears, "
            "side view facing right, 16-bit sega genesis style, "
            "high contrast, clean black outline, no background"
        ),
        "size": (24, 24),  # Smaller than hero
        "palette_name": "epoch_hero_dog",  # Same palette as hero!
    },
}

# =============================================================================
# GENERATION FUNCTIONS
# =============================================================================

def generate_character(
    client: PixelLabClient,
    cache: GenerationCache,
    name: str,
    config: dict,
    dry_run: bool = False
) -> bool:
    """Generate 5-way sprite for a character."""
    desc = config["description"]
    width, height = config["size"]
    
    print(f"\n{'='*60}")
    print(f"Generating: {name.upper()}")
    print(f"Size: {width}x{height}")
    print(f"Description: {desc[:60]}...")
    print(f"{'='*60}")
    
    # Check cache
    if cache.has_cached_images(desc, width, height):
        print("[OK] Found in cache - loading without API call")
        images = cache.load_images(desc, width, height)
        if images:
            return _save_character_sprites(name, images, OUTPUT_DIR)
    
    if dry_run:
        print("[DRY RUN] Would generate here")
        return True
    
    # Generate via API
    print("Calling PixelLab API...")
    result = client.create_character_8_directions(
        description=desc,
        width=width,
        height=height,
        outline="medium",      # Clean pixel art outline
        shading="soft",        # Genesis-style shading
        detail="medium",       # Not too busy
        view="side",           # Side view for 8-way rotation
        max_poll_attempts=15,  # Reduced attempts
        poll_interval=10.0     # Increased to avoid rate limiting
    )
    
    if not result.success:
        print(f"[FAIL] {result.error}")
        return False
    
    print(f"[OK] Got {len(result.images)} directions")
    print(f"  Cost: ${result.cost_usd:.4f}")
    
    # Build images dict
    directions = result.metadata.get("directions", [])
    images = dict(zip(directions, result.images))
    
    # Cache immediately (before any processing that could fail)
    cache.save_images(desc, width, height, images)
    print(f"  Cached to {cache.get_cache_path(desc, width, height)}")
    
    return _save_character_sprites(name, images, OUTPUT_DIR)


def _save_character_sprites(name: str, images: dict, output_dir: Path) -> bool:
    """Save only the 5 unique directions."""
    output_dir.mkdir(parents=True, exist_ok=True)
    saved = 0
    
    for dir_name in UNIQUE_DIRECTIONS:
        if dir_name in images:
            # Normalize filename
            safe_name = dir_name.replace("-", "_")
            out_path = output_dir / f"{name}_{safe_name}.png"
            images[dir_name].save(out_path)
            print(f"  Saved: {out_path.name}")
            saved += 1
    
    print(f"  Total: {saved} unique sprites saved")
    print("  (Mirror NE, E, SE at runtime with SPR_setHFlip)")
    return saved > 0


# =============================================================================
# MAIN
# =============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate Hero and Dog sprites")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    parser.add_argument("--hero-only", action="store_true", help="Generate only hero")
    parser.add_argument("--dog-only", action="store_true", help="Generate only dog")
    parser.add_argument("--no-confirm", action="store_true", help="Skip confirmation")
    args = parser.parse_args()
    
    print("=" * 60)
    print("NEON SURVIVORS - Character Sprite Generation")
    print("=" * 60)
    print(f"Output: {OUTPUT_DIR}")
    print(f"Palette: player_warm (shared)")
    print()
    
    # Determine which characters to generate
    chars_to_gen = []
    if args.hero_only:
        chars_to_gen = ["hero"]
    elif args.dog_only:
        chars_to_gen = ["fenrir"]
    else:
        chars_to_gen = ["hero", "fenrir"]  # Both
    
    # Setup
    cache = GenerationCache(CACHE_DIR)
    budget = BudgetTracker(max_generations=5, max_cost=0.15)
    
    # Estimate cost
    cached_count = sum(
        1 for name in chars_to_gen 
        if cache.has_cached_images(CHARACTERS[name]["description"], 
                                   *CHARACTERS[name]["size"])
    )
    new_count = len(chars_to_gen) - cached_count
    est_cost = new_count * 0.015
    
    print(f"Characters: {', '.join(chars_to_gen)}")
    print(f"Cached: {cached_count}, Need generation: {new_count}")
    print(f"Estimated cost: ${est_cost:.4f}")
    print()
    
    # Confirmation
    if not args.no_confirm and not args.dry_run and new_count > 0:
        response = input("Proceed with generation? [y/N]: ").strip().lower()
        if response != 'y':
            print("Aborted.")
            return
    
    # Initialize client
    if not args.dry_run:
        print("\nInitializing PixelLab client...")
        client = PixelLabClient(max_calls=60)  # Account for polling
    else:
        client = None
    
    # Generate each character
    success_count = 0
    for name in chars_to_gen:
        if budget.can_generate() or cache.has_cached_images(
            CHARACTERS[name]["description"], *CHARACTERS[name]["size"]
        ):
            success = generate_character(
                client, cache, name, CHARACTERS[name], 
                dry_run=args.dry_run
            )
            if success:
                success_count += 1
                budget.record_generation(0.015)
        else:
            print(f"\n[WARN] Budget exhausted - skipping {name}")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"COMPLETE: {success_count}/{len(chars_to_gen)} characters generated")
    if client:
        print(f"Session cost: ${client.get_session_cost():.4f}")
    print("=" * 60)
    
    # Show palette info
    if HAS_PALETTE_TOOLS and success_count > 0:
        print("\nNote: Both sprites use 'player_warm' palette (PAL0)")
        print("Export with: export_palette_c(get_genesis_palette('player_warm'), 'pal_player')")


if __name__ == "__main__":
    main()
