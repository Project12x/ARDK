
## Asset Pipeline Workflow

### Automated Build (Recommended)

```batch
REM Build all assets from scratch
build_assets.bat

REM Then compile ROM
compile.bat
```

### Manual Steps

1. **Generate Sprites**

   ```bash
   python tools/gen_sprites.py
   ```

   - Creates individual sprite PNGs in `gfx/generated/`
   - Outputs: player, enemies, weapons, pickups

2. **Create Sprite Sheet**

   ```bash
   python tools/make_spritesheet.py
   ```

   - Combines sprites into 128x128 organized layout
   - Generates tile map reference JSON
   - Creates ASM include file with tile constants

3. **Index Colors (4-color palette)**

   ```bash
   python tools/make_indexed_sheet.py
   ```

   - Quantizes RGB colors to 4-color indexed palette
   - Required for img2chr compatibility
   - Output: `gfx/generated/neon_indexed_sheet.png`

4. **Convert to CHR**

   ```bash
   img2chr gfx/generated/neon_indexed_sheet.png src/game/assets/sprites.chr
   ```

   - Converts indexed PNG to NES CHR format
   - Must manually pad to 8KB (see build_assets.bat)

5. **Rebuild ROM**

   ```bash
   compile.bat
   ```

## File Structure

```
SurvivorNES/
├── tools/
│   ├── gen_sprites.py          # Generates individual sprite PNGs
│   ├── make_spritesheet.py     # Combines sprites into sheet
│   ├── make_indexed_sheet.py   # Creates 4-color indexed version
│   └── img2chr/                # Cloned img2chr tool
│
├── gfx/
│   ├── generated/              # Generated sprite PNGs
│   │   ├── player_rad_dude.png
│   │   ├── enemy_bit_drone.png
│   │   ├── enemy_neon_skull.png
│   │   ├── pickup_xp_gem.png
│   │   ├── weapon_laser.png
│   │   ├── neon_survivors_sheet.png      # RGB sprite sheet
│   │   ├── neon_indexed_sheet.png        # Indexed (4-color)
│   │   └── tile_map.json                 # Tile index reference
│   │
│   └── opensource/             # Downloaded open-source assets
│
├── src/game/assets/
│   ├── sprites.chr             # Final CHR file (8KB)
│   └── sprite_tiles.inc        # ASM tile constants
│
├── build_assets.bat            # Automated asset build script
└── compile.bat                 # ROM compilation script
```

## Sprite Tile Map

Our sprites are organized in the CHR file as follows:

| Tile Index | Sprite | Size | Description |
|------------|--------|------|-------------|
| `$00-$03` | Player | 16x16 | Rad 90s dude (2x2 tiles: $00, $01, $10, $11) |
| `$02` | Bit Drone | 8x8 | Basic geometric enemy |
| `$03-$06` | Neon Skull | 16x16 | Floating skull enemy (2x2 tiles) |
| `$20` | XP Gem | 8x8 | Magenta crystal pickup |
| `$21` | Laser | 8x8 | Cyan projectile |

### Using Tiles in Code

The `sprite_tiles.inc` file provides constants:

```asm6502
.include "sprite_tiles.inc"

; Draw player sprite (16x16 = 4 tiles)
lda #TILE_PLAYER_RAD_DUDE    ; $00
sta $0201                     ; Top-left tile

lda #TILE_PLAYER_RAD_DUDE+1  ; $01
sta $0205                     ; Top-right tile

lda #TILE_PLAYER_RAD_DUDE+$10 ; $10
sta $0209                     ; Bottom-left tile

lda #TILE_PLAYER_RAD_DUDE+$11 ; $11
sta $020D                     ; Bottom-right tile
```

## NES Color Constraints

### Sprite Palette

NES sprites use 4-color palettes (including transparent):

- **Color 0**: Black (transparent)
- **Color 1**: Magenta/Pink ($15)
- **Color 2**: Cyan ($21)
- **Color 3**: White ($30)

### Indexed PNG Requirements

For `img2chr` to work correctly:

1. **Exactly 4 colors** (or fewer)
2. **Indexed color mode** (not RGB)
3. **8x8 tile alignment** (width/height divisible by 8)
4. **Grayscale mapping** (img2chr uses grayscale values as indices)

Our `make_indexed_sheet.py` script handles this conversion automatically.

## Troubleshooting

### "7 colors found! The max is 4!"

- Your PNG has too many colors
- Run `make_indexed_sheet.py` to quantize to 4 colors
- Or manually reduce colors in an image editor (GIMP, Aseprite)

