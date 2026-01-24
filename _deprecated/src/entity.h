/*
 * =============================================================================
 * ARDK - Agentic Retro Development Kit
 * entity.h - Entity Data Structure
 * =============================================================================
 *
 * The Entity structure is the foundation for all game objects:
 * players, enemies, projectiles, pickups, etc.
 *
 * LOCKED DECISIONS:
 * - Structure size: 16 bytes (power of 2 for fast indexing)
 * - Position: fixed8_8 for subpixel accuracy
 * - Entity ID: 8-bit, max 256 entities
 *
 * Memory Layout:
 * Each entity is exactly 16 bytes, allowing:
 *   entity_ptr = entity_base + (entity_id << 4)
 *
 * On 6502: LDA entity_id, ASL, ASL, ASL, ASL gives offset
 * On 68000: Just shift left 4
 * =============================================================================
 */

#ifndef ARDK_ENTITY_H
#define ARDK_ENTITY_H

#include "types.h"

/* ---------------------------------------------------------------------------
 * Entity Flags (byte 0)
 * --------------------------------------------------------------------------- */

#define ENT_FLAG_ACTIVE     0x01    /* Entity is active/alive */
#define ENT_FLAG_VISIBLE    0x02    /* Should be rendered */
#define ENT_FLAG_SOLID      0x04    /* Participates in collision */
#define ENT_FLAG_FRIENDLY   0x08    /* Player team (for collision groups) */
#define ENT_FLAG_ENEMY      0x10    /* Enemy team */
#define ENT_FLAG_PICKUP     0x20    /* Can be collected */
#define ENT_FLAG_INVULN     0x40    /* Currently invulnerable */
#define ENT_FLAG_FLASH      0x80    /* Currently flashing (hit effect) */

/* ---------------------------------------------------------------------------
 * Entity Types
 *
 * High nibble = category, low nibble = subtype
 * This allows fast category checks: (type & 0xF0) == ENT_CAT_*
 * --------------------------------------------------------------------------- */

/* Categories (high nibble) */
#define ENT_CAT_NONE        0x00
#define ENT_CAT_PLAYER      0x10
#define ENT_CAT_ENEMY       0x20
#define ENT_CAT_PROJECTILE  0x30
#define ENT_CAT_PICKUP      0x40
#define ENT_CAT_EFFECT      0x50
#define ENT_CAT_TRIGGER     0x60

/* Player subtypes */
#define ENT_TYPE_PLAYER     0x10

/* Enemy subtypes */
#define ENT_TYPE_ENEMY_BASIC    0x20
#define ENT_TYPE_ENEMY_FAST     0x21
#define ENT_TYPE_ENEMY_TANK     0x22
#define ENT_TYPE_ENEMY_SHOOTER  0x23
#define ENT_TYPE_ENEMY_BOSS     0x2F

/* Projectile subtypes */
#define ENT_TYPE_PROJ_BULLET    0x30
#define ENT_TYPE_PROJ_LASER     0x31
#define ENT_TYPE_PROJ_MISSILE   0x32
#define ENT_TYPE_PROJ_SPREAD    0x33
#define ENT_TYPE_PROJ_ORBIT     0x34
#define ENT_TYPE_PROJ_ENEMY     0x3E    /* Enemy projectile */

/* Pickup subtypes */
#define ENT_TYPE_PICKUP_XP      0x40
#define ENT_TYPE_PICKUP_HEALTH  0x41
#define ENT_TYPE_PICKUP_COIN    0x42
#define ENT_TYPE_PICKUP_MAGNET  0x43
#define ENT_TYPE_PICKUP_BOMB    0x44
#define ENT_TYPE_PICKUP_WEAPON  0x45

/* Effect subtypes (visual only, no collision) */
#define ENT_TYPE_EFFECT_EXPLOSION   0x50
#define ENT_TYPE_EFFECT_SPARK       0x51
#define ENT_TYPE_EFFECT_TEXT        0x52

