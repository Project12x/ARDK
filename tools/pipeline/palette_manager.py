"""
Palette Management System for Retro Game Development.

This module provides centralized palette management for games targeting
hardware with strict palette limitations (Genesis, NES, SNES, GameBoy).
It ensures color consistency across all assets and helps artists stay
within hardware constraints during development.

Key Problems Solved:
    - Genesis has only 4 palettes × 16 colors = 64 total colors
    - All sprites sharing a palette must use compatible colors
    - AI-generated art often violates palette constraints
    - Manual color checking is tedious and error-prone

Key Components:
    - PaletteManager: Central manager for game-wide palette definitions
    - PaletteSlot: A single palette with semantic meaning (e.g., "player", "enemies")
    - ValidationResult: Detailed results from sprite validation
    - PaletteUsageStats: Track which assets use which palettes

Main Features:
    1. Define palette slots with semantic categories (player, enemy, UI, etc.)
    2. Validate sprites against allowed palette colors
    3. Auto-remap colors to nearest palette entries
    4. Generate AI prompt constraints for palette-limited generation
    5. Export palettes as SGDK-compatible C headers

Usage:
    >>> from pipeline.palette_manager import PaletteManager, create_genesis_game_palettes
    >>>
    >>> # Quick start with default palettes
    >>> manager = create_genesis_game_palettes()
    >>>
    >>> # Validate a sprite uses correct colors
    >>> result = manager.validate_sprite(sprite_image, allowed_slots=[0])
    >>> if not result.valid:
    ...     fixed = manager.remap_to_palette(sprite_image, target_slot=0)
    >>>
    >>> # Get AI generation constraints
    >>> prompt = manager.get_ai_prompt_constraint(slot=0)
    >>> # "Use ONLY these exact colors: #FFFFFF, #E0B090, ..."
    >>>
    >>> # Export for SGDK
    >>> manager.export_c_header("palettes.h")

Genesis Palette Layout:
    PAL0 (hardware index 0): Player, NPCs, shared sprites
    PAL1 (hardware index 1): Enemies, hazards
    PAL2 (hardware index 2): Background plane A (main tileset)
    PAL3 (hardware index 3): Background plane B, UI, effects

    Note: Color 0 in each palette is transparent/backdrop color.

Platform Support:
    - genesis: 4 palettes × 16 colors (64 total)
    - nes: 4 palettes × 4 colors (16 total per sprite/BG)
    - snes: 8 palettes × 16 colors (256 total)
    - gameboy: 1 palette × 4 colors (grayscale)

Phase Implementation:
    - Phase 2.1.x: Core palette management system
"""

import json
import os
import math
from typing import List, Tuple, Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from pathlib import Path

# Import from sibling modules
try:
    from .palette_converter import (
        PaletteConverter, PaletteFormat, rgb_to_lab, color_distance_lab
    )
except ImportError:
    # Fallback for standalone testing
    PaletteConverter = None
    PaletteFormat = None

    def rgb_to_lab(r: int, g: int, b: int) -> Tuple[float, float, float]:
        """Convert RGB to CIE LAB for perceptual color comparison."""
        # Normalize RGB to 0-1
        r, g, b = r / 255.0, g / 255.0, b / 255.0

        # sRGB to linear
        def linearize(c):
            return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

        r, g, b = linearize(r), linearize(g), linearize(b)

        # Linear RGB to XYZ
        x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375
        y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
        z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041

        # XYZ to LAB (D65 illuminant)
        xn, yn, zn = 0.95047, 1.0, 1.08883
        x, y, z = x / xn, y / yn, z / zn

        def f(t):
            return t ** (1/3) if t > 0.008856 else (7.787 * t) + (16 / 116)

        L = (116 * f(y)) - 16
        a = 500 * (f(x) - f(y))
        b_val = 200 * (f(y) - f(z))

        return (L, a, b_val)

    def color_distance_lab(lab1: Tuple[float, float, float],
                           lab2: Tuple[float, float, float]) -> float:
        """Calculate perceptual color distance (Delta E)."""
        return math.sqrt(
            (lab1[0] - lab2[0]) ** 2 +
            (lab1[1] - lab2[1]) ** 2 +
            (lab1[2] - lab2[2]) ** 2
        )


