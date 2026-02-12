/**
 * EPOCH - Main Entry Point
 * Sega Genesis / Mega Drive
 *
 * "Zelda meets Tower Defense across Time"
 */

#include "engine/entity.h"
#include "engine/profiler.h" // Visual frame profiler
#include "engine/raster.h"   // For H-Int wavy effects
#include "engine/spatial.h"  // For spatial grid
#include "engine/system.h"   // For SYSTEM_run
#include "game.h"
#include "game/audio.h"
#include "game/director.h"
#include "game/enemies.h"
#include "game/fenrir.h"
#include "game/pickups.h"
#include "game/projectiles.h"
#include "ui/build_mode.h"
#include "ui/upgrade_menu.h"
#include <genesis.h>
#include <string.h>

// BGM resource
extern const u8 bgm_test[];

#include "resources.h"

// =============================================================================
// GLOBALS
// =============================================================================
Game game;
InputState input;
u8 collisionMap[MAP_HEIGHT_TILES][MAP_WIDTH_TILES / 8];

// Player sprite handle
static Sprite *playerSprite = NULL;
static Sprite *towerSprite = NULL;

// Fire cooldown
static u8 fireCooldown = 0;

// Forward Declarations
static void tower_spawn(void);

// =============================================================================
// ANIMATION DEFINITIONS
// =============================================================================
// Frames based on original animMap: {2, 1, 0, 1, 2, 3, 4, 3}
static const u8 FRAMES_P_UP[] = {2};
static const u8 FRAMES_P_DOWN[] = {1};
static const u8 FRAMES_P_SIDE[] = {0};    // Left/Right (Left is mirrored)
static const u8 FRAMES_P_DIAG_UP[] = {3}; // Up-Right (Up-Left is mirrored)
static const u8 FRAMES_P_DIAG_DOWN[] = {
    4}; // Down-Right (Down-Left is mirrored)

static const AnimDef ANIM_P_UP = {1, 60, ANIM_LOOP, FRAMES_P_UP};
static const AnimDef ANIM_P_DOWN = {1, 60, ANIM_LOOP, FRAMES_P_DOWN};
static const AnimDef ANIM_P_SIDE = {1, 60, ANIM_LOOP, FRAMES_P_SIDE};
static const AnimDef ANIM_P_DIAG_UP = {1, 60, ANIM_LOOP, FRAMES_P_DIAG_UP};
static const AnimDef ANIM_P_DIAG_DOWN = {1, 60, ANIM_LOOP, FRAMES_P_DIAG_DOWN};

// PLAYER SPRITE CACHING (v0.7.4 - reduce SPR_* calls)
static s16 playerPosXCache = -999;
static s16 playerPosYCache = -999;
static u8 playerFrameCache = 0xFF;
static u8 playerFlipCache = 0xFF;
static u8 playerVisCache = 0xFF; // 0=HIDDEN, 1=VISIBLE, 0xFF=unset

// Main Game Loop

// =============================================================================
// CAMERA / SCROLLING
// =============================================================================
static Map *bgMap = NULL;

// Camera position (top-left of view in world coords, 8.8 fixed-point)
s32 cameraX = 0;
s32 cameraY = 0;

// =============================================================================
// INPUT HANDLING
// =============================================================================
void input_update(void) {
  input.previous = input.current;
  input.current = JOY_readJoypad(JOY_1);
  input.pressed = input.current & ~input.previous;
  input.released = ~input.current & input.previous;
}

bool input_isHeld(u16 button) { return (input.current & button) != 0; }

bool input_justPressed(u16 button) { return (input.pressed & button) != 0; }

bool input_justReleased(u16 button) { return (input.released & button) != 0; }

// =============================================================================
// PLAYER ACTIONS
// =============================================================================
static void player_melee_attack(void) {
  Entity *player = entity_getPlayer();
  if (!(player->flags & ENT_ACTIVE))
    return;

  // Define Hitbox in front of player
  s32 hitX = player->x;
  s32 hitY = player->y;
  s32 range = FP(32); // 32 pixel range

  // Offset based on facing
  switch (playerData.facing) {
  case DIR_UP:
    hitY -= range;
    break;
  case DIR_DOWN:
    hitY += range;
    break;
  case DIR_LEFT:
    hitX -= range;
    break;
  case DIR_RIGHT:
    hitX += range;
    break;
  case DIR_UP_LEFT:
    hitX -= range;
    hitY -= range;
    break;
  case DIR_UP_RIGHT:
    hitX += range;
    hitY -= range;
    break;
  case DIR_DOWN_LEFT:
    hitX -= range;
    hitY += range;
    break;
  case DIR_DOWN_RIGHT:
    hitX += range;
    hitY += range;
    break;
  }

  // Debug Hitbox Logic (Simple Box Check vs Enemies)
  // Range is approx 32x32 centered at hitX, hitY
  s32 halfSize = FP(24); // Generous hit area

  // Debug Visual
  projectile_spawn_visual(FP_INT(hitX), FP_INT(hitY));

  for (u8 i = SLOT_ENEMIES_START; i <= SLOT_ENEMIES_END; i++) {
    Entity *enemy = &entities[i];
    if (enemy->flags & ENT_ACTIVE) {
      if (abs(enemy->x - hitX) < halfSize && abs(enemy->y - hitY) < halfSize) {
        enemy_damage(i, 50); // Massive damage for debug
      }
    }
  }
}

