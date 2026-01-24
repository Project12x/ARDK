# ARDK Multi-Engine Architecture

This directory contains platform-specific engine implementations organized by CPU architecture family.

## Directory Structure

```
engines/
├── common/              Shared C code (compiles for all platforms)
├── 6502/                6502 CPU family (NES, C64, Atari, PCE)
│   ├── shared/          Shared 6502 assembly routines
│   └── nes/             NES-specific engine
├── 68k/                 68000 CPU family (Genesis, Neo Geo, Amiga)
│   ├── shared/          Shared 68K assembly routines
│   └── genesis/         Genesis-specific engine
├── z80/                 Z80 CPU family (SMS, Game Boy, MSX)
│   ├── shared/          Shared Z80 routines
│   ├── sms/             Master System engine
│   └── gb/              Game Boy engine
└── arm/                 ARM CPU family (GBA, DS)
    └── gba/             GBA engine
```

## Selecting an Engine

### Build Command Format
```bash
compile.bat <platform> <profile>

# Examples:
compile.bat nes STANDARD      # NES with balanced settings
compile.bat nes FAST          # NES optimized for speed
compile.bat genesis STANDARD  # Genesis (when available)
```

### Available Profiles

| Profile | Description | Use Case |
|---------|-------------|----------|
| **FAST** | Speed-optimized, fewer features | Action-heavy games, tight frame budgets |
| **STANDARD** | Balanced performance and features | Most games (recommended) |
| **FULL** | All features, maximum entities | Bullet hell, debug builds |

## Platform Status

| Platform | Family | Status | Toolchain |
|----------|--------|--------|-----------|
| NES | 6502 | **Ready** | cc65 |
| Genesis | 68k | Stub | SGDK |
| SMS | Z80 | Planned | devkitSMS |
| Game Boy | Z80 | Planned | GBDK |
| GBA | ARM | Planned | devkitARM |

## Adding a New Platform

1. Create directory: `engines/<family>/<platform>/`
2. Add ENGINE.md documenting the platform
3. Create init/, core/, hal_native/, profiles/ subdirectories
4. Implement HAL functions for the platform
5. Add to compile.bat platform selection

## Shared Code Philosophy

### CPU Family Shared (`<family>/shared/`)
Assembly routines shared across platforms with same CPU:
- Math routines (multiply, divide, sine tables)
- Entity iteration hot paths
- Fixed-point arithmetic

### Common C (`common/`)
Platform-agnostic C code that compiles everywhere:
- Entity manager (16-byte struct)
- State machine
- Collision detection (uses HAL math)

### Platform-Specific (`<family>/<platform>/`)
Code unique to each platform:
- Init/boot sequence
- Hardware register access
- Interrupt handlers
- Platform-specific optimizations

## Relationship to HAL

```
┌─────────────────────────────────────────────────┐
│                  Game Logic                      │
│              (game/src/*.c)                      │
├─────────────────────────────────────────────────┤
│                     HAL                          │
│    (src/hal/hal.h - platform-agnostic API)       │
├─────────────────────────────────────────────────┤
│                   Engine                         │
│    (engines/<family>/<platform>/ - this dir)     │
├─────────────────────────────────────────────────┤
│                  Hardware                        │
│         (actual NES/Genesis/etc.)                │
└─────────────────────────────────────────────────┘
```

The **HAL** defines WHAT operations are available (sprite, input, audio).
The **Engine** implements HOW those operations work on specific hardware.
