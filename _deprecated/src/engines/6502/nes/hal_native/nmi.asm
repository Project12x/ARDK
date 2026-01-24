; =============================================================================
; NES NMI Handler with High-Fidelity Graphics Support
; =============================================================================
; Features:
;   - OAM DMA transfer
;   - CHR bank animation (Batman-style animated backgrounds)
;   - Parallax scroll setup (for IRQ-driven multi-layer scroll)
; =============================================================================

.include "nes.inc"
.import reset
.importzp nmi_flag

; CHR animation variables (from zeropage.asm)
.importzp chr_anim_timer, chr_anim_frame, chr_anim_speed, chr_anim_bank_base

; Parallax system (optional, check if enabled)
.import parallax_setup_frame, parallax_irq
.importzp parallax_active

; Engine flags
.importzp engine_flags

; Engine flag bits
ENGINE_FLAG_CHR_ANIM    = $01   ; Enable CHR animation
ENGINE_FLAG_PARALLAX    = $02   ; Enable parallax scrolling

.segment "CODE"

; =============================================================================
; NMI - Vertical blank interrupt handler
; =============================================================================
.proc nmi
    ; Preserve registers
    pha
    txa
    pha
    tya
    pha

    ; ---------------------------------------------
    ; 1. OAM DMA (must happen during vblank)
    ; ---------------------------------------------
    lda #$02
    sta $4014

    ; ---------------------------------------------
    ; 2. CHR Animation Update (if enabled)
    ; ---------------------------------------------
    lda engine_flags
    and #ENGINE_FLAG_CHR_ANIM
    beq @skip_chr_anim

    ; Increment animation timer
    inc chr_anim_timer
    lda chr_anim_timer
    cmp chr_anim_speed          ; Compare to animation speed
    bcc @skip_chr_anim          ; Not time yet

    ; Reset timer and advance frame
    lda #0
    sta chr_anim_timer
    inc chr_anim_frame
    lda chr_anim_frame
    and #$03                    ; Wrap at 4 frames (0-3)
    sta chr_anim_frame

    ; Calculate CHR bank: base + (frame * 2) for 2KB banks
    asl a                       ; frame * 2
    clc
    adc chr_anim_bank_base

    ; Swap background CHR bank (MMC3 register 0)
    ldx #$00
    stx $8000                   ; Select bank register 0
    sta $8001                   ; Set new bank

@skip_chr_anim:

    ; ---------------------------------------------
    ; 3. Parallax Setup (if enabled)
    ; ---------------------------------------------
    lda engine_flags
    and #ENGINE_FLAG_PARALLAX
    beq @skip_parallax

    ; Check if parallax system is active
    lda parallax_active
    beq @skip_parallax

    ; Setup parallax for this frame (configures first layer + IRQ)
    jsr parallax_setup_frame

@skip_parallax:

    ; ---------------------------------------------
    ; 4. Signal frame complete
    ; ---------------------------------------------
    lda #1
    sta nmi_flag

    ; Restore registers
    pla
    tay
    pla
    tax
    pla
    rti
.endproc

; =============================================================================
; IRQ - Scanline interrupt handler (for parallax)
; =============================================================================
.proc irq
    ; Check if parallax is active
    lda parallax_active
    beq @simple_rti

    ; Delegate to parallax IRQ handler
    jmp parallax_irq

@simple_rti:
    rti
.endproc

.segment "VECTORS"
    .word nmi
    .word reset
    .word irq
