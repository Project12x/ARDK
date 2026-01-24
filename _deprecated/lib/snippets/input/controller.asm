; =============================================================================
; CONTROLLER INPUT - Full input handling with edge detection
; =============================================================================
; Handles: Standard controllers, Turbo, Hold detection, Combos
; =============================================================================

.segment "ZEROPAGE"

; Controller 1 state
pad1_current:       .res 1       ; Currently held buttons
pad1_previous:      .res 1       ; Previous frame buttons
pad1_pressed:       .res 1       ; Just pressed this frame
pad1_released:      .res 1       ; Just released this frame
pad1_hold_timer:    .res 1       ; Frames button held

; Controller 2 state
pad2_current:       .res 1
pad2_previous:      .res 1
pad2_pressed:       .res 1
pad2_released:      .res 1

; Button constants
BTN_A       = %10000000
BTN_B       = %01000000
BTN_SELECT  = %00100000
BTN_START   = %00010000
BTN_UP      = %00001000
BTN_DOWN    = %00000100
BTN_LEFT    = %00000010
BTN_RIGHT   = %00000001

; Directional masks
BTN_DPAD    = BTN_UP | BTN_DOWN | BTN_LEFT | BTN_RIGHT

.segment "CODE"

; -----------------------------------------------------------------------------
; read_controllers - Read both controllers with debouncing
; Call once per frame, early in main loop
; -----------------------------------------------------------------------------
.proc read_controllers
    ; Save previous state
    lda pad1_current
    sta pad1_previous
    lda pad2_current
    sta pad2_previous

    ; Read controller 1
    jsr read_pad1
    sta pad1_current

    ; Read controller 2
    jsr read_pad2
    sta pad2_current

    ; Calculate pressed (just pressed this frame)
    lda pad1_current
    eor pad1_previous            ; Changed bits
    and pad1_current             ; Only newly pressed
    sta pad1_pressed

    ; Calculate released (just released this frame)
    lda pad1_current
    eor pad1_previous            ; Changed bits
    and pad1_previous            ; Only newly released
    sta pad1_released

    ; Same for pad 2
    lda pad2_current
    eor pad2_previous
    and pad2_current
    sta pad2_pressed

    lda pad2_current
    eor pad2_previous
    and pad2_previous
    sta pad2_released

    ; Update hold timer
    lda pad1_current
    beq @reset_hold
    inc pad1_hold_timer
    lda pad1_hold_timer
    cmp #255
    bcc @done
    lda #255                     ; Cap at 255
    sta pad1_hold_timer
    bne @done

@reset_hold:
    lda #0
    sta pad1_hold_timer

@done:
    rts
.endproc

; -----------------------------------------------------------------------------
; read_pad1 - Raw read of controller 1
; Output: A = button state
; -----------------------------------------------------------------------------
.proc read_pad1
    ; Strobe controller
    lda #$01
    sta $4016
    lda #$00
    sta $4016

    ; Read 8 buttons
    ldx #8
    lda #0
@loop:
    pha
    lda $4016
    and #%00000011               ; Handle both standard and clones
    cmp #1
    pla
    ror                          ; Rotate carry into result
    dex
    bne @loop

    rts
.endproc

; -----------------------------------------------------------------------------
; read_pad2 - Raw read of controller 2
; Output: A = button state
; -----------------------------------------------------------------------------
.proc read_pad2
    lda #$01
    sta $4016
    lda #$00
    sta $4016

    ldx #8
    lda #0
@loop:
    pha
    lda $4017                    ; Port $4017 for controller 2
    and #%00000011
    cmp #1
    pla
    ror
    dex
    bne @loop

    rts
.endproc

; -----------------------------------------------------------------------------
; HELPER FUNCTIONS
; -----------------------------------------------------------------------------

; -----------------------------------------------------------------------------
; is_pressed - Check if button was just pressed
; Input: A = button mask
; Output: Z flag (BEQ = pressed)
; -----------------------------------------------------------------------------
.proc is_pressed
    and pad1_pressed
    rts
.endproc

; -----------------------------------------------------------------------------
; is_held - Check if button is currently held
; Input: A = button mask
; Output: Z flag (BEQ = held)
; -----------------------------------------------------------------------------
.proc is_held
    and pad1_current
    rts
.endproc

; -----------------------------------------------------------------------------
; is_released - Check if button was just released
; Input: A = button mask
; Output: Z flag
; -----------------------------------------------------------------------------
.proc is_released
    and pad1_released
    rts
.endproc

; -----------------------------------------------------------------------------
; get_dpad_direction - Get D-pad as 0-7 direction (or 8 for none)
; Output: A = direction (0=up, 1=up-right, 2=right, ... 7=up-left, 8=none)
; -----------------------------------------------------------------------------
.proc get_dpad_direction
    lda pad1_current
    and #BTN_DPAD

    ; Quick lookup using table
    tax
    lda dpad_direction_table, x
    rts

dpad_direction_table:
    ; Indexed by UDLR bits
    .byte 8                      ; 0000 = none
    .byte 2                      ; 0001 = right
    .byte 6                      ; 0010 = left
    .byte 8                      ; 0011 = left+right (invalid)
    .byte 4                      ; 0100 = down
    .byte 3                      ; 0101 = down-right
    .byte 5                      ; 0110 = down-left
    .byte 4                      ; 0111 = down (left+right cancel)
    .byte 0                      ; 1000 = up
    .byte 1                      ; 1001 = up-right
    .byte 7                      ; 1010 = up-left
    .byte 0                      ; 1011 = up (left+right cancel)
    .byte 8                      ; 1100 = up+down (invalid)
    .byte 2                      ; 1101 = right (up+down cancel)
    .byte 6                      ; 1110 = left (up+down cancel)
    .byte 8                      ; 1111 = all (invalid)
