---
description: Genesis/68000 development checklist - prevents expensive math mistakes
---

# 68000 Development Workflow

> **CRITICAL**: Before writing ANY code for the Sega Genesis, review this.

## The Golden Rules

1. **NEVER use `/` or `%` in hot paths** (140-170 cycles each!)
2. **NEVER multiply by non-power-of-2** (70+ cycles)
3. **Use `>>` for divide, `<<` for multiply, `&` for modulo**
4. **All grid widths MUST be power-of-2** (16, 32, 64, etc.)

## Quick Conversion Reference

| Bad (Slow) | Good (Fast) | Savings |
|------------|-------------|---------|
| `x / 8` | `x >> 3` | 95%+ |
| `x / 2` | `x >> 1` | 95%+ |
| `x % 64` | `x & 63` | 95%+ |
| `x * 20` | AVOID or LUT | N/A |
| `random() % 1280` | `random() & 0x3FF` | 95%+ |

## Before Committing Code

// turbo-all

1. Search for `/` operators: `grep -n "/ [0-9]" src/**/*.c`
2. Search for `%` operators: `grep -n "% [0-9]" src/**/*.c`
3. Search for non-power-of-2 multiplies: Review any `* [constant]`
4. Verify grid dimensions: Check `#define GRID_W` is power-of-2
5. Build and test: `.\build.bat`

## Full Reference

See: [OPTIMIZATION_GUIDE.md](../projects/epoch/docs/OPTIMIZATION_GUIDE.md)
