; =============================================================================
; SPRITE MULTIPLEXING - Display more than 8 sprites per scanline
; =============================================================================
; NES hardware limit: 8 sprites per scanline, excess sprites disappear
; Solution: Sort sprites by Y, cycle through visible sprites each frame
; Result: Managed flickering instead of invisible sprites
; =============================================================================

.segment "ZEROPAGE"
sprite_sort_y:      .res 64      ; Y positions for sorting
sprite_sort_idx:    .res 64      ; Original indices
num_active_sprites: .res 1       ; Count of active sprites
flicker_offset:     .res 1       ; Rotates each frame for even flickering

.segment "CODE"

; -----------------------------------------------------------------------------
; init_sprite_system - Call once at startup
; -----------------------------------------------------------------------------
.proc init_sprite_system
    lda #0
    sta num_active_sprites
    sta flicker_offset
    rts
.endproc

; -----------------------------------------------------------------------------
; sort_sprites_by_y - Insertion sort (fast for nearly-sorted data)
; Call before update_oam each frame
; -----------------------------------------------------------------------------
.proc sort_sprites_by_y
    ldx num_active_sprites
    cpx #2
    bcc @done                    ; Nothing to sort if < 2 sprites

    ldx #1                       ; Start at second element
@outer_loop:
    lda sprite_sort_y, x         ; Key = current Y
    sta temp_y
    lda sprite_sort_idx, x       ; Key index
    sta temp_idx

    txa
    tay
    dey                          ; j = i - 1

@inner_loop:
    bmi @insert                  ; j < 0, insert here
    lda sprite_sort_y, y
    cmp temp_y
    bcc @insert                  ; array[j] < key, insert here
    beq @insert

    ; Shift element right
    lda sprite_sort_y, y
    sta sprite_sort_y+1, y
    lda sprite_sort_idx, y
    sta sprite_sort_idx+1, y

    dey
    jmp @inner_loop

@insert:
    iny
    lda temp_y
    sta sprite_sort_y, y
    lda temp_idx
    sta sprite_sort_idx, y

    inx
    cpx num_active_sprites
    bne @outer_loop

@done:
    rts

temp_y:   .byte 0
temp_idx: .byte 0
.endproc

; -----------------------------------------------------------------------------
; apply_flicker_rotation - Rotate sprite priority for even flickering
; Call after sorting, before OAM copy
; -----------------------------------------------------------------------------
.proc apply_flicker_rotation
    ; Increment flicker offset each frame
    inc flicker_offset
    lda flicker_offset
    cmp num_active_sprites
    bcc @apply
    lda #0
    sta flicker_offset

@apply:
    ; Rotate the sorted list by flicker_offset
    ; This ensures all sprites get equal screen time
    ; Implementation: copy to temp, rotate, copy back

    ldx flicker_offset
    ldy #0
@rotate_loop:
    cpx num_active_sprites
    bcc @no_wrap
    ldx #0
@no_wrap:
    lda sprite_sort_idx, x
    sta temp_buffer, y
    inx
    iny
    cpy num_active_sprites
    bne @rotate_loop

    ; Copy back
    ldy #0
@copy_back:
    lda temp_buffer, y
    sta sprite_sort_idx, y
    iny
    cpy num_active_sprites
    bne @copy_back

    rts

temp_buffer: .res 64
.endproc

; -----------------------------------------------------------------------------
; update_oam_multiplexed - Copy sprites to OAM in sorted/rotated order
; Only first 64 sprites copied (NES OAM limit)
; -----------------------------------------------------------------------------
.proc update_oam_multiplexed
    lda num_active_sprites
    cmp #64
    bcc @use_actual
    lda #64                      ; Clamp to 64
@use_actual:
    sta temp_count

    ldx #0                       ; OAM index
    ldy #0                       ; Sorted index

@copy_loop:
    cpy temp_count
    beq @hide_rest

    ; Get original sprite index
    lda sprite_sort_idx, y
    asl
    asl                          ; * 4 for OAM offset
    tax

    ; Copy 4 bytes (Y, tile, attr, X)
    ; Source: your game's sprite data
    ; Dest: OAM buffer at $0200

    ; ... copy code depends on your sprite data format ...

    iny
    jmp @copy_loop

@hide_rest:
    ; Hide remaining OAM entries (move off-screen)
    lda #$FF
@hide_loop:
    cpy #64
    beq @done
    sta $0200, y                 ; Y = $FF (off-screen)
    iny
    iny
    iny
    iny
    bne @hide_loop

@done:
    rts

temp_count: .byte 0
.endproc

; =============================================================================
; USAGE EXAMPLE:
; =============================================================================
; In your game loop:
;
;   jsr update_game_sprites      ; Update sprite positions
;   jsr sort_sprites_by_y        ; Sort by Y for proper layering
;   jsr apply_flicker_rotation   ; Rotate for even flickering
;   jsr update_oam_multiplexed   ; Copy to OAM
;
; Result: Sprites properly sorted (closer = in front),
;         excess sprites flicker evenly instead of disappearing
; =============================================================================
