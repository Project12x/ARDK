; =============================================================================
; TOWER SURVIVORS - Demo using ACTION_SURVIVOR Engine Variant
; =============================================================================
; A "Vampire Survivors" style game where you protect a central tower.
; Features:
;   - Player moves with D-pad, auto-fires at enemies
;   - Enemies spawn in waves, pathfind toward tower
;   - XP sparks home to tower when enemies die
;   - Tower gains XP, player gains upgrades
;   - Engine optimizations: Recca shuffler, quadrant AI, spatial grid
; =============================================================================

.include "nes.inc"

; Include the ACTION_SURVIVOR engine variant
.include "variants/action_survivor.inc"
.include "variants/action_survivor_advanced.inc"

; Export entry points
.export Reset
.export NMI
.export IRQ

; =============================================================================
; Game Constants
; =============================================================================

; Screen boundaries
SCREEN_LEFT         = 8
SCREEN_RIGHT        = 240
SCREEN_TOP          = 16
SCREEN_BOTTOM       = 200      ; Leave room for HUD at bottom

; Tower position (center of screen)
TOWER_CENTER_X      = 128
TOWER_CENTER_Y      = 112

; Player settings
PLAYER_SPEED        = 2
PLAYER_MAX_HP       = 10
PLAYER_REGEN_RATE   = 60       ; Frames per HP regen

; Enemy settings
ENEMY_BASE_HP       = 3
ENEMY_XP_VALUE      = 5

; Weapon settings
WEAPON_COOLDOWN     = 10
BULLET_SPEED        = 4
BULLET_DAMAGE       = 1

; Spawn settings
INITIAL_SPAWN_RATE  = 120      ; Frames between spawns
MIN_SPAWN_RATE      = 30
SPAWN_ACCELERATION  = 5        ; Frames to reduce per wave

; =============================================================================
; Zero Page Exports (for engine variant)
; =============================================================================
.exportzp nmi_flag, frame_counter
.exportzp player_x, player_y, player_hp, player_inv_timer
.exportzp tower_x, tower_y, tower_hp, tower_xp_lo, tower_xp_hi
.exportzp tower_damage_flash, ppu_mask_shadow
.exportzp scroll_x, scroll_y, chr_anim_timer, chr_anim_frame
.exportzp oam_shuffle_seed, oam_enemy_start

; =============================================================================
; Additional Zero Page Variables
; =============================================================================
.segment "ZEROPAGE"

game_state:         .res 1     ; 0=title, 1=playing, 2=gameover, 3=paused
wave_number:        .res 1
score_lo:           .res 1
score_hi:           .res 1
weapon_timer:       .res 1
player_regen_counter: .res 1

; =============================================================================
; Main Code
; =============================================================================
.segment "CODE"

; -----------------------------------------------------------------------------
; Reset - NES Initialization
; -----------------------------------------------------------------------------
.proc Reset
    sei
    cld
    ldx #$FF
    txs

    ; Disable rendering
    lda #0
    sta $2000
    sta $2001

    ; Wait for PPU
:   bit $2002
    bpl :-

    ; Clear RAM
    lda #0
    ldx #0
@clear:
    sta $0000, x
    sta $0100, x
    sta $0200, x
    sta $0300, x
    sta $0400, x
    sta $0500, x
    sta $0600, x
    sta $0700, x
    inx
    bne @clear

    ; Wait for PPU again
:   bit $2002
    bpl :-

    ; Initialize MMC3
    jsr mmc3_init

    ; Initialize game
    jsr game_init

    ; Load palettes
    jsr load_palettes

    ; Draw background
    jsr draw_background

    ; Initialize engine systems
    jsr sprite_multiplexer_init
    jsr spark_buffer_init
    jsr spatial_grid_clear

    ; Setup MMC3 IRQ for HUD split
    jsr irq_split_init

    ; Enable NMI and rendering
    lda #%10010000          ; NMI on, sprites at $0000, BG at $1000
    sta $2000
    sta ppu_ctrl_shadow

    lda #%00011110          ; Show sprites and BG
    sta $2001
    sta ppu_mask_shadow

    ; Main loop
