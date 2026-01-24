/**
 * ARDK - Tech Demo 440 (Optimized)
 * Replicating "Luftoheit" density (440 Sprites, 440 Colors)
 *
 * OPTIMIZATIONS:
 * 1. DMA Clear: Uses DMA_doVRamFill to clear Plane B instantly.
 * 2. Fast Loop: Uses native C operators (>> 16, +) to avoid macro
 * overhead/deprecation.
 * 3. H-Int Safety: Minimal critical sections.
 */

#include "resources.h"
#include <genesis.h>


// =============================================================================
// CONSTANTS & CONFIG
// =============================================================================
#define MAX_ENTITIES 440
#define HW_SPRITE_LIMIT 80
#define SOFT_SPRITE_IDX 1

typedef struct {
  fix16 x, y;
  fix16 vx, vy;
} Entity;

Entity entities[MAX_ENTITIES];
Sprite *hwSprites[HW_SPRITE_LIMIT];
u16 paletteBuffer[224]; // Rainbow colors per scanline

// =============================================================================
// H-INTERRUPT (Rainbow Effect)
// CRITICAL: Must use HINTERRUPT_CALLBACK to generate RTE!
// =============================================================================
HINTERRUPT_CALLBACK HIntHandler() {
  // Raw VDP access for maximum speed
  vu16 *ctrl = (vu16 *)0xC00004;
  vu16 *data = (vu16 *)0xC00000;
  vu16 *hv = (vu16 *)0xC00008;

  // Get V-Counter (upper byte of HV register)
  u16 vcount = *hv >> 8;
  if (vcount >= 224)
    return;

  u16 col = paletteBuffer[vcount];

  // Set CRAM color 0 (background)
  *ctrl = 0xC000;
  *ctrl = 0x0000;
  *data = col;
}

// =============================================================================
// INITIALIZATION
// =============================================================================
void init_palette_rainbow() {
#define RGB_DEF(r, g, b) (((b & 7) << 9) | ((g & 7) << 5) | ((r & 7) << 1))
  for (int i = 0; i < 224; i++) {
    u16 r = (i / 16) % 8;
    u16 g = (i / 8) % 8;
    u16 b = i % 8;
    paletteBuffer[i] = RGB_DEF(r, g, b);
  }
}

void init_entities() {
  SPR_init();

  for (int i = 0; i < MAX_ENTITIES; i++) {
    // Random Start
    entities[i].x = FIX16((random() % 320));
    entities[i].y = FIX16((random() % 224));

    // Random Velocity (ensure non-zero)
    s16 rvx = (random() % 5) - 2;
    s16 rvy = (random() % 5) - 2;
    if (rvx == 0)
      rvx = 1;
    if (rvy == 0)
      rvy = 1;

    entities[i].vx = FIX16(rvx);
    entities[i].vy = FIX16(rvy);

    // Hardware sprites (first 80)
    if (i < HW_SPRITE_LIMIT) {
      // Use resource tile for HW sprites
      // Use native shift instead of macro
      hwSprites[i] =
          SPR_addSprite(&spr_ball, entities[i].x >> 16, entities[i].y >> 16,
                        TILE_ATTR(PAL1, TRUE, FALSE, FALSE));
    }
  }
}

// =============================================================================
// MAIN
// =============================================================================
int main() {
  VDP_setScreenWidth320();

  // Safe Resource Loading (CPU)
  PAL_setPalette(PAL1, pal_ball.data, CPU);

  init_palette_rainbow();
  init_entities();

  // Load Tile for Soft Sprites (Index 1) from resource
  VDP_loadTileSet(spr_ball.animations[0]->frames[0]->tileset, SOFT_SPRITE_IDX,
                  CPU);

  // Soft Sprite Attribute (Palette 1, Priority 1, Tile Index 1)
  const u16 SOFT_ATTR = TILE_ATTR_FULL(PAL1, 1, 0, 0, SOFT_SPRITE_IDX);

  // Enable H-Int for rainbow effect
  SYS_disableInts();
  VDP_setHIntCounter(0);
  SYS_setHIntCallback(HIntHandler);
  VDP_setHInterrupt(TRUE);
  SYS_enableInts();

  char str[32];

  while (TRUE) {
    // 1. DMA CLEAR (Start of Frame)
    // Clear Plane B (NameTable) with DMA Fill.

    // CRITICAL: Protect VDP Setup from H-Int
    SYS_disableInts();
    DMA_doVRamFill(VDP_getPlaneAddress(BG_B, 0, 0), 64 * 32 * 2, 0, 1);
    SYS_enableInts();

    // 2. PROCESS ENTITIES
    SYS_disableInts();

    // Batch 1: Soft Sprites (Plane B writes)
    for (int i = HW_SPRITE_LIMIT; i < MAX_ENTITIES; i++) {
      // Physics (Native Addition)
      entities[i].x += entities[i].vx;
      entities[i].y += entities[i].vy;

      // Bounce (screen bounds 320x224)
      if (entities[i].x < FIX16(0) || entities[i].x > FIX16(312))
        entities[i].vx = -entities[i].vx;
      if (entities[i].y < FIX16(0) || entities[i].y > FIX16(216))
        entities[i].vy = -entities[i].vy;

      // Draw Soft (Direct VDP Write)
      // Native shift: >> 16 to get int, then >> 3 to get tile index
      // Combined: >> 19
      s16 tx = entities[i].x >> 19;
      s16 ty = entities[i].y >> 19;

      if (tx >= 0 && tx < 40 && ty >= 0 && ty < 28) {
        VDP_setTileMapXY(BG_B, SOFT_ATTR, tx, ty);
      }
    }
    SYS_enableInts();

    // Batch 2: HW Sprites (Physics only - SPR_update handles VDP)
    for (int i = 0; i < HW_SPRITE_LIMIT; i++) {
      entities[i].x += entities[i].vx;
      entities[i].y += entities[i].vy;

      // Bounce
      if (entities[i].x < FIX16(0) || entities[i].x > FIX16(312))
        entities[i].vx = -entities[i].vx;
      if (entities[i].y < FIX16(0) || entities[i].y > FIX16(216))
        entities[i].vy = -entities[i].vy;

      // Native shift
      SPR_setPosition(hwSprites[i], entities[i].x >> 16, entities[i].y >> 16);
    }

    // 3. HW SPRITE UPDATE (VDP TRANSFER)
    SYS_disableInts();
    SPR_update();

    // Stats
    sprintf(str, "SPR:%d COL:448 FPS:%ld", MAX_ENTITIES, SYS_getFPS());
    VDP_drawText(str, 1, 1);
    SYS_enableInts();

    VDP_waitVSync();
  }
  return 0;
}
