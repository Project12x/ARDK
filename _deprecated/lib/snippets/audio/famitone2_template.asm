; =============================================================================
; FAMITONE2 INTEGRATION TEMPLATE
; =============================================================================
; FamiTone2 is a compact music engine for NES (~1KB ROM)
; Plays music exported from FamiTracker
; =============================================================================

; -----------------------------------------------------------------------------
; FAMITONE2 CONFIGURATION
; -----------------------------------------------------------------------------
; FamiTone2 requires these defines before include

FT_DPCM_OFF      = 0             ; 1 = Disable DPCM (saves RAM)
FT_SFX_ENABLE    = 1             ; 1 = Enable sound effects
FT_THREAD        = 1             ; 1 = Thread-safe (call from NMI)
FT_PAL_SUPPORT   = 0             ; 1 = PAL timing support
FT_NTSC_SUPPORT  = 1             ; 1 = NTSC timing support

FT_SFX_STREAMS   = 4             ; Number of SFX channels (1-4)

; -----------------------------------------------------------------------------
; MEMORY ALLOCATION
; -----------------------------------------------------------------------------
.segment "ZEROPAGE"

; FamiTone2 uses ~36 bytes of zero page
; Reserve this block for the engine
FT_BASE_ADR = *                  ; Base address for FT variables
.res 36                          ; Reserve 36 bytes

.segment "BSS"

; FamiTone2 uses ~256 bytes of BSS
FT_BSS_BASE = *
.res 256

; -----------------------------------------------------------------------------
; INCLUDE FAMITONE2 ENGINE
; -----------------------------------------------------------------------------
; Download from: https://github.com/Shiru/NES/tree/master/famitone2

; .include "lib/famitone/famitone2.asm"

; -----------------------------------------------------------------------------
; MUSIC AND SFX DATA
; -----------------------------------------------------------------------------
; Export from FamiTracker using text export, then convert with text2data tool

.segment "RODATA"

; Music data (exported from FamiTracker)
; music_data:
;     .include "music/game_music.asm"

; Sound effects data
; sfx_data:
;     .include "sfx/game_sfx.asm"

; -----------------------------------------------------------------------------
; SOUND EFFECT CONSTANTS
; -----------------------------------------------------------------------------
; Define SFX IDs matching your exported data

SFX_JUMP        = 0
SFX_SHOOT       = 1
SFX_HIT         = 2
SFX_EXPLOSION   = 3
SFX_POWERUP     = 4
SFX_MENU_SELECT = 5
SFX_MENU_MOVE   = 6
SFX_DEATH       = 7

; Music track IDs
MUSIC_TITLE     = 0
MUSIC_GAMEPLAY  = 1
MUSIC_BOSS      = 2
MUSIC_GAMEOVER  = 3
MUSIC_VICTORY   = 4

; -----------------------------------------------------------------------------
; INITIALIZATION
; -----------------------------------------------------------------------------
.segment "CODE"

; -----------------------------------------------------------------------------
; audio_init - Initialize audio system
; Call once at startup
; -----------------------------------------------------------------------------
.proc audio_init
    ; Initialize FamiTone2 for NTSC
    lda #<music_data
    sta temp_ptr
    lda #>music_data
    sta temp_ptr+1
    ldx #$00                     ; NTSC mode
    ; jsr FamiToneInit

    ; Initialize SFX
    lda #<sfx_data
    sta temp_ptr
    lda #>sfx_data
    sta temp_ptr+1
    ; jsr FamiToneSfxInit

    rts

temp_ptr: .res 2
.endproc

; -----------------------------------------------------------------------------
; audio_update - Update audio (call every frame in NMI)
; -----------------------------------------------------------------------------
.proc audio_update
    ; jsr FamiToneUpdate
    rts
.endproc

; -----------------------------------------------------------------------------
; play_music - Start playing a music track
; Input: A = track number
; -----------------------------------------------------------------------------
.proc play_music
    ; jsr FamiToneMusicPlay
    rts
.endproc

; -----------------------------------------------------------------------------
; stop_music - Stop current music
; -----------------------------------------------------------------------------
.proc stop_music
    ; jsr FamiToneMusicStop
    rts
.endproc

; -----------------------------------------------------------------------------
; pause_music - Pause current music (can resume)
; Input: A = 0 to unpause, non-zero to pause
; -----------------------------------------------------------------------------
.proc pause_music
    ; jsr FamiToneMusicPause
    rts
.endproc

; -----------------------------------------------------------------------------
; play_sfx - Play a sound effect
; Input: A = SFX number, X = channel (0-3)
; -----------------------------------------------------------------------------
.proc play_sfx
    ; jsr FamiToneSfxPlay
    rts
.endproc

; =============================================================================
; HELPER MACROS
; =============================================================================

; Play SFX on any available channel
.macro PLAY_SFX sfx_id
    lda #sfx_id
    ldx #FT_SFX_CH0              ; Or cycle through channels
    jsr play_sfx
.endmacro

; Start music track
.macro PLAY_MUSIC track_id
    lda #track_id
    jsr play_music
.endmacro

; =============================================================================
; NMI HANDLER INTEGRATION
; =============================================================================
;
; In your NMI handler, call audio_update:
;
; nmi_handler:
;     pha
;     txa
;     pha
;     tya
;     pha
;
;     ; ... PPU updates ...
;
;     jsr audio_update          ; Update audio every frame
;
;     pla
;     tay
;     pla
;     tax
;     pla
;     rti

; =============================================================================
; FAMITRACKER EXPORT WORKFLOW
; =============================================================================
;
; 1. Create music in FamiTracker
;
; 2. Export as text:
;    File → Export text...
;    Save as music.txt
;
; 3. Convert with text2data:
;    tools\text2data music.txt -ca65
;    Output: music.asm
;
; 4. Include in your project:
;    music_data:
;        .include "music/music.asm"
;
; 5. Export SFX similarly, or use separate .nsf files

; =============================================================================
; FAMISTUDIO ALTERNATIVE
; =============================================================================
;
; FamiStudio is a modern alternative with built-in engine:
; https://famistudio.org/
;
; Benefits:
; - Modern UI (vs FamiTracker's dated interface)
; - Built-in sound engine export
; - Better compression
; - Active development
;
; Export:
; 1. Create music in FamiStudio
; 2. File → Export → Engine → Assembly
; 3. Select ca65 format
; 4. Include generated files

; =============================================================================
; USAGE EXAMPLE
; =============================================================================
;
; ; At game start:
;   jsr audio_init
;   PLAY_MUSIC MUSIC_TITLE
;
; ; When player jumps:
;   PLAY_SFX SFX_JUMP
;
; ; When entering gameplay:
;   PLAY_MUSIC MUSIC_GAMEPLAY
;
; ; When game over:
;   jsr stop_music
;   PLAY_SFX SFX_DEATH
;   ; Wait, then:
;   PLAY_MUSIC MUSIC_GAMEOVER
;
; ; In NMI:
;   jsr audio_update
;
; =============================================================================
