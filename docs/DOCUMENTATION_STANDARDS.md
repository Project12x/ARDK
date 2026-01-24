# ARDK Documentation Standards

> **Version**: 1.0
> **Purpose**: Self-documenting code and auto-generated reference materials

---

## Philosophy

Documentation in ARDK follows three principles:

1. **Code IS Documentation** - Well-structured code with consistent patterns needs fewer comments
2. **Comments Explain WHY** - Not what (the code shows that), but why this approach
3. **Auto-Generate References** - Extract API docs from structured comments

---

## Part 1: Code Documentation Layers

### Layer 1: File Headers (Required)

Every source file starts with a structured header:

```c
/*
 * =============================================================================
 * ARDK - Agentic Retro Development Kit
 * <filename> - <one-line description>
 * =============================================================================
 *
 * <2-4 sentence explanation of what this file does and why it exists>
 *
 * DEPENDENCIES:
 *   - hal.h (required)
 *   - entity.h (for entity types)
 *
 * PLATFORM NOTES:
 *   - NES: Uses zero page $80-$8F for scratch
 *   - Genesis: Uses A6 as entity pool base
 *
 * =============================================================================
 */
```

**Assembly equivalent:**
```asm
;==============================================================================
; ARDK - Agentic Retro Development Kit
; <filename> - <one-line description>
;==============================================================================
;
; <explanation>
;
; REGISTER CONVENTIONS:
;   A     - Accumulator / return value
;   X     - Index / loop counter
;   Y     - Index / entity field offset
;
; ZERO PAGE USAGE:
;   $00-$0F   Engine reserved
;   $10-$1F   This module's scratch
;
;==============================================================================
```

### Layer 2: Section Banners (Required for logical sections)

Group related code with visual separators:

```c
/* ===========================================================================
 * Collision Detection
 *
 * AABB collision using the separating axis theorem.
 * All coordinates are 8.8 fixed-point.
 * =========================================================================== */
```

```asm
;------------------------------------------------------------------------------
; Input Handling
;
; Reads controller state and calculates newly-pressed buttons.
; Call once per frame before game logic.
;------------------------------------------------------------------------------
```

### Layer 3: Function/Macro Documentation (Required for public API)

Use structured doc comments that tools can parse:

```c
/**
 * @brief Spawn a new entity at the given position.
 *
 * Allocates from the entity pool and initializes with default values.
 * Returns ENTITY_ID_NONE if pool is full or category limit reached.
 *
 * @param type    Entity type (ENT_TYPE_xxx or ENT_CAT_xxx | subtype)
 * @param x       X position in 8.8 fixed-point
 * @param y       Y position in 8.8 fixed-point
 *
 * @return Entity ID (0-MAX_ENTITIES-1) or ENTITY_ID_NONE on failure
 *
 * @note Category limits enforced: enemies, projectiles, pickups, effects
 * @see entity_free(), entity_get()
 *
 * @platform NES: Max 32 entities (MINIMAL tier)
 * @platform Genesis: Max 128 entities (STANDARD tier)
 */
entity_id_t entity_spawn(u8 type, fixed8_8 x, fixed8_8 y);
```

**Assembly equivalent:**
```asm
;------------------------------------------------------------------------------
; entity_spawn
;
; Spawn a new entity at the given position.
;
; INPUT:
;   A     = Entity type (ENT_TYPE_xxx)
;   ptr0  = X position (16-bit, 8.8 fixed)
;   ptr1  = Y position (16-bit, 8.8 fixed)
;
; OUTPUT:
;   A     = Entity ID, or $FF if pool full
;   C     = Set if allocation failed
;
; CLOBBERS:
;   X, Y, ptr2
;
; CYCLES:
;   ~120 cycles (success), ~40 cycles (failure)
;------------------------------------------------------------------------------
.proc entity_spawn
    ; Implementation...
.endproc
```

### Layer 4: Inline Comments (Sparingly, for WHY)

