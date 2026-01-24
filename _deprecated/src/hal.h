/*
 * =============================================================================
 * ARDK - Agentic Retro Development Kit
 * hal.h - Hardware Abstraction Layer Interface
 * =============================================================================
 *
 * This file defines the platform-agnostic API that all games use.
 * Each platform (NES, Genesis, etc.) provides its own implementation.
 *
 * LOCKED DECISIONS:
 * - Function signatures defined here are PERMANENT
 * - Adding new functions is allowed, changing existing signatures is NOT
 * - Sprite IDs are 8-bit, positions are fixed8_8
 * - Button masks use standard HAL_BTN_* constants
 *
 * Implementation Notes:
 * - Each platform implements these in hal_<platform>.c
 * - Functions may be macros/inlines for performance
 * - Not all features available on all platforms (check HAL_CAP_* flags)
 * =============================================================================
 */

#ifndef ARDK_HAL_H
#define ARDK_HAL_H

#include "types.h"

/* ---------------------------------------------------------------------------
 * HAL Version
 * --------------------------------------------------------------------------- */

#define HAL_VERSION_MAJOR   1
#define HAL_VERSION_MINOR   1
#define HAL_VERSION_PATCH   0

/* ---------------------------------------------------------------------------
 * Input System
 *
 * Button constants are defined as bit flags for easy combination testing.
 * All platforms map their native buttons to these standard constants.
 * --------------------------------------------------------------------------- */

/* Standard button masks (bit flags) */
#define HAL_BTN_A       0x0001
#define HAL_BTN_B       0x0002
#define HAL_BTN_SELECT  0x0004
#define HAL_BTN_START   0x0008
#define HAL_BTN_UP      0x0010
#define HAL_BTN_DOWN    0x0020
#define HAL_BTN_LEFT    0x0040
#define HAL_BTN_RIGHT   0x0080

/* Extended buttons (for 6-button Genesis, SNES, etc.) */
#define HAL_BTN_C       0x0100  /* Genesis C, SNES Y */
#define HAL_BTN_X       0x0200  /* Genesis X, SNES X */
#define HAL_BTN_Y       0x0400  /* Genesis Y */
#define HAL_BTN_Z       0x0800  /* Genesis Z */
#define HAL_BTN_L       0x1000  /* SNES L, GBA L */
#define HAL_BTN_R       0x2000  /* SNES R, GBA R */

/* Controller port (0 = player 1, 1 = player 2) */
typedef u8 port_t;
#define HAL_PORT_1  0
#define HAL_PORT_2  1

/* Read current button state (returns held buttons) */
u16 hal_input_read(port_t port);

/* Read newly pressed buttons this frame */
u16 hal_input_pressed(port_t port);

/* Read newly released buttons this frame */
u16 hal_input_released(port_t port);

/* ---------------------------------------------------------------------------
 * Sprite System
 *
 * Sprites are referenced by slot ID (0-63 typical, platform-dependent).
 * Position uses fixed-point for subpixel movement.
 * Attributes (flip, priority, palette) packed into single byte.
 * --------------------------------------------------------------------------- */

/* Sprite attribute flags */
#define HAL_SPR_FLIP_H      0x01    /* Flip horizontally */
#define HAL_SPR_FLIP_V      0x02    /* Flip vertically */
#define HAL_SPR_PRIORITY    0x04    /* Behind background (if supported) */
#define HAL_SPR_PAL0        0x00    /* Palette 0 */
#define HAL_SPR_PAL1        0x10    /* Palette 1 */
#define HAL_SPR_PAL2        0x20    /* Palette 2 */
#define HAL_SPR_PAL3        0x30    /* Palette 3 */
#define HAL_SPR_PAL_MASK    0x30

/* Show a sprite at given position
 * slot: Hardware sprite slot (0-MAX_SPRITES)
 * x, y: Position in fixed-point (top-left of sprite)
 * tile: Tile/pattern ID
 * attr: Attribute flags (flip, palette, priority)
 */
void hal_sprite_set(u8 slot, fixed8_8 x, fixed8_8 y, sprite_id_t tile, u8 attr);

