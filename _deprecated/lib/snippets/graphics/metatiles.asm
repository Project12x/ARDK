; =============================================================================
; METATILE SYSTEM - Build levels from 16x16 or 32x32 blocks
; =============================================================================
; NES background is 8x8 tiles, but most games use larger "metatiles"
; Benefits: Smaller level data, easier level design, consistent collision
; =============================================================================

.segment "ZEROPAGE"

; Metatile rendering state
meta_ptr:           .res 2       ; Pointer to current metatile definition
level_ptr:          .res 2       ; Pointer to level data
render_x:           .res 1       ; Current render position
render_y:           .res 1

; Column buffer for scrolling
column_buffer:      .res 30      ; One column of tiles (30 rows visible)

.segment "CODE"

; =============================================================================
; 16x16 METATILE SYSTEM (2x2 tiles)
; =============================================================================
; Most common format: Each metatile = 4 tiles + 1 attribute nibble
; 5 bytes per metatile definition

; Metatile definition format:
; Byte 0: Top-left tile
; Byte 1: Top-right tile
; Byte 2: Bottom-left tile
; Byte 3: Bottom-right tile
; Byte 4: Attribute (collision/palette info)

METATILE_SIZE = 5                ; Bytes per metatile definition

; -----------------------------------------------------------------------------
; get_metatile - Get pointer to metatile definition
; Input: A = metatile ID
; Output: meta_ptr = pointer to metatile data
; -----------------------------------------------------------------------------
.proc get_metatile
    ; Multiply by METATILE_SIZE (5)
    sta temp_id
    asl                          ; x2
    asl                          ; x4
    clc
    adc temp_id                  ; x5

    ; Add to base address
    clc
    adc #<metatile_defs
    sta meta_ptr
    lda #0
    adc #>metatile_defs
    sta meta_ptr+1

    rts

temp_id: .byte 0
.endproc

; -----------------------------------------------------------------------------
; draw_metatile - Draw single metatile to nametable
; Input: A = metatile ID, X = screen X (in metatiles), Y = screen Y
; PPU address must be set before calling
; -----------------------------------------------------------------------------
.proc draw_metatile
    ; Get metatile definition
    jsr get_metatile

    ; Calculate PPU address
    ; Address = $2000 + Y*64 + X*2
    ; (Each metatile is 2 tiles wide, each row is 32 tiles)

    tya
    asl                          ; Y * 2
    asl                          ; Y * 4
    asl                          ; Y * 8
    asl                          ; Y * 16
    asl                          ; Y * 32
    asl                          ; Y * 64
    sta ppu_addr_lo

    txa
    asl                          ; X * 2
    clc
    adc ppu_addr_lo
    sta ppu_addr_lo

    ; Set PPU address (top row)
    bit $2002
    lda #$20                     ; Nametable 0
    sta $2006
    lda ppu_addr_lo
    sta $2006

    ; Write top-left and top-right
    ldy #0
    lda (meta_ptr), y            ; Top-left
    sta $2007
    iny
    lda (meta_ptr), y            ; Top-right
    sta $2007

    ; Set address for bottom row (+32)
    lda #$20
    sta $2006
    lda ppu_addr_lo
    clc
    adc #32
    sta $2006

    ; Write bottom-left and bottom-right
    iny
    lda (meta_ptr), y            ; Bottom-left
    sta $2007
    iny
    lda (meta_ptr), y            ; Bottom-right
    sta $2007

    rts

ppu_addr_lo: .byte 0
.endproc

; -----------------------------------------------------------------------------
; draw_metatile_column - Draw column of metatiles (for scrolling)
; Input: level_ptr = level data, X = column number
; Draws to column_buffer, then uploads during vblank
; -----------------------------------------------------------------------------
.proc draw_metatile_column
    stx current_column

    ; Get column from level data
    ; Level format assumed: array of metatile IDs, row-major

    ldy #0                       ; Metatile Y position

@row_loop:
    ; Get metatile ID from level
    ; Offset = Y * level_width + X
    tya
    ; ... calculate offset based on your level format ...

    lda (level_ptr), y           ; Get metatile ID
    jsr get_metatile

    ; Copy top tiles to column buffer
    ldx #0
    lda (meta_ptr, x)            ; Tile depends on column parity
    ; ... store to column_buffer ...

    iny
    cpy #15                      ; 15 metatiles tall = 30 tiles
    bne @row_loop

    rts

current_column: .byte 0
.endproc

; =============================================================================
; 32x32 METATILE SYSTEM (4x4 tiles)
; =============================================================================
; Used by some games for larger structures
; Each metatile = 16 tiles + attributes
; Can also be 4 16x16 metatiles nested

; Super-metatile definition (4 metatile IDs)
; Byte 0: Top-left metatile
; Byte 1: Top-right metatile
; Byte 2: Bottom-left metatile
; Byte 3: Bottom-right metatile

