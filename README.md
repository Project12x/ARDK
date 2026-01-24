# ARDK-Genesis

Genesis/Mega Drive game development with AI-powered asset generation tools.

## Projects

- **EPOCH** - Tower defense / horde survival hybrid (working titles: Time Guardians, Neon Guardians)

## Requirements

- **SGDK** - Sega Genesis Development Kit
  - Download from: <https://github.com/Stephane-D/SGDK>
  - Set `GDK` environment variable to install path
- **Python 3.10+** - For AI asset pipeline
- **PixelLab API key** (optional) - For pixel art generation

## Building

```bash
cd projects/epoch
build.bat
# Output: out/rom.bin
```

## Project Structure

```text
ARDK-Genesis/
├── projects/           # Individual games
│   ├── epoch/          # Main game (SGDK)
│   └── genesis_demo/   # Test project
├── tools/              # AI asset pipeline
│   ├── asset_generators/   # PixelLab, Pollinations clients
│   ├── unified_pipeline.py # Main sprite processor
│   └── configs/        # API keys, platform specs
├── gfx/                # Graphics assets
├── docs/               # Documentation
└── _deprecated/        # Old NES/HAL code (preserved)
```

## AI Asset Pipeline

Generate game-ready sprites using AI:

```bash
# Process sprite for Genesis
python tools/unified_pipeline.py sprite.png -o projects/epoch/res/ --platform genesis

# Check PixelLab balance
python tools/asset_generators/pixellab_client.py --balance
```

## License

MIT License
