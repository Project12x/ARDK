; =============================================================================
; ACTION MODULE - Powerup System
; XP gems, health pickups, and item collection with magnet effect
; =============================================================================

.include "../../engine.inc"

; Only compile if action module is enabled and powerups are used
.if (.defined(MODULE_ACTION_ENABLED) .and .defined(USE_POWERUPS))

; -----------------------------------------------------------------------------
; Zero Page Variables ($48+)
; -----------------------------------------------------------------------------
.segment "ZEROPAGE"

; Powerup spawn parameters (exported for use by game code)
.exportzp powerup_spawn_x
powerup_spawn_x:    .res 1      ; $48

.exportzp powerup_spawn_y
powerup_spawn_y:    .res 1      ; $49

.exportzp powerup_spawn_type
powerup_spawn_type: .res 1      ; $4A

.exportzp powerup_count
powerup_count: .res 1           ; $4B - Active powerup count

; -----------------------------------------------------------------------------
; BSS - Powerup Pool
; -----------------------------------------------------------------------------
.segment "BSS"

; Powerup structure (8 bytes per powerup)
; [x, y, type, lifetime, flags, vx, vy, _pad]
powerup_pool: .res MAX_POWERUPS * 8

.ifndef POWERUP_SIZE
    POWERUP_SIZE = 8
.endif

; Offsets into powerup structure
PWR_X       = 0
PWR_Y       = 1
PWR_TYPE    = 2     ; Type (XP, health, etc.)
PWR_LIFE    = 3     ; Lifetime in frames (0 = infinite)
PWR_FLAGS   = 4     ; Active flag, magnet flag
PWR_VX      = 5     ; Velocity X (for magnet attraction)
PWR_VY      = 6     ; Velocity Y (for magnet attraction)
PWR_PAD     = 7

; Powerup flags
PWR_FLAG_ACTIVE     = $01
PWR_FLAG_MAGNETIC   = $02   ; Being attracted to player

; Powerup types (defined in action.inc)
; PWR_TYPE_XP_GEM     = 0
; PWR_TYPE_HEALTH     = 1
; PWR_TYPE_COIN       = 2
; PWR_TYPE_MAGNET     = 3

; Powerup values
PWR_VALUE_XP_GEM    = 1
PWR_VALUE_HEALTH    = 10
PWR_VALUE_COIN      = 5

; Magnet range (squared distance for efficiency)
MAGNET_RANGE_SQ     = 64 * 64   ; 64 pixel radius
MAGNET_SPEED        = 2         ; Pixels per frame attraction

; -----------------------------------------------------------------------------
; CODE
; -----------------------------------------------------------------------------
.segment "CODE"

; -----------------------------------------------------------------------------
; powerup_init
; Initializes powerup system
; Input: None
; Output: None
; Destroys: A, X
; -----------------------------------------------------------------------------
.export powerup_init
.proc powerup_init
    lda #0
    sta powerup_count

    ; Clear all powerup slots
    ldx #0
@loop:
    sta a:powerup_pool + PWR_FLAGS, x
    txa
    clc
    adc #POWERUP_SIZE
    tax
    cpx #(MAX_POWERUPS * POWERUP_SIZE)
    bne @loop

    rts
.endproc

; -----------------------------------------------------------------------------
; powerup_spawn
; Spawns a new powerup
; Input:
;   powerup_spawn_x (ZP) - X position
;   powerup_spawn_y (ZP) - Y position
;   powerup_spawn_type (ZP) - Powerup type
; Output:
;   X = powerup index (or $FF if failed)
;   Carry = 1 if success, 0 if pool full
; Destroys: A, X
; -----------------------------------------------------------------------------
.export powerup_spawn
.proc powerup_spawn
    ; Find free slot
    ldx #0
