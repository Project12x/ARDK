# Asset Pipeline Handoff Report

**Date:** 2026-01-24
**Version:** 3.4.0
**Scope:** `tools/` directory - Asset processing pipeline for retro game development

---

## Executive Summary

The ARDK asset pipeline processes sprites, backgrounds, and audio for retro platforms (Genesis, NES, SNES, etc.). It features:

- **Unified configuration** via `.ardk.yaml`
- **Consistent CLI** across all tools
- **Progress reporting** with JSON output for CI/CD
- **GUI-ready event system** for React/Electron integration
- **Safety safeguards** (dry-run, rate limiting, budget caps)

---

## Quick Start

```bash
cd tools

# Install dependencies
pip install pillow numpy pyyaml watchdog tqdm

# Test imports
python -c "from pipeline.core import get_config; print(get_config())"

# Run tile optimizer
python optimize_tiles.py ../gfx/sprites/player.png --output out/ --summary

# Watch for changes
python watch_assets.py ../gfx/sprites --processor sprite
```

---

## Architecture Overview

```
tools/
├── .ardk.yaml                 # Project configuration
├── pipeline/
│   ├── core/                  # Core architecture
│   │   ├── config.py          # PipelineConfig, PathsConfig, WatchConfig
│   │   ├── events.py          # EventEmitter, EventType (GUI integration)
│   │   ├── pipeline.py        # Main Pipeline class
│   │   └── safeguards.py      # DryRun, budget limits, rate limiting
│   │
│   ├── cli_utils.py           # Shared CLI argument handling
│   ├── reporting.py           # ProgressTracker, SummaryReport, JSONReporter
│   │
│   ├── optimization/          # Tile deduplication
│   ├── watch/                 # File watching with circuit breaker
│   ├── quantization/          # Perceptual color science, dithering
│   ├── ai_providers/          # Pollinations, SD, PixieHaus
│   ├── integrations/          # Aseprite support
│   │
│   └── [30+ specialized modules]
│
├── optimize_tiles.py          # CLI: Tile optimization
├── watch_assets.py            # CLI: Asset file watcher
├── make_spritesheet.py        # CLI: Sprite sheet assembly
└── asset_generators/          # AI-powered asset generation
```

---

## Key Files for New Developer

| File | Purpose | Read First? |
|------|---------|-------------|
| `.ardk.yaml` | Project configuration | Yes |
| `pipeline/core/config.py` | All config dataclasses | Yes |
| `pipeline/cli_utils.py` | CLI argument patterns | Yes |
| `pipeline/core/events.py` | Event system for GUI | If doing GUI |
| `pipeline/core/pipeline.py` | Main orchestrator | For deep dive |
| `pipeline/README.md` | Full documentation | Reference |

---

## Configuration System

### .ardk.yaml

Located at `tools/.ardk.yaml`, auto-discovered by walking up from CWD:

```yaml
platform: nes

paths:
  sprites: gfx/sprites
  generated: gfx/generated
  output: src/game/assets
  cache: .ardk_cache

palettes:
  player: [0x0F, 0x15, 0x21, 0x30]
  enemy: [0x0F, 0x06, 0x16, 0x30]

safeguards:
  dry_run: true
  max_generations_per_run: 5
  max_cost_per_run: 1.00

watch:
  debounce: 1.0
  max_rate: 60
  timeout: 30.0
```

### Loading in Code

```python
from pipeline.core import get_config, load_project_config, find_config_file

# Auto-discover and cache
config = get_config()

# Load specific file
config = load_project_config("path/to/config.yaml")

# Find config file path
config_path = find_config_file()  # Returns Path or None
```

---

## CLI Utilities

All CLI tools use shared utilities from `pipeline/cli_utils.py`:

```python
from pipeline.cli_utils import (
    create_parser,      # Consistent argparse setup
    add_common_args,    # --config, --output, --verbose, --json, etc.
    add_watch_args,     # --debounce, --max-rate, --timeout
    add_safety_args,    # --max-generations, --budget
    setup_from_args,    # Load config + apply CLI overrides
    VerbosePrinter,     # Context-aware printing
    CLIReporter,        # Progress + summary + JSON
)

# Example usage
parser = create_parser("My tool description")
add_common_args(parser)
args = parser.parse_args()
config, verbosity = setup_from_args(args)
```

### Standard Arguments

```
--config/-c FILE      Config file path
--platform/-p         Target platform
--output/-o DIR       Output directory
--dry-run/-n          Preview mode
--verbose/-v          Increase verbosity
--quiet/-q            Suppress output
--json [FILE]         JSON report (- for stdout)
--summary             Show detailed summary
--progress            Show progress bar
--no-progress         Disable progress bar
```

---

## Event System (GUI Integration)

