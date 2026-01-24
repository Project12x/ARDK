# ARDK Libraries, APIs & Middleware Design

> **Version**: 1.0
> **Purpose**: Design document for ARDK's internal libraries and distributable tools

---

## Executive Summary

ARDK consists of three layers:
1. **Distributable Tools** - Standalone utilities usable outside ARDK
2. **Core Libraries** - Platform-agnostic APIs for game development
3. **HAL Layer** - Hardware abstraction with platform-specific backends

The sprite pipeline (`unified_pipeline.py`) is already mature enough for standalone distribution. This document outlines additional tools and libraries to develop.

---

## Part 1: Distributable Tools (Standalone Usage)

These tools should work independently, without requiring the full ARDK framework.

### 1.1 Sprite Pipeline (EXISTING - Ready for Distribution)

**Current:** `unified_pipeline.py` v5.4

**Features:**
- 17 platform targets
- AI-powered sprite labeling (6 providers)
- Content-based sprite detection
- Text/label filtering
- Platform-specific resampling
- Correct tile format output

**Distribution Plan:**
```
ardk-sprite-pipeline/
├── sprite_pipeline.py      # Renamed from unified_pipeline.py
├── platforms/              # Platform configs as separate modules
│   ├── __init__.py
│   ├── nes.py
│   ├── genesis.py
│   ├── gameboy.py
│   └── ...
├── providers/              # AI label providers
│   ├── groq.py
│   ├── gemini.py
│   └── ...
├── requirements.txt
├── setup.py               # pip installable
└── README.md
```

**pip installation:**
```bash
pip install ardk-sprite-pipeline

# Usage
ardk-sprites input.png -o output/ --platform nes
ardk-sprites --batch sprites/ --platform genesis
```

**Modern PC Usage (Retro Styling):**
```python
from ardk_sprites import SpritePipeline, NESConfig

# Enforce NES-style constraints on modern assets
pipeline = SpritePipeline(NESConfig)
pipeline.process("character.png", enforce_palette=True)
# Outputs indexed PNG with 4-color palette, 8x8 tiles
```

---

### 1.2 Tilemap Converter (TO BUILD)

**Purpose:** Convert Tiled/LDTK maps to platform-specific formats

**Features:**
- Read .tmx (Tiled) and .ldtk (LDTK) formats
- Output platform-specific nametables
- Metatile compression
- Collision map extraction
- Attribute table generation (NES)

**Architecture:**
```python
# ardk_tilemaps/converter.py
class TilemapConverter:
    def __init__(self, platform: PlatformConfig):
        self.platform = platform

    def load_tiled(self, path: str) -> Tilemap:
        """Load Tiled .tmx file."""
        pass

    def load_ldtk(self, path: str) -> Tilemap:
        """Load LDTK .ldtk file."""
        pass

    def export_nametable(self, tilemap: Tilemap) -> bytes:
        """Export platform-specific nametable."""
        pass

    def export_collision(self, tilemap: Tilemap) -> bytes:
        """Export collision map."""
        pass

    def export_metatiles(self, tilemap: Tilemap) -> bytes:
        """Export metatile definitions."""
        pass
```

**CLI:**
```bash
ardk-tilemaps level1.tmx -o level1.bin --platform nes
ardk-tilemaps world.ldtk -o world/ --platform genesis --split-layers
```

---

### 1.3 Audio Converter (TO BUILD)

**Purpose:** Convert audio to platform-specific formats

**Features:**
- WAV/MP3 → platform samples
- MIDI → platform music data
- FamiTracker .ftm → NES
- DefleMask .dmf → Genesis/GB
- MOD/XM → Amiga/SNES

**Architecture:**
```python
# ardk_audio/converter.py
class AudioConverter:
    def __init__(self, platform: PlatformConfig):
        self.platform = platform

    def convert_sample(self, wav_path: str) -> bytes:
        """Convert WAV to platform sample format."""
        # NES: 1-bit DPCM
        # Genesis: 8-bit PCM
        # SNES: BRR compression
        pass

    def convert_music(self, source_path: str) -> bytes:
        """Convert tracker/MIDI to platform music."""
        pass
```

---

### 1.4 Font Generator (TO BUILD)

