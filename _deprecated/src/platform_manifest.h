/*
 * =============================================================================
 * ARDK - Platform Manifest System
 * platform_manifest.h - Compile-time platform capability declaration
 * =============================================================================
 *
 * Each platform declares its full capabilities in one place. This enables:
 *
 *   1. Build validation - Catch incompatible features at compile time
 *   2. Asset validation - Verify assets fit platform constraints
 *   3. Code generation - Auto-generate optimal code paths
 *   4. Documentation - Single source of truth for platform specs
 *
 * USAGE:
 *   Platform hal_config.h defines HAL_PLATFORM_MANIFEST before including this.
 *   Build tools read manifest to validate and optimize.
 *
 * =============================================================================
 */

#ifndef ARDK_PLATFORM_MANIFEST_H
#define ARDK_PLATFORM_MANIFEST_H

/* ===========================================================================
 * Platform Identification
 * =========================================================================== */

/* Platform family (for shared code paths) */
#define ARDK_FAMILY_6502        0x01    /* NES, C64, Atari, etc. */
#define ARDK_FAMILY_Z80         0x02    /* SMS, Game Gear, GB, etc. */
#define ARDK_FAMILY_68K         0x03    /* Genesis, Neo Geo, etc. */
#define ARDK_FAMILY_65816       0x04    /* SNES */
#define ARDK_FAMILY_ARM         0x05    /* GBA, DS, etc. */

/* Endianness */
#define ARDK_ENDIAN_LITTLE      0x00
#define ARDK_ENDIAN_BIG         0x01

/* ===========================================================================
 * CPU Family Groupings
 *
 * Systems grouped by CPU architecture for code migration.
 * Each family shares an assembly HAL file (hal_6502.inc, hal_68k.inc, etc.)
 *
 * PRIMARY TARGETS (robust dev pipelines):
 *   - NES (6502)
 *   - Mega Drive / Genesis (68K)
 *   - Game Boy (Z80-like LR35902)
 *
 * MIGRATION PATHS:
 *   - NES code → C64, PCE, Atari 2600/7800
 *   - Genesis code → Amiga, Neo Geo, X68000
 *   - Game Boy code → SMS, Game Gear, MSX
 * =========================================================================== */

/* 6502 Family - Little-endian 8-bit, 64K address space */
#define ARDK_PLAT_NES           0x0100  /* Primary target */
#define ARDK_PLAT_C64           0x0101  /* Commodore 64 */
#define ARDK_PLAT_PCE           0x0102  /* PC Engine / TurboGrafx (HuC6280 = 65C02) */
#define ARDK_PLAT_ATARI2600     0x0103  /* Atari 2600 */
#define ARDK_PLAT_ATARI7800     0x0104  /* Atari 7800 */
#define ARDK_PLAT_APPLE2        0x0105  /* Apple II */
#define ARDK_PLAT_BBC           0x0106  /* BBC Micro */

/* Z80 Family - Little-endian 8-bit, 64K address space */
#define ARDK_PLAT_GB            0x0200  /* Primary target (LR35902) */
#define ARDK_PLAT_GBC           0x0201  /* Game Boy Color */
#define ARDK_PLAT_SMS           0x0202  /* Sega Master System (MINIMAL_PLUS peak) */
#define ARDK_PLAT_GG            0x0203  /* Sega Game Gear */
#define ARDK_PLAT_MSX           0x0204  /* MSX */
#define ARDK_PLAT_MSX2          0x0205  /* MSX2 (MINIMAL_PLUS) */
#define ARDK_PLAT_ZX            0x0206  /* ZX Spectrum */
#define ARDK_PLAT_COLECO        0x0207  /* ColecoVision */
#define ARDK_PLAT_NGP           0x0208  /* Neo Geo Pocket (MINIMAL_PLUS floor) */
#define ARDK_PLAT_NGPC          0x0209  /* Neo Geo Pocket Color */

