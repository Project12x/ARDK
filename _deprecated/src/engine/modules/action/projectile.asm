; =============================================================================
; ACTION MODULE - Projectile System
; Manages bullets, weapons, and projectile entities
; =============================================================================

.include "../../engine.inc"

; Only compile if action module is enabled
.ifdef MODULE_ACTION_ENABLED

; -----------------------------------------------------------------------------
; Zero Page Variables (allocated in module_config.inc $40+)
; -----------------------------------------------------------------------------
.segment "ZEROPAGE"

; Projectile spawn parameters
.exportzp projectile_spawn_x, projectile_spawn_y
.exportzp projectile_spawn_vx, projectile_spawn_vy
.exportzp projectile_spawn_type, projectile_spawn_flags
projectile_spawn_x:     .res 1  ; $40
projectile_spawn_y:     .res 1  ; $41
projectile_spawn_vx:    .res 1  ; $42
projectile_spawn_vy:    .res 1  ; $43
projectile_spawn_type:  .res 1  ; $44
projectile_spawn_flags: .res 1  ; $45

projectile_count: .res 1        ; $46 - Active projectile count

; -----------------------------------------------------------------------------
; BSS - Projectile Pool
; -----------------------------------------------------------------------------
.segment "BSS"

; Projectile structure (8 bytes per projectile)
; [x, y, vx, vy, type, lifetime, flags, _pad]
projectile_pool: .res MAX_PROJECTILES * 8

.ifndef PROJECTILE_SIZE
    PROJECTILE_SIZE = 8
.endif

; Offsets into projectile structure
PROJ_X       = 0
PROJ_Y       = 1
PROJ_VX      = 2    ; Velocity X (signed)
PROJ_VY      = 3    ; Velocity Y (signed)
PROJ_TYPE    = 4    ; Weapon type (0=laser, 1=missile, etc.)
PROJ_LIFE    = 5    ; Lifetime counter (frames)
PROJ_FLAGS   = 6    ; Bit flags (active, friendly, etc.)
PROJ_PAD     = 7

; Projectile flags (defined in action.inc, referenced here for documentation)
; PROJ_FLAG_ACTIVE   = $01
; PROJ_FLAG_FRIENDLY = $02

; Projectile types (defined in action.inc)
; PROJ_TYPE_LASER     = 0
; PROJ_TYPE_MISSILE   = 1
; PROJ_TYPE_BEAM      = 2

; -----------------------------------------------------------------------------
; CODE
; -----------------------------------------------------------------------------
.segment "CODE"

; -----------------------------------------------------------------------------
; projectile_init
; Initializes projectile system
; Input: None
; Output: None
; Destroys: A, X
; -----------------------------------------------------------------------------
.export projectile_init
.proc projectile_init
    lda #0
    sta projectile_count

    ; Clear all projectile slots
    ldx #0
@loop:
    sta projectile_pool + PROJ_FLAGS, x
    txa
    clc
    adc #PROJECTILE_SIZE
    tax
    cpx #(MAX_PROJECTILES * PROJECTILE_SIZE)
    bne @loop

    rts
.endproc

; -----------------------------------------------------------------------------
; projectile_spawn
; Spawns a new projectile
; Input:
;   projectile_spawn_x (ZP) - X position
;   projectile_spawn_y (ZP) - Y position
;   projectile_spawn_vx (ZP) - X velocity
;   projectile_spawn_vy (ZP) - Y velocity
;   projectile_spawn_type (ZP) - Projectile type
;   projectile_spawn_flags (ZP) - Flags (friendly bit)
; Output:
;   X = projectile index (or $FF if failed)
;   Carry = 1 if success, 0 if pool full
; Destroys: A, X, Y
; -----------------------------------------------------------------------------
.export projectile_spawn
.proc projectile_spawn
    ; Find free slot
    ldx #0
@find_slot:
    lda projectile_pool + PROJ_FLAGS, x
    and #PROJ_FLAG_ACTIVE
    beq @found_slot

    txa
    clc
    adc #PROJECTILE_SIZE
    tax
    cpx #(MAX_PROJECTILES * PROJECTILE_SIZE)
    bne @find_slot

    ; No free slots
    ldx #$FF
    clc
    rts

@found_slot:
    ; Store X index for return
    txa
    pha

    ; Initialize projectile
    lda projectile_spawn_x
    sta projectile_pool + PROJ_X, x

    lda projectile_spawn_y
    sta projectile_pool + PROJ_Y, x

    lda projectile_spawn_vx
    sta projectile_pool + PROJ_VX, x

    lda projectile_spawn_vy
    sta projectile_pool + PROJ_VY, x

    lda projectile_spawn_type
    sta projectile_pool + PROJ_TYPE, x

    lda #60             ; 1 second lifetime at 60fps
    sta projectile_pool + PROJ_LIFE, x

    lda projectile_spawn_flags
    ora #PROJ_FLAG_ACTIVE
    sta projectile_pool + PROJ_FLAGS, x

    ; Increment count
    inc projectile_count

    ; Restore index and return success
    pla
    tax
    sec
    rts
