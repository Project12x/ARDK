;==============================================================================
; ARDK - Assembly HAL for 68000 Family
; hal_68k.inc - Platform-agnostic macros for 68K-based systems
;==============================================================================
;
; TARGET SYSTEMS:
;   - Sega Genesis / Mega Drive (primary)
;   - Amiga (OCS/ECS/AGA)
;   - Neo Geo
;   - Atari ST
;   - Sharp X68000
;
; DESIGN PRINCIPLES:
;   1. Macros expand to optimal code per-platform
;   2. Register conventions preserved across platforms
;   3. Memory model abstracted (Genesis vs Amiga chip RAM)
;   4. Platform-specific features opt-in via extensions
;
; REGISTER CONVENTIONS (68K standard):
;   D0-D2  - Scratch / return values
;   D3-D7  - Preserved across calls
;   A0-A1  - Scratch / pointers
;   A2-A6  - Preserved across calls
;   A7/SP  - Stack pointer
;
; ARDK-SPECIFIC CONVENTIONS:
;   A6     - Entity pool base pointer
;   D7     - Frame counter
;
;==============================================================================

;------------------------------------------------------------------------------
; Platform Detection
;------------------------------------------------------------------------------

    .ifndef PLATFORM_68K_FAMILY
PLATFORM_68K_FAMILY     equ 1
    .endif

; Set defaults if platform not specified
    .ifndef PLATFORM_GENESIS
    .ifndef PLATFORM_AMIGA
    .ifndef PLATFORM_NEOGEO
        ; Default to Genesis
PLATFORM_GENESIS        equ 1
    .endif
    .endif
    .endif

;------------------------------------------------------------------------------
; Fixed-Point Constants (8.8 format)
;------------------------------------------------------------------------------

FP_ONE                  equ $0100       ; 1.0 in 8.8
FP_HALF                 equ $0080       ; 0.5 in 8.8
FP_QUARTER              equ $0040       ; 0.25 in 8.8

;------------------------------------------------------------------------------
; Button Constants (Platform-Agnostic)
;------------------------------------------------------------------------------

HAL_BTN_A               equ $0001
HAL_BTN_B               equ $0002
HAL_BTN_C               equ $0004
HAL_BTN_START           equ $0008
HAL_BTN_UP              equ $0010
HAL_BTN_DOWN            equ $0020
HAL_BTN_LEFT            equ $0040
HAL_BTN_RIGHT           equ $0080
HAL_BTN_X               equ $0100       ; 6-button
HAL_BTN_Y               equ $0200       ; 6-button
HAL_BTN_Z               equ $0400       ; 6-button
HAL_BTN_MODE            equ $0800       ; 6-button

;------------------------------------------------------------------------------
; Entity Structure Offsets (must match entity.h)
;------------------------------------------------------------------------------

ENT_FLAGS               equ 0           ; u8  - entity flags
ENT_TYPE                equ 1           ; u8  - entity type
ENT_X                   equ 2           ; i16 - X position (8.8 fixed)
ENT_Y                   equ 4           ; i16 - Y position (8.8 fixed)
ENT_VX                  equ 6           ; i16 - X velocity (8.8 fixed)
ENT_VY                  equ 8           ; i16 - Y velocity (8.8 fixed)
ENT_HP                  equ 10          ; u8  - health points
ENT_TIMER               equ 11          ; u8  - general timer
ENT_SPRITE              equ 12          ; u8  - sprite ID
ENT_FRAME               equ 13          ; u8  - animation frame
ENT_DATA                equ 14          ; u16 - type-specific data
ENT_SIZE                equ 16          ; Total size per entity

; Entity flags
ENT_FLAG_ACTIVE         equ $01
ENT_FLAG_VISIBLE        equ $02
ENT_FLAG_SOLID          equ $04
ENT_FLAG_FRIENDLY       equ $08
ENT_FLAG_ENEMY          equ $10
ENT_FLAG_PICKUP         equ $20
ENT_FLAG_INVULN         equ $40
ENT_FLAG_FLASH          equ $80

