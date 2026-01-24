# Sprite Pipeline Reference (v5.3)

> **Tool**: `tools/unified_pipeline.py`
> **Version**: 5.3 - 17 Retro Platforms
> **Last Updated**: 2026-01-10

Complete reference for the multi-platform sprite processing pipeline.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [How It Works](#how-it-works)
3. [Platform Reference](#platform-reference)
4. [Command Line Options](#command-line-options)
5. [AI Integration](#ai-integration)
6. [Output Files](#output-files)
7. [Troubleshooting](#troubleshooting)
8. [Extending the Pipeline](#extending-the-pipeline)
9. [Palette Quantization Improvements](#palette-quantization-improvements)

---

## Quick Start

```bash
# Process single PNG for NES (default)
python tools/unified_pipeline.py player.png -o output/

# Process for Game Boy
python tools/unified_pipeline.py player.png -o output/ --platform gb

# Batch process entire folder
python tools/unified_pipeline.py --batch gfx/ai_output/ -o gfx/processed/

# With AI labeling (requires API key in .env)
python tools/unified_pipeline.py player.png -o output/ --ai groq
```

---

## How It Works

### Pipeline Stages

```
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 1: LOAD                                                   │
│  - Load PNG file                                                 │
│  - Convert to RGBA mode                                          │
│  - Report dimensions                                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 2: PALETTE EXTRACTION                                     │
│  - Use platform default palette, OR                              │
│  - Use forced palette from --palette flag                        │
│  - NES example: $0F (black), $24 (magenta), $2C (cyan), $30 (white)│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 3: SPRITE DETECTION                                       │
│  - Scan image for non-transparent regions                        │
│  - Create bounding boxes around content                          │
│  - Merge overlapping regions                                     │
│  - Filter out text labels (aspect ratio, fill density heuristics)│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 4: AI LABELING (Optional)                                 │
│  - Send sprite sheet to AI vision model                          │
│  - Get semantic labels: type (player/enemy/item), action (idle/run)│
│  - Cache results to avoid repeated API calls                     │
│  - Fallback chain: Groq → Gemini → OpenAI → Anthropic → Pollinations│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 5: CONVERSION                                             │
│  For each detected sprite:                                       │
│  - Crop from source image                                        │
│  - Scale to target size (platform-specific resampling)           │
│  - Quantize colors to palette (nearest color matching)           │
│  - Generate platform-specific tile data                          │
│  - Save: scaled PNG, indexed PNG, tile data file                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 6: COMBINE                                                │
│  - Concatenate all tile data into single bank file               │
│  - Pad to platform bank size (8KB for NES)                       │
│  - Save metadata.json with sprite info                           │
└─────────────────────────────────────────────────────────────────┘
```

### Color Quantization

The pipeline maps RGB colors to the platform's palette using Euclidean distance:

```python
# For each pixel:
best_color = min(palette_colors, key=lambda c:
    (r - c[0])**2 + (g - c[1])**2 + (b - c[2])**2
)
```

Transparent pixels (alpha < 128) are always mapped to color index 0.

### Resampling Modes

| Mode | Used By | Effect |
|------|---------|--------|
| LANCZOS | NES, SNES, Genesis, Amiga, PCE, SMS, GBA, Neo Geo, Lynx | Smooth downscaling, anti-aliased |
| NEAREST | Game Boy, C64, CGA, Atari 2600, MSX | Sharp pixels, authentic retro look |

---

## Platform Reference

### Nintendo Platforms

#### NES / Famicom
```
Aliases:    nes, famicom
Colors:     4 per sprite (3 + transparent)
Bit Depth:  2bpp
Tile Size:  8x8 pixels
Format:     CHR (2 bitplanes, 8 bytes each)
Extension:  .chr
Bytes/Tile: 16

Palette Format: NES PPU indices ($00-$3F)
Default:    $0F (black), $24 (magenta), $2C (cyan), $30 (white)
```

#### Game Boy (DMG)
```
Aliases:    gb, gameboy, dmg
Colors:     4 shades of green
Bit Depth:  2bpp
Tile Size:  8x8 pixels
Format:     2bpp interleaved (same as NES CHR)
Extension:  .2bpp
Bytes/Tile: 16
Resampling: NEAREST

Fixed Palette (DMG-01 LCD):
  0: (155, 188, 15)  - Lightest
  1: (139, 172, 15)  - Light
  2: (48, 98, 48)    - Dark
  3: (15, 56, 15)    - Darkest
```

#### Game Boy Color
```
Aliases:    gbc, gameboycolor, cgb
Colors:     4 per palette, 8 palettes (32 sprite colors)
Bit Depth:  2bpp tiles, 15-bit RGB palette
Tile Size:  8x8 pixels
Format:     2bpp (same as DMG)
Extension:  .2bpp
Bytes/Tile: 16
Resampling: NEAREST

Palette Format: 15-bit RGB (0BBBBBGGGGGRRRRR)
Default:    0x0000 (black), 0x7C1F (magenta), 0x03FF (cyan), 0x7FFF (white)
```

#### SNES / Super Famicom
```
Aliases:    snes, superfamicom, sfc
Colors:     16 per palette (15 + transparent)
Bit Depth:  4bpp
Tile Size:  8x8 pixels
Format:     4bpp interleaved bitplanes
Extension:  .bin
Bytes/Tile: 32

Palette Format: 15-bit RGB (0BBBBBGGGGGRRRRR)
```

#### Game Boy Advance
```
Aliases:    gba, gameboyadvance, advance
Colors:     16 per palette (256 total sprite colors)
Bit Depth:  4bpp (or 8bpp mode)
Tile Size:  8x8 pixels
Max Sprite: 64x64 pixels
Format:     4bpp linear, 2 pixels per byte, little-endian
Extension:  .gba
Bytes/Tile: 32

Palette Format: 15-bit RGB (0BBBBBGGGGGRRRRR)
Note: Low nibble stored first (opposite of Genesis)
```

### Sega Platforms

#### Genesis / Megadrive
```
Aliases:    genesis, megadrive, md
Colors:     16 per palette (15 + transparent)
Bit Depth:  4bpp
Tile Size:  8x8 pixels
Format:     4bpp packed (2 pixels per byte)
Extension:  .bin
Bytes/Tile: 32

Palette Format: 9-bit RGB (0000BBB0GGG0RRR0)
```

#### Master System / Game Gear
```
Aliases:    sms, mastersystem, gamegear, gg
Colors:     16 per palette
Bit Depth:  4bpp
Tile Size:  8x8 pixels
Format:     4bpp planar (4 bitplanes interleaved per row)
Extension:  .sms
Bytes/Tile: 32

SMS Palette: 6-bit RGB (00BBGGRR, 64 colors)
Game Gear:  12-bit RGB (4096 colors)
```

### Other Consoles

#### PC Engine / TurboGrafx-16
```
Aliases:    pce, pcengine, turbografx, tg16
Colors:     16 per palette
Bit Depth:  4bpp
Tile Size:  8x8 pixels
Format:     4bpp interleaved (same as SNES)
Extension:  .bin
Bytes/Tile: 32

Palette Format: 9-bit RGB (GGGRRRBBB)
```

#### Atari 2600
```
Aliases:    atari2600, vcs, 2600
Colors:     2 (foreground + background)
Bit Depth:  1bpp
Tile Size:  8x1 (scanline-based)
Format:     1 byte per scanline
Extension:  .a26
Bytes/Line: 1
Resampling: NEAREST

Note: 2600 has no tile system. Output is raw player graphics data.
Each byte represents 8 horizontal pixels for one scanline.
```

#### Atari Lynx
```
Aliases:    lynx, atarilynx
Colors:     16 per sprite from 4096
Bit Depth:  4bpp
Tile Size:  8x8 pixels
Max Sprite: Unlimited (memory dependent)
Format:     4bpp packed (2 pixels per byte)
Extension:  .lnx
Bytes/Tile: 32

Palette Format: 12-bit RGB with unusual order (GGGG BBBB RRRR)
Note: Lynx hardware can RLE-compress sprites automatically.
```

#### MSX / MSX2
```
Aliases:    msx, msx1, msx2
Colors:     16 (fixed TMS9918) or 16 from 512 (MSX2)
Bit Depth:  4bpp
Tile Size:  8x8 pixels
Sprite Size: 8x8 or 16x16
Format:     1bpp pattern with color attributes
Extension:  .msx
Bytes/Tile: 8 (1bpp pattern)
Resampling: NEAREST

MSX1 TMS9918 Fixed Palette (16 colors):
  0: Transparent   8: Medium Red
  1: Black         9: Light Red
  2: Medium Green  10: Dark Yellow
  3: Light Green   11: Light Yellow
  4: Dark Blue     12: Dark Green
  5: Light Blue    13: Magenta
  6: Dark Red      14: Gray
  7: Cyan          15: White
```

### SNK Platforms

#### Neo Geo (MVS/AES)
```
Aliases:    neogeo, neo, mvs, aes
Colors:     16 per palette (256+ on screen)
Bit Depth:  4bpp
Tile Size:  16x16 pixels (fixed)
Max Sprite: 16 wide × 512 tall (32 tiles!)
Format:     Planar, 4 bitplanes interleaved per row
Extension:  .neo
Bytes/Tile: 128

Palette Format: 16-bit (D RRRRR GGGGG BBBBB)
  D = Dark bit (adds ~6% brightness)
  Each channel: 5 bits = 32 levels

Note: Neo Geo sprites are always 16 pixels wide.
      Wider sprites are created by chaining multiple sprites.
      Vertical sprites can be up to 32 tiles (512 pixels) tall.
```

### Computer Platforms

#### Commodore Amiga (OCS/ECS)
```
Aliases:    amiga, amigaocs, amigaecs
Colors:     32 (5 bitplanes)
Bit Depth:  5bpp
Tile Size:  16x16 pixels (blitter preference)
Format:     Planar (separate bitplanes)
Extension:  .raw
Bytes/Tile: 160

Palette Format: 12-bit RGB (0x0RGB, 4096 colors)
```

#### Commodore Amiga (AGA)
```
Aliases:    amigaaga, aga, a1200, a4000
Colors:     256 (8 bitplanes)
Bit Depth:  8bpp
Tile Size:  16x16 pixels
Format:     Planar (8 bitplanes)
Extension:  .raw
Bytes/Tile: 256

Palette Format: 24-bit RGB (16M colors)
```

#### Commodore 64
```
Aliases:    c64, commodore64, vic20
Colors:     4 per sprite (from 16 fixed)
Bit Depth:  2bpp
Sprite Size: 24x21 pixels (hardware limit)
Format:     1bpp hires or 2bpp multicolor
Extension:  .spr
Bytes/Sprite: 64
Resampling: NEAREST

Fixed VIC-II Palette (16 colors):
  0: Black       8: Orange
  1: White       9: Brown
  2: Red        10: Light Red
  3: Cyan       11: Dark Grey
  4: Purple     12: Grey
  5: Green      13: Light Green
  6: Blue       14: Light Blue
  7: Yellow     15: Light Grey

Default: 0 (black), 4 (purple), 3 (cyan), 1 (white)
```

#### IBM CGA
```
Aliases:    cga, ibmpc
Colors:     4 (fixed palettes)
Bit Depth:  2bpp
Tile Size:  8x8 pixels
Format:     2bpp (4 pixels per byte)
Extension:  .cga
Bytes/Tile: 16
Resampling: NEAREST

Palette 0 (Low):  Black, Green, Red, Brown
Palette 0 (High): Black, Light Green, Light Red, Yellow
Palette 1 (Low):  Black, Cyan, Magenta, Light Grey
Palette 1 (High): Black, Light Cyan, Light Magenta, White  ← Default

Default uses Palette 1 High for synthwave look.
```

---

## Command Line Options

```
usage: unified_pipeline.py [-h] -o OUTPUT [--batch BATCH]
                           [--platform PLATFORM] [--size SIZE]
                           [--palette PALETTE] [--category CATEGORY]
                           [--ai {groq,gemini,openai,anthropic,grok,xai,pollinations}]
                           [--no-ai] [--no-text-filter]
                           [input]

Arguments:
  input                 Input PNG file (required unless --batch)
  -o, --output         Output directory (required)
  --batch              Batch process all PNGs in directory
  --platform, -p       Target platform (default: nes)
  --size               Target sprite size in pixels (default: 32)
  --palette            Force palette, e.g., "0F,24,2C,30" for NES
  --category           Asset category hint (player, enemy, item, etc.)
  --ai                 Preferred AI provider for labeling
  --no-ai              Disable AI analysis completely
  --no-text-filter     Keep text labels (don't filter them out)
```

### Examples

```bash
# Basic NES processing
python tools/unified_pipeline.py sprite.png -o output/

# 16x16 sprites for NES
python tools/unified_pipeline.py items.png -o output/ --size 16

# Custom synthwave palette
python tools/unified_pipeline.py player.png -o output/ --palette 0F,15,2C,30

# Game Boy with AI labeling
python tools/unified_pipeline.py enemies.png -o output/ --platform gb --ai groq

# Genesis batch processing
python tools/unified_pipeline.py --batch gfx/ai_output/ -o gfx/genesis/ --platform genesis

# Disable text filtering (keep all detected regions)
python tools/unified_pipeline.py sheet.png -o output/ --no-text-filter
```

---

## AI Integration

### Supported Providers

| Provider | Speed | Cost | API Key Env Var |
|----------|-------|------|-----------------|
| Groq | Fastest | Free tier | `GROQ_API_KEY` |
| Gemini | Fast | Free tier | `GEMINI_API_KEY` |
| OpenAI | Medium | Paid | `OPENAI_API_KEY` |
| Anthropic | Medium | Paid | `ANTHROPIC_API_KEY` |
| Grok/xAI | Medium | Paid | `XAI_API_KEY` |
| Pollinations | Slow | Free | `POLLINATIONS_API_KEY` |

### Setup

Create `.env` file in project root:
```
GROQ_API_KEY=gsk_your_key_here
GEMINI_API_KEY=AIza_your_key_here
```

### What AI Does

The AI analyzes the sprite sheet image and returns:
- **type**: player, enemy, item, vfx, boss, etc.
- **action**: idle, run, attack, jump, death, etc.
- **description**: Semantic name like "synthwave_hero_idle"

This information is used for:
- Naming output files (e.g., `sprite_01_synthwave_hero_idle.chr`)
- Organizing sprites by type
- Generating meaningful metadata

### Fallback Chain

If preferred provider fails, pipeline tries others in order:
```
Groq → Gemini → OpenAI → Anthropic → Grok → Pollinations
```

---

## Output Files

### Directory Structure
```
output/
├── metadata.json              # Sprite info, palette, settings
├── sprites.chr                # Combined tile bank (platform format)
├── sprite_01_hero_idle.chr    # Individual sprite tiles
├── sprite_01_hero_idle_scaled.png    # Resized RGBA
├── sprite_01_hero_idle_indexed.png   # Quantized palette
├── sprite_02_hero_run.chr
├── sprite_02_hero_run_scaled.png
├── sprite_02_hero_run_indexed.png
└── ...
```

### metadata.json
```json
{
  "source": "gfx/ai_output/player.png",
  "timestamp": "2026-01-10T12:00:00",
  "platform": "NES",
  "target_size": 32,
  "colors_per_palette": 4,
  "bits_per_pixel": 2,
  "tile_format": ".chr",
  "unified_palette": [15, 36, 44, 48],
  "palette_hex": "$0F, $24, $2C, $30",
  "ai_provider": "Groq",
  "sprites_count": 5,
  "sprites": [
    {
      "id": 1,
      "type": "player",
      "action": "idle",
      "description": "synthwave_hero_idle",
      "frame": 1,
      "bbox": {"x": 10, "y": 20, "width": 64, "height": 64},
      "tile_file": "sprite_01_synthwave_hero_idle.chr",
      "tile_size": 256
    }
  ]
}
```

---

## Troubleshooting

### "No sprites detected"
- Check if image has transparency (PNG with alpha channel)
- Sprites must be non-black, non-transparent regions
- Try `--no-text-filter` to see all detected regions
- Increase brightness threshold if sprites are too dark

### Sprites look wrong after conversion
- Verify palette matches your game's palette
- Check that source colors are close to palette colors
- Use `--palette` to force specific colors
- View the `_indexed.png` files to see quantization result

### CHR file wrong size
- NES CHR should be 16 bytes per 8x8 tile
- 32x32 sprite = 16 tiles = 256 bytes
- Combined bank is padded to 8KB (8192 bytes)

### AI not working
- Check `.env` file has valid API key
- Try different provider with `--ai gemini`
- Use `--no-ai` to skip AI and use default labels
- Check console for rate limit or API errors

### Colors look washed out
- NES colors are limited to 2C02 PPU palette
- Some RGB colors have no close NES equivalent
- Edit source art to use colors closer to target palette
- View NES palette: https://www.nesdev.org/wiki/PPU_palettes

---

## Extending the Pipeline

### Adding New Platform

1. Create new PlatformConfig class:
```python
class MyPlatformConfig(PlatformConfig):
    name = "MyPlatform"
    tile_width = 8
    tile_height = 8
    bits_per_pixel = 4
    colors_per_palette = 16
    output_extension = ".myp"

    palette_rgb = {0: (0,0,0), 1: (255,0,0), ...}
    default_palette = [0, 1, 2, 3, ...]

    @classmethod
    def generate_tile_data(cls, indexed_img):
        # Convert indexed image to platform format
        pixels = list(indexed_img.getdata())
        # ... conversion logic ...
        return bytes(tile_data)
```

2. Add to PLATFORMS registry:
```python
PLATFORMS['myplatform'] = MyPlatformConfig
PLATFORMS['mp'] = MyPlatformConfig  # Alias
```

### Custom Palette Extraction

Override `PaletteExtractor.extract_from_image()` to use different algorithm:
- K-means clustering
- Median cut
- Octree quantization

### Custom Sprite Detection

Override `ContentDetector.detect()` for different detection methods:
- Edge detection
- Grid-based extraction
- Manual bounding boxes from config file

---

## Self-Healing Validations

The pipeline includes automatic checks:

```python
# Dimension validation
if width % 8 != 0 or height % 8 != 0:
    print("[WARN] Dimensions not tile-aligned, will be padded")

# Sprite count check
if len(sprites) > 64:
    print("[WARN] Too many sprites for NES OAM (64 max)")

# CHR size validation
expected_size = (width // 8) * (height // 8) * bytes_per_tile
if len(chr_data) != expected_size:
    print(f"[ERROR] CHR size mismatch: {len(chr_data)} vs {expected_size}")

# Empty sprite detection
if len(sprites) == 0:
    print("[ERROR] No sprites detected - check source image")
```

---

## Palette Quantization Improvements

The current pipeline uses simple Euclidean distance in RGB color space for palette mapping. This section documents available libraries and techniques for improved quantization quality.

### Current Approach (v5.3)

```python
# Simple RGB Euclidean distance
for i, pal_rgb in enumerate(palette):
    dist = (r - pal_rgb[0])**2 + (g - pal_rgb[1])**2 + (b - pal_rgb[2])**2
    if dist < min_dist:
        best_idx = i
```

**Pros**: Fast, simple, no dependencies
**Cons**: Doesn't match human color perception, poor results with limited palettes

### Recommended Improvements

#### 1. Perceptual Color Space (CIELAB)

Convert to CIELAB (L*a*b*) color space before distance calculation. Human eyes perceive color differences more accurately in this space.

```python
# Using colour-science library
pip install colour-science

from colour import sRGB_to_XYZ, XYZ_to_Lab

def perceptual_distance(rgb1, rgb2):
    lab1 = XYZ_to_Lab(sRGB_to_XYZ(np.array(rgb1) / 255))
    lab2 = XYZ_to_Lab(sRGB_to_XYZ(np.array(rgb2) / 255))
    return np.sum((lab1 - lab2) ** 2)
```

**Best for**: All platforms, especially those with limited palettes (NES, GB, C64)

#### 2. libimagequant (pngquant)

Industry-standard library for high-quality palette quantization. Used by pngquant, which produces excellent results.

```python
# Python binding
pip install imagequant

import imagequant

liq = imagequant.LIQ()
liq.set_max_colors(16)  # Platform palette size
result = liq.quantize(rgba_pixels, width, height)
indexed = result.remap()
palette = result.get_palette()
```

**Pros**: Best quality for generating optimal palettes, dithering support
**Cons**: Generates its own palette (need to remap to fixed platform palette)
**Best for**: Amiga, SNES, Genesis (platforms with flexible palettes)

#### 3. Pillow Quantization Modes

Built-in to Pillow, no extra dependencies.

```python
from PIL import Image

# MEDIANCUT - Fast, good quality
img.quantize(colors=16, method=Image.MEDIANCUT)

# MAXCOVERAGE - Better color coverage
img.quantize(colors=16, method=Image.MAXCOVERAGE)

# FASTOCTREE - Very fast, acceptable quality
img.quantize(colors=16, method=Image.FASTOCTREE)

# LIBIMAGEQUANT - Best quality (if available)
img.quantize(colors=16, method=Image.LIBIMAGEQUANT)
```

**Best for**: Quick improvements with no extra dependencies

#### 4. scikit-image K-Means

More control over clustering algorithm.

```python
pip install scikit-image

from skimage import color
from sklearn.cluster import KMeans

# Convert to LAB for perceptual clustering
lab = color.rgb2lab(img_rgb)
pixels = lab.reshape(-1, 3)

kmeans = KMeans(n_clusters=16, random_state=42)
labels = kmeans.fit_predict(pixels)
centers = kmeans.cluster_centers_
```

**Best for**: Custom palette extraction from source art

#### 5. Dithering Options

For retro platforms, ordered dithering can improve perceived color depth.

```python
# Floyd-Steinberg (error diffusion)
indexed = img.convert('P', palette=Image.ADAPTIVE, colors=4, dither=Image.FLOYDSTEINBERG)

# Ordered dithering (Bayer matrix) - more retro look
# Implement 4x4 or 8x8 Bayer matrix
BAYER_4x4 = [
    [ 0,  8,  2, 10],
    [12,  4, 14,  6],
    [ 3, 11,  1,  9],
    [15,  7, 13,  5]
]
```

**Best for**: Atari 2600, C64, Game Boy (1bpp or 2bpp platforms)

### API and Cloud Options

#### Replicate.com
Hosts ML models for image processing. Can do style transfer, super-resolution before quantization.

```python
import replicate

output = replicate.run(
    "stability-ai/stable-diffusion",
    input={"prompt": "pixel art style, 16 colors", "image": img}
)
```

#### Remove.bg / PhotoRoom API
Clean up sprites, remove backgrounds before processing.

```python
import requests

response = requests.post(
    'https://api.remove.bg/v1.0/removebg',
    files={'image_file': open('sprite.png', 'rb')},
    headers={'X-Api-Key': API_KEY}
)
```

### Integration Roadmap

**Phase 1** (Low effort, high impact):
- [ ] Add CIELAB distance option (`--quantize lab`)
- [ ] Use Pillow's LIBIMAGEQUANT when available

**Phase 2** (Medium effort):
- [ ] Add Floyd-Steinberg dithering option (`--dither fs`)
- [ ] Add ordered dithering option (`--dither bayer`)

**Phase 3** (Higher effort):
- [ ] Implement palette optimization for flexible-palette platforms
- [ ] Add preview mode to compare quantization methods

### Library Comparison

| Library | Quality | Speed | Dependencies | Best For |
|---------|---------|-------|--------------|----------|
| RGB Euclidean | ★★☆☆☆ | ★★★★★ | None | Quick & dirty |
| colour-science | ★★★★☆ | ★★★★☆ | numpy | Perceptual accuracy |
| libimagequant | ★★★★★ | ★★★☆☆ | C library | Best overall quality |
| Pillow MEDIANCUT | ★★★☆☆ | ★★★★★ | None | No-dependency upgrade |
| scikit-image | ★★★★☆ | ★★★☆☆ | numpy, scipy | Custom analysis |

### Platform-Specific Recommendations

| Platform | Recommended Method | Notes |
|----------|-------------------|-------|
| NES | CIELAB distance | Fixed palette, perceptual matching critical |
| Game Boy | Ordered dithering | 4 shades benefit from dithering |
| SNES/GBA | libimagequant | Flexible palette, can optimize |
| Genesis | CIELAB + dithering | 9-bit color, limited but flexible |
| Neo Geo | libimagequant | Large palette space |
| C64 | Ordered dithering | Fixed palette, dithering essential |
| Amiga | libimagequant | HAM mode can use different approach |

---

*This reference covers unified_pipeline.py v5.3. Update when pipeline changes.*
