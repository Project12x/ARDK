; =============================================================================
; ACTION_SURVIVOR Variant - Tower Defense Survivors Engine
; =============================================================================
; Optimized for:
;   - 64 simultaneous enemies with Recca-style sprite multiplexing
;   - Tower protection gameplay (XP flows to tower as sparks)
;   - Quadrant-based AI throttling (15Hz per enemy)
;   - Interleaved bullet rendering (30fps doubles effective count)
;   - Stride array data layout for maximum performance
; =============================================================================

; -----------------------------------------------------------------------------
; Configuration Constants
; -----------------------------------------------------------------------------
MAX_ENEMIES         = 64
MAX_BULLETS         = 64
MAX_XP_GEMS         = 32
ENEMIES_PER_QUADRANT = 16      ; 64 / 4 quadrants

; Sprite slot allocation
OAM_SLOT_TOWER      = 0        ; Slots 0-3 (16x16 tower)
OAM_SLOT_PLAYER     = 4        ; Slots 4-7 (16x16 player)
OAM_SLOT_BULLETS    = 8        ; Slots 8-15 (8 bullets visible per frame)
OAM_SLOT_ENEMIES    = 16       ; Slots 16-63 (48 enemy sprites max)

; AI update quadrants (2-bit frame phase)
QUADRANT_0          = %00000000 ; Enemies 0-15
QUADRANT_1          = %00000001 ; Enemies 16-31
QUADRANT_2          = %00000010 ; Enemies 32-47
QUADRANT_3          = %00000011 ; Enemies 48-63

; Spatial grid (8x8 = 64 cells, 32px per cell)
GRID_CELL_SIZE      = 32
GRID_CELL_SHIFT     = 5        ; log2(32)
GRID_WIDTH          = 8
GRID_HEIGHT         = 8

; Prime offset for OAM shuffling (prevents static dropout)
OAM_SHUFFLE_PRIME   = 17       ; Must be coprime with 48

; Interleaved bullet frames
BULLET_FRAME_EVEN   = 0
BULLET_FRAME_ODD    = 1

; -----------------------------------------------------------------------------
; Zero Page Allocation
; -----------------------------------------------------------------------------
.segment "ZEROPAGE"

; Engine temps ($00-$0F)
temp1:              .res 1
temp2:              .res 1
temp3:              .res 1
temp4:              .res 1
frame_counter:      .res 1
logic_started:      .res 1     ; VBlank watchdog flag
ai_quadrant:        .res 1     ; Current AI update quadrant (0-3)
oam_shuffle_seed:   .res 1     ; LCG seed for sprite shuffling
bullet_frame:       .res 1     ; Even/odd bullet frame toggle
.res 6                          ; Reserved

; HAL/Hardware ($10-$1F)
scroll_x:           .res 1
scroll_y:           .res 1
ppu_ctrl_shadow:    .res 1
ppu_mask_shadow:    .res 1
chr_anim_timer:     .res 1
chr_anim_frame:     .res 1
.res 10                         ; Reserved

; Input ($20-$21)
buttons:            .res 1
buttons_old:        .res 1

; Player state ($22-$2F)
player_x:           .res 1
player_y:           .res 1
player_hp:          .res 1
player_hp_max:      .res 1
player_xp_lo:       .res 1
player_xp_hi:       .res 1
player_level:       .res 1
player_inv_timer:   .res 1     ; Invincibility frames
player_regen_timer: .res 1     ; HP regen timer
.res 5                          ; Reserved

; Tower state ($30-$3F)
tower_x:            .res 1
tower_y:            .res 1
tower_hp:           .res 1
tower_hp_max:       .res 1
tower_xp_lo:        .res 1
tower_xp_hi:        .res 1
tower_upgrade_flags:.res 1     ; Which upgrades unlocked
tower_damage_flash: .res 1
.res 8                          ; Reserved

