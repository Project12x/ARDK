/**
 * EPOCH - Upgrade Menu Implementation
 * Tower-based upgrade shop with text+icon UI
 */

#include "ui/upgrade_menu.h"
#include "constants.h"
#include "engine/entity.h"
#include "game.h"
#include <genesis.h>

// =============================================================================
// GLOBALS
// =============================================================================
UpgradeState upgrades = {0, 0, 0, 0, 0};

static bool menuOpen = FALSE;
static u8 selectedUpgrade = 0;

// Fire rate lookup (frames between shots per level)
static const u8 FIRE_RATE_TABLE[] = {10, 8, 7, 6, 5, 4};

// Damage lookup (per level)
static const u8 DAMAGE_TABLE[] = {1, 1, 2, 2, 3};

// Magnet range lookup (pixels, per level)
static const u8 MAGNET_TABLE[] = {80, 100, 130, 160};

// Upgrade costs
static const u16 UPGRADE_COSTS[] = {UPGRADE_COST_FIRE_RATE, UPGRADE_COST_DAMAGE,
                                    UPGRADE_COST_SPREAD, UPGRADE_COST_FENRIR,
                                    UPGRADE_COST_MAGNET};

// Upgrade names for display
static const char *UPGRADE_NAMES[] = {"FIRE RATE", "DAMAGE", "SPREAD",
                                      "FENRIR ATK", "MAGNET"};

// Forward declaration
static void upgrade_menu_draw(void);

// =============================================================================
// INIT
// =============================================================================
void upgrade_menu_init(void) {
  upgrades.fireRateLevel = 0;
  upgrades.damageLevel = 0;
  upgrades.spreadUnlocked = 0;
  upgrades.fenrirUnlocked = 0;
  upgrades.magnetLevel = 0;
  menuOpen = FALSE;
  selectedUpgrade = 0;
}

// =============================================================================
// MENU STATE
// =============================================================================
bool upgrade_menu_isOpen(void) { return menuOpen; }

void upgrade_menu_open(void) {
  menuOpen = TRUE;
  selectedUpgrade = 0;
  // Draw initial menu
  upgrade_menu_draw();
}

void upgrade_menu_close(void) {
  menuOpen = FALSE;
  // Clear menu area
  VDP_clearTextArea(8, 6, 24, 12);
}

// =============================================================================
// GET CURRENT LEVEL FOR UPGRADE
// =============================================================================
static u8 getUpgradeLevel(u8 type) {
  switch (type) {
  case UPGRADE_FIRE_RATE:
    return upgrades.fireRateLevel;
  case UPGRADE_DAMAGE:
    return upgrades.damageLevel;
  case UPGRADE_SPREAD:
    return upgrades.spreadUnlocked;
  case UPGRADE_FENRIR:
    return upgrades.fenrirUnlocked;
  case UPGRADE_MAGNET:
    return upgrades.magnetLevel;
  default:
    return 0;
  }
}

static u8 getMaxLevel(u8 type) {
  switch (type) {
  case UPGRADE_FIRE_RATE:
    return UPGRADE_MAX_FIRE_RATE;
  case UPGRADE_DAMAGE:
    return UPGRADE_MAX_DAMAGE;
  case UPGRADE_SPREAD:
    return UPGRADE_MAX_SPREAD;
  case UPGRADE_FENRIR:
    return UPGRADE_MAX_FENRIR;
  case UPGRADE_MAGNET:
    return UPGRADE_MAX_MAGNET;
  default:
    return 0;
  }
}

// =============================================================================
// DRAW MENU
// =============================================================================
static void upgrade_menu_draw(void) {
  char buf[32];

  // Header
  VDP_drawText("== UPGRADES ==", 10, 6);

  // XP display
  sprintf(buf, "XP: %lu", game.playerXP);
  VDP_drawText(buf, 10, 7);

  // Upgrade list
  for (u8 i = 0; i < UPGRADE_COUNT; i++) {
    u8 level = getUpgradeLevel(i);
    u8 maxLvl = getMaxLevel(i);
    u16 cost = UPGRADE_COSTS[i];

    // Selector arrow
    const char *arrow = (i == selectedUpgrade) ? ">" : " ";

    // Status: level or MAXED
    if (level >= maxLvl) {
      sprintf(buf, "%s %-10s  MAX", arrow, UPGRADE_NAMES[i]);
    } else {
      sprintf(buf, "%s %-10s %3d", arrow, UPGRADE_NAMES[i], cost);
    }
    VDP_drawText(buf, 9, 9 + i);
  }

  // Instructions
  VDP_drawText("C:BUY  START:EXIT", 9, 16);
}

// =============================================================================
// PURCHASE UPGRADE
// =============================================================================
static bool purchaseUpgrade(u8 type) {
  u8 level = getUpgradeLevel(type);
  u8 maxLvl = getMaxLevel(type);
  u16 cost = UPGRADE_COSTS[type];

  // Check if already maxed
  if (level >= maxLvl)
    return FALSE;

  // Check if enough XP
  if (game.playerXP < cost)
    return FALSE;

  // Deduct XP
  game.playerXP -= cost;

  // Apply upgrade
  switch (type) {
  case UPGRADE_FIRE_RATE:
    upgrades.fireRateLevel++;
    break;
  case UPGRADE_DAMAGE:
    upgrades.damageLevel++;
    break;
  case UPGRADE_SPREAD:
    upgrades.spreadUnlocked = 1;
    break;
  case UPGRADE_FENRIR:
    upgrades.fenrirUnlocked = 1;
    break;
  case UPGRADE_MAGNET:
    upgrades.magnetLevel++;
    break;
  }

  return TRUE;
}

// =============================================================================
// UPDATE (Called every frame when menu is open)
// =============================================================================
void upgrade_menu_update(void) {
  if (!menuOpen)
    return;

  extern InputState input;

  // Navigation
  if (input.pressed & BUTTON_UP) {
    if (selectedUpgrade > 0)
      selectedUpgrade--;
  }
  if (input.pressed & BUTTON_DOWN) {
    if (selectedUpgrade < UPGRADE_COUNT - 1)
      selectedUpgrade++;
  }

  // Purchase
  if (input.pressed & BUTTON_C) {
    purchaseUpgrade(selectedUpgrade);
  }

  // Close menu
  if (input.pressed & BUTTON_START) {
    upgrade_menu_close();
    return;
  }

  // Redraw
  upgrade_menu_draw();
}

// =============================================================================
// STAT GETTERS
// =============================================================================
u8 upgrade_getFireRate(void) { return FIRE_RATE_TABLE[upgrades.fireRateLevel]; }

u8 upgrade_getDamage(void) { return DAMAGE_TABLE[upgrades.damageLevel]; }

u8 upgrade_getMagnetRange(void) { return MAGNET_TABLE[upgrades.magnetLevel]; }
