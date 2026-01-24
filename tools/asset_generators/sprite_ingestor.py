"""
Sprite Ingestor - Bridge between AI generation and sprite processing pipeline.

This module ensures generated sprites can be properly ingested by unified_pipeline.py
and that the processing pipeline outputs can be used by the generators for refinement.

Workflow:
1. Generator creates high-tier source assets
2. Ingestor validates and prepares for processing
3. unified_pipeline.py processes to target platform format
4. Ingestor verifies output and provides feedback for regeneration if needed

Key Features:
- Validates AI-generated sprites against tier constraints
- Prepares sprite sheets for unified_pipeline consumption
- Handles tier-based downsampling with platform-specific palettes
- Creates intermediate formats for pipeline handoff
- Collects processing results back into generator manifest
"""

import json
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
from enum import Enum

try:
    from PIL import Image, ImageEnhance, ImageFilter
    import numpy as np
except ImportError:
    raise ImportError("PIL and numpy required: pip install pillow numpy")

from .tier_system import (
    HardwareTier, TIER_SPECS,
    get_tier_for_platform, get_generation_tier,
    get_downsample_config, DownsampleConfig,
    # Platform-specific palette handling
    PlatformPaletteConfig,
    get_platform_palette_config,
    get_nearest_palette_color,
)


# =============================================================================
# Ingestion Status
# =============================================================================

class IngestionStatus(Enum):
    """Status of sprite ingestion."""
    PENDING = "pending"
    VALIDATED = "validated"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    NEEDS_REGENERATION = "needs_regeneration"


@dataclass
class ValidationResult:
    """Result of validating a sprite against tier constraints."""

    valid: bool
    tier: HardwareTier
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    # Detected properties
    detected_colors: int = 0
    detected_size: Tuple[int, int] = (0, 0)
    has_transparency: bool = False

    # Recommendations
    suggested_fixes: List[str] = field(default_factory=list)


@dataclass
class IngestionManifest:
    """Manifest for tracking sprites through the pipeline."""

    source_file: str
    source_tier: HardwareTier
    target_platforms: List[str]

    # Processing status per platform
    platform_status: Dict[str, IngestionStatus] = field(default_factory=dict)

    # Output files per platform
    platform_outputs: Dict[str, Dict[str, str]] = field(default_factory=dict)

    # Validation results
    validation: Optional[ValidationResult] = None

    # Metadata
    asset_type: str = "sprite"  # sprite, background, tile
    animation_name: Optional[str] = None
    frame_index: Optional[int] = None

    # Hash for change detection
    content_hash: str = ""


# =============================================================================
# Sprite Ingestor
# =============================================================================

