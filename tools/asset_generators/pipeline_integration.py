"""
Pipeline Integration - Unified workflow for asset generation and sprite production.

This module bridges the AI-powered generation pipeline with the sprite processing
pipeline, ensuring consistent output that works together for game development.

Workflow:
1. Generate → AI creates raw assets (characters, backgrounds, parallax)
2. Process → unified_pipeline processes for platform (palette, tiles, format)
3. Optimize → Tile deduplication, flip detection, symmetry analysis
4. Export → Platform-ready CHR, tilemaps, includes

Features:
- Consistent palette management across sprites and backgrounds
- Shared tile optimization for memory efficiency
- Animation frame generation for both sprites and tiles
- HAL-compatible output for engine integration
"""

import os
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
from enum import Enum

try:
    from PIL import Image
    import numpy as np
except ImportError:
    raise ImportError("PIL and numpy required: pip install pillow numpy")

from .base_generator import (
    PlatformConfig, GenerationFlags, GeneratedAsset,
    PollinationsClient, get_platform_config, validate_asset_for_platform,
)
from .character_generator import CharacterGenerator, CharacterSheet
from .background_generator import (
    BackgroundGenerator, ScrollingBackground, AnimatedBackground,
    BACKGROUND_ANIMATION_PRESETS
)
from .parallax_generator import ParallaxGenerator, ParallaxSet
from .animated_tile_generator import AnimatedTileGenerator, AnimatedTile, AnimatedTileset
from .cross_gen_converter import (
    CrossGenConverter, ConversionResult, TierGenerationResult,
    ConversionMode, GenerationTier,
)

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from tile_optimizers.tile_deduplicator import TileDeduplicator, TileOptimizationResult
from tile_optimizers.symmetry_detector import SymmetryDetector


# =============================================================================
# Enums
# =============================================================================

class AssetType(Enum):
    """Types of assets in the pipeline."""
    CHARACTER = "character"
    BACKGROUND = "background"
    ANIMATED_BACKGROUND = "animated_background"  # Multi-frame animated BG
    PARALLAX = "parallax"
    ANIMATED_TILE = "animated_tile"
    TILESET = "tileset"
    SPRITE_SHEET = "sprite_sheet"


class PipelineStage(Enum):
    """Stages in the asset pipeline."""
    GENERATE = "generate"      # AI generation
    PROCESS = "process"        # Platform conversion
    OPTIMIZE = "optimize"      # Tile optimization
    EXPORT = "export"          # Final output


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class PipelineConfig:
    """Configuration for the integrated pipeline."""

    # Platform
    platform: str = "nes"

    # Generation settings
    use_ai_generation: bool = True
    ai_model_policy: str = "best_for_task"

    # Processing settings
    target_sprite_size: int = 32
    force_palette: Optional[List[int]] = None
    filter_text_labels: bool = True

    # Optimization settings
    enable_flip_optimization: bool = True
    enable_tile_deduplication: bool = True
    enable_symmetry_detection: bool = True

    # Output settings
    generate_includes: bool = True
    generate_previews: bool = True
    generate_hal_config: bool = True

    # Animation settings
    default_animation_set: str = "standard"
    background_animation_frames: int = 4

    # Validation
    validate_tile_limits: bool = True
    warn_on_oversized: bool = True


@dataclass
class PipelineResult:
    """Result from running the pipeline on an asset."""

    asset_type: AssetType
    name: str
    success: bool

    # Generated files
    files: Dict[str, str] = field(default_factory=dict)

    # Statistics
    stats: Dict[str, Any] = field(default_factory=dict)

    # Warnings and errors
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    # References to generated assets
    character_sheet: Optional[CharacterSheet] = None
    background: Optional[ScrollingBackground] = None
    animated_background: Optional[AnimatedBackground] = None
    parallax_set: Optional[ParallaxSet] = None
    animated_tiles: Optional[List[AnimatedTile]] = None


