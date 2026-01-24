"""
SNES Platform Configuration - Hardware constraints and generation settings.

The SNES has flexible graphics capabilities:
- Up to 1024 tiles per BG layer
- 16 colors per palette (varies by mode)
- 8 palettes for backgrounds
- Multiple BG modes (Mode 7 rotation/scaling)
- Large sprites up to 64x64
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Dict


# =============================================================================
# Hardware Configuration
# =============================================================================

@dataclass
class SNESHardwareConfig:
    """SNES hardware specifications."""

    # CPU/Memory
    cpu: str = "WDC 65C816 @ 3.58MHz"
    coprocessor: str = "SPC700 (audio)"
    ram: int = 131072  # 128KB main RAM
    vram: int = 65536  # 64KB VRAM

    # Graphics
    ppu: str = "S-PPU (PPU1 + PPU2)"
    screen_width: int = 256
    screen_height: int = 224  # Can be 239 in some modes
    color_depth: int = 15  # 15-bit color (32768 colors)

    # Tiles
    tile_width: int = 8
    tile_height: int = 8
    tile_16x16_available: bool = True  # BG can use 16x16 tiles

    # BG Modes
    bg_modes: Dict[int, str] = field(
        default_factory=lambda: {
            0: "4 layers, 4 colors each",
            1: "2 layers 16-color, 1 layer 4-color",
            2: "2 layers 16-color, offset-per-tile",
            3: "1 layer 256-color, 1 layer 16-color",
            4: "1 layer 256-color, 1 layer 4-color, offset",
            5: "1 layer 16-color hi-res, 1 layer 4-color",
            6: "1 layer 16-color hi-res, offset",
            7: "1 layer 256-color rotation/scaling",
        }
    )

    # Palettes
    cgram_size: int = 512  # 512 bytes = 256 15-bit colors
    max_colors: int = 256

    # Sprites
    max_sprites: int = 128
    sprites_per_scanline: int = 32
    sprite_tiles_per_scanline: int = 34
    sprite_sizes: List[Tuple[int, int]] = field(
        default_factory=lambda: [
            (8, 8), (16, 16), (32, 32), (64, 64),
        ]
    )


# =============================================================================
# Asset Generation Configuration
# =============================================================================

SNES_CONFIG = SNESHardwareConfig()

SNES_ASSET_CONFIG = {
    # Tier identification
    'tier': 'STANDARD',
    'tier_id': 2,

    # Tile constraints
    'max_tiles_per_layer': 1024,
    'max_chr_banks': 4,  # Practical limit
    'tile_size': (8, 8),
    'tile_16x16_mode': True,
    'bits_per_pixel': 4,  # Most common (Mode 1)

    # Color constraints (Mode 1 - most common)
    'colors_per_palette': 16,
    'max_palettes': 8,
    'transparent_index': 0,
    'total_colors': 128,  # 8 × 16 for sprites

    # Sprite constraints
    'max_sprites': 128,
    'sprite_sizes': [(8, 8), (16, 16), (32, 32), (64, 64)],
    'max_metasprite_tiles': 128,

    # Animation constraints
    'max_animation_frames': 8,
    'suggested_frame_counts': {
        'idle': 4,
        'walk': 6,
        'run': 8,
        'attack': 5,
        'hurt': 3,
        'death': 5,
        'jump': 4,
    },

    # Parallax
    'max_parallax_layers': 4,  # Up to 4 BG layers in Mode 0
    'parallax_methods': ['multi_bg', 'hdma', 'mode7'],

    # Optimization
    'enable_flip_optimization': True,
    'enable_tile_deduplication': True,
    'enable_priority': True,

    # Generation style
    'prompt_style': '16-bit SNES pixel art, rich color palette, smooth gradients, detailed sprites with soft shading',
    'resampling': 'LANCZOS',
    'dithering': True,

    # SNES-specific settings
    'color_math': True,  # Supports transparency/blending
    'mosaic': True,  # Hardware mosaic effect

    # Palette hints
    'palette_hints': {
        'color_format': '15-bit RGB (5-5-5)',
        'max_value': 31,  # Per channel
        'recommended_sprite_palettes': 8,
        'recommended_bg_palettes': 8,
    },

    # Mode-specific settings
    'modes': {
        1: {
            'name': 'Mode 1 (Standard)',
            'layers': 3,
            'bpp': [4, 4, 2],
            'colors': [16, 16, 4],
        },
        3: {
            'name': 'Mode 3 (256-color)',
            'layers': 2,
            'bpp': [8, 4],
            'colors': [256, 16],
        },
        7: {
            'name': 'Mode 7 (Rotation)',
            'layers': 1,
            'bpp': [8],
            'colors': [256],
            'special': 'rotation_scaling',
        },
    },

    # HDMA for effects
    'hdma_channels': 8,
    'hdma_uses': ['parallax', 'color_gradient', 'window', 'mosaic'],

    # File formats
    'chr_format': 'snes_4bpp',  # 32 bytes per tile (planar)
    'tilemap_format': 'snes_word',  # 16-bit per entry
}


# =============================================================================
# Helper Functions
# =============================================================================

def get_snes_chr_size(tile_count: int, bpp: int = 4) -> int:
    """Calculate CHR size in bytes for given tile count and color depth."""
    bytes_per_tile = (bpp * 8 * 8) // 8  # bpp × 64 pixels / 8 bits
    return tile_count * bytes_per_tile


def snes_rgb_to_cgram(r: int, g: int, b: int) -> int:
    """
    Convert 8-bit RGB to SNES CGRAM format.

    SNES uses 15-bit color (5 bits per channel).
    Format: 0BBBBBGG GGGRRRRR
    """
    r_5 = (r >> 3) & 0x1F
    g_5 = (g >> 3) & 0x1F
    b_5 = (b >> 3) & 0x1F

    return (b_5 << 10) | (g_5 << 5) | r_5


def cgram_to_rgb(cgram_color: int) -> Tuple[int, int, int]:
    """Convert SNES CGRAM color to 8-bit RGB."""
    r = (cgram_color & 0x1F) * 8
    g = ((cgram_color >> 5) & 0x1F) * 8
    b = ((cgram_color >> 10) & 0x1F) * 8
    return (r, g, b)


def get_snes_tilemap_entry(
    tile_index: int,
    palette: int = 0,
    priority: bool = False,
    h_flip: bool = False,
    v_flip: bool = False,
) -> int:
    """
    Create a SNES tilemap entry word.

    Format (16-bit):
    VHOOPPPC CCTTTTTT TTTT
    V = Vertical flip
    H = Horizontal flip
    OO = BG priority (0-1 for most modes)
    PPP = Palette (0-7)
    C = High bit of character number (for >256 tiles)
    T = Tile number (low 10 bits)
    """
    entry = tile_index & 0x3FF
    entry |= (palette & 0x07) << 10
    if priority:
        entry |= 0x2000
    if h_flip:
        entry |= 0x4000
    if v_flip:
        entry |= 0x8000
    return entry


def get_mode_info(mode: int) -> Dict:
    """Get information about a SNES BG mode."""
    modes = SNES_ASSET_CONFIG['modes']
    return modes.get(mode, modes[1])


def validate_snes_palette(palette: List[int], bpp: int = 4) -> List[str]:
    """Validate a palette for SNES compatibility."""
    errors = []

    max_colors = 2 ** bpp
    if len(palette) > max_colors:
        errors.append(f"Palette has {len(palette)} colors, max is {max_colors} for {bpp}bpp")

    for i, color in enumerate(palette):
        if color > 0x7FFF:
            errors.append(f"Color {i} (${color:04X}) exceeds SNES 15-bit range")

    return errors


def get_optimal_mode(
    num_layers: int,
    max_colors_needed: int,
    needs_rotation: bool = False,
) -> int:
    """Suggest optimal SNES BG mode based on requirements."""

    if needs_rotation:
        return 7

    if max_colors_needed > 16:
        return 3  # 256-color mode

    if num_layers <= 2:
        return 1  # Most common, good balance

    if num_layers == 4:
        return 0  # 4 layers, but only 4 colors each

    return 1  # Default to Mode 1
