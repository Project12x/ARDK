import os
import json
from dataclasses import dataclass, asdict
from typing import List, Tuple, Optional, Dict, Any
from abc import ABC, abstractmethod
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np

# PLATFORM CONFIGURATION SYSTEM
# =============================================================================
# Supports: NES, Sega Genesis/Megadrive, SNES, Amiga, PC Engine/TurboGrafx
# Each platform has different tile formats, color depths, and sprite constraints
# Ref: tools/platform_specs.json for strict hardware limits.

def load_platform_specs() -> Dict[str, Any]:
    specs_path = Path(__file__).parent / "platform_specs.json"
    if specs_path.exists():
        with open(specs_path, "r") as f:
            return json.load(f)
    return {}

PLATFORM_SPECS = load_platform_specs()

class PlatformConfig:
    """
    Base class for platform-specific configuration.

    This class serves as the foundation for the Agentic Retro Development Kit (ARDK),
    providing both sprite processing parameters AND hardware/build system info for
    cross-platform engine development.

    Attributes are grouped into:
    - Graphics: tile format, colors, sprites
    - Hardware: CPU, memory map, constraints
    - Build: toolchain, assembler, linker
    - Audio: sound chip, channels, format
    """

    # =========================================================================
    # IDENTITY
    # =========================================================================
    name: str = "Generic"
    full_name: str = "Generic Platform"
    manufacturer: str = "Unknown"
    year: int = 1980
    generation: int = 0              # Console generation (3rd, 4th, etc.)

    # =========================================================================
    # GRAPHICS - Sprite/Tile Configuration
    # =========================================================================
    tile_width: int = 8              # Tile width in pixels
    tile_height: int = 8             # Tile height in pixels
    bits_per_pixel: int = 2          # Color depth (2=4 colors, 4=16 colors)
    colors_per_palette: int = 4      # Colors per sprite palette
    max_palettes: int = 4            # Number of available palettes
    max_sprite_width: int = 64       # Max hardware sprite width
    max_sprite_height: int = 64      # Max hardware sprite height
    max_sprites_total: int = 64      # Max sprites in OAM/SAT
    max_sprites_per_line: int = 8    # Sprites per scanline before flicker
    bytes_per_tile: int = 16         # Bytes per tile in output format
    output_extension: str = ".bin"   # Output file extension
    palette_rgb: Dict[int, Tuple[int, int, int]] = {}  # System palette
    default_palette: List[int] = []  # Default palette indices
    resample_mode: str = "LANCZOS"   # Downscaling: LANCZOS (smooth) or NEAREST (pixelated)

    # Dithering configuration (for gradient handling)
    dither_method: str = "ordered"   # none, ordered (Bayer), floyd, atkinson
    dither_matrix_size: int = 4      # 2, 4, or 8 for Bayer matrix
    dither_strength: float = 1.0     # 0.0-2.0, higher = more dithering

    # Video hardware
    screen_width: int = 256          # Native resolution width
    screen_height: int = 240         # Native resolution height
    video_chip: str = "Unknown"      # PPU, VDP, etc.
    tile_based_bg: bool = True       # Background uses tiles (vs bitmap)

    # =========================================================================
    # HARDWARE - CPU & Memory
    # =========================================================================
    cpu_name: str = "Unknown"        # e.g., "Ricoh 2A03", "Motorola 68000"
    cpu_family: str = "unknown"      # 6502, z80, 68000, arm, 65816, sh2, mips
    cpu_bits: int = 8                # 8, 16, 32-bit
    cpu_speed_mhz: float = 1.0       # Clock speed
    cpu_endian: str = "little"       # little or big endian

    # Memory map (addresses as integers)
    ram_start: int = 0x0000          # Main RAM start
    ram_size: int = 0x0800           # Main RAM size (bytes)
    rom_start: int = 0x8000          # PRG/Code ROM start
    rom_size: int = 0x8000           # Max ROM size (bytes)
    vram_start: int = 0x0000         # Video RAM start
    vram_size: int = 0x0000          # Video RAM size

    # Zero page / direct page (6502/65816)
    zp_start: int = 0x00             # Zero page start
    zp_size: int = 0x100             # Zero page size
    zp_reserved: List[range] = []    # System-reserved ZP ranges

    # Stack
    stack_start: int = 0x0100        # Stack location
    stack_size: int = 0x100          # Stack size

    # Bank switching / memory mapping
    mapper_name: str = "None"        # Mapper/MBC name
    prg_bank_size: int = 0x4000      # PRG bank size (if banked)
    chr_bank_size: int = 0x2000      # CHR bank size (if banked)
    max_prg_banks: int = 1           # Max PRG banks
    max_chr_banks: int = 1           # Max CHR banks

    # =========================================================================
    # BUILD SYSTEM - Toolchain Configuration
    # =========================================================================
    toolchain: str = "custom"        # cc65, sgdk, devkitpro, z88dk, gbdk
    assembler: str = "ca65"          # Assembler command
    compiler: str = ""               # C compiler (if available)
    linker: str = "ld65"             # Linker command
    rom_tool: str = ""               # ROM builder tool

    # File extensions
    asm_extension: str = ".asm"      # Assembly file extension
    obj_extension: str = ".o"        # Object file extension
    rom_extension: str = ".bin"      # Final ROM extension

    # Build flags
    asm_flags: List[str] = []        # Default assembler flags
    link_flags: List[str] = []       # Default linker flags
    defines: List[str] = []          # Default preprocessor defines

    # =========================================================================
    # AUDIO - Sound Hardware
    # =========================================================================
    audio_chip: str = "None"         # Sound chip name
    sound_channels: int = 4          # Number of hardware channels

    # =========================================================================
    # ADVANCED MAPPING (NEW)
    # =========================================================================
    mmc3_banking_mode: Optional[Dict[str, int]] = None  # e.g., {'bg': 256, 'spr': 256}
    reserved_status_bar_height: int = 0                 # Reserved pixel height for status bar
    allow_mirroring_x: bool = False                     # Hardware supports X-flipping BG tiles
    allow_mirroring_y: bool = False                     # Hardware supports Y-flipping BG tiles
    audio_type: str = "psg"          # psg, fm, pcm, wavetable
    music_driver: str = ""           # Common music driver (e.g., famitone, echo)
    tracker_format: str = ""         # Native tracker format

    # =========================================================================
    # CONSTRAINTS - Platform Limits for Code Generation
    # =========================================================================
    cycle_budget_per_frame: int = 0  # CPU cycles per frame
    vblank_cycles: int = 0           # Cycles available in VBlank
    dma_available: bool = False      # Has DMA for fast copies

    # Instruction set notes
    has_multiply: bool = False       # Hardware multiply instruction
    has_divide: bool = False         # Hardware divide instruction
    fast_zero_page: bool = False     # Zero page is faster (6502)

    # =========================================================================
    # HAL TIER INTEGRATION - Links to ARDK tiered system
    # =========================================================================
    hal_tier: int = 0                # 0=MINIMAL, 1=STANDARD, 2=EXTENDED
    hal_tier_name: str = "MINIMAL"   # Human-readable tier name
    hal_max_entities: int = 32       # From hal_tiers.h defaults
    hal_max_enemies: int = 12        # Per-category limit
    hal_max_projectiles: int = 16    # Per-category limit
    hal_max_pickups: int = 16        # Per-category limit
    hal_max_effects: int = 8         # Per-category limit
    hal_platform_id: int = 0x0000    # ARDK_PLAT_xxx from platform_manifest.h

    @classmethod
    def generate_tile_data(cls, indexed_img: Image.Image) -> bytes:
        """Convert indexed image to platform-specific tile format"""
        raise NotImplementedError("Subclass must implement generate_tile_data")

    @classmethod
    def get_palette_rgb(cls, palette_indices: List[int]) -> List[Tuple[int, int, int]]:
        """Get RGB values for palette indices"""
        return [cls.palette_rgb.get(idx, (0, 0, 0)) for idx in palette_indices]

    @classmethod
    def get_memory_map(cls) -> Dict[str, Dict]:
        """Return structured memory map for documentation/code generation"""
        return {
            'ram': {'start': cls.ram_start, 'size': cls.ram_size},
            'rom': {'start': cls.rom_start, 'size': cls.rom_size},
            'vram': {'start': cls.vram_start, 'size': cls.vram_size},
            'stack': {'start': cls.stack_start, 'size': cls.stack_size},
            'zp': {'start': cls.zp_start, 'size': cls.zp_size},
        }

    @classmethod
    def get_build_command(cls, source_files: List[str], output: str) -> str:
        """Generate build command for this platform"""
        # Override in subclass for platform-specific build
        return f"# Build command for {cls.name} - override in subclass"

    @classmethod
    def validate_sprite_count(cls, count: int) -> List[str]:
        """Validate sprite count against tier and hardware limits."""
        warnings = []

        # Check against HAL entity limit
        if count > cls.hal_max_entities:
            warnings.append(
                f"Sprite count ({count}) exceeds HAL_MAX_ENTITIES ({cls.hal_max_entities}) "
                f"for {cls.hal_tier_name} tier"
            )

        # Check against hardware OAM limit
        if count > cls.max_sprites_total:
            warnings.append(
                f"Sprite count ({count}) exceeds hardware sprite limit ({cls.max_sprites_total})"
            )

        # Check if metasprites would exceed per-scanline limit
        tiles_per_sprite = (32 // cls.tile_width) * (32 // cls.tile_height)  # Assuming 32x32 metasprite
        if tiles_per_sprite > cls.max_sprites_per_line:
            warnings.append(
                f"32x32 metasprite uses {tiles_per_sprite} tiles per line, "
                f"hardware limit is {cls.max_sprites_per_line}"
            )

        return warnings

    @classmethod
    def suggest_tier(cls, sprite_count: int, complexity: str = "medium") -> str:
        """Suggest appropriate tier for this content."""
        if sprite_count <= 32 and complexity in ["low", "medium"]:
            return "MINIMAL (NES, Game Boy, SMS) - 8-bit systems with limited RAM"
        elif sprite_count <= 128:
            return "STANDARD (Genesis, SNES, PCE) - 16-bit systems with more resources"
        else:
            return "EXTENDED (GBA, Neo Geo) - Advanced systems with abundant resources"

    @classmethod
    def get_tier_info(cls) -> Dict[str, Any]:
        """Return tier information for this platform."""
        return {
            'tier': cls.hal_tier,
            'tier_name': cls.hal_tier_name,
            'platform_id': hex(cls.hal_platform_id),
            'limits': {
                'max_entities': cls.hal_max_entities,
                'max_enemies': cls.hal_max_enemies,
                'max_projectiles': cls.hal_max_projectiles,
                'max_pickups': cls.hal_max_pickups,
                'max_effects': cls.hal_max_effects,
                'max_sprites_total': cls.max_sprites_total,
                'max_sprites_per_line': cls.max_sprites_per_line,
            }
        }


class NESConfig(PlatformConfig):
    """Nintendo Entertainment System / Famicom"""

    # Identity
    name = "NES"
    full_name = "Nintendo Entertainment System"
    manufacturer = "Nintendo"
    year = 1983
    generation = 3

    # Graphics
    tile_width = 8
    tile_height = 8
    bits_per_pixel = 2
    colors_per_palette = 4      # 3 colors + transparent
    max_palettes = 4            # 4 sprite palettes
    max_sprite_width = 64       # 8 sprites * 8px (flickering for more)
    max_sprite_height = 64
    max_sprites_total = 64      # OAM holds 64 sprites
    max_sprites_per_line = 8
    
    # NES/Famicom Specifics
    # By default, NES DOES NOT support BG mirroring in hardware (MMC3/ MMC5 might via bank switching but not per-tile flipping like GB/SNES)
    # However, user requested optimization constraints so we enable flags if specific mappers allow.
    # Standard MMC3: BG can use 256 tiles from pattern table 0 or 1.
    mmc3_banking_mode = {'bg_bank_size': 256, 'spr_bank_size': 256}
    reserved_status_bar_height = 0
    allow_mirroring_x = False # Standard NES PPU cannot flip BG tiles
    allow_mirroring_y = False    # 8 sprites per scanline
    bytes_per_tile = 16         # 2 bitplanes, 8 bytes each
    output_extension = ".chr"
    screen_width = 256
    screen_height = 240
    video_chip = "2C02 PPU"
    tile_based_bg = True

    # NES-specific dithering: Use 4x4 ordered dithering for best results
    # with only 4 colors per palette. Higher strength helps with gradients.
    dither_method = "ordered"
    dither_matrix_size = 4          # 4x4 Bayer - visible at NES resolution
    dither_strength = 1.2           # Slightly stronger for 4-color limit

    # Hardware
    cpu_name = "Ricoh 2A03"
    cpu_family = "6502"
    cpu_bits = 8
    cpu_speed_mhz = 1.79        # 1.789773 MHz (NTSC)
    cpu_endian = "little"

    ram_start = 0x0000
    ram_size = 0x0800           # 2KB internal RAM
    rom_start = 0x8000          # PRG ROM (with mapper, can be $8000-$FFFF)
    rom_size = 0x8000           # 32KB (without mapper)
    vram_start = 0x2000         # PPU VRAM
    vram_size = 0x0800          # 2KB VRAM (nametables)

    zp_start = 0x00
    zp_size = 0x100
    zp_reserved = [range(0x00, 0x10)]  # Often reserved for engine
    stack_start = 0x0100
    stack_size = 0x100

    mapper_name = "MMC3"        # Default mapper for this project
    prg_bank_size = 0x2000      # 8KB banks (MMC3)
    chr_bank_size = 0x0400      # 1KB banks (MMC3)
    max_prg_banks = 64          # 512KB PRG max
    max_chr_banks = 256         # 256KB CHR max

    # Build system
    toolchain = "cc65"
    assembler = "ca65"
    compiler = "cc65"
    linker = "ld65"
    rom_tool = ""               # ld65 outputs directly
    asm_extension = ".asm"
    obj_extension = ".o"
    rom_extension = ".nes"
    asm_flags = ["-t", "nes"]
    link_flags = ["-C", "nes.cfg"]

    # Audio
    audio_chip = "2A03 APU"
    audio_channels = 5          # 2 pulse, 1 triangle, 1 noise, 1 DPCM
    audio_type = "psg"
    music_driver = "famitone2"
    tracker_format = "ftm"      # FamiTracker

    # Constraints
    cycle_budget_per_frame = 29780  # ~29780 cycles per frame (NTSC)
    vblank_cycles = 2273        # ~2273 cycles in VBlank
    dma_available = True        # OAM DMA via $4014
    has_multiply = False
    has_divide = False
    fast_zero_page = True       # ZP is 1 cycle faster

    # HAL Tier Integration
    hal_tier = 0                # MINIMAL
    hal_tier_name = "MINIMAL"
    hal_platform_id = 0x0100    # ARDK_PLAT_NES
    hal_max_entities = 32       # From hal_tiers.h
    hal_max_enemies = 12
    hal_max_projectiles = 16
    hal_max_pickups = 16
    hal_max_effects = 8

    # NES PPU Palette (2C02)
    palette_rgb = {
        0x00: (84, 84, 84),    0x01: (0, 30, 116),    0x02: (8, 16, 144),    0x03: (48, 0, 136),
        0x04: (68, 0, 100),    0x05: (92, 0, 48),     0x06: (84, 4, 0),      0x07: (60, 24, 0),
        0x08: (32, 42, 0),     0x09: (8, 58, 0),      0x0A: (0, 64, 0),      0x0B: (0, 60, 0),
        0x0C: (0, 50, 60),     0x0D: (0, 0, 0),       0x0E: (0, 0, 0),       0x0F: (0, 0, 0),
        0x10: (152, 150, 152), 0x11: (8, 76, 196),    0x12: (48, 50, 236),   0x13: (92, 30, 228),
        0x14: (136, 20, 176),  0x15: (160, 20, 100),  0x16: (152, 34, 32),   0x17: (120, 60, 0),
        0x18: (84, 90, 0),     0x19: (40, 114, 0),    0x1A: (8, 124, 0),     0x1B: (0, 118, 40),
        0x1C: (0, 102, 120),   0x1D: (0, 0, 0),       0x1E: (0, 0, 0),       0x1F: (0, 0, 0),
        0x20: (236, 238, 236), 0x21: (76, 154, 236),  0x22: (120, 124, 236), 0x23: (176, 98, 236),
        0x24: (228, 84, 236),  0x25: (236, 88, 180),  0x26: (236, 106, 100), 0x27: (212, 136, 32),
        0x28: (160, 170, 0),   0x29: (116, 196, 0),   0x2A: (76, 208, 32),   0x2B: (56, 204, 108),
        0x2C: (56, 180, 204),  0x2D: (60, 60, 60),    0x2E: (0, 0, 0),       0x2F: (0, 0, 0),
        0x30: (236, 238, 236), 0x31: (168, 204, 236), 0x32: (188, 188, 236), 0x33: (212, 178, 236),
        0x34: (236, 174, 236), 0x35: (236, 174, 212), 0x36: (236, 180, 176), 0x37: (228, 196, 144),
        0x38: (204, 210, 120), 0x39: (180, 222, 120), 0x3A: (168, 226, 144), 0x3B: (152, 226, 180),
        0x3C: (160, 214, 228), 0x3D: (160, 162, 160), 0x3E: (0, 0, 0),       0x3F: (0, 0, 0),
    }
    default_palette = [0x0F, 0x24, 0x2C, 0x30]  # Black, Magenta, Cyan, White (Synthwave)

    @classmethod
    def generate_tile_data(cls, indexed_img: Image.Image) -> bytes:
        """NES CHR format: 2 bitplanes, 8 bytes each per 8x8 tile"""
        pixels = list(indexed_img.getdata())
        width, height = indexed_img.size
        tiles_x = width // 8
        tiles_y = height // 8

        chr_data = bytearray()
        for ty in range(tiles_y):
            for tx in range(tiles_x):
                plane0 = bytearray(8)
                plane1 = bytearray(8)
                for row in range(8):
                    for col in range(8):
                        px = tx * 8 + col
                        py = ty * 8 + row
                        if px < width and py < height:
                            color = pixels[py * width + px] & 0x03
                            if color & 1:
                                plane0[row] |= (0x80 >> col)
                            if color & 2:
                                plane1[row] |= (0x80 >> col)
                chr_data.extend(plane0)
                chr_data.extend(plane1)
        return bytes(chr_data)

    @staticmethod
    def _encode_tile(pixels, width, x, y):
        """Encode a single 8x8 tile to NES 2bpp format"""
        plane0 = bytearray(8)
        plane1 = bytearray(8)
        for row in range(8):
            for col in range(8):
                if x + col < width: # No y check needed as it is passed carefully
                    color = pixels[(y + row) * width + (x + col)] & 0x03
                    if color & 1:
                        plane0[row] |= (0x80 >> col)
                    if color & 2:
                        plane1[row] |= (0x80 >> col)
        return plane0 + plane1

    @classmethod
    def generate_background_data(cls, indexed_img: Image.Image) -> Tuple[bytes, bytes]:
        """
        Generate NES Background Data:
        Returns: (nametable_data, chr_data)
        where nametable_data is 1024 bytes (960 NT + 64 AT)
        and chr_data is deduplicated tile bank (up to 4096 bytes)
        """
        pixels = list(indexed_img.getdata())
        width, height = indexed_img.size
        
        # NES Background is 32x30 tiles (256x240)
        # We will iterate 32x30, referencing the source image
        
        unique_tiles = {bytes([0]*64): 0} # Pre-seed empty tile at index 0
        chr_bank = bytearray([0]*64)
        nametable = bytearray(960)
        
        # 1. Tile Generation & Deduplication
        idx_counter = 1 # Start at 1
        
        for ty in range(30):
            for tx in range(32):
                x = tx * 8
                y = ty * 8
                
                # Check if we are inside image bounds
                if x >= width or y >= height:
                    # Out of bounds: use a blank tile (index 0 usually, or create one)
                    # For simplicity, we assume index 0 is valid or will be created
                    # Let's Encode a blank tile if OOB? 
                    # Actually, let's just clamp/skip.
                    tile_bytes = bytes(16) # Blank tile
                else:
                    tile_bytes = cls._encode_tile(pixels, width, x, y)
                
                # Deduplicate
                tile_hash = bytes(tile_bytes)
                if tile_hash not in unique_tiles:
                    if len(unique_tiles) >= 256:
                        # Hardware limit! 
                        # Ideally we would find the "closest" tile or error.
                        print(f"      [WARN] Background exceeds 256 unique tiles! Clipping.")
                        nametable[ty * 32 + tx] = 0
                        continue
                        
                    unique_tiles[tile_hash] = idx_counter
                    chr_bank.extend(tile_bytes)
                    idx_counter += 1
                
                nametable[ty * 32 + tx] = unique_tiles[tile_hash]

        # 2. Attribute Table (64 bytes)
        # For now, simplistic approach: Assume Palette 0 applies to everything.
        # Ideally, we would look at the colors used in the 16x16 blocks.
        # But 'indexed_img' is usually 0-3 (one palette). 
        # So Attribute Table is all zeros.
        attr_table = bytes(64)
        
        return (bytes(nametable) + attr_table, bytes(chr_bank))

    @classmethod
    def generate_nametable(cls, indexed_img: Image.Image, tile_data: bytes) -> bytes:

        """
        Generate NES Nametable (32x30 tile indices) + Attribute Table.
        Assumes 'tile_data' contains the deduplicated CHR bank used by this map.
        """
        width, height = indexed_img.size
        # NES screen is 256x240 (32x30 tiles)
        # If image is larger/smaller, we might need resizing or cropping, but assume 256x240 for now.
        
        # 1. Build Name Table (960 bytes)
        nametable = bytearray(960)
        
        # We need to match each 8x8 tile in the image to a tile in 'tile_data'
        # This requires reconstructing the image tiles and comparing.
        # For efficiency, let's assume 'indexed_img' is what produced 'tile_data'.
        # IF tile_data is exactly the linear tiles of the image (no dedup), then:
        #   indices are just 0, 1, 2... 
        # BUT standard unique processing enables dedup.
        
        # Re-extract tiles from image
        img_tiles = []
        pixels = list(indexed_img.getdata())
        for ty in range(30):
            for tx in range(32):
                # Extract 8x8 tile
                single_tile = bytearray()
                # ... encoding logic similar to generate_tile_data ...
                # This suggests we should refactor tile encoding to single tile helper.
                pass
                
        # SIMPLIFICATION:
        # Since we are modifying the pipeline, let's update `generate_tile_data` to return 
        # both (chr_data, map_data) OR make a new `generate_full_screen_data` method?
        
        # Let's add a placeholder for now and implement the helper refactor next.
        return bytearray(1024) 



class GenesisConfig(PlatformConfig):
    """Sega Genesis / Megadrive - Primary 68000 target platform"""

    # Identity
    name = "Genesis"
    full_name = "Sega Genesis / Mega Drive"
    manufacturer = "Sega"
    year = 1988
    generation = 4

    # Graphics
    tile_width = 8
    tile_height = 8
    bits_per_pixel = 4
    colors_per_palette = 16     # 15 colors + transparent
    max_palettes = 4            # 4 palettes of 16 colors each
    max_sprite_width = 32       # 4 tiles wide
    max_sprite_height = 32      # 4 tiles tall
    max_sprites_total = 80      # 80 sprites in sprite table
    max_sprites_per_line = 20   # 20 sprites per scanline
    bytes_per_tile = 32         # 4bpp, 8x8 = 32 bytes
    output_extension = ".bin"
    screen_width = 320          # 320 or 256 mode
    screen_height = 224         # 224 or 240 (PAL)
    video_chip = "VDP (315-5313)"
    tile_based_bg = True

    # Genesis dithering: 16 colors allows smoother gradients, lighter dithering
    dither_method = "ordered"
    dither_matrix_size = 4
    dither_strength = 0.8           # Less aggressive - 16 colors is plenty

    # Hardware - 68000 main CPU + Z80 for audio
    cpu_name = "Motorola 68000"
    cpu_family = "68000"
    cpu_bits = 16               # 16-bit data bus, 32-bit internal
    cpu_speed_mhz = 7.67        # 7.6704 MHz (NTSC)
    cpu_endian = "big"          # 68000 is big-endian!

    ram_start = 0xFF0000        # Work RAM at $FF0000-$FFFFFF
    ram_size = 0x10000          # 64KB main RAM
    rom_start = 0x000000        # ROM at $000000-$3FFFFF
    rom_size = 0x400000         # 4MB max ROM
    vram_start = 0xC00000       # VDP VRAM access via ports
    vram_size = 0x10000         # 64KB VRAM

    # No zero page on 68000, but has address registers
    zp_start = 0
    zp_size = 0
    stack_start = 0xFFFFFC      # Stack grows down from top of RAM
    stack_size = 0x1000         # ~4KB typical

    mapper_name = "None"        # Genesis uses linear ROM (up to 4MB)
    prg_bank_size = 0x80000     # No fixed banks, but SRAM at $200000
    chr_bank_size = 0           # No CHR ROM, tiles in VRAM
    max_prg_banks = 1
    max_chr_banks = 0

    # Build system - SGDK (Sega Genesis Development Kit)
    toolchain = "sgdk"
    assembler = "m68k-elf-as"
    compiler = "m68k-elf-gcc"
    linker = "m68k-elf-ld"
    rom_tool = "rom_head"       # SGDK ROM header tool
    asm_extension = ".s"        # GNU as convention
    obj_extension = ".o"
    rom_extension = ".bin"
    asm_flags = ["-m68000"]
    link_flags = ["-T", "md.ld"]

    # Audio - YM2612 FM + SN76489 PSG (via Z80)
    audio_chip = "YM2612 + SN76489"
    audio_channels = 10         # 6 FM + 4 PSG
    audio_type = "fm"
    music_driver = "echo"       # Echo sound engine, or XGM
    tracker_format = "vgm"      # VGM or DefleMask

    # Constraints
    cycle_budget_per_frame = 127137  # ~127k cycles at 7.67MHz/60fps
    vblank_cycles = 10000       # Approximate VBlank time
    dma_available = True        # VDP DMA for fast VRAM transfers
    has_multiply = True         # 68000 has MULS/MULU
    has_divide = True           # 68000 has DIVS/DIVU
    fast_zero_page = False      # No ZP, but register-based ops are fast

    # HAL Tier Integration
    hal_tier = 1                # STANDARD
    hal_tier_name = "STANDARD"
    hal_platform_id = 0x0300    # ARDK_PLAT_GENESIS
    hal_max_entities = 128      # From hal_tiers.h STANDARD tier
    hal_max_enemies = 48
    hal_max_projectiles = 48
    hal_max_pickups = 32
    hal_max_effects = 24

    # Genesis 9-bit RGB palette (512 colors, showing common values)
    # Format: 0000BBB0GGG0RRR0 - 3 bits per channel
    palette_rgb = {i: ((i & 0xE) << 4, (i & 0xE0) >> 1, (i & 0xE00) >> 6)
                   for i in range(512)}
    # Override with common synthwave colors
    palette_rgb.update({
        0x000: (0, 0, 0),         # Black
        0xE0E: (224, 0, 224),     # Magenta
        0x0EE: (0, 224, 224),     # Cyan
        0xEEE: (224, 224, 224),   # White
        0xE00: (224, 0, 0),       # Red
        0x0E0: (0, 224, 0),       # Green
        0x00E: (0, 0, 224),       # Blue
    })
    default_palette = [0x000, 0xE0E, 0x0EE, 0xEEE,
                       0x444, 0x888, 0xCCC, 0xE00,
                       0x0E0, 0x00E, 0xEE0, 0x0EE,
                       0xE0E, 0x666, 0xAAA, 0xEEE]

    @classmethod
    def generate_tile_data(cls, indexed_img: Image.Image) -> bytes:
        """Genesis tile format: 4bpp planar, 32 bytes per 8x8 tile"""
        pixels = list(indexed_img.getdata())
        width, height = indexed_img.size
        tiles_x = width // 8
        tiles_y = height // 8

        tile_data = bytearray()
        for ty in range(tiles_y):
            for tx in range(tiles_x):
                for row in range(8):
                    for col in range(0, 8, 2):
                        px1 = tx * 8 + col
                        px2 = tx * 8 + col + 1
                        py = ty * 8 + row
                        c1 = pixels[py * width + px1] & 0x0F if px1 < width and py < height else 0
                        c2 = pixels[py * width + px2] & 0x0F if px2 < width and py < height else 0
                        tile_data.append((c1 << 4) | c2)
        return bytes(tile_data)


class SNESConfig(PlatformConfig):
    """Super Nintendo / Super Famicom"""

    name = "SNES"
    tile_width = 8
    tile_height = 8
    bits_per_pixel = 4
    colors_per_palette = 16     # 15 colors + transparent
    max_sprite_width = 64       # Up to 64x64 with mode settings
    max_sprite_height = 64
    bytes_per_tile = 32         # 4bpp interleaved
    output_extension = ".bin"

    # SNES 15-bit RGB (32768 colors)
    # Format: 0BBBBBGGGGGRRRRR
    palette_rgb = {}  # Generated dynamically
    default_palette = [0x0000, 0x7C1F, 0x03FF, 0x7FFF,
                       0x294A, 0x4E73, 0x739C, 0x001F,
                       0x03E0, 0x7C00, 0x03FF, 0x7C1F,
                       0x7FE0, 0x4210, 0x6318, 0x7FFF]

    @classmethod
    def _rgb_to_snes(cls, r: int, g: int, b: int) -> int:
        return ((b >> 3) << 10) | ((g >> 3) << 5) | (r >> 3)

    @classmethod
    def _snes_to_rgb(cls, snes: int) -> Tuple[int, int, int]:
        r = (snes & 0x1F) << 3
        g = ((snes >> 5) & 0x1F) << 3
        b = ((snes >> 10) & 0x1F) << 3
        return (r, g, b)

    @classmethod
    def get_palette_rgb(cls, palette_indices: List[int]) -> List[Tuple[int, int, int]]:
        return [cls._snes_to_rgb(idx) for idx in palette_indices]

    @classmethod
    def generate_tile_data(cls, indexed_img: Image.Image) -> bytes:
        """SNES 4bpp format: interleaved bitplanes"""
        pixels = list(indexed_img.getdata())
        width, height = indexed_img.size
        tiles_x = width // 8
        tiles_y = height // 8

        tile_data = bytearray()
        for ty in range(tiles_y):
            for tx in range(tiles_x):
                # SNES 4bpp: planes 0&1 interleaved, then planes 2&3
                planes = [bytearray(8) for _ in range(4)]
                for row in range(8):
                    for col in range(8):
                        px = tx * 8 + col
                        py = ty * 8 + row
                        color = pixels[py * width + px] & 0x0F if px < width and py < height else 0
                        for plane in range(4):
                            if color & (1 << plane):
                                planes[plane][row] |= (0x80 >> col)
                # Interleave: row0_p0, row0_p1, row1_p0, row1_p1, ...
                for row in range(8):
                    tile_data.append(planes[0][row])
                    tile_data.append(planes[1][row])
                for row in range(8):
                    tile_data.append(planes[2][row])
                    tile_data.append(planes[3][row])
        return bytes(tile_data)


class AmigaConfig(PlatformConfig):
    """Commodore Amiga OCS/ECS - 32 colors (5 bitplanes)"""

    name = "Amiga"
    tile_width = 16             # Amiga blitter prefers 16px wide
    tile_height = 16
    bits_per_pixel = 5          # 5 bitplanes = 32 colors (OCS/ECS max)
    colors_per_palette = 32     # OCS/ECS can display 32 colors simultaneously
    max_sprite_width = 16       # Hardware sprites are 16px wide (4 colors each)
    max_sprite_height = 255     # Virtually unlimited height
    bytes_per_tile = 160        # 16x16 @ 5bpp = 160 bytes
    output_extension = ".raw"

    # Amiga 12-bit RGB (4096 colors total palette)
    # OCS/ECS: 12-bit color (4 bits per channel = 4096 colors)
    palette_rgb = {}  # 12-bit: 0x0RGB
    # 32-color synthwave palette
    default_palette = [
        0x000, 0xF0F, 0x0FF, 0xFFF,  # Black, Magenta, Cyan, White
        0x444, 0x888, 0xCCC, 0xF00,  # Greys, Red
        0x0F0, 0x00F, 0xFF0, 0x0FF,  # Green, Blue, Yellow, Cyan
        0xF0F, 0x606, 0x066, 0xF6F,  # Magenta shades
        0x808, 0x088, 0xF8F, 0x8F8,  # More shades
        0x0F8, 0xF08, 0x80F, 0x0F0,  # Neon colors
        0xF80, 0x08F, 0xAA0, 0x0AA,  # More neons
        0xA0A, 0x666, 0x999, 0xEEE,  # Final shades
    ]

    @classmethod
    def _amiga_to_rgb(cls, amiga: int) -> Tuple[int, int, int]:
        r = ((amiga >> 8) & 0xF) * 17
        g = ((amiga >> 4) & 0xF) * 17
        b = (amiga & 0xF) * 17
        return (r, g, b)

    @classmethod
    def get_palette_rgb(cls, palette_indices: List[int]) -> List[Tuple[int, int, int]]:
        return [cls._amiga_to_rgb(idx) for idx in palette_indices]

    @classmethod
    def generate_tile_data(cls, indexed_img: Image.Image) -> bytes:
        """Amiga planar format: 5 separate bitplanes for 32 colors"""
        pixels = list(indexed_img.getdata())
        width, height = indexed_img.size
        num_planes = cls.bits_per_pixel  # 5 for OCS/ECS, 8 for AGA

        # Amiga stores bitplanes separately
        planes = [bytearray() for _ in range(num_planes)]
        for y in range(height):
            for plane in range(num_planes):
                row_data = 0
                for x in range(width):
                    color = pixels[y * width + x] & ((1 << num_planes) - 1)
                    if color & (1 << plane):
                        row_data |= (1 << (7 - (x % 8)))
                    if (x + 1) % 8 == 0:
                        planes[plane].append(row_data)
                        row_data = 0
                if width % 8 != 0:
                    planes[plane].append(row_data)

        # Interleave planes (common Amiga format)
        result = bytearray()
        bytes_per_row = (width + 7) // 8
        for y in range(height):
            for plane in range(num_planes):
                start = y * bytes_per_row
                result.extend(planes[plane][start:start + bytes_per_row])
        return bytes(result)


class AmigaAGAConfig(AmigaConfig):
    """Commodore Amiga AGA - 256 colors (8 bitplanes), 24-bit palette"""

    name = "AmigaAGA"
    bits_per_pixel = 8          # 8 bitplanes = 256 colors
    colors_per_palette = 256    # AGA can display 256 colors simultaneously
    bytes_per_tile = 256        # 16x16 @ 8bpp = 256 bytes

    # AGA uses 24-bit RGB palette (16M colors)
    # For default, we'll use a gradient-friendly 256-color synthwave palette
    default_palette = list(range(256))  # Placeholder - actual colors set by get_palette_rgb

    @classmethod
    def _amiga_to_rgb(cls, amiga: int) -> Tuple[int, int, int]:
        """AGA: Full 24-bit RGB if > 0xFFF, else 12-bit compatible"""
        if amiga > 0xFFF:
            # 24-bit RGB: 0xRRGGBB
            r = (amiga >> 16) & 0xFF
            g = (amiga >> 8) & 0xFF
            b = amiga & 0xFF
            return (r, g, b)
        else:
            # 12-bit RGB compatible: 0x0RGB
            r = ((amiga >> 8) & 0xF) * 17
            g = ((amiga >> 4) & 0xF) * 17
            b = (amiga & 0xF) * 17
            return (r, g, b)


class PCEngineConfig(PlatformConfig):
    """NEC PC Engine / TurboGrafx-16"""

    name = "PCEngine"
    tile_width = 8
    tile_height = 8
    bits_per_pixel = 4
    colors_per_palette = 16
    max_sprite_width = 32       # 16 or 32 px wide
    max_sprite_height = 64      # Up to 64 px tall
    bytes_per_tile = 32         # 4bpp
    output_extension = ".bin"

    # PC Engine 9-bit RGB (512 colors)
    # Format: GGGRRRBBB
    palette_rgb = {}
    default_palette = [0x000, 0x1B6, 0x0DB, 0x1FF,
                       0x092, 0x124, 0x1B6, 0x007,
                       0x038, 0x1C0, 0x03F, 0x1B6,
                       0x1F8, 0x0DB, 0x16D, 0x1FF]

    @classmethod
    def _pce_to_rgb(cls, pce: int) -> Tuple[int, int, int]:
        g = ((pce >> 6) & 0x7) * 36
        r = ((pce >> 3) & 0x7) * 36
        b = (pce & 0x7) * 36
        return (r, g, b)

    @classmethod
    def get_palette_rgb(cls, palette_indices: List[int]) -> List[Tuple[int, int, int]]:
        return [cls._pce_to_rgb(idx) for idx in palette_indices]

    @classmethod
    def generate_tile_data(cls, indexed_img: Image.Image) -> bytes:
        """PCE tile format: similar to SNES 4bpp"""
        # PCE uses same interleaved format as SNES for sprites
        return SNESConfig.generate_tile_data(indexed_img)


class C64Config(PlatformConfig):
    """Commodore 64 - Fixed 16-color palette with multicolor mode"""

    name = "C64"
    tile_width = 8
    tile_height = 8
    bits_per_pixel = 2          # Multicolor mode: 4 colors per 4x8 cell
    colors_per_palette = 4      # 3 colors + shared bg/multicolor
    max_sprite_width = 24       # Hardware sprites 24x21
    max_sprite_height = 21
    bytes_per_tile = 64         # 24x21 sprite = 63 bytes + 1 padding
    output_extension = ".spr"
    resample_mode = "NEAREST"   # Authentic pixel look

    # C64 fixed 16-color palette (VIC-II)
    # These are the exact hardware colors
    palette_rgb = {
        0x0: (0, 0, 0),         # Black
        0x1: (255, 255, 255),   # White
        0x2: (136, 0, 0),       # Red
        0x3: (170, 255, 238),   # Cyan
        0x4: (204, 68, 204),    # Purple
        0x5: (0, 204, 85),      # Green
        0x6: (0, 0, 170),       # Blue
        0x7: (238, 238, 119),   # Yellow
        0x8: (221, 136, 85),    # Orange
        0x9: (102, 68, 0),      # Brown
        0xA: (255, 119, 119),   # Light Red
        0xB: (51, 51, 51),      # Dark Grey
        0xC: (119, 119, 119),   # Grey
        0xD: (170, 255, 102),   # Light Green
        0xE: (0, 136, 255),     # Light Blue
        0xF: (187, 187, 187),   # Light Grey
    }
    # Synthwave-ish C64 palette: Black, Purple, Cyan, White
    default_palette = [0x0, 0x4, 0x3, 0x1]

    @classmethod
    def get_palette_rgb(cls, palette_indices: List[int]) -> List[Tuple[int, int, int]]:
        return [cls.palette_rgb.get(idx & 0xF, (0, 0, 0)) for idx in palette_indices]

    @classmethod
    def generate_tile_data(cls, indexed_img: Image.Image) -> bytes:
        """C64 sprite format: 24x21 pixels, 3 bytes per row, MSB first"""
        pixels = list(indexed_img.getdata())
        width, height = indexed_img.size

        # C64 sprites are 24x21, pad/crop as needed
        sprite_w, sprite_h = 24, 21
        sprite_data = bytearray()

        for y in range(sprite_h):
            for byte_x in range(3):  # 3 bytes per row (24 pixels)
                byte_val = 0
                for bit in range(8):
                    x = byte_x * 8 + bit
                    if x < width and y < height:
                        color = pixels[y * width + x] & 0x03
                        # Multicolor mode: 2 bits per pixel, but we use hires for simplicity
                        if color > 0:
                            byte_val |= (0x80 >> bit)
                sprite_data.append(byte_val)

        # Pad to 64 bytes (standard C64 sprite block)
        while len(sprite_data) < 64:
            sprite_data.append(0)

        return bytes(sprite_data)


class CGAConfig(PlatformConfig):
    """IBM CGA - 4 fixed color palettes"""

    name = "CGA"
    tile_width = 8
    tile_height = 8
    bits_per_pixel = 2
    colors_per_palette = 4
    max_sprite_width = 320      # No hardware sprites, all software
    max_sprite_height = 200
    bytes_per_tile = 16         # 8x8 @ 2bpp = 16 bytes
    output_extension = ".cga"
    resample_mode = "NEAREST"   # Authentic pixel look

    # CGA has 2 main palettes in 320x200 4-color mode
    # Palette 0: Black, Green, Red, Yellow/Brown
    # Palette 1: Black, Cyan, Magenta, White
    PALETTE_0_LOW = {0: (0,0,0), 1: (0,170,0), 2: (170,0,0), 3: (170,85,0)}
    PALETTE_0_HIGH = {0: (0,0,0), 1: (85,255,85), 2: (255,85,85), 3: (255,255,85)}
    PALETTE_1_LOW = {0: (0,0,0), 1: (0,170,170), 2: (170,0,170), 3: (170,170,170)}
    PALETTE_1_HIGH = {0: (0,0,0), 1: (85,255,255), 2: (255,85,255), 3: (255,255,255)}

    # Default to high-intensity Palette 1 (Cyan-Magenta-White) for synthwave look
    palette_rgb = PALETTE_1_HIGH
    default_palette = [0, 1, 2, 3]  # Direct indices into 4-color palette

    @classmethod
    def get_palette_rgb(cls, palette_indices: List[int]) -> List[Tuple[int, int, int]]:
        return [cls.palette_rgb.get(idx & 0x03, (0, 0, 0)) for idx in palette_indices]

    @classmethod
    def generate_tile_data(cls, indexed_img: Image.Image) -> bytes:
        """CGA 2bpp format: 4 pixels per byte, MSB first"""
        pixels = list(indexed_img.getdata())
        width, height = indexed_img.size

        tile_data = bytearray()
        for y in range(height):
            for x in range(0, width, 4):
                byte_val = 0
                for px in range(4):
                    if x + px < width:
                        color = pixels[y * width + x + px] & 0x03
                        byte_val |= (color << (6 - px * 2))
                tile_data.append(byte_val)

        return bytes(tile_data)


class GameBoyConfig(PlatformConfig):
    """Nintendo Game Boy (DMG) - 4 shades of green, massive homebrew scene"""

    # Identity
    name = "GameBoy"
    full_name = "Nintendo Game Boy"
    manufacturer = "Nintendo"
    year = 1989
    generation = 4  # Handheld, same era as Genesis/SNES

    # Graphics
    tile_width = 8
    tile_height = 8
    bits_per_pixel = 2
    colors_per_palette = 4      # 4 shades per palette
    max_palettes = 2            # 1 BG palette, 2 OBJ palettes (shared)
    max_sprite_width = 8        # 8x8 or 8x16 sprites
    max_sprite_height = 16      # 8x16 in tall sprite mode
    max_sprites_total = 40      # OAM holds 40 sprites
    max_sprites_per_line = 10   # 10 sprites per scanline
    bytes_per_tile = 16         # 2bpp, same as NES
    output_extension = ".2bpp"  # Standard GB tile format
    resample_mode = "NEAREST"   # Authentic pixel look
    screen_width = 160
    screen_height = 144
    video_chip = "Sharp LR35902 PPU"
    tile_based_bg = True

    # Hardware - Sharp LR35902 (Z80 variant, NOT true Z80)
    cpu_name = "Sharp LR35902"
    cpu_family = "z80"          # Z80-like but reduced instruction set
    cpu_bits = 8
    cpu_speed_mhz = 4.19        # 4.194304 MHz
    cpu_endian = "little"

    ram_start = 0xC000          # Work RAM
    ram_size = 0x2000           # 8KB internal RAM
    rom_start = 0x0000          # Cartridge ROM at $0000-$7FFF
    rom_size = 0x8000           # 32KB visible (banked beyond)
    vram_start = 0x8000         # Video RAM at $8000-$9FFF
    vram_size = 0x2000          # 8KB VRAM

    zp_start = 0xFF80           # HRAM (high RAM) - fast access
    zp_size = 0x7F              # 127 bytes of HRAM
    stack_start = 0xFFFE        # Stack at top of HRAM
    stack_size = 0x7E           # Limited by HRAM

    mapper_name = "MBC1"        # Most common mapper
    prg_bank_size = 0x4000      # 16KB ROM banks
    chr_bank_size = 0           # No separate CHR, tiles in VRAM
    max_prg_banks = 128         # Up to 2MB ROM (MBC5)
    max_chr_banks = 0

    # Build system - GBDK-2020 or RGBDS
    toolchain = "rgbds"         # RGBDS is pure ASM, GBDK for C
    assembler = "rgbasm"
    compiler = "lcc"            # GBDK uses SDCC-based lcc
    linker = "rgblink"
    rom_tool = "rgbfix"         # Fixes ROM header
    asm_extension = ".asm"
    obj_extension = ".o"
    rom_extension = ".gb"
    asm_flags = []
    link_flags = ["-m", "game.map", "-n", "game.sym"]

    # Audio
    audio_chip = "LR35902 APU"
    audio_channels = 4          # 2 pulse, 1 wave, 1 noise
    audio_type = "psg"
    music_driver = "hUGEDriver"
    tracker_format = "uge"      # hUGETracker

    # Constraints
    cycle_budget_per_frame = 70224  # ~70k cycles at 4.19MHz/59.7fps
    vblank_cycles = 4560        # Mode 1 (VBlank) duration
    dma_available = True        # OAM DMA via $FF46
    has_multiply = False
    has_divide = False
    fast_zero_page = True       # HRAM is faster (1 cycle less)

    # HAL Tier Integration
    hal_tier = 0                # MINIMAL
    hal_tier_name = "MINIMAL"
    hal_platform_id = 0x0200    # ARDK_PLAT_GB
    hal_max_entities = 32       # Limited RAM
    hal_max_enemies = 12
    hal_max_projectiles = 16
    hal_max_pickups = 16
    hal_max_effects = 8

    # Classic Game Boy green shades (DMG-01)
    # These approximate the actual LCD colors
    palette_rgb = {
        0: (155, 188, 15),      # Lightest (off/white)
        1: (139, 172, 15),      # Light
        2: (48, 98, 48),        # Dark
        3: (15, 56, 15),        # Darkest (on/black)
    }
    # Alt: Pocket/Light grayscale
    PALETTE_POCKET = {0: (255,255,255), 1: (170,170,170), 2: (85,85,85), 3: (0,0,0)}

    default_palette = [0, 1, 2, 3]

    @classmethod
    def get_palette_rgb(cls, palette_indices: List[int]) -> List[Tuple[int, int, int]]:
        return [cls.palette_rgb.get(idx & 0x03, (155, 188, 15)) for idx in palette_indices]

    @classmethod
    def generate_tile_data(cls, indexed_img: Image.Image) -> bytes:
        """Game Boy 2bpp format: identical to NES CHR (2 bitplanes interleaved per row)"""
        # GB uses same 2bpp format as NES
        pixels = list(indexed_img.getdata())
        width, height = indexed_img.size
        tiles_x = width // 8
        tiles_y = height // 8

        tile_data = bytearray()
        for ty in range(tiles_y):
            for tx in range(tiles_x):
                for row in range(8):
                    # Low bits first, then high bits (per row)
                    low_byte = 0
                    high_byte = 0
                    for col in range(8):
                        px = tx * 8 + col
                        py = ty * 8 + row
                        if px < width and py < height:
                            color = pixels[py * width + px] & 0x03
                            if color & 1:
                                low_byte |= (0x80 >> col)
                            if color & 2:
                                high_byte |= (0x80 >> col)
                    tile_data.append(low_byte)
                    tile_data.append(high_byte)

        return bytes(tile_data)


class GameBoyColorConfig(PlatformConfig):
    """Nintendo Game Boy Color - 56 colors on screen, huge homebrew community"""

    name = "GBC"
    tile_width = 8
    tile_height = 8
    bits_per_pixel = 2          # Still 2bpp tiles, but more palettes
    colors_per_palette = 4      # 4 colors per palette
    max_sprite_width = 8
    max_sprite_height = 16
    bytes_per_tile = 16
    output_extension = ".2bpp"
    resample_mode = "NEAREST"

    # GBC uses 15-bit RGB (same as SNES): 0BBBBBGGGGGRRRRR
    # Can display 8 BG palettes + 8 sprite palettes = 56 unique colors on screen
    # Total palette: 32768 colors
    palette_rgb = {}  # Dynamically converted from 15-bit

    # Synthwave GBC palette
    default_palette = [
        0x0000,  # Black
        0x7C1F,  # Magenta (R=31, G=0, B=31)
        0x03FF,  # Cyan (R=31, G=31, B=0)
        0x7FFF,  # White
    ]

    @classmethod
    def _gbc_to_rgb(cls, gbc: int) -> Tuple[int, int, int]:
        """Convert 15-bit GBC color to RGB"""
        r = (gbc & 0x1F) << 3
        g = ((gbc >> 5) & 0x1F) << 3
        b = ((gbc >> 10) & 0x1F) << 3
        return (r, g, b)

    @classmethod
    def get_palette_rgb(cls, palette_indices: List[int]) -> List[Tuple[int, int, int]]:
        return [cls._gbc_to_rgb(idx) for idx in palette_indices]

    @classmethod
    def generate_tile_data(cls, indexed_img: Image.Image) -> bytes:
        """GBC uses same 2bpp tile format as DMG Game Boy"""
        return GameBoyConfig.generate_tile_data(indexed_img)


class MasterSystemConfig(PlatformConfig):
    """Sega Master System / Game Gear - Active homebrew scene"""

    name = "SMS"
    tile_width = 8
    tile_height = 8
    bits_per_pixel = 4
    colors_per_palette = 16     # 16 colors from 64 (SMS) or 4096 (GG)
    max_sprite_width = 8        # 8x8 or 8x16
    max_sprite_height = 16
    bytes_per_tile = 32         # 4bpp planar
    output_extension = ".sms"

    # SMS uses 6-bit RGB (2 bits per channel = 64 colors)
    # Format: 00BBGGRR
    palette_rgb = {i: (
        (i & 0x03) * 85,        # R: bits 0-1
        ((i >> 2) & 0x03) * 85, # G: bits 2-3
        ((i >> 4) & 0x03) * 85  # B: bits 4-5
    ) for i in range(64)}

    default_palette = [
        0x00,  # Black
        0x33,  # Magenta-ish (R=3, G=0, B=3)
        0x0F,  # Cyan-ish (R=3, G=3, B=0)
        0x3F,  # White
        0x15, 0x2A, 0x3E, 0x01,
        0x02, 0x04, 0x08, 0x10,
        0x20, 0x14, 0x28, 0x3C,
    ]

    @classmethod
    def get_palette_rgb(cls, palette_indices: List[int]) -> List[Tuple[int, int, int]]:
        return [cls.palette_rgb.get(idx & 0x3F, (0, 0, 0)) for idx in palette_indices]

    @classmethod
    def generate_tile_data(cls, indexed_img: Image.Image) -> bytes:
        """SMS 4bpp planar format: 4 bitplanes interleaved per row"""
        pixels = list(indexed_img.getdata())
        width, height = indexed_img.size
        tiles_x = width // 8
        tiles_y = height // 8

        tile_data = bytearray()
        for ty in range(tiles_y):
            for tx in range(tiles_x):
                for row in range(8):
                    # SMS: 4 bitplanes per row, interleaved
                    planes = [0, 0, 0, 0]
                    for col in range(8):
                        px = tx * 8 + col
                        py = ty * 8 + row
                        if px < width and py < height:
                            color = pixels[py * width + px] & 0x0F
                            for plane in range(4):
                                if color & (1 << plane):
                                    planes[plane] |= (0x80 >> col)
                    for plane in planes:
                        tile_data.append(plane)

        return bytes(tile_data)


class Atari2600Config(PlatformConfig):
    """Atari 2600 (VCS) - Challenging but active homebrew scene"""

    name = "Atari2600"
    tile_width = 8
    tile_height = 1             # 2600 is scanline-based, not tile-based
    bits_per_pixel = 1          # Sprites are 1bpp (player graphics)
    colors_per_palette = 2      # Foreground + background per scanline
    max_sprite_width = 8        # Player graphics are 8 pixels wide
    max_sprite_height = 192     # Full screen height
    bytes_per_tile = 1          # 1 byte = 8 pixels
    output_extension = ".a26"
    resample_mode = "NEAREST"

    # Atari 2600 NTSC palette (128 colors)
    # Simplified to common colors - full palette is luminance + hue
    palette_rgb = {
        0x00: (0, 0, 0),        # Black
        0x0E: (255, 255, 255),  # White
        0x46: (255, 0, 255),    # Magenta
        0x9A: (0, 255, 255),    # Cyan
        0x26: (255, 0, 0),      # Red
        0xC6: (0, 255, 0),      # Green
        0x86: (0, 0, 255),      # Blue
        0x1E: (255, 255, 0),    # Yellow
    }

    default_palette = [0x00, 0x46]  # Black background, Magenta foreground

    @classmethod
    def get_palette_rgb(cls, palette_indices: List[int]) -> List[Tuple[int, int, int]]:
        return [cls.palette_rgb.get(idx, (0, 0, 0)) for idx in palette_indices]

    @classmethod
    def generate_tile_data(cls, indexed_img: Image.Image) -> bytes:
        """Atari 2600 player graphics: 1bpp, one byte per scanline"""
        pixels = list(indexed_img.getdata())
        width, height = indexed_img.size

        # Output 8 pixels wide, full height
        sprite_data = bytearray()
        for y in range(height):
            byte_val = 0
            for x in range(min(8, width)):
                if x < width and pixels[y * width + x] > 0:
                    byte_val |= (0x80 >> x)
            sprite_data.append(byte_val)

        return bytes(sprite_data)


class GBAConfig(PlatformConfig):
    """Nintendo Game Boy Advance - 32,768 colors, huge homebrew scene, ARM architecture"""

    # Identity
    name = "GBA"
    full_name = "Nintendo Game Boy Advance"
    manufacturer = "Nintendo"
    year = 2001
    generation = 6  # Same gen as PS2/GameCube/Xbox

    # Graphics
    tile_width = 8
    tile_height = 8
    bits_per_pixel = 4          # 4bpp (16 colors) or 8bpp (256 colors)
    colors_per_palette = 16     # 16 palettes of 16 colors = 256 sprite colors
    max_palettes = 16           # 16 sprite palettes
    max_sprite_width = 64       # Up to 64x64 sprites
    max_sprite_height = 64
    max_sprites_total = 128     # OAM holds 128 sprites
    max_sprites_per_line = 128  # Limited by pixel bandwidth, not count
    bytes_per_tile = 32         # 4bpp: 32 bytes per 8x8 tile
    output_extension = ".gba"
    resample_mode = "LANCZOS"
    screen_width = 240
    screen_height = 160
    video_chip = "Custom PPU"
    tile_based_bg = True        # Modes 0-2 are tiled, 3-5 are bitmap

    # Hardware - ARM7TDMI (first ARM in our kit!)
    cpu_name = "ARM7TDMI"
    cpu_family = "arm"
    cpu_bits = 32
    cpu_speed_mhz = 16.78       # 16.78 MHz
    cpu_endian = "little"

    ram_start = 0x02000000      # EWRAM (external work RAM)
    ram_size = 0x40000          # 256KB EWRAM
    rom_start = 0x08000000      # Game Pak ROM
    rom_size = 0x2000000        # 32MB max ROM
    vram_start = 0x06000000     # VRAM
    vram_size = 0x18000         # 96KB VRAM

    # IWRAM (internal work RAM) - fast 32-bit access
    zp_start = 0x03000000       # IWRAM (fast RAM)
    zp_size = 0x8000            # 32KB IWRAM
    stack_start = 0x03007F00    # Stack in IWRAM
    stack_size = 0x400          # ~1KB typical

    mapper_name = "None"        # Linear ROM access
    prg_bank_size = 0x2000000   # No banking needed
    chr_bank_size = 0
    max_prg_banks = 1
    max_chr_banks = 0

    # Build system - devkitPro / devkitARM
    toolchain = "devkitpro"
    assembler = "arm-none-eabi-as"
    compiler = "arm-none-eabi-gcc"
    linker = "arm-none-eabi-ld"
    rom_tool = "gbafix"
    asm_extension = ".s"
    obj_extension = ".o"
    rom_extension = ".gba"
    asm_flags = ["-mthumb", "-mthumb-interwork"]
    link_flags = ["-specs=gba.specs"]

    # Audio
    audio_chip = "GBA PWM"
    audio_channels = 6          # 4 GB channels + 2 DMA channels
    audio_type = "pcm"          # DMA sound is PCM
    music_driver = "maxmod"     # Or Krawall, libgba audio
    tracker_format = "xm"       # MOD/XM via maxmod

    # Constraints
    cycle_budget_per_frame = 280896  # ~280k cycles at 16.78MHz/59.7fps
    vblank_cycles = 83776       # VBlank + HBlank time
    dma_available = True        # 4 DMA channels
    has_multiply = True         # ARM has MUL, MLA
    has_divide = False          # No hardware divide (use BIOS SWI)
    fast_zero_page = True       # IWRAM is 32-bit, faster than ROM

    # GBA uses 15-bit RGB (same as GBC/SNES): 0BBBBBGGGGGRRRRR
    # But stored little-endian in memory
    palette_rgb = {}

    # Synthwave GBA palette (16 colors)
    default_palette = [
        0x0000,  # Transparent/Black
        0x7C1F,  # Magenta
        0x03FF,  # Cyan
        0x7FFF,  # White
        0x0010,  # Dark blue
        0x4210,  # Dark grey
        0x6318,  # Medium grey
        0x001F,  # Red
        0x03E0,  # Green
        0x7C00,  # Blue
        0x03FF,  # Yellow-ish
        0x7C1F,  # Pink
        0x7FE0,  # Light cyan
        0x5294,  # Mid grey
        0x739C,  # Light grey
        0x7FFF,  # White
    ]

    @classmethod
    def _gba_to_rgb(cls, gba: int) -> Tuple[int, int, int]:
        """Convert 15-bit GBA color to RGB (same as SNES/GBC)"""
        r = (gba & 0x1F) << 3
        g = ((gba >> 5) & 0x1F) << 3
        b = ((gba >> 10) & 0x1F) << 3
        return (r, g, b)

    @classmethod
    def get_palette_rgb(cls, palette_indices: List[int]) -> List[Tuple[int, int, int]]:
        return [cls._gba_to_rgb(idx) for idx in palette_indices]

    @classmethod
    def generate_tile_data(cls, indexed_img: Image.Image) -> bytes:
        """GBA 4bpp tile format: linear, 2 pixels per byte, little-endian"""
        pixels = list(indexed_img.getdata())
        width, height = indexed_img.size
        tiles_x = width // 8
        tiles_y = height // 8

        tile_data = bytearray()
        for ty in range(tiles_y):
            for tx in range(tiles_x):
                for row in range(8):
                    for col in range(0, 8, 2):
                        px1 = tx * 8 + col
                        px2 = tx * 8 + col + 1
                        py = ty * 8 + row
                        c1 = pixels[py * width + px1] & 0x0F if px1 < width and py < height else 0
                        c2 = pixels[py * width + px2] & 0x0F if px2 < width and py < height else 0
                        # GBA stores low nibble first (opposite of Genesis)
                        tile_data.append((c2 << 4) | c1)

        return bytes(tile_data)


class NeoGeoConfig(PlatformConfig):
    """SNK Neo Geo - Premium arcade/home system, 4096 colors, active homebrew"""

    name = "NeoGeo"
    tile_width = 16             # Neo Geo sprites are 16 pixels wide
    tile_height = 16
    bits_per_pixel = 4          # 4bpp per sprite, but 256 colors per sprite via palette
    colors_per_palette = 16     # 16 colors per palette, sprites can use different palettes
    max_sprite_width = 16       # Fixed 16px wide, but can chain horizontally
    max_sprite_height = 512     # Up to 32 tiles tall (512 pixels!)
    bytes_per_tile = 128        # 16x16 @ 4bpp = 128 bytes
    output_extension = ".neo"
    resample_mode = "LANCZOS"

    # Neo Geo uses 16-bit color: DRGB (D=dark bit, 5 bits each RGB)
    # Format: D RRRRR GGGGG BBBBB
    palette_rgb = {}

    # Synthwave palette for Neo Geo
    default_palette = [
        0x0000,  # Black (transparent)
        0x8010,  # Dark magenta
        0x001F,  # Bright magenta (R=0, G=0, B=31)
        0x03E0,  # Bright cyan (R=0, G=31, B=0)
        0x7FFF,  # White
        0x4210,  # Dark grey
        0x6318,  # Medium grey
        0x0200,  # Dark cyan
        0x7C00,  # Bright red
        0x03E0,  # Bright green
        0x001F,  # Bright blue
        0x7FE0,  # Yellow
        0x7C1F,  # Pink
        0x5294,  # Mid tone
        0x739C,  # Light grey
        0x7FFF,  # White
    ]

    @classmethod
    def _neogeo_to_rgb(cls, ng: int) -> Tuple[int, int, int]:
        """Convert Neo Geo color to RGB"""
        # Dark bit adds to each channel if set
        dark = (ng >> 15) & 1
        r = ((ng >> 10) & 0x1F)
        g = ((ng >> 5) & 0x1F)
        b = (ng & 0x1F)
        # Scale to 8-bit
        r = (r << 3) | (r >> 2)
        g = (g << 3) | (g >> 2)
        b = (b << 3) | (b >> 2)
        if dark:
            r = min(255, r + 16)
            g = min(255, g + 16)
            b = min(255, b + 16)
        return (r, g, b)

    @classmethod
    def get_palette_rgb(cls, palette_indices: List[int]) -> List[Tuple[int, int, int]]:
        return [cls._neogeo_to_rgb(idx) for idx in palette_indices]

    @classmethod
    def generate_tile_data(cls, indexed_img: Image.Image) -> bytes:
        """Neo Geo sprite format: planar, 16x16 tiles"""
        pixels = list(indexed_img.getdata())
        width, height = indexed_img.size

        # Neo Geo uses planar format with specific bit arrangement
        # Each 16x16 tile is stored as 4 bitplanes
        tile_data = bytearray()

        tiles_x = width // 16
        tiles_y = height // 16

        for ty in range(tiles_y):
            for tx in range(tiles_x):
                # 4 bitplanes, each is 16 rows of 2 bytes (16 bits per row)
                planes = [[0] * 32 for _ in range(4)]

                for row in range(16):
                    for col in range(16):
                        px = tx * 16 + col
                        py = ty * 16 + row
                        if px < width and py < height:
                            color = pixels[py * width + px] & 0x0F
                            byte_idx = row * 2 + (col // 8)
                            bit = 7 - (col % 8)
                            for plane in range(4):
                                if color & (1 << plane):
                                    planes[plane][byte_idx] |= (1 << bit)

                # Output planes interleaved
                for row in range(16):
                    for plane in range(4):
                        tile_data.append(planes[plane][row * 2])
                        tile_data.append(planes[plane][row * 2 + 1])

        return bytes(tile_data)


class MSXConfig(PlatformConfig):
    """MSX / MSX2 - Popular in Japan and Europe, active homebrew"""

    name = "MSX"
    tile_width = 8
    tile_height = 8
    bits_per_pixel = 4          # MSX2 supports 4bpp (16 colors from 512)
    colors_per_palette = 16
    max_sprite_width = 16       # 8x8 or 16x16 sprites
    max_sprite_height = 16
    bytes_per_tile = 32         # 4bpp
    output_extension = ".msx"
    resample_mode = "NEAREST"

    # MSX2 uses 9-bit RGB (3 bits per channel = 512 colors)
    # Format: 0 RRR GGG BBB
    palette_rgb = {i: (
        ((i >> 6) & 0x7) * 36,   # R
        ((i >> 3) & 0x7) * 36,   # G
        (i & 0x7) * 36           # B
    ) for i in range(512)}

    # MSX1 TMS9918 palette (fixed 16 colors) - more commonly used
    TMS9918_PALETTE = {
        0: (0, 0, 0),           # Transparent
        1: (0, 0, 0),           # Black
        2: (33, 200, 66),       # Medium Green
        3: (94, 220, 120),      # Light Green
        4: (84, 85, 237),       # Dark Blue
        5: (125, 118, 252),     # Light Blue
        6: (212, 82, 77),       # Dark Red
        7: (66, 235, 245),      # Cyan
        8: (252, 85, 84),       # Medium Red
        9: (255, 121, 120),     # Light Red
        10: (212, 193, 84),     # Dark Yellow
        11: (230, 206, 128),    # Light Yellow
        12: (33, 176, 59),      # Dark Green
        13: (201, 91, 186),     # Magenta
        14: (204, 204, 204),    # Gray
        15: (255, 255, 255),    # White
    }

    palette_rgb = TMS9918_PALETTE
    default_palette = list(range(16))

    @classmethod
    def get_palette_rgb(cls, palette_indices: List[int]) -> List[Tuple[int, int, int]]:
        return [cls.palette_rgb.get(idx & 0x0F, (0, 0, 0)) for idx in palette_indices]

    @classmethod
    def generate_tile_data(cls, indexed_img: Image.Image) -> bytes:
        """MSX sprite format: similar to SMS, 1bpp with color per line"""
        pixels = list(indexed_img.getdata())
        width, height = indexed_img.size

        # MSX sprites are 1bpp with color attribute
        # For simplicity, output as pattern data (1bpp)
        tile_data = bytearray()
        tiles_x = width // 8
        tiles_y = height // 8

        for ty in range(tiles_y):
            for tx in range(tiles_x):
                for row in range(8):
                    byte_val = 0
                    for col in range(8):
                        px = tx * 8 + col
                        py = ty * 8 + row
                        if px < width and py < height:
                            if pixels[py * width + px] > 0:
                                byte_val |= (0x80 >> col)
                    tile_data.append(byte_val)

        return bytes(tile_data)


class AtariLynxConfig(PlatformConfig):
    """Atari Lynx - Color handheld, 16 colors from 4096, active homebrew"""

    name = "Lynx"
    tile_width = 8
    tile_height = 8
    bits_per_pixel = 4
    colors_per_palette = 16     # 16 colors from 4096 (12-bit RGB)
    max_sprite_width = 512      # No fixed limit, memory dependent
    max_sprite_height = 512
    bytes_per_tile = 32         # 4bpp
    output_extension = ".lnx"
    resample_mode = "LANCZOS"

    # Lynx uses 12-bit RGB (4 bits per channel = 4096 colors)
    # Format: GGGG BBBB RRRR (unusual order!)
    palette_rgb = {}

    default_palette = [
        0x000,  # Black
        0xF0F,  # Magenta (G=15, B=0, R=15)
        0x0FF,  # Cyan (G=0, B=15, R=15... wait, need to check order)
        0xFFF,  # White
        0x444,  # Dark grey
        0x888,  # Medium grey
        0xCCC,  # Light grey
        0x00F,  # Red
        0x0F0,  # Green
        0xF00,  # Blue
        0x0FF,  # Yellow
        0xF0F,  # Magenta
        0xFF0,  # Cyan
        0x666,  # Grey
        0xAAA,  # Light grey
        0xFFF,  # White
    ]

    @classmethod
    def _lynx_to_rgb(cls, lynx: int) -> Tuple[int, int, int]:
        """Convert Lynx 12-bit color (GGGGBBBBRRRR) to RGB"""
        g = ((lynx >> 8) & 0xF) * 17
        b = ((lynx >> 4) & 0xF) * 17
        r = (lynx & 0xF) * 17
        return (r, g, b)

    @classmethod
    def get_palette_rgb(cls, palette_indices: List[int]) -> List[Tuple[int, int, int]]:
        return [cls._lynx_to_rgb(idx) for idx in palette_indices]

    @classmethod
    def generate_tile_data(cls, indexed_img: Image.Image) -> bytes:
        """Lynx sprite format: packed 4bpp, run-length encoded in hardware"""
        # For raw output, just do packed 4bpp (2 pixels per byte)
        pixels = list(indexed_img.getdata())
        width, height = indexed_img.size

        tile_data = bytearray()
        for y in range(height):
            for x in range(0, width, 2):
                c1 = pixels[y * width + x] & 0x0F if x < width else 0
                c2 = pixels[y * width + x + 1] & 0x0F if x + 1 < width else 0
                tile_data.append((c1 << 4) | c2)

        return bytes(tile_data)


# Platform registry
PLATFORMS: Dict[str, type] = {
    # Nintendo
    'nes': NESConfig,
    'famicom': NESConfig,
    'gb': GameBoyConfig,
    'gameboy': GameBoyConfig,
    'dmg': GameBoyConfig,
    'gbc': GameBoyColorConfig,
    'gameboycolor': GameBoyColorConfig,
    'cgb': GameBoyColorConfig,
    'snes': SNESConfig,
    'superfamicom': SNESConfig,
    'sfc': SNESConfig,
    # Sega
    'genesis': GenesisConfig,
    'megadrive': GenesisConfig,
    'md': GenesisConfig,
    'sms': MasterSystemConfig,
    'mastersystem': MasterSystemConfig,
    'gamegear': MasterSystemConfig,  # Same tile format, different palette
    'gg': MasterSystemConfig,
    # NEC
    'pce': PCEngineConfig,
    'pcengine': PCEngineConfig,
    'turbografx': PCEngineConfig,
    'tg16': PCEngineConfig,
    # Commodore
    'amiga': AmigaConfig,
    'amigaocs': AmigaConfig,
    'amigaecs': AmigaConfig,
    'amigaaga': AmigaAGAConfig,
    'aga': AmigaAGAConfig,
    'a1200': AmigaAGAConfig,
    'a4000': AmigaAGAConfig,
    'c64': C64Config,
    'commodore64': C64Config,
    'vic20': C64Config,
    # Atari
    'atari2600': Atari2600Config,
    'vcs': Atari2600Config,
    '2600': Atari2600Config,
    'lynx': AtariLynxConfig,
    'atarilynx': AtariLynxConfig,
    # PC
    'cga': CGAConfig,
    'ibmpc': CGAConfig,
    # Nintendo (additional)
    'gba': GBAConfig,
    'gameboyadvance': GBAConfig,
    'advance': GBAConfig,
    # SNK
    'neogeo': NeoGeoConfig,
    'neo': NeoGeoConfig,
    'mvs': NeoGeoConfig,
    'aes': NeoGeoConfig,
    # MSX
    'msx': MSXConfig,
    'msx1': MSXConfig,
    'msx2': MSXConfig,
}

def get_platform(name: str) -> PlatformConfig:
    """Get platform config by name"""
    key = name.lower().replace('-', '').replace(' ', '')
    if key not in PLATFORMS:
        available = ', '.join(sorted(set(PLATFORMS.values().__class__.__name__ for v in PLATFORMS.values())))
        raise ValueError(f"Unknown platform: {name}. Available: {list(set(p.name for p in PLATFORMS.values()))}")
    return PLATFORMS[key]

# Legacy compatibility
NES_PALETTE_RGB = NESConfig.palette_rgb
SYNTHWAVE_PALETTE = NESConfig.default_palette

ASSET_CATEGORIES = {
    'player': {'prefixes': ['player_'], 'size': 32},
    'enemies': {'prefixes': ['enemies_', 'enemy_'], 'size': 32},
    'boss': {'prefixes': ['boss_'], 'size': 64},
    'items': {'prefixes': ['items_', 'item_', 'projectile_'], 'size': 16},
    'background': {'prefixes': ['background_', 'bg_'], 'size': 128},
    'ui': {'prefixes': ['ui_', 'hud_', 'font_'], 'size': 8},
    'vfx': {'prefixes': ['vfx_', 'fx_', 'effect_'], 'size': 16},
    'title': {'prefixes': ['title_', 'logo_'], 'size': 64},
}

# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class BoundingBox:
    x: int
    y: int
    width: int
    height: int

    def crop_box(self) -> Tuple[int, int, int, int]:
        return (self.x, self.y, self.x + self.width, self.y + self.height)

    def to_dict(self) -> Dict[str, int]:
        """Return dictionary representation for JSON serialization."""
        return {"x": self.x, "y": self.y, "w": self.width, "h": self.height}

    @classmethod
    def from_dict(cls, d: Dict[str, int]) -> 'BoundingBox':
        """Create BoundingBox from dictionary (supports both 'width'/'w' keys)."""
        return cls(
            x=d.get('x', 0),
            y=d.get('y', 0),
            width=d.get('width', d.get('w', 0)),
            height=d.get('height', d.get('h', 0))
        )


@dataclass
class CollisionMask:
    """
    Collision data for a sprite, supporting both AABB boxes and per-pixel masks.

    For Genesis/SGDK integration, this generates:
    - AABB: SpriteCollision struct with hitbox/hurtbox offsets
    - Pixel: 1-bit mask array for complex shapes (bosses, irregular sprites)

    Attributes:
        hitbox: Damage-dealing collision box (weapon, projectile core)
        hurtbox: Damage-receiving collision box (body, vulnerable area)
        pixel_mask: Optional 1-bit per-pixel mask for precise collision
        mask_type: "aabb" (default) or "pixel" for complex sprites
        confidence: AI confidence score (0.0-1.0) for the analysis
        reasoning: AI explanation of hitbox/hurtbox placement
    """
    hitbox: BoundingBox
    hurtbox: BoundingBox
    pixel_mask: Optional[bytes] = None
    mask_type: str = "aabb"
    confidence: float = 0.0
    reasoning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Return dictionary representation for JSON serialization."""
        result = {
            "hitbox": self.hitbox.to_dict(),
            "hurtbox": self.hurtbox.to_dict(),
            "mask_type": self.mask_type,
            "confidence": self.confidence,
            "reasoning": self.reasoning
        }
        if self.pixel_mask:
            import base64
            result["pixel_mask"] = base64.b64encode(self.pixel_mask).decode('ascii')
        return result

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'CollisionMask':
        """Create CollisionMask from dictionary."""
        pixel_mask = None
        if d.get('pixel_mask'):
            import base64
            pixel_mask = base64.b64decode(d['pixel_mask'])
        return cls(
            hitbox=BoundingBox.from_dict(d.get('hitbox', {})),
            hurtbox=BoundingBox.from_dict(d.get('hurtbox', {})),
            pixel_mask=pixel_mask,
            mask_type=d.get('mask_type', 'aabb'),
            confidence=d.get('confidence', 0.0),
            reasoning=d.get('reasoning', '')
        )


@dataclass
class SpriteInfo:
    id: int
    bbox: BoundingBox
    sprite_type: str = "sprite"
    action: str = "idle"
    frame_index: int = 0
    description: str = ""
    collision: Optional[CollisionMask] = None

    def to_dict(self) -> Dict[str, Any]:
        """Return dictionary representation for JSON serialization."""
        result = {
            "id": self.id,
            "bbox": self.bbox.to_dict(),
            "sprite_type": self.sprite_type,
            "action": self.action,
            "frame_index": self.frame_index,
            "description": self.description
        }
        if self.collision:
            result["collision"] = self.collision.to_dict()
        return result

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'SpriteInfo':
        """Create SpriteInfo from dictionary."""
        collision = None
        if d.get('collision'):
            collision = CollisionMask.from_dict(d['collision'])
        return cls(
            id=d.get('id', 0),
            bbox=BoundingBox.from_dict(d.get('bbox', {})),
            sprite_type=d.get('sprite_type', 'sprite'),
            action=d.get('action', 'idle'),
            frame_index=d.get('frame_index', 0),
            description=d.get('description', ''),
            collision=collision
        )


# =============================================================================
# END OF FILE
# =============================================================================




