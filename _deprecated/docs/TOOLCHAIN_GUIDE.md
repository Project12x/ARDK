# ARDK Toolchain & Library Guide

> **Version**: 1.0
> **Purpose**: Installation guide for platform toolchains, organized by CPU family

---

## Quick Reference: Primary Targets

| Platform | CPU Family | Toolchain | Install Priority |
|----------|-----------|-----------|------------------|
| **NES** | 6502 | cc65 | HIGH |
| **Genesis/MD** | 68K | SGDK | HIGH |
| **Game Boy** | Z80 | RGBDS | HIGH |
| **SNES** | 65816 | PVSnesLib | MEDIUM |
| **PC Engine** | 6502 | HuC | MEDIUM |
| **GBA** | ARM | devkitARM | MEDIUM |

---

## 1. 6502 Family Toolchains

### cc65 (NES, C64, Atari, Apple II)
**Our primary 6502 toolchain - install first!**

```bash
# Windows (via MSYS2 or manual)
# Download from: https://cc65.github.io/
# Add bin/ to PATH

# macOS
brew install cc65

# Linux
sudo apt install cc65  # Debian/Ubuntu
# or build from source for latest

# Verify
ca65 --version
ld65 --version
cc65 --version
```

**Directory structure:**
```
tools/
  toolchains/
    cc65/
      bin/         # ca65, ld65, cc65, etc.
      lib/         # Runtime libraries
      cfg/         # Linker configs (nes.cfg, c64.cfg)
      include/     # C headers
```

**Environment variable:**
```bash
CC65_HOME=C:\path\to\cc65
PATH=%CC65_HOME%\bin;%PATH%
```

### HuC (PC Engine / TurboGrafx-16)
**65C02-based, different toolchain from cc65**

```bash
# Clone and build
git clone https://github.com/pce-devel/huc.git
cd huc
make

# Includes:
# - huc (C compiler)
# - pceas (assembler)
# - nesasm (NES variant, avoid for PCE)
```

**Directory structure:**
```
tools/
  toolchains/
    huc/
      bin/         # huc, pceas
      include/     # PCE headers
```

---

## 2. Z80 Family Toolchains

### RGBDS (Game Boy / Game Boy Color)
**THE standard for Game Boy - install this!**

```bash
# Windows
# Download from: https://rgbds.gbdev.io/install/
# Or via Chocolatey: choco install rgbds

# macOS
brew install rgbds

# Linux
sudo apt install rgbds  # Debian/Ubuntu (might be old)
# For latest: build from source

# Verify
rgbasm --version
rgblink --version
rgbfix --version
rgbgfx --version  # Graphics conversion tool!
```

**Directory structure:**
```
tools/
  toolchains/
    rgbds/
      bin/         # rgbasm, rgblink, rgbfix, rgbgfx
```

**Note:** RGBDS includes `rgbgfx` which converts PNG to Game Boy format. We should integrate this into our pipeline!

### devkitSMS (Master System / Game Gear)
**Z80 toolchain for Sega 8-bit**

```bash
# Uses SDCC + WLA-DX
# Download devkitSMS from: https://github.com/sverx/devkitSMS

# Requires:
# - SDCC (Small Device C Compiler)
# - WLA-DX (assembler/linker)

# SDCC
# Windows: https://sdcc.sourceforge.net/
# macOS: brew install sdcc
# Linux: sudo apt install sdcc

# WLA-DX
git clone https://github.com/vhelin/wla-dx.git
cd wla-dx && cmake . && make
```

**Directory structure:**
```
tools/
  toolchains/
    devkitSMS/
      sdcc/          # SDCC compiler
      wla-dx/        # wla-z80, wlalink
      devkitSMS/     # SMS-specific libs
```

### GBDK-2020 (Alternative GB toolchain)
**C-focused Game Boy development**

```bash
# Download from: https://github.com/gbdk-2020/gbdk-2020/releases

# Includes:
# - lcc (C compiler)
# - GBDK libraries
# - Examples
```

---

## 3. 68000 Family Toolchains

### SGDK (Sega Genesis / Mega Drive)
**THE standard for Genesis - install this!**

