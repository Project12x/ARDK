"""
Sprite Effect Variants for Retro Game Development.

Generate common sprite effect variants algorithmically without AI,
perfect for hit flashes, damage states, and visual feedback.

Phase: 1.3 (Core Features)

Key Features:
- White flash (hit confirmation)
- Damage tint (red overlay)
- Invulnerability blink (alternating frames)
- Silhouette (solid color)
- Palette swap
- Outline generation
- Shadow/drop shadow
- Glow effects

Usage:
    from tools.pipeline.effects import (
        SpriteEffects,
        white_flash,
        damage_tint,
        generate_hit_variants,
    )

    # Quick functions
    flashed = white_flash(sprite_image)
    damaged = damage_tint(sprite_image, intensity=0.5)

    # Full effect generator
    effects = SpriteEffects()
    variants = effects.generate_hit_set(sprite_image)
    # Returns: {'normal': img, 'flash': img, 'damage': img, 'silhouette': img}

Performance:
    - All operations are PIL-based (fast, no AI)
    - Typical sprite (32x32): < 1ms per effect
    - Batch of 100 sprites: < 100ms total
"""

from typing import List, Tuple, Dict, Optional, Literal
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFilter
import math


# Type aliases
RGB = Tuple[int, int, int]
RGBA = Tuple[int, int, int, int]
ColorMapping = Dict[RGB, RGB]
EffectType = Literal['flash', 'damage', 'silhouette', 'outline', 'shadow', 'glow', 'blink']


@dataclass
class EffectConfig:
    """Configuration for effect generation."""
    flash_color: RGB = (255, 255, 255)
    damage_color: RGB = (255, 0, 0)
    damage_intensity: float = 0.5
    silhouette_color: RGB = (0, 0, 0)
    outline_color: RGB = (0, 0, 0)
    outline_width: int = 1
    shadow_color: RGBA = (0, 0, 0, 128)
    shadow_offset: Tuple[int, int] = (2, 2)
    glow_color: RGB = (255, 255, 255)
    glow_radius: int = 2
    alpha_threshold: int = 128


@dataclass
class EffectResult:
    """Result of effect generation with metadata."""
    image: Image.Image
    effect_type: str
    config: EffectConfig


