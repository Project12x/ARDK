/*
 * =============================================================================
 * ARDK - Hardware Tier Definitions
 * hal_tiers.h - Capability tiers for platform grouping
 * =============================================================================
 *
 * DUAL-TIER SYSTEM:
 *   Platforms have separate tiers for ASSETS (sprites/audio) and LOGIC (CPU/RAM).
 *   This allows systems like Neo Geo (STANDARD sprites, STANDARD_PLUS logic) to
 *   be properly categorized.
 *
 * DESIGN PHILOSOPHY:
 *   "Design at tier peak, downsample within tier"
 *   - Design game logic for the most capable platform in each logic tier
 *   - Design assets for the highest-detail platform in each asset tier
 *   - Pipeline/compiler reduces for less capable platforms in same tier
 *
 * TIER HIERARCHY:
 *   1. hal_tiers.h defines baseline values per tier
 *   2. Platform hal_config.h includes tier, can override any value
 *   3. Game code uses final resolved HAL_* macros
 *
 * USAGE:
 *   In platform hal_config.h:
 *     #define HAL_TIER_ASSETS HAL_TIER_STANDARD
 *     #define HAL_TIER_LOGIC  HAL_TIER_STANDARD_PLUS
 *     #define HAL_TIER        HAL_TIER_LOGIC      // Primary tier for budgets
 *     #include "../hal_tiers.h"
 *     // Override specific values if needed:
 *     #undef HAL_MAX_ENEMIES
 *     #define HAL_MAX_ENEMIES 64  // Platform-specific override
 *
 * =============================================================================
 */

#ifndef ARDK_HAL_TIERS_H
#define ARDK_HAL_TIERS_H

/* ===========================================================================
 * Tier Identifiers
 * ===========================================================================
 *
 * TIER HIERARCHY (weakest to strongest):
 *
 *   MINIMAL (0)        - 8-bit home consoles and computers
 *   MINIMAL_PLUS (1)   - Enhanced 8-bit (MSX2, SMS - Z80 with better graphics)
 *   STANDARD (2)       - 16-bit consoles (Genesis, SNES, PCE)
 *   STANDARD_PLUS (3)  - Enhanced 16-bit (Neo Geo, Sega CD, X68000)
 *   EXTENDED (4)       - 32-bit portables (GBA, DS)
 *
 * NOTE: Modern PC (Steam/itch.io releases) is a BUILD TARGET, not a tier.
 * Modern PC compiles C HAL code with SDL2 backend, using the tier limits
 * from whatever retro platform the game was originally designed for.
 * See engines/modern_pc/ for SDL2 HAL backend (future).
 *
 * NOTE: Retro PCs (DOS, Amiga, Atari ST) are planned as future targets.
 * They may be added as HAL tiers (RETRO_PC_68K, RETRO_PC_X86) or handled
 * as engine-only targets depending on community needs. The Amiga scene
 * is particularly active. See "FUTURE: RETRO PC PLATFORMS" section below.
 * The asset pipeline already supports vga/cga/amiga_aga for graphics style.
 *
 * ===========================================================================
 */

#define HAL_TIER_MINIMAL        0   /* NES, GB, GBC, C64, ZX, Atari 2600/7800 */
#define HAL_TIER_MINIMAL_PLUS   1   /* SMS, MSX2, Neo Geo Pocket (enhanced 8-bit) */
#define HAL_TIER_STANDARD       2   /* Genesis, SNES, PC Engine, Amiga OCS */
#define HAL_TIER_STANDARD_PLUS  3   /* Neo Geo, Sega CD, X68000, 32X */
#define HAL_TIER_EXTENDED       4   /* GBA, DS, PSP */

/* Maximum tier value (for bounds checking) */
#define HAL_TIER_MAX            HAL_TIER_EXTENDED

