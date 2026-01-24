# ARDK Emulators

Development emulators for testing and debugging ARDK projects.

## Directory Structure

```
emulators/
├── mesen/              # Mesen (NES/SNES/GB/GBA) - Primary development emulator
│   ├── Mesen.exe       # Main executable (download separately)
│   ├── settings.xml    # ARDK-specific settings preset
│   └── README.md       # Setup instructions
│
├── fceux/              # FCEUX (NES) - Alternative/legacy testing
│   └── README.md
│
├── snes9x/             # Snes9x (SNES) - Future HAL tier testing
│   └── README.md
│
├── mgba/               # mGBA (GBA/GB) - Future HAL tier testing
│   └── README.md
│
└── genesis/            # Blastem/Gens (Genesis/MD) - Future HAL tier testing
    └── README.md
```

## Primary Emulator: Mesen

Mesen is the recommended emulator for ARDK development due to:

- **Headless test runner mode** (`--testrunner`) for CI/CD
- **Lua scripting API** for automated testing and debugging
- **Accurate emulation** with cycle-accurate PPU/CPU
- **Built-in debugging tools** (memory viewer, trace logger, debugger)
- **Multi-platform support** (NES, SNES, GB, GBA in Mesen 2)

### Download

- **Mesen 2** (recommended): https://www.mesen.ca/
- **Mesen Classic** (NES only): https://github.com/SourMesen/Mesen/releases

### Installation

1. Download Mesen from the link above
2. Extract to `tools/emulators/mesen/`
3. Run tests: `tools/testing/run_tests.bat`

## Emulator Capabilities Matrix

| Feature              | Mesen | FCEUX | Snes9x | mGBA | Blastem |
|---------------------|-------|-------|--------|------|---------|
| Headless mode       | ✅    | ❌    | ❌     | ✅   | ✅      |
| Lua scripting       | ✅    | ✅    | ❌     | ✅   | ❌      |
| Memory viewer       | ✅    | ✅    | ✅     | ✅   | ✅      |
| Trace logger        | ✅    | ✅    | ✅     | ✅   | ✅      |
| Breakpoints         | ✅    | ✅    | ✅     | ✅   | ✅      |
| Cycle accuracy      | ✅    | ⚠️    | ⚠️     | ✅   | ✅      |
| CI/CD integration   | ✅    | ❌    | ❌     | ✅   | ✅      |

## Usage with ARDK

### Running Tests (Headless)

```batch
tools\emulators\mesen\Mesen.exe --testrunner --timeout=30 ^
    projects\hal_demo\build\hal_demo.nes ^
    tools\testing\tests\sanity_test.lua
```

### Interactive Debugging

```batch
tools\emulators\mesen\Mesen.exe projects\hal_demo\build\hal_demo.nes
```

Then load debug scripts via Debug → Script Window.

### Batch Testing

```batch
tools\testing\run_tests.bat
```
