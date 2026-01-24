"""
Asset Organizer - Semantic labeling and hierarchical organization for game assets.

Features:
- Project association prompts (project-specific vs shared library)
- Semantic labeling (gameplay states, animation types, system types)
- Per-platform directory hierarchies
- Animation frame organization (idle, walk, attack, etc.)
- Automatic categorization based on asset metadata
"""

import os
import json
import shutil
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
from enum import Enum
from datetime import datetime


# =============================================================================
# Semantic Labels - Gameplay States
# =============================================================================

class GameplayState(Enum):
    """Standard gameplay animation states across all platforms."""

    # Core movement states
    IDLE = "idle"
    WALK = "walk"
    RUN = "run"
    JUMP = "jump"
    FALL = "fall"
    CROUCH = "crouch"
    CRAWL = "crawl"
    CLIMB = "climb"
    SWIM = "swim"

    # Combat states
    ATTACK = "attack"
    ATTACK_LIGHT = "attack_light"
    ATTACK_HEAVY = "attack_heavy"
    ATTACK_SPECIAL = "attack_special"
    SHOOT = "shoot"
    THROW = "throw"
    BLOCK = "block"
    DODGE = "dodge"

    # Damage states
    HURT = "hurt"
    KNOCKBACK = "knockback"
    DEATH = "death"
    REVIVE = "revive"

    # Interaction states
    INTERACT = "interact"
    PICKUP = "pickup"
    USE_ITEM = "use_item"
    TALK = "talk"

    # Special states
    SPAWN = "spawn"
    DESPAWN = "despawn"
    TRANSFORM = "transform"
    CHARGE = "charge"
    VICTORY = "victory"
    DEFEAT = "defeat"


class AssetCategory(Enum):
    """Top-level asset categories."""

    # Characters
    PLAYER = "player"
    ENEMY = "enemy"
    NPC = "npc"
    BOSS = "boss"

    # Objects
    PROJECTILE = "projectile"
    ITEM = "item"
    PICKUP = "pickup"
    WEAPON = "weapon"

    # Environment
    BACKGROUND = "background"
    FOREGROUND = "foreground"
    TILESET = "tileset"
    PARALLAX = "parallax"

    # Effects
    VFX = "vfx"
    PARTICLE = "particle"
    EXPLOSION = "explosion"

    # UI
    HUD = "hud"
    MENU = "menu"
    FONT = "font"
    ICON = "icon"

    # Audio (for organization, not processing)
    MUSIC = "music"
    SFX = "sfx"


class SystemType(Enum):
    """System-level asset types based on hardware needs."""

    # CHR/Pattern table types
    CHR_SPRITE = "chr_sprite"           # Sprite pattern data
    CHR_BACKGROUND = "chr_background"   # Background pattern data
    CHR_ANIMATED = "chr_animated"       # Animated tile data (multiple banks)

    # Map/Level data
    NAMETABLE = "nametable"             # Tile map data
    METATILE = "metatile"               # Metatile definitions
    COLLISION = "collision"             # Collision map

    # Palette data
    PALETTE_SPRITE = "palette_sprite"
    PALETTE_BG = "palette_bg"
    PALETTE_SHARED = "palette_shared"

    # Animation data
    ANIM_SPRITE = "anim_sprite"         # Sprite animation sequences
    ANIM_TILE = "anim_tile"             # Tile animation (CHR swap)

    # Audio data
    AUDIO_MUSIC = "audio_music"
    AUDIO_SFX = "audio_sfx"


# =============================================================================
# Platform-Specific Hierarchies
# =============================================================================

# Directory structure templates per platform
PLATFORM_HIERARCHIES = {
    'nes': {
        'chr': {
            'sprites': ['player', 'enemies', 'projectiles', 'items', 'effects'],
            'backgrounds': ['static', 'animated'],
            'shared': ['fonts', 'hud'],
        },
        'maps': {
            'levels': [],
            'collision': [],
            'metatiles': [],
        },
        'palettes': {
            'sprites': [],
            'backgrounds': [],
        },
        'animations': {
            'sprites': ['player', 'enemies', 'items'],
            'tiles': ['water', 'lava', 'effects'],
        },
    },
    'genesis': {
        'tiles': {
            'sprites': ['player', 'enemies', 'projectiles', 'items', 'effects'],
            'backgrounds': ['static', 'animated', 'parallax'],
            'shared': ['fonts', 'hud'],
        },
        'maps': {
            'levels': [],
            'collision': [],
        },
        'palettes': [],
        'animations': {
            'sprites': [],
            'tiles': [],
        },
    },
    'snes': {
        'graphics': {
            'sprites': ['player', 'enemies', 'projectiles', 'items', 'effects'],
            'backgrounds': ['mode7', 'standard', 'animated'],
            'shared': ['fonts', 'hud'],
        },
        'maps': {
            'levels': [],
            'collision': [],
        },
        'palettes': [],
        'animations': [],
    },
}

