/**
 * =============================================================================
 * ARDK HAL - Parallax Scrolling Abstraction Layer
 * =============================================================================
 * Cross-platform parallax scrolling support.
 *
 * Platform implementations:
 *   NES:     MMC3 scanline IRQ + CHR bank switching
 *   Genesis: Dual scroll planes + line scroll table
 *   SNES:    Mode 1 scroll planes + HDMA
 *   GBA:     Multiple BG layers + affine
 *   RETRO_PC: Software blitting (unlimited layers)
 *
 * Design Philosophy:
 *   - Define layers at highest tier (RETRO_PC: 8 layers)
 *   - Scale down for lower tiers
 *   - Platform HAL implements actual rendering
 * =============================================================================
 */

#ifndef HAL_PARALLAX_H
#define HAL_PARALLAX_H

#include "types.h"

/* Note: This header is designed to be included from hal.h after platform
 * configuration is established. Platform-specific HAL_PARALLAX_* macros
 * should be defined in the platform's hal_config.h */

/* -----------------------------------------------------------------------------
 * Platform-Specific Layer Limits
 * -------------------------------------------------------------------------- */

#if defined(HAL_PLATFORM_NES)
    /* NES: 3 layers via MMC3 scanline IRQ */
    #define HAL_PARALLAX_MAX_LAYERS     3
    #define HAL_PARALLAX_SCANLINE_IRQ   1   /* Uses IRQ for mid-screen changes */
    #define HAL_PARALLAX_CHR_SWITCH     1   /* Can switch CHR banks per layer */

#elif defined(HAL_PLATFORM_SMS)
    /* SMS: 2 layers (BG + sprites as pseudo-layer) */
    #define HAL_PARALLAX_MAX_LAYERS     2
    #define HAL_PARALLAX_SCANLINE_IRQ   1   /* Line interrupt available */
    #define HAL_PARALLAX_CHR_SWITCH     0   /* No runtime tile switching */

#elif defined(HAL_PLATFORM_GENESIS)
    /* Genesis: 4 layers (Plane A, Plane B, Window, line scroll) */
    #define HAL_PARALLAX_MAX_LAYERS     4
    #define HAL_PARALLAX_SCANLINE_IRQ   1   /* H-INT available */
    #define HAL_PARALLAX_CHR_SWITCH     0   /* DMA tile upload instead */
    #define HAL_PARALLAX_LINE_SCROLL    1   /* Per-line scroll tables */

#elif defined(HAL_PLATFORM_SNES)
    /* SNES: 4 layers (Mode 1) + HDMA for effects */
    #define HAL_PARALLAX_MAX_LAYERS     4
    #define HAL_PARALLAX_SCANLINE_IRQ   1   /* H-blank IRQ + HDMA */
    #define HAL_PARALLAX_CHR_SWITCH     1   /* VRAM DMA */
    #define HAL_PARALLAX_HDMA           1   /* HDMA for smooth gradients */

#elif defined(HAL_PLATFORM_GBA)
    /* GBA: 4 BG layers (Mode 0) or 2 affine (Mode 1/2) */
    #define HAL_PARALLAX_MAX_LAYERS     4
    #define HAL_PARALLAX_SCANLINE_IRQ   1   /* H-blank */
    #define HAL_PARALLAX_CHR_SWITCH     1   /* DMA */
    #define HAL_PARALLAX_AFFINE         1   /* Rotation/scaling on layers 2-3 */

#elif defined(HAL_PLATFORM_RETRO_PC) || defined(HAL_PLATFORM_DOS_VGA)
    /* RETRO_PC: Software rendering, practical limit only */
    #define HAL_PARALLAX_MAX_LAYERS     8
    #define HAL_PARALLAX_SCANLINE_IRQ   0   /* Software handles all */
    #define HAL_PARALLAX_CHR_SWITCH     0   /* N/A */
    #define HAL_PARALLAX_SOFTWARE       1   /* Full software blitting */

#else
    /* Default/unknown platform */
    #define HAL_PARALLAX_MAX_LAYERS     2
    #define HAL_PARALLAX_SCANLINE_IRQ   0
    #define HAL_PARALLAX_CHR_SWITCH     0
#endif

/* -----------------------------------------------------------------------------
 * Parallax Layer Structure
 * -------------------------------------------------------------------------- */

/**
 * Layer flags (matches ASM LAYER_FLAG_* in parallax.asm)
 */
