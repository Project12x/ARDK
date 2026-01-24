"""
Input Validation Module.

Pre-flight validation for all pipeline inputs to catch errors early
and provide clear feedback.

Usage:
    >>> from pipeline.validation import ImageValidator, validate_pipeline_input
    >>> validator = ImageValidator(platform="genesis")
    >>> result = validator.validate("sprite.png")
    >>> if not result['valid']:
    ...     print(result['errors'])
"""

from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from PIL import Image
import os

from .errors import (
    ValidationError,
    InvalidInputError,
    ImageDimensionError,
    ColorCountError,
    PlatformNotSupportedError,
    safe_image_open,
    validate_path,
    validate_platform,
)


# Platform constraints
PLATFORM_LIMITS = {
    'genesis': {
        'max_sprite_width': 32,
        'max_sprite_height': 32,
        'max_colors_per_palette': 16,
        'max_palettes': 4,
        'tile_size': 8,
        'supported_formats': ['PNG', 'BMP'],
    },
    'nes': {
        'max_sprite_width': 8,
        'max_sprite_height': 16,
        'max_colors_per_palette': 4,
        'max_palettes': 8,
        'tile_size': 8,
        'supported_formats': ['PNG', 'BMP'],
    },
    'snes': {
        'max_sprite_width': 64,
        'max_sprite_height': 64,
        'max_colors_per_palette': 16,
        'max_palettes': 8,
        'tile_size': 8,
        'supported_formats': ['PNG', 'BMP'],
    },
    'gameboy': {
        'max_sprite_width': 8,
        'max_sprite_height': 16,
        'max_colors_per_palette': 4,
        'max_palettes': 2,
        'tile_size': 8,
        'supported_formats': ['PNG', 'BMP'],
    },
    'gba': {
        'max_sprite_width': 64,
        'max_sprite_height': 64,
        'max_colors_per_palette': 256,
        'max_palettes': 16,
        'tile_size': 8,
        'supported_formats': ['PNG', 'BMP'],
    },
}


class ValidationResult:
    """Result of a validation check."""

    def __init__(self, valid: bool = True):
        self.valid = valid
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: Dict[str, Any] = {}

    def add_error(self, message: str):
        """Add an error (marks result as invalid)."""
        self.valid = False
        self.errors.append(message)

    def add_warning(self, message: str):
        """Add a warning (doesn't affect validity)."""
        self.warnings.append(message)

    def add_info(self, key: str, value: Any):
        """Add informational data."""
        self.info[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'valid': self.valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'info': self.info,
        }

    def __bool__(self) -> bool:
        return self.valid