/* ---------------------------------------------------------------------------
 * Entity Structure (16 bytes)
 *
 * Offset  Size  Field       Description
 * ------  ----  ----------  -----------
 *  0      1     flags       ENT_FLAG_* bits
 *  1      1     type        ENT_TYPE_* value
 *  2      2     x           X position (fixed8_8)
 *  4      2     y           Y position (fixed8_8)
 *  6      2     vx          X velocity (fixed8_8)
 *  8      2     vy          Y velocity (fixed8_8)
 * 10      1     hp          Health points (0 = dead, or low byte for 16-bit)
 * 11      1     timer       General purpose timer (countdown)
 * 12      1     sprite      Sprite/animation ID
 * 13      1     frame       Animation frame
 * 14      2     data        Type-specific data (see below)
 * ------  ----  ----------  -----------
 * Total: 16 bytes
 *
 * NOTE: For entities needing 16-bit HP (player, bosses), the 'data' field
 * stores extended HP info. Use ENT_HP16_* macros for these entity types.
 * --------------------------------------------------------------------------- */

typedef struct Entity {
    u8          flags;      /* ENT_FLAG_* */
    u8          type;       /* ENT_TYPE_* */
    fixed8_8    x;          /* X position */
    fixed8_8    y;          /* Y position */
    fixed8_8    vx;         /* X velocity */
    fixed8_8    vy;         /* Y velocity */
    u8          hp;         /* Health (low byte, or full HP if <=255) */
    u8          timer;      /* General timer */
    sprite_id_t sprite;     /* Sprite asset ID */
    u8          frame;      /* Animation frame */
    u16         data;       /* Type-specific */
} Entity;

/* Verify structure size at compile time */
typedef char _entity_size_check[(sizeof(Entity) == 16) ? 1 : -1];

/* ---------------------------------------------------------------------------
 * 16-bit HP Support
 *
 * For entities that need more than 255 HP (player, bosses), we use:
 *   hp field = low byte of HP (0-255)
 *   data.hi  = high byte of HP (0-255)
 *   data.lo  = available for other use (weapon type, AI state, etc.)
 *
 * This gives 0-65535 HP range while maintaining the 16-byte struct.
 * Regular enemies (hp <= 255) just use the hp field directly.
 * --------------------------------------------------------------------------- */

/* Check if entity type uses 16-bit HP */
#define ENT_USES_HP16(e)    (((e)->type == ENT_TYPE_PLAYER) || \
                             ((e)->type == ENT_TYPE_ENEMY_BOSS))

/* Get 16-bit HP (for player/boss) */
#define ENT_HP16_GET(e)     ((u16)((e)->hp) | ((u16)(ENT_DATA_HI(e)) << 8))

/* Set 16-bit HP (for player/boss) - preserves data.lo */
#define ENT_HP16_SET(e, hp16) do { \
    (e)->hp = (u8)((hp16) & 0xFF); \
    (e)->data = ((e)->data & 0x00FF) | (((hp16) >> 8) << 8); \
} while(0)

/* Add to 16-bit HP (clamps to 0-65535) */
#define ENT_HP16_ADD(e, amt) do { \
    u16 _hp = ENT_HP16_GET(e); \
    u16 _new = _hp + (amt); \
    if (_new < _hp) _new = 0xFFFF; /* Overflow check */ \
    ENT_HP16_SET(e, _new); \
} while(0)

/* Subtract from 16-bit HP (clamps to 0) */
#define ENT_HP16_SUB(e, amt) do { \
    u16 _hp = ENT_HP16_GET(e); \
    if ((amt) >= _hp) { ENT_HP16_SET(e, 0); } \
    else { ENT_HP16_SET(e, _hp - (amt)); } \
} while(0)

/* For player specifically: data.lo stores weapon type */
#define ENT_PLAYER_WEAPON(e)        ENT_DATA_LO(e)
#define ENT_PLAYER_WEAPON_SET(e, w) ((e)->data = ((e)->data & 0xFF00) | (w))

/* ---------------------------------------------------------------------------
 * Type-Specific Data Field Usage
 *
 * The 'data' field (16 bits) is interpreted based on entity type:
 *
 * Player (uses 16-bit HP):
 *   hp      = HP low byte (0-255)
 *   data.lo = current weapon type
 *   data.hi = HP high byte (0-255) -> total HP range 0-65535
 *
 * Enemy (regular, 8-bit HP):
 *   hp      = full HP (0-255)
 *   data.lo = target entity ID (for homing)
 *   data.hi = AI state
 *
 * Enemy Boss (uses 16-bit HP):
 *   hp      = HP low byte
 *   data.lo = AI state / attack pattern
 *   data.hi = HP high byte
 *
 * Projectile:
 *   hp      = unused (or penetration count)
 *   data.lo = damage amount (8-bit, 0-255)
 *   data.hi = owner entity ID
 *
 * Pickup:
 *   hp      = unused
 *   data.lo = value (XP amount, health amount, etc.)
 *   data.hi = magnet attraction state / timer
 *
 * Effect:
 *   hp      = unused
 *   data    = lifetime counter (16-bit)
 * --------------------------------------------------------------------------- */

