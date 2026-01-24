# ARDK AI Prompt Templates

> **Version**: 1.3
> **Purpose**: Tier-aware prompt templates for AI asset generation (images & audio)
> **Philosophy**: Generate at tier's highest-detail platform, pipeline downsamples within tier

---

## Design Philosophy

### Per-Tier High Targets

Rather than generating everything at maximum quality and downsampling across all tiers,
we generate at the **highest graphical detail platform within each tier**. This produces
better results for each tier's aesthetic while still allowing pipeline downsampling.

```text
┌─────────────────────────────────────────────────────────────────────┐
│                         TIER-SPECIFIC TARGETS                        │
│                                                                      │
│  MINIMAL → SMS (Master System)     16 colors, 256x192, best sprites │
│  STANDARD → SNES                   256 colors, Mode 7, best depth    │
│  EXTENDED → Nintendo DS            Dual screen, full capabilities    │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    unified_pipeline.py                               │
│         Downsample WITHIN tier to other tier platforms               │
└─────────────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
   │   MINIMAL    │  │   STANDARD   │  │   EXTENDED   │
   │   SMS────►   │  │   SNES───►   │  │    DS────►   │
   │   NES        │  │   Neo Geo    │  │    GBA       │
   │   Game Boy   │  │   Genesis    │  │              │
   │   C64        │  │   PC Engine  │  │              │
   │   ZX Spectrum│  │              │  │              │
   │   Atari 2600 │  │              │  │              │
   └──────────────┘  └──────────────┘  └──────────────┘
```

**Why per-tier targets:**
- Captures the authentic aesthetic of each era
- Better palette choices for target tier's limitations
- Smaller quality gap when downsampling within tier
- SMS sprites look different from DS sprites - preserve that character
- Artists/AI can focus on tier-appropriate detail levels

**Note on Neo Geo & Sega CD:** While Neo Geo and Sega CD have impressive capabilities,
they use STANDARD tier for **asset aesthetics** but **STANDARD_PLUS** tier for **game logic**.
STANDARD_PLUS is an intermediate tier between STANDARD and EXTENDED, optimized for fast 68000 CPUs.
Sprites designed at SNES quality work perfectly on both platforms.

---

## Tier Target Specifications

### MINIMAL Tier → Target: Sega Master System (SMS)

**Why SMS as target:**
- Best sprite system in MINIMAL tier (16 colors per sprite line)
- 256x192 resolution provides more detail than NES (256x240 but limited sprites)
- Cleaner than Game Boy (4 shades of green)
- Better color palette than NES's restrictive 4-color sprite limitation

**SMS Target Specs:**
| Property | Value |
|----------|-------|
| Resolution | 256x192 |
| Sprite size | 8x8 or 8x16 |
| Colors per sprite | Up to 16 (from 64-color palette) |
| Total on-screen | 64 sprites, 8 per line |
| Tile size | 8x8 |

**Downsamples to:**
- NES: 4 colors per sprite, different palette indexing
- Game Boy: 4 shades grayscale
- Atari 2600: Severe reduction (2 colors per line)

---

### STANDARD Tier → Target: Neo Geo / SNES

**Why Neo Geo/SNES as target:**
- Neo Geo: Maximum sprite capabilities (380 sprites, huge sizes)
- SNES: Best color depth (256 colors from 32768, mode 7)
- Both support large, detailed sprites
- Represent the peak of 2D sprite-based gaming

**Neo Geo Target Specs:**
| Property | Value |
|----------|-------|
| Resolution | 320x224 |
| Sprite size | 16x16 to 512x512 (tiles) |
| Colors | 4096 on-screen, 65536 total |
| Sprites on-screen | 380 |
| Detail level | Arcade-quality pixel art |

**SNES Target Specs:**
| Property | Value |
|----------|-------|
| Resolution | 256x224 (up to 512x448) |
| Sprite size | 8x8 to 64x64 |
| Colors | 256 per screen from 32768 |
| Sprites on-screen | 128, 32 per line |

