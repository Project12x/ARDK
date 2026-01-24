#ifndef PICKUPS_H
#define PICKUPS_H

#include <genesis.h>

void pickups_init(void);
void pickups_spawn(s16 x, s16 y, u8 type);
void pickups_update(void);

// Pickup Types (stored in Entity.type variant)
#define PICKUP_XP_SMALL 0
#define PICKUP_XP_BIG 1
#define PICKUP_HEALTH 2

#endif // PICKUPS_H
