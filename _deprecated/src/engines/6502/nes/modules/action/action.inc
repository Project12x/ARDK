; =============================================================================
; ACTION MODULE - Main Include File
; Exports all action module interfaces
; =============================================================================

.ifndef ACTION_INC
ACTION_INC = 1

; Only include if action module is enabled
.ifdef MODULE_ACTION_ENABLED

; -----------------------------------------------------------------------------
; Projectile System Exports
; -----------------------------------------------------------------------------
.global projectile_init
.global projectile_spawn
.global projectile_update_all
.global projectile_check_collision
.global projectile_deactivate
.global projectile_render_all

; Projectile spawn parameters (ZP variables to set before calling projectile_spawn)
; Defined in projectile.asm, import these in game code to use
.globalzp projectile_spawn_x
.globalzp projectile_spawn_y
.globalzp projectile_spawn_vx
.globalzp projectile_spawn_vy
.globalzp projectile_spawn_type
.globalzp projectile_spawn_flags

; Projectile types
PROJ_TYPE_LASER     = 0
PROJ_TYPE_MISSILE   = 1
PROJ_TYPE_BEAM      = 2

; Projectile flags
PROJ_FLAG_ACTIVE    = $01
PROJ_FLAG_FRIENDLY  = $02
PROJ_FLAG_ENEMY     = $04

; -----------------------------------------------------------------------------
; Spawner System Exports (if enabled)
; -----------------------------------------------------------------------------
.if .defined(USE_SPAWNER)
    .global spawner_init
    .global spawner_update
    .global spawner_increase_difficulty
    .global spawner_reset
    .global spawner_set_wave

    .globalzp spawner_timer
    .globalzp spawner_wave
    .globalzp spawner_difficulty
.endif

; -----------------------------------------------------------------------------
; Powerup System Exports (if enabled)
; -----------------------------------------------------------------------------
.if .defined(USE_POWERUPS)
    .global powerup_init
    .global powerup_spawn
    .global powerup_update_all
    .global powerup_render_all

    ; Powerup spawn parameters (defined in powerup.asm)
    .globalzp powerup_spawn_x
    .globalzp powerup_spawn_y
    .globalzp powerup_spawn_type

    ; Powerup types
    PWR_TYPE_XP_GEM     = 0
    PWR_TYPE_HEALTH     = 1
    PWR_TYPE_COIN       = 2
    PWR_TYPE_MAGNET     = 3

    .globalzp powerup_count
.endif

; -----------------------------------------------------------------------------
; Zero Page Allocation for Action Module
; This is defined in module_config.inc but documented here for reference:
;
; Projectile System ($40-$47):
;   $40-$45: projectile_spawn_x/y/vx/vy/type/flags
;   $46-$47: collision_x/y (for projectile_check_collision)
;
; Spawner System ($48-$4A):
;   $48: spawner_timer
;   $49: spawner_wave
;   $4A: spawner_difficulty
;
; Powerup System ($4B-$4F):
;   $4B-$4D: powerup_spawn_x/y/type
;   $4E: powerup_count
;   $4F: (reserved)
; -----------------------------------------------------------------------------

.endif ; MODULE_ACTION_ENABLED

.endif ; ACTION_INC
