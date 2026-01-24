"""
AI Provider Registry.

Manages provider discovery, selection, and fallback chains for robust
sprite generation across multiple AI services.

Fallback Strategy:
    1. Try preferred provider (if specified)
    2. Fall back through chain based on availability
    3. Return error if all providers fail

Default Fallback Chain:
    Pixie.haus (best for pixel art) -> Pollinations (free) -> SD Local (free)

Key Functions:
    - get_generation_provider(name): Get a specific or best available provider
    - get_available_providers(): List names of all working providers
    - generate_with_fallback(prompt, config): Generate with automatic fallback
    - provider_status(): Get status of all registered providers
    - register_provider(name, provider): Add custom provider

Usage:
    >>> from pipeline.ai_providers import generate_with_fallback, GenerationConfig
    >>> config = GenerationConfig(width=32, height=32, platform="genesis")
    >>> result = generate_with_fallback("pixel art knight", config)
    >>> if result.success:
    ...     result.image.save("knight.png")
    ... else:
    ...     print(f"Failed: {result.errors}")

Provider Status Check:
    >>> from pipeline.ai_providers import provider_status
    >>> for name, info in provider_status().items():
    ...     print(f"{name}: {'available' if info['available'] else 'unavailable'}")
"""

import os
from typing import Optional, List, Dict, Type, Callable

from .base import (
    GenerationProvider,
    GenerationResult,
    GenerationConfig,
    ProviderCapability,
)
from .pollinations import PollinationsGenerationProvider
from .pixie_haus import PixieHausProvider
from .stable_diffusion import StableDiffusionLocalProvider


class NoProvidersAvailableError(Exception):
    """Raised when no AI providers are available."""
    pass