#define HAL_PARALLAX_FLAG_ENABLED       0x01    /* Layer is active */
#define HAL_PARALLAX_FLAG_ANIMATE       0x02    /* CHR/tiles animate */
#define HAL_PARALLAX_FLAG_WRAP_X        0x04    /* Wrap horizontally */
#define HAL_PARALLAX_FLAG_WRAP_Y        0x08    /* Wrap vertically */
#define HAL_PARALLAX_FLAG_PRIORITY_HIGH 0x10    /* Draw above sprites */

/**
 * Parallax layer definition
 *
 * Each layer scrolls independently based on camera position.
 * Speed is 0-255 where:
 *   0   = static (doesn't move)
 *   64  = 25% of camera speed (distant background)
 *   128 = 50% of camera speed (mid-ground)
 *   192 = 75% of camera speed
 *   255 = 100% of camera speed (foreground)
 *
 * NOTE: Two structure sizes exist for memory efficiency:
 *   - Compact (8 bytes): For MINIMAL tier (NES, GB, SMS)
 *   - Full (12 bytes): For STANDARD+ tiers (Genesis, SNES, GBA)
 *
 * The compact version saves RAM on 8-bit platforms.
 * Assembly hot paths (engines/6502/nes/hal_native/parallax.asm) use the
 * compact layout directly.
 */

#if defined(HAL_PLATFORM_NES) || defined(HAL_PLATFORM_SMS) || defined(HAL_PLATFORM_GB)

/**
 * Compact parallax layer (8 bytes) - for 8-bit platforms
 *
 * Layout matches engines/6502/nes/hal_native/parallax.asm:
 *   Offset 0: scanline     (u8)  - Scanline trigger (0-239)
 *   Offset 1: scroll_x_lo  (u8)  - X scroll fractional
 *   Offset 2: scroll_x_hi  (u8)  - X scroll pixel
 *   Offset 3: scroll_y     (u8)  - Y scroll (pixel only, no subpixel)
 *   Offset 4: tileset_id   (u8)  - CHR bank / tileset
 *   Offset 5: speed        (u8)  - Speed factor (0-255)
 *   Offset 6: flags        (u8)  - HAL_PARALLAX_FLAG_* bits
 *   Offset 7: reserved     (u8)  - Future use
 */
typedef struct {
    u8   scanline;      /**< Scanline where this layer starts (0-239 NES) */
    u8   scroll_x_lo;   /**< X scroll low byte (fractional) */
    u8   scroll_x_hi;   /**< X scroll high byte (pixel) */
    u8   scroll_y;      /**< Y scroll (pixel only on 8-bit) */
    u8   tileset_id;    /**< Platform-specific tileset/CHR bank */
    u8   speed;         /**< Speed factor (0-255, 128=50%) */
    u8   flags;         /**< HAL_PARALLAX_FLAG_* bits */
    u8   reserved;      /**< Reserved for future use */
} hal_parallax_layer_t;

#define HAL_PARALLAX_LAYER_SIZE  8

/* Accessors for compact structure scroll_x as 16-bit value */
#define HAL_PARALLAX_GET_SCROLL_X(layer) \
    ((i16)(((u16)(layer)->scroll_x_hi << 8) | (layer)->scroll_x_lo))
#define HAL_PARALLAX_SET_SCROLL_X(layer, val) do { \
    (layer)->scroll_x_lo = (u8)((val) & 0xFF); \
    (layer)->scroll_x_hi = (u8)(((val) >> 8) & 0xFF); \
} while(0)

/* Compatibility: map speed_x to speed for portable code */
#define speed_x speed

#else

/**
 * Full parallax layer (12 bytes) - for 16-bit+ platforms
 *
 * Provides additional features:
 *   - Separate X/Y speed factors
 *   - Full 16-bit scroll for both axes
 *   - Palette selection per layer
 */
typedef struct {
    u8   scanline;      /**< Scanline where this layer starts (0-239 NES) */
    u8   pad0;          /**< Padding for alignment */
    i16  scroll_x;      /**< Current X scroll (8.8 fixed point) */
    i16  scroll_y;      /**< Current Y scroll (8.8 fixed point) */
    u8   speed_x;       /**< X speed factor (0-255, 128=50%) */
    u8   speed_y;       /**< Y speed factor (usually same as speed_x) */
    u8   tileset_id;    /**< Platform-specific tileset/CHR bank */
    u8   palette_id;    /**< Palette to use (if applicable) */
    u8   flags;         /**< HAL_PARALLAX_FLAG_* bits */
    u8   reserved;      /**< Padding for alignment */
} hal_parallax_layer_t;

#define HAL_PARALLAX_LAYER_SIZE  12

