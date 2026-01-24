# Cross-Platform Retro Game Engine Research

> **Date**: 2026-01-10
> **Purpose**: Research existing tools, engines, and approaches for cross-platform retro game development
> **Goal**: Inform the design of the Agentic Retro Development Kit (ARDK)

---

## Executive Summary

After researching the current landscape, **no existing tool provides a true cross-platform HAL** for developing games that run natively on multiple retro consoles (NES + Genesis + SNES etc.) from a single codebase. The closest approaches are:

1. **Platform-specific SDKs** (cc65, SGDK, devkitPro) - excellent but isolated
2. **Emulator-based abstraction** (libretro/Lutro) - modern runtime, not native ROMs
3. **Visual tools** (NESmaker, Retro Game Builder) - limited to single platform

This represents a **significant opportunity** for ARDK to fill a gap in the ecosystem.

---

## Existing Tools by Platform

### NES / Famicom (6502)

| Tool | Type | Language | Notes |
|------|------|----------|-------|
| **[cc65](https://cc65.github.io/)** | Compiler/Toolchain | C/ASM | Industry standard, excellent docs |
| **[NESmaker](https://www.thenew8bitheroes.com/)** | Visual IDE | GUI/ASM | No-code option, commercial |
| **[NESDEV Wiki](https://www.nesdev.org/)** | Community | - | Best resource for NES hardware |
| **[8bitworkshop](https://8bitworkshop.com/)** | Browser IDE | C/ASM | Instant feedback, great for learning |
| **vbcc** | Compiler | C | Better optimization than cc65, weird license |

**Key Insight**: cc65 is mature but generates mediocre code. vbcc produces 2-3x faster code but has licensing concerns.

### Sega Genesis / Mega Drive (68000)

| Tool | Type | Language | Notes |
|------|------|----------|-------|
| **[SGDK](https://github.com/Stephane-D/SGDK)** | Full SDK | C | De facto standard, excellent |
| **[Echo](https://github.com/sikthehedgehog/Echo)** | Sound Engine | ASM | Most popular audio driver |
| **SecondBasic** | Compiler | BASIC | Beginner-friendly |
| **Java Grinder** | Compiler | Java | Experimental |

**Key Insight**: SGDK is remarkably polished. The 68000's register-based architecture maps well to C, making it easier to get good performance from compiled code vs. 6502.

### SNES / Super Famicom (65816)

| Tool | Type | Language | Notes |
|------|------|----------|-------|
| **[PVSnesLib](https://github.com/alekmaul/pvsneslib)** | SDK | C/ASM | Most complete C option |
| **[libSFX](https://github.com/Optiroc/libSFX)** | Framework | ASM | ca65-based, powerful macros |
| **cc65 (ca65)** | Assembler | ASM | Supports 65816, no C compiler |
| **Calypsi** | Compiler | C | Commercial, best 65816 C support |

**Key Insight**: SNES C development is harder than Genesis. The 65816 mode switching and variable register widths make it less compiler-friendly.

### Game Boy / Game Boy Color (Z80-like)

| Tool | Type | Language | Notes |
|------|------|----------|-------|
| **[RGBDS](https://rgbds.gbdev.io/)** | Toolchain | ASM | Standard assembler |
| **[GBDK-2020](https://github.com/gbdk-2020/gbdk-2020)** | SDK | C | Active fork, very capable |
| **[hUGETracker](https://github.com/SuperDisk/hUGETracker)** | Audio | Tracker | Best GB music tool |

**Key Insight**: GBDK-2020 is excellent and actively maintained. GB development has matured significantly.

### Game Boy Advance (ARM7)

| Tool | Type | Language | Notes |
|------|------|----------|-------|
| **[devkitPro/devkitARM](https://devkitpro.org/)** | Toolchain | C/C++ | Standard choice |
| **[libtonc](https://gbadev.net/tonc/)** | Library | C | Best documentation |
| **[Butano](https://gvaliente.github.io/butano/)** | Engine | C++ | High-level, modern C++ |
| **[maxmod](https://maxmod.devkitpro.org/)** | Audio | C | MOD/XM playback |

**Key Insight**: Butano is impressive - a full C++ engine with ECS, tilemaps, sprites, audio. Shows what's possible with modern tooling on retro hardware.

---

## Cross-Platform Approaches

### 1. Libretro (Runtime Abstraction)

**[Libretro](https://www.libretro.com/)** provides a cross-platform API for game cores:

```
┌─────────────────────────────────────────────────────┐
│              Your Game (libretro core)              │
├─────────────────────────────────────────────────────┤
│                   libretro API                       │
├───────┬───────┬───────┬───────┬───────┬────────────┤
│Windows│ Linux │ macOS │Android│  iOS  │   Web      │
│       │       │       │       │       │ (WASM)     │
└───────┴───────┴───────┴───────┴───────┴────────────┘
```

**Pros**:
- Write once, run everywhere
- Handles video/audio/input abstraction
- Huge existing frontend ecosystem (RetroArch)

**Cons**:
- Output is NOT a native ROM - requires emulator/frontend
- Can't target actual hardware
- Not suitable for "authentic" homebrew releases

**Lutro** specifically targets retro-style game development on libretro using Lua.

### 2. Write for Emulators

A pragmatic approach: write your game as an actual NES/Genesis ROM, then distribute for emulators.

**Pros**:
- True native ROMs
- Works on flashcarts/real hardware
- Authentic experience

**Cons**:
- Still single-platform per codebase
- No code sharing between platforms

### 3. The Missing Piece: Native Cross-Platform HAL

**Nobody has built this yet**:

```
┌─────────────────────────────────────────────────────┐
│              Game Logic (Platform-Agnostic)         │
│         Movement, AI, State Machines, etc.          │
├─────────────────────────────────────────────────────┤
│          Hardware Abstraction Layer (HAL)            │
│  draw_sprite(), play_sfx(), get_buttons(), etc.     │
├───────────┬───────────┬───────────┬─────────────────┤
│    NES    │  Genesis  │   SNES    │      GBA        │
│   6502    │   68000   │   65816   │     ARM7        │
│    PPU    │    VDP    │    PPU    │     LCD         │
└───────────┴───────────┴───────────┴─────────────────┘
```

**This is what ARDK should become.**

---

## Compiler Performance Comparison

From [6502 Compiler Benchmark](https://sgadrat.itch.io/super-tilt-bro/devlog/219534/benchmark-c-compilers-for-the-6502-cpu):

| Compiler | Relative Performance | Notes |
|----------|---------------------|-------|
| vbcc | 100% (baseline) | Best optimization |
| 6502-gcc | ~60% | Experimental |
| cc65 | ~37% | Most stable/supported |

**For 68000**: GCC produces good code. SGDK uses m68k-elf-gcc.

**For ARM**: GCC is excellent. devkitARM is industry standard.

---

## Audio Middleware

| Platform | Recommended Driver | Format |
|----------|-------------------|--------|
| NES | FamiTone2, Famistudio | FTM |
| Genesis | Echo, XGM | VGM, DefleMask |
| SNES | N-SPC | BRR samples |
| Game Boy | hUGEDriver | UGE |
| GBA | maxmod | MOD, XM, IT |

**Cross-platform tracker**: [Furnace](https://github.com/tildearrow/furnace) supports 50+ sound chips including all major retro platforms.

---

## ARDK Design Recommendations

Based on this research:

### 1. Start with Dual-Target: NES + Genesis

- **NES (6502)**: Constrained, teaches efficiency
- **Genesis (68000)**: More headroom, good C support
- Different enough to prove the HAL works

### 2. Use Existing Toolchains

Don't reinvent the wheel:
- **NES**: cc65 (or vbcc if we can work around licensing)
- **Genesis**: SGDK's m68k-elf-gcc
- **GBA**: devkitARM
- **SNES**: ca65 + custom tooling (C is problematic)

### 3. HAL Interface Design

```c
// hal.h - Platform-agnostic interface

// Video
void hal_sprite_show(u8 id, i16 x, i16 y, u8 tile, u8 attr);
void hal_sprite_hide(u8 id);
void hal_bg_tile_set(u8 x, u8 y, u8 tile);
void hal_palette_set(u8 index, u8 r, u8 g, u8 b);

// Audio
void hal_sfx_play(u8 id);
void hal_music_play(u8 id);
void hal_music_stop(void);

// Input
u16 hal_input_read(u8 port);
#define BTN_A      0x01
#define BTN_B      0x02
#define BTN_START  0x04
// ...etc

// System
void hal_wait_vblank(void);
u16  hal_get_frame_count(void);
```

### 4. Asset Pipeline Integration

Our sprite pipeline becomes one component:

```
┌────────────────────────────────────────────────────────────┐
│                    ARDK Asset Pipeline                      │
├──────────────┬──────────────┬──────────────┬───────────────┤
│   Sprites    │    Music     │   Tilemaps   │    Fonts      │
│ (existing!)  │  (Furnace)   │   (Tiled)    │  (custom)     │
├──────────────┴──────────────┴──────────────┴───────────────┤
│              Unified Metadata Format (JSON)                 │
├────────────────────────────────────────────────────────────┤
│           Platform-Specific Output Generators               │
└────────────────────────────────────────────────────────────┘
```

### 5. AI Agent Integration Points

```
┌─────────────────────────────────────────────────────────────┐
│                      AI Agent Layer                          │
├─────────────┬─────────────┬─────────────┬──────────────────┤
│   Sprite    │    Code     │   Music     │      Test        │
│   Agent     │   Agent     │   Agent     │     Agent        │
│             │             │             │                  │
│ Generate    │ Generate    │ Generate    │ Automated        │
│ sprites     │ HAL calls   │ chip music  │ ROM testing      │
│ from        │ from game   │ from MIDI   │ in emulators     │
│ prompts     │ logic desc  │ or humming  │                  │
└─────────────┴─────────────┴─────────────┴──────────────────┘
```

---

## Competitive Analysis

| Project | Scope | Our Advantage |
|---------|-------|---------------|
| NESmaker | NES only, visual | We target multiple platforms + code |
| SGDK | Genesis only | We add NES, SNES, GBA |
| libretro | Modern runtime | We produce native ROMs |
| Butano | GBA only, C++ | We're multi-platform |
| cc65/RGBDS | Tools, not engine | We provide full engine + HAL |

**ARDK's unique value**: Native multi-platform ROMs from shared game logic, with AI-assisted development.

---

## Next Steps

1. **Define HAL Interface** (hal.h) - start simple, 10-15 functions
2. **Implement NES HAL** - prove the concept works
3. **Implement Genesis HAL** - validate cross-platform design
4. **Create Sample Game** - simple action game that builds for both
5. **Expand Asset Pipeline** - add audio, tilemaps
6. **Add More Platforms** - SNES, GBA, Game Boy

---

## Sources

- [SGDK - Sega Genesis Development Kit](https://github.com/Stephane-D/SGDK)
- [cc65 - 6502 C Compiler](https://cc65.github.io/)
- [devkitPro](https://devkitpro.org/)
- [Libretro API Documentation](https://docs.libretro.com/development/cores/developing-cores/)
- [NESDEV Wiki](https://www.nesdev.org/)
- [GBADev.net - Tonc Tutorial](https://gbadev.net/tonc/)
- [6502 Compiler Benchmark](https://sgadrat.itch.io/super-tilt-bro/devlog/219534/benchmark-c-compilers-for-the-6502-cpu)
- [Butano - GBA C++ Engine](https://gvaliente.github.io/butano/)
- [Lutro - Retro Game Engine](https://lutro.libretro.com/)
- [8bitworkshop](https://8bitworkshop.com/)
- [PVSnesLib](https://github.com/alekmaul/pvsneslib)

---

*This research informs the ARDK project direction. Update as landscape evolves.*