**Good:**
```c
/* Skip inactive entities - they're in the free list */
if (!(e->flags & ENT_FLAG_ACTIVE)) continue;

/* Use approximate distance to avoid expensive sqrt */
dist = hal_distance_approx(dx, dy);
```

**Bad:**
```c
/* Increment i */
i++;

/* Check if entity is active */
if (e->flags & ENT_FLAG_ACTIVE) {
```

---

## Part 2: Documentation Files Structure

```
docs/
├── README.md                    # Quick start guide
├── PROJECT_ARCHITECTURE.md      # System design overview
├── PIPELINE_REFERENCE.md        # Asset pipeline details
├── TOOLCHAIN_GUIDE.md           # Toolchain installation
├── DOCUMENTATION_STANDARDS.md   # This file
├── ARDK_LIBRARIES.md            # Library planning
│
├── api/                         # Auto-generated API reference
│   ├── hal.md                   # HAL API
│   ├── entity.md                # Entity system API
│   ├── hal_tiers.md             # Tier system reference
│   └── platform_manifest.md     # Platform capabilities
│
├── guides/                      # How-to guides
│   ├── adding_enemy_type.md
│   ├── porting_to_new_platform.md
│   └── optimizing_for_nes.md
│
└── platform/                    # Platform-specific notes
    ├── nes.md
    ├── genesis.md
    └── gameboy.md
```

---

## Part 3: Auto-Documentation System

### 3.1 Doc Extractor Tool (To Build)

Extract structured comments into markdown:

```python
# tools/extract_docs.py

"""
Extracts API documentation from ARDK source files.

Usage:
    python tools/extract_docs.py src/hal/hal.h -o docs/api/hal.md
    python tools/extract_docs.py src/hal/ -o docs/api/ --recursive
"""

import re
from pathlib import Path

class DocExtractor:
    """Extract documentation from C and assembly files."""

    # Patterns for structured doc comments
    C_DOC_PATTERN = re.compile(
        r'/\*\*\s*\n(.*?)\*/\s*\n\s*(\w+.*?);',
        re.DOTALL
    )

    ASM_DOC_PATTERN = re.compile(
        r';-+\n; (\w+)\n;\n(.*?);-+\n\.proc \1',
        re.DOTALL
    )

    def extract_c(self, content: str) -> list:
        """Extract doc comments from C code."""
        functions = []
        for match in self.C_DOC_PATTERN.finditer(content):
            doc = match.group(1)
            signature = match.group(2)
            functions.append(self._parse_doc(doc, signature))
        return functions

    def _parse_doc(self, doc: str, signature: str) -> dict:
        """Parse structured doc comment."""
        result = {
            'signature': signature.strip(),
            'brief': '',
            'params': [],
            'returns': '',
            'notes': [],
            'platforms': [],
            'see_also': [],
        }

        # Parse @tags
        for line in doc.split('\n'):
            line = line.strip().lstrip('* ')
            if line.startswith('@brief'):
                result['brief'] = line[6:].strip()
            elif line.startswith('@param'):
                result['params'].append(line[6:].strip())
            elif line.startswith('@return'):
                result['returns'] = line[7:].strip()
            elif line.startswith('@note'):
                result['notes'].append(line[5:].strip())
            elif line.startswith('@platform'):
                result['platforms'].append(line[9:].strip())
            elif line.startswith('@see'):
                result['see_also'].append(line[4:].strip())

        return result

    def to_markdown(self, functions: list, title: str) -> str:
        """Generate markdown documentation."""
        md = [f"# {title}\n"]

        for func in functions:
            md.append(f"## `{func['signature']}`\n")
            md.append(f"{func['brief']}\n")

            if func['params']:
                md.append("### Parameters\n")
                for param in func['params']:
                    md.append(f"- {param}\n")

            if func['returns']:
                md.append(f"### Returns\n{func['returns']}\n")

            if func['platforms']:
                md.append("### Platform Notes\n")
                for plat in func['platforms']:
                    md.append(f"- {plat}\n")

            if func['see_also']:
                md.append(f"### See Also\n{', '.join(func['see_also'])}\n")

            md.append("---\n")

        return '\n'.join(md)
```