class ImageValidator:
    """Validator for image inputs."""

    def __init__(self, platform: str = 'genesis', strict: bool = False):
        """
        Initialize image validator.

        Args:
            platform: Target platform for validation
            strict: If True, warnings become errors
        """
        self.platform = validate_platform(platform, list(PLATFORM_LIMITS.keys()))
        self.limits = PLATFORM_LIMITS[self.platform]
        self.strict = strict

    def validate(self, image_path: str, check_colors: bool = True) -> ValidationResult:
        """
        Validate an image file for pipeline processing.

        Args:
            image_path: Path to image file
            check_colors: Whether to check color count (expensive)

        Returns:
            ValidationResult with errors/warnings
        """
        result = ValidationResult()

        # Check path
        try:
            path = Path(image_path)
            if not path.exists():
                result.add_error(f"Image file not found: {image_path}")
                return result
            if not path.is_file():
                result.add_error(f"Path is not a file: {image_path}")
                return result
        except Exception as e:
            result.add_error(f"Invalid path: {e}")
            return result

        # Try to load image
        try:
            img = Image.open(image_path)
        except Exception as e:
            result.add_error(f"Failed to load image: {e}")
            return result

        result.add_info('width', img.width)
        result.add_info('height', img.height)
        result.add_info('mode', img.mode)
        result.add_info('format', img.format)

        # Check format
        if img.format and img.format not in self.limits['supported_formats']:
            msg = f"Format {img.format} not in supported formats: {self.limits['supported_formats']}"
            if self.strict:
                result.add_error(msg)
            else:
                result.add_warning(msg)

        # Check dimensions
        max_w = self.limits['max_sprite_width']
        max_h = self.limits['max_sprite_height']

        if img.width > max_w or img.height > max_h:
            result.add_error(
                f"Image {img.width}x{img.height} exceeds {self.platform} "
                f"sprite limits {max_w}x{max_h}"
            )

        # Check tile alignment
        tile_size = self.limits['tile_size']
        if img.width % tile_size != 0:
            msg = f"Width {img.width} not aligned to {tile_size}px tiles"
            if self.strict:
                result.add_error(msg)
            else:
                result.add_warning(msg)

        if img.height % tile_size != 0:
            msg = f"Height {img.height} not aligned to {tile_size}px tiles"
            if self.strict:
                result.add_error(msg)
            else:
                result.add_warning(msg)

        # Check color count (expensive, optional)
        if check_colors:
            try:
                # Get unique colors
                if img.mode == 'P':
                    # Indexed mode - count palette colors
                    palette = img.getpalette()
                    if palette:
                        # Count non-zero palette entries
                        color_count = len([i for i in range(0, len(palette), 3) if i < 768])
                    else:
                        color_count = 0
                else:
                    # Direct color - count unique pixels
                    colors = img.getcolors(maxcolors=257)
                    if colors is None:
                        result.add_warning("Image has more than 256 colors (too many to count)")
                        color_count = 257
                    else:
                        color_count = len(colors)

                result.add_info('color_count', color_count)

                max_colors = self.limits['max_colors_per_palette']
                if color_count > max_colors:
                    result.add_error(
                        f"Image has {color_count} colors, but {self.platform} "
                        f"supports max {max_colors} per palette"
                    )

            except Exception as e:
                result.add_warning(f"Could not check color count: {e}")

        return result

    def validate_batch(self, image_paths: List[str]) -> Dict[str, ValidationResult]:
        """
        Validate multiple images.

        Args:
            image_paths: List of image paths

        Returns:
            Dict mapping paths to ValidationResults
        """
        results = {}
        for path in image_paths:
            results[path] = self.validate(path)
        return results


class AnimationValidator:
    """Validator for animation inputs."""

    SUPPORTED_ACTIONS = ['idle', 'walk', 'run', 'attack', 'jump', 'death', 'hit', 'cast']

    def __init__(self, platform: str = 'genesis'):
        """Initialize animation validator."""
        self.platform = platform
        self.limits = PLATFORM_LIMITS.get(platform, {})

    def validate(self,
                 action: str,
                 frame_count: int,
                 frame_width: int,
                 frame_height: int) -> ValidationResult:
        """
        Validate animation parameters.

        Args:
            action: Animation action name
            frame_count: Number of frames
            frame_width: Width of each frame
            frame_height: Height of each frame

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        # Check action
        if action not in self.SUPPORTED_ACTIONS:
            result.add_error(
                f"Unknown action '{action}'. Supported: {self.SUPPORTED_ACTIONS}"
            )

        # Check frame count
        if frame_count < 1:
            result.add_error("Frame count must be at least 1")
        elif frame_count > 32:
            result.add_warning("Frame count > 32 may cause memory issues")

        # Check dimensions
        if self.limits:
            max_w = self.limits.get('max_sprite_width', 32)
            max_h = self.limits.get('max_sprite_height', 32)

            if frame_width > max_w:
                result.add_error(f"Frame width {frame_width} exceeds limit {max_w}")
            if frame_height > max_h:
                result.add_error(f"Frame height {frame_height} exceeds limit {max_h}")

        result.add_info('action', action)
        result.add_info('frame_count', frame_count)
        result.add_info('total_width', frame_width * frame_count)

        return result


class TilesetValidator:
    """Validator for tileset generation inputs."""

    def __init__(self, platform: str = 'genesis'):
        """Initialize tileset validator."""
        self.platform = platform
        self.limits = PLATFORM_LIMITS.get(platform, {})

    def validate(self,
                 tile_size: int,
                 tile_count: int,
                 description: str = "") -> ValidationResult:
        """
        Validate tileset parameters.

        Args:
            tile_size: Size of each tile (width = height)
            tile_count: Number of tiles to generate
            description: Tileset description

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        # Check tile size
        valid_sizes = [8, 16, 24, 32]
        if tile_size not in valid_sizes:
            result.add_error(f"Tile size must be one of: {valid_sizes}")

        # Check tile count
        if tile_count < 1:
            result.add_error("Tile count must be at least 1")
        elif tile_count > 256:
            result.add_error("Tile count cannot exceed 256")
        elif tile_count > 64:
            result.add_warning("Large tile counts may take a long time to generate")

        # Check description
        if not description or len(description.strip()) < 3:
            result.add_warning("Description is very short - results may be generic")
        elif len(description) > 500:
            result.add_warning("Description is very long - may be truncated by AI")

        result.add_info('tile_size', tile_size)
        result.add_info('tile_count', tile_count)
        result.add_info('total_tiles', tile_count)

        return result