@main_loop:
    ; Wait for NMI
    lda #0
    sta nmi_flag
@wait:
    lda nmi_flag
    beq @wait

    ; Start watchdog
    jsr watchdog_start

    ; Game state machine
    lda game_state
    cmp #1
    bne @skip_gameplay

    ; --- GAMEPLAY ---
    jsr read_controller
    jsr watchdog_checkpoint

    jsr update_player
    jsr watchdog_checkpoint

    jsr ai_update_quadrant      ; Only updates 1/4 of enemies
    jsr watchdog_checkpoint

    jsr update_weapons
    jsr update_bullets
    jsr watchdog_checkpoint

    jsr spark_process           ; Process 4 XP sparks
    jsr check_tower_proximity   ; Enemies at tower
    jsr watchdog_checkpoint

    jsr spatial_grid_build      ; Rebuild for collision
    jsr process_collisions
    jsr watchdog_checkpoint

    jsr update_spawner

@skip_gameplay:
    ; Render (always, with adaptive quality)
    jsr render_all

    jmp @main_loop
.endproc

; -----------------------------------------------------------------------------
; NMI Handler
; -----------------------------------------------------------------------------
.proc NMI
    pha
    txa
    pha
    tya
    pha

    ; Use enhanced NMI with VRAM buffer and watchdog
    ; Check if logic completed
    lda logic_started
    bne @skip_updates

    ; OAM DMA
    lda #0
    sta $2003
    lda #$02
    sta $4014

    ; Flush VRAM buffer (sprite-to-BG baking)
    jsr vram_buffer_flush

    ; Update palette flashes
    jsr flash_update_nmi

    ; Update CHR animation
    jsr chr_anim_update_nmi

    ; Reset scroll
    lda scroll_x
    sta $2005
    lda scroll_y
    sta $2005

    ; Reload MMC3 IRQ counter
    lda #HUD_SPLIT_LINE
    sta $C000
    sta $C001

@skip_updates:
    inc frame_counter
    lda #1
    sta nmi_flag

    pla
    tay
    pla
    tax
    pla
    rti
.endproc

; -----------------------------------------------------------------------------
; IRQ Handler (MMC3 scanline IRQ for HUD)
; -----------------------------------------------------------------------------
.proc IRQ
    pha

    ; Acknowledge IRQ
    sta $C001

    ; Switch to HUD CHR bank
    lda #$02
    sta $8000
    lda #$0C
    sta $8001

    ; Reset scroll for HUD
    lda #0
    sta $2005
    sta $2005

    pla
    rti
.endproc

; -----------------------------------------------------------------------------
; Game Init
; -----------------------------------------------------------------------------
.proc game_init
    ; Player at bottom center
    lda #TOWER_CENTER_X
    sta player_x
    lda #TOWER_CENTER_Y + 48
    sta player_y
    lda #PLAYER_MAX_HP
    sta player_hp
    sta player_hp_max
    lda #0
    sta player_xp_lo
    sta player_xp_hi
    sta player_level
    sta player_inv_timer

    ; Tower at center
    lda #TOWER_CENTER_X - 8
    sta tower_x
    lda #TOWER_CENTER_Y - 8
    sta tower_y
    lda #100                ; Tower has lots of HP
    sta tower_hp
    sta tower_hp_max
    lda #0
    sta tower_xp_lo
    sta tower_xp_hi
    sta tower_upgrade_flags
    sta tower_damage_flash

    ; Spawner
    lda #INITIAL_SPAWN_RATE
    sta spawn_rate
    sta spawn_timer
    lda #1
    sta spawn_wave
    lda #0
    sta spawn_count
    sta enemy_count

    ; Weapons
    lda #0
    sta weapon0_type        ; Basic shot
    lda #1
    sta weapon0_level
    lda #WEAPON_COOLDOWN
    sta weapon0_cooldown
    sta weapon_timer

    ; Game state
    lda #1                  ; Start playing
    sta game_state
    lda #0
    sta wave_number
    sta score_lo
    sta score_hi

    ; Clear all enemies
    ldx #MAX_ENEMIES - 1
    lda #0
