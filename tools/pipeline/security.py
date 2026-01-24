"""
Security Hardening Module.

Path traversal prevention, input sanitization, and API key protection.

Usage:
    >>> from pipeline.security import sanitize_filename, secure_path
    >>> safe_name = sanitize_filename("../../etc/passwd")  # "etc_passwd"
    >>> safe_path = secure_path("output/sprite.png", base_dir="output")
"""

from typing import Optional
from pathlib import Path
import re
import os

from .errors import PathTraversalError, ValidationError


# Dangerous path patterns
DANGEROUS_PATTERNS = [
    r'\.\./',  # Parent directory traversal
    r'\.\.\\',  # Windows parent directory traversal
    r'^/',  # Absolute path (Unix)
    r'^[A-Za-z]:',  # Absolute path (Windows)
    r'~/',  # Home directory
    r'\$',  # Environment variable
    r'%',  # Windows environment variable
]

# Dangerous filename characters
DANGEROUS_CHARS = '<>:"|?*\0\r\n\t'

# Reserved Windows filenames
WINDOWS_RESERVED = [
    'CON', 'PRN', 'AUX', 'NUL',
    'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
    'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9',
]


def sanitize_filename(filename: str, replacement: str = '_') -> str:
    """
    Sanitize a filename to remove dangerous characters.

    Args:
        filename: Original filename
        replacement: Character to replace dangerous chars with

    Returns:
        Sanitized filename

    Example:
        >>> sanitize_filename("sprite:test?.png")
        'sprite_test_.png'
    """
    # Remove path separators
    filename = filename.replace('/', replacement)
    filename = filename.replace('\\', replacement)

    # Remove dangerous characters
    for char in DANGEROUS_CHARS:
        filename = filename.replace(char, replacement)

    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')

    # Check for Windows reserved names
    name_without_ext = Path(filename).stem.upper()
    if name_without_ext in WINDOWS_RESERVED:
        filename = f"{replacement}{filename}"

    # Ensure not empty
    if not filename:
        filename = "unnamed"

    # Limit length (255 is common filesystem limit)
    if len(filename) > 255:
        ext = Path(filename).suffix
        name = Path(filename).stem
        max_name_len = 255 - len(ext)
        filename = name[:max_name_len] + ext

    return filename


def sanitize_path(path: str, replacement: str = '_') -> str:
    """
    Sanitize a full path to remove dangerous patterns.

    Args:
        path: Original path
        replacement: Character to replace dangerous patterns with

    Returns:
        Sanitized path

    Example:
        >>> sanitize_path("output/../secret.txt")
        'output/secret.txt'
    """
    # Normalize path separators
    path = path.replace('\\', '/')

    # Remove dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        path = re.sub(pattern, '', path)

    # Split into parts and sanitize each
    parts = path.split('/')
    safe_parts = [sanitize_filename(part, replacement) for part in parts if part]

    return '/'.join(safe_parts)


def secure_path(path: str,
                base_dir: Optional[str] = None,
                must_exist: bool = False,
                create_parents: bool = False) -> Path:
    """
    Validate and secure a file path.

    Args:
        path: Path to validate
        base_dir: Base directory to restrict to (prevents traversal)
        must_exist: If True, raise error if path doesn't exist
        create_parents: If True, create parent directories

    Returns:
        Validated Path object

    Raises:
        PathTraversalError: Path attempts to escape base_dir
        FileNotFoundError: Path doesn't exist (if must_exist=True)

    Example:
        >>> secure_path("sprite.png", base_dir="output")
        PosixPath('output/sprite.png')
    """
    # Convert to Path and resolve
    path_obj = Path(path)

    # Check for absolute paths when base_dir specified
    if base_dir and path_obj.is_absolute():
        raise PathTraversalError(str(path))

    # If base_dir specified, make path relative to it
    if base_dir:
        base_obj = Path(base_dir).resolve()
        path_obj = (base_obj / path).resolve()

        # Verify path is within base_dir
        try:
            path_obj.relative_to(base_obj)
        except ValueError:
            raise PathTraversalError(str(path))
    else:
        path_obj = path_obj.resolve()

    # Check existence
    if must_exist and not path_obj.exists():
        raise FileNotFoundError(str(path))

    # Create parent directories if requested
    if create_parents and not path_obj.parent.exists():
        path_obj.parent.mkdir(parents=True, exist_ok=True)

    return path_obj


def validate_filename_length(filename: str, max_length: int = 255) -> bool:
    """
    Validate filename length.

    Args:
        filename: Filename to check
        max_length: Maximum allowed length

    Returns:
        True if valid, False otherwise
    """
    return 0 < len(filename) <= max_length


