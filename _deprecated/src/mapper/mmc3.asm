; =============================================================================
; NEON SURVIVORS - MMC3 Bank Switching Routines
; Platform-specific mapper control (NES-only)
; =============================================================================
;
; PORTABILITY NOTE:
; This file is NES-specific. When porting to other platforms:
; - Mega Drive: Replace with VDP tile/palette DMA routines
; - PC Engine: Replace with HuCard bank switching
; The game logic in src/game/ should NOT call these directly.
; Instead, use the abstract routines in src/engine/graphics.asm
;
; =============================================================================

.include "data/nes.inc"

.segment "CODE"

; -----------------------------------------------------------------------------
; Switch CHR Bank (Background Tiles)
; Input: A = bank number (0-31), X = slot (0-3)
; -----------------------------------------------------------------------------
.proc switch_chr_bank
    ; Save bank for slot
    pha
    txa
    sta MMC3_BANK_SELECT    ; Select CHR slot register
    pla
    sta MMC3_BANK_DATA      ; Set bank number
    rts
.endproc

; -----------------------------------------------------------------------------
; Switch PRG Bank
; Input: A = bank number (0-15), X = slot (0=8000, 1=A000)
; -----------------------------------------------------------------------------
.proc switch_prg_bank
    pha
    txa
    clc
    adc #$06                ; PRG registers are 6 and 7
    sta MMC3_BANK_SELECT
    pla
    sta MMC3_BANK_DATA
    rts
.endproc

; -----------------------------------------------------------------------------
; Set Mirroring Mode
; Input: A = 0 for vertical, 1 for horizontal
; -----------------------------------------------------------------------------
.proc set_mirroring
    sta MMC3_MIRROR
    rts
.endproc

; -----------------------------------------------------------------------------
; Enable PRG RAM (Battery-backed save)
; -----------------------------------------------------------------------------
.proc enable_sram
    lda #$80
    sta MMC3_SRAM_EN
    rts
.endproc

; -----------------------------------------------------------------------------
; Disable PRG RAM (Write protect)
; -----------------------------------------------------------------------------
.proc disable_sram
    lda #$00
    sta MMC3_SRAM_EN
    rts
.endproc

; -----------------------------------------------------------------------------
; Set up Scanline IRQ (for raster effects)
; Input: A = scanline number to trigger IRQ
; -----------------------------------------------------------------------------
.proc set_scanline_irq
    sta MMC3_IRQ_LATCH      ; Set counter value
    sta MMC3_IRQ_RELOAD     ; Reload counter
    sta MMC3_IRQ_ENABLE     ; Enable IRQ
    rts
.endproc

; -----------------------------------------------------------------------------
; Disable Scanline IRQ
; -----------------------------------------------------------------------------
.proc disable_scanline_irq
    sta MMC3_IRQ_DISABLE
    rts
.endproc
