; =============================================================================
; Tower Survivors - iNES Header
; MMC3 Mapper (4) with 32KB PRG, 32KB CHR
; =============================================================================

.segment "HEADER"

    .byte "NES", $1A        ; iNES magic number
    .byte $02               ; 2 x 16KB PRG ROM banks = 32KB
    .byte $04               ; 4 x 8KB CHR ROM banks = 32KB
    .byte $40               ; Flags 6: MMC3 mapper (4), horizontal mirroring
    .byte $00               ; Flags 7: NES 1.0 format
    .byte $00               ; PRG RAM size (0 = 8KB)
    .byte $00               ; Flags 9: NTSC
    .byte $00               ; Flags 10: unused
    .byte $00, $00, $00, $00, $00  ; Padding
