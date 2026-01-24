"""
Cross-Generation Asset Converter - AI-powered asset conversion between platforms.

Enables:
- Upsampling: NES → Genesis/SNES (add detail, colors, resolution)
- Downsampling: Genesis → NES (reduce colors, simplify detail)
- Tier-aware generation: Generate at "best of tier" for multi-platform deployment
- Smart style transfer: Maintain visual identity across hardware generations

Conversion Strategies:
1. UPSCALE: Increase resolution and add detail (8-bit → 16-bit)
2. DOWNSCALE: Reduce resolution and colors (16-bit → 8-bit)
3. ADAPT: Keep resolution, adjust colors/style for target platform
4. GENERATE_TIER: Create new asset at tier level for multi-platform use
"""

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
from enum import Enum
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('CrossGenConverter')

try:
    from PIL import Image, ImageFilter, ImageEnhance
    import numpy as np
except ImportError:
    raise ImportError("PIL and numpy required: pip install pillow numpy")

from .base_generator import (
    PlatformConfig, PollinationsClient, get_platform_config,
    get_platform_limits, validate_asset_for_platform,
    platform_config_from_limits, MODEL_MAP,
)

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from configs.platform_limits import (
    PlatformLimits, PlatformTier, NES_LIMITS, GENESIS_LIMITS,
    SNES_LIMITS, GAMEBOY_LIMITS,
)

# Import tile optimizer for deduplication with H/V flip
sys.path.insert(0, str(Path(__file__).parent.parent))
from tile_optimizers.tile_deduplicator import (
    TileDeduplicator, TileOptimizationResult, TileFlags, TileRef,
)


# =============================================================================
# Enums and Constants
# =============================================================================

class ConversionMode(Enum):
    """Conversion operation modes."""
    UPSCALE = "upscale"          # Add detail and colors (8-bit → 16-bit)
    DOWNSCALE = "downscale"      # Reduce detail and colors (16-bit → 8-bit)
    ADAPT = "adapt"              # Same resolution, different palette/style
    REGENERATE = "regenerate"    # AI regenerates in target style


class GenerationTier(Enum):
    """Generation quality tiers for multi-platform assets."""
    TIER_8BIT = "8bit"           # NES, GB, C64 quality
    TIER_16BIT = "16bit"         # Genesis, SNES quality
    TIER_32BIT = "32bit"         # GBA, DS quality
    TIER_BEST = "best"           # Highest quality for downsampling


# Platform tier mapping
TIER_PLATFORMS = {
    GenerationTier.TIER_8BIT: ['nes', 'gb', 'gbc', 'sms', 'c64'],
    GenerationTier.TIER_16BIT: ['genesis', 'snes', 'pce', 'neogeo'],
    GenerationTier.TIER_32BIT: ['gba', 'nds', 'psp'],
}

# Conversion capability matrix
CONVERSION_PATHS = {
    # (source_tier, target_tier): ConversionMode
    (PlatformTier.MINIMAL, PlatformTier.STANDARD): ConversionMode.UPSCALE,
    (PlatformTier.MINIMAL, PlatformTier.EXTENDED): ConversionMode.UPSCALE,
    (PlatformTier.STANDARD, PlatformTier.MINIMAL): ConversionMode.DOWNSCALE,
    (PlatformTier.STANDARD, PlatformTier.EXTENDED): ConversionMode.UPSCALE,
    (PlatformTier.EXTENDED, PlatformTier.MINIMAL): ConversionMode.DOWNSCALE,
    (PlatformTier.EXTENDED, PlatformTier.STANDARD): ConversionMode.DOWNSCALE,
    # Same tier = adapt
    (PlatformTier.MINIMAL, PlatformTier.MINIMAL): ConversionMode.ADAPT,
    (PlatformTier.STANDARD, PlatformTier.STANDARD): ConversionMode.ADAPT,
    (PlatformTier.EXTENDED, PlatformTier.EXTENDED): ConversionMode.ADAPT,
}


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class ConversionResult:
    """Result of cross-generation conversion."""

    success: bool
    source_platform: str
    target_platform: str
    conversion_mode: ConversionMode

    # Images
    source_image: Optional[Image.Image] = None
    converted_image: Optional[Image.Image] = None

    # Conversion stats
    source_resolution: Tuple[int, int] = (0, 0)
    target_resolution: Tuple[int, int] = (0, 0)
    source_colors: int = 0
    target_colors: int = 0

    # Quality metrics
    detail_change: str = "none"  # increased, decreased, maintained
    color_change: str = "none"
    style_fidelity: float = 0.0  # 0-1, how well it matches target style

    # Output files
    files: Dict[str, str] = field(default_factory=dict)

    # Validation
    validation_passed: bool = True
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TierGenerationResult:
    """Result of tier-based generation for multi-platform deployment."""

    tier: GenerationTier
    master_image: Image.Image
    platform_variants: Dict[str, Image.Image]  # platform -> converted image

    # Stats
    base_resolution: Tuple[int, int] = (0, 0)
    base_colors: int = 0

    # Per-platform validation
    platform_validation: Dict[str, Dict] = field(default_factory=dict)

    warnings: List[str] = field(default_factory=list)
    files: Dict[str, str] = field(default_factory=dict)


# =============================================================================
# Cross-Generation Converter
# =============================================================================

