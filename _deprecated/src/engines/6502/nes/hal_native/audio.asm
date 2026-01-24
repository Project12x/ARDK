; =============================================================================
; NEON SURVIVORS - Audio / APU Interface
; Simple sound effects using the NES APU
; =============================================================================
;
; PORTABILITY: This file is NES-specific (uses APU registers).
; When porting, replace with platform-specific audio API.
;
; =============================================================================

.include "nes.inc"

.segment "CODE"

; -----------------------------------------------------------------------------
; Initialize Audio/APU
; Sets up the APU for sound playback
; -----------------------------------------------------------------------------
.export audio_init
.proc audio_init
    ; Enable all sound channels
    lda #$0F        ; Enable Square 1, Square 2, Triangle, Noise
    sta APU_STATUS

    ; Disable frame IRQ
    lda #$40
    sta APU_FRAME

    ; Initialize Square 1 (for beeps)
    lda #$30        ; Duty 00, constant volume, volume 0
    sta APU_PULSE1_CTRL

    ; Initialize Square 2 (for effects)
    lda #$30
    sta APU_PULSE2_CTRL

    ; Initialize Triangle (for bass)
    lda #$80        ; Linear counter control, no reload
    sta APU_TRI_CTRL

    ; Initialize Noise (for percussion/hits)
    lda #$30        ; Constant volume, volume 0
    sta APU_NOISE_CTRL

    rts
.endproc

; -----------------------------------------------------------------------------
; Play Beep Sound
; Simple high-pitched beep for UI feedback
; -----------------------------------------------------------------------------
.export audio_play_beep
.proc audio_play_beep
    ; Set Square 1 to play a beep
    lda #$BF        ; Duty 10, constant volume, volume F (max)
    sta APU_PULSE1_CTRL

    ; Set frequency (A-4 note, ~440 Hz)
    lda #$FD        ; Period low byte
    sta APU_PULSE1_LO
    lda #$01        ; Period high byte (3 bits) + length counter
    sta APU_PULSE1_HI

    rts
.endproc

; -----------------------------------------------------------------------------
; Play Hit Sound
; Short noise burst for collision/hit effects
; -----------------------------------------------------------------------------
.export audio_play_hit
.proc audio_play_hit
    ; Set Noise channel
    lda #$9F        ; Constant volume, volume F
    sta APU_NOISE_CTRL

    ; Set noise period (short, high-pitched)
    lda #$04        ; Short period
    sta APU_NOISE_LO

    ; Trigger noise
    lda #$08        ; Length counter load
    sta APU_NOISE_HI

    rts
.endproc

; -----------------------------------------------------------------------------
; Play Shoot Sound
; Square wave sound for projectile firing
; -----------------------------------------------------------------------------
.export audio_play_shoot
.proc audio_play_shoot
    ; Set Square 2
    lda #$BF        ; Duty 10, constant volume, volume F
    sta APU_PULSE2_CTRL

    ; Set frequency (higher pitch than beep)
    lda #$7F        ; Period low byte
    sta APU_PULSE2_LO
    lda #$01        ; Period high byte + length
    sta APU_PULSE2_HI

    rts
.endproc

; -----------------------------------------------------------------------------
; Play Pickup Sound
; Rising pitch for collecting items
; -----------------------------------------------------------------------------
.export audio_play_pickup
.proc audio_play_pickup
    ; Set Triangle channel (sine-like wave)
    lda #$FF        ; Linear counter load
    sta APU_TRI_CTRL

    ; Set frequency (mid-range)
    lda #$9F        ; Period low byte
    sta APU_TRI_LO
    lda #$02        ; Period high byte + length
    sta APU_TRI_HI

    rts
.endproc

; -----------------------------------------------------------------------------
; Stop All Sounds
; Silences all channels
; -----------------------------------------------------------------------------
.export audio_stop_all
.proc audio_stop_all
    ; Set all channels to volume 0
    lda #$30        ; Duty, constant volume 0
    sta APU_PULSE1_CTRL
    sta APU_PULSE2_CTRL

    lda #$00
    sta APU_TRI_CTRL

    lda #$30
    sta APU_NOISE_CTRL

    rts
.endproc

; -----------------------------------------------------------------------------
; Audio Update
; Called each frame to update sound effects (envelopes, decay, etc.)
; For now, simple - just fades out sounds over time
; -----------------------------------------------------------------------------
.export audio_update
.proc audio_update
    ; TODO: Implement sound effect decay/envelope system
    ; For now, do nothing - sounds will play until length counter expires
    rts
.endproc