**Purpose:** Convert fonts to tile-based format

**Features:**
- TTF/OTF → fixed-width tiles
- Variable width support (where platform allows)
- Multiple character sets (ASCII, extended, custom)
- Kerning tables

**CLI:**
```bash
ardk-fonts PressStart2P.ttf -o font.chr --platform nes --size 8x8
ardk-fonts custom.png -o font.bin --platform genesis --grid 8x8
```

---

### 1.5 ROM Validator (TO BUILD)

**Purpose:** Validate ROMs for correctness

**Features:**
- Header validation (iNES, SMD, etc.)
- Checksum verification/fixing
- Size validation
- Mapper detection
- Emulator compatibility check

**CLI:**
```bash
ardk-validate game.nes --fix-checksum
ardk-validate game.bin --platform genesis
```

---

### 1.6 Palette Tool (TO BUILD)

**Purpose:** Work with platform palettes

**Features:**
- Visualize platform palettes
- Extract palette from image
- Convert between palette formats
- Generate gradient-friendly palettes
- Synthwave/vaporwave presets

**CLI:**
```bash
ardk-palette --show nes           # Display NES palette
ardk-palette sprite.png --extract # Extract palette from sprite
ardk-palette --convert nes genesis palette.pal  # Convert between formats
```

---

## Part 2: Core Libraries (ARDK Internal)

These are linked into games and provide platform-agnostic APIs.

### 2.1 Entity System (EXISTING)

**Location:** `src/hal/entity.c`, `src/hal/entity.h`

**Features:**
- O(1) allocation/deallocation
- Split pool by category
- Hitbox system
- Tier-aware limits

**API:**
```c
entity_id_t entity_spawn(u8 type, fixed8_8 x, fixed8_8 y);
void entity_free(entity_id_t id);
Entity* entity_get(entity_id_t id);
bool_t entity_collide(entity_id_t a, entity_id_t b);
```

---

### 2.2 Fixed-Point Math Library (PARTIAL)

**Location:** `src/hal/hal.h` (macros), needs expansion

**Current:**
```c
#define FP_TO_INT(x)  ((i16)((x) >> 8))
#define INT_TO_FP(x)  ((fixed8_8)((x) << 8))
#define FP_ADD(a, b)  ((a) + (b))
#define FP_MUL(a, b)  ...
```

**TO ADD:**
```c
// Fixed-point library (platform-optimized)
fixed8_8 fp_sin(angle_t angle);     // 256-entry lookup
fixed8_8 fp_cos(angle_t angle);
angle_t fp_atan2(fixed8_8 y, fixed8_8 x);
fixed8_8 fp_sqrt(fixed8_8 x);       // Approximation
fixed8_8 fp_dist(fixed8_8 dx, fixed8_8 dy);  // Fast distance

// Vector operations
void vec2_normalize(fixed8_8* x, fixed8_8* y);
void vec2_rotate(fixed8_8* x, fixed8_8* y, angle_t angle);
fixed8_8 vec2_dot(fixed8_8 ax, fixed8_8 ay, fixed8_8 bx, fixed8_8 by);
```

**Implementation:** Assembly-optimized per family with C fallback.

---

### 2.3 Random Number Generator (TO BUILD)

**Purpose:** Deterministic RNG for gameplay

**Features:**
- LFSR-based (fast on all platforms)
- Seedable for replays
- Multiple streams
- Range functions

**API:**
```c
void rng_seed(u16 seed);
u8 rng_next(void);              // 0-255
u8 rng_range(u8 min, u8 max);   // Inclusive range
bool_t rng_chance(u8 percent);  // True with X% probability
i8 rng_signed(void);            // -128 to 127
```

---

### 2.4 State Machine Library (TO BUILD)

**Purpose:** Generic state machine for game states and AI

**Features:**
- Enter/Exit/Update callbacks
- State history (for back navigation)
- Timer-based transitions
- Hierarchical states (optional)

**API:**
```c
typedef struct {
    void (*enter)(void);
    void (*update)(void);
    void (*exit)(void);
} State;

void state_init(State* initial);
void state_change(State* new_state);
void state_update(void);
State* state_current(void);
```

---

### 2.5 Input Abstraction (EXISTING - EXPAND)

