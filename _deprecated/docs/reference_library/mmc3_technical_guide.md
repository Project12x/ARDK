# NES MMC3 (Mapper 4) Technical Guide

## 1. Overview

The MMC3 (Memory Management Controller 3) is the most popular NES mapper, used in titles like *Super Mario Bros. 3*, *Mega Man 3-6*, and *Kirby's Adventure*. It enables complex logic, split-screen scrolling, and fine-grained graphics swapping.

## 2. Memory Map & Registers

### Bank Select ($8000 - Even)

Controls which bank register ($8001) is being updated.

```
7  bit  0
C P x x x R R R
| |       | | |
| |       +-+-+-- Register Number (0-7)
| +-------------- PRG ROM Mode (0: $8000 fixed, 1: $C000 fixed)
+---------------- CHR A12 Inversion (0: Standard, 1: Inverted)
```

### Bank Data ($8001 - Odd)

Writes the bank index to the selected register.

- **R0, R1**: 2KB CHR Banks (Indexes 0-255).
- **R2, R3, R4, R5**: 1KB CHR Banks.
- **R6, R7**: 8KB PRG ROM Banks.

### Mirroring ($A000 - Even)

- `0`: Vertical Mirroring (Side-scrolling)
- `1`: Horizontal Mirroring (Vertical scrolling)

### IRQ Latch ($C000 - Even)

Specifies the target scanline counter value.

### IRQ Reload ($C001 - Odd)

Forces the IRQ counter to reload from the latch on the next A12 edge.

### IRQ Enable/Disable ($E000/$E001)

- **$E000**: Disable IRQs.
- **$E001**: Enable IRQs.

## 3. The Scanline IRQ

The MMC3 counts scanlines by monitoring the PPU Address line A12.

- **Requirement**: The PPU must fetch generic patterns from the left pattern table ($0000) and sprite patterns from the right ($1000) - or vice versa - to toggle A12 reliably.
- **Trick**: If you use 8x16 sprites, the PPU fetches from both tables automatically, making the IRQ counter extremely stable.
- **Usage**: Used for split screens (status bars at the bottom) or parallax effects (changing scroll mid-screen).

## 4. Banking Strategies

### 2KB vs 1KB CHR

- **R0/R1 (2KB)**: Best for Backgrounds or large animation sets.
- **R2-R5 (1KB)**: Best for Sprites. You can swap individual enemy types or efficient animation frames.

### Example: "Kirby" Style

- **Backgrounds**: Uses R0/R1 for the level tileset.
- **Kirby**: Uses R2 for his base animations.
- **Enemies**: Uses R3, R4, R5 for dynamic enemy loading. When a "Waddle Dee" appears, bank R3 is set to "Waddle Dee Graphics". If a "Bronto Burt" appears, R3 switches to "Bronto Burt".
