"""
Shared CLI utilities for consistent argument handling across all pipeline tools.

Usage:
    from pipeline.cli_utils import create_parser, add_common_args, setup_from_args

    parser = create_parser("Tool description")
    add_common_args(parser)
    # Add tool-specific args...
    args = parser.parse_args()

    config, verbose = setup_from_args(args)

    # With reporting
    from pipeline.cli_utils import create_reporter
    reporter = create_reporter(args)
    # ... process files ...
    reporter.finish()
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, Tuple, List, Any

from .core import (
    PipelineConfig,
    get_config,
    load_project_config,
    find_config_file,
    clear_config_cache,
)
from .reporting import (
    ProgressTracker,
    SummaryReport,
    JSONReporter,
    ResultStatus,
    format_duration,
    format_size,
)


def create_parser(
    description: str,
    epilog: Optional[str] = None
) -> argparse.ArgumentParser:
    """
    Create an argument parser with consistent formatting.

    Args:
        description: Tool description
        epilog: Optional epilog text

    Returns:
        Configured ArgumentParser
    """
    if epilog is None:
        epilog = "Uses .ardk.yaml config if present. CLI args override config values."

    return argparse.ArgumentParser(
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )


def add_common_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """
    Add common arguments used by all pipeline tools.

    Adds:
        --config/-c: Config file path
        --platform/-p: Target platform override
        --output/-o: Output directory override
        --dry-run: Preview mode (no writes)
        --verbose/-v: Verbose output
        --quiet/-q: Suppress non-essential output

    Args:
        parser: Parser to add arguments to

    Returns:
        The parser (for chaining)
    """
    # Config group
    config_group = parser.add_argument_group('configuration')
    config_group.add_argument(
        '--config', '-c',
        metavar='FILE',
        help='Config file path (default: auto-discover .ardk.yaml)'
    )
    config_group.add_argument(
        '--platform', '-p',
        choices=['nes', 'genesis', 'snes', 'gameboy', 'sms', 'pce', 'amiga'],
        help='Target platform (overrides config)'
    )

    # Output group
    output_group = parser.add_argument_group('output')
    output_group.add_argument(
        '--output', '-o',
        metavar='DIR',
        help='Output directory (overrides config)'
    )
    output_group.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Preview mode - show what would be done without making changes'
    )

    # Verbosity group
    verbosity_group = parser.add_argument_group('verbosity')
    verbosity_group.add_argument(
        '--verbose', '-v',
        action='count',
        default=0,
        help='Increase verbosity (-v for info, -vv for debug)'
    )
    verbosity_group.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress non-essential output'
    )

    # Reporting group
    report_group = parser.add_argument_group('reporting')
    report_group.add_argument(
        '--json',
        metavar='FILE',
        nargs='?',
        const='-',
        help='Output JSON report (use - for stdout, or specify file path)'
    )
    report_group.add_argument(
        '--summary',
        action='store_true',
        help='Show detailed summary at end'
    )
    report_group.add_argument(
        '--progress',
        action='store_true',
        default=True,
        help='Show progress bar (default: enabled)'
    )
    report_group.add_argument(
        '--no-progress',
        action='store_true',
        help='Disable progress bar'
    )

    return parser


def add_safety_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """
    Add safety-related arguments for tools that do AI generation or expensive operations.

    Adds:
        --max-generations: Limit AI generations
        --budget: Budget cap in USD
        --no-confirm: Skip confirmation prompts

    Args:
        parser: Parser to add arguments to

    Returns:
        The parser (for chaining)
    """
    safety_group = parser.add_argument_group('safety')
    safety_group.add_argument(
        '--max-generations',
        type=int,
        metavar='N',
        help='Maximum AI generations per run (overrides config)'
    )
    safety_group.add_argument(
        '--budget',
        type=float,
        metavar='USD',
        help='Budget cap in USD (overrides config)'
    )
    safety_group.add_argument(
        '--no-confirm',
        action='store_true',
        help='Skip confirmation prompts'
    )

    return parser


def add_watch_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """
    Add watch mode arguments.

    Adds:
        --debounce: Debounce delay
        --max-rate: Rate limit
        --max-file-size: File size limit
        --timeout: Processing timeout

    Args:
        parser: Parser to add arguments to

    Returns:
        The parser (for chaining)
    """
    watch_group = parser.add_argument_group('watch mode')
    watch_group.add_argument(
        '--debounce',
        type=float,
        metavar='SECONDS',
        help='Debounce delay before processing (default: 1.0)'
    )
    watch_group.add_argument(
        '--max-rate',
        type=int,
        metavar='N',
        help='Maximum changes per minute (default: 60)'
    )
    watch_group.add_argument(
        '--max-file-size',
        type=float,
        metavar='MB',
        help='Skip files larger than this (default: 50.0)'
    )
    watch_group.add_argument(
        '--timeout',
        type=float,
        metavar='SECONDS',
        help='Processing timeout per file (default: 30.0)'
    )

    return parser


def setup_from_args(
    args: argparse.Namespace,
    require_config: bool = False
) -> Tuple[PipelineConfig, int]:
    """
    Load config and apply CLI overrides.

    Args:
        args: Parsed arguments
        require_config: If True, error if no config file found

    Returns:
        Tuple of (config, verbosity_level)
        verbosity_level: 0=quiet, 1=normal, 2=verbose, 3=debug
    """
    # Clear cache to ensure fresh load
    clear_config_cache()

    # Load config
    config_path = getattr(args, 'config', None)

    if config_path:
        config = load_project_config(config_path=config_path)
    else:
        config = load_project_config()

    # Check if config file was found
    if require_config and config.project_root is None:
        config_file = find_config_file()
        if config_file is None:
            print("Error: No config file found. Create .ardk.yaml or use --config", file=sys.stderr)
            sys.exit(1)

    # Apply CLI overrides
    if hasattr(args, 'platform') and args.platform:
        config.platform = args.platform

    if hasattr(args, 'output') and args.output:
        config.paths.output = args.output

    if hasattr(args, 'dry_run') and args.dry_run:
        config.safeguards.dry_run = True

    # Safety overrides
    if hasattr(args, 'max_generations') and args.max_generations is not None:
        config.safeguards.max_generations_per_run = args.max_generations

    if hasattr(args, 'budget') and args.budget is not None:
        config.safeguards.max_cost_per_run = args.budget

    if hasattr(args, 'no_confirm') and args.no_confirm:
        config.safeguards.require_confirmation = False

    # Watch mode overrides
    if hasattr(args, 'debounce') and args.debounce is not None:
        config.watch.debounce = args.debounce

    if hasattr(args, 'max_rate') and args.max_rate is not None:
        config.watch.max_rate = args.max_rate

    if hasattr(args, 'max_file_size') and args.max_file_size is not None:
        config.watch.max_file_size_mb = args.max_file_size

    if hasattr(args, 'timeout') and args.timeout is not None:
        config.watch.timeout = args.timeout

    # Calculate verbosity level
    quiet = getattr(args, 'quiet', False)
    verbose = getattr(args, 'verbose', 0)

    if quiet:
        verbosity = 0
    else:
        verbosity = 1 + verbose  # 1=normal, 2=verbose, 3+=debug

    return config, verbosity


def print_config_status(config: PipelineConfig, verbosity: int = 1):
    """
    Print config status message.

    Args:
        config: Loaded config
        verbosity: Verbosity level (0=quiet, 1=normal, 2+=verbose)
    """
    if verbosity == 0:
        return

    config_file = find_config_file()
    if config_file:
        print(f"Config: {config_file}")
    else:
        print("Config: defaults (no .ardk.yaml found)")

    if verbosity >= 2:
        print(f"Platform: {config.platform}")
        print(f"Output: {config.paths.output}")
        print(f"Dry-run: {config.safeguards.dry_run}")
        print()


def print_dry_run_notice():
    """Print dry-run mode notice."""
    print()
    print("=" * 60)
    print("DRY-RUN MODE - No changes were made")
    print("Use --no-dry-run or set dry_run: false in config to enable")
    print("=" * 60)


def confirm_action(prompt: str, default: bool = False) -> bool:
    """
    Ask for user confirmation.

    Args:
        prompt: Question to ask
        default: Default if user just presses Enter

    Returns:
        True if confirmed
    """
    if default:
        suffix = "[Y/n]"
    else:
        suffix = "[y/N]"

    try:
        response = input(f"{prompt} {suffix} ").strip().lower()
        if not response:
            return default
        return response in ('y', 'yes')
    except (EOFError, KeyboardInterrupt):
        print()
        return False


class VerbosePrinter:
    """
    Context-aware printer that respects verbosity settings.

    Usage:
        vprint = VerbosePrinter(verbosity=2)
        vprint.info("Always shown")
        vprint.verbose("Only at -v")
        vprint.debug("Only at -vv")
    """

    def __init__(self, verbosity: int = 1, prefix: str = ""):
        """
        Initialize printer.

        Args:
            verbosity: 0=quiet, 1=normal, 2=verbose, 3=debug
            prefix: Optional prefix for all messages
        """
        self.verbosity = verbosity
        self.prefix = prefix

    def _print(self, msg: str, level: int, prefix: str = ""):
        """Internal print with level check."""
        if self.verbosity >= level:
            full_prefix = f"{self.prefix}{prefix}" if prefix else self.prefix
            if full_prefix:
                print(f"{full_prefix}{msg}")
            else:
                print(msg)

    def error(self, msg: str):
        """Print error (always shown)."""
        self._print(msg, 0, "[ERROR] ")

    def warn(self, msg: str):
        """Print warning (always shown)."""
        self._print(msg, 0, "[WARN] ")

    def info(self, msg: str):
        """Print info (normal verbosity)."""
        self._print(msg, 1)

    def success(self, msg: str):
        """Print success (normal verbosity)."""
        self._print(msg, 1, "[OK] ")

    def verbose(self, msg: str):
        """Print verbose message (requires -v)."""
        self._print(msg, 2, "  ")

    def debug(self, msg: str):
        """Print debug message (requires -vv)."""
        self._print(msg, 3, "  [DEBUG] ")

    def header(self, msg: str, char: str = "=", width: int = 60):
        """Print section header."""
        if self.verbosity >= 1:
            print(char * width)
            print(msg)
            print(char * width)
            print()


class CLIReporter:
    """
    Unified reporter for CLI tools with progress, summary, and JSON output.

    Usage:
        reporter = CLIReporter(args, verbosity, total_items=10, title="Processing")
        for item in items:
            try:
                result = process(item)
                reporter.success(item, data={"tiles": result.tiles})
            except Exception as e:
                reporter.error(item, str(e))
            reporter.advance()
        exit_code = reporter.finish()
    """

    def __init__(
        self,
        args: argparse.Namespace,
        verbosity: int = 1,
        total_items: int = 0,
        title: str = "Processing",
        tool_name: str = "ardk-pipeline",
    ):
        """
        Initialize CLI reporter.

        Args:
            args: Parsed arguments (checks for --json, --summary, --no-progress)
            verbosity: Verbosity level
            total_items: Total items for progress bar
            title: Title for summary report
            tool_name: Tool name for JSON output
        """
        self.args = args
        self.verbosity = verbosity
        self.vprint = VerbosePrinter(verbosity)

        # Determine output modes
        self.json_output = getattr(args, 'json', None)
        self.show_summary = getattr(args, 'summary', False)
        self.show_progress = (
            not getattr(args, 'no_progress', False) and
            getattr(args, 'progress', True) and
            verbosity > 0 and
            total_items > 0 and
            not self.json_output  # Disable progress for JSON output
        )

        # Create trackers
        self.summary = SummaryReport(title=title)
        self.json_reporter = JSONReporter(tool_name=tool_name) if self.json_output else None

        # Create progress tracker
        if self.show_progress:
            self.progress = ProgressTracker(
                total=total_items,
                description=title,
                disable=verbosity == 0,
            )
        else:
            self.progress = None

    def success(
        self,
        path: str,
        message: Optional[str] = None,
        data: Optional[dict] = None,
        duration_ms: float = 0.0,
    ):
        """Record a successful result."""
        self.summary.add_success(path, data=data, duration_ms=duration_ms)
        if self.json_reporter:
            self.json_reporter.add_result(path, success=True, data=data)

    def warning(self, path: str, message: str, data: Optional[dict] = None):
        """Record a warning."""
        self.summary.add_warning(path, message, data=data)
        if self.json_reporter:
            self.json_reporter.add_result(path, success=True, warnings=[message], data=data)

    def error(self, path: str, message: str, data: Optional[dict] = None):
        """Record an error."""
        self.summary.add_error(path, message, data=data)
        if self.json_reporter:
            self.json_reporter.add_result(path, success=False, error=message, data=data)

    def skip(self, path: str, reason: str):
        """Record a skipped item."""
        self.summary.add_skipped(path, reason)
        if self.json_reporter:
            self.json_reporter.add_result(path, success=True, warnings=[f"Skipped: {reason}"])

    def add_stat(self, key: str, value: Any):
        """Add a statistic to the summary."""
        self.summary.add_stat(key, value)
        if self.json_reporter:
            self.json_reporter.add_metadata(key, value)

    def advance(self, n: int = 1, status: Optional[str] = None):
        """Advance the progress bar."""
        if self.progress:
            self.progress.advance(n, status)

    def set_description(self, description: str):
        """Update progress description."""
        if self.progress:
            self.progress.set_description(description)

    def finish(self) -> int:
        """
        Finish reporting and output results.

        Returns:
            Exit code (0 for success, 1 for errors)
        """
        # Close progress bar
        if self.progress:
            self.progress.finish()

        # Output JSON if requested
        if self.json_output:
            if self.json_output == '-':
                self.json_reporter.print_json()
            else:
                self.json_reporter.save(self.json_output)
                self.vprint.info(f"JSON report saved to: {self.json_output}")

        # Show summary if requested or if errors occurred
        elif self.show_summary or self.summary.has_errors:
            self.summary.print_summary(
                show_warnings=True,
                show_errors=True,
            )
        elif self.verbosity > 0:
            # Brief status line
            if self.summary.has_errors:
                print(f"Completed with {self.summary.error_count} errors")
            elif self.summary.has_warnings:
                print(f"Completed with {self.summary.warning_count} warnings")
            elif self.summary.total_count > 0:
                print(f"Completed: {self.summary.success_count} files processed")

        # Return exit code
        return 1 if self.summary.has_errors else 0

    @property
    def has_errors(self) -> bool:
        return self.summary.has_errors


def create_reporter(
    args: argparse.Namespace,
    verbosity: int = 1,
    total_items: int = 0,
    title: str = "Processing",
    tool_name: str = "ardk-pipeline",
) -> CLIReporter:
    """
    Create a CLI reporter from parsed arguments.

    Args:
        args: Parsed arguments
        verbosity: Verbosity level
        total_items: Total items for progress bar
        title: Title for summary report
        tool_name: Tool name for JSON output

    Returns:
        Configured CLIReporter
    """
    return CLIReporter(
        args=args,
        verbosity=verbosity,
        total_items=total_items,
        title=title,
        tool_name=tool_name,
    )
