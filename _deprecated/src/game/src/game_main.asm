; =============================================================================
; NEON SURVIVORS - Main Game Loop
; Core game logic runs here between NMI frames
; =============================================================================

.include "../../engine/engine.inc"

.export Game_Init, Game_Update
.import reset:abs

; -----------------------------------------------------------------------------
; Game State Constants
; -----------------------------------------------------------------------------
GAME_STATE_TITLE    = 0
GAME_STATE_PLAYING  = 1
GAME_STATE_LEVELUP  = 2
GAME_STATE_PAUSED   = 3
GAME_STATE_GAMEOVER = 4

; -----------------------------------------------------------------------------
; Game Initialization
; -----------------------------------------------------------------------------
.proc Game_Init
    ; Initialize player position (center of screen)
    lda #128
    sta player_x
    lda #120
    sta player_y

    ; Initialize player stats
    lda #100
    sta player_health   ; Using engine's player_health ZP variable
    lda #1
    sta player_level
    lda #0
    sta player_xp
    sta player_xp+1
    sta player_coins
    sta player_coins+1

    ; Game state = title screen
    lda #GAME_STATE_TITLE
    sta game_state

    ; Initialize enemy position (upper right area)
    lda #200
    sta enemy_x
    lda #60
    sta enemy_y
    lda #60             ; Fire every 60 frames (1 second)
    sta enemy_fire_timer

    ; Initialize action module systems
.ifdef MODULE_ACTION_ENABLED
    jsr projectile_init

.ifdef USE_SPAWNER
    jsr spawner_init
.endif

.ifdef USE_POWERUPS
    jsr powerup_init
.endif
.endif

    ; Load palettes
    jsr load_palettes

    ; Draw Title Screen
    jsr draw_title_screen

    rts
.endproc

; -----------------------------------------------------------------------------
; Draw Title Screen Text
; -----------------------------------------------------------------------------
.proc draw_title_screen
    bit PPU_STATUS
    
    ; Name Table 0 ($2000)
    lda #$20
    sta PPU_ADDR
    lda #$00
    sta PPU_ADDR
    
    ; Clear screen (fill with 0/space)
    ldx #0
    ldy #0
    lda #0  ; Tile 0 = Space (in new font map?) check gen_assets.
            ; No, gen_assets doesn't define space at 0 explicitly?
            ; Ah, gen_assets initializes "data = bytearray(8192)", so tile 0 is empty.
            ; Correct.
@clear_loop:
    sta PPU_DATA
    inx
    bne @clear_loop
    iny
    cpy #4              ; 4 pages = 1KB name table
    bne @clear_loop
    
    ; Write "NEON SURVIVORS" at roughly center (Row 10, Col 8)
    ; $2000 + 10*32 + 8 = $2000 + 320 + 8 = $2148
    lda #$21
    sta PPU_ADDR
    lda #$48
    sta PPU_ADDR
    
    ldx #0
@loop_title:
    lda text_title, x
    beq @done_title
    sta PPU_DATA
    inx
    jmp @loop_title
@done_title:

    ; Write "PRESS START" at Row 20, Col 10
    ; $2000 + 20*32 + 10 = $2000 + 640 + 10 = $228A
    lda #$22
    sta PPU_ADDR
    lda #$8A
    sta PPU_ADDR
    
    ldx #0
@loop_start:
    lda text_start, x
    beq @done_start
    sta PPU_DATA
    inx
    jmp @loop_start
@done_start:

    rts
.endproc

.segment "RODATA"
text_title:
    .byte "NEON SURVIVORS", 0
text_start:
    .byte "PRESS START", 0
.segment "CODE"

; -----------------------------------------------------------------------------
; Load Color Palettes
; -----------------------------------------------------------------------------
.proc load_palettes
    bit PPU_STATUS          ; Reset PPU latch
    
    lda #$3F
    sta PPU_ADDR
    lda #$00
    sta PPU_ADDR            ; PPU address = $3F00 (palettes)
    
    ldx #0
@loop:
    lda palette_data, x
    sta PPU_DATA
    inx
    cpx #32                 ; 32 bytes = 8 palettes
    bne @loop
    
    rts
.endproc

; -----------------------------------------------------------------------------
; Palette Data - Retrofuture Synthwave Colors
; -----------------------------------------------------------------------------
.segment "RODATA"