class CrossGenConverter:
    """
    Cross-generation asset converter.

    Converts assets between different hardware generations while
    respecting platform constraints and maintaining visual identity.

    Uses ALGORITHMIC processing for platform adaptation (resize, quantize, tile optimize).
    AI is used for cross-gen upscaling (NES -> 16-bit):
    - Default: BFL Kontext (precise dimensions)
    - Multi-model: BFL + gptimage-large + nanobanana fallbacks
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        debug: bool = False,
        debug_dir: Optional[Path] = None,
        multi_model: bool = False,
    ):
        """
        Initialize converter.

        Args:
            api_key: Optional Pollinations API key
            debug: Enable debug output and save intermediate images
            debug_dir: Directory for debug output (default: ./debug/)
            multi_model: Use multiple AI models with fallbacks (default: BFL only)
        """
        self.client = PollinationsClient(api_key)
        self.debug = debug
        self.multi_model = multi_model
        self._debug_dir = Path(debug_dir) if debug_dir else Path('./debug')

        # Configure logging level based on debug flag
        if self.debug:
            logger.setLevel(logging.DEBUG)
            self._debug_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Debug mode enabled. Output: {self._debug_dir}")
            logger.info(f"Multi-model mode: {self.multi_model}")
        else:
            logger.setLevel(logging.INFO)

        # Platform configs cache
        self._platform_configs: Dict[str, PlatformConfig] = {}

        logger.debug(f"CrossGenConverter initialized (debug={debug}, multi_model={multi_model})")

    def get_platform_config(self, platform: str) -> PlatformConfig:
        """Get or create platform config."""
        if platform not in self._platform_configs:
            self._platform_configs[platform] = get_platform_config(platform)
        return self._platform_configs[platform]

    # -------------------------------------------------------------------------
    # Main Conversion Methods
    # -------------------------------------------------------------------------

    def convert(
        self,
        image: Image.Image,
        source_platform: str,
        target_platform: str,
        description: str = "",
        preserve_palette: bool = False,
    ) -> ConversionResult:
        """
        Convert asset from one platform to another.

        Automatically determines the best conversion strategy based on
        source and target platform tiers.

        Args:
            image: Source image to convert
            source_platform: Source platform name (nes, genesis, etc.)
            target_platform: Target platform name
            description: Optional description for AI context
            preserve_palette: Try to maintain similar color scheme

        Returns:
            ConversionResult with converted image and metadata
        """
        source_config = self.get_platform_config(source_platform)
        target_config = self.get_platform_config(target_platform)

        # Determine conversion mode
        source_tier = self._get_tier(source_config)
        target_tier = self._get_tier(target_config)
        mode = CONVERSION_PATHS.get(
            (source_tier, target_tier),
            ConversionMode.ADAPT
        )

        result = ConversionResult(
            success=False,
            source_platform=source_platform,
            target_platform=target_platform,
            conversion_mode=mode,
            source_image=image,
            source_resolution=(image.width, image.height),
        )

        try:
            if mode == ConversionMode.UPSCALE:
                converted = self._upscale_convert(
                    image, source_config, target_config, description
                )
            elif mode == ConversionMode.DOWNSCALE:
                converted = self._downscale_convert(
                    image, source_config, target_config, description, preserve_palette
                )
            elif mode == ConversionMode.ADAPT:
                converted = self._adapt_convert(
                    image, source_config, target_config, description, preserve_palette
                )
            else:
                converted = self._regenerate_convert(
                    image, source_config, target_config, description
                )

            result.converted_image = converted
            result.target_resolution = (converted.width, converted.height)
            result.target_colors = self._count_colors(converted)
            result.source_colors = self._count_colors(image)

            # Validate against target platform
            validation = validate_asset_for_platform(
                target_platform,
                tile_count=self._estimate_tiles(converted, target_config),
                colors_used=result.target_colors,
            )
            result.validation_passed = validation['valid']
            result.warnings.extend(validation.get('warnings', []))
            result.errors.extend(validation.get('errors', []))

            # Calculate quality metrics
            result.detail_change = self._assess_detail_change(mode)
            result.color_change = self._assess_color_change(
                result.source_colors, result.target_colors
            )

            result.success = True

        except Exception as e:
            result.errors.append(str(e))

        return result

    def upscale_to_16bit(
        self,
        image: Image.Image,
        source_platform: str = "nes",
        target_platform: str = "genesis",
        description: str = "",
        scale_factor: int = 2,
        use_tile_aware: bool = True,
        tier_only: bool = False,
    ) -> ConversionResult:
        """
        Upscale 8-bit asset to 16-bit quality.

        Uses img2img AI to intelligently add detail and expand color palette
        while maintaining the original design's character.

        Supports two modes:
        1. tier_only=True: Generic "16-bit" style without exact platform limits
           - Creates a bespoke 16-bit sprite that can be further refined
           - Use this to then call adapt_to_platform() for final output
        2. tier_only=False: Apply exact platform constraints (genesis, snes, etc.)
           - Final output conforms to hardware limits

        If use_tile_aware=True and both platforms are tile-based, uses
        per-tile enhancement for better hardware accuracy.

        Args:
            image: Source 8-bit image
            source_platform: Source platform (nes, gb, etc.)
            target_platform: Target 16-bit platform (genesis, snes) or tier name
            description: Description for AI context
            scale_factor: Resolution multiplier (1, 2, or 4)
            use_tile_aware: Use tile-aware conversion if applicable
            tier_only: If True, generate generic tier style without exact limits

        Returns:
            ConversionResult with upscaled image
        """
        source_config = self.get_platform_config(source_platform)

        # Handle tier_only mode - generic tier style without exact platform limits
        if tier_only:
            return self._upscale_tier_only(
                image, source_config, target_platform, description, scale_factor
            )

        target_config = self.get_platform_config(target_platform)

        result = ConversionResult(
            success=False,
            source_platform=source_platform,
            target_platform=target_platform,
            conversion_mode=ConversionMode.UPSCALE,
            source_image=image,
            source_resolution=(image.width, image.height),
        )

        try:
            # Check if both platforms are tile-based for tile-aware conversion
            source_limits = source_config._full_limits
            target_limits = target_config._full_limits
            source_tile_based = getattr(source_limits.backgrounds, 'is_tile_based', True) if source_limits else True
            target_tile_based = getattr(target_limits.backgrounds, 'is_tile_based', True) if target_limits else True

            if use_tile_aware and source_tile_based and target_tile_based:
                # Use tile-aware conversion for hardware-accurate upgrade
                print(f"  Using tile-aware conversion ({source_platform} -> {target_platform})")
                tile_result = self.convert_tile_aware(
                    image, source_platform, target_platform, description, use_ai_enhancement=True
                )
                result.converted_image = tile_result.converted_image
                result.target_resolution = tile_result.target_resolution
                result.target_colors = tile_result.target_colors
                result.source_colors = tile_result.source_colors
                result.metadata = tile_result.metadata
                result.warnings = tile_result.warnings
                result.detail_change = "increased"
                result.color_change = "expanded"
                result.success = tile_result.success
                return result

            # Standard img2img upscaling for non-tile or mixed conversions
            target_width = image.width * scale_factor
            target_height = image.height * scale_factor

            # Clamp to target platform screen size if needed
            max_width = target_config.screen_width * 4  # Allow multi-screen

            if target_width > max_width:
                scale = max_width / target_width
                target_width = max_width
                target_height = int(target_height * scale)

            print(f"  Using img2img upscale ({image.width}x{image.height} -> {target_width}x{target_height})")

            # Use img2img_upscale for AI-enhanced upscaling
            upscaled = self.client.img2img_upscale(
                image=image,
                target_platform=target_platform,
                scale=scale_factor,
                add_detail=True,
                use_zimage=(scale_factor == 2),  # Use zimage for 2x
            )

            # Post-process for target platform (color reduction, tile optimization)
            converted = self._postprocess_for_platform(upscaled, target_config)

            # Tile-optimize if target is tile-based
            if target_tile_based:
                dedup = TileDeduplicator(
                    tile_width=target_config.tile_width,
                    tile_height=target_config.tile_height,
                    enable_h_flip=target_config.hardware_h_flip,
                    enable_v_flip=target_config.hardware_v_flip,
                )
                tile_result = dedup.optimize(converted)
                print(f"  Tile optimization: {tile_result.optimized_tile_count} unique tiles")
                print(f"  Savings from flip detection: {tile_result.savings_percent:.1f}%")

                if tile_result.optimized_tile_count > target_config.max_tiles_per_bank:
                    result.warnings.append(
                        f"Tile count ({tile_result.optimized_tile_count}) exceeds "
                        f"{target_platform} limit ({target_config.max_tiles_per_bank})"
                    )
                    converted = self._reduce_tile_count(converted, target_config)

                result.metadata['tiles'] = {
                    'unique': tile_result.optimized_tile_count,
                    'original': tile_result.original_tile_count,
                    'savings_percent': tile_result.savings_percent,
                    'flip_stats': tile_result.flip_stats,
                }

            result.converted_image = converted
            result.target_resolution = (converted.width, converted.height)
            result.target_colors = self._count_colors(converted)
            result.source_colors = self._count_colors(image)
            result.detail_change = "increased"
            result.color_change = "expanded"
            result.success = True

        except Exception as e:
            result.errors.append(str(e))
            import traceback
            traceback.print_exc()

        return result

    def _reduce_tile_count(
        self,
        image: Image.Image,
        config: PlatformConfig,
    ) -> Image.Image:
        """Reduce unique tile count to fit within platform limits."""
        # More aggressive quantization
        max_colors = max(config.colors_per_palette * config.max_palettes // 2, 4)

        # Handle RGBA properly
        if image.mode == 'RGBA':
            alpha = image.split()[3]
            rgb = image.convert('RGB')
            quantized = rgb.quantize(colors=max_colors, method=Image.Quantize.FASTOCTREE)
            result = quantized.convert('RGBA')
            result.putalpha(alpha)
        else:
            quantized = image.quantize(colors=max_colors, method=Image.Quantize.FASTOCTREE)
            result = quantized.convert('RGBA')

        # Re-check tile count
        dedup = TileDeduplicator(
            tile_width=config.tile_width,
            tile_height=config.tile_height,
            enable_h_flip=config.hardware_h_flip,
            enable_v_flip=config.hardware_v_flip,
        )
        tile_result = dedup.optimize(result)

        print(f"    After reduction: {tile_result.optimized_tile_count} tiles")
        return result

    def downscale_to_8bit(
        self,
        image: Image.Image,
        source_platform: str = "genesis",
        target_platform: str = "nes",
        description: str = "",
        preserve_key_details: bool = True,
    ) -> ConversionResult:
        """
        Downscale 16-bit asset to 8-bit quality.

        Intelligently reduces colors and detail while preserving
        the essential character of the original design.

        Args:
            image: Source 16-bit image
            source_platform: Source platform (genesis, snes)
            target_platform: Target 8-bit platform (nes, gb)
            description: Description for AI context
            preserve_key_details: Use AI to identify and preserve key features

        Returns:
            ConversionResult with downscaled image
        """
        source_config = self.get_platform_config(source_platform)
        target_config = self.get_platform_config(target_platform)

        result = ConversionResult(
            success=False,
            source_platform=source_platform,
            target_platform=target_platform,
            conversion_mode=ConversionMode.DOWNSCALE,
            source_image=image,
            source_resolution=(image.width, image.height),
        )

        try:
            # Calculate target dimensions
            scale_factor = target_config.screen_width / source_config.screen_width
            target_width = int(image.width * scale_factor)
            target_height = int(image.height * scale_factor)

            # Ensure tile alignment
            target_width = (target_width // target_config.tile_width) * target_config.tile_width
            target_height = (target_height // target_config.tile_height) * target_config.tile_height

            if preserve_key_details:
                # Use AI to intelligently downscale
                converted = self._ai_downscale(
                    image, source_config, target_config, description,
                    (target_width, target_height)
                )
            else:
                # Use algorithmic downscaling
                converted = self._algorithmic_downscale(
                    image, target_config, (target_width, target_height)
                )

            result.converted_image = converted
            result.target_resolution = (converted.width, converted.height)
            result.target_colors = self._count_colors(converted)
            result.source_colors = self._count_colors(image)
            result.detail_change = "decreased"
            result.color_change = "reduced"
            result.success = True

            # Validate
            validation = validate_asset_for_platform(
                target_platform,
                tile_count=self._estimate_tiles(converted, target_config),
                colors_used=result.target_colors,
            )
            result.validation_passed = validation['valid']
            result.warnings.extend(validation.get('warnings', []))

        except Exception as e:
            result.errors.append(str(e))

        return result

    # -------------------------------------------------------------------------
    # Tier-Based Generation
    # -------------------------------------------------------------------------

    def generate_for_tier(
        self,
        description: str,
        tier: GenerationTier,
        asset_type: str = "sprite",
        size: Optional[Tuple[int, int]] = None,
        target_platforms: Optional[List[str]] = None,
    ) -> TierGenerationResult:
        """
        Generate asset at tier quality level for multi-platform deployment.

        Creates a "master" asset at the tier's best quality, then generates
        platform-specific variants through intelligent downsampling.

        Args:
            description: Asset description for AI generation
            tier: Target generation tier (8bit, 16bit, 32bit, best)
            asset_type: Type of asset (sprite, background, tile)
            size: Optional override for asset dimensions
            target_platforms: Specific platforms to generate variants for

        Returns:
            TierGenerationResult with master and platform variants
        """
        # Get tier configuration
        tier_config = self._get_tier_config(tier)

        # Determine target platforms
        if target_platforms is None:
            target_platforms = TIER_PLATFORMS.get(tier, ['nes'])

        # Calculate master asset size
        if size is None:
            size = self._get_tier_default_size(tier, asset_type)

        result = TierGenerationResult(
            tier=tier,
            master_image=None,
            platform_variants={},
            base_resolution=size,
        )

        try:
            # Generate master asset at tier quality
            master = self._generate_tier_master(
                description, tier, tier_config, asset_type, size
            )
            result.master_image = master
            result.base_colors = self._count_colors(master)

            # Generate platform variants
            for platform in target_platforms:
                platform_config = self.get_platform_config(platform)

                # Convert master to platform-specific version
                variant = self._create_platform_variant(
                    master, tier_config, platform_config, description
                )
                result.platform_variants[platform] = variant

                # Validate variant
                validation = validate_asset_for_platform(
                    platform,
                    tile_count=self._estimate_tiles(variant, platform_config),
                    colors_used=self._count_colors(variant),
                )
                result.platform_validation[platform] = validation

                if not validation['valid']:
                    result.warnings.append(
                        f"{platform}: {', '.join(validation.get('errors', []))}"
                    )

        except Exception as e:
            result.warnings.append(str(e))

        return result

    def create_multi_platform_set(
        self,
        description: str,
        platforms: List[str],
        asset_type: str = "sprite",
        base_size: Optional[Tuple[int, int]] = None,
    ) -> Dict[str, ConversionResult]:
        """
        Create a set of platform-specific assets from a single description.

        Generates at the highest tier among target platforms, then creates
        optimized versions for each platform.

        Args:
            description: Asset description
            platforms: List of target platforms
            asset_type: Type of asset
            base_size: Optional base size

        Returns:
            Dict mapping platform names to ConversionResults
        """
        # Determine highest tier among targets
        highest_tier = PlatformTier.MINIMAL
        for platform in platforms:
            config = self.get_platform_config(platform)
            tier = self._get_tier(config)
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

        # Generate tier result
        tier_result = self.generate_for_tier(
            description=description,
            tier=gen_tier,
            asset_type=asset_type,
            size=base_size,
            target_platforms=platforms,
        )

        # Package as conversion results
        results = {}
        for platform in platforms:
            variant = tier_result.platform_variants.get(platform)
            validation = tier_result.platform_validation.get(platform, {})

            results[platform] = ConversionResult(
                success=variant is not None,
                source_platform=f"tier_{gen_tier.value}",
                target_platform=platform,
                conversion_mode=ConversionMode.ADAPT,
                source_image=tier_result.master_image,
                converted_image=variant,
                source_resolution=tier_result.base_resolution,
                target_resolution=(variant.width, variant.height) if variant else (0, 0),
                source_colors=tier_result.base_colors,
                target_colors=self._count_colors(variant) if variant else 0,
                validation_passed=validation.get('valid', False),
                warnings=validation.get('warnings', []),
                errors=validation.get('errors', []),
            )

        return results

    # -------------------------------------------------------------------------
    # Tier-Based & Platform Adaptation Methods
    # -------------------------------------------------------------------------

    def _upscale_tier_only(
        self,
        image: Image.Image,
        source_config: PlatformConfig,
        target_tier: str,
        description: str,
        scale_factor: int,
    ) -> ConversionResult:
        """
        Upscale to a generic tier style without exact platform constraints.

        Creates a high-quality intermediate that can be further refined
        via adapt_to_platform().

        Args:
            image: Source image
            source_config: Source platform config
            target_tier: Tier name ("8bit", "16bit", "32bit") or platform name
            description: Asset description
            scale_factor: Scale multiplier

        Returns:
            ConversionResult with tier-quality image (no platform limits applied)
        """
        # Map tier names to representative configs
        tier_configs = {
            '8bit': {'colors': 16, 'style': '8-bit pixel art'},
            '16bit': {'colors': 64, 'style': '16-bit pixel art with smooth gradients'},
            '32bit': {'colors': 256, 'style': 'high-quality pixel art with rich colors'},
        }

        # Use tier config if specified, otherwise infer from platform name
        if target_tier.lower() in tier_configs:
            tier_cfg = tier_configs[target_tier.lower()]
        else:
            # Try to get tier from platform
            try:
                platform_config = self.get_platform_config(target_tier)
                tier = platform_config.tier
                if tier in ('MINIMAL', 'MINIMAL_PLUS'):
                    tier_cfg = tier_configs['8bit']
                elif tier in ('STANDARD', 'STANDARD_PLUS'):
                    tier_cfg = tier_configs['16bit']
                else:
                    tier_cfg = tier_configs['32bit']
            except Exception:
                tier_cfg = tier_configs['16bit']  # Default

        result = ConversionResult(
            success=False,
            source_platform=source_config.name,
            target_platform=f"tier_{target_tier}",
            conversion_mode=ConversionMode.UPSCALE,
            source_image=image,
            source_resolution=(image.width, image.height),
        )

        try:
            target_width = image.width * scale_factor
            target_height = image.height * scale_factor
            start_time = time.time()

            logger.info(f"Tier upscale: {target_tier} ({image.width}x{image.height} -> {target_width}x{target_height})")
            logger.debug(f"Style: {tier_cfg['style']}, Max colors: {tier_cfg['colors']}")

            # Build enhancement prompts
            # For general img2img models (GPT-image, nanobanana)
            enhancement_prompt = f"highly detailed 16-bit version, preserve exact composition and colors, add texture and shading"
            if description:
                enhancement_prompt += f", {description}"
            logger.debug(f"Enhancement prompt: {enhancement_prompt}")

            # For BFL Kontext - needs action-oriented edit instructions
            kontext_prompt = "Upscale this pixel art image to higher resolution. Add fine details, texture, and smooth gradients while preserving the original composition and color palette. Enhance sharpness and add subtle shading to make it look like professional 16-bit video game art."
            logger.debug(f"Kontext prompt: {kontext_prompt}")

            upscaled = None

            # === DEFAULT: BFL Kontext (precise dimensions) ===
            logger.info("Attempting BFL Kontext (default)...")
            bfl_start = time.time()
            try:
                bfl_result = self.client.img2img_bfl_kontext(
                    image=image,
                    prompt=kontext_prompt,  # Use Kontext-specific edit prompt
                    width=target_width,
                    height=target_height,
                )
                if bfl_result:
                    upscaled = bfl_result
                    logger.info(f"BFL Kontext SUCCESS: {upscaled.width}x{upscaled.height} in {time.time() - bfl_start:.1f}s")
                else:
                    logger.warning("BFL Kontext returned None (no API key or error)")
            except Exception as e:
                logger.error(f"BFL Kontext FAILED: {e}")

            # === MULTI-MODEL FALLBACKS (only if flagged) ===
            if upscaled is None and self.multi_model:
                logger.info("Multi-model mode: trying Pollinations fallbacks...")

                # Fallback 1: gptimage-large
                logger.debug("Trying gptimage-large on gen.pollinations.ai...")
                gpt_start = time.time()
                try:
                    upscaled = self.client.img2img_enhance(
                        image=image,
                        enhancement_prompt=enhancement_prompt,
                        width=target_width,
                        height=target_height,
                        model='gptimage-large',
                        use_ai=True,
                    )
                    logger.info(f"gptimage-large SUCCESS: {upscaled.width}x{upscaled.height} in {time.time() - gpt_start:.1f}s")
                except Exception as e:
                    logger.warning(f"gptimage-large FAILED: {e}")

                # Fallback 2: nanobanana
                if upscaled is None:
                    logger.debug("Trying nanobanana...")
                    nano_start = time.time()
                    try:
                        upscaled = self.client.img2img_enhance(
                            image=image,
                            enhancement_prompt=enhancement_prompt,
                            width=target_width,
                            height=target_height,
                            model='nanobanana',
                            use_ai=True,
                        )
                        logger.info(f"nanobanana SUCCESS: {upscaled.width}x{upscaled.height} in {time.time() - nano_start:.1f}s")
                    except Exception as e:
                        logger.warning(f"nanobanana FAILED: {e}")

            # === ALGORITHMIC FALLBACK ===
            if upscaled is None:
                logger.warning("All AI models failed, using algorithmic upscale (LANCZOS)")
                upscaled = image.resize((target_width, target_height), Image.LANCZOS)
                logger.debug(f"Algorithmic result: {upscaled.width}x{upscaled.height}")

            # Resize to target dimensions if needed (Pollinations ignores dimensions)
            if upscaled.size != (target_width, target_height):
                logger.info(f"Resizing {upscaled.width}x{upscaled.height} -> {target_width}x{target_height}")
                upscaled = upscaled.resize((target_width, target_height), Image.LANCZOS)

            # Log total time
            total_time = time.time() - start_time
            logger.info(f"Tier upscale complete in {total_time:.1f}s")

            # Save debug image
            if self.debug and self._debug_dir:
                debug_path = self._debug_dir / f"tier_upscale_{target_tier}.png"
                upscaled.save(debug_path)
                logger.debug(f"Saved debug image: {debug_path}")

            # Light color quantization to tier level (not platform-specific)
            if tier_cfg['colors'] < 256:
                # Handle RGBA properly
                if upscaled.mode == 'RGBA':
                    alpha = upscaled.split()[3]
                    rgb = upscaled.convert('RGB')
                    quantized = rgb.quantize(colors=tier_cfg['colors'], method=Image.Quantize.FASTOCTREE)
                    converted = quantized.convert('RGBA')
                    converted.putalpha(alpha)
                else:
                    quantized = upscaled.quantize(colors=tier_cfg['colors'], method=Image.Quantize.FASTOCTREE)
                    converted = quantized.convert('RGBA')
            else:
                converted = upscaled if upscaled.mode == 'RGBA' else upscaled.convert('RGBA')

            result.converted_image = converted
            result.target_resolution = (converted.width, converted.height)
            result.target_colors = self._count_colors(converted)
            result.source_colors = self._count_colors(image)
            result.detail_change = "increased"
            result.color_change = "expanded"
            result.metadata['tier'] = target_tier
            result.metadata['tier_colors'] = tier_cfg['colors']
            result.metadata['tier_style'] = tier_cfg['style']
            result.metadata['ready_for_platform_adapt'] = True
            result.success = True

        except Exception as e:
            result.errors.append(str(e))
            import traceback
            traceback.print_exc()

        return result

    def adapt_to_platform(
        self,
        image: Image.Image,
        target_platform: str,
        description: str = "",
        remove_text: bool = True,
    ) -> ConversionResult:
        """
        Adapt a tier-quality image to exact platform constraints.

        This is the second stage of the two-stage workflow:
        1. upscale_to_16bit(tier_only=True) -> bespoke 16-bit sprite
        2. adapt_to_platform() -> perfect genesis/snes/etc sprite

        Applies:
        - Text removal (crop AI-generated labels)
        - Exact color palette limits (16 colors/tile for Genesis)
        - Tile optimization with H/V flip detection
        - Resolution constraints
        - Platform-specific quantization

        Args:
            image: Tier-quality image (from tier_only upscale)
            target_platform: Exact platform name (genesis, snes, etc.)
            description: Asset description for AI context
            remove_text: Remove AI text labels from margins (default True)

        Returns:
            ConversionResult with platform-conformant image
        """
        # Preprocess: Remove AI-generated text labels (simple crop, no AI)
        if remove_text:
            image = self.client.preprocess_remove_text(image)

        # DEBUG: Save after text removal
        if self.debug:
            self._debug_dir.mkdir(parents=True, exist_ok=True)
            debug_path = self._debug_dir / f"01_after_text_removal_{target_platform}.png"
            image.save(debug_path)
            print(f"    [DEBUG] Saved: {debug_path}")

        target_config = self.get_platform_config(target_platform)

        result = ConversionResult(
            success=False,
            source_platform="tier_intermediate",
            target_platform=target_platform,
            conversion_mode=ConversionMode.ADAPT,
            source_image=image,
            source_resolution=(image.width, image.height),
        )

        try:
            print(f"  Adapting to {target_platform} limits:")
            print(f"    Colors: {target_config.colors_per_palette} per palette, {target_config.max_palettes} palettes")
            print(f"    Max tiles: {target_config.max_tiles_per_bank}")

            # Step 1: Resize to platform resolution if needed
            target_limits = target_config._full_limits
            max_width = target_config.screen_width * 2  # Allow 2 screens
            max_height = target_config.screen_height

            if image.width > max_width or image.height > max_height:
                scale = min(max_width / image.width, max_height / image.height)
                new_width = int(image.width * scale)
                new_height = int(image.height * scale)
                # Align to tile grid
                new_width = (new_width // target_config.tile_width) * target_config.tile_width
                new_height = (new_height // target_config.tile_height) * target_config.tile_height
                # Use NEAREST for 8-bit platforms to preserve pixel sharpness
                resample = Image.NEAREST if target_config.tier in ('MINIMAL', 'MINIMAL_PLUS') else Image.LANCZOS
                image = image.resize((new_width, new_height), resample)
                print(f"    Resized to {new_width}x{new_height} (using {'NEAREST' if resample == Image.NEAREST else 'LANCZOS'})")

            # Step 2: Quantize to platform color limits
            # NES: 4 colors/palette × 4 palettes = 16 colors
            # Genesis: 16 colors/palette × 4 palettes = 64 colors
            total_colors = target_config.colors_per_palette * target_config.max_palettes

            # For 8-bit platforms, use more careful quantization
            is_8bit = target_config.tier in ('MINIMAL', 'MINIMAL_PLUS')

            # Handle RGBA properly for quantization
            if image.mode == 'RGBA':
                alpha = image.split()[3]
                rgb = image.convert('RGB')
                # Use MEDIANCUT for 8-bit (better color selection), FASTOCTREE for 16-bit (faster)
                if is_8bit:
                    # For NES, quantize to slightly more colors then reduce
                    # This preserves more detail
                    quantized = rgb.quantize(colors=min(total_colors * 2, 32), method=Image.Quantize.MEDIANCUT)
                    converted = quantized.convert('RGB').quantize(colors=total_colors, method=Image.Quantize.MEDIANCUT)
                    converted = converted.convert('RGBA')
                else:
                    quantized = rgb.quantize(colors=total_colors, method=Image.Quantize.FASTOCTREE)
                    converted = quantized.convert('RGBA')
                converted.putalpha(alpha)
            else:
                if is_8bit:
                    quantized = image.convert('RGB').quantize(colors=min(total_colors * 2, 32), method=Image.Quantize.MEDIANCUT)
                    converted = quantized.convert('RGB').quantize(colors=total_colors, method=Image.Quantize.MEDIANCUT)
                    converted = converted.convert('RGBA')
                else:
                    quantized = image.quantize(colors=total_colors, method=Image.Quantize.FASTOCTREE)
                    converted = quantized.convert('RGBA')

            print(f"    Quantized to {total_colors} colors ({'8-bit' if is_8bit else '16-bit'} mode)")

            # Step 3: Tile optimization with H/V flip detection
            is_tile_based = getattr(target_limits.backgrounds, 'is_tile_based', True) if target_limits else True

            if is_tile_based:
                dedup = TileDeduplicator(
                    tile_width=target_config.tile_width,
                    tile_height=target_config.tile_height,
                    enable_h_flip=target_config.hardware_h_flip,
                    enable_v_flip=target_config.hardware_v_flip,
                    colors_per_palette=target_config.colors_per_palette,
                )
                tile_result = dedup.optimize(converted)

                print(f"    Tiles: {tile_result.optimized_tile_count} unique (was {tile_result.original_tile_count})")
                print(f"    Flip savings: {tile_result.savings_percent:.1f}%")
                print(f"    Flip breakdown: {tile_result.flip_stats}")

                # Check tile limit
                if tile_result.optimized_tile_count > target_config.max_tiles_per_bank:
                    print(f"    WARNING: Over limit! Reducing tile count...")
                    converted = self._reduce_tile_count(converted, target_config)
                    # Re-optimize
                    tile_result = dedup.optimize(converted)
                    print(f"    After reduction: {tile_result.optimized_tile_count} tiles")

                result.metadata['tiles'] = {
                    'unique': tile_result.optimized_tile_count,
                    'original': tile_result.original_tile_count,
                    'savings_percent': tile_result.savings_percent,
                    'flip_stats': tile_result.flip_stats,
                    'within_limit': tile_result.optimized_tile_count <= target_config.max_tiles_per_bank,
                }

            result.converted_image = converted
            result.target_resolution = (converted.width, converted.height)
            result.target_colors = self._count_colors(converted)
            result.source_colors = self._count_colors(image)
            result.detail_change = "maintained"
            result.color_change = "reduced" if result.target_colors < result.source_colors else "maintained"

            # Validate
            validation = validate_asset_for_platform(
                target_platform,
                tile_count=result.metadata.get('tiles', {}).get('unique', 0),
                colors_used=result.target_colors,
            )
            result.validation_passed = validation['valid']
            result.warnings.extend(validation.get('warnings', []))
            result.errors.extend(validation.get('errors', []))

            result.success = True

        except Exception as e:
            result.errors.append(str(e))
            import traceback
            traceback.print_exc()

        return result

    # -------------------------------------------------------------------------
    # Tile-Aware Conversion Methods (NEW)
    # -------------------------------------------------------------------------

    def convert_tile_aware(
        self,
        image: Image.Image,
        source_platform: str,
        target_platform: str,
        description: str = "",
        use_ai_enhancement: bool = True,
    ) -> ConversionResult:
        """
        Convert asset with tile vs raster awareness.

        Automatically determines if source/target are tile-based or bitmap
        and applies appropriate conversion strategy.

        Args:
            image: Source image
            source_platform: Source platform name
            target_platform: Target platform name
            description: Asset description for AI context
            use_ai_enhancement: Use AI for detail enhancement (vs algorithmic)

        Returns:
            ConversionResult with properly converted image
        """
        source_config = self.get_platform_config(source_platform)
        target_config = self.get_platform_config(target_platform)

        # Get tile/bitmap mode from platform limits
        source_limits = source_config._full_limits
        target_limits = target_config._full_limits

        source_tile_based = getattr(source_limits.backgrounds, 'is_tile_based', True) if source_limits else True
        target_tile_based = getattr(target_limits.backgrounds, 'is_tile_based', True) if target_limits else True

        result = ConversionResult(
            success=False,
            source_platform=source_platform,
            target_platform=target_platform,
            conversion_mode=ConversionMode.ADAPT,
            source_image=image,
            source_resolution=(image.width, image.height),
        )

        try:
            if source_tile_based and target_tile_based:
                # Tile-to-tile: Use per-tile enhancement
                converted = self._tile_to_tile_convert(
                    image, source_config, target_config, description, use_ai_enhancement
                )
                result.metadata['conversion_type'] = 'tile_to_tile'

            elif source_tile_based and not target_tile_based:
                # Tile-to-raster: Render tiles to bitmap
                converted = self._tile_to_raster_convert(
                    image, source_config, target_config, description
                )
                result.metadata['conversion_type'] = 'tile_to_raster'

            elif not source_tile_based and target_tile_based:
                # Raster-to-tile: Quantize bitmap to tiles
                converted = self._raster_to_tile_convert(
                    image, source_config, target_config, description
                )
                result.metadata['conversion_type'] = 'raster_to_tile'

            else:
                # Raster-to-raster: Direct image transformation
                converted = self._raster_to_raster_convert(
                    image, source_config, target_config, description
                )
                result.metadata['conversion_type'] = 'raster_to_raster'

            result.converted_image = converted
            result.target_resolution = (converted.width, converted.height)
            result.target_colors = self._count_colors(converted)
            result.source_colors = self._count_colors(image)
            result.success = True

            # Validate against target
            validation = validate_asset_for_platform(
                target_platform,
                tile_count=self._estimate_tiles(converted, target_config),
                colors_used=result.target_colors,
            )
            result.validation_passed = validation['valid']
            result.warnings.extend(validation.get('warnings', []))

        except Exception as e:
            result.errors.append(str(e))

        return result

    def _tile_to_tile_convert(
        self,
        image: Image.Image,
        source_config: PlatformConfig,
        target_config: PlatformConfig,
        description: str,
        use_ai: bool = True,
    ) -> Image.Image:
        """
        Convert between two tile-based platforms with per-tile enhancement.

        This is the core conversion for NES->Genesis style upgrades.
        """
        # Step 1: Extract tiles from source
        dedup = TileDeduplicator(
            tile_width=source_config.tile_width,
            tile_height=source_config.tile_height,
            enable_h_flip=source_config.hardware_h_flip,
            enable_v_flip=source_config.hardware_v_flip,
            colors_per_palette=source_config.colors_per_palette,
        )
        tile_result = dedup.optimize(image)

        print(f"  Extracted {tile_result.original_tile_count} tiles, {tile_result.optimized_tile_count} unique")
        print(f"  Flip stats: {tile_result.flip_stats}")

        # Step 2: Calculate target dimensions
        scale = target_config.screen_width / source_config.screen_width
        if scale < 1:
            scale = 1  # Don't downscale for same-tier conversion

        target_width = int(image.width * scale)
        target_height = int(image.height * scale)

        # Align to target tile grid
        target_width = (target_width // target_config.tile_width) * target_config.tile_width
        target_height = (target_height // target_config.tile_height) * target_config.tile_height

        # Step 3: Enhance each unique tile
        enhanced_tiles = []
        for tile in tile_result.unique_tiles:
            if use_ai:
                # Use AI to enhance tile with more colors
                tile_img = self._array_to_image(tile.pixels, source_config)
                try:
                    enhanced = self.client.img2img_tile_enhance(
                        tile_img,
                        source_colors=source_config.colors_per_palette,
                        target_colors=target_config.colors_per_palette,
                        context=description,
                    )
                except Exception as e:
                    print(f"    AI enhancement failed for tile {tile.tile_id}: {e}")
                    # Fallback to algorithmic enhancement
                    enhanced = self._algorithmic_tile_enhance(
                        tile_img, source_config, target_config
                    )
            else:
                tile_img = self._array_to_image(tile.pixels, source_config)
                enhanced = self._algorithmic_tile_enhance(
                    tile_img, source_config, target_config
                )

            enhanced_tiles.append(enhanced)

        # Step 4: Reconstruct image from enhanced tiles
        result = self._reconstruct_from_tiles(
            enhanced_tiles, tile_result.tile_map,
            source_config, target_config,
            (target_width, target_height)
        )

        # Step 5: Tile-optimize the result for target platform
        target_dedup = TileDeduplicator(
            tile_width=target_config.tile_width,
            tile_height=target_config.tile_height,
            enable_h_flip=target_config.hardware_h_flip,
            enable_v_flip=target_config.hardware_v_flip,
            colors_per_palette=target_config.colors_per_palette,
        )
        final_result = target_dedup.optimize(result)

        print(f"  Target: {final_result.optimized_tile_count} unique tiles (max: {target_config.max_tiles_per_bank})")

        # Check tile limit
        if final_result.optimized_tile_count > target_config.max_tiles_per_bank:
            print(f"  WARNING: Exceeds tile limit, reducing...")
            result = self._reduce_tile_count(result, target_config)

        return result

    def _tile_to_raster_convert(
        self,
        image: Image.Image,
        source_config: PlatformConfig,
        target_config: PlatformConfig,
        description: str,
    ) -> Image.Image:
        """Convert tile-based image to raster/bitmap format."""
        # Simply render at target resolution with full color
        target_width = int(image.width * (target_config.screen_width / source_config.screen_width))
        target_height = int(image.height * (target_config.screen_height / source_config.screen_height))

        # Use AI to add detail since we're removing tile constraints
        return self.client.img2img_upscale(
            image,
            target_platform='bitmap',
            scale=max(1, target_width // image.width),
            add_detail=True,
        )

    def _raster_to_tile_convert(
        self,
        image: Image.Image,
        source_config: PlatformConfig,
        target_config: PlatformConfig,
        description: str,
    ) -> Image.Image:
        """Convert raster/bitmap image to tile-based format."""
        # Step 1: Resize to target dimensions
        target_width = target_config.screen_width
        target_height = target_config.screen_height

        resized = image.resize(
            (target_width, target_height),
            Image.LANCZOS if target_config.tier != 'MINIMAL' else Image.NEAREST
        )

        # Step 2: Quantize colors to palette limit
        total_colors = target_config.colors_per_palette * target_config.max_palettes
        quantized = resized.quantize(colors=total_colors, method=Image.MEDIANCUT)
        result = quantized.convert('RGBA')

        # Step 3: Tile-optimize with H/V flip deduplication
        dedup = TileDeduplicator(
            tile_width=target_config.tile_width,
            tile_height=target_config.tile_height,
            enable_h_flip=target_config.hardware_h_flip,
            enable_v_flip=target_config.hardware_v_flip,
            colors_per_palette=target_config.colors_per_palette,
        )
        tile_result = dedup.optimize(result)

        print(f"  Raster to tiles: {tile_result.optimized_tile_count} unique tiles")
        print(f"  Savings from flip detection: {tile_result.savings_percent:.1f}%")

        # Check if within limits
        if tile_result.optimized_tile_count > target_config.max_tiles_per_bank:
            print(f"  WARNING: Exceeds tile limit ({target_config.max_tiles_per_bank})")
            result = self._reduce_tile_count(result, target_config)

        return result

    def _raster_to_raster_convert(
        self,
        image: Image.Image,
        source_config: PlatformConfig,
        target_config: PlatformConfig,
        description: str,
    ) -> Image.Image:
        """Convert between bitmap/raster formats."""
        # Direct style transfer with color adjustment
        return self.client.img2img_style_transfer(
            image,
            target_style=target_config.prompt_style,
            preserve_content=0.9,
        )

    def _array_to_image(
        self,
        pixels: np.ndarray,
        config: PlatformConfig,
    ) -> Image.Image:
        """Convert numpy pixel array to PIL Image."""
        # Create grayscale image from indexed pixels
        # Scale indices to 0-255 range
        scale = 255 // (config.colors_per_palette - 1)
        scaled = (pixels * scale).astype(np.uint8)
        return Image.fromarray(scaled, mode='L').convert('RGBA')

    def _algorithmic_tile_enhance(
        self,
        tile: Image.Image,
        source_config: PlatformConfig,
        target_config: PlatformConfig,
    ) -> Image.Image:
        """Algorithmically enhance a tile (fallback when AI fails)."""
        # Scale tile if needed
        scale = target_config.tile_width // source_config.tile_width
        if scale > 1:
            tile = tile.resize(
                (tile.width * scale, tile.height * scale),
                Image.NEAREST
            )

        # Expand color palette through interpolation
        if target_config.colors_per_palette > source_config.colors_per_palette:
            # Add intermediate colors
            from PIL import ImageFilter
            tile = tile.filter(ImageFilter.SMOOTH)

        return tile

    def _reconstruct_from_tiles(
        self,
        enhanced_tiles: List[Image.Image],
        tile_map: List[TileRef],
        source_config: PlatformConfig,
        target_config: PlatformConfig,
        target_size: Tuple[int, int],
    ) -> Image.Image:
        """Reconstruct image from enhanced tiles using tile map."""
        target_width, target_height = target_size

        # Calculate scale factor
        scale_x = target_config.tile_width / source_config.tile_width
        scale_y = target_config.tile_height / source_config.tile_height

        result = Image.new('RGBA', (target_width, target_height), (0, 0, 0, 0))

        for ref in tile_map:
            if ref.tile_id >= len(enhanced_tiles):
                continue

            tile = enhanced_tiles[ref.tile_id].copy()

            # Apply flip flags
            if ref.flags.horizontal_flip:
                tile = tile.transpose(Image.FLIP_LEFT_RIGHT)
            if ref.flags.vertical_flip:
                tile = tile.transpose(Image.FLIP_TOP_BOTTOM)

            # Calculate position in target
            target_x = int(ref.x * scale_x)
            target_y = int(ref.y * scale_y)

            # Resize tile if needed
            if tile.width != target_config.tile_width or tile.height != target_config.tile_height:
                tile = tile.resize(
                    (target_config.tile_width, target_config.tile_height),
                    Image.NEAREST
                )

            # Paste tile
            if target_x + tile.width <= target_width and target_y + tile.height <= target_height:
                result.paste(tile, (target_x, target_y))

        return result

    # -------------------------------------------------------------------------
    # Internal Conversion Methods
    # -------------------------------------------------------------------------

    def _upscale_convert(
        self,
        image: Image.Image,
        source_config: PlatformConfig,
        target_config: PlatformConfig,
        description: str,
    ) -> Image.Image:
        """Perform upscale conversion using AI img2img."""

        # Calculate target size
        scale = max(
            target_config.screen_width / source_config.screen_width,
            2.0  # Minimum 2x upscale
        )
        target_width = int(image.width * scale)
        target_height = int(image.height * scale)

        # Tile-align
        target_width = (target_width // target_config.tile_width) * target_config.tile_width
        target_height = (target_height // target_config.tile_height) * target_config.tile_height

        # Clamp to API limits
        max_dim = 1280
        if target_width > max_dim or target_height > max_dim:
            scale_down = max_dim / max(target_width, target_height)
            target_width = int(target_width * scale_down)
            target_height = int(target_height * scale_down)
            # Re-align to tiles
            target_width = (target_width // target_config.tile_width) * target_config.tile_width
            target_height = (target_height // target_config.tile_height) * target_config.tile_height

        # Build edit prompt for img2img upscaling
        edit_prompt = f"""Upscale to {target_config.name} quality.
