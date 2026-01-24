/*
 * =============================================================================
 * ARDK - Agentic Retro Development Kit
 * hal_common.c - Platform-Agnostic HAL Implementations
 * =============================================================================
 *
 * This file contains HAL function implementations that are pure computation
 * with no hardware dependencies. These work identically on all platforms.
 *
 * Platform-specific implementations (in hal_nes.c, hal_genesis.c, etc.) can
 * override these if they have optimized versions.
 *
 * To use: Link this file with your platform-specific HAL.
 * =============================================================================
 */

#include "hal.h"

/* Platform config needed for screen dimensions and FPS */
/* Include the appropriate one based on build target */
#if defined(PLATFORM_NES)
    #include "nes/hal_config.h"
#elif defined(PLATFORM_GENESIS)
    #include "genesis/hal_config.h"
#elif defined(PLATFORM_SNES)
    #include "snes/hal_config.h"
#elif defined(PLATFORM_GBA)
    #include "gba/hal_config.h"
#else
    /* Default fallback values for testing */
    #ifndef HAL_SCREEN_WIDTH
        #define HAL_SCREEN_WIDTH    256
    #endif
    #ifndef HAL_SCREEN_HEIGHT
        #define HAL_SCREEN_HEIGHT   240
    #endif
    #ifndef HAL_SAFE_WIDTH
        #define HAL_SAFE_WIDTH      256
    #endif
    #ifndef HAL_SAFE_HEIGHT
        #define HAL_SAFE_HEIGHT     224
    #endif
    #ifndef HAL_FPS
        #define HAL_FPS             60
    #endif
#endif

/* ===========================================================================
 * Collision Helpers
 * =========================================================================== */

/*
 * Check if two axis-aligned rectangles overlap.
 * Uses the separating axis theorem - if there's a gap on any axis, no overlap.
 */
bool_t hal_rect_overlap(i16 ax, i16 ay, u8 aw, u8 ah,
                        i16 bx, i16 by, u8 bw, u8 bh) {
    /* Check for gap on X axis */
    if (ax + aw <= bx) return FALSE;  /* A is left of B */
    if (bx + bw <= ax) return FALSE;  /* B is left of A */

    /* Check for gap on Y axis */
    if (ay + ah <= by) return FALSE;  /* A is above B */
    if (by + bh <= ay) return FALSE;  /* B is above A */

    /* No gaps found - rectangles overlap */
    return TRUE;
}

/*
 * Check if a point is inside a rectangle.
 */
bool_t hal_point_in_rect(i16 px, i16 py,
                         i16 rx, i16 ry, u8 rw, u8 rh) {
    if (px < rx) return FALSE;
    if (py < ry) return FALSE;
    if (px >= rx + rw) return FALSE;
    if (py >= ry + rh) return FALSE;
    return TRUE;
}

/* ===========================================================================
 * Screen Bounds
 * =========================================================================== */

u16 hal_screen_width(void) {
    return HAL_SCREEN_WIDTH;
}

u16 hal_screen_height(void) {
    return HAL_SCREEN_HEIGHT;
}

u16 hal_safe_width(void) {
    return HAL_SAFE_WIDTH;
}

u16 hal_safe_height(void) {
    return HAL_SAFE_HEIGHT;
}

/*
 * Check if a point is on screen (using fixed-point position).
 */
bool_t hal_on_screen(fixed8_8 x, fixed8_8 y) {
    i16 px = FP_TO_INT(x);
    i16 py = FP_TO_INT(y);

    if (px < 0 || px >= HAL_SCREEN_WIDTH) return FALSE;
    if (py < 0 || py >= HAL_SCREEN_HEIGHT) return FALSE;
    return TRUE;
}

/*
 * Check if a rectangle is at least partially on screen.
 */
bool_t hal_on_screen_rect(fixed8_8 x, fixed8_8 y, u8 w, u8 h) {
    i16 px = FP_TO_INT(x);
    i16 py = FP_TO_INT(y);

    /* Off left or right */
    if (px + w <= 0 || px >= HAL_SCREEN_WIDTH) return FALSE;
    /* Off top or bottom */
    if (py + h <= 0 || py >= HAL_SCREEN_HEIGHT) return FALSE;
    return TRUE;
}

