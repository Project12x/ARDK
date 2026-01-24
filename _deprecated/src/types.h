/*
 * =============================================================================
 * ARDK - Agentic Retro Development Kit
 * types.h - Platform-Agnostic Type Definitions
 * =============================================================================
 *
 * These types are the foundation of all ARDK code. Once defined, they should
 * NEVER change. All game logic and HAL implementations depend on these.
 *
 * LOCKED DECISIONS:
 * - Fixed-point format: 8.8 (8 bits integer, 8 bits fraction)
 * - Coordinate system: Origin top-left, Y increases downward
 * - Signed types use two's complement
 * =============================================================================
 */

#ifndef ARDK_TYPES_H
#define ARDK_TYPES_H

/* ---------------------------------------------------------------------------
 * Basic Integer Types
 * These map to platform-native types for optimal code generation
 * --------------------------------------------------------------------------- */

typedef unsigned char   u8;     /* 0 to 255 */
typedef signed char     i8;     /* -128 to 127 */
typedef unsigned short  u16;    /* 0 to 65535 */
typedef signed short    i16;    /* -32768 to 32767 */
typedef unsigned long   u32;    /* 0 to 4294967295 */
typedef signed long     i32;    /* -2147483648 to 2147483647 */

/* 64-bit types (for higher-tier fixed-point math) */
#if defined(__GNUC__) || defined(__clang__) || defined(_MSC_VER)
    typedef unsigned long long  u64;
    typedef signed long long    i64;
#else
    /* Fallback for older compilers - may not have 64-bit support */
    typedef u32 u64;    /* Truncated, 32-bit platforms may not need 64-bit */
    typedef i32 i64;
#endif

/* Boolean type */
typedef u8 bool_t;
#define TRUE  1
#define FALSE 0

/* NULL pointer */
#ifndef NULL
#define NULL ((void*)0)
#endif

/* ---------------------------------------------------------------------------
 * Fixed-Point Math
 *
 * The fixed-point format varies by tier (set in hal_tiers.h via HAL_FIXED_POINT_BITS):
 *   - MINIMAL/MINIMAL_PLUS: 8.8 format (16-bit total)
 *   - STANDARD: 8.8 format (16-bit total)
 *   - STANDARD_PLUS: 12.12 format (24-bit, stored in 32-bit)
 *   - EXTENDED: 16.16 format (32-bit total)
 *
 * For 8-bit platforms, 8.8 is optimal (fits in 16-bit word).
 * For 16-bit platforms with fast multiply (68K), 8.8 or 12.12 is good.
 * For 32-bit platforms (ARM), 16.16 gives best precision.
 *
 * The "base" fixed type (fixed8_8) is always available as a common format
 * for cross-platform entity positions. Use fixed_t for tier-optimal math.
 *
 * Usage:
 *   fixed8_8 velocity = FP_FROM_INT(2);      // 2.0 in base format
 *   fixed_t precise = FPX_FROM_INT(2);       // 2.0 in tier-optimal format
 *   i16 pixels = FP_TO_INT(position);        // Extract integer part
 * --------------------------------------------------------------------------- */

/* Base fixed-point: 8.8 format (always available for entity positions) */
typedef i16 fixed8_8;   /* Signed 8.8 fixed-point */
typedef u16 ufixed8_8;  /* Unsigned 8.8 fixed-point */

/* Base (8.8) fixed-point constants */
#define FP_ONE      256     /* 1.0 in 8.8 format */
#define FP_HALF     128     /* 0.5 in 8.8 format */
#define FP_QUARTER  64      /* 0.25 in 8.8 format */
#define FP_ZERO     0       /* 0.0 */

/* Base (8.8) fixed-point conversion macros */
#define FP_FROM_INT(i)      ((fixed8_8)((i) << 8))
#define FP_TO_INT(fp)       ((i8)((fp) >> 8))
#define FP_TO_INT_ROUND(fp) ((i8)(((fp) + 128) >> 8))
#define FP_FRAC(fp)         ((u8)((fp) & 0xFF))

/* Fixed-point from float (compile-time only, not for runtime!) */
#define FP_FROM_FLOAT(f)    ((fixed8_8)((f) * 256.0f))

