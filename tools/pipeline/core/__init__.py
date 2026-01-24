"""
ARDK Pipeline Core - Unified Asset Processing with Enforced Safeguards.

This module provides the core pipeline functionality used by both CLI and GUI.
Safeguards are built into the core and CANNOT be bypassed.

Architecture:
    Core (this module)
    ├── Pipeline         - Main orchestrator (CLI/GUI agnostic)
    ├── PipelineConfig   - Unified configuration
    ├── Safeguards       - Budget, caching, validation (ALWAYS enforced)
    ├── Events           - Progress callbacks for GUI
    └── Stages           - Processing stages (input, palette, detect, etc.)

Usage:
    from tools.pipeline.core import Pipeline, PipelineConfig

    # Create pipeline with config
    config = PipelineConfig(
        platform='genesis',
        dry_run=True,  # Preview mode
    )
    pipeline = Pipeline(config)

    # Process assets
    result = pipeline.process('sprite.png', 'output/')

    # Or process Aseprite file
    result = pipeline.process('character.ase', 'output/')

    # Or generate from prompt
    result = pipeline.generate('warrior with sword', 'output/')

Key Principle:
    Safeguards are ENFORCED at the core level. There is no way to bypass:
    - Budget limits (max generations, max cost)
    - Dry-run mode (must be explicitly disabled)
    - Caching (always saves before processing)
    - Validation (checks inputs before processing)
"""

from .config import (
    PipelineConfig,
    SafeguardConfig,
    GenerationConfig,
    ProcessingConfig,
    ExportConfig,
    PathsConfig,
    WatchConfig,
    PalettesConfig,
    # Auto-discovery functions
    find_config_file,
    load_project_config,
    get_config,
    clear_config_cache,
)

from .safeguards import (
    Safeguards,
    SafeguardViolation,
    BudgetExhausted,
    ValidationFailed,
    DryRunActive,
    ConfirmationRequired,
)

from .events import (
    PipelineEvent,
    EventType,
    ProgressEvent,
    StageEvent,
    ErrorEvent,
    EventEmitter,
)

from .pipeline import Pipeline

__all__ = [
    # Main classes
    'Pipeline',
    'PipelineConfig',

    # Configuration
    'SafeguardConfig',
    'GenerationConfig',
    'ProcessingConfig',
    'ExportConfig',
    'PathsConfig',
    'WatchConfig',
    'PalettesConfig',

    # Config discovery
    'find_config_file',
    'load_project_config',
    'get_config',
    'clear_config_cache',

    # Safeguards
    'Safeguards',
    'SafeguardViolation',
    'BudgetExhausted',
    'ValidationFailed',
    'DryRunActive',
    'ConfirmationRequired',

    # Events (for GUI)
    'PipelineEvent',
    'EventType',
    'ProgressEvent',
    'StageEvent',
    'ErrorEvent',
    'EventEmitter',
]