palette_data:
    ; Background palettes
    .byte $0F, $21, $31, $30  ; Black, Cyan, Light Cyan, White
    .byte $0F, $14, $24, $34  ; Black, Purple, Pink, Light Pink
    .byte $0F, $12, $22, $32  ; Black, Blue, Light Blue, Pale Blue
    .byte $0F, $1A, $2A, $3A  ; Black, Green, Light Green, Pale Green
    
    ; Sprite palettes
    .byte $0F, $24, $2C, $30  ; Player: Black, Magenta, Light Cyan, White
    .byte $0F, $11, $21, $31  ; Enemies: Black, Blue, Cyan, Light Cyan
    .byte $0F, $16, $26, $30  ; Weapons: Black, Red, Orange, White
    .byte $0F, $19, $29, $39  ; Pickups: Black, Green, Yellow, Pale Yellow

; -----------------------------------------------------------------------------
; Zero Page Variables
; -----------------------------------------------------------------------------
.segment "ZEROPAGE"

; Engine core variables are already exported by engine.inc
; (frame_count, nmi_ready, ppu_ctrl_copy, scroll_x, scroll_y,
;  player_x, player_y, player_health, player_xp, player_coins, player_level,
;  buttons, buttons_pressed, temp1-4, oam_index)

; Game-specific state
game_state:         .res 1      ; Current game state
buttons_old:        .res 1      ; Previous frame buttons (for edge detection)
player_dir:         .res 1      ; Facing direction

; Weapon timers
weapon_timer:       .res 1
weapon_active:      .res 1

; Enemy state
enemy_x:            .res 1      ; Enemy X position
enemy_y:            .res 1      ; Enemy Y position
enemy_fire_timer:   .res 1      ; Enemy auto-fire countdown

; -----------------------------------------------------------------------------
; Main Code
; -----------------------------------------------------------------------------
.segment "CODE"

; -----------------------------------------------------------------------------
; Main Game Loop
; -----------------------------------------------------------------------------
.proc Game_Update
    ; Read controller input (using engine input system)
    jsr input_read

    ; Calculate newly pressed buttons (buttons_pressed handled by engine)
    lda buttons
    eor buttons_old
    and buttons
    sta buttons_pressed
    lda buttons
    sta buttons_old

    ; State machine
    lda game_state
    cmp #GAME_STATE_TITLE
    beq @state_title
    cmp #GAME_STATE_PLAYING
    beq @state_playing
    cmp #GAME_STATE_LEVELUP
    beq @state_levelup
    cmp #GAME_STATE_GAMEOVER
    beq @state_gameover
    jmp @done

@state_title:
    jsr update_title
    jmp @done

@state_playing:
    jsr update_player
    jsr update_enemy

    ; Update action module systems
.ifdef MODULE_ACTION_ENABLED
.ifdef USE_SPAWNER
    jsr spawner_update
.endif

    jsr projectile_update_all

.ifdef USE_POWERUPS
    jsr powerup_update_all
.endif
.endif

    jsr update_weapons
    jsr check_collisions
    jsr update_sprites
    jmp @done

@state_levelup:
    jsr update_levelup_menu
    jmp @done

@state_gameover:
    jsr update_gameover
    jmp @done

@done:
    rts
.endproc

; -----------------------------------------------------------------------------
; State Handlers
; -----------------------------------------------------------------------------
.proc update_title
    ; Check for START button
    lda buttons_pressed
    and #BTN_START
    beq @done

    ; Start game
    lda #GAME_STATE_PLAYING
    sta game_state

@done:
    rts
.endproc

.proc update_player
    ; Movement speed
    PLAYER_SPEED = 2
    
    ; Check D-pad
    lda buttons
    and #BTN_UP
    beq @not_up
    lda player_y
    sec
    sbc #PLAYER_SPEED
    sta player_y
@not_up:

    lda buttons
    and #BTN_DOWN
    beq @not_down
    lda player_y
    clc
    adc #PLAYER_SPEED
    sta player_y
@not_down:

    lda buttons
    and #BTN_LEFT
    beq @not_left
    lda player_x
    sec
    sbc #PLAYER_SPEED
    sta player_x
@not_left:

    lda buttons
    and #BTN_RIGHT
    beq @not_right
    lda player_x
    clc
    adc #PLAYER_SPEED
    sta player_x
@not_right:

    rts
.endproc

.proc update_enemy
    ; Enemy auto-fire logic