@find_slot:
    lda a:powerup_pool + PWR_FLAGS, x
    and #PWR_FLAG_ACTIVE
    beq @found_slot

    txa
    clc
    adc #POWERUP_SIZE
    tax
    cpx #(MAX_POWERUPS * POWERUP_SIZE)
    bne @find_slot

    ; No free slots
    ldx #$FF
    clc
    rts

@found_slot:
    ; Initialize powerup
    lda powerup_spawn_x
    sta a:powerup_pool + PWR_X, x

    lda powerup_spawn_y
    sta a:powerup_pool + PWR_Y, x

    lda powerup_spawn_type
    sta a:powerup_pool + PWR_TYPE, x

    lda #0              ; Infinite lifetime (or set to 600 for 10 seconds)
    sta a:powerup_pool + PWR_LIFE, x

    lda #PWR_FLAG_ACTIVE
    sta a:powerup_pool + PWR_FLAGS, x

    lda #0
    sta a:powerup_pool + PWR_VX, x
    sta a:powerup_pool + PWR_VY, x

    ; Increment count
    inc powerup_count

    sec
    rts
.endproc

; -----------------------------------------------------------------------------
; powerup_update_all
; Updates all active powerups (magnet effect, lifetime, player collision)
; Input:
;   player_x (ZP) - Player X position
;   player_y (ZP) - Player Y position
; Output: None
; Destroys: A, X, Y
; -----------------------------------------------------------------------------
.export powerup_update_all
.proc powerup_update_all
    lda powerup_count
    bne @start
    jmp @done           ; Early exit if no powerups

@start:
    ldx #0
@loop:
    ; Check if active
    lda a:powerup_pool + PWR_FLAGS, x
    and #PWR_FLAG_ACTIVE
    bne @active
    jmp @next
@active:

    ; Check lifetime (if not infinite)
    lda a:powerup_pool + PWR_LIFE, x
    beq @skip_lifetime
    dec a:powerup_pool + PWR_LIFE, x
    bne @skip_lifetime
    ; Lifetime expired
    jmp @deactivate
@skip_lifetime:

    ; Calculate distance to player (for magnet effect)
    lda player_x
    sec
    sbc a:powerup_pool + PWR_X, x
    sta temp_dx

    lda player_y
    sec
    sbc a:powerup_pool + PWR_Y, x
    sta temp_dy

    ; Check if within magnet range (simple Manhattan distance for speed)
    lda temp_dx
    bpl @dx_positive
    eor #$FF
    adc #1
@dx_positive:
    cmp #64
    bcs @no_magnet      ; Too far

    lda temp_dy
    bpl @dy_positive
    eor #$FF
    adc #1
@dy_positive:
    cmp #64
    bcs @no_magnet

    ; Within magnet range - apply attraction
    lda temp_dx
    bpl @move_right
    lda a:powerup_pool + PWR_X, x
    sec
    sbc #MAGNET_SPEED
    jmp @store_x
@move_right:
    lda a:powerup_pool + PWR_X, x
    clc
    adc #MAGNET_SPEED
@store_x:
    sta a:powerup_pool + PWR_X, x

    lda temp_dy
    bpl @move_down
    lda a:powerup_pool + PWR_Y, x
    sec
    sbc #MAGNET_SPEED
    jmp @store_y
@move_down:
    lda a:powerup_pool + PWR_Y, x
    clc
    adc #MAGNET_SPEED
@store_y:
    sta a:powerup_pool + PWR_Y, x

    ; Set magnetic flag
    lda a:powerup_pool + PWR_FLAGS, x
    ora #PWR_FLAG_MAGNETIC
    sta a:powerup_pool + PWR_FLAGS, x

@no_magnet:
    ; Check collision with player (8x8 hitbox)
    lda a:powerup_pool + PWR_X, x
    sec
    sbc player_x
    clc
    adc #4              ; Center offset
    bpl @check_x_range
    eor #$FF
    adc #1
