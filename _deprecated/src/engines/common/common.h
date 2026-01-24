/**
 * =============================================================================
 * ARDK Common Engine Layer
 * =============================================================================
 * Platform-agnostic code that compiles for all targets.
 * Uses HAL for all hardware access.
 *
 * This layer provides:
 *   - Entity management (16-byte struct ECS)
 *   - State machine
 *   - Collision detection
 *   - Shared game logic utilities
 * =============================================================================
 */

#ifndef ARDK_COMMON_H
#define ARDK_COMMON_H

#include "../../hal/types.h"
#include "../../hal/hal.h"

/* =============================================================================
 * Entity System
 * =========================================================================== */

/**
 * Entity structure - 16 bytes, fixed layout across all platforms.
 *
 * This exact layout is mirrored in assembly for hot path optimization.
 * DO NOT change field order or sizes!
 *
 * Layout MUST match hal/entity.h and engines/6502/nes/core/entity.asm:
 * Offset  Size  Field       Description
 * ------  ----  ----------  -------------------------------------------
 *  0      1     flags       ENT_FLAG_* bits
 *  1      1     type        ENT_TYPE_* value
 *  2      2     x           X position (8.8 fixed point, lo/hi)
 *  4      2     y           Y position (8.8 fixed point, lo/hi)
 *  6      2     vx          X velocity (8.8 fixed point, lo/hi)
 *  8      2     vy          Y velocity (8.8 fixed point, lo/hi)
 * 10      1     health      Health points
 * 11      1     timer       General purpose timer
 * 12      1     sprite_id   Sprite/animation ID
 * 13      1     frame       Animation frame
 * 14      2     data        Type-specific data (lo/hi)
 * ------  ----  ----------  -------------------------------------------
 * Total: 16 bytes
 */
typedef struct {
    u8       flags;         /*  0:   Status flags (ENT_FLAG_*) */
    u8       type;          /*  1:   Entity type (ENT_TYPE_*) */
    fixed8_8 x;             /*  2-3: X position (8.8 fixed point) */
    fixed8_8 y;             /*  4-5: Y position */
    fixed8_8 vx;            /*  6-7: X velocity (8.8 fixed point) */
    fixed8_8 vy;            /*  8-9: Y velocity (8.8 fixed point) */
    u8       health;        /* 10:   Current health */
    u8       timer;         /* 11:   General purpose timer */
    u8       sprite_id;     /* 12:   Base sprite/tile ID */
    u8       frame;         /* 13:   Animation frame */
    u16      data;          /* 14-15: Type-specific data */
} entity_t;

/* Compile-time size check */
_Static_assert(sizeof(entity_t) == 16, "entity_t must be 16 bytes");

/* Entity type categories (high nibble) */
#define ENT_CAT_NONE        0x00
#define ENT_CAT_PLAYER      0x10
#define ENT_CAT_ENEMY       0x20
#define ENT_CAT_PROJECTILE  0x30
#define ENT_CAT_PICKUP      0x40
#define ENT_CAT_EFFECT      0x50

/* Entity flags */
#define ENT_FLAG_ACTIVE     0x01    /* Entity is active */
#define ENT_FLAG_VISIBLE    0x02    /* Entity should render */
#define ENT_FLAG_COLLIDE    0x04    /* Entity participates in collision */
#define ENT_FLAG_DAMAGE     0x08    /* Entity can deal damage */
#define ENT_FLAG_INVULN     0x10    /* Entity is invulnerable */
#define ENT_FLAG_FLIP_H     0x20    /* Flip sprite horizontally */
#define ENT_FLAG_FLIP_V     0x40    /* Flip sprite vertically */
#define ENT_FLAG_MARKED     0x80    /* Marked for deletion */

/* Entity manager state */
typedef struct {
    entity_t* entities;     /* Entity array (platform allocates) */
    u16       capacity;     /* Maximum entities (from profile) */
    u16       count;        /* Current active count */
    u16       first_free;   /* First free slot (or capacity if full) */
} entity_manager_t;

