"""
Base classes for AI generation providers.

Defines the abstract interface that all generation providers must implement,
plus common data structures for generation results and configuration.

Core Components:
    - ProviderCapability: Flags indicating what a provider can do
    - GenerationConfig: Configuration for generation requests
    - GenerationResult: Output from generation including images, frames, errors
    - GenerationProvider: Abstract base class for all providers

Implementing a Custom Provider:
    1. Subclass GenerationProvider
    2. Implement required properties: name, capabilities, is_available
    3. Implement generate() method
    4. Optionally implement _generate_animation_impl, _generate_views_impl, etc.
    5. Register with: register_provider("my_provider", MyProvider())

See pollinations.py for a complete implementation example.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Flag, auto
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple, Union
from PIL import Image


class ProviderCapability(Flag):
    """Capabilities that a generation provider may support."""
    NONE = 0
    TEXT_TO_IMAGE = auto()       # Generate from text prompt
    IMAGE_TO_IMAGE = auto()      # Transform existing image
    INPAINTING = auto()          # Fill masked regions
    OUTPAINTING = auto()         # Extend image boundaries
    UPSCALING = auto()           # Increase resolution
    ANIMATION = auto()           # Generate animation frames
    MULTI_VIEW = auto()          # Generate multiple angles/views
    PALETTE_CONSTRAINT = auto()  # Enforce specific color palette
    PIXEL_PERFECT = auto()       # Guaranteed pixel-aligned output
    STYLE_TRANSFER = auto()      # Apply reference style


@dataclass
class GenerationConfig:
    """Configuration for sprite generation."""

    # Output dimensions
    width: int = 32
    height: int = 32

    # Platform constraints
    platform: str = "genesis"  # genesis, nes, snes, gameboy
    max_colors: int = 16
    palette: Optional[List[Tuple[int, int, int]]] = None  # RGB tuples

    # Generation parameters
    seed: Optional[int] = None
    steps: int = 20
    cfg_scale: float = 7.0

    # Style
    style_reference: Optional[Union[str, Path, Image.Image]] = None
    negative_prompt: str = "blurry, realistic, photo, 3d render, anti-aliasing"

    # Animation (if supported)
    animation_frames: int = 1
    animation_action: Optional[str] = None  # idle, walk, attack, etc.

    # Multi-view (if supported)
    views: int = 1
    view_angles: Optional[List[str]] = None  # front, side, back, etc.

    # Quality/speed tradeoff
    quality: str = "balanced"  # fast, balanced, quality

    # Extra provider-specific options
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationResult:
    """Result from a generation request."""

    # Success/failure
    success: bool

    # Generated image(s)
    image: Optional[Image.Image] = None
    images: List[Image.Image] = field(default_factory=list)

    # Metadata
    provider: str = ""
    model: str = ""
    seed_used: Optional[int] = None
    generation_time_ms: int = 0

    # For animations
    frames: List[Image.Image] = field(default_factory=list)
    frame_durations: List[int] = field(default_factory=list)  # ms per frame

    # For multi-view
    views: Dict[str, Image.Image] = field(default_factory=dict)

    # Errors/warnings
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Cost tracking
    cost_usd: float = 0.0
    tokens_used: int = 0

    # Raw response (for debugging)
    raw_response: Optional[Any] = None

    def __post_init__(self):
        """Ensure images list is populated from single image."""
        if self.image and not self.images:
            self.images = [self.image]
        elif self.images and not self.image:
            self.image = self.images[0] if self.images else None


class GenerationProvider(ABC):
    """
    Abstract base class for AI generation providers.

    Each provider implements generation capabilities specific to their API,
    while presenting a unified interface for the pipeline.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> ProviderCapability:
        """Flags indicating what this provider can do."""
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and accessible."""
        pass

    @abstractmethod
    def generate(self, prompt: str, config: Optional[GenerationConfig] = None) -> GenerationResult:
        """
        Generate an image from a text prompt.

        Args:
            prompt: Text description of the sprite to generate
            config: Generation configuration (uses defaults if None)

        Returns:
            GenerationResult with the generated image(s)
        """
        pass

    def generate_from_image(self,
                           source: Image.Image,
                           prompt: str,
                           config: Optional[GenerationConfig] = None,
                           strength: float = 0.7) -> GenerationResult:
        """
        Generate a new image based on a source image (img2img).

        Args:
            source: Source image to transform
            prompt: Text description guiding the transformation
            config: Generation configuration
            strength: How much to change (0=keep original, 1=ignore original)

        Returns:
            GenerationResult with the transformed image
        """
        if not (self.capabilities & ProviderCapability.IMAGE_TO_IMAGE):
            return GenerationResult(
                success=False,
                errors=[f"{self.name} does not support image-to-image generation"]
            )
        return self._generate_from_image_impl(source, prompt, config, strength)

    def _generate_from_image_impl(self,
                                  source: Image.Image,
                                  prompt: str,
                                  config: Optional[GenerationConfig],
                                  strength: float) -> GenerationResult:
        """Override in subclasses that support img2img."""
        return GenerationResult(
            success=False,
            errors=["img2img not implemented"]
        )

    def generate_animation(self,
                          source: Image.Image,
                          action: str,
                          config: Optional[GenerationConfig] = None) -> GenerationResult:
        """
        Generate animation frames from a single sprite.

        Args:
            source: Source sprite (single frame)
            action: Animation action (idle, walk, attack, jump, etc.)
            config: Generation configuration

        Returns:
            GenerationResult with frames list populated
        """
        if not (self.capabilities & ProviderCapability.ANIMATION):
            return GenerationResult(
                success=False,
                errors=[f"{self.name} does not support animation generation"]
            )
        return self._generate_animation_impl(source, action, config)

    def _generate_animation_impl(self,
                                 source: Image.Image,
                                 action: str,
                                 config: Optional[GenerationConfig]) -> GenerationResult:
        """Override in subclasses that support animation."""
        return GenerationResult(
            success=False,
            errors=["Animation generation not implemented"]
        )

    def generate_views(self,
                      source: Image.Image,
                      views: List[str],
                      config: Optional[GenerationConfig] = None) -> GenerationResult:
        """
        Generate multiple view angles from a single sprite.

        Args:
            source: Source sprite
            views: List of view angles ("front", "side", "back", "front-right", etc.)
            config: Generation configuration

        Returns:
            GenerationResult with views dict populated
        """
        if not (self.capabilities & ProviderCapability.MULTI_VIEW):
            return GenerationResult(
                success=False,
                errors=[f"{self.name} does not support multi-view generation"]
            )
        return self._generate_views_impl(source, views, config)

    def _generate_views_impl(self,
                            source: Image.Image,
                            views: List[str],
                            config: Optional[GenerationConfig]) -> GenerationResult:
        """Override in subclasses that support multi-view."""
        return GenerationResult(
            success=False,
            errors=["Multi-view generation not implemented"]
        )

    def upscale(self,
               source: Image.Image,
               scale: int = 2,
               config: Optional[GenerationConfig] = None) -> GenerationResult:
        """
        Upscale an image while preserving pixel art style.

        Args:
            source: Source image to upscale
            scale: Scale factor (2 or 4)
            config: Generation configuration

        Returns:
            GenerationResult with upscaled image
        """
        if not (self.capabilities & ProviderCapability.UPSCALING):
            return GenerationResult(
                success=False,
                errors=[f"{self.name} does not support upscaling"]
            )
        return self._upscale_impl(source, scale, config)

    def _upscale_impl(self,
                     source: Image.Image,
                     scale: int,
                     config: Optional[GenerationConfig]) -> GenerationResult:
        """Override in subclasses that support upscaling."""
        return GenerationResult(
            success=False,
            errors=["Upscaling not implemented"]
        )

    def health_check(self) -> Tuple[bool, str]:
        """
        Check if the provider is healthy and responding.

        Returns:
            Tuple of (is_healthy, message)
        """
        try:
            # Simple test generation
            result = self.generate(
                "test sprite",
                GenerationConfig(width=16, height=16, quality="fast")
            )
            if result.success:
                return True, f"{self.name} is healthy"
            else:
                return False, f"{self.name} failed: {result.errors}"
        except Exception as e:
            return False, f"{self.name} error: {e}"

    def estimate_cost(self, config: GenerationConfig) -> float:
        """
        Estimate the cost (in USD) for a generation with given config.

        Returns:
            Estimated cost in USD (0 for free/local providers)
        """
        return 0.0  # Default to free, override in paid providers

    def _build_pixel_art_prompt(self, base_prompt: str, config: GenerationConfig) -> str:
        """
        Helper to build a pixel art-optimized prompt.

        Adds appropriate style keywords based on platform.
        """
        platform_styles = {
            "genesis": "16-bit Sega Genesis pixel art, 4-color per palette",
            "nes": "8-bit NES pixel art, limited palette",
            "snes": "16-bit SNES pixel art, vibrant colors",
            "gameboy": "4-shade Gameboy pixel art, green tint",
            "gameboy_color": "Gameboy Color pixel art",
        }

        style = platform_styles.get(config.platform, "pixel art, retro game sprite")

        # Build full prompt
        parts = [
            style,
            base_prompt,
            f"{config.width}x{config.height} sprite",
            "clean pixel edges",
            "no anti-aliasing",
            "transparent background" if config.platform != "gameboy" else "solid background",
        ]

        if config.palette and len(config.palette) <= 16:
            parts.append(f"exactly {len(config.palette)} colors")
        elif config.max_colors:
            parts.append(f"maximum {config.max_colors} colors")

        return ", ".join(parts)