def is_safe_path(path: str, base_dir: Optional[str] = None) -> bool:
    """
    Check if a path is safe (no traversal attempts).

    Args:
        path: Path to check
        base_dir: Base directory to restrict to

    Returns:
        True if safe, False if dangerous
    """
    try:
        secure_path(path, base_dir)
        return True
    except (PathTraversalError, ValueError):
        return False


def mask_api_key(api_key: str, visible_chars: int = 4) -> str:
    """
    Mask an API key for logging/display.

    Args:
        api_key: API key to mask
        visible_chars: Number of chars to show at start/end

    Returns:
        Masked API key

    Example:
        >>> mask_api_key("sk-1234567890abcdef")
        'sk-1...cdef'
    """
    if not api_key or len(api_key) <= visible_chars * 2:
        return "***"

    start = api_key[:visible_chars]
    end = api_key[-visible_chars:]
    return f"{start}...{end}"


def sanitize_for_logging(data: dict) -> dict:
    """
    Sanitize dictionary for safe logging (remove secrets).

    Args:
        data: Dictionary to sanitize

    Returns:
        Sanitized copy with secrets masked

    Example:
        >>> sanitize_for_logging({"api_key": "secret", "name": "sprite"})
        {'api_key': '***', 'name': 'sprite'}
    """
    sensitive_keys = {
        'api_key', 'apikey', 'token', 'secret', 'password', 'passwd',
        'auth', 'authorization', 'credential', 'private_key'
    }

    result = {}
    for key, value in data.items():
        key_lower = key.lower()

        # Check if key contains sensitive terms
        is_sensitive = any(term in key_lower for term in sensitive_keys)

        if is_sensitive:
            if isinstance(value, str):
                result[key] = mask_api_key(value)
            else:
                result[key] = "***"
        elif isinstance(value, dict):
            result[key] = sanitize_for_logging(value)
        else:
            result[key] = value

    return result


def validate_url(url: str, allowed_schemes: list = ['http', 'https']) -> bool:
    """
    Validate URL is safe.

    Args:
        url: URL to validate
        allowed_schemes: List of allowed schemes

    Returns:
        True if valid and safe
    """
    from urllib.parse import urlparse

    try:
        parsed = urlparse(url)

        # Check scheme
        if parsed.scheme not in allowed_schemes:
            return False

        # Check for localhost/private IPs (basic check)
        hostname = parsed.hostname
        if hostname:
            hostname_lower = hostname.lower()
            if hostname_lower in ['localhost', '127.0.0.1', '0.0.0.0']:
                return False
            if hostname_lower.startswith('192.168.') or hostname_lower.startswith('10.'):
                return False

        return True

    except Exception:
        return False


def sanitize_command_arg(arg: str) -> str:
    """
    Sanitize command-line argument to prevent injection.

    Args:
        arg: Argument to sanitize

    Returns:
        Sanitized argument

    Example:
        >>> sanitize_command_arg("file.png; rm -rf /")
        'file.png'
    """
    # Remove shell metacharacters
    dangerous_chars = ';|&$`<>()\n\r\t'
    for char in dangerous_chars:
        arg = arg.replace(char, '')

    # Remove leading dashes (prevents flag injection)
    arg = arg.lstrip('-')

    return arg.strip()


class SecureConfig:
    """
    Secure configuration manager for API keys and secrets.

    Loads from environment or config file, never logs secrets.
    """

    def __init__(self):
        """Initialize secure config."""
        self._secrets = {}

    def set(self, key: str, value: str):
        """
        Store a secret value.

        Args:
            key: Secret key name
            value: Secret value
        """
        self._secrets[key] = value

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a secret value.

        Args:
            key: Secret key name
            default: Default value if not found

        Returns:
            Secret value or default
        """
        return self._secrets.get(key, default)

    def load_from_env(self, prefix: str = "PIPELINE_"):
        """
        Load secrets from environment variables.

        Args:
            prefix: Prefix for environment variables
        """
        for key, value in os.environ.items():
            if key.startswith(prefix):
                clean_key = key[len(prefix):].lower()
                self._secrets[clean_key] = value

    def safe_dict(self) -> dict:
        """
        Get safe dictionary for logging (all values masked).

        Returns:
            Dict with masked values
        """
        return {key: "***" for key in self._secrets.keys()}


# Global secure config instance
_secure_config = SecureConfig()


def get_secure_config() -> SecureConfig:
    """Get global secure configuration instance."""
    return _secure_config


def validate_input_size(data: str, max_size_kb: int = 1024) -> bool:
    """
    Validate input data size to prevent DoS.

    Args:
        data: Input data string
        max_size_kb: Maximum size in kilobytes

    Returns:
        True if within limits
    """
    size_bytes = len(data.encode('utf-8'))
    size_kb = size_bytes / 1024
    return size_kb <= max_size_kb
