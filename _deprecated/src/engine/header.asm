; =============================================================================
; NEON SURVIVORS - iNES Header
; NES ROM format header for emulators and flash carts
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

; =============================================================================
; Header Flags Reference:
; -----------------------------------------------------------------------------
; Byte 6 (Flags 6):
;   Bit 0: Mirroring (0=horizontal, 1=vertical)
;   Bit 1: Battery-backed PRG RAM
;   Bit 2: Trainer present
;   Bit 3: Four-screen VRAM
;   Bits 4-7: Lower nibble of mapper number
;
; MMC3 = Mapper 4 = $04
; $43 = 0100 0011 = Mapper 4, vertical mirroring, battery
; =============================================================================
