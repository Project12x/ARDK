# ARDK Ecosystem Integration Plan

Last updated: 2026-06-24

## Purpose

ARDK should not try to replace the retrodev ecosystem. It should become the agentic
coordination layer that understands the user's art direction, target hardware, source
assets, build constraints, and available tools, then chooses the best path through them.

The practical product is a retro asset and build planner:

1. ingest source art, maps, audio, prompts, and project manifests,
2. reason about target-system constraints,
3. call the right existing tools when they are better than ARDK's native code,
4. emit durable reports, previews, manifests, and platform-native resources,
5. preserve cross-system intent instead of flattening everything into one backend.

Genesis/SGDK remains the proving ground because it forces serious palette, VRAM, sprite,
audio, and emulator-debug constraints. The broader target is cross-system conversion and
agentic retro development across NES, Game Boy, SMS/GG, C64, SNES, PC Engine, Amiga, and
other systems.

## Capability vs Direction

Keep these separate everywhere:

- **System capability profile**: the stable hardware envelope for a target system: color encoding, palette count, colors per palette, transparency rules, sprite limits, tile format, plane/background rules, DMA/VRAM pressure, emulator/toolchain validation.
- **Game art direction profile**: the per-project or per-game taste layer: mood, palette language, outline rules, ramp shapes, dithering taste, sprite/background separation, faction colors, UI language, and reference art.

The system profile should rarely change. The game profile should change constantly
from project to project. ARDK's job is to optimize art direction inside the system
envelope, not to make every Genesis/NES/GB/C64 project look the same.

Implementation anchor: `docs/ART_OPTIMIZATION_CONTRACT.md` defines the first durable
schema and loader for this split.

## License Posture

This is planning guidance, not legal advice. Verify licenses before vendoring, linking,
or redistributing third-party code.

Recommended ARDK license posture:

- **Project license**: GPLv3-or-later is the best default if the goal is maximum source
  expansion and compatibility with modern GPLv3-compatible dependencies.
- **Generated output**: state explicitly that ARDK does not claim GPL status or ownership
  over generated art, maps, audio, code stubs, or exported game assets solely because ARDK
  produced them.
- **Adapters over vendoring**: prefer subprocess adapters, file-format import/export, and
  optional Python dependencies over copying upstream source.
- **GPLv2-only caution**: GPLv2-only code is not compatible with GPLv3-only code. Keep
  GPLv2-only tools external unless licensing is clarified.
- **Apache-2.0**: compatible with GPLv3, not GPLv2-only.
- **Proprietary/source-available tools**: integrate through user-installed executables and
  documented file formats only; do not vendor.
- **Private use**: GPL obligations generally matter when conveying/distributing the
  program, not when privately using or modifying it.

## Integration Modes

Use the lightest integration mode that preserves value.

| Mode | Meaning | Good For | Risk |
|---|---|---|---|
| Native dependency | Import the library directly in ARDK | Python color science, solvers, image processing | Dependency/packaging weight |
| Optional dependency | Use if installed, fallback otherwise | Numba, colour-science, OpenCV, OR-Tools | Multiple paths to test |
| Subprocess adapter | Call external executable | SGDK, Aseprite, Furnace, emulators, compressors | CLI/version drift |
| File-format bridge | Read/write stable files | Tiled, LDtk, Aseprite JSON, VGM, PNG | Format coverage gaps |
| Reference/spec source | Use docs/specs, not code | hardware manuals, wikis, community docs | drift, attribution |
| Inspiration only | Study workflow; reimplement cleanly | incompatible-license tools | accidental copying |

## Native ARDK Anchors

These should remain the internal spine that ecosystem tools plug into:

