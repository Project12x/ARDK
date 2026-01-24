; 4x 8KB CHR banks for MMC3
.segment "CHR_BANK0"
    .incbin "src/game/assets/sprites.chr"

.segment "CHR_BANK1"
    .incbin "src/game/assets/sprites.chr"  ; Duplicate for now

.segment "CHR_BANK2"
    .incbin "src/game/assets/sprites.chr"  ; Duplicate for now

.segment "CHR_BANK3"
    .incbin "src/game/assets/sprites.chr"  ; Duplicate for now
