;==============================================================================
; ARDK - Assembly HAL for 6502 Family
; hal_6502.inc - Platform-agnostic macros for 6502-based systems
;==============================================================================
;
; TARGET SYSTEMS:
;   - NES (primary)
;   - Commodore 64
;   - Atari 2600/7800
;   - PC Engine (HuC6280, 65C02 derivative)
;   - Apple II
;
; DESIGN PRINCIPLES:
;   1. Macros expand to optimal code per-platform
;   2. Register conventions preserved across platforms
;   3. Zero-page usage abstracted
;   4. Platform-specific features opt-in via extensions
;
; REGISTER CONVENTIONS:
;   A - Accumulator (primary work register)
;   X - Index register (entity iteration, table indexing)
;   Y - Index register (secondary, often for data offsets)
;   SP - Stack pointer (rarely touched directly)
;
; ZERO PAGE CONVENTIONS:
;   $00-$0F - HAL reserved (pointers, temps)
;   $10-$1F - Input state
;   $20-$2F - Player state cache
;   $30-$7F - Game use
;   $80-$FF - Platform-specific / stack area
;
;==============================================================================

;------------------------------------------------------------------------------
; Platform Detection
;------------------------------------------------------------------------------

.ifndef PLATFORM_6502_FAMILY
    .define PLATFORM_6502_FAMILY 1
.endif

; Set defaults if platform not specified
.ifndef PLATFORM_NES
.ifndef PLATFORM_C64
.ifndef PLATFORM_PCE
    ; Default to NES
    .define PLATFORM_NES 1
.endif
.endif
.endif

;------------------------------------------------------------------------------
; Zero Page Allocation
;------------------------------------------------------------------------------

; HAL reserved zero page locations
HAL_PTR_LO      = $00       ; General-purpose pointer (low byte)
HAL_PTR_HI      = $01       ; General-purpose pointer (high byte)
HAL_PTR2_LO     = $02       ; Second pointer (low)
HAL_PTR2_HI     = $03       ; Second pointer (high)
HAL_TEMP0       = $04       ; Temporary storage
HAL_TEMP1       = $05
HAL_TEMP2       = $06
HAL_TEMP3       = $07
HAL_MATH_A_LO   = $08       ; Math operand A (16-bit)
HAL_MATH_A_HI   = $09
HAL_MATH_B_LO   = $0A       ; Math operand B (16-bit)
HAL_MATH_B_HI   = $0B
HAL_MATH_R_LO   = $0C       ; Math result (16-bit)
HAL_MATH_R_HI   = $0D
HAL_FRAME_LO    = $0E       ; Frame counter (low)
HAL_FRAME_HI    = $0F       ; Frame counter (high)

; Input state
HAL_JOY1_STATE  = $10       ; Controller 1 current state
HAL_JOY1_PRESS  = $11       ; Controller 1 newly pressed
HAL_JOY1_PREV   = $12       ; Controller 1 previous frame
HAL_JOY2_STATE  = $13       ; Controller 2 current state
HAL_JOY2_PRESS  = $14       ; Controller 2 newly pressed
HAL_JOY2_PREV   = $15       ; Controller 2 previous frame

;------------------------------------------------------------------------------
; Button Constants (Platform-Agnostic)
;------------------------------------------------------------------------------

HAL_BTN_A       = %00000001
HAL_BTN_B       = %00000010
HAL_BTN_SELECT  = %00000100
HAL_BTN_START   = %00001000
HAL_BTN_UP      = %00010000
HAL_BTN_DOWN    = %00100000
HAL_BTN_LEFT    = %01000000
HAL_BTN_RIGHT   = %10000000

;------------------------------------------------------------------------------
; Fixed-Point Macros (8.8 format)
;------------------------------------------------------------------------------

; Convert integer to fixed-point (compile-time)
.define FP_FROM_INT(n)  ((n) << 8)

; Convert fixed-point to integer (drops fractional part)
.macro FP_TO_INT result, fp_lo, fp_hi
    lda fp_hi
    sta result
.endmacro

; Add two fixed-point values: R = A + B
; Inputs in HAL_MATH_A and HAL_MATH_B, result in HAL_MATH_R
.macro FP_ADD
    clc
    lda HAL_MATH_A_LO
    adc HAL_MATH_B_LO
    sta HAL_MATH_R_LO
    lda HAL_MATH_A_HI
    adc HAL_MATH_B_HI
    sta HAL_MATH_R_HI
.endmacro

; Subtract: R = A - B
.macro FP_SUB
    sec
    lda HAL_MATH_A_LO
    sbc HAL_MATH_B_LO
    sta HAL_MATH_R_LO
    lda HAL_MATH_A_HI
    sbc HAL_MATH_B_HI
    sta HAL_MATH_R_HI
.endmacro

; Negate: R = -A
.macro FP_NEG
    sec
    lda #0
    sbc HAL_MATH_A_LO
    sta HAL_MATH_R_LO
    lda #0
    sbc HAL_MATH_A_HI
    sta HAL_MATH_R_HI
.endmacro

