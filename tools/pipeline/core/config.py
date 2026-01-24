"""
Unified Pipeline Configuration.

All configuration is centralized here. The Pipeline class uses these
configs and ENFORCES safeguards - they cannot be disabled.

Supports loading from:
- .ardk.yaml (preferred)
- .ardk.json
- pipeline.yaml
- pipeline.json

Auto-discovers config files by walking up from current directory to project root.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable
from enum import Enum, auto
from pathlib import Path
import json
import os

# Try to import PyYAML, fall back gracefully
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


# Config file names to search for (in priority order)
CONFIG_FILE_NAMES = [
    '.ardk.yaml',
    '.ardk.json',
    'pipeline.yaml',
    'pipeline.json',
    'ardk.yaml',
    'ardk.json',
]


class InputType(Enum):
    """Detected input type."""
    PNG = auto()          # Standard PNG image
    ASEPRITE = auto()     # .ase/.aseprite file
    PROMPT = auto()       # Text prompt for AI generation
    DIRECTORY = auto()    # Batch directory
    UNKNOWN = auto()


class Platform(Enum):
    """Target platform."""
    NES = "nes"
    GENESIS = "genesis"
    SNES = "snes"
    GAMEBOY = "gameboy"
    MASTER_SYSTEM = "sms"
    PC_ENGINE = "pce"
    AMIGA = "amiga"


@dataclass
class SafeguardConfig:
    """
    ENFORCED safeguards - these CANNOT be bypassed.

    The Pipeline will refuse to operate if these are violated.
    """
    # Generation limits
    max_generations_per_run: int = 5
    max_cost_per_run: float = 0.50

    # Dry run (MUST be explicitly set to False to enable real operations)
    dry_run: bool = True  # DEFAULT: True for safety

    # Confirmation (for destructive operations)
    require_confirmation: bool = True

    # Caching (always enabled, cannot be disabled)
    cache_dir: str = ".ardk_cache"

    # Validation
    validate_inputs: bool = True
    validate_outputs: bool = True

    # Budget tracking persistence
    persist_budget: bool = True
    budget_file: str = ".ardk_budget.json"


@dataclass
class GenerationConfig:
    """Configuration for AI generation."""
    # Provider selection
    provider: str = "pixellab"  # pixellab, pollinations, openai, etc.

    # Generation parameters
    width: int = 32
    height: int = 32

    # PixelLab-specific
    outline: str = "medium"
    shading: str = "soft"
    detail: str = "medium"
    view: str = "side"

    # Multi-directional
    generate_8_directions: bool = False
    use_mirror_optimization: bool = True  # 5 unique + 3 mirrored

    # Style reference
    style_image_path: Optional[str] = None

    # Polling (for async jobs)
    max_poll_attempts: int = 30
    poll_interval: float = 10.0


@dataclass
class ProcessingConfig:
    """Configuration for sprite processing."""
    # Target size
    target_size: int = 32

    # Palette
    palette_name: Optional[str] = None
    forced_palette: Optional[List[int]] = None
    colors_per_palette: int = 16

    # Detection
    filter_text: bool = True
    use_ai_detection: bool = True

    # Optimization
    optimize_tiles: bool = True
    max_tiles: int = 256

    # Collision
    generate_collision: bool = False

    # Dithering
    dither_method: str = "floyd-steinberg"  # floyd-steinberg, ordered, atkinson, none
    dither_strength: float = 1.0


@dataclass
class ExportConfig:
    """Configuration for asset export."""
    # Output format
    output_format: str = "sgdk"  # sgdk, ca65, wla-dx, raw

    # File generation
    generate_res_file: bool = True
    generate_headers: bool = True
    generate_metadata: bool = True

    # Debug output
    save_debug_images: bool = True
    save_intermediate: bool = False


@dataclass
class AsepriteConfig:
    """Configuration for Aseprite integration."""
    # Export settings
    sheet_type: str = "horizontal"  # packed, horizontal, vertical, rows
    scale: int = 1
    trim: bool = False
    shape_padding: int = 1

    # Layer handling
    export_layers_separate: bool = False
    export_tags_separate: bool = True

    # Animation
    convert_to_sequences: bool = True


@dataclass
class PathsConfig:
    """
    Project paths configuration.

    All paths are relative to project root unless absolute.
    """
    # Source directories
    sprites: str = "gfx/sprites"
    backgrounds: str = "gfx/backgrounds"
    generated: str = "gfx/generated"
    processed: str = "gfx/processed"

    # Output directories
    output: str = "src/game/assets"
    chr_output: str = "src/game/assets"
    asm_output: str = "src/game/assets"

    # Cache and temp
    cache: str = ".ardk_cache"
    temp: str = ".ardk_temp"

    def resolve(self, project_root: Path) -> 'PathsConfig':
        """Resolve all paths relative to project root."""
        resolved = PathsConfig()
        for field_name in ['sprites', 'backgrounds', 'generated', 'processed',
                          'output', 'chr_output', 'asm_output', 'cache', 'temp']:
            path_str = getattr(self, field_name)
            path = Path(path_str)
            if not path.is_absolute():
                path = project_root / path
            setattr(resolved, field_name, str(path))
        return resolved


@dataclass
class WatchConfig:
    """Configuration for watch mode."""
    # Directories to watch (relative to project root)
    watch_dirs: List[str] = field(default_factory=lambda: ['gfx/sprites', 'gfx/backgrounds'])

    # File extensions to monitor
    extensions: List[str] = field(default_factory=lambda: ['.png', '.aseprite', '.bmp'])

    # Debounce delay (seconds)
    debounce: float = 1.0

    # Safety limits
    max_file_size_mb: float = 50.0
    max_rate: int = 60  # changes per minute
    max_queue: int = 100
    timeout: float = 30.0  # processing timeout per file

    # Circuit breaker
    circuit_breaker_errors: int = 5
    circuit_breaker_cooldown: float = 60.0

    # Hot reload
    hot_reload_enabled: bool = False
    hot_reload_command: Optional[str] = None


@dataclass
class PalettesConfig:
    """Named palette definitions."""
    # Palette definitions as name -> list of NES color indices
    # Example: player: [0x0F, 0x15, 0x21, 0x30]
    palettes: Dict[str, List[int]] = field(default_factory=dict)

    def get(self, name: str) -> Optional[List[int]]:
        """Get a palette by name."""
        return self.palettes.get(name)

    def add(self, name: str, colors: List[int]):
        """Add a named palette."""
        self.palettes[name] = colors


@dataclass
class PipelineConfig:
    """
    Main pipeline configuration.

    Combines all sub-configurations and enforces safeguards.
    """
    # Target platform
    platform: str = "genesis"

    # Sub-configurations
    safeguards: SafeguardConfig = field(default_factory=SafeguardConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    aseprite: AsepriteConfig = field(default_factory=AsepriteConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)
    watch: WatchConfig = field(default_factory=WatchConfig)
    palettes: PalettesConfig = field(default_factory=PalettesConfig)

    # Project root (auto-detected or explicitly set)
    project_root: Optional[str] = None

    # AI provider for analysis (separate from generation)
    ai_provider: Optional[str] = None
    offline_mode: bool = False

    # Callbacks (for GUI integration)
    on_progress: Optional[Callable[[float, str], None]] = None
    on_stage_start: Optional[Callable[[str], None]] = None
    on_stage_complete: Optional[Callable[[str, Any], None]] = None
    on_error: Optional[Callable[[str, Exception], None]] = None

    # Logging
    verbose: bool = False
    log_file: Optional[str] = None

    def __post_init__(self):
        """Validate configuration after creation."""
        self._validate()

    def _validate(self):
        """Validate configuration values."""
        # Ensure safeguards exist
        if self.safeguards is None:
            self.safeguards = SafeguardConfig()

        # Validate platform
        valid_platforms = ['nes', 'genesis', 'megadrive', 'snes', 'gameboy',
                          'gb', 'sms', 'pce', 'amiga']
        if self.platform.lower() not in valid_platforms:
            raise ValueError(f"Invalid platform: {self.platform}. "
                           f"Valid: {', '.join(valid_platforms)}")

        # Normalize platform name
        if self.platform.lower() == 'megadrive':
            self.platform = 'genesis'
        elif self.platform.lower() == 'gb':
            self.platform = 'gameboy'

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PipelineConfig':
        """Create config from dictionary (for JSON/YAML loading)."""
        # Extract sub-configs
        safeguards = SafeguardConfig(**data.pop('safeguards', {}))
        generation = GenerationConfig(**data.pop('generation', {}))
        processing = ProcessingConfig(**data.pop('processing', {}))
        export = ExportConfig(**data.pop('export', {}))
        aseprite = AsepriteConfig(**data.pop('aseprite', {}))
        paths = PathsConfig(**data.pop('paths', {}))
        watch_data = data.pop('watch', {})
        watch = WatchConfig(**watch_data) if watch_data else WatchConfig()

        # Handle palettes specially (it's a dict of palette names -> colors)
        palettes_data = data.pop('palettes', {})
        palettes = PalettesConfig(palettes=palettes_data)

        return cls(
            safeguards=safeguards,
            generation=generation,
            processing=processing,
            export=export,
            aseprite=aseprite,
            paths=paths,
            watch=watch,
            palettes=palettes,
            **data
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary (for JSON/YAML saving)."""
        from dataclasses import asdict
        return asdict(self)

    @classmethod
    def load(cls, path: str) -> 'PipelineConfig':
        """Load config from JSON or YAML file."""
        path = Path(path)

        with open(path, 'r') as f:
            content = f.read()

        # Determine format based on extension
        if path.suffix in ['.yaml', '.yml']:
            if not HAS_YAML:
                raise ImportError(
                    "PyYAML is required for YAML config files. "
                    "Install with: pip install pyyaml"
                )
            data = yaml.safe_load(content)
        else:
            data = json.loads(content)

        config = cls.from_dict(data or {})
        config.project_root = str(path.parent)
        return config

    def save(self, path: str):
        """Save config to JSON or YAML file."""
        path = Path(path)

        # Filter out non-serializable callbacks
        data = self.to_dict()
        data.pop('on_progress', None)
        data.pop('on_stage_start', None)
        data.pop('on_stage_complete', None)
        data.pop('on_error', None)

        with open(path, 'w') as f:
            if path.suffix in ['.yaml', '.yml']:
                if not HAS_YAML:
                    raise ImportError(
                        "PyYAML is required for YAML output. "
                        "Install with: pip install pyyaml"
                    )
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            else:
                json.dump(data, f, indent=2)

    def get_path(self, name: str) -> Path:
        """Get a resolved path by name."""
        path_str = getattr(self.paths, name, None)
        if path_str is None:
            raise ValueError(f"Unknown path name: {name}")

        path = Path(path_str)
        if not path.is_absolute() and self.project_root:
            path = Path(self.project_root) / path

        return path