.ifdef MODULE_ACTION_ENABLED
    ; Decrement fire timer
    lda enemy_fire_timer
    beq @fire
    dec enemy_fire_timer
    jmp @done

@fire:
    ; Reset timer (60 frames = 1 second)
    lda #60
    sta enemy_fire_timer

    ; Spawn enemy projectile aimed left (toward player)
    lda enemy_x
    sta projectile_spawn_x

    lda enemy_y
    clc
    adc #8              ; Center of 32x32 sprite
    sta projectile_spawn_y

    ; Velocity: shoot left
    lda #<(-3)          ; -3 velocity (moves left)
    sta projectile_spawn_vx
    lda #0
    sta projectile_spawn_vy

    lda #PROJ_TYPE_LASER
    sta projectile_spawn_type

    lda #PROJ_FLAG_ENEMY    ; Enemy projectile flag
    sta projectile_spawn_flags

    jsr projectile_spawn

@done:
.endif
    rts
.endproc

.proc update_weapons
    ; Auto-attack weapon logic using projectile module
.ifdef MODULE_ACTION_ENABLED
    ; Decrement weapon timer
    lda weapon_timer
    beq @fire
    dec weapon_timer
    jmp @done

@fire:
    ; Reset timer (30 frames = 0.5 seconds at 60fps)
    lda #30
    sta weapon_timer

    ; Spawn projectile in player's facing direction
    lda player_x
    clc
    adc #4              ; Center of 16x16 sprite
    sta projectile_spawn_x

    lda player_y
    clc
    adc #4
    sta projectile_spawn_y

    ; Default velocity: shoot right
    lda #4
    sta projectile_spawn_vx
    lda #0
    sta projectile_spawn_vy

    lda #PROJ_TYPE_LASER
    sta projectile_spawn_type

    lda #PROJ_FLAG_FRIENDLY
    sta projectile_spawn_flags

    jsr projectile_spawn

@done:
.endif
    rts
.endproc

.proc check_collisions
    ; TODO: Implement collision detection between:
    ; - Projectiles and enemies
    ; - Player and enemy projectiles
    ; - Player and powerups (handled by powerup_update_all)
    rts
.endproc

