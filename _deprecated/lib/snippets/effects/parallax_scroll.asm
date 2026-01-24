; =============================================================================
; PARALLAX SCROLLING - Multiple scroll speeds for depth effect
; =============================================================================
; Techniques: Split scroll, CHR banking, attribute tricks
; Examples: Batman, Ninja Gaiden, many scrolling shooters
; =============================================================================

.segment "ZEROPAGE"

; Scroll positions (8.8 fixed point for sub-pixel precision)
scroll_x_lo:        .res 1       ; Fractional X scroll
scroll_x_hi:        .res 1       ; Pixel X scroll (0-255)
scroll_y_lo:        .res 1
scroll_y_hi:        .res 1

; Layer speeds (8-bit fraction, 256 = 1x speed)
layer_speed_far:    .res 1       ; Distant layer (slower)
layer_speed_mid:    .res 1       ; Middle layer
layer_speed_near:   .res 1       ; Near layer (faster)

; Calculated layer positions
layer_scroll_far:   .res 1
layer_scroll_mid:   .res 1
layer_scroll_near:  .res 1

; Split point for scanline-based parallax
split_scanline:     .res 1       ; Where to change scroll

.segment "CODE"

; -----------------------------------------------------------------------------
; init_parallax - Initialize parallax scrolling
; -----------------------------------------------------------------------------
.proc init_parallax
    ; Set default layer speeds
    lda #64                      ; 0.25x for far background
    sta layer_speed_far
    lda #128                     ; 0.5x for mid
    sta layer_speed_mid
    lda #256-1                   ; ~1.0x for near (player layer)
    sta layer_speed_near

    ; Default split at scanline 96 (1/3 down screen)
    lda #96
    sta split_scanline

    ; Clear scroll
    lda #0
    sta scroll_x_lo
    sta scroll_x_hi
    sta scroll_y_lo
    sta scroll_y_hi

    rts
.endproc

; -----------------------------------------------------------------------------
; update_parallax - Calculate layer scroll values
; Call after updating main scroll
; -----------------------------------------------------------------------------
.proc update_parallax
    ; Far layer = main_scroll * layer_speed_far / 256
    lda scroll_x_hi
    ldx layer_speed_far
    jsr mul_scroll_speed
    sta layer_scroll_far

    ; Mid layer
    lda scroll_x_hi
    ldx layer_speed_mid
    jsr mul_scroll_speed
    sta layer_scroll_mid

    ; Near layer (usually same as main or slightly faster)
    lda scroll_x_hi
    sta layer_scroll_near

    rts
.endproc

; Helper: multiply scroll by speed factor
; Input: A = scroll position, X = speed (0-255)
; Output: A = result
mul_scroll_speed:
    ; Simple 8x8 multiply, take high byte
    sta temp_scroll
    stx temp_speed

    lda #0
    ldy #8
@loop:
    lsr temp_speed
    bcc @no_add
    clc
    adc temp_scroll
@no_add:
    ror
    dey
    bne @loop
    ; A = high byte of result (scroll * speed / 256)
    rts

temp_scroll: .byte 0
temp_speed:  .byte 0

; =============================================================================
; SCANLINE SPLIT PARALLAX
; =============================================================================
; Uses sprite 0 hit to trigger mid-frame scroll change
; This creates visible parallax without extra CHR banks

; -----------------------------------------------------------------------------
; setup_sprite0_split - Position sprite 0 for split detection
; Sprite 0 should be placed at the split point
; -----------------------------------------------------------------------------
.proc setup_sprite0_split
    ; Position sprite 0 at split scanline
    lda split_scanline
    sec
    sbc #1                       ; Sprite 0 hit triggers on next scanline
    sta $0200                    ; Sprite 0 Y

    ; Use a solid tile that will definitely hit background
    lda #$FF                     ; Solid tile (customize for your tileset)
    sta $0201

    ; Attributes
    lda #%00100000               ; Behind background for cleaner look
    sta $0202

    ; X position - place where background has pixels
    lda #8                       ; Near left edge (customize)
    sta $0203

    rts
.endproc

; -----------------------------------------------------------------------------
; wait_sprite0_clear - Wait for sprite 0 flag to clear
; Call at start of vblank handling
; -----------------------------------------------------------------------------
.proc wait_sprite0_clear
@wait:
    bit $2002
    bvs @wait                    ; Wait while sprite 0 flag set
    rts
.endproc

; -----------------------------------------------------------------------------
; wait_sprite0_hit - Wait for sprite 0 hit
; Call after NMI, before rendering top portion
; -----------------------------------------------------------------------------
.proc wait_sprite0_hit
@wait:
    bit $2002
    bvc @wait                    ; Wait until sprite 0 flag set
    rts
.endproc

; -----------------------------------------------------------------------------
; apply_split_scroll - Use in NMI for two-layer parallax
; -----------------------------------------------------------------------------
.proc apply_split_scroll
    ; Set scroll for top portion (far layer)
    lda layer_scroll_far
    sta $2005                    ; X scroll
    lda #0
    sta $2005                    ; Y scroll

    ; Wait for sprite 0 hit (marks split point)
    jsr wait_sprite0_hit

    ; Small delay for timing (adjust as needed)
    ldx #10
