# ARDK Master Plan
## Agentic Retro Development Kit - Unified Development Roadmap

> **Version**: 1.4
> **Last Updated**: 2026-01-11
> **Project**: NEON SURVIVORS + ARDK Cross-Platform Framework
> **Status**: Phase 1 Complete, Phase 2 In Progress

---

## Executive Summary

ARDK (Agentic Retro Development Kit) is a cross-platform retro game development framework that enables writing game logic once and compiling for multiple vintage platforms. NEON SURVIVORS serves as the flagship game demonstrating ARDK's capabilities.

**Vision**: Create the most developer-friendly retro game development toolkit, featuring AI-assisted asset pipelines, platform-agnostic APIs, and comprehensive documentation.

---

## Document Map

This master plan references all project artifacts. Use this as your navigation hub.

### Core Documentation

| Document | Location | Purpose | Status |
|----------|----------|---------|--------|
| **This File** | `ARDK_MASTER_PLAN.md` | Master roadmap, goals, phases | Active |
| [PROJECT_ARCHITECTURE.md](docs/PROJECT_ARCHITECTURE.md) | `docs/` | Technical architecture, HAL, memory maps | Complete |
| [PIPELINE_REFERENCE.md](docs/PIPELINE_REFERENCE.md) | `docs/` | Sprite pipeline detailed reference | Complete |
| [TOOLCHAIN_GUIDE.md](docs/TOOLCHAIN_GUIDE.md) | `docs/` | Platform toolchain installation | Complete |
| [ARDK_LIBRARIES.md](docs/ARDK_LIBRARIES.md) | `docs/` | Library & API planning | Complete |
| [DOCUMENTATION_STANDARDS.md](docs/DOCUMENTATION_STANDARDS.md) | `docs/` | Comment & documentation conventions | Complete |

### Supporting Documentation

| Document | Location | Purpose |
|----------|----------|---------|
| [QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md) | `docs/` | Command cheatsheet |
| [CROSS_PLATFORM_RESEARCH.md](docs/CROSS_PLATFORM_RESEARCH.md) | `docs/` | Platform comparison research |
| [REUSABLE_ENGINE_ARCHITECTURE.md](docs/REUSABLE_ENGINE_ARCHITECTURE.md) | `docs/` | Engine design patterns |

### Key Source Files - HAL Core

| File | Location | Purpose | Status |
|------|----------|---------|--------|
| `hal.h` | `src/hal/` | HAL interface (locked) | Complete |
| `entity.h` | `src/hal/` | Entity system (locked) | Complete |
| `entity.c` | `src/hal/` | Entity implementation | Complete |
| `types.h` | `src/hal/` | Platform-agnostic types | Complete |
| `hal_tiers.h` | `src/hal/` | Tier system (MINIMAL/STANDARD/STANDARD_PLUS/EXTENDED) | Complete |
| `platform_manifest.h` | `src/hal/` | Platform capabilities & migration | Complete |
| `asset_ids.h` | `src/hal/` | Asset ID allocation scheme | Complete |
| `asset_format.h` | `src/hal/` | Asset format definitions | Complete |
| `hal_common.c` | `src/hal/` | Shared HAL implementation | Complete |

### Key Source Files - Assembly HAL (Per-Family)

| File | Location | Family | Platforms |
|------|----------|--------|-----------|
| `hal_6502.inc` | `src/hal/asm/` | 6502 | NES, C64, PCE, Atari |
| `hal_68k.inc` | `src/hal/asm/` | 68000 | Genesis, Amiga, Neo Geo |
| `hal_z80_gb.inc` | `src/hal/asm/` | Z80 | Game Boy, SMS, MSX |

### Key Source Files - Platform Implementations

| File | Location | Platform |
|------|----------|----------|
| `hal_config.h` | `src/hal/nes/` | NES configuration |
| `hal_nes.c` | `src/hal/nes/` | NES HAL implementation |
| `hal_config.h` | `src/hal/genesis/` | Genesis configuration |
| `hal_genesis.c` | `src/hal/genesis/` | Genesis HAL implementation |

### Key Source Files - Tools

| File | Location | Purpose |
|------|----------|---------|
| `unified_pipeline.py` | `tools/` | Master sprite processor (17 platforms) |
| `verify_toolchains.py` | `tools/` | Toolchain verification |
| `extract_docs.py` | `tools/` | API documentation generator |
| `ardk_build.py` | `tools/` | Multi-platform build orchestrator |
| `generate_math_tables.py` | `tools/` | Sin/cos/atan2 lookup tables |

### AI-Powered Tools

| File | Location | Purpose |
|------|----------|---------|
| `ai_audio_analyzer.py` | `tools/` | Audio analysis & conversion hints |
| `ai_level_assistant.py` | `tools/` | Level design suggestions |
| `ai_code_optimizer.py` | `tools/` | Assembly optimization hints |
| `ai_palette_optimizer.py` | `tools/` | Palette reduction & optimization |

---

## Project Goals

### Primary Goals

1. **Complete NEON SURVIVORS for NES**
   - Playable vampire survivors clone
   - Wave-based enemies, XP/leveling, weapon upgrades
   - Polished with audio and visual effects

