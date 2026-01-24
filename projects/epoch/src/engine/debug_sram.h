#ifndef _ENGINE_DEBUG_SRAM_H_
#define _ENGINE_DEBUG_SRAM_H_

#include <genesis.h>

// =============================================================================
// SRAM DEBUG LOGGER
// =============================================================================
// Writes performance metrics to battery-backed SRAM for analysis.
// After running the game, open the .srm file in a hex editor to view data.
//
// SRAM Layout (starting at offset 0x0000):
//   0x00-0x03: Magic "DEBG" (0x44454247)
//   0x04-0x07: Total frames
//   0x08-0x0B: Slow frames (>16ms)
//   0x0C-0x1F: Per-subsystem timing (scanlines)
//   0x20-0x2F: Entity counts and peaks
//   0x30+:     Frame history (last 32 frames)
// =============================================================================

// Enable/disable SRAM logging (set to 0 for release builds)
#define DEBUG_SRAM_ENABLED 1

#if DEBUG_SRAM_ENABLED

// Debug data structure (mirrors SRAM layout)
typedef struct {
  u32 magic;       // 0x00: "DEBG" (0x44454247)
  u32 totalFrames; // 0x04: Total frames since start
  u32 slowFrames;  // 0x08: Frames that exceeded budget

  // Per-subsystem timing (in VDP scanlines, ~7.6us each)
  u16 playerLines;      // 0x0C: player_update scanlines
  u16 cameraLines;      // 0x0E: camera_update scanlines
  u16 directorLines;    // 0x10: director_update scanlines
  u16 enemiesLines;     // 0x12: enemies_update scanlines
  u16 projectilesLines; // 0x14: projectiles_update scanlines
  u16 fenrirLines;      // 0x16: fenrir_update scanlines
  u16 pickupsLines;     // 0x18: pickups_update scanlines
  u16 sprUpdateLines;   // 0x1A: SPR_update scanlines
  u16 totalFrameLines;  // 0x1C: Total frame scanlines
  u16 reserved1;        // 0x1E: Padding

  // Entity counts
  u8 activeEnemies;     // 0x20
  u8 activeProjectiles; // 0x21
  u8 visibleSprites;    // 0x22
  u8 reserved2;         // 0x23

  // Peak values (worst case)
  u16 peakFrameLines;   // 0x24: Worst total frame
  u16 peakEnemiesLines; // 0x26: Worst enemies_update
  u16 peakProjLines;    // 0x28: Worst projectiles_update
  u16 peakSprLines;     // 0x2A: Worst SPR_update

  // Reserved for future use
  u16 reserved3[2]; // 0x2C-0x2F

  // Rolling history: last 32 frame times (ring buffer)
  u16 frameHistory[32]; // 0x30-0x6F: Last 32 frame scanline counts
  u8 historyIndex;      // 0x70: Current position in ring buffer
} DebugSRAMData;

// Global debug data (in RAM, flushed to SRAM periodically)
extern DebugSRAMData debugData;

// Current timing session (for measuring individual functions)
extern u16 dbg_startLine;

// =============================================================================
// API
// =============================================================================

// Initialize debug system (call once at game start)
void debug_init(void);

// Start timing a section (uses VDP H-counter)
void debug_startTimer(void);

// Stop timing and return scanlines elapsed
u16 debug_stopTimer(void);

// Record timing for a specific subsystem
void debug_recordPlayer(u16 lines);
void debug_recordCamera(u16 lines);
void debug_recordDirector(u16 lines);
void debug_recordEnemies(u16 lines);
void debug_recordProjectiles(u16 lines);
void debug_recordFenrir(u16 lines);
void debug_recordPickups(u16 lines);
void debug_recordSprUpdate(u16 lines);

// Record entity counts
void debug_recordEntityCounts(u8 enemies, u8 projectiles, u8 sprites);

// Mark frame complete and flush to SRAM periodically
void debug_endFrame(void);

// Force flush to SRAM (call before soft reset or on pause)
void debug_flushToSRAM(void);

#else

// Disabled stubs
#define debug_init()
#define debug_startTimer()
#define debug_stopTimer() 0
#define debug_recordPlayer(l)
#define debug_recordCamera(l)
#define debug_recordDirector(l)
#define debug_recordEnemies(l)
#define debug_recordProjectiles(l)
#define debug_recordFenrir(l)
#define debug_recordPickups(l)
#define debug_recordSprUpdate(l)
#define debug_recordEntityCounts(e, p, s)
#define debug_endFrame()
#define debug_flushToSRAM()

#endif // DEBUG_SRAM_ENABLED

#endif // _ENGINE_DEBUG_SRAM_H_
