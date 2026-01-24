#include "game/enemy_data.h"

// Forward declarations of AI routines (defined in enemies.c)
extern void AI_Chase(Entity *self, s32 targetX, s32 targetY);
extern void AI_Flank(Entity *self, s32 targetX, s32 targetY);

// =============================================================================
// ENEMY DATABASE
// =============================================================================
const EnemyDef EnemyDatabase[ENEMY_COUNT] = {
    // [ID]           = { name,     HP,  speed, score, entType, aiFunc }
    [ENEMY_ID_GRUNT] = {"Grunt", 30, 0x80, 100, ENT_TYPE_ENEMY_BASIC, AI_Chase},
    [ENEMY_ID_RUSHER] = {"Rusher", 15, 0xC0, 150, ENT_TYPE_ENEMY_FAST,
                         AI_Flank},
    [ENEMY_ID_TANK] = {"Tank", 100, 0x40, 300, ENT_TYPE_ENEMY_TANK, AI_Chase}};