**Downsamples to:**
- Genesis: 61 colors, slightly smaller sprites
- PC Engine: 482 colors but smaller sprite limit

---

### EXTENDED Tier → Target: Nintendo DS

**Why DS as target:**
- Dual screens allow showcasing more content
- Full 2D capabilities with 3D support
- 262,144 colors
- Represents the pinnacle of dedicated 2D handheld hardware

**DS Target Specs:**
| Property | Value |
|----------|-------|
| Resolution | 256x192 per screen (x2) |
| Sprite size | Up to 64x64 |
| Colors | 262,144 (18-bit) |
| Sprites | 128 per screen |
| Features | Rotation, scaling, alpha |

**Downsamples to:**
- GBA: 32,768 colors, single screen
- PSP: Easy downscale (more powerful but different aspect)

---

## Image Prompt Templates

### MINIMAL Tier Template (SMS Target)

```text
[ARDK_SPRITE_MINIMAL]

Create a {subject} as pixel art for a Sega Master System game.

TECHNICAL REQUIREMENTS:
- Resolution: {width}x{height} pixels (target 64x64 max, scales to 32x32, 16x16)
- Colors: Maximum 16 colors (will reduce to 4 for NES/GB)
- Format: PNG with transparency
- Style: Clean pixel art with hard edges, no anti-aliasing
- Palette: Choose colors that reduce well to 4 shades

AESTHETIC DIRECTION:
- Era feel: 8-bit console (1985-1992)
- Detail level: Moderate - readable at small sizes
- Theme: {theme}
- Reference style: Alex Kidd, Wonder Boy, Phantasy Star SMS

KEY CONSTRAINTS:
- Sprites must read clearly at 16x16 final size
- Key silhouette identifiable at a glance
- 2-3 signature colors that survive 4-color reduction
- No gradients - use dithering sparingly

DO NOT:
- Add text labels or watermarks
- Use more than 16 colors total
- Create details smaller than 2x2 pixels
- Anti-alias edges
```

### STANDARD Tier Template (Neo Geo/SNES Target)

```text
[ARDK_SPRITE_STANDARD]

Create a {subject} as high-quality pixel art for a Neo Geo or SNES game.

TECHNICAL REQUIREMENTS:
- Resolution: {width}x{height} pixels (target 128x128, scales to 64x64, 32x32)
- Colors: Up to 256 colors (will reduce to 16 for Genesis)
- Format: PNG with transparency
- Style: Detailed pixel art, the golden age of 2D
- Palette: Rich but organized - use color ramps effectively

AESTHETIC DIRECTION:
- Era feel: 16-bit arcade/console (1990-1997)
- Detail level: High - showcase pixel art craftsmanship
- Theme: {theme}
- Reference style: Metal Slug, Street Fighter, Chrono Trigger

KEY CONSTRAINTS:
- Can include subtle shading and highlights
- Animation frames should flow smoothly
- Maintain consistency for sprite sheets
- Details should remain visible at 32x32

DO NOT:
- Add text labels or watermarks
- Use true gradients (stepped color ramps OK)
- Create details smaller than 1x1 pixel (no sub-pixel tricks)
- Anti-alias edges to background
```

### EXTENDED Tier Template (DS Target)

```text
[ARDK_SPRITE_EXTENDED]

Create a {subject} as detailed pixel art for a Nintendo DS game.

TECHNICAL REQUIREMENTS:
- Resolution: {width}x{height} pixels (target 256x256, scales down as needed)
- Colors: Full color range available (will reduce for GBA if needed)
- Format: PNG with transparency
- Style: Modern pixel art with refined detail
- Palette: Can use full gradients and subtle color transitions

AESTHETIC DIRECTION:
- Era feel: Late handheld/modern pixel art (2004-2010)
- Detail level: Maximum - showcase the art
- Theme: {theme}
- Reference style: Castlevania DS series, Pokemon HG/SS, Disgaea DS

KEY CONSTRAINTS:
- Can include detailed shading
- Smooth animation expected
- Rich color palettes encouraged
- Sprite sheets should be comprehensive

DO NOT:
- Add text labels or watermarks
- Mix pixel art with painted/filtered elements
- Anti-alias edges to transparent background
```

