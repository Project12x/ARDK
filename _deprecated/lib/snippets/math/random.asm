; =============================================================================
; RANDOM NUMBER GENERATORS - Fast LFSR and Galois implementations
; =============================================================================
; Multiple RNG options with different speed/quality tradeoffs
; All use Linear Feedback Shift Registers (LFSR)
; =============================================================================

.segment "ZEROPAGE"
rng_seed:           .res 2       ; 16-bit seed for better period

.segment "CODE"

; -----------------------------------------------------------------------------
; init_rng - Initialize random seed (call once at startup)
; Uses frame counter or other entropy source
; -----------------------------------------------------------------------------
.proc init_rng
    ; Use current frame count or any changing value
    lda frame_counter
    ora #$01                     ; Ensure not zero
    sta rng_seed
    lda frame_counter
    eor #$A5                     ; XOR for variety
    ora #$01
    sta rng_seed+1
    rts
.endproc

; -----------------------------------------------------------------------------
; rand8_fast - Fast 8-bit random (simple LFSR)
; Output: A = random 0-255
; Cycles: ~20
; Period: 255 (not 256!)
; -----------------------------------------------------------------------------
.proc rand8_fast
    lda rng_seed
    beq @do_eor                  ; If zero, force EOR
    asl
    beq @no_eor                  ; If result zero but no carry, skip
    bcc @no_eor
@do_eor:
    eor #$1D                     ; Taps: bits 0,2,3,4 (maximal LFSR)
@no_eor:
    sta rng_seed
    rts
.endproc

; -----------------------------------------------------------------------------
; rand8_galois - Galois LFSR (slightly better distribution)
; Output: A = random 0-255
; Cycles: ~25
; -----------------------------------------------------------------------------
.proc rand8_galois
    lda rng_seed
    lsr                          ; Shift right
    bcc @no_eor
    eor #$B4                     ; Taps for maximal period
@no_eor:
    sta rng_seed
    rts
.endproc

; -----------------------------------------------------------------------------
; rand16 - 16-bit random for better period (65535)
; Output: A = random 0-255, rng_seed updated
; Cycles: ~40
; Quality: Much longer period, better randomness
; -----------------------------------------------------------------------------
.proc rand16
    ; Galois LFSR with 16-bit state
    lda rng_seed+1
    lsr
    lda rng_seed
    ror
    bcc @no_eor
    ; Taps for 16-bit maximal LFSR
    lda rng_seed+1
    eor #$B4
    sta rng_seed+1
    lda rng_seed
    eor #$00
@no_eor:
    sta rng_seed
    ror rng_seed+1

    ; Return low byte as random
    lda rng_seed
    rts
.endproc

; -----------------------------------------------------------------------------
; rand_range - Random number in range 0 to A-1
; Input: A = max (exclusive)
; Output: A = random 0 to max-1
; Note: Slightly biased for non-power-of-2 ranges
; -----------------------------------------------------------------------------
.proc rand_range
    sta temp_max
    jsr rand8_fast
    ; Simple modulo using repeated subtraction
@sub_loop:
    cmp temp_max
    bcc @done
    sbc temp_max
    jmp @sub_loop
@done:
    rts

temp_max: .byte 0
.endproc

; -----------------------------------------------------------------------------
; rand_range_mask - Fast range for power-of-2 (unbiased)
; Input: A = mask (e.g., $0F for 0-15, $1F for 0-31)
; Output: A = random within mask
; -----------------------------------------------------------------------------
.proc rand_range_mask
    sta temp_mask
    jsr rand8_fast
    and temp_mask
    rts

temp_mask: .byte 0
.endproc

; -----------------------------------------------------------------------------
; rand_coin - 50/50 random (bit 0)
; Output: Carry = random 0 or 1
; -----------------------------------------------------------------------------
.proc rand_coin
    jsr rand8_fast
    lsr                          ; Bit 0 to carry
    rts
.endproc

