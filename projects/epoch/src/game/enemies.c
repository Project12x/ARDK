#include "game/enemies.h"
#include "engine/math_fast.h"
#include "engine/spatial.h"
#include "game.h"
#include "game/audio.h"
#include "game/director.h"
#include "game/pickups.h"
#include "game/projectiles.h"

/**
 * =============================================================================
 * EPOCH Engine - Enemy Subsystem
 * =============================================================================
 *
 * ARCHITECTURE: Hybrid Object Pool + Graphics Swap
 *
 * This module uses a pre-allocated sprite pool to avoid SGDK sprite allocation
 * during gameplay. All 24 enemy sprites are created at init and never released.
 *
 * KEY TECHNIQUES:
 * 1. Object Pool: Sprites are pre-allocated, toggled via SPR_setVisibility()
 * 2. Graphics Swap: SPR_setDefinition() changes sprite graphics at runtime
 * 3. Palette Swap: SPR_setPalette() distinguishes enemy types visually
 *
 * WHY THIS APPROACH:
 * - Frequent SPR_addSprite()/SPR_releaseSprite() caused SGDK state corruption
 * - VRAM fragmentation led to sprite allocation failures
 * - Pool pattern guarantees stable performance with 24 concurrent enemies
 *
 * SAT BUDGET: Uses slots 2-25 (24 sprites from 80 total)
 * =============================================================================
 */

// =============================================================================
// GLOBALS / STATICS
// =============================================================================

/**
 * ENEMY SPRITE POOL (v0.7.3 Optimized)
 *
 * Architecture: Pre-allocated sprite pool with graphics swapping
 * - Sprites allocated ONCE at init, NEVER released during gameplay
 * - Graphics swapped via SPR_setDefinition() based on enemy type
 * - Visibility toggled via SPR_setVisibility() for culling
 *
 * Performance Optimizations:
 * - spriteFlipCache: Only call SPR_setHFlip when flip state changes
 * - spritePosCache: Only call SPR_setPosition when position changes
 * - Hint-based slot search: O(1) average instead of O(N)
 * - MAX_VISIBLE_ENEMIES reduced to match screen capacity
 */
#define MAX_VISIBLE_ENEMIES 12 // Screen capacity (SAT: slots 2-13)

static Sprite *enemySprites[MAX_VISIBLE_ENEMIES] = {NULL};
static bool spriteSlotFree[MAX_VISIBLE_ENEMIES];
static u8 spriteFlipCache[MAX_VISIBLE_ENEMIES];  // 0=left, 1=right, 0xFF=unset
static s16 spritePosXCache[MAX_VISIBLE_ENEMIES]; // Cached X position
static s16 spritePosYCache[MAX_VISIBLE_ENEMIES]; // Cached Y position
static u8
    spriteVisCache[MAX_VISIBLE_ENEMIES]; // 0=HIDDEN, 1=VISIBLE, 0xFF=unset

// Hint-based sprite slot search for O(1) average case
static u8 lastFreeSpriteHint = 0;

// Sprite definitions (shared tilesets - multiple sprites reference same VRAM
// tiles)
extern const SpriteDefinition spr_enemy; // Large enemy (32x32, Tank)
extern const SpriteDefinition
    spr_enemy_small; // Small enemy (16x16, Grunt/Rusher)
extern const Palette pal_enemy;

// =============================================================================
// HELPER: Find free sprite slot (optimized)
// =============================================================================
static u8 findFreeSpriteSlot(void) {
  // Start search from last hint
  for (u8 s = lastFreeSpriteHint; s < MAX_VISIBLE_ENEMIES; s++) {
    if (spriteSlotFree[s]) {
      lastFreeSpriteHint = s + 1;
      return s;
    }
  }
  // Wrap around
  for (u8 s = 0; s < lastFreeSpriteHint && s < MAX_VISIBLE_ENEMIES; s++) {
    if (spriteSlotFree[s]) {
      lastFreeSpriteHint = s + 1;
      return s;
    }
  }
  return 0xFF; // No free slot
}

