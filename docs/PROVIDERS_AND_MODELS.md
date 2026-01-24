# ARDK Pollinations.AI Provider & Models Reference
## Last Updated: January 2026

This document catalogs all available Pollinations.AI models and establishes per-tier protocols for the ARDK sprite generation pipeline.

---

## API Endpoints

| Service | Endpoint |
|---------|----------|
| Unified Generation | `https://gen.pollinations.ai/v1/chat/completions` |
| Image Generation | `https://image.pollinations.ai/prompt/{prompt}` |
| Text Models List | `https://text.pollinations.ai/models` |
| Image Models List | `https://gen.pollinations.ai/image/models` |
| All Models List | `https://gen.pollinations.ai/v1/models` |

---

## Text/Chat Models (23 Available as of January 2026)

### OpenAI Family
| Model ID | Aliases | Description | Vision | Speed | Best For |
|----------|---------|-------------|--------|-------|----------|
| `openai` | - | GPT-5 Mini | Yes | Medium | General tasks, default |
| `openai-fast` | `gpt-oss`, `gpt-oss-20b` | GPT-OSS 20B Reasoning (OVH) | No | Fast | Quick reasoning |
| `openai-large` | - | GPT-5.2 | **Yes** | Slow | **Palette extraction, complex vision** |
| `openai-audio` | - | Audio processing | No | Medium | TTS/STT |

### Claude Family
| Model ID | Description | Vision | Speed | Best For |
|----------|-------------|--------|-------|----------|
| `claude` | Standard Claude | Yes | Medium | Balanced analysis |
| `claude-fast` | Speed-optimized Claude | No | Fast | Quick text tasks |
| `claude-large` | Enhanced Claude | **Yes** | Slow | Deep analysis |

### Gemini Family (Google)
| Model ID | Aliases | Description | Vision | Tools | Best For |
|----------|---------|-------------|--------|-------|----------|
| `gemini` | `gemini-2.5-flash-lite` | Gemini 2.5 Flash Lite | **Yes** | code_execution | Vision + code |
| `gemini-fast` | - | Speed-optimized Gemini | **Yes** | code_execution | **Fast sprite detection** |
| `gemini-large` | - | Large Gemini variant | **Yes** | code_execution | Complex vision |
| `gemini-search` | - | Gemini with Google Search | No | google_search | Research |

### Specialized Models
| Model ID | Description | Vision | Speed | Best For |
|----------|-------------|--------|-------|----------|
| `qwen-coder` | Qwen3-Coder-30B | No | Medium | **6502 assembly, code generation** |
| `deepseek` | DeepSeek V3.2 | No | Fast | Reasoning, optimization |
| `grok` | xAI Grok | No | Medium | General chat |
| `mistral` | Mistral Small 3.2 24B | No | Fast | Efficient inference |
| `perplexity-fast` | Speed Perplexity | No | Fast | Search queries |
| `perplexity-reasoning` | Reasoning Perplexity | No | Slow | Complex reasoning |
| `kimi` | Kimi model | No | Medium | General |
| `nova-fast` | Amazon Nova Micro | No | **Very Fast** | Ultra-low-cost |
| `glm` | GLM model | No | Medium | General |
| `minimax` | MiniMax model | No | Medium | General |

### Community/Special Purpose
| Model ID | Description | Vision | Best For |
|----------|-------------|--------|----------|
| `bidara` | NASA Biomimetic Designer | **Yes** | Scientific analysis |
| `chickytutor` | Language Tutor | No | Educational |
| `midijourney` | Music/MIDI generation | No | Audio asset generation |

---

## Image Generation Models (10 Available)