.endproc

; =============================================================================
; ADVANCED INPUT FEATURES
; =============================================================================

.segment "ZEROPAGE"
turbo_counter:      .res 1       ; For turbo/autofire

.segment "CODE"

; -----------------------------------------------------------------------------
; is_turbo_pressed - Auto-repeat while held (for shooting)
; Input: A = button mask
; Output: Z flag (BEQ = "pressed" this frame)
; Turbo rate: Every 4 frames
; -----------------------------------------------------------------------------
.proc is_turbo_pressed
    sta temp_mask

    ; Check if actually pressed this frame
    and pad1_pressed
    bne @yes                     ; Just pressed = yes

    ; Check if held and turbo timer elapsed
    lda temp_mask
    and pad1_current
    beq @no                      ; Not held

    ; Held - check turbo timer
    lda turbo_counter
    and #$03                     ; Every 4 frames
    bne @no

@yes:
    lda #0                       ; Z = 1
    rts

@no:
    lda #1                       ; Z = 0
    rts

temp_mask: .byte 0
.endproc

; -----------------------------------------------------------------------------
; check_hold_action - Trigger after holding for N frames
; Input: A = button mask, X = frames to hold
; Output: Carry set if hold threshold reached this frame
; Use for: Charge attacks, menu shortcuts
; -----------------------------------------------------------------------------
.proc check_hold_action
    sta temp_mask
    stx hold_threshold

    ; Must be held
    and pad1_current
    beq @no

    ; Check if we just hit the threshold
    lda pad1_hold_timer
    cmp hold_threshold
    bne @no

    sec                          ; Yes, trigger!
    rts

@no:
    clc
    rts

temp_mask:       .byte 0
hold_threshold:  .byte 0
.endproc

; =============================================================================
; COMBO INPUT (Street Fighter style)
; =============================================================================

.segment "BSS"
combo_buffer:       .res 16      ; Last 16 inputs
combo_buffer_idx:   .res 1       ; Current position
combo_timer:        .res 16      ; Time since each input

.segment "CODE"

; -----------------------------------------------------------------------------
; record_input - Add current input to combo buffer
; Call after read_controllers
; -----------------------------------------------------------------------------
.proc record_input
    lda pad1_pressed
    beq @done                    ; No new input

    ; Store in circular buffer
    ldx combo_buffer_idx
    sta combo_buffer, x

    lda #0
    sta combo_timer, x           ; Reset timer

    inx
    txa
    and #$0F                     ; Wrap at 16
    sta combo_buffer_idx

@done:
    ; Age all timers
    ldx #15
@age_loop:
    lda combo_timer, x
    cmp #255
    beq @skip
    inc combo_timer, x
@skip:
    dex
    bpl @age_loop

    rts
.endproc

; -----------------------------------------------------------------------------
; check_combo - Check if recent inputs match a combo
; Input: X = pointer to combo definition, Y = combo length
; Output: Carry set if combo matched
;
; Combo format: sequence of button presses, most recent last
; Time window: 30 frames between inputs
; -----------------------------------------------------------------------------
.proc check_combo
    stx combo_ptr
    sty combo_len

    ; Start from most recent input and work backwards
    lda combo_buffer_idx
    sec
    sbc combo_len
    and #$0F
    sta check_idx

    ldy #0                       ; Combo position

@check_loop:
    ; Get expected button from combo
    lda (combo_ptr), y
    sta expected_btn

    ; Get actual button from buffer
    ldx check_idx
    lda combo_buffer, x
    cmp expected_btn
    bne @fail                    ; Wrong button

    ; Check timing (must be within 30 frames)
    lda combo_timer, x
    cmp #30
    bcs @fail                    ; Too slow

    ; Next input
    inc check_idx
    lda check_idx
    and #$0F
    sta check_idx

    iny
    cpy combo_len
    bne @check_loop

    ; Success!
    sec
    rts

@fail:
    clc
    rts

combo_ptr:     .res 2
combo_len:     .byte 0
check_idx:     .byte 0
expected_btn:  .byte 0
.endproc

; =============================================================================
; EXAMPLE COMBOS
; =============================================================================

; Hadouken: Down, Down-Right, Right, A
combo_hadouken:
    .byte BTN_DOWN
    .byte BTN_DOWN | BTN_RIGHT
    .byte BTN_RIGHT
    .byte BTN_A
COMBO_HADOUKEN_LEN = 4

; Shoryuken: Right, Down, Down-Right, A
combo_shoryuken:
    .byte BTN_RIGHT
    .byte BTN_DOWN
    .byte BTN_DOWN | BTN_RIGHT
    .byte BTN_A
COMBO_SHORYUKEN_LEN = 4

; =============================================================================
; USAGE EXAMPLES:
; =============================================================================
;
; ; Basic input check:
;   jsr read_controllers
;
;   lda #BTN_A
;   jsr is_pressed
;   beq @a_just_pressed
;
;   lda #BTN_B
;   jsr is_held
;   bne @b_held
;
; ; Turbo fire (autofire while held):
;   lda #BTN_B
;   jsr is_turbo_pressed
;   beq @fire_bullet
;
; ; Charge attack (hold B for 60 frames):
;   lda #BTN_B
;   ldx #60
;   jsr check_hold_action
;   bcs @release_charge_attack
;
; ; 8-direction movement:
;   jsr get_dpad_direction
;   cmp #8
;   beq @no_movement
;   ; A = 0-7 direction
;
; ; Combo detection:
;   jsr record_input              ; Every frame
;   ldx #<combo_hadouken
;   ldy #COMBO_HADOUKEN_LEN
;   jsr check_combo
;   bcs @do_hadouken
;
; =============================================================================
