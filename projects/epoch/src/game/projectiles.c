#include "game/projectiles.h"
#include "engine/spatial.h" // For spatial grid collision
#include "game.h"           // For game state and camera refs
#include "game/audio.h"
#include "game/enemies.h"

// =============================================================================
// GLOBALS / STATICS
// =============================================================================
// Projectile sprites (Object Pooling - Pre-allocated for performance)
#define MAX_VISIBLE_PROJECTILES 10 // Reduced to minimize SPR_update overhead
static Sprite *projectileSprites[MAX_VISIBLE_PROJECTILES];
static bool spriteSlotFree[MAX_VISIBLE_PROJECTILES];

// SPRITE CACHING: Reduce SPR_* calls
static s16 projPosXCache[MAX_VISIBLE_PROJECTILES]; // Cached X position
static s16 projPosYCache[MAX_VISIBLE_PROJECTILES]; // Cached Y position
static u8
    projVisCache[MAX_VISIBLE_PROJECTILES]; // 0=HIDDEN, 1=VISIBLE, 0xFF=unset

// OPTIMIZATION: Hint-based sprite slot search
static u8 lastFreeProjSlot = 0;

extern const SpriteDefinition spr_projectile;
extern const Palette pal_player; // Used for projectiles (PAL0 usually)

// =============================================================================
// HELPER: Find free projectile sprite slot (optimized)
// =============================================================================
static u8 findFreeProjSpriteSlot(void) {
  // Start from hint
  for (u8 i = lastFreeProjSlot; i < MAX_VISIBLE_PROJECTILES; i++) {
    if (spriteSlotFree[i]) {
      lastFreeProjSlot = i + 1;
      return i;
    }
  }
  // Wrap around
  for (u8 i = 0; i < lastFreeProjSlot && i < MAX_VISIBLE_PROJECTILES; i++) {
    if (spriteSlotFree[i]) {
      lastFreeProjSlot = i + 1;
      return i;
    }
  }
  return 0xFF; // No free slot
}

// =============================================================================
// INIT - Pre-allocate all projectile sprites (Object Pooling)
// =============================================================================
void projectiles_init(void) {
  // Initialize Object Pool: Allocate ALL sprites once at startup
  for (u8 i = 0; i < MAX_VISIBLE_PROJECTILES; i++) {
    // Clear existing if any (safety for soft reset)
    if (projectileSprites[i]) {
      SPR_releaseSprite(projectileSprites[i]);
    }

    // Allocate Sprite ONCE - never released during gameplay
    // Low priority + PAL3 for Shadow/Highlight glow effect
    projectileSprites[i] = SPR_addSprite(&spr_projectile, -32, -32,
                                         TILE_ATTR(PAL3, FALSE, FALSE, FALSE));

    // Default to Hidden (inactive)
    if (projectileSprites[i]) {
      SPR_setVisibility(projectileSprites[i], HIDDEN);
    }
    spriteSlotFree[i] = TRUE;
    projPosXCache[i] = -999; // Invalid - forces first update
    projPosYCache[i] = -999;
    projVisCache[i] = 0xFF; // Unset
  }
  lastFreeProjSlot = 0;
}

// =============================================================================
// SPAWN
// =============================================================================
void projectile_spawn(s16 x, s16 y, s8 dx, s8 dy) {
  s8 slot = entity_alloc(ENT_TYPE_PROJ_PLAYER);
  if (slot < 0)
    return;

  audio_play_sfx(SFX_SHOOT);

  Entity *proj = &entities[(u8)slot];
  proj->flags = ENT_ACTIVE | ENT_VISIBLE | ENT_FRIENDLY;
  proj->x = FP(x);
  proj->y = FP(y);
  proj->vx = FP(dx * 3); // Fast projectile in fixed-point
  proj->vy = FP(dy * 3);
  proj->timer = 60;  // Lifetime in frames
  proj->data = 0xFF; // No sprite yet

  // OPTIMIZED: Use pre-allocated pool
  u8 spriteSlot = findFreeProjSpriteSlot();
  if (spriteSlot != 0xFF) {
    s16 screenX = x - FP_INT(cameraX);
    s16 screenY = y - FP_INT(cameraY);

    // Activate Sprite from Pool
    spriteSlotFree[spriteSlot] = FALSE;
    Sprite *spr = projectileSprites[spriteSlot];

    if (spr) {
      SPR_setVisibility(spr, VISIBLE);
      SPR_setPosition(spr, screenX - 8, screenY - 8);
    }

    proj->data = spriteSlot;
  }
}