/* ===========================================================================
 * Timing Helpers
 * =========================================================================== */

/*
 * Convert frames to milliseconds.
 * At 60 FPS: 1 frame = 16.67ms
 * At 50 FPS: 1 frame = 20ms
 */
u16 hal_frames_to_ms(u16 frames) {
#if HAL_FPS == 60
    /* 1000ms / 60fps = 16.67ms per frame */
    /* Use (frames * 1000 + 30) / 60 for rounding */
    return (u16)(((u32)frames * 1000 + 30) / 60);
#elif HAL_FPS == 50
    /* 1000ms / 50fps = 20ms per frame */
    return frames * 20;
#else
    /* Generic calculation */
    return (u16)(((u32)frames * 1000 + (HAL_FPS/2)) / HAL_FPS);
#endif
}

/*
 * Convert milliseconds to frames.
 */
u16 hal_ms_to_frames(u16 ms) {
#if HAL_FPS == 60
    /* 60fps / 1000ms = 0.06 frames per ms */
    /* Use (ms * 60 + 500) / 1000 for rounding */
    return (u16)(((u32)ms * 60 + 500) / 1000);
#elif HAL_FPS == 50
    /* 50fps / 1000ms = 0.05 frames per ms */
    return (u16)(((u32)ms * 50 + 500) / 1000);
#else
    return (u16)(((u32)ms * HAL_FPS + 500) / 1000);
#endif
}

/*
 * Convert seconds to frames, capped at 255.
 */
u8 hal_seconds_to_frames(u8 seconds) {
    u16 frames = (u16)seconds * HAL_FPS;
    if (frames > 255) return 255;
    return (u8)frames;
}

/* ===========================================================================
 * Math Helpers (platform-agnostic versions)
 *
 * These are fallback implementations. Platforms with lookup tables or
 * hardware support should provide optimized versions in their hal_xxx.c
 * =========================================================================== */

/*
 * Distance squared - avoids expensive sqrt.
 * For range checks: hal_distance_sq(dx, dy) < (range * range)
 *
 * Note: Input is fixed8_8, but we extract integer parts to avoid overflow.
 * For subpixel precision, platform-specific versions can use 32-bit math.
 */
u16 hal_distance_sq(fixed8_8 dx, fixed8_8 dy) {
    /* Convert to integer pixels for simple calculation */
    i16 idx = FP_TO_INT(dx);
    i16 idy = FP_TO_INT(dy);

    /* Calculate squares (watch for overflow with large values) */
    i32 dx2 = (i32)idx * idx;
    i32 dy2 = (i32)idy * idy;
    i32 result = dx2 + dy2;

    /* Clamp to u16 range */
    if (result > 0xFFFF) return 0xFFFF;
    return (u16)result;
}

/*
 * Approximate distance using the alpha max plus beta min algorithm.
 * max(|dx|,|dy|) + min(|dx|,|dy|) * 0.5 gives ~6% error
 * max + min * 0.375 gives ~3% error
 *
 * We use max + min/2 for simplicity (just a shift).
 */
fixed8_8 hal_distance_approx(fixed8_8 dx, fixed8_8 dy) {
    /* Get absolute values */
    fixed8_8 adx = (dx < 0) ? -dx : dx;
    fixed8_8 ady = (dy < 0) ? -dy : dy;

    /* Find max and min */
    fixed8_8 max_val, min_val;
    if (adx > ady) {
        max_val = adx;
        min_val = ady;
    } else {
        max_val = ady;
        min_val = adx;
    }

    /* Approximate: max + min/2 */
    return max_val + (min_val >> 1);
}

/*
 * Normalize a vector to approximately unit length.
 * In fixed8_8, unit length = 256 (1.0).
 *
 * This is a simple iterative approximation. Platform-specific versions
 * should use lookup tables for better performance.
 */
