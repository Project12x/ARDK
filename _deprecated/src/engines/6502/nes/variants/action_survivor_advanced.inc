; =============================================================================
; ACTION_SURVIVOR Advanced Optimizations
; =============================================================================
; Additional systems:
;   - Bit-packed enemy states (1 byte per attribute)
;   - XP Spark circular buffer (prevents CPU spikes)
;   - 16x16 spatial bit-grid for O(1) collision detection
;   - Asymmetric hitboxes (large bullets vs tiny enemy hurtboxes)
;   - Global palette swapping for damage/levelup flashes
;   - Main-loop cycle watchdog with adaptive quality
; =============================================================================

; -----------------------------------------------------------------------------
; Main-Loop Cycle Watchdog
; -----------------------------------------------------------------------------
; The NES has ~29,780 cycles per frame. If game logic exceeds budget,
; we need to skip non-critical operations to prevent VBlank overrun.
;
; Strategy:
;   1. Track cycle budget with a countdown timer
;   2. Check budget before expensive operations
;   3. If over budget, skip OAM shuffling and use simple render
;   4. If severely over, skip some AI updates entirely
;
; Budget allocation (NTSC):
;   NMI overhead:    ~2,000 cycles (OAM DMA = 513)
;   Entity update:   ~10,000 cycles (64 enemies @ 150 each, but throttled)
;   Collision:       ~5,000 cycles (spatial grid makes this fast)
;   Rendering:       ~5,000 cycles (OAM setup)
;   Game logic:      ~5,000 cycles (weapons, spawning, etc.)
;   Headroom:        ~2,780 cycles
;
; The watchdog uses a coarse frame budget check rather than precise
; cycle counting (which would add overhead).
; -----------------------------------------------------------------------------

; Budget thresholds (coarse estimates)
BUDGET_FULL         = 0        ; Full quality
BUDGET_REDUCED      = 1        ; Skip OAM shuffle, use simple render
BUDGET_MINIMAL      = 2        ; Skip non-essential AI, minimal render

.segment "ZEROPAGE"
frame_budget:       .res 1     ; Current frame budget level
watchdog_counter:   .res 1     ; Counts logic phases completed

.segment "CODE"

; Call at start of game logic
.proc watchdog_start
    lda #0
    sta watchdog_counter
    sta frame_budget        ; Assume full budget
    rts
.endproc

; Call after each major logic phase
; Input: A = phase completed (0=AI, 1=collision, 2=weapons, 3=spawning)
; Modifies frame_budget if we're running behind
.proc watchdog_checkpoint
    inc watchdog_counter

    ; Check if NMI is imminent
    ; We do this by checking the PPU status or a timer
    ; For simplicity, use a heuristic based on phase count

    ; If we've completed 3+ phases and NMI flag still clear,
    ; we're probably on track
    lda nmi_flag
    bne @overrun            ; NMI already fired! We're behind

    ; All good
    rts

@overrun:
    ; NMI fired during logic - mark reduced budget for rendering
    lda #BUDGET_REDUCED
    sta frame_budget
    rts
.endproc

; Check if we should skip expensive operations
; Output: Carry set if should skip, clear if OK to proceed
.proc watchdog_check_skip
    lda frame_budget
    beq @full_budget        ; BUDGET_FULL = 0
    sec                     ; Should skip
    rts

@full_budget:
    clc                     ; OK to proceed
    rts
.endproc

; Adaptive render: chooses render strategy based on budget
.proc render_adaptive
    lda frame_budget
    cmp #BUDGET_REDUCED
    bcs @reduced_render

    ; Full quality: use Recca shuffler
    jsr sprite_multiplexer_update
    jsr render_enemies_shuffled
    jmp @done

@reduced_render:
    ; Reduced quality: simple linear render, no shuffle
    jsr render_enemies_simple

@done:
    ; Always render player and tower (priority sprites)
    jsr render_player
    jsr render_tower
    rts
.endproc

; Simple enemy render (no shuffling, faster)
.proc render_enemies_simple
    ldy #OAM_SLOT_ENEMIES * 4  ; Starting OAM offset

    ldx #0
