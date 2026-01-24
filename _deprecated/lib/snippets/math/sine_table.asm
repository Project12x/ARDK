; =============================================================================
; SINE/COSINE LOOKUP TABLES - For circular motion, waves, rotations
; =============================================================================
; 256-entry tables, values 0-255 representing -1.0 to +1.0
; Actually: 0 = -1.0, 128 = 0.0, 255 = +1.0 (unsigned)
; Or use signed: -128 to +127
; =============================================================================

.segment "RODATA"

; -----------------------------------------------------------------------------
; sine_table - 256 entries, one full period
; Index 0 = 0 degrees, Index 64 = 90 degrees, Index 128 = 180 degrees, etc.
; Values: 128 = 0, 255 = +1, 0 = -1 (offset unsigned format)
; -----------------------------------------------------------------------------
sine_table:
    .byte 128, 131, 134, 137, 140, 143, 146, 149
    .byte 152, 155, 158, 162, 165, 167, 170, 173
    .byte 176, 179, 182, 185, 188, 190, 193, 196
    .byte 198, 201, 203, 206, 208, 211, 213, 215
    .byte 218, 220, 222, 224, 226, 228, 230, 232
    .byte 234, 235, 237, 238, 240, 241, 243, 244
    .byte 245, 246, 248, 249, 250, 250, 251, 252
    .byte 253, 253, 254, 254, 254, 255, 255, 255
    .byte 255, 255, 255, 255, 254, 254, 254, 253
    .byte 253, 252, 251, 250, 250, 249, 248, 246
    .byte 245, 244, 243, 241, 240, 238, 237, 235
    .byte 234, 232, 230, 228, 226, 224, 222, 220
    .byte 218, 215, 213, 211, 208, 206, 203, 201
    .byte 198, 196, 193, 190, 188, 185, 182, 179
    .byte 176, 173, 170, 167, 165, 162, 158, 155
    .byte 152, 149, 146, 143, 140, 137, 134, 131
    .byte 128, 124, 121, 118, 115, 112, 109, 106
    .byte 103, 100,  97,  93,  90,  88,  85,  82
    .byte  79,  76,  73,  70,  67,  65,  62,  59
    .byte  57,  54,  52,  49,  47,  44,  42,  40
    .byte  37,  35,  33,  31,  29,  27,  25,  23
    .byte  21,  20,  18,  17,  15,  14,  12,  11
    .byte  10,   9,   7,   6,   5,   5,   4,   3
    .byte   2,   2,   1,   1,   1,   0,   0,   0
    .byte   0,   0,   0,   0,   1,   1,   1,   2
    .byte   2,   3,   4,   5,   5,   6,   7,   9
    .byte  10,  11,  12,  14,  15,  17,  18,  20
    .byte  21,  23,  25,  27,  29,  31,  33,  35
    .byte  37,  40,  42,  44,  47,  49,  52,  54
    .byte  57,  59,  62,  65,  67,  70,  73,  76
    .byte  79,  82,  85,  88,  90,  93,  97, 100
    .byte 103, 106, 109, 112, 115, 118, 121, 124