/* Hide a sprite (move off-screen or disable) */
void hal_sprite_hide(u8 slot);

/* Hide all sprites */
void hal_sprite_hide_all(void);

/* Set metasprite (multi-tile sprite)
 * Returns number of hardware sprites used */
u8 hal_metasprite_set(u8 start_slot, fixed8_8 x, fixed8_8 y,
                      const u8* data, u8 attr);

/* ---------------------------------------------------------------------------
 * Background/Tilemap System
 *
 * Simple tile-based background manipulation.
 * Coordinate system: tile units (not pixels)
 * --------------------------------------------------------------------------- */

/* Set a single background tile */
void hal_bg_tile_set(u8 x, u8 y, u8 tile);

/* Set a row of tiles */
void hal_bg_row_set(u8 x, u8 y, const u8* tiles, u8 count);

/* Set a column of tiles */
void hal_bg_col_set(u8 x, u8 y, const u8* tiles, u8 count);

/* Set background scroll position (pixels) */
void hal_bg_scroll_set(i16 x, i16 y);

/* Fill entire nametable with tile */
void hal_bg_fill(u8 tile);

/* ---------------------------------------------------------------------------
 * Palette System
 *
 * Palettes are indexed by ID. Colors specified in RGB (platform converts).
 * --------------------------------------------------------------------------- */

/* Set a color in a palette
 * palette: Palette number (0-3 sprite, 4-7 background typical)
 * index: Color index within palette (0-3 typical)
 * r, g, b: Color components (0-255, platform quantizes)
 */
void hal_palette_set_color(palette_id_t palette, u8 index, u8 r, u8 g, u8 b);

/* Set entire palette from packed data (platform-specific format) */
void hal_palette_set_raw(palette_id_t palette, const u8* data);

/* Fade all palettes toward black (0) or white (255)
 * level: 0 = normal, 128 = half brightness, 255 = black/white */
void hal_palette_fade(u8 level);

/* ---------------------------------------------------------------------------
 * Audio System
 *
 * Simple fire-and-forget sound effects and music control.
 * Priority: Music is lower priority, SFX can interrupt
 * --------------------------------------------------------------------------- */

/* Play a sound effect (can overlap, priority-based) */
void hal_sfx_play(sfx_id_t id);

/* Play a sound effect on specific channel (for precise control) */
void hal_sfx_play_on(sfx_id_t id, u8 channel);

/* Stop all sound effects */
void hal_sfx_stop_all(void);

/* Start playing music track (loops by default) */
void hal_music_play(music_id_t id);

/* Stop music */
void hal_music_stop(void);

/* Pause/resume music */
void hal_music_pause(void);
void hal_music_resume(void);

/* Set music volume (0-255) */
void hal_music_volume(u8 vol);

/* ---------------------------------------------------------------------------
 * System Functions
 * --------------------------------------------------------------------------- */

/* Initialize HAL (call once at startup) */
void hal_init(void);

/* Wait for vertical blank (sync point for updates) */
void hal_wait_vblank(void);

/* Get current frame counter (wraps at 65536) */
u16 hal_frame_count(void);

/* Get frames per second for this platform */
u8 hal_fps(void);

/* Seed random number generator */
void hal_rand_seed(u16 seed);

/* Get random number (0-255) */
u8 hal_rand(void);

/* Get random number in range [0, max) */
u8 hal_rand_range(u8 max);

/* ---------------------------------------------------------------------------
 * Platform Capabilities
 *
 * Query what features the current platform supports.
 * Use these to conditionally enable features.
 * --------------------------------------------------------------------------- */