.proc update_sprites
    ; Initialize OAM index
    lda #0
    sta oam_index

    ; Render player sprite (32x32 = 16 tiles in 4x4 grid)
    ; Using explicit writes like projectile_render_all
    ; OAM format: Y, Tile, Attributes, X
    ; Tile layout:
    ;   Row 0: $00, $01, $02, $03  (Y + 0)
    ;   Row 1: $04, $05, $06, $07  (Y + 8)
    ;   Row 2: $08, $09, $0A, $0B  (Y + 16)
    ;   Row 3: $0C, $0D, $0E, $0F  (Y + 24)

    ldy #0                  ; OAM index

    ; === Row 0 (Y offset = 0) ===
    ; Tile $00 (top-left)
    lda player_y
    sta $0200, y            ; Y position
    lda #$00
    sta $0201, y            ; Tile
    lda #$00
    sta $0202, y            ; Attributes (palette 0)
    lda player_x
    sta $0203, y            ; X position
    iny
    iny
    iny
    iny

    ; Tile $01
    lda player_y
    sta $0200, y
    lda #$01
    sta $0201, y
    lda #$00
    sta $0202, y
    lda player_x
    clc
    adc #8
    sta $0203, y
    iny
    iny
    iny
    iny

    ; Tile $02
    lda player_y
    sta $0200, y
    lda #$02
    sta $0201, y
    lda #$00
    sta $0202, y
    lda player_x
    clc
    adc #16
    sta $0203, y
    iny
    iny
    iny
    iny

    ; Tile $03
    lda player_y
    sta $0200, y
    lda #$03
    sta $0201, y
    lda #$00
    sta $0202, y
    lda player_x
    clc
    adc #24
    sta $0203, y
    iny
    iny
    iny
    iny

    ; === Row 1 (Y offset = 8) ===
    ; Tile $04
    lda player_y
    clc
    adc #8
    sta $0200, y
    lda #$04
    sta $0201, y
    lda #$00
    sta $0202, y
    lda player_x
    sta $0203, y
    iny
    iny
    iny
    iny

    ; Tile $05
    lda player_y
    clc
    adc #8
    sta $0200, y
    lda #$05
    sta $0201, y
    lda #$00
    sta $0202, y
    lda player_x
    clc
    adc #8
    sta $0203, y
    iny
    iny
    iny
    iny

    ; Tile $06
    lda player_y
    clc
    adc #8
    sta $0200, y
    lda #$06
    sta $0201, y
    lda #$00
    sta $0202, y
    lda player_x
    clc
    adc #16
    sta $0203, y
    iny
    iny
    iny
    iny

    ; Tile $07
    lda player_y
    clc
    adc #8
    sta $0200, y
    lda #$07
    sta $0201, y
    lda #$00
    sta $0202, y
    lda player_x
    clc
    adc #24
    sta $0203, y
    iny
    iny
    iny
    iny

    ; === Row 2 (Y offset = 16) ===
    ; Tile $08
    lda player_y
    clc
    adc #16
    sta $0200, y
    lda #$08
    sta $0201, y
    lda #$00
    sta $0202, y
    lda player_x
    sta $0203, y
    iny
    iny
    iny
    iny

    ; Tile $09
    lda player_y
    clc
    adc #16
    sta $0200, y
    lda #$09
    sta $0201, y
    lda #$00
    sta $0202, y
    lda player_x
    clc
    adc #8
    sta $0203, y
    iny
    iny
    iny
    iny

    ; Tile $0A
    lda player_y
    clc
    adc #16
    sta $0200, y
    lda #$0A
    sta $0201, y
    lda #$00
    sta $0202, y
    lda player_x
    clc
    adc #16
    sta $0203, y
    iny
    iny
    iny
    iny

    ; Tile $0B
    lda player_y
    clc
    adc #16
    sta $0200, y
    lda #$0B
    sta $0201, y
    lda #$00
    sta $0202, y
    lda player_x
    clc
    adc #24
    sta $0203, y
    iny
    iny
    iny
    iny

    ; === Row 3 (Y offset = 24) ===
    ; Tile $0C
    lda player_y
    clc
    adc #24
    sta $0200, y
    lda #$0C
    sta $0201, y
    lda #$00
    sta $0202, y
    lda player_x
    sta $0203, y
    iny
    iny
    iny
    iny

    ; Tile $0D
    lda player_y
    clc
    adc #24
    sta $0200, y
    lda #$0D
    sta $0201, y
    lda #$00
    sta $0202, y
    lda player_x
    clc
    adc #8
    sta $0203, y
    iny
    iny
    iny
    iny

    ; Tile $0E
    lda player_y
    clc
    adc #24
    sta $0200, y
    lda #$0E
    sta $0201, y
    lda #$00
    sta $0202, y
    lda player_x
    clc
    adc #16
    sta $0203, y
    iny
    iny
    iny
    iny

    ; Tile $0F
    lda player_y
    clc
    adc #24
    sta $0200, y
    lda #$0F
    sta $0201, y
    lda #$00
    sta $0202, y
    lda player_x
    clc
    adc #24
    sta $0203, y
    iny
    iny
    iny
    iny

    ; Update OAM index (16 sprites = 64 bytes)
    sty oam_index

    ; ========================================
    ; Render Enemy Sprite (32x32 = 16 tiles)
    ; Enemy tiles start at $10
    ; ========================================
    ldy oam_index

    ; === Enemy Row 0 (Y offset = 0) ===
    ; Tile $10 (top-left)
    lda enemy_y
    sta $0200, y
    lda #$10
    sta $0201, y
    lda #$01                ; Palette 1 (enemy colors)
    sta $0202, y
    lda enemy_x
    sta $0203, y
    iny
    iny
    iny
    iny

    ; Tile $11
    lda enemy_y
    sta $0200, y
    lda #$11
    sta $0201, y
    lda #$01
    sta $0202, y
    lda enemy_x
    clc
    adc #8
    sta $0203, y
    iny
    iny
    iny
    iny

    ; Tile $12
    lda enemy_y
    sta $0200, y
    lda #$12
    sta $0201, y
    lda #$01
    sta $0202, y
    lda enemy_x
    clc
    adc #16
    sta $0203, y
    iny
    iny
    iny
    iny

    ; Tile $13
    lda enemy_y
    sta $0200, y
    lda #$13
    sta $0201, y
    lda #$01
    sta $0202, y
    lda enemy_x
    clc
    adc #24
    sta $0203, y
    iny
    iny
    iny
    iny

    ; === Enemy Row 1 (Y offset = 8) ===
    ; Tile $14
    lda enemy_y
    clc
    adc #8
    sta $0200, y
    lda #$14
    sta $0201, y
    lda #$01
    sta $0202, y
    lda enemy_x
    sta $0203, y
    iny
    iny
    iny
    iny

    ; Tile $15
    lda enemy_y
    clc
    adc #8
    sta $0200, y
    lda #$15
    sta $0201, y
    lda #$01
    sta $0202, y
    lda enemy_x
    clc
    adc #8
    sta $0203, y
    iny
    iny
    iny
    iny

    ; Tile $16
    lda enemy_y
    clc
    adc #8
    sta $0200, y
    lda #$16
    sta $0201, y
    lda #$01
    sta $0202, y
    lda enemy_x
    clc
    adc #16
    sta $0203, y
    iny
    iny
    iny
    iny

    ; Tile $17
    lda enemy_y
    clc
    adc #8
    sta $0200, y
    lda #$17
    sta $0201, y
    lda #$01
    sta $0202, y
    lda enemy_x
    clc
    adc #24
    sta $0203, y
    iny
    iny
    iny
    iny

    ; === Enemy Row 2 (Y offset = 16) ===
    ; Tile $18
    lda enemy_y
    clc
    adc #16
    sta $0200, y
    lda #$18
    sta $0201, y
    lda #$01
    sta $0202, y
    lda enemy_x
    sta $0203, y
    iny
    iny
    iny
    iny

    ; Tile $19
    lda enemy_y
    clc
    adc #16
    sta $0200, y
    lda #$19
    sta $0201, y
    lda #$01
    sta $0202, y
    lda enemy_x
    clc
    adc #8
    sta $0203, y
    iny
    iny
    iny
    iny

    ; Tile $1A
    lda enemy_y
    clc
    adc #16
    sta $0200, y
    lda #$1A
    sta $0201, y
    lda #$01
    sta $0202, y
    lda enemy_x
    clc
    adc #16
    sta $0203, y
    iny
    iny
    iny
    iny

    ; Tile $1B
    lda enemy_y
    clc
    adc #16
    sta $0200, y
    lda #$1B
    sta $0201, y
    lda #$01
    sta $0202, y
    lda enemy_x
    clc
    adc #24
    sta $0203, y
    iny
    iny
    iny
    iny

    ; === Enemy Row 3 (Y offset = 24) ===
    ; Tile $1C
    lda enemy_y
    clc
    adc #24
    sta $0200, y
    lda #$1C
    sta $0201, y
    lda #$01
    sta $0202, y
    lda enemy_x
    sta $0203, y
    iny
    iny
    iny
    iny

    ; Tile $1D
    lda enemy_y
    clc
    adc #24
    sta $0200, y
    lda #$1D
    sta $0201, y
    lda #$01
    sta $0202, y
    lda enemy_x
    clc
    adc #8
    sta $0203, y
    iny
    iny
    iny
    iny

    ; Tile $1E
    lda enemy_y
    clc
    adc #24
    sta $0200, y
    lda #$1E
    sta $0201, y
    lda #$01
    sta $0202, y
    lda enemy_x
    clc
    adc #16
    sta $0203, y
    iny
    iny
    iny
    iny

    ; Tile $1F
    lda enemy_y
    clc
    adc #24
    sta $0200, y
    lda #$1F
    sta $0201, y
    lda #$01
    sta $0202, y
    lda enemy_x
    clc
    adc #24
    sta $0203, y
    iny
    iny
    iny
    iny

    ; Update OAM index after enemy (32 sprites total = 128 bytes)
    sty oam_index

    ; Render action module sprites
.ifdef MODULE_ACTION_ENABLED
    jsr projectile_render_all

.ifdef USE_POWERUPS
    jsr powerup_render_all
.endif
.endif

    ; Hide remaining sprites
    ldy oam_index
@hide_loop:
    beq @done               ; Y wrapped to 0, we're done (256 sprites hidden)
    lda #$FF                ; Y = $FF hides sprite
    sta $0200, y
    iny
    iny
    iny
    iny
    jmp @hide_loop

@done:
    rts
.endproc

.proc update_levelup_menu
    ; TODO: Level-up selection
    rts
.endproc

.proc update_gameover
    ; Check for START to restart
    lda buttons_pressed
    and #BTN_START
    beq @done

    jmp reset               ; Restart game

@done:
    rts
.endproc
