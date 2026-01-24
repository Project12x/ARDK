# ARDK-Genesis Projects

Individual game and demo projects for Sega Genesis/Mega Drive using SGDK.

## Project Structure

Each project follows SGDK conventions:

```
project_name/
├── src/           # C source files (.c)
├── inc/           # Header files (.h)
├── res/           # Resources (defined in .res files)
│   ├── sprites/   # Sprite PNGs
│   ├── tiles/     # Tileset PNGs
│   ├── maps/      # Map data
│   └── audio/     # Music and SFX
├── out/           # Build output (ROM, intermediates)
└── project.res    # SGDK resource definitions
```

## Projects

### `neon_survivors/`
**NEON SURVIVORS** - A Vampire Survivors-style horde survival game.
- Synthwave aesthetic (magenta, cyan, white)
- Wave-based enemies
- XP/leveling system
- Tower placement (defense hybrid)
- Auto-attacking weapons

### `genesis_demo/`
Simple demonstration project for testing SGDK setup and basic mechanics.

### `_common/`
Shared assets and code used across multiple projects.
- Common sprite sheets
- Shared utility functions
- Reusable game components

## Building

Requires SGDK installed and configured.

```bash
# From project directory
cd projects/neon_survivors
%GDK%/bin/make -f %GDK%/makefile.gen
# Output: out/rom.bin
```

Or use the build script:
```bash
./build.sh neon_survivors
```

## Asset Pipeline Integration

Use the tools in `tools/` to generate and process assets:

```bash
# Generate sprite with PixelLab
python tools/asset_generators/pixellab_client.py --generate "robot enemy" --size 32x32

# Process sprite for Genesis
python tools/unified_pipeline.py sprite.png -o res/sprites/ --platform genesis
```

## Genesis Specs

| Resource | Limit |
|----------|-------|
| Sprites | 80 on screen, 20 per scanline |
| Sprite size | 8x8 to 32x32 |
| Colors | 64 total (4 palettes x 16 colors) |
| VRAM | 64KB |
| Resolution | 320x224 (NTSC) |
| CPU | Motorola 68000 @ 7.67 MHz |
| Sound | Yamaha YM2612 (FM) + SN76489 (PSG) |

## SGDK Resources

- [SGDK GitHub](https://github.com/Stephane-D/SGDK)
- [SGDK Wiki](https://github.com/Stephane-D/SGDK/wiki)
- [Genesis Development Wiki](https://segaretro.org/Sega_Mega_Drive/Development)
