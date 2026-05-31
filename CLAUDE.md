# ARDK — agent notes

**What this is:** the "Agentic Retro Dev Kit" — a Python toolchain for retro game dev: AI asset generation, a sprite/tile processing pipeline, and cross-platform build orchestration. Primary target today is **Sega Genesis / Mega Drive (SGDK)**. See `README.md` for usage.

**Origin:** split out on 2026-05-30 from the old `SurvivorNES` mono-repo. Sibling repos: `epoch` (the flagship Genesis game built with these tools), `ardk-assets` (generated gfx), `ardk-demos` (SGDK demos), `ardk-nes-prototype` (the archived original NES/6502 + multi-platform HAL engine that predates the Genesis pivot).

## Ground rule: the code is canon
Don't trust commit messages or `.md` docs to be accurate — heavy drift after a 4-month gap and a NES→Genesis pivot. Crucially for this repo: **"a class/module exists" ≠ "it works end-to-end."** Much of the multi-platform / tier breadth is designed-but-not-proven. Verify before relying on a feature.

## Canonical entry points (under tools/)
- `tools/ardk_generator.py` — AI asset generation CLI (`character`/`background`/`parallax`/`animated-tile`/`batch`/`analyze`/`list-presets`). Providers: PixelLab (pixel-art) + Pollinations/flux (cheap).
- `python -m tools.pipeline.cli` — canonical asset processing pipeline (palette quantization, tile dedup w/ flip, SGDK `.res`/Genesis export, VGM/audio, Tiled maps).
- `tools/ardk_build.py` — cross-platform build orchestrator.
- Emulator automation: `tools/blastem_remote.py`, `tools/monitor_gamestate.py`, `tools/inspect_vram.py` — GDB-remote control of BlastEm to read Work-RAM/VRAM and automate playtests.

**Safety:** the pipeline enforces dry-run ON by default + per-run cost/generation budget that can't be bypassed. Use `--no-dry-run` only to actually write files / spend on APIs.

**Deprecated** (see `tools/DEPRECATED.md`): `tools/unified_pipeline.py` and older one-off scripts, superseded by `tools/pipeline/` + `tools/asset_generators/`.
