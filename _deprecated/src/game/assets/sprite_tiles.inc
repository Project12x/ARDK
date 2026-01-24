; =============================================================================
; NEON SURVIVORS - Sprite Tile Definitions
; Generated from AI-processed player_rad_90s.png (run animation frames 2-5)
; =============================================================================

; -----------------------------------------------------------------------------
; CHR Layout (from AI-processed player_rad_90s.png)
; Total: 64 tiles = 4 animation frames x 16 tiles each
;
; Each 32x32 sprite = 16 tiles in 4x4 arrangement:
;   Row 0: $00, $01, $02, $03
;   Row 1: $04, $05, $06, $07
;   Row 2: $08, $09, $0A, $0B
;   Row 3: $0C, $0D, $0E, $0F
;
; Frame layout in CHR:
;   $00-$0F: Run Frame 1 (used for idle/default)
;   $10-$1F: Run Frame 2
;   $20-$2F: Run Frame 3
;   $30-$3F: Run Frame 4
; -----------------------------------------------------------------------------

; Player Animation - using run frames for all states
; (Idle uses run frame 1, Run cycles through all 4)
TILE_PLAYER_IDLE1       = $00   ; Run frame 1 used as idle
TILE_PLAYER_IDLE2       = $10   ; Run frame 2 used as idle alt

; Player Run Animation (32x32 sprites)
TILE_PLAYER_RUN1        = $00   ; Run frame 1 base tile
TILE_PLAYER_RUN2        = $10   ; Run frame 2 base tile
TILE_PLAYER_RUN3        = $20   ; Run frame 3 base tile
TILE_PLAYER_RUN4        = $30   ; Run frame 4 base tile

; Player Attack Animation (using run frame for now)
TILE_PLAYER_ATTACK1     = $00   ; Placeholder - uses run frame 1

; Number of tiles per 32x32 sprite
TILES_PER_32x32         = 16

; Animation frame counts
PLAYER_IDLE_FRAMES      = 2
PLAYER_RUN_FRAMES       = 4
PLAYER_ATTACK_FRAMES    = 1

; For 2x2 metatile (16x16) compatibility:
; Use only top-left quadrant of each 32x32 sprite
TILE_PLAYER_16_IDLE_TL  = $00   ; Top-left
TILE_PLAYER_16_IDLE_TR  = $01   ; Top-right
TILE_PLAYER_16_IDLE_BL  = $04   ; Bottom-left (row 1)
TILE_PLAYER_16_IDLE_BR  = $05   ; Bottom-right

; Legacy compatibility names (2x2 metatile)
TILE_PLAYER_IDLE_TL     = $00
TILE_PLAYER_IDLE_TR     = $01
TILE_PLAYER_IDLE_BL     = $04
TILE_PLAYER_IDLE_BR     = $05

; Placeholder tile definitions for items (not yet in CHR)
TILE_PICKUP_XP_GEM      = $00   ; Placeholder - will be loaded into CHR bank
TILE_PICKUP_HEALTH      = $00   ; Placeholder

; Palette info (from AI analysis)
; Palette 0: $0F (black/transparent), $24 (magenta), $1C (cyan), $00 (black)

; End of sprite tile definitions
