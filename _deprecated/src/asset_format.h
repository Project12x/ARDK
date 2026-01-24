/*
 * =============================================================================
 * ARDK - Intermediate Asset Format
 * asset_format.h - Platform-agnostic asset bundle specification
 * =============================================================================
 *
 * ARDK uses an intermediate asset format that decouples asset creation from
 * platform-specific export. This allows:
 *
 *   1. Process once, export many - Assets processed once, then exported per-platform
 *   2. Metadata preservation - Colors, hotspots, collision preserved across exports
 *   3. Automatic optimization - Per-platform palette reduction, tile deduplication
 *   4. Validation - Catch errors before platform-specific export
 *
 * PIPELINE:
 *   Source (PNG/Aseprite) → ARDK Bundle (.ardk) → Platform Export (CHR/tiles)
 *
 * BUNDLE STRUCTURE:
 *   - Header (magic, version, asset count)
 *   - Asset table (type, ID, offset, size for each asset)
 *   - Asset data (sprites, palettes, tilemaps, etc.)
 *   - Metadata (names, tags, collision boxes)
 *
 * This file defines the binary format. Tools read/write this format.
 * Game code never sees this - it only sees platform-specific exports.
 * =============================================================================
 */

#ifndef ARDK_ASSET_FORMAT_H
#define ARDK_ASSET_FORMAT_H

#include "types.h"

/* ===========================================================================
 * Bundle Header
 * =========================================================================== */

#define ARDK_BUNDLE_MAGIC       0x41524B44  /* "ARKD" in ASCII */
#define ARDK_BUNDLE_VERSION     1

typedef struct {
    u32     magic;          /* ARDK_BUNDLE_MAGIC */
    u16     version;        /* Format version */
    u16     asset_count;    /* Number of assets in bundle */
    u32     data_offset;    /* Offset to asset data section */
    u32     meta_offset;    /* Offset to metadata section */
    u32     total_size;     /* Total bundle size in bytes */
    u8      flags;          /* Bundle flags */
    u8      reserved[3];    /* Padding to 24 bytes */
} ARDK_BundleHeader;

/* Bundle flags */
#define ARDK_BUNDLE_COMPRESSED  0x01    /* Data section is compressed */
#define ARDK_BUNDLE_ENCRYPTED   0x02    /* Bundle is encrypted (future) */

/* ===========================================================================
 * Asset Types
 * =========================================================================== */

#define ARDK_ASSET_SPRITE       0x01    /* Single sprite or sprite sheet */
#define ARDK_ASSET_METASPRITE   0x02    /* Multi-tile sprite with offsets */
#define ARDK_ASSET_TILESET      0x03    /* Background tileset */
#define ARDK_ASSET_TILEMAP      0x04    /* Tile arrangement (level/screen) */
#define ARDK_ASSET_PALETTE      0x05    /* Color palette */
#define ARDK_ASSET_ANIMATION    0x06    /* Animation sequence */
#define ARDK_ASSET_COLLISION    0x07    /* Collision map/shapes */
#define ARDK_ASSET_AUDIO_SFX    0x10    /* Sound effect */
#define ARDK_ASSET_AUDIO_MUSIC  0x11    /* Music track */
#define ARDK_ASSET_DATA_RAW     0x20    /* Raw binary data */
#define ARDK_ASSET_DATA_TABLE   0x21    /* Lookup table */

/* ===========================================================================
 * Asset Table Entry
 * =========================================================================== */

typedef struct {
    u8      type;           /* ARDK_ASSET_* */
    u8      id;             /* Asset ID (matches asset_ids.h) */
    u16     flags;          /* Asset-specific flags */
    u32     offset;         /* Offset from data_offset */
    u32     size;           /* Size in bytes */
    u16     width;          /* Width in pixels (sprites/tiles) or entries (tables) */
    u16     height;         /* Height in pixels or 0 */
} ARDK_AssetEntry;

/* Asset flags (common) */
#define ARDK_ASSET_FLAG_REQUIRED    0x0001  /* Must be loaded */
#define ARDK_ASSET_FLAG_PRELOAD     0x0002  /* Load at startup */
#define ARDK_ASSET_FLAG_STREAM      0x0004  /* Can be streamed */

/* Sprite-specific flags */
#define ARDK_SPRITE_FLAG_ANIMATED   0x0010  /* Has animation data */
#define ARDK_SPRITE_FLAG_HOTSPOT    0x0020  /* Has hotspot/origin */
#define ARDK_SPRITE_FLAG_COLLISION  0x0040  /* Has collision box */

/* ===========================================================================
 * Sprite Asset Data
 *
 * Stored in 32-bit RGBA format for maximum compatibility.
 * Platform exporters quantize to target palette.
 * =========================================================================== */

typedef struct {
    u16     width;          /* Sprite width in pixels */
    u16     height;         /* Sprite height in pixels */
    i8      hotspot_x;      /* Origin X offset (for positioning) */
    i8      hotspot_y;      /* Origin Y offset */
    u8      frame_count;    /* Number of animation frames (1 if static) */
    u8      bpp;            /* Bits per pixel in data (8, 16, 24, 32) */
    /* Followed by: pixel data (width * height * (bpp/8) * frame_count bytes) */
} ARDK_SpriteHeader;

