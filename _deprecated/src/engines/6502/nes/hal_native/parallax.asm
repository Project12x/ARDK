; =============================================================================
; NES Parallax Scrolling Module
; MMC3 scanline IRQ-based multi-layer parallax
; =============================================================================
; Based on techniques from Sunsoft's Batman: Return of the Joker
;
; Features:
;   - Up to 3 independent scroll layers
;   - CHR bank switching per layer
;   - 8.8 fixed-point sub-pixel scrolling
;   - Automatic speed-based scroll calculation
;
; Usage:
;   1. Call parallax_init during game init
;   2. Set layer parameters via parallax_set_layer
;   3. Call parallax_update each frame with camera position
;   4. Call parallax_setup_frame during NMI (before rendering)
;   5. IRQ handler runs automatically during scanlines
; =============================================================================

.include "nes.inc"

; -----------------------------------------------------------------------------
; Constants
; -----------------------------------------------------------------------------
MAX_PARALLAX_LAYERS = 3

; Layer structure offsets (8 bytes per layer)
LAYER_SCANLINE   = 0    ; Scanline to trigger (0-239)
LAYER_SCROLL_X_L = 1    ; X scroll low byte (fractional)
LAYER_SCROLL_X_H = 2    ; X scroll high byte (pixel)
LAYER_SCROLL_Y   = 3    ; Y scroll (pixel only)
LAYER_CHR_BANK   = 4    ; CHR bank for this layer
LAYER_SPEED      = 5    ; Speed factor (0=static, 128=50%, 255=100%)
LAYER_FLAGS      = 6    ; Bit 0: enabled, Bit 1: animate CHR
LAYER_RESERVED   = 7    ; Reserved for future use
LAYER_SIZE       = 8

; Flags
LAYER_FLAG_ENABLED = $01
LAYER_FLAG_ANIMATE = $02

; -----------------------------------------------------------------------------
; Zero Page Variables
; -----------------------------------------------------------------------------
.segment "ZEROPAGE"

.exportzp parallax_active, parallax_count, irq_current_layer

parallax_active:      .res 1    ; Non-zero if parallax system is active
parallax_count:       .res 1    ; Number of enabled layers (1-3)
irq_current_layer:    .res 1    ; Which layer the next IRQ should configure

; Camera position (set by game, read by parallax)
.exportzp camera_x, camera_x_frac, camera_y
camera_x:             .res 1    ; Camera X position (high byte)
camera_x_frac:        .res 1    ; Camera X position (low/fractional byte)
camera_y:             .res 1    ; Camera Y position

; Temporaries for IRQ (must be in ZP for speed)
irq_temp:             .res 2

; -----------------------------------------------------------------------------
; RAM Variables
; -----------------------------------------------------------------------------
.segment "BSS"

.export parallax_layers
parallax_layers:      .res MAX_PARALLAX_LAYERS * LAYER_SIZE  ; 24 bytes

; -----------------------------------------------------------------------------
; Code
; -----------------------------------------------------------------------------
.segment "CODE"

; =============================================================================
; parallax_init - Initialize parallax system
; =============================================================================
; Inputs: None
; Outputs: None
; Clobbers: A, X
; =============================================================================
.export parallax_init
.proc parallax_init
    ; Clear all parallax data
    lda #0
    ldx #MAX_PARALLAX_LAYERS * LAYER_SIZE - 1
@clear:
    sta parallax_layers, x
    dex
    bpl @clear

    ; Initialize state
    lda #0
    sta parallax_active
    sta parallax_count
    sta irq_current_layer
    sta camera_x
    sta camera_x_frac
    sta camera_y

    ; Disable MMC3 IRQ
    sta $E000

    rts
.endproc

; =============================================================================
; parallax_set_layer - Configure a parallax layer
; =============================================================================
; Inputs:
;   X = layer index (0-2)
;   A = scanline trigger (0-239)
;   Stack: speed, chr_bank, scroll_y (pushed in that order)
; Outputs: None
; Clobbers: A, X, Y
; =============================================================================
; Call like:
;   lda #SPEED
;   pha
;   lda #CHR_BANK
;   pha
;   lda #SCROLL_Y
;   pha
;   ldx #LAYER_INDEX
;   lda #SCANLINE
;   jsr parallax_set_layer
;   ; (stack is cleaned by routine)
; =============================================================================
.export parallax_set_layer
.proc parallax_set_layer
    ; Calculate offset: X * 8
    txa
    asl a
    asl a
    asl a
    tay                     ; Y = layer offset

    ; Store scanline
    ; A still has scanline value
    sta parallax_layers + LAYER_SCANLINE, y

    ; Get parameters from stack
    ; Stack layout: [return_lo] [return_hi] [scroll_y] [chr_bank] [speed]
    tsx

    ; scroll_y (offset +3 from current SP)
    lda $0103, x
    sta parallax_layers + LAYER_SCROLL_Y, y

    ; chr_bank (offset +4)
    lda $0104, x
    sta parallax_layers + LAYER_CHR_BANK, y

    ; speed (offset +5)
    lda $0105, x
    sta parallax_layers + LAYER_SPEED, y

    ; Set enabled flag
    lda #LAYER_FLAG_ENABLED
    sta parallax_layers + LAYER_FLAGS, y

    ; Initialize scroll to 0
    lda #0
    sta parallax_layers + LAYER_SCROLL_X_L, y
    sta parallax_layers + LAYER_SCROLL_X_H, y

    ; Clean up stack (remove 3 bytes we pushed)
    pla                     ; Return address low
    sta irq_temp
    pla                     ; Return address high
    sta irq_temp+1
    pla                     ; scroll_y (discard)
    pla                     ; chr_bank (discard)
    pla                     ; speed (discard)
    lda irq_temp+1
    pha
    lda irq_temp
    pha

    ; Update layer count
    jsr count_enabled_layers

    rts
