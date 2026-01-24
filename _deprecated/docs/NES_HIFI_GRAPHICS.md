# NES High-Fidelity Graphics Techniques

> **Reference**: Sunsoft's Batman: Return of the Joker (1991)
> **Goal**: Push NES graphics to pseudo-16-bit quality
> **Cross-Platform Impact**: Techniques that can be abstracted to Genesis/SNES

---

## Overview

Batman: Return of the Joker represents the peak of NES graphics programming. The techniques used can be categorized into:

1. **CHR-ROM Bank Switching** - Animated backgrounds without CPU cost
2. **Scanline IRQ Parallax** - Multiple scroll layers
3. **Strategic Sprite Budgeting** - Quality over quantity
4. **Dithered Pre-rendered Art** - More perceived colors
5. **Audio Exploitation** - Bass-heavy soundtrack (Sunsoft bass)

---

## 1. CHR-ROM Bank Switching

### How It Works

The NES PPU can display 256 background tiles and 256 sprite tiles at once (from CHR-ROM). MMC3 allows swapping 1KB or 2KB CHR banks during rendering.

**Batman's Approach**:
- Store 8+ sets of animated tiles in CHR-ROM
- Swap banks every few frames for animation
- Swap mid-frame via IRQ for different tile sets per screen region

### Implementation

```asm
; CHR bank animation timer (in zero page)
.segment "ZEROPAGE"
chr_anim_timer:  .res 1    ; Counts frames
chr_anim_frame:  .res 1    ; Current animation frame (0-7)

; In NMI handler - animate CHR every 8 frames
.proc update_chr_animation
    ; Increment timer
    inc chr_anim_timer
    lda chr_anim_timer
    and #$07              ; Every 8 frames
    bne @done

    ; Advance animation frame
    inc chr_anim_frame
    lda chr_anim_frame
    and #$03              ; 4 frames of animation
    sta chr_anim_frame

    ; Calculate CHR bank: base_bank + (anim_frame * 2)
    ; For 2KB banks, multiply by 2
    asl a
    clc
    adc #CHR_BANK_WATER_BASE  ; e.g., bank 8

    ; Swap background CHR bank
    ldx #$00              ; MMC3 register 0 (2KB CHR at $0000)
    stx $8000
    sta $8001             ; Set new bank

@done:
    rts
.endproc
```

### CHR-ROM Organization for Animation

```
; 32KB CHR-ROM layout (4 x 8KB banks)
;
; Bank 0 (8KB): Static sprites
;   $00-$0F: Player frames
;   $10-$1F: Enemy type 1
;   $20-$2F: Enemy type 2
;   $30-$3F: Projectiles/items
;   $40-$7F: More sprites
;   $80-$FF: Static background
;
; Bank 1 (8KB): Animated BG frame 0
;   $00-$7F: Background tiles (water/clouds frame 0)
;   $80-$FF: Background tiles (parallax layer)
;
; Bank 2 (8KB): Animated BG frame 1
;   ... water/clouds frame 1
;
; Bank 3 (8KB): Animated BG frame 2
;   ... water/clouds frame 2
```

---

## 2. Scanline IRQ Parallax

### The Technique

MMC3's scanline counter triggers an IRQ at a specific screen line. By changing scroll registers and CHR banks in the IRQ, you create multiple parallax layers.

### Implementation

