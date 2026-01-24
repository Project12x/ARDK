# EPOCH Optimization Guide

## Based on Xeno Crisis / Lufthoheit / Earthion Techniques

---

## ✅ Already Implemented

### Object Pooling (Xeno Crisis Method)

- **Entity Pool**: `entities[MAX_ENTITIES]` with `entity_alloc()`/`entity_free()`
- **Sprite Pools**: `enemySprites[MAX_VISIBLE_ENEMIES]`, `projectileSprites[MAX_VISIBLE_PROJECTILES]`
- **No malloc**: All memory is statically allocated at boot

### Dirty Flag Caching (HUD)

- HUD only updates VDP when values change (`lastScore`, `lastHP`, etc.)

---

## ⚠️ Needs Improvement

### 1. DMA Queuing (VBlank Flush)

**Current Issue**: We use `DMA` parameter in `VDP_drawTextEx()` calls, but may not be properly queuing.

**Fix**: Ensure all VDP updates go through SGDK's DMA queue and flush during VBlank:

```c
// SGDK handles this automatically if you use:
// - SPR_update() (queues sprite DMA)
// - SYS_doVBlankProcess() (flushes all queued DMA)

// Avoid: Direct VDP writes during active display
// Prefer: CPU transfer for small updates, DMA queue for large batches
```

### 2. XGM2 Driver (Earthion Method)

**Current**: Using standard XGM driver
**Recommended**: Switch to XGM2 for better Z80 offloading

```c
// In audio_init():
// XGM2_init();  // If available in SGDK 1.90+
```

### 3. Shadow/Highlight Mode (Lufthoheit Trick)

**Not Implemented Yet**

For neon/crystal effects:

```c
// Enable Shadow/Highlight Mode
VDP_setHilightShadow(TRUE);

// Palette 3, Color 14 = Highlight operator (brightens background)
// Palette 3, Color 15 = Shadow operator (darkens background)

// Low Priority sprites = automatically shadowed (darker)
// Use for: glass, smoke, tinted overlays
```

---

## 🔧 Optimization Checklist

| Feature | Status | Technique |
|---------|--------|-----------|
| Object Pooling | ✅ Done | Static arrays, no malloc |
| DMA Queuing | ⚠️ Partial | Verify SYS_doVBlankProcess() timing |
| Shadow/Highlight | ❌ TODO | VDP_setHilightShadow() for neon FX |
| XGM2 Audio | ❌ TODO | Switch from XGM to XGM2 |
| Dirty Flags | ✅ Done | HUD caching implemented |
| Tile Streaming | ❌ TODO | For animated backgrounds |

---

## Performance Rules

1. **Never malloc during gameplay** - all memory pre-allocated
2. **Never write VDP during active display** - queue for VBlank
3. **Minimize per-frame loops** - batch operations, use dirty flags
4. **Z80 handles audio** - keep 68000 free for game logic
5. **Shadow/Highlight is FREE** - use it for visual effects

---

## VBlank Budget (NTSC: 4560 cycles)

| Operation | Approx. Cycles |
|-----------|----------------|
| Sprite Update (80 sprites) | ~2000 |
| BG Scroll | ~100 |
| Palette Update | ~200 |
| Text Update (10 chars) | ~500 |
| **Remaining for DMA** | ~1760 |

Stay under budget to maintain 60fps!

---

## 🚨 CRITICAL: 68000 CPU Math Operations

> **ALWAYS consult this section before writing ANY math code!**
> These costs apply EVERY TIME the operation executes.

### Operation Cycle Costs

| Operation | Cycles | Notes |
|-----------|--------|-------|
| `a + b` | 4-8 | Fast |
| `a - b` | 4-8 | Fast |
| `a << n` (shift) | 4 | **USE THIS** |
| `a >> n` (shift) | 4 | **USE THIS** |
| `a & mask` (AND) | 4 | **USE THIS for mod power-of-2** |
| `a * b` (16-bit) | 38-70 | Avoid in hot paths |
| `a * b` (32-bit) | 70+ | **EXTREMELY EXPENSIVE** |
| `a / b` | 140-170 | **AVOID AT ALL COSTS** |
| `a % b` | 140-170 | **AVOID AT ALL COSTS** |

### 🔥 Hot Path Rules (Code that runs per-entity per-frame)

1. **NEVER use `/` or `%`** - Use shifts and AND masks instead
2. **NEVER multiply by non-power-of-2** - Use lookup tables or shifts
3. **Use 16-bit math** - 32-bit operations are 2x slower
4. **All constants must be power-of-2** for any multiplied/divided value

### Conversion Patterns

