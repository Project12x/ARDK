# Deprecated Code

This folder contains deprecated code from the original cross-platform ARDK (Agentic Retro Development Kit) project.

## Why Deprecated?

The original vision was to create a HAL (Hardware Abstraction Layer) that would allow writing game logic once and compiling for multiple retro platforms (NES, Genesis, Game Boy, etc.). However, agentic coding of 6502 assembly for NES proved unrealistic with current AI capabilities.

**Decision (2026-01-14)**: Focus solely on **Genesis/Mega Drive** development using **SGDK** (C-based), which is much more suitable for AI-assisted development.

## Contents

### `src/`
- `hal/` - Hardware Abstraction Layer (platform-agnostic API)
- `engines/` - Multi-platform engine implementations
  - `6502/nes/` - NES engine (6502 assembly)
  - `68k/genesis/` - Genesis engine stubs
  - `z80/gb/` - Game Boy engine stubs
  - `common/` - Shared C code
- `engine/` - Legacy NES engine
- `data/`, `mapper/`, `states/`, `game/` - NES game data

### `projects/`
- `hal_demo/` - HAL demonstration project (NES)
- `survivor_demo/` - NEON SURVIVORS NES demo
- `_template/` - NES project template

### `cfg/`
- NES linker configurations (mmc3.cfg, etc.)

### `docs/`
- NES-specific documentation (Mesen guides, debug checklists)

### Build Files
- `compile.bat` - NES build script
- Various debug and test scripts

## Potential Future Use

This code may be revived if:
1. Better AI tooling for 6502 assembly emerges
2. A C-based NES SDK becomes viable (cc65 improvements)
3. The Genesis port is complete and we want to backport

## Do Not Delete

Keep this folder for reference and potential future development.
