"""
ARDK Pixel Pipeline - Sprite Processing for Retro Platforms.

This package provides tools for processing sprites and assets for
retro gaming platforms, with first-class SGDK/Genesis support.

Modules:
    animation         - Animation metadata extraction and SGDK export
    sheet_assembler   - Sprite sheet assembly and AI-powered dissection
    sgdk_format       - SGDK sprite formatting and validation
    genesis_export    - Genesis 4bpp tile export with mirror optimization
    palette_converter - Cross-platform palette conversion
    palette_manager   - Game-wide palette management and validation
    sgdk_resources    - SGDK resource file (.res) generation
    performance       - Performance budget calculator (scanline/DMA analysis)
    collision_editor  - Collision visualization and debug tools
    animation_fsm     - Animation state machine C code generator
    cross_platform    - Multi-platform asset export (NES, Game Boy, SMS)
    maps              - Tiled TMX/TSX map parsing and SGDK export
    audio             - Audio conversion and SFX management for Genesis
    platforms         - Platform-specific configurations
    processing        - Core image processing
    ai                - AI provider integration
    style             - Style transfer system
    fallback          - Fallback processing when AI unavailable
    quantization      - Perceptual color science and dithering (Phase 0.7-0.8)
    effects           - Sprite effects (hit flash, damage tint, etc.) (Phase 1.3)
    integrations      - External tool integrations (Aseprite) (Phase 1.8)
"""

# Animation module (Phase 1.1)
from .animation import (
    AnimationPattern,
    AnimationFrame,
    AnimationSequence,
    AnimationExtractor,
    DEFAULT_TIMING,
    ONE_SHOT_ACTIONS,
    export_sgdk_animations,
    export_animations_json,
    load_animations_json,
    # AI/PixelLab integration (frame-based)
    create_sequence_from_frames,
    assemble_sprite_sheet,
    generate_animation_bundle,
    generate_multi_animation_bundle,
    # Sprite sheet processing (any AI model)
    split_sprite_sheet,
    generate_sprite_sheet_prompt,
    generate_animation_from_sheet,
    batch_generate_from_sheets,
)

# Sheet assembly and dissection (Phase 1.2)
from .sheet_assembler import (
    # Data structures
    FramePlacement,
    SheetLayout,
    DetectedSprite,
    PackingAlgorithm,
    AIProvider,
    # Assembler
    SpriteSheetAssembler,
    # Dissectors
    SheetDissector,
    GridDissector,
    # Convenience functions
    assemble_sheet,
    dissect_sheet,
)

# Palette conversion (Phase 2.0.4)
from .palette_converter import (
    PaletteFormat,
    PaletteInfo,
    PaletteConverter,
    NES_PALETTE,
    GAMEBOY_PALETTE_GREEN,
    GAMEBOY_PALETTE_GRAY,
)

# Genesis export with tile mirroring (Phase 2.0.3) and VDP-ready export (Phase 2.1.2)
from .genesis_export import (
    TileMatch,
    TileOptimizationStats,
    TileFormat,
    flip_tile_h,
    flip_tile_v,
    flip_tile_hv,
    find_tile_match,
    find_tile_match_multiplatform,
    export_genesis_tilemap_optimized,
    # VDP-Ready Export (Phase 2.1.2)
    SpriteAttribute,
    export_sprite_attribute_table,
    export_cram_palette,
    export_tilemap_with_attributes,
    align_for_dma,
    export_vdp_ready_sprite,
)

# SGDK resource file generation (Phase 2.1.1)
from .sgdk_resources import (
    Compression,
    SpriteOptimization,
    TilesetOptimization,
    SpriteResource,
    TilesetResource,
    PaletteResource,
    MapResource,
    ImageResource,
    BinaryResource,
    XGMResource,
    WAVResource,
    SGDKResourceGenerator,
    generate_resources_from_directory,
    sprite_to_res_entry,
)

# Palette management (Game-wide palette definitions)
from .palette_manager import (
    PalettePurpose,
    PaletteSlot,
    ValidationResult,
    PaletteUsageStats,
    PaletteManager,
    create_genesis_game_palettes,
)

# Performance budget calculator (Phase 2.1.3)
from .performance import (
    SeverityLevel,
    ScanlineInfo,
    PerformanceWarning,
    PerformanceReport,
    PerformanceBudgetCalculator,
    analyze_sprite_performance,
)

