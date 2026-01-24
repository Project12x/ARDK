#ifndef _ENGINE_PROFILER_H_
#define _ENGINE_PROFILER_H_

#include "engine/debug_sram.h"
#include <genesis.h>


// =============================================================================
// VISUAL FRAME PROFILER + SRAM TIMING
// =============================================================================
// Uses background color changes to measure function timing visually.
// Also records precise scanline counts to SRAM for hex analysis.
//
// Run the ROM and observe the colored bars on the left edge of screen:
// - Larger bar = more time consumed
// - Each color represents a different subsystem
//
// After running, open the .srm file to see numerical data.
// =============================================================================

// Enable/disable profiling (set to 0 for release builds)
#define PROFILER_ENABLED 1

#if PROFILER_ENABLED

// Color definitions (Genesis RGB format: 0x0BGR)
#define PROF_COLOR_PLAYER 0x000E      // Red
#define PROF_COLOR_CAMERA 0x00E0      // Green
#define PROF_COLOR_DIRECTOR 0x00EE    // Yellow
#define PROF_COLOR_ENEMIES 0x0E00     // Blue
#define PROF_COLOR_PROJECTILES 0x0E0E // Magenta
#define PROF_COLOR_FENRIR 0x0EE0      // Cyan
#define PROF_COLOR_PICKUPS 0x0888     // Gray
#define PROF_COLOR_HUD 0x0EEE         // White
#define PROF_COLOR_SPR_UPDATE 0x040E  // Dark Red/Brown
#define PROF_COLOR_VBLANK 0x0000      // Black (reset)

// Timing variables (defined in debug_sram.c)
extern u16 dbg_startLine;

// Macro to set profiler color AND start timing
#define PROF_START(color)                                                      \
  do {                                                                         \
    PAL_setColor(0, color);                                                    \
    debug_startTimer();                                                        \
  } while (0)

#define PROF_END() PAL_setColor(0, PROF_COLOR_VBLANK)

// Named profiler markers with SRAM recording
#define PROF_PLAYER_START() PROF_START(PROF_COLOR_PLAYER)
#define PROF_PLAYER_END()                                                      \
  debug_recordPlayer(debug_stopTimer());                                       \
  PROF_END()

#define PROF_CAMERA_START() PROF_START(PROF_COLOR_CAMERA)
#define PROF_CAMERA_END()                                                      \
  debug_recordCamera(debug_stopTimer());                                       \
  PROF_END()

#define PROF_DIRECTOR_START() PROF_START(PROF_COLOR_DIRECTOR)
#define PROF_DIRECTOR_END()                                                    \
  debug_recordDirector(debug_stopTimer());                                     \
  PROF_END()

#define PROF_ENEMIES_START() PROF_START(PROF_COLOR_ENEMIES)
#define PROF_ENEMIES_END()                                                     \
  debug_recordEnemies(debug_stopTimer());                                      \
  PROF_END()

#define PROF_PROJECTILES_START() PROF_START(PROF_COLOR_PROJECTILES)
#define PROF_PROJECTILES_END()                                                 \
  debug_recordProjectiles(debug_stopTimer());                                  \
  PROF_END()

#define PROF_FENRIR_START() PROF_START(PROF_COLOR_FENRIR)
#define PROF_FENRIR_END()                                                      \
  debug_recordFenrir(debug_stopTimer());                                       \
  PROF_END()

#define PROF_PICKUPS_START() PROF_START(PROF_COLOR_PICKUPS)
#define PROF_PICKUPS_END()                                                     \
  debug_recordPickups(debug_stopTimer());                                      \
  PROF_END()

#define PROF_HUD_START() PROF_START(PROF_COLOR_HUD)
#define PROF_HUD_END() PROF_END()

#define PROF_SPR_UPDATE_START() PROF_START(PROF_COLOR_SPR_UPDATE)
#define PROF_SPR_UPDATE_END()                                                  \
  debug_recordSprUpdate(debug_stopTimer());                                    \
  PROF_END()

#else

// Profiling disabled - macros expand to nothing
#define PROF_START(color)
#define PROF_END()
#define PROF_PLAYER_START()
#define PROF_PLAYER_END()
#define PROF_CAMERA_START()
#define PROF_CAMERA_END()
#define PROF_DIRECTOR_START()
#define PROF_DIRECTOR_END()
#define PROF_ENEMIES_START()
#define PROF_ENEMIES_END()
#define PROF_PROJECTILES_START()
#define PROF_PROJECTILES_END()
#define PROF_FENRIR_START()
#define PROF_FENRIR_END()
#define PROF_PICKUPS_START()
#define PROF_PICKUPS_END()
#define PROF_HUD_START()
#define PROF_HUD_END()
#define PROF_SPR_UPDATE_START()
#define PROF_SPR_UPDATE_END()

#endif // PROFILER_ENABLED

#endif // _ENGINE_PROFILER_H_
