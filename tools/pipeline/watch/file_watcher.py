"""
File Watcher for Asset Pipeline.

Monitors file system for asset changes and triggers pipeline processing with
debouncing and hot reload support.

Usage:
    >>> from pipeline.watch import AssetWatcher, WatchConfig
    >>> config = WatchConfig(
    ...     watch_dirs=['assets/sprites', 'assets/tilesets'],
    ...     extensions=['.png', '.aseprite'],
    ...     debounce_seconds=1.0
    ... )
    >>> watcher = AssetWatcher(config)
    >>> watcher.on_change = lambda event: print(f"Changed: {event.path}")
    >>> watcher.start()
    >>> # ... watcher runs in background ...
    >>> watcher.stop()
"""

from typing import List, Callable, Optional, Set, Dict, Any
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import time
import threading
import hashlib
from collections import deque
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent


class ChangeType(Enum):
    """Type of file change."""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"


@dataclass
class FileChangeEvent:
    """
    File change event with metadata.

    Attributes:
        path: Path to changed file
        change_type: Type of change
        timestamp: Unix timestamp of change
        hash: SHA256 hash of file (None for deletions)
    """
    path: Path
    change_type: ChangeType
    timestamp: float
    hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'path': str(self.path),
            'change_type': self.change_type.value,
            'timestamp': self.timestamp,
            'hash': self.hash,
        }


@dataclass
class SafetyConfig:
    """
    Safety limits for watch mode to prevent resource exhaustion.

    Attributes:
        max_file_size_mb: Maximum file size to process (MB)
        max_changes_per_minute: Rate limit for processing
        max_queue_depth: Maximum pending files in queue
        max_processing_time_seconds: Timeout per file processing
        circuit_breaker_errors: Pause after N consecutive errors
        circuit_breaker_cooldown: Cooldown period after circuit break (seconds)
        error_backoff_seconds: Delay after processing error
    """
    max_file_size_mb: float = 50.0
    max_changes_per_minute: int = 60
    max_queue_depth: int = 100
    max_processing_time_seconds: float = 30.0
    circuit_breaker_errors: int = 5
    circuit_breaker_cooldown: float = 60.0
    error_backoff_seconds: float = 5.0


@dataclass
class WatchConfig:
    """
    Configuration for asset watcher.

    Attributes:
        watch_dirs: Directories to watch
        extensions: File extensions to monitor (e.g., ['.png', '.aseprite'])
        debounce_seconds: Wait time before processing (avoid rapid rewrites)
        recursive: Watch subdirectories recursively
        ignore_patterns: Glob patterns to ignore (e.g., ['*.tmp', '.*'])
        hot_reload_enabled: Enable hot reload to emulator/runtime
        hot_reload_command: Command to trigger hot reload
        safety: Safety limits (None = no limits)
    """
    watch_dirs: List[str]
    extensions: List[str] = field(default_factory=lambda: ['.png', '.aseprite', '.bmp'])
    debounce_seconds: float = 1.0
    recursive: bool = True
    ignore_patterns: List[str] = field(default_factory=lambda: ['*.tmp', '.*', '*~'])
    hot_reload_enabled: bool = False
    hot_reload_command: Optional[str] = None
    safety: Optional[SafetyConfig] = field(default_factory=SafetyConfig)


class RateLimiter:
    """
    Sliding window rate limiter.

    Tracks processing events in a sliding time window to enforce rate limits.
    """

    def __init__(self, max_per_minute: int):
        """
        Initialize rate limiter.

        Args:
            max_per_minute: Maximum events allowed per minute
        """
        self.max_per_minute = max_per_minute
        self._events: deque = deque()
        self._lock = threading.Lock()

    def is_allowed(self) -> bool:
        """
        Check if an event is allowed under the rate limit.

        Returns:
            True if event is within rate limit
        """
        current_time = time.time()

        with self._lock:
            # Remove events older than 60 seconds
            while self._events and current_time - self._events[0] > 60.0:
                self._events.popleft()

            # Check if we're at the limit
            if len(self._events) >= self.max_per_minute:
                return False

            # Record this event
            self._events.append(current_time)
            return True

    def get_current_rate(self) -> int:
        """Get current events per minute."""
        current_time = time.time()
        with self._lock:
            # Remove old events
            while self._events and current_time - self._events[0] > 60.0:
                self._events.popleft()
            return len(self._events)