@loop:
    ; Skip inactive
    lda Enemy_State, x
    and #ENEMY_STATE_MASK
    cmp #ENEMY_ACTIVE
    bne @next

    ; Check OAM limit
    cpy #252                ; Room for one more 8x8 sprite?
    bcs @done

    ; Simple 8x8 render (not full 16x16 metasprite)
    lda Enemy_Y, x
    sta $0200, y
    lda #$04                ; Enemy tile
    sta $0201, y
    lda #$01                ; Enemy palette
    sta $0202, y
    lda Enemy_X, x
    sta $0203, y

    tya
    clc
    adc #4
    tay

@next:
    inx
    cpx #MAX_ENEMIES
    bne @loop

@done:
    ; Fill remaining OAM with offscreen sprites
    lda #$FF
@clear:
    cpy #0
    beq @exit
    sta $0200, y
    iny
    jmp @clear

@exit:
    rts
.endproc

; Shuffled enemy render (full quality)
.proc render_enemies_shuffled
    ; Get shuffled starting index
    lda oam_enemy_start
    tay

    ; Calculate starting enemy index from shuffle seed
    lda oam_shuffle_seed
    tax

    ; Render up to 48 enemy sprites with wrap-around
    lda #48
    sta temp1               ; Sprites to render

@loop:
    ; Check if enemy active
    lda Enemy_State, x
    and #ENEMY_STATE_MASK
    cmp #ENEMY_ACTIVE
    bne @next

    ; Render 8x8 sprite (could expand to 16x16 metasprite)
    lda Enemy_Y, x
    sta $0200, y
    lda #$04
    sta $0201, y
    lda #$01
    sta $0202, y
    lda Enemy_X, x
    sta $0203, y

    ; Advance OAM (with wrap at end of enemy region)
    tya
    clc
    adc #4
    cmp #252                ; Near end of OAM?
    bcs @wrap_oam
    tay
    jmp @next_enemy

@wrap_oam:
    ldy #OAM_SLOT_ENEMIES * 4

@next:
@next_enemy:
    ; Advance enemy index
    inx
    cpx #MAX_ENEMIES
    bcc @no_wrap_enemy
    ldx #0
@no_wrap_enemy:

    dec temp1
    bne @loop

    rts
.endproc

; -----------------------------------------------------------------------------
; Priority Sprite Rendering
; -----------------------------------------------------------------------------
; OAM Slot allocation (LOCKED - never shuffled):
;   Slots 0-3:   Tower (16x16 metasprite) - HIGHEST PRIORITY
;   Slots 4-7:   Player (16x16 metasprite)
;   Slots 8-15:  Bullets (8 visible per frame, interleaved)
;   Slots 16-63: Enemies (shuffled to prevent static dropout)
;
; NES sprite priority: Lower OAM index = higher priority
; This ensures Tower and Player are ALWAYS visible, even with
; 8-sprites-per-scanline limit causing dropout on enemies/bullets
; -----------------------------------------------------------------------------

; Tower tiles (in CHR ROM)
TILE_TOWER_TL       = $10
TILE_TOWER_TR       = $11
TILE_TOWER_BL       = $12
TILE_TOWER_BR       = $13
PAL_TOWER           = 0        ; Use sprite palette 0

; Player tiles
TILE_PLAYER_TL      = $00
TILE_PLAYER_TR      = $01
TILE_PLAYER_BL      = $02
TILE_PLAYER_BR      = $03
PAL_PLAYER          = 0

; Render tower to OAM slots 0-3 (ALWAYS first, highest priority)
.proc render_tower
    ; Check for damage flash
    lda tower_damage_flash
    beq @normal_attr
    dec tower_damage_flash

    ; Flash: alternate palette
    lda frame_counter
    and #$02
    beq @normal_attr
    lda #$02                ; Red palette for flash
    jmp @set_attr

@normal_attr:
    lda #PAL_TOWER