/* ===========================================================================
 * Platform Tier Assignments (Floor → Peak per tier)
 * ===========================================================================
 *
 * INTERPOLATION KEY: Within each tier, platforms are ranked from "floor"
 * (barely meets tier minimum) to "peak" (defines tier ceiling). Design for
 * peak, confidently reduce for floor. This enables NES+Genesis simultaneous
 * development by ensuring proper mapping between disparate capability levels.
 *
 * ===== MINIMAL TIER (8-bit baseline) =====
 *   Floor: Atari 2600 (128 bytes RAM, 2 sprites)
 *   Low:   ZX Spectrum (attribute color, contended RAM)
 *   Mid:   C64 (64KB shared, 8 HW sprites)
 *   High:  NES (2KB fast RAM, 64 sprites, 8/line)
 *   Peak:  Game Boy (Z80@4.19MHz, 8KB RAM, 40 sprites)
 *
 *   | Platform     | CPU           | MHz  | RAM    | Sprites | /Line | Colors |
 *   |--------------|---------------|------|--------|---------|-------|--------|
 *   | Atari 2600   | 6507          | 1.19 | 128B   | 2       | 2     | 2      |
 *   | ZX Spectrum  | Z80           | 3.5  | 48KB*  | SW      | -     | 2/cell |
 *   | C64          | 6510          | 1.02 | 64KB*  | 8       | 8     | 4 MCM  |
 *   | NES          | 6502          | 1.79 | 2KB    | 64      | 8     | 4/spr  |
 *   | Game Boy     | Z80-like      | 4.19 | 8KB    | 40      | 10    | 4 gray |
 *   | GBC          | Z80-like      | 8.38 | 32KB   | 40      | 10    | 4/pal  |
 *   * = shared/contended with video
 *
 * ===== MINIMAL_PLUS TIER (enhanced 8-bit) =====
 *   Floor: Neo Geo Pocket (Z80@6.144MHz, 4KB work RAM)
 *   Mid:   MSX2 (Z80@3.58MHz, V9938 VDP, 128KB VRAM)
 *   Peak:  SMS (Z80@3.58MHz, 8KB RAM, 16 colors/sprite)
 *
 *   | Platform       | CPU    | MHz  | RAM  | Sprites | /Line | Colors  |
 *   |----------------|--------|------|------|---------|-------|---------|
 *   | Neo Geo Pocket | Z80    | 6.14 | 4KB  | 64      | 8     | 8/pal   |
 *   | MSX2           | Z80    | 3.58 | 64KB | 32      | 8     | 16/spr  |
 *   | SMS            | Z80    | 3.58 | 8KB  | 64      | 8     | 16/spr  |
 *
 *   SMS moved here: Better than NES (16 vs 4 colors/sprite), Z80 vs 6502,
 *   but clearly not in Genesis/SNES league. "Best 8-bit graphics" tier.
 *
 * ===== STANDARD TIER (16-bit) =====
 *   Floor: PC Engine (65C02@7.16MHz, 8KB RAM)
 *   Mid:   Genesis (68000@7.67MHz, 64KB RAM)
 *   High:  Amiga OCS (68000@7.09MHz, 512KB, blitter)
 *   Peak:  SNES (65816@3.58MHz, 128KB RAM, Mode 7)
 *
 *   | Platform   | CPU        | MHz  | RAM   | Sprites | /Line | Colors |
 *   |------------|------------|------|-------|---------|-------|--------|
 *   | PC Engine  | 65C02      | 7.16 | 8KB   | 64      | 16    | 482    |
 *   | Genesis    | 68000      | 7.67 | 64KB  | 80      | 20    | 64     |
 *   | Amiga OCS  | 68000      | 7.09 | 512KB | 8       | 8     | 32 HAM |
 *   | SNES       | 65816      | 3.58 | 128KB | 128     | 32    | 256    |
 *
 * ===== STANDARD_PLUS TIER (enhanced 16-bit / arcade) =====
 *   Floor: 32X (2x SH-2@23MHz, adds to Genesis)
 *   Mid:   Sega CD (68000@12.5MHz + 68000@7.67MHz, 768KB)
 *   High:  X68000 (68000@10MHz, 1MB+, 65536 colors)
 *   Peak:  Neo Geo (68000@12MHz, 64KB+330KB, 4096 colors)
 *
 *   | Platform  | CPU                | MHz     | RAM     | Sprites | /Line | Colors |
 *   |-----------|--------------------|---------|---------|---------|-------|--------|
 *   | 32X       | 2x SH-2            | 23+23   | 256KB+  | +       | +     | 32K    |
 *   | Sega CD   | 68000+68000        | 12.5+7.6| 768KB   | =Gen    | =Gen  | =Gen   |
 *   | X68000    | 68000              | 10      | 1-4MB   | 128     | 32    | 65536  |
 *   | Neo Geo   | 68000              | 12      | 64KB+   | 380     | 96    | 4096   |
 *
 * ===== EXTENDED TIER (32-bit portables) =====
 *   Floor: GBA (ARM7@16.78MHz, 256KB RAM)
 *   Peak:  DS (ARM9@67MHz + ARM7@33MHz, 4MB RAM)
 *
 *   | Platform | CPU           | MHz    | RAM   | Sprites | /Line | Colors |
 *   |----------|---------------|--------|-------|---------|-------|--------|
 *   | GBA      | ARM7TDMI      | 16.78  | 256KB | 128     | 128   | 32K    |
 *   | DS       | ARM9+ARM7     | 67+33  | 4MB   | 128x2   | 128   | 262K   |
 *
 * ===== FUTURE: RETRO PC PLATFORMS =====
 *   Retro PC platforms (DOS, Atari ST, Amiga) are NOT currently in HAL tiers.
 *   They use software rendering and have different constraints than consoles.
 *   Support is planned for future expansion:
 *
 *   engines/68k/atari_st/     (Atari ST/STE - 68000, STANDARD-like)
 *   engines/68k/atari_falcon/ (Atari Falcon - 68030, STANDARD_PLUS-like)
 *   engines/68k/amiga/        (Amiga OCS/ECS - 68000, STANDARD-like)
 *   engines/68k/amiga_aga/    (Amiga AGA - 68020+, STANDARD_PLUS-like)
 *   engines/x86/dos/          (DOS VGA - 386+, software rendering)
 *   engines/x86/pc98/         (NEC PC-98 - V30/386)
 *
 *   FUTURE TIER CONSIDERATION:
 *   If community demand warrants (especially from the active Amiga scene),
 *   retro PCs may be added as HAL tiers:
 *     - HAL_TIER_RETRO_PC_68K (5) - Amiga, Atari ST/Falcon
 *     - HAL_TIER_RETRO_PC_X86 (6) - DOS VGA, PC-98
 *   This would provide tier-specific budgets for software-rendered platforms.
 *
 *   The asset pipeline already supports vga/cga/amiga_aga naming for
 *   graphics style conversion (resolution, palette, dithering).
 *
 * ===========================================================================
 */

