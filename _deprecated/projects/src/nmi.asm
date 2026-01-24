; =============================================================================
; HAL Demo - NMI Handler
; Minimal NMI for demo purposes
; =============================================================================

.include "nes.inc"

.importzp nmi_flag

.segment "CODE"

; -----------------------------------------------------------------------------
; NMI - Called every VBlank (~60 times per second)
; -----------------------------------------------------------------------------
.export NMI
.proc NMI
    pha                     ; Save registers
    txa
    pha
    tya
    pha

    ; Trigger OAM DMA (copy $0200-$02FF to PPU OAM)
    lda #0
    sta $2003               ; OAM_ADDR = 0
    lda #$02
    sta $4014               ; OAM_DMA = $02 (triggers DMA from $0200)

    ; Reset scroll (important after any PPU reads/writes)
    lda #0
    sta $2005               ; PPU_SCROLL X
    sta $2005               ; PPU_SCROLL Y

    ; Signal to main loop that VBlank occurred
    lda #1
    sta nmi_flag

    pla                     ; Restore registers
    tay
    pla
    tax
    pla

    rti                     ; Return from interrupt
.endproc

; -----------------------------------------------------------------------------
; IRQ - Not used in this demo
; -----------------------------------------------------------------------------
.export IRQ
.proc IRQ
    rti
.endproc
