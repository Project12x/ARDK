"""
Platform Limits - Per-console system constraints for asset generation and organization.

This is the single source of truth for ALL hardware limitations per platform.
Asset generators, organizers, and pipelines should reference these limits
to make informed decisions about asset processing.

Categories of limits:
- Graphics: Tiles, palettes, sprites, backgrounds
- Memory: RAM, VRAM, ROM sizes
- Animation: Frame counts, timing, bank swapping
- Audio: Channels, sample rates, music formats
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum


# =============================================================================
# Platform Tiers
# =============================================================================

class PlatformTier(Enum):
    """Hardware capability tiers."""
    MINIMAL = 0      # NES, GB, C64, ZX Spectrum
    MINIMAL_PLUS = 1 # SMS, MSX2, Neo Geo Pocket
    STANDARD = 2     # Genesis, SNES, PC Engine, Amiga OCS
    STANDARD_PLUS = 3 # Neo Geo, Sega CD, 32X
    EXTENDED = 4     # GBA, DS, PSP


# =============================================================================
# Graphics Limits
# =============================================================================

@dataclass
class TileLimits:
    """Tile/pattern table constraints."""

    tile_width: int = 8
    tile_height: int = 8
    bits_per_pixel: int = 2              # 2bpp = 4 colors, 4bpp = 16 colors

    # Pattern table / CHR limits
    max_tiles_per_bank: int = 256        # Tiles per CHR bank
    max_banks_total: int = 32            # Total CHR banks available
    bytes_per_tile: int = 16             # Calculated from bpp and size

    # Flip optimization support
    hardware_h_flip: bool = True
    hardware_v_flip: bool = True

    # Tile arrangement
    metatile_width: int = 2              # Metatile = 2x2 tiles
    metatile_height: int = 2


@dataclass
class PaletteLimits:
    """Color and palette constraints."""

    colors_per_palette: int = 4          # Colors per sub-palette
    max_palettes_bg: int = 4             # Background palettes
    max_palettes_sprite: int = 4         # Sprite palettes
    total_system_colors: int = 64        # Colors in master palette

    # Transparency
    transparent_index: int = 0           # Which index is transparent
    shared_bg_color: bool = True         # All palettes share color 0?

    # Color format
    color_depth: int = 6                 # Bits per color channel
    color_format: str = "rgb"            # RGB, BGR, etc.


@dataclass
class SpriteLimits:
    """Sprite hardware constraints."""

    max_sprites_total: int = 64          # Max sprites on screen
    max_sprites_per_scanline: int = 8    # Sprites per horizontal line

    # Sprite sizes available
    sprite_sizes: List[Tuple[int, int]] = field(
        default_factory=lambda: [(8, 8), (8, 16)]
    )

    # OAM format
    oam_bytes_per_sprite: int = 4        # Bytes per OAM entry
    oam_total_size: int = 256            # Total OAM buffer size

    # Flickering behavior
    priority_bits: int = 1               # Bits for sprite priority


@dataclass
class BackgroundLimits:
    """Background layer constraints."""

    screen_width: int = 256
    screen_height: int = 240
    visible_height: int = 224            # NTSC safe area

    # Nametable
    nametable_width_tiles: int = 32
    nametable_height_tiles: int = 30
    nametable_size_bytes: int = 1024     # Includes attribute table

    # Scrolling
    scroll_x_bits: int = 8               # Fine scroll resolution
    scroll_y_bits: int = 8
    supports_split_scroll: bool = False  # Mid-screen scroll change

    # Layers
    background_layers: int = 1           # Number of BG planes
    supports_parallax: bool = False      # Hardware parallax support
    parallax_method: str = "none"        # irq, dma, hardware

    # Graphics mode: tile-based vs bitmap/raster
    is_tile_based: bool = True           # True = tile-based (NES, Genesis), False = bitmap (Amiga HAM)
    is_bitmap_capable: bool = False      # Can display bitmap modes (Mode 7, Amiga, etc.)


@dataclass
class AnimationLimits:
    """Animation-related constraints."""

    # CHR/tile animation
    supports_chr_animation: bool = False  # Bank swapping for tile animation
    max_animation_frames: int = 4         # Max frames for tile animation
    animation_banks_available: int = 0    # Banks for animation data

    # Sprite animation (frame counts)
    recommended_frames: Dict[str, int] = field(default_factory=lambda: {
        'idle': 2,
        'walk': 4,
        'run': 4,
        'attack': 3,
        'hurt': 2,
        'death': 3,
        'jump': 2,
    })

    # Timing
    vblank_cycles: int = 2273            # CPU cycles in vblank
    frame_rate: float = 60.0             # Target frame rate (NTSC)


# =============================================================================
# Memory Limits
# =============================================================================

@dataclass
class MemoryLimits:
    """Memory constraints."""

    # RAM
    internal_ram: int = 2048             # Internal work RAM
    external_ram: int = 0                # Cartridge RAM

    # VRAM
    vram_size: int = 2048                # Video RAM
    oam_size: int = 256                  # Sprite attribute memory

    # ROM (varies by mapper/cartridge)
    max_prg_rom: int = 32768             # Program ROM
    max_chr_rom: int = 8192              # Character ROM

    # With common mappers
    extended_prg_rom: int = 524288       # 512KB with MMC3
    extended_chr_rom: int = 262144       # 256KB with MMC3


# =============================================================================
# Audio Limits
# =============================================================================

@dataclass
class AudioLimits:
    """Audio hardware constraints."""

    # Channels
    pulse_channels: int = 2
    triangle_channels: int = 1
    noise_channels: int = 1
    dpcm_channels: int = 1
    total_channels: int = 5

    # Sample playback
    supports_samples: bool = True
    sample_rate: int = 33143             # DPCM sample rate
    sample_bits: int = 1                 # 1-bit delta

    # Music format
    music_driver: str = "famitone"       # Recommended music engine
    sfx_slots: int = 4                   # Concurrent SFX


# =============================================================================
# Complete Platform Limits
# =============================================================================

@dataclass
class PlatformLimits:
    """Complete hardware limits for a platform."""

    name: str
    tier: PlatformTier
    cpu: str

    tiles: TileLimits
    palettes: PaletteLimits
    sprites: SpriteLimits
    backgrounds: BackgroundLimits
    animations: AnimationLimits
    memory: MemoryLimits
    audio: AudioLimits

    # Additional platform-specific notes
    notes: List[str] = field(default_factory=list)
    mapper_notes: Dict[str, str] = field(default_factory=dict)


# =============================================================================
# Platform Definitions
# =============================================================================

NES_LIMITS = PlatformLimits(
    name="NES",
    tier=PlatformTier.MINIMAL,
    cpu="Ricoh 2A03 (6502 @ 1.79MHz)",

    tiles=TileLimits(
        tile_width=8,
        tile_height=8,
        bits_per_pixel=2,
        max_tiles_per_bank=256,
        max_banks_total=32,              # MMC3 can address 256KB CHR
        bytes_per_tile=16,
        hardware_h_flip=True,
        hardware_v_flip=True,
        metatile_width=2,
        metatile_height=2,
    ),

    palettes=PaletteLimits(
        colors_per_palette=4,
        max_palettes_bg=4,
        max_palettes_sprite=4,
        total_system_colors=54,          # 54 unique colors in NES palette
        transparent_index=0,
        shared_bg_color=True,            # $3F00 shared across all BG palettes
        color_depth=6,
        color_format="nes_ppu",
    ),

    sprites=SpriteLimits(
        max_sprites_total=64,
        max_sprites_per_scanline=8,
        sprite_sizes=[(8, 8), (8, 16)],
        oam_bytes_per_sprite=4,
        oam_total_size=256,
        priority_bits=1,
    ),

    backgrounds=BackgroundLimits(
        screen_width=256,
        screen_height=240,
        visible_height=224,
        nametable_width_tiles=32,
        nametable_height_tiles=30,
        nametable_size_bytes=1024,
        scroll_x_bits=8,
        scroll_y_bits=8,
        supports_split_scroll=True,      # Via mapper IRQ
        background_layers=1,
        supports_parallax=True,          # Via IRQ tricks
        parallax_method="scanline_irq",
        is_tile_based=True,              # NES is purely tile-based
        is_bitmap_capable=False,
    ),

    animations=AnimationLimits(
        supports_chr_animation=True,     # Via bank swapping
        max_animation_frames=4,
        animation_banks_available=16,    # 4 banks × 4 frames
        recommended_frames={
            'idle': 2,
            'walk': 4,
            'run': 4,
            'attack': 3,
            'hurt': 2,
            'death': 3,
            'jump': 2,
        },
        vblank_cycles=2273,
        frame_rate=60.0988,
    ),

    memory=MemoryLimits(
        internal_ram=2048,
        external_ram=8192,               # With battery backup
        vram_size=2048,
        oam_size=256,
        max_prg_rom=32768,               # NROM
        max_chr_rom=8192,                # NROM
        extended_prg_rom=524288,         # MMC3 (512KB)
        extended_chr_rom=262144,         # MMC3 (256KB)
    ),

    audio=AudioLimits(
        pulse_channels=2,
        triangle_channels=1,
        noise_channels=1,
        dpcm_channels=1,
        total_channels=5,
        supports_samples=True,
        sample_rate=33143,
        sample_bits=1,
        music_driver="famitone2",
        sfx_slots=4,
    ),

    notes=[
        "8 sprite limit per scanline causes flickering",
        "Use MMC3 mapper for CHR animation support",
        "Attribute table groups colors in 16x16 areas",
        "NTSC and PAL have different timing",
    ],

    mapper_notes={
        'NROM': "32KB PRG, 8KB CHR, no banking",
        'MMC1': "256KB PRG, 128KB CHR, slow bank switch",
        'MMC3': "512KB PRG, 256KB CHR, scanline IRQ for splits",
        'MMC5': "1MB PRG, 1MB CHR, extra audio, complex",
    },
)


GENESIS_LIMITS = PlatformLimits(
    name="Genesis",
    tier=PlatformTier.STANDARD,
    cpu="Motorola 68000 @ 7.67MHz",

    tiles=TileLimits(
        tile_width=8,
        tile_height=8,
        bits_per_pixel=4,
        max_tiles_per_bank=2048,         # VRAM holds ~2K tiles
        max_banks_total=1,               # All in VRAM
        bytes_per_tile=32,
        hardware_h_flip=True,
        hardware_v_flip=True,
        metatile_width=2,
        metatile_height=2,
    ),

    palettes=PaletteLimits(
        colors_per_palette=16,
        max_palettes_bg=4,
        max_palettes_sprite=4,
        total_system_colors=512,         # 9-bit color
        transparent_index=0,
        shared_bg_color=False,
        color_depth=9,
        color_format="bgr",
    ),

    sprites=SpriteLimits(
        max_sprites_total=80,
        max_sprites_per_scanline=20,
        sprite_sizes=[
            (8, 8), (8, 16), (8, 24), (8, 32),
            (16, 8), (16, 16), (16, 24), (16, 32),
            (24, 8), (24, 16), (24, 24), (24, 32),
            (32, 8), (32, 16), (32, 24), (32, 32),
        ],
        oam_bytes_per_sprite=8,
        oam_total_size=640,
        priority_bits=1,
    ),

    backgrounds=BackgroundLimits(
        screen_width=320,
        screen_height=224,
        visible_height=224,
        nametable_width_tiles=64,
        nametable_height_tiles=32,
        nametable_size_bytes=8192,
        scroll_x_bits=10,
        scroll_y_bits=10,
        supports_split_scroll=True,      # Via HBlank
        background_layers=2,             # Plane A and B
        supports_parallax=True,          # Hardware scroll per line
        parallax_method="line_scroll",
        is_tile_based=True,              # Genesis is tile-based
        is_bitmap_capable=False,         # No bitmap mode
    ),

    animations=AnimationLimits(
        supports_chr_animation=True,     # Via DMA
        max_animation_frames=8,
        animation_banks_available=0,     # Use VRAM DMA
        recommended_frames={
            'idle': 4,
            'walk': 6,
            'run': 6,
            'attack': 4,
            'hurt': 3,
            'death': 4,
            'jump': 3,
        },
        vblank_cycles=4000,              # More time available
        frame_rate=59.92,
    ),

    memory=MemoryLimits(
        internal_ram=65536,              # 64KB main RAM
        external_ram=8192,               # With SRAM
        vram_size=65536,                 # 64KB VRAM
        oam_size=640,
        max_prg_rom=4194304,             # 4MB common
        max_chr_rom=0,                   # No CHR ROM (tiles in VRAM)
        extended_prg_rom=4194304,
        extended_chr_rom=0,
    ),

    audio=AudioLimits(
        pulse_channels=3,                # PSG squares
        triangle_channels=0,
        noise_channels=1,                # PSG noise
        dpcm_channels=1,                 # YM2612 DAC
        total_channels=10,               # 6 FM + 4 PSG
        supports_samples=True,
        sample_rate=26000,
        sample_bits=8,
        music_driver="echo",
        sfx_slots=8,
    ),

    notes=[
        "DMA transfers during VBlank for tile updates",
        "Two scrolling background planes",
        "Per-line horizontal scroll for effects",
        "68000 much faster than 6502",
    ],
)


SNES_LIMITS = PlatformLimits(
    name="SNES",
    tier=PlatformTier.STANDARD,
    cpu="WDC 65816 @ 3.58MHz",

    tiles=TileLimits(
        tile_width=8,
        tile_height=8,
        bits_per_pixel=4,                # Up to 8bpp in some modes
        max_tiles_per_bank=1024,
        max_banks_total=4,
        bytes_per_tile=32,
        hardware_h_flip=True,
        hardware_v_flip=True,
        metatile_width=2,
        metatile_height=2,
    ),

    palettes=PaletteLimits(
        colors_per_palette=16,
        max_palettes_bg=8,
        max_palettes_sprite=8,
        total_system_colors=32768,       # 15-bit color
        transparent_index=0,
        shared_bg_color=False,
        color_depth=15,
        color_format="bgr",
    ),

    sprites=SpriteLimits(
        max_sprites_total=128,
        max_sprites_per_scanline=32,
        sprite_sizes=[
            (8, 8), (16, 16), (32, 32), (64, 64),
        ],
        oam_bytes_per_sprite=4,
        oam_total_size=544,
        priority_bits=2,
    ),

    backgrounds=BackgroundLimits(
        screen_width=256,
        screen_height=224,
        visible_height=224,
        nametable_width_tiles=32,
        nametable_height_tiles=32,
        nametable_size_bytes=2048,
        scroll_x_bits=10,
        scroll_y_bits=10,
        supports_split_scroll=True,
        background_layers=4,             # Mode 0 has 4 layers
        supports_parallax=True,
        parallax_method="hdma",
        is_tile_based=True,              # SNES is primarily tile-based
        is_bitmap_capable=True,          # Mode 7 can do bitmap-like effects
    ),

    animations=AnimationLimits(
        supports_chr_animation=True,
        max_animation_frames=8,
        animation_banks_available=8,
        recommended_frames={
            'idle': 4,
            'walk': 6,
            'run': 8,
            'attack': 5,
            'hurt': 3,
            'death': 5,
            'jump': 4,
        },
        vblank_cycles=2100,
        frame_rate=60.0988,
    ),

    memory=MemoryLimits(
        internal_ram=131072,             # 128KB WRAM
        external_ram=32768,
        vram_size=65536,
        oam_size=544,
        max_prg_rom=4194304,             # 4MB common
        max_chr_rom=0,
        extended_prg_rom=6291456,        # 6MB with SA-1
        extended_chr_rom=0,
    ),

    audio=AudioLimits(
        pulse_channels=0,
        triangle_channels=0,
        noise_channels=0,
        dpcm_channels=8,                 # 8 sample channels
        total_channels=8,
        supports_samples=True,
        sample_rate=32000,
        sample_bits=16,
        music_driver="spc700",
        sfx_slots=8,
    ),

    notes=[
        "Mode 7 for rotation/scaling effects",
        "HDMA for per-line register changes",
        "Up to 4 background layers",
        "SPC700 audio coprocessor",
    ],
)


GAMEBOY_LIMITS = PlatformLimits(
    name="Game Boy",
    tier=PlatformTier.MINIMAL,
    cpu="Sharp LR35902 (Z80-like @ 4.19MHz)",

    tiles=TileLimits(
        tile_width=8,
        tile_height=8,
        bits_per_pixel=2,
        max_tiles_per_bank=256,
        max_banks_total=2,               # Bank 0 and 1
        bytes_per_tile=16,
        hardware_h_flip=True,
        hardware_v_flip=True,
        metatile_width=2,
        metatile_height=2,
    ),

    palettes=PaletteLimits(
        colors_per_palette=4,
        max_palettes_bg=1,               # DMG has 1 BG palette
        max_palettes_sprite=2,           # 2 sprite palettes
        total_system_colors=4,           # 4 shades of green
        transparent_index=0,
        shared_bg_color=False,
        color_depth=2,
        color_format="gray",
    ),

    sprites=SpriteLimits(
        max_sprites_total=40,
        max_sprites_per_scanline=10,
        sprite_sizes=[(8, 8), (8, 16)],
        oam_bytes_per_sprite=4,
        oam_total_size=160,
        priority_bits=1,
    ),

    backgrounds=BackgroundLimits(
        screen_width=160,
        screen_height=144,
        visible_height=144,
        nametable_width_tiles=32,
        nametable_height_tiles=32,
        nametable_size_bytes=1024,
        scroll_x_bits=8,
        scroll_y_bits=8,
        supports_split_scroll=True,      # Via HBlank
        background_layers=2,             # BG + Window
        supports_parallax=True,
        parallax_method="hblank",
        is_tile_based=True,              # Game Boy is tile-based
        is_bitmap_capable=False,
    ),

    animations=AnimationLimits(
        supports_chr_animation=False,    # No CHR banking
        max_animation_frames=2,
        animation_banks_available=0,
        recommended_frames={
            'idle': 2,
            'walk': 2,
            'run': 2,
            'attack': 2,
            'hurt': 1,
            'death': 2,
            'jump': 1,
        },
        vblank_cycles=1140,
        frame_rate=59.7275,
    ),

    memory=MemoryLimits(
        internal_ram=8192,
        external_ram=32768,
        vram_size=8192,
        oam_size=160,
        max_prg_rom=32768,
        max_chr_rom=0,
        extended_prg_rom=2097152,        # 2MB with MBC5
        extended_chr_rom=0,
    ),

    audio=AudioLimits(
        pulse_channels=2,
        triangle_channels=0,
        noise_channels=1,
        dpcm_channels=1,                 # Wave channel
        total_channels=4,
        supports_samples=True,
        sample_rate=65536,               # Wave table
        sample_bits=4,
        music_driver="gbt_player",
        sfx_slots=4,
    ),

    notes=[
        "Very limited VRAM - share tiles between sprites and BG",
        "Window layer for HUD overlay",
        "No color on original DMG",
        "MBC5 for larger ROMs",
    ],
)


# =============================================================================
# Additional Platforms
# =============================================================================

SMS_LIMITS = PlatformLimits(
    name="SMS",
    tier=PlatformTier.MINIMAL_PLUS,
    cpu="Zilog Z80 @ 3.58MHz",

    tiles=TileLimits(
        tile_width=8,
        tile_height=8,
        bits_per_pixel=4,
        max_tiles_per_bank=448,          # 14KB VRAM for tiles
        max_banks_total=1,
        bytes_per_tile=32,
        hardware_h_flip=True,
        hardware_v_flip=True,
        metatile_width=1,
        metatile_height=1,
    ),

    palettes=PaletteLimits(
        colors_per_palette=16,
        max_palettes_bg=1,
        max_palettes_sprite=1,
        total_system_colors=64,          # 6-bit RGB
        transparent_index=0,
        shared_bg_color=False,
        color_depth=6,
        color_format="rgb",
    ),

    sprites=SpriteLimits(
        max_sprites_total=64,
        max_sprites_per_scanline=8,
        sprite_sizes=[(8, 8), (8, 16)],  # Mode 4
        oam_bytes_per_sprite=2,
        oam_total_size=256,
        priority_bits=0,
    ),

    backgrounds=BackgroundLimits(
        screen_width=256,
        screen_height=192,
        visible_height=192,
        nametable_width_tiles=32,
        nametable_height_tiles=28,
        nametable_size_bytes=1792,
        scroll_x_bits=8,
        scroll_y_bits=8,
        supports_split_scroll=True,      # Line interrupt
        background_layers=1,
        supports_parallax=True,
        parallax_method="line_interrupt",
        is_tile_based=True,              # SMS is tile-based
        is_bitmap_capable=False,
    ),

    animations=AnimationLimits(
        supports_chr_animation=True,     # Via VRAM writes
        max_animation_frames=4,
        animation_banks_available=0,
        recommended_frames={
            'idle': 2,
            'walk': 4,
            'run': 4,
            'attack': 3,
            'hurt': 2,
            'death': 3,
            'jump': 2,
        },
        vblank_cycles=1500,
        frame_rate=59.92,
    ),

    memory=MemoryLimits(
        internal_ram=8192,
        external_ram=8192,
        vram_size=16384,
        oam_size=256,
        max_prg_rom=1048576,
        max_chr_rom=0,
        extended_prg_rom=4194304,
        extended_chr_rom=0,
    ),

    audio=AudioLimits(
        pulse_channels=2,
        triangle_channels=0,
        noise_channels=1,
        dpcm_channels=0,
        total_channels=4,                # 3 square + 1 noise (PSG)
        supports_samples=False,
        sample_rate=0,
        sample_bits=0,
        music_driver="psglib",
        sfx_slots=4,
    ),

    notes=[
        "Mode 4 is most common for games",
        "Better color than NES (16 colors per palette)",
        "Line interrupt for parallax effects",
        "VDP writes only during VBlank/HBlank",
    ],
)


PCE_LIMITS = PlatformLimits(
    name="PC Engine",
    tier=PlatformTier.STANDARD,
    cpu="HuC6280 (65C02) @ 7.16MHz",

    tiles=TileLimits(
        tile_width=8,
        tile_height=8,
        bits_per_pixel=4,
        max_tiles_per_bank=2048,         # 64KB VRAM
        max_banks_total=1,
        bytes_per_tile=32,
        hardware_h_flip=True,
        hardware_v_flip=True,
        metatile_width=2,
        metatile_height=2,
    ),

    palettes=PaletteLimits(
        colors_per_palette=16,
        max_palettes_bg=16,
        max_palettes_sprite=16,
        total_system_colors=512,         # 9-bit color
        transparent_index=0,
        shared_bg_color=True,
        color_depth=9,
        color_format="grb",
    ),

    sprites=SpriteLimits(
        max_sprites_total=64,
        max_sprites_per_scanline=16,
        sprite_sizes=[
            (16, 16), (16, 32), (16, 64),
            (32, 16), (32, 32), (32, 64),
        ],
        oam_bytes_per_sprite=8,
        oam_total_size=512,
        priority_bits=1,
    ),

    backgrounds=BackgroundLimits(
        screen_width=256,
        screen_height=240,
        visible_height=224,
        nametable_width_tiles=32,
        nametable_height_tiles=32,
        nametable_size_bytes=2048,
        scroll_x_bits=10,
        scroll_y_bits=9,
        supports_split_scroll=True,
        background_layers=1,             # But powerful scanline effects
        supports_parallax=True,
        parallax_method="raster_counter",
        is_tile_based=True,              # PC Engine is tile-based
        is_bitmap_capable=False,
    ),

    animations=AnimationLimits(
        supports_chr_animation=True,
        max_animation_frames=8,
        animation_banks_available=0,
        recommended_frames={
            'idle': 4,
            'walk': 6,
            'run': 6,
            'attack': 4,
            'hurt': 2,
            'death': 4,
            'jump': 3,
        },
        vblank_cycles=3000,
        frame_rate=59.94,
    ),

    memory=MemoryLimits(
        internal_ram=8192,
        external_ram=0,
        vram_size=65536,
        oam_size=512,
        max_prg_rom=2097152,
        max_chr_rom=0,
        extended_prg_rom=2097152,
        extended_chr_rom=0,
    ),

    audio=AudioLimits(
        pulse_channels=6,                # 6 wavetable channels
        triangle_channels=0,
        noise_channels=1,                # Channel 6 can be noise
        dpcm_channels=0,
        total_channels=6,
        supports_samples=True,           # 5-bit samples
        sample_rate=7000,
        sample_bits=5,
        music_driver="squirrel",
        sfx_slots=6,
    ),

    notes=[
        "Very capable 8-bit system",
        "Large sprites (up to 32x64)",
        "16 palettes for BG and sprites each",
        "Fast CPU allows complex effects",
        "CD-ROM games have more resources",
    ],
)


GBA_LIMITS = PlatformLimits(
    name="GBA",
    tier=PlatformTier.EXTENDED,
    cpu="ARM7TDMI @ 16.78MHz",

    tiles=TileLimits(
        tile_width=8,
        tile_height=8,
        bits_per_pixel=8,                # Up to 8bpp
        max_tiles_per_bank=1024,
        max_banks_total=4,               # Multiple charblocks
        bytes_per_tile=64,               # 8bpp
        hardware_h_flip=True,
        hardware_v_flip=True,
        metatile_width=2,
        metatile_height=2,
    ),

    palettes=PaletteLimits(
        colors_per_palette=256,          # Mode 4
        max_palettes_bg=1,               # 256-color mode
        max_palettes_sprite=1,
        total_system_colors=32768,       # 15-bit color
        transparent_index=0,
        shared_bg_color=False,
        color_depth=15,
        color_format="bgr",
    ),

    sprites=SpriteLimits(
        max_sprites_total=128,
        max_sprites_per_scanline=128,    # Memory limited, not hardware
        sprite_sizes=[
            (8, 8), (16, 16), (32, 32), (64, 64),
            (16, 8), (32, 8), (32, 16), (64, 32),
            (8, 16), (8, 32), (16, 32), (32, 64),
        ],
        oam_bytes_per_sprite=8,
        oam_total_size=1024,
        priority_bits=2,
    ),

    backgrounds=BackgroundLimits(
        screen_width=240,
        screen_height=160,
        visible_height=160,
        nametable_width_tiles=32,
        nametable_height_tiles=32,
        nametable_size_bytes=2048,
        scroll_x_bits=9,
        scroll_y_bits=9,
        supports_split_scroll=True,
        background_layers=4,             # 4 BG layers in tile modes
        supports_parallax=True,
        parallax_method="bg_layers",
        is_tile_based=True,              # GBA modes 0-2 are tile-based
        is_bitmap_capable=True,          # Modes 3-5 are bitmap modes
    ),

    animations=AnimationLimits(
        supports_chr_animation=True,
        max_animation_frames=16,
        animation_banks_available=4,
        recommended_frames={
            'idle': 6,
            'walk': 8,
            'run': 8,
            'attack': 6,
            'hurt': 4,
            'death': 6,
            'jump': 4,
        },
        vblank_cycles=10000,
        frame_rate=59.73,
    ),

    memory=MemoryLimits(
        internal_ram=32768,              # IWRAM
        external_ram=262144,             # EWRAM
        vram_size=98304,                 # 96KB VRAM
        oam_size=1024,
        max_prg_rom=33554432,            # 32MB
        max_chr_rom=0,
        extended_prg_rom=33554432,
        extended_chr_rom=0,
    ),

    audio=AudioLimits(
        pulse_channels=2,
        triangle_channels=0,
        noise_channels=1,
        dpcm_channels=2,                 # 2 DMA channels
        total_channels=6,                # 4 GB + 2 DMA
        supports_samples=True,
        sample_rate=32768,
        sample_bits=8,
        music_driver="maxmod",
        sfx_slots=8,
    ),

    notes=[
        "32-bit ARM CPU very powerful",
        "4 background layers with affine support",
        "Mode 7-style rotation/scaling",
        "256-color mode or 16-color 4bpp mode",
        "DMA sound channels for streaming audio",
    ],
)


# Mega Drive (alias for Genesis with additional notes)
MEGADRIVE_LIMITS = PlatformLimits(
    name="Mega Drive",
    tier=PlatformTier.STANDARD,
    cpu="Motorola 68000 @ 7.67MHz + Z80 @ 3.58MHz",

    tiles=TileLimits(
        tile_width=8,
        tile_height=8,
        bits_per_pixel=4,
        max_tiles_per_bank=2048,
        max_banks_total=1,
        bytes_per_tile=32,
        hardware_h_flip=True,
        hardware_v_flip=True,
        metatile_width=2,
        metatile_height=2,
    ),

    palettes=PaletteLimits(
        colors_per_palette=16,
        max_palettes_bg=4,
        max_palettes_sprite=4,
        total_system_colors=512,         # 9-bit RGB (3 bits per channel)
        transparent_index=0,
        shared_bg_color=False,
        color_depth=9,
        color_format="bgr",              # Actually BGR order
    ),

    sprites=SpriteLimits(
        max_sprites_total=80,
        max_sprites_per_scanline=20,     # 320 pixels / 16 = 20 max
        sprite_sizes=[
            (8, 8), (8, 16), (8, 24), (8, 32),
            (16, 8), (16, 16), (16, 24), (16, 32),
            (24, 8), (24, 16), (24, 24), (24, 32),
            (32, 8), (32, 16), (32, 24), (32, 32),
        ],
        oam_bytes_per_sprite=8,          # Link, pattern, attr, size, x, y
        oam_total_size=640,              # 80 sprites * 8 bytes
        priority_bits=1,                 # High/low priority
    ),

    backgrounds=BackgroundLimits(
        screen_width=320,                # H40 mode (common)
        screen_height=224,
        visible_height=224,
        nametable_width_tiles=64,        # Or 128 in some configs
        nametable_height_tiles=32,       # Or 64
        nametable_size_bytes=8192,       # Per plane
        scroll_x_bits=10,
        scroll_y_bits=10,
        supports_split_scroll=True,
        background_layers=2,             # Plane A + Plane B
        supports_parallax=True,
        parallax_method="line_scroll",   # Per-line H-scroll
        is_tile_based=True,              # Mega Drive is tile-based
        is_bitmap_capable=False,
    ),

    animations=AnimationLimits(
        supports_chr_animation=True,
        max_animation_frames=8,
        animation_banks_available=0,     # Use DMA
        recommended_frames={
            'idle': 4,
            'walk': 6,
            'run': 6,
            'attack': 4,
            'hurt': 3,
            'death': 4,
            'jump': 3,
        },
        vblank_cycles=4000,
        frame_rate=59.92,
    ),

    memory=MemoryLimits(
        internal_ram=65536,
        external_ram=8192,
        vram_size=65536,
        oam_size=640,
        max_prg_rom=4194304,
        max_chr_rom=0,
        extended_prg_rom=4194304,
        extended_chr_rom=0,
    ),

    audio=AudioLimits(
        pulse_channels=3,                # PSG
        triangle_channels=0,
        noise_channels=1,                # PSG
        dpcm_channels=1,                 # YM2612 DAC
        total_channels=10,               # 6 FM + 3 PSG + 1 noise
        supports_samples=True,
        sample_rate=26000,
        sample_bits=8,
        music_driver="echo",
        sfx_slots=8,
    ),

    notes=[
        "Two scrolling background planes (A and B)",
        "Per-line horizontal scroll for raster effects",
        "VDP DMA for fast tile updates",
        "Shadow/highlight mode doubles effective colors",
        "68000 + Z80 allows parallel processing",
        "Window layer can override plane A",
        "Sprite link list for ordering",
    ],
)


# =============================================================================
# Platform Registry
# =============================================================================

PLATFORM_LIMITS: Dict[str, PlatformLimits] = {
    # 8-bit
    'nes': NES_LIMITS,
    'gb': GAMEBOY_LIMITS,
    'gameboy': GAMEBOY_LIMITS,
    'sms': SMS_LIMITS,
    'mastersystem': SMS_LIMITS,
    # 16-bit
    'genesis': GENESIS_LIMITS,
    'megadrive': MEGADRIVE_LIMITS,
    'md': MEGADRIVE_LIMITS,
    'snes': SNES_LIMITS,
    'pce': PCE_LIMITS,
    'pcengine': PCE_LIMITS,
    'tg16': PCE_LIMITS,
    # 32-bit
    'gba': GBA_LIMITS,
}


def get_platform_limits(platform: str) -> PlatformLimits:
    """Get limits for a platform."""
    return PLATFORM_LIMITS.get(platform.lower(), NES_LIMITS)


def get_recommended_frames(platform: str, gameplay_state: str) -> int:
    """Get recommended animation frames for a state on a platform."""
    limits = get_platform_limits(platform)
    return limits.animations.recommended_frames.get(gameplay_state.lower(), 2)


def get_max_sprites(platform: str) -> int:
    """Get max sprites for a platform."""
    limits = get_platform_limits(platform)
    return limits.sprites.max_sprites_total


def get_tile_limit(platform: str) -> int:
    """Get max tiles per bank for a platform."""
    limits = get_platform_limits(platform)
    return limits.tiles.max_tiles_per_bank


def supports_chr_animation(platform: str) -> bool:
    """Check if platform supports CHR bank animation."""
    limits = get_platform_limits(platform)
    return limits.animations.supports_chr_animation


def get_animation_banks(platform: str) -> int:
    """Get number of banks available for animation."""
    limits = get_platform_limits(platform)
    return limits.animations.animation_banks_available


def validate_asset_for_platform(
    platform: str,
    tile_count: int,
    colors_used: int,
    sprite_count: int = 0,
) -> Dict[str, Any]:
    """
    Validate asset parameters against platform limits.

    Returns dict with 'valid' bool and any warnings/errors.
    """
    limits = get_platform_limits(platform)
    result = {
        'valid': True,
        'warnings': [],
        'errors': [],
    }

    # Check tile count
    if tile_count > limits.tiles.max_tiles_per_bank:
        result['errors'].append(
            f"Tile count ({tile_count}) exceeds {platform.upper()} limit "
            f"({limits.tiles.max_tiles_per_bank})"
        )
        result['valid'] = False
    elif tile_count > limits.tiles.max_tiles_per_bank * 0.9:
        result['warnings'].append(
            f"Tile count ({tile_count}) near {platform.upper()} limit"
        )

    # Check colors
    max_colors = limits.palettes.colors_per_palette * limits.palettes.max_palettes_bg
    if colors_used > max_colors:
        result['errors'].append(
            f"Color count ({colors_used}) exceeds {platform.upper()} limit ({max_colors})"
        )
        result['valid'] = False

    # Check sprites
    if sprite_count > limits.sprites.max_sprites_total:
        result['errors'].append(
            f"Sprite count ({sprite_count}) exceeds {platform.upper()} limit "
            f"({limits.sprites.max_sprites_total})"
        )
        result['valid'] = False

    return result


# =============================================================================
# CLI
# =============================================================================

def main():
    """Print platform limits."""
    import argparse

    parser = argparse.ArgumentParser(description='Query platform limits')
    parser.add_argument('platform', nargs='?', default='nes',
                       help='Platform to query')
    parser.add_argument('--all', action='store_true',
                       help='Show all platforms')

    args = parser.parse_args()

    def print_limits(name: str, limits: PlatformLimits):
        print(f"\n{'='*60}")
        print(f"{limits.name} ({limits.tier.name})")
        print(f"CPU: {limits.cpu}")
        print(f"{'='*60}")

        print(f"\nTiles:")
        print(f"  Size: {limits.tiles.tile_width}x{limits.tiles.tile_height}")
        print(f"  Per bank: {limits.tiles.max_tiles_per_bank}")
        print(f"  Total banks: {limits.tiles.max_banks_total}")
        print(f"  BPP: {limits.tiles.bits_per_pixel}")

        print(f"\nPalettes:")
        print(f"  Colors per palette: {limits.palettes.colors_per_palette}")
        print(f"  BG palettes: {limits.palettes.max_palettes_bg}")
        print(f"  Sprite palettes: {limits.palettes.max_palettes_sprite}")

        print(f"\nSprites:")
        print(f"  Max on screen: {limits.sprites.max_sprites_total}")
        print(f"  Per scanline: {limits.sprites.max_sprites_per_scanline}")
        print(f"  Sizes: {limits.sprites.sprite_sizes}")

        print(f"\nBackgrounds:")
        print(f"  Resolution: {limits.backgrounds.screen_width}x{limits.backgrounds.screen_height}")
        print(f"  Layers: {limits.backgrounds.background_layers}")
        print(f"  Parallax: {limits.backgrounds.parallax_method}")

        print(f"\nAnimation:")
        print(f"  CHR animation: {limits.animations.supports_chr_animation}")
        print(f"  Max frames: {limits.animations.max_animation_frames}")
        print(f"  Recommended frames: {limits.animations.recommended_frames}")

        if limits.notes:
            print(f"\nNotes:")
            for note in limits.notes:
                print(f"  - {note}")

    if args.all:
        for name, limits in PLATFORM_LIMITS.items():
            print_limits(name, limits)
    else:
        limits = get_platform_limits(args.platform)
        print_limits(args.platform, limits)


if __name__ == '__main__':
    main()