// =============================================================================
// PLAYER UPDATE
// =============================================================================
static void player_spawn(void) {
  s8 slot = entity_alloc(ENT_TYPE_PLAYER);
  if (slot < 0)
    return;

  Entity *player = &entities[slot];
  player->flags = ENT_ACTIVE | ENT_VISIBLE | ENT_SOLID | ENT_FRIENDLY;
  player->x = FP(SCREEN_WIDTH / 2); // Center of screen
  player->y = FP(SCREEN_HEIGHT / 2);
  player->hp = playerData.maxHP;

  // Create sprite
  playerSprite =
      SPR_addSprite(&spr_player, FP_INT(player->x) - (PLAYER_WIDTH / 2),
                    FP_INT(player->y) - (PLAYER_HEIGHT / 2),
                    TILE_ATTR(PAL1, TRUE, FALSE, FALSE));
}

// =============================================================================
// INPUT LOOKUP TABLE (Direction vectors)
// =============================================================================
// Maps joystick state (Lower 4 bits: R L D U) to Normalized Vectors (8.8 Fixed)
// Index: [Right][Left][Down][Up] (bitmask)
// Scale: 256 = 1.0, 181 = 0.707
static const s16 INPUT_VECTORS[16][2] = {
    {0, 0},       // 0000: Neutral
    {0, -256},    // 0001: UP
    {0, 256},     // 0010: DOWN
    {0, 0},       // 0011: U+D (Cancel)
    {-256, 0},    // 0100: LEFT
    {-181, -181}, // 0101: UP+LEFT
    {-181, 181},  // 0110: DOWN+LEFT
    {-256, 0},    // 0111: U+D+L (Left overrides)
    {256, 0},     // 1000: RIGHT
    {181, -181},  // 1001: UP+RIGHT
    {181, 181},   // 1010: DOWN+RIGHT
    {256, 0},     // 1011: U+D+R (Right overrides)
    {0, 0},       // 1100: L+R (Cancel)
    {0, -256},    // 1101: U+L+R (Up overrides)
    {0, 256},     // 1110: D+L+R (Down overrides)
    {0, 0}        // 1111: All (Cancel)
};

// Map input state to Facing Direction (for animations)
static const u8 INPUT_FACING[16] = {
    DIR_DOWN,       // 0: Default
    DIR_UP,         // 1: UP
    DIR_DOWN,       // 2: DOWN
    DIR_DOWN,       // 3: U+D
    DIR_LEFT,       // 4: LEFT
    DIR_UP_LEFT,    // 5: UL
    DIR_DOWN_LEFT,  // 6: DL
    DIR_LEFT,       // 7: L dominant
    DIR_RIGHT,      // 8: RIGHT
    DIR_UP_RIGHT,   // 9: UR
    DIR_DOWN_RIGHT, // 10: DR
    DIR_RIGHT,      // 11: R dominant
    DIR_DOWN,       // 12: LR
    DIR_UP,         // 13: ULR
    DIR_DOWN,       // 14: DLR
    DIR_DOWN        // 15: All
};

