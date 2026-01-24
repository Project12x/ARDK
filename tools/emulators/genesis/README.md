# Genesis/Mega Drive Emulators

For future Genesis HAL tier development (HAL_TIER_STANDARD).

## Recommended: BlastEm

Download from: https://www.retrodev.com/blastem/

### Features
- Cycle-accurate emulation
- Headless mode support
- GDB remote debugging
- Command line scripting

### Command Line
```batch
# Run ROM
blastem.exe game.bin

# Headless mode
blastem.exe -h game.bin
```

## Alternative: Gens/GS

Download from: https://segaretro.org/Gens/GS

- Less accurate but more compatible
- Built-in Lua scripting

## Future Use

When ARDK expands to support Genesis/Mega Drive:
- HAL_TIER_STANDARD (SNES/Genesis capability level)
- Dual-plane scrolling
- 68000 + Z80 architecture
- FM synthesis audio (YM2612)

## Also Applicable

- Sega CD
- 32X (limited)
