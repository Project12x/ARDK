; =============================================================================
; RLE (RUN-LENGTH ENCODING) COMPRESSION
; =============================================================================
; Simple and fast compression for repetitive data (backgrounds, nametables)
; Format: [count][byte] pairs, where count=0 marks end
; For non-repeating data: negative count followed by literal bytes
; =============================================================================

.segment "ZEROPAGE"
rle_src:        .res 2           ; Source pointer
rle_dst:        .res 2           ; Destination pointer
rle_count:      .res 1           ; Byte counter

.segment "CODE"

; =============================================================================
; SIMPLE RLE (runs only, no literals)
; =============================================================================
; Format: [count][value] pairs, $00 count = end
; Good for: Solid backgrounds, simple patterns
; Compression: ~50-80% for typical NES backgrounds

; -----------------------------------------------------------------------------
; rle_decode_simple - Decompress RLE data to buffer
; Input: rle_src = source data, rle_dst = destination
; Output: Fills destination with decompressed data
; -----------------------------------------------------------------------------
.proc rle_decode_simple
    ldy #0                       ; Source index

@loop:
    lda (rle_src), y             ; Get count
    beq @done                    ; 0 = end marker
    sta rle_count
    iny
    lda (rle_src), y             ; Get value
    iny

    ldx rle_count
@write_loop:
    sta (rle_dst)
    inc rle_dst
    bne @no_inc_hi
    inc rle_dst+1
@no_inc_hi:
    dex
    bne @write_loop

    jmp @loop

@done:
    rts
.endproc

; -----------------------------------------------------------------------------
; rle_decode_to_ppu - Decompress directly to PPU
; Input: rle_src = source data, PPU address already set
; Use for: Loading nametables directly
; -----------------------------------------------------------------------------
.proc rle_decode_to_ppu
    ldy #0

@loop:
    lda (rle_src), y             ; Get count
    beq @done
    sta rle_count
    iny
    lda (rle_src), y             ; Get value
    iny

    ldx rle_count
@write_loop:
    sta $2007                    ; Write to PPU
    dex
    bne @write_loop

    jmp @loop

@done:
    rts
.endproc

; =============================================================================
; ADVANCED RLE (runs + literals)
; =============================================================================
; Format:
;   Positive count (1-127): Run - count copies of next byte
;   Negative count (-1 to -128): Literal - |count| literal bytes follow
;   Zero: End marker
;
; Better for mixed data with some non-repeating sections

; -----------------------------------------------------------------------------
; rle_decode_advanced - Decompress RLE with literal support
; Input: rle_src = source, rle_dst = destination
; -----------------------------------------------------------------------------
.proc rle_decode_advanced
    ldy #0

@loop:
    lda (rle_src), y             ; Get control byte
    beq @done                    ; 0 = end
    bmi @literal                 ; Negative = literal run

    ; Positive = repeat run
    sta rle_count
    iny
    lda (rle_src), y             ; Value to repeat
    iny

    ldx rle_count
@repeat_loop:
    sta (rle_dst)
    jsr inc_dst
    dex
    bne @repeat_loop
    jmp @loop

@literal:
    ; Negative = literal bytes follow
    eor #$FF
    clc
    adc #1                       ; Negate to get count
    sta rle_count

@literal_loop:
    iny
    lda (rle_src), y             ; Get literal byte
    sta (rle_dst)
    jsr inc_dst
    dec rle_count
    bne @literal_loop
    iny
    jmp @loop

@done:
    rts

inc_dst:
    inc rle_dst
    bne @no_inc
    inc rle_dst+1
@no_inc:
    rts
.endproc

; =============================================================================
; RLE ENCODER (for tools/runtime compression)
; =============================================================================

.segment "BSS"
encode_buffer:      .res 256     ; Temporary encode buffer

.segment "CODE"

; -----------------------------------------------------------------------------
; rle_encode_simple - Compress buffer using simple RLE
; Input: rle_src = source, A = source length, rle_dst = destination
; Output: A = compressed length
; Note: Usually run offline in tools, but included for completeness
; -----------------------------------------------------------------------------
.proc rle_encode_simple
    sta src_len

    ldy #0                       ; Source index
    ldx #0                       ; Dest index

