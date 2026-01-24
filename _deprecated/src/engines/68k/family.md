# 68000 CPU Family

The Motorola 68000 powers the most capable 16-bit systems. This family shares:
- 32-bit internal architecture (16-bit data bus)
- 8 data registers (D0-D7), 8 address registers (A0-A7)
- Linear 24-bit address space (16MB)
- Big-endian byte order

## Platforms in This Family

| Platform | CPU | MHz | Notes |
|----------|-----|-----|-------|
| **Genesis** | 68000 | 7.67 | Z80 coprocessor for audio |
| Neo Geo | 68000 | 12 | Massive sprite system |
| Amiga 500 | 68000 | 7.14 | Blitter, copper, 4-channel audio |
| Amiga 1200 | 68020 | 14 | Enhanced 68K with cache |
| X68000 | 68000 | 10 | Japanese computer, arcade-quality |
| Atari ST | 68000 | 8 | YM2149 audio, GEM OS |

## Shared Code (`shared/`)

Assembly and C routines that work across all 68K platforms:

### math_16bit.asm
- 16x16 multiply (native MULU)
- 32/16 divide (native DIVU)
- Trigonometry tables (can be larger than 6502)

### entity_68k.asm
- Entity iteration (optimized for 68K)
- Uses address registers for pointer walks
- Leverages MOVEM for batch register saves

### fixed_point.c
- 16.16 fixed-point (more precision than 6502)
- Fast multiply using MULS
- Can be C since 68K handles it well

## 68000 Optimization Patterns

### Use Address Registers for Pointers
```asm
; Load entity pointer into A0
movea.l entity_ptr, a0

; Access fields via offset
move.w  ENTITY_X(a0), d0    ; Load X
move.w  ENTITY_Y(a0), d1    ; Load Y
```

### MOVEM for Batch Operations
```asm
; Save multiple registers (one instruction!)
movem.l d0-d7/a0-a6, -(sp)

; Process...

; Restore all registers
movem.l (sp)+, d0-d7/a0-a6
```

### DBcc for Loops
```asm
; Process 100 entities
move.w  #99, d7             ; Counter (N-1)
loop:
    ; Process entity at (a0)
    add.l   #ENTITY_SIZE, a0
    dbra    d7, loop        ; Decrement and branch
```

### Use WORD Operations When Possible
```asm
; LONG operation: 8+ cycles
move.l  d0, d1

; WORD operation: 4 cycles
move.w  d0, d1

; 68K penalizes long operations on 16-bit bus
```

## Memory Architecture

68K platforms generally have much more RAM:

| Resource | Genesis | Neo Geo | Amiga |
|----------|---------|---------|-------|
| Main RAM | 64KB | 64KB | 512KB+ |
| VRAM | 64KB | 64KB* | Shared |
| Sprite capacity | 80 | 384 | Variable |

*Neo Geo has separate sprite/fix layer memory

## Cross-Platform Portability

Code written for Genesis can port to Neo Geo/Amiga with:
1. **Different graphics system** (VDP vs sprite system vs blitter)
2. **Different audio** (YM2612+PSG vs YM2610 vs Paula)
3. **Same game logic** (entity system, AI)
4. **Similar performance** (all 68K ~7-12MHz)

The HAL abstracts these differences!

## C vs Assembly

68K is more C-friendly than 6502:
- **Use C for**: Game logic, state machines, AI
- **Use ASM for**: VDP/DMA operations, audio drivers, tight loops

Most Genesis games use ~80% C, ~20% ASM for hot paths.
