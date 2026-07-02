"""
Dry-run art optimization reports for ARDK assets.

The optimizer does not mutate source art. It evaluates assets against an
ArtOptimizationContract and reports art-quality and hardware-pressure signals.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
from math import ceil
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
import argparse
import json

from .art_profiles import ArtOptimizationContract, load_art_optimization_contract
from .palettes.genesis_palettes import rgb_to_genesis_vdp, snap_to_genesis_color

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    Image = None
    HAS_PILLOW = False


RGB = Tuple[int, int, int]
RGBA = Tuple[int, int, int, int]


@dataclass
class SceneAsset:
    """One asset entry in a visible-together scene manifest."""

    path: str
    role: str = "unknown"
    asset_id: Optional[str] = None
    visible: bool = True
    layer: Optional[str] = None
    palette_role: Optional[str] = None
    max_simultaneous: int = 1
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(
        cls,
        data: str | Dict[str, Any],
        base_dir: Optional[Path] = None,
    ) -> "SceneAsset":
        """Create a scene asset from a path string or mapping."""
        if isinstance(data, str):
            data = {"path": data}

        path_value = data["path"]
        asset_path = Path(path_value)
        if base_dir and not asset_path.is_absolute():
            asset_path = (base_dir / asset_path).resolve()

        return cls(
            path=str(asset_path),
            role=data.get("role", "unknown"),
            asset_id=data.get("asset_id"),
            visible=bool(data.get("visible", True)),
            layer=data.get("layer"),
            palette_role=data.get("palette_role"),
            max_simultaneous=max(1, int(data.get("max_simultaneous", 1))),
            tags=list(data.get("tags", [])),
            metadata=dict(data.get("metadata", {})),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-compatible dictionary."""
        return asdict(self)


