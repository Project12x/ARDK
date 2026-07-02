# Palette Intelligence and Cross-System Asset Roadmap

Last updated: 2026-06-24

## North Star

ARDK should become an agentic retro art-direction engine: it should ingest source art,
understand the intended look, and produce platform-specific assets that respect each
machine's constraints without flattening the user's art direction.

Genesis/SGDK is the current proving ground because its constraints are rich enough to
force serious planning: 4 palettes x 16 colors, CRAM quantization, sprite/background
palette sharing, tile budgets, and visual tricks like shadow/highlight mode. The goal is
not Genesis-only reliability. The goal is cross-system asset intelligence with Genesis as
the first hard target.

NES, Game Boy, Master System, C64, SNES, Amiga, and other existing platform notes remain
valuable. Do not delete or archive those ideas just because Genesis is the active focus.
Instead, tag docs and code paths by platform, maturity, and proof level.

## Status Legend

- **Built**: code exists and appears to implement the capability.
- **Partial**: some code exists, but it is not yet a complete end-to-end workflow.
- **In Flight**: the repo points toward this, but the canonical path is unclear or split.
- **Proposed**: useful capability that still needs design and implementation.
- **Needs Proof**: code or docs claim the feature, but it needs tests, sample assets, or a CLI smoke path.

## Existing Building Blocks

- `tools/pipeline/palette_manager.py`: game-wide palette slots, semantic purposes, locks, validation, remapping, usage tracking, prompt constraints, image export, JSON save/load, SGDK C header export.
- `tools/pipeline/palette_converter.py`: cross-platform palette conversion, RGB/Lab distance, Genesis CRAM export, SNES/NES/Game Boy export helpers.
- `tools/pipeline/quantization/perceptual.py`: Lab conversion, perceptual distance, optimal palette extraction, and quantizer scaffolding.
- `tools/pipeline/quantization/dither_numba.py`: Floyd-Steinberg, ordered/Bayer, Atkinson, no-dither, and batch dithering.
- `tools/pipeline/palettes/genesis_palettes.py`: predefined Genesis palettes, Genesis color snapping, VDP color conversion, validation, and C/ASM export.
- `tools/pipeline/cross_platform.py`: per-asset export to Genesis, NES, Game Boy, Game Boy Color, SMS, and Game Gear with platform specs and binary palette encoding.
- `tools/pipeline/genesis_export.py`: Genesis-specific tile, tilemap, sprite, CRAM, and SGDK-oriented export utilities.
- `tools/pipeline/effects.py`: palette swaps, hit/damage palettes, silhouettes, outlines, glow, and sprite effect variants.
- `tools/pipeline/platforms.py`: broad platform constraints and palette defaults across multiple retro systems.

## Current Shape of the Gap

The repo already has many palette primitives. The missing layer is a planner that reasons
across an asset family or scene before export. Today, most paths are per-asset:

1. extract or choose a palette,
2. quantize that asset,
3. export that asset to a platform format.

The desired workflow is scene/project-first:

1. analyze all source sprites, backgrounds, UI, FX, and variants,
2. infer or accept semantic color roles,
3. reserve important colors and ramps,
4. solve palette assignments under target-platform constraints,
5. produce recolored assets plus tradeoff reports,
6. export platform-native resources.

## Durable Design Principles

- Preserve source art and intent; never let a backend overwrite the art direction silently.
- Separate **system capability** from **game art direction**: Genesis, NES, GB, C64, etc. each have stable hardware art envelopes, but every game should be free to define its own mood, palette language, outline rules, rendering taste, and asset identity inside that envelope.
- Treat every target system as a constraint solver problem, not just a file-format problem.
- Prefer platform-specific solvers over one generic quantizer with flags.
- Report tradeoffs in plain language: lost hue, merged ramp, palette collision, contrast loss, tile/sprite budget pressure.
- Keep NES and other platform knowledge active; tag by maturity instead of deleting or burying it.
- Make Genesis excellent first, then generalize the planner interfaces to harsher and stranger machines.
- Keep all AI/API-dependent steps optional, cached, budgeted, and dry-run-safe.

Implementation anchor: `docs/ART_OPTIMIZATION_CONTRACT.md` defines the first code-level
split between system capability profiles and game art direction profiles.
`tools/pipeline/art_optimizer.py` adds the first dry-run evaluator for real image assets.

## External Oracles and Benchmarks

Palette intelligence should not be judged only by ARDK's own output. Keep a small set
of external tools around as comparison oracles:

- **Genesis / cross-system**: compare tile, map, and palette output against SuperFamiconv before building custom encoders for every target.
- **Genesis palette quality**: compare hard cases against Rilden-style Mega Drive palette quantization and PNGPalPrio4SGDK-style palette/priority workflows.
- **NES**: compare CHR, nametable, palette, attribute, and debug-view behavior against makechr for attribute-table-heavy scenes.
- **General quantization**: compare perceptual errors against libimagequant/pngquant, then explain where ARDK intentionally differs for hardware or art-direction reasons.
- **Regression output**: keep benchmark reports as artifacts: input image, candidate palette, indexed preview, external-tool preview, error heatmap, and human-readable tradeoff summary.