| Model ID | Aliases | Description | Quality | Speed | Resolution | Best For |
|----------|---------|-------------|---------|-------|------------|----------|
| `flux` | - | Flux Schnell | High | Fast | 1280x1280 | **Pixel art, sprites** |
| `turbo` | - | SDXL Turbo (single-step) | Medium | **Very Fast** | Standard | Quick prototypes |
| `gptimage` | `gpt-image`, `gpt-image-1-mini` | GPT Image 1 Mini | High | Medium | Standard | General |
| `gptimage-large` | `gpt-image-1.5` | GPT Image 1.5 | **Very High** | Slow | **4K** | High-quality assets |
| `seedream` | - | Seedream 4.0 (ByteDance) | High | Medium | Standard | Good gradients |
| `seedream-pro` | - | Seedream 4.5 Pro | **Very High** | Slow | **4K, Multi** | Production assets |
| `kontext` | - | FLUX.1 Kontext | High | Medium | Variable | **Image editing** |
| `nanobanana` | - | Gemini 2.5 Flash Image | Medium | Fast | Standard | Quick gen |
| `nanobanana-pro` | - | Gemini 3 Pro Image | High | Slow | **4K, Thinking** | Complex scenes |
| `zimage` | `z-image`, `z-image-turbo` | Z-Image Turbo (6B Flux) | High | Fast | **2x upscale** | Upscaling |

---

## Vision-Capable Models (Confirmed)

Models that support image INPUT for analysis:

| Model ID | Provider | Speed | Recommended Use |
|----------|----------|-------|-----------------|
| `openai-large` | OpenAI GPT-5.2 | Slow | **Primary: Palette extraction** |
| `gemini-fast` | Google Gemini | Fast | **Primary: Sprite detection** |
| `gemini` | Google Gemini | Medium | Sprite analysis |
| `gemini-large` | Google Gemini | Slow | Complex analysis |
| `claude` | Anthropic | Medium | Fallback analysis |
| `claude-large` | Anthropic | Slow | Deep analysis |
| `bidara` | NASA | Medium | Scientific sprites |

---

## Rate Limits & Tiers

### API Key Types
| Key Type | Prefix | Use Case | Rate Limit |
|----------|--------|----------|------------|
| Publishable | `pk_` | Client-side demos | 1 pollen/hour per IP+key |
| Secret | `sk_` | Server-side (production) | **No rate limits** |

### User Tiers
| Tier | Interval | Concurrent | Models | Daily Pollen |
|------|----------|------------|--------|--------------|
| Anonymous | 6-7s | 1 | Restricted | 0 |
| Seed (Free) | 7s | Tier-based | Standard | Small grant |
| Flower (Paid) | 1s | 20 | All | Medium grant |
| Nectar (Enterprise) | 1s | Unlimited | All | Large grant |

### Authenticated (enter.pollinations.ai)
- **Interval**: 1 second (vs 6-7s default)
- **Concurrent**: 20 requests
- **Access**: All models

### Pollen Credits
- $1 ≈ 1 Pollen
- Free models cost 0 Pollen
- Purchased Pollen never expires

---

## ARDK Pipeline Model Assignments

### Universal Model Selection (All Tiers)

Models are **consistent across all tiers** - what differs is the **generation configuration**.

| Pipeline Stage | Primary Model | Fallback | Reason |
|----------------|---------------|----------|--------|
| **Sprite Detection** | `gemini-fast` | `gemini` | Fast vision, accurate bounding boxes |
| **Palette Extraction** | `openai-large` | `gemini-large` | Best color analysis (GPT-5.2) |
| **Sprite Generation** | `flux` | `turbo` | Clean output, good for downsampling |
| **Code Generation** | `qwen-coder` | `deepseek` | Assembly expertise (6502/68K/Z80) |
| **Animation Analysis** | `gemini` | `claude` | Frame detection, timing |
| **Tilemap Analysis** | `gemini-large` | `openai-large` | Pattern recognition |

---

## Per-Tier Image Generation Configuration

Each tier generates at its **"best in class" resolution** to preserve detail for the downsampling/dithering pipeline.

### Tier 0: MINIMAL (NES, GB, GBC, SMS, C64)
**Target**: 4 colors per sprite, 8x8 or 16x16 tiles

