"""
Background Generator - AI-powered scrolling background generation.

Features:
- Generate backgrounds N screens wide
- Seamless horizontal looping
- Tile deduplication with platform limits
- Automatic tile reduction if over limit
- Collision layer generation (optional)
"""

import os
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

try:
    from PIL import Image, ImageFilter, ImageEnhance
    import numpy as np
except ImportError:
    raise ImportError("PIL and numpy required: pip install pillow numpy")

from .base_generator import (
    AssetGenerator, GeneratedAsset, GenerationFlags,
    PlatformConfig, get_nes_config, get_platform_config,
    get_platform_limits, validate_asset_for_platform,
)

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from tile_optimizers.tile_deduplicator import TileDeduplicator, TileOptimizationResult


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class ScrollingBackground:
    """Result of scrolling background generation."""

    name: str
    full_image: Image.Image
    optimized_tiles: TileOptimizationResult

    # Dimensions
    width_pixels: int
    height_pixels: int
    width_screens: int

    # Tile data
    chr_data: bytes
    tilemap: List[int]
    palette: List[int]

    # Metadata
    is_seamless: bool = False
    collision_map: Optional[List[int]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    @property
    def tile_count(self) -> int:
        return self.optimized_tiles.unique_count if self.optimized_tiles else 0

    @property
    def savings_percent(self) -> float:
        return self.optimized_tiles.savings_percent if self.optimized_tiles else 0.0


@dataclass
class AnimatedBackground:
    """Result of animated background generation with multiple frames."""

    name: str
    frames: List[Image.Image]           # All animation frames
    frame_count: int

    # Dimensions
    width_pixels: int
    height_pixels: int
    width_screens: int

    # Per-frame CHR data (one bank per frame for bank swapping)
    chr_banks: List[bytes]              # CHR data for each frame
    tilemaps: List[List[int]]           # Tilemap for each frame
    palette: List[int]                  # Unified palette across frames

    # Animation metadata
    animation_type: str = 'water'       # water, lava, neon, etc.
    speed_ms: int = 150                 # Milliseconds per frame
    is_seamless: bool = True

    # Optimization stats per frame
    tiles_per_frame: List[int] = field(default_factory=list)
    bank_utilization: List[float] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    @property
    def total_chr_size(self) -> int:
        return sum(len(bank) for bank in self.chr_banks)

    @property
    def max_tiles_used(self) -> int:
        return max(self.tiles_per_frame) if self.tiles_per_frame else 0


# Animation presets for backgrounds
BACKGROUND_ANIMATION_PRESETS = {
    'water': {
        'frames': 4,
        'speed_ms': 150,
        'description': 'Flowing water with wave patterns',
        'style_hint': 'horizontal wave motion, blue tones, ripple effects',
        'variation': 'wave_offset',  # How frames differ
    },
    'lava': {
        'frames': 4,
        'speed_ms': 120,
        'description': 'Flowing lava with bubbles',
        'style_hint': 'slow flow, orange-red glow, bubbling spots',
        'variation': 'brightness_pulse',
    },
    'neon': {
        'frames': 2,
        'speed_ms': 500,
        'description': 'Flickering neon signs',
        'style_hint': 'bright colors, subtle flicker, glow effect',
        'variation': 'brightness_flicker',
    },
    'neon_pulse': {
        'frames': 4,
        'speed_ms': 200,
        'description': 'Pulsing neon glow',
        'style_hint': 'color cycling, synthwave aesthetic',
        'variation': 'color_pulse',
    },
    'stars': {
        'frames': 4,
        'speed_ms': 300,
        'description': 'Twinkling starfield',
        'style_hint': 'dark background, varying star brightness',
        'variation': 'point_brightness',
    },
    'waterfall': {
        'frames': 4,
        'speed_ms': 100,
        'description': 'Vertical waterfall',
        'style_hint': 'downward flow, white foam, mist',
        'variation': 'vertical_scroll',
    },
    'electric': {
        'frames': 4,
        'speed_ms': 60,
        'description': 'Electric arcs and sparks',
        'style_hint': 'white-blue jagged lines, random paths',
        'variation': 'random_lines',
    },
    'conveyor': {
        'frames': 4,
        'speed_ms': 100,
        'description': 'Moving conveyor belt',
        'style_hint': 'horizontal stripes, industrial',
        'variation': 'horizontal_scroll',
    },
    'fire': {
        'frames': 4,
        'speed_ms': 80,
        'description': 'Flickering flames',
        'style_hint': 'yellow-orange-red, upward flicker',
        'variation': 'upward_wave',
    },
}


@dataclass
class CompositionZone:
    """Defines a horizontal zone in the background composition."""

    name: str
    y_start_percent: float  # 0.0 - 1.0
    y_end_percent: float
    description: str
    tile_density: str = "normal"  # sparse, normal, dense


# Default composition zones for backgrounds
DEFAULT_ZONES = [
    CompositionZone("sky", 0.0, 0.35, "Sky area with clouds or stars", "sparse"),
    CompositionZone("midground", 0.35, 0.7, "Buildings, trees, or distant features", "normal"),
    CompositionZone("ground", 0.7, 1.0, "Ground level, platforms, street", "dense"),
]


# =============================================================================
# Background Generator
# =============================================================================

class BackgroundGenerator(AssetGenerator):
    """Generate scrolling backgrounds with tile optimization."""

    def __init__(
        self,
        platform: Optional[PlatformConfig] = None,
        api_key: Optional[str] = None,
    ):
        """Initialize background generator."""
        platform = platform or get_nes_config()
        super().__init__(platform, api_key)

        self.deduplicator = TileDeduplicator(
            tile_width=platform.tile_width,
            tile_height=platform.tile_height,
            enable_h_flip=platform.enable_flip_optimization,
            enable_v_flip=platform.enable_flip_optimization,
        )

    def generate(self, description: str, **kwargs) -> GeneratedAsset:
        """Generate a basic background asset."""
        bg = self.generate_scrolling_bg(
            description=description,
            width_screens=kwargs.get('width_screens', 2),
            seamless=kwargs.get('seamless', True),
        )

        return GeneratedAsset(
            name=bg.name,
            image=bg.full_image,
            palette=bg.palette,
            chr_data=bg.chr_data,
            tile_map=bg.tilemap,
            metadata=bg.metadata,
            warnings=bg.warnings,
        )

    def optimize(self, asset: GeneratedAsset) -> GeneratedAsset:
        """Optimize an existing background asset."""
        # Re-run tile optimization
        optimized = self.deduplicator.optimize(asset.image)

        asset.chr_data = self.deduplicator.generate_chr(optimized)
        asset.tile_map = self.deduplicator.generate_tilemap(optimized)
        asset.metadata['unique_tiles'] = optimized.unique_count
        asset.metadata['savings_percent'] = optimized.savings_percent

        return asset

    # -------------------------------------------------------------------------
    # Main Generation Methods
    # -------------------------------------------------------------------------

    def generate_scrolling_bg(
        self,
        description: str,
        width_screens: int = 2,
        seamless: bool = True,
        zones: Optional[List[CompositionZone]] = None,
    ) -> ScrollingBackground:
        """
        Generate a scrolling background.

        Args:
            description: Text description of the background
            width_screens: Width in screen units (1 screen = platform width)
            seamless: Whether to ensure seamless horizontal looping
            zones: Optional custom composition zones

        Returns:
            ScrollingBackground with optimized tiles
        """
        zones = zones or DEFAULT_ZONES

        # Calculate dimensions
        width = self.platform.screen_width * width_screens
        height = self.platform.screen_height

        # Build generation prompt
        prompt = self._build_background_prompt(
            description, width, height, seamless, zones
        )

        # Generate image
        raw_image = self.client.generate_image(
            prompt=prompt,
            width=width,
            height=height,
            model='flux',
        )

        # Post-process
        processed = self._postprocess_background(raw_image, seamless)

        # Optimize tiles
        optimized = self.deduplicator.optimize(processed)

        # Validate against full platform system limits
        max_tiles = self.platform.max_tiles_per_bank
        validation = validate_asset_for_platform(
            self.platform.name.lower(),
            tile_count=optimized.unique_count,
            colors_used=self.platform.colors_per_palette * self.platform.max_palettes,
            sprite_count=0,
        )

        # Check tile limits and reduce if needed
        if not validation['valid'] or optimized.unique_count > max_tiles:
            processed = self._reduce_tiles(processed, optimized, max_tiles)
            optimized = self.deduplicator.optimize(processed)

        # Extract palette
        palette = self._extract_bg_palette(processed)

        # Generate CHR and tilemap
        chr_data = self.deduplicator.generate_chr(optimized)
        tilemap = self.deduplicator.generate_tilemap(optimized)

        # Build warnings from validation
        warnings = validation.get('warnings', []).copy()
        warnings.extend(validation.get('errors', []))

        # Additional proximity warning
        valid, msg = self.platform.validate_tile_count(optimized.unique_count)
        if msg:
            warnings.append(msg)

        # Create name from description
        name = self._sanitize_name(description)

        return ScrollingBackground(
            name=name,
            full_image=processed,
            optimized_tiles=optimized,
            width_pixels=width,
            height_pixels=height,
            width_screens=width_screens,
            chr_data=chr_data,
            tilemap=tilemap,
            palette=palette,
            is_seamless=seamless,
            metadata={
                'description': description,
                'unique_tiles': optimized.unique_count,
                'total_tiles': optimized.total_tiles,
                'savings_percent': optimized.savings_percent,
                'platform': self.platform.name,
                'zones': [z.name for z in zones],
            },
            warnings=warnings,
        )

    def generate_with_collision(
        self,
        description: str,
        width_screens: int = 2,
        seamless: bool = True,
    ) -> ScrollingBackground:
        """
        Generate background with collision layer.

        Args:
            description: Background description
            width_screens: Width in screens
            seamless: Seamless looping

        Returns:
            ScrollingBackground with collision_map populated
        """
        # Generate base background
        bg = self.generate_scrolling_bg(description, width_screens, seamless)

        # Generate collision map
        bg.collision_map = self._generate_collision_map(bg.full_image)
        bg.metadata['has_collision'] = True

        return bg

    # -------------------------------------------------------------------------
    # Animated Background Generation
    # -------------------------------------------------------------------------

    def generate_animated_bg(
        self,
        description: str,
        animation_type: str = 'water',
        width_screens: int = 1,
        frame_count: Optional[int] = None,
        speed_ms: Optional[int] = None,
    ) -> AnimatedBackground:
        """
        Generate animated background with multiple CHR bank frames.

        Each frame is a complete background that fits within the platform's
        system limits (not just CHR limits). Uses comprehensive platform
        constraints including animation capabilities, tile limits, and
        color restrictions.

        Args:
            description: Background scene description
            animation_type: Type of animation (water, lava, neon, etc.)
            width_screens: Width in screens (usually 1 for animated BGs)
            frame_count: Override frame count from preset
            speed_ms: Override animation speed from preset

        Returns:
            AnimatedBackground with per-frame CHR banks
        """
        # Get preset configuration
        preset = BACKGROUND_ANIMATION_PRESETS.get(
            animation_type,
            BACKGROUND_ANIMATION_PRESETS['water']
        )

        frame_count = frame_count or preset['frames']
        speed_ms = speed_ms or preset['speed_ms']

        # Validate against full platform system limits (not just CHR)
        can_animate, reason = self.platform.can_animate_chr(frame_count)
        if not can_animate:
            # Platform doesn't support CHR animation or has limited frames
            if not self.platform.supports_chr_animation:
                print(f"  WARNING: {self.platform.name} does not support CHR animation")
                print(f"           Generating static background instead")
                frame_count = 1
            else:
                # Reduce to platform's max animation frames
                old_count = frame_count
                frame_count = min(frame_count, self.platform.max_animation_frames)
                if frame_count != old_count:
                    print(f"  WARNING: Reduced frames from {old_count} to {frame_count}")
                    print(f"           ({self.platform.name} max: {self.platform.max_animation_frames})")

        # Also check animation bank availability
        if frame_count > self.platform.animation_banks_available:
            old_count = frame_count
            frame_count = max(1, self.platform.animation_banks_available)
            print(f"  WARNING: Reduced frames from {old_count} to {frame_count}")
            print(f"           (only {self.platform.animation_banks_available} animation banks available)")

        # Calculate dimensions
        width = self.platform.screen_width * width_screens
        height = self.platform.screen_height

        # Generate all frames
        frames = []
        chr_banks = []
        tilemaps = []
        tiles_per_frame = []
        bank_utilization = []
        warnings = []

        print(f"  Generating {frame_count} animation frames for: {description}")
        print(f"  Animation type: {animation_type} ({preset['description']})")
        print(f"  Platform: {self.platform.name} (Tier: {self.platform.tier})")
        print(f"  System limits:")
        print(f"    - Max tiles per bank: {self.platform.max_tiles_per_bank}")
        print(f"    - Colors per palette: {self.platform.colors_per_palette}")
        print(f"    - Max palettes: {self.platform.max_palettes}")
        print(f"    - Animation frames: {self.platform.max_animation_frames}")
        print(f"    - Animation banks: {self.platform.animation_banks_available}")

        for frame_idx in range(frame_count):
            print(f"    Frame {frame_idx + 1}/{frame_count}...", end=" ")

            # Build frame-specific prompt
            prompt = self._build_animated_frame_prompt(
                description,
                animation_type,
                preset,
                frame_idx,
                frame_count,
                width,
                height,
            )

            # Generate frame
            raw_frame = self.client.generate_image(
                prompt=prompt,
                width=width,
                height=height,
                model='flux',
                seed=42 + frame_idx,  # Consistent but different per frame
            )

            # Post-process
            processed = self._postprocess_background(raw_frame, seamless=True)

            # Apply frame variation based on animation type
            processed = self._apply_frame_variation(
                processed,
                animation_type,
                frame_idx,
                frame_count,
                preset['variation'],
            )

            # Optimize tiles
            optimized = self.deduplicator.optimize(processed)

            # Validate against platform system limits (tiles, colors, etc.)
            max_tiles = self.platform.max_tiles_per_bank
            validation = validate_asset_for_platform(
                self.platform.name.lower(),
                tile_count=optimized.unique_count,
                colors_used=self.platform.colors_per_palette,  # Per-frame palette
                sprite_count=0,  # Backgrounds don't use sprites
            )

            # Check tile limit and reduce if needed
            if not validation['valid'] or optimized.unique_count > max_tiles:
                processed = self._reduce_tiles_aggressive(
                    processed,
                    optimized,
                    max_tiles,
                    animation_type,
                )
                optimized = self.deduplicator.optimize(processed)

                if optimized.unique_count > max_tiles:
                    warnings.append(
                        f"Frame {frame_idx}: {optimized.unique_count} tiles "
                        f"exceeds {self.platform.name} limit ({max_tiles})"
                    )

            # Add any validation warnings
            warnings.extend(validation.get('warnings', []))

            # Generate CHR and tilemap for this frame
            chr_data = self.deduplicator.generate_chr(optimized)
            tilemap = self.deduplicator.generate_tilemap(optimized)

            frames.append(processed)
            chr_banks.append(chr_data)
            tilemaps.append(tilemap)
            tiles_per_frame.append(optimized.unique_count)
            bank_utilization.append(
                (optimized.unique_count / max_tiles) * 100
            )

            print(f"{optimized.unique_count} tiles ({bank_utilization[-1]:.1f}% bank)")

        # Extract unified palette from all frames
        palette = self._extract_unified_palette(frames)

        # Create name
        name = self._sanitize_name(description)

        return AnimatedBackground(
            name=name,
            frames=frames,
            frame_count=frame_count,
            width_pixels=width,
            height_pixels=height,
            width_screens=width_screens,
            chr_banks=chr_banks,
            tilemaps=tilemaps,
            palette=palette,
            animation_type=animation_type,
            speed_ms=speed_ms,
            is_seamless=True,
            tiles_per_frame=tiles_per_frame,
            bank_utilization=bank_utilization,
            metadata={
                'description': description,
                'animation_preset': animation_type,
                'platform': self.platform.name,
                'max_tiles_per_bank': self.platform.max_tiles_per_bank,
            },
            warnings=warnings,
        )

    def _build_animated_frame_prompt(
        self,
        description: str,
        animation_type: str,
        preset: Dict,
        frame_idx: int,
        frame_count: int,
        width: int,
        height: int,
    ) -> str:
        """Build prompt for a specific animation frame."""

        style = self._build_style_prompt()

        # Frame-specific variation instructions
        phase = frame_idx / frame_count  # 0.0 to 1.0
        variation_text = self._get_frame_variation_prompt(
            animation_type,
            preset['variation'],
            phase,
        )

        prompt = f"""[ARDK_ANIMATED_BACKGROUND_FRAME]
Create frame {frame_idx + 1} of {frame_count} for animated background: {description}

ANIMATION TYPE: {animation_type} - {preset['description']}

FRAME VARIATION ({frame_idx + 1}/{frame_count}):
{variation_text}

DIMENSIONS: {width}x{height} pixels

STYLE: {style}

TILE OPTIMIZATION (CRITICAL):
- Maximum {self.platform.max_tiles_per_bank} unique 8x8 tiles
- Use repeating patterns extensively
- Solid color regions save tiles
- Gradual variations, not random detail
- Animation comes from frame-to-frame changes, not tile complexity

TECHNICAL:
- {preset['style_hint']}
- Clean pixel edges, no anti-aliasing
- {self.platform.colors_per_palette} colors per palette
- Must loop seamlessly (frame 1 follows frame {frame_count})
"""
        return prompt

    def _get_frame_variation_prompt(
        self,
        animation_type: str,
        variation: str,
        phase: float,
    ) -> str:
        """Get frame-specific variation instructions."""

        if variation == 'wave_offset':
            offset = int(phase * 8)  # 0-7 pixel offset
            return f"Water wave pattern shifted {offset} pixels horizontally"

        elif variation == 'brightness_pulse':
            if phase < 0.25:
                return "Lava at base brightness, some dim glow spots"
            elif phase < 0.5:
                return "Lava slightly brighter, glow spots intensifying"
            elif phase < 0.75:
                return "Lava at peak brightness, bright glow spots visible"
            else:
                return "Lava dimming back, glow spots fading"

        elif variation == 'brightness_flicker':
            return "Neon at full brightness" if phase < 0.5 else "Neon slightly dimmed (flicker)"

        elif variation == 'color_pulse':
            colors = ["magenta dominant", "purple transitioning", "cyan dominant", "purple transitioning"]
            return f"Neon glow phase: {colors[int(phase * 4) % 4]}"

        elif variation == 'point_brightness':
            return f"Stars twinkling phase {int(phase * 4) + 1}: different stars at peak brightness"

        elif variation == 'vertical_scroll':
            offset = int(phase * 8)
            return f"Waterfall pattern shifted {offset} pixels downward"

        elif variation == 'horizontal_scroll':
            offset = int(phase * 8)
            return f"Conveyor stripes shifted {offset} pixels horizontally"

        elif variation == 'upward_wave':
            offset = int(phase * 8)
            return f"Flame pattern shifted {offset} pixels upward with flicker"

        elif variation == 'random_lines':
            return f"Electric arcs in random pattern variation {int(phase * 4) + 1}"

        return f"Animation phase {phase:.2f}"

    def _apply_frame_variation(
        self,
        image: Image.Image,
        animation_type: str,
        frame_idx: int,
        frame_count: int,
        variation: str,
    ) -> Image.Image:
        """Apply programmatic variation to frame for consistent animation."""

        arr = np.array(image)
        height, width = arr.shape[:2]
        phase = frame_idx / frame_count

        if variation == 'wave_offset':
            # Horizontal wave: shift rows by varying amounts
            offset = int(phase * 8)
            result = np.zeros_like(arr)
            for y in range(height):
                wave = int(np.sin((y / 8 + phase * 2 * np.pi) * 0.5) * 2)
                shift = (offset + wave) % width
                result[y] = np.roll(arr[y], shift, axis=0)
            return Image.fromarray(result)

        elif variation == 'vertical_scroll':
            # Vertical scroll: shift all rows down
            offset = int(phase * 8)
            result = np.roll(arr, offset, axis=0)
            return Image.fromarray(result)

        elif variation == 'horizontal_scroll':
            # Horizontal scroll: shift all columns right
            offset = int(phase * 8)
            result = np.roll(arr, offset, axis=1)
            return Image.fromarray(result)

        elif variation == 'brightness_pulse':
            # Brightness modulation
            factor = 0.9 + 0.2 * np.sin(phase * 2 * np.pi)
            result = np.clip(arr * factor, 0, 255).astype(np.uint8)
            return Image.fromarray(result)

        elif variation == 'brightness_flicker':
            # Simple on/off flicker
            factor = 1.0 if phase < 0.5 else 0.85
            result = np.clip(arr * factor, 0, 255).astype(np.uint8)
            return Image.fromarray(result)

        # For variations that are better handled by AI prompting
        return image

    def _reduce_tiles_aggressive(
        self,
        image: Image.Image,
        current_optimized: TileOptimizationResult,
        max_tiles: int,
        animation_type: str,
    ) -> Image.Image:
        """
        Aggressively reduce tiles when standard reduction fails.

        Uses platform-aware strategies:
        1. Increased posterization
        2. Block averaging
        3. Pattern simplification
        """
        reduction_needed = current_optimized.unique_count - max_tiles

        # Strategy 1: Stronger posterization
        arr = np.array(image)
        posterize_levels = max(4, 8 - (reduction_needed // 50))
        arr = (arr // (256 // posterize_levels)) * (256 // posterize_levels)
        image = Image.fromarray(arr.astype(np.uint8))

        # Strategy 2: Block averaging (make 8x8 blocks more uniform)
        arr = np.array(image)
        height, width = arr.shape[:2]
        for ty in range(height // 8):
            for tx in range(width // 8):
                y, x = ty * 8, tx * 8
                block = arr[y:y+8, x:x+8]
                # Find most common color in block
                pixels = block.reshape(-1, 3)
                colors, counts = np.unique(
                    pixels, axis=0, return_counts=True
                )
                if len(colors) > 2:
                    # Keep only top 2 colors
                    top_indices = np.argsort(counts)[-2:]
                    top_colors = colors[top_indices]
                    # Remap other pixels to nearest top color
                    for py in range(8):
                        for px in range(8):
                            pixel = block[py, px]
                            dists = [np.sum((pixel - c) ** 2) for c in top_colors]
                            arr[y+py, x+px] = top_colors[np.argmin(dists)]

        image = Image.fromarray(arr)

        # Re-quantize
        image = self._quantize_to_platform(image)

        return image

    def _extract_unified_palette(
        self,
        frames: List[Image.Image],
    ) -> List[int]:
        """Extract a unified palette that works across all frames."""

        # Combine all frames into one image for palette extraction
        if not frames:
            return [0x0F, 0x00, 0x10, 0x30]

        combined_width = frames[0].width * len(frames)
        combined = Image.new('RGB', (combined_width, frames[0].height))

        for i, frame in enumerate(frames):
            if frame.mode != 'RGB':
                frame = frame.convert('RGB')
            combined.paste(frame, (i * frame.width, 0))

        return self._extract_palette_ai(
            combined,
            num_colors=self.platform.colors_per_palette
        )

    def save_animated_background(
        self,
        bg: AnimatedBackground,
        output_dir: str,
    ) -> Dict[str, str]:
        """
        Save animated background to files.

        Creates:
        - Per-frame CHR banks (for bank swapping)
        - Per-frame tilemaps
        - Unified palette
        - Assembly include with animation config
        - Preview GIF

        Returns dict of created file paths.
        """
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        created_files = {}

        # Save metadata
        metadata = {
            'name': bg.name,
            'animation_type': bg.animation_type,
            'frame_count': bg.frame_count,
            'speed_ms': bg.speed_ms,
            'width_pixels': bg.width_pixels,
            'height_pixels': bg.height_pixels,
            'tiles_per_frame': bg.tiles_per_frame,
            'bank_utilization': bg.bank_utilization,
            'palette': bg.palette,
            'is_seamless': bg.is_seamless,
            'platform': self.platform.name,
            'max_tiles_per_bank': self.platform.max_tiles_per_bank,
            **bg.metadata,
        }
        meta_path = out_path / "metadata.json"
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        created_files['metadata'] = str(meta_path)

        # Save CHR banks (one per frame)
        for i, chr_data in enumerate(bg.chr_banks):
            chr_path = out_path / f"{bg.name}_frame{i}.chr"
            with open(chr_path, 'wb') as f:
                f.write(chr_data)
            created_files[f'chr_frame_{i}'] = str(chr_path)

        # Save tilemaps (one per frame, or shared if identical)
        for i, tilemap in enumerate(bg.tilemaps):
            tm_path = out_path / f"{bg.name}_tilemap{i}.bin"
            with open(tm_path, 'wb') as f:
                f.write(bytes(tilemap))
            created_files[f'tilemap_{i}'] = str(tm_path)

        # Save frame images
        for i, frame in enumerate(bg.frames):
            frame_path = out_path / f"{bg.name}_frame{i}.png"
            frame.save(frame_path)
            created_files[f'frame_{i}'] = str(frame_path)

        # Save animated GIF preview
        gif_path = out_path / f"{bg.name}_preview.gif"
        bg.frames[0].save(
            gif_path,
            save_all=True,
            append_images=bg.frames[1:],
            duration=bg.speed_ms,
            loop=0,
        )
        created_files['preview_gif'] = str(gif_path)

        # Save assembly include
        inc_path = out_path / f"{bg.name}_anim.inc"
        self._write_animated_asm_include(bg, inc_path)
        created_files['include'] = str(inc_path)

        return created_files

    def _write_animated_asm_include(
        self,
        bg: AnimatedBackground,
        path: Path,
    ) -> None:
        """Write assembly include for animated background."""

        # Calculate NES-specific values
        speed_frames = bg.speed_ms // 16  # ~60fps

        chr_bank_refs = "\n".join([
            f";   Frame {i}: .incbin \"{bg.name}_frame{i}.chr\" "
            f"({bg.tiles_per_frame[i]} tiles, {bg.bank_utilization[i]:.0f}% bank)"
            for i in range(bg.frame_count)
        ])

        content = f"""; =============================================================================
; {bg.name} - Animated Background Data
; Generated by ARDK Background Generator
; =============================================================================
; Animation: {bg.animation_type}
; Frames: {bg.frame_count}
; Speed: {bg.speed_ms}ms ({speed_frames} game frames @ 60fps)
; =============================================================================

; Dimensions
{bg.name.upper()}_WIDTH_PIXELS = {bg.width_pixels}
{bg.name.upper()}_HEIGHT_PIXELS = {bg.height_pixels}

; Animation constants
{bg.name.upper()}_FRAME_COUNT = {bg.frame_count}
{bg.name.upper()}_SPEED_MS = {bg.speed_ms}
{bg.name.upper()}_SPEED_FRAMES = {speed_frames}

; Tile usage per frame (for CHR bank allocation)
{bg.name.upper()}_MAX_TILES = {max(bg.tiles_per_frame)}

; Palette (NES format)
{bg.name.upper()}_PALETTE:
    .byte ${bg.palette[0]:02X}, ${bg.palette[1]:02X}, ${bg.palette[2]:02X}, ${bg.palette[3]:02X}

; CHR bank references (include one per animation frame)
{chr_bank_refs}

; Animation update routine:
; 1. Decrement timer, if 0:
;    a. Reset timer to {bg.name.upper()}_SPEED_FRAMES
;    b. Increment frame counter (wrap at FRAME_COUNT)
;    c. Set MMC3 register to swap to new CHR bank
;
; Example (NES MMC3):
;   lda #{bg.name.upper()}_SPEED_FRAMES
;   sta anim_timer
;   ...
;   ; In update:
;   dec anim_timer
;   bne @done
;   ; Timer expired - advance frame
;   lda #CHR_ANIM_SPEED
;   sta anim_timer
;   inc anim_frame
;   lda anim_frame
;   cmp #{bg.name.upper()}_FRAME_COUNT
;   bcc @swap_bank
;   lda #0
;   sta anim_frame
; @swap_bank:
;   ; Swap CHR bank via MMC3 register
;   lda #$82          ; R2 for BG tiles at $0000-$07FF
;   sta $8000
;   lda anim_frame
;   asl a             ; Multiply by bank size offset
;   asl a
;   clc
;   adc #BASE_BG_BANK ; Add base bank number
;   sta $8001
; @done:
"""

        with open(path, 'w') as f:
            f.write(content)

    # -------------------------------------------------------------------------
    # Prompt Building
    # -------------------------------------------------------------------------

    def _build_background_prompt(
        self,
        description: str,
        width: int,
        height: int,
        seamless: bool,
        zones: List[CompositionZone],
    ) -> str:
        """Build prompt for background generation."""

        style = self._build_style_prompt()

        # Zone descriptions
        zone_text = "\n".join([
            f"- {z.name.upper()} ({int(z.y_start_percent*100)}-{int(z.y_end_percent*100)}%): "
            f"{z.description}"
            for z in zones
        ])

        seamless_text = ""
        if seamless:
            seamless_text = """
SEAMLESS LOOPING REQUIREMENT:
- Left and right edges MUST match perfectly for horizontal scrolling
- Avoid distinct landmarks at edges
- Use repeating patterns that tile naturally
- Background should scroll infinitely without visible seam
"""

        prompt = f"""[ARDK_SCROLLING_BACKGROUND]
Create a scrolling game background: {description}

STYLE: {style}

DIMENSIONS: {width}x{height} pixels (will scroll horizontally)

COMPOSITION ZONES:
{zone_text}

TILE OPTIMIZATION:
- Use repeating tile patterns where possible
- Avoid excessive unique detail
- Maximum unique tiles: {self.platform.max_tiles_per_bank}
- Solid color areas save tiles
{seamless_text}
TECHNICAL:
- Clean pixel edges, no anti-aliasing
- Limited color palette ({self.platform.colors_per_palette} colors per palette)
- {self.platform.tile_width}x{self.platform.tile_height} pixel tile grid alignment
"""
        return prompt

    # -------------------------------------------------------------------------
    # Post-Processing
    # -------------------------------------------------------------------------

    def _postprocess_background(
        self,
        image: Image.Image,
        seamless: bool,
    ) -> Image.Image:
        """Post-process generated background."""

        # Ensure correct mode
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Resize if needed
        target_height = self.platform.screen_height
        if image.height != target_height:
            aspect = image.width / image.height
            new_width = int(target_height * aspect)
            # Round to tile boundary
            new_width = (new_width // self.platform.tile_width) * self.platform.tile_width
            image = self._resize_image(image, (new_width, target_height))

        # Ensure seamless if requested
        if seamless:
            image = self._ensure_seamless(image)

        # Quantize colors
        image = self._quantize_to_platform(image)

        return image

    def _ensure_seamless(self, image: Image.Image) -> Image.Image:
        """
        Ensure image loops seamlessly by blending edges.

        Uses a gradient blend at the seam point.
        """
        arr = np.array(image)
        height, width = arr.shape[:2]

        # Blend width (one tile width on each side)
        blend_width = self.platform.tile_width * 2

        if width < blend_width * 4:
            # Image too narrow for proper blending
            return image

        # Create blend mask (0 at left edge, 1 at blend_width)
        blend_mask = np.linspace(0, 1, blend_width).reshape(1, -1, 1)

        # Get left and right edges
        left_edge = arr[:, :blend_width].astype(float)
        right_edge = arr[:, -blend_width:].astype(float)

        # Blend: left side gets gradual transition from right
        blended_left = (right_edge * (1 - blend_mask) + left_edge * blend_mask)

        # Apply blend to left edge
        result = arr.copy()
        result[:, :blend_width] = blended_left.astype(np.uint8)

        return Image.fromarray(result)

    def _quantize_to_platform(self, image: Image.Image) -> Image.Image:
        """Quantize image to platform color limits."""

        # For NES, use 4 colors per palette, max 4 palettes = 16 colors
        # For Genesis/SNES, more colors available
        total_colors = self.platform.colors_per_palette * self.platform.max_palettes

        # Quantize
        quantized = image.quantize(colors=total_colors, method=Image.MEDIANCUT)

        # Convert back to RGB for processing
        return quantized.convert('RGB')

    def _reduce_tiles(
        self,
        image: Image.Image,
        current_optimized: TileOptimizationResult,
        max_tiles: int,
    ) -> Image.Image:
        """
        Reduce tile count by simplifying image.

        Strategies:
        1. Slight blur to merge similar tiles
        2. Color reduction
        3. Pattern simplification
        """
        reduction_needed = current_optimized.unique_count - max_tiles

        # Strategy 1: Light blur
        if reduction_needed > 0:
            # Very light blur to merge near-identical tiles
            blurred = image.filter(ImageFilter.GaussianBlur(radius=0.5))

            # Re-quantize
            blurred = self._quantize_to_platform(blurred)

            # Check if sufficient
            test_opt = self.deduplicator.optimize(blurred)
            if test_opt.unique_count <= max_tiles:
                return blurred

            image = blurred
            reduction_needed = test_opt.unique_count - max_tiles

        # Strategy 2: Reduce colors further
        if reduction_needed > 0:
            reduced_colors = max(4, self.platform.colors_per_palette * 2)
            quantized = image.quantize(colors=reduced_colors, method=Image.MEDIANCUT)
            image = quantized.convert('RGB')

        return image

    # -------------------------------------------------------------------------
    # Palette and Collision
    # -------------------------------------------------------------------------

    def _extract_bg_palette(self, image: Image.Image) -> List[int]:
        """Extract NES-compatible palette from background."""

        # Use AI palette extraction from base class
        return self._extract_palette_ai(
            image,
            num_colors=self.platform.colors_per_palette
        )

    def _generate_collision_map(self, image: Image.Image) -> List[int]:
        """
        Generate collision map from image.

        Uses brightness to determine solid tiles:
        - Dark areas (ground) = solid (1)
        - Light areas (sky) = passable (0)
        """
        # Convert to grayscale
        gray = image.convert('L')
        arr = np.array(gray)

        height, width = arr.shape
        tiles_x = width // self.platform.tile_width
        tiles_y = height // self.platform.tile_height

        collision = []

        # Threshold for "solid" (darker = more likely solid)
        threshold = 100

        for ty in range(tiles_y):
            for tx in range(tiles_x):
                x = tx * self.platform.tile_width
                y = ty * self.platform.tile_height

                tile = arr[y:y + self.platform.tile_height,
                          x:x + self.platform.tile_width]

                # Average brightness
                avg_brightness = np.mean(tile)

                # Dark tiles are solid
                is_solid = 1 if avg_brightness < threshold else 0
                collision.append(is_solid)

        return collision

    # -------------------------------------------------------------------------
    # Output Methods
    # -------------------------------------------------------------------------

    def save_background(
        self,
        bg: ScrollingBackground,
        output_dir: str,
    ) -> Dict[str, str]:
        """
        Save background to files.

        Returns dict of created file paths.
        """
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        created_files = {}

        # Save metadata
        metadata_path = out_path / "metadata.json"
        metadata = {
            'name': bg.name,
            'width_pixels': bg.width_pixels,
            'height_pixels': bg.height_pixels,
            'width_screens': bg.width_screens,
            'is_seamless': bg.is_seamless,
            'tile_count': bg.tile_count,
            'savings_percent': bg.savings_percent,
            'palette': bg.palette,
            'has_collision': bg.collision_map is not None,
            **bg.metadata,
        }
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        created_files['metadata'] = str(metadata_path)

        # Save CHR data
        chr_path = out_path / f"{bg.name}.chr"
        with open(chr_path, 'wb') as f:
            f.write(bg.chr_data)
        created_files['chr'] = str(chr_path)

        # Save tilemap
        tilemap_path = out_path / f"{bg.name}_tilemap.bin"
        with open(tilemap_path, 'wb') as f:
            f.write(bytes(bg.tilemap))
        created_files['tilemap'] = str(tilemap_path)

        # Save collision map if present
        if bg.collision_map:
            collision_path = out_path / f"{bg.name}_collision.bin"
            with open(collision_path, 'wb') as f:
                f.write(bytes(bg.collision_map))
            created_files['collision'] = str(collision_path)

        # Save preview image
        preview_path = out_path / f"{bg.name}_preview.png"
        bg.full_image.save(preview_path)
        created_files['preview'] = str(preview_path)

        # Save assembly include file
        inc_path = out_path / f"{bg.name}.inc"
        self._write_asm_include(bg, inc_path)
        created_files['include'] = str(inc_path)

        return created_files

    def _write_asm_include(self, bg: ScrollingBackground, path: Path) -> None:
        """Write assembly include file for background."""

        tiles_x = bg.width_pixels // self.platform.tile_width
        tiles_y = bg.height_pixels // self.platform.tile_height

        content = f"""; =============================================================================
; {bg.name} - Scrolling Background Data
; Generated by ARDK Background Generator
; =============================================================================

; Dimensions
{bg.name.upper()}_WIDTH_PIXELS = {bg.width_pixels}
{bg.name.upper()}_HEIGHT_PIXELS = {bg.height_pixels}
{bg.name.upper()}_WIDTH_TILES = {tiles_x}
{bg.name.upper()}_HEIGHT_TILES = {tiles_y}
{bg.name.upper()}_WIDTH_SCREENS = {bg.width_screens}

; Tile info
{bg.name.upper()}_UNIQUE_TILES = {bg.tile_count}
{bg.name.upper()}_SEAMLESS = {1 if bg.is_seamless else 0}

; Palette (NES format)
{bg.name.upper()}_PALETTE:
    .byte ${bg.palette[0]:02X}, ${bg.palette[1]:02X}, ${bg.palette[2]:02X}, ${bg.palette[3]:02X}

; External data references
; .incbin "{bg.name}.chr"        ; CHR tile data
; .incbin "{bg.name}_tilemap.bin" ; Tilemap with flip flags
"""

        if bg.collision_map:
            content += f'; .incbin "{bg.name}_collision.bin" ; Collision map\n'

        with open(path, 'w') as f:
            f.write(content)

    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------

    def _sanitize_name(self, description: str) -> str:
        """Convert description to valid filename."""
        # Take first few words
        words = description.lower().split()[:3]
        name = '_'.join(words)
        # Remove non-alphanumeric
        name = ''.join(c if c.isalnum() or c == '_' else '' for c in name)
        return name or 'background'


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    """Command-line interface for background generation."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate scrolling backgrounds for retro platforms'
    )
    parser.add_argument('description', help='Background description')
    parser.add_argument('-o', '--output', required=True, help='Output directory')
    parser.add_argument('--width-screens', type=int, default=2,
                       help='Width in screens (default: 2)')
    parser.add_argument('--seamless', action='store_true', default=True,
                       help='Ensure seamless looping (default: True)')
    parser.add_argument('--no-seamless', action='store_false', dest='seamless',
                       help='Disable seamless looping')
    parser.add_argument('--collision', action='store_true',
                       help='Generate collision map')
    parser.add_argument('--platform', choices=['nes', 'genesis', 'snes', 'gb', 'gameboy'],
                       default='nes', help='Target platform')
    parser.add_argument('--animated', type=str, default=None,
                       choices=list(BACKGROUND_ANIMATION_PRESETS.keys()),
                       help='Generate animated background with specified type')
    parser.add_argument('--frames', type=int, default=None,
                       help='Override animation frame count')
    parser.add_argument('--show-limits', action='store_true',
                       help='Show platform system limits and exit')

    args = parser.parse_args()

    # Get platform config using comprehensive limits system
    platform = get_platform_config(args.platform)

    # Show limits and exit if requested
    if args.show_limits:
        print(f"\n{platform.name} System Limits:")
        print(f"  Tier: {platform.tier}")
        print(f"  Tiles per bank: {platform.max_tiles_per_bank}")
        print(f"  CHR banks: {platform.max_chr_banks}")
        print(f"  Colors per palette: {platform.colors_per_palette}")
        print(f"  Max palettes (BG): {platform.max_palettes}")
        print(f"  Screen: {platform.screen_width}x{platform.screen_height}")
        print(f"  CHR animation: {'Yes' if platform.supports_chr_animation else 'No'}")
        if platform.supports_chr_animation:
            print(f"  Max animation frames: {platform.max_animation_frames}")
            print(f"  Animation banks: {platform.animation_banks_available}")
        print(f"  Parallax layers: {platform.max_parallax_layers}")
        print(f"  Parallax method: {platform.parallax_method}")
        return

    # Create generator
    generator = BackgroundGenerator(platform=platform)

    print(f"Generating background: {args.description}")
    print(f"Platform: {platform.name} (Tier: {platform.tier})")
    print(f"Width: {args.width_screens} screens ({args.width_screens * platform.screen_width}px)")
    print(f"Seamless: {args.seamless}")

    # Generate animated or static
    if args.animated:
        print(f"Animation type: {args.animated}")
        bg = generator.generate_animated_bg(
            args.description,
            animation_type=args.animated,
            width_screens=args.width_screens,
            frame_count=args.frames,
        )
        files = generator.save_animated_background(bg, args.output)

        print(f"\nGeneration complete!")
        print(f"Frames: {bg.frame_count}")
        print(f"Max tiles per frame: {bg.max_tiles_used}")
        print(f"Total CHR size: {bg.total_chr_size} bytes")
    else:
        # Static background
        if args.collision:
            bg = generator.generate_with_collision(
                args.description,
                width_screens=args.width_screens,
                seamless=args.seamless,
            )
        else:
            bg = generator.generate_scrolling_bg(
                args.description,
                width_screens=args.width_screens,
                seamless=args.seamless,
            )

        files = generator.save_background(bg, args.output)

        print(f"\nGeneration complete!")
        print(f"Unique tiles: {bg.tile_count} (saved {bg.savings_percent:.1f}%)")

    print(f"\nCreated files:")
    for name, path in files.items():
        print(f"  {name}: {path}")

    if bg.warnings:
        print(f"\nWarnings:")
        for w in bg.warnings:
            print(f"  - {w}")


if __name__ == '__main__':
    main()
