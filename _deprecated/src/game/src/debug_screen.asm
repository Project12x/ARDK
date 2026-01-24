; =============================================================================
; NEON SURVIVORS - Debug/Test Screen
; Boot screen for testing assets, audio, and engine systems
; =============================================================================

.include "../../engine/engine.inc"
.include "../assets/sprite_tiles.inc"

.export Debug_Init, Debug_Update
.import Game_Init
.import audio_init:abs, audio_play_beep:abs, audio_play_hit:abs, audio_play_shoot:abs, audio_play_pickup:abs

; -----------------------------------------------------------------------------
; Debug Menu States
; -----------------------------------------------------------------------------
DEBUG_MENU_MAIN         = 0
DEBUG_MENU_GRAPHICS     = 1
DEBUG_MENU_AUDIO        = 2
DEBUG_MENU_INPUT        = 3
DEBUG_MENU_PLAYFIELD    = 4

; -----------------------------------------------------------------------------
; Zero Page (Debug-specific)
; -----------------------------------------------------------------------------
.segment "ZEROPAGE"
debug_state:        .res 1
debug_cursor:       .res 1
debug_test_x:       .res 1
debug_test_y:       .res 1
debug_anim_frame:   .res 1
debug_anim_timer:   .res 1

; -----------------------------------------------------------------------------
; Debug Screen Initialization
; -----------------------------------------------------------------------------
.segment "CODE"
.proc Debug_Init
    ; Set debug state
    lda #DEBUG_MENU_MAIN
    sta debug_state

    lda #0
    sta debug_cursor

    ; Test character position (center)
    lda #120
    sta debug_test_x
    lda #100
    sta debug_test_y

    ; Animation
    lda #0
    sta debug_anim_frame
    lda #15
    sta debug_anim_timer

    ; Initialize audio
    jsr audio_init

    ; Load palettes (this happens before rendering is enabled, so it's safe)
    jsr load_debug_palettes

    ; Clear sprites
    lda #$FF
    ldx #0
@clear_oam:
    sta $0200, x
    inx
    bne @clear_oam

    rts
.endproc

; -----------------------------------------------------------------------------
; Load Debug Palettes
; -----------------------------------------------------------------------------
.proc load_debug_palettes
    bit PPU_STATUS

    lda #$3F
    sta PPU_ADDR
    lda #$00
    sta PPU_ADDR

    ldx #0
@loop:
    lda debug_palette, x
    sta PPU_DATA
    inx
    cpx #32
    bne @loop

    rts
.endproc

; Debug palette data
debug_palette:
    ; Background palettes
    .byte $0F, $00, $10, $30  ; Black, Dark Gray, Light Gray, White (for text)
    .byte $0F, $21, $31, $11  ; Black, Cyan, Light Cyan, Blue (highlights)
    .byte $0F, $16, $26, $36  ; Black, Red, Orange, Yellow (warnings)
    .byte $0F, $1A, $2A, $3A  ; Black, Green, Light Green, Pale Green (success)

    ; Sprite palettes
    .byte $0F, $15, $25, $30  ; Player: Magenta, Pink, White
    .byte $0F, $11, $21, $31  ; Enemies: Blue, Cyan, Light Cyan
    .byte $0F, $16, $26, $30  ; Weapons: Red, Orange, White
    .byte $0F, $19, $29, $39  ; Pickups: Green, Yellow, Pale Yellow

; -----------------------------------------------------------------------------
; Draw Main Menu
; -----------------------------------------------------------------------------
.proc draw_main_menu
    bit PPU_STATUS

    ; Set PPU address to name table
    lda #$20
    sta PPU_ADDR
    lda #$00
    sta PPU_ADDR

    ; Clear screen
    lda #$00
    ldx #0
    ldy #0
@clear:
    sta PPU_DATA
    inx
    bne @clear
    iny
    cpy #4
    bne @clear

    ; Draw title
    lda #$20
    sta PPU_ADDR
    lda #$62  ; Row 3, col 2
    sta PPU_ADDR

    ldx #0
@title_loop:
    lda text_title, x
    beq @title_done
    sta PPU_DATA
    inx
    jmp @title_loop
@title_done:

    ; Draw menu options
    lda #$20
    sta PPU_ADDR
    lda #$C4  ; Row 6, col 4
    sta PPU_ADDR

    ldx #0
@menu_loop:
    lda text_menu, x
    beq @menu_done
    cmp #$0A  ; Newline
    bne @not_newline
    ; Move to next line
    txa
    pha
    lda PPU_ADDR  ; Read current address
    clc
    adc #32
    sta PPU_ADDR
    lda #$04
    sta PPU_ADDR
    pla
    tax
    inx
    jmp @menu_loop
@not_newline:
    sta PPU_DATA
    inx
    jmp @menu_loop
@menu_done:

    rts
.endproc

; -----------------------------------------------------------------------------
; Debug Update Loop
; -----------------------------------------------------------------------------
.proc Debug_Update
    ; Read input
    jsr input_read

    ; Test audio: Play beep on A button press
    lda buttons_pressed
    and #$80  ; A button
    beq @not_a
    jsr audio_play_beep
@not_a:

    ; Play hit sound on B button press
    lda buttons_pressed
    and #$40  ; B button
    beq @not_b
    jsr audio_play_hit
@not_b:

    ; Play shoot sound on START button press
    lda buttons_pressed
    and #$10  ; START button
    beq @not_start
    jsr audio_play_shoot
@not_start:

    ; Play pickup sound on SELECT button press
    lda buttons_pressed
    and #$20  ; SELECT button
    beq @not_select
    jsr audio_play_pickup
@not_select:

    ; Simple test: move sprite with D-pad
    lda buttons
    and #$08  ; Up
    beq @not_up
    dec debug_test_y
@not_up:
    lda buttons
    and #$04  ; Down
    beq @not_down
    inc debug_test_y
@not_down:
    lda buttons
    and #$02  ; Left
    beq @not_left
    dec debug_test_x
@not_left:
    lda buttons
    and #$01  ; Right
    beq @not_right
    inc debug_test_x
@not_right:

    ; Render test sprite at debug_test_x, debug_test_y
    lda debug_test_y
    sta $0200       ; Y position
    lda #$00        ; Tile 0
    sta $0201
    lda #$00        ; Attributes (palette 0)
    sta $0202
    lda debug_test_x
    sta $0203       ; X position

    ; Hide remaining sprites
    lda #$FF
    ldx #4
@hide_sprites:
    sta $0200, x
    inx
    inx
    inx
    inx
    cpx #0
    bne @hide_sprites

    rts
.endproc

; -----------------------------------------------------------------------------
; Update Main Menu
; -----------------------------------------------------------------------------
.proc update_main_menu
    ; Check for UP/DOWN
    lda buttons_pressed
    and #BTN_UP
    beq @not_up

    lda debug_cursor
    beq @not_up
    dec debug_cursor
@not_up:

    lda buttons_pressed
    and #BTN_DOWN
    beq @not_down

    lda debug_cursor
    cmp #4  ; 5 menu items (0-4)
    bcs @not_down
    inc debug_cursor
@not_down:

    ; Check for A/START to select
    lda buttons_pressed
    and #(BTN_A | BTN_START)
    beq @not_select

    ; Jump to selected test
    lda debug_cursor
    cmp #0
    beq @select_graphics
    cmp #1
    beq @select_audio
    cmp #2
    beq @select_input
    cmp #3
    beq @select_playfield
    cmp #4
    beq @select_game
    jmp @not_select

@select_graphics:
    lda #DEBUG_MENU_GRAPHICS
    sta debug_state
    jsr draw_graphics_test
    jmp @not_select

@select_audio:
    lda #DEBUG_MENU_AUDIO
    sta debug_state
    jsr draw_audio_test
    jmp @not_select

@select_input:
    lda #DEBUG_MENU_INPUT
    sta debug_state
    jmp @not_select

@select_playfield:
    lda #DEBUG_MENU_PLAYFIELD
    sta debug_state
    jsr draw_playfield_test
    jmp @not_select

@select_game:
    ; Return to main game
    jmp Game_Init

@not_select:
    rts
.endproc

; -----------------------------------------------------------------------------
; Graphics Test Screen
; -----------------------------------------------------------------------------
.proc update_graphics_test
    ; Animate test sprite
    dec debug_anim_timer
    bne @no_anim

    lda #15
    sta debug_anim_timer

    inc debug_anim_frame
    lda debug_anim_frame
    and #$03
    sta debug_anim_frame
@no_anim:

    ; B button to return
    lda buttons_pressed
    and #BTN_B
    beq @not_back

    lda #DEBUG_MENU_MAIN
    sta debug_state
    jsr draw_main_menu
@not_back:

    rts
.endproc

.proc draw_graphics_test
    ; Draw test screen
    bit PPU_STATUS
    lda #$20
    sta PPU_ADDR
    lda #$00
    sta PPU_ADDR

    ; Clear
    lda #$00
    ldx #0
    ldy #0
@clear:
    sta PPU_DATA
    inx
    bne @clear
    iny
    cpy #4
    bne @clear

    ; Draw "GRAPHICS TEST" text
    ; (Implementation TBD - add text rendering)

    rts
.endproc

; -----------------------------------------------------------------------------
; Audio Test Screen
; -----------------------------------------------------------------------------
.proc update_audio_test
    ; Test audio on button press
    lda buttons_pressed
    and #BTN_A
    beq @not_a
    ; TODO: Play beep sound
@not_a:

    ; B to return
    lda buttons_pressed
    and #BTN_B
    beq @not_back

    lda #DEBUG_MENU_MAIN
    sta debug_state
    jsr draw_main_menu
@not_back:

    rts
.endproc

.proc draw_audio_test
    ; Draw audio test screen
    bit PPU_STATUS
    lda #$20
    sta PPU_ADDR
    lda #$00
    sta PPU_ADDR

    ; Clear
    lda #$00
    ldx #0
    ldy #0
@clear:
    sta PPU_DATA
    inx
    bne @clear
    iny
    cpy #4
    bne @clear

    ; Draw "AUDIO TEST" text
    ; (Implementation TBD)

    rts
.endproc

; -----------------------------------------------------------------------------
; Playfield Test - Character Movement
; -----------------------------------------------------------------------------
.proc update_playfield_test
    ; Move test character with D-pad
    lda buttons
    and #BTN_UP
    beq @not_up
    dec debug_test_y
@not_up:

    lda buttons
    and #BTN_DOWN
    beq @not_down
    inc debug_test_y
@not_down:

    lda buttons
    and #BTN_LEFT
    beq @not_left
    dec debug_test_x
@not_left:

    lda buttons
    and #BTN_RIGHT
    beq @not_right
    inc debug_test_x
@not_right:

    ; B to return
    lda buttons_pressed
    and #BTN_B
    beq @not_back

    lda #DEBUG_MENU_MAIN
    sta debug_state
    jsr draw_main_menu
@not_back:

    rts
.endproc

.proc draw_playfield_test
    ; Draw playfield test screen
    bit PPU_STATUS
    lda #$20
    sta PPU_ADDR
    lda #$00
    sta PPU_ADDR

    ; Clear
    lda #$00
    ldx #0
    ldy #0
@clear:
    sta PPU_DATA
    inx
    bne @clear
    iny
    cpy #4
    bne @clear

    ; Draw "PLAYFIELD TEST" text and instructions
    ; (Implementation TBD)

    rts
.endproc

; -----------------------------------------------------------------------------
; Render Debug Sprites
; -----------------------------------------------------------------------------
.proc render_debug_sprites
    lda #0
    sta oam_index

    ; Render cursor on main menu
    lda debug_state
    cmp #DEBUG_MENU_MAIN
    bne @not_main_menu

    ldy oam_index

    ; Cursor sprite (simple square)
    lda debug_cursor
    ; Calculate Y position (each menu item is 16 pixels apart)
    asl
    asl
    asl
    asl  ; * 16
    clc
    adc #96  ; Starting Y position
    sta $0200, y

    lda #TILE_PICKUP_XP_GEM  ; Use XP gem as cursor
    sta $0201, y
    lda #$03  ; Palette 3 (green)
    sta $0202, y
    lda #24  ; X position
    sta $0203, y

    iny
    iny
    iny
    iny
    sty oam_index
@not_main_menu:

    ; Render test character in playfield test
    lda debug_state
    cmp #DEBUG_MENU_PLAYFIELD
    bne @not_playfield

    ldy oam_index

    ; Render 2x2 player sprite
    ; Top-left
    lda debug_test_y
    sta $0200, y
    lda #TILE_PLAYER_IDLE_TL
    sta $0201, y
    lda #$00
    sta $0202, y
    lda debug_test_x
    sta $0203, y

    iny
    iny
    iny
    iny

    ; Top-right
    lda debug_test_y
    sta $0200, y
    lda #TILE_PLAYER_IDLE_TR
    sta $0201, y
    lda #$00
    sta $0202, y
    lda debug_test_x
    clc
    adc #8
    sta $0203, y

    iny
    iny
    iny
    iny

    ; Bottom-left
    lda debug_test_y
    clc
    adc #8
    sta $0200, y
    lda #TILE_PLAYER_IDLE_BL
    sta $0201, y
    lda #$00
    sta $0202, y
    lda debug_test_x
    sta $0203, y

    iny
    iny
    iny
    iny

    ; Bottom-right
    lda debug_test_y
    clc
    adc #8
    sta $0200, y
    lda #TILE_PLAYER_IDLE_BR
    sta $0201, y
    lda #$00
    sta $0202, y
    lda debug_test_x
    clc
    adc #8
    sta $0203, y

    iny
    iny
    iny
    iny

    sty oam_index
@not_playfield:

    ; Hide remaining sprites
    ldy oam_index
@hide_loop:
    beq @done
    lda #$FF
    sta $0200, y
    iny
    iny
    iny
    iny
    jmp @hide_loop

@done:
    rts
.endproc

; -----------------------------------------------------------------------------
; Text Data
; -----------------------------------------------------------------------------
.segment "RODATA"
text_title:
    .byte "DEBUG / TEST SCREEN", 0

text_menu:
    .byte "1. GRAPHICS TEST", $0A
    .byte "2. AUDIO TEST", $0A
    .byte "3. INPUT TEST", $0A
    .byte "4. PLAYFIELD TEST", $0A
    .byte "5. START GAME", 0
