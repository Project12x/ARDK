"""
Tests for AI Generation Providers.

Tests provider interfaces, registry, and fallback behavior.
All API calls are mocked to avoid actual costs during testing.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

from PIL import Image

from pipeline.ai_providers.base import (
    GenerationProvider,
    GenerationResult,
    GenerationConfig,
    ProviderCapability,
)
from pipeline.ai_providers.pollinations import PollinationsGenerationProvider
from pipeline.ai_providers.pixie_haus import PixieHausProvider
from pipeline.ai_providers.stable_diffusion import StableDiffusionLocalProvider
from pipeline.ai_providers.registry import (
    ProviderRegistry,
    get_generation_provider,
    get_available_providers,
    register_provider,
    generate_with_fallback,
    provider_status,
    NoProvidersAvailableError,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory."""
    return tmp_path


@pytest.fixture
def sample_image():
    """Create a sample 32x32 sprite image."""
    img = Image.new('RGBA', (32, 32), (255, 0, 255, 255))
    # Draw a simple pattern
    pixels = img.load()
    for y in range(8, 24):
        for x in range(8, 24):
            pixels[x, y] = (100, 100, 200, 255)
    return img


@pytest.fixture
def sample_config():
    """Create a sample generation config."""
    return GenerationConfig(
        width=32,
        height=32,
        platform="genesis",
        max_colors=16,
        seed=42,
    )


@pytest.fixture
def mock_image_response():
    """Create a mock image response (PNG bytes)."""
    img = Image.new('RGB', (128, 128), (100, 150, 200))
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()


# =============================================================================
# GenerationConfig Tests
# =============================================================================

class TestGenerationConfig:
    """Tests for GenerationConfig dataclass."""

    def test_default_values(self):
        """Should have sensible defaults."""
        config = GenerationConfig()
        assert config.width == 32
        assert config.height == 32
        assert config.platform == "genesis"
        assert config.max_colors == 16
        assert config.seed is None
        assert config.steps == 20

    def test_custom_values(self):
        """Should accept custom values."""
        config = GenerationConfig(
            width=64,
            height=64,
            platform="nes",
            max_colors=4,
            seed=12345,
        )
        assert config.width == 64
        assert config.platform == "nes"
        assert config.seed == 12345

    def test_palette_constraint(self):
        """Should accept custom palette."""
        palette = [
            (0, 0, 0),
            (255, 0, 0),
            (0, 255, 0),
            (255, 255, 255),
        ]
        config = GenerationConfig(palette=palette)
        assert config.palette == palette


# =============================================================================
# GenerationResult Tests
# =============================================================================

class TestGenerationResult:
    """Tests for GenerationResult dataclass."""

    def test_success_result(self, sample_image):
        """Should create successful result."""
        result = GenerationResult(
            success=True,
            image=sample_image,
            provider="TestProvider",
            model="test-model",
            generation_time_ms=500,
        )
        assert result.success is True
        assert result.image is not None
        assert len(result.errors) == 0

    def test_failure_result(self):
        """Should create failure result with errors."""
        result = GenerationResult(
            success=False,
            errors=["API error", "Rate limited"],
            provider="TestProvider",
        )
        assert result.success is False
        assert len(result.errors) == 2
        assert result.image is None

    def test_images_list_from_single(self, sample_image):
        """Should populate images list from single image."""
        result = GenerationResult(
            success=True,
            image=sample_image,
        )
        assert len(result.images) == 1
        assert result.images[0] == sample_image

    def test_animation_frames(self, sample_image):
        """Should store animation frames."""
        frames = [sample_image.copy() for _ in range(4)]
        durations = [100, 100, 100, 100]

        result = GenerationResult(
            success=True,
            frames=frames,
            frame_durations=durations,
        )
        assert len(result.frames) == 4
        assert len(result.frame_durations) == 4


# =============================================================================
# ProviderCapability Tests
# =============================================================================

