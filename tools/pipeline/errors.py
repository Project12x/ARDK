"""
Pipeline Error Handling System.

Comprehensive exception hierarchy with clear error messages and
actionable suggestions for users.

Usage:
    >>> from pipeline.errors import ImageLoadError, safe_image_open
    >>> try:
    ...     img = safe_image_open("sprite.png")
    ... except ImageLoadError as e:
    ...     print(f"Error: {e}")
    ...     print(f"Suggestion: {e.suggestion}")
"""

from typing import Optional, List, Dict, Any
from pathlib import Path


class PipelineError(Exception):
    """
    Base exception for all pipeline errors.

    All pipeline exceptions include:
    - Clear error message
    - Actionable suggestion
    - Error code for programmatic handling
    - Optional context data
    """

    error_code: str = "PIPELINE_ERROR"

    def __init__(self,
                 message: str,
                 suggestion: Optional[str] = None,
                 context: Optional[Dict[str, Any]] = None):
        """
        Initialize pipeline error.

        Args:
            message: Clear description of what went wrong
            suggestion: Actionable fix suggestion for the user
            context: Additional context data (file paths, dimensions, etc.)
        """
        self.message = message
        self.suggestion = suggestion or "Check the documentation for guidance."
        self.context = context or {}

        super().__init__(self.message)

    def __str__(self) -> str:
        """Format error with message and suggestion."""
        parts = [f"[{self.error_code}] {self.message}"]
        if self.suggestion:
            parts.append(f"Suggestion: {self.suggestion}")
        if self.context:
            parts.append(f"Context: {self.context}")
        return "\n".join(parts)


# ============================================================================
# File & I/O Errors
# ============================================================================

class FileError(PipelineError):
    """Base class for file-related errors."""
    error_code = "FILE_ERROR"


class FileNotFoundError(FileError):
    """File does not exist or cannot be accessed."""
    error_code = "FILE_NOT_FOUND"

    def __init__(self, path: str, file_type: str = "file"):
        super().__init__(
            message=f"{file_type.capitalize()} not found: {path}",
            suggestion=f"Check that the {file_type} path is correct and the file exists.",
            context={'path': path, 'file_type': file_type}
        )


class FilePermissionError(FileError):
    """File cannot be read or written due to permissions."""
    error_code = "FILE_PERMISSION"

    def __init__(self, path: str, operation: str = "read"):
        super().__init__(
            message=f"Permission denied when trying to {operation}: {path}",
            suggestion=f"Check file permissions and ensure you have {operation} access.",
            context={'path': path, 'operation': operation}
        )


class DiskSpaceError(FileError):
    """Insufficient disk space for operation."""
    error_code = "DISK_SPACE"

    def __init__(self, required_mb: float, available_mb: float):
        super().__init__(
            message=f"Insufficient disk space: need {required_mb:.1f}MB, have {available_mb:.1f}MB",
            suggestion="Free up disk space or use a different output directory.",
            context={'required_mb': required_mb, 'available_mb': available_mb}
        )


# ============================================================================
# Image Errors
# ============================================================================

class ImageError(PipelineError):
    """Base class for image-related errors."""
    error_code = "IMAGE_ERROR"


class ImageLoadError(ImageError):
    """Failed to load or decode image file."""
    error_code = "IMAGE_LOAD"

    def __init__(self, path: str, reason: str = "Unknown"):
        super().__init__(
            message=f"Failed to load image: {path}",
            suggestion=f"Ensure the file is a valid image format (PNG, BMP, etc.). {reason}",
            context={'path': path, 'reason': reason}
        )


class ImageFormatError(ImageError):
    """Image format not supported."""
    error_code = "IMAGE_FORMAT"

    def __init__(self, path: str, actual_format: str, supported_formats: List[str]):
        formats_str = ", ".join(supported_formats)
        super().__init__(
            message=f"Unsupported image format: {actual_format}",
            suggestion=f"Convert the image to a supported format: {formats_str}",
            context={'path': path, 'format': actual_format, 'supported': supported_formats}
        )


class ImageDimensionError(ImageError):
    """Image dimensions exceed platform limits."""
    error_code = "IMAGE_DIMENSION"

    def __init__(self, width: int, height: int, max_width: int, max_height: int):
        super().__init__(
            message=f"Image dimensions {width}x{height} exceed platform limits {max_width}x{max_height}",
            suggestion=f"Resize the image to fit within {max_width}x{max_height} pixels.",
            context={'width': width, 'height': height, 'max_width': max_width, 'max_height': max_height}
        )


class ColorCountError(ImageError):
    """Image has too many colors for platform."""
    error_code = "COLOR_COUNT"

    def __init__(self, color_count: int, max_colors: int, platform: str):
        super().__init__(
            message=f"Image has {color_count} colors, but {platform} supports max {max_colors}",
            suggestion=f"Reduce colors using quantization or palette conversion.",
            context={'color_count': color_count, 'max_colors': max_colors, 'platform': platform}
        )


# ============================================================================
# Validation Errors
# ============================================================================

