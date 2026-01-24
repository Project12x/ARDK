#!/usr/bin/env python3
"""
ARDK Pipeline CLI - Command Line Interface.

This is the CLI wrapper for the core Pipeline.
It provides argument parsing and interactive confirmation.

The core Pipeline enforces all safeguards - this CLI just provides
a user-friendly interface.

Usage:
    # Process a PNG (dry-run by default)
    python -m tools.pipeline.cli sprite.png -o output/

    # Actually process (disable dry-run)
    python -m tools.pipeline.cli sprite.png -o output/ --no-dry-run

    # Process Aseprite file
    python -m tools.pipeline.cli character.ase -o output/

    # Generate from prompt
    python -m tools.pipeline.cli "warrior with sword" -o output/ --generate

    # Batch process directory
    python -m tools.pipeline.cli --batch gfx/input/ -o gfx/output/

    # Check status
    python -m tools.pipeline.cli --status
"""

import argparse
import sys
import os
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.core import (
    Pipeline,
    PipelineConfig,
    SafeguardConfig,
    GenerationConfig,
    ProcessingConfig,
    ExportConfig,
    EventEmitter,
    EventType,
    SafeguardViolation,
    BudgetExhausted,
    DryRunActive,
)
from pipeline.core.events import ConsoleEventHandler


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog='ardk-pipeline',
        description='ARDK Asset Pipeline - Unified sprite processing with enforced safeguards',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Process PNG (dry-run by default - safe!)
    python -m tools.pipeline.cli sprite.png -o output/

    # Actually process (requires explicit --no-dry-run)
    python -m tools.pipeline.cli sprite.png -o output/ --no-dry-run

    # Process Aseprite file
    python -m tools.pipeline.cli character.ase -o output/ --no-dry-run

    # Generate 8-direction character
    python -m tools.pipeline.cli "warrior with sword" -o output/ --generate --8dir

    # Batch process with custom limits
    python -m tools.pipeline.cli --batch input/ -o output/ --max-gens 10 --max-cost 1.00

Platforms:
    nes, genesis, snes, gameboy, sms, pce, amiga

Safety:
    - Dry-run is ON by default (use --no-dry-run to disable)
    - Generation budget: 5 per run, $0.50 max (use --max-gens/--max-cost to change)
    - All results are cached before processing
