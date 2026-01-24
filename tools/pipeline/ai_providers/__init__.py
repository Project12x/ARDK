"""
AI Generation Providers Module.

Unified interface for AI-powered sprite generation across multiple providers.
Supports text-to-image, animation generation, multi-view, and upscaling.

Providers:
    - PollinationsGenerationProvider: Free, 30+ models, animation & multi-view & upscaling
    - PixieHausProvider: Pixel-perfect sprites, palette constraints (requires API key)
    - StableDiffusionLocalProvider: Local SD WebUI, custom models (requires local setup)

Capabilities:
    - TEXT_TO_IMAGE: Generate sprites from text descriptions
    - ANIMATION: Generate walk/attack/idle animation frames
    - MULTI_VIEW: Generate front/side/back views
    - IMAGE_TO_IMAGE: Transform existing sprites
    - UPSCALING: Upscale while preserving pixel art style
    - PALETTE_CONSTRAINT: Enforce specific color palettes

Quick Start:
    >>> from pipeline.ai_providers import get_generation_provider, GenerationConfig
    >>> provider = get_generation_provider()  # Gets best available
    >>> config = GenerationConfig(width=32, height=32, platform="genesis")
    >>> result = provider.generate("pixel art knight", config)
    >>> if result.success:
    ...     result.image.save("knight.png")

Animation Generation:
    >>> from PIL import Image
    >>> source = Image.open("knight_idle.png")
    >>> result = provider.generate_animation(source, "walk", config)
    >>> for i, frame in enumerate(result.frames):
    ...     frame.save(f"knight_walk_{i}.png")

Upscaling:
    >>> from PIL import Image
    >>> source = Image.open("sprite_32x32.png")
    >>> result = provider.upscale(source, scale=2, config)
    >>> if result.success:
    ...     result.image.save("sprite_64x64.png")  # 2x upscaled

Fallback Chain:
    >>> from pipeline.ai_providers import generate_with_fallback
    >>> result = generate_with_fallback("dragon boss", config, preferred="pixie_haus")
    >>> # Tries: pixie_haus -> pollinations -> sd_local

Integration:
    This module is used by:
    - AIAnimationGenerator in ai.py for animation workflows
    - AIUpscaler in ai.py for upscaling + requantization (Phase 3.2)
    - GenerativeResizer in ai.py for sprite variant generation
"""

from .base import (
    GenerationProvider,
    GenerationResult,
    GenerationConfig,
    ProviderCapability,
)

from .pollinations import PollinationsGenerationProvider
from .pixie_haus import PixieHausProvider
from .stable_diffusion import StableDiffusionLocalProvider
from .registry import (
    get_generation_provider,
    get_available_providers,
    register_provider,
    generate_with_fallback,
    provider_status,
    ProviderRegistry,
    NoProvidersAvailableError,
)

__all__ = [
    # Base classes
    'GenerationProvider',
    'GenerationResult',
    'GenerationConfig',
    'ProviderCapability',
    # Providers
    'PollinationsGenerationProvider',
    'PixieHausProvider',
    'StableDiffusionLocalProvider',
    # Registry
    'get_generation_provider',
    'get_available_providers',
    'register_provider',
    'generate_with_fallback',
    'provider_status',
    'ProviderRegistry',
    'NoProvidersAvailableError',
]