class ValidationError(PipelineError):
    """Base class for validation errors."""
    error_code = "VALIDATION_ERROR"


class InvalidInputError(ValidationError):
    """Input parameter is invalid."""
    error_code = "INVALID_INPUT"

    def __init__(self, param_name: str, param_value: Any, expected: str):
        super().__init__(
            message=f"Invalid value for {param_name}: {param_value}",
            suggestion=f"Expected {expected}",
            context={'param_name': param_name, 'param_value': param_value, 'expected': expected}
        )


class PathTraversalError(ValidationError):
    """Attempted path traversal detected."""
    error_code = "PATH_TRAVERSAL"

    def __init__(self, path: str):
        super().__init__(
            message=f"Path traversal attempt detected: {path}",
            suggestion="Use only relative paths within the project directory.",
            context={'path': path}
        )


class PlatformNotSupportedError(ValidationError):
    """Target platform not supported."""
    error_code = "PLATFORM_NOT_SUPPORTED"

    def __init__(self, platform: str, supported: List[str]):
        platforms_str = ", ".join(supported)
        super().__init__(
            message=f"Platform not supported: {platform}",
            suggestion=f"Use one of: {platforms_str}",
            context={'platform': platform, 'supported': supported}
        )


# ============================================================================
# API Errors
# ============================================================================

class APIError(PipelineError):
    """Base class for API-related errors."""
    error_code = "API_ERROR"


class APIConnectionError(APIError):
    """Failed to connect to API."""
    error_code = "API_CONNECTION"

    def __init__(self, provider: str, reason: str = "Connection failed"):
        super().__init__(
            message=f"Failed to connect to {provider}: {reason}",
            suggestion="Check your internet connection and API endpoint status.",
            context={'provider': provider, 'reason': reason}
        )


class APITimeoutError(APIError):
    """API request timed out."""
    error_code = "API_TIMEOUT"

    def __init__(self, provider: str, timeout_seconds: float):
        super().__init__(
            message=f"API request to {provider} timed out after {timeout_seconds}s",
            suggestion="Try again or increase the timeout value.",
            context={'provider': provider, 'timeout_seconds': timeout_seconds}
        )


class APIRateLimitError(APIError):
    """API rate limit exceeded."""
    error_code = "API_RATE_LIMIT"

    def __init__(self, provider: str, retry_after: Optional[int] = None):
        retry_msg = f" Retry after {retry_after}s." if retry_after else ""
        super().__init__(
            message=f"Rate limit exceeded for {provider}.{retry_msg}",
            suggestion="Wait before making more requests or use a different provider.",
            context={'provider': provider, 'retry_after': retry_after}
        )


class APIKeyError(APIError):
    """API key missing or invalid."""
    error_code = "API_KEY"

    def __init__(self, provider: str):
        super().__init__(
            message=f"Invalid or missing API key for {provider}",
            suggestion=f"Set the API key in your environment or config file.",
            context={'provider': provider}
        )


class APIQuotaExceededError(APIError):
    """API quota/budget exceeded."""
    error_code = "API_QUOTA"

    def __init__(self, provider: str, quota_type: str = "requests"):
        super().__init__(
            message=f"API quota exceeded for {provider} ({quota_type})",
            suggestion="Wait for quota reset or upgrade your API plan.",
            context={'provider': provider, 'quota_type': quota_type}
        )


# ============================================================================
# Resource Errors
# ============================================================================

class ResourceError(PipelineError):
    """Base class for resource management errors."""
    error_code = "RESOURCE_ERROR"


class MemoryError(ResourceError):
    """Insufficient memory for operation."""
    error_code = "MEMORY"

    def __init__(self, operation: str, required_mb: float):
        super().__init__(
            message=f"Insufficient memory for {operation}: need ~{required_mb:.1f}MB",
            suggestion="Close other applications or process smaller images.",
            context={'operation': operation, 'required_mb': required_mb}
        )


class CacheLimitError(ResourceError):
    """Cache size limit exceeded."""
    error_code = "CACHE_LIMIT"

    def __init__(self, current_mb: float, limit_mb: float):
        super().__init__(
            message=f"Cache size {current_mb:.1f}MB exceeds limit {limit_mb:.1f}MB",
            suggestion="Clear the cache or increase the cache size limit.",
            context={'current_mb': current_mb, 'limit_mb': limit_mb}
        )


# ============================================================================
# Processing Errors
# ============================================================================

class ProcessingError(PipelineError):
    """Base class for processing errors."""
    error_code = "PROCESSING_ERROR"


class QuantizationError(ProcessingError):
    """Color quantization failed."""
    error_code = "QUANTIZATION"

    def __init__(self, reason: str):
        super().__init__(
            message=f"Color quantization failed: {reason}",
            suggestion="Try using a different quantization method or increase color count.",
            context={'reason': reason}
        )


class CompressionError(ProcessingError):
    """Compression failed."""
    error_code = "COMPRESSION"

    def __init__(self, format: str, reason: str):
        super().__init__(
            message=f"Compression failed ({format}): {reason}",
            suggestion="Check input data format and try a different compression method.",
            context={'format': format, 'reason': reason}
        )


