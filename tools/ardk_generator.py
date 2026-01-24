#!/usr/bin/env python3
"""
ARDK Asset Generator - Unified CLI for bespoke asset generation.

This tool wraps the asset_generators module to provide:
- Character sprite sheet generation with animations
- Scrolling background generation
- Multi-layer parallax generation
- Animated background tile generation
- Tile optimization and deduplication
- Integrated pipeline for batch processing

Uses Pollinations.ai with "best model for each task" policy.

Usage:
    # Generate character sprites
    python ardk_generator.py character "cyberpunk ninja" -o output/ninja/ --platform nes

    # Generate scrolling background
    python ardk_generator.py background "neon city street at night" -o output/city/ --width 4

    # Generate parallax set
    python ardk_generator.py parallax "synthwave cityscape" -o output/parallax/ --preset city_4layer

    # Generate animated tiles
    python ardk_generator.py animated-tile "flowing water" -o output/water/ --preset water

    # Process batch from JSON definition
    python ardk_generator.py batch assets.json -o output/ --platform nes

    # Analyze existing image for tile optimization
    python ardk_generator.py analyze input.png --platform nes
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from asset_generators import (
    CharacterGenerator,
    BackgroundGenerator,
    ParallaxGenerator,
    AnimatedTileGenerator,
    IntegratedPipeline,
    PipelineConfig,
    get_nes_config,
    get_genesis_config,
    get_snes_config,
    GenerationFlags,
    LAYER_PRESETS,
    TILE_ANIMATION_PRESETS,
)
from tile_optimizers import TileDeduplicator, SymmetryDetector


# =============================================================================
# Platform Configuration
# =============================================================================

PLATFORM_CONFIGS = {
    'nes': get_nes_config,
    'genesis': get_genesis_config,
    'snes': get_snes_config,
}


# =============================================================================
# Character Generation Command
# =============================================================================

def cmd_character(args):
    """Generate character sprite sheet with animations."""
    platform = PLATFORM_CONFIGS[args.platform]()

    print(f"ARDK Character Generator")
    print(f"========================")
    print(f"Description: {args.description}")
    print(f"Platform: {platform.name}")
    print(f"Animation set: {args.animation_set}")
    print(f"Sprite size: {args.size}x{args.size}")
    print()

    generator = CharacterGenerator(platform=platform)

    # Set generation flags
    flags = GenerationFlags(
        animation_set=args.animation_set,
        use_h_flip=not args.no_flip,
        use_v_flip=not args.no_flip,
        detect_symmetry=not args.no_symmetry,
        deduplicate_tiles=not args.no_dedup,
    )
    generator.set_flags(flags)

    print("Generating character sheet...")
    sheet = generator.generate(
        description=args.description,
        animation_set=args.animation_set,
        sprite_width=args.size,
        sprite_height=args.size,
    )

    print(f"\nGenerated {len(sheet.animations)} animations:")
    for anim in sheet.animations:
        print(f"  {anim.name}: {anim.frame_count} frames")

    print(f"\nSaving to {args.output}...")
    files = generator.save_character(sheet, args.output)

    print(f"\nCreated files:")
    for name, path in files.items():
        print(f"  {name}: {path}")

    if sheet.warnings:
        print(f"\nWarnings:")
        for w in sheet.warnings:
            print(f"  - {w}")

    print("\nDone!")


# =============================================================================
# Background Generation Command
# =============================================================================

def cmd_background(args):
    """Generate scrolling background."""
    platform = PLATFORM_CONFIGS[args.platform]()

    print(f"ARDK Background Generator")
    print(f"=========================")
    print(f"Description: {args.description}")
    print(f"Platform: {platform.name}")
    print(f"Width: {args.width} screens ({args.width * platform.screen_width}px)")
    print(f"Seamless: {not args.no_seamless}")
    print()

    generator = BackgroundGenerator(platform=platform)

    # Set generation flags
    flags = GenerationFlags(
        seamless_loop=not args.no_seamless,
        use_h_flip=not args.no_flip,
        use_v_flip=not args.no_flip,
        deduplicate_tiles=not args.no_dedup,
        generate_collision=args.collision,
    )
    generator.set_flags(flags)

    print("Generating background...")
    if args.collision:
        bg = generator.generate_with_collision(
            args.description,
            width_screens=args.width,
            seamless=not args.no_seamless,
        )
    else:
        bg = generator.generate_scrolling_bg(
            args.description,
            width_screens=args.width,
            seamless=not args.no_seamless,
        )

    print(f"\nGeneration complete!")
    print(f"Dimensions: {bg.width_pixels}x{bg.height_pixels}")
    print(f"Unique tiles: {bg.tile_count}")
    print(f"Savings: {bg.savings_percent:.1f}%")

    print(f"\nSaving to {args.output}...")
    files = generator.save_background(bg, args.output)

    print(f"\nCreated files:")
    for name, path in files.items():
        print(f"  {name}: {path}")

    if bg.warnings:
        print(f"\nWarnings:")
        for w in bg.warnings:
            print(f"  - {w}")

    print("\nDone!")


# =============================================================================
# Parallax Generation Command
# =============================================================================

def cmd_parallax(args):
    """Generate multi-layer parallax background."""
    platform = PLATFORM_CONFIGS[args.platform]()

    print(f"ARDK Parallax Generator")
    print(f"=======================")
    print(f"Description: {args.description}")
    print(f"Platform: {platform.name}")
    print(f"Preset: {args.preset}")
    print(f"Width: {args.width} screens")
    print()

    # Show preset info
    preset_layers = LAYER_PRESETS.get(args.preset, [])
    print(f"Preset layers ({len(preset_layers)}):")
    for layer in preset_layers:
        print(f"  - {layer['name']}: speed={layer['speed']}, height={int(layer['height_pct']*100)}%")
    print()

    generator = ParallaxGenerator(platform=platform)

    print("Generating parallax layers...")
    parallax = generator.generate_parallax_set(
        description=args.description,
        preset=args.preset,
        width_screens=args.width,
    )

    print(f"\nGeneration complete!")
    print(f"Total layers: {parallax.layer_count}")
    print(f"Total CHR size: {parallax.total_chr_size} bytes")

    print("\nLayer summary:")
    for layer in parallax.layers:
        print(f"  {layer.index}. {layer.name}: {layer.tile_count} tiles, "
              f"speed={layer.scroll_speed}, scanlines={layer.y_start}-{layer.y_end}")

    print(f"\nSaving to {args.output}...")
    files = generator.save_parallax_set(parallax, args.output)

    print(f"\nCreated files:")
    for name, path in files.items():
        print(f"  {name}: {path}")

    if parallax.warnings:
        print(f"\nWarnings:")
        for w in parallax.warnings:
            print(f"  - {w}")

    print("\nDone!")


# =============================================================================
# Analyze Command
# =============================================================================

def cmd_analyze(args):
    """Analyze existing image for optimization opportunities."""
    from PIL import Image

    platform = PLATFORM_CONFIGS[args.platform]()

    print(f"ARDK Asset Analyzer")
    print(f"===================")
    print(f"Input: {args.input}")
    print(f"Platform: {platform.name}")
    print()

    # Load image
    image = Image.open(args.input)
    print(f"Image size: {image.width}x{image.height}")
    print(f"Mode: {image.mode}")
    print()

    # Tile deduplication analysis
    print("Tile Deduplication Analysis:")
    print("-" * 40)
    deduplicator = TileDeduplicator(
        tile_width=platform.tile_width,
        tile_height=platform.tile_height,
        enable_h_flip=platform.enable_flip_optimization,
        enable_v_flip=platform.enable_flip_optimization,
    )

    optimized = deduplicator.optimize(image)
    print(f"Total tiles: {optimized.total_tiles}")
    print(f"Unique tiles: {optimized.unique_count}")
    print(f"Savings: {optimized.savings_percent:.1f}%")
    print(f"H-flip matches: {optimized.h_flip_count}")
    print(f"V-flip matches: {optimized.v_flip_count}")
    print()

    # Symmetry analysis
    print("Symmetry Analysis:")
    print("-" * 40)
    detector = SymmetryDetector(
        tile_width=platform.tile_width,
        tile_height=platform.tile_height,
    )

    report = detector.analyze_image(image)
    print(f"H-symmetric tiles: {report.h_symmetric_count} ({report.h_symmetric_percent:.1f}%)")
    print(f"V-symmetric tiles: {report.v_symmetric_count} ({report.v_symmetric_percent:.1f}%)")
    print(f"Fully symmetric: {report.full_symmetric_count}")
    print()

    hints = report.get_optimization_hints()
    if hints:
        print("Optimization hints:")
        for hint in hints:
            print(f"  - {hint}")
    else:
        print("No significant symmetry patterns detected.")

    # Platform compliance
    print()
    print("Platform Compliance:")
    print("-" * 40)
    max_tiles = platform.max_tiles_per_bank
    if optimized.unique_count <= max_tiles:
        print(f"[OK] Tile count ({optimized.unique_count}) within limit ({max_tiles})")
    else:
        over = optimized.unique_count - max_tiles
        print(f"[WARNING] Tile count exceeds limit by {over} tiles")
        print(f"  Need to reduce from {optimized.unique_count} to {max_tiles}")

    print("\nDone!")


# =============================================================================
# Animated Tile Command
# =============================================================================

def cmd_animated_tile(args):
    """Generate animated background tile."""
    platform = PLATFORM_CONFIGS[args.platform]()

    print(f"ARDK Animated Tile Generator")
    print(f"============================")
    print(f"Description: {args.description}")
    print(f"Platform: {platform.name}")
    print(f"Preset: {args.preset}")
    print()

    generator = AnimatedTileGenerator(platform=platform)

    preset_info = TILE_ANIMATION_PRESETS.get(args.preset, {})
    print(f"Animation: {preset_info.get('description', 'Custom')}")
    print(f"Frames: {args.frames or preset_info.get('frames', 4)}")
    print(f"Speed: {args.speed or preset_info.get('speed_ms', 100)}ms")
    print()

    print("Generating animated tile...")
    tile = generator.generate_animated_tile(
        args.description,
        preset=args.preset,
        frame_count=args.frames,
        speed_ms=args.speed,
    )

    print(f"\nGenerated {tile.frame_count} frames @ {tile.speed_ms}ms")

    print(f"\nSaving to {args.output}...")
    files = generator.save_animated_tile(tile, args.output)

    print(f"\nCreated files:")
    for name, path in files.items():
        print(f"  {name}: {path}")

    print("\nDone!")


# =============================================================================
# Batch Command
# =============================================================================

def cmd_batch(args):
    """Process batch of assets from JSON definition."""
    platform = args.platform

    print(f"ARDK Batch Processor")
    print(f"====================")
    print(f"Input: {args.input}")
    print(f"Platform: {platform}")
    print()

    # Load asset definitions
    with open(args.input, 'r') as f:
        asset_list = json.load(f)

    print(f"Loaded {len(asset_list)} asset definitions")
    print()

    # Configure pipeline
    config = PipelineConfig(platform=platform)
    pipeline = IntegratedPipeline(config)
    pipeline.manifest.project_name = args.project_name or Path(args.input).stem

    # Process all assets
    results = pipeline.process_asset_list(asset_list, args.output)

    # Summary
    print(f"\n{'='*60}")
    print("Summary")
    print(f"{'='*60}")

    success_count = sum(1 for r in results if r.success)
    print(f"Processed: {len(results)}")
    print(f"Success: {success_count}")
    print(f"Failed: {len(results) - success_count}")

    # Save manifest
    manifest_path = str(Path(args.output) / "manifest.json")
    pipeline.save_manifest(manifest_path)
    print(f"\nManifest saved to: {manifest_path}")

    # Resource analysis
    analysis = pipeline.analyze_project_resources()
    print(f"\nResource Usage:")
    print(f"  Tiles: {analysis['usage']['unique_tiles']} / {analysis['limits']['max_tiles']} "
          f"({analysis['usage']['tile_usage_percent']:.1f}%)")
    print(f"  CHR: {analysis['usage']['chr_bytes']} / {analysis['limits']['max_chr_bytes']} bytes "
          f"({analysis['usage']['chr_usage_percent']:.1f}%)")

    if analysis['warnings']:
        print("\nWarnings:")
        for w in analysis['warnings']:
            print(f"  - {w}")

    print("\nDone!")


# =============================================================================
# List Presets Command
# =============================================================================

def cmd_list_presets(args):
    """List available presets."""
    if args.type == 'parallax' or args.type == 'all':
        print("Available Parallax Presets")
        print("=" * 50)
        print()

        for name, layers in LAYER_PRESETS.items():
            print(f"{name}:")
            for layer in layers:
                desc = layer.get('description', '')
                print(f"  - {layer['name']:<20} speed={layer['speed']:<5} height={int(layer['height_pct']*100):>3}%")
                if desc:
                    print(f"    {desc}")
            print()

    if args.type == 'animation' or args.type == 'all':
        print("Available Tile Animation Presets")
        print("=" * 50)
        print()

        for name, config in TILE_ANIMATION_PRESETS.items():
            print(f"{name}:")
            print(f"  Frames: {config['frames']}, Speed: {config['speed_ms']}ms")
            print(f"  {config['description']}")
            print()


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='ARDK Asset Generator - Bespoke sprite and background generation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Generate character with standard animations (NES)
    python ardk_generator.py character "space marine" -o output/marine/

    # Generate character with full animations (Genesis)
    python ardk_generator.py character "ninja warrior" -o output/ninja/ \\
        --platform genesis --animation-set full --size 32

    # Generate scrolling background
    python ardk_generator.py background "forest at sunset" -o output/forest/ \\
        --width 4 --collision

    # Generate parallax cityscape
    python ardk_generator.py parallax "cyberpunk city" -o output/city/ \\
        --preset city_4layer --platform snes

    # Generate animated water tile
    python ardk_generator.py animated-tile "flowing river water" -o output/water/ \\
        --preset water --frames 4

    # Process batch from JSON file
    python ardk_generator.py batch assets.json -o output/ --platform nes

    # Analyze existing sprite sheet
    python ardk_generator.py analyze sprites.png --platform nes

    # List available presets
    python ardk_generator.py list-presets --type all
"""
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Character command
    char_parser = subparsers.add_parser('character', help='Generate character sprite sheet')
    char_parser.add_argument('description', help='Character description')
    char_parser.add_argument('-o', '--output', required=True, help='Output directory')
    char_parser.add_argument('--platform', choices=['nes', 'genesis', 'snes'],
                            default='nes', help='Target platform')
    char_parser.add_argument('--animation-set', choices=['minimal', 'standard', 'full'],
                            default='standard', help='Animation set')
    char_parser.add_argument('--size', type=int, default=32, help='Sprite size (default: 32)')
    char_parser.add_argument('--no-flip', action='store_true', help='Disable flip optimization')
    char_parser.add_argument('--no-symmetry', action='store_true', help='Disable symmetry detection')
    char_parser.add_argument('--no-dedup', action='store_true', help='Disable tile deduplication')
    char_parser.set_defaults(func=cmd_character)

    # Background command
    bg_parser = subparsers.add_parser('background', help='Generate scrolling background')
    bg_parser.add_argument('description', help='Background description')
    bg_parser.add_argument('-o', '--output', required=True, help='Output directory')
    bg_parser.add_argument('--platform', choices=['nes', 'genesis', 'snes'],
                          default='nes', help='Target platform')
    bg_parser.add_argument('--width', type=int, default=2, help='Width in screens (default: 2)')
    bg_parser.add_argument('--no-seamless', action='store_true', help='Disable seamless looping')
    bg_parser.add_argument('--collision', action='store_true', help='Generate collision map')
    bg_parser.add_argument('--no-flip', action='store_true', help='Disable flip optimization')
    bg_parser.add_argument('--no-dedup', action='store_true', help='Disable tile deduplication')
    bg_parser.set_defaults(func=cmd_background)

    # Parallax command
    parallax_parser = subparsers.add_parser('parallax', help='Generate parallax layers')
    parallax_parser.add_argument('description', help='Scene description')
    parallax_parser.add_argument('-o', '--output', required=True, help='Output directory')
    parallax_parser.add_argument('--platform', choices=['nes', 'genesis', 'snes'],
                                default='nes', help='Target platform')
    parallax_parser.add_argument('--preset', choices=list(LAYER_PRESETS.keys()),
                                default='standard_3layer', help='Layer preset')
    parallax_parser.add_argument('--width', type=int, default=2, help='Base width in screens')
    parallax_parser.set_defaults(func=cmd_parallax)

    # Animated tile command
    anim_parser = subparsers.add_parser('animated-tile', help='Generate animated background tile')
    anim_parser.add_argument('description', help='Tile description')
    anim_parser.add_argument('-o', '--output', required=True, help='Output directory')
    anim_parser.add_argument('--platform', choices=['nes', 'genesis', 'snes'],
                            default='nes', help='Target platform')
    anim_parser.add_argument('--preset', choices=list(TILE_ANIMATION_PRESETS.keys()),
                            default='water', help='Animation preset')
    anim_parser.add_argument('--frames', type=int, help='Override frame count')
    anim_parser.add_argument('--speed', type=int, help='Override speed (ms per frame)')
    anim_parser.set_defaults(func=cmd_animated_tile)

    # Batch command
    batch_parser = subparsers.add_parser('batch', help='Process batch from JSON file')
    batch_parser.add_argument('input', help='JSON file with asset definitions')
    batch_parser.add_argument('-o', '--output', required=True, help='Output directory')
    batch_parser.add_argument('--platform', choices=['nes', 'genesis', 'snes'],
                             default='nes', help='Target platform')
    batch_parser.add_argument('--project-name', help='Project name for manifest')
    batch_parser.set_defaults(func=cmd_batch)

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze image for optimization')
    analyze_parser.add_argument('input', help='Input image file')
    analyze_parser.add_argument('--platform', choices=['nes', 'genesis', 'snes'],
                               default='nes', help='Target platform')
    analyze_parser.set_defaults(func=cmd_analyze)

    # List presets command
    presets_parser = subparsers.add_parser('list-presets', help='List available presets')
    presets_parser.add_argument('--type', choices=['parallax', 'animation', 'all'],
                               default='all', help='Preset type to list')
    presets_parser.set_defaults(func=cmd_list_presets)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    # Run the selected command
    args.func(args)


if __name__ == '__main__':
    main()