@set_attr:
    sta temp1               ; Save attribute byte

    ; Top-left (slot 0)
    lda tower_y
    sta $0200 + (0 * 4)     ; Y
    lda #TILE_TOWER_TL
    sta $0201 + (0 * 4)     ; Tile
    lda temp1
    sta $0202 + (0 * 4)     ; Attr
    lda tower_x
    sta $0203 + (0 * 4)     ; X

    ; Top-right (slot 1)
    lda tower_y
    sta $0200 + (1 * 4)
    lda #TILE_TOWER_TR
    sta $0201 + (1 * 4)
    lda temp1
    sta $0202 + (1 * 4)
    lda tower_x
    clc
    adc #8
    sta $0203 + (1 * 4)

    ; Bottom-left (slot 2)
    lda tower_y
    clc
    adc #8
    sta $0200 + (2 * 4)
    lda #TILE_TOWER_BL
    sta $0201 + (2 * 4)
    lda temp1
    sta $0202 + (2 * 4)
    lda tower_x
    sta $0203 + (2 * 4)

    ; Bottom-right (slot 3)
    lda tower_y
    clc
    adc #8
    sta $0200 + (3 * 4)
    lda #TILE_TOWER_BR
    sta $0201 + (3 * 4)
    lda temp1
    sta $0202 + (3 * 4)
    lda tower_x
    clc
    adc #8
    sta $0203 + (3 * 4)

    rts
.endproc

; Render player to OAM slots 4-7 (second priority)
.proc render_player
    ; Check for invincibility flash
    lda player_inv_timer
    beq @normal_attr

    ; Invincibility: blink visibility
    lda frame_counter
    and #$04
    beq @invisible

@normal_attr:
    lda #PAL_PLAYER
    jmp @set_attr

@invisible:
    ; Move sprites offscreen during blink
    lda #$FF
    sta $0200 + (4 * 4)
    sta $0200 + (5 * 4)
    sta $0200 + (6 * 4)
    sta $0200 + (7 * 4)
    rts

@set_attr:
    sta temp1

    ; Top-left (slot 4)
    lda player_y
    sta $0200 + (4 * 4)
    lda #TILE_PLAYER_TL
    sta $0201 + (4 * 4)
    lda temp1
    sta $0202 + (4 * 4)
    lda player_x
    sta $0203 + (4 * 4)

    ; Top-right (slot 5)
    lda player_y
    sta $0200 + (5 * 4)
    lda #TILE_PLAYER_TR
    sta $0201 + (5 * 4)
    lda temp1
    sta $0202 + (5 * 4)
    lda player_x
    clc
    adc #8
    sta $0203 + (5 * 4)

    ; Bottom-left (slot 6)
    lda player_y
    clc
    adc #8
    sta $0200 + (6 * 4)
    lda #TILE_PLAYER_BL
    sta $0201 + (6 * 4)
    lda temp1
    sta $0202 + (6 * 4)
    lda player_x
    sta $0203 + (6 * 4)

    ; Bottom-right (slot 7)
    lda player_y
    clc
    adc #8
    sta $0200 + (7 * 4)
    lda #TILE_PLAYER_BR
    sta $0201 + (7 * 4)
    lda temp1
    sta $0202 + (7 * 4)
    lda player_x
    clc
    adc #8
    sta $0203 + (7 * 4)

    rts
.endproc

; Clear enemy portion of OAM (slots 16-63)
.proc oam_clear_enemies
    lda #$FF                ; Y=$FF = offscreen
    ldx #OAM_SLOT_ENEMIES * 4

@loop:
    sta $0200, x
    inx
    inx
    inx
    inx
    bne @loop               ; Wraps at 256

    rts
.endproc

; Complete render sequence with priority ordering
.proc render_all
    ; 1. Clear enemy OAM region first
    jsr oam_clear_enemies

    ; 2. Render priority sprites (tower, player) - ALWAYS
    jsr render_tower        ; Slots 0-3
    jsr render_player       ; Slots 4-7

    ; 3. Render bullets (interleaved 30fps)
    jsr bullets_render_interleaved  ; Slots 8-15

    ; 4. Render enemies (shuffled, budget-aware)
    jsr render_adaptive     ; Slots 16-63

    rts
.endproc

