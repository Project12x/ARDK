"""
ARDK Asset Generators - Bespoke sprite and background generation pipeline.

This module provides AI-powered asset generation with:
- Platform-specific sprite sheet generation
- Tile optimization (symmetry, mirroring, deduplication)
- Scrolling backgrounds with seamless looping
- Multi-layer parallax support
- Animated background tiles
- Integrated pipeline for complete asset workflows
- Cross-generation conversion (NES → Genesis, etc.)
- Tier-based multi-platform generation

Uses Pollinations.ai with "best model for each task" policy:
- Image Generation: flux (best pixel-art output)
- Sprite Detection: gemini-fast (fast bounding boxes)
- Palette Extraction: openai-large (best color understanding)
- Animation Analysis: gemini (frame timing)
- Layout Analysis: gemini-large (complex sheets)
"""

from .base_generator import (
    AssetGenerator,
    GenerationFlags,
    GeneratedAsset,
    PlatformConfig,
    PollinationsClient,
    get_nes_config,
    get_genesis_config,
    get_snes_config,
    get_gameboy_config,
    get_platform_config,
    validate_asset_for_platform,
)
from .character_generator import CharacterGenerator, CharacterSheet, AnimationData
from .background_generator import BackgroundGenerator, ScrollingBackground
from .parallax_generator import ParallaxGenerator, ParallaxSet, ParallaxLayer, LAYER_PRESETS
from .animated_tile_generator import (
    AnimatedTileGenerator,
    AnimatedTile,
    AnimatedTileset,
    TILE_ANIMATION_PRESETS,
)
from .pipeline_integration import (
    IntegratedPipeline,
    PipelineConfig,
    PipelineResult,
    AssetType,
    ProjectManifest,
)
from .tier_system import (
    AssetTier,
    AssetTierSpec,
    TIER_SPECS,
    DownsampleConfig,
    PlatformPaletteConfig,
    PLATFORM_PALETTE_CONFIGS,
    get_tier_for_platform,
    get_generation_tier,
    get_downsample_config,
    get_prompt_for_tier,
    get_platform_palette_config,
    NES_MASTER_PALETTE,
    GB_PALETTE,
    SMS_PALETTE,
)
from .sprite_ingestor import (
    SpriteIngestor,
    IngestionManifest,
    IngestionStatus,
    ValidationResult,
)
from .asset_manifest import (
    UnifiedAssetManifest,
    AssetEntry,
    AssetVariant,
    AnimationEntry,
    AssetCategory,
    ProcessingStage,
    OutputFormat,
    create_project_manifest,
    load_or_create_manifest,
)
from .cross_gen_converter import (
    CrossGenConverter,
    ConversionResult,
    TierGenerationResult,
    ConversionMode,
    GenerationTier,
)

__all__ = [
    # Base
    'AssetGenerator',
    'GenerationFlags',
    'GeneratedAsset',
    'PlatformConfig',
    'PollinationsClient',
    # Platform configs
    'get_nes_config',
    'get_genesis_config',
    'get_snes_config',
    'get_gameboy_config',
    'get_platform_config',
    'validate_asset_for_platform',
    # Character generation
    'CharacterGenerator',
    'CharacterSheet',
    'AnimationData',
    # Background generation
    'BackgroundGenerator',
    'ScrollingBackground',
    # Parallax generation
    'ParallaxGenerator',
    'ParallaxSet',
    'ParallaxLayer',
    'LAYER_PRESETS',
    # Animated tiles
    'AnimatedTileGenerator',
    'AnimatedTile',
    'AnimatedTileset',
    'TILE_ANIMATION_PRESETS',
    # Pipeline integration
    'IntegratedPipeline',
    'PipelineConfig',
    'PipelineResult',
    'AssetType',
    'ProjectManifest',
    # Tier system
    'AssetTier',
    'AssetTierSpec',
    'TIER_SPECS',
    'DownsampleConfig',
    'PlatformPaletteConfig',
    'PLATFORM_PALETTE_CONFIGS',
    'get_tier_for_platform',
    'get_generation_tier',
    'get_downsample_config',
    'get_prompt_for_tier',
    'get_platform_palette_config',
    'NES_MASTER_PALETTE',
    'GB_PALETTE',
    'SMS_PALETTE',
    # Sprite ingestion
    'SpriteIngestor',
    'IngestionManifest',
    'IngestionStatus',
    'ValidationResult',
    # Unified asset manifest
    'UnifiedAssetManifest',
    'AssetEntry',
    'AssetVariant',
    'AnimationEntry',
    'AssetCategory',
    'ProcessingStage',
    'OutputFormat',
    'create_project_manifest',
    'load_or_create_manifest',
    # Cross-generation conversion
    'CrossGenConverter',
    'ConversionResult',
    'TierGenerationResult',
    'ConversionMode',
    'GenerationTier',
]

__version__ = '1.1.0'
