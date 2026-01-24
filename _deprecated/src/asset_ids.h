/*
 * =============================================================================
 * ARDK - Agentic Retro Development Kit
 * asset_ids.h - Central Asset ID Registry
 * =============================================================================
 *
 * SINGLE SOURCE OF TRUTH for all asset IDs in the game.
 *
 * RULES:
 * 1. ALL sprite, sound, and music IDs must be defined HERE
 * 2. NEVER define asset IDs in other files
 * 3. NEVER reuse an ID for different assets
 * 4. When adding new assets, add them to the appropriate section below
 *
 * ID Ranges (defined in types.h):
 *   0x00-0x0F: System reserved (don't use)
 *   0x10-0x7F: Game assets (sprites, sfx, music)
 *   0x80-0xFF: Dynamic/runtime (procedural, loaded)
 *
 * =============================================================================
 */

#ifndef ARDK_ASSET_IDS_H
#define ARDK_ASSET_IDS_H

/* ===========================================================================
 * SPRITE IDs (0x10-0x4F)
 *
 * These map to tile indices in CHR ROM or metasprite definitions.
 * Organized by entity category for easy lookup.
 * =========================================================================== */

/* --- Player Sprites (0x10-0x1F) --- */
#define SPR_PLAYER_IDLE         0x10
#define SPR_PLAYER_WALK1        0x11
#define SPR_PLAYER_WALK2        0x12
#define SPR_PLAYER_HURT         0x13
#define SPR_PLAYER_DEATH        0x14
/* 0x15-0x1F reserved for player animations */

/* --- Enemy Sprites (0x20-0x3F) --- */
#define SPR_ENEMY_BASIC         0x20
#define SPR_ENEMY_BASIC_WALK    0x21
#define SPR_ENEMY_FAST          0x22
#define SPR_ENEMY_FAST_WALK     0x23
#define SPR_ENEMY_TANK          0x24
#define SPR_ENEMY_TANK_WALK     0x25
#define SPR_ENEMY_SHOOTER       0x26
#define SPR_ENEMY_SHOOTER_FIRE  0x27
#define SPR_ENEMY_BOSS          0x28
#define SPR_ENEMY_BOSS_PHASE2   0x29
/* 0x2A-0x3F reserved for more enemies */

/* --- Projectile Sprites (0x40-0x4F) --- */
#define SPR_PROJ_BULLET         0x40
#define SPR_PROJ_LASER          0x41
#define SPR_PROJ_MISSILE        0x42
#define SPR_PROJ_SPREAD         0x43
#define SPR_PROJ_ORBIT          0x44
#define SPR_PROJ_ENEMY          0x45    /* Enemy projectile */
#define SPR_PROJ_BOSS           0x46    /* Boss projectile */
/* 0x47-0x4F reserved for projectiles */

/* --- Pickup Sprites (0x50-0x5F) --- */
#define SPR_PICKUP_XP_SMALL     0x50
#define SPR_PICKUP_XP_MEDIUM    0x51
#define SPR_PICKUP_XP_LARGE     0x52
#define SPR_PICKUP_HEALTH       0x53
#define SPR_PICKUP_COIN         0x54
#define SPR_PICKUP_MAGNET       0x55
#define SPR_PICKUP_BOMB         0x56
#define SPR_PICKUP_WEAPON       0x57
/* 0x58-0x5F reserved for pickups */

/* --- Effect Sprites (0x60-0x6F) --- */
#define SPR_EFFECT_EXPLOSION1   0x60
#define SPR_EFFECT_EXPLOSION2   0x61
#define SPR_EFFECT_EXPLOSION3   0x62
#define SPR_EFFECT_SPARK        0x63
#define SPR_EFFECT_HIT          0x64
#define SPR_EFFECT_LEVELUP      0x65
#define SPR_EFFECT_HEAL         0x66
/* 0x67-0x6F reserved for effects */

/* --- UI Sprites (0x70-0x7F) --- */
#define SPR_UI_CURSOR           0x70
#define SPR_UI_HEART_FULL       0x71
#define SPR_UI_HEART_EMPTY      0x72
#define SPR_UI_WEAPON_ICON      0x73
/* 0x74-0x7F reserved for UI */


/* ===========================================================================
 * SOUND EFFECT IDs (0x10-0x4F)
 *
 * Separate namespace from sprites - these index into the SFX bank.
 * =========================================================================== */

/* --- Player SFX (0x10-0x1F) --- */
#define SFX_PLAYER_SHOOT        0x10
#define SFX_PLAYER_HIT          0x11
#define SFX_PLAYER_DEATH        0x12
#define SFX_PLAYER_LEVELUP      0x13
#define SFX_PLAYER_HEAL         0x14
/* 0x15-0x1F reserved */

