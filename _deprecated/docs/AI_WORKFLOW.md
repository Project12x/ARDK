# AI-Accelerated Asset Workflow

**Purpose**: Leverage AI APIs (Gemini, Groq, rembg) for professional sprite extraction and processing

**Status**: Planning phase - homegrown solution working, API integration next

---

## Current Homegrown Pipeline (Working)

### Step 1: Background Removal
```bash
python tools/remove_background.py \
    gfx/ai_output/input.png \
    gfx/processed/nobg.png \
    --method edges
```

**Method**: Flood-fill edge detection
- Assumes background connects to edges
- Works for: Single sprites, sprite sheets with borders
- Limitations: Fails if sprite touches edges, mixed backgrounds

### Step 2: Color Quantization
```bash
python tools/process_ai_assets_v2.py \
    gfx/processed/nobg.png \
    gfx/processed/indexed.png \
    --size 128x128
```

**Method**: Smart brightness-based quantization
- Maps colors to 4 NES palette indices based on distribution
- Palette: Black (0), Magenta ($24), Cyan ($1C), White ($30)
- Limitations: Fixed palette, doesn't optimize per-sprite

### Step 3: CHR Conversion
```bash
python tools/png2chr.py \
    gfx/processed/indexed.png \
    src/game/assets/output.chr
```

**Method**: Direct PNG → CHR tile encoding
- Converts 8x8 tiles to NES 2-bitplane format
- Requires indexed PNG with exactly 4 colors

### Step 4: Sprite Analysis
```bash
# Find best tiles for sprites
python tools/analyze_sprites.py gfx/processed/indexed.png
```

**Output**: Tile density map, metatile suggestions

---

## Proposed AI-Accelerated Pipeline

### Architecture

```
AI Input PNG → AI API → Enhanced Processing → CHR → ROM
     ↓           ↓              ↓            ↓      ↓
  512x512    Segment      Quantize      Encode  Test
            Classify      Optimize      Verify  Refine
```

### API Options

#### Option 1: Gemini Vision API
- **Use Case**: Sprite segmentation, classification
- **Advantages**:
  - Multimodal (image + text prompts)
  - Can identify sprite types (player, enemy, item)
  - Can detect sprite boundaries automatically
- **Implementation**:
  ```python
  import google.generativeai as genai

  model = genai.GenerativeModel('gemini-1.5-flash')
  response = model.generate_content([
      "Identify all individual sprites in this sprite sheet. "
      "For each sprite, provide: bounding box (x,y,w,h), "
      "classification (player/enemy/item/vfx), "
      "suggested color palette.",
      image_data
  ])
  ```

#### Option 2: Groq API (Fast Inference)
- **Use Case**: Rapid batch processing
- **Advantages**: Extremely fast (400+ tokens/sec)
- **Implementation**: Similar to Gemini, optimized for speed

#### Option 3: rembg (Background Removal)
- **Use Case**: Professional background removal
- **Advantages**:
  - ML-based, handles complex backgrounds
  - Works with sprites touching edges
  - No cloud API needed (runs locally)
- **Installation**: `pip install rembg`
- **Implementation**:
  ```python
  from rembg import remove

  input_image = Image.open('input.png')
  output_image = remove(input_image)
  output_image.save('output_nobg.png')
  ```

### Proposed Workflow v2.0

```python
# tools/ai_process_sprites.py

import os
from PIL import Image
from rembg import remove
import google.generativeai as genai

def process_sprite_sheet_ai(input_path, output_dir):
    """
    AI-accelerated sprite sheet processing

    Args:
        input_path: Path to AI-generated sprite sheet
        output_dir: Output directory for processed sprites

    Returns:
        List of processed sprite metadata
    """

    # Step 1: Remove background with rembg (ML-based)
    print("[1/5] Removing background (ML)...")
    img = Image.open(input_path)
    img_nobg = remove(img)

    # Step 2: Analyze with Gemini Vision
    print("[2/5] Analyzing sprites (Gemini)...")
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = """
    Analyze this sprite sheet. Return JSON with:
    {
      "sprites": [
        {
          "bbox": [x, y, width, height],
          "type": "player|enemy|item|vfx",
          "dominant_colors": ["#RRGGBB", ...],
          "suggested_nes_palette": ["$00", "$24", "$1C", "$30"]
        }
      ]
    }
    """

    response = model.generate_content([prompt, img_nobg])
    sprite_data = json.loads(response.text)

    # Step 3: Extract individual sprites
    print("[3/5] Extracting sprites...")
    extracted = []
    for sprite_info in sprite_data['sprites']:
        x, y, w, h = sprite_info['bbox']
        sprite_img = img_nobg.crop((x, y, x+w, y+h))

        # Resize to NES-friendly dimensions (multiple of 8)
        w_nes = ((w + 7) // 8) * 8
        h_nes = ((h + 7) // 8) * 8
        sprite_img = sprite_img.resize((w_nes, h_nes), Image.NEAREST)

        extracted.append((sprite_img, sprite_info))

    # Step 4: Optimize palette per sprite
    print("[4/5] Optimizing palettes...")
    for sprite_img, info in extracted:
        palette = optimize_nes_palette(sprite_img, info['suggested_nes_palette'])
        indexed = quantize_to_palette(sprite_img, palette)

        # Save processed sprite
        sprite_name = f"{info['type']}_{len(extracted)}.png"
        indexed.save(os.path.join(output_dir, sprite_name))

    # Step 5: Generate CHR and metadata
    print("[5/5] Generating CHR...")
    generate_chr_from_sprites(extracted, output_dir)

    return extracted

def optimize_nes_palette(img, suggested):
    """
    Optimize 4-color NES palette based on actual sprite colors

    Uses k-means clustering to find best 3 colors (+ transparent)
    """
    from sklearn.cluster import KMeans

    pixels = list(img.getdata())
    non_transparent = [p for p in pixels if p[3] > 0]

    if len(non_transparent) < 3:
        return suggested  # Use AI suggestion if not enough data

    # Cluster into 3 colors
    kmeans = KMeans(n_clusters=3, n_init=10)
    kmeans.fit(non_transparent)
    centers = kmeans.cluster_centers_

    # Map to nearest NES colors
    nes_palette = [0x0F]  # Black (transparent)
    for color in centers:
        nes_palette.append(map_to_nes_color(color))

    return nes_palette

def map_to_nes_color(rgb):
    """Map RGB to nearest NES palette color"""
    NES_PALETTE = {
        0x24: (252, 56, 228),   # Magenta
        0x1C: (0, 228, 252),    # Cyan
        0x30: (252, 252, 252),  # White
        # ... full NES palette
    }

    min_dist = float('inf')
    best_color = 0x30

    for nes_idx, nes_rgb in NES_PALETTE.items():
        dist = sum((a-b)**2 for a, b in zip(rgb, nes_rgb))
        if dist < min_dist:
            min_dist = dist
            best_color = nes_idx

    return best_color
```