#define HAL_CAP_SPRITE_FLIP     0x0001  /* Hardware sprite flipping */
#define HAL_CAP_SPRITE_ZOOM     0x0002  /* Sprite scaling (Genesis, GBA) */
#define HAL_CAP_BG_SCROLL       0x0004  /* Background scrolling */
#define HAL_CAP_BG_SCROLL_Y     0x0008  /* Vertical scroll (some don't) */
#define HAL_CAP_RASTER_FX       0x0010  /* Scanline effects */
#define HAL_CAP_MULTIPLY        0x0020  /* Hardware multiply */
#define HAL_CAP_DIVIDE          0x0040  /* Hardware divide */
#define HAL_CAP_STEREO          0x0080  /* Stereo audio */
#define HAL_CAP_PCM             0x0100  /* PCM audio samples */
#define HAL_CAP_SAVE            0x0200  /* Battery-backed save */

/* Get platform capability flags */
u16 hal_capabilities(void);

/* Check if specific capability is supported */
#define HAL_HAS_CAP(cap)  ((hal_capabilities() & (cap)) != 0)

/* ---------------------------------------------------------------------------
 * Math Functions
 *
 * Platform-specific implementations optimize for each CPU.
 * NES: 256-byte lookup tables
 * Genesis: Can use MUL instruction or smaller tables
 * GBA: ARM has fast multiply
 *
 * Angle system: 256 units = full circle (like binary radians)
 *   0 = right, 64 = down, 128 = left, 192 = up
 * --------------------------------------------------------------------------- */

/* Sine/Cosine - returns fixed8_8 in range [-256, 256] (-1.0 to 1.0) */
fixed8_8 hal_sin(angle_t angle);
fixed8_8 hal_cos(angle_t angle);

/* Arctangent - returns angle from delta. For homing projectiles, aiming */
angle_t hal_atan2(fixed8_8 dy, fixed8_8 dx);

/* Distance squared (avoids slow sqrt) - for range checks
 * Returns u16 to handle larger distances without overflow
 * To check if distance < threshold: hal_distance_sq(dx,dy) < threshold*threshold */
u16 hal_distance_sq(fixed8_8 dx, fixed8_8 dy);

/* Optional: Approximate distance (faster than sqrt, less accurate)
 * Uses max(|dx|,|dy|) + min(|dx|,|dy|)/2 approximation */
fixed8_8 hal_distance_approx(fixed8_8 dx, fixed8_8 dy);

/* Normalize a vector to unit length (magnitude ~= 256 in fixed8_8)
 * Modifies dx, dy in place. Returns original magnitude. */
fixed8_8 hal_normalize(fixed8_8* dx, fixed8_8* dy);

/* ---------------------------------------------------------------------------
 * Screen Bounds
 *
 * Runtime access to screen dimensions for platform-agnostic bounds checking.
 * These are functions (not macros) so game code doesn't need platform headers.
 * --------------------------------------------------------------------------- */

/* Get screen dimensions */
u16 hal_screen_width(void);
u16 hal_screen_height(void);

/* Get safe area (visible on all TVs, accounts for overscan) */
u16 hal_safe_width(void);
u16 hal_safe_height(void);

/* Bounds checking helpers - returns TRUE if position is on screen */
bool_t hal_on_screen(fixed8_8 x, fixed8_8 y);
bool_t hal_on_screen_rect(fixed8_8 x, fixed8_8 y, u8 w, u8 h);

/* ---------------------------------------------------------------------------
 * Collision Helpers
 *
 * Simple AABB (axis-aligned bounding box) collision detection.
 * Platform-agnostic, but platforms may optimize.
 * --------------------------------------------------------------------------- */

/* Check if two rectangles overlap
 * All parameters in pixels (use FP_TO_INT for fixed-point positions) */
bool_t hal_rect_overlap(i16 ax, i16 ay, u8 aw, u8 ah,
                        i16 bx, i16 by, u8 bw, u8 bh);

/* Check if point is inside rectangle */
bool_t hal_point_in_rect(i16 px, i16 py,
                         i16 rx, i16 ry, u8 rw, u8 rh);

/* ---------------------------------------------------------------------------
 * Timing Helpers
 *
 * Platform-agnostic frame/time conversion.
 * Handles 50Hz (PAL) vs 60Hz (NTSC) differences.
 * --------------------------------------------------------------------------- */

