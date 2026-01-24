/*
 * =============================================================================
 * ARDK - Genesis/Mega Drive HAL Implementation
 * hal_genesis.c - Hardware Abstraction Layer for Genesis
 * =============================================================================
 *
 * This file implements the HAL interface for the Genesis/Mega Drive platform.
 * Uses SGDK conventions where applicable.
 *
 * Build with: SGDK (make) or m68k-elf-gcc directly
 * =============================================================================
 */

#include "../hal.h"
#include "hal_config.h"

/* ---------------------------------------------------------------------------
 * Type aliases for 68000
 * --------------------------------------------------------------------------- */

typedef volatile u16* vu16;
typedef volatile u32* vu32;

/* ---------------------------------------------------------------------------
 * Hardware Registers
 * --------------------------------------------------------------------------- */

#define VDP_DATA_W      (*((vu16)VDP_DATA))
#define VDP_DATA_L      (*((vu32)VDP_DATA))
#define VDP_CTRL_W      (*((vu16)VDP_CTRL))
#define VDP_CTRL_L      (*((vu32)VDP_CTRL))

/* ---------------------------------------------------------------------------
 * State Variables
 * --------------------------------------------------------------------------- */

static u16 frame_count;
static u16 rand_state;

/* Input state */
static u16 joy1_cur;
static u16 joy1_prev;
static u16 joy2_cur;
static u16 joy2_prev;

/* Scroll state */
static i16 scroll_x;
static i16 scroll_y;

/* Sprite table shadow (in work RAM, DMA to VRAM) */
/* Each sprite entry: 8 bytes */
/* Format: YYYY YYYY | SSSS HHHH | NNNN NNNN NNNN NNNN | XXXX XXXX */
/* Y = Y pos, S = size, H = H-link, N = next sprite, tile, flip, palette */
/* We use a simpler format here and convert during DMA */
static u16 sprite_buffer[HAL_MAX_SPRITES * 4];
static u8 sprite_count;

/* ---------------------------------------------------------------------------
 * VDP Helper Functions
 * --------------------------------------------------------------------------- */

/* Write VDP register */
static void vdp_reg_set(u8 reg, u8 value) {
    VDP_CTRL_W = 0x8000 | (reg << 8) | value;
}

/* Set VRAM write address */
static void vdp_vram_addr(u16 addr) {
    VDP_CTRL_L = 0x40000000 | ((u32)(addr & 0x3FFF) << 16) | ((addr >> 14) & 3);
}

/* Set CRAM (palette) write address */
static void vdp_cram_addr(u16 addr) {
    VDP_CTRL_L = 0xC0000000 | ((u32)(addr & 0x3FFF) << 16);
}

/* ---------------------------------------------------------------------------
 * HAL Implementation: Input
 *
 * Genesis uses a multiplexed controller protocol.
 * 3-button: TH pin toggles to read different button groups
 * 6-button: Multiple TH toggles within a frame
 * --------------------------------------------------------------------------- */