### Integration with Build System

```batch
REM build_assets_ai.bat

@echo off
echo ========================================
echo  AI-Accelerated Asset Pipeline
echo ========================================

REM Ensure API keys are set
if "%GEMINI_API_KEY%"=="" (
    echo ERROR: GEMINI_API_KEY not set
    exit /b 1
)

REM Process all AI-generated assets
echo [1/3] Processing player sprites...
python tools/ai_process_sprites.py ^
    gfx/ai_output/player_rad_90s.png ^
    gfx/processed/player ^
    --type player

echo [2/3] Processing enemies...
python tools/ai_process_sprites.py ^
    gfx/ai_output/enemies_synthwave.png ^
    gfx/processed/enemies ^
    --type enemy

echo [3/3] Processing items...
python tools/ai_process_sprites.py ^
    gfx/ai_output/items_projectiles.png ^
    gfx/processed/items ^
    --type item

echo.
echo ========================================
echo  Assets processed! Building ROM...
echo ========================================

REM Continue with normal build
call compile.bat
```

---

## Best Practices

### 1. API Key Management
```bash
# .env file (DO NOT COMMIT)
GEMINI_API_KEY=your_key_here
GROQ_API_KEY=your_key_here

# Load in scripts
from dotenv import load_dotenv
load_dotenv()
```

### 2. Caching API Responses
```python
import hashlib
import json

def cached_ai_call(image_path, prompt):
    """Cache expensive AI API calls"""
    cache_key = hashlib.md5(f"{image_path}{prompt}".encode()).hexdigest()
    cache_file = f".cache/ai_{cache_key}.json"

    if os.path.exists(cache_file):
        with open(cache_file) as f:
            return json.load(f)

    # Make API call
    response = call_ai_api(image_path, prompt)

    # Save to cache
    os.makedirs('.cache', exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(response, f)

    return response
```

### 3. Fallback to Homegrown
```python
def process_with_fallback(image_path):
    """Try AI, fall back to homegrown if fails"""
    try:
        return process_sprite_sheet_ai(image_path)
    except Exception as e:
        print(f"AI processing failed: {e}")
        print("Falling back to homegrown pipeline...")
        return process_sprite_sheet_homegrown(image_path)
```

### 4. Quality Validation
```python
def validate_chr_output(chr_path):
    """Ensure CHR has visible data"""
    with open(chr_path, 'rb') as f:
        data = f.read()

    non_zero = sum(1 for byte in data if byte != 0)
    ratio = non_zero / len(data)

    if ratio < 0.05:  # Less than 5% non-zero
        raise ValueError(f"CHR appears empty: {ratio*100:.1f}% non-zero")

    print(f"✓ CHR validation passed: {ratio*100:.1f}% non-zero bytes")
```

---

## Implementation Timeline

### Phase 1: rembg Integration (Immediate)
- **Goal**: Replace edge-detection with ML background removal
- **Effort**: 1-2 hours
- **Files**: `tools/remove_background_ml.py`

### Phase 2: Gemini Sprite Analysis (Next)
- **Goal**: Auto-detect sprite boundaries and types
- **Effort**: 4-6 hours
- **Files**: `tools/ai_analyze_sprites.py`

### Phase 3: End-to-End Pipeline (Final)
- **Goal**: Single command to process all assets
- **Effort**: 2-3 hours
- **Files**: `tools/ai_process_sprites.py`, `build_assets_ai.bat`

---

## Cost Considerations

### Gemini Flash API
- **Rate**: $0.075 per 1M input tokens
- **Image**: ~258 tokens per image
- **Cost per sprite sheet**: ~$0.00002 (negligible)

### Groq API
- **Rate**: Free tier available
- **Speed**: 10x faster than Gemini

### rembg
- **Cost**: Free (runs locally)
- **Requirements**: ~2GB RAM for model

**Total estimated cost**: < $1/month for active development

---

## Next Steps

1. **Test current ROM** - Verify tiles $75, $76, $85, $86 display correctly
2. **Install rembg** - `pip install rembg`
3. **Get API keys** - Register for Gemini API
4. **Implement Phase 1** - ML background removal
5. **Validate results** - Compare with homegrown pipeline
6. **Scale to full pipeline** - Process all 21 AI assets

---

## Notes

- Keep homegrown pipeline as fallback
- Cache all AI API responses
- Validate CHR output before building ROM
- Document tile indices in `sprite_tiles.inc`
- Version control processed assets separately from source
