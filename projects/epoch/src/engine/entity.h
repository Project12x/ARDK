/**
 * EPOCH - Entity System
 * Sega Genesis / Mega Drive
 *
 * 16-byte aligned entities for fast array indexing
 */

#ifndef _ENGINE_ENTITY_H_
#define _ENGINE_ENTITY_H_

#include "engine/animation.h"
#include "engine/config.h"
#include <genesis.h>

// =============================================================================
// ENTITY FLAGS
// =============================================================================
#define ENT_ACTIVE 0x01   // Entity is in use
#define ENT_VISIBLE 0x02  // Entity should be rendered
#define ENT_SOLID 0x04    // Entity has collision
#define ENT_FRIENDLY 0x08 // Friendly to player
#define ENT_ENEMY 0x10    // Hostile to player
#define ENT_PICKUP 0x20   // Can be picked up
#define ENT_INVULN 0x40   // Currently invulnerable
#define ENT_FIRING 0x80   // Currently firing weapon

// =============================================================================
// COLLISION MASKS (Three-Gate Filter - Gate 1)
// =============================================================================
#define COLL_NONE 0x00     // No collision
#define COLL_PLAYER 0x01   // Player entity
#define COLL_ENEMY 0x02    // Enemy entities
#define COLL_PROJ_PLR 0x04 // Player projectiles (hits enemies)
#define COLL_PROJ_ENY 0x08 // Enemy projectiles (hits player)
#define COLL_PICKUP 0x10   // Pickups (collected by player)
#define COLL_TOWER 0x20    // Towers
#define COLL_FENRIR 0x40   // Fenrir companion

// =============================================================================
// ENTITY TYPES
// =============================================================================
// High nibble = category, low nibble = variant
#define ENT_TYPE_NONE 0x00

// Player & companion (0x1X)
#define ENT_TYPE_PLAYER 0x10
#define ENT_TYPE_FENRIR 0x11

// Enemies (0x2X)
#define ENT_TYPE_ENEMY_BASIC 0x20
#define ENT_TYPE_ENEMY_FAST 0x21
#define ENT_TYPE_ENEMY_TANK 0x22
#define ENT_TYPE_ENEMY_RANGED 0x23

// Projectiles (0x3X)
#define ENT_TYPE_PROJ_PLAYER 0x30
#define ENT_TYPE_PROJ_ENEMY 0x31
#define ENT_TYPE_PROJ_TOWER 0x32

// Towers (0x4X)
#define ENT_TYPE_TOWER_BASIC 0x40
#define ENT_TYPE_TOWER_FLAME 0x41
#define ENT_TYPE_TOWER_SLOW 0x42
#define ENT_TYPE_TOWER_CENTER 0x43

// NPCs (0x5X)
#define ENT_TYPE_NPC 0x50
#define ENT_TYPE_NPC_MERCHANT 0x51
#define ENT_TYPE_NPC_SMITH 0x52

// Pickups (0x6X)
#define ENT_TYPE_PICKUP_XP 0x60
#define ENT_TYPE_PICKUP_HEALTH 0x61
#define ENT_TYPE_PICKUP_WEAPON 0x62
#define ENT_TYPE_PICKUP_BOMB 0x63

// =============================================================================
// ENTITY STRUCTURE (24 bytes)
// =============================================================================
typedef struct {
  u8 flags;    // Offset 0:  Entity state flags (1)
  u8 type;     // Offset 1:  Entity type (1)
  u8 timer;    // Offset 2:  Animation/state timer (1)
  u8 frame;    // Offset 3:  Current animation frame (1)
  s32 x;       // Offset 4:  X position (8.8 fixed point) - Aligned 4
  s32 y;       // Offset 8:  Y position (8.8 fixed point) - Aligned 4
  s16 vx;      // Offset 12: X velocity (8.8 fixed point) - Aligned 2
  s16 vy;      // Offset 14: Y velocity (8.8 fixed point) - Aligned 2
  s16 hp;      // Offset 16: Health points (2) - Aligned 2
  u16 data;    // Offset 18: Type-specific data (2) - Aligned 2
  u8 width;    // Offset 20: Hitbox Width
  u8 height;   // Offset 21: Hitbox Height
  u8 spriteId; // Offset 22: Sprite definition index
  u8 collMask; // Offset 23: Collision bitmask (Three-Gate filter)
} Entity;      // Total: 24 bytes

