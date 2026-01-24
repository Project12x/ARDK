;==============================================================================
; ARDK - Assembly HAL for Z80/Game Boy Family
; hal_z80_gb.inc - Platform-agnostic macros for Z80-based systems
;==============================================================================
;
; TARGET SYSTEMS:
;   - Game Boy / Game Boy Color (primary - Sharp LR35902)
;   - Sega Master System (Z80)
;   - Sega Game Gear (Z80)
;   - MSX / MSX2
;   - ZX Spectrum
;   - ColecoVision
;
; NOTE: Game Boy uses a custom "Sharp LR35902" which is Z80-like but NOT
; identical. Key differences:
;   - No IX/IY index registers
;   - No alternate register set (AF', BC', etc.)
;   - Different flag behavior in some instructions
;   - Different I/O model (memory-mapped vs ports)
;
; This file provides two macro sets:
;   1. Game Boy specific (PLATFORM_GB)
;   2. Standard Z80 (PLATFORM_SMS, etc.)
;
; REGISTER CONVENTIONS:
;   A     - Accumulator
;   BC    - General purpose / counter
;   DE    - General purpose / destination pointer
;   HL    - Primary pointer / accumulator pair
;   SP    - Stack pointer
;
; ARDK CONVENTIONS:
;   HL    - Entity pointer (after ENTITY_GET_PTR)
;   BC    - Iteration counter
;   DE    - Secondary pointer / velocity
;
;==============================================================================

;------------------------------------------------------------------------------
; Platform Detection
;------------------------------------------------------------------------------

IF !DEF(PLATFORM_Z80_FAMILY)
PLATFORM_Z80_FAMILY EQU 1
ENDC

; Set defaults if platform not specified
IF !DEF(PLATFORM_GB) && !DEF(PLATFORM_SMS) && !DEF(PLATFORM_GG)
    ; Default to Game Boy
PLATFORM_GB EQU 1
ENDC

;------------------------------------------------------------------------------
; Hardware Registers (Game Boy)
;------------------------------------------------------------------------------

IF DEF(PLATFORM_GB)

; LCD registers
LCDC            EQU $FF40   ; LCD Control
STAT            EQU $FF41   ; LCD Status
SCY             EQU $FF42   ; Scroll Y
SCX             EQU $FF43   ; Scroll X
LY              EQU $FF44   ; Current scanline
LYC             EQU $FF45   ; LY Compare
DMA             EQU $FF46   ; OAM DMA source
BGP             EQU $FF47   ; BG Palette
OBP0            EQU $FF48   ; Sprite Palette 0
OBP1            EQU $FF49   ; Sprite Palette 1
WY              EQU $FF4A   ; Window Y
WX              EQU $FF4B   ; Window X

; Input
JOYP            EQU $FF00   ; Joypad

; Interrupt flags
IF_REG          EQU $FF0F   ; Interrupt Flag
IE_REG          EQU $FFFF   ; Interrupt Enable

; VRAM
VRAM_TILES      EQU $8000   ; Tile data
VRAM_MAP0       EQU $9800   ; BG Map 0
VRAM_MAP1       EQU $9C00   ; BG Map 1

; OAM
OAM_RAM         EQU $FE00   ; Sprite attributes (40 sprites * 4 bytes)

; WRAM
WRAM            EQU $C000   ; Work RAM
HRAM            EQU $FF80   ; High RAM (fast)

ENDC ; PLATFORM_GB

;------------------------------------------------------------------------------
; Hardware Registers (Master System)
;------------------------------------------------------------------------------

IF DEF(PLATFORM_SMS)

; VDP ports
VDP_DATA        EQU $BE     ; VDP data port
VDP_CTRL        EQU $BF     ; VDP control port

; Input ports
IO_PORT_A       EQU $DC     ; Controller port A
IO_PORT_B       EQU $DD     ; Controller port B

; Memory control
MEM_CTRL        EQU $3E     ; Memory control

ENDC ; PLATFORM_SMS

;------------------------------------------------------------------------------
; Button Constants (Platform-Agnostic)
;------------------------------------------------------------------------------