---

## Sprite Type Presets (Per-Tier)

### Player Character

#### MINIMAL (SMS Target)
```text
[ARDK_PLAYER_MINIMAL]
Subject: Main playable character - {character_description}
Resolution: 64x64 pixels (scales to 32x32, 16x16)
Colors: 16 max, design for 4-color survival

DESIGN PRIORITIES:
1. MUST be recognizable at 16x16
2. Strong silhouette with 2-3 key colors
3. Simple shapes that animate well
4. Distinct from enemies even in monochrome

ANIMATION SET:
- Idle (2 frames, subtle)
- Walk (4 frames)
- Attack (2-3 frames)
- Hurt (1 frame)
- Death (2 frames)

Reference: Alex Kidd, Wonder Boy, Mega Man NES
```

#### STANDARD (Neo Geo/SNES Target)
```text
[ARDK_PLAYER_STANDARD]
Subject: Main playable character - {character_description}
Resolution: 128x128 pixels (scales to 64x64, 32x32)
Colors: Up to 64 for character

DESIGN PRIORITIES:
1. Expressive, detailed design
2. Smooth animation potential
3. Character personality visible in sprite
4. Works as hero in action scenes

ANIMATION SET:
- Idle (4 frames, personality)
- Walk/Run (6-8 frames)
- Attack variants (4-6 frames each)
- Hurt (2 frames)
- Death (4 frames, dramatic)
- Special (4-6 frames)

Reference: Metal Slug soldiers, Chrono Trigger, Street Fighter
```

#### EXTENDED (DS Target)
```text
[ARDK_PLAYER_EXTENDED]
Subject: Main playable character - {character_description}
Resolution: 256x256 pixels (scales down as needed)
Colors: Full palette

DESIGN PRIORITIES:
1. Detailed, polished character design
2. Fluid animation expected
3. Expressive poses and personality
4. Can include subtle effects (glow, shadow)

ANIMATION SET:
- Idle (4-6 frames, breathing/movement)
- Walk/Run (8 frames smooth cycle)
- Multiple attack types (6+ frames each)
- Hurt (2-3 frames)
- Death (6 frames, impactful)
- Victory/Taunt (4-6 frames)
- Special abilities (6-8 frames each)

Reference: Castlevania DS protagonists, Pokemon trainer sprites
```

---

### Enemy - Basic

#### MINIMAL (SMS Target)
```text
[ARDK_ENEMY_MINIMAL]
Subject: Common enemy - {enemy_description}
Resolution: 32x32 pixels (scales to 16x16, 8x8)
Colors: 8-16, design for 4-color survival

DESIGN:
- Clearly hostile silhouette
- Simple, menacing shape
- Must work with many on screen
- Death can be simple (flash + disappear)

ANIMATION: Idle (2 frames), Death (1-2 frames)
Reference: Mega Man NES enemies, Castlevania skeletons
```

#### STANDARD (Neo Geo/SNES Target)
```text
[ARDK_ENEMY_STANDARD]
Subject: Common enemy - {enemy_description}
Resolution: 64x64 pixels (scales to 32x32)
Colors: 16-32

DESIGN:
- Detailed hostile design
- Attack animations visible
- Satisfying to defeat
- Variety possible (recolor variants)

ANIMATION: Idle (2-4 frames), Attack (3 frames), Death (3 frames explosion)
Reference: Metal Slug enemies, Contra Hard Corps
```

#### EXTENDED (DS Target)
```text
[ARDK_ENEMY_EXTENDED]
Subject: Common enemy - {enemy_description}
Resolution: 128x128 pixels (scales down)
Colors: Full

DESIGN:
- Polished enemy design
- Personality even in basic enemies
- Smooth attack tells
- Impactful death animation

ANIMATION: Idle (4 frames), Move (4 frames), Attack (4 frames), Death (4-6 frames)
Reference: Castlevania DS enemies, Mega Man ZX
```

