#include "game/pickups.h"
#include "engine/entity.h"
#include "game.h"
#include "game/director.h"
#include "game/projectiles.h"
#include "resources.h"

void pickups_init(void) {
  // No specific init
}

void pickups_spawn(s16 x, s16 y, u8 pickupType) {
  s8 slot = entity_alloc(ENT_TYPE_PICKUP_XP);
  if (slot < 0)
    return;

  Entity *p = &entities[(u8)slot];
  p->flags = ENT_ACTIVE | ENT_VISIBLE | ENT_PICKUP;

  // Default XP value
  u16 xpValue = 10;

  if (pickupType == PICKUP_XP_BIG) {
    xpValue = 50;
  }
  // If it's health or bomb, we need different logic or a different spawn
  // function For now, spawn() assumes XP based on calls. But let's handle the
  // passed type if it maps to Entity Types.

  // Safe mapping:
  if (pickupType == PICKUP_HEALTH) {
    p->type = ENT_TYPE_PICKUP_HEALTH;
  } else {
    p->type = ENT_TYPE_PICKUP_XP; // Small or Big
  }

  p->x = FP(x);
  p->y = FP(y);
  p->vx = 0;
  p->vy = 0;
  p->timer = 0;
  p->data = xpValue; // Store Value
}

void pickups_update(void) {
  Entity *player = entity_getPlayer();
  Entity *fenrir = entity_getFenrir();

  // OPTIMIZED: Only scan TOWERS slot range where pickups are allocated (58-63)
  // Reduces from 64 to 6 iterations
  // POINTER WALK OPTIMIZATION
  Entity *p = &entities[SLOT_TOWERS_START];
  Entity *end = &entities[SLOT_TOWERS_END];
  u8 i = SLOT_TOWERS_START;

  for (; p <= end; p++, i++) {
    if (!(p->flags & ENT_ACTIVE))
      continue;
    if (!(p->flags & ENT_PICKUP))
      continue;

    // Type Check
    bool isXP = (p->type == ENT_TYPE_PICKUP_XP);
    bool isBomb = (p->type == ENT_TYPE_PICKUP_BOMB);

    // Player Interaction
    if (player->flags & ENT_ACTIVE) {
      // PERF: Use 16-bit pixel math instead of 32-bit FP
      s16 px = (s16)(player->x >> 8);
      s16 py = (s16)(player->y >> 8);
      s16 pickX = (s16)(p->x >> 8);
      s16 pickY = (s16)(p->y >> 8);

      s16 dx = px - pickX;
      s16 dy = py - pickY;

      // Fast inline abs
      if (dx < 0)
        dx = -dx;
      if (dy < 0)
        dy = -dy;
      s16 dist = dx + dy;

      // Collection (approx < 20px Manhattan)
      if (dist < 20) {
        if (isXP) {
          game.playerXP += p->data;
        } else if (isBomb) {
          director_activateBomb();
        }
        entity_free(i);
        continue;
      }

      // Magnet (80px Manhattan) - Only for XP
      if (isXP && dist < 80) {
        // Move pickup toward player (shift in FP space)
        s32 fpDx = player->x - p->x;
        s32 fpDy = player->y - p->y;
        p->x += fpDx >> 4;
        p->y += fpDy >> 4;
      }
    }

    // Fenrir Collection (Only XP) - 16-bit pixel math
    if (isXP && fenrir && (fenrir->flags & ENT_ACTIVE)) {
      s16 fx = (s16)(fenrir->x >> 8);
      s16 fy = (s16)(fenrir->y >> 8);
      s16 pickX = (s16)(p->x >> 8);
      s16 pickY = (s16)(p->y >> 8);

      s16 dx = fx - pickX;
      s16 dy = fy - pickY;
      if (dx < 0)
        dx = -dx;
      if (dy < 0)
        dy = -dy;

      if ((dx + dy) < 20) {
        game.playerXP += 10;
        entity_free(i);
        continue;
      }
    }
  }
}