class TestProviderCapability:
    """Tests for ProviderCapability flags."""

    def test_capability_combination(self):
        """Should combine capabilities with bitwise OR."""
        caps = (
            ProviderCapability.TEXT_TO_IMAGE |
            ProviderCapability.IMAGE_TO_IMAGE |
            ProviderCapability.UPSCALING
        )
        assert caps & ProviderCapability.TEXT_TO_IMAGE
        assert caps & ProviderCapability.UPSCALING
        assert not (caps & ProviderCapability.ANIMATION)

    def test_capability_check(self):
        """Should check for specific capability."""
        caps = ProviderCapability.TEXT_TO_IMAGE | ProviderCapability.ANIMATION

        # Has these
        assert caps & ProviderCapability.TEXT_TO_IMAGE
        assert caps & ProviderCapability.ANIMATION

        # Doesn't have these
        assert not (caps & ProviderCapability.UPSCALING)
        assert not (caps & ProviderCapability.PALETTE_CONSTRAINT)


# =============================================================================
# PollinationsProvider Tests
# =============================================================================

class TestPollinationsProvider:
    """Tests for PollinationsGenerationProvider."""

    def test_initialization_default(self):
        """Should initialize with defaults."""
        provider = PollinationsGenerationProvider()
        assert provider.is_available is True  # Works without API key
        assert "Pollinations" in provider.name

    def test_initialization_with_model(self):
        """Should accept custom model."""
        provider = PollinationsGenerationProvider(model="flux")
        assert "flux" in provider.name

    def test_capabilities(self):
        """Should report correct capabilities."""
        provider = PollinationsGenerationProvider()
        caps = provider.capabilities

        assert caps & ProviderCapability.TEXT_TO_IMAGE
        assert caps & ProviderCapability.IMAGE_TO_IMAGE
        assert caps & ProviderCapability.STYLE_TRANSFER

    @patch('urllib.request.urlopen')
    def test_generate_success(self, mock_urlopen, mock_image_response, sample_config):
        """Should generate image from prompt."""
        # Mock response
        mock_response = MagicMock()
        mock_response.read.return_value = mock_image_response
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        provider = PollinationsGenerationProvider()
        result = provider.generate("pixel art warrior", sample_config)

        assert result.success is True
        assert result.image is not None
        assert result.provider == provider.name
        assert result.seed_used is not None

    @patch('urllib.request.urlopen')
    def test_generate_rate_limit(self, mock_urlopen, sample_config):
        """Should handle rate limiting gracefully."""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="",
            code=429,
            msg="Too Many Requests",
            hdrs={},
            fp=None,
        )

        provider = PollinationsGenerationProvider()
        result = provider.generate("test", sample_config)

        assert result.success is False
        assert any("rate" in e.lower() for e in result.errors)

    @patch('urllib.request.urlopen')
    def test_generate_network_error(self, mock_urlopen, sample_config):
        """Should handle network errors."""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("Connection failed")

        provider = PollinationsGenerationProvider()
        result = provider.generate("test", sample_config)

        assert result.success is False
        assert any("network" in e.lower() for e in result.errors)

    def test_cost_estimate(self, sample_config):
        """Pollinations should be free."""
        provider = PollinationsGenerationProvider()
        cost = provider.estimate_cost(sample_config)
        assert cost == 0.0


# =============================================================================
# PixieHausProvider Tests
# =============================================================================

class TestPixieHausProvider:
    """Tests for PixieHausProvider."""

    def test_initialization_without_key(self):
        """Should not be available without API key."""
        with patch.dict('os.environ', {}, clear=True):
            provider = PixieHausProvider()
            assert provider.is_available is False

    def test_capabilities(self):
        """Should report pixel-art focused capabilities."""
        provider = PixieHausProvider(api_key="test-key")
        caps = provider.capabilities

        assert caps & ProviderCapability.TEXT_TO_IMAGE
        assert caps & ProviderCapability.PIXEL_PERFECT
        assert caps & ProviderCapability.PALETTE_CONSTRAINT
        assert caps & ProviderCapability.ANIMATION
        assert caps & ProviderCapability.MULTI_VIEW

    def test_platform_palette_mapping(self):
        """Should map platforms to palette modes."""
        provider = PixieHausProvider()

        assert "genesis" in provider.PLATFORM_PALETTES
        assert "nes" in provider.PLATFORM_PALETTES
        assert "gameboy" in provider.PLATFORM_PALETTES

    def test_generate_unavailable(self, sample_config):
        """Should fail gracefully when not configured."""
        provider = PixieHausProvider()  # No API key
        result = provider.generate("test", sample_config)

        assert result.success is False
        assert any("not configured" in e.lower() for e in result.errors)

    def test_cost_estimate(self, sample_config):
        """Should estimate reasonable costs."""
        provider = PixieHausProvider()
        cost = provider.estimate_cost(sample_config)
        assert cost > 0

        # Animation should cost more
        anim_config = GenerationConfig(animation_frames=4)
        anim_cost = provider.estimate_cost(anim_config)
        assert anim_cost > cost