; Entity categories (high nibble of type)
ENT_CAT_NONE            equ $00
ENT_CAT_PLAYER          equ $10
ENT_CAT_ENEMY           equ $20
ENT_CAT_PROJECTILE      equ $30
ENT_CAT_PICKUP          equ $40
ENT_CAT_EFFECT          equ $50

;------------------------------------------------------------------------------
; Fixed-Point Macros
;------------------------------------------------------------------------------

; Convert integer to fixed-point (D0 = input/output)
FP_FROM_INT:    macro
    lsl.w   #8, d0
    endm

; Convert fixed-point to integer (D0 = input/output)
FP_TO_INT:      macro
    asr.w   #8, d0
    ext.l   d0
    endm

; Add fixed-point: D0 = D0 + D1
FP_ADD:         macro
    add.w   d1, d0
    endm

; Subtract fixed-point: D0 = D0 - D1
FP_SUB:         macro
    sub.w   d1, d0
    endm

; Multiply fixed-point: D0 = D0 * D1 (preserves D2)
; Result is 8.8 format
FP_MUL:         macro
    muls.w  d1, d0          ; 16x16 -> 32 signed
    asr.l   #8, d0          ; Shift back to 8.8
    endm

; Divide fixed-point: D0 = D0 / D1
FP_DIV:         macro
    ext.l   d0
    lsl.l   #8, d0          ; Pre-shift for precision
    divs.w  d1, d0          ; 32/16 -> 16 quotient
    endm

; Absolute value: D0 = |D0|
FP_ABS:         macro
    tst.w   d0
    bpl.s   .abs_done\@
    neg.w   d0
.abs_done\@:
    endm

;------------------------------------------------------------------------------
; Entity Access Macros
;
; A6 = entity pool base
; D6 = entity index (not multiplied)
; Uses A0 as entity pointer after ENTITY_GET_PTR
;------------------------------------------------------------------------------

; Get pointer to entity D6 into A0
; A6 must be entity pool base
ENTITY_GET_PTR: macro
    move.l  d6, d0
    lsl.l   #4, d0          ; * 16 (entity size)
    lea     (a6, d0.l), a0  ; A0 = &entity_pool[D6]
    endm

; Check if entity is active (sets Z flag)
ENTITY_IS_ACTIVE: macro
    ENTITY_GET_PTR
    btst    #0, ENT_FLAGS(a0)   ; Test ACTIVE flag
    endm

; Get entity field into D0
; field = ENT_* offset
ENTITY_GET_BYTE: macro  field
    ENTITY_GET_PTR
    moveq   #0, d0
    move.b  \field(a0), d0
    endm

ENTITY_GET_WORD: macro  field
    ENTITY_GET_PTR
    move.w  \field(a0), d0
    endm

; Set entity field from D0
ENTITY_SET_BYTE: macro  field
    ENTITY_GET_PTR
    move.b  d0, \field(a0)
    endm

ENTITY_SET_WORD: macro  field
    ENTITY_GET_PTR
    move.w  d0, \field(a0)
    endm

; Apply velocity to position for entity in A0
ENTITY_APPLY_VELOCITY: macro
    move.w  ENT_VX(a0), d0
    add.w   d0, ENT_X(a0)
    move.w  ENT_VY(a0), d0
    add.w   d0, ENT_Y(a0)
    endm

; Iterate over all entities
; \1 = label to call for each active entity (A0 = entity, D6 = index)
; \2 = max entity count
ENTITY_FOR_EACH: macro  handler, max_count
    moveq   #0, d6
.entity_loop\@:
    ENTITY_GET_PTR
    btst    #0, ENT_FLAGS(a0)
    beq.s   .entity_next\@
    jsr     \handler
.entity_next\@:
    addq.w  #1, d6
    cmp.w   #\max_count, d6
    blt.s   .entity_loop\@
    endm