@check_x_range:
    cmp #12             ; 8 + 4 pixel tolerance
    bcs @next

    lda a:powerup_pool + PWR_Y, x
    sec
    sbc player_y
    clc
    adc #4
    bpl @check_y_range
    eor #$FF
    adc #1
@check_y_range:
    cmp #12
    bcs @next

    ; Collision detected - collect powerup
    jsr collect_powerup
    jmp @deactivate

@deactivate:
    lda a:powerup_pool + PWR_FLAGS, x
    and #<~PWR_FLAG_ACTIVE
    sta a:powerup_pool + PWR_FLAGS, x
    dec powerup_count

@next:
    txa
    clc
    adc #POWERUP_SIZE
    tax
    cpx #(MAX_POWERUPS * POWERUP_SIZE)
    beq @done
    jmp @loop

@done:
    rts

temp_dx: .res 1
temp_dy: .res 1
.endproc

; -----------------------------------------------------------------------------
; collect_powerup
; Handles powerup collection effects
; Input: X = powerup pool index
; Output: None
; Destroys: A, Y
; -----------------------------------------------------------------------------
.proc collect_powerup
    ; Get powerup type
    lda a:powerup_pool + PWR_TYPE, x
    tay

    ; Jump table for powerup effects
    lda effect_table_lo, y
    sta temp_ptr
    lda effect_table_hi, y
    sta temp_ptr + 1
    jmp (temp_ptr)

effect_xp:
    lda player_xp
    clc
    adc #PWR_VALUE_XP_GEM
    sta player_xp
    bcc @done
    inc player_xp + 1   ; Handle overflow
@done:
    rts

effect_health:
    lda player_health
    clc
    adc #PWR_VALUE_HEALTH
    bcc @store
    lda #255            ; Cap at max
@store:
    sta player_health
    rts

effect_coin:
    lda player_coins
    clc
    adc #PWR_VALUE_COIN
    sta player_coins
    bcc @done
    inc player_coins + 1
@done:
    rts

effect_magnet:
    ; Activate temporary magnet (future feature)
    rts

temp_ptr: .res 2

; Effect jump table
effect_table_lo:
    .lobytes effect_xp, effect_health, effect_coin, effect_magnet
effect_table_hi:
    .hibytes effect_xp, effect_health, effect_coin, effect_magnet
.endproc

; -----------------------------------------------------------------------------
; powerup_render_all
; Renders all active powerups to OAM buffer
; Input: oam_index (ZP) - Starting OAM index
; Output: oam_index (ZP) - Updated to next free slot
; Destroys: A, X, Y
; -----------------------------------------------------------------------------
.export powerup_render_all
.proc powerup_render_all
    lda powerup_count
    beq @done

    ldx #0
    ldy oam_index

@loop:
    ; Check if active
    lda a:powerup_pool + PWR_FLAGS, x
    and #PWR_FLAG_ACTIVE
    beq @next

    ; Write to OAM
    lda a:powerup_pool + PWR_Y, x
    sec
    sbc #1
    sta $0200, y

    ; Tile based on type
    lda a:powerup_pool + PWR_TYPE, x
    clc
    adc #$20            ; Base tile for powerups
    sta $0201, y

    ; Attributes (palette 2 for powerups)
    lda #$02
    sta $0202, y

    ; X position
    lda a:powerup_pool + PWR_X, x
    sta $0203, y

    ; Next sprite
    iny
    iny
    iny
    iny

@next:
    txa
    clc
    adc #POWERUP_SIZE
    tax
    cpx #(MAX_POWERUPS * POWERUP_SIZE)
    bne @loop

    sty oam_index

@done:
    rts
.endproc

; -----------------------------------------------------------------------------
; External dependencies
; All ZP variables imported via engine.inc (player_x, player_y, player_health,
; player_xp, player_coins, oam_index)
; -----------------------------------------------------------------------------

.endif ; MODULE_ACTION_ENABLED && USE_POWERUPS
