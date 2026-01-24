; =============================================================================
; NES Engine - FAST Profile
; =============================================================================
; Speed-optimized build with unrolled loops and lookup tables.
; Sacrifices features for maximum performance.
;
; Use for:
;   - Action-heavy scenes with many entities
;   - Competitive timing-sensitive gameplay
;   - Smaller ROM footprint (no parallax, no CHR animation)
; =============================================================================

.ifndef PROFILE_INCLUDED
PROFILE_INCLUDED = 1

; -----------------------------------------------------------------------------
; Profile Identifier
; -----------------------------------------------------------------------------
PROFILE_FAST     = 1
PROFILE_STANDARD = 0
PROFILE_FULL     = 0

; -----------------------------------------------------------------------------
; Entity Limits (reduced for speed)
; -----------------------------------------------------------------------------
MAX_ENTITIES     = 32       ; Fewer entities = faster iteration
MAX_ENEMIES      = 8        ; Limit enemies for consistent frame time
MAX_PROJECTILES  = 16       ; Standard projectile count
MAX_PICKUPS      = 16       ; Fewer pickups
MAX_EFFECTS      = 8        ; Minimal effects

; -----------------------------------------------------------------------------
; Optimization Flags
; -----------------------------------------------------------------------------
UNROLL_ENTITY_LOOP   = 1    ; Fully unroll entity update loop (larger ROM, faster)
USE_LOOKUP_TABLES    = 1    ; Use 256-byte sine/cos tables
INLINE_COLLISION     = 1    ; Inline collision checks (no JSR overhead)
FAST_MULTIPLY        = 1    ; Use optimized 8x8 multiply routine

; -----------------------------------------------------------------------------
; Feature Flags (disabled for speed)
; -----------------------------------------------------------------------------
PARALLAX_ENABLED     = 0    ; No parallax scrolling (saves IRQ time)
CHR_ANIM_ENABLED     = 0    ; No animated backgrounds (saves NMI time)
SPRITE_FLICKER       = 0    ; No sprite cycling (assume careful design)
DEBUG_ENABLED        = 0    ; No debug features

; -----------------------------------------------------------------------------
; Memory Configuration
; -----------------------------------------------------------------------------
ENTITY_STRUCT_SIZE   = 16   ; Standard 16-byte entity
ZP_ENTITY_TEMPS      = 8    ; Minimal ZP temps for entity processing

; -----------------------------------------------------------------------------
; Timing Budget (cycles per frame at 60fps = ~29780 cycles)
; -----------------------------------------------------------------------------
; FAST profile targets:
;   Entity update:  4000 cycles (32 entities x 125 cycles)
;   Collision:      3000 cycles (optimized AABB)
;   Rendering:      8000 cycles (OAM setup)
;   Game logic:     8000 cycles (player, weapons, spawning)
;   Available:      6780 cycles (headroom)

.endif ; PROFILE_INCLUDED
