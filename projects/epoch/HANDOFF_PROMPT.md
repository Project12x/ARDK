# EPOCH - LLM/Engineer Handoff Prompt

> **Use this prompt to onboard a new LLM or developer to continue EPOCH development**  
> **Last Updated**: 2026-01-24

---

## Quick Start

You are continuing development of **EPOCH**, a Sega Genesis game built with SGDK. This is a "Zelda meets Tower Defense" survivor-like with continuous directional fire combat.

**Current State**: v0.7.18 - **PLAYABLE, OPTIMIZED, ART WIP**

Core gameplay loop is functional. Performance optimized. Art assets being finalized via manual pipeline.

---

## Essential Files to Read (Priority Order)

### 1. Current Status (START HERE)

```
projects/epoch/PROJECT_STATE.md           # What's done, what's not, immediate next steps
```

### 2. Architecture & Technical Docs

```
projects/epoch/TECHNICAL_OVERVIEW.md      # Full architecture, directory structure, hardware reference
```

### 3. Development Roadmap

```
MASTER_IMPLEMENTATION_PLAN.md             # Milestones, phases, planned features
```

### 4. Source Code (Key Files)

```
projects/epoch/src/main.c                  # Game loop, player, camera (34KB)
projects/epoch/src/engine/                 # Core systems (spatial, entity, animation)
projects/epoch/src/game/                   # Gameplay (enemies, projectiles, fenrir, director)
projects/epoch/inc/constants.h             # Game constants, fixed-point macros
```

### 5. Resources

```
projects/epoch/res/resources.res           # SGDK sprite/palette definitions
projects/epoch/build.bat                   # Build script
```

---

## What's Done (v0.7.18)

### Core Systems ✅

- Player movement (8-dir, dash, strafe lock)
- Continuous auto-fire with projectiles
- Enemy spawning via wave director
- Fenrir companion (follow/attack modes)
- XP pickups and collection
- Background map scrolling

### Engine ✅

- Modular architecture (`engine/` + `game/`)
- Spatial hash grid for collision
- Three-Gate collision filter (90% CPU reduction)
- Frame staggering (50% collision reduction)
- Sprite caching (position/flip/visibility)
- Object pool pattern (no runtime allocation)
- SRAM-based profiler

### Performance ✅

- 60 FPS with 24 enemies + 20 projectiles
- Time-sliced tile collision
- Flicker management (depth cycling)

---

## What's NOT Done

### Art Assets 🔨 (User Handling)

- Hero sprite direction mapping incorrect
- Fenrir needs proper terrier sprite
- Enemies need synthwave cyber virus theme
- UI elements (health bar, XP bar)

### Gameplay Features 🔜

- **Weapon Upgrade System** - XP → level up → stats scale
- **Enemy AI Differentiation** - Tank/Rusher/Ranged unique behaviors
- **Pickup Magnet Effect** - Auto-collect XP radius
- **Fenrir Combat Polish** - Damage dealing, targeting
- **Screen Shake / VFX** - Hit feedback
- **Audio Polish** - SFX variety, level up jingle

### Future Milestones 📋

- Boss encounters
- Town/NPC dialogue system
- Tower placement (build mode UI stub exists)
- Zone transitions

---

## Build & Test

```batch
# Prerequisites: SGDK installed, GDK environment variable set
cd projects/epoch
build.bat
# Output: out/rom.bin
```

**Emulator**: BlastEm recommended (<https://www.retrodev.com/blastem/>)

---

## Directory Structure

```
projects/epoch/
├── build.bat                  # SGDK build script
├── PROJECT_STATE.md           # Current status (update frequently)
├── TECHNICAL_OVERVIEW.md      # Full architecture docs
├── HANDOFF_PROMPT.md          # This file
│
├── inc/                       # Headers
├── src/
│   ├── main.c                 # Game loop, player, camera
│   ├── engine/                # Spatial, entity, animation, math, profiler
│   └── game/                  # Enemies, projectiles, fenrir, director, pickups
├── res/
│   ├── resources.res          # Resource definitions
│   ├── sprites/               # Sprite sheets
│   └── tilesets/              # Background tiles
└── out/                       # Build output (rom.bin)
```

---

## Key Technical Details

### Collision System

- **Three-Gate Filter**: Bitmask → Manhattan → AABB
- **Frame Staggering**: Half entities checked per frame
- **Spatial Hash**: 32px grid cells, O(1) lookup

### Sprite Management

- **Object Pool**: Pre-allocated, no runtime alloc
- **SAT Layout**: Slots 0-1 Player/Fenrir, 2-25 Enemies, 26-45 Projectiles
- **Caching**: Position, flip, visibility cached to avoid redundant SGDK calls

### Fixed-Point Math

- **8.8 format**: Upper 8 bits integer, lower 8 bits fractional
- **LUTs**: Sin/cos tables in `sinetable.h`
- **No floats**: All math uses integers and shifts

---

## You Are Encouraged To

### Implement Engine Features

The following are ready to implement (no art required):

1. Weapon upgrade system
2. Enemy AI differentiation
3. Pickup magnet effect
4. Fenrir combat polish
5. Screen shake / hit feedback
6. Audio polish

### Refactor If Needed

- main.c is large (34KB) - can be split further
- Code follows 68000 optimization rules per genesis.md

### Update Documentation

- Keep PROJECT_STATE.md current
- Update MASTER_IMPLEMENTATION_PLAN.md when completing phases

---

## Genesis Hardware Quick Reference

| Resource | Limit |
|----------|-------|
| CPU | Motorola 68000 @ 7.67 MHz |
| RAM | 64KB |
| VRAM | 64KB |
| Resolution | 320×224 pixels |
| Sprites | 80 total, 20 per scanline |
| Palettes | 4 × 16 colors (64 total) |

---

## Success Criteria

### Current Goal: v1.0 (Progression & Depth)

- [ ] Weapon upgrade system working
- [ ] Enemy type differentiation (Tank/Rusher/Ranged)
- [ ] Pickup magnet effect
- [ ] Fenrir deals damage to enemies
- [ ] Final art assets integrated

### Stretch: v1.5 (Polish)

- [ ] Screen shake, particles
- [ ] Audio variety
- [ ] UI/HUD polish
- [ ] Boss encounter

---

*This project is playable and optimized. Focus on adding depth and polish.*
