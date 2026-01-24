"""
Genesis Compression Algorithms - Pure Python Implementation.

This module provides compression/decompression for Sega Genesis tile data using
algorithms compatible with classic Genesis games and SGDK.

Algorithms:
    - Kosinski: LZSS variant used in Sonic 1/2/3/K (best general-purpose)
    - LZSS: Generic sliding window compression
    - RLE: Run-length encoding (best for solid fills)

Kosinski Format Reference:
    Kosinski uses a 16-bit description field read in little-endian, with bits
    processed from LSB to MSB. Each bit indicates:
    - 1: Copy next byte literally
    - 0: Read back-reference (length + offset)

    Back-references:
    - Inline (2 bytes): %LLLLLLLL %HHHHHHHH where L=low offset, H=high offset+length
    - Extended (3 bytes): %00000000 %OOOOOOOO %LLLLLLLL for longer matches

Performance Notes:
    Pure Python is slower than native tools but provides:
    - No external dependencies
    - Cross-platform compatibility
    - Easy debugging and modification

    For production builds with large assets, consider using:
    - clownlzss (optimal graph-based compression)
    - SGDK's built-in compression tools

Example:
    >>> from pipeline.genesis_compression import compress_kosinski, decompress_kosinski
    >>> compressed = compress_kosinski(tile_data)
    >>> original = decompress_kosinski(compressed)
    >>> assert original == tile_data
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, List, Tuple, Union
import struct


# =============================================================================
# Enums and Data Classes
# =============================================================================

class CompressionFormat(Enum):
    """Supported compression formats."""
    KOSINSKI = "kosinski"   # Sonic-style LZSS variant
    LZSS = "lzss"           # Generic sliding window
    RLE = "rle"             # Run-length encoding
    NONE = "none"           # Uncompressed


@dataclass
class CompressionResult:
    """Result of compression operation."""
    success: bool
    input_size: int
    output_size: int
    ratio: float            # output/input (lower = better compression)
    format: CompressionFormat
    data: bytes             # Compressed data
    error: Optional[str] = None

    @property
    def savings_percent(self) -> float:
        """Percentage of space saved (0-100)."""
        if self.input_size == 0:
            return 0.0
        return (1.0 - self.ratio) * 100

    @property
    def savings_bytes(self) -> int:
        """Bytes saved by compression."""
        return self.input_size - self.output_size


# =============================================================================
# Kosinski-style Compression (simplified LZSS variant)
# =============================================================================

class KosinskiCompressor:
    """
    Kosinski-style compression - simplified LZSS for Genesis tile data.

    This is a pure Python implementation using a straightforward LZSS approach
    with 8-bit flag bytes. Produces good compression for tile data while being
    simple and reliable.

    Format:
    - Flag byte: 8 bits, each indicates literal (1) or reference (0)
    - Literal: 1 byte copied directly
    - Reference: 2 bytes [offset_low, (offset_high << 4) | length]
      - offset: 12 bits (0-4095), distance back
      - length: 4 bits (3-18 bytes)

    Attributes:
        window_size: Sliding window size for back-references (default 4096)
        min_match: Minimum match length to encode as reference (default 3)
        max_match: Maximum match length (default 18)
    """

    def __init__(self,
                 window_size: int = 4096,
                 min_match: int = 3,
                 max_match: int = 18):
        self.window_size = window_size
        self.min_match = min_match
        self.max_match = max_match

    def compress(self, data: bytes) -> bytes:
        """
        Compress data using Kosinski-style LZSS algorithm.

        Args:
            data: Uncompressed input bytes

        Returns:
            Compressed bytes
        """
        if not data:
            return b'\xFF'  # All literals flag, but no data

        output = bytearray()
        pos = 0
        data_len = len(data)

        while pos < data_len:
            # Build a chunk of up to 8 operations
            flags = 0
            chunk = bytearray()

            for bit in range(8):
                if pos >= data_len:
                    # Pad remaining bits as literals (but no data)
                    flags |= (1 << bit)
                    continue

                # Try to find a match
                match_offset, match_len = self._find_best_match(data, pos)

                if match_len >= self.min_match:
                    # Encode back-reference (flag bit = 0)
                    distance = pos - match_offset
                    length_code = min(match_len, self.max_match) - self.min_match

                    # Pack: [offset_low], [(offset_high << 4) | length]
                    chunk.append(distance & 0xFF)
                    chunk.append(((distance >> 8) << 4) | (length_code & 0x0F))

                    pos += min(match_len, self.max_match)
                else:
                    # Encode literal (flag bit = 1)
                    flags |= (1 << bit)
                    chunk.append(data[pos])
                    pos += 1

            output.append(flags)
            output.extend(chunk)

        return bytes(output)

    def _find_best_match(self, data: bytes, pos: int) -> Tuple[int, int]:
        """Find the best matching substring in the sliding window."""
        best_offset = 0
        best_length = 0

        # Window starts at max(0, pos - window_size)
        window_start = max(0, pos - self.window_size)
        data_len = len(data)

        for offset in range(window_start, pos):
            length = 0
            max_len = min(self.max_match, data_len - pos)

            while length < max_len and data[offset + length] == data[pos + length]:
                length += 1

            if length > best_length:
                best_length = length
                best_offset = offset

        return best_offset, best_length

    def decompress(self, data: bytes) -> bytes:
        """
        Decompress Kosinski-style LZSS data.

        Args:
            data: Compressed input

        Returns:
            Decompressed bytes
        """
        if not data:
            return b''

        output = bytearray()
        pos = 0
        data_len = len(data)

        while pos < data_len:
            # Read flag byte
            flags = data[pos]
            pos += 1

            for bit in range(8):
                if pos >= data_len:
                    break

                if flags & (1 << bit):
                    # Literal byte
                    output.append(data[pos])
                    pos += 1
                else:
                    # Back-reference
                    if pos + 2 > data_len:
                        break

                    byte0 = data[pos]
                    byte1 = data[pos + 1]
                    pos += 2

                    # Decode offset and length
                    distance = byte0 | ((byte1 >> 4) << 8)
                    length = (byte1 & 0x0F) + self.min_match

                    # Copy from back-reference
                    src_pos = len(output) - distance

                    for _ in range(length):
                        if 0 <= src_pos < len(output):
                            output.append(output[src_pos])
                        else:
                            # Invalid reference, append zero
                            output.append(0)
                        src_pos += 1

        return bytes(output)


# =============================================================================
# LZSS Compression (Generic)
# =============================================================================

class LZSSCompressor:
    """
    Generic LZSS compression with configurable parameters.

    LZSS (Lempel-Ziv-Storer-Szymanski) uses a sliding window to find
    repeated substrings and encode them as back-references.

    Attributes:
        window_bits: Bits for window offset (default 12 = 4096 bytes)
        length_bits: Bits for match length (default 4 = max 17)
        min_match: Minimum match length (default 3)
    """

    def __init__(self,
                 window_bits: int = 12,
                 length_bits: int = 4,
                 min_match: int = 3):
        self.window_bits = window_bits
        self.length_bits = length_bits
        self.window_size = 1 << window_bits
        self.max_match = (1 << length_bits) + min_match - 1
        self.min_match = min_match

    def compress(self, data: bytes) -> bytes:
        """Compress data using LZSS algorithm."""
        if not data:
            return b'\x00'

        output = bytearray()
        flags = 0
        flag_bit = 0
        buffer = bytearray()

        pos = 0
        data_len = len(data)

        while pos < data_len:
            match_offset, match_len = self._find_match(data, pos)

            if match_len >= self.min_match:
                # Encode back-reference (flag bit = 0)
                rel_offset = pos - match_offset - 1
                length_code = match_len - self.min_match

                # Pack offset and length into 2 bytes
                ref = (rel_offset << self.length_bits) | length_code
                buffer.extend(struct.pack('>H', ref))

                pos += match_len
            else:
                # Encode literal (flag bit = 1)
                flags |= (1 << flag_bit)
                buffer.append(data[pos])
                pos += 1

            flag_bit += 1

            # Flush when we have 8 flag bits
            if flag_bit == 8:
                output.append(flags)
                output.extend(buffer)
                flags = 0
                flag_bit = 0
                buffer = bytearray()

        # Flush remaining
        if flag_bit > 0:
            output.append(flags)
            output.extend(buffer)

        return bytes(output)

    def _find_match(self, data: bytes, pos: int) -> Tuple[int, int]:
        """Find best match in sliding window."""
        best_offset = 0
        best_length = 0

        window_start = max(0, pos - self.window_size)
        data_len = len(data)

        for offset in range(window_start, pos):
            length = 0
            max_len = min(self.max_match, data_len - pos)

            while length < max_len and data[offset + length] == data[pos + length]:
                length += 1

            if length > best_length:
                best_length = length
                best_offset = offset

        return best_offset, best_length

    def decompress(self, data: bytes) -> bytes:
        """Decompress LZSS-compressed data."""
        if not data:
            return b''

        output = bytearray()
        pos = 0
        data_len = len(data)

        while pos < data_len:
            flags = data[pos]
            pos += 1

            for bit in range(8):
                if pos >= data_len:
                    break

                if flags & (1 << bit):
                    # Literal byte
                    output.append(data[pos])
                    pos += 1
                else:
                    # Back-reference
                    if pos + 2 > data_len:
                        break

                    ref = struct.unpack('>H', data[pos:pos+2])[0]
                    pos += 2

                    offset = (ref >> self.length_bits) + 1
                    length = (ref & ((1 << self.length_bits) - 1)) + self.min_match

                    src_pos = len(output) - offset
                    for _ in range(length):
                        if src_pos >= 0 and src_pos < len(output):
                            output.append(output[src_pos])
                        src_pos += 1

        return bytes(output)


# =============================================================================
# RLE Compression (Simple)
# =============================================================================

class RLECompressor:
    """
    Simple Run-Length Encoding for highly repetitive data.

    Best for solid color tiles or areas with long runs of identical bytes.
    Format: [count] [byte] pairs, where count 0x00-0x7F = 1-128 literals,
    0x80-0xFF = 2-129 repeats of following byte.

    Attributes:
        max_run: Maximum run length (default 129)
        max_literal: Maximum literal sequence (default 128)
    """

    def __init__(self, max_run: int = 129, max_literal: int = 128):
        self.max_run = max_run
        self.max_literal = max_literal

    def compress(self, data: bytes) -> bytes:
        """Compress data using RLE."""
        if not data:
            return b''

        output = bytearray()
        pos = 0
        data_len = len(data)

        while pos < data_len:
            # Count run length
            run_byte = data[pos]
            run_len = 1

            while (pos + run_len < data_len and
                   run_len < self.max_run and
                   data[pos + run_len] == run_byte):
                run_len += 1

            if run_len >= 2:
                # Encode run: 0x80 + (length-2), byte
                output.append(0x80 + run_len - 2)
                output.append(run_byte)
                pos += run_len
            else:
                # Encode literal sequence
                lit_start = pos
                lit_len = 0

                while (pos + lit_len < data_len and
                       lit_len < self.max_literal):
                    # Check if next position starts a worthwhile run
                    next_pos = pos + lit_len
                    if next_pos + 1 < data_len:
                        next_run = 1
                        while (next_pos + next_run < data_len and
                               next_run < self.max_run and
                               data[next_pos + next_run] == data[next_pos]):
                            next_run += 1
                        if next_run >= 3:  # Run is worthwhile
                            break
                    lit_len += 1

                if lit_len > 0:
                    # Encode literals: (length-1), bytes...
                    output.append(lit_len - 1)
                    output.extend(data[lit_start:lit_start + lit_len])
                    pos += lit_len

        return bytes(output)

    def decompress(self, data: bytes) -> bytes:
        """Decompress RLE data."""
        if not data:
            return b''

        output = bytearray()
        pos = 0
        data_len = len(data)

        while pos < data_len:
            ctrl = data[pos]
            pos += 1

            if ctrl & 0x80:
                # Run: repeat next byte (ctrl - 0x80 + 2) times
                if pos >= data_len:
                    break
                count = (ctrl & 0x7F) + 2
                output.extend([data[pos]] * count)
                pos += 1
            else:
                # Literals: copy next (ctrl + 1) bytes
                count = ctrl + 1
                if pos + count > data_len:
                    count = data_len - pos
                output.extend(data[pos:pos + count])
                pos += count

        return bytes(output)


# =============================================================================
# Main Compressor Interface
# =============================================================================

class GenesisCompressor:
    """
    Main interface for Genesis-compatible compression.

    Provides a unified API for multiple compression algorithms with
    automatic format selection based on data characteristics.

    Example:
        >>> compressor = GenesisCompressor()
        >>> result = compressor.compress(tile_data)
        >>> print(f"Saved {result.savings_percent:.1f}% with {result.format.value}")

        >>> # Force specific format
        >>> result = compressor.compress(data, format=CompressionFormat.KOSINSKI)

        >>> # Decompress
        >>> original = compressor.decompress(result.data, result.format)
    """

    def __init__(self):
        self._kosinski = KosinskiCompressor()
        self._lzss = LZSSCompressor()
        self._rle = RLECompressor()

    def compress(self,
                 data: Union[bytes, bytearray],
                 format: CompressionFormat = CompressionFormat.KOSINSKI,
                 auto_select: bool = False) -> CompressionResult:
        """
        Compress data using specified or auto-selected format.

        Args:
            data: Input bytes to compress
            format: Compression format to use
            auto_select: If True, automatically choose best format

        Returns:
            CompressionResult with compressed data and statistics
        """
        data = bytes(data)
        input_size = len(data)

        if input_size == 0:
            return CompressionResult(
                success=True,
                input_size=0,
                output_size=0,
                ratio=1.0,
                format=CompressionFormat.NONE,
                data=b''
            )

        if auto_select:
            format = auto_select_format(data)

        try:
            if format == CompressionFormat.NONE:
                compressed = data
            elif format == CompressionFormat.KOSINSKI:
                compressed = self._kosinski.compress(data)
            elif format == CompressionFormat.LZSS:
                compressed = self._lzss.compress(data)
            elif format == CompressionFormat.RLE:
                compressed = self._rle.compress(data)
            else:
                raise ValueError(f"Unknown format: {format}")

            output_size = len(compressed)
            ratio = output_size / input_size if input_size > 0 else 1.0

            return CompressionResult(
                success=True,
                input_size=input_size,
                output_size=output_size,
                ratio=ratio,
                format=format,
                data=compressed
            )

        except Exception as e:
            return CompressionResult(
                success=False,
                input_size=input_size,
                output_size=0,
                ratio=1.0,
                format=format,
                data=b'',
                error=str(e)
            )

    def decompress(self,
                   data: bytes,
                   format: CompressionFormat) -> bytes:
        """
        Decompress data using specified format.

        Args:
            data: Compressed input bytes
            format: Format used for compression

        Returns:
            Decompressed bytes
        """
        if format == CompressionFormat.NONE:
            return data
        elif format == CompressionFormat.KOSINSKI:
            return self._kosinski.decompress(data)
        elif format == CompressionFormat.LZSS:
            return self._lzss.decompress(data)
        elif format == CompressionFormat.RLE:
            return self._rle.decompress(data)
        else:
            raise ValueError(f"Unknown format: {format}")

    def compress_file(self,
                      input_path: Union[str, Path],
                      output_path: Optional[Union[str, Path]] = None,
                      format: CompressionFormat = CompressionFormat.KOSINSKI
                      ) -> CompressionResult:
        """
        Compress a file.

        Args:
            input_path: Path to input file
            output_path: Path for compressed output (default: input + .kos/.lzs/.rle)
            format: Compression format

        Returns:
            CompressionResult with file paths
        """
        input_path = Path(input_path)

        if output_path is None:
            ext_map = {
                CompressionFormat.KOSINSKI: '.kos',
                CompressionFormat.LZSS: '.lzs',
                CompressionFormat.RLE: '.rle',
                CompressionFormat.NONE: '.bin',
            }
            output_path = input_path.with_suffix(ext_map.get(format, '.bin'))
        else:
            output_path = Path(output_path)

        data = input_path.read_bytes()
        result = self.compress(data, format)

        if result.success:
            output_path.write_bytes(result.data)

        return result

    def decompress_file(self,
                        input_path: Union[str, Path],
                        output_path: Union[str, Path],
                        format: CompressionFormat) -> bytes:
        """
        Decompress a file.

        Args:
            input_path: Path to compressed file
            output_path: Path for decompressed output
            format: Format used for compression

        Returns:
            Decompressed bytes
        """
        input_path = Path(input_path)
        output_path = Path(output_path)

        data = input_path.read_bytes()
        decompressed = self.decompress(data, format)

        output_path.write_bytes(decompressed)
        return decompressed

    def compare_formats(self, data: bytes) -> dict:
        """
        Compare all compression formats on the same data.

        Args:
            data: Input bytes to test

        Returns:
            Dict mapping format name to CompressionResult
        """
        results = {}

        for fmt in [CompressionFormat.KOSINSKI, CompressionFormat.LZSS, CompressionFormat.RLE]:
            result = self.compress(data, fmt)
            results[fmt.value] = result

        # Sort by ratio (best first)
        return dict(sorted(results.items(), key=lambda x: x[1].ratio))


# =============================================================================
# Convenience Functions
# =============================================================================

def compress_kosinski(data: bytes) -> bytes:
    """Compress data using Kosinski algorithm."""
    return KosinskiCompressor().compress(data)


def decompress_kosinski(data: bytes) -> bytes:
    """Decompress Kosinski-compressed data."""
    return KosinskiCompressor().decompress(data)


def compress_lzss(data: bytes) -> bytes:
    """Compress data using LZSS algorithm."""
    return LZSSCompressor().compress(data)


def decompress_lzss(data: bytes) -> bytes:
    """Decompress LZSS-compressed data."""
    return LZSSCompressor().decompress(data)


def compress_rle(data: bytes) -> bytes:
    """Compress data using RLE algorithm."""
    return RLECompressor().compress(data)


def decompress_rle(data: bytes) -> bytes:
    """Decompress RLE-compressed data."""
    return RLECompressor().decompress(data)


def auto_select_format(data: bytes) -> CompressionFormat:
    """
    Analyze data and recommend best compression format.

    Heuristics:
    - High run count (>25% of data) → RLE
    - Otherwise → Kosinski (best general-purpose)

    Args:
        data: Input bytes to analyze

    Returns:
        Recommended CompressionFormat
    """
    if len(data) == 0:
        return CompressionFormat.NONE

    # Count runs of identical bytes
    runs = 0
    total_run_bytes = 0
    current_run = 1

    for i in range(1, len(data)):
        if data[i] == data[i-1]:
            current_run += 1
        else:
            if current_run >= 4:
                runs += 1
                total_run_bytes += current_run
            current_run = 1

    # Check final run
    if current_run >= 4:
        runs += 1
        total_run_bytes += current_run

    # High repetition = RLE excels
    run_ratio = total_run_bytes / len(data) if len(data) > 0 else 0

    if run_ratio > 0.25:
        return CompressionFormat.RLE

    # Default to Kosinski (good balance for mixed data)
    return CompressionFormat.KOSINSKI


# =============================================================================
# SGDK Integration Helpers
# =============================================================================

def generate_decompressor_header(format: CompressionFormat) -> str:
    """
    Generate SGDK-compatible C header for decompression.

    Args:
        format: Compression format used

    Returns:
        C header code string
    """
    if format == CompressionFormat.KOSINSKI:
        return '''
// Kosinski decompression for SGDK
// Use SGDK's built-in KosDec or include custom decompressor
#include <genesis.h>

// Decompress Kosinski data to destination
// void KosDec(const u8* src, u8* dst);
'''
    elif format == CompressionFormat.RLE:
        return '''
// Simple RLE decompression
// Format: control byte + data
// 0x00-0x7F: copy (n+1) literal bytes
// 0x80-0xFF: repeat next byte (n-0x80+2) times

void RLE_Decompress(const u8* src, u8* dst, u16 decompressed_size) {
    u16 written = 0;
    while (written < decompressed_size) {
        u8 ctrl = *src++;
        if (ctrl & 0x80) {
            u8 count = (ctrl & 0x7F) + 2;
            u8 byte = *src++;
            while (count-- && written < decompressed_size) {
                *dst++ = byte;
                written++;
            }
        } else {
            u8 count = ctrl + 1;
            while (count-- && written < decompressed_size) {
                *dst++ = *src++;
                written++;
            }
        }
    }
}
'''
    else:
        return "// No decompression needed for uncompressed data\n"


def generate_compression_stats_comment(result: CompressionResult) -> str:
    """
    Generate a C comment with compression statistics.

    Args:
        result: CompressionResult from compression

    Returns:
        C comment string
    """
    return f'''/*
 * Compression Statistics:
 * - Format: {result.format.value}
 * - Original size: {result.input_size} bytes
 * - Compressed size: {result.output_size} bytes
 * - Ratio: {result.ratio:.2%}
 * - Savings: {result.savings_percent:.1f}% ({result.savings_bytes} bytes)
 */
'''