; -----------------------------------------------------------------------------
; cosine_table - Just offset sine by 64 (90 degrees)
; For convenience, separate table or use: cos(x) = sin(x + 64)
; -----------------------------------------------------------------------------
cosine_table:
    .byte 255, 255, 255, 255, 254, 254, 254, 253
    .byte 253, 252, 251, 250, 250, 249, 248, 246
    .byte 245, 244, 243, 241, 240, 238, 237, 235
    .byte 234, 232, 230, 228, 226, 224, 222, 220
    .byte 218, 215, 213, 211, 208, 206, 203, 201
    .byte 198, 196, 193, 190, 188, 185, 182, 179
    .byte 176, 173, 170, 167, 165, 162, 158, 155
    .byte 152, 149, 146, 143, 140, 137, 134, 131
    .byte 128, 124, 121, 118, 115, 112, 109, 106
    .byte 103, 100,  97,  93,  90,  88,  85,  82
    .byte  79,  76,  73,  70,  67,  65,  62,  59
    .byte  57,  54,  52,  49,  47,  44,  42,  40
    .byte  37,  35,  33,  31,  29,  27,  25,  23
    .byte  21,  20,  18,  17,  15,  14,  12,  11
    .byte  10,   9,   7,   6,   5,   5,   4,   3
    .byte   2,   2,   1,   1,   1,   0,   0,   0
    .byte   0,   0,   0,   0,   1,   1,   1,   2
    .byte   2,   3,   4,   5,   5,   6,   7,   9
    .byte  10,  11,  12,  14,  15,  17,  18,  20
    .byte  21,  23,  25,  27,  29,  31,  33,  35
    .byte  37,  40,  42,  44,  47,  49,  52,  54
    .byte  57,  59,  62,  65,  67,  70,  73,  76
    .byte  79,  82,  85,  88,  90,  93,  97, 100
    .byte 103, 106, 109, 112, 115, 118, 121, 124
    .byte 128, 131, 134, 137, 140, 143, 146, 149
    .byte 152, 155, 158, 162, 165, 167, 170, 173
    .byte 176, 179, 182, 185, 188, 190, 193, 196
    .byte 198, 201, 203, 206, 208, 211, 213, 215
    .byte 218, 220, 222, 224, 226, 228, 230, 232
    .byte 234, 235, 237, 238, 240, 241, 243, 244
    .byte 245, 246, 248, 249, 250, 250, 251, 252
    .byte 253, 253, 254, 254, 254, 255, 255, 255

; -----------------------------------------------------------------------------
; signed_sine_table - Values -128 to +127 (actual signed format)
; Useful for direct velocity application
; -----------------------------------------------------------------------------
signed_sine_table:
    .byte   0,   3,   6,   9,  12,  15,  18,  21
    .byte  24,  27,  30,  34,  37,  39,  42,  45
    .byte  48,  51,  54,  57,  60,  62,  65,  68
    .byte  70,  73,  75,  78,  80,  83,  85,  87
    .byte  90,  92,  94,  96,  98, 100, 102, 104
    .byte 106, 107, 109, 110, 112, 113, 115, 116
    .byte 117, 118, 120, 121, 122, 122, 123, 124
    .byte 125, 125, 126, 126, 126, 127, 127, 127
    .byte 127, 127, 127, 127, 126, 126, 126, 125
    .byte 125, 124, 123, 122, 122, 121, 120, 118
    .byte 117, 116, 115, 113, 112, 110, 109, 107
    .byte 106, 104, 102, 100,  98,  96,  94,  92
    .byte  90,  87,  85,  83,  80,  78,  75,  73
    .byte  70,  68,  65,  62,  60,  57,  54,  51
    .byte  48,  45,  42,  39,  37,  34,  30,  27
    .byte  24,  21,  18,  15,  12,   9,   6,   3
    .byte   0,  -3,  -6,  -9, -12, -15, -18, -21
    .byte -24, -27, -30, -34, -37, -39, -42, -45
    .byte -48, -51, -54, -57, -60, -62, -65, -68
    .byte -70, -73, -75, -78, -80, -83, -85, -87
    .byte -90, -92, -94, -96, -98,-100,-102,-104
    .byte -106,-107,-109,-110,-112,-113,-115,-116
    .byte -117,-118,-120,-121,-122,-122,-123,-124
    .byte -125,-125,-126,-126,-126,-127,-127,-127
    .byte -128,-127,-127,-127,-126,-126,-126,-125
    .byte -125,-124,-123,-122,-122,-121,-120,-118
    .byte -117,-116,-115,-113,-112,-110,-109,-107
    .byte -106,-104,-102,-100, -98, -96, -94, -92
    .byte -90, -87, -85, -83, -80, -78, -75, -73
    .byte -70, -68, -65, -62, -60, -57, -54, -51
    .byte -48, -45, -42, -39, -37, -34, -30, -27
    .byte -24, -21, -18, -15, -12,  -9,  -6,  -3

.segment "CODE"

