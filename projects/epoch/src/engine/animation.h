#ifndef _ENGINE_ANIMATION_H_
#define _ENGINE_ANIMATION_H_

#include <genesis.h>

// =============================================================================
// ANIMATION MODES
// =============================================================================
#define ANIM_LOOP 0     // Play repeatedly
#define ANIM_ONCE 1     // Play once and stop at the last frame
#define ANIM_PINGPONG 2 // Play forward then backward repeatedly

// =============================================================================
// ANIMATION STRUCTURES
// =============================================================================

/**
 * @brief Defines a single animation sequence.
 *
 * Contains the frames, speed, and looping behavior for an animation.
 * Optimized for static storage (ROM).
 */
typedef struct {
  u8 numFrames; /**< Total number of frames in the sequence */
  u8 speed;     /**< Frame delay (ticks per frame). Higher = slower. */
  u8 loopMode; /**< Behavior when end is reached (ANIM_LOOP, ANIM_ONCE, etc.) */
  const u8 *frames; /**< Pointer to array of sprite indices */
} AnimDef;

/**
 * @brief Runtime state of an animation instance.
 *
 * Tracks the current frame, timer, and playback state for a specific entity.
 */
typedef struct {
  const AnimDef *anim; /**< Pointer to the animation definition being played */
  u8 currentFrame;     /**< Current index in the frame array */
  u8 timer;            /**< Internal timer for speed control */
  u8 finished;         /**< Flag: 1 if ANIM_ONCE has finished */
  s8 direction;        /**< Playback direction (1=forward, -1=backward) */
} AnimState;

// =============================================================================
// API
// =============================================================================

// =============================================================================
// API
// =============================================================================

/**
 * @brief Start playing an animation.
 *
 * @param state Pointer to the entity's animation state.
 * @param newAnim Pointer to the animation definition to play.
 * @param force If TRUE, resets the animation even if it's already playing.
 */
void anim_play(AnimState *state, const AnimDef *newAnim, bool force);

/**
 * @brief Update animation state. Call once per frame.
 *
 * Advances the timer and updates the current frame index based on logic.
 *
 * @param state Pointer to the animation state to update.
 */
void anim_update(AnimState *state);

/**
 * @brief Get the current sprite index to draw.
 *
 * @param state Pointer to the animation state.
 * @return u8 The sprite index from the frame array.
 */
u8 anim_getFrame(const AnimState *state);

#endif // _ENGINE_ANIMATION_H_
