#include "engine/raster.h"

// =============================================================================
// STATE
// =============================================================================
u8 rasterEnabled = 0;
u8 rasterFrame = 0;

// Line scroll buffer - stores horizontal scroll offset for each scanline
static s16 lineScrollBuffer[224];

// =============================================================================
// H-INT CALLBACK - Called every scanline when enabled
// =============================================================================
static void hIntCallback(void) {
  // Get current scanline
  u16 scanline = VDP_getScanlineCounter();

  // Apply horizontal scroll from buffer
  if (scanline < 224) {
    VDP_setHorizontalScrollLine(BG_B, scanline, &lineScrollBuffer[scanline], 1,
                                DMA_QUEUE);
  }
}

// =============================================================================
// INIT
// =============================================================================
void raster_init(void) {
  rasterEnabled = 0;
  rasterFrame = 0;

  // Initialize scroll buffer to 0
  for (u16 i = 0; i < 224; i++) {
    lineScrollBuffer[i] = 0;
  }

  // Enable line-by-line horizontal scrolling
  VDP_setScrollingMode(HSCROLL_LINE, VSCROLL_PLANE);
}

// =============================================================================
// ENABLE/DISABLE
// =============================================================================
void raster_enable(void) {
  if (!rasterEnabled) {
    rasterEnabled = 1;
    // Set H-Int callback (commented out - using buffer approach instead)
    // SYS_setHIntCallback(hIntCallback);
    // VDP_setHIntCounter(1);  // Trigger every scanline
    // VDP_setHInterrupt(TRUE);
  }
}

void raster_disable(void) {
  if (rasterEnabled) {
    rasterEnabled = 0;
    // VDP_setHInterrupt(FALSE);
    // SYS_setHIntCallback(NULL);

    // Reset scroll buffer
    for (u16 i = 0; i < 224; i++) {
      lineScrollBuffer[i] = 0;
    }
    // Apply reset
    VDP_setHorizontalScrollLine(BG_B, 0, lineScrollBuffer, 224, DMA_QUEUE);
  }
}

// =============================================================================
// UPDATE - Call each frame
// Pre-compute all scanline offsets for the wave effect
// =============================================================================
void raster_update(void) {
  if (!rasterEnabled)
    return;

  rasterFrame += RASTER_WAVE_SPEED;

  // Pre-compute wavy scroll for each scanline
  for (u16 y = 0; y < 224; y++) {
    // Use sine table for smooth wave
    // Different phase per scanline creates the wave effect
    u8 phase = rasterFrame + (y << 1); // y * 2 for tighter waves
    s16 offset =
        sinLUT(phase) >> (7 - RASTER_WAVE_AMPLITUDE); // Scale to amplitude
    lineScrollBuffer[y] = offset;
  }

  // Upload entire scroll buffer via DMA
  VDP_setHorizontalScrollLine(BG_B, 0, lineScrollBuffer, 224, DMA_QUEUE);
}