class PalettePurpose(Enum):
    """
    Semantic categories for palette slots.

    Assigning a purpose to each palette slot helps organize assets
    and ensures related sprites share compatible colors. This also
    enables validation rules (e.g., "player sprites must use PAL0").
    """
    PLAYER = "player"           # Player character sprites
    NPC = "npc"                 # Friendly NPCs (often shares with PLAYER)
    ENEMY = "enemy"             # Enemies, bosses, hazards
    BACKGROUND_A = "bg_a"       # Background plane A (main tileset)
    BACKGROUND_B = "bg_b"       # Background plane B (parallax)
    UI = "ui"                   # HUD, menus, dialog boxes
    EFFECTS = "effects"         # Particles, explosions, magic
    SHARED = "shared"           # Multi-purpose (default)


@dataclass
class PaletteSlot:
    """
    A single hardware palette slot with color definitions and metadata.

    Each slot holds a fixed number of colors determined by the platform:
    - Genesis: 16 colors per slot (index 0 is transparent)
    - NES: 4 colors per slot
    - SNES: 16 colors per slot
    - GameBoy: 4 grayscale levels

    The slot includes cached CIE LAB color values for fast perceptual
    color matching, allowing efficient nearest-color lookups without
    repeated RGB-to-LAB conversions.

    Attributes:
        index: Hardware palette index (0-3 for Genesis, determines CRAM offset).
        name: Human-readable identifier (e.g., "player_npc", "enemies").
        colors: List of RGB tuples. Index 0 is typically transparent.
        purpose: Semantic category for organizing assets.
        locked: If True, prevents auto-optimization tools from modifying colors.
        description: Usage notes for artists (stored in exports).

    Example:
        >>> slot = PaletteSlot(
        ...     index=0, name="player",
        ...     colors=[(0,0,0), (255,255,255), (200,150,100), ...],
        ...     purpose=PalettePurpose.PLAYER
        ... )
        >>> idx, dist = slot.find_nearest_color((210, 160, 110))
    """
    index: int
    name: str
    colors: List[Tuple[int, int, int]]
    purpose: PalettePurpose = PalettePurpose.SHARED
    locked: bool = False
    description: str = ""

    # Pre-computed LAB values for O(1) perceptual color matching
    _lab_cache: List[Tuple[float, float, float]] = field(default_factory=list, repr=False)

    def __post_init__(self):
        """Build LAB cache for color matching."""
        self._rebuild_lab_cache()

    def _rebuild_lab_cache(self):
        """Rebuild LAB color cache after color changes."""
        self._lab_cache = [rgb_to_lab(*c) for c in self.colors]

    @property
    def max_colors(self) -> int:
        """Maximum colors in this slot."""
        return len(self.colors)

    @property
    def used_colors(self) -> int:
        """Number of non-transparent colors actually used."""
        # Count colors that aren't the transparent color (index 0)
        if not self.colors:
            return 0
        transparent = self.colors[0]
        return sum(1 for c in self.colors[1:] if c != transparent)

    def find_nearest_color(self, rgb: Tuple[int, int, int],
                           skip_transparent: bool = True) -> Tuple[int, float]:
        """
        Find the nearest color in this palette.

        Args:
            rgb: RGB color to match
            skip_transparent: If True, don't match to color 0

        Returns:
            Tuple of (palette_index, distance)
        """
        target_lab = rgb_to_lab(*rgb)
        best_idx = 0
        best_dist = float('inf')

        start_idx = 1 if skip_transparent else 0

        for i in range(start_idx, len(self._lab_cache)):
            dist = color_distance_lab(target_lab, self._lab_cache[i])
            if dist < best_dist:
                best_dist = dist
                best_idx = i

        return best_idx, best_dist

    def contains_color(self, rgb: Tuple[int, int, int],
                       tolerance: float = 0.0) -> bool:
        """
        Check if this palette contains a color (exact or within tolerance).

        Args:
            rgb: RGB color to check
            tolerance: Maximum Delta E distance for a match (0 = exact)

        Returns:
            True if color is in palette
        """
        if tolerance == 0:
            return rgb in self.colors

        _, dist = self.find_nearest_color(rgb)
        return dist <= tolerance

    def get_hex_colors(self) -> List[str]:
        """Get colors as hex strings for display/export."""
        return [f"#{r:02X}{g:02X}{b:02X}" for r, g, b in self.colors]

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            'index': self.index,
            'name': self.name,
            'purpose': self.purpose.value,
            'colors': self.colors,
            'locked': self.locked,
            'description': self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'PaletteSlot':
        """Deserialize from dictionary."""
        return cls(
            index=data['index'],
            name=data['name'],
            colors=[tuple(c) for c in data['colors']],
            purpose=PalettePurpose(data.get('purpose', 'shared')),
            locked=data.get('locked', False),
            description=data.get('description', ''),
        )


