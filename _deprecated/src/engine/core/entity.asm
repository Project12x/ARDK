; =============================================================================
; NEON SURVIVORS - Entity System
; Platform-independent entity management
; =============================================================================
;
; PORTABILITY: This file is platform-agnostic and can be used on NES/MD/PCE
; with minimal changes to entity limits.
;
; =============================================================================

.include "nes.inc"
.importzp temp1, temp2, temp3, temp4

; -----------------------------------------------------------------------------
; Entity System Configuration
; -----------------------------------------------------------------------------
.ifdef __NES__
    MAX_ENEMIES     = 14        ; NES sprite limit consideration
    MAX_PROJECTILES = 8
    MAX_PICKUPS     = 8
.endif

; Entity Types
ETYPE_NONE      = 0
ETYPE_PLAYER    = 1
ETYPE_ENEMY     = 2
ETYPE_PROJECTILE= 3
ETYPE_PICKUP    = 4
ETYPE_WEAPON_FX = 5

; Entity Flags
EFLAG_ACTIVE    = %00000001
EFLAG_VISIBLE   = %00000010
EFLAG_COLLIDE   = %00000100
EFLAG_FLASH     = %00001000     ; Invincibility flash

; Entity structure size (keep power of 2 for fast indexing)
ENTITY_SIZE     = 16

; Entity structure offsets
ENT_TYPE        = 0             ; 1 byte - entity type
ENT_FLAGS       = 1             ; 1 byte - flags
ENT_X_LO        = 2             ; 1 byte - X position (fractional)
ENT_X_HI        = 3             ; 1 byte - X position (whole)
ENT_Y_LO        = 4             ; 1 byte - Y position (fractional)
ENT_Y_HI        = 5             ; 1 byte - Y position (whole)
ENT_VX          = 6             ; 1 byte - X velocity (signed)
ENT_VY          = 7             ; 1 byte - Y velocity (signed)
ENT_HP          = 8             ; 1 byte - Health
ENT_TIMER       = 9             ; 1 byte - General timer
ENT_SUBTYPE     = 10            ; 1 byte - Enemy/weapon subtype
ENT_ANIM_FRAME  = 11            ; 1 byte - Animation frame
ENT_EXTRA1      = 12            ; 1 byte - Extra data 1
ENT_EXTRA2      = 13            ; 1 byte - Extra data 2
ENT_EXTRA3      = 14            ; 1 byte - Extra data 3
ENT_EXTRA4      = 15            ; 1 byte - Extra data 4

; -----------------------------------------------------------------------------
; Entity RAM Allocation
; -----------------------------------------------------------------------------
.segment "BSS"

enemy_pool:     .res MAX_ENEMIES * ENTITY_SIZE
proj_pool:      .res MAX_PROJECTILES * ENTITY_SIZE
pickup_pool:    .res MAX_PICKUPS * ENTITY_SIZE

enemy_count:    .res 1          ; Current active enemy count
proj_count:     .res 1
pickup_count:   .res 1

; -----------------------------------------------------------------------------
; Entity System Code
; -----------------------------------------------------------------------------
.segment "CODE"

; -----------------------------------------------------------------------------
; Initialize Entity Pools (clear all entities)
; -----------------------------------------------------------------------------
.proc init_entities
    ldx #0
    txa
@clear_enemies:
    sta enemy_pool, x
    inx
    cpx #(MAX_ENEMIES * ENTITY_SIZE)
    bne @clear_enemies
    
    ldx #0
@clear_proj:
    sta proj_pool, x
    inx
    cpx #(MAX_PROJECTILES * ENTITY_SIZE)
    bne @clear_proj
    
    ldx #0
@clear_pickups:
    sta pickup_pool, x
    inx
    cpx #(MAX_PICKUPS * ENTITY_SIZE)
    bne @clear_pickups
    
    sta enemy_count
    sta proj_count
    sta pickup_count
    
    rts