.endproc

; Count enabled layers
.proc count_enabled_layers
    lda #0
    sta parallax_count

    ldx #0
    ldy #0                  ; Layer offset
@loop:
    lda parallax_layers + LAYER_FLAGS, y
    and #LAYER_FLAG_ENABLED
    beq @next
    inc parallax_count
@next:
    tya
    clc
    adc #LAYER_SIZE
    tay
    inx
    cpx #MAX_PARALLAX_LAYERS
    bne @loop

    ; Set active flag if we have layers
    lda parallax_count
    sta parallax_active

    rts
.endproc

; =============================================================================
; parallax_update - Update layer scroll positions based on camera
; =============================================================================
; Call each frame before NMI
; Inputs: camera_x, camera_x_frac (set by game code)
; Outputs: Updates layer scroll values
; Clobbers: A, X, Y
; =============================================================================
.export parallax_update
.proc parallax_update
    ; Skip if not active
    lda parallax_active
    beq @done

    ldy #0                  ; Layer offset
    ldx #0                  ; Layer counter

@loop:
    ; Check if layer enabled
    lda parallax_layers + LAYER_FLAGS, y
    and #LAYER_FLAG_ENABLED
    beq @next

    ; Calculate scroll: camera_x * speed / 256
    ; This gives us sub-pixel precision
    ;
    ; scroll = (camera_x_full * speed) >> 8
    ; where camera_x_full = (camera_x << 8) | camera_x_frac
    ;
    ; Simplified: scroll_hi = camera_x * speed >> 8
    ;             scroll_lo = camera_x_frac * speed >> 8

    ; High byte calculation: camera_x * speed
    lda camera_x
    sta irq_temp
    lda parallax_layers + LAYER_SPEED, y
    sta irq_temp+1

    ; 8x8 multiply (result in A = high byte)
    jsr multiply_8x8_hi

    ; Store as scroll X high byte
    sta parallax_layers + LAYER_SCROLL_X_H, y

    ; Low byte calculation: camera_x_frac * speed
    lda camera_x_frac
    sta irq_temp
    ; irq_temp+1 still has speed

    jsr multiply_8x8_hi
    sta parallax_layers + LAYER_SCROLL_X_L, y

@next:
    tya
    clc
    adc #LAYER_SIZE
    tay
    inx
    cpx #MAX_PARALLAX_LAYERS
    bne @loop

@done:
    rts
.endproc

; 8x8 multiply, return high byte only
; Inputs: irq_temp = multiplicand, irq_temp+1 = multiplier
; Output: A = high byte of result
; Clobbers: X
.proc multiply_8x8_hi
    lda #0
    ldx #8
    clc
@loop:
    bcc @no_add
    clc
    adc irq_temp+1
@no_add:
    ror a
    ror irq_temp
    dex
    bne @loop
    ; A now has high byte
    rts
.endproc

; =============================================================================
; parallax_setup_frame - Setup IRQ for next frame (call during NMI)
; =============================================================================
; Must be called during vblank before rendering starts
; Inputs: None
; Outputs: Configures first layer scroll and arms IRQ for next layer
; Clobbers: A, X, Y
; =============================================================================
.export parallax_setup_frame
.proc parallax_setup_frame
    ; Skip if not active
    lda parallax_active
    beq @done

    ; Reset layer counter
    lda #0
    sta irq_current_layer

    ; Find first enabled layer
    ldy #0
@find_first:
    lda parallax_layers + LAYER_FLAGS, y
    and #LAYER_FLAG_ENABLED
    bne @found_first
    tya
    clc
    adc #LAYER_SIZE
    tay
    cpy #MAX_PARALLAX_LAYERS * LAYER_SIZE
    bne @find_first
    jmp @done               ; No enabled layers

