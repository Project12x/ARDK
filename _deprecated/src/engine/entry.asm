; =============================================================================
; MINIMAL NES TEST - Absolute bare minimum to show a sprite
; =============================================================================

.include "nes.inc"

.import input_read
.importzp buttons, buttons_old, buttons_pressed

.segment "ZEROPAGE"
.exportzp nmi_flag
nmi_flag: .res 1

.segment "CODE"

; -----------------------------------------------------------------------------
; Reset - Minimal NES Initialization
; -----------------------------------------------------------------------------
.export reset
.proc reset
    sei                     ; Disable interrupts
    cld                     ; Disable decimal mode
    ldx #$FF
    txs                     ; Initialize stack

    ; Disable rendering and NMI
    lda #0
    sta $2000               ; PPU_CTRL = 0
    sta $2001               ; PPU_MASK = 0

    ; Wait for PPU to be ready (1st vblank)
:   bit $2002
    bpl :-

    ; Clear ALL RAM
    lda #0
    tax
:   sta $0000, x
    sta $0100, x
    sta $0200, x
    sta $0300, x
    sta $0400, x
    sta $0500, x
    sta $0600, x
    sta $0700, x
    inx
    bne :-

    ; Wait for PPU to be ready (2nd vblank)
:   bit $2002
    bpl :-

    ; === PPU is now ready ===

    ; Initialize MMC3 (CRITICAL - do this before anything else!)
    jsr init_mmc3

    ; Load palette
    lda $2002               ; Reset PPU latch
    lda #$3F
    sta $2006               ; PPU_ADDR high
    lda #$00
    sta $2006               ; PPU_ADDR low

    ; Write 32 palette bytes
    ldx #0
:   lda palette, x
    sta $2007               ; PPU_DATA
    inx
    cpx #32
    bne :-

    ; Put 4x4 sprite (32x32) on screen at (100, 100)
    ; Using AI-extracted player sprite: tiles $00-$0F (16 tiles)
    ; Arranged as 4 rows of 4 tiles each

    ; Row 0 (Y=100): Tiles $00, $01, $02, $03
    lda #100
    sta $0200
    lda #$00
    sta $0201
    lda #0
    sta $0202
    lda #100
    sta $0203

    lda #100
    sta $0204
    lda #$01
    sta $0205
    lda #0
    sta $0206
    lda #108
    sta $0207

    lda #100
    sta $0208
    lda #$02
    sta $0209
    lda #0
    sta $020A
    lda #116
    sta $020B

    lda #100
    sta $020C
    lda #$03
    sta $020D
    lda #0
    sta $020E
    lda #124
    sta $020F

    ; Row 1 (Y=108): Tiles $04, $05, $06, $07
    lda #108
    sta $0210
    lda #$04
    sta $0211
    lda #0
    sta $0212
    lda #100
    sta $0213

    lda #108
    sta $0214
    lda #$05
    sta $0215
    lda #0
    sta $0216
    lda #108
    sta $0217

    lda #108
    sta $0218
    lda #$06
    sta $0219
    lda #0
    sta $021A
    lda #116
    sta $021B

    lda #108
    sta $021C
    lda #$07
    sta $021D
    lda #0
    sta $021E
    lda #124
    sta $021F

    ; Row 2 (Y=116): Tiles $08, $09, $0A, $0B
    lda #116
    sta $0220
    lda #$08
    sta $0221
    lda #0
    sta $0222
    lda #100
    sta $0223

    lda #116
    sta $0224
    lda #$09
    sta $0225
    lda #0
    sta $0226
    lda #108
    sta $0227

    lda #116
    sta $0228
    lda #$0A
    sta $0229
    lda #0
    sta $022A
    lda #116
    sta $022B

    lda #116
    sta $022C
    lda #$0B
    sta $022D
    lda #0
    sta $022E
    lda #124
    sta $022F

    ; Row 3 (Y=124): Tiles $0C, $0D, $0E, $0F
    lda #124
    sta $0230
    lda #$0C
    sta $0231
    lda #0
    sta $0232
    lda #100
    sta $0233

    lda #124
    sta $0234
    lda #$0D
    sta $0235
    lda #0
    sta $0236
    lda #108
    sta $0237

    lda #124
    sta $0238
    lda #$0E
    sta $0239
    lda #0
    sta $023A
    lda #116
    sta $023B

    lda #124
    sta $023C
    lda #$0F
    sta $023D
    lda #0
    sta $023E
    lda #124
    sta $023F

    ; Hide all other sprites (start at sprite 16)
    lda #$FF
    ldx #64                 ; Start after 16 sprites (16 * 4 bytes = 64)
