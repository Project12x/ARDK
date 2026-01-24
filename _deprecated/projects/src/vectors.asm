; =============================================================================
; HAL Demo - CPU Vectors
; NES interrupt vector table at $FFFA-$FFFF
; =============================================================================

.import NMI
.import Reset
.import IRQ

.segment "VECTORS"

    .addr NMI               ; $FFFA - NMI vector
    .addr Reset             ; $FFFC - Reset vector
    .addr IRQ               ; $FFFE - IRQ/BRK vector