class SpriteEffects:
    """
    Generate sprite effect variants using PIL operations.

    All effects preserve transparency and work with RGBA images.
    Results can be used directly for Genesis/NES sprite sheets.

    Example:
        effects = SpriteEffects()

        # Single effect
        flash = effects.white_flash(sprite)

        # Generate full hit set
        variants = effects.generate_hit_set(sprite)

        # Custom configuration
        effects = SpriteEffects(EffectConfig(
            damage_color=(255, 128, 0),  # Orange instead of red
            damage_intensity=0.7
        ))
    """

    def __init__(self, config: Optional[EffectConfig] = None):
        """
        Initialize with optional configuration.

        Args:
            config: Effect configuration, uses defaults if None
        """
        self.config = config or EffectConfig()

    def white_flash(self, img: Image.Image,
                    color: Optional[RGB] = None,
                    threshold: Optional[int] = None) -> Image.Image:
        """
        Replace all non-transparent pixels with a solid color.

        Creates the classic "hit flash" effect used for damage feedback.

        Args:
            img: Source sprite image
            color: Flash color (default: white)
            threshold: Alpha threshold for transparency (default: 128)

        Returns:
            Flashed sprite image
        """
        color = color or self.config.flash_color
        threshold = threshold if threshold is not None else self.config.alpha_threshold

        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        result = img.copy()
        pixels = result.load()

        for y in range(img.height):
            for x in range(img.width):
                r, g, b, a = pixels[x, y]
                if a >= threshold:
                    pixels[x, y] = (*color, a)

        return result

    def damage_tint(self, img: Image.Image,
                    tint: Optional[RGB] = None,
                    intensity: Optional[float] = None) -> Image.Image:
        """
        Overlay a color tint on the sprite.

        Creates damage/hurt state visual feedback.

        Args:
            img: Source sprite image
            tint: Tint color (default: red)
            intensity: Blend intensity 0.0-1.0 (default: 0.5)

        Returns:
            Tinted sprite image
        """
        tint = tint or self.config.damage_color
        intensity = intensity if intensity is not None else self.config.damage_intensity

        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        result = img.copy()
        pixels = result.load()

        for y in range(img.height):
            for x in range(img.width):
                r, g, b, a = pixels[x, y]
                if a > 0:
                    r = int(r * (1 - intensity) + tint[0] * intensity)
                    g = int(g * (1 - intensity) + tint[1] * intensity)
                    b = int(b * (1 - intensity) + tint[2] * intensity)
                    pixels[x, y] = (
                        max(0, min(255, r)),
                        max(0, min(255, g)),
                        max(0, min(255, b)),
                        a
                    )

        return result

    def invulnerability_blink(self, img: Image.Image,
                               bright_intensity: float = 0.3) -> List[Image.Image]:
        """
        Generate 2-frame blink sequence for invulnerability.

        Returns normal frame and brightened frame for alternating display.

        Args:
            img: Source sprite image
            bright_intensity: How much to brighten (0.0-1.0)

        Returns:
            List of [normal, bright] frames
        """
        normal = img.copy() if img.mode == 'RGBA' else img.convert('RGBA')
        bright = self.damage_tint(img, (255, 255, 255), bright_intensity)
        return [normal, bright]

    def silhouette(self, img: Image.Image,
                   color: Optional[RGB] = None,
                   threshold: Optional[int] = None) -> Image.Image:
        """
        Create solid color silhouette of sprite.

        Useful for shadows, death effects, or selection indicators.

        Args:
            img: Source sprite image
            color: Silhouette color (default: black)
            threshold: Alpha threshold (default: 128)

        Returns:
            Silhouette image
        """
        color = color or self.config.silhouette_color
        threshold = threshold if threshold is not None else self.config.alpha_threshold

        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        result = img.copy()
        pixels = result.load()

        for y in range(img.height):
            for x in range(img.width):
                r, g, b, a = pixels[x, y]
                if a >= threshold:
                    pixels[x, y] = (*color, a)

        return result

    def palette_swap(self, img: Image.Image,
                     mapping: ColorMapping) -> Image.Image:
        """
        Swap colors according to mapping dictionary.

        Perfect for team colors, elemental variants, etc.

        Args:
            img: Source sprite image
            mapping: Dict mapping source RGB to target RGB

        Returns:
            Palette-swapped image

        Example:
            # Red team to blue team
            mapping = {
                (255, 0, 0): (0, 0, 255),
                (200, 0, 0): (0, 0, 200),
                (150, 0, 0): (0, 0, 150),
            }
            blue_team = effects.palette_swap(red_sprite, mapping)
        """
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        result = img.copy()
        pixels = result.load()

        for y in range(img.height):
            for x in range(img.width):
                pixel = pixels[x, y][:3]
                if pixel in mapping:
                    r, g, b = mapping[pixel]
                    pixels[x, y] = (r, g, b, pixels[x, y][3])

        return result

    def outline(self, img: Image.Image,
                color: Optional[RGB] = None,
                width: Optional[int] = None,
                threshold: Optional[int] = None) -> Image.Image:
        """
        Add outline around sprite.

        Useful for selection highlighting or making sprites pop.

        Args:
            img: Source sprite image
            color: Outline color (default: black)
            width: Outline width in pixels (default: 1)
            threshold: Alpha threshold (default: 128)

        Returns:
            Image with outline added
        """
        color = color or self.config.outline_color
        width = width if width is not None else self.config.outline_width
        threshold = threshold if threshold is not None else self.config.alpha_threshold

        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # Create expanded canvas for outline
        new_width = img.width + width * 2
        new_height = img.height + width * 2
        result = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))

        # Create outline mask by checking neighbors
        src_pixels = img.load()
        outline_mask = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))
        mask_pixels = outline_mask.load()

        # For each pixel, if it's transparent but has a non-transparent neighbor, color it
        for y in range(new_height):
            for x in range(new_width):
                src_x = x - width
                src_y = y - width

                # Check if this pixel is transparent in source (or out of bounds)
                if 0 <= src_x < img.width and 0 <= src_y < img.height:
                    if src_pixels[src_x, src_y][3] >= threshold:
                        continue  # Skip non-transparent source pixels

                # Check if any neighbor within width is non-transparent
                has_neighbor = False
                for dy in range(-width, width + 1):
                    for dx in range(-width, width + 1):
                        if dx == 0 and dy == 0:
                            continue
                        nx = src_x + dx
                        ny = src_y + dy
                        if 0 <= nx < img.width and 0 <= ny < img.height:
                            if src_pixels[nx, ny][3] >= threshold:
                                # Check distance for circular outline
                                dist = math.sqrt(dx * dx + dy * dy)
                                if dist <= width + 0.5:
                                    has_neighbor = True
                                    break
                    if has_neighbor:
                        break

                if has_neighbor:
                    mask_pixels[x, y] = (*color, 255)

        # Composite: outline first, then sprite on top
        result.paste(outline_mask, (0, 0))
        result.paste(img, (width, width), img)

        return result

    def drop_shadow(self, img: Image.Image,
                    color: Optional[RGBA] = None,
                    offset: Optional[Tuple[int, int]] = None,
                    threshold: Optional[int] = None) -> Image.Image:
        """
        Add drop shadow behind sprite.

        Creates depth effect for UI or floating elements.

        Args:
            img: Source sprite image
            color: Shadow color with alpha (default: semi-transparent black)
            offset: Shadow offset (x, y) pixels (default: (2, 2))
            threshold: Alpha threshold (default: 128)

        Returns:
            Image with shadow added
        """
        color = color or self.config.shadow_color
        offset = offset or self.config.shadow_offset
        threshold = threshold if threshold is not None else self.config.alpha_threshold

        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # Create expanded canvas
        expand_x = abs(offset[0])
        expand_y = abs(offset[1])
        new_width = img.width + expand_x
        new_height = img.height + expand_y

        result = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))

        # Create shadow as silhouette
        shadow = self.silhouette(img, color[:3], threshold)

        # Apply shadow alpha
        shadow_pixels = shadow.load()
        for y in range(shadow.height):
            for x in range(shadow.width):
                r, g, b, a = shadow_pixels[x, y]
                if a > 0:
                    # Blend shadow alpha with original alpha
                    new_alpha = int(a * color[3] / 255)
                    shadow_pixels[x, y] = (r, g, b, new_alpha)

        # Position shadow and sprite
        shadow_x = max(0, offset[0])
        shadow_y = max(0, offset[1])
        sprite_x = max(0, -offset[0])
        sprite_y = max(0, -offset[1])

        result.paste(shadow, (shadow_x, shadow_y), shadow)
        result.paste(img, (sprite_x, sprite_y), img)

        return result

    def glow(self, img: Image.Image,
             color: Optional[RGB] = None,
             radius: Optional[int] = None,
             threshold: Optional[int] = None) -> Image.Image:
        """
        Add glow effect around sprite.

        Perfect for power-ups, magic effects, or selection.

        Args:
            img: Source sprite image
            color: Glow color (default: white)
            radius: Glow radius in pixels (default: 2)
            threshold: Alpha threshold (default: 128)

        Returns:
            Image with glow added
        """
        color = color or self.config.glow_color
        radius = radius if radius is not None else self.config.glow_radius
        threshold = threshold if threshold is not None else self.config.alpha_threshold

        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # Create expanded canvas
        expand = radius * 2
        new_width = img.width + expand
        new_height = img.height + expand
        result = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))

        # Create glow base (silhouette)
        glow_base = self.silhouette(img, color, threshold)

        # Expand glow using multiple passes
        glow_expanded = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))
        glow_expanded.paste(glow_base, (radius, radius), glow_base)

        # Apply blur for soft glow (simulate with multiple outlines at decreasing alpha)
        for r in range(radius, 0, -1):
            alpha = int(255 * (r / radius) * 0.5)  # Fade out
            outline = self.outline(img, color, r, threshold)

            # Adjust alpha
            outline_pixels = outline.load()
            for y in range(outline.height):
                for x in range(outline.width):
                    pixel = outline_pixels[x, y]
                    if pixel[3] > 0 and pixel[:3] == color:
                        outline_pixels[x, y] = (*color, min(pixel[3], alpha))

            # Paste centered
            offset = radius - r + r  # Center in expanded canvas
            glow_expanded.paste(outline, (offset, offset), outline)

        # Composite: glow first, then sprite on top
        result = glow_expanded
        result.paste(img, (radius, radius), img)

        return result

    def generate_hit_set(self, img: Image.Image) -> Dict[str, Image.Image]:
        """
        Generate complete hit effect variant set.

        Creates all common game feedback sprites in one call.

        Args:
            img: Source sprite image

        Returns:
            Dict with keys: 'normal', 'flash', 'damage', 'silhouette'
        """
        return {
            'normal': img.copy() if img.mode == 'RGBA' else img.convert('RGBA'),
            'flash': self.white_flash(img),
            'damage': self.damage_tint(img),
            'silhouette': self.silhouette(img),
        }

    def generate_full_set(self, img: Image.Image,
                          include_outline: bool = False,
                          include_shadow: bool = False,
                          include_glow: bool = False) -> Dict[str, Image.Image]:
        """
        Generate comprehensive effect variant set.

        Args:
            img: Source sprite image
            include_outline: Include outlined variant
            include_shadow: Include shadow variant
            include_glow: Include glow variant

        Returns:
            Dict of all requested effect variants
        """
        variants = self.generate_hit_set(img)

        if include_outline:
            variants['outline'] = self.outline(img)

        if include_shadow:
            variants['shadow'] = self.drop_shadow(img)

        if include_glow:
            variants['glow'] = self.glow(img)

        # Add blink frames
        blink = self.invulnerability_blink(img)
        variants['blink_normal'] = blink[0]
        variants['blink_bright'] = blink[1]

        return variants


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def white_flash(img: Image.Image,
                color: RGB = (255, 255, 255),
                threshold: int = 128) -> Image.Image:
    """Quick white flash effect."""
    return SpriteEffects().white_flash(img, color, threshold)