; Absolute value: R = |A|
.macro FP_ABS
    lda HAL_MATH_A_HI
    bpl @positive
    FP_NEG
    jmp @done
@positive:
    lda HAL_MATH_A_LO
    sta HAL_MATH_R_LO
    lda HAL_MATH_A_HI
    sta HAL_MATH_R_HI
@done:
.endmacro

;------------------------------------------------------------------------------
; Entity Access Macros
;
; Entity structure is 16 bytes, allowing fast indexing with X << 4
; X register holds entity ID throughout these macros
;------------------------------------------------------------------------------

; Entity field offsets (must match entity.h)
ENT_FLAGS   = 0
ENT_TYPE    = 1
ENT_X_LO    = 2
ENT_X_HI    = 3
ENT_Y_LO    = 4
ENT_Y_HI    = 5
ENT_VX_LO   = 6
ENT_VX_HI   = 7
ENT_VY_LO   = 8
ENT_VY_HI   = 9
ENT_HP      = 10
ENT_TIMER   = 11
ENT_SPRITE  = 12
ENT_FRAME   = 13
ENT_DATA_LO = 14
ENT_DATA_HI = 15

; Entity flags
ENT_FLAG_ACTIVE   = %00000001
ENT_FLAG_VISIBLE  = %00000010
ENT_FLAG_SOLID    = %00000100
ENT_FLAG_FRIENDLY = %00001000
ENT_FLAG_ENEMY    = %00010000
ENT_FLAG_PICKUP   = %00100000
ENT_FLAG_INVULN   = %01000000
ENT_FLAG_FLASH    = %10000000

; Entity categories (high nibble of type)
ENT_CAT_NONE        = $00
ENT_CAT_PLAYER      = $10
ENT_CAT_ENEMY       = $20
ENT_CAT_PROJECTILE  = $30
ENT_CAT_PICKUP      = $40
ENT_CAT_EFFECT      = $50

; Load entity base address into HAL_PTR
; X = entity ID (0-31)
.macro ENTITY_LOAD_PTR
    ; Base address = entity_pool + (X * 16)
    ; For 6502, we use a lookup table for speed
    lda entity_ptr_lo, x
    sta HAL_PTR_LO
    lda entity_ptr_hi, x
    sta HAL_PTR_HI
.endmacro

; Get entity field (result in A)
; X = entity ID, field = ENT_* offset
.macro ENTITY_GET_FIELD field
    ENTITY_LOAD_PTR
    ldy #field
    lda (HAL_PTR_LO), y
.endmacro

; Set entity field (value in A)
.macro ENTITY_SET_FIELD field
    pha
    ENTITY_LOAD_PTR
    pla
    ldy #field
    sta (HAL_PTR_LO), y
.endmacro

; Check if entity is active (sets Z flag)
.macro ENTITY_IS_ACTIVE
    ENTITY_GET_FIELD ENT_FLAGS
    and #ENT_FLAG_ACTIVE
.endmacro

; Apply velocity to position for entity X
.macro ENTITY_APPLY_VELOCITY
    ENTITY_LOAD_PTR

    ; X position += VX
    ldy #ENT_X_LO
    clc
    lda (HAL_PTR_LO), y
    ldy #ENT_VX_LO
    adc (HAL_PTR_LO), y
    ldy #ENT_X_LO
    sta (HAL_PTR_LO), y

    ldy #ENT_X_HI
    lda (HAL_PTR_LO), y
    ldy #ENT_VX_HI
    adc (HAL_PTR_LO), y
    ldy #ENT_X_HI
    sta (HAL_PTR_LO), y

    ; Y position += VY
    ldy #ENT_Y_LO
    clc
    lda (HAL_PTR_LO), y
    ldy #ENT_VY_LO
    adc (HAL_PTR_LO), y
    ldy #ENT_Y_LO
    sta (HAL_PTR_LO), y

    ldy #ENT_Y_HI
    lda (HAL_PTR_LO), y
    ldy #ENT_VY_HI
    adc (HAL_PTR_LO), y
    ldy #ENT_Y_HI
    sta (HAL_PTR_LO), y
.endmacro

;------------------------------------------------------------------------------
; Input Macros
;------------------------------------------------------------------------------

; Read controllers and update input state
; Platform-specific implementation, common interface
.macro HAL_INPUT_UPDATE
    .ifdef PLATFORM_NES
        jsr _hal_nes_input_read
    .elseif PLATFORM_C64
        jsr _hal_c64_input_read
    .elseif PLATFORM_PCE
        jsr _hal_pce_input_read
    .else
        jsr _hal_nes_input_read
    .endif

    ; Calculate newly pressed (current AND NOT previous)
    lda HAL_JOY1_PREV
    eor #$FF
    and HAL_JOY1_STATE
    sta HAL_JOY1_PRESS

    lda HAL_JOY2_PREV
    eor #$FF
    and HAL_JOY2_STATE
    sta HAL_JOY2_PRESS

    ; Save current as previous
    lda HAL_JOY1_STATE
    sta HAL_JOY1_PREV
    lda HAL_JOY2_STATE
    sta HAL_JOY2_PREV
