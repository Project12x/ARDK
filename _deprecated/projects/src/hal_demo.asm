; =============================================================================
; HAL Demo - Demonstrates ARDK HAL Capabilities
; =============================================================================
; Features demonstrated:
;   - Player movement (D-pad)
;   - Enemy with simple chase AI
;   - Player projectiles (auto-fire)
;   - Screen boundary clamping
;   - 16x16 metasprite rendering
;   - Background with static tiles
;   - MMC3 mapper CHR bank switching
;
; Advanced MMC3 Features (inspired by Batman, Recca, Kirby):
;   - Multi-split scanline IRQ (parallax + status bar)
;   - CHR bank animation (animated background tiles)
;   - Status bar frozen at bottom 40 pixels
;   - Mid-frame CHR bank swapping
; =============================================================================

; =============================================================================
; FEATURE FLAGS - Enable/disable advanced features
; =============================================================================
; Set to 1 to enable, 0 to disable
; These allow building different engine configurations from the same codebase
;
; Feature Groups (for future engine variants):
;   BASIC:    All flags = 0 (simple NES game, no mapper tricks)
;   ENHANCED: STATUS_BAR = 1 (Kirby-style fixed HUD)
;   ADVANCED: STATUS_BAR + CHR_ANIMATION (Recca-style animated tiles)
;   FULL:     All flags = 1 (Batman/Recca/Kirby full feature set)
; =============================================================================

; Status bar IRQ - Freezes bottom 40 pixels (requires MMC3 IRQ)
; Games: Kirby's Adventure, Batman, most MMC3 games with HUD
.define FEATURE_STATUS_BAR_IRQ  1

; CHR bank animation - Swaps CHR banks for animated background tiles
; Games: Recca, Crisis Force (animated fire/water/energy effects)
; REQUIRES: Multiple CHR banks with animation frames in ROM
.define FEATURE_CHR_ANIMATION   0     ; Disabled - need animation CHR data

; Parallax scrolling - Background scrolls slower than foreground
; Games: Kirby's Adventure, Ninja Gaiden 2
.define FEATURE_PARALLAX        1

; Mid-frame CHR swap - Different tiles for status bar vs playfield
; Games: Batman (Sunsoft), some text-heavy RPGs
; REQUIRES: Separate CHR bank for status bar graphics
.define FEATURE_STATUS_CHR_SWAP 0     ; Disabled - need status bar CHR data

; Multi-split IRQ - Multiple screen splits per frame (advanced parallax)
; Games: Ninja Gaiden 2 (train stage), some demos
; REQUIRES: Careful timing, may cause visual glitches
.define FEATURE_MULTI_SPLIT_IRQ 0     ; Disabled - complex, needs tuning

; =============================================================================

.include "nes.inc"

; MMC3 registers are defined in nes.inc:
; MMC3_BANK_SELECT = $8000
; MMC3_BANK_DATA   = $8001
; MMC3_MIRRORING   = $A000
; MMC3_SRAM_EN     = $A001

; Export entry points
.export Reset
.export NMI
.export IRQ

; Import assets
.import background_nametable


; =============================================================================
; Constants
; =============================================================================

; Screen boundaries
SCREEN_LEFT     = 8
SCREEN_RIGHT    = 232       ; 256 - 24 (sprite width safety)
SCREEN_TOP      = 16
SCREEN_BOTTOM   = 208       ; 240 - 32 (sprite height safety)

; Speeds (pixels per frame)
PLAYER_SPEED    = 2
ENEMY_SPEED     = 1
BULLET_SPEED    = 4

; Timing
FIRE_COOLDOWN   = 15        ; Frames between shots
MAX_BULLETS     = 8

; Sprite tiles (in CHR ROM)
; 32x32 sprites = 16 tiles each ($00-$0F for player)
TILE_PLAYER_START = $00
TILE_ENEMY_START  = $10
TILE_BULLET_START = $20 ; Using center 2x2 of the 32x32 asset

; Palettes
PAL_PLAYER      = 0
PAL_ENEMY       = 1
PAL_BULLET      = 2

; =============================================================================
; Advanced MMC3 Constants (Recca/Batman/Kirby style)
; =============================================================================

; Screen split positions (scanline numbers)
; NES visible area: 240 scanlines (0-239)
; Status bar: bottom 40 pixels = scanlines 200-239
SPLIT_STATUS_BAR    = 199       ; IRQ fires after this many scanlines
PLAYFIELD_HEIGHT    = 200       ; Playable area height in pixels

; IRQ state machine
IRQ_STATE_IDLE      = 0
IRQ_STATE_PLAYFIELD = 1
IRQ_STATE_STATUS    = 2

; CHR Animation (Recca-style animated tiles)
; We can swap 1KB CHR banks mid-frame for animation
CHR_ANIM_SPEED      = 8         ; Frames between animation steps
CHR_ANIM_FRAMES     = 4         ; Number of animation frames

; Parallax scroll divisors (fake parallax via different scroll speeds)
PARALLAX_BG_SPEED   = 1         ; Background scrolls at 1/2 player speed
PARALLAX_FG_SPEED   = 2         ; Foreground scrolls at full speed

; =============================================================================
; Zero Page Variables
; =============================================================================
.segment "ZEROPAGE"

; System state
nmi_flag:       .res 1          ; Set by NMI handler

; Input state (read locally, no external dependency)
buttons:        .res 1          ; Current button state
buttons_old:    .res 1          ; Previous frame

; Player state
player_x:       .res 1
player_y:       .res 1

; Enemy state
enemy_x:        .res 1
enemy_y:        .res 1