;------------------------------------------------------------------------------
; Input Macros (Genesis-specific with abstraction layer)
;------------------------------------------------------------------------------

    .ifdef PLATFORM_GENESIS

IO_DATA_1               equ $A10003
IO_DATA_2               equ $A10005
IO_CTRL_1               equ $A10009
IO_CTRL_2               equ $A1000B

; Read controller 1 into D0 (active-low converted to active-high)
HAL_INPUT_READ_P1: macro
    move.b  #$40, IO_CTRL_1     ; Set TH as output
    move.b  #$40, IO_DATA_1     ; TH = 1
    nop
    nop
    move.b  IO_DATA_1, d0       ; Read CBRLDU
    lsl.b   #2, d0
    move.b  #$00, IO_DATA_1     ; TH = 0
    nop
    nop
    move.b  IO_DATA_1, d1       ; Read SA00DU
    andi.b  #$3F, d1
    or.b    d1, d0
    not.b   d0                  ; Convert to active-high
    endm

; Check if button held (Z flag set if NOT pressed)
HAL_BTN_HELD: macro buttons
    move.w  _joy1_state, d0
    and.w   #\buttons, d0
    endm

; Check if button just pressed
HAL_BTN_PRESSED: macro buttons
    move.w  _joy1_pressed, d0
    and.w   #\buttons, d0
    endm

    .endif ; PLATFORM_GENESIS

    .ifdef PLATFORM_AMIGA

; Amiga joystick reading (Port 2 = JOY1DAT)
JOY1DAT                 equ $DFF00C

HAL_INPUT_READ_P1: macro
    move.w  JOY1DAT, d0
    ; Decode Amiga joystick format to standard
    ; (Amiga uses different encoding)
    moveq   #0, d1
    btst    #1, d0      ; Right
    beq.s   .no_right\@
    or.w    #HAL_BTN_RIGHT, d1
.no_right\@:
    btst    #9, d0      ; Left
    beq.s   .no_left\@
    or.w    #HAL_BTN_LEFT, d1
.no_left\@:
    ; Down = bit 0 XOR bit 1
    move.w  d0, d2
    lsr.w   #1, d2
    eor.w   d0, d2
    btst    #0, d2
    beq.s   .no_down\@
    or.w    #HAL_BTN_DOWN, d1
.no_down\@:
    ; Up = bit 8 XOR bit 9
    move.w  d0, d2
    lsr.w   #1, d2
    eor.w   d0, d2
    btst    #8, d2
    beq.s   .no_up\@
    or.w    #HAL_BTN_UP, d1
.no_up\@:
    move.w  d1, d0
    endm

    .endif ; PLATFORM_AMIGA

;------------------------------------------------------------------------------
; Sprite Macros (Genesis VDP)
;------------------------------------------------------------------------------

    .ifdef PLATFORM_GENESIS

VDP_DATA                equ $C00000
VDP_CTRL                equ $C00004

; Set sprite in sprite table
; D0 = slot, D1 = X, D2 = Y, D3 = tile, D4 = size/link
HAL_SPRITE_SET: macro
    ; Calculate VRAM address for sprite slot
    ; Sprite table at $BC00, 8 bytes per sprite
    move.l  d0, d5
    lsl.l   #3, d5              ; * 8
    add.l   #$BC00, d5
    ; Set VDP write address
    lsl.l   #2, d5
    lsr.w   #2, d5
    swap    d5
    or.l    #$40000000, d5
    move.l  d5, VDP_CTRL
    ; Write sprite data
    move.w  d2, VDP_DATA        ; Y position
    move.w  d4, VDP_DATA        ; Size/link
    move.w  d3, VDP_DATA        ; Tile
    move.w  d1, VDP_DATA        ; X position
    endm

; Hide sprite by moving off-screen
HAL_SPRITE_HIDE: macro slot
    moveq   #\slot, d0
    moveq   #0, d1              ; X = 0
    move.w  #224, d2            ; Y = off screen
    moveq   #0, d3
    moveq   #0, d4
    HAL_SPRITE_SET
    endm

    .endif ; PLATFORM_GENESIS