@dataclass
class ArtSceneManifest:
    """A list of assets expected to be visible together in one scene."""

    scene_id: str
    display_name: str
    target_system: str
    assets: List[SceneAsset] = field(default_factory=list)
    scene_type: str = "unknown"
    notes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        base_dir: Optional[Path] = None,
    ) -> "ArtSceneManifest":
        """Create a scene manifest from a dictionary."""
        assets = [
            SceneAsset.from_dict(asset_data, base_dir=base_dir)
            for asset_data in data.get("assets", [])
        ]
        return cls(
            scene_id=data["scene_id"],
            display_name=data["display_name"],
            target_system=data.get("target_system", ""),
            assets=assets,
            scene_type=data.get("scene_type", "unknown"),
            notes=list(data.get("notes", [])),
            metadata=dict(data.get("metadata", {})),
        )

    @classmethod
    def load(cls, path: str | Path) -> "ArtSceneManifest":
        """Load a scene manifest from JSON or YAML."""
        path = Path(path)
        return cls.from_dict(_load_mapping(path), base_dir=path.parent)

    @property
    def visible_assets(self) -> List[SceneAsset]:
        """Return assets marked visible in this scene."""
        return [asset for asset in self.assets if asset.visible]

    def roles_by_path(self) -> Dict[str, str]:
        """Return visible asset roles keyed by resolved path string."""
        return {asset.path: asset.role for asset in self.visible_assets}

    def summary(self) -> Dict[str, Any]:
        """Return scene summary metadata for reports."""
        return {
            "scene_id": self.scene_id,
            "scene_name": self.display_name,
            "scene_type": self.scene_type,
            "target_system": self.target_system,
            "visible_assets": len(self.visible_assets),
            "asset_instances": sum(asset.max_simultaneous for asset in self.visible_assets),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-compatible dictionary."""
        return {
            "scene_id": self.scene_id,
            "display_name": self.display_name,
            "target_system": self.target_system,
            "scene_type": self.scene_type,
            "assets": [asset.to_dict() for asset in self.assets],
            "notes": self.notes,
            "metadata": self.metadata,
        }


@dataclass
class ArtOptimizationIssue:
    """One dry-run issue discovered while evaluating art."""

    severity: str
    code: str
    message: str
    asset_path: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-compatible dictionary."""
        return asdict(self)


@dataclass
class TilePressureStats:
    """Tile reuse and VRAM pressure estimates for one asset."""

    total_tiles: int
    unique_tiles_exact: int
    unique_tiles_with_flips: int
    tile_reuse_ratio: float
    flip_reuse_savings: int
    estimated_vram_bytes: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-compatible dictionary."""
        return asdict(self)


@dataclass
class ColorPressureStats:
    """Color and palette pressure estimates for one asset."""

    visible_pixels: int
    transparent_pixels: int
    conventional_transparency_pixels: int
    unique_source_colors: int
    unique_snapped_colors: int
    estimated_palettes_needed: int
    average_snap_error: float
    max_snap_error: float
    snapped_colors: List[List[int]] = field(default_factory=list)
    top_colors: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-compatible dictionary."""
        return asdict(self)


@dataclass
class AssetOptimizationAnalysis:
    """Dry-run analysis for one asset."""

    asset_path: str
    role: str
    width: int
    height: int
    mode: str
    color: ColorPressureStats
    tiles: TilePressureStats
    estimated_sprite_cells: int
    estimated_sprites_per_scanline: int
    issues: List[ArtOptimizationIssue] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-compatible dictionary."""
        data = asdict(self)
        data["color"] = self.color.to_dict()
        data["tiles"] = self.tiles.to_dict()
        data["issues"] = [issue.to_dict() for issue in self.issues]
        return data


@dataclass
class PaletteAssetAssignment:
    """One asset's proposed assignment to a hardware palette slot."""

    asset_path: str
    role: str
    assigned_palette: str
    requested_palette: Optional[str]
    asset_id: Optional[str]
    unique_snapped_colors: int
    estimated_palettes_needed: int
    status: str
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-compatible dictionary."""
        return asdict(self)


@dataclass
class PaletteSlotPlan:
    """Dry-run recommendation for one hardware palette slot."""

    palette_role: str
    purpose: str
    usable_colors: int
    unique_snapped_colors: int
    colors_remaining: int
    status: str
    assigned_assets: List[PaletteAssetAssignment] = field(default_factory=list)
    snapped_colors: List[List[int]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-compatible dictionary."""
        return {
            "palette_role": self.palette_role,
            "purpose": self.purpose,
            "usable_colors": self.usable_colors,
            "unique_snapped_colors": self.unique_snapped_colors,
            "colors_remaining": self.colors_remaining,
            "status": self.status,
            "assigned_assets": [
                assignment.to_dict() for assignment in self.assigned_assets
            ],
            "snapped_colors": self.snapped_colors,
            "recommendations": self.recommendations,
        }


@dataclass
class ArtOptimizationReport:
    """Dry-run report for a group of assets."""

    contract_summary: Dict[str, Any]
    assets: List[AssetOptimizationAnalysis]
    issues: List[ArtOptimizationIssue]
    totals: Dict[str, Any]
    verdict: Dict[str, str]
    scene_summary: Optional[Dict[str, Any]] = None
    palette_plan: List[PaletteSlotPlan] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-compatible dictionary."""
        data = {
            "contract_summary": self.contract_summary,
            "assets": [asset.to_dict() for asset in self.assets],
            "issues": [issue.to_dict() for issue in self.issues],
            "totals": self.totals,
            "verdict": self.verdict,
        }
        if self.scene_summary:
            data["scene_summary"] = self.scene_summary
        if self.palette_plan:
            data["palette_plan"] = [slot.to_dict() for slot in self.palette_plan]
        return data

    def to_json(self, indent: int = 2) -> str:
        """Serialize the report as JSON."""
        return json.dumps(self.to_dict(), indent=indent)

    def save(self, path: str | Path) -> None:
        """Save the report to disk as JSON."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json(), encoding="utf-8")

    def format_human(self) -> str:
        """Return a compact human-readable report."""
        lines = [
            "ARDK Art Optimization Report",
            f"System: {self.contract_summary.get('system_name')}",
            f"Game: {self.contract_summary.get('game_name')}",
        ]

        if self.scene_summary:
            lines.append(f"Scene: {self.scene_summary.get('scene_name')}")
            lines.append(
                "Scene Assets: "
                f"{self.scene_summary.get('visible_assets')} visible / "
                f"{self.scene_summary.get('asset_instances')} instance(s)"
            )

        lines.extend(
            [
                f"Assets: {len(self.assets)}",
                (
                    "Verdict: "
                    f"art={self.verdict['art_quality']} "
                    f"hardware={self.verdict['hardware_fit']} "
                    f"palette={self.verdict['palette_fit']}"
                ),
                "",
            ]
        )

        for asset in self.assets:
            lines.extend(
                [
                    f"- {asset.asset_path}",
                    f"  role={asset.role} size={asset.width}x{asset.height}",
                    (
                        "  colors="
                        f"{asset.color.unique_source_colors} source / "
                        f"{asset.color.unique_snapped_colors} Genesis-snapped / "
                        f"{asset.color.estimated_palettes_needed} palette(s)"
                    ),
                    (
                        "  tiles="
                        f"{asset.tiles.total_tiles} total / "
                        f"{asset.tiles.unique_tiles_with_flips} unique with flips / "
                        f"{asset.tiles.estimated_vram_bytes} bytes"
                    ),
                ]
            )
            for issue in asset.issues:
                lines.append(f"  [{issue.severity.upper()}] {issue.code}: {issue.message}")

        if self.palette_plan:
            lines.append("")
            lines.append("Palette plan:")
            for slot in self.palette_plan:
                assets = ", ".join(
                    assignment.asset_id or Path(assignment.asset_path).name
                    for assignment in slot.assigned_assets
                ) or "empty"
                lines.append(
                    f"- {slot.palette_role} ({slot.purpose}): "
                    f"{slot.unique_snapped_colors}/{slot.usable_colors} colors, "
                    f"{slot.status}, assets={assets}"
                )
                for recommendation in slot.recommendations:
                    lines.append(f"  - {recommendation}")

        if self.issues:
            lines.append("")
            lines.append("Scene issues:")
            for issue in self.issues:
                lines.append(f"- [{issue.severity.upper()}] {issue.code}: {issue.message}")

        return "\n".join(lines)


class ArtOptimizer:
    """Analyze assets against an art optimization contract without mutating them."""

    def __init__(self, contract: ArtOptimizationContract):
        self.contract = contract
        self.system = contract.system
        self.art_direction = contract.art_direction
        self.tile_width = int(self.system.tiles.get("tile_width", 8))
        self.tile_height = int(self.system.tiles.get("tile_height", 8))
        self.colors_per_palette = int(self.system.palettes.get("colors_per_palette", 16))
        self.usable_colors_per_palette = int(
            self.system.palettes.get(
                "usable_colors_per_palette",
                max(1, self.colors_per_palette - 1),
            )
        )
        self.palette_count = int(self.system.palettes.get("count", 4))
        self.transparent_rgb = tuple(
            self.system.palettes.get("conventional_transparency_rgb", [255, 0, 255])
        )
        self.max_sprite_width = int(self.system.sprites.get("max_sprite_width", 32))
        self.max_sprite_height = int(self.system.sprites.get("max_sprite_height", 32))
        self.sprites_per_scanline = int(self.system.sprites.get("sprites_per_scanline", 20))
        self.bytes_per_tile = int(self.system.tiles.get("bytes_per_tile", 32))

    def analyze_assets(
        self,
        asset_paths: Sequence[str | Path],
        roles: Optional[Dict[str, str]] = None,
    ) -> ArtOptimizationReport:
        """Analyze assets and return a dry-run report."""
        if not HAS_PILLOW:
            raise ImportError("Pillow is required for art optimization reports")

        roles = roles or {}
        analyses = [
            self.analyze_asset(Path(asset_path), role=roles.get(str(asset_path)))
            for asset_path in asset_paths
        ]

        scene_assets = [
            SceneAsset(path=analysis.asset_path, role=analysis.role)
            for analysis in analyses
        ]
        palette_plan, palette_issues = self._build_palette_plan(analyses, scene_assets)
        report_issues = self._scene_issues(analyses)
        report_issues.extend(palette_issues)
        totals = self._calculate_totals(analyses)
        verdict = self._calculate_verdict(analyses, report_issues, totals)

        return ArtOptimizationReport(
            contract_summary=self.contract.summary(),
            assets=analyses,
            issues=report_issues,
            totals=totals,
            verdict=verdict,
            palette_plan=palette_plan,
        )

    def analyze_scene(self, scene: ArtSceneManifest) -> ArtOptimizationReport:
        """Analyze all visible assets in a scene manifest."""
        visible_assets = scene.visible_assets
        roles = {asset.path: asset.role for asset in visible_assets}
        analyses = [
            self.analyze_asset(asset.path, role=roles.get(asset.path))
            for asset in visible_assets
        ]

        palette_plan, palette_issues = self._build_palette_plan(analyses, visible_assets)
        report_issues = self._scene_issues(analyses)
        report_issues.extend(palette_issues)
        report_issues.extend(self._manifest_issues(scene, visible_assets, analyses))
        totals = self._calculate_totals(analyses)
        totals["scene_asset_instances"] = sum(
            asset.max_simultaneous for asset in visible_assets
        )
        verdict = self._calculate_verdict(analyses, report_issues, totals)

        return ArtOptimizationReport(
            contract_summary=self.contract.summary(),
            assets=analyses,
            issues=report_issues,
            totals=totals,
            verdict=verdict,
            scene_summary=scene.summary(),
            palette_plan=palette_plan,
        )

    def analyze_asset(
        self,
        asset_path: str | Path,
        role: Optional[str] = None,
    ) -> AssetOptimizationAnalysis:
        """Analyze one image asset."""
        if not HAS_PILLOW:
            raise ImportError("Pillow is required for art optimization reports")

        path = Path(asset_path)
        inferred_role = role or self._infer_role(path)
        with Image.open(path) as image:
            original_mode = image.mode
            rgba = image.convert("RGBA")

        color_stats = self._analyze_colors(rgba)
        tile_stats = self._analyze_tiles(rgba)
        sprite_cells = self._estimate_sprite_cells(rgba.width, rgba.height)
        sprites_per_scanline = max(1, ceil(rgba.width / self.max_sprite_width))

        issues = self._asset_issues(
            path=path,
            role=inferred_role,
            width=rgba.width,
            height=rgba.height,
            color=color_stats,
            tiles=tile_stats,
            estimated_sprite_cells=sprite_cells,
            estimated_sprites_per_scanline=sprites_per_scanline,
        )

        return AssetOptimizationAnalysis(
            asset_path=str(path),
            role=inferred_role,
            width=rgba.width,
            height=rgba.height,
            mode=original_mode,
            color=color_stats,
            tiles=tile_stats,
            estimated_sprite_cells=sprite_cells,
            estimated_sprites_per_scanline=sprites_per_scanline,
            issues=issues,
        )

    def _analyze_colors(self, image: "Image.Image") -> ColorPressureStats:
        color_counts: Counter[RGB] = Counter()
        transparent_pixels = 0
        conventional_transparency_pixels = 0

        for r, g, b, a in _image_pixels(image):
            rgb = (r, g, b)
            if a < 128:
                transparent_pixels += 1
                continue
            if rgb == self.transparent_rgb:
                conventional_transparency_pixels += 1
                continue
            color_counts[rgb] += 1

        snapped_counts: Counter[RGB] = Counter()
        total_error = 0.0
        max_error = 0.0
        for rgb, count in color_counts.items():
            snapped = self._snap_color(rgb)
            error = _rgb_distance(rgb, snapped)
            total_error += error * count
            max_error = max(max_error, error)
            snapped_counts[snapped] += count

        visible_pixels = sum(color_counts.values())
        average_error = total_error / visible_pixels if visible_pixels else 0.0
        estimated_palettes = ceil(len(snapped_counts) / self.usable_colors_per_palette)

        top_colors = []
        for rgb, count in color_counts.most_common(16):
            snapped = self._snap_color(rgb)
            top_colors.append(
                {
                    "rgb": list(rgb),
                    "count": count,
                    "snapped_rgb": list(snapped),
                    "genesis_vdp": f"0x{rgb_to_genesis_vdp(*snapped):03X}",
                }
            )

        return ColorPressureStats(
            visible_pixels=visible_pixels,
            transparent_pixels=transparent_pixels,
            conventional_transparency_pixels=conventional_transparency_pixels,
            unique_source_colors=len(color_counts),
            unique_snapped_colors=len(snapped_counts),
            estimated_palettes_needed=estimated_palettes,
            average_snap_error=round(average_error, 3),
            max_snap_error=round(max_error, 3),
            snapped_colors=[list(rgb) for rgb in sorted(snapped_counts.keys())],
            top_colors=top_colors,
        )

    def _analyze_tiles(self, image: "Image.Image") -> TilePressureStats:
        tiles = list(_iter_tiles(image, self.tile_width, self.tile_height))
        exact_unique = {tile for tile in tiles}
        canonical_unique = {_canonical_tile(tile, self.tile_width, self.tile_height) for tile in tiles}
        unique_with_flips = len(canonical_unique)
        total_tiles = len(tiles)
        reuse_ratio = total_tiles / unique_with_flips if unique_with_flips else 1.0

        return TilePressureStats(
            total_tiles=total_tiles,
            unique_tiles_exact=len(exact_unique),
            unique_tiles_with_flips=unique_with_flips,
            tile_reuse_ratio=round(reuse_ratio, 3),
            flip_reuse_savings=max(0, len(exact_unique) - unique_with_flips),
            estimated_vram_bytes=unique_with_flips * self.bytes_per_tile,
        )

    def _asset_issues(
        self,
        path: Path,
        role: str,
        width: int,
        height: int,
        color: ColorPressureStats,
        tiles: TilePressureStats,
        estimated_sprite_cells: int,
        estimated_sprites_per_scanline: int,
    ) -> List[ArtOptimizationIssue]:
        issues: List[ArtOptimizationIssue] = []
        asset = str(path)

        if width % self.tile_width != 0 or height % self.tile_height != 0:
            issues.append(
                ArtOptimizationIssue(
                    severity="warning",
                    code="TILE_ALIGNMENT",
                    message="Asset dimensions are not aligned to the system tile grid.",
                    asset_path=asset,
                    details={"tile_width": self.tile_width, "tile_height": self.tile_height},
                )
            )

        if color.conventional_transparency_pixels > 0:
            issues.append(
                ArtOptimizationIssue(
                    severity="info",
                    code="CONVENTIONAL_TRANSPARENCY_COLOR",
                    message="Asset uses the conventional transparency color; ensure it maps to palette index 0.",
                    asset_path=asset,
                    details={"pixels": color.conventional_transparency_pixels},
                )
            )

        if color.unique_snapped_colors > self.usable_colors_per_palette:
            issues.append(
                ArtOptimizationIssue(
                    severity="warning",
                    code="SINGLE_PALETTE_PRESSURE",
                    message="Asset needs more colors than one usable hardware palette can hold.",
                    asset_path=asset,
                    details={
                        "unique_snapped_colors": color.unique_snapped_colors,
                        "usable_colors_per_palette": self.usable_colors_per_palette,
                        "estimated_palettes_needed": color.estimated_palettes_needed,
                    },
                )
            )

        if color.unique_source_colors > color.unique_snapped_colors * 2:
            issues.append(
                ArtOptimizationIssue(
                    severity="info",
                    code="SOURCE_COLOR_NOISE",
                    message="Many source colors collapse to fewer hardware colors; check ramps and anti-aliasing.",
                    asset_path=asset,
                    details={
                        "unique_source_colors": color.unique_source_colors,
                        "unique_snapped_colors": color.unique_snapped_colors,
                    },
                )
            )

        if color.average_snap_error > 18:
            issues.append(
                ArtOptimizationIssue(
                    severity="warning",
                    code="HIGH_CRAM_SNAP_ERROR",
                    message="Average color shift after Genesis snapping is high.",
                    asset_path=asset,
                    details={
                        "average_snap_error": color.average_snap_error,
                        "max_snap_error": color.max_snap_error,
                    },
                )
            )

        if role not in {"background", "world_background", "tileset", "ui"}:
            if width > self.max_sprite_width or height > self.max_sprite_height:
                issues.append(
                    ArtOptimizationIssue(
                        severity="info",
                        code="METASPRITE_REQUIRED",
                        message="Asset exceeds one hardware sprite cell and will need metasprite composition.",
                        asset_path=asset,
                        details={
                            "max_sprite_width": self.max_sprite_width,
                            "max_sprite_height": self.max_sprite_height,
                            "estimated_sprite_cells": estimated_sprite_cells,
                        },
                    )
                )

            if estimated_sprites_per_scanline > self.sprites_per_scanline:
                issues.append(
                    ArtOptimizationIssue(
                        severity="error",
                        code="SPRITE_SCANLINE_OVER_BUDGET",
                        message="Asset alone can exceed the per-scanline sprite limit.",
                        asset_path=asset,
                        details={
                            "estimated_sprites_per_scanline": estimated_sprites_per_scanline,
                            "sprites_per_scanline_budget": self.sprites_per_scanline,
                        },
                    )
                )

        practical_tile_budget = self.system.tiles.get("practical_art_tile_budget")
        if practical_tile_budget and tiles.unique_tiles_with_flips > int(practical_tile_budget):
            issues.append(
                ArtOptimizationIssue(
                    severity="warning",
                    code="ASSET_TILE_BUDGET_PRESSURE",
                    message="Asset consumes more unique tiles than the practical art tile budget.",
                    asset_path=asset,
                    details={
                        "unique_tiles_with_flips": tiles.unique_tiles_with_flips,
                        "practical_art_tile_budget": practical_tile_budget,
                    },
                )
            )

        return issues

    def _build_palette_plan(
        self,
        analyses: Sequence[AssetOptimizationAnalysis],
        scene_assets: Sequence[SceneAsset],
    ) -> Tuple[List[PaletteSlotPlan], List[ArtOptimizationIssue]]:
        palette_roles = [f"PAL{index}" for index in range(self.palette_count)]
        preferred_roles = self.system.optimization_defaults.get("preferred_palette_roles", {})
        slots: Dict[str, Dict[str, Any]] = {
            role: {
                "purpose": preferred_roles.get(role, "unassigned"),
                "assignments": [],
                "colors": set(),
            }
            for role in palette_roles
        }
        issues: List[ArtOptimizationIssue] = []
        scene_assets_by_path = {
            _path_key(asset.path): asset
            for asset in scene_assets
        }

        for analysis in analyses:
            scene_asset = scene_assets_by_path.get(
                _path_key(analysis.asset_path),
                SceneAsset(path=analysis.asset_path, role=analysis.role),
            )
            requested_palette = scene_asset.palette_role or self._desired_palette_for_role(
                analysis.role
            )
            assigned_palette = self._valid_or_fallback_palette(
                requested_palette,
                analysis.role,
                slots,
            )
            snapped_colors = {tuple(color) for color in analysis.color.snapped_colors}
            slot = slots[assigned_palette]
            slot["colors"].update(snapped_colors)

            recommendations = self._asset_palette_recommendations(
                analysis,
                assigned_palette,
            )
            status = "fits"
            if analysis.color.unique_snapped_colors > self.usable_colors_per_palette:
                status = "needs_reduction_or_split"

            assignment = PaletteAssetAssignment(
                asset_path=analysis.asset_path,
                role=analysis.role,
                assigned_palette=assigned_palette,
                requested_palette=requested_palette,
                asset_id=scene_asset.asset_id,
                unique_snapped_colors=analysis.color.unique_snapped_colors,
                estimated_palettes_needed=analysis.color.estimated_palettes_needed,
                status=status,
                recommendations=recommendations,
            )
            slot["assignments"].append(assignment)

            if requested_palette and requested_palette not in palette_roles:
                issues.append(
                    ArtOptimizationIssue(
                        severity="warning",
                        code="INVALID_PALETTE_ROLE",
                        message="Asset requested a palette role not exposed by this system profile.",
                        asset_path=analysis.asset_path,
                        details={
                            "requested_palette": requested_palette,
                            "assigned_palette": assigned_palette,
                            "valid_palette_roles": palette_roles,
                        },
                    )
                )

        palette_plan: List[PaletteSlotPlan] = []
        for palette_role in palette_roles:
            slot = slots[palette_role]
            colors = sorted(slot["colors"])
            unique_color_count = len(colors)
            colors_remaining = self.usable_colors_per_palette - unique_color_count
            recommendations = self._slot_palette_recommendations(
                palette_role,
                slot["purpose"],
                slot["assignments"],
                unique_color_count,
            )

            if not slot["assignments"]:
                status = "empty"
            elif unique_color_count > self.usable_colors_per_palette:
                status = "over_budget"
                issues.append(
                    ArtOptimizationIssue(
                        severity="warning",
                        code="PALETTE_SLOT_OVER_BUDGET",
                        message="Assigned assets exceed the usable color budget for one hardware palette.",
                        details={
                            "palette_role": palette_role,
                            "unique_snapped_colors": unique_color_count,
                            "usable_colors_per_palette": self.usable_colors_per_palette,
                            "assigned_assets": [
                                assignment.asset_id or assignment.asset_path
                                for assignment in slot["assignments"]
                            ],
                        },
                    )
                )
            elif colors_remaining <= 2:
                status = "tight"
            else:
                status = "fits"

            palette_plan.append(
                PaletteSlotPlan(
                    palette_role=palette_role,
                    purpose=slot["purpose"],
                    usable_colors=self.usable_colors_per_palette,
                    unique_snapped_colors=unique_color_count,
                    colors_remaining=colors_remaining,
                    status=status,
                    assigned_assets=slot["assignments"],
                    snapped_colors=[list(color) for color in colors],
                    recommendations=recommendations,
                )
            )

        return palette_plan, issues

    def _desired_palette_for_role(self, role: str) -> Optional[str]:
        role_keys = self._role_lookup_keys(role)
        for key in role_keys:
            role_policy = self.art_direction.asset_roles.get(key, {})
            if isinstance(role_policy, dict) and role_policy.get("desired_palette"):
                return role_policy["desired_palette"]

        fallback = {
            "world_background": "PAL0",
            "background": "PAL0",
            "tileset": "PAL0",
            "player": "PAL1",
            "hero": "PAL1",
            "enemies": "PAL2",
            "enemy": "PAL2",
            "npc": "PAL2",
            "ui": "PAL3",
            "hud": "PAL3",
            "fx": "PAL3",
            "effect": "PAL3",
        }
        for key in role_keys:
            if key in fallback:
                return fallback[key]

        return None

    def _valid_or_fallback_palette(
        self,
        requested_palette: Optional[str],
        role: str,
        slots: Dict[str, Dict[str, Any]],
    ) -> str:
        palette_roles = [f"PAL{index}" for index in range(self.palette_count)]
        if requested_palette in palette_roles:
            return requested_palette

        desired = self._desired_palette_for_role(role)
        if desired in palette_roles:
            return desired

        return min(
            palette_roles,
            key=lambda palette_role: (
                len(slots[palette_role]["assignments"]),
                len(slots[palette_role]["colors"]),
            ),
        )

    def _asset_palette_recommendations(
        self,
        analysis: AssetOptimizationAnalysis,
        assigned_palette: str,
    ) -> List[str]:
        recommendations: List[str] = []
        if analysis.color.unique_snapped_colors > self.usable_colors_per_palette:
            excess = analysis.color.unique_snapped_colors - self.usable_colors_per_palette
            recommendations.append(
                f"Reduce or merge at least {excess} snapped color(s), "
                f"or split this asset across multiple palettes before assigning to {assigned_palette}."
            )
        if analysis.color.estimated_palettes_needed > 1:
            recommendations.append(
                "Review protected ramps and accents before automatic color merging."
            )
        return recommendations

    def _slot_palette_recommendations(
        self,
        palette_role: str,
        purpose: str,
        assignments: Sequence[PaletteAssetAssignment],
        unique_color_count: int,
    ) -> List[str]:
        recommendations: List[str] = []
        if not assignments:
            recommendations.append("Reserve this slot for scene-specific overrides or future assets.")
            return recommendations

        if unique_color_count > self.usable_colors_per_palette:
            excess = unique_color_count - self.usable_colors_per_palette
            recommendations.append(
                f"Palette {palette_role} is {excess} color(s) over budget; "
                "merge ramps, share outlines/neutrals, or move one asset to another slot."
            )
        elif self.usable_colors_per_palette - unique_color_count <= 2:
            recommendations.append(
                f"Palette {palette_role} is tight; avoid adding more accents to {purpose}."
            )
        else:
            recommendations.append(
                f"Palette {palette_role} has room for shared accents or a small FX ramp."
            )

        if len(assignments) > 1:
            recommendations.append(
                "Shared slot: compare combined contact sheets before committing this assignment."
            )

        return recommendations

    def _role_lookup_keys(self, role: str) -> List[str]:
        normalized = (role or "unknown").lower()
        aliases = {
            "enemy": "enemies",
            "monster": "enemies",
            "npc": "enemies",
            "background": "world_background",
            "bg": "world_background",
            "hud": "ui",
            "effect": "fx",
            "projectile": "fx",
        }
        keys = [normalized]
        if normalized in aliases:
            keys.append(aliases[normalized])
        if normalized.endswith("s"):
            keys.append(normalized[:-1])
        return list(dict.fromkeys(keys))

    def _scene_issues(
        self,
        analyses: Sequence[AssetOptimizationAnalysis],
    ) -> List[ArtOptimizationIssue]:
        issues: List[ArtOptimizationIssue] = []
        snapped_scene_colors = set()
        for analysis in analyses:
            for color in analysis.color.snapped_colors:
                snapped_scene_colors.add(tuple(color))

        estimated_scene_palettes = ceil(len(snapped_scene_colors) / self.usable_colors_per_palette)
        if estimated_scene_palettes > self.palette_count:
            issues.append(
                ArtOptimizationIssue(
                    severity="warning",
                    code="SCENE_PALETTE_BUDGET_PRESSURE",
                    message="Top scene colors imply more palettes than the system exposes.",
                    details={
                        "estimated_scene_palettes": estimated_scene_palettes,
                        "palette_count": self.palette_count,
                        "top_snapped_scene_colors": len(snapped_scene_colors),
                    },
                )
            )

        total_unique_tiles = sum(asset.tiles.unique_tiles_with_flips for asset in analyses)
        max_unique_tiles = int(self.system.tiles.get("max_unique_tiles", 0) or 0)
        practical_tile_budget = int(self.system.tiles.get("practical_art_tile_budget", 0) or 0)

        if max_unique_tiles and total_unique_tiles > max_unique_tiles:
            issues.append(
                ArtOptimizationIssue(
                    severity="error",
                    code="SCENE_TILE_BUDGET_EXCEEDED",
                    message="Combined assets exceed the system's maximum unique tile budget.",
                    details={
                        "unique_tiles_with_flips": total_unique_tiles,
                        "max_unique_tiles": max_unique_tiles,
                    },
                )
            )
        elif practical_tile_budget and total_unique_tiles > practical_tile_budget:
            issues.append(
                ArtOptimizationIssue(
                    severity="warning",
                    code="SCENE_TILE_BUDGET_PRESSURE",
                    message="Combined assets exceed the practical art tile budget.",
                    details={
                        "unique_tiles_with_flips": total_unique_tiles,
                        "practical_art_tile_budget": practical_tile_budget,
                    },
                )
            )

        return issues

    def _manifest_issues(
        self,
        scene: ArtSceneManifest,
        scene_assets: Sequence[SceneAsset],
        analyses: Sequence[AssetOptimizationAnalysis],
    ) -> List[ArtOptimizationIssue]:
        issues: List[ArtOptimizationIssue] = []

        if scene.target_system and not self.system.matches(scene.target_system):
            issues.append(
                ArtOptimizationIssue(
                    severity="error",
                    code="SCENE_TARGET_MISMATCH",
                    message="Scene manifest target does not match the loaded system profile.",
                    details={
                        "scene_target_system": scene.target_system,
                        "system_id": self.system.system_id,
                    },
                )
            )

        analysis_by_path = {analysis.asset_path: analysis for analysis in analyses}
        estimated_scanline_sprites = 0
        sprite_roles = {"player", "enemies", "enemy", "npc", "fx", "unknown"}

        for asset in scene_assets:
            analysis = analysis_by_path.get(asset.path)
            if not analysis or asset.role not in sprite_roles:
                continue
            estimated_scanline_sprites += (
                analysis.estimated_sprites_per_scanline * asset.max_simultaneous
            )

        if estimated_scanline_sprites > self.sprites_per_scanline:
            issues.append(
                ArtOptimizationIssue(
                    severity="warning",
                    code="SCENE_SPRITE_SCANLINE_PRESSURE",
                    message="Scene instances can exceed the per-scanline sprite budget if vertically clustered.",
                    details={
                        "estimated_same_line_sprites": estimated_scanline_sprites,
                        "sprites_per_scanline_budget": self.sprites_per_scanline,
                    },
                )
            )

        desired_palette_roles = Counter(
            asset.palette_role
            for asset in scene_assets
            if asset.palette_role
        )
        overloaded_roles = {
            role: count
            for role, count in desired_palette_roles.items()
            if count > 1 and role in {"PAL0", "PAL1", "PAL2", "PAL3"}
        }
        if overloaded_roles:
            issues.append(
                ArtOptimizationIssue(
                    severity="info",
                    code="SHARED_PALETTE_ROLE",
                    message="Multiple scene assets request the same hardware palette role.",
                    details={"palette_roles": overloaded_roles},
                )
            )

        return issues

    def _calculate_totals(
        self,
        analyses: Sequence[AssetOptimizationAnalysis],
    ) -> Dict[str, Any]:
        severity_counts = Counter()
        for analysis in analyses:
            for issue in analysis.issues:
                severity_counts[issue.severity] += 1

        total_unique_tiles = sum(asset.tiles.unique_tiles_with_flips for asset in analyses)
        total_vram_bytes = sum(asset.tiles.estimated_vram_bytes for asset in analyses)

        return {
            "asset_count": len(analyses),
            "unique_tiles_with_flips": total_unique_tiles,
            "estimated_vram_bytes": total_vram_bytes,
            "max_unique_tiles": self.system.tiles.get("max_unique_tiles"),
            "practical_art_tile_budget": self.system.tiles.get("practical_art_tile_budget"),
            "severity_counts": dict(severity_counts),
        }

    def _calculate_verdict(
        self,
        analyses: Sequence[AssetOptimizationAnalysis],
        scene_issues: Sequence[ArtOptimizationIssue],
        totals: Dict[str, Any],
    ) -> Dict[str, str]:
        all_issues = list(scene_issues)
        for analysis in analyses:
            all_issues.extend(analysis.issues)

        has_error = any(issue.severity == "error" for issue in all_issues)
        has_warning = any(issue.severity == "warning" for issue in all_issues)
        max_snap_error = max(
            (analysis.color.average_snap_error for analysis in analyses),
            default=0.0,
        )

        art_quality = "clean"
        if max_snap_error > 18:
            art_quality = "needs_palette_review"
        elif any(issue.code == "SOURCE_COLOR_NOISE" for issue in all_issues):
            art_quality = "watch_ramps"

        hardware_fit = "legal"
        if has_error:
            hardware_fit = "over_budget"
        elif has_warning:
            hardware_fit = "pressure"

        palette_fit = "ok"
        if any("PALETTE" in issue.code for issue in all_issues):
            palette_fit = "pressure"
        if any(issue.code == "SCENE_PALETTE_BUDGET_PRESSURE" for issue in all_issues):
            palette_fit = "over_budget_likely"

        tile_budget = totals.get("practical_art_tile_budget")
        if tile_budget and totals["unique_tiles_with_flips"] > tile_budget:
            hardware_fit = "tile_pressure"

        return {
            "art_quality": art_quality,
            "hardware_fit": hardware_fit,
            "palette_fit": palette_fit,
        }

    def _snap_color(self, rgb: RGB) -> RGB:
        if self.system.matches("genesis"):
            return snap_to_genesis_color(*rgb)
        return rgb

    def _estimate_sprite_cells(self, width: int, height: int) -> int:
        cells_x = max(1, ceil(width / self.max_sprite_width))
        cells_y = max(1, ceil(height / self.max_sprite_height))
        return cells_x * cells_y

    def _infer_role(self, path: Path) -> str:
        lowered = path.as_posix().lower()
        if any(token in lowered for token in ("background", "/bg", "_bg", "tileset", "tilemap")):
            return "world_background"
        if any(token in lowered for token in ("ui", "hud", "font", "menu")):
            return "ui"
        if any(token in lowered for token in ("fx", "effect", "projectile", "bullet")):
            return "fx"
        if any(token in lowered for token in ("enemy", "npc", "monster")):
            return "enemies"
        if any(token in lowered for token in ("player", "hero", "avatar")):
            return "player"
        return "unknown"


def analyze_assets(
    contract: ArtOptimizationContract,
    asset_paths: Sequence[str | Path],
    roles: Optional[Dict[str, str]] = None,
) -> ArtOptimizationReport:
    """Analyze assets against a loaded contract."""
    return ArtOptimizer(contract).analyze_assets(asset_paths, roles=roles)


def analyze_scene(
    contract: ArtOptimizationContract,
    scene: ArtSceneManifest,
) -> ArtOptimizationReport:
    """Analyze a scene manifest against a loaded contract."""
    return ArtOptimizer(contract).analyze_scene(scene)


def load_and_analyze_assets(
    system_profile: str | Path,
    art_direction_profile: str | Path,
    asset_paths: Sequence[str | Path],
    roles: Optional[Dict[str, str]] = None,
) -> ArtOptimizationReport:
    """Load profiles, merge a contract, and analyze assets."""
    contract = load_art_optimization_contract(system_profile, art_direction_profile)
    return analyze_assets(contract, asset_paths, roles=roles)


def load_and_analyze_scene(
    system_profile: str | Path,
    art_direction_profile: str | Path,
    scene_manifest: str | Path,
) -> ArtOptimizationReport:
    """Load profiles and a scene manifest, then analyze visible assets."""
    contract = load_art_optimization_contract(system_profile, art_direction_profile)
    scene = ArtSceneManifest.load(scene_manifest)
    return analyze_scene(contract, scene)


def _load_mapping(path: Path) -> Dict[str, Any]:
    """Load a JSON or YAML mapping from disk."""
    content = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        if not HAS_YAML:
            raise ImportError(
                "PyYAML is required for YAML scene manifests. "
                "Install with: pip install pyyaml"
            )
        data = yaml.safe_load(content)
    else:
        data = json.loads(content)

    if not isinstance(data, dict):
        raise ValueError(f"Scene manifest must be a mapping: {path}")

    return data


def _path_key(path: str | Path) -> str:
    """Normalize paths for comparing scene manifest entries to analyses."""
    return str(Path(path).resolve()).lower()


def _rgb_distance(a: RGB, b: RGB) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5


def _iter_tiles(image: "Image.Image", tile_width: int, tile_height: int) -> Iterable[bytes]:
    tiles_x = ceil(image.width / tile_width)
    tiles_y = ceil(image.height / tile_height)
    for tile_y in range(tiles_y):
        for tile_x in range(tiles_x):
            x = tile_x * tile_width
            y = tile_y * tile_height
            tile = Image.new("RGBA", (tile_width, tile_height), (0, 0, 0, 0))
            tile.paste(image.crop((x, y, x + tile_width, y + tile_height)), (0, 0))
            yield tile.tobytes()


def _image_pixels(image: "Image.Image") -> Iterable[RGBA]:
    if hasattr(image, "get_flattened_data"):
        return image.get_flattened_data()
    return image.getdata()


def _canonical_tile(tile: bytes, tile_width: int, tile_height: int) -> bytes:
    return min(
        tile,
        _flip_tile_h(tile, tile_width, tile_height),
        _flip_tile_v(tile, tile_width, tile_height),
        _flip_tile_hv(tile, tile_width, tile_height),
    )


def _flip_tile_h(tile: bytes, tile_width: int, tile_height: int) -> bytes:
    rows = _tile_rows(tile, tile_width, tile_height)
    return b"".join(_reverse_pixel_row(row) for row in rows)


def _flip_tile_v(tile: bytes, tile_width: int, tile_height: int) -> bytes:
    return b"".join(reversed(_tile_rows(tile, tile_width, tile_height)))


def _flip_tile_hv(tile: bytes, tile_width: int, tile_height: int) -> bytes:
    return _flip_tile_h(_flip_tile_v(tile, tile_width, tile_height), tile_width, tile_height)


def _tile_rows(tile: bytes, tile_width: int, tile_height: int) -> List[bytes]:
    bytes_per_pixel = 4
    row_size = tile_width * bytes_per_pixel
    return [tile[row * row_size:(row + 1) * row_size] for row in range(tile_height)]


def _reverse_pixel_row(row: bytes) -> bytes:
    bytes_per_pixel = 4
    pixels = [
        row[index:index + bytes_per_pixel]
        for index in range(0, len(row), bytes_per_pixel)
    ]
    return b"".join(reversed(pixels))


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point for dry-run art optimization reports."""
    parser = argparse.ArgumentParser(description="Generate a dry-run art optimization report.")
    parser.add_argument("assets", nargs="*", help="PNG assets to analyze")
    parser.add_argument(
        "--scene-manifest",
        help="Scene manifest describing visible-together assets and roles",
    )
    parser.add_argument(
        "--system-profile",
        default="profiles/systems/genesis.json",
        help="System capability profile path",
    )
    parser.add_argument(
        "--art-direction",
        default="profiles/games/example_genesis_style.json",
        help="Game art direction profile path",
    )
    parser.add_argument("--output", help="Optional JSON report output path")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of human text")
    args = parser.parse_args(argv)

    if args.scene_manifest:
        report = load_and_analyze_scene(
            args.system_profile,
            args.art_direction,
            args.scene_manifest,
        )
    else:
        if not args.assets:
            parser.error("provide at least one asset or --scene-manifest")
        report = load_and_analyze_assets(
            args.system_profile,
            args.art_direction,
            args.assets,
        )

    if args.output:
        report.save(args.output)

    if args.json:
        print(report.to_json())
    else:
        print(report.format_human())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
