/*
 * =============================================================================
 * ARDK - Agentic Retro Development Kit
 * entity.c - Entity Pool Implementation
 * =============================================================================
 *
 * Manages a fixed-size pool of entities with O(1) allocation and deallocation
 * using a free list.
 *
 * Memory layout:
 *   - Entity array: MAX_ENTITIES * 16 bytes
 *   - Free list: Linked through entity pool (no extra memory)
 *
 * Allocation strategy:
 *   - Free list stored as indices in the 'data' field of inactive entities
 *   - Alloc: Pop from free list head - O(1)
 *   - Free: Push to free list head - O(1)
 *
 * Special slots:
 *   - Slot 0 is always reserved for the player
 *   - Player is never in the free list
 * =============================================================================
 */

#include "entity.h"
#include "hal.h"

/* Include platform config to get tier-defined limits */
#if defined(PLATFORM_NES)
    #include "nes/hal_config.h"
#elif defined(PLATFORM_GENESIS)
    #include "genesis/hal_config.h"
#elif defined(PLATFORM_SNES)
    #include "snes/hal_config.h"
#elif defined(PLATFORM_GBA)
    #include "gba/hal_config.h"
#else
    /* Default fallback limits for testing/compilation */
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
#endif

/* ===========================================================================
 * Entity Pool Storage
 *
 * Split pool architecture: Each entity category has its own count limit
 * from the tier system, but shares the same physical array. This prevents
 * one category (e.g., projectiles) from starving another (e.g., enemies).
 * =========================================================================== */

/* The entity pool - platform may place this in specific RAM region */
static Entity entity_pool[MAX_ENTITIES];

/* Free list head (index of first free slot, or ENTITY_ID_NONE if full) */
static entity_id_t free_list_head;

/* Count of active entities (for stats/debugging) */
static u8 active_count;

/* Per-category counts for split pool enforcement */
static u8 enemy_count;
static u8 projectile_count;
static u8 pickup_count;
static u8 effect_count;

/* ===========================================================================
 * Hitbox Table
 *
 * Defines collision bounds for each entity type.
 * Indexed by ENT_TYPE_* >> 4 (category) and ENT_TYPE_* & 0x0F (subtype).
 * =========================================================================== */

/* Default hitboxes by category (can be refined per-type) */
static const Hitbox hitbox_table[] = {
    /* ENT_CAT_NONE (0x00) */
    { 0, 0, 8, 8 },

    /* ENT_CAT_PLAYER (0x10) - 32x32 sprite, smaller hitbox */
    { 4, 4, 24, 24 },

    /* ENT_CAT_ENEMY (0x20) - varies by type, default 24x24 */
    { 4, 4, 24, 24 },

    /* ENT_CAT_PROJECTILE (0x30) - small hitbox */
    { 1, 1, 6, 6 },

    /* ENT_CAT_PICKUP (0x40) - 8x8 */
    { 0, 0, 8, 8 },

    /* ENT_CAT_EFFECT (0x50) - no collision */
    { 0, 0, 0, 0 },

    /* ENT_CAT_TRIGGER (0x60) - varies */
    { 0, 0, 16, 16 },
};

#define HITBOX_TABLE_SIZE (sizeof(hitbox_table) / sizeof(hitbox_table[0]))

/* ===========================================================================
 * Initialization
 * =========================================================================== */