```asm
; Parallax layer configuration
.segment "ZEROPAGE"
parallax_count:     .res 1    ; Number of active layers (1-3)
irq_next_layer:     .res 1    ; Which layer IRQ should set up next

; Layer data in RAM (3 layers max for NES)
.segment "BSS"
parallax_layers:              ; Array of layer structs
    ; Layer 0 (top - sky)
    parallax0_scanline:  .res 1
    parallax0_scroll_x:  .res 2   ; 8.8 fixed point
    parallax0_scroll_y:  .res 1
    parallax0_chr_bank:  .res 1
    parallax0_speed:     .res 1   ; 0-255, 128=50%, 255=100%

    ; Layer 1 (middle - mountains)
    parallax1_scanline:  .res 1
    parallax1_scroll_x:  .res 2
    parallax1_scroll_y:  .res 1
    parallax1_chr_bank:  .res 1
    parallax1_speed:     .res 1

    ; Layer 2 (bottom - ground, 100% speed)
    parallax2_scanline:  .res 1
    parallax2_scroll_x:  .res 2
    parallax2_scroll_y:  .res 1
    parallax2_chr_bank:  .res 1
    parallax2_speed:     .res 1

; IRQ handler for parallax
.proc irq_parallax
    pha
    txa
    pha
    tya
    pha

    ; Acknowledge MMC3 IRQ
    sta $E000             ; Disable IRQ
    sta $E001             ; Enable IRQ (re-arm)

    ; Get current layer index
    ldx irq_next_layer

    ; Set scroll based on layer
    cpx #0
    beq @layer0
    cpx #1
    beq @layer1
    jmp @layer2

@layer0:
    ; Set scroll for sky layer
    lda parallax0_scroll_x
    sta $2005             ; X scroll (low byte, pixel position)
    lda parallax0_scroll_y
    sta $2005             ; Y scroll

    ; Set CHR bank for this layer
    lda #$00
    sta $8000
    lda parallax0_chr_bank
    sta $8001

    ; Setup next IRQ for layer 1
    lda parallax1_scanline
    sta $C000             ; IRQ latch
    sta $C001             ; Reload counter
    inc irq_next_layer
    jmp @done

@layer1:
    lda parallax1_scroll_x
    sta $2005
    lda parallax1_scroll_y
    sta $2005

    lda #$00
    sta $8000
    lda parallax1_chr_bank
    sta $8001

    lda parallax2_scanline
    sta $C000
    sta $C001
    inc irq_next_layer
    jmp @done

@layer2:
    lda parallax2_scroll_x
    sta $2005
    lda parallax2_scroll_y
    sta $2005

    lda #$00
    sta $8000
    lda parallax2_chr_bank
    sta $8001

    ; No more layers - disable IRQ until next frame
    sta $E000
    lda #0
    sta irq_next_layer

@done:
    pla
    tay
    pla
    tax
    pla
    rti
.endproc

; Call in NMI to start parallax for next frame
.proc setup_parallax_frame
    ; Reset layer counter
    lda #0
    sta irq_next_layer

    ; Set initial scroll (layer 0)
    lda parallax0_scroll_x
    sta $2005
    lda parallax0_scroll_y
    sta $2005

    ; Setup first IRQ for layer 1
    lda parallax1_scanline
    sta $C000             ; IRQ latch value
    sta $C001             ; Reload counter
    sta $E001             ; Enable IRQ

    rts
.endproc

; Update parallax positions based on camera
.proc update_parallax_scroll
    ; For each layer, scroll_x = camera_x * speed / 256
    ; Layer 0: 25% speed (64/256)
    lda camera_x
    lsr a                 ; /2
    lsr a                 ; /4
    sta parallax0_scroll_x

    ; Layer 1: 50% speed (128/256)
    lda camera_x
    lsr a                 ; /2
    sta parallax1_scroll_x

    ; Layer 2: 100% speed
    lda camera_x
    sta parallax2_scroll_x

    rts
.endproc
```

---

## 3. Strategic Sprite Budgeting

### Batman's Philosophy

**"Bomb the screen with graphics, limit the enemies"**

Instead of many small, simple enemies, Batman uses:
- Large, detailed player sprite (16-24 tiles)
- Large, detailed bosses (12-16 tiles)
- Only 1-2 humanoid enemies on screen at once
- Rich projectiles and effects

### Budget Allocation

```
High-Fidelity Mode (Boss battles, cutscenes):
┌────────────────────────────────────────┐
│ Player:       16 sprites (4x4)         │
│ Boss:         12 sprites (3x4)         │
│ Projectiles:   8 sprites               │
│ Effects:       8 sprites               │
│ HUD:           4 sprites               │
│ ────────────────────────────────────── │
│ TOTAL:        48 sprites (< 64 max)    │
│ Scanline max: ~8 sprites (careful Y)   │
└────────────────────────────────────────┘

Action Mode (Many enemies):
┌────────────────────────────────────────┐
│ Player:        8 sprites (2x4)         │
│ Enemies:      24 sprites (8 x 3 each)  │
│ Projectiles:  16 sprites               │
│ Effects:       8 sprites               │
│ HUD:           4 sprites               │
│ ────────────────────────────────────── │
│ TOTAL:        60 sprites               │
│ Scanline max: Carefully stagger Y      │
└────────────────────────────────────────┘
```

### Implementation: Dynamic LOD

```asm
; Check sprite budget and switch modes
.proc check_sprite_budget
    ; Count active sprites
    lda enemy_count
    cmp #3
    bcs @action_mode

@hifi_mode:
    ; Few enemies - use large player sprite
    lda #16
    sta player_sprite_count
    jmp @done

@action_mode:
    ; Many enemies - use smaller player sprite
    lda #8
    sta player_sprite_count

@done:
    rts
.endproc
```

---

## 4. Dithered Pre-rendered Art

### NES Color Limitations

- 4 colors per 8x8 tile (including transparent)
- 4 background palettes per 16x16 attribute region
- 4 sprite palettes, any sprite can use any palette

### Dithering Patterns

Ordered dithering simulates intermediate colors:

```
Pattern A (50% mix):    Pattern B (25% mix):
█ ░ █ ░                 █ ░ ░ ░
░ █ ░ █                 ░ ░ ░ ░
█ ░ █ ░                 ░ ░ █ ░
░ █ ░ █                 ░ ░ ░ ░
```

