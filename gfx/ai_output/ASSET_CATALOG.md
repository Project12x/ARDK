# AI-Generated Assets Catalog

**Generated:** January 2026
**Tool:** Nano Banana (AI sprite generation)
**Purpose:** NES-compatible sprites and graphics for NEON SURVIVORS

---

## Asset Inventory

### 🎮 Player Characters (7 files)

1. **player_rad_90s.png** (562KB)
   - Original "rad 90s dude" concept
   - Baseball cap, sunglasses, shorts aesthetic
   - Use: Primary player sprite

2. **player_alt_radical.png** (527KB)
   - Alternative radical 90s style
   - Use: Player skin variant

3. **player_hair_dude.png** (611KB)
   - Long-haired character design
   - Use: Alternative player character

4. **player_hair_weapon.png** (807KB)
   - Long-haired character with weapon
   - Use: Armed player variant

5. **player_guitar_weapon.png** (862KB)
   - Player wielding guitar as weapon
   - Use: Special weapon variant or boss

6. **player_hero_combat.png** (599KB)
   - Combat-ready hero sprite
   - Use: Attack/action poses

7. **player_hero_idle_run.png** (558KB)
   - Idle and running animations
   - Use: Movement sprites

8. **player_hero_guitar.png** (727KB)
   - Hero with guitar (music-based attack?)
   - Use: Special ability sprite

9. **player_hero_master_sheet.png** (669KB)
   - Complete sprite sheet compilation
   - Use: Full animation set

### 👾 Enemies (2 files)

1. **enemies_synthwave.png** (561KB)
   - Synthwave-themed enemy designs
   - Bit Drone, Neon Skull variants
   - Use: Core enemy roster

2. **enemies_alt_glitch.png** (770KB)
   - Glitch-themed enemy variants
   - Digital corruption aesthetic
   - Use: Advanced enemy types

### 🏆 Boss

1. **boss_mainframe.png** (720KB)
   - Large mainframe/computer boss
   - Cyberpunk aesthetic
   - Use: End-of-level boss encounter

### 💎 Items & Projectiles

1. **items_projectiles.png** (533KB)
   - XP gems, health pickups, powerups
   - Weapon projectiles (lasers, missiles)
   - Use: Collectibles and weapon effects

### 💥 Visual Effects

1. **vfx_explosion.png** (849KB)
   - Explosion animation frames
   - Use: Death effects, impact VFX

### 🎨 Backgrounds (2 files)

1. **background_cyberpunk.png** (861KB)
   - Neon city background
   - Use: Urban arena backdrop

2. **background_alt_ruins.png** (623KB)
   - Ruined/destroyed cityscape
   - Use: Late-game area background

### 📝 UI & Text (3 files)

1. **title_logo.png** (688KB)
   - "NEON SURVIVORS" title logo
   - Use: Title screen

2. **title_logo_alt.png** (725KB)
   - Alternative title design
   - Use: Alternate title or credits

3. **ui_hud_font.png** (657KB)
   - Custom HUD font
   - Numbers, health bars, XP display
   - Use: In-game UI elements

4. **logo_dev_walrus.png** (739KB)
   - Developer logo/splash screen
   - "Walrus Games" or similar branding
   - Use: Boot splash screen

---

## Integration Pipeline

### Step 1: Prepare Assets for NES

All PNG files need conversion to NES CHR format:

```bash
# Use NesTiler for batch conversion
nestiler -i0 player_rad_90s.png -o player.chr --mode sprites --lossy 0

# Or use img2chr after manual indexing
python tools/make_indexed_sheet.py gfx/ai_output/player_rad_90s.png
img2chr gfx/ai_output/player_rad_90s_indexed.png src/game/assets/player.chr
```

### Step 2: Organize by Module

**Action Module Assets:**
- `items_projectiles.png` → Projectile tiles (lasers, missiles)
- `items_projectiles.png` → Powerup tiles (XP gems, health)
- `vfx_explosion.png` → Death/impact effects

