# ARDK Asset Pipeline Plan

> **Version**: 3.9
> **Created**: 2026-01-16
> **Updated**: 2026-01-17
> **Status**: Phases 1-4 Mostly Complete

---

## Executive Summary

Expand the unified pipeline from a sprite extraction tool into a full-featured **asset production system** covering graphics, audio, and tilemaps, with first-class SGDK/Genesis support and eventual React-based GUI.

**Principles:**
- Open-source compatible (no paid-only dependencies in core)
- CLI-first (GUI wraps CLI, never replaces it)
- Platform-agnostic export (Genesis, NES, SNES, GBA, modern engines)
- Default to PixelLab for generation (exact dimensions, 4bpp support)
- Validate early, fail fast (catch format issues before build)
- Graceful degradation (local fallbacks when APIs unavailable)

---

## Development Standards (Apply Throughout)

These practices apply to ALL phases - not deferred to the end.

### Code Quality

**Every new file/function must have:**
- Module-level docstring with purpose, dependencies, example usage
- Class/function docstrings with Args, Returns, Raises, Example
- Complete type hints for all public functions
- Named constants (no magic numbers)

**Naming:** `snake_case` modules/functions, `PascalCase` classes, `UPPER_SNAKE` constants

**Comments:** Explain *why*, not *what*. Use `# TODO(#issue):` and `# DEBT:` markers.

### Testing (Per-Feature)

**When adding a feature, also add:**
- Unit tests in `tools/tests/test_<module>.py`
- Integration test if it touches multiple modules
- Golden master image if it produces visual output

**Coverage targets:** 90% core, 85% export, 70% AI (mocked)

```bash
pytest tools/tests/ --cov=tools/pipeline --cov-report=html
```

### Documentation (Continuous)

**Living Documents (update with each feature):**

- **USAGE.md** - User-facing "how to use" guide
  - Add module section when implementing new module
  - Include basic and advanced usage examples
  - Document common errors and solutions
  - Update Table of Contents when adding sections

- **CLI Reference** (in USAGE.md) - Command-line flags
  - Add new flags as they're implemented
  - Include examples for each flag

- **CHANGELOG.md** - User-visible changes
  - Add entry for each release
  - Group by: Added, Changed, Fixed, Removed

- **ADRs** (Architecture Decision Records) - Significant choices
  - Create `docs/adr/NNNN-title.md` for major decisions
  - Document context, decision, and consequences

**Per-Module Documentation:**

When implementing a module, add to USAGE.md:

```markdown
### Module Name

**File:** `module.py`
**Phase:** X.Y (Status)

Brief description of what this module does.

#### Key Classes

\`\`\`python
# Basic usage example
from tools.pipeline import ModuleClass

instance = ModuleClass()
result = instance.do_something("input.png")
\`\`\`

#### Advanced Usage

[More complex examples if applicable]

#### Common Issues

[Known gotchas and solutions]
```

### Refactoring Triggers

| Trigger | Action |
|---------|--------|
| Function > 50 lines | Extract helpers |
| Module > 500 lines | Split into submodules |
| 3+ similar code blocks | Extract to utility |
| After completing a phase | Review changed modules |

### GUI-Readiness (Build-In From Start)

All new code should support future GUI integration:
- Return `Result[T]` objects, not print statements
- Use `EventEmitter` from `core/events.py` for progress callbacks
- Accept `cancel_token: Event` for cancellation
- Keep I/O separate from core logic
- Ensure all outputs are JSON-serializable
- Use `core/pipeline.py` as entry point (not CLI directly)

**Event System Usage:**
```python
from tools.pipeline.core import EventEmitter, EventType

emitter = EventEmitter()
emitter.on(EventType.PROGRESS, lambda e: update_ui(e.percent))
pipeline = Pipeline(config, event_emitter=emitter)
```

### Phase Completion Checklist (Use Per-Phase)

Each phase must complete these gates before moving on:

```markdown
#### Quality Gates
- [ ] **Tests**: Unit tests written for all new public functions
- [ ] **Docs**: Docstrings complete (module, class, public functions)
- [ ] **USAGE.md**: Module section added with examples
- [ ] **Types**: Type hints on all public interfaces
- [ ] **CLI**: New flags documented in CLI Reference section
- [ ] **Integration**: Works with existing pipeline (no regressions)
- [ ] **Review**: Code reviewed for DEBT markers and TODO items
```

---

## Phase Overview

| Phase | Name | Status | Dependencies |
|-------|------|--------|--------------|
| **0** | Foundation | ✅ Complete | None |
| **1** | Core Features | ✅ Complete | Phase 0 |
| **2** | SGDK Integration | ✅ Mostly Complete | Phase 1 |
| **3** | AI-Powered Features | ✅ Complete | Phase 1-2 |
| **4** | Advanced Tools | ✅ Mostly Complete | Phase 1-3 |
| **5** | Hardening & Quality | ✅ Complete | All Features |
| **6.1** | Optimization & Performance | 📋 Planned | Phase 2, 5 |
| **6.2** | Asset Management & Workflow | 📋 Planned | Phase 5, 6.1 |
| **6.3** | AI & Quality Enhancement | 📋 Planned | Phase 3, 5 |
| **6.4** | Palette & Color Management | 📋 Planned | Phase 1, 3 |
| **6.5** | Animation Enhancement | 📋 Planned | Phase 1, 3 |
| **6.6** | Toolchain Integration | 📋 Planned | Phase 2 |
| **6.7** | Infrastructure & Extensibility | 📋 Planned | All Phases |
| **7** | GUI (Workshop.OS) | 📋 Future | Phase 1-6.7 |

---

## Implementation Status

### Existing Files

| File | Status | Phase |
|------|--------|-------|
| `sgdk_format.py` | ✅ Complete | 0.1 |
| `genesis_export.py` | ✅ Complete | 0.6 |
| `ai.py` | ✅ Complete | 0.4 |
| `processing.py` | ✅ Complete | 0.3 |
| `style.py` | ✅ Complete | 0.4 |
| `platforms.py` | ✅ Complete | 0.3 |
| `fallback.py` | ✅ Complete | 0.4 |
| `palettes/genesis_palettes.py` | ✅ Complete | 0.2 |
| `animation.py` | ✅ Complete | 1.1 |
| `sheet_assembler.py` | ✅ Complete | 1.2 |
| `effects.py` | ✅ Complete | 1.3 |
| `palette_converter.py` | ✅ Complete | 1.6 |
| `palette_manager.py` | ✅ Complete | 1.6 |
| `sgdk_resources.py` | ✅ Complete | 2.1 |
| `performance.py` | ✅ Complete | 2.3 |
| `animation_fsm.py` | ✅ Complete | 4.1 |
| `collision_editor.py` | ✅ Complete | 4.2 |
| `cross_platform.py` | ✅ Complete | 4.3 |
| `audio.py` | ✅ Complete | (WAV/PCM) |
| `maps.py` | ✅ Complete | (Tilemaps) |
| `quantization/perceptual.py` | ✅ Complete | 0.7 |
| `quantization/dither_numba.py` | ✅ Complete | 0.8 |
| `integrations/aseprite.py` | ✅ Complete | 1.8 |
| `core/__init__.py` | ✅ Complete | 0.9 |
| `core/config.py` | ✅ Complete | 0.9 |
| `core/pipeline.py` | ✅ Complete | 0.9 |
| `core/safeguards.py` | ✅ Complete | 0.9 |
| `core/events.py` | ✅ Complete | 0.9 |
| `cli.py` | ✅ Complete | 0.9 |
| `rotation.py` | ✅ Complete | 1.4 |

### Files to Create

| File | Phase | Priority |
|------|-------|----------|
| ~~`animation.py`~~ | 1.1 | ✅ Done |
| ~~`sheet_assembler.py`~~ | 1.2 | ✅ Done |
| ~~`effects.py`~~ | 1.3 | ✅ Done |
| ~~`rotation.py`~~ | 1.4 | ✅ Done |
| ~~`palette_converter.py`~~ | 1.6 | ✅ Done |
| ~~`sgdk_resources.py`~~ | 2.1 | ✅ Done |
| ~~`performance.py`~~ | 2.3 | ✅ Done |
| ~~`animation_fsm.py`~~ | 4.1 | ✅ Done |
| ~~`collision_editor.py`~~ | 4.2 | ✅ Done |
| ~~`cross_platform.py`~~ | 4.3 | ✅ Done |
| `scene_composer.py` | 4.4 | MEDIUM |
| ~~`errors.py`~~ | 5.1 | ✅ Done |
| ~~`validation.py`~~ | 5.2 | ✅ Done |
| ~~`resources.py`~~ | 5.3 | ✅ Done |
| ~~`security.py`~~ | 5.5 | ✅ Done |
| ~~`metrics.py`~~ | 5.6 | ✅ Done |
| `tests/conftest.py` | Ongoing | HIGH |
| `tests/test_*.py` | Ongoing | HIGH |
| ~~`core/`~~ | 0.9 | ✅ Done |
| `io/` (refactor) | Ongoing | MEDIUM |
| ~~`quantization/perceptual.py`~~ | 0.7 | ✅ Done |
| ~~`quantization/dither_numba.py`~~ | 0.8 | ✅ Done |
| ~~`integrations/aseprite.py`~~ | 1.8 | ✅ Done |
| `tilemap/tiled_import.py` | 2.6 | HIGH |
| `audio/vgm_tools.py` | 2.7 | HIGH |
| ~~`compression/genesis_compress.py`~~ | 2.8 | ✅ Done |
| `ai_providers/pixie_haus.py` | 3.6 | MEDIUM |
| `ai_providers/stable_diffusion.py` | 3.6 | MEDIUM |

---

## Phase 0: Foundation (COMPLETE)

**Goal:** Core infrastructure for SGDK-compliant sprite processing.

### 0.1 SGDK Sprite Formatter ✅

**File:** `tools/pipeline/sgdk_format.py`

Converts any sprite image to SGDK-compliant format:
- Resize to target dimensions (max 32×32)
- Convert alpha channel to magenta transparency
- Quantize to 16 colors with palette control
- Arrange into sprite sheets (≥128px width)
- Validate before rescomp

**Key Classes:**
- `SGDKFormatter` - Main conversion class
- `ValidationResult` - Pre-flight validation results

**CLI:** `--format-sgdk`

### 0.2 Genesis Palette Definitions ✅

**File:** `tools/pipeline/palettes/genesis_palettes.py`

Platform-specific color palettes:
- `GENESIS_PALETTES` - Curated 16-color palettes
- `get_genesis_palette(name)` - Retrieve by name

### 0.3 Platform Configurations ✅

**File:** `tools/pipeline/platforms.py`

Platform specs for Genesis, NES, SNES, GBA:
- Sprite size limits
- Color depth
- Tile alignment requirements
- VRAM budgets

### 0.4 AI Provider Integration ✅

**File:** `tools/pipeline/ai.py`

Multi-provider AI integration:
- PixelLab (primary - exact dimensions)
- Pollinations (free fallback)
- Gemini, Groq, OpenAI (vision analysis)

**File:** `tools/pipeline/style.py`

Style transfer system:
- `StyleAdapter` - Provider-specific adapters
- `StyleProfile` - Portable style definitions
- `StyleManager` - Capture/apply styles

### 0.5 Collision Detection ✅

**File:** `tools/pipeline/genesis_export.py` (partial)

AI-powered collision box detection:
- Hitbox/hurtbox inference
- Debug overlay generation

### 0.6 Genesis 4bpp Tile Export ✅

**File:** `tools/pipeline/genesis_export.py`

Genesis tile data export:
- `export_genesis_tiles()` - 4bpp tile binary
- `export_genesis_tilemap()` - Deduplicated tilemap + indices
- C header generation with SGDK defines

---

### 0.7 Perceptual Color Science ✅

**File:** `tools/pipeline/quantization/perceptual.py` ✅ IMPLEMENTED

**Purpose:** Foundational color handling - upgrade palette matching from RGB Euclidean to perceptually accurate color difference algorithms.

**Dependencies:**

```bash
pip install colour-science colorspacious
```

**Libraries:**

