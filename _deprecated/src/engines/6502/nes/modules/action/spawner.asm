; =============================================================================
; ACTION MODULE - Enemy Spawner System
; Timer-based enemy wave spawning with difficulty scaling
; =============================================================================

.include "../../engine.inc"

; Only compile if action module is enabled and spawner is used
.if (.defined(MODULE_ACTION_ENABLED) .and .defined(USE_SPAWNER))

; -----------------------------------------------------------------------------
; Zero Page Variables
; -----------------------------------------------------------------------------
.segment "ZEROPAGE"
spawner_timer:      .res 1      ; Frames until next spawn
spawner_wave:       .res 1      ; Current wave number
spawner_difficulty: .res 1      ; Difficulty multiplier (0-15)

; -----------------------------------------------------------------------------
; BSS - Spawn Patterns
; -----------------------------------------------------------------------------
.segment "BSS"
spawn_interval:     .res 1      ; Frames between spawns
spawn_count:        .res 1      ; Enemies to spawn this wave
spawn_type:         .res 1      ; Enemy type to spawn

; -----------------------------------------------------------------------------
; Constants
; -----------------------------------------------------------------------------
SPAWN_INTERVAL_BASE = 120       ; 2 seconds at 60fps
SPAWN_INTERVAL_MIN  = 30        ; Minimum spawn interval (0.5s)
SPAWN_COUNT_BASE    = 3         ; Enemies per wave at start
SPAWN_COUNT_MAX     = 10        ; Maximum enemies per wave

; Spawn positions (screen edges)
SPAWN_TOP       = 16
SPAWN_BOTTOM    = 208
SPAWN_LEFT      = 16
SPAWN_RIGHT     = 224

; -----------------------------------------------------------------------------
; CODE
; -----------------------------------------------------------------------------
.segment "CODE"

; -----------------------------------------------------------------------------
; spawner_init
; Initializes spawner system
; Input: None
; Output: None
; Destroys: A
; -----------------------------------------------------------------------------
.export spawner_init
.proc spawner_init
    lda #SPAWN_INTERVAL_BASE
    sta spawn_interval
    sta spawner_timer

    lda #SPAWN_COUNT_BASE
    sta spawn_count

    lda #0
    sta spawner_wave
    sta spawner_difficulty
    sta spawn_type

    rts
.endproc

; -----------------------------------------------------------------------------
; spawner_update
; Updates spawner timer and spawns enemies when ready
; Input: None
; Output: None
; Destroys: A, X, Y
; -----------------------------------------------------------------------------
.export spawner_update
.proc spawner_update
    ; Decrement timer
    dec spawner_timer
    bne @done

    ; Reset timer
    lda spawn_interval
    sta spawner_timer

    ; Spawn wave of enemies
    lda spawn_count
    sta temp_count

@spawn_loop:
    jsr spawn_enemy
    dec temp_count
    bne @spawn_loop

    ; Advance to next wave
    inc spawner_wave

    ; Increase difficulty every 5 waves
    lda spawner_wave
    and #$04            ; Check bit 2 (every 4 waves)
    beq @done
    jsr spawner_increase_difficulty

@done:
    rts

temp_count: .res 1
.endproc

; -----------------------------------------------------------------------------
; spawn_enemy
; Spawns a single enemy at random screen edge
; Input: None
; Output: None
; Destroys: A, X, Y
; -----------------------------------------------------------------------------
.proc spawn_enemy
    ; Get random edge (0-3: top, right, bottom, left)
    jsr random_get
    and #$03
    tax

    ; Jump table for edge selection
    lda edge_spawn_table_lo, x
    sta temp_ptr
    lda edge_spawn_table_hi, x
    sta temp_ptr + 1
    jmp (temp_ptr)

; Edge spawn routines
spawn_top:
    jsr random_get
    and #$7F
    clc
    adc #SPAWN_LEFT
    sta entity_spawn_x
    lda #SPAWN_TOP
    sta entity_spawn_y
    jmp do_spawn

spawn_right:
    lda #SPAWN_RIGHT
    sta entity_spawn_x
    jsr random_get
    and #$7F
    clc
    adc #SPAWN_TOP
    sta entity_spawn_y
    jmp do_spawn

spawn_bottom:
    jsr random_get
    and #$7F
    clc
    adc #SPAWN_LEFT
    sta entity_spawn_x
    lda #SPAWN_BOTTOM
    sta entity_spawn_y
    jmp do_spawn

spawn_left:
    lda #SPAWN_LEFT
    sta entity_spawn_x
    jsr random_get
    and #$7F
    clc
    adc #SPAWN_TOP
    sta entity_spawn_y
    ; Fall through to do_spawn

do_spawn:
    ; Set enemy type based on wave
    lda spawner_wave
    lsr a
    lsr a
    and #$03            ; Cycle through 4 enemy types
    sta entity_spawn_type

    ; Set health based on difficulty
    lda spawner_difficulty
    lsr a
    clc
    adc #1
    sta entity_spawn_health

    ; Spawn enemy entity
    jsr entity_spawn
    rts

temp_ptr: .res 2

; Edge spawn jump table
edge_spawn_table_lo:
    .lobytes spawn_top, spawn_right, spawn_bottom, spawn_left
edge_spawn_table_hi:
    .hibytes spawn_top, spawn_right, spawn_bottom, spawn_left
.endproc

; -----------------------------------------------------------------------------
; spawner_increase_difficulty
; Increases spawn rate and enemy count
; Input: None
; Output: None
; Destroys: A
; -----------------------------------------------------------------------------
.export spawner_increase_difficulty
.proc spawner_increase_difficulty
    ; Increase difficulty counter
    lda spawner_difficulty
    cmp #15
    beq @done           ; Max difficulty
    inc spawner_difficulty

    ; Decrease spawn interval (faster spawns)
    lda spawn_interval
    cmp #SPAWN_INTERVAL_MIN
    beq @skip_interval
    sec
    sbc #10
    cmp #SPAWN_INTERVAL_MIN
    bcs @store_interval
    lda #SPAWN_INTERVAL_MIN
@store_interval:
    sta spawn_interval
@skip_interval:

    ; Increase spawn count (more enemies)
    lda spawn_count
    cmp #SPAWN_COUNT_MAX
    beq @done
    inc spawn_count

@done:
    rts
.endproc

; -----------------------------------------------------------------------------
; spawner_reset
; Resets spawner to initial difficulty
; Input: None
; Output: None
; Destroys: A
; -----------------------------------------------------------------------------
.export spawner_reset
.proc spawner_reset
    jsr spawner_init
    rts
.endproc

; -----------------------------------------------------------------------------
; spawner_set_wave
; Manually sets wave number (for testing or level progression)
; Input: A = wave number
; Output: None
; Destroys: A
; -----------------------------------------------------------------------------
.export spawner_set_wave
.proc spawner_set_wave
    sta spawner_wave

    ; Calculate difficulty from wave
    lsr a
    lsr a               ; Divide by 4
    cmp #16
    bcc @store
    lda #15             ; Cap at 15
@store:
    sta spawner_difficulty
    rts
.endproc

; -----------------------------------------------------------------------------
; External dependencies
; -----------------------------------------------------------------------------
.import random_get
.import entity_spawn

; ZP variables for entity spawning (defined in engine.inc)
; Already imported by engine.inc, no need to re-import

.endif ; MODULE_ACTION_ENABLED && USE_SPAWNER