; -----------------------------------------------------------------------------
; get_sine - Get sine value
; Input: A = angle (0-255, 256 = full circle)
; Output: A = sine value (128 = 0, 255 = +1, 0 = -1)
; -----------------------------------------------------------------------------
.proc get_sine
    tax
    lda sine_table, x
    rts
.endproc

; -----------------------------------------------------------------------------
; get_cosine - Get cosine value
; Input: A = angle
; Output: A = cosine value
; -----------------------------------------------------------------------------
.proc get_cosine
    clc
    adc #64                      ; cos(x) = sin(x + 90)
    tax
    lda sine_table, x
    rts
.endproc

; -----------------------------------------------------------------------------
; get_signed_sine - Get signed sine (-128 to +127)
; Input: A = angle
; Output: A = signed sine value
; -----------------------------------------------------------------------------
.proc get_signed_sine
    tax
    lda signed_sine_table, x
    rts
.endproc

; =============================================================================
; CIRCULAR MOTION HELPER
; =============================================================================

.segment "ZEROPAGE"
circle_angle:       .res 1       ; Current angle
circle_radius:      .res 1       ; Radius in pixels
circle_center_x:    .res 1       ; Center X
circle_center_y:    .res 1       ; Center Y

.segment "CODE"

; -----------------------------------------------------------------------------
; calc_circle_pos - Calculate position on circle
; Input: Set circle_* variables
; Output: X = x position, Y = y position
; -----------------------------------------------------------------------------
.proc calc_circle_pos
    ; X = center_x + radius * cos(angle)
    lda circle_angle
    jsr get_cosine               ; A = cos (0-255)
    sec
    sbc #128                     ; Convert to signed (-128 to +127)
    sta temp_cos

    ; Multiply by radius
    lda temp_cos
    bpl @pos_x
    eor #$FF
    clc
    adc #1                       ; Absolute value
@pos_x:
    ldx circle_radius
    jsr mul_8x8_16               ; A * X = result
    lda temp_cos
    bpl @add_x
    lda math_result_lo
    eor #$FF
    clc
    adc #1
    sta math_result_lo
@add_x:
    lda circle_center_x
    clc
    adc math_result_lo
    sta result_x

    ; Y = center_y + radius * sin(angle)
    lda circle_angle
    jsr get_sine
    sec
    sbc #128
    sta temp_sin

    lda temp_sin
    bpl @pos_y
    eor #$FF
    clc
    adc #1
@pos_y:
    ldx circle_radius
    jsr mul_8x8_16
    lda temp_sin
    bpl @add_y
    lda math_result_lo
    eor #$FF
    clc
    adc #1
    sta math_result_lo
@add_y:
    lda circle_center_y
    clc
    adc math_result_lo
    sta result_y

    ldx result_x
    ldy result_y
    rts

temp_cos:  .byte 0
temp_sin:  .byte 0
result_x:  .byte 0
result_y:  .byte 0
.endproc

; =============================================================================
; USAGE EXAMPLES:
; =============================================================================
;
; ; Orbiting enemy around player:
;   lda #128
;   sta circle_center_x      ; Player X
;   lda #120
;   sta circle_center_y      ; Player Y
;   lda #32
;   sta circle_radius        ; 32 pixel radius
;   lda frame_counter        ; Use frame counter as angle
;   sta circle_angle
;   jsr calc_circle_pos      ; X, Y = orbit position
;   stx enemy_x
;   sty enemy_y
;
; ; Wave motion (bobbing):
;   lda frame_counter
;   asl                      ; Double speed
;   tax
;   lda sine_table, x        ; Get sine
;   sec
;   sbc #128                 ; Center at 0
;   asr                      ; Divide by 4 for subtle motion
;   asr
;   clc
;   adc base_y               ; Add to base position
;   sta sprite_y
;
; ; 8-direction movement using angle:
;   lda player_direction     ; 0-255
;   jsr get_signed_sine
;   sta player_vy            ; Vertical velocity
;   lda player_direction
;   clc
;   adc #64
;   jsr get_signed_sine
;   sta player_vx            ; Horizontal velocity
;
; =============================================================================