// Compile-time size check (portable - works with all C compilers)
typedef char entity_size_check[(sizeof(Entity) == 24) ? 1 : -1];

// =============================================================================
// PLAYER DATA (Extended - separate from Entity)
// =============================================================================
typedef struct {
  u8 weaponType;     // Current static weapon (WeaponType)
  u8 weaponLevel;    // Weapon upgrade level (0-3)
  u8 volatileWeapon; // Current alt-fire weapon
  u8 facing;         // Direction (0-7)

  u16 maxHP;     // Max health
  u16 currentHP; // Current health

  u8 invulnTimer;  // Iframes remaining
  u8 dashTimer;    // Dash duration remaining
  u8 strafeLocked; // A button held - facing locked
  u8 dashCooldown; // Frames until dash available again

  u8 keysCollected; // For expedition puzzles
  u8 techUnlocked;  // Bitfield of abilities
  u8 towersPlaced;  // Number of towers currently placed

  u16 fireRate;     // Frames between shots
  u16 fireCooldown; // Frames until next shot

  AnimState animState; // Current animation state
} PlayerData;

// =============================================================================
// FENRIR DATA (Extended - companion)
// =============================================================================
typedef struct {
  u8 mode;       // 0=follow, 1=guard, 2=attack
  u8 targetSlot; // Entity slot of current target
  u8 followDist; // Distance to maintain from player
  u8 ability;    // Currently equipped ability
} FenrirData;

// =============================================================================
// OPTIMIZATION MACROS (Xeno Crisis Style)
// =============================================================================

// Unroll entity loop by 4 for performance.
// Eliminates 75% of loop overhead instructions (cmp/bne).
// USAGE:
//   ENTITY_FAST_ITERATE(i, start, end, {
//      Entity *e = &entities[i];
//      if(e->flags & ENT_ACTIVE) {
//          // do work
//      }
//   })
#define ENTITY_FAST_ITERATE(idx, start, end, block)                            \
  {                                                                            \
    u16 _limit = (end);                                                        \
    u16 idx;                                                                   \
    for (idx = (start); idx <= _limit - 3; idx += 4) {                         \
      {                                                                        \
        block                                                                  \
      }                                                                        \
      {                                                                        \
        u16 _saved_i = idx;                                                    \
        idx = idx + 1;                                                         \
        {block} idx = _saved_i;                                                \
      }                                                                        \
      {                                                                        \
        u16 _saved_i = idx;                                                    \
        idx = idx + 2;                                                         \
        {block} idx = _saved_i;                                                \
      }                                                                        \
      {                                                                        \
        u16 _saved_i = idx;                                                    \
        idx = idx + 3;                                                         \
        {block} idx = _saved_i;                                                \
      }                                                                        \
    }                                                                          \
    /* Handle remainders */                                                    \
    for (; idx <= _limit; idx++) {                                             \
      {                                                                        \
        block                                                                  \
      }                                                                        \
    }                                                                          \
  }
extern Entity entities[MAX_ENTITIES];
extern u8 entityCount;

extern PlayerData playerData;
extern FenrirData fenrirData;

// =============================================================================
// FUNCTION PROTOTYPES
// =============================================================================

// Entity pool management
void entity_initPool(void);
s8 entity_alloc(u8 type);
void entity_free(u8 slot);
void entity_freeAll(void);

// Entity updates
void entity_updateAll(void);

// Entity queries
Entity *entity_getPlayer(void);
Entity *entity_getFenrir(void);
u8 entity_findNearest(s16 x, s16 y, u8 typeMask);

// Collision
bool entity_checkCollision(Entity *a, Entity *b);
bool entity_checkTileCollision(Entity *e, s16 newX, s16 newY);

#endif // _ENGINE_ENTITY_H_
