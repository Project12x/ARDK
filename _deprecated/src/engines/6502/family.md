# 6502 CPU Family

The 6502 and its variants power many classic 8-bit systems. This family shares:
- 8-bit accumulator and index registers
- 256-byte zero page (fast access)
- 256-byte stack
- Little-endian byte order

## Platforms in This Family

| Platform | CPU | MHz | Notes |
|----------|-----|-----|-------|
| **NES** | 2A03 | 1.79 | Custom 6502 with APU, no decimal mode |
| Commodore 64 | 6510 | 1.02 | 6502 with I/O port |
| Atari 800/XL | 6502C | 1.79 | ANTIC/GTIA graphics |
| Apple II | 6502 | 1.02 | Original 6502 |
| PC Engine | HuC6280 | 7.16 | Enhanced 6502 with extra addressing |

## Shared Code (`shared/`)

Assembly routines that work across all 6502 platforms:

### math_8bit.asm
- 8x8 multiply (result in A:temp)
- 8-bit divide
- 256-byte sine/cosine tables

### fixed_point.asm
- 8.8 fixed-point add/subtract
- Fixed-point multiply (uses math_8bit)
- Conversion macros

### entity_6502.asm
- Entity iteration loop (optimized for 6502)
- Entity spawn/despawn
- Works with 16-byte entity struct

## 6502 Optimization Patterns

### Zero Page is Gold
```asm
; SLOW: Absolute addressing (4 cycles)
lda $0300

; FAST: Zero page addressing (3 cycles)
lda $30

; Reserve ZP for hot variables!
```

### Unrolling Pays Off
```asm
; Loop version: 8 + N*10 cycles
ldx #0
loop:
  lda table,x
  sta dest,x
  inx
  cpx #4
  bne loop

; Unrolled: 16 cycles (saves 26 cycles for 4 iterations!)
lda table+0
sta dest+0
lda table+1
sta dest+1
lda table+2
sta dest+2
lda table+3
sta dest+3
```

### Self-Modifying Code
```asm
; Update jump table entry at runtime
lda #<handler
sta jump_target+1
lda #>handler
sta jump_target+2

jump_target:
  jmp $0000       ; Modified at runtime
```

### Indexed Indirect for Entity Access
```asm
; Entity pointer in ZP
lda entity_ptr_lo
sta $00
lda entity_ptr_hi
sta $01

; Access entity fields via (zp),y
ldy #ENTITY_X
lda ($00),y       ; Load X position
```

## Memory Constraints

All 6502 platforms share tight memory:

| Resource | NES | C64 | Atari |
|----------|-----|-----|-------|
| RAM | 2KB | 64KB* | 48KB* |
| ZP Available | ~200 bytes | ~200 bytes | ~200 bytes |
| Stack | 256 bytes | 256 bytes | 256 bytes |

*C64/Atari have more RAM but share with display/ROM

## Cross-Platform Portability

Code written for NES can port to C64/Atari with:
1. **Different init sequence** (platform-specific boot)
2. **Different graphics API** (PPU vs VIC-II vs ANTIC)
3. **Different audio** (APU vs SID vs POKEY)
4. **Same game logic** (entity system, collision, AI)

The HAL abstracts these differences!
