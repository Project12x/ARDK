#ifndef _ENGINE_RASTER_H_
#define _ENGINE_RASTER_H_

#include "engine/sinetable.h"
#include <genesis.h>


// =============================================================================
// H-INT RASTER EFFECTS
// Wave effect for heat haze / water distortion
// =============================================================================

// Effect intensity (shift amount)
#define RASTER_WAVE_AMPLITUDE 2 // Max 4px wave
#define RASTER_WAVE_SPEED 3     // How fast the wave moves

// State
extern u8 rasterEnabled;
extern u8 rasterFrame;

// =============================================================================
// FUNCTIONS
// =============================================================================

// Initialize H-Int for raster effects
void raster_init(void);

// Enable/disable wavy background effect
void raster_enable(void);
void raster_disable(void);

// Call each frame to advance the wave animation
void raster_update(void);

#endif // _ENGINE_RASTER_H_