@clear_enemies:
    sta Enemy_State, x
    dex
    bpl @clear_enemies

    ; Init engine state
    lda #8
    sta chr_anim_timer
    lda #0
    sta chr_anim_frame
    sta scroll_x
    sta scroll_y
    sta ai_quadrant
    sta bullet_frame

    rts
.endproc

; -----------------------------------------------------------------------------
; Read Controller
; -----------------------------------------------------------------------------
.proc read_controller
    lda buttons
    sta buttons_old

    lda #1
    sta $4016
    lda #0
    sta $4016

    ldx #8
    lda #0
@loop:
    pha
    lda $4016
    and #$03
    cmp #1
    pla
    ror a
    dex
    bne @loop

    sta buttons
    rts
.endproc

; -----------------------------------------------------------------------------
; Update Player
; -----------------------------------------------------------------------------
.proc update_player
    ; Decrement invincibility
    lda player_inv_timer
    beq @check_input
    dec player_inv_timer

@check_input:
    ; UP (bit 4)
    lda buttons
    and #%00010000
    beq @not_up
    lda player_y
    cmp #SCREEN_TOP
    beq @not_up
    dec player_y
    dec player_y
@not_up:

    ; DOWN (bit 5)
    lda buttons
    and #%00100000
    beq @not_down
    lda player_y
    cmp #SCREEN_BOTTOM
    bcs @not_down
    inc player_y
    inc player_y
@not_down:

    ; LEFT (bit 6)
    lda buttons
    and #%01000000
    beq @not_left
    lda player_x
    cmp #SCREEN_LEFT
    beq @not_left
    dec player_x
    dec player_x
@not_left:

    ; RIGHT (bit 7)
    lda buttons
    and #%10000000
    beq @not_right
    lda player_x
    cmp #SCREEN_RIGHT
    bcs @not_right
    inc player_x
    inc player_x
@not_right:

    ; HP regen
    inc player_regen_counter
    lda player_regen_counter
    cmp #PLAYER_REGEN_RATE
    bcc @no_regen
    lda #0
    sta player_regen_counter
    lda player_hp
    cmp player_hp_max
    bcs @no_regen
    inc player_hp
@no_regen:

    rts
.endproc

; -----------------------------------------------------------------------------
; Update Weapons (auto-fire)
; -----------------------------------------------------------------------------
.proc update_weapons
    dec weapon_timer
    bne @done

    ; Reset timer
    lda weapon0_cooldown
    sta weapon_timer

    ; Find nearest enemy and fire toward it
    jsr find_nearest_enemy
    bcc @done               ; No enemies

    ; Spawn bullet toward enemy (temp1=enemy X, temp2=enemy Y)
    jsr spawn_bullet_toward

@done:
    rts
.endproc

; Find nearest enemy to player
; Output: Carry set if found, temp1=X, temp2=Y
.proc find_nearest_enemy
    lda #$FF
    sta temp3               ; Best distance
    lda #0
    sta temp4               ; Best enemy index

    ldx #0
@loop:
    lda Enemy_State, x
    and #ENEMY_STATE_MASK
    cmp #ENEMY_ACTIVE
    bne @next

    ; Manhattan distance
    lda Enemy_X, x
    sec
    sbc player_x
    bcs @pos_x
    eor #$FF
    clc
    adc #1
@pos_x:
    sta temp1

    lda Enemy_Y, x
    sec
    sbc player_y
    bcs @pos_y
    eor #$FF
    clc
    adc #1
@pos_y:
    clc
    adc temp1               ; Total distance

    cmp temp3
    bcs @next               ; Not closer

    ; New best
    sta temp3
    stx temp4

@next:
    inx
    cpx #MAX_ENEMIES
    bne @loop

    ; Found any?
    lda temp3
    cmp #$FF
    beq @none

    ; Return position of best enemy
    ldx temp4
    lda Enemy_X, x
    sta temp1
    lda Enemy_Y, x
    sta temp2
    sec
    rts

