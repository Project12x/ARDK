"""
Character Sheet Generator - AI-powered character sprite sheet creation.

Generates complete character sheets with:
- Multiple animation sets (minimal, standard, full)
- Per-tier frame counts
- Unified palette across all frames
- Horizontal strip layout per animation
- Proper sprite sizing for target platform
"""

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from io import BytesIO

try:
    from PIL import Image
    import numpy as np
except ImportError:
    raise ImportError("PIL and numpy required: pip install pillow numpy")

from .base_generator import (
    AssetGenerator,
    GeneratedAsset,
    GenerationFlags,
    PlatformConfig,
    get_platform_config,
    validate_asset_for_platform,
)
from .asset_manifest import (
    UnifiedAssetManifest,
    AssetEntry,
    AssetCategory,
    ProcessingStage,
    AnimationEntry as ManifestAnimationEntry,
)
from .tier_system import (
    AssetTier,
    get_generation_tier,
)

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from tile_optimizers import TileDeduplicator


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class AnimationFrame:
    """Single animation frame."""
    image: Image.Image
    duration_ms: int = 100
    hotspot_x: int = 0
    hotspot_y: int = 0


@dataclass
class Animation:
    """Animation sequence."""
    name: str
    frames: List[AnimationFrame]
    loop: bool = True
    frame_rate: int = 12


@dataclass
class CharacterSheet:
    """Complete character with all animations."""
    name: str
    animations: Dict[str, Animation]
    base_size: Tuple[int, int]
    palette: List[int]
    metadata: Dict[str, Any] = field(default_factory=dict)
    chr_data: Optional[bytes] = None
    warnings: List[str] = field(default_factory=list)


# =============================================================================
# Animation Configuration
# =============================================================================

# Animation sets by complexity
ANIMATION_SETS = {
    'minimal': ['idle', 'walk', 'hurt'],
    'standard': ['idle', 'walk', 'attack', 'jump', 'hurt', 'death'],
    'full': ['idle', 'walk', 'run', 'attack_1', 'attack_2', 'jump',
             'fall', 'hurt', 'death', 'special'],
}

# Frame counts per tier and animation
FRAME_COUNTS = {
    # MINIMAL tier (NES, GB)
    ('MINIMAL', 'idle'): 2,
    ('MINIMAL', 'walk'): 4,
    ('MINIMAL', 'run'): 4,
    ('MINIMAL', 'attack'): 2,
    ('MINIMAL', 'attack_1'): 2,
    ('MINIMAL', 'attack_2'): 2,
    ('MINIMAL', 'jump'): 2,
    ('MINIMAL', 'fall'): 1,
    ('MINIMAL', 'hurt'): 1,
    ('MINIMAL', 'death'): 2,
    ('MINIMAL', 'special'): 2,

    # STANDARD tier (Genesis, SNES)
    ('STANDARD', 'idle'): 4,
    ('STANDARD', 'walk'): 6,
    ('STANDARD', 'run'): 6,
    ('STANDARD', 'attack'): 4,
    ('STANDARD', 'attack_1'): 4,
    ('STANDARD', 'attack_2'): 4,
    ('STANDARD', 'jump'): 3,
    ('STANDARD', 'fall'): 2,
    ('STANDARD', 'hurt'): 2,
    ('STANDARD', 'death'): 4,
    ('STANDARD', 'special'): 4,

    # EXTENDED tier (GBA, DS)
    ('EXTENDED', 'idle'): 6,
    ('EXTENDED', 'walk'): 8,
    ('EXTENDED', 'run'): 8,
    ('EXTENDED', 'attack'): 6,
    ('EXTENDED', 'attack_1'): 6,
    ('EXTENDED', 'attack_2'): 6,
    ('EXTENDED', 'jump'): 4,
    ('EXTENDED', 'fall'): 3,
    ('EXTENDED', 'hurt'): 3,
    ('EXTENDED', 'death'): 6,
    ('EXTENDED', 'special'): 6,
}

