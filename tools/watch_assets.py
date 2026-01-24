#!/usr/bin/env python3
"""
Asset Watch Mode CLI.

Monitors asset directories for changes and automatically processes them through
the pipeline. Supports debouncing and optional hot reload to emulator.

Usage:
    python watch_assets.py assets/sprites --processor sprite
    python watch_assets.py assets/sprites assets/tilesets --debounce 2.0
    python watch_assets.py assets/ --hot-reload --reload-cmd "make reload"
    python watch_assets.py assets/ --extensions .png .aseprite --recursive
"""

import sys
import signal
from pathlib import Path

# Add pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.watch import AssetWatcher, WatchConfig, SafetyConfig, PipelineWatcher, FileChangeEvent
from pipeline.cli_utils import (
    create_parser,
    add_common_args,
    add_watch_args,
    setup_from_args,
    print_config_status,
    VerbosePrinter,
)


# =============================================================================
# Processors
# =============================================================================

def process_sprite(path: Path):
    """Process sprite through pipeline."""
    from pipeline.processing import SpriteConverter
    from pipeline.platforms import GenesisConfig
    from PIL import Image

    print(f"  Converting sprite: {path.name}")

    img = Image.open(path)
    converter = SpriteConverter(platform=GenesisConfig)

    # Scale and convert
    scaled = converter.scale_sprite(img, target_size=32)
    indexed = converter.index_sprite(scaled)

    # Save output
    output_dir = Path("output") / "sprites"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / path.name
    indexed.save(output_path)

    print(f"  → Saved to {output_path}")


def process_tileset(path: Path):
    """Process tileset through pipeline."""
    from pipeline.optimization import TileOptimizer
    from PIL import Image

    print(f"  Optimizing tileset: {path.name}")

    img = Image.open(path)
    optimizer = TileOptimizer(platform='genesis')
    result = optimizer.optimize_image(img)

    print(f"  → {result.unique_tile_count} unique tiles "
          f"({result.stats.savings_percent:.1f}% savings)")

    # Save optimized tiles
    output_dir = Path("output") / "tilesets" / path.stem
    output_dir.mkdir(parents=True, exist_ok=True)
    result.save_tiles(str(output_dir), prefix=path.stem)
    result.save_tile_map(str(output_dir / f"{path.stem}_tilemap.json"))

    print(f"  → Saved to {output_dir}")


def process_generic(path: Path):
    """Generic processor - just report changes."""
    print(f"  Changed: {path.name}")


# =============================================================================
# Main
# =============================================================================