/* ===========================================================================
 * Tier Peak Platforms (for design targets)
 * =========================================================================== */

/* Asset tier peaks - highest graphical detail in each tier */
#define HAL_ASSET_PEAK_MINIMAL       "GBC"          /* 4/palette, best MINIMAL colors */
#define HAL_ASSET_PEAK_MINIMAL_PLUS  "SMS"          /* 16 colors/sprite */
#define HAL_ASSET_PEAK_STANDARD      "SNES"         /* 256 colors, Mode 7 */
#define HAL_ASSET_PEAK_STANDARD_PLUS "Neo Geo"      /* 4096 colors, arcade quality */
#define HAL_ASSET_PEAK_EXTENDED      "DS"           /* 262K colors, dual screen */

/* Logic tier peaks - most capable CPU/RAM in each tier */
#define HAL_LOGIC_PEAK_MINIMAL       "GBC"          /* Z80@8.38MHz, 32KB RAM */
#define HAL_LOGIC_PEAK_MINIMAL_PLUS  "SMS"          /* Z80@3.58MHz, 8KB fast RAM */
#define HAL_LOGIC_PEAK_STANDARD      "SNES"         /* 65816, 128KB RAM */
#define HAL_LOGIC_PEAK_STANDARD_PLUS "Neo Geo"      /* 68000@12MHz, 384KB+ */
#define HAL_LOGIC_PEAK_EXTENDED      "DS"           /* ARM9+ARM7, 4MB RAM */

