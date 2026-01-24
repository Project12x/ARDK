/* =============================================================================
 * Genesis Engine - STANDARD Profile
 * =============================================================================
 * Balanced build with good performance and features.
 * Recommended for most games.
 * =========================================================================== */

#ifndef PROFILE_INCLUDED
#define PROFILE_INCLUDED 1

/* Profile Identifier */
#define PROFILE_FAST     0
#define PROFILE_STANDARD 1
#define PROFILE_FULL     0

/* Entity Limits */
#define MAX_ENTITIES     192
#define MAX_ENEMIES      48
#define MAX_PROJECTILES  64
#define MAX_PICKUPS      48
#define MAX_EFFECTS      32

/* DMA Budget (bytes per frame during VBlank) */
#define DMA_BUDGET_BYTES 7000   /* ~75% of VBlank time */

/* Feature Flags */
#define DUAL_SCROLL_PLANES  1   /* Use both Plane A and B */
#define LINE_SCROLL_ENABLED 1   /* Per-line scroll effects */
#define SPRITE_LINK_ENABLED 1   /* Use sprite linking */
#define Z80_AUDIO_ENABLED   1   /* Z80 handles audio */

/* Debug Features */
#define DEBUG_ENABLED       0

#endif /* PROFILE_INCLUDED */
