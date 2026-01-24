/*
 * =============================================================================
 * ARDK - NES HAL Implementation
 * hal_nes.c - Hardware Abstraction Layer for NES
 * =============================================================================
 *
 * This file implements the HAL interface for the NES platform.
 * Uses cc65 conventions and NES-specific hardware access.
 *
 * Build with: cl65 -t nes ...
 * =============================================================================
 */

#include "../hal.h"
#include "hal_config.h"

/* ---------------------------------------------------------------------------
 * Zero Page Variables (for performance)
 * --------------------------------------------------------------------------- */

#pragma zpsym ("hal_temp")
#pragma zpsym ("hal_temp2")
#pragma zpsym ("frame_count")
#pragma zpsym ("rand_state")

static unsigned char hal_temp;
static unsigned char hal_temp2;
static unsigned int frame_count;
static unsigned int rand_state;

/* ---------------------------------------------------------------------------
 * OAM Shadow Buffer
 *
 * We update this buffer, then DMA to OAM during VBlank
 * --------------------------------------------------------------------------- */

#define OAM_BUF     ((unsigned char*)0x0200)

/* OAM entry offsets */
#define OAM_Y       0
#define OAM_TILE    1
#define OAM_ATTR    2
#define OAM_X       3

/* ---------------------------------------------------------------------------
 * Input State
 * --------------------------------------------------------------------------- */

static u16 joy1_cur;        /* Current frame button state */
static u16 joy1_prev;       /* Previous frame state */
static u16 joy2_cur;
static u16 joy2_prev;

/* Read controller (internal) */
static u8 read_joy(u8 port) {
    u8 result = 0;
    u8 i;
    volatile u8* joy_port = (port == 0) ? (u8*)JOY1 : (u8*)JOY2;

    /* Strobe controller */
    *((u8*)JOY1) = 1;
    *((u8*)JOY1) = 0;

    /* Read 8 bits */
    for (i = 0; i < 8; ++i) {
        result >>= 1;
        if (*joy_port & 1) {
            result |= 0x80;
        }
    }

    return result;
}

/* ---------------------------------------------------------------------------
 * HAL Implementation: Input
 * --------------------------------------------------------------------------- */

u16 hal_input_read(port_t port) {
    if (port == 0) return joy1_cur;
    return joy2_cur;
}

u16 hal_input_pressed(port_t port) {
    if (port == 0) return joy1_cur & ~joy1_prev;
    return joy2_cur & ~joy2_prev;
}

u16 hal_input_released(port_t port) {
    if (port == 0) return ~joy1_cur & joy1_prev;
    return ~joy2_cur & joy2_prev;
}

/* ---------------------------------------------------------------------------
 * HAL Implementation: Sprites
 * --------------------------------------------------------------------------- */

void hal_sprite_set(u8 slot, fixed8_8 x, fixed8_8 y, sprite_id_t tile, u8 attr) {
    u8* oam = OAM_BUF + (slot << 2);

    /* Convert fixed-point to pixel (take integer part) */
    oam[OAM_X] = (u8)(x >> 8);
    oam[OAM_Y] = (u8)(y >> 8) - 1;  /* NES OAM Y is offset by 1 */
    oam[OAM_TILE] = tile;

    /* Convert HAL attributes to NES format */
    /* HAL: bit 0=flipH, 1=flipV, 2=priority, 4-5=palette */
    /* NES: bit 6=flipH, 7=flipV, 5=priority, 0-1=palette */
    oam[OAM_ATTR] = ((attr & HAL_SPR_FLIP_H) ? 0x40 : 0) |
                    ((attr & HAL_SPR_FLIP_V) ? 0x80 : 0) |
                    ((attr & HAL_SPR_PRIORITY) ? 0x20 : 0) |
                    ((attr >> 4) & 0x03);
}

void hal_sprite_hide(u8 slot) {
    u8* oam = OAM_BUF + (slot << 2);
    oam[OAM_Y] = 0xFF;  /* Off-screen */
}

void hal_sprite_hide_all(void) {
    u8 i;
    for (i = 0; i < HAL_MAX_SPRITES; ++i) {
        hal_sprite_hide(i);
    }
}

