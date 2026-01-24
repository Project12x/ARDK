# NES Development Quick Reference

**Quick access to tools, commands, and workflows**

---

## Essential Commands

### Build & Test
```bash
compile.bat                    # Build ROM
build_assets.bat               # Rebuild graphics
mesen build/neon_survivors.nes # Test in emulator
```

### Asset Pipeline
```bash
# Graphics (choose one)
img2chr input.png output.chr                          # Simple
nestiler -i0 input.png -o output.chr --mode sprites   # Advanced

# Music
# 1. Suno → Export MIDI
# 2. FamiStudio → Import MIDI → Export CA65
# 3. .include "music.s" in code
```

---

## Tool Downloads

| Tool | URL | Purpose |
|------|-----|---------|
| NEXXT | https://frankengraphics.itch.io/nexxt | CHR editor |
| NesTiler | https://github.com/ClusterM/NesTiler/releases | Batch PNG→CHR |
| FamiStudio | https://famistudio.org | Music editor |
| Mesen | https://mesen.ca | Emulator/debugger |
| create-nes-game | npm install -g create-nes-game | Build system |

---

## Memory Map

```
$0000-$00FF: Zero Page
  $00-$0F: Engine temps
  $10-$2F: HAL state
  $30-$FF: Game + stack

$0200-$02FF: OAM Buffer (sprites)
$0300-$07FF: General RAM
$6000-$7FFF: SRAM (MMC3)
$8000-$FFFF: PRG ROM
```

---

## Sprite Tile Map

| Index | Sprite | Size |
|-------|--------|------|
| $00-$03 | Player (2x2) | 16x16 |
| $02 | Bit Drone | 8x8 |
| $03-$06 | Neon Skull | 16x16 |
| $20 | XP Gem | 8x8 |
| $21 | Laser | 8x8 |

---

## Code Snippets

### Render 16x16 Sprite
```asm
; Player at (x, y) using tiles $00-$03
lda player_y
sta $0200          ; Top-left Y
lda #$00
sta $0201          ; Tile $00
lda #$00
sta $0202          ; Attributes
lda player_x
sta $0203          ; Top-left X

; Repeat for $01 (top-right), $10 (bottom-left), $11 (bottom-right)
```

### AABB Collision
```c
bool collides = !(x1 + w1 < x2 || x2 + w2 < x1 ||
                  y1 + h1 < y2 || y2 + h2 < y1);
```

### Spawn Entity
```asm
lda #ENEMY_TYPE
sta temp1
lda #128          ; X position
sta temp2
lda #100          ; Y position
sta temp3
jsr entity_spawn  ; Returns index in X
```

---

## Common Issues

### "7 colors found!"
→ Reduce PNG to 4 colors (indexed mode)

### "CHR file is 4KB"
→ Pad to 8KB: `truncate -s 8192 file.chr`

### "Sprites flicker"
→ Max 8 sprites per scanline, use sprite cycling

### "MIDI import fails"
→ Ensure monophonic (one note per channel)

---

## Documentation Index

- **[NES_DEVELOPMENT_TOOLKIT.md](NES_DEVELOPMENT_TOOLKIT.md)** - Complete tool catalog
- **[REUSABLE_ENGINE_ARCHITECTURE.md](REUSABLE_ENGINE_ARCHITECTURE.md)** - Code patterns
- **[ASSET_PIPELINE.md](../ASSET_PIPELINE.md)** - Graphics/audio workflows
- **[MODERN_PIPELINE_SUMMARY.md](MODERN_PIPELINE_SUMMARY.md)** - Overview for sharing

---

**[Full Documentation]** → `/docs/` folder