@none:
    clc
    rts
.endproc

; Spawn bullet toward temp1,temp2
.proc spawn_bullet_toward
    ; Find free bullet slot (check bitmask)
    ldx #0
@find:
    lda Bullet_Active
    and bit_masks_bullet, x
    beq @found
    inx
    cpx #8                  ; Only use first 8 slots for simplicity
    bne @find
    rts                     ; No slots

@found:
    ; Set active
    lda Bullet_Active
    ora bit_masks_bullet, x
    sta Bullet_Active

    ; Position at player
    lda player_x
    clc
    adc #8
    sta Bullet_X, x
    lda player_y
    sta Bullet_Y, x

    ; Calculate velocity toward target
    ; Simple: just move toward target
    lda temp1
    cmp player_x
    bcc @vel_left
    lda #BULLET_SPEED
    jmp @set_vel_x
@vel_left:
    lda #256 - BULLET_SPEED ; Negative velocity
@set_vel_x:
    sta Bullet_VelX, x

    lda temp2
    cmp player_y
    bcc @vel_up
    lda #BULLET_SPEED
    jmp @set_vel_y
@vel_up:
    lda #256 - BULLET_SPEED
@set_vel_y:
    sta Bullet_VelY, x

    rts

bit_masks_bullet:
    .byte $01, $02, $04, $08, $10, $20, $40, $80
.endproc

; -----------------------------------------------------------------------------
; Update Bullets
; -----------------------------------------------------------------------------
.proc update_bullets
    ldx #0
@loop:
    ; Check active
    txa
    lsr a
    lsr a
    lsr a
    tay
    txa
    and #$07
    sta temp1
    lda Bullet_Active, y
    and bit_masks_bullet, temp1
    beq @next

    ; Move bullet
    lda Bullet_X, x
    clc
    adc Bullet_VelX, x
    sta Bullet_X, x

    lda Bullet_Y, x
    clc
    adc Bullet_VelY, x
    sta Bullet_Y, x

    ; Check bounds
    lda Bullet_X, x
    cmp #8
    bcc @deactivate
    cmp #248
    bcs @deactivate
    lda Bullet_Y, x
    cmp #8
    bcc @deactivate
    cmp #232
    bcc @next

@deactivate:
    lda bit_masks_bullet, temp1
    eor #$FF
    and Bullet_Active, y
    sta Bullet_Active, y

@next:
    inx
    cpx #MAX_BULLETS
    bne @loop

    rts
.endproc

; -----------------------------------------------------------------------------
; Process Collisions
; -----------------------------------------------------------------------------
.proc process_collisions
    ldx #0
@bullet_loop:
    ; Check bullet active
    txa
    lsr a
    lsr a
    lsr a
    tay
    txa
    and #$07
    sta temp1
    lda Bullet_Active, y
    and bit_masks_bullet, temp1
    beq @next_bullet

    ; Use spatial grid for fast collision
    lda Bullet_X, x
    ldy Bullet_Y, x
    jsr spatial_grid_check
    bcc @next_bullet        ; No enemies in this cell

    ; Potential hit - check with asymmetric hitbox
    jsr collision_asymmetric
    bcc @next_bullet

    ; HIT! Damage enemy (temp4 = enemy index)
    stx temp2               ; Save bullet index
    ldx temp4
    lda #BULLET_DAMAGE
    jsr enemy_damage
    bcc @enemy_alive

    ; Enemy died - spawn XP spark
    lda #ENEMY_XP_VALUE
    jsr spark_spawn

    ; Increment score
    lda score_lo
    clc
    adc #1
    sta score_lo
    bcc @enemy_alive
    inc score_hi

@enemy_alive:
    ldx temp2               ; Restore bullet index

    ; Deactivate bullet
    txa
    and #$07
    sta temp1
    txa
    lsr a
    lsr a
    lsr a
    tay
    lda bit_masks_bullet, temp1
    eor #$FF
    and Bullet_Active, y
    sta Bullet_Active, y