2. **Establish ARDK Framework**
   - Platform-agnostic HAL supporting 6+ platforms
   - Reusable entity system, collision, state machines
   - Comprehensive toolchain for asset conversion

3. **Create Distributable Tools**
   - Standalone sprite pipeline (PyPI)
   - Tilemap converter (Tiled/LDTK support)
   - ROM validators per platform

### Success Criteria

| Milestone | Criteria | Target |
|-----------|----------|--------|
| Playable Demo | 5-minute gameplay loop | Phase 2 |
| Multi-platform | Same game on NES + 1 other | Phase 4 |
| Tool Release | Sprite pipeline on PyPI | Phase 3 |
| Documentation | 100% API coverage | Ongoing |

---

## Adaptive Phased Roadmap

### Philosophy

This roadmap uses **adaptive phases** - each phase has clear goals but flexible implementation order. Complete all phase goals before advancing, but within a phase, tackle tasks in any order that unblocks progress.

---

## Platform Manifest System

The `platform_manifest.h` defines compile-time platform capabilities enabling build validation, asset validation, and optimal code generation.

### CPU Family Architecture

| Family | ID | Platforms | Endian | Word Size |
|--------|-----|-----------|--------|-----------|
| 6502 | 0x01 | NES, C64, PCE, Atari 2600/7800, Apple II, BBC | Little | 8-bit |
| Z80 | 0x02 | Game Boy, GBC, SMS, Game Gear, MSX, ZX Spectrum | Little | 8-bit |
| 68000 | 0x03 | Genesis, Amiga, Neo Geo, X68000, Sega CD, 32X | Big | 16/32-bit |
| 65816 | 0x04 | SNES, Super Famicom | Little | 16-bit |
| ARM | 0x05 | GBA, Nintendo DS | Little | 32-bit |

### Platform IDs

```text
6502 Family (0x01xx):
  ARDK_PLAT_NES         0x0100  (Primary)
  ARDK_PLAT_C64         0x0101
  ARDK_PLAT_PCE         0x0102
  ARDK_PLAT_ATARI2600   0x0103
  ARDK_PLAT_ATARI7800   0x0104
  ARDK_PLAT_APPLE2      0x0105
  ARDK_PLAT_BBC         0x0106

Z80 Family (0x02xx):
  ARDK_PLAT_GB          0x0200  (Primary)
  ARDK_PLAT_GBC         0x0201
  ARDK_PLAT_SMS         0x0202
  ARDK_PLAT_GG          0x0203
  ARDK_PLAT_MSX         0x0204
  ARDK_PLAT_ZX          0x0205
  ARDK_PLAT_COLECO      0x0206

68000 Family (0x03xx):
  ARDK_PLAT_GENESIS     0x0300  (Primary)
  ARDK_PLAT_AMIGA_OCS   0x0301
  ARDK_PLAT_AMIGA_AGA   0x0302
  ARDK_PLAT_NEOGEO      0x0303
  ARDK_PLAT_X68000      0x0304
  ARDK_PLAT_SEGACD      0x0305
  ARDK_PLAT_32X         0x0306

65816 Family (0x04xx):
  ARDK_PLAT_SNES        0x0400

ARM Family (0x05xx):
  ARDK_PLAT_GBA         0x0500
  ARDK_PLAT_NDS         0x0501
```

### Video Capabilities Flags

```text
Sprite Sizes:
  ARDK_SPRITE_SIZE_8x8      0x0001
  ARDK_SPRITE_SIZE_8x16     0x0002
  ARDK_SPRITE_SIZE_16x16    0x0004
  ARDK_SPRITE_SIZE_16x32    0x0008
  ARDK_SPRITE_SIZE_32x32    0x0010
  ARDK_SPRITE_SIZE_VARIABLE 0x0100

Background Modes:
  ARDK_BG_MODE_TILE         0x0001
  ARDK_BG_MODE_BITMAP       0x0002
  ARDK_BG_MODE_AFFINE       0x0004  (Mode 7)

Scroll Capabilities:
  ARDK_SCROLL_X             0x0001
  ARDK_SCROLL_Y             0x0002
  ARDK_SCROLL_PER_LINE      0x0004
  ARDK_SCROLL_PER_TILE      0x0008
```

### Audio Capabilities Flags

```text
Audio Channel Types:
  ARDK_AUDIO_PULSE          0x0001
  ARDK_AUDIO_TRIANGLE       0x0002
  ARDK_AUDIO_NOISE          0x0004
  ARDK_AUDIO_PCM            0x0008
  ARDK_AUDIO_FM             0x0010
  ARDK_AUDIO_WAVETABLE      0x0020
```

---

## Migration Strategy

### Primary Targets vs Migration Targets

**Primary Targets** (robust toolchains, focus development here):

- NES (6502) - cc65
- Genesis (68K) - SGDK
- Game Boy (Z80) - RGBDS

**Migration Targets** (port from primary):

- 6502 → C64, PCE, Atari 2600/7800
- 68K → Amiga, Neo Geo, X68000
- Z80 → SMS, Game Gear, MSX

### Migration Difficulty Levels