"""
    )

    # Input (positional or via flags)
    parser.add_argument('input', nargs='?', help='Input file (PNG, ASE) or prompt')
    parser.add_argument('-o', '--output', help='Output directory (required for processing)')
    parser.add_argument('--batch', metavar='DIR', help='Batch process directory')

    # Mode flags
    parser.add_argument('--generate', '-g', action='store_true',
                       help='Treat input as generation prompt')
    parser.add_argument('--8dir', dest='eight_dir', action='store_true',
                       help='Generate 8 directional views')
    parser.add_argument('--status', action='store_true',
                       help='Show pipeline status and exit')

    # Platform
    parser.add_argument('--platform', '-p', default='genesis',
                       choices=['nes', 'genesis', 'megadrive', 'snes',
                               'gameboy', 'gb', 'sms', 'pce', 'amiga'],
                       help='Target platform (default: genesis)')

    # Processing
    parser.add_argument('--size', type=int, default=32,
                       help='Target sprite size (default: 32)')
    parser.add_argument('--palette', type=str,
                       help='Force palette name (e.g., player_warm)')
    parser.add_argument('--category', type=str,
                       help='Asset category (player, enemy, etc.)')
    parser.add_argument('--collision', action='store_true',
                       help='Generate collision data')

    # AI
    parser.add_argument('--ai', type=str,
                       choices=['groq', 'gemini', 'openai', 'anthropic', 'pollinations'],
                       help='AI provider for analysis')
    parser.add_argument('--offline', action='store_true',
                       help='Offline mode (no AI)')

    # Safeguards
    parser.add_argument('--no-dry-run', action='store_true',
                       help='Disable dry-run mode (REQUIRED for real operations)')
    parser.add_argument('--no-confirm', action='store_true',
                       help='Skip confirmation prompts')
    parser.add_argument('--max-gens', type=int, default=5,
                       help='Maximum generations per run (default: 5)')
    parser.add_argument('--max-cost', type=float, default=0.50,
                       help='Maximum cost in USD (default: 0.50)')

    # Output control
    parser.add_argument('--no-res', action='store_true',
                       help='Skip .res file generation')
    parser.add_argument('--no-headers', action='store_true',
                       help='Skip header file generation')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')

    # Config file
    parser.add_argument('--config', type=str,
                       help='Load config from JSON file')
    parser.add_argument('--save-config', type=str,
                       help='Save config to JSON file')

    return parser


def build_config(args) -> PipelineConfig:
    """Build PipelineConfig from parsed arguments."""
    # Safeguards config
    safeguards = SafeguardConfig(
        dry_run=not args.no_dry_run,  # Dry-run ON by default!
        require_confirmation=not args.no_confirm,
        max_generations_per_run=args.max_gens,
        max_cost_per_run=args.max_cost,
    )

    # Generation config
    generation = GenerationConfig(
        width=args.size,
        height=args.size,
        generate_8_directions=args.eight_dir,
    )

    # Processing config
    processing = ProcessingConfig(
        target_size=args.size,
        palette_name=args.palette,
        generate_collision=args.collision,
    )

    # Export config
    export = ExportConfig(
        generate_res_file=not args.no_res,
        generate_headers=not args.no_headers,
    )

    return PipelineConfig(
        platform=args.platform,
        safeguards=safeguards,
        generation=generation,
        processing=processing,
        export=export,
        ai_provider=args.ai,
        offline_mode=args.offline,
        verbose=args.verbose,
    )


def interactive_confirm(prompt: str) -> bool:
    """Ask for user confirmation."""
    response = input(f"\n{prompt} [y/N]: ").strip().lower()
    return response == 'y'


def print_status(pipeline: Pipeline):
    """Print pipeline status."""
    status = pipeline.get_status()

    print("\n" + "=" * 60)
    print("ARDK Pipeline Status")
    print("=" * 60)
    print(f"\n  Platform: {status['platform'].upper()}")
    print(f"  Offline:  {status['offline_mode']}")
    print("\n  Safeguards:")
    sg = status['safeguards']
    print(f"    Dry-run:        {sg['dry_run']} {'(SAFE MODE)' if sg['dry_run'] else ''}")
    print(f"    Gens remaining: {sg['generations_remaining']}")
    print(f"    Cost remaining: ${sg['cost_remaining']:.2f}")
    print(f"    Cache dir:      {sg['cache_dir']}")
    print("=" * 60 + "\n")


def main():
    parser = create_parser()
    args = parser.parse_args()

    # Load config from file if specified
    if args.config:
        config = PipelineConfig.load(args.config)
        # Override with CLI args
        if args.no_dry_run:
            config.safeguards.dry_run = False
    else:
        config = build_config(args)

    # Save config if requested
    if args.save_config:
        config.save(args.save_config)
        print(f"Config saved to: {args.save_config}")
        return

    # Create event emitter with console handler
    emitter = EventEmitter()
    emitter.on_all(ConsoleEventHandler(verbose=args.verbose))

    # Create pipeline
    pipeline = Pipeline(config, event_emitter=emitter)

    # Status check
    if args.status:
        print_status(pipeline)
        return

    # Validate output is specified for processing
    if not args.output:
        parser.print_help()
        print("\nError: -o/--output is required for processing.")
        sys.exit(1)

    # Validate input
    if not args.input and not args.batch:
        parser.print_help()
        print("\nError: No input specified. Provide a file path or use --batch.")
        sys.exit(1)

    # Print header
    print("\n" + "=" * 60)
    print("  ARDK Asset Pipeline")
    print("=" * 60)
    print(f"  Platform:  {config.platform.upper()}")
    print(f"  Dry-run:   {config.safeguards.dry_run}")
    print(f"  Max gens:  {config.safeguards.max_generations_per_run}")
    print(f"  Max cost:  ${config.safeguards.max_cost_per_run:.2f}")
    print("=" * 60 + "\n")

    # Handle confirmation if needed
    if not config.safeguards.require_confirmation:
        pipeline.confirm()
    else:
        # Interactive confirmation
        if config.safeguards.dry_run:
            print("[DRY RUN] This is a preview - no changes will be made.")
            print("          Use --no-dry-run to enable real operations.\n")
        else:
            if args.generate:
                prompt = f"Generate from: {args.input[:50]}..."
            else:
                prompt = f"Process: {args.input}"

            if interactive_confirm(f"Proceed with: {prompt}"):
                pipeline.confirm()
            else:
                print("Aborted.")
                sys.exit(0)

    # Execute
    try:
        if args.batch:
            result = pipeline.process_batch(args.batch, args.output)
        elif args.generate:
            result = pipeline.generate(args.input, args.output)
        else:
            result = pipeline.process(args.input, args.output, args.category)

        # Handle result
        if result.get('dry_run'):
            print(result.get('report', 'Dry-run complete.'))
        elif result.get('confirmation_required'):
            print("\nConfirmation required. Run with --no-confirm to skip.")
        elif result.get('success'):
            print("\n" + "=" * 60)
            print("  SUCCESS")
            print("=" * 60)
            if 'cost_usd' in result:
                print(f"  Cost: ${result['cost_usd']:.4f}")
            if 'images' in result:
                print(f"  Images: {', '.join(result['images'])}")
            print(f"  Output: {args.output}")
            print("=" * 60 + "\n")
        else:
            print(f"\nError: {result.get('error', 'Unknown error')}")
            sys.exit(1)

    except BudgetExhausted as e:
        print(f"\n[BUDGET EXHAUSTED] {e}")
        print("Use --max-gens or --max-cost to increase limits.")
        sys.exit(1)

    except DryRunActive as e:
        print(f"\n[DRY RUN] {e}")
        sys.exit(0)

    except SafeguardViolation as e:
        print(f"\n[SAFEGUARD] {e}")
        sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nAborted by user.")
        sys.exit(130)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
