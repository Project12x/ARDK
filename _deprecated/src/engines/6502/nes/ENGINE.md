# NES Engine (6502)

> **CPU**: Ricoh 2A03 (6502 variant, 1.79MHz NTSC)
> **RAM**: 2KB internal + 8KB PRG-RAM (MMC3)
> **Tier**: MINIMAL (HAL_TIER_MINIMAL)

## Engine Variants

The NES engine supports multiple **variants** optimized for different game genres:

| Variant | Genre | Max Enemies | Key Optimizations |
|---------|-------|-------------|-------------------|
| **ACTION_SURVIVOR** | Horde/Survivors | 64 | Recca shuffler, quadrant AI, spatial grid |
| **ACTION_SHMUP** | Bullet Hell | 96 bullets | Interleaved render, bullet pooling |
| **ADVENTURE_ZELDA** | Top-down RPG | 16 | Scroll engine, room transitions |
| **PLATFORM_ACTION** | Platformer | 24 | Physics, slope collision |

### ACTION_SURVIVOR Features

Optimized for "Vampire Survivors" style gameplay with tower defense:

- **Recca Sprite Multiplexer**: Prime-offset OAM shuffling (mod 17) prevents static dropout
- **Quadrant AI Throttling**: 64 enemies update in 4-frame rotation (15Hz per enemy)
- **Stride Arrays (SoA)**: Enemy_X[64], Enemy_Y[64] etc. for fast indexed access
- **Spatial Bit-Grid**: 16x16 grid for O(1) collision culling
- **XP Spark Buffer**: Circular buffer processes 4 sparks/frame to prevent CPU spikes
- **Interleaved Bullets**: 30fps alternating sets doubles effective bullet count
- **Asymmetric Hitboxes**: Large bullet hitboxes vs 1px enemy hurtboxes
- **CHR Bank Animation**: 0-cycle global enemy animation via bank swapping
- **Priority Culling**: Tower/Player locked to OAM slots 0-7 (never dropout)
- **VBlank Watchdog**: Adaptive render quality if logic overruns
- **MMC3 IRQ Split**: Static HUD at scanline 200

### Using a Variant

```asm
.include "nes.inc"
.include "variants/action_survivor.inc"
.include "variants/action_survivor_advanced.inc"
```

See [variants/README.md](variants/README.md) for detailed documentation.

## Quick Reference

| Resource | Limit | Notes |
|----------|-------|-------|
| Sprites | 64 total, 8/scanline | OAM at $0200-$02FF |
| Sprite size | 8x8 or 8x16 | Global setting |
| BG tiles | 256 | Per CHR bank |
| CHR banks | 8KB each, bankswitch | MMC3 supports 256KB |
| Colors | 4 per palette, 4 palettes | 25 unique colors on screen |
| Resolution | 256x240 | 256x224 visible (NTSC) |

## Directory Structure

```
nes/
├── ENGINE.md           This file
├── engine.inc          Main engine include
├── nes.inc             NES hardware defines
├── init/               Boot sequence
│   ├── header.asm      iNES header (mapper config)
│   ├── entry.asm       Reset handler, initialization
│   └── zeropage.asm    Zero page variable allocation
├── core/               Core systems
│   ├── entity.asm      Entity management
│   └── graphics.asm    CHR bank management
├── hal_native/         Hardware interface
│   ├── nmi.asm         NMI handler (VBlank)
│   ├── input.asm       Controller reading
│   ├── audio.asm       APU interface
│   └── parallax.asm    MMC3 IRQ parallax
├── modules/            Optional game modules
│   ├── action/         Projectiles, powerups, spawners
│   ├── adventure/      (future)
│   └── platform/       (future)
├── utils/              Utility routines
│   ├── collision.asm   AABB collision
│   └── random.asm      LFSR random numbers
└── profiles/           Build profiles
    ├── FAST.inc        Speed-optimized
    ├── STANDARD.inc    Balanced (default)
    └── FULL.inc        All features
```

## Memory Map

