# ARDK — Agentic Retro Dev Kit

A Python toolchain for retro game development: AI-powered asset generation, a
sprite/tile processing pipeline, and cross-platform build orchestration. The
primary target today is **Sega Genesis / Mega Drive (SGDK)**.

> This repo holds the **tooling only**. It was split out of the original
> mono-repo (`SurvivorNES`). Related repos:
>
> | Repo | Contents |
> |------|----------|
> | **epoch** | The flagship Genesis game (SGDK/C), built with these tools |
> | **ardk-assets** | Generated/processed graphics (the old `gfx/` working output) |
> | **ardk-demos** | Small SGDK test projects (`genesis_demo`, `tech_demo_440`) |
> | **ardk-nes-prototype** | The original NES/6502 + multi-platform HAL engine (archived) |

## Requirements

- **Python 3.10+** — for the asset pipeline (`pip install -r requirements-ai.txt`)
- **SGDK** — only needed to build a game; set the `GDK` environment variable
  (<https://github.com/Stephane-D/SGDK>)
- **API keys** (optional) — copy `.env.example` to `.env`; PixelLab and/or
  Pollinations enable AI image generation

## Layout

```text
ardk/
├── tools/
│   ├── ardk_generator.py    # AI asset generation CLI (character/background/parallax/...)
│   ├── ardk_build.py        # Cross-platform build orchestrator
│   ├── pipeline/            # Asset pipeline package (canonical) — entry: pipeline/cli.py
│   ├── asset_generators/    # PixelLab + Pollinations clients, tier/prompt system
│   ├── configs/             # Platform limits + API keys (nes/genesis/snes)
│   └── ...                  # Emulator automation, tile optimizers, misc scripts
├── docs/                    # Architecture, pipeline reference, providers/models
└── artifacts/               # Debug captures (VRAM dumps, automation output)
```

## Canonical entry points

```bash
# Generate a character sprite sheet (AI). Dry-run is ON by default everywhere.
python tools/ardk_generator.py character "neon cyborg knight" -o out/ --platform genesis

# Process an existing sprite through the pipeline (use --no-dry-run to actually write)
python -m tools.pipeline.cli sprite.png -o ../epoch/res/sprites/ --platform genesis --no-dry-run

# Build a game for a platform
python tools/ardk_build.py --platform genesis
```

**Safety:** the pipeline enforces a dry-run-by-default + per-run cost/generation
budget that cannot be bypassed. Pass `--no-dry-run` only when you intend to write
files or spend on API calls.

> **Deprecated:** `tools/unified_pipeline.py` and several older one-off scripts
> are superseded by `tools/pipeline/` + `tools/asset_generators/`. See
> `tools/DEPRECATED.md`.

## License

MIT License
