# NES Development Libraries & Resources

**Comprehensive collection of NES development tools, libraries, and middleware**

---

## Core Libraries

### neslib (Shiru)
**The most popular NES C library**
- **URL**: https://github.com/clbr/neslib
- **Language**: C (cc65)
- **Features**: PPU access, sprites, controllers, VRAM updates
- **License**: Public Domain
```bash
# Installation
git clone https://github.com/clbr/neslib lib/neslib
```

### NESFab
**High-level NES programming language**
- **URL**: https://pubby.games/nesfab.html
- **Language**: Custom (compiles to 6502)
- **Features**: Modern syntax, automatic bank switching, built-in game patterns
- **License**: GPL

### cc65
**C compiler and assembler suite**
- **URL**: https://cc65.github.io/
- **Includes**: ca65 (assembler), ld65 (linker), cc65 (C compiler)
- **License**: zlib
- **Status**: ✅ Already installed in tools/cc65

### asm6f
**Fast 6502 assembler**
- **URL**: https://github.com/freem/asm6f
- **Features**: Fast compilation, simple syntax
- **License**: Public Domain

---

## Audio Libraries

### FamiTone2
**Compact NES music engine**
- **URL**: https://github.com/Shiru/NES/tree/master/famitone2
- **Size**: ~1KB ROM
- **Features**: FamiTracker export, SFX support
- **License**: Public Domain
```asm
; Usage
.include "famitone2.asm"
jsr FamiToneInit
jsr FamiToneMusicPlay
; Call FamiToneUpdate every frame in NMI
```

### FamiTone5 (GGSound)
**Enhanced FamiTone**
- **URL**: https://github.com/gradualgames/ggsound
- **Features**: More effects, better compression
- **License**: MIT

### Pently
**Advanced NES audio engine**
- **URL**: https://github.com/pinobatch/pently
- **Features**: Attack/release envelopes, vibrato, portamento
- **License**: zlib
```asm
; More expressive than FamiTone
; Good for complex musical pieces
```

### FamiStudio
**Modern FamiTracker alternative + engine**
- **URL**: https://famistudio.org/
- **Features**: Modern UI, built-in sound engine, NSF export
- **License**: MIT

### MUSE (by Memblers)
**Music System for NES**
- **URL**: https://forums.nesdev.org/viewtopic.php?t=4545
- **Features**: Compact, easy integration

---

## Graphics Libraries

### NESmaker
**Visual NES game creation tool**
- **URL**: https://www.thenew8bitheroes.com/
- **Features**: Visual editor, no coding required
- **License**: Commercial

### NEXXT (NES Screen Tool)
**Graphics editing for NES**
- **URL**: https://frankengraphics.itch.io/nexxt
- **Features**: Tileset editing, nametable editing, CHR management
- **License**: Free

### YY-CHR
**CHR/tile editor**
- **URL**: https://www.romhacking.net/utilities/119/
- **Features**: Edit CHR-ROM directly, multiple formats
- **License**: Freeware

### NES Lightbox
**Online NES graphics tool**
- **URL**: https://famicom.party/neslightbox/
- **Features**: Browser-based, quick prototyping

---

## Compression Libraries

### donut
**NES-optimized compression**
- **URL**: https://github.com/jroweboy/donut-nes
- **Features**: Fast decompression, good ratio
- **License**: MIT
```asm
; Decompresses to VRAM during vblank
jsr donut_decompress
```

### PackBits / RLE
**Simple run-length encoding**
```asm
; Good for simple patterns
; Built-in to many tools
```

### LZ4 (NES port)
**Fast decompression**
- **URL**: https://github.com/emmanuel-marty/lz4ultra
- **Features**: Very fast decode, moderate compression

### Tokumaru's compression
**Various NES compression routines**
- **URL**: https://forums.nesdev.org/viewtopic.php?t=13078
- **Features**: Multiple algorithms optimized for NES

---

## Math Libraries

### Fixed Point Math
```asm
; 8.8 fixed point multiplication
; Common in NES games for smooth movement
.proc mul8x8
    ; A * X = 16-bit result
    sta temp1
    stx temp2
    ; ... implementation
.endproc
```

### Sine/Cosine Tables
```asm
; Pre-calculated for NES
; 256 entry tables common
sine_table:
    .byte $00, $03, $06, $09, $0C, ...
```

### Random Number Generators
```asm
; Linear feedback shift register
; Fast and effective
.proc rand
    lda seed
    asl
    bcc :+
    eor #$1D
:   sta seed
    rts
.endproc
```

### Division Routines
**Integer division for 6502**
- 8-bit / 8-bit
- 16-bit / 8-bit
- Pre-calculated tables for common divisors

---

## Input Libraries

### Multi-tap Support
```asm
; Four Score / Satellite adapter
; Read controllers 3 & 4
```

### Zapper Support
```asm
; Light gun reading
lda $4017
and #%00011000  ; Trigger + Light sensor
```

### Power Pad Support
```asm
; Floor mat controller
; 12 button matrix
```

---

## Mapper Libraries

