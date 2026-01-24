"""
Genesis/Mega Drive Platform Configuration - Hardware constraints and generation settings.

The Genesis has more generous limits:
- 64KB VRAM for tiles (up to 2048 tiles)
- 16 colors per palette
- 4 palettes (64 total colors on screen)
- Hardware H/V flip
- Dual playfield (A and B) for parallax
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Dict


# =============================================================================
# Hardware Configuration
# =============================================================================

@dataclass
class GenesisHardwareConfig:
    """Genesis/Mega Drive hardware specifications."""

    # CPU/Memory
    cpu: str = "Motorola 68000 @ 7.67MHz"
    coprocessor: str = "Zilog Z80 @ 3.58MHz"
    ram: int = 65536  # 64KB main RAM
    vram: int = 65536  # 64KB VRAM

    # Graphics
    vdp: str = "Yamaha YM7101"
    screen_width: int = 320  # Can also be 256
    screen_height: int = 224  # Can also be 240 (PAL)
    screen_modes: List[Tuple[int, int]] = field(
        default_factory=lambda: [(256, 224), (320, 224), (256, 240), (320, 240)]
    )

    # Tiles
    tile_width: int = 8
    tile_height: int = 8
    max_tiles: int = 2048  # In VRAM
    bits_per_pixel: int = 4  # 4bpp = 16 colors

    # Palettes
    colors_per_palette: int = 16  # Including transparent
    num_palettes: int = 4
    total_colors: int = 64  # 4 palettes × 16 colors

    # Sprites
    max_sprites: int = 80
    sprites_per_scanline: int = 20
    max_sprite_pixels_per_line: int = 320
    sprite_sizes: List[Tuple[int, int]] = field(
        default_factory=lambda: [
            (8, 8), (8, 16), (8, 24), (8, 32),
            (16, 8), (16, 16), (16, 24), (16, 32),
            (24, 8), (24, 16), (24, 24), (24, 32),
            (32, 8), (32, 16), (32, 24), (32, 32),
        ]
    )

    # Planes
    num_planes: int = 2  # Plane A and Plane B
    plane_sizes: List[Tuple[int, int]] = field(
        default_factory=lambda: [(32, 32), (64, 32), (32, 64), (64, 64)]
    )


# =============================================================================
# Asset Generation Configuration
# =============================================================================

GENESIS_CONFIG = GenesisHardwareConfig()

GENESIS_ASSET_CONFIG = {
    # Tier identification
    'tier': 'STANDARD',
    'tier_id': 2,

    # Tile constraints
    'max_tiles': 2048,
    'max_tiles_per_plane': 1024,  # Practical limit per plane
    'tile_size': (8, 8),
    'bits_per_pixel': 4,  # 4bpp = 16 colors

    # Color constraints
    'colors_per_palette': 16,
    'max_palettes': 4,
    'transparent_index': 0,
    'total_colors': 64,

    # Sprite constraints
    'max_sprites': 80,
    'sprite_sizes': [
        (8, 8), (16, 16), (24, 24), (32, 32),
    ],
    'max_metasprite_tiles': 64,  # Can be larger than NES

    # Animation constraints
    'max_animation_frames': 8,
    'suggested_frame_counts': {
        'idle': 4,
        'walk': 6,
        'run': 6,
        'attack': 4,
        'hurt': 2,
        'death': 4,
        'jump': 3,
    },

    # Parallax
    'max_parallax_layers': 4,  # Plane A, B, sprites, line scroll
    'parallax_methods': ['dual_plane', 'line_scroll', 'column_scroll'],

    # Optimization
    'enable_flip_optimization': True,
    'enable_tile_deduplication': True,
    'enable_priority': True,  # Sprite priority bits

    # Generation style
    'prompt_style': '16-bit Genesis pixel art, vibrant colors, up to 16 colors per sprite, smooth gradients allowed, detailed sprites',
    'resampling': 'LANCZOS',  # Higher quality for 16-bit
    'dithering': True,  # Genesis often uses subtle dithering

    # Genesis-specific palette hints
    'palette_hints': {
        'color_format': '9-bit RGB (3-3-3)',
        'max_brightness': 14,  # 0-14 per channel (not 0-15)
        'recommended_bg_palette': [
            0x000,  # Black (transparent)
            0x222,  # Dark gray
            0x444,  # Gray
            0x666,  # Light gray
            0x888,  # Lighter gray
            0xAAA,  # Near white
            0xEEE,  # White
            0x008,  # Dark blue
            0x00E,  # Bright blue
            0x080,  # Dark green
            0x0E0,  # Bright green
            0x800,  # Dark red
            0xE00,  # Bright red
            0x880,  # Brown/orange
            0xEE0,  # Yellow
            0xE0E,  # Magenta
        ],
    },

    # DMA settings
    'dma_slots_per_frame': 64,  # Approximate
    'vblank_lines': 40,  # Lines available for DMA

    # File formats
    'chr_format': 'genesis_4bpp',  # 32 bytes per tile
    'tilemap_format': 'genesis_word',  # 16-bit per entry
}


# =============================================================================
# Helper Functions
# =============================================================================

def get_genesis_chr_size(tile_count: int) -> int:
    """Calculate CHR size in bytes for given tile count."""
    return tile_count * 32  # 32 bytes per 8x8 tile (4bpp)


def genesis_rgb_to_vdp(r: int, g: int, b: int) -> int:
    """
    Convert 8-bit RGB to Genesis VDP color format.

    Genesis uses 9-bit color (3 bits per channel).
    Format: 0000BBB0GGG0RRR0
    """
    r_3 = (r >> 5) & 0x07
    g_3 = (g >> 5) & 0x07
    b_3 = (b >> 5) & 0x07

    return (b_3 << 9) | (g_3 << 5) | (r_3 << 1)


def vdp_to_rgb(vdp_color: int) -> Tuple[int, int, int]:
    """Convert Genesis VDP color to 8-bit RGB."""
    r = ((vdp_color >> 1) & 0x07) * 36  # Scale 0-7 to 0-252
    g = ((vdp_color >> 5) & 0x07) * 36
    b = ((vdp_color >> 9) & 0x07) * 36
    return (r, g, b)


def get_genesis_tilemap_entry(
    tile_index: int,
    palette: int = 0,
    priority: bool = False,
    h_flip: bool = False,
    v_flip: bool = False,
) -> int:
    """
    Create a Genesis tilemap entry word.

    Format (16-bit):
    PCCVHTTT TTTTTTTT
    P = Priority (1 = high)
    CC = Palette (0-3)
    V = Vertical flip
    H = Horizontal flip
    T = Tile index (0-2047)
    """
    entry = tile_index & 0x7FF
    if h_flip:
        entry |= 0x0800
    if v_flip:
        entry |= 0x1000
    entry |= (palette & 0x03) << 13
    if priority:
        entry |= 0x8000
    return entry


def validate_genesis_palette(palette: List[int]) -> List[str]:
    """Validate a palette for Genesis compatibility."""
    errors = []

    if len(palette) > 16:
        errors.append(f"Palette has {len(palette)} colors, max is 16")

    for i, color in enumerate(palette):
        if color > 0xEEE:
            errors.append(f"Color {i} (${color:03X}) exceeds Genesis range")

        # Check for invalid bits (odd positions should be 0)
        if color & 0x111:
            errors.append(f"Color {i} (${color:03X}) has invalid low bits")

    return errors