Add detail appropriate for {target_config.prompt_style}.
Expand to {target_config.colors_per_palette} colors per palette.
Preserve original composition and subject matter.
{description}"""

        # Use img2img to upscale while preserving source content
        try:
            upscaled = self.client.img2img_edit(
                image=image,
                edit_prompt=edit_prompt,
                width=target_width,
                height=target_height,
                model='kontext',
            )
            return self._postprocess_for_platform(upscaled, target_config)
        except Exception as e:
            print(f"AI upscale failed: {e}, using algorithmic fallback")
            # Algorithmic fallback
            upscaled = image.resize((target_width, target_height), Image.LANCZOS)
            return self._postprocess_for_platform(upscaled, target_config)

    def _downscale_convert(
        self,
        image: Image.Image,
        source_config: PlatformConfig,
        target_config: PlatformConfig,
        description: str,
        preserve_palette: bool,
    ) -> Image.Image:
        """Perform downscale conversion."""

        # Calculate target size
        scale = min(
            target_config.screen_width / source_config.screen_width,
            0.5  # Maximum 0.5x downscale by default
        )
        target_width = max(
            int(image.width * scale),
            target_config.tile_width * 2  # Minimum 2 tiles wide
        )
        target_height = max(
            int(image.height * scale),
            target_config.tile_height * 2
        )

        # Tile-align
        target_width = (target_width // target_config.tile_width) * target_config.tile_width
        target_height = (target_height // target_config.tile_height) * target_config.tile_height

        # Use AI for intelligent downscaling
        return self._ai_downscale(
            image, source_config, target_config, description,
            (target_width, target_height)
        )

    def _adapt_convert(
        self,
        image: Image.Image,
        source_config: PlatformConfig,
        target_config: PlatformConfig,
        description: str,
        preserve_palette: bool,
    ) -> Image.Image:
        """Adapt asset for same-tier platform with different specs."""

        # Resize if screen dimensions differ
        if source_config.screen_width != target_config.screen_width:
            scale = target_config.screen_width / source_config.screen_width
            new_width = int(image.width * scale)
            new_height = int(image.height * scale)
            image = image.resize(
                (new_width, new_height),
                Image.LANCZOS if target_config.tier != 'MINIMAL' else Image.NEAREST
            )

        # Adjust colors
        return self._postprocess_for_platform(image, target_config)

    def _regenerate_convert(
        self,
        image: Image.Image,
        source_config: PlatformConfig,
        target_config: PlatformConfig,
        description: str,
    ) -> Image.Image:
        """Completely regenerate asset in target platform style."""

        # Analyze source image for context
        analysis = self._analyze_image(image, source_config)

        # Build regeneration prompt
        prompt = self._build_regeneration_prompt(
            analysis, target_config, description
        )

        # Calculate target size based on original proportions
        aspect = image.width / image.height
        target_height = target_config.screen_height
        target_width = int(target_height * aspect)
        target_width = (target_width // target_config.tile_width) * target_config.tile_width

        # Generate new version
        regenerated = self.client.generate_image(
            prompt=prompt,
            width=target_width,
            height=target_height,
            model='flux',
        )

        return self._postprocess_for_platform(regenerated, target_config)

    def _ai_downscale(
        self,
        image: Image.Image,
        source_config: PlatformConfig,
        target_config: PlatformConfig,
        description: str,
        target_size: Tuple[int, int],
    ) -> Image.Image:
        """Use AI img2img for intelligent downscaling that preserves key features."""

        # Build edit prompt for the img2img transformation
        edit_prompt = f"""Convert to {target_config.name} style pixel art.