def find_config_file(start_dir: Optional[str] = None) -> Optional[Path]:
    """
    Find a config file by walking up from start_dir to root.

    Args:
        start_dir: Directory to start searching from (default: cwd)

    Returns:
        Path to config file if found, None otherwise
    """
    if start_dir is None:
        start_dir = os.getcwd()

    current = Path(start_dir).resolve()

    # Walk up directory tree
    while current != current.parent:
        for config_name in CONFIG_FILE_NAMES:
            config_path = current / config_name
            if config_path.exists():
                return config_path

        current = current.parent

    # Check root
    for config_name in CONFIG_FILE_NAMES:
        config_path = current / config_name
        if config_path.exists():
            return config_path

    return None


def load_project_config(
    config_path: Optional[str] = None,
    start_dir: Optional[str] = None
) -> PipelineConfig:
    """
    Load project configuration.

    Searches for config file if not explicitly provided.
    Returns default config if no file found.

    Args:
        config_path: Explicit path to config file
        start_dir: Directory to start searching from

    Returns:
        PipelineConfig instance
    """
    if config_path:
        return PipelineConfig.load(config_path)

    # Auto-discover config file
    found = find_config_file(start_dir)
    if found:
        return PipelineConfig.load(str(found))

    # Return default config with project_root set to cwd
    config = PipelineConfig()
    config.project_root = start_dir or os.getcwd()
    return config


def get_config() -> PipelineConfig:
    """
    Get the project configuration (convenience function).

    This is the main entry point for scripts to get configuration.
    Caches the result for repeated calls.

    Returns:
        PipelineConfig instance
    """
    # Use a simple cache via function attribute
    if not hasattr(get_config, '_cached'):
        get_config._cached = load_project_config()
    return get_config._cached


def clear_config_cache():
    """Clear the cached configuration."""
    if hasattr(get_config, '_cached'):
        delattr(get_config, '_cached')