# Animation descriptions for AI prompts
ANIMATION_DESCRIPTIONS = {
    'idle': "Standing still with subtle breathing/movement. Character at rest, relaxed pose.",
    'walk': "Walking cycle with feet alternating. Natural stride, arms swinging. Should loop seamlessly.",
    'run': "Running cycle, faster and more dynamic than walk. Exaggerated poses, forward lean.",
    'attack': "Melee attack or punch. Wind-up, strike, follow-through phases.",
    'attack_1': "Primary attack. Quick decisive strike motion.",
    'attack_2': "Secondary attack. Different weapon/motion than attack_1.",
    'jump': "Jump sequence: crouch preparation, lift-off, airborne pose.",
    'fall': "Falling/descending pose. Arms/legs positioned for descent.",
    'hurt': "Taking damage. Recoil pose, pained expression, knocked back slightly.",
    'death': "Death sequence. Dramatic collapse to final resting pose.",
    'special': "Special ability activation. Power-up effect, dramatic pose.",
}

# Default timing per animation (ms per frame)
DEFAULT_TIMING = {
    'idle': 150,
    'walk': 100,
    'run': 80,
    'attack': 60,
    'attack_1': 60,
    'attack_2': 70,
    'jump': 100,
    'fall': 100,
    'hurt': 120,
    'death': 150,
    'special': 80,
}


# =============================================================================
# Character Generator
# =============================================================================