## 50-Point Plan With Reality Status

### Palette Intelligence

1. **Project palette registry** — **Partial**. `PaletteManager` can save/load palette definitions; next step is a canonical project-level manifest schema.
2. **Scene-level palette planning** — **Proposed**. Need a planner that considers all visible sprites, backgrounds, UI, and effects together.
3. **Asset-group palette planning** — **Partial**. Palette purposes exist; need group manifests such as `player`, `enemies`, `terrain`, `ui`, `fx`.
4. **Semantic color roles** — **Partial**. Palette slots have purpose metadata; individual colors need roles like skin, metal, outline, shadow, highlight.
5. **Locked colors and protected ramps** — **Partial**. Palette slots can be locked; need per-color and per-ramp locks.
6. **Palette reuse scoring** — **Proposed**. Score whether an asset should reuse an existing palette or justify a new one.
7. **Perceptual color distance** — **Built**. Lab and perceptual matching exist in quantization and palette conversion modules.
8. **HSV/value/ramp scoring** — **Proposed**. Need scoring that preserves readable ramps, not just nearest individual colors.
9. **Contrast/readability scoring** — **Partial**. Palette image text contrast exists; asset-level readability scoring does not.
10. **Palette budget reports** — **Partial**. Usage reports exist; need per-scene/per-platform budget summaries.

### Genesis Proving Ground

11. **Genesis 4 x 16 palette model** — **Built**. Platform configs and palette manager both model Genesis palette limits.
12. **Transparency/index-zero handling** — **Partial**. Several modules reserve index 0; this needs consistent validation across all exporters.
13. **CRAM quantization and preview** — **Partial**. CRAM export and Genesis snapping exist; preview/reporting should be unified.
14. **Sprite/background palette assignment** — **Proposed**. Need a solver that assigns assets to PAL0-PAL3 by scene.
15. **Palette conflict detection** — **Partial**. Sprite validation exists; cross-scene conflict detection is the missing step.
16. **Shadow/highlight simulation** — **Proposed**. Need Genesis VDP shadow/highlight mode preview, not just drop-shadow sprite effects.
17. **Shadow/highlight-safe suggestions** — **Proposed**. Planner should identify colors that survive or benefit from shadow/highlight mode.
18. **Shadow/highlight readability checks** — **Proposed**. Detect when the mode collapses contrast or damages important silhouettes.
19. **Palette strategy presets** — **Partial**. Predefined palettes exist; need optimizer presets such as vivid, moody, arcade, low-noise.
20. **SGDK-ready palette resources** — **Built**. SGDK C/header and CRAM export paths exist.

### Cross-System Backend

21. **Common asset intermediate representation** — **Proposed**. Need a durable IR for source, semantic roles, indexed variants, and exports.
22. **Versioned asset states** — **Partial**. Outputs and metadata exist in places; need one manifest linking original, analyzed, indexed, and platform-native versions.
23. **Platform constraint descriptors** — **Built / Needs Proof**. Broad descriptors exist in `platforms.py` and `cross_platform.py`; they need consolidation and tests.
24. **Platform-tagged docs** — **Proposed**. Keep NES and older docs active, but label assumptions, target systems, and proof status.
25. **Per-system palette solvers** — **Partial**. Conversion exists; solver-level behavior is still missing for most platforms.
26. **NES attribute-table-aware planning** — **Proposed**. NES conversion should understand 16x16 attribute regions and shared background palettes.
27. **Sprite-vs-background palette rules** — **Partial**. Palette purposes exist; solver constraints need to model sprite/BG separation per platform.
28. **C64 multicolor compromises** — **Partial / Needs Proof**. C64 constraints are represented, but compromise planning needs implementation.
29. **GB/1bpp/2bpp intentional remapping** — **Partial**. Game Boy palettes exist; style-preserving remap policies need to be explicit.
30. **Asset-family conversion workflow** — **Partial**. Multi-platform per-asset export exists; family/scene-aware conversion remains to build.

### Agentic Conversion

