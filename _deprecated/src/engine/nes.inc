; =============================================================================
; NEON SURVIVORS - NES Hardware Definitions
; PPU, APU, and MMC3 register addresses
; =============================================================================

; -----------------------------------------------------------------------------
; PPU Registers ($2000-$2007)
; -----------------------------------------------------------------------------
PPU_CTRL        = $2000     ; PPU Control Register 1
PPU_MASK        = $2001     ; PPU Control Register 2
PPU_STATUS      = $2002     ; PPU Status Register
OAM_ADDR        = $2003     ; OAM Address
OAM_DATA        = $2004     ; OAM Data
PPU_SCROLL      = $2005     ; PPU Scroll Position
PPU_ADDR        = $2006     ; PPU Address
PPU_DATA        = $2007     ; PPU Data

; -----------------------------------------------------------------------------
; APU & I/O Registers
; -----------------------------------------------------------------------------
OAM_DMA         = $4014     ; OAM DMA Register
APU_STATUS      = $4015     ; APU Status
JOYPAD1         = $4016     ; Joypad 1
JOYPAD2         = $4017     ; Joypad 2 / APU Frame Counter

; -----------------------------------------------------------------------------
; APU Sound Channels
; -----------------------------------------------------------------------------
APU_PULSE1_CTRL = $4000     ; Pulse 1 Control
APU_PULSE1_SWEEP= $4001     ; Pulse 1 Sweep
APU_PULSE1_LO   = $4002     ; Pulse 1 Timer Low
APU_PULSE1_HI   = $4003     ; Pulse 1 Timer High

APU_PULSE2_CTRL = $4004     ; Pulse 2 Control
APU_PULSE2_SWEEP= $4005     ; Pulse 2 Sweep
APU_PULSE2_LO   = $4006     ; Pulse 2 Timer Low
APU_PULSE2_HI   = $4007     ; Pulse 2 Timer High

APU_TRI_CTRL    = $4008     ; Triangle Control
APU_TRI_LO      = $400A     ; Triangle Timer Low
APU_TRI_HI      = $400B     ; Triangle Timer High

APU_NOISE_CTRL  = $400C     ; Noise Control
APU_NOISE_LO    = $400E     ; Noise Timer
APU_NOISE_HI    = $400F     ; Noise Length

APU_DMC_CTRL    = $4010     ; DMC Control
APU_DMC_LOAD    = $4011     ; DMC Direct Load
APU_DMC_ADDR    = $4012     ; DMC Sample Address
APU_DMC_LEN     = $4013     ; DMC Sample Length

APU_FRAME       = $4017     ; Frame Counter / IRQ

; -----------------------------------------------------------------------------
; MMC3 Mapper Registers
; -----------------------------------------------------------------------------
MMC3_BANK_SELECT= $8000     ; Bank select and PRG/CHR mode
MMC3_BANK_DATA  = $8001     ; Bank data
MMC3_MIRRORING  = $A000     ; Mirroring control
MMC3_MIRROR     = $A000     ; Mirroring control (alias)
MMC3_SRAM_EN    = $A001     ; PRG RAM protect
MMC3_IRQ_LATCH  = $C000     ; IRQ latch value
MMC3_IRQ_RELOAD = $C001     ; IRQ counter reload
MMC3_IRQ_DISABLE= $E000     ; IRQ disable
MMC3_IRQ_ENABLE = $E001     ; IRQ enable

; -----------------------------------------------------------------------------
; MMC3 Bank Select Values
; -----------------------------------------------------------------------------
MMC3_CHR_2K_0   = $00       ; 2KB CHR bank at $0000
MMC3_CHR_2K_1   = $01       ; 2KB CHR bank at $0800
MMC3_CHR_1K_0   = $02       ; 1KB CHR bank at $1000
MMC3_CHR_1K_1   = $03       ; 1KB CHR bank at $1400
MMC3_CHR_1K_2   = $04       ; 1KB CHR bank at $1800
MMC3_CHR_1K_3   = $05       ; 1KB CHR bank at $1C00
MMC3_PRG_8K_0   = $06       ; 8KB PRG bank at $8000 (or $C000)
MMC3_PRG_8K_1   = $07       ; 8KB PRG bank at $A000

; -----------------------------------------------------------------------------
; Controller Button Masks (HAL-compatible format)
; -----------------------------------------------------------------------------
; These match HAL_BTN_* definitions in hal/hal.h for cross-platform compatibility.
; The NES hardware reads buttons in reverse order (A=bit7), but the input routine
; remaps to this HAL format for consistency with game code.
;
; HAL format (low byte of 16-bit mask):
;   Bit 0: A
;   Bit 1: B
;   Bit 2: Select
;   Bit 3: Start
;   Bit 4: Up
;   Bit 5: Down
;   Bit 6: Left
;   Bit 7: Right
;
BTN_A           = %00000001     ; HAL_BTN_A
BTN_B           = %00000010     ; HAL_BTN_B
BTN_SELECT      = %00000100     ; HAL_BTN_SELECT
BTN_START       = %00001000     ; HAL_BTN_START
BTN_UP          = %00010000     ; HAL_BTN_UP
BTN_DOWN        = %00100000     ; HAL_BTN_DOWN
BTN_LEFT        = %01000000     ; HAL_BTN_LEFT
BTN_RIGHT       = %10000000     ; HAL_BTN_RIGHT

; Raw NES hardware button order (for input routine internal use)
BTN_RAW_A       = %10000000
BTN_RAW_B       = %01000000
BTN_RAW_SELECT  = %00100000
BTN_RAW_START   = %00010000
BTN_RAW_UP      = %00001000
BTN_RAW_DOWN    = %00000100
BTN_RAW_LEFT    = %00000010
BTN_RAW_RIGHT   = %00000001

; -----------------------------------------------------------------------------
; PPU Control Flags
; -----------------------------------------------------------------------------
PPUCTRL_NMI     = %10000000 ; Enable NMI on VBlank
PPUCTRL_SPR8X16 = %00100000 ; 8x16 sprites
PPUCTRL_BGADDR  = %00010000 ; Background pattern table $1000
PPUCTRL_SPRADDR = %00001000 ; Sprite pattern table $1000
PPUCTRL_VRAM32  = %00000100 ; VRAM increment 32
PPUCTRL_NT1     = %00000001 ; Nametable bit 0
PPUCTRL_NT2     = %00000010 ; Nametable bit 1

PPUMASK_COLOR   = %00000000 ; Normal color
PPUMASK_GRAYSCALE=%00000001 ; Grayscale
PPUMASK_BGLEFT  = %00000010 ; Show background in leftmost 8 pixels
PPUMASK_SPRLEFT = %00000100 ; Show sprites in leftmost 8 pixels
PPUMASK_BG      = %00001000 ; Show background
PPUMASK_SPR     = %00010000 ; Show sprites
PPUMASK_RED     = %00100000 ; Emphasize red
PPUMASK_GREEN   = %01000000 ; Emphasize green
PPUMASK_BLUE    = %10000000 ; Emphasize blue