# Collision visualization (Phase 2.2.3)
from .collision_editor import (
    CollisionBox,
    CollisionVisualizer,
    render_collision_debug,
    export_collision_debug_image,
)

# Animation FSM code generator (Phase 2.2.2)
from .animation_fsm import (
    ConditionType,
    Transition,
    AnimationState,
    FSMValidationResult,
    AnimationFSM,
    create_character_fsm,
)

# Cross-platform export (Phase 2.2.1)
from .cross_platform import (
    Platform,
    PlatformSpec,
    ExportConfig,
    ExportResult,
    CrossPlatformExporter,
    export_multi_platform,
    get_platform_info,
    PLATFORM_SPECS,
)

# Tiled map integration (Phase 3.0)
from .maps import (
    # Enums
    CollisionType,
    ObjectType,
    # Data classes
    TileLayer,
    MapObject,
    ObjectLayer,
    TileProperties,
    Tileset,
    TiledMap,
    MapExportConfig,
    MapExportResult,
    # Classes
    TiledParser,
    CollisionExporter,
    SGDKMapExporter,
    MapVisualizer,
    # Convenience functions
    load_tiled_map,
    export_map_to_sgdk,
    extract_collision,
)

# Audio pipeline (Phase 3.1)
from .audio import (
    # Enums
    AudioFormat,
    SFXPriority,
    # Constants
    GENESIS_SAMPLE_RATES,
    DEFAULT_SFX_RATE,
    DEFAULT_MUSIC_RATE,
    Z80_CPU_USAGE,
    # Data classes
    AudioInfo,
    ConversionResult,
    SoundEffect,
    SFXBank,
    # Classes
    AudioConverter,
    SFXManager,
    # Convenience functions
    convert_audio,
    analyze_audio,
    validate_audio,
)

# Perceptual quantization and dithering (Phase 0.7-0.8)
from .quantization import (
    # Perceptual color science (Phase 0.7)
    find_nearest_perceptual,
    find_nearest_rgb,
    extract_optimal_palette,
    rgb_to_lab,
    lab_to_rgb,
    calculate_color_distance,
    PerceptualQuantizer,
    # Dithering algorithms (Phase 0.8)
    floyd_steinberg_numba,
    ordered_dither_numba,
    atkinson_dither_numba,
    DitherEngine,
    DitherResult,
    dither_image,
    get_available_methods,
    get_bayer_matrix,
    is_numba_available,
    NUMBA_AVAILABLE,
)

# Sprite effects (Phase 1.3)
from .effects import (
    SpriteEffects,
    EffectConfig,
    EffectResult,
    # Convenience functions
    white_flash,
    damage_tint,
    silhouette,
    outline,
    drop_shadow,
    glow,
    palette_swap,
    generate_hit_variants,
    batch_generate_effects,
    # Genesis helpers
    create_genesis_hit_palette,
    create_damage_palette,
)