### 3.2 Header Summary Generator

Generate quick-reference from headers:

```python
# tools/header_summary.py

"""
Generate summary of all public APIs from headers.

Output: docs/api/QUICK_REFERENCE.md
"""

def generate_quick_ref(headers: list) -> str:
    """Generate quick reference card."""
    sections = []

    for header in headers:
        funcs = extract_function_signatures(header)
        macros = extract_macro_definitions(header)
        types = extract_type_definitions(header)

        sections.append(f"""
## {header.stem}

### Types
{format_types(types)}

### Macros
{format_macros(macros)}

### Functions
{format_funcs(funcs)}
""")

    return '\n'.join(sections)
```

### 3.3 Platform Capability Matrix

Auto-generate from platform configs:

```python
# tools/generate_platform_matrix.py

"""
Generate platform comparison matrix from unified_pipeline.py configs.

Output: docs/PLATFORM_MATRIX.md
"""

from unified_pipeline import PLATFORMS

def generate_matrix():
    headers = ['Platform', 'Family', 'Tier', 'Colors', 'Sprites', 'Resolution']

    rows = []
    for name, config in sorted(PLATFORMS.items()):
        rows.append([
            config.name,
            config.cpu_family,
            config.hal_tier_name,
            str(config.colors_per_palette),
            str(config.max_sprites_total),
            f"{config.screen_width}x{config.screen_height}"
        ])

    return format_markdown_table(headers, rows)
```

---

## Part 4: Comment Templates

### 4.1 TODO/FIXME/HACK Tags

Use consistent tags that tools can find:

```c
/* TODO(username): Description of what needs doing */
/* FIXME(username): Description of bug to fix */
/* HACK(username): Explanation of why this hack exists */
/* PERF(username): Note about performance concern */
/* PLATFORM(nes): NES-specific behavior explanation */
```

**Extract with:**
```bash
grep -rn "TODO\|FIXME\|HACK\|PERF" src/
```

### 4.2 Memory Map Comments

Document memory usage in one place:

```c
/* ===========================================================================
 * ZERO PAGE MEMORY MAP ($00-$FF)
 *
 * $00-$0F   Engine core (frame counter, temp vars)
 * $10-$1F   Input system (joy state, previous, pressed)
 * $20-$2F   Player state (position, velocity, health)
 * $30-$3F   Game state (state machine, timers)
 * $40-$4F   Entity iteration temps
 * $50-$5F   Collision temps
 * $60-$7F   Available for game-specific use
 * $80-$FF   Stack overflow area (don't use!)
 * =========================================================================== */
```

### 4.3 Magic Number Documentation

When magic numbers are unavoidable:

```c
/* PPU Control Register bits */
#define PPUCTRL_NMI         0x80    /* Enable NMI on VBlank */
#define PPUCTRL_SPRITE_SIZE 0x20    /* 0=8x8, 1=8x16 sprites */
#define PPUCTRL_BG_TABLE    0x10    /* BG pattern table: 0=$0000, 1=$1000 */
#define PPUCTRL_SPR_TABLE   0x08    /* Sprite pattern table */
#define PPUCTRL_VRAM_INC    0x04    /* VRAM increment: 0=+1, 1=+32 */
#define PPUCTRL_NAMETABLE   0x03    /* Base nametable address */
```

---

## Part 5: Assembly Documentation Conventions

### 5.1 Register Documentation

At file top, document register conventions:

```asm
;==============================================================================
; REGISTER CONVENTIONS (6502)
;
; A     - Accumulator, function return value
; X     - Index register, loop counter, entity ID
; Y     - Index register, field offset within entity
;
; Zero Page Pointers:
; ptr0  - General purpose 16-bit pointer ($00-$01)
; ptr1  - Secondary pointer ($02-$03)
; ptr2  - Entity pointer after ENTITY_GET_PTR ($04-$05)
;
; Scratch:
; tmp0-tmp3 - Temporary storage ($06-$09)
;==============================================================================
```