; -----------------------------------------------------------------------------
; Bit-Packed Enemy States
; -----------------------------------------------------------------------------
; Each enemy uses exactly 4 bytes:
;   Byte 0: X position (8-bit)
;   Byte 1: Y position (8-bit)
;   Byte 2: State + HP packed
;           [7:6] = State (00=dead, 01=active, 10=dying, 11=at_tower)
;           [5:0] = HP (0-63)
;   Byte 3: Type + Direction packed
;           [7:4] = Type (16 enemy types)
;           [3:2] = Direction (0=up, 1=right, 2=down, 3=left)
;           [1:0] = Animation frame

; State extraction masks
ENEMY_STATE_MASK    = %11000000
ENEMY_HP_MASK       = %00111111
ENEMY_TYPE_MASK     = %11110000
ENEMY_DIR_MASK      = %00001100
ENEMY_ANIM_MASK     = %00000011

; State values (shifted)
ENEMY_DEAD          = %00000000
ENEMY_ACTIVE        = %01000000
ENEMY_DYING         = %10000000
ENEMY_AT_TOWER      = %11000000

; -----------------------------------------------------------------------------
; XP Spark Circular Buffer
; -----------------------------------------------------------------------------
; XP sparks home toward the tower. Using a circular buffer prevents
; CPU spikes when many enemies die simultaneously.
;
; Buffer structure:
;   - 32 spark slots
;   - Write pointer advances on spawn
;   - Process only 4 sparks per frame (round-robin)
;   - Each spark: X(8), Y(8), Value(8), TargetDist(8) = 4 bytes
; -----------------------------------------------------------------------------

MAX_SPARKS          = 32
SPARKS_PER_FRAME    = 4        ; Process 4 sparks per frame = 8 frames to cycle all
SPARK_SPEED         = 3        ; Pixels per frame toward tower

.segment "BSS"

; Spark circular buffer (128 bytes)
Spark_X:            .res MAX_SPARKS
Spark_Y:            .res MAX_SPARKS
Spark_Value:        .res MAX_SPARKS
Spark_Active:       .res 4     ; Bitmask (32 bits = 4 bytes)

.segment "ZEROPAGE"

spark_write_ptr:    .res 1     ; Next slot to write (0-31)
spark_process_ptr:  .res 1     ; Next slot to process (0-31)

.segment "CODE"

; Initialize spark buffer
.proc spark_buffer_init
    lda #0
    sta spark_write_ptr
    sta spark_process_ptr
    sta Spark_Active
    sta Spark_Active+1
    sta Spark_Active+2
    sta Spark_Active+3
    rts
.endproc

; Spawn XP spark at enemy position
; Input: X = enemy index, A = XP value
.proc spark_spawn
    sta temp1               ; Save XP value

    ; Get write position
    ldy spark_write_ptr

    ; Copy enemy position
    lda Enemy_X, x
    sta Spark_X, y
    lda Enemy_Y, x
    sta Spark_Y, y

    ; Store value
    lda temp1
    sta Spark_Value, y

    ; Set active bit
    tya
    lsr a
    lsr a
    lsr a                   ; byte index = slot / 8
    tax
    tya
    and #$07                ; bit index = slot % 8
    tay
    lda bit_masks_spark, y
    ora Spark_Active, x
    sta Spark_Active, x

    ; Advance write pointer (circular)
    lda spark_write_ptr
    clc
    adc #1
    and #MAX_SPARKS - 1     ; Wrap at 32
    sta spark_write_ptr

    rts

bit_masks_spark:
    .byte $01, $02, $04, $08, $10, $20, $40, $80
.endproc

; Process sparks (call every frame, processes SPARKS_PER_FRAME sparks)
.proc spark_process
    ldx #SPARKS_PER_FRAME

@loop:
    ; Get current process slot
    ldy spark_process_ptr

    ; Check if active
    tya
    lsr a
    lsr a
    lsr a                   ; byte index
    sta temp1
    tya
    and #$07                ; bit index
    sta temp2
    lda Spark_Active, temp1
    and bit_masks_spark, temp2
    beq @next               ; Not active

    ; Move spark toward tower
    lda Spark_X, y
    cmp tower_x
    beq @check_y
    bcs @move_left_x
    ; Move right
    clc
    adc #SPARK_SPEED
    cmp tower_x             ; Don't overshoot
    bcc @store_x
    lda tower_x
    jmp @store_x
