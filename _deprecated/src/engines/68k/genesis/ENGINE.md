# Genesis/Mega Drive Engine (68000)

> **CPU**: Motorola 68000 (7.67MHz NTSC)
> **Co-processor**: Z80 (3.58MHz) for audio
> **RAM**: 64KB main + 8KB Z80 + 64KB VRAM
> **Tier**: STANDARD (HAL_TIER_STANDARD)

## Quick Reference

| Resource | Limit | Notes |
|----------|-------|-------|
| Sprites | 80 total, 20/scanline | 320 sprite tiles in VRAM |
| Sprite sizes | 8x8 to 32x32 | Multiple sizes per sprite |
| BG planes | 2 (A and B) | Independent scroll |
| Colors | 16 per palette, 4 palettes | 61 unique colors on screen |
| Resolution | 320x224 or 256x224 | H40 or H32 mode |
| VRAM | 64KB | Shared BG/sprites |

## Directory Structure

```
genesis/
├── ENGINE.md           This file
├── init/               Boot sequence
│   ├── header.asm      ROM header (SEGA string, vectors)
│   └── entry.c         Initialization
├── core/               Core systems
│   ├── vdp.c           VDP control
│   ├── dma_queue.c     DMA queue for VRAM updates
│   └── entity.c        Entity management (can use common/)
├── hal_native/         Hardware interface
│   ├── input.c         6-button controller
│   ├── audio_z80.c     Z80 driver communication
│   └── audio_ym2612.c  FM synthesis
└── profiles/           Build profiles
    ├── FAST.inc
    ├── STANDARD.inc
    └── FULL.inc
```

## Memory Map

### 68000 Address Space
```
$000000-$3FFFFF   ROM (up to 4MB)
$400000-$7FFFFF   Reserved (Sega CD, 32X)
$A00000-$A0FFFF   Z80 address space
$A10000-$A1001F   I/O ports (controllers, etc.)
$C00000-$C0001F   VDP ports
$E00000-$FFFFFF   68000 RAM (64KB, mirrored)
```

### RAM Layout ($FF0000-$FFFFFF)
```
$FF0000-$FF0FFF   Stack (4KB)
$FF1000-$FF1FFF   Entity data (4KB = 256 entities)
$FF2000-$FF2FFF   Game state (4KB)
$FF3000-$FFFFFF   Available (~52KB)
```

## VDP Architecture

### Planes
- **Plane A**: Foreground, full scroll
- **Plane B**: Background, full scroll
- **Window**: Fixed position overlay
- **Sprites**: 80 hardware sprites

### VRAM Layout (64KB)
```
$0000-$9FFF   Plane A tiles (40KB)
$A000-$AFFF   Plane B tiles (4KB)
$B000-$B7FF   Sprite tiles (2KB for 64 sprites)
$B800-$BFFF   Window tiles (2KB)
$C000-$CFFF   Plane A nametable (4KB)
$D000-$DFFF   Plane B nametable (4KB)
$E000-$E7FF   Window nametable (2KB)
$F000-$F27F   Sprite attribute table (640 bytes)
$F800-$FFFF   H-scroll table (optional)
```

## Build Profiles

### FAST Profile
- **Entities**: 128 max (32 enemies)
- **DMA Budget**: 50% (less VRAM updates)
- **Features**: Single scroll plane
- **Use case**: Fast action, many sprites

### STANDARD Profile (Default)
- **Entities**: 192 max (48 enemies)
- **DMA Budget**: 75%
- **Features**: Dual planes, line scroll
- **Use case**: Most games

### FULL Profile
- **Entities**: 256 max (64 enemies)
- **DMA Budget**: 100%
- **Features**: All VDP features
- **Use case**: Technical showcases

## Genesis vs NES Scaling

| Aspect | NES | Genesis | Scale Factor |
|--------|-----|---------|--------------|
| CPU Speed | 1.79 MHz | 7.67 MHz | 4.3x |
| RAM | 2KB | 64KB | 32x |
| Sprites | 64 (8/line) | 80 (20/line) | 1.25x/2.5x |
| Colors | 25 | 61 | 2.4x |
| Entity Budget | 48 | 192 | 4x |

## SGDK Integration

This engine uses [SGDK](https://github.com/Stephane-D/SGDK) for:
- C compiler (GCC 68K)
- Library functions
- Resource management

### Building
```bash
# Requires SGDK installed
%GDK%\bin\make -f %GDK%\makefile.gen
```

## Toolchain Requirements

- **SGDK**: Genesis Development Kit
- **GCC**: m68k-elf-gcc (included in SGDK)
- **Assembler**: GNU AS (68K)

## Status

**Current**: Stub implementation
**Next Steps**:
1. Implement VDP initialization
2. Basic sprite rendering
3. Controller input
4. Connect to HAL

## Related Documentation

- [68K Family](../family.md)
- [HAL Reference](../../../hal/hal.h)
- [HAL Genesis Config](../../../hal/genesis/hal_config.h)