@dataclass
class ValidationResult:
    """Result of validating a sprite against palette constraints."""
    valid: bool
    sprite_path: str = ""
    allowed_slots: List[int] = field(default_factory=list)
    colors_found: List[Tuple[int, int, int]] = field(default_factory=list)
    invalid_colors: List[Tuple[int, int, int]] = field(default_factory=list)
    suggested_slot: Optional[int] = None
    remap_suggestions: Dict[Tuple[int, int, int], Tuple[int, int, int]] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        if self.valid:
            return f"✓ Valid: {len(self.colors_found)} colors within allowed palettes"
        else:
            return (
                f"✗ Invalid: {len(self.invalid_colors)} colors not in allowed palettes\n"
                f"  Invalid: {self.invalid_colors[:5]}{'...' if len(self.invalid_colors) > 5 else ''}"
            )


@dataclass
class PaletteUsageStats:
    """Track palette usage across game assets."""
    slot_index: int
    slot_name: str
    assets_using: List[str] = field(default_factory=list)
    colors_used: Set[int] = field(default_factory=set)  # Indices within palette
    color_frequency: Dict[int, int] = field(default_factory=dict)  # color_idx -> count


class PaletteManager:
    """
    Central manager for game-wide palette definitions and validation.

    Handles:
    - Defining palette slots with semantic meaning
    - Validating sprites against palette constraints
    - Remapping colors to nearest palette entries
    - Tracking palette usage across assets
    - Generating AI prompt constraints
    - Exporting palettes to various formats
    """

    # Platform palette limits
    PLATFORM_SPECS = {
        'genesis': {'slots': 4, 'colors_per_slot': 16, 'total': 64},
        'nes': {'slots': 4, 'colors_per_slot': 4, 'total': 16},  # Per sprite
        'snes': {'slots': 8, 'colors_per_slot': 16, 'total': 256},
        'gameboy': {'slots': 1, 'colors_per_slot': 4, 'total': 4},
    }

    def __init__(self, platform: str = 'genesis'):
        """
        Initialize palette manager for a specific platform.

        Args:
            platform: Target platform ('genesis', 'nes', 'snes', 'gameboy')
        """
        self.platform = platform.lower()
        if self.platform not in self.PLATFORM_SPECS:
            raise ValueError(f"Unknown platform: {platform}")

        self.specs = self.PLATFORM_SPECS[self.platform]
        self.slots: Dict[int, PaletteSlot] = {}
        self.usage_stats: Dict[int, PaletteUsageStats] = {}

        # Color tolerance for matching (Delta E)
        self.match_tolerance = 5.0  # Slightly lenient for anti-aliased edges

        # Initialize empty slots
        for i in range(self.specs['slots']):
            self._init_empty_slot(i)

    def _init_empty_slot(self, index: int):
        """Initialize an empty palette slot."""
        colors_count = self.specs['colors_per_slot']
        # Start with all black (transparent at 0)
        colors = [(0, 0, 0)] * colors_count
        self.slots[index] = PaletteSlot(
            index=index,
            name=f"palette_{index}",
            colors=colors,
            purpose=PalettePurpose.SHARED,
        )
        self.usage_stats[index] = PaletteUsageStats(
            slot_index=index,
            slot_name=f"palette_{index}",
        )

    def define_slot(
        self,
        index: int,
        name: str,
        colors: List[Tuple[int, int, int]],
        purpose: PalettePurpose = PalettePurpose.SHARED,
        locked: bool = False,
        description: str = "",
    ) -> PaletteSlot:
        """
        Define or update a palette slot.

        Args:
            index: Palette slot index (0-3 for Genesis)
            name: Human-readable name (e.g., "player_npc")
            colors: List of RGB tuples (pad to max if shorter)
            purpose: Semantic category
            locked: Prevent auto-optimization
            description: Usage notes for artists

        Returns:
            The created/updated PaletteSlot

        Example:
            manager.define_slot(0, "player", [
                (0, 0, 0),        # 0: Transparent
                (255, 255, 255),  # 1: White highlight
                (0, 0, 0),        # 2: Black outline
                (220, 180, 140),  # 3: Skin light
                (180, 130, 90),   # 4: Skin mid
                (140, 90, 60),    # 5: Skin shadow
                (80, 50, 30),     # 6: Hair dark
                (120, 80, 50),    # 7: Hair mid
                (60, 100, 180),   # 8: Armor blue
                (40, 70, 140),    # 9: Armor dark
                (100, 140, 220),  # 10: Armor light
                (200, 60, 60),    # 11: Cape red
                (140, 40, 40),    # 12: Cape shadow
                (80, 80, 80),     # 13: Metal gray
                (120, 120, 120),  # 14: Metal light
                (40, 40, 40),     # 15: Metal dark
            ], purpose=PalettePurpose.PLAYER)
        """
        if index < 0 or index >= self.specs['slots']:
            raise ValueError(f"Invalid slot index {index} for {self.platform}")

        max_colors = self.specs['colors_per_slot']

        # Pad or truncate colors list
        if len(colors) < max_colors:
            colors = list(colors) + [(0, 0, 0)] * (max_colors - len(colors))
        elif len(colors) > max_colors:
            colors = colors[:max_colors]
            print(f"Warning: Truncated palette to {max_colors} colors")

        # Ensure all colors are tuples
        colors = [tuple(c) for c in colors]

        slot = PaletteSlot(
            index=index,
            name=name,
            colors=colors,
            purpose=purpose,
            locked=locked,
            description=description,
        )

        self.slots[index] = slot
        self.usage_stats[index] = PaletteUsageStats(
            slot_index=index,
            slot_name=name,
        )

        return slot

    def get_slot(self, index: int) -> Optional[PaletteSlot]:
        """Get a palette slot by index."""
        return self.slots.get(index)

    def get_slot_by_name(self, name: str) -> Optional[PaletteSlot]:
        """Get a palette slot by name."""
        for slot in self.slots.values():
            if slot.name == name:
                return slot
        return None

    def get_slots_by_purpose(self, purpose: PalettePurpose) -> List[PaletteSlot]:
        """Get all slots with a specific purpose."""
        return [s for s in self.slots.values() if s.purpose == purpose]

    def validate_sprite(
        self,
        image,  # PIL.Image.Image
        allowed_slots: List[int] = None,
        sprite_path: str = "",
        tolerance: float = None,
    ) -> ValidationResult:
        """
        Validate that a sprite only uses colors from allowed palettes.

        Args:
            image: PIL Image to validate
            allowed_slots: List of allowed palette slot indices (None = all)
            sprite_path: Path for reporting
            tolerance: Color matching tolerance (None = use default)

        Returns:
            ValidationResult with details
        """
        if allowed_slots is None:
            allowed_slots = list(self.slots.keys())

        if tolerance is None:
            tolerance = self.match_tolerance

        # Build combined allowed colors from all allowed slots
        allowed_colors = set()
        for idx in allowed_slots:
            if idx in self.slots:
                allowed_colors.update(self.slots[idx].colors)

        # Get unique colors from image
        if image.mode == 'P':
            # Indexed image
            palette_data = image.getpalette()
            if palette_data:
                used_indices = set(image.getdata())
                image_colors = set()
                for idx in used_indices:
                    r = palette_data[idx * 3]
                    g = palette_data[idx * 3 + 1]
                    b = palette_data[idx * 3 + 2]
                    image_colors.add((r, g, b))
            else:
                image_colors = set()
        elif image.mode == 'RGBA':
            # Get non-transparent pixels
            image_colors = set()
            for pixel in image.getdata():
                if pixel[3] > 0:  # Not fully transparent
                    image_colors.add((pixel[0], pixel[1], pixel[2]))
        elif image.mode == 'RGB':
            image_colors = set(image.getdata())
        else:
            # Convert to RGB
            rgb_image = image.convert('RGB')
            image_colors = set(rgb_image.getdata())

        # Check each color
        invalid_colors = []
        remap_suggestions = {}

        for color in image_colors:
            if color in allowed_colors:
                continue

            # Check with tolerance
            found_match = False
            best_match = None
            best_dist = float('inf')

            for idx in allowed_slots:
                if idx not in self.slots:
                    continue
                slot = self.slots[idx]
                match_idx, dist = slot.find_nearest_color(color)
                if dist <= tolerance:
                    found_match = True
                    break
                if dist < best_dist:
                    best_dist = dist
                    best_match = slot.colors[match_idx]

            if not found_match:
                invalid_colors.append(color)
                if best_match:
                    remap_suggestions[color] = best_match

        # Suggest best slot if validation failed
        suggested_slot = None
        if invalid_colors:
            # Find slot with most matching colors
            best_slot = None
            best_matches = 0
            for idx in allowed_slots:
                if idx not in self.slots:
                    continue
                slot = self.slots[idx]
                matches = sum(1 for c in image_colors if slot.contains_color(c, tolerance))
                if matches > best_matches:
                    best_matches = matches
                    best_slot = idx
            suggested_slot = best_slot

        return ValidationResult(
            valid=len(invalid_colors) == 0,
            sprite_path=sprite_path,
            allowed_slots=allowed_slots,
            colors_found=list(image_colors),
            invalid_colors=invalid_colors,
            suggested_slot=suggested_slot,
            remap_suggestions=remap_suggestions,
        )

    def remap_to_palette(
        self,
        image,  # PIL.Image.Image
        target_slot: int,
        preserve_transparency: bool = True,
    ):
        """
        Remap all colors in an image to the nearest palette colors.

        Args:
            image: PIL Image to remap
            target_slot: Palette slot to use
            preserve_transparency: Keep fully transparent pixels as-is

        Returns:
            New PIL Image with remapped colors (mode='P' indexed)
        """
        try:
            from PIL import Image
        except ImportError:
            raise ImportError("PIL required: pip install pillow")

        if target_slot not in self.slots:
            raise ValueError(f"Invalid slot index: {target_slot}")

        slot = self.slots[target_slot]

        # Convert to RGBA for processing
        if image.mode != 'RGBA':
            image = image.convert('RGBA')

        width, height = image.size
        pixels = list(image.getdata())

        # Create indexed image
        indexed_pixels = []

        for pixel in pixels:
            r, g, b, a = pixel

            # Handle transparency
            if preserve_transparency and a < 128:
                indexed_pixels.append(0)  # Transparent index
                continue

            # Find nearest color in palette
            color = (r, g, b)
            match_idx, _ = slot.find_nearest_color(color, skip_transparent=True)
            indexed_pixels.append(match_idx)

        # Create new indexed image
        result = Image.new('P', (width, height))

        # Build palette data (R, G, B for each entry)
        palette_data = []
        for color in slot.colors:
            palette_data.extend(color)
        # Pad to 256 colors (required by PIL)
        while len(palette_data) < 768:
            palette_data.extend([0, 0, 0])

        result.putpalette(palette_data)
        result.putdata(indexed_pixels)

        return result

    def track_asset_usage(
        self,
        image,  # PIL.Image.Image
        asset_path: str,
        slot_index: int,
    ):
        """
        Track which colors an asset uses from a palette.

        Args:
            image: PIL Image
            asset_path: Path to asset for tracking
            slot_index: Palette slot the asset uses
        """
        if slot_index not in self.usage_stats:
            return

        stats = self.usage_stats[slot_index]
        slot = self.slots[slot_index]

        # Add asset to list
        if asset_path not in stats.assets_using:
            stats.assets_using.append(asset_path)

        # Get colors from image
        if image.mode == 'P':
            used_indices = set(image.getdata())
            for idx in used_indices:
                if idx < len(slot.colors):
                    stats.colors_used.add(idx)
                    stats.color_frequency[idx] = stats.color_frequency.get(idx, 0) + 1
        else:
            # For RGB/RGBA, find which palette indices are used
            if image.mode != 'RGBA':
                image = image.convert('RGBA')

            for pixel in image.getdata():
                if pixel[3] < 128:  # Transparent
                    continue
                color = (pixel[0], pixel[1], pixel[2])
                match_idx, dist = slot.find_nearest_color(color)
                if dist < self.match_tolerance:
                    stats.colors_used.add(match_idx)
                    stats.color_frequency[match_idx] = stats.color_frequency.get(match_idx, 0) + 1

    def get_ai_prompt_constraint(
        self,
        slot: int,
        format: str = "natural",
        include_hex: bool = True,
    ) -> str:
        """
        Generate AI prompt constraints for a palette.

        Args:
            slot: Palette slot index
            format: "natural" (prose), "list" (bullet points), or "json"
            include_hex: Include hex color codes

        Returns:
            String to append to AI art generation prompts
        """
        if slot not in self.slots:
            return ""

        palette = self.slots[slot]
        colors = palette.colors[1:]  # Skip transparent

        if format == "json":
            return json.dumps({
                'palette_name': palette.name,
                'colors': [
                    {'rgb': c, 'hex': f"#{c[0]:02X}{c[1]:02X}{c[2]:02X}"}
                    for c in colors if c != (0, 0, 0)
                ]
            })

        # Build color descriptions
        color_strs = []
        for c in colors:
            if c == (0, 0, 0):
                continue
            if include_hex:
                color_strs.append(f"#{c[0]:02X}{c[1]:02X}{c[2]:02X}")
            else:
                # Try to describe the color
                color_strs.append(self._describe_color(c))

        if format == "list":
            return (
                f"STRICT PALETTE CONSTRAINT - Only use these {len(color_strs)} colors:\n"
                + "\n".join(f"- {c}" for c in color_strs)
            )

        # Natural format
        return (
            f"Use ONLY these exact colors (no gradients, no anti-aliasing to other colors): "
            f"{', '.join(color_strs)}. "
            f"This is a {self.specs['colors_per_slot']}-color palette constraint. "
            f"Every pixel must match one of these colors exactly."
        )

    def _describe_color(self, rgb: Tuple[int, int, int]) -> str:
        """Generate a simple color description."""
        r, g, b = rgb

        # Brightness
        brightness = (r + g + b) / 3 / 255

        if brightness < 0.2:
            lightness = "dark"
        elif brightness > 0.8:
            lightness = "light"
        else:
            lightness = ""

        # Dominant channel
        if max(r, g, b) - min(r, g, b) < 30:
            # Grayscale
            return f"{lightness} gray" if lightness else "gray"

        if r >= g and r >= b:
            if g > b:
                hue = "orange" if g > r * 0.5 else "red"
            else:
                hue = "pink" if b > r * 0.5 else "red"
        elif g >= r and g >= b:
            if b > r:
                hue = "cyan" if b > g * 0.5 else "green"
            else:
                hue = "yellow" if r > g * 0.5 else "green"
        else:
            if r > g:
                hue = "purple" if r > b * 0.5 else "blue"
            else:
                hue = "cyan" if g > b * 0.5 else "blue"

        return f"{lightness} {hue}".strip()

    def export_palette_image(
        self,
        slot: int,
        output_path: str,
        cell_size: int = 32,
        show_indices: bool = True,
    ) -> str:
        """
        Export a palette slot as a visual PNG.

        Args:
            slot: Palette slot index
            output_path: Output file path
            cell_size: Size of each color cell
            show_indices: Draw index numbers on cells

        Returns:
            Path to generated image
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            raise ImportError("PIL required: pip install pillow")

        if slot not in self.slots:
            raise ValueError(f"Invalid slot: {slot}")

        palette = self.slots[slot]
        num_colors = len(palette.colors)

        # Arrange in 4x4 grid for Genesis (16 colors)
        cols = 4 if num_colors >= 4 else num_colors
        rows = (num_colors + cols - 1) // cols

        width = cols * cell_size
        height = rows * cell_size

        img = Image.new('RGB', (width, height), (128, 128, 128))
        draw = ImageDraw.Draw(img)

        for i, color in enumerate(palette.colors):
            row = i // cols
            col = i % cols
            x = col * cell_size
            y = row * cell_size

            # Draw color cell
            draw.rectangle(
                [x, y, x + cell_size - 1, y + cell_size - 1],
                fill=color,
                outline=(255, 255, 255) if i == 0 else None
            )

            # Draw index
            if show_indices:
                # Choose contrasting text color
                brightness = sum(color) / 3
                text_color = (0, 0, 0) if brightness > 128 else (255, 255, 255)
                draw.text(
                    (x + 2, y + 2),
                    str(i),
                    fill=text_color,
                )

        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        img.save(output_path)
        return output_path

    def export_c_header(
        self,
        output_path: str,
        include_all_slots: bool = True,
        slots: List[int] = None,
    ) -> str:
        """
        Export palettes as SGDK-compatible C header.

        Args:
            output_path: Output .h file path
            include_all_slots: Include all defined slots
            slots: Specific slots to include (if not all)

        Returns:
            Generated header content
        """
        if slots is None:
            slots = list(self.slots.keys()) if include_all_slots else []

        lines = [
            "// Auto-generated palette definitions",
            f"// Platform: {self.platform.upper()}",
            f"// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "// Generator: ARDK Pipeline (palette_manager.py)",
            "",
            "#ifndef _GAME_PALETTES_H_",
            "#define _GAME_PALETTES_H_",
            "",
            "#include <genesis.h>",
            "",
        ]

        for idx in sorted(slots):
            if idx not in self.slots:
                continue

            slot = self.slots[idx]
            c_name = slot.name.upper().replace(' ', '_')

            lines.append(f"// Palette {idx}: {slot.name}")
            if slot.description:
                lines.append(f"// {slot.description}")
            lines.append(f"// Purpose: {slot.purpose.value}")
            lines.append(f"#define PAL_{c_name}_INDEX {idx}")
            lines.append("")

            # Genesis CRAM format: 0000BBB0GGG0RRR0
            lines.append(f"const u16 pal_{slot.name.lower()}[16] = {{")
            color_strs = []
            for i, (r, g, b) in enumerate(slot.colors):
                # Convert to Genesis 9-bit BGR
                gr = (r >> 5) & 0x7  # 3 bits
                gg = (g >> 5) & 0x7
                gb = (b >> 5) & 0x7
                cram = (gb << 9) | (gg << 5) | (gr << 1)
                color_strs.append(f"    0x{cram:04X},  // {i}: #{r:02X}{g:02X}{b:02X}")

            lines.extend(color_strs)
            lines.append("};")
            lines.append("")

        lines.extend([
            "// Load all game palettes",
            "static inline void loadGamePalettes(void) {",
        ])

        for idx in sorted(slots):
            if idx not in self.slots:
                continue
            slot = self.slots[idx]
            lines.append(f"    PAL_setPalette(PAL{idx}, pal_{slot.name.lower()});")

        lines.extend([
            "}",
            "",
            "#endif // _GAME_PALETTES_H_",
        ])

        content = "\n".join(lines)

        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return content

    def save(self, path: str):
        """Save palette definitions to JSON file."""
        data = {
            'version': '1.0',
            'platform': self.platform,
            'match_tolerance': self.match_tolerance,
            'slots': {str(k): v.to_dict() for k, v in self.slots.items()},
        }

        output_dir = os.path.dirname(path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def load(self, path: str):
        """Load palette definitions from JSON file."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.platform = data.get('platform', self.platform)
        self.match_tolerance = data.get('match_tolerance', 5.0)

        if self.platform in self.PLATFORM_SPECS:
            self.specs = self.PLATFORM_SPECS[self.platform]

        for key, slot_data in data.get('slots', {}).items():
            idx = int(key)
            self.slots[idx] = PaletteSlot.from_dict(slot_data)
            self.usage_stats[idx] = PaletteUsageStats(
                slot_index=idx,
                slot_name=slot_data['name'],
            )

    def get_usage_report(self) -> str:
        """Generate a usage report for all palettes."""
        lines = [
            f"Palette Usage Report - {self.platform.upper()}",
            "=" * 50,
            "",
        ]

        for idx in sorted(self.slots.keys()):
            slot = self.slots[idx]
            stats = self.usage_stats.get(idx)

            lines.append(f"PAL{idx}: {slot.name} ({slot.purpose.value})")
            lines.append(f"  Colors defined: {len(slot.colors)}")
            lines.append(f"  Colors used: {len(stats.colors_used) if stats else 0}")
            lines.append(f"  Assets using: {len(stats.assets_using) if stats else 0}")

            if stats and stats.assets_using:
                for asset in stats.assets_using[:5]:
                    lines.append(f"    - {asset}")
                if len(stats.assets_using) > 5:
                    lines.append(f"    ... and {len(stats.assets_using) - 5} more")

            lines.append("")

        return "\n".join(lines)