class CharacterGenerator(AssetGenerator):
    """Generate character sheets with animation frames."""

    def __init__(
        self,
        platform: PlatformConfig,
        api_key: Optional[str] = None,
    ):
        super().__init__(platform, api_key)
        self.deduplicator = TileDeduplicator(
            tile_width=platform.tile_width,
            tile_height=platform.tile_height,
            colors_per_palette=platform.colors_per_palette,
        )

    def generate(
        self,
        description: str,
        animation_set: str = 'standard',
        sprite_size: Optional[Tuple[int, int]] = None,
        name: str = 'character',
        **kwargs,
    ) -> CharacterSheet:
        """
        Generate complete character sheet.

        Args:
            description: Character description for AI
            animation_set: 'minimal', 'standard', or 'full'
            sprite_size: Override sprite size (width, height)
            name: Character name for output files
            **kwargs: Additional generation options

        Returns:
            CharacterSheet with all animations
        """
        # Determine sprite size
        if sprite_size is None:
            sprite_size = self._get_default_sprite_size()

        # Get animation list for this set
        anim_names = ANIMATION_SETS.get(animation_set, ANIMATION_SETS['standard'])

        # Generate all animations
        animations = {}
        all_frames = []  # Collect all frames for unified palette

        print(f"Generating character: {name}")
        print(f"  Animation set: {animation_set} ({len(anim_names)} animations)")
        print(f"  Sprite size: {sprite_size[0]}x{sprite_size[1]}")

        for anim_name in anim_names:
            frame_count = self._get_frame_count(anim_name)
            print(f"  [{anim_name}] Generating {frame_count} frames...")

            frames = self._generate_animation(
                description=description,
                anim_name=anim_name,
                frame_count=frame_count,
                sprite_size=sprite_size,
            )

            if frames:
                timing = DEFAULT_TIMING.get(anim_name, 100)
                animations[anim_name] = Animation(
                    name=anim_name,
                    frames=frames,
                    loop=anim_name not in ['death', 'hurt'],
                    frame_rate=int(1000 / timing),
                )
                all_frames.extend(frames)

        # Extract unified palette from all frames
        print("  Extracting unified palette...")
        palette = self._extract_unified_palette(all_frames)

        # Build character sheet
        sheet = CharacterSheet(
            name=name,
            animations=animations,
            base_size=sprite_size,
            palette=palette,
            metadata={
                'animation_set': animation_set,
                'platform': self.platform.name,
                'tier': self.platform.tier,
                'total_frames': len(all_frames),
            },
        )

        # Optimize and generate CHR if requested
        sheet = self.optimize(sheet)

        return sheet

    def optimize(self, sheet: CharacterSheet) -> CharacterSheet:
        """
        Optimize character sheet for platform.

        Validates against full platform system limits including:
        - Tile count limits
        - Sprite count limits
        - Color/palette constraints
        """
        if not self.flags.deduplicate_tiles:
            return sheet

        # Combine all frames into single image for optimization
        all_frames = []
        for anim in sheet.animations.values():
            for frame in anim.frames:
                all_frames.append(frame.image)

        if not all_frames:
            return sheet

        # Create combined sheet
        frame_w, frame_h = sheet.base_size
        combined = Image.new('RGBA', (frame_w * len(all_frames), frame_h), (0, 0, 0, 0))

        for i, frame_img in enumerate(all_frames):
            combined.paste(frame_img, (i * frame_w, 0))

        # Run tile optimization
        result = self.deduplicator.optimize(combined, sheet.palette)

        # Validate against platform system limits
        validation = validate_asset_for_platform(
            self.platform.name.lower(),
            tile_count=result.optimized_tile_count,
            colors_used=len(sheet.palette),
            sprite_count=len(all_frames),  # Each frame is a sprite
        )

        # Add validation warnings/errors
        sheet.warnings.extend(validation.get('warnings', []))
        if not validation['valid']:
            sheet.warnings.extend(validation.get('errors', []))

        # Check sprite-specific limits
        valid, msg = self.platform.validate_sprite_count(len(all_frames))
        if msg:
            sheet.warnings.append(msg)

        # Check tile limits
        valid, msg = self.platform.validate_tile_count(result.optimized_tile_count)
        if msg:
            sheet.warnings.append(msg)

        # Generate CHR data
        sheet.chr_data = self.deduplicator.generate_chr(result)

        # Update metadata with validation info
        sheet.metadata['tile_optimization'] = {
            'original_tiles': result.original_tile_count,
            'unique_tiles': result.optimized_tile_count,
            'savings_percent': result.savings_percent,
            'flip_stats': result.flip_stats,
        }
        sheet.metadata['platform_validation'] = {
            'valid': validation['valid'],
            'platform': self.platform.name,
            'tile_limit': self.platform.max_tiles_per_bank,
            'sprite_limit': self.platform.max_sprites,
            'color_limit': self.platform.colors_per_palette,
        }

        if result.warnings:
            sheet.warnings.extend(result.warnings)

        return sheet

    # -------------------------------------------------------------------------
    # Animation Generation
    # -------------------------------------------------------------------------

    def _generate_animation(
        self,
        description: str,
        anim_name: str,
        frame_count: int,
        sprite_size: Tuple[int, int],
    ) -> List[AnimationFrame]:
        """Generate single animation sequence via AI."""

        prompt = self._build_animation_prompt(
            description=description,
            anim_name=anim_name,
            frame_count=frame_count,
            sprite_size=sprite_size,
        )

        # Calculate sheet dimensions
        sheet_width = sprite_size[0] * frame_count
        sheet_height = sprite_size[1]

        # Generate at higher resolution, then downscale
        scale = 4 if self.platform.tier == 'MINIMAL' else 2
        gen_width = sheet_width * scale
        gen_height = sheet_height * scale

        try:
            # Generate sprite strip via Pollinations
            sheet_image = self.client.generate_image(
                prompt=prompt,
                width=gen_width,
                height=gen_height,
                model='flux',
            )

            # Downscale to target size
            sheet_image = self._resize_image(sheet_image, (sheet_width, sheet_height))

            # Split into individual frames
            frames = self._split_frames(sheet_image, frame_count, sprite_size)

            # Get timing
            timing_ms = DEFAULT_TIMING.get(anim_name, 100)

            return [
                AnimationFrame(
                    image=f,
                    duration_ms=timing_ms,
                    hotspot_x=sprite_size[0] // 2,
                    hotspot_y=sprite_size[1],  # Bottom center
                )
                for f in frames
            ]

        except Exception as e:
            print(f"    Warning: Failed to generate {anim_name}: {e}")
            return []

    def _build_animation_prompt(
        self,
        description: str,
        anim_name: str,
        frame_count: int,
        sprite_size: Tuple[int, int],
    ) -> str:
        """Build animation-specific generation prompt."""

        tier = self.platform.tier
        style = self._build_style_prompt()
        anim_desc = ANIMATION_DESCRIPTIONS.get(anim_name, "Animation sequence.")

        return f"""Create a {frame_count}-frame sprite animation strip.

CHARACTER: {description}

ANIMATION: {anim_name.upper()}
{anim_desc}

LAYOUT:
- Horizontal strip: {frame_count} frames side by side
- Each frame: {sprite_size[0]}x{sprite_size[1]} pixels
- Total size: {sprite_size[0] * frame_count}x{sprite_size[1]} pixels
- Transparent background (alpha channel)
- Frames flow left to right showing animation progression

TECHNICAL ({tier} tier):
- Colors: Maximum {self.platform.colors_per_palette} colors (including transparent)
- Style: {style}
- Clean pixel art edges, NO anti-aliasing to transparent areas
- Consistent character size and proportions across ALL frames
- Character should be centered in each frame

IMPORTANT:
- Each frame should show a DIFFERENT pose in the animation sequence
- Animation should flow naturally from frame to frame
- For looping animations, last frame should transition back to first

DO NOT:
- Add text, labels, numbers, or frame indicators
- Include background elements or ground
- Vary character size between frames
- Anti-alias sprite edges to transparent background
- Make all frames look the same
"""

    def _split_frames(
        self,
        sheet: Image.Image,
        frame_count: int,
        sprite_size: Tuple[int, int],
    ) -> List[Image.Image]:
        """Split sprite strip into individual frames."""
        frames = []
        frame_w, frame_h = sprite_size

        for i in range(frame_count):
            x = i * frame_w
            frame = sheet.crop((x, 0, x + frame_w, frame_h))
            frames.append(frame)

        return frames

    # -------------------------------------------------------------------------
    # Palette and Utilities
    # -------------------------------------------------------------------------

    def _extract_unified_palette(
        self,
        frames: List[AnimationFrame],
    ) -> List[int]:
        """Extract unified palette from all animation frames."""
        if not frames:
            return [0x0F, 0x24, 0x2C, 0x30]  # Default synthwave

        # Combine samples from all frames
        combined = Image.new('RGBA', (16 * len(frames), 16), (0, 0, 0, 0))

        for i, frame in enumerate(frames):
            # Sample center of each frame
            sample = frame.image.resize((16, 16), Image.LANCZOS)
            combined.paste(sample, (i * 16, 0))

        # Use AI to extract optimal palette
        return self._extract_palette_ai(combined, self.platform.colors_per_palette)

    def _get_frame_count(self, anim_name: str) -> int:
        """
        Get frame count for animation based on platform system limits.

        Uses the platform's recommended_frames from comprehensive limits,
        falling back to tier-based defaults if not specified.
        """
        # First check platform's recommended frames (from system limits)
        if hasattr(self.platform, 'recommended_frames') and self.platform.recommended_frames:
            # Map animation names to standard names
            name_map = {
                'attack_1': 'attack',
                'attack_2': 'attack',
                'fall': 'jump',
                'special': 'attack',
            }
            lookup_name = name_map.get(anim_name, anim_name)
            if lookup_name in self.platform.recommended_frames:
                return self.platform.recommended_frames[lookup_name]

        # Fall back to tier-based lookup
        key = (self.platform.tier, anim_name)
        return FRAME_COUNTS.get(key, 2)

    def _get_default_sprite_size(self) -> Tuple[int, int]:
        """Get default sprite size for platform."""
        if self.platform.tier == 'MINIMAL':
            return (16, 16)  # NES/GB
        elif self.platform.tier == 'STANDARD':
            return (32, 32)  # Genesis/SNES
        else:
            return (64, 64)  # GBA/DS

    # -------------------------------------------------------------------------
    # Output
    # -------------------------------------------------------------------------

    def save_character(
        self,
        sheet: CharacterSheet,
        output_dir: Path,
    ) -> Dict[str, Path]:
        """
        Save character sheet to files.

        Args:
            sheet: CharacterSheet to save
            output_dir: Output directory

        Returns:
            Dict mapping file type to path
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        outputs = {}

        # Save metadata
        metadata_path = output_dir / 'metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump({
                'name': sheet.name,
                'base_size': sheet.base_size,
                'palette': [f'${c:02X}' for c in sheet.palette],
                'animations': {
                    name: {
                        'frames': len(anim.frames),
                        'loop': anim.loop,
                        'frame_rate': anim.frame_rate,
                    }
                    for name, anim in sheet.animations.items()
                },
                **sheet.metadata,
            }, f, indent=2)
        outputs['metadata'] = metadata_path

        # Save combined sheet image
        if sheet.animations:
            sheet_img = self._create_sheet_image(sheet)
            sheet_path = output_dir / f'{sheet.name}_sheet.png'
            sheet_img.save(sheet_path)
            outputs['sheet'] = sheet_path

        # Save CHR data
        if sheet.chr_data:
            chr_path = output_dir / f'{sheet.name}.chr'
            with open(chr_path, 'wb') as f:
                f.write(sheet.chr_data)
            outputs['chr'] = chr_path

        # Save individual animation strips
        anim_dir = output_dir / 'animations'
        anim_dir.mkdir(exist_ok=True)

        for name, anim in sheet.animations.items():
            if anim.frames:
                strip = self._create_animation_strip(anim, sheet.base_size)
                strip_path = anim_dir / f'{name}.png'
                strip.save(strip_path)
                outputs[f'anim_{name}'] = strip_path

        return outputs

    def _create_sheet_image(self, sheet: CharacterSheet) -> Image.Image:
        """Create combined sprite sheet image."""
        frame_w, frame_h = sheet.base_size

        # Calculate dimensions
        max_frames = max(len(a.frames) for a in sheet.animations.values())
        num_rows = len(sheet.animations)

        width = frame_w * max_frames
        height = frame_h * num_rows

        combined = Image.new('RGBA', (width, height), (0, 0, 0, 0))

        row = 0
        for anim in sheet.animations.values():
            for col, frame in enumerate(anim.frames):
                x = col * frame_w
                y = row * frame_h
                combined.paste(frame.image, (x, y))
            row += 1

        return combined

    def _create_animation_strip(
        self,
        anim: Animation,
        sprite_size: Tuple[int, int],
    ) -> Image.Image:
        """Create horizontal animation strip."""
        frame_w, frame_h = sprite_size
        width = frame_w * len(anim.frames)

        strip = Image.new('RGBA', (width, frame_h), (0, 0, 0, 0))

        for i, frame in enumerate(anim.frames):
            strip.paste(frame.image, (i * frame_w, 0))

        return strip

    # -------------------------------------------------------------------------
    # Manifest Integration
    # -------------------------------------------------------------------------

    def save_to_manifest(
        self,
        sheet: CharacterSheet,
        manifest: UnifiedAssetManifest,
        output_dir: Path,
        target_platforms: Optional[List[str]] = None,
    ) -> AssetEntry:
        """
        Save character to manifest and prepare for pipeline processing.

        This creates processor-compatible output that can be ingested
        by the sprite processing pipeline.

        Args:
            sheet: Generated CharacterSheet
            manifest: Project manifest to add asset to
            output_dir: Output directory
            target_platforms: Override target platforms

        Returns:
            AssetEntry added to manifest
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        platforms = target_platforms or manifest.default_platforms

        # Save the sheet image as source
        sheet_img = self._create_sheet_image(sheet)
        source_path = output_dir / f"{sheet.name}_source.png"
        sheet_img.save(source_path)

        # Add to manifest
        entry = manifest.add_asset(
            name=sheet.name,
            category=AssetCategory.CHARACTER,
            source_file=str(source_path),
            target_platforms=platforms,
            description=sheet.metadata.get('description', ''),
            tags=['character', self.platform.tier.lower()],
            generation_prompt=sheet.metadata.get('prompt', ''),
            generation_model='flux',
        )

        # Add animation entries to manifest
        for anim_name, anim in sheet.animations.items():
            timing_ms = DEFAULT_TIMING.get(anim_name, 100)

            # Save individual animation strip
            strip = self._create_animation_strip(anim, sheet.base_size)
            strip_path = output_dir / 'animations' / f'{anim_name}.png'
            strip_path.parent.mkdir(exist_ok=True)
            strip.save(strip_path)

            # Calculate frame offsets in sheet
            frame_offsets = []
            for i in range(len(anim.frames)):
                frame_offsets.append((i * sheet.base_size[0], 0))

            manifest.add_animation(
                asset_id=entry.asset_id,
                anim_name=anim_name,
                frame_count=len(anim.frames),
                frame_width=sheet.base_size[0],
                frame_height=sheet.base_size[1],
                frame_duration_ms=timing_ms,
                loop=anim.loop,
                frame_files=[str(strip_path)],
                frame_offsets=frame_offsets,
            )

        # Update variant info for each platform
        for platform in platforms:
            manifest.update_variant_stage(
                entry.asset_id,
                platform,
                ProcessingStage.GENERATED,
                dimensions=sheet.base_size,
                colors_used=len(sheet.palette),
            )

        # Save processor-compatible metadata
        self._save_processor_metadata(sheet, entry, output_dir)

        return entry

    def _save_processor_metadata(
        self,
        sheet: CharacterSheet,
        entry: AssetEntry,
        output_dir: Path,
    ) -> None:
        """
        Save metadata in format compatible with unified_pipeline.py.

        This creates the bridge between generator and processor.
        """
        # Create processor-compatible manifest
        processor_manifest = {
            'version': '1.0',
            'generator': 'CharacterGenerator',
            'asset_id': entry.asset_id,
            'asset_type': 'character',

            # Source info
            'source': {
                'file': entry.source_file,
                'tier': entry.generation_tier.name,
                'size': list(sheet.base_size),
            },

            # Palette info (processor needs this)
            'palette': {
                'indices': sheet.palette,
                'hex': [f'${c:02X}' for c in sheet.palette],
                'count': len(sheet.palette),
            },

            # Animation data (processor needs frame layout)
            'animations': {
                name: {
                    'frames': len(anim.frames),
                    'width': sheet.base_size[0],
                    'height': sheet.base_size[1],
                    'timing_ms': DEFAULT_TIMING.get(name, 100),
                    'loop': anim.loop,
                    'strip_file': f'animations/{name}.png',
                }
                for name, anim in sheet.animations.items()
            },

            # Target platforms
            'targets': entry.target_platforms,

            # CHR info if available
            'chr': {
                'available': sheet.chr_data is not None,
                'file': f'{sheet.name}.chr' if sheet.chr_data else None,
                'tiles': sheet.metadata.get('tile_optimization', {}).get('unique_tiles', 0),
            },

            # Processing hints
            'processing_hints': {
                'deduplicate': True,
                'allow_flip': self.flags.use_h_flip or self.flags.use_v_flip,
                'maintain_order': True,  # Keep animation frame order
            },
        }

        # Save processor manifest
        manifest_path = output_dir / f'{sheet.name}_processor.json'
        with open(manifest_path, 'w') as f:
            json.dump(processor_manifest, f, indent=2)

    def generate_for_platforms(
        self,
        description: str,
        target_platforms: List[str],
        name: str = 'character',
        animation_set: str = 'standard',
        manifest: Optional[UnifiedAssetManifest] = None,
        output_dir: Optional[Path] = None,
        **kwargs,
    ) -> Tuple[CharacterSheet, Optional[AssetEntry]]:
        """
        Generate character optimized for highest tier among target platforms.

        This is the preferred entry point for multi-platform generation.

        Args:
            description: Character description
            target_platforms: List of target platform names
            name: Character name
            animation_set: Animation set complexity
            manifest: Optional manifest to add asset to
            output_dir: Output directory (required if manifest provided)
            **kwargs: Additional generation options

        Returns:
            Tuple of (CharacterSheet, AssetEntry if manifest provided)
        """
        # Determine generation tier
        gen_tier = get_generation_tier(target_platforms)

        # Map tier to sprite size
        tier_sizes = {
            AssetTier.MINIMAL: (16, 16),
            AssetTier.MINIMAL_PLUS: (16, 16),
            AssetTier.STANDARD: (32, 32),
            AssetTier.STANDARD_PLUS: (48, 48),
            AssetTier.EXTENDED: (64, 64),
        }
        sprite_size = tier_sizes.get(gen_tier, (32, 32))

        # Generate at highest tier
        sheet = self.generate(
            description=description,
            animation_set=animation_set,
            sprite_size=sprite_size,
            name=name,
            **kwargs,
        )

        # Store generation info
        sheet.metadata['target_platforms'] = target_platforms
        sheet.metadata['generation_tier'] = gen_tier.name
        sheet.metadata['description'] = description

        # Add to manifest if provided
        entry = None
        if manifest and output_dir:
            entry = self.save_to_manifest(
                sheet, manifest, output_dir, target_platforms
            )

        return sheet, entry