/* Convert between frames and approximate seconds */
u16 hal_frames_to_ms(u16 frames);      /* Frames to milliseconds */
u16 hal_ms_to_frames(u16 ms);          /* Milliseconds to frames */
u8  hal_seconds_to_frames(u8 seconds); /* Seconds to frames (capped at 255) */

/* ---------------------------------------------------------------------------
 * Metasprite Data Format
 *
 * Metasprites are multi-tile sprites stored as arrays of sprite entries.
 * Each entry is 4 bytes:
 *
 *   Byte 0: X offset (signed i8, relative to metasprite origin)
 *   Byte 1: Y offset (signed i8, relative to metasprite origin)
 *   Byte 2: Tile ID
 *   Byte 3: Attribute modifier (XOR'd with base attributes)
 *
 * Terminator: 0x80 in byte 0 (X offset of -128 is invalid, signals end)
 *
 * Example 16x16 metasprite (4 8x8 tiles):
 *   const u8 player_metasprite[] = {
 *       0,  0, 0x00, 0x00,  // Top-left
 *       8,  0, 0x01, 0x00,  // Top-right
 *       0,  8, 0x02, 0x00,  // Bottom-left
 *       8,  8, 0x03, 0x00,  // Bottom-right
 *       0x80                 // End marker
 *   };
 * --------------------------------------------------------------------------- */

/* Metasprite end marker */
#define HAL_METASPRITE_END  0x80

/* ---------------------------------------------------------------------------
 * Platform Limits Query
 *
 * Runtime access to tier-defined limits. Allows game code to query limits
 * without needing platform-specific headers.
 *
 * Limit IDs defined in hal_tiers.h:
 *   HAL_LIMIT_ENTITIES, HAL_LIMIT_ENEMIES, HAL_LIMIT_PROJECTILES,
 *   HAL_LIMIT_PICKUPS, HAL_LIMIT_EFFECTS, HAL_LIMIT_COLLISION, HAL_LIMIT_UPDATE
 * --------------------------------------------------------------------------- */

/* Get a platform limit by ID */
u16 hal_get_limit(u8 limit_id);

/* Convenience macros for common limits */
#define hal_max_entities()      hal_get_limit(0)
#define hal_max_enemies()       hal_get_limit(1)
#define hal_max_projectiles()   hal_get_limit(2)
#define hal_max_pickups()       hal_get_limit(3)
#define hal_max_effects()       hal_get_limit(4)

/* Get current platform tier (MINIMAL=0, STANDARD=1, EXTENDED=2) */
u8 hal_get_tier(void);

/* Get tier name string for debug/logging */
const char* hal_get_tier_name(void);

/* ---------------------------------------------------------------------------
 * Platform Extensions (Graceful Degradation/Expansion)
 *
 * Extensions expose platform-specific features that have no universal equivalent.
 * Game code queries for extensions and gracefully degrades when unavailable.
 *
 * Design principles:
 *   1. QUERY FIRST: Always check hal_has_extension() before using
 *   2. GRACEFUL FALLBACK: Provide alternative when extension unavailable
 *   3. OPT-IN: Extensions never required for core gameplay
 *
 * Usage pattern:
 *   if (hal_has_extension(HAL_EXT_SCANLINE_IRQ)) {
 *       hal_ext_scanline_irq_set(96, water_reflect_callback);
 *   } else {
 *       // Skip water reflection or use simpler effect
 *   }
 * --------------------------------------------------------------------------- */

/* Extension IDs - grouped by category */

/* Display extensions (0x00-0x1F) */
#define HAL_EXT_SCANLINE_IRQ    0x00    /* Per-scanline interrupts (NES MMC3, Genesis HInt) */
#define HAL_EXT_MODE7           0x01    /* SNES Mode 7 rotation/scaling */
#define HAL_EXT_AFFINE_SPRITE   0x02    /* GBA affine sprite transforms */
#define HAL_EXT_HDMA            0x03    /* SNES HDMA (per-scanline DMA) */
#define HAL_EXT_WINDOW          0x04    /* Hardware window/masking (SNES, GBA) */
#define HAL_EXT_MOSAIC          0x05    /* Mosaic effect (SNES, GBA) */
#define HAL_EXT_LINE_SCROLL     0x06    /* Per-line scroll (Genesis, SNES) */