; Weapon state
fire_timer:     .res 1

; Bullet pool (8 bullets, 4 bytes each: x, y, active, velocity_x)
bullets:        .res MAX_BULLETS * 4

; Temp variables
temp1:          .res 1
temp2:          .res 1
scroll_x:       .res 1
scroll_y:       .res 1

; =============================================================================
; Advanced MMC3 Variables (Recca/Batman/Kirby style)
; =============================================================================

; IRQ state machine
irq_state:      .res 1          ; Current IRQ state (what split we're at)

; CHR Animation state (Recca-style)
chr_anim_timer: .res 1          ; Countdown timer for animation
chr_anim_frame: .res 1          ; Current animation frame (0-3)

; Parallax scrolling (Kirby-style)
parallax_x:     .res 1          ; Slow background scroll position
scroll_x_sub:   .res 1          ; Sub-pixel scroll accumulator

; Status bar data
status_score_lo:.res 1          ; Score low byte
status_score_hi:.res 1          ; Score high byte
status_lives:   .res 1          ; Player lives
status_level:   .res 1          ; Current level

; Frame counter for timing
frame_count:    .res 1          ; Increments each frame

; =============================================================================
; Main Code
; =============================================================================
.segment "CODE"

; -----------------------------------------------------------------------------
; Reset - NES Initialization and Main Loop
; -----------------------------------------------------------------------------
.proc Reset
    sei                     ; Disable interrupts
    cld                     ; Disable decimal mode
    ldx #$FF
    txs                     ; Initialize stack

    ; Disable rendering and NMI during init
    lda #0
    sta $2000               ; PPU_CTRL
    sta $2001               ; PPU_MASK

    ; Wait for first vblank
:   bit $2002
    bpl :-

    ; Clear RAM ($0000-$07FF)
    lda #0
    ldx #0
@clear_ram:
    sta $0000, x
    sta $0100, x
    sta $0200, x
    sta $0300, x
    sta $0400, x
    sta $0500, x
    sta $0600, x
    sta $0700, x
    inx
    bne @clear_ram

    ; Wait for second vblank (PPU fully ready)
:   bit $2002
    bpl :-

    ; Initialize MMC3 mapper
    jsr mmc3_init

    ; Initialize game state
    jsr game_init

    ; Load palettes
    jsr load_palettes

    ; Draw Background
    jsr draw_background



    ; Enable NMI - Pattern table configuration for MMC3 IRQ
    ; =========================================================================
    ; MMC3 scanline IRQ requires A12 to toggle during rendering.
    ; For IRQ: Background at $0xxx, Sprites at $1xxx
    ; =========================================================================
    ; Bit 7: NMI enable (1)
    ; Bit 5: Sprite size (0 = 8x8)
    ; Bit 4: BG pattern table (0 = $0000)
    ; Bit 3: Sprite pattern table (1 = $1000)
    lda #%10001000
    sta $2000

    ; Enable rendering
    ; Bit 4: Show sprites
    ; Bit 3: Show background
    ; Bit 2: Show sprites in leftmost 8 pixels
    ; Bit 1: Show BG in leftmost 8 pixels
    lda #%00011110
    sta $2001

    ; Enable IRQ for MMC3 scanline counter (status bar split)
    cli

    ; Main loop
@main_loop:
    ; Wait for NMI
    lda #0
    sta nmi_flag
@wait_nmi:
    lda nmi_flag
    beq @wait_nmi

    ; Read controller
    jsr read_controller

    ; Update game logic
    jsr update_player
    jsr update_enemy
    jsr update_weapon
    jsr update_bullets

    ; ==========================================================================
    ; Advanced MMC3 Updates (Recca/Batman/Kirby style)
    ; Only run features that are enabled via feature flags
    ; ==========================================================================

    ; Update frame counter (always needed for timing)
    inc frame_count

.if FEATURE_CHR_ANIMATION = 1
    ; Update CHR animation (Recca-style animated tiles)
    jsr update_chr_animation
.endif

.if FEATURE_PARALLAX = 1
    ; Update parallax scrolling (Kirby-style multi-layer)
    jsr update_parallax
.else
    ; Simple scroll without parallax
    inc scroll_x
.endif

    ; Render sprites to OAM shadow
    jsr render_sprites

    jmp @main_loop
.endproc

; -----------------------------------------------------------------------------
; NMI Handler - Called every VBlank
; -----------------------------------------------------------------------------
; Advanced MMC3 Features (Recca/Batman/Kirby style):
; - Sets up IRQ for status bar split at scanline 200
; - Applies CHR bank animation (swaps animated tile banks)
; - Sets up parallax scroll for main playfield
; -----------------------------------------------------------------------------
.proc NMI
    pha
    txa
    pha
    tya
    pha

    ; ==========================================================================
    ; OAM DMA - Transfer sprite data from $0200-$02FF to PPU OAM
    ; Must happen during VBlank (we're in NMI, so this is safe)
    ; Takes 513-514 CPU cycles - do this first while we have time
    ; ==========================================================================
    lda #0
    sta $2003               ; Set OAM address to 0
    lda #$02                ; High byte of $0200
    sta $4014               ; Trigger DMA

    ; ==========================================================================
    ; CHR Bank Animation (Recca-style) - FEATURE FLAG CONTROLLED
    ; Swap background CHR bank based on animation frame
    ; This creates animated background tiles like Recca's fire effects
    ; ==========================================================================
.if FEATURE_CHR_ANIMATION = 1
    ; Bank R2 controls PPU $0000-$03FF (first 1KB of BG tiles)
    ; We cycle through banks 8, 12, 16, 20 for 4 frames of animation
    lda #$82                ; Select register R2 (with A12 inversion)
    sta MMC3_BANK_SELECT
    lda chr_anim_frame      ; Get current frame (0-3)
    asl a                   ; Multiply by 4 (each frame uses 4 1KB banks apart)
    asl a
    clc
    adc #$08                ; Add base bank (8)
    sta MMC3_BANK_DATA      ; Set CHR bank for animated tiles
.endif

    ; ==========================================================================
    ; PPU Scroll Setup (Kirby-style parallax)
    ; Main playfield uses parallax_x for slow background scroll
    ; ==========================================================================
    bit $2002               ; Reset PPU address latch

    ; Set scroll for main playfield (top 200 scanlines)
    ; Use parallax_x for background scroll position
    lda scroll_x
    sta $2005               ; X scroll
    lda #0                  ; Y scroll = 0 for horizontal scroller
    sta $2005

    ; ==========================================================================
    ; MMC3 Scanline IRQ Setup (Batman/Kirby style status bar)
    ; Technical: MMC3 counts A12 rising edges during rendering
    ; A12 rises when PPU fetches from $1xxx pattern table
    ; We split at scanline 200 to freeze the bottom 40 pixels
    ; ==========================================================================
.if FEATURE_STATUS_BAR_IRQ = 1
    ; Set IRQ state - we're starting a new frame
    lda #IRQ_STATE_PLAYFIELD
    sta irq_state

    ; Disable and acknowledge any pending IRQ
    lda #0
    sta $E000               ; Write to $E000 to disable & ack

    ; Set scanline counter: fire after 199 scanlines (before line 200)
    ; This leaves 40 scanlines (200-239) for the frozen status bar
    lda #SPLIT_STATUS_BAR
    sta $C000               ; Set IRQ latch value
    sta $C001               ; Reload counter from latch

    ; Enable IRQ
    sta $E001               ; Write to $E001 to enable
.endif

    ; Signal main loop that VBlank processing is done
    lda #1
    sta nmi_flag

    pla
    tay
    pla
    tax
    pla
    rti
.endproc

; -----------------------------------------------------------------------------
; IRQ Handler - MMC3 Scanline IRQ for Status Bar
; -----------------------------------------------------------------------------
; Advanced Features (Recca/Batman/Kirby style):
; - Fires at scanline 200 (after 199 A12 rises)
; - Freezes scroll for status bar (no scrolling in bottom 40px)
; - Can optionally swap CHR banks for status bar graphics
; - Uses state machine for potential multi-split (future: parallax layers)
;
; Technical Notes (from nesdev.org):
; - IRQ fires 1-2 scanlines after counter reaches 0 (emulator variance)
; - Must acknowledge IRQ by writing to $E000 ASAP
; - $2005/$2006 writes must happen during HBlank for clean split
; - For perfect timing, fire IRQ 1 scanline early and spin
; -----------------------------------------------------------------------------
.proc IRQ
    pha
    txa
    pha

.if FEATURE_STATUS_BAR_IRQ = 1
    ; ==========================================================================
    ; Acknowledge MMC3 IRQ immediately (critical for timing)
    ; Must write to $E000 before doing anything else
    ; ==========================================================================
    lda #0
    sta $E000               ; Disable & acknowledge IRQ

    ; ==========================================================================
    ; Check IRQ state and handle accordingly
    ; ==========================================================================
    lda irq_state
    cmp #IRQ_STATE_PLAYFIELD
    bne @done               ; Unexpected state, bail out

    ; ==========================================================================
    ; Status Bar Split (Kirby/Batman style)
    ; Reset scroll to (0, 0) so status bar is static
    ; Per NES technical docs: reset latch before writing $2005
    ; ==========================================================================

    ; Wait a few cycles to ensure we're in HBlank
    ; This prevents mid-tile scroll changes that cause glitches
    ldx #3
@wait_hblank:
    dex
    bne @wait_hblank

    ; Reset PPU address latch
    bit $2002

    ; Set scroll to (0, 0) for frozen status bar
    lda #0
    sta $2005               ; X scroll = 0
    sta $2005               ; Y scroll = 0

    ; --------------------------------------------------------------------------
    ; Optional: Swap CHR bank for status bar graphics (Batman-style)
    ; --------------------------------------------------------------------------
.if FEATURE_STATUS_CHR_SWAP = 1
    lda #$82                ; Register R2 (1KB at $0000)
    sta MMC3_BANK_SELECT
    lda #$18                ; Status bar tiles in bank 24
    sta MMC3_BANK_DATA
.endif

    ; Update state - we're now in status bar region
    lda #IRQ_STATE_STATUS
    sta irq_state

@done:
.endif ; FEATURE_STATUS_BAR_IRQ

    pla
    tax
    pla
    rti
.endproc

; -----------------------------------------------------------------------------
; MMC3 Init - Recca-style for MMC3 scanline IRQ
; -----------------------------------------------------------------------------
; With PPUCTRL: BG at $0xxx, Sprites at $1xxx
; We need: Background CHR at PPU $0000, Sprites CHR at PPU $1000
;
; Using A12 inversion (bit 7 = 1):
;   R0, R1: 2KB banks at PPU $1000-$1FFF (sprites)
;   R2-R5: 1KB banks at PPU $0000-$0FFF (background)
; -----------------------------------------------------------------------------
.proc mmc3_init
    ; === CHR Bank Setup (bit 7 = 1 for A12 inversion) ===

    ; R0: 2KB at PPU $1000-$17FF = Sprites (CHR bank 0)
    lda #$80
    sta MMC3_BANK_SELECT
    lda #$00
    sta MMC3_BANK_DATA

    ; R1: 2KB at PPU $1800-$1FFF = Sprites (CHR bank 2)
    lda #$81
    sta MMC3_BANK_SELECT
    lda #$02
    sta MMC3_BANK_DATA

    ; R2: 1KB at PPU $0000-$03FF = Background (CHR bank 8)
    ; R2: 1KB at PPU $0000-$03FF = Background (CHR bank 0)
    lda #$82
    sta MMC3_BANK_SELECT
    lda #$00
    sta MMC3_BANK_DATA

    ; R3: 1KB at PPU $0400-$07FF = Background (CHR bank 1)
    lda #$83
    sta MMC3_BANK_SELECT
    lda #$01
    sta MMC3_BANK_DATA

    ; R4: 1KB at PPU $0800-$0BFF = Background (CHR bank 2)
    lda #$84
    sta MMC3_BANK_SELECT
    lda #$02
    sta MMC3_BANK_DATA

    ; R5: 1KB at PPU $0C00-$0FFF = Background (CHR bank 3)
    lda #$85
    sta MMC3_BANK_SELECT
    lda #$03
    sta MMC3_BANK_DATA

    ; === PRG Bank Setup ===
    lda #$86
    sta MMC3_BANK_SELECT
    lda #$00
    sta MMC3_BANK_DATA

    lda #$87
    sta MMC3_BANK_SELECT
    lda #$01
    sta MMC3_BANK_DATA

    ; Horizontal mirroring for side-scrollers
    lda #$01
    sta MMC3_MIRRORING

    ; Enable PRG RAM
    lda #$80
    sta MMC3_SRAM_EN

    ; Disable IRQ initially
    lda #$00
    sta $E000

    rts
.endproc

; -----------------------------------------------------------------------------
; Game Init
; -----------------------------------------------------------------------------
.proc game_init
    ; Player at center-left
    lda #64
    sta player_x
    lda #112
    sta player_y

    ; Enemy at center-right
    lda #192
    sta enemy_x
    lda #112
    sta enemy_y

    ; Clear weapon timer
    lda #0
    sta fire_timer

    ; Clear bullets
    ldx #0
    lda #0
@clear_bullets:
    sta bullets, x
    inx
    cpx #MAX_BULLETS * 4
    bne @clear_bullets

    ; ==========================================================================
    ; Initialize Advanced MMC3 State (Recca/Batman/Kirby style)
    ; ==========================================================================

    ; IRQ state machine - start in idle
    lda #IRQ_STATE_IDLE
    sta irq_state

    ; CHR animation - start at frame 0, timer loaded
    lda #0
    sta chr_anim_frame
    lda #CHR_ANIM_SPEED
    sta chr_anim_timer

    ; Parallax scroll
    lda #0
    sta parallax_x
    sta scroll_x_sub

    ; Status bar initial values
    lda #0
    sta status_score_lo
    sta status_score_hi
    lda #3                      ; Start with 3 lives
    sta status_lives
    lda #1                      ; Level 1
    sta status_level

    ; Frame counter
    lda #0
    sta frame_count

    rts
.endproc

; -----------------------------------------------------------------------------
; Read Controller - Simple polling
; -----------------------------------------------------------------------------
.proc read_controller
    ; Save old state
    lda buttons
    sta buttons_old

    ; Strobe
    lda #1
    sta $4016
    lda #0
    sta $4016

    ; Read 8 buttons (A, B, Select, Start, Up, Down, Left, Right)
    ldx #8
    lda #0
@loop:
    pha
    lda $4016
    and #$03            ; Handle Famicom expansion
    cmp #1
    pla
    ror a               ; Rotate carry into result
    dex
    bne @loop

    ; A now has buttons in NES hardware order: A B Sel Sta U D L R
    ; Store directly (we'll use NES order for simplicity)
    sta buttons

    rts
.endproc

; -----------------------------------------------------------------------------
; Update Player - D-pad movement
; -----------------------------------------------------------------------------
; Button bits after read_controller (ROR order):
;   Bit 7: Right
;   Bit 6: Left
;   Bit 5: Down
;   Bit 4: Up
;   Bit 3: Start
;   Bit 2: Select
;   Bit 1: B
;   Bit 0: A
; -----------------------------------------------------------------------------
.proc update_player
    ; Check UP (bit 4)
    lda buttons
    and #%00010000
    beq @not_up
    lda player_y
    sec
    sbc #PLAYER_SPEED
    cmp #SCREEN_TOP
    bcs @store_y_up
    lda #SCREEN_TOP
@store_y_up:
    sta player_y
@not_up:

    ; Check DOWN (bit 5)
    lda buttons
    and #%00100000
    beq @not_down
    lda player_y
    clc
    adc #PLAYER_SPEED
    cmp #SCREEN_BOTTOM
    bcc @store_y_down
    lda #SCREEN_BOTTOM
@store_y_down:
    sta player_y
@not_down:

    ; Check LEFT (bit 6)
    lda buttons
    and #%01000000
    beq @not_left
    lda player_x
    sec
    sbc #PLAYER_SPEED
    cmp #SCREEN_LEFT
    bcs @store_x_left
    lda #SCREEN_LEFT
@store_x_left:
    sta player_x
@not_left:

    ; Check RIGHT (bit 7)
    lda buttons
    and #%10000000
    beq @not_right
    lda player_x
    clc
    adc #PLAYER_SPEED
    cmp #SCREEN_RIGHT
    bcc @store_x_right
    lda #SCREEN_RIGHT
@store_x_right:
    sta player_x
@not_right:

    rts
.endproc

; -----------------------------------------------------------------------------
; Update Enemy - Chase AI
; -----------------------------------------------------------------------------
.proc update_enemy
    ; Move toward player X
    lda enemy_x
    cmp player_x
    beq @check_y
    bcs @move_left
    ; Move right
    clc
    adc #ENEMY_SPEED
    sta enemy_x
    jmp @check_y
@move_left:
    sec
    sbc #ENEMY_SPEED
    sta enemy_x

@check_y:
    ; Move toward player Y
    lda enemy_y
    cmp player_y
    beq @done
    bcs @move_up
    ; Move down
    clc
    adc #ENEMY_SPEED
    sta enemy_y
    jmp @done
@move_up:
    sec
    sbc #ENEMY_SPEED
    sta enemy_y

@done:
    rts
.endproc

; -----------------------------------------------------------------------------
; Update Weapon - Auto-fire
; -----------------------------------------------------------------------------
.proc update_weapon
    ; Decrement timer
    lda fire_timer
    beq @can_fire
    dec fire_timer
    rts

@can_fire:
    ; Reset timer
    lda #FIRE_COOLDOWN
    sta fire_timer

    ; Find inactive bullet
    ldx #0
@find_slot:
    lda bullets+2, x     ; Active flag
    beq @spawn
    txa
    clc
    adc #4
    tax
    cpx #MAX_BULLETS * 4
    bne @find_slot
    rts                  ; No slots

@spawn:
    lda player_x
    clc
    adc #16
    sta bullets, x       ; X

    lda player_y
    clc
    adc #4
    sta bullets+1, x     ; Y

    lda #1
    sta bullets+2, x     ; Active

    lda #BULLET_SPEED
    sta bullets+3, x     ; Velocity

    rts
.endproc

; -----------------------------------------------------------------------------
; Update Bullets
; -----------------------------------------------------------------------------
.proc update_bullets
    ldx #0

@loop:
    lda bullets+2, x     ; Active?
    beq @next

    ; Move bullet
    lda bullets, x
    clc
    adc bullets+3, x
    sta bullets, x

    ; Off screen?
    cmp #250
    bcs @deactivate
    jmp @next

@deactivate:
    lda #0
    sta bullets+2, x

@next:
    txa
    clc
    adc #4
    tax
    cpx #MAX_BULLETS * 4
    bne @loop

    rts
.endproc

; =============================================================================
; Advanced MMC3 Update Routines (Recca/Batman/Kirby style)
; =============================================================================

; -----------------------------------------------------------------------------
; Update CHR Animation (Recca-style)
; -----------------------------------------------------------------------------
; Cycles through 4 animation frames for animated background tiles
; Timer-based to control animation speed independently of game logic
; Similar to Recca's flame effects and Kirby's water animations
; -----------------------------------------------------------------------------
.proc update_chr_animation
    ; Decrement timer
    dec chr_anim_timer
    bne @done               ; Timer not expired, nothing to do

    ; Timer expired - advance to next frame
    lda #CHR_ANIM_SPEED
    sta chr_anim_timer      ; Reset timer

    ; Advance frame (0 -> 1 -> 2 -> 3 -> 0)
    inc chr_anim_frame
    lda chr_anim_frame
    cmp #CHR_ANIM_FRAMES
    bcc @done               ; Frame < 4, we're good

    ; Wrap to frame 0
    lda #0
    sta chr_anim_frame

@done:
    rts
.endproc

; -----------------------------------------------------------------------------
; Update Parallax Scrolling (Kirby-style)
; -----------------------------------------------------------------------------
; Creates fake parallax by scrolling background slower than foreground
; Uses sub-pixel accumulator for smooth fractional scrolling
; Similar to Kirby's Adventure multi-layer backgrounds
; -----------------------------------------------------------------------------
.proc update_parallax
    ; Main scroll increments every frame (foreground speed)
    inc scroll_x

    ; Parallax background scrolls at half speed
    ; Use sub-pixel accumulator: add 1 every 2 frames
    inc scroll_x_sub
    lda scroll_x_sub
    cmp #PARALLAX_FG_SPEED  ; Every 2 frames...
    bcc @done

    ; Reset sub-pixel counter and increment parallax position
    lda #0
    sta scroll_x_sub
    inc parallax_x

@done:
    rts
.endproc

; -----------------------------------------------------------------------------
; Update Status Bar (Kirby-style)
; -----------------------------------------------------------------------------
; Updates the frozen status bar at bottom of screen
; This is called during VBlank to update VRAM for status display
; For now just placeholder - actual rendering would update nametable
; -----------------------------------------------------------------------------
.proc update_status_bar
    ; Score display would go here
    ; Lives display would go here
    ; Level indicator would go here

    ; Placeholder: increment score every frame for demo
    inc status_score_lo
    bne @done
    inc status_score_hi

@done:
    rts
.endproc

; -----------------------------------------------------------------------------
; Render Sprites
; -----------------------------------------------------------------------------
.proc render_sprites
    ; Clear OAM
    ldx #0
    lda #$FF
@clear:
    sta $0200, x
    inx
    bne @clear

    ldy #0               ; OAM index

    ; =========================================================================
    ; Player (32x32 Metasprite - 16 sprites)
    ; =========================================================================
    ; We will use a macro or just block copy for clarity in this demo
    ; Layout:
    ; 00 01 02 03
    ; 04 05 06 07
    ; 08 09 0A 0B
    ; 0C 0D 0E 0F
    
    ; Row 0
    jsr draw_player_row_0
    ; Row 1
    jsr draw_player_row_1
    ; Row 2
    jsr draw_player_row_2
    ; Row 3
    jsr draw_player_row_3

    ; =========================================================================
    ; Enemy (32x32 Metasprite - 16 sprites)
    ; =========================================================================
    ; Reusing similar logic but with Enemy coordinates and separate Tile Constants
    
    ; Row 0
    jsr draw_enemy_row_0
    ; Row 1
    jsr draw_enemy_row_1
    ; Row 2
    jsr draw_enemy_row_2
    ; Row 3
    jsr draw_enemy_row_3

    ; =========================================================================
    ; Bullets (16x16 Center Cut - 4 sprites each)
    ; =========================================================================
    ; Tiles used: 05, 06, 09, 0A (Center of 4x4) relative to TILE_BULLET_START
    ldx #0
@bullet_loop:
    lda bullets+2, x     ; Active?
    beq @bullet_next

    ; Bullet TL (Offset 5)
    lda bullets+1, x     ; Y
    clc
    adc #8               ; Center Offset Y
    sta $0200, y
    lda #TILE_BULLET_START + $05
    sta $0201, y
    lda #PAL_BULLET
    sta $0202, y
    lda bullets, x       ; X
    clc
    adc #8               ; Center Offset X
    sta $0203, y
    iny
    iny
    iny
    iny

    ; Bullet TR (Offset 6)
    lda bullets+1, x
    clc
    adc #8
    sta $0200, y
    lda #TILE_BULLET_START + $06
    sta $0201, y
    lda #PAL_BULLET
    sta $0202, y
    lda bullets, x
    clc
    adc #16              ; X+8
    sta $0203, y
    iny
    iny
    iny
    iny

    ; Bullet BL (Offset 9)
    lda bullets+1, x
    clc
    adc #16              ; Y+8
    sta $0200, y
    lda #TILE_BULLET_START + $09
    sta $0201, y
    lda #PAL_BULLET
    sta $0202, y
    lda bullets, x
    clc
    adc #8
    sta $0203, y
    iny
    iny
    iny
    iny

    ; Bullet BR (Offset 10)
    lda bullets+1, x
    clc
    adc #16
    sta $0200, y
    lda #TILE_BULLET_START + $0A
    sta $0201, y
    lda #PAL_BULLET
    sta $0202, y
    lda bullets, x
    clc
    adc #16
    sta $0203, y
    iny
    iny
    iny
    iny

@bullet_next:
    txa
    clc
    adc #4
    tax
    cpx #MAX_BULLETS * 4
    beq @bullets_done
    jmp @bullet_loop
@bullets_done:

    rts
.endproc

; =============================================================================
; Helper Drawing Routines (Unrolled Rows)
; =============================================================================

.proc draw_player_row_0
    ; Sprite 0 (0,0)
    lda player_y
    sta $0200, y
    lda #TILE_PLAYER_START + $00
    sta $0201, y
    lda #PAL_PLAYER
    sta $0202, y
    lda player_x
    sta $0203, y
    iny
    iny
    iny
    iny
    ; Sprite 1 (8,0)
    lda player_y
    sta $0200, y
    lda #TILE_PLAYER_START + $01
    sta $0201, y
    lda #PAL_PLAYER
    sta $0202, y
    lda player_x
    clc
    adc #8
    sta $0203, y
    iny
    iny
    iny
    iny
    ; Sprite 2 (16,0)
    lda player_y
    sta $0200, y
    lda #TILE_PLAYER_START + $02
    sta $0201, y
    lda #PAL_PLAYER
    sta $0202, y
    lda player_x
    clc
    adc #16
    sta $0203, y
    iny
    iny
    iny
    iny
    ; Sprite 3 (24,0)
    lda player_y
    sta $0200, y
    lda #TILE_PLAYER_START + $03
    sta $0201, y
    lda #PAL_PLAYER
    sta $0202, y
    lda player_x
    clc
    adc #24
    sta $0203, y
    iny
    iny
    iny
    iny
    rts
.endproc

.proc draw_player_row_1
    ; Sprite 4 (0,8)
    lda player_y
    clc
    adc #8
    sta $0200, y
    lda #TILE_PLAYER_START + $04
    sta $0201, y
    lda #PAL_PLAYER
    sta $0202, y
    lda player_x
    sta $0203, y
    iny
    iny
    iny
    iny
    ; Sprite 5 (8,8)
    lda player_y
    clc
    adc #8
    sta $0200, y
    lda #TILE_PLAYER_START + $05
    sta $0201, y
    lda #PAL_PLAYER
    sta $0202, y
    lda player_x
    clc
    adc #8
    sta $0203, y
    iny
    iny
    iny
    iny
    ; Sprite 6 (16,8)
    lda player_y
    clc
    adc #8
    sta $0200, y
    lda #TILE_PLAYER_START + $06
    sta $0201, y
    lda #PAL_PLAYER
    sta $0202, y
    lda player_x
    clc
    adc #16
    sta $0203, y
    iny
    iny
    iny
    iny
    ; Sprite 7 (24,8)
    lda player_y
    clc
    adc #8
    sta $0200, y
    lda #TILE_PLAYER_START + $07
    sta $0201, y
    lda #PAL_PLAYER
    sta $0202, y
    lda player_x
    clc
    adc #24
    sta $0203, y
    iny
    iny
    iny
    iny
    rts
.endproc

.proc draw_player_row_2
    ; Sprite 8 (0,16)
    lda player_y
    clc
    adc #16
    sta $0200, y
    lda #TILE_PLAYER_START + $08
    sta $0201, y
    lda #PAL_PLAYER
    sta $0202, y
    lda player_x
    sta $0203, y
    iny
    iny
    iny
    iny
    ; Sprite 9 (8,16)
    lda player_y
    clc
    adc #16
    sta $0200, y
    lda #TILE_PLAYER_START + $09
    sta $0201, y
    lda #PAL_PLAYER
    sta $0202, y
    lda player_x
    clc
    adc #8
    sta $0203, y
    iny
    iny
    iny
    iny
    ; Sprite 10 (16,16)
    lda player_y
    clc
    adc #16
    sta $0200, y
    lda #TILE_PLAYER_START + $0A
    sta $0201, y
    lda #PAL_PLAYER
    sta $0202, y
    lda player_x
    clc
    adc #16
    sta $0203, y
    iny
    iny
    iny
    iny
    ; Sprite 11 (24,16)
    lda player_y
    clc
    adc #16
    sta $0200, y
    lda #TILE_PLAYER_START + $0B
    sta $0201, y
    lda #PAL_PLAYER
    sta $0202, y
    lda player_x
    clc
    adc #24
    sta $0203, y
    iny
    iny
    iny
    iny
    rts
.endproc

.proc draw_player_row_3
    ; Sprite 12 (0,24)
    lda player_y
    clc
    adc #24
    sta $0200, y
    lda #TILE_PLAYER_START + $0C
    sta $0201, y
    lda #PAL_PLAYER
    sta $0202, y
    lda player_x
    sta $0203, y
    iny
    iny
    iny
    iny
    ; Sprite 13 (8,24)
    lda player_y
    clc
    adc #24
    sta $0200, y
    lda #TILE_PLAYER_START + $0D
    sta $0201, y
    lda #PAL_PLAYER
    sta $0202, y
    lda player_x
    clc
    adc #8
    sta $0203, y
    iny
    iny
    iny
    iny
    ; Sprite 14 (16,24)
    lda player_y
    clc
    adc #24
    sta $0200, y
    lda #TILE_PLAYER_START + $0E
    sta $0201, y
    lda #PAL_PLAYER
    sta $0202, y
    lda player_x
    clc
    adc #16
    sta $0203, y
    iny
    iny
    iny
    iny
    ; Sprite 15 (24,24)
    lda player_y
    clc
    adc #24
    sta $0200, y
    lda #TILE_PLAYER_START + $0F
    sta $0201, y
    lda #PAL_PLAYER
    sta $0202, y
    lda player_x
    clc
    adc #24
    sta $0203, y
    iny
    iny
    iny
    iny
    rts
.endproc

.proc draw_enemy_row_0
    ; Sprite 0 (0,0) - Enemy
    lda enemy_y
    sta $0200, y
    lda #TILE_ENEMY_START + $00
    sta $0201, y
    lda #PAL_ENEMY
    sta $0202, y
    lda enemy_x
    sta $0203, y
    iny
    iny
    iny
    iny
    ; Sprite 1 (8,0)
    lda enemy_y
    sta $0200, y
    lda #TILE_ENEMY_START + $01
    sta $0201, y
    lda #PAL_ENEMY
    sta $0202, y
    lda enemy_x
    clc
    adc #8
    sta $0203, y
    iny
    iny
    iny
    iny
    ; Sprite 2 (16,0)
    lda enemy_y
    sta $0200, y
    lda #TILE_ENEMY_START + $02
    sta $0201, y
    lda #PAL_ENEMY
    sta $0202, y
    lda enemy_x
    clc
    adc #16
    sta $0203, y
    iny
    iny
    iny
    iny
    ; Sprite 3 (24,0)
    lda enemy_y
    sta $0200, y
    lda #TILE_ENEMY_START + $03
    sta $0201, y
    lda #PAL_ENEMY
    sta $0202, y
    lda enemy_x
    clc
    adc #24
    sta $0203, y
    iny
    iny
    iny
    iny
    rts
.endproc

.proc draw_enemy_row_1
    ; Sprite 4 (0,8)
    lda enemy_y
    clc
    adc #8
    sta $0200, y
    lda #TILE_ENEMY_START + $04
    sta $0201, y
    lda #PAL_ENEMY
    sta $0202, y
    lda enemy_x
    sta $0203, y
    iny
    iny
    iny
    iny
    ; Sprite 5 (8,8)
    lda enemy_y
    clc
    adc #8
    sta $0200, y
    lda #TILE_ENEMY_START + $05
    sta $0201, y
    lda #PAL_ENEMY
    sta $0202, y
    lda enemy_x
    clc
    adc #8
    sta $0203, y
    iny
    iny
    iny
    iny
    ; Sprite 6 (16,8)
    lda enemy_y
    clc
    adc #8
    sta $0200, y
    lda #TILE_ENEMY_START + $06
    sta $0201, y
    lda #PAL_ENEMY
    sta $0202, y
    lda enemy_x
    clc
    adc #16
    sta $0203, y
    iny
    iny
    iny
    iny
    ; Sprite 7 (24,8)
    lda enemy_y
    clc
    adc #8
    sta $0200, y
    lda #TILE_ENEMY_START + $07
    sta $0201, y
    lda #PAL_ENEMY
    sta $0202, y
    lda enemy_x
    clc
    adc #24
    sta $0203, y
    iny
    iny
    iny
    iny
    rts
.endproc

.proc draw_enemy_row_2
    ; Sprite 8 (0,16)
    lda enemy_y
    clc
    adc #16
    sta $0200, y
    lda #TILE_ENEMY_START + $08
    sta $0201, y
    lda #PAL_ENEMY
    sta $0202, y
    lda enemy_x
    sta $0203, y
    iny
    iny
    iny
    iny
    ; Sprite 9 (8,16)
    lda enemy_y
    clc
    adc #16
    sta $0200, y
    lda #TILE_ENEMY_START + $09
    sta $0201, y
    lda #PAL_ENEMY
    sta $0202, y
    lda enemy_x
    clc
    adc #8
    sta $0203, y
    iny
    iny
    iny
    iny
    ; Sprite 10 (16,16)
    lda enemy_y
    clc
    adc #16
    sta $0200, y
    lda #TILE_ENEMY_START + $0A
    sta $0201, y
    lda #PAL_ENEMY
    sta $0202, y
    lda enemy_x
    clc
    adc #16
    sta $0203, y
    iny
    iny
    iny
    iny
    ; Sprite 11 (24,16)
    lda enemy_y
    clc
    adc #16
    sta $0200, y
    lda #TILE_ENEMY_START + $0B
    sta $0201, y
    lda #PAL_ENEMY
    sta $0202, y
    lda enemy_x
    clc
    adc #24
    sta $0203, y
    iny
    iny
    iny
    iny
    rts
.endproc

.proc draw_enemy_row_3
    ; Sprite 12 (0,24)
    lda enemy_y
    clc
    adc #24
    sta $0200, y
    lda #TILE_ENEMY_START + $0C
    sta $0201, y
    lda #PAL_ENEMY
    sta $0202, y
    lda enemy_x
    sta $0203, y
    iny
    iny
    iny
    iny
    ; Sprite 13 (8,24)
    lda enemy_y
    clc
    adc #24
    sta $0200, y
    lda #TILE_ENEMY_START + $0D
    sta $0201, y
    lda #PAL_ENEMY
    sta $0202, y
    lda enemy_x
    clc
    adc #8
    sta $0203, y
    iny
    iny
    iny
    iny
    ; Sprite 14 (16,24)
    lda enemy_y
    clc
    adc #24
    sta $0200, y
    lda #TILE_ENEMY_START + $0E
    sta $0201, y
    lda #PAL_ENEMY
    sta $0202, y
    lda enemy_x
    clc
    adc #16
    sta $0203, y
    iny
    iny
    iny
    iny
    ; Sprite 15 (24,24)
    lda enemy_y
    clc
    adc #24
    sta $0200, y
    lda #TILE_ENEMY_START + $0F
    sta $0201, y
    lda #PAL_ENEMY
    sta $0202, y
    lda enemy_x
    clc
    adc #24
    sta $0203, y
    iny
    iny
    iny
    iny
    rts
.endproc

; -----------------------------------------------------------------------------
; Load Palettes
; -----------------------------------------------------------------------------
.proc load_palettes
    bit $2002            ; Reset latch

    lda #$3F
    sta $2006
    lda #$00
    sta $2006

    ldx #0
@loop:
    lda palette_data, x
    sta $2007
    inx
    cpx #32
    bne @loop

    rts
.endproc

; -----------------------------------------------------------------------------
; Draw Background
; -----------------------------------------------------------------------------
.proc draw_background
    ; Set PPU address to $2000 (Nametable 0)
    lda #$20
    sta $2006
    lda #$00
    sta $2006

    ; Load 1KB nametable
    lda #<background_nametable
    sta $00
    lda #>background_nametable
    sta $01

    ldx #4          ; 4 pages of 256 bytes = 1024 bytes
    ldy #0
@loop:
    lda ($00), y
    sta $2007
    iny
    bne @loop
    inc $01
    dex
    bne @loop

    rts
.endproc

; =============================================================================
; Data
; =============================================================================
; =============================================================================
; Assets (CHR data is usually in a separate bank or segment)
; =============================================================================
.segment "RODATA"

; =============================================================================
; Assets (Handled in graphics.asm)
; =============================================================================
; .segment "RODATA"

; Original assets
; background_nametable:
;     ; .incbin "assets/background.nam" ; Original placeholder
;     .incbin "../assets/bg_cyberpunk.nam" ; New optimized background

palette_data:
    ; Background palettes (AI-extracted from cyberpunk image)
    ; PAL 0: Main background - Black, Red, Orange, White
    .byte $0F, $16, $27, $30
    .byte $0F, $16, $27, $30
    .byte $0F, $16, $27, $30
    .byte $0F, $16, $27, $30  ; Alt: Red ramp (Corrected from $3026)
    .byte $0F, $0A, $1A, $2A  ; Alt: Green ramp

    ; Sprite palettes (AI-extracted to match CHR data)
    ; PAL 0: Player (Pink/Cyan/White)
    .byte $0F, $24, $2C, $30
    ; PAL 1 (sprites $10-$1F): Enemy - Black, Magenta, Cyan, White
    .byte $0F, $24, $2C, $30
    ; PAL 2 (sprites $20-$2F): Bullet - Black, Magenta, Cyan, White
    .byte $0F, $24, $2C, $30
    ; PAL 3: Pickups/Effects
    .byte $0F, $19, $29, $39

;.segment "CHR"
; CHR Bank 0: Background Tiles
;.incbin "../assets/bg_cyberpunk.chr"
; Fill remainder of 1KB if needed (not needed for full bank)

; CHR Bank 1: Sprites
;.incbin "../assets/sprites.chr"