**Current:** `hal_input_*` functions

**TO ADD:**
```c
// Buffered input for fighting-game style combos
void input_buffer_init(u8 buffer_frames);
bool_t input_check_sequence(const u8* sequence, u8 length);

// Virtual buttons (remappable)
void input_map_button(u8 virtual_btn, u8 physical_btn);
bool_t input_virtual_held(u8 virtual_btn);
bool_t input_virtual_pressed(u8 virtual_btn);

// Analog simulation (D-pad to analog)
fixed8_8 input_get_axis_x(void);
fixed8_8 input_get_axis_y(void);
```

---

### 2.6 Object Pool Library (TO BUILD)

**Purpose:** Generic memory pools beyond entities

**Features:**
- Fixed-size block allocation
- Type-safe wrappers
- Debug overflow detection

**API:**
```c
typedef struct Pool Pool;

Pool* pool_create(u8 block_size, u8 max_blocks, void* memory);
void* pool_alloc(Pool* pool);
void pool_free(Pool* pool, void* block);
u8 pool_count(Pool* pool);
bool_t pool_is_full(Pool* pool);
```

---

### 2.7 Timer System (TO BUILD)

**Purpose:** Frame-based timers and delays

**Features:**
- Multiple timer channels
- One-shot and repeating
- Callbacks or polling

**API:**
```c
typedef void (*timer_callback_t)(u8 timer_id);

u8 timer_create(u16 frames, bool_t repeat, timer_callback_t callback);
void timer_cancel(u8 timer_id);
void timer_update_all(void);  // Call once per frame
u16 timer_remaining(u8 timer_id);
```

---

### 2.8 Text/String Library (TO BUILD)

**Purpose:** Text rendering and string handling

**Features:**
- Number to string (no sprintf dependency)
- Fixed-width text rendering
- Text box system

**API:**
```c
// Number formatting
void str_from_u8(char* buf, u8 value);
void str_from_u16(char* buf, u16 value);
void str_from_u8_hex(char* buf, u8 value);

// Text rendering
void text_print(u8 x, u8 y, const char* str);
void text_print_number(u8 x, u8 y, u16 value, u8 digits);

// Text box
void textbox_open(u8 x, u8 y, u8 w, u8 h);
void textbox_print(const char* str);
void textbox_wait_button(void);
```

---

### 2.9 Scene/Level Management (TO BUILD)

**Purpose:** Level loading and transitions

**Features:**
- Compressed level data
- Streaming for large levels
- Transition effects

**API:**
```c
void scene_load(u8 scene_id);
void scene_transition(u8 scene_id, u8 effect);
void scene_update(void);
u8 scene_current(void);

// Level data access
const u8* level_get_tilemap(void);
const u8* level_get_collision(void);
const u8* level_get_entities(void);
```

---

## Part 3: Middleware (Game-Specific Systems)

These are optional modules games can include.

### 3.1 Survivors-Style Weapon System

```c
// Weapon data
typedef struct {
    u8 type;
    u8 level;
    u8 cooldown;
    u8 damage;
    u8 projectile_count;
    u8 spread_angle;
} Weapon;

void weapon_init(Weapon* w, u8 type);
void weapon_upgrade(Weapon* w);
void weapon_fire(Weapon* w, fixed8_8 x, fixed8_8 y, angle_t aim);
```

### 3.2 XP/Leveling System

```c
void xp_add(u16 amount);
u16 xp_current(void);
u8 xp_level(void);
bool_t xp_check_levelup(void);  // Returns true once on level up
u16 xp_for_next_level(void);
```

### 3.3 Spawner System

```c
typedef struct {
    u8 enemy_type;
    u16 delay_min;
    u16 delay_max;
    u8 count_min;
    u8 count_max;
} SpawnWave;

void spawner_set_waves(const SpawnWave* waves, u8 count);
void spawner_update(void);
void spawner_pause(void);
void spawner_resume(void);
```

---

## Part 4: Pipeline Integration with Tiers

### Current Gaps

The sprite pipeline has per-platform configs but doesn't integrate with HAL tiers.

**Missing connections:**
1. Pipeline doesn't read `hal_tiers.h` limits
2. No sprite count validation against `HAL_MAX_SPRITES`
3. No warning when sprites exceed platform capabilities

