"""
Platform Configurations - Hardware-specific asset generation settings.

Provides detailed configurations for each supported retro platform,
including tile limits, color constraints, and generation parameters.
"""

from .nes_config import NES_CONFIG, NES_ASSET_CONFIG
from .genesis_config import GENESIS_CONFIG, GENESIS_ASSET_CONFIG
from .snes_config import SNES_CONFIG, SNES_ASSET_CONFIG
from .platform_registry import (
    get_platform_config,
    get_asset_config,
    list_platforms,
    PLATFORM_REGISTRY,
)

__all__ = [
    # NES
    'NES_CONFIG',
    'NES_ASSET_CONFIG',
    # Genesis
    'GENESIS_CONFIG',
    'GENESIS_ASSET_CONFIG',
    # SNES
    'SNES_CONFIG',
    'SNES_ASSET_CONFIG',
    # Registry
    'get_platform_config',
    'get_asset_config',
    'list_platforms',
    'PLATFORM_REGISTRY',
]