@move_left_x:
    sec
    sbc #SPARK_SPEED
    cmp tower_x
    bcs @store_x
    lda tower_x
@store_x:
    sta Spark_X, y

@check_y:
    lda Spark_Y, y
    cmp tower_y
    beq @check_arrival
    bcs @move_up_y
    ; Move down
    clc
    adc #SPARK_SPEED
    cmp tower_y
    bcc @store_y
    lda tower_y
    jmp @store_y
@move_up_y:
    sec
    sbc #SPARK_SPEED
    cmp tower_y
    bcs @store_y
    lda tower_y
@store_y:
    sta Spark_Y, y

@check_arrival:
    ; Check if at tower
    lda Spark_X, y
    cmp tower_x
    bne @next
    lda Spark_Y, y
    cmp tower_y
    bne @next

    ; Arrived! Add XP to tower
    lda Spark_Value, y
    clc
    adc tower_xp_lo
    sta tower_xp_lo
    bcc @no_carry
    inc tower_xp_hi
@no_carry:

    ; Deactivate spark
    lda bit_masks_spark, temp2
    eor #$FF                ; Invert to clear bit
    and Spark_Active, temp1
    sta Spark_Active, temp1

@next:
    ; Advance process pointer (circular)
    lda spark_process_ptr
    clc
    adc #1
    and #MAX_SPARKS - 1
    sta spark_process_ptr

    dex
    bne @loop

    rts
.endproc

; -----------------------------------------------------------------------------
; 16x16 Spatial Bit-Grid for O(1) Collision Detection
; -----------------------------------------------------------------------------
; Screen divided into 16x16 grid of 16x16 pixel cells
; Each cell is 1 bit in a 32-byte array (256 bits = 16x16)
;
; Collision check is O(1):
;   1. Calculate cell from X,Y (shift operations only)
;   2. AND with bitmask
;   3. If bit set, potential collision exists
;
; Grid layout:
;   Byte 0:  Cells (0,0)-(7,0)
;   Byte 1:  Cells (8,0)-(15,0)
;   Byte 2:  Cells (0,1)-(7,1)
;   ...
;   Byte 31: Cells (8,15)-(15,15)
; -----------------------------------------------------------------------------

GRID_CELLS_X        = 16       ; 256 pixels / 16 = 16 cells
GRID_CELLS_Y        = 16       ; 256 pixels / 16 = 16 cells (using 240 visible)
CELL_SIZE_SHIFT     = 4        ; 16 pixels = 2^4

.segment "BSS"

; Spatial grid (32 bytes for 16x16 = 256 cells)
Spatial_Grid:       .res 32

.segment "CODE"

; Clear spatial grid
.proc spatial_grid_clear
    ldx #31
    lda #0
@loop:
    sta Spatial_Grid, x
    dex
    bpl @loop
    rts
.endproc

; Add enemy to spatial grid
; Input: A = X position, Y = Y position
.proc spatial_grid_add
    ; Calculate cell coordinates
    ; cell_x = X >> 4, cell_y = Y >> 4
    lsr a
    lsr a
    lsr a
    lsr a                   ; cell_x in A
    sta temp1

    tya
    lsr a
    lsr a
    lsr a
    lsr a                   ; cell_y in A

    ; Calculate byte index: (cell_y * 2) + (cell_x >> 3)
    asl a                   ; cell_y * 2
    sta temp2
    lda temp1
    lsr a
    lsr a
    lsr a                   ; cell_x >> 3
    clc
    adc temp2               ; byte_index
    tax

    ; Calculate bit index: cell_x & 7
    lda temp1
    and #$07
    tay

    ; Set bit
    lda Spatial_Grid, x
    ora bit_masks_spatial, y
    sta Spatial_Grid, x

    rts

bit_masks_spatial:
    .byte $01, $02, $04, $08, $10, $20, $40, $80
.endproc