class AnimationError(ProcessingError):
    """Animation generation/extraction failed."""
    error_code = "ANIMATION"

    def __init__(self, reason: str):
        super().__init__(
            message=f"Animation processing failed: {reason}",
            suggestion="Check frame count, dimensions, and sprite sheet layout.",
            context={'reason': reason}
        )


# ============================================================================
# Configuration Errors
# ============================================================================

class ConfigError(PipelineError):
    """Base class for configuration errors."""
    error_code = "CONFIG_ERROR"


class MissingDependencyError(ConfigError):
    """Required dependency not installed."""
    error_code = "MISSING_DEPENDENCY"

    def __init__(self, package: str, install_cmd: str):
        super().__init__(
            message=f"Required package not installed: {package}",
            suggestion=f"Install with: {install_cmd}",
            context={'package': package, 'install_cmd': install_cmd}
        )


class InvalidConfigError(ConfigError):
    """Configuration file invalid."""
    error_code = "INVALID_CONFIG"

    def __init__(self, config_file: str, reason: str):
        super().__init__(
            message=f"Invalid configuration in {config_file}: {reason}",
            suggestion="Check the configuration file syntax and required fields.",
            context={'config_file': config_file, 'reason': reason}
        )


# ============================================================================
# Helper Functions
# ============================================================================

def safe_image_open(path: str, convert_to: str = 'RGBA', max_size: tuple = None):
    """
    Safely open an image with comprehensive error handling.

    Args:
        path: Path to image file
        convert_to: Color mode to convert to (RGBA, RGB, etc.)
        max_size: Maximum dimensions (width, height) or None

    Returns:
        PIL Image object

    Raises:
        FileNotFoundError: File doesn't exist
        ImageLoadError: File can't be loaded as an image
        ImageDimensionError: Image exceeds max_size
    """
    from PIL import Image
    import os

    path = str(path)

    # Check file exists
    if not os.path.exists(path):
        raise FileNotFoundError(path, "image")

    # Try to open
    try:
        img = Image.open(path)
    except Exception as e:
        raise ImageLoadError(path, str(e))

    # Check dimensions
    if max_size:
        max_w, max_h = max_size
        if img.width > max_w or img.height > max_h:
            raise ImageDimensionError(img.width, img.height, max_w, max_h)

    # Convert if needed
    if convert_to and img.mode != convert_to:
        try:
            img = img.convert(convert_to)
        except Exception as e:
            raise ImageLoadError(path, f"Failed to convert to {convert_to}: {e}")

    return img


def validate_path(path: str, base_dir: str = None, must_exist: bool = False) -> Path:
    """
    Validate and sanitize a file path.

    Args:
        path: Path to validate
        base_dir: Base directory to restrict to (prevents traversal)
        must_exist: If True, raise error if path doesn't exist

    Returns:
        Validated Path object

    Raises:
        PathTraversalError: Path attempts to escape base_dir
        FileNotFoundError: Path doesn't exist (if must_exist=True)
    """
    path_obj = Path(path).resolve()

    # Check for path traversal
    if base_dir:
        base_obj = Path(base_dir).resolve()
        try:
            path_obj.relative_to(base_obj)
        except ValueError:
            raise PathTraversalError(str(path))

    # Check existence
    if must_exist and not path_obj.exists():
        raise FileNotFoundError(str(path))

    return path_obj


def check_disk_space(path: str, required_mb: float):
    """
    Check if sufficient disk space is available.

    Args:
        path: Directory path to check
        required_mb: Required space in megabytes

    Raises:
        DiskSpaceError: Insufficient disk space
    """
    import shutil

    stat = shutil.disk_usage(path)
    available_mb = stat.free / (1024 * 1024)

    if available_mb < required_mb:
        raise DiskSpaceError(required_mb, available_mb)


def validate_platform(platform: str, supported: List[str] = None) -> str:
    """
    Validate platform name.

    Args:
        platform: Platform name to validate
        supported: List of supported platforms

    Returns:
        Lowercase platform name

    Raises:
        PlatformNotSupportedError: Platform not in supported list
    """
    if supported is None:
        supported = ['genesis', 'nes', 'snes', 'gameboy', 'gba', 'mastersystem']

    platform = platform.lower()

    if platform not in supported:
        raise PlatformNotSupportedError(platform, supported)

    return platform


def handle_error(error: Exception, context: str = "") -> Dict[str, Any]:
    """
    Convert any exception to a standardized error dict.

    Args:
        error: Exception that occurred
        context: Additional context string

    Returns:
        Dict with error details suitable for JSON responses
    """
    if isinstance(error, PipelineError):
        return {
            'success': False,
            'error_code': error.error_code,
            'message': error.message,
            'suggestion': error.suggestion,
            'context': error.context,
        }
    else:
        return {
            'success': False,
            'error_code': 'UNKNOWN_ERROR',
            'message': str(error),
            'suggestion': 'An unexpected error occurred. Check logs for details.',
            'context': {'exception_type': type(error).__name__, 'context': context},
        }
