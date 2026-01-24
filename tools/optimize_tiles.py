#!/usr/bin/env python3
"""
Tile Optimizer CLI.

Optimize sprite sheets by deduplicating tiles and detecting flips.
Reduces VRAM usage and improves performance on retro platforms.

Usage:
    python optimize_tiles.py input.png --output output_dir/
    python optimize_tiles.py assets/sprites/*.png --batch
    python optimize_tiles.py input.png --platform genesis --stats
    python optimize_tiles.py input.png --json report.json
"""

import sys
import time
from pathlib import Path

# Add pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.optimization import (
    TileOptimizer,
    BatchTileOptimizer,
)
from pipeline.cli_utils import (
    create_parser,
    add_common_args,
    setup_from_args,
    print_config_status,
    VerbosePrinter,
    CLIReporter,
)


def optimize_single(args, config, verbosity):
    """Optimize a single sprite sheet."""
    vprint = VerbosePrinter(verbosity)
    input_path = Path(args.input)

    if not input_path.exists():
        vprint.error(f"Input file not found: {input_path}")
        return 1

    vprint.header(f"Optimizing {input_path.name}")

    # Create optimizer using platform from config
    platform = args.platform or config.platform
    optimizer = TileOptimizer(
        tile_width=args.tile_width,
        tile_height=args.tile_height,
        allow_mirror_x=not args.no_flip_h,
        allow_mirror_y=not args.no_flip_v,
        platform=platform,
    )

    # Optimize
    start = time.time()
    result = optimizer.optimize_sprite_sheet(str(input_path))
    duration_ms = (time.time() - start) * 1000

    # Print statistics
    if args.stats or verbosity >= 2:
        print(result.stats)
        print()

    # Check VRAM budget
    if args.check_vram:
        fits, used, available = optimizer.check_vram_budget(result.unique_tile_count)
        print(f"VRAM Budget Check ({platform}):")
        print(f"  Used: {used} bytes ({used/1024:.2f} KB)")
        print(f"  Available: {available} bytes ({available/1024:.2f} KB)")
        if fits:
            vprint.success("Tiles fit within VRAM budget")
        else:
            vprint.warn(f"Exceeds VRAM budget by {used - available} bytes")
        print()

    # Save outputs
    output_dir = args.output or (config.paths.output if hasattr(config.paths, 'output') else None)
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save unique tiles
        if args.save_tiles:
            tiles_dir = output_path / "tiles"
            result.save_tiles(str(tiles_dir), prefix=input_path.stem)
            vprint.verbose(f"Saved {result.unique_tile_count} unique tiles to {tiles_dir}")

        # Save tile map
        if args.save_map:
            map_path = output_path / f"{input_path.stem}_tilemap.json"
            result.save_tile_map(str(map_path))
            vprint.verbose(f"Saved tile map to {map_path}")

        # Save reconstructed image (for verification)
        if args.verify:
            reconstructed = result.reconstruct_image()
            verify_path = output_path / f"{input_path.stem}_reconstructed.png"
            reconstructed.save(verify_path)
            vprint.verbose(f"Saved reconstructed image to {verify_path}")

    # JSON output
    if args.json:
        import json
        report = {
            "tool": "optimize_tiles",
            "input": str(input_path),
            "platform": platform,
            "duration_ms": round(duration_ms, 1),
            "results": {
                "original_tiles": result.stats.original_tile_count,
                "unique_tiles": result.unique_tile_count,
                "duplicates_removed": result.stats.original_tile_count - result.unique_tile_count,
                "savings_bytes": result.stats.savings_bytes,
                "savings_percent": round(result.stats.savings_percent, 2),
                "h_flip_matches": result.stats.h_flip_matches,
                "v_flip_matches": result.stats.v_flip_matches,
                "hv_flip_matches": result.stats.hv_flip_matches,
            }
        }
        if args.json == '-':
            print(json.dumps(report, indent=2))
        else:
            with open(args.json, 'w') as f:
                json.dump(report, f, indent=2)
            vprint.info(f"JSON report saved to: {args.json}")
        return 0

    # Summary
    print()
    vprint.header("Optimization Complete", char="-", width=40)
    print(f"  Original Tiles: {result.stats.original_tile_count}")
    print(f"  Unique Tiles:   {result.unique_tile_count}")
    print(f"  Savings:        {result.stats.savings_bytes} bytes ({result.stats.savings_percent:.1f}%)")

    if result.stats.h_flip_matches > 0:
        print(f"  H-Flip Matches: {result.stats.h_flip_matches}")
    if result.stats.v_flip_matches > 0:
        print(f"  V-Flip Matches: {result.stats.v_flip_matches}")
    if result.stats.hv_flip_matches > 0:
        print(f"  HV-Flip Matches: {result.stats.hv_flip_matches}")

    print(f"  Time:           {duration_ms:.1f}ms")

    return 0


