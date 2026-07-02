"""
Art optimization profiles for ARDK.

This module separates stable hardware capability from per-game art direction.
System profiles describe what a machine can do. Game profiles describe what a
project wants to look like inside that envelope.
"""

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


ProfileData = Dict[str, Any]


class ArtProfileError(ValueError):
    """Raised when an art profile is invalid or incompatible."""


def _load_mapping(path: Path) -> ProfileData:
    """Load a JSON or YAML mapping from disk."""
    content = path.read_text(encoding="utf-8")

    if path.suffix.lower() in {".yaml", ".yml"}:
        if not HAS_YAML:
            raise ImportError(
                "PyYAML is required for YAML art profiles. "
                "Install with: pip install pyyaml"
            )
        data = yaml.safe_load(content)
    else:
        data = json.loads(content)

    if not isinstance(data, dict):
        raise ArtProfileError(f"Profile must be a mapping: {path}")

    return data


def _save_mapping(path: Path, data: ProfileData) -> None:
    """Save a JSON or YAML mapping to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.suffix.lower() in {".yaml", ".yml"}:
        if not HAS_YAML:
            raise ImportError(
                "PyYAML is required for YAML art profiles. "
                "Install with: pip install pyyaml"
            )
        path.write_text(
            yaml.dump(data, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )
        return

    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


@dataclass
class SystemCapabilityProfile:
    """
    Stable hardware envelope for one target system.

    This is intentionally not a style guide. It should change only when the
    target hardware model, toolchain assumptions, or validation expectations
    change.
    """

    system_id: str
    display_name: str
    profile_version: int = 1
    aliases: List[str] = field(default_factory=list)
    resolution: ProfileData = field(default_factory=dict)
    color: ProfileData = field(default_factory=dict)
    palettes: ProfileData = field(default_factory=dict)
    tiles: ProfileData = field(default_factory=dict)
    sprites: ProfileData = field(default_factory=dict)
    planes: ProfileData = field(default_factory=dict)
    transfer: ProfileData = field(default_factory=dict)
    audio: ProfileData = field(default_factory=dict)
    toolchain: ProfileData = field(default_factory=dict)
    validation: ProfileData = field(default_factory=dict)
    optimization_defaults: ProfileData = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: ProfileData) -> "SystemCapabilityProfile":
        """Create a system profile from a dictionary."""
        return cls(
            system_id=data["system_id"],
            display_name=data["display_name"],
            profile_version=int(data.get("profile_version", 1)),
            aliases=list(data.get("aliases", [])),
            resolution=dict(data.get("resolution", {})),
            color=dict(data.get("color", {})),
            palettes=dict(data.get("palettes", {})),
            tiles=dict(data.get("tiles", {})),
            sprites=dict(data.get("sprites", {})),
            planes=dict(data.get("planes", {})),
            transfer=dict(data.get("transfer", {})),
            audio=dict(data.get("audio", {})),
            toolchain=dict(data.get("toolchain", {})),
            validation=dict(data.get("validation", {})),
            optimization_defaults=dict(data.get("optimization_defaults", {})),
            notes=list(data.get("notes", [])),
        )

    @classmethod
    def load(cls, path: str | Path) -> "SystemCapabilityProfile":
        """Load a system profile from JSON or YAML."""
        return cls.from_dict(_load_mapping(Path(path)))

    def to_dict(self) -> ProfileData:
        """Convert the system profile to a JSON/YAML-compatible dictionary."""
        return asdict(self)

    def save(self, path: str | Path) -> None:
        """Save the system profile as JSON or YAML."""
        _save_mapping(Path(path), self.to_dict())

    def matches(self, target_system: str) -> bool:
        """Return whether this profile matches a target system identifier."""
        target = target_system.lower()
        names = {self.system_id.lower(), *(alias.lower() for alias in self.aliases)}
        return target in names

    def validate(self) -> List[str]:
        """Return validation warnings for missing or suspicious capability data."""
        warnings: List[str] = []

        if not self.system_id:
            warnings.append("system_id is required")
        if not self.display_name:
            warnings.append("display_name is required")

        colors_per_palette = self.palettes.get("colors_per_palette")
        if not isinstance(colors_per_palette, int) or colors_per_palette <= 0:
            warnings.append("palettes.colors_per_palette should be a positive integer")

        palette_count = self.palettes.get("count")
        if not isinstance(palette_count, int) or palette_count <= 0:
            warnings.append("palettes.count should be a positive integer")

        transparent_index = self.palettes.get("transparent_index")
        if isinstance(transparent_index, int) and isinstance(colors_per_palette, int):
            if transparent_index >= colors_per_palette:
                warnings.append("palettes.transparent_index exceeds colors_per_palette")

        max_unique_tiles = self.tiles.get("max_unique_tiles")
        if max_unique_tiles is not None and int(max_unique_tiles) <= 0:
            warnings.append("tiles.max_unique_tiles should be positive")

        sprites_per_scanline = self.sprites.get("sprites_per_scanline")
        if sprites_per_scanline is not None and int(sprites_per_scanline) <= 0:
            warnings.append("sprites.sprites_per_scanline should be positive")

        return warnings


@dataclass
class GameArtDirectionProfile:
    """
    Per-game art direction inside a target system's capability envelope.

    This profile is expected to vary between games, genres, scenes, and visual
    experiments. It should not redefine what the target machine can do.
    """

    game_id: str
    display_name: str
    target_system: str
    profile_version: int = 1
    mood: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    palette_language: ProfileData = field(default_factory=dict)
    outline_rules: ProfileData = field(default_factory=dict)
    rendering_rules: ProfileData = field(default_factory=dict)
    asset_roles: ProfileData = field(default_factory=dict)
    scene_rules: ProfileData = field(default_factory=dict)
    protected_colors: List[ProfileData] = field(default_factory=list)
    protected_ramps: List[ProfileData] = field(default_factory=list)
    scoring_weights: ProfileData = field(default_factory=dict)
    export_preferences: ProfileData = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: ProfileData) -> "GameArtDirectionProfile":
        """Create a game art direction profile from a dictionary."""
        return cls(
            game_id=data["game_id"],
            display_name=data["display_name"],
            target_system=data["target_system"],
            profile_version=int(data.get("profile_version", 1)),
            mood=list(data.get("mood", [])),
            references=list(data.get("references", [])),
            palette_language=dict(data.get("palette_language", {})),
            outline_rules=dict(data.get("outline_rules", {})),
            rendering_rules=dict(data.get("rendering_rules", {})),
            asset_roles=dict(data.get("asset_roles", {})),
            scene_rules=dict(data.get("scene_rules", {})),
            protected_colors=list(data.get("protected_colors", [])),
            protected_ramps=list(data.get("protected_ramps", [])),
            scoring_weights=dict(data.get("scoring_weights", {})),
            export_preferences=dict(data.get("export_preferences", {})),
            notes=list(data.get("notes", [])),
        )

    @classmethod
    def load(cls, path: str | Path) -> "GameArtDirectionProfile":
        """Load a game art direction profile from JSON or YAML."""
        return cls.from_dict(_load_mapping(Path(path)))

    def to_dict(self) -> ProfileData:
        """Convert the game profile to a JSON/YAML-compatible dictionary."""
        return asdict(self)

    def save(self, path: str | Path) -> None:
        """Save the game profile as JSON or YAML."""
        _save_mapping(Path(path), self.to_dict())

    def validate(self) -> List[str]:
        """Return validation warnings for missing or suspicious direction data."""
        warnings: List[str] = []

        if not self.game_id:
            warnings.append("game_id is required")
        if not self.display_name:
            warnings.append("display_name is required")
        if not self.target_system:
            warnings.append("target_system is required")

        for name, weight in self.scoring_weights.items():
            if not isinstance(weight, (int, float)) or weight < 0:
                warnings.append(f"scoring_weights.{name} should be a non-negative number")

        return warnings


@dataclass
class ArtOptimizationContract:
    """
    The merged contract consumed by future art optimization passes.

    It preserves the boundary between fixed machine capability and per-game taste
    while giving downstream planners one object to validate and score against.
    """

    system: SystemCapabilityProfile
    art_direction: GameArtDirectionProfile
    profile_version: int = 1

    @classmethod
    def from_profiles(
        cls,
        system: SystemCapabilityProfile,
        art_direction: GameArtDirectionProfile,
    ) -> "ArtOptimizationContract":
        """Create and validate a contract from loaded profiles."""
        contract = cls(system=system, art_direction=art_direction)
        errors = contract.validate()
        if errors:
            raise ArtProfileError("; ".join(errors))
        return contract

    @classmethod
    def load(
        cls,
        system_path: str | Path,
        art_direction_path: str | Path,
    ) -> "ArtOptimizationContract":
        """Load system and game profiles and merge them into a contract."""
        system = SystemCapabilityProfile.load(system_path)
        art_direction = GameArtDirectionProfile.load(art_direction_path)
        return cls.from_profiles(system, art_direction)

    def validate(self) -> List[str]:
        """Return contract-level validation errors and warnings."""
        issues = []
        issues.extend(self.system.validate())
        issues.extend(self.art_direction.validate())

        if not self.system.matches(self.art_direction.target_system):
            issues.append(
                "art_direction.target_system does not match the system profile "
                f"({self.art_direction.target_system!r} vs {self.system.system_id!r})"
            )

        return issues

    @property
    def scoring_weights(self) -> ProfileData:
        """Return system default scoring weights overridden by game direction."""
        defaults = dict(self.system.optimization_defaults.get("scoring_weights", {}))
        defaults.update(self.art_direction.scoring_weights)
        return defaults

    def to_dict(self) -> ProfileData:
        """Convert the merged contract to a JSON/YAML-compatible dictionary."""
        return {
            "profile_version": self.profile_version,
            "system": self.system.to_dict(),
            "art_direction": self.art_direction.to_dict(),
            "scoring_weights": self.scoring_weights,
        }

    def save(self, path: str | Path) -> None:
        """Save the merged contract as JSON or YAML."""
        _save_mapping(Path(path), self.to_dict())

    def summary(self) -> ProfileData:
        """Return a compact summary for logs, doctor output, and dry-run reports."""
        return {
            "system_id": self.system.system_id,
            "system_name": self.system.display_name,
            "game_id": self.art_direction.game_id,
            "game_name": self.art_direction.display_name,
            "palette_count": self.system.palettes.get("count"),
            "colors_per_palette": self.system.palettes.get("colors_per_palette"),
            "target_system": self.art_direction.target_system,
            "mood": self.art_direction.mood,
            "scoring_weights": self.scoring_weights,
        }


def load_art_optimization_contract(
    system_path: str | Path,
    art_direction_path: str | Path,
) -> ArtOptimizationContract:
    """Convenience wrapper for loading a merged art optimization contract."""
    return ArtOptimizationContract.load(system_path, art_direction_path)