| Level | Code | Description |
|-------|------|-------------|
| SAME | 0 | Same platform (no migration) |
| TRIVIAL | 1 | Same family, same graphics chip |
| EASY | 2 | Same family, different graphics |
| MODERATE | 3 | Same family, significant differences |
| HARD | 4 | Different family, similar tier |
| IMPOSSIBLE | 255 | Cannot migrate |

### Migration Matrix

```text
From NES:
  → C64:     EASY      (Same CPU, different PPU)
  → PCE:     MODERATE  (65C02, different graphics)
  → Atari:   MODERATE  (Simplified graphics)

From Genesis:
  → Neo Geo: TRIVIAL   (Same CPU, enhanced graphics)
  → Amiga:   EASY      (Same CPU, different blitter)
  → X68000:  EASY      (Same CPU, enhanced)

From Game Boy:
  → GBC:     TRIVIAL   (Same + color)
  → SMS:     EASY      (True Z80, more colors)
  → MSX:     MODERATE  (Different graphics chip)
```

### Assembly HAL Selection

Each family shares an assembly HAL file:

```text
ARDK_ASM_HAL_6502     "hal/asm/hal_6502.inc"
ARDK_ASM_HAL_68K      "hal/asm/hal_68k.inc"
ARDK_ASM_HAL_Z80_GB   "hal/asm/hal_z80_gb.inc"
```

---

## HAL Dual-Tier System

### Design Philosophy: "Design at Peak, Downsample Within Tier"

Platforms have **separate tiers for Assets and Logic**. This allows systems like Neo Geo (STANDARD sprite aesthetic, STANDARD_PLUS logic capability) to be properly categorized.

- **Asset Tier**: Determines sprite aesthetic, color depth, audio style
- **Logic Tier**: Determines CPU budgets, entity counts, AI complexity

### Tier Hierarchy

```
MINIMAL (0)        → 8-bit baseline (NES, GB, C64, ZX, Atari)
MINIMAL_PLUS (1)   → Enhanced 8-bit (SMS, MSX2, NGP)
STANDARD (2)       → 16-bit consoles (Genesis, SNES, PCE, Amiga OCS)
STANDARD_PLUS (3)  → Enhanced 16-bit (Neo Geo, Sega CD, X68000, 32X)
EXTENDED (4)       → 32-bit portables (GBA, DS)
RETRO_PC (5)       → VGA-era reference (DOS VGA, Amiga AGA, Atari ST)
```

### Within-Tier Interpolation

Each tier has a **floor** (barely meets tier minimum) to **peak** (defines ceiling). This enables simultaneous NES+Genesis development by mapping capability levels correctly.

### Complete Platform Specifications

#### MINIMAL Tier (8-bit baseline)

| Position | Platform | CPU | MHz | RAM | Sprites | /Line | Col/Spr | Notes |
|----------|----------|-----|-----|-----|---------|-------|---------|-------|
| Floor | Atari 2600 | 6507 | 1.19 | 128B | 2 | 2 | 2 | Racing the beam |
| Low | ZX Spectrum | Z80 | 3.5 | 48KB* | SW | - | 2/cell | Attribute clash |
| Mid | C64 | 6510 | 1.02 | 64KB* | 8 | 8 | 4 MCM | VIC-II, SID audio |
| High | NES | 6502 | 1.79 | 2KB | 64 | 8 | 4 | Primary 6502 target |
| Peak | Game Boy | Z80-like | 4.19 | 8KB | 40 | 10 | 4 gray | |
| Peak+ | GBC | Z80-like | 8.38 | 32KB | 40 | 10 | 4/pal | Double speed mode |

*= shared/contended with video

**MINIMAL Design Direction**: Target GBC capabilities, reduce for NES (less RAM, slower CPU), further reduce for Atari (extreme limits).

#### MINIMAL_PLUS Tier (Enhanced 8-bit)

| Position | Platform | CPU | MHz | RAM | Sprites | /Line | Col/Spr | Notes |
|----------|----------|-----|-----|-----|---------|-------|---------|-------|
| Floor | Neo Geo Pocket | Z80 | 6.14 | 4KB | 64 | 8 | 8/pal | Handheld |
| Mid | MSX2 | Z80 | 3.58 | 64KB | 32 | 8 | 16 | V9938 VDP, 128KB VRAM |
| Peak | SMS | Z80 | 3.58 | 8KB | 64 | 8 | 16 | VDP same as MSX2 |

**MINIMAL_PLUS Design Direction**: SMS is the design peak. Better color than NES (16 vs 4 colors/sprite), Z80 vs 6502, but clearly below 16-bit league. This tier bridges 8-bit and 16-bit.

**Why SMS moved here**: SMS has 16 colors per sprite vs NES's 4. It's the "best 8-bit graphics" tier, visually closer to PC Engine than NES.

#### STANDARD Tier (16-bit)

| Position | Platform | CPU | MHz | RAM | Sprites | /Line | Colors | Notes |
|----------|----------|-----|-----|-----|---------|-------|--------|-------|
| Floor | PC Engine | 65C02 | 7.16 | 8KB | 64 | 16 | 482 | Fast 6502, great color |
| Mid | Genesis | 68000 | 7.67 | 64KB | 80 | 20 | 64 | Primary 68K target |
| High | Amiga OCS | 68000 | 7.09 | 512KB | 8 | 8 | 32 HAM | Blitter, copper |
| Peak | SNES | 65816 | 3.58 | 128KB | 128 | 32 | 256 | Mode 7, best color |