/* Read 3-button controller */
static u16 read_joy_3btn(u8 port) {
    volatile u8* data_port = (port == 0) ?
        (volatile u8*)IO_DATA1 : (volatile u8*)IO_DATA2;
    volatile u8* ctrl_port = (port == 0) ?
        (volatile u8*)IO_CTRL1 : (volatile u8*)IO_CTRL2;

    u16 result = 0;
    u8 val;

    /* Set TH as output, other pins as input */
    *ctrl_port = 0x40;

    /* TH = 1: Read Up, Down, Left, Right, B, C */
    *data_port = 0x40;
    val = *data_port;

    if (!(val & 0x01)) result |= HAL_BTN_UP;
    if (!(val & 0x02)) result |= HAL_BTN_DOWN;
    if (!(val & 0x04)) result |= HAL_BTN_LEFT;
    if (!(val & 0x08)) result |= HAL_BTN_RIGHT;
    if (!(val & 0x10)) result |= HAL_BTN_B;
    if (!(val & 0x20)) result |= HAL_BTN_C;

    /* TH = 0: Read A, Start */
    *data_port = 0x00;
    val = *data_port;

    if (!(val & 0x10)) result |= HAL_BTN_A;
    if (!(val & 0x20)) result |= HAL_BTN_START;

    return result;
}

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
    u16* spr = &sprite_buffer[slot * 4];

    /* Convert fixed-point to screen coordinates */
    /* Genesis sprite Y: 128 = top of screen */
    /* Genesis sprite X: 128 = left of screen */
    i16 px = (x >> 8) + 128;
    i16 py = (y >> 8) + 128;

    /* Word 0: Y position (10 bits) + size/link (6 bits) */
    /* For 8x8 sprite: size = 0 */
    spr[0] = (py & 0x3FF);

    /* Word 1: Size (4 bits) + Link (7 bits) */
    /* Size: 0=8x8, 1=8x16, 2=8x24, 3=8x32 (horizontal)
     *       + 4,8,12 for vertical sizing */
    spr[1] = (slot + 1) & 0x7F;  /* Link to next sprite */

    /* Word 2: Priority, palette, flip, pattern */
    /* Bit 15: Priority (1 = high)
     * Bit 14-13: Palette (0-3)
     * Bit 12: V-flip
     * Bit 11: H-flip
     * Bit 10-0: Pattern index */
    spr[2] = tile |
             ((attr & HAL_SPR_PRIORITY) ? 0x8000 : 0) |
             (((attr >> 4) & 3) << 13) |
             ((attr & HAL_SPR_FLIP_V) ? 0x1000 : 0) |
             ((attr & HAL_SPR_FLIP_H) ? 0x0800 : 0);

    /* Word 3: X position (10 bits) */
    spr[3] = px & 0x3FF;

    if (slot >= sprite_count) {
        sprite_count = slot + 1;
    }
}

void hal_sprite_hide(u8 slot) {
    u16* spr = &sprite_buffer[slot * 4];
    spr[0] = 0;     /* Y = 0 (off screen top) */
    spr[3] = 0;     /* X = 0 */
}

void hal_sprite_hide_all(void) {
    u8 i;
    for (i = 0; i < HAL_MAX_SPRITES; ++i) {
        sprite_buffer[i * 4] = 0;
        sprite_buffer[i * 4 + 1] = 0;
        sprite_buffer[i * 4 + 2] = 0;
        sprite_buffer[i * 4 + 3] = 0;
    }
    sprite_count = 0;
}