.endproc

; -----------------------------------------------------------------------------
; Find Free Entity Slot
; Input: X = pool base offset
; Output: X = entity offset, Carry = 0 if found, 1 if full
; -----------------------------------------------------------------------------
.proc find_free_enemy
    ldx #0
@loop:
    lda enemy_pool + ENT_TYPE, x
    beq @found              ; Type 0 = free slot
    txa
    clc
    adc #ENTITY_SIZE
    tax
    cpx #(MAX_ENEMIES * ENTITY_SIZE)
    bne @loop
    
    ; Pool full
    sec
    rts
    
@found:
    clc
    rts
.endproc

; -----------------------------------------------------------------------------
; Spawn Enemy
; Input: A = enemy subtype, temp1/temp2 = X/Y position
; Output: Carry = 0 if spawned, 1 if pool full
; -----------------------------------------------------------------------------
.proc spawn_enemy
    pha                     ; Save subtype
    jsr find_free_enemy
    bcs @full
    
    ; Initialize entity
    lda #ETYPE_ENEMY
    sta enemy_pool + ENT_TYPE, x
    lda #EFLAG_ACTIVE | EFLAG_VISIBLE | EFLAG_COLLIDE
    sta enemy_pool + ENT_FLAGS, x
    
    lda #0
    sta enemy_pool + ENT_X_LO, x
    lda temp1
    sta enemy_pool + ENT_X_HI, x
    
    lda #0
    sta enemy_pool + ENT_Y_LO, x
    lda temp2
    sta enemy_pool + ENT_Y_HI, x
    
    pla                     ; Restore subtype
    sta enemy_pool + ENT_SUBTYPE, x
    
    ; Set HP based on subtype (would lookup in table)
    lda #3
    sta enemy_pool + ENT_HP, x
    
    inc enemy_count
    clc
    rts
    
@full:
    pla                     ; Clean up stack
    sec
    rts
.endproc

; -----------------------------------------------------------------------------
; Kill Entity (mark as inactive)
; Input: X = entity offset in pool
; -----------------------------------------------------------------------------
.proc kill_enemy
    lda #ETYPE_NONE
    sta enemy_pool + ENT_TYPE, x
    dec enemy_count
    rts
.endproc

; -----------------------------------------------------------------------------
; Update All Enemies (called each frame)
; -----------------------------------------------------------------------------
.proc update_all_enemies
    ldx #0
@loop:
    lda enemy_pool + ENT_TYPE, x
    beq @next               ; Skip inactive
    
    ; Apply velocity to position (8.8 fixed point)
    lda enemy_pool + ENT_VX, x
    clc
    adc enemy_pool + ENT_X_LO, x
    sta enemy_pool + ENT_X_LO, x
    lda enemy_pool + ENT_VX, x
    bpl @vx_pos
    lda #$FF                ; Sign extend negative
    jmp @vx_done
@vx_pos:
    lda #$00
@vx_done:
    adc enemy_pool + ENT_X_HI, x
    sta enemy_pool + ENT_X_HI, x
    
    ; Same for Y velocity
    lda enemy_pool + ENT_VY, x
    clc
    adc enemy_pool + ENT_Y_LO, x
    sta enemy_pool + ENT_Y_LO, x
    lda enemy_pool + ENT_VY, x
    bpl @vy_pos
    lda #$FF
    jmp @vy_done
@vy_pos:
    lda #$00
@vy_done:
    adc enemy_pool + ENT_Y_HI, x
    sta enemy_pool + ENT_Y_HI, x
    
@next:
    txa
    clc
    adc #ENTITY_SIZE
    tax
    cpx #(MAX_ENEMIES * ENTITY_SIZE)
    bne @loop
    
    rts
.endproc


; Export stub for entity_spawn (to be implemented)
.export entity_spawn
.proc entity_spawn
    ; TODO: Implement entity spawning
    rts
.endproc