# Aseprite integration (Phase 1.8)
from .integrations import (
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
    # Animation (Phase 1.1)
    'AnimationPattern',
    'AnimationFrame',
    'AnimationSequence',
    'AnimationExtractor',
    'DEFAULT_TIMING',
    'ONE_SHOT_ACTIONS',
    'export_sgdk_animations',
    'export_animations_json',
    'load_animations_json',
    # AI/PixelLab integration (frame-based)
    'create_sequence_from_frames',
    'assemble_sprite_sheet',
    'generate_animation_bundle',
    'generate_multi_animation_bundle',
    # Sprite sheet processing (any AI model)
    'split_sprite_sheet',
    'generate_sprite_sheet_prompt',
    'generate_animation_from_sheet',
    'batch_generate_from_sheets',
    # Sheet assembly and dissection (Phase 1.2)
    'FramePlacement',
    'SheetLayout',
    'DetectedSprite',
    'PackingAlgorithm',
    'AIProvider',
    'SpriteSheetAssembler',
    'SheetDissector',
    'GridDissector',
    'assemble_sheet',
    'dissect_sheet',
    # Palette conversion (Phase 2.0.4)
    'PaletteFormat',
    'PaletteInfo',
    'PaletteConverter',
    'NES_PALETTE',
    'GAMEBOY_PALETTE_GREEN',
    'GAMEBOY_PALETTE_GRAY',
    # Genesis export with tile mirroring (Phase 2.0.3)
    'TileMatch',
    'TileOptimizationStats',
    'TileFormat',
    'flip_tile_h',
    'flip_tile_v',
    'flip_tile_hv',
    'find_tile_match',
    'find_tile_match_multiplatform',
    'export_genesis_tilemap_optimized',
    # VDP-Ready Export (Phase 2.1.2)
    'SpriteAttribute',
    'export_sprite_attribute_table',
    'export_cram_palette',
    'export_tilemap_with_attributes',
    'align_for_dma',
    'export_vdp_ready_sprite',
    # SGDK resource file generation (Phase 2.1.1)
    'Compression',
    'SpriteOptimization',
    'TilesetOptimization',
    'SpriteResource',
    'TilesetResource',
    'PaletteResource',
    'MapResource',
    'ImageResource',
    'BinaryResource',
    'XGMResource',
    'WAVResource',
    'SGDKResourceGenerator',
    'generate_resources_from_directory',
    'sprite_to_res_entry',
    # Palette management
    'PalettePurpose',
    'PaletteSlot',
    'ValidationResult',
    'PaletteUsageStats',
    'PaletteManager',
    'create_genesis_game_palettes',
    # Performance budget calculator (Phase 2.1.3)
    'SeverityLevel',
    'ScanlineInfo',
    'PerformanceWarning',
    'PerformanceReport',
    'PerformanceBudgetCalculator',
    'analyze_sprite_performance',
    # Collision visualization (Phase 2.2.3)
    'CollisionBox',
    'CollisionVisualizer',
    'render_collision_debug',
    'export_collision_debug_image',
    # Animation FSM code generator (Phase 2.2.2)
    'ConditionType',
    'Transition',
    'AnimationState',
    'FSMValidationResult',
    'AnimationFSM',
    'create_character_fsm',
    # Cross-platform export (Phase 2.2.1)
    'Platform',
    'PlatformSpec',
    'ExportConfig',
    'ExportResult',
    'CrossPlatformExporter',
    'export_multi_platform',
    'get_platform_info',
    'PLATFORM_SPECS',
    # Tiled map integration (Phase 3.0)
    'CollisionType',
    'ObjectType',
    'TileLayer',
    'MapObject',
    'ObjectLayer',
    'TileProperties',
    'Tileset',
    'TiledMap',
    'MapExportConfig',
    'MapExportResult',
    'TiledParser',
    'CollisionExporter',
    'SGDKMapExporter',
    'MapVisualizer',
    'load_tiled_map',
    'export_map_to_sgdk',
    'extract_collision',
    # Audio pipeline (Phase 3.1)
    'AudioFormat',
    'SFXPriority',
    'GENESIS_SAMPLE_RATES',
    'DEFAULT_SFX_RATE',
    'DEFAULT_MUSIC_RATE',
    'Z80_CPU_USAGE',
    'AudioInfo',
    'ConversionResult',
    'SoundEffect',
    'SFXBank',
    'AudioConverter',
    'SFXManager',
    'convert_audio',
    'analyze_audio',
    'validate_audio',
    # Perceptual quantization and dithering (Phase 0.7-0.8)
    'find_nearest_perceptual',
    'find_nearest_rgb',
    'extract_optimal_palette',
    'rgb_to_lab',
    'lab_to_rgb',
    'calculate_color_distance',
    'PerceptualQuantizer',
    'floyd_steinberg_numba',
    'ordered_dither_numba',
    'atkinson_dither_numba',
    'DitherEngine',
    'DitherResult',
    'dither_image',
    'get_available_methods',
    'get_bayer_matrix',
    'is_numba_available',
    'NUMBA_AVAILABLE',
    # Sprite effects (Phase 1.3)
    'SpriteEffects',
    'EffectConfig',
    'EffectResult',
    'white_flash',
    'damage_tint',
    'silhouette',
    'outline',
    'drop_shadow',
    'glow',
    'palette_swap',
    'generate_hit_variants',
    'batch_generate_effects',
    'create_genesis_hit_palette',
    'create_damage_palette',
    # Aseprite integration (Phase 1.8)
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

__version__ = '3.4.0'