```bash
# Windows (primary platform for SGDK)
# Download from: https://github.com/Stephane-D/SGDK/releases

# Extract to C:\SGDK (or similar short path)
# Set environment variable:
GDK=C:\SGDK
PATH=%GDK%\bin;%PATH%

# Linux/macOS
# Use Docker or build from source
docker pull ghcr.io/stephane-d/sgdk:latest
```

**Directory structure:**
```
tools/
  toolchains/
    sgdk/
      bin/           # make, rescomp, tools
      lib/           # SGDK libraries
      inc/           # Headers
      src/           # SGDK source (for reference)
```

**SGDK includes critical tools:**
- `rescomp` - Resource compiler (sprites, tilemaps, music)
- `xgmtool` - XGM music format tools
- `appack` - Compression

### VBCC + vasm (Amiga, Atari ST)
**Cross-platform 68K C compiler**

```bash
# Download from: http://www.compilers.de/vbcc.html

# Components:
# - vbcc (C compiler)
# - vasm (assembler, Motorola syntax)
# - vlink (linker)
```

**Directory structure:**
```
tools/
  toolchains/
    vbcc/
      bin/           # vc, vasmm68k_mot, vlink
      targets/       # Target-specific configs
```

### ngdevkit (Neo Geo)
**Open-source Neo Geo SDK**

```bash
# Linux/macOS (primary)
# Follow: https://github.com/dciabrin/ngdevkit

# Windows: Use WSL2

# Requires:
# - GNU m68k toolchain
# - Custom Neo Geo tools
```

---

## 4. 65816 Family Toolchains

### PVSnesLib (SNES / Super Famicom)
**Primary SNES toolchain**

```bash
# Download from: https://github.com/alekmaul/pvsneslib/releases

# Windows setup:
# Extract to C:\pvsneslib
PVSNESLIB_HOME=C:\pvsneslib
PATH=%PVSNESLIB_HOME%\devkitsnes\bin;%PATH%

# Includes:
# - 816-tcc (C compiler)
# - wla-65816 (assembler)
# - gfx4snes (graphics converter)
# - snesbrr (audio converter)
```

**Directory structure:**
```
tools/
  toolchains/
    pvsneslib/
      devkitsnes/    # Tools
      include/       # SNES headers
      lib/           # Libraries
```

### ca65 65816 mode
**cc65's 65816 support (limited)**

```bash
# ca65 supports 65816 via:
ca65 --cpu 65816 source.asm

# Less mature than WLA-65816 for SNES
```

---

## 5. ARM Family Toolchains

### devkitARM (GBA, DS)
**Part of devkitPro**

```bash
# Windows/macOS/Linux
# Install devkitPro: https://devkitpro.org/wiki/Getting_Started

# Windows: Run graphical installer
# macOS: brew install devkitpro-pacman
# Linux: Follow pacman setup

# Install GBA tools:
dkp-pacman -S gba-dev

# Environment:
DEVKITPRO=/opt/devkitpro  # or Windows path
DEVKITARM=$DEVKITPRO/devkitARM
PATH=$DEVKITARM/bin:$PATH
```

**Directory structure:**
```
tools/
  toolchains/
    devkitARM/
      bin/           # arm-none-eabi-gcc, etc.
      lib/           # libgba, libtonc
```

### Butano (Modern GBA Framework)
**High-level C++ framework for GBA**

```bash
# Requires devkitARM first
git clone https://github.com/GValiente/butano.git

# Set environment:
BUTANO_HOME=/path/to/butano
```

---

## 6. Platform-Agnostic Tools

### Python Requirements (for our pipeline)
```bash
pip install pillow numpy python-dotenv httpx
```

### Graphics Tools (Universal)

| Tool | Purpose | Platforms |
|------|---------|-----------|
| **Aseprite** | Sprite editor | All |
| **GIMP** | Image editing | All |
| **Tiled** | Tilemap editor | All |
| **LDTK** | Level designer | All |

### Audio Tools

| Tool | Platform | Purpose |
|------|----------|---------|
| **FamiTracker** | NES | .ftm music |
| **DefleMask** | Multi | Genesis, GB, SMS |
| **SnesMod** | SNES | .it/.xm conversion |
| **OpenMPT** | PC/Amiga | MOD/XM/IT |

---

## 7. Recommended Directory Structure