def optimize_batch(args, config, verbosity):
    """Optimize multiple sprite sheets with progress tracking."""
    vprint = VerbosePrinter(verbosity)
    input_patterns = args.input if isinstance(args.input, list) else [args.input]

    # Collect all input files
    input_files = []
    for pattern in input_patterns:
        path = Path(pattern)
        if path.is_file():
            input_files.append(path)
        elif path.is_dir():
            input_files.extend(path.glob("*.png"))
        else:
            # Glob pattern
            input_files.extend(Path(".").glob(pattern))

    if not input_files:
        vprint.error("No input files found")
        return 1

    vprint.header(f"Batch Optimizing {len(input_files)} Files")

    # Create reporter for progress and summary
    reporter = CLIReporter(
        args=args,
        verbosity=verbosity,
        total_items=len(input_files),
        title="Tile Optimization",
        tool_name="optimize_tiles",
    )

    # Create batch optimizer
    platform = args.platform or config.platform
    batch = BatchTileOptimizer(
        tile_width=args.tile_width,
        tile_height=args.tile_height,
        allow_mirror_x=not args.no_flip_h,
        allow_mirror_y=not args.no_flip_v,
        platform=platform,
    )

    # Track totals
    total_original = 0
    total_unique = 0
    total_savings = 0

    # Optimize all files
    for input_file in input_files:
        reporter.set_description(f"Processing {input_file.name}")
        start = time.time()

        try:
            result = batch.optimizer.optimize_sprite_sheet(str(input_file))
            duration_ms = (time.time() - start) * 1000

            # Track totals
            total_original += result.stats.original_tile_count
            total_unique += result.unique_tile_count
            total_savings += result.stats.savings_bytes

            # Record result
            reporter.success(
                str(input_file),
                data={
                    "unique_tiles": result.unique_tile_count,
                    "savings_percent": round(result.stats.savings_percent, 1),
                },
                duration_ms=duration_ms,
            )

            # Verbose output
            vprint.verbose(f"{input_file.name}: {result.unique_tile_count} tiles ({result.stats.savings_percent:.1f}% savings)")

            # Save outputs if requested
            output_dir = args.output or (config.paths.output if hasattr(config.paths, 'output') else None)
            if output_dir:
                output_path = Path(output_dir) / input_file.stem
                output_path.mkdir(parents=True, exist_ok=True)

                if args.save_tiles:
                    result.save_tiles(str(output_path), prefix=input_file.stem)

                if args.save_map:
                    map_path = output_path / f"{input_file.stem}_tilemap.json"
                    result.save_tile_map(str(map_path))

        except Exception as e:
            reporter.error(str(input_file), str(e))
            vprint.verbose(f"{input_file.name}: Error - {e}")

        reporter.advance()

    # Add summary statistics
    reporter.add_stat("total_original_tiles", total_original)
    reporter.add_stat("total_unique_tiles", total_unique)
    reporter.add_stat("total_duplicates_removed", total_original - total_unique)
    reporter.add_stat("total_savings_bytes", total_savings)
    reporter.add_stat("total_savings_kb", round(total_savings / 1024, 1))

    # Finish and get exit code
    return reporter.finish()


def main():
    epilog = """
Examples:
  # Optimize single sprite sheet
  python optimize_tiles.py sprite.png --output optimized/

  # Batch optimize with progress bar
  python optimize_tiles.py assets/sprites/*.png --batch --output out/

  # Generate JSON report for CI/CD
  python optimize_tiles.py assets/*.png --batch --json report.json

  # Optimize for specific platform
  python optimize_tiles.py sprite.png --platform nes --check-vram

  # Show detailed summary
  python optimize_tiles.py assets/*.png --batch --summary
    """

    parser = create_parser(
        "Optimize sprite sheets by deduplicating tiles",
        epilog=epilog
    )

    # Add common args (config, platform, output, dry-run, verbose, quiet, json, summary, progress)
    add_common_args(parser)

    # Input
    parser.add_argument('input', nargs='+',
                       help='Input sprite sheet(s) or pattern')

    # Tile settings
    tile_group = parser.add_argument_group('tile settings')
    tile_group.add_argument('--tile-width', type=int, default=8,
                       help='Tile width in pixels (default: 8)')
    tile_group.add_argument('--tile-height', type=int, default=8,
                       help='Tile height in pixels (default: 8)')

    # Flip detection
    flip_group = parser.add_argument_group('flip detection')
    flip_group.add_argument('--no-flip-h', action='store_true',
                       help='Disable horizontal flip detection')
    flip_group.add_argument('--no-flip-v', action='store_true',
                       help='Disable vertical flip detection')

    # Platform
    platform_group = parser.add_argument_group('platform')
    platform_group.add_argument('--check-vram', action='store_true',
                       help='Check if tiles fit within platform VRAM budget')

    # Output options
    save_group = parser.add_argument_group('save options')
    save_group.add_argument('--save-tiles', action='store_true',
                       help='Save individual unique tiles as PNG files')
    save_group.add_argument('--save-map', action='store_true',
                       help='Save tile map as JSON')
    save_group.add_argument('--verify', action='store_true',
                       help='Save reconstructed image for verification')

    # Processing mode
    parser.add_argument('--batch', action='store_true',
                       help='Batch process multiple files')

    # Output control
    parser.add_argument('--stats', action='store_true',
                       help='Show detailed statistics')

    args = parser.parse_args()

    # Load config
    config, verbosity = setup_from_args(args)

    # Show config status in verbose mode
    if verbosity >= 2:
        print_config_status(config, verbosity)

    # Default to saving everything if output directory specified
    if args.output and not (args.save_tiles or args.save_map):
        args.save_tiles = True
        args.save_map = True

    # Process
    try:
        if args.batch or len(args.input) > 1:
            return optimize_batch(args, config, verbosity)
        else:
            args.input = args.input[0]
            return optimize_single(args, config, verbosity)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if verbosity >= 2:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
