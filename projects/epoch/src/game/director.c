/**
 * EPOCH - Director System
 * Wave management, difficulty scaling, boss encounters
 */

#include "game/director.h"
#include "engine/math_fast.h"
#include "game.h"
#include "game/enemies.h"
#include "game/enemy_data.h"

// =============================================================================
// GLOBALS
// =============================================================================
DirectorState director;

// =============================================================================
// CONSTANTS
// =============================================================================
#define BASE_SPAWN_INTERVAL 90   // 1.5 seconds at 60fps
#define MIN_SPAWN_INTERVAL 30    // 0.5 second minimum
#define BASE_ENEMIES_PER_SPAWN 3 // Start with 3
#define MAX_ENEMIES_PER_SPAWN 6  // Cap at 6 per spawn
#define MAX_ACTIVE_ENEMIES 15    // v0.7.3: Reduced from 21 for 60fps stability
#define WAVE_ENEMY_COUNT_BASE 10 // Total enemies per wave
#define BOSS_WAVE_INTERVAL 5     // Boss every 5 waves

// =============================================================================
// INIT
// =============================================================================
void director_init(void) {
  director.waveNumber = 0;
  director.waveTimer = 0;
  director.spawnInterval = BASE_SPAWN_INTERVAL;
  director.enemiesPerSpawn = BASE_ENEMIES_PER_SPAWN;
  director.enemiesRemaining = 0;
  director.bossActive = 0;
  director.liveEnemyCount = 0; // OPTIMIZATION: Start with 0 live enemies
}

// =============================================================================
// WAVE START
// =============================================================================
void director_startWave(u16 waveNum) {
  director.waveNumber = waveNum;

  // Scale difficulty with wave number
  // Spawn interval decreases (faster spawns)
  u16 interval = BASE_SPAWN_INTERVAL - (waveNum * 10);
  if (interval < MIN_SPAWN_INTERVAL)
    interval = MIN_SPAWN_INTERVAL;
  director.spawnInterval = interval;

  // Enemies per spawn increases
  u8 perSpawn = BASE_ENEMIES_PER_SPAWN + (waveNum / 3);
  if (perSpawn > MAX_ENEMIES_PER_SPAWN)
    perSpawn = MAX_ENEMIES_PER_SPAWN;
  director.enemiesPerSpawn = perSpawn;

  // Total enemies this wave
  director.enemiesRemaining = WAVE_ENEMY_COUNT_BASE + (waveNum * 4);

  // Check for boss wave
  if ((waveNum % BOSS_WAVE_INTERVAL) == 0 && waveNum > 0) {
    // Spawn boss (use Tank as placeholder for now)
    enemy_spawn_by_id(ENEMY_ID_TANK);
    director.bossActive = 1;
  }

  director.waveTimer = director.spawnInterval;
}

// =============================================================================
// UPDATE (Called every frame)
// =============================================================================
void director_update(void) {
  // Auto-start first wave if not started
  if (director.waveNumber == 0) {
    director_startWave(1);
    return;
  }

  // Check if wave is complete (all enemies killed)
  if (director.enemiesRemaining == 0 && !director.bossActive) {
    // Start next wave after short delay
    director_startWave(director.waveNumber + 1);
    return;
  }

  // Spawn timer countdown
  if (director.waveTimer > 0) {
    director.waveTimer--;
    return; // Only count/spawn when timer hits 0
  }

  // Timer reached 0 - OPTIMIZED: Use cached count instead of looping
  u8 activeEnemies = director.liveEnemyCount;

  // Only spawn if under limit
  if (activeEnemies < MAX_ACTIVE_ENEMIES) {
    // Spawn a batch of enemies (up to remaining slots)
    EnemyId spawnType = ENEMY_ID_GRUNT; // Default

    // Vary enemy type based on wave
    if (director.waveNumber >= 3) {
      // Mix in Rushers
      if ((Math_randomRange(3)) == 0) {
        spawnType = ENEMY_ID_RUSHER;
      }
    }
    if (director.waveNumber >= 6) {
      // Mix in Tanks
      u8 roll = Math_randomRange(5);
      if (roll == 0)
        spawnType = ENEMY_ID_TANK;
      else if (roll == 1)
        spawnType = ENEMY_ID_RUSHER;
    }

    // Spawn batch (limited by remaining room)
    u8 toSpawn = director.enemiesPerSpawn;
    if (activeEnemies + toSpawn > MAX_ACTIVE_ENEMIES) {
      toSpawn = MAX_ACTIVE_ENEMIES - activeEnemies;
    }
    for (u8 i = 0; i < toSpawn; i++) {
      enemy_spawn_by_id(spawnType);
    }
  }

  // Reset timer
  director.waveTimer = director.spawnInterval;
}

// =============================================================================
// CALLBACKS
// =============================================================================
void director_onEnemyKilled(void) {
  if (director.enemiesRemaining > 0) {
    director.enemiesRemaining--;
  }
  // OPTIMIZATION: Decrement cached live count
  if (director.liveEnemyCount > 0) {
    director.liveEnemyCount--;
  }

  // Random drop chance (10% chance)
  if ((Math_randomRange(10)) == 0) {
    director_spawnDrop();
  }
  // Note: Boss death handled separately via bossActive flag
}

// OPTIMIZATION: Call when enemy spawns
void director_onEnemySpawned(void) { director.liveEnemyCount++; }

// OPTIMIZATION: Get cached count instead of looping
u8 director_getLiveEnemyCount(void) { return director.liveEnemyCount; }

// =============================================================================
// DROP SYSTEM
// =============================================================================
static u8 pendingBomb = 0; // Flag for bomb activation

void director_spawnDrop(void) {
  // Spawn bomb pickup entity within player view
  Entity *player = entity_getPlayer();
  if (!(player->flags & ENT_ACTIVE))
    return;

  // Random position within screen (offset from player)
  s16 offsetX = (Math_randomRange(200)) - 100; // -100 to +100 pixels
  s16 offsetY = (Math_randomRange(140)) - 70;  // -70 to +70 pixels

  s32 spawnX = player->x + FP(offsetX);
  s32 spawnY = player->y + FP(offsetY);

  // Clamp to map bounds
  if (spawnX < FP(16))
    spawnX = FP(16);
  if (spawnY < FP(16))
    spawnY = FP(16);
  if (spawnX > FP(MAP_WIDTH - 16))
    spawnX = FP(MAP_WIDTH - 16);
  if (spawnY > FP(MAP_HEIGHT - 16))
    spawnY = FP(MAP_HEIGHT - 16);

  // Allocate pickup entity
  s8 slot = entity_alloc(ENT_TYPE_PICKUP_BOMB);
  if (slot < 0)
    return;

  Entity *pickup = &entities[slot];
  pickup->x = spawnX;
  pickup->y = spawnY;
  pickup->flags = ENT_ACTIVE | ENT_PICKUP;
  pickup->timer = 255; // Lifetime (despawn timer)
}

void director_activateBomb(void) {
  // Damage all enemies for 60 damage
  for (u8 i = SLOT_ENEMIES_START; i <= SLOT_ENEMIES_END && i < MAX_ENTITIES;
       i++) {
    if (entities[i].flags & ENT_ACTIVE) {
      enemy_damage(i, 60);
    }
  }
  pendingBomb = 0;
}

u8 director_hasPendingBomb(void) { return pendingBomb; }
