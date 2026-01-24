"""
Audio Pipeline Extensions for Genesis/SGDK.

This subpackage provides VGM/XGM tools for Genesis music workflow:
- VGM file validation and analysis
- XGM conversion via xgmtool wrapper
- WOPN instrument bank parsing

Workflow:
    1. Compose in Furnace Tracker (or other Genesis-compatible tracker)
    2. Export as VGM
    3. Validate with validate_vgm()
    4. Convert to XGM with XGMToolWrapper
    5. Include in SGDK project via .res file

Example:
    >>> from pipeline.vgm import XGMToolWrapper, validate_vgm
    >>> errors = validate_vgm("music.vgm")
    >>> if not errors:
    ...     wrapper = XGMToolWrapper()
    ...     result = wrapper.convert("music.vgm", "music.xgm")
"""

from .vgm_tools import (
    # VGM Analysis
    VGMHeader,
    VGMInfo,
    parse_vgm_header,
    validate_vgm,
    get_vgm_info,

    # XGM Conversion
    XGMConversionResult,
    XGMToolWrapper,

    # WOPN Banks
    WOPNOperator,
    WOPNPatch,
    WOPNBank,
    WOPNParser,

    # Utilities
    detect_vgm_chips,
    estimate_xgm_size,
)

__all__ = [
    # VGM
    'VGMHeader',
    'VGMInfo',
    'parse_vgm_header',
    'validate_vgm',
    'get_vgm_info',

    # XGM
    'XGMConversionResult',
    'XGMToolWrapper',

    # WOPN
    'WOPNOperator',
    'WOPNPatch',
    'WOPNBank',
    'WOPNParser',

    # Utils
    'detect_vgm_chips',
    'estimate_xgm_size',
]
