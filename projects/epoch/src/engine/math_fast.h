#ifndef _MATH_FAST_H_
#define _MATH_FAST_H_

#include <genesis.h>

/**
 * @brief Initialize Fast Math tables (Distance LUT).
 * Call this once at engine startup.
 */
void Math_init(void);

/**
 * @brief Fast Random Range (0 to limit-1)
 * Usage: Math_randomRange(10) returns 0..9.
 * Uses multiplication and shift instead of modulo/division.
 *
 * @param limit Upper bound (exclusive)
 * @return u16 Random value
 */
static inline u16 Math_randomRange(u16 limit) {
  // ((u32)random() * limit) >> 16
  // random() returns u16. Product fits in u32.
  // This scales the 0-65535 random value to 0-limit.
  return ((u32)random() * limit) >> 16;
}

/**
 * @brief Approximate Distance using 32x32 Look-Up Table.
 * Result is in grid units (input scaled down by shift).
 *
 * @param dx Delta X
 * @param dy Delta Y
 * @return u8 Approximate distance (0-31+)
 */
u8 Math_getDistance32(s16 dx, s16 dy);

#endif // _MATH_FAST_H_
