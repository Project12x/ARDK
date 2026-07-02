# Art Optimization Handoff

Last updated: 2026-07-01

## Branch

- Branch: `codex/art-optimization-contract`
- Base branch at time of work: `master`
- First pushed commit: `d95d357 Add art optimization contracts`
- PR URL helper: <https://github.com/Project12x/ARDK/pull/new/codex/art-optimization-contract>

## Purpose

This branch starts the ARDK art-optimization layer: a dry-run system that separates
stable hardware capability from per-game art direction, then evaluates real assets
against both.

The important design split:

- **System capability profile**: what the target system can physically do.
- **Game art direction profile**: what a specific game wants to look like inside that
  hardware envelope.

Genesis is the first proving ground, but the design is meant to generalize.

## New Files

- `tools/pipeline/art_profiles.py`: dataclass loader for system capability profiles,
  game art direction profiles, and merged optimization contracts.
- `tools/pipeline/art_optimizer.py`: dry-run image analyzer, scene analyzer, and
  first-pass palette slot planner.
- `profiles/systems/genesis.json`: Genesis/Mega Drive capability profile.
- `profiles/games/example_genesis_style.json`: example game-specific art direction.
- `profiles/scenes/example_genesis_scene.json`: example visible-together scene manifest.
- `docs/ART_OPTIMIZATION_CONTRACT.md`: durable contract documentation.
- `docs/PALETTE_INTELLIGENCE_ROADMAP.md`: palette roadmap and external benchmark plan.
- `docs/ECOSYSTEM_INTEGRATION_PLAN.md`: ecosystem/tool/library integration plan.

## Existing File Updated

- `tools/pipeline/__init__.py`: exports the art profile contract types.

`tools.pipeline.art_optimizer` is intentionally not eagerly re-exported from
`tools.pipeline.__init__` so `python -m tools.pipeline.art_optimizer` can run without
module preloading warnings.

## How To Run

Compile the new modules:

```powershell
python -m py_compile tools\pipeline\art_profiles.py tools\pipeline\art_optimizer.py
```

Analyze loose assets:

```powershell
python -m tools.pipeline.art_optimizer `
  --system-profile profiles/systems/genesis.json `
  --art-direction profiles/games/example_genesis_style.json `
  tools/epoch_hero_sprite.png
```

Analyze a scene manifest:

```powershell
python -m tools.pipeline.art_optimizer `
  --system-profile profiles/systems/genesis.json `
  --art-direction profiles/games/example_genesis_style.json `
  --scene-manifest profiles/scenes/example_genesis_scene.json
```

Emit JSON:

```powershell
python -m tools.pipeline.art_optimizer `
  --system-profile profiles/systems/genesis.json `
  --art-direction profiles/games/example_genesis_style.json `
  --scene-manifest profiles/scenes/example_genesis_scene.json `
  --json
```

## Current Behavior

The optimizer is dry-run only. It does not mutate, quantize, export, or overwrite art.

It currently reports:

- source color count,
- Genesis-snapped color count,
- estimated palettes needed,
- average and maximum CRAM snap error,
- conventional transparency/index-zero hints,
- 8x8 tile count,
- unique tile count with flip reuse,
- rough VRAM bytes,
- metasprite pressure,
- scene-level sprite scanline pressure,
- PAL0-PAL3 first-pass assignments,
- over-budget palette slot warnings.

Example result from the sample scene:

- `PAL0`: empty / reserved for world background.
- `PAL1`: hero assigned, over budget.
- `PAL2`: enemy assigned, over budget.
- `PAL3`: FX assigned, over budget.

This is expected: the sample files are useful because they create obvious pressure.

## Important Constraints

- JSON examples are used because PyYAML was not installed locally.
- YAML profiles/manifests are supported only when PyYAML is installed.
- Scene manifest paths are resolved relative to the manifest file.
- The palette planner is not yet an optimizer; it is a deterministic explainer.
- The palette planner counts unique Genesis-snapped RGB colors, not semantic ramps.
- Shadow/highlight mode is represented as a scoring concern, not yet simulated.
- `AGENTS.md` remains untracked and was intentionally excluded from commits.
- Git emits a warning about `C:\Users\estee/.config/git/ignore` permission denial; it
  did not block commits or pushes.

## Validation Used

```powershell
python -m py_compile tools\pipeline\art_profiles.py tools\pipeline\art_optimizer.py
python -m tools.pipeline.art_optimizer --system-profile profiles\systems\genesis.json --art-direction profiles\games\example_genesis_style.json --scene-manifest profiles\scenes\example_genesis_scene.json
python -c "from tools.pipeline.art_optimizer import load_and_analyze_scene; r=load_and_analyze_scene('profiles/systems/genesis.json','profiles/games/example_genesis_style.json','profiles/scenes/example_genesis_scene.json'); print(r.scene_summary['scene_id'], len(r.assets), r.verdict['palette_fit'])"
```

## Next Slice

Add palette reduction proposals.

For each over-budget palette slot, the next report should propose:

- which colors are safest to merge,
- which colors are likely protected by art direction,
- which ramps should be preserved,
- which assets should move to another slot,
- whether the asset should split into multiple palette-backed variants,
- what tradeoff the user is accepting.

Suggested next implementation shape:

- add `PaletteReductionProposal` dataclass,
- group snapped colors into crude ramps by hue/value,
- mark protected colors/ramps from the game profile,
- propose merges by nearest Genesis-valid color,
- output proposals without mutating source art.

That turns “PAL1 is 21 colors over budget” into “merge these neutrals, preserve this
skin ramp, and keep the hero accent.”