31. **Explain tradeoffs output** — **Proposed**. Every conversion should explain what changed and why.
32. **Palette sacrifice proposals** — **Proposed**. The agent should suggest mergers, ramp cuts, or palette reallocations before applying them.
33. **Art-direction preference prompts** — **Proposed**. Ask when choices are genuinely aesthetic: contrast vs fidelity, smoother ramps vs bolder silhouettes.
34. **Before/after/contact-sheet previews** — **Partial**. Palette images exist; need generated contact sheets for assets and scenes.
35. **Multi-target comparison sheets** — **Proposed**. Show Genesis/NES/GB/C64/etc. side by side from the same source set.
36. **Palette mutation search** — **Proposed**. Explore nearby hardware colors to improve shared fit while preserving mood.
37. **Automatic recolor variants** — **Partial**. Palette swap utilities exist; planner-driven enemy/faction variants remain to build.
38. **Style consistency checks** — **Proposed**. Detect drift across generated batches, animations, and converted platforms.
39. **Source-art diagnosis** — **Proposed**. Identify colors, gradients, transparency, outlines, and ramps that will stress target systems.
40. **Palette collision repair suggestions** — **Proposed**. Suggest fixes when assets fight over the same hardware palette.

### Pipeline Integration

41. **Platform-aware default palette extraction** — **In Flight**. Multiple extractors exist; the canonical `Pipeline` path should stop falling back to NES-centric behavior for Genesis.
42. **Global planning before per-asset export** — **Proposed**. Add a planning phase before quantization/export.
43. **Project and scene manifests** — **Proposed**. Define manifests that list assets, roles, scene groups, target platforms, and palette policies.
44. **Palette reports on every export** — **Partial**. Some reports exist; require consistent machine-readable and human-readable reports.
45. **Cross-platform regression tests** — **Partial**. Perceptual and dither tests exist; add Genesis/NES/C64/GB scene-level fixtures.
46. **Golden sample assets** — **Proposed**. Add tiny committed fixtures that expose palette sharing, ramps, gradients, transparency, and conflicts.
47. **Visual diff tooling** — **Proposed**. Add quantization/recolor diffs with palette and perceptual error summaries.
48. **Palette policy config** — **Partial**. `.ardk.yaml` has palette-related settings; need richer project/scene policies.
49. **CLI commands** — **Proposed**. Add `plan-palettes`, `recolor`, `compare-targets`, and `palette-report`.
50. **Flagship multi-target demo** — **Proposed**. Demonstrate one asset family exported to Genesis and NES first, then extend to GB/C64/SMS.

## Suggested Phases

### Phase 0: Make Existing Work Visible

- Add a palette feature matrix that lists built, partial, in-flight, and proposed capabilities.
- Add or update tests that prove `PaletteManager`, `PaletteConverter`, Genesis palette snapping, and perceptual quantization behave as advertised.
- Add CLI smoke paths that exercise existing code without requiring API calls.
- Label docs by platform and proof status instead of deleting older material.

### Phase 1: Shared Palette Manifest

- Define `palette_plan.json` or `palette_plan.yaml` as the stable artifact.
- Include source assets, scene groups, asset roles, target systems, locked colors, protected ramps, and desired mood/style.
- Save planner output separately from user-authored policy.
- Make every export able to reference the chosen palette plan.

### Phase 2: Genesis Scene Palette Planner

- Use Genesis as the first full solver target.
- Inputs: source sprites, backgrounds, UI, FX, optional user palette locks, optional semantic roles.
- Outputs: PAL0-PAL3 assignments, CRAM values, indexed previews, conflict warnings, SGDK resources, and a tradeoff report.
- Add shadow/highlight simulation as a planner mode, not as a generic sprite effect.

### Phase 3: Cross-System Solvers

- Add NES attribute-region planning.
- Add Game Boy/GBC remap policies.
- Add SMS/Game Gear palette policies.
- Add C64 multicolor mode compromise planning.
- Make each solver consume the same asset IR and emit platform-specific reports.

### Phase 4: Agentic Art Direction

- Add source-art diagnosis before conversion.
- Add proposed fix lists rather than silent remapping.
- Add contact sheets and comparison sheets.
- Add AI-assisted explanations and suggestions, but keep deterministic offline reports as the base layer.

### Phase 5: Regression and Demo

- Commit small golden fixtures.
- Add visual regression outputs for palette planning.
- Build a flagship demo from one source asset family to Genesis + NES first.
- Expand the demo to GB/C64/SMS once the planner interfaces stabilize.

## First Implementation Slice

The first useful slice should avoid rewriting existing systems. It should connect them:

1. Define a `PalettePlan` artifact that references existing `PaletteManager` slots.
2. Add a dry-run `plan-palettes` CLI command that reads a list of assets and target platform.
3. For Genesis, extract candidate palettes from all assets, snap them to CRAM, and score reuse pressure.
4. Emit a human report: palette slots, colors used, conflicts, likely sacrifices, and suggested assignments.
5. Emit a machine report: JSON with palette assignments and warnings.
6. Run optional external comparisons against SuperFamiconv/Rilden-style workflows when configured.
7. Add fixtures and tests for one player sprite, one enemy sprite, one background tile sample, and one UI sample.
8. Wire the existing Genesis exporter to optionally consume the generated plan.
8. Only after that, add preview/contact-sheet generation.

This keeps ARDK's broader cross-system ambition intact while making Genesis the first
place where the palette planner becomes real, testable, and useful.
