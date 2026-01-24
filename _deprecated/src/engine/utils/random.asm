; =============================================================================
; NEON SURVIVORS - Random Number Generator
; Platform-independent PRNG using LFSR
; =============================================================================
;
; PORTABILITY: Pure math - works on any platform unchanged.
; Uses a 16-bit Linear Feedback Shift Register (LFSR)
;
; =============================================================================

.importzp temp1, temp2, temp3, temp4

.segment "ZEROPAGE"

; PRNG state (16-bit)
rng_state:      .res 2

.segment "CODE"

; -----------------------------------------------------------------------------
; Initialize RNG with Seed
; Input: A = seed low byte, X = seed high byte
; Note: Seed should not be zero!
; -----------------------------------------------------------------------------
.proc rng_seed
    sta rng_state
    stx rng_state+1
    
    ; Ensure non-zero seed
    ora rng_state+1
    bne @done
    lda #$01
    sta rng_state
    
@done:
    rts
.endproc

; -----------------------------------------------------------------------------
; Generate Random Byte
; Output: A = random byte (0-255)
; Clobbers: X
; -----------------------------------------------------------------------------
.export random_get
.export rng_next
.proc random_get  ; Alias for compatibility
    jmp rng_next
.endproc
.proc rng_next
    ; 16-bit Galois LFSR with taps at bits 16, 14, 13, 11
    ; Polynomial: x^16 + x^14 + x^13 + x^11 + 1
    
    lda rng_state
    lsr a
    ror rng_state+1
    bcc @no_eor
    
    ; XOR with polynomial taps
    lda rng_state
    eor #$B4                ; Taps for upper byte
    sta rng_state
    lda rng_state+1
    eor #$00
    sta rng_state+1
    
@no_eor:
    lda rng_state
    rts
.endproc

; -----------------------------------------------------------------------------
; Generate Random Byte in Range
; Input: A = max value (exclusive, 0-255)
; Output: A = random value (0 to max-1)
; Note: Uses rejection sampling for uniform distribution
; -----------------------------------------------------------------------------
.proc rng_range
    sta temp1               ; Save max
    
@retry:
    jsr rng_next            ; Get random byte
    cmp temp1               ; Compare with max
    bcs @retry              ; If >= max, try again
    
    rts
.endproc

; -----------------------------------------------------------------------------
; Generate Random Direction Vector
; Output: temp1 = dx (-1, 0, or 1), temp2 = dy (-1, 0, or 1)
; Useful for random enemy movement
; -----------------------------------------------------------------------------
.proc rng_direction
    jsr rng_next
    and #$03                ; 0-3
    tax
    lda dir_table_x, x
    sta temp1
    lda dir_table_y, x
    sta temp2
    rts
    
dir_table_x:
    .byte $FF, $01, $00, $00  ; -1, +1, 0, 0
dir_table_y:
    .byte $00, $00, $FF, $01  ; 0, 0, -1, +1
.endproc

; -----------------------------------------------------------------------------
; Generate Random Spawn Position (Edge of Screen)
; Output: temp1 = X position, temp2 = Y position
; Spawns enemies just outside visible area
; -----------------------------------------------------------------------------
.proc rng_spawn_position
    jsr rng_next
    and #$03                ; Pick edge (0-3)
    
    cmp #0
    beq @top
    cmp #1
    beq @bottom
    cmp #2
    beq @left
    ; else right
    
@right:
    lda #248                ; Right edge
    sta temp1
    jsr rng_next
    sta temp2               ; Random Y
    rts
    
@left:
    lda #8                  ; Left edge
    sta temp1
    jsr rng_next
    sta temp2
    rts
    
@top:
    jsr rng_next
    sta temp1               ; Random X
    lda #8                  ; Top edge
    sta temp2
    rts
    
@bottom:
    jsr rng_next
    sta temp1               ; Random X
    lda #232                ; Bottom edge
    sta temp2
    rts
.endproc