/* 68000 Family - Big-endian 16/32-bit, 16MB address space */
#define ARDK_PLAT_GENESIS       0x0300  /* Primary target */
#define ARDK_PLAT_MEGADRIVE     0x0300  /* Alias for Genesis */
#define ARDK_PLAT_AMIGA_OCS     0x0301  /* Amiga OCS/ECS (STANDARD tier) */
#define ARDK_PLAT_AMIGA_AGA     0x0605  /* Amiga AGA (RETRO_PC peak - 68020+) */
#define ARDK_PLAT_NEOGEO        0x0303  /* Neo Geo AES/MVS */
#define ARDK_PLAT_X68000        0x0304  /* Sharp X68000 */
#define ARDK_PLAT_SEGACD        0x0305  /* Sega CD (68K + sub-68K) */
#define ARDK_PLAT_32X           0x0306  /* 32X (SH-2, but 68K for main) */

/* 65816 Family - 16-bit extension of 6502 */
#define ARDK_PLAT_SNES          0x0400  /* Super Nintendo */
#define ARDK_PLAT_SFC           0x0400  /* Alias for SNES */

/* ARM Family - 32-bit RISC */
#define ARDK_PLAT_GBA           0x0500  /* Game Boy Advance */
#define ARDK_PLAT_NDS           0x0501  /* Nintendo DS */

/* RETRO_PC Family - VGA-era platforms (x86, 68K-based computers)
 * This is the "reference implementation" tier for faux-retro development.
 * Design here first, then downsample to actual retro platforms. */
#define ARDK_FAMILY_RETRO_PC    0x06    /* DOS/VGA, Amiga AGA, Atari ST */

#define ARDK_PLAT_DOS_VGA       0x0600  /* DOS Mode 13h/X (320x200@256) */
#define ARDK_PLAT_DOS_MODEX     0x0601  /* DOS Mode X (320x240@256, page flip) */
#define ARDK_PLAT_ATARI_ST      0x0602  /* Atari ST (68000@8MHz, 512KB) */
#define ARDK_PLAT_ATARI_FALCON  0x0603  /* Atari Falcon (68030, DSP) */
#define ARDK_PLAT_PC98          0x0604  /* NEC PC-98 (640x400, Japan) */

/* ===========================================================================
 * Assembly HAL Selection
 *
 * Maps platform to appropriate assembly HAL include file.
 * =========================================================================== */

#define ARDK_ASM_HAL_6502       "hal/asm/hal_6502.inc"
#define ARDK_ASM_HAL_68K        "hal/asm/hal_68k.inc"
#define ARDK_ASM_HAL_Z80_GB     "hal/asm/hal_z80_gb.inc"
#define ARDK_ASM_HAL_RETRO_PC   "hal/asm/hal_retro_pc.inc"  /* x86 or C-based */

/* Helper: Get ASM HAL path from family */
#define ARDK_GET_ASM_HAL(family) \
    (((family) == ARDK_FAMILY_6502) ? ARDK_ASM_HAL_6502 : \
     ((family) == ARDK_FAMILY_68K) ? ARDK_ASM_HAL_68K : \
     ((family) == ARDK_FAMILY_Z80) ? ARDK_ASM_HAL_Z80_GB : \
     ((family) == ARDK_FAMILY_RETRO_PC) ? ARDK_ASM_HAL_RETRO_PC : \
     "")

/* Helper: Get family from platform ID */
#define ARDK_PLATFORM_TO_FAMILY(plat) (((plat) >> 8) & 0xFF)

/* ===========================================================================
 * Family-Specific Constraints
 *
 * Compile-time checks based on CPU architecture.
 * =========================================================================== */

#if defined(HAL_MANIFEST_FAMILY)

#if HAL_MANIFEST_FAMILY == ARDK_FAMILY_6502
    /* 6502: 256-byte stack, ZP indirect addressing */
    #define ARDK_STACK_SIZE         256
    #define ARDK_HAS_INDEX_REG      0       /* No true index registers */
    #define ARDK_HAS_MULTIPLY       0       /* No hardware multiply */
    #define ARDK_MAX_DIRECT_ADDR    0xFFFF  /* 64K address space */
#endif

