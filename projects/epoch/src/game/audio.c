#include "game/audio.h"
#include "resources.h"
#include <snd/xgm2.h> // XGM2 driver for better Z80 offloading

// SFX Cooldown to prevent Z80 bus saturation
static u8 sfxCooldown[4] = {0, 0, 0, 0};
#define SFX_COOLDOWN_FRAMES 3

void audio_init(void) {
  // Load XGM2 driver (better Z80 offloading than XGM)
  Z80_loadDriver(Z80_DRIVER_XGM2, TRUE);
}

void audio_update(void) {
  // Decrement cooldowns each frame
  for (u8 i = 0; i < 4; i++) {
    if (sfxCooldown[i] > 0)
      sfxCooldown[i]--;
  }
}

void audio_play_sfx(u8 sfxId) {
  // Check cooldown to prevent Z80 bus saturation
  if (sfxId < 4 && sfxCooldown[sfxId] > 0) {
    return;
  }

  // Set cooldown
  if (sfxId < 4) {
    sfxCooldown[sfxId] = SFX_COOLDOWN_FRAMES;
  }

  // Play SFX via XGM2 (better performance than XGM)
  const u8 *sample = NULL;
  u32 len = 0;
  switch (sfxId) {
  case SFX_SHOOT:
    sample = sfx_shoot;
    len = sizeof(sfx_shoot);
    break;
  case SFX_HIT:
    sample = sfx_hit;
    len = sizeof(sfx_hit);
    break;
  case SFX_DIE:
    sample = sfx_die;
    len = sizeof(sfx_die);
    break;
  default:
    return;
  }
  XGM2_playPCM(sample, len, SOUND_PCM_CH2);
}