/* Memory/DMA extensions (0x20-0x3F) */
#define HAL_EXT_DMA_QUEUE       0x20    /* Queued DMA during VBlank (Genesis) */
#define HAL_EXT_VRAM_DIRECT     0x21    /* Direct VRAM access outside VBlank */
#define HAL_EXT_WRAM_BANK       0x22    /* Banked work RAM (NES mappers, SNES) */

/* Audio extensions (0x40-0x5F) */
#define HAL_EXT_FM_SYNTH        0x40    /* FM synthesis (Genesis YM2612) */
#define HAL_EXT_WAVETABLE       0x41    /* Wavetable audio (PC Engine) */
#define HAL_EXT_ADPCM           0x42    /* ADPCM samples (Neo Geo, PC Engine CD) */
#define HAL_EXT_STREAMING       0x43    /* Streaming audio (CD systems) */

/* Coprocessor extensions (0x60-0x7F) */
#define HAL_EXT_Z80             0x60    /* Z80 coprocessor (Genesis) */
#define HAL_EXT_SPC700          0x61    /* SPC700 audio CPU (SNES) */
#define HAL_EXT_DSP             0x62    /* DSP coprocessor (SNES DSP-1, etc.) */
#define HAL_EXT_SUPERFX         0x63    /* SuperFX (SNES) */

/* Query if extension is available on current platform */
bool_t hal_has_extension(u8 ext_id);

/* Get extension interface (returns NULL if unavailable)
 * Cast result to appropriate extension struct type */
const void* hal_get_extension(u8 ext_id);

/* ---------------------------------------------------------------------------
 * Extension Callback Types
 *
 * Common callback signatures used by extensions.
 * --------------------------------------------------------------------------- */

/* Scanline IRQ callback - called at specified scanline */
typedef void (*hal_scanline_callback_t)(u8 scanline);

/* VBlank task callback - for DMA queue items */
typedef void (*hal_vblank_task_t)(void);

/* ---------------------------------------------------------------------------
 * Extension: Scanline IRQ (HAL_EXT_SCANLINE_IRQ)
 *
 * Allows triggering code at specific scanlines for:
 *   - Split-screen effects
 *   - Water reflections
 *   - Status bar separation
 *   - Palette changes mid-frame
 *
 * Platforms: NES (MMC3), Genesis (HInt), SNES (IRQ), GBA (HBlank)
 * --------------------------------------------------------------------------- */

typedef struct {
    /* Set scanline IRQ (scanline 0-223 typical, callback called there) */
    void (*set)(u8 scanline, hal_scanline_callback_t callback);

    /* Disable scanline IRQ */
    void (*disable)(void);

    /* Get current scanline (if available, 0xFF if not in HBlank) */
    u8 (*get_scanline)(void);
} HAL_Ext_ScanlineIRQ;

/* ---------------------------------------------------------------------------
 * Extension: DMA Queue (HAL_EXT_DMA_QUEUE)
 *
 * Queue VRAM/CRAM updates to execute during VBlank for flicker-free updates.
 * Essential on Genesis for large tilemap updates.
 *
 * Platforms: Genesis (VDP DMA), SNES (HDMA/DMA)
 * --------------------------------------------------------------------------- */

typedef struct {
    /* Queue a memory transfer (executed next VBlank) */
    bool_t (*queue)(const void* src, u16 dest, u16 size);

    /* Queue a VRAM fill */
    bool_t (*queue_fill)(u16 dest, u16 value, u16 size);

    /* Get bytes remaining in queue budget */
    u16 (*bytes_available)(void);

    /* Flush queue immediately (use sparingly) */
    void (*flush)(void);
} HAL_Ext_DMAQueue;

/* ---------------------------------------------------------------------------
 * Extension: Line Scroll (HAL_EXT_LINE_SCROLL)
 *
 * Per-line horizontal scroll for parallax, water waves, heat distortion.
 *
 * Platforms: Genesis (per-line HScroll), SNES (HDMA scroll), GBA (HBlank)
 * --------------------------------------------------------------------------- */