### Pipeline Integration

Add to `unified_pipeline.py`:

```python
def apply_nes_dithering(image, method='ordered'):
    """
    Apply NES-optimized dithering.

    Methods:
    - 'ordered': Bayer matrix aligned to 8x8 tiles
    - 'diffusion': Floyd-Steinberg with tile boundary awareness
    - 'none': Hard quantization only
    """
    if method == 'ordered':
        # 4x4 Bayer matrix, tiled to cover image
        bayer = np.array([
            [0,  8,  2, 10],
            [12, 4, 14,  6],
            [3, 11,  1,  9],
            [15, 7, 13,  5]
        ]) / 16.0

        # Apply at 8x8 tile boundaries
        for ty in range(0, height, 8):
            for tx in range(0, width, 8):
                tile = image[ty:ty+8, tx:tx+8]
                # Apply Bayer threshold
                for py in range(8):
                    for px in range(8):
                        threshold = bayer[py % 4][px % 4]
                        # ... quantize with threshold
```

---

## 5. Cross-Platform Abstraction

### HAL Parallax Layer Structure

```c
/* src/hal/hal_parallax.h */

typedef struct {
    uint8_t  scanline;      /* Trigger scanline (0-239 NES, 0-223 Genesis) */
    int16_t  scroll_x;      /* 8.8 fixed point */
    int16_t  scroll_y;      /* 8.8 fixed point */
    uint8_t  speed;         /* 0=static, 128=50%, 255=100% camera speed */
    uint8_t  tileset_id;    /* Platform-specific tileset/CHR bank */
} hal_parallax_layer_t;

/* Platform limits */
#if HAL_PLATFORM == HAL_PLAT_NES
    #define HAL_PARALLAX_MAX_LAYERS  3   /* IRQ limited */
#elif HAL_PLATFORM == HAL_PLAT_GENESIS
    #define HAL_PARALLAX_MAX_LAYERS  4   /* 2 scroll planes + line scroll */
#elif HAL_PLATFORM == HAL_PLAT_SNES
    #define HAL_PARALLAX_MAX_LAYERS  4   /* Mode 1 + HDMA */
#else
    #define HAL_PARALLAX_MAX_LAYERS  8   /* Software rendering */
#endif

/* API */
void hal_parallax_init(void);
void hal_parallax_set_layer(uint8_t layer_id, const hal_parallax_layer_t* layer);
void hal_parallax_update(int16_t camera_x, int16_t camera_y);
void hal_parallax_render(void);  /* Platform-specific */
```

### NES-to-Genesis Mapping

| NES Technique | Genesis Equivalent |
|--------------|-------------------|
| CHR bank swap | DMA tile upload |
| Scanline IRQ | H-INT / Line scroll table |
| 3 parallax layers | Plane A + Plane B + window |
| 64 sprites | 80 sprites |
| 8 sprites/line | 20 sprites/line |

---

## 6. Implementation Checklist

### Phase 1: Static High-Fidelity
- [ ] Organize CHR-ROM with sprite/BG separation
- [ ] Implement large metasprite rendering
- [ ] Enable background tiles

### Phase 2: CHR Animation
- [ ] Setup animated CHR banks in graphics.asm
- [ ] Timer-driven bank switching in NMI
- [ ] Test waterfall/cloud animation

### Phase 3: Parallax
- [ ] Implement IRQ handler for MMC3
- [ ] 2-layer parallax (sky + ground)
- [ ] 3-layer parallax (sky + mountains + ground)

### Phase 4: Cross-Platform
- [ ] Add hal_parallax.h to HAL
- [ ] NES parallax implementation
- [ ] Genesis parallax implementation (line scroll)

---

## Memory Impact

### Zero Page Usage (+8 bytes)
```
$D0-$D1: chr_anim_timer, chr_anim_frame
$D2-$D3: irq_next_layer, parallax_count
$D4-$D7: Reserved for parallax temps
```

### RAM Usage (+24 bytes)
```
$0780-$0797: Parallax layer data (3 layers × 8 bytes)
```

### CHR-ROM Impact
- Static game: 1 CHR bank (8KB)
- With animation: 2-4 CHR banks (16-32KB)
- Full Batman-style: 8 CHR banks (64KB) - requires larger ROM

---

## References

- [Batman: Return of the Joker Analysis](https://www.reddit.com/r/nes/comments/1h8zqtq/batmanreturn_of_the_joker_how_did_they_do_it/)
- [MMC3 Technical Reference](https://www.nesdev.org/wiki/MMC3)
- [NES Parallax Scrolling](https://www.nesdev.org/wiki/PPU_scrolling)
- [Sunsoft Audio Engine](https://www.nesdev.org/wiki/Sunsoft_5B_audio)

---

*This document is part of the ARDK (Agentic Retro Development Kit) project.*