Reduce to {target_config.colors_per_palette} colors per palette.
{target_config.prompt_style}.
Preserve key visual features and composition.
{description}"""

        # Use img2img to transform while preserving source content
        try:
            downscaled = self.client.img2img_edit(
                image=image,
                edit_prompt=edit_prompt,
                width=target_size[0],
                height=target_size[1],
                model='kontext',
            )
            return self._postprocess_for_platform(downscaled, target_config)
        except Exception as e:
            print(f"AI downscale failed: {e}, using algorithmic fallback")
            return self._algorithmic_downscale(image, target_config, target_size)

    def _algorithmic_downscale(
        self,
        image: Image.Image,
        target_config: PlatformConfig,
        target_size: Tuple[int, int],
    ) -> Image.Image:
        """Algorithmic downscaling with color reduction."""

        # Resize
        resized = image.resize(target_size, Image.LANCZOS)

        # Reduce colors - handle RGBA properly
        total_colors = target_config.colors_per_palette * target_config.max_palettes

        # For RGBA, we need to use FASTOCTREE or LIBIMAGEQUANT
        if resized.mode == 'RGBA':
            # Save alpha channel
            alpha = resized.split()[3]
            # Convert to RGB for quantization
            rgb = resized.convert('RGB')
            # Quantize RGB
            quantized = rgb.quantize(colors=total_colors, method=Image.Quantize.FASTOCTREE)
            # Convert back to RGBA
            result = quantized.convert('RGBA')
            # Restore alpha channel
            result.putalpha(alpha)
            return result
        else:
            quantized = resized.quantize(colors=total_colors, method=Image.Quantize.FASTOCTREE)
            return quantized.convert('RGBA')

    # -------------------------------------------------------------------------
    # Prompt Building
    # -------------------------------------------------------------------------

    def _build_upscale_prompt(
        self,
        image: Image.Image,
        source_config: PlatformConfig,
        target_config: PlatformConfig,
        description: str,
        target_size: Tuple[int, int],
    ) -> str:
        """Build prompt for AI upscaling."""

        return f"""[CROSS_GEN_UPSCALE]
