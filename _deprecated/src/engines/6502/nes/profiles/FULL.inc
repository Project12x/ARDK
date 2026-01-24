; =============================================================================
; NES Engine - FULL Profile
; =============================================================================
; Maximum features enabled. Largest ROM, most entity capacity.
; May require careful frame budget management.
;
; Use for:
;   - Maximum entity counts (bullet hell, swarm games)
;   - All visual features enabled
;   - Debug builds during development
; =============================================================================

.ifndef PROFILE_INCLUDED
PROFILE_INCLUDED = 1

; -----------------------------------------------------------------------------
; Profile Identifier
; -----------------------------------------------------------------------------
PROFILE_FAST     = 0
PROFILE_STANDARD = 0
PROFILE_FULL     = 1

; -----------------------------------------------------------------------------
; Entity Limits (maximum)
; -----------------------------------------------------------------------------
MAX_ENTITIES     = 64       ; Maximum entities
MAX_ENEMIES      = 16       ; Maximum enemies (all OAM for them if needed)
MAX_PROJECTILES  = 32       ; Bullet hell support
MAX_PICKUPS      = 32       ; Maximum pickups
MAX_EFFECTS      = 16       ; Full effects

; -----------------------------------------------------------------------------
; Optimization Flags
; -----------------------------------------------------------------------------
UNROLL_ENTITY_LOOP   = 1    ; Unrolled for max speed (need it with 64 entities)
USE_LOOKUP_TABLES    = 1    ; Full lookup tables
INLINE_COLLISION     = 1    ; Inline for speed
FAST_MULTIPLY        = 1    ; Optimized multiply

; -----------------------------------------------------------------------------
; Feature Flags (all enabled)
; -----------------------------------------------------------------------------
PARALLAX_ENABLED     = 1    ; Full parallax
CHR_ANIM_ENABLED     = 1    ; Animated backgrounds
SPRITE_FLICKER       = 1    ; Sprite cycling
DEBUG_ENABLED        = 1    ; Debug features available

; -----------------------------------------------------------------------------
; Memory Configuration
; -----------------------------------------------------------------------------
ENTITY_STRUCT_SIZE   = 16   ; Standard 16-byte entity
ZP_ENTITY_TEMPS      = 32   ; Maximum ZP temps

; -----------------------------------------------------------------------------
; Timing Budget
; -----------------------------------------------------------------------------
; FULL profile pushes timing limits:
;   Entity update:  10000 cycles (64 entities, unrolled)
;   Collision:       5000 cycles (inline, many checks)
;   Parallax:        1500 cycles
;   CHR animation:    500 cycles
;   Rendering:       8000 cycles
;   Game logic:      4000 cycles
;   Available:        780 cycles (VERY tight - may drop frames!)
;
; WARNING: FULL profile may cause slowdown with max entities.
; Use frame skip or reduce entity counts dynamically.

; -----------------------------------------------------------------------------
; Debug Features (only in FULL profile)
; -----------------------------------------------------------------------------
.if DEBUG_ENABLED
    DEBUG_SHOW_HITBOXES  = 1    ; Draw collision boxes
    DEBUG_SHOW_FRAMETIME = 1    ; Display frame timing
    DEBUG_ENTITY_COUNT   = 1    ; Show entity count on screen
.endif

.endif ; PROFILE_INCLUDED