**STANDARD Design Direction**: SNES is the design peak for assets (256 colors, Mode 7). Genesis is the primary 68K target for logic. The NES↔Genesis mapping proves simultaneous 8-bit/16-bit development.

#### STANDARD_PLUS Tier (Enhanced 16-bit / Arcade)

| Position | Platform | CPU | MHz | RAM | Sprites | /Line | Colors | Notes |
|----------|----------|-----|-----|-----|---------|-------|--------|-------|
| Floor | 32X | 2×SH-2 | 23+23 | 256KB+ | + | + | 32K | Genesis addon |
| Mid | Sega CD | 68000×2 | 12.5+7.6 | 768KB | =Gen | =Gen | =Gen | Scaling, CD audio |
| High | X68000 | 68000 | 10 | 1-4MB | 128 | 32 | 65536 | Sharp's powerhouse |
| Peak | Neo Geo | 68000 | 12 | 64KB+ | 380 | 96 | 4096 | Arcade at home |

**STANDARD_PLUS Design Direction**: Neo Geo is the peak - 68000 @ 12MHz with massive sprite capability. Design logic for Neo Geo, reduce for Sega CD. Asset tier remains STANDARD (16-bit aesthetic).

#### EXTENDED Tier (32-bit Portables)

| Position | Platform | CPU | MHz | RAM | Sprites | /Line | Colors | Notes |
|----------|----------|-----|-----|-----|---------|-------|--------|-------|
| Floor | GBA | ARM7TDMI | 16.78 | 256KB | 128 | 128 | 32K | Mode 7-like rotation |
| Peak | DS | ARM9+ARM7 | 67+33 | 4MB | 128×2 | 128 | 262K | Dual screens, 3D |

**EXTENDED Design Direction**: DS is the peak. GBA is essentially "portable SNES+" - ARM7 provides desktop-class performance in portable form.

#### RETRO_PC Tier (VGA-era Reference Implementation)

| Position | Platform | CPU | MHz | RAM | Resolution | Colors | Notes |
|----------|----------|-----|-----|-----|------------|--------|-------|
| Floor | Atari ST | 68000 | 8 | 512KB | 320×200 | 16 | MIDI, GEM |
| Low | DOS Mode 13h | 386+ | 16+ | 640KB | 320×200 | 256 | Linear framebuffer |
| Mid | DOS Mode X | 386+ | 16+ | 640KB | 320×240 | 256 | Page flipping |
| High | Atari Falcon | 68030 | 16 | 4MB+ | 320×240+ | 256 | DSP |
| Peak | Amiga AGA | 68020+ | 14+ | 2MB+ | 320×256+ | 256 | Copper, blitter |
| Alt | PC-98 | V30/386 | 8+ | 640KB | 640×400 | 16/256 | Japan market |

**RETRO_PC Design Direction**: This is the **reference implementation tier** for modern faux-retro development. Design your game here first with generous limits (320×240@256 colors), then downsample to actual retro platforms. Amiga AGA serves as the peak.

**Key RETRO_PC characteristics**:
- 256 color indexed palette (8-bit)
- 320×200 or 320×240 resolution
- Software rendering (no hardware sprite limits on DOS)
- Generous RAM (640KB-4MB)
- Generous CPU (386 @ 16MHz+)

### Platform Tier Summary

| Platform | Asset Tier | Logic Tier | Position | Notes |
|----------|------------|------------|----------|-------|
| Atari 2600 | MINIMAL | MINIMAL | Floor | Extreme constraints |
| ZX Spectrum | MINIMAL | MINIMAL | Low | Attribute color |
| C64 | MINIMAL | MINIMAL | Mid | VIC-II, SID |
| NES | MINIMAL | MINIMAL | High | **Primary 6502 target** |
| Game Boy | MINIMAL | MINIMAL | Peak | |
| GBC | MINIMAL | MINIMAL | Peak+ | |
| Neo Geo Pocket | MINIMAL_PLUS | MINIMAL_PLUS | Floor | Handheld |
| MSX2 | MINIMAL_PLUS | MINIMAL_PLUS | Mid | V9938 VDP |
| SMS | MINIMAL_PLUS (Peak) | MINIMAL_PLUS (Peak) | Peak | 16 col/sprite |
| PC Engine | STANDARD | STANDARD | Floor | Fast 65C02 |
| Genesis | STANDARD | STANDARD | Mid | **Primary 68K target** |
| Amiga OCS | STANDARD | STANDARD | High | Blitter/copper |
| SNES | STANDARD (Peak) | STANDARD (Peak) | Peak | Mode 7, 256 colors |
| 32X | STANDARD | STANDARD_PLUS | Floor | Genesis addon |
| Sega CD | STANDARD | STANDARD_PLUS | Mid | Dual 68000 |
| X68000 | STANDARD_PLUS | STANDARD_PLUS | High | Sharp's 68K |
| Neo Geo | STANDARD | STANDARD_PLUS (Peak) | Peak | Arcade quality |
| GBA | EXTENDED | EXTENDED | Floor | Portable SNES+ |
| DS | EXTENDED (Peak) | EXTENDED (Peak) | Peak | Dual screens |
| Atari ST | RETRO_PC | RETRO_PC | Floor | 68000 @ 8MHz |
| DOS VGA | RETRO_PC | RETRO_PC | Mid | Mode 13h/X |
| Atari Falcon | RETRO_PC | RETRO_PC | High | 68030 + DSP |
| Amiga AGA | RETRO_PC (Peak) | RETRO_PC (Peak) | Peak | Reference impl |
| PC-98 | RETRO_PC | RETRO_PC | Alt | Japan market |