/* Base (8.8) fixed-point arithmetic */
#define FP_ADD(a, b)    ((a) + (b))
#define FP_SUB(a, b)    ((a) - (b))
#define FP_NEG(a)       (-(a))
#define FP_ABS(a)       ((a) < 0 ? -(a) : (a))

/* Multiply two 8.8 values - result is 8.8
 * Note: This requires 32-bit intermediate for correctness */
#define FP_MUL(a, b)    ((fixed8_8)(((i32)(a) * (i32)(b)) >> 8))

/* Divide 8.8 by 8.8 - result is 8.8 */
#define FP_DIV(a, b)    ((fixed8_8)(((i32)(a) << 8) / (b)))

/* ---------------------------------------------------------------------------
 * Tier-Optimal Fixed-Point (fixed_t)
 *
 * Use these for math that benefits from higher precision on capable platforms.
 * Convert to fixed8_8 when storing in entity structs or sending to HAL.
 *
 * The FPX_* macros work with the tier-optimal fixed_t type.
 * --------------------------------------------------------------------------- */

#if defined(HAL_FIXED_POINT_BITS) && HAL_FIXED_POINT_BITS == 16
    /* 16.16 format for EXTENDED tier (GBA, DS) */
    typedef i32 fixed_t;
    typedef u32 ufixed_t;

    #define FPX_BITS        16
    #define FPX_ONE         65536       /* 1.0 in 16.16 */
    #define FPX_HALF        32768       /* 0.5 */
    #define FPX_QUARTER     16384       /* 0.25 */

    #define FPX_FROM_INT(i)     ((fixed_t)((i) << 16))
    #define FPX_TO_INT(fp)      ((i16)((fp) >> 16))
    #define FPX_FROM_FLOAT(f)   ((fixed_t)((f) * 65536.0f))
    #define FPX_MUL(a, b)       ((fixed_t)(((i64)(a) * (i64)(b)) >> 16))
    #define FPX_DIV(a, b)       ((fixed_t)(((i64)(a) << 16) / (b)))

    /* Convert between tier-optimal and base 8.8 */
    #define FPX_TO_FP88(fpx)    ((fixed8_8)((fpx) >> 8))
    #define FP88_TO_FPX(fp88)   ((fixed_t)((fp88) << 8))

#elif defined(HAL_FIXED_POINT_BITS) && HAL_FIXED_POINT_BITS == 12
    /* 12.12 format for STANDARD_PLUS tier (68K sweet spot) */
    typedef i32 fixed_t;    /* 24 bits used, stored in 32-bit for alignment */
    typedef u32 ufixed_t;

    #define FPX_BITS        12
    #define FPX_ONE         4096        /* 1.0 in 12.12 */
    #define FPX_HALF        2048        /* 0.5 */
    #define FPX_QUARTER     1024        /* 0.25 */

    #define FPX_FROM_INT(i)     ((fixed_t)((i) << 12))
    #define FPX_TO_INT(fp)      ((i16)((fp) >> 12))
    #define FPX_FROM_FLOAT(f)   ((fixed_t)((f) * 4096.0f))
    #define FPX_MUL(a, b)       ((fixed_t)(((i32)(a) * (i32)(b)) >> 12))
    #define FPX_DIV(a, b)       ((fixed_t)(((i32)(a) << 12) / (b)))

    /* Convert between tier-optimal and base 8.8 */
    #define FPX_TO_FP88(fpx)    ((fixed8_8)((fpx) >> 4))
    #define FP88_TO_FPX(fp88)   ((fixed_t)((fp88) << 4))

#else
    /* Default: 8.8 format for MINIMAL/MINIMAL_PLUS/STANDARD tiers */
    typedef i16 fixed_t;
    typedef u16 ufixed_t;

    #define FPX_BITS        8
    #define FPX_ONE         FP_ONE
    #define FPX_HALF        FP_HALF
    #define FPX_QUARTER     FP_QUARTER

    #define FPX_FROM_INT(i)     FP_FROM_INT(i)
    #define FPX_TO_INT(fp)      FP_TO_INT(fp)
    #define FPX_FROM_FLOAT(f)   FP_FROM_FLOAT(f)
    #define FPX_MUL(a, b)       FP_MUL(a, b)
    #define FPX_DIV(a, b)       FP_DIV(a, b)

    /* No conversion needed - same format */
    #define FPX_TO_FP88(fpx)    (fpx)
    #define FP88_TO_FPX(fp88)   (fp88)