Upscale this {source_config.name} pixel art to {target_config.name} quality.

ORIGINAL: {source_config.name} ({source_config.tier} tier)
- Resolution: {image.width}x{image.height}
- Colors: {source_config.colors_per_palette} per palette
- Style: {source_config.prompt_style}

TARGET: {target_config.name} ({target_config.tier} tier)
- Resolution: {target_size[0]}x{target_size[1]}
- Colors: {target_config.colors_per_palette} per palette
- Style: {target_config.prompt_style}

DESCRIPTION: {description or 'pixel art asset'}

UPSCALING REQUIREMENTS:
- Add subtle detail appropriate for {target_config.name}
- Expand color palette from {source_config.colors_per_palette} to {target_config.colors_per_palette} colors
- Maintain the original design's character and silhouette
- Add shading/highlights appropriate for 16-bit style
- Keep clean pixel edges (no anti-aliasing to background)
- Preserve the original's charm while adding richness

DO NOT:
- Change the fundamental design
- Add elements not implied by the original
- Use anti-aliasing on sprite edges
- Over-detail small features
"""

    def _build_downscale_prompt(
        self,
        image: Image.Image,
        source_config: PlatformConfig,
        target_config: PlatformConfig,
        description: str,
        target_size: Tuple[int, int],
    ) -> str:
        """Build prompt for AI downscaling."""

        return f"""[CROSS_GEN_DOWNSCALE]