void projectile_spawn_visual(s16 x, s16 y) {
  s8 slot = entity_alloc(ENT_TYPE_PROJ_PLAYER);
  if (slot < 0)
    return;

  Entity *proj = &entities[(u8)slot];
  proj->flags = ENT_ACTIVE | ENT_VISIBLE; // Not Friendly (so no collision)
  proj->x = FP(x);
  proj->y = FP(y);
  proj->vx = 0;
  proj->vy = 0;
  proj->timer = 10; // Short lifetime (visual only)
  proj->data = 0xFF;

  // OPTIMIZED: Use pre-allocated pool
  u8 spriteSlot = findFreeProjSpriteSlot();
  if (spriteSlot != 0xFF) {
    s16 screenX = x - FP_INT(cameraX);
    s16 screenY = y - FP_INT(cameraY);

    // Activate Sprite from Pool
    spriteSlotFree[spriteSlot] = FALSE;
    Sprite *spr = projectileSprites[spriteSlot];

    if (spr) {
      SPR_setVisibility(spr, VISIBLE);
      SPR_setPosition(spr, screenX - 8, screenY - 8);
    }

    proj->data = spriteSlot;
  }
}

// =============================================================================
// HELPER: DESTROY
// =============================================================================
void projectile_destroy(u8 slot) {
  if (slot >= MAX_ENTITIES)
    return;
  Entity *proj = &entities[slot];

  // Return sprite to pool (hide, don't release)
  u8 pSpriteIdx = (u8)proj->data;
  if (pSpriteIdx < MAX_VISIBLE_PROJECTILES && projectileSprites[pSpriteIdx]) {
    SPR_setVisibility(projectileSprites[pSpriteIdx], HIDDEN);
    spriteSlotFree[pSpriteIdx] = TRUE;
    // NOTE: We do NOT release the sprite, we just hide it
  }
  entity_free(slot);
}

// =============================================================================
// UPDATE - Optimized with Spatial Hashing
// =============================================================================
void projectiles_update(void) {
  // Pre-calc camera
  s16 camXInt = FP_INT(cameraX);
  s16 camYInt = FP_INT(cameraY);

  Entity *proj = &entities[SLOT_PROJ_START];
  for (u8 i = SLOT_PROJ_START; i <= SLOT_PROJ_END; i++, proj++) {
    if ((proj->type & 0xF0) != ENT_TYPE_PROJ_PLAYER)
      continue; // Safety check
    if (!(proj->flags & ENT_ACTIVE))
      continue;

    // Move projectile
    proj->x += proj->vx;
    proj->y += proj->vy;

    // Update lifetime
    if (proj->timer > 0) {
      proj->timer--;
    }

    // Get sprite index from entity.data
    u8 spriteIdx = (u8)proj->data;

    // Remove if off screen (in world coords) or expired
    if (proj->timer == 0 || proj->x < 0 || proj->x > FP(MAP_WIDTH) ||
        proj->y < 0 || proj->y > FP(MAP_HEIGHT)) {
      projectile_destroy(i);
      continue;
    }

    // ═══════════════════════════════════════════════════════════════════════
    // THREE-GATE COLLISION (Gold Standard 68000 Optimization)
    // Replaces 9-cell nested loop with single optimized call
    // Gate 1: Bitmask filter (COLL_ENEMY)
    // Gate 2: Manhattan heuristic
    // Gate 3: Full AABB (only ~10% of checks reach this)
    // + Frame Staggering: 50% CPU reduction
    // ═══════════════════════════════════════════════════════════════════════
    u8 hitSlot =
        spatial_checkCollisionThreeGate(i, COLL_ENEMY, game.frameCount);
    bool hit = FALSE;

    if (hitSlot != 0xFF) {
      // Collision detected - damage enemy and destroy projectile
      enemy_damage(hitSlot, 10);
      projectile_destroy(i);
      hit = TRUE;
    }

    if (hit)
      continue;

    // Update sprite position (camera-relative) with culling + CACHING
    if (spriteIdx < MAX_VISIBLE_PROJECTILES && projectileSprites[spriteIdx]) {
      s16 px = FP_INT(proj->x) - camXInt;
      s16 py = FP_INT(proj->y) - camYInt;

      // Culling check
      if (px < -16 || px > SCREEN_WIDTH + 16 || py < -16 ||
          py > SCREEN_HEIGHT + 16) {
        // Off-screen - hide if not already hidden
        if (projVisCache[spriteIdx] != 0) {
          SPR_setVisibility(projectileSprites[spriteIdx], HIDDEN);
          projVisCache[spriteIdx] = 0;
        }
      } else {
        // On-screen - update with caching
        s16 drawX = px - 8;
        s16 drawY = py - 8;

        // PERF: Only call SPR_setVisibility when visibility changes
        if (projVisCache[spriteIdx] != 1) {
          SPR_setVisibility(projectileSprites[spriteIdx], VISIBLE);
          projVisCache[spriteIdx] = 1;
        }

        // PERF: Only call SPR_setPosition/Depth when position changes
        if (drawX != projPosXCache[spriteIdx] ||
            drawY != projPosYCache[spriteIdx]) {
          SPR_setPosition(projectileSprites[spriteIdx], drawX, drawY);
          SPR_setDepth(projectileSprites[spriteIdx], -FP_INT(proj->y));
          projPosXCache[spriteIdx] = drawX;
          projPosYCache[spriteIdx] = drawY;
        }
      }
    }
  }
}
