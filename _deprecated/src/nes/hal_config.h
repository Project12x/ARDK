/*
 * =============================================================================
 * ARDK - NES Platform Configuration
 * hal_config.h - NES-specific constants and limits
 * =============================================================================
 *
 * NES Hardware Specifications:
 * - CPU: Ricoh 2A03 (6502 @ 1.79 MHz NTSC)
 * - PPU: 2C02, 256x240 visible (256x224 safe)
 * - Sprites: 64 hardware sprites, 8x8 or 8x16, 8 per scanline
 * - Colors: 52-color palette, 4 sprite palettes of 3 colors each
 * - RAM: 2KB internal, more with mapper
 *
 * TIER: MINIMAL
 * =============================================================================
 */

#ifndef ARDK_HAL_CONFIG_NES_H
#define ARDK_HAL_CONFIG_NES_H

/* ---------------------------------------------------------------------------
 * Tier Selection - Must be before hal_tiers.h include
 *
 * NES is TIER_MINIMAL: 8-bit CPU, 2KB RAM, limited sprites
 * --------------------------------------------------------------------------- */

#define HAL_TIER    HAL_TIER_MINIMAL

/* Platform-specific overrides BEFORE including tiers */
/* (Override tier defaults if NES needs different values) */

/* NES-specific: We can push enemies a bit higher with MMC3 RAM */
/* #define HAL_MAX_ENEMIES  16 */  /* Uncomment to override tier default of 12 */

#include "../hal_tiers.h"

/* ---------------------------------------------------------------------------
 * Screen Dimensions
 * --------------------------------------------------------------------------- */

#define HAL_SCREEN_WIDTH    256
#define HAL_SCREEN_HEIGHT   240
#define HAL_SAFE_WIDTH      256     /* Full width is safe */
#define HAL_SAFE_HEIGHT     224     /* Top/bottom 8 pixels often cut */

/* ---------------------------------------------------------------------------
 * Sprite Limits
 * --------------------------------------------------------------------------- */

#define HAL_MAX_SPRITES         64      /* Hardware OAM limit */
#define HAL_MAX_SPRITES_LINE    8       /* Per scanline limit */
#define HAL_SPRITE_WIDTH        8       /* Base sprite size */
#define HAL_SPRITE_HEIGHT       8       /* 8x8 mode (can be 8x16) */

/* ---------------------------------------------------------------------------
 * Tile/Background
 * --------------------------------------------------------------------------- */

#define HAL_TILE_WIDTH      8
#define HAL_TILE_HEIGHT     8
#define HAL_BG_WIDTH        32      /* Nametable width in tiles */
#define HAL_BG_HEIGHT       30      /* Nametable height in tiles */
#define HAL_BG_WIDTH_PX     256
#define HAL_BG_HEIGHT_PX    240

/* ---------------------------------------------------------------------------
 * Timing
 * --------------------------------------------------------------------------- */

#define HAL_FPS_NTSC        60
#define HAL_FPS_PAL         50
#define HAL_CYCLES_FRAME    29780   /* CPU cycles per frame (NTSC) */
#define HAL_VBLANK_CYCLES   2273    /* Cycles during VBlank */

/* Use NTSC as default */
#define HAL_FPS             HAL_FPS_NTSC

/* ---------------------------------------------------------------------------
 * Memory Limits
 * --------------------------------------------------------------------------- */

#define HAL_RAM_SIZE        0x0800  /* 2KB internal RAM */
#define HAL_ZP_SIZE         0x100   /* Zero page (256 bytes) */

/* Entity pool size (limited by RAM) */
#define MAX_ENTITIES        32      /* Fits in available RAM */

/* ---------------------------------------------------------------------------
 * Platform Capabilities
 * --------------------------------------------------------------------------- */

#define HAL_PLATFORM_CAPS   ( \
    HAL_CAP_SPRITE_FLIP |       \
    HAL_CAP_BG_SCROLL |         \
    HAL_CAP_BG_SCROLL_Y         \
)
/* NES does NOT have: SPRITE_ZOOM, MULTIPLY, DIVIDE, STEREO, PCM */

/* ---------------------------------------------------------------------------
 * Audio
 * --------------------------------------------------------------------------- */

#define HAL_AUDIO_CHANNELS  5       /* 2 pulse, 1 triangle, 1 noise, 1 DPCM */
#define HAL_SFX_CHANNELS    2       /* Usually use pulse channels for SFX */

/* ---------------------------------------------------------------------------
 * NES-Specific Hardware Addresses
 * --------------------------------------------------------------------------- */

/* PPU registers */
#define PPU_CTRL        0x2000
#define PPU_MASK        0x2001
#define PPU_STATUS      0x2002
#define OAM_ADDR        0x2003
#define OAM_DATA        0x2004
#define PPU_SCROLL      0x2005
#define PPU_ADDR        0x2006
#define PPU_DATA        0x2007
#define OAM_DMA         0x4014

/* APU registers */
#define APU_PULSE1      0x4000
#define APU_PULSE2      0x4004
#define APU_TRIANGLE    0x4008
#define APU_NOISE       0x400C
#define APU_DMC         0x4010
#define APU_STATUS      0x4015
#define APU_FRAME       0x4017

/* Controller ports */
#define JOY1            0x4016
#define JOY2            0x4017

#endif /* ARDK_HAL_CONFIG_NES_H */