# Alias for backwards compatibility
AnimationData = Animation


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    """Command-line interface for character generation."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate character sprite sheets with animations'
    )
    parser.add_argument('description', help='Character description')
    parser.add_argument('-o', '--output', required=True, help='Output directory')
    parser.add_argument('--name', default='character', help='Character name')
    parser.add_argument('--platform', default='nes',
                       choices=['nes', 'genesis', 'snes', 'gb', 'gameboy'],
                       help='Target platform')
    parser.add_argument('--animation-set', default='standard',
                       choices=['minimal', 'standard', 'full'],
                       help='Animation set complexity')
    parser.add_argument('--sprite-size', type=int, nargs=2,
                       metavar=('W', 'H'),
                       help='Override sprite size')
    parser.add_argument('--api-key', help='Pollinations API key')
    parser.add_argument('--show-limits', action='store_true',
                       help='Show platform system limits and exit')

    args = parser.parse_args()

    # Get platform config using comprehensive system limits
    platform = get_platform_config(args.platform)

    # Show limits and exit if requested
    if args.show_limits:
        print(f"\n{platform.name} Character Generation Limits:")
        print(f"  Tier: {platform.tier}")
        print(f"  Max sprites: {platform.max_sprites}")
        print(f"  Sprites per scanline: {platform.max_sprites_per_scanline}")
        print(f"  Sprite sizes: {platform.sprite_sizes}")
        print(f"  Colors per palette: {platform.colors_per_palette}")
        print(f"  Sprite palettes: {platform.max_palettes_sprite}")
        print(f"  Tiles per bank: {platform.max_tiles_per_bank}")
        print(f"  H/V flip support: {platform.hardware_h_flip}/{platform.hardware_v_flip}")
        print(f"\n  Recommended animation frames:")
        for anim, frames in platform.recommended_frames.items():
            print(f"    {anim}: {frames} frames")
        return

    # Create generator
    generator = CharacterGenerator(platform, api_key=args.api_key)

    # Set flags
    flags = GenerationFlags(animation_set=args.animation_set)
    generator.set_flags(flags)

    # Generate
    sprite_size = tuple(args.sprite_size) if args.sprite_size else None
    sheet = generator.generate(
        description=args.description,
        animation_set=args.animation_set,
        sprite_size=sprite_size,
        name=args.name,
    )

    # Save
    outputs = generator.save_character(sheet, Path(args.output))

    print(f"\nCharacter generated successfully!")
    print(f"Output files:")
    for name, path in outputs.items():
        print(f"  {name}: {path}")

    if sheet.warnings:
        print(f"\nWarnings:")
        for warning in sheet.warnings:
            print(f"  - {warning}")


if __name__ == '__main__':
    main()