```c
// ❌ BAD: Division (140+ cycles)
x = value / 8;

// ✅ GOOD: Shift (4 cycles)
x = value >> 3;  // Divide by 8 = shift right 3

// ❌ BAD: Modulo (140+ cycles)
x = value % 64;

// ✅ GOOD: AND mask (4 cycles)
x = value & 63;  // Mod 64 = AND with 63 (must be power-of-2 minus 1!)

// ❌ BAD: Multiply by non-power-of-2 (70+ cycles)
x = y * 20;

// ✅ GOOD: Shift multiply (4 cycles)
x = y << 5;  // Multiply by 32

// ❌ BAD: Random with modulo
x = random() % 1280;

// ✅ GOOD: Random with AND (approximate but fast)
x = random() & 0x3FF;  // 0-1023, close to 1280 range
```

### Grid/Array Index Calculation

```c
// ❌ BAD: Grid width is 20 (not power of 2)
#define GRID_W 20
index = x + (y * GRID_W);  // 70+ cycle multiply!

// ✅ GOOD: Grid width is 32 (power of 2)
#define GRID_W 32
#define GRID_W_SHIFT 5
index = x + (y << GRID_W_SHIFT);  // 4 cycle shift!
```

### Collision/Hitbox Calculations

```c
// ❌ BAD: Division for half-size
halfW = width / 2;

// ✅ GOOD: Shift for half-size
halfW = width >> 1;

// ❌ BAD: Tile coordinate from pixels
tileX = pixelX / 8;

// ✅ GOOD: Shift for tile coordinate
tileX = pixelX >> 3;  // Divide by 8 = shift right 3
```

### Negative Number Warning

```c
// ⚠️ CAUTION: Right-shift of negative s16 then cast to u16
s16 x = -10;
u16 tile = x >> 3;  // WRONG! Gives garbage due to sign extension

// ✅ CORRECT: Clamp BEFORE shifting
if (x < 0) x = 0;
u16 tile = x >> 3;  // Now safe
```

---

## Power-of-2 Quick Reference

| Power | Value | Shift | AND Mask |
|-------|-------|-------|----------|
| 2^1 | 2 | <<1 >>1 | &1 |
| 2^2 | 4 | <<2 >>2 | &3 |
| 2^3 | 8 | <<3 >>3 | &7 |
| 2^4 | 16 | <<4 >>4 | &15 |
| 2^5 | 32 | <<5 >>5 | &31 |
| 2^6 | 64 | <<6 >>6 | &63 |
| 2^7 | 128 | <<7 >>7 | &127 |
| 2^8 | 256 | <<8 >>8 | &255 |
| 2^9 | 512 | <<9 >>9 | &511 |
| 2^10 | 1024 | <<10 >>10 | &1023 |

---

## ⚡ SGDK Fast Math Functions

Use these instead of raw operations:

```c
// Fast sine (256-entry LUT, returns -255 to +255)
s16 sinFix16(u16 angle);
s16 cosFix16(u16 angle);

// Fast random (LFSR, very fast)
u16 random();  // 0-65535

// Fast absolute value (avoid stdlib abs())
#define FAST_ABS(x) ((x) < 0 ? -(x) : (x))

// Distance approximation (avoid sqrt)
#define MANHATTAN_DIST(dx, dy) (FAST_ABS(dx) + FAST_ABS(dy))
```

---

## 🎯 Checklist Before Committing Code

- [ ] No `/` or `%` operators in hot paths
- [ ] All grid/array dimensions are power-of-2
- [ ] All multiplies use shifts or are pre-computed
- [ ] Negative values clamped before shifting
- [ ] No 32-bit math where 16-bit suffices
- [ ] Random ranges use AND masks, not modulo
- [ ] SPR_ functions use state caching (see below)

---

## 🎮 SGDK Function Call Caching (v0.7.3)

SGDK functions like `SPR_setHFlip`, `SPR_setVisibility` have overhead. **Cache state and only call on change.**

### Pattern: Flip State Caching

```c
// State cache (parallel to sprite array)
static u8 spriteFlipCache[MAX_SPRITES];  // 0=left, 1=right, 0xFF=unset

// In init: set all to 0xFF
spriteFlipCache[i] = 0xFF;

// In update: only call when state changes
u8 newFlip = (entity->vx > 0) ? 1 : ((entity->vx < 0) ? 0 : cache);
if (newFlip != spriteFlipCache[idx] && newFlip != 0xFF) {
  SPR_setHFlip(sprites[idx], newFlip);
  spriteFlipCache[idx] = newFlip;
}

// On release: reset cache
spriteFlipCache[idx] = 0xFF;
```

### Impact

- **Before**: 15+ SPR_setHFlip calls per frame (every enemy every frame)
- **After**: 2-3 calls per frame (only when direction changes)
