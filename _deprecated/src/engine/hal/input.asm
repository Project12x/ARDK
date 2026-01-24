; =============================================================================
; NEON SURVIVORS - Gamepad Input
; Platform-specific controller reading (NES version)
; =============================================================================
;
; PORTABILITY: This file is NES-specific.
; When porting, replace with platform-specific input reading that returns
; the same button mask format in the 'buttons' variable.
;
; HAL-compatible button mask format (matches hal/hal.h HAL_BTN_*):
;   Bit 0: A      (HAL_BTN_A      = 0x0001)
;   Bit 1: B      (HAL_BTN_B      = 0x0002)
;   Bit 2: Select (HAL_BTN_SELECT = 0x0004)
;   Bit 3: Start  (HAL_BTN_START  = 0x0008)
;   Bit 4: Up     (HAL_BTN_UP     = 0x0010)
;   Bit 5: Down   (HAL_BTN_DOWN   = 0x0020)
;   Bit 6: Left   (HAL_BTN_LEFT   = 0x0040)
;   Bit 7: Right  (HAL_BTN_RIGHT  = 0x0080)
;
; NES hardware reads in opposite order (A=bit7, Right=bit0), so we remap.
; =============================================================================

.include "nes.inc"

.segment "ZEROPAGE"

; Controller state (shared with main.asm)
.exportzp buttons, buttons_old, buttons_pressed

buttons:        .res 1      ; Current frame button state
buttons_old:    .res 1      ; Previous frame
buttons_pressed:.res 1      ; Newly pressed this frame (alias for buttons_new)

; Second controller (if needed)
buttons_p2:     .res 1
buttons_old_p2: .res 1
buttons_new_p2: .res 1

.segment "CODE"

; -----------------------------------------------------------------------------
; Input Read - Main Entry Point
; Exported for game code
; -----------------------------------------------------------------------------
.export input_read
.proc input_read
    jmp read_gamepad_p1  ; Just read P1 for now
.endproc

; -----------------------------------------------------------------------------
; Read Both Controllers
; Updates buttons, buttons_old, buttons_pressed for both players
; -----------------------------------------------------------------------------
.export read_gamepads
.proc read_gamepads
    jsr read_gamepad_p1
    jsr read_gamepad_p2
    rts
.endproc

; -----------------------------------------------------------------------------
; Read Player 1 Controller
; Reads raw NES format and remaps to HAL format
; -----------------------------------------------------------------------------
.proc read_gamepad_p1
    ; Save old state
    lda buttons
    sta buttons_old

    ; Strobe controller
    lda #1
    sta JOYPAD1
    lda #0
    sta JOYPAD1

    ; Read 8 buttons into raw NES format (A=bit7, Right=bit0)
    ldx #8
    lda #0
@loop:
    pha
    lda JOYPAD1
    and #%00000011          ; Handle Famicom expansion port
    cmp #1
    pla
    ror a                   ; Rotate carry into result
    dex
    bne @loop

    ; A now contains raw NES format: A B Sel Sta U D L R (bits 7-0)
    ; Need HAL format: R L D U Sta Sel B A (bits 7-0)
    ; This is a simple bit reversal
    jsr reverse_bits

    sta buttons

    ; Calculate newly pressed
    eor buttons_old
    and buttons
    sta buttons_pressed

    rts
.endproc

; -----------------------------------------------------------------------------
; Reverse Bits in A
; Converts NES hardware order to HAL format
; Input:  A = bits in order 76543210
; Output: A = bits in order 01234567
; -----------------------------------------------------------------------------
.proc reverse_bits
    ; Use a lookup table for fast reversal (could also do shift loop)
    ; For now, use shift method (smaller code, ~40 cycles)
    ldx #8
    sta @temp
    lda #0
@rev_loop:
    asl @temp           ; Shift MSB of temp into carry
    ror a               ; Rotate carry into MSB of result
    dex
    bne @rev_loop
    rts
@temp: .byte 0
.endproc

; -----------------------------------------------------------------------------
; Read Player 2 Controller
; Reads raw NES format and remaps to HAL format
; -----------------------------------------------------------------------------
.proc read_gamepad_p2
    lda buttons_p2
    sta buttons_old_p2

    lda #1
    sta JOYPAD1
    lda #0
    sta JOYPAD1

    ldx #8
    lda #0
@loop:
    pha
    lda JOYPAD2
    and #%00000011
    cmp #1
    pla
    ror a
    dex
    bne @loop

    ; Remap to HAL format
    jsr reverse_bits

    sta buttons_p2

    eor buttons_old_p2
    and buttons_p2
    sta buttons_new_p2

    rts
.endproc

; -----------------------------------------------------------------------------
; Check if Button Held
; Input: A = button mask to check
; Output: Carry = 1 if all specified buttons are held
; -----------------------------------------------------------------------------
.proc is_button_held
    and buttons
    cmp buttons             ; Will set carry if match
    beq @held
    clc
    rts
@held:
    sec
    rts
.endproc

; -----------------------------------------------------------------------------
; Check if Button Just Pressed
; Input: A = button mask to check
; Output: Carry = 1 if pressed this frame (wasn't held last frame)
; -----------------------------------------------------------------------------
.proc is_button_pressed
    and buttons_pressed
    beq @not_pressed
    sec
    rts
@not_pressed:
    clc
    rts
.endproc