;------------------------------------------------------------------------------
; DMA Macros (Genesis)
;------------------------------------------------------------------------------

    .ifdef PLATFORM_GENESIS

; Queue DMA transfer (source in A0, dest in D0, length in D1)
; Actual transfer happens in VBlank
HAL_DMA_QUEUE: macro
    ; Store in DMA queue for VBlank processing
    lea     _dma_queue, a1
    move.w  _dma_queue_count, d2
    lsl.w   #3, d2              ; * 8 bytes per entry
    move.l  a0, (a1, d2.w)      ; Source
    move.w  d0, 4(a1, d2.w)     ; Dest
    move.w  d1, 6(a1, d2.w)     ; Length
    addq.w  #1, _dma_queue_count
    endm

    .endif ; PLATFORM_GENESIS

;------------------------------------------------------------------------------
; Math Table Lookups
;------------------------------------------------------------------------------

; Get sin(angle) into D0 (8.8 fixed-point)
; Input: D0 = angle (0-255)
HAL_SIN: macro
    andi.w  #$FF, d0
    add.w   d0, d0              ; * 2 for word table
    lea     sin_table, a0
    move.w  (a0, d0.w), d0
    endm

; Get cos(angle) into D0
HAL_COS: macro
    addi.w  #64, d0             ; cos(x) = sin(x + 64)
    andi.w  #$FF, d0
    add.w   d0, d0
    lea     sin_table, a0
    move.w  (a0, d0.w), d0
    endm

; Get atan2(dy, dx) into D0 (angle 0-255)
; Input: D0 = dy, D1 = dx
HAL_ATAN2: macro
    ; Use lookup table with octant mirroring
    jsr     _hal_atan2_impl
    endm

;------------------------------------------------------------------------------
; Frame Timing
;------------------------------------------------------------------------------

; Wait for VBlank
HAL_WAIT_VBLANK: macro
    .ifdef PLATFORM_GENESIS
        ; Wait for VBlank flag in VDP status
.wait_vblank\@:
        move.w  VDP_CTRL, d0
        btst    #3, d0
        beq.s   .wait_vblank\@
    .endif
    .ifdef PLATFORM_AMIGA
        ; Wait for VPOSR line 300
.wait_vblank\@:
        move.l  $DFF004, d0     ; VPOSR/VHPOSR
        lsr.l   #8, d0
        cmp.w   #300, d0
        blt.s   .wait_vblank\@
    .endif
    endm

; Increment frame counter (D7)
HAL_FRAME_INC: macro
    addq.l  #1, d7
    endm

;------------------------------------------------------------------------------
; Memory Operations
;------------------------------------------------------------------------------

; Fast memory copy: A0 = src, A1 = dest, D0 = count (longwords)
HAL_MEMCPY_FAST: macro
    subq.w  #1, d0
.copy_loop\@:
    move.l  (a0)+, (a1)+
    dbf     d0, .copy_loop\@
    endm

; Fast memory fill: A0 = dest, D0 = value, D1 = count (longwords)
HAL_MEMSET_FAST: macro
    subq.w  #1, d1
.fill_loop\@:
    move.l  d0, (a0)+
    dbf     d1, .fill_loop\@
    endm

;------------------------------------------------------------------------------
; Random Number Generation
;------------------------------------------------------------------------------

; Linear feedback shift register random
; Result in D0 (0-65535)
HAL_RAND: macro
    move.w  _rand_seed, d0
    move.w  d0, d1
    lsl.w   #7, d1
    eor.w   d1, d0
    move.w  d0, d1
    lsr.w   #9, d1
    eor.w   d1, d0
    move.w  d0, d1
    lsl.w   #8, d1
    eor.w   d1, d0
    move.w  d0, _rand_seed
    endm

;==============================================================================
; End of hal_68k.inc
;==============================================================================
