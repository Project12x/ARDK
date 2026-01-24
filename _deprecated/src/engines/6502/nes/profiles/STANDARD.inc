; =============================================================================
; NES Engine - STANDARD Profile
; =============================================================================
; Balanced build with good performance and full features.
; Recommended for most games.
;
; Use for:
;   - General gameplay with visual polish
;   - Games needing parallax and CHR animation
;   - Balanced entity counts
; =============================================================================

.ifndef PROFILE_INCLUDED
PROFILE_INCLUDED = 1

; -----------------------------------------------------------------------------
; Profile Identifier
; -----------------------------------------------------------------------------
PROFILE_FAST     = 0
PROFILE_STANDARD = 1
PROFILE_FULL     = 0

; -----------------------------------------------------------------------------
; Entity Limits (balanced)
; -----------------------------------------------------------------------------
MAX_ENTITIES     = 48       ; Good entity count
MAX_ENEMIES      = 12       ; Reasonable enemy limit
MAX_PROJECTILES  = 24       ; More projectiles for weapon variety
MAX_PICKUPS      = 24       ; Standard pickup count
MAX_EFFECTS      = 12       ; Visual effects

; -----------------------------------------------------------------------------
; Optimization Flags
; -----------------------------------------------------------------------------
UNROLL_ENTITY_LOOP   = 0    ; Normal loop (smaller ROM)
USE_LOOKUP_TABLES    = 1    ; Still use lookup tables
INLINE_COLLISION     = 0    ; Use JSR for collision (code sharing)
FAST_MULTIPLY        = 1    ; Optimized multiply

; -----------------------------------------------------------------------------
; Feature Flags (most enabled)
; -----------------------------------------------------------------------------
PARALLAX_ENABLED     = 1    ; Enable parallax scrolling
CHR_ANIM_ENABLED     = 1    ; Enable animated backgrounds
SPRITE_FLICKER       = 1    ; Cycle sprites to reduce flicker
DEBUG_ENABLED        = 0    ; Debug off for release

; -----------------------------------------------------------------------------
; Memory Configuration
; -----------------------------------------------------------------------------
ENTITY_STRUCT_SIZE   = 16   ; Standard 16-byte entity
ZP_ENTITY_TEMPS      = 16   ; More ZP temps available

; -----------------------------------------------------------------------------
; Timing Budget
; -----------------------------------------------------------------------------
; STANDARD profile targets:
;   Entity update:  7000 cycles (48 entities x ~145 cycles)
;   Collision:      4000 cycles (standard AABB)
;   Parallax:       1500 cycles (IRQ setup)
;   CHR animation:   500 cycles (bank switch)
;   Rendering:      8000 cycles (OAM + sprite flicker)
;   Game logic:     6000 cycles
;   Available:      2780 cycles (tight but workable)

.endif ; PROFILE_INCLUDED