def main():
    epilog = """
Examples:
  # Watch sprites directory
  python watch_assets.py assets/sprites --processor sprite

  # Watch multiple directories
  python watch_assets.py assets/sprites assets/tilesets

  # Enable hot reload
  python watch_assets.py assets/ --hot-reload --reload-cmd "make reload"

  # Watch specific extensions
  python watch_assets.py assets/ --extensions .png .aseprite

  # Custom safety limits
  python watch_assets.py assets/ --max-file-size 10 --max-rate 30 --timeout 15

  # Disable safety (development only)
  python watch_assets.py assets/ --no-safety

Processors:
  sprite  - Process sprites (scale, convert, export)
  tileset - Optimize tilesets (deduplicate tiles)
  generic - Just report changes (no processing)
"""

    parser = create_parser(
        "Watch asset directories and auto-process changes",
        epilog=epilog
    )

    # Add common args (config, platform, output, dry-run, verbose, quiet)
    add_common_args(parser)

    # Add watch-specific args (debounce, max-rate, max-file-size, timeout)
    add_watch_args(parser)

    # Watch directories (positional)
    parser.add_argument('directories', nargs='+',
                       help='Directories to watch for changes')

    # Watch options
    watch_group = parser.add_argument_group('watch options')
    watch_group.add_argument('--extensions', nargs='+',
                       default=['.png', '.aseprite', '.bmp'],
                       help='File extensions to monitor (default: .png .aseprite .bmp)')
    watch_group.add_argument('--no-recursive', action='store_true',
                       help='Do not watch subdirectories')
    watch_group.add_argument('--ignore', nargs='+',
                       default=['*.tmp', '.*', '*~'],
                       help='Patterns to ignore (default: *.tmp .* *~)')

    # Processing
    parser.add_argument('--processor', choices=['sprite', 'tileset', 'generic'],
                       default='generic',
                       help='Processing function to use (default: generic)')

    # Hot reload
    parser.add_argument('--hot-reload', action='store_true',
                       help='Enable hot reload after processing')
    parser.add_argument('--reload-cmd',
                       help='Command to run for hot reload (e.g., "make reload")')

    # Safety options (additional)
    safety_group = parser.add_argument_group('safety (additional)')
    safety_group.add_argument('--no-safety', action='store_true',
                              help='Disable safety limits (development only)')
    safety_group.add_argument('--max-queue', type=int, default=100,
                              help='Max pending files in queue (default: 100)')
    safety_group.add_argument('--circuit-breaker', type=int, default=5,
                              help='Pause after N consecutive errors (default: 5)')
    safety_group.add_argument('--cooldown', type=float, default=60.0,
                              help='Circuit breaker cooldown in seconds (default: 60)')

    args = parser.parse_args()

    # Load config and apply CLI overrides
    config, verbosity = setup_from_args(args)
    vprint = VerbosePrinter(verbosity)

    # Show config status
    print_config_status(config, verbosity)

    # Validate directories
    for directory in args.directories:
        if not Path(directory).exists():
            vprint.error(f"Directory does not exist: {directory}")
            return 1

    # Select processor
    processor_map = {
        'sprite': process_sprite,
        'tileset': process_tileset,
        'generic': process_generic,
    }
    processor_func = processor_map[args.processor]

    # Create safety config from pipeline config + CLI overrides
    if args.no_safety:
        safety = None
    else:
        # Get values from config.watch, with CLI args taking precedence
        safety = SafetyConfig(
            max_file_size_mb=args.max_file_size if args.max_file_size else config.watch.max_file_size_mb,
            max_changes_per_minute=args.max_rate if args.max_rate else config.watch.max_rate,
            max_queue_depth=args.max_queue,
            max_processing_time_seconds=args.timeout if args.timeout else config.watch.timeout,
            circuit_breaker_errors=args.circuit_breaker,
            circuit_breaker_cooldown=args.cooldown,
        )

    # Get debounce from CLI or config
    debounce = args.debounce if args.debounce else config.watch.debounce

    # Create watch config
    watch_config = WatchConfig(
        watch_dirs=args.directories,
        extensions=args.extensions,
        debounce_seconds=debounce,
        recursive=not args.no_recursive,
        ignore_patterns=args.ignore,
        hot_reload_enabled=args.hot_reload,
        hot_reload_command=args.reload_cmd,
        safety=safety,
    )

    # Create watcher
    if args.processor == 'generic':
        # Use basic watcher
        watcher = AssetWatcher(watch_config)

        def on_change(event: FileChangeEvent):
            vprint.header(f"{event.change_type.value.upper()}: {event.path.name}")
            vprint.verbose(f"Time: {event.timestamp}")
            if event.hash:
                vprint.verbose(f"Hash: {event.hash[:16]}...")

        watcher.on_change = on_change
    else:
        # Use pipeline watcher
        watcher = PipelineWatcher(
            watch_config,
            processor_func=processor_func,
            enable_hot_reload=args.hot_reload
        )

    # Set up signal handler for graceful shutdown
    def signal_handler(sig, frame):
        vprint.info("\nReceived interrupt signal")
        watcher.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)

    # Start watching
    try:
        watcher.start()

        # Keep main thread alive
        while True:
            import time
            time.sleep(1)

    except KeyboardInterrupt:
        watcher.stop()
        return 0
    except Exception as e:
        vprint.error(str(e))
        if verbosity >= 2:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