fixed8_8 hal_normalize(fixed8_8* dx, fixed8_8* dy) {
    /* Get approximate magnitude */
    fixed8_8 mag = hal_distance_approx(*dx, *dy);

    if (mag == 0) {
        /* Can't normalize zero vector */
        return 0;
    }

    /* Scale to unit length: new = old * 256 / mag */
    /* Using 32-bit intermediate to avoid overflow */
    *dx = (fixed8_8)(((i32)*dx << 8) / mag);
    *dy = (fixed8_8)(((i32)*dy << 8) / mag);

    return mag;
}

/* ===========================================================================
 * Sin/Cos/Atan2 - Stub implementations
 *
 * These MUST be provided by platform-specific code with lookup tables.
 * The stubs here are just for compilation - they're not accurate!
 * =========================================================================== */

#ifndef HAL_MATH_TABLES_PROVIDED

/* Very rough sin approximation - DO NOT USE IN PRODUCTION */
/* Platforms must define HAL_MATH_TABLES_PROVIDED and provide real tables */
fixed8_8 hal_sin(angle_t angle) {
    /* Placeholder: rough approximation using parabola */
    /* Real implementation needs 256-entry lookup table */
    i16 a = angle;
    if (a > 128) a = 256 - a;  /* Mirror for second half */
    if (a > 64) a = 128 - a;   /* Mirror for quarters */

    /* Approximate with parabola: sin(x) ≈ 4x(1-x) for x in [0,1] */
    /* Here x = a/64, result scaled to [-256, 256] */
    i16 result = (a * (64 - a)) >> 2;

    /* Negate for angles 128-255 */
    if (angle > 128) result = -result;

    return (fixed8_8)result;
}

fixed8_8 hal_cos(angle_t angle) {
    /* cos(x) = sin(x + 90°) = sin(x + 64) in our 256-angle system */
    return hal_sin(angle + 64);
}

angle_t hal_atan2(fixed8_8 dy, fixed8_8 dx) {
    /* Very rough approximation - real implementation needs lookup table */
    /* This is just to make code compile */

    if (dx == 0 && dy == 0) return 0;

    /* Determine quadrant */
    u8 quadrant = 0;
    fixed8_8 adx = dx, ady = dy;

    if (dx < 0) { adx = -dx; quadrant |= 2; }
    if (dy < 0) { ady = -dy; quadrant |= 1; }

    /* Rough angle in first quadrant (0-63) */
    angle_t angle;
    if (adx >= ady) {
        /* Angle 0-45° (0-32 in our system) */
        angle = (angle_t)((ady * 32) / adx);
    } else {
        /* Angle 45-90° (32-64 in our system) */
        angle = 64 - (angle_t)((adx * 32) / ady);
    }

    /* Adjust for quadrant */
    switch (quadrant) {
        case 0: return angle;           /* Quadrant 1: 0-63 */
        case 2: return 128 - angle;     /* Quadrant 2: 64-128 */
        case 3: return 128 + angle;     /* Quadrant 3: 128-192 */
        case 1: return 256 - angle;     /* Quadrant 4: 192-255 */
    }
    return 0;
}

#endif /* HAL_MATH_TABLES_PROVIDED */

/* ===========================================================================
 * Platform Tier and Limits Query
 *
 * Provides runtime access to compile-time limits defined by the tier system.
 * =========================================================================== */

/*
 * Get the current platform tier.
 */
u8 hal_get_tier(void) {
#ifdef HAL_TIER
    return HAL_TIER;
#else
    return 0;  /* Default to MINIMAL if not defined */
#endif
}

/*
 * Get tier name for debugging/logging.
 */
const char* hal_get_tier_name(void) {
#ifdef HAL_TIER_NAME
    return HAL_TIER_NAME;
#else
    return "UNKNOWN";
#endif
}

/*
 * Get a platform limit by ID.
 * This provides runtime access to compile-time tier limits.
 */