class CircuitBreaker:
    """
    Circuit breaker pattern for error handling.

    Tracks consecutive errors and opens circuit (pauses processing)
    when error threshold is reached.
    """

    def __init__(self, max_errors: int, cooldown_seconds: float):
        """
        Initialize circuit breaker.

        Args:
            max_errors: Maximum consecutive errors before opening
            cooldown_seconds: Cooldown period after opening
        """
        self.max_errors = max_errors
        self.cooldown_seconds = cooldown_seconds
        self._error_count = 0
        self._opened_at: Optional[float] = None
        self._lock = threading.Lock()

    def record_success(self):
        """Record a successful operation."""
        with self._lock:
            self._error_count = 0
            self._opened_at = None

    def record_error(self) -> bool:
        """
        Record an error.

        Returns:
            True if circuit should open (pause processing)
        """
        with self._lock:
            self._error_count += 1
            if self._error_count >= self.max_errors:
                self._opened_at = time.time()
                return True
            return False

    def is_open(self) -> bool:
        """
        Check if circuit is open (processing paused).

        Returns:
            True if circuit is open
        """
        with self._lock:
            if self._opened_at is None:
                return False

            # Check if cooldown has passed
            if time.time() - self._opened_at >= self.cooldown_seconds:
                # Reset circuit
                self._error_count = 0
                self._opened_at = None
                return False

            return True

    def get_cooldown_remaining(self) -> float:
        """Get remaining cooldown time in seconds."""
        with self._lock:
            if self._opened_at is None:
                return 0.0
            remaining = self.cooldown_seconds - (time.time() - self._opened_at)
            return max(0.0, remaining)


