; =============================================================================
; SCREEN SHAKE & CAMERA EFFECTS
; =============================================================================
; Techniques: Scroll offset shake, horizontal jitter, impact effects
; Used in: Beat-em-ups, action games, explosions
; =============================================================================

.segment "ZEROPAGE"

; Shake state
shake_intensity:    .res 1       ; Current shake amount (pixels)
shake_duration:     .res 1       ; Frames remaining
shake_decay:        .res 1       ; How fast shake diminishes
shake_offset_x:     .res 1       ; Current X offset (signed)
shake_offset_y:     .res 1       ; Current Y offset (signed)

; Camera state
camera_x:           .res 2       ; 16-bit camera X
camera_y:           .res 2       ; 16-bit camera Y
camera_target_x:    .res 2       ; Where camera wants to be
camera_target_y:    .res 2
camera_speed:       .res 1       ; How fast camera moves to target

; Scroll output (what actually gets written to PPU)
final_scroll_x:     .res 1
final_scroll_y:     .res 1

.segment "CODE"

; =============================================================================
; SCREEN SHAKE
; =============================================================================

; -----------------------------------------------------------------------------
; start_shake - Begin screen shake effect
; Input: A = intensity (pixels), X = duration (frames)
; -----------------------------------------------------------------------------
.proc start_shake
    sta shake_intensity
    stx shake_duration

    ; Default decay rate
    lda #1
    sta shake_decay

    rts
.endproc

; -----------------------------------------------------------------------------
; start_shake_big - Dramatic shake (boss death, big explosion)
; -----------------------------------------------------------------------------
.proc start_shake_big
    lda #8                       ; 8 pixel intensity
    ldx #30                      ; Half second
    jsr start_shake
    lda #0                       ; No decay (full intensity throughout)
    sta shake_decay
    rts
.endproc

; -----------------------------------------------------------------------------
; start_shake_small - Light shake (hit, small explosion)
; -----------------------------------------------------------------------------
.proc start_shake_small
    lda #2                       ; 2 pixel intensity
    ldx #8                       ; ~8 frames
    jsr start_shake
    lda #1                       ; Quick decay
    sta shake_decay
    rts
.endproc

; -----------------------------------------------------------------------------
; update_shake - Update shake effect (call every frame)
; Output: shake_offset_x/y updated
; -----------------------------------------------------------------------------
.proc update_shake
    ; Check if shake active
    lda shake_duration
    beq @no_shake

    ; Generate random offset based on intensity
    jsr rand8_fast               ; Assumes RNG available
    and shake_intensity          ; Mask to intensity
    sta temp_offset

    ; Make it signed (-intensity to +intensity)
    jsr rand8_fast
    and #$01                     ; Random sign
    beq @positive_x
    lda temp_offset
    eor #$FF
    clc
    adc #1                       ; Negate
    sta temp_offset
@positive_x:
    lda temp_offset
    sta shake_offset_x

    ; Y offset (usually smaller or zero for horizontal shake)
    lda shake_intensity
    lsr                          ; Half intensity for Y
    sta temp_offset

    jsr rand8_fast
    and temp_offset
    sta temp_offset

    jsr rand8_fast
    and #$01
    beq @positive_y
    lda temp_offset
    eor #$FF
    clc
    adc #1
    sta temp_offset
@positive_y:
    lda temp_offset
    sta shake_offset_y

    ; Decay
    dec shake_duration
    beq @done

    ; Apply decay to intensity
    lda shake_decay
    beq @done                    ; No decay
    lda shake_intensity
    sec
    sbc shake_decay
    bcs @store_intensity
    lda #0                       ; Clamp to 0
@store_intensity:
    sta shake_intensity

@done:
    rts

@no_shake:
    lda #0
    sta shake_offset_x
    sta shake_offset_y
    rts

temp_offset: .byte 0
.endproc

; =============================================================================
; SMOOTH CAMERA
; =============================================================================

; -----------------------------------------------------------------------------
; init_camera - Initialize camera system
; Input: A/X = initial X position (16-bit), Y/? = initial Y
; -----------------------------------------------------------------------------
.proc init_camera
    sta camera_x
    stx camera_x+1
    sta camera_target_x
    stx camera_target_x+1

    ; Default speed
    lda #8                       ; ~1/8th of distance per frame
    sta camera_speed

    rts
.endproc

; -----------------------------------------------------------------------------
; set_camera_target - Set where camera should move to
; Input: A/X = target X (16-bit)
; -----------------------------------------------------------------------------
.proc set_camera_target
    sta camera_target_x
    stx camera_target_x+1
    rts
