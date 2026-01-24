#include "ui/build_mode.h"
#include "game.h"
#include "resources.h"

// State
static s16 cursorX = 160;
static s16 cursorY = 112;
static u8 cursorBlink = 0;
static BuildItem currentItem = BUILD_ITEM_WALL;

// Constants
#define TILE_SIZE 8
#define GRID_W 40
#define GRID_H 28

// Sprite for cursor (using Player sprite frame 0 or similar for now)
static Sprite *cursorSprite = NULL;

void build_mode_init(void) {
  cursorX = 160;
  cursorY = 112;
  cursorBlink = 0;

  // Force redraw of UI
  // Note: We need to access the static variable.
  // Since buildLastXP is static in this file, we can't access it here unless we
  // move declaration up. I will move the declaration of buildLastXP to top of
  // file (or just set game.playerXP to mismatch?) Actually, I'll just declare
  // it at top.
}
// Moved static variable up
static u32 buildLastXP = 0xFFFFFFFF;

void build_mode_update(void) {
  // 1. Move Cursor
  if (input_isHeld(BUTTON_LEFT))
    cursorX -= 2;
  if (input_isHeld(BUTTON_RIGHT))
    cursorX += 2;
  if (input_isHeld(BUTTON_UP))
    cursorY -= 2;
  if (input_isHeld(BUTTON_DOWN))
    cursorY += 2;

  // Clamp
  if (cursorX < 0)
    cursorX = 0;
  if (cursorX > 320 - 16)
    cursorX = 320 - 16;
  if (cursorY < 0)
    cursorY = 0;
  if (cursorY > 224 - 16)
    cursorY = 224 - 16;

  // 2. Snap to Grid (16x16 metatiles logic?)
  s16 gridX = (cursorX + 8) / 8;
  s16 gridY = (cursorY + 8) / 8;

  // 3. Place Item (Button A)
  if (input_justPressed(BUTTON_A)) {
    if (game.playerXP >= 10) { // Cost 10 XP
      game.playerXP -= 10;

      // Calculate World Coordinates
      s32 worldX = FP_INT(cameraX) + cursorX;
      s32 worldY = FP_INT(cameraY) + cursorY;

      // Calculate Tile Coordinates (Global Map)
      u16 gridX = worldX / 8;
      u16 gridY = worldY / 8;

      // Calculate Plane Coordinates (64x64 Wrap)
      u16 planeX = gridX % 64;
      u16 planeY = gridY % 64;

      // Draw to BG_A (Using 2x2 block for visibility - 16px wall)
      u16 attr =
          TILE_ATTR_FULL(PAL0, TRUE, FALSE, FALSE, 1); // Solid color index 1

      VDP_setTileMapXY(BG_A, attr, planeX, planeY);
      VDP_setTileMapXY(BG_A, attr, (planeX + 1) % 64, planeY);
      VDP_setTileMapXY(BG_A, attr, planeX, (planeY + 1) % 64);
      VDP_setTileMapXY(BG_A, attr, (planeX + 1) % 64, (planeY + 1) % 64);

      // Update Collision Map (Global)
      // Update Collision Map (Global) - Bitwise
      if (gridX < MAP_WIDTH_TILES - 1 && gridY < MAP_HEIGHT_TILES - 1) {
        collisionMap[gridY][gridX >> 3] |= (1 << (gridX & 7));
        collisionMap[gridY][(gridX + 1) >> 3] |= (1 << ((gridX + 1) & 7));
        collisionMap[gridY + 1][gridX >> 3] |= (1 << (gridX & 7));
        collisionMap[gridY + 1][(gridX + 1) >> 3] |= (1 << ((gridX + 1) & 7));
      }
    }
  }

  // 4. Exit (Start handled in main.c, or B to cancel?)
}

void build_mode_draw(void) {
  // Determine Cursor Screen Pos

  // Draw Static UI ONCE (checked via static flag or input change?)
  // Actually, SGDK text layers persist until cleared or overwritten.
  // We can just draw the static text constantly? No, that's the problem.

  // Use a dirty flag for XP update
  static u32 buildLastXP = 0xFFFFFFFF;
  if (game.playerXP != buildLastXP) {
    char buf[16];
    sprintf(buf, "XP: %lu ", game.playerXP); // Space to clear
    VDP_drawTextEx(WINDOW, buf, TILE_ATTR_FULL(PAL0, TRUE, FALSE, FALSE, 0), 1,
                   1, DMA);
    buildLastXP = game.playerXP;

    // Redraw static labels if needed (just to be safe on first frame)
    VDP_drawTextEx(WINDOW, "BUILD MODE",
                   TILE_ATTR_FULL(PAL0, TRUE, FALSE, FALSE, 0), 12, 1, DMA);
    VDP_drawTextEx(WINDOW, "A: PLACE WALL (10XP)",
                   TILE_ATTR_FULL(PAL0, TRUE, FALSE, FALSE, 0), 1, 3, DMA);
  }

  // The static labels "BUILD MODE" and instructions don't change.
  // If we just entered this mode, we should draw them.
  // main.c calls init() when entering.
  // Let's reset buildLastXP in init().

  // Software Cursor (Blink tile?)
  // Or just sprite.
  // Let's rely on main.c to handle SPR_update()

  // Debug cursor (on WINDOW plane to avoid scrolling garbage)
  static s16 lastTx = -1;
  static s16 lastTy = -1;

  s16 tx = (cursorX + 4) / 8;
  s16 ty = (cursorY + 4) / 8;

  // Clamp to valid WINDOW range
  if (ty < 4)
    ty = 4; // Below HUD
  if (ty > 27)
    ty = 27;
  if (tx > 39)
    tx = 39;

  cursorBlink++;

  // Clear previous cursor position if moved
  if (lastTx >= 0 && lastTy >= 0 && (lastTx != tx || lastTy != ty)) {
    VDP_drawTextEx(WINDOW, " ", TILE_ATTR_FULL(PAL0, TRUE, FALSE, FALSE, 0),
                   lastTx, lastTy, DMA);
  }

  // Draw cursor with blink
  if (cursorBlink & 0x10) {
    VDP_drawTextEx(WINDOW, "+", TILE_ATTR_FULL(PAL0, TRUE, FALSE, FALSE, 0), tx,
                   ty, DMA);
  } else {
    VDP_drawTextEx(WINDOW, " ", TILE_ATTR_FULL(PAL0, TRUE, FALSE, FALSE, 0), tx,
                   ty, DMA);
  }

  lastTx = tx;
  lastTy = ty;
}
