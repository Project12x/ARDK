/*
 * =============================================================================
 * ARDK - Genesis/Mega Drive Platform Configuration
 * hal_config.h - Genesis-specific constants and limits
 * =============================================================================
 *
 * Genesis Hardware Specifications:
 * - CPU: Motorola 68000 @ 7.67 MHz (NTSC)
 * - VDP: Custom, 320x224 (NTSC) or 320x240 (PAL)
 * - Sprites: 80 hardware sprites, 8x8 to 32x32, 20 per scanline
 * - Colors: 512-color palette, 4 palettes of 16 colors each
 * - RAM: 64KB main, 64KB VRAM
 * - Sound: YM2612 FM + SN76489 PSG
 *
 * TIER: STANDARD
 * =============================================================================
 */

#ifndef ARDK_HAL_CONFIG_GENESIS_H
#define ARDK_HAL_CONFIG_GENESIS_H

/* ---------------------------------------------------------------------------
 * Tier Selection - Must be before hal_tiers.h include
 *
 * Genesis is TIER_STANDARD: 16-bit CPU, 64KB RAM, hardware multiply
 * --------------------------------------------------------------------------- */

#define HAL_TIER    HAL_TIER_STANDARD

/* Platform-specific overrides BEFORE including tiers */
/* Genesis has plenty of RAM, can push limits higher if needed */
/* #define HAL_MAX_ENEMIES  64 */  /* Uncomment to override tier default of 48 */

#include "../hal_tiers.h"

/* ---------------------------------------------------------------------------
 * Screen Dimensions
 * --------------------------------------------------------------------------- */

#define HAL_SCREEN_WIDTH    320
#define HAL_SCREEN_HEIGHT   224     /* NTSC, PAL is 240 */
#define HAL_SAFE_WIDTH      320
#define HAL_SAFE_HEIGHT     224

/* Optional 256-wide mode */
#define HAL_SCREEN_WIDTH_H32    256

/* ---------------------------------------------------------------------------
 * Sprite Limits
 * --------------------------------------------------------------------------- */

#define HAL_MAX_SPRITES         80      /* Hardware sprite limit */
#define HAL_MAX_SPRITES_LINE    20      /* Per scanline limit */
#define HAL_SPRITE_WIDTH        8       /* Minimum sprite size */
#define HAL_SPRITE_HEIGHT       8       /* Can be 8,16,24,32 */
#define HAL_SPRITE_MAX_WIDTH    32      /* Maximum sprite size */
#define HAL_SPRITE_MAX_HEIGHT   32

/* ---------------------------------------------------------------------------
 * Tile/Background
 * --------------------------------------------------------------------------- */

#define HAL_TILE_WIDTH      8
#define HAL_TILE_HEIGHT     8
#define HAL_BG_WIDTH        64      /* Scroll plane can be 32,64,128 */
#define HAL_BG_HEIGHT       32      /* Scroll plane height */
#define HAL_BG_WIDTH_PX     512
#define HAL_BG_HEIGHT_PX    256

/* Genesis has two scroll planes */
#define HAL_HAS_PLANE_A     1
#define HAL_HAS_PLANE_B     1

/* ---------------------------------------------------------------------------
 * Timing
 * --------------------------------------------------------------------------- */

#define HAL_FPS_NTSC        60
#define HAL_FPS_PAL         50
#define HAL_CYCLES_FRAME    127137  /* 68000 cycles per frame (NTSC) */
#define HAL_VBLANK_CYCLES   4770    /* Cycles during VBlank */

#define HAL_FPS             HAL_FPS_NTSC

/* ---------------------------------------------------------------------------
 * Memory Limits
 * --------------------------------------------------------------------------- */

#define HAL_RAM_SIZE        0x10000     /* 64KB main RAM */
#define HAL_VRAM_SIZE       0x10000     /* 64KB VRAM */

/* Entity pool size - inherited from tier, can override if needed */
/* Note: HAL_MAX_ENTITIES defined in hal_tiers.h (128 for STANDARD tier) */

/* ---------------------------------------------------------------------------
 * Platform Capabilities
 * --------------------------------------------------------------------------- */

#define HAL_PLATFORM_CAPS   ( \
    HAL_CAP_SPRITE_FLIP |       \
    HAL_CAP_BG_SCROLL |         \
    HAL_CAP_BG_SCROLL_Y |       \
    HAL_CAP_RASTER_FX |         \
    HAL_CAP_STEREO |            \
    HAL_CAP_PCM                 \
)
/* Genesis does NOT have hardware multiply in 68000 (though DIV exists) */
/* But 68000 has MUL instruction, so we could add HAL_CAP_MULTIPLY */

/* ---------------------------------------------------------------------------
 * Audio
 * --------------------------------------------------------------------------- */

#define HAL_AUDIO_CHANNELS_FM   6       /* YM2612 FM channels */
#define HAL_AUDIO_CHANNELS_PSG  4       /* SN76489 (3 tone + 1 noise) */
#define HAL_AUDIO_CHANNELS      10      /* Total */
#define HAL_SFX_CHANNELS        3       /* Typically use PSG for SFX */

/* ---------------------------------------------------------------------------
 * Genesis-Specific Hardware Addresses
 * --------------------------------------------------------------------------- */

/* VDP Ports */
#define VDP_DATA        0xC00000
#define VDP_CTRL        0xC00004
#define VDP_HVCOUNTER   0xC00008

/* Controller Ports */
#define IO_DATA1        0xA10003
#define IO_DATA2        0xA10005
#define IO_DATA3        0xA10007
#define IO_CTRL1        0xA10009
#define IO_CTRL2        0xA1000B
#define IO_CTRL3        0xA1000D

/* Z80 Control */
#define Z80_BUSREQ      0xA11100
#define Z80_RESET       0xA11200
#define Z80_RAM         0xA00000

/* YM2612 */
#define YM2612_A0       0xA04000
#define YM2612_D0       0xA04001
#define YM2612_A1       0xA04002
#define YM2612_D1       0xA04003

/* PSG */
#define PSG_PORT        0xC00011

/* ---------------------------------------------------------------------------
 * VDP Register Values
 * --------------------------------------------------------------------------- */

/* Plane sizes */
#define PLANE_32x32     0x00
#define PLANE_64x32     0x01
#define PLANE_128x32    0x03
#define PLANE_32x64     0x10
#define PLANE_64x64     0x11
#define PLANE_32x128    0x30

/* VDP addresses (typical SGDK layout) */
#define VRAM_PLANE_A    0xC000
#define VRAM_PLANE_B    0xE000
#define VRAM_WINDOW     0xB000
#define VRAM_SPRITES    0xBC00
#define VRAM_HSCROLL    0xB800

#endif /* ARDK_HAL_CONFIG_GENESIS_H */
