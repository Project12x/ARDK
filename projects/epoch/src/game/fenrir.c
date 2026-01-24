#include "game/fenrir.h"
#include "engine/sinetable.h" // For floating bob effect
#include "game.h"
#include "game/enemies.h"

// =============================================================================
// CONSTANTS
// =============================================================================
#define FENRIR_FOLLOW_DIST FP(48) // Stay 48px behind player
// Note: FENRIR_SPEED is defined in constants.h

// =============================================================================
// STATIC STATE
// =============================================================================
static Sprite *fenrirSprite = NULL;
static FenrirMode currentMode = FENRIR_MODE_FOLLOW;

// OPTIMIZATION: Cache target to avoid searching every frame
static u8 cachedTargetSlot = 0xFF; // Cached enemy/pickup slot
static u8 searchTimer = 0;         // Only search every N frames
#define FENRIR_SEARCH_INTERVAL 15  // Search for targets every 15 frames

// Floating bob effect counter
static u8 bobCounter = 0;

// SPRITE CACHING: Reduce SPR_* calls
static u8 fenrirVisCache = 0xFF; // 0=HIDDEN, 1=VISIBLE, 0xFF=unset

// Placeholder: Reuse enemy sprite definition
extern const SpriteDefinition spr_fenrir;
extern const Palette pal_fenrir;
// =============================================================================
// INIT
// =============================================================================
void fenrir_init(void) {
  fenrirSprite = NULL;
  currentMode = FENRIR_MODE_FOLLOW;
  cachedTargetSlot = 0xFF;
  searchTimer = 0;
}

// =============================================================================
// SPAWN
// =============================================================================
void fenrir_spawn(s32 x, s32 y) {
  s8 slot = entity_alloc(ENT_TYPE_FENRIR);
  if (slot < 0)
    return;

  Entity *fenrir = &entities[slot];
  fenrir->flags = ENT_ACTIVE | ENT_VISIBLE | ENT_SOLID | ENT_FRIENDLY;
  fenrir->x = x;
  fenrir->y = y;
  fenrir->hp = 100;
  fenrir->frame = 0;

  // Create sprite using player palette (PAL0) for palette sharing
  s16 screenX = FP_INT(x) - FP_INT(cameraX);
  s16 screenY = FP_INT(y) - FP_INT(cameraY);
  fenrirSprite = SPR_addSprite(&spr_fenrir, screenX - 16, screenY - 16,
                               TILE_ATTR(PAL0, TRUE, FALSE, FALSE));
}

