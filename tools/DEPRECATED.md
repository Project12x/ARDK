# Deprecated Scripts

This document lists scripts that are deprecated and should not be used for new development.
Use the recommended alternatives instead.

**Note:** Deprecated scripts have been moved to the `deprecated/` folder.

---

## Background Generation Scripts

| Script | Location | Replacement |
|--------|----------|-------------|
| `generate_background.py` | `deprecated/` | `asset_generators/background_generator.py` |
| `generate_bg.py` | `deprecated/` | `asset_generators/background_generator.py` |
| `gen_tileable_bg.py` | `deprecated/` | `asset_generators/background_generator.py` |
| `gen_tileset.py` | `deprecated/` | `asset_generators/background_generator.py` |

**Why:** These are one-off scripts with hardcoded paths and API keys. The `BackgroundGenerator` class provides:
- Platform-specific constraints
- Tile deduplication
- Proper error handling
- Config-based API keys

**Migration:**
```python
# Old way (DON'T USE)
# python generate_background.py

# New way
from asset_generators.background_generator import BackgroundGenerator
gen = BackgroundGenerator(platform="genesis")
result = gen.generate_scrolling_background(width_screens=4, tileable=True)
```

---

## Transparency Fix Scripts

| Script | Location | Platform | Replacement |
|--------|----------|----------|-------------|
| `fix_enemy_transparency.py` | `deprecated/` | Genesis | `fix_genesis_assets.py` |
| `fix_hero_transparency.py` | `deprecated/` | Genesis | `fix_genesis_assets.py` |
| `fix_sprite_transparency.py` | KEEP | Generic | Use for any platform |
| `fix_genesis_assets.py` | KEEP | Genesis | Use for Genesis/Mega Drive |

**Why:** `fix_enemy_transparency.py` and `fix_hero_transparency.py` are asset-specific one-off scripts.

**Which to use:**
- **Generic (any platform):** `fix_sprite_transparency.py` - Works with any indexed PNG
- **Genesis/Mega Drive:** `fix_genesis_assets.py` - Handles magenta transparency, 16-color palettes, batch processing

**Migration:**
```python
# Old way (DON'T USE)
# python fix_enemy_transparency.py

# Generic - single file (any platform)
from fix_sprite_transparency import fix_sprite_transparency
fix_sprite_transparency("path/to/sprite.png")

# Genesis - batch processing
python fix_genesis_assets.py  # Edit file list in script
```

---

## Sprite Generation Scripts

| Script | Location | Replacement |
|--------|----------|-------------|
| `generate_player_assets.py` | `deprecated/` | `generate_player_v2.py` |

**Why:** `generate_player_assets.py` uses custom PixelLab client instead of official SDK.

**Note:** `gen_sprites.py` and `gen_assets.py` are **NOT deprecated** - they are test asset generators
for creating placeholder sprites offline without API calls. See "Scripts to KEEP" section.

**Migration:**
```python
# Old way (DON'T USE)
# python generate_player_assets.py

# New way - use CharacterGenerator for AI generation
from asset_generators.character_generator import CharacterGenerator
gen = CharacterGenerator(platform="genesis")
result = gen.generate_character(description="warrior hero", directions=8)

# Or use generate_player_v2.py for styled generation
python generate_player_v2.py

# For offline test assets (no API), use gen_sprites.py or gen_assets.py
python gen_sprites.py
```

---

## Conversion Scripts

| Script | Location | Replacement |
|--------|----------|-------------|
| `convert_sprite.py` | `deprecated/` | `simple_sprite_convert.py` or `pipeline/processing.py` |
| `make_indexed_sheet.py` | `deprecated/` | `make_spritesheet.py --indexed` |

**Why:** These are one-off scripts superseded by more complete implementations.

**Note:** The indexed output from `make_indexed_sheet.py` is now available via:
```bash
python make_spritesheet.py --indexed
```

**Migration:**
```python
# Old way (DON'T USE)
# python convert_sprite.py

# New way - use SpriteConverter
from pipeline.processing import SpriteConverter
converter = SpriteConverter(platform=GenesisConfig)
indexed = converter.index_sprite(img)

# For sprite sheets
from pipeline.sheet_assembler import SpriteSheetAssembler
assembler = SpriteSheetAssembler()
sheet = assembler.create_sheet(sprites, layout)
```

---

## Scripts to DELETE

These deprecated scripts can be safely removed after confirming no active use:

1. `fix_enemy_transparency.py` - Duplicate functionality (use `fix_genesis_assets.py`)
2. `fix_hero_transparency.py` - Duplicate functionality (use `fix_genesis_assets.py`)
3. `convert_sprite.py` - One-off conversion (use `simple_sprite_convert.py`)

---

## Scripts to KEEP (Production-Ready)

| Script | Purpose | Notes |
|--------|---------|-------|
| `generate_player_v2.py` | Player sprite generation | Uses official SDK |
| `generate_hero_sprite.py` | Hero + dog generation | Has safety/budget controls |
| `fix_genesis_assets.py` | Batch transparency fix | Production-ready |
| `fix_sprite_transparency.py` | Single-file transparency | Reusable function |
| `simple_sprite_convert.py` | NES CHR conversion | Best CHR implementation |
| `make_spritesheet.py` | Sheet assembly | Complete workflow |
| `optimize_tiles.py` | Tile deduplication CLI | Uses pipeline/optimization |
| `watch_assets.py` | File watching CLI | Uses pipeline/watch |
| `gen_sprites.py` | Test sprite generation | Offline placeholders, no API |
| `gen_assets.py` | Test asset generation | Offline placeholders, no API |

---

## Scripts to ARCHIVE (Experimental)

| Script | Purpose | Notes |
|--------|---------|-------|
| `generate_hero_multimodal.py` | Multi-provider comparison | Quality testing tool |

---

## Canonical Pipeline Modules

For new development, use these pipeline modules:

```
pipeline/
├── optimization/tile_optimizer.py  # Tile deduplication
├── watch/file_watcher.py           # File watching
├── processing.py                    # Sprite conversion
├── sheet_assembler.py              # Sheet layout
├── validation.py                    # Asset validation
├── platforms.py                     # Platform configs
└── palettes/genesis_palettes.py    # Color palettes

asset_generators/
├── character_generator.py          # Character sprites
├── background_generator.py         # Backgrounds
├── parallax_generator.py           # Parallax layers
└── animated_tile_generator.py      # Animated tiles
```

---

## CLI Entry Points

| CLI Tool | Purpose | Module |
|----------|---------|--------|
| `python -m pipeline.cli` | Unified pipeline CLI | `pipeline/cli.py` |
| `python optimize_tiles.py` | Tile optimization | `pipeline/optimization/` |
| `python watch_assets.py` | Asset watching | `pipeline/watch/` |
| `python ardk_generator.py` | Asset generation | `asset_generators/` |

---

*Last updated: 2026-01-24*
