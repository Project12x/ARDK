/**
 * =============================================================================
 * ARDK Entity Manager
 * =============================================================================
 * Platform-agnostic entity management using 16-byte fixed structure.
 * Compiles for NES (cc65), Genesis (SGDK), GBA (devkitARM), etc.
 * =============================================================================
 */

#include "common.h"

/* =============================================================================
 * Entity Manager Core
 * =========================================================================== */

void entity_manager_init(entity_manager_t* em, entity_t* buffer, u16 capacity)
{
    em->entities = buffer;
    em->capacity = capacity;
    em->count = 0;
    em->first_free = 0;

    /* Clear all entities */
    entity_manager_clear(em);
}

void entity_manager_clear(entity_manager_t* em)
{
    u16 i;
    for (i = 0; i < em->capacity; i++) {
        em->entities[i].flags = 0;
        em->entities[i].type = ENT_CAT_NONE;
    }
    em->count = 0;
    em->first_free = 0;
}

entity_t* entity_spawn(entity_manager_t* em, u8 type, fixed8_8 x, fixed8_8 y)
{
    u16 i;
    entity_t* ent;

    /* Find free slot starting from first_free hint */
    for (i = em->first_free; i < em->capacity; i++) {
        ent = &em->entities[i];
        if (!(ent->flags & ENT_FLAG_ACTIVE)) {
            /* Found free slot - initialize entity */
            ent->flags = ENT_FLAG_ACTIVE | ENT_FLAG_VISIBLE;
            ent->type = type;
            ent->x = x;
            ent->y = y;
            ent->vx = 0;
            ent->vy = 0;
            ent->health = 1;
            ent->timer = 0;
            ent->sprite_id = 0;
            ent->frame = 0;
            ent->data = 0;

            em->count++;

            /* Update first_free hint */
            em->first_free = i + 1;

            return ent;
        }
    }

    /* No free slot found */
    return NULL;
}

void entity_despawn(entity_manager_t* em, entity_t* ent)
{
    u16 index;

    if (ent == NULL) return;
    if (!(ent->flags & ENT_FLAG_ACTIVE)) return;

    /* Mark as inactive */
    ent->flags = 0;
    ent->type = ENT_CAT_NONE;

    em->count--;

    /* Update first_free hint if this slot is earlier */
    index = (u16)(ent - em->entities);
    if (index < em->first_free) {
        em->first_free = index;
    }
}

void entity_update_all(entity_manager_t* em)
{
    u16 i;
    entity_t* ent;

    for (i = 0; i < em->capacity; i++) {
        ent = &em->entities[i];

        /* Skip inactive entities */
        if (!(ent->flags & ENT_FLAG_ACTIVE)) continue;

        /* Check for marked-for-deletion */
        if (ent->flags & ENT_FLAG_MARKED) {
            entity_despawn(em, ent);
            continue;
        }

        /* Apply velocity */
        apply_velocity(ent);

        /* Decrement timer if active */
        if (ent->timer > 0) {
            ent->timer--;
        }
    }
}

u16 entity_count_active(entity_manager_t* em)
{
    return em->count;
}

/* =============================================================================
 * Entity Utilities
 * =========================================================================== */

void apply_velocity(entity_t* ent)
{
    /* Add velocity to position (both are 8.8 fixed point) */
    ent->x = FP_ADD(ent->x, ent->vx);
    ent->y = FP_ADD(ent->y, ent->vy);
}

angle_t direction_to(entity_t* from, entity_t* to)
{
    fixed8_8 dx = FP_SUB(to->x, from->x);
    fixed8_8 dy = FP_SUB(to->y, from->y);
    return hal_atan2(dy, dx);
}

u16 distance_sq(entity_t* a, entity_t* b)
{
    fixed8_8 dx = FP_SUB(b->x, a->x);
    fixed8_8 dy = FP_SUB(b->y, a->y);
    return hal_distance_sq(dx, dy);
}

void move_toward(entity_t* ent, fixed8_8 target_x, fixed8_8 target_y, i8 speed)
{
    fixed8_8 dx = FP_SUB(target_x, ent->x);
    fixed8_8 dy = FP_SUB(target_y, ent->y);

    /* Normalize and apply speed */
    /* For simplicity, just use sign of delta for basic chase */
    if (dx > FP_QUARTER) {
        ent->vx = speed;
    } else if (dx < -FP_QUARTER) {
        ent->vx = -speed;
    } else {
        ent->vx = 0;
    }

    if (dy > FP_QUARTER) {
        ent->vy = speed;
    } else if (dy < -FP_QUARTER) {
        ent->vy = -speed;
    } else {
        ent->vy = 0;
    }
}