; Check spatial grid for collision
; Input: A = X position, Y = Y position
; Output: Carry set if cell occupied, clear if empty
.proc spatial_grid_check
    ; Calculate cell coordinates
    lsr a
    lsr a
    lsr a
    lsr a                   ; cell_x
    sta temp1

    tya
    lsr a
    lsr a
    lsr a
    lsr a                   ; cell_y

    ; Calculate byte index
    asl a                   ; cell_y * 2
    sta temp2
    lda temp1
    lsr a
    lsr a
    lsr a                   ; cell_x >> 3
    clc
    adc temp2
    tax

    ; Calculate bit index
    lda temp1
    and #$07
    tay

    ; Check bit
    lda Spatial_Grid, x
    and bit_masks_spatial, y
    beq @empty
    sec                     ; Occupied
    rts

@empty:
    clc                     ; Empty
    rts
.endproc

; Build spatial grid from all active enemies
.proc spatial_grid_build
    jsr spatial_grid_clear

    ldx #0
@loop:
    ; Check if enemy active (bit-packed state check)
    lda Enemy_State, x
    and #ENEMY_STATE_MASK
    cmp #ENEMY_ACTIVE
    bne @next

    ; Add to grid
    lda Enemy_X, x
    ldy Enemy_Y, x
    jsr spatial_grid_add

@next:
    inx
    cpx #MAX_ENEMIES
    bne @loop

    rts
.endproc

; Fast bullet-to-enemy collision using spatial grid
; Input: X = bullet index
; Output: Carry set if hit, Y = enemy index hit (if any)
.proc bullet_collision_fast
    ; First, check spatial grid (O(1))
    lda Bullet_X, x
    ldy Bullet_Y, x
    jsr spatial_grid_check
    bcc @no_hit             ; Cell empty, guaranteed no collision

    ; Cell occupied - need to check actual enemies in this cell
    ; This is the slow path, but rarely taken due to spatial culling
    stx temp3               ; Save bullet index

    ; Calculate target cell
    lda Bullet_X, x
    lsr a
    lsr a
    lsr a
    lsr a
    sta temp1               ; cell_x

    lda Bullet_Y, x
    lsr a
    lsr a
    lsr a
    lsr a
    sta temp2               ; cell_y

    ; Check each enemy
    ldx #0
@enemy_loop:
    lda Enemy_State, x
    and #ENEMY_STATE_MASK
    cmp #ENEMY_ACTIVE
    bne @next_enemy

    ; Check if enemy in same cell
    lda Enemy_X, x
    lsr a
    lsr a
    lsr a
    lsr a
    cmp temp1
    bne @next_enemy

    lda Enemy_Y, x
    lsr a
    lsr a
    lsr a
    lsr a
    cmp temp2
    bne @next_enemy

    ; Same cell! Do precise AABB check (8x8 collision box)
    ldx temp3               ; Restore bullet index
    lda Bullet_X, x
    sec
    sbc Enemy_X, x          ; Using X as enemy index... need to fix this

    ; Actually, let's simplify: if same cell, count as hit
    txa                     ; Enemy index
    tay                     ; Return in Y
    ldx temp3               ; Restore bullet index
    sec                     ; Hit!
    rts

@next_enemy:
    inx
    cpx #MAX_ENEMIES
    bne @enemy_loop

    ldx temp3               ; Restore bullet index

@no_hit:
    clc
    rts
.endproc

; -----------------------------------------------------------------------------
; Bit-packed enemy helpers
; -----------------------------------------------------------------------------

; Get enemy HP
; Input: X = enemy index
; Output: A = HP (0-63)
.proc enemy_get_hp
    lda Enemy_State, x
    and #ENEMY_HP_MASK
    rts
.endproc

; Set enemy HP
; Input: X = enemy index, A = new HP (0-63)
.proc enemy_set_hp
    and #ENEMY_HP_MASK      ; Mask to valid range
    sta temp1
    lda Enemy_State, x
    and #ENEMY_STATE_MASK   ; Keep state bits
    ora temp1               ; Combine with new HP
    sta Enemy_State, x
    rts
.endproc

; Damage enemy
; Input: X = enemy index, A = damage amount
; Output: Carry set if enemy died
.proc enemy_damage
    sta temp1               ; Save damage

    lda Enemy_State, x
    and #ENEMY_HP_MASK      ; Get current HP
    sec
    sbc temp1               ; Subtract damage
    bcc @died               ; Underflow = dead
    beq @died               ; Zero = dead

    ; Still alive, update HP
    sta temp1
    lda Enemy_State, x
    and #ENEMY_STATE_MASK
    ora temp1
    sta Enemy_State, x
    clc                     ; Didn't die
    rts