Downscale this {source_config.name} pixel art to {target_config.name} style.

ORIGINAL: {source_config.name} ({source_config.tier} tier)
- Resolution: {image.width}x{image.height}
- Colors: Up to {source_config.colors_per_palette * source_config.max_palettes} colors
- Style: {source_config.prompt_style}

TARGET: {target_config.name} ({target_config.tier} tier)
- Resolution: {target_size[0]}x{target_size[1]}
- Colors: {target_config.colors_per_palette} per palette (max {target_config.colors_per_palette * target_config.max_palettes} total)
- Style: {target_config.prompt_style}

DESCRIPTION: {description or 'pixel art asset'}

DOWNSCALING REQUIREMENTS:
- Simplify to essential shapes and features
- Reduce to {target_config.colors_per_palette}-color palette per sprite/area
- Use chunky pixels with clear edges
- Preserve silhouette and key identifying features
- Apply {target_config.name}-appropriate dithering if needed
- Maintain readability at smaller size

KEY FEATURES TO PRESERVE:
- Overall shape and proportions
- Most distinctive visual elements
- Color relationships (warm/cool, light/dark)
- Character/identity of the design

DO NOT:
- Add detail not in original
- Use anti-aliasing
- Exceed color limits
"""

    def _build_regeneration_prompt(
        self,
        analysis: Dict,
        target_config: PlatformConfig,
        description: str,
    ) -> str:
        """Build prompt for complete regeneration."""

        return f"""[CROSS_GEN_REGENERATE]
