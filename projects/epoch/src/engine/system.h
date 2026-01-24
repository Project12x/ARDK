#ifndef _ENGINE_SYSTEM_H_
#define _ENGINE_SYSTEM_H_

#include <genesis.h>

// =============================================================================
// GAME LIFECYCLE CALLBACKS
// =============================================================================
/**
 * @brief Game lifecycle callbacks.
 *
 * Defines the contract between the Engine and the Game.
 * Implementing these callbacks allows a game to run within the EPOCH engine.
 */
typedef struct {
  void (*init)(void); /**< Called once at startup. Initialize game resources. */
  void (*update)(void); /**< Called once per frame. Update game logic. */
  void (*draw)(void);   /**< Optional. Called after update for rendering. */

  /**
   * @brief Input event handler.
   * @param joy Joypad ID (JOY_1, etc.)
   * @param changed Changed button state
   * @param state Current button state
   */
  void (*joyEvent)(u16 joy, u16 changed, u16 state);
} GameCallbacks;

// =============================================================================
// SYSTEM API
// =============================================================================

/**
 * @brief Initialize the console hardware.
 *
 * Sets up the VDP (320x224, Planes A/B/Window), Input system, and generic
 * resources. This MUST be called before SYSTEM_run().
 */
void SYSTEM_init(void);

/**
 * @brief Execute the main game loop.
 *
 * This function enters an infinite loop and does not return.
 * It manages the standard Genesis frame cycle:
 * 1. Process Input
 * 2. Game Update (callback)
 * 3. Game Draw (callback)
 * 4. Engine Updates (Sprites, VBlank)
 * 5. Wait for VSync
 *
 * @param game Pointer to the GameCallbacks structure defining the game logic.
 */
void SYSTEM_run(const GameCallbacks *game);

#endif // _ENGINE_SYSTEM_H_