// =============================================================================
// INIT - Pre-allocate ALL enemy sprites (Object Pool Pattern)
// =============================================================================
void enemies_init(void) {
  // Pre-allocate all sprite slots using the small enemy sprite
  // (We'll resize/redefine as needed, but tiles will be shared)
  for (u8 i = 0; i < MAX_VISIBLE_ENEMIES; i++) {
    // Clear existing if any (safety for soft reset)
    if (enemySprites[i]) {
      SPR_releaseSprite(enemySprites[i]);
    }

    // Allocate sprite ONCE at init - use small enemy as default
    // Position off-screen initially
    enemySprites[i] = SPR_addSprite(&spr_enemy_small, -32, -32,
                                    TILE_ATTR(PAL2, TRUE, FALSE, FALSE));

    // Default to hidden (in pool, not active)
    if (enemySprites[i]) {
      SPR_setVisibility(enemySprites[i], HIDDEN);
    }
    spriteSlotFree[i] = TRUE;
    spriteFlipCache[i] = 0xFF; // Unset - will trigger initial SPR_setHFlip
    spritePosXCache[i] = -999; // Invalid position - forces first update
    spritePosYCache[i] = -999;
    spriteVisCache[i] = 0xFF; // Unset - forces first visibility update
  }
  lastFreeSpriteHint = 0;
}

// =============================================================================
// AI BEHAVIORS (v0.7.4 - PURE 16-BIT PIXEL MATH)
// All calculations done in pixels, not fixed-point
// =============================================================================

void AI_Chase(Entity *self, s32 targetX, s32 targetY) {
  // Convert to 16-bit pixels immediately
  s16 tx = (s16)(targetX >> 8);
  s16 ty = (s16)(targetY >> 8);
  s16 sx = (s16)(self->x >> 8);
  s16 sy = (s16)(self->y >> 8);

  s16 dx = tx - sx;
  s16 dy = ty - sy;

  EnemyId id =
      (EnemyId)(self->frame < ENEMY_COUNT ? self->frame : ENEMY_ID_GRUNT);
  s16 speed = EnemyDatabase[id].speed;

  // Manhattan distance for orbit check (all 16-bit)
  s16 absDx = dx;
  if (absDx < 0)
    absDx = -absDx;
  s16 absDy = dy;
  if (absDy < 0)
    absDy = -absDy;
  s16 manhattanDist = absDx + absDy;

  if (manhattanDist > 72) {
    // Outside orbit radius: move toward tower
    if (dx > 4)
      self->vx = speed;
    else if (dx < -4)
      self->vx = -speed;
    else
      self->vx = 0;

    if (dy > 4)
      self->vy = speed;
    else if (dy < -4)
      self->vy = -speed;
    else
      self->vy = 0;
  } else {
    // Inside orbit radius: circle around tower (clockwise)
    if (dy > 0)
      self->vx = speed;
    else
      self->vx = -speed;

    if (dx > 0)
      self->vy = -speed;
    else
      self->vy = speed;
  }
}

void AI_Flank(Entity *self, s32 targetX, s32 targetY) {
  // Convert to 16-bit pixels immediately
  s16 tx = (s16)(targetX >> 8);
  s16 ty = (s16)(targetY >> 8);
  s16 sx = (s16)(self->x >> 8);
  s16 sy = (s16)(self->y >> 8);

  s16 dx = tx - sx;
  s16 dy = ty - sy;

  EnemyId id =
      (EnemyId)(self->frame < ENEMY_COUNT ? self->frame : ENEMY_ID_RUSHER);
  s16 speed = EnemyDatabase[id].speed;

  // Add flank offset (in pixels)
  s16 offsetX = (dy > 0) ? 32 : -32;
  s16 offsetY = (dx > 0) ? -32 : 32;
  dx += offsetX;
  dy += offsetY;

  if (dx > 4)
    self->vx = speed;
  else if (dx < -4)
    self->vx = -speed;
  else
    self->vx = 0;

  if (dy > 4)
    self->vy = speed;
  else if (dy < -4)
    self->vy = -speed;
  else
    self->vy = 0;
}

// =============================================================================
// SPAWN
// =============================================================================
void enemy_spawn_by_id(EnemyId id) {
  if (id >= ENEMY_COUNT)
    return;

  const EnemyDef *def = &EnemyDatabase[id];
  s8 slot = entity_alloc(def->entityType);
  if (slot < 0)
    return;

  director_onEnemySpawned(); // OPTIMIZATION: Track live count

  Entity *enemy = &entities[(u8)slot];
  enemy->flags = ENT_ACTIVE | ENT_VISIBLE | ENT_SOLID | ENT_ENEMY;
  enemy->hp = def->maxHP;
  enemy->frame = id;
  enemy->data = 0xFF; // No sprite yet (will be assigned in update)

  // PERFORMANCE: Use shift-based random instead of expensive modulo/multiply
  // random() returns 0-65535. We need positions within map bounds.
  // Map is 1280x896. Use shifts: (random() >> 6) gives 0-1023, good enough for
  // 1280
  u16 side = random() & 3; // Fast mod-4 using AND
  u16 rnd = random();

  switch (side) {
  case 0:                              // Top edge
    enemy->x = FP(16 + (rnd & 0x3FF)); // 16 + 0-1023 = 16-1039
    enemy->y = FP(16);
    break;
  case 1: // Bottom edge
    enemy->x = FP(16 + (rnd & 0x3FF));
    enemy->y = FP(MAP_HEIGHT - 16);
    break;
  case 2: // Left edge
    enemy->x = FP(16);
    enemy->y = FP(16 + ((rnd >> 6) & 0x1FF) + ((rnd >> 2) & 0xFF)); // ~0-767
    break;
  case 3: // Right edge
    enemy->x = FP(MAP_WIDTH - 16);
    enemy->y = FP(16 + ((rnd >> 6) & 0x1FF) + ((rnd >> 2) & 0xFF));
    break;
  }
}

