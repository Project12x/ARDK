"""
Progress Reporting and Summary Generation.

Provides:
- Progress bars (text-based with optional tqdm support)
- Summary reports (text and JSON)
- Timing and statistics tracking
- CI/CD-friendly output formats

Usage:
    from pipeline.reporting import ProgressTracker, SummaryReport, JSONReporter

    # Track progress
    tracker = ProgressTracker(total=10, description="Processing sprites")
    for item in items:
        process(item)
        tracker.advance()
    tracker.finish()

    # Generate summary
    report = SummaryReport()
    report.add_success("sprite.png", {"tiles": 4})
    report.add_warning("large.png", "File exceeds recommended size")
    report.add_error("broken.png", "Invalid format")
    report.print_summary()

    # JSON output for CI/CD
    reporter = JSONReporter()
    reporter.add_result("sprite.png", success=True, data={...})
    reporter.save("report.json")
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, TextIO
from pathlib import Path
from datetime import datetime
from enum import Enum
import json
import sys
import time

# Try to import tqdm for fancy progress bars
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False


class ResultStatus(Enum):
    """Result status for processed items."""
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class ProcessingResult:
    """Result of processing a single item."""
    path: str
    status: ResultStatus
    message: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ProgressTracker:
    """
    Track and display progress for batch operations.

    Uses tqdm if available, falls back to simple text progress.
    """

    def __init__(
        self,
        total: int,
        description: str = "Processing",
        unit: str = "items",
        disable: bool = False,
        file: TextIO = sys.stderr,
        bar_format: Optional[str] = None,
    ):
        """
        Initialize progress tracker.

        Args:
            total: Total number of items to process
            description: Description shown before progress bar
            unit: Unit name for items (e.g., "files", "sprites")
            disable: If True, don't show progress (for quiet mode)
            file: Output file for progress (default: stderr)
            bar_format: Custom format string (tqdm only)
        """
        self.total = total
        self.description = description
        self.unit = unit
        self.disable = disable
        self.file = file
        self.current = 0
        self.start_time = time.time()
        self._last_update = 0

        if HAS_TQDM and not disable:
            self._pbar = tqdm(
                total=total,
                desc=description,
                unit=unit,
                file=file,
                bar_format=bar_format,
                leave=True,
            )
        else:
            self._pbar = None
            if not disable:
                self._print_simple_start()

    def _print_simple_start(self):
        """Print simple progress start."""
        print(f"{self.description}: 0/{self.total} {self.unit}", file=self.file, end="")
        self.file.flush()

    def _print_simple_update(self):
        """Print simple progress update."""
        elapsed = time.time() - self.start_time
        rate = self.current / elapsed if elapsed > 0 else 0

        # Clear line and reprint
        print(f"\r{self.description}: {self.current}/{self.total} {self.unit} "
              f"[{elapsed:.1f}s, {rate:.1f} {self.unit}/s]",
              file=self.file, end="")
        self.file.flush()

    def advance(self, n: int = 1, status: Optional[str] = None):
        """
        Advance progress by n items.

        Args:
            n: Number of items to advance
            status: Optional status message to display
        """
        self.current += n

        if self._pbar:
            self._pbar.update(n)
            if status:
                self._pbar.set_postfix_str(status)
        elif not self.disable:
            # Rate-limit simple updates (every 0.1s or on completion)
            now = time.time()
            if now - self._last_update > 0.1 or self.current >= self.total:
                self._print_simple_update()
                self._last_update = now

    def set_description(self, description: str):
        """Update the description."""
        self.description = description
        if self._pbar:
            self._pbar.set_description(description)

    def finish(self):
        """Complete the progress tracking."""
        elapsed = time.time() - self.start_time

        if self._pbar:
            self._pbar.close()
        elif not self.disable:
            print(f"\r{self.description}: {self.total}/{self.total} {self.unit} "
                  f"[{elapsed:.1f}s total]", file=self.file)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.finish()


class SummaryReport:
    """
    Collect and display processing summary.

    Tracks successes, warnings, errors, and statistics.
    """

    def __init__(self, title: str = "Processing Summary"):
        """Initialize summary report."""
        self.title = title
        self.results: List[ProcessingResult] = []
        self.start_time = time.time()
        self.extra_stats: Dict[str, Any] = {}

    def add_result(
        self,
        path: str,
        status: ResultStatus,
        message: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        duration_ms: float = 0.0,
    ):
        """Add a processing result."""
        self.results.append(ProcessingResult(
            path=str(path),
            status=status,
            message=message,
            data=data or {},
            duration_ms=duration_ms,
        ))

    def add_success(self, path: str, data: Optional[Dict[str, Any]] = None, duration_ms: float = 0.0):
        """Add a successful result."""
        self.add_result(path, ResultStatus.SUCCESS, data=data, duration_ms=duration_ms)

    def add_warning(self, path: str, message: str, data: Optional[Dict[str, Any]] = None):
        """Add a warning result."""
        self.add_result(path, ResultStatus.WARNING, message=message, data=data)

    def add_error(self, path: str, message: str, data: Optional[Dict[str, Any]] = None):
        """Add an error result."""
        self.add_result(path, ResultStatus.ERROR, message=message, data=data)

    def add_skipped(self, path: str, reason: str):
        """Add a skipped result."""
        self.add_result(path, ResultStatus.SKIPPED, message=reason)

    def add_stat(self, key: str, value: Any):
        """Add an extra statistic."""
        self.extra_stats[key] = value

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.results if r.status == ResultStatus.SUCCESS)

    @property
    def warning_count(self) -> int:
        return sum(1 for r in self.results if r.status == ResultStatus.WARNING)

    @property
    def error_count(self) -> int:
        return sum(1 for r in self.results if r.status == ResultStatus.ERROR)

    @property
    def skipped_count(self) -> int:
        return sum(1 for r in self.results if r.status == ResultStatus.SKIPPED)

    @property
    def total_count(self) -> int:
        return len(self.results)

    @property
    def total_duration_ms(self) -> float:
        return sum(r.duration_ms for r in self.results)

    @property
    def elapsed_seconds(self) -> float:
        return time.time() - self.start_time

    @property
    def has_errors(self) -> bool:
        return self.error_count > 0

    @property
    def has_warnings(self) -> bool:
        return self.warning_count > 0

    def get_by_status(self, status: ResultStatus) -> List[ProcessingResult]:
        """Get all results with a specific status."""
        return [r for r in self.results if r.status == status]

    def print_summary(
        self,
        file: TextIO = sys.stdout,
        show_all: bool = False,
        show_warnings: bool = True,
        show_errors: bool = True,
        char: str = "=",
        width: int = 60,
    ):
        """
        Print formatted summary report.

        Args:
            file: Output file
            show_all: Show all processed files (not just errors/warnings)
            show_warnings: Show warning details
            show_errors: Show error details
            char: Character for separator lines
            width: Width of separator lines
        """
        # Header
        print(char * width, file=file)
        print(f"  {self.title}", file=file)
        print(char * width, file=file)
        print(file=file)

        # Statistics
        print(f"Total processed: {self.total_count}", file=file)
        print(f"  Successful:    {self.success_count}", file=file)
        if self.warning_count:
            print(f"  Warnings:      {self.warning_count}", file=file)
        if self.error_count:
            print(f"  Errors:        {self.error_count}", file=file)
        if self.skipped_count:
            print(f"  Skipped:       {self.skipped_count}", file=file)
        print(file=file)

        # Timing
        print(f"Time elapsed:    {self.elapsed_seconds:.2f}s", file=file)
        if self.total_count > 0:
            avg_ms = self.total_duration_ms / self.total_count
            print(f"Avg per file:    {avg_ms:.1f}ms", file=file)
        print(file=file)

        # Extra stats
        if self.extra_stats:
            print("Statistics:", file=file)
            for key, value in self.extra_stats.items():
                print(f"  {key}: {value}", file=file)
            print(file=file)

        # Errors
        if show_errors and self.error_count:
            print("-" * width, file=file)
            print("ERRORS:", file=file)
            for result in self.get_by_status(ResultStatus.ERROR):
                print(f"  [ERROR] {result.path}", file=file)
                if result.message:
                    print(f"          {result.message}", file=file)
            print(file=file)

        # Warnings
        if show_warnings and self.warning_count:
            print("-" * width, file=file)
            print("WARNINGS:", file=file)
            for result in self.get_by_status(ResultStatus.WARNING):
                print(f"  [WARN] {result.path}", file=file)
                if result.message:
                    print(f"         {result.message}", file=file)
            print(file=file)

        # All files (if requested)
        if show_all:
            print("-" * width, file=file)
            print("ALL FILES:", file=file)
            for result in self.results:
                status_icon = {
                    ResultStatus.SUCCESS: "[OK]",
                    ResultStatus.WARNING: "[WARN]",
                    ResultStatus.ERROR: "[ERROR]",
                    ResultStatus.SKIPPED: "[SKIP]",
                }[result.status]
                print(f"  {status_icon} {result.path}", file=file)
            print(file=file)

        # Footer
        print(char * width, file=file)

        # Final status line
        if self.error_count:
            print(f"FAILED: {self.error_count} error(s)", file=file)
        elif self.warning_count:
            print(f"COMPLETED with {self.warning_count} warning(s)", file=file)
        else:
            print("COMPLETED successfully", file=file)
        print(char * width, file=file)

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "title": self.title,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": self.total_count,
                "success": self.success_count,
                "warnings": self.warning_count,
                "errors": self.error_count,
                "skipped": self.skipped_count,
            },
            "timing": {
                "elapsed_seconds": round(self.elapsed_seconds, 3),
                "total_processing_ms": round(self.total_duration_ms, 1),
            },
            "statistics": self.extra_stats,
            "results": [
                {
                    "path": r.path,
                    "status": r.status.value,
                    "message": r.message,
                    "data": r.data,
                    "duration_ms": r.duration_ms,
                    "timestamp": r.timestamp,
                }
                for r in self.results
            ],
        }


class JSONReporter:
    """
    Generate JSON reports for CI/CD integration.

    Outputs machine-readable results for automated pipelines.
    """

    def __init__(self, tool_name: str = "ardk-pipeline", version: str = "1.0"):
        """Initialize JSON reporter."""
        self.tool_name = tool_name
        self.version = version
        self.start_time = datetime.now()
        self.results: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}

    def add_metadata(self, key: str, value: Any):
        """Add metadata to the report."""
        self.metadata[key] = value

    def add_result(
        self,
        path: str,
        success: bool,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        warnings: Optional[List[str]] = None,
    ):
        """Add a processing result."""
        self.results.append({
            "path": str(path),
            "success": success,
            "error": error,
            "warnings": warnings or [],
            "data": data or {},
            "timestamp": datetime.now().isoformat(),
        })

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        end_time = datetime.now()
        success_count = sum(1 for r in self.results if r["success"])
        error_count = sum(1 for r in self.results if not r["success"])

        return {
            "tool": self.tool_name,
            "version": self.version,
            "timestamp": {
                "start": self.start_time.isoformat(),
                "end": end_time.isoformat(),
                "duration_seconds": (end_time - self.start_time).total_seconds(),
            },
            "summary": {
                "total": len(self.results),
                "success": success_count,
                "errors": error_count,
                "exit_code": 0 if error_count == 0 else 1,
            },
            "metadata": self.metadata,
            "results": self.results,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def save(self, path: str):
        """Save report to JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            f.write(self.to_json())

    def print_json(self, file: TextIO = sys.stdout, indent: int = 2):
        """Print JSON to file."""
        print(self.to_json(indent=indent), file=file)


def format_duration(seconds: float) -> str:
    """Format duration in human-readable form."""
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.0f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def format_size(bytes: int) -> str:
    """Format file size in human-readable form."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024:
            return f"{bytes:.1f}{unit}"
        bytes /= 1024
    return f"{bytes:.1f}TB"