u16 hal_get_limit(u8 limit_id) {
    switch (limit_id) {
        case 0:  /* HAL_LIMIT_ENTITIES */
#ifdef HAL_MAX_ENTITIES
            return HAL_MAX_ENTITIES;
#else
            return 32;
#endif

        case 1:  /* HAL_LIMIT_ENEMIES */
#ifdef HAL_MAX_ENEMIES
            return HAL_MAX_ENEMIES;
#else
            return 12;
#endif

        case 2:  /* HAL_LIMIT_PROJECTILES */
#ifdef HAL_MAX_PROJECTILES
            return HAL_MAX_PROJECTILES;
#else
            return 16;
#endif

        case 3:  /* HAL_LIMIT_PICKUPS */
#ifdef HAL_MAX_PICKUPS
            return HAL_MAX_PICKUPS;
#else
            return 16;
#endif

        case 4:  /* HAL_LIMIT_EFFECTS */
#ifdef HAL_MAX_EFFECTS
            return HAL_MAX_EFFECTS;
#else
            return 8;
#endif

        case 5:  /* HAL_LIMIT_COLLISION */
#ifdef HAL_COLLISION_BUDGET
            return HAL_COLLISION_BUDGET;
#else
            return 64;
#endif

        case 6:  /* HAL_LIMIT_UPDATE */
#ifdef HAL_UPDATE_BUDGET
            return HAL_UPDATE_BUDGET;
#else
            return 32;
#endif

        default:
            return 0;
    }
}

/* ===========================================================================
 * Platform Extensions (Graceful Degradation)
 *
 * Default implementations return FALSE/NULL. Platform-specific HAL files
 * override these to expose actual hardware features.
 * =========================================================================== */

/*
 * Check if extension is available.
 * Default: No extensions available. Platforms override in hal_xxx.c
 */
#ifndef HAL_EXTENSIONS_PROVIDED
bool_t hal_has_extension(u8 ext_id) {
    (void)ext_id;  /* Unused in default implementation */
    return FALSE;
}

/*
 * Get extension interface.
 * Default: Returns NULL. Platforms return pointer to extension struct.
 */
const void* hal_get_extension(u8 ext_id) {
    (void)ext_id;
    return NULL;
}
#endif /* HAL_EXTENSIONS_PROVIDED */

/* ===========================================================================
 * CPU Family Tables
 *
 * Lists platforms in each CPU family with migration notes.
 * Used by tools and runtime for cross-platform planning.
 * =========================================================================== */

#include "platform_manifest.h"

/* 6502 Family Members */
const ARDK_FamilyMember ardk_family_6502[] = {
    { ARDK_PLAT_NES,       "NES",      "Primary target. PPU requires specific tile format." },
    { ARDK_PLAT_C64,       "C64",      "VIC-II has different sprite limits. SID audio." },
    { ARDK_PLAT_PCE,       "PCE",      "HuC6280 is 65C02. VDC has 64 sprites." },
    { ARDK_PLAT_ATARI2600, "Atari2600","Extreme constraints. TIA requires racing the beam." },
    { ARDK_PLAT_ATARI7800, "Atari7800","MARIA chip. More capable than 2600." },
    { ARDK_PLAT_APPLE2,    "AppleII",  "No hardware sprites. Software rendering." },
    { ARDK_PLAT_BBC,       "BBC",      "6845 CRTC. Various graphics modes." },
    { 0, NULL, NULL }  /* Sentinel */
};

/* Z80 Family Members */
const ARDK_FamilyMember ardk_family_z80[] = {
    { ARDK_PLAT_GB,     "GameBoy",  "Primary target. LR35902 lacks IX/IY registers." },
    { ARDK_PLAT_GBC,    "GBC",      "Same CPU as GB. More colors, double-speed mode." },
    { ARDK_PLAT_SMS,    "SMS",      "Standard Z80. VDP similar to Genesis." },
    { ARDK_PLAT_GG,     "GameGear", "SMS compatible. Smaller screen, more colors." },
    { ARDK_PLAT_MSX,    "MSX",      "TMS9918 VDP. Various RAM configurations." },
    { ARDK_PLAT_ZX,     "Spectrum", "ULA graphics. Attribute color clash." },
    { ARDK_PLAT_COLECO, "Coleco",   "TMS9918 VDP. Similar to MSX." },
    { 0, NULL, NULL }  /* Sentinel */
};

