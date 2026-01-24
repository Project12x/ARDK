"""
Unified Asset Manifest - Complete tracking for generation-to-processing pipeline.

This module provides a comprehensive manifest system that tracks assets from
AI generation through platform-specific processing, enabling:
- Full provenance tracking (source → variants → outputs)
- Cross-platform asset correlation
- Regeneration with consistent settings
- Pipeline handoff between generation and processing stages

The manifest serves as the "contract" between:
1. Asset generators (character, background, parallax, animated tile)
2. Sprite ingestor (tier-based downsampling, palette reallocation)
3. unified_pipeline.py (platform-specific processing)
4. Build system (CHR/ROM assembly)
"""

import json
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from enum import Enum

from .tier_system import (
    AssetTier,
    get_tier_for_platform,
    get_generation_tier,
)


# =============================================================================
# Manifest Enums
# =============================================================================

class AssetCategory(Enum):
    """High-level asset categories."""
    CHARACTER = "character"
    BACKGROUND = "background"
    PARALLAX = "parallax"
    ANIMATED_TILE = "animated_tile"
    TILESET = "tileset"
    UI = "ui"
    EFFECT = "effect"


class ProcessingStage(Enum):
    """Asset processing stages."""
    GENERATED = "generated"          # AI output received
    VALIDATED = "validated"          # Passed tier constraints
    DOWNSAMPLED = "downsampled"      # Tier reduction applied
    PALETTE_MAPPED = "palette_mapped"  # Platform palette applied
    PROCESSED = "processed"          # unified_pipeline complete
    EXPORTED = "exported"            # Final format (CHR, etc.)
    FAILED = "failed"                # Processing failed


class OutputFormat(Enum):
    """Output file formats."""
    PNG = "png"
    CHR = "chr"           # NES/Famicom CHR ROM
    BIN = "bin"           # Generic binary
    ASM_INC = "asm_inc"   # Assembly include
    C_HEADER = "c_header" # C header file
    JSON = "json"         # Metadata/manifest
    TILEMAP = "tilemap"   # Tile map data


# =============================================================================
# Asset Entry
# =============================================================================

@dataclass
class AssetVariant:
    """A platform-specific variant of an asset."""

    platform: str
    tier: AssetTier
    stage: ProcessingStage

    # File paths
    source_file: str = ""      # Input to this stage
    output_files: Dict[str, str] = field(default_factory=dict)  # format -> path

    # Processing metadata
    colors_used: int = 0
    palette_indices: List[int] = field(default_factory=list)
    dimensions: tuple = (0, 0)
    tile_count: int = 0

    # Quality metrics
    color_accuracy: float = 1.0  # 1.0 = perfect match to source
    detail_preserved: float = 1.0  # 1.0 = no detail loss

    # Errors/warnings
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    # Timestamps
    created_at: str = ""
    processed_at: str = ""


@dataclass
class AnimationEntry:
    """Animation data within an asset."""

    name: str
    frame_count: int
    frame_width: int
    frame_height: int

    # Timing
    frame_duration_ms: int = 100
    loop: bool = True

    # Frame data
    frame_files: List[str] = field(default_factory=list)
    frame_offsets: List[tuple] = field(default_factory=list)  # (x, y) in sheet

    # CHR bank info (for NES)
    chr_bank_start: int = 0
    chr_bank_count: int = 1


@dataclass
class AssetEntry:
    """
    Complete tracking for a single logical asset.

    An asset may have multiple variants (one per target platform)
    and multiple animations (for characters).
    """

    # Identity
    asset_id: str                    # Unique identifier
    name: str                        # Human-readable name
    category: AssetCategory

    # Generation info
    generation_tier: AssetTier       # Tier used for generation
    generation_prompt: str = ""      # AI prompt used
    generation_model: str = ""       # AI model used
    generation_seed: Optional[int] = None

    # Source tracking
    source_file: str = ""            # Original AI output
    source_hash: str = ""            # Content hash for change detection

    # Target platforms
    target_platforms: List[str] = field(default_factory=list)

    # Platform variants
    variants: Dict[str, AssetVariant] = field(default_factory=dict)

    # Animations (for characters/animated tiles)
    animations: Dict[str, AnimationEntry] = field(default_factory=dict)

    # Metadata
    tags: List[str] = field(default_factory=list)
    description: str = ""

    # Timestamps
    created_at: str = ""
    updated_at: str = ""

    # Custom properties
    properties: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Unified Manifest