### Zero Page ($00-$FF)
```
$00-$0F   Engine temps (temp1-temp4, frame_counter, etc.)
$10-$1F   HAL/Hardware (scroll_x/y, ppu_ctrl_shadow)
$20-$21   Input (buttons, buttons_old)
$22-$2F   Player state (x, y, hp, xp, level, etc.)
$30-$3F   Game state (state machine, timers)
$40-$47   CHR animation (timer, frame, speed, base_bank)
$48-$7F   Module temps (profile-dependent)
$80-$FF   Available for game
```

### RAM ($0000-$07FF)
```
$0000-$00FF   Zero page (see above)
$0100-$01FF   Stack
$0200-$02FF   OAM shadow buffer (DO NOT USE)
$0300-$03FF   Projectiles (16 x 16 bytes)
$0400-$04FF   Enemies (16 x 16 bytes)
$0500-$05FF   Pickups (32 x 8 bytes)
$0600-$07FF   Available (512 bytes)
```

## Build Profiles

### FAST Profile
- **Entities**: 32 max (8 enemies)
- **Features**: No parallax, no CHR animation
- **Optimizations**: Unrolled loops, inline collision
- **Use case**: Action-heavy, frame-critical

### STANDARD Profile (Default)
- **Entities**: 48 max (12 enemies)
- **Features**: Parallax, CHR animation, sprite flicker
- **Optimizations**: Lookup tables
- **Use case**: Most games

### FULL Profile
- **Entities**: 64 max (16 enemies)
- **Features**: All enabled + debug
- **Warning**: May drop frames at max capacity
- **Use case**: Bullet hell, development

## Using the Engine

### Include Order
```asm
.include "nes.inc"              ; Hardware defines first
.include "profiles/STANDARD.inc" ; Profile settings
.include "engine.inc"           ; Engine macros
```

### Accessing HAL from Assembly
```asm
; Input
jsr input_read          ; Updates buttons, buttons_old, buttons_pressed

; Sprites
lda #Y_POS
sta OAM_BUF, x          ; Direct OAM access

; CHR Bank Switching (MMC3)
lda #$00
sta $8000               ; Select bank register
lda #BANK_NUM
sta $8001               ; Set bank
```

### Interrupt Handlers
- **NMI** (nmi.asm): OAM DMA, CHR animation, parallax setup
- **IRQ** (parallax.asm): Mid-screen scroll changes for parallax

## Performance Guidelines

### Cycles Per Frame (NTSC 60fps)
```
Available: ~29,780 CPU cycles per frame

NMI overhead:     ~2,000 cycles (OAM DMA is 513)
Entity update:    ~150 cycles/entity
Collision check:  ~100 cycles/pair
Sprite render:    ~50 cycles/sprite

Example (STANDARD profile):
  48 entities x 150 = 7,200 cycles
  24 collision pairs x 100 = 2,400 cycles
  40 sprites x 50 = 2,000 cycles
  Total: ~11,600 + NMI = ~13,600 cycles
  Headroom: ~16,000 cycles for game logic
```

### Optimization Tips
1. **Use zero page** for frequently accessed variables
2. **Unroll critical loops** (entity update is the big one)
3. **Limit collision pairs** - spatial partitioning helps
4. **Minimize branches** in hot paths
5. **Use lookup tables** for sine/cos/atan2

## Mapper Configuration

Current: **MMC3 (Mapper 4)**
- PRG-ROM: Up to 512KB
- CHR-ROM: Up to 256KB
- PRG-RAM: 8KB (battery-backed optional)
- Scanline IRQ: Yes (used for parallax)

### Bank Switching
```asm
; PRG banks ($8000-$9FFF and $A000-$BFFF)
lda #$06        ; Register 6 = $8000 bank
sta $8000
lda #BANK_NUM
sta $8001

; CHR banks (2KB at $0000, 2KB at $0800, 4x1KB at $1000-$1C00)
lda #$00        ; Register 0 = 2KB CHR at $0000
sta $8000
lda #CHR_BANK
sta $8001
```

## Related Documentation

- [HAL Reference](../../../hal/hal.h)
- [Platform Manifest](../../../hal/platform_manifest.h)
- [Tier Definitions](../../../hal/hal_tiers.h)
- [NES HiFi Graphics](../../../../docs/NES_HIFI_GRAPHICS.md)