@scan:
    cpy src_len
    beq @finish

    lda (rle_src), y             ; Get current byte
    sta current_val

    ; Count consecutive bytes
    lda #1
    sta run_count

@count_run:
    iny
    cpy src_len
    beq @emit_run
    lda (rle_src), y
    cmp current_val
    bne @emit_run
    inc run_count
    lda run_count
    cmp #255                     ; Max run length
    bne @count_run

@emit_run:
    ; Store count and value
    lda run_count
    sta (rle_dst), x
    inx
    lda current_val
    sta (rle_dst), x
    inx
    jmp @scan

@finish:
    ; End marker
    lda #0
    sta (rle_dst), x
    inx
    txa                          ; Return compressed length
    rts

src_len:     .byte 0
current_val: .byte 0
run_count:   .byte 0
.endproc

; =============================================================================
; NAMETABLE HELPERS
; =============================================================================

; -----------------------------------------------------------------------------
; load_nametable_rle - Load RLE-compressed nametable to PPU
; Input: A = nametable (0-3), rle_src = compressed data
; -----------------------------------------------------------------------------
.proc load_nametable_rle
    ; Calculate nametable address ($2000, $2400, $2800, $2C00)
    asl
    asl
    ora #$20                     ; $20, $24, $28, $2C

    ; Set PPU address
    bit $2002                    ; Reset latch
    sta $2006                    ; High byte
    lda #$00
    sta $2006                    ; Low byte

    ; Decompress to PPU
    jsr rle_decode_to_ppu

    rts
.endproc

; -----------------------------------------------------------------------------
; load_attribute_rle - Load RLE-compressed attribute table
; Input: A = nametable (0-3), rle_src = compressed attributes
; Attributes are 64 bytes at end of each nametable
; -----------------------------------------------------------------------------
.proc load_attribute_rle
    ; Calculate attribute address ($23C0, $27C0, $2BC0, $2FC0)
    asl
    asl
    ora #$23

    bit $2002
    sta $2006
    lda #$C0
    sta $2006

    jsr rle_decode_to_ppu

    rts
.endproc

; =============================================================================
; EXAMPLE RLE DATA
; =============================================================================

; Example: Simple repeating background
; 32 tiles of $24 (sky), 64 tiles of $00 (space), 32 tiles of $45 (ground)
example_rle_data:
    .byte 32, $24                ; 32x sky tile
    .byte 64, $00                ; 64x empty
    .byte 32, $45                ; 32x ground
    .byte 0                      ; End marker

; Example: Mixed data with literals
; Format: +N = repeat next byte N times, -N = N literal bytes follow
example_mixed_rle:
    .byte 10, $20                ; 10x space
    .byte -5, "HELLO"            ; 5 literal bytes
    .byte 10, $20                ; 10x space
    .byte 0                      ; End

; =============================================================================
; USAGE EXAMPLES:
; =============================================================================
;
; ; Load compressed nametable:
;   lda #<level1_nametable_rle
;   sta rle_src
;   lda #>level1_nametable_rle
;   sta rle_src+1
;   lda #0                       ; Nametable 0 ($2000)
;   jsr load_nametable_rle
;
; ; Decompress to RAM buffer:
;   lda #<compressed_data
;   sta rle_src
;   lda #>compressed_data
;   sta rle_src+1
;   lda #<buffer
;   sta rle_dst
;   lda #>buffer
;   sta rle_dst+1
;   jsr rle_decode_simple
;
; =============================================================================
; COMPRESSION TIPS:
; =============================================================================
;
; 1. RLE works best for:
;    - Solid color backgrounds
;    - Simple repeating patterns
;    - Attribute tables (lots of same values)
;
; 2. RLE works poorly for:
;    - Detailed graphics
;    - Random/noisy data
;    - Already compressed data
;
; 3. For better compression, consider:
;    - donut (NES-optimized, ~3:1 ratio)
;    - LZ4 (fast decompress, ~2:1 ratio)
;    - Tokumaru's specialized routines
;
; 4. Typical NES compression ratios:
;    - Simple backgrounds: 80-90% (RLE)
;    - Complex backgrounds: 40-60% (LZ variants)
;    - Sprite data: Usually not worth compressing
;
; =============================================================================
