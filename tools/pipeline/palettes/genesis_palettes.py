"""
Genesis/Mega Drive color palettes.

The Genesis uses 9-bit color (3 bits per channel = 512 possible colors).
Each palette has 16 colors, with index 0 being transparent (magenta).

The actual Genesis VDP color values are:
    0x0EEE = White (E=14 per channel, scaled to 255)
    0x0000 = Black

Color channel formula:
    VDP value (0-14) -> RGB (0-255): value * 255 / 14
    RGB (0-255) -> VDP (0-14): round(value * 14 / 255)

Valid Genesis RGB levels: 0, 36, 72, 109, 145, 182, 218, 255
(These are the 8 levels that map cleanly to 3-bit values)

Usage:
    from pipeline.palettes.genesis_palettes import (
        get_genesis_palette,
        snap_to_genesis_color,
        extract_palette,
    )

    # Get predefined palette
    palette = get_genesis_palette("player_warm")

    # Snap arbitrary color to nearest Genesis color
    snapped = snap_to_genesis_color(200, 150, 100)

    # Extract palette from image
    from PIL import Image
    img = Image.open("sprite.png")
    palette = extract_palette(img)
"""

from typing import List, Tuple, Optional
from collections import Counter

# Magenta transparency (must be index 0 for SGDK)
TRANSPARENT = (255, 0, 255)

# Valid Genesis color levels (3-bit = 8 levels per channel)
# These map to VDP values 0, 2, 4, 6, 8, 10, 12, 14
GENESIS_LEVELS = [0, 36, 72, 109, 145, 182, 218, 255]


# =============================================================================
# PREDEFINED PALETTES
# =============================================================================

GENESIS_PALETTES = {
    # Warm palette for player characters
    "player_warm": [
        TRANSPARENT,           # 0: Transparent
        (0, 0, 0),             # 1: Black (outline)
        (255, 255, 255),       # 2: White (highlight)
        (255, 218, 182),       # 3: Skin light
        (218, 182, 145),       # 4: Skin mid
        (182, 109, 72),        # 5: Skin dark
        (218, 72, 72),         # 6: Red (primary)
        (182, 36, 36),         # 7: Red dark
        (255, 182, 72),        # 8: Gold accent
        (182, 145, 36),        # 9: Gold dark
        (72, 72, 182),         # 10: Blue accent
        (36, 36, 145),         # 11: Blue dark
        (145, 145, 145),       # 12: Gray mid
        (72, 72, 72),          # 13: Gray dark
        (182, 182, 182),       # 14: Gray light
        (255, 145, 72),        # 15: Orange highlight
    ],

    # Cool palette for enemies/monsters
    "enemy_cool": [
        TRANSPARENT,
        (0, 0, 0),
        (255, 255, 255),
        (72, 182, 72),         # Green (goblin skin)
        (36, 145, 36),
        (0, 72, 0),
        (182, 72, 182),        # Purple (magic)
        (145, 36, 145),
        (72, 72, 218),         # Blue (ice)
        (36, 36, 145),
        (218, 218, 72),        # Yellow (warning)
        (182, 182, 36),
        (145, 145, 145),
        (72, 72, 72),
        (182, 182, 182),
        (255, 72, 72),         # Red (damage)
    ],

    # Environment/tileset palette
    "environment": [
        TRANSPARENT,
        (0, 0, 0),
        (255, 255, 255),
        (72, 145, 72),         # Grass light
        (36, 109, 36),         # Grass mid
        (0, 72, 0),            # Grass dark
        (182, 145, 109),       # Dirt light
        (145, 109, 72),        # Dirt mid
        (109, 72, 36),         # Dirt dark
        (145, 145, 182),       # Stone light
        (109, 109, 145),       # Stone mid
        (72, 72, 109),         # Stone dark
        (109, 72, 36),         # Wood
        (72, 145, 182),        # Water
        (36, 109, 145),        # Water dark
        (218, 218, 145),       # Sand
    ],

    # Projectiles and effects
    "effects": [
        TRANSPARENT,
        (0, 0, 0),
        (255, 255, 255),
        (255, 255, 145),       # Bright yellow (muzzle flash)
        (255, 218, 72),
        (255, 182, 0),
        (255, 145, 0),         # Orange (fire)
        (255, 72, 0),
        (255, 0, 0),           # Red (explosion)
        (182, 0, 0),
        (72, 182, 255),        # Cyan (energy)
        (0, 145, 255),
        (182, 72, 255),        # Purple (magic)
        (145, 0, 182),
        (72, 255, 72),         # Green (heal)
        (0, 182, 0),
    ],

    # UI and HUD elements
    "ui": [
        TRANSPARENT,
        (0, 0, 0),
        (255, 255, 255),
        (218, 218, 218),       # Light gray
        (182, 182, 182),
        (145, 145, 145),
        (109, 109, 109),
        (72, 72, 72),
        (255, 72, 72),         # Health red
        (72, 255, 72),         # Health green
        (72, 145, 255),        # Mana blue
        (255, 218, 72),        # XP gold
        (255, 145, 0),         # Warning orange
        (182, 72, 255),        # Special purple
        (36, 36, 36),          # Near black
        (218, 182, 145),       # Parchment
    ],

    # Grayscale (for fade effects, silhouettes)
    "grayscale": [
        TRANSPARENT,
        (0, 0, 0),
        (36, 36, 36),
        (72, 72, 72),
        (109, 109, 109),
        (145, 145, 145),
        (182, 182, 182),
        (218, 218, 218),
        (255, 255, 255),
        (72, 72, 72),
        (109, 109, 109),
        (145, 145, 145),
        (182, 182, 182),
        (218, 218, 218),
        (36, 36, 36),
        (0, 0, 0),
    ],

    # Epoch: Hero (Rad Dude) + Fenrir (Dog) - Shared palette
    # Hero: 90s grunge skater, red flannel, blue jeans, skin, TOY LASER GUN
    # Dog: Scruffy black/brown terrier
    "epoch_hero_dog": [
        TRANSPARENT,               # 0: Transparent (magenta)
        (0, 0, 0),                 # 1: Black (outline)
        (255, 255, 255),           # 2: White (highlight)
        (255, 218, 182),           # 3: Skin light
        (218, 182, 145),           # 4: Skin mid / Brown light (shared)
        (182, 145, 109),           # 5: Skin shadow / Brown mid
        (255, 72, 72),             # 6: Red light (flannel highlight)
        (218, 36, 36),             # 7: Red mid (flannel, cap)
        (145, 36, 36),             # 8: Red dark (flannel shadow)
        (72, 109, 182),            # 9: Blue light (jeans)
        (36, 72, 145),             # 10: Blue dark (jeans shadow)
        (109, 72, 36),             # 11: Brown dark (dog fur)
        (255, 182, 72),            # 12: Orange light (TOY GUN highlight)
        (255, 145, 0),             # 13: Orange mid (TOY GUN body)
        (182, 109, 0),             # 14: Orange dark (TOY GUN shadow)
        (109, 109, 109),           # 15: Gray (t-shirt, details)
    ],
}