/* ===========================================================================
 * Validate tier is defined
 * =========================================================================== */

#ifndef HAL_TIER
    #error "HAL_TIER must be defined before including hal_tiers.h"
#endif

/* Default asset/logic tiers to HAL_TIER if not specified */
#ifndef HAL_TIER_ASSETS
    #define HAL_TIER_ASSETS HAL_TIER
#endif
#ifndef HAL_TIER_LOGIC
    #define HAL_TIER_LOGIC HAL_TIER
#endif

/* ===========================================================================
 * TIER_MINIMAL Defaults (NES, GB, GBC, C64, ZX, Atari 2600/7800)
 * ===========================================================================
 * Design target: GBC capabilities (fastest Z80 variant, 32KB RAM)
 * Reduce for: NES (slower 6502, 2KB), C64 (shared RAM), Atari (severe limits)
 */

#if HAL_TIER == HAL_TIER_MINIMAL

    /* --- Entity Limits --- */
    #ifndef HAL_MAX_ENTITIES
        #define HAL_MAX_ENTITIES        32
    #endif
    #ifndef HAL_MAX_ENEMIES
        #define HAL_MAX_ENEMIES         12
    #endif
    #ifndef HAL_MAX_PROJECTILES
        #define HAL_MAX_PROJECTILES     16
    #endif
    #ifndef HAL_MAX_PICKUPS
        #define HAL_MAX_PICKUPS         16
    #endif
    #ifndef HAL_MAX_EFFECTS
        #define HAL_MAX_EFFECTS         8
    #endif

    /* --- Memory Budgets --- */
    #ifndef HAL_ENTITY_RAM_BUDGET
        #define HAL_ENTITY_RAM_BUDGET   512     /* Bytes for entity pools */
    #endif
    #ifndef HAL_SCRATCH_RAM
        #define HAL_SCRATCH_RAM         128     /* Bytes for temp buffers */
    #endif

    /* --- Performance Hints --- */
    #ifndef HAL_COLLISION_BUDGET
        #define HAL_COLLISION_BUDGET    64      /* Max collision checks/frame */
    #endif
    #ifndef HAL_UPDATE_BUDGET
        #define HAL_UPDATE_BUDGET       32      /* Max entity updates/frame */
    #endif

    /* --- AI Complexity --- */
    #ifndef HAL_AI_PATHFIND
        #define HAL_AI_PATHFIND         0       /* No pathfinding */
    #endif
    #ifndef HAL_AI_GROUP_BEHAVIOR
        #define HAL_AI_GROUP_BEHAVIOR   0       /* No group AI */
    #endif
    #ifndef HAL_AI_PREDICTION
        #define HAL_AI_PREDICTION       0       /* No prediction frames */
    #endif
    #ifndef HAL_AI_UPDATE_SPLIT
        #define HAL_AI_UPDATE_SPLIT     4       /* Update 1/4 enemies per frame */
    #endif

    /* --- Physics Precision --- */
    #ifndef HAL_FIXED_POINT_BITS
        #define HAL_FIXED_POINT_BITS    8       /* 8.8 fixed point */
    #endif

    /* --- Feature Flags --- */
    #ifndef HAL_HAS_FAST_MULTIPLY
        #define HAL_HAS_FAST_MULTIPLY   0
    #endif
    #ifndef HAL_HAS_DIVIDE
        #define HAL_HAS_DIVIDE          0
    #endif
    #ifndef HAL_USE_SPLIT_TABLES
        #define HAL_USE_SPLIT_TABLES    1       /* Use lo/hi byte tables for 6502 */
    #endif