---

### Boss Enemy

#### MINIMAL (SMS Target)
```text
[ARDK_BOSS_MINIMAL]
Subject: Boss enemy - {boss_description}
Resolution: 128x128 pixels (composite of smaller sprites)
Colors: 16, plan for 4-color sections

DESIGN:
- Impressive for 8-bit era
- Clear attack patterns readable in sprite
- Can be assembled from multiple sprites
- Memorable silhouette

Reference: Wonder Boy III bosses, R-Type bosses
```

#### STANDARD (Neo Geo/SNES Target)
```text
[ARDK_BOSS_STANDARD]
Subject: Boss enemy - {boss_description}
Resolution: 256x256 pixels
Colors: 64+

DESIGN:
- Large, imposing, detailed
- Multiple attack animations
- Damage states visible
- Screen presence

Reference: Metal Slug bosses, Contra III bosses, SNES RPG bosses
```

#### EXTENDED (DS Target)
```text
[ARDK_BOSS_EXTENDED]
Subject: Boss enemy - {boss_description}
Resolution: 512x512 pixels (or multi-sprite assembly)
Colors: Full palette

DESIGN:
- Spectacular, memorable
- Complex animation sets
- Phase changes visible
- Can use both screens on DS

Reference: Castlevania DS bosses, Mega Man ZX bosses
```

---

## Audio Prompt Templates (SUNO/Music AI)

### Per-Tier Audio Philosophy

| Tier | Target Style | Conversion |
|------|--------------|------------|
| MINIMAL | Chiptune (NES/GB style) | Direct use or simplify |
| STANDARD | FM Synthesis + PCM (Genesis/SNES) | Rich but convert-ready |
| EXTENDED | Full quality (CD/streaming) | Reference quality |

### MINIMAL Tier Music (Chiptune Target)

```text
[ARDK_MUSIC_MINIMAL]

Compose {mood} chiptune music in authentic 8-bit style.

TECHNICAL:
- Channels: Maximum 4 (2 pulse, 1 triangle, 1 noise)
- No samples or complex waveforms
- Clear melody that works monophonically
- Loopable at {length} seconds

STYLE:
- Era: NES/Game Boy (1985-1995)
- Arpeggios instead of chords
- Simple but catchy melodies
- Drum sounds from noise channel
- {mood_description}

REFERENCE: {reference_games} (Mega Man, Castlevania, Kirby GB)

DO NOT:
- Use more than 4 simultaneous voices
- Include vocals
- Use reverb or modern effects
- Create complex stereo panning
```

### STANDARD Tier Music (FM/PCM Target)

```text
[ARDK_MUSIC_STANDARD]

Compose {mood} music in 16-bit era style.

TECHNICAL:
- Channels: 6-10 (FM synthesis + PCM samples)
- Can use instrument samples
- Stereo panning allowed
- Loopable at {length} seconds

STYLE:
- Era: Genesis/SNES (1989-1996)
- Rich FM tones OR orchestral samples
- Fuller arrangements than 8-bit
- {mood_description}

REFERENCE: {reference_games} (Streets of Rage, Chrono Trigger, Sonic)

DO NOT:
- Use modern compression/limiting
- Include vocals
- Use streaming-quality production
```

### EXTENDED Tier Music (Full Quality Target)

```text
[ARDK_MUSIC_EXTENDED]

Compose {mood} music for modern retro-style game.

TECHNICAL:
- Full production quality
- Any instrumentation
- Professional mixing
- Loopable at {length} seconds

STYLE:
- Era: Modern pixel art games
- Full orchestral or electronic
- Can reference older styles with modern production
- {mood_description}

REFERENCE: {reference_games} (Shovel Knight, Celeste, Undertale)
```

---

## Music Type Presets

### Title Screen

#### MINIMAL
```text
[ARDK_TITLE_MINIMAL]
Style: NES chiptune
Length: 30-45 seconds loop
Mood: Inviting, memorable hook
Channels: 4 max
Reference: Mega Man 2 title, Castlevania NES title
```

