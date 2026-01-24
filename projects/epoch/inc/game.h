/**
 * EPOCH - Game State and Core Structures
 * Sega Genesis / Mega Drive
 */

#ifndef _GAME_H_
#define _GAME_H_

#include "constants.h"
#include <genesis.h>

// =============================================================================
// GAME STATES
// =============================================================================
typedef enum {
  STATE_TITLE = 0,
  STATE_SIEGE = 1,
  STATE_EXPEDITION = 2,
  STATE_TOWN = 3,
  STATE_PAUSED = 4,
  STATE_LEVELUP = 5,
  STATE_GAMEOVER = 6
} GameState;

// =============================================================================
// ZONE IDS
// =============================================================================
typedef enum {
  ZONE_TOWER = 0,   // Central Tower (Siege area)
  ZONE_WILDS_1 = 1, // Wilds zone 1
  ZONE_TOWN_1 = 2,  // First town
  ZONE_COUNT
} ZoneId;

// =============================================================================
// DIRECTION
// =============================================================================
typedef enum {
  DIR_RIGHT = 0,
  DIR_DOWN_RIGHT = 1,
  DIR_DOWN = 2,
  DIR_DOWN_LEFT = 3,
  DIR_LEFT = 4,
  DIR_UP_LEFT = 5,
  DIR_UP = 6,
  DIR_UP_RIGHT = 7
} Direction;

// =============================================================================
// WEAPON TYPES
// =============================================================================
typedef enum {
  WEAPON_EMITTER = 0,  // Type A: Narrow precision beam
  WEAPON_SPREADER = 1, // Type B: Wide 45° cone
  WEAPON_HELIX = 2,    // Type C: Oscillating sine wave
  WEAPON_COUNT
} WeaponType;

// =============================================================================
// GAME STRUCTURE
// =============================================================================
typedef struct {
  GameState state;
  GameState prevState; // For pause/unpause

  u32 frameCount; // Global frame counter

  u16 siegeTimer;   // Frames remaining in siege
  u16 waveNumber;   // Current enemy wave
  u8 flickerOffset; // For sprite depth cycling (Xeno Crisis style)

  u8 currentZone; // ZoneId

  // Player stats
  u16 playerLevel;
  u32 playerXP;
  u32 score;

  // Resources
  u8 heat; // Alt-fire resource (0-100)

  // Flags
  u8 gateOpen; // Can exit siege area
  u8 paused;
} Game;

// =============================================================================
// INPUT STATE
// =============================================================================
typedef struct {
  u16 current;  // Current frame buttons
  u16 previous; // Previous frame buttons
  u16 pressed;  // Just pressed this frame
  u16 released; // Just released this frame
} InputState;

// =============================================================================
// GLOBALS
// =============================================================================
extern Game game;
extern InputState input;
extern u8 collisionMap[MAP_HEIGHT_TILES][MAP_WIDTH_TILES / 8];

// Camera Globals (Exposed for rendering)
extern s32 cameraX;
extern s32 cameraY;

// =============================================================================
// FUNCTION PROTOTYPES
// =============================================================================

// Game state management
void game_init(void);
void game_update(void);
void game_changeState(GameState newState);

// Input
void input_update(void);
bool input_isPressed(u16 button);
bool input_isHeld(u16 button);
bool input_justPressed(u16 button);
bool input_justReleased(u16 button);

#endif // _GAME_H_
