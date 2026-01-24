"""
Platform Registry - Central registry for all platform configurations.

Provides a unified interface to access platform configs by name or tier.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .nes_config import NES_CONFIG, NES_ASSET_CONFIG
from .genesis_config import GENESIS_CONFIG, GENESIS_ASSET_CONFIG
from .snes_config import SNES_CONFIG, SNES_ASSET_CONFIG


# =============================================================================
# Registry
# =============================================================================

@dataclass
class PlatformEntry:
    """Entry in the platform registry."""
    name: str
    aliases: List[str]
    tier: str
    tier_id: int
    hardware_config: Any
    asset_config: Dict


PLATFORM_REGISTRY: Dict[str, PlatformEntry] = {
    'nes': PlatformEntry(
        name='NES',
        aliases=['famicom', 'fc', 'nintendo'],
        tier='MINIMAL',
        tier_id=0,
        hardware_config=NES_CONFIG,
        asset_config=NES_ASSET_CONFIG,
    ),
    'genesis': PlatformEntry(
        name='Genesis',
        aliases=['megadrive', 'md', 'sega_genesis'],
        tier='STANDARD',
        tier_id=2,
        hardware_config=GENESIS_CONFIG,
        asset_config=GENESIS_ASSET_CONFIG,
    ),
    'snes': PlatformEntry(
        name='SNES',
        aliases=['super_nintendo', 'sfc', 'super_famicom'],
        tier='STANDARD',
        tier_id=2,
        hardware_config=SNES_CONFIG,
        asset_config=SNES_ASSET_CONFIG,
    ),
}


# Build alias lookup
_ALIAS_MAP: Dict[str, str] = {}
for platform_id, entry in PLATFORM_REGISTRY.items():
    _ALIAS_MAP[platform_id] = platform_id
    _ALIAS_MAP[entry.name.lower()] = platform_id
    for alias in entry.aliases:
        _ALIAS_MAP[alias.lower()] = platform_id


# =============================================================================
# Public API
# =============================================================================

def get_platform_config(platform: str) -> Optional[Any]:
    """
    Get hardware configuration for a platform.

    Args:
        platform: Platform name or alias (case-insensitive)

    Returns:
        Hardware config dataclass or None if not found
    """
    platform_id = _ALIAS_MAP.get(platform.lower())
    if platform_id and platform_id in PLATFORM_REGISTRY:
        return PLATFORM_REGISTRY[platform_id].hardware_config
    return None


def get_asset_config(platform: str) -> Optional[Dict]:
    """
    Get asset generation configuration for a platform.

    Args:
        platform: Platform name or alias (case-insensitive)

    Returns:
        Asset config dict or None if not found
    """
    platform_id = _ALIAS_MAP.get(platform.lower())
    if platform_id and platform_id in PLATFORM_REGISTRY:
        return PLATFORM_REGISTRY[platform_id].asset_config
    return None


def list_platforms() -> List[Dict[str, str]]:
    """
    List all registered platforms.

    Returns:
        List of dicts with platform info
    """
    return [
        {
            'id': platform_id,
            'name': entry.name,
            'tier': entry.tier,
            'aliases': entry.aliases,
        }
        for platform_id, entry in PLATFORM_REGISTRY.items()
    ]


def get_platforms_by_tier(tier: str) -> List[str]:
    """
    Get all platforms in a given tier.

    Args:
        tier: Tier name (MINIMAL, MINIMAL_PLUS, STANDARD, etc.)

    Returns:
        List of platform IDs
    """
    return [
        platform_id
        for platform_id, entry in PLATFORM_REGISTRY.items()
        if entry.tier == tier
    ]


def resolve_platform(name: str) -> str:
    """
    Resolve a platform name/alias to canonical ID.

    Args:
        name: Platform name or alias

    Returns:
        Canonical platform ID

    Raises:
        ValueError if platform not found
    """
    platform_id = _ALIAS_MAP.get(name.lower())
    if platform_id:
        return platform_id
    raise ValueError(f"Unknown platform: {name}. Available: {', '.join(PLATFORM_REGISTRY.keys())}")


def get_generation_style(platform: str) -> str:
    """
    Get the prompt style string for a platform.

    Args:
        platform: Platform name or alias

    Returns:
        Style string for AI generation prompts
    """
    config = get_asset_config(platform)
    if config:
        return config.get('prompt_style', '')
    return ''


def get_tile_constraints(platform: str) -> Dict[str, int]:
    """
    Get tile-related constraints for a platform.

    Args:
        platform: Platform name or alias

    Returns:
        Dict with tile constraints
    """
    config = get_asset_config(platform)
    if not config:
        return {}

    return {
        'tile_width': config.get('tile_size', (8, 8))[0],
        'tile_height': config.get('tile_size', (8, 8))[1],
        'max_tiles': config.get('max_tiles_per_bank', config.get('max_tiles', 256)),
        'bits_per_pixel': config.get('bits_per_pixel', 2),
        'colors_per_palette': config.get('colors_per_palette', 4),
    }


def get_sprite_constraints(platform: str) -> Dict[str, Any]:
    """
    Get sprite-related constraints for a platform.

    Args:
        platform: Platform name or alias

    Returns:
        Dict with sprite constraints
    """
    config = get_asset_config(platform)
    if not config:
        return {}

    return {
        'max_sprites': config.get('max_sprites', 64),
        'sprite_sizes': config.get('sprite_sizes', [(8, 8)]),
        'max_metasprite_tiles': config.get('max_metasprite_tiles', 16),
        'max_animation_frames': config.get('max_animation_frames', 4),
        'suggested_frame_counts': config.get('suggested_frame_counts', {}),
    }


def get_parallax_constraints(platform: str) -> Dict[str, Any]:
    """
    Get parallax-related constraints for a platform.

    Args:
        platform: Platform name or alias

    Returns:
        Dict with parallax constraints
    """
    config = get_asset_config(platform)
    if not config:
        return {}

    return {
        'max_layers': config.get('max_parallax_layers', 2),
        'method': config.get('parallax_method', config.get('parallax_methods', ['simple'])),
    }


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    """Command-line interface for platform info."""
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description='Query platform configurations'
    )
    parser.add_argument('platform', nargs='?', help='Platform to query')
    parser.add_argument('--list', action='store_true', help='List all platforms')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--tiles', action='store_true', help='Show tile constraints')
    parser.add_argument('--sprites', action='store_true', help='Show sprite constraints')
    parser.add_argument('--parallax', action='store_true', help='Show parallax constraints')

    args = parser.parse_args()

    if args.list:
        platforms = list_platforms()
        if args.json:
            print(json.dumps(platforms, indent=2))
        else:
            print("Available platforms:")
            for p in platforms:
                print(f"  {p['id']:10} ({p['name']:12}) - Tier: {p['tier']}")
                if p['aliases']:
                    print(f"             Aliases: {', '.join(p['aliases'])}")
        return

    if not args.platform:
        parser.print_help()
        return

    try:
        platform_id = resolve_platform(args.platform)
    except ValueError as e:
        print(f"Error: {e}")
        return

    entry = PLATFORM_REGISTRY[platform_id]

    if args.tiles:
        constraints = get_tile_constraints(platform_id)
        if args.json:
            print(json.dumps(constraints, indent=2))
        else:
            print(f"Tile constraints for {entry.name}:")
            for k, v in constraints.items():
                print(f"  {k}: {v}")
        return

    if args.sprites:
        constraints = get_sprite_constraints(platform_id)
        if args.json:
            print(json.dumps(constraints, indent=2))
        else:
            print(f"Sprite constraints for {entry.name}:")
            for k, v in constraints.items():
                print(f"  {k}: {v}")
        return

    if args.parallax:
        constraints = get_parallax_constraints(platform_id)
        if args.json:
            print(json.dumps(constraints, indent=2))
        else:
            print(f"Parallax constraints for {entry.name}:")
            for k, v in constraints.items():
                print(f"  {k}: {v}")
        return

    # Default: show all info
    if args.json:
        print(json.dumps(entry.asset_config, indent=2))
    else:
        print(f"Platform: {entry.name}")
        print(f"Tier: {entry.tier} (ID: {entry.tier_id})")
        print(f"Aliases: {', '.join(entry.aliases)}")
        print()
        print("Asset configuration:")
        for k, v in entry.asset_config.items():
            if not isinstance(v, dict):
                print(f"  {k}: {v}")


if __name__ == '__main__':
    main()