#### STANDARD
```text
[ARDK_TITLE_STANDARD]
Style: Genesis FM or SNES orchestral
Length: 45-60 seconds loop
Mood: Epic, sets game tone
Reference: Sonic 2 title, Final Fantasy VI opening
```

#### EXTENDED
```text
[ARDK_TITLE_EXTENDED]
Style: Full production
Length: 60-90 seconds loop
Mood: Cinematic, memorable theme
Reference: Shovel Knight, Hollow Knight title
```

### Action/Stage

#### MINIMAL
```text
[ARDK_ACTION_MINIMAL]
Style: Driving chiptune
Length: 60 seconds loop
BPM: 140-160
Mood: Energetic, heroic
Reference: Mega Man stages, Contra NES
```

#### STANDARD
```text
[ARDK_ACTION_STANDARD]
Style: FM synth or orchestral action
Length: 75-90 seconds loop
BPM: 130-160
Mood: Intense, layered
Reference: Streets of Rage 2, Castlevania Bloodlines
```

#### EXTENDED
```text
[ARDK_ACTION_EXTENDED]
Style: Full production action
Length: 90-120 seconds loop
BPM: 120-170
Mood: Driving, complex arrangement
Reference: Celeste, Hades action tracks
```

### Boss Battle

#### MINIMAL
```text
[ARDK_BOSS_MINIMAL]
Style: Intense chiptune
Length: 45 seconds loop
BPM: 150-180
Mood: Urgent, threatening
Reference: Mega Man boss, Castlevania boss
```

#### STANDARD
```text
[ARDK_BOSS_STANDARD]
Style: Heavy FM or orchestral
Length: 60 seconds loop
BPM: 140-170
Mood: Climactic, powerful
Reference: Thunder Force IV boss, FFVI boss
```

#### EXTENDED
```text
[ARDK_BOSS_EXTENDED]
Style: Cinematic boss music
Length: 75-90 seconds loop
Mood: Epic confrontation
Reference: Shovel Knight bosses, Hollow Knight
```

---

## SFX Templates (Per-Tier)

### MINIMAL (Chiptune SFX)
```text
[ARDK_SFX_MINIMAL]
Style: Pure synthesis (no samples)
- Shoot: Short pulse sweep (0.1s)
- Hit: Noise burst (0.05s)
- Pickup: Rising arpeggio (0.2s)
- Explosion: Noise decay (0.3s)
- Jump: Pitch rise (0.15s)
Reference: NES/GB sound effects
```

### STANDARD (FM/Sample SFX)
```text
[ARDK_SFX_STANDARD]
Style: FM synthesis or short samples
- Shoot: Punchy with slight reverb (0.15s)
- Hit: Impact with body (0.1s)
- Pickup: Melodic chime (0.3s)
- Explosion: Layered boom (0.4s)
- Jump: Springy with character (0.2s)
Reference: Genesis/SNES sound effects
```

### EXTENDED (Full Quality SFX)
```text
[ARDK_SFX_EXTENDED]
Style: Full sample quality
- Shoot: Designed, punchy (0.2s)
- Hit: Satisfying impact (0.15s)
- Pickup: Rewarding jingle (0.4s)
- Explosion: Cinematic boom (0.5s)
- Jump: Characterful spring (0.25s)
Reference: Modern indie game SFX
```

---

## Theme Modifiers

Apply these to any tier template:

### Synthwave/Retrowave
```text
THEME: SYNTHWAVE
- Palette: Magenta, cyan, purple, hot pink, electric blue
- Aesthetic: 80s retro-futurism, neon grids
- Music: Arpeggiated synths, gated drums
- Reference: Hotline Miami, Far Cry Blood Dragon
```

### Dark Fantasy
```text
THEME: DARK_FANTASY
- Palette: Deep purples, blood reds, bone white
- Aesthetic: Gothic, supernatural
- Music: Minor keys, orchestral, choir
- Reference: Castlevania, Dark Souls
```