void entity_init_all(void) {
    entity_id_t i;

    /* Clear all entities */
    for (i = 0; i < MAX_ENTITIES; i++) {
        entity_pool[i].flags = 0;
        entity_pool[i].type = ENT_CAT_NONE;
        entity_pool[i].x = 0;
        entity_pool[i].y = 0;
        entity_pool[i].vx = 0;
        entity_pool[i].vy = 0;
        entity_pool[i].hp = 0;
        entity_pool[i].timer = 0;
        entity_pool[i].sprite = 0;
        entity_pool[i].frame = 0;
        entity_pool[i].data = 0;
    }

    /* Build free list (skip slot 0, reserved for player) */
    /* Each free slot's 'data' field points to next free slot */
    for (i = 1; i < MAX_ENTITIES - 1; i++) {
        entity_pool[i].data = i + 1;
    }
    entity_pool[MAX_ENTITIES - 1].data = ENTITY_ID_NONE;  /* End of list */

    free_list_head = 1;  /* First free slot is 1 (0 is player) */
    active_count = 0;

    /* Reset per-category counts */
    enemy_count = 0;
    projectile_count = 0;
    pickup_count = 0;
    effect_count = 0;

    /* Initialize player slot (always exists, starts inactive) */
    entity_pool[ENTITY_ID_PLAYER].type = ENT_TYPE_PLAYER;
}

/* ===========================================================================
 * Category Pool Helpers (Split Pool Architecture)
 *
 * These enforce per-category limits from the tier system, preventing one
 * category from starving another.
 * =========================================================================== */

/*
 * Check if category limit allows spawning another entity of this type.
 * Uses tier-defined limits from HAL_MAX_ENEMIES, etc.
 */
static bool_t category_can_spawn(u8 category) {
    switch (category) {
        case ENT_CAT_ENEMY:
            return enemy_count < HAL_MAX_ENEMIES;
        case ENT_CAT_PROJECTILE:
            return projectile_count < HAL_MAX_PROJECTILES;
        case ENT_CAT_PICKUP:
            return pickup_count < HAL_MAX_PICKUPS;
        case ENT_CAT_EFFECT:
            return effect_count < HAL_MAX_EFFECTS;
        case ENT_CAT_PLAYER:
            return TRUE;  /* Player always allowed */
        default:
            return TRUE;  /* Unknown categories not limited */
    }
}

/*
 * Increment category count when entity is spawned.
 */
static void category_increment(u8 category) {
    switch (category) {
        case ENT_CAT_ENEMY:      enemy_count++;      break;
        case ENT_CAT_PROJECTILE: projectile_count++; break;
        case ENT_CAT_PICKUP:     pickup_count++;     break;
        case ENT_CAT_EFFECT:     effect_count++;     break;
    }
}

/*
 * Decrement category count when entity is freed.
 */
static void category_decrement(u8 category) {
    switch (category) {
        case ENT_CAT_ENEMY:
            if (enemy_count > 0) enemy_count--;
            break;
        case ENT_CAT_PROJECTILE:
            if (projectile_count > 0) projectile_count--;
            break;
        case ENT_CAT_PICKUP:
            if (pickup_count > 0) pickup_count--;
            break;
        case ENT_CAT_EFFECT:
            if (effect_count > 0) effect_count--;
            break;
    }
}

/* ===========================================================================
 * Allocation / Deallocation
 * =========================================================================== */

entity_id_t entity_alloc(void) {
    entity_id_t id;

    /* Check if pool is full */
    if (free_list_head == ENTITY_ID_NONE) {
        return ENTITY_ID_NONE;
    }

    /* Pop from free list */
    id = free_list_head;
    free_list_head = (entity_id_t)entity_pool[id].data;

    /* Clear the allocated entity */
    entity_pool[id].flags = 0;
    entity_pool[id].type = ENT_CAT_NONE;
    entity_pool[id].data = 0;

    active_count++;
    return id;
}

void entity_free(entity_id_t id) {
    u8 category;

    /* Don't free the player slot or invalid IDs */
    if (id == ENTITY_ID_PLAYER || id >= MAX_ENTITIES) {
        return;
    }

    /* Don't double-free */
    if (!(entity_pool[id].flags & ENT_FLAG_ACTIVE)) {
        return;
    }

    /* Decrement category count before clearing type */
    category = entity_pool[id].type & 0xF0;
    category_decrement(category);

    /* Mark as inactive */
    entity_pool[id].flags = 0;
    entity_pool[id].type = ENT_CAT_NONE;

    /* Push to free list */
    entity_pool[id].data = free_list_head;
    free_list_head = id;

    if (active_count > 0) active_count--;
}

