# Mesen - ARDK Development Emulator

Primary emulator for NES development and automated testing.

## Installation

1. Download Mesen 2 from https://www.mesen.ca/
2. Extract `Mesen.exe` (and dependencies) to this directory
3. Verify installation: `Mesen.exe --version`

## Directory Contents

```
mesen/
├── Mesen.exe           # Main executable (YOU MUST DOWNLOAD)
├── README.md           # This file
├── settings.xml        # ARDK preset settings (optional)
└── Debugger/           # Debug symbol files (auto-generated)
```

## Command Line Usage

### Run ROM Normally
```batch
Mesen.exe "path\to\game.nes"
```

### Headless Test Runner
```batch
Mesen.exe --testrunner --timeout=30 "game.nes" "test.lua"
```

Exit codes:
- `0` = Test passed (script called `emu.stop(0)`)
- `1` = Test failed (script called `emu.stop(1)`)
- Other = Timeout or error

### Load with Lua Script
```batch
Mesen.exe --script="debug.lua" "game.nes"
```

### Load Debug Symbols
```batch
Mesen.exe --dbg="game.dbg" "game.nes"
```

## Keyboard Shortcuts (Default)

| Key | Action |
|-----|--------|
| F5 | Run/Continue |
| F6 | Step Into |
| F7 | Step Over |
| F8 | Step Out |
| F9 | Toggle Breakpoint |
| F12 | Reset |
| Ctrl+R | Soft Reset |
| Ctrl+D | Open Debugger |
| Ctrl+M | Open Memory Viewer |
| Ctrl+P | Open PPU Viewer |

## Debug Symbol Integration

When building with ld65, generate a .dbg file:

```batch
ld65 -C config.cfg -o game.nes --dbgfile game.dbg *.o
```

Mesen will auto-load `game.dbg` if it's in the same directory as `game.nes`,
giving you symbol names in the debugger instead of raw addresses.

## Lua Script Location

Scripts can be loaded from:
1. Command line: `--script="path/to/script.lua"`
2. Script Window: Debug → Script Window → Open
3. Auto-load: Place in Mesen's LuaScripts folder

ARDK test scripts are in: `tools/testing/tests/`

## Settings Recommendations

For development, enable these in Options:

- **Emulation → Run Ahead** - Reduces input latency
- **Video → Integer Scaling** - Pixel-perfect display
- **Audio → Reduce latency** - Better audio sync
- **Debug → Break on BRK** - Catch crashes
- **Debug → Break on uninit memory read** - Find bugs

## Troubleshooting

### "Mesen.exe not found"
Download from https://www.mesen.ca/ and place in this directory.

### Tests timeout immediately
Ensure your Lua script calls `emu.stop(0)` or `emu.stop(1)` to signal completion.

### No debug symbols
Rebuild with `--dbgfile` flag in ld65, or ensure .dbg file is next to .nes file.

### Script errors
Check Mesen's log window (View → Log Window) for Lua error messages.