static void player_update(void) {
  Entity *player = entity_getPlayer();
  if (!(player->flags & ENT_ACTIVE))
    return;

  // Movement velocity
  // Read D-pad bitmask
  // Bit 0: UP, Bit 1: DOWN, Bit 2: LEFT, Bit 3: RIGHT
  u8 inputState = 0;
  if (input_isHeld(BUTTON_UP))
    inputState |= 0x1;
  if (input_isHeld(BUTTON_DOWN))
    inputState |= 0x2;
  if (input_isHeld(BUTTON_LEFT))
    inputState |= 0x4;
  if (input_isHeld(BUTTON_RIGHT))
    inputState |= 0x8;

  // Apply Movement LUT
  // Note: INPUT_VECTORS contains normalized values (256 or 181)
  // Multiply by Speed and shift by 8 (Fixed Point)
  s16 moveX = (PLAYER_SPEED * INPUT_VECTORS[inputState][0]) >> 8;
  s16 moveY = (PLAYER_SPEED * INPUT_VECTORS[inputState][1]) >> 8;

  // Update facing direction (unless strafe locked)
  if (!playerData.strafeLocked && (moveX != 0 || moveY != 0)) {
    playerData.facing = INPUT_FACING[inputState];
  }

  // Strafe lock (A button)
  playerData.strafeLocked = input_isHeld(BUTTON_A);

  // Dash cooldown countdown
  if (playerData.dashCooldown > 0) {
    playerData.dashCooldown--;
  }

  // Dash (C button) - requires cooldown to be 0
  if (input_justPressed(BUTTON_C) && playerData.dashTimer == 0 &&
      playerData.dashCooldown == 0) {
    playerData.dashTimer = DASH_DURATION;
    playerData.dashCooldown = DASH_COOLDOWN; // Start cooldown immediately
  }

  // Apply dash boost and iframes
  if (playerData.dashTimer > 0) {
    playerData.dashTimer--;
    playerData.invulnTimer = 2; // Maintain iframes during entire dash
    // PERF: Replace (moveX * DASH_SPEED) / PLAYER_SPEED with shift approx
    // Ratio is ~2.67, use 2.5x = (x << 1) + (x >> 1)
    moveX = (moveX << 1) + (moveX >> 1);
    moveY = (moveY << 1) + (moveY >> 1);
  }

  // Apply velocity
  player->vx = moveX;
  player->vy = moveY;

  // Apply velocity & Collision
  s32 nextX = player->x + player->vx;
  s32 nextY = player->y + player->vy;

  // Check X - Pass INTEGER pixel coords (s16 friendly)
  if (!entity_checkTileCollision(player, FP_INT(nextX), FP_INT(player->y))) {
    player->x = nextX;
  }
  // Check Y
  if (!entity_checkTileCollision(player, FP_INT(player->x), FP_INT(nextY))) {
    player->y = nextY;
  }

  // Clamp to map bounds (scrollable world)
  s32 halfW = FP(PLAYER_WIDTH / 2);
  s32 halfH = FP(PLAYER_HEIGHT / 2);

  if (player->x < halfW)
    player->x = halfW;
  if (player->x > FP(MAP_WIDTH) - halfW)
    player->x = FP(MAP_WIDTH) - halfW;
  if (player->y < halfH)
    player->y = halfH;
  if (player->y > FP(MAP_HEIGHT) - halfH)
    player->y = FP(MAP_HEIGHT) - halfH;

  // Update invulnerability
  if (playerData.invulnTimer > 0) {
    playerData.invulnTimer--;
  }

  // Update sprite position (camera-relative) WITH CACHING
  if (playerSprite) {
    s32 screenX = player->x - cameraX;
    s32 screenY = player->y - cameraY;
    s16 drawX = FP_INT(screenX) - (PLAYER_WIDTH / 2);
    s16 drawY = FP_INT(screenY) - (PLAYER_HEIGHT / 2);

    // PERF: Only call SPR_setPosition when position changes
    if (drawX != playerPosXCache || drawY != playerPosYCache) {
      SPR_setPosition(playerSprite, drawX, drawY);
      SPR_setDepth(playerSprite, -FP_INT(player->y));
      playerPosXCache = drawX;
      playerPosYCache = drawY;
    }

    // Select Animation based on Facing
    const AnimDef *targetAnim = &ANIM_P_DOWN; // Default

    switch (playerData.facing) {
    case DIR_UP:
      targetAnim = &ANIM_P_UP;
      break;
    case DIR_DOWN:
      targetAnim = &ANIM_P_DOWN;
      break;
    case DIR_LEFT:
      targetAnim = &ANIM_P_SIDE;
      break;
    case DIR_RIGHT:
      targetAnim = &ANIM_P_SIDE;
      break;
    case DIR_UP_LEFT:
      targetAnim = &ANIM_P_DIAG_UP;
      break;
    case DIR_UP_RIGHT:
      targetAnim = &ANIM_P_DIAG_UP;
      break;
    case DIR_DOWN_LEFT:
      targetAnim = &ANIM_P_DIAG_DOWN;
      break;
    case DIR_DOWN_RIGHT:
      targetAnim = &ANIM_P_DIAG_DOWN;
      break;
    }

    // Play Animation (only restarts if different)
    anim_play(&playerData.animState, targetAnim, FALSE);

    // Update Animation State
    anim_update(&playerData.animState);

    // H-Flip Logic
    u8 flipHost =
        (playerData.facing >= DIR_DOWN_LEFT && playerData.facing <= DIR_UP_LEFT)
            ? 1
            : 0;

    // PERF: Only call SPR_setFrame when frame changes
    u8 currentFrame = anim_getFrame(&playerData.animState);
    if (currentFrame != playerFrameCache) {
      SPR_setFrame(playerSprite, currentFrame);
      playerFrameCache = currentFrame;
    }

    // PERF: Only call SPR_setHFlip when flip state changes
    if (flipHost != playerFlipCache) {
      SPR_setHFlip(playerSprite, flipHost);
      playerFlipCache = flipHost;
    }

    // PERF: Only call SPR_setVisibility when visibility changes
    u8 newVis;
    if (playerData.invulnTimer > 0) {
      newVis = (playerData.invulnTimer & 0x04) ? 1 : 0;
    } else {
      newVis = 1; // Always visible when not invulnerable
    }
    if (newVis != playerVisCache) {
      SPR_setVisibility(playerSprite, newVis ? VISIBLE : HIDDEN);
      playerVisCache = newVis;
    }
  }
}

// =============================================================================
// TOWER SPAWN & UPDATE
// =============================================================================
static void tower_spawn(void) {
  s8 slot = entity_alloc(ENT_TYPE_TOWER_CENTER);
  if (slot < 0)
    return;

  Entity *tower = &entities[slot];
  tower->flags = ENT_ACTIVE | ENT_VISIBLE | ENT_SOLID | ENT_FRIENDLY;
  tower->x = FP(TOWER_X);
  tower->y = FP(TOWER_Y);
  tower->width = FP(50); // Set Hitbox size
  tower->height = FP(50);
  tower->hp = 200;

  // Tower rendered as background tiles instead of sprite (see game_init)
  // towerSprite is no longer used - saves 64 sprite tiles!
  towerSprite = NULL;
}

static void towers_update(void) {
  // Tower is now a background tile, no sprite to update
  // Collision entity still exists and is handled by entity system
}

// =============================================================================
// CAMERA UPDATE (v0.7.5 - Tile-Boundary Scroll Caching)
// =============================================================================
static s16 lastCamX = -1; // Pixel-level cache for VDP scroll
static s16 lastCamY = -1;
static s16 lastTileX = -1; // Tile-level cache for MAP_scrollTo
static s16 lastTileY = -1;