### Entity Limits by Logic Tier

| Limit | MINIMAL | MINIMAL_PLUS | STANDARD | STANDARD_PLUS | EXTENDED | RETRO_PC |
|-------|---------|--------------|----------|---------------|----------|----------|
| MAX_ENTITIES | 32 | 48 | 128 | 192 | 256 | 512 |
| MAX_ENEMIES | 12 | 16 | 48 | 72 | 96 | 128 |
| MAX_PROJECTILES | 16 | 24 | 48 | 72 | 96 | 128 |
| MAX_PICKUPS | 16 | 24 | 48 | 48 | 64 | 96 |
| MAX_EFFECTS | 8 | 12 | 24 | 32 | 48 | 64 |

### Memory Budgets by Logic Tier

| Budget | MINIMAL | MINIMAL_PLUS | STANDARD | STANDARD_PLUS | EXTENDED | RETRO_PC |
|--------|---------|--------------|----------|---------------|----------|----------|
| ENTITY_RAM_BUDGET | 512B | 768B | 2048B | 4096B | 8192B | 16384B |
| SCRATCH_RAM | 128B | 256B | 512B | 1024B | 2048B | 4096B |

### Performance Budgets by Logic Tier

| Budget | MINIMAL | MINIMAL_PLUS | STANDARD | STANDARD_PLUS | EXTENDED | RETRO_PC |
|--------|---------|--------------|----------|---------------|----------|----------|
| COLLISION_BUDGET | 64/frame | 96/frame | 256/frame | 384/frame | 512/frame | 1024/frame |
| UPDATE_BUDGET | 32/frame | 48/frame | 128/frame | 192/frame | 256/frame | 512/frame |

### AI Complexity by Logic Tier

| Feature | MINIMAL | MINIMAL_PLUS | STANDARD | STANDARD_PLUS | EXTENDED | RETRO_PC |
|---------|---------|--------------|----------|---------------|----------|----------|
| AI_PATHFIND | No | No | Basic | Full | Full | Full |
| AI_GROUP_BEHAVIOR | No | No | No | Yes | Yes | Yes |
| AI_PREDICTION | 0 frames | 2 frames | 4 frames | 6 frames | 8 frames | 16 frames |
| AI_UPDATE_SPLIT | 1/4/frame | 1/3/frame | 1/2/frame | 3/4/frame | All | All |

### Feature Flags by Logic Tier

| Feature | MINIMAL | MINIMAL_PLUS | STANDARD | STANDARD_PLUS | EXTENDED | RETRO_PC |
|---------|---------|--------------|----------|---------------|----------|----------|
| HAS_FAST_MULTIPLY | No | No | Yes | Yes | Yes | Yes |
| HAS_DIVIDE | No | No | Yes | Yes | Yes | Yes |
| USE_SPLIT_TABLES | Yes | Yes | No | No | No | No |
| FIXED_POINT_BITS | 8.8 | 8.8 | 8.8 | 12.12 | 16.16 | 16.16 |

### NES ↔ Genesis Mapping (Proof of Concept)

This is the core proof: simultaneous development for NES (MINIMAL) and Genesis (STANDARD).

| Aspect | NES (MINIMAL) | Genesis (STANDARD) | Mapping Strategy |
|--------|---------------|-------------------|------------------|
| Enemies | 12 max | 48 max | 4× scale factor |
| Projectiles | 16 max | 48 max | 3× scale factor |
| Collision checks | 64/frame | 256/frame | 4× scale factor |
| AI complexity | Chase only | + Pathfinding | Feature toggle |
| Fixed point | 8.8 | 8.8 | Same precision |
| Entity struct | 16 bytes | 16 bytes | Identical layout |

**The mapping works because**:
1. Entity structure is identical (16 bytes, same layout)
2. Fixed point precision matches (8.8 on both)
3. Logic scales linearly (4× enemies = 4× checks)
4. Only features are toggled (pathfinding on/off)

---

## Phase 0: Foundation ✅ COMPLETE

**Goal**: Establish core NES engine and development environment.

### Deliverables ✅
- [x] NES engine with MMC3 mapper
- [x] Player movement (32x32 sprite)
- [x] Enemy with auto-fire projectiles
- [x] Projectile system module
- [x] Basic game state machine
- [x] Build pipeline (compile.bat, ca65/ld65)

### Key Files Created
- `src/engine/init.asm` - Hardware initialization
- `src/engine/nmi.asm` - VBlank handler
- `src/engine/input.asm` - Controller reading
- `src/game/src/game_main.asm` - Main game loop
- `cfg/mmc3.cfg` - Linker configuration

---

## Phase 1: Asset Pipeline ✅ COMPLETE

