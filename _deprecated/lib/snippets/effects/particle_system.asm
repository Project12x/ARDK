; =============================================================================
; PARTICLE SYSTEM - Explosions, sparks, debris, blood, etc.
; =============================================================================
; Lightweight particle manager for visual effects
; Uses minimal RAM and CPU, shares sprite pool with game objects
; =============================================================================

.segment "ZEROPAGE"

; Particle pool indices
particle_count:     .res 1       ; Active particles
particle_next:      .res 1       ; Next free slot

.segment "BSS"

; Particle pool (16 particles max - adjust as needed)
MAX_PARTICLES = 16

particle_x_lo:      .res MAX_PARTICLES   ; X position (8.8 fixed point)
particle_x_hi:      .res MAX_PARTICLES
particle_y_lo:      .res MAX_PARTICLES   ; Y position
particle_y_hi:      .res MAX_PARTICLES
particle_vx:        .res MAX_PARTICLES   ; X velocity (signed)
particle_vy:        .res MAX_PARTICLES   ; Y velocity (signed)
particle_life:      .res MAX_PARTICLES   ; Frames remaining (0 = dead)
particle_tile:      .res MAX_PARTICLES   ; Sprite tile
particle_attr:      .res MAX_PARTICLES   ; Sprite attributes
particle_type:      .res MAX_PARTICLES   ; Type for special behavior

.segment "CODE"

; Particle types
PTYPE_NORMAL    = 0              ; Basic physics
PTYPE_GRAVITY   = 1              ; Falls down
PTYPE_FLOAT     = 2              ; Floats upward (smoke)
PTYPE_FADE      = 3              ; Changes palette over time
PTYPE_SPARK     = 4              ; Bounces off floor

; -----------------------------------------------------------------------------
; init_particles - Initialize particle system
; -----------------------------------------------------------------------------
.proc init_particles
    lda #0
    sta particle_count
    sta particle_next

    ; Clear all particles
    ldx #MAX_PARTICLES-1
@clear:
    sta particle_life, x
    dex
    bpl @clear

    rts
.endproc

; -----------------------------------------------------------------------------
; spawn_particle - Create a single particle
; Input: A = tile, X = x position, Y = y position
; Output: Carry clear = success, set = pool full
; -----------------------------------------------------------------------------
.proc spawn_particle
    sta temp_tile
    stx temp_x
    sty temp_y

    ; Find free slot
    ldx particle_next
@find_slot:
    lda particle_life, x
    beq @found
    inx
    cpx #MAX_PARTICLES
    bcc @check
    ldx #0                       ; Wrap
@check:
    cpx particle_next            ; Full loop?
    bne @find_slot

    ; Pool full
    sec
    rts

@found:
    ; Initialize particle
    lda temp_x
    sta particle_x_hi, x
    lda #$80                     ; 0.5 sub-pixel
    sta particle_x_lo, x

    lda temp_y
    sta particle_y_hi, x
    lda #$80
    sta particle_y_lo, x

    lda #0
    sta particle_vx, x
    sta particle_vy, x

    lda #60                      ; 1 second lifetime
    sta particle_life, x

    lda temp_tile
    sta particle_tile, x

    lda #0                       ; Default attributes
    sta particle_attr, x
    sta particle_type, x

    ; Update next pointer
    inx
    cpx #MAX_PARTICLES
    bcc @no_wrap
    ldx #0
@no_wrap:
    stx particle_next

    inc particle_count

    clc                          ; Success
    rts

temp_tile: .byte 0
temp_x:    .byte 0
temp_y:    .byte 0
.endproc

; -----------------------------------------------------------------------------
; spawn_particle_velocity - Spawn with initial velocity
; Input: A = tile, X = x pos, Y = y pos
;        Stack: vx, vy (push vy first, then vx)
; -----------------------------------------------------------------------------
.proc spawn_particle_velocity
    jsr spawn_particle
    bcs @failed

    ; Get velocity from stack (saved X is slot index)
    ; ... implementation depends on calling convention ...

@failed:
    rts
.endproc

; -----------------------------------------------------------------------------
; update_particles - Update all particles (call every frame)
; -----------------------------------------------------------------------------
.proc update_particles
    ldx #MAX_PARTICLES-1

@loop:
    lda particle_life, x
    beq @next                    ; Skip dead particles

    ; Decrement life
    dec particle_life, x
    beq @kill

    ; Apply type-specific behavior
    lda particle_type, x
    beq @physics                 ; PTYPE_NORMAL
    cmp #PTYPE_GRAVITY
    beq @gravity
    cmp #PTYPE_FLOAT
    beq @float
    jmp @physics

@gravity:
    ; Add gravity to Y velocity
    lda particle_vy, x
    clc
    adc #2                       ; Gravity acceleration
    sta particle_vy, x
    jmp @physics

@float:
    ; Subtract from Y velocity (float up)
    lda particle_vy, x
    sec
    sbc #1
    sta particle_vy, x
    jmp @physics

@physics:
    ; Apply X velocity
    lda particle_vx, x
    bmi @neg_vx

    ; Positive X velocity
    clc
    adc particle_x_lo, x
    sta particle_x_lo, x
    lda particle_x_hi, x
    adc #0
    sta particle_x_hi, x
    jmp @apply_vy

@neg_vx:
    ; Negative X velocity (sign extend)
    clc
    adc particle_x_lo, x
    sta particle_x_lo, x
    lda particle_x_hi, x
    adc #$FF                     ; Sign extension
    sta particle_x_hi, x