Recreate this pixel art in {target_config.name} style.

ANALYZED ORIGINAL:
- Type: {analysis.get('type', 'sprite')}
- Dominant colors: {analysis.get('colors', 'various')}
- Subject: {analysis.get('subject', 'unknown')}
- Style notes: {analysis.get('style', 'pixel art')}

TARGET: {target_config.name} ({target_config.tier} tier)
- Colors: {target_config.colors_per_palette} per palette
- Style: {target_config.prompt_style}

DESCRIPTION: {description or analysis.get('subject', 'pixel art asset')}

REGENERATION REQUIREMENTS:
- Create fresh art in authentic {target_config.name} style
- Capture the essence and subject of the original
- Use hardware-accurate color palette
- Follow {target_config.name} pixel art conventions
- Match the general composition and feel

STYLE GUIDE:
{target_config.prompt_style}
"""

    # -------------------------------------------------------------------------
    # Tier Generation Helpers
    # -------------------------------------------------------------------------

    def _get_tier_config(self, tier: GenerationTier) -> PlatformConfig:
        """Get a representative config for a generation tier."""
        tier_platforms = {
            GenerationTier.TIER_8BIT: 'nes',
            GenerationTier.TIER_16BIT: 'genesis',
            GenerationTier.TIER_32BIT: 'gba',
            GenerationTier.TIER_BEST: 'snes',  # SNES has most colors
        }
        platform = tier_platforms.get(tier, 'genesis')
        return self.get_platform_config(platform)

    def _get_tier_default_size(
        self,
        tier: GenerationTier,
        asset_type: str,
    ) -> Tuple[int, int]:
        """Get default size for tier and asset type."""
        sizes = {
            ('8bit', 'sprite'): (16, 16),
            ('8bit', 'background'): (256, 240),
            ('8bit', 'tile'): (8, 8),
            ('16bit', 'sprite'): (32, 32),
            ('16bit', 'background'): (320, 224),
            ('16bit', 'tile'): (8, 8),
            ('32bit', 'sprite'): (64, 64),
            ('32bit', 'background'): (240, 160),
            ('32bit', 'tile'): (8, 8),
            ('best', 'sprite'): (64, 64),
            ('best', 'background'): (320, 240),
            ('best', 'tile'): (8, 8),
        }
        return sizes.get((tier.value, asset_type), (32, 32))

    def _generate_tier_master(
        self,
        description: str,
        tier: GenerationTier,
        tier_config: PlatformConfig,
        asset_type: str,
        size: Tuple[int, int],
    ) -> Image.Image:
        """Generate master asset at tier quality."""

        prompt = f"""[TIER_GENERATION]
Create a {asset_type} in {tier.value} pixel art style.

DESCRIPTION: {description}

SPECIFICATIONS:
- Resolution: {size[0]}x{size[1]} pixels
- Style: {tier_config.prompt_style}
- Colors: Up to {tier_config.colors_per_palette * tier_config.max_palettes} colors
- This will be used as a master for multi-platform deployment

QUALITY:
- Clean pixel edges, no anti-aliasing to transparent areas
- Proper sprite proportions for {asset_type}
- Game-ready quality
- Transparent background (for sprites)