@found_first:
    ; Set initial scroll from first layer
    lda parallax_layers + LAYER_SCROLL_X_H, y
    sta $2005               ; X scroll
    lda parallax_layers + LAYER_SCROLL_Y, y
    sta $2005               ; Y scroll

    ; Set CHR bank for first layer
    lda #$00                ; MMC3 bank register 0 (2KB CHR at $0000)
    sta $8000
    lda parallax_layers + LAYER_CHR_BANK, y
    sta $8001

    ; Find next enabled layer for IRQ
    lda #1
    sta irq_current_layer   ; Next IRQ handles layer 1

    ; Get scanline for layer 1 (if exists)
    tya
    clc
    adc #LAYER_SIZE
    tay
    cpy #MAX_PARALLAX_LAYERS * LAYER_SIZE
    bcs @no_more_layers

    lda parallax_layers + LAYER_FLAGS, y
    and #LAYER_FLAG_ENABLED
    beq @no_more_layers

    ; Setup IRQ for next layer's scanline
    lda parallax_layers + LAYER_SCANLINE, y
    sta $C000               ; IRQ latch
    sta $C001               ; Reload counter
    sta $E001               ; Enable IRQ
    jmp @done

@no_more_layers:
    ; Only one layer, no IRQ needed
    sta $E000               ; Disable IRQ

@done:
    rts
.endproc

; =============================================================================
; parallax_irq - IRQ handler for scanline-triggered layer switching
; =============================================================================
; Called automatically by hardware when scanline counter hits 0
; Inputs: irq_current_layer = which layer to configure
; Outputs: Sets scroll/CHR for current layer, arms IRQ for next
; =============================================================================
.export parallax_irq
.proc parallax_irq
    pha
    txa
    pha
    tya
    pha

    ; Acknowledge IRQ (write to $E000 then $E001)
    sta $E000               ; Disable IRQ
    sta $E001               ; Re-enable/acknowledge

    ; Calculate layer offset: irq_current_layer * 8
    lda irq_current_layer
    asl a
    asl a
    asl a
    tay                     ; Y = layer offset

    ; Safety check
    cpy #MAX_PARALLAX_LAYERS * LAYER_SIZE
    bcs @done

    ; Set scroll for this layer
    ; Note: This should be done at the start of hblank
    ; We're relying on the IRQ timing being close enough
    lda parallax_layers + LAYER_SCROLL_X_H, y
    sta $2005               ; X scroll
    lda parallax_layers + LAYER_SCROLL_Y, y
    sta $2005               ; Y scroll

    ; Set CHR bank
    lda #$00
    sta $8000
    lda parallax_layers + LAYER_CHR_BANK, y
    sta $8001

    ; Setup next layer's IRQ
    inc irq_current_layer
    lda irq_current_layer
    cmp parallax_count
    bcs @no_more            ; No more layers

    ; Calculate next layer offset
    asl a
    asl a
    asl a
    tay

    ; Check if next layer is enabled
    lda parallax_layers + LAYER_FLAGS, y
    and #LAYER_FLAG_ENABLED
    beq @no_more

    ; Set scanline for next IRQ
    lda parallax_layers + LAYER_SCANLINE, y
    sta $C000               ; IRQ latch
    sta $C001               ; Reload counter
    jmp @done

@no_more:
    ; Disable further IRQs this frame
    sta $E000

@done:
    pla
    tay
    pla
    tax
    pla
    rti
.endproc

; =============================================================================
; parallax_disable - Turn off parallax system
; =============================================================================
.export parallax_disable
.proc parallax_disable
    lda #0
    sta parallax_active
    sta $E000               ; Disable MMC3 IRQ
    rts
.endproc

; =============================================================================
; Convenience: Setup a simple 2-layer parallax (sky + ground)
; =============================================================================
; Inputs:
;   A = sky CHR bank
;   X = ground CHR bank
;   Y = split scanline (where ground starts)
; =============================================================================
.export parallax_setup_simple_2layer
.proc parallax_setup_simple_2layer
    ; Save parameters
    pha                     ; Sky CHR bank
    txa
    pha                     ; Ground CHR bank
    tya
    pha                     ; Split scanline

    ; Initialize
    jsr parallax_init

    ; Layer 0: Sky (top of screen, 25% scroll speed)
    lda #64                 ; Speed = 25% (64/256)
    pha
    lda $0103, x            ; Sky CHR bank (was first thing pushed)
    tsx
    lda $0106, x            ; Get sky bank from deep in stack
    pha
    lda #0                  ; Y scroll = 0
    pha
    ldx #0                  ; Layer 0
    lda #0                  ; Scanline = 0 (top)
    jsr parallax_set_layer

    ; Layer 1: Ground (from split line, 100% scroll speed)
    lda #255                ; Speed = 100%
    pha
    tsx
    lda $0104, x            ; Ground CHR bank
    pha
    lda #0                  ; Y scroll
    pha
    ldx #1                  ; Layer 1
    tsx
    lda $0106, x            ; Split scanline
    jsr parallax_set_layer

    ; Clean up our original 3 parameters
    tsx
    txa
    clc
    adc #3
    tax
    txs

    rts
.endproc
