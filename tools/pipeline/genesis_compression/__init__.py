"""
Genesis Compression Module.

Provides compression algorithms compatible with Sega Genesis/Mega Drive hardware,
including pure Python implementations and optional external tool wrappers.

Supported Formats:
    - Kosinski: Sega's original LZSS variant (Sonic 1/2/3/K)
    - LZSS: Generic sliding window compression
    - RLE: Simple run-length encoding for highly repetitive data

Usage:
    >>> from pipeline.genesis_compression import GenesisCompressor, CompressionFormat
    >>> compressor = GenesisCompressor()
    >>> result = compressor.compress(tile_data, format=CompressionFormat.KOSINSKI)
    >>> print(f"Compressed: {result.input_size} -> {result.output_size} bytes ({result.ratio:.1%})")
"""

from .genesis_compress import (
    CompressionFormat,
    CompressionResult,
    GenesisCompressor,
    KosinskiCompressor,
    LZSSCompressor,
    RLECompressor,
    compress_kosinski,
    decompress_kosinski,
    compress_lzss,
    decompress_lzss,
    compress_rle,
    decompress_rle,
    auto_select_format,
)

__all__ = [
    'CompressionFormat',
    'CompressionResult',
    'GenesisCompressor',
    'KosinskiCompressor',
    'LZSSCompressor',
    'RLECompressor',
    'compress_kosinski',
    'decompress_kosinski',
    'compress_lzss',
    'decompress_lzss',
    'compress_rle',
    'decompress_rle',
    'auto_select_format',
]
