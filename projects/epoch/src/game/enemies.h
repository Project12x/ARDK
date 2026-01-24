#ifndef _GAME_ENEMIES_H_
#define _GAME_ENEMIES_H_

#include "engine/entity.h"
#include "game/enemy_data.h"
#include <genesis.h>

// Init
void enemies_init(void);

// Updates
void enemies_update(void);

// Spawning
void enemy_spawn_at(s32 x, s32 y);
void enemy_spawn_at_edge(void);
void enemy_spawn_by_id(EnemyId id);
void enemy_damage(u8 slot, u8 dmg);

// =============================================================================
// AI BEHAVIORS (VTable-lite)
// =============================================================================
void AI_Chase(Entity *self, s32 targetX, s32 targetY);
void AI_Flank(Entity *self, s32 targetX, s32 targetY);

#endif // _GAME_ENEMIES_H_
