"""
Asset Tier System - Graphics-Only Tier Definitions for Multi-Platform Assets.

Aligned with HAL_TIER_ASSETS definitions from src/hal/hal_tiers.h.
This module ONLY handles graphics/asset tiers - NOT logic/CPU tiers.

HAL Asset Tier Definitions:
- HAL_TIER_MINIMAL (0): NES, GB, GBC, C64, ZX, Atari 2600/7800
- HAL_TIER_MINIMAL_PLUS (1): SMS, MSX2, Neo Geo Pocket
- HAL_TIER_STANDARD (2): Genesis, SNES, PC Engine, Amiga OCS
- HAL_TIER_STANDARD_PLUS (3): Neo Geo, Sega CD, X68000, 32X
- HAL_TIER_EXTENDED (4): GBA, DS, PSP

Asset Peak Platforms (HAL_ASSET_PEAK_* from hal_tiers.h):
- MINIMAL peak: GBC - best 4/palette colors, 56 on screen
- MINIMAL_PLUS peak: SMS - 16 colors/sprite
- STANDARD peak: SNES - 256 colors on screen, Mode 7 capable
- STANDARD_PLUS peak: Neo Geo - 4096 colors, arcade quality
- EXTENDED peak: DS - 262K colors, dual screen

Design Philosophy:
1. Design assets for the HIGHEST tier among target platforms (peak quality)
2. Downsample and reconfigure to lower tiers as needed
3. Platform-specific palette reallocation within tier constraints
4. Generate once at peak, convert many times to specific platforms

Workflow:
1. Identify all target platforms
2. Find highest tier = generation tier (use that tier's peak as target)
3. Generate high-quality source asset at peak tier quality
4. Downsample to each lower tier with appropriate constraints
5. Apply platform-specific palette and format conversions
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import IntEnum


# =============================================================================
# Tier Definitions
# =============================================================================

class AssetTier(IntEnum):
    """
    Asset/Graphics capability tiers - aligned with HAL_TIER_ASSETS.

    These tiers represent GRAPHICAL capabilities only, not CPU/logic.
    Use these for sprite generation, palette allocation, and tile limits.
    """
    MINIMAL = 0        # NES, GB, GBC, C64, ZX, Atari 2600/7800
    MINIMAL_PLUS = 1   # SMS, MSX2, Neo Geo Pocket
    STANDARD = 2       # Genesis, SNES, PC Engine, Amiga OCS
    STANDARD_PLUS = 3  # Neo Geo, Sega CD, X68000, 32X
    EXTENDED = 4       # GBA, DS, PSP


# Alias for backwards compatibility
HardwareTier = AssetTier


@dataclass
class AssetTierSpec:
    """
    Graphical specification for an asset tier.

    IMPORTANT: These are GRAPHICS-ONLY specifications.
    They define colors, sprites, tiles - NOT CPU or memory.

    The 'peak_platform' is the best graphical target within the tier.
    Design for the peak, then reduce for lesser platforms in the tier.
    """

    tier: AssetTier
    name: str
    peak_platform: str  # HAL_ASSET_PEAK_* - design target for this tier

    # Color capabilities
    colors_per_palette: int
    max_palettes: int
    total_colors: int  # Max simultaneous on screen
    color_depth_bits: int  # Bits per color channel

    # Sprite capabilities
    max_sprite_size: Tuple[int, int]
    recommended_sprite_size: Tuple[int, int]
    max_sprite_colors: int  # Colors per sprite (excl. transparent)

    # Tile/Background capabilities
    tile_size: Tuple[int, int]
    max_unique_tiles: int
    max_bg_palettes: int  # Background palettes

    # Animation capabilities (frames per animation)
    max_animation_frames: int
    recommended_frame_counts: Dict[str, int]

    # Generation style hints for AI
    prompt_style: str
    dithering_allowed: bool
    anti_aliasing_allowed: bool
    gradient_allowed: bool

    # Platforms in this asset tier
    platforms: List[str] = field(default_factory=list)


# Alias for backwards compatibility
TierSpec = AssetTierSpec


# =============================================================================
# Tier Specifications
# =============================================================================

# =============================================================================
# Asset Tier Specifications
# =============================================================================
# Aligned with HAL_ASSET_PEAK_* definitions from hal_tiers.h

TIER_SPECS: Dict[AssetTier, AssetTierSpec] = {
    AssetTier.MINIMAL: AssetTierSpec(
        tier=AssetTier.MINIMAL,
        name="MINIMAL",
        peak_platform="GBC",  # HAL_ASSET_PEAK_MINIMAL - best 4/palette colors
        colors_per_palette=4,
        max_palettes=8,  # GBC has 8 BG + 8 sprite palettes
        total_colors=56,  # GBC: 56 colors on screen
        color_depth_bits=5,  # GBC: 15-bit color (5 per channel)
        max_sprite_size=(16, 16),  # 8x16 mode common
        recommended_sprite_size=(16, 16),
        max_sprite_colors=3,  # +1 transparent per palette
        tile_size=(8, 8),
        max_unique_tiles=256,  # Per CHR bank
        max_bg_palettes=4,
        max_animation_frames=4,
        recommended_frame_counts={
            'idle': 2, 'walk': 4, 'run': 4, 'attack': 3,
            'hurt': 2, 'death': 3, 'jump': 2,
        },
        prompt_style="8-bit pixel art for Game Boy Color, limited palette (4 colors per sprite), "
                    "chunky pixels, bold outlines, high contrast, iconic readable silhouettes, "
                    "no anti-aliasing, no gradients, NES/Game Boy aesthetic",
        dithering_allowed=False,
        anti_aliasing_allowed=False,
        gradient_allowed=False,
        platforms=['nes', 'famicom', 'gb', 'gbc', 'c64', 'zx', 'atari2600', 'atari7800'],
    ),

    AssetTier.MINIMAL_PLUS: AssetTierSpec(
        tier=AssetTier.MINIMAL_PLUS,
        name="MINIMAL_PLUS",
        peak_platform="SMS",  # HAL_ASSET_PEAK_MINIMAL_PLUS - 16 colors/sprite
        colors_per_palette=16,
        max_palettes=2,  # SMS: 1 sprite + 1 BG palette
        total_colors=32,  # SMS: 32 simultaneous from 64
        color_depth_bits=6,  # SMS: 6-bit palette (2 per channel)
        max_sprite_size=(16, 16),  # SMS sprite limit
        recommended_sprite_size=(16, 16),
        max_sprite_colors=15,  # 16 - 1 transparent
        tile_size=(8, 8),
        max_unique_tiles=448,  # SMS VRAM limit
        max_bg_palettes=1,
        max_animation_frames=6,
        recommended_frame_counts={
            'idle': 3, 'walk': 4, 'run': 6, 'attack': 4,
            'hurt': 2, 'death': 4, 'jump': 3,
        },
        prompt_style="8-bit pixel art for Sega Master System, up to 16 colors per sprite, "
                    "clean pixel edges, subtle shading, no anti-aliasing, "
                    "enhanced 8-bit aesthetic, SMS/Game Gear quality",
        dithering_allowed=True,  # Ordered dithering OK
        anti_aliasing_allowed=False,
        gradient_allowed=False,
        platforms=['sms', 'gamegear', 'msx2', 'ngp', 'ngpc'],
    ),

    AssetTier.STANDARD: AssetTierSpec(
        tier=AssetTier.STANDARD,
        name="STANDARD",
        peak_platform="SNES",  # HAL_ASSET_PEAK_STANDARD - 256 colors, Mode 7
        colors_per_palette=16,
        max_palettes=8,  # SNES: 8 sprite palettes
        total_colors=256,  # SNES Mode 3/4 can do 256
        color_depth_bits=15,  # SNES: 15-bit color
        max_sprite_size=(64, 64),  # SNES supports up to 64x64
        recommended_sprite_size=(32, 32),
        max_sprite_colors=15,  # Per palette
        tile_size=(8, 8),
        max_unique_tiles=1024,  # SNES per layer
        max_bg_palettes=8,
        max_animation_frames=8,
        recommended_frame_counts={
            'idle': 4, 'walk': 6, 'run': 8, 'attack': 5,
            'hurt': 3, 'death': 5, 'jump': 4,
        },
        prompt_style="16-bit pixel art for Super Nintendo, vibrant colors (16 per palette), "
                    "smooth shading, subtle color gradients, detailed sprites with depth, "
                    "SNES/Genesis aesthetic, clean pixel edges, dithering for smooth transitions",
        dithering_allowed=True,
        anti_aliasing_allowed=False,
        gradient_allowed=True,
        platforms=['genesis', 'megadrive', 'snes', 'sfc', 'pce', 'turbografx', 'amiga'],
    ),

    AssetTier.STANDARD_PLUS: AssetTierSpec(
        tier=AssetTier.STANDARD_PLUS,
        name="STANDARD_PLUS",
        peak_platform="Neo Geo",  # HAL_ASSET_PEAK_STANDARD_PLUS - 4096 colors, arcade
        colors_per_palette=16,  # Neo Geo: 16 per palette
        max_palettes=256,  # Neo Geo: 256 palettes!
        total_colors=4096,  # Neo Geo: 4096 on screen
        color_depth_bits=16,  # Neo Geo: 16-bit color
        max_sprite_size=(512, 512),  # Neo Geo huge sprites
        recommended_sprite_size=(64, 64),
        max_sprite_colors=15,  # Per palette, but 256 palettes
        tile_size=(16, 16),  # Neo Geo uses 16x16 tiles
        max_unique_tiles=4096,
        max_bg_palettes=256,
        max_animation_frames=12,
        recommended_frame_counts={
            'idle': 6, 'walk': 8, 'run': 10, 'attack': 6,
            'hurt': 4, 'death': 8, 'jump': 6,
        },
        prompt_style="Arcade-quality 16-bit pixel art for Neo Geo, rich palette (4096 colors), "
                    "smooth color gradients, detailed shading with highlights and shadows, "
                    "Neo Geo/arcade quality, professional sprite work, subtle dithering",
        dithering_allowed=True,
        anti_aliasing_allowed=True,  # Very subtle, pixel-respectful
        gradient_allowed=True,
        platforms=['neogeo', 'segacd', '32x', 'x68000'],
    ),

    AssetTier.EXTENDED: AssetTierSpec(
        tier=AssetTier.EXTENDED,
        name="EXTENDED",
        peak_platform="DS",  # HAL_ASSET_PEAK_EXTENDED - 262K colors, dual screen
        colors_per_palette=256,
        max_palettes=16,
        total_colors=262144,  # DS: 18-bit color
        color_depth_bits=18,  # DS: 6 bits per channel
        max_sprite_size=(128, 128),  # DS OAM supports large sprites
        recommended_sprite_size=(64, 64),
        max_sprite_colors=255,
        tile_size=(8, 8),
        max_unique_tiles=8192,
        max_bg_palettes=16,
        max_animation_frames=16,
        recommended_frame_counts={
            'idle': 8, 'walk': 10, 'run': 12, 'attack': 8,
            'hurt': 4, 'death': 10, 'jump': 8,
        },
        prompt_style="High-fidelity pixel art for Nintendo DS, full color range (262K), "
                    "smooth anti-aliased edges where appropriate, detailed shading, "
                    "multiple highlight and shadow levels, GBA/DS quality, modern retro",
        dithering_allowed=True,
        anti_aliasing_allowed=True,
        gradient_allowed=True,
        platforms=['gba', 'nds', 'psp'],
    ),
}


# =============================================================================
# Platform to Tier Mapping
# =============================================================================

PLATFORM_TIER_MAP: Dict[str, HardwareTier] = {}
for tier, spec in TIER_SPECS.items():
    for platform in spec.platforms:
        PLATFORM_TIER_MAP[platform] = tier

# Add aliases
PLATFORM_TIER_MAP.update({
    'fc': HardwareTier.MINIMAL,
    'md': HardwareTier.STANDARD,
    'sfc': HardwareTier.STANDARD,
    'pce': HardwareTier.STANDARD,
    'tg16': HardwareTier.STANDARD,
})


# =============================================================================
# Platform-Specific Palette Configuration
# =============================================================================

@dataclass
class PlatformPaletteConfig:
    """
    Bespoke palette configuration for a specific platform.

    Each platform has unique color encoding, palette constraints,
    and optimal quantization strategies.
    """

    platform: str

    # Color encoding
    bits_per_channel: int  # R, G, B bits each
    color_format: str  # "RGB", "BGR", "RGBI", etc.
    total_palette_colors: int  # Master palette size

    # Palette structure
    colors_per_subpalette: int
    num_subpalettes: int
    shared_color_index: Optional[int] = None  # e.g., NES shares color 0

    # Transparency
    transparent_index: Optional[int] = 0  # Which index is transparent
    transparency_required: bool = True

    # Special constraints
    fixed_colors: Dict[int, Tuple[int, int, int]] = field(default_factory=dict)
    prohibited_colors: List[Tuple[int, int, int]] = field(default_factory=list)

    # Quantization hints
    prefer_saturated: bool = False  # Boost saturation before quantize
    luminance_weight: float = 1.0  # Weight luminance in color matching
    hue_preservation: bool = False  # Try to preserve hue over exact color

    # Hardware palette (if platform has fixed master palette)
    hardware_palette: Optional[List[Tuple[int, int, int]]] = None


# =============================================================================
# Platform Palette Definitions
# =============================================================================

# NES Master Palette (2C02 NTSC, commonly used approximation)
NES_MASTER_PALETTE = [
    # Row 0 (Grays + Dark Colors)
    (0x7C, 0x7C, 0x7C), (0x00, 0x00, 0xFC), (0x00, 0x00, 0xBC), (0x44, 0x28, 0xBC),
    (0x94, 0x00, 0x84), (0xA8, 0x00, 0x20), (0xA8, 0x10, 0x00), (0x88, 0x14, 0x00),
    (0x50, 0x30, 0x00), (0x00, 0x78, 0x00), (0x00, 0x68, 0x00), (0x00, 0x58, 0x00),
    (0x00, 0x40, 0x58), (0x00, 0x00, 0x00), (0x00, 0x00, 0x00), (0x00, 0x00, 0x00),
    # Row 1 (Midtones)
    (0xBC, 0xBC, 0xBC), (0x00, 0x78, 0xF8), (0x00, 0x58, 0xF8), (0x68, 0x44, 0xFC),
    (0xD8, 0x00, 0xCC), (0xE4, 0x00, 0x58), (0xF8, 0x38, 0x00), (0xE4, 0x5C, 0x10),
    (0xAC, 0x7C, 0x00), (0x00, 0xB8, 0x00), (0x00, 0xA8, 0x00), (0x00, 0xA8, 0x44),
    (0x00, 0x88, 0x88), (0x00, 0x00, 0x00), (0x00, 0x00, 0x00), (0x00, 0x00, 0x00),
    # Row 2 (Highlights)
    (0xF8, 0xF8, 0xF8), (0x3C, 0xBC, 0xFC), (0x68, 0x88, 0xFC), (0x98, 0x78, 0xF8),
    (0xF8, 0x78, 0xF8), (0xF8, 0x58, 0x98), (0xF8, 0x78, 0x58), (0xFC, 0xA0, 0x44),
    (0xF8, 0xB8, 0x00), (0xB8, 0xF8, 0x18), (0x58, 0xD8, 0x54), (0x58, 0xF8, 0x98),
    (0x00, 0xE8, 0xD8), (0x78, 0x78, 0x78), (0x00, 0x00, 0x00), (0x00, 0x00, 0x00),
    # Row 3 (Pastels)
    (0xFC, 0xFC, 0xFC), (0xA4, 0xE4, 0xFC), (0xB8, 0xB8, 0xF8), (0xD8, 0xB8, 0xF8),
    (0xF8, 0xB8, 0xF8), (0xF8, 0xA4, 0xC0), (0xF0, 0xD0, 0xB0), (0xFC, 0xE0, 0xA8),
    (0xF8, 0xD8, 0x78), (0xD8, 0xF8, 0x78), (0xB8, 0xF8, 0xB8), (0xB8, 0xF8, 0xD8),
    (0x00, 0xFC, 0xFC), (0xF8, 0xD8, 0xF8), (0x00, 0x00, 0x00), (0x00, 0x00, 0x00),
]

# Game Boy 4-shade palette (green-tinted classic)
GB_PALETTE = [
    (0x0F, 0x38, 0x0F),  # Darkest
    (0x30, 0x62, 0x30),  # Dark
    (0x8B, 0xAC, 0x0F),  # Light
    (0x9B, 0xBC, 0x0F),  # Lightest
]

# SMS Master Palette (6-bit, 64 colors)
SMS_PALETTE = []
for r in range(4):
    for g in range(4):
        for b in range(4):
            SMS_PALETTE.append((r * 85, g * 85, b * 85))


PLATFORM_PALETTE_CONFIGS: Dict[str, PlatformPaletteConfig] = {
    # -------------------------------------------------------------------------
    # MINIMAL Tier
    # -------------------------------------------------------------------------
    'nes': PlatformPaletteConfig(
        platform='nes',
        bits_per_channel=6,  # 2C02 uses 6-bit DAC
        color_format='RGB',
        total_palette_colors=64,
        colors_per_subpalette=4,
        num_subpalettes=4,  # 4 sprite palettes
        shared_color_index=0,  # All palettes share color 0
        transparent_index=0,
        transparency_required=True,
        luminance_weight=1.2,  # NES looks better with luminance-weighted matching
        hardware_palette=NES_MASTER_PALETTE,
    ),

    'famicom': PlatformPaletteConfig(
        platform='famicom',
        bits_per_channel=6,
        color_format='RGB',
        total_palette_colors=64,
        colors_per_subpalette=4,
        num_subpalettes=4,
        shared_color_index=0,
        transparent_index=0,
        transparency_required=True,
        luminance_weight=1.2,
        hardware_palette=NES_MASTER_PALETTE,
    ),

    'gb': PlatformPaletteConfig(
        platform='gb',
        bits_per_channel=2,  # 4 shades
        color_format='GRAY',
        total_palette_colors=4,
        colors_per_subpalette=4,
        num_subpalettes=1,
        transparent_index=0,
        transparency_required=True,
        hardware_palette=GB_PALETTE,
    ),

    'gbc': PlatformPaletteConfig(
        platform='gbc',
        bits_per_channel=5,  # 15-bit color
        color_format='RGB',
        total_palette_colors=32768,  # 15-bit
        colors_per_subpalette=4,
        num_subpalettes=8,  # 8 sprite palettes
        transparent_index=0,
        transparency_required=True,
        prefer_saturated=True,  # GBC colors look better saturated
    ),

    'c64': PlatformPaletteConfig(
        platform='c64',
        bits_per_channel=4,
        color_format='RGBI',  # 16 fixed colors
        total_palette_colors=16,
        colors_per_subpalette=4,  # Multicolor mode
        num_subpalettes=1,
        shared_color_index=0,  # Background color shared
        transparent_index=0,
        transparency_required=False,
        # C64 16-color palette (VIC-II)
        hardware_palette=[
            (0x00, 0x00, 0x00), (0xFF, 0xFF, 0xFF), (0x88, 0x00, 0x00), (0xAA, 0xFF, 0xEE),
            (0xCC, 0x44, 0xCC), (0x00, 0xCC, 0x55), (0x00, 0x00, 0xAA), (0xEE, 0xEE, 0x77),
            (0xDD, 0x88, 0x55), (0x66, 0x44, 0x00), (0xFF, 0x77, 0x77), (0x33, 0x33, 0x33),
            (0x77, 0x77, 0x77), (0xAA, 0xFF, 0x66), (0x00, 0x88, 0xFF), (0xBB, 0xBB, 0xBB),
        ],
    ),

    # -------------------------------------------------------------------------
    # MINIMAL_PLUS Tier
    # -------------------------------------------------------------------------
    'sms': PlatformPaletteConfig(
        platform='sms',
        bits_per_channel=2,  # 6-bit total (2 per channel)
        color_format='RGB',
        total_palette_colors=64,
        colors_per_subpalette=16,
        num_subpalettes=2,  # 1 sprite + 1 BG
        transparent_index=0,
        transparency_required=True,
        hardware_palette=SMS_PALETTE,
    ),

    'gamegear': PlatformPaletteConfig(
        platform='gamegear',
        bits_per_channel=4,  # 12-bit color
        color_format='RGB',
        total_palette_colors=4096,
        colors_per_subpalette=16,
        num_subpalettes=2,
        transparent_index=0,
        transparency_required=True,
    ),

    # -------------------------------------------------------------------------
    # STANDARD Tier
    # -------------------------------------------------------------------------
    'genesis': PlatformPaletteConfig(
        platform='genesis',
        bits_per_channel=3,  # 9-bit color (3 per channel)
        color_format='BGR',  # Genesis uses BGR
        total_palette_colors=512,
        colors_per_subpalette=16,
        num_subpalettes=4,
        transparent_index=0,
        transparency_required=True,
        # Shadow/highlight mode prohibited colors (optional)
        prohibited_colors=[],
    ),

    'megadrive': PlatformPaletteConfig(
        platform='megadrive',
        bits_per_channel=3,
        color_format='BGR',
        total_palette_colors=512,
        colors_per_subpalette=16,
        num_subpalettes=4,
        transparent_index=0,
        transparency_required=True,
    ),

    'snes': PlatformPaletteConfig(
        platform='snes',
        bits_per_channel=5,  # 15-bit color
        color_format='BGR',  # SNES uses BGR
        total_palette_colors=32768,
        colors_per_subpalette=16,
        num_subpalettes=8,
        transparent_index=0,
        transparency_required=True,
        prefer_saturated=False,  # SNES has great color depth
    ),

    'sfc': PlatformPaletteConfig(
        platform='sfc',
        bits_per_channel=5,
        color_format='BGR',
        total_palette_colors=32768,
        colors_per_subpalette=16,
        num_subpalettes=8,
        transparent_index=0,
        transparency_required=True,
    ),

    'pce': PlatformPaletteConfig(
        platform='pce',
        bits_per_channel=3,  # 9-bit color
        color_format='RGB',
        total_palette_colors=512,
        colors_per_subpalette=16,
        num_subpalettes=16,  # More palettes than Genesis
        transparent_index=0,
        transparency_required=True,
    ),

    # -------------------------------------------------------------------------
    # STANDARD_PLUS Tier
    # -------------------------------------------------------------------------
    'neogeo': PlatformPaletteConfig(
        platform='neogeo',
        bits_per_channel=5,  # 16-bit color (5-5-5 + dark bit)
        color_format='RGB',
        total_palette_colors=65536,
        colors_per_subpalette=16,
        num_subpalettes=256,  # 256 palettes!
        transparent_index=0,
        transparency_required=True,
    ),

    # -------------------------------------------------------------------------
    # EXTENDED Tier
    # -------------------------------------------------------------------------
    'gba': PlatformPaletteConfig(
        platform='gba',
        bits_per_channel=5,  # 15-bit color
        color_format='BGR',
        total_palette_colors=32768,
        colors_per_subpalette=16,  # Can also use 256-color mode
        num_subpalettes=16,
        transparent_index=0,
        transparency_required=True,
    ),

    'nds': PlatformPaletteConfig(
        platform='nds',
        bits_per_channel=5,  # 15/18-bit color
        color_format='BGR',
        total_palette_colors=262144,  # 18-bit in extended modes
        colors_per_subpalette=256,
        num_subpalettes=16,
        transparent_index=0,
        transparency_required=True,
    ),
}


# =============================================================================
# Downsampling Configuration
# =============================================================================

@dataclass
class DownsampleConfig:
    """Configuration for downsampling from one tier to another."""

    source_tier: HardwareTier
    target_tier: HardwareTier

    # Color reduction method
    color_reduction: str = "median_cut"  # median_cut, k_means, octree

    # Dithering for color reduction
    apply_dithering: bool = False
    dither_method: str = "ordered"  # ordered, floyd_steinberg, none
    dither_strength: float = 0.5

    # Sprite size handling
    resize_method: str = "NEAREST"  # NEAREST, LANCZOS, BILINEAR

    # Palette optimization
    optimize_palette: bool = True
    preserve_transparency: bool = True

    # Quality settings
    sharpen_after_resize: bool = False
    contrast_boost: float = 1.0  # 1.0 = no change
    saturation_boost: float = 1.0  # 1.0 = no change

    # Platform-specific palette mapping
    use_hardware_palette: bool = False  # Force mapping to hardware palette
    palette_matching_method: str = "euclidean"  # euclidean, weighted_luminance, perceptual


# Pre-configured downsample paths
DOWNSAMPLE_CONFIGS: Dict[Tuple[HardwareTier, HardwareTier], DownsampleConfig] = {
    # STANDARD to MINIMAL (Genesis/SNES → NES)
    (HardwareTier.STANDARD, HardwareTier.MINIMAL): DownsampleConfig(
        source_tier=HardwareTier.STANDARD,
        target_tier=HardwareTier.MINIMAL,
        color_reduction="median_cut",
        apply_dithering=False,  # NES doesn't do dithering well
        resize_method="NEAREST",
        contrast_boost=1.1,  # Boost contrast for limited palette
        saturation_boost=1.15,  # Boost saturation for NES vibrant look
        use_hardware_palette=True,  # Map to NES master palette
        palette_matching_method="weighted_luminance",
    ),

    # STANDARD to MINIMAL_PLUS (Genesis → SMS)
    (HardwareTier.STANDARD, HardwareTier.MINIMAL_PLUS): DownsampleConfig(
        source_tier=HardwareTier.STANDARD,
        target_tier=HardwareTier.MINIMAL_PLUS,
        color_reduction="median_cut",
        apply_dithering=True,
        dither_method="ordered",
        dither_strength=0.3,  # Subtle ordered dithering
        resize_method="NEAREST",
        use_hardware_palette=True,
        palette_matching_method="euclidean",
    ),

    # EXTENDED to STANDARD (GBA → Genesis)
    (HardwareTier.EXTENDED, HardwareTier.STANDARD): DownsampleConfig(
        source_tier=HardwareTier.EXTENDED,
        target_tier=HardwareTier.STANDARD,
        color_reduction="k_means",
        apply_dithering=True,
        dither_method="ordered",
        dither_strength=0.4,
        resize_method="LANCZOS",  # Higher quality for significant reduction
        palette_matching_method="perceptual",
    ),

    # STANDARD_PLUS to STANDARD (Neo Geo → SNES)
    (HardwareTier.STANDARD_PLUS, HardwareTier.STANDARD): DownsampleConfig(
        source_tier=HardwareTier.STANDARD_PLUS,
        target_tier=HardwareTier.STANDARD,
        color_reduction="median_cut",
        apply_dithering=True,
        dither_method="ordered",
        dither_strength=0.35,
        resize_method="LANCZOS",
        palette_matching_method="perceptual",
    ),

    # EXTENDED to MINIMAL (GBA → NES) - Extreme downgrade
    (HardwareTier.EXTENDED, HardwareTier.MINIMAL): DownsampleConfig(
        source_tier=HardwareTier.EXTENDED,
        target_tier=HardwareTier.MINIMAL,
        color_reduction="median_cut",
        apply_dithering=False,
        resize_method="NEAREST",
        sharpen_after_resize=True,
        contrast_boost=1.2,
        saturation_boost=1.2,
        use_hardware_palette=True,
        palette_matching_method="weighted_luminance",
    ),

    # MINIMAL_PLUS to MINIMAL (SMS → NES)
    (HardwareTier.MINIMAL_PLUS, HardwareTier.MINIMAL): DownsampleConfig(
        source_tier=HardwareTier.MINIMAL_PLUS,
        target_tier=HardwareTier.MINIMAL,
        color_reduction="median_cut",
        apply_dithering=False,
        resize_method="NEAREST",
        contrast_boost=1.1,
        use_hardware_palette=True,
        palette_matching_method="weighted_luminance",
    ),

    # STANDARD_PLUS to MINIMAL (Neo Geo → NES)
    (HardwareTier.STANDARD_PLUS, HardwareTier.MINIMAL): DownsampleConfig(
        source_tier=HardwareTier.STANDARD_PLUS,
        target_tier=HardwareTier.MINIMAL,
        color_reduction="median_cut",
        apply_dithering=False,
        resize_method="NEAREST",
        sharpen_after_resize=True,
        contrast_boost=1.2,
        saturation_boost=1.15,
        use_hardware_palette=True,
        palette_matching_method="weighted_luminance",
    ),

    # STANDARD_PLUS to MINIMAL_PLUS (Neo Geo → SMS)
    (HardwareTier.STANDARD_PLUS, HardwareTier.MINIMAL_PLUS): DownsampleConfig(
        source_tier=HardwareTier.STANDARD_PLUS,
        target_tier=HardwareTier.MINIMAL_PLUS,
        color_reduction="median_cut",
        apply_dithering=True,
        dither_method="ordered",
        dither_strength=0.3,
        resize_method="NEAREST",
        use_hardware_palette=True,
        palette_matching_method="euclidean",
    ),

    # EXTENDED to MINIMAL_PLUS (GBA → SMS)
    (HardwareTier.EXTENDED, HardwareTier.MINIMAL_PLUS): DownsampleConfig(
        source_tier=HardwareTier.EXTENDED,
        target_tier=HardwareTier.MINIMAL_PLUS,
        color_reduction="median_cut",
        apply_dithering=True,
        dither_method="ordered",
        dither_strength=0.35,
        resize_method="NEAREST",
        sharpen_after_resize=True,
        use_hardware_palette=True,
        palette_matching_method="euclidean",
    ),

    # EXTENDED to STANDARD_PLUS (GBA → Neo Geo)
    (HardwareTier.EXTENDED, HardwareTier.STANDARD_PLUS): DownsampleConfig(
        source_tier=HardwareTier.EXTENDED,
        target_tier=HardwareTier.STANDARD_PLUS,
        color_reduction="k_means",
        apply_dithering=False,  # Neo Geo has enough colors
        resize_method="LANCZOS",
        palette_matching_method="perceptual",
    ),
}


# =============================================================================
# Platform-Specific Palette Functions
# =============================================================================

def get_platform_palette_config(platform: str) -> Optional[PlatformPaletteConfig]:
    """Get palette configuration for a specific platform."""
    return PLATFORM_PALETTE_CONFIGS.get(platform.lower())


def get_nearest_palette_color(
    color: Tuple[int, int, int],
    palette: List[Tuple[int, int, int]],
    method: str = "euclidean",
) -> int:
    """
    Find the nearest color in a palette.

    Args:
        color: RGB tuple to match
        palette: List of RGB tuples
        method: "euclidean", "weighted_luminance", or "perceptual"

    Returns:
        Index of nearest color in palette
    """
    if method == "euclidean":
        # Simple RGB distance
        distances = [
            (color[0] - p[0]) ** 2 + (color[1] - p[1]) ** 2 + (color[2] - p[2]) ** 2
            for p in palette
        ]
    elif method == "weighted_luminance":
        # Weight by human luminance perception
        distances = [
            0.299 * (color[0] - p[0]) ** 2 +
            0.587 * (color[1] - p[1]) ** 2 +
            0.114 * (color[2] - p[2]) ** 2
            for p in palette
        ]
    elif method == "perceptual":
        # CIE76-inspired perceptual distance (simplified)
        def to_lab_approx(rgb):
            # Simplified sRGB to Lab approximation
            r, g, b = [c / 255.0 for c in rgb]
            l = 0.2126 * r + 0.7152 * g + 0.0722 * b
            a = 1.4749 * (r - l)
            b_ch = 0.6223 * (b - l)
            return (l * 100, a * 100, b_ch * 100)

        lab_color = to_lab_approx(color)
        distances = []
        for p in palette:
            lab_p = to_lab_approx(p)
            d = ((lab_color[0] - lab_p[0]) ** 2 +
                 (lab_color[1] - lab_p[1]) ** 2 +
                 (lab_color[2] - lab_p[2]) ** 2)
            distances.append(d)
    else:
        distances = [
            (color[0] - p[0]) ** 2 + (color[1] - p[1]) ** 2 + (color[2] - p[2]) ** 2
            for p in palette
        ]

    return distances.index(min(distances))


def quantize_to_bits(value: int, bits: int) -> int:
    """Quantize an 8-bit value to fewer bits and scale back."""
    shift = 8 - bits
    quantized = (value >> shift) << shift
    # Fill lower bits to maintain range
    if bits < 8:
        fill = quantized >> bits
        quantized |= fill
    return min(255, quantized)


def apply_platform_color_encoding(
    color: Tuple[int, int, int],
    config: PlatformPaletteConfig,
) -> Tuple[int, int, int]:
    """
    Apply platform-specific color encoding.

    Reduces color precision to match platform capabilities.
    """
    r, g, b = color
    bits = config.bits_per_channel

    r = quantize_to_bits(r, bits)
    g = quantize_to_bits(g, bits)
    b = quantize_to_bits(b, bits)

    return (r, g, b)


# =============================================================================
# Tier Functions
# =============================================================================

def get_tier_for_platform(platform: str) -> HardwareTier:
    """Get the hardware tier for a given platform."""
    platform_lower = platform.lower()
    if platform_lower in PLATFORM_TIER_MAP:
        return PLATFORM_TIER_MAP[platform_lower]
    # Default to MINIMAL for unknown platforms
    return HardwareTier.MINIMAL


def get_tier_spec(tier: HardwareTier) -> TierSpec:
    """Get the full specification for a tier."""
    return TIER_SPECS[tier]


def get_generation_tier(target_platforms: List[str]) -> HardwareTier:
    """
    Determine the optimal generation tier for a set of target platforms.

    Returns the HIGHEST tier among the targets, so we generate at maximum
    quality and downsample to lower tiers.
    """
    if not target_platforms:
        return HardwareTier.STANDARD  # Safe default

    tiers = [get_tier_for_platform(p) for p in target_platforms]
    return max(tiers)


def get_downsample_config(
    source_tier: HardwareTier,
    target_tier: HardwareTier,
) -> DownsampleConfig:
    """Get downsample configuration for a tier transition."""

    if source_tier == target_tier:
        # No downsampling needed
        return DownsampleConfig(
            source_tier=source_tier,
            target_tier=target_tier,
        )

    if source_tier < target_tier:
        raise ValueError(f"Cannot upsample from {source_tier.name} to {target_tier.name}")

    # Check for pre-configured path
    key = (source_tier, target_tier)
    if key in DOWNSAMPLE_CONFIGS:
        return DOWNSAMPLE_CONFIGS[key]

    # Create default config for this transition
    return DownsampleConfig(
        source_tier=source_tier,
        target_tier=target_tier,
        color_reduction="median_cut",
        apply_dithering=target_tier >= HardwareTier.MINIMAL_PLUS,
        resize_method="NEAREST" if target_tier <= HardwareTier.MINIMAL else "LANCZOS",
    )


def get_prompt_for_tier(
    tier: HardwareTier,
    asset_type: str = "sprite",
    custom_hints: Optional[str] = None,
) -> str:
    """
    Build a generation prompt optimized for the given tier.

    Args:
        tier: Target hardware tier
        asset_type: "sprite", "background", "tile"
        custom_hints: Additional style hints

    Returns:
        Complete prompt style string
    """
    spec = TIER_SPECS[tier]

    base_prompt = spec.prompt_style

    # Add asset-type specific guidance
    type_hints = {
        'sprite': f"Character sprite with clear silhouette, "
                 f"max {spec.max_sprite_colors} colors, "
                 f"optimized for {spec.recommended_sprite_size[0]}x{spec.recommended_sprite_size[1]} pixels",

        'background': f"Tileable background, "
                     f"optimized for {spec.tile_size[0]}x{spec.tile_size[1]} tile grid, "
                     f"max {spec.max_unique_tiles} unique tiles",

        'tile': f"Seamlessly tileable pattern, "
               f"exactly {spec.tile_size[0]}x{spec.tile_size[1]} pixels, "
               f"max {spec.colors_per_palette} colors",
    }

    prompt_parts = [base_prompt]

    if asset_type in type_hints:
        prompt_parts.append(type_hints[asset_type])

    # Add tier-specific constraints
    if not spec.anti_aliasing_allowed:
        prompt_parts.append("absolutely no anti-aliasing or smoothing")
    if not spec.gradient_allowed:
        prompt_parts.append("no color gradients, use flat colors")
    if not spec.dithering_allowed:
        prompt_parts.append("no dithering patterns")

    if custom_hints:
        prompt_parts.append(custom_hints)

    return ", ".join(prompt_parts)


def get_animation_frames(tier: HardwareTier, anim_name: str) -> int:
    """Get recommended frame count for an animation at a given tier."""
    spec = TIER_SPECS[tier]
    return spec.recommended_frame_counts.get(anim_name, 4)


def can_downsample(source_tier: HardwareTier, target_tier: HardwareTier) -> bool:
    """Check if downsampling from source to target is valid."""
    return source_tier >= target_tier


def get_downsample_chain(
    source_tier: HardwareTier,
    target_tier: HardwareTier,
) -> List[HardwareTier]:
    """
    Get the chain of tiers for progressive downsampling.

    For extreme tier differences, it may be better to downsample
    in steps rather than all at once.
    """
    if source_tier <= target_tier:
        return [target_tier]

    tier_diff = source_tier - target_tier

    if tier_diff <= 1:
        # Direct downsampling is fine
        return [target_tier]

    # For larger differences, create intermediate steps
    chain = []
    current = source_tier
    while current > target_tier:
        current = HardwareTier(current - 1)
        chain.append(current)

    return chain


# =============================================================================
# Tier Comparison Utilities
# =============================================================================

def compare_tiers(tier_a: HardwareTier, tier_b: HardwareTier) -> Dict[str, Any]:
    """Compare two tiers and show the differences."""
    spec_a = TIER_SPECS[tier_a]
    spec_b = TIER_SPECS[tier_b]

    return {
        'colors': {
            tier_a.name: spec_a.total_colors,
            tier_b.name: spec_b.total_colors,
            'reduction': spec_a.total_colors - spec_b.total_colors,
        },
        'sprite_size': {
            tier_a.name: spec_a.max_sprite_size,
            tier_b.name: spec_b.max_sprite_size,
        },
        'tiles': {
            tier_a.name: spec_a.max_unique_tiles,
            tier_b.name: spec_b.max_unique_tiles,
            'reduction': spec_a.max_unique_tiles - spec_b.max_unique_tiles,
        },
        'animation_frames': {
            tier_a.name: spec_a.max_animation_frames,
            tier_b.name: spec_b.max_animation_frames,
        },
        'features_lost': {
            'dithering': spec_a.dithering_allowed and not spec_b.dithering_allowed,
            'anti_aliasing': spec_a.anti_aliasing_allowed and not spec_b.anti_aliasing_allowed,
            'gradients': spec_a.gradient_allowed and not spec_b.gradient_allowed,
        },
    }


def print_tier_summary():
    """Print a summary of all tiers."""
    print("ARDK Hardware Tier System")
    print("=" * 60)
    print()

    for tier in HardwareTier:
        spec = TIER_SPECS[tier]
        print(f"Tier {tier.value}: {spec.name}")
        print(f"  Colors: {spec.total_colors} on screen ({spec.colors_per_palette}/palette)")
        print(f"  Sprites: up to {spec.max_sprite_size[0]}x{spec.max_sprite_size[1]}")
        print(f"  Tiles: {spec.max_unique_tiles} unique")
        print(f"  Animation: up to {spec.max_animation_frames} frames")
        print(f"  Platforms: {', '.join(spec.platforms)}")
        print()


# =============================================================================
# CLI Entry Point
# =============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='ARDK Tier System Information')
    parser.add_argument('--summary', action='store_true', help='Show tier summary')
    parser.add_argument('--platform', help='Show tier for platform')
    parser.add_argument('--compare', nargs=2, help='Compare two tiers')
    parser.add_argument('--downsample', nargs=2, help='Show downsample config')

    args = parser.parse_args()

    if args.summary:
        print_tier_summary()
    elif args.platform:
        tier = get_tier_for_platform(args.platform)
        spec = TIER_SPECS[tier]
        print(f"{args.platform} → Tier {tier.value}: {spec.name}")
        print(f"Prompt style: {spec.prompt_style[:100]}...")
    elif args.compare:
        tier_a = HardwareTier[args.compare[0].upper()]
        tier_b = HardwareTier[args.compare[1].upper()]
        import json
        print(json.dumps(compare_tiers(tier_a, tier_b), indent=2))
    elif args.downsample:
        tier_a = HardwareTier[args.downsample[0].upper()]
        tier_b = HardwareTier[args.downsample[1].upper()]
        config = get_downsample_config(tier_a, tier_b)
        print(f"Downsample: {tier_a.name} → {tier_b.name}")
        print(f"  Color reduction: {config.color_reduction}")
        print(f"  Dithering: {config.apply_dithering} ({config.dither_method})")
        print(f"  Resize: {config.resize_method}")
    else:
        parser.print_help()