def damage_tint(img: Image.Image,
                tint: RGB = (255, 0, 0),
                intensity: float = 0.5) -> Image.Image:
    """Quick damage tint effect."""
    return SpriteEffects().damage_tint(img, tint, intensity)


def silhouette(img: Image.Image,
               color: RGB = (0, 0, 0),
               threshold: int = 128) -> Image.Image:
    """Quick silhouette effect."""
    return SpriteEffects().silhouette(img, color, threshold)


def outline(img: Image.Image,
            color: RGB = (0, 0, 0),
            width: int = 1,
            threshold: int = 128) -> Image.Image:
    """Quick outline effect."""
    return SpriteEffects().outline(img, color, width, threshold)


def drop_shadow(img: Image.Image,
                color: RGBA = (0, 0, 0, 128),
                offset: Tuple[int, int] = (2, 2),
                threshold: int = 128) -> Image.Image:
    """Quick drop shadow effect."""
    return SpriteEffects().drop_shadow(img, color, offset, threshold)


def glow(img: Image.Image,
         color: RGB = (255, 255, 255),
         radius: int = 2,
         threshold: int = 128) -> Image.Image:
    """Quick glow effect."""
    return SpriteEffects().glow(img, color, radius, threshold)


def generate_hit_variants(img: Image.Image) -> Dict[str, Image.Image]:
    """Quick hit variant set generation."""
    return SpriteEffects().generate_hit_set(img)


