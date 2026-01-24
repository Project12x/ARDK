# ARDK Asset Pipeline - Usage Guide

> **Version**: 2.0.0
> **Last Updated**: 2026-01-18
> **Status**: Living Document - Updated with each feature

This document grows alongside the codebase. Each module section is updated when features are implemented or discovered.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Module Reference](#module-reference)
   - [Animation](#animation-module)
   - [Sheet Assembly](#sheet-assembly-module)
   - [Palette Conversion](#palette-conversion-module)
   - [Genesis Export](#genesis-export-module)
   - [SGDK Resources](#sgdk-resources-module)
   - [Palette Manager](#palette-manager-module)
   - [Performance Analysis](#performance-analysis-module)
   - [Collision Editor](#collision-editor-module)
   - [Animation FSM](#animation-fsm-module)
   - [Cross-Platform Export](#cross-platform-export-module)
   - [Tiled Maps](#tiled-maps-module)
   - [Audio Pipeline](#audio-pipeline-module)
   - [VGM Tools](#vgm-tools-module)
   - [AI Generation Providers](#ai-generation-providers-module) *(NEW)*
   - [Compression](#compression-module)
   - [Optimization](#optimization-module) *(NEW - Phase 6.1)*
   - [Watch](#watch-module) *(NEW - Phase 6.2)*
   - [Processing](#processing-module) *(NEW)*
   - [AI Integration](#ai-integration-module) *(NEW)*
   - [Fallback Analysis](#fallback-analysis-module) *(NEW)*
   - [Style System](#style-system-module) *(NEW)*
   - [AI Generation](#ai-generation-module) *(NEW)*
   - [Quantization](#quantization-module) *(NEW)*
   - [Sprite Effects](#sprite-effects-module) *(NEW)*
   - [Aseprite Integration](#aseprite-integration-module) *(NEW)*
   - [Core Architecture](#core-architecture) *(NEW)*
4. [Feature Status](#feature-status)
5. [Common Workflows](#common-workflows)
6. [CLI Reference](#cli-reference)
7. [Troubleshooting](#troubleshooting)
8. [Known Issues & Workarounds](#known-issues--workarounds)
9. [Contributing](#contributing)

---

## Quick Start

```python
from tools.pipeline import (
    # Animation
    AnimationExtractor, export_sgdk_animations,
    # Sprites
    SpriteSheetAssembler, dissect_sheet,
    # SGDK
    SGDKResourceGenerator, generate_resources_from_directory,
    # Performance
    analyze_sprite_performance,
)

# Extract animations from a sprite sheet
extractor = AnimationExtractor()
sequences = extractor.extract_from_sheet("player.png", frame_size=(32, 32))
export_sgdk_animations(sequences, "res/player_anims.h")

# Generate SGDK resource file
generator = SGDKResourceGenerator(output_dir="res/")
generator.add_sprite("player", "sprites/player.png", width=32, height=32)
generator.write_resource_file("resources.res")
```

---

## Installation

### Prerequisites

```bash
# Core dependencies
pip install pillow numpy

# Optional: AI-powered features
pip install openai anthropic

# Optional: Performance features (Phase 0.7-0.8)
pip install colour-science colorspacious numba

# Optional: Audio conversion
pip install pydub scipy
```

### Project Structure

```
tools/pipeline/
├── __init__.py           # Main exports
├── animation.py          # Animation extraction (1.1)
├── sheet_assembler.py    # Sheet assembly/dissection (1.2)
├── palette_converter.py  # Palette conversion (1.6)
├── palette_manager.py    # Game-wide palette management
├── genesis_export.py     # Genesis tile export (0.6)
├── sgdk_format.py        # SGDK formatting (0.1)
├── sgdk_resources.py     # Resource file generation (2.1)
├── performance.py        # Performance analysis (2.3)
├── collision_editor.py   # Collision visualization (4.2)
├── animation_fsm.py      # FSM code generation (4.1)
├── cross_platform.py     # Multi-platform export (4.3)
├── maps.py               # Tiled map support
├── audio.py              # Audio conversion
├── vgm/                  # VGM/XGM tools (2.7)
│   ├── __init__.py
│   └── vgm_tools.py      # VGM parsing, XGM conversion, WOPN banks
├── genesis_compression/  # Genesis compression (2.8)
│   ├── __init__.py
│   └── genesis_compress.py
├── ai_providers/         # AI generation providers (3.6)
│   ├── __init__.py
│   ├── base.py           # GenerationProvider interface
│   ├── pollinations.py   # Pollinations.ai provider
│   ├── pixie_haus.py     # Pixie.haus provider
│   ├── stable_diffusion.py  # Local SD provider
│   └── registry.py       # Provider registry & fallback
├── ai.py                 # AI provider integration
├── platforms.py          # Platform configurations
├── processing.py         # Image processing
├── style.py              # Style transfer
├── fallback.py           # AI fallback processing
└── quantization/         # Perceptual color science (0.7-0.8)
    ├── __init__.py
    ├── perceptual.py     # CIEDE2000, Lab color, palette extraction
    └── dither_numba.py   # JIT-accelerated dithering
```

---

## Module Reference

### Animation Module

**File:** `animation.py`
**Phase:** 1.1 (Complete)

Extract animation sequences from sprite sheets and generate SGDK-compatible headers.

#### Key Classes

```python
from tools.pipeline import AnimationExtractor, AnimationSequence

# Extract from grid-based sprite sheet
extractor = AnimationExtractor()
sequences = extractor.extract_from_sheet(
    image_path="player.png",
    frame_size=(32, 32),      # Width x Height per frame
    rows=4,                    # Optional: override detection
    cols=8                     # Optional: override detection
)

# Access sequence data
for seq in sequences:
    print(f"{seq.name}: {len(seq.frames)} frames, {seq.frame_duration}ms each")
```

#### Filename Pattern Detection

Automatically detects animations from filename patterns:

```python
# These files will be grouped as "walk" animation:
# player_walk_01.png, player_walk_02.png, player_walk_03.png

extractor = AnimationExtractor()
sequences = extractor.extract_from_files("sprites/player_*.png")
```

#### SGDK Export

```python
from tools.pipeline import export_sgdk_animations

# Export to SGDK header format
export_sgdk_animations(
    sequences,
    output_path="res/player_anims.h",
    sprite_name="SPR_PLAYER"
)
```

**Generated output:**
```c
// Auto-generated by ARDK Pipeline
#define ANIM_PLAYER_IDLE       0
#define ANIM_PLAYER_WALK       1
#define ANIM_PLAYER_ATTACK     2

const Animation* const player_animations[] = {
    &anim_player_idle,
    &anim_player_walk,
    &anim_player_attack,
};
```

#### AI-Powered Animation Generation

Generate animation frames from text descriptions using AI providers:

```python
from tools.pipeline.ai import AIAnimationGenerator

# Initialize generator for Genesis platform
gen = AIAnimationGenerator(platform="genesis")

# Generate single animation (returns frames + sheet + metadata)
result = gen.generate_animation(
    description="knight warrior with sword",
    action="walk",          # idle, walk, run, attack, jump, death, hit, cast
    frames=6,               # Auto-selected if None
    width=32,
    height=32,
)

if result['success']:
    result['sheet'].save("knight_walk_sheet.png")
    for i, frame in enumerate(result['frames']):
        frame.save(f"knight_walk_{i}.png")

# Generate complete SGDK bundle (PNG + JSON + C header)
paths = gen.generate_animation_bundle(
    description="knight warrior",
    action="walk",
    sprite_name="player",
    output_dir="res/sprites"
)
# Creates: player_walk.png, player_walk.json, player_walk.h

# Generate multiple animations at once
paths = gen.generate_multi_animation(
    description="knight warrior",
    actions=["idle", "walk", "attack", "death"],
    sprite_name="player",
    output_dir="res/sprites"
)
# Creates combined sheet with all animations
```

**Supported Actions:** `idle`, `walk`, `run`, `attack`, `jump`, `death`, `hit`, `cast`

**Provider Fallback:** Uses Pollinations (free) -> Pixie.haus -> SD Local

---

### Sheet Assembly Module

**File:** `sheet_assembler.py`
**Phase:** 1.2 (Complete)

Assemble individual frames into optimized sprite sheets, or dissect existing sheets.

#### Assembling Sheets

```python
from tools.pipeline import SpriteSheetAssembler, PackingAlgorithm

assembler = SpriteSheetAssembler(
    algorithm=PackingAlgorithm.TIGHT_PACK,  # or GRID, ROW_PACK
    padding=1,                               # Pixels between sprites
    power_of_two=True                        # Force POT dimensions
)

# Add frames
assembler.add_frame("idle_01.png")
assembler.add_frame("idle_02.png")
assembler.add_frame("walk_01.png")

# Build sheet
layout = assembler.build()
layout.save("spritesheet.png")

# Get frame coordinates for game code
for name, placement in layout.placements.items():
    print(f"{name}: x={placement.x}, y={placement.y}")
```

#### Dissecting Sheets

```python
from tools.pipeline import dissect_sheet, GridDissector

# Grid-based dissection (uniform frames)
frames = dissect_sheet(
    "spritesheet.png",
    frame_width=32,
    frame_height=32,
    output_dir="frames/"
)

# AI-powered dissection (irregular sprites)
from tools.pipeline import SheetDissector, AIProvider

dissector = SheetDissector(provider=AIProvider.CLAUDE)
sprites = dissector.detect_sprites("complex_sheet.png")

for sprite in sprites:
    sprite.image.save(f"detected/{sprite.name}.png")
```

---

### Palette Conversion Module

**File:** `palette_converter.py`
**Phase:** 1.6 (Complete)

Convert palettes between platforms and formats.

#### Basic Conversion

```python
from tools.pipeline import PaletteConverter, PaletteFormat

converter = PaletteConverter()

# Convert image to Genesis palette
result = converter.convert(
    image_path="sprite.png",
    target_format=PaletteFormat.GENESIS,
    max_colors=15  # +1 for transparency
)

result.image.save("sprite_genesis.png")
print(f"Colors used: {len(result.palette)}")
```

#### Platform Presets

```python
from tools.pipeline import NES_PALETTE, GAMEBOY_PALETTE_GREEN

# Force specific palette
result = converter.convert(
    "sprite.png",
    target_palette=GAMEBOY_PALETTE_GREEN
)
```

#### Batch Conversion

```python
# Convert directory of sprites
converter.batch_convert(
    input_dir="sprites/",
    output_dir="sprites_genesis/",
    target_format=PaletteFormat.GENESIS
)
```

---

### Genesis Export Module

**File:** `genesis_export.py`
**Phase:** 0.6 (Complete)

Export Genesis-ready tile data with automatic mirror optimization.

#### Tile Export with Optimization

```python
from tools.pipeline import export_genesis_tilemap_optimized

stats = export_genesis_tilemap_optimized(
    image_path="tileset.png",
    output_tiles="tiles.bin",
    output_map="tilemap.bin",
    optimize_mirrors=True  # Find H/V flipped duplicates
)

print(f"Original tiles: {stats.original_count}")
print(f"After optimization: {stats.optimized_count}")
print(f"Saved: {stats.savings_percent:.1f}%")
```

#### VDP-Ready Export

```python
from tools.pipeline import export_vdp_ready_sprite, align_for_dma

# Export with VDP attributes
result = export_vdp_ready_sprite(
    image_path="player.png",
    palette_index=0,
    priority=True
)

# Align for DMA transfer
aligned_data = align_for_dma(result.tile_data)
```

---

### SGDK Resources Module

**File:** `sgdk_resources.py`
**Phase:** 2.1 (Complete)

Generate SGDK resource files (.res) programmatically.

#### Basic Resource Generation

```python
from tools.pipeline import SGDKResourceGenerator, Compression

gen = SGDKResourceGenerator(output_dir="res/")

# Add sprite
gen.add_sprite(
    name="player",
    path="sprites/player.png",
    width=32,
    height=32,
    compression=Compression.FAST
)

# Add tileset
gen.add_tileset(
    name="forest",
    path="tilesets/forest.png",
    compression=Compression.BEST
)

# Add palette
gen.add_palette(
    name="player_pal",
    path="palettes/player.pal"
)

# Generate .res file
gen.write_resource_file("resources.res")
```

#### Directory Scanning

```python
from tools.pipeline import generate_resources_from_directory

# Auto-detect resources from directory structure
generate_resources_from_directory(
    input_dir="assets/",
    output_file="res/resources.res",
    sprite_dirs=["sprites/"],
    tileset_dirs=["tilesets/"],
    palette_dirs=["palettes/"]
)
```

---

### Palette Manager Module

**File:** `palette_manager.py`
**Phase:** 1.6 (Complete)

Manage game-wide palette allocation for Genesis (4 palettes x 16 colors).

#### Setting Up Palettes

```python
from tools.pipeline import PaletteManager, PalettePurpose

manager = PaletteManager()

# Define palette slots
manager.set_slot(0, purpose=PalettePurpose.PLAYER)
manager.set_slot(1, purpose=PalettePurpose.ENEMIES)
manager.set_slot(2, purpose=PalettePurpose.BACKGROUND)
manager.set_slot(3, purpose=PalettePurpose.UI)

# Load palettes from images
manager.load_palette_from_image(0, "sprites/player.png")
manager.load_palette_from_image(1, "sprites/enemies.png")

# Validate game palette budget
result = manager.validate()
if not result.valid:
    for warning in result.warnings:
        print(f"Warning: {warning}")
```

#### Exporting Palettes

```python
# Export for SGDK
manager.export_sgdk("res/palettes.h")

# Export as binary
manager.export_binary("res/palettes.bin")
```

---

### Performance Analysis Module

**File:** `performance.py`
**Phase:** 2.3 (Complete)

Analyze sprites for Genesis hardware limits (scanline sprite limits, DMA budget).

#### Analyzing Sprites

```python
from tools.pipeline import analyze_sprite_performance, PerformanceBudgetCalculator

# Quick analysis
report = analyze_sprite_performance("sprites/player.png")
print(f"Sprite size: {report.width}x{report.height}")
print(f"Tiles used: {report.tile_count}")
print(f"Scanline warnings: {len(report.warnings)}")

# Detailed calculator
calc = PerformanceBudgetCalculator()
calc.add_sprite("player", "sprites/player.png", instances=1)
calc.add_sprite("enemy", "sprites/enemy.png", instances=10)
calc.add_sprite("bullet", "sprites/bullet.png", instances=20)

report = calc.analyze()
for warning in report.warnings:
    print(f"[{warning.severity}] Line {warning.scanline}: {warning.message}")
```

---

### Collision Editor Module

**File:** `collision_editor.py`
**Phase:** 4.2 (Complete)

Visualize and debug collision boxes on sprites.

```python
from tools.pipeline import CollisionVisualizer, CollisionBox

viz = CollisionVisualizer()

# Define collision boxes
hitbox = CollisionBox(x=8, y=4, width=16, height=28, type="hitbox")
hurtbox = CollisionBox(x=4, y=0, width=24, height=32, type="hurtbox")

# Render debug overlay
viz.add_box(hitbox, color=(255, 0, 0, 128))
viz.add_box(hurtbox, color=(0, 255, 0, 128))

debug_image = viz.render("sprites/player.png")
debug_image.save("debug/player_collision.png")
```

---

### Animation FSM Module

**File:** `animation_fsm.py`
**Phase:** 4.1 (Complete)

Generate C code for animation state machines.

```python
from tools.pipeline import AnimationFSM, AnimationState, Transition, ConditionType

fsm = AnimationFSM(name="player")

# Define states
fsm.add_state(AnimationState("idle", animation="ANIM_IDLE", looping=True))
fsm.add_state(AnimationState("walk", animation="ANIM_WALK", looping=True))
fsm.add_state(AnimationState("attack", animation="ANIM_ATTACK", looping=False))

# Define transitions
fsm.add_transition(Transition(
    from_state="idle",
    to_state="walk",
    condition=ConditionType.INPUT,
    condition_value="moving"
))

fsm.add_transition(Transition(
    from_state="walk",
    to_state="idle",
    condition=ConditionType.INPUT,
    condition_value="!moving"
))

# Generate C code
fsm.export_c("src/player_fsm.c", "src/player_fsm.h")
```

---

### Cross-Platform Export Module

**File:** `cross_platform.py`
**Phase:** 4.3 (Complete)

Export assets for multiple retro platforms simultaneously.

```python
from tools.pipeline import CrossPlatformExporter, Platform, ExportConfig

exporter = CrossPlatformExporter()

# Configure platforms
exporter.add_platform(Platform.GENESIS, ExportConfig(
    max_colors=16,
    tile_size=8,
    sprite_limit=80
))

exporter.add_platform(Platform.NES, ExportConfig(
    max_colors=4,
    tile_size=8,
    sprite_limit=64
))

exporter.add_platform(Platform.GAMEBOY, ExportConfig(
    max_colors=4,
    tile_size=8,
    grayscale=True
))

# Export sprite to all platforms
results = exporter.export("sprites/player.png", output_dir="export/")

for platform, result in results.items():
    print(f"{platform}: {result.output_path} ({result.color_count} colors)")
```

---

### Tiled Maps Module

**File:** `maps.py`
**Phase:** Complete

Import Tiled .tmx maps and export for SGDK.

```python
from tools.pipeline import load_tiled_map, export_map_to_sgdk

# Load map
tiled_map = load_tiled_map("levels/level1.tmx")

print(f"Map size: {tiled_map.width}x{tiled_map.height} tiles")
print(f"Layers: {[layer.name for layer in tiled_map.layers]}")

# Export for SGDK
export_map_to_sgdk(
    tiled_map,
    output_dir="res/levels/",
    map_name="level1"
)
```

#### Collision Extraction

```python
from tools.pipeline import extract_collision, CollisionType

collision = extract_collision(
    tiled_map,
    collision_layer="collision",  # Layer name in Tiled
    output_path="res/level1_collision.bin"
)
```

---

### Audio Pipeline Module

**File:** `audio.py`
**Phase:** Complete

Convert audio files for Genesis (PCM/WAV to SGDK format).

```python
from tools.pipeline import AudioConverter, convert_audio, SFXManager

# Simple conversion
result = convert_audio(
    "sfx/explosion.wav",
    output_path="res/sfx_explosion.wav",
    sample_rate=13379  # Genesis Z80 optimal
)

print(f"Duration: {result.duration_ms}ms")
print(f"Size: {result.size_bytes} bytes")

# SFX management
sfx_manager = SFXManager()
sfx_manager.add_sfx("explosion", "sfx/explosion.wav", priority=5)
sfx_manager.add_sfx("jump", "sfx/jump.wav", priority=3)
sfx_manager.add_sfx("coin", "sfx/coin.wav", priority=1)

# Export all SFX
sfx_manager.export_all("res/sfx/")
sfx_manager.export_header("src/sfx_ids.h")
```

---

### VGM Tools Module

**File:** `vgm/vgm_tools.py`
**Phase:** 2.7 (Complete)

VGM file validation, XGM conversion, and WOPN instrument bank parsing for Genesis audio workflow.

#### VGM File Validation

Check VGM files for Genesis compatibility before conversion:

```python
from tools.pipeline.vgm import validate_vgm, get_vgm_info, parse_vgm_header

# Quick validation
errors = validate_vgm("music.vgm")
if errors:
    for err in errors:
        print(f"Error: {err}")
else:
    print("VGM is Genesis-compatible!")

# Full file information
info = get_vgm_info("music.vgm")
print(f"Version: {info.header.version_string}")
print(f"Duration: {info.header.duration_seconds:.1f}s")
print(f"Has loop: {info.header.has_loop}")
print(f"Genesis compatible: {info.is_genesis_compatible}")

# Warnings (non-fatal issues)
for warning in info.warnings:
    print(f"Warning: {warning}")
```

#### Chip Detection

Detect which sound chips are used in a VGM:

```python
from tools.pipeline.vgm import parse_vgm_header, detect_vgm_chips
from tools.pipeline.vgm.vgm_tools import VGMChip

header = parse_vgm_header("music.vgm")
chips = detect_vgm_chips(header)

if chips & VGMChip.YM2612:
    print("Uses YM2612 FM synthesis")
if chips & VGMChip.SN76489:
    print("Uses SN76489 PSG")
```

#### XGM Conversion

Convert VGM to SGDK's optimized XGM format:

```python
from tools.pipeline.vgm import XGMToolWrapper

# Initialize wrapper (finds xgmtool automatically)
wrapper = XGMToolWrapper()

# Check if xgmtool is available
if not wrapper.is_available():
    print("Install SGDK and add xgmtool to PATH")

# Convert single file
result = wrapper.convert(
    "music.vgm",
    "music.xgm",
    optimize=True,      # Run optimization pass
    timing="ntsc"       # "ntsc" (60Hz) or "pal" (50Hz)
)

if result.success:
    print(f"Converted: {result.output_path}")
    print(f"Size: {result.input_size} -> {result.output_size} bytes")
    print(f"Compression: {result.compression_ratio:.1%}")
else:
    for err in result.errors:
        print(f"Error: {err}")

# Batch conversion
vgm_files = ["track1.vgm", "track2.vgm", "track3.vgm"]
results = wrapper.batch_convert(vgm_files, output_dir="res/music/")
```

#### WOPN Instrument Banks

Parse and manipulate FM instrument banks (OPN2BankEditor format):

```python
from tools.pipeline.vgm import WOPNParser, WOPNPatch, WOPNOperator, WOPNBank

parser = WOPNParser()

# Load existing bank
bank = parser.load("instruments.wopn")
print(f"Bank: {bank.name}")
print(f"Melodic patches: {len(bank.melodic_patches)}")
print(f"Drum patches: {len(bank.drum_patches)}")

# Find patch by name
bass = bank.find_patch("Bass")
if bass:
    print(f"Bass: algorithm={bass.algorithm}, feedback={bass.feedback}")

# Get patch by index
patch = bank.get_patch(0)  # First melodic patch

# Export to TFI format (common FM instrument format)
tfi_data = patch.to_tfi()
with open("bass.tfi", "wb") as f:
    f.write(tfi_data)

# Create custom patch
operators = [
    WOPNOperator(
        detune=3, multiple=1, total_level=35,
        rate_scaling=0, attack_rate=31, decay_1_rate=10,
        decay_2_rate=5, release_rate=8, sustain_level=3,
        am_enable=False, ssg_eg=0
    )
    for _ in range(4)  # 4 operators per FM voice
]

custom_patch = WOPNPatch(
    name="MyBass",
    algorithm=4,
    feedback=5,
    operators=operators
)

# Create and save custom bank
custom_bank = WOPNBank(
    name="MyInstruments",
    version=2,
    melodic_patches=[custom_patch],
    drum_patches=[]
)
parser.save(custom_bank, "my_instruments.wopn")
```

#### XGM Size Estimation

Estimate the output size before conversion:

```python
from tools.pipeline.vgm import get_vgm_info, estimate_xgm_size

info = get_vgm_info("music.vgm")
estimated_size = estimate_xgm_size(info)
print(f"Estimated XGM size: ~{estimated_size} bytes")
```

#### Workflow: Furnace Tracker → SGDK

```python
from tools.pipeline.vgm import validate_vgm, XGMToolWrapper
from tools.pipeline import SGDKResourceGenerator

# 1. Validate exported VGM
errors = validate_vgm("furnace_export.vgm")
if errors:
    raise ValueError(f"VGM validation failed: {errors}")

# 2. Convert to XGM
wrapper = XGMToolWrapper()
result = wrapper.convert("furnace_export.vgm", "res/music/bgm.xgm")
if not result.success:
    raise ValueError(f"Conversion failed: {result.errors}")

# 3. Add to SGDK resources
gen = SGDKResourceGenerator(output_dir="res/")
gen.add_xgm("bgm", "music/bgm.xgm")
gen.generate("resources.res")
```

---

### AI Generation Providers Module

**Directory:** `ai_providers/`
**Phase:** 3.6 (Complete)

Unified interface for AI-powered sprite generation across multiple providers with automatic fallback.

#### Available Providers

| Provider | Cost | Best For | Requires |
|----------|------|----------|----------|
| **Pollinations** | Free | General generation, prototyping | Nothing (works out of box) |
| **Pixie.haus** | Paid | Pixel-perfect, palette-constrained | `PIXIE_HAUS_API_KEY` |
| **SD Local** | Free* | Custom models, privacy | Local SD WebUI running |

*Electricity/hardware costs apply

#### Quick Start

```python
from tools.pipeline.ai_providers import (
    get_generation_provider,
    generate_with_fallback,
    GenerationConfig,
)

# Get best available provider
provider = get_generation_provider()

# Generate a sprite
config = GenerationConfig(
    width=32,
    height=32,
    platform="genesis",
    max_colors=16,
)

result = provider.generate("warrior with sword", config)

if result.success:
    result.image.save("warrior.png")
    print(f"Generated in {result.generation_time_ms}ms by {result.provider}")
else:
    print(f"Failed: {result.errors}")
```

#### Generation with Fallback

Automatically tries multiple providers until one succeeds:

```python
from tools.pipeline.ai_providers import generate_with_fallback, GenerationConfig

# Tries Pixie.haus -> Pollinations -> SD Local
result = generate_with_fallback(
    prompt="pixel art dragon boss",
    config=GenerationConfig(
        width=64,
        height=64,
        platform="genesis",
    ),
    preferred="pixie_haus",  # Try this first
)

if result.success:
    print(f"Generated by: {result.provider}")
```

#### Provider-Specific Usage

**Pollinations (Free, Versatile):**

```python
from tools.pipeline.ai_providers import PollinationsGenerationProvider

provider = PollinationsGenerationProvider(
    model="gptimage-large",  # Best quality
    # model="flux",         # Good for concepts
    # model="turbo",        # Fastest
)

result = provider.generate("NES-style hero idle sprite")
```

**Pixie.haus (Pixel-Perfect):**

```python
import os
from tools.pipeline.ai_providers import PixieHausProvider, GenerationConfig

# Set API key in environment
os.environ['PIXIE_HAUS_API_KEY'] = 'your-key-here'

provider = PixieHausProvider()

# Pixie.haus has built-in palette constraints
config = GenerationConfig(
    width=32,
    height=32,
    platform="genesis",  # Uses Genesis palette mode
    max_colors=16,
)

result = provider.generate("cyberpunk warrior", config)
```

**Local Stable Diffusion (Free, Custom Models):**

```python
from tools.pipeline.ai_providers import StableDiffusionLocalProvider

# Requires Automatic1111 WebUI running at http://127.0.0.1:7860
provider = StableDiffusionLocalProvider(
    api_url="http://127.0.0.1:7860",
    checkpoint="pixel-art-xl.safetensors",  # Custom pixel art model
)

if provider.is_available:
    result = provider.generate("sprite sheet of slime enemy")
else:
    print("Start the SD WebUI first!")
```

#### Advanced Features

**Image-to-Image Transform:**

```python
from PIL import Image
from tools.pipeline.ai_providers import get_generation_provider

provider = get_generation_provider()
source = Image.open("sketch.png")

result = provider.generate_from_image(
    source=source,
    prompt="convert to pixel art Genesis style",
    strength=0.7,  # How much to change (0-1)
)
```

**Animation Generation (Pixie.haus):**

```python
from tools.pipeline.ai_providers import PixieHausProvider

provider = PixieHausProvider()
source = Image.open("hero_idle.png")

result = provider.generate_animation(
    source=source,
    action="walk",  # idle, walk, attack, jump, death
)

if result.success:
    for i, frame in enumerate(result.frames):
        frame.save(f"hero_walk_{i}.png")
```

**Multi-View Generation (Pixie.haus):**

```python
result = provider.generate_views(
    source=hero_front,
    views=["front", "side", "back", "front-right", "back-right"],
)

for view_name, view_img in result.views.items():
    view_img.save(f"hero_{view_name}.png")
```

**Upscaling:**

```python
result = provider.upscale(
    source=small_sprite,
    scale=2,  # 2x or 4x
)
```

#### Provider Status

Check what's available:

```python
from tools.pipeline.ai_providers import (
    get_available_providers,
    provider_status,
)

# List available providers
available = get_available_providers()
print(f"Available: {available}")

# Detailed status
status = provider_status()
for name, info in status.items():
    print(f"{name}: {'✓' if info['available'] else '✗'}")
```

#### Custom Provider Registration

Add your own provider:

```python
from tools.pipeline.ai_providers import (
    GenerationProvider,
    GenerationResult,
    GenerationConfig,
    ProviderCapability,
    register_provider,
)

class MyCustomProvider(GenerationProvider):
    @property
    def name(self):
        return "MyProvider"

    @property
    def capabilities(self):
        return ProviderCapability.TEXT_TO_IMAGE

    @property
    def is_available(self):
        return True

    def generate(self, prompt, config=None):
        # Your implementation here
        ...

register_provider("my_provider", MyCustomProvider())
```

---

### Optimization Module

**File:** `optimization/tile_optimizer.py`
**Phase:** 6.1 (Advanced Tile Optimization)

Advanced tile deduplication with flip detection, VRAM budget tracking, and batch processing for retro platforms.

#### TileOptimizer

Optimize sprite sheets by deduplicating tiles and detecting flipped duplicates:

```python
from pipeline.optimization import TileOptimizer

# Initialize optimizer for Genesis (64KB VRAM)
optimizer = TileOptimizer(
    tile_width=8,
    tile_height=8,
    allow_mirror_x=True,   # Detect horizontal flips
    allow_mirror_y=True,   # Detect vertical flips
    platform='genesis'     # genesis, nes, snes, gameboy, gba
)

# Optimize a sprite sheet
result = optimizer.optimize_image(sprite_sheet)

# Access results
print(f"Original tiles: {result.stats.original_tile_count}")
print(f"Unique tiles: {result.unique_tile_count}")
print(f"Savings: {result.stats.savings_bytes} bytes ({result.stats.savings_percent:.1f}%)")
print(f"H-Flip matches: {result.stats.h_flip_matches}")
print(f"V-Flip matches: {result.stats.v_flip_matches}")

# Access unique tiles
for idx, tile in enumerate(result.unique_tiles):
    tile.save(f"tile_{idx:04d}.png")

# Access tile map for reconstruction
for idx, tile_ref in enumerate(result.tile_map):
    print(f"Position {idx}: tile {tile_ref.index}, "
          f"flip_h={tile_ref.flip_h}, flip_v={tile_ref.flip_v}")
```

#### VRAM Budget Tracking

Check if tiles fit within platform VRAM limits:

```python
# Check VRAM usage for Genesis (64KB limit)
fits, used_bytes, available_bytes = optimizer.check_vram_budget(
    result.unique_tile_count
)

if fits:
    print(f"✓ {used_bytes} bytes used ({used_bytes/available_bytes*100:.1f}%)")
else:
    print(f"✗ Exceeds VRAM by {used_bytes - available_bytes} bytes")

# Get maximum tiles that fit in budget
max_tiles = optimizer.get_max_tiles_for_budget()
print(f"Platform can hold up to {max_tiles} tiles")
```

#### Saving and Loading Results

```python
# Save unique tiles as individual images
result.save_tiles(
    output_dir="optimized/tiles",
    prefix="sprite"
)

# Save tile map as JSON
result.save_tile_map("optimized/tilemap.json")

# Reconstruct image from optimized tiles (verification)
reconstructed = result.reconstruct_image()
reconstructed.save("reconstructed.png")
```

#### Batch Processing

Optimize multiple sprite sheets at once:

```python
from pipeline.optimization import BatchTileOptimizer

batch = BatchTileOptimizer(
    platform='genesis',
    allow_mirror_x=True,
    allow_mirror_y=True
)

# Optimize entire directory
results = batch.optimize_directory(
    input_dir="assets/sprites",
    pattern="*.png"
)

# Print summary
batch.print_summary()
# Output:
# Files Processed: 15
# Total Original Tiles: 2048
# Total Unique Tiles: 512
# Total Savings: 49152 bytes (48.0 KB)
```

#### CLI Tool

Use the standalone CLI for quick optimizations:

```bash
# Optimize single sprite sheet
python optimize_tiles.py sprite.png --output optimized/ --stats

# Batch optimize directory
python optimize_tiles.py assets/sprites/*.png --batch --output out/

# Check VRAM budget for NES
python optimize_tiles.py sprite.png --platform nes --check-vram

# Disable flip detection
python optimize_tiles.py sprite.png --no-flip-h --no-flip-v

# Save tiles and verify reconstruction
python optimize_tiles.py sprite.png --save-tiles --verify --output out/
```

#### Platform VRAM Limits

| Platform | VRAM Budget | Max Tiles (8x8 RGBA) |
|----------|-------------|----------------------|
| Genesis  | 64 KB       | 256 tiles            |
| NES      | 8 KB        | 32 tiles             |
| SNES     | 64 KB       | 256 tiles            |
| Game Boy | 8 KB        | 32 tiles             |
| GBA      | 96 KB       | 384 tiles            |

#### Use Cases

**Genesis Sprite Optimization:**

```python
# Genesis can flip tiles in hardware for free
optimizer = TileOptimizer(platform='genesis')
result = optimizer.optimize_image(player_sprite)
# Typical savings: 30-50% for symmetric sprites
```

**NES CHR-ROM Banking:**

```python
# NES has only 8KB per CHR bank - critical optimization
optimizer = TileOptimizer(platform='nes', allow_mirror_x=False)
result = optimizer.optimize_image(tileset)
if result.stats.vram_used_bytes > 8192:
    print("Warning: Exceeds single CHR bank, requires bank switching")
```

**Tile Deduplication for Large Levels:**

```python
# Find duplicate tiles across entire level tileset
optimizer = TileOptimizer(allow_mirror_x=True, allow_mirror_y=True)
result = optimizer.optimize_image(level_tileset)
print(f"Removed {result.stats.duplicate_count} duplicate tiles")
```

---

### Watch Module

**File:** `watch/file_watcher.py`
**Phase:** 6.2 (Workflow Automation)

File system monitoring with debouncing and hot reload support for artist workflow automation.

#### AssetWatcher

Monitor directories for asset changes with intelligent debouncing:

```python
from pipeline.watch import AssetWatcher, WatchConfig

# Configure watcher
config = WatchConfig(
    watch_dirs=['assets/sprites', 'assets/tilesets'],
    extensions=['.png', '.aseprite'],
    debounce_seconds=1.0,
    recursive=True,
    ignore_patterns=['*.tmp', '.*', '*~']
)

# Create watcher
watcher = AssetWatcher(config)

# Set up callback
def on_change(event):
    print(f"{event.change_type.value}: {event.path.name}")
    if event.hash:
        print(f"Hash: {event.hash[:16]}...")

watcher.on_change = on_change

# Start watching
watcher.start()

# ... watcher runs in background ...

# Stop watching
watcher.stop()
```

#### Features

**Debouncing:**
Waits for file writes to complete before processing:

```python
config = WatchConfig(
    watch_dirs=['assets/'],
    debounce_seconds=2.0  # Wait 2s after last change
)
```

**Hash-based Change Detection:**
Skips duplicate writes (same content):

```python
watcher = AssetWatcher(config)

# First save triggers processing
asset.save('sprite.png')

# Re-save without changes - skipped
asset.save('sprite.png')

# Modified save triggers processing
modified_asset.save('sprite.png')
```

**Selective Processing:**
Only monitors specified extensions and patterns:

```python
config = WatchConfig(
    watch_dirs=['assets/'],
    extensions=['.png', '.aseprite', '.bmp'],
    ignore_patterns=['*.tmp', '.*', '*_backup.png']
)
```

#### PipelineWatcher

Integrated watcher that processes changes through the pipeline:

```python
from pipeline.watch import PipelineWatcher, WatchConfig

def process_sprite(path):
    """Custom processing function."""
    from PIL import Image
    from pipeline.optimization import TileOptimizer

    img = Image.open(path)
    optimizer = TileOptimizer(platform='genesis')
    result = optimizer.optimize_image(img)

    # Save optimized tiles
    output_dir = Path('output') / path.stem
    result.save_tiles(str(output_dir))
    print(f"✓ Optimized {path.name}: {result.unique_tile_count} tiles")

# Create pipeline watcher
config = WatchConfig(watch_dirs=['assets/sprites'])
watcher = PipelineWatcher(
    config,
    processor_func=process_sprite,
    enable_hot_reload=False
)

watcher.start()
```

#### Hot Reload Integration

Trigger emulator reload after processing:

```python
config = WatchConfig(
    watch_dirs=['assets/'],
    hot_reload_enabled=True,
    hot_reload_command='make reload'  # Custom reload command
)

watcher = PipelineWatcher(
    config,
    processor_func=process_sprite,
    enable_hot_reload=True
)

watcher.start()

# On batch complete, runs: make reload
```

#### CLI Tool

Use the standalone CLI for quick monitoring:

```bash
# Watch sprites directory
python watch_assets.py assets/sprites --processor sprite

# Watch multiple directories
python watch_assets.py assets/sprites assets/tilesets

# Custom debounce time
python watch_assets.py assets/ --debounce 2.0

# Enable hot reload
python watch_assets.py assets/ --hot-reload --reload-cmd "make reload"

# Watch specific extensions
python watch_assets.py assets/ --extensions .png .aseprite

# Non-recursive (top level only)
python watch_assets.py assets/ --no-recursive
```

#### Built-in Processors

**Sprite Processor:**
Scales and converts sprites for Genesis:

```bash
python watch_assets.py assets/sprites --processor sprite
# Automatically: scale → convert → export to output/sprites/
```

**Tileset Processor:**
Optimizes tilesets by deduplicating tiles:

```bash
python watch_assets.py assets/tilesets --processor tileset
# Automatically: optimize → save tiles → save tilemap
```

**Generic Processor:**
Just reports changes without processing:

```bash
python watch_assets.py assets/ --processor generic
# Output: CREATED: sprite.png
#         Hash: abc123def456...
```

#### Statistics

Watcher tracks processing statistics:

```python
watcher = AssetWatcher(config)
watcher.start()

# ... after processing ...

watcher.stop()

# Output:
# Statistics:
#   Changes Detected: 15
#   Changes Processed: 12
#   Changes Skipped: 3 (duplicates)
```

#### Error Handling

Set up error callback for processing failures:

```python
watcher = AssetWatcher(config)

def on_error(exception):
    print(f"Error: {exception}")
    # Log to file, send notification, etc.

watcher.on_error = on_error
watcher.start()
```

#### Safety Features

Protect against resource exhaustion, infinite loops, and cost overruns with SafetyConfig:

```python
from pipeline.watch import AssetWatcher, WatchConfig, SafetyConfig

# Configure safety limits
safety = SafetyConfig(
    max_file_size_mb=50.0,              # Skip files > 50MB
    max_changes_per_minute=60,          # Rate limit: 60 changes/min max
    max_queue_depth=100,                # Max 100 pending files
    max_processing_time_seconds=30.0,   # Timeout per file
    circuit_breaker_errors=5,           # Pause after 5 errors
    circuit_breaker_cooldown=60.0,      # 60s cooldown period
    error_backoff_seconds=5.0           # 5s delay after error
)

config = WatchConfig(
    watch_dirs=['assets/'],
    safety=safety  # Enable safety limits
)

watcher = AssetWatcher(config)
watcher.start()
```

**Rate Limiting:**
Prevents processing more than N files per minute:

```python
safety = SafetyConfig(max_changes_per_minute=30)  # Max 30/min
config = WatchConfig(watch_dirs=['assets/'], safety=safety)
watcher = AssetWatcher(config)

# If rate exceeded, files are queued for later processing
# Statistics show: changes_rate_limited
```

**File Size Limits:**
Skips files exceeding size threshold:

```python
safety = SafetyConfig(max_file_size_mb=10.0)  # Skip files > 10MB
config = WatchConfig(watch_dirs=['assets/'], safety=safety)
watcher = AssetWatcher(config)

# Large files automatically skipped
# Statistics show: changes_too_large
```

**Circuit Breaker:**
Pauses processing after consecutive errors:

```python
safety = SafetyConfig(
    circuit_breaker_errors=3,      # Open after 3 errors
    circuit_breaker_cooldown=60.0  # Pause for 60s
)
config = WatchConfig(watch_dirs=['assets/'], safety=safety)
watcher = AssetWatcher(config)

# After 3 consecutive errors:
# ⚠ Circuit breaker opened after 3 errors
#    Pausing for 60.0s...
# [Processing paused for cooldown period]
# ✓ Circuit breaker reset after cooldown
```

**Processing Timeout:**
Prevents hung processing operations:

```python
safety = SafetyConfig(
    max_processing_time_seconds=15.0,  # 15s timeout
    error_backoff_seconds=2.0          # Wait 2s after timeout
)
config = WatchConfig(watch_dirs=['assets/'], safety=safety)
watcher = AssetWatcher(config)

# If processing exceeds timeout:
# ⚠ Timeout processing sprite.png (>15.0s)
# [Applies 2s backoff before next file]
```

**Queue Depth Limit:**
Prevents memory exhaustion from file floods:

```python
safety = SafetyConfig(max_queue_depth=50)  # Max 50 pending files
config = WatchConfig(watch_dirs=['assets/'], safety=safety)
watcher = AssetWatcher(config)

# If 50 files already queued, new changes are dropped
# Prevents memory exhaustion during file floods
```

**Disabling Safety (Development Only):**

```python
# WARNING: Only for development/testing
config = WatchConfig(
    watch_dirs=['assets/'],
    safety=None  # Disable all safety limits
)
```

**Safety Statistics:**

```python
watcher = AssetWatcher(config)
watcher.start()

# ... after processing ...

watcher.stop()

# Output:
# Statistics:
#   Changes Detected: 120
#   Changes Processed: 85
#   Changes Skipped: 15 (duplicates)
#
#   Safety Stats:
#     Rate Limited: 12
#     Too Large: 3
#     Timed Out: 2
#     Circuit Breaker Trips: 1
#     Current Rate: 48/min
```

**CLI Safety Options:**

```bash
# Production-safe defaults
python watch_assets.py assets/ --processor sprite

# Stricter limits for CI/CD
python watch_assets.py assets/ \
    --max-file-size 10 \
    --max-rate 30 \
    --timeout 15

# Development mode (no limits)
python watch_assets.py assets/ --no-safety
```

**Best Practices:**

1. **Always use safety limits in production** - Default SafetyConfig is enabled by default
2. **Tune rate limits for your workflow** - Artists: 30-60/min, CI/CD: 10-20/min
3. **Set appropriate timeouts** - Neural upscaling: 60s+, simple converts: 10-30s
4. **Monitor circuit breaker trips** - Indicates systemic processing issues
5. **Use file size limits** - Prevents accidental processing of huge files
6. **Test error scenarios** - Verify circuit breaker and backoff behavior

#### Use Cases

**Artist Workflow:**

```python
# Artist saves sprite in Aseprite → auto-process to Genesis format
config = WatchConfig(
    watch_dirs=['work/sprites'],
    extensions=['.aseprite', '.png'],
    debounce_seconds=1.5  # Wait for save complete
)

def process_sprite(path):
    # Convert to Genesis, optimize, export
    pass

watcher = PipelineWatcher(config, processor_func=process_sprite)
watcher.start()
# Artist can see changes in emulator immediately
```

**Tileset Hot Reload:**

```python
# Designer tweaks tileset → auto-rebuild level → reload emulator
config = WatchConfig(
    watch_dirs=['assets/tilesets'],
    hot_reload_enabled=True,
    hot_reload_command='make build && blastem game.bin'
)

watcher = PipelineWatcher(config, process_tileset, enable_hot_reload=True)
watcher.start()
```

**Continuous Integration:**

```python
# Watch for asset commits → validate → generate reports
config = WatchConfig(
    watch_dirs=['assets/'],
    recursive=True
)

def validate_asset(path):
    from pipeline.validation import ImageValidator
    validator = ImageValidator(platform='genesis')
    result = validator.validate(str(path))
    if not result:
        raise ValueError(f"Validation failed: {result.errors}")

watcher = PipelineWatcher(config, validate_asset)
watcher.start()
```

---

### Processing Module

**File:** `processing.py`
**Phase:** 0.x (Core Utilities)

Low-level image processing utilities for tile optimization, background detection, and sprite conversion.

#### Legacy TileOptimizer (Backward Compatible)

The original TileOptimizer in `processing.py` now uses the new advanced optimizer internally:

```python
from tools.pipeline.processing import TileOptimizer

# Old API still works (backward compatible)
optimizer = TileOptimizer(
    tile_width=8,
    tile_height=8,
    allow_mirror_x=True,
    allow_mirror_y=True
)

# Returns old format: (unique_tiles, tile_map, count)
unique_tiles, tile_map, count = optimizer.optimize(image)

# tile_map is list of dicts for backward compatibility
for entry in tile_map:
    print(f"Tile {entry['index']}, flip_x={entry['flip_x']}, flip_y={entry['flip_y']}")
```

**Note:** New code should use `pipeline.optimization.TileOptimizer` for access to enhanced features like VRAM tracking, batch processing, and statistics.

#### FloodFillBackgroundDetector

Smart background removal using edge-initiated flood fill (preserves internal black pixels):

```python
from tools.pipeline.processing import FloodFillBackgroundDetector

detector = FloodFillBackgroundDetector(tolerance=10)

# Detect background color from corners
bg_color = detector.detect_background_color(image)
print(f"Background: RGB{bg_color}")

# Get content mask (1=content, 0=background)
mask = detector.get_content_mask(image)

# Detect sprite bounding boxes
sprites = detector.detect(image)
for bbox in sprites:
    print(f"Sprite at ({bbox.x}, {bbox.y}) size {bbox.width}x{bbox.height}")
```

#### SpriteConverter

Platform-agnostic sprite converter with dithering support:

```python
from tools.pipeline.processing import SpriteConverter
from tools.pipeline.platforms import GenesisConfig, NESConfig

# Genesis converter with ordered dithering
converter = SpriteConverter(
    platform=GenesisConfig,
    palette=[0x000, 0x222, 0x666, 0xEEE]  # Genesis BGR format
)

# Scale sprite to target size
scaled = converter.scale_sprite(image, target_size=32)

# Convert to indexed palette with dithering
# Dithering methods: 'none', 'ordered' (Bayer), 'floyd' (Floyd-Steinberg)
indexed = converter.index_sprite(scaled)

# Generate tile data
tile_data = converter.generate_tile_data(indexed)
```

#### PaletteExtractor

Extract optimal NES/Genesis palettes from images:

```python
from tools.pipeline.processing import PaletteExtractor

extractor = PaletteExtractor()

# Algorithmic extraction (fast, no AI)
palette = extractor.extract_from_image(image, num_colors=4)
print(f"Palette: {[f'${c:02X}' for c in palette]}")

# AI-enhanced extraction (uses AIAnalyzer)
from tools.pipeline.ai import AIAnalyzer
analyzer = AIAnalyzer()
palette = extractor.extract_with_ai(image, analyzer, num_colors=4)
```

---

### AI Integration Module

**File:** `ai.py`
**Phase:** 3.x (AI Features)

Multi-provider AI integration for sprite analysis, labeling, and collision detection.

#### AIAnalyzer

Main entry point for AI-powered sprite analysis with automatic fallback:

```python
from tools.pipeline.ai import AIAnalyzer

# Auto-detect available providers (Pollinations → Gemini → OpenAI → etc.)
analyzer = AIAnalyzer()

# Or specify preferred provider
analyzer = AIAnalyzer(
    preferred_provider='pollinations',
    pollinations_model='openai-large',  # or 'gemini-large', 'claude'
    cache_dir='.cache/ai'
)

# Offline mode (uses heuristic fallback)
analyzer = AIAnalyzer(offline_mode=True)

print(f"Using: {analyzer.provider_name}")
print(f"Available: {analyzer.available}")
```

#### Sprite Analysis

```python
from tools.pipeline.ai import AIAnalyzer
from tools.pipeline.platforms import SpriteInfo, BoundingBox

# Analyze sprite sheet for labels
analyzer = AIAnalyzer()
sprites = [
    SpriteInfo(id=1, bbox=BoundingBox(0, 0, 32, 32)),
    SpriteInfo(id=2, bbox=BoundingBox(32, 0, 32, 32)),
]

result = analyzer.analyze(
    img=sprite_sheet,
    sprites=sprites,
    use_cache=True,
    filename="player.png"  # Hints for fallback
)

# Result format:
# {'sprites': [
#     {'id': 1, 'type': 'player', 'action': 'idle', 'description': 'hero_idle_1'},
#     {'id': 2, 'type': 'player', 'action': 'walk', 'description': 'hero_walk_1'}
# ]}

# Apply labels back to sprites
sprites = analyzer.apply_labels(sprites, result)
```

#### AI-Powered Collision Detection

```python
# Analyze sprite for hitbox/hurtbox
collision = analyzer.analyze_collision(
    sprite_img=cropped_sprite,
    sprite_type="player",
    sprite_width=32,
    sprite_height=32
)

print(f"Hitbox: {collision['hitbox']}")  # {'x': 8, 'y': 4, 'w': 16, 'h': 28}
print(f"Hurtbox: {collision['hurtbox']}")
print(f"Confidence: {collision['confidence']}")
print(f"Reasoning: {collision['reasoning']}")

# Generate pixel-perfect collision mask
mask_bytes = analyzer.generate_pixel_mask(sprite_img, threshold=128)
```

#### ConsensusEngine

Multi-model validation for higher accuracy:

```python
from tools.pipeline.ai import AIAnalyzer, ConsensusEngine

analyzer = AIAnalyzer()
consensus = ConsensusEngine(analyzer)

# Query multiple models and vote on results
consensus.models = ['openai-large', 'gemini-large', 'claude']
result = consensus.resolve(sprite_sheet, sprites, output_dir='output/')

# Saves consensus_report.txt to output/debug/
# Result only includes sprites with 2+ model agreement
```

#### Available AI Providers

| Provider | Environment Variable | Vision Support |
|----------|---------------------|----------------|
| Pollinations | `POLLINATIONS_API_KEY` | Yes (30+ models) |
| Gemini | `GEMINI_API_KEY` | Yes |
| OpenAI | `OPENAI_API_KEY` | Yes |
| Anthropic | `ANTHROPIC_API_KEY` | Yes |
| Groq | `GROQ_API_KEY` | Yes (Llama 4) |
| Grok/xAI | `XAI_API_KEY` | Yes |

---

### Fallback Analysis Module

**File:** `fallback.py`
**Phase:** 0.7 (Offline Support)

Heuristic-based sprite analysis when AI is unavailable or in offline mode.

#### FallbackAnalyzer

```python
from tools.pipeline.fallback import FallbackAnalyzer, get_fallback_labels

analyzer = FallbackAnalyzer(filename_hints=True)

# Analyze sprites using heuristics
result = analyzer.analyze_sprites(
    img=sprite_sheet,
    sprites=sprite_list,
    filename="player_walk.png"  # Used for type hints
)

# Result format matches AI output:
# {'sprites': [
#     {'id': 1, 'type': 'character', 'action': 'walk', 'description': 'character_walk_1',
#      'confidence': 0.5, 'method': 'fallback_heuristic', 'size_category': 'medium'}
# ]}

# Convenience function
result = get_fallback_labels(sprites, img, filename="player.png")
```

#### Heuristic Rules

Size-based type inference:
- **tiny** (< 12px): projectile
- **small** (12-20px): item
- **medium** (20-40px): character
- **large** (40-64px): boss
- **huge** (64+px): ui/background

Filename pattern detection:
- `player*`, `hero*` → player
- `enemy*`, `monster*` → enemy
- `bullet*`, `projectile*` → projectile
- `item*`, `pickup*` → item

#### Fallback Collision

```python
from tools.pipeline.fallback import apply_fallback_collision

# Add heuristic collision masks to sprites
sprites = apply_fallback_collision(sprites)

# Default: hitbox is inner 70%, hurtbox is inner 90%
for sprite in sprites:
    print(f"Hitbox: {sprite.collision.hitbox}")
    print(f"Hurtbox: {sprite.collision.hurtbox}")
```

---

### Style System Module

**File:** `style.py`
**Phase:** 3.x (AI Features)

Provider-agnostic style capture and transfer for consistent AI-generated assets.

#### StyleProfile

Define reusable style characteristics:

```python
from tools.pipeline.style import (
    StyleProfile, StyleManager,
    OutlineStyle, ShadingLevel, DetailLevel
)

# Create style manually
style = StyleProfile(
    name="genesis_warrior",
    palette=[(0, 0, 0), (36, 36, 109), (145, 109, 36), (255, 255, 255)],
    outline_style=OutlineStyle.BLACK,
    shading_level=ShadingLevel.MODERATE,
    detail_level=DetailLevel.MEDIUM,
    target_platform="genesis"
)

# Save/load styles
style.save("styles/warrior.json")
loaded = StyleProfile.load("styles/warrior.json")
```

#### StyleManager

Capture and apply styles:

```python
from tools.pipeline.style import StyleManager

manager = StyleManager(styles_dir="styles/")

# Capture style from reference image
style = manager.capture_style(
    img=reference_image,
    name="my_style",
    platform="genesis"
)

# Auto-detected characteristics:
print(f"Outline: {style.outline_style}")      # OutlineStyle.BLACK
print(f"Shading: {style.shading_level}")      # ShadingLevel.MODERATE
print(f"Contrast: {style.contrast}")           # 0.0-1.0
print(f"Saturation: {style.saturation}")       # 0.0-1.0
print(f"Dither: {style.dither_pattern}")       # 'none', 'bayer', 'light'

# Save with reference image
path = manager.save_style(style, include_reference=True)

# List available styles
print(manager.list_styles())  # ['warrior', 'my_style', ...]
```

#### Style Adapters

Apply styles to different AI providers:

```python
# Apply style to generation parameters
params = {"prompt": "warrior sprite, attack pose"}
styled_params = manager.apply_style(style, "pixellab", params)

# styled_params now includes:
# - style_image (reference)
# - color_image (palette swatch)
# - outline, shading, detail settings

# Get adapter directly
adapter = manager.get_adapter("pollinations")
print(adapter.get_supported_features())
# ['prompt_style', 'reference_image_img2img', 'palette_prompt']
```

#### Supported Adapters

| Adapter | Provider | Features |
|---------|----------|----------|
| PixelLabAdapter | PixelLab | style_image, color_image, v2 style_options |
| PollinationsAdapter | Pollinations.ai | Prompt-based style, img2img |
| BFLKontextAdapter | Black Forest Labs | Reference image, strength control |

#### Convenience Functions

```python
from tools.pipeline.style import capture_style, apply_style, load_style

# Quick capture
style = capture_style(image, "quick_style", platform="genesis")

# Quick apply
params = apply_style(style, "pollinations", {"prompt": "hero sprite"})

# Quick load
style = load_style("warrior", styles_dir="styles/")
```

---

### AI Generation Module

**File:** `ai.py`, `style.py`, `processing.py`
**Phase:** 3.x (Partially Implemented)

Comprehensive AI-powered asset generation with platform-aware constraints.

#### Generation Approaches

**Tier-Based Generation** (Recommended)

Generate assets sized for a hardware tier, then export to specific platforms:

```python
from tools.pipeline.platforms import get_tier_info
from tools.pipeline.ai import AIAnalyzer, GenerativeResizer

# Generate for STANDARD tier (Genesis, SNES, PCE)
# Max 32x32 sprites, 16 colors, 128 entities
tier_info = GenesisConfig.get_tier_info()
print(f"Tier: {tier_info['tier_name']}")
print(f"Max entities: {tier_info['limits']['max_entities']}")

# Generate sprite at tier-appropriate size
resizer = GenerativeResizer()
resizer.generate_variant("concept.png", "sprite_32x32.png")
```

**Console-Specific Generation**

Generate assets with exact console constraints:

```python
from tools.pipeline.platforms import GenesisConfig, NESConfig

# Genesis: 16 colors, 32x32 max sprite, 80 sprites total
genesis_limits = {
    'max_colors': GenesisConfig.colors_per_palette,  # 16
    'max_sprite_size': (GenesisConfig.max_sprite_width,
                        GenesisConfig.max_sprite_height),  # (64, 64)
    'sprites_per_line': GenesisConfig.max_sprites_per_line,  # 20
}

# NES: 4 colors per palette, 64 sprites total, 8 per scanline
nes_limits = {
    'max_colors': NESConfig.colors_per_palette,  # 4
    'sprites_per_line': NESConfig.max_sprites_per_line,  # 8
}
```

#### View Types

**Orthogonal Views** (Top-Down/Side-View)

```python
# Standard orthogonal sprite - single facing direction
# Use for: platformers, top-down shooters
# Status: IMPLEMENTED via standard generation

from tools.pipeline.processing import SpriteConverter
converter = SpriteConverter(platform=GenesisConfig)
result = converter.index_sprite(img)  # Side or top view
```

**8-Way Sprite Generation** *(PLANNED - Not Implemented)*

```python
# Status: PLANNED (rotation.py not yet created)
# Workaround: Use PIL rotation + manual cleanup

from PIL import Image

def generate_8way_simple(img: Image.Image) -> list:
    """Generate 8 directions using PIL rotation (low quality)."""
    directions = []
    for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
        rotated = img.rotate(-angle, expand=False, resample=Image.NEAREST)
        directions.append(rotated)
    return directions

# Better approach: Generate E direction, mirror for W
def generate_8way_with_mirror(img: Image.Image) -> list:
    """Use mirroring for symmetric sprites."""
    e = img  # East (original)
    w = img.transpose(Image.FLIP_LEFT_RIGHT)  # West (mirrored)
    # N, S, NE, SE, NW, SW via rotation
    n = img.rotate(-90, expand=False, resample=Image.NEAREST)
    s = img.rotate(90, expand=False, resample=Image.NEAREST)
    return [n, img, s, w]  # Simplified 4-way
```

**Isometric Views** *(PLANNED - Not Implemented)*

```python
# Status: NOT IN PLAN - Needs addition
# Isometric sprites require specialized AI prompting
# Workaround: Use PixelLab with explicit isometric prompts

# Manual isometric conversion (approximate)
from PIL import Image, ImageTransform

def pseudo_isometric(img: Image.Image) -> Image.Image:
    """Apply pseudo-isometric skew (crude approximation)."""
    w, h = img.size
    # Skew transform coefficients
    coeffs = (1, -0.5, 0, 0, 1, 0, 0, 0)
    return img.transform((w, h), Image.AFFINE, coeffs, resample=Image.NEAREST)
```

#### Model Selection Strategy

**PixelLab** (Primary - Spec Conformity)
- Exact pixel dimensions
- Native 4bpp/8bpp output
- Palette constraint support
- Best for: Final production assets

**Pollinations/Flux** (Secondary - Creative Design)
- Great artistic quality
- Poor spec conformity (requires post-processing)
- Best for: Concept art, iteration, experimentation

**Recommended Hybrid Workflow:**

```python
# 1. Generate concept with creative model (Pollinations/Flux)
#    - High quality design, ignore constraints
#    - Iterate on style and composition

# 2. Refine with PixelLab for final asset
#    - Exact dimensions
#    - Palette conformity
#    - Production-ready output

from tools.pipeline.style import StyleManager, capture_style

# Capture style from Pollinations output
style = capture_style(concept_img, "my_style", platform="genesis")

# Apply to PixelLab generation (when implemented)
# params = style_manager.apply_style(style, "pixellab", base_params)
```

#### Full PixelLab Stack *(PLANNED)*

```python
# Status: API integration exists, full stack not documented
# PixelLab endpoints available:
# - /generate: Text-to-image with exact dimensions
# - /animate: Single frame to animation sequence
# - /rotate: 8-direction generation (high quality)
# - /upscale: 2x/4x with palette preservation

# Example (when fully implemented):
# pixellab.generate(prompt="warrior", width=32, height=32, palette="genesis")
# pixellab.animate(sprite, action="walk", frames=4)
# pixellab.rotate(sprite, directions=8)
```

#### AI-Powered Upscaling *(IMPLEMENTED)*

**File:** `ai.py` (`AIUpscaler` class)
**Phase:** 3.2 (Complete)

Upscale sprites using AI providers while maintaining platform constraints (color limits,
palette). Automatically requantizes the result using perceptual color matching.

```python
from tools.pipeline.ai import AIUpscaler
from PIL import Image

# Initialize upscaler
upscaler = AIUpscaler(platform="genesis")

# Simple 2x upscale
result = upscaler.upscale("sprite_32x32.png", scale=2)
if result['success']:
    result['image'].save("sprite_64x64.png")
    print(f"Upscaled via {result['provider']}")

# Upscale + requantize (recommended for platform compliance)
result = upscaler.upscale_and_requantize(
    "sprite.png",
    scale=2,
    max_colors=16,  # Genesis limit
    dither=True     # Optional Floyd-Steinberg dithering
)
if result['success']:
    result['image'].save("sprite_upscaled.png")
    print(f"Palette: {len(result['palette'])} colors")

# Upscale to specific palette
genesis_palette = [
    (0, 0, 0), (255, 0, 0), (0, 255, 0), (0, 0, 255),
    (255, 255, 0), (255, 0, 255), (0, 255, 255), (255, 255, 255),
]
result = upscaler.upscale_and_requantize(
    "sprite.png",
    scale=4,
    palette=genesis_palette,
    output_path="output/sprite_4x.png"
)

# Batch upscale multiple sprites
sprites = ["sprite1.png", "sprite2.png", "sprite3.png"]
results = upscaler.batch_upscale(
    sprites,
    scale=2,
    requantize=True,
    max_colors=16,
    show_progress=True
)
```

**Features:**
- AI-assisted upscaling (2x, 4x) via Pollinations, Pixie.haus, or SD Local
- Automatic requantization to platform color limits
- Perceptual color matching (CIEDE2000) for best quality
- Optional dithering for smooth gradients
- Fallback to nearest-neighbor if AI fails
- Batch processing support

**Fallback Chain:** `pollinations -> pixie_haus -> sd_local -> nearest-neighbor`

#### Background Removal *(IMPLEMENTED)*

**File:** `ai.py` (`BackgroundRemover` class)
**Phase:** 3.3 (Complete)

Remove backgrounds from sprites using AI (rembg) with automatic fallback to flood-fill
detection. Includes alpha-to-magenta conversion for Genesis/SGDK compatibility.

```python
from tools.pipeline.ai import BackgroundRemover

# Initialize remover
remover = BackgroundRemover()  # Default: 'auto' method

# Remove background (returns RGBA with transparency)
result = remover.remove_background("photo_sprite.png")
if result['success']:
    result['image'].save("sprite_transparent.png")
    print(f"Used method: {result['method_used']}")

# For Genesis/SGDK (magenta transparency)
result = remover.remove_for_genesis("photo_sprite.png")
if result['success']:
    result['image'].save("genesis_sprite.png")  # RGB with magenta bg

# Force specific method
result = remover.remove_background("sprite.png", method='flood_fill')
result = remover.remove_background("sprite.png", method='rembg')
result = remover.remove_background("sprite.png", method='threshold')

# Convert existing images
rgba = remover.magenta_to_alpha(genesis_sprite)  # Magenta -> Alpha
rgb = remover.alpha_to_magenta(rgba_sprite)       # Alpha -> Magenta

# Batch processing
sprites = ["sprite1.png", "sprite2.png", "sprite3.png"]
results = remover.batch_remove(sprites, for_genesis=True, show_progress=True)

# Check available methods
print(BackgroundRemover.get_available_methods())
# ['auto', 'rembg', 'flood_fill', 'threshold']  (if rembg installed)

# Available rembg models
print(BackgroundRemover.get_rembg_models())
# ['u2net', 'u2netp', 'u2net_human_seg', 'silueta', 'isnet-general-use', 'isnet-anime']
```

**Methods:**

- `rembg` - AI-based (u2net), highest quality, requires `pip install rembg`
- `flood_fill` - Rule-based, good for solid color backgrounds
- `threshold` - Simple corner sampling, fast but may have artifacts
- `auto` - Tries rembg → flood_fill → threshold

**Features:**

- AI background removal via rembg (7+ models)
- Automatic fallback chain
- Alpha ↔ Magenta conversion for Genesis
- Edge refinement post-processing
- Batch processing with progress output

#### Tileset Generation *(IMPLEMENTED)*

**File:** `ai.py` (`TilesetGenerator` class)
**Phase:** 3.4 (Complete)

Generate coherent tilesets from text prompts using multiple AI providers. Supports
auto-tile layouts (Wang/blob tiles) for seamless level building with platform-specific
palette constraints.

```python
from tools.pipeline.ai import TilesetGenerator

# Initialize generator
generator = TilesetGenerator(platform="genesis")

# Generate simple tileset (16 tiles)
result = generator.generate_tileset(
    "stone brick wall",
    tile_size=16,
    tile_count=16,
    style="medieval"
)
if result['success']:
    result['tileset_image'].save("stone_tileset.png")
    print(f"Generated {result['tile_count']} tiles via {result['provider']}")

# Generate auto-tile set (Wang/blob tiles for seamless edges)
result = generator.generate_autotile(
    "grass terrain",
    tile_size=16,
    layout='wang_16',  # 16-tile Wang/blob layout
    seed=12345
)
if result['success']:
    result['tileset_image'].save("grass_autotile.png")
    print(f"Layout: {result['layout']}")

# Generate with collision metadata
result = generator.generate_with_collision(
    "stone floor",
    tile_size=16,
    tile_count=16
)
if result['success']:
    for tile_data in result['collision_map']:
        print(f"Tile {tile_data['tile_index']}: solid={tile_data['solid']}")

# Batch generate multiple tilesets
tilesets = ["grass", "stone", "water", "lava"]
results = generator.batch_generate(
    tilesets,
    tile_size=16,
    tile_count=16,
    show_progress=True
)

# Check supported options
print(TilesetGenerator.get_tile_sizes())  # [8, 16, 24, 32]
print(TilesetGenerator.get_supported_layouts())  # ['wang_16', 'rpgmaker_47', 'simple_4']
```

**Features:**

- Multi-provider support (Pollinations, Pixie.haus, SD Local)
- Coherent tile generation with edge matching
- Auto-tile layouts (16-tile Wang/blob, 4-tile simple)
- Platform-specific palette constraints
- Automatic collision detection
- Batch generation with progress
- Seed-based coherence strategies

**Coherence Methods:**

- `guided` - Uses descriptive prompts for consistency (default)
- `seed` - Incremental seeds for variation within theme
- `reference` - Uses first tile as style reference

**Auto-tile Layouts:**

- `wang_16` - 16-tile Wang/blob layout covering all edge combinations
- `simple_4` - 4-tile simplified layout (isolated, horizontal, vertical, filled)
- `rpgmaker_47` - RPG Maker 47-tile format (planned)

#### Cross-Generational Asset Scaling *(IMPLEMENTED)*

```python
from tools.pipeline.cross_platform import CrossPlatformExporter

exporter = CrossPlatformExporter()

# Generate from high-res source, export to multiple platforms
exporter.add_platform(Platform.GENESIS, ExportConfig(max_colors=16))
exporter.add_platform(Platform.NES, ExportConfig(max_colors=4))
exporter.add_platform(Platform.GAMEBOY, ExportConfig(grayscale=True))

results = exporter.export("sprite_hires.png", output_dir="export/")
# Creates: genesis/sprite.png, nes/sprite.png, gameboy/sprite.png
```

---

### Quantization Module

**File:** `quantization/perceptual.py`, `quantization/dither_numba.py`
**Phase:** 0.7-0.8 (Complete)

High-performance perceptual color science and dithering for retro console palette conversion.

#### Perceptual Color Matching

Find the perceptually closest palette color using CIEDE2000 or CAM02-UCS:

```python
from tools.pipeline import (
    find_nearest_perceptual,
    find_nearest_rgb,
    calculate_color_distance,
    rgb_to_lab,
)

# Genesis palette (RGB tuples)
palette = [
    (0, 0, 0),        # Black
    (36, 36, 109),    # Dark blue
    (145, 109, 36),   # Brown
    (255, 255, 255),  # White
]

# Find nearest color (perceptually accurate)
pixel = (100, 80, 50)  # Brownish
idx = find_nearest_perceptual(pixel, palette, method='CIEDE2000')
print(f"Nearest color: {palette[idx]}")  # (145, 109, 36)

# Compare with simple RGB distance
idx_rgb = find_nearest_rgb(pixel, palette)
# May give different results for colors where perception differs from math

# Calculate perceptual distance between colors
dist = calculate_color_distance((255, 0, 0), (200, 50, 50), method='CIEDE2000')
print(f"Perceptual distance: {dist:.2f}")  # Lower = more similar

# Convert to Lab color space
lab = rgb_to_lab((145, 109, 36))
print(f"Lab: L={lab[0]:.1f}, a={lab[1]:.1f}, b={lab[2]:.1f}")
```

#### Optimal Palette Extraction

Extract the best N colors from an image using various algorithms:

```python
from tools.pipeline import extract_optimal_palette
from PIL import Image

img = Image.open("character.png")

# K-means clustering (default, best quality)
palette = extract_optimal_palette(img, num_colors=16, method='kmeans')

# Median cut (faster, good for photos)
palette = extract_optimal_palette(img, num_colors=16, method='median_cut')

# Octree (fastest, lower quality)
palette = extract_optimal_palette(img, num_colors=16, method='octree')

print(f"Extracted {len(palette)} colors: {palette[:4]}...")
```

#### PerceptualQuantizer Class

Full quantization pipeline with dithering support:

```python
from tools.pipeline import PerceptualQuantizer

# Create quantizer with platform constraints
quantizer = PerceptualQuantizer(
    color_method='CIEDE2000',  # or 'CAM02-UCS', 'RGB'
    dither_method='floyd-steinberg',  # or 'ordered', 'atkinson', 'none'
    dither_strength=1.0  # 0.0-2.0, for ordered dithering
)

# Quantize to fixed palette
genesis_palette = [(0,0,0), (36,36,109), (145,109,36), (255,255,255), ...]
result = quantizer.quantize(img, palette=genesis_palette)

# Or extract optimal palette first
result = quantizer.quantize(img, num_colors=16)

# Access results
result.image.save("quantized.png")  # Indexed PIL Image
print(f"Palette used: {result.palette}")
print(f"Index array shape: {result.indices.shape}")  # (H, W) uint8
```

#### High-Performance Dithering

Numba JIT-accelerated dithering for batch processing (10-50x faster):

```python
from tools.pipeline import (
    floyd_steinberg_numba,
    ordered_dither_numba,
    atkinson_dither_numba,
    DitherEngine,
    dither_image,
    is_numba_available,
    get_bayer_matrix,
)
import numpy as np

# Check if Numba acceleration is available
if is_numba_available():
    print("Numba JIT enabled - maximum performance")
else:
    print("Numba not installed - using numpy fallback")

# Quick dithering function
result_img = dither_image(
    image=img,
    palette=genesis_palette,
    method='floyd-steinberg',  # or 'ordered', 'atkinson', 'none'
    strength=1.0
)

# Low-level numba functions (for custom pipelines)
pixels = np.array(img, dtype=np.float32)  # (H, W, 3)
palette_array = np.array(genesis_palette, dtype=np.float32)  # (N, 3)

# Floyd-Steinberg error diffusion (best quality)
indices = floyd_steinberg_numba(pixels, palette_array)

# Ordered/Bayer dithering (consistent patterns, parallelizable)
bayer = get_bayer_matrix(4)  # 4x4 Bayer matrix (or 2, 8)
indices = ordered_dither_numba(pixels, palette_array, bayer, strength=1.0)

# Atkinson dithering (Mac-style, softer, higher contrast)
indices = atkinson_dither_numba(pixels, palette_array)
```

#### DitherEngine for Batch Processing

Process multiple sprites with the same palette efficiently:

```python
from tools.pipeline import DitherEngine

# Create engine (reuses compiled kernels)
engine = DitherEngine(
    method='floyd-steinberg',
    strength=1.0,
    bayer_size=4  # For ordered dithering
)

# Single image
result = engine.dither(img, genesis_palette)
result.image.save("dithered.png")

# Batch processing (100 sprites in seconds vs minutes)
images = [Image.open(f"sprite_{i}.png") for i in range(100)]
results = engine.dither_batch(images, genesis_palette, show_progress=True)

for i, r in enumerate(results):
    r.image.save(f"output/sprite_{i}.png")
```

#### Dithering Methods Comparison

| Method | Quality | Speed | Pattern | Best For |
|--------|---------|-------|---------|----------|
| `floyd-steinberg` | Excellent | Fast | Diffused | Photos, gradients |
| `ordered` | Good | Fastest | Regular grid | Retro look, animations |
| `atkinson` | Good | Fast | Softer diffusion | High contrast, Mac-style |
| `none` | Variable | Instant | None | Flat colors, testing |

#### Performance Tips

```python
# 1. Reuse DitherEngine for batches (avoids recompilation)
engine = DitherEngine(method='ordered')
results = [engine.dither(img, pal) for img in images]  # Efficient

# 2. Use ordered dithering for animations (consistent patterns)
engine = DitherEngine(method='ordered', bayer_size=4)

# 3. Pre-convert palette to numpy for low-level functions
palette_np = np.array(palette, dtype=np.float32)
# Reuse palette_np for all images

# 4. First call is slower (JIT compilation), subsequent calls are fast
_ = floyd_steinberg_numba(pixels, palette_np)  # Warmup
# Now all calls are 10-50x faster
```

---

### Sprite Effects Module

**File:** `effects.py`
**Phase:** 1.3 (Complete)

Generate common sprite effect variants algorithmically for hit flashes, damage states, and visual feedback.

#### Basic Effects

```python
from tools.pipeline import (
    white_flash,
    damage_tint,
    silhouette,
    outline,
    drop_shadow,
    glow,
    palette_swap,
)
from PIL import Image

sprite = Image.open("player.png")

# Hit flash (all pixels become white)
flashed = white_flash(sprite)

# Damage tint (red overlay at 50% intensity)
hurt = damage_tint(sprite, tint=(255, 0, 0), intensity=0.5)

# Silhouette (solid black shape)
shadow = silhouette(sprite, color=(0, 0, 0))

# Outline (1px black border)
outlined = outline(sprite, color=(0, 0, 0), width=1)

# Drop shadow
with_shadow = drop_shadow(sprite, offset=(2, 2))

# Glow effect
glowing = glow(sprite, color=(255, 255, 0), radius=2)
```

#### SpriteEffects Class

```python
from tools.pipeline import SpriteEffects, EffectConfig

# Custom configuration
config = EffectConfig(
    flash_color=(255, 255, 255),
    damage_color=(255, 0, 0),
    damage_intensity=0.5,
    outline_color=(0, 0, 0),
    outline_width=1,
)

effects = SpriteEffects(config)

# Generate complete hit effect set
variants = effects.generate_hit_set(sprite)
# Returns: {'normal': img, 'flash': img, 'damage': img, 'silhouette': img}

# Generate full effect set
all_variants = effects.generate_full_set(
    sprite,
    include_outline=True,
    include_shadow=True,
    include_glow=True
)

# Invulnerability blink (2-frame sequence)
blink_frames = effects.invulnerability_blink(sprite)
# Returns: [normal_frame, bright_frame]
```

#### Palette Swap

```python
from tools.pipeline import palette_swap

# Define color mapping (RGB tuples)
red_to_blue = {
    (255, 0, 0): (0, 0, 255),
    (200, 0, 0): (0, 0, 200),
    (150, 0, 0): (0, 0, 150),
}

# Create blue team variant
blue_sprite = palette_swap(red_sprite, red_to_blue)
```

#### Genesis-Specific Helpers

```python
from tools.pipeline import create_genesis_hit_palette, create_damage_palette

# Base palette (16 colors)
palette = [(0,0,0), (36,36,109), (145,109,36), ...]

# Create flash palette (all colors become white)
flash_pal = create_genesis_hit_palette(palette)
# Use CRAM swap for instant flash effect

# Create damage palette (colors tinted red)
damage_pal = create_damage_palette(palette, tint=(255, 0, 0), intensity=0.3)
```

#### Batch Processing

```python
from tools.pipeline import batch_generate_effects

sprites = [Image.open(f"enemy_{i}.png") for i in range(50)]

# Generate flash and damage variants for all
results = batch_generate_effects(
    sprites,
    effects_list=['flash', 'damage', 'silhouette'],
    show_progress=True
)

for i, variants in enumerate(results):
    variants['flash'].save(f"output/enemy_{i}_flash.png")
    variants['damage'].save(f"output/enemy_{i}_damage.png")
```

---

### Aseprite Integration Module

**File:** `integrations/aseprite.py`
**Phase:** 1.8 (Complete)

Automate sprite export from Aseprite files, preserving layers, tags, and metadata.

#### Check Availability

```python
from tools.pipeline import is_aseprite_available, AsepriteExporter

# Check if Aseprite CLI is available
if is_aseprite_available():
    print("Aseprite ready!")
else:
    print("Aseprite not installed or not in PATH")

# Get version
exporter = AsepriteExporter()
print(exporter.get_version())  # "Aseprite 1.3.x"
```

#### Export Sprite Sheet

```python
from tools.pipeline import AsepriteExporter

exporter = AsepriteExporter()

# Export with metadata
result = exporter.export_sheet(
    "characters/player.ase",
    "output/",
    sheet_type="horizontal",  # packed, horizontal, vertical, rows
    scale=1,
    trim=False,
    shape_padding=1,
)

if result.success:
    print(f"Exported: {result.sheet_path}")
    print(f"Frames: {result.frame_count}")
    print(f"Tags: {result.tags}")
    print(f"Layers: {result.layers}")
else:
    print(f"Error: {result.error}")
```

#### Parse Existing JSON (No Aseprite Needed)

```python
from tools.pipeline import parse_aseprite_json, frames_to_animation_sequences

# Parse pre-exported JSON
metadata = parse_aseprite_json("player.json")

print(f"Frame size: {metadata.frame_width}x{metadata.frame_height}")
print(f"Total frames: {len(metadata.frames)}")

# List animations
for tag in metadata.tags:
    print(f"  {tag.name}: frames {tag.start_frame}-{tag.end_frame}")

# Convert to animation sequences
sequences = frames_to_animation_sequences(metadata)
for seq in sequences:
    print(f"{seq['name']}: {len(seq['frames'])} frames, loop={seq['loop']}")
```

#### Extract Frames

```python
from tools.pipeline.integrations.aseprite import (
    extract_frames_from_sheet,
    extract_tag_frames,
)

# Extract all frames
all_frames = extract_frames_from_sheet("player.png", "player.json")

# Extract specific animation
walk_frames = extract_tag_frames("player.png", "player.json", "walk")
for i, frame in enumerate(walk_frames):
    frame.save(f"walk_{i:02d}.png")
```

#### Export Layers Separately

```python
exporter = AsepriteExporter()

# Export each layer as separate file
layers = exporter.export_layers_separate(
    "character.ase",
    "output/layers/"
)

# layers = {'body': Path('body.png'), 'shadow': Path('shadow.png'), ...}
```

#### Export Tags Separately

```python
# Export each animation tag as separate sprite sheet
tag_sheets = exporter.export_tags_separate(
    "character.ase",
    "output/animations/",
    sheet_type="horizontal"
)

# tag_sheets = {
#     'idle': AsepriteExportResult(...),
#     'walk': AsepriteExportResult(...),
#     'attack': AsepriteExportResult(...),
# }
```

#### Working with Metadata

```python
metadata = parse_aseprite_json("player.json")

# Get specific tag
walk_tag = metadata.get_tag("walk")
if walk_tag:
    print(f"Walk: {walk_tag.frame_count} frames")
    print(f"Direction: {walk_tag.direction}")  # forward, reverse, pingpong
    print(f"Loops: {walk_tag.is_looping}")

# Get frames for tag
walk_frames = metadata.get_frames_for_tag("walk")
for frame in walk_frames:
    print(f"  Frame {frame.index}: {frame.duration}ms at ({frame.x}, {frame.y})")

# Access slices (hitboxes, etc.)
for slice in metadata.slices:
    print(f"Slice '{slice.name}': {slice.width}x{slice.height} at ({slice.x}, {slice.y})")
    if slice.pivot_x is not None:
        print(f"  Pivot: ({slice.pivot_x}, {slice.pivot_y})")
```

---

## Core Architecture

> **Phase**: 0.9 | **Status**: ✅ Complete | **Files**: `core/`

The core architecture provides a unified pipeline with enforced safeguards that cannot be bypassed. It separates core logic from interfaces (CLI/GUI) for maintainability and future GUI integration.

### Architecture Overview

```
tools/pipeline/
├── core/                    # Core library (CLI/GUI agnostic)
│   ├── __init__.py         # Public exports
│   ├── config.py           # Unified configuration (dataclasses)
│   ├── pipeline.py         # Main orchestrator
│   ├── safeguards.py       # ENFORCED safety (cannot bypass)
│   └── events.py           # Progress callbacks for GUI
├── cli.py                   # CLI wrapper (thin layer)
└── [other modules]          # Existing functionality
```

### Quick Start

```python
from tools.pipeline.core import Pipeline, PipelineConfig, SafeguardConfig

# Create config (dry-run is ON by default for safety)
config = PipelineConfig(
    platform='genesis',
    safeguards=SafeguardConfig(
        dry_run=False,         # Enable real operations
        max_generations_per_run=10,
        max_cost_per_run=1.00,
    ),
)

# Create pipeline
pipeline = Pipeline(config)
pipeline.confirm()  # Required for interactive mode

# Process an image
result = pipeline.process('sprite.png', 'output/')

# Process Aseprite file (auto-detected)
result = pipeline.process('character.ase', 'output/')

# Generate from prompt
result = pipeline.generate('warrior with sword', 'output/')
```

### CLI Usage

```bash
# Check pipeline status
python -m tools.pipeline.cli --status

# Process (dry-run by default - SAFE!)
python -m tools.pipeline.cli sprite.png -o output/

# Actually process (requires explicit --no-dry-run)
python -m tools.pipeline.cli sprite.png -o output/ --no-dry-run

# Generate from prompt
python -m tools.pipeline.cli "warrior with sword" -o output/ --generate --no-dry-run

# Generate 8 directions
python -m tools.pipeline.cli "warrior" -o output/ --generate --8dir --no-dry-run

# Custom budget limits
python -m tools.pipeline.cli sprite.png -o output/ --max-gens 10 --max-cost 1.00
```

### Safeguards (ENFORCED)

These safeguards are built into the core and **cannot be bypassed**:

| Safeguard | Default | Description |
|-----------|---------|-------------|
| **Dry-run** | ON | Must explicitly use `--no-dry-run` to enable writes |
| **Budget** | 5 gens, $0.50 | Limits AI generations and cost per session |
| **Caching** | Always | Saves all API responses before processing |
| **Validation** | Always | Checks inputs before processing |
| **Confirmation** | Interactive | Prompts before destructive operations |

```python
from tools.pipeline.core import BudgetExhausted, DryRunActive

try:
    result = pipeline.generate('prompt', 'output/')
except DryRunActive as e:
    print("Dry-run mode is active - use --no-dry-run")
except BudgetExhausted as e:
    print("Budget exhausted - increase limits or wait")
```

### Event System (for GUI)

The event system enables real-time progress updates for GUI integration:

```python
from tools.pipeline.core import Pipeline, EventEmitter, EventType

# Create event emitter
emitter = EventEmitter()

# Register handlers
def on_progress(event):
    print(f"Progress: {event.percent:.0f}% - {event.message}")

def on_stage(event):
    print(f"Stage {event.stage_number}/{event.total_stages}: {event.stage_name}")

emitter.on(EventType.PROGRESS, on_progress)
emitter.on(EventType.STAGE_START, on_stage)

# Create pipeline with emitter
pipeline = Pipeline(config, event_emitter=emitter)
```

**Event Types:**
- `PROGRESS` - Percent complete and message
- `STAGE_START` - Stage beginning
- `STAGE_COMPLETE` - Stage finished
- `GENERATION_START` - AI generation starting
- `GENERATION_COMPLETE` - AI generation finished
- `ERROR` - Error occurred
- `WARNING` - Warning message

### Configuration Options

```python
from tools.pipeline.core import (
    PipelineConfig,
    SafeguardConfig,
    GenerationConfig,
    ProcessingConfig,
    ExportConfig,
)

config = PipelineConfig(
    platform='genesis',           # Target platform
    offline_mode=False,           # Disable AI features
    ai_provider='groq',           # AI provider (groq, gemini, openai, anthropic)
    verbose=True,                 # Verbose output

    safeguards=SafeguardConfig(
        dry_run=True,             # Dry-run mode (default: True)
        require_confirmation=True, # Interactive confirmation
        max_generations_per_run=5, # Max AI generations
        max_cost_per_run=0.50,    # Max cost in USD
        cache_dir='.ardk_cache',  # Cache directory
    ),

    generation=GenerationConfig(
        width=32,                 # Default width
        height=32,                # Default height
        generate_8_directions=False,  # Generate 8-dir views
    ),

    processing=ProcessingConfig(
        target_size=32,           # Target sprite size
        palette_name=None,        # Force specific palette
        generate_collision=False, # Generate collision data
    ),

    export=ExportConfig(
        generate_res_file=True,   # Generate .res file
        generate_headers=True,    # Generate .h headers
    ),
)
```

### Input Type Detection

The pipeline automatically detects input types:

| Input | Type | Handling |
|-------|------|----------|
| `sprite.png` | PNG | Image processing |
| `character.ase` | Aseprite | Layer/tag extraction |
| `sprites/` | Directory | Batch processing |
| `"pixel art warrior"` | Prompt | AI generation |

### Module Integration

The core pipeline integrates with all existing modules:

```python
# The pipeline auto-loads these modules as needed:
# - quantization/perceptual.py  (CIEDE2000 color matching)
# - quantization/dither_numba.py (JIT dithering)
# - integrations/aseprite.py (Aseprite export)
# - processing.py (tile optimization)
# - effects.py (sprite effects)
# - genesis_export.py (4bpp export)
# - ai.py (AI analysis)
# - pixellab_client.py (AI generation)
```

---

### Compression Module

**File:** `genesis_compression/genesis_compress.py`
**Phase:** 2.8 (SGDK Integration)

Compression algorithms for reducing ROM size of Genesis tile/sprite data.

#### Supported Formats

| Format | Best For | Typical Savings |
|--------|----------|-----------------|
| **Kosinski** | Mixed data, tilesets | 30-50% |
| **LZSS** | General purpose | 20-40% |
| **RLE** | Solid fills, repetitive patterns | 50-80% |

#### Basic Usage

```python
from tools.pipeline.genesis_compression import (
    GenesisCompressor,
    CompressionFormat,
    compress_kosinski,
    decompress_kosinski,
)

# Quick compression
compressor = GenesisCompressor()
result = compressor.compress(tile_data, CompressionFormat.KOSINSKI)

print(f"Original: {result.input_size} bytes")
print(f"Compressed: {result.output_size} bytes")
print(f"Savings: {result.savings_percent:.1f}%")

# Decompress
original = compressor.decompress(result.data, result.format)
```

#### Auto-Select Format

Let the compressor choose the best format based on data characteristics:

```python
result = compressor.compress(data, auto_select=True)
print(f"Selected format: {result.format.value}")
```

#### Compare All Formats

Test which format works best for your data:

```python
results = compressor.compare_formats(tileset_data)

for format_name, result in results.items():
    print(f"{format_name}: {result.savings_percent:.1f}% savings")
```

#### File-Based Compression

```python
# Compress a file
result = compressor.compress_file(
    "sprites/player.bin",
    format=CompressionFormat.KOSINSKI
)
# Creates sprites/player.kos

# Decompress back
compressor.decompress_file(
    "sprites/player.kos",
    "sprites/player_restored.bin",
    CompressionFormat.KOSINSKI
)
```

#### Convenience Functions

```python
# Direct compression/decompression
from tools.pipeline.genesis_compression import (
    compress_kosinski, decompress_kosinski,
    compress_lzss, decompress_lzss,
    compress_rle, decompress_rle,
)

compressed = compress_kosinski(raw_tiles)
original = decompress_kosinski(compressed)
```

#### SGDK Integration

Generate decompressor headers for your C code:

```python
from tools.pipeline.genesis_compression.genesis_compress import (
    generate_decompressor_header,
    generate_compression_stats_comment,
)

# Get C header for decompression routine
header = generate_decompressor_header(CompressionFormat.KOSINSKI)

# Get stats as C comment
comment = generate_compression_stats_comment(result)
```

**Note:** For production builds with large assets, consider using external tools like [clownlzss](https://github.com/Clownacy/clownlzss) for optimal compression. The pure Python implementation prioritizes portability over maximum compression.

---

## Production Hardening (Phase 5)

**Phase:** 5 (Complete)

Comprehensive error handling, validation, resource management, security, and metrics for production-ready pipeline operations.

### Error Handling

**File:** `errors.py`

Comprehensive exception hierarchy with clear error messages and actionable suggestions.

```python
from tools.pipeline.errors import (
    PipelineError,
    ImageLoadError,
    ValidationError,
    APIError,
    safe_image_open,
    validate_path,
    handle_error
)

# Safe image loading with comprehensive error handling
try:
    img = safe_image_open("sprite.png", convert_to='RGBA', max_size=(32, 32))
except ImageLoadError as e:
    print(f"Error: {e.message}")
    print(f"Suggestion: {e.suggestion}")
    print(f"Context: {e.context}")

# Path validation with traversal prevention
try:
    safe_path = validate_path("output/sprite.png", base_dir="output", must_exist=False)
except PathTraversalError as e:
    print(f"Security Error: {e}")

# Convert any error to standardized dict
error_dict = handle_error(exception, context="image_processing")
# Returns: {'success': False, 'error_code': ..., 'message': ..., 'suggestion': ...}
```

**Exception Hierarchy:**

- `PipelineError` - Base exception
  - `FileError` - File I/O errors
    - `FileNotFoundError` - File doesn't exist
    - `FilePermissionError` - Permission denied
    - `DiskSpaceError` - Insufficient disk space
  - `ImageError` - Image processing errors
    - `ImageLoadError` - Failed to load image
    - `ImageFormatError` - Unsupported format
    - `ImageDimensionError` - Exceeds platform limits
    - `ColorCountError` - Too many colors
  - `ValidationError` - Input validation errors
    - `InvalidInputError` - Invalid parameter
    - `PathTraversalError` - Path traversal attempt
    - `PlatformNotSupportedError` - Unknown platform
  - `APIError` - API-related errors
    - `APIConnectionError` - Connection failed
    - `APITimeoutError` - Request timed out
    - `APIRateLimitError` - Rate limit exceeded
    - `APIKeyError` - Invalid API key
    - `APIQuotaExceededError` - Quota exceeded
  - `ResourceError` - Resource management errors
    - `MemoryError` - Insufficient memory
    - `CacheLimitError` - Cache size exceeded
  - `ProcessingError` - Processing errors
    - `QuantizationError` - Quantization failed
    - `CompressionError` - Compression failed
    - `AnimationError` - Animation processing failed
  - `ConfigError` - Configuration errors
    - `MissingDependencyError` - Package not installed
    - `InvalidConfigError` - Invalid config file

### Input Validation

**File:** `validation.py`

Pre-flight validation for all pipeline inputs with platform-aware checks.

```python
from tools.pipeline.validation import (
    ImageValidator,
    AnimationValidator,
    TilesetValidator,
    validate_pipeline_input,
    validate_output_path
)

# Validate image for platform
validator = ImageValidator(platform="genesis", strict=False)
result = validator.validate("sprite.png", check_colors=True)

if not result.valid:
    for error in result.errors:
        print(f"Error: {error}")
    for warning in result.warnings:
        print(f"Warning: {warning}")

print(f"Image info: {result.info}")
# {'width': 32, 'height': 32, 'mode': 'RGBA', 'color_count': 15}

# Validate animation parameters
anim_validator = AnimationValidator(platform="genesis")
result = anim_validator.validate(
    action="walk",
    frame_count=8,
    frame_width=32,
    frame_height=32
)

# Validate tileset parameters
tileset_validator = TilesetValidator(platform="genesis")
result = tileset_validator.validate(
    tile_size=16,
    tile_count=16,
    description="stone brick wall"
)

# Unified validation entry point
result = validate_pipeline_input(
    'image',
    platform='genesis',
    path='sprite.png'
)

# Validate output path
result = validate_output_path("output/sprite.png", base_dir="output")
```

**Platform Limits:**

- **Genesis:** 32x32px sprites, 16 colors/palette, 8px tiles
- **NES:** 8x16px sprites, 4 colors/palette, 8px tiles
- **SNES:** 64x64px sprites, 16 colors/palette, 8px tiles
- **Game Boy:** 8x16px sprites, 4 colors/palette, 8px tiles
- **GBA:** 64x64px sprites, 256 colors/palette, 8px tiles

### Resource Management

**File:** `resources.py`

Context managers for proper cleanup, memory limits, and temporary file handling.

```python
from tools.pipeline.resources import (
    TempFileManager,
    ImagePool,
    FileWriter,
    memory_limit,
    check_system_resources
)

# Automatic temporary file cleanup
with TempFileManager() as tmp:
    temp_file = tmp.create(".png")
    temp_dir = tmp.create_dir()
    # Files automatically deleted on exit

# Image pool with memory limits
with ImagePool(max_size_mb=100) as pool:
    img1 = pool.load("sprite1.png")
    img2 = pool.load("sprite2.png")
    # All images automatically closed on exit

    # Check memory usage
    usage = pool.get_memory_usage()
    print(f"Using {usage['total_mb']:.1f}MB / {usage['max_mb']}MB")

# Safe file writing (atomic operations)
with FileWriter("output.png", check_disk_space=True) as writer:
    img.save(writer.temp_path)
    # File atomically moved to output.png on success

# Monitor memory usage
with memory_limit("image processing", max_mb=100):
    # Process images
    pass

# Check system resources before operation
resources = check_system_resources(
    required_memory_mb=100,
    required_disk_mb=50,
    output_dir="output"
)
```

### Security Hardening

**File:** `security.py`

Path traversal prevention, input sanitization, and API key protection.

```python
from tools.pipeline.security import (
    sanitize_filename,
    sanitize_path,
    secure_path,
    mask_api_key,
    sanitize_for_logging,
    validate_url,
    SecureConfig
)

# Sanitize filename
safe_name = sanitize_filename("sprite:test?.png")  # "sprite_test_.png"

# Sanitize path
safe_path = sanitize_path("output/../secret.txt")  # "output/secret.txt"

# Secure path validation (prevents traversal)
try:
    path = secure_path(
        "sprite.png",
        base_dir="output",
        must_exist=False,
        create_parents=True
    )
except PathTraversalError:
    print("Path traversal attempt detected!")

# Mask API keys for logging
masked = mask_api_key("sk-1234567890abcdef")  # "sk-1...cdef"

# Sanitize dict for logging (removes secrets)
data = {"api_key": "secret", "name": "sprite"}
safe_data = sanitize_for_logging(data)
# {'api_key': '***', 'name': 'sprite'}

# Validate URLs
is_safe = validate_url("https://api.example.com", allowed_schemes=['https'])

# Secure configuration management
config = SecureConfig()
config.load_from_env(prefix="PIPELINE_")
api_key = config.get("api_key")
print(config.safe_dict())  # All values masked for logging
```

**Security Features:**

- Path traversal prevention
- Filename sanitization
- API key masking in logs
- Sensitive data filtering
- URL validation
- Command injection prevention

### Logging & Metrics

**File:** `metrics.py`

Structured logging, performance metrics, and cost tracking.

```python
from tools.pipeline.metrics import (
    get_logger,
    MetricsCollector,
    CostTracker,
    PerformanceProfiler,
    track_operation
)

# Structured logging with automatic sanitization
logger = get_logger(__name__, structured=False)
logger.info("Processing sprite", extra={'width': 32, 'height': 32})

# Track operation with metrics
with track_operation("sprite_processing") as tracker:
    # Process sprite
    tracker.add_metric('frames_processed', 10)
    tracker.add_cost('pollinations', 0.01)

# Metrics collection
metrics = MetricsCollector()
metrics.record_metric("images_processed", 1)
metrics.start_timer("processing")
# ... do work ...
duration = metrics.stop_timer("processing")
metrics.record_cost("pollinations", 0.01)

# Get metrics summary
summary = metrics.get_metrics()
print(f"Total cost: ${summary['costs']}")

# Export to JSON
metrics.export_json("metrics.json")

# Cost tracking with budget limits
tracker = CostTracker(budget_limit=10.0)
try:
    tracker.add_cost(
        provider="pollinations",
        cost=0.01,
        description="Image generation"
    )
except ValueError as e:
    print(f"Budget exceeded: {e}")

summary = tracker.get_summary()
print(f"Total: ${summary['total_cost']:.2f}")
print(f"Remaining: ${summary['remaining_budget']:.2f}")

# Export cost report
tracker.export_report("costs.json")

# Performance profiling
profiler = PerformanceProfiler()
profiler.start()

profiler.start_stage("load_image")
# ... load image ...
profiler.end_stage()

profiler.start_stage("process_image", metadata={'size': '32x32'})
# ... process image ...
profiler.end_stage()

profiler.print_report()
# Performance Report
# ==================
# Total Duration: 1234.56ms
# Stages: 2
# ------------------
#   load_image: 234.56ms
#   process_image: 1000.00ms
#     size: 32x32
```

**Metrics Features:**

- Structured JSON logging
- Operation timing
- API cost tracking
- Budget limits
- Performance profiling
- Export to JSON
- Automatic data sanitization

---

## Feature Status

### Implemented (Ready to Use)

| Feature | File | Status |
|---------|------|--------|
| Sprite Analysis (AI) | `ai.py` | ✅ Complete |
| Multi-Provider Support | `ai.py` | ✅ 6 providers |
| Semantic Labeling | `ai.py` | ✅ Complete |
| Sprite Categorization | `ai.py`, `fallback.py` | ✅ AI + heuristic |
| Style Capture/Transfer | `style.py` | ✅ Complete |
| Console Limitations | `platforms.py` | ✅ All platforms |
| Palette Optimization | `palette_converter.py` | ✅ Genesis/NES/SNES |
| Animation Extraction | `animation.py` | ✅ Complete |
| Sheet Assembly | `sheet_assembler.py` | ✅ Bin-packing |
| Cross-Platform Export | `cross_platform.py` | ✅ Complete |
| Performance Analysis | `performance.py` | ✅ Scanline/VRAM |
| Collision Detection (AI) | `ai.py` | ✅ Hitbox inference |
| Fallback Analysis | `fallback.py` | ✅ Offline mode |
| Tile Optimization | `processing.py` | ✅ Mirror detection |
| Perceptual Quantization | `quantization/perceptual.py` | ✅ CIEDE2000, CAM02-UCS |
| JIT Dithering | `quantization/dither_numba.py` | ✅ Floyd-Steinberg, Ordered, Atkinson |
| Sprite Effects | `effects.py` | ✅ Flash, tint, silhouette, outline, glow |
| Aseprite Integration | `integrations/aseprite.py` | ✅ CLI export, JSON parsing |
| Core Architecture | `core/` | ✅ Pipeline, Safeguards, Events |
| Enforced Safeguards | `core/safeguards.py` | ✅ Budget, dry-run, caching |
| VGM Tools | `vgm/vgm_tools.py` | ✅ VGM parsing, XGM conversion, WOPN banks |
| Genesis Compression | `genesis_compression/` | ✅ Kosinski, LZSS, RLE |
| AI Generation Providers | `ai_providers/` | ✅ Pollinations, Pixie.haus, SD Local, fallback chain |
| AI Animation Generation | `ai.py` | ✅ AIAnimationGenerator, idle/walk/attack/death frames |

### Partially Implemented (Needs Work)

| Feature | File | Status | Issue |
|---------|------|--------|-------|
| PixelLab Integration | `ai.py` | ⚠️ Partial | API exists, workflow incomplete |
| Style Adapters | `style.py` | ⚠️ Partial | PixelLab adapter needs testing |
| Hybrid Model Stack | - | ⚠️ Concept | Not formalized in code |
| Tier-Based Generation | `platforms.py` | ⚠️ Data only | No generation workflow |

### Planned (Not Implemented)

| Feature | File | Phase | Priority |
|---------|------|-------|----------|
| 8-Way Rotation | `rotation.py` | 1.4 | IN PROGRESS |
| Isometric Views | - | Not planned | LOW |
| Orthogonal View Toggle | - | Not planned | LOW |

### Recently Implemented (Phase 3)

| Feature | File | Phase | Notes |
|---------|------|-------|-------|
| Tileset Generation | `ai.py` | 3.4 ✅ | `TilesetGenerator` with Wang/blob auto-tiles, collision detection |
| Background Removal | `ai.py` | 3.3 ✅ | `BackgroundRemover` with rembg, flood-fill, alpha↔magenta |
| AI Upscaling + Requantize | `ai.py` | 3.2 ✅ | `AIUpscaler` class with perceptual color matching |
| AI Animation Generation | `ai.py` | 3.1 ✅ | `AIAnimationGenerator` class, generates walk/attack/idle frames |
| AI Providers Module | `ai_providers/` | 3.6 ✅ | Pollinations, Pixie.haus, SD Local with fallback chain |
| Provider Fallback Chain | `ai_providers/registry.py` | 3.6 ✅ | Automatic provider selection and retry |
| Sprite Effects | `effects.py` | 1.3 ✅ | Flash, tint, silhouette, outline, glow |

### Known Broken/Issues

| Feature | Issue | Workaround |
|---------|-------|------------|
| Non-PixelLab models | Great design, poor spec conformity | Use for concepts, refine with PixelLab |
| 8-way generation | Not implemented | Manual PIL rotation + mirror |
| Isometric sprites | Not supported | Use PixelLab prompts directly |

---

## Common Workflows

### Workflow 1: New Character Setup

```python
from tools.pipeline import (
    AnimationExtractor,
    export_sgdk_animations,
    SGDKResourceGenerator,
    analyze_sprite_performance,
    AnimationFSM,
    create_character_fsm
)

# 1. Extract animations from sprite sheet
extractor = AnimationExtractor()
animations = extractor.extract_from_sheet(
    "raw/warrior.png",
    frame_size=(32, 32)
)

# 2. Check performance
report = analyze_sprite_performance("raw/warrior.png")
if report.warnings:
    print("Performance warnings - consider optimization")

# 3. Generate SGDK resources
gen = SGDKResourceGenerator(output_dir="res/")
gen.add_sprite("warrior", "raw/warrior.png", width=32, height=32)
gen.write_resource_file("resources.res")

# 4. Export animation definitions
export_sgdk_animations(animations, "res/warrior_anims.h")

# 5. Generate FSM code
fsm = create_character_fsm("warrior", animations)
fsm.export_c("src/warrior_fsm.c", "src/warrior_fsm.h")
```

### Workflow 2: Level Import from Tiled

```python
from tools.pipeline import (
    load_tiled_map,
    export_map_to_sgdk,
    extract_collision,
    SGDKResourceGenerator
)

# 1. Load Tiled map
level = load_tiled_map("tiled/level1.tmx")

# 2. Export map data
export_map_to_sgdk(level, "res/maps/", "level1")

# 3. Extract collision
extract_collision(level, "collision", "res/maps/level1_col.bin")

# 4. Add to resources
gen = SGDKResourceGenerator(output_dir="res/")
gen.add_map("level1", "res/maps/level1.bin")
gen.write_resource_file("resources.res")
```

---

## CLI Reference

### Main Pipeline CLI

The main pipeline CLI provides unified asset processing with enforced safeguards.

```bash
# Process PNG (dry-run by default - safe!)
python -m pipeline.cli sprite.png -o output/

# Actually process (requires explicit --no-dry-run)
python -m pipeline.cli sprite.png -o output/ --no-dry-run

# Process Aseprite file
python -m pipeline.cli character.ase -o output/ --no-dry-run

# Generate 8-direction character from prompt
python -m pipeline.cli "warrior with sword" -o output/ --generate --8dir

# Batch process directory
python -m pipeline.cli --batch input/ -o output/ --no-dry-run

# Check pipeline status
python -m pipeline.cli --status

# Custom safety limits
python -m pipeline.cli sprite.png -o output/ --max-gens 10 --max-cost 1.00
```

**Flags:**
| Flag | Description |
|------|-------------|
| `-o, --output` | Output directory (required) |
| `--batch DIR` | Batch process directory |
| `-g, --generate` | Treat input as generation prompt |
| `--8dir` | Generate 8 directional views |
| `--no-dry-run` | Actually process (default is dry-run) |
| `--max-gens N` | Max AI generations per run |
| `--max-cost USD` | Max cost in USD |
| `--platform` | Target platform (nes, genesis, snes, etc.) |
| `--status` | Show pipeline status and exit |

### Tile Optimization CLI

Optimize tilesets by deduplicating tiles with flip detection.

```bash
# Basic optimization
python optimize_tiles.py tileset.png --output optimized/

# Show statistics
python optimize_tiles.py tileset.png --stats

# Disable flip detection
python optimize_tiles.py tileset.png --no-flip-h --no-flip-v

# Platform-specific VRAM limits
python optimize_tiles.py tileset.png --platform nes --check-vram

# Batch processing
python optimize_tiles.py assets/*.png --batch --output optimized/

# Custom tile size
python optimize_tiles.py tileset.png --tile-width 16 --tile-height 16
```

**Flags:**
| Flag | Description |
|------|-------------|
| `--output, -o` | Output directory |
| `--stats` | Show optimization statistics |
| `--no-flip-h` | Disable horizontal flip detection |
| `--no-flip-v` | Disable vertical flip detection |
| `--platform` | Platform for VRAM limits (nes, genesis, snes, etc.) |
| `--check-vram` | Warn if exceeding VRAM budget |
| `--batch` | Batch process multiple files |
| `--tile-width` | Tile width in pixels (default: 8) |
| `--tile-height` | Tile height in pixels (default: 8) |

### File Watcher CLI

Watch directories for asset changes and auto-process.

```bash
# Watch sprites directory
python watch_assets.py assets/sprites --processor sprite

# Watch multiple directories
python watch_assets.py assets/sprites assets/tilesets

# Custom debounce time
python watch_assets.py assets/ --debounce 2.0

# Enable hot reload
python watch_assets.py assets/ --hot-reload --reload-cmd "make reload"

# Watch specific extensions
python watch_assets.py assets/ --extensions .png .aseprite

# Non-recursive (top level only)
python watch_assets.py assets/ --no-recursive

# Disable safety limits (development only)
python watch_assets.py assets/ --no-safety

# Custom safety limits
python watch_assets.py assets/ --max-file-size 10 --max-rate 30 --timeout 15
```

**Flags:**
| Flag | Description |
|------|-------------|
| `--processor` | Built-in processor (sprite, tileset, generic) |
| `--debounce` | Debounce time in seconds (default: 1.0) |
| `--extensions` | File extensions to watch |
| `--no-recursive` | Don't watch subdirectories |
| `--hot-reload` | Enable hot reload |
| `--reload-cmd` | Command to run on hot reload |
| `--no-safety` | Disable safety limits |
| `--max-file-size` | Max file size in MB |
| `--max-rate` | Max changes per minute |
| `--timeout` | Processing timeout in seconds |

### ARDK Generator CLI

Generate assets using the asset_generators module.

```bash
# Generate character
python ardk_generator.py character "warrior hero" --platform genesis --output output/

# Generate background
python ardk_generator.py background "forest scene" --platform genesis --output output/

# Generate parallax layers
python ardk_generator.py parallax "mountain landscape" --layers 3 --output output/

# Generate animated tiles
python ardk_generator.py animated "waterfall" --frames 4 --output output/
```

### Legacy CLI Commands

*(Deprecated - see ../DEPRECATED.md for migration guide)*

```bash
# Old: use asset_generators instead
python gen_sprites.py          # DEPRECATED
python gen_assets.py           # DEPRECATED
python generate_background.py  # DEPRECATED

# Use instead:
python ardk_generator.py character "description" --platform genesis
python ardk_generator.py background "description" --platform genesis
```

---

## Troubleshooting

### Common Issues

**"Too many colors" error**
```python
# Genesis sprites are limited to 16 colors (15 + transparency)
# Use palette converter to reduce:
from tools.pipeline import PaletteConverter, PaletteFormat

converter = PaletteConverter()
result = converter.convert("sprite.png", PaletteFormat.GENESIS)
```

**"Sprite too large" warning**
```
Genesis hardware limits:
- Max sprite size: 32x32 pixels (4x4 tiles)
- Max sprites per scanline: 20
- Max sprite pixels per scanline: 320
```

**Animation frames not detected**
```python
# Ensure consistent naming:
# Good: walk_01.png, walk_02.png, walk_03.png
# Bad: walk1.png, walk-2.png, walk_3.png

# Or specify pattern explicitly:
extractor.extract_from_files("sprites/*.png", pattern=r"(\w+)_(\d+)\.png")
```

---

## Known Issues & Workarounds

### AI Model Conformity Issues

**Problem:** Non-PixelLab models (Pollinations, Flux, SD) produce great designs but don't conform to retro console specifications.

**Symptoms:**
- Wrong dimensions (not 8-pixel aligned)
- Too many colors
- Anti-aliasing artifacts
- Non-indexed color mode

**Workaround - Hybrid Pipeline:**

```python
from tools.pipeline.processing import SpriteConverter
from tools.pipeline.palette_converter import PaletteConverter, PaletteFormat
from tools.pipeline.platforms import GenesisConfig

def conform_to_genesis(ai_output_path: str, output_path: str):
    """Post-process AI output to Genesis specs."""
    from PIL import Image

    img = Image.open(ai_output_path)

    # 1. Resize to valid sprite size (nearest neighbor)
    target_size = (32, 32)  # Must be 8-aligned
    img = img.resize(target_size, Image.NEAREST)

    # 2. Convert to indexed 16-color palette
    converter = PaletteConverter()
    result = converter.convert(img, PaletteFormat.GENESIS, max_colors=15)

    # 3. Replace background with magenta transparency
    # (assuming top-left pixel is background)
    result = result.convert('RGBA')
    bg_color = result.getpixel((0, 0))[:3]
    data = result.getdata()
    new_data = []
    for pixel in data:
        if pixel[:3] == bg_color:
            new_data.append((255, 0, 255, 0))  # Magenta transparent
        else:
            new_data.append(pixel)
    result.putdata(new_data)

    result.save(output_path)
    return output_path
```

### 8-Way Sprite Generation Not Available

**Problem:** `rotation.py` is planned but not implemented.

**Workaround - Manual 4-Way with Mirroring:**

```python
from PIL import Image

def create_4way_sprites(east_facing: Image.Image) -> dict:
    """Create 4 directions from a single east-facing sprite."""
    return {
        'E': east_facing,
        'W': east_facing.transpose(Image.FLIP_LEFT_RIGHT),
        'N': east_facing.rotate(-90, expand=False, resample=Image.NEAREST),
        'S': east_facing.rotate(90, expand=False, resample=Image.NEAREST),
    }

# For 8-way, diagonal directions are lower quality:
def create_8way_sprites(east_facing: Image.Image) -> dict:
    """Create 8 directions (diagonals are rotated, lower quality)."""
    sprites = create_4way_sprites(east_facing)
    sprites.update({
        'NE': east_facing.rotate(-45, expand=False, resample=Image.NEAREST),
        'SE': east_facing.rotate(45, expand=False, resample=Image.NEAREST),
        'NW': sprites['W'].rotate(-45, expand=False, resample=Image.NEAREST),
        'SW': sprites['W'].rotate(45, expand=False, resample=Image.NEAREST),
    })
    return sprites
```

### Isometric Sprites Not Supported

**Problem:** No built-in isometric view generation.

**Workaround - PixelLab Prompting:**

```python
# Use explicit prompts for PixelLab:
isometric_prompt = """
Create a 32x32 pixel art sprite in isometric view (30-degree angle).
Subject: warrior character, idle pose
Style: 16-bit Genesis, 16 colors max
View: Isometric (2:1 pixel ratio)
"""

# After generation, validate proportions:
# - Isometric tiles should be 2:1 width:height ratio
# - Common sizes: 64x32, 32x16, 128x64
```

### AI Upscaling Loses Pixel Art Quality

**Problem:** Standard AI upscalers add anti-aliasing and blur.

**Workaround - Integer Scaling:**

```python
from PIL import Image

def pixel_perfect_upscale(img: Image.Image, scale: int = 2) -> Image.Image:
    """Upscale with nearest neighbor (preserves pixels)."""
    w, h = img.size
    return img.resize((w * scale, h * scale), Image.NEAREST)

# For AI upscaling that adds detail (when implemented):
# 1. Upscale with AI
# 2. Re-quantize to platform palette
# 3. Apply ordered dithering if needed
```

### Style Inconsistency Across Generations

**Problem:** Multiple AI generation calls produce inconsistent styles.

**Workaround - Style Capture + Reference:**

```python
from tools.pipeline.style import StyleManager, capture_style

# 1. Generate first sprite and capture its style
manager = StyleManager(styles_dir="styles/")
first_sprite = Image.open("first_generated.png")
style = manager.capture_style(first_sprite, "my_game_style", platform="genesis")
manager.save_style(style, include_reference=True)

# 2. Apply style to subsequent generations
# (Requires adapter support for your AI provider)
params = {"prompt": "warrior attack pose"}
styled_params = manager.apply_style(style, "pollinations", params)

# 3. For PixelLab, use style_image parameter directly
```

### Performance Analysis False Positives

**Problem:** Performance warnings for sprites that won't all be on screen.

**Workaround - Analyze Actual Game Scenarios:**

```python
from tools.pipeline.performance import PerformanceBudgetCalculator

calc = PerformanceBudgetCalculator()

# Define actual game scenario (not just all sprites)
scenario = [
    {'name': 'player', 'y': 100, 'height': 32, 'count': 1},
    {'name': 'enemy', 'y': 120, 'height': 24, 'count': 5},  # Max enemies on screen
    {'name': 'bullet', 'y': 110, 'height': 8, 'count': 10},
]

# Expand to individual sprites for analysis
sprites = []
for entity in scenario:
    for i in range(entity['count']):
        sprites.append({
            'y': entity['y'] + (i * 2),  # Stagger slightly
            'height': entity['height']
        })

report = calc.analyze_sprite_layout(sprites)
# Only shows real in-game violations
```

---

## Contributing

### Adding Documentation

When implementing a new feature:

1. Add usage examples to this document under the appropriate module section
2. Include common use cases and gotchas
3. Update the Table of Contents if adding new sections
4. Add CLI flags to the CLI Reference section

### Documentation Checklist

For each new feature, document:

- [ ] Module location and phase
- [ ] Key classes and functions
- [ ] Basic usage example
- [ ] Advanced usage (if applicable)
- [ ] Common errors and solutions
- [ ] CLI flags (if applicable)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0.0 | 2026-01-18 | Added Tileset Generation (Phase 3.4): TilesetGenerator with Wang/blob auto-tiles, collision detection, multi-provider support. **Phase 3 Complete!** |
| 1.9.0 | 2026-01-18 | Added Background Removal (Phase 3.3): BackgroundRemover with rembg, flood-fill, alpha↔magenta conversion |
| 1.8.0 | 2026-01-18 | Added AI Upscaling + Requantize (Phase 3.2): AIUpscaler class with perceptual color matching, dithering, batch support |
| 1.7.0 | 2026-01-18 | Added AI Animation Generation (Phase 3.1): AIAnimationGenerator, animation sprite sheets, SGDK integration |
| 1.6.0 | 2026-01-17 | Added AI Generation Providers (Phase 3.6): Pollinations, Pixie.haus, SD Local with fallback chain |
| 1.5.0 | 2026-01-17 | Added VGM Tools (Phase 2.7) and Genesis Compression (Phase 2.8) modules |
| 1.4.0 | 2026-01-17 | Added Sprite Effects (Phase 1.3) and Aseprite Integration (Phase 1.8) modules |
| 1.3.0 | 2026-01-17 | Added Quantization module (Phase 0.7-0.8): perceptual color science, CIEDE2000, Numba-accelerated dithering |
| 1.2.0 | 2026-01-17 | Added AI Generation module, Feature Status tables, Known Issues & Workarounds |
| 1.1.0 | 2026-01-17 | Added Processing, AI Integration, Fallback, and Style System modules |
| 1.0.0 | 2026-01-17 | Initial documentation covering existing modules |

---

*This document is auto-updated as features are implemented. For planned features, see [ASSET_PIPELINE_PLAN.md](ASSET_PIPELINE_PLAN.md).*