class SpriteIngestor:
    """
    Bridge between AI generation and sprite processing pipeline.

    Validates generated sprites, prepares them for processing, and
    manages the handoff between generation and processing stages.
    """

    def __init__(self, output_dir: str = "output"):
        """Initialize ingestor with output directory."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Cache for processed sprites
        self._cache_dir = self.output_dir / ".cache"
        self._cache_dir.mkdir(exist_ok=True)

        # Manifests for tracking
        self.manifests: Dict[str, IngestionManifest] = {}

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def validate_sprite(
        self,
        image: Union[Image.Image, str, Path],
        target_tier: HardwareTier,
        asset_type: str = "sprite",
    ) -> ValidationResult:
        """
        Validate a sprite against tier constraints.

        Args:
            image: PIL Image or path to image file
            target_tier: Target hardware tier
            asset_type: "sprite", "background", or "tile"

        Returns:
            ValidationResult with validation status and recommendations
        """
        if isinstance(image, (str, Path)):
            image = Image.open(image)

        spec = TIER_SPECS[target_tier]
        result = ValidationResult(valid=True, tier=target_tier)

        # Detect colors
        if image.mode == 'P':
            colors = len(image.getpalette()) // 3
        else:
            # Count unique colors
            arr = np.array(image.convert('RGB'))
            unique = len(np.unique(arr.reshape(-1, 3), axis=0))
            colors = unique

        result.detected_colors = colors
        result.detected_size = image.size

        # Check transparency
        if image.mode in ('RGBA', 'LA', 'PA'):
            alpha = image.split()[-1]
            has_transparent = np.array(alpha).min() < 255
            result.has_transparency = has_transparent
        elif image.mode == 'P' and 'transparency' in image.info:
            result.has_transparency = True

        # Validate against tier constraints
        if asset_type == "sprite":
            max_colors = spec.max_sprite_colors + 1  # +1 for transparent
            max_size = spec.max_sprite_size

            if colors > max_colors:
                result.warnings.append(
                    f"Color count ({colors}) exceeds tier limit ({max_colors}). "
                    f"Will be reduced during processing."
                )

            if image.width > max_size[0] or image.height > max_size[1]:
                result.warnings.append(
                    f"Size ({image.width}x{image.height}) exceeds tier max "
                    f"({max_size[0]}x{max_size[1]}). Consider splitting into metasprite."
                )

            # Check if size is tile-aligned
            tile_w, tile_h = spec.tile_size
            if image.width % tile_w != 0 or image.height % tile_h != 0:
                result.warnings.append(
                    f"Size not aligned to {tile_w}x{tile_h} tile grid. "
                    f"Will be padded during processing."
                )

        elif asset_type == "background":
            max_tiles = spec.max_unique_tiles

            # Estimate tile count
            tile_w, tile_h = spec.tile_size
            tiles_x = (image.width + tile_w - 1) // tile_w
            tiles_y = (image.height + tile_h - 1) // tile_h
            estimated_tiles = tiles_x * tiles_y

            if estimated_tiles > max_tiles:
                result.warnings.append(
                    f"Estimated tiles ({estimated_tiles}) may exceed limit ({max_tiles}). "
                    f"Deduplication will be applied."
                )

        # Check for problematic patterns
        if not spec.anti_aliasing_allowed:
            # Check for anti-aliasing (many similar colors)
            if colors > spec.total_colors * 2:
                result.warnings.append(
                    "Sprite appears to have anti-aliasing. "
                    "This tier requires hard pixel edges."
                )
                result.suggested_fixes.append(
                    "Regenerate with 'no anti-aliasing' in prompt"
                )

        if not spec.gradient_allowed:
            # Simple gradient detection (many brightness levels)
            if image.mode in ('RGB', 'RGBA'):
                gray = image.convert('L')
                gray_arr = np.array(gray)
                unique_grays = len(np.unique(gray_arr))
                if unique_grays > spec.colors_per_palette * 4:
                    result.warnings.append(
                        "Sprite appears to have gradients. "
                        "This tier requires flat colors."
                    )

        # Determine if valid (errors are fatal, warnings are not)
        result.valid = len(result.errors) == 0

        return result

    # -------------------------------------------------------------------------
    # Preparation for Processing
    # -------------------------------------------------------------------------

    def prepare_for_pipeline(
        self,
        image: Union[Image.Image, str, Path],
        target_platforms: List[str],
        asset_name: str,
        asset_type: str = "sprite",
    ) -> IngestionManifest:
        """
        Prepare a generated sprite for processing by unified_pipeline.

        Args:
            image: PIL Image or path
            target_platforms: List of target platform names
            asset_name: Name for the asset
            asset_type: "sprite", "background", "tile"

        Returns:
            IngestionManifest tracking the asset through processing
        """
        if isinstance(image, (str, Path)):
            source_path = str(image)
            image = Image.open(image)
        else:
            # Save temporary file for pipeline
            source_path = str(self._cache_dir / f"{asset_name}_source.png")
            image.save(source_path)

        # Determine source tier (highest among targets)
        source_tier = get_generation_tier(target_platforms)

        # Validate against source tier
        validation = self.validate_sprite(image, source_tier, asset_type)

        # Create manifest
        manifest = IngestionManifest(
            source_file=source_path,
            source_tier=source_tier,
            target_platforms=target_platforms,
            validation=validation,
            asset_type=asset_type,
            content_hash=self._compute_hash(image),
        )

        # Initialize platform status
        for platform in target_platforms:
            manifest.platform_status[platform] = IngestionStatus.PENDING

        # Store manifest
        self.manifests[asset_name] = manifest

        return manifest

    def create_platform_variants(
        self,
        manifest: IngestionManifest,
        asset_name: str,
    ) -> Dict[str, str]:
        """
        Create platform-specific variants for processing.

        This handles tier-based downsampling with platform-specific
        palette allocation.

        Args:
            manifest: Ingestion manifest
            asset_name: Asset name

        Returns:
            Dict mapping platform to prepared file path
        """
        source_image = Image.open(manifest.source_file)
        variant_paths = {}

        for platform in manifest.target_platforms:
            target_tier = get_tier_for_platform(platform)

            # Get downsample config if needed
            if manifest.source_tier > target_tier:
                config = get_downsample_config(manifest.source_tier, target_tier)
                variant = self._downsample_sprite(source_image, config, target_tier, platform)
            else:
                variant = source_image.copy()

            # Apply platform-specific adjustments (bespoke palette reallocation)
            variant = self._apply_platform_adjustments(variant, platform, target_tier)

            # Save variant
            variant_path = self._cache_dir / f"{asset_name}_{platform}.png"
            variant.save(variant_path)
            variant_paths[platform] = str(variant_path)

            manifest.platform_status[platform] = IngestionStatus.VALIDATED

        return variant_paths

    # -------------------------------------------------------------------------
    # Downsampling
    # -------------------------------------------------------------------------

    def _downsample_sprite(
        self,
        image: Image.Image,
        config: DownsampleConfig,
        target_tier: HardwareTier,
        platform: Optional[str] = None,
    ) -> Image.Image:
        """
        Downsample sprite according to configuration with bespoke per-platform handling.

        Args:
            image: Source image
            config: Downsample configuration
            target_tier: Target tier for constraints
            platform: Optional specific platform for palette constraints

        Returns:
            Downsampled image
        """
        spec = TIER_SPECS[target_tier]
        result = image.copy()

        # Get platform-specific palette config if available
        palette_config = get_platform_palette_config(platform) if platform else None

        # Resize if needed
        max_size = spec.max_sprite_size
        if result.width > max_size[0] or result.height > max_size[1]:
            # Calculate new size maintaining aspect ratio
            scale = min(max_size[0] / result.width, max_size[1] / result.height)
            new_size = (int(result.width * scale), int(result.height * scale))

            # Round to tile size
            tile_w, tile_h = spec.tile_size
            new_size = (
                ((new_size[0] + tile_w - 1) // tile_w) * tile_w,
                ((new_size[1] + tile_h - 1) // tile_h) * tile_h,
            )

            # Apply resize
            resample = {
                'NEAREST': Image.NEAREST,
                'LANCZOS': Image.LANCZOS,
                'BILINEAR': Image.BILINEAR,
            }.get(config.resize_method, Image.NEAREST)

            result = result.resize(new_size, resample)

        # Preserve transparency
        has_alpha = result.mode in ('RGBA', 'LA', 'PA')
        if has_alpha:
            alpha = result.split()[-1]
            rgb = result.convert('RGB')
        else:
            rgb = result.convert('RGB')
            alpha = None

        # Apply saturation boost if configured
        saturation_boost = getattr(config, 'saturation_boost', 1.0)
        if saturation_boost != 1.0:
            enhancer = ImageEnhance.Color(rgb)
            rgb = enhancer.enhance(saturation_boost)

        # Apply contrast boost if configured
        if config.contrast_boost != 1.0:
            enhancer = ImageEnhance.Contrast(rgb)
            rgb = enhancer.enhance(config.contrast_boost)

        # Sharpen after resize if configured
        if config.sharpen_after_resize:
            rgb = rgb.filter(ImageFilter.SHARPEN)

        # Determine max colors for this platform/tier
        if palette_config:
            max_colors = palette_config.colors_per_subpalette
        else:
            max_colors = spec.max_sprite_colors + 1  # +1 for transparent

        # Check if we should use hardware palette mapping
        use_hardware = getattr(config, 'use_hardware_palette', False)
        matching_method = getattr(config, 'palette_matching_method', 'euclidean')

        if use_hardware and palette_config and palette_config.hardware_palette:
            # Map to hardware palette using bespoke color matching
            result = self._map_to_hardware_palette(
                rgb, palette_config, max_colors, matching_method
            )
        else:
            # Standard quantization
            method = {
                'median_cut': Image.MEDIANCUT,
                'octree': Image.FASTOCTREE,
                'k_means': Image.MEDIANCUT,  # PIL doesn't have k-means, use median
            }.get(config.color_reduction, Image.MEDIANCUT)

            # Apply dithering if configured
            dither_flag = 0
            if config.apply_dithering and config.dither_method == 'floyd_steinberg':
                dither_flag = 1

            quantized = rgb.quantize(colors=max_colors, method=method, dither=dither_flag)

            # Apply ordered dithering manually if requested
            if config.apply_dithering and config.dither_method == 'ordered':
                result = self._apply_ordered_dithering(
                    rgb, quantized, config.dither_strength
                )
            else:
                result = quantized.convert('RGB')

        # Restore alpha if present
        if alpha is not None:
            if result.mode != 'RGBA':
                result = result.convert('RGBA')
            result.putalpha(alpha)

        return result

    def _map_to_hardware_palette(
        self,
        image: Image.Image,
        palette_config: PlatformPaletteConfig,
        max_colors: int,
        matching_method: str,
    ) -> Image.Image:
        """
        Map image colors to a platform's hardware palette.

        This is the bespoke per-platform palette reallocation.
        """
        hardware_palette = palette_config.hardware_palette
        if not hardware_palette:
            return image

        arr = np.array(image.convert('RGB'))
        height, width, _ = arr.shape

        # First, reduce to max_colors using quantization
        quantized = image.convert('RGB').quantize(colors=max_colors, method=Image.MEDIANCUT)
        quant_palette = quantized.getpalette()[:max_colors * 3]

        # Map each quantized color to nearest hardware color
        color_map = {}
        for i in range(max_colors):
            src_color = (quant_palette[i*3], quant_palette[i*3+1], quant_palette[i*3+2])
            hw_idx = get_nearest_palette_color(src_color, hardware_palette, matching_method)
            color_map[i] = hardware_palette[hw_idx]

        # Apply the mapping
        quant_arr = np.array(quantized)
        result_arr = np.zeros((height, width, 3), dtype=np.uint8)

        for idx, new_color in color_map.items():
            mask = quant_arr == idx
            result_arr[mask] = new_color

        return Image.fromarray(result_arr)

    def _apply_ordered_dithering(
        self,
        original: Image.Image,
        quantized: Image.Image,
        strength: float,
    ) -> Image.Image:
        """
        Apply ordered (Bayer) dithering for retro-appropriate pattern dithering.
        """
        # 4x4 Bayer matrix normalized to 0-1
        bayer_4x4 = np.array([
            [0,  8,  2, 10],
            [12, 4, 14,  6],
            [3, 11,  1,  9],
            [15, 7, 13,  5],
        ]) / 16.0

        orig_arr = np.array(original.convert('RGB')).astype(np.float32)
        quant_arr = np.array(quantized.convert('RGB')).astype(np.float32)

        height, width, _ = orig_arr.shape

        # Tile the Bayer matrix
        bayer_tiled = np.tile(bayer_4x4, (height // 4 + 1, width // 4 + 1))[:height, :width]
        bayer_tiled = np.stack([bayer_tiled] * 3, axis=-1)

        # Calculate error and apply dithering threshold
        error = orig_arr - quant_arr
        threshold = (bayer_tiled - 0.5) * strength * 64

        # Add dithered error
        result = quant_arr + np.where(np.abs(error) > np.abs(threshold), np.sign(error) * 32, 0)
        result = np.clip(result, 0, 255).astype(np.uint8)

        return Image.fromarray(result)

    def _apply_platform_adjustments(
        self,
        image: Image.Image,
        platform: str,
        tier: HardwareTier,
    ) -> Image.Image:
        """
        Apply platform-specific color encoding and constraints.

        Uses bespoke per-platform palette configuration for accurate conversion.
        """
        palette_config = get_platform_palette_config(platform)
        if not palette_config:
            # Fallback to basic tier-based adjustment
            return self._apply_basic_tier_adjustment(image, tier)

        result = image.copy()

        # Handle grayscale platforms (Game Boy)
        if palette_config.color_format == 'GRAY':
            return self._convert_to_grayscale_platform(result, palette_config)

        # Apply color bit depth reduction
        if result.mode in ('RGB', 'RGBA'):
            has_alpha = result.mode == 'RGBA'
            if has_alpha:
                alpha = result.split()[-1]
                rgb = result.convert('RGB')
            else:
                rgb = result
                alpha = None

            # Apply platform color encoding (bit depth reduction)
            arr = np.array(rgb)
            bits = palette_config.bits_per_channel

            # Quantize each channel to platform bit depth
            shift = 8 - bits
            arr = ((arr >> shift) << shift)

            # Fill lower bits for proper display
            if bits < 8:
                arr = arr | (arr >> bits)

            result = Image.fromarray(arr.astype(np.uint8))

            # Handle BGR platforms (Genesis, SNES, GBA)
            if palette_config.color_format == 'BGR':
                # Swap R and B channels for internal representation
                arr = np.array(result)
                arr = arr[:, :, ::-1]  # RGB to BGR
                arr = arr[:, :, ::-1]  # BGR back to RGB for display
                # Note: Actual BGR encoding happens at export time

            # Restore alpha
            if alpha is not None:
                result = result.convert('RGBA')
                result.putalpha(alpha)

        # Apply platform-specific palette mapping if hardware palette exists
        if palette_config.hardware_palette and result.mode in ('RGB', 'P'):
            result = self._enforce_hardware_palette(result, palette_config)

        return result

    def _apply_basic_tier_adjustment(
        self,
        image: Image.Image,
        tier: HardwareTier,
    ) -> Image.Image:
        """Fallback basic adjustment when no platform config exists."""
        spec = TIER_SPECS[tier]
        result = image.copy()

        # Basic color reduction based on tier
        if result.mode == 'RGB':
            bits = spec.color_depth_bits
            if bits < 8:
                arr = np.array(result)
                shift = 8 - min(bits, 8)
                arr = ((arr >> shift) << shift)
                result = Image.fromarray(arr.astype(np.uint8))

        return result

    def _convert_to_grayscale_platform(
        self,
        image: Image.Image,
        config: PlatformPaletteConfig,
    ) -> Image.Image:
        """Convert image to grayscale for platforms like Game Boy."""
        # Convert to grayscale
        gray = image.convert('L')

        if config.hardware_palette:
            # Map to hardware grayscale palette
            num_shades = len(config.hardware_palette)
            quantized = gray.quantize(colors=num_shades, method=Image.MEDIANCUT)

            # Create palette image with hardware colors
            hw_palette = []
            for color in config.hardware_palette:
                hw_palette.extend(color)
            # Pad to 256 colors
            hw_palette.extend([0, 0, 0] * (256 - num_shades))

            quantized.putpalette(hw_palette)
            return quantized.convert('RGB')
        else:
            # Simple quantization
            return gray.quantize(colors=config.total_palette_colors)

    def _enforce_hardware_palette(
        self,
        image: Image.Image,
        config: PlatformPaletteConfig,
    ) -> Image.Image:
        """Ensure all colors in image are from hardware palette."""
        if not config.hardware_palette:
            return image

        arr = np.array(image.convert('RGB'))
        height, width, _ = arr.shape

        # Map each pixel to nearest hardware color
        result_arr = np.zeros_like(arr)
        flat_arr = arr.reshape(-1, 3)

        # Use vectorized nearest color lookup for efficiency
        for i, pixel in enumerate(flat_arr):
            hw_idx = get_nearest_palette_color(
                tuple(pixel), config.hardware_palette, 'weighted_luminance'
            )
            flat_arr[i] = config.hardware_palette[hw_idx]

        result_arr = flat_arr.reshape(height, width, 3)
        return Image.fromarray(result_arr)

    # -------------------------------------------------------------------------
    # Pipeline Integration
    # -------------------------------------------------------------------------

    def invoke_pipeline(
        self,
        manifest: IngestionManifest,
        variant_paths: Dict[str, str],
        output_base: str,
    ) -> Dict[str, Dict[str, str]]:
        """
        Invoke unified_pipeline.py for each platform variant.

        Args:
            manifest: Ingestion manifest
            variant_paths: Dict of platform -> variant file path
            output_base: Base output directory

        Returns:
            Dict of platform -> output files dict
        """
        import subprocess
        import sys

        results = {}

        for platform, variant_path in variant_paths.items():
            manifest.platform_status[platform] = IngestionStatus.PROCESSING

            # Output directory for this platform
            platform_output = Path(output_base) / platform
            platform_output.mkdir(parents=True, exist_ok=True)

            # Invoke pipeline with specific model to ensure quality
            # Use openai-large (GPT-5.2) for reliable detection as per debug findings
            pipeline_config = UnifiedPipelineConfig(
                input_path=variant_path,
                output_path=str(platform_output),
                platform=platform,
                use_ai=True,
                ai_provider="pollinations", # This will now default to openai-large inside unified_pipeline
                no_ai=False, # Ensure AI is used
            )
            pipeline = UnifiedPipeline(pipeline_config)

            try:
                pipeline_result = pipeline.run()

                if pipeline_result.success:
                    manifest.platform_status[platform] = IngestionStatus.PROCESSED

                    # Find output files
                    outputs = {}
                    for f in platform_output.iterdir():
                        if f.is_file():
                            ext = f.suffix.lower()
                            outputs[ext] = str(f)

                    manifest.platform_outputs[platform] = outputs
                    results[platform] = outputs

                else:
                    manifest.platform_status[platform] = IngestionStatus.FAILED
                    results[platform] = {'error': result.stderr}

            except subprocess.TimeoutExpired:
                manifest.platform_status[platform] = IngestionStatus.FAILED
                results[platform] = {'error': 'Pipeline timeout'}

            except Exception as e:
                manifest.platform_status[platform] = IngestionStatus.FAILED
                results[platform] = {'error': str(e)}

        return results

    def process_generated_sprite(
        self,
        image: Union[Image.Image, str, Path],
        asset_name: str,
        target_platforms: List[str],
        output_dir: str,
        asset_type: str = "sprite",
    ) -> Dict[str, Any]:
        """
        Complete workflow: prepare, create variants, process, collect results.

        This is the main entry point for processing AI-generated sprites.

        Args:
            image: Source image (high-tier)
            asset_name: Asset name
            target_platforms: List of target platforms
            output_dir: Output directory
            asset_type: "sprite", "background", "tile"

        Returns:
            Dict with processing results
        """
        # Prepare manifest
        manifest = self.prepare_for_pipeline(
            image, target_platforms, asset_name, asset_type
        )

        # Check validation
        if manifest.validation and not manifest.validation.valid:
            return {
                'success': False,
                'errors': manifest.validation.errors,
                'warnings': manifest.validation.warnings,
                'manifest': manifest,
            }

        # Create platform variants
        variant_paths = self.create_platform_variants(manifest, asset_name)

        # Process through pipeline
        results = self.invoke_pipeline(manifest, variant_paths, output_dir)

        # Collect summary
        success_count = sum(
            1 for s in manifest.platform_status.values()
            if s == IngestionStatus.PROCESSED
        )

        return {
            'success': success_count == len(target_platforms),
            'processed': success_count,
            'total': len(target_platforms),
            'platform_results': results,
            'warnings': manifest.validation.warnings if manifest.validation else [],
            'manifest': manifest,
        }

    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------

    def _compute_hash(self, image: Image.Image) -> str:
        """Compute content hash for an image."""
        arr = np.array(image)
        return hashlib.md5(arr.tobytes()).hexdigest()

    def save_manifest(self, asset_name: str, output_path: str) -> None:
        """Save manifest to JSON file."""
        if asset_name not in self.manifests:
            return

        manifest = self.manifests[asset_name]

        data = {
            'source_file': manifest.source_file,
            'source_tier': manifest.source_tier.name,
            'target_platforms': manifest.target_platforms,
            'asset_type': manifest.asset_type,
            'content_hash': manifest.content_hash,
            'platform_status': {
                p: s.value for p, s in manifest.platform_status.items()
            },
            'platform_outputs': manifest.platform_outputs,
            'validation': {
                'valid': manifest.validation.valid,
                'detected_colors': manifest.validation.detected_colors,
                'detected_size': manifest.validation.detected_size,
                'warnings': manifest.validation.warnings,
                'errors': manifest.validation.errors,
            } if manifest.validation else None,
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

    def load_manifest(self, path: str) -> Optional[IngestionManifest]:
        """Load manifest from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)

        manifest = IngestionManifest(
            source_file=data['source_file'],
            source_tier=HardwareTier[data['source_tier']],
            target_platforms=data['target_platforms'],
            asset_type=data.get('asset_type', 'sprite'),
            content_hash=data.get('content_hash', ''),
        )

        manifest.platform_status = {
            p: IngestionStatus(s)
            for p, s in data.get('platform_status', {}).items()
        }
        manifest.platform_outputs = data.get('platform_outputs', {})

        if data.get('validation'):
            v = data['validation']
            manifest.validation = ValidationResult(
                valid=v['valid'],
                tier=manifest.source_tier,
                detected_colors=v.get('detected_colors', 0),
                detected_size=tuple(v.get('detected_size', (0, 0))),
                warnings=v.get('warnings', []),
                errors=v.get('errors', []),
            )

        return manifest


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    """Command-line interface for sprite ingestion."""
    import argparse

    parser = argparse.ArgumentParser(
        description='ARDK Sprite Ingestor - Bridge generation and processing'
    )
    parser.add_argument('input', help='Input sprite image')
    parser.add_argument('-o', '--output', required=True, help='Output directory')
    parser.add_argument('--name', help='Asset name (default: input filename)')
    parser.add_argument('--platforms', nargs='+', required=True,
                       help='Target platforms')
    parser.add_argument('--type', choices=['sprite', 'background', 'tile'],
                       default='sprite', help='Asset type')
    parser.add_argument('--validate-only', action='store_true',
                       help='Only validate, do not process')

    args = parser.parse_args()

    asset_name = args.name or Path(args.input).stem

    ingestor = SpriteIngestor(args.output)

    if args.validate_only:
        # Just validate
        source_tier = get_generation_tier(args.platforms)
        result = ingestor.validate_sprite(args.input, source_tier, args.type)

        print(f"Validation Result: {'VALID' if result.valid else 'INVALID'}")
        print(f"Tier: {result.tier.name}")
        print(f"Colors: {result.detected_colors}")
        print(f"Size: {result.detected_size[0]}x{result.detected_size[1]}")

        if result.warnings:
            print("\nWarnings:")
            for w in result.warnings:
                print(f"  - {w}")

        if result.errors:
            print("\nErrors:")
            for e in result.errors:
                print(f"  - {e}")

    else:
        # Full processing
        print(f"Processing: {args.input}")
        print(f"Targets: {', '.join(args.platforms)}")
        print()

        result = ingestor.process_generated_sprite(
            args.input,
            asset_name,
            args.platforms,
            args.output,
            args.type,
        )

        print(f"\nProcessed: {result['processed']}/{result['total']} platforms")

        if result['warnings']:
            print("\nWarnings:")
            for w in result['warnings']:
                print(f"  - {w}")

        if not result['success']:
            print("\nFailed platforms:")
            for platform, data in result['platform_results'].items():
                if 'error' in data:
                    print(f"  {platform}: {data['error']}")

        # Save manifest
        manifest_path = Path(args.output) / f"{asset_name}_manifest.json"
        ingestor.save_manifest(asset_name, str(manifest_path))
        print(f"\nManifest saved to: {manifest_path}")


if __name__ == '__main__':
    main()