**Goal**: Create robust, multi-platform sprite processing pipeline.

### Deliverables ✅
- [x] `unified_pipeline.py` v5.2 - 13+ platform support
- [x] AI sprite labeling (6 providers: Groq, Gemini, OpenAI, Anthropic, Grok, Pollinations)
- [x] Text label filtering (removes AI-generated text)
- [x] Platform-specific resampling (LANCZOS/NEAREST)
- [x] HAL tier integration (validates against entity limits)
- [x] Metadata JSON output

### Supported Platforms
| Platform | Tier | Colors | Format |
|----------|------|--------|--------|
| NES | MINIMAL | 4 | 2bpp CHR |
| Game Boy | MINIMAL | 4 | 2bpp |
| Game Boy Color | MINIMAL | 4/palette | 2bpp |
| Master System | MINIMAL | 16 | 4bpp planar |
| Genesis | STANDARD | 16 | 4bpp packed |
| SNES | STANDARD | 16 | 4bpp interleaved |
| PC Engine | STANDARD | 16 | 4bpp |
| Amiga OCS | STANDARD | 32 | 5 bitplanes |
| Amiga AGA | EXTENDED | 256 | 8 bitplanes |
| GBA | EXTENDED | 256 | 8bpp |
| C64 | MINIMAL | 4 | 2bpp sprite |
| CGA | MINIMAL | 4 | 2bpp |
| Atari 2600 | MINIMAL | 2 | 1bpp |

---

## Phase 2: Core Gameplay 🔄 IN PROGRESS

**Goal**: Implement vampire survivors gameplay loop.

### Phase 2.1: Enemy System 🔲
**Dependencies**: Phase 0
**Estimated Effort**: Medium

**Tasks**:
- [ ] Enemy data structure (x, y, hp, type, state)
- [ ] Enemy array in RAM ($0400-$04FF, 16 enemies max)
- [ ] Basic chase AI (move toward player)
- [ ] Enemy spawner (wave-based)
- [ ] Enemy death and removal
- [ ] Multiple enemy types from AI sprites

**Files to Modify**:
- `src/game/src/game_main.asm` - enemy update/render
- `src/engine/modules/action/spawner.asm` - spawning logic
- `src/game/assets/sprites.chr` - enemy tiles

**Acceptance Criteria**:
```
□ 16 enemies simultaneously on screen
□ Enemies chase player at varying speeds
□ Wave spawning with difficulty scaling
□ 10-minute play without crashes
```

---

### Phase 2.2: Collision System 🔲
**Dependencies**: Phase 2.1
**Estimated Effort**: Medium

**Tasks**:
- [ ] AABB collision detection routine
- [ ] Player-enemy collision → player takes damage
- [ ] Projectile-enemy collision → enemy takes damage
- [ ] Invincibility frames after hit
- [ ] Visual feedback (sprite flash)

**Files to Modify**:
- `src/game/src/game_main.asm` - collision checks
- `src/engine/collision.asm` (new, optional)

**Acceptance Criteria**:
```
□ Collision bounds visually correct
□ No integer overflow in position math
□ Death transitions work (enemy/player)
□ Kill 50 enemies without glitches
```

---

### Phase 2.3: XP & Leveling 🔲
**Dependencies**: Phase 2.2
**Estimated Effort**: Large

**Tasks**:
- [ ] XP gem drops from dead enemies
- [ ] XP collection (auto-pickup radius)
- [ ] XP counter (16-bit for large values)
- [ ] Level up trigger at XP thresholds
- [ ] Level up screen (pause game, show options)
- [ ] Weapon selection UI

**Files to Modify**:
- `src/engine/modules/action/powerup.asm` - XP gem logic
- `src/game/src/game_main.asm` - levelup state, UI

**Acceptance Criteria**:
```
□ 16-bit XP math (no overflow)
□ Clean state transitions (PLAYING ↔ LEVELUP)
□ Level up 10 times in single session
```

---

### Phase 2.4: Weapon Variety 🔲
**Dependencies**: Phase 2.3
**Estimated Effort**: Medium

**Tasks**:
- [ ] Weapon data structure (type, level, cooldown, damage)
- [ ] Weapon types: Laser (straight), Spread (3-way), Orbit (circular)
- [ ] Weapon upgrades (damage, speed, count)
- [ ] Visual variety (different projectile tiles)

**Files to Modify**:
- `src/game/src/game_main.asm` - weapon logic
- `src/engine/modules/action/projectile.asm` - behaviors

**Acceptance Criteria**:
```
□ All 3 weapon types functional
□ Max projectiles on screen without slowdown
□ Weapon upgrades visible in gameplay
```

---

## Phase 3: Polish & Content 🔲

**Goal**: Complete game experience with audio and visuals.

### Phase 3.1: Visual Polish 🔲
- [ ] Background tiles (from AI assets)
- [ ] Death animations
- [ ] Hit flash effects
- [ ] Screen shake (optional)

### Phase 3.2: Audio 🔲
- [ ] Background music (FamiTracker)
- [ ] Sound effects (shoot, hit, pickup, levelup)
- [ ] Audio engine integration