/* 68000 Family Members */
const ARDK_FamilyMember ardk_family_68k[] = {
    { ARDK_PLAT_GENESIS,   "Genesis",  "Primary target. VDP with 80 sprites, FM audio." },
    { ARDK_PLAT_AMIGA_OCS, "AmigaOCS", "Blitter + Copper. HAM mode. 4-channel MOD audio." },
    { ARDK_PLAT_AMIGA_AGA, "AmigaAGA", "256 colors. Larger sprites. AGA chipset." },
    { ARDK_PLAT_NEOGEO,    "NeoGeo",   "Similar to Genesis VDP. 380 sprites! YM2610." },
    { ARDK_PLAT_X68000,    "X68000",   "65536 colors. Very capable. PCM audio." },
    { ARDK_PLAT_SEGACD,    "SegaCD",   "Genesis + sub-68K + CD-ROM. Scaling/rotation." },
    { ARDK_PLAT_32X,       "32X",      "Genesis + SH-2. Direct framebuffer access." },
    { 0, NULL, NULL }  /* Sentinel */
};

/*
 * Get family members array.
 * Returns pointer to array and sets count via output parameter.
 */
const ARDK_FamilyMember* hal_get_family_members(u8 family, u8* count) {
    const ARDK_FamilyMember* members = NULL;
    u8 n = 0;

    switch (family) {
        case ARDK_FAMILY_6502:
            members = ardk_family_6502;
            n = 7;
            break;
        case ARDK_FAMILY_Z80:
            members = ardk_family_z80;
            n = 7;
            break;
        case ARDK_FAMILY_68K:
            members = ardk_family_68k;
            n = 7;
            break;
        default:
            n = 0;
            break;
    }

    if (count) *count = n;
    return members;
}

/*
 * Check migration difficulty from current platform to target.
 * Returns ARDK_MIGRATE_xxx constant.
 */
u8 hal_check_migration(u16 target_platform) {
    u8 current_family;
    u8 target_family;

#ifdef HAL_MANIFEST_FAMILY
    current_family = HAL_MANIFEST_FAMILY;
#else
    current_family = ARDK_FAMILY_6502;  /* Default to NES */
#endif

    target_family = ARDK_PLATFORM_TO_FAMILY(target_platform);

    /* Same platform = no migration needed */
#ifdef HAL_PLATFORM_ID
    if (target_platform == HAL_PLATFORM_ID) {
        return ARDK_MIGRATE_SAME;
    }
#endif

    /* Same family = varying difficulty based on graphics chip */
    if (current_family == target_family) {
        /* Check for known easy migrations */
        #ifdef HAL_PLATFORM_ID
        u16 src = HAL_PLATFORM_ID;
        #else
        u16 src = ARDK_PLAT_NES;
        #endif

        /* Trivial: Same console family (GB→GBC, etc.) */
        if ((src == ARDK_PLAT_GB && target_platform == ARDK_PLAT_GBC) ||
            (src == ARDK_PLAT_SMS && target_platform == ARDK_PLAT_GG)) {
            return ARDK_MIGRATE_TRIVIAL;
        }

        /* Easy: Similar graphics chips */
        if ((src == ARDK_PLAT_NES && target_platform == ARDK_PLAT_C64) ||
            (src == ARDK_PLAT_GENESIS && target_platform == ARDK_PLAT_NEOGEO)) {
            return ARDK_MIGRATE_EASY;
        }

        /* Moderate: Same CPU, different everything else */
        return ARDK_MIGRATE_MODERATE;
    }

    /* Different family = hard or impossible */
    /* Could be possible between similar tiers (NES→GB, Genesis→SNES) */
    if ((current_family == ARDK_FAMILY_6502 && target_family == ARDK_FAMILY_Z80) ||
        (current_family == ARDK_FAMILY_Z80 && target_family == ARDK_FAMILY_6502)) {
        /* 8-bit to 8-bit is doable with effort */
        return ARDK_MIGRATE_HARD;
    }

    if ((current_family == ARDK_FAMILY_68K && target_family == ARDK_FAMILY_65816) ||
        (current_family == ARDK_FAMILY_65816 && target_family == ARDK_FAMILY_68K)) {
        /* 16-bit to 16-bit is doable */
        return ARDK_MIGRATE_HARD;
    }

    /* Significant architecture difference */
    return ARDK_MIGRATE_IMPOSSIBLE;
}
