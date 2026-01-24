"""
External Tool Integrations for ARDK Asset Pipeline.

This package provides integrations with external tools:
- Aseprite: Sprite editor with animation support
- (Future: Tiled, LDTK, etc.)

Usage:
    from tools.pipeline.integrations import (
        AsepriteExporter,
        parse_aseprite_json,
    )
"""

from .aseprite import (
    AsepriteExporter,
    AsepriteExportResult,
    AsepriteFrame,
    AsepriteTag,
    AsepriteLayer,
    AsepriteMetadata,
    parse_aseprite_json,
    frames_to_animation_sequences,
    is_aseprite_available,
)

__all__ = [
    'AsepriteExporter',
    'AsepriteExportResult',
    'AsepriteFrame',
    'AsepriteTag',
    'AsepriteLayer',
    'AsepriteMetadata',
    'parse_aseprite_json',
    'frames_to_animation_sequences',
    'is_aseprite_available',
]