class AssetWatcher(FileSystemEventHandler):
    """
    Watch for asset changes and trigger pipeline processing.

    Features:
    - Debouncing (wait for file write to complete)
    - Hash-based change detection (skip duplicate writes)
    - Selective processing (only changed files)
    - Hot reload hooks (optional emulator reload)

    Usage:
        >>> watcher = AssetWatcher(config)
        >>> watcher.on_change = lambda event: process_asset(event.path)
        >>> watcher.start()
    """

    def __init__(self, config: WatchConfig):
        """
        Initialize asset watcher.

        Args:
            config: Watch configuration
        """
        super().__init__()
        self.config = config

        # Callbacks
        self.on_change: Optional[Callable[[FileChangeEvent], None]] = None
        self.on_batch_complete: Optional[Callable[[List[FileChangeEvent]], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None

        # Internal state
        self._observer: Optional[Observer] = None
        self._pending: Dict[str, float] = {}  # path -> timestamp
        self._file_hashes: Dict[str, str] = {}  # path -> hash
        self._lock = threading.Lock()
        self._debounce_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Safety features
        self._rate_limiter: Optional[RateLimiter] = None
        self._circuit_breaker: Optional[CircuitBreaker] = None
        if config.safety:
            self._rate_limiter = RateLimiter(config.safety.max_changes_per_minute)
            self._circuit_breaker = CircuitBreaker(
                config.safety.circuit_breaker_errors,
                config.safety.circuit_breaker_cooldown
            )

        # Statistics
        self.changes_detected = 0
        self.changes_processed = 0
        self.changes_skipped = 0
        self.changes_rate_limited = 0
        self.changes_too_large = 0
        self.changes_timed_out = 0
        self.circuit_breaker_trips = 0

    def start(self):
        """
        Start watching for file changes.

        Starts background threads for file monitoring and debouncing.
        """
        if self._observer is not None:
            raise RuntimeError("Watcher already started")

        print(f"Starting asset watcher...")
        print(f"  Watching: {', '.join(self.config.watch_dirs)}")
        print(f"  Extensions: {', '.join(self.config.extensions)}")
        print(f"  Debounce: {self.config.debounce_seconds}s")

        if self.config.safety:
            print(f"\n  Safety Limits:")
            print(f"    Max file size: {self.config.safety.max_file_size_mb}MB")
            print(f"    Rate limit: {self.config.safety.max_changes_per_minute}/min")
            print(f"    Queue depth: {self.config.safety.max_queue_depth}")
            print(f"    Processing timeout: {self.config.safety.max_processing_time_seconds}s")
            print(f"    Circuit breaker: {self.config.safety.circuit_breaker_errors} errors / {self.config.safety.circuit_breaker_cooldown}s cooldown")

        # Create observer
        self._observer = Observer()

        # Schedule watching for each directory
        for watch_dir in self.config.watch_dirs:
            path = Path(watch_dir)
            if not path.exists():
                print(f"  Warning: Directory does not exist: {watch_dir}")
                continue

            self._observer.schedule(
                self,
                str(path),
                recursive=self.config.recursive
            )
            print(f"  Scheduled: {watch_dir}")

        # Start observer
        self._observer.start()

        # Start debounce thread
        self._stop_event.clear()
        self._debounce_thread = threading.Thread(target=self._debounce_loop, daemon=True)
        self._debounce_thread.start()

        print("✓ Watcher started. Press Ctrl+C to stop.")

    def stop(self):
        """Stop watching for file changes."""
        if self._observer is None:
            return

        print("\nStopping asset watcher...")

        # Stop debounce thread
        self._stop_event.set()
        if self._debounce_thread:
            self._debounce_thread.join(timeout=2.0)

        # Stop observer
        self._observer.stop()
        self._observer.join(timeout=2.0)
        self._observer = None

        print("✓ Watcher stopped.")
        self._print_statistics()

    def on_any_event(self, event: FileSystemEvent):
        """Handle any file system event."""
        # Skip directories
        if event.is_directory:
            return

        # Get path
        path = Path(event.src_path)

        # Check extension
        if path.suffix not in self.config.extensions:
            return

        # Check ignore patterns
        if self._should_ignore(path):
            return

        # Determine change type
        if event.event_type == 'created':
            change_type = ChangeType.CREATED
        elif event.event_type == 'modified':
            change_type = ChangeType.MODIFIED
        elif event.event_type == 'deleted':
            change_type = ChangeType.DELETED
        elif event.event_type == 'moved':
            change_type = ChangeType.MOVED
            path = Path(event.dest_path)
        else:
            return

        # Check queue depth limit
        with self._lock:
            if self.config.safety and len(self._pending) >= self.config.safety.max_queue_depth:
                # Queue is full, drop this change
                return

            self._pending[str(path)] = time.time()
            self.changes_detected += 1

    def _should_ignore(self, path: Path) -> bool:
        """Check if path matches ignore patterns."""
        from fnmatch import fnmatch

        path_str = str(path)
        for pattern in self.config.ignore_patterns:
            if fnmatch(path.name, pattern) or fnmatch(path_str, pattern):
                return True
        return False

    def _debounce_loop(self):
        """Background thread that processes pending changes after debounce."""
        batch: List[FileChangeEvent] = []

        while not self._stop_event.is_set():
            time.sleep(0.1)  # Check every 100ms

            # Check circuit breaker
            if self._circuit_breaker and self._circuit_breaker.is_open():
                remaining = self._circuit_breaker.get_cooldown_remaining()
                if remaining > 0:
                    # Still in cooldown
                    continue
                else:
                    # Cooldown finished, circuit closed
                    print(f"\n✓ Circuit breaker reset after cooldown")

            current_time = time.time()
            to_process: List[str] = []

            # Find files ready to process (past debounce time)
            with self._lock:
                for file_path, timestamp in list(self._pending.items()):
                    if current_time - timestamp >= self.config.debounce_seconds:
                        to_process.append(file_path)
                        del self._pending[file_path]

            # Process each file
            for file_path in to_process:
                # Rate limiting check
                if self._rate_limiter and not self._rate_limiter.is_allowed():
                    self.changes_rate_limited += 1
                    # Put back in pending queue for later
                    with self._lock:
                        self._pending[file_path] = time.time()
                    continue

                event = self._create_change_event(Path(file_path))

                if event is None:
                    continue

                # Check if file actually changed (hash comparison)
                if self._is_duplicate_change(event):
                    self.changes_skipped += 1
                    continue

                # File size check
                if not self._check_file_size(event.path):
                    self.changes_too_large += 1
                    print(f"⚠ Skipped (too large): {event.path.name}")
                    continue

                self.changes_processed += 1
                batch.append(event)

                # Call change callback with timeout
                if self.on_change:
                    success = self._process_with_timeout(event)

                    # Update circuit breaker
                    if self._circuit_breaker:
                        if success:
                            self._circuit_breaker.record_success()
                        else:
                            should_open = self._circuit_breaker.record_error()
                            if should_open:
                                self.circuit_breaker_trips += 1
                                print(f"\n⚠ Circuit breaker opened after {self._circuit_breaker.max_errors} errors")
                                print(f"   Pausing for {self._circuit_breaker.cooldown_seconds}s...")
                                break  # Stop processing this batch

            # Call batch callback if we processed anything
            if batch and self.on_batch_complete:
                try:
                    self.on_batch_complete(batch.copy())
                except Exception as e:
                    if self.on_error:
                        self.on_error(e)
                    else:
                        print(f"Error in batch callback: {e}")
                batch.clear()

    def _create_change_event(self, path: Path) -> Optional[FileChangeEvent]:
        """Create change event for path."""
        # Check if file exists
        if not path.exists():
            return FileChangeEvent(
                path=path,
                change_type=ChangeType.DELETED,
                timestamp=time.time(),
                hash=None
            )

        # Calculate hash
        try:
            file_hash = self._hash_file(path)
        except Exception as e:
            print(f"Warning: Could not hash {path}: {e}")
            return None

        # Determine change type (created vs modified)
        if str(path) in self._file_hashes:
            change_type = ChangeType.MODIFIED
        else:
            change_type = ChangeType.CREATED

        return FileChangeEvent(
            path=path,
            change_type=change_type,
            timestamp=time.time(),
            hash=file_hash
        )

    def _hash_file(self, path: Path) -> str:
        """Calculate SHA256 hash of file."""
        sha256 = hashlib.sha256()
        with open(path, 'rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _is_duplicate_change(self, event: FileChangeEvent) -> bool:
        """Check if this is a duplicate change (same hash)."""
        path_str = str(event.path)

        # Check if hash changed
        if event.hash is None:
            # Deletion
            if path_str in self._file_hashes:
                del self._file_hashes[path_str]
            return False

        old_hash = self._file_hashes.get(path_str)
        if old_hash == event.hash:
            # Same content, skip
            return True

        # Update stored hash
        self._file_hashes[path_str] = event.hash
        return False

    def _check_file_size(self, path: Path) -> bool:
        """
        Check if file size is within limits.

        Args:
            path: Path to check

        Returns:
            True if file size is acceptable
        """
        if not self.config.safety:
            return True

        try:
            size_mb = path.stat().st_size / (1024 * 1024)
            return size_mb <= self.config.safety.max_file_size_mb
        except Exception:
            return False

    def _process_with_timeout(self, event: FileChangeEvent) -> bool:
        """
        Process event with timeout protection.

        Args:
            event: Event to process

        Returns:
            True if processing succeeded
        """
        if not self.config.safety or self.config.safety.max_processing_time_seconds <= 0:
            # No timeout, process normally
            try:
                self.on_change(event)
                return True
            except Exception as e:
                if self.on_error:
                    self.on_error(e)
                else:
                    print(f"Error processing {event.path}: {e}")

                # Apply error backoff
                if self.config.safety:
                    time.sleep(self.config.safety.error_backoff_seconds)
                return False

        # Process with timeout
        result = {'success': False, 'exception': None}

        def target():
            try:
                self.on_change(event)
                result['success'] = True
            except Exception as e:
                result['exception'] = e

        thread = threading.Thread(target=target, daemon=True)
        thread.start()
        thread.join(timeout=self.config.safety.max_processing_time_seconds)

        if thread.is_alive():
            # Timeout occurred
            self.changes_timed_out += 1
            print(f"⚠ Timeout processing {event.path.name} (>{self.config.safety.max_processing_time_seconds}s)")

            # Apply error backoff
            time.sleep(self.config.safety.error_backoff_seconds)
            return False

        if result['exception']:
            if self.on_error:
                self.on_error(result['exception'])
            else:
                print(f"Error processing {event.path}: {result['exception']}")

            # Apply error backoff
            time.sleep(self.config.safety.error_backoff_seconds)
            return False

        return result['success']

    def _print_statistics(self):
        """Print watcher statistics."""
        print("\nStatistics:")
        print(f"  Changes Detected: {self.changes_detected}")
        print(f"  Changes Processed: {self.changes_processed}")
        print(f"  Changes Skipped: {self.changes_skipped}")

        if self.config.safety:
            print(f"\n  Safety Stats:")
            print(f"    Rate Limited: {self.changes_rate_limited}")
            print(f"    Too Large: {self.changes_too_large}")
            print(f"    Timed Out: {self.changes_timed_out}")
            print(f"    Circuit Breaker Trips: {self.circuit_breaker_trips}")

            if self._rate_limiter:
                current_rate = self._rate_limiter.get_current_rate()
                print(f"    Current Rate: {current_rate}/min")

    def trigger_hot_reload(self):
        """
        Trigger hot reload to emulator/runtime.

        Executes hot_reload_command if configured.
        """
        if not self.config.hot_reload_enabled:
            return

        if self.config.hot_reload_command:
            import subprocess
            try:
                subprocess.run(
                    self.config.hot_reload_command,
                    shell=True,
                    check=True,
                    capture_output=True
                )
                print("✓ Hot reload triggered")
            except subprocess.CalledProcessError as e:
                print(f"✗ Hot reload failed: {e}")


# =============================================================================
# Pipeline Integration
# =============================================================================

class PipelineWatcher(AssetWatcher):
    """
    Asset watcher integrated with pipeline processing.

    Automatically processes changed assets through the pipeline.

    Usage:
        >>> from pipeline.watch import PipelineWatcher, WatchConfig
        >>> config = WatchConfig(watch_dirs=['assets/sprites'])
        >>> watcher = PipelineWatcher(config, processor_func=process_sprite)
        >>> watcher.start()
    """

    def __init__(self,
                 config: WatchConfig,
                 processor_func: Callable[[Path], None],
                 enable_hot_reload: bool = False):
        """
        Initialize pipeline watcher.

        Args:
            config: Watch configuration
            processor_func: Function to process changed files
            enable_hot_reload: Enable hot reload after processing
        """
        super().__init__(config)
        self.processor_func = processor_func
        self.enable_hot_reload = enable_hot_reload

        # Set up callbacks
        self.on_change = self._process_change
        if enable_hot_reload:
            self.on_batch_complete = self._on_batch_complete

    def _process_change(self, event: FileChangeEvent):
        """Process a file change through the pipeline."""
        if event.change_type == ChangeType.DELETED:
            print(f"Deleted: {event.path.name}")
            return

        print(f"\n{'='*60}")
        print(f"Processing: {event.path.name}")
        print(f"Change type: {event.change_type.value}")
        print(f"{'='*60}")

        try:
            start_time = time.time()
            self.processor_func(event.path)
            duration = time.time() - start_time
            print(f"✓ Processed in {duration:.2f}s")
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()

    def _on_batch_complete(self, events: List[FileChangeEvent]):
        """Trigger hot reload after batch processing."""
        if self.enable_hot_reload:
            print(f"\nBatch complete ({len(events)} files)")
            self.trigger_hot_reload()
