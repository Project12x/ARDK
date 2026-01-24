# EPOCH Master Implementation Plan

> **Vision**: A complete, polished Genesis game that pushes the hardware  
> **Philosophy**: Build → Play → Learn → Iterate  
> **Last Updated**: 2026-01-24

---

## Design Pillars

1. **"Zelda meets Tower Defense across Time"** - Hybrid exploration + defense
2. **Continuous Action** - Always shooting, always moving
3. **Companion Synergy** - Fenrir as strategic partner, not passive follower
4. **Emergent Challenge** - Systems that create unexpected situations

---

## Current State (v0.7.18)

✅ **Core Loop**: Combat, Waves, Tower Defense  
✅ **Foundation**: Graphics Pipeline (MAP API), Physics (32-bit), Collision (Three-Gate)  
✅ **Debug**: GDB Automation, Flicker Manager, SRAM Profiler  
✅ **Optimization**: Spatial Hashing, Frame Staggering, Sprite Caching  
✅ **Rendering**: Object Pool Sprites, Z-Sorting, Hybrid Sprite Architecture  
🔨 **Art**: Sprite pipeline manual (user handling)  

---

## Milestone 2: Architectural Foundation (v0.6) ✅ COMPLETE

### Phase 2.1: Engine Modularization ✅

- Split `main.c` into `src/engine/` and `src/game/`.
- ECS-Lite (24-byte aligned structs).

### Phase 2.2: Data-Driven Design ✅

- `EnemyDef` structs for stats/sprites (`enemy_data.c`).
- VTable-lite AI (`AI_Chase`, `AI_Flank`).

### Phase 2.3: Performance & Scale ✅

- Spatial Hash Grid.
- Dynamic Sprite Culling.

### Phase 2.4: Director System ✅

- Wave Manager with escalating difficulty.
- Enemy variation (Grunt → Rusher → Tank).

### Phase 2.5: Asset Polish ✅

- Fenrir sprite integrated.
- Projectile and enemy sprites.

---

## Milestone 2.5: Optimization Deep Dive (v0.7) ✅ COMPLETE

### Phase 5: CPU Optimization ✅

- Removed 32-bit multiplication from AI.
- AI Time-Slicing (1/4 frame updates).
- Pointer Walking loops.
- Fast Math LUTs.

### Phase 6: Rendering Optimization ✅

- Object Pooling for Projectiles.
- Z-Sorting via `SPR_setDepth()`.
- VRAM Slotting verification.

### Phase 7: Hybrid Sprite Pool Architecture ✅

- **Object Pool Pattern**: Pre-allocate all sprites at init.
- **Graphics Swapping**: `SPR_setDefinition()` for dynamic enemy types.
- **SAT Layout**:
  - Slots 0-1: Player/Fenrir (permanent)
  - Slots 2-25: Enemy Pool (24, graphics-swappable)
  - Slots 26-45: Projectile Pool (20)
  - Slots 46-55: Dynamic Zone (pickups/bosses)
- **Background Objects**: Tower/buildables use BG tiles (zero SAT cost).

---

## Milestone 3: Exploration Systems (v0.8)

### Phase 3.1: Camera & Scrolling ✅

- Smooth follow camera.

### Phase 3.2: World Structure 🔜

- Zone transitions (Combat ↔ Town).
- Tilemap collision polish.

### Phase 3.3: Fenrir Companion ✅

- Follow/Guard/Attack modes.
- AI state machine.

---

## Milestone 4: Progression & Depth (v1.0)

### Phase 4.1: Weapon Upgrade System 🔜

- [ ] XP thresholds trigger level up
- [ ] Weapon stats scale with level (fire rate, spread, damage)
- [ ] Visual/audio feedback on level up
- [ ] Max weapon level cap (5?)

### Phase 4.2: Enemy AI Differentiation 🔜

- [ ] Tank: Slow movement, high HP, blocks projectiles
- [ ] Rusher: Fast charge at player, low HP
- [ ] Ranged: Maintains distance, fires projectiles
- [ ] AI behavior trees per enemy type

### Phase 4.3: Pickup Magnet Effect 🔜

- [ ] Auto-collect XP gems within radius
- [ ] Magnet radius scales with player level
- [ ] Smooth attraction movement

### Phase 4.4: Fenrir Combat Polish 🔜

- [ ] Damage dealing to enemies (attack mode)
- [ ] Attack cooldown tuning
- [ ] Better target selection (nearest, lowest HP)
- [ ] Combat feedback (hit flash)

### Phase 4.5: Content Expansion

- **Enemy Types**:
  - [x] Grunt (Basic Chase AI)
  - [x] Rusher (AI_Flank, faster)
  - [x] Tank (Slow, High HP)
- [ ] Boss Encounter
- [ ] Environmental Hazards

---

## Milestone 5: Polish & Release (v1.5)

### Phase 5.1: Audio & Atmosphere 🔜

- [x] XGM2 integration
- [ ] Sound effects variety (enemy death, level up, pickup)
- [ ] Level up jingle
- [ ] BGM transitions between zones

### Phase 5.2: Visual Polish 🔜

- [ ] Screen shake on player damage
- [ ] Hit flash effects (enemies/player)
- [ ] Particles (death puffs, XP sparkle)
- [ ] UI/HUD polish (health bar, XP bar)

### Phase 5.3: Art Assets (User Pipeline)

- [ ] Hero sprite: 8-directional with proper frame mapping
- [ ] Fenrir sprite: Brown/gold terrier, shared palette
- [ ] Enemy sprites: Synthwave cyber virus theme
- [ ] Projectile sprites
- [ ] UI elements

---

## Technical Decisions (Locked)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Sprite Management | Hybrid Object Pool | Avoids SGDK corruption, stable 24 enemies |
| Map System | Full scroll | MAP API with BG_B |
| Entity Cap | 64 fixed | Slot-based allocation |
| Collision | AABB + Spatial Hash | O(1) lookup |
| Static Objects | BG tiles | Zero SAT cost |

---

## Risk & Contingency

| Risk | Impact | Mitigation |
|------|--------|------------|
| Sprite limit | High | Object Pool ✅, Culling ✅ |
| CPU bottleneck | High | Spatial Hashing ✅, Time-Slicing ✅ |
| SGDK Corruption | High | Object Pool ✅ (no runtime alloc) |
| Content Pipeline | Medium | Automated Asset Pipeline ✅ |

---

## Immediate Next Steps

### Engine (Agent Can Implement)

1. **Weapon Upgrade System** - XP → level up → stats scale
2. **Enemy AI Differentiation** - Tank/Rusher/Ranged behaviors
3. **Pickup Magnet Effect** - Auto-collect XP radius
4. **Fenrir Combat Polish** - Damage dealing, targeting
5. **Screen Shake / Hit Feedback** - Camera shake, flash effects
6. **Audio Polish** - SFX variety, level up jingle

### Art (User Pipeline)

1. Hero sprite with correct direction frames
2. Fenrir terrier with shared palette
3. Synthwave cyber virus enemies
4. UI elements (health/XP bars)

---

## Success Vision

A complete Genesis game that:

- Runs flawlessly on real hardware (60fps)
- Handles 24 concurrent enemies with stable rendering
- Offers deep, strategic combat and progression