typedef struct {
    /* Set scroll table (array of 224/240 i16 values, or NULL to disable) */
    void (*set_table)(const i16* scroll_table);

    /* Set single line scroll (for simple effects) */
    void (*set_line)(u8 line, i16 scroll);

    /* Enable/disable line scroll mode */
    void (*enable)(bool_t enabled);
} HAL_Ext_LineScroll;

/* ---------------------------------------------------------------------------
 * Convenience Macros for Extension Access
 * --------------------------------------------------------------------------- */

/* Get typed extension pointer (returns NULL if unavailable) */
#define HAL_GET_EXT_SCANLINE()   ((const HAL_Ext_ScanlineIRQ*)hal_get_extension(HAL_EXT_SCANLINE_IRQ))
#define HAL_GET_EXT_DMA()        ((const HAL_Ext_DMAQueue*)hal_get_extension(HAL_EXT_DMA_QUEUE))
#define HAL_GET_EXT_LINESCROLL() ((const HAL_Ext_LineScroll*)hal_get_extension(HAL_EXT_LINE_SCROLL))

/* ---------------------------------------------------------------------------
 * Parallax System
 *
 * High-level parallax scrolling API. Abstracts platform-specific
 * implementations (NES scanline IRQ, Genesis scroll planes, etc.)
 *
 * See hal_parallax.h for full API and layer structure.
 * --------------------------------------------------------------------------- */

#include "hal_parallax.h"

/* ---------------------------------------------------------------------------
 * CHR/Tileset Animation
 *
 * Animated background tiles (waterfalls, clouds, etc.)
 * NES: CHR bank switching during NMI
 * Genesis: DMA tile updates
 * Software: Frame-based tile swapping
 * --------------------------------------------------------------------------- */

/* Enable/disable CHR animation */
void hal_chr_anim_enable(bool_t enabled);

/* Configure CHR animation
 * base_bank: First CHR bank of animation sequence
 * frame_count: Number of animation frames (1-8)
 * speed: Frames between animation updates (1=fastest, 255=slowest)
 */
void hal_chr_anim_configure(u8 base_bank, u8 frame_count, u8 speed);

/* Get current animation frame (0 to frame_count-1) */
u8 hal_chr_anim_get_frame(void);

/* Force specific animation frame */
void hal_chr_anim_set_frame(u8 frame);

/* ---------------------------------------------------------------------------
 * Platform Constants (defined in hal_config.h per platform)
 * --------------------------------------------------------------------------- */

/* These must be defined by each platform's hal_config.h:
 *
 * HAL_SCREEN_WIDTH     Screen width in pixels
 * HAL_SCREEN_HEIGHT    Screen height in pixels
 * HAL_SAFE_WIDTH       Safe area width (visible on all displays)
 * HAL_SAFE_HEIGHT      Safe area height
 * HAL_MAX_SPRITES      Maximum hardware sprites
 * HAL_SPRITE_WIDTH     Default sprite width
 * HAL_SPRITE_HEIGHT    Default sprite height
 * HAL_TILE_WIDTH       Tile width in pixels
 * HAL_TILE_HEIGHT      Tile height in pixels
 * HAL_BG_WIDTH         Background width in tiles
 * HAL_BG_HEIGHT        Background height in tiles
 * HAL_FPS              Frames per second (50 or 60)
 *
 * Tier system (in hal_tiers.h):
 * HAL_TIER             Platform tier (0=MINIMAL, 1=STANDARD, 2=EXTENDED)
 * HAL_MAX_ENTITIES     Max entity pool size
 * HAL_MAX_ENEMIES      Max simultaneous enemies
 * HAL_MAX_PROJECTILES  Max simultaneous projectiles
 * HAL_MAX_PICKUPS      Max pickups on screen
 * HAL_MAX_EFFECTS      Max visual effects
 */

#endif /* ARDK_HAL_H */