HAL_BTN_A       EQU %00000001
HAL_BTN_B       EQU %00000010
HAL_BTN_SELECT  EQU %00000100
HAL_BTN_START   EQU %00001000
HAL_BTN_UP      EQU %00010000
HAL_BTN_DOWN    EQU %00100000
HAL_BTN_LEFT    EQU %01000000
HAL_BTN_RIGHT   EQU %10000000

;------------------------------------------------------------------------------
; Memory Layout
;------------------------------------------------------------------------------

; HRAM variables (Game Boy high RAM for speed)
IF DEF(PLATFORM_GB)

HAL_JOY_STATE   EQU $FF80   ; Current joypad state
HAL_JOY_PRESS   EQU $FF81   ; Newly pressed buttons
HAL_JOY_PREV    EQU $FF82   ; Previous frame state
HAL_FRAME_LO    EQU $FF83   ; Frame counter low
HAL_FRAME_HI    EQU $FF84   ; Frame counter high
HAL_TEMP0       EQU $FF85   ; Temp storage
HAL_TEMP1       EQU $FF86
HAL_TEMP2       EQU $FF87
HAL_TEMP3       EQU $FF88
HAL_DMA_ROUTINE EQU $FF89   ; OAM DMA routine stored here (10 bytes)

ENDC

;------------------------------------------------------------------------------
; Entity Structure Offsets (must match entity.h)
;------------------------------------------------------------------------------

ENT_FLAGS       EQU 0       ; u8
ENT_TYPE        EQU 1       ; u8
ENT_X_LO        EQU 2       ; u8 (8.8 low)
ENT_X_HI        EQU 3       ; u8 (8.8 high)
ENT_Y_LO        EQU 4       ; u8
ENT_Y_HI        EQU 5       ; u8
ENT_VX_LO       EQU 6       ; u8
ENT_VX_HI       EQU 7       ; u8
ENT_VY_LO       EQU 8       ; u8
ENT_VY_HI       EQU 9       ; u8
ENT_HP          EQU 10      ; u8
ENT_TIMER       EQU 11      ; u8
ENT_SPRITE      EQU 12      ; u8
ENT_FRAME       EQU 13      ; u8
ENT_DATA_LO     EQU 14      ; u8
ENT_DATA_HI     EQU 15      ; u8
ENT_SIZE        EQU 16

; Entity flags
ENT_FLAG_ACTIVE   EQU %00000001
ENT_FLAG_VISIBLE  EQU %00000010
ENT_FLAG_SOLID    EQU %00000100
ENT_FLAG_FRIENDLY EQU %00001000
ENT_FLAG_ENEMY    EQU %00010000
ENT_FLAG_PICKUP   EQU %00100000
ENT_FLAG_INVULN   EQU %01000000
ENT_FLAG_FLASH    EQU %10000000

; Entity categories
ENT_CAT_NONE        EQU $00
ENT_CAT_PLAYER      EQU $10
ENT_CAT_ENEMY       EQU $20
ENT_CAT_PROJECTILE  EQU $30
ENT_CAT_PICKUP      EQU $40
ENT_CAT_EFFECT      EQU $50

;------------------------------------------------------------------------------
; Fixed-Point Macros (8.8 format)
;
; DE = value (D = high/integer, E = low/fraction)
; HL = value (H = high, L = low)
;------------------------------------------------------------------------------

; Add 16-bit: HL = HL + DE
MACRO FP_ADD_HL_DE
    add hl, de
ENDM

; Subtract 16-bit: HL = HL - DE
MACRO FP_SUB_HL_DE
    ; Z80/GB lacks direct 16-bit subtract
    ld a, l
    sub e
    ld l, a
    ld a, h
    sbc d
    ld h, a
ENDM

; Negate HL
MACRO FP_NEG_HL
    ld a, l
    cpl
    ld l, a
    ld a, h
    cpl
    ld h, a
    inc hl
ENDM

; Convert HL (8.8 fixed) to A (integer only)
MACRO FP_TO_INT_A
    ld a, h
ENDM

;------------------------------------------------------------------------------
; Entity Access Macros
;
; Entity ID in A or B, result pointer in HL
;------------------------------------------------------------------------------