; -----------------------------------------------------------------------------
; rand_percent - Random check against percentage
; Input: A = percentage threshold (0-255, where 255=100%)
; Output: Carry set if random < threshold (success)
; Usage: Check if event happens with X% probability
; -----------------------------------------------------------------------------
.proc rand_percent
    sta temp_threshold
    jsr rand8_fast
    cmp temp_threshold           ; Carry clear if random < threshold
    rts

temp_threshold: .byte 0
.endproc

; =============================================================================
; WEIGHTED RANDOM - For loot drops, enemy spawns, etc.
; =============================================================================

; -----------------------------------------------------------------------------
; rand_weighted - Pick from weighted table
; Input: X = pointer to weight table (ends with $00)
; Output: A = index of selected item
;
; Weight table format: .byte weight1, weight2, weight3, ..., 0
; Higher weight = more likely
; -----------------------------------------------------------------------------
.proc rand_weighted
    ; First sum all weights
    stx weight_ptr
    ldy #0
    lda #0
@sum_loop:
    clc
    adc ($00), y                 ; Would be (weight_ptr), y
    beq @sum_done
    iny
    bne @sum_loop
@sum_done:
    sta total_weight

    ; Get random within total
    jsr rand8_fast
@clamp:
    cmp total_weight
    bcc @pick
    sbc total_weight
    jmp @clamp

@pick:
    ; Walk through weights until random exhausted
    sta temp_rand
    ldy #0
    lda #0
    sta running_sum

@pick_loop:
    lda ($00), y                 ; Weight at index Y
    beq @return_last             ; End of table
    clc
    adc running_sum
    sta running_sum
    cmp temp_rand
    bcs @found                   ; running_sum > random, found it
    iny
    bne @pick_loop

@found:
    tya                          ; Return index
    rts

@return_last:
    dey
    tya
    rts

weight_ptr:   .byte 0
total_weight: .byte 0
running_sum:  .byte 0
temp_rand:    .byte 0
.endproc

; =============================================================================
; SHUFFLE - Fisher-Yates shuffle for arrays
; =============================================================================

; -----------------------------------------------------------------------------
; shuffle_array - Randomly shuffle array in place
; Input: X = pointer to array, A = length
; -----------------------------------------------------------------------------
.proc shuffle_array
    sta array_len
    stx array_ptr

    ldx array_len
    dex                          ; Start at last index

@loop:
    cpx #0
    beq @done

    ; Get random 0 to X
    inx
    txa
    jsr rand_range
    sta rand_idx

    dex                          ; Back to current index

    ; Swap array[x] with array[rand_idx]
    ldy rand_idx
    lda ($00), y                 ; array[rand_idx]  (would be array_ptr)
    sta temp_val
    txa
    tay
    lda ($00), y                 ; array[x]
    ldy rand_idx
    sta ($00), y                 ; array[rand_idx] = array[x]
    lda temp_val
    txa
    tay
    sta ($00), y                 ; array[x] = temp

    dex
    bne @loop

@done:
    rts

array_ptr:  .byte 0
array_len:  .byte 0
rand_idx:   .byte 0
temp_val:   .byte 0
.endproc

; =============================================================================
; USAGE EXAMPLES:
; =============================================================================
;
; ; Initialize at game start:
;   jsr init_rng
;
; ; Simple random 0-255:
;   jsr rand8_fast
;   sta enemy_spawn_x
;
; ; Random 0-15 (fast, power of 2):
;   lda #$0F
;   jsr rand_range_mask
;   sta random_direction
;
; ; Random 0-99 (slower, any range):
;   lda #100
;   jsr rand_range
;   sta damage_roll
;
; ; 30% chance to drop item:
;   lda #77                      ; 77/255 ≈ 30%
;   jsr rand_percent
;   bcc @no_drop
;   jsr spawn_item
; @no_drop:
;
; ; Weighted loot table:
; loot_weights:
;   .byte 100    ; Common (index 0)
;   .byte 40     ; Uncommon (index 1)
;   .byte 10     ; Rare (index 2)
;   .byte 2      ; Legendary (index 3)
;   .byte 0      ; End marker
;
;   ldx #<loot_weights
;   jsr rand_weighted
;   ; A = 0 (common), 1 (uncommon), 2 (rare), or 3 (legendary)
;
; =============================================================================
