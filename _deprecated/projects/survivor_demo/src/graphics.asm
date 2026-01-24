; =============================================================================
; Tower Survivors - CHR Graphics Data
; =============================================================================

; CHR Bank 0 - Sprites Frame A (8KB)
.segment "CHR_BANK0"
    ; For now, use placeholder data
    ; In production, would .incbin "../assets/sprites_frame0.chr"
    .res $2000, $00

; CHR Bank 1 - Background tiles (8KB)
.segment "CHR_BANK1"
    .res $2000, $00

; CHR Bank 2 - Sprites Frame B / Additional (8KB)
.segment "CHR_BANK2"
    .res $2000, $00

; CHR Bank 3 - HUD tiles (8KB)
.segment "CHR_BANK3"
    .res $2000, $00