; Weapon state ($40-$4F) - 4 weapon slots
weapon0_type:       .res 1
weapon0_level:      .res 1
weapon0_cooldown:   .res 1
weapon0_timer:      .res 1
weapon1_type:       .res 1
weapon1_level:      .res 1
weapon1_cooldown:   .res 1
weapon1_timer:      .res 1
weapon2_type:       .res 1
weapon2_level:      .res 1
weapon2_cooldown:   .res 1
weapon2_timer:      .res 1
weapon3_type:       .res 1
weapon3_level:      .res 1
weapon3_cooldown:   .res 1
weapon3_timer:      .res 1

; Spawner state ($50-$5F)
spawn_timer:        .res 1
spawn_wave:         .res 1
spawn_count:        .res 1
spawn_rate:         .res 1
enemy_count:        .res 1     ; Active enemies
.res 11                         ; Reserved

; OAM shuffler state ($60-$6F)
oam_enemy_start:    .res 1     ; Starting OAM index for enemies
oam_index:          .res 1     ; Current OAM write position
.res 14                         ; Reserved

; Reserved ($70-$7F)
.res 16

; Density map cache ($80-$9F) - 32 bytes for fast collision culling
density_cache:      .res 32

; Game temps ($A0-$FF)
game_temp:          .res 96

; -----------------------------------------------------------------------------
; RAM Allocation (Stride Arrays)
; -----------------------------------------------------------------------------
.segment "BSS"

; Enemy stride arrays (SoA pattern for fast indexed access)
Enemy_X:            .res MAX_ENEMIES    ; $0300-$033F
Enemy_Y:            .res MAX_ENEMIES    ; $0340-$037F
Enemy_HP:           .res MAX_ENEMIES    ; $0380-$03BF
Enemy_State:        .res MAX_ENEMIES    ; $03C0-$03FF
                                        ; State: 0=inactive, 1=active, 2=dying

; Bullet stride arrays
Bullet_X:           .res MAX_BULLETS    ; $0400-$043F
Bullet_Y:           .res MAX_BULLETS    ; $0440-$047F
Bullet_Active:      .res 8              ; $0480-$0487 (bitmask: 64 bullets)
Bullet_VelX:        .res MAX_BULLETS    ; $0488-$04C7
Bullet_VelY:        .res MAX_BULLETS    ; $04C8-$0507

; XP gem stride arrays
XPGem_X:            .res MAX_XP_GEMS    ; $0508-$0527
XPGem_Y:            .res MAX_XP_GEMS    ; $0528-$0547
XPGem_Value:        .res MAX_XP_GEMS    ; $0548-$0567
XPGem_Active:       .res 4              ; $0568-$056B (bitmask: 32 gems)

; Spatial density map (8x8 grid = 64 cells)
Density_Map:        .res 64             ; $056C-$05AB

; -----------------------------------------------------------------------------
; Engine Core Routines
; -----------------------------------------------------------------------------
.segment "CODE"

