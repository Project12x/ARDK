#include "engine/debug_sram.h"

#if DEBUG_SRAM_ENABLED

// =============================================================================
// SRAM DEBUG LOGGER IMPLEMENTATION
// =============================================================================
// Uses VDP V-counter to measure time between function calls.
// One scanline = ~63.5 CPU cycles @ 7.67MHz = ~8.28 microseconds
// Full frame = 262 scanlines (NTSC) or 312 (PAL)
// We have ~224 visible + 38 VBlank = 262 total
// Budget for 60fps: ~224 scanlines of "active" time before VBlank
// =============================================================================

// Magic value to verify valid debug data
#define DEBUG_MAGIC 0x44454247 // "DEBG"

// Flush to SRAM every N frames (60 = once per second)
#define FLUSH_INTERVAL 60

// Global debug data
DebugSRAMData debugData;

// Timing state
u16 dbg_startLine = 0;
static u16 frameStartLine = 0;
static u16 flushCounter = 0;

// Accumulator for averaging (resets on flush)
static u32 accPlayerLines = 0;
static u32 accCameraLines = 0;
static u32 accDirectorLines = 0;
static u32 accEnemiesLines = 0;
static u32 accProjectilesLines = 0;
static u32 accFenrirLines = 0;
static u32 accPickupsLines = 0;
static u32 accSprUpdateLines = 0;
static u32 accFramesInPeriod = 0;

// =============================================================================
// VDP V-COUNTER ACCESS
// =============================================================================
// The VDP V-counter at 0xC00008 gives current scanline (0-261 NTSC)
// We read bits 0-7 for the low byte of the scanline number
static inline u16 getVCounter(void) {
  // VDP V-counter port
  volatile u8 *vcounter = (volatile u8 *)0xC00008;
  return *vcounter;
}

// =============================================================================
// INITIALIZATION
// =============================================================================
void debug_init(void) {
  // Clear RAM structure
  memset(&debugData, 0, sizeof(debugData));
  debugData.magic = DEBUG_MAGIC;

  // Reset accumulators
  accPlayerLines = 0;
  accCameraLines = 0;
  accDirectorLines = 0;
  accEnemiesLines = 0;
  accProjectilesLines = 0;
  accFenrirLines = 0;
  accPickupsLines = 0;
  accSprUpdateLines = 0;
  accFramesInPeriod = 0;
  flushCounter = 0;

  // IMMEDIATELY write to SRAM to force file creation
  debug_flushToSRAM();
}

// =============================================================================
// TIMING API
// =============================================================================
void debug_startTimer(void) { dbg_startLine = getVCounter(); }

u16 debug_stopTimer(void) {
  u16 endLine = getVCounter();
  // Handle wrap-around (V-counter resets at ~262)
  if (endLine >= dbg_startLine) {
    return endLine - dbg_startLine;
  } else {
    // Wrapped around VBlank
    return (262 - dbg_startLine) + endLine;
  }
}

// =============================================================================
// RECORDING API
// =============================================================================
void debug_recordPlayer(u16 lines) {
  accPlayerLines += lines;
  // Update peak
  if (lines > debugData.playerLines) {
    debugData.playerLines = lines;
  }
}

void debug_recordCamera(u16 lines) { accCameraLines += lines; }

void debug_recordDirector(u16 lines) { accDirectorLines += lines; }

void debug_recordEnemies(u16 lines) {
  accEnemiesLines += lines;
  if (lines > debugData.peakEnemiesLines) {
    debugData.peakEnemiesLines = lines;
  }
}

void debug_recordProjectiles(u16 lines) {
  accProjectilesLines += lines;
  if (lines > debugData.peakProjLines) {
    debugData.peakProjLines = lines;
  }
}

void debug_recordFenrir(u16 lines) { accFenrirLines += lines; }

void debug_recordPickups(u16 lines) { accPickupsLines += lines; }

void debug_recordSprUpdate(u16 lines) {
  accSprUpdateLines += lines;
  if (lines > debugData.peakSprLines) {
    debugData.peakSprLines = lines;
  }
}

void debug_recordEntityCounts(u8 enemies, u8 projectiles, u8 sprites) {
  debugData.activeEnemies = enemies;
  debugData.activeProjectiles = projectiles;
  debugData.visibleSprites = sprites;
}

// =============================================================================
// FRAME END
// =============================================================================
void debug_endFrame(void) {
  debugData.totalFrames++;
  accFramesInPeriod++;

  // Calculate total frame time
  u16 frameEndLine = getVCounter();
  u16 frameLines;
  if (frameEndLine >= frameStartLine) {
    frameLines = frameEndLine - frameStartLine;
  } else {
    frameLines = (262 - frameStartLine) + frameEndLine;
  }

  // Record in history ring buffer
  debugData.frameHistory[debugData.historyIndex] = frameLines;
  debugData.historyIndex = (debugData.historyIndex + 1) & 31;

  // Check for slow frame (>224 scanlines = missed VBlank)
  if (frameLines > 224) {
    debugData.slowFrames++;
  }

  // Update peak
  if (frameLines > debugData.peakFrameLines) {
    debugData.peakFrameLines = frameLines;
  }

  // Reset frame start for next iteration
  frameStartLine = getVCounter();

  // Periodic flush to SRAM
  flushCounter++;
  if (flushCounter >= FLUSH_INTERVAL) {
    // Calculate averages
    if (accFramesInPeriod > 0) {
      debugData.playerLines = accPlayerLines / accFramesInPeriod;
      debugData.cameraLines = accCameraLines / accFramesInPeriod;
      debugData.directorLines = accDirectorLines / accFramesInPeriod;
      debugData.enemiesLines = accEnemiesLines / accFramesInPeriod;
      debugData.projectilesLines = accProjectilesLines / accFramesInPeriod;
      debugData.fenrirLines = accFenrirLines / accFramesInPeriod;
      debugData.pickupsLines = accPickupsLines / accFramesInPeriod;
      debugData.sprUpdateLines = accSprUpdateLines / accFramesInPeriod;
    }

    debug_flushToSRAM();

    // Reset accumulators
    accPlayerLines = 0;
    accCameraLines = 0;
    accDirectorLines = 0;
    accEnemiesLines = 0;
    accProjectilesLines = 0;
    accFenrirLines = 0;
    accPickupsLines = 0;
    accSprUpdateLines = 0;
    accFramesInPeriod = 0;
    flushCounter = 0;
  }
}

// =============================================================================
// SRAM FLUSH
// =============================================================================
void debug_flushToSRAM(void) {
  // Enable SRAM access
  SRAM_enable();

  // Write entire structure to SRAM (byte by byte for safety)
  u8 *src = (u8 *)&debugData;
  for (u16 i = 0; i < sizeof(debugData); i++) {
    SRAM_writeByte(i, src[i]);
  }

  // Disable SRAM access
  SRAM_disable();
}

#endif // DEBUG_SRAM_ENABLED
