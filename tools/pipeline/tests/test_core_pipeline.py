"""
Tests for core/pipeline.py - Phase 0.9

Tests the main Pipeline orchestrator including:
- Input type detection
- Configuration handling
- Safeguard integration
- Event emitting
"""

import pytest
import tempfile
from pathlib import Path
from PIL import Image

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.core import (
    Pipeline,
    PipelineConfig,
    SafeguardConfig,
    EventEmitter,
    EventType,
    DryRunActive,
    ValidationFailed,
)
from pipeline.core.config import InputType


class TestPipelineConfig:
    """Tests for PipelineConfig."""

    def test_default_config(self):
        """Default config should have sane defaults."""
        config = PipelineConfig()

        assert config.platform == "genesis"
        assert config.safeguards.dry_run is True
        assert config.safeguards.max_generations_per_run == 5
        assert config.safeguards.max_cost_per_run == 0.50

    def test_custom_platform(self):
        """Custom platform should be stored."""
        config = PipelineConfig(platform="nes")
        assert config.platform == "nes"

    def test_custom_safeguards(self):
        """Custom safeguard config should be used."""
        safeguards = SafeguardConfig(
            dry_run=False,
            max_generations_per_run=10,
            max_cost_per_run=2.00
        )
        config = PipelineConfig(safeguards=safeguards)

        assert config.safeguards.dry_run is False
        assert config.safeguards.max_generations_per_run == 10
        assert config.safeguards.max_cost_per_run == 2.00


class TestPipelineInit:
    """Tests for Pipeline initialization."""

    @pytest.fixture
    def config(self, temp_dir):
        """Create test config with temp cache."""
        return PipelineConfig(
            platform="genesis",
            safeguards=SafeguardConfig(
                dry_run=True,
                cache_dir=str(Path(temp_dir) / ".cache")
            )
        )

    def test_init_creates_safeguards(self, config):
        """Pipeline should create safeguards."""
        pipeline = Pipeline(config)
        assert pipeline.safeguards is not None

    def test_init_creates_event_emitter(self, config):
        """Pipeline should have event emitter."""
        pipeline = Pipeline(config)
        assert pipeline.events is not None

    def test_init_accepts_custom_emitter(self, config):
        """Pipeline should accept custom event emitter."""
        emitter = EventEmitter()
        pipeline = Pipeline(config, event_emitter=emitter)
        assert pipeline.events is emitter

    def test_stores_config(self, config):
        """Pipeline should store config."""
        pipeline = Pipeline(config)
        assert pipeline.config is config


class TestInputTypeDetection:
    """Tests for input type detection."""

    @pytest.fixture
    def pipeline(self, temp_dir):
        """Create pipeline for testing."""
        config = PipelineConfig(
            safeguards=SafeguardConfig(
                dry_run=True,
                cache_dir=str(Path(temp_dir) / ".cache")
            )
        )
        return Pipeline(config)

    def test_detect_png(self, pipeline, sample_png_file):
        """Should detect PNG files."""
        input_type = pipeline._detect_input_type(sample_png_file)
        assert input_type == InputType.PNG

    def test_detect_aseprite_ase(self, pipeline, temp_dir):
        """Should detect .ase files."""
        ase_file = Path(temp_dir) / "test.ase"
        ase_file.write_bytes(b"dummy")  # Create file

        input_type = pipeline._detect_input_type(str(ase_file))
        assert input_type == InputType.ASEPRITE

    def test_detect_aseprite_long(self, pipeline, temp_dir):
        """Should detect .aseprite files."""
        ase_file = Path(temp_dir) / "test.aseprite"
        ase_file.write_bytes(b"dummy")

        input_type = pipeline._detect_input_type(str(ase_file))
        assert input_type == InputType.ASEPRITE

    def test_detect_directory(self, pipeline, temp_dir):
        """Should detect directories."""
        input_type = pipeline._detect_input_type(temp_dir)
        assert input_type == InputType.DIRECTORY

    def test_detect_prompt(self, pipeline):
        """Should detect text prompts."""
        prompt = "pixel art warrior character with sword and shield"
        input_type = pipeline._detect_input_type(prompt)
        assert input_type == InputType.PROMPT

    def test_detect_unknown(self, pipeline, temp_dir):
        """Should return UNKNOWN for unknown files."""
        txt_file = Path(temp_dir) / "test.txt"
        txt_file.write_text("hello")

        input_type = pipeline._detect_input_type(str(txt_file))
        assert input_type == InputType.UNKNOWN


class TestSafeguardEnforcement:
    """Tests for safeguard enforcement."""

    @pytest.fixture
    def dry_run_pipeline(self, temp_dir):
        """Create pipeline with dry-run enabled."""
        config = PipelineConfig(
            safeguards=SafeguardConfig(
                dry_run=True,
                cache_dir=str(Path(temp_dir) / ".cache")
            )
        )
        return Pipeline(config)

    def test_dry_run_is_default(self, dry_run_pipeline):
        """Dry-run should be enabled by default."""
        assert dry_run_pipeline.safeguards.dry_run is True

    def test_confirm_method(self, temp_dir):
        """confirm() should update confirmation state."""
        config = PipelineConfig(
            safeguards=SafeguardConfig(
                dry_run=True,
                require_confirmation=True,
                cache_dir=str(Path(temp_dir) / ".cache")
            )
        )
        pipeline = Pipeline(config)

        assert not pipeline.safeguards._confirmed
        pipeline.confirm()
        assert pipeline.safeguards._confirmed