**Player Assets:**
- `player_rad_90s.png` → Main character sprites
- `player_hero_master_sheet.png` → Full animation set

**Enemy Assets:**
- `enemies_synthwave.png` → Enemy sprites (tiles $30-$50)
- `boss_mainframe.png` → Boss sprite (large 4x4 metatile)

**Background Assets:**
- `background_cyberpunk.png` → Nametable data
- Convert to metatiles for room system

**UI Assets:**
- `ui_hud_font.png` → Font tiles for score/health display
- `title_logo.png` → Title screen logo tiles

### Step 3: CHR Bank Organization

**8KB CHR Bank Layout:**
```
$00-$1F: Player sprites (32 tiles = 512 bytes)
$20-$3F: Projectiles & powerups (32 tiles)
$40-$7F: Enemies (64 tiles)
$80-$9F: VFX (32 tiles)
$A0-$BF: UI/font (32 tiles)
$C0-$FF: Boss/special (64 tiles)
```

### Step 4: Tile Constant Definitions

Create `src/game/assets/tile_defs.inc`:

```asm
; Player tiles (from player_rad_90s.png)
TILE_PLAYER_BASE    = $00
TILE_PLAYER_IDLE    = $00  ; 2x2 metatile
TILE_PLAYER_RUN1    = $04
TILE_PLAYER_RUN2    = $08
TILE_PLAYER_ATTACK  = $0C

; Projectile tiles (from items_projectiles.png)
TILE_LASER          = $20
TILE_MISSILE        = $21
TILE_BEAM           = $22

; Powerup tiles
TILE_XP_GEM         = $24
TILE_HEALTH         = $25
TILE_COIN           = $26

; Enemy tiles (from enemies_synthwave.png)
TILE_ENEMY_DRONE    = $40
TILE_ENEMY_SKULL    = $44  ; 2x2 metatile
TILE_ENEMY_GLITCH   = $48

; VFX tiles (from vfx_explosion.png)
TILE_EXPLOSION_1    = $80
TILE_EXPLOSION_2    = $81
TILE_EXPLOSION_3    = $82
TILE_EXPLOSION_4    = $83
```

---

## Recommended Workflow

### Priority 1: Core Gameplay Assets
1. **player_rad_90s.png** → Convert to player.chr
2. **items_projectiles.png** → Extract projectile/powerup tiles
3. **enemies_synthwave.png** → Convert to enemy.chr

### Priority 2: Polish Assets
4. **vfx_explosion.png** → Add death effects
5. **ui_hud_font.png** → Implement score display
6. **background_cyberpunk.png** → Add parallax background

### Priority 3: Advanced Features
7. **boss_mainframe.png** → Boss encounter system
8. **title_logo.png** → Title screen graphics
9. **player_hero_master_sheet.png** → Animation system

---

## Asset Processing Scripts

### Create Indexed PNG (4-color palette)
```bash
python tools/make_indexed_sheet.py gfx/ai_output/player_rad_90s.png
```

### Convert to CHR
```bash
img2chr gfx/ai_output/player_rad_90s_indexed.png src/game/assets/sprites.chr
```

### Combine Multiple Assets
```bash
# Use spritesheet combiner
python tools/make_spritesheet.py \
  --input gfx/ai_output/player_rad_90s.png \
  --input gfx/ai_output/items_projectiles.png \
  --input gfx/ai_output/enemies_synthwave.png \
  --output src/game/assets/combined.chr
```

---

## Notes

- All PNGs are RGB format - need conversion to 4-color indexed
- NES palette limitations: 4 colors per sprite, 64 sprites max
- Some assets may need manual editing for NES constraints
- Large sprites (guitar weapon, boss) need metatile system
- Background images need conversion to nametable format

---

## Next Steps

1. ✅ Catalog assets (this file)
2. ⏳ Convert priority 1 assets to indexed PNG
3. ⏳ Generate CHR files with img2chr/NesTiler
4. ⏳ Update sprite_tiles.inc with new tile constants
5. ⏳ Replace placeholder graphics in game_main.asm
6. ⏳ Test in emulator (Mesen)