; Get entity pointer: HL = entity_pool + (A * 16)
; Input: A = entity ID
; Output: HL = pointer to entity
MACRO ENTITY_GET_PTR
    ; Multiply A by 16 (shift left 4)
    ld h, 0
    ld l, a
    add hl, hl      ; *2
    add hl, hl      ; *4
    add hl, hl      ; *8
    add hl, hl      ; *16
    ; Add entity pool base
    ld de, entity_pool
    add hl, de
ENDM

; Check if entity active (Z flag set if NOT active)
; Input: HL = entity pointer
MACRO ENTITY_IS_ACTIVE
    ld a, [hl]              ; Get flags
    and ENT_FLAG_ACTIVE
ENDM

; Get entity field byte into A
; Input: HL = entity pointer
MACRO ENTITY_GET_FIELD offset
    push hl
    ld de, offset
    add hl, de
    ld a, [hl]
    pop hl
ENDM

; Set entity field byte from A
; Input: HL = entity pointer, A = value
MACRO ENTITY_SET_FIELD offset
    push hl
    push af
    ld de, offset
    add hl, de
    pop af
    ld [hl], a
    pop hl
ENDM

; Apply velocity to position
; Input: HL = entity pointer
; Preserves: HL
MACRO ENTITY_APPLY_VELOCITY
    push hl

    ; X += VX
    ; Get X into DE
    ld de, ENT_X_LO
    add hl, de
    ld e, [hl]
    inc hl
    ld d, [hl]      ; DE = X

    push hl
    pop hl          ; Restore for VX
    ld bc, (ENT_VX_LO - ENT_X_HI)
    add hl, bc
    ld c, [hl]
    inc hl
    ld b, [hl]      ; BC = VX

    ; DE = X + VX
    push hl
    ld h, d
    ld l, e
    add hl, bc
    ld d, h
    ld e, l
    pop hl

    ; Store X back
    ld bc, (ENT_X_LO - ENT_VX_HI)
    add hl, bc
    ld [hl], e
    inc hl
    ld [hl], d

    ; Similar for Y...
    pop hl
    push hl

    ld de, ENT_Y_LO
    add hl, de
    ld e, [hl]
    inc hl
    ld d, [hl]

    ld bc, (ENT_VY_LO - ENT_Y_HI)
    add hl, bc
    ld c, [hl]
    inc hl
    ld b, [hl]

    push hl
    ld h, d
    ld l, e
    add hl, bc
    ld d, h
    ld e, l
    pop hl

    ld bc, (ENT_Y_LO - ENT_VY_HI)
    add hl, bc
    ld [hl], e
    inc hl
    ld [hl], d

    pop hl
ENDM

;------------------------------------------------------------------------------
; Input Macros (Game Boy)
;------------------------------------------------------------------------------

IF DEF(PLATFORM_GB)

; Read joypad into A (active-high: 1 = pressed)
MACRO HAL_INPUT_READ
    ; Read D-pad
    ld a, $20           ; Select D-pad
    ldh [JOYP], a
    ldh a, [JOYP]       ; Read (need multiple reads for stability)
    ldh a, [JOYP]
    cpl                 ; Convert to active-high
    and $0F
    swap a              ; Move to high nibble
    ld b, a

    ; Read buttons
    ld a, $10           ; Select buttons
    ldh [JOYP], a
    ldh a, [JOYP]
    ldh a, [JOYP]
    ldh a, [JOYP]
    ldh a, [JOYP]
    cpl
    and $0F
    or b                ; Combine with D-pad

    ; Reset joypad
    ld b, a
    ld a, $30
    ldh [JOYP], a
    ld a, b
ENDM

; Update input state (call once per frame)
MACRO HAL_INPUT_UPDATE
    ; Save previous state
    ldh a, [HAL_JOY_STATE]
    ldh [HAL_JOY_PREV], a

    ; Read new state
    HAL_INPUT_READ
    ldh [HAL_JOY_STATE], a

    ; Calculate newly pressed
    ld b, a
    ldh a, [HAL_JOY_PREV]
    cpl
    and b
    ldh [HAL_JOY_PRESS], a
ENDM

; Check if button held (Z = not pressed)
MACRO HAL_BTN_HELD buttons
    ldh a, [HAL_JOY_STATE]
    and buttons
ENDM

; Check if button just pressed
MACRO HAL_BTN_PRESSED buttons
    ldh a, [HAL_JOY_PRESS]
    and buttons