void enemy_spawn_at(s32 x, s32 y) {
  EnemyId id = ENEMY_ID_GRUNT;
  s8 slot = entity_alloc(ENT_TYPE_ENEMY_BASIC);
  if (slot < 0)
    return;

  director_onEnemySpawned(); // OPTIMIZATION: Track live count

  Entity *enemy = &entities[(u8)slot];
  enemy->flags = ENT_ACTIVE | ENT_VISIBLE | ENT_SOLID | ENT_ENEMY;
  enemy->hp = EnemyDatabase[id].maxHP;
  enemy->frame = id;
  enemy->data = 0xFF;
  enemy->x = x;
  enemy->y = y;
}

void enemy_spawn_at_edge(void) { enemy_spawn_by_id(ENEMY_ID_GRUNT); }

// =============================================================================
// DAMAGE LOGIC
// =============================================================================
void enemy_damage(u8 slot, u8 dmg) {
  if (slot < MAX_ENTITIES && (entities[slot].flags & ENT_ACTIVE)) {
    Entity *enemy = &entities[slot];

    if (enemy->hp > dmg) {
      enemy->hp -= dmg;
      enemy->timer = 4; // Flash timer
      audio_play_sfx(SFX_HIT);
    } else {
      // DEATH
      enemy->hp = 0;
      audio_play_sfx(SFX_DIE);

      // Drop XP
      pickups_spawn(FP_INT(enemy->x), FP_INT(enemy->y), PICKUP_XP_SMALL);

      enemy->flags &= ~ENT_VISIBLE; // Hide immediately
      enemy->timer = 0;

      // Score
      EnemyId id =
          (EnemyId)(enemy->frame < ENEMY_COUNT ? enemy->frame : ENEMY_ID_GRUNT);
      game.score += EnemyDatabase[id].scoreValue;

      // Return Sprite to Pool (hide, don't release)
      u8 spriteIdx = (u8)enemy->data;
      if (spriteIdx < MAX_VISIBLE_ENEMIES && enemySprites[spriteIdx]) {
        SPR_setVisibility(enemySprites[spriteIdx], HIDDEN);
        spriteSlotFree[spriteIdx] = TRUE;
        enemy->data = 0xFF;
      }

      entity_free(slot);
      director_onEnemyKilled();
    }
  }
}

