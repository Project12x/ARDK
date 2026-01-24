"""
Cross-Platform Palette Converter (Phase 2.0.4)

Converts palettes between platform-specific formats while preserving visual intent.
Supports Genesis (9-bit BGR), SNES (15-bit BGR), NES (fixed 64-color), and standard RGB.

Usage:
    from pipeline.palette_converter import PaletteConverter, PaletteFormat

    converter = PaletteConverter()

    # Convert RGB colors to Genesis format
    genesis_pal = converter.convert(rgb_colors, PaletteFormat.RGB_24BIT, PaletteFormat.GENESIS_9BIT)

    # Export as Genesis CRAM data
    cram_bytes = converter.export_genesis_cram(genesis_pal)

    # Generate C header
    header = converter.export_c_header(genesis_pal, "player", PaletteFormat.GENESIS_9BIT)
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
from datetime import datetime
import math


# =============================================================================
# PALETTE FORMAT DEFINITIONS
# =============================================================================

class PaletteFormat(Enum):
    """Supported palette formats for retro platforms."""
    GENESIS_9BIT = "genesis"    # 3-3-3 BGR (512 colors total)
    NES_6BIT = "nes"            # Fixed 64-color palette (2-2-2 emphasis)
    SNES_15BIT = "snes"         # 5-5-5 BGR (32768 colors)
    GAMEBOY_2BIT = "gameboy"    # 4 shades of green/gray
    RGB_24BIT = "rgb"           # Standard 8-8-8 RGB


@dataclass
class PaletteInfo:
    """Information about a converted palette."""
    format: PaletteFormat
    colors: List[Tuple[int, int, int]]  # RGB tuples
    raw_values: List[int]               # Platform-specific values
    color_count: int

    @property
    def bytes_per_color(self) -> int:
        """Bytes per color entry for this format."""
        return {
            PaletteFormat.GENESIS_9BIT: 2,
            PaletteFormat.NES_6BIT: 1,
            PaletteFormat.SNES_15BIT: 2,
            PaletteFormat.GAMEBOY_2BIT: 1,
            PaletteFormat.RGB_24BIT: 3,
        }.get(self.format, 2)


# =============================================================================
# NES PALETTE (Fixed 64 colors)
# =============================================================================

# NES PPU palette - 64 fixed colors (values are approximate RGB)
# Based on the 2C02 PPU color output
NES_PALETTE = [
    # Row 0 (0x00-0x0F)
    (84, 84, 84),    # 0x00 - Dark gray
    (0, 30, 116),    # 0x01 - Dark blue
    (8, 16, 144),    # 0x02 - Blue-violet
    (48, 0, 136),    # 0x03 - Violet
    (68, 0, 100),    # 0x04 - Purple
    (92, 0, 48),     # 0x05 - Dark magenta
    (84, 4, 0),      # 0x06 - Dark red
    (60, 24, 0),     # 0x07 - Brown
    (32, 42, 0),     # 0x08 - Olive
    (8, 58, 0),      # 0x09 - Dark green
    (0, 64, 0),      # 0x0A - Green
    (0, 60, 0),      # 0x0B - Dark cyan-green
    (0, 50, 60),     # 0x0C - Dark cyan
    (0, 0, 0),       # 0x0D - Black
    (0, 0, 0),       # 0x0E - Black (mirror)
    (0, 0, 0),       # 0x0F - Black (mirror)

    # Row 1 (0x10-0x1F)
    (152, 150, 152), # 0x10 - Light gray
    (8, 76, 196),    # 0x11 - Medium blue
    (48, 50, 236),   # 0x12 - Blue
    (92, 30, 228),   # 0x13 - Blue-violet
    (136, 20, 176),  # 0x14 - Violet
    (160, 20, 100),  # 0x15 - Magenta
    (152, 34, 32),   # 0x16 - Red
    (120, 60, 0),    # 0x17 - Orange
    (84, 90, 0),     # 0x18 - Yellow-green
    (40, 114, 0),    # 0x19 - Green
    (8, 124, 0),     # 0x1A - Green
    (0, 118, 40),    # 0x1B - Cyan-green
    (0, 102, 120),   # 0x1C - Cyan
    (0, 0, 0),       # 0x1D - Black
    (0, 0, 0),       # 0x1E - Black (mirror)
    (0, 0, 0),       # 0x1F - Black (mirror)

    # Row 2 (0x20-0x2F)
    (236, 238, 236), # 0x20 - White
    (76, 154, 236),  # 0x21 - Light blue
    (120, 124, 236), # 0x22 - Periwinkle
    (176, 98, 236),  # 0x23 - Light violet
    (228, 84, 236),  # 0x24 - Pink-violet
    (236, 88, 180),  # 0x25 - Pink
    (236, 106, 100), # 0x26 - Light red
    (212, 136, 32),  # 0x27 - Orange
    (160, 170, 0),   # 0x28 - Yellow
    (116, 196, 0),   # 0x29 - Yellow-green
    (76, 208, 32),   # 0x2A - Light green
    (56, 204, 108),  # 0x2B - Cyan-green
    (56, 180, 204),  # 0x2C - Light cyan
    (60, 60, 60),    # 0x2D - Dark gray
    (0, 0, 0),       # 0x2E - Black (mirror)
    (0, 0, 0),       # 0x2F - Black (mirror)

    # Row 3 (0x30-0x3F)
    (236, 238, 236), # 0x30 - White
    (168, 204, 236), # 0x31 - Pale blue
    (188, 188, 236), # 0x32 - Pale periwinkle
    (212, 178, 236), # 0x33 - Pale violet
    (236, 174, 236), # 0x34 - Pale pink
    (236, 174, 212), # 0x35 - Pale magenta
    (236, 180, 176), # 0x36 - Pale red
    (228, 196, 144), # 0x37 - Pale orange
    (204, 210, 120), # 0x38 - Pale yellow
    (180, 222, 120), # 0x39 - Pale yellow-green
    (168, 226, 144), # 0x3A - Pale green
    (152, 226, 180), # 0x3B - Pale cyan-green
    (160, 214, 228), # 0x3C - Pale cyan
    (160, 162, 160), # 0x3D - Medium gray
    (0, 0, 0),       # 0x3E - Black (mirror)
    (0, 0, 0),       # 0x3F - Black (mirror)
]


# =============================================================================
# GAMEBOY PALETTE (4 shades)
# =============================================================================

# Classic GameBoy green shades (DMG)
GAMEBOY_PALETTE_GREEN = [
    (155, 188, 15),   # Lightest (white)
    (139, 172, 15),   # Light
    (48, 98, 48),     # Dark
    (15, 56, 15),     # Darkest (black)
]

# GameBoy grayscale (for emulators/GBP)
GAMEBOY_PALETTE_GRAY = [
    (255, 255, 255),  # White
    (170, 170, 170),  # Light gray
    (85, 85, 85),     # Dark gray
    (0, 0, 0),        # Black
]


# =============================================================================
# COLOR SPACE CONVERSION UTILITIES
# =============================================================================

def rgb_to_lab(r: int, g: int, b: int) -> Tuple[float, float, float]:
    """
    Convert RGB to CIE LAB color space for perceptual color distance.

    LAB is device-independent and better represents human color perception.
    """
    # Normalize RGB to 0-1
    r_lin = r / 255.0
    g_lin = g / 255.0
    b_lin = b / 255.0

    # Convert to linear RGB (remove gamma)
    def linearize(c):
        if c > 0.04045:
            return ((c + 0.055) / 1.055) ** 2.4
        return c / 12.92

    r_lin = linearize(r_lin)
    g_lin = linearize(g_lin)
    b_lin = linearize(b_lin)

    # Convert to XYZ (D65 illuminant)
    x = r_lin * 0.4124564 + g_lin * 0.3575761 + b_lin * 0.1804375
    y = r_lin * 0.2126729 + g_lin * 0.7151522 + b_lin * 0.0721750
    z = r_lin * 0.0193339 + g_lin * 0.1191920 + b_lin * 0.9503041

    # Normalize for D65 white point
    x /= 0.95047
    y /= 1.00000
    z /= 1.08883

    # Convert to LAB
    def f(t):
        if t > 0.008856:
            return t ** (1/3)
        return (7.787 * t) + (16/116)

    l = (116 * f(y)) - 16
    a = 500 * (f(x) - f(y))
    b_val = 200 * (f(y) - f(z))

    return (l, a, b_val)


def color_distance_lab(c1: Tuple[int, int, int], c2: Tuple[int, int, int]) -> float:
    """
    Calculate perceptual color distance using CIE LAB Delta E.

    Lower values = more similar colors.
    """
    lab1 = rgb_to_lab(*c1)
    lab2 = rgb_to_lab(*c2)

    dl = lab1[0] - lab2[0]
    da = lab1[1] - lab2[1]
    db = lab1[2] - lab2[2]

    return math.sqrt(dl*dl + da*da + db*db)


def color_distance_rgb(c1: Tuple[int, int, int], c2: Tuple[int, int, int]) -> float:
    """Simple Euclidean distance in RGB space (faster but less accurate)."""
    dr = c1[0] - c2[0]
    dg = c1[1] - c2[1]
    db = c1[2] - c2[2]
    return math.sqrt(dr*dr + dg*dg + db*db)


# =============================================================================
# PALETTE CONVERTER CLASS
# =============================================================================

class PaletteConverter:
    """
    Cross-platform palette converter.

    Converts between RGB, Genesis 9-bit, SNES 15-bit, NES fixed palette,
    and GameBoy 2-bit formats.
    """

    def __init__(self, use_perceptual: bool = True):
        """
        Initialize converter.

        Args:
            use_perceptual: Use LAB color space for matching (slower but better)
        """
        self.use_perceptual = use_perceptual
        self._distance_func = color_distance_lab if use_perceptual else color_distance_rgb

    # =========================================================================
    # MAIN CONVERSION API
    # =========================================================================

    def convert(self, colors: List[Tuple[int, int, int]],
                source: PaletteFormat,
                target: PaletteFormat) -> List[Tuple[int, int, int]]:
        """
        Convert palette between formats.

        Args:
            colors: List of RGB tuples (0-255 per channel)
            source: Source format (for documentation, assumed RGB internally)
            target: Target format

        Returns:
            List of RGB tuples converted to target format's color space
        """
        if target == PaletteFormat.RGB_24BIT:
            return colors  # No conversion needed

        if target == PaletteFormat.GENESIS_9BIT:
            return [self._rgb_to_genesis(c) for c in colors]

        if target == PaletteFormat.SNES_15BIT:
            return [self._rgb_to_snes(c) for c in colors]

        if target == PaletteFormat.NES_6BIT:
            return [self._rgb_to_nes(c) for c in colors]

        if target == PaletteFormat.GAMEBOY_2BIT:
            return [self._rgb_to_gameboy(c) for c in colors]

        raise ValueError(f"Unsupported target format: {target}")

    def convert_to_raw(self, colors: List[Tuple[int, int, int]],
                       target: PaletteFormat) -> List[int]:
        """
        Convert RGB colors to raw platform-specific values.

        Args:
            colors: List of RGB tuples
            target: Target format

        Returns:
            List of platform-specific integer values
        """
        if target == PaletteFormat.GENESIS_9BIT:
            return [self._rgb_to_genesis_raw(c) for c in colors]

        if target == PaletteFormat.SNES_15BIT:
            return [self._rgb_to_snes_raw(c) for c in colors]

        if target == PaletteFormat.NES_6BIT:
            return [self._find_nearest_nes(c) for c in colors]

        if target == PaletteFormat.GAMEBOY_2BIT:
            return [self._rgb_to_gameboy_index(c) for c in colors]

        if target == PaletteFormat.RGB_24BIT:
            return [(c[0] << 16) | (c[1] << 8) | c[2] for c in colors]

        raise ValueError(f"Unsupported target format: {target}")

    # =========================================================================
    # GENESIS (9-bit BGR)
    # =========================================================================

    def _rgb_to_genesis(self, rgb: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """
        Convert RGB to Genesis color space (quantized to 3-3-3).

        Genesis uses 9-bit BGR: 3 bits per channel (8 levels: 0, 36, 73, 109, 146, 182, 219, 255)
        """
        r = (rgb[0] >> 5) * 36  # Quantize to 3 bits, expand back
        g = (rgb[1] >> 5) * 36
        b = (rgb[2] >> 5) * 36

        # Clamp to valid range
        r = min(255, r)
        g = min(255, g)
        b = min(255, b)

        return (r, g, b)

    def _rgb_to_genesis_raw(self, rgb: Tuple[int, int, int]) -> int:
        """
        Convert RGB to Genesis CRAM format (16-bit word).

        Format: 0000BBB0GGG0RRR0
        - Bits 1-3: Red (0-7)
        - Bits 5-7: Green (0-7)
        - Bits 9-11: Blue (0-7)
        """
        r = (rgb[0] >> 5) & 0x07  # 3 bits
        g = (rgb[1] >> 5) & 0x07
        b = (rgb[2] >> 5) & 0x07

        return (r << 1) | (g << 5) | (b << 9)

    def genesis_raw_to_rgb(self, cram_value: int) -> Tuple[int, int, int]:
        """Convert Genesis CRAM value back to RGB."""
        r = ((cram_value >> 1) & 0x07) * 36
        g = ((cram_value >> 5) & 0x07) * 36
        b = ((cram_value >> 9) & 0x07) * 36
        return (min(255, r), min(255, g), min(255, b))

    # =========================================================================
    # SNES (15-bit BGR)
    # =========================================================================

    def _rgb_to_snes(self, rgb: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """
        Convert RGB to SNES color space (quantized to 5-5-5).

        SNES uses 15-bit BGR: 5 bits per channel (32 levels)
        """
        r = (rgb[0] >> 3) * 8  # Quantize to 5 bits, expand back
        g = (rgb[1] >> 3) * 8
        b = (rgb[2] >> 3) * 8

        return (min(255, r), min(255, g), min(255, b))

    def _rgb_to_snes_raw(self, rgb: Tuple[int, int, int]) -> int:
        """
        Convert RGB to SNES CGRAM format (16-bit word).

        Format: 0BBBBBGGGGGRRRRR
        - Bits 0-4: Red (0-31)
        - Bits 5-9: Green (0-31)
        - Bits 10-14: Blue (0-31)
        """
        r = (rgb[0] >> 3) & 0x1F  # 5 bits
        g = (rgb[1] >> 3) & 0x1F
        b = (rgb[2] >> 3) & 0x1F

        return r | (g << 5) | (b << 10)

    def snes_raw_to_rgb(self, cgram_value: int) -> Tuple[int, int, int]:
        """Convert SNES CGRAM value back to RGB."""
        r = (cgram_value & 0x1F) * 8
        g = ((cgram_value >> 5) & 0x1F) * 8
        b = ((cgram_value >> 10) & 0x1F) * 8
        return (min(255, r), min(255, g), min(255, b))

    # =========================================================================
    # NES (Fixed 64-color palette)
    # =========================================================================

    def _rgb_to_nes(self, rgb: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """Find nearest NES palette color and return its RGB value."""
        idx = self._find_nearest_nes(rgb)
        return NES_PALETTE[idx]

    def _find_nearest_nes(self, rgb: Tuple[int, int, int]) -> int:
        """
        Find nearest NES palette entry for an RGB color.

        Uses perceptual color distance (LAB) if enabled.

        Returns:
            NES palette index (0-63)
        """
        best_idx = 0
        best_dist = float('inf')

        for idx, nes_color in enumerate(NES_PALETTE):
            dist = self._distance_func(rgb, nes_color)
            if dist < best_dist:
                best_dist = dist
                best_idx = idx

        return best_idx

    def find_nearest_nes(self, rgb: Tuple[int, int, int]) -> int:
        """Public API for finding nearest NES palette index."""
        return self._find_nearest_nes(rgb)

    # =========================================================================
    # GAMEBOY (4 shades)
    # =========================================================================

    def _rgb_to_gameboy(self, rgb: Tuple[int, int, int],
                        use_green: bool = False) -> Tuple[int, int, int]:
        """
        Convert RGB to nearest GameBoy shade.

        Args:
            rgb: Input RGB color
            use_green: Use classic green palette (True) or grayscale (False)
        """
        idx = self._rgb_to_gameboy_index(rgb)
        palette = GAMEBOY_PALETTE_GREEN if use_green else GAMEBOY_PALETTE_GRAY
        return palette[idx]

    def _rgb_to_gameboy_index(self, rgb: Tuple[int, int, int]) -> int:
        """
        Convert RGB to GameBoy shade index (0-3).

        Uses luminance to determine shade.
        """
        # Calculate perceived luminance (ITU-R BT.601)
        luma = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]

        # Map to 4 levels
        if luma >= 192:
            return 0  # Lightest
        elif luma >= 128:
            return 1  # Light
        elif luma >= 64:
            return 2  # Dark
        else:
            return 3  # Darkest

    # =========================================================================
    # EXPORT FUNCTIONS
    # =========================================================================

    def export_genesis_cram(self, colors: List[Tuple[int, int, int]],
                            pad_to: int = 16) -> bytes:
        """
        Export palette as Genesis CRAM data (binary).

        Args:
            colors: List of RGB tuples
            pad_to: Pad to this many colors (default 16 for one palette)

        Returns:
            Binary data for CRAM (2 bytes per color, big-endian)
        """
        result = bytearray()

        for i in range(pad_to):
            if i < len(colors):
                raw = self._rgb_to_genesis_raw(colors[i])
            else:
                raw = 0  # Transparent/black padding

            # Genesis is big-endian
            result.append((raw >> 8) & 0xFF)
            result.append(raw & 0xFF)

        return bytes(result)

    def export_snes_cgram(self, colors: List[Tuple[int, int, int]],
                          pad_to: int = 16) -> bytes:
        """
        Export palette as SNES CGRAM data (binary).

        Args:
            colors: List of RGB tuples
            pad_to: Pad to this many colors (default 16)

        Returns:
            Binary data for CGRAM (2 bytes per color, little-endian)
        """
        result = bytearray()

        for i in range(pad_to):
            if i < len(colors):
                raw = self._rgb_to_snes_raw(colors[i])
            else:
                raw = 0  # Black padding

            # SNES is little-endian
            result.append(raw & 0xFF)
            result.append((raw >> 8) & 0xFF)

        return bytes(result)

    def export_nes_palette(self, colors: List[Tuple[int, int, int]],
                           pad_to: int = 4) -> bytes:
        """
        Export palette as NES palette indices.

        Args:
            colors: List of RGB tuples
            pad_to: Pad to this many colors (default 4 for one attribute set)

        Returns:
            Binary data (1 byte per color, NES palette index)
        """
        result = bytearray()

        for i in range(pad_to):
            if i < len(colors):
                idx = self._find_nearest_nes(colors[i])
            else:
                idx = 0x0F  # Black padding

            result.append(idx)

        return bytes(result)

    def export_c_header(self, colors: List[Tuple[int, int, int]],
                        name: str, target: PaletteFormat,
                        pad_to: Optional[int] = None) -> str:
        """
        Generate C header with palette data.

        Args:
            colors: List of RGB tuples
            name: Palette name (used for C identifiers)
            target: Target format
            pad_to: Pad to this many colors (auto if None)

        Returns:
            C header file content as string
        """
        # Sanitize name for C identifier
        c_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in name)
        c_name_upper = c_name.upper()

        # Determine padding
        if pad_to is None:
            if target in (PaletteFormat.GENESIS_9BIT, PaletteFormat.SNES_15BIT):
                pad_to = 16
            elif target == PaletteFormat.NES_6BIT:
                pad_to = 4
            elif target == PaletteFormat.GAMEBOY_2BIT:
                pad_to = 4
            else:
                pad_to = len(colors)

        # Get raw values
        raw_values = self.convert_to_raw(colors, target)

        # Pad if needed
        while len(raw_values) < pad_to:
            raw_values.append(0)

        # Generate header content
        lines = [
            f"// Auto-generated palette data",
            f"// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"// Source: palette_converter.py",
            f"// Format: {target.value}",
            f"// Colors: {len(colors)} (padded to {pad_to})",
            f"",
            f"#ifndef _PAL_{c_name_upper}_H_",
            f"#define _PAL_{c_name_upper}_H_",
            f"",
        ]

        # Add platform-specific include
        if target == PaletteFormat.GENESIS_9BIT:
            lines.append(f"#include <genesis.h>")
        elif target == PaletteFormat.SNES_15BIT:
            lines.append(f"// SNES/libsfc compatible")
        lines.append("")

        # Generate constant array
        lines.append(f"#define PAL_{c_name_upper}_COUNT {pad_to}")
        lines.append("")

        if target == PaletteFormat.GENESIS_9BIT:
            lines.append(f"// Genesis CRAM format: 0000BBB0GGG0RRR0")
            lines.append(f"const u16 pal_{c_name}[PAL_{c_name_upper}_COUNT] = {{")
            for i, val in enumerate(raw_values):
                rgb = colors[i] if i < len(colors) else (0, 0, 0)
                comment = f"// #{i:02d}: RGB({rgb[0]:3}, {rgb[1]:3}, {rgb[2]:3})"
                if i < len(raw_values) - 1:
                    lines.append(f"    0x{val:04X}, {comment}")
                else:
                    lines.append(f"    0x{val:04X}  {comment}")
            lines.append(f"}};")

        elif target == PaletteFormat.SNES_15BIT:
            lines.append(f"// SNES CGRAM format: 0BBBBBGGGGGRRRRR")
            lines.append(f"const unsigned short pal_{c_name}[PAL_{c_name_upper}_COUNT] = {{")
            for i, val in enumerate(raw_values):
                rgb = colors[i] if i < len(colors) else (0, 0, 0)
                comment = f"// #{i:02d}: RGB({rgb[0]:3}, {rgb[1]:3}, {rgb[2]:3})"
                if i < len(raw_values) - 1:
                    lines.append(f"    0x{val:04X}, {comment}")
                else:
                    lines.append(f"    0x{val:04X}  {comment}")
            lines.append(f"}};")

        elif target == PaletteFormat.NES_6BIT:
            lines.append(f"// NES palette indices (0x00-0x3F)")
            lines.append(f"const unsigned char pal_{c_name}[PAL_{c_name_upper}_COUNT] = {{")
            for i, val in enumerate(raw_values):
                nes_rgb = NES_PALETTE[val] if val < len(NES_PALETTE) else (0, 0, 0)
                comment = f"// #{i:02d}: NES ${val:02X} = RGB({nes_rgb[0]:3}, {nes_rgb[1]:3}, {nes_rgb[2]:3})"
                if i < len(raw_values) - 1:
                    lines.append(f"    0x{val:02X}, {comment}")
                else:
                    lines.append(f"    0x{val:02X}  {comment}")
            lines.append(f"}};")

        elif target == PaletteFormat.GAMEBOY_2BIT:
            lines.append(f"// GameBoy palette indices (0-3, lightest to darkest)")
            lines.append(f"const unsigned char pal_{c_name}[PAL_{c_name_upper}_COUNT] = {{")
            for i, val in enumerate(raw_values):
                shade = ["white", "light", "dark", "black"][val] if val < 4 else "?"
                comment = f"// #{i:02d}: {shade}"
                if i < len(raw_values) - 1:
                    lines.append(f"    {val}, {comment}")
                else:
                    lines.append(f"    {val}  {comment}")
            lines.append(f"}};")

        lines.append("")
        lines.append(f"#endif // _PAL_{c_name_upper}_H_")
        lines.append("")

        return "\n".join(lines)

    # =========================================================================
    # IMAGE PALETTE EXTRACTION
    # =========================================================================

    def extract_from_image(self, img, max_colors: int = 16) -> List[Tuple[int, int, int]]:
        """
        Extract palette from a PIL Image.

        Args:
            img: PIL Image object
            max_colors: Maximum colors to extract

        Returns:
            List of RGB tuples
        """
        # Convert to RGB if needed
        if img.mode == 'P':
            # Indexed image - extract from palette
            palette = img.getpalette()
            if palette:
                colors = []
                for i in range(min(max_colors, 256)):
                    r = palette[i * 3]
                    g = palette[i * 3 + 1]
                    b = palette[i * 3 + 2]
                    colors.append((r, g, b))
                return colors

        # For other modes, quantize
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Quantize to get palette
        quantized = img.quantize(colors=max_colors)
        palette = quantized.getpalette()

        colors = []
        for i in range(max_colors):
            r = palette[i * 3]
            g = palette[i * 3 + 1]
            b = palette[i * 3 + 2]
            colors.append((r, g, b))

        return colors


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def convert_palette(colors: List[Tuple[int, int, int]],
                    target: PaletteFormat) -> List[Tuple[int, int, int]]:
    """
    Quick palette conversion.

    Args:
        colors: List of RGB tuples
        target: Target format

    Returns:
        Converted colors
    """
    converter = PaletteConverter()
    return converter.convert(colors, PaletteFormat.RGB_24BIT, target)


def export_genesis_palette(colors: List[Tuple[int, int, int]],
                           output_path: str,
                           name: str = "palette") -> bool:
    """
    Export colors as Genesis CRAM binary and C header.

    Args:
        colors: List of RGB tuples
        output_path: Base path (will add .bin and .h extensions)
        name: Palette name for C identifiers

    Returns:
        True if successful
    """
    import os

    converter = PaletteConverter()

    # Export binary
    bin_path = output_path if output_path.endswith('.bin') else f"{output_path}.bin"
    cram_data = converter.export_genesis_cram(colors)

    os.makedirs(os.path.dirname(bin_path) or '.', exist_ok=True)

    try:
        with open(bin_path, 'wb') as f:
            f.write(cram_data)
        print(f"      [EXPORT] Genesis palette: {bin_path}")
    except Exception as e:
        print(f"      [ERROR] Failed to write palette: {e}")
        return False

    # Export header
    header_path = bin_path.replace('.bin', '.h')
    header_content = converter.export_c_header(colors, name, PaletteFormat.GENESIS_9BIT)

    try:
        with open(header_path, 'w') as f:
            f.write(header_content)
        print(f"      [EXPORT] Palette header: {header_path}")
    except Exception as e:
        print(f"      [WARN] Failed to write header: {e}")

    return True


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Enums
    'PaletteFormat',
    # Classes
    'PaletteConverter',
    'PaletteInfo',
    # Constants
    'NES_PALETTE',
    'GAMEBOY_PALETTE_GREEN',
    'GAMEBOY_PALETTE_GRAY',
    # Functions
    'convert_palette',
    'export_genesis_palette',
    'rgb_to_lab',
    'color_distance_lab',
    'color_distance_rgb',
]