### MMC3 Library
```asm
; Bank switching helpers
.macro set_prg_bank bank
    lda #$06
    sta $8000
    lda #bank
    sta $8001
.endmacro

.macro set_chr_bank slot, bank
    lda #slot
    sta $8000
    lda #bank
    sta $8001
.endmacro
```

### MMC1 Library
```asm
; Serial register interface
.proc mmc1_write
    ; Write 5 bits serially
    sta $8000
    lsr
    sta $8000
    lsr
    sta $8000
    lsr
    sta $8000
    lsr
    sta $8000
    rts
.endproc
```

### UNROM/UOROM
```asm
; Simple bank switching
; Self-modifying for bus conflicts
```

---

## Effect Libraries

### Sprite Multiplexing
**Display more than 8 sprites per scanline**
```asm
; Sort sprites by Y
; Cycle through visible sprites
; Managed flickering
```

### Parallax Scrolling
```asm
; Multiple scroll speeds
; Split status bar
; Raster effects
```

### Palette Animation
```asm
; Color cycling
; Fade in/out
; Flash effects
```

### Screen Transitions
```asm
; Wipes, fades, iris effects
; Palette-based or tile-based
```

---

## Development Tools

### Emulators (Accuracy-focused)
- **Mesen** - Best debugger, very accurate
- **FCEUX** - Good debugger, widely used
- **Nestopia** - Very accurate
- **puNES** - Accurate, good PPU viewer

### Emulators (Hardware-accurate)
- **Mesen** - Cycle-accurate option
- **bsnes-nes** - Extreme accuracy

### Debuggers
- **Mesen Debugger** - Best overall
- **FCEUX Debugger** - Popular, lots of tutorials
- **NO$NES** - Good for timing analysis

### ROM Analyzers
- **DisPel** - 6502 disassembler
- **NES Disassembler** - Generates asm from ROM
- **fceux-trace** - Execution trace

### Build Systems
- **Make** - Traditional
- **CMake** - Cross-platform
- **NesMake** - NES-specific

---

## Testing Tools

### Test ROMs
- **nestest** - CPU accuracy test
- **sprite_hit_tests** - PPU sprite 0 tests
- **sprite_overflow** - Sprite limit tests
- **apu_test** - Audio accuracy tests

### Validation
- **ines_validator** - iNES header checker
- **ROM_CHECKER** - Mapper validation

---

## Online Resources

### Documentation
- **NESdev Wiki** - https://www.nesdev.org/wiki/
- **6502.org** - http://www.6502.org/
- **Obelisk 6502** - http://www.obelisk.me.uk/6502/

### Communities
- **NESdev Forums** - https://forums.nesdev.org/
- **Reddit r/nesdev** - https://reddit.com/r/nesdev
- **Discord** - NESdev Discord server

### Tutorials
- **Nerdy Nights** - Classic NES tutorial series
- **Famicom Party** - Modern web-based tutorial
- **NES Starter Kit** - Template project

---

## Commercial/Advanced

### PowerPak / EverDrive
**Flash carts for hardware testing**
- Test on real hardware
- Support various mappers

### RGB/HDMI Mods
**For accurate color testing**
- Hi-Def NES
- RetroTINK

---

## Template Projects

### Minimal Template
```
project/
├── src/
│   ├── main.asm
│   ├── header.asm
│   └── reset.asm
├── chr/
│   └── graphics.chr
├── config/
│   └── nes.cfg
└── Makefile
```

### Full Engine Template
```
project/
├── src/
│   ├── engine/
│   │   ├── ppu.asm
│   │   ├── input.asm
│   │   ├── audio.asm
│   │   └── math.asm
│   ├── game/
│   │   ├── player.asm
│   │   ├── enemies.asm
│   │   └── levels.asm
│   └── main.asm
├── assets/
│   ├── sprites/
│   ├── backgrounds/
│   └── music/
├── lib/
│   ├── neslib/
│   └── famitone/
├── tools/
│   └── build scripts
└── build/
```

---

## Installation Scripts

### Quick Setup (All Libraries)
```bash
#!/bin/bash
# install_nes_libs.sh

# Create lib directory
mkdir -p lib

# Clone neslib
git clone https://github.com/clbr/neslib lib/neslib

# Clone FamiTone2
git clone https://github.com/Shiru/NES lib/famitone_repo
cp -r lib/famitone_repo/famitone2 lib/famitone2

# Clone Pently
git clone https://github.com/pinobatch/pently lib/pently

# Clone donut compression
git clone https://github.com/jroweboy/donut-nes lib/donut

echo "NES libraries installed!"
```

---

## Version Compatibility Matrix

| Library | cc65 | asm6 | ca65 | Notes |
|---------|------|------|------|-------|
| neslib | ✅ | ❌ | ✅ | C library |
| FamiTone2 | ✅ | ✅ | ✅ | Pure ASM |
| Pently | ✅ | ❌ | ✅ | ca65 macros |
| donut | ✅ | ✅ | ✅ | Pure ASM |

---

**Keep this document updated as you discover new resources!**