/* --- Enemy SFX (0x20-0x2F) --- */
#define SFX_ENEMY_HIT           0x20
#define SFX_ENEMY_DEATH         0x21
#define SFX_ENEMY_SPAWN         0x22
#define SFX_BOSS_ROAR           0x23
#define SFX_BOSS_DEATH          0x24
/* 0x25-0x2F reserved */

/* --- Weapon SFX (0x30-0x3F) --- */
#define SFX_WEAPON_LASER        0x30
#define SFX_WEAPON_MISSILE      0x31
#define SFX_WEAPON_SPREAD       0x32
#define SFX_WEAPON_ORBIT        0x33
#define SFX_WEAPON_UPGRADE      0x34
/* 0x35-0x3F reserved */

/* --- Pickup/UI SFX (0x40-0x4F) --- */
#define SFX_PICKUP_XP           0x40
#define SFX_PICKUP_HEALTH       0x41
#define SFX_PICKUP_COIN         0x42
#define SFX_PICKUP_POWERUP      0x43
#define SFX_UI_SELECT           0x44
#define SFX_UI_CONFIRM          0x45
#define SFX_UI_CANCEL           0x46
#define SFX_UI_PAUSE            0x47
/* 0x48-0x4F reserved */


/* ===========================================================================
 * MUSIC IDs (0x10-0x2F)
 *
 * Music tracks - fewer needed than SFX.
 * =========================================================================== */

#define MUS_TITLE               0x10
#define MUS_GAMEPLAY            0x11
#define MUS_GAMEPLAY_INTENSE    0x12    /* When many enemies on screen */
#define MUS_BOSS                0x13
#define MUS_VICTORY             0x14
#define MUS_GAMEOVER            0x15
#define MUS_LEVELUP             0x16    /* Short jingle */
/* 0x17-0x2F reserved */


/* ===========================================================================
 * PALETTE IDs (0x00-0x0F)
 *
 * Standard palette slots. Platform-specific but consistent naming.
 * =========================================================================== */

/* Sprite palettes (typically 0-3) */
#define PAL_SPR_PLAYER          0x00
#define PAL_SPR_ENEMY           0x01
#define PAL_SPR_PROJECTILE      0x02
#define PAL_SPR_PICKUP          0x03

/* Background palettes (typically 4-7) */
#define PAL_BG_MAIN             0x04
#define PAL_BG_UI               0x05
#define PAL_BG_ACCENT           0x06
#define PAL_BG_DARK             0x07


/* ===========================================================================
 * METASPRITE IDs
 *
 * These reference metasprite data arrays (defined in metasprites.c/inc).
 * Used with hal_metasprite_set().
 * =========================================================================== */

#define META_PLAYER_32X32       0x00
#define META_ENEMY_BASIC_32X32  0x01
#define META_ENEMY_FAST_16X16   0x02
#define META_ENEMY_TANK_32X32   0x03
#define META_BOSS_64X64         0x04
/* Add more as needed */


/* ===========================================================================
 * ID Validation (for debug builds)
 * =========================================================================== */

#ifdef DEBUG
    #define ASSERT_VALID_SPRITE_ID(id)  \
        ((void)((id) >= 0x10 && (id) <= 0x7F ? 0 : _invalid_sprite_id()))
    #define ASSERT_VALID_SFX_ID(id)     \
        ((void)((id) >= 0x10 && (id) <= 0x4F ? 0 : _invalid_sfx_id()))
    #define ASSERT_VALID_MUSIC_ID(id)   \
        ((void)((id) >= 0x10 && (id) <= 0x2F ? 0 : _invalid_music_id()))
#else
    #define ASSERT_VALID_SPRITE_ID(id)  ((void)0)
    #define ASSERT_VALID_SFX_ID(id)     ((void)0)
    #define ASSERT_VALID_MUSIC_ID(id)   ((void)0)
#endif


/* ===========================================================================
 * Next Available IDs (update when adding new assets)
 *
 * This section helps track what IDs are free.
 * =========================================================================== */

/*
 * SPRITES:
 *   Player:     0x15-0x1F free
 *   Enemy:      0x2A-0x3F free
 *   Projectile: 0x47-0x4F free
 *   Pickup:     0x58-0x5F free
 *   Effect:     0x67-0x6F free
 *   UI:         0x74-0x7F free
 *
 * SFX:
 *   Player:     0x15-0x1F free
 *   Enemy:      0x25-0x2F free
 *   Weapon:     0x35-0x3F free
 *   Pickup/UI:  0x48-0x4F free
 *
 * MUSIC:       0x17-0x2F free
 */

#endif /* ARDK_ASSET_IDS_H */
