#!/usr/bin/env python3
"""
Batch Sprite Processing Tool for NEON SURVIVORS

Processes all AI-generated PNG assets from gfx/ai_output/ and organizes
them into categorized directories with CHR files ready for NES.

Usage:
    python batch_process.py              # Process all assets
    python batch_process.py --no-ai      # Process without Gemini AI
    python batch_process.py --category player  # Process only player sprites
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# Add tools directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from sprite_pipeline import SpritePipeline

# Asset categories based on filename prefixes
ASSET_CATEGORIES = {
    'player': {
        'prefixes': ['player_'],
        'target_size': 32,
        'description': 'Player character sprites'
    },
    'enemies': {
        'prefixes': ['enemies_', 'enemy_'],
        'target_size': 32,
        'description': 'Enemy sprites'
    },
    'boss': {
        'prefixes': ['boss_'],
        'target_size': 64,  # Bosses may be larger
        'description': 'Boss sprites'
    },
    'items': {
        'prefixes': ['items_', 'item_'],
        'target_size': 16,
        'description': 'Items and projectiles'
    },
    'background': {
        'prefixes': ['background_', 'bg_'],
        'target_size': 128,  # Backgrounds are tile-based
        'description': 'Background tiles'
    },
    'ui': {
        'prefixes': ['ui_', 'hud_'],
        'target_size': 8,
        'description': 'UI elements and HUD'
    },
    'vfx': {
        'prefixes': ['vfx_', 'fx_', 'effect_'],
        'target_size': 16,
        'description': 'Visual effects'
    },
    'title': {
        'prefixes': ['title_', 'logo_'],
        'target_size': 64,
        'description': 'Title screen and logos'
    }
}


def categorize_asset(filename):
    """Determine the category of an asset based on its filename."""
    filename_lower = filename.lower()

    for category, config in ASSET_CATEGORIES.items():
        for prefix in config['prefixes']:
            if filename_lower.startswith(prefix):
                return category

    return 'misc'  # Default category for uncategorized assets


def get_target_size(category):
    """Get the target sprite size for a category."""
    if category in ASSET_CATEGORIES:
        return ASSET_CATEGORIES[category]['target_size']
    return 32  # Default size


def discover_assets(input_dir):
    """Discover all PNG assets in the input directory."""
    assets = []

    for filename in os.listdir(input_dir):
        if filename.lower().endswith('.png'):
            filepath = os.path.join(input_dir, filename)
            category = categorize_asset(filename)

            assets.append({
                'filename': filename,
                'filepath': filepath,
                'category': category,
                'target_size': get_target_size(category)
            })

    return assets


def process_batch(input_dir, output_base_dir, use_ai=True, category_filter=None):
    """
    Process all assets in batch mode.

    Args:
        input_dir: Directory containing AI-generated PNGs
        output_base_dir: Base output directory for processed assets
        use_ai: Whether to use Gemini AI for analysis
        category_filter: If set, only process this category

    Returns:
        Dictionary with processing results and manifest
    """
    print("=" * 70)
    print("  NEON SURVIVORS - Batch Sprite Processor")
    print("=" * 70)
    print(f"  Input:  {input_dir}")
    print(f"  Output: {output_base_dir}")
    print(f"  AI:     {'Enabled' if use_ai else 'Disabled'}")
    if category_filter:
        print(f"  Filter: {category_filter} only")
    print("=" * 70)

    # Discover assets
    assets = discover_assets(input_dir)
    print(f"\nDiscovered {len(assets)} PNG assets:")

    # Group by category
    by_category = {}
    for asset in assets:
        cat = asset['category']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(asset)

    for cat, cat_assets in sorted(by_category.items()):
        print(f"  [{cat}] {len(cat_assets)} files")
        for asset in cat_assets:
            print(f"    - {asset['filename']}")

    # Apply category filter if specified
    if category_filter:
        if category_filter not in by_category:
            print(f"\nError: Category '{category_filter}' not found")
            return None
        assets = by_category[category_filter]
        print(f"\nFiltering to {len(assets)} assets in '{category_filter}'")

    # Create output directories
    os.makedirs(output_base_dir, exist_ok=True)
    for category in by_category.keys():
        cat_dir = os.path.join(output_base_dir, category)
        os.makedirs(cat_dir, exist_ok=True)

    # Initialize pipeline
    pipeline = SpritePipeline(use_ai=use_ai)

    # Process each asset
    results = {
        'timestamp': datetime.now().isoformat(),
        'input_dir': input_dir,
        'output_dir': output_base_dir,
        'use_ai': use_ai,
        'assets': [],
        'summary': {
            'total': len(assets),
            'success': 0,
            'failed': 0,
            'by_category': {}
        }
    }

    for i, asset in enumerate(assets):
        print(f"\n{'='*70}")
        print(f"  [{i+1}/{len(assets)}] Processing: {asset['filename']}")
        print(f"  Category: {asset['category']}, Target size: {asset['target_size']}px")
        print(f"{'='*70}")

        # Output directory for this asset's category
        output_dir = os.path.join(output_base_dir, asset['category'],
                                  Path(asset['filename']).stem)

        try:
            # Process the asset
            metadata = pipeline.process(
                asset['filepath'],
                output_dir,
                target_size=asset['target_size']
            )

            # Record success
            asset_result = {
                'filename': asset['filename'],
                'category': asset['category'],
                'status': 'success',
                'output_dir': output_dir,
                'sprites_extracted': len(metadata.get('sprites', [])) if metadata else 0,
                'chr_files': []
            }

            # Find generated CHR files
            if os.path.exists(output_dir):
                for f in os.listdir(output_dir):
                    if f.endswith('.chr'):
                        chr_path = os.path.join(output_dir, f)
                        chr_size = os.path.getsize(chr_path)
                        asset_result['chr_files'].append({
                            'filename': f,
                            'path': chr_path,
                            'size': chr_size,
                            'tiles': chr_size // 16
                        })

            results['assets'].append(asset_result)
            results['summary']['success'] += 1

            cat = asset['category']
            if cat not in results['summary']['by_category']:
                results['summary']['by_category'][cat] = {'success': 0, 'failed': 0}
            results['summary']['by_category'][cat]['success'] += 1

            print(f"\n  [SUCCESS] Extracted {asset_result['sprites_extracted']} sprites")
            print(f"  [SUCCESS] Generated {len(asset_result['chr_files'])} CHR files")

        except Exception as e:
            # Record failure
            asset_result = {
                'filename': asset['filename'],
                'category': asset['category'],
                'status': 'failed',
                'error': str(e)
            }
            results['assets'].append(asset_result)
            results['summary']['failed'] += 1

            cat = asset['category']
            if cat not in results['summary']['by_category']:
                results['summary']['by_category'][cat] = {'success': 0, 'failed': 0}
            results['summary']['by_category'][cat]['failed'] += 1

            print(f"\n  [FAILED] {e}")
            import traceback
            traceback.print_exc()

    # Write manifest
    manifest_path = os.path.join(output_base_dir, 'manifest.json')
    with open(manifest_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nManifest written to: {manifest_path}")

    # Print summary
    print("\n" + "=" * 70)
    print("  BATCH PROCESSING COMPLETE")
    print("=" * 70)
    print(f"  Total:   {results['summary']['total']}")
    print(f"  Success: {results['summary']['success']}")
    print(f"  Failed:  {results['summary']['failed']}")
    print("\n  By Category:")
    for cat, stats in sorted(results['summary']['by_category'].items()):
        print(f"    [{cat}] {stats['success']} success, {stats['failed']} failed")

    # List all generated CHR files
    print("\n  Generated CHR Files:")
    total_tiles = 0
    for asset in results['assets']:
        if asset['status'] == 'success':
            for chr_file in asset.get('chr_files', []):
                print(f"    {chr_file['path']}")
                print(f"      Size: {chr_file['size']} bytes ({chr_file['tiles']} tiles)")
                total_tiles += chr_file['tiles']

    print(f"\n  Total tiles generated: {total_tiles}")
    print("=" * 70)

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Batch process AI-generated sprite sheets for NES',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Categories:
  player     - Player character sprites (32x32)
  enemies    - Enemy sprites (32x32)
  boss       - Boss sprites (64x64)
  items      - Items and projectiles (16x16)
  background - Background tiles (128x128)
  ui         - UI elements and HUD (8x8)
  vfx        - Visual effects (16x16)
  title      - Title screen and logos (64x64)

Examples:
  python batch_process.py                    # Process all assets
  python batch_process.py --no-ai            # Without AI analysis
  python batch_process.py --category player  # Only player sprites
  python batch_process.py -o custom_output   # Custom output directory
"""
    )

    parser.add_argument(
        '-i', '--input',
        default=None,
        help='Input directory (default: gfx/ai_output/)'
    )
    parser.add_argument(
        '-o', '--output',
        default=None,
        help='Output directory (default: gfx/processed/batch/)'
    )
    parser.add_argument(
        '--no-ai',
        action='store_true',
        help='Disable Gemini AI analysis'
    )
    parser.add_argument(
        '--category', '-c',
        choices=list(ASSET_CATEGORIES.keys()) + ['misc'],
        help='Process only specified category'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List assets without processing'
    )

    args = parser.parse_args()

    # Determine paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    input_dir = args.input or os.path.join(base_dir, 'gfx', 'ai_output')
    output_dir = args.output or os.path.join(base_dir, 'gfx', 'processed', 'batch')

    # Validate input directory
    if not os.path.exists(input_dir):
        print(f"Error: Input directory not found: {input_dir}")
        sys.exit(1)

    # List mode
    if args.list:
        assets = discover_assets(input_dir)
        by_category = {}
        for asset in assets:
            cat = asset['category']
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(asset)

        print(f"Assets in {input_dir}:\n")
        for cat, cat_assets in sorted(by_category.items()):
            desc = ASSET_CATEGORIES.get(cat, {}).get('description', 'Uncategorized')
            size = ASSET_CATEGORIES.get(cat, {}).get('target_size', 32)
            print(f"[{cat}] {desc} ({size}x{size})")
            for asset in cat_assets:
                print(f"  - {asset['filename']}")
            print()

        print(f"Total: {len(assets)} assets")
        return

    # Process batch
    try:
        results = process_batch(
            input_dir,
            output_dir,
            use_ai=not args.no_ai,
            category_filter=args.category
        )

        if results and results['summary']['failed'] > 0:
            sys.exit(1)  # Exit with error if any failed

    except KeyboardInterrupt:
        print("\n\nProcessing interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
