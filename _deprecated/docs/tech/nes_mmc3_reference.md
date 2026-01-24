# NES MMC3 (Mapper 4) Technical Reference

*Current Verification Status: DRAFT / PENDING VERIFICATION*

## Overview

The MMC3 (Memory Management Controller 3) provides sophisticated bank switching and IRQ capabilities, essential for complex NES games.

### Feature Summary

- **PRG RAM**: 8KB at `$6000-$7FFF` (Optional battery backup).
- **PRG ROM**: 8KB swappable banks.
- **CHR ROM**: 1KB and 2KB swappable banks (Finely grained).
- **IRQ**: Scanline-based counter (Counting A12 toggles).

## Memory Map

| Address       | Function                          | Notes |
|---------------|-----------------------------------|-------|
| `$8000-$9FFF` | Bank Select & Data                | Even: Select, Odd: Data |
| `$A000-$BFFF` | Mirroring & PRG RAM Protect       | Even: Mirroring, Odd: RAM |
| `$C000-$DFFF` | IRQ Latch & Reload                | Even: Latch, Odd: Reload |
| `$E000-$FFFF` | IRQ Disable & Enable              | Even: Disable, Odd: Enable |

---

## Detailed Register Usage

### 1. Bank Select Register (`$8000`) - Write Even

```asm
7  bit  0
---- ----
CPxx xRRR
||    |||
||    +++- Register Number to update (0-7)
|+-------- PRG ROM bank mode (0: $8000 swappable, 1: $C000 swappable)
+--------- CHR A12 inversion (0: 2KB banks at $0000, 1: 2KB banks at $1000)
```

### 2. Bank Data Register (`$8001`) - Write Odd

Writes the Bank Index to the register selected by `$8000`.

**CHR Banks (1KB units, Index 0-255):**

- **R0 (`000`):** 2KB CHR (PPU $0000 or $1000) - Sends `N` and `N+1`.
- **R1 (`001`):** 2KB CHR (PPU $0800 or $1800) - Sends `N` and `N+1`.
- **R2 (`010`):** 1KB CHR (PPU $1000 or $0000)
- **R3 (`011`):** 1KB CHR (PPU $1400 or $0400)
- **R4 (`100`):** 1KB CHR (PPU $1800 or $0800)
- **R5 (`101`):** 1KB CHR (PPU $1C00 or $0C00)

**PRG Banks (8KB units, Index 0-63):**

- **R6 (`110`):** 8KB PRG at `$8000` (or `$C000` if Mode=1)
- **R7 (`111`):** 8KB PRG at `$A000`

---

## "Survivor-Style" High Entity Count Strategy

Handling 50+ entities on NES requires strictly managing the 64-sprite hardware limit and VRAM bandwidth.

### 1. The 64-Sprite Limit (OAM Cycling)

The NES PPU can only render 64 sprites total, and 8 per scanline.
**Technique:** Flicker / Multiplexing.

- Every frame, randomize or cycle the order of sprites in the OAM buffer.
- `Frame N`: Draw Sprites 0-63.
- `Frame N+1`: Draw Sprites 63-0 (or shuffle).
- Results in 30fps "ghosting" for low-priority entities when overloaded, but prevents total invisibility.

### 2. VRAM Banking for Variety

You cannot fit animations for 10 different enemy types in 4KB of Sprite pattern table.
**Technique:** Mid-Frame Bank Switching (Advanced) or Checkerboarding.

- **Standard**: Allocate specific 1KB banks (R2-R5) for "Enemy Slots".
  - `CHR_BANK_A` ($1000-$13FF): Skeleton
  - `CHR_BANK_B` ($1400-$17FF): Bat
  - `CHR_BANK_C` ($1800-$1BFF): Boss Head
- **Dynamic**: If you spawn a "Goblin", replace `CHR_BANK_A` with the Goblin Bank. All "Skeleton" instances must despawn or flicker away.

### 3. Metasprite Optimization (The "16x16" Rule)

Don't use 24x24 or 32x32 sprites for fodder enemies.

- 16x16 = 4 HW sprites. 64 / 4 = 16 Enemies max (w/o flicker).
- 8x8 = 1 HW sprite. 64 / 1 = 64 Enemies max.
- **Survivors Target**: Use 16x16 for elites/player, 8x16 or 8x8 for swarmers.

### 4. Code Example: Dynamic Bank Loading

```asm
; Input: A = Enemy Type ID (translates to Bank #)
; Input: X = CHR Slot (0-3, mapping to R2-R5)
load_enemy_graphics:
    pha
    
    ; Select Register (2 + X)
    txa
    clc
    adc #2              ; R2 start index
    sta MMC3_BANK_SELECT
    
    pla                 ; Restore Bank #
    sta MMC3_BANK_DATA  ; Swap instantly!
    rts
```

---

## Pipeline Implications

To support this, the asset pipeline MUST:

1. **Enforce Size**: Resize assets to 16x16 (or 8x8) to maximize density.
2. **Limit Colors**: 3 colors + Transparent per palette.
3. **Bank Alignment**: Output 1KB (64 tile) or 2KB (128 tile) chunks for easy swapping.