```
SurvivorNES/
├── tools/
│   ├── unified_pipeline.py     # Our sprite pipeline
│   ├── ardk_build.py           # Build orchestrator
│   │
│   ├── toolchains/             # External toolchains (gitignored)
│   │   ├── cc65/               # 6502 family
│   │   ├── rgbds/              # Game Boy
│   │   ├── sgdk/               # Genesis
│   │   ├── pvsneslib/          # SNES
│   │   ├── devkitARM/          # GBA
│   │   ├── huc/                # PC Engine
│   │   ├── devkitSMS/          # Master System
│   │   ├── vbcc/               # Amiga
│   │   └── ngdevkit/           # Neo Geo
│   │
│   ├── converters/             # ARDK asset converters
│   │   ├── tilemap_converter.py
│   │   ├── audio_converter.py
│   │   └── font_converter.py
│   │
│   └── validators/             # Build validation
│       ├── rom_validator.py
│       └── asset_validator.py
│
├── src/
│   └── hal/
│       ├── asm/                # Assembly HAL per family
│       ├── nes/                # NES-specific
│       ├── genesis/            # Genesis-specific
│       ├── gb/                 # Game Boy-specific
│       └── ...
│
└── .env.toolchains             # Toolchain paths (gitignored)
```

---

## 8. Environment Configuration

Create `.env.toolchains` (add to .gitignore):

```bash
# 6502 Family
CC65_HOME=C:/tools/cc65
HUC_HOME=C:/tools/huc

# Z80 Family
RGBDS_HOME=C:/tools/rgbds
SDCC_HOME=C:/tools/sdcc

# 68000 Family
GDK=C:/SGDK
VBCC_HOME=C:/tools/vbcc

# 65816 Family
PVSNESLIB_HOME=C:/pvsneslib

# ARM Family
DEVKITPRO=C:/devkitPro
DEVKITARM=${DEVKITPRO}/devkitARM
```

---

## 9. Installation Priority

### Phase 1: Core Targets (Install Now)
1. **cc65** - NES development (our primary platform)
2. **RGBDS** - Game Boy development
3. **SGDK** - Genesis development
4. **Python + Pillow** - Asset pipeline

### Phase 2: Secondary Targets
5. **PVSnesLib** - SNES development
6. **devkitARM** - GBA development
7. **HuC** - PC Engine development

### Phase 3: Extended Platforms
8. **devkitSMS** - Master System
9. **VBCC** - Amiga
10. **ngdevkit** - Neo Geo

---

## 10. Verification Script

Create `tools/verify_toolchains.py`:

```python
#!/usr/bin/env python3
"""Verify installed toolchains for ARDK."""

import shutil
import subprocess
import os

TOOLCHAINS = {
    '6502': {
        'cc65': ['ca65', 'ld65', 'cc65'],
        'huc': ['huc', 'pceas'],
    },
    'z80': {
        'rgbds': ['rgbasm', 'rgblink', 'rgbfix', 'rgbgfx'],
        'sdcc': ['sdcc'],
        'wla-z80': ['wla-z80', 'wlalink'],
    },
    '68k': {
        'sgdk': ['make'],  # SGDK uses make
        'vbcc': ['vc', 'vasmm68k_mot', 'vlink'],
    },
    '65816': {
        'pvsneslib': ['816-tcc', 'wla-65816'],
    },
    'arm': {
        'devkitarm': ['arm-none-eabi-gcc', 'arm-none-eabi-as'],
    },
}

def check_tool(tool):
    """Check if tool is in PATH."""
    return shutil.which(tool) is not None

def main():
    print("ARDK Toolchain Verification")
    print("=" * 50)

    for family, toolchains in TOOLCHAINS.items():
        print(f"\n{family.upper()} Family:")
        for name, tools in toolchains.items():
            found = all(check_tool(t) for t in tools)
            status = "✓" if found else "✗"
            print(f"  {status} {name}: {', '.join(tools)}")

if __name__ == "__main__":
    main()
```

---

## Next Steps

After installing toolchains:
1. Run `python tools/verify_toolchains.py` to confirm
2. Test builds with `python tools/ardk_build.py --validate`
3. Process test sprites with `python tools/unified_pipeline.py`