class ConfigValidator:
    """Validator for configuration inputs."""

    @staticmethod
    def validate_seed(seed: Optional[int]) -> ValidationResult:
        """Validate random seed value."""
        result = ValidationResult()

        if seed is not None:
            if not isinstance(seed, int):
                result.add_error(f"Seed must be an integer, got {type(seed)}")
            elif seed < 0:
                result.add_error("Seed must be non-negative")
            elif seed > 2**32 - 1:
                result.add_error("Seed too large (max: 2^32-1)")

        return result

    @staticmethod
    def validate_scale(scale: int, valid_scales: List[int] = [2, 4]) -> ValidationResult:
        """Validate upscale factor."""
        result = ValidationResult()

        if scale not in valid_scales:
            result.add_error(f"Scale must be one of: {valid_scales}")

        result.add_info('scale', scale)
        return result

    @staticmethod
    def validate_provider(provider: str,
                         available_providers: List[str]) -> ValidationResult:
        """Validate AI provider name."""
        result = ValidationResult()

        provider_lower = provider.lower()

        if provider_lower not in [p.lower() for p in available_providers]:
            result.add_error(
                f"Unknown provider '{provider}'. Available: {available_providers}"
            )

        result.add_info('provider', provider_lower)
        return result


def validate_pipeline_input(input_type: str,
                            platform: str = 'genesis',
                            **kwargs) -> ValidationResult:
    """
    Unified validation entry point.

    Args:
        input_type: Type of input to validate ('image', 'animation', 'tileset', etc.)
        platform: Target platform
        **kwargs: Type-specific parameters

    Returns:
        ValidationResult

    Usage:
        >>> result = validate_pipeline_input('image', platform='genesis', path='sprite.png')
        >>> if not result:
        ...     print(result.errors)
    """
    if input_type == 'image':
        validator = ImageValidator(platform)
        return validator.validate(kwargs.get('path', ''))

    elif input_type == 'animation':
        validator = AnimationValidator(platform)
        return validator.validate(
            action=kwargs.get('action', ''),
            frame_count=kwargs.get('frame_count', 0),
            frame_width=kwargs.get('frame_width', 0),
            frame_height=kwargs.get('frame_height', 0),
        )

    elif input_type == 'tileset':
        validator = TilesetValidator(platform)
        return validator.validate(
            tile_size=kwargs.get('tile_size', 16),
            tile_count=kwargs.get('tile_count', 16),
            description=kwargs.get('description', ''),
        )

    else:
        result = ValidationResult()
        result.add_error(f"Unknown input type: {input_type}")
        return result


def validate_output_path(path: str, base_dir: str = None) -> ValidationResult:
    """
    Validate output path for writing.

    Args:
        path: Output path to validate
        base_dir: Base directory to restrict to

    Returns:
        ValidationResult
    """
    result = ValidationResult()

    try:
        path_obj = Path(path)

        # Check parent directory exists or can be created
        parent = path_obj.parent
        if not parent.exists():
            result.add_info('parent_exists', False)
            result.add_warning(f"Parent directory will be created: {parent}")
        else:
            result.add_info('parent_exists', True)

        # Check path traversal
        if base_dir:
            try:
                validate_path(str(path), base_dir)
            except Exception as e:
                result.add_error(str(e))

        # Check if file already exists
        if path_obj.exists():
            result.add_warning(f"Output file already exists and will be overwritten: {path}")

        result.add_info('path', str(path_obj))

    except Exception as e:
        result.add_error(f"Invalid output path: {e}")

    return result
