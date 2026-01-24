; =============================================================================
; PALETTE FADE EFFECTS - Fade in, fade out, flash
; =============================================================================
; NES palettes are 6-bit values ($00-$3F)
; Brightness controlled by upper 2 bits: $0x=dark, $1x=normal, $2x=bright, $3x=white
; Fade by adjusting brightness levels
; =============================================================================

.segment "ZEROPAGE"
fade_level:         .res 1       ; Current fade level (0=black, 4=full)
fade_target:        .res 1       ; Target fade level
fade_speed:         .res 1       ; Frames between fade steps
fade_counter:       .res 1       ; Frame counter
fade_active:        .res 1       ; Non-zero if fading

.segment "BSS"
original_palette:   .res 32      ; Store original palette for fading
faded_palette:      .res 32      ; Calculated faded palette

.segment "CODE"

; -----------------------------------------------------------------------------
; init_fade - Initialize fade system with current palette
; Input: Palette data at pal_buffer (32 bytes)
; -----------------------------------------------------------------------------
.proc init_fade
    ; Copy current palette as original
    ldx #31
@copy:
    lda pal_buffer, x
    sta original_palette, x
    dex
    bpl @copy

    lda #4                       ; Full brightness
    sta fade_level
    sta fade_target
    lda #0
    sta fade_active

    rts
.endproc

; -----------------------------------------------------------------------------
; start_fade_out - Begin fade to black
; Input: A = speed (frames per step, 1=fast, 8=slow)
; -----------------------------------------------------------------------------
.proc start_fade_out
    sta fade_speed
    sta fade_counter
    lda #0
    sta fade_target
    lda #1
    sta fade_active
    rts
.endproc

; -----------------------------------------------------------------------------
; start_fade_in - Begin fade from black to full
; Input: A = speed (frames per step)
; -----------------------------------------------------------------------------
.proc start_fade_in
    sta fade_speed
    sta fade_counter
    lda #0
    sta fade_level               ; Start from black
    lda #4
    sta fade_target
    lda #1
    sta fade_active
    jsr calculate_faded_palette  ; Apply immediate black
    rts
.endproc

; -----------------------------------------------------------------------------
; update_fade - Call every frame
; Returns: A = 1 if still fading, 0 if done
; -----------------------------------------------------------------------------
.proc update_fade
    lda fade_active
    beq @done_inactive

    ; Count down frames
    dec fade_counter
    bne @still_waiting

    ; Reset counter
    lda fade_speed
    sta fade_counter

    ; Step toward target
    lda fade_level
    cmp fade_target
    beq @reached_target
    bcc @fade_up

@fade_down:
    dec fade_level
    jmp @apply

@fade_up:
    inc fade_level

@apply:
    jsr calculate_faded_palette

    lda #1
    rts

@reached_target:
    lda #0
    sta fade_active

@done_inactive:
    lda #0
    rts

@still_waiting:
    lda #1
    rts
.endproc

; -----------------------------------------------------------------------------
; calculate_faded_palette - Apply fade_level to original_palette
; fade_level: 0=black, 1=very dark, 2=dark, 3=normal, 4=full
; -----------------------------------------------------------------------------
.proc calculate_faded_palette
    ldx #31

@loop:
    lda fade_level
    beq @black                   ; Level 0 = all black

    lda original_palette, x
    cmp #$0F                     ; Skip if already black
    beq @store

    ; Extract hue (lower 4 bits)
    and #$0F
    sta temp_hue

    ; Get original brightness (upper 2 bits / 16)
    lda original_palette, x
    lsr
    lsr
    lsr
    lsr                          ; Now 0-3

    ; Adjust brightness based on fade level
    ; fade_level 4 = no change
    ; fade_level 3 = -1 brightness
    ; fade_level 2 = -2 brightness
    ; fade_level 1 = -3 brightness
    sec
    sbc #4
    clc
    adc fade_level               ; Adjusted brightness

    bpl @not_negative
    lda #0                       ; Clamp to 0
@not_negative:
    cmp #4
    bcc @in_range
    lda #3                       ; Clamp to 3
@in_range:

    ; Reconstruct palette entry
    asl
    asl
    asl
    asl                          ; Move to upper nibble
    ora temp_hue
    jmp @store

@black:
    lda #$0F                     ; NES black

@store:
    sta faded_palette, x
    dex
    bpl @loop

    ; Copy faded palette to PPU buffer
    ldx #31
@copy_to_buffer:
    lda faded_palette, x
    sta pal_buffer, x
    dex
    bpl @copy_to_buffer

    rts

temp_hue: .byte 0
.endproc

; -----------------------------------------------------------------------------
; flash_palette - Quick white flash (hit effect, etc.)
; Input: A = flash intensity (1-4)
; -----------------------------------------------------------------------------
.proc flash_palette
    sta temp_intensity

    ldx #31
@loop:
    lda original_palette, x
    cmp #$0F
    beq @skip                    ; Don't flash black

    ; Add intensity to brightness
    and #$F0
    lsr
    lsr
    lsr
    lsr
    clc
    adc temp_intensity
    cmp #4
    bcc @ok
    lda #3                       ; Max brightness
@ok:
    asl
    asl
    asl
    asl
    sta temp_bright

    lda original_palette, x
    and #$0F
    ora temp_bright
    sta pal_buffer, x
    jmp @next

@skip:
    lda #$0F
    sta pal_buffer, x

@next:
    dex
    bpl @loop
    rts

temp_intensity: .byte 0
temp_bright:    .byte 0
.endproc

; =============================================================================
; USAGE EXAMPLES:
; =============================================================================
;
; ; Initialize at game start:
;   jsr init_fade
;
; ; Fade out (scene transition):
;   lda #4                ; Speed: 4 frames per step
;   jsr start_fade_out
;
; ; In main loop:
;   jsr update_fade       ; Returns A=1 if still fading
;   beq @fade_complete
;
; ; Quick hit flash:
;   lda #2
;   jsr flash_palette
;
; ; Fade in from black:
;   lda #3
;   jsr start_fade_in
;
; =============================================================================