/* ===========================================================================
 * TIER_MINIMAL_PLUS Defaults (SMS, MSX2, Neo Geo Pocket)
 * ===========================================================================
 * Design target: SMS capabilities (Z80@3.58MHz, 8KB fast RAM, 16 colors/sprite)
 * Enhanced 8-bit: Better graphics than MINIMAL, still 8-bit CPUs
 */

#elif HAL_TIER == HAL_TIER_MINIMAL_PLUS

    /* --- Entity Limits --- */
    #ifndef HAL_MAX_ENTITIES
        #define HAL_MAX_ENTITIES        48
    #endif
    #ifndef HAL_MAX_ENEMIES
        #define HAL_MAX_ENEMIES         16
    #endif
    #ifndef HAL_MAX_PROJECTILES
        #define HAL_MAX_PROJECTILES     24
    #endif
    #ifndef HAL_MAX_PICKUPS
        #define HAL_MAX_PICKUPS         24
    #endif
    #ifndef HAL_MAX_EFFECTS
        #define HAL_MAX_EFFECTS         12
    #endif

    /* --- Memory Budgets --- */
    #ifndef HAL_ENTITY_RAM_BUDGET
        #define HAL_ENTITY_RAM_BUDGET   768     /* Bytes for entity pools */
    #endif
    #ifndef HAL_SCRATCH_RAM
        #define HAL_SCRATCH_RAM         256     /* Bytes for temp buffers */
    #endif

    /* --- Performance Hints --- */
    #ifndef HAL_COLLISION_BUDGET
        #define HAL_COLLISION_BUDGET    96      /* Max collision checks/frame */
    #endif
    #ifndef HAL_UPDATE_BUDGET
        #define HAL_UPDATE_BUDGET       48      /* Max entity updates/frame */
    #endif

    /* --- AI Complexity --- */
    #ifndef HAL_AI_PATHFIND
        #define HAL_AI_PATHFIND         0       /* No pathfinding (8-bit still) */
    #endif
    #ifndef HAL_AI_GROUP_BEHAVIOR
        #define HAL_AI_GROUP_BEHAVIOR   0       /* No group AI */
    #endif
    #ifndef HAL_AI_PREDICTION
        #define HAL_AI_PREDICTION       2       /* 2 frames prediction */
    #endif
    #ifndef HAL_AI_UPDATE_SPLIT
        #define HAL_AI_UPDATE_SPLIT     3       /* Update 1/3 enemies per frame */
    #endif

    /* --- Physics Precision --- */
    #ifndef HAL_FIXED_POINT_BITS
        #define HAL_FIXED_POINT_BITS    8       /* 8.8 fixed point */
    #endif

    /* --- Feature Flags --- */
    #ifndef HAL_HAS_FAST_MULTIPLY
        #define HAL_HAS_FAST_MULTIPLY   0
    #endif
    #ifndef HAL_HAS_DIVIDE
        #define HAL_HAS_DIVIDE          0
    #endif
    #ifndef HAL_USE_SPLIT_TABLES
        #define HAL_USE_SPLIT_TABLES    1       /* Z80 still benefits from split tables */
    #endif

/* ===========================================================================
 * TIER_STANDARD Defaults (Genesis, SNES, PC Engine, Amiga OCS)
 * ===========================================================================
 * Design target: SNES capabilities (best color depth, Mode 7)
 * Reduce for: Genesis (fewer colors), PCE (less RAM without CD)
 */