u8 hal_metasprite_set(u8 start_slot, fixed8_8 x, fixed8_8 y,
                      const u8* data, u8 attr) {
    u8 slot = start_slot;
    i8 dx, dy;

    while (slot < HAL_MAX_SPRITES) {
        dx = (i8)*data++;
        if (dx == (i8)0x80) break;

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

void hal_bg_tile_set(u8 x, u8 y, u8 tile) {
    u16 offset = ((u16)y * HAL_BG_WIDTH + x) * 2;
    vdp_vram_addr(VRAM_PLANE_A + offset);
    VDP_DATA_W = tile;
}

void hal_bg_row_set(u8 x, u8 y, const u8* tiles, u8 count) {
    u16 offset = ((u16)y * HAL_BG_WIDTH + x) * 2;
    u8 i;

    vdp_vram_addr(VRAM_PLANE_A + offset);

    for (i = 0; i < count; ++i) {
        VDP_DATA_W = tiles[i];
    }
}

void hal_bg_col_set(u8 x, u8 y, const u8* tiles, u8 count) {
    u8 i;

    for (i = 0; i < count; ++i) {
        hal_bg_tile_set(x, y + i, tiles[i]);
    }
}

void hal_bg_scroll_set(i16 x, i16 y) {
    scroll_x = x;
    scroll_y = y;

    /* Update horizontal scroll (HSCROLL table) */
    vdp_vram_addr(VRAM_HSCROLL);
    VDP_DATA_W = -scroll_x;     /* Genesis scrolls in opposite direction */

    /* Update vertical scroll (VSRAM) */
    VDP_CTRL_L = 0x40000010;    /* VSRAM write */
    VDP_DATA_W = scroll_y;
}

void hal_bg_fill(u8 tile) {
    u16 i;
    u16 size = HAL_BG_WIDTH * HAL_BG_HEIGHT;

    vdp_vram_addr(VRAM_PLANE_A);

    for (i = 0; i < size; ++i) {
        VDP_DATA_W = tile;
    }
}

/* ---------------------------------------------------------------------------
 * HAL Implementation: Palette
 * --------------------------------------------------------------------------- */

void hal_palette_set_color(palette_id_t palette, u8 index, u8 r, u8 g, u8 b) {
    /* Genesis color: 0000BBB0GGG0RRR0 */
    /* 3 bits per channel */
    u16 color = ((b >> 5) << 9) | ((g >> 5) << 5) | ((r >> 5) << 1);
    u16 addr = (palette * 32) + (index * 2);

    vdp_cram_addr(addr);
    VDP_DATA_W = color;
}

void hal_palette_set_raw(palette_id_t palette, const u8* data) {
    u16 addr = palette * 32;
    u8 i;

    vdp_cram_addr(addr);

    /* Assume data is already in Genesis format (16 colors, 2 bytes each) */
    for (i = 0; i < 16; ++i) {
        VDP_DATA_W = (data[i*2] << 8) | data[i*2 + 1];
    }
}

void hal_palette_fade(u8 level) {
    /* TODO: Implement palette fade */
    (void)level;
}

/* ---------------------------------------------------------------------------
 * HAL Implementation: Audio
 *
 * Genesis audio is complex (YM2612 + Z80 + PSG).
 * These are stubs - integrate with Echo, XGM, or custom driver.
 * --------------------------------------------------------------------------- */

void hal_sfx_play(sfx_id_t id) {
    /* TODO: Call sound driver */
    (void)id;
}

void hal_sfx_play_on(sfx_id_t id, u8 channel) {
    (void)id;
    (void)channel;
}

void hal_sfx_stop_all(void) {
    /* TODO: Call sound driver */
}

void hal_music_play(music_id_t id) {
    /* TODO: Call sound driver */
    (void)id;
}

void hal_music_stop(void) {
    /* TODO: Call sound driver */
}

void hal_music_pause(void) {
    /* TODO */
}

void hal_music_resume(void) {
    /* TODO */
}

void hal_music_volume(u8 vol) {
    (void)vol;
}

/* ---------------------------------------------------------------------------
 * HAL Implementation: System
 * --------------------------------------------------------------------------- */

void hal_init(void) {
    /* Basic VDP init (SGDK does this more thoroughly) */

    /* Mode set registers */
    vdp_reg_set(0x00, 0x04);    /* Mode 1: H-INT off */
    vdp_reg_set(0x01, 0x44);    /* Mode 2: Display on, V-INT on */
    vdp_reg_set(0x0B, 0x00);    /* Mode 3: Full scroll */
    vdp_reg_set(0x0C, 0x81);    /* Mode 4: H40 mode, no interlace */

    /* Plane addresses */
    vdp_reg_set(0x02, VRAM_PLANE_A >> 10);
    vdp_reg_set(0x03, VRAM_WINDOW >> 10);
    vdp_reg_set(0x04, VRAM_PLANE_B >> 13);
    vdp_reg_set(0x05, VRAM_SPRITES >> 9);
    vdp_reg_set(0x0D, VRAM_HSCROLL >> 10);

    /* Plane size (64x32) */
    vdp_reg_set(0x10, PLANE_64x32);

    /* Auto-increment 2 bytes */
    vdp_reg_set(0x0F, 0x02);

    /* Clear sprites */
    hal_sprite_hide_all();

    /* Initialize state */
    frame_count = 0;
    rand_state = 0xACE1;
    joy1_cur = joy1_prev = 0;
    joy2_cur = joy2_prev = 0;
}

void hal_wait_vblank(void) {
    /* Save previous input */
    joy1_prev = joy1_cur;
    joy2_prev = joy2_cur;

    /* Wait for VBlank (bit 3 of VDP status) */
    while (!(VDP_CTRL_W & 0x08));

    /* DMA sprite table to VRAM */
    /* (In real implementation, use DMA for speed) */
    {
        u8 i;
        vdp_vram_addr(VRAM_SPRITES);
        for (i = 0; i < sprite_count * 4; ++i) {
            VDP_DATA_W = sprite_buffer[i];
        }
        /* End of sprite list (link = 0) */
        if (sprite_count > 0) {
            vdp_vram_addr(VRAM_SPRITES + (sprite_count - 1) * 8 + 2);
            VDP_DATA_W = sprite_buffer[(sprite_count - 1) * 4 + 1] & 0xFF80;
        }
    }

    /* Read controllers */
    joy1_cur = read_joy_3btn(0);
    joy2_cur = read_joy_3btn(1);

    /* Wait for VBlank end */
    while (VDP_CTRL_W & 0x08);

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
