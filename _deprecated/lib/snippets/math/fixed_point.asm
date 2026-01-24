; =============================================================================
; FIXED POINT MATH - 8.8 and 4.4 formats for smooth movement
; =============================================================================
; 8.8 format: High byte = integer, Low byte = fraction
; Example: $01.80 = 1.5 (1 + 128/256)
; Range: 0.00 to 255.996 (unsigned) or -128 to +127.996 (signed)
; =============================================================================

.segment "ZEROPAGE"
; 8.8 fixed point variables
math_result_lo:     .res 1       ; Low byte of result (fraction)
math_result_hi:     .res 1       ; High byte of result (integer)
math_temp:          .res 4       ; Temp storage for operations

.segment "CODE"

; -----------------------------------------------------------------------------
; add_8_8 - Add two 8.8 fixed point numbers
; Input: A:X = first operand (A=hi, X=lo)
;        Y = pointer to second operand (2 bytes, lo:hi)
; Output: math_result_hi:math_result_lo
; -----------------------------------------------------------------------------
.proc add_8_8
    stx math_result_lo
    sta math_result_hi

    clc
    lda math_result_lo
    adc $00, y                   ; Add low bytes
    sta math_result_lo

    lda math_result_hi
    adc $01, y                   ; Add high bytes with carry
    sta math_result_hi

    rts
.endproc

; -----------------------------------------------------------------------------
; sub_8_8 - Subtract two 8.8 fixed point numbers
; Input: A:X = first operand (A=hi, X=lo)
;        Y = pointer to second operand
; Output: math_result_hi:math_result_lo = first - second
; -----------------------------------------------------------------------------
.proc sub_8_8
    stx math_result_lo
    sta math_result_hi

    sec
    lda math_result_lo
    sbc $00, y                   ; Subtract low bytes
    sta math_result_lo

    lda math_result_hi
    sbc $01, y                   ; Subtract high bytes with borrow
    sta math_result_hi

    rts
.endproc

; -----------------------------------------------------------------------------
; mul_8x8_16 - Multiply two 8-bit numbers, 16-bit result
; Input: A = multiplicand, X = multiplier
; Output: math_result_hi:math_result_lo = A * X
; Destroys: A, X, Y
; -----------------------------------------------------------------------------
.proc mul_8x8_16
    sta math_temp
    stx math_temp+1

    lda #0
    sta math_result_lo
    sta math_result_hi

    ldy #8                       ; 8 bits

@loop:
    lsr math_temp+1              ; Shift multiplier right
    bcc @no_add                  ; Bit was 0, skip add

    clc
    lda math_result_lo
    adc math_temp
    sta math_result_lo
    lda math_result_hi
    adc #0
    sta math_result_hi

@no_add:
    asl math_temp                ; Shift multiplicand left
    rol math_result_hi           ; (actually shifts into result)

    dey
    bne @loop

    rts
.endproc

; -----------------------------------------------------------------------------
; mul_8_8_frac - Multiply 8.8 by 8-bit fraction (0-255 = 0.0 to 0.996)
; Input: A:X = 8.8 value, Y = 8-bit fraction
; Output: math_result_hi:math_result_lo = scaled result
; Use for: Applying velocity, friction, etc.
; -----------------------------------------------------------------------------
.proc mul_8_8_frac
    ; Store inputs
    stx math_temp               ; Lo byte of 8.8
    sta math_temp+1             ; Hi byte of 8.8
    sty math_temp+2             ; Fraction multiplier

    ; Multiply hi byte by fraction
    lda math_temp+1
    ldx math_temp+2
    jsr mul_8x8_16
    lda math_result_lo          ; This becomes new hi byte
    sta math_temp+3

    ; Multiply lo byte by fraction
    lda math_temp
    ldx math_temp+2
    jsr mul_8x8_16

    ; Combine: temp+3 is hi, result_hi is middle, result_lo discarded
    lda math_result_hi
    sta math_result_lo
    lda math_temp+3
    sta math_result_hi

    rts
.endproc

