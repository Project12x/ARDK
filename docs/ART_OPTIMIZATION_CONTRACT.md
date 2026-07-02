# ARDK Art Optimization Contract

Last updated: 2026-07-01

## Purpose

The art optimization contract is the boundary between what a system can do and what
a game wants to look like.

ARDK should optimize game-specific art direction inside a stable hardware envelope.
It should not make every Genesis, NES, Game Boy, or C64 project share one house style.

## Core Split

### System Capability Profile

System profiles describe hardware and toolchain facts:

- color encoding, palette count, and colors per palette,
- transparency rules and native palette formats,
- tile size, tile budget, flip support, and packing assumptions,
- sprite size, sprite count, and per-scanline limits,
- plane/background rules, priority, and scroll model,
- VRAM/DMA pressure,
- emulator and toolchain validation expectations.

Example: `profiles/systems/genesis.json`

This file should change rarely.

### Game Art Direction Profile

Game profiles describe taste and intent:

- mood, references, palette language, and color accents,
- outline rules, ramp rules, dithering taste, and readability preferences,
- asset roles such as player, enemy, background, UI, and FX,
- protected colors and protected ramps,
- scoring weights for art quality and hardware pressure,
- report/export preferences.

Example: `profiles/games/example_genesis_style.json`

This file should change constantly between games.

## Contract Object

`tools/pipeline/art_profiles.py` exposes:

- `SystemCapabilityProfile`
- `GameArtDirectionProfile`
- `ArtOptimizationContract`
- `load_art_optimization_contract(system_path, art_direction_path)`

The contract validates that the game profile targets the loaded system profile,
then merges system scoring defaults with game-specific scoring weights.

JSON profiles work with no extra dependencies. YAML profiles are also supported when
PyYAML is installed.

Example:

```python
from tools.pipeline.art_profiles import load_art_optimization_contract

contract = load_art_optimization_contract(
    "profiles/systems/genesis.json",
    "profiles/games/example_genesis_style.json",
)

print(contract.summary())
```

## Dry-Run Art Optimization Report

`tools/pipeline/art_optimizer.py` is the first evaluator built on top of the
contract. It does not rewrite, quantize, or export assets. It reads source images and
reports whether they look likely to fit the art direction and target hardware.

It currently reports:

- source color count,
- Genesis-snapped color count,
- estimated palettes needed,
- transparency/index-zero conventions,
- average and maximum Genesis CRAM snap error,
- 8x8 tile count,
- unique tile count with horizontal/vertical flip reuse,
- estimated tile VRAM bytes,
- metasprite pressure,
- per-asset and scene-level warnings.

CLI example:

```powershell
python -m tools.pipeline.art_optimizer `
  --system-profile profiles/systems/genesis.json `
  --art-direction profiles/games/example_genesis_style.json `
  --output art_optimization_report.json `
  tools/epoch_hero_sprite.png
```

Python example:

```python
from tools.pipeline.art_optimizer import load_and_analyze_assets

report = load_and_analyze_assets(
    "profiles/systems/genesis.json",
    "profiles/games/example_genesis_style.json",
    ["tools/epoch_hero_sprite.png"],
)

print(report.format_human())
```

## Scene Manifests

Scene manifests describe which assets are visible together and what role each asset
plays. This gives the optimizer enough context to evaluate shared palette pressure,
sprite scanline pressure, and palette-role conflicts.

Example: `profiles/scenes/example_genesis_scene.json`

Scene manifest fields:

- `scene_id` and `display_name`
- `target_system`
- `scene_type`
- `assets`
- per-asset `path`, `role`, `palette_role`, `layer`, `visible`, and `max_simultaneous`
- optional `tags`, `notes`, and `metadata`

Scene CLI example:

```powershell
python -m tools.pipeline.art_optimizer `
  --system-profile profiles/systems/genesis.json `
  --art-direction profiles/games/example_genesis_style.json `
  --scene-manifest profiles/scenes/example_genesis_scene.json
```

The scene report still mutates nothing. It only reports pressure and likely tradeoffs.

## Palette Slot Plan

Scene reports now include a first-pass `palette_plan` for hardware palette slots such
as Genesis `PAL0`-`PAL3`.

The planner uses:

- explicit per-asset `palette_role` from the scene manifest,
- `desired_palette` from the game art direction profile,
- system default palette purposes from the system capability profile,
- each asset's Genesis-snapped color set.

It reports for each slot:

- intended purpose,
- assigned assets,
- unique snapped colors,
- usable color budget,
- remaining colors,
- status: `empty`, `fits`, `tight`, or `over_budget`,
- recommendations such as merging ramps, sharing outlines/neutrals, moving assets,
  or preserving a slot for future scene-specific overrides.

This is still not a final solver. It is the bridge between "palette pressure exists"
and "here is the first PAL0-PAL3 assignment ARDK recommends."

## Genesis First

Genesis is the first proving ground because it forces useful constraints:

- 4 palettes x 16 colors,
- index 0 transparency conventions,
- 512-color CRAM space,
- 8x8 4bpp tiles,
- 64 KB VRAM,
- 80 sprites total and 20 sprites per scanline,
- SGDK `rescomp` validation,
- BlastEm runtime checks.

The Genesis system profile should not say “dark industrial” or “bold comic.” Those
belong in game art direction profiles.

## First Optimizer Target

The first useful optimizer should be dry-run only.

Inputs:

- a system capability profile,
- a game art direction profile,
- one scene manifest or list of visible assets.

Outputs:

- `art_optimization_report.json`,
- palette slot recommendations,
- protected-color and protected-ramp warnings,
- tile reuse and palette reuse pressure,
- Genesis-specific CRAM/index-zero warnings,
- optional contact sheet and error heatmap later.

## Scoring Categories

Start with these categories:

- `palette_fit`
- `ramp_preservation`
- `silhouette_contrast`
- `palette_reuse`
- `tile_reuse`
- `sprite_scanline_safety`
- `vram_pressure`
- `dma_pressure`
- `shadow_highlight_safety`

System profiles provide sane defaults. Game profiles override priorities.

## Non-Goals

- Do not bake one “Genesis style” into the system profile.
- Do not overwrite source art silently.
- Do not mutate assets in the first dry-run implementation.
- Do not claim emulator validation unless the ROM/export was actually run.
- Do not delete or devalue other target-system profiles when Genesis is the focus.
