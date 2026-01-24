# ARDK-Genesis - Continuation Prompt

**Project**: ARDK-Genesis (rename folder from SurvivorNES)
**Date**: 2026-01-14
**Game**: EPOCH (working titles: Time Guardians, Neon Guardians)
**Platform**: Sega Genesis/Mega Drive (SGDK)
**Status**: Fresh start - epoch folder is empty, ready for development

---

## WHAT IS THIS PROJECT?

**ARDK-Genesis** is a Genesis game development project with AI-powered asset generation tools.

### Components

1. **EPOCH** - A tower defense / horde survival hybrid for Genesis (not yet implemented)
2. **AI Asset Pipeline** - Multi-provider sprite/background generation (PixelLab, Pollinations)

### Key Change (2026-01-14)

NES development was deprecated due to difficulty of agentic 6502 assembly coding. Now focusing **solely on Genesis** using SGDK (C-based), which is much more suitable for AI-assisted development.

---

## GAME: EPOCH

A tower defense / horde survival hybrid for Sega Genesis.

- **Genre**: Tower defense + horde survival
- **Aesthetic**: Synthwave/cyberpunk (magenta, cyan, white)
- **Features**:
  - Wave-based enemies
  - Tower placement and upgrades
  - XP/leveling system
  - Auto-attacking weapons
- **Technical**: SGDK, 68000 C code

### Game States

```text
TITLE --> PLAYING <--> LEVELUP
             |             |
         PAUSED <-----  GAMEOVER
```

---

## PROJECT STRUCTURE

```text
ARDK-Genesis/
├── START_PROMPT.md              # This file
├── README.md
│
├── projects/
│   ├── _common/                 # Shared assets
│   ├── epoch/                   # Main game (EMPTY - fresh start)
│   │   ├── src/
│   │   ├── inc/
│   │   ├── res/
│   │   └── out/
│   └── genesis_demo/            # Simple test project
│
├── tools/                       # AI asset generation & processing
│   ├── unified_pipeline.py      # Main sprite processor (13+ platforms)
│   ├── asset_generators/        # AI generation modules
│   │   ├── pixellab_client.py   # PixelLab API (pixel art specialist)
│   │   ├── base_generator.py    # PollinationsClient
│   │   ├── model_config.py      # Model tiers
│   │   ├── prompt_system.py     # Platform-aware prompts
│   │   ├── tier_system.py       # Platform tier configs
│   │   ├── sprite_ingestor.py   # Validation & palette mapping
│   │   ├── character_generator.py
│   │   ├── background_generator.py
│   │   └── cross_gen_converter.py
│   ├── configs/
│   │   └── api_keys.py          # API keys
│   ├── pipeline/
│   ├── tile_optimizers/
│   └── emulators/genesis/
│
├── docs/                        # Documentation
│   ├── PROJECT_ARCHITECTURE.md
│   ├── PIPELINE_REFERENCE.md
│   ├── PROVIDERS_AND_MODELS.md
│   ├── AI_PROMPT_TEMPLATES.md
│   └── DOCUMENTATION_STANDARDS.md
│
├── gfx/                         # Graphics assets
│   ├── ai_output/
│   ├── converted/
│   ├── generated/
│   ├── opensource/
│   └── processed/
│
├── src/genesis/                 # Shared Genesis code (future)
│
└── _deprecated/                 # Old NES/HAL code (preserved)
    ├── README.md
    ├── src/
    ├── projects/
    ├── docs/
    ├── tools/                   # NES tools (cc65, nestiler, etc.)
    └── lib/                     # NES libraries
```

---

## AI ASSET PIPELINE

### Providers

| Provider | Models | Cost | Best For |
|----------|--------|------|----------|
| **PixelLab** | pixflux, bitforge, rotate, animate | $0.01/image | Pixel art, exact dimensions, animation |
| **Pollinations** | flux, gptimage, seedream | $0.0002-$0.03 | Bulk generation, img2img |

### Model Tiers

| Tier | txt2img | img2img | Cost | Use Case |
|------|---------|---------|------|----------|
| **economy** | flux | gptimage | $0.0002 | Prototyping |
| **quality** | seedream | gptimage | $0.03 | Better quality |
| **pixelart** | pixellab-pixflux | pixellab-bitforge | $0.01 | Game-ready sprites |

### PixelLab Features

- **pixflux**: Text-to-pixelart (up to 400x400), outline/shading controls
- **bitforge**: Style transfer and inpainting (up to 200x200)
- **rotate**: Generate 4 or 8 directional sprites
- **animate**: Text-driven animation (2-20 frames)

### Usage

```python
# Generate sprite with PixelLab
from asset_generators.pixellab_client import PixelLabClient

client = PixelLabClient()
result = client.generate_image_pixflux(
    description="robot guardian tower, laser turret",
    width=32, height=32,
    outline="single_color_black",
    shading="detailed"
)
result.image.save("tower.png")

# Process for Genesis
python tools/unified_pipeline.py tower.png -o res/sprites/ --platform genesis
```

---

## GENESIS SPECS

| Resource | Limit |
|----------|-------|
| Sprites | 80 on screen, 20 per scanline |
| Sprite size | 8x8 to 32x32 |
| Colors | 64 total (4 palettes x 16) |
| VRAM | 64KB |
| Resolution | 320x224 (NTSC) |
| CPU | Motorola 68000 @ 7.67 MHz |

### Suggested Entity Limits

| Limit | Value |
|-------|-------|
| MAX_ENEMIES | 48 |
| MAX_PROJECTILES | 64 |
| MAX_TOWERS | 8 |
| MAX_PICKUPS | 32 |

---

## BUILD COMMANDS

```bash
# Build EPOCH (requires SGDK installed, GDK env var set)
cd projects/epoch
build.bat
# Output: out/rom.bin

# Process sprites for Genesis
python tools/unified_pipeline.py sprite.png -o projects/epoch/res/ --platform genesis

# Test PixelLab balance
python tools/asset_generators/pixellab_client.py --balance

# Test model suite
python tools/test_model_suite.py
```

---

## API KEYS

Located in `tools/configs/api_keys.py`:

```python
_API_KEYS = {
    'pollinations': 'sk_...',
    'bfl': 'bfl_...',
    'pixellab': '',  # Required - get from https://pixellab.ai
}
```

---

## WHAT NOT TO DO

- **Don't develop NES code** - it's deprecated in `_deprecated/`
- **Don't use `kontext` model alone** - returns promo page; use `flux-kontext`
- **Don't URL-encode the `image` parameter** in Pollinations API

---

## NEXT STEPS

The `projects/epoch/` folder is empty and ready for a fresh implementation. When starting development:

1. Create `src/main.c` - Game entry point
2. Create `inc/game.h` - Game definitions and structures
3. Create `res/resources.res` - SGDK resource definitions
4. Create `build.bat` - Build script

---

## KEY FILES

### Tools (Active)

- `tools/unified_pipeline.py` - Main sprite processor
- `tools/asset_generators/pixellab_client.py` - PixelLab API
- `tools/asset_generators/model_config.py` - Model tiers
- `tools/asset_generators/prompt_system.py` - Platform prompts
- `tools/configs/api_keys.py` - API configuration

### Deprecated (Preserved - Do Not Delete)

- `_deprecated/` - All NES/HAL code, tools, and documentation

---

*Focus: Genesis game development with AI-powered asset generation. The EPOCH game folder is empty - ready for fresh development.*