/* ===========================================================================
 * Metasprite Asset Data
 *
 * Defines a multi-tile sprite as a collection of positioned tiles.
 * Platform exporters convert to platform-specific metasprite format.
 * =========================================================================== */

typedef struct {
    i8      x_offset;       /* X position relative to metasprite origin */
    i8      y_offset;       /* Y position relative to metasprite origin */
    u8      tile_index;     /* Index into associated tileset */
    u8      attributes;     /* Flip flags, palette (platform-agnostic encoding) */
} ARDK_MetaspriteTile;

#define ARDK_META_FLIP_H    0x01
#define ARDK_META_FLIP_V    0x02
#define ARDK_META_PAL_MASK  0x30
#define ARDK_META_PAL_SHIFT 4

typedef struct {
    u8      tile_count;     /* Number of tiles in metasprite */
    u8      tileset_id;     /* Associated tileset asset ID */
    i8      hitbox_x;       /* Collision box X offset */
    i8      hitbox_y;       /* Collision box Y offset */
    u8      hitbox_w;       /* Collision box width */
    u8      hitbox_h;       /* Collision box height */
    u8      reserved[2];
    /* Followed by: tile_count * ARDK_MetaspriteTile */
} ARDK_MetaspriteHeader;

/* ===========================================================================
 * Palette Asset Data
 *
 * Stored as 24-bit RGB. Platform exporters quantize to target.
 * =========================================================================== */

typedef struct {
    u8      color_count;    /* Number of colors (4, 16, 256 typical) */
    u8      format;         /* ARDK_PAL_* */
    u8      reserved[2];
    /* Followed by: color_count * 3 bytes (RGB) or 4 bytes (RGBA) */
} ARDK_PaletteHeader;

#define ARDK_PAL_RGB24      0x00    /* 3 bytes per color */
#define ARDK_PAL_RGBA32     0x01    /* 4 bytes per color */
#define ARDK_PAL_INDEXED    0x02    /* References master palette */

/* ===========================================================================
 * Animation Asset Data
 *
 * Defines frame timing for animated sprites.
 * =========================================================================== */

typedef struct {
    u8      frame_index;    /* Sprite frame to display */
    u8      duration;       /* Duration in game frames (1/60s units) */
    u8      flags;          /* Per-frame flags */
    u8      reserved;
} ARDK_AnimationFrame;

#define ARDK_ANIM_FLAG_FLIP_H   0x01    /* Flip this frame horizontally */
#define ARDK_ANIM_FLAG_FLIP_V   0x02    /* Flip this frame vertically */
#define ARDK_ANIM_FLAG_EVENT    0x04    /* Trigger event callback */

typedef struct {
    u8      frame_count;    /* Number of frames in animation */
    u8      loop_mode;      /* ARDK_LOOP_* */
    u8      sprite_id;      /* Associated sprite asset */
    u8      reserved;
    /* Followed by: frame_count * ARDK_AnimationFrame */
} ARDK_AnimationHeader;

#define ARDK_LOOP_NONE      0x00    /* Play once and stop */
#define ARDK_LOOP_FORWARD   0x01    /* Loop from start */
#define ARDK_LOOP_PINGPONG  0x02    /* Reverse at end */
#define ARDK_LOOP_REVERSE   0x03    /* Play backwards */

/* ===========================================================================
 * Metadata Section
 *
 * Optional human-readable metadata for tooling.
 * =========================================================================== */

typedef struct {
    u8      asset_id;       /* Which asset this metadata belongs to */
    u8      key_length;     /* Length of key string */
    u16     value_length;   /* Length of value string */
    /* Followed by: key string (key_length bytes, not null-terminated) */
    /* Followed by: value string (value_length bytes, not null-terminated) */
} ARDK_MetadataEntry;

/* Common metadata keys (convention, not enforced):
 *   "name"     - Human-readable asset name
 *   "source"   - Original source file path
 *   "author"   - Creator attribution
 *   "tags"     - Comma-separated tags for filtering
 *   "layer"    - Rendering layer hint
 */

/* ===========================================================================
 * Platform Export Hints
 *
 * Optional section to guide platform-specific export.
 * =========================================================================== */

typedef struct {
    u8      platform_id;    /* ARDK_PLATFORM_* */
    u8      hint_type;      /* ARDK_HINT_* */
    u16     hint_value;     /* Hint-specific value */
} ARDK_ExportHint;

/* Platform IDs */
#define ARDK_PLATFORM_NES       0x01
#define ARDK_PLATFORM_GENESIS   0x02
#define ARDK_PLATFORM_SNES      0x03
#define ARDK_PLATFORM_GBA       0x04
#define ARDK_PLATFORM_GB        0x05
#define ARDK_PLATFORM_SMS       0x06
#define ARDK_PLATFORM_PCE       0x07

/* Hint types */
#define ARDK_HINT_CHR_BANK      0x01    /* Preferred CHR bank */
#define ARDK_HINT_VRAM_ADDR     0x02    /* Preferred VRAM address */
#define ARDK_HINT_PRIORITY      0x03    /* Sprite priority */
#define ARDK_HINT_PALETTE       0x04    /* Preferred palette slot */

#endif /* ARDK_ASSET_FORMAT_H */