### Proposed Integration

Add tier awareness to pipeline:

```python
# In unified_pipeline.py

class PlatformConfig:
    # Existing fields...

    # NEW: Tier integration
    hal_tier: int = 0                # 0=MINIMAL, 1=STANDARD, 2=EXTENDED
    hal_max_entities: int = 32       # From hal_tiers.h
    hal_max_sprites_total: int = 64  # Hardware limit
    hal_max_sprites_line: int = 8    # Per-scanline limit

    @classmethod
    def validate_sprite_count(cls, count: int) -> List[str]:
        """Validate sprite count against tier limits."""
        warnings = []

        if count > cls.hal_max_entities:
            warnings.append(
                f"Sprite count ({count}) exceeds HAL_MAX_ENTITIES ({cls.hal_max_entities})"
            )

        if count > cls.max_sprites_total:
            warnings.append(
                f"Sprite count ({count}) exceeds hardware limit ({cls.max_sprites_total})"
            )

        return warnings

    @classmethod
    def suggest_tier(cls, sprite_count: int, complexity: str) -> str:
        """Suggest appropriate tier for this content."""
        if sprite_count <= 32 and complexity == "low":
            return "MINIMAL (NES, GB, SMS)"
        elif sprite_count <= 128:
            return "STANDARD (Genesis, SNES)"
        else:
            return "EXTENDED (GBA, Neo Geo)"
```

### Metasprite Budgeting

Add metasprite validation:

```python
def validate_metasprite(self, sprite: SpriteInfo) -> Dict:
    """Check if sprite fits platform constraints."""
    tiles_used = (sprite.width // 8) * (sprite.height // 8)

    return {
        'tiles': tiles_used,
        'fits_oam': tiles_used <= self.platform.max_sprites_total,
        'per_line_ok': (sprite.width // 8) <= self.platform.max_sprites_per_line,
        'suggested_split': self._suggest_split(sprite) if not fits else None
    }
```

---

## Part 5: Distribution Strategy

### PyPI Packages

| Package | Purpose | Status |
|---------|---------|--------|
| `ardk-sprites` | Sprite pipeline | Ready |
| `ardk-tilemaps` | Tilemap converter | Planned |
| `ardk-audio` | Audio converter | Planned |
| `ardk-fonts` | Font generator | Planned |
| `ardk-validate` | ROM validator | Planned |
| `ardk-palette` | Palette tools | Planned |

### npm Packages (for web tools)

| Package | Purpose | Status |
|---------|---------|--------|
| `@ardk/sprite-viewer` | Web sprite preview | Planned |
| `@ardk/palette-editor` | Web palette editor | Planned |

### Standalone Binaries

For users without Python:
- PyInstaller builds for Windows/macOS/Linux
- Single executable per tool

---

## Part 6: Priority Order

### Immediate (This Week)
1. Add tier validation to sprite pipeline
2. Create `verify_toolchains.py` script
3. Document current API surface

### Short-term (This Month)
4. Build tilemap converter (Tiled support first)
5. Build font generator
6. Build ROM validator
7. Expand fixed-point math library

### Medium-term (Next Month)
8. Build audio converter
9. Add state machine library
10. Add timer system
11. Prepare sprite pipeline for PyPI

### Long-term (Future)
12. Web-based tools
13. IDE integration (VS Code extension)
14. Visual debugging tools

---

## Summary

**Distributable Tools (6):**
1. Sprite Pipeline - READY
2. Tilemap Converter - TO BUILD
3. Audio Converter - TO BUILD
4. Font Generator - TO BUILD
5. ROM Validator - TO BUILD
6. Palette Tool - TO BUILD

**Core Libraries (9):**
1. Entity System - EXISTS
2. Fixed-Point Math - EXPAND
3. RNG - TO BUILD
4. State Machine - TO BUILD
5. Input Abstraction - EXPAND
6. Object Pool - TO BUILD
7. Timer System - TO BUILD
8. Text/String - TO BUILD
9. Scene Management - TO BUILD

**Middleware (3):**
1. Weapon System - TO BUILD
2. XP/Leveling - TO BUILD
3. Spawner - TO BUILD
