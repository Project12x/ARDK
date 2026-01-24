"""
API key configuration for AI services.

Uses python-dotenv to load keys from .env file.
Environment variables take priority over .env values.

Setup:
    1. Copy .env.example to .env
    2. Add your API keys to .env
    3. Install dotenv: pip install python-dotenv

Usage:
    from configs.api_keys import get_api_key
    key = get_api_key('pollinations')
"""

import os
from pathlib import Path

# Try to load .env file
try:
    from dotenv import load_dotenv
    # Look for .env in project root (two levels up from this file)
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # python-dotenv not installed, rely on environment variables only
    pass

# API Keys - loaded from environment variables (set via .env or system)
# No hardcoded fallbacks - keys must be configured by user
_API_KEYS = {
    'pollinations': os.environ.get('POLLINATIONS_API_KEY', ''),
    'bfl': os.environ.get('BFL_API_KEY', ''),
    'pixellab': os.environ.get('PIXELLAB_API_KEY', ''),
}


def get_api_key(service: str) -> str:
    """
    Get API key for a service.

    Args:
        service: Service name ('pollinations', 'bfl', 'pixellab')

    Returns:
        API key string, or empty string if not configured
    """
    return _API_KEYS.get(service.lower(), '')


def set_api_key(service: str, key: str):
    """
    Set API key for a service (runtime only, not persisted).

    Args:
        service: Service name
        key: API key value
    """
    _API_KEYS[service.lower()] = key


# Convenience exports
POLLINATIONS_API_KEY = get_api_key('pollinations')
BFL_API_KEY = get_api_key('bfl')
PIXELLAB_API_KEY = get_api_key('pixellab')