# =============================================================================
# PALETTE FUNCTIONS
# =============================================================================

def get_genesis_palette(name: str) -> Optional[List[Tuple[int, int, int]]]:
    """
    Get a predefined Genesis palette by name.

    Args:
        name: Palette name ("player_warm", "enemy_cool", etc.)

    Returns:
        List of 16 RGB tuples, or None if not found
    """
    return GENESIS_PALETTES.get(name)


def list_palettes() -> List[str]:
    """Return list of available palette names."""
    return list(GENESIS_PALETTES.keys())


def snap_to_genesis_color(r: int, g: int, b: int) -> Tuple[int, int, int]:
    """
    Snap RGB values to nearest Genesis-valid color.

    Genesis uses 3 bits per channel, giving 8 possible levels.

    Args:
        r, g, b: RGB values (0-255)

    Returns:
        Tuple of snapped (r, g, b) values
    """
    def snap_channel(v: int) -> int:
        return min(GENESIS_LEVELS, key=lambda x: abs(x - v))

    return (snap_channel(r), snap_channel(g), snap_channel(b))


def rgb_to_genesis_vdp(r: int, g: int, b: int) -> int:
    """
    Convert RGB to Genesis VDP color format.

    VDP format: 0x0BGR (4 bits each, but only 3 bits used = 0-14 even values)

    Args:
        r, g, b: RGB values (0-255)

    Returns:
        16-bit VDP color value
    """
    # Snap to valid levels first
    r, g, b = snap_to_genesis_color(r, g, b)

    # Convert to 3-bit values (0-7)
    vr = GENESIS_LEVELS.index(r) * 2 if r in GENESIS_LEVELS else 0
    vg = GENESIS_LEVELS.index(g) * 2 if g in GENESIS_LEVELS else 0
    vb = GENESIS_LEVELS.index(b) * 2 if b in GENESIS_LEVELS else 0

    return (vb << 8) | (vg << 4) | vr


def genesis_vdp_to_rgb(vdp_color: int) -> Tuple[int, int, int]:
    """
    Convert Genesis VDP color to RGB.

    Args:
        vdp_color: 16-bit VDP color (0x0BGR format)

    Returns:
        Tuple of (r, g, b) values (0-255)
    """
    vr = (vdp_color & 0x00F) // 2
    vg = ((vdp_color >> 4) & 0x00F) // 2
    vb = ((vdp_color >> 8) & 0x00F) // 2

    # Clamp to valid range
    vr = min(7, vr)
    vg = min(7, vg)
    vb = min(7, vb)

    return (GENESIS_LEVELS[vr], GENESIS_LEVELS[vg], GENESIS_LEVELS[vb])


