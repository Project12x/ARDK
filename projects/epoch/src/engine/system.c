#include "engine/system.h"
#include "engine/math_fast.h"
#include "engine/profiler.h" // Visual frame profiler

// Global callback storage
static const GameCallbacks *currentGame = NULL;

// =============================================================================
// INPUT HANDLER WRAPPER
// =============================================================================
static void inputHandler(u16 joy, u16 changed, u16 state) {
  if (currentGame && currentGame->joyEvent) {
    currentGame->joyEvent(joy, changed, state);
  }
}

// =============================================================================
// SYSTEM INIT
// =============================================================================
void SYSTEM_init(void) {
  // 1. VDP Setup
  VDP_setScreenWidth320();
  VDP_setPlaneSize(64, 64, TRUE);
  VDP_setScrollingMode(HSCROLL_PLANE, VSCROLL_PLANE);

  // Window Plane (HUD area - Top 4 rows)
  VDP_setWindowVPos(FALSE, 4);

  // 2. Input Setup
  JOY_setEventHandler(inputHandler);

  // 3. Math Init
  Math_init();

  // 3. Audio / Misc (Can move XGM driver load here if generic)
  // Z80_loadDriver(Z80_DRIVER_XGM2, TRUE); // Example
}

// =============================================================================
// MAIN LOOP
// =============================================================================
void SYSTEM_run(const GameCallbacks *game) {
  currentGame = game;

  if (currentGame && currentGame->init) {
    currentGame->init();
  }

  while (TRUE) {
    // Game Logic
    if (currentGame && currentGame->update) {
      currentGame->update();
    }

    // Draw (if separate) or VDP processes
    if (currentGame && currentGame->draw) {
      currentGame->draw();
    }

    // Engine-level Updates (Sprites, VBlank) - PROFILED
    PROF_SPR_UPDATE_START();
    SPR_update();
    PROF_SPR_UPDATE_END();

    SYS_doVBlankProcess();
  }
}
