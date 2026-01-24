#include "engine/animation.h"

// =============================================================================
// PLAY ANIMATION
// =============================================================================
void anim_play(AnimState *state, const AnimDef *newAnim, bool force) {
  if (state->anim == newAnim && !force) {
    return; // Already playing this animation
  }

  state->anim = newAnim;
  state->currentFrame = 0;
  state->timer = 0;
  state->finished = 0;
  state->direction = 1; // Default to forward
}

// =============================================================================
// UPDATE ANIMATION
// =============================================================================
void anim_update(AnimState *state) {
  if (!state->anim)
    return; // No animation set
  if (state->finished)
    return; // Animation finished (ANIM_ONCE)

  state->timer++;

  // Check if it's time to advance frame
  if (state->timer >= state->anim->speed) {
    state->timer = 0;

    // Advance frame based on direction
    s16 nextFrame = state->currentFrame + state->direction;

    // Handle Loops / Ends
    if (nextFrame >= state->anim->numFrames) {
      // Reached END
      if (state->anim->loopMode == ANIM_ONCE) {
        state->currentFrame = state->anim->numFrames - 1;
        state->finished = 1;
      } else if (state->anim->loopMode == ANIM_PINGPONG) {
        state->currentFrame = state->anim->numFrames - 2; // Step back
        state->direction = -1;                            // Reverse
      } else {
        // ANIM_LOOP
        state->currentFrame = 0;
      }
    } else if (nextFrame < 0) {
      // Reached START in PingPong reverse
      if (state->anim->loopMode == ANIM_PINGPONG) {
        state->currentFrame = 1; // Step forward
        state->direction = 1;    // Forward
      } else {
        // Should not happen in Loop/Once, but safe fallback
        state->currentFrame = 0;
      }
    } else {
      // Valid next frame
      state->currentFrame = (u8)nextFrame;
    }
  }
}

// =============================================================================
// GET CURRENT FRAME
// =============================================================================
u8 anim_getFrame(const AnimState *state) {
  if (!state->anim || !state->anim->frames)
    return 0;
  return state->anim->frames[state->currentFrame];
}