```python
TIER_MINIMAL_CONFIG = {
    "model": "flux",
    "width": 256,           # 16x scale of 16px sprite
    "height": 256,
    "seed": 42,
    "prompt_prefix": "pixel art, 8-bit style, limited palette, sharp edges, no anti-aliasing, ",
    "prompt_suffix": ", NES aesthetic, chunky pixels, high contrast",
    "negative": "gradient, smooth shading, blur, soft edges, realistic",

    # Downsampling config
    "target_size": 16,      # Final sprite size
    "colors": 4,            # Max colors per sprite palette
    "dither": "none",       # No dithering for 4-color
    "resampling": "NEAREST" # Preserve hard edges
}
```

### Tier 1: MINIMAL_PLUS (SMS, MSX2, Neo Geo Pocket)
**Target**: 4-16 colors, 8x16 or 16x16 tiles

```python
TIER_MINIMAL_PLUS_CONFIG = {
    "model": "flux",
    "width": 512,           # Higher source resolution
    "height": 512,
    "seed": 42,
    "prompt_prefix": "pixel art, 16-bit handheld style, clean palette, ",
    "prompt_suffix": ", Game Gear aesthetic, vibrant colors",
    "negative": "gradient, blur, realistic, photographic",

    # Downsampling config
    "target_size": 16,
    "colors": 16,
    "dither": "ordered",    # Light ordered dithering OK
    "resampling": "NEAREST"
}
```

### Tier 2: STANDARD (Genesis, SNES, PCE, Amiga OCS)
**Target**: 16 colors per palette, 16x16 to 32x32 tiles

```python
TIER_STANDARD_CONFIG = {
    "model": "flux",
    "width": 1024,          # High detail for downsampling
    "height": 1024,
    "seed": 42,
    "prompt_prefix": "16-bit pixel art, detailed sprites, clean shading, ",
    "prompt_suffix": ", Genesis/SNES quality, smooth color bands",
    "negative": "blur, noise, over-detailed, realistic photo",

    # Downsampling config
    "target_size": 32,
    "colors": 16,
    "dither": "floyd_steinberg",  # FS dithering for gradients
    "resampling": "LANCZOS"       # Better edge preservation
}
```

### Tier 3: STANDARD_PLUS (Neo Geo, 32X, Sega CD)
**Target**: 256 colors, large sprites (64x64+)

```python
TIER_STANDARD_PLUS_CONFIG = {
    "model": "flux",
    "width": 1280,          # Max flux resolution
    "height": 1280,
    "seed": 42,
    "prompt_prefix": "arcade quality sprite, detailed shading, smooth gradients, ",
    "prompt_suffix": ", Neo Geo quality, professional game art",
    "negative": "pixelated, low-res, amateur",

    # Downsampling config
    "target_size": 64,
    "colors": 256,
    "dither": "floyd_steinberg",
    "resampling": "LANCZOS"
}
```

### Tier 4: EXTENDED (GBA, DS, PSP)
**Target**: Full color, high detail

```python
TIER_EXTENDED_CONFIG = {
    "model": "flux",        # Or gptimage-large for 4K
    "width": 1280,
    "height": 1280,
    "seed": 42,
    "prompt_prefix": "high quality game sprite, detailed, professional, ",
    "prompt_suffix": ", handheld console quality, polished",
    "negative": "blurry, low quality",

    # Downsampling config
    "target_size": 128,
    "colors": 256,          # Or 32768 for DS
    "dither": "none",       # Full color, no dithering needed
    "resampling": "LANCZOS"
}
```

---

## Generation-to-Platform Pipeline

The pipeline generates at the **highest tier** needed, then downsamples to all target platforms:

```
┌─────────────────────────────────────────────────────────────────────┐
│  AI Generation (flux @ 1024x1024)                                   │
│  "cyberpunk soldier character, side view, game sprite"              │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  unified_pipeline.py --multi-platform                               │
└─────────────────────────────────────────────────────────────────────┘
          │              │              │              │
          ▼              ▼              ▼              ▼
    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
    │   NES   │    │ Genesis │    │  SNES   │    │   GBA   │
    │ 16x16   │    │  32x32  │    │  32x32  │    │  64x64  │
    │ 4 color │    │16 color │    │16 color │    │256 color│
    │ NEAREST │    │ LANCZOS │    │ LANCZOS │    │ LANCZOS │
    │ no dith │    │ FS dith │    │ FS dith │    │ no dith │
    └─────────┘    └─────────┘    └─────────┘    └─────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
    sprites.chr   sprites.bin   sprites.chr   sprites.raw
```