static void camera_update(void) {
  Entity *player = entity_getPlayer();
  if (!(player->flags & ENT_ACTIVE))
    return;

  // Get player screen position (relative to camera)
  s32 playerScreenX = player->x - cameraX;
  s32 playerScreenY = player->y - cameraY;

  // Screen center in fixed-point
  s32 centerX = FP(SCREEN_WIDTH / 2);
  s32 centerY = FP(SCREEN_HEIGHT / 2);
  s32 deadX = FP(CAMERA_DEADZONE_X);
  s32 deadY = FP(CAMERA_DEADZONE_Y);

  // Move camera if player is outside dead zone
  if (playerScreenX < centerX - deadX) {
    cameraX -= (centerX - deadX - playerScreenX) >> 2; // Smooth follow
  } else if (playerScreenX > centerX + deadX) {
    cameraX += (playerScreenX - centerX - deadX) >> 2;
  }

  if (playerScreenY < centerY - deadY) {
    cameraY -= (centerY - deadY - playerScreenY) >> 2;
  } else if (playerScreenY > centerY + deadY) {
    cameraY += (playerScreenY - centerY - deadY) >> 2;
  }

  // Clamp camera to map bounds
  if (cameraX < 0)
    cameraX = 0;
  if (cameraY < 0)
    cameraY = 0;
  if (cameraX > FP(MAP_WIDTH - SCREEN_WIDTH))
    cameraX = FP(MAP_WIDTH - SCREEN_WIDTH);
  if (cameraY > FP(MAP_HEIGHT - SCREEN_HEIGHT))
    cameraY = FP(MAP_HEIGHT - SCREEN_HEIGHT);

  // SCROLL CACHING: Only update when camera position changes
  // Note: MAP_scrollTo needs every-pixel updates for smooth tile streaming
  s16 camXInt = FP_INT(cameraX);
  s16 camYInt = FP_INT(cameraY);

  if (bgMap && (camXInt != lastCamX || camYInt != lastCamY)) {
    MAP_scrollTo(bgMap, camXInt, camYInt);
    VDP_setHorizontalScroll(BG_A, -camXInt);
    VDP_setVerticalScroll(BG_A, -camYInt);
    lastCamX = camXInt;
    lastCamY = camYInt;
  }
}

// =============================================================================
// HUD UPDATE
// =============================================================================
// HUD Caching
static u32 lastScore = 0xFFFFFFFF;
static u16 lastTimerSeconds = 0xFFFF;
static u16 lastWave = 0xFFFF;
static u8 lastEnemyCount = 0xFF;
static u8 lastHP = 0xFF;
static u8 lastWeapon = 0xFF;
static u8 lastDashStatus = 0xFF; // 0=OK, 1=CD