@apply_vy:
    ; Apply Y velocity
    lda particle_vy, x
    bmi @neg_vy

    clc
    adc particle_y_lo, x
    sta particle_y_lo, x
    lda particle_y_hi, x
    adc #0
    sta particle_y_hi, x
    jmp @check_bounds

@neg_vy:
    clc
    adc particle_y_lo, x
    sta particle_y_lo, x
    lda particle_y_hi, x
    adc #$FF
    sta particle_y_hi, x

@check_bounds:
    ; Kill if off screen
    lda particle_y_hi, x
    cmp #240                     ; Below screen
    bcs @kill
    jmp @next

@kill:
    lda #0
    sta particle_life, x
    dec particle_count

@next:
    dex
    bpl @loop
    rts
.endproc

; -----------------------------------------------------------------------------
; render_particles - Draw particles to OAM (call before OAM DMA)
; Input: Y = starting OAM index (sprite number * 4)
; Output: Y = next free OAM index
; -----------------------------------------------------------------------------
.proc render_particles
    ldx #0

@loop:
    lda particle_life, x
    beq @skip                    ; Skip dead particles

    ; Y position
    lda particle_y_hi, x
    sta $0200, y

    ; Tile
    iny
    lda particle_tile, x
    sta $0200, y

    ; Attributes
    iny
    lda particle_attr, x
    sta $0200, y

    ; X position
    iny
    lda particle_x_hi, x
    sta $0200, y

    iny                          ; Next OAM slot

@skip:
    inx
    cpx #MAX_PARTICLES
    bne @loop

    rts
.endproc

; =============================================================================
; EFFECT SPAWNERS
; =============================================================================

; -----------------------------------------------------------------------------
; spawn_explosion - Spawn explosion particles
; Input: X = center X, Y = center Y
; -----------------------------------------------------------------------------
.proc spawn_explosion
    stx center_x
    sty center_y

    ; Spawn 8 particles in a burst
    lda #8
    sta spawn_count

@loop:
    ; Random position offset
    jsr rand8_fast
    and #$0F                     ; -8 to +7
    sec
    sbc #8
    clc
    adc center_x
    tax

    jsr rand8_fast
    and #$0F
    sec
    sbc #8
    clc
    adc center_y
    tay

    lda #$F0                     ; Explosion tile (customize)
    jsr spawn_particle
    bcs @done                    ; Pool full

    ; Set velocity (outward from center)
    ldx particle_next
    dex
    bpl @no_wrap
    ldx #MAX_PARTICLES-1
@no_wrap:

    ; Random outward velocity
    jsr rand8_fast
    and #$07
    sec
    sbc #4                       ; -4 to +3
    sta particle_vx, x

    jsr rand8_fast
    and #$07
    sec
    sbc #4
    sta particle_vy, x

    lda #PTYPE_GRAVITY
    sta particle_type, x

    lda #30                      ; Shorter life for explosion
    sta particle_life, x

    dec spawn_count
    bne @loop

@done:
    rts

center_x:    .byte 0
center_y:    .byte 0
spawn_count: .byte 0
.endproc

; -----------------------------------------------------------------------------
; spawn_hit_spark - Quick spark effect for damage
; Input: X = x position, Y = y position
; -----------------------------------------------------------------------------
.proc spawn_hit_spark
    stx temp_x
    sty temp_y

    ; Spawn 3 sparks
    ldx #3
@loop:
    lda #$F1                     ; Spark tile
    ldx temp_x
    ldy temp_y
    jsr spawn_particle
    bcs @done

    ; Random velocity
    ldx particle_next
    dex
    bpl @ok
    ldx #MAX_PARTICLES-1
@ok:
    jsr rand8_fast
    and #$0F
    sec
    sbc #8
    sta particle_vx, x

    jsr rand8_fast
    and #$07
    sec
    sbc #8
    sta particle_vy, x

    lda #PTYPE_NORMAL
    sta particle_type, x

    lda #10                      ; Very short life
    sta particle_life, x

    dex
    bne @loop

@done:
    rts

temp_x: .byte 0
temp_y: .byte 0
.endproc

; -----------------------------------------------------------------------------
; spawn_smoke - Rising smoke puff
; Input: X = x position, Y = y position
; -----------------------------------------------------------------------------
.proc spawn_smoke
    lda #$F2                     ; Smoke tile
    jsr spawn_particle
    bcs @done

    ; Float upward
    ldx particle_next
    dex
    bpl @ok
    ldx #MAX_PARTICLES-1
@ok:
    lda #$FC                     ; Slight upward velocity (-4)
    sta particle_vy, x

    jsr rand8_fast
    and #$03
    sec
    sbc #2                       ; Slight random X drift
    sta particle_vx, x

    lda #PTYPE_FLOAT
    sta particle_type, x

    lda #45                      ; Longer life for smoke
    sta particle_life, x

@done:
    rts
.endproc

; =============================================================================
; USAGE EXAMPLE
; =============================================================================
;
; ; Initialization:
;   jsr init_particles
;
; ; When enemy dies:
;   ldx enemy_x
;   ldy enemy_y
;   jsr spawn_explosion
;
; ; When player takes hit:
;   ldx player_x
;   ldy player_y
;   jsr spawn_hit_spark
;
; ; Every frame:
;   jsr update_particles
;
; ; In sprite rendering (before OAM DMA):
;   ldy #32                      ; Start at sprite 8 (skip player/enemies)
;   jsr render_particles
;   ; Y now = next free sprite slot
;
; =============================================================================
