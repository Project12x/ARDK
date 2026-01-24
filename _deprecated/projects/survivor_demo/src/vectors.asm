; =============================================================================
; Tower Survivors - CPU Vectors
; =============================================================================

.import Reset, NMI, IRQ

.segment "VECTORS"
    .word NMI               ; $FFFA - NMI vector
    .word Reset             ; $FFFC - Reset vector
    .word IRQ               ; $FFFE - IRQ/BRK vector