### 5.2 Cycle Counts

Document critical path timing:

```asm
;------------------------------------------------------------------------------
; wait_vblank - Wait for vertical blank
;
; CYCLES: Variable (0 to ~27,000 depending on when called)
; TIMING: Call at end of game loop, before next frame's updates
;------------------------------------------------------------------------------
.proc wait_vblank
    ; 2 cycles: bit $2002
    ; 2 cycles: bpl loop (not taken = 2, taken = 3)
    ; Total per iteration: 5 cycles (when looping)
@loop:
    bit PPUSTATUS       ; 4 cycles
    bpl @loop           ; 2/3 cycles
    rts                 ; 6 cycles
.endproc
```

### 5.3 Macro Documentation

```asm
;------------------------------------------------------------------------------
; ENTITY_GET_PTR - Get pointer to entity in pool
;
; Calculates: HL = entity_pool + (A * 16)
;
; INPUT:
;   A     = Entity ID (0-31)
;
; OUTPUT:
;   HL    = Pointer to entity structure
;
; CLOBBERS:
;   DE
;
; SIZE: 12 bytes
; CYCLES: 44 cycles
;------------------------------------------------------------------------------
MACRO ENTITY_GET_PTR
    ld h, 0
    ld l, a
    add hl, hl          ; *2 (8 cycles)
    add hl, hl          ; *4 (8 cycles)
    add hl, hl          ; *8 (8 cycles)
    add hl, hl          ; *16 (8 cycles)
    ld de, entity_pool
    add hl, de          ; 8 cycles
ENDM
```

---

## Part 6: Documentation Workflow

### On Every Commit

1. **New functions** get full doc comments
2. **Changed behavior** updates relevant docs
3. **Magic numbers** get named constants with comments

### Weekly Tasks

1. Run `extract_docs.py` to update API reference
2. Check for orphaned TODOs
3. Update PLATFORM_MATRIX.md if configs changed

### Before Release

1. Review all doc files for accuracy
2. Run link checker on markdown
3. Generate PDF reference manual (optional)

---

## Part 7: Documentation Build Integration

Add to `ardk_build.py`:

```python
def build_docs(self) -> bool:
    """Generate documentation from source."""
    print("Generating documentation...")

    # Extract API docs
    for header in (self.root / "src/hal").glob("*.h"):
        output = self.root / "docs/api" / f"{header.stem}.md"
        extract_docs(header, output)

    # Generate platform matrix
    generate_platform_matrix(self.root / "docs/PLATFORM_MATRIX.md")

    # Generate quick reference
    generate_quick_ref(self.root / "docs/api/QUICK_REFERENCE.md")

    print("Documentation generated successfully")
    return True
```

CLI:
```bash
python tools/ardk_build.py --docs
```

---

## Part 8: Living Documentation Principle

### Self-Updating Where Possible

1. **Tier limits** - Read from `hal_tiers.h`, not hardcoded in docs
2. **Platform list** - Generated from `unified_pipeline.py`
3. **API signatures** - Extracted from actual headers

### Version-Controlled

1. All docs in git alongside code
2. Doc changes require same review as code
3. Breaking changes require doc updates

### Discoverable

1. README points to all major docs
2. Each doc links to related docs
3. Code comments reference doc files

---

## Quick Reference: Comment Density Guidelines

| Code Type | Comment Ratio | Notes |
|-----------|---------------|-------|
| Public API | High | Full doc comments on every function |
| Internal functions | Medium | Brief explanation of purpose |
| Simple helpers | Low | Only if non-obvious |
| Critical paths | High | Cycle counts, timing notes |
| Magic numbers | Always | Named constants with comments |
| Algorithms | High | Explain the approach |
| Workarounds | Always | Explain WHY the hack exists |

---

## Summary

1. **Structured headers** on every file
2. **Doc comments** on public APIs (extractable)
3. **Section banners** for logical grouping
4. **WHY comments** inline (not WHAT)
5. **Auto-generate** reference docs from source
6. **Keep docs versioned** with code