def palette_swap(img: Image.Image, mapping: ColorMapping) -> Image.Image:
    """Quick palette swap."""
    return SpriteEffects().palette_swap(img, mapping)


# =============================================================================
# BATCH PROCESSING
# =============================================================================

def batch_generate_effects(images: List[Image.Image],
                           effects_list: List[EffectType],
                           config: Optional[EffectConfig] = None,
                           show_progress: bool = False) -> List[Dict[str, Image.Image]]:
    """
    Generate effects for multiple sprites.

    Args:
        images: List of source images
        effects_list: List of effect types to generate
        config: Effect configuration
        show_progress: Print progress

    Returns:
        List of dicts, each containing requested effects for one image
    """
    engine = SpriteEffects(config)
    results = []
    total = len(images)

    effect_funcs = {
        'flash': engine.white_flash,
        'damage': engine.damage_tint,
        'silhouette': engine.silhouette,
        'outline': engine.outline,
        'shadow': engine.drop_shadow,
        'glow': engine.glow,
    }

    for i, img in enumerate(images):
        variants = {'normal': img.copy() if img.mode == 'RGBA' else img.convert('RGBA')}

        for effect in effects_list:
            if effect == 'blink':
                blink = engine.invulnerability_blink(img)
                variants['blink_normal'] = blink[0]
                variants['blink_bright'] = blink[1]
            elif effect in effect_funcs:
                variants[effect] = effect_funcs[effect](img)

        results.append(variants)

        if show_progress and (i + 1) % 10 == 0:
            print(f"  Generated effects for {i + 1}/{total} sprites...")

    return results


