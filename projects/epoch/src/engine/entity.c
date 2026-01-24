#include "engine/entity.h"
#include "game.h"   // For collisionMap
#include <string.h> // For memset

// =============================================================================
// GLOBALS
// =============================================================================
Entity entities[MAX_ENTITIES];
u8 entityCount = 0;

PlayerData playerData;
FenrirData fenrirData;

// =============================================================================
// ENTITY POOL MANAGEMENT
// =============================================================================
void entity_initPool(void) {
  memset(entities, 0, sizeof(entities));
  entityCount = 0;

  // Clear other data
  memset(&playerData, 0, sizeof(PlayerData));
  memset(&fenrirData, 0, sizeof(FenrirData));
}

s8 entity_alloc(u8 type) {
  // Find free slot based on type
  u8 start, end;

  // Determine slot range based on type category (upper nibble)
  switch (type & 0xF0) {
  case 0x10: // Player/Fenrir
    start = SLOT_PLAYER;
    end = SLOT_FENRIR + 1;
    break;
  case 0x20: // Enemies
    start = SLOT_ENEMIES_START;
    end = SLOT_ENEMIES_END + 1;
    break;
  case 0x30: // Projectiles
    start = SLOT_PROJ_START;
    end = SLOT_PROJ_END + 1;
    break;
  default:
    start = SLOT_TOWERS_START;
    end = MAX_ENTITIES;
    break;
  }

  // Linear scan for free slot in range
  for (u8 i = start; i < end; i++) {
    if (!(entities[i].flags & ENT_ACTIVE)) {
      // Found free slot
      entities[i].flags = ENT_ACTIVE | ENT_VISIBLE;
      entities[i].type = type;
      entities[i].timer = 0;
      entities[i].data = 0;

      // Default Hitbox Sizes (Width/Height)
      // Can be overridden after alloc if needed
      if ((type & 0xF0) == ENT_TYPE_PLAYER) {
        entities[i].width = 16;
        entities[i].height = 16;
        entities[i].collMask =
            (type == ENT_TYPE_PLAYER) ? COLL_PLAYER : COLL_FENRIR;
      } else if ((type & 0xF0) == ENT_TYPE_ENEMY_BASIC) { // 0x20
        entities[i].width = 24;
        entities[i].height = 24;
        entities[i].collMask = COLL_ENEMY;
      } else if ((type & 0xF0) == ENT_TYPE_PROJ_PLAYER) { // 0x30
        entities[i].width = 12;
        entities[i].height = 12;
        entities[i].collMask =
            (type == ENT_TYPE_PROJ_PLAYER) ? COLL_PROJ_PLR : COLL_PROJ_ENY;
      } else if ((type & 0xF0) == ENT_TYPE_TOWER_BASIC) { // 0x40
        entities[i].width = 64;
        entities[i].height = 64;
        entities[i].collMask = COLL_TOWER;
      } else if ((type & 0xF0) == 0x60) { // Pickups
        entities[i].width = 16;
        entities[i].height = 16;
        entities[i].collMask = COLL_PICKUP;
      } else {
        entities[i].width = 16;
        entities[i].height = 16;
        entities[i].collMask = COLL_NONE;
      }

      entityCount++;
      return i;
    }
  }

  return -1; // No free slot
}

void entity_free(u8 slot) {
  if (slot < MAX_ENTITIES && (entities[slot].flags & ENT_ACTIVE)) {
    entities[slot].flags = 0;
    entities[slot].type = ENT_TYPE_NONE;
    if (entityCount > 0)
      entityCount--;
  }
}

void entity_freeAll(void) { entity_initPool(); }

// =============================================================================
// ENTITY QUEIRES
// =============================================================================
Entity *entity_getPlayer(void) { return &entities[SLOT_PLAYER]; }

Entity *entity_getFenrir(void) { return &entities[SLOT_FENRIR]; }