; -----------------------------------------------------------------------------
; draw_super_metatile - Draw 32x32 block
; Input: A = super-metatile ID, X = screen X (in 32px units), Y = screen Y
; -----------------------------------------------------------------------------
.proc draw_super_metatile
    jsr get_super_metatile

    ; Get X,Y in metatile units (multiply by 2)
    txa
    asl
    sta meta_x
    tya
    asl
    sta meta_y

    ; Draw four sub-metatiles
    ldy #0
    lda (meta_ptr), y            ; Top-left
    ldx meta_x
    ldy meta_y
    jsr draw_metatile

    ldy #1
    lda (meta_ptr), y            ; Top-right
    ldx meta_x
    inx
    ldy meta_y
    jsr draw_metatile

    ldy #2
    lda (meta_ptr), y            ; Bottom-left
    ldx meta_x
    ldy meta_y
    iny
    jsr draw_metatile

    ldy #3
    lda (meta_ptr), y            ; Bottom-right
    ldx meta_x
    inx
    ldy meta_y
    iny
    jsr draw_metatile

    rts

meta_x: .byte 0
meta_y: .byte 0
.endproc

get_super_metatile:
    ; Similar to get_metatile but for super-metatile table
    asl
    asl                          ; x4 (4 bytes per super-metatile)
    clc
    adc #<super_metatile_defs
    sta meta_ptr
    lda #0
    adc #>super_metatile_defs
    sta meta_ptr+1
    rts

; =============================================================================
; COLLISION DETECTION
; =============================================================================

; Collision flags in metatile attribute byte
COLL_SOLID      = %00000001      ; Blocks movement
COLL_PLATFORM   = %00000010      ; Solid from above only
COLL_HAZARD     = %00000100      ; Damages player
COLL_WATER      = %00001000      ; Swimming physics
COLL_LADDER     = %00010000      ; Climbing

; -----------------------------------------------------------------------------
; get_collision_at - Get collision flags at world position
; Input: A = world X, Y-reg = world Y (pixel coordinates)
; Output: A = collision flags
; -----------------------------------------------------------------------------
.proc get_collision_at
    ; Convert to metatile coordinates
    ; X / 16, Y / 16
    lsr
    lsr
    lsr
    lsr
    sta meta_x

    tya
    lsr
    lsr
    lsr
    lsr
    sta meta_y

    ; Get metatile ID from level
    ; ... depends on level format ...

    ; Get collision byte from metatile definition
    jsr get_metatile
    ldy #4                       ; Attribute byte
    lda (meta_ptr), y

    rts

meta_x: .byte 0
meta_y: .byte 0
.endproc

; -----------------------------------------------------------------------------
; check_solid - Check if position is blocked
; Input: A = world X, Y = world Y
; Output: Carry set if solid
; -----------------------------------------------------------------------------
.proc check_solid
    jsr get_collision_at
    and #COLL_SOLID | COLL_PLATFORM
    beq @not_solid
    sec
    rts
@not_solid:
    clc
    rts
.endproc

; =============================================================================
; METATILE DATA (EXAMPLE)
; =============================================================================

.segment "RODATA"

; 16x16 metatile definitions
metatile_defs:
    ; Metatile 0: Empty/sky
    .byte $24, $24, $24, $24     ; All sky tiles
    .byte $00                    ; No collision

    ; Metatile 1: Solid brick
    .byte $45, $45, $45, $45     ; Brick tiles
    .byte COLL_SOLID             ; Solid

    ; Metatile 2: Platform (solid from above)
    .byte $50, $51, $24, $24     ; Platform top, empty bottom
    .byte COLL_PLATFORM

    ; Metatile 3: Spikes (hazard)
    .byte $60, $61, $62, $63     ; Spike tiles
    .byte COLL_SOLID | COLL_HAZARD

    ; Metatile 4: Ladder
    .byte $70, $71, $70, $71     ; Ladder tiles
    .byte COLL_LADDER

    ; ... add more metatiles ...

; 32x32 super-metatile definitions
super_metatile_defs:
    ; Super-metatile 0: 2x2 of metatile 0 (empty)
    .byte 0, 0, 0, 0

    ; Super-metatile 1: 2x2 of metatile 1 (solid block)
    .byte 1, 1, 1, 1

    ; ... add more ...

; =============================================================================
; USAGE EXAMPLE
; =============================================================================
;
; ; Draw a screen of metatiles:
;   ldx #0                       ; Start at metatile column 0
; @col_loop:
;   ldy #0                       ; Start at metatile row 0
; @row_loop:
;   ; Get metatile ID from level data
;   lda (level_ptr), y           ; Simplified - real calc needed
;   jsr draw_metatile
;
;   iny
;   cpy #15                      ; 15 rows of metatiles
;   bne @row_loop
;
;   inx
;   cpx #16                      ; 16 columns of metatiles
;   bne @col_loop
;
; ; Collision check:
;   lda player_x
;   ldy player_y
;   jsr check_solid
;   bcs @hit_wall
;
; =============================================================================
