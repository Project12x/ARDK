"""
Tests for core/safeguards.py - Phase 0.9

Tests safeguard enforcement including:
- Cache (request/response/image caching)
- BudgetTracker (generation limits, cost limits)
- Validator (input/output validation)
- Exception types
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from PIL import Image

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.core.safeguards import (
    Cache,
    CacheEntry,
    BudgetTracker,
    BudgetState,
    Validator,
    Safeguards,
    SafeguardViolation,
    BudgetExhausted,
    ValidationFailed,
    DryRunActive,
    ConfirmationRequired,
)
from pipeline.core.config import SafeguardConfig


class TestExceptions:
    """Tests for exception hierarchy."""

    def test_safeguard_violation_is_exception(self):
        """SafeguardViolation should be an Exception."""
        assert issubclass(SafeguardViolation, Exception)

    def test_budget_exhausted_is_safeguard_violation(self):
        """BudgetExhausted should be a SafeguardViolation."""
        assert issubclass(BudgetExhausted, SafeguardViolation)

    def test_validation_failed_is_safeguard_violation(self):
        """ValidationFailed should be a SafeguardViolation."""
        assert issubclass(ValidationFailed, SafeguardViolation)

    def test_dry_run_active_is_safeguard_violation(self):
        """DryRunActive should be a SafeguardViolation."""
        assert issubclass(DryRunActive, SafeguardViolation)

    def test_confirmation_required_is_safeguard_violation(self):
        """ConfirmationRequired should be a SafeguardViolation."""
        assert issubclass(ConfirmationRequired, SafeguardViolation)

    def test_exception_with_message(self):
        """Exceptions should support custom messages."""
        msg = "Test error message"
        e = BudgetExhausted(msg)
        assert str(e) == msg


class TestCache:
    """Tests for Cache class."""

    @pytest.fixture
    def cache(self, temp_dir):
        """Create a Cache instance in temp directory."""
        cache_dir = Path(temp_dir) / ".ardk_cache"
        return Cache(str(cache_dir))

    def test_cache_creates_directories(self, cache):
        """Cache should create required subdirectories."""
        assert cache.cache_dir.exists()
        assert cache.requests_dir.exists()
        assert cache.responses_dir.exists()
        assert cache.images_dir.exists()

    def test_get_cache_key(self, cache):
        """Cache keys should be deterministic."""
        key1 = cache.get_cache_key("test prompt", 32, 32)
        key2 = cache.get_cache_key("test prompt", 32, 32)
        key3 = cache.get_cache_key("different prompt", 32, 32)

        assert key1 == key2  # Same input = same key
        assert key1 != key3  # Different input = different key
        assert len(key1) == 12  # MD5 truncated to 12 chars

    def test_save_and_load_request(self, cache):
        """Should save and load request parameters."""
        key = "test_key_123"
        params = {"description": "test", "width": 32}

        cache.save_request(key, params)

        # Check file exists
        request_file = cache.requests_dir / f"{key}.json"
        assert request_file.exists()

        # Verify content
        with open(request_file) as f:
            data = json.load(f)
            assert data["params"] == params

    def test_save_and_load_response(self, cache):
        """Should save and load API responses."""
        key = "test_response_key"
        response = {"images": [{"base64": "abc123"}], "usage": {"usd": 0.05}}

        cache.save_response(key, response)
        loaded = cache.load_response(key)

        assert loaded == response

    def test_load_missing_response(self, cache):
        """Loading missing response should return None."""
        result = cache.load_response("nonexistent_key")
        assert result is None

    def test_has_cached_response(self, cache):
        """has_cached_response should check file existence."""
        key = "check_key"

        assert not cache.has_cached_response(key)

        cache.save_response(key, {"test": True})

        assert cache.has_cached_response(key)

    def test_save_and_load_images(self, cache, test_image_32x32):
        """Should save and load images."""
        key = "image_cache_key"
        images = {"front": test_image_32x32, "back": test_image_32x32}

        cache.save_images(key, images)
        loaded = cache.load_images(key)

        assert loaded is not None
        assert "front" in loaded
        assert "back" in loaded
        assert loaded["front"].size == (32, 32)

    def test_load_missing_images(self, cache):
        """Loading missing images should return None."""
        result = cache.load_images("nonexistent_images")
        assert result is None


class TestBudgetTracker:
    """Tests for BudgetTracker class."""

    @pytest.fixture
    def tracker(self, temp_dir):
        """Create a BudgetTracker with temp file."""
        budget_file = Path(temp_dir) / ".ardk_budget.json"
        return BudgetTracker(
            max_generations=5,
            max_cost=0.50,
            persist=True,
            budget_file=str(budget_file)
        )

    @pytest.fixture
    def no_persist_tracker(self):
        """Create a non-persisting BudgetTracker."""
        return BudgetTracker(
            max_generations=3,
            max_cost=0.25,
            persist=False
        )

    def test_initial_state(self, tracker):
        """Initial state should have zero usage."""
        assert tracker.state.generations_used == 0
        assert tracker.state.cost_used == 0.0
        assert tracker.can_generate()

    def test_record_generation(self, tracker):
        """Recording generation should update state."""
        tracker.record_generation(cost=0.10)

        assert tracker.state.generations_used == 1
        assert tracker.state.cost_used == 0.10

    def test_can_generate_within_budget(self, tracker):
        """Should return True when within budget."""
        tracker.record_generation(cost=0.10)
        assert tracker.can_generate()

    def test_can_generate_exhausted_generations(self, no_persist_tracker):
        """Should return False when generations exhausted."""
        for _ in range(3):
            no_persist_tracker.record_generation(cost=0.01)

        assert not no_persist_tracker.can_generate()

    def test_can_generate_exhausted_cost(self, no_persist_tracker):
        """Should return False when cost exhausted."""
        no_persist_tracker.record_generation(cost=0.30)

        assert not no_persist_tracker.can_generate()

    def test_check_budget_raises_when_exhausted(self, no_persist_tracker):
        """check_budget should raise BudgetExhausted."""
        for _ in range(3):
            no_persist_tracker.record_generation(cost=0.01)

        with pytest.raises(BudgetExhausted):
            no_persist_tracker.check_budget()

    def test_get_remaining(self, tracker):
        """get_remaining should return correct values."""
        tracker.record_generation(cost=0.10)

        remaining = tracker.get_remaining()

        assert remaining["generations"] == 4
        assert remaining["cost"] == pytest.approx(0.40)

    def test_reset(self, tracker):
        """reset should clear budget state."""
        tracker.record_generation(cost=0.10)
        tracker.reset()

        assert tracker.state.generations_used == 0
        assert tracker.state.cost_used == 0.0

    def test_persistence(self, temp_dir):
        """Budget should persist across instances."""
        budget_file = Path(temp_dir) / ".ardk_budget_persist.json"

        # First tracker
        tracker1 = BudgetTracker(
            max_generations=10,
            max_cost=1.00,
            persist=True,
            budget_file=str(budget_file)
        )
        tracker1.record_generation(cost=0.15)

        # Second tracker loads same file
        tracker2 = BudgetTracker(
            max_generations=10,
            max_cost=1.00,
            persist=True,
            budget_file=str(budget_file)
        )

        assert tracker2.state.generations_used == 1
        assert tracker2.state.cost_used == pytest.approx(0.15)


class TestValidator:
    """Tests for Validator class."""

    def test_validate_input_file_exists(self, sample_png_file):
        """Valid file should return no errors."""
        errors = Validator.validate_input_file(sample_png_file)
        assert len(errors) == 0

    def test_validate_input_file_not_exists(self):
        """Non-existent file should return error."""
        errors = Validator.validate_input_file("/nonexistent/file.png")
        assert len(errors) == 1
        assert "not found" in errors[0].lower()

    def test_validate_input_file_invalid_type(self, temp_dir):
        """Invalid file type should return error."""
        txt_file = Path(temp_dir) / "test.txt"
        txt_file.write_text("hello")

        errors = Validator.validate_input_file(str(txt_file))
        assert len(errors) == 1
        assert "unsupported" in errors[0].lower()

    def test_validate_input_file_too_large(self, temp_dir):
        """Image over 4096px should return error."""
        large_img = Image.new('RGB', (5000, 100))
        path = Path(temp_dir) / "large.png"
        large_img.save(path)

        errors = Validator.validate_input_file(str(path))
        assert len(errors) == 1
        assert "too large" in errors[0].lower()

    def test_validate_input_file_too_small(self, temp_dir):
        """Image under 8px should return error."""
        small_img = Image.new('RGB', (4, 4))
        path = Path(temp_dir) / "tiny.png"
        small_img.save(path)

        errors = Validator.validate_input_file(str(path))
        assert len(errors) == 1
        assert "too small" in errors[0].lower()

    def test_validate_output_dir_creates(self, temp_dir):
        """Should create output directory if needed."""
        new_dir = Path(temp_dir) / "new_output" / "subdir"

        errors = Validator.validate_output_dir(str(new_dir))

        assert len(errors) == 0
        assert new_dir.exists()

    def test_validate_prompt_valid(self):
        """Valid prompt should return no errors."""
        errors = Validator.validate_prompt("pixel art warrior with sword")
        assert len(errors) == 0

    def test_validate_prompt_too_short(self):
        """Prompt under 3 chars should return error."""
        errors = Validator.validate_prompt("ab")
        assert len(errors) == 1
        assert "too short" in errors[0].lower()

    def test_validate_prompt_too_long(self):
        """Prompt over 2000 chars should return error."""
        long_prompt = "a" * 2001
        errors = Validator.validate_prompt(long_prompt)
        assert len(errors) == 1
        assert "too long" in errors[0].lower()

    def test_validate_prompt_empty(self):
        """Empty prompt should return error."""
        errors = Validator.validate_prompt("")
        assert len(errors) == 1


class TestSafeguards:
    """Tests for main Safeguards class."""

    @pytest.fixture
    def safeguards(self, temp_dir):
        """Create Safeguards with temp directories."""
        config = SafeguardConfig(
            dry_run=True,
            require_confirmation=True,
            max_generations_per_run=5,
            max_cost_per_run=0.50,
            cache_dir=str(Path(temp_dir) / ".ardk_cache")
        )
        return Safeguards(config)

    def test_has_cache(self, safeguards):
        """Safeguards should have cache component."""
        assert hasattr(safeguards, 'cache')
        assert isinstance(safeguards.cache, Cache)

    def test_has_budget(self, safeguards):
        """Safeguards should have budget component."""
        assert hasattr(safeguards, 'budget')
        assert isinstance(safeguards.budget, BudgetTracker)

    def test_dry_run_default_true(self, safeguards):
        """Dry run should be enabled by default."""
        assert safeguards.config.dry_run is True

    def test_get_status(self, safeguards):
        """get_status should return safeguard state."""
        status = safeguards.get_status()

        assert "dry_run" in status
        assert "generations_remaining" in status
        assert "cost_remaining" in status
        assert status["dry_run"] is True
