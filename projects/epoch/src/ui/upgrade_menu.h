/**
 * EPOCH - Upgrade Menu Header
 * Tower-based upgrade shop system
 */

#ifndef _UPGRADE_MENU_H_
#define _UPGRADE_MENU_H_

#include <genesis.h>

// Upgrade levels (stored in playerData or separate)
typedef struct {
  u8 fireRateLevel;  // 0-5
  u8 damageLevel;    // 0-4
  u8 spreadUnlocked; // 0 or 1
  u8 fenrirUnlocked; // 0 or 1
  u8 magnetLevel;    // 0-3
} UpgradeState;

extern UpgradeState upgrades;

// Menu control
void upgrade_menu_init(void);
bool upgrade_menu_isOpen(void);
void upgrade_menu_open(void);
void upgrade_menu_close(void);
void upgrade_menu_update(void); // Call every frame when open

// Get current stats based on upgrades
u8 upgrade_getFireRate(void);    // Returns frames between shots
u8 upgrade_getDamage(void);      // Returns damage per projectile
u8 upgrade_getMagnetRange(void); // Returns magnet range in pixels

#endif // _UPGRADE_MENU_H_