# =============================================================================
# StableDiffusionLocalProvider Tests
# =============================================================================

class TestStableDiffusionLocalProvider:
    """Tests for StableDiffusionLocalProvider."""

    def test_initialization_default(self):
        """Should initialize with default localhost URL."""
        provider = StableDiffusionLocalProvider()
        assert "127.0.0.1:7860" in provider._api_url

    def test_initialization_custom_url(self):
        """Should accept custom API URL."""
        provider = StableDiffusionLocalProvider(api_url="http://192.168.1.100:7860")
        assert "192.168.1.100" in provider._api_url

    def test_capabilities(self):
        """Should report local capabilities."""
        provider = StableDiffusionLocalProvider()
        caps = provider.capabilities

        assert caps & ProviderCapability.TEXT_TO_IMAGE
        assert caps & ProviderCapability.IMAGE_TO_IMAGE
        assert caps & ProviderCapability.UPSCALING
        assert caps & ProviderCapability.INPAINTING

    @patch('urllib.request.urlopen')
    def test_availability_check_success(self, mock_urlopen):
        """Should detect when SD is running."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        provider = StableDiffusionLocalProvider()
        provider._is_available = None  # Reset cache
        assert provider.is_available is True

    @patch('urllib.request.urlopen')
    def test_availability_check_failure(self, mock_urlopen):
        """Should detect when SD is not running."""
        mock_urlopen.side_effect = Exception("Connection refused")

        provider = StableDiffusionLocalProvider()
        provider._is_available = None  # Reset cache
        assert provider.is_available is False

    def test_cost_estimate(self, sample_config):
        """Local SD should be free."""
        provider = StableDiffusionLocalProvider()
        cost = provider.estimate_cost(sample_config)
        assert cost == 0.0


# =============================================================================
# ProviderRegistry Tests
# =============================================================================

class TestProviderRegistry:
    """Tests for ProviderRegistry."""

    @pytest.fixture
    def fresh_registry(self):
        """Create a fresh registry for testing."""
        return ProviderRegistry()

    def test_register_and_get(self, fresh_registry):
        """Should register and retrieve providers."""
        mock_provider = MagicMock(spec=GenerationProvider)
        mock_provider.is_available = True

        fresh_registry.register("test_provider", mock_provider)
        retrieved = fresh_registry.get("test_provider")

        assert retrieved == mock_provider

    def test_get_case_insensitive(self, fresh_registry):
        """Should retrieve providers case-insensitively."""
        mock_provider = MagicMock(spec=GenerationProvider)
        mock_provider.is_available = True

        fresh_registry.register("TestProvider", mock_provider)

        assert fresh_registry.get("testprovider") == mock_provider
        assert fresh_registry.get("TESTPROVIDER") == mock_provider

    def test_get_available(self, fresh_registry):
        """Should return only available providers."""
        available = MagicMock(spec=GenerationProvider)
        available.is_available = True

        unavailable = MagicMock(spec=GenerationProvider)
        unavailable.is_available = False

        fresh_registry.register("available", available)
        fresh_registry.register("unavailable", unavailable)

        result = fresh_registry.get_available()
        assert available in result
        assert unavailable not in result

    def test_get_with_capability(self, fresh_registry):
        """Should filter by capability."""
        with_animation = MagicMock(spec=GenerationProvider)
        with_animation.is_available = True
        with_animation.capabilities = ProviderCapability.ANIMATION

        without_animation = MagicMock(spec=GenerationProvider)
        without_animation.is_available = True
        without_animation.capabilities = ProviderCapability.TEXT_TO_IMAGE

        fresh_registry.register("with_anim", with_animation)
        fresh_registry.register("without_anim", without_animation)

        result = fresh_registry.get_with_capability(ProviderCapability.ANIMATION)
        assert with_animation in result
        assert without_animation not in result

    def test_fallback_order(self, fresh_registry):
        """Should try providers in fallback order."""
        first = MagicMock(spec=GenerationProvider)
        first.is_available = False

        second = MagicMock(spec=GenerationProvider)
        second.is_available = True
        second.capabilities = ProviderCapability.TEXT_TO_IMAGE

        fresh_registry.register("first", first)
        fresh_registry.register("second", second)
        fresh_registry.set_fallback_order(["first", "second"])

        result = fresh_registry.get_best_provider()
        assert result == second

    def test_no_providers_error(self, fresh_registry):
        """Should raise error when no providers available."""
        # Clear any auto-initialized providers
        fresh_registry._providers.clear()
        fresh_registry._initialized = True  # Prevent re-initialization

        with pytest.raises(NoProvidersAvailableError):
            fresh_registry.get_best_provider()

    def test_status_report(self, fresh_registry):
        """Should report provider status."""
        mock = MagicMock(spec=GenerationProvider)
        mock.name = "MockProvider"
        mock.is_available = True
        mock.capabilities = ProviderCapability.TEXT_TO_IMAGE

        fresh_registry.register("mock", mock)
        status = fresh_registry.status()

        assert "mock" in status
        assert status["mock"]["available"] is True


# =============================================================================
# Fallback Chain Tests
# =============================================================================

class TestFallbackChain:
    """Tests for fallback generation behavior."""

    @pytest.fixture
    def mock_registry(self):
        """Create a registry with mock providers."""
        registry = ProviderRegistry()

        # First provider fails
        failing = MagicMock(spec=GenerationProvider)
        failing.is_available = True
        failing.generate.return_value = GenerationResult(
            success=False,
            errors=["Provider 1 failed"],
        )

        # Second provider succeeds
        success_img = Image.new('RGB', (32, 32), (100, 100, 100))
        succeeding = MagicMock(spec=GenerationProvider)
        succeeding.is_available = True
        succeeding.generate.return_value = GenerationResult(
            success=True,
            image=success_img,
            provider="succeeding",
        )

        registry.register("failing", failing)
        registry.register("succeeding", succeeding)
        registry.set_fallback_order(["failing", "succeeding"])

        return registry

    def test_fallback_to_second_provider(self, mock_registry, sample_config):
        """Should fall back when first provider fails."""
        result = mock_registry.generate_with_fallback("test prompt", sample_config)

        assert result.success is True
        assert result.provider == "succeeding"

    def test_collect_errors_from_all(self, sample_config):
        """Should collect errors from all attempted providers."""
        registry = ProviderRegistry()

        # Both providers fail
        fail1 = MagicMock(spec=GenerationProvider)
        fail1.is_available = True
        fail1.generate.return_value = GenerationResult(
            success=False,
            errors=["Error from provider 1"],
        )

        fail2 = MagicMock(spec=GenerationProvider)
        fail2.is_available = True
        fail2.generate.return_value = GenerationResult(
            success=False,
            errors=["Error from provider 2"],
        )

        registry.register("fail1", fail1)
        registry.register("fail2", fail2)
        registry.set_fallback_order(["fail1", "fail2"])

        result = registry.generate_with_fallback("test", sample_config)

        assert result.success is False
        assert len(result.errors) >= 2


# =============================================================================
# Integration Tests
# =============================================================================

class TestProviderIntegration:
    """Integration tests for provider workflows."""

    def test_provider_registration_workflow(self):
        """Test registering a custom provider."""
        # Create custom mock provider
        custom = MagicMock(spec=GenerationProvider)
        custom.name = "CustomProvider"
        custom.is_available = True
        custom.capabilities = ProviderCapability.TEXT_TO_IMAGE

        # Register with global registry
        register_provider("custom", custom)

        # Should be discoverable
        assert "custom" in get_available_providers()

    def test_prompt_building(self, sample_config):
        """Test pixel art prompt construction."""
        provider = PollinationsGenerationProvider()

        prompt = provider._build_pixel_art_prompt("warrior with sword", sample_config)

        # Should include platform style
        assert "genesis" in prompt.lower() or "16-bit" in prompt.lower()

        # Should include dimensions
        assert "32" in prompt

        # Should include color limit
        assert "16" in prompt or "color" in prompt.lower()