static char scoreStr[32];
static void hud_update(void) {
  // 1. SCORE (Row 1, Left)
  if (game.score != lastScore) {
    VDP_drawTextEx(WINDOW,
                   "SCORE:", TILE_ATTR_FULL(PAL0, TRUE, FALSE, FALSE, 0), 1, 1,
                   DMA);
    uintToStr(game.score, scoreStr, 6);
    VDP_drawTextEx(WINDOW, scoreStr,
                   TILE_ATTR_FULL(PAL0, TRUE, FALSE, FALSE, 0), 7, 1, DMA);
    lastScore = game.score;
  }

  // 2. TIME (Row 1, Right)
  u16 seconds = game.siegeTimer / 60;
  if (seconds != lastTimerSeconds) {
    u16 mins = seconds / 60;
    u16 secs = seconds % 60;

    VDP_drawTextEx(WINDOW, "TIME ", TILE_ATTR_FULL(PAL0, TRUE, FALSE, FALSE, 0),
                   28, 1, DMA);

    // Mins
    uintToStr(mins, scoreStr, 2);
    // uintToStr pads with spaces, replace space with 0 if needed or manual
    // logic
    if (mins < 10) {
      scoreStr[0] = '0';
      scoreStr[1] = (char)('0' + mins);
      scoreStr[2] = 0;
    }
    VDP_drawTextEx(WINDOW, scoreStr,
                   TILE_ATTR_FULL(PAL0, TRUE, FALSE, FALSE, 0), 33, 1, DMA);

    VDP_drawTextEx(WINDOW, ":", TILE_ATTR_FULL(PAL0, TRUE, FALSE, FALSE, 0), 35,
                   1, DMA);

    // Secs
    if (secs < 10) {
      scoreStr[0] = '0';
      scoreStr[1] = (char)('0' + secs);
      scoreStr[2] = 0;
    } else {
      uintToStr(secs, scoreStr, 2);
    }
    VDP_drawTextEx(WINDOW, scoreStr,
                   TILE_ATTR_FULL(PAL0, TRUE, FALSE, FALSE, 0), 36, 1, DMA);

    lastTimerSeconds = seconds;
  }

  // 3. WAVE & ENEMY (Row 2, Left)
  if (director.waveNumber != lastWave) {
    VDP_drawTextEx(WINDOW, "WAVE ", TILE_ATTR_FULL(PAL0, TRUE, FALSE, FALSE, 0),
                   1, 2, DMA);
    uintToStr(director.waveNumber, scoreStr, 1);
    VDP_drawTextEx(WINDOW, scoreStr,
                   TILE_ATTR_FULL(PAL0, TRUE, FALSE, FALSE, 0), 6, 2, DMA);
    lastWave = director.waveNumber;
  }

  // Active Enemy Count - Use cached count for performance
  u8 enemyCount = director_getLiveEnemyCount();

  if (enemyCount != lastEnemyCount) {
    VDP_drawTextEx(WINDOW, "E:", TILE_ATTR_FULL(PAL0, TRUE, FALSE, FALSE, 0),
                   10, 2, DMA);
    uintToStr(enemyCount, scoreStr, 2);
    VDP_drawTextEx(WINDOW, scoreStr,
                   TILE_ATTR_FULL(PAL0, TRUE, FALSE, FALSE, 0), 12, 2, DMA);
    lastEnemyCount = enemyCount;
  }

  // 4. HP BAR (Row 2, Center)
  if (playerData.currentHP != lastHP) {
    u8 hpPercent = (playerData.currentHP * 10) / playerData.maxHP;
    char hpBar[14];
    hpBar[0] = '[';
    for (u8 i = 0; i < 10; i++) {
      hpBar[1 + i] = (i < hpPercent) ? '=' : '-';
    }
    hpBar[11] = ']';
    hpBar[12] = '\0';
    VDP_drawTextEx(WINDOW, "HP", TILE_ATTR_FULL(PAL0, TRUE, FALSE, FALSE, 0),
                   16, 2, DMA);
    VDP_drawTextEx(WINDOW, hpBar, TILE_ATTR_FULL(PAL0, TRUE, FALSE, FALSE, 0),
                   19, 2, DMA);
    lastHP = playerData.currentHP;
  }

  // 5. WEAPON (Row 1, Center)
  if (playerData.weaponType != lastWeapon) {
    static const char *weaponNames[] = {"EMIT", "SPRD", "HELIX"};
    VDP_drawTextEx(WINDOW, weaponNames[playerData.weaponType % 3],
                   TILE_ATTR_FULL(PAL0, TRUE, FALSE, FALSE, 0), 18, 1, DMA);
    lastWeapon = playerData.weaponType;
  }

  // 6. DASH (Row 2, Right)
  u8 currentDashStatus = (playerData.dashCooldown > 0) ? 1 : 0;
  if (currentDashStatus != lastDashStatus) {
    if (currentDashStatus) {
      VDP_drawTextEx(WINDOW, "DASH---",
                     TILE_ATTR_FULL(PAL0, TRUE, FALSE, FALSE, 0), 32, 2, DMA);
    } else {
      VDP_drawTextEx(WINDOW, "DASH OK",
                     TILE_ATTR_FULL(PAL0, TRUE, FALSE, FALSE, 0), 32, 2, DMA);
    }
    lastDashStatus = currentDashStatus;
  }

  // 7. TOWER ARROW INDICATOR (Dynamic on Window Plane)
  // We must track previous position to clear it, otherwise it leaves trails.
  static u8 lastAx = 0;
  static u8 lastAy = 0;
  static bool wasArrowVisible = FALSE;

  Entity *player = entity_getPlayer();
  if (player->flags & ENT_ACTIVE) {
    s32 towerScreenX = FP(TOWER_X) - cameraX;
    s32 towerScreenY = FP(TOWER_Y) - cameraY;
    s16 tsx = FP_INT(towerScreenX);
    s16 tsy = FP_INT(towerScreenY);

    // Check if tower is off-screen
    if (tsx < 0 || tsx > SCREEN_WIDTH || tsy < 0 || tsy > SCREEN_HEIGHT) {
      char arrow[2] = {0, 0};

      // Clamp Logic
      s16 clampedX = tsx;
      s16 clampedY = tsy;
      if (clampedX < 0)
        clampedX = 0;
      if (clampedX > SCREEN_WIDTH)
        clampedX = SCREEN_WIDTH;
      if (clampedY < 0)
        clampedY = 0;
      if (clampedY > SCREEN_HEIGHT)
        clampedY = SCREEN_HEIGHT;

      // Convert to Window Tile Coords
      u8 ax = clampedX / 8;
      u8 ay = clampedY / 8;

      // Bounds Checking for Text
      if (ax > 38)
        ax = 38;
      if (ay > 26)
        ay = 26;
      if (ay < 5)
        ay = 5; // Keep below HUD (Window Height 4 + 1 padding)

      // Direction Logic
      if (tsx < 0)
        arrow[0] = '<';
      else if (tsx > SCREEN_WIDTH)
        arrow[0] = '>';
      else if (tsy < 0)
        arrow[0] = '^';
      else if (tsy > SCREEN_HEIGHT)
        arrow[0] = 'v';

      if (arrow[0]) {
        // If position changed, clear old pos
        if (wasArrowVisible && (ax != lastAx || ay != lastAy)) {
          VDP_drawTextEx(WINDOW, " ",
                         TILE_ATTR_FULL(PAL0, TRUE, FALSE, FALSE, 0), lastAx,
                         lastAy, DMA);
        }

        // Draw New (if changed or first time)
        if (!wasArrowVisible || ax != lastAx || ay != lastAy) {
          VDP_drawTextEx(WINDOW, arrow,
                         TILE_ATTR_FULL(PAL0, TRUE, FALSE, FALSE, 0), ax, ay,
                         DMA);
          lastAx = ax;
          lastAy = ay;
          wasArrowVisible = TRUE;
        }
      }
    } else {
      // Tower IS on screen. Clear arrow if it was visible.
      if (wasArrowVisible) {
        VDP_drawTextEx(WINDOW, " ", TILE_ATTR_FULL(PAL0, TRUE, FALSE, FALSE, 0),
                       lastAx, lastAy, DMA);
        wasArrowVisible = FALSE;
      }
    }
  }
}