ENDM

ENDC ; PLATFORM_GB

;------------------------------------------------------------------------------
; Input Macros (Master System)
;------------------------------------------------------------------------------

IF DEF(PLATFORM_SMS)

MACRO HAL_INPUT_READ
    in a, (IO_PORT_A)
    cpl                 ; Convert to active-high
ENDM

ENDC ; PLATFORM_SMS

;------------------------------------------------------------------------------
; Sprite Macros (Game Boy OAM)
;------------------------------------------------------------------------------

IF DEF(PLATFORM_GB)

; OAM shadow buffer in WRAM
OAM_SHADOW      EQU $C000   ; 40 sprites * 4 bytes = 160 bytes

; Set sprite in OAM shadow
; slot = 0-39, Y/X in A/B, tile in C, attr in D
MACRO HAL_SPRITE_SET slot
    ld hl, OAM_SHADOW + (slot * 4)
    ld a, b             ; Y position
    add 16              ; GB Y offset
    ld [hl+], a
    ld a, c             ; X position
    add 8               ; GB X offset
    ld [hl+], a
    ld a, d             ; Tile
    ld [hl+], a
    ld a, e             ; Attributes
    ld [hl], a
ENDM

; Hide sprite
MACRO HAL_SPRITE_HIDE slot
    ld hl, OAM_SHADOW + (slot * 4)
    xor a               ; Y = 0 (off screen)
    ld [hl], a
ENDM

; Copy OAM shadow to real OAM via DMA
; Must call from HRAM!
MACRO HAL_OAM_DMA
    ld a, HIGH(OAM_SHADOW)
    ldh [DMA], a
    ld a, 40            ; Wait 160 cycles
.dma_wait\@:
    dec a
    jr nz, .dma_wait\@
ENDM

ENDC ; PLATFORM_GB

;------------------------------------------------------------------------------
; Frame Timing
;------------------------------------------------------------------------------

IF DEF(PLATFORM_GB)

; Wait for VBlank (LY = 144)
MACRO HAL_WAIT_VBLANK
.wait_vblank\@:
    ldh a, [LY]
    cp 144
    jr nz, .wait_vblank\@
ENDM

; Increment frame counter
MACRO HAL_FRAME_INC
    ldh a, [HAL_FRAME_LO]
    inc a
    ldh [HAL_FRAME_LO], a
    jr nz, .no_carry\@
    ldh a, [HAL_FRAME_HI]
    inc a
    ldh [HAL_FRAME_HI], a
.no_carry\@:
ENDM

ENDC ; PLATFORM_GB

;------------------------------------------------------------------------------
; Math Table Lookups
;------------------------------------------------------------------------------

; Get sin(angle) into HL (8.8 fixed)
; Input: A = angle (0-255)
MACRO HAL_SIN
    ld h, 0
    ld l, a
    add hl, hl          ; *2 for word table
    ld de, sin_table
    add hl, de
    ld a, [hl+]
    ld h, [hl]
    ld l, a             ; HL = sin value
ENDM

; Get cos(angle) into HL
MACRO HAL_COS
    add 64              ; cos = sin(x+64)
    HAL_SIN
ENDM

;------------------------------------------------------------------------------
; Memory Operations
;------------------------------------------------------------------------------

; Copy BC bytes from HL to DE
MACRO HAL_MEMCPY
.copy\@:
    ld a, [hl+]
    ld [de], a
    inc de
    dec bc
    ld a, b
    or c
    jr nz, .copy\@
ENDM

; Fill BC bytes at HL with A
MACRO HAL_MEMSET
.fill\@:
    ld [hl+], a
    dec bc
    ld a, b
    or c
    jr nz, .fill\@
ENDM

;------------------------------------------------------------------------------
; Random Number Generation
;------------------------------------------------------------------------------

; Simple LFSR random, result in A
MACRO HAL_RAND
    ldh a, [HAL_TEMP3]
    ld b, a
    add a               ; Shift left
    jr nc, .no_tap\@
    xor $1D             ; Tap polynomial
.no_tap\@:
    ldh [HAL_TEMP3], a
ENDM

;==============================================================================
; End of hal_z80_gb.inc
;==============================================================================
