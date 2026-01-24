#include "engine/math_fast.h"

// 32x32 Distance LUT (1KB)
// Stores sqrt(x*x + y*y) for x,y in [0,31]
static u8 DISTANCE_LUT[32][32];

void Math_init(void) {
  // Generate Distance LUT at runtime to save ROM space
  // and avoid giant static array definitions in code.
  // 32*32 = 1024 iterations. Fast enough for init.
  for (int y = 0; y < 32; y++) {
    for (int x = 0; x < 32; x++) {
      // Simple integer sqrt approximation or just use float during init
      // Since this runs once during boot, we can use fix32/float logic if
      // needed But we want to avoid linking heavy float lib if possible. Using
      // basic integer sqrt logic:
      u32 sq = (x * x) + (y * y);

      // Simple integer sqrt
      u32 root = 0;
      u32 bit = 1 << 10; // Start bit (optimized for small numbers)
      while (bit > sq)
        bit >>= 2;

      while (bit != 0) {
        if (sq >= root + bit) {
          sq -= root + bit;
          root = (root >> 1) + bit;
        } else {
          root >>= 1;
        }
        bit >>= 2;
      }
      DISTANCE_LUT[y][x] = (u8)root;
    }
  }
}

u8 Math_getDistance32(s16 dx, s16 dy) {
  // Abs
  if (dx < 0)
    dx = -dx;
  if (dy < 0)
    dy = -dy;

  // Scale down to fit in table (assuming inputs are large world coords)
  // Adjust shift based on usage.
  // If usage is "Close range check", maybe shift by 4 (16px units) or 5 (32px
  // units). Let's assume input is PIXELS. We want to check ranges up to ~512px?
  // 32 * 16 = 512. So shift by 4.
  // User can just pass (val >> 4) themselves?
  // No, helper should be generic.
  // BUT we need to clamp to 31.

  // Implementation: Input is assumed to be "Table Index Units".
  // Callers are responsible for shifting.
  // Wait, that's dangerous. Let's make it accept "Table Indices".

  // CLAMP
  if (dx > 31)
    dx = 31;
  if (dy > 31)
    dy = 31;

  return DISTANCE_LUT[dy][dx];
}