#if HAL_MANIFEST_FAMILY == ARDK_FAMILY_Z80
    /* Z80: 16-bit stack, IX/IY index registers (not on GB) */
    #define ARDK_STACK_SIZE         65536   /* Full address space */
    #define ARDK_HAS_INDEX_REG      1       /* IX/IY (standard Z80 only) */
    #define ARDK_HAS_MULTIPLY       0       /* No hardware multiply */
    #define ARDK_MAX_DIRECT_ADDR    0xFFFF  /* 64K address space */
#endif

#if HAL_MANIFEST_FAMILY == ARDK_FAMILY_68K
    /* 68000: 16MB address space, 8 data + 8 address registers */
    #define ARDK_STACK_SIZE         65536   /* Practical stack limit */
    #define ARDK_HAS_INDEX_REG      8       /* A0-A7 address registers */
    #define ARDK_HAS_MULTIPLY       1       /* MULU/MULS instructions */
    #define ARDK_MAX_DIRECT_ADDR    0xFFFFFF /* 16MB address space */
#endif

#if HAL_MANIFEST_FAMILY == ARDK_FAMILY_RETRO_PC
    /* RETRO_PC: VGA-era platforms, generous limits, software rendering */
    #define ARDK_STACK_SIZE         65536   /* x86 stack is large */
    #define ARDK_HAS_INDEX_REG      1       /* SI/DI or various depending on platform */
    #define ARDK_HAS_MULTIPLY       1       /* All RETRO_PC platforms have multiply */
    #define ARDK_MAX_DIRECT_ADDR    0xFFFFFF /* 16MB on 386, more on later */
    #define ARDK_HAS_FRAMEBUFFER    1       /* Linear or planar framebuffer */
#endif

#endif /* HAL_MANIFEST_FAMILY */

/* ===========================================================================
 * Migration Compatibility Flags
 *
 * Check if code from one platform can run on another.
 * =========================================================================== */

/* Check if target platform is in same family (basic compatibility) */
#define ARDK_SAME_FAMILY(src_plat, dst_plat) \
    (ARDK_PLATFORM_TO_FAMILY(src_plat) == ARDK_PLATFORM_TO_FAMILY(dst_plat))

/* Check if migration requires only minor changes */
#define ARDK_EASY_MIGRATION(src_plat, dst_plat) \
    (ARDK_SAME_FAMILY(src_plat, dst_plat) && \
     ((src_plat) == (dst_plat) || \
      ((src_plat) == ARDK_PLAT_NES && (dst_plat) == ARDK_PLAT_C64) || \
      ((src_plat) == ARDK_PLAT_GB && (dst_plat) == ARDK_PLAT_GBC) || \
      ((src_plat) == ARDK_PLAT_GENESIS && (dst_plat) == ARDK_PLAT_NEOGEO)))

/* ===========================================================================
 * Video System Capabilities
 * =========================================================================== */

/* Sprite size modes */
#define ARDK_SPRITE_SIZE_8x8        0x0001
#define ARDK_SPRITE_SIZE_8x16       0x0002
#define ARDK_SPRITE_SIZE_16x16      0x0004
#define ARDK_SPRITE_SIZE_16x32      0x0008
#define ARDK_SPRITE_SIZE_32x32      0x0010
#define ARDK_SPRITE_SIZE_VARIABLE   0x0100  /* Can mix sizes */

/* Background modes */
#define ARDK_BG_MODE_TILE           0x0001  /* Tile-based background */
#define ARDK_BG_MODE_BITMAP         0x0002  /* Bitmap mode (GBA) */
#define ARDK_BG_MODE_AFFINE         0x0004  /* Rotation/scaling (Mode 7) */

/* Scroll capabilities */
#define ARDK_SCROLL_X               0x0001
#define ARDK_SCROLL_Y               0x0002
#define ARDK_SCROLL_PER_LINE        0x0004  /* Per-scanline scroll */
#define ARDK_SCROLL_PER_TILE        0x0008  /* Per-tile column scroll */

/* ===========================================================================
 * Audio System Capabilities
 * =========================================================================== */

/* Audio channel types */
#define ARDK_AUDIO_PULSE            0x0001  /* Square/pulse wave */
#define ARDK_AUDIO_TRIANGLE         0x0002  /* Triangle wave */
#define ARDK_AUDIO_NOISE            0x0004  /* Noise channel */
#define ARDK_AUDIO_PCM              0x0008  /* PCM/sample playback */
#define ARDK_AUDIO_FM               0x0010  /* FM synthesis */
#define ARDK_AUDIO_WAVETABLE        0x0020  /* Wavetable synthesis */