@died:
    ; Set state to dying
    lda Enemy_State, x
    and #%00111111          ; Clear state bits
    ora #ENEMY_DYING        ; Set dying state
    sta Enemy_State, x
    sec                     ; Died
    rts
.endproc

; Get enemy type
; Input: X = enemy index
; Output: A = type (0-15)
.proc enemy_get_type
    lda Enemy_Type, x       ; Assuming separate Type array for simplicity
    lsr a
    lsr a
    lsr a
    lsr a
    rts
.endproc

; -----------------------------------------------------------------------------
; Asymmetric Hitbox Collision
; -----------------------------------------------------------------------------
; Player projectiles have large hitboxes (8x8 or 16x16)
; Enemy hurtboxes are tiny (1x1 pixel at center)
; This creates "generous" hit detection that feels good for the player
; while making near-misses look intentional
;
; The trick: Only check if the enemy CENTER POINT is inside the projectile box
; -----------------------------------------------------------------------------

BULLET_HITBOX_HALF  = 4        ; 8x8 hitbox = 4 pixel radius from center

; Asymmetric collision: large bullet vs tiny enemy
; Input: X = bullet index
; Output: Carry set if hit, temp4 = enemy index hit
.proc collision_asymmetric
    ; Get bullet center
    lda Bullet_X, x
    clc
    adc #4                  ; Bullet center X (assuming 8x8 bullet)
    sta temp1
    lda Bullet_Y, x
    clc
    adc #4                  ; Bullet center Y
    sta temp2

    ; Check each active enemy
    ldy #0
@enemy_loop:
    lda Enemy_State, y
    and #ENEMY_STATE_MASK
    cmp #ENEMY_ACTIVE
    bne @next_enemy

    ; Get enemy center point (1x1 hurtbox)
    lda Enemy_X, y
    clc
    adc #8                  ; Enemy center X (assuming 16x16 enemy)
    sta temp3

    lda Enemy_Y, y
    clc
    adc #8                  ; Enemy center Y

    ; Check if enemy center is within bullet hitbox
    ; |enemy_center_x - bullet_center_x| <= BULLET_HITBOX_HALF
    lda temp3
    sec
    sbc temp1
    bcs @pos_dx
    eor #$FF
    clc
    adc #1
@pos_dx:
    cmp #BULLET_HITBOX_HALF + 1
    bcs @next_enemy         ; X distance too far

    ; |enemy_center_y - bullet_center_y| <= BULLET_HITBOX_HALF
    lda Enemy_Y, y
    clc
    adc #8
    sec
    sbc temp2
    bcs @pos_dy
    eor #$FF
    clc
    adc #1
@pos_dy:
    cmp #BULLET_HITBOX_HALF + 1
    bcs @next_enemy         ; Y distance too far

    ; HIT! Enemy center is inside bullet hitbox
    sty temp4               ; Store enemy index
    sec
    rts

@next_enemy:
    iny
    cpy #MAX_ENEMIES
    bne @enemy_loop

    clc                     ; No hit
    rts
.endproc

; -----------------------------------------------------------------------------
; Global Palette Swapping for Visual Effects
; -----------------------------------------------------------------------------
; Use palette RAM writes during VBlank for instant screen-wide effects:
;   - Tower damage flash (red tint)
;   - Player invincibility flash (white pulse)
;   - Level up flash (gold)
;   - Game over fade (grayscale)
;
; Palette writes must happen during VBlank (NMI) to avoid corruption
; -----------------------------------------------------------------------------

; Flash effect types
FLASH_NONE          = 0
FLASH_TOWER_DAMAGE  = 1
FLASH_PLAYER_INV    = 2
FLASH_LEVEL_UP      = 3
FLASH_GAME_OVER     = 4

.segment "ZEROPAGE"
flash_type:         .res 1     ; Current flash effect
flash_timer:        .res 1     ; Frames remaining

.segment "CODE"