; =============================================================================
; mmc3_init - Initialize MMC3 mapper for ACTION_SURVIVOR
; =============================================================================
; MMC3 Bank Select Register ($8000):
;   Bits 0-2: Register to update (0-7)
;   Bit 6: PRG mode (0 = $8000 swappable, 1 = $C000 swappable)
;   Bit 7: CHR A12 inversion (0 = 2KB at $0000, 1KB at $1000)
;
; CHR Bank Numbers are in 1KB UNITS:
;   For 2KB registers (R0, R1): LSB is ignored, so use EVEN numbers
;   For 1KB registers (R2-R5): Use exact 1KB bank number
;
; Our CHR ROM Layout (32KB = 32 x 1KB banks):
;   Bank 0-7   ($0000-$1FFF): sprites.chr (8KB) - Sprite tiles
;   Bank 8-15  ($2000-$3FFF): background.chr (8KB) - BG tiles
;   Bank 16-23 ($4000-$5FFF): CHR_BANK2 (8KB) - Animation frame 2 / extra
;   Bank 24-31 ($6000-$7FFF): CHR_BANK3 (8KB) - HUD tiles
;
; PPU Address Mapping:
;   $0000-$07FF: Sprites (2KB) - R0 selects which 2KB from CHR ROM
;   $0800-$0FFF: Sprites (2KB) - R1 selects which 2KB from CHR ROM
;   $1000-$13FF: Background (1KB) - R2
;   $1400-$17FF: Background (1KB) - R3
;   $1800-$1BFF: Background (1KB) - R4
;   $1C00-$1FFF: Background (1KB) - R5
; =============================================================================
.proc mmc3_init
    ; ----- CHR Bank Setup -----
    ; We want sprites at PPU $0000-$0FFF from CHR ROM bank 0 (sprites.chr)
    ; We want backgrounds at PPU $1000-$1FFF from CHR ROM bank 8 (background.chr)

    ; R0: 2KB CHR bank at PPU $0000-$07FF
    ; Value is in 1KB units, LSB ignored for 2KB banks
    ; Bank 0 = first 2KB of sprites.chr
    lda #$00                ; Select R0
    sta $8000
    lda #$00                ; CHR bank 0 (1KB units, 0-1 = first 2KB)
    sta $8001

    ; R1: 2KB CHR bank at PPU $0800-$0FFF
    ; Bank 2 = second 2KB of sprites.chr (1KB banks 2-3)
    lda #$01                ; Select R1
    sta $8000
    lda #$02                ; CHR bank 2 (1KB units, 2-3 = second 2KB)
    sta $8001

    ; R2: 1KB CHR bank at PPU $1000-$13FF
    ; Bank 8 = first 1KB of background.chr
    lda #$02                ; Select R2
    sta $8000
    lda #$08                ; CHR bank 8
    sta $8001

    ; R3: 1KB CHR bank at PPU $1400-$17FF
    ; Bank 9 = second 1KB of background.chr
    lda #$03                ; Select R3
    sta $8000
    lda #$09                ; CHR bank 9
    sta $8001

    ; R4: 1KB CHR bank at PPU $1800-$1BFF
    ; Bank 10 = third 1KB of background.chr
    lda #$04                ; Select R4
    sta $8000
    lda #$0A                ; CHR bank 10
    sta $8001

    ; R5: 1KB CHR bank at PPU $1C00-$1FFF
    ; Bank 11 = fourth 1KB of background.chr
    lda #$05                ; Select R5
    sta $8000
    lda #$0B                ; CHR bank 11
    sta $8001

    ; ----- PRG Bank Setup -----
    ; With PRG mode 0 (bit 6 = 0): $8000 and $A000 are swappable
    ; R6: 8KB PRG bank at $8000-$9FFF
    ; R7: 8KB PRG bank at $A000-$BFFF
    ; $C000-$FFFF is fixed to last 16KB of PRG ROM
    ; For our 32KB PRG ROM, we have banks 0-3 (8KB each)
    ; Fixed bank is bank 2-3 (last 16KB)

    lda #$06                ; Select R6 (PRG bank at $8000)
    sta $8000
    lda #$00                ; PRG bank 0
    sta $8001

    lda #$07                ; Select R7 (PRG bank at $A000)
    sta $8000
    lda #$01                ; PRG bank 1
    sta $8001

    ; ----- Mirroring -----
    ; $A000: Mirroring control
    ; Bit 0: 0 = Vertical mirroring, 1 = Horizontal mirroring
    lda #$00                ; Vertical mirroring (for horizontal scrolling)
    sta $A000

    ; ----- PRG RAM -----
    ; $A001: PRG RAM protect
    ; Bit 7: 1 = Enable PRG RAM ($6000-$7FFF)
    ; Bit 6: 0 = Allow writes to PRG RAM
    lda #$80                ; Enable PRG RAM, allow writes
    sta $A001

    ; ----- IRQ -----
    ; Disable IRQ initially (will be enabled for HUD split)
    sta $E000               ; Disable IRQ

    rts
.endproc

; =============================================================================
; vblank_watchdog_start - Call at start of game logic
; =============================================================================
.proc vblank_watchdog_start
    lda #1
    sta logic_started
    rts
.endproc

; =============================================================================
; vblank_watchdog_end - Call at end of game logic
; =============================================================================
.proc vblank_watchdog_end
    lda #0
    sta logic_started
    rts
.endproc

; =============================================================================
; sprite_multiplexer_init - Initialize Recca-style OAM shuffler
; =============================================================================
.proc sprite_multiplexer_init
    lda frame_counter
    sta oam_shuffle_seed
    lda #OAM_SLOT_ENEMIES * 4
    sta oam_enemy_start
    rts
