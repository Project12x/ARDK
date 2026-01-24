"""
Test suite for AssetWatcher.

Tests file watching, debouncing, hash-based change detection, and hot reload hooks.
"""

import pytest
import time
import tempfile
import shutil
from pathlib import Path
from PIL import Image

from pipeline.watch import (
    AssetWatcher, WatchConfig, SafetyConfig, FileChangeEvent,
    ChangeType, PipelineWatcher, RateLimiter, CircuitBreaker
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def test_image():
    """Create a test image."""
    img = Image.new('RGBA', (32, 32), (255, 0, 0, 255))
    return img


@pytest.fixture
def watch_config(temp_dir):
    """Create basic watch configuration."""
    return WatchConfig(
        watch_dirs=[str(temp_dir)],
        extensions=['.png', '.txt'],
        debounce_seconds=0.5,
        recursive=True,
    )


# =============================================================================
# Configuration Tests
# =============================================================================

def test_watch_config_defaults():
    """Test WatchConfig default values."""
    config = WatchConfig(watch_dirs=['assets/'])

    assert config.watch_dirs == ['assets/']
    assert '.png' in config.extensions
    assert config.debounce_seconds == 1.0
    assert config.recursive is True
    assert '*.tmp' in config.ignore_patterns
    assert config.hot_reload_enabled is False


def test_watch_config_custom():
    """Test WatchConfig with custom values."""
    config = WatchConfig(
        watch_dirs=['dir1', 'dir2'],
        extensions=['.jpg'],
        debounce_seconds=2.0,
        recursive=False,
        ignore_patterns=['*.bak'],
        hot_reload_enabled=True,
        hot_reload_command='reload.sh'
    )

    assert config.watch_dirs == ['dir1', 'dir2']
    assert config.extensions == ['.jpg']
    assert config.debounce_seconds == 2.0
    assert config.recursive is False
    assert config.ignore_patterns == ['*.bak']
    assert config.hot_reload_enabled is True
    assert config.hot_reload_command == 'reload.sh'


# =============================================================================
# FileChangeEvent Tests
# =============================================================================

def test_file_change_event_created(temp_dir):
    """Test FileChangeEvent for created file."""
    path = temp_dir / 'test.png'
    event = FileChangeEvent(
        path=path,
        change_type=ChangeType.CREATED,
        timestamp=time.time(),
        hash='abc123'
    )

    assert event.path == path
    assert event.change_type == ChangeType.CREATED
    assert event.hash == 'abc123'


def test_file_change_event_to_dict(temp_dir):
    """Test FileChangeEvent serialization."""
    path = temp_dir / 'test.png'
    event = FileChangeEvent(
        path=path,
        change_type=ChangeType.MODIFIED,
        timestamp=1234567890.0,
        hash='def456'
    )

    data = event.to_dict()

    assert 'path' in data
    assert 'change_type' in data
    assert 'timestamp' in data
    assert 'hash' in data
    assert data['change_type'] == 'modified'
    assert data['timestamp'] == 1234567890.0


# =============================================================================
# AssetWatcher Tests
# =============================================================================

def test_asset_watcher_init(watch_config):
    """Test AssetWatcher initialization."""
    watcher = AssetWatcher(watch_config)

    assert watcher.config == watch_config
    assert watcher.on_change is None
    assert watcher.changes_detected == 0
    assert watcher.changes_processed == 0


def test_asset_watcher_should_ignore(watch_config):
    """Test ignore pattern matching."""
    watcher = AssetWatcher(watch_config)

    # Should ignore
    assert watcher._should_ignore(Path('.hidden')) is True
    assert watcher._should_ignore(Path('file.tmp')) is True
    assert watcher._should_ignore(Path('file~')) is True

    # Should not ignore
    assert watcher._should_ignore(Path('sprite.png')) is False
    assert watcher._should_ignore(Path('data.txt')) is False


def test_asset_watcher_hash_file(watch_config, temp_dir, test_image):
    """Test file hashing."""
    watcher = AssetWatcher(watch_config)

    # Create test file
    test_file = temp_dir / 'test.png'
    test_image.save(test_file)

    # Calculate hash
    hash1 = watcher._hash_file(test_file)
    assert isinstance(hash1, str)
    assert len(hash1) == 64  # SHA256 hex digest

    # Same file should have same hash
    hash2 = watcher._hash_file(test_file)
    assert hash1 == hash2

    # Modified file should have different hash
    test_image2 = Image.new('RGBA', (32, 32), (0, 255, 0, 255))
    test_image2.save(test_file)
    hash3 = watcher._hash_file(test_file)
    assert hash1 != hash3


def test_asset_watcher_duplicate_detection(watch_config, temp_dir, test_image):
    """Test duplicate change detection via hash comparison."""
    watcher = AssetWatcher(watch_config)

    # Create test file
    test_file = temp_dir / 'test.png'
    test_image.save(test_file)

    # First change - not a duplicate
    event1 = watcher._create_change_event(test_file)
    assert watcher._is_duplicate_change(event1) is False

    # Same file again - is a duplicate
    event2 = watcher._create_change_event(test_file)
    assert watcher._is_duplicate_change(event2) is True

    # Modified file - not a duplicate
    test_image2 = Image.new('RGBA', (32, 32), (0, 255, 0, 255))
    test_image2.save(test_file)
    event3 = watcher._create_change_event(test_file)
    assert watcher._is_duplicate_change(event3) is False


def test_asset_watcher_start_stop(watch_config):
    """Test starting and stopping watcher."""
    watcher = AssetWatcher(watch_config)

    # Should not be running initially
    assert watcher._observer is None

    # Start watcher
    watcher.start()
    assert watcher._observer is not None

    # Stop watcher
    watcher.stop()
    assert watcher._observer is None


def test_asset_watcher_callback(watch_config, temp_dir, test_image):
    """Test on_change callback is called."""
    watcher = AssetWatcher(watch_config)

    changes_received = []

    def on_change(event: FileChangeEvent):
        changes_received.append(event)

    watcher.on_change = on_change

    # Start watcher
    watcher.start()

    try:
        # Create a file
        test_file = temp_dir / 'test.png'
        test_image.save(test_file)

        # Wait for debounce + processing
        time.sleep(watch_config.debounce_seconds + 0.5)

        # Should have received change event
        assert len(changes_received) > 0
        event = changes_received[0]
        assert event.path.name == 'test.png'
        assert event.change_type in (ChangeType.CREATED, ChangeType.MODIFIED)

    finally:
        watcher.stop()


# =============================================================================
# PipelineWatcher Tests
# =============================================================================

def test_pipeline_watcher_init(watch_config):
    """Test PipelineWatcher initialization."""
    processed = []

    def processor(path: Path):
        processed.append(path)

    watcher = PipelineWatcher(watch_config, processor_func=processor)

    assert watcher.processor_func == processor
    assert watcher.on_change is not None


def test_pipeline_watcher_processes_changes(watch_config, temp_dir, test_image):
    """Test PipelineWatcher processes file changes."""
    processed = []

    def processor(path: Path):
        processed.append(path)

    watcher = PipelineWatcher(watch_config, processor_func=processor)
    watcher.start()

    try:
        # Create a file
        test_file = temp_dir / 'test.png'
        test_image.save(test_file)

        # Wait for debounce + processing
        time.sleep(watch_config.debounce_seconds + 0.5)

        # Should have processed the file
        assert len(processed) > 0
        assert processed[0].name == 'test.png'

    finally:
        watcher.stop()


def test_pipeline_watcher_hot_reload_disabled(watch_config):
    """Test PipelineWatcher with hot reload disabled."""
    def processor(path: Path):
        pass

    watcher = PipelineWatcher(watch_config, processor_func=processor, enable_hot_reload=False)

    assert watcher.on_batch_complete is None


def test_pipeline_watcher_hot_reload_enabled(watch_config):
    """Test PipelineWatcher with hot reload enabled."""
    def processor(path: Path):
        pass

    watcher = PipelineWatcher(watch_config, processor_func=processor, enable_hot_reload=True)

    assert watcher.on_batch_complete is not None


# =============================================================================
# Integration Tests
# =============================================================================

def test_watcher_multiple_changes(watch_config, temp_dir, test_image):
    """Test watcher handles multiple file changes."""
    watcher = AssetWatcher(watch_config)
    changes_received = []

    def on_change(event: FileChangeEvent):
        changes_received.append(event)

    watcher.on_change = on_change
    watcher.start()

    try:
        # Create multiple files
        for i in range(3):
            test_file = temp_dir / f'test_{i}.png'
            test_image.save(test_file)

        # Wait for debounce + processing
        time.sleep(watch_config.debounce_seconds + 1.0)

        # Should have received all changes
        assert len(changes_received) == 3

    finally:
        watcher.stop()


def test_watcher_ignores_unsupported_extensions(watch_config, temp_dir):
    """Test watcher ignores files with unsupported extensions."""
    watcher = AssetWatcher(watch_config)
    changes_received = []

    def on_change(event: FileChangeEvent):
        changes_received.append(event)

    watcher.on_change = on_change
    watcher.start()

    try:
        # Create file with unsupported extension
        test_file = temp_dir / 'test.jpg'
        test_file.write_text('test')

        # Wait
        time.sleep(watch_config.debounce_seconds + 0.5)

        # Should not have received any changes
        assert len(changes_received) == 0

    finally:
        watcher.stop()


def test_watcher_statistics(watch_config, temp_dir, test_image):
    """Test watcher tracks statistics."""
    watcher = AssetWatcher(watch_config)

    def on_change(event: FileChangeEvent):
        pass

    watcher.on_change = on_change
    watcher.start()

    try:
        # Create file
        test_file = temp_dir / 'test.png'
        test_image.save(test_file)

        # Wait
        time.sleep(watch_config.debounce_seconds + 0.5)

        # Should have incremented statistics
        assert watcher.changes_detected > 0
        assert watcher.changes_processed > 0

    finally:
        watcher.stop()


# =============================================================================
# Safety Features Tests
# =============================================================================

def test_safety_config_defaults():
    """Test SafetyConfig default values."""
    config = SafetyConfig()

    assert config.max_file_size_mb == 50.0
    assert config.max_changes_per_minute == 60
    assert config.max_queue_depth == 100
    assert config.max_processing_time_seconds == 30.0
    assert config.circuit_breaker_errors == 5
    assert config.circuit_breaker_cooldown == 60.0
    assert config.error_backoff_seconds == 5.0


def test_safety_config_custom():
    """Test SafetyConfig with custom values."""
    config = SafetyConfig(
        max_file_size_mb=10.0,
        max_changes_per_minute=30,
        max_queue_depth=50,
        max_processing_time_seconds=15.0,
        circuit_breaker_errors=3,
        circuit_breaker_cooldown=30.0,
        error_backoff_seconds=2.0
    )

    assert config.max_file_size_mb == 10.0
    assert config.max_changes_per_minute == 30
    assert config.max_queue_depth == 50
    assert config.max_processing_time_seconds == 15.0
    assert config.circuit_breaker_errors == 3
    assert config.circuit_breaker_cooldown == 30.0
    assert config.error_backoff_seconds == 2.0


def test_watch_config_with_safety():
    """Test WatchConfig with SafetyConfig."""
    safety = SafetyConfig(max_file_size_mb=10.0)
    config = WatchConfig(
        watch_dirs=['assets/'],
        safety=safety
    )

    assert config.safety is not None
    assert config.safety.max_file_size_mb == 10.0


def test_watch_config_safety_defaults():
    """Test WatchConfig creates default SafetyConfig."""
    config = WatchConfig(watch_dirs=['assets/'])

    assert config.safety is not None
    assert config.safety.max_file_size_mb == 50.0


def test_watch_config_no_safety():
    """Test WatchConfig without safety limits."""
    config = WatchConfig(watch_dirs=['assets/'], safety=None)

    assert config.safety is None


def test_rate_limiter_allows_within_limit():
    """Test RateLimiter allows events within limit."""
    limiter = RateLimiter(max_per_minute=5)

    # Should allow first 5 events
    for i in range(5):
        assert limiter.is_allowed() is True

    # Should reject 6th event
    assert limiter.is_allowed() is False


def test_rate_limiter_sliding_window():
    """Test RateLimiter uses sliding window."""
    limiter = RateLimiter(max_per_minute=2)

    # Allow 2 events
    assert limiter.is_allowed() is True
    assert limiter.is_allowed() is True

    # Get current rate
    assert limiter.get_current_rate() == 2

    # Should reject 3rd event
    assert limiter.is_allowed() is False


def test_circuit_breaker_opens_after_errors():
    """Test CircuitBreaker opens after max errors."""
    breaker = CircuitBreaker(max_errors=3, cooldown_seconds=1.0)

    # Should not be open initially
    assert breaker.is_open() is False

    # Record errors
    assert breaker.record_error() is False  # Error 1
    assert breaker.record_error() is False  # Error 2
    assert breaker.record_error() is True   # Error 3 - should open

    # Should be open now
    assert breaker.is_open() is True


def test_circuit_breaker_resets_on_success():
    """Test CircuitBreaker resets on success."""
    breaker = CircuitBreaker(max_errors=3, cooldown_seconds=1.0)

    # Record errors
    breaker.record_error()
    breaker.record_error()

    # Record success
    breaker.record_success()

    # Should reset error count
    assert breaker.is_open() is False
    breaker.record_error()
    breaker.record_error()
    assert breaker.record_error() is True  # Should take 3 more errors


def test_circuit_breaker_cooldown():
    """Test CircuitBreaker cooldown period."""
    breaker = CircuitBreaker(max_errors=2, cooldown_seconds=0.5)

    # Open circuit
    breaker.record_error()
    breaker.record_error()

    assert breaker.is_open() is True

    # Wait for cooldown
    time.sleep(0.6)

    # Should be closed after cooldown
    assert breaker.is_open() is False


def test_circuit_breaker_cooldown_remaining():
    """Test CircuitBreaker reports remaining cooldown time."""
    breaker = CircuitBreaker(max_errors=1, cooldown_seconds=2.0)

    # Not open yet
    assert breaker.get_cooldown_remaining() == 0.0

    # Open circuit
    breaker.record_error()
    assert breaker.is_open() is True

    # Should have cooldown remaining
    remaining = breaker.get_cooldown_remaining()
    assert 1.5 < remaining <= 2.0


def test_watcher_file_size_limit(temp_dir):
    """Test watcher skips files exceeding size limit."""
    safety = SafetyConfig(max_file_size_mb=0.001)  # 1KB limit
    config = WatchConfig(
        watch_dirs=[str(temp_dir)],
        extensions=['.txt'],
        debounce_seconds=0.5,
        safety=safety
    )
    watcher = AssetWatcher(config)

    changes_received = []

    def on_change(event: FileChangeEvent):
        changes_received.append(event)

    watcher.on_change = on_change
    watcher.start()

    try:
        # Create large file (>1KB)
        test_file = temp_dir / 'large.txt'
        test_file.write_text('x' * 2000)

        # Wait
        time.sleep(config.debounce_seconds + 0.5)

        # Should not have processed due to size limit
        assert len(changes_received) == 0
        assert watcher.changes_too_large > 0

    finally:
        watcher.stop()


def test_watcher_safety_statistics(temp_dir):
    """Test watcher tracks safety statistics."""
    safety = SafetyConfig(max_file_size_mb=0.001)
    config = WatchConfig(
        watch_dirs=[str(temp_dir)],
        extensions=['.txt'],
        debounce_seconds=0.5,
        safety=safety
    )
    watcher = AssetWatcher(config)
    watcher.on_change = lambda e: None
    watcher.start()

    try:
        # Create large file
        test_file = temp_dir / 'large.txt'
        test_file.write_text('x' * 2000)

        # Wait
        time.sleep(config.debounce_seconds + 0.5)

        # Check safety statistics exist
        assert hasattr(watcher, 'changes_rate_limited')
        assert hasattr(watcher, 'changes_too_large')
        assert hasattr(watcher, 'changes_timed_out')
        assert hasattr(watcher, 'circuit_breaker_trips')
        assert watcher.changes_too_large > 0

    finally:
        watcher.stop()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