### Sci-Fi
```text
THEME: SCIFI
- Palette: Steel blue, orange highlights, chrome
- Aesthetic: Technological, sleek
- Music: Electronic, ambient, industrial
- Reference: Metroid, Mega Man X
```

### Cute/Kawaii
```text
THEME: CUTE
- Palette: Pastels, soft pink, mint green
- Aesthetic: Rounded, friendly
- Music: Upbeat, bouncy, melodic
- Reference: Kirby, Yoshi, Animal Crossing
```

### Horror
```text
THEME: HORROR
- Palette: Desaturated, sickly greens, deep reds
- Aesthetic: Unsettling, corrupted
- Music: Dissonant, sparse, tense
- Reference: Silent Hill, Resident Evil
```

---

## Pipeline Integration

### Workflow by Tier

```text
MINIMAL Tier Workflow:
1. Generate at SMS specs using ARDK_*_MINIMAL templates
2. Pipeline converts: SMS → NES → GB → Atari 2600
3. Review at SMS quality, spot-check NES/GB

STANDARD Tier Workflow:
1. Generate at Neo Geo/SNES specs using ARDK_*_STANDARD templates
2. Pipeline converts: Neo Geo/SNES → Genesis → PCE
3. Review at SNES quality, verify Genesis colors

EXTENDED Tier Workflow:
1. Generate at DS specs using ARDK_*_EXTENDED templates
2. Pipeline converts: DS → GBA → (PSP)
3. Review at DS quality, verify GBA fit
```

### Command Examples

```bash
# Generate for MINIMAL tier (SMS target, converts to NES/GB)
python tools/unified_pipeline.py sprite.png -o gfx/ --tier minimal

# Generate for STANDARD tier (SNES target, converts to Genesis)
python tools/unified_pipeline.py sprite.png -o gfx/ --tier standard

# Generate for EXTENDED tier (DS target, converts to GBA)
python tools/unified_pipeline.py sprite.png -o gfx/ --tier extended

# Generate for specific platform (uses appropriate tier)
python tools/unified_pipeline.py sprite.png -o gfx/ --platform nes
# (Automatically uses MINIMAL tier settings)
```

### Prompt Generation Tool (Future)

```bash
# Generate complete prompt file for a game
python tools/prompt_generator.py \
    --tier minimal \
    --theme synthwave \
    --game-type survivors \
    --output prompts/minimal_survivors/

# Output structure:
prompts/minimal_survivors/
├── sprites/
│   ├── player.txt      # ARDK_PLAYER_MINIMAL + SYNTHWAVE theme
│   ├── enemy_basic.txt
│   └── boss.txt
├── music/
│   ├── title.txt       # ARDK_TITLE_MINIMAL + SYNTHWAVE theme
│   ├── action.txt
│   └── boss.txt
└── sfx/
    ├── shoot.txt       # ARDK_SFX_MINIMAL
    └── pickup.txt
```

---

## Quick Reference Card

| Asset | MINIMAL (SMS) | STANDARD (Neo Geo/SNES) | EXTENDED (DS) |
|-------|---------------|-------------------------|---------------|
| Player | 64x64, 16 col | 128x128, 64 col | 256x256, full |
| Enemy | 32x32, 16 col | 64x64, 32 col | 128x128, full |
| Boss | 128x128, 16 col | 256x256, 64 col | 512x512, full |
| Projectile | 16x16, 8 col | 32x32, 16 col | 64x64, full |
| Pickup | 16x16, 8 col | 32x32, 16 col | 64x64, full |
| Music | 4ch chiptune | 6-10ch FM/PCM | Full quality |
| SFX | Synth only | FM + samples | Full samples |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-11 | Initial template system (single EXTENDED target) |
| 1.1 | 2026-01-11 | Refactored to per-tier targets (SMS/Neo Geo/DS) |
| 1.2 | 2026-01-11 | Updated STANDARD peak to SNES (Neo Geo has split tiers) |
| 1.3 | 2026-01-11 | Clarified STANDARD_PLUS logic tier for Neo Geo & Sega CD |

---

*Generate at tier's peak, downsample within tier!*