DO NOT:
- Add text or labels
- Use gradients or anti-aliasing
- Include background elements (for sprites)
"""

        # Generate at higher resolution for quality
        gen_width = size[0] * 4
        gen_height = size[1] * 4

        master = self.client.generate_image(
            prompt=prompt,
            width=gen_width,
            height=gen_height,
            model='flux',
        )

        # Downscale to target
        master = master.resize(size, Image.LANCZOS)

        return master

    def _create_platform_variant(
        self,
        master: Image.Image,
        source_config: PlatformConfig,
        target_config: PlatformConfig,
        description: str,
    ) -> Image.Image:
        """Create platform-specific variant from master."""

        # Determine if we need to scale
        source_tier = self._get_tier(source_config)
        target_tier = self._get_tier(target_config)

        if source_tier.value > target_tier.value:
            # Downscale
            return self._downscale_convert(
                master, source_config, target_config, description, False
            )
        elif source_tier.value < target_tier.value:
            # Upscale (unusual but possible)
            return self._upscale_convert(
                master, source_config, target_config, description
            )
        else:
            # Same tier, just adapt colors/style
            return self._adapt_convert(
                master, source_config, target_config, description, True
            )

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    def _get_tier(self, config: PlatformConfig) -> PlatformTier:
        """Get PlatformTier from config."""
        tier_map = {
            'MINIMAL': PlatformTier.MINIMAL,
            'MINIMAL_PLUS': PlatformTier.MINIMAL_PLUS,
            'STANDARD': PlatformTier.STANDARD,
            'STANDARD_PLUS': PlatformTier.STANDARD_PLUS,
            'EXTENDED': PlatformTier.EXTENDED,
        }
        return tier_map.get(config.tier, PlatformTier.STANDARD)

    def _postprocess_for_platform(
        self,
        image: Image.Image,
        config: PlatformConfig,
    ) -> Image.Image:
        """Post-process image for target platform constraints."""

        # Ensure correct mode
        if image.mode not in ('RGB', 'RGBA'):
            image = image.convert('RGBA')

        # Quantize colors
        total_colors = config.colors_per_palette * config.max_palettes

        # For 8-bit platforms, use nearest neighbor
        if config.tier == 'MINIMAL':
            # More aggressive quantization
            quantized = image.quantize(
                colors=min(total_colors, 16),
                method=Image.MEDIANCUT
            )
        else:
            quantized = image.quantize(
                colors=total_colors,
                method=Image.MEDIANCUT
            )

        return quantized.convert('RGBA')

    def _count_colors(self, image: Image.Image) -> int:
        """Count unique colors in image."""
        if image.mode == 'P':
            return len(image.getcolors(maxcolors=256) or [])

        img_rgb = image.convert('RGB')
        colors = img_rgb.getcolors(maxcolors=65536)
        return len(colors) if colors else 65536

    def _estimate_tiles(
        self,
        image: Image.Image,
        config: PlatformConfig,
    ) -> int:
        """Estimate number of unique tiles in image."""
        width_tiles = image.width // config.tile_width
        height_tiles = image.height // config.tile_height
        total_tiles = width_tiles * height_tiles

        # Estimate ~60% unique after optimization
        return int(total_tiles * 0.6)

    def _analyze_image(
        self,
        image: Image.Image,
        config: PlatformConfig,
    ) -> Dict:
        """Analyze image characteristics for regeneration."""

        # Get dominant colors
        img_rgb = image.convert('RGB')
        colors = img_rgb.getcolors(maxcolors=256)

        if colors:
            sorted_colors = sorted(colors, key=lambda x: x[0], reverse=True)
            dominant = [c[1] for c in sorted_colors[:5]]
        else:
            dominant = [(128, 128, 128)]

        return {
            'type': 'sprite' if image.width < 64 else 'background',
            'colors': [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in dominant],
            'subject': 'pixel art asset',
            'style': config.prompt_style,
            'size': (image.width, image.height),
        }

    def _assess_detail_change(self, mode: ConversionMode) -> str:
        """Assess how detail changed in conversion."""
        return {
            ConversionMode.UPSCALE: "increased",
            ConversionMode.DOWNSCALE: "decreased",
            ConversionMode.ADAPT: "maintained",
            ConversionMode.REGENERATE: "regenerated",
        }.get(mode, "unknown")

    def _assess_color_change(self, source: int, target: int) -> str:
        """Assess how colors changed."""
        if target > source * 1.5:
            return "expanded"
        elif target < source * 0.5:
            return "reduced"
        else:
            return "maintained"

    # -------------------------------------------------------------------------
    # Output Methods
    # -------------------------------------------------------------------------

    def save_conversion_result(
        self,
        result: ConversionResult,
        output_dir: str,
        name: str = "converted",
    ) -> Dict[str, str]:
        """Save conversion result to files."""

        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        files = {}

        # Save converted image
        if result.converted_image:
            img_path = out_path / f"{name}_{result.target_platform}.png"
            result.converted_image.save(img_path)
            files['converted'] = str(img_path)

        # Save source for reference
        if result.source_image:
            src_path = out_path / f"{name}_{result.source_platform}_source.png"
            result.source_image.save(src_path)
            files['source'] = str(src_path)

        # Save metadata
        meta = {
            'source_platform': result.source_platform,
            'target_platform': result.target_platform,
            'conversion_mode': result.conversion_mode.value,
            'source_resolution': result.source_resolution,
            'target_resolution': result.target_resolution,
            'source_colors': result.source_colors,
            'target_colors': result.target_colors,
            'detail_change': result.detail_change,
            'color_change': result.color_change,
            'validation_passed': result.validation_passed,
            'warnings': result.warnings,
        }

        meta_path = out_path / f"{name}_conversion.json"
        with open(meta_path, 'w') as f:
            json.dump(meta, f, indent=2)
        files['metadata'] = str(meta_path)

        result.files = files
        return files

    def save_tier_result(
        self,
        result: TierGenerationResult,
        output_dir: str,
        name: str = "asset",
    ) -> Dict[str, str]:
        """Save tier generation result to files."""

        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        files = {}

        # Save master
        if result.master_image:
            master_path = out_path / f"{name}_master_{result.tier.value}.png"
            result.master_image.save(master_path)
            files['master'] = str(master_path)

        # Save platform variants
        for platform, variant in result.platform_variants.items():
            variant_path = out_path / f"{name}_{platform}.png"
            variant.save(variant_path)
            files[f'variant_{platform}'] = str(variant_path)

        # Save metadata
        meta = {
            'tier': result.tier.value,
            'base_resolution': result.base_resolution,
            'base_colors': result.base_colors,
            'platforms': list(result.platform_variants.keys()),
            'validation': result.platform_validation,
            'warnings': result.warnings,
        }

        meta_path = out_path / f"{name}_tier_generation.json"
        with open(meta_path, 'w') as f:
            json.dump(meta, f, indent=2)
        files['metadata'] = str(meta_path)

        result.files = files
        return files


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    """Command-line interface for cross-generation conversion."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Cross-generation asset converter'
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Convert command
    convert_parser = subparsers.add_parser('convert', help='Convert asset between platforms')
    convert_parser.add_argument('input', help='Input image file')
    convert_parser.add_argument('-o', '--output', required=True, help='Output directory')
    convert_parser.add_argument('--from', dest='source', required=True,
                               help='Source platform (nes, genesis, snes, gb)')
    convert_parser.add_argument('--to', dest='target', required=True,
                               help='Target platform')
    convert_parser.add_argument('--description', default='',
                               help='Asset description for AI context')

    # Upscale command
    upscale_parser = subparsers.add_parser('upscale', help='Upscale 8-bit to 16-bit')
    upscale_parser.add_argument('input', help='Input image file')
    upscale_parser.add_argument('-o', '--output', required=True, help='Output directory')
    upscale_parser.add_argument('--from', dest='source', default='nes',
                               help='Source platform (default: nes)')
    upscale_parser.add_argument('--to', dest='target', default='genesis',
                               help='Target platform (default: genesis)')
    upscale_parser.add_argument('--scale', type=int, default=2,
                               help='Scale factor (1, 2, or 4)')
    upscale_parser.add_argument('--description', default='',
                               help='Asset description')

    # Downscale command
    downscale_parser = subparsers.add_parser('downscale', help='Downscale 16-bit to 8-bit')
    downscale_parser.add_argument('input', help='Input image file')
    downscale_parser.add_argument('-o', '--output', required=True, help='Output directory')
    downscale_parser.add_argument('--from', dest='source', default='genesis',
                                 help='Source platform (default: genesis)')
    downscale_parser.add_argument('--to', dest='target', default='nes',
                                 help='Target platform (default: nes)')
    downscale_parser.add_argument('--description', default='',
                                 help='Asset description')

    # Generate tier command
    tier_parser = subparsers.add_parser('generate', help='Generate at tier for multi-platform')
    tier_parser.add_argument('description', help='Asset description')
    tier_parser.add_argument('-o', '--output', required=True, help='Output directory')
    tier_parser.add_argument('--tier', default='16bit',
                            choices=['8bit', '16bit', '32bit', 'best'],
                            help='Generation tier')
    tier_parser.add_argument('--type', default='sprite',
                            choices=['sprite', 'background', 'tile'],
                            help='Asset type')
    tier_parser.add_argument('--platforms', nargs='+',
                            default=['nes', 'genesis'],
                            help='Target platforms')
    tier_parser.add_argument('--size', type=int, nargs=2,
                            metavar=('W', 'H'),
                            help='Override asset size')

    args = parser.parse_args()

    converter = CrossGenConverter()

    if args.command == 'convert':
        image = Image.open(args.input)
        result = converter.convert(
            image=image,
            source_platform=args.source,
            target_platform=args.target,
            description=args.description,
        )

        name = Path(args.input).stem
        files = converter.save_conversion_result(result, args.output, name)

        print(f"Conversion: {args.source} → {args.target}")
        print(f"Mode: {result.conversion_mode.value}")
        print(f"Resolution: {result.source_resolution} → {result.target_resolution}")
        print(f"Colors: {result.source_colors} → {result.target_colors}")
        print(f"Valid: {result.validation_passed}")
        print(f"\nFiles:")
        for k, v in files.items():
            print(f"  {k}: {v}")

    elif args.command == 'upscale':
        image = Image.open(args.input)
        result = converter.upscale_to_16bit(
            image=image,
            source_platform=args.source,
            target_platform=args.target,
            description=args.description,
            scale_factor=args.scale,
        )

        name = Path(args.input).stem
        files = converter.save_conversion_result(result, args.output, name)

        print(f"Upscaled: {args.source} → {args.target}")
        print(f"Resolution: {result.source_resolution} → {result.target_resolution}")
        print(f"Colors: {result.source_colors} → {result.target_colors}")

    elif args.command == 'downscale':
        image = Image.open(args.input)
        result = converter.downscale_to_8bit(
            image=image,
            source_platform=args.source,
            target_platform=args.target,
            description=args.description,
        )

        name = Path(args.input).stem
        files = converter.save_conversion_result(result, args.output, name)

        print(f"Downscaled: {args.source} → {args.target}")
        print(f"Resolution: {result.source_resolution} → {result.target_resolution}")
        print(f"Colors: {result.source_colors} → {result.target_colors}")

    elif args.command == 'generate':
        tier = GenerationTier(args.tier)
        size = tuple(args.size) if args.size else None

        result = converter.generate_for_tier(
            description=args.description,
            tier=tier,
            asset_type=args.type,
            size=size,
            target_platforms=args.platforms,
        )

        files = converter.save_tier_result(result, args.output, 'asset')

        print(f"Generated at tier: {tier.value}")
        print(f"Platforms: {', '.join(result.platform_variants.keys())}")
        print(f"Base resolution: {result.base_resolution}")
        print(f"Base colors: {result.base_colors}")
        print(f"\nFiles:")
        for k, v in files.items():
            print(f"  {k}: {v}")

        if result.warnings:
            print(f"\nWarnings:")
            for w in result.warnings:
                print(f"  - {w}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