// AABB Collision Check (v0.7.4 - PURE 16-BIT MATH)
// Converts to integer pixels immediately to avoid all 32-bit operations
bool entity_checkCollision(Entity *a, Entity *b) {
  // Convert to 16-bit integer pixels (FP_INT = >> 8)
  s16 ax = (s16)(a->x >> 8);
  s16 ay = (s16)(a->y >> 8);
  s16 bx = (s16)(b->x >> 8);
  s16 by = (s16)(b->y >> 8);

  // Compute distance (16-bit)
  s16 dx = ax - bx;
  s16 dy = ay - by;

  // Fast inline abs (16-bit)
  if (dx < 0)
    dx = -dx;
  if (dy < 0)
    dy = -dy;

  // Combined half-widths in pixels (u8 + u8 = u16, >> 1 = u8)
  // No need for FP conversion since we're in pixel space
  s16 combinedHalfW = (a->width + b->width) >> 1;
  s16 combinedHalfH = (a->height + b->height) >> 1;

  return (dx < combinedHalfW && dy < combinedHalfH);
}
// Find nearest entity matching the given FLAG mask
u8 entity_findNearest(s16 x, s16 y, u8 flagMask) {
  u8 nearest = 0xFF; // Invalid
  s32 minDist = 0x7FFFFFFF;

  // Mask high/low slots based on expected type? No, search all.
  // Optimization: Could limit search range based on mask if we knew types.
  // But linear scan of 64 is fast enough.

  for (u8 i = 0; i < MAX_ENTITIES; i++) {
    if ((entities[i].flags & ENT_ACTIVE) && (entities[i].flags & flagMask)) {
      // Calculate distance (Manhattan is faster and sufficient)
      s32 dx = FP_INT(entities[i].x) - x;
      s32 dy = FP_INT(entities[i].y) - y;
      s32 dist = abs(dx) + abs(dy);

      if (dist < minDist) {
        minDist = dist;
        nearest = i;
      }
    }
  }
  return nearest;
}
// Check collision against static map tiles
// NOTE: newX/newY are INTEGER pixel coordinates, not fixed-point!
bool entity_checkTileCollision(Entity *e, s16 newX, s16 newY) {
  // newX/newY are already integer pixels (caller does FP_INT conversion)
  s16 x = newX;
  s16 y = newY;

  // Check 4 corners of hitbox
  // Hitbox offsets from center (SHIFT for speed)
  s16 halfW = e->width >> 1;
  s16 halfH = e->height >> 1;

  s16 left = x - halfW;
  s16 right = x + halfW;
  s16 top = y - halfH;
  s16 bottom = y + halfH;

  // CLAMP PIXEL VALUES FIRST (before shift) to avoid negative→u16 overflow
  if (left < 0)
    left = 0;
  if (top < 0)
    top = 0;
  if (right >= MAP_WIDTH)
    right = MAP_WIDTH - 1;
  if (bottom >= MAP_HEIGHT)
    bottom = MAP_HEIGHT - 1;

  // Early exit if completely out of bounds
  if (left >= MAP_WIDTH || right < 0 || top >= MAP_HEIGHT || bottom < 0) {
    return FALSE; // Off map = no collision
  }

  // Now safe to convert to tile coords with shift
  u16 tLeft = left >> 3;
  u16 tRight = right >> 3;
  u16 tTop = top >> 3;
  u16 tBottom = bottom >> 3;

  // Clamp tile coords to valid range (should already be OK but safety check)
  if (tLeft >= MAP_WIDTH_TILES)
    tLeft = MAP_WIDTH_TILES - 1;
  if (tRight >= MAP_WIDTH_TILES)
    tRight = MAP_WIDTH_TILES - 1;
  if (tTop >= MAP_HEIGHT_TILES)
    tTop = MAP_HEIGHT_TILES - 1;
  if (tBottom >= MAP_HEIGHT_TILES)
    tBottom = MAP_HEIGHT_TILES - 1;

  // Check all tiles covered by hitbox
  for (u16 ty = tTop; ty <= tBottom; ty++) {
    for (u16 tx = tLeft; tx <= tRight; tx++) {
      // Bitwise check: collisionMap[ty][tx/8] & (1 << (tx%8))
      if (collisionMap[ty][tx >> 3] & (1 << (tx & 7))) {
        return TRUE; // Collision detected
      }
    }
  }

  return FALSE;
}