u8 hal_metasprite_set(u8 start_slot, fixed8_8 x, fixed8_8 y,
                      const u8* data, u8 attr) {
    /* Metasprite data format:
     * For each sprite: dx, dy, tile, attr_mod
     * Terminated by 0x80 in dx position
     */
    u8 slot = start_slot;
    i8 dx, dy;

    while (slot < HAL_MAX_SPRITES) {
        dx = (i8)*data++;
        if (dx == (i8)0x80) break;  /* End marker */

        dy = (i8)*data++;
        hal_sprite_set(slot, x + FP_FROM_INT(dx), y + FP_FROM_INT(dy),
                       *data++, attr ^ *data++);
        slot++;
    }

    return slot - start_slot;
}

/* ---------------------------------------------------------------------------
 * HAL Implementation: Background
 * --------------------------------------------------------------------------- */

static u8 ppu_ctrl_val = 0x80;  /* NMI enabled */
static i16 scroll_x = 0;
static i16 scroll_y = 0;

void hal_bg_tile_set(u8 x, u8 y, u8 tile) {
    u16 addr = 0x2000 + (y << 5) + x;

    /* Wait for safe VRAM access (should be in VBlank) */
    *((u8*)PPU_ADDR) = addr >> 8;
    *((u8*)PPU_ADDR) = addr & 0xFF;
    *((u8*)PPU_DATA) = tile;
}

void hal_bg_row_set(u8 x, u8 y, const u8* tiles, u8 count) {
    u16 addr = 0x2000 + (y << 5) + x;
    u8 i;

    *((u8*)PPU_ADDR) = addr >> 8;
    *((u8*)PPU_ADDR) = addr & 0xFF;

    for (i = 0; i < count; ++i) {
        *((u8*)PPU_DATA) = tiles[i];
    }
}

void hal_bg_col_set(u8 x, u8 y, const u8* tiles, u8 count) {
    u8 i;

    /* Must set address for each tile (no vertical increment mode) */
    /* Actually NES has increment-32 mode... let's use it */
    *((u8*)PPU_CTRL) = ppu_ctrl_val | 0x04;  /* Increment 32 */

    {
        u16 addr = 0x2000 + (y << 5) + x;
        *((u8*)PPU_ADDR) = addr >> 8;
        *((u8*)PPU_ADDR) = addr & 0xFF;
    }

    for (i = 0; i < count; ++i) {
        *((u8*)PPU_DATA) = tiles[i];
    }

    *((u8*)PPU_CTRL) = ppu_ctrl_val;  /* Restore increment 1 */
}

void hal_bg_scroll_set(i16 x, i16 y) {
    scroll_x = x;
    scroll_y = y;
    /* Actual scroll update happens in VBlank handler */
}

void hal_bg_fill(u8 tile) {
    u16 i;

    *((u8*)PPU_ADDR) = 0x20;
    *((u8*)PPU_ADDR) = 0x00;

    for (i = 0; i < 960; ++i) {
        *((u8*)PPU_DATA) = tile;
    }
}

/* ---------------------------------------------------------------------------
 * HAL Implementation: Palette
 * --------------------------------------------------------------------------- */

/* NES palette lookup (approximate RGB to NES color) */
/* This is a simplified version - real implementation would use full LUT */
static u8 rgb_to_nes(u8 r, u8 g, u8 b) {
    /* Very basic approximation */
    u8 luma = (r + g + g + b) >> 2;

    if (luma < 32) return 0x0F;     /* Black */
    if (luma < 96) return 0x00;     /* Dark gray */
    if (luma < 160) return 0x10;    /* Light gray */
    return 0x30;                     /* White */

    /* TODO: Proper color matching with full NES palette */
}

void hal_palette_set_color(palette_id_t palette, u8 index, u8 r, u8 g, u8 b) {
    u16 addr = 0x3F00 + (palette << 2) + index;

    *((u8*)PPU_ADDR) = addr >> 8;
    *((u8*)PPU_ADDR) = addr & 0xFF;
    *((u8*)PPU_DATA) = rgb_to_nes(r, g, b);
}

