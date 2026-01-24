# NES Reusable Engine Architecture Guide

**Last Updated:** January 2026
**Purpose:** Design pattern for bespoke NES engines usable across multiple games

---

## Table of Contents

1. [Philosophy & Goals](#philosophy--goals)
2. [Directory Structure](#directory-structure)
3. [Separation of Concerns](#separation-of-concerns)
4. [Hardware Abstraction Layer (HAL)](#hardware-abstraction-layer-hal)
5. [Core Engine Systems](#core-engine-systems)
6. [Game Layer Integration](#game-layer-integration)
7. [Memory Management](#memory-management)
8. [Build System Integration](#build-system-integration)
9. [Porting Considerations](#porting-considerations)
10. [Example Implementation](#example-implementation)

---

## Philosophy & Goals

### Core Principles

1. **Separation of Concerns**: Engine code is completely independent of game logic
2. **Hardware Abstraction**: Platform-specific code isolated in HAL layer
3. **Reusability**: Engine can be dropped into new projects without modification
4. **Portability**: Design with future ports in mind (Genesis, PC Engine)
5. **AI-Friendly**: Clear interfaces and documentation for LLM-assisted development

### Design Goals

- **Minimize coupling**: Game should never directly access hardware registers
- **Maximize reuse**: 80% of engine code unchanged between projects
- **Simplify porting**: Only HAL layer needs rewriting for new platforms
- **Enable iteration**: Game developers focus on gameplay, not hardware details

---

## Directory Structure

### Recommended Layout

```
project/
├── src/
│   ├── engine/               # Reusable engine (platform-agnostic where possible)
│   │   ├── entry.asm         # System initialization, vectors, entry point
│   │   ├── hal/              # Hardware Abstraction Layer
│   │   │   ├── nes/          # NES-specific implementations
│   │   │   │   ├── ppu.asm   # PPU control
│   │   │   │   ├── apu.asm   # Audio control
│   │   │   │   ├── input.asm # Controller reading
│   │   │   │   └── nmi.asm   # VBlank interrupt
│   │   │   └── hal.inc       # HAL interface definitions
│   │   ├── core/             # Platform-independent core systems
│   │   │   ├── entity.asm    # Entity pooling system
│   │   │   ├── collision.asm # AABB collision detection
│   │   │   ├── math.asm      # Math utilities (lookup tables)
│   │   │   └── state.asm     # State machine framework
│   │   ├── utils/            # Utility functions
│   │   │   ├── random.asm    # PRNG
│   │   │   ├── memory.asm    # Memory utilities
│   │   │   └── timing.asm    # Frame counting, delays
│   │   └── engine.inc        # Engine-wide definitions
│   │
│   ├── game/                 # Game-specific code (NOT reusable)
│   │   ├── src/
│   │   │   ├── game_main.asm # Game entry point
│   │   │   ├── states/       # Game states (title, playing, etc.)
│   │   │   ├── entities/     # Player, enemy implementations
│   │   │   └── config.inc    # Game configuration
│   │   └── assets/
│   │       ├── sprites.chr   # Graphics data
│   │       ├── music.s       # FamiStudio export
│   │       └── data/         # Level data, tables
│   │
│   └── mapper/               # Mapper-specific code (MMC3, MMC5, etc.)
│       └── mmc3.asm
│
├── tools/                    # Build tools
├── gfx/                      # Graphics sources (PNG, etc.)
├── audio/                    # Music sources (FamiStudio projects)
├── config/                   # Build configs (ld65 config files)
└── docs/                     # Documentation
```

---

## Separation of Concerns

### Three-Layer Architecture

```
┌─────────────────────────────────────┐
│         GAME LAYER                  │  ← Game-specific logic
│  (states, entities, gameplay)       │
└─────────────────────────────────────┘
                 ▼
┌─────────────────────────────────────┐
│      ENGINE CORE LAYER              │  ← Platform-agnostic
│  (entity system, collision, math)   │
└─────────────────────────────────────┘
                 ▼
┌─────────────────────────────────────┐
│   HARDWARE ABSTRACTION LAYER (HAL)  │  ← Platform-specific
│     (PPU, APU, Input, NMI)          │
└─────────────────────────────────────┘
```

### Communication Flow

- **Game → Engine**: Calls engine APIs
- **Engine → HAL**: Uses HAL interfaces
- **HAL → Hardware**: Direct register access
- **Game → HAL**: NEVER allowed (use engine APIs)

---

## Hardware Abstraction Layer (HAL)

### Purpose

Isolate all platform-specific code in one place for easy porting.

### HAL Interface Pattern

Define abstract interfaces, implement per-platform:

**hal/hal.inc** (Interface):
```asm
; HAL interface - platform-independent declarations
.global hal_init
.global hal_vblank_wait
.global hal_sprite_clear
.global hal_sprite_draw
.global hal_input_read
```

**hal/nes/ppu.asm** (NES Implementation):
```asm
.include "../hal.inc"

.export hal_sprite_clear
.export hal_sprite_draw

.proc hal_sprite_clear
    ; NES-specific OAM clearing
    lda #$FF
    ldx #0
@loop:
    sta $0200, x
    inx
    bne @loop
    rts
.endproc

.proc hal_sprite_draw
    ; A = tile, X = x, Y = y, temp1 = attributes
    ; NES-specific sprite rendering
    ; ...
    rts
.endproc
```

### HAL Modules

#### PPU (Graphics)
- Screen enable/disable
- Sprite management (OAM)
- Background updates
- Palette setting
- Scrolling

#### APU (Audio)
- Music playback
- Sound effect triggers
- Channel management

#### Input
- Controller polling
- Button state tracking
- Multi-controller support

#### NMI (VBlank)
- Frame synchronization
- OAM DMA
- VRAM updates

---

## Core Engine Systems

### Entity System

**Purpose**: Manage game objects (player, enemies, projectiles)

**Features**:
- Fixed-size pools (no dynamic allocation)
- Component-based design
- Automatic lifecycle management

**entity.asm** (Reusable):
```asm
; Platform-independent entity system
.include "../engine.inc"

.segment "BSS"
entity_pool:    .res MAX_ENTITIES * ENTITY_SIZE

.segment "CODE"

.proc entity_spawn
    ; Find free slot
    ; Initialize entity
    ; Return index in X
    rts
.endproc

.proc entity_update_all
    ; Update positions, apply velocity
    ; Platform-independent physics
    rts
.endproc
```

### Collision Detection

**Purpose**: AABB, circle, point-rect collision

**collision.asm** (Reusable):
```asm
; Pure math - works on any platform unchanged

.proc check_aabb_collision
    ; Input: coll_x1, y1, w1, h1, x2, y2, w2, h2
    ; Output: Carry = 1 if collision
    ; ... pure math logic ...
    rts
.endproc
```

### State Machine

**Purpose**: Game state management (title, playing, paused, etc.)

**state.asm** (Framework):
```asm
; Generic state machine framework

.segment "ZEROPAGE"
current_state:  .res 1
next_state:     .res 1

.segment "CODE"

.proc state_update
    ; Call current state handler from jump table
    ldx current_state
    jsr (state_handlers, x)

    ; Check for state transition
    lda next_state
    cmp #$FF
    beq @no_change
    sta current_state
    lda #$FF
    sta next_state
@no_change:
    rts
.endproc
```

---

## Game Layer Integration

### Game Interface Contract

The game layer implements these required functions:

```asm
; game/src/game_main.asm

.export Game_Init      ; Called once at startup
.export Game_Update    ; Called every frame

.proc Game_Init
    ; Initialize game-specific systems
    ; Set up initial state
    rts
.endproc

.proc Game_Update
    ; Read input via HAL
    ; Update game logic via engine APIs
    ; Render via HAL
    rts
.endproc
```

### Engine Entry Point

**engine/entry.asm**:
```asm
.import Game_Init
.import Game_Update

.proc reset
    ; 1. Hardware initialization
    jsr hal_init

    ; 2. Engine initialization
    jsr engine_init

    ; 3. Game initialization
    jsr Game_Init

    ; 4. Main loop
@loop:
    jsr hal_vblank_wait
    jsr Game_Update
    jmp @loop
.endproc
```

---

## Memory Management

### Zero Page Allocation

Divide zero page carefully:

```asm
; engine/engine.inc

; $00-$0F: Engine core (16 bytes)
engine_temp1    = $00
engine_temp2    = $01
frame_counter   = $02
nmi_flag        = $03

; $10-$2F: HAL layer (32 bytes)
scroll_x        = $10
scroll_y        = $11
ppu_ctrl_shadow = $12

; $30-$7F: Game layer (80 bytes)
player_x        = $30
player_y        = $31
; ... game variables ...

; $80-$FF: Reserved for stack operations
```

### RAM Organization

```
$0000-$00FF: Zero Page (256 bytes)
  ├── $00-$0F: Engine temps
  ├── $10-$2F: HAL state
  └── $30-$FF: Game + stack

$0100-$01FF: Stack (256 bytes)

$0200-$02FF: OAM Buffer (256 bytes)

$0300-$07FF: General RAM (1.25KB)
  ├── Engine pools
  ├── Game state
  └── Level data
```

---

## Build System Integration

### Makefile with Engine/Game Separation

```makefile
# Makefile

# Engine sources
ENGINE_SRCS = src/engine/entry.asm \
              src/engine/hal/nes/ppu.asm \
              src/engine/hal/nes/nmi.asm \
              src/engine/core/entity.asm \
              src/engine/core/collision.asm \
              src/engine/utils/random.asm

# Game sources
GAME_SRCS = src/game/src/game_main.asm \
            src/game/src/states/title.asm \
            src/game/src/states/gameplay.asm

# Assemble engine
engine: $(ENGINE_SRCS)
	@echo "Building engine..."
	@for src in $(ENGINE_SRCS); do \
		ca65 -t nes $$src -o build/$$(basename $$src .asm).o; \
	done

# Assemble game
game: $(GAME_SRCS)
	@echo "Building game..."
	@for src in $(GAME_SRCS); do \
		ca65 -t nes $$src -o build/$$(basename $$src .asm).o; \
	done

# Link
rom: engine game
	ld65 -C config/mmc3.cfg -o build/game.nes build/*.o
```

---

## Porting Considerations

### NES → Sega Genesis

**What Changes**:
- HAL layer completely rewritten (VDP instead of PPU)
- Sprite system (80 sprites vs 64)
- Resolution (320x224 vs 256x240)
- Color system (512 colors vs 54)

**What Stays**:
- Entity system
- Collision detection
- Math utilities
- State machine
- Game logic

**Porting Estimate**: ~20% code rewrite (HAL only)

### NES → PC Engine

**What Changes**:
- HAL layer (similar 6502 CPU makes this easier)
- Sprite/tile formats
- Sound chip

**What Stays**:
- Nearly all engine core
- All game logic

**Porting Estimate**: ~10% code rewrite

---

## Example Implementation

### Minimal Reusable Engine

**engine/engine.inc**:
```asm
; Engine-wide constants and ZP allocation
MAX_ENTITIES = 16
ENTITY_SIZE = 16

; Zero page
.globalzp engine_temp1, engine_temp2
.globalzp frame_counter, nmi_flag
```

**engine/entry.asm**:
```asm
.include "engine.inc"
.import Game_Init, Game_Update
.import hal_init, hal_vblank_wait

.segment "ZEROPAGE"
.exportzp frame_counter, nmi_flag
frame_counter:  .res 1
nmi_flag:       .res 1
engine_temp1:   .res 1
engine_temp2:   .res 1

.segment "CODE"
.export reset

.proc reset
    sei
    cld
    ldx #$FF
    txs

    jsr hal_init
    jsr Game_Init

@loop:
    jsr hal_vblank_wait
    jsr Game_Update
    inc frame_counter
    jmp @loop
.endproc
```

**game/src/game_main.asm**:
```asm
.include "../../engine/engine.inc"
.import hal_sprite_draw

.export Game_Init, Game_Update

.segment "ZEROPAGE"
player_x: .res 1
player_y: .res 1

.segment "CODE"

.proc Game_Init
    lda #128
    sta player_x
    sta player_y
    rts
.endproc

.proc Game_Update
    ; Read input (HAL)
    ; Update game state (engine)
    ; Render (HAL)

    lda #$00            ; Tile
    ldx player_x
    ldy player_y
    jsr hal_sprite_draw

    rts
.endproc
```

---

## Best Practices

### DO ✅

- Keep all hardware register access in HAL
- Use engine APIs in game code
- Document all engine interfaces
- Separate engine/game in build system
- Use include guards in .inc files
- Export/import cleanly between layers
- Comment platform-specific assumptions

### DON'T ❌

- Access PPU/APU registers from game code
- Hardcode NES-specific values in engine core
- Mix game logic into engine systems
- Use NES-specific assembly in portable code
- Couple game state to engine internals

---

## Migration Path

### Existing Project → Reusable Engine

1. **Identify Hardware Access**
   - Search for `$2000-$2007` (PPU registers)
   - Search for `$4000-$4017` (APU/IO registers)
   - Move to HAL layer

2. **Extract Generic Systems**
   - Entity management
   - Collision detection
   - Math functions
   - Move to engine/core/

3. **Create HAL Abstractions**
   - Define interfaces in hal/hal.inc
   - Implement in hal/nes/
   - Update game code to use HAL

4. **Reorganize Directory Structure**
   - Move engine code to src/engine/
   - Move game code to src/game/
   - Update build system

5. **Document Interfaces**
   - Add comments to all exported functions
   - Create architecture docs
   - Document ZP allocation

---

## Resources

### Example Projects with Good Architecture

- **MK1_NES**: [github.com/mojontwins/MK1_NES](https://github.com/mojontwins/MK1_NES)
- **nes-starter-kit**: [github.com/igwgames/nes-starter-kit](https://github.com/igwgames/nes-starter-kit)

### Further Reading

- NESDev Wiki: [nesdev.org/wiki/Programming_guide](https://www.nesdev.org/wiki/Programming_guide)
- Shiru's C Guide: [Programming NES games in C](https://shiru.untergrund.net/articles/programming_nes_games_in_c.htm)

---

**End of Reusable Engine Architecture Guide**