/* Macros to access data field */
#define ENT_DATA_LO(e)      ((u8)((e)->data & 0xFF))
#define ENT_DATA_HI(e)      ((u8)((e)->data >> 8))
#define ENT_DATA_SET(e, lo, hi) ((e)->data = ((u16)(hi) << 8) | (lo))

/* ---------------------------------------------------------------------------
 * Entity Pool
 *
 * Entities are stored in a fixed-size array for predictable memory.
 * Max entities depends on platform RAM constraints.
 * --------------------------------------------------------------------------- */

#ifndef MAX_ENTITIES
#define MAX_ENTITIES    64      /* Default, override per platform */
#endif

/* Entity ID type (index into pool) */
typedef u8 entity_id_t;

#define ENTITY_ID_NONE      0xFF    /* Invalid/no entity */
#define ENTITY_ID_PLAYER    0       /* Player is always slot 0 */

/* ---------------------------------------------------------------------------
 * Entity Iteration Helpers
 * --------------------------------------------------------------------------- */

/* Category check macros */
#define ENT_IS_PLAYER(e)        (((e)->type & 0xF0) == ENT_CAT_PLAYER)
#define ENT_IS_ENEMY(e)         (((e)->type & 0xF0) == ENT_CAT_ENEMY)
#define ENT_IS_PROJECTILE(e)    (((e)->type & 0xF0) == ENT_CAT_PROJECTILE)
#define ENT_IS_PICKUP(e)        (((e)->type & 0xF0) == ENT_CAT_PICKUP)
#define ENT_IS_EFFECT(e)        (((e)->type & 0xF0) == ENT_CAT_EFFECT)

/* Active check */
#define ENT_IS_ACTIVE(e)        (((e)->flags & ENT_FLAG_ACTIVE) != 0)

/* Collision group checks */
#define ENT_IS_FRIENDLY(e)      (((e)->flags & ENT_FLAG_FRIENDLY) != 0)
#define ENT_IS_HOSTILE(e)       (((e)->flags & ENT_FLAG_ENEMY) != 0)

/* ---------------------------------------------------------------------------
 * Entity Functions (implemented in entity.c)
 * --------------------------------------------------------------------------- */

/* Initialize entity pool (call once at game start) */
void entity_init_all(void);

/* Find a free entity slot, returns ENTITY_ID_NONE if full */
entity_id_t entity_alloc(void);

/* Free an entity slot */
void entity_free(entity_id_t id);

/* Get pointer to entity by ID */
Entity* entity_get(entity_id_t id);

/* Spawn helper - allocates and initializes basic fields */
entity_id_t entity_spawn(u8 type, fixed8_8 x, fixed8_8 y);

/* Update all active entities (calls type-specific update) */
void entity_update_all(void);

/* Render all visible entities */
void entity_render_all(void);

/* Count active entities of given type mask */
u8 entity_count(u8 type_mask);

/* Find first entity of given type, returns ENTITY_ID_NONE if not found */
entity_id_t entity_find_first(u8 type);

/* ---------------------------------------------------------------------------
 * Collision Helpers
 * --------------------------------------------------------------------------- */

/* Hitbox dimensions stored separately (entity just has position) */
typedef struct Hitbox {
    i8 offset_x;    /* Offset from entity position */
    i8 offset_y;
    u8 width;       /* Hitbox dimensions */
    u8 height;
} Hitbox;

/* Get hitbox for entity type (from ROM table) */
const Hitbox* entity_get_hitbox(u8 type);

/* Check if two entities overlap (AABB) */
bool_t entity_collide(entity_id_t a, entity_id_t b);

/* Check if point is inside entity hitbox */
bool_t entity_point_inside(entity_id_t id, fixed8_8 x, fixed8_8 y);

/* Find all entities colliding with given entity
 * Returns count, fills 'results' array with IDs */
u8 entity_find_collisions(entity_id_t id, entity_id_t* results, u8 max_results);

#endif /* ARDK_ENTITY_H */