# =============================================================================
# Convenience Functions
# =============================================================================

def create_genesis_game_palettes() -> PaletteManager:
    """
    Create a PaletteManager with typical Genesis game palette layout.

    Returns a manager with 4 slots pre-configured for common use cases.
    """
    manager = PaletteManager('genesis')

    # PAL0: Player / NPCs (shared sprite palette)
    manager.define_slot(0, "player_npc", [
        (0, 0, 0),        # 0: Transparent
        (255, 255, 255),  # 1: White (shared highlight)
        (0, 0, 0),        # 2: Black outline
        (224, 176, 144),  # 3: Skin light
        (176, 128, 96),   # 4: Skin mid
        (128, 80, 48),    # 5: Skin shadow
        (96, 64, 32),     # 6: Hair/leather dark
        (144, 96, 64),    # 7: Hair/leather mid
        (64, 96, 176),    # 8: Cloth blue
        (48, 64, 128),    # 9: Cloth blue dark
        (96, 144, 208),   # 10: Cloth blue light
        (208, 64, 64),    # 11: Accent red
        (144, 32, 32),    # 12: Accent red dark
        (96, 96, 96),     # 13: Metal mid
        (144, 144, 144),  # 14: Metal light
        (48, 48, 48),     # 15: Metal dark
    ], purpose=PalettePurpose.PLAYER, description="Player character and friendly NPCs")

    # PAL1: Enemies
    manager.define_slot(1, "enemies", [
        (0, 0, 0),        # 0: Transparent
        (255, 255, 255),  # 1: White highlight
        (0, 0, 0),        # 2: Black outline
        (128, 224, 128),  # 3: Slime green light
        (64, 176, 64),    # 4: Slime green mid
        (32, 128, 32),    # 5: Slime green dark
        (224, 128, 64),   # 6: Demon orange
        (176, 80, 32),    # 7: Demon orange dark
        (80, 32, 128),    # 8: Undead purple
        (48, 16, 80),     # 9: Undead purple dark
        (176, 176, 208),  # 10: Ghost white
        (208, 208, 64),   # 11: Energy yellow
        (160, 160, 32),   # 12: Energy yellow dark
        (96, 96, 96),     # 13: Stone gray
        (144, 144, 144),  # 14: Stone gray light
        (48, 48, 48),     # 15: Stone gray dark
    ], purpose=PalettePurpose.ENEMY, description="Enemies and hazards")

    # PAL2: Background A (main tileset)
    manager.define_slot(2, "background_a", [
        (0, 0, 0),        # 0: Transparent / BG color
        (32, 48, 64),     # 1: Sky dark
        (64, 96, 128),    # 2: Sky mid
        (96, 144, 192),   # 3: Sky light
        (64, 48, 32),     # 4: Ground dark
        (112, 80, 48),    # 5: Ground mid
        (160, 128, 80),   # 6: Ground light
        (32, 80, 32),     # 7: Grass dark
        (64, 128, 64),    # 8: Grass mid
        (96, 176, 96),    # 9: Grass light
        (80, 64, 48),     # 10: Wood dark
        (128, 96, 64),    # 11: Wood mid
        (176, 144, 112),  # 12: Wood light
        (64, 64, 80),     # 13: Stone dark
        (96, 96, 112),    # 14: Stone mid
        (144, 144, 160),  # 15: Stone light
    ], purpose=PalettePurpose.BACKGROUND_A, description="Main background tileset")

    # PAL3: UI and effects
    manager.define_slot(3, "ui_effects", [
        (0, 0, 0),        # 0: Transparent
        (255, 255, 255),  # 1: Text white
        (0, 0, 0),        # 2: Text shadow
        (224, 224, 64),   # 3: Gold/coins
        (176, 144, 32),   # 4: Gold dark
        (255, 64, 64),    # 5: Health red
        (176, 32, 32),    # 6: Health red dark
        (64, 64, 255),    # 7: Mana blue
        (32, 32, 176),    # 8: Mana blue dark
        (64, 224, 64),    # 9: Heal green
        (255, 128, 0),    # 10: Fire orange
        (128, 64, 0),     # 11: Fire orange dark
        (0, 192, 255),    # 12: Ice cyan
        (0, 128, 176),    # 13: Ice cyan dark
        (255, 255, 128),  # 14: Lightning yellow
        (80, 80, 80),     # 15: UI frame gray
    ], purpose=PalettePurpose.UI, description="HUD, menus, particle effects")

    return manager


# =============================================================================
# Test / Demo
# =============================================================================

if __name__ == "__main__":
    print("=== Palette Manager Test ===\n")

    # Create with default Genesis palettes
    manager = create_genesis_game_palettes()

    # Print slot info
    for idx, slot in manager.slots.items():
        print(f"PAL{idx}: {slot.name} ({slot.purpose.value})")
        print(f"  Colors: {slot.get_hex_colors()[:4]}...")
        print()

    # Test AI prompt generation
    print("AI Prompt Constraint (natural):")
    print(manager.get_ai_prompt_constraint(0, format="natural"))
    print()

    print("AI Prompt Constraint (list):")
    print(manager.get_ai_prompt_constraint(0, format="list"))
    print()

    # Save and reload test
    manager.save("test_palettes.json")
    print("Saved to test_palettes.json")

    manager2 = PaletteManager('genesis')
    manager2.load("test_palettes.json")
    print("Loaded from test_palettes.json")
    print(f"Slot 0 name: {manager2.get_slot(0).name}")

    # Clean up
    os.remove("test_palettes.json")

    print("\nTest complete!")
