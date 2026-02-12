/**
 * EPOCH - Constants and Hardware Limits
 * Sega Genesis / Mega Drive
 */

#ifndef _CONSTANTS_H_
#define _CONSTANTS_H_

// =============================================================================
// GAME INFO
// =============================================================================
#define GAME_NAME "EPOCH"
#define GAME_VERSION "0.1.0"

// =============================================================================
// SCREEN & MAP (Engine Overrides)
// =============================================================================
// Define engine overrides BEFORE including config.h
#define ARDK_MAP_WIDTH 1280
#define ARDK_MAP_HEIGHT 896
#define ARDK_MAX_ENTITIES 64

#include "engine/config.h"

// Map Helper Macros (using Engine Constants)
#define MAP_WIDTH_TILES (MAP_WIDTH / 8)
#define MAP_HEIGHT_TILES (MAP_HEIGHT / 8)

// Center Tower Position (center of map)
#define TOWER_X 640
#define TOWER_Y 448

// Camera Settings
#define CAMERA_DEADZONE_X 80
#define CAMERA_DEADZONE_Y 60
#define CAMERA_SPEED 0x0080 // 0.5 in fixed-point

// =============================================================================
// ZONE / MAP SYSTEM (Hybrid Rooms)
// =============================================================================
// Each zone is a 2x2 grid of screens
#define ROOM_WIDTH_TILES 40  // 320 / 8
#define ROOM_HEIGHT_TILES 28 // 224 / 8
#define ZONE_ROOMS_X 2
#define ZONE_ROOMS_Y 2
#define ZONE_WIDTH_TILES (ROOM_WIDTH_TILES * ZONE_ROOMS_X)   // 80
#define ZONE_HEIGHT_TILES (ROOM_HEIGHT_TILES * ZONE_ROOMS_Y) // 56
#define ZONE_WIDTH_PX (ZONE_WIDTH_TILES * 8)                 // 640
#define ZONE_HEIGHT_PX (ZONE_HEIGHT_TILES * 8)               // 448

#define ZONE_EXIT_MARGIN 8 // Pixels from edge to trigger zone transition
#define ZONE_BLOCKED 0xFF  // No exit in this direction

// =============================================================================
// ENTITY LIMITS (Game Specific)
// =============================================================================
#define MAX_ENEMIES 24
#define MAX_PROJECTILES 32
#define MAX_TOWERS 8
#define MAX_NPCS 4

// Slot aliases are provided by config.h, but we can verify or use them directly
// if needed. (SLOT_PLAYER, SLOT_ENEMIES_START, etc are in config.h)
// Game-Specific Slot Ends
#define SLOT_TOWERS_END (MAX_ENTITIES - 1)

// =============================================================================
// SPRITE SIZES
// =============================================================================
#define PLAYER_WIDTH 32
#define PLAYER_HEIGHT 32
#define FENRIR_WIDTH 24
#define FENRIR_HEIGHT 24
#define ENEMY_WIDTH 16
#define ENEMY_HEIGHT 16

// =============================================================================
// GAMEPLAY
// =============================================================================
#define SIEGE_DURATION_SEC 480 // 8 minutes
#define SIEGE_DURATION_FRAMES                                                  \
  (SIEGE_DURATION_SEC * 60) // ~28800 frames at 60fps

#define PLAYER_SPEED 0x0180 // Fixed 8.8: 1.5 pixels/frame
#define FENRIR_SPEED 0x0140 // Fixed 8.8: 1.25 pixels/frame
#define DASH_SPEED 0x0400   // Fixed 8.8: 4 pixels/frame
#define DASH_DURATION 12    // Frames
#define DASH_COOLDOWN 60    // 1 second cooldown between dashes

// =============================================================================
// FIXED POINT MATH (Provided by engine/config.h)
// =============================================================================
// FP(), FP_INT(), FP_FRAC() are available.
#define FP_ONE (1 << FP_SHIFT) // 256 = 1.0
#define FP_HALF (FP_ONE >> 1)  // 128 = 0.5

// =============================================================================
// INPUT
// =============================================================================
#define INPUT_DEADZONE 0x10 // Analog deadzone (if using analog)

// =============================================================================
// COMBAT
// =============================================================================
#define HEAT_MAX 100
#define HEAT_REGEN 1 // Per frame when not firing alt
#define ALT_FIRE_COST 25

#define INVULN_FRAMES 60      // 1 second of invincibility after hit
#define DASH_INVULN_FRAMES 10 // i-frames during dash

// =============================================================================
// UPGRADE SHOP (Tower-Based)
// =============================================================================
#define TOWER_INTERACT_RANGE 48  // Pixels from tower center to open shop

// Upgrade costs (XP)
#define UPGRADE_COST_FIRE_RATE  50
#define UPGRADE_COST_DAMAGE     75
#define UPGRADE_COST_SPREAD    150
#define UPGRADE_COST_FENRIR    100
#define UPGRADE_COST_MAGNET     60

// Max upgrade levels
#define UPGRADE_MAX_FIRE_RATE   5
#define UPGRADE_MAX_DAMAGE      4
#define UPGRADE_MAX_SPREAD      1
#define UPGRADE_MAX_FENRIR      1
#define UPGRADE_MAX_MAGNET      3

// Upgrade type indices
#define UPGRADE_FIRE_RATE  0
#define UPGRADE_DAMAGE     1
#define UPGRADE_SPREAD     2
#define UPGRADE_FENRIR     3
#define UPGRADE_MAGNET     4
#define UPGRADE_COUNT      5

#endif // _CONSTANTS_H_