# Animation frame organization by gameplay state
ANIMATION_FRAME_STRUCTURE = {
    GameplayState.IDLE: {
        'min_frames': 2,
        'max_frames': 4,
        'nes_frames': 2,
        'loop': True,
        'speed_ms': 150,
    },
    GameplayState.WALK: {
        'min_frames': 4,
        'max_frames': 8,
        'nes_frames': 4,
        'loop': True,
        'speed_ms': 100,
    },
    GameplayState.RUN: {
        'min_frames': 4,
        'max_frames': 6,
        'nes_frames': 4,
        'loop': True,
        'speed_ms': 80,
    },
    GameplayState.ATTACK: {
        'min_frames': 3,
        'max_frames': 6,
        'nes_frames': 3,
        'loop': False,
        'speed_ms': 60,
    },
    GameplayState.HURT: {
        'min_frames': 2,
        'max_frames': 3,
        'nes_frames': 2,
        'loop': False,
        'speed_ms': 100,
    },
    GameplayState.DEATH: {
        'min_frames': 3,
        'max_frames': 5,
        'nes_frames': 3,
        'loop': False,
        'speed_ms': 120,
    },
    GameplayState.JUMP: {
        'min_frames': 2,
        'max_frames': 4,
        'nes_frames': 2,
        'loop': False,
        'speed_ms': 100,
    },
}


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class AssetLabel:
    """Semantic label for an asset."""

    category: AssetCategory
    name: str                                   # e.g., "cyber_ninja"
    gameplay_state: Optional[GameplayState] = None
    system_type: Optional[SystemType] = None
    frame_index: Optional[int] = None           # For animation frames
    variant: Optional[str] = None               # e.g., "blue", "damaged"

    # Additional metadata
    tags: List[str] = field(default_factory=list)

    def to_filename(self, extension: str = ".png") -> str:
        """Generate standardized filename from label."""
        parts = [self.category.value, self.name]

        if self.gameplay_state:
            parts.append(self.gameplay_state.value)

        if self.frame_index is not None:
            parts.append(f"f{self.frame_index:02d}")

        if self.variant:
            parts.append(self.variant)

        return "_".join(parts) + extension

    def to_path(self, platform: str = "nes") -> str:
        """Generate directory path from label."""
        parts = []

        # Category determines top-level directory
        if self.category in (AssetCategory.PLAYER, AssetCategory.ENEMY,
                            AssetCategory.NPC, AssetCategory.BOSS):
            parts.append("sprites")
            parts.append(self.category.value)
        elif self.category in (AssetCategory.PROJECTILE, AssetCategory.ITEM,
                               AssetCategory.PICKUP, AssetCategory.WEAPON):
            parts.append("sprites")
            parts.append("objects")
        elif self.category in (AssetCategory.BACKGROUND, AssetCategory.FOREGROUND,
                               AssetCategory.TILESET, AssetCategory.PARALLAX):
            parts.append("backgrounds")
            parts.append(self.category.value)
        elif self.category in (AssetCategory.VFX, AssetCategory.PARTICLE,
                               AssetCategory.EXPLOSION):
            parts.append("effects")
        elif self.category in (AssetCategory.HUD, AssetCategory.MENU,
                               AssetCategory.FONT, AssetCategory.ICON):
            parts.append("ui")

        # Add name subdirectory for characters
        if self.category in (AssetCategory.PLAYER, AssetCategory.ENEMY,
                            AssetCategory.NPC, AssetCategory.BOSS):
            parts.append(self.name)

        return "/".join(parts)


@dataclass
class ProjectAssociation:
    """Associates an asset with a project or marks it as shared."""

    is_project_specific: bool = False
    project_name: Optional[str] = None

    # If shared, which library category
    library_category: str = "generic"  # generic, synthwave, fantasy, scifi, etc.

    # Reusability hints
    reusable_in_projects: List[str] = field(default_factory=list)