#endif

/* Common FPX arithmetic (same for all tiers) */
#define FPX_ADD(a, b)   ((a) + (b))
#define FPX_SUB(a, b)   ((a) - (b))
#define FPX_NEG(a)      (-(a))
#define FPX_ABS(a)      ((a) < 0 ? -(a) : (a))

/* ---------------------------------------------------------------------------
 * Screen Coordinates
 *
 * LOCKED: Origin is top-left (0,0), Y increases downward
 * This matches hardware sprite coordinates on NES, Genesis, GB, GBA, etc.
 * --------------------------------------------------------------------------- */

typedef i16 coord_t;    /* Screen coordinate (allows off-screen values) */

/* Common screen boundaries (can be overridden per platform) */
#define SCREEN_MIN_X    0
#define SCREEN_MIN_Y    0
/* SCREEN_MAX_X and SCREEN_MAX_Y defined per platform in hal_config.h */

/* ---------------------------------------------------------------------------
 * Direction and Angle Types
 * --------------------------------------------------------------------------- */

/* 8-direction enum (for movement, facing) */
typedef enum {
    DIR_NONE  = 0,
    DIR_UP    = 1,
    DIR_DOWN  = 2,
    DIR_LEFT  = 4,
    DIR_RIGHT = 8,
    DIR_UP_LEFT    = DIR_UP | DIR_LEFT,     /* 5 */
    DIR_UP_RIGHT   = DIR_UP | DIR_RIGHT,    /* 9 */
    DIR_DOWN_LEFT  = DIR_DOWN | DIR_LEFT,   /* 6 */
    DIR_DOWN_RIGHT = DIR_DOWN | DIR_RIGHT   /* 10 */
} direction_t;

/* 256-angle system (0 = right, 64 = down, 128 = left, 192 = up)
 * Matches typical atan2 lookup table approach */
typedef u8 angle_t;

#define ANGLE_RIGHT 0
#define ANGLE_DOWN  64
#define ANGLE_LEFT  128
#define ANGLE_UP    192

/* ---------------------------------------------------------------------------
 * Asset ID Types
 *
 * LOCKED: 8-bit IDs with reserved ranges
 * 0x00-0x0F: System reserved
 * 0x10-0x7F: Game assets
 * 0x80-0xFF: Platform-specific / dynamic
 * --------------------------------------------------------------------------- */

typedef u8 sprite_id_t;     /* Sprite/tile asset ID */
typedef u8 sfx_id_t;        /* Sound effect ID */
typedef u8 music_id_t;      /* Music track ID */
typedef u8 palette_id_t;    /* Palette ID */

/* Reserved ID ranges */
#define ASSET_ID_NONE       0x00
#define ASSET_ID_SYSTEM_MAX 0x0F
#define ASSET_ID_GAME_MIN   0x10
#define ASSET_ID_GAME_MAX   0x7F
#define ASSET_ID_DYNAMIC    0x80

/* ---------------------------------------------------------------------------
 * Bit Manipulation Helpers
 * --------------------------------------------------------------------------- */

#define BIT(n)          (1 << (n))
#define BIT_SET(v, n)   ((v) |= BIT(n))
#define BIT_CLR(v, n)   ((v) &= ~BIT(n))
#define BIT_FLIP(v, n)  ((v) ^= BIT(n))
#define BIT_TEST(v, n)  (((v) & BIT(n)) != 0)

/* ---------------------------------------------------------------------------
 * Min/Max/Clamp
 * --------------------------------------------------------------------------- */

#define MIN(a, b)       ((a) < (b) ? (a) : (b))
#define MAX(a, b)       ((a) > (b) ? (a) : (b))
#define CLAMP(v, lo, hi) (MIN(MAX(v, lo), hi))

/* ---------------------------------------------------------------------------
 * Array Size Helper
 * --------------------------------------------------------------------------- */

#define ARRAY_SIZE(arr) (sizeof(arr) / sizeof((arr)[0]))

#endif /* ARDK_TYPES_H */
