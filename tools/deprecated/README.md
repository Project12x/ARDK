# Deprecated Scripts

These scripts are deprecated and should not be used for new development.
They are kept here for reference only.

See [../DEPRECATED.md](../DEPRECATED.md) for migration guides.

## Scripts in this folder

| Script | Replacement |
|--------|-------------|
| `convert_sprite.py` | `simple_sprite_convert.py` or `pipeline/processing.py` |
| `fix_enemy_transparency.py` | `fix_genesis_assets.py` |
| `fix_hero_transparency.py` | `fix_genesis_assets.py` |
| `gen_tileable_bg.py` | `asset_generators/background_generator.py` |
| `gen_tileset.py` | `asset_generators/background_generator.py` |
| `generate_background.py` | `asset_generators/background_generator.py` |
| `generate_bg.py` | `asset_generators/background_generator.py` |
| `generate_player_assets.py` | `generate_player_v2.py` |
| `make_indexed_sheet.py` | `make_spritesheet.py` |

**Note:** `gen_sprites.py` and `gen_assets.py` were moved back to main `tools/` folder.
They are test asset generators for offline placeholder creation - not deprecated.

## Why deprecated?

- **One-off scripts**: Hardcoded paths/values, not reusable
- **Security issues**: Some have hardcoded API keys
- **Superseded**: Better implementations exist in the pipeline
- **Test code**: Manual test data, not production assets
