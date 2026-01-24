# ARDK Asset Pipeline

Unified asset processing pipeline for retro game development.

**Version:** 3.4.0
**Last Updated:** 2026-01-24

## Quick Start

```bash
# Process a sprite (dry-run by default)
python -m pipeline.cli sprite.png -o output/

# Use project config (.ardk.yaml)
python optimize_tiles.py sprite.png --config ../.ardk.yaml

# Watch for changes with progress reporting
python watch_assets.py assets/sprites --processor sprite

# Optimize tiles with JSON output for CI/CD
python optimize_tiles.py tileset.png --json report.json --summary
```

## Documentation

- **[USAGE.md](USAGE.md)** - Complete module reference
- **[../DEPRECATED.md](../DEPRECATED.md)** - Deprecated scripts and migration guide
- **[../.ardk.yaml](../.ardk.yaml)** - Project configuration example

## Directory Structure

```
pipeline/
├── core/                    # Core architecture
│   ├── __init__.py          # Core exports
│   ├── pipeline.py          # Main pipeline orchestrator
│   ├── safeguards.py        # Safety enforcement
│   ├── events.py            # Event system for GUI
│   └── config.py            # Configuration dataclasses
│
├── cli_utils.py             # Shared CLI utilities (NEW)
├── reporting.py             # Progress & summary reporting (NEW)
│
├── optimization/            # Asset optimization
│   └── tile_optimizer.py    # Tile deduplication with flip detection
│
├── watch/                   # File watching
│   └── file_watcher.py      # Debouncing, rate limiting, circuit breaker
│
├── quantization/            # Color quantization
│   ├── perceptual.py        # Perceptual color reduction
│   └── dither_numba.py      # JIT-compiled dithering
│
├── ai_providers/            # AI generation backends
│   ├── pollinations.py      # Free Flux provider
│   ├── stable_diffusion.py  # SD/ComfyUI provider
│   └── pixie_haus.py        # Pixie Haus provider
│
├── palettes/                # Platform palettes
│   └── genesis_palettes.py  # Genesis/Mega Drive colors
│
├── integrations/            # External tool integrations
│   └── aseprite.py          # Aseprite file support
│
├── genesis_compression/     # Compression algorithms
│   └── genesis_compress.py  # RLE, LZ77, Kosinski
│
├── vgm/                     # Audio tools
│   └── vgm_tools.py         # VGM file manipulation
│
├── tests/                   # Test suite
│   └── *.py                 # pytest tests
│
├── animation.py             # Animation extraction
├── animation_fsm.py         # State machine animations
├── audio.py                 # Audio pipeline
├── cli.py                   # Command-line interface
├── collision_editor.py      # Collision box editing
├── cross_platform.py        # Multi-platform export
├── effects.py               # Sprite effects (glow, outline)
├── errors.py                # Exception classes
├── fallback.py              # Fallback analysis
├── genesis_export.py        # Genesis-specific export
├── maps.py                  # Tiled map support
├── metrics.py               # Performance metrics
├── palette_converter.py     # Palette conversion
├── palette_manager.py       # Palette management
├── performance.py           # VRAM/cycle analysis
├── platforms.py             # Platform configurations
├── processing.py            # Image processing
├── resources.py             # Resource management
├── rotation.py              # Sprite rotation
├── security.py              # Security hardening
├── sgdk_format.py           # SGDK formatting
├── sgdk_resources.py        # SGDK resource generation
├── sheet_assembler.py       # Sprite sheet assembly
├── sprite_mirror_util.py    # Mirror optimization
├── style.py                 # Style system
├── validation.py            # Asset validation
└── USAGE.md                 # Detailed documentation
```

## Configuration System

### Project Config (.ardk.yaml)

Create `.ardk.yaml` in your project root:

```yaml
# Platform target
platform: genesis

# Directory paths
paths:
  sprites: gfx/sprites
  backgrounds: gfx/backgrounds
  generated: gfx/generated
  output: src/game/assets

# Platform palettes
palettes:
  player: [0x0F, 0x15, 0x21, 0x30]
  enemy: [0x0F, 0x06, 0x16, 0x30]

# Safety settings
safeguards:
  dry_run: true
  max_generations_per_run: 5
  max_cost_per_run: 1.00
```

### Loading Config

```python
from pipeline.core import get_config, load_project_config

# Auto-discover .ardk.yaml
config = get_config()

# Load specific config file
config = load_project_config("path/to/.ardk.yaml")
```

## CLI Tools

| Tool | Purpose | Module |
|------|---------|--------|
| `python -m pipeline.cli` | Main pipeline | `cli.py` |
| `python optimize_tiles.py` | Tile optimization | `optimization/` |
| `python watch_assets.py` | File watching | `watch/` |
| `python make_spritesheet.py` | Sheet assembly | `sheet_assembler.py` |