:   sta $0200, x
    inx
    inx
    inx
    inx
    bne :-

    ; Enable NMI
    lda #%10000000
    sta $2000               ; PPU_CTRL: NMI on

    ; Enable rendering (sprites only)
    lda #%00010000
    sta $2001               ; PPU_MASK: show sprites

    ; Main loop - read input and update sprite
:
    ; Wait for NMI to complete
    lda #0
    sta nmi_flag
@wait_nmi:
    lda nmi_flag
    beq @wait_nmi

    ; Read controller
    jsr input_read

    ; Check Up - move all 16 sprites (4x4 metatile)
    lda buttons
    and #%00001000          ; Up bit
    beq @check_down
    ; Move all Y positions up by 2
    ldx #0
@move_up_loop:
    lda $0200, x            ; Y position
    sec
    sbc #2
    sta $0200, x
    inx
    inx
    inx
    inx                     ; Skip to next sprite (4 bytes each)
    cpx #64                 ; 16 sprites * 4 bytes = 64
    bne @move_up_loop

@check_down:
    lda buttons
    and #%00000100          ; Down bit
    beq @check_left
    ; Move all Y positions down by 2
    ldx #0
@move_down_loop:
    lda $0200, x
    clc
    adc #2
    sta $0200, x
    inx
    inx
    inx
    inx
    cpx #64
    bne @move_down_loop

@check_left:
    lda buttons
    and #%00000010          ; Left bit
    beq @check_right
    ; Move all X positions left by 2
    ldx #3                  ; X is at offset 3 in each sprite
@move_left_loop:
    lda $0200, x
    sec
    sbc #2
    sta $0200, x
    inx
    inx
    inx
    inx
    cpx #67                 ; 64 + 3
    bne @move_left_loop

@check_right:
    lda buttons
    and #%00000001          ; Right bit
    beq @done_input
    ; Move all X positions right by 2
    ldx #3
@move_right_loop:
    lda $0200, x
    clc
    adc #2
    sta $0200, x
    inx
    inx
    inx
    inx
    cpx #67
    bne @move_right_loop

@done_input:
    jmp :-
.endproc

; -----------------------------------------------------------------------------
; Palette Data
; -----------------------------------------------------------------------------
palette:
    ; Background palettes (not used yet)
    .byte $0F,$30,$30,$30, $0F,$30,$30,$30, $0F,$30,$30,$30, $0F,$30,$30,$30
    ; Sprite palette 0: Black, Magenta, Cyan, White (matching AI sprite)
    .byte $0F,$24,$1C,$30, $0F,$30,$30,$30, $0F,$30,$30,$30, $0F,$30,$30,$30
    ; $0F = Black (transparent)
    ; $24 = Magenta/Pink
    ; $1C = Cyan
    ; $30 = White

; -----------------------------------------------------------------------------
; Initialize MMC3 - Critical for mapper to work
; Based on proven working examples
; -----------------------------------------------------------------------------
.proc init_mmc3
    ; PRG Bank setup
    lda #$06
    sta $8000           ; Select register 6 (PRG bank at $8000)
    lda #$00
    sta $8001           ; Use bank 0

    lda #$07
    sta $8000           ; Select register 7 (PRG bank at $A000)
    lda #$01
    sta $8001           ; Use bank 1

    ; CHR Bank setup - 2K banks use EVEN numbers only!
    lda #$00
    sta $8000           ; Select register 0
    lda #$00
    sta $8001           ; 2KB CHR bank 0 at $0000

    lda #$01
    sta $8000           ; Select register 1
    lda #$02            ; EVEN number! (not 1)
    sta $8001           ; 2KB CHR bank 2 at $0800

    ; 1KB CHR banks
    lda #$02
    sta $8000
    lda #$04
    sta $8001           ; 1KB CHR bank 4 at $1000

    lda #$03
    sta $8000
    lda #$05
    sta $8001           ; 1KB CHR bank 5 at $1400

    lda #$04
    sta $8000
    lda #$06
    sta $8001           ; 1KB CHR bank 6 at $1800

    lda #$05
    sta $8000
    lda #$07
    sta $8001           ; 1KB CHR bank 7 at $1C00

    ; Mirroring (horizontal)
    lda #$00
    sta $A000

    ; Enable WRAM
    lda #$80
    sta $A001

    ; Disable IRQ
    sta $E000

    rts
.endproc