// =============================================================================
// GAME STATE
// =============================================================================
void game_init(void) {
  // Release player/tower sprites before re-init (prevents ghost sprites on restart)
  if (playerSprite) {
    SPR_releaseSprite(playerSprite);
    playerSprite = NULL;
  }
  if (towerSprite) {
    SPR_releaseSprite(towerSprite);
    towerSprite = NULL;
  }

  audio_init();
  // Init modules
  entity_initPool();
  enemies_init();
  projectiles_init();
  fenrir_init();

  // Reset sprite caches (force full update on new sprites)
  playerPosXCache = -999;
  playerPosYCache = -999;
  playerFrameCache = 0xFF;
  playerFlipCache = 0xFF;
  playerVisCache = 0xFF;

  // Reset HUD Caching
  lastScore = 0xFFFFFFFF;
  lastTimerSeconds = 0xFFFF;
  lastWave = 0xFFFF;
  lastEnemyCount = 0xFF;
  lastHP = 0xFF;
  lastWeapon = 0xFF;
  lastDashStatus = 0xFF;

  // Clear Collision Map (0 = Walkable, 1 = Solid)
  memset(collisionMap, 0, sizeof(collisionMap));

  // Reset Game Struct
  memset(&game, 0, sizeof(Game));
  game.state = STATE_SIEGE; // Start in SIEGE for immediate gameplay
  game.currentZone = ZONE_TOWER;
  game.siegeTimer = SIEGE_DURATION_FRAMES;
  game.flickerOffset = 0;
  game.score = 0;

  // Init Player Data
  memset(&playerData, 0, sizeof(PlayerData));
  playerData.maxHP = 100;
  playerData.currentHP = 100;
  playerData.weaponType = WEAPON_EMITTER;
  playerData.weaponLevel = 0;
  playerData.fireRate = 10; // 6 shots/sec
  playerData.fireCooldown = 0;
  playerData.facing = DIR_DOWN; // Default facing

  // Init Companion Data
  memset(&fenrirData, 0, sizeof(FenrirData));
  fenrirData.mode = 0; // Follow

  // Re-spawn essential entities
  player_spawn();
  tower_spawn();

  // Draw tower to background layer - DISABLED (causes garbage)
  // TODO: Investigate alternative tower rendering approach
  // u16 towerTileX = (TOWER_X - 32) / 8;
  // u16 towerTileY = (TOWER_Y - 32) / 8;
  // VDP_drawImageEx(
  //     BG_B, &img_tower,
  //     TILE_ATTR_FULL(PAL3, FALSE, FALSE, FALSE, TILE_USER_INDEX + 400),
  //     towerTileX, towerTileY, FALSE, CPU);

  // Spawn Fenrir companion (offset from player)
  Entity *pSpawn = entity_getPlayer();
  if (pSpawn->flags & ENT_ACTIVE) {
    fenrir_spawn(pSpawn->x + FP(32), pSpawn->y + FP(32));
  }

  // Initialize Director (handles wave spawning)
  director_init();

  // Camera Logic Init
  Entity *player = entity_getPlayer();
  if (player->flags & ENT_ACTIVE) {
    cameraX = player->x - FP(SCREEN_WIDTH / 2);
    cameraY = player->y - FP(SCREEN_HEIGHT / 2);
  }
}