class ProviderRegistry:
    """
    Central registry for AI generation providers.

    Handles provider registration, discovery, and fallback chains.
    """

    # Default fallback order (can be customized)
    DEFAULT_FALLBACK_ORDER = [
        "pixie_haus",      # Best for pixel art, has costs
        "pollinations",    # Free, good quality
        "sd_local",        # Free, requires local setup
    ]

    def __init__(self):
        self._providers: Dict[str, GenerationProvider] = {}
        self._fallback_order: List[str] = self.DEFAULT_FALLBACK_ORDER.copy()
        self._initialized = False

    def _ensure_initialized(self):
        """Lazy initialization of default providers."""
        if self._initialized:
            return

        # Register default providers
        self.register("pollinations", PollinationsGenerationProvider())
        self.register("pixie_haus", PixieHausProvider())
        self.register("sd_local", StableDiffusionLocalProvider())

        self._initialized = True

    def register(self, name: str, provider: GenerationProvider):
        """
        Register a provider with the registry.

        Args:
            name: Unique identifier for this provider
            provider: Provider instance
        """
        self._providers[name.lower()] = provider

    def unregister(self, name: str):
        """Remove a provider from the registry."""
        self._providers.pop(name.lower(), None)

    def get(self, name: str) -> Optional[GenerationProvider]:
        """
        Get a specific provider by name.

        Args:
            name: Provider name (case-insensitive)

        Returns:
            Provider instance or None if not found
        """
        self._ensure_initialized()
        return self._providers.get(name.lower())

    def get_available(self) -> List[GenerationProvider]:
        """
        Get list of all available (configured and accessible) providers.

        Returns:
            List of available provider instances
        """
        self._ensure_initialized()
        return [p for p in self._providers.values() if p.is_available]

    def get_available_names(self) -> List[str]:
        """Get names of all available providers."""
        self._ensure_initialized()
        return [name for name, p in self._providers.items() if p.is_available]

    def get_with_capability(self, capability: ProviderCapability) -> List[GenerationProvider]:
        """
        Get providers that support a specific capability.

        Args:
            capability: Required capability flag(s)

        Returns:
            List of providers with the capability
        """
        self._ensure_initialized()
        return [
            p for p in self._providers.values()
            if p.is_available and (p.capabilities & capability)
        ]

    def set_fallback_order(self, order: List[str]):
        """
        Set custom fallback order for providers.

        Args:
            order: List of provider names in priority order
        """
        self._fallback_order = [name.lower() for name in order]

    def get_best_provider(self,
                          preferred: Optional[str] = None,
                          capability: Optional[ProviderCapability] = None) -> GenerationProvider:
        """
        Get the best available provider.

        Args:
            preferred: Preferred provider name (tried first)
            capability: Required capability (filters providers)

        Returns:
            Best available provider

        Raises:
            NoProvidersAvailableError: If no providers are available
        """
        self._ensure_initialized()

        # Try preferred provider first
        if preferred:
            provider = self.get(preferred)
            if provider and provider.is_available:
                if capability is None or (provider.capabilities & capability):
                    return provider

        # Try fallback chain
        for name in self._fallback_order:
            provider = self.get(name)
            if provider and provider.is_available:
                if capability is None or (provider.capabilities & capability):
                    return provider

        # Try any available provider
        available = self.get_available()
        if capability:
            available = [p for p in available if p.capabilities & capability]

        if available:
            return available[0]

        raise NoProvidersAvailableError(
            f"No AI providers available. Install API keys or run local SD.\n"
            f"Registered: {list(self._providers.keys())}\n"
            f"Available: {self.get_available_names()}"
        )

    def generate_with_fallback(self,
                               prompt: str,
                               config: Optional[GenerationConfig] = None,
                               preferred: Optional[str] = None,
                               max_retries: int = 2) -> GenerationResult:
        """
        Generate with automatic fallback to other providers on failure.

        Args:
            prompt: Generation prompt
            config: Generation configuration
            preferred: Preferred provider to try first
            max_retries: Number of fallback attempts

        Returns:
            GenerationResult from first successful provider
        """
        self._ensure_initialized()
        config = config or GenerationConfig()

        errors = []
        tried = set()

        # Build provider order
        provider_order = []
        if preferred:
            provider_order.append(preferred.lower())

        for name in self._fallback_order:
            if name not in provider_order:
                provider_order.append(name)

        # Try each provider
        for name in provider_order:
            if len(tried) >= max_retries + 1:
                break

            provider = self.get(name)
            if not provider or not provider.is_available:
                continue

            tried.add(name)

            try:
                result = provider.generate(prompt, config)
                if result.success:
                    return result
                else:
                    errors.extend([f"[{name}] {e}" for e in result.errors])
            except Exception as e:
                errors.append(f"[{name}] Exception: {e}")

        # All providers failed
        return GenerationResult(
            success=False,
            errors=errors or ["No providers available"],
            provider="fallback_chain",
        )

    def status(self) -> Dict[str, Dict]:
        """
        Get status of all registered providers.

        Returns:
            Dict mapping provider names to status info
        """
        self._ensure_initialized()

        status = {}
        for name, provider in self._providers.items():
            status[name] = {
                "name": provider.name,
                "available": provider.is_available,
                "capabilities": str(provider.capabilities),
            }
        return status


# Global registry instance
_registry = ProviderRegistry()


def get_generation_provider(name: Optional[str] = None,
                            capability: Optional[ProviderCapability] = None) -> GenerationProvider:
    """
    Get a generation provider from the global registry.

    Args:
        name: Specific provider name, or None for best available
        capability: Required capability

    Returns:
        Provider instance

    Raises:
        NoProvidersAvailableError: If no matching provider found
    """
    if name:
        provider = _registry.get(name)
        if provider and provider.is_available:
            return provider
        # Fall through to best available
    return _registry.get_best_provider(preferred=name, capability=capability)


def get_available_providers() -> List[str]:
    """Get names of all available providers."""
    return _registry.get_available_names()


def register_provider(name: str, provider: GenerationProvider):
    """Register a custom provider with the global registry."""
    _registry.register(name, provider)


def generate_with_fallback(prompt: str,
                          config: Optional[GenerationConfig] = None,
                          preferred: Optional[str] = None) -> GenerationResult:
    """
    Generate image with automatic fallback.

    Convenience function that uses the global registry.

    Args:
        prompt: Generation prompt
        config: Generation configuration
        preferred: Preferred provider name

    Returns:
        GenerationResult from first successful provider
    """
    return _registry.generate_with_fallback(prompt, config, preferred)


def provider_status() -> Dict[str, Dict]:
    """Get status of all registered providers."""
    return _registry.status()