# =============================================================================

@dataclass
class UnifiedAssetManifest:
    """
    Complete manifest tracking all assets in a project.

    This is the single source of truth for asset pipeline state,
    enabling:
    - Incremental processing (skip unchanged assets)
    - Cross-platform builds from single source
    - Regeneration with preserved settings
    - Build system integration
    """

    # Project info
    project_name: str
    project_version: str = "1.0.0"

    # Assets by ID
    assets: Dict[str, AssetEntry] = field(default_factory=dict)

    # Platform configurations used
    platform_configs: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Global settings
    default_tier: AssetTier = AssetTier.STANDARD
    default_platforms: List[str] = field(default_factory=lambda: ['nes'])

    # Output directories
    output_base: str = "output"
    source_dir: str = "assets/source"
    processed_dir: str = "assets/processed"

    # Build info
    last_build_time: str = ""
    build_count: int = 0

    # Timestamps
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        """Set creation timestamp if not set."""
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    # -------------------------------------------------------------------------
    # Asset Management
    # -------------------------------------------------------------------------

    def add_asset(
        self,
        name: str,
        category: AssetCategory,
        source_file: str,
        target_platforms: Optional[List[str]] = None,
        **kwargs,
    ) -> AssetEntry:
        """
        Add a new asset to the manifest.

        Args:
            name: Human-readable asset name
            category: Asset category (character, background, etc.)
            source_file: Path to source file
            target_platforms: List of target platforms (default: manifest default)
            **kwargs: Additional AssetEntry fields

        Returns:
            The created AssetEntry
        """
        platforms = target_platforms or self.default_platforms
        gen_tier = get_generation_tier(platforms)

        # Generate unique ID
        asset_id = self._generate_asset_id(name, category)

        # Compute source hash
        source_hash = self._compute_file_hash(source_file) if Path(source_file).exists() else ""

        entry = AssetEntry(
            asset_id=asset_id,
            name=name,
            category=category,
            generation_tier=gen_tier,
            source_file=source_file,
            source_hash=source_hash,
            target_platforms=platforms,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            **kwargs,
        )

        # Initialize variants for each platform
        for platform in platforms:
            tier = get_tier_for_platform(platform)
            entry.variants[platform] = AssetVariant(
                platform=platform,
                tier=tier,
                stage=ProcessingStage.GENERATED,
                source_file=source_file,
                created_at=datetime.now().isoformat(),
            )

        self.assets[asset_id] = entry
        self._touch()

        return entry

    def get_asset(self, asset_id: str) -> Optional[AssetEntry]:
        """Get an asset by ID."""
        return self.assets.get(asset_id)

    def get_assets_by_category(self, category: AssetCategory) -> List[AssetEntry]:
        """Get all assets of a specific category."""
        return [a for a in self.assets.values() if a.category == category]

    def get_assets_by_platform(self, platform: str) -> List[AssetEntry]:
        """Get all assets targeting a specific platform."""
        return [a for a in self.assets.values() if platform in a.target_platforms]

    def get_assets_needing_processing(self, platform: Optional[str] = None) -> List[AssetEntry]:
        """Get assets that haven't completed processing."""
        result = []
        for asset in self.assets.values():
            for plat, variant in asset.variants.items():
                if platform and plat != platform:
                    continue
                if variant.stage not in (ProcessingStage.PROCESSED, ProcessingStage.EXPORTED):
                    result.append(asset)
                    break
        return result

    def update_variant_stage(
        self,
        asset_id: str,
        platform: str,
        stage: ProcessingStage,
        output_files: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> bool:
        """
        Update the processing stage of an asset variant.

        Args:
            asset_id: Asset identifier
            platform: Platform name
            stage: New processing stage
            output_files: Output files produced (format -> path)
            **kwargs: Additional variant fields to update

        Returns:
            True if update successful
        """
        asset = self.assets.get(asset_id)
        if not asset:
            return False

        variant = asset.variants.get(platform)
        if not variant:
            return False

        variant.stage = stage
        variant.processed_at = datetime.now().isoformat()

        if output_files:
            variant.output_files.update(output_files)

        for key, value in kwargs.items():
            if hasattr(variant, key):
                setattr(variant, key, value)

        asset.updated_at = datetime.now().isoformat()
        self._touch()

        return True

    def add_animation(
        self,
        asset_id: str,
        anim_name: str,
        frame_count: int,
        frame_width: int,
        frame_height: int,
        **kwargs,
    ) -> Optional[AnimationEntry]:
        """Add animation data to an asset."""
        asset = self.assets.get(asset_id)
        if not asset:
            return None

        entry = AnimationEntry(
            name=anim_name,
            frame_count=frame_count,
            frame_width=frame_width,
            frame_height=frame_height,
            **kwargs,
        )

        asset.animations[anim_name] = entry
        asset.updated_at = datetime.now().isoformat()
        self._touch()

        return entry

    def remove_asset(self, asset_id: str) -> bool:
        """Remove an asset from the manifest."""
        if asset_id in self.assets:
            del self.assets[asset_id]
            self._touch()
            return True
        return False

    # -------------------------------------------------------------------------
    # Queries
    # -------------------------------------------------------------------------

    def get_chr_bank_assignments(self, platform: str) -> Dict[str, Dict[str, int]]:
        """
        Get CHR bank assignments for all assets on a platform.

        Returns:
            Dict of asset_id -> {anim_name: bank_index}
        """
        assignments = {}
        for asset in self.get_assets_by_platform(platform):
            if asset.animations:
                assignments[asset.asset_id] = {}
                for anim_name, anim in asset.animations.items():
                    assignments[asset.asset_id][anim_name] = anim.chr_bank_start
        return assignments

    def get_total_tile_count(self, platform: str) -> int:
        """Get total unique tiles used across all assets for a platform."""
        total = 0
        for asset in self.get_assets_by_platform(platform):
            variant = asset.variants.get(platform)
            if variant:
                total += variant.tile_count
        return total

    def get_palette_usage(self, platform: str) -> Dict[int, List[str]]:
        """
        Get palette usage by index for a platform.

        Returns:
            Dict of palette_index -> [asset_ids using it]
        """
        usage: Dict[int, List[str]] = {}
        for asset in self.get_assets_by_platform(platform):
            variant = asset.variants.get(platform)
            if variant:
                for idx in variant.palette_indices:
                    if idx not in usage:
                        usage[idx] = []
                    usage[idx].append(asset.asset_id)
        return usage

    def check_resource_limits(self, platform: str) -> Dict[str, Any]:
        """
        Check if assets exceed platform resource limits.

        Returns:
            Dict with limit checks and warnings
        """
        from .tier_system import TIER_SPECS

        tier = get_tier_for_platform(platform)
        spec = TIER_SPECS[tier]

        total_tiles = self.get_total_tile_count(platform)
        palette_usage = self.get_palette_usage(platform)

        return {
            'tiles': {
                'used': total_tiles,
                'limit': spec.max_unique_tiles,
                'ok': total_tiles <= spec.max_unique_tiles,
            },
            'palettes': {
                'used': len(palette_usage),
                'limit': spec.max_palettes,
                'ok': len(palette_usage) <= spec.max_palettes,
            },
            'warnings': self._collect_warnings(platform),
        }

    def _collect_warnings(self, platform: str) -> List[str]:
        """Collect all warnings for a platform."""
        warnings = []
        for asset in self.get_assets_by_platform(platform):
            variant = asset.variants.get(platform)
            if variant and variant.warnings:
                for w in variant.warnings:
                    warnings.append(f"{asset.name}: {w}")
        return warnings

    # -------------------------------------------------------------------------
    # Change Detection
    # -------------------------------------------------------------------------

    def check_for_changes(self) -> List[str]:
        """
        Check which assets have changed since last processing.

        Returns:
            List of asset IDs with changes
        """
        changed = []
        for asset_id, asset in self.assets.items():
            if asset.source_file and Path(asset.source_file).exists():
                current_hash = self._compute_file_hash(asset.source_file)
                if current_hash != asset.source_hash:
                    changed.append(asset_id)
        return changed

    def mark_source_updated(self, asset_id: str) -> bool:
        """Update source hash after detecting changes."""
        asset = self.assets.get(asset_id)
        if not asset or not asset.source_file:
            return False

        if Path(asset.source_file).exists():
            asset.source_hash = self._compute_file_hash(asset.source_file)
            asset.updated_at = datetime.now().isoformat()

            # Reset all variants to need reprocessing
            for variant in asset.variants.values():
                variant.stage = ProcessingStage.GENERATED

            self._touch()
            return True
        return False

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    def save(self, path: Union[str, Path]) -> None:
        """Save manifest to JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = self._to_dict()

        with open(path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    @classmethod
    def load(cls, path: Union[str, Path]) -> 'UnifiedAssetManifest':
        """Load manifest from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)

        return cls._from_dict(data)

    def _to_dict(self) -> Dict[str, Any]:
        """Convert manifest to dictionary for serialization."""
        return {
            'project_name': self.project_name,
            'project_version': self.project_version,
            'default_tier': self.default_tier.name,
            'default_platforms': self.default_platforms,
            'output_base': self.output_base,
            'source_dir': self.source_dir,
            'processed_dir': self.processed_dir,
            'last_build_time': self.last_build_time,
            'build_count': self.build_count,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'platform_configs': self.platform_configs,
            'assets': {
                asset_id: self._asset_to_dict(asset)
                for asset_id, asset in self.assets.items()
            },
        }

    def _asset_to_dict(self, asset: AssetEntry) -> Dict[str, Any]:
        """Convert asset entry to dictionary."""
        return {
            'asset_id': asset.asset_id,
            'name': asset.name,
            'category': asset.category.value,
            'generation_tier': asset.generation_tier.name,
            'generation_prompt': asset.generation_prompt,
            'generation_model': asset.generation_model,
            'generation_seed': asset.generation_seed,
            'source_file': asset.source_file,
            'source_hash': asset.source_hash,
            'target_platforms': asset.target_platforms,
            'tags': asset.tags,
            'description': asset.description,
            'created_at': asset.created_at,
            'updated_at': asset.updated_at,
            'properties': asset.properties,
            'variants': {
                platform: self._variant_to_dict(variant)
                for platform, variant in asset.variants.items()
            },
            'animations': {
                name: self._animation_to_dict(anim)
                for name, anim in asset.animations.items()
            },
        }

    def _variant_to_dict(self, variant: AssetVariant) -> Dict[str, Any]:
        """Convert variant to dictionary."""
        return {
            'platform': variant.platform,
            'tier': variant.tier.name,
            'stage': variant.stage.value,
            'source_file': variant.source_file,
            'output_files': variant.output_files,
            'colors_used': variant.colors_used,
            'palette_indices': variant.palette_indices,
            'dimensions': variant.dimensions,
            'tile_count': variant.tile_count,
            'color_accuracy': variant.color_accuracy,
            'detail_preserved': variant.detail_preserved,
            'warnings': variant.warnings,
            'errors': variant.errors,
            'created_at': variant.created_at,
            'processed_at': variant.processed_at,
        }

    def _animation_to_dict(self, anim: AnimationEntry) -> Dict[str, Any]:
        """Convert animation entry to dictionary."""
        return {
            'name': anim.name,
            'frame_count': anim.frame_count,
            'frame_width': anim.frame_width,
            'frame_height': anim.frame_height,
            'frame_duration_ms': anim.frame_duration_ms,
            'loop': anim.loop,
            'frame_files': anim.frame_files,
            'frame_offsets': anim.frame_offsets,
            'chr_bank_start': anim.chr_bank_start,
            'chr_bank_count': anim.chr_bank_count,
        }

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> 'UnifiedAssetManifest':
        """Create manifest from dictionary."""
        manifest = cls(
            project_name=data['project_name'],
            project_version=data.get('project_version', '1.0.0'),
            default_tier=AssetTier[data.get('default_tier', 'STANDARD')],
            default_platforms=data.get('default_platforms', ['nes']),
            output_base=data.get('output_base', 'output'),
            source_dir=data.get('source_dir', 'assets/source'),
            processed_dir=data.get('processed_dir', 'assets/processed'),
            last_build_time=data.get('last_build_time', ''),
            build_count=data.get('build_count', 0),
            created_at=data.get('created_at', ''),
            updated_at=data.get('updated_at', ''),
            platform_configs=data.get('platform_configs', {}),
        )

        # Load assets
        for asset_id, asset_data in data.get('assets', {}).items():
            asset = cls._asset_from_dict(asset_data)
            manifest.assets[asset_id] = asset

        return manifest

    @classmethod
    def _asset_from_dict(cls, data: Dict[str, Any]) -> AssetEntry:
        """Create asset entry from dictionary."""
        asset = AssetEntry(
            asset_id=data['asset_id'],
            name=data['name'],
            category=AssetCategory(data['category']),
            generation_tier=AssetTier[data.get('generation_tier', 'STANDARD')],
            generation_prompt=data.get('generation_prompt', ''),
            generation_model=data.get('generation_model', ''),
            generation_seed=data.get('generation_seed'),
            source_file=data.get('source_file', ''),
            source_hash=data.get('source_hash', ''),
            target_platforms=data.get('target_platforms', []),
            tags=data.get('tags', []),
            description=data.get('description', ''),
            created_at=data.get('created_at', ''),
            updated_at=data.get('updated_at', ''),
            properties=data.get('properties', {}),
        )

        # Load variants
        for platform, variant_data in data.get('variants', {}).items():
            asset.variants[platform] = cls._variant_from_dict(variant_data)

        # Load animations
        for name, anim_data in data.get('animations', {}).items():
            asset.animations[name] = cls._animation_from_dict(anim_data)

        return asset

    @classmethod
    def _variant_from_dict(cls, data: Dict[str, Any]) -> AssetVariant:
        """Create variant from dictionary."""
        return AssetVariant(
            platform=data['platform'],
            tier=AssetTier[data.get('tier', 'STANDARD')],
            stage=ProcessingStage(data.get('stage', 'generated')),
            source_file=data.get('source_file', ''),
            output_files=data.get('output_files', {}),
            colors_used=data.get('colors_used', 0),
            palette_indices=data.get('palette_indices', []),
            dimensions=tuple(data.get('dimensions', (0, 0))),
            tile_count=data.get('tile_count', 0),
            color_accuracy=data.get('color_accuracy', 1.0),
            detail_preserved=data.get('detail_preserved', 1.0),
            warnings=data.get('warnings', []),
            errors=data.get('errors', []),
            created_at=data.get('created_at', ''),
            processed_at=data.get('processed_at', ''),
        )

    @classmethod
    def _animation_from_dict(cls, data: Dict[str, Any]) -> AnimationEntry:
        """Create animation entry from dictionary."""
        return AnimationEntry(
            name=data['name'],
            frame_count=data['frame_count'],
            frame_width=data['frame_width'],
            frame_height=data['frame_height'],
            frame_duration_ms=data.get('frame_duration_ms', 100),
            loop=data.get('loop', True),
            frame_files=data.get('frame_files', []),
            frame_offsets=[tuple(o) for o in data.get('frame_offsets', [])],
            chr_bank_start=data.get('chr_bank_start', 0),
            chr_bank_count=data.get('chr_bank_count', 1),
        )

    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------

    def _generate_asset_id(self, name: str, category: AssetCategory) -> str:
        """Generate unique asset ID."""
        base = f"{category.value}_{name}".lower().replace(' ', '_')
        # Add timestamp hash for uniqueness
        timestamp_hash = hashlib.md5(
            datetime.now().isoformat().encode()
        ).hexdigest()[:6]
        return f"{base}_{timestamp_hash}"

    def _compute_file_hash(self, path: str) -> str:
        """Compute MD5 hash of a file."""
        try:
            with open(path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except (IOError, OSError):
            return ""

    def _touch(self) -> None:
        """Update the manifest timestamp."""
        self.updated_at = datetime.now().isoformat()


# =============================================================================
# Factory Functions
# =============================================================================

def create_project_manifest(
    project_name: str,
    platforms: Optional[List[str]] = None,
    output_dir: str = "output",
) -> UnifiedAssetManifest:
    """
    Create a new project manifest with sensible defaults.

    Args:
        project_name: Name of the project
        platforms: Default target platforms
        output_dir: Base output directory

    Returns:
        Configured UnifiedAssetManifest
    """
    return UnifiedAssetManifest(
        project_name=project_name,
        default_platforms=platforms or ['nes'],
        output_base=output_dir,
        source_dir=f"{output_dir}/source",
        processed_dir=f"{output_dir}/processed",
    )


def load_or_create_manifest(
    path: Union[str, Path],
    project_name: str = "ARDK Project",
    platforms: Optional[List[str]] = None,
) -> UnifiedAssetManifest:
    """
    Load existing manifest or create new one.

    Args:
        path: Path to manifest file
        project_name: Name if creating new
        platforms: Default platforms if creating new

    Returns:
        UnifiedAssetManifest (loaded or new)
    """
    path = Path(path)
    if path.exists():
        return UnifiedAssetManifest.load(path)
    else:
        manifest = create_project_manifest(project_name, platforms)
        manifest.save(path)
        return manifest


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    """Command-line interface for manifest management."""
    import argparse

    parser = argparse.ArgumentParser(
        description='ARDK Unified Asset Manifest Manager'
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Create command
    create_parser = subparsers.add_parser('create', help='Create new manifest')
    create_parser.add_argument('--name', required=True, help='Project name')
    create_parser.add_argument('--platforms', nargs='+', default=['nes'],
                               help='Target platforms')
    create_parser.add_argument('-o', '--output', default='asset_manifest.json',
                               help='Output file')

    # Info command
    info_parser = subparsers.add_parser('info', help='Show manifest info')
    info_parser.add_argument('manifest', help='Manifest file')

    # List command
    list_parser = subparsers.add_parser('list', help='List assets')
    list_parser.add_argument('manifest', help='Manifest file')
    list_parser.add_argument('--category', help='Filter by category')
    list_parser.add_argument('--platform', help='Filter by platform')

    # Check command
    check_parser = subparsers.add_parser('check', help='Check resource limits')
    check_parser.add_argument('manifest', help='Manifest file')
    check_parser.add_argument('--platform', default='nes', help='Platform to check')

    args = parser.parse_args()

    if args.command == 'create':
        manifest = create_project_manifest(args.name, args.platforms)
        manifest.save(args.output)
        print(f"Created manifest: {args.output}")
        print(f"  Project: {args.name}")
        print(f"  Platforms: {', '.join(args.platforms)}")

    elif args.command == 'info':
        manifest = UnifiedAssetManifest.load(args.manifest)
        print(f"Project: {manifest.project_name} v{manifest.project_version}")
        print(f"Assets: {len(manifest.assets)}")
        print(f"Default platforms: {', '.join(manifest.default_platforms)}")
        print(f"Created: {manifest.created_at}")
        print(f"Updated: {manifest.updated_at}")

    elif args.command == 'list':
        manifest = UnifiedAssetManifest.load(args.manifest)

        assets = list(manifest.assets.values())
        if args.category:
            category = AssetCategory(args.category)
            assets = [a for a in assets if a.category == category]
        if args.platform:
            assets = [a for a in assets if args.platform in a.target_platforms]

        print(f"Assets ({len(assets)}):")
        for asset in assets:
            stages = [f"{p}:{v.stage.value}" for p, v in asset.variants.items()]
            print(f"  {asset.asset_id}: {asset.name} [{asset.category.value}]")
            print(f"    Stages: {', '.join(stages)}")

    elif args.command == 'check':
        manifest = UnifiedAssetManifest.load(args.manifest)
        results = manifest.check_resource_limits(args.platform)

        print(f"Resource check for {args.platform}:")
        print(f"  Tiles: {results['tiles']['used']}/{results['tiles']['limit']} "
              f"{'OK' if results['tiles']['ok'] else 'EXCEEDED'}")
        print(f"  Palettes: {results['palettes']['used']}/{results['palettes']['limit']} "
              f"{'OK' if results['palettes']['ok'] else 'EXCEEDED'}")

        if results['warnings']:
            print("\nWarnings:")
            for w in results['warnings']:
                print(f"  - {w}")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