- [colour-science](https://colour.readthedocs.io/) - CIELAB, XYZ, comprehensive color space conversions
- [colorspacious](https://colorspacious.readthedocs.io/) - CAM02-UCS, fast delta-E calculation

**Features:**

- CIEDE2000 color difference (industry standard for perceptual matching)
- CAM02-UCS uniform color space for palette optimization
- Glasbey algorithm for maximally distinct palette generation
- K-means clustering for optimal palette extraction from images

```python
from colour import delta_E
from colorspacious import cspace_convert, deltaE

def find_nearest_perceptual(rgb: Tuple[int, int, int],
                            palette: List[Tuple[int, int, int]],
                            method: str = "CIEDE2000") -> int:
    """
    Find nearest palette color using perceptual color difference.

    Args:
        rgb: Source color (0-255 per channel)
        palette: Target palette colors
        method: "CIEDE2000" | "CAM02-UCS" | "CIELab"

    Returns:
        Index of perceptually nearest color in palette
    """
    # Normalize to 0-1 range
    rgb_norm = [c / 255.0 for c in rgb]

    min_dist = float('inf')
    best_idx = 0

    for idx, pal_color in enumerate(palette):
        pal_norm = [c / 255.0 for c in pal_color]

        if method == "CIEDE2000":
            dist = delta_E(rgb_norm, pal_norm, method='CIE 2000')
        elif method == "CAM02-UCS":
            dist = deltaE(rgb_norm, pal_norm, input_space="sRGB1")
        else:  # CIELab
            dist = delta_E(rgb_norm, pal_norm, method='CIE 1976')

        if dist < min_dist:
            min_dist = dist
            best_idx = idx

    return best_idx

def extract_optimal_palette(image: Image.Image,
                            num_colors: int = 16,
                            method: str = "kmeans") -> List[Tuple[int, int, int]]:
    """
    Extract optimal palette from image using clustering.

    Args:
        image: Source image
        num_colors: Target palette size (default 16 for Genesis)
        method: "kmeans" | "median_cut" | "octree"

    Returns:
        List of RGB tuples representing optimal palette
    """
    pass  # Implementation uses sklearn KMeans or custom median cut
```

---

### 0.8 Numba-Accelerated Dithering ✅

**File:** `tools/pipeline/quantization/dither_numba.py` ✅ IMPLEMENTED

**Purpose:** JIT-compiled Floyd-Steinberg dithering for 10-50x speedup on large batches.

**Dependencies:**

```bash
pip install numba
```

```python
import numba
import numpy as np

@numba.jit(nopython=True)
def floyd_steinberg_numba(pixels: np.ndarray,
                          palette: np.ndarray) -> np.ndarray:
    """
    Floyd-Steinberg dithering with Numba JIT compilation.

    10-50x faster than pure PIL for batch processing.
    """
    height, width = pixels.shape[:2]
    output = np.zeros((height, width), dtype=np.uint8)
    error = pixels.astype(np.float32)

    for y in range(height):
        for x in range(width):
            old_pixel = error[y, x]
            new_idx = find_nearest_color_fast(old_pixel, palette)
            new_pixel = palette[new_idx]
            output[y, x] = new_idx

            quant_error = old_pixel - new_pixel

            # Distribute error to neighbors
            if x + 1 < width:
                error[y, x + 1] += quant_error * 7 / 16
            if y + 1 < height:
                if x > 0:
                    error[y + 1, x - 1] += quant_error * 3 / 16
                error[y + 1, x] += quant_error * 5 / 16
                if x + 1 < width:
                    error[y + 1, x + 1] += quant_error * 1 / 16

    return output
```

**CLI:** `--quantize-method [perceptual|fast]`, `--dither [floyd-steinberg|ordered|none]`

---

### 0.9 Core Architecture & Safeguards ✅

**Files:** `tools/pipeline/core/` ✅ IMPLEMENTED

**Purpose:** Unified pipeline architecture with enforced safeguards that cannot be bypassed. Provides clean separation between core logic and interfaces (CLI/GUI).

**Architecture:**

```
tools/pipeline/
├── core/                    # Core library (CLI/GUI agnostic)
│   ├── __init__.py         # Public exports
│   ├── config.py           # Unified configuration (dataclasses)
│   ├── pipeline.py         # Main orchestrator
│   ├── safeguards.py       # ENFORCED safety (cannot bypass)
│   └── events.py           # Progress callbacks for GUI
├── cli.py                   # CLI wrapper (thin layer)
└── unified_pipeline.py      # Legacy entry point (wraps core)
```

**Key Classes:**

```python
from tools.pipeline.core import Pipeline, PipelineConfig, SafeguardConfig

# Configuration with enforced safeguards
config = PipelineConfig(
    platform='genesis',
    safeguards=SafeguardConfig(
        dry_run=True,               # DEFAULT: True for safety
        max_generations_per_run=5,  # Budget limit
        max_cost_per_run=0.50,      # Cost limit in USD
        require_confirmation=True,  # Prompt before destructive ops
    ),
)

# Create pipeline
pipeline = Pipeline(config)

# Process (auto-detects input type: PNG, Aseprite, or prompt)
result = pipeline.process('sprite.png', 'output/')
result = pipeline.process('character.ase', 'output/')
result = pipeline.generate('warrior with sword', 'output/')
```

**Enforced Safeguards (CANNOT be bypassed):**

| Safeguard | Default | Purpose |
|-----------|---------|---------|
| `dry_run` | `True` | Must explicitly disable to run real operations |
| `max_generations_per_run` | 5 | Hard limit on AI generations |
| `max_cost_per_run` | $0.50 | Hard limit on API costs |
| `require_confirmation` | `True` | Prompt before destructive operations |
| Caching | Always ON | Saves before processing to prevent data loss |
| Validation | Always ON | Checks inputs/outputs before processing |

**Event System (for GUI):**

```python
from tools.pipeline.core import EventEmitter, EventType

emitter = EventEmitter()
emitter.on(EventType.PROGRESS, lambda e: update_ui(e.percent, e.message))
emitter.on(EventType.STAGE_START, lambda e: show_stage(e.stage_name))
emitter.on(EventType.GENERATION_COMPLETE, lambda e: log_cost(e.data['cost']))

pipeline = Pipeline(config, event_emitter=emitter)
```

**CLI:**

```bash
# Status check
python -m tools.pipeline.cli --status

# Dry-run (default - safe preview)
python -m tools.pipeline.cli sprite.png -o output/

# Execute (requires explicit --no-dry-run)
python -m tools.pipeline.cli sprite.png -o output/ --no-dry-run

# Custom budget
python -m tools.pipeline.cli sprite.png -o output/ --max-gens 10 --max-cost 1.00 --no-dry-run

# Generate from prompt
python -m tools.pipeline.cli "warrior with sword" -o output/ --generate --8dir --no-dry-run
```

**New CLI Flags:**

| Flag | Description |
|------|-------------|
| `--status` | Show safeguard status (budget remaining, dry-run state) |
| `--no-dry-run` | REQUIRED to enable real operations |
| `--no-confirm` | Skip confirmation prompts |
| `--max-gens N` | Maximum generations per run (default: 5) |
| `--max-cost USD` | Maximum cost in USD (default: 0.50) |
| `--config FILE` | Load configuration from JSON file |
| `--save-config FILE` | Save current configuration to JSON file |

---

### Phase 0 Quality Gates

- [x] **Tests**: `test_sgdk_format.py`, `test_genesis_export.py`, `test_platforms.py`
- [x] **Tests**: `test_perceptual.py`, `test_dither_numba.py` (for 0.7-0.8) ✅
- [x] **Tests**: `test_core_pipeline.py`, `test_safeguards.py` (for 0.9) ✅
- [x] **Docs**: Module docstrings in all Phase 0 files
- [x] **USAGE.md**: Foundation modules documented (sgdk_format, genesis_export, platforms)
- [x] **USAGE.md**: Perceptual/dither modules documented (v1.3.0)
- [x] **USAGE.md**: Core architecture & safeguards documented (for 0.9) ✅
- [x] **Types**: Type hints on SGDKFormatter, ValidationResult, export functions
- [x] **Types**: Type hints on Pipeline, PipelineConfig, Safeguards (0.9)
- [x] **CLI**: `--format-sgdk`, `--platform genesis`, `--quantize-method`, `--dither` documented
- [x] **CLI**: `--status`, `--no-dry-run`, `--max-gens`, `--max-cost` documented (0.9)
- [x] **Integration**: Verified with SGDK rescomp compilation
- [x] **Integration**: Core pipeline verified with dry-run mode (0.9)
- [x] **Review**: No critical DEBT markers remaining

**Remaining for Phase 0:**

- [x] `quantization/perceptual.py` (0.7) - CIEDE2000, colour-science integration ✅ IMPLEMENTED
- [x] `quantization/dither_numba.py` (0.8) - JIT-accelerated dithering ✅ IMPLEMENTED
- [x] `core/` (0.9) - Unified architecture with enforced safeguards ✅ IMPLEMENTED
- [x] `cli.py` (0.9) - New CLI wrapper with safeguard integration ✅ IMPLEMENTED

**Phase 0 Status: COMPLETE** ✅

---

## Phase 1: Core Features

**Goal:** Essential sprite processing features that build on Phase 0 foundation.

**Dependencies:** Phase 0 complete

### 1.1 Animation Metadata Extraction ✅

**File:** `tools/pipeline/animation.py` ✅ IMPLEMENTED

**Purpose:** Auto-detect frame sequences from sprite sheets and generate SGDK-ready animation definitions.

**Features:**
- Parse filename patterns (`idle_01`, `walk_02`, `attack_03`)
- Detect animation sequences from spatial arrangement
- Generate frame timing metadata
- Mark loop points (one-shot vs looping)
- Export SGDK `AnimationFrame` structs

```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
import re

class AnimationPattern(Enum):
    PREFIX_NUMBER = "prefix_##"     # idle_01, idle_02
    SPATIAL = "spatial"             # Left-to-right, top-to-bottom
    AI = "ai"                       # AI-assisted grouping

@dataclass
class AnimationFrame:
    sprite_index: int               # Index in sprite sheet
    duration: int                   # Frames to display (1 = 1/60s)
    hotspot_x: int = 0              # Pivot point X
    hotspot_y: int = 0              # Pivot point Y

@dataclass
class AnimationSequence:
    name: str                       # "idle", "walk", "attack"
    frames: List[AnimationFrame] = field(default_factory=list)
    loop: bool = True               # True = loop, False = one-shot

    @property
    def frame_count(self) -> int:
        return len(self.frames)

    @property
    def total_duration(self) -> int:
        return sum(f.duration for f in self.frames)

# Default timing by action type (frames per sprite at 60fps)
DEFAULT_TIMING = {
    'idle': 10,      # Slow breathing
    'walk': 6,       # Medium pace
    'run': 4,        # Fast
    'attack': 3,     # Quick strikes
    'hit': 2,        # Very fast reaction
    'death': 8,      # Dramatic
    'default': 6,    # Fallback
}

class AnimationExtractor:
    """Extract animation sequences from sprite sheets."""

    def __init__(self, default_duration: int = 6):
        self.default_duration = default_duration

    def extract_from_names(self, sprite_names: List[str]) -> List[AnimationSequence]:
        """
        Extract animations from sprite names using prefix_## pattern.

        Example:
            ['idle_01', 'idle_02', 'walk_01', 'walk_02']
            → [AnimationSequence('idle', 2 frames), AnimationSequence('walk', 2 frames)]
        """
        groups: Dict[str, List[tuple]] = {}
        pattern = re.compile(r'^(.+?)_?(\d+)$')

        for idx, name in enumerate(sprite_names):
            match = pattern.match(name)
            if match:
                prefix = match.group(1)
                frame_num = int(match.group(2))
                if prefix not in groups:
                    groups[prefix] = []
                groups[prefix].append((idx, frame_num))

        sequences = []
        for prefix, frames in groups.items():
            frames.sort(key=lambda x: x[1])
            duration = DEFAULT_TIMING.get(prefix.lower(), self.default_duration)
            loop = prefix.lower() not in ['attack', 'death', 'hit', 'die']

            seq = AnimationSequence(
                name=prefix,
                frames=[AnimationFrame(sprite_index=idx, duration=duration)
                        for idx, _ in frames],
                loop=loop
            )
            sequences.append(seq)

        return sequences

    def extract_spatial(self, sprite_count: int, frames_per_row: int,
                        anim_names: List[str] = None) -> List[AnimationSequence]:
        """Extract animations assuming row-major layout."""
        sequences = []
        num_anims = sprite_count // frames_per_row

        for i in range(num_anims):
            name = anim_names[i] if anim_names and i < len(anim_names) else f"anim_{i}"
            start_idx = i * frames_per_row

            seq = AnimationSequence(
                name=name,
                frames=[AnimationFrame(sprite_index=start_idx + j, duration=self.default_duration)
                        for j in range(frames_per_row)],
                loop=True
            )
            sequences.append(seq)

        return sequences

def export_sgdk_animations(sequences: List[AnimationSequence], output_path: str) -> None:
    """Generate SGDK-compatible C header with animation data."""
    lines = [
        "// Auto-generated animation data",
        "// Generated by unified_pipeline.py",
        "",
        "#ifndef _ANIMATIONS_H_",
        "#define _ANIMATIONS_H_",
        "",
        "#include <genesis.h>",
        ""
    ]

    for seq in sequences:
        c_name = seq.name.upper()
        lines.append(f"// Animation: {seq.name} ({seq.frame_count} frames, {'loop' if seq.loop else 'one-shot'})")
        lines.append(f"const AnimationFrame anim_{seq.name}[] = {{")
        for frame in seq.frames:
            lines.append(f"    {{ {frame.sprite_index}, {frame.duration}, {frame.hotspot_x}, {frame.hotspot_y} }},")
        lines.append("};")
        lines.append(f"const Animation animation_{seq.name} = {{ anim_{seq.name}, {seq.frame_count}, {'TRUE' if seq.loop else 'FALSE'} }};")
        lines.append("")

    lines.append("#endif // _ANIMATIONS_H_")

    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))
```

**SGDK Export Format:**
```c
const AnimationFrame anim_player_idle[] = {
    { 0, 10, 16, 32 },  // frame 0, 10 ticks, hotspot at (16,32)
    { 1, 10, 16, 32 },
    { 2, 10, 16, 32 },
    { 3, 10, 16, 32 },
};

const Animation animation_player_idle = {
    anim_player_idle,
    4,      // frame count
    TRUE    // loop
};
```

**CLI:** `--animations`

---

### 1.2 Sprite Sheet Assembly ✅

**File:** `tools/pipeline/sheet_assembler.py` ✅ IMPLEMENTED

**Purpose:** Pack individual sprite frames into optimized sprite sheets with metadata.

**Features:**
- Bin-packing algorithm for minimal sheet size
- Power-of-2 dimensions (VRAM friendly)
- Generate frame index JSON
- Hotspot/pivot point marking
- Padding options (1px for filtering)

```python
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any, Optional
from PIL import Image

@dataclass
class FramePlacement:
    source_path: str
    name: str
    x: int                      # Position in sheet
    y: int
    width: int
    height: int
    hotspot_x: int = 0          # Relative to frame
    hotspot_y: int = 0

@dataclass
class SheetLayout:
    width: int
    height: int
    frames: List[FramePlacement]

class SpriteSheetAssembler:
    """
    Bin-packing sprite sheet generator.

    Advantages over grid layout:
    - 15-40% VRAM savings with irregular sprites
    - Power-of-2 sheet dimensions for Genesis VDP
    - Maintains tile alignment (8px boundaries)
    """

    VALID_SHEET_SIZES = [64, 128, 256, 512]
    TILE_ALIGN = 8

    def __init__(self, max_width: int = 256, max_height: int = 256,
                 padding: int = 0, power_of_2: bool = True):
        self.max_width = max_width
        self.max_height = max_height
        self.padding = padding
        self.power_of_2 = power_of_2
        self.frames: List[Tuple[str, str, Image.Image, Tuple[int, int]]] = []

    def add_frame(self, image: Image.Image, name: str,
                  source_path: str = "", hotspot: Tuple[int, int] = None) -> None:
        """Add a frame to be packed."""
        hs = hotspot or (image.width // 2, image.height)
        self.frames.append((name, source_path, image, hs))

    def assemble(self) -> Tuple[Image.Image, SheetLayout]:
        """Pack all frames into optimal sheet using shelf algorithm."""
        if not self.frames:
            raise ValueError("No frames to assemble")

        # Sort by height (descending) for better shelf packing
        sorted_frames = sorted(self.frames, key=lambda f: f[2].height, reverse=True)

        # Calculate required dimensions
        placements = []
        shelf_y = 0
        shelf_height = 0
        current_x = 0
        max_width_used = 0

        for name, source, img, hotspot in sorted_frames:
            w = self._align_to_tile(img.width) + self.padding
            h = self._align_to_tile(img.height) + self.padding

            # Check if fits on current shelf
            if current_x + w > self.max_width:
                # Move to next shelf
                shelf_y += shelf_height
                shelf_height = 0
                current_x = 0

            # Place on current shelf
            placements.append(FramePlacement(
                source_path=source,
                name=name,
                x=current_x,
                y=shelf_y,
                width=img.width,
                height=img.height,
                hotspot_x=hotspot[0],
                hotspot_y=hotspot[1]
            ))

            shelf_height = max(shelf_height, h)
            current_x += w
            max_width_used = max(max_width_used, current_x)

        total_height = shelf_y + shelf_height

        # Round to power of 2 if requested
        if self.power_of_2:
            sheet_width = self._next_power_of_2(max_width_used)
            sheet_height = self._next_power_of_2(total_height)
        else:
            sheet_width = max_width_used
            sheet_height = total_height

        # Ensure minimum width for SGDK
        sheet_width = max(sheet_width, 128)

        # Create sheet
        sheet = Image.new('RGBA', (sheet_width, sheet_height), (255, 0, 255, 255))

        # Place frames
        for i, (name, source, img, hotspot) in enumerate(sorted_frames):
            p = placements[i]
            sheet.paste(img, (p.x, p.y), img if img.mode == 'RGBA' else None)

        layout = SheetLayout(width=sheet_width, height=sheet_height, frames=placements)
        return sheet, layout

    def export_metadata(self, layout: SheetLayout, output_path: str,
                        format: str = "json") -> None:
        """Export frame positions as JSON or C header."""
        import json

        if format == "json":
            data = {
                "sheet_width": layout.width,
                "sheet_height": layout.height,
                "frames": [
                    {
                        "name": f.name,
                        "x": f.x, "y": f.y,
                        "w": f.width, "h": f.height,
                        "hx": f.hotspot_x, "hy": f.hotspot_y
                    }
                    for f in layout.frames
                ]
            }
            with open(output_path, 'w') as fp:
                json.dump(data, fp, indent=2)
        elif format == "c":
            self._export_c_header(layout, output_path)

    def _export_c_header(self, layout: SheetLayout, output_path: str) -> None:
        """Generate C header with frame data."""
        lines = [
            "// Auto-generated sprite sheet metadata",
            "#ifndef _SHEET_FRAMES_H_",
            "#define _SHEET_FRAMES_H_",
            "",
            f"#define SHEET_WIDTH  {layout.width}",
            f"#define SHEET_HEIGHT {layout.height}",
            f"#define FRAME_COUNT  {len(layout.frames)}",
            "",
            "typedef struct { s16 x, y, w, h, hx, hy; } FrameInfo;",
            "",
            "const FrameInfo frames[] = {"
        ]
        for f in layout.frames:
            lines.append(f"    {{ {f.x}, {f.y}, {f.width}, {f.height}, {f.hotspot_x}, {f.hotspot_y} }}, // {f.name}")
        lines.append("};")
        lines.append("")
        lines.append("#endif")

        with open(output_path, 'w') as fp:
            fp.write('\n'.join(lines))

    def _align_to_tile(self, size: int) -> int:
        """Align to 8-pixel tile boundary."""
        return ((size + self.TILE_ALIGN - 1) // self.TILE_ALIGN) * self.TILE_ALIGN

    def _next_power_of_2(self, n: int) -> int:
        """Round up to next power of 2."""
        for size in self.VALID_SHEET_SIZES:
            if n <= size:
                return size
        return 512
```

**Output JSON:**
```json
{
  "sheet_width": 128,
  "sheet_height": 64,
  "frames": [
    {"name": "idle_0", "x": 0, "y": 0, "w": 32, "h": 32, "hx": 16, "hy": 32},
    {"name": "idle_1", "x": 32, "y": 0, "w": 32, "h": 32, "hx": 16, "hy": 32}
  ]
}
```

**CLI:** `--assemble-sheet`

---

### 1.3 Hit Flash / Effect Variants ✅

**File:** `tools/pipeline/effects.py` ✅ IMPLEMENTED

**Purpose:** Generate common sprite effect variants without AI.

**Features:**
- White flash (hit confirmation)
- Damage tint (red overlay)
- Invulnerability blink (alternating frames)
- Silhouette (solid color)
- Palette swap

```python
from PIL import Image
from typing import List, Tuple

class SpriteEffects:
    """Generate sprite effect variants using PIL operations."""

    @staticmethod
    def white_flash(img: Image.Image, threshold: int = 128) -> Image.Image:
        """Replace all non-transparent pixels with white."""
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        result = img.copy()
        pixels = result.load()

        for y in range(img.height):
            for x in range(img.width):
                r, g, b, a = pixels[x, y]
                if a >= threshold:
                    pixels[x, y] = (255, 255, 255, a)

        return result

    @staticmethod
    def damage_tint(img: Image.Image, tint: Tuple[int, int, int] = (255, 0, 0),
                    intensity: float = 0.5) -> Image.Image:
        """Overlay a color tint on the sprite."""
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        result = img.copy()
        pixels = result.load()

        for y in range(img.height):
            for x in range(img.width):
                r, g, b, a = pixels[x, y]
                if a > 0:
                    r = int(r * (1 - intensity) + tint[0] * intensity)
                    g = int(g * (1 - intensity) + tint[1] * intensity)
                    b = int(b * (1 - intensity) + tint[2] * intensity)
                    pixels[x, y] = (r, g, b, a)

        return result

    @staticmethod
    def invulnerability_blink(img: Image.Image) -> List[Image.Image]:
        """Generate 2-frame blink sequence (normal, brightened)."""
        normal = img.copy()
        bright = SpriteEffects.damage_tint(img, (255, 255, 255), 0.3)
        return [normal, bright]

    @staticmethod
    def silhouette(img: Image.Image, color: Tuple[int, int, int] = (0, 0, 0),
                   threshold: int = 128) -> Image.Image:
        """Create solid color silhouette."""
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        result = img.copy()
        pixels = result.load()

        for y in range(img.height):
            for x in range(img.width):
                r, g, b, a = pixels[x, y]
                if a >= threshold:
                    pixels[x, y] = (*color, a)

        return result

    @staticmethod
    def palette_swap(img: Image.Image,
                     mapping: dict) -> Image.Image:
        """Swap colors according to mapping dict."""
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        result = img.copy()
        pixels = result.load()

        for y in range(img.height):
            for x in range(img.width):
                pixel = pixels[x, y][:3]
                if pixel in mapping:
                    r, g, b = mapping[pixel]
                    pixels[x, y] = (r, g, b, pixels[x, y][3])

        return result
```

**CLI:** `--hit-flash`, `--damage-tint`, `--silhouette`

---

### 1.4 8-Direction Rotation ✅

**File:** `tools/pipeline/rotation.py` ✅ IMPLEMENTED

**Purpose:** Generate 8 directional variants from a single sprite.

**Features:**
- Simple PIL rotation (fast, lower quality)
- PixelLab AI rotation (higher quality, costs $0.01/image)
- Automatic mirroring for symmetric directions

```python
from PIL import Image
from typing import List, Optional
from enum import Enum

class Direction(Enum):
    N = 0
    NE = 1
    E = 2
    SE = 3
    S = 4
    SW = 5
    W = 6
    NW = 7

class SpriteRotator:
    """Generate directional sprite variants."""

    DIRECTION_ANGLES = {
        Direction.N: 0,
        Direction.NE: 45,
        Direction.E: 90,
        Direction.SE: 135,
        Direction.S: 180,
        Direction.SW: 225,
        Direction.W: 270,
        Direction.NW: 315,
    }

    def __init__(self, use_ai: bool = False, pixellab_client=None):
        self.use_ai = use_ai
        self.pixellab = pixellab_client

    def rotate_simple(self, img: Image.Image, source_dir: Direction = Direction.E) -> List[Image.Image]:
        """
        Generate 8 directions using PIL rotation and mirroring.

        Note: Best for top-down or simple sprites. Side-view sprites
        should use AI rotation for better quality.
        """
        results = []
        base_angle = self.DIRECTION_ANGLES[source_dir]

        for direction in Direction:
            target_angle = self.DIRECTION_ANGLES[direction]
            rotation = (target_angle - base_angle) % 360

            if rotation == 0:
                results.append(img.copy())
            elif rotation == 180:
                results.append(img.transpose(Image.ROTATE_180))
            else:
                # For non-90-degree rotations, use affine transform
                rotated = img.rotate(-rotation, expand=True, resample=Image.NEAREST)
                results.append(rotated)

        return results

    def rotate_with_mirror(self, img: Image.Image,
                           source_dir: Direction = Direction.E) -> List[Image.Image]:
        """
        Generate 8 directions using mirroring where possible.

        Assumes sprite is roughly symmetric. Generates:
        - E (original)
        - W (horizontal flip of E)
        - N, S, NE, SE, NW, SW via rotation
        """
        results = [None] * 8

        # Original direction
        results[source_dir.value] = img.copy()

        # Horizontal mirror
        opposite = (source_dir.value + 4) % 8
        results[opposite] = img.transpose(Image.FLIP_LEFT_RIGHT)

        # Fill remaining with rotations (lower quality, but fast)
        for i, direction in enumerate(Direction):
            if results[i] is None:
                angle = (self.DIRECTION_ANGLES[direction] - self.DIRECTION_ANGLES[source_dir]) % 360
                results[i] = img.rotate(-angle, expand=False, resample=Image.NEAREST)

        return results

    async def rotate_ai(self, img: Image.Image, width: int, height: int) -> Optional[List[Image.Image]]:
        """
        Generate 8 directions using PixelLab AI.

        Returns None if AI is unavailable.
        """
        if not self.use_ai or not self.pixellab:
            return None

        result = self.pixellab.generate_8_rotations(img, width, height)
        if result.success:
            return result.images
        return None
```

**CLI:** `--rotate-8dir [simple|mirror|ai]`

---

### 1.5 Tile Deduplication with Mirroring ✅

**Enhancement to:** `tools/pipeline/genesis_export.py` ✅ IMPLEMENTED

**Purpose:** Detect H/V flipped tile duplicates and save VRAM.

**Current State:** ✅ Fully implemented with H-flip, V-flip, and H+V flip detection.

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class TileMatch:
    index: int                  # Index of matching unique tile
    h_flip: bool                # Horizontally flipped
    v_flip: bool                # Vertically flipped

def flip_tile_h(tile_bytes: bytes) -> bytes:
    """Horizontally flip an 8x8 tile (4bpp, 32 bytes)."""
    result = bytearray(32)
    for row in range(8):
        for col in range(4):
            src_byte = tile_bytes[row * 4 + col]
            dst_col = 3 - col
            # Swap nibbles within byte AND reverse byte order
            result[row * 4 + dst_col] = ((src_byte & 0x0F) << 4) | ((src_byte & 0xF0) >> 4)
    return bytes(result)

def flip_tile_v(tile_bytes: bytes) -> bytes:
    """Vertically flip an 8x8 tile (4bpp, 32 bytes)."""
    result = bytearray(32)
    for row in range(8):
        src_row = 7 - row
        for col in range(4):
            result[row * 4 + col] = tile_bytes[src_row * 4 + col]
    return bytes(result)

def find_tile_match(tile_bytes: bytes,
                    unique_tiles: List[bytes]) -> Optional[TileMatch]:
    """
    Check if tile matches any unique tile, including flipped variants.

    Returns:
        TileMatch with flip flags, or None if no match
    """
    # Check exact match
    try:
        idx = unique_tiles.index(tile_bytes)
        return TileMatch(idx, False, False)
    except ValueError:
        pass

    # Check H-flip
    h_flipped = flip_tile_h(tile_bytes)
    try:
        idx = unique_tiles.index(h_flipped)
        return TileMatch(idx, True, False)
    except ValueError:
        pass

    # Check V-flip
    v_flipped = flip_tile_v(tile_bytes)
    try:
        idx = unique_tiles.index(v_flipped)
        return TileMatch(idx, False, True)
    except ValueError:
        pass

    # Check H+V flip
    hv_flipped = flip_tile_h(v_flipped)
    try:
        idx = unique_tiles.index(hv_flipped)
        return TileMatch(idx, True, True)
    except ValueError:
        pass

    return None

def export_genesis_tilemap_optimized(indexed_img, output_path: str,
                                      use_mirroring: bool = True) -> dict:
    """
    Enhanced tilemap export with flip flag optimization.

    Tilemap entry format (16-bit):
    Bits 15: Priority
    Bits 14-13: Palette
    Bit 12: V-flip
    Bit 11: H-flip
    Bits 10-0: Tile index
    """
    # Implementation extends existing export_genesis_tilemap()
    # to use find_tile_match() for mirror detection
    pass
```

**Expected VRAM Savings:** 20-40% fewer unique tiles for symmetric content.

**CLI:** `--optimize-mirrors`

---

### 1.6 Palette Cross-Platform Converter ✅

**File:** `tools/pipeline/palette_converter.py` ✅ IMPLEMENTED

**Purpose:** Convert palettes between platform-specific formats.

```python
from enum import Enum
from typing import List, Tuple
import colorsys

class PaletteFormat(Enum):
    GENESIS_9BIT = "genesis"    # 3-3-3 BGR (512 colors)
    NES_6BIT = "nes"            # Fixed 64-color palette
    SNES_15BIT = "snes"         # 5-5-5 BGR (32768 colors)
    RGB_24BIT = "rgb"           # 8-8-8 standard

# NES fixed palette (first 16 shown)
NES_PALETTE = [
    (84, 84, 84), (0, 30, 116), (8, 16, 144), (48, 0, 136),
    (68, 0, 100), (92, 0, 48), (84, 4, 0), (60, 24, 0),
    (32, 42, 0), (8, 58, 0), (0, 64, 0), (0, 60, 0),
    (0, 50, 60), (0, 0, 0), (0, 0, 0), (0, 0, 0),
    # ... 48 more colors
]

class PaletteConverter:
    """Convert palettes between platform formats."""

    def rgb_to_genesis(self, r: int, g: int, b: int) -> int:
        """Convert 24-bit RGB to Genesis 9-bit BGR."""
        # Genesis format: 0000BBB0GGG0RRR0
        r3 = (r >> 5) & 0x07
        g3 = (g >> 5) & 0x07
        b3 = (b >> 5) & 0x07
        return (b3 << 9) | (g3 << 5) | (r3 << 1)

    def genesis_to_rgb(self, value: int) -> Tuple[int, int, int]:
        """Convert Genesis 9-bit to 24-bit RGB."""
        r = ((value >> 1) & 0x07) * 36
        g = ((value >> 5) & 0x07) * 36
        b = ((value >> 9) & 0x07) * 36
        return (r, g, b)

    def rgb_to_snes(self, r: int, g: int, b: int) -> int:
        """Convert 24-bit RGB to SNES 15-bit BGR."""
        r5 = (r >> 3) & 0x1F
        g5 = (g >> 3) & 0x1F
        b5 = (b >> 3) & 0x1F
        return (b5 << 10) | (g5 << 5) | r5

    def find_nearest_nes(self, rgb: Tuple[int, int, int]) -> int:
        """Find nearest NES palette entry using LAB color distance."""
        min_dist = float('inf')
        best_idx = 0

        for idx, nes_color in enumerate(NES_PALETTE):
            dist = self._color_distance_lab(rgb, nes_color)
            if dist < min_dist:
                min_dist = dist
                best_idx = idx

        return best_idx

    def convert_palette(self, colors: List[Tuple[int, int, int]],
                        target: PaletteFormat) -> List[int]:
        """Convert RGB palette to target format."""
        if target == PaletteFormat.GENESIS_9BIT:
            return [self.rgb_to_genesis(*c) for c in colors]
        elif target == PaletteFormat.SNES_15BIT:
            return [self.rgb_to_snes(*c) for c in colors]
        elif target == PaletteFormat.NES_6BIT:
            return [self.find_nearest_nes(c) for c in colors]
        else:
            return colors

    def export_genesis_cram(self, colors: List[Tuple[int, int, int]]) -> bytes:
        """Export as Genesis CRAM format (32 bytes for 16 colors)."""
        data = bytearray()
        for color in colors[:16]:
            value = self.rgb_to_genesis(*color)
            data.extend(value.to_bytes(2, byteorder='big'))
        # Pad to 32 bytes if needed
        while len(data) < 32:
            data.extend(b'\x00\x00')
        return bytes(data)

    def export_c_header(self, colors: List[Tuple[int, int, int]],
                        name: str, format: PaletteFormat) -> str:
        """Generate C header with palette data."""
        converted = self.convert_palette(colors, format)
        c_name = name.upper()

        lines = [
            f"// Auto-generated palette ({format.value})",
            f"const u16 pal_{name}[16] = {{"
        ]

        for i, value in enumerate(converted[:16]):
            comment = f"// {colors[i]}" if i < len(colors) else ""
            lines.append(f"    0x{value:04X}, {comment}")

        lines.append("};")
        return '\n'.join(lines)

    def _color_distance_lab(self, c1: Tuple[int, int, int],
                            c2: Tuple[int, int, int]) -> float:
        """Calculate perceptual color distance in LAB space."""
        # Simplified: use RGB Euclidean for now
        # TODO: Implement proper LAB conversion
        dr = c1[0] - c2[0]
        dg = c1[1] - c2[1]
        db = c1[2] - c2[2]
        return (dr*dr + dg*dg + db*db) ** 0.5
```

**CLI:** `--convert-palette --to [genesis|nes|snes]`

---

### 1.7 Batch Processing Mode ✅

**Enhancement to:** `tools/pipeline/core/pipeline.py` ✅ IMPLEMENTED

**Purpose:** Process entire asset folders efficiently.

**Features:**
- Progress events via EventEmitter
- Per-file success/failure tracking
- Error summary at end
- Integrated with safeguards

**CLI:** `python -m tools.pipeline.cli --batch DIR -o OUTPUT/`

---

### 1.8 Aseprite Integration ✅

**File:** `tools/pipeline/integrations/aseprite.py` ✅ IMPLEMENTED

**Purpose:** Automate sprite export from Aseprite files, preserving layers, tags, and metadata.

**Methods:**
- [Aseprite CLI](https://www.aseprite.org/docs/cli/) - Batch export via subprocess
- [Aseprite Lua API](https://www.aseprite.org/api/) - In-editor scripting
- [Aseprite MCP Server](https://creati.ai/mcp/aseprite-mcp/) - Python remote control

**Features:**
- Auto-export `.ase` → sprite sheet + JSON metadata
- Preserve layer structure (body, shadow, effects)
- Extract animation tags as separate sequences
- Generate SGDK-ready output directly

```python
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class AsepriteExportResult:
    sheet_path: Path
    json_path: Path
    layers: List[str]
    tags: List[str]
    frame_count: int

class AsepriteExporter:
    """
    Automate Aseprite sprite exports via CLI.

    Requires Aseprite to be installed and in PATH, or specify exe_path.
    """

    def __init__(self, exe_path: Optional[str] = None):
        self.exe = exe_path or "aseprite"

    def export_sheet(self,
                     input_path: Path,
                     output_dir: Path,
                     *,
                     scale: int = 1,
                     sheet_type: str = "packed",
                     split_layers: bool = False,
                     split_tags: bool = False) -> AsepriteExportResult:
        """
        Export Aseprite file to sprite sheet with metadata.

        Args:
            input_path: Path to .ase or .aseprite file
            output_dir: Output directory
            scale: Scale factor (1, 2, 4)
            sheet_type: "packed" | "horizontal" | "vertical" | "rows"
            split_layers: Export each layer as separate sheet
            split_tags: Export each tag as separate sheet

        Returns:
            AsepriteExportResult with paths and metadata
        """
        name = input_path.stem
        sheet_path = output_dir / f"{name}.png"
        json_path = output_dir / f"{name}.json"

        cmd = [
            self.exe, "-b",  # Batch mode
            str(input_path),
            "--sheet", str(sheet_path),
            "--sheet-type", sheet_type,
            "--data", str(json_path),
            "--format", "json-array",
            "--list-layers",
            "--list-tags",
        ]

        if scale != 1:
            cmd.extend(["--scale", str(scale)])

        if split_layers:
            cmd.append("--split-layers")

        if split_tags:
            cmd.append("--split-tags")

        subprocess.run(cmd, check=True, capture_output=True)

        # Parse JSON for metadata
        with open(json_path) as f:
            data = json.load(f)

        return AsepriteExportResult(
            sheet_path=sheet_path,
            json_path=json_path,
            layers=data.get("meta", {}).get("layers", []),
            tags=[t["name"] for t in data.get("meta", {}).get("frameTags", [])],
            frame_count=len(data.get("frames", []))
        )

    def export_layers_separate(self,
                               input_path: Path,
                               output_dir: Path) -> Dict[str, Path]:
        """Export each layer as a separate PNG."""
        cmd = [
            self.exe, "-b",
            str(input_path),
            "--save-as", str(output_dir / "{layer}.png"),
            "--split-layers"
        ]
        subprocess.run(cmd, check=True, capture_output=True)

        return {p.stem: p for p in output_dir.glob("*.png")}
```

**CLI:** `--from-aseprite FILE.ase`, `--ase-split-layers`, `--ase-split-tags`

### Phase 1 Quality Gates

- [x] **Tests**: `test_animation.py`, `test_sheet_assembler.py`, `test_palette_converter.py`
- [x] **Tests**: `test_rotation.py` (1.4) ✅
- [x] **Docs**: Docstrings for AnimationExtractor, SpriteSheetAssembler, PaletteConverter
- [x] **USAGE.md**: Animation, Sheet Assembly, Palette modules documented
- [x] **USAGE.md**: Effects, Aseprite modules documented (v1.4.0)
- [x] **Types**: Complete type hints on all public interfaces
- [x] **CLI**: `--animations`, `--assemble-sheet`, `--convert-palette` documented
- [x] **CLI**: `--rotate-8dir`, `--batch` documented (1.4, 1.7)
- [x] **Integration**: Output compatible with Phase 0 SGDK formatter
- [x] **Review**: Audited `effects.py`, `rotation.py` for DEBT markers

**Remaining for Phase 1:**

- [x] `effects.py` (1.3) - Hit flash, damage tint, silhouette ✅ IMPLEMENTED
- [x] `rotation.py` (1.4) - 8-direction sprite generation ✅ IMPLEMENTED
- [x] Tile deduplication with mirroring (1.5) ✅ IMPLEMENTED
- [x] Batch processing mode (1.7) ✅ IMPLEMENTED
- [x] `integrations/aseprite.py` (1.8) - Aseprite CLI automation ✅ IMPLEMENTED

**Phase 1 Status: COMPLETE** ✅

---

## Phase 2: SGDK Integration

**Goal:** Generate SGDK-ready assets directly from the pipeline.

**Dependencies:** Phase 1 complete (especially 1.1 Animation, 1.2 Sheet Assembly)

### 2.1 SGDK Resource File (.res) Generation ✅

**File:** `tools/pipeline/sgdk_resources.py` ✅ IMPLEMENTED

**Purpose:** Generate complete SGDK resource definitions for rescomp.

```python
from typing import List, Optional
from dataclasses import dataclass, field

@dataclass
class SpriteResource:
    name: str
    path: str
    width_tiles: int
    height_tiles: int
    compression: str = "NONE"
    time: int = 0

@dataclass
class TilesetResource:
    name: str
    path: str
    compression: str = "NONE"
    opt: str = "ALL"

@dataclass
class PaletteResource:
    name: str
    path: str

@dataclass
class MapResource:
    name: str
    tileset: str
    path: str
    compression: str = "NONE"

class SGDKResourceGenerator:
    """Generate SGDK .res files for rescomp compilation."""

    def __init__(self):
        self.sprites: List[SpriteResource] = []
        self.tilesets: List[TilesetResource] = []
        self.palettes: List[PaletteResource] = []
        self.maps: List[MapResource] = []

    def add_sprite(self, name: str, path: str,
                   width_px: int, height_px: int,
                   compression: str = "NONE") -> None:
        """Register a sprite resource."""
        self.sprites.append(SpriteResource(
            name=name,
            path=path,
            width_tiles=width_px // 8,
            height_tiles=height_px // 8,
            compression=compression
        ))

    def add_tileset(self, name: str, path: str,
                    compression: str = "NONE") -> None:
        """Register a tileset resource."""
        self.tilesets.append(TilesetResource(
            name=name, path=path, compression=compression
        ))

    def add_palette(self, name: str, path: str) -> None:
        """Register a palette resource."""
        self.palettes.append(PaletteResource(name=name, path=path))

    def add_map(self, name: str, tileset_name: str,
                map_path: str, compression: str = "NONE") -> None:
        """Register a tilemap resource."""
        self.maps.append(MapResource(
            name=name, tileset=tileset_name,
            path=map_path, compression=compression
        ))

    def generate(self, output_path: str) -> None:
        """Generate complete .res file."""
        lines = [
            "// Auto-generated by unified_pipeline.py",
            "// Do not edit manually",
            ""
        ]

        # Palettes
        if self.palettes:
            lines.append("// Palettes")
            for p in self.palettes:
                lines.append(f'PALETTE {p.name} "{p.path}"')
            lines.append("")

        # Sprites
        if self.sprites:
            lines.append("// Sprites")
            for s in self.sprites:
                lines.append(f'SPRITE {s.name} "{s.path}" {s.width_tiles} {s.height_tiles} {s.compression} {s.time}')
            lines.append("")

        # Tilesets
        if self.tilesets:
            lines.append("// Tilesets")
            for t in self.tilesets:
                lines.append(f'TILESET {t.name} "{t.path}" {t.compression} {t.opt}')
            lines.append("")

        # Maps
        if self.maps:
            lines.append("// Maps")
            for m in self.maps:
                lines.append(f'MAP {m.name} {m.tileset} "{m.path}" {m.compression}')
            lines.append("")

        with open(output_path, 'w') as f:
            f.write('\n'.join(lines))
```

**Output:**
```
// Auto-generated by unified_pipeline.py

PALETTE pal_player "res/sprites/player_pal.png"

SPRITE spr_player "res/sprites/player.png" 4 4 NONE 0
SPRITE spr_fenrir "res/sprites/fenrir.png" 3 3 NONE 0

TILESET ts_siege "res/tiles/siege_tiles.png" NONE ALL

MAP map_siege ts_siege "res/maps/siege.tmx" NONE
```

**CLI:** `--generate-res`

---

### 2.2 VDP-Ready Export

**Enhancement to:** `tools/pipeline/genesis_export.py`

**Purpose:** Generate data directly usable by Genesis VDP hardware.

```python
from typing import List, Tuple

def export_sprite_attribute_table(sprites: List[dict],
                                   base_tile: int = 0,
                                   palette: int = 0) -> bytes:
    """
    Generate VDP Sprite Attribute Table entries.

    SAT Entry (8 bytes):
    - Word 0: Y position (+ 128 offset)
    - Word 1: Size (bits 10-8) | Link (bits 6-0)
    - Word 2: Priority/Palette/VF/HF/Tile
    - Word 3: X position (+ 128 offset)
    """
    data = bytearray()

    for i, sprite in enumerate(sprites):
        y = sprite['y'] + 128
        x = sprite['x'] + 128
        size = sprite.get('size', 0x05)  # Default 2x2 tiles
        link = (i + 1) if i < len(sprites) - 1 else 0
        tile = base_tile + sprite.get('tile_offset', 0)
        attr = (palette << 13) | tile

        data.extend(y.to_bytes(2, 'big'))
        data.extend(((size << 8) | link).to_bytes(2, 'big'))
        data.extend(attr.to_bytes(2, 'big'))
        data.extend(x.to_bytes(2, 'big'))

    return bytes(data)

def export_cram_palette(colors: List[Tuple[int, int, int]],
                        palette_index: int = 0) -> bytes:
    """
    Export palette in Genesis CRAM format.

    Each color: 0000BBB0GGG0RRR0 (9-bit, word-aligned)
    """
    from .palette_converter import PaletteConverter
    converter = PaletteConverter()
    return converter.export_genesis_cram(colors)

def export_tilemap_with_attributes(tilemap: List[int],
                                   palette: int = 0,
                                   priority: bool = False,
                                   base_tile: int = 0,
                                   flip_data: List[Tuple[bool, bool]] = None) -> bytes:
    """
    Export tilemap with full VDP attributes.

    Tilemap entry (16-bit):
    Bit 15: Priority
    Bits 14-13: Palette index
    Bit 12: Vertical flip
    Bit 11: Horizontal flip
    Bits 10-0: Tile index
    """
    data = bytearray()

    for i, tile_idx in enumerate(tilemap):
        entry = base_tile + tile_idx

        # Add flip flags if provided
        if flip_data and i < len(flip_data):
            h_flip, v_flip = flip_data[i]
            if h_flip:
                entry |= (1 << 11)
            if v_flip:
                entry |= (1 << 12)

        # Add palette
        entry |= (palette << 13)

        # Add priority
        if priority:
            entry |= (1 << 15)

        data.extend(entry.to_bytes(2, 'big'))

    return bytes(data)
```

**CLI:** `--vdp-export`

---

### 2.3 Performance Budget Calculator ✅

**File:** `tools/pipeline/performance.py` ✅ IMPLEMENTED

**Purpose:** Analyze assets for Genesis hardware limit violations.

```python
from dataclasses import dataclass, field
from typing import List, Dict
from PIL import Image

@dataclass
class PerformanceReport:
    sprites_total: int = 0
    sprites_per_scanline: Dict[int, int] = field(default_factory=dict)
    scanline_violations: List[int] = field(default_factory=list)
    dma_bytes: int = 0
    dma_time_lines: float = 0.0
    vram_tiles: int = 0
    vram_percent: float = 0.0
    warnings: List[str] = field(default_factory=list)

class PerformanceBudgetCalculator:
    """Analyze sprites for Genesis hardware limit violations."""

    # Genesis limits
    MAX_SPRITES = 80
    MAX_SPRITES_PER_LINE = 20
    MAX_PIXELS_PER_LINE = 320
    DMA_BYTES_PER_LINE = 168  # ~168 bytes per scanline in vblank
    VBLANK_LINES = 40         # ~40 scanlines at 60Hz NTSC
    VRAM_TILES = 2048         # Total VRAM tile slots

    def analyze_sprite_layout(self, sprites: List[dict],
                              screen_height: int = 224) -> PerformanceReport:
        """Analyze sprite positions for scanline violations."""
        report = PerformanceReport()
        report.sprites_total = len(sprites)

        # Count sprites per scanline
        for line in range(screen_height):
            count = 0
            for sprite in sprites:
                y = sprite['y']
                h = sprite['height']
                if y <= line < y + h:
                    count += 1

            if count > 0:
                report.sprites_per_scanline[line] = count

            if count > self.MAX_SPRITES_PER_LINE:
                report.scanline_violations.append(line)
                report.warnings.append(
                    f"Line {line}: {count} sprites (max {self.MAX_SPRITES_PER_LINE})"
                )

        return report

    def estimate_dma_time(self, tile_bytes: int) -> float:
        """Estimate DMA transfer time in scanlines."""
        return tile_bytes / self.DMA_BYTES_PER_LINE

    def check_vram_budget(self, tile_count: int) -> Tuple[int, float, List[str]]:
        """Check if tile count fits in VRAM."""
        percent = (tile_count / self.VRAM_TILES) * 100
        warnings = []

        if tile_count > self.VRAM_TILES:
            warnings.append(f"VRAM overflow: {tile_count} tiles > {self.VRAM_TILES} max")
        elif percent > 80:
            warnings.append(f"VRAM usage high: {percent:.1f}%")

        return tile_count, percent, warnings

    def generate_heatmap(self, sprites: List[dict],
                         width: int = 320, height: int = 224) -> Image.Image:
        """Generate visual heatmap showing sprite density."""
        img = Image.new('RGB', (width, height), (0, 0, 0))
        pixels = img.load()

        for line in range(height):
            count = 0
            for sprite in sprites:
                y = sprite['y']
                h = sprite['height']
                if y <= line < y + h:
                    count += 1

            # Color based on count
            if count == 0:
                color = (0, 0, 0)
            elif count <= 10:
                color = (0, 255, 0)      # Green: safe
            elif count <= 15:
                color = (255, 255, 0)    # Yellow: caution
            elif count <= 19:
                color = (255, 128, 0)    # Orange: near limit
            else:
                color = (255, 0, 0)      # Red: overflow

            for x in range(width):
                pixels[x, line] = color

        return img
```

**CLI:** `--performance-report`

---

### 2.4 Assembly Export Formats

**Enhancement to:** `tools/unified_pipeline.py`

**Purpose:** Export tile/sprite data in assembler-specific formats.

**Formats:**
- `ca65`: 6502 assembly for NES (cc65 toolchain)
- `asm68k`: 68000 assembly for Genesis
- `wla-dx`: Multi-platform assembler

```asm
; Example asm68k output
player_tiles:
    dc.l    $01234567, $89ABCDEF    ; Tile 0, row 0-1
    dc.l    $01234567, $89ABCDEF    ; Tile 0, row 2-3
    ; ...
```

**CLI:** `--format [ca65|asm68k|wla-dx]`

---

### 2.5 Tile Cache System

**Enhancement to:** `tools/pipeline/processing.py`

**Purpose:** Hash-based caching to avoid reprocessing unchanged tiles.

**Features:**
- SHA256 hash of tile content
- Disk-based cache with configurable size
- Cache invalidation on palette change
- Stats reporting

**CLI:** `--cache-dir DIR`, `--cache-stats`

---

### 2.6 Tilemap Editor Integration

**File:** `tools/pipeline/tilemap/tiled_import.py` (NEW)

**Purpose:** Import tilemaps from external editors (Tiled, LDtk) and convert to SGDK MAP format.

**Dependencies:**
```bash
pip install pytmx
```

**Editors Supported:**
- [Tiled](https://www.mapeditor.org/) via [PyTMX](https://github.com/bitcraft/PyTMX) - Industry standard TMX/JSON format
- [LDtk](https://ldtk.io/) - Modern JSON format with built-in auto-tiling

**Features:**
- Import TMX/JSON tilemaps from Tiled
- Import LDtk project files (native JSON)
- Convert tile indices to SGDK MAP format
- Extract collision layers as separate data
- Support for multiple layers (background, foreground, collision)

```python
import pytmx
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass
class TilemapLayer:
    name: str
    width: int
    height: int
    tiles: List[int]  # Tile indices
    properties: Dict[str, any]

@dataclass
class ImportedTilemap:
    width: int
    height: int
    tile_width: int
    tile_height: int
    layers: List[TilemapLayer]
    tileset_path: Optional[Path]

class TiledImporter:
    """
    Import tilemaps from Tiled TMX/JSON format.

    Uses PyTMX for robust parsing of Tiled's format.
    """

    def load(self, path: Path) -> ImportedTilemap:
        """Load a Tiled map file (.tmx or .json)."""
        if path.suffix == '.tmx':
            return self._load_tmx(path)
        else:
            return self._load_json(path)

    def _load_tmx(self, path: Path) -> ImportedTilemap:
        """Load TMX format using PyTMX."""
        tiled_map = pytmx.TiledMap(str(path))

        layers = []
        for layer in tiled_map.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                tiles = []
                for y in range(layer.height):
                    for x in range(layer.width):
                        gid = layer.data[y][x]
                        tiles.append(gid if gid else 0)

                layers.append(TilemapLayer(
                    name=layer.name,
                    width=layer.width,
                    height=layer.height,
                    tiles=tiles,
                    properties=dict(layer.properties)
                ))

        return ImportedTilemap(
            width=tiled_map.width,
            height=tiled_map.height,
            tile_width=tiled_map.tilewidth,
            tile_height=tiled_map.tileheight,
            layers=layers,
            tileset_path=None  # Extract from tilesets
        )

    def export_sgdk_map(self, tilemap: ImportedTilemap,
                        output_path: Path,
                        layer_name: str = None) -> None:
        """Export tilemap layer to SGDK MAP format."""
        layer = tilemap.layers[0]
        if layer_name:
            layer = next(l for l in tilemap.layers if l.name == layer_name)

        # Generate C header with map data
        lines = [
            f"// Auto-generated from Tiled map",
            f"// Layer: {layer.name}",
            f"#define MAP_{layer.name.upper()}_WIDTH  {layer.width}",
            f"#define MAP_{layer.name.upper()}_HEIGHT {layer.height}",
            f"",
            f"const u16 map_{layer.name.lower()}[] = {{"
        ]

        for y in range(layer.height):
            row_start = y * layer.width
            row_tiles = layer.tiles[row_start:row_start + layer.width]
            row_str = ", ".join(f"0x{t:04X}" for t in row_tiles)
            lines.append(f"    {row_str},")

        lines.append("};")

        with open(output_path, 'w') as f:
            f.write('\n'.join(lines))


class LDtkImporter:
    """
    Import tilemaps from LDtk JSON format.

    LDtk uses a simple JSON structure - no external library needed.
    See: https://ldtk.io/json/
    """

    def load(self, path: Path) -> ImportedTilemap:
        """Load LDtk project file."""
        with open(path) as f:
            data = json.load(f)

        # LDtk has levels containing layers
        level = data["levels"][0]  # First level
        layers = []

        for layer_data in level.get("layerInstances", []):
            if layer_data["__type"] == "Tiles":
                tiles = [0] * (layer_data["__cWid"] * layer_data["__cHei"])

                for tile in layer_data.get("gridTiles", []):
                    px = tile["px"]
                    grid_x = px[0] // layer_data["__gridSize"]
                    grid_y = px[1] // layer_data["__gridSize"]
                    idx = grid_y * layer_data["__cWid"] + grid_x
                    tiles[idx] = tile["t"]  # Tile ID

                layers.append(TilemapLayer(
                    name=layer_data["__identifier"],
                    width=layer_data["__cWid"],
                    height=layer_data["__cHei"],
                    tiles=tiles,
                    properties={}
                ))

        return ImportedTilemap(
            width=level["pxWid"] // data["defaultGridSize"],
            height=level["pxHei"] // data["defaultGridSize"],
            tile_width=data["defaultGridSize"],
            tile_height=data["defaultGridSize"],
            layers=layers,
            tileset_path=None
        )
```

**CLI:** `--import-tiled FILE.tmx`, `--import-ldtk FILE.ldtk`, `--map-layer NAME`

---

### 2.7 Audio Pipeline Tools

**File:** `tools/pipeline/audio/vgm_tools.py` (NEW)

**Purpose:** Complete audio pipeline from tracker/MIDI to SGDK-ready XGM format.

**Tools Chain:**
1. [Furnace Tracker](https://github.com/tildearrow/furnace) - Open source multi-system tracker (replaces DefleMask)
2. [xgmtool](https://github.com/Stephane-D/SGDK/tree/master/tools/xgmtool) - SGDK's VGM→XGM converter
3. WOPN bank parser - FM instrument definitions

**Features:**
- Wrap xgmtool for VGM→XGM conversion
- Parse WOPN banks for FM patch management
- Validate audio against Genesis hardware limits
- Batch convert music library

```python
import subprocess
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass

@dataclass
class XGMConversionResult:
    success: bool
    output_path: Optional[Path]
    warnings: List[str]
    pcm_channels: int
    fm_channels: int

class XGMToolWrapper:
    """
    Wrapper for SGDK's xgmtool VGM→XGM converter.

    xgmtool is part of SGDK and must be in PATH or specified.
    """

    def __init__(self, xgmtool_path: Optional[str] = None):
        self.exe = xgmtool_path or "xgmtool"

    def convert_vgm_to_xgm(self,
                           vgm_path: Path,
                           output_path: Optional[Path] = None,
                           *,
                           optimize: bool = True,
                           timing: str = "ntsc") -> XGMConversionResult:
        """
        Convert VGM file to XGM format for SGDK.

        Args:
            vgm_path: Input VGM file (must be Genesis/Mega Drive VGM)
            output_path: Output XGM path (default: same name with .xgm)
            optimize: Run VGM optimization pass
            timing: "ntsc" (60Hz) or "pal" (50Hz)

        Returns:
            XGMConversionResult with status and metadata
        """
        if output_path is None:
            output_path = vgm_path.with_suffix('.xgm')

        cmd = [self.exe, str(vgm_path), str(output_path)]

        if optimize:
            cmd.append("-o")  # Optimize

        if timing == "pal":
            cmd.append("-p")  # PAL timing

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            warnings = [line for line in result.stderr.split('\n')
                        if 'warning' in line.lower()]

            return XGMConversionResult(
                success=True,
                output_path=output_path,
                warnings=warnings,
                pcm_channels=4,  # XGM supports up to 4 PCM
                fm_channels=6   # YM2612 has 6 FM channels
            )

        except subprocess.CalledProcessError as e:
            return XGMConversionResult(
                success=False,
                output_path=None,
                warnings=[e.stderr],
                pcm_channels=0,
                fm_channels=0
            )

    def validate_vgm(self, vgm_path: Path) -> List[str]:
        """
        Validate VGM file for Genesis compatibility.

        Checks:
        - VGM version (must be 1.50+)
        - Chip type (YM2612 + SN76489)
        - Frame timing (sub-frame may fail conversion)
        """
        warnings = []

        # Read VGM header
        with open(vgm_path, 'rb') as f:
            header = f.read(64)

        if header[:4] != b'Vgm ':
            warnings.append("Not a valid VGM file")
            return warnings

        version = int.from_bytes(header[8:12], 'little')
        if version < 0x150:
            warnings.append(f"VGM version 0x{version:03X} < 1.50, may not convert")

        ym2612_clock = int.from_bytes(header[44:48], 'little')
        if ym2612_clock == 0:
            warnings.append("No YM2612 chip data - not a Genesis VGM")

        return warnings


@dataclass
class WOPNPatch:
    """FM instrument patch from WOPN bank."""
    name: str
    algorithm: int
    feedback: int
    operators: List[dict]  # 4 operators with TL, AR, DR, etc.


class WOPNParser:
    """
    Parse WOPN instrument bank files for FM patch management.

    WOPN is the format used by OPN2BankEditor and other FM tools.
    """

    def load(self, path: Path) -> List[WOPNPatch]:
        """Load WOPN bank and return list of patches."""
        patches = []

        with open(path, 'rb') as f:
            magic = f.read(11)
            if magic != b'WOPN2-BANK\x00':
                raise ValueError("Not a valid WOPN bank file")

            version = int.from_bytes(f.read(2), 'little')
            num_melodic = int.from_bytes(f.read(2), 'little')
            num_drums = int.from_bytes(f.read(2), 'little')

            # Read melodic patches
            for i in range(num_melodic * 128):
                patch_data = f.read(66)  # WOPN patch size
                if len(patch_data) < 66:
                    break

                name = patch_data[:32].decode('ascii', errors='ignore').strip('\x00')
                # Parse algorithm, feedback, operators...
                patches.append(WOPNPatch(
                    name=name or f"Patch_{i}",
                    algorithm=patch_data[34] & 0x07,
                    feedback=(patch_data[34] >> 3) & 0x07,
                    operators=[]  # Full parsing would extract op data
                ))

        return patches
```

**CLI:** `--convert-vgm FILE.vgm`, `--validate-vgm`, `--wopn-bank FILE.wopn`

**Recommended Workflow:**
1. Compose in [Furnace Tracker](https://github.com/tildearrow/furnace) (free, open source)
2. Export as VGM
3. Convert with `--convert-vgm`
4. Include in SGDK project via .res file

---

### 2.8 Genesis Compression

**File:** `tools/pipeline/compression/genesis_compress.py` (NEW)

**Purpose:** Compress tile/sprite data using Genesis-compatible algorithms for smaller ROMs.

**Dependencies:**
```bash
# clownlzss - optimal graph-based LZSS (build from source or use binaries)
git clone https://github.com/Clownacy/clownlzss
```

**Formats Supported:**
- [clownlzss](https://github.com/Clownacy/clownlzss) - Optimal graph-based LZSS variants
- [Kosinski](https://github.com/Clownacy/accurate-kosinski) - Sega's original format (Sonic 1/2)
- Nemesis - Entropy-based (best for repetitive patterns)
- LZSS - Generic variant

**Features:**
- Wrap clownlzss for optimal compression
- Support Kosinski for Sonic-style ROM hacking
- Automatic format selection based on data characteristics
- Decompression routines for SGDK

```python
import subprocess
from pathlib import Path
from typing import Optional, Literal
from dataclasses import dataclass
from enum import Enum

class CompressionFormat(Enum):
    KOSINSKI = "kosinski"
    NEMESIS = "nemesis"
    LZSS = "lzss"
    UNCOMPRESSED = "none"

@dataclass
class CompressionResult:
    success: bool
    input_size: int
    output_size: int
    ratio: float  # Compression ratio (smaller = better)
    format: CompressionFormat
    output_path: Optional[Path]

class GenesisCompressor:
    """
    Compress tile data using Genesis-compatible algorithms.

    Uses clownlzss for optimal LZSS compression via graph theory.
    """

    def __init__(self,
                 clownlzss_path: Optional[str] = None,
                 kosinski_path: Optional[str] = None):
        self.clownlzss = clownlzss_path or "clownlzss"
        self.kosinski = kosinski_path or "kosinski"

    def compress(self,
                 input_path: Path,
                 output_path: Optional[Path] = None,
                 format: CompressionFormat = CompressionFormat.KOSINSKI
                 ) -> CompressionResult:
        """
        Compress binary data using specified format.

        Args:
            input_path: Input binary file (raw tile data)
            output_path: Output path (default: input + format extension)
            format: Compression format to use

        Returns:
            CompressionResult with sizes and ratio
        """
        input_size = input_path.stat().st_size

        if format == CompressionFormat.UNCOMPRESSED:
            return CompressionResult(
                success=True,
                input_size=input_size,
                output_size=input_size,
                ratio=1.0,
                format=format,
                output_path=input_path
            )

        if output_path is None:
            output_path = input_path.with_suffix(f'.{format.value}')

        try:
            if format == CompressionFormat.KOSINSKI:
                cmd = [self.kosinski, "-c", str(input_path), str(output_path)]
            elif format == CompressionFormat.LZSS:
                cmd = [self.clownlzss, "-c", "rocket",
                       str(input_path), str(output_path)]
            else:
                raise ValueError(f"Unsupported format: {format}")

            subprocess.run(cmd, check=True, capture_output=True)

            output_size = output_path.stat().st_size
            return CompressionResult(
                success=True,
                input_size=input_size,
                output_size=output_size,
                ratio=output_size / input_size,
                format=format,
                output_path=output_path
            )

        except subprocess.CalledProcessError as e:
            return CompressionResult(
                success=False,
                input_size=input_size,
                output_size=0,
                ratio=1.0,
                format=format,
                output_path=None
            )

    def auto_select_format(self, data: bytes) -> CompressionFormat:
        """
        Analyze data and recommend best compression format.

        - Kosinski: Good general-purpose, fast decompression
        - Nemesis: Best for highly repetitive data (solid colors)
        - LZSS: Balanced size/speed
        """
        # Count runs of identical bytes
        runs = 0
        current_run = 1
        for i in range(1, len(data)):
            if data[i] == data[i-1]:
                current_run += 1
            else:
                if current_run > 4:
                    runs += 1
                current_run = 1

        # High run count = repetitive = Nemesis excels
        if runs > len(data) // 32:
            return CompressionFormat.NEMESIS

        # Default to Kosinski (good balance)
        return CompressionFormat.KOSINSKI

    def generate_decompressor_header(self,
                                     format: CompressionFormat) -> str:
        """Generate SGDK-compatible decompression function declarations."""
        if format == CompressionFormat.KOSINSKI:
            return '''
// Kosinski decompression (from SGDK or custom)
void Kos_Decompress(const u8* src, u8* dst);
'''
        elif format == CompressionFormat.NEMESIS:
            return '''
// Nemesis decompression
void Nem_Decompress(const u8* src, u8* dst);
'''
        else:
            return "// No decompression needed for uncompressed data"
```

**CLI:** `--compress [kosinski|nemesis|lzss|auto]`, `--decompress`

**Expected Savings:**
- Tile data: 30-60% reduction with Kosinski
- Repetitive patterns: 50-80% with Nemesis
- Mixed content: 20-40% with LZSS

### Phase 2 Quality Gates

- [x] **Tests**: `test_sgdk_resources.py`, `test_performance.py`
- [x] **Docs**: Docstrings for SGDKResourceGenerator, PerformanceBudgetCalculator
- [x] **USAGE.md**: SGDK Resources, Performance, Maps, Audio modules documented
- [ ] **USAGE.md**: Tiled import, VGM tools, Compression (when implemented)
- [x] **Types**: Type hints on all resource/export functions
- [x] **CLI**: `--generate-res`, `--performance-report` documented
- [x] **Integration**: Generated .res files compile with rescomp
- [ ] **Review**: Audit VDP export and assembly format code when implemented

**Remaining for Phase 2:**

- [ ] VDP-Ready Export (2.2) - SAT entries, CRAM palettes
- [ ] Assembly Export Formats (2.4) - ca65, asm68k, wla-dx
- [ ] Tile Cache System (2.5) - Hash-based caching
- [ ] `tilemap/tiled_import.py` (2.6) - PyTMX/LDtk import
- [ ] `audio/vgm_tools.py` (2.7) - xgmtool wrapper, WOPN parser
- [x] `compression/genesis_compress.py` (2.8) - Kosinski/LZSS compression ✅

---

## Phase 3: AI-Powered Features

**Goal:** Leverage AI for complex sprite generation and transformation.

**Dependencies:** Phase 1-2 complete, AI providers configured

### 3.1 AI Animation Generation ✅

**Enhancement to:** `tools/pipeline/ai.py`

**Purpose:** Generate animation frames from a single sprite.

**Methods:**
- PixelLab `animate` endpoint (primary)
- Pollinations img2img interpolation (fallback)

**Actions:** `idle`, `walk`, `attack`, `jump`, `death`

**CLI:** `--animate [idle|walk|attack|jump|death]`

---

### 3.2 AI Upscaling + Requantize ✅

**Purpose:** Upscale sprites while maintaining platform constraints.

**Methods:**
- Real-ESRGAN (local, open-source)
- Pollinations upscale (fallback)
- Re-quantize to target palette

**CLI:** `--upscale [2x|4x]`

---

### 3.3 Background Removal ✅

**Purpose:** Remove backgrounds from reference images.

**Methods:**
- rembg library (local)
- AI fallback
- Auto alpha→magenta conversion

**CLI:** `--remove-bg [auto|color:hex|ai]`

---

### 3.4 Tileset Generation ✅

**Purpose:** Generate coherent tilesets from prompts.

**Features:**
- Auto-tile compatible layout
- Collision metadata per tile
- Style consistency

**CLI:** `--tileset --style [grass|stone|metal|organic]`

---

### 3.5 Style Transfer System ✅

**Already implemented in:** `tools/pipeline/style.py`

**Features:**
- `StyleProfile` - Portable style definitions
- `StyleManager` - Capture/apply across providers
- Provider-specific adapters

---

### 3.6 Alternative AI Providers ✅

**File:** `tools/pipeline/ai_providers/` (NEW directory)

**Purpose:** Expand AI provider options beyond PixelLab/Pollinations for redundancy and specialized capabilities.

**New Providers:**

| Provider | Strength | Use Case |
|----------|----------|----------|
| [Pixie.haus](https://pixie.haus/) | Pixel-perfect pipelines | Built-in quantization, scaling |
| [PixAI/AIPixelKit](https://www.pixapt.com/) | Platform palettes | NES/GB/SNES/Genesis presets |
| Stable Diffusion (local) | Customizable, no API cost | Fine-tuned for specific style |

**File:** `tools/pipeline/ai_providers/pixie_haus.py` (NEW)

```python
from dataclasses import dataclass
from typing import Optional, List
import httpx

@dataclass
class PixieHausConfig:
    """Configuration for Pixie.haus API."""
    api_key: str
    base_url: str = "https://api.pixie.haus/v1"

class PixieHausProvider:
    """
    Pixie.haus AI provider for pixel-perfect sprite generation.

    Features:
    - Built-in color palette quantization
    - Nearest-neighbor scaling
    - Background removal tailored for games
    """

    def __init__(self, config: PixieHausConfig):
        self.config = config
        self.client = httpx.Client(
            base_url=config.base_url,
            headers={"Authorization": f"Bearer {config.api_key}"}
        )

    def generate_sprite(self,
                        prompt: str,
                        *,
                        width: int = 32,
                        height: int = 32,
                        palette: str = "genesis",
                        max_colors: int = 16) -> bytes:
        """
        Generate a sprite with platform-specific constraints.

        Args:
            prompt: Description of sprite to generate
            width: Output width in pixels
            height: Output height in pixels
            palette: "genesis" | "nes" | "snes" | "gameboy"
            max_colors: Maximum colors (Genesis = 16)

        Returns:
            PNG image bytes
        """
        response = self.client.post("/generate", json={
            "prompt": prompt,
            "width": width,
            "height": height,
            "palette_mode": palette,
            "max_colors": max_colors,
            "pixel_perfect": True
        })
        response.raise_for_status()
        return response.content
```

**File:** `tools/pipeline/ai_providers/stable_diffusion.py` (NEW)

```python
from pathlib import Path
from typing import Optional
import subprocess

class StableDiffusionLocal:
    """
    Local Stable Diffusion for cost-free, customizable generation.

    Requires:
    - stable-diffusion-webui or ComfyUI running locally
    - Fine-tuned checkpoint for pixel art (recommended)
    """

    def __init__(self,
                 api_url: str = "http://127.0.0.1:7860",
                 checkpoint: Optional[str] = None):
        self.api_url = api_url
        self.checkpoint = checkpoint

    def generate(self,
                 prompt: str,
                 *,
                 width: int = 512,
                 height: int = 512,
                 steps: int = 20,
                 cfg_scale: float = 7.0,
                 negative_prompt: str = "blurry, realistic, photo") -> bytes:
        """
        Generate image via local Stable Diffusion API.

        Args:
            prompt: Generation prompt (add "pixel art" for best results)
            width: Output width (will be downscaled after)
            height: Output height
            steps: Sampling steps
            cfg_scale: Classifier-free guidance scale
            negative_prompt: Things to avoid

        Returns:
            PNG image bytes
        """
        import httpx

        # Add pixel art styling to prompt
        styled_prompt = f"pixel art, {prompt}, 16-bit, retro game sprite"

        response = httpx.post(f"{self.api_url}/sdapi/v1/txt2img", json={
            "prompt": styled_prompt,
            "negative_prompt": negative_prompt,
            "width": width,
            "height": height,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "sampler_name": "DPM++ 2M Karras"
        })
        response.raise_for_status()

        import base64
        data = response.json()
        return base64.b64decode(data["images"][0])

    def is_available(self) -> bool:
        """Check if local SD instance is running."""
        try:
            import httpx
            response = httpx.get(f"{self.api_url}/sdapi/v1/sd-models", timeout=2.0)
            return response.status_code == 200
        except Exception:
            return False
```

**Enhanced Fallback Chain:**

```python
# In ai.py - Updated fallback order
PROVIDER_PRIORITY = [
    "pixellab",        # Primary: exact dimensions, 4bpp native
    "pixie_haus",      # Secondary: pixel-perfect pipelines
    "stable_diffusion", # Tertiary: local, free, customizable
    "pollinations",    # Fallback: free but less control
]

def get_available_provider():
    """Return first available provider from priority list."""
    for provider_name in PROVIDER_PRIORITY:
        provider = get_provider(provider_name)
        if provider and provider.is_available():
            return provider
    raise NoProvidersAvailableError("No AI providers configured or available")
```

**CLI:** `--ai-provider [pixellab|pixie|sd-local|pollinations|auto]`

### Phase 3 Quality Gates

- [ ] **Tests**: `test_ai.py` with mocked API responses, `test_style.py`
- [ ] **Docs**: Docstrings for all AI generation functions
- [ ] **USAGE.md**: AI generation, upscaling, style transfer documented
- [ ] **Types**: Type hints on all AI interfaces, Result types for fallbacks
- [ ] **CLI**: `--animate`, `--upscale`, `--remove-bg`, `--tileset` documented
- [ ] **Integration**: Fallback chain tested (PixelLab → Pollinations → local)
- [ ] **Review**: API key handling secure, no keys in logs

**Phase 3 Tasks:**

- [x] AI Animation Generation (3.1) - Generate walk/attack from single frame ✅
- [x] AI Upscaling (3.2) - Upscale + requantize to platform limits ✅
- [x] Background Removal (3.3) - rembg integration ✅
- [x] Tileset Generation (3.4) - Coherent tile sets from prompts ✅
- [x] Style Transfer System (3.5) - Already in `style.py`
- [x] `ai_providers/pixie_haus.py` (3.6) - Pixie.haus integration ✅
- [x] `ai_providers/stable_diffusion.py` (3.6) - Local SD integration ✅
- [x] Enhanced fallback chain in `ai_providers/registry.py` (3.6) ✅

---

## Phase 4: Advanced Tools

**Goal:** Sophisticated tooling for complex game development needs.

**Dependencies:** Phase 1-3 complete

### 4.1 Animation State Machine Generator ✅

**File:** `tools/pipeline/animation_fsm.py` ✅ IMPLEMENTED

**Purpose:** Generate SGDK-ready animation state machine code from YAML definitions.

**Input Format (YAML):**
```yaml
states:
  idle:
    animation: anim_idle
    transitions:
      move: walk
      attack: attack
      hit: hurt

  walk:
    animation: anim_walk
    transitions:
      stop: idle
      attack: attack

  attack:
    animation: anim_attack
    on_frame: attack_hitbox_check
    transitions:
      done: idle
```

**Output (C):**
```c
typedef enum {
    ANIM_STATE_IDLE,
    ANIM_STATE_WALK,
    ANIM_STATE_ATTACK,
    ANIM_STATE_COUNT
} AnimState;

typedef enum {
    ANIM_EVENT_MOVE,
    ANIM_EVENT_STOP,
    ANIM_EVENT_ATTACK,
    ANIM_EVENT_COUNT
} AnimEvent;

const s8 anim_transitions[ANIM_STATE_COUNT][ANIM_EVENT_COUNT] = {
    { ANIM_STATE_WALK, -1, ANIM_STATE_ATTACK },  // IDLE
    { -1, ANIM_STATE_IDLE, ANIM_STATE_ATTACK },  // WALK
    { -1, -1, -1 },                               // ATTACK (done→idle via callback)
};
```

**CLI:** `--generate-fsm input.yaml`

---

### 4.2 Collision Visualization / Editor ✅

**File:** `tools/pipeline/collision_editor.py` ✅ IMPLEMENTED

**Purpose:** Preview and edit collision boxes visually.

**Features:**
- Render overlay with hitbox/hurtbox
- Generate animated GIF with collision boxes
- TKinter-based interactive editor
- Export updated collision JSON

**CLI:** `--collision-editor`, `--collision-overlay`, `--export-gif`

---

### 4.3 Cross-Platform Variants ✅

**File:** `tools/pipeline/cross_platform.py` ✅ IMPLEMENTED

**Purpose:** Generate platform-specific versions from high-res source.

**Conversions:**
- Genesis (32x32, 16 colors) → NES (16x16, 4 colors)
- Genesis → Game Boy (4 colors, grayscale)
- Genesis → SNES (16 colors, 64x64 max)

**CLI:** `--also-export [nes|gameboy|snes]`

---

### 4.4 Scene Composition

**File:** `tools/pipeline/scene_composer.py` (NEW)

**Purpose:** Compose multiple sprites into scenes for testing, preview mockups, and promotional screenshots.

**Features:**

- Layer multiple sprites with Z-ordering
- Position sprites on a Genesis-resolution canvas (320x224 or 256x224)
- Preview with background tile layer support
- Apply palette constraints (max 4 palettes, 15 colors each)
- Export as screenshot (PNG) or animated GIF
- JSON scene definition format for reproducible compositions

**Scene Definition (JSON):**
```json
{
  "canvas": { "width": 320, "height": 224 },
  "background": "bg_forest.png",
  "layers": [
    {
      "sprite": "player_idle.png",
      "position": { "x": 160, "y": 112 },
      "z_order": 10,
      "palette_index": 0
    },
    {
      "sprite": "enemy_grunt.png",
      "position": { "x": 80, "y": 120 },
      "z_order": 5,
      "palette_index": 1,
      "flip_h": true
    },
    {
      "sprite": "projectile.png",
      "position": { "x": 120, "y": 115 },
      "z_order": 15,
      "palette_index": 0
    }
  ]
}
```

**Class Interface:**

```python
@dataclass
class SceneLayer:
    """A single sprite layer in a scene composition."""
    sprite_path: Path
    position: tuple[int, int]
    z_order: int = 0
    palette_index: int = 0
    flip_h: bool = False
    flip_v: bool = False
    animation_frames: Optional[list[Path]] = None

@dataclass
class SceneComposition:
    """A complete scene with multiple layers."""
    canvas_size: tuple[int, int]
    background: Optional[Path]
    layers: list[SceneLayer]

class SceneComposer:
    """Compose sprites into preview scenes."""

    def __init__(self, palette_manager: Optional[PaletteManager] = None):
        """Initialize with optional shared palette manager."""
        pass

    def load_scene(self, scene_path: Path) -> SceneComposition:
        """Load scene definition from JSON file."""
        pass

    def render(self, scene: SceneComposition,
               *, scale: int = 1, show_grid: bool = False) -> Image.Image:
        """Render scene to PIL Image."""
        pass

    def render_animated(self, scene: SceneComposition,
                        *, fps: int = 12, duration_ms: int = 2000) -> list[Image.Image]:
        """Render animated scene with sprite animations."""
        pass

    def export_png(self, scene: SceneComposition, output_path: Path,
                   *, scale: int = 2) -> Path:
        """Export scene as PNG screenshot."""
        pass

    def export_gif(self, scene: SceneComposition, output_path: Path,
                   *, fps: int = 12, loop: bool = True) -> Path:
        """Export animated scene as GIF."""
        pass

    def validate_scene(self, scene: SceneComposition) -> list[str]:
        """Validate scene against Genesis hardware limits."""
        pass
```

**CLI:**

```bash
# Render scene to PNG
python unified_pipeline.py --compose-scene scene.json --output screenshot.png

# Render with 2x scaling for promotional use
python unified_pipeline.py --compose-scene scene.json --scale 2 --output promo.png

# Render animated scene to GIF
python unified_pipeline.py --compose-scene scene.json --animated --fps 12 --output preview.gif

# Show grid overlay for alignment
python unified_pipeline.py --compose-scene scene.json --show-grid --output debug.png
```

---

### Phase 4 Quality Gates ✅

- [x] **Tests**: `test_animation_fsm.py`, `test_collision_editor.py`, `test_cross_platform.py`
- [x] **Docs**: Docstrings for FSM generator, collision editor, platform converters
- [x] **USAGE.md**: FSM, Collision, Cross-Platform modules documented
- [ ] **USAGE.md**: Scene Composition (when implemented)
- [x] **Types**: Type hints on YAML parsing, collision data structures
- [x] **CLI**: `--generate-fsm`, `--collision-editor`, `--also-export` documented
- [x] **Integration**: FSM output compiles with SGDK, collision JSON loads correctly
- [ ] **Review**: Scene composition code when implemented

**Remaining for Phase 4:**

- [ ] Scene Composition (4.4) - Multi-sprite scene preview

---

## Phase 5: Hardening

**Goal:** Production-ready error handling, validation, and security.

**Dependencies:** All feature phases complete

### 5.1 Error Handling ✅

**File:** `tools/pipeline/errors.py` (NEW)

**Purpose:** Comprehensive error handling with clear messages.

```python
class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass

class ImageLoadError(PipelineError):
    """Failed to load or validate image."""
    pass

class APIError(PipelineError):
    """API call failed."""
    pass

class ValidationError(PipelineError):
    """Input/output validation failed."""
    pass

def safe_image_open(path: str, convert_to: str = 'RGBA') -> Image.Image:
    """Safely open an image with error handling."""
    pass
```

**Fixes:**
- Wrap all `Image.open()` calls
- Catch API timeouts
- Handle disk space errors
- Log all exceptions with context

---

### 5.2 Input Validation ✅

**Purpose:** Validate all inputs before processing.

**Checks:**
- File exists and readable
- Image format supported
- Dimensions within limits
- Color count within platform limits
- Path traversal prevention

---

### 5.3 Resource Management ✅

**Purpose:** Proper cleanup and memory management.

**Features:**
- Context managers for file handles
- Memory limits for large images
- Temp file cleanup
- Connection pooling for APIs

---

### 5.4 API Reliability (⏭️ Skipped)

**Purpose:** Robust API interaction.

**Features:**
- Exponential backoff retry
- Rate limiting
- Timeout handling
- Fallback chain

---

### 5.5 Security Hardening ✅

**Purpose:** Prevent security issues.

**Features:**
- Path traversal prevention
- API key protection
- Input sanitization
- Output filename sanitization

---

### 5.6 Logging & Metrics ✅

**Purpose:** Comprehensive observability.

**Features:**
- Structured logging
- Processing time metrics
- API call tracking
- Cost estimation
- Validation statistics

**CLI:** `--verbose`, `--metrics`

### Phase 5 Quality Gates

- [ ] **Tests**: `test_errors.py`, `test_validation.py`, integration tests with invalid inputs
- [ ] **Docs**: Error messages include actionable fix suggestions
- [ ] **USAGE.md**: Troubleshooting section expanded, error codes documented
- [ ] **Types**: Custom exception hierarchy with typed error data
- [ ] **CLI**: `--verbose`, `--metrics`, `--validate-only` documented
- [ ] **Integration**: All modules use centralized error handling
- [ ] **Review**: Security audit complete, no path traversal or injection vulnerabilities

**Phase 5 Tasks:**

- [ ] Error Handling (5.1) - `errors.py` with exception hierarchy
- [ ] Input Validation (5.2) - Pre-flight checks for all inputs
- [ ] Resource Management (5.3) - Context managers, memory limits
- [ ] API Reliability (5.4) - Retry logic, rate limiting, fallbacks
- [ ] Security Hardening (5.5) - Path traversal, input sanitization
- [ ] Logging & Metrics (5.6) - Structured logging, cost tracking

---

## Phase 6: Production Optimization & Expansion

**Goal:** Optimize performance, expand tooling ecosystem, and improve artist workflows.

**Dependencies:** Phase 1-5 complete (foundation in place)

**Strategy:** Build on existing functionality rather than creating parallel systems. Each sub-phase includes refactoring, testing, and documentation.

---

## Phase 6.1: Optimization & Performance

**Goal:** Maximize efficiency for resource-constrained retro hardware (Genesis VRAM, ROM size).

**Dependencies:** Phase 2 (SGDK), Phase 5 (hardening)

**Timeline:** 2-3 weeks

### 6.1.1 Advanced Sprite Packing

**File:** `tools/pipeline/optimization/sprite_packer.py` (NEW)

**Purpose:** Automatic sprite atlas generation with optimal rectangle packing.

**Why Critical:** Genesis VRAM is 64KB. Smart packing saves 20-30% space.

**Dependencies:**
```bash
pip install rectpack
```

**Implementation:**

```python
from rectpack import newPacker
from typing import List, Dict, Tuple
from PIL import Image
from dataclasses import dataclass

@dataclass
class PackedSprite:
    """A sprite with its position in the atlas."""
    name: str
    image: Image.Image
    x: int
    y: int
    width: int
    height: int
    rotated: bool = False

class SpriteAtlasGenerator:
    """
    Generate optimized sprite atlases with multiple packing algorithms.

    Features:
    - Multiple bin packing algorithms (MaxRects, Guillotine, Skyline)
    - Rotation support (90° for better packing)
    - Padding control (prevent tile bleeding)
    - Power-of-2 sizing (GPU-friendly)
    """

    ALGORITHMS = ['MaxRects', 'Guillotine', 'Skyline']

    def __init__(self,
                 max_width: int = 512,
                 max_height: int = 512,
                 padding: int = 2,
                 power_of_2: bool = True,
                 allow_rotation: bool = True):
        """
        Initialize atlas generator.

        Args:
            max_width: Maximum atlas width
            max_height: Maximum atlas height
            padding: Pixels between sprites (prevents bleeding)
            power_of_2: Force power-of-2 dimensions
            allow_rotation: Allow 90° rotation for better packing
        """
        self.max_width = max_width
        self.max_height = max_height
        self.padding = padding
        self.power_of_2 = power_of_2
        self.allow_rotation = allow_rotation

    def pack(self, sprites: Dict[str, Image.Image]) -> List[PackedSprite]:
        """
        Pack sprites into optimal atlas layout.

        Returns:
            List of PackedSprite with positions
        """
        # Try all algorithms, pick best
        best_result = None
        best_area = float('inf')

        for algo in self.ALGORITHMS:
            result = self._pack_with_algorithm(sprites, algo)
            area = result['width'] * result['height']

            if area < best_area:
                best_area = area
                best_result = result

        return best_result['sprites']

    def generate_atlas(self, sprites: Dict[str, Image.Image]) -> Tuple[Image.Image, Dict]:
        """
        Generate final atlas image and metadata.

        Returns:
            (atlas_image, metadata_dict)
        """
        packed = self.pack(sprites)

        # Calculate final dimensions
        max_x = max(s.x + s.width for s in packed)
        max_y = max(s.y + s.height for s in packed)

        if self.power_of_2:
            max_x = self._next_power_of_2(max_x)
            max_y = self._next_power_of_2(max_y)

        # Create atlas
        atlas = Image.new('RGBA', (max_x, max_y), (0, 0, 0, 0))

        metadata = {
            'width': max_x,
            'height': max_y,
            'sprites': {}
        }

        for sprite in packed:
            img = sprite.image
            if sprite.rotated:
                img = img.rotate(90, expand=True)

            atlas.paste(img, (sprite.x, sprite.y))

            metadata['sprites'][sprite.name] = {
                'x': sprite.x,
                'y': sprite.y,
                'width': sprite.width,
                'height': sprite.height,
                'rotated': sprite.rotated
            }

        return atlas, metadata

    def _pack_with_algorithm(self, sprites, algo):
        """Pack sprites using specific algorithm."""
        # Implementation uses rectpack library
        pass

    def _next_power_of_2(self, n: int) -> int:
        """Round up to next power of 2."""
        power = 1
        while power < n:
            power *= 2
        return power

def pack_sprite_directory(input_dir: str, output_path: str,
                         metadata_path: str = None):
    """
    Convenience function to pack all sprites in a directory.

    Usage:
        >>> pack_sprite_directory("sprites/characters", "atlas.png")
    """
    packer = SpriteAtlasGenerator()

    # Load all sprites
    sprites = {}
    for file in Path(input_dir).glob("*.png"):
        sprites[file.stem] = Image.open(file)

    # Generate atlas
    atlas, metadata = packer.generate_atlas(sprites)

    # Save
    atlas.save(output_path)
    if metadata_path:
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
```

**CLI:** `--pack-sprites DIR --output atlas.png --metadata atlas.json`

**Integration:** Export metadata in SGDK .res format

---

### 6.1.2 Advanced Compression Ecosystem

**File:** `tools/pipeline/compression/retro_compress.py` (NEW)

**Purpose:** Multi-algorithm compression with Genesis/NES-optimized codecs.

**Why:** Genesis standard is Exomizer. Current basic compression is suboptimal.

**Algorithms to add:**

| Algorithm | Best For | Ratio | Speed | Genesis Support |
|-----------|----------|-------|-------|-----------------|
| **Exomizer** | 68000 code | Excellent | Slow compress | Native asm decompressor |
| **ZX0** | Tile data | Great | Fast decompress | Available |
| **ZX7** | Mixed data | Good | Very fast | Available |
| **apultra** | Large assets | Excellent | Fastest decompress | Available |
| **LZ4** | Real-time | Fast | Very fast | Custom |

**Dependencies:**
```bash
# Install external tools
# Exomizer: https://bitbucket.org/magli143/exomizer/wiki/Home
# ZX0: https://github.com/einar-saukas/ZX0
# apultra: https://github.com/emmanuel-marty/apultra
```

**Implementation:**

```python
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, Tuple
from dataclasses import dataclass

@dataclass
class CompressionResult:
    """Result of compression operation."""
    original_size: int
    compressed_size: int
    ratio: float
    algorithm: str
    compressed_data: bytes
    decompress_cycles: Optional[int] = None  # 68000 cycles if known

class RetroCompressor:
    """
    Multi-algorithm compression with retro-optimized codecs.

    Automatically selects best algorithm based on:
    - Data type (code, tiles, audio, level data)
    - Target platform (Genesis, NES, SNES)
    - Size vs. speed tradeoff
    """

    # External tool paths (configure once)
    TOOLS = {
        'exomizer': 'exomizer',
        'zx0': 'zx0',
        'zx7': 'zx7',
        'apultra': 'apultra',
    }

    def __init__(self, platform: str = 'genesis'):
        """
        Initialize compressor for target platform.

        Args:
            platform: 'genesis' | 'nes' | 'snes' | 'gameboy'
        """
        self.platform = platform
        self._verify_tools()

    def compress_auto(self, data: bytes,
                     data_type: str = 'auto') -> CompressionResult:
        """
        Automatically select best compression algorithm.

        Args:
            data: Data to compress
            data_type: 'code' | 'tiles' | 'audio' | 'level' | 'auto'

        Returns:
            CompressionResult with best algorithm
        """
        # Try all available algorithms
        results = []

        for algo in ['exomizer', 'zx0', 'zx7', 'apultra']:
            if self._is_tool_available(algo):
                try:
                    result = self._compress_with(data, algo)
                    results.append(result)
                except Exception as e:
                    continue

        if not results:
            raise RuntimeError("No compression tools available")

        # Select best based on data type
        if data_type == 'code':
            # Favor Exomizer (best ratio, optimized for 68k)
            return min(results, key=lambda r: r.compressed_size)
        elif data_type == 'tiles':
            # Favor ZX0 (good ratio, fast decompress)
            zx0_results = [r for r in results if r.algorithm == 'zx0']
            return zx0_results[0] if zx0_results else results[0]
        else:
            # Favor best ratio
            return min(results, key=lambda r: r.compressed_size)

    def compress_exomizer(self, data: bytes,
                         level: int = 3) -> CompressionResult:
        """
        Compress with Exomizer (Genesis standard).

        Args:
            level: Compression level 1-9 (higher = better ratio, slower)
        """
        # Write temp file
        temp_in = Path("temp_compress_in.bin")
        temp_out = Path("temp_compress_out.bin")

        try:
            temp_in.write_bytes(data)

            # Run exomizer
            subprocess.run([
                self.TOOLS['exomizer'],
                'raw',
                f'-c{level}',
                str(temp_in),
                '-o', str(temp_out)
            ], check=True, capture_output=True)

            compressed = temp_out.read_bytes()

            return CompressionResult(
                original_size=len(data),
                compressed_size=len(compressed),
                ratio=len(compressed) / len(data),
                algorithm='exomizer',
                compressed_data=compressed
            )

        finally:
            temp_in.unlink(missing_ok=True)
            temp_out.unlink(missing_ok=True)

    def compress_zx0(self, data: bytes) -> CompressionResult:
        """Compress with ZX0 (fast decompress)."""
        # Similar implementation
        pass

    def batch_analyze(self, files: List[Path]) -> Dict[str, CompressionResult]:
        """
        Analyze multiple files and recommend best compression.

        Returns:
            Dict mapping filename to best compression result
        """
        results = {}

        for file_path in files:
            data = file_path.read_bytes()

            # Detect data type from extension
            data_type = self._detect_data_type(file_path)

            # Compress
            result = self.compress_auto(data, data_type)
            results[str(file_path)] = result

        return results

    def generate_report(self, results: Dict[str, CompressionResult]) -> str:
        """Generate human-readable compression report."""
        report = ["Compression Analysis Report", "=" * 60, ""]

        total_original = sum(r.original_size for r in results.values())
        total_compressed = sum(r.compressed_size for r in results.values())

        report.append(f"Total Files: {len(results)}")
        report.append(f"Original Size: {total_original:,} bytes")
        report.append(f"Compressed Size: {total_compressed:,} bytes")
        report.append(f"Total Savings: {total_original - total_compressed:,} bytes ({(1 - total_compressed/total_original)*100:.1f}%)")
        report.append("")
        report.append("Per-File Breakdown:")
        report.append("-" * 60)

        for filename, result in sorted(results.items()):
            report.append(f"{filename}:")
            report.append(f"  Algorithm: {result.algorithm}")
            report.append(f"  Original: {result.original_size:,} bytes")
            report.append(f"  Compressed: {result.compressed_size:,} bytes")
            report.append(f"  Ratio: {result.ratio:.2%}")
            report.append("")

        return "\n".join(report)

    def _compress_with(self, data: bytes, algo: str) -> CompressionResult:
        """Compress with specific algorithm."""
        method = getattr(self, f'compress_{algo}')
        return method(data)

    def _verify_tools(self):
        """Check which compression tools are available."""
        for tool, command in self.TOOLS.items():
            if not shutil.which(command):
                print(f"Warning: {tool} not found in PATH")

    def _is_tool_available(self, tool: str) -> bool:
        """Check if tool is available."""
        return shutil.which(self.TOOLS[tool]) is not None

    def _detect_data_type(self, path: Path) -> str:
        """Detect data type from file extension."""
        suffix = path.suffix.lower()

        if suffix in ['.bin', '.o']:
            return 'code'
        elif suffix in ['.tiles', '.chr']:
            return 'tiles'
        elif suffix in ['.pcm', '.wav']:
            return 'audio'
        elif suffix in ['.map', '.level']:
            return 'level'
        else:
            return 'auto'

# Convenience functions
def compress_file(input_path: str, output_path: str,
                 algorithm: str = 'auto', platform: str = 'genesis'):
    """
    Compress a file with best algorithm.

    Usage:
        >>> compress_file("level1.bin", "level1.exo", algorithm='exomizer')
    """
    compressor = RetroCompressor(platform)
    data = Path(input_path).read_bytes()

    if algorithm == 'auto':
        result = compressor.compress_auto(data)
    else:
        result = compressor._compress_with(data, algorithm)

    Path(output_path).write_bytes(result.compressed_data)

    print(f"Compressed {input_path} -> {output_path}")
    print(f"  Algorithm: {result.algorithm}")
    print(f"  {result.original_size:,} -> {result.compressed_size:,} bytes ({result.ratio:.2%})")
```

**CLI:**
- `--compress FILE --algorithm [auto|exomizer|zx0|zx7|apultra]`
- `--compress-batch DIR --report compression_report.txt`

---

### 6.1.3 Tile Deduplication & Optimization

**File:** `tools/pipeline/optimization/tile_optimizer.py` (EXPAND EXISTING)

**Purpose:** Expand existing basic dedupe with flip detection, palette sharing, and VRAM optimization.

**Status:** ⚠️ Basic logic exists in `processing.py` - EXPAND and extract to dedicated module

**Impact:** Can save 40-50% of Genesis VRAM usage

**Implementation:**

```python
from typing import List, Dict, Set, Tuple
from PIL import Image
import numpy as np
from dataclasses import dataclass
from enum import IntFlag

class TileTransform(IntFlag):
    """Tile transformation flags (matches Genesis VDP)."""
    NORMAL = 0x0000
    HFLIP = 0x0800   # Horizontal flip
    VFLIP = 0x1000   # Vertical flip
    HVFLIP = 0x1800  # Both flips

@dataclass
class TileReference:
    """Reference to a tile in the optimized bank."""
    tile_index: int
    transform: TileTransform
    palette: int = 0

@dataclass
class OptimizedTileBank:
    """Optimized tile bank with deduplication."""
    tiles: List[np.ndarray]  # Unique tiles only
    tile_map: Dict[bytes, TileReference]  # Hash -> reference
    savings_bytes: int
    original_count: int
    optimized_count: int

class TileOptimizer:
    """
    Advanced tile optimization with flip detection and palette sharing.

    Features:
    - Tile deduplication (find identical 8x8 tiles)
    - Flip detection (use H/V flip instead of storing duplicates)
    - Palette remapping (share tiles across sprites)
    - VRAM budget tracking
    """

    TILE_SIZE = 8  # Genesis/NES/SNES standard

    def __init__(self,
                 enable_flip: bool = True,
                 enable_palette_remap: bool = False,
                 tile_size: int = 8):
        """
        Initialize tile optimizer.

        Args:
            enable_flip: Use H/V flip to reduce duplicate tiles
            enable_palette_remap: Allow palette remapping for more savings
            tile_size: Tile size in pixels (8 for Genesis/NES/SNES)
        """
        self.enable_flip = enable_flip
        self.enable_palette_remap = enable_palette_remap
        self.tile_size = tile_size

    def optimize_sprite_sheet(self, image: Image.Image) -> OptimizedTileBank:
        """
        Optimize a sprite sheet by deduplicating tiles.

        Args:
            image: Sprite sheet image

        Returns:
            OptimizedTileBank with deduplicated tiles
        """
        # Extract all tiles
        tiles = self._extract_tiles(image)

        # Build optimized bank
        unique_tiles = []
        tile_map = {}

        for tile in tiles:
            # Check if tile already exists (with transforms)
            ref = self._find_existing_tile(tile, unique_tiles)

            if ref is None:
                # New unique tile
                idx = len(unique_tiles)
                unique_tiles.append(tile)
                tile_map[self._hash_tile(tile)] = TileReference(idx, TileTransform.NORMAL)
            else:
                # Reuse existing tile
                tile_map[self._hash_tile(tile)] = ref

        original_count = len(tiles)
        optimized_count = len(unique_tiles)
        savings = (original_count - optimized_count) * self.tile_size * self.tile_size * 4  # bytes

        return OptimizedTileBank(
            tiles=unique_tiles,
            tile_map=tile_map,
            savings_bytes=savings,
            original_count=original_count,
            optimized_count=optimized_count
        )

    def optimize_batch(self, sprites: List[Image.Image]) -> OptimizedTileBank:
        """
        Optimize multiple sprites together for maximum savings.

        This finds shared tiles across all sprites.
        """
        all_tiles = []

        for sprite in sprites:
            tiles = self._extract_tiles(sprite)
            all_tiles.extend(tiles)

        # Deduplicate across all sprites
        unique_tiles = []
        tile_map = {}

        for tile in all_tiles:
            ref = self._find_existing_tile(tile, unique_tiles)

            if ref is None:
                idx = len(unique_tiles)
                unique_tiles.append(tile)
                tile_map[self._hash_tile(tile)] = TileReference(idx, TileTransform.NORMAL)
            else:
                tile_map[self._hash_tile(tile)] = ref

        savings = (len(all_tiles) - len(unique_tiles)) * self.tile_size * self.tile_size * 4

        return OptimizedTileBank(
            tiles=unique_tiles,
            tile_map=tile_map,
            savings_bytes=savings,
            original_count=len(all_tiles),
            optimized_count=len(unique_tiles)
        )

    def export_genesis_tiles(self, bank: OptimizedTileBank,
                            output_path: str):
        """
        Export optimized tiles in Genesis VDP format.

        Format: 4bpp planar (32 bytes per 8x8 tile)
        """
        from .genesis_export import export_tiles_4bpp

        tile_data = []
        for tile in bank.tiles:
            tile_bytes = export_tiles_4bpp(tile)
            tile_data.append(tile_bytes)

        with open(output_path, 'wb') as f:
            f.write(b''.join(tile_data))

    def generate_report(self, bank: OptimizedTileBank) -> str:
        """Generate optimization report."""
        report = [
            "Tile Optimization Report",
            "=" * 60,
            "",
            f"Original Tiles: {bank.original_count}",
            f"Optimized Tiles: {bank.optimized_count}",
            f"Savings: {bank.optimized_count - bank.original_count} tiles",
            f"VRAM Saved: {bank.savings_bytes:,} bytes",
            f"Reduction: {(1 - bank.optimized_count / bank.original_count) * 100:.1f}%",
            ""
        ]

        if self.enable_flip:
            report.append("✓ Flip detection enabled")
        if self.enable_palette_remap:
            report.append("✓ Palette remapping enabled")

        return "\n".join(report)

    def _extract_tiles(self, image: Image.Image) -> List[np.ndarray]:
        """Extract all 8x8 tiles from image."""
        img_array = np.array(image)
        tiles = []

        h, w = img_array.shape[:2]

        for y in range(0, h, self.tile_size):
            for x in range(0, w, self.tile_size):
                # Extract tile
                tile = img_array[y:y+self.tile_size, x:x+self.tile_size]

                # Pad if needed (edge tiles)
                if tile.shape[0] < self.tile_size or tile.shape[1] < self.tile_size:
                    padded = np.zeros((self.tile_size, self.tile_size, 4), dtype=np.uint8)
                    padded[:tile.shape[0], :tile.shape[1]] = tile
                    tile = padded

                tiles.append(tile)

        return tiles

    def _find_existing_tile(self, tile: np.ndarray,
                           existing: List[np.ndarray]) -> Optional[TileReference]:
        """
        Find if tile exists in bank (checking transforms).

        Returns:
            TileReference if found, None otherwise
        """
        tile_hash = self._hash_tile(tile)

        for idx, existing_tile in enumerate(existing):
            # Check normal
            if np.array_equal(tile, existing_tile):
                return TileReference(idx, TileTransform.NORMAL)

            if not self.enable_flip:
                continue

            # Check horizontal flip
            if np.array_equal(tile, np.fliplr(existing_tile)):
                return TileReference(idx, TileTransform.HFLIP)

            # Check vertical flip
            if np.array_equal(tile, np.flipud(existing_tile)):
                return TileReference(idx, TileTransform.VFLIP)

            # Check both flips
            if np.array_equal(tile, np.flipud(np.fliplr(existing_tile))):
                return TileReference(idx, TileTransform.HVFLIP)

        return None

    def _hash_tile(self, tile: np.ndarray) -> bytes:
        """Generate hash of tile data."""
        return tile.tobytes()

# Integration with existing pipeline
def optimize_for_genesis(sprite_sheet: Image.Image,
                        output_tiles: str,
                        output_metadata: str):
    """
    Optimize sprite sheet for Genesis and export.

    Usage:
        >>> optimize_for_genesis("player.png", "player_tiles.bin", "player_tiles.json")
    """
    optimizer = TileOptimizer(enable_flip=True)
    bank = optimizer.optimize_sprite_sheet(sprite_sheet)

    # Export tiles
    optimizer.export_genesis_tiles(bank, output_tiles)

    # Export metadata
    metadata = {
        'original_tiles': bank.original_count,
        'optimized_tiles': bank.optimized_count,
        'savings_bytes': bank.savings_bytes,
        'tile_map': {
            k.hex(): {'index': v.tile_index, 'transform': v.transform.value}
            for k, v in bank.tile_map.items()
        }
    }

    with open(output_metadata, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(optimizer.generate_report(bank))
```

**CLI:**
- `--optimize-tiles SPRITE --output tiles.bin --report`
- `--optimize-batch DIR --shared-tiles shared.bin`

---

### 6.1.4 Code Hygiene (Phase 6.1)

**Tasks:**
- [ ] Extract tile deduplication from `processing.py` to `optimization/tile_optimizer.py`
- [ ] Refactor compression logic from `compression/` to unified `retro_compress.py`
- [ ] Add type hints to all new modules
- [ ] Add comprehensive docstrings with examples
- [ ] Remove any duplicate logic between modules

**Testing:**
- [ ] Unit tests for sprite packing algorithms
- [ ] Benchmark tests for compression ratios
- [ ] Golden master tests for tile optimization
- [ ] Integration test: full pipeline with optimization

**Documentation:**
- [ ] Add "Optimization" section to USAGE.md
- [ ] Document compression algorithm selection guide
- [ ] Add performance comparison tables
- [ ] Create optimization best practices guide

---

## Phase 6.2: Asset Management & Workflow

**Goal:** Improve artist workflow with automation, tracking, and hot reload.

**Dependencies:** Phase 5 (validation, resources), Phase 6.1 (optimization)

**Timeline:** 2 weeks

### 6.2.1 Asset Database & Dependency Tracking

**File:** `tools/pipeline/database/asset_db.py` (NEW)

**Purpose:** Central asset catalog with metadata, tags, and dependency graph.

**Why Critical:** As games grow, tracking asset relationships manually becomes impossible.

**Dependencies:**
```bash
pip install sqlalchemy alembic
```

**Schema:**

```python
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

Base = declarative_base()

# Many-to-many relationship tables
asset_tags = Table('asset_tags', Base.metadata,
    Column('asset_id', Integer, ForeignKey('assets.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)

asset_dependencies = Table('asset_dependencies', Base.metadata,
    Column('asset_id', Integer, ForeignKey('assets.id')),
    Column('depends_on_id', Integer, ForeignKey('assets.id'))
)

class Asset(Base):
    """Asset record in database."""
    __tablename__ = 'assets'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    type = Column(String, nullable=False)  # 'sprite', 'tileset', 'palette', 'audio'
    path = Column(String, nullable=False)
    hash = Column(String)  # SHA256 for change detection
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Metadata
    width = Column(Integer)
    height = Column(Integer)
    color_count = Column(Integer)
    file_size = Column(Integer)

    # Relationships
    tags = relationship('Tag', secondary=asset_tags, back_populates='assets')
    dependencies = relationship('Asset',
                               secondary=asset_dependencies,
                               primaryjoin=id==asset_dependencies.c.asset_id,
                               secondaryjoin=id==asset_dependencies.c.depends_on_id,
                               backref='dependents')
    versions = relationship('AssetVersion', back_populates='asset', cascade='all, delete-orphan')

class Tag(Base):
    """Tag for asset categorization."""
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    assets = relationship('Asset', secondary=asset_tags, back_populates='tags')

class AssetVersion(Base):
    """Version history for assets."""
    __tablename__ = 'asset_versions'

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False)
    version = Column(Integer, nullable=False)
    hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    comment = Column(String)

    asset = relationship('Asset', back_populates='versions')

class AssetDatabase:
    """
    Asset database manager.

    Features:
    - Track all pipeline assets
    - Dependency graph (sprite uses palette X)
    - Version history
    - Tag-based organization
    - Change detection
    """

    def __init__(self, db_path: str = "assets.db"):
        """Initialize database connection."""
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def add_asset(self, name: str, type: str, path: str, **metadata) -> Asset:
        """Add new asset to database."""
        # Check if exists
        existing = self.session.query(Asset).filter_by(name=name).first()
        if existing:
            return self.update_asset(name, **metadata)

        # Compute hash
        file_hash = self._compute_hash(path)

        asset = Asset(
            name=name,
            type=type,
            path=path,
            hash=file_hash,
            **metadata
        )

        self.session.add(asset)
        self.session.commit()

        # Create initial version
        self._create_version(asset, "Initial version")

        return asset

    def update_asset(self, name: str, **metadata) -> Asset:
        """Update asset metadata."""
        asset = self.session.query(Asset).filter_by(name=name).first()
        if not asset:
            raise ValueError(f"Asset '{name}' not found")

        # Update fields
        for key, value in metadata.items():
            if hasattr(asset, key):
                setattr(asset, key, value)

        # Check if content changed
        new_hash = self._compute_hash(asset.path)
        if new_hash != asset.hash:
            asset.hash = new_hash
            self._create_version(asset, "Content updated")

        asset.updated_at = datetime.utcnow()
        self.session.commit()

        return asset

    def add_dependency(self, asset_name: str, depends_on: str):
        """Record that asset depends on another asset."""
        asset = self.session.query(Asset).filter_by(name=asset_name).first()
        dependency = self.session.query(Asset).filter_by(name=depends_on).first()

        if not asset or not dependency:
            raise ValueError("Asset not found")

        if dependency not in asset.dependencies:
            asset.dependencies.append(dependency)
            self.session.commit()

    def get_dependents(self, asset_name: str) -> List[Asset]:
        """Get all assets that depend on this asset."""
        asset = self.session.query(Asset).filter_by(name=asset_name).first()
        if not asset:
            return []

        return asset.dependents

    def get_dependencies(self, asset_name: str) -> List[Asset]:
        """Get all assets this asset depends on."""
        asset = self.session.query(Asset).filter_by(name=asset_name).first()
        if not asset:
            return []

        return asset.dependencies

    def tag_asset(self, asset_name: str, tag_name: str):
        """Add tag to asset."""
        asset = self.session.query(Asset).filter_by(name=asset_name).first()
        tag = self.session.query(Tag).filter_by(name=tag_name).first()

        if not tag:
            tag = Tag(name=tag_name)
            self.session.add(tag)

        if tag not in asset.tags:
            asset.tags.append(tag)
            self.session.commit()

    def find_by_tag(self, tag_name: str) -> List[Asset]:
        """Find all assets with tag."""
        tag = self.session.query(Tag).filter_by(name=tag_name).first()
        return tag.assets if tag else []

    def get_changed_assets(self) -> List[Asset]:
        """Find assets whose files have changed on disk."""
        changed = []

        for asset in self.session.query(Asset).all():
            current_hash = self._compute_hash(asset.path)
            if current_hash != asset.hash:
                changed.append(asset)

        return changed

    def invalidate_cache(self, asset_name: str):
        """Invalidate cache for asset and all dependents."""
        asset = self.session.query(Asset).filter_by(name=asset_name).first()
        if not asset:
            return

        # Recursively invalidate dependents
        to_invalidate = [asset]
        while to_invalidate:
            current = to_invalidate.pop()
            # Clear cache for this asset
            self._clear_cache(current)
            # Add dependents to queue
            to_invalidate.extend(current.dependents)

    def _compute_hash(self, path: str) -> str:
        """Compute SHA256 hash of file."""
        import hashlib
        with open(path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()

    def _create_version(self, asset: Asset, comment: str = ""):
        """Create version snapshot."""
        version_num = len(asset.versions) + 1
        version = AssetVersion(
            asset_id=asset.id,
            version=version_num,
            hash=asset.hash,
            comment=comment
        )
        self.session.add(version)
        self.session.commit()

    def _clear_cache(self, asset: Asset):
        """Clear cached files for asset."""
        # Implementation depends on cache strategy
        pass

# CLI integration
def scan_project(project_dir: str, db_path: str = "assets.db"):
    """
    Scan project directory and populate database.

    Usage:
        >>> scan_project("my_game/assets")
    """
    db = AssetDatabase(db_path)

    # Scan for assets
    for sprite_file in Path(project_dir).rglob("*.png"):
        # Determine type from path
        asset_type = 'sprite'
        if 'tiles' in str(sprite_file):
            asset_type = 'tileset'
        elif 'palette' in str(sprite_file):
            asset_type = 'palette'

        # Get metadata
        img = Image.open(sprite_file)
        metadata = {
            'width': img.width,
            'height': img.height,
            'file_size': sprite_file.stat().st_size
        }

        # Add to database
        db.add_asset(
            name=sprite_file.stem,
            type=asset_type,
            path=str(sprite_file),
            **metadata
        )

    print(f"Scanned {len(list(Path(project_dir).rglob('*.png')))} assets")
```

**CLI:**
- `--db-scan PROJECT_DIR` - Scan and populate database
- `--db-query "tag:characters"` - Query database
- `--db-dependents ASSET` - Show dependency tree
- `--db-changed` - Show changed assets

---

### 6.2.2 Hot Reload / Watch Mode

**File:** `tools/pipeline/watch/file_watcher.py` (NEW)

**Purpose:** Auto-regenerate assets when source files change + push to running emulator.

**Impact:** Instant feedback loop for artists (modify PNG → see in-game immediately)

**Dependencies:**
```bash
pip install watchdog
```

**Implementation:**

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent
from pathlib import Path
from typing import Callable, Dict, List
import time

class AssetWatcher(FileSystemEventHandler):
    """
    Watch for asset changes and trigger pipeline processing.

    Features:
    - Debouncing (wait for file write to complete)
    - Selective processing (only changed assets)
    - Hot reload to emulator (optional)
    """

    def __init__(self,
                 watch_dir: str,
                 pipeline_callback: Callable[[str], None],
                 debounce_seconds: float = 0.5,
                 extensions: List[str] = ['.png', '.ase']):
        """
        Initialize file watcher.

        Args:
            watch_dir: Directory to watch
            pipeline_callback: Function to call when file changes
            debounce_seconds: Wait time before processing
            extensions: File extensions to watch
        """
        super().__init__()
        self.watch_dir = Path(watch_dir)
        self.pipeline_callback = pipeline_callback
        self.debounce_seconds = debounce_seconds
        self.extensions = extensions

        # Debouncing state
        self._pending: Dict[str, float] = {}  # path -> last_modified_time

    def on_modified(self, event):
        """Handle file modification event."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Check extension
        if file_path.suffix not in self.extensions:
            return

        # Debounce (wait for file write to complete)
        current_time = time.time()
        self._pending[str(file_path)] = current_time

        # Schedule processing
        time.sleep(self.debounce_seconds)

        # Check if still the latest modification
        if self._pending.get(str(file_path)) == current_time:
            self._process_file(file_path)
            del self._pending[str(file_path)]

    def _process_file(self, file_path: Path):
        """Process changed file through pipeline."""
        print(f"🔄 Change detected: {file_path.name}")

        try:
            self.pipeline_callback(str(file_path))
            print(f"✓ Processed: {file_path.name}")
        except Exception as e:
            print(f"✗ Error processing {file_path.name}: {e}")

class WatchManager:
    """
    Manage multiple file watchers.

    Integrates with pipeline and optional emulator hot reload.
    """

    def __init__(self, project_dir: str):
        """Initialize watch manager."""
        self.project_dir = Path(project_dir)
        self.observers: List[Observer] = []

    def start_watching(self,
                      watch_dirs: List[str],
                      pipeline_config: dict = None,
                      hot_reload: bool = False):
        """
        Start watching directories for changes.

        Args:
            watch_dirs: Directories to watch
            pipeline_config: Pipeline configuration
            hot_reload: Enable hot reload to emulator
        """
        from ..core.pipeline import Pipeline

        # Create pipeline instance
        pipeline = Pipeline(pipeline_config or {})

        def process_callback(file_path: str):
            """Process file through pipeline."""
            output_dir = self.project_dir / "output"
            result = pipeline.process(file_path, str(output_dir))

            if hot_reload:
                self._hot_reload_to_emulator(result)

        # Create watchers for each directory
        for watch_dir in watch_dirs:
            handler = AssetWatcher(watch_dir, process_callback)
            observer = Observer()
            observer.schedule(handler, str(watch_dir), recursive=True)
            observer.start()
            self.observers.append(observer)

            print(f"👁️  Watching: {watch_dir}")

        print(f"✓ Watch mode active. Press Ctrl+C to stop.")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop all watchers."""
        for observer in self.observers:
            observer.stop()
            observer.join()

        print("✓ Watch mode stopped")

    def _hot_reload_to_emulator(self, result):
        """Push changes to running emulator (if supported)."""
        # Emulator integration (future enhancement)
        # Could use debugger protocol for Kega Fusion, BlastEm, etc.
        pass

# CLI entry point
def watch_mode(project_dir: str, watch_dirs: List[str] = None):
    """
    Start watch mode for asset pipeline.

    Usage:
        >>> watch_mode("my_game", watch_dirs=["assets/sprites", "assets/tiles"])
    """
    if watch_dirs is None:
        # Default: watch common asset directories
        watch_dirs = ["sprites", "tiles", "palettes"]

    manager = WatchManager(project_dir)
    manager.start_watching(watch_dirs)
```

**CLI:**
- `--watch [DIRS...]` - Start watch mode
- `--watch --hot-reload` - Enable emulator hot reload

---

### 6.2.3 Batch Processing & Job Queue

**File:** `tools/pipeline/queue/batch_processor.py` (NEW)

**Purpose:** Process large batches of assets in parallel with progress tracking.

**Dependencies:**
```bash
pip install celery redis  # OR
pip install dramatiq      # Lighter alternative
```

**Implementation:**

```python
from typing import List, Dict, Callable, Any
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
import json

@dataclass
class BatchJob:
    """A batch processing job."""
    id: str
    input_files: List[str]
    output_dir: str
    config: Dict[str, Any]
    total: int
    completed: int = 0
    failed: int = 0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class BatchProcessor:
    """
    Process assets in parallel with progress tracking.

    Features:
    - Multi-process parallelism
    - Progress tracking
    - Error collection
    - Resumable jobs
    """

    def __init__(self, max_workers: int = None):
        """
        Initialize batch processor.

        Args:
            max_workers: Max parallel workers (default: CPU count)
        """
        self.max_workers = max_workers

    def process_batch(self,
                     input_files: List[str],
                     output_dir: str,
                     processor_func: Callable[[str, str, dict], None],
                     config: Dict[str, Any] = None,
                     resume: bool = False) -> BatchJob:
        """
        Process batch of files in parallel.

        Args:
            input_files: List of input file paths
            output_dir: Output directory
            processor_func: Function(input_path, output_path, config) -> None
            config: Configuration dict
            resume: Resume from previous run

        Returns:
            BatchJob with results
        """
        config = config or {}
        job_id = self._generate_job_id()

        # Create job
        job = BatchJob(
            id=job_id,
            input_files=input_files,
            output_dir=output_dir,
            config=config,
            total=len(input_files)
        )

        # Check for resume
        if resume:
            job = self._load_checkpoint(job_id) or job

        # Process in parallel
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            futures = {}
            for input_file in input_files[job.completed:]:
                output_file = self._get_output_path(input_file, output_dir)
                future = executor.submit(
                    self._safe_process,
                    processor_func,
                    input_file,
                    output_file,
                    config
                )
                futures[future] = input_file

            # Collect results
            for future in as_completed(futures):
                input_file = futures[future]

                try:
                    future.result()
                    job.completed += 1
                except Exception as e:
                    job.failed += 1
                    job.errors.append(f"{input_file}: {str(e)}")

                # Print progress
                self._print_progress(job)

                # Checkpoint
                if job.completed % 10 == 0:
                    self._save_checkpoint(job)

        # Final checkpoint
        self._save_checkpoint(job)

        return job

    def process_directory(self,
                         input_dir: str,
                         output_dir: str,
                         pattern: str = "*.png",
                         processor_func: Callable = None,
                         config: Dict[str, Any] = None) -> BatchJob:
        """
        Process all files in directory matching pattern.

        Usage:
            >>> processor.process_directory(
            ...     "sprites/raw",
            ...     "sprites/processed",
            ...     pattern="*.png",
            ...     processor_func=process_sprite
            ... )
        """
        input_files = [str(p) for p in Path(input_dir).glob(pattern)]
        return self.process_batch(input_files, output_dir, processor_func, config)

    def _safe_process(self, func, input_path, output_path, config):
        """Safely execute processor function with error handling."""
        try:
            func(input_path, output_path, config)
        except Exception as e:
            raise RuntimeError(f"Processing failed: {e}")

    def _get_output_path(self, input_path: str, output_dir: str) -> str:
        """Generate output path from input path."""
        input_file = Path(input_path)
        output_path = Path(output_dir) / input_file.name
        return str(output_path)

    def _generate_job_id(self) -> str:
        """Generate unique job ID."""
        import uuid
        return str(uuid.uuid4())[:8]

    def _save_checkpoint(self, job: BatchJob):
        """Save job checkpoint."""
        checkpoint_file = Path(f".batch_{job.id}.json")

        with open(checkpoint_file, 'w') as f:
            json.dump({
                'id': job.id,
                'input_files': job.input_files,
                'output_dir': job.output_dir,
                'config': job.config,
                'total': job.total,
                'completed': job.completed,
                'failed': job.failed,
                'errors': job.errors
            }, f)

    def _load_checkpoint(self, job_id: str) -> Optional[BatchJob]:
        """Load job checkpoint."""
        checkpoint_file = Path(f".batch_{job_id}.json")

        if not checkpoint_file.exists():
            return None

        with open(checkpoint_file, 'r') as f:
            data = json.load(f)
            return BatchJob(**data)

    def _print_progress(self, job: BatchJob):
        """Print progress bar."""
        percent = (job.completed / job.total) * 100
        bar_length = 40
        filled = int(bar_length * job.completed / job.total)
        bar = '█' * filled + '░' * (bar_length - filled)

        print(f"\r[{bar}] {percent:.1f}% ({job.completed}/{job.total}) Failed: {job.failed}", end='')

        if job.completed == job.total:
            print()  # Newline when done

# Convenience functions
def batch_process_sprites(input_dir: str, output_dir: str, **config):
    """
    Batch process all sprites in directory.

    Usage:
        >>> batch_process_sprites("raw_sprites/", "processed/",
        ...                       platform='genesis', max_colors=16)
    """
    from ..core.pipeline import Pipeline

    pipeline = Pipeline(config)

    def process_func(input_path, output_path, cfg):
        pipeline.process(input_path, output_path)

    processor = BatchProcessor()
    job = processor.process_directory(input_dir, output_dir,
                                     processor_func=process_func,
                                     config=config)

    print(f"\n✓ Batch complete: {job.completed} succeeded, {job.failed} failed")

    if job.errors:
        print("\nErrors:")
        for error in job.errors[:10]:  # Show first 10
            print(f"  - {error}")
```

**CLI:**
- `--batch-process DIR --output OUT` - Process directory
- `--batch-resume JOB_ID` - Resume interrupted batch

---

### 6.2.4 Code Hygiene (Phase 6.2)

**Tasks:**
- [ ] Review database schema for normalization
- [ ] Add connection pooling to AssetDatabase
- [ ] Add retry logic to file watcher (handle locked files)
- [ ] Implement graceful shutdown for batch processor
- [ ] Add progress callbacks to batch processor

**Testing:**
- [ ] Unit tests for asset database CRUD operations
- [ ] Integration test: watch mode with mock file changes
- [ ] Load test: batch process 1000 sprites
- [ ] Test: database migration with Alembic

**Documentation:**
- [ ] Add "Asset Management" section to USAGE.md
- [ ] Document watch mode setup and usage
- [ ] Create batch processing examples
- [ ] Add database schema diagram

---

## Phase 6.3: AI & Quality Enhancement

**Goal:** Expand AI capabilities with better models and quality assurance.

**Dependencies:** Phase 3 (AI features), Phase 5 (validation)

**Timeline:** 2-3 weeks

### 6.3.1 Advanced Neural Upscaling

**File:** `tools/pipeline/upscalers/` (NEW directory)

**Purpose:** Add specialized upscaling models that preserve pixel art aesthetic.

**Status:** ⚠️ Basic Pollinations upscaler exists in `ai_providers/pollinations.py` - EXPAND with better models

**Models to add:**

| Model | Best For | Preservation | Speed | Local/API |
|-------|----------|--------------|-------|-----------|
| **Real-ESRGAN** | General pixel art | Excellent | Medium | Local |
| **waifu2x** | Anime/pixel art | Great | Fast | Both |
| **Real-CUGAN** | Conservative upscale | Best | Slow | Local |
| **AnimeSR** | Anime sprites | Excellent | Medium | Local |

**Dependencies:**
```bash
pip install realesrgan basicsr facexlib gfpgan
pip install torch torchvision  # PyTorch for models
```

**Implementation:**

```python
from pathlib import Path
from PIL import Image
import numpy as np
from typing import Optional, Literal
from dataclasses import dataclass

@dataclass
class UpscaleResult:
    """Result of upscaling operation."""
    image: Image.Image
    model: str
    scale: int
    time_ms: float

class NeuralUpscaler:
    """
    Multi-model neural upscaler with pixel art preservation.

    Features:
    - Multiple specialized models
    - Automatic model selection based on content
    - Tile-based processing for large images
    - GPU acceleration (if available)
    """

    MODELS = {
        'realesrgan': 'RealESRGAN_x4plus_anime_6B',
        'waifu2x': 'waifu2x-caffe',
        'cugan': 'up2x-latest-conservative',
        'animeresr': 'animeSR_v1',
    }

    def __init__(self,
                 model: str = 'realesrgan',
                 gpu: bool = True,
                 tile_size: int = 512):
        """
        Initialize upscaler.

        Args:
            model: Model name ('realesrgan', 'waifu2x', 'cugan', 'animesr')
            gpu: Use GPU acceleration if available
            tile_size: Tile size for processing (larger = faster but more VRAM)
        """
        self.model_name = model
        self.gpu = gpu and self._is_gpu_available()
        self.tile_size = tile_size
        self._model = None

    def upscale(self,
               image: Image.Image,
               scale: int = 4,
               preserve_alpha: bool = True) -> UpscaleResult:
        """
        Upscale image using neural network.

        Args:
            image: Input image
            scale: Upscale factor (2, 4, or 8)
            preserve_alpha: Preserve alpha channel

        Returns:
            UpscaleResult with upscaled image
        """
        import time
        start_time = time.time()

        # Load model lazily
        if self._model is None:
            self._model = self._load_model()

        # Convert to RGB for processing
        has_alpha = image.mode == 'RGBA'
        if has_alpha and preserve_alpha:
            alpha = image.split()[3]
            rgb = image.convert('RGB')
        else:
            rgb = image.convert('RGB')
            alpha = None

        # Upscale
        upscaled_rgb = self._upscale_impl(rgb, scale)

        # Restore alpha
        if alpha and preserve_alpha:
            # Upscale alpha channel separately
            alpha_upscaled = alpha.resize(
                (upscaled_rgb.width, upscaled_rgb.height),
                Image.NEAREST  # Sharp alpha
            )
            upscaled_rgb.putalpha(alpha_upscaled)

        elapsed_ms = (time.time() - start_time) * 1000

        return UpscaleResult(
            image=upscaled_rgb,
            model=self.model_name,
            scale=scale,
            time_ms=elapsed_ms
        )

    def _upscale_impl(self, image: Image.Image, scale: int) -> Image.Image:
        """Implementation-specific upscaling."""
        if self.model_name == 'realesrgan':
            return self._upscale_realesrgan(image, scale)
        elif self.model_name == 'waifu2x':
            return self._upscale_waifu2x(image, scale)
        elif self.model_name == 'cugan':
            return self._upscale_cugan(image, scale)
        elif self.model_name == 'animesr':
            return self._upscale_animesr(image, scale)
        else:
            raise ValueError(f"Unknown model: {self.model_name}")

    def _upscale_realesrgan(self, image: Image.Image, scale: int) -> Image.Image:
        """Upscale with Real-ESRGAN."""
        from realesrgan import RealESRGANer
        from basicsr.archs.rrdbnet_arch import RRDBNet

        # Convert PIL to numpy
        img_np = np.array(image)

        # Upscale
        output, _ = self._model.enhance(img_np, outscale=scale)

        # Convert back to PIL
        return Image.fromarray(output)

    def _upscale_waifu2x(self, image: Image.Image, scale: int) -> Image.Image:
        """Upscale with waifu2x."""
        # waifu2x implementation (can use command-line tool or library)
        # For now, fallback to simple resize
        target_size = (image.width * scale, image.height * scale)
        return image.resize(target_size, Image.LANCZOS)

    def _upscale_cugan(self, image: Image.Image, scale: int) -> Image.Image:
        """Upscale with Real-CUGAN (conservative, preserves pixel art)."""
        # Real-CUGAN implementation
        pass

    def _upscale_animesr(self, image: Image.Image, scale: int) -> Image.Image:
        """Upscale with AnimeSR."""
        # AnimeSR implementation
        pass

    def _load_model(self):
        """Load upscaling model."""
        if self.model_name == 'realesrgan':
            from realesrgan import RealESRGANer
            from basicsr.archs.rrdbnet_arch import RRDBNet

            model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64,
                           num_block=6, num_grow_ch=32, scale=4)

            upsampler = RealESRGANer(
                scale=4,
                model_path=self._get_model_path('realesrgan'),
                model=model,
                tile=self.tile_size,
                tile_pad=10,
                pre_pad=0,
                half=self.gpu  # FP16 for GPU
            )

            return upsampler

        # Other models...
        return None

    def _get_model_path(self, model_name: str) -> str:
        """Get path to model weights."""
        # Download models to cache directory
        from huggingface_hub import hf_hub_download

        repo_map = {
            'realesrgan': 'xinntao/Real-ESRGAN',
            'animesr': 'TencentARC/AnimeSR',
        }

        if model_name in repo_map:
            return hf_hub_download(
                repo_id=repo_map[model_name],
                filename=f"{model_name}.pth"
            )

        return None

    def _is_gpu_available(self) -> bool:
        """Check if GPU is available."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

# Convenience function
def upscale_sprite(input_path: str, output_path: str,
                  model: str = 'realesrgan', scale: int = 4):
    """
    Upscale sprite with best model.

    Usage:
        >>> upscale_sprite("char_16x16.png", "char_64x64.png", scale=4)
    """
    upscaler = NeuralUpscaler(model=model)

    img = Image.open(input_path)
    result = upscaler.upscale(img, scale=scale)
    result.image.save(output_path)

    print(f"✓ Upscaled {scale}x using {model}")
    print(f"  {img.width}x{img.height} -> {result.image.width}x{result.image.height}")
    print(f"  Time: {result.time_ms:.0f}ms")
```

**CLI:** `--upscale INPUT --model [realesrgan|waifu2x|cugan] --scale [2|4|8]`

**Integration:** Update `ai.py` AIUpscaler to use these models

---

### 6.3.2 Semantic Segmentation (SAM)

**File:** `tools/pipeline/segmentation/sam.py` (NEW)

**Purpose:** Expand basic rembg with SAM (Segment Anything Model) for precise masking.

**Status:** ⚠️ Basic rembg exists in `ai.py` BackgroundRemover - EXPAND with SAM

**Dependencies:**
```bash
pip install segment-anything transformers
```

**Use Cases:**
- Auto-detect character vs. weapon vs. effects (separate layers)
- Click-to-segment specific objects
- Pose estimation for character rigging
- Auto-generate collision masks

**Implementation:**

```python
from segment_anything import sam_model_registry, SamPredictor
from PIL import Image
import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Segment:
    """A segmented region."""
    mask: np.ndarray  # Binary mask
    bbox: Tuple[int, int, int, int]  # x, y, width, height
    area: int
    confidence: float
    label: Optional[str] = None

class SemanticSegmenter:
    """
    Semantic segmentation using SAM (Segment Anything Model).

    Features:
    - Automatic object detection
    - Point-based segmentation (click to select)
    - Bounding box segmentation
    - Multi-layer export (character, weapon, effects)
    """

    def __init__(self, model_type: str = 'vit_b', device: str = 'cuda'):
        """
        Initialize SAM model.

        Args:
            model_type: 'vit_h' (huge), 'vit_l' (large), 'vit_b' (base)
            device: 'cuda' or 'cpu'
        """
        self.model_type = model_type
        self.device = device
        self._predictor = None

    def segment_all(self, image: Image.Image) -> List[Segment]:
        """
        Automatically segment all objects in image.

        Returns:
            List of detected segments
        """
        if self._predictor is None:
            self._load_model()

        # Convert to numpy
        img_array = np.array(image.convert('RGB'))

        # Set image
        self._predictor.set_image(img_array)

        # Generate masks
        masks, scores, _ = self._predictor.predict(
            point_coords=None,
            point_labels=None,
            multimask_output=True
        )

        # Convert to Segment objects
        segments = []
        for mask, score in zip(masks, scores):
            bbox = self._mask_to_bbox(mask)
            segments.append(Segment(
                mask=mask,
                bbox=bbox,
                area=np.sum(mask),
                confidence=float(score)
            ))

        return segments

    def segment_point(self,
                     image: Image.Image,
                     point: Tuple[int, int],
                     foreground: bool = True) -> Segment:
        """
        Segment object at point location.

        Args:
            image: Input image
            point: (x, y) coordinates
            foreground: True for foreground, False for background

        Returns:
            Segmented object
        """
        if self._predictor is None:
            self._load_model()

        img_array = np.array(image.convert('RGB'))
        self._predictor.set_image(img_array)

        # Predict
        masks, scores, _ = self._predictor.predict(
            point_coords=np.array([point]),
            point_labels=np.array([1 if foreground else 0]),
            multimask_output=False
        )

        mask = masks[0]
        bbox = self._mask_to_bbox(mask)

        return Segment(
            mask=mask,
            bbox=bbox,
            area=np.sum(mask),
            confidence=float(scores[0])
        )

    def extract_layers(self,
                      image: Image.Image,
                      layer_points: Dict[str, List[Tuple[int, int]]]) -> Dict[str, Image.Image]:
        """
        Extract multiple layers from image using point prompts.

        Args:
            image: Input image
            layer_points: Dict of layer_name -> list of points
                Example: {
                    'character': [(50, 50)],
                    'weapon': [(80, 30)],
                    'effects': [(60, 70)]
                }

        Returns:
            Dict of layer_name -> extracted image
        """
        layers = {}

        for layer_name, points in layer_points.items():
            # Segment all points
            segments = []
            for point in points:
                segment = self.segment_point(image, point, foreground=True)
                segments.append(segment)

            # Combine masks
            combined_mask = np.zeros_like(segments[0].mask)
            for segment in segments:
                combined_mask = np.logical_or(combined_mask, segment.mask)

            # Extract layer
            img_array = np.array(image)
            layer_array = img_array.copy()
            layer_array[~combined_mask] = [0, 0, 0, 0]  # Make background transparent

            layers[layer_name] = Image.fromarray(layer_array)

        return layers

    def auto_detect_character(self, image: Image.Image) -> Segment:
        """
        Automatically detect main character in sprite.

        Assumes character is:
        - Largest segment
        - Roughly centered
        - Has sufficient area
        """
        segments = self.segment_all(image)

        if not segments:
            raise ValueError("No segments detected")

        # Find largest segment near center
        center_x = image.width / 2
        center_y = image.height / 2

        best_segment = None
        best_score = 0

        for segment in segments:
            x, y, w, h = segment.bbox
            cx = x + w / 2
            cy = y + h / 2

            # Score based on size and proximity to center
            dist_to_center = ((cx - center_x)**2 + (cy - center_y)**2) ** 0.5
            size_score = segment.area / (image.width * image.height)
            center_score = 1 / (1 + dist_to_center / min(image.width, image.height))

            score = size_score * center_score * segment.confidence

            if score > best_score:
                best_score = score
                best_segment = segment

        return best_segment

    def generate_collision_mask(self,
                                image: Image.Image,
                                simplify: bool = True,
                                tolerance: int = 2) -> np.ndarray:
        """
        Generate collision mask for sprite.

        Args:
            image: Input sprite
            simplify: Simplify mask to reduce polygon complexity
            tolerance: Simplification tolerance

        Returns:
            Binary collision mask
        """
        # Segment character
        character = self.auto_detect_character(image)

        if simplify:
            # Simplify mask using morphological operations
            from scipy import ndimage

            # Erode then dilate (opening) to remove noise
            mask = ndimage.binary_opening(character.mask, iterations=tolerance)

            # Dilate then erode (closing) to fill holes
            mask = ndimage.binary_closing(mask, iterations=tolerance)
        else:
            mask = character.mask

        return mask

    def _load_model(self):
        """Load SAM model."""
        # Download model weights
        checkpoint_map = {
            'vit_b': 'sam_vit_b_01ec64.pth',
            'vit_l': 'sam_vit_l_0b3195.pth',
            'vit_h': 'sam_vit_h_4b8939.pth',
        }

        checkpoint_path = self._download_checkpoint(checkpoint_map[self.model_type])

        # Load model
        sam = sam_model_registry[self.model_type](checkpoint=checkpoint_path)
        sam.to(device=self.device)

        self._predictor = SamPredictor(sam)

    def _download_checkpoint(self, filename: str) -> str:
        """Download SAM checkpoint."""
        from huggingface_hub import hf_hub_download

        return hf_hub_download(
            repo_id="facebook/sam-vit-base",
            filename=filename,
            cache_dir=".cache/sam"
        )

    def _mask_to_bbox(self, mask: np.ndarray) -> Tuple[int, int, int, int]:
        """Convert binary mask to bounding box."""
        rows = np.any(mask, axis=1)
        cols = np.any(mask, axis=0)

        if not np.any(rows) or not np.any(cols):
            return (0, 0, 0, 0)

        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]

        return (int(cmin), int(rmin), int(cmax - cmin), int(rmax - rmin))

# Integration with existing BackgroundRemover
def segment_sprite_layers(input_path: str, output_dir: str):
    """
    Segment sprite into layers (character, weapon, effects).

    Usage:
        >>> segment_sprite_layers("warrior.png", "warrior_layers/")
    """
    segmenter = SemanticSegmenter()

    img = Image.open(input_path)

    # Auto-detect layers
    # (In practice, would need UI for point selection or auto-detection heuristics)
    layer_points = {
        'character': [(img.width // 2, img.height // 2)],  # Center point
    }

    layers = segmenter.extract_layers(img, layer_points)

    # Save layers
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for name, layer_img in layers.items():
        layer_img.save(output_path / f"{name}.png")

    print(f"✓ Extracted {len(layers)} layers to {output_dir}")
```

**CLI:**
- `--segment INPUT --output-layers DIR`
- `--segment-auto INPUT --detect-character`
- `--generate-collision INPUT --output mask.png`

---

### 6.3.3 Visual Regression Testing

**File:** `tools/tests/test_visual_regression.py` (NEW)

**Purpose:** Detect unintended visual changes from pipeline refactoring.

**Dependencies:**
```bash
pip install pytest-image-diff pixelmatch
```

**Implementation:**

```python
import pytest
from PIL import Image
from pathlib import Path
import numpy as np
from pixelmatch.contrib.PIL import pixelmatch

class VisualRegressionTest:
    """
    Visual regression testing for pipeline operations.

    Compares output against golden master images.
    """

    GOLDEN_MASTER_DIR = Path("tests/golden_masters")
    TOLERANCE = 0.01  # 1% difference threshold

    def test_sprite_processing(self):
        """Test that sprite processing produces expected output."""
        from tools.pipeline.processing import process_sprite

        # Process test sprite
        input_path = "tests/fixtures/test_sprite.png"
        output_path = "tests/output/test_sprite_processed.png"

        process_sprite(input_path, output_path, platform='genesis')

        # Compare to golden master
        golden_path = self.GOLDEN_MASTER_DIR / "test_sprite_processed.png"
        self._assert_images_match(output_path, golden_path)

    def test_palette_conversion(self):
        """Test palette conversion visual output."""
        from tools.pipeline.palette_converter import PaletteConverter

        # Convert palette
        converter = PaletteConverter()
        input_img = Image.open("tests/fixtures/test_fullcolor.png")
        converted = converter.convert_to_genesis_palette(input_img)

        # Save and compare
        output_path = Path("tests/output/test_palette_converted.png")
        converted.save(output_path)

        golden_path = self.GOLDEN_MASTER_DIR / "test_palette_converted.png"
        self._assert_images_match(output_path, golden_path)

    def _assert_images_match(self, output_path: Path, golden_path: Path):
        """Assert that output matches golden master."""
        if not golden_path.exists():
            raise FileNotFoundError(
                f"Golden master not found: {golden_path}\n"
                f"Run with --update-goldens to create it"
            )

        # Load images
        output_img = Image.open(output_path).convert('RGBA')
        golden_img = Image.open(golden_path).convert('RGBA')

        # Check dimensions
        assert output_img.size == golden_img.size, \
            f"Size mismatch: {output_img.size} vs {golden_img.size}"

        # Pixel-level comparison
        diff_img = Image.new('RGBA', output_img.size)
        mismatch = pixelmatch(
            golden_img,
            output_img,
            diff_img,
            threshold=0.1,
            alpha=0.5
        )

        total_pixels = output_img.width * output_img.height
        diff_percent = mismatch / total_pixels

        if diff_percent > self.TOLERANCE:
            # Save diff image for inspection
            diff_path = Path("tests/output") / f"diff_{output_path.name}"
            diff_img.save(diff_path)

            raise AssertionError(
                f"Visual regression detected: {diff_percent:.2%} difference\n"
                f"Diff saved to: {diff_path}\n"
                f"Update golden master if change is intentional: pytest --update-goldens"
            )

    @pytest.fixture(autouse=True)
    def setup(self, request):
        """Setup test environment."""
        # Create output directory
        Path("tests/output").mkdir(parents=True, exist_ok=True)

        # Check for --update-goldens flag
        if request.config.getoption("--update-goldens"):
            self._update_mode = True
        else:
            self._update_mode = False

    def _update_golden_master(self, output_path: Path, golden_path: Path):
        """Update golden master with new output."""
        self.GOLDEN_MASTER_DIR.mkdir(parents=True, exist_ok=True)

        import shutil
        shutil.copy2(output_path, golden_path)

        print(f"✓ Updated golden master: {golden_path}")

# pytest configuration
def pytest_addoption(parser):
    parser.addoption(
        "--update-goldens",
        action="store_true",
        default=False,
        help="Update golden master images with current output"
    )
```

**CLI:**
- `pytest tests/test_visual_regression.py` - Run tests
- `pytest --update-goldens` - Update golden masters

---

### 6.3.4 Advanced AI Features

**File:** `tools/pipeline/ai/advanced.py` (NEW)

**Purpose:** Additional AI-powered quality and consistency features.

**Features:**

1. **Style Consistency Checker**
   - Verify all sprites match art style
   - Detect outliers (wrong palette, different detail level)
   - Use perceptual embeddings (CLIP, DINOv2)

2. **Color Harmony Validator**
   - Check palette for color theory issues
   - Suggest improvements
   - Detect low contrast (accessibility)

3. **Content-Aware Fill**
   - Smart inpainting for sprite repairs
   - Remove artifacts
   - Fill missing areas

**Implementation sketch:**

```python
class StyleConsistencyChecker:
    """Check if sprite matches art style of other sprites."""

    def check_consistency(self, test_sprite: Image.Image,
                         reference_sprites: List[Image.Image]) -> float:
        """
        Calculate style consistency score (0-1).

        Uses CLIP embeddings to measure similarity.
        """
        # Compute embeddings
        test_embedding = self._compute_embedding(test_sprite)
        ref_embeddings = [self._compute_embedding(ref) for ref in reference_sprites]

        # Compute average cosine similarity
        similarities = [self._cosine_similarity(test_embedding, ref)
                       for ref in ref_embeddings]

        return np.mean(similarities)
```

---

### 6.3.5 Code Hygiene (Phase 6.3)

**Tasks:**
- [ ] Unify upscaler interface across models
- [ ] Add model caching (don't re-download)
- [ ] Add GPU memory management for SAM
- [ ] Refactor AI modules into consistent structure
- [ ] Add fallback chains (SAM → rembg → flood-fill)

**Testing:**
- [ ] Benchmark upscaling models (quality vs speed)
- [ ] Unit tests for SAM segmentation
- [ ] Visual regression test suite with golden masters
- [ ] Integration test: full AI pipeline

**Documentation:**
- [ ] Add "AI & Quality" section to USAGE.md
- [ ] Document model selection guide
- [ ] Add visual regression testing guide
- [ ] Create upscaling quality comparison

---

## Phase 6.4: Palette & Color Management

**Goal:** Expand palette tooling with curated libraries and generation.

**Dependencies:** Phase 1 (palette conversion)

**Timeline:** 1 week

### 6.4.1 Lospec Palette Integration

**File:** `tools/pipeline/palettes/lospec.py` (NEW)

**Purpose:** Access 1000+ curated retro palettes from Lospec.

**Implementation:**

```python
import httpx
from typing import List, Tuple, Optional

class LospecPaletteLibrary:
    """
    Access Lospec palette database.

    Lospec: https://lospec.com/palette-list
    """

    BASE_URL = "https://lospec.com/palette-list"

    def fetch_palette(self, name: str) -> List[Tuple[int, int, int]]:
        """
        Fetch palette by name.

        Example:
            >>> lospec = LospecPaletteLibrary()
            >>> palette = lospec.fetch_palette("SEGA-Genesis")
        """
        url = f"{self.BASE_URL}/{name}.json"
        resp = httpx.get(url)
        resp.raise_for_status()

        data = resp.json()
        colors = data['colors']

        # Convert hex to RGB
        rgb_colors = []
        for hex_color in colors:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            rgb_colors.append((r, g, b))

        return rgb_colors

    def search_palettes(self,
                       tags: List[str] = None,
                       max_colors: int = None) -> List[dict]:
        """
        Search Lospec database.

        Args:
            tags: Filter by tags (e.g., ['retro', '16-bit'])
            max_colors: Filter by max color count
        """
        # Implementation uses Lospec API
        pass
```

### 6.4.2 Colormind AI Integration

**File:** `tools/pipeline/palettes/colormind.py` (NEW)

**Purpose:** Generate harmonious palettes using AI.

**API:** http://colormind.io/api-access/

---

### 6.4.3 Code Hygiene (Phase 6.4)

**Tasks:**
- [ ] Unify palette format across modules
- [ ] Add palette validation (check color counts, duplicates)
- [ ] Create palette preview generator
- [ ] Add palette conversion utilities

**Testing:**
- [ ] Unit tests for Lospec API
- [ ] Test palette application on sprites
- [ ] Integration test with palette converter

**Documentation:**
- [ ] Add "Palette Management" section to USAGE.md
- [ ] Document Lospec integration
- [ ] Create palette selection guide

---

## Phase 6.5: Animation Enhancement

**Goal:** Advanced animation tools (tweening, easing, motion blur).

**Dependencies:** Phase 1 (animation), Phase 3 (AI)

**Timeline:** 1-2 weeks

### 6.5.1 Tweening & Interpolation

**File:** `tools/pipeline/animation/tweening.py` (NEW)

**Purpose:** Generate intermediate frames between keyframes.

**Implementation:**

```python
class FrameInterpolator:
    """
    Generate intermediate animation frames.

    Methods:
    - Optical flow (best quality)
    - Pixel blending (fast)
    - AI interpolation (experimental)
    """

    def tween_frames(self,
                    start: Image.Image,
                    end: Image.Image,
                    steps: int,
                    method: str = 'optical_flow',
                    easing: str = 'linear') -> List[Image.Image]:
        """
        Generate frames between start and end.

        Args:
            start: Starting keyframe
            end: Ending keyframe
            steps: Number of intermediate frames
            method: 'optical_flow' | 'blend' | 'ai'
            easing: 'linear' | 'ease_in' | 'ease_out' | 'ease_in_out'

        Returns:
            List of intermediate frames
        """
        frames = [start]

        for i in range(1, steps + 1):
            t = i / (steps + 1)

            # Apply easing
            t = self._apply_easing(t, easing)

            # Interpolate
            if method == 'optical_flow':
                frame = self._optical_flow_interpolate(start, end, t)
            elif method == 'blend':
                frame = self._blend_interpolate(start, end, t)
            elif method == 'ai':
                frame = self._ai_interpolate(start, end, t)

            frames.append(frame)

        frames.append(end)
        return frames

    def _apply_easing(self, t: float, easing: str) -> float:
        """Apply easing function."""
        if easing == 'linear':
            return t
        elif easing == 'ease_in':
            return t * t
        elif easing == 'ease_out':
            return t * (2 - t)
        elif easing == 'ease_in_out':
            return t * t * (3 - 2 * t)
        return t

    def _optical_flow_interpolate(self, start, end, t):
        """Interpolate using optical flow."""
        # Use OpenCV optical flow
        pass

    def _blend_interpolate(self, start, end, t):
        """Simple alpha blending."""
        return Image.blend(start, end, t)
```

### 6.5.2 Motion Blur Generation

**Purpose:** Add motion blur for fast-moving sprites.

---

### 6.5.3 Code Hygiene (Phase 6.5)

**Tasks:**
- [ ] Add animation preview generator
- [ ] Integrate with existing animation.py
- [ ] Add easing curve visualizer
- [ ] Optimize frame interpolation

**Testing:**
- [ ] Unit tests for tweening algorithms
- [ ] Visual tests for easing functions
- [ ] Integration test with AnimationExtractor

**Documentation:**
- [ ] Add "Animation Tools" section to USAGE.md
- [ ] Document tweening usage
- [ ] Add animation examples

---

## Phase 6.6: Toolchain Integration

**Goal:** Integrate with modern retro development tools.

**Dependencies:** Phase 2 (SGDK)

**Timeline:** 2-3 weeks

### 6.6.1 Additional Platform Support

**Add support for:**

**Genesis/Mega Drive:**
- Marsdev (SGDK alternative)
- SGDK Studio integration

**NES:**
- cc65 compiler integration
- NESASM assembler
- NES Screen Tool CLI

**SNES:**
- bass assembler
- Asar assembler

**Game Boy:**
- GBDK-2020 integration
- BGB debugger API

### 6.6.2 Modern Engine Export

**Add export formats for:**
- Unity (sprite sheets + JSON metadata)
- Godot (.tres/.res resources)
- Love2D (Lua tables)
- Defold (sprite atlases)

---

### 6.6.3 Code Hygiene (Phase 6.6)

**Tasks:**
- [ ] Create unified exporter interface
- [ ] Add platform detection
- [ ] Refactor cross_platform.py with new formats
- [ ] Add toolchain validation

**Testing:**
- [ ] Integration tests for each platform
- [ ] Test exports with actual toolchains
- [ ] Validate output formats

**Documentation:**
- [ ] Add "Platform Support" section to USAGE.md
- [ ] Document each toolchain integration
- [ ] Add export format examples

---

## Phase 6.7: Infrastructure & Extensibility

**Goal:** Plugin system, web preview, CI/CD integration.

**Dependencies:** All previous phases

**Timeline:** 3-4 weeks

### 6.7.1 Plugin Architecture

**File:** `tools/pipeline/plugins/plugin_system.py` (NEW)

**Purpose:** Allow community contributions without forking.

**Implementation:**

```python
from typing import Callable, Dict, Any
from pathlib import Path
import importlib.util

class PipelinePlugin:
    """
    Base class for pipeline plugins.

    Hooks available:
    - on_image_load(img) -> img
    - on_palette_extract(palette) -> palette
    - on_tile_optimize(tiles) -> tiles
    - on_export(data) -> data
    """

    name: str = "unnamed_plugin"
    version: str = "1.0.0"

    def on_image_load(self, img: Image.Image) -> Image.Image:
        """Called after image load, before processing."""
        return img

    def on_palette_extract(self, palette: List[Tuple[int, int, int]]) -> List[Tuple[int, int, int]]:
        """Called after palette extraction."""
        return palette

    def on_tile_optimize(self, tiles: List) -> List:
        """Called during tile optimization."""
        return tiles

    def on_export(self, data: Any) -> Any:
        """Called before final export."""
        return data

class PluginManager:
    """Load and manage plugins."""

    def __init__(self, plugin_dir: str = "tools/pipeline/plugins"):
        self.plugin_dir = Path(plugin_dir)
        self.plugins: Dict[str, PipelinePlugin] = {}

    def load_plugins(self):
        """Load all plugins from plugin directory."""
        for plugin_file in self.plugin_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue

            plugin = self._load_plugin(plugin_file)
            if plugin:
                self.plugins[plugin.name] = plugin
                print(f"✓ Loaded plugin: {plugin.name} v{plugin.version}")

    def _load_plugin(self, plugin_file: Path) -> Optional[PipelinePlugin]:
        """Load plugin from file."""
        spec = importlib.util.spec_from_file_location("plugin", plugin_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find PipelinePlugin subclass
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and issubclass(obj, PipelinePlugin) and obj != PipelinePlugin:
                return obj()

        return None
```

**Example Plugin:**

```python
# tools/pipeline/plugins/auto_sharpen.py
from ..plugins.plugin_system import PipelinePlugin
from PIL import ImageFilter

class AutoSharpenPlugin(PipelinePlugin):
    """Automatically sharpen sprites after processing."""

    name = "auto_sharpen"
    version = "1.0.0"

    def on_image_load(self, img):
        """Apply sharpening filter."""
        return img.filter(ImageFilter.SHARPEN)
```

### 6.7.2 Web Preview Server

**File:** `tools/pipeline/server/preview_server.py` (NEW)

**Purpose:** Web-based asset preview and approval system.

**Dependencies:**
```bash
pip install fastapi uvicorn jinja2
```

**Implementation:**

```python
from fastapi import FastAPI, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path

app = FastAPI(title="Asset Pipeline Preview")

# Mount static files
app.mount("/output", StaticFiles(directory="output"), name="output")

@app.get("/", response_class=HTMLResponse)
def preview_gallery():
    """Show gallery of all processed assets."""
    sprites = list(Path("output").glob("*.png"))

    html = """
    <html>
    <head><title>Asset Gallery</title></head>
    <body>
        <h1>Processed Assets</h1>
        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 20px;">
    """

    for sprite in sprites:
        html += f"""
        <div style="border: 1px solid #ccc; padding: 10px;">
            <img src="/output/{sprite.name}" style="max-width: 100%; image-rendering: pixelated;">
            <p>{sprite.name}</p>
            <button onclick="approve('{sprite.name}')">Approve</button>
        </div>
        """

    html += """
        </div>
    </body>
    </html>
    """

    return html

@app.post("/approve/{asset_name}")
def approve_asset(asset_name: str):
    """Mark asset as approved."""
    # Record approval in database
    return {"status": "approved", "asset": asset_name}

@app.post("/upload")
async def upload_asset(file: UploadFile):
    """Upload asset for processing."""
    # Save and trigger pipeline
    pass
```

**CLI:** `--preview-server --port 8000`

### 6.7.3 CI/CD Integration

**File:** `.github/workflows/asset_pipeline.yml` (NEW)

**Purpose:** Automate asset processing in CI/CD.

```yaml
name: Asset Pipeline

on:
  push:
    paths:
      - 'assets/**'
  pull_request:
    paths:
      - 'assets/**'

jobs:
  process-assets:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e tools/pipeline

      - name: Process changed assets
        run: |
          python -m tools.pipeline.batch --changed-only --output output/

      - name: Run visual regression tests
        run: |
          pytest tests/test_visual_regression.py

      - name: Upload processed assets
        uses: actions/upload-artifact@v3
        with:
          name: processed-assets
          path: output/

      - name: Comment on PR with preview
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '✅ Assets processed successfully. [View artifacts](https://github.com/${{ github.repository }}/actions/runs/${{ github.run_id }})'
            })
```

---

### 6.7.4 Code Hygiene (Phase 6.7)

**Tasks:**
- [ ] Add plugin sandboxing (safety)
- [ ] Add API authentication to web server
- [ ] Create CI/CD templates for multiple platforms (GitHub, GitLab, etc.)
- [ ] Add telemetry (optional, privacy-respecting)

**Testing:**
- [ ] Unit tests for plugin loading
- [ ] Integration test: full pipeline with plugins
- [ ] Test web server endpoints
- [ ] Test CI/CD workflow

**Documentation:**
- [ ] Add "Plugins" section to USAGE.md
- [ ] Document plugin development guide
- [ ] Add web server setup guide
- [ ] Create CI/CD integration guide

---

## Phase Summary & Refactor Checklist

After completing each phase, run this checklist:

### Code Quality Checklist

- [ ] **Type Hints:** All public functions have complete type hints
- [ ] **Docstrings:** All modules, classes, functions have docstrings with examples
- [ ] **Tests:** 90%+ coverage on core modules
- [ ] **No Duplication:** No copy-pasted code between modules
- [ ] **Consistent Naming:** snake_case functions, PascalCase classes
- [ ] **Error Handling:** All errors use pipeline exception hierarchy
- [ ] **Logging:** All operations use structured logging
- [ ] **Security:** All paths validated, no injection vulnerabilities

### Documentation Checklist

- [ ] **USAGE.md:** Module section added with examples
- [ ] **CHANGELOG.md:** Entry added for user-visible changes
- [ ] **README.md:** Updated if public API changed
- [ ] **Examples:** At least 2 examples per major feature
- [ ] **Common Issues:** Known gotchas documented

### Integration Checklist

- [ ] **Backward Compatible:** Existing code still works
- [ ] **CLI Updated:** New flags added and documented
- [ ] **Config Schema:** Updated if new options added
- [ ] **Database Migration:** Alembic migration if schema changed
- [ ] **Plugin Hooks:** New plugin hooks added where appropriate

### Performance Checklist

- [ ] **Benchmarks:** Performance measured vs baseline
- [ ] **Memory:** No memory leaks (tested with large batches)
- [ ] **Optimization:** Bottlenecks profiled and optimized
- [ ] **Caching:** Expensive operations cached appropriately

---

## Implementation Priority

**Immediate Impact (Start Here):**
1. Phase 6.1.3: Tile Deduplication (Genesis VRAM savings)
2. Phase 6.2.2: Watch Mode (artist workflow)
3. Phase 6.3.1: Real-ESRGAN (quality improvement)

**High Value (Next):**
4. Phase 6.1.1: Sprite Packing
5. Phase 6.1.2: Advanced Compression
6. Phase 6.2.1: Asset Database

**Medium Term:**
7. Phase 6.3.2: SAM Segmentation
8. Phase 6.3.3: Visual Regression Testing
9. Phase 6.4: Palette Tools

**Polish (After core features):**
10. Phase 6.5: Animation Enhancement
11. Phase 6.6: Toolchain Integration
12. Phase 6.7: Infrastructure

---

**Ready to start implementation?** Which phase would you like to tackle first? I recommend starting with **Phase 6.1.3 (Tile Deduplication)** since you already have basic logic to expand, and it directly impacts your Genesis game's VRAM budget!

**Goal:** React-based GUI wrapping all CLI functionality.

**Dependencies:** All prior phases complete (Phase 1-6.7)

### Prerequisites

- All CLI features work standalone
- Core pipeline with event system operational (Phase 0.9)
- API server uses core pipeline (not CLI wrapper)
- WebSocket support for real-time progress via EventEmitter

### Architecture

```
┌─────────────────────────────────────────────────┐
│                 Workshop.OS GUI                  │
│  (React 18 + Vite + TanStack + Zustand)         │
├─────────────────────────────────────────────────┤
│                 Python Backend                   │
│      (FastAPI wrapping core/pipeline.py)        │
├─────────────────────────────────────────────────┤
│               core/pipeline.py                   │
│    ┌─────────────────────────────────────┐      │
│    │  EventEmitter → WebSocket bridge    │      │
│    │  - PROGRESS events → client updates │      │
│    │  - STAGE events → step indicators   │      │
│    │  - ERROR events → error toasts      │      │
│    └─────────────────────────────────────┘      │
├─────────────────────────────────────────────────┤
│            Enforced Safeguards Layer             │
│  (Budget, Caching, Validation - CANNOT bypass)  │
└─────────────────────────────────────────────────┘

         CLI (cli.py)                GUI (api/)
              │                          │
              └──────────┬───────────────┘
                         ▼
               core/pipeline.py
                         │
            ┌────────────┼────────────┐
            ▼            ▼            ▼
        safeguards   events.py    stages
```

### Event-to-WebSocket Bridge

The GUI connects to the core pipeline's event system:

```python
# api/server.py
from tools.pipeline.core import Pipeline, EventEmitter, EventType

@app.websocket("/api/progress/{job_id}")
async def progress_websocket(websocket: WebSocket, job_id: str):
    emitter = EventEmitter()

    # Bridge events to WebSocket
    async def on_progress(event):
        await websocket.send_json({
            "type": "progress",
            "percent": event.percent,
            "message": event.message
        })

    emitter.on(EventType.PROGRESS, on_progress)
    emitter.on(EventType.STAGE_START, lambda e: websocket.send_json(...))

    pipeline = Pipeline(config, event_emitter=emitter)
    result = await run_in_executor(pipeline.process, ...)
```

### API Endpoints

```
POST /api/process       - Run pipeline (returns job_id)
POST /api/generate      - Generate from prompt
POST /api/validate      - Pre-flight validation
GET  /api/status        - Pipeline status (budget, cache)
GET  /api/palettes      - List available palettes
GET  /api/platforms     - List supported platforms
WS   /api/progress/:id  - Real-time job progress via EventEmitter
```

### GUI Components

- Sprite sheet grid viewer
- Animation preview player
- Collision box editor (drag handles)
- Palette picker
- SGDK validation panel
- Before/after comparison
- **Budget indicator** (generations remaining, cost)
- **Dry-run toggle** (preview mode switch)

### Phase 6 Quality Gates

- [ ] **Tests**: API endpoint tests, WebSocket integration tests, React component tests
- [ ] **Docs**: API reference auto-generated from OpenAPI spec
- [ ] **USAGE.md**: GUI usage section, API examples
- [ ] **Types**: TypeScript types generated from Python dataclasses
- [ ] **CLI**: GUI launch documented (`--serve`, `--gui`)
- [ ] **Integration**: 100% CLI feature parity verified
- [ ] **Review**: Accessibility audit, responsive design tested

**Phase 6 Tasks:**

- [ ] FastAPI server wrapping pipeline (`api/server.py`)
- [ ] WebSocket progress streaming (`api/websocket.py`)
- [ ] React frontend with sprite viewer
- [ ] Collision box editor with drag handles
- [ ] Palette picker component
- [ ] Before/after comparison view

---

## Testing Strategy

### Unit Tests

- `SGDKFormatter` with known inputs → validate output
- Palette quantization roundtrip
- Validation catches all error cases
- 4bpp tile generation produces correct bytes
- Animation extraction from names

### Integration Tests

- Process real sprite sheet end-to-end
- Export to all supported formats
- rescomp compilation succeeds
- API endpoints return expected data

### Visual Regression

- Compare output images to known-good references
- Diff tolerance for AI-generated content

---

## CLI Reference

### Core Pipeline (Recommended)

The new core pipeline provides enforced safeguards and is the recommended entry point:

```bash
# Check pipeline status
python -m tools.pipeline.cli --status

# Basic processing (dry-run by default - SAFE!)
python -m tools.pipeline.cli sprite.png -o output/

# Actually process (requires explicit --no-dry-run)
python -m tools.pipeline.cli sprite.png -o output/ --no-dry-run

# Process Aseprite file (auto-detected)
python -m tools.pipeline.cli character.ase -o output/ --no-dry-run

# Generate from prompt
python -m tools.pipeline.cli "warrior with sword" -o output/ --generate --no-dry-run

# Generate 8-direction character
python -m tools.pipeline.cli "warrior with sword" -o output/ --generate --8dir --no-dry-run

# Batch process directory
python -m tools.pipeline.cli --batch gfx/input/ -o gfx/output/ --no-dry-run

# Custom budget limits
python -m tools.pipeline.cli "sprite prompt" -o output/ --generate --max-gens 10 --max-cost 1.00

# Skip confirmation prompts (for scripts)
python -m tools.pipeline.cli sprite.png -o output/ --no-dry-run --no-confirm

# Save/load configuration
python -m tools.pipeline.cli --save-config my_config.json
python -m tools.pipeline.cli sprite.png -o output/ --config my_config.json

# Specify AI provider
python -m tools.pipeline.cli sprite.png -o output/ --ai groq
python -m tools.pipeline.cli sprite.png -o output/ --offline  # No AI

# Full example with all options
python -m tools.pipeline.cli sprite.png \
    -o output/ \
    --platform genesis \
    --size 32 \
    --palette player_warm \
    --category player \
    --collision \
    --no-dry-run \
    --no-confirm \
    --verbose
```

**Safeguard Flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `--no-dry-run` | OFF (dry-run ON) | Enable real operations (required for writes) |
| `--no-confirm` | OFF | Skip interactive confirmation prompts |
| `--max-gens N` | 5 | Maximum AI generations per run |
| `--max-cost N` | 0.50 | Maximum cost in USD per run |

### Legacy Pipeline (unified_pipeline.py)

```bash
# Basic processing
python unified_pipeline.py input.png --platform genesis --output out/

# Animation extraction
python unified_pipeline.py sheet.png --animations --output anims.h

# Sprite sheet assembly
python unified_pipeline.py frames/*.png --assemble-sheet --output sheet.png

# SGDK resource generation
python unified_pipeline.py res/*.png --platform genesis --generate-res

# Performance analysis
python unified_pipeline.py scene.png --platform genesis --performance-report

# Tile optimization with mirroring
python unified_pipeline.py tileset.png --platform genesis --optimize-mirrors

# Palette conversion
python unified_pipeline.py --convert-palette input.png --to genesis

# Effect generation
python unified_pipeline.py sprite.png --hit-flash --damage-tint

# 8-direction rotation
python unified_pipeline.py sprite.png --rotate-8dir ai

# Batch processing
python unified_pipeline.py --batch --input-dir assets/ --output-dir out/

# Full pipeline with all features
python unified_pipeline.py input.png \
    --platform genesis \
    --animations \
    --generate-res \
    --performance-report \
    --optimize-mirrors \
    --verbose

# --- Perceptual Color Science (1.8) ---
# Quantization with perceptual color matching
python unified_pipeline.py input.png --quantize-method ciede2000
python unified_pipeline.py input.png --quantize-method cam02-ucs

# Dithering algorithms (Numba-accelerated)
python unified_pipeline.py input.png --dither floyd-steinberg
python unified_pipeline.py input.png --dither ordered-8x8
python unified_pipeline.py input.png --dither atkinson

# --- Aseprite Integration (1.9) ---
# Import from Aseprite file directly
python unified_pipeline.py sprite.aseprite --from-aseprite --output out/

# Split layers into separate sprites
python unified_pipeline.py character.aseprite --from-aseprite --ase-split-layers

# Export animation tags separately
python unified_pipeline.py character.aseprite --from-aseprite --ase-split-tags

# --- Tilemap Editor Integration (2.6) ---
# Import Tiled .tmx maps
python unified_pipeline.py level.tmx --import-tiled --platform genesis

# Import LDtk projects
python unified_pipeline.py world.ldtk --import-ldtk --platform genesis

# Process specific map layer
python unified_pipeline.py level.tmx --import-tiled --map-layer collision

# --- Audio Pipeline Tools (2.7) ---
# Convert VGM to XGM for SGDK
python unified_pipeline.py music.vgm --convert-vgm --output music.xgm

# Validate VGM file structure
python unified_pipeline.py music.vgm --validate-vgm

# Specify FM instrument bank
python unified_pipeline.py music.vgm --convert-vgm --wopn-bank instruments.wopn

# --- Genesis Compression (2.8) ---
# Compress graphics data (Kosinski default)
python unified_pipeline.py tileset.bin --compress --output tileset.kos

# Compress with specific format
python unified_pipeline.py tileset.bin --compress nemesis --output tileset.nem
python unified_pipeline.py tileset.bin --compress lzss --output tileset.lz

# Decompress for editing
python unified_pipeline.py tileset.kos --decompress --output tileset.bin

# --- Alternative AI Providers (3.6) ---
# Use Pixie.haus for AI upscaling
python unified_pipeline.py input.png --ai-provider pixie-haus --upscale 2x

# Use local Stable Diffusion
python unified_pipeline.py input.png --ai-provider stable-diffusion-local

# Use PixAI service
python unified_pipeline.py input.png --ai-provider pixai

# --- Scene Composition (4.4) ---
# Render scene to PNG
python unified_pipeline.py --compose-scene scene.json --output screenshot.png

# Render with scaling for promotional use
python unified_pipeline.py --compose-scene scene.json --scale 2 --output promo.png

# Render animated scene to GIF
python unified_pipeline.py --compose-scene scene.json --animated --fps 12 --output preview.gif

# Show grid overlay for alignment
python unified_pipeline.py --compose-scene scene.json --show-grid --output debug.png
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-10 | Initial plan |
| 2.0 | 2026-01-15 | Added Phase 1.7, 1.8, 2.0 expansions |
| 3.0 | 2026-01-16 | **Complete reorganization**: Consolidated duplicates, logical phase ordering, clear dependencies |
| 3.1 | 2026-01-17 | **Status update**: Marked Phases 1-4 implementations as complete, added audio.py and maps.py |
| 3.2 | 2026-01-17 | **Quality expansion**: Added 5.7-5.11 (Code Standards, Testing, Docs, Refactoring, GUI-Readiness) |
| 3.3 | 2026-01-17 | **Standards restructure**: Moved quality standards to "Development Standards (Apply Throughout)" section |
| 3.4 | 2026-01-17 | **Consolidation**: Removed verbose 5.7-5.11 sections (now condensed at top); Phase 5 focuses on hardening only |
| 3.5 | 2026-01-17 | **Quality Gates**: Added per-phase quality gates with tests, docs, types, CLI, integration, and review checklists |
| 3.6 | 2026-01-17 | **Tool Integration**: Added 1.8 (colour-science/Numba dithering), 1.9 (Aseprite CLI), 2.6 (Tiled/LDtk), 2.7 (xgmtool/VGM), 2.8 (Kosinski compression), 3.6 (Pixie.haus/SD local) |
| 3.7 | 2026-01-17 | **Audit Fixes**: Expanded 4.4 Scene Composition with full spec, added 18 missing CLI flags to reference, updated Phase 4 status to "Mostly Complete" |
| 3.8 | 2026-01-17 | **Foundational Refactor**: Renamed to "Asset Pipeline" (covers graphics, audio, tilemaps); moved Perceptual Color Science (0.7) and Numba Dithering (0.8) to Phase 0 as foundational; renumbered Aseprite Integration to 1.8; restored Phase 4 dependency on Phase 3 (cross-platform uses AI) |
| 3.9 | 2026-01-17 | **Documentation Integration**: Created USAGE.md as living document; expanded Documentation (Continuous) section with USAGE.md practices; added USAGE.md checkboxes to all Phase Quality Gates |

---

## Migration Notes (v2.0 → v3.0)

| Old Location | New Location | Notes |
|--------------|--------------|-------|
| Phase 1.1 (Hit Flash) | Phase 1.3 | Same feature |
| Phase 1.2 (Rotation) | Phase 1.4 | Same feature |
| Phase 1.7.1 (Layout) | Phase 1.2 | Merged with 2.0.2 |
| Phase 1.7.3 (Animation) | Phase 1.1 | Merged with 2.0.1 |
| Phase 1.7.5 (Rotation) | Phase 1.4 | Merged |
| Phase 1.8 (Hardening) | Phase 5 | Standalone phase |
| Phase 2.0.1-2.0.4 | Phase 1.1-1.6 | Tier 1 → Core Features |
| Phase 2.1.1-2.1.3 | Phase 2.1-2.3 | Tier 2 → SGDK Integration |
| Phase 2.2.1-2.2.3 | Phase 4.1-4.3 | Tier 3 → Advanced Tools |
| Phase 2.4 (Palette) | Phase 1.6 | Merged with 2.0.4 |
| Phase 3 (GUI) | Phase 6 | Moved to end |

---

## Approval

- [ ] Phase structure approved
- [ ] Implementation order approved
- [ ] Ready to begin Phase 1 implementation