@dataclass
class OrganizedAsset:
    """An asset with full organization metadata."""

    source_path: str
    label: AssetLabel
    association: ProjectAssociation

    # Derived paths
    organized_path: Optional[str] = None
    chr_path: Optional[str] = None

    # Platform-specific data
    platform: str = "nes"

    # Processing status
    processed: bool = False
    process_date: Optional[str] = None

    # File references
    variants: List[str] = field(default_factory=list)  # Other variants of same asset


@dataclass
class AssetManifest:
    """Manifest tracking all organized assets."""

    project_name: str
    platform: str
    created: str
    modified: str

    # Organized assets by category
    assets: Dict[str, List[OrganizedAsset]] = field(default_factory=dict)

    # Index for quick lookup
    by_name: Dict[str, OrganizedAsset] = field(default_factory=dict)
    by_gameplay_state: Dict[str, List[OrganizedAsset]] = field(default_factory=dict)

    # Statistics
    total_sprites: int = 0
    total_backgrounds: int = 0
    total_animations: int = 0
    chr_usage_bytes: int = 0


# =============================================================================
# Asset Organizer
# =============================================================================

class AssetOrganizer:
    """
    Organize assets with semantic labels and project associations.

    Handles:
    - Prompting for project association
    - Applying semantic labels
    - Creating hierarchical directory structures
    - Tracking animation frames by gameplay state
    """

    def __init__(
        self,
        base_path: str,
        platform: str = "nes",
        project_name: Optional[str] = None,
    ):
        """
        Initialize asset organizer.

        Args:
            base_path: Root directory for asset organization
            platform: Target platform (nes, genesis, snes)
            project_name: Current project name (None for shared library)
        """
        self.base_path = Path(base_path)
        self.platform = platform
        self.project_name = project_name

        # Load or create manifest
        self.manifest = self._load_or_create_manifest()

        # Track pending organization requests
        self.pending_assets: List[Dict] = []

    def _load_or_create_manifest(self) -> AssetManifest:
        """Load existing manifest or create new one."""
        manifest_path = self.base_path / "asset_manifest.json"

        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                data = json.load(f)
                return AssetManifest(
                    project_name=data.get('project_name', ''),
                    platform=data.get('platform', self.platform),
                    created=data.get('created', ''),
                    modified=datetime.now().isoformat(),
                )

        return AssetManifest(
            project_name=self.project_name or '',
            platform=self.platform,
            created=datetime.now().isoformat(),
            modified=datetime.now().isoformat(),
        )

    # -------------------------------------------------------------------------
    # Project Association
    # -------------------------------------------------------------------------

    def prompt_project_association(
        self,
        asset_description: str,
    ) -> ProjectAssociation:
        """
        Generate project association prompt data for UI.

        Returns the data structure for the AskUserQuestion tool
        to query about project association.

        Args:
            asset_description: Description of the asset being organized

        Returns:
            ProjectAssociation with default values (to be updated by user response)
        """
        # This returns the prompt structure - actual prompting done by caller
        return {
            'question': f"Is '{asset_description}' specific to a project or shared?",
            'header': "Association",
            'options': [
                {
                    'label': f"Project: {self.project_name}" if self.project_name else "Current Project",
                    'description': "Asset is specific to this project only"
                },
                {
                    'label': "Shared Library",
                    'description': "Asset can be reused across multiple projects"
                },
            ],
            'multiSelect': False,
        }

    def get_library_category_prompt(self) -> Dict:
        """Get prompt for shared library category selection."""
        return {
            'question': "Which library category does this asset belong to?",
            'header': "Category",
            'options': [
                {'label': "Generic", 'description': "Universal assets (UI, fonts, common items)"},
                {'label': "Synthwave", 'description': "Neon, cyberpunk, retrowave aesthetic"},
                {'label': "Fantasy", 'description': "Medieval, magic, dungeons"},
                {'label': "Sci-Fi", 'description': "Space, robots, futuristic"},
            ],
            'multiSelect': False,
        }

    def create_project_association(
        self,
        is_project_specific: bool,
        library_category: str = "generic",
    ) -> ProjectAssociation:
        """Create project association from user choices."""
        return ProjectAssociation(
            is_project_specific=is_project_specific,
            project_name=self.project_name if is_project_specific else None,
            library_category=library_category,
        )

    # -------------------------------------------------------------------------
    # Semantic Labeling
    # -------------------------------------------------------------------------

    def create_label(
        self,
        category: str,
        name: str,
        gameplay_state: Optional[str] = None,
        frame_index: Optional[int] = None,
        variant: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> AssetLabel:
        """
        Create semantic label for an asset.

        Args:
            category: Asset category (player, enemy, background, etc.)
            name: Asset name (e.g., "cyber_ninja", "slime")
            gameplay_state: Animation state (idle, walk, attack, etc.)
            frame_index: Frame number for animations
            variant: Variant name (e.g., "blue", "damaged")
            tags: Additional tags for searchability

        Returns:
            AssetLabel with all metadata
        """
        # Parse category
        try:
            cat_enum = AssetCategory(category.lower())
        except ValueError:
            cat_enum = AssetCategory.ITEM  # Default

        # Parse gameplay state
        state_enum = None
        if gameplay_state:
            try:
                state_enum = GameplayState(gameplay_state.lower())
            except ValueError:
                pass

        return AssetLabel(
            category=cat_enum,
            name=name.lower().replace(' ', '_'),
            gameplay_state=state_enum,
            frame_index=frame_index,
            variant=variant,
            tags=tags or [],
        )

    def infer_label_from_filename(self, filename: str) -> AssetLabel:
        """
        Attempt to infer semantic label from existing filename.

        Parses patterns like:
        - player_idle_f01.png
        - enemy_slime_attack.chr
        - bg_synthwave_city.png
        """
        stem = Path(filename).stem.lower()
        parts = stem.replace('-', '_').split('_')

        # Try to identify category
        category = AssetCategory.ITEM
        name = "unknown"
        gameplay_state = None
        frame_index = None
        variant = None

        for i, part in enumerate(parts):
            # Check for category
            try:
                category = AssetCategory(part)
                continue
            except ValueError:
                pass

            # Check for gameplay state
            try:
                gameplay_state = GameplayState(part)
                continue
            except ValueError:
                pass

            # Check for frame index (f01, f02, frame1, etc.)
            if part.startswith('f') and part[1:].isdigit():
                frame_index = int(part[1:])
                continue
            if part.startswith('frame') and part[5:].isdigit():
                frame_index = int(part[5:])
                continue

            # Otherwise, consider it part of the name
            if name == "unknown":
                name = part
            else:
                # Could be variant or additional name part
                if part in ('blue', 'red', 'green', 'gold', 'damaged', 'alt'):
                    variant = part
                else:
                    name = f"{name}_{part}"

        return AssetLabel(
            category=category,
            name=name,
            gameplay_state=gameplay_state,
            frame_index=frame_index,
            variant=variant,
        )

    # -------------------------------------------------------------------------
    # Directory Structure
    # -------------------------------------------------------------------------

    def get_asset_directory(
        self,
        label: AssetLabel,
        association: ProjectAssociation,
    ) -> Path:
        """
        Determine the directory path for an asset.

        Args:
            label: Semantic label for the asset
            association: Project association

        Returns:
            Path to the asset's directory
        """
        if association.is_project_specific:
            # Project-specific asset
            base = self.base_path / "projects" / (association.project_name or "default")
        else:
            # Shared library asset
            base = self.base_path / "library" / association.library_category

        # Add platform subdirectory
        base = base / self.platform

        # Add semantic path
        semantic_path = label.to_path(self.platform)

        return base / semantic_path

    def create_directory_structure(
        self,
        project_name: Optional[str] = None,
    ) -> Dict[str, Path]:
        """
        Create the full directory structure for a project or library.

        Returns dict mapping category names to paths.
        """
        created_paths = {}

        if project_name:
            base = self.base_path / "projects" / project_name / self.platform
        else:
            base = self.base_path / "library" / "generic" / self.platform

        hierarchy = PLATFORM_HIERARCHIES.get(self.platform, PLATFORM_HIERARCHIES['nes'])

        def create_recursive(parent: Path, structure: dict):
            for key, value in structure.items():
                path = parent / key
                path.mkdir(parents=True, exist_ok=True)
                created_paths[key] = path

                if isinstance(value, dict):
                    create_recursive(path, value)
                elif isinstance(value, list):
                    for subdir in value:
                        subpath = path / subdir
                        subpath.mkdir(parents=True, exist_ok=True)
                        created_paths[f"{key}/{subdir}"] = subpath

        create_recursive(base, hierarchy)

        return created_paths

    # -------------------------------------------------------------------------
    # Animation Frame Organization
    # -------------------------------------------------------------------------

    def get_animation_config(
        self,
        gameplay_state: GameplayState,
    ) -> Dict[str, Any]:
        """Get animation configuration for a gameplay state."""
        return ANIMATION_FRAME_STRUCTURE.get(
            gameplay_state,
            {
                'min_frames': 2,
                'max_frames': 4,
                'nes_frames': 2,
                'loop': True,
                'speed_ms': 100,
            }
        )

    def organize_animation_frames(
        self,
        frames: List[str],
        label: AssetLabel,
        association: ProjectAssociation,
    ) -> List[OrganizedAsset]:
        """
        Organize animation frames into proper structure.

        Args:
            frames: List of frame file paths
            label: Base label (without frame index)
            association: Project association

        Returns:
            List of OrganizedAsset for each frame
        """
        organized = []
        target_dir = self.get_asset_directory(label, association)
        target_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectory for this animation
        if label.gameplay_state:
            anim_dir = target_dir / label.gameplay_state.value
        else:
            anim_dir = target_dir / "frames"

        anim_dir.mkdir(parents=True, exist_ok=True)

        for i, frame_path in enumerate(frames):
            # Create frame-specific label
            frame_label = AssetLabel(
                category=label.category,
                name=label.name,
                gameplay_state=label.gameplay_state,
                frame_index=i,
                variant=label.variant,
                tags=label.tags.copy(),
            )

            # Determine target path
            filename = frame_label.to_filename()
            target_path = anim_dir / filename

            # Create organized asset
            asset = OrganizedAsset(
                source_path=frame_path,
                label=frame_label,
                association=association,
                organized_path=str(target_path),
                platform=self.platform,
            )

            organized.append(asset)

        return organized

    # -------------------------------------------------------------------------
    # Asset Organization
    # -------------------------------------------------------------------------

    def organize_asset(
        self,
        source_path: str,
        label: AssetLabel,
        association: ProjectAssociation,
        copy_file: bool = True,
    ) -> OrganizedAsset:
        """
        Organize a single asset.

        Args:
            source_path: Path to source file
            label: Semantic label
            association: Project association
            copy_file: Whether to copy/move the file

        Returns:
            OrganizedAsset with full metadata
        """
        target_dir = self.get_asset_directory(label, association)
        target_dir.mkdir(parents=True, exist_ok=True)

        # Determine filename
        extension = Path(source_path).suffix
        filename = label.to_filename(extension)
        target_path = target_dir / filename

        # Copy file if requested
        if copy_file and Path(source_path).exists():
            shutil.copy2(source_path, target_path)

        # Create organized asset
        asset = OrganizedAsset(
            source_path=source_path,
            label=label,
            association=association,
            organized_path=str(target_path),
            platform=self.platform,
            processed=True,
            process_date=datetime.now().isoformat(),
        )

        # Update manifest
        category_key = label.category.value
        if category_key not in self.manifest.assets:
            self.manifest.assets[category_key] = []
        self.manifest.assets[category_key].append(asset)

        self.manifest.by_name[label.name] = asset

        if label.gameplay_state:
            state_key = label.gameplay_state.value
            if state_key not in self.manifest.by_gameplay_state:
                self.manifest.by_gameplay_state[state_key] = []
            self.manifest.by_gameplay_state[state_key].append(asset)

        return asset

    def save_manifest(self) -> str:
        """Save manifest to disk."""
        manifest_path = self.base_path / "asset_manifest.json"

        self.manifest.modified = datetime.now().isoformat()

        # Convert to serializable format
        data = {
            'project_name': self.manifest.project_name,
            'platform': self.manifest.platform,
            'created': self.manifest.created,
            'modified': self.manifest.modified,
            'total_sprites': self.manifest.total_sprites,
            'total_backgrounds': self.manifest.total_backgrounds,
            'total_animations': self.manifest.total_animations,
            'chr_usage_bytes': self.manifest.chr_usage_bytes,
            'assets': {},
        }

        for category, assets in self.manifest.assets.items():
            data['assets'][category] = [
                {
                    'source_path': a.source_path,
                    'organized_path': a.organized_path,
                    'label': {
                        'category': a.label.category.value,
                        'name': a.label.name,
                        'gameplay_state': a.label.gameplay_state.value if a.label.gameplay_state else None,
                        'frame_index': a.label.frame_index,
                        'variant': a.label.variant,
                        'tags': a.label.tags,
                    },
                    'association': {
                        'is_project_specific': a.association.is_project_specific,
                        'project_name': a.association.project_name,
                        'library_category': a.association.library_category,
                    },
                    'platform': a.platform,
                    'processed': a.processed,
                    'process_date': a.process_date,
                }
                for a in assets
            ]

        with open(manifest_path, 'w') as f:
            json.dump(data, f, indent=2)

        return str(manifest_path)

    # -------------------------------------------------------------------------
    # Query Methods
    # -------------------------------------------------------------------------

    def find_by_gameplay_state(
        self,
        state: GameplayState,
    ) -> List[OrganizedAsset]:
        """Find all assets with a specific gameplay state."""
        return self.manifest.by_gameplay_state.get(state.value, [])

    def find_by_category(
        self,
        category: AssetCategory,
    ) -> List[OrganizedAsset]:
        """Find all assets in a category."""
        return self.manifest.assets.get(category.value, [])

    def find_by_name(
        self,
        name: str,
    ) -> Optional[OrganizedAsset]:
        """Find asset by name."""
        return self.manifest.by_name.get(name.lower())

    def get_animation_set(
        self,
        name: str,
    ) -> Dict[GameplayState, List[OrganizedAsset]]:
        """Get all animation frames for a character/object."""
        result = {}

        for state in GameplayState:
            assets = self.find_by_gameplay_state(state)
            matching = [a for a in assets if a.label.name == name.lower()]
            if matching:
                result[state] = sorted(matching, key=lambda a: a.label.frame_index or 0)

        return result


# =============================================================================
# Utility Functions
# =============================================================================

def get_gameplay_states() -> List[str]:
    """Get list of all gameplay state names."""
    return [s.value for s in GameplayState]


def get_asset_categories() -> List[str]:
    """Get list of all asset category names."""
    return [c.value for c in AssetCategory]


def get_recommended_frames(
    gameplay_state: str,
    platform: str = "nes",
) -> int:
    """Get recommended frame count for a gameplay state on a platform."""
    try:
        state = GameplayState(gameplay_state.lower())
    except ValueError:
        return 2

    config = ANIMATION_FRAME_STRUCTURE.get(state)
    if not config:
        return 2

    if platform == "nes":
        return config.get('nes_frames', 2)
    else:
        return config.get('max_frames', 4)


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    """Command-line interface for asset organization."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Organize game assets with semantic labels'
    )
    parser.add_argument('action', choices=['init', 'organize', 'list', 'find'],
                       help='Action to perform')
    parser.add_argument('--base-path', default='.', help='Base directory')
    parser.add_argument('--platform', default='nes',
                       choices=['nes', 'genesis', 'snes'],
                       help='Target platform')
    parser.add_argument('--project', help='Project name')
    parser.add_argument('--file', help='File to organize')
    parser.add_argument('--category', help='Asset category')
    parser.add_argument('--name', help='Asset name')
    parser.add_argument('--state', help='Gameplay state')

    args = parser.parse_args()

    organizer = AssetOrganizer(
        base_path=args.base_path,
        platform=args.platform,
        project_name=args.project,
    )

    if args.action == 'init':
        paths = organizer.create_directory_structure(args.project)
        print(f"Created {len(paths)} directories")
        for name, path in paths.items():
            print(f"  {name}: {path}")

    elif args.action == 'organize':
        if not args.file:
            print("Error: --file required for organize")
            return

        label = organizer.create_label(
            category=args.category or 'item',
            name=args.name or Path(args.file).stem,
            gameplay_state=args.state,
        )

        association = organizer.create_project_association(
            is_project_specific=bool(args.project),
        )

        asset = organizer.organize_asset(args.file, label, association)
        print(f"Organized: {asset.organized_path}")

        organizer.save_manifest()

    elif args.action == 'list':
        print(f"Gameplay States:")
        for state in get_gameplay_states():
            config = ANIMATION_FRAME_STRUCTURE.get(GameplayState(state), {})
            frames = config.get('nes_frames', '?')
            print(f"  {state}: {frames} frames")

        print(f"\nAsset Categories:")
        for cat in get_asset_categories():
            print(f"  {cat}")

    elif args.action == 'find':
        if args.name:
            asset = organizer.find_by_name(args.name)
            if asset:
                print(f"Found: {asset.organized_path}")
            else:
                print(f"Not found: {args.name}")
        elif args.state:
            try:
                state = GameplayState(args.state)
                assets = organizer.find_by_gameplay_state(state)
                print(f"Found {len(assets)} assets with state '{args.state}':")
                for a in assets:
                    print(f"  {a.label.name}: {a.organized_path}")
            except ValueError:
                print(f"Unknown state: {args.state}")


if __name__ == '__main__':
    main()