### Phase 3.3: Game Flow 🔲
- [ ] Title screen with START
- [ ] Game over screen
- [ ] Victory condition (survive X minutes or kill boss)
- [ ] High score (optional)

**Acceptance Criteria**:
```
□ Full playthrough: title → gameplay → end
□ Audio doesn't cause slowdown
□ ROM size within limits (128KB PRG, 128KB CHR)
```

---

## Phase 4: Multi-Platform 🔲

**Goal**: Port NEON SURVIVORS to second platform using HAL.

### Phase 4.1: HAL Completion 🔲
- [ ] Complete Genesis HAL implementation
- [ ] Test all HAL functions on NES
- [ ] Abstract remaining platform-specific code

### Phase 4.2: Genesis Port 🔲
- [ ] Build system for Genesis (SGDK)
- [ ] Asset conversion pipeline integration
- [ ] Genesis-specific optimizations

### Phase 4.3: Game Boy Port (Optional) 🔲
- [ ] Build system for Game Boy (RGBDS)
- [ ] Handle reduced sprite limits
- [ ] Monochrome palette adaptation

**Acceptance Criteria**:
```
□ Same game runs on NES and Genesis
□ Asset pipeline serves both platforms
□ Platform-specific optimizations documented
```

---

## Phase 5: Tool Distribution 🔲

**Goal**: Package and distribute ARDK tools.

### Phase 5.1: Sprite Pipeline Distribution 🔲
- [ ] Refactor as installable package
- [ ] Add comprehensive CLI help
- [ ] Write PyPI documentation
- [ ] Publish to PyPI as `ardk-sprites`

### Phase 5.2: Additional Tools 🔲
- [ ] Tilemap converter (Tiled/LDTK)
- [ ] Font generator
- [ ] ROM validator
- [ ] Audio converter

**Acceptance Criteria**:

```text
□ pip install ardk-sprites works
□ All tools have --help documentation
□ Examples in repository
```

---

## Phase 5.5: Build Validation System 🔲

**Goal**: Automated validation using platform manifest system.

### Phase 5.5.1: Compile-Time Validation 🔲

- [ ] Integrate manifest checks into build scripts
- [ ] Sprite size validation against `HAL_MANIFEST_SPRITE_SIZES`
- [ ] Entity count validation against tier limits
- [ ] Memory budget overflow detection

### Phase 5.5.2: Asset Validation 🔲

- [ ] Extend sprite pipeline with manifest awareness
- [ ] Validate CHR size against `HAL_MANIFEST_VRAM`
- [ ] Validate palette count against `HAL_MANIFEST_PALETTES`
- [ ] Warn when assets exceed platform capabilities

### Phase 5.5.3: CI/CD Pipeline 🔲

- [ ] GitHub Actions for multi-platform builds
- [ ] Automated ROM validation per platform
- [ ] Asset pipeline regression tests
- [ ] Emulator-based smoke tests

**Validation Macros Available**:

```c
// From platform_manifest.h
ARDK_VALIDATE_SPRITE_SIZE(w, h)   // Check sprite size support
ARDK_VALIDATE_SCROLL(mode)        // Check scroll capability
ARDK_VALIDATE_AUDIO(type)         // Check audio channel support
ARDK_HAS_RAM_GTE(bytes)           // Check RAM threshold
ARDK_HAS_SPR_LINE_GTE(n)          // Check sprites-per-line
```

**Acceptance Criteria**:

```text
□ Build fails on manifest violations
□ Asset pipeline warns on capability mismatches
□ CI builds all primary platforms on push
□ Emulator tests pass on all platforms
```

---

## Phase 6: Release 🔲

**Goal**: Public release of NEON SURVIVORS and ARDK.

### Phase 6.1: Testing 🔲
- [ ] Test on Mesen, FCEUX, Nestopia
- [ ] Test on real hardware (Everdrive/PowerPak)
- [ ] Edge cases (max enemies, max projectiles, max level)
- [ ] Long session test (1+ hour)

### Phase 6.2: Release Package 🔲
- [ ] Final ROM build
- [ ] README with controls
- [ ] Screenshots/GIFs
- [ ] ROM header verified

### Phase 6.3: Documentation 🔲
- [ ] Tutorial: "Your First ARDK Game"
- [ ] API reference (auto-generated)
- [ ] Platform comparison guide

**Acceptance Criteria**:
```
□ All documentation current
□ No debug code in release
□ Source code publicly available
```

---

## Cross-Phase Concerns

These apply throughout all phases:

### Documentation Standards
Every code change must follow [DOCUMENTATION_STANDARDS.md](docs/DOCUMENTATION_STANDARDS.md):
- File headers with @file, @brief, @platform
- Section banners (80 chars)
- Function doc comments (@brief, @param, @return)
- Assembly conventions (INPUT/OUTPUT/CLOBBERS)

### Hygiene Checkpoints
After every significant change:
```
□ Code compiles without warnings
□ ROM runs in emulator without crashes
□ No memory conflicts (check ZP allocation)
□ Documentation updated
□ Working build backed up
```

### Memory Budget Tracking
Monitor these limits:

**Zero Page ($00-$FF)**:
```
$00-$0F   Engine reserved
$10-$1F   Input system
$20-$2F   Player state
$30-$3F   Game state
$40-$4F   Action module
$50-$7F   Enemy temps (48 bytes)
$80-$9F   Weapon state (32 bytes)
$A0-$FF   Available (96 bytes)
```