static void update_siege(void) {
  // =========================================================================
  // UPGRADE MENU - Pauses gameplay
  // =========================================================================
  if (upgrade_menu_isOpen()) {
    upgrade_menu_update();
    return; // Skip rest of update while menu is open
  }

  // Check for tower proximity + C button to open upgrade menu
  Entity *player = entity_getPlayer();
  if (player->flags & ENT_ACTIVE) {
    s16 px = FP_INT(player->x);
    s16 py = FP_INT(player->y);
    s16 dx = px - TOWER_X;
    s16 dy = py - TOWER_Y;
    if (dx < 0)
      dx = -dx;
    if (dy < 0)
      dy = -dy;

    // Within tower range + C pressed = open menu
    if ((dx + dy) < TOWER_INTERACT_RANGE && input_justPressed(BUTTON_C)) {
      upgrade_menu_open();
      return;
    }
  }

  // =========================================================================
  // NORMAL SIEGE LOGIC
  // =========================================================================
  if (game.siegeTimer > 0) {
    game.siegeTimer--;
    if (game.siegeTimer == 0) {
      game.gateOpen = TRUE;
    }
  }

  // Regenerate heat
  if (game.heat < HEAT_MAX) {
    game.heat++;
  }

  // Update player (PROFILED)
  PROF_PLAYER_START();
  player_update();
  PROF_PLAYER_END();

  // Update camera (PROFILED)
  PROF_CAMERA_START();
  camera_update();
  PROF_CAMERA_END();

  // Handle Combat Inputs
  if (fireCooldown > 0) {
    fireCooldown--;
  }

  // BUTTON A: Strafe Lock AND Fire (Primary)
  // Strafe lock is handled in player_update, but we check firing here
  if (input_isHeld(BUTTON_A) && fireCooldown == 0) {
    Entity *player = entity_getPlayer();
    if (player->flags & ENT_ACTIVE) {
      // Get direction offsets based on facing
      s8 dx = 0, dy = 0;
      switch (playerData.facing) {
      case DIR_UP:
        dy = -1;
        break;
      case DIR_DOWN:
        dy = 1;
        break;
      case DIR_LEFT:
        dx = -1;
        break;
      case DIR_RIGHT:
        dx = 1;
        break;
      case DIR_UP_LEFT:
        dx = -1;
        dy = -1;
        break;
      case DIR_UP_RIGHT:
        dx = 1;
        dy = -1;
        break;
      case DIR_DOWN_LEFT:
        dx = -1;
        dy = 1;
        break;
      case DIR_DOWN_RIGHT:
        dx = 1;
        dy = 1;
        break;
      }
      projectile_spawn(FP_INT(player->x), FP_INT(player->y), dx, dy);
      fireCooldown = upgrade_getFireRate(); // Uses upgrade level
    }
  }

  // BUTTON B: Secondary Attack (Debug Melee Cone)
  if (input_justPressed(BUTTON_B)) {
    player_melee_attack();
  }

  // Update Subsystems (with profiler markers + SRAM recording)
  PROF_DIRECTOR_START();
  director_update(); // Wave spawning
  PROF_DIRECTOR_END();

  PROF_ENEMIES_START();
  enemies_update();
  PROF_ENEMIES_END();

  PROF_PROJECTILES_START();
  projectiles_update();
  PROF_PROJECTILES_END();

  PROF_FENRIR_START();
  fenrir_update();
  PROF_FENRIR_END();

  PROF_PICKUPS_START();
  towers_update();
  pickups_update();
  PROF_PICKUPS_END();

  // Check pickup collisions (player touching pickups)
  // 'player' already retrieved for tower proximity check above
  if (player->flags & ENT_ACTIVE) {
    // Pickup collection handled in pickups_update()

    // Enemy→Player collision damage (if not invulnerable)
    // OPTIMIZED: Use spatial grid instead of full enemy loop
    if (playerData.invulnTimer == 0) {
      u8 cellX = (FP_INT(player->x)) >> SPATIAL_CELL_SHIFT;
      u8 cellY = (FP_INT(player->y)) >> SPATIAL_CELL_SHIFT;

      // Clamp cell coords
      if (cellX >= SPATIAL_GRID_W)
        cellX = SPATIAL_GRID_W - 1;
      if (cellY >= SPATIAL_GRID_H)
        cellY = SPATIAL_GRID_H - 1;

      // Check 9 cells around player
      bool hit = FALSE;
      for (s8 dy = -1; dy <= 1 && !hit; dy++) {
        for (s8 dx = -1; dx <= 1 && !hit; dx++) {
          s8 nx = (s8)cellX + dx;
          s8 ny = (s8)cellY + dy;

          if (nx < 0 || nx >= SPATIAL_GRID_W || ny < 0 || ny >= SPATIAL_GRID_H)
            continue;

          u16 cellIdx = nx + (ny << SPATIAL_GRID_W_SHIFT);
          u8 slot = spatial_getFirstInCell(cellIdx);

          while (slot != SPATIAL_NULL && !hit) {
            Entity *enemy = &entities[slot];
            if ((enemy->flags & ENT_ACTIVE) && (enemy->flags & ENT_ENEMY)) {
              // PERF: Use 16-bit pixel math instead of 32-bit FP
              s16 edx = (s16)(player->x >> 8) - (s16)(enemy->x >> 8);
              s16 edy = (s16)(player->y >> 8) - (s16)(enemy->y >> 8);
              if (edx < 0)
                edx = -edx;
              if (edy < 0)
                edy = -edy;

              // Collision radius: 20 pixels (now in pixel space, not FP)
              if (edx < 20 && edy < 20) {
                u8 damage = 10;
                if (playerData.currentHP > damage) {
                  playerData.currentHP -= damage;
                } else {
                  playerData.currentHP = 0;
                  game.state = STATE_GAMEOVER;
                  return;
                }
                playerData.invulnTimer = 60;
                hit = TRUE;
              }
            }
            slot = spatialGrid.nextEntity[slot];
          }
        }
      }
    }
  }

  hud_update();
}

static void update_expedition(void) {
  player_update();
  camera_update(); // Camera should work here too
  // TODO: Fenrir, NPCs, zone transitions
}

static void update_town(void) {
  player_update();
  camera_update();
  // TODO: NPC interaction, dialogue
}

void game_changeState(GameState newState) {
  game.prevState = game.state;
  game.state = newState;
}

