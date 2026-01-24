# NEON SURVIVORS - Current Status

## ✅ WORKING

### Core Systems
- **MMC3 Mapper**: Properly initialized with correct bank setup
- **NMI Handler**: Firing every frame, sprite DMA working
- **Sprite Rendering**: One sprite displays at (100, 100)
- **CHR ROM**: 4x 8KB banks configured
- **Build System**: ca65/ld65 compiling successfully (65KB ROM)

### Files Created/Fixed
- `config/nrom.cfg` - NROM linker config (used for testing)
- `config/mmc3.cfg` - MMC3 linker config (current)
- `src/engine/entry.asm` - Minimal working reset handler + MMC3 init
- `src/engine/hal/nmi.asm` - Minimal NMI with sprite DMA
- `src/engine/header.asm` - Correct iNES header for MMC3
- `src/game/assets/sprites.chr` - Test CHR with smiley face sprite

## ❌ NOT YET WORKING

### Asset Pipeline Issues
- `process_ai_assets.py` - Creating empty indexed PNGs (all pixels = 0)
- `png2chr.py` - Works but receives empty input
- AI-generated assets not yet integrated

### Missing Features
- Input handling (D-pad to move sprite)
- Debug screen with menu
- Audio system (APU code exists but not integrated)
- Player sprite graphics (placeholder smiley only)
- Background rendering
- Text rendering

## 📋 NEXT STEPS

### Immediate (Get Sprite Moving)
1. **Add input system** - Read controller, move sprite
2. **Test D-pad movement** - Verify input works

### Short Term (Asset Integration)
3. **Fix process_ai_assets.py** - Debug why it creates empty images
4. **Convert one AI asset properly** - Get actual player sprite showing
5. **Test CHR bank switching** - Verify MMC3 can swap graphics

### Medium Term (Playable Demo)
6. **Restore debug screen** - Menu system, feature tests
7. **Add audio back** - Button presses make sounds
8. **Multiple sprites** - Show several player frames
9. **Animation system** - Sprite flipping/frame changes

## 🐛 KNOWN ISSUES

### AI Asset Processing
**Problem**: `process_ai_assets.py` produces indexed PNGs with all pixels = 0

**Likely Cause**:
- Quantization function maps all colors to index 0 (transparent)
- Or image extraction is selecting wrong area
- Or palette mapping is broken

**To Debug**:
```bash
python tools/process_ai_assets.py --asset player_rad_90s
# Check: gfx/processed/player_rad_90s_indexed.png
# Should have visible sprites, not all black
```

### CHR Conversion
**Problem**: `png2chr.py` creates CHR files but they're all zeros

**Actual Cause**: Input PNG is all zeros (see above)

**png2chr.py itself works fine** - tested with manually created indexed PNGs

## 💡 LESSONS LEARNED

### What Worked
1. **Start simple** - NROM test ROM first, then MMC3
2. **Empty CHR = invisible sprites** - Always check CHR has data!
3. **MMC3 2K CHR banks use EVEN numbers** (0, 2, 4, 6 not 0, 1, 2, 3)
4. **Proven examples** - Following working code is better than experimentation
5. **Standard NES patterns** - 2 VBlank wait, RAM clear, palette before render

### What Didn't Work
- Complex initialization before basics tested
- Assuming CHR files were populated
- Not verifying asset processing output

## 🎯 GOAL

**Immediate Goal**: Get D-pad input moving the sprite

**Next Milestone**: Show actual player sprite from AI assets

**Final Goal**: Vampire Survivors-style game with:
- Player sprite (from AI assets)
- Enemy waves
- Auto-firing weapons
- XP/levelup system
- Synthwave aesthetics

## 📁 ROM STATUS

**Current ROM**: `build/neon_survivors.nes`
- **Size**: 65,552 bytes
- **Mapper**: MMC3 (Mapper 4)
- **PRG ROM**: 32KB (2x 16KB banks)
- **CHR ROM**: 32KB (4x 8KB banks)
- **What It Does**: Shows single smiley face sprite, infinite loop

**Test In Mesen**: Load ROM, should see black background + one sprite at center-ish

## 🔗 Key References Used

- [NESdev Wiki - Init Code](https://www.nesdev.org/wiki/Init_code)
- [nesdoug/33_MMC3](https://github.com/nesdoug/33_MMC3)
- [NES_bankswitch_example PR#4](https://github.com/gutomaia/NES_bankswitch_example/pull/4)
- Proven NES homebrew initialization patterns (Nerdy Nights, etc.)