/* ===========================================================================
 * Access Functions
 * =========================================================================== */

Entity* entity_get(entity_id_t id) {
    if (id >= MAX_ENTITIES) {
        return NULL;
    }
    return &entity_pool[id];
}

entity_id_t entity_spawn(u8 type, fixed8_8 x, fixed8_8 y) {
    entity_id_t id;
    Entity* e;
    u8 category = type & 0xF0;

    /* Check category limit before allocating */
    if (!category_can_spawn(category)) {
        return ENTITY_ID_NONE;
    }

    id = entity_alloc();
    if (id == ENTITY_ID_NONE) {
        return ENTITY_ID_NONE;
    }

    /* Increment category count */
    category_increment(category);

    e = &entity_pool[id];
    e->flags = ENT_FLAG_ACTIVE | ENT_FLAG_VISIBLE;
    e->type = type;
    e->x = x;
    e->y = y;
    e->vx = 0;
    e->vy = 0;
    e->hp = 1;  /* Default to 1 HP */
    e->timer = 0;
    e->sprite = 0;
    e->frame = 0;
    e->data = 0;

    /* Set collision flags based on type category */
    switch (category) {
        case ENT_CAT_PLAYER:
            e->flags |= ENT_FLAG_SOLID | ENT_FLAG_FRIENDLY;
            break;
        case ENT_CAT_ENEMY:
            e->flags |= ENT_FLAG_SOLID | ENT_FLAG_ENEMY;
            break;
        case ENT_CAT_PROJECTILE:
            e->flags |= ENT_FLAG_SOLID;
            /* Projectile team set by spawner */
            break;
        case ENT_CAT_PICKUP:
            e->flags |= ENT_FLAG_PICKUP;
            break;
        case ENT_CAT_EFFECT:
            /* Effects are just visual, no collision */
            e->flags &= ~ENT_FLAG_SOLID;
            break;
    }

    return id;
}

/* ===========================================================================
 * Iteration and Queries
 * =========================================================================== */

u8 entity_count(u8 type_mask) {
    u8 count = 0;
    entity_id_t i;

    for (i = 0; i < MAX_ENTITIES; i++) {
        if (entity_pool[i].flags & ENT_FLAG_ACTIVE) {
            if (type_mask == 0 || (entity_pool[i].type & 0xF0) == type_mask) {
                count++;
            }
        }
    }
    return count;
}

entity_id_t entity_find_first(u8 type) {
    entity_id_t i;

    for (i = 0; i < MAX_ENTITIES; i++) {
        if ((entity_pool[i].flags & ENT_FLAG_ACTIVE) &&
            entity_pool[i].type == type) {
            return i;
        }
    }
    return ENTITY_ID_NONE;
}

/* ===========================================================================
 * Collision Functions
 * =========================================================================== */

const Hitbox* entity_get_hitbox(u8 type) {
    u8 category = (type >> 4) & 0x0F;

    if (category < HITBOX_TABLE_SIZE) {
        return &hitbox_table[category];
    }
    return &hitbox_table[0];  /* Default */
}