.endproc

; -----------------------------------------------------------------------------
; projectile_update_all
; Updates all active projectiles (movement, lifetime, bounds check)
; Input: None
; Output: None
; Destroys: A, X, Y
; -----------------------------------------------------------------------------
.export projectile_update_all
.proc projectile_update_all
    lda projectile_count
    beq @done           ; Early exit if no projectiles

    ldx #0
@loop:
    ; Check if active
    lda projectile_pool + PROJ_FLAGS, x
    and #PROJ_FLAG_ACTIVE
    beq @next

    ; Update position
    lda projectile_pool + PROJ_X, x
    clc
    adc projectile_pool + PROJ_VX, x
    sta projectile_pool + PROJ_X, x

    lda projectile_pool + PROJ_Y, x
    clc
    adc projectile_pool + PROJ_VY, x
    sta projectile_pool + PROJ_Y, x

    ; Decrement lifetime
    dec projectile_pool + PROJ_LIFE, x
    beq @deactivate

    ; Bounds check (deactivate if off screen)
    lda projectile_pool + PROJ_X, x
    cmp #240
    bcs @deactivate     ; X >= 240 (off right or wrapped negative)

    lda projectile_pool + PROJ_Y, x
    cmp #224
    bcs @deactivate     ; Y >= 224 (off bottom or wrapped negative)

    bcc @next

@deactivate:
    lda projectile_pool + PROJ_FLAGS, x
    and #<~PROJ_FLAG_ACTIVE
    sta projectile_pool + PROJ_FLAGS, x
    dec projectile_count

@next:
    txa
    clc
    adc #PROJECTILE_SIZE
    tax
    cpx #(MAX_PROJECTILES * PROJECTILE_SIZE)
    bne @loop

@done:
    rts
.endproc

; -----------------------------------------------------------------------------
; projectile_check_collision
; Checks if a projectile collides with a point (entity position)
; Input:
;   X = projectile pool index
;   collision_x (ZP) - X position to check
;   collision_y (ZP) - Y position to check
; Output:
;   Carry = 1 if collision, 0 if no collision
; Destroys: A
; -----------------------------------------------------------------------------
.export projectile_check_collision
.proc projectile_check_collision
    ; Simple point-in-rect collision (8x8 projectile hitbox)
    lda projectile_pool + PROJ_X, x
    sec
    sbc collision_x
    bcs @check_right
    eor #$FF
    adc #1
@check_right:
    cmp #8
    bcs @no_collision

    lda projectile_pool + PROJ_Y, x
    sec
    sbc collision_y
    bcs @check_bottom
    eor #$FF
    adc #1
@check_bottom:
    cmp #8
    bcs @no_collision

    ; Collision detected
    sec
    rts

@no_collision:
    clc
    rts
.endproc

; -----------------------------------------------------------------------------
; projectile_deactivate
; Deactivates a projectile by index
; Input: X = projectile pool index
; Output: None
; Destroys: A
; -----------------------------------------------------------------------------
.export projectile_deactivate
.proc projectile_deactivate
    lda projectile_pool + PROJ_FLAGS, x
    and #<~PROJ_FLAG_ACTIVE
    sta projectile_pool + PROJ_FLAGS, x
    dec projectile_count
    rts
.endproc

; -----------------------------------------------------------------------------
; projectile_render_all
; Renders all active projectiles to OAM buffer
; Input: oam_index (ZP) - Starting OAM index
; Output: oam_index (ZP) - Updated to next free slot
; Destroys: A, X, Y
; -----------------------------------------------------------------------------
.export projectile_render_all
.proc projectile_render_all
    lda projectile_count
    beq @done

    ldx #0
    ldy oam_index

@loop:
    ; Check if active
    lda projectile_pool + PROJ_FLAGS, x
    and #PROJ_FLAG_ACTIVE
    beq @next

    ; Write to OAM
    lda projectile_pool + PROJ_Y, x
    sec
    sbc #1              ; Adjust for OAM Y offset
    sta $0200, y

    ; Tile based on type
    lda projectile_pool + PROJ_TYPE, x
    clc
    adc #$21            ; Base tile for projectiles
    sta $0201, y

    ; Attributes (palette, priority)
    lda projectile_pool + PROJ_FLAGS, x
    and #PROJ_FLAG_FRIENDLY
    beq @enemy_proj
    lda #$00            ; Palette 0 for friendly
    beq @write_attr
@enemy_proj:
    lda #$01            ; Palette 1 for enemy
@write_attr:
    sta $0202, y

    ; X position
    lda projectile_pool + PROJ_X, x
    sta $0203, y

    ; Next sprite
    iny
    iny
    iny
    iny

@next:
    txa
    clc
    adc #PROJECTILE_SIZE
    tax
    cpx #(MAX_PROJECTILES * PROJECTILE_SIZE)
    bne @loop

    sty oam_index

@done:
    rts
.endproc

.endif ; MODULE_ACTION_ENABLED