#elif HAL_TIER == HAL_TIER_STANDARD

    /* --- Entity Limits --- */
    #ifndef HAL_MAX_ENTITIES
        #define HAL_MAX_ENTITIES        128
    #endif
    #ifndef HAL_MAX_ENEMIES
        #define HAL_MAX_ENEMIES         48
    #endif
    #ifndef HAL_MAX_PROJECTILES
        #define HAL_MAX_PROJECTILES     48
    #endif
    #ifndef HAL_MAX_PICKUPS
        #define HAL_MAX_PICKUPS         48
    #endif
    #ifndef HAL_MAX_EFFECTS
        #define HAL_MAX_EFFECTS         24
    #endif

    /* --- Memory Budgets --- */
    #ifndef HAL_ENTITY_RAM_BUDGET
        #define HAL_ENTITY_RAM_BUDGET   2048    /* Bytes for entity pools */
    #endif
    #ifndef HAL_SCRATCH_RAM
        #define HAL_SCRATCH_RAM         512     /* Bytes for temp buffers */
    #endif

    /* --- Performance Hints --- */
    #ifndef HAL_COLLISION_BUDGET
        #define HAL_COLLISION_BUDGET    256     /* Max collision checks/frame */
    #endif
    #ifndef HAL_UPDATE_BUDGET
        #define HAL_UPDATE_BUDGET       128     /* Max entity updates/frame */
    #endif

    /* --- AI Complexity --- */
    #ifndef HAL_AI_PATHFIND
        #define HAL_AI_PATHFIND         1       /* Basic pathfinding */
    #endif
    #ifndef HAL_AI_GROUP_BEHAVIOR
        #define HAL_AI_GROUP_BEHAVIOR   0       /* No group AI */
    #endif
    #ifndef HAL_AI_PREDICTION
        #define HAL_AI_PREDICTION       4       /* 4 frames prediction */
    #endif
    #ifndef HAL_AI_UPDATE_SPLIT
        #define HAL_AI_UPDATE_SPLIT     2       /* Update 1/2 enemies per frame */
    #endif

    /* --- Physics Precision --- */
    #ifndef HAL_FIXED_POINT_BITS
        #define HAL_FIXED_POINT_BITS    8       /* 8.8 fixed point */
    #endif

    /* --- Feature Flags --- */
    #ifndef HAL_HAS_FAST_MULTIPLY
        #define HAL_HAS_FAST_MULTIPLY   1
    #endif
    #ifndef HAL_HAS_DIVIDE
        #define HAL_HAS_DIVIDE          1
    #endif
    #ifndef HAL_USE_SPLIT_TABLES
        #define HAL_USE_SPLIT_TABLES    0       /* 16-bit CPUs can use word tables */
    #endif

/* ===========================================================================
 * TIER_STANDARD_PLUS Defaults (Neo Geo, Sega CD)
 * ===========================================================================
 * Design target: Neo Geo capabilities (fast 68K, huge sprite RAM)
 * These are "enhanced 16-bit" - 16-bit sprite aesthetic but more CPU/RAM
 * Sega CD: Dual 68000, 768KB RAM, CD streaming
 * Neo Geo: 68000 @ 12MHz, 330KB dedicated sprite RAM
 */

#elif HAL_TIER == HAL_TIER_STANDARD_PLUS

    /* --- Entity Limits --- */
    #ifndef HAL_MAX_ENTITIES
        #define HAL_MAX_ENTITIES        192
    #endif
    #ifndef HAL_MAX_ENEMIES
        #define HAL_MAX_ENEMIES         72
    #endif
    #ifndef HAL_MAX_PROJECTILES
        #define HAL_MAX_PROJECTILES     72
    #endif
    #ifndef HAL_MAX_PICKUPS
        #define HAL_MAX_PICKUPS         48
    #endif
    #ifndef HAL_MAX_EFFECTS
        #define HAL_MAX_EFFECTS         32
    #endif

    /* --- Memory Budgets --- */
    #ifndef HAL_ENTITY_RAM_BUDGET
        #define HAL_ENTITY_RAM_BUDGET   4096    /* Bytes for entity pools */
    #endif
    #ifndef HAL_SCRATCH_RAM
        #define HAL_SCRATCH_RAM         1024    /* Bytes for temp buffers */
    #endif

    /* --- Performance Hints --- */
    #ifndef HAL_COLLISION_BUDGET
        #define HAL_COLLISION_BUDGET    384     /* Max collision checks/frame */
    #endif
    #ifndef HAL_UPDATE_BUDGET
        #define HAL_UPDATE_BUDGET       192     /* Max entity updates/frame */
    #endif

    /* --- AI Complexity --- */
    #ifndef HAL_AI_PATHFIND
        #define HAL_AI_PATHFIND         1       /* Full pathfinding */
    #endif
    #ifndef HAL_AI_GROUP_BEHAVIOR
        #define HAL_AI_GROUP_BEHAVIOR   1       /* Group AI enabled */
    #endif
    #ifndef HAL_AI_PREDICTION
        #define HAL_AI_PREDICTION       6       /* 6 frames prediction */
    #endif
    #ifndef HAL_AI_UPDATE_SPLIT
        #define HAL_AI_UPDATE_SPLIT     1       /* Update all enemies every frame */
    #endif

    /* --- Physics Precision --- */
    #ifndef HAL_FIXED_POINT_BITS
        #define HAL_FIXED_POINT_BITS    12      /* 12.12 fixed point (68K sweet spot) */
    #endif

    /* --- Feature Flags --- */
    #ifndef HAL_HAS_FAST_MULTIPLY
        #define HAL_HAS_FAST_MULTIPLY   1
    #endif
    #ifndef HAL_HAS_DIVIDE
        #define HAL_HAS_DIVIDE          1
    #endif
    #ifndef HAL_USE_SPLIT_TABLES
        #define HAL_USE_SPLIT_TABLES    0
    #endif

