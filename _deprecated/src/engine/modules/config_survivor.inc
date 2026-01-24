; =============================================================================
; SURVIVOR-LIKE Configuration
; Vampire Survivors / NEON SURVIVORS style game
; =============================================================================

; Module selection
MODULE_ACTION = 1           ; Enable action module
; MODULE_ADVENTURE = 0      ; Not needed
; MODULE_PLATFORM = 0       ; Not needed

; Feature flags
USE_PROJECTILES = 1         ; Auto-fire weapons
USE_SPAWNER = 1             ; Enemy wave spawning
USE_POWERUPS = 1            ; XP gems, upgrades
USE_TILE_COLLISION = 0      ; Arena boundaries only (simple)
USE_SCROLLING = 0           ; Static arena
USE_ROOM_SYSTEM = 0
USE_INVENTORY = 0           ; Weapons tracked differently
USE_PHYSICS_GRAVITY = 0     ; Top-down movement
USE_CAMERA_FOLLOW = 0       ; Player stays centered

; Action module configuration
MAX_PROJECTILES = 16        ; Player weapons + enemy bullets
MAX_POWERUPS = 8            ; XP gems on screen
SPAWN_TIMER_MAX = 60        ; Spawn enemy every 60 frames initially

; Game type identifier
GAME_TYPE_ID = 1            ; 1 = Survivor-like

; Include main module config
.include "module_config.inc"