def extract_palette(img, max_colors: int = 16,
                    snap_to_genesis: bool = True) -> List[Tuple[int, int, int]]:
    """
    Extract dominant colors from image.

    Ensures magenta is index 0 for transparency.

    Args:
        img: PIL Image object
        max_colors: Maximum colors to extract (default 16)
        snap_to_genesis: If True, snap colors to valid Genesis values

    Returns:
        List of up to max_colors RGB tuples
    """
    from PIL import Image

    if img.mode != 'RGB':
        img = img.convert('RGB')

    pixels = list(img.getdata())

    # Remove magenta (we'll add it back as index 0)
    non_transparent = [p for p in pixels if p != TRANSPARENT]

    # Count colors
    counter = Counter(non_transparent)

    # Get most common colors
    common = counter.most_common(max_colors - 1)

    # Build palette with magenta first
    palette = [TRANSPARENT]

    for color, _ in common:
        if snap_to_genesis:
            genesis_color = snap_to_genesis_color(*color)
        else:
            genesis_color = color

        if genesis_color not in palette:
            palette.append(genesis_color)

        if len(palette) >= max_colors:
            break

    # Pad with black if needed
    while len(palette) < max_colors:
        palette.append((0, 0, 0))

    return palette


def create_palette_image(palette: List[Tuple[int, int, int]],
                         swatch_size: int = 16) -> 'Image.Image':
    """
    Create a visual representation of a palette.

    Args:
        palette: List of RGB tuples
        swatch_size: Size of each color swatch in pixels

    Returns:
        PIL Image showing the palette
    """
    from PIL import Image, ImageDraw

    # Create 16x1 or 4x4 layout
    cols = 4 if len(palette) > 4 else len(palette)
    rows = (len(palette) + cols - 1) // cols

    width = cols * swatch_size
    height = rows * swatch_size

    img = Image.new('RGB', (width, height), (128, 128, 128))
    draw = ImageDraw.Draw(img)

    for i, color in enumerate(palette):
        col = i % cols
        row = i // cols
        x = col * swatch_size
        y = row * swatch_size

        # Draw swatch
        draw.rectangle(
            [x, y, x + swatch_size - 1, y + swatch_size - 1],
            fill=color,
            outline=(0, 0, 0)
        )

    return img


def validate_palette(palette: List[Tuple[int, int, int]]) -> List[str]:
    """
    Check if a palette is valid for Genesis.

    Args:
        palette: List of RGB tuples

    Returns:
        List of warning messages (empty if valid)
    """
    warnings = []

    if len(palette) > 16:
        warnings.append(f"Palette has {len(palette)} colors, max is 16")

    if len(palette) > 0 and palette[0] != TRANSPARENT:
        warnings.append(
            f"Index 0 should be transparent (magenta), "
            f"found {palette[0]}"
        )

    for i, color in enumerate(palette):
        snapped = snap_to_genesis_color(*color)
        if snapped != color:
            warnings.append(
                f"Color {i} {color} is not Genesis-valid, "
                f"should be {snapped}"
            )

    return warnings


# =============================================================================
# PALETTE EXPORT
# =============================================================================

def export_palette_asm(palette: List[Tuple[int, int, int]],
                       name: str = "palette") -> str:
    """
    Export palette as 68000 assembly for SGDK.

    Args:
        palette: List of RGB tuples
        name: Label name for the palette

    Returns:
        Assembly string
    """
    lines = [
        f"; Genesis palette: {name}",
        f"; {len(palette)} colors",
        f"",
        f"{name}:",
    ]

    for i in range(0, len(palette), 8):
        chunk = palette[i:i+8]
        vdp_values = [rgb_to_genesis_vdp(*c) for c in chunk]
        hex_str = ", ".join(f"${v:04X}" for v in vdp_values)
        lines.append(f"    dc.w {hex_str}")

    return "\n".join(lines)


def export_palette_c(palette: List[Tuple[int, int, int]],
                     name: str = "palette") -> str:
    """
    Export palette as C array for SGDK.

    Args:
        palette: List of RGB tuples
        name: Variable name for the palette

    Returns:
        C code string
    """
    vdp_values = [rgb_to_genesis_vdp(*c) for c in palette]

    lines = [
        f"// Genesis palette: {name}",
        f"// {len(palette)} colors",
        f"const u16 {name}[{len(palette)}] = {{",
    ]

    for i in range(0, len(vdp_values), 8):
        chunk = vdp_values[i:i+8]
        hex_str = ", ".join(f"0x{v:04X}" for v in chunk)
        comma = "," if i + 8 < len(vdp_values) else ""
        lines.append(f"    {hex_str}{comma}")

    lines.append("};")

    return "\n".join(lines)