@delay:
    dex
    bne @delay

    ; Change scroll for bottom portion (near layer)
    lda layer_scroll_near
    sta $2005
    lda #0
    sta $2005

    rts
.endproc

; =============================================================================
; THREE-LAYER PARALLAX WITH IRQ (MMC3)
; =============================================================================
; Uses MMC3 scanline counter for precise splits

.segment "ZEROPAGE"
irq_layer:          .res 1       ; Which layer we're on (0-2)

.segment "CODE"

; -----------------------------------------------------------------------------
; setup_mmc3_parallax - Configure MMC3 IRQ for parallax
; Requires MMC3 mapper
; -----------------------------------------------------------------------------
.proc setup_mmc3_parallax
    ; Disable IRQ first
    sta $E000                    ; Disable MMC3 IRQ

    ; Set counter for first split
    lda #48                      ; Split at scanline 48
    sta $C000                    ; IRQ latch
    sta $C001                    ; Reload counter

    ; Enable IRQ
    sta $E001

    lda #0
    sta irq_layer

    rts
.endproc

; -----------------------------------------------------------------------------
; parallax_irq_handler - MMC3 IRQ handler for parallax
; Call from IRQ vector
; -----------------------------------------------------------------------------
.proc parallax_irq_handler
    pha
    txa
    pha

    ; Acknowledge IRQ
    sta $E000
    sta $E001

    ; Which layer are we switching to?
    ldx irq_layer
    inx
    cpx #3
    bcc @valid
    ldx #0                       ; Wrap around
@valid:
    stx irq_layer

    ; Apply scroll for this layer
    cpx #0
    beq @layer0
    cpx #1
    beq @layer1
    ; Layer 2 (bottom - near)
    lda layer_scroll_near
    jmp @apply

@layer0:
    ; Top layer (far)
    lda layer_scroll_far
    jmp @apply

@layer1:
    ; Middle layer
    lda layer_scroll_mid

@apply:
    ; Write scroll (need to write $2000 to latch properly)
    sta $2005                    ; X scroll
    lda #0
    sta $2005                    ; Y scroll

    ; Set up next split
    lda irq_layer
    beq @next48
    cmp #1
    beq @next96

    ; After layer 2, next is layer 0 at scanline 48
    lda #48
    jmp @set_counter

@next48:
    lda #48                      ; Next split in 48 scanlines
    jmp @set_counter

@next96:
    lda #48                      ; Another 48 scanlines

@set_counter:
    sta $C000
    sta $C001
    sta $E001                    ; Re-enable IRQ

    pla
    tax
    pla
    rti
.endproc

; =============================================================================
; CHR BANK PARALLAX
; =============================================================================
; Swap CHR banks mid-frame for completely different graphics per layer
; Most visually impressive but uses CHR space

; -----------------------------------------------------------------------------
; setup_chr_parallax - CHR bank switching for parallax
; Uses sprite 0 hit timing
; -----------------------------------------------------------------------------
.proc setup_chr_parallax
    ; Initial CHR banks for far layer
    lda #$00                     ; Far background CHR bank
    ; Write to MMC3 CHR registers...
    ; (MMC3 specific: $8000 = select, $8001 = bank)

    jsr setup_sprite0_split

    rts
.endproc

; -----------------------------------------------------------------------------
; chr_parallax_nmi - NMI handler portion for CHR parallax
; -----------------------------------------------------------------------------
.proc chr_parallax_nmi
    ; Far layer CHR (top of screen)
    lda #$80                     ; Select CHR bank 0
    sta $8000
    lda #0                       ; Bank 0 = far graphics
    sta $8001

    ; Wait for split
    jsr wait_sprite0_hit

    ; Near layer CHR (bottom of screen)
    lda #$80
    sta $8000
    lda #2                       ; Bank 2 = near graphics
    sta $8001

    rts
.endproc

; =============================================================================
; USAGE EXAMPLE - SIMPLE TWO-LAYER
; =============================================================================
;
; ; Initialization:
;   jsr init_parallax
;   jsr setup_sprite0_split
;
; ; Every frame:
;   ; Update main scroll based on player movement
;   lda player_x
;   sta scroll_x_hi
;   jsr update_parallax
;
; ; In NMI handler:
;   jsr wait_sprite0_clear       ; Clear flag from last frame
;   ; ... do vblank updates ...
;   jsr apply_split_scroll       ; Apply parallax scrolling
;
; =============================================================================
; ADVANCED TECHNIQUES:
; =============================================================================
;
; 1. RASTER BARS (multiple scroll changes per frame)
;    - Use multiple sprite 0 hits (position sprite 0 differently each frame)
;    - Or use mapper IRQ for precise timing
;
; 2. PSEUDO-3D ROADS (like Rad Racer)
;    - Change scroll speed per scanline
;    - Use lookup table indexed by scanline
;    - Requires very tight timing
;
; 3. WATER REFLECTIONS
;    - Flip nametable vertically at split
;    - Animate scroll offset for wave effect
;
; 4. PARALLAX STARS
;    - Multiple CHR banks with different star patterns
;    - Swap banks at different scanlines
;
; =============================================================================
