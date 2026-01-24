"""
Dynamic Prompt System for Retro Game Asset Generation.

Builds AI generation prompts that enforce console constraints FROM THE START:
- Tile grid alignment (8x8 or 16x16)
- Color limits per palette/sprite
- Tile mirroring optimization (H-flip, V-flip)
- Sprite count limits
- Platform-specific visual styles

Usage:
    from asset_generators.prompt_system import PromptBuilder

    builder = PromptBuilder("nes")
    prompt = builder.sprite_prompt(
        description="robot enemy with laser eyes",
        size=(16, 16),
        animation="idle"
    )
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

from .tier_system import (
    AssetTier, TIER_SPECS, PLATFORM_TIER_MAP,
    get_tier_for_platform, get_tier_spec,
    PlatformPaletteConfig, PLATFORM_PALETTE_CONFIGS,
)


# =============================================================================
# Platform Constraint Definitions
# =============================================================================

@dataclass
class PlatformConstraints:
    """
    Hardware constraints for a specific platform.

    These constraints should be built into prompts FROM GENERATION
    to produce assets that work within platform limits without
    heavy post-processing.
    """

    platform: str
    display_name: str

    # Resolution
    native_width: int
    native_height: int

    # Tile system
    tile_size: Tuple[int, int]
    max_unique_tiles: int
    tiles_per_row: int  # For CHR alignment

    # Color constraints
    colors_per_palette: int
    num_sprite_palettes: int
    num_bg_palettes: int
    total_onscreen_colors: int

    # Sprite constraints
    max_sprite_width: int
    max_sprite_height: int
    sprites_per_scanline: int
    oam_entries: int  # Total hardware sprites

    # Tile optimization hints
    supports_h_flip: bool
    supports_v_flip: bool
    encourages_symmetry: bool  # True if flipping is common/expected

    # Style keywords
    style_keywords: List[str] = field(default_factory=list)
    anti_keywords: List[str] = field(default_factory=list)  # Things to avoid

    # Platform-specific notes
    notes: str = ""


# Platform constraint definitions
PLATFORM_CONSTRAINTS: Dict[str, PlatformConstraints] = {
    # -------------------------------------------------------------------------
    # NES / Famicom
    # -------------------------------------------------------------------------
    'nes': PlatformConstraints(
        platform='nes',
        display_name='NES/Famicom',
        native_width=256,
        native_height=240,
        tile_size=(8, 8),
        max_unique_tiles=256,
        tiles_per_row=16,
        colors_per_palette=4,  # Including transparent
        num_sprite_palettes=4,
        num_bg_palettes=4,
        total_onscreen_colors=25,  # 4 palettes * 3 colors + 1 shared + 12 bg
        max_sprite_width=8,  # 8x8 or 8x16 mode
        max_sprite_height=16,
        sprites_per_scanline=8,
        oam_entries=64,
        supports_h_flip=True,
        supports_v_flip=True,
        encourages_symmetry=True,
        style_keywords=[
            'NES 8-bit pixel art',
            '4 colors per sprite',
            'bold black outlines',
            'high contrast',
            'chunky pixels',
            'iconic silhouette',
            'clean readable shapes',
            'no subpixel detail',
        ],
        anti_keywords=[
            'anti-aliasing',
            'smooth gradients',
            'dithering',
            'soft edges',
            'blur',
            'glow effects',
        ],
        notes='Design sprites with horizontal symmetry to save tile space via H-flip.',
    ),

    'famicom': PlatformConstraints(
        platform='famicom',
        display_name='Famicom',
        native_width=256,
        native_height=240,
        tile_size=(8, 8),
        max_unique_tiles=256,
        tiles_per_row=16,
        colors_per_palette=4,
        num_sprite_palettes=4,
        num_bg_palettes=4,
        total_onscreen_colors=25,
        max_sprite_width=8,
        max_sprite_height=16,
        sprites_per_scanline=8,
        oam_entries=64,
        supports_h_flip=True,
        supports_v_flip=True,
        encourages_symmetry=True,
        style_keywords=[
            'Famicom 8-bit',
            '4 colors maximum',
            'bold outlines',
            'high contrast pixels',
        ],
        anti_keywords=[
            'anti-aliasing',
            'gradients',
            'dithering',
        ],
    ),

    # -------------------------------------------------------------------------
    # Game Boy
    # -------------------------------------------------------------------------
    'gb': PlatformConstraints(
        platform='gb',
        display_name='Game Boy',
        native_width=160,
        native_height=144,
        tile_size=(8, 8),
        max_unique_tiles=256,
        tiles_per_row=16,
        colors_per_palette=4,  # 4 shades of green
        num_sprite_palettes=2,
        num_bg_palettes=1,
        total_onscreen_colors=4,
        max_sprite_width=8,
        max_sprite_height=16,
        sprites_per_scanline=10,
        oam_entries=40,
        supports_h_flip=True,
        supports_v_flip=True,
        encourages_symmetry=True,
        style_keywords=[
            'Game Boy monochrome',
            '4 shades only',
            'green tint aesthetic',
            'high contrast',
            'clear silhouettes',
        ],
        anti_keywords=[
            'color',
            'gradients',
            'anti-aliasing',
        ],
    ),

    'gbc': PlatformConstraints(
        platform='gbc',
        display_name='Game Boy Color',
        native_width=160,
        native_height=144,
        tile_size=(8, 8),
        max_unique_tiles=512,  # Two banks
        tiles_per_row=16,
        colors_per_palette=4,
        num_sprite_palettes=8,
        num_bg_palettes=8,
        total_onscreen_colors=56,
        max_sprite_width=8,
        max_sprite_height=16,
        sprites_per_scanline=10,
        oam_entries=40,
        supports_h_flip=True,
        supports_v_flip=True,
        encourages_symmetry=True,
        style_keywords=[
            'Game Boy Color pixel art',
            '4 colors per palette',
            'vibrant saturated colors',
            'clear outlines',
        ],
        anti_keywords=[
            'anti-aliasing',
            'gradients',
        ],
    ),

    # -------------------------------------------------------------------------
    # Sega Master System
    # -------------------------------------------------------------------------
    'sms': PlatformConstraints(
        platform='sms',
        display_name='Sega Master System',
        native_width=256,
        native_height=192,
        tile_size=(8, 8),
        max_unique_tiles=448,
        tiles_per_row=16,
        colors_per_palette=16,
        num_sprite_palettes=1,
        num_bg_palettes=1,
        total_onscreen_colors=32,
        max_sprite_width=8,
        max_sprite_height=16,
        sprites_per_scanline=8,
        oam_entries=64,
        supports_h_flip=False,  # SMS does NOT support sprite flipping!
        supports_v_flip=False,
        encourages_symmetry=False,
        style_keywords=[
            'Sega Master System pixel art',
            '16 colors per sprite',
            'clean pixel edges',
            'subtle shading',
        ],
        anti_keywords=[
            'anti-aliasing',
            'smooth gradients',
        ],
        notes='SMS has NO sprite flipping, so duplicate tiles for mirrored poses.',
    ),

    # -------------------------------------------------------------------------
    # Sega Genesis / Mega Drive
    # -------------------------------------------------------------------------
    'genesis': PlatformConstraints(
        platform='genesis',
        display_name='Sega Genesis',
        native_width=320,
        native_height=224,
        tile_size=(8, 8),
        max_unique_tiles=2048,
        tiles_per_row=16,
        colors_per_palette=16,
        num_sprite_palettes=4,
        num_bg_palettes=4,
        total_onscreen_colors=64,
        max_sprite_width=32,
        max_sprite_height=32,
        sprites_per_scanline=20,
        oam_entries=80,
        supports_h_flip=True,
        supports_v_flip=True,
        encourages_symmetry=True,
        style_keywords=[
            'Sega Genesis 16-bit pixel art',
            '16 colors per palette',
            'vibrant colors',
            'detailed shading',
            'clean pixel edges',
            'iconic 90s game style',
        ],
        anti_keywords=[
            'anti-aliasing',
            'photorealistic',
        ],
    ),

    'megadrive': PlatformConstraints(
        platform='megadrive',
        display_name='Mega Drive',
        native_width=320,
        native_height=224,
        tile_size=(8, 8),
        max_unique_tiles=2048,
        tiles_per_row=16,
        colors_per_palette=16,
        num_sprite_palettes=4,
        num_bg_palettes=4,
        total_onscreen_colors=64,
        max_sprite_width=32,
        max_sprite_height=32,
        sprites_per_scanline=20,
        oam_entries=80,
        supports_h_flip=True,
        supports_v_flip=True,
        encourages_symmetry=True,
        style_keywords=[
            'Mega Drive 16-bit',
            '16 colors per palette',
            'bold colors',
        ],
        anti_keywords=[
            'anti-aliasing',
        ],
    ),

    # -------------------------------------------------------------------------
    # Super Nintendo / Super Famicom
    # -------------------------------------------------------------------------
    'snes': PlatformConstraints(
        platform='snes',
        display_name='Super Nintendo',
        native_width=256,
        native_height=224,
        tile_size=(8, 8),
        max_unique_tiles=1024,
        tiles_per_row=16,
        colors_per_palette=16,
        num_sprite_palettes=8,
        num_bg_palettes=8,
        total_onscreen_colors=256,
        max_sprite_width=64,
        max_sprite_height=64,
        sprites_per_scanline=34,
        oam_entries=128,
        supports_h_flip=True,
        supports_v_flip=True,
        encourages_symmetry=True,
        style_keywords=[
            'Super Nintendo 16-bit pixel art',
            '16 colors per palette',
            'rich color depth',
            'smooth shading',
            'detailed sprites',
            'SNES aesthetic',
        ],
        anti_keywords=[
            'anti-aliasing',
            'photorealistic',
        ],
    ),

    # -------------------------------------------------------------------------
    # PC Engine / TurboGrafx-16
    # -------------------------------------------------------------------------
    'pce': PlatformConstraints(
        platform='pce',
        display_name='PC Engine',
        native_width=256,
        native_height=240,
        tile_size=(8, 8),
        max_unique_tiles=2048,
        tiles_per_row=16,
        colors_per_palette=16,
        num_sprite_palettes=16,
        num_bg_palettes=16,
        total_onscreen_colors=512,
        max_sprite_width=32,
        max_sprite_height=64,
        sprites_per_scanline=16,
        oam_entries=64,
        supports_h_flip=True,
        supports_v_flip=True,
        encourages_symmetry=True,
        style_keywords=[
            'PC Engine pixel art',
            'vibrant anime style',
            '16 colors per sprite',
            'detailed shading',
        ],
        anti_keywords=[
            'anti-aliasing',
        ],
    ),

    # -------------------------------------------------------------------------
    # Neo Geo
    # -------------------------------------------------------------------------
    'neogeo': PlatformConstraints(
        platform='neogeo',
        display_name='Neo Geo',
        native_width=320,
        native_height=224,
        tile_size=(16, 16),
        max_unique_tiles=4096,
        tiles_per_row=16,
        colors_per_palette=16,
        num_sprite_palettes=256,
        num_bg_palettes=256,
        total_onscreen_colors=4096,
        max_sprite_width=512,
        max_sprite_height=512,
        sprites_per_scanline=96,
        oam_entries=380,
        supports_h_flip=True,
        supports_v_flip=True,
        encourages_symmetry=True,
        style_keywords=[
            'Neo Geo arcade quality pixel art',
            'rich color palette',
            'detailed shading and highlights',
            'professional sprite work',
            'fighting game style',
        ],
        anti_keywords=[
            'low resolution',
            'simple',
        ],
    ),

    # -------------------------------------------------------------------------
    # Game Boy Advance
    # -------------------------------------------------------------------------
    'gba': PlatformConstraints(
        platform='gba',
        display_name='Game Boy Advance',
        native_width=240,
        native_height=160,
        tile_size=(8, 8),
        max_unique_tiles=1024,
        tiles_per_row=32,
        colors_per_palette=16,  # Can use 256-color mode too
        num_sprite_palettes=16,
        num_bg_palettes=16,
        total_onscreen_colors=512,
        max_sprite_width=64,
        max_sprite_height=64,
        sprites_per_scanline=128,
        oam_entries=128,
        supports_h_flip=True,
        supports_v_flip=True,
        encourages_symmetry=True,
        style_keywords=[
            'Game Boy Advance pixel art',
            'detailed shading',
            'smooth color transitions',
            'GBA aesthetic',
        ],
        anti_keywords=[
            'anti-aliased edges',
        ],
    ),

    # -------------------------------------------------------------------------
    # Nintendo DS
    # -------------------------------------------------------------------------
    'nds': PlatformConstraints(
        platform='nds',
        display_name='Nintendo DS',
        native_width=256,
        native_height=192,
        tile_size=(8, 8),
        max_unique_tiles=8192,
        tiles_per_row=32,
        colors_per_palette=256,
        num_sprite_palettes=16,
        num_bg_palettes=16,
        total_onscreen_colors=4096,
        max_sprite_width=64,
        max_sprite_height=64,
        sprites_per_scanline=128,
        oam_entries=128,
        supports_h_flip=True,
        supports_v_flip=True,
        encourages_symmetry=True,
        style_keywords=[
            'Nintendo DS pixel art',
            'high color depth',
            'detailed sprites',
            'modern retro style',
        ],
        anti_keywords=[],
    ),
}


# =============================================================================
# Tile Optimization Hints
# =============================================================================

TILE_OPTIMIZATION_HINTS: Dict[str, str] = {
    'symmetry': (
        "Design with HORIZONTAL SYMMETRY when possible - "
        "the left and right halves should mirror each other. "
        "This allows using H-flip to save 50% of tile memory."
    ),
    'v_symmetry': (
        "Design with VERTICAL SYMMETRY when possible - "
        "the top and bottom halves should mirror each other. "
        "This allows using V-flip to save tile memory."
    ),
    'tile_aligned': (
        "Align all visual elements to an 8x8 pixel grid. "
        "Major shapes should fit cleanly within tile boundaries. "
        "Avoid details that span tile edges unnecessarily."
    ),
    'shared_colors': (
        "Use a consistent color palette across the entire sprite. "
        "Pick colors that work well together - avoid subtle variations. "
        "All tiles in a sprite must share the same palette."
    ),
    'clear_silhouette': (
        "Create a clear, recognizable silhouette that reads well at small sizes. "
        "The character should be identifiable from shape alone."
    ),
    'no_orphan_pixels': (
        "Avoid isolated single pixels. Each pixel should connect to at least "
        "one adjacent pixel of the same color (except for highlights/details)."
    ),
    'contrast': (
        "Use high contrast between colors. "
        "Outlines should clearly separate the sprite from any background."
    ),
}


# =============================================================================
# Animation Prompt Hints
# =============================================================================

ANIMATION_HINTS: Dict[str, str] = {
    'idle': "subtle breathing motion or weight shift, character at rest but alive",
    'walk': "clear walk cycle with distinct contact, pass, and lift poses",
    'run': "dynamic running pose with exaggerated motion and clear silhouette",
    'attack': "powerful attack pose with clear anticipation and follow-through",
    'hurt': "recoil pose showing impact, distinct from idle",
    'death': "dramatic death pose, clearly different from other states",
    'jump': "airborne pose with extended limbs showing momentum",
    'fall': "falling pose distinct from jump, showing downward motion",
    'crouch': "low defensive pose with reduced height",
    'climb': "climbing pose with hands/feet positioned for grip",
}


# =============================================================================
# Prompt Builder Class
# =============================================================================

class PromptBuilder:
    """
    Dynamic prompt builder that enforces platform constraints.

    Generates prompts that guide AI models to create assets that:
    1. Fit within hardware color limits
    2. Align to tile grids
    3. Optimize for tile mirroring/reuse
    4. Match platform-specific visual styles

    Usage:
        builder = PromptBuilder("nes")
        prompt = builder.sprite_prompt("robot enemy", size=(16, 16))
    """

    def __init__(self, platform: str):
        """
        Initialize builder for a specific platform.

        Args:
            platform: Platform identifier (e.g., 'nes', 'genesis', 'snes')
        """
        self.platform = platform.lower()

        # Get platform constraints
        if self.platform not in PLATFORM_CONSTRAINTS:
            raise ValueError(f"Unknown platform: {platform}. Available: {list(PLATFORM_CONSTRAINTS.keys())}")

        self.constraints = PLATFORM_CONSTRAINTS[self.platform]
        self.tier = get_tier_for_platform(self.platform)
        self.tier_spec = get_tier_spec(self.tier)

        # Get palette config if available
        self.palette_config = PLATFORM_PALETTE_CONFIGS.get(self.platform)

    def _build_constraint_block(self) -> str:
        """Build the hardware constraints section of the prompt."""
        c = self.constraints

        parts = [
            f"HARDWARE CONSTRAINTS for {c.display_name}:",
            f"- Maximum {c.colors_per_palette} colors per sprite (including transparent)",
            f"- Tile size: {c.tile_size[0]}x{c.tile_size[1]} pixels",
            f"- Align all details to {c.tile_size[0]}x{c.tile_size[1]} grid",
        ]

        if c.encourages_symmetry and c.supports_h_flip:
            parts.append("- DESIGN WITH HORIZONTAL SYMMETRY to enable tile flipping")

        if not c.supports_h_flip:
            parts.append("- NO hardware sprite flipping available")

        return " ".join(parts)

    def _build_style_block(self) -> str:
        """Build the style keywords section."""
        c = self.constraints

        style = ", ".join(c.style_keywords[:5])  # Top 5 keywords
        anti = ", ".join(f"no {kw}" for kw in c.anti_keywords[:3])

        return f"STYLE: {style}. {anti}."

    def _build_optimization_hints(self, include_hints: List[str]) -> str:
        """Build optimization hints section."""
        hints = [TILE_OPTIMIZATION_HINTS[h] for h in include_hints if h in TILE_OPTIMIZATION_HINTS]
        if hints:
            return "OPTIMIZATION: " + " ".join(hints)
        return ""

    def sprite_prompt(
        self,
        description: str,
        size: Tuple[int, int] = None,
        animation: str = None,
        facing: str = "right",
        include_hints: List[str] = None,
        extra_style: str = None,
    ) -> str:
        """
        Build a prompt for sprite generation.

        Args:
            description: What the sprite depicts (e.g., "robot enemy")
            size: Sprite dimensions (width, height). Defaults to platform recommendation.
            animation: Animation pose (e.g., 'idle', 'walk', 'attack')
            facing: Direction character faces ('left', 'right', 'front')
            include_hints: List of optimization hints to include
            extra_style: Additional style instructions

        Returns:
            Complete prompt string optimized for the platform
        """
        c = self.constraints

        # Default size to platform recommendation
        if size is None:
            size = self.tier_spec.recommended_sprite_size

        # Default hints for sprites
        if include_hints is None:
            include_hints = ['symmetry', 'tile_aligned', 'clear_silhouette', 'contrast']
            if not c.supports_h_flip:
                include_hints.remove('symmetry')

        # Build prompt parts
        parts = []

        # Main description with size
        parts.append(
            f"Create a {size[0]}x{size[1]} pixel sprite of {description}, "
            f"facing {facing}."
        )

        # Animation hint
        if animation and animation in ANIMATION_HINTS:
            parts.append(f"Pose: {ANIMATION_HINTS[animation]}.")

        # Platform constraints
        parts.append(self._build_constraint_block())

        # Style keywords
        parts.append(self._build_style_block())

        # Optimization hints
        opt_hints = self._build_optimization_hints(include_hints)
        if opt_hints:
            parts.append(opt_hints)

        # Extra style
        if extra_style:
            parts.append(extra_style)

        # Platform notes
        if c.notes:
            parts.append(f"NOTE: {c.notes}")

        return " ".join(parts)

    def background_prompt(
        self,
        description: str,
        tileable: bool = True,
        scrolling: str = None,
        include_hints: List[str] = None,
        extra_style: str = None,
    ) -> str:
        """
        Build a prompt for background generation.

        Args:
            description: What the background depicts
            tileable: Whether the background should tile seamlessly
            scrolling: Scroll direction ('horizontal', 'vertical', 'both', None)
            include_hints: List of optimization hints
            extra_style: Additional style instructions

        Returns:
            Complete prompt string
        """
        c = self.constraints

        # Default hints for backgrounds
        if include_hints is None:
            include_hints = ['tile_aligned', 'shared_colors']

        parts = []

        # Main description
        tile_count = f"using max {c.max_unique_tiles} unique tiles"
        parts.append(
            f"Create a {c.display_name} background of {description}, "
            f"{tile_count}, on a {c.tile_size[0]}x{c.tile_size[1]} tile grid."
        )

        # Tileable instruction
        if tileable:
            if scrolling == 'horizontal':
                parts.append("Must tile SEAMLESSLY HORIZONTALLY for side-scrolling.")
            elif scrolling == 'vertical':
                parts.append("Must tile SEAMLESSLY VERTICALLY for vertical scrolling.")
            elif scrolling == 'both':
                parts.append("Must tile SEAMLESSLY in both directions.")
            else:
                parts.append("Design for tile reuse - repeat patterns to save tiles.")

        # Platform constraints
        parts.append(self._build_constraint_block())

        # Style
        parts.append(self._build_style_block())

        # Optimization
        opt_hints = self._build_optimization_hints(include_hints)
        if opt_hints:
            parts.append(opt_hints)

        if extra_style:
            parts.append(extra_style)

        return " ".join(parts)

    def tile_prompt(
        self,
        description: str,
        count: int = 1,
        tileset_theme: str = None,
        include_hints: List[str] = None,
    ) -> str:
        """
        Build a prompt for individual tile generation.

        Args:
            description: What the tile depicts
            count: Number of tile variations to create
            tileset_theme: Theme for coherent tileset
            include_hints: List of optimization hints

        Returns:
            Complete prompt string
        """
        c = self.constraints

        if include_hints is None:
            include_hints = ['tile_aligned', 'shared_colors']

        parts = []

        size = c.tile_size
        parts.append(
            f"Create {count} {size[0]}x{size[1]} pixel tile(s) of {description}, "
            f"using exactly {c.colors_per_palette} colors."
        )

        if tileset_theme:
            parts.append(f"Part of {tileset_theme} tileset - maintain visual consistency.")

        parts.append("Must be tileable (edges must match when repeated).")
        parts.append(self._build_style_block())

        opt_hints = self._build_optimization_hints(include_hints)
        if opt_hints:
            parts.append(opt_hints)

        return " ".join(parts)

    def animation_set_prompt(
        self,
        description: str,
        animations: List[str],
        size: Tuple[int, int] = None,
        include_hints: List[str] = None,
    ) -> str:
        """
        Build a prompt for a coherent animation set.

        Args:
            description: Character description
            animations: List of animations to include
            size: Sprite size for all frames
            include_hints: Optimization hints

        Returns:
            Complete prompt string
        """
        c = self.constraints

        if size is None:
            size = self.tier_spec.recommended_sprite_size

        if include_hints is None:
            include_hints = ['symmetry', 'shared_colors', 'clear_silhouette']

        parts = []

        # Get frame counts
        frame_counts = []
        for anim in animations:
            count = self.tier_spec.recommended_frame_counts.get(anim, 4)
            if anim in ANIMATION_HINTS:
                frame_counts.append(f"{anim} ({count} frames): {ANIMATION_HINTS[anim]}")
            else:
                frame_counts.append(f"{anim} ({count} frames)")

        parts.append(
            f"Create animation sprite sheet for {description}, "
            f"{size[0]}x{size[1]} pixels per frame."
        )

        parts.append("ANIMATIONS NEEDED: " + "; ".join(frame_counts))

        parts.append(
            "ALL FRAMES MUST: share the same color palette, "
            "maintain consistent proportions, "
            "use matching outline style."
        )

        parts.append(self._build_constraint_block())
        parts.append(self._build_style_block())

        opt_hints = self._build_optimization_hints(include_hints)
        if opt_hints:
            parts.append(opt_hints)

        return " ".join(parts)

    def upscale_prompt(
        self,
        source_platform: str,
        description: str = None,
    ) -> str:
        """
        Build a prompt for cross-gen upscaling (8-bit to 16-bit).

        Args:
            source_platform: Original platform (e.g., 'nes')
            description: Optional description of the content

        Returns:
            Action-oriented prompt for img2img upscaling
        """
        c = self.constraints
        source = PLATFORM_CONSTRAINTS.get(source_platform.lower())

        parts = []

        # Action-oriented instruction (required for Kontext-style models)
        parts.append("Upscale and enhance this pixel art sprite.")

        # Color expansion
        if source:
            color_increase = c.colors_per_palette - source.colors_per_palette
            if color_increase > 0:
                parts.append(
                    f"Expand from {source.colors_per_palette} to {c.colors_per_palette} colors. "
                    f"Add {color_increase} additional shades for smoother gradients."
                )

        # Detail enhancement
        parts.append(
            "Add fine details: subtle texture, enhanced shading with highlights and shadows, "
            "smooth color transitions while maintaining sharp pixel edges."
        )

        # Preserve original
        parts.append(
            "PRESERVE: original composition, character silhouette, color palette hues, "
            "and recognizable features. Do not change the subject or add new elements."
        )

        # Target style
        parts.append(f"Target quality: {c.display_name} {', '.join(c.style_keywords[:3])}.")

        if description:
            parts.append(f"Content: {description}")

        return " ".join(parts)

    def get_dimensions(self, asset_type: str = 'sprite') -> Tuple[int, int]:
        """
        Get recommended dimensions for an asset type.

        Args:
            asset_type: 'sprite', 'background', 'tile'

        Returns:
            (width, height) tuple
        """
        c = self.constraints

        if asset_type == 'sprite':
            return self.tier_spec.recommended_sprite_size
        elif asset_type == 'tile':
            return c.tile_size
        elif asset_type == 'background':
            return (c.native_width, c.native_height)
        else:
            return self.tier_spec.recommended_sprite_size

    def get_max_colors(self) -> int:
        """Get maximum colors per sprite/palette for this platform."""
        return self.constraints.colors_per_palette

    def supports_flipping(self) -> Tuple[bool, bool]:
        """Check if platform supports H-flip and V-flip."""
        return (self.constraints.supports_h_flip, self.constraints.supports_v_flip)


# =============================================================================
# Convenience Functions
# =============================================================================

def get_platform_prompt(
    platform: str,
    asset_type: str,
    description: str,
    **kwargs
) -> str:
    """
    Quick function to get a platform-appropriate prompt.

    Args:
        platform: Target platform
        asset_type: 'sprite', 'background', 'tile', 'animation_set'
        description: Asset description
        **kwargs: Additional arguments for the specific prompt type

    Returns:
        Complete prompt string
    """
    builder = PromptBuilder(platform)

    if asset_type == 'sprite':
        return builder.sprite_prompt(description, **kwargs)
    elif asset_type == 'background':
        return builder.background_prompt(description, **kwargs)
    elif asset_type == 'tile':
        return builder.tile_prompt(description, **kwargs)
    elif asset_type == 'animation_set':
        animations = kwargs.pop('animations', ['idle', 'walk'])
        return builder.animation_set_prompt(description, animations, **kwargs)
    elif asset_type == 'upscale':
        source = kwargs.get('source_platform', 'nes')
        return builder.upscale_prompt(source, description)
    else:
        raise ValueError(f"Unknown asset type: {asset_type}")


def get_available_platforms() -> List[str]:
    """Get list of supported platforms."""
    return list(PLATFORM_CONSTRAINTS.keys())


def get_platform_info(platform: str) -> Dict[str, Any]:
    """Get detailed info about a platform's constraints."""
    if platform.lower() not in PLATFORM_CONSTRAINTS:
        return {}

    c = PLATFORM_CONSTRAINTS[platform.lower()]
    return {
        'name': c.display_name,
        'resolution': (c.native_width, c.native_height),
        'tile_size': c.tile_size,
        'colors_per_palette': c.colors_per_palette,
        'max_tiles': c.max_unique_tiles,
        'supports_h_flip': c.supports_h_flip,
        'supports_v_flip': c.supports_v_flip,
        'style_keywords': c.style_keywords,
        'notes': c.notes,
    }


# =============================================================================
# CLI for Testing
# =============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Dynamic Prompt System')
    parser.add_argument('--platform', default='nes', help='Target platform')
    parser.add_argument('--type', default='sprite', help='Asset type')
    parser.add_argument('--desc', default='robot enemy', help='Description')
    parser.add_argument('--list', action='store_true', help='List platforms')

    args = parser.parse_args()

    if args.list:
        print("Available platforms:")
        for p in get_available_platforms():
            info = get_platform_info(p)
            print(f"  {p}: {info['name']} - {info['colors_per_palette']} colors/palette, "
                  f"{info['tile_size'][0]}x{info['tile_size'][1]} tiles")
    else:
        prompt = get_platform_prompt(args.platform, args.type, args.desc)
        print(f"Platform: {args.platform.upper()}")
        print(f"Asset type: {args.type}")
        print(f"Description: {args.desc}")
        print()
        print("GENERATED PROMPT:")
        print("-" * 60)
        print(prompt)
