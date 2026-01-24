#ifndef _ENGINE_SPATIAL_H_
#define _ENGINE_SPATIAL_H_

#include "engine/config.h"
#include <genesis.h>

// =============================================================================
// SPATIAL GRID CONFIGURATION
// =============================================================================
#define SPATIAL_CELL_SIZE 64
#define SPATIAL_CELL_SHIFT 6 // log2(64) for fast division

// PERFORMANCE: Grid width MUST be power of 2 for fast multiplication via shift!
// Map is 1280x896, with 64px cells = 20x14 logical cells
// We use 32x16 grid (next power of 2) to enable shift: cellY << 5 instead of *
// 20
#define SPATIAL_GRID_W_SHIFT 5                     // log2(32) for fast multiply
#define SPATIAL_GRID_W (1 << SPATIAL_GRID_W_SHIFT) // 32 (power of 2!)
#define SPATIAL_GRID_H 16                          // 16 (already power of 2)
#define SPATIAL_GRID_CELLS (SPATIAL_GRID_W * SPATIAL_GRID_H) // 512

#define SPATIAL_NULL 0xFF // Empty cell marker

// =============================================================================
// SPATIAL GRID STRUCTURE
// =============================================================================
typedef struct {
  u8 firstInCell[SPATIAL_GRID_CELLS]; // Slot of first entity in each cell
  u8 nextEntity[MAX_ENTITIES];        // Next entity in same cell (linked list)
} SpatialGrid;

// =============================================================================
// GLOBAL GRID INSTANCE
// =============================================================================
extern SpatialGrid spatialGrid;

// =============================================================================
// API
// =============================================================================

// Clear all cells (call once per frame before inserting)
void spatial_clear(void);

// Insert entity into grid based on its position
void spatial_insert(u8 slot, s32 x, s32 y);

// Get cell index from world position
static inline u16 spatial_getCellIndex(s32 x, s32 y) {
  s16 px = FP_INT(x);
  s16 py = FP_INT(y);

  if (px < 0)
    px = 0;
  if (px >= MAP_WIDTH)
    px = MAP_WIDTH - 1;
  if (py < 0)
    py = 0;
  if (py >= MAP_HEIGHT)
    py = MAP_HEIGHT - 1;

  u8 cellX = px >> SPATIAL_CELL_SHIFT;
  u8 cellY = py >> SPATIAL_CELL_SHIFT;

  if (cellX >= SPATIAL_GRID_W)
    cellX = SPATIAL_GRID_W - 1;
  if (cellY >= SPATIAL_GRID_H)
    cellY = SPATIAL_GRID_H - 1;
  // PERFORMANCE: Use shift instead of multiply (cellY << 5 instead of * 32)
  return cellX + (cellY << SPATIAL_GRID_W_SHIFT);
}

// Iterate entities in a cell (returns first slot, use nextEntity[] to iterate)
u16 spatial_getFirstInCell(u16 cellIndex);

// =============================================================================
// THREE-GATE COLLISION (Gold Standard 68000 Optimization)
// =============================================================================
// Gate 1: Bitmask filter (1 AND instruction)
// Gate 2: Manhattan heuristic (fast distance pre-check)
// Gate 3: Full AABB (only if Gates 1 & 2 pass)
//
// Uses Frame Staggering: Only checks even/odd slots per frame (50% CPU
// reduction) Returns slot of first collision, or 0xFF if none
u8 spatial_checkCollisionThreeGate(u8 sourceSlot, u8 targetMask,
                                   u16 frameCount);

#endif // _ENGINE_SPATIAL_H_