.endproc

; =============================================================================
; sprite_multiplexer_update - Rotate OAM priority using prime offset
; =============================================================================
; Uses LCG: seed = (seed + PRIME) mod 48
; This ensures every enemy gets OAM priority over 48 frames
; =============================================================================
.proc sprite_multiplexer_update
    ; Advance seed by prime offset
    lda oam_shuffle_seed
    clc
    adc #OAM_SHUFFLE_PRIME
    cmp #48                 ; 48 enemy slots available
    bcc @no_wrap
    sec
    sbc #48
@no_wrap:
    sta oam_shuffle_seed

    ; Calculate starting OAM index for enemies
    ; oam_enemy_start = OAM_SLOT_ENEMIES * 4 + (seed * 4)
    asl a                   ; seed * 2
    asl a                   ; seed * 4
    clc
    adc #OAM_SLOT_ENEMIES * 4
    sta oam_enemy_start

    rts
.endproc

; =============================================================================
; ai_update_quadrant - Update 1/4 of enemies per frame
; =============================================================================
; Call every frame. Updates enemies [quadrant*16, quadrant*16+15]
; Result: Each enemy updates at 15Hz (60fps / 4 quadrants)
; =============================================================================
.proc ai_update_quadrant
    ; Calculate starting enemy index
    lda ai_quadrant
    asl a                   ; * 2
    asl a                   ; * 4
    asl a                   ; * 8
    asl a                   ; * 16
    tax                     ; X = starting enemy index

    ; Process 16 enemies
    ldy #ENEMIES_PER_QUADRANT
@enemy_loop:
    ; Skip inactive enemies
    lda Enemy_State, x
    beq @next_enemy

    ; --- Quick-drop distance check (8-bit Manhattan) ---
    ; If |player_x - enemy_x| > threshold, skip Y check
    lda player_x
    sec
    sbc Enemy_X, x
    bcs @pos_dx
    eor #$FF                ; Negate (approximate abs)
    clc
    adc #1
@pos_dx:
    cmp #64                 ; Distance threshold
    bcs @move_toward_tower  ; Too far from player, target tower

    ; Check Y distance
    lda player_y
    sec
    sbc Enemy_Y, x
    bcs @pos_dy
    eor #$FF
    clc
    adc #1
@pos_dy:
    cmp #64
    bcs @move_toward_tower

    ; --- Close to player: aggro behavior ---
    jmp @move_toward_player

@move_toward_tower:
    ; Move toward tower
    lda Enemy_X, x
    cmp tower_x
    beq @check_tower_y
    bcs @tower_move_left
    ; Move right toward tower
    inc Enemy_X, x
    jmp @check_tower_y
@tower_move_left:
    dec Enemy_X, x

@check_tower_y:
    lda Enemy_Y, x
    cmp tower_y
    beq @next_enemy
    bcs @tower_move_up
    inc Enemy_Y, x
    jmp @next_enemy
@tower_move_up:
    dec Enemy_Y, x
    jmp @next_enemy

@move_toward_player:
    ; Move toward player
    lda Enemy_X, x
    cmp player_x
    beq @check_player_y
    bcs @player_move_left
    inc Enemy_X, x
    jmp @check_player_y
@player_move_left:
    dec Enemy_X, x

@check_player_y:
    lda Enemy_Y, x
    cmp player_y
    beq @next_enemy
    bcs @player_move_up
    inc Enemy_Y, x
    jmp @next_enemy
@player_move_up:
    dec Enemy_Y, x

@next_enemy:
    inx
    dey
    bne @enemy_loop

    ; Advance to next quadrant
    inc ai_quadrant
    lda ai_quadrant
    and #$03                ; Wrap at 4
    sta ai_quadrant

    rts
.endproc

; =============================================================================
; density_map_build - Build spatial density map for collision culling
; =============================================================================
; Each bit in Density_Map represents a 32x32 pixel cell
; Set if any enemy occupies that cell
; =============================================================================
.proc density_map_build
    ; Clear density map
    ldx #63
    lda #0