.endproc

; -----------------------------------------------------------------------------
; update_camera - Smooth camera follow (call every frame)
; Lerps camera toward target
; -----------------------------------------------------------------------------
.proc update_camera
    ; X axis: camera_x += (target_x - camera_x) / speed

    ; Calculate difference
    lda camera_target_x
    sec
    sbc camera_x
    sta diff_lo
    lda camera_target_x+1
    sbc camera_x+1
    sta diff_hi

    ; Divide by speed (shift right)
    ldx camera_speed
@div_loop:
    cpx #1
    beq @apply_x
    lda diff_hi
    cmp #$80                     ; Check sign for arithmetic shift
    ror diff_hi
    ror diff_lo
    dex
    dex                          ; Divide by 2 each iteration
    bne @div_loop

@apply_x:
    ; Add to camera
    lda camera_x
    clc
    adc diff_lo
    sta camera_x
    lda camera_x+1
    adc diff_hi
    sta camera_x+1

    ; Same for Y (if needed)
    ; ... similar code for camera_y ...

    rts

diff_lo: .byte 0
diff_hi: .byte 0
.endproc

; -----------------------------------------------------------------------------
; camera_follow_player - Common pattern: center on player
; Input: Player position in player_x (16-bit)
; -----------------------------------------------------------------------------
.proc camera_follow_player
    ; Target = player_x - 128 (center of screen)
    lda player_x
    sec
    sbc #128
    sta camera_target_x
    lda player_x+1
    sbc #0
    sta camera_target_x+1

    ; Clamp to level bounds
    ; ... add bounds checking ...

    jsr update_camera
    rts

player_x: .res 2                 ; Would be in ZEROPAGE normally
.endproc

; =============================================================================
; FINAL SCROLL CALCULATION
; =============================================================================

; -----------------------------------------------------------------------------
; calc_final_scroll - Combine camera + shake for final scroll values
; Output: final_scroll_x/y ready to write to PPU
; -----------------------------------------------------------------------------
.proc calc_final_scroll
    ; Base scroll from camera (take low byte for PPU)
    lda camera_x
    clc
    adc shake_offset_x           ; Add shake offset (signed)
    sta final_scroll_x

    lda camera_y
    clc
    adc shake_offset_y
    sta final_scroll_y

    rts
.endproc

; -----------------------------------------------------------------------------
; apply_scroll - Write scroll to PPU (call during vblank)
; -----------------------------------------------------------------------------
.proc apply_scroll
    lda final_scroll_x
    sta $2005
    lda final_scroll_y
    sta $2005

    ; Also update $2000 for nametable selection based on scroll
    lda camera_x+1               ; High byte determines nametable
    and #$01                     ; Nametable 0 or 1
    ora #%10010000               ; NMI enable, 8x8 sprites, BG pattern 0
    sta $2000

    rts
.endproc

; =============================================================================
; SPECIAL EFFECTS
; =============================================================================

; -----------------------------------------------------------------------------
; hitstop - Freeze game briefly for impact (fighting game technique)
; Input: A = frames to freeze
; -----------------------------------------------------------------------------
.segment "ZEROPAGE"
hitstop_counter:    .res 1

.segment "CODE"

.proc start_hitstop
    sta hitstop_counter
    rts
.endproc

.proc check_hitstop
    lda hitstop_counter
    beq @not_frozen
    dec hitstop_counter
    sec                          ; Return: frozen
    rts
@not_frozen:
    clc                          ; Return: not frozen
    rts
.endproc

; -----------------------------------------------------------------------------
; zoom_effect - Pseudo-zoom using palette tricks
; Changes brightness to simulate distance
; -----------------------------------------------------------------------------
.proc start_zoom_in
    ; Brighten palette over several frames
    ; Implementation depends on your palette system
    rts
.endproc

; =============================================================================
; USAGE EXAMPLE
; =============================================================================
;
; ; Game init:
;   jsr init_camera
;
; ; When player gets hit:
;   jsr start_shake_small
;   lda #3
;   jsr start_hitstop
;
; ; When boss dies:
;   jsr start_shake_big
;
; ; Every frame (main loop):
;   jsr check_hitstop
;   bcs @skip_update             ; Skip game logic if frozen
;
;   jsr update_game
;   jsr camera_follow_player
;
; @skip_update:
;   jsr update_shake
;   jsr calc_final_scroll
;
; ; In NMI:
;   jsr apply_scroll
;
; =============================================================================