// =============================================================================
// UPDATE - OPTIMIZED: Only search for targets every 15 frames
// =============================================================================
void fenrir_update(void) {
  Entity *fenrir = entity_getFenrir();
  if (!(fenrir->flags & ENT_ACTIVE))
    return;

  Entity *player = entity_getPlayer();
  if (!(player->flags & ENT_ACTIVE))
    return;

  // OPTIMIZATION: Decrement search timer
  if (searchTimer > 0) {
    searchTimer--;
  }

  // Check if cached target is still valid
  Entity *target = NULL;
  if (cachedTargetSlot != 0xFF && cachedTargetSlot < MAX_ENTITIES) {
    Entity *cached = &entities[cachedTargetSlot];
    if (cached->flags & ENT_ACTIVE) {
      target = cached;
    } else {
      cachedTargetSlot = 0xFF; // Target died, clear cache
    }
  }

  switch (currentMode) {
  case FENRIR_MODE_FOLLOW: {
    // OPTIMIZATION: Only search for enemies periodically
    if (searchTimer == 0) {
      searchTimer = FENRIR_SEARCH_INTERVAL;

      // Quick scan using 16-bit pixel math (early exit on first find)
      s16 fx = (s16)(fenrir->x >> 8);
      s16 fy = (s16)(fenrir->y >> 8);
      for (u8 i = SLOT_ENEMIES_START; i <= SLOT_ENEMIES_END; i++) {
        if (entities[i].flags & ENT_ACTIVE) {
          s16 ex = (s16)(entities[i].x >> 8);
          s16 ey = (s16)(entities[i].y >> 8);
          s16 dx = ex - fx;
          s16 dy = ey - fy;
          if (dx < 0)
            dx = -dx;
          if (dy < 0)
            dy = -dy;
          if (dx < 64 && dy < 64) {
            cachedTargetSlot = i;
            currentMode = FENRIR_MODE_ATTACK;
            break;
          }
        }
      }
    }

    // Follow player with offset (16-bit pixel math)
    s16 px = (s16)(player->x >> 8);
    s16 py = (s16)(player->y >> 8);
    s16 fx = (s16)(fenrir->x >> 8);
    s16 fy = (s16)(fenrir->y >> 8);
    s16 dx = px - fx;
    s16 dy = py - fy;
    s16 abs_dx = (dx < 0) ? -dx : dx;
    s16 abs_dy = (dy < 0) ? -dy : dy;

    // Only move if too far from player (48 pixels)
    if (abs_dx > 48 || abs_dy > 48) {
      if (dx > 4)
        fenrir->vx = FENRIR_SPEED;
      else if (dx < -4)
        fenrir->vx = -FENRIR_SPEED;
      else
        fenrir->vx = 0;

      if (dy > 4)
        fenrir->vy = FENRIR_SPEED;
      else if (dy < -4)
        fenrir->vy = -FENRIR_SPEED;
      else
        fenrir->vy = 0;
    } else {
      fenrir->vx = 0;
      fenrir->vy = 0;
    }
    break;
  }

  case FENRIR_MODE_ATTACK: {
    // Use cached target if valid
    if (target) {
      // Move towards target
      s32 dx = target->x - fenrir->x;
      s32 dy = target->y - fenrir->y;

      if (dx > FP(2))
        fenrir->vx = FENRIR_SPEED;
      else if (dx < -FP(2))
        fenrir->vx = -FENRIR_SPEED;
      else
        fenrir->vx = 0;

      if (dy > FP(2))
        fenrir->vy = FENRIR_SPEED;
      else if (dy < -FP(2))
        fenrir->vy = -FENRIR_SPEED;
      else
        fenrir->vy = 0;

      // Attack Check - Melee Bite
      if (fenrir->timer == 0) {
        if (abs(dx) < FP(24) && abs(dy) < FP(24)) {
          enemy_damage(cachedTargetSlot, 25);
          fenrir->timer = 20;
        }
      } else {
        fenrir->timer--;
      }
    } else {
      // OPTIMIZATION: Search for new target only periodically
      if (searchTimer == 0) {
        searchTimer = FENRIR_SEARCH_INTERVAL;

        s32 minDist = FP(96);
        for (u8 i = SLOT_ENEMIES_START; i <= SLOT_ENEMIES_END; i++) {
          Entity *e = &entities[i];
          if (e->flags & ENT_ACTIVE) {
            s32 dx = e->x - fenrir->x;
            s32 dy = e->y - fenrir->y;
            s32 dist = abs(dx) + abs(dy);
            if (dist < minDist) {
              minDist = dist;
              cachedTargetSlot = i;
              target = e;
            }
          }
        }
      }

      if (!target) {
        currentMode = FENRIR_MODE_FOLLOW;
        cachedTargetSlot = 0xFF;
      }
    }
    break;
  }

  case FENRIR_MODE_FETCH:
  case FENRIR_MODE_GUARD:
    // Simplified: Just follow for now
    currentMode = FENRIR_MODE_FOLLOW;
    break;
  }

  // Apply velocity
  fenrir->x += fenrir->vx;
  fenrir->y += fenrir->vy;

  // Clamp to map bounds
  if (fenrir->x < FP(16))
    fenrir->x = FP(16);
  if (fenrir->y < FP(16))
    fenrir->y = FP(16);
  if (fenrir->x > FP(MAP_WIDTH - 16))
    fenrir->x = FP(MAP_WIDTH - 16);
  if (fenrir->y > FP(MAP_HEIGHT - 16))
    fenrir->y = FP(MAP_HEIGHT - 16);

  // Update sprite position with floating bob effect
  if (fenrirSprite) {
    s32 screenX = fenrir->x - cameraX;
    s32 screenY = fenrir->y - cameraY;
    s16 sx = FP_INT(screenX);
    s16 sy = FP_INT(screenY);

    // VISIBILITY CULLING - with caching
    if (sx < -32 || sx > SCREEN_WIDTH + 32 || sy < -32 ||
        sy > SCREEN_HEIGHT + 32) {
      // Off-screen - hide if not already hidden
      if (fenrirVisCache != 0) {
        SPR_setVisibility(fenrirSprite, HIDDEN);
        fenrirVisCache = 0;
      }
    } else {
      // On-screen - show if not already visible
      if (fenrirVisCache != 1) {
        SPR_setVisibility(fenrirSprite, VISIBLE);
        fenrirVisCache = 1;
      }

      // Apply sine bob effect (smooth floating motion)
      bobCounter += 4; // Speed of bob
      s16 bobOffset =
          sinLUT(bobCounter) >> 5; // Divide by 32 for subtle ~4px bob

      SPR_setPosition(fenrirSprite, sx - 16, sy - 16 + bobOffset);
      SPR_setDepth(fenrirSprite, -FP_INT(fenrir->y));
    }
  }
}

// =============================================================================
// MODE HELPERS
// =============================================================================
FenrirMode fenrir_getMode(void) { return currentMode; }

void fenrir_cycleMode(void) {
  currentMode = (FenrirMode)((currentMode + 1) % 3);
}
