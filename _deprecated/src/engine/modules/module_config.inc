; =============================================================================
; NEON SURVIVORS - Module Configuration System
; Defines which engine modules are included in the build
; =============================================================================
;
; USAGE: Include ONE of the game-specific config files at the top of your
;        game's main file:
;
;   .include "../../engine/modules/config_survivor.inc"
;   .include "../../engine/modules/config_shmup.inc"
;   .include "../../engine/modules/config_zelda.inc"
;   .include "../../engine/modules/config_platformer.inc"
;
; Each config file defines which modules to enable.
; =============================================================================

.ifndef MODULE_CONFIG_INC
MODULE_CONFIG_INC = 1

; Module flags (set by game-specific config)
.ifdef MODULE_ACTION
    .ifndef MODULE_ACTION_ENABLED
        MODULE_ACTION_ENABLED = 1
    .endif
.else
    MODULE_ACTION_ENABLED = 0
.endif

.ifdef MODULE_ADVENTURE
    .ifndef MODULE_ADVENTURE_ENABLED
        MODULE_ADVENTURE_ENABLED = 1
    .endif
.else
    MODULE_ADVENTURE_ENABLED = 0
.endif

.ifdef MODULE_PLATFORM
    .ifndef MODULE_PLATFORM_ENABLED
        MODULE_PLATFORM_ENABLED = 1
    .endif
.else
    MODULE_PLATFORM_ENABLED = 0
.endif

; Feature flags (set by game-specific config)
.ifndef USE_PROJECTILES
    USE_PROJECTILES = 0
.endif

.ifndef USE_SPAWNER
    USE_SPAWNER = 0
.endif

.ifndef USE_POWERUPS
    USE_POWERUPS = 0
.endif

.ifndef USE_TILE_COLLISION
    USE_TILE_COLLISION = 0
.endif

.ifndef USE_SCROLLING
    USE_SCROLLING = 0
.endif

.ifndef USE_ROOM_SYSTEM
    USE_ROOM_SYSTEM = 0
.endif

.ifndef USE_INVENTORY
    USE_INVENTORY = 0
.endif

.ifndef USE_PHYSICS_GRAVITY
    USE_PHYSICS_GRAVITY = 0
.endif

.ifndef USE_CAMERA_FOLLOW
    USE_CAMERA_FOLLOW = 0
.endif

; =============================================================================
; Module Constants (configured per game type)
; =============================================================================

.if MODULE_ACTION_ENABLED
    ; Action module settings
    .ifndef MAX_PROJECTILES
        MAX_PROJECTILES = 16        ; Bullets/weapons
    .endif

    .ifndef MAX_POWERUPS
        MAX_POWERUPS = 8            ; XP gems, items
    .endif

    .ifndef SPAWN_TIMER_MAX
        SPAWN_TIMER_MAX = 60        ; Frames between enemy spawns
    .endif
.endif

.if MODULE_ADVENTURE_ENABLED
    ; Adventure module settings
    .ifndef MAX_INVENTORY_SLOTS
        MAX_INVENTORY_SLOTS = 8
    .endif

    .ifndef MAX_TRIGGERS
        MAX_TRIGGERS = 16           ; Switches, doors, etc.
    .endif
.endif

.if MODULE_PLATFORM_ENABLED
    ; Platform module settings
    .ifndef GRAVITY
        GRAVITY = 2                 ; Pixels per frame
    .endif

    .ifndef JUMP_VELOCITY
        JUMP_VELOCITY = 8
    .endif

    .ifndef TERMINAL_VELOCITY
        TERMINAL_VELOCITY = 16
    .endif
.endif

; =============================================================================
; Zero Page Allocation (conditional based on modules)
; =============================================================================

; Core engine uses $00-$2F (48 bytes) - see engine.inc
; Modules allocate from $30 onwards

.if MODULE_ACTION_ENABLED
    ; Action module: $30-$3F (16 bytes)
    .ifndef MODULE_ACTION_ZP_START
        MODULE_ACTION_ZP_START = $30
    .endif
    .ifndef MODULE_ACTION_ZP_END
        MODULE_ACTION_ZP_END = $3F
    .endif
.endif

.if MODULE_ADVENTURE_ENABLED
    ; Adventure module: $40-$4F (16 bytes)
    .ifndef MODULE_ADVENTURE_ZP_START
        MODULE_ADVENTURE_ZP_START = $40
    .endif
    .ifndef MODULE_ADVENTURE_ZP_END
        MODULE_ADVENTURE_ZP_END = $4F
    .endif
.endif

.if MODULE_PLATFORM_ENABLED
    ; Platform module: $50-$5F (16 bytes)
    .ifndef MODULE_PLATFORM_ZP_START
        MODULE_PLATFORM_ZP_START = $50
    .endif
    .ifndef MODULE_PLATFORM_ZP_END
        MODULE_PLATFORM_ZP_END = $5F
    .endif
.endif

; Game-specific variables start at $60
.ifndef GAME_ZP_START
    GAME_ZP_START = $60
.endif
.ifndef GAME_ZP_END
    GAME_ZP_END = $FF
.endif

; =============================================================================
; Debug Info
; =============================================================================

.if MODULE_ACTION_ENABLED
    .out "Module: ACTION enabled"
.endif

.if MODULE_ADVENTURE_ENABLED
    .out "Module: ADVENTURE enabled"
.endif

.if MODULE_PLATFORM_ENABLED
    .out "Module: PLATFORM enabled"
.endif

.endif ; MODULE_CONFIG_INC