class TestEventEmitting:
    """Tests for event emission."""

    @pytest.fixture
    def event_capture(self):
        """Fixture to capture emitted events."""
        class EventCapture:
            def __init__(self):
                self.events = []

            def handler(self, event):
                self.events.append(event)

        return EventCapture()

    def test_emitter_on(self, temp_dir, event_capture):
        """Should register event handlers."""
        emitter = EventEmitter()
        emitter.on(EventType.PROGRESS, event_capture.handler)

        config = PipelineConfig(
            safeguards=SafeguardConfig(
                dry_run=True,
                cache_dir=str(Path(temp_dir) / ".cache")
            )
        )
        pipeline = Pipeline(config, event_emitter=emitter)

        # Emit progress event directly
        pipeline.events.emit_progress(50.0, "Test message", "test_stage")

        assert len(event_capture.events) == 1
        assert event_capture.events[0].percent == 50.0

    def test_emitter_on_all(self, temp_dir, event_capture):
        """on_all should receive all event types."""
        emitter = EventEmitter()
        emitter.on_all(event_capture.handler)

        config = PipelineConfig(
            safeguards=SafeguardConfig(
                dry_run=True,
                cache_dir=str(Path(temp_dir) / ".cache")
            )
        )
        pipeline = Pipeline(config, event_emitter=emitter)

        # Emit multiple event types
        pipeline.events.emit_progress(25.0, "Progress", "stage1")
        pipeline.events.emit_stage_start("test", 1, 3)

        assert len(event_capture.events) == 2


class TestPipelineGetStatus:
    """Tests for get_status method."""

    def test_get_status_returns_dict(self, temp_dir):
        """get_status should return dictionary."""
        config = PipelineConfig(
            platform="genesis",
            safeguards=SafeguardConfig(
                dry_run=True,
                cache_dir=str(Path(temp_dir) / ".cache")
            )
        )
        pipeline = Pipeline(config)

        status = pipeline.get_status()

        assert isinstance(status, dict)
        assert "platform" in status
        assert "safeguards" in status
        assert status["platform"] == "genesis"

    def test_get_status_includes_safeguards(self, temp_dir):
        """get_status should include safeguard info."""
        config = PipelineConfig(
            safeguards=SafeguardConfig(
                dry_run=True,
                max_generations_per_run=10,
                cache_dir=str(Path(temp_dir) / ".cache")
            )
        )
        pipeline = Pipeline(config)

        status = pipeline.get_status()
        sg = status["safeguards"]

        assert sg["dry_run"] is True
        assert sg["generations_remaining"] == 10


class TestInputValidation:
    """Tests for input validation."""

    @pytest.fixture
    def pipeline(self, temp_dir):
        """Create pipeline for testing."""
        config = PipelineConfig(
            safeguards=SafeguardConfig(
                dry_run=True,
                validate_inputs=True,
                cache_dir=str(Path(temp_dir) / ".cache")
            )
        )
        return Pipeline(config)

    def test_validate_nonexistent_file(self, pipeline, temp_dir):
        """Should raise ValidationFailed for missing file."""
        with pytest.raises(ValidationFailed):
            pipeline.safeguards.validate_input("/nonexistent/file.png")

    def test_validate_prompt_too_short(self, pipeline):
        """Should raise ValidationFailed for short prompt."""
        with pytest.raises(ValidationFailed):
            pipeline.safeguards.validate_prompt("ab")


class TestProcessMethods:
    """Tests for process methods (with dry-run)."""

    @pytest.fixture
    def pipeline(self, temp_dir):
        """Create pipeline for testing."""
        config = PipelineConfig(
            safeguards=SafeguardConfig(
                dry_run=True,
                cache_dir=str(Path(temp_dir) / ".cache")
            )
        )
        pipeline = Pipeline(config)
        pipeline.confirm()  # Skip confirmation
        return pipeline

    def test_process_validates_output(self, pipeline, sample_png_file, temp_dir):
        """process() should validate output directory."""
        output_dir = Path(temp_dir) / "output"

        # Should not raise - creates output dir
        result = pipeline.process(sample_png_file, str(output_dir))

        # Dry-run should report success without doing work
        assert "dry_run" in result or "error" not in result


class TestLazyLoading:
    """Tests for lazy loading of heavy modules."""

    @pytest.fixture
    def pipeline(self, temp_dir):
        """Create pipeline for testing."""
        config = PipelineConfig(
            offline_mode=True,  # Prevent AI loading
            safeguards=SafeguardConfig(
                dry_run=True,
                cache_dir=str(Path(temp_dir) / ".cache")
            )
        )
        return Pipeline(config)

    def test_ai_analyzer_not_loaded_initially(self, pipeline):
        """AI analyzer should not be loaded until needed."""
        assert pipeline._ai_analyzer is None

    def test_aseprite_exporter_not_loaded_initially(self, pipeline):
        """Aseprite exporter should not be loaded until needed."""
        assert pipeline._aseprite_exporter is None

    def test_pixellab_client_not_loaded_initially(self, pipeline):
        """PixelLab client should not be loaded until needed."""
        assert pipeline._pixellab_client is None