/* Accessors for full structure (direct access) */
#define HAL_PARALLAX_GET_SCROLL_X(layer)        ((layer)->scroll_x)
#define HAL_PARALLAX_SET_SCROLL_X(layer, val)   ((layer)->scroll_x = (val))

#endif

/* -----------------------------------------------------------------------------
 * Parallax System State
 * -------------------------------------------------------------------------- */

typedef struct {
    hal_parallax_layer_t layers[HAL_PARALLAX_MAX_LAYERS];
    u8   layer_count;       /**< Number of active layers */
    u8   active;            /**< System enabled flag */
    i16  camera_x;          /**< Current camera X (8.8 fixed point) */
    i16  camera_y;          /**< Current camera Y (8.8 fixed point) */
} hal_parallax_state_t;

/* -----------------------------------------------------------------------------
 * API Functions (Platform-implemented)
 * -------------------------------------------------------------------------- */

/**
 * Initialize parallax system
 * Call once at game start
 */
void hal_parallax_init(void);

/**
 * Configure a parallax layer
 *
 * @param layer_id  Layer index (0 to HAL_PARALLAX_MAX_LAYERS-1)
 * @param layer     Layer configuration
 */
void hal_parallax_set_layer(u8 layer_id, const hal_parallax_layer_t* layer);

/**
 * Enable or disable a layer
 *
 * @param layer_id  Layer index
 * @param enabled   Non-zero to enable
 */
void hal_parallax_enable_layer(u8 layer_id, u8 enabled);

/**
 * Update all layers based on camera position
 * Call each frame before rendering
 *
 * @param camera_x  Camera X position (8.8 fixed point)
 * @param camera_y  Camera Y position (8.8 fixed point)
 */
void hal_parallax_update(i16 camera_x, i16 camera_y);

/**
 * Render parallax layers
 * Platform-specific implementation
 * NES: Called during NMI to setup IRQs
 * Genesis: Updates scroll plane registers
 * Software: Blits layers to framebuffer
 */
void hal_parallax_render(void);

/**
 * Disable parallax system entirely
 */
void hal_parallax_shutdown(void);

/* -----------------------------------------------------------------------------
 * Convenience Macros
 * -------------------------------------------------------------------------- */

/**
 * Create a simple 2-layer parallax setup (common case)
 * Layer 0: Sky/distant background (25% speed)
 * Layer 1: Ground/foreground (100% speed)
 *
 * Works with both compact (8-byte) and full (12-byte) layer structures.
 */
#if defined(HAL_PLATFORM_NES) || defined(HAL_PLATFORM_SMS) || defined(HAL_PLATFORM_GB)
/* Compact structure version */
#define HAL_PARALLAX_SIMPLE_2LAYER(sky_tileset, ground_tileset, split_line) \
    do { \
        hal_parallax_layer_t sky = { \
            .scanline = 0, \
            .scroll_x_lo = 0, .scroll_x_hi = 0, .scroll_y = 0, \
            .speed = 64, \
            .tileset_id = (sky_tileset), \
            .flags = HAL_PARALLAX_FLAG_ENABLED | HAL_PARALLAX_FLAG_WRAP_X \
        }; \
        hal_parallax_layer_t ground = { \
            .scanline = (split_line), \
            .scroll_x_lo = 0, .scroll_x_hi = 0, .scroll_y = 0, \
            .speed = 255, \
            .tileset_id = (ground_tileset), \
            .flags = HAL_PARALLAX_FLAG_ENABLED | HAL_PARALLAX_FLAG_WRAP_X \
        }; \
        hal_parallax_set_layer(0, &sky); \
        hal_parallax_set_layer(1, &ground); \
    } while(0)

#define HAL_PARALLAX_3LAYER(bg_tile, mid_tile, fg_tile, line1, line2) \
    do { \
        hal_parallax_layer_t bg = { \
            .scanline = 0, \
            .scroll_x_lo = 0, .scroll_x_hi = 0, .scroll_y = 0, \
            .speed = 64, \
            .tileset_id = (bg_tile), \
            .flags = HAL_PARALLAX_FLAG_ENABLED | HAL_PARALLAX_FLAG_WRAP_X \
        }; \
        hal_parallax_layer_t mid = { \
            .scanline = (line1), \
            .scroll_x_lo = 0, .scroll_x_hi = 0, .scroll_y = 0, \
            .speed = 128, \
            .tileset_id = (mid_tile), \
            .flags = HAL_PARALLAX_FLAG_ENABLED | HAL_PARALLAX_FLAG_WRAP_X \
        }; \
        hal_parallax_layer_t fg = { \
            .scanline = (line2), \
            .scroll_x_lo = 0, .scroll_x_hi = 0, .scroll_y = 0, \
            .speed = 255, \
            .tileset_id = (fg_tile), \
            .flags = HAL_PARALLAX_FLAG_ENABLED | HAL_PARALLAX_FLAG_WRAP_X \
        }; \
        hal_parallax_set_layer(0, &bg); \
        hal_parallax_set_layer(1, &mid); \
        hal_parallax_set_layer(2, &fg); \
    } while(0)