/* Entity manager API */
void     entity_manager_init(entity_manager_t* em, entity_t* buffer, u16 capacity);
void     entity_manager_clear(entity_manager_t* em);
entity_t* entity_spawn(entity_manager_t* em, u8 type, fixed8_8 x, fixed8_8 y);
void     entity_despawn(entity_manager_t* em, entity_t* ent);
void     entity_update_all(entity_manager_t* em);
u16      entity_count_active(entity_manager_t* em);

/* Entity iteration macros */
#define FOREACH_ENTITY(em, ent) \
    for (entity_t* ent = (em)->entities; \
         ent < (em)->entities + (em)->capacity; \
         ent++) \
        if (ent->flags & ENT_FLAG_ACTIVE)

#define FOREACH_ENTITY_TYPE(em, ent, type_mask) \
    for (entity_t* ent = (em)->entities; \
         ent < (em)->entities + (em)->capacity; \
         ent++) \
        if ((ent->flags & ENT_FLAG_ACTIVE) && ((ent->type & 0xF0) == (type_mask)))

/* =============================================================================
 * State Machine
 * =========================================================================== */

/* Game states */
typedef enum {
    STATE_BOOT = 0,
    STATE_TITLE,
    STATE_PLAYING,
    STATE_PAUSED,
    STATE_LEVELUP,
    STATE_GAMEOVER,
    STATE_VICTORY,
    STATE_COUNT
} game_state_t;

/* State callbacks */
typedef void (*state_enter_fn)(void);
typedef void (*state_update_fn)(void);
typedef void (*state_exit_fn)(void);

typedef struct {
    state_enter_fn  enter;
    state_update_fn update;
    state_exit_fn   exit;
} state_handlers_t;

/* State machine */
typedef struct {
    game_state_t    current;
    game_state_t    next;
    u8              transition_pending;
    state_handlers_t handlers[STATE_COUNT];
} state_machine_t;

void state_machine_init(state_machine_t* sm);
void state_machine_register(state_machine_t* sm, game_state_t state,
                           state_enter_fn enter, state_update_fn update,
                           state_exit_fn exit);
void state_machine_change(state_machine_t* sm, game_state_t new_state);
void state_machine_update(state_machine_t* sm);

/* =============================================================================
 * Collision Detection
 * =========================================================================== */

/* Collision result */
typedef struct {
    entity_t* a;
    entity_t* b;
    i16       overlap_x;
    i16       overlap_y;
} collision_result_t;

/* Collision pair callback */
typedef void (*collision_callback_fn)(entity_t* a, entity_t* b);

/* AABB collision check (uses HAL math) */
bool_t collision_aabb(fixed8_8 ax, fixed8_8 ay, u8 aw, u8 ah,
                      fixed8_8 bx, fixed8_8 by, u8 bw, u8 bh);

/* Check collision between two entities */
bool_t collision_entity_pair(entity_t* a, entity_t* b,
                             u8 a_width, u8 a_height,
                             u8 b_width, u8 b_height);

/* Check all entities of one type against another type */
void collision_check_types(entity_manager_t* em,
                          u8 type_a, u8 type_b,
                          u8 width_a, u8 height_a,
                          u8 width_b, u8 height_b,
                          collision_callback_fn callback);

/* =============================================================================
 * Utility Functions
 * =========================================================================== */

/* Direction from one entity to another (returns angle_t) */
angle_t direction_to(entity_t* from, entity_t* to);

/* Distance squared between entities (for range checks) */
u16 distance_sq(entity_t* a, entity_t* b);

/* Move entity toward target (basic chase AI) */
void move_toward(entity_t* ent, fixed8_8 target_x, fixed8_8 target_y, i8 speed);

/* Apply velocity to position */
void apply_velocity(entity_t* ent);

/* Screen bounds checking */
bool_t entity_on_screen(entity_t* ent);
void   entity_wrap_screen(entity_t* ent);
void   entity_clamp_screen(entity_t* ent);

#endif /* ARDK_COMMON_H */