- `tools/pipeline/palette_manager.py`: game-wide palette slots, locks, validation, remapping, usage tracking, prompt constraints, and SGDK palette export.
- `tools/pipeline/palette_converter.py`: platform color-space conversion, perceptual matching, Genesis CRAM, SNES/NES/Game Boy export helpers.
- `tools/pipeline/quantization/`: perceptual color metrics, palette extraction, dithering engines.
- `tools/pipeline/palettes/genesis_palettes.py`: Genesis palette presets, color snapping, VDP encoding, validation, C/ASM export.
- `tools/pipeline/genesis_export.py`: Genesis-native tile/tilemap/sprite/palette export.
- `tools/pipeline/cross_platform.py`: multi-platform export layer.
- `tools/pipeline/maps.py`: Tiled/TMX-style map ingestion and SGDK/Genesis map export path.
- `tools/pipeline/audio.py`: WAV/PCM/audio conversion path.
- `tools/blastem_remote.py`, `tools/monitor_gamestate.py`, `tools/inspect_vram.py`: emulator automation and runtime inspection.

## Priority Integration Matrix

### Color, Palette, Quantization

| Tool / Library | License / Posture | Integration Mode | Why It Matters | ARDK Use |
|---|---|---|---|---|
| [Pillow](https://github.com/python-pillow/Pillow) | permissive-style PIL/Pillow license | Native dependency | Core image IO/manipulation | Keep as baseline image backend |
| [NumPy](https://numpy.org/) | BSD | Native dependency | Fast pixel arrays and scoring | Standard array representation |
| [SciPy](https://scipy.org/) | BSD | Optional dependency | Optimization, clustering, spatial methods | Useful fallback for solvers/metrics |
| [scikit-learn](https://scikit-learn.org/) | BSD | Optional dependency | K-means/clustering already aligned with quantization | Palette extraction and asset clustering |
| [scikit-image](https://github.com/scikit-image/scikit-image) | BSD-style | Optional dependency | Image metrics, segmentation, transforms | Source-art diagnosis and visual diffs |
| [OpenCV](https://github.com/opencv/opencv) | Apache-2.0 | Optional dependency | Fast computer vision operations | Sprite detection, masks, contact sheets |
| [colour-science](https://github.com/colour-science/colour) | BSD-3-Clause | Optional dependency | Serious color science, CIE spaces, deltas | High-quality palette scoring |
| [Colorspacious](https://github.com/njsmith/colorspacious) | MIT | Optional dependency | CAM02-UCS and color-blindness simulation | Accessibility/readability scoring |
| [libimagequant](https://github.com/ImageOptim/libimagequant) | GPLv3+ for FOSS / commercial dual license | Optional native/subprocess | Excellent palette quantization | Best-in-class flexible-palette candidate generation |
| [pngquant](https://pngquant.org/) | GPL/commercial family via libimagequant | Subprocess adapter | Practical CLI around libimagequant | Compare ARDK quantization against known-good output |
| [ImageMagick](https://imagemagick.org/) | permissive-style ImageMagick license | Subprocess adapter | Format conversion, inspection, batch transforms | Emergency fallback and diagnostics |
| [Lospec palettes](https://lospec.com/palette-list) | palette-specific licenses vary | Reference/import only | Community palette library | Import user-approved palettes with attribution |

### Constraint Solving and Planning

| Tool / Library | License / Posture | Integration Mode | Why It Matters | ARDK Use |
|---|---|---|---|---|
| [OR-Tools](https://github.com/google/or-tools) | Apache-2.0 | Optional dependency | CP-SAT and assignment optimization | Scene palette assignment, palette reuse, asset grouping |
| [Z3](https://github.com/Z3Prover/z3) | MIT | Optional dependency | SMT solving and unsat explanations | Explain impossible palette/sprite/map constraints |
| `scipy.optimize` | BSD | Optional dependency | Lightweight numerical optimization | Palette mutation search and scoring |
| [NetworkX](https://networkx.org/) | BSD | Optional dependency | Graph clustering and matching | Palette conflict graphs, asset dependency graphs |

### Pixel Art Editors and Art Sources

| Tool | License / Posture | Integration Mode | Why It Matters | ARDK Use |
|---|---|---|---|---|
| [Aseprite](https://github.com/aseprite/aseprite) | source-available EULA / commercial binaries | User-installed CLI + file bridge | Industry-standard sprite workflow, CLI, Lua, JSON export | Import `.aseprite` exports; call CLI only if user configured it |
| [LibreSprite](https://github.com/LibreSprite/LibreSprite) | GPLv2-only | External/subprocess only unless compatibility resolved | Free fork of old Aseprite | Optional editor bridge; do not vendor into GPLv3-only code |
| [Pixelorama](https://github.com/Orama-Interactive/Pixelorama) | MIT | External/subprocess/file bridge | Open pixel-art editor with CLI automation and palette tools | Candidate free editor bridge |
| [GrafX2](https://gitlab.com/GrafX2/grafX2) | AGPL-family in repo metadata; verify exact terms | External tool | Strong indexed/palette art workflow | Palette and indexed-art reference workflow |
| [Retro Graphics Toolkit](https://github.com/ComputerNerd/Retro-Graphics-Toolkit) | GPLv3-or-later | Inspiration/subprocess/file bridge | Multi-platform retro graphics conversion and tile editors | Study workflows; optional external comparison tool |
| Pro Motion NG | commercial | User-installed external | Pro-grade pixel workflow | Document export/import conventions only |
| GraphicsGale | freeware/proprietary status varies | User-installed external | Common older pixel-art workflow | File import/export only |

### Maps, Levels, and Tile Worlds

| Tool | License / Posture | Integration Mode | Why It Matters | ARDK Use |
|---|---|---|---|---|
| [Tiled](https://github.com/mapeditor/tiled) | mixed/GPL-2.0/Apache/BSD project licensing; verify components | File bridge + optional CLI | Mature TMX/JSON editor; SGDK mentions support | Canonical tilemap import/export bridge |
| [LDtk](https://github.com/deepnight/ldtk) | MIT | File bridge | Modern JSON-first level editor | Add LDtk import path and platform constraints |
| [Ogmo Editor](https://ogmo-editor-3.github.io/) | verify before bundling | File bridge | Simple JSON level workflow | Optional level import |
| 16Tile | external | User-installed external | SGDK-specific map editor | Genesis-specific import/export compatibility |
| PNGPalPrio4SGDK | external | User-installed external | Palette/priority editing for SGDK PNGs | Compare with ARDK Genesis palette-priority plan |
| Rilden Mega Drive palette quantizer | external web/reference | Reference / manual comparison | Dedicated MD palette constraint tool | Benchmark Genesis quantization quality |

### Asset Converters and Backend Reference Tools

| Tool | License / Posture | Integration Mode | Why It Matters | ARDK Use |
|---|---|---|---|---|
| [SuperFamiconv](https://github.com/Optiroc/SuperFamiconv) | MIT | Subprocess/reference adapter | Flexible tile, palette, and map converter for MD, SNES, GB/GBC/GBA, SMS/GG, PCE, WonderSwan | Highest-priority external converter benchmark; compare ARDK outputs before reimplementing niche encoders |
| [makechr](https://github.com/dustmop/makechr) | verify exact license before vendoring | Subprocess/reference adapter | Python NES image splitter for CHR, nametable, palette, attributes, and spritelist | NES proof oracle for attribute/palette constraints and debug views |
| [grit](https://github.com/devkitPro/grit) | GPL-2.0 plus mixed bundled licenses | Subprocess only | GBA/NDS-era raster/image converter with devkitPro lineage | Future GBA/NDS benchmark; avoid vendoring mixed-license code |
| [Porytiles](https://github.com/grunt-lucas/porytiles) | MIT | Reference/subprocess candidate | GBA overworld tileset compiler with palette-generation focus | Study metatile/block/palette assignment ideas for large tile worlds |
| Retro console ROM-hacking editors | license varies | User-installed/file bridge | Many artists already use CHR/tile/palette editors | Import/export their stable file formats; do not depend on abandoned binaries |

### Genesis / Mega Drive

| Tool / Source | License / Posture | Integration Mode | Why It Matters | ARDK Use |
|---|---|---|---|---|
| [SGDK](https://github.com/Stephane-D/SGDK) | MIT for SGDK library/tools; bundled compiler/runtime has GNU/GCC terms | Subprocess/toolchain adapter | Primary Genesis backend | `.res`, `rescomp`, build validation, generated headers |
| SGDK `rescomp` | SGDK bundled tool | Subprocess adapter | Authoritative SGDK asset compiler | Validate `.res` and generated assets |
| [BlastEm](https://www.retrodev.com/blastem/) | GPLv3+ | Subprocess/GDB remote | Accurate Genesis emulator with GDB remote and debug tools | Automated boot, RAM/VRAM checks, screenshots, playtests |
| Gens KMod | external/older | Optional external | KLog/KDebug-friendly workflow | Debug log validation where available |
| Exodus | external | Optional external | Accuracy-focused emulator | Heavy validation/manual debugging |
| [Genesis Plus GX](https://github.com/ekeeke/Genesis-Plus-GX) | verify target component license | External/reference | Accurate emulator core | Potential future libretro-based testing |
| [ares](https://github.com/ares-emulator/ares) | ISC in repo metadata; verify bundled deps | External/manual/subprocess | Accuracy-preservation multi-system emulator | Secondary cross-system sanity check for visual/audio behavior |
| [Plutiedev](https://plutiedev.com/) | reference site | Reference/spec | Excellent hardware explanations | Link in docs and diagnostic explanations |
| [awesome-megadrive](https://github.com/And-0/awesome-megadrive) | reference index | Reference/spec | Curated MD resources | Seed integration discovery |
| [MarsDev](https://github.com/andwn/marsdev) | verify before bundling | Toolchain alternative | Cross-platform Genesis/32X environment | Optional toolchain detection |
| [docker-sgdk](https://gitlab.com/doragasu/docker-sgdk) | verify | External/container | Reproducible SGDK builds | Future CI/backend option |

### NES / 6502 / Cross-6502

| Tool / Source | License / Posture | Integration Mode | Why It Matters | ARDK Use |
|---|---|---|---|---|
| [cc65](https://cc65.github.io/) | permissive/zlib-family; verify exact package | Toolchain adapter | Classic 6502 C/ASM toolchain | NES/C64/Atari build/export validation |
| [llvm-mos](https://github.com/llvm-mos/llvm-mos-sdk) | LLVM/Apache-family; verify components | Toolchain adapter | Modern LLVM-based 6502 C/C++ | Future higher-level 6502 backend |
| ca65 | cc65 component | Toolchain adapter | Mature assembler/linker | NES asset/code output |
| [MesenCE](https://github.com/nesdev-org/MesenCE) | GPLv3 | Emulator adapter | Modern multi-system emulator/debugger | NES/SNES/GB/SMS/PCE automated checks |
| [Nesdev Wiki](https://www.nesdev.org/wiki/Nesdev_Wiki) | reference | Reference/spec | NES hardware truth source | Attribute-table palette planner |
| [FamiStudio](https://github.com/BleuBleu/FamiStudio) | MIT | File bridge/subprocess | NES music authoring and export | Future NES audio import/export |

### Game Boy / Game Boy Color / SMS / Game Gear

| Tool / Source | License / Posture | Integration Mode | Why It Matters | ARDK Use |
|---|---|---|---|---|
| [RGBDS](https://rgbds.gbdev.io/) | verify exact license | Toolchain adapter | Standard GB assembler/linker | GB/GBC asset/code workflows |
| [GBDK-2020](https://github.com/gbdk-2020/gbdk-2020) | verify exact subcomponent licenses | Toolchain adapter | C toolkit for GB/GBC, SMS/GG, NES, and related ports | Cross-handheld backend option and platform capability reference |
| [SameBoy](https://github.com/LIJI32/SameBoy) | Expat/MIT-style with stated exception | Emulator adapter/reference | Accurate GB/GBC emulator with palette/timing focus | GB palette/timing validation |
| [Emulicious](https://emulicious.net/) | freeware/proprietary; do not vendor | User-installed external | Strong debugger for GB/SMS/GG/MSX | Optional manual/remote debugging workflow |
| [Pan Docs](https://gbdev.io/pandocs/) | reference | Reference/spec | Canonical GB/GBC hardware docs | GB/GBC palette and tile constraints |
| [SMS Power](https://www.smspower.org/) | reference/community | Reference/spec | SMS/GG hardware and dev knowledge | SMS/GG constraints and validation notes |

### SNES / GBA / Other 16-bit+ Backends

| Tool / Source | License / Posture | Integration Mode | Why It Matters | ARDK Use |
|---|---|---|---|---|
| [devkitPro](https://devkitpro.org/wiki/Getting_Started) | mixed toolchain terms; verify | User-installed toolchain | GBA/NDS and broader homebrew ecosystem | Future GBA/NDS build adapters |
| [PVSnesLib](https://github.com/alekmaul/pvsneslib) | verify exact license | Toolchain/backend adapter | SNES C development | Future SNES resource backend |
| [WLA-DX](https://github.com/vhelin/wla-dx) | GPL-family; verify | Assembler adapter | Multi-CPU assembler | Optional SMS/SNES/GB/PCE assembly output |
| [mGBA](https://mgba.io/) | MPL/GPL-family; verify | Emulator adapter | GBA/GB emulator with tooling | Future GBA/GB checks |

### Audio and Music

| Tool / Library | License / Posture | Integration Mode | Why It Matters | ARDK Use |
|---|---|---|---|---|
| [Furnace](https://github.com/tildearrow/furnace) | GPLv2-or-later/GPLv3 | File bridge/subprocess | Huge multi-system tracker; YM2612, SN76489, NES, SID, GB, etc. | Main cross-system music authoring bridge |
| DefleMask | proprietary/commercial/freeware terms vary | File bridge only | Common tracker workflow; Furnace compatibility exists | Import/export where user provides files |
| [vgmtools](https://github.com/vgmrips/vgmtools) | GPL-2.0 | Subprocess/reference | VGM conversion, compression, trimming, command counting, and diagnostics | VGM optimization and validation reports before SGDK XGM conversion |
| SGDK XGM/XGM2 tools | SGDK bundled | Subprocess | Genesis music/SFX runtime path | Validate SGDK-compatible audio output |
| [hUGETracker](https://github.com/SuperDisk/hUGETracker) | verify exact license | File bridge/subprocess | Game Boy tracker workflow around hUGEDriver ecosystem | Future GB audio import/export path |
| [Audacity](https://www.audacityteam.org/) | GPL | User-installed external | WAV editing and batch processing | Document optional round-trip workflow |
| [pydub](https://github.com/jiaaro/pydub) | MIT | Optional dependency | Audio conversion wrapper | Already aligns with `audio.py` optional path |

### Compression and Asset Packing

| Tool | License / Posture | Integration Mode | Why It Matters | ARDK Use |
|---|---|---|---|---|
| [ZX0](https://github.com/einar-saukas/ZX0) | BSD-3 for compressor; permissive decompressor use with attribution requirement | Subprocess/optional native | Excellent 8-bit compression tradeoff | NES/SMS/GB/C64 packed assets |
| [LZSA](https://github.com/emmanuel-marty/lzsa) | zlib/CC0 mix | Subprocess/native candidate | Fast decompression on 8-bit CPUs, 6502/Z80/68000 paths | Cross-system packed assets |
| Exomizer | verify exact license | Subprocess | Popular C64/8-bit compressor | C64 and 6502 asset packing |
| PuCrunch | verify exact license | Subprocess | Classic C64/8-bit compression | Optional comparison |
| SGDK compression formats | SGDK bundled | Native/subprocess via rescomp | Kosinski/other Genesis-native formats | Prefer SGDK-native for Genesis unless reason not to |

### Build, Runtime, CI, and Packaging

| Tool | License / Posture | Integration Mode | Why It Matters | ARDK Use |
|---|---|---|---|---|
| Python 3.10+ | PSF | Runtime | ARDK baseline | Fix local runtime and document setup |
| `uv` / `pip-tools` / `venv` | verify chosen tool | Setup adapter | Reproducible Python envs | Developer onboarding |
| CMake | BSD-style | Build adapter | Cross-platform build orchestration | Toolchain detection/build metadata |
| Ninja | Apache-2.0 | Build adapter | Fast builds | Optional backend for CMake/toolchains |
| Docker / Podman | mixed | External/container | Reproducible toolchains | Optional CI/devcontainer path |
| GitHub Actions | service | CI | Community confidence | Unit tests, smoke exports, license checks |
| `reuse` / SPDX tools | GPL/Apache ecosystem; verify | Dev tooling | License hygiene | Generate dependency/license inventory |
| `pip-licenses` | BSD | Dev tooling | Python dependency license scan | CI license report |

### AI and Agentic Art Sources

| Tool / Service | License / Posture | Integration Mode | Why It Matters | ARDK Use |
|---|---|---|---|---|
| PixelLab | service/API terms | Provider adapter | Pixel-art generation | Existing paid provider path with budget controls |
| Pollinations | service/API terms | Provider adapter | Low-friction image generation | Existing cheap/free-ish provider path |
| ComfyUI | GPL-family; verify nodes/models separately | Local service adapter | Local image workflows | Optional local generation and upscaling |
| AUTOMATIC1111 Stable Diffusion WebUI | AGPL/GPL-family; verify | Local service adapter | Existing user workflows | Optional external image generation |
| `rembg` | MIT | Optional dependency/subprocess | Background removal | Sprite extraction preprocessing |
| Real-ESRGAN / upscalers | licenses vary by code/model | Optional external | Pre-downsample cleanup | User-configured only; model license checks |
| Local vision-language models | model licenses vary | Provider adapter | Source-art diagnosis | Optional; never assume model output rights |

### Hardware References and Communities

These should feed docs, diagnostics, and links, not vendored content:

- [Plutiedev](https://plutiedev.com/) for Mega Drive hardware explanations.
- [SpritesMind](https://gendev.spritesmind.net/forum/) for Mega Drive development discussion.
- [SegaRetro](https://segaretro.org/) for manuals and historical references.
- [Rasterscroll Mega Drive Graphics Guide](https://rasterscroll.com/mdgraphics/) for visual constraints.
- [Nesdev Wiki](https://www.nesdev.org/wiki/Nesdev_Wiki) for NES hardware.
- [GBDev Pan Docs](https://gbdev.io/pandocs/) for Game Boy hardware.
- [SMS Power](https://www.smspower.org/) for Master System/Game Gear.
- [C64 Wiki](https://www.c64-wiki.com/) and [Codebase64](https://codebase64.org/) for C64 techniques.
- [Amiga Hardware Reference Manual mirrors](https://amigadev.elowar.com/) for Amiga hardware research.

## Research Round 2 Findings

This pass found several integration targets that are more useful as adapters,
benchmarks, and proof oracles than as things to rewrite.

### Strongest New Candidates

- **SuperFamiconv first**: it already speaks the exact kind of cross-system tile/palette/map language ARDK wants. Treat it as the first external converter benchmark for MD/SNES/GB/GBC/GBA/SMS/GG/PCE/WonderSwan output.
- **Aseprite as a workflow bridge**: its CLI can batch export sheets, JSON metadata, layers, tags, slices, grids, palettes, and indexed conversions. ARDK should consume those exports and optionally drive the CLI when configured.
- **Tiled and LDtk as scene manifests**: their JSON formats carry layers, tilesets, custom properties, parallax, and object data. ARDK should attach palette budgets and hardware constraints to these maps instead of flattening them too early.
- **makechr as NES proof oracle**: its debug views for palette, colorization, tile reuse, nametable, and CHR pages are exactly the kind of explainable output ARDK should generate across systems.
- **Porytiles as a tile-world study target**: even if Pokemon-specific, its palette-generation and tileset-compilation framing is valuable for large overworld/background asset planning.

### Validation Implications

- **Genesis**: keep BlastEm as the automation spine because it exposes debugger and GDB-remote workflows; use SGDK `rescomp` as the authoritative resource compiler.
- **Cross-system**: MesenCE is a useful GPLv3-compatible external validator for NES/SNES/GB/GBA/PCE/SMS/GG/WS, while ares is a strong manual/secondary accuracy check.
- **GB/GBC**: SameBoy is the accuracy reference for palette/timing questions; Emulicious remains valuable as a user-installed debugger, especially for SMS/GG/MSX overlap.
- **Audio**: Furnace plus VGM export plus SGDK XGM/XGM2 tools is the Genesis music spine. `vgmtools` can add trimming, command counting, compression, and diagnostics before conversion.
- **Compression**: prefer platform-native formats where the runtime already supports them; benchmark ZX0/LZSA/Exomizer-style options by ratio, decode cycles, RAM scratch, and decompressor licensing.

### Licensing Notes

- GPLv3-or-later is friendly to GPLv3 tools such as MesenCE and Retro Graphics Toolkit, but external subprocess/file bridges still keep optional dependencies optional.
- GPLv2-only or non-commercially licensed tools should remain external unless the project deliberately chooses a compatible licensing path.
- Mixed-license tools like `grit` are useful benchmarks, but should not be vendored without a component-level audit.
- Source-available/proprietary tools such as Aseprite and Emulicious should be user-installed integrations only.

## Adapter Architecture

Create a first-class integration layer instead of one-off calls sprinkled across tools.

Proposed package:

```text
tools/pipeline/integrations/
  __init__.py
  registry.py
  capability.py
  licenses.py
  diagnostics.py
  adapters/
    sgdk.py
    blastem.py
    aseprite.py
    pixelorama.py
    superfamiconv.py
    makechr.py
    tiled.py
    ldtk.py
    furnace.py
    vgmtools.py
    zx0.py
    lzsa.py
    mesen.py
    sameboy.py
    ortools.py
    z3.py
```

Every adapter should expose:

- `name`
- `kind`: `library`, `subprocess`, `file_format`, `service`, `reference`
- `license_id`
- `license_risk`: `low`, `medium`, `high`, `unknown`
- `is_available()`
- `version()`
- `capabilities()`
- `doctor()`
- `dry_run_plan()`
- `run()` or format-specific methods

## Capability Vocabulary

Use capability names instead of hard-coded tool names in pipeline code:

- `image.read`
- `image.write`
- `image.quantize`
- `image.dither`
- `image.palette.extract`
- `image.palette.score`
- `image.palette.convert`
- `sprite.detect`
- `sprite.sheet.export`
- `asset.convert.tiles`
- `asset.compare.external`
- `tile.deduplicate`
- `tile.pack`
- `map.read`
- `map.export`
- `audio.read`
- `audio.export.vgm`
- `audio.export.xgm`
- `audio.optimize.vgm`
- `compress.pack`
- `compress.benchmark`
- `toolchain.build`
- `emulator.boot`
- `emulator.debug.gdb`
- `emulator.inspect.vram`
- `solver.assign`
- `solver.explain_unsat`
- `ai.generate.image`
- `ai.analyze.image`

## First Implementation Slices

### Slice 1: Ecosystem Registry and Doctor

Goal: make ARDK aware of installed tools without depending on them.

- Add integration registry scaffolding.
- Add `ardk doctor` or `python -m tools.pipeline.cli --doctor`.
- Detect Python, Pillow, NumPy, SGDK/GDK, Java for SGDK tools, BlastEm, Aseprite, Tiled, LDtk, Furnace, SuperFamiconv, OR-Tools, Z3.
- Emit JSON and human-readable reports.
- Include license posture in the report.

### Slice 2: Palette Solver Backend

Goal: connect existing palette code with solver libraries.

- Keep current native greedy/fallback planner.
- Add optional OR-Tools CP-SAT planner for scene palette assignment.
- Add optional Z3 diagnostic path for impossible constraints.
- Output `palette_plan.json` with assignments, conflicts, and explanations.
- Feed the plan into Genesis export first.

### Slice 3: External Quantization Benchmarks

Goal: stop guessing whether ARDK's quantization is good.

- Add optional `pngquant` / `libimagequant` comparison.
- Add optional SuperFamiconv/Rilden comparison for Genesis-specific palette-map results.
- Add `colour-science` and `colorspacious` scoring backends.
- Generate before/after/contact sheets.
- Emit perceptual error and readability reports.

### Slice 4: Editor Bridges

Goal: make ARDK fit real artist workflows.

- Add Aseprite JSON import and optional CLI export.
- Add Pixelorama project/export bridge if practical.
- Add Tiled and LDtk scene manifests.
- Add SuperFamiconv and makechr subprocess benchmark adapters.
- Keep all proprietary/source-available tools external and user-configured.

### Slice 5: Emulator Validation

Goal: prove exports in real hardware-like environments.

- Genesis: SGDK build + BlastEm boot + VRAM/CRAM inspection.
- NES/GB/SMS: MesenCE/SameBoy/Emulicious adapters where available; ares as secondary manual/subprocess check.
- Capture screenshots and machine-readable runtime reports.
- Never claim validation if emulator did not actually run.

## Documentation Work Items

- Add `docs/DEPENDENCY_POLICY.md` with license rules, vendoring rules, and generated-output policy.
- Add `docs/INTEGRATION_MATRIX.md` generated from adapter metadata.
- Add `docs/PLATFORM_PROOF_MATRIX.md` showing which systems are proven, partial, or design-only.
- Add `docs/TOOLCHAIN_SETUP.md` for Windows-first setup, then Linux/macOS.
- Add `docs/GENERATED_OUTPUT_POLICY.md` so users know their generated assets remain theirs.

## Non-Goals

- Do not rewrite SGDK, Tiled, Aseprite, Furnace, Mesen, or existing mature tools.
- Do not vendor proprietary or unclear-license code.
- Do not collapse all target systems into Genesis assumptions.
- Do not delete NES-era knowledge; tag it by platform and proof status.
- Do not silently spend API money or silently mutate source art.

## Near-Term Priority Order

1. Fix local Python/toolchain environment so tests and docs can be validated.
2. Add the integration registry and doctor command.
3. Add license/dependency inventory reporting.
4. Add `PalettePlan` and Genesis scene palette planning.
5. Add OR-Tools and Z3 as optional solver backends.
6. Add libimagequant/pngquant comparison path.
7. Add SuperFamiconv and makechr benchmark adapters.
8. Add Aseprite/Tiled/LDtk/Furnace bridges.
9. Add emulator validation reports.
10. Expand the same patterns to NES, GB, SMS/GG, and C64.
11. Publish a flagship multi-target demo that shows ARDK coordinating multiple tools.

## Guiding Sentence

ARDK should be the retrodev conductor: it does not need to play every instrument, but it
should know what each instrument can do, when to call it, how to verify the result, and
how to explain the tradeoffs to the human making the game.