The pipeline emits typed events for GUI integration:

```python
from pipeline.core import Pipeline, EventEmitter, EventType, ProgressEvent

emitter = EventEmitter()

# Register handlers
emitter.on(EventType.PROGRESS, lambda e: print(f"{e.percent}%"))
emitter.on(EventType.STAGE_START, lambda e: print(f"Starting: {e.stage_name}"))
emitter.on(EventType.GENERATION_COMPLETE, lambda e: print(f"Cost: ${e.data['cost']}"))

# Or receive all events
emitter.on_all(lambda e: send_to_websocket(e))

# Create pipeline with emitter
pipeline = Pipeline(config, event_emitter=emitter)
```

### Event Types

| Event | Data | When |
|-------|------|------|
| `PROGRESS` | percent, message, stage | During processing |
| `STAGE_START` | stage_name, index, total | Stage begins |
| `STAGE_COMPLETE` | stage_name, result | Stage ends |
| `PIPELINE_ERROR` | error_type, message | On error |
| `GENERATION_START` | prompt, provider | AI generation starts |
| `GENERATION_COMPLETE` | cost_usd, images | AI generation ends |
| `BUDGET_WARNING` | remaining | Budget running low |
| `DRY_RUN_BLOCKED` | action | Blocked by dry-run |

---

## Reporting System

### Progress Tracking

```python
from pipeline.reporting import ProgressTracker

with ProgressTracker(total=100, description="Processing") as progress:
    for item in items:
        process(item)
        progress.advance()
```

### Summary Reports

```python
from pipeline.reporting import SummaryReport

report = SummaryReport(title="Tile Optimization")
report.add_success("sprite1.png", data={"tiles": 12})
report.add_warning("sprite2.png", "Large file size")
report.add_error("sprite3.png", "Invalid format")
report.print_summary()
```

### JSON Output

```python
from pipeline.reporting import JSONReporter

reporter = JSONReporter(tool_name="optimize_tiles")
reporter.add_result("sprite.png", success=True, data={"tiles": 12})
reporter.save("report.json")  # Or reporter.print_json()
```

---

## Safety Safeguards

### Dry Run (Default ON)

```python
config.safeguards.dry_run = True  # Default
# All writes are simulated, nothing changes on disk
```

### Budget Limits

```python
config.safeguards.max_generations_per_run = 5
config.safeguards.max_cost_per_run = 1.00  # USD
```

### Rate Limiting (Watch Mode)

```python
config.watch.max_rate = 60          # Max changes per minute
config.watch.debounce = 1.0         # Seconds between processing
config.watch.circuit_breaker = 5    # Errors before shutdown
```

---

## Common Workflows

### 1. Process Single Sprite

```bash
python optimize_tiles.py sprite.png --output out/ --platform genesis
```

### 2. Batch Process Directory

```bash
python optimize_tiles.py gfx/sprites/*.png --batch --json report.json
```

### 3. Watch for Changes

```bash
python watch_assets.py gfx/sprites --processor sprite --debounce 2.0
```

### 4. Generate AI Assets (with safeguards)

```python
from pipeline.core import Pipeline

pipeline = Pipeline(config)
result = pipeline.generate("16x16 warrior sprite", "output/")
# Respects dry_run, budget, confirmation requirements
```

---

## Testing

```bash
cd tools
python -m pytest pipeline/tests/ -v

# Specific tests
python -m pytest pipeline/tests/test_tile_optimizer.py -v
python -m pytest tests/test_file_watcher.py -v
```

---

## Dependencies

```bash
# Required
pip install pillow numpy pyyaml

# Recommended
pip install watchdog tqdm

# Optional
pip install numba colour-science  # JIT dithering
pip install openai anthropic      # AI features
pip install pydub scipy           # Audio
```

---

## GUI Integration Checklist

For React/Electron integration:

- [x] Event system ready (`EventEmitter` in `core/events.py`)
- [x] JSON output supported (`--json` flag, `JSONReporter`)
- [x] Config serializable (`PipelineConfig.to_dict()`)
- [x] Progress streaming ready (`ProgressEvent` emitted)

**Missing for full GUI:**
- [ ] HTTP API wrapper (FastAPI/Flask)
- [ ] WebSocket for real-time events
- [ ] File upload endpoint

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 3.4.0 | 2026-01-24 | Config system, CLI utils, Progress reporting |
| 3.3.0 | 2026-01-19 | Watch mode safety (circuit breaker, rate limit) |
| 3.2.0 | 2026-01-17 | Tile optimization with VRAM tracking |
| 3.0.0 | 2026-01-16 | Core architecture, enforced safeguards |

---

## Contact

For pipeline architecture questions, reference this handoff document and the inline documentation in each module.