### Standard CLI Arguments

All tools support these arguments via `cli_utils.py`:

```
Configuration:
  --config/-c FILE     Config file path (default: auto-discover .ardk.yaml)
  --platform/-p        Target platform (nes, genesis, snes, gameboy, etc.)

Output:
  --output/-o DIR      Output directory
  --dry-run/-n         Preview mode (no writes)

Verbosity:
  --verbose/-v         Increase verbosity (-v info, -vv debug)
  --quiet/-q           Suppress non-essential output

Reporting:
  --json [FILE]        Output JSON report (- for stdout)
  --summary            Show detailed summary at end
  --progress           Show progress bar (default: enabled)
  --no-progress        Disable progress bar
```

## Key Features

### Safety Enforcement

```python
from pipeline.core import Pipeline, SafeguardConfig

config = SafeguardConfig(
    dry_run=True,              # Preview only (default)
    max_generations=5,         # Limit AI calls
    max_cost_usd=0.50,         # Budget cap
    require_confirmation=True  # Interactive approval
)

pipeline = Pipeline(safeguards=config)
result = pipeline.process("sprite.png")  # Safe by default
```

### Progress & Reporting

```python
from pipeline.cli_utils import CLIReporter, create_reporter
from pipeline.reporting import ProgressTracker, SummaryReport

# CLI integration
reporter = create_reporter(args, verbosity=1, total_items=10, title="Processing")
for item in items:
    result = process(item)
    reporter.success(item, data={"tiles": result.tiles})
    reporter.advance()
exit_code = reporter.finish()

# Standalone progress bar
with ProgressTracker(total=100, description="Optimizing") as progress:
    for i in range(100):
        do_work()
        progress.advance()
```

### JSON Output for CI/CD

```bash
# Generate machine-readable report
python optimize_tiles.py assets/*.png --batch --json report.json

# Pipe to jq for processing
python optimize_tiles.py sprite.png --json - | jq '.results'
```

### Tile Optimization

```python
from pipeline.optimization import TileOptimizer

optimizer = TileOptimizer(
    tile_width=8,
    tile_height=8,
    allow_mirror_x=True,
    allow_mirror_y=True,
    platform='genesis'
)

result = optimizer.optimize_sprite_sheet("tileset.png")
print(f"Reduced to {result.unique_tile_count} unique tiles")
print(f"VRAM usage: {result.stats.vram_bytes} bytes")
```

### File Watching with Safety

```python
from pipeline.watch import AssetWatcher, WatchConfig, SafetyConfig

safety = SafetyConfig(
    max_file_size_mb=50.0,
    max_changes_per_minute=60,
    circuit_breaker_errors=5
)

config = WatchConfig(
    watch_dirs=['assets/'],
    extensions=['.png', '.aseprite'],
    safety=safety
)

watcher = AssetWatcher(config)
watcher.on_change = process_asset
watcher.start()
```

### Event System (GUI Integration)

```python
from pipeline.core import Pipeline, EventEmitter, EventType

emitter = EventEmitter()

@emitter.on(EventType.PROGRESS)
def on_progress(event):
    print(f"Progress: {event.percent}% - {event.message}")

@emitter.on(EventType.STAGE_COMPLETE)
def on_stage(event):
    print(f"Stage {event.stage_name} complete")

pipeline = Pipeline(config, event_emitter=emitter)
```

## Platform Support

| Platform | Config | Palette | Export |
|----------|--------|---------|--------|
| Genesis/MD | `genesis` | 64 colors | SGDK |
| NES | `nes` | 54 colors | CHR |
| SNES | `snes` | 256 colors | - |
| Game Boy | `gameboy` | 4 colors | - |
| SMS | `sms` | 64 colors | - |
| PC Engine | `pce` | 512 colors | - |
| Amiga | `amiga` | 4096 colors | - |

## Testing

```bash
cd tools
python -m pytest pipeline/tests/ -v

# Run specific tests
python -m pytest pipeline/tests/test_tile_optimizer.py -v
python -m pytest tests/test_file_watcher.py -v
```

## Dependencies

```bash
# Core
pip install pillow numpy pyyaml

# Optional: AI features
pip install openai anthropic

# Optional: Performance (JIT dithering)
pip install numba colour-science

# Optional: File watching
pip install watchdog

# Optional: Progress bars
pip install tqdm

# Optional: Audio
pip install pydub scipy
```

## Version History

- **3.4.0** - Unified configuration (.ardk.yaml), CLI utilities, Progress & Reporting
- **3.3.0** - Watch mode safety (rate limiting, circuit breaker, timeouts)
- **3.2.0** - Tile optimization with VRAM tracking
- **3.0.0** - Core architecture with enforced safeguards
- **2.0.0** - Phase 2 complete (SGDK, performance, cross-platform)

---

See [USAGE.md](USAGE.md) for complete module documentation.
