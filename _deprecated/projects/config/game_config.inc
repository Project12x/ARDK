; =============================================================================
; HAL Demo - Game Configuration
; =============================================================================
; Demonstrates ARDK HAL capabilities with minimal configuration.
; =============================================================================

; -----------------------------------------------------------------------------
; Feature Flags
; -----------------------------------------------------------------------------

USE_PARALLAX    = 0         ; Disabled for simplicity
USE_CHR_ANIM    = 0         ; Disabled for simplicity
USE_SPAWNER     = 0         ; Manual enemy placement
USE_POWERUPS    = 0         ; No pickups in demo
USE_AUDIO       = 0         ; No audio in demo

; -----------------------------------------------------------------------------
; Entity Limits
; -----------------------------------------------------------------------------

MAX_ENEMIES     = 4         ; One demo enemy
MAX_PROJECTILES = 8         ; Player bullets
MAX_PICKUPS     = 0         ; None
MAX_EFFECTS     = 4         ; Hit sparks

; -----------------------------------------------------------------------------
; Player Configuration
; -----------------------------------------------------------------------------

PLAYER_MAX_HP   = 3         ; 3 hearts
PLAYER_SPEED    = 192       ; 0.75 pixels/frame (smooth movement)
PLAYER_IFRAMES  = 90        ; 1.5 seconds invincibility

; -----------------------------------------------------------------------------
; Sprite Tile Indices (in CHR ROM)
; -----------------------------------------------------------------------------
; Player: 16x16 = 4 tiles in 2x2 arrangement
; Tiles are arranged in CHR as:
;   $00 $01   (top-left, top-right)
;   $10 $11   (bottom-left, bottom-right)

TILE_PLAYER_TL  = $00       ; Player top-left
TILE_PLAYER_TR  = $01       ; Player top-right
TILE_PLAYER_BL  = $10       ; Player bottom-left
TILE_PLAYER_BR  = $11       ; Player bottom-right

TILE_ENEMY_TL   = $02       ; Enemy top-left
TILE_ENEMY_TR   = $03       ; Enemy top-right
TILE_ENEMY_BL   = $12       ; Enemy bottom-left
TILE_ENEMY_BR   = $13       ; Enemy bottom-right

TILE_BULLET     = $04       ; Single 8x8 bullet

; -----------------------------------------------------------------------------
; Screen Boundaries
; -----------------------------------------------------------------------------

SCREEN_LEFT     = 8
SCREEN_RIGHT    = 240
SCREEN_TOP      = 16
SCREEN_BOTTOM   = 224

; -----------------------------------------------------------------------------
; Palette Indices
; -----------------------------------------------------------------------------

PAL_PLAYER      = 0         ; Blue player
PAL_ENEMY       = 1         ; Red enemy
PAL_PROJECTILE  = 2         ; Yellow bullets
PAL_EFFECT      = 3         ; White sparks
