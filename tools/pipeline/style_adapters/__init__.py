"""
Style adapters for different AI providers.

This module provides provider-specific style translation. The main style.py
module contains the adapters, this package allows for extension with custom
adapters.

Usage:
    from pipeline.style_adapters import PixelLabAdapter, PollinationsAdapter

    # Or import all
    from pipeline.style import (
        StyleAdapter,
        PixelLabAdapter,
        PollinationsAdapter,
        BFLKontextAdapter,
        StyleManager,
        StyleProfile,
    )
"""
from ..style import (
    StyleAdapter,
    PixelLabAdapter,
    PollinationsAdapter,
    BFLKontextAdapter,
    StyleProfile,
    StyleManager,
    OutlineStyle,
    ShadingLevel,
    DetailLevel,
)

__all__ = [
    # Core classes
    'StyleAdapter',
    'StyleProfile',
    'StyleManager',

    # Adapters
    'PixelLabAdapter',
    'PollinationsAdapter',
    'BFLKontextAdapter',

    # Enums
    'OutlineStyle',
    'ShadingLevel',
    'DetailLevel',
]
