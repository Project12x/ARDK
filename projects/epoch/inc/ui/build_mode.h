#ifndef UI_BUILD_MODE_H
#define UI_BUILD_MODE_H

#include <genesis.h>

void build_mode_init(void);
void build_mode_update(void);
void build_mode_draw(void);

// Temporary: Current Item Selection
typedef enum {
  BUILD_ITEM_NONE = 0,
  BUILD_ITEM_WALL = 1, // Blocks enemies
  BUILD_ITEM_MINE = 2  // Explodes
} BuildItem;

#endif // UI_BUILD_MODE_H
