#ifndef _GAME_ENEMY_DATA_H_
#define _GAME_ENEMY_DATA_H_

#include "engine/entity.h"

// =============================================================================
// ENEMY IDS
// =============================================================================
typedef enum {
  ENEMY_ID_GRUNT = 0,
  ENEMY_ID_RUSHER = 1,
  ENEMY_ID_TANK = 2,
  ENEMY_COUNT
} EnemyId;

// =============================================================================
// AI FUNCTION SIGNATURE
// =============================================================================
typedef void (*AIRoutine)(Entity *self, s32 targetX, s32 targetY);

// =============================================================================
// ENEMY DEFINITION (Static Data)
// =============================================================================
typedef struct {
  const char *name;    // Debug name
  s16 maxHP;           // Health points
  s16 speed;           // Movement speed (fixed-point 8.8)
  u16 scoreValue;      // Score on kill
  u8 entityType;       // ENT_TYPE_ENEMY_* value
  AIRoutine aiRoutine; // AI Function pointer
} EnemyDef;

// =============================================================================
// GLOBAL DATABASE
// =============================================================================
extern const EnemyDef EnemyDatabase[ENEMY_COUNT];

#endif // _GAME_ENEMY_DATA_H_