/* ===========================================================================
 * Memory Architecture
 * =========================================================================== */

/* Memory mapping style */
#define ARDK_MEM_LINEAR             0x00    /* Flat address space */
#define ARDK_MEM_BANKED             0x01    /* Bank-switched ROM/RAM */
#define ARDK_MEM_SEGMENTED          0x02    /* Segmented (68K style) */

/* ===========================================================================
 * Platform Manifest Structure
 *
 * Defined as compile-time constants in each platform's hal_config.h
 * =========================================================================== */

#ifdef HAL_PLATFORM_MANIFEST

/*
 * Example manifest (NES):
 *
 * #define HAL_MANIFEST_NAME           "NES"
 * #define HAL_MANIFEST_FAMILY         ARDK_FAMILY_6502
 * #define HAL_MANIFEST_ENDIAN         ARDK_ENDIAN_LITTLE
 * #define HAL_MANIFEST_CPU_MHZ        1790     // kHz actually (1.79 MHz)
 * #define HAL_MANIFEST_WORD_SIZE      8
 *
 * // Video
 * #define HAL_MANIFEST_SCREEN_W       256
 * #define HAL_MANIFEST_SCREEN_H       240
 * #define HAL_MANIFEST_COLORS         52       // Master palette colors
 * #define HAL_MANIFEST_PALETTES       8        // 4 sprite + 4 BG
 * #define HAL_MANIFEST_COLORS_PER_PAL 4        // Including transparent
 * #define HAL_MANIFEST_SPRITES_TOTAL  64
 * #define HAL_MANIFEST_SPRITES_LINE   8
 * #define HAL_MANIFEST_SPRITE_SIZES   (ARDK_SPRITE_SIZE_8x8 | ARDK_SPRITE_SIZE_8x16)
 * #define HAL_MANIFEST_BG_LAYERS      1
 * #define HAL_MANIFEST_BG_MODES       ARDK_BG_MODE_TILE
 * #define HAL_MANIFEST_SCROLL_CAPS    (ARDK_SCROLL_X | ARDK_SCROLL_Y)
 *
 * // Memory
 * #define HAL_MANIFEST_RAM_INTERNAL   2048
 * #define HAL_MANIFEST_RAM_MAPPER     8192     // MMC3 WRAM
 * #define HAL_MANIFEST_VRAM           2048
 * #define HAL_MANIFEST_OAM            256
 * #define HAL_MANIFEST_MEM_MODEL      ARDK_MEM_BANKED
 *
 * // Audio
 * #define HAL_MANIFEST_AUDIO_CHANS    5
 * #define HAL_MANIFEST_AUDIO_TYPES    (ARDK_AUDIO_PULSE | ARDK_AUDIO_TRIANGLE | ARDK_AUDIO_NOISE | ARDK_AUDIO_PCM)
 */

#endif /* HAL_PLATFORM_MANIFEST */

/* ===========================================================================
 * Compile-Time Validation Macros
 *
 * Use these to catch platform incompatibilities at compile time.
 * =========================================================================== */

/* Check if sprite size is supported */
#define ARDK_VALIDATE_SPRITE_SIZE(w, h) \
    ((((w) == 8 && (h) == 8) && (HAL_MANIFEST_SPRITE_SIZES & ARDK_SPRITE_SIZE_8x8)) || \
     (((w) == 8 && (h) == 16) && (HAL_MANIFEST_SPRITE_SIZES & ARDK_SPRITE_SIZE_8x16)) || \
     (((w) == 16 && (h) == 16) && (HAL_MANIFEST_SPRITE_SIZES & ARDK_SPRITE_SIZE_16x16)) || \
     (((w) == 32 && (h) == 32) && (HAL_MANIFEST_SPRITE_SIZES & ARDK_SPRITE_SIZE_32x32)))

/* Check if scroll mode is supported */
#define ARDK_VALIDATE_SCROLL(mode) \
    ((HAL_MANIFEST_SCROLL_CAPS & (mode)) == (mode))