bool_t entity_collide(entity_id_t a, entity_id_t b) {
    Entity* ea;
    Entity* eb;
    const Hitbox* ha;
    const Hitbox* hb;
    i16 ax, ay, bx, by;

    if (a >= MAX_ENTITIES || b >= MAX_ENTITIES) {
        return FALSE;
    }

    ea = &entity_pool[a];
    eb = &entity_pool[b];

    /* Both must be active and solid */
    if (!(ea->flags & ENT_FLAG_ACTIVE) || !(ea->flags & ENT_FLAG_SOLID)) {
        return FALSE;
    }
    if (!(eb->flags & ENT_FLAG_ACTIVE) || !(eb->flags & ENT_FLAG_SOLID)) {
        return FALSE;
    }

    /* Get hitboxes */
    ha = entity_get_hitbox(ea->type);
    hb = entity_get_hitbox(eb->type);

    /* Calculate hitbox positions (entity pos + hitbox offset) */
    ax = FP_TO_INT(ea->x) + ha->offset_x;
    ay = FP_TO_INT(ea->y) + ha->offset_y;
    bx = FP_TO_INT(eb->x) + hb->offset_x;
    by = FP_TO_INT(eb->y) + hb->offset_y;

    /* Check overlap */
    return hal_rect_overlap(ax, ay, ha->width, ha->height,
                            bx, by, hb->width, hb->height);
}

bool_t entity_point_inside(entity_id_t id, fixed8_8 x, fixed8_8 y) {
    Entity* e;
    const Hitbox* h;
    i16 ex, ey, px, py;

    if (id >= MAX_ENTITIES) {
        return FALSE;
    }

    e = &entity_pool[id];
    if (!(e->flags & ENT_FLAG_ACTIVE)) {
        return FALSE;
    }

    h = entity_get_hitbox(e->type);

    ex = FP_TO_INT(e->x) + h->offset_x;
    ey = FP_TO_INT(e->y) + h->offset_y;
    px = FP_TO_INT(x);
    py = FP_TO_INT(y);

    return hal_point_in_rect(px, py, ex, ey, h->width, h->height);
}

u8 entity_find_collisions(entity_id_t id, entity_id_t* results, u8 max_results) {
    u8 count = 0;
    entity_id_t i;

    if (id >= MAX_ENTITIES || results == NULL || max_results == 0) {
        return 0;
    }

    for (i = 0; i < MAX_ENTITIES && count < max_results; i++) {
        if (i != id && entity_collide(id, i)) {
            results[count++] = i;
        }
    }

    return count;
}

/* ===========================================================================
 * Update and Render (called by game loop)
 *
 * These are stubs - actual behavior is defined by game code that registers
 * type-specific update/render callbacks, or by game loop calling per-type
 * update functions.
 * =========================================================================== */

/*
 * Generic update: Move entities by velocity, decrement timers.
 * Game code should call type-specific update functions after this.
 */
void entity_update_all(void) {
    entity_id_t i;

    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* e = &entity_pool[i];

        if (!(e->flags & ENT_FLAG_ACTIVE)) {
            continue;
        }

        /* Apply velocity */
        e->x = FP_ADD(e->x, e->vx);
        e->y = FP_ADD(e->y, e->vy);

        /* Decrement timer */
        if (e->timer > 0) {
            e->timer--;
        }

        /* Handle invincibility flash */
        if (e->flags & ENT_FLAG_INVULN) {
            /* Toggle flash flag each frame for visual effect */
            e->flags ^= ENT_FLAG_FLASH;
        }
    }
}

/*
 * Generic render: Draw all visible entities using HAL sprite functions.
 * Game code may override this with custom rendering.
 */
void entity_render_all(void) {
    entity_id_t i;
    u8 sprite_slot = 0;

    for (i = 0; i < MAX_ENTITIES && sprite_slot < 64; i++) {
        Entity* e = &entity_pool[i];

        if (!(e->flags & ENT_FLAG_ACTIVE)) {
            continue;
        }
        if (!(e->flags & ENT_FLAG_VISIBLE)) {
            continue;
        }
        /* Skip if flashing and on "off" frame */
        if ((e->flags & ENT_FLAG_FLASH) && (hal_frame_count() & 0x02)) {
            continue;
        }

        /* Simple single-sprite render (game code handles metasprites) */
        hal_sprite_set(sprite_slot, e->x, e->y, e->sprite, 0);
        sprite_slot++;
    }

    /* Hide remaining sprites */
    while (sprite_slot < 64) {
        hal_sprite_hide(sprite_slot);
        sprite_slot++;
    }
}
