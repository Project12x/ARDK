/**
 * ARDK Engine Configuration
 *
 * Default engine constants.
 */

#ifndef _ENGINE_CONFIG_H_
#define _ENGINE_CONFIG_H_

#include <genesis.h>

// =============================================================================
// ENTITY SYSTEM
// =============================================================================
#ifndef ARDK_MAX_ENTITIES
#define ARDK_MAX_ENTITIES 64
#endif

// =============================================================================
// MAP DIMENSIONS
// =============================================================================
#ifndef ARDK_MAP_WIDTH
#define ARDK_MAP_WIDTH 1280
#endif

#ifndef ARDK_MAP_HEIGHT
#define ARDK_MAP_HEIGHT 896
#endif

// =============================================================================
// FIXED POINT MATH
// =============================================================================
#define ARDK_FP_SHIFT 8
#define ARDK_FP(x) ((x) << ARDK_FP_SHIFT)
#define ARDK_FP_INT(x) ((x) >> ARDK_FP_SHIFT)
#define ARDK_FP_FRAC(x) ((x) & 0xFF)

// =============================================================================
// SCREEN DIMENSIONS
// =============================================================================
#define ARDK_SCREEN_WIDTH 320
#define ARDK_SCREEN_HEIGHT 224

// =============================================================================
// ENTITY SLOT RANGES - Games can override these
// =============================================================================
#ifndef ARDK_SLOT_PLAYER
#define ARDK_SLOT_PLAYER 0
#endif
#ifndef ARDK_SLOT_COMPANION
#define ARDK_SLOT_COMPANION 1
#endif
#ifndef ARDK_SLOT_ENEMIES_START
#define ARDK_SLOT_ENEMIES_START 2
#endif
#ifndef ARDK_SLOT_ENEMIES_END
#define ARDK_SLOT_ENEMIES_END 25
#endif
#ifndef ARDK_SLOT_PROJ_START
#define ARDK_SLOT_PROJ_START 26
#endif
#ifndef ARDK_SLOT_PROJ_END
#define ARDK_SLOT_PROJ_END 57
#endif
#ifndef ARDK_SLOT_MISC_START
#define ARDK_SLOT_MISC_START 58
#endif

// =============================================================================
// COMPATIBILITY ALIASES - For existing code using old names
// =============================================================================
#define MAX_ENTITIES ARDK_MAX_ENTITIES
#define MAP_WIDTH ARDK_MAP_WIDTH
#define MAP_HEIGHT ARDK_MAP_HEIGHT
#define FP_SHIFT ARDK_FP_SHIFT
#define FP(x) ARDK_FP(x)
#define FP_INT(x) ARDK_FP_INT(x)
#define FP_FRAC(x) ARDK_FP_FRAC(x)
#define SCREEN_WIDTH ARDK_SCREEN_WIDTH
#define SCREEN_HEIGHT ARDK_SCREEN_HEIGHT

// Slot aliases
#define SLOT_PLAYER ARDK_SLOT_PLAYER
#define SLOT_FENRIR ARDK_SLOT_COMPANION
#define SLOT_ENEMIES_START ARDK_SLOT_ENEMIES_START
#define SLOT_ENEMIES_END ARDK_SLOT_ENEMIES_END
#define SLOT_PROJ_START ARDK_SLOT_PROJ_START
#define SLOT_PROJ_END ARDK_SLOT_PROJ_END
#define SLOT_TOWERS_START ARDK_SLOT_MISC_START

#endif // _ENGINE_CONFIG_H_