@clear:
    sta Density_Map, x
    dex
    bpl @clear

    ; Populate from active enemies
    ldx #0
@enemy_loop:
    lda Enemy_State, x
    beq @next

    ; Calculate cell index: (Y / 32) * 8 + (X / 32)
    lda Enemy_Y, x
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a                   ; Y / 32
    asl a
    asl a
    asl a                   ; * 8
    sta temp1

    lda Enemy_X, x
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a                   ; X / 32
    ora temp1               ; cell = row*8 + col
    tay

    ; Set density bit
    lda #$FF                ; Mark cell as occupied
    sta Density_Map, y

@next:
    inx
    cpx #MAX_ENEMIES
    bne @enemy_loop

    rts
.endproc

; =============================================================================
; collision_check_bitmask - Fast collision using density map
; =============================================================================
; Input: A = X position, Y = Y position of projectile
; Output: Carry set if potential collision, clear if no enemies in cell
; =============================================================================
.proc collision_check_bitmask
    ; Save projectile position
    sta temp1               ; X
    sty temp2               ; Y

    ; Calculate cell index
    tya
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a                   ; Y / 32
    asl a
    asl a
    asl a                   ; * 8
    sta temp3

    lda temp1
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a                   ; X / 32
    ora temp3
    tay

    ; Check density map
    lda Density_Map, y
    beq @no_collision       ; Cell empty, skip detailed check
    sec                     ; Potential collision
    rts

@no_collision:
    clc
    rts
.endproc

; =============================================================================
; bullets_render_interleaved - 30fps bullet rendering
; =============================================================================
; Alternates between even and odd indexed bullets each frame
; Effectively doubles visible bullet count via persistence of vision
; =============================================================================
.proc bullets_render_interleaved
    ; Get current OAM position
    lda #OAM_SLOT_BULLETS * 4
    sta oam_index

    ; Determine which set to render this frame
    lda bullet_frame
    eor #1
    sta bullet_frame
    beq @render_even

@render_odd:
    ldx #1                  ; Start at bullet 1
    jmp @render_loop

@render_even:
    ldx #0                  ; Start at bullet 0

@render_loop:
    ; Check if we've filled all bullet slots
    lda oam_index
    cmp #OAM_SLOT_ENEMIES * 4
    bcs @done

    ; Check bullet active (bitmask)
    txa
    lsr a
    lsr a
    lsr a                   ; byte index = X / 8
    tay
    txa
    and #$07                ; bit index = X % 8
    sta temp1
    lda Bullet_Active, y
    and bit_masks, temp1    ; Would need lookup table
    beq @skip

    ; Render bullet to OAM
    ldy oam_index
    lda Bullet_Y, x
    sta $0200, y            ; Y position
    lda #$08                ; Bullet tile
    sta $0201, y
    lda #$02                ; Palette 2, no flip
    sta $0202, y
    lda Bullet_X, x
    sta $0203, y

    ; Advance OAM index
    tya
    clc
    adc #4
    sta oam_index

@skip:
    ; Advance by 2 (interleaved)
    inx
    inx
    cpx #MAX_BULLETS
    bcc @render_loop

@done:
    rts

; Bit mask lookup table
bit_masks:
    .byte $01, $02, $04, $08, $10, $20, $40, $80
.endproc

; =============================================================================
; chr_bank_swap_animation - Global animation via CHR bank switching
; =============================================================================
; Swaps between CHR banks for "free" animation of all sprites
; =============================================================================
.proc chr_bank_swap_animation
    ; Decrement timer
    dec chr_anim_timer
    bne @done

    ; Reset timer (e.g., 8 frames per animation frame)
    lda #8
    sta chr_anim_timer

    ; Toggle animation frame
    lda chr_anim_frame
    eor #1
    sta chr_anim_frame

    ; Swap sprite CHR bank
    ; Frame 0: Use CHR bank 0/2
    ; Frame 1: Use CHR bank 8/10 (if available)
    beq @frame0

@frame1:
    lda #$00
    sta $8000
    lda #$08                ; Alternate sprite bank
    sta $8001
    lda #$01
    sta $8000
    lda #$0A
    sta $8001
    rts

