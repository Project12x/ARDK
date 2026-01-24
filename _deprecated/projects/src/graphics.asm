; =============================================================================
; HAL Demo - CHR Graphics Data
; Includes sprite and background tile data
; =============================================================================

; CHR Bank 0 - Player Sprites (8KB)
; Generated from player_rad_90s.png
.segment "CHR_BANK0"
    ; .incbin "../assets/processed/sprites.chr"
    .res $2000, $00 ; Placeholder if sprites missing

; CHR Bank 1 - Background Tiles (8KB)
; Generated from background_cyberpunk.png
.segment "CHR_BANK1"
    .incbin "../assets/bg_cyberpunk.chr"
    ; Pad to 8KB if needed (actually MMC3 uses 1KB/2KB chunks, segment size matters)
    ; For valid banking, we usually fill the segment.
    ; But here we just include the file.
    .res $1000, $00 ; Padding guess

; CHR Bank 2 - Projectile & Item Sprites (8KB)
; Generated from items_projectiles.png
.segment "CHR_BANK2"
    ; .incbin "../assets/processed/projectiles.chr"
    .res $2000, $00

; CHR Bank 3 - Empty (8KB)
.segment "CHR_BANK3"
    .res $2000, $00

; =============================================================================
; Nametables (RODATA)
; =============================================================================
.segment "RODATA"
    .export background_nametable
background_nametable:
    .incbin "../assets/bg_cyberpunk.nam"

