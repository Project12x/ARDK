# EPOCH - Project State

> **Version**: 0.7.18  
> **Last Updated**: 2026-01-24  
> **Status**: PLAYABLE - Performance Optimized

---

## Current State Summary

**EPOCH** is a Genesis survivor-like game with tower defense elements. The game is playable with core systems functional.

### ✅ Implemented Systems

| System | Status | Notes |
|--------|--------|-------|
| **Player Movement** | ✅ Complete | 8-dir, dash, strafe lock |
| **Projectile System** | ✅ Complete | Auto-fire, collision |
| **Enemy Spawning** | ✅ Complete | Wave-based via director |
| **Fenrir Companion** | ✅ Complete | Follow, attack modes |
| **Collision Detection** | ✅ Optimized | Three-Gate filter, frame staggering |
| **Spatial Grid** | ✅ Optimized | Static hash grid, intrusive lists |
| **Sprite Caching** | ✅ Complete | Position, flip, visibility |
| **Background Scrolling** | ✅ Complete | Large map streaming |
| **Audio** | ✅ Basic | XGM2 driver, SFX |
| **Debug Profiler** | ✅ Complete | SRAM timing output |

### 🔨 In Progress

| System | Status | Notes |
|--------|--------|-------|
| **Art Assets** | 🔨 WIP | User handling sprite pipeline manually |
| **Hero Direction** | 🔨 Needs Fix | Frame-to-direction mapping incorrect |
| **Enemy Variety** | 🔨 Placeholder | Using placeholder sprites |

### 📋 Not Started

| System | Priority | Notes |
|--------|----------|-------|
| Level-up System | Medium | XP collection exists but no upgrades |
| Tower Placement | Medium | Build mode UI exists, placement TBD |
| Town/NPC System | Low | Dialogue system not started |
| Boss Encounters | Low | Design TBD |

---

## Performance Status

### Optimizations Completed (v0.7.x)

1. **Sprite Caching** - All entities cache position/flip/visibility
2. **Three-Gate Collision** - Bitmask → Manhattan → AABB filtering
3. **Frame Staggering** - 50% CPU reduction on collision checks
4. **Time-Sliced Tile Collision** - Enemies check every 2 frames
5. **Scroll Caching** - VDP calls only on position change

### Known Performance Costs

- **MAP_scrollTo** - Required for large map tile streaming (unavoidable)
- **SPR_update** - SGDK sprite engine overhead (normal)

---

## File Structure

```
src/
├── main.c              # Game loop, player, camera (34KB)
├── engine/
│   ├── animation.c/h   # Frame-based animation system
│   ├── entity.c/h      # Entity pool, collision masks
│   ├── spatial.c/h     # Spatial hash grid, Three-Gate
│   ├── math_fast.c/h   # Integer math, LUTs
│   ├── debug_sram.c/h  # SRAM profiler output
│   ├── raster.c/h      # Raster effects (unused)
│   ├── sinetable.h     # Pre-calculated sine LUT
│   └── system.c/h      # VBlank, frame timing
├── game/
│   ├── enemies.c/h     # Enemy AI, spawning, sprite management
│   ├── projectiles.c/h # Projectile physics, collision
│   ├── fenrir.c/h      # Dog companion AI
│   ├── director.c/h    # Wave spawning logic
│   ├── pickups.c       # XP gems, health drops
│   ├── enemy_data.c/h  # Enemy type definitions
│   └── audio.c         # Sound effect triggers
└── ui/
    └── build_mode.c    # Tower placement UI (stub)
```

---

## Engine Improvement Opportunities

### Ready to Implement

1. **Weapon Upgrade System**
   - XP collection exists, upgrade logic needed
   - Weapon level affects fire rate, spread, damage

2. **Enemy Variety Logic**
   - enemy_data.h has type definitions
   - Need AI behavior differentiation (tank, rusher, ranged)

3. **Fenrir Attack Mode**
   - Basic AI exists, combat behavior needs tuning
   - Damage dealing to enemies

4. **Pickup Magnet Effect**
   - XP gems exist, auto-collect radius TBD

5. **Screen Shake / VFX**
   - Raster system exists but unused
   - Could add hit feedback effects

6. **Audio Polish**
   - More SFX variety (enemy death, level up)
   - BGM transitions

### Requires Art Assets

- New enemy sprites (user handling)
- Hero direction fix (user handling)
- UI elements (health bar, XP bar)

---

## Build & Test

```batch
cd projects/epoch
build.bat
# Output: out/rom.bin
```

**Emulator**: BlastEm recommended

---

## Recent Changes

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-24 | 0.7.18 | Reverted broken AI sprites, sprites stable |
| 2026-01-22 | 0.7.17 | Three-Gate collision, frame staggering |
| 2026-01-21 | 0.7.16 | Sprite caching (all entities) |
| 2026-01-20 | 0.7.15 | Time-sliced tile collision |

---

*This document is kept updated with project status.*
