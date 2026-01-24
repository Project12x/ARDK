; =============================================================================
; SHMUP Configuration
; Shoot-em-up / Bullet Hell style game
; =============================================================================

; Module selection
MODULE_ACTION = 1           ; Enable action module
; MODULE_ADVENTURE = 0      ; Not needed
; MODULE_PLATFORM = 0       ; Not needed

; Feature flags
USE_PROJECTILES = 1         ; Player shots + enemy bullets
USE_SPAWNER = 1             ; Enemy wave patterns
USE_POWERUPS = 1            ; Power-ups, score items
USE_TILE_COLLISION = 0      ; Sprite-based only
USE_SCROLLING = 1           ; Vertical scrolling background
USE_ROOM_SYSTEM = 0
USE_INVENTORY = 0
USE_PHYSICS_GRAVITY = 0     ; Space physics
USE_CAMERA_FOLLOW = 0       ; Auto-scroll

; Action module configuration
MAX_PROJECTILES = 24        ; More bullets on screen
MAX_POWERUPS = 4            ; Fewer items than survivor-like
SPAWN_TIMER_MAX = 30        ; Faster enemy spawning

; Game type identifier
GAME_TYPE_ID = 2            ; 2 = Shmup

; Include main module config
.include "module_config.inc"
