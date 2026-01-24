# NEON SURVIVORS - Project Architecture

> ⚠️ **DEPRECATION NOTICE**: This document is for the **NES version** which is
> on hold. For the active **Sega Genesis/EPOCH** project, see:
>
> - [MASTER_IMPLEMENTATION_PLAN.md](../MASTER_IMPLEMENTATION_PLAN.md) - Current roadmap
> - [projects/epoch/](../projects/epoch/) - Genesis game source
> - Engine architecture: `brain/*/modern_architecture.md` (session artifacts)

> **Last Updated**: 2026-01-10 (NES version paused)
> **Version**: 0.2.0-alpha
> **Status**: ON HOLD - Genesis version is primary focus

This document provides a high-level overview of the **NES version** architecture. Keep this for reference if NES development resumes.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [ARDK - Hardware Abstraction Layer](#ardk---hardware-abstraction-layer)
3. [Directory Structure](#directory-structure)
4. [Build Pipeline](#build-pipeline)
5. [Asset Pipeline](#asset-pipeline)
6. [Game Architecture](#game-architecture)
7. [Module System](#module-system)
8. [Memory Map](#memory-map)
9. [Data Flow Diagrams](#data-flow-diagrams)
10. [Hygiene Checkpoints](#hygiene-checkpoints)

---

## Project Overview

**NEON SURVIVORS** is a Vampire Survivors-style action game for the NES, featuring:

- Synthwave/cyberpunk aesthetic (magenta, cyan, white palette)
- Auto-attacking weapons with upgrades
- Wave-based enemy spawning
- XP/leveling system
- MMC3 mapper for bank switching

### Tech Stack

| Component | Technology |
|-----------|------------|
| Assembler | ca65 (cc65 suite) |
| Linker | ld65 |
| Mapper | MMC3 (iNES mapper 4) |
| Graphics | Custom Python pipeline |
| AI Integration | Groq, Gemini, OpenAI (sprite labeling) |

---

## ARDK - Hardware Abstraction Layer

The **Agentic Retro Development Kit (ARDK)** provides a platform-agnostic foundation for cross-platform retro game development. The HAL allows game logic to be written once and compiled for multiple platforms.

### ARDK Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Game Logic (Platform-Agnostic)                │
│              Movement, AI, State Machines, Collision             │
├─────────────────────────────────────────────────────────────────┤
│                  Hardware Abstraction Layer (HAL)                │
│       hal_sprite_set(), hal_input_read(), hal_sfx_play()        │
├───────────────┬───────────────┬───────────────┬─────────────────┤
│      NES      │    Genesis    │     SNES      │      GBA        │
│     6502      │    68000      │    65816      │     ARM7        │
│ hal_nes.c     │ hal_genesis.c │  hal_snes.c   │  hal_gba.c      │
└───────────────┴───────────────┴───────────────┴─────────────────┘
```

### Core HAL Files

| File | Purpose |
|------|---------|
| `src/hal/types.h` | Platform-agnostic types (u8, i16, fixed8_8) |
| `src/hal/hal.h` | HAL interface (function signatures) |
| `src/hal/entity.h` | 16-byte Entity structure for all game objects |
| `src/hal/nes/hal_config.h` | NES-specific constants |
| `src/hal/nes/hal_nes.c` | NES HAL implementation |
| `src/hal/genesis/hal_config.h` | Genesis-specific constants |
| `src/hal/genesis/hal_genesis.c` | Genesis HAL implementation |

### Locked Design Decisions

These are **permanent** and should never change:

| Decision | Value | Rationale |
|----------|-------|-----------|
| Fixed-point format | 8.8 | High byte = pixel, low byte = subpixel (1/256) |
| Entity size | 16 bytes | Power of 2 for fast indexing (id << 4) |
| Coordinate origin | Top-left | Matches all target hardware |
| Y direction | Down = positive | Matches all target hardware |
| Asset IDs | 8-bit | 0x00-0x0F system, 0x10-0x7F game, 0x80+ dynamic |

### HAL Capabilities by Platform

| Capability | NES | Genesis | SNES | GBA |
|------------|-----|---------|------|-----|
| Sprite flip | Yes | Yes | Yes | Yes |
| Sprite zoom | No | No | Yes | Yes |
| BG scroll | Yes | Yes | Yes | Yes |
| Hardware multiply | No | Yes | Yes | Yes |
| Stereo audio | No | Yes | Yes | Yes |
| Max sprites | 64 | 80 | 128 | 128 |
| Max per line | 8 | 20 | 32 | 128 |

### Entity System

All game objects (player, enemies, projectiles, pickups) use the same 16-byte structure:

```c
typedef struct Entity {
    u8          flags;      // ENT_FLAG_ACTIVE, VISIBLE, SOLID, etc.
    u8          type;       // ENT_TYPE_PLAYER, ENEMY_BASIC, etc.
    fixed8_8    x;          // Position (8.8 fixed-point)
    fixed8_8    y;
    fixed8_8    vx;         // Velocity
    fixed8_8    vy;
    u8          hp;         // Health
    u8          timer;      // General purpose countdown
    sprite_id_t sprite;     // Sprite asset ID
    u8          frame;      // Animation frame
    u16         data;       // Type-specific (damage, owner, etc.)
} Entity;  // 16 bytes exactly
```

---

## Directory Structure

```
SurvivorNES/
├── src/                        # Source code
│   ├── hal/                    # Hardware Abstraction Layer (ARDK)
│   │   ├── types.h             # Platform-agnostic types (u8, fixed8_8, etc.)
│   │   ├── hal.h               # HAL interface (locked function signatures)
│   │   ├── entity.h            # 16-byte entity structure
│   │   ├── nes/                # NES platform implementation
│   │   │   ├── hal_config.h    # NES constants (screen, sprites, timing)
│   │   │   └── hal_nes.c       # NES HAL implementation
│   │   └── genesis/            # Genesis platform implementation
│   │       ├── hal_config.h    # Genesis constants
│   │       └── hal_genesis.c   # Genesis HAL implementation
│   │
│   ├── engine/                 # Reusable engine code
│   │   ├── engine.inc          # Main engine include (imports all modules)
│   │   ├── init.asm            # NES hardware initialization
│   │   ├── nmi.asm             # Vertical blank interrupt handler
│   │   ├── graphics.asm        # CHR bank includes
│   │   ├── input.asm           # Controller reading
│   │   └── modules/            # Optional engine modules
│   │       └── action/         # Combat module (projectiles, spawners, powerups)
│   │           ├── action.inc  # Module exports
│   │           ├── projectile.asm
│   │           ├── spawner.asm
│   │           └── powerup.asm
│   │
│   └── game/                   # Game-specific code
│       ├── src/
│       │   └── game_main.asm   # Main game loop, player logic, rendering
│       └── assets/
│           ├── sprites.chr     # Combined sprite graphics (8KB)
│           └── sprite_tiles.inc # Tile index constants
│
├── tools/                      # Build and asset tools
│   ├── unified_pipeline.py     # Master sprite processing (v5.2, 13 platforms)
│   ├── png2chr.py              # PNG to CHR converter
│   └── make_spritesheet.py     # Sprite sheet combiner
│
├── gfx/                        # Graphics assets
│   ├── ai_output/              # AI-generated sprite sheets (input)
│   └── processed/              # Pipeline output (indexed PNGs, CHR files)
│
├── build/                      # Build output
│   └── neon_survivors.nes      # Final ROM
│
├── docs/                       # Documentation
│   ├── PROJECT_ARCHITECTURE.md # This file
│   └── PIPELINE_REFERENCE.md   # Sprite pipeline details
│
├── cfg/
│   └── mmc3.cfg                # Linker configuration (memory layout)
│
└── compile.bat                 # Build script
```

---

## Build Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                        BUILD FLOW                                │
└─────────────────────────────────────────────────────────────────┘

  Source Files (.asm)          Asset Files (.chr)
         │                            │
         ▼                            │
    ┌─────────┐                       │
    │  ca65   │  Assembler            │
    │         │  Creates .o files     │
    └────┬────┘                       │
         │                            │
         ▼                            ▼
    ┌─────────────────────────────────────┐
    │              ld65                    │
    │   Linker (uses cfg/mmc3.cfg)        │
    │   Combines code + graphics          │
    └─────────────────┬───────────────────┘
                      │
                      ▼
              ┌───────────────┐
              │ neon_survivors│
              │     .nes      │
              └───────────────┘
```

### Build Commands

```bash
# Full build (Windows)
compile.bat

# Manual build
ca65 -o build/init.o src/engine/init.asm -g
ca65 -o build/game_main.o src/game/src/game_main.asm -g
# ... (other .asm files)
ld65 -o build/neon_survivors.nes -C cfg/mmc3.cfg build/*.o
```

### Build Artifacts

| File | Size | Description |
|------|------|-------------|
| `build/*.o` | ~1-4KB each | Object files |
| `build/neon_survivors.nes` | ~128KB | Final ROM (MMC3, 128KB PRG + 128KB CHR) |

---

## Asset Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    SPRITE PIPELINE (v5.2)                        │
└─────────────────────────────────────────────────────────────────┘

  AI-Generated PNG                    Manual PNG
  (gfx/ai_output/)                   (any source)
         │                                │
         └────────────┬───────────────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │   unified_pipeline.py  │
         │                        │
         │  1. Load PNG           │
         │  2. Detect sprites     │
         │  3. Filter text labels │
         │  4. AI labeling (opt)  │
         │  5. Quantize to 4 colors│
         │  6. Generate CHR tiles │
         └───────────┬────────────┘
                     │
                     ▼
         ┌────────────────────────┐
         │  gfx/processed/        │
         │  ├── metadata.json     │
         │  ├── sprite_XX.chr     │
         │  ├── sprite_XX.png     │
         │  └── sprites.chr       │ ◄── Combined 8KB bank
         └───────────┬────────────┘
                     │
                     ▼
         ┌────────────────────────┐
         │  src/game/assets/      │
         │  └── sprites.chr       │ ◄── Copy to game assets
         └────────────────────────┘
```

### Pipeline Usage

```bash
# Single file (NES)
python tools/unified_pipeline.py player.png -o gfx/processed/player/

# Batch process
python tools/unified_pipeline.py --batch gfx/ai_output/ -o gfx/processed/

# Other platforms
python tools/unified_pipeline.py sprite.png -o out/ --platform gb
python tools/unified_pipeline.py sprite.png -o out/ --platform genesis
python tools/unified_pipeline.py sprite.png -o out/ --platform c64
```

### Supported Platforms (13)

| Platform | Colors | Format | Extension |
|----------|--------|--------|-----------|
| NES | 4 | 2bpp CHR | .chr |
| Game Boy | 4 | 2bpp | .2bpp |
| Game Boy Color | 4/palette | 2bpp | .2bpp |
| SNES | 16 | 4bpp interleaved | .bin |
| Genesis | 16 | 4bpp packed | .bin |
| Master System | 16 | 4bpp planar | .sms |
| PC Engine | 16 | 4bpp | .bin |
| Amiga OCS | 32 | 5 bitplanes | .raw |
| Amiga AGA | 256 | 8 bitplanes | .raw |
| C64 | 4 | 2bpp sprite | .spr |
| CGA | 4 | 2bpp | .cga |
| Atari 2600 | 2 | 1bpp | .a26 |

---

## Game Architecture

### State Machine

```
┌─────────────────────────────────────────────────────────────────┐
│                      GAME STATES                                 │
└─────────────────────────────────────────────────────────────────┘

                    ┌──────────┐
         ┌─────────│  TITLE   │◄────────────┐
         │         │  (0)     │             │
         │         └────┬─────┘             │
         │              │ START             │
         │              ▼                   │
         │         ┌──────────┐             │
         │    ┌───►│ PLAYING  │────┐        │
         │    │    │  (1)     │    │        │
         │    │    └────┬─────┘    │        │
         │    │         │          │        │
         │    │   LEVEL │    PAUSE │        │
         │    │    UP   │          │        │
         │    │         ▼          ▼        │
         │    │    ┌──────────┐ ┌──────────┐│
         │    └────│ LEVELUP  │ │ PAUSED   ││
         │         │  (2)     │ │  (3)     ││
         │         └──────────┘ └────┬─────┘│
         │                           │      │
         │                     GAME  │      │
         │                     OVER  │      │
         │                           │      │
         └───────────────────────────┴──────┘
```

### Main Loop (game_main.asm)

```
Game_Update:
    │
    ├── [TITLE]    → update_title()     → Wait for START
    │
    ├── [PLAYING]  → update_player()    → Move player (D-pad)
    │              → update_enemy()     → Enemy AI + auto-fire
    │              → update_weapons()   → Player auto-attack
    │              → projectile_update_all()
    │              → update_sprites()   → OAM rendering
    │
    ├── [LEVELUP]  → update_levelup()   → Weapon selection
    │
    └── [PAUSED]   → update_paused()    → Wait for unpause
```

### Entity Rendering Order (OAM)

```
OAM $0200-$02FF (64 sprites max)

Offset  │ Entity          │ Tiles      │ Size
────────┼─────────────────┼────────────┼──────────
$00-$3F │ Player          │ $00-$0F    │ 32x32 (16 tiles)
$40-$7F │ Enemy           │ $10-$1F    │ 32x32 (16 tiles)
$80+    │ Projectiles     │ $20-$23    │ 8x8 (1 tile each)
        │ Powerups        │ $24+       │ 8x8
```

---

## Module System

The engine uses conditional compilation for optional features:

### Module Flags (defined in engine.inc or build)

```asm
MODULE_ACTION_ENABLED = 1    ; Projectiles, spawners, powerups
USE_SPAWNER = 1              ; Enemy wave spawning
USE_POWERUPS = 1             ; XP gems, health, coins
```

### Action Module (src/engine/modules/action/)

**projectile.asm** - Bullet/laser system

```
Functions:
  projectile_init         - Clear all projectiles
  projectile_spawn        - Create new projectile (uses ZP params)
  projectile_update_all   - Move all active projectiles
  projectile_render_all   - Draw to OAM
  projectile_check_collision - Hit detection
  projectile_deactivate   - Remove projectile

Zero Page Parameters ($40-$47):
  projectile_spawn_x      - X position
  projectile_spawn_y      - Y position
  projectile_spawn_vx     - X velocity (signed)
  projectile_spawn_vy     - Y velocity (signed)
  projectile_spawn_type   - PROJ_TYPE_LASER/MISSILE/BEAM
  projectile_spawn_flags  - PROJ_FLAG_FRIENDLY/ENEMY
```

**spawner.asm** - Wave-based enemy spawning

```
Functions:
  spawner_init            - Reset spawner state
  spawner_update          - Tick timer, spawn enemies
  spawner_increase_difficulty
  spawner_set_wave

Zero Page ($48-$4A):
  spawner_timer           - Frames until next spawn
  spawner_wave            - Current wave number
  spawner_difficulty      - Difficulty multiplier
```

**powerup.asm** - Collectibles

```
Functions:
  powerup_init            - Clear all powerups
  powerup_spawn           - Create powerup (uses ZP params)
  powerup_update_all      - Move toward player (magnet)
  powerup_render_all      - Draw to OAM

Types:
  PWR_TYPE_XP_GEM   = 0
  PWR_TYPE_HEALTH   = 1
  PWR_TYPE_COIN     = 2
  PWR_TYPE_MAGNET   = 3
```

---

## Memory Map

### Zero Page ($00-$FF)

```
$00-$0F   Engine reserved (frame counter, temp vars)
$10-$1F   Input (buttons, buttons_pressed, etc.)
$20-$2F   Player state (x, y, health, level, etc.)
$30-$3F   Game state (game_state, timers, etc.)
$40-$4F   Action module (projectile params, spawner, powerup)
$50-$FF   Available for game use
```

### RAM ($0000-$07FF)

```
$0000-$00FF   Zero Page
$0100-$01FF   Stack
$0200-$02FF   OAM Shadow (sprite data, DMA'd to PPU)
$0300-$07FF   General RAM (entity arrays, buffers)
```

### PRG ROM Layout (MMC3)

```
$8000-$9FFF   Bank 0 (swappable) - Game code
$A000-$BFFF   Bank 1 (swappable) - Game code/data
$C000-$DFFF   Bank 2 (fixed) - Engine code
$E000-$FFFF   Bank 3 (fixed) - Vectors, init
```

### CHR ROM Layout (8KB banks)

```
CHR Bank 0: sprites.chr
  $00-$0F: Player (32x32, 16 tiles)
  $10-$1F: Enemy (32x32, 16 tiles)
  $20-$23: Projectile (8x8, 4 tiles)
  $24-$2F: Powerups
  $30-$7F: Available
  $80-$FF: Background tiles
```

---

## Data Flow Diagrams

### Player Movement

```
Controller → input.asm → buttons_pressed → game_main.asm
                                              │
                            ┌─────────────────┴─────────────────┐
                            │         update_player()           │
                            │                                   │
                            │  if BTN_LEFT:  player_x -= 2     │
                            │  if BTN_RIGHT: player_x += 2     │
                            │  if BTN_UP:    player_y -= 2     │
                            │  if BTN_DOWN:  player_y += 2     │
                            └─────────────────┬─────────────────┘
                                              │
                                              ▼
                                        update_sprites()
                                              │
                                              ▼
                                         OAM $0200+
```

### Enemy Auto-Fire

```
┌─────────────────────────────────────────────────────────────────┐
│                    update_enemy()                                │
│                                                                  │
│   enemy_fire_timer > 0?                                         │
│         │                                                        │
│    YES  │  NO                                                    │
│         │   │                                                    │
│         ▼   ▼                                                    │
│   timer--   Reset timer to 60                                   │
│             │                                                    │
│             ▼                                                    │
│   ┌─────────────────────────────────────┐                       │
│   │ Set projectile_spawn_x = enemy_x    │                       │
│   │ Set projectile_spawn_y = enemy_y+8  │                       │
│   │ Set projectile_spawn_vx = -3        │ ◄── Shoots LEFT      │
│   │ Set projectile_spawn_vy = 0         │                       │
│   │ Set projectile_spawn_type = LASER   │                       │
│   │ Set projectile_spawn_flags = ENEMY  │                       │
│   │ Call projectile_spawn               │                       │
│   └─────────────────────────────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Hygiene Checkpoints

### After Every Major Change

- [ ] Code compiles without errors
- [ ] ROM runs in Mesen without crashes
- [ ] No new linker warnings
- [ ] Comments updated for changed code
- [ ] This document updated if architecture changed

### Weekly Review

- [ ] Remove dead code
- [ ] Check for unused variables
- [ ] Verify ZP allocations don't overlap
- [ ] Test all game states
- [ ] Backup working ROM

### Before New Feature

- [ ] Document the feature in this file first
- [ ] Identify which files will change
- [ ] Check memory budget (RAM, ROM, CHR)
- [ ] Plan rollback strategy

### Self-Healing Validations (Built into Pipeline)

```python
# In unified_pipeline.py:
- Validates PNG dimensions are multiples of 8
- Warns if sprite count exceeds platform limits
- Checks CHR file size matches expected
- Verifies palette indices are valid
- Reports if no sprites detected (possible error)
```

---

## Quick Reference

### Common Tasks

**Add new sprite to game:**

1. Process with pipeline: `python tools/unified_pipeline.py sprite.png -o gfx/processed/`
2. Copy CHR: `copy gfx/processed/sprites.chr src/game/assets/`
3. Update `sprite_tiles.inc` with new tile indices
4. Add rendering code to `update_sprites` in game_main.asm
5. Rebuild: `compile.bat`

**Add new enemy type:**

1. Add enemy state variables in BSS section
2. Add update_enemy_X proc
3. Add rendering in update_sprites
4. Update CHR with enemy tiles

**Debug sprite issues:**

1. Open ROM in Mesen
2. Debug → PPU Viewer → Sprites tab
3. Check tile indices, palette, position
4. Verify CHR bank is correct

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2026-01-10 | Initial architecture with player, enemy, projectiles |
| 0.2.0 | 2026-01-10 | Added ARDK HAL foundation (types.h, hal.h, entity.h, NES/Genesis stubs) |

---

*Keep this document updated! It's your map through the codebase.*