### CHR file is 4KB instead of 8KB

- NES CHR ROM banks are 8KB
- Pad with zeros: `dd if=/dev/zero bs=1 count=4096 >> sprites.chr` (Linux)
- Or use Python: `build_assets.bat` handles this automatically

### Sprites appear garbled in emulator

- Check tile indices match your sprite sheet layout
- Verify palette is set correctly in code
- Use Mesen's PPU viewer to inspect CHR data

### img2chr not found

- Install Node.js: <https://nodejs.org/>
- Run: `npm install -g img2chr`
- Verify: `img2chr --version`

## Adding New Sprites

1. **Generate or create PNG** (any size, RGB)
   - Place in `gfx/generated/`

2. **Add to sprite sheet layout**
   - Edit `tools/make_spritesheet.py`
   - Update `layout` dictionary with tile position

3. **Rebuild assets**

   ```bash
   build_assets.bat
   ```

4. **Update ASM code**
   - Use tile index from `tile_map.json`
   - Or reference constant from `sprite_tiles.inc`

## References

- [img2chr GitHub](https://github.com/jehna/img2chr)
- [NEXXT Studio](https://frankengraphics.itch.io/nexxt)
- [NESDev Wiki - CHR](https://www.nesdev.org/wiki/CHR_ROM)
- [NESDev Wiki - Tools](https://www.nesdev.org/wiki/Tools)
- [NES Maker Asset Pipeline](https://forums.nesdev.org/viewtopic.php?t=24026)

## Future Enhancements

- [ ] Integrate Aseprite export directly
- [ ] Support multiple CHR banks for more sprites
- [ ] Animation frame generation
- [ ] Metatile/metasprite system
- [ ] Background tile generation
- [ ] Palette optimization (find best 4-color combos)

# NEON SURVIVORS - Modern Asset Pipeline

**Last Updated:** January 2026
**Purpose:** Production-quality asset workflow using industry-standard tools

## Overview

This project uses **professional NES development tools** following 2026 best practices:

### Graphics Pipeline

- **NEXXT Studio** - Primary graphics editor (industry standard)
- **NesTiler** - Automated batch PNG → CHR conversion
- **img2chr** - Simple converter for quick iterations
- **Nano Banana** - AI sprite generation

### Audio Pipeline

- **FamiStudio** - Modern DAW-style NES music editor
- **Suno AI** - Monophonic chiptune generation + MIDI export

### Build System

- **create-nes-game** - Modern orchestration (recommended for new projects)
- **Makefile** - Traditional with automatic dependency tracking

---

## Production Graphics Tools

### NEXXT Studio ⭐ PRIMARY TOOL

- **Type**: All-in-one NES graphics editor
- **Download**: [frankengraphics.itch.io/nexxt](https://frankengraphics.itch.io/nexxt)
- **Status**: Free, actively maintained (227K LOC, successor to NESST's 14.5K LOC)
- **Features**:
  - Sprite & background tile editing
  - CHR-ROM/CHR-RAM support
  - Nametable/attribute editing
  - Metatile system with collision maps
  - Palette editor
  - Animation preview
  - Import/Export CHR, PNG, ASM data
- **Use Case**: Primary tool for manual graphics work

### NesTiler ⭐ AUTOMATION

- **Type**: Command-line batch converter (PNG → CHR)
- **GitHub**: [ClusterM/NesTiler](https://github.com/ClusterM/NesTiler)
- **Install**: Download from [releases](https://github.com/ClusterM/NesTiler/releases), requires .NET 6
- **Features**:
  - Batch PNG/BMP → CHR conversion
  - Generates pattern tables, nametables, palettes
  - Lossy compression (0-3 levels)
  - Tile grouping/deduplication
  - Background, 8x8 sprite, 8x16 sprite modes
- **Usage**:

  ```bash
  nestiler -i0 sprites.png -o sprites.chr --mode sprites --lossy 0
  nestiler -i0 bg.png:0:256 -o tiles.chr --mode background
  ```

- **Use Case**: Build system integration, batch processing

### img2chr (Fallback)

- **Type**: Simple PNG → CHR converter
- **GitHub**: [jehna/img2chr](https://github.com/jehna/img2chr)
- **Install**: `npm install -g img2chr`
- **Limitations**: Requires pre-indexed 4-color PNG, basic conversion only
- **Usage**: `img2chr input.png output.chr`
- **Use Case**: Quick tests when NesTiler unavailable
