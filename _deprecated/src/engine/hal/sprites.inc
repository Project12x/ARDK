; =============================================================================
; HAL Sprite Macros - NES Implementation
; Simplifies OAM manipulation for metasprites
; =============================================================================
;
; These macros abstract the NES OAM format (Y, Tile, Attr, X) into
; more readable operations. They work with both single 8x8 sprites
; and 16x16 metasprites (4 tiles in 2x2 arrangement).
;
; OAM Layout:
;   Byte 0: Y position (scanline, 1 = top visible)
;   Byte 1: Tile index
;   Byte 2: Attributes (palette, flip, priority)
;   Byte 3: X position
;
; =============================================================================

; OAM Shadow location in RAM
OAM_SHADOW      = $0200

; Sprite attribute bits
SPR_PALETTE_0   = %00000000
SPR_PALETTE_1   = %00000001
SPR_PALETTE_2   = %00000010
SPR_PALETTE_3   = %00000011
SPR_PRIORITY    = %00100000     ; 0 = in front of BG, 1 = behind BG
SPR_FLIP_H      = %01000000     ; Horizontal flip
SPR_FLIP_V      = %10000000     ; Vertical flip

; =============================================================================
; oam_index (exported zero page variable)
; Game code should use this to track next free OAM slot
; =============================================================================

; -----------------------------------------------------------------------------
; SPRITE_WRITE - Write a single 8x8 sprite to OAM
; Parameters:
;   1: Y position (immediate or variable)
;   2: X position (immediate or variable)
;   3: Tile index
;   4: Attributes
;   5: OAM offset (Y register value, 0/4/8/etc)
; Clobbers: A
; -----------------------------------------------------------------------------
.macro SPRITE_WRITE y_pos, x_pos, tile, attr, oam_off
    lda y_pos
    sta OAM_SHADOW + oam_off
    lda #tile
    sta OAM_SHADOW + oam_off + 1
    lda #attr
    sta OAM_SHADOW + oam_off + 2
    lda x_pos
    sta OAM_SHADOW + oam_off + 3
.endmacro

; -----------------------------------------------------------------------------
; SPRITE_WRITE_Y - Write sprite using Y register as OAM index
; Parameters: y_pos, x_pos in A/X or zero page
; Use when dynamically iterating through sprites
; Clobbers: A
; Usage:
;   ldy oam_index
;   lda player_y
;   sta OAM_SHADOW, y       ; Y position
;   iny
;   lda #TILE_PLAYER
;   sta OAM_SHADOW, y       ; Tile
;   etc.
; -----------------------------------------------------------------------------

; -----------------------------------------------------------------------------
; METASPRITE_16x16 - Write a 16x16 metasprite (4 tiles)
; Parameters:
;   1: Y position (zero page address)
;   2: X position (zero page address)
;   3: Base tile (top-left tile index)
;   4: Palette (0-3)
;   5: OAM start offset (0/16/32/etc, must be multiple of 16)
;
; Tile arrangement in CHR (assumes sequential):
;   $00 $01   (top-left, top-right)
;   $10 $11   (bottom-left, bottom-right) - row offset 16 in CHR
;
; Clobbers: A
; -----------------------------------------------------------------------------
.macro METASPRITE_16x16 y_zp, x_zp, base_tile, palette, oam_off
    ; Top-left sprite
    lda y_zp
    sta OAM_SHADOW + oam_off
    lda #base_tile
    sta OAM_SHADOW + oam_off + 1
    lda #palette
    sta OAM_SHADOW + oam_off + 2
    lda x_zp
    sta OAM_SHADOW + oam_off + 3

    ; Top-right sprite
    lda y_zp
    sta OAM_SHADOW + oam_off + 4
    lda #(base_tile + 1)
    sta OAM_SHADOW + oam_off + 5
    lda #palette
    sta OAM_SHADOW + oam_off + 6
    lda x_zp
    clc
    adc #8
    sta OAM_SHADOW + oam_off + 7

    ; Bottom-left sprite
    lda y_zp
    clc
    adc #8
    sta OAM_SHADOW + oam_off + 8
    lda #(base_tile + 16)       ; Row below in CHR = +16 tiles
    sta OAM_SHADOW + oam_off + 9
    lda #palette
    sta OAM_SHADOW + oam_off + 10
    lda x_zp
    sta OAM_SHADOW + oam_off + 11

    ; Bottom-right sprite
    lda y_zp
    clc
    adc #8
    sta OAM_SHADOW + oam_off + 12
    lda #(base_tile + 17)       ; +16 for row, +1 for column
    sta OAM_SHADOW + oam_off + 13
    lda #palette
    sta OAM_SHADOW + oam_off + 14
    lda x_zp
    clc
    adc #8
    sta OAM_SHADOW + oam_off + 15
.endmacro

; -----------------------------------------------------------------------------
; SPRITE_HIDE - Hide a sprite by setting Y to 240 (off-screen)
; Parameters:
;   1: OAM offset
; Clobbers: A
; -----------------------------------------------------------------------------
.macro SPRITE_HIDE oam_off
    lda #$FF
    sta OAM_SHADOW + oam_off
.endmacro

; -----------------------------------------------------------------------------
; OAM_CLEAR - Clear all OAM (hide all sprites)
; Clobbers: A, X
; -----------------------------------------------------------------------------
.macro OAM_CLEAR
    lda #$FF
    ldx #0
:   sta OAM_SHADOW, x
    inx
    bne :-
.endmacro

; -----------------------------------------------------------------------------
; OAM_DMA_TRIGGER - Trigger OAM DMA transfer
; Call during VBlank only!
; Clobbers: A
; -----------------------------------------------------------------------------
.macro OAM_DMA_TRIGGER
    lda #0
    sta OAM_ADDR
    lda #>OAM_SHADOW
    sta $4014           ; DMA transfer takes 513-514 cycles
.endmacro
