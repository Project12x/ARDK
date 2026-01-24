# ARDK Pixel Pipeline Documentation

> **Version**: 3.1.0
> **Target Platform**: Genesis/Mega Drive (SGDK)
> **Secondary Platforms**: NES, Game Boy, Master System, Game Gear

A comprehensive sprite and asset processing pipeline for retro game development, with first-class support for SGDK (Sega Genesis Development Kit).

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Module Overview](#module-overview)
3. [Animation System](#animation-system)
4. [Sprite Sheet Tools](#sprite-sheet-tools)
5. [Genesis/SGDK Export](#genesissgdk-export)
6. [Palette Management](#palette-management)
7. [Performance Analysis](#performance-analysis)
8. [Collision Visualization](#collision-visualization)
9. [Animation FSM Generator](#animation-fsm-generator)
10. [Cross-Platform Export](#cross-platform-export)
11. [Complete Workflow Example](#complete-workflow-example)

---

## Quick Start

```python
from pipeline import (
    # Animation
    AnimationExtractor, export_sgdk_animations,
    # Sprite sheets
    SpriteSheetAssembler, dissect_sheet,
    # Genesis export
    export_genesis_tilemap_optimized, export_vdp_ready_sprite,
    # Palette
    PaletteManager, PaletteConverter,
    # Performance
    PerformanceBudgetCalculator,
    # Debug
    CollisionVisualizer,
    # FSM
    AnimationFSM, create_character_fsm,
)
```

### Minimal Example: Export Sprite to SGDK

```python
from PIL import Image
from pipeline import export_vdp_ready_sprite, SGDKResourceGenerator

# Load sprite sheet
sheet = Image.open("player.png")

# Export VDP-ready binary data
tile_data, palette_data, sat_data = export_vdp_ready_sprite(
    sheet,
    palette_index=0,
    output_prefix="player"
)

# Generate .res file for SGDK
gen = SGDKResourceGenerator()
gen.add_sprite("player", "player.png", width=32, height=32)
gen.write("res/sprites.res")
```

---

## Module Overview

| Module | Purpose | Key Classes/Functions |
|--------|---------|----------------------|
| `animation` | Animation metadata extraction | `AnimationExtractor`, `export_sgdk_animations` |
| `sheet_assembler` | Sprite sheet assembly/dissection | `SpriteSheetAssembler`, `dissect_sheet` |
| `genesis_export` | Genesis 4bpp tile export | `export_genesis_tilemap_optimized`, `export_vdp_ready_sprite` |
| `palette_converter` | Cross-platform palette conversion | `PaletteConverter`, `PaletteFormat` |
| `palette_manager` | Game-wide palette management | `PaletteManager`, `PaletteSlot` |
| `sgdk_resources` | SGDK .res file generation | `SGDKResourceGenerator`, `SpriteResource` |
| `performance` | VDP performance analysis | `PerformanceBudgetCalculator`, `PerformanceReport` |
| `collision_editor` | Collision box visualization | `CollisionVisualizer`, `render_collision_debug` |
| `animation_fsm` | Animation state machine C code | `AnimationFSM`, `create_character_fsm` |
| `cross_platform` | Multi-platform asset export | `CrossPlatformExporter`, `Platform`, `export_multi_platform` |

---

## Animation System

### AnimationExtractor

Extracts animation metadata from sprite sheets, detecting patterns like idle, walk, attack cycles.

```python
from pipeline import AnimationExtractor, AnimationPattern

# Create extractor
extractor = AnimationExtractor()

# Define expected animations
patterns = [
    AnimationPattern("idle", frame_count=4, row=0),
    AnimationPattern("walk", frame_count=6, row=1),
    AnimationPattern("attack", frame_count=4, row=2, one_shot=True),
]

# Extract from sheet
sequences = extractor.extract(
    "player_sheet.png",
    patterns=patterns,
    frame_width=32,
    frame_height=32
)

# Export to SGDK header
from pipeline import export_sgdk_animations
export_sgdk_animations(sequences, "player_anim.h")
```

### Animation Timing

Default frame timings (in 1/60s ticks):

| Animation | Default Ticks | Notes |
|-----------|---------------|-------|
| idle | 10 | ~6 FPS, relaxed |
| walk | 6 | ~10 FPS, moderate |
| run | 4 | ~15 FPS, fast |
| attack | 4 | Quick, responsive |
| hurt | 8 | Brief stun |
| death | 12 | Dramatic, slow |

### AI-Powered Sheet Generation

```python
from pipeline import (
    generate_animation_bundle,
    generate_sprite_sheet_prompt,
)

# Generate prompt for AI image generation
prompt = generate_sprite_sheet_prompt(
    character="armored knight",
    animations=["idle", "walk", "attack"],
    style="16-bit Genesis pixel art",
    frame_size=32
)

# After getting AI-generated sheet, process it
bundle = generate_animation_bundle(
    sheet_path="ai_generated_knight.png",
    animations=["idle", "walk", "attack"],
    frame_width=32,
    frame_height=32
)
```

---

## Sprite Sheet Tools

### SpriteSheetAssembler

Assembles individual frames into optimized sprite sheets.

```python
from pipeline import SpriteSheetAssembler, PackingAlgorithm
from PIL import Image

assembler = SpriteSheetAssembler(
    algorithm=PackingAlgorithm.BINARY_TREE,  # Efficient packing
    padding=1,                                # 1px between sprites
    power_of_two=True                         # Genesis-friendly sizes
)

# Add frames
frames = [Image.open(f"frame_{i}.png") for i in range(8)]
for i, frame in enumerate(frames):
    assembler.add_frame(frame, name=f"walk_{i}")

# Assemble
sheet, layout = assembler.assemble()
sheet.save("walk_sheet.png")

# Layout contains frame positions
for placement in layout.placements:
    print(f"{placement.name}: ({placement.x}, {placement.y})")
```

### Sheet Dissection

Split existing sprite sheets into individual sprites.

```python
from pipeline import dissect_sheet, GridDissector

# Grid-based dissection (uniform frame sizes)
dissector = GridDissector(frame_width=32, frame_height=32)
sprites = dissector.dissect("spritesheet.png")

# Or use auto-detection
from pipeline import SheetDissector
dissector = SheetDissector()
detected = dissector.detect_sprites("spritesheet.png")

for sprite in detected:
    print(f"Found sprite at ({sprite.x}, {sprite.y}) size {sprite.width}x{sprite.height}")
```

---

## Genesis/SGDK Export

### Tile Deduplication with Mirror Detection

The Genesis VDP supports horizontal and vertical tile flipping. This pipeline detects mirrored tiles to reduce VRAM usage.

```python
from pipeline import (
    export_genesis_tilemap_optimized,
    TileOptimizationStats,
    find_tile_match
)

# Export with automatic deduplication
tiles, tilemap, stats = export_genesis_tilemap_optimized(
    image_path="background.png",
    detect_mirrors=True  # Enable H/V flip detection
)

print(f"Original tiles: {stats.original_count}")
print(f"Unique tiles: {stats.unique_count}")
print(f"Mirrors found: {stats.h_flip_count + stats.v_flip_count + stats.hv_flip_count}")
print(f"VRAM saved: {stats.bytes_saved} bytes")
```

### VDP-Ready Export

Export sprites with proper VDP formats for direct hardware use.

```python
from pipeline import (
    export_vdp_ready_sprite,
    export_sprite_attribute_table,
    export_cram_palette,
    align_for_dma,
    SpriteAttribute
)

# Complete VDP-ready export
tile_data, palette_data, sat_entry = export_vdp_ready_sprite(
    sprite_image,
    palette_index=1,      # PAL1 (0-3)
    priority=True,        # Draw above background
    output_prefix="enemy"
)

# Manual SAT entry creation
attr = SpriteAttribute(
    y=100,
    size=0x05,           # 2x2 tiles (16x16 pixels)
    link=1,              # Next sprite in chain
    priority=True,
    palette=1,
    h_flip=False,
    v_flip=False,
    tile_index=64
)
sat_bytes = export_sprite_attribute_table([attr])

# Align data for DMA transfers
aligned_tiles = align_for_dma(tile_data, alignment=256)
```

### SGDK Resource File Generation

```python
from pipeline import (
    SGDKResourceGenerator,
    SpriteResource,
    TilesetResource,
    PaletteResource,
    Compression,
    SpriteOptimization
)

gen = SGDKResourceGenerator()

# Add sprite definition
gen.add_sprite(
    name="player",
    path="gfx/player.png",
    width=32,
    height=32,
    compression=Compression.BEST,
    optimization=SpriteOptimization.BALANCED
)

# Add tileset
gen.add_tileset(
    name="level1_tiles",
    path="gfx/level1.png",
    compression=Compression.FAST
)

# Add palette
gen.add_palette(
    name="player_pal",
    path="gfx/player.png"
)

# Write .res file
gen.write("res/resources.res")

# Output example:
# SPRITE player "gfx/player.png" 4 4 BEST NONE
# TILESET level1_tiles "gfx/level1.png" FAST ALL
# PALETTE player_pal "gfx/player.png"
```

---

## Palette Management

### PaletteManager

Manage game-wide palettes with slot allocation and validation.

```python
from pipeline import (
    PaletteManager,
    PaletteSlot,
    PalettePurpose,
    create_genesis_game_palettes
)

# Quick setup for typical Genesis game
manager = create_genesis_game_palettes()

# Or manual configuration
manager = PaletteManager(platform="genesis")

# Register palette slots
manager.register_slot(PaletteSlot(
    index=0,
    name="player",
    purpose=PalettePurpose.SPRITE,
    colors=[(0,0,0), (255,0,0), (0,255,0), ...]  # 16 colors
))

manager.register_slot(PaletteSlot(
    index=1,
    name="enemies",
    purpose=PalettePurpose.SPRITE,
    locked=False  # Can be swapped at runtime
))

# Validate all palettes
result = manager.validate_all()
if not result.valid:
    for error in result.errors:
        print(f"Error: {error}")

# Get usage stats
stats = manager.get_usage_stats()
print(f"Slots used: {stats.slots_used}/4")
print(f"Colors used: {stats.colors_used}/64")
```

### PaletteConverter

Convert between platform color formats.

```python
from pipeline import PaletteConverter, PaletteFormat

converter = PaletteConverter()

# Convert RGB to Genesis CRAM format (9-bit BGR)
genesis_colors = converter.convert(
    colors=[(255, 128, 64), (0, 200, 100)],
    target_format=PaletteFormat.GENESIS_CRAM
)

# Convert to NES palette indices
nes_indices = converter.convert(
    colors=[(255, 0, 0), (0, 255, 0)],
    target_format=PaletteFormat.NES
)

# Available formats
# - PaletteFormat.GENESIS_CRAM  (9-bit BGR, 512 colors)
# - PaletteFormat.NES           (Fixed 54-color palette)
# - PaletteFormat.GAMEBOY       (4 shades of green/gray)
# - PaletteFormat.RGB888        (24-bit standard)
# - PaletteFormat.RGB565        (16-bit)
```

---

## Performance Analysis

### PerformanceBudgetCalculator

Analyze sprite layouts against Genesis VDP hardware limits.

```python
from pipeline import (
    PerformanceBudgetCalculator,
    PerformanceReport,
    analyze_sprite_performance
)

calculator = PerformanceBudgetCalculator()

# Define sprite positions (from your game layout)
sprites = [
    {'x': 10, 'y': 100, 'width': 32, 'height': 32, 'name': 'player'},
    {'x': 50, 'y': 102, 'width': 16, 'height': 16, 'name': 'bullet_1'},
    {'x': 80, 'y': 100, 'width': 24, 'height': 24, 'name': 'enemy_1'},
    # ... more sprites
]

# Analyze layout
report = calculator.analyze_sprite_layout(sprites)

# Check results
print(report.summary())

# Detailed checks
if report.scanline_violations:
    print(f"WARNING: {len(report.scanline_violations)} scanlines exceed 20 sprite limit!")
    for scanline in report.scanline_violations[:5]:
        count = report.sprites_per_scanline[scanline]
        print(f"  Line {scanline}: {count} sprites")

# Get optimization suggestions
for suggestion in calculator.suggest_optimizations(report):
    print(f"- {suggestion}")
```

### DMA Budget Estimation

```python
# Estimate DMA transfer time
tile_bytes = 2048  # 64 tiles * 32 bytes
palette_bytes = 32  # 16 colors * 2 bytes

scanlines_needed, dma_report = calculator.estimate_dma_time(
    tile_bytes=tile_bytes,
    palette_bytes=palette_bytes
)

print(f"DMA will consume {scanlines_needed:.1f} scanlines")
print(f"Vblank budget used: {dma_report.vblank_budget_used:.1f}%")

if scanlines_needed > 40:  # Exceeds vblank
    print("WARNING: DMA exceeds vblank! Split across multiple frames.")
```

### Visual Heatmap

```python
# Generate visual density heatmap (requires PIL)
heatmap = calculator.generate_heatmap(sprites, width=320, height=224, scale=2)
if heatmap:
    heatmap.save("sprite_density.png")
    # Colors: Green=safe, Yellow=caution, Orange=near limit, Red=overflow
```

### Hardware Limits Reference

| Limit | Value | Description |
|-------|-------|-------------|
| MAX_SPRITES | 80 | Total sprites in SAT |
| MAX_SPRITES_PER_LINE | 20 | Sprites per scanline |
| MAX_PIXELS_PER_LINE | 320 | Sprite pixel width per line |
| DMA_BYTES_PER_LINE | 168 | DMA transfer rate |
| VBLANK_LINES | 40 | Available vblank scanlines (NTSC) |

---

## Collision Visualization

### CollisionVisualizer

Render collision boxes overlaid on sprites for debugging.

```python
from pipeline import (
    CollisionVisualizer,
    CollisionBox,
    render_collision_debug,
    export_collision_debug_image
)
from PIL import Image

viz = CollisionVisualizer()

# Load sprite
sprite = Image.open("player.png")

# Define collision boxes
hitbox = CollisionBox(x=8, y=4, width=16, height=24, box_type="hitbox")
hurtbox = CollisionBox(x=4, y=0, width=24, height=32, box_type="hurtbox")

# Render overlay (4x scale for visibility)
overlay = viz.render_overlay(
    sprite,
    hitbox=hitbox,
    hurtbox=hurtbox,
    scale=4,
    show_sprite_outline=True
)
overlay.save("player_collision_debug.png")
```

### Quick Debug Function

```python
# One-liner debug image
overlay = render_collision_debug(
    sprite_image,
    hitbox={'x': 8, 'y': 4, 'width': 16, 'height': 24},
    hurtbox={'x': 4, 'y': 0, 'width': 24, 'height': 32},
    scale=4
)

# Or from file paths
export_collision_debug_image(
    "sprites/player.png",
    "debug/player_collision.png",
    hitbox={'x': 8, 'y': 4, 'width': 16, 'height': 24}
)
```

### Animated GIF Export

```python
# Generate debug animation showing collision per frame
frames = [Image.open(f"attack_{i}.png") for i in range(4)]

# Different collision boxes per frame (attack hitbox grows)
collisions = [
    (CollisionBox(4, 4, 8, 24, "hitbox"), CollisionBox(0, 0, 32, 32, "hurtbox")),
    (CollisionBox(8, 4, 16, 24, "hitbox"), CollisionBox(0, 0, 32, 32, "hurtbox")),
    (CollisionBox(12, 4, 24, 24, "hitbox"), CollisionBox(0, 0, 32, 32, "hurtbox")),  # Extended!
    (CollisionBox(4, 4, 8, 24, "hitbox"), CollisionBox(0, 0, 32, 32, "hurtbox")),
]

viz.render_animation(frames, collisions, "attack_debug.gif", fps=10, scale=4)
```

### Color Scheme

| Box Type | Fill Color | Use Case |
|----------|------------|----------|
| hitbox | Red (50% transparent) | Damage dealing zones |
| hurtbox | Green (50% transparent) | Vulnerable zones |
| trigger | Blue (50% transparent) | Interaction zones |

---

## Animation FSM Generator

### AnimationFSM

Generate SGDK-compatible C code for animation state machines.

```python
from pipeline import (
    AnimationFSM,
    AnimationState,
    Transition,
    create_character_fsm
)

# Quick setup for typical character
fsm = create_character_fsm("player", include_combat=True)

# Validate before export
result = fsm.validate()
print(result.summary())

# Export C code
fsm.export_sgdk("src/player_anim")
# Creates: src/player_anim.h and src/player_anim.c
```

### Manual FSM Definition

```python
fsm = AnimationFSM("enemy", initial_state="patrol")

# Define states
patrol = AnimationState("patrol", anim_index=0, loop=True)
chase = AnimationState("chase", anim_index=1, loop=True)
attack = AnimationState("attack", anim_index=2, loop=False)
hurt = AnimationState("hurt", anim_index=3, loop=False)

# Add transitions
patrol.add_transition(Transition("chase", condition="event_see_player"))
chase.add_transition(Transition("patrol", condition="!event_see_player"))
chase.add_transition(Transition("attack", condition="event_in_range"))
attack.add_transition(Transition("chase", condition="anim_complete"))

# Hurt can interrupt any state (high priority)
for state in [patrol, chase, attack]:
    state.add_transition(Transition("hurt", condition="event_damage", priority=10))
hurt.add_transition(Transition("patrol", condition="anim_complete"))

# Add to FSM
for state in [patrol, chase, attack, hurt]:
    fsm.add_state(state)

# Export
fsm.export_sgdk("src/enemy_anim")
```

### Condition Types

| Condition | Syntax | Example |
|-----------|--------|---------|
| Input | `input_X` / `!input_X` | `input_move`, `!input_attack` |
| Animation Complete | `anim_complete` | One-shot finished |
| Timer | `timer_Nms` | `timer_500ms`, `timer_30` (frames) |
| Event | `event_X` | `event_damage`, `event_land` |
| Custom | `function_name` | Calls user function |

### Generated C Code Usage

```c
// In your game code
#include "player_anim.h"

void Player_init(Sprite* sprite) {
    Player_AnimFSM_init(sprite);
}

void Player_update(Sprite* sprite, u16 joypad) {
    // Build input flags
    u16 input = 0;
    if (joypad & BUTTON_LEFT || joypad & BUTTON_RIGHT) {
        input |= PLAYER_INPUT_MOVE;
    }
    if (joypad & BUTTON_A) {
        input |= PLAYER_INPUT_ATTACK;
    }

    // Update FSM
    Player_AnimFSM_update(sprite, input);

    // Check current state if needed
    if (Player_AnimFSM_getState() == PLAYER_ANIM_ATTACK) {
        // Attack logic...
    }
}

void Player_onHit(Sprite* sprite) {
    // Trigger damage event
    Player_AnimFSM_triggerEvent(sprite, PLAYER_EVENT_DAMAGE);
}
```

### JSON Export/Import

```python
# Export FSM to JSON for external tools
fsm.export_json("player_fsm.json")

# Load FSM from JSON
fsm = AnimationFSM.load_json("player_fsm.json")
```

---

## Cross-Platform Export

### CrossPlatformExporter

Export sprites to multiple retro platforms from a single source image.

```python
from pipeline import (
    CrossPlatformExporter,
    Platform,
    ExportConfig,
    export_multi_platform,
    get_platform_info,
)

# Quick export to multiple platforms
results = export_multi_platform(
    "player.png",
    platforms=[Platform.GENESIS, Platform.NES, Platform.GAMEBOY],
    output_dir="exports/"
)

for result in results:
    if result.success:
        print(f"{result.platform.name}: {result.tile_count} tiles, {result.colors_used} colors")
    else:
        print(f"{result.platform.name}: FAILED - {result.error}")
```

### Detailed Configuration

```python
from pipeline import CrossPlatformExporter, ExportConfig, Platform

exporter = CrossPlatformExporter()

# Configure export options
config = ExportConfig(
    platforms=[Platform.GENESIS, Platform.NES, Platform.GAMEBOY, Platform.MASTER_SYSTEM],
    output_dir="build/assets",
    create_subdirs=True,           # Create platform-specific folders
    transparent_color=(255, 0, 255), # Magenta = transparent
    dither=False,                   # No dithering for pixel art
    optimize_tiles=True,            # Deduplicate tiles
    generate_headers=True,          # Create C header files
    prefix="player"                 # Prefix for identifiers
)

results = exporter.export_sprite("gfx/player.png", config)
```

### Platform Specifications

```python
# Get platform hardware info
info = get_platform_info(Platform.GENESIS)
print(f"Colors: {info['total_colors']}")
print(f"Palette size: {info['palette_size']}")
print(f"Bits per pixel: {info['bits_per_pixel']}")
```

### Platform Constraints Reference

| Platform | Total Colors | Palette Size | BPP | Max Sprites |
|----------|--------------|--------------|-----|-------------|
| Genesis | 512 | 16 x 4 | 4 | 80 |
| NES | 54 (fixed) | 4 x 4 | 2 | 64 |
| Game Boy | 4 | 4 x 1 | 2 | 40 |
| Game Boy Color | 32768 | 4 x 8 | 2 | 40 |
| Master System | 64 | 16 x 2 | 4 | 64 |
| Game Gear | 4096 | 16 x 2 | 4 | 64 |

### Batch Export

```python
# Export all PNGs in a directory to all platforms
results = exporter.export_directory(
    "gfx/sprites/",
    config=config,
    pattern="*.png"
)

for filename, file_results in results.items():
    print(f"{filename}:")
    for r in file_results:
        status = "OK" if r.success else "FAIL"
        print(f"  {r.platform.name}: {status}")
```

### Output Structure

```
exports/
├── genesis/
│   ├── player.tiles    # 4bpp tile data
│   ├── player.pal      # CRAM palette (9-bit BGR)
│   └── player.h        # C header
├── nes/
│   ├── player.tiles    # 2bpp CHR data (planar)
│   ├── player.pal      # Palette indices
│   └── player.h
└── gameboy/
    ├── player.tiles    # 2bpp tile data (planar)
    ├── player.pal      # 2-bit grayscale
    └── player.h
```

---

## Complete Workflow Example

### Full Asset Pipeline

```python
from PIL import Image
from pipeline import (
    # Animation
    AnimationExtractor, AnimationPattern, export_sgdk_animations,
    # Export
    export_genesis_tilemap_optimized, export_vdp_ready_sprite,
    # Resources
    SGDKResourceGenerator,
    # Palette
    PaletteManager, create_genesis_game_palettes,
    # Performance
    PerformanceBudgetCalculator,
    # FSM
    create_character_fsm,
    # Debug
    CollisionVisualizer, CollisionBox
)

# 1. Setup palette manager
palette_mgr = create_genesis_game_palettes()

# 2. Extract animations from sprite sheet
extractor = AnimationExtractor()
patterns = [
    AnimationPattern("idle", 4, row=0),
    AnimationPattern("walk", 6, row=1),
    AnimationPattern("attack", 4, row=2, one_shot=True),
]
sequences = extractor.extract("player.png", patterns, 32, 32)

# 3. Export SGDK animation header
export_sgdk_animations(sequences, "inc/player_anim.h")

# 4. Generate VDP-ready data
sheet = Image.open("player.png")
tile_data, palette_data, _ = export_vdp_ready_sprite(sheet, palette_index=0)

# 5. Create SGDK resource file
res_gen = SGDKResourceGenerator()
res_gen.add_sprite("spr_player", "gfx/player.png", 32, 32)
res_gen.add_palette("pal_player", "gfx/player.png")
res_gen.write("res/player.res")

# 6. Generate animation FSM
fsm = create_character_fsm("player")
fsm.export_sgdk("src/player_fsm")

# 7. Validate performance budget
calc = PerformanceBudgetCalculator()
test_sprites = [
    {'x': 160, 'y': 100, 'width': 32, 'height': 32},  # Player
    *[{'x': 50 + i*40, 'y': 100, 'width': 16, 'height': 16} for i in range(5)]  # Bullets
]
report = calc.analyze_sprite_layout(test_sprites)
print(report.summary())

# 8. Generate debug collision image
viz = CollisionVisualizer()
hitbox = CollisionBox(8, 4, 16, 24, "hitbox")
hurtbox = CollisionBox(4, 0, 24, 32, "hurtbox")
debug_img = viz.render_overlay(sheet.crop((0, 0, 32, 32)), hitbox, hurtbox, scale=4)
debug_img.save("debug/player_collision.png")

print("Asset pipeline complete!")
```

### Output Files

```
project/
├── inc/
│   └── player_anim.h          # Animation frame definitions
├── src/
│   ├── player_fsm.h           # FSM state enum and functions
│   └── player_fsm.c           # FSM implementation
├── res/
│   └── player.res             # SGDK resource definitions
├── gfx/
│   └── player.png             # Source sprite sheet
└── debug/
    └── player_collision.png   # Collision debug image
```

---

## API Quick Reference

### Animation Module
```python
AnimationPattern(name, frame_count, row=0, one_shot=False)
AnimationFrame(index, duration, x, y, width, height)
AnimationSequence(name, frames, loop=True)
AnimationExtractor().extract(path, patterns, frame_width, frame_height)
export_sgdk_animations(sequences, output_path)
```

### Sheet Assembly
```python
SpriteSheetAssembler(algorithm, padding, power_of_two)
  .add_frame(image, name)
  .assemble() -> (Image, SheetLayout)
dissect_sheet(path, frame_width, frame_height) -> List[Image]
```

### Genesis Export
```python
export_genesis_tilemap_optimized(path, detect_mirrors) -> (tiles, tilemap, stats)
export_vdp_ready_sprite(image, palette_index) -> (tile_bytes, palette_bytes, sat_bytes)
export_sprite_attribute_table(attributes) -> bytes
export_cram_palette(colors) -> bytes
align_for_dma(data, alignment) -> bytes
```

### Palette
```python
PaletteManager(platform).register_slot(slot).validate_all()
PaletteConverter().convert(colors, target_format)
create_genesis_game_palettes() -> PaletteManager
```

### Performance
```python
PerformanceBudgetCalculator()
  .analyze_sprite_layout(sprites) -> PerformanceReport
  .estimate_dma_time(tile_bytes, palette_bytes) -> (scanlines, report)
  .generate_heatmap(sprites, width, height, scale) -> Image
  .suggest_optimizations(report) -> List[str]
```

### Collision Debug
```python
CollisionVisualizer()
  .render_overlay(sprite, hitbox, hurtbox, scale) -> Image
  .render_animation(frames, collisions, output, fps) -> bool
  .export_debug_sheet(sprites, sheet, output) -> bool
render_collision_debug(sprite, hitbox, hurtbox, scale) -> Image
```

### Animation FSM

```python
AnimationFSM(name, initial_state)
  .add_state(AnimationState)
  .validate() -> FSMValidationResult
  .export_sgdk(base_path)
  .export_json(path)
AnimationState(name, anim_index, loop, on_enter, on_exit)
  .add_transition(Transition)
Transition(target_state, condition, priority, callback)
create_character_fsm(name, include_combat) -> AnimationFSM
```

### Cross-Platform

```python
CrossPlatformExporter()
  .export_sprite(path, config) -> List[ExportResult]
  .export_directory(dir, config, pattern) -> Dict[str, List[ExportResult]]
  .get_platform_spec(platform) -> PlatformSpec
ExportConfig(platforms, output_dir, transparent_color, dither, optimize_tiles)
export_multi_platform(path, platforms, output_dir) -> List[ExportResult]
get_platform_info(platform) -> Dict[str, Any]
Platform.GENESIS | Platform.NES | Platform.GAMEBOY | Platform.MASTER_SYSTEM
```

---

## Troubleshooting

### Common Issues

**"PIL not available"**
```bash
pip install Pillow
```

**Scanline violations in performance report**
- Stagger sprite Y positions by 1-2 pixels
- Combine small sprites into larger composites
- Use sprite multiplexing (cycle visibility)

**DMA exceeds vblank**
- Split uploads across multiple frames
- Use compressed tile data
- Implement double-buffering

**FSM validation warnings**
- Ensure one-shot animations have `anim_complete` transitions
- Check all states are reachable from initial state
- Verify transition targets exist

---

## Version History

- **3.0.0**: Added Animation FSM, Collision Visualizer, Performance Calculator
- **2.1.0**: Added VDP-Ready Export, SGDK Resources, Palette Manager
- **2.0.0**: Added Genesis tile export with mirror detection
- **1.0.0**: Initial animation and sheet assembly