; -----------------------------------------------------------------------------
; div_16_8 - Divide 16-bit by 8-bit, 8-bit result
; Input: math_result_hi:math_result_lo = dividend
;        A = divisor
; Output: X = quotient, A = remainder
; -----------------------------------------------------------------------------
.proc div_16_8
    sta math_temp               ; Divisor

    ldx #16                     ; 16 bits
    lda #0                      ; Clear remainder

@loop:
    asl math_result_lo          ; Shift dividend left
    rol math_result_hi
    rol a                       ; Shift into remainder

    cmp math_temp               ; Compare with divisor
    bcc @no_sub                 ; Remainder < divisor

    sbc math_temp               ; Subtract divisor
    inc math_result_lo          ; Set quotient bit

@no_sub:
    dex
    bne @loop

    ; Result: math_result_lo = quotient, A = remainder
    ldx math_result_lo
    rts
.endproc

; -----------------------------------------------------------------------------
; negate_8_8 - Negate signed 8.8 value
; Input: A:X = value (A=hi, X=lo)
; Output: math_result_hi:math_result_lo = -input
; -----------------------------------------------------------------------------
.proc negate_8_8
    stx math_result_lo
    sta math_result_hi

    ; Two's complement: invert and add 1
    lda math_result_lo
    eor #$FF
    clc
    adc #1
    sta math_result_lo

    lda math_result_hi
    eor #$FF
    adc #0
    sta math_result_hi

    rts
.endproc

; =============================================================================
; VELOCITY/PHYSICS HELPERS
; =============================================================================

; -----------------------------------------------------------------------------
; apply_velocity - Add velocity to position (both 8.8)
; Input: X = offset to position (2 bytes), Y = offset to velocity (2 bytes)
; Modifies: Position at X
; -----------------------------------------------------------------------------
.proc apply_velocity
    clc
    lda $00, x                   ; Position lo
    adc $00, y                   ; Velocity lo
    sta $00, x

    lda $01, x                   ; Position hi
    adc $01, y                   ; Velocity hi
    sta $01, x

    rts
.endproc

; -----------------------------------------------------------------------------
; apply_friction - Multiply velocity by friction factor
; Input: X = offset to velocity (2 bytes), A = friction (e.g., 240 = 94%)
; Modifies: Velocity at X
; -----------------------------------------------------------------------------
.proc apply_friction
    tay                          ; Friction to Y
    lda $01, x                   ; Velocity hi
    pha
    lda $00, x                   ; Velocity lo
    tax
    pla                          ; A:X = velocity
    jsr mul_8_8_frac
    pla                          ; Get original X back
    tax
    lda math_result_lo
    sta $00, x
    lda math_result_hi
    sta $01, x
    rts
.endproc

; =============================================================================
; COMMON FRACTIONS (for velocity/physics)
; =============================================================================
FRAC_50_PERCENT  = 128           ; 0.5
FRAC_75_PERCENT  = 192           ; 0.75
FRAC_90_PERCENT  = 230           ; 0.90 (light friction)
FRAC_95_PERCENT  = 243           ; 0.95 (very light friction)
FRAC_25_PERCENT  = 64            ; 0.25

; =============================================================================
; USAGE EXAMPLES:
; =============================================================================
;
; ; Player position/velocity (8.8 format)
; player_x_lo:  .byte 0    ; Fractional part
; player_x_hi:  .byte 100  ; Integer part (pixel)
; player_vx_lo: .byte 0
; player_vx_hi: .byte 0
;
; ; Add velocity to position:
;   clc
;   lda player_x_lo
;   adc player_vx_lo
;   sta player_x_lo
;   lda player_x_hi
;   adc player_vx_hi
;   sta player_x_hi
;
; ; Apply friction (95%):
;   lda player_vx_hi
;   ldx player_vx_lo
;   ldy #FRAC_95_PERCENT
;   jsr mul_8_8_frac
;   lda math_result_lo
;   sta player_vx_lo
;   lda math_result_hi
;   sta player_vx_hi
;
; ; Get integer position for sprite:
;   lda player_x_hi       ; This is the pixel position
;   sta sprite_x
;
; =============================================================================
