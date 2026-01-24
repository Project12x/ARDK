"""
NES Platform Configuration - Hardware constraints and generation settings.

The NES has strict limitations:
- 8KB CHR banks (256 tiles each)
- 4 colors per palette (including transparent)
- 4 background palettes, 4 sprite palettes
- 8x8 or 8x16 sprite modes
- Horizontal/vertical flip via attributes
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any


# =============================================================================
# Hardware Configuration
# =============================================================================

@dataclass
class NESHardwareConfig:
    """NES hardware specifications."""

    # CPU/Memory
    cpu: str = "Ricoh 2A03 (6502)"
    ram: int = 2048  # 2KB internal RAM
    vram: int = 2048  # 2KB VRAM

    # Graphics
    ppu: str = "Ricoh 2C02"
    screen_width: int = 256
    screen_height: int = 240
    visible_height: int = 224  # NTSC safe area

    # Tiles
    tile_width: int = 8
    tile_height: int = 8
    chr_bank_size: int = 8192  # 8KB per CHR bank
    tiles_per_bank: int = 256  # 256 8x8 tiles per 8KB

    # Palettes
    colors_per_palette: int = 4  # Including transparent
    bg_palettes: int = 4
    sprite_palettes: int = 4
    total_system_colors: int = 54  # NES master palette

    # Sprites
    max_sprites: int = 64
    sprites_per_scanline: int = 8
    sprite_modes: List[Tuple[int, int]] = field(
        default_factory=lambda: [(8, 8), (8, 16)]
    )

    # Mappers
    common_mappers: Dict[str, int] = field(
        default_factory=lambda: {
            'NROM': 0,      # 32KB PRG, 8KB CHR (no banking)
            'MMC1': 1,      # 256KB PRG, 128KB CHR
            'UNROM': 2,     # 256KB PRG, CHR-RAM
            'CNROM': 3,     # 32KB PRG, 32KB CHR
            'MMC3': 4,      # 512KB PRG, 256KB CHR (IRQ)
            'MMC5': 5,      # 1MB PRG, 1MB CHR (advanced)
        }
    )


# =============================================================================
# Asset Generation Configuration
# =============================================================================

NES_CONFIG = NESHardwareConfig()

NES_ASSET_CONFIG = {
    # Tier identification
    'tier': 'MINIMAL',
    'tier_id': 0,

    # Tile constraints
    'max_tiles_per_bank': 256,
    'max_chr_banks': 2,  # Typical for MMC3
    'tile_size': (8, 8),
    'bits_per_pixel': 2,  # 2bpp = 4 colors

    # Color constraints
    'colors_per_palette': 4,
    'max_palettes': 4,  # Per plane (BG or sprite)
    'transparent_index': 0,  # Index 0 is always transparent

    # Sprite constraints
    'max_sprites': 64,
    'sprite_sizes': [(8, 8), (8, 16)],
    'max_metasprite_tiles': 16,  # Reasonable limit for 32x32

    # Animation constraints
    'max_animation_frames': 4,  # Per animation
    'suggested_frame_counts': {
        'idle': 2,
        'walk': 4,
        'run': 4,
        'attack': 3,
        'hurt': 2,
        'death': 3,
        'jump': 2,
    },

    # Parallax
    'max_parallax_layers': 3,  # Via MMC3 IRQ
    'parallax_method': 'scanline_irq',

    # Optimization
    'enable_flip_optimization': True,
    'enable_tile_deduplication': True,

    # Generation style
    'prompt_style': '8-bit NES pixel art, limited 4-color palette per sprite, chunky pixels, no anti-aliasing, black outlines optional',
    'resampling': 'NEAREST',
    'dithering': False,  # NES rarely uses dithering

    # ==========================================================================
    # CHR Animation Configuration (MMC3 Bank Swapping)
    # ==========================================================================
    # For animated backgrounds like Recca's fire or Kirby's water:
    # - Each animation frame needs its own 4KB CHR bank
    # - MMC3 can swap 1KB or 2KB banks independently
    # - 4 frames = 4 banks = 16KB CHR just for animated BG
    #
    # Bank layout recommendation:
    #   Banks 0-3:  Static BG tiles (always visible)
    #   Banks 4-7:  Animated BG frame 0
    #   Banks 8-11: Animated BG frame 1
    #   Banks 12-15: Animated BG frame 2
    #   Banks 16-19: Animated BG frame 3
    #   Banks 20+:  Sprite tiles
    # ==========================================================================
    'chr_animation': {
        'enabled': True,
        'max_animation_frames': 4,          # Max frames for animated backgrounds
        'banks_per_frame': 1,               # 4KB banks per animation frame
        'animation_bank_start': 4,          # First bank for animation data
        'static_bg_banks': 4,               # Banks reserved for static BG
        'sprite_bank_start': 20,            # First bank for sprites

        # Animation presets with recommended frame counts
        'presets': {
            'water': {'frames': 4, 'speed_ms': 150, 'banks': 4},
            'lava': {'frames': 4, 'speed_ms': 120, 'banks': 4},
            'fire': {'frames': 4, 'speed_ms': 80, 'banks': 4},
            'neon': {'frames': 2, 'speed_ms': 500, 'banks': 2},
            'stars': {'frames': 4, 'speed_ms': 300, 'banks': 4},
            'waterfall': {'frames': 4, 'speed_ms': 100, 'banks': 4},
        },

        # Total CHR budget for typical MMC3 game
        'total_chr_banks': 32,              # 256KB CHR ROM max
        'recommended_layout': {
            'static_bg': 4,                 # 4 banks = 16KB
            'animated_bg': 16,              # 16 banks = 64KB (4 frames × 4 banks)
            'sprites': 12,                  # 12 banks = 48KB
        },
    },

    # Status bar configuration (Kirby/Batman style)
    'status_bar': {
        'enabled': False,                   # Enable via feature flag in ASM
        'height_pixels': 40,                # Bottom 40 pixels frozen
        'scanline_split': 199,              # IRQ fires after this scanline
        'separate_chr_bank': False,         # Use different tiles for status bar
        'status_chr_bank': 24,              # CHR bank for status bar tiles
    },

    # NES-specific palette hints
    'palette_hints': {
        'background': 'Use $0F (black) as transparent, choose 3 contrasting colors',
        'sprite': 'First color is transparent, use bright colors for visibility',
        'recommended_bg_palettes': [
            [0x0F, 0x00, 0x10, 0x30],  # Grayscale
            [0x0F, 0x06, 0x16, 0x26],  # Warm (reds)
            [0x0F, 0x01, 0x11, 0x21],  # Cool (blues)
            [0x0F, 0x09, 0x19, 0x29],  # Greens
        ],
        'recommended_sprite_palettes': [
            [0x0F, 0x16, 0x27, 0x30],  # Player (warm + white)
            [0x0F, 0x05, 0x15, 0x25],  # Enemy 1 (purples)
            [0x0F, 0x0B, 0x1B, 0x2B],  # Enemy 2 (cyans)
            [0x0F, 0x06, 0x17, 0x28],  # Items (yellow/orange)
        ],
    },

    # File formats
    'chr_format': 'nes_2bpp',  # 16 bytes per tile
    'tilemap_format': 'raw',  # Tile indices
    'attribute_format': 'nes_attr',  # 2x2 metatile palettes
}


# =============================================================================
# Helper Functions
# =============================================================================

def get_nes_chr_size(tile_count: int) -> int:
    """Calculate CHR size in bytes for given tile count."""
    return tile_count * 16  # 16 bytes per 8x8 tile (2bpp)


def get_nes_tilemap_size(width_tiles: int, height_tiles: int) -> int:
    """Calculate tilemap size in bytes."""
    return width_tiles * height_tiles


def get_nes_attribute_size(width_tiles: int, height_tiles: int) -> int:
    """Calculate attribute table size in bytes."""
    # Attributes cover 4x4 tile areas (2x2 metatiles)
    attr_cols = (width_tiles + 3) // 4
    attr_rows = (height_tiles + 3) // 4
    return attr_cols * attr_rows


def nes_color_to_rgb(nes_color: int) -> Tuple[int, int, int]:
    """Convert NES palette index to approximate RGB."""
    # Simplified NES palette (not exact, but representative)
    NES_PALETTE_RGB = {
        0x0F: (0, 0, 0),        # Black
        0x00: (84, 84, 84),     # Dark gray
        0x10: (152, 152, 152),  # Gray
        0x20: (236, 236, 236),  # Light gray
        0x30: (252, 252, 252),  # White
        0x01: (0, 0, 168),      # Dark blue
        0x11: (0, 88, 248),     # Blue
        0x21: (68, 136, 252),   # Light blue
        0x02: (0, 0, 188),      # Dark purple
        0x12: (104, 68, 252),   # Purple
        0x22: (152, 120, 248),  # Light purple
        0x06: (168, 16, 0),     # Dark red
        0x16: (248, 56, 0),     # Red
        0x26: (248, 120, 88),   # Light red
        0x09: (0, 120, 0),      # Dark green
        0x19: (0, 184, 0),      # Green
        0x29: (88, 216, 84),    # Light green
        0x0C: (0, 136, 136),    # Dark cyan
        0x1C: (0, 232, 216),    # Cyan
        0x2C: (88, 248, 248),   # Light cyan
    }
    return NES_PALETTE_RGB.get(nes_color, (128, 128, 128))


def validate_nes_palette(palette: List[int]) -> List[str]:
    """Validate a palette for NES compatibility."""
    errors = []

    if len(palette) != 4:
        errors.append(f"Palette must have exactly 4 colors, got {len(palette)}")

    if palette and palette[0] != 0x0F:
        errors.append(f"First color should be $0F (black) for transparency, got ${palette[0]:02X}")

    for i, color in enumerate(palette):
        if not (0x00 <= color <= 0x3F):
            errors.append(f"Color {i} (${color:02X}) out of NES range ($00-$3F)")

    return errors