void hal_palette_set_raw(palette_id_t palette, const u8* data) {
    u16 addr = 0x3F00 + (palette << 2);
    u8 i;

    *((u8*)PPU_ADDR) = addr >> 8;
    *((u8*)PPU_ADDR) = addr & 0xFF;

    for (i = 0; i < 4; ++i) {
        *((u8*)PPU_DATA) = data[i];
    }
}

void hal_palette_fade(u8 level) {
    /* TODO: Implement palette fade using emphasis bits or color swapping */
    (void)level;
}

/* ---------------------------------------------------------------------------
 * HAL Implementation: Audio
 * --------------------------------------------------------------------------- */

/* Audio implementation depends on chosen driver (FamiTone2, etc.) */
/* These are stubs - integrate with actual audio driver */

void hal_sfx_play(sfx_id_t id) {
    /* TODO: Call FamiTone2 sfx play */
    (void)id;
}

void hal_sfx_play_on(sfx_id_t id, u8 channel) {
    (void)id;
    (void)channel;
}

void hal_sfx_stop_all(void) {
    /* TODO: Call FamiTone2 sfx stop */
}

void hal_music_play(music_id_t id) {
    /* TODO: Call FamiTone2 music play */
    (void)id;
}

void hal_music_stop(void) {
    /* TODO: Call FamiTone2 music stop */
}

void hal_music_pause(void) {
    /* TODO: Call FamiTone2 music pause */
}

void hal_music_resume(void) {
    /* TODO: Call FamiTone2 music resume */
}

void hal_music_volume(u8 vol) {
    (void)vol;
}

/* ---------------------------------------------------------------------------
 * HAL Implementation: System
 * --------------------------------------------------------------------------- */

void hal_init(void) {
    /* Disable rendering during init */
    *((u8*)PPU_CTRL) = 0;
    *((u8*)PPU_MASK) = 0;

    /* Clear OAM */
    hal_sprite_hide_all();

    /* Initialize state */
    frame_count = 0;
    rand_state = 0xACE1;
    joy1_cur = joy1_prev = 0;
    joy2_cur = joy2_prev = 0;

    /* Wait for PPU warm-up */
    while (!(*((u8*)PPU_STATUS) & 0x80));
    while (!(*((u8*)PPU_STATUS) & 0x80));

    /* Enable rendering */
    ppu_ctrl_val = 0x80;  /* NMI enabled */
    *((u8*)PPU_CTRL) = ppu_ctrl_val;
    *((u8*)PPU_MASK) = 0x1E;  /* Show sprites and background */
}

void hal_wait_vblank(void) {
    /* Save previous input state */
    joy1_prev = joy1_cur;
    joy2_prev = joy2_cur;

    /* Wait for NMI flag or poll VBlank */
    while (!(*((u8*)PPU_STATUS) & 0x80));

    /* Perform OAM DMA */
    *((u8*)OAM_ADDR) = 0;
    *((u8*)OAM_DMA) = 0x02;  /* DMA from $0200 */

    /* Update scroll */
    *((u8*)PPU_SCROLL) = (u8)scroll_x;
    *((u8*)PPU_SCROLL) = (u8)scroll_y;

    /* Read controllers */
    joy1_cur = read_joy(0);
    joy2_cur = read_joy(1);

    /* Increment frame counter */
    frame_count++;
}

u16 hal_frame_count(void) {
    return frame_count;
}

u8 hal_fps(void) {
    return HAL_FPS;
}

void hal_rand_seed(u16 seed) {
    rand_state = seed ? seed : 0xACE1;
}

u8 hal_rand(void) {
    /* Simple LFSR */
    rand_state ^= rand_state << 7;
    rand_state ^= rand_state >> 9;
    rand_state ^= rand_state << 8;
    return (u8)rand_state;
}

u8 hal_rand_range(u8 max) {
    if (max == 0) return 0;
    return hal_rand() % max;
}

u16 hal_capabilities(void) {
    return HAL_PLATFORM_CAPS;
}