/* Check if audio type is supported */
#define ARDK_VALIDATE_AUDIO(type) \
    ((HAL_MANIFEST_AUDIO_TYPES & (type)) != 0)

/* ===========================================================================
 * Platform Comparison Helpers
 *
 * For conditional compilation based on relative capabilities.
 * =========================================================================== */

/* True if platform has more RAM than threshold */
#define ARDK_HAS_RAM_GTE(bytes)     (HAL_MANIFEST_RAM_INTERNAL >= (bytes))

/* True if platform has more sprites per line than threshold */
#define ARDK_HAS_SPR_LINE_GTE(n)    (HAL_MANIFEST_SPRITES_LINE >= (n))

/* True if platform has per-line scroll */
#define ARDK_HAS_LINE_SCROLL        (HAL_MANIFEST_SCROLL_CAPS & ARDK_SCROLL_PER_LINE)

/* True if platform has FM audio */
#define ARDK_HAS_FM_AUDIO           (HAL_MANIFEST_AUDIO_TYPES & ARDK_AUDIO_FM)

/* ===========================================================================
 * Feature Scaling Macros
 *
 * Automatically scale features based on platform capability.
 * =========================================================================== */

/* Scale enemy count based on RAM and sprite limits */
#define ARDK_SCALE_ENEMIES(base) \
    ((base) * HAL_MANIFEST_SPRITES_LINE / 8)

/* Scale effect complexity based on CPU speed */
#define ARDK_SCALE_EFFECTS(base) \
    ((HAL_MANIFEST_CPU_MHZ > 5000) ? (base) * 2 : (base))

/* ===========================================================================
 * Runtime Manifest Query (Optional)
 *
 * For platforms that need runtime feature detection.
 * =========================================================================== */

typedef struct {
    const char* name;
    u16     platform_id;        /* ARDK_PLAT_xxx */
    u8      family;             /* ARDK_FAMILY_xxx */
    u8      tier;               /* HAL_TIER_xxx */
    u8      endian;
    u8      word_size;
    u16     cpu_khz;
    u16     screen_w;
    u16     screen_h;
    u8      colors;
    u8      palettes;
    u8      colors_per_pal;
    u8      sprites_total;
    u8      sprites_line;
    u16     sprite_sizes;
    u8      bg_layers;
    u8      bg_modes;
    u16     scroll_caps;
    u32     ram_internal;
    u32     ram_mapper;
    u16     vram;
    u8      audio_chans;
    u16     audio_types;
    const char* asm_hal_path;   /* Path to family's assembly HAL */
} ARDK_PlatformManifest;

/* Get manifest for current platform (implemented in hal_xxx.c) */
const ARDK_PlatformManifest* hal_get_manifest(void);

/* ===========================================================================
 * Family Capability Queries
 *
 * Runtime queries for family-specific features.
 * =========================================================================== */

/* Get list of platforms in same family */
typedef struct {
    u16     platform_id;
    const char* name;
    const char* notes;          /* Migration notes */
} ARDK_FamilyMember;

/* Family member tables (defined in hal_common.c) */
extern const ARDK_FamilyMember ardk_family_6502[];
extern const ARDK_FamilyMember ardk_family_z80[];
extern const ARDK_FamilyMember ardk_family_68k[];

/* Get family members array and count */
const ARDK_FamilyMember* hal_get_family_members(u8 family, u8* count);

/* Check if current platform can migrate to target */
u8 hal_check_migration(u16 target_platform);

/* Migration difficulty levels */
#define ARDK_MIGRATE_SAME       0   /* Same platform */
#define ARDK_MIGRATE_TRIVIAL    1   /* Same family, same graphics chip */
#define ARDK_MIGRATE_EASY       2   /* Same family, different graphics */
#define ARDK_MIGRATE_MODERATE   3   /* Same family, significant differences */
#define ARDK_MIGRATE_HARD       4   /* Different family, similar tier */
#define ARDK_MIGRATE_IMPOSSIBLE 255 /* Cannot migrate */

#endif /* ARDK_PLATFORM_MANIFEST_H */
