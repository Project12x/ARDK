#ifndef _GAME_PROJECTILES_H_
#define _GAME_PROJECTILES_H_

#include "engine/entity.h"
#include <genesis.h>

// Init
void projectiles_init(void);

// Updates
void projectiles_update(void);

// Actions
void projectile_spawn(s16 x, s16 y, s8 dx, s8 dy);
void projectile_spawn_visual(s16 x, s16 y);
void projectile_destroy(u8 slot);

#endif // _GAME_PROJECTILES_H_
