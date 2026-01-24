; =============================================================================
; PROJECT: [Project Name]
; game_config.inc - Project Configuration
; =============================================================================
; Edit this file to configure your project's features and limits.
; =============================================================================

; -----------------------------------------------------------------------------
; Feature Flags
; -----------------------------------------------------------------------------
; Set to 1 to enable, 0 to disable (saves ROM/RAM space)

USE_PARALLAX    = 0         ; Multi-layer background scrolling
USE_CHR_ANIM    = 0         ; Animated background tiles
USE_SPAWNER     = 0         ; Enemy wave spawning system
USE_POWERUPS    = 0         ; Item drops and pickups
USE_AUDIO       = 0         ; Sound effects and music

; -----------------------------------------------------------------------------
; Entity Limits
; -----------------------------------------------------------------------------
; Adjust based on your game's needs. Lower = faster, less RAM.

MAX_ENEMIES     = 12        ; Maximum simultaneous enemies
MAX_PROJECTILES = 16        ; Maximum bullets/lasers on screen
MAX_PICKUPS     = 8         ; Maximum items on ground
MAX_EFFECTS     = 8         ; Maximum particle effects

; -----------------------------------------------------------------------------
; Player Configuration
; -----------------------------------------------------------------------------

PLAYER_MAX_HP   = 10        ; Maximum health
PLAYER_SPEED    = 256       ; Movement speed (8.8 fixed point, 256 = 1 pixel/frame)
PLAYER_IFRAMES  = 60        ; Invincibility frames after hit

; -----------------------------------------------------------------------------
; Sprite Configuration
; -----------------------------------------------------------------------------

PLAYER_TILE     = $00       ; Starting tile index for player
PLAYER_WIDTH    = 16        ; Player sprite width in pixels
PLAYER_HEIGHT   = 16        ; Player sprite height in pixels

ENEMY_TILE      = $10       ; Starting tile index for enemies
PROJ_TILE       = $20       ; Starting tile index for projectiles
PICKUP_TILE     = $30       ; Starting tile index for pickups

; -----------------------------------------------------------------------------
; Screen Configuration
; -----------------------------------------------------------------------------

SCREEN_LEFT     = 8         ; Left boundary (pixels)
SCREEN_RIGHT    = 248       ; Right boundary (pixels)
SCREEN_TOP      = 16        ; Top boundary (pixels)
SCREEN_BOTTOM   = 224       ; Bottom boundary (pixels)

; -----------------------------------------------------------------------------
; Palette Indices
; -----------------------------------------------------------------------------

PAL_PLAYER      = 0         ; Player uses sprite palette 0
PAL_ENEMY       = 1         ; Enemies use sprite palette 1
PAL_PROJECTILE  = 2         ; Projectiles use sprite palette 2
PAL_PICKUP      = 3         ; Pickups use sprite palette 3
