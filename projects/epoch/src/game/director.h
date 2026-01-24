/**
 * EPOCH - Director System
 * Wave management, difficulty scaling, boss encounters
 */

#ifndef _GAME_DIRECTOR_H_
#define _GAME_DIRECTOR_H_

#include <genesis.h>

// =============================================================================
// DIRECTOR STATE
// =============================================================================
typedef struct {
  u16 waveNumber;       // Current wave (1-indexed)
  u16 waveTimer;        // Frames until next spawn batch
  u16 spawnInterval;    // Frames between spawn batches
  u16 enemiesPerSpawn;  // Enemies spawned per batch
  u16 enemiesRemaining; // Enemies left to kill this wave
  u8 bossActive;        // 1 if boss is alive
  u8 liveEnemyCount;    // OPTIMIZATION: Cached count of active enemies
} DirectorState;

extern DirectorState director;

// =============================================================================
// FUNCTION PROTOTYPES
// =============================================================================
void director_init(void);
void director_update(void);
void director_startWave(u16 waveNum);
void director_onEnemyKilled(void);
void director_onEnemySpawned(void);  // OPTIMIZATION: Call when enemy spawns
u8 director_getLiveEnemyCount(void); // OPTIMIZATION: Get cached count

// Drop system
void director_spawnDrop(void);
void director_activateBomb(void);
u8 director_hasPendingBomb(void);

#endif // _GAME_DIRECTOR_H_