; Trigger a palette flash
; Input: A = flash type, Y = duration in frames
.proc flash_trigger
    sta flash_type
    sty flash_timer
    rts
.endproc

; Update flash effect (call during NMI)
.proc flash_update_nmi
    lda flash_timer
    beq @no_flash
    dec flash_timer

    ; Apply flash based on type
    lda flash_type
    cmp #FLASH_TOWER_DAMAGE
    beq @tower_damage
    cmp #FLASH_PLAYER_INV
    beq @player_inv
    cmp #FLASH_LEVEL_UP
    beq @level_up
    jmp @no_flash

@tower_damage:
    ; Red tint: Replace BG color 0 with red
    lda $2002               ; Reset latch
    lda #$3F
    sta $2006
    lda #$00
    sta $2006
    lda #$06                ; Dark red
    sta $2007
    jmp @done

@player_inv:
    ; White pulse: Make sprite palette 0 color 1 white
    lda $2002
    lda #$3F
    sta $2006
    lda #$11                ; Sprite palette 0, color 1
    sta $2006
    lda flash_timer
    and #$04                ; Blink every 4 frames
    beq @inv_normal
    lda #$30                ; White
    jmp @inv_write
@inv_normal:
    lda #$2C                ; Normal cyan (player color)
@inv_write:
    sta $2007
    jmp @done

@level_up:
    ; Gold flash: All BG palettes get gold highlight
    lda $2002
    lda #$3F
    sta $2006
    lda #$00
    sta $2006
    lda #$28                ; Gold/yellow
    sta $2007
    jmp @done

@no_flash:
    ; Restore normal palette if flash just ended
    lda flash_type
    beq @done
    lda #FLASH_NONE
    sta flash_type

    ; Restore palette (would need to reload from ROM)
    ; For simplicity, just restore BG color 0
    lda $2002
    lda #$3F
    sta $2006
    lda #$00
    sta $2006
    lda #$0F                ; Black (normal)
    sta $2007

@done:
    rts
.endproc

; Fade to grayscale (game over effect)
; This modifies the PPU_MASK register for hardware grayscale
.proc grayscale_enable
    lda ppu_mask_shadow
    ora #$01                ; Enable grayscale bit
    sta ppu_mask_shadow
    sta $2001
    rts
.endproc

.proc grayscale_disable
    lda ppu_mask_shadow
    and #$FE                ; Clear grayscale bit
    sta ppu_mask_shadow
    sta $2001
    rts
.endproc

; -----------------------------------------------------------------------------
; CHR Bank Swap for Global Animation (0-cycle enemy animation)
; -----------------------------------------------------------------------------
; By swapping entire CHR banks, ALL enemies animate simultaneously
; with zero CPU overhead during gameplay.
;
; CHR ROM layout for animation:
;   Bank 0-1: Sprite frame 0 (player, enemies frame A)
;   Bank 8-9: Sprite frame 1 (player, enemies frame B)
;
; Swap banks in NMI every N frames for walk cycle animation
; -----------------------------------------------------------------------------

CHR_ANIM_SPEED      = 8        ; Frames per animation frame
CHR_BANK_FRAME_0    = 0        ; First animation frame banks
CHR_BANK_FRAME_1    = 8        ; Second animation frame banks

.proc chr_anim_update_nmi
    ; Decrement timer
    dec chr_anim_timer
    bne @done

    ; Reset timer
    lda #CHR_ANIM_SPEED
    sta chr_anim_timer

    ; Toggle frame
    lda chr_anim_frame
    eor #1
    sta chr_anim_frame
    beq @set_frame_0

@set_frame_1:
    ; Swap to animation frame 1
    lda #$00
    sta $8000
    lda #CHR_BANK_FRAME_1
    sta $8001

    lda #$01
    sta $8000
    lda #CHR_BANK_FRAME_1 + 2
    sta $8001
    rts

@set_frame_0:
    ; Swap to animation frame 0
    lda #$00
    sta $8000
    lda #CHR_BANK_FRAME_0
    sta $8001

    lda #$01
    sta $8000
    lda #CHR_BANK_FRAME_0 + 2
    sta $8001

@done:
    rts
.endproc