/* ===========================================================================
 * TIER_EXTENDED Defaults (GBA, DS)
 * ===========================================================================
 * Design target: DS capabilities (ARM9, 4MB RAM, dual screens)
 * Reduce for: GBA (single screen, less RAM)
 */

#elif HAL_TIER == HAL_TIER_EXTENDED

    /* --- Entity Limits --- */
    #ifndef HAL_MAX_ENTITIES
        #define HAL_MAX_ENTITIES        256
    #endif
    #ifndef HAL_MAX_ENEMIES
        #define HAL_MAX_ENEMIES         96
    #endif
    #ifndef HAL_MAX_PROJECTILES
        #define HAL_MAX_PROJECTILES     96
    #endif
    #ifndef HAL_MAX_PICKUPS
        #define HAL_MAX_PICKUPS         64
    #endif
    #ifndef HAL_MAX_EFFECTS
        #define HAL_MAX_EFFECTS         48
    #endif

    /* --- Memory Budgets --- */
    #ifndef HAL_ENTITY_RAM_BUDGET
        #define HAL_ENTITY_RAM_BUDGET   8192    /* Bytes for entity pools */
    #endif
    #ifndef HAL_SCRATCH_RAM
        #define HAL_SCRATCH_RAM         2048    /* Bytes for temp buffers */
    #endif

    /* --- Performance Hints --- */
    #ifndef HAL_COLLISION_BUDGET
        #define HAL_COLLISION_BUDGET    512     /* Max collision checks/frame */
    #endif
    #ifndef HAL_UPDATE_BUDGET
        #define HAL_UPDATE_BUDGET       256     /* Max entity updates/frame */
    #endif

    /* --- AI Complexity --- */
    #ifndef HAL_AI_PATHFIND
        #define HAL_AI_PATHFIND         1       /* Full pathfinding */
    #endif
    #ifndef HAL_AI_GROUP_BEHAVIOR
        #define HAL_AI_GROUP_BEHAVIOR   1       /* Group AI enabled */
    #endif
    #ifndef HAL_AI_PREDICTION
        #define HAL_AI_PREDICTION       8       /* 8 frames prediction */
    #endif
    #ifndef HAL_AI_UPDATE_SPLIT
        #define HAL_AI_UPDATE_SPLIT     1       /* Update all enemies every frame */
    #endif

    /* --- Physics Precision --- */
    #ifndef HAL_FIXED_POINT_BITS
        #define HAL_FIXED_POINT_BITS    16      /* 16.16 fixed point */
    #endif

    /* --- Feature Flags --- */
    #ifndef HAL_HAS_FAST_MULTIPLY
        #define HAL_HAS_FAST_MULTIPLY   1
    #endif
    #ifndef HAL_HAS_DIVIDE
        #define HAL_HAS_DIVIDE          1
    #endif
    #ifndef HAL_USE_SPLIT_TABLES
        #define HAL_USE_SPLIT_TABLES    0
    #endif

