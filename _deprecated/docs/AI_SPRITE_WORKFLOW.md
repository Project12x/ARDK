# AI-Accelerated Sprite Workflow for NEON SURVIVORS

**Status**: ✅ Fully Operational
**Powered by**: Gemini 2.5 Flash Vision API
**Last Updated**: January 9, 2026

---

## Overview

This workflow uses Google's Gemini AI to automatically process sprite sheets, extracting and organizing sprites with natural language labels.

### What It Does

1. **Analyzes** sprite sheets with AI vision
2. **Identifies** individual sprites and animations
3. **Labels** sprites with natural language descriptions
4. **Extracts** sprites with proper boundaries
5. **Removes** backgrounds intelligently
6. **Converts** to NES 4-color palette
7. **Generates** CHR files for NES hardware
8. **Organizes** into folders by type/action

### Capabilities

- ✅ Detects sprites automatically (no manual cropping!)
- ✅ Handles unexpected objects ("exploding watermelon", "pizza slice", etc.)
- ✅ Creates custom categories when needed
- ✅ Organizes by type AND action
- ✅ Generates descriptive filenames
- ✅ Batch processes entire folders
- ✅ Creates searchable catalogs

---

## Quick Start

### Single Sprite Sheet

```bash
python tools/ai_sprite_processor.py gfx/ai_output/player_rad_90s.png --output gfx/processed/player_ai
```

### Batch Process All Sheets

```bash
# Windows
process_all_sprites.bat

# Linux/Mac
./process_all_sprites.sh  # (TODO: create this)
```

### Generate Catalog

```bash
python tools/generate_sprite_catalog.py gfx/processed/batch --output docs/SPRITE_CATALOG.md --asm src/game/sprite_tiles.inc
```

---

## Example Output

### Input
AI-generated 1024x1024 sprite sheet: `player_rad_90s.png`

### AI Analysis
Gemini identifies:
- **3 sprite groups** detected
- **Idle animation**: "Player character idle animation frames, showing slight weight shifts"
- **Running**: "Player character running animation frames, depicting forward movement"
- **Shooting**: "Player character shooting animation frames, including holding a weapon"

### Organized Output
```
gfx/processed/player_ai/
├── player/
│   ├── idle/
│   │   ├── player_character_idle_animation_frames.chr (228 tiles)
│   │   └── player_character_idle_animation_frames.png
│   ├── running/
│   │   ├── player_character_running_animation_frames.chr (156 tiles)
│   │   └── player_character_running_animation_frames.png
│   └── shooting/
│       ├── player_character_shooting_animation_frames.chr (108 tiles)
│       └── player_character_shooting_animation_frames.png
├── analysis.json
└── metadata.json
```

---

## Handling Unexpected Objects

The AI is trained to handle ANY sprite, even unexpected ones:

### Examples

| Sprite | Type | Action | Description |
|--------|------|--------|-------------|
| Watermelon | `food` | `exploding` | "exploding watermelon with juice spray" |
| Pizza | `powerup` | `spinning` | "pizza slice spinning animation" |
| Boombox | `decoration` | `static` | "retro 80s boombox with speakers" |
| Skateboard | `vehicle` | `rolling` | "skateboard with motion lines" |
| Laser | `projectile` | `firing` | "neon pink laser beam" |

### How It Works

1. **AI decides category**: If standard types don't fit, creates custom category
2. **Natural language**: Describes what it sees creatively
3. **Auto-organizes**: Places in `type/action/` folder structure

---

## Configuration

### API Key Setup

1. Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create `.env` file:
   ```
   GEMINI_API_KEY=your_key_here
   ```
3. API key is cached and reused

### Free Tier Limits

- **Rate**: 15 requests per minute
- **Daily**: 1500 requests per day
- **Image**: Up to 4MB per image

**Tip**: Use `--no-cache` flag to bypass cache if needed

---

## Advanced Usage

### Filter by Type

```bash
# Extract only player sprites
python tools/ai_sprite_processor.py input.png --output out/ --type player

# Extract only items
python tools/ai_sprite_processor.py input.png --output out/ --type item
```

### Custom Prompts (Advanced)

Edit `tools/ai_sprite_processor.py` line 114-159 to customize the AI prompt:
- Add game-specific terminology
- Request specific attributes
- Guide classification logic

### Fallback to Homegrown

If AI fails, processor automatically falls back to:
1. Built-in background removal (edge detection)
2. Built-in CHR converter (png2chr algorithm)
3. Saves debug images for manual inspection

---

## Troubleshooting

### "Quota Exceeded" Error

**Cause**: Free tier rate limit hit
**Solution**: Wait 60 seconds and retry, or upgrade to paid tier

### "Empty CHR Files" Error