# =============================================================================
# GENESIS-SPECIFIC HELPERS
# =============================================================================

def create_genesis_hit_palette(base_palette: List[RGB],
                                flash_color: RGB = (238, 238, 238)) -> List[RGB]:
    """
    Create Genesis-compatible flash palette.

    Genesis uses BGR 3-3-3 (9-bit color), so we quantize the flash color.

    Args:
        base_palette: Original 16-color palette
        flash_color: Flash color (will be quantized to Genesis range)

    Returns:
        New palette with all colors set to flash color
    """
    # Quantize to Genesis 9-bit color (0-7 per channel, scaled to 0-255)
    def quantize_genesis(c: int) -> int:
        return (c // 32) * 32 + 16  # 8 levels: 16, 48, 80, 112, 144, 176, 208, 240

    quantized = (
        quantize_genesis(flash_color[0]),
        quantize_genesis(flash_color[1]),
        quantize_genesis(flash_color[2]),
    )

    # Keep index 0 (transparency) as-is, flash all others
    return [base_palette[0]] + [quantized] * (len(base_palette) - 1)


def create_damage_palette(base_palette: List[RGB],
                          tint: RGB = (255, 0, 0),
                          intensity: float = 0.3) -> List[RGB]:
    """
    Create damage-tinted palette for Genesis CRAM swap.

    More efficient than per-pixel tinting on Genesis hardware.

    Args:
        base_palette: Original 16-color palette
        tint: Damage tint color
        intensity: Blend intensity

    Returns:
        Tinted palette
    """
    result = [base_palette[0]]  # Keep transparency

    for color in base_palette[1:]:
        r = int(color[0] * (1 - intensity) + tint[0] * intensity)
        g = int(color[1] * (1 - intensity) + tint[1] * intensity)
        b = int(color[2] * (1 - intensity) + tint[2] * intensity)
        result.append((
            max(0, min(255, r)),
            max(0, min(255, g)),
            max(0, min(255, b)),
        ))

    return result