**RAM Allocation**:
```
$0200-$02FF   OAM Shadow (reserved)
$0300-$03FF   Projectiles (16 × 16 bytes)
$0400-$04FF   Enemies (16 × 16 bytes)
$0500-$05FF   Powerups (32 × 8 bytes)
$0600-$07FF   Available (512 bytes)
```

---

## Quick Commands

```bash
# Build game
compile.bat

# Process sprites for NES
python tools/unified_pipeline.py sprite.png -o gfx/processed/

# Process for other platforms
python tools/unified_pipeline.py sprite.png -o out/ --platform gb
python tools/unified_pipeline.py sprite.png -o out/ --platform genesis

# Batch process
python tools/unified_pipeline.py --batch gfx/ai_output/ -o gfx/processed/

# Verify toolchains
python tools/verify_toolchains.py

# Generate API documentation
python tools/extract_docs.py --all

# Test ROM
start build/neon_survivors.nes
```

---

## Toolchain Requirements

### Primary (Install First)
| Tool | Platform | Command |
|------|----------|---------|
| cc65 | NES | `ca65 --version` |
| RGBDS | Game Boy | `rgbasm --version` |
| SGDK | Genesis | Set `GDK` env var |

### Secondary
| Tool | Platform | Command |
|------|----------|---------|
| PVSnesLib | SNES | `816-tcc --version` |
| devkitARM | GBA | `arm-none-eabi-gcc --version` |
| HuC | PC Engine | `huc --version` |

See [TOOLCHAIN_GUIDE.md](docs/TOOLCHAIN_GUIDE.md) for full installation instructions.

---

## Decision Log

Major architectural decisions and their rationale:

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-01-10 | Fixed-point 8.8 format | High byte = pixel, universal across platforms |
| 2026-01-10 | 16-byte entity structure | Power of 2 for fast indexing |
| 2026-01-10 | Tier system (MINIMAL/STANDARD/EXTENDED) | Allows scaling to platform capabilities |
| 2026-01-10 | AI sprite labeling with 6 providers | Redundancy, cost optimization |
| 2026-01-11 | Documentation as code | Auto-generation ensures consistency |
| 2026-01-11 | Platform manifest system | Compile-time validation, migration paths |
| 2026-01-11 | CPU family groupings | Shared assembly HAL per family (6502/Z80/68K) |
| 2026-01-11 | Primary vs migration targets | Focus on NES/Genesis/GB, port to others |
| 2026-01-11 | Dual-tier system (Asset/Logic) | Neo Geo has STANDARD sprites but enhanced logic |
| 2026-01-11 | "Design at peak, downsample" | Better quality than bottom-up additive approach |
| 2026-01-11 | Tier peaks: SMS/SNES/DS | Highest detail platforms per tier for design targets |
| 2026-01-11 | STANDARD_PLUS logic tier | Neo Geo & Sega CD: 16-bit aesthetics, enhanced 68K power |
| 2026-01-11 | MINIMAL_PLUS tier | SMS moved here (16 col/sprite vs NES's 4), bridges 8-bit and 16-bit |
| 2026-01-11 | RETRO_PC tier | VGA-era reference implementation for faux-retro modern dev |
| 2026-01-11 | Floor→Peak interpolation | Each tier has clear capability gradient for scaling |
| 2026-01-11 | NES↔Genesis mapping | Proof of concept for simultaneous 8-bit/16-bit development |
| 2026-01-11 | Added MSX2, NGP, X68000, DOS VGA, Atari ST/Falcon, PC-98 | Expanded homebrew platform support |

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| Memory overflow | High | Track ZP/RAM allocation, set MAX constants |
| Platform divergence | Medium | HAL abstracts differences, regular testing |
| Tool dependencies | Low | Document versions, use stable releases |
| Scope creep | Medium | Phase gates, acceptance criteria |

---

## Contributing

### Before Starting Work
1. Check this plan for current phase and priorities
2. Read [DOCUMENTATION_STANDARDS.md](docs/DOCUMENTATION_STANDARDS.md)
3. Run `python tools/verify_toolchains.py` to confirm setup
4. Identify which files you'll modify

### After Completing Work
1. Run hygiene checkpoint
2. Update this plan (check off completed items)
3. Update relevant documentation
4. Test in emulator

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-11 | Initial master plan consolidating all artifacts |
| 1.1 | 2026-01-11 | Added Platform Manifest System, Migration Strategy, HAL Tier details, Build Validation phase |
| 1.2 | 2026-01-11 | Dual-tier system (Asset/Logic), Neo Geo moved to EXTENDED logic, added C64/ZX/GB/PCE details |
| 1.3 | 2026-01-11 | Added STANDARD_PLUS logic tier for Neo Geo & Sega CD (enhanced 16-bit) |
| 1.4 | 2026-01-11 | Major tier restructuring: MINIMAL_PLUS (SMS/MSX2/NGP), RETRO_PC (VGA/ST/AGA), Floor→Peak interpolation, NES↔Genesis mapping proof |

---

*This is the source of truth for ARDK development. Keep it updated!*