@dataclass
class ProjectManifest:
    """Manifest for a complete project's assets."""

    project_name: str
    platform: str
    created: str

    # Asset lists
    characters: List[Dict] = field(default_factory=list)
    backgrounds: List[Dict] = field(default_factory=list)
    animated_backgrounds: List[Dict] = field(default_factory=list)
    parallax_sets: List[Dict] = field(default_factory=list)
    animated_tiles: List[Dict] = field(default_factory=list)

    # Resource budgets
    chr_usage: Dict[str, int] = field(default_factory=dict)
    palette_usage: Dict[str, List[int]] = field(default_factory=dict)

    # Total statistics
    total_unique_tiles: int = 0
    total_chr_bytes: int = 0


# =============================================================================
# Integrated Pipeline
# =============================================================================

class IntegratedPipeline:
    """
    Unified pipeline for AI generation and sprite processing.

    Bridges the generation pipeline (Pollinations AI) with the processing
    pipeline (unified_pipeline.py) for a complete asset workflow.
    """

    def __init__(
        self,
        config: Optional[PipelineConfig] = None,
        api_key: Optional[str] = None,
    ):
        """Initialize the integrated pipeline."""
        self.config = config or PipelineConfig()
        self.api_key = api_key

        # Get platform configuration using comprehensive system limits
        self.platform = get_platform_config(self.config.platform)

        # Initialize generators
        self.character_gen = CharacterGenerator(self.platform, api_key)
        self.background_gen = BackgroundGenerator(self.platform, api_key)
        self.parallax_gen = ParallaxGenerator(self.platform, api_key)
        self.animated_tile_gen = AnimatedTileGenerator(self.platform, api_key)

        # Initialize cross-generation converter
        self.converter = CrossGenConverter(api_key)

        # Initialize optimizers
        self.deduplicator = TileDeduplicator(
            tile_width=self.platform.tile_width,
            tile_height=self.platform.tile_height,
            enable_h_flip=self.config.enable_flip_optimization,
            enable_v_flip=self.config.enable_flip_optimization,
        )
        self.symmetry_detector = SymmetryDetector(
            tile_width=self.platform.tile_width,
            tile_height=self.platform.tile_height,
        )

        # Set generation flags
        self._setup_generation_flags()

        # Project tracking
        self.manifest = ProjectManifest(
            project_name="",
            platform=self.config.platform,
            created="",
        )

    def _setup_generation_flags(self) -> None:
        """Configure generation flags for all generators."""
        flags = GenerationFlags(
            use_h_flip=self.config.enable_flip_optimization,
            use_v_flip=self.config.enable_flip_optimization,
            detect_symmetry=self.config.enable_symmetry_detection,
            deduplicate_tiles=self.config.enable_tile_deduplication,
            animation_set=self.config.default_animation_set,
        )

        self.character_gen.set_flags(flags)
        self.background_gen.set_flags(flags)

    # -------------------------------------------------------------------------
    # Main Pipeline Methods
    # -------------------------------------------------------------------------

    def generate_character(
        self,
        description: str,
        output_dir: str,
        animation_set: str = "standard",
        sprite_size: int = 32,
    ) -> PipelineResult:
        """
        Generate a complete character with animations.

        Args:
            description: Character description for AI
            output_dir: Where to save output
            animation_set: minimal, standard, or full
            sprite_size: Sprite dimensions

        Returns:
            PipelineResult with generated files and stats
        """
        result = PipelineResult(
            asset_type=AssetType.CHARACTER,
            name=self._sanitize_name(description),
            success=False,
        )

        try:
            # Stage 1: Generate
            print(f"[GENERATE] Creating character: {description}")
            sheet = self.character_gen.generate(
                description=description,
                animation_set=animation_set,
                sprite_width=sprite_size,
                sprite_height=sprite_size,
            )

            # Stage 2: Process (already done in generator)

            # Stage 3: Optimize
            print(f"[OPTIMIZE] Analyzing tiles...")
            result.stats['animations'] = len(sheet.animations)
            result.stats['total_frames'] = sum(a.frame_count for a in sheet.animations)

            # Stage 4: Export
            print(f"[EXPORT] Saving to {output_dir}")
            files = self.character_gen.save_character(sheet, output_dir)
            result.files = files

            result.character_sheet = sheet
            result.warnings = sheet.warnings
            result.success = True

            # Update manifest
            self._update_manifest_character(sheet, output_dir)

        except Exception as e:
            result.errors.append(str(e))

        return result

    def generate_background(
        self,
        description: str,
        output_dir: str,
        width_screens: int = 2,
        seamless: bool = True,
        with_collision: bool = False,
    ) -> PipelineResult:
        """
        Generate a scrolling background.

        Args:
            description: Scene description
            output_dir: Where to save output
            width_screens: Width in screens
            seamless: Ensure seamless looping
            with_collision: Generate collision map

        Returns:
            PipelineResult with generated files and stats
        """
        result = PipelineResult(
            asset_type=AssetType.BACKGROUND,
            name=self._sanitize_name(description),
            success=False,
        )

        try:
            # Stage 1: Generate
            print(f"[GENERATE] Creating background: {description}")
            if with_collision:
                bg = self.background_gen.generate_with_collision(
                    description, width_screens, seamless
                )
            else:
                bg = self.background_gen.generate_scrolling_bg(
                    description, width_screens, seamless
                )

            # Stage 2-3: Process and Optimize (done in generator)
            result.stats['width_pixels'] = bg.width_pixels
            result.stats['height_pixels'] = bg.height_pixels
            result.stats['unique_tiles'] = bg.tile_count
            result.stats['savings_percent'] = bg.savings_percent

            # Stage 4: Export
            print(f"[EXPORT] Saving to {output_dir}")
            files = self.background_gen.save_background(bg, output_dir)
            result.files = files

            result.background = bg
            result.warnings = bg.warnings
            result.success = True

            # Update manifest
            self._update_manifest_background(bg, output_dir)

        except Exception as e:
            result.errors.append(str(e))

        return result

    def generate_parallax(
        self,
        description: str,
        output_dir: str,
        preset: str = "standard_3layer",
        width_screens: int = 2,
    ) -> PipelineResult:
        """
        Generate a multi-layer parallax background.

        Args:
            description: Scene description
            output_dir: Where to save output
            preset: Parallax layer preset
            width_screens: Base width in screens

        Returns:
            PipelineResult with generated files and stats
        """
        result = PipelineResult(
            asset_type=AssetType.PARALLAX,
            name=self._sanitize_name(description),
            success=False,
        )

        try:
            # Stage 1: Generate
            print(f"[GENERATE] Creating parallax: {description}")
            parallax = self.parallax_gen.generate_parallax_set(
                description, preset, width_screens
            )

            # Stats
            result.stats['layer_count'] = parallax.layer_count
            result.stats['total_chr_size'] = parallax.total_chr_size
            result.stats['layers'] = [
                {'name': l.name, 'tiles': l.tile_count, 'speed': l.scroll_speed}
                for l in parallax.layers
            ]

            # Stage 4: Export
            print(f"[EXPORT] Saving to {output_dir}")
            files = self.parallax_gen.save_parallax_set(parallax, output_dir)
            result.files = files

            result.parallax_set = parallax
            result.warnings = parallax.warnings
            result.success = True

            # Update manifest
            self._update_manifest_parallax(parallax, output_dir)

        except Exception as e:
            result.errors.append(str(e))

        return result

    def generate_animated_background(
        self,
        description: str,
        output_dir: str,
        animation_type: str = "water",
        width_screens: int = 1,
        frame_count: Optional[int] = None,
        speed_ms: Optional[int] = None,
    ) -> PipelineResult:
        """
        Generate an animated background with multiple CHR bank frames.

        Each frame is a complete background that fits within platform tile limits.
        Designed for CHR bank swapping animation (NES MMC3, etc.).

        Args:
            description: Background scene description
            output_dir: Where to save output
            animation_type: Type of animation (water, lava, neon, fire, etc.)
            width_screens: Width in screens (usually 1 for animated BGs)
            frame_count: Override frame count from preset
            speed_ms: Override animation speed from preset

        Returns:
            PipelineResult with generated files and stats
        """
        result = PipelineResult(
            asset_type=AssetType.ANIMATED_BACKGROUND,
            name=self._sanitize_name(description),
            success=False,
        )

        try:
            # Stage 1: Generate
            print(f"[GENERATE] Creating animated background: {description}")
            print(f"  Animation type: {animation_type}")

            animated_bg = self.background_gen.generate_animated_bg(
                description=description,
                animation_type=animation_type,
                width_screens=width_screens,
                frame_count=frame_count,
                speed_ms=speed_ms,
            )

            # Stats
            result.stats['frame_count'] = animated_bg.frame_count
            result.stats['animation_type'] = animated_bg.animation_type
            result.stats['speed_ms'] = animated_bg.speed_ms
            result.stats['tiles_per_frame'] = animated_bg.tiles_per_frame
            result.stats['max_tiles_used'] = animated_bg.max_tiles_used
            result.stats['bank_utilization'] = animated_bg.bank_utilization
            result.stats['total_chr_size'] = animated_bg.total_chr_size

            # Stage 4: Export
            print(f"[EXPORT] Saving to {output_dir}")
            files = self.background_gen.save_animated_background(
                animated_bg, output_dir
            )
            result.files = files

            result.animated_background = animated_bg
            result.warnings = animated_bg.warnings
            result.success = True

            # Update manifest
            self._update_manifest_animated_background(animated_bg, output_dir)

        except Exception as e:
            result.errors.append(str(e))

        return result

    def generate_animated_tiles(
        self,
        tile_definitions: List[Dict],
        output_dir: str,
        base_description: str = "",
    ) -> PipelineResult:
        """
        Generate animated background tiles.

        Args:
            tile_definitions: List of tile specs with name, preset, description
            output_dir: Where to save output
            base_description: Base scene description for consistency

        Returns:
            PipelineResult with generated files and stats
        """
        result = PipelineResult(
            asset_type=AssetType.ANIMATED_TILE,
            name=self._sanitize_name(base_description or "tiles"),
            success=False,
        )

        try:
            # Generate tileset
            print(f"[GENERATE] Creating {len(tile_definitions)} animated tiles")
            tileset = self.animated_tile_gen.generate_animated_tileset(
                tile_definitions, base_description
            )

            result.stats['tile_count'] = len(tileset.animated_tiles)
            result.stats['frame_count'] = tileset.frame_count

            # Export
            print(f"[EXPORT] Saving to {output_dir}")
            files = self.animated_tile_gen.save_animated_tileset(tileset, output_dir)
            result.files = files

            result.animated_tiles = tileset.animated_tiles
            result.warnings = tileset.warnings
            result.success = True

        except Exception as e:
            result.errors.append(str(e))

        return result

    # -------------------------------------------------------------------------
    # Cross-Generation Conversion
    # -------------------------------------------------------------------------

    def convert_asset(
        self,
        image_path: str,
        output_dir: str,
        source_platform: str,
        target_platform: str,
        description: str = "",
    ) -> ConversionResult:
        """
        Convert an existing asset from one platform to another.

        Uses AI to intelligently upscale, downscale, or adapt the asset
        based on source and target platform capabilities.

        Args:
            image_path: Path to source image
            output_dir: Output directory
            source_platform: Source platform (nes, genesis, etc.)
            target_platform: Target platform
            description: Optional description for AI context

        Returns:
            ConversionResult with converted image
        """
        from PIL import Image as PILImage

        image = PILImage.open(image_path)
        result = self.converter.convert(
            image=image,
            source_platform=source_platform,
            target_platform=target_platform,
            description=description,
        )

        if result.success:
            name = Path(image_path).stem
            self.converter.save_conversion_result(result, output_dir, name)

        return result

    def upscale_to_16bit(
        self,
        image_path: str,
        output_dir: str,
        source_platform: str = "nes",
        target_platform: str = "genesis",
        description: str = "",
        scale_factor: int = 2,
    ) -> ConversionResult:
        """
        Upscale an 8-bit asset to 16-bit quality.

        AI adds detail, expands color palette, and increases resolution
        while maintaining the original design's character.

        Args:
            image_path: Path to source 8-bit image
            output_dir: Output directory
            source_platform: Source 8-bit platform
            target_platform: Target 16-bit platform
            description: Asset description for AI context
            scale_factor: Resolution multiplier (1, 2, or 4)

        Returns:
            ConversionResult with upscaled image
        """
        from PIL import Image as PILImage

        image = PILImage.open(image_path)
        result = self.converter.upscale_to_16bit(
            image=image,
            source_platform=source_platform,
            target_platform=target_platform,
            description=description,
            scale_factor=scale_factor,
        )

        if result.success:
            name = Path(image_path).stem
            self.converter.save_conversion_result(result, output_dir, name)

        return result

    def downscale_to_8bit(
        self,
        image_path: str,
        output_dir: str,
        source_platform: str = "genesis",
        target_platform: str = "nes",
        description: str = "",
    ) -> ConversionResult:
        """
        Downscale a 16-bit asset to 8-bit quality.

        AI intelligently reduces colors and detail while preserving
        the essential character of the original design.

        Args:
            image_path: Path to source 16-bit image
            output_dir: Output directory
            source_platform: Source 16-bit platform
            target_platform: Target 8-bit platform
            description: Asset description for AI context

        Returns:
            ConversionResult with downscaled image
        """
        from PIL import Image as PILImage

        image = PILImage.open(image_path)
        result = self.converter.downscale_to_8bit(
            image=image,
            source_platform=source_platform,
            target_platform=target_platform,
            description=description,
        )

        if result.success:
            name = Path(image_path).stem
            self.converter.save_conversion_result(result, output_dir, name)

        return result

    def generate_multi_platform(
        self,
        description: str,
        output_dir: str,
        platforms: List[str],
        asset_type: str = "sprite",
        size: Optional[Tuple[int, int]] = None,
    ) -> TierGenerationResult:
        """
        Generate asset at best tier for multi-platform deployment.

        Creates a master asset at the highest tier among targets,
        then generates optimized variants for each platform.

        Args:
            description: Asset description
            output_dir: Output directory
            platforms: List of target platforms
            asset_type: Type of asset (sprite, background, tile)
            size: Optional override for dimensions

        Returns:
            TierGenerationResult with master and all variants
        """
        # Determine highest tier among targets
        from configs.platform_limits import PlatformTier

        highest_tier = PlatformTier.MINIMAL
        for platform in platforms:
            config = get_platform_config(platform)
            tier_name = config.tier
            tier = getattr(PlatformTier, tier_name, PlatformTier.MINIMAL)
            if tier.value > highest_tier.value:
                highest_tier = tier

        # Map to generation tier
        gen_tier = {
            PlatformTier.MINIMAL: GenerationTier.TIER_8BIT,
            PlatformTier.MINIMAL_PLUS: GenerationTier.TIER_8BIT,
            PlatformTier.STANDARD: GenerationTier.TIER_16BIT,
            PlatformTier.STANDARD_PLUS: GenerationTier.TIER_16BIT,
            PlatformTier.EXTENDED: GenerationTier.TIER_32BIT,
        }.get(highest_tier, GenerationTier.TIER_16BIT)

        result = self.converter.generate_for_tier(
            description=description,
            tier=gen_tier,
            asset_type=asset_type,
            size=size,
            target_platforms=platforms,
        )

        # Save results
        self.converter.save_tier_result(result, output_dir, "asset")

        return result

    # -------------------------------------------------------------------------
    # Batch Processing
    # -------------------------------------------------------------------------

    def process_asset_list(
        self,
        asset_list: List[Dict],
        base_output_dir: str,
    ) -> List[PipelineResult]:
        """
        Process a list of asset definitions.

        Each asset dict should have:
        - type: character, background, parallax, animated_tile
        - description: Text description
        - name: Output folder name
        - Additional type-specific options

        Args:
            asset_list: List of asset definitions
            base_output_dir: Base output directory

        Returns:
            List of PipelineResult for each asset
        """
        results = []

        for asset_def in asset_list:
            asset_type = asset_def.get('type', 'character')
            description = asset_def.get('description', '')
            name = asset_def.get('name', self._sanitize_name(description))
            output_dir = str(Path(base_output_dir) / name)

            print(f"\n{'='*60}")
            print(f"Processing: {name} ({asset_type})")
            print(f"{'='*60}")

            if asset_type == 'character':
                result = self.generate_character(
                    description=description,
                    output_dir=output_dir,
                    animation_set=asset_def.get('animation_set', 'standard'),
                    sprite_size=asset_def.get('sprite_size', 32),
                )
            elif asset_type == 'background':
                result = self.generate_background(
                    description=description,
                    output_dir=output_dir,
                    width_screens=asset_def.get('width_screens', 2),
                    seamless=asset_def.get('seamless', True),
                    with_collision=asset_def.get('collision', False),
                )
            elif asset_type == 'parallax':
                result = self.generate_parallax(
                    description=description,
                    output_dir=output_dir,
                    preset=asset_def.get('preset', 'standard_3layer'),
                    width_screens=asset_def.get('width_screens', 2),
                )
            elif asset_type == 'animated_tile':
                result = self.generate_animated_tiles(
                    tile_definitions=asset_def.get('tiles', []),
                    output_dir=output_dir,
                    base_description=description,
                )
            elif asset_type == 'animated_background':
                result = self.generate_animated_background(
                    description=description,
                    output_dir=output_dir,
                    animation_type=asset_def.get('animation_type', 'water'),
                    width_screens=asset_def.get('width_screens', 1),
                    frame_count=asset_def.get('frame_count'),
                    speed_ms=asset_def.get('speed_ms'),
                )
            else:
                result = PipelineResult(
                    asset_type=AssetType.CHARACTER,
                    name=name,
                    success=False,
                    errors=[f"Unknown asset type: {asset_type}"],
                )

            results.append(result)

            if result.success:
                print(f"[SUCCESS] {name}")
            else:
                print(f"[FAILED] {name}: {result.errors}")

        return results

    # -------------------------------------------------------------------------
    # Manifest Management
    # -------------------------------------------------------------------------

    def _update_manifest_character(
        self,
        sheet: CharacterSheet,
        output_dir: str,
    ) -> None:
        """Update manifest with character info."""
        self.manifest.characters.append({
            'name': sheet.name,
            'animations': [a.name for a in sheet.animations],
            'output_dir': output_dir,
        })

    def _update_manifest_background(
        self,
        bg: ScrollingBackground,
        output_dir: str,
    ) -> None:
        """Update manifest with background info."""
        self.manifest.backgrounds.append({
            'name': bg.name,
            'width_screens': bg.width_screens,
            'unique_tiles': bg.tile_count,
            'output_dir': output_dir,
        })
        self.manifest.total_unique_tiles += bg.tile_count
        self.manifest.total_chr_bytes += len(bg.chr_data)

    def _update_manifest_parallax(
        self,
        parallax: ParallaxSet,
        output_dir: str,
    ) -> None:
        """Update manifest with parallax info."""
        self.manifest.parallax_sets.append({
            'name': parallax.name,
            'layers': [l.name for l in parallax.layers],
            'output_dir': output_dir,
        })
        self.manifest.total_chr_bytes += parallax.total_chr_size

    def _update_manifest_animated_background(
        self,
        bg: AnimatedBackground,
        output_dir: str,
    ) -> None:
        """Update manifest with animated background info."""
        self.manifest.animated_backgrounds.append({
            'name': bg.name,
            'animation_type': bg.animation_type,
            'frame_count': bg.frame_count,
            'speed_ms': bg.speed_ms,
            'tiles_per_frame': bg.tiles_per_frame,
            'max_tiles_used': bg.max_tiles_used,
            'output_dir': output_dir,
        })
        # Count max tiles used (each frame uses same slot, not additive)
        self.manifest.total_unique_tiles += bg.max_tiles_used
        self.manifest.total_chr_bytes += bg.total_chr_size

    def save_manifest(self, output_path: str) -> None:
        """Save project manifest."""
        from datetime import datetime
        self.manifest.created = datetime.now().isoformat()

        manifest_dict = {
            'project_name': self.manifest.project_name,
            'platform': self.manifest.platform,
            'created': self.manifest.created,
            'characters': self.manifest.characters,
            'backgrounds': self.manifest.backgrounds,
            'animated_backgrounds': self.manifest.animated_backgrounds,
            'parallax_sets': self.manifest.parallax_sets,
            'animated_tiles': self.manifest.animated_tiles,
            'totals': {
                'unique_tiles': self.manifest.total_unique_tiles,
                'chr_bytes': self.manifest.total_chr_bytes,
            },
        }

        with open(output_path, 'w') as f:
            json.dump(manifest_dict, f, indent=2)

    # -------------------------------------------------------------------------
    # Analysis and Validation
    # -------------------------------------------------------------------------

    def analyze_project_resources(self) -> Dict[str, Any]:
        """
        Analyze total resource usage for the project.

        Uses comprehensive platform system limits for accurate validation.
        """
        # Calculate limits from platform config (uses full system limits)
        max_tiles = self.platform.max_tiles_per_bank * self.platform.max_chr_banks
        bytes_per_tile = 16 if self.platform.bits_per_pixel == 2 else 32
        max_chr = max_tiles * bytes_per_tile

        # Calculate usage percentages safely
        tile_usage_pct = (self.manifest.total_unique_tiles / max_tiles * 100) if max_tiles > 0 else 0
        chr_usage_pct = (self.manifest.total_chr_bytes / max_chr * 100) if max_chr > 0 else 0

        analysis = {
            'platform': self.platform.name,
            'tier': self.platform.tier,
            'limits': {
                'max_tiles': max_tiles,
                'max_tiles_per_bank': self.platform.max_tiles_per_bank,
                'max_chr_banks': self.platform.max_chr_banks,
                'max_chr_bytes': max_chr,
                'max_sprites': self.platform.max_sprites,
                'colors_per_palette': self.platform.colors_per_palette,
                'max_palettes': self.platform.max_palettes,
                'animation_frames': self.platform.max_animation_frames,
                'supports_chr_animation': self.platform.supports_chr_animation,
            },
            'usage': {
                'unique_tiles': self.manifest.total_unique_tiles,
                'chr_bytes': self.manifest.total_chr_bytes,
                'tile_usage_percent': tile_usage_pct,
                'chr_usage_percent': chr_usage_pct,
            },
            'assets': {
                'characters': len(self.manifest.characters),
                'backgrounds': len(self.manifest.backgrounds),
                'animated_backgrounds': len(self.manifest.animated_backgrounds),
                'parallax_sets': len(self.manifest.parallax_sets),
            },
            'warnings': [],
        }

        # Validate using full platform limits
        validation = validate_asset_for_platform(
            self.platform.name.lower(),
            tile_count=self.manifest.total_unique_tiles,
            colors_used=self.platform.colors_per_palette * self.platform.max_palettes,
            sprite_count=0,
        )
        analysis['warnings'].extend(validation.get('warnings', []))
        analysis['warnings'].extend(validation.get('errors', []))

        # Additional proximity warnings
        if tile_usage_pct > 90:
            analysis['warnings'].append(
                f"Tile usage ({tile_usage_pct:.1f}%) approaching {self.platform.name} limit!"
            )
        if chr_usage_pct > 90:
            analysis['warnings'].append(
                f"CHR usage ({chr_usage_pct:.1f}%) approaching {self.platform.name} limit!"
            )

        # Check animation compatibility
        if self.manifest.animated_backgrounds and not self.platform.supports_chr_animation:
            analysis['warnings'].append(
                f"{self.platform.name} does not support CHR bank animation - animated backgrounds may not work"
            )

        return analysis

    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------

    def _sanitize_name(self, description: str) -> str:
        """Convert description to valid folder name."""
        words = description.lower().split()[:3]
        name = '_'.join(words)
        name = ''.join(c if c.isalnum() or c == '_' else '' for c in name)
        return name or 'asset'


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    """Command-line interface for integrated pipeline."""
    import argparse

    parser = argparse.ArgumentParser(
        description='ARDK Integrated Asset Pipeline'
    )
    parser.add_argument('asset_file', nargs='?', help='JSON file with asset definitions')
    parser.add_argument('-o', '--output', help='Output directory')
    parser.add_argument('--platform', choices=['nes', 'genesis', 'snes', 'gb', 'gameboy'],
                       default='nes', help='Target platform')
    parser.add_argument('--project-name', default='game', help='Project name')
    parser.add_argument('--show-limits', action='store_true',
                       help='Show platform system limits and exit')

    args = parser.parse_args()

    # Get platform config for limits display
    platform = get_platform_config(args.platform)

    # Show limits and exit if requested
    if args.show_limits:
        print(f"\n{platform.name} System Limits (Tier: {platform.tier})")
        print(f"{'='*50}")
        print(f"\nTiles:")
        print(f"  Per bank: {platform.max_tiles_per_bank}")
        print(f"  Total banks: {platform.max_chr_banks}")
        print(f"  Bits per pixel: {platform.bits_per_pixel}")
        print(f"\nPalettes:")
        print(f"  Colors per palette: {platform.colors_per_palette}")
        print(f"  BG palettes: {platform.max_palettes}")
        print(f"  Sprite palettes: {platform.max_palettes_sprite}")
        print(f"\nSprites:")
        print(f"  Max on screen: {platform.max_sprites}")
        print(f"  Per scanline: {platform.max_sprites_per_scanline}")
        print(f"  Sizes: {platform.sprite_sizes}")
        print(f"\nScreen:")
        print(f"  Resolution: {platform.screen_width}x{platform.screen_height}")
        print(f"  Visible: {platform.screen_width}x{platform.visible_height}")
        print(f"\nAnimation:")
        print(f"  CHR animation: {'Yes' if platform.supports_chr_animation else 'No'}")
        if platform.supports_chr_animation:
            print(f"  Max frames: {platform.max_animation_frames}")
            print(f"  Banks available: {platform.animation_banks_available}")
        print(f"\nParallax:")
        print(f"  Layers: {platform.max_parallax_layers}")
        print(f"  Method: {platform.parallax_method}")
        print(f"\nRecommended animation frames:")
        for anim, frames in platform.recommended_frames.items():
            print(f"  {anim}: {frames}")
        return

    # Validate required arguments for processing
    if not args.asset_file:
        parser.error("asset_file is required unless using --show-limits")
    if not args.output:
        parser.error("-o/--output is required unless using --show-limits")

    # Load asset definitions
    with open(args.asset_file, 'r') as f:
        asset_list = json.load(f)

    # Configure pipeline
    config = PipelineConfig(platform=args.platform)
    pipeline = IntegratedPipeline(config)
    pipeline.manifest.project_name = args.project_name

    # Process all assets
    print(f"ARDK Integrated Pipeline")
    print(f"========================")
    print(f"Platform: {platform.name} (Tier: {platform.tier})")
    print(f"Assets: {len(asset_list)}")
    print()

    results = pipeline.process_asset_list(asset_list, args.output)

    # Summary
    print(f"\n{'='*60}")
    print("Summary")
    print(f"{'='*60}")

    success_count = sum(1 for r in results if r.success)
    print(f"Processed: {len(results)}")
    print(f"Success: {success_count}")
    print(f"Failed: {len(results) - success_count}")

    # Save manifest
    manifest_path = str(Path(args.output) / "manifest.json")
    pipeline.save_manifest(manifest_path)
    print(f"\nManifest saved to: {manifest_path}")

    # Resource analysis
    analysis = pipeline.analyze_project_resources()
    print(f"\nResource Usage:")
    print(f"  Tiles: {analysis['usage']['unique_tiles']} / {analysis['limits']['max_tiles']} "
          f"({analysis['usage']['tile_usage_percent']:.1f}%)")
    print(f"  CHR: {analysis['usage']['chr_bytes']} / {analysis['limits']['max_chr_bytes']} bytes "
          f"({analysis['usage']['chr_usage_percent']:.1f}%)")

    if analysis['warnings']:
        print("\nWarnings:")
        for w in analysis['warnings']:
            print(f"  - {w}")


if __name__ == '__main__':
    main()
