# EPOCH - Technical Overview

> **Version**: 0.7.18 (Performance Optimized)  
> **Platform**: Sega Genesis / Mega Drive  
> **SDK**: SGDK (external dependency - not bundled)  
> **Language**: C (m68k-elf-gcc)  
> **Status**: PLAYABLE, OPTIMIZED, ART WIP  
> **Last Updated**: 2026-01-24

---

## Table of Contents

1. [Project Summary](#project-summary)
2. [Build Requirements](#build-requirements)
3. [Directory Structure](#directory-structure)
4. [Architecture Deep Dive](#architecture-deep-dive)
5. [Code Walkthrough](#code-walkthrough)
6. [Data Structures Reference](#data-structures-reference)
7. [Control Scheme](#control-scheme)
8. [Planned Systems (Days 2-4)](#planned-systems-days-2-4)
9. [Genesis Hardware Reference](#genesis-hardware-reference)
10. [AI Asset Pipeline Integration](#ai-asset-pipeline-integration)
11. [Xeno Crisis Lessons & Implementation](#xeno-crisis-lessons--implementation)
12. [Known Issues & Concerns](#known-issues--concerns)
13. [File Manifest](#file-manifest)

---

## Project Summary

**EPOCH** is a Genesis game combining:

- **Tower Defense**: 8-minute siege phases defending a Central Tower
- **Zelda-style Exploration**: Scrolling "hybrid room" zones (4 screens each)
- **Town/NPC System**: Safe zones with dialogue and upgrades

**High Concept**: "Zelda meets Tower Defense across Time"

**Current State**: Core gameplay loop functional. Enemies spawn in waves, player shoots automatically, pickups drop. Performance optimized with Three-Gate collision (90% reduction), frame staggering, and sprite caching. Art assets being finalized via manual pipeline.

---

## Build Requirements

### SGDK (Sega Genesis Development Kit)

**SGDK is NOT bundled in this repository.** It must be installed separately.

1. **Download**: <https://github.com/Stephane-D/SGDK/releases>
2. **Install**: Extract to a path (e.g., `C:\sgdk`)
3. **Set Environment Variable**: `GDK=C:\sgdk`

**SGDK provides**:

- `m68k-elf-gcc` - Cross-compiler for Motorola 68000
- `genesis.h` - Hardware abstraction library
- `rescomp` - Resource compiler for sprites, tilesets, etc.
- `makefile.gen` - Standard Genesis makefile

### Build Command

```batch
cd projects/epoch
build.bat
```

**Expected Output**: `out/rom.bin`

### Testing

Use a Genesis emulator:

- **BlastEm** (recommended): <https://www.retrodev.com/blastem/>
- **Gens/GS**: <https://segaretro.org/Gens/GS>

---

## Directory Structure

```
projects/epoch/
│
├── build.bat                  # Build script (calls SGDK makefile)
├── PROJECT_STATE.md           # Current project status (updated frequently)
├── TECHNICAL_OVERVIEW.md      # This document
│
├── inc/                       # Header files
│   ├── constants.h            # Hardware limits, game constants, fixed-point macros
│   └── ...                    # Additional headers
│
├── src/
│   ├── main.c                 # Game loop, player, camera, input (34KB)
│   │
│   ├── engine/                # ✅ Core engine systems
│   │   ├── animation.c/h      # Frame-based animation system
│   │   ├── entity.c/h         # Entity pool, collision masks
│   │   ├── spatial.c/h        # Spatial hash grid, Three-Gate collision
│   │   ├── math_fast.c/h      # Integer math, LUT operations
│   │   ├── debug_sram.c/h     # SRAM-based profiler output
│   │   ├── raster.c/h         # Raster effects (available)
│   │   ├── sinetable.h        # Pre-calculated sine LUT
│   │   └── system.c/h         # VBlank, frame timing
│   │
│   ├── game/                  # ✅ Gameplay systems
│   │   ├── enemies.c/h        # Enemy AI, spawning, sprite management
│   │   ├── projectiles.c/h    # Projectile physics, collision
│   │   ├── fenrir.c/h         # Dog companion AI
│   │   ├── director.c/h       # Wave spawning logic
│   │   ├── pickups.c          # XP gems, health drops
│   │   ├── enemy_data.c/h     # Enemy type definitions
│   │   └── audio.c            # Sound effect triggers
│   │
│   └── ui/                    # 🔨 UI systems (stub)
│       └── build_mode.c       # Tower placement (not implemented)
│
├── res/
│   ├── resources.res          # SGDK resource definitions
│   ├── sprites/               # Sprite sheets
│   ├── tilesets/              # Background tiles
│   └── sfx/                   # Sound effects
│
└── out/                       # Build output (rom.bin)
```

---

## Architecture Deep Dive

### Game State Machine

```
                    ┌─────────────┐
                    │  STATE_TITLE │
                    └──────┬──────┘
                           │ Start
                           ▼
┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│ STATE_PAUSED │◄──►│ STATE_SIEGE │───►│STATE_EXPEDITION│
└──────────────┘    └──────┬──────┘    └───────┬──────┘
                           │                    │
                           │                    ▼
                           │              ┌───────────┐
                           │              │STATE_TOWN │
                           │              └───────────┘
                           ▼
                    ┌─────────────┐
                    │STATE_GAMEOVER│
                    └─────────────┘
```

**State Transitions**:

- TITLE → SIEGE: Press Start
- SIEGE → EXPEDITION: Exit gate (when siege timer = 0)
- SIEGE ↔ PAUSED: Start button (also opens build mode)
- EXPEDITION → TOWN: Enter town zone
- Any → GAMEOVER: Player HP = 0

### Entity System Design

**Philosophy**: Cache-friendly, fixed-size structures for fast iteration.

```
┌─────────────────────────────────────────────────────────────┐
│                    ENTITY POOL (64 slots)                   │
├─────┬─────┬─────────────────┬─────────────────┬────────────┤
│  0  │  1  │     2 - 25      │    26 - 57      │  58 - 63   │
│Player│Fenrir│   Enemies (24)  │ Projectiles (32)│Towers/NPCs │
└─────┴─────┴─────────────────┴─────────────────┴────────────┘
```

**Entity Structure (16 bytes)**:

```
Offset  Size  Field      Description
──────  ────  ─────      ───────────
0       1     flags      ENT_ACTIVE, ENT_VISIBLE, ENT_SOLID, etc.
1       1     type       ENT_TYPE_PLAYER, ENT_TYPE_ENEMY_BASIC, etc.
2       2     x          X position (8.8 fixed point)
4       2     y          Y position (8.8 fixed point)
6       2     vx         X velocity (8.8 fixed point)
8       2     vy         Y velocity (8.8 fixed point)
10      1     hp         Health points
11      1     timer      Animation/state timer
12      1     spriteId   Sprite definition index
13      1     frame      Current animation frame
14      2     data       Type-specific data (enemy target, projectile owner, etc.)
```

**Why 16 bytes?**: Power of 2 allows fast array indexing with bit shifts instead of multiplication.

### Fixed-Point Math

All positions and velocities use **8.8 fixed-point** format:

- Upper 8 bits: Integer part (pixel position)
- Lower 8 bits: Fractional part (sub-pixel precision)

```c
#define FP_SHIFT  8
#define FP_ONE    256            // 1.0 in fixed point
#define FP(x)     ((x) << 8)     // Convert int to fixed: FP(100) = 25600
#define FP_INT(x) ((x) >> 8)     // Convert fixed to int: FP_INT(25600) = 100
```

**Example**: Player speed of 1.5 pixels/frame = `0x0180` (384 in decimal, which is 1.5 × 256)

### Memory Layout

**RAM Usage** (estimated):

```
Entity pool:        64 × 16 = 1,024 bytes
PlayerData:                     20 bytes
FenrirData:                      4 bytes
Game struct:                    16 bytes
InputState:                      8 bytes
Stack:                       ~2,048 bytes
SGDK overhead:            ~4,000 bytes
────────────────────────────────────────
Total:                    ~7,120 bytes (of 64KB)
```

**VRAM Usage** (planned):

```
Player sprites:     32 tiles × 32 bytes = 1,024 bytes
Tileset:           256 tiles × 32 bytes = 8,192 bytes
Plane A map:        80 × 56 × 2 bytes  = 8,960 bytes
Plane B map:        64 × 32 × 2 bytes  = 4,096 bytes
Font/UI:            64 tiles × 32 bytes = 2,048 bytes
────────────────────────────────────────────────────
Total:                               ~24,320 bytes (of 64KB)
```

---

## Code Walkthrough

### `inc/constants.h`

**Purpose**: Central location for all magic numbers and hardware limits.

**Key Sections**:

- Screen dimensions (320×224)
- Zone/map system constants (hybrid room sizes)
- Entity slot ranges
- Sprite sizes
- Gameplay values (speeds, durations)
- Fixed-point macros
- Combat values (heat, invuln frames)

**Design Decision**: All gameplay-tunable values are here for easy adjustment.

### `inc/game.h`

**Purpose**: Game state management and input handling.

**Key Types**:

```c
GameState       // Enum: TITLE, SIEGE, EXPEDITION, TOWN, PAUSED, LEVELUP, GAMEOVER
ZoneId          // Enum: ZONE_TOWER, ZONE_WILDS_1, ZONE_TOWN_1
Direction       // Enum: 8 directions (RIGHT, DOWN_RIGHT, DOWN, etc.)
WeaponType      // Enum: EMITTER, SPREADER, HELIX
Game            // Struct: state, timer, zone, player stats
InputState      // Struct: current, previous, pressed, released buttons
```

**Input Pattern**:

```c
input.current  = JOY_readJoypad(JOY_1);
input.pressed  = input.current & ~input.previous;  // Just pressed
input.released = ~input.current & input.previous;  // Just released
```

### `inc/entity.h`

**Purpose**: Entity system with type definitions and extended data structures.

**Flag System** (bitfield):

```c
ENT_ACTIVE   0x01  // In use
ENT_VISIBLE  0x02  // Should render
ENT_SOLID    0x04  // Has collision
ENT_FRIENDLY 0x08  // Allied with player
ENT_ENEMY    0x10  // Hostile
ENT_PICKUP   0x20  // Collectible
ENT_INVULN   0x40  // Invincible
ENT_FIRING   0x80  // Currently shooting
```

**Type System** (category + variant):

```c
0x1X = Player/Companion (0x10=Player, 0x11=Fenrir)
0x2X = Enemies (0x20=Basic, 0x21=Fast, 0x22=Tank, 0x23=Ranged)
0x3X = Projectiles (0x30=Player, 0x31=Enemy, 0x32=Tower)
0x4X = Towers (0x40=Basic, 0x41=Flame, 0x42=Slow)
0x5X = NPCs (0x50=Generic, 0x51=Merchant, 0x52=Smith)
0x6X = Pickups (0x60=XP, 0x61=Health, 0x62=Weapon)
```

**Extended Data Structures**:

- `PlayerData`: weapon, facing, HP, invuln, dash, strafe lock, fire rate
- `FenrirData`: mode (follow/guard/attack), target, follow distance

### `src/main.c`

**Purpose**: Everything for Day 1 - will be refactored later.

**Structure**:

1. **Globals**: Game, InputState, entities[], playerData, fenrirData, playerSprite
2. **Input Functions**: input_update(), input_isHeld(), input_justPressed()
3. **Game Init**: game_init() - clear state, init pools, set defaults
4. **Entity Pool**: entity_initPool(), entity_alloc(), entity_free()
5. **Player Logic**: player_spawn(), player_update()
6. **State Updates**: update_siege(), update_expedition(), update_town()
7. **Main Loop**: game_update() state machine, main() entry point

**Player Update Flow**:

```
1. Read D-pad → calculate moveX, moveY
2. Normalize diagonal movement (×0.707)
3. Update facing direction (if not strafe-locked)
4. Check strafe lock (A held)
5. Check dash (C pressed) → boost speed, set invuln
6. Apply velocity to position
7. Clamp to screen bounds
8. Decrement timers (invuln, dash)
9. Update sprite position and flip
10. Handle invuln blink effect
```

### `res/resources.res`

**Purpose**: SGDK resource compiler definitions.

**Current Content**:

```
SPRITE spr_player "sprites/player.png" 4 4 NONE 0
```

**Format**: `SPRITE name "path" width_tiles height_tiles compression timing`

- 4×4 tiles = 32×32 pixels
- NONE = no compression
- 0 = no animation timing (single frame)

---

## Data Structures Reference

### Complete Entity Struct

```c
typedef struct {
    u8  flags;      // Bit 0: active, 1: visible, 2: solid, 3: friendly,
                    //     4: enemy, 5: pickup, 6: invuln, 7: firing
    u8  type;       // High nibble: category, Low nibble: variant
    s16 x;          // 8.8 fixed point X position
    s16 y;          // 8.8 fixed point Y position
    s16 vx;         // 8.8 fixed point X velocity
    s16 vy;         // 8.8 fixed point Y velocity
    u8  hp;         // Health points (0-255)
    u8  timer;      // Multi-purpose timer
    u8  spriteId;   // Index into sprite definitions
    u8  frame;      // Animation frame (0-255)
    u16 data;       // Type-specific:
                    //   Enemy: target slot (8) + state (8)
                    //   Projectile: owner slot (8) + damage (8)
                    //   Tower: cooldown (16)
                    //   NPC: dialogue ID (16)
} Entity;           // Total: 16 bytes
```

### Complete PlayerData Struct

```c
typedef struct {
    u8  weaponType;     // 0=Emitter, 1=Spreader, 2=Helix
    u8  weaponLevel;    // 0-3 upgrade level
    u8  volatileWeapon; // Alt-fire weapon ID
    u8  facing;         // 0-7 direction index

    u16 maxHP;          // Maximum health
    u16 currentHP;      // Current health

    u8  invulnTimer;    // Frames of invincibility remaining
    u8  dashTimer;      // Frames of dash remaining
    u8  strafeLocked;   // TRUE if A button held

    u8  keysCollected;  // For expedition puzzles
    u8  techUnlocked;   // Bitfield of abilities
    u8  towersPlaced;   // Current tower count

    u16 fireRate;       // Frames between shots
    u16 fireCooldown;   // Frames until next shot
} PlayerData;           // Total: 20 bytes
```

### Complete Game Struct

```c
typedef struct {
    GameState state;        // Current state
    GameState prevState;    // For pause/unpause

    u16 siegeTimer;         // Frames remaining (8 min = 28800)
    u8  waveNumber;         // Current enemy wave

    u8  currentZone;        // Zone ID

    u16 playerLevel;        // Player level
    u32 playerXP;           // Experience points
    u32 score;              // Score

    u8  heat;               // Alt-fire resource (0-100)
    u8  gateOpen;           // Can exit siege area
    u8  paused;             // Pause flag
} Game;
```

---

## Control Scheme

### 3-Button Genesis Layout

| Button | Combat (Siege/Expedition) | Town | Build Mode |
|--------|---------------------------|------|------------|
| **D-Pad** | Move + Aim | Move | Move cursor |
| **A (Hold)** | Strafe Lock | - | - |
| **B** | Alt-Fire | - | Place/Remove |
| **C** | Dash (i-frames) | Interact | Confirm |
| **Start** | Pause / Enter Build | Pause | Exit Build |

### Core Mechanic: Continuous Fire

- **No shoot button** - weapon fires automatically in facing direction
- **Strafe Lock (A)** - essential skill: lock facing, move freely
- **Weapon type determines kill zone shape**:
  - Emitter: Narrow beam (precision)
  - Spreader: 45° cone (crowd control)
  - Helix: Sine wave (area denial)

---

## Planned Systems (Days 2-4)

### Day 2: Hybrid Room Scrolling

**Zone Structure**:

- Each zone = 2×2 screens = 640×448 pixels = 80×56 tiles
- Camera follows player with smooth scroll
- Clamps to zone bounds
- Zone transitions at edges (fade/scroll-lock)

**Key Files to Create**:

- `inc/map.h` - Zone struct, map constants
- `src/world/map.c` - Zone loading, scrolling
- `src/world/collision.c` - Tile collision
- `src/world/zones.c` - Zone definitions

### Day 3: Mode Transitions

**Features**:

- Siege timer HUD
- Gate entity (closed during siege, opens at timer=0)
- Zone transition (Tower → Wilds)
- Fenrir companion (follows player)

**Key Files to Create**:

- `src/states/state_siege.c`
- `src/states/state_expedition.c`
- `src/ui/hud.c`
- `src/entity/fenrir.c`

### Day 4: NPCs & Dialogue

**Features**:

- NPC entity type
- Proximity trigger
- Text box rendering
- Dialogue sequences

**Key Files to Create**:

- `src/entity/npcs.c`
- `src/ui/dialogue.c`

---

## Genesis Hardware Reference

### CPU & Memory

| Resource | Specification |
|----------|---------------|
| Main CPU | Motorola 68000 @ 7.67 MHz |
| Sound CPU | Zilog Z80 @ 3.58 MHz |
| Main RAM | 64 KB |
| VRAM | 64 KB |
| Color RAM | 128 bytes (64 colors) |

### Video (VDP)

| Feature | Limit |
|---------|-------|
| Resolution | 320×224 (H40) or 256×224 (H32) |
| Tile Size | 8×8 pixels |
| Bits per Pixel | 4 (16 colors per palette) |
| Palettes | 4 (64 total colors) |
| Max Tiles in VRAM | 2048 |
| Background Planes | 2 (A and B) |
| Plane Sizes | 32×32, 64×32, 32×64, 64×64 tiles |

### Sprites

| Feature | Limit |
|---------|-------|
| Max Sprites | 80 total |
| Per Scanline | 20 sprites OR 320 pixels |
| Sprite Sizes | 8, 16, 24, 32 (width and height independently) |
| Sprite Tiles | 1 to 16 (4×4 max) |
| H/V Flip | Hardware supported |
| Priority | Per-sprite, over/under plane |

### Color Format

Genesis uses 9-bit color (3 bits per channel):

```
Format: 0000BBB0GGG0RRR0
        ────┬── ───┬── ───┬──
            │      │      └── Red (0-7, even positions)
            │      └── Green (0-7, even positions)
            └── Blue (0-7, even positions)
```

**Note**: Only even values (0,2,4,6,8,A,C,E) are valid per channel.

---

## AI Asset Pipeline Integration

The project includes Python tools for AI-assisted sprite generation at `tools/`:

### Relevant Files

| File | Purpose |
|------|---------|
| `tools/configs/genesis_config.py` | Genesis hardware specs, palette helpers |
| `tools/unified_pipeline.py` | Main sprite processor (supports Genesis) |
| `tools/asset_generators/pixellab_client.py` | PixelLab API ($0.01/image) |
| `tools/asset_generators/base_generator.py` | Pollinations API (free) |

### Usage

```bash
# Generate sprite with platform constraints
python tools/unified_pipeline.py input.png -o output/ --platform genesis

# Generate with PixelLab (requires API key)
python tools/asset_generators/pixellab_client.py --generate "robot guardian" --size 32x32
```

### Genesis-Specific Processing

From `tools/configs/genesis_config.py`:

- 4bpp tile generation (32 bytes/tile)
- 9-bit RGB palette conversion
- Tile deduplication with H/V flip detection
- VDP tilemap entry generation

---

## Xeno Crisis Lessons & Implementation

Lessons learned from analyzing Xeno Crisis (2019) by Bitmap Bureau, a best-in-class Genesis arena shooter that manages high sprite counts without severe slowdown.

### 1. Sprite Budget Strategy

**Xeno Crisis Approach**: Strict size limits on enemies (16×16, 24×24, 32×32 max for mobs).

**EPOCH Implementation**:

- **Tower**: 64×64 (8×8 tiles) - acceptable for static structure
- **Enemies**: Target 24×24 or 32×32 for mobs
- **Projectiles**: 8×8 single-tile sprites ✅ (already implemented)
- **Player**: 32×32 ✅ (appropriate for hero character)

### 2. Sprite Flickering & Depth Cycling

**Xeno Crisis Approach**: Rotates sprite rendering order every frame to distribute flickering when exceeding 20 sprites/scanline limit.

**EPOCH Implementation** ✅:

```c
// In game.h
typedef struct {
    // ... other fields
    u8 flickerOffset;  // For sprite depth cycling
} Game;

// In main.c game loop
game.flickerOffset++;

// In enemies_update()
SPR_setDepth(enemySprites[i], SPR_MIN_DEPTH + ((i + game.flickerOffset) & 0x1F));
```

**Result**: Sprites cycle through depth buffer. When sprite limit is exceeded, the flickering sprite changes each frame instead of one sprite permanently disappearing.

### 3. Palette Management

**Xeno Crisis Approach**:

- PAL0: Backgrounds (darker, low contrast)
- PAL1: Player & UI (high contrast "hero" colors)
- PAL2: Enemies (shared palette for ALL basic enemies)
- PAL3: FX / Bullets / Elites

**EPOCH Current Allocation**:

- PAL0: Background ✅
- PAL1: Player ✅
- PAL2: Enemy ✅
- PAL3: Tower ✅

**Consideration**: All 4 palettes used. Future UI/FX may require palette sharing between tower and enemies (both use similar grey/red tones).

### 4. Input Handling: Strafe Lock

**Xeno Crisis Approach**: A button locks firing direction while allowing free movement (essential for 3-button Genesis pads).

**EPOCH Implementation** ✅:

```c
// In player_update()
if (input_isHeld(BUTTON_A)) {
    playerData.strafeLocked = TRUE;
    // Facing direction locked, movement independent
} else {
    playerData.strafeLocked = FALSE;
    // Update facing based on movement direction
}
```

**Future Enhancement**: Add 6-button pad detection for twin-stick style controls (XYBZ for directional shooting).

### 5. Asset Transparency Handling

**Lesson Learned**: AI-generated sprites may use near-magenta colors (e.g., RGB 254,0,254) instead of exact #FF00FF.

**EPOCH Solution** ✅:

```python
# In tools/fix_genesis_assets.py
# Detect near-magenta colors (high R, low G, high B)
if r > 200 and g < 50 and b > 200:
    pixels[x, y] = (0, 0, 0, 0)  # Force transparent
```

**Result**: Tower sprite transparency now works correctly with AI-generated assets.

### 6. Testing & Automation

**EPOCH Innovation**: GDB socket-based automation framework.

**Implementation**:

- `tools/blastem_test.py`: Socket connection to BlastEm GDB server
- `tools/emulators/blastem/`: Local emulator copy for reproducibility
- PIL ImageGrab integration for screenshot capture
- Automated ROM testing with visual verification

**Usage**:

```bash
python tools/blastem_test.py
# Launches BlastEm, runs game, captures screenshots, exits cleanly
```

---

## Known Issues & Concerns

### Resolved Issues ✅

1. **Sprite Palette Assignments**: Fixed - Player→PAL1, Enemy→PAL2, Tower→PAL3
2. **Tower Transparency**: Fixed - Near-magenta chroma key detection implemented
3. **Background Tiling**: Fixed - Corrected stride from 16 to 32 tiles
4. **Flicker Management**: Implemented - Sprite depth cycling active
5. **Collision Performance**: Implemented - Three-Gate filter (90% CPU reduction)
6. **Sprite API Bottleneck**: Fixed - Sprite caching for all entities
7. **Enemy Tile Collision**: Fixed - Time-sliced every 2 frames

### Current Limitations

1. **Art Assets**: Hero sprite direction mapping incorrect, sprites WIP
2. **Palette Budget**: All 4 palettes allocated. UI may require sharing.
3. **Weapon Upgrades**: XP collected but no upgrade system yet
4. **Boss Encounters**: Not yet designed

### Architecture Notes

1. **Engine/Game Split**: Code properly modularized into engine/ and game/
2. **SGDK 2.x API**: Tested and working
3. **Object Pool Pattern**: All entities use pre-allocated pools, no runtime alloc

---

## File Manifest

| File | Lines | Bytes | Description |
|------|-------|-------|-------------|
| `build.bat` | 22 | 598 | SGDK build script |
| `inc/constants.h` | 89 | 2,847 | All game constants |
| `inc/game.h` | 97 | 2,654 | State machine, input |
| `inc/entity.h` | 132 | 4,128 | Entity system |
| `src/main.c` | 332 | 10,245 | Game loop, player |
| `res/resources.res` | 25 | 683 | Resource definitions |
| `res/sprites/player.png` | - | ~500 | 32×32 placeholder |
| **Total** | **697** | **~21KB** | |

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-24 | 0.7.18 | Art pipeline separation, PROJECT_STATE.md created, sprite revert |
| 2026-01-22 | 0.7.17 | Three-Gate collision, frame staggering, 90% collision CPU reduction |
| 2026-01-21 | 0.7.16 | Sprite caching for all entities |
| 2026-01-20 | 0.7.15 | Time-sliced tile collision for enemies |
| 2026-01-19 | 0.7.0 | Engine/game modularization, director system |
| 2026-01-17 | 0.2.0 | Graphics pipeline stabilized: palette fixes, tower transparency, background tiling, flicker manager, GDB automation |
| 2026-01-16 | 0.1.0 | Initial Day 1 implementation |

---

*Document updated with Xeno Crisis lessons and current implementation status.*
