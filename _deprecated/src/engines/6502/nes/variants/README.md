# NES Engine Variants

Engine variants are pre-configured combinations of modules and optimizations for specific game genres.

## Available Variants

| Variant | Genre | Max Entities | Sprite Strategy | Best For |
|---------|-------|--------------|-----------------|----------|
| **ACTION_SURVIVOR** | Survivors/Horde | 64 enemies | Recca multiplexer | Tower defense survivors |
| **ACTION_SHMUP** | Bullet Hell | 96 bullets | Interleaved rendering | Vertical shooters |
| **ADVENTURE_ZELDA** | Top-down RPG | 16 enemies | Standard | Zelda-likes |
| **PLATFORM_ACTION** | Platformer | 24 enemies | Standard | Mega Man, Castlevania |

## Variant Architecture

Each variant includes:
```
variant_xxx.inc       ; Main include (pulls in all components)
├── core features     ; Always included (MMC3, input, NMI)
├── memory layout     ; Variant-specific RAM allocation
├── sprite strategy   ; How OAM is managed
└── AI throttling     ; How/when entities update
```

## Core Features (All Variants)

- MMC3 mapper initialization
- Controller input (with HAL button format)
- NMI handler with OAM DMA
- VBlank watchdog for stability
- CHR bank switching

## ACTION_SURVIVOR Variant

Optimized for "Vampire Survivors" style gameplay with tower defense elements.

### Features
- **Recca Sprite Multiplexer**: Prime-offset OAM shuffling prevents static dropout
- **Interleaved Bullets**: 30fps alternating sets doubles effective bullet count
- **Quadrant AI**: 64 enemies update in 4-frame rotation (15Hz per enemy)
- **Spatial Bitmask**: Fast collision culling via density map
- **Stride Arrays**: SoA layout for maximum indexed addressing speed

### Memory Layout
```
Zero Page:
$00-$0F   Engine temps
$10-$1F   HAL/Hardware
$20-$2F   Player state (x, y, hp, xp_lo, xp_hi, level)
$30-$3F   Tower state (x, y, hp, xp_lo, xp_hi, upgrade_flags)
$40-$4F   Weapon state (type, level, cooldown, damage x4)
$50-$5F   Spawner state
$60-$6F   OAM shuffler state
$70-$7F   Reserved
$80-$9F   Density map cache (32 bytes = 256 cells)
$A0-$FF   Game temps

RAM:
$0200     OAM shadow (64 sprites)
$0300     Enemy_X[64] (stride array)
$0340     Enemy_Y[64]
$0380     Enemy_HP[64]
$03C0     Enemy_State[64]
$0400     Bullet_X[64]
$0440     Bullet_Y[64]
$0480     Bullet_Active[64] (bitmask: 8 bytes)
$0488     Bullet_VelX[64]
$04C8     Bullet_VelY[64]
$0500     XP_Gem_X[32]
$0520     XP_Gem_Y[32]
$0540     XP_Gem_Value[32]
$0560     Density_Map[64] (8x8 grid, 32px cells)
$05A0     Available
```

### Sprite Priority
1. **Slot 0-3**: Tower (always visible, 16x16)
2. **Slot 4-7**: Player (always visible, 16x16)
3. **Slot 8-15**: Bullets (interleaved 30fps)
4. **Slot 16-63**: Enemies (Recca shuffled)

## Usage

```asm
; In your game's main file:
.include "nes.inc"
.include "variants/action_survivor.inc"

; Variant provides:
;   - mmc3_init
;   - sprite_multiplexer_update
;   - ai_update_quadrant
;   - collision_check_bitmask
;   - etc.
```
