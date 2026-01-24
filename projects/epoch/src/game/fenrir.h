#ifndef _GAME_FENRIR_H_
#define _GAME_FENRIR_H_

#include "engine/entity.h"
#include <genesis.h>

// =============================================================================
// FENRIR MODES
// =============================================================================
typedef enum {
  FENRIR_MODE_FOLLOW = 0, // Orbit/Follow player
  FENRIR_MODE_GUARD = 1,  // Stay close and attack nearby
  FENRIR_MODE_ATTACK = 2, // Actively hunt enemies
  FENRIR_MODE_FETCH = 3   // Fetch pickups
} FenrirMode;

// =============================================================================
// API
// =============================================================================

// Init (call from game_init)
void fenrir_init(void);

// Spawn Fenrir near player
void fenrir_spawn(s32 x, s32 y);

// Update AI and position
void fenrir_update(void);

// Get current mode
FenrirMode fenrir_getMode(void);

// Cycle to next mode
void fenrir_cycleMode(void);

#endif // _GAME_FENRIR_H_
