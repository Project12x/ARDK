#include "engine/spatial.h"
#include "engine/entity.h"
#include <string.h>

// =============================================================================
// GLOBAL GRID INSTANCE
// =============================================================================
SpatialGrid spatialGrid;

// =============================================================================
// CLEAR
// =============================================================================
void spatial_clear(void) {
  // Mark all cells as empty
  memset(spatialGrid.firstInCell, SPATIAL_NULL,
         sizeof(spatialGrid.firstInCell));
  memset(spatialGrid.nextEntity, SPATIAL_NULL, sizeof(spatialGrid.nextEntity));
}

// =============================================================================
// INSERT
// =============================================================================
void spatial_insert(u8 slot, s32 x, s32 y) {
  u16 cellIndex = spatial_getCellIndex(x, y);

  // Prepend to linked list
  spatialGrid.nextEntity[slot] = spatialGrid.firstInCell[cellIndex];
  spatialGrid.firstInCell[cellIndex] = slot;
}

// =============================================================================
// QUERY
// =============================================================================
u16 spatial_getFirstInCell(u16 cellIndex) {
  if (cellIndex >= SPATIAL_GRID_CELLS)
    return SPATIAL_NULL;
  return spatialGrid.firstInCell[cellIndex];
}

// =============================================================================
// THREE-GATE COLLISION (Gold Standard 68000 Optimization)
// =============================================================================
// REGISTER REUSE: Source entity data cached once, compared against many targets
// FRAME STAGGERING: Only checks even/odd slots per frame (50% CPU reduction)
// THREE GATES: Bitmask → Manhattan → AABB (abort early at each gate)
u8 spatial_checkCollisionThreeGate(u8 sourceSlot, u8 targetMask,
                                   u16 frameCount) {
  Entity *source = &entities[sourceSlot];

  // REGISTER REUSE: Cache source data in registers (compiler hint via local
  // vars)
  s16 srcX = (s16)(source->x >> 8); // Center X in pixels
  s16 srcY = (s16)(source->y >> 8); // Center Y in pixels
  s16 srcHalfW = source->width >> 1;
  s16 srcHalfH = source->height >> 1;

  // Manhattan threshold: Maximum possible overlap distance
  // If manhattan > this, AABB cannot possibly overlap
  s16 manhattanMax = srcHalfW + srcHalfH + 32; // +32 for target's half-size

  // Get source's grid cell
  u16 srcCell = spatial_getCellIndex(source->x, source->y);

  // Walk intrusive linked list in source's cell
  u8 slot = spatialGrid.firstInCell[srcCell];
  while (slot != SPATIAL_NULL) {
    // FRAME STAGGERING: Only check every other slot per frame
    // Even frames check even slots, odd frames check odd slots
    // This halves collision CPU cost with imperceptible 1-frame delay
    if ((slot & 1) == (frameCount & 1)) {
      Entity *target = &entities[slot];

      // Skip self and inactive entities
      if (slot != sourceSlot && (target->flags & ENT_ACTIVE)) {

        // ═══════════════════════════════════════════════════════════════════
        // GATE 1: BITMASK FILTER (1 AND instruction - cheapest possible check)
        // ═══════════════════════════════════════════════════════════════════
        if (target->collMask & targetMask) {

          // Convert target position to pixels
          s16 tgtX = (s16)(target->x >> 8);
          s16 tgtY = (s16)(target->y >> 8);

          // Distance calculation (reuse for both gates)
          s16 dx = srcX - tgtX;
          s16 dy = srcY - tgtY;

          // Fast inline abs (branchless would be mask>>31 trick, but this is
          // ok)
          if (dx < 0)
            dx = -dx;
          if (dy < 0)
            dy = -dy;

          // ═════════════════════════════════════════════════════════════════
          // GATE 2: MANHATTAN HEURISTIC (2 ADDs vs 4 CMPs - fast early exit)
          // ═════════════════════════════════════════════════════════════════
          if (dx + dy < manhattanMax) {

            // ═══════════════════════════════════════════════════════════════
            // GATE 3: FULL AABB (only reached ~10% of the time)
            // ═══════════════════════════════════════════════════════════════
            s16 tgtHalfW = target->width >> 1;
            s16 tgtHalfH = target->height >> 1;
            s16 combinedW = srcHalfW + tgtHalfW;
            s16 combinedH = srcHalfH + tgtHalfH;

            if (dx < combinedW && dy < combinedH) {
              return slot; // COLLISION DETECTED!
            }
          }
        }
      }
    }

    slot = spatialGrid.nextEntity[slot];
  }

  return 0xFF; // No collision
}