void game_update(void) {
  game.frameCount++;
  input_update();
  audio_update();  // Tick SFX cooldowns
  spatial_clear(); // Clear spatial grid for collision optimization
  game.flickerOffset++;

  // Pause toggle
  if (input_justPressed(BUTTON_START)) {
    if (game.state == STATE_PAUSED) {
      game.state = game.prevState;
      // Clear any build mode text artifacts from BG_A
      VDP_clearPlane(BG_A, TRUE);
    } else if (game.state == STATE_SIEGE || game.state == STATE_EXPEDITION) {
      game.prevState = game.state;
      game.state = STATE_PAUSED;
      build_mode_init();
    }
  }

  // =========================================================================
  // STATE MACHINE
  // =========================================================================
  switch (game.state) {
  case STATE_TITLE:
    VDP_drawText("NEON SURVIVORS", 12, 10);
    // Blink effect
    if ((game.frameCount % 60) < 30) {
      VDP_drawText("           ", 13, 16); // Blink off
    } else {
      VDP_drawText("PRESS START", 13, 16); // Blink on
    }

    if (input_justPressed(BUTTON_START)) {
      // Transition to GAME
      VDP_clearPlane(BG_A, TRUE);
      game_init(); // Reset game data

      // Ensure we don't re-init audio/director redundantly if game_init does it
      // generic But game_init logic clears entities, so it's good.
      game.state =
          STATE_SIEGE; // Changed to STATE_SIEGE as STATE_GAME is not defined

      // Seed RNG based on frame count
      setRandomSeed(game.frameCount);
    }
    break;

  case STATE_SIEGE:
    update_siege();
    break;

  case STATE_EXPEDITION:
    update_expedition();
    break;

  case STATE_TOWN:
    update_town();
    break;

  case STATE_PAUSED:
    build_mode_update();
    build_mode_draw();
    break;

  case STATE_LEVELUP:
    break;

  case STATE_GAMEOVER: {
    // Draw game over screen ONCE (cached)
    static bool gameOverDrawn = FALSE;
    if (!gameOverDrawn) {
      // Expand window to full screen so text is fixed on screen
      VDP_setWindowVPos(FALSE, 28);

      // Draw Game Over screen on WINDOW plane (screen-fixed)
      VDP_drawTextEx(WINDOW, "================",
                     TILE_ATTR_FULL(PAL0, TRUE, FALSE, FALSE, 0), 12, 10, CPU);
      VDP_drawTextEx(WINDOW, "   GAME  OVER   ",
                     TILE_ATTR_FULL(PAL0, TRUE, FALSE, FALSE, 0), 12, 12, CPU);
      VDP_drawTextEx(WINDOW, "================",
                     TILE_ATTR_FULL(PAL0, TRUE, FALSE, FALSE, 0), 12, 14, CPU);

      // Show final score
      sprintf(scoreStr, "SCORE: %lu", game.score);
      VDP_drawTextEx(WINDOW, scoreStr,
                     TILE_ATTR_FULL(PAL0, TRUE, FALSE, FALSE, 0), 14, 16, CPU);
      sprintf(scoreStr, "WAVE: %u", director.waveNumber);
      VDP_drawTextEx(WINDOW, scoreStr,
                     TILE_ATTR_FULL(PAL0, TRUE, FALSE, FALSE, 0), 15, 17, CPU);

      VDP_drawTextEx(WINDOW, "PRESS START",
                     TILE_ATTR_FULL(PAL0, TRUE, FALSE, FALSE, 0), 14, 20, CPU);
      gameOverDrawn = TRUE;
    }

    if (input_justPressed(BUTTON_START)) {
      VDP_clearPlane(WINDOW, TRUE);      // Clear game over text
      VDP_setWindowVPos(FALSE, 4);       // Restore HUD-only window
      gameOverDrawn = FALSE;
      game.state = STATE_TITLE;
    }
    break;
  }
  }

  // End frame profiling (flushes to SRAM periodically)
  debug_endFrame();
}

// =============================================================================
// MAIN
// =============================================================================
// =============================================================================
// ENGINE CALLBACKS
// =============================================================================

/**
 * @brief Initialize game-specific resources and state.
 *
 * Called once by SYSTEM_init().
 * Handles palette loading, tile generation, map creation, and initial entity
 * spawning.
 */
static void epoch_init(void) {
  // Initialize SRAM debug logger
  debug_init();

  // 1. VDP Setup (Game Specific)
  // SYSTEM_init handles resolution/planes/window-pos

  // Load palettes (Use CPU to ensure synchronous load)
  PAL_setPalette(PAL0, pal_bg.data, CPU);
  PAL_setPalette(PAL1, pal_player.data, CPU);
  PAL_setPalette(PAL2, pal_enemy.data, CPU);
  PAL_setPalette(PAL3, pal_tower.data, CPU);

  // Enable Shadow/Highlight mode for neon FX (Lufthoheit trick)
  VDP_setHilightShadow(TRUE);
  VDP_setBackgroundColor(0);
  PAL_setColor(0, 0x0000); // Back to Black

  // Manually Load Tileset to guarantee VRAM data
  u16 tileIndex = TILE_USER_INDEX + 16; // Offset slightly to be safe
  VDP_loadTileSet(&bg_tileset, tileIndex, CPU);

  // Draw background (Seamless Tiling via MAP Engine)
  bgMap = MAP_create(&map_background, BG_B,
                     TILE_ATTR_FULL(PAL0, FALSE, FALSE, FALSE, tileIndex));
  MAP_scrollTo(bgMap, FP_INT(cameraX), FP_INT(cameraY));

  // Init Sprites - FULL GAME RESTORED
  SPR_init();
  game_init();
  upgrade_menu_init(); // Initialize upgrade shop system
  enemy_spawn_at(entity_getPlayer()->x + FP(60), entity_getPlayer()->y);

  // H-Int raster wavy effect - DISABLED (causes slowdown due to 224 iter/frame)
  // TODO: Optimize with sparser updates or fixed amplitude
  // raster_init();
  // raster_enable();

  // Start background music - DISABLED FOR PERFORMANCE TEST
  // XGM2_play(bgm_test);

  VDP_clearPlane(BG_A, TRUE);
}

/**
 * @brief Main game update loop.
 *
 * Called every frame by SYSTEM_run().
 * Delegates to game_update() which handles state machine, entities, and input.
 */
static void epoch_update(void) {
  game_update();
  // raster_update(); // DISABLED - wavy effect for water parallax only
}

// =============================================================================
// MAIN
// =============================================================================
int main(bool hardReset) {
  (void)hardReset;

  // Define Game
  const GameCallbacks epochGame = {.init = epoch_init,
                                   .update = epoch_update,
                                   .draw = NULL,
                                   .joyEvent = NULL};

  // Init Engine
  SYSTEM_init();

  // Run Game
  SYSTEM_run(&epochGame);

  return 0;
}
