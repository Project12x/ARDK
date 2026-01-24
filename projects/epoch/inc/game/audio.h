#ifndef AUDIO_H
#define AUDIO_H

#include <genesis.h>

// SFX IDs for playback
#define SFX_SHOOT 1
#define SFX_HIT 2
#define SFX_DIE 3

#define CH_SFX SOUND_PCM_CH1

void audio_init(void);
void audio_update(void);
void audio_play_sfx(u8 sfxId);

#endif // AUDIO_H
