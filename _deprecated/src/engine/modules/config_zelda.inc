; =============================================================================
; ZELDA-LIKE Configuration
; Top-down adventure game with rooms
; =============================================================================

; Module selection
MODULE_ACTION = 1           ; Enable action module (for combat)
MODULE_ADVENTURE = 1        ; Enable adventure module
; MODULE_PLATFORM = 0       ; Not needed

; Feature flags
USE_PROJECTILES = 1         ; Sword beams, boomerang
USE_SPAWNER = 0             ; Enemies placed in rooms, not spawned
USE_POWERUPS = 1            ; Hearts, rupees
USE_TILE_COLLISION = 1      ; Full metatile collision
USE_SCROLLING = 0           ; Room transitions instead
USE_ROOM_SYSTEM = 1         ; Screen-by-screen rooms
USE_INVENTORY = 1           ; Items, equipment
USE_PHYSICS_GRAVITY = 0     ; Top-down
USE_CAMERA_FOLLOW = 0       ; Snap to rooms

; Action module configuration
MAX_PROJECTILES = 8         ; Link's weapons
MAX_POWERUPS = 6            ; Items on ground

; Adventure module configuration
MAX_INVENTORY_SLOTS = 8     ; Sword, shield, bombs, etc.
MAX_TRIGGERS = 16           ; Doors, switches, chests

; Game type identifier
GAME_TYPE_ID = 3            ; 3 = Zelda-like

; Include main module config
.include "module_config.inc"