bool_t entity_on_screen(entity_t* ent)
{
    i16 x = FP_TO_INT(ent->x);
    i16 y = FP_TO_INT(ent->y);
    return hal_on_screen(ent->x, ent->y);
}

void entity_wrap_screen(entity_t* ent)
{
    i16 x = FP_TO_INT(ent->x);
    i16 y = FP_TO_INT(ent->y);
    u16 w = hal_screen_width();
    u16 h = hal_screen_height();

    if (x < 0) {
        ent->x = FP_FROM_INT(w - 1);
    } else if (x >= (i16)w) {
        ent->x = FP_FROM_INT(0);
    }

    if (y < 0) {
        ent->y = FP_FROM_INT(h - 1);
    } else if (y >= (i16)h) {
        ent->y = FP_FROM_INT(0);
    }
}

void entity_clamp_screen(entity_t* ent)
{
    i16 x = FP_TO_INT(ent->x);
    i16 y = FP_TO_INT(ent->y);
    u16 w = hal_screen_width();
    u16 h = hal_screen_height();

    if (x < 0) {
        ent->x = FP_FROM_INT(0);
        ent->vx = 0;
    } else if (x >= (i16)w) {
        ent->x = FP_FROM_INT(w - 1);
        ent->vx = 0;
    }

    if (y < 0) {
        ent->y = FP_FROM_INT(0);
        ent->vy = 0;
    } else if (y >= (i16)h) {
        ent->y = FP_FROM_INT(h - 1);
        ent->vy = 0;
    }
}

/* =============================================================================
 * Collision Detection
 * =========================================================================== */

bool_t collision_aabb(fixed8_8 ax, fixed8_8 ay, u8 aw, u8 ah,
                      fixed8_8 bx, fixed8_8 by, u8 bw, u8 bh)
{
    /* Convert to integer for comparison */
    i16 ax_int = FP_TO_INT(ax);
    i16 ay_int = FP_TO_INT(ay);
    i16 bx_int = FP_TO_INT(bx);
    i16 by_int = FP_TO_INT(by);

    /* AABB overlap test */
    return hal_rect_overlap(ax_int, ay_int, aw, ah,
                           bx_int, by_int, bw, bh);
}

bool_t collision_entity_pair(entity_t* a, entity_t* b,
                             u8 a_width, u8 a_height,
                             u8 b_width, u8 b_height)
{
    /* Both must be active and collidable */
    if (!(a->flags & ENT_FLAG_ACTIVE)) return FALSE;
    if (!(b->flags & ENT_FLAG_ACTIVE)) return FALSE;
    if (!(a->flags & ENT_FLAG_COLLIDE)) return FALSE;
    if (!(b->flags & ENT_FLAG_COLLIDE)) return FALSE;

    return collision_aabb(a->x, a->y, a_width, a_height,
                         b->x, b->y, b_width, b_height);
}

void collision_check_types(entity_manager_t* em,
                          u8 type_a, u8 type_b,
                          u8 width_a, u8 height_a,
                          u8 width_b, u8 height_b,
                          collision_callback_fn callback)
{
    u16 i, j;
    entity_t* a;
    entity_t* b;

    /* O(n*m) collision check - okay for small counts */
    for (i = 0; i < em->capacity; i++) {
        a = &em->entities[i];

        /* Check type A */
        if (!(a->flags & ENT_FLAG_ACTIVE)) continue;
        if ((a->type & 0xF0) != type_a) continue;

        for (j = 0; j < em->capacity; j++) {
            if (i == j) continue;  /* Don't collide with self */

            b = &em->entities[j];

            /* Check type B */
            if (!(b->flags & ENT_FLAG_ACTIVE)) continue;
            if ((b->type & 0xF0) != type_b) continue;

            /* Check collision */
            if (collision_aabb(a->x, a->y, width_a, height_a,
                              b->x, b->y, width_b, height_b)) {
                callback(a, b);
            }
        }
    }
}