#else
    #error "Unknown HAL_TIER value"
#endif

/* ===========================================================================
 * Derived Limits (calculated from tier values)
 * =========================================================================== */

/* Total entity pool size (should fit in HAL_ENTITY_RAM_BUDGET) */
#define HAL_ENTITY_POOL_SIZE    (HAL_MAX_ENEMIES + HAL_MAX_PROJECTILES + \
                                 HAL_MAX_PICKUPS + HAL_MAX_EFFECTS + 1)

/* Verify pool fits in budget (1 = player) */
/* Each entity is 16 bytes */
#if (HAL_ENTITY_POOL_SIZE * 16) > HAL_ENTITY_RAM_BUDGET
    #warning "Entity pools exceed HAL_ENTITY_RAM_BUDGET"
#endif

/* ===========================================================================
 * Limit IDs for hal_get_limit()
 * =========================================================================== */

#define HAL_LIMIT_ENTITIES      0
#define HAL_LIMIT_ENEMIES       1
#define HAL_LIMIT_PROJECTILES   2
#define HAL_LIMIT_PICKUPS       3
#define HAL_LIMIT_EFFECTS       4
#define HAL_LIMIT_COLLISION     5
#define HAL_LIMIT_UPDATE        6
#define HAL_LIMIT_COUNT         7   /* Number of limit types */

/* ===========================================================================
 * Tier Name Strings (for debug/logging)
 * =========================================================================== */

#if HAL_TIER == HAL_TIER_MINIMAL
    #define HAL_TIER_NAME "MINIMAL"
#elif HAL_TIER == HAL_TIER_MINIMAL_PLUS
    #define HAL_TIER_NAME "MINIMAL_PLUS"
#elif HAL_TIER == HAL_TIER_STANDARD
    #define HAL_TIER_NAME "STANDARD"
#elif HAL_TIER == HAL_TIER_STANDARD_PLUS
    #define HAL_TIER_NAME "STANDARD_PLUS"
#elif HAL_TIER == HAL_TIER_EXTENDED
    #define HAL_TIER_NAME "EXTENDED"
#endif

/* Asset tier name (may differ from logic tier) */
#if HAL_TIER_ASSETS == HAL_TIER_MINIMAL
    #define HAL_TIER_ASSETS_NAME "MINIMAL"
#elif HAL_TIER_ASSETS == HAL_TIER_MINIMAL_PLUS
    #define HAL_TIER_ASSETS_NAME "MINIMAL_PLUS"
#elif HAL_TIER_ASSETS == HAL_TIER_STANDARD
    #define HAL_TIER_ASSETS_NAME "STANDARD"
#elif HAL_TIER_ASSETS == HAL_TIER_STANDARD_PLUS
    #define HAL_TIER_ASSETS_NAME "STANDARD_PLUS"
#elif HAL_TIER_ASSETS == HAL_TIER_EXTENDED
    #define HAL_TIER_ASSETS_NAME "EXTENDED"
#endif

/* Logic tier name (may differ from asset tier) */
#if HAL_TIER_LOGIC == HAL_TIER_MINIMAL
    #define HAL_TIER_LOGIC_NAME "MINIMAL"
#elif HAL_TIER_LOGIC == HAL_TIER_MINIMAL_PLUS
    #define HAL_TIER_LOGIC_NAME "MINIMAL_PLUS"
#elif HAL_TIER_LOGIC == HAL_TIER_STANDARD
    #define HAL_TIER_LOGIC_NAME "STANDARD"
#elif HAL_TIER_LOGIC == HAL_TIER_STANDARD_PLUS
    #define HAL_TIER_LOGIC_NAME "STANDARD_PLUS"
#elif HAL_TIER_LOGIC == HAL_TIER_EXTENDED
    #define HAL_TIER_LOGIC_NAME "EXTENDED"
#endif

#endif /* ARDK_HAL_TIERS_H */