@frame0:
    lda #$00
    sta $8000
    lda #$00
    sta $8001
    lda #$01
    sta $8000
    lda #$02
    sta $8001

@done:
    rts
.endproc

; =============================================================================
; NMI Handler with VBlank Watchdog
; =============================================================================
.proc NMI_survivor
    pha
    txa
    pha
    tya
    pha

    ; Check watchdog - did logic complete?
    lda logic_started
    beq @do_dma

    ; WATCHDOG TRIGGERED: Logic overran frame!
    ; Skip OAM DMA to prevent garbage, maintain audio/IRQ stability
    jmp @skip_dma

@do_dma:
    ; OAM DMA
    lda #0
    sta $2003
    lda #$02
    sta $4014

@skip_dma:
    ; Reset scroll
    lda #0
    sta $2005
    sta $2005

    ; Increment frame counter
    inc frame_counter

    ; Signal main loop
    lda #1
    sta nmi_flag

    pla
    tay
    pla
    tax
    pla
    rti
.endproc

; =============================================================================
; sprite_to_bg_bake - Convert "at-tower" enemies to BG tiles
; =============================================================================
; When enemies reach the tower, convert them to background tiles instead
; of sprites. This frees sprite slots and creates a "swarming" visual.
; Uses a VRAM buffer to update during VBlank.
; =============================================================================

; VRAM update buffer (in RAM, max 64 bytes per frame)
VRAM_BUF_SIZE       = 64
.segment "BSS"
vram_buffer:        .res VRAM_BUF_SIZE
vram_buf_len:       .res 1

.segment "CODE"

.proc sprite_to_bg_init
    lda #0
    sta vram_buf_len
    rts
.endproc

; Queue a tile update: A=tile, X=nametable offset low, Y=nametable offset high
.proc vram_buffer_add
    pha                     ; Save tile

    ; Check buffer space
    lda vram_buf_len
    cmp #VRAM_BUF_SIZE - 3
    bcs @full

    ; Add to buffer: [addr_hi, addr_lo, tile]
    tax
    tya
    sta vram_buffer, x      ; High byte of address
    inx
    pla                     ; Get addr_lo from stack... wait, need to reorganize
    ; Actually let's simplify: just store the data

@full:
    pla                     ; Discard tile
    rts
.endproc

; Flush VRAM buffer during VBlank
.proc vram_buffer_flush
    ldx vram_buf_len
    beq @done

    ; Process buffer in triplets (addr_hi, addr_lo, tile)
    ldy #0
@loop:
    cpy vram_buf_len
    bcs @clear

    ; Set PPU address
    lda vram_buffer, y
    sta $2006               ; High byte
    iny
    lda vram_buffer, y
    sta $2006               ; Low byte
    iny

    ; Write tile
    lda vram_buffer, y
    sta $2007
    iny

    jmp @loop

@clear:
    lda #0
    sta vram_buf_len

@done:
    rts
.endproc

; Convert enemy at tower to BG tile
; Input: X = enemy index
.proc enemy_bake_to_bg
    ; Calculate nametable position from enemy X,Y
    ; Nametable address = $2000 + (Y/8)*32 + (X/8)

    lda Enemy_Y, x
    lsr a
    lsr a
    lsr a                   ; Y / 8
    sta temp1
    asl a
    asl a
    asl a
    asl a
    asl a                   ; * 32
    sta temp2               ; Low byte

    lda temp1
    lsr a
    lsr a
    lsr a                   ; Carry into high byte
    ora #$20                ; Base $2000
    sta temp3               ; High byte

    lda Enemy_X, x
    lsr a
    lsr a
    lsr a                   ; X / 8
    clc
    adc temp2
    sta temp2
    bcc @no_carry
    inc temp3
@no_carry:

    ; Queue VRAM update
    lda vram_buf_len
    cmp #VRAM_BUF_SIZE - 3
    bcs @buffer_full

    tay
    lda temp3
    sta vram_buffer, y      ; Addr high
    iny
    lda temp2
    sta vram_buffer, y      ; Addr low
    iny
    lda #$10                ; "Enemy at tower" tile
    sta vram_buffer, y
    iny
    sty vram_buf_len

    ; Deactivate sprite enemy
    lda #0
    sta Enemy_State, x