// =============================================================================
// UPDATE
// =============================================================================
void enemies_update(void) {
  // Pre-calculate constants
  s16 camXInt = FP_INT(cameraX);
  s16 camYInt = FP_INT(cameraY);
  s32 targetX = FP(TOWER_X);
  s32 targetY = FP(TOWER_Y);
  u8 frameSlice =
      game.frameCount & 0x0F; // For off-screen throttle (every 16 frames)

  // === ENEMY LOOP (Pointer Walk) ===
  Entity *enemy = &entities[SLOT_ENEMIES_START];
  Entity *end = &entities[SLOT_ENEMIES_END];

  for (; enemy <= end; enemy++) {
    if (enemy->flags & ENT_ACTIVE) {
      if (enemy->flags & ENT_VISIBLE) {
        EnemyId id = (EnemyId)(enemy->frame < ENEMY_COUNT ? enemy->frame
                                                          : ENEMY_ID_GRUNT);
        const EnemyDef *def = &EnemyDatabase[id];
        u8 slot = (u8)(enemy - entities);

        // Decrement flash timer (for damage blink effect)
        if (enemy->timer > 0) {
          enemy->timer--;
        }

        // AI (Time-Slicing: only update every 4 frames based on slot)
        if (def->aiRoutine && ((slot & 3) == (game.frameCount & 3))) {
          def->aiRoutine(enemy, targetX, targetY);
        }

        // Physics & Collision (TIME-SLICED for performance)
        // Collision only checked every 2 frames per enemy (50% reduction)
        // Enemies still move every frame - collision just catches up
        s32 nextX = enemy->x + enemy->vx;
        s32 nextY = enemy->y + enemy->vy;

        // Time-slice collision: slot % 2 == frameCount % 2
        if ((slot & 1) == (game.frameCount & 1)) {
          // Check X movement
          if (!entity_checkTileCollision(enemy, FP_INT(nextX),
                                         FP_INT(enemy->y))) {
            enemy->x = nextX;
          }
          // Check Y movement
          if (!entity_checkTileCollision(enemy, FP_INT(enemy->x),
                                         FP_INT(nextY))) {
            enemy->y = nextY;
          }
        } else {
          // Skip collision this frame, just move
          enemy->x = nextX;
          enemy->y = nextY;
        }

        // Spatial Grid
        spatial_insert(slot, enemy->x, enemy->y);

        // Sprite Culling & Update
        s16 screenX = FP_INT(enemy->x) - camXInt;
        s16 screenY = FP_INT(enemy->y) - camYInt;
        u8 spriteIdx = (u8)enemy->data;

        // Use wider culling margins (64px)
        if (screenX > -64 && screenX < SCREEN_WIDTH + 64 && screenY > -64 &&
            screenY < SCREEN_HEIGHT + 64) {
          // VISIBLE - Get a sprite from pool if needed
          if (spriteIdx == 0xFF) {
            u8 s = findFreeSpriteSlot();
            if (s != 0xFF && enemySprites[s]) {
              spriteSlotFree[s] = FALSE;
              enemy->data = s;
              spriteIdx = s;

              // GRAPHICS SWAP: Set sprite definition based on enemy type
              const SpriteDefinition *sprDef =
                  (id == ENEMY_ID_TANK) ? &spr_enemy : &spr_enemy_small;
              SPR_setDefinition(enemySprites[s], sprDef);

              // Set palette based on enemy type
              u8 palIdx = (id == ENEMY_ID_RUSHER)
                              ? PAL1
                              : ((id == ENEMY_ID_TANK) ? PAL0 : PAL2);
              SPR_setPalette(enemySprites[s], palIdx);

              // Set initial visibility
              SPR_setVisibility(enemySprites[s], VISIBLE);
            }
          }

          // Update sprite position and visibility (WITH CACHING)
          if (spriteIdx != 0xFF && enemySprites[spriteIdx]) {
            s16 offset = (id == ENEMY_ID_TANK) ? 16 : 8;
            s16 drawX = screenX - offset;
            s16 drawY = screenY - offset;

            // PERF: Only call SPR_setPosition when position changes
            if (drawX != spritePosXCache[spriteIdx] ||
                drawY != spritePosYCache[spriteIdx]) {
              SPR_setPosition(enemySprites[spriteIdx], drawX, drawY);
              spritePosXCache[spriteIdx] = drawX;
              spritePosYCache[spriteIdx] = drawY;
              // Only update depth when position changes
              SPR_setDepth(enemySprites[spriteIdx], -FP_INT(enemy->y));
            }

            // PERF: Only call SPR_setVisibility when visibility actually
            // changes
            u8 newVis = (enemy->timer & 4) ? 0 : 1; // 0=HIDDEN, 1=VISIBLE
            if (newVis != spriteVisCache[spriteIdx]) {
              SPR_setVisibility(enemySprites[spriteIdx],
                                newVis ? VISIBLE : HIDDEN);
              spriteVisCache[spriteIdx] = newVis;
            }

            // PERF: Only call SPR_setHFlip when flip state actually changes
            u8 newFlip =
                (enemy->vx > 0)
                    ? 1
                    : ((enemy->vx < 0) ? 0 : spriteFlipCache[spriteIdx]);
            if (newFlip != spriteFlipCache[spriteIdx] && newFlip != 0xFF) {
              SPR_setHFlip(enemySprites[spriteIdx], newFlip);
              spriteFlipCache[spriteIdx] = newFlip;
            }
          }
        } else {
          // OFF SCREEN - Return sprite to pool
          if (spriteIdx != 0xFF && enemySprites[spriteIdx]) {
            SPR_setVisibility(enemySprites[spriteIdx], HIDDEN);
            spriteSlotFree[spriteIdx] = TRUE;
            spriteFlipCache[spriteIdx] = 0xFF; // Reset cache
            spritePosXCache[spriteIdx] = -999; // Reset position cache
            spritePosYCache[spriteIdx] = -999;
            spriteVisCache[spriteIdx] = 0xFF; // Reset visibility cache
            enemy->data = 0xFF;
          }
        }
      }
    }
  }

  // Wave Management
  if (director_getLiveEnemyCount() < 4) {
    enemy_spawn_at_edge();
  }
}