**Cause**: Background removal was too aggressive
**Solution**:
1. Check `debug_analysis_image.png`
2. Manually adjust `sprite_*_nobg.png` if needed
3. Re-run CHR conversion only

### "Sprites Too Small" Warning

**Cause**: AI bounding boxes were tight
**Solution**: AI now uses generous boundaries. Clear cache and re-analyze.

---

## Workflow Integration

### Step 1: Generate Sprites (External)

Use AI image generators:
- **Midjourney**: "NES pixel art sprite sheet, rad 90s character"
- **DALL-E**: "8-bit NES style sprite sheet, synthwave colors"
- **Stable Diffusion**: Custom LoRA for NES aesthetics

Save to: `gfx/ai_output/`

### Step 2: Batch Process

```bash
process_all_sprites.bat
```

### Step 3: Review & Select

```bash
python tools/generate_sprite_catalog.py gfx/processed/batch --output docs/SPRITE_CATALOG.md
```

Browse `docs/SPRITE_CATALOG.md` and select sprites to use.

### Step 4: Copy to Assets

```bash
# Example: Use idle animation
copy gfx\processed\batch\player_rad_90s\player\idle\*.chr src\game\assets\
```

### Step 5: Generate Assembly Includes

```bash
python tools/generate_sprite_catalog.py gfx/processed/batch --asm src/game/sprite_tiles.inc
```

### Step 6: Use in Code

```asm
.include "sprite_tiles.inc"

; Load player idle sprite
lda #TILE_PLAYER_IDLE_PLAYER_CHARACTER_IDLE_ANIMATION_FRAMES_START
sta sprite_tile
```

---

## Performance Tips

### Batch Processing

- **Sequential**: ~30 seconds per sheet (API calls)
- **Parallel**: NOT recommended (rate limits)
- **Optimal**: Process overnight or during breaks

### Caching

- Analysis results cached in `.cache/`
- Reusing same input = instant results
- Clear cache with `rm -rf .cache`

### Image Size

- **Optimal**: 1024x1024 or smaller
- **Large**: Auto-resized to 2048x2048
- **Tiny**: Works but AI may miss details

---

## Output Files

### Per Sprite Sheet

| File | Purpose |
|------|---------|
| `analysis.json` | Raw AI analysis (bounding boxes, labels) |
| `metadata.json` | Processed metadata (CHR paths, palettes) |
| `sprite_*_nobg.png` | Background removed |
| `sprite_*_indexed.png` | 4-color NES palette |
| `{type}/{action}/*.chr` | NES CHR tile data |
| `{type}/{action}/*.png` | Reference PNG |

### Batch Output

| File | Purpose |
|------|---------|
| `docs/SPRITE_CATALOG.md` | Human-readable catalog |
| `sprite_index.json` | Machine-readable index |
| `src/game/sprite_tiles.inc` | Assembly constants |

---

## Future Enhancements

### Planned Features

- [ ] Animation frame detection & splitting
- [ ] Automatic palette optimization per sprite
- [ ] Groq API integration (faster inference)
- [ ] rembg ML background removal
- [ ] Sprite preview thumbnails in catalog
- [ ] Auto-detect sprite size (8x8, 16x16, 32x32)

### Integration Ideas

- [ ] Export to Tiled map editor
- [ ] Generate C header files
- [ ] Create sprite previewer tool
- [ ] Batch convert to multiple formats (GB, SMS, etc.)

---

## API Cost Estimates

### Free Tier (Current)

- **Cost**: $0/month
- **Limit**: 1500 requests/day
- **Capacity**: ~50 sprite sheets/day

### Paid Tier (If Needed)

- **Gemini 2.5 Flash**: $0.075 per 1M input tokens
- **Image cost**: ~500 tokens/image
- **Estimate**: ~$0.04 per 1000 sprite sheets
- **Realistic**: < $1/month for active development

**Verdict**: Extremely cost-effective!

---

## Credits

- **AI Model**: Google Gemini 2.5 Flash
- **NES Tools**: cc65, neslib community
- **Homebrew**: NESdev wiki, romhacking.net
- **Inspiration**: 90s arcade sprite rippers

---

## Support

### Documentation

- [AI_WORKFLOW.md](AI_WORKFLOW.md) - Original planning doc
- [SPRITE_CATALOG.md](docs/SPRITE_CATALOG.md) - Generated catalog
- [NESdev Wiki](https://www.nesdev.org/wiki/) - NES technical reference

### Troubleshooting

1. Check `.cache/` for cached analyses
2. Review `debug_analysis_image.png` to see what AI analyzed
3. Inspect `sprite_*_nobg.png` for background removal quality
4. Verify CHR files with `tools/preview_tiles.py`

### Contact

- Report issues on GitHub
- Share sprite sheets for testing
- Contribute improvements via PR

---

**Happy sprite processing! 🎮✨**