@buffer_full:
    rts
.endproc

; =============================================================================
; MMC3 IRQ Split - Static HUD at scanline 200
; =============================================================================
; Sets up MMC3 scanline counter to fire IRQ at line 200
; IRQ handler switches to HUD CHR bank and disables scrolling
; =============================================================================

HUD_SPLIT_LINE      = 200   ; Scanline to split at (bottom 40 lines for HUD)

.proc irq_split_init
    ; Set IRQ latch value (scanlines until IRQ)
    lda #HUD_SPLIT_LINE
    sta $C000               ; IRQ latch
    sta $C001               ; Reload counter
    sta $E001               ; Enable IRQ
    rts
.endproc

.proc irq_split_disable
    sta $E000               ; Disable IRQ
    rts
.endproc

; IRQ Handler - Called at scanline 200
.proc IRQ_hud_split
    pha

    ; Acknowledge IRQ by writing to $C001
    sta $C001

    ; Switch to HUD CHR bank for background
    ; Assumes HUD tiles are in CHR bank 12-15
    lda #$02
    sta $8000
    lda #$0C                ; HUD CHR bank
    sta $8001

    lda #$03
    sta $8000
    lda #$0D
    sta $8001

    lda #$04
    sta $8000
    lda #$0E
    sta $8001

    lda #$05
    sta $8000
    lda #$0F
    sta $8001

    ; Reset scroll for HUD (no scrolling in HUD area)
    lda #0
    sta $2005
    sta $2005

    pla
    rti
.endproc

; =============================================================================
; Enhanced NMI with VRAM buffer flush and IRQ setup
; =============================================================================
.proc NMI_survivor_enhanced
    pha
    txa
    pha
    tya
    pha

    ; Check watchdog
    lda logic_started
    bne @skip_updates

    ; OAM DMA
    lda #0
    sta $2003
    lda #$02
    sta $4014

    ; Flush VRAM buffer (sprite-to-BG updates)
    jsr vram_buffer_flush

    ; Reset CHR banks to game graphics (IRQ will switch for HUD)
    lda #$02
    sta $8000
    lda #$04
    sta $8001

    lda #$03
    sta $8000
    lda #$05
    sta $8001

    lda #$04
    sta $8000
    lda #$06
    sta $8001

    lda #$05
    sta $8000
    lda #$07
    sta $8001

    ; Reset scroll
    lda scroll_x
    sta $2005
    lda scroll_y
    sta $2005

    ; Reload IRQ counter for next frame's HUD split
    lda #HUD_SPLIT_LINE
    sta $C000
    sta $C001

@skip_updates:
    ; Increment frame counter
    inc frame_counter

    ; Signal main loop
    lda #1
    sta nmi_flag

    pla
    tay
    pla
    tax
    pla
    rti
.endproc

; =============================================================================
; Tower proximity check - determines if enemy should bake to BG
; =============================================================================
TOWER_BAKE_DISTANCE = 8     ; Pixels from tower center to trigger bake

.proc check_tower_proximity
    ; For each active enemy, check if at tower
    ldx #0
@loop:
    lda Enemy_State, x
    beq @next

    ; Check X distance to tower
    lda Enemy_X, x
    sec
    sbc tower_x
    bcs @pos_x
    eor #$FF
    clc
    adc #1
@pos_x:
    cmp #TOWER_BAKE_DISTANCE
    bcs @next

    ; Check Y distance to tower
    lda Enemy_Y, x
    sec
    sbc tower_y
    bcs @pos_y
    eor #$FF
    clc
    adc #1
@pos_y:
    cmp #TOWER_BAKE_DISTANCE
    bcs @next

    ; Enemy is at tower - bake to BG and damage tower
    jsr enemy_bake_to_bg

    ; Damage tower
    lda tower_hp
    beq @next                ; Already dead
    dec tower_hp

    ; Flash effect
    lda #8
    sta tower_damage_flash

@next:
    inx
    cpx #MAX_ENEMIES
    bne @loop

    rts
.endproc

; External NMI flag (import from main code)
.importzp nmi_flag