.endmacro

; Check if button(s) held (result in Z flag)
.macro HAL_BTN_HELD buttons
    lda HAL_JOY1_STATE
    and #buttons
.endmacro

; Check if button(s) just pressed (result in Z flag)
.macro HAL_BTN_PRESSED buttons
    lda HAL_JOY1_PRESS
    and #buttons
.endmacro

;------------------------------------------------------------------------------
; Sprite Macros
;
; Abstract sprite handling across platforms.
; NES: 4 bytes per sprite in OAM shadow
; C64: Direct VIC-II sprite registers
; PCE: SATB format
;------------------------------------------------------------------------------

.ifdef PLATFORM_NES
    ; NES OAM format: Y, Tile, Attr, X
    OAM_SHADOW = $0200

    .macro HAL_SPRITE_SET slot, x_pos, y_pos, tile, attr
        lda y_pos
        sta OAM_SHADOW + (slot * 4) + 0
        lda tile
        sta OAM_SHADOW + (slot * 4) + 1
        lda attr
        sta OAM_SHADOW + (slot * 4) + 2
        lda x_pos
        sta OAM_SHADOW + (slot * 4) + 3
    .endmacro

    .macro HAL_SPRITE_HIDE slot
        lda #$FF
        sta OAM_SHADOW + (slot * 4) + 0
    .endmacro
.endif

.ifdef PLATFORM_C64
    ; C64 VIC-II sprites (8 hardware sprites)
    VIC_SPR_X   = $D000
    VIC_SPR_Y   = $D001
    VIC_SPR_MSB = $D010
    VIC_SPR_EN  = $D015

    .macro HAL_SPRITE_SET slot, x_pos, y_pos, tile, attr
        ; X position (with MSB handling)
        lda x_pos
        sta VIC_SPR_X + (slot * 2)
        ; Y position
        lda y_pos
        sta VIC_SPR_Y + (slot * 2)
        ; Sprite pointer
        lda tile
        sta $07F8 + slot
    .endmacro

    .macro HAL_SPRITE_HIDE slot
        lda VIC_SPR_EN
        and #($FF ^ (1 << slot))
        sta VIC_SPR_EN
    .endmacro
.endif

;------------------------------------------------------------------------------
; Math Table Lookups
;
; Sin/cos/atan2 using 256-entry tables.
; Angle: 0-255 = full circle
; Result: Fixed 8.8 (-256 to 256 for sin/cos)
;------------------------------------------------------------------------------

; Get sin(angle) into HAL_MATH_R
; Input: A = angle (0-255)
.macro HAL_SIN
    tax
    lda sin_table_lo, x
    sta HAL_MATH_R_LO
    lda sin_table_hi, x
    sta HAL_MATH_R_HI
.endmacro

; Get cos(angle) into HAL_MATH_R
; Input: A = angle (0-255)
.macro HAL_COS
    clc
    adc #64             ; cos(x) = sin(x + 64)
    tax
    lda sin_table_lo, x
    sta HAL_MATH_R_LO
    lda sin_table_hi, x
    sta HAL_MATH_R_HI
.endmacro

;------------------------------------------------------------------------------
; Frame Timing
;------------------------------------------------------------------------------

; Wait for VBlank (platform-specific)
.macro HAL_WAIT_VBLANK
    .ifdef PLATFORM_NES
        ; Wait for NMI flag
        :   bit $2002
            bpl :-
    .elseif PLATFORM_C64
        ; Wait for raster line 251
        :   lda $D012
            cmp #251
            bne :-
    .elseif PLATFORM_PCE
        ; Wait for VSYNC interrupt flag
        jsr _hal_pce_wait_vblank
    .endif
.endmacro

; Increment frame counter
.macro HAL_FRAME_INC
    inc HAL_FRAME_LO
    bne :+
    inc HAL_FRAME_HI
:
.endmacro

;------------------------------------------------------------------------------
; Memory Copy (Platform-Optimized)
;------------------------------------------------------------------------------

; Copy bytes from (HAL_PTR) to (HAL_PTR2)
; Y = count (0 = 256 bytes)
.macro HAL_MEMCPY
    dey
:   lda (HAL_PTR_LO), y
    sta (HAL_PTR2_LO), y
    dey
    bpl :-
.endmacro

; Fill memory at (HAL_PTR) with A
; Y = count (0 = 256 bytes)
.macro HAL_MEMSET
    dey
:   sta (HAL_PTR_LO), y
    dey
    bpl :-
.endmacro

;------------------------------------------------------------------------------
; Random Number Generation
;------------------------------------------------------------------------------

; Simple LFSR random, result in A
.macro HAL_RAND
    lda HAL_TEMP3       ; Use temp as seed storage
    beq @seed
    asl
    bcc @no_eor
    eor #$1D            ; Tap bits
@no_eor:
    sta HAL_TEMP3
    jmp @done
@seed:
    lda #$A5            ; Default seed
    sta HAL_TEMP3
@done:
.endmacro

;==============================================================================
; End of hal_6502.inc
;==============================================================================
