# mGBA - Game Boy Advance Emulator

For future GBA HAL tier development (HAL_TIER_EXTENDED).

## Installation

Download from: https://mgba.io/

## Features

- Headless mode support (`-P` flag)
- Lua scripting API
- GDB remote debugging
- Accurate emulation

## Command Line

```batch
# Run ROM
mgba.exe game.gba

# Headless with script
mgba.exe -P -s script.lua game.gba
```

## Future Use

When ARDK expands to support GBA:
- HAL_TIER_EXTENDED (GBA/DS capability level)
- Mode 3/4/5 bitmap modes
- Affine sprite transformations
- DMA-driven effects

## Also Supports

- Game Boy (DMG)
- Game Boy Color
- Super Game Boy
