# ARDK Asset Generators

AI-powered asset generation pipeline for retro game development.

## Overview

The asset generators module provides a complete pipeline for generating, converting, and optimizing pixel art assets for retro gaming platforms (NES, Genesis, SNES, etc.).

## Architecture

```
asset_generators/
├── base_generator.py      # Core classes, Pollinations client, platform configs
├── model_config.py        # Model tiers (economy/quality/precision/pixelart)
├── prompt_system.py       # Dynamic prompts with console constraints
├── pixellab_client.py     # PixelLab API (pixel art specialist)
├── tier_system.py         # Hardware tier definitions (MINIMAL→EXTENDED)
├── cross_gen_converter.py # Cross-generation conversion (8-bit→16-bit)
├── sprite_generator.py    # Sprite sheet generation
└── background_generator.py # Parallax background generation
```

## Model Tiers

| Tier | txt2img Model | Cost | Best For |
|------|---------------|------|----------|
| **economy** | flux | $0.0002/image | Bulk generation, prototyping |
| **quality** | seedream | $0.03/image | Better output quality |
| **precision** | gptimage-large | ~$8/1M tokens | Critical assets |
| **pixelart** | pixellab-pixflux | $0.01/image | Game-ready sprites |

## API Integrations

### Pollinations.ai (Free/Cheap)
- `flux` - Text-to-image, best for pixel art ($0.0002/image)
- `gptimage` - Image-to-image with content preservation
- `nanobanana` - Gemini-based alternative

### BFL Kontext (Precise Dimensions)
- `flux-kontext-pro` - Exact dimension control
- Requires BFL_API_KEY

### PixelLab (Pixel Art Specialist)
- `pixflux` - Text-to-pixel art (up to 400x400)
- `bitforge` - Style transfer and inpainting
- `rotate` - Multi-directional sprite generation
- `animate` - Text-driven animation (2-20 frames)
- Requires PIXELLAB_API_KEY

## Dynamic Prompt System

Prompts are built with platform constraints FROM generation:

```python
from asset_generators.prompt_system import PromptBuilder

builder = PromptBuilder("nes")
prompt = builder.sprite_prompt(
    description="robot enemy with laser eyes",
    size=(16, 16),
    animation="idle"
)
# Includes: 4 colors, 8x8 tile alignment, symmetry hints, no anti-aliasing
```

### Supported Platforms
- NES, Famicom, Game Boy, Game Boy Color
- Sega Master System, Genesis/Mega Drive
- SNES/Super Famicom, PC Engine
- Neo Geo, GBA, Nintendo DS

## Quick Start

### Economy Mode (Cheapest)
```python
from asset_generators.base_generator import PollinationsClient

client = PollinationsClient()
image = client.generate_image(
    prompt="16-bit robot sprite, pixel art",
    width=64, height=64,
    model="flux"  # $0.0002/image
)
```

### PixelArt Mode (Best Quality)
```python
from asset_generators.pixellab_client import PixelLabClient, Outline, Shading

client = PixelLabClient()
result = client.generate_image(
    description="robot enemy with red glowing eyes",
    width=64, height=64,
    outline=Outline.SINGLE_COLOR_BLACK,
    shading=Shading.DETAILED,
    no_background=True
)
sprite = result.image
```

### Generate 8-Directional Sprites
```python
directions = client.generate_directional_sprites(
    reference_image=sprite,
    directions=8  # or 4
)
# Returns dict: {"north": img, "north-east": img, ...}
```

### Text-Driven Animation
```python
result = client.animate_with_text(
    description="robot character",
    action="walk",  # or "run", "attack", "idle"
    reference_image=sprite,
    n_frames=4
)
frames = result.images  # List of 4 PIL Images
```

## Cross-Generation Conversion

Convert assets between platform tiers:

```python
from asset_generators.cross_gen_converter import CrossGenConverter

converter = CrossGenConverter()

# NES → Genesis (8-bit to 16-bit)
result = converter.upscale_to_16bit(
    image=nes_sprite,
    source_platform="nes",
    target_platform="genesis",
    scale_factor=2
)
```

## Configuration

### API Keys (`configs/api_keys.py`)
```python
POLLINATIONS_API_KEY = "sk_..."  # Optional, increases rate limits
BFL_API_KEY = "bfl_..."          # Required for Kontext
PIXELLAB_API_KEY = "..."         # Required for PixelLab
```

### Environment Variables
```bash
export POLLINATIONS_API_KEY="sk_..."
export BFL_API_KEY="bfl_..."
export PIXELLAB_API_KEY="..."
```

## Testing

```bash
# Run model test suite
python tools/test_model_suite.py

# Test prompt system
python tools/asset_generators/prompt_system.py --platform nes --type sprite --desc "robot"

# Check PixelLab balance
python tools/asset_generators/pixellab_client.py --balance
```

## Completed Features

- [x] Pollinations.ai integration (txt2img, img2img)
- [x] BFL Kontext integration (precise dimensions)
- [x] PixelLab integration (pixel art specialist)
- [x] Dynamic prompt system with console constraints
- [x] Model tier configuration (economy/quality/precision/pixelart)
- [x] Cross-generation conversion pipeline
- [x] Multi-directional sprite generation
- [x] Text-driven animation

## Pending Features

- [ ] Automatic palette optimization per platform
- [ ] Tile deduplication with H-flip/V-flip detection
- [ ] Sprite sheet auto-layout
- [ ] Animation timing analysis
- [ ] Batch generation with style consistency
