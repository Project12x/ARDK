# NES Code Snippet Library

Reusable 6502 assembly code snippets for NES game development.

## Directory Structure

```
snippets/
├── audio/           # Sound and music
│   └── famitone2_template.asm
├── compression/     # Data compression
│   └── rle.asm
├── effects/         # Visual effects
│   ├── palette_fade.asm
│   ├── parallax_scroll.asm
│   ├── particle_system.asm
│   └── screen_shake.asm
├── graphics/        # Sprite and background rendering
│   ├── metatiles.asm
│   ├── palette_fade.asm
│   └── sprite_multiplexing.asm
├── input/           # Controller handling
│   └── controller.asm
└── math/            # Math routines
    ├── fixed_point.asm
    ├── random.asm
    └── sine_table.asm
```

## Quick Reference

### Graphics

| File | Purpose | Key Functions |
|------|---------|---------------|
| `sprite_multiplexing.asm` | Show 8+ sprites per scanline | `sort_sprites_by_y`, `apply_flicker_rotation` |
| `palette_fade.asm` | Screen fades and flash effects | `start_fade_in`, `start_fade_out`, `flash_palette` |
| `metatiles.asm` | 16x16/32x32 level building blocks | `draw_metatile`, `get_collision_at` |

### Math

| File | Purpose | Key Functions |
|------|---------|---------------|
| `fixed_point.asm` | 8.8 fixed point for smooth movement | `add_8_8`, `mul_8x8_16`, `apply_velocity` |
| `sine_table.asm` | Circular motion, waves | `get_sine`, `get_cosine`, `calc_circle_pos` |
| `random.asm` | Fast random numbers | `rand8_fast`, `rand_range`, `rand_weighted` |

### Effects

| File | Purpose | Key Functions |
|------|---------|---------------|
| `parallax_scroll.asm` | Multi-layer scrolling | `update_parallax`, `apply_split_scroll` |
| `screen_shake.asm` | Impact feedback | `start_shake`, `update_shake`, `start_hitstop` |
| `particle_system.asm` | Explosions, sparks | `spawn_explosion`, `spawn_hit_spark`, `update_particles` |

### Input

| File | Purpose | Key Functions |
|------|---------|---------------|
| `controller.asm` | Full input handling | `read_controllers`, `is_pressed`, `is_turbo_pressed` |

### Audio

| File | Purpose | Key Functions |
|------|---------|---------------|
| `famitone2_template.asm` | Music integration | `audio_init`, `play_music`, `play_sfx` |

### Compression

| File | Purpose | Key Functions |
|------|---------|---------------|
| `rle.asm` | Simple data compression | `rle_decode_simple`, `rle_decode_to_ppu` |

## Usage

1. Copy desired snippet to your project's `src/` directory
2. Include in your main assembly file:
   ```asm
   .include "effects/screen_shake.asm"
   ```
3. Call initialization functions at game start
4. Call update functions each frame

## Integration Notes

- All snippets use ca65/ld65 syntax (cc65 toolchain)
- Most snippets need zeropage variables - check `.segment "ZEROPAGE"` sections
- Some snippets depend on others (e.g., screen_shake needs random.asm)
- Customize constants at top of each file for your game

## Memory Requirements

| Category | Typical ZP Usage | BSS Usage |
|----------|------------------|-----------|
| Graphics | 8-16 bytes | 64-256 bytes |
| Math | 4-8 bytes | 0 bytes |
| Effects | 8-12 bytes | 128-512 bytes |
| Input | 8-12 bytes | 16-64 bytes |
| Audio | 36 bytes | 256 bytes |

## Performance Notes

- Most routines optimized for speed over size
- Update functions typically 100-500 cycles
- Rendering functions may take longer (1000+ cycles)
- Profile in Mesen debugger for accurate timing