@next_bullet:
    inx
    cpx #MAX_BULLETS
    bne @bullet_loop

    rts
.endproc

; -----------------------------------------------------------------------------
; Update Spawner
; -----------------------------------------------------------------------------
.proc update_spawner
    dec spawn_timer
    bne @done

    ; Reset timer
    lda spawn_rate
    sta spawn_timer

    ; Spawn enemy at random edge
    jsr spawn_enemy

    ; Accelerate spawning
    inc spawn_count
    lda spawn_count
    cmp #10
    bcc @done

    ; New wave
    lda #0
    sta spawn_count
    inc spawn_wave

    ; Speed up spawning
    lda spawn_rate
    cmp #MIN_SPAWN_RATE
    bcc @done
    sec
    sbc #SPAWN_ACCELERATION
    sta spawn_rate

@done:
    rts
.endproc

; Spawn enemy at random screen edge
.proc spawn_enemy
    ; Find free slot
    ldx #0
@find:
    lda Enemy_State, x
    and #ENEMY_STATE_MASK
    beq @found
    inx
    cpx #MAX_ENEMIES
    bne @find
    rts                     ; No slots

@found:
    ; Random edge (use frame counter as pseudo-random)
    lda frame_counter
    and #$03
    beq @spawn_top
    cmp #1
    beq @spawn_right
    cmp #2
    beq @spawn_bottom
    ; else spawn left

@spawn_left:
    lda #8
    sta Enemy_X, x
    lda frame_counter
    and #$7F
    clc
    adc #32
    sta Enemy_Y, x
    jmp @set_state

@spawn_right:
    lda #240
    sta Enemy_X, x
    lda frame_counter
    lsr a
    and #$7F
    clc
    adc #32
    sta Enemy_Y, x
    jmp @set_state

@spawn_top:
    lda frame_counter
    and #$7F
    clc
    adc #64
    sta Enemy_X, x
    lda #16
    sta Enemy_Y, x
    jmp @set_state

@spawn_bottom:
    lda frame_counter
    lsr a
    and #$7F
    clc
    adc #64
    sta Enemy_X, x
    lda #200
    sta Enemy_Y, x

@set_state:
    ; Set active with HP
    lda #ENEMY_ACTIVE | ENEMY_BASE_HP
    sta Enemy_State, x

    inc enemy_count

    rts
.endproc

; -----------------------------------------------------------------------------
; Load Palettes
; -----------------------------------------------------------------------------
.proc load_palettes
    bit $2002
    lda #$3F
    sta $2006
    lda #$00
    sta $2006

    ldx #0
@loop:
    lda palette_data, x
    sta $2007
    inx
    cpx #32
    bne @loop

    rts
.endproc

; -----------------------------------------------------------------------------
; Draw Background
; -----------------------------------------------------------------------------
.proc draw_background
    bit $2002
    lda #$20
    sta $2006
    lda #$00
    sta $2006

    ; Fill with tile 0 (empty/floor)
    ldy #0
    ldx #0
    lda #$00
@fill:
    sta $2007
    inx
    bne @fill
    iny
    cpy #4                  ; 4 * 256 = 1024 bytes (32x30 + attributes)
    bne @fill

    rts
.endproc

; =============================================================================
; Data
; =============================================================================
.segment "RODATA"

palette_data:
    ; BG palettes
    .byte $0F, $00, $10, $30  ; BG 0: Floor
    .byte $0F, $06, $16, $26  ; BG 1: Walls (red)
    .byte $0F, $01, $11, $21  ; BG 2: Tower base (blue)
    .byte $0F, $09, $19, $29  ; BG 3: HUD (green)

    ; Sprite palettes
    .byte $0F, $11, $21, $30  ; SPR 0: Player (blue)
    .byte $0F, $06, $16, $26  ; SPR 1: Enemies (red)
    .byte $0F, $28, $38, $30  ; SPR 2: Bullets (yellow)
    .byte $0F, $12, $22, $32  ; SPR 3: XP sparks (cyan)