#else
/* Full structure version */
#define HAL_PARALLAX_SIMPLE_2LAYER(sky_tileset, ground_tileset, split_line) \
    do { \
        hal_parallax_layer_t sky = { \
            .scanline = 0, \
            .scroll_x = 0, .scroll_y = 0, \
            .speed_x = 64, .speed_y = 0, \
            .tileset_id = (sky_tileset), \
            .flags = HAL_PARALLAX_FLAG_ENABLED | HAL_PARALLAX_FLAG_WRAP_X \
        }; \
        hal_parallax_layer_t ground = { \
            .scanline = (split_line), \
            .scroll_x = 0, .scroll_y = 0, \
            .speed_x = 255, .speed_y = 0, \
            .tileset_id = (ground_tileset), \
            .flags = HAL_PARALLAX_FLAG_ENABLED | HAL_PARALLAX_FLAG_WRAP_X \
        }; \
        hal_parallax_set_layer(0, &sky); \
        hal_parallax_set_layer(1, &ground); \
    } while(0)

/**
 * Create a 3-layer parallax setup
 * Layer 0: Distant background (25% speed)
 * Layer 1: Mid-ground (50% speed)
 * Layer 2: Foreground (100% speed)
 */
#define HAL_PARALLAX_3LAYER(bg_tile, mid_tile, fg_tile, line1, line2) \
    do { \
        hal_parallax_layer_t bg = { \
            .scanline = 0, \
            .speed_x = 64, .speed_y = 0, \
            .tileset_id = (bg_tile), \
            .flags = HAL_PARALLAX_FLAG_ENABLED | HAL_PARALLAX_FLAG_WRAP_X \
        }; \
        hal_parallax_layer_t mid = { \
            .scanline = (line1), \
            .speed_x = 128, .speed_y = 0, \
            .tileset_id = (mid_tile), \
            .flags = HAL_PARALLAX_FLAG_ENABLED | HAL_PARALLAX_FLAG_WRAP_X \
        }; \
        hal_parallax_layer_t fg = { \
            .scanline = (line2), \
            .speed_x = 255, .speed_y = 0, \
            .tileset_id = (fg_tile), \
            .flags = HAL_PARALLAX_FLAG_ENABLED | HAL_PARALLAX_FLAG_WRAP_X \
        }; \
        hal_parallax_set_layer(0, &bg); \
        hal_parallax_set_layer(1, &mid); \
        hal_parallax_set_layer(2, &fg); \
    } while(0)
#endif

/* -----------------------------------------------------------------------------
 * Tier-Based Defaults
 * -------------------------------------------------------------------------- */

/**
 * Recommended parallax complexity by tier
 *
 * MINIMAL (NES, GB):
 *   - 2-3 layers maximum
 *   - Horizontal scroll only (no vertical parallax)
 *   - Limited CHR animation frames (4)
 *
 * MINIMAL_PLUS (SMS, MSX2):
 *   - 2 layers maximum (no mid-frame switching)
 *   - Line interrupt for split effects
 *
 * STANDARD (Genesis, SNES):
 *   - 4 layers via hardware scroll planes
 *   - Per-line scroll for wave/heat effects
 *   - Both X and Y parallax
 *
 * STANDARD_PLUS (Neo Geo):
 *   - 4+ layers, large tileset support
 *   - Smooth sub-pixel scrolling
 *
 * EXTENDED (GBA, DS):
 *   - 4 layers + affine effects
 *   - Rotation/scaling on background layers
 */

/* Tier layer limits (for runtime scaling) */
static const u8 hal_parallax_tier_limits[] = {
    3,  /* MINIMAL: NES/GB - IRQ limited */
    2,  /* MINIMAL_PLUS: SMS - line int only */
    4,  /* STANDARD: Genesis/SNES - dual planes */
    4,  /* STANDARD_PLUS: Neo Geo */
    4   /* EXTENDED: GBA/DS */
};

#endif /* HAL_PARALLAX_H */
