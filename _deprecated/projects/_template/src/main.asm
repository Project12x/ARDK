; =============================================================================
; PROJECT: [Project Name]
; main.asm - Game Entry Point
; =============================================================================
; This file is the entry point for your game. The ARDK engine handles:
;   - Hardware initialization (PPU, APU, RAM clear)
;   - Palette loading
;   - NMI/IRQ setup
;
; Your code starts at Game_Init and runs the main loop.
; =============================================================================

.include "nes.inc"          ; NES hardware definitions
.include "game_config.inc"  ; Project-specific configuration

; Import ARDK engine symbols
.import Reset               ; Engine entry point
.import nmi_flag            ; VBlank sync flag
.importzp buttons, buttons_pressed

; Export game entry points (called by engine)
.export Game_Init
.export Game_Update
.export Game_Render

; =============================================================================
; Zero Page Variables
; =============================================================================
.segment "ZEROPAGE"

; Player state
player_x:       .res 2      ; 8.8 fixed-point X position
player_y:       .res 2      ; 8.8 fixed-point Y position
player_vx:      .res 2      ; 8.8 fixed-point X velocity
player_vy:      .res 2      ; 8.8 fixed-point Y velocity
player_health:  .res 1      ; Current HP
player_state:   .res 1      ; Animation state

; Game state
game_state:     .res 1      ; Current game state
frame_counter:  .res 1      ; Animation timer

; =============================================================================
; Constants
; =============================================================================
PLAYER_SPEED    = 256       ; 1.0 pixels per frame (8.8 format)
PLAYER_START_X  = 128 * 256 ; Center of screen (8.8)
PLAYER_START_Y  = 120 * 256 ; Center of screen (8.8)

; Game states
STATE_TITLE     = 0
STATE_PLAYING   = 1
STATE_PAUSED    = 2
STATE_GAMEOVER  = 3

; =============================================================================
; Code
; =============================================================================
.segment "CODE"

; -----------------------------------------------------------------------------
; Game_Init - Called once at startup
; -----------------------------------------------------------------------------
.proc Game_Init
    ; Initialize player
    lda #<PLAYER_START_X
    sta player_x
    lda #>PLAYER_START_X
    sta player_x+1

    lda #<PLAYER_START_Y
    sta player_y
    lda #>PLAYER_START_Y
    sta player_y+1

    ; Clear velocity
    lda #0
    sta player_vx
    sta player_vx+1
    sta player_vy
    sta player_vy+1

    ; Set initial health
    lda #3
    sta player_health

    ; Start in playing state
    lda #STATE_PLAYING
    sta game_state

    rts
.endproc

; -----------------------------------------------------------------------------
; Game_Update - Called every frame (during active time)
; -----------------------------------------------------------------------------
.proc Game_Update
    ; Increment frame counter
    inc frame_counter

    ; Branch based on game state
    lda game_state
    cmp #STATE_PLAYING
    bne @done

    ; Handle input
    jsr Update_Player_Input

    ; Apply velocity to position
    jsr Update_Player_Position

    ; Update enemies, projectiles, etc.
    ; jsr Update_Enemies
    ; jsr Update_Projectiles

@done:
    rts
.endproc

; -----------------------------------------------------------------------------
; Game_Render - Called every frame (populates OAM)
; -----------------------------------------------------------------------------
.proc Game_Render
    ; Clear OAM (hide all sprites)
    ldx #0
    lda #$FF
@clear_oam:
    sta $0200, x
    inx
    bne @clear_oam

    ; Render player sprite
    jsr Render_Player

    ; Render enemies, projectiles, etc.
    ; jsr Render_Enemies
    ; jsr Render_Projectiles

    rts
.endproc

; -----------------------------------------------------------------------------
; Update_Player_Input - Read input and set velocity
; -----------------------------------------------------------------------------
.proc Update_Player_Input
    ; Reset velocity
    lda #0
    sta player_vx
    sta player_vx+1
    sta player_vy
    sta player_vy+1

    ; Check D-pad
    lda buttons

    ; Right
    ldx buttons
    txa
    and #BTN_RIGHT
    beq @check_left
    lda #<PLAYER_SPEED
    sta player_vx
    lda #>PLAYER_SPEED
    sta player_vx+1
    jmp @check_up

@check_left:
    txa
    and #BTN_LEFT
    beq @check_up
    ; Negative velocity
    lda #<(-PLAYER_SPEED)
    sta player_vx
    lda #>(-PLAYER_SPEED)
    sta player_vx+1

@check_up:
    txa
    and #BTN_UP
    beq @check_down
    lda #<(-PLAYER_SPEED)
    sta player_vy
    lda #>(-PLAYER_SPEED)
    sta player_vy+1
    jmp @done

@check_down:
    txa
    and #BTN_DOWN
    beq @done
    lda #<PLAYER_SPEED
    sta player_vy
    lda #>PLAYER_SPEED
    sta player_vy+1

@done:
    rts
.endproc

; -----------------------------------------------------------------------------
; Update_Player_Position - Apply velocity to position
; -----------------------------------------------------------------------------
.proc Update_Player_Position
    ; X position += X velocity
    clc
    lda player_x
    adc player_vx
    sta player_x
    lda player_x+1
    adc player_vx+1
    sta player_x+1

    ; Y position += Y velocity
    clc
    lda player_y
    adc player_vy
    sta player_y
    lda player_y+1
    adc player_vy+1
    sta player_y+1

    ; TODO: Screen boundary clamping

    rts
.endproc

; -----------------------------------------------------------------------------
; Render_Player - Draw player sprite to OAM
; -----------------------------------------------------------------------------
.proc Render_Player
    ; Get pixel position (high byte of 8.8 fixed point)
    lda player_y+1
    sta $0200           ; Y position (sprite 0)
    lda #$00            ; Tile index
    sta $0201
    lda #$00            ; Attributes (palette 0, no flip)
    sta $0202
    lda player_x+1
    sta $0203           ; X position

    rts
.endproc