### Multi-Platform Generation Example

```python
# Generate once, output for all platforms
python tools/unified_pipeline.py \
    --input ai_generated/soldier.png \
    --multi-platform nes,genesis,snes,gba \
    --output assets/processed/

# Output:
# assets/processed/nes/soldier.chr      (4-color, 16x16)
# assets/processed/genesis/soldier.bin  (16-color, 32x32)
# assets/processed/snes/soldier.chr     (16-color, 32x32)
# assets/processed/gba/soldier.raw      (256-color, 64x64)
```

---

## Pipeline Implementation

### Sprite Detection (gemini-fast)
```python
prompt = """Analyze this sprite sheet. Find the FIRST {sprite_type} sprite.
Return ONLY JSON: {"x": <left>, "y": <top>, "width": <w>, "height": <h>}"""
model = "gemini-fast"  # Fast vision, good for bounding boxes
```

### Palette Extraction (openai-large)
```python
prompt = """Analyze colors for NES conversion. Pick 4 NES colors.
First MUST be $0F (black). Pick dark, mid, bright spread.
Return ONLY JSON: {"palette": ["$0F", "$XX", "$XX", "$XX"], "reason": "brief"}"""
model = "openai-large"  # GPT-5.2, best color understanding
max_tokens = 500
```

### Sprite Generation (flux)
```python
url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
params = {
    "model": "flux",
    "width": 1024,
    "height": 1024,
    "seed": 42  # For reproducibility
}
# Flux produces clean, pixel-art friendly output
```

### Code Generation (qwen-coder)
```python
prompt = """Generate 6502 assembly for NES sprite rendering.
Use ca65 syntax. Include OAM DMA setup."""
model = "qwen-coder"  # Specialized for code
```

---

## API Request Examples

### Vision Request (Sprite Detection)
```python
import urllib.request
import json
import base64

payload = {
    "model": "gemini-fast",
    "messages": [{
        "role": "user",
        "content": [
            {"type": "text", "text": "Find sprite bounding box..."},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
        ]
    }],
    "max_tokens": 200
}

headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer sk_pHTAsUugsKvRUwFfxzOnpStVkpROBgzM"
}

req = urllib.request.Request(
    "https://gen.pollinations.ai/v1/chat/completions",
    data=json.dumps(payload).encode(),
    headers=headers
)
```

### Image Generation Request
```
GET https://image.pollinations.ai/prompt/NES%20pixel%20art%20character%2016x16?model=flux&width=256&height=256&seed=42
```

---

## Best Practices

1. **Always use `gemini-fast` for sprite detection** - fastest vision model
2. **Use `openai-large` for palette extraction** - best color understanding (GPT-5.2)
3. **Use `flux` for sprite generation** - cleanest pixel-art output
4. **Use `qwen-coder` for assembly generation** - specialized for code
5. **Set `max_tokens: 500+` for palette extraction** - JSON needs space
6. **Use secret keys (`sk_`) for production** - no rate limits
7. **Implement fallback models** - handle API failures gracefully

---

## Changelog

- **2026-01-12**: Revised per-tier protocols - consistent model choices, tier-specific generation CONFIG
- **2026-01-12**: Complete documentation with confirmed models and pipeline assignments
- **2026-01-05**: Flux model restored, Qwen3-Coder-30B added
- **2025-12-29**: GPT Image 1.5 available as `gptimage-large`
- **2025-12-15**: `openai-large` upgraded to GPT-5.2, Gemini tools enabled
- **2025-12-07**: Video generation (Veo, Seedance), Perplexity/Gemini web search

---

## Sources

- [Pollinations GitHub](https://github.com/pollinations/pollinations)
- [Pollinations API Docs](https://github.com/pollinations/pollinations/blob/main/APIDOCS.md)
- [Pollen FAQ](https://github.com/pollinations/pollinations/blob/master/enter.pollinations.ai/POLLEN_FAQ.md)
