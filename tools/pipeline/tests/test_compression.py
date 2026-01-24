"""
Tests for compression/genesis_compress.py - Phase 2.8

Tests Genesis-compatible compression algorithms including:
- Kosinski compression/decompression
- LZSS compression/decompression
- RLE compression/decompression
- Auto format selection
- Round-trip integrity
"""

import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.genesis_compression import (
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


class TestCompressionFormat:
    """Tests for CompressionFormat enum."""

    def test_format_values(self):
        """All format values should be strings."""
        assert CompressionFormat.KOSINSKI.value == "kosinski"
        assert CompressionFormat.LZSS.value == "lzss"
        assert CompressionFormat.RLE.value == "rle"
        assert CompressionFormat.NONE.value == "none"


class TestCompressionResult:
    """Tests for CompressionResult dataclass."""

    def test_savings_percent(self):
        """savings_percent should calculate correctly."""
        result = CompressionResult(
            success=True,
            input_size=100,
            output_size=60,
            ratio=0.6,
            format=CompressionFormat.KOSINSKI,
            data=b'x' * 60
        )
        assert result.savings_percent == pytest.approx(40.0)

    def test_savings_bytes(self):
        """savings_bytes should be input - output."""
        result = CompressionResult(
            success=True,
            input_size=100,
            output_size=60,
            ratio=0.6,
            format=CompressionFormat.KOSINSKI,
            data=b'x' * 60
        )
        assert result.savings_bytes == 40

    def test_zero_input(self):
        """savings_percent should handle zero input."""
        result = CompressionResult(
            success=True,
            input_size=0,
            output_size=0,
            ratio=1.0,
            format=CompressionFormat.NONE,
            data=b''
        )
        assert result.savings_percent == 0.0


class TestKosinskiCompressor:
    """Tests for Kosinski compression."""

    @pytest.fixture
    def compressor(self):
        return KosinskiCompressor()

    def test_compress_empty(self, compressor):
        """Empty input should produce valid output."""
        result = compressor.compress(b'')
        assert len(result) > 0
        # Should decompress back to empty
        decompressed = compressor.decompress(result)
        assert decompressed == b''

    def test_compress_single_byte(self, compressor):
        """Single byte should compress and decompress."""
        data = b'\x42'
        compressed = compressor.compress(data)
        decompressed = compressor.decompress(compressed)
        assert decompressed == data

    def test_compress_repeated_bytes(self, compressor):
        """Repeated bytes should compress well."""
        data = b'\xFF' * 100
        compressed = compressor.compress(data)
        # Should achieve some compression
        assert len(compressed) < len(data)
        # Round-trip
        decompressed = compressor.decompress(compressed)
        assert decompressed == data

    def test_compress_sequential(self, compressor):
        """Sequential data should round-trip."""
        data = bytes(range(256))
        compressed = compressor.compress(data)
        decompressed = compressor.decompress(compressed)
        assert decompressed == data

    def test_compress_tile_like_data(self, compressor):
        """Tile-like patterns should compress."""
        # Simulate 8x8 4bpp tile (32 bytes)
        tile = bytes([
            0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77,
            0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77,
            0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77,
            0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77,
        ])
        compressed = compressor.compress(tile)
        decompressed = compressor.decompress(compressed)
        assert decompressed == tile

    def test_roundtrip_random_data(self, compressor):
        """Random-ish data should round-trip correctly."""
        import random
        random.seed(42)
        data = bytes(random.randint(0, 255) for _ in range(1000))
        compressed = compressor.compress(data)
        decompressed = compressor.decompress(compressed)
        assert decompressed == data


class TestLZSSCompressor:
    """Tests for LZSS compression."""

    @pytest.fixture
    def compressor(self):
        return LZSSCompressor()

    def test_compress_empty(self, compressor):
        """Empty input should produce minimal output."""
        result = compressor.compress(b'')
        assert result == b'\x00'

    def test_compress_single_byte(self, compressor):
        """Single byte should compress and decompress."""
        data = b'\x42'
        compressed = compressor.compress(data)
        decompressed = compressor.decompress(compressed)
        assert decompressed == data

    def test_compress_repeated(self, compressor):
        """Repeated data should compress well."""
        data = b'ABCD' * 50
        compressed = compressor.compress(data)
        assert len(compressed) < len(data)
        decompressed = compressor.decompress(compressed)
        assert decompressed == data

    def test_roundtrip_binary(self, compressor):
        """Binary data should round-trip."""
        data = bytes(range(256)) * 2
        compressed = compressor.compress(data)
        decompressed = compressor.decompress(compressed)
        assert decompressed == data


class TestRLECompressor:
    """Tests for RLE compression."""

    @pytest.fixture
    def compressor(self):
        return RLECompressor()

    def test_compress_empty(self, compressor):
        """Empty input should produce empty output."""
        result = compressor.compress(b'')
        assert result == b''

    def test_compress_single_byte(self, compressor):
        """Single byte should compress as literal."""
        data = b'\x42'
        compressed = compressor.compress(data)
        decompressed = compressor.decompress(compressed)
        assert decompressed == data

    def test_compress_run(self, compressor):
        """Run of bytes should compress efficiently."""
        data = b'\xFF' * 50
        compressed = compressor.compress(data)
        # Should be much smaller
        assert len(compressed) < len(data) / 2
        decompressed = compressor.decompress(compressed)
        assert decompressed == data

    def test_compress_alternating(self, compressor):
        """Alternating bytes should still work."""
        data = b'\x00\xFF' * 50
        compressed = compressor.compress(data)
        decompressed = compressor.decompress(compressed)
        assert decompressed == data

    def test_solid_color_tile(self, compressor):
        """Solid color tile should compress very well."""
        # 32 bytes of same value (solid 4bpp tile)
        tile = b'\x00' * 32
        compressed = compressor.compress(tile)
        # Should be tiny
        assert len(compressed) <= 4
        decompressed = compressor.decompress(compressed)
        assert decompressed == tile


class TestGenesisCompressor:
    """Tests for main GenesisCompressor interface."""

    @pytest.fixture
    def compressor(self):
        return GenesisCompressor()

    def test_compress_kosinski(self, compressor):
        """Should compress with Kosinski format."""
        data = b'Test data for compression' * 10
        result = compressor.compress(data, CompressionFormat.KOSINSKI)

        assert result.success
        assert result.format == CompressionFormat.KOSINSKI
        assert result.input_size == len(data)
        assert result.output_size == len(result.data)

    def test_compress_lzss(self, compressor):
        """Should compress with LZSS format."""
        data = b'Test data for compression' * 10
        result = compressor.compress(data, CompressionFormat.LZSS)

        assert result.success
        assert result.format == CompressionFormat.LZSS

    def test_compress_rle(self, compressor):
        """Should compress with RLE format."""
        data = b'\xFF' * 100
        result = compressor.compress(data, CompressionFormat.RLE)

        assert result.success
        assert result.format == CompressionFormat.RLE
        assert result.ratio < 0.5  # Should compress well

    def test_compress_none(self, compressor):
        """NONE format should return data unchanged."""
        data = b'unchanged data'
        result = compressor.compress(data, CompressionFormat.NONE)

        assert result.success
        assert result.data == data
        assert result.ratio == 1.0

    def test_compress_empty(self, compressor):
        """Empty input should handle gracefully."""
        result = compressor.compress(b'')

        assert result.success
        assert result.input_size == 0
        assert result.format == CompressionFormat.NONE

    def test_decompress_roundtrip(self, compressor):
        """Compress then decompress should return original."""
        data = b'Hello, Genesis!' * 20

        for fmt in [CompressionFormat.KOSINSKI, CompressionFormat.LZSS, CompressionFormat.RLE]:
            result = compressor.compress(data, fmt)
            assert result.success, f"Failed to compress with {fmt}"

            decompressed = compressor.decompress(result.data, fmt)
            assert decompressed == data, f"Round-trip failed for {fmt}"

    def test_auto_select(self, compressor):
        """Auto-select should choose appropriate format."""
        # Highly repetitive data should prefer RLE
        repetitive = b'\x00' * 1000
        result = compressor.compress(repetitive, auto_select=True)
        assert result.success

        # Mixed data should work too
        mixed = bytes(range(256)) * 4
        result = compressor.compress(mixed, auto_select=True)
        assert result.success

    def test_compare_formats(self, compressor):
        """compare_formats should return results for all formats."""
        data = b'Test' * 100

        results = compressor.compare_formats(data)

        assert 'kosinski' in results
        assert 'lzss' in results
        assert 'rle' in results

        # All should succeed
        for name, result in results.items():
            assert result.success, f"{name} failed"


class TestAutoSelectFormat:
    """Tests for auto_select_format function."""

    def test_empty_data(self):
        """Empty data should return NONE."""
        assert auto_select_format(b'') == CompressionFormat.NONE

    def test_highly_repetitive(self):
        """Highly repetitive data should suggest RLE."""
        data = b'\x00' * 100 + b'\xFF' * 100
        fmt = auto_select_format(data)
        assert fmt == CompressionFormat.RLE

    def test_mixed_data(self):
        """Mixed data should suggest Kosinski."""
        data = bytes(range(256))
        fmt = auto_select_format(data)
        assert fmt == CompressionFormat.KOSINSKI


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_compress_kosinski(self):
        """compress_kosinski should work."""
        data = b'test' * 20
        compressed = compress_kosinski(data)
        assert len(compressed) > 0

    def test_decompress_kosinski(self):
        """decompress_kosinski should work."""
        data = b'test' * 20
        compressed = compress_kosinski(data)
        decompressed = decompress_kosinski(compressed)
        assert decompressed == data

    def test_compress_lzss(self):
        """compress_lzss should work."""
        data = b'test' * 20
        compressed = compress_lzss(data)
        assert len(compressed) > 0

    def test_decompress_lzss(self):
        """decompress_lzss should work."""
        data = b'test' * 20
        compressed = compress_lzss(data)
        decompressed = decompress_lzss(compressed)
        assert decompressed == data

    def test_compress_rle(self):
        """compress_rle should work."""
        data = b'\xFF' * 50
        compressed = compress_rle(data)
        assert len(compressed) < len(data)

    def test_decompress_rle(self):
        """decompress_rle should work."""
        data = b'\xFF' * 50
        compressed = compress_rle(data)
        decompressed = decompress_rle(compressed)
        assert decompressed == data


class TestFileOperations:
    """Tests for file-based compression."""

    def test_compress_file(self, temp_dir):
        """Should compress file to disk."""
        compressor = GenesisCompressor()

        # Create test file
        input_file = Path(temp_dir) / "test.bin"
        input_file.write_bytes(b'Genesis test data' * 50)

        # Compress
        result = compressor.compress_file(input_file)

        assert result.success
        output_file = input_file.with_suffix('.kos')
        assert output_file.exists()

    def test_decompress_file(self, temp_dir):
        """Should decompress file from disk."""
        compressor = GenesisCompressor()

        # Create and compress test file
        input_file = Path(temp_dir) / "test.bin"
        original_data = b'Genesis test data' * 50
        input_file.write_bytes(original_data)

        result = compressor.compress_file(input_file, format=CompressionFormat.KOSINSKI)
        compressed_file = input_file.with_suffix('.kos')

        # Decompress
        output_file = Path(temp_dir) / "test_out.bin"
        decompressed = compressor.decompress_file(
            compressed_file,
            output_file,
            CompressionFormat.KOSINSKI
        )

        assert decompressed == original_data
        assert output_file.exists()
        assert output_file.read_bytes() == original_data


class TestRealWorldData:
    """Tests with realistic Genesis tile data."""

    def test_4bpp_tileset(self):
        """Should handle 4bpp tileset data."""
        compressor = GenesisCompressor()

        # Simulate a small tileset (4 tiles, 32 bytes each)
        tiles = []
        for i in range(4):
            # Create tile with some pattern
            tile = bytes([(i * 16 + j) & 0xFF for j in range(32)])
            tiles.append(tile)

        tileset = b''.join(tiles)

        result = compressor.compress(tileset, CompressionFormat.KOSINSKI)
        assert result.success

        decompressed = compressor.decompress(result.data, result.format)
        assert decompressed == tileset

    def test_sprite_sheet(self):
        """Should handle sprite sheet data."""
        compressor = GenesisCompressor()

        # Simulate 32x32 sprite (16 tiles = 512 bytes)
        sprite_data = bytes([
            (x ^ y) & 0xFF
            for y in range(32)
            for x in range(16)  # 4bpp = 2 pixels per byte
        ])

        result = compressor.compress(sprite_data, CompressionFormat.KOSINSKI)
        assert result.success

        decompressed = compressor.decompress(result.data, result.format)
        assert decompressed == sprite_data

    def test_tilemap(self):
        """Should handle tilemap data (16-bit entries)."""
        compressor = GenesisCompressor()

        # 32x28 tilemap (Genesis default) = 896 entries × 2 bytes
        import struct
        tilemap = b''.join(
            struct.pack('>H', (y * 32 + x) & 0x7FF)
            for y in range(28)
            for x in range(32)
        )

        result = compressor.compress(tilemap, CompressionFormat.KOSINSKI)
        assert result.success

        decompressed = compressor.decompress(result.data, result.format)
        assert decompressed == tilemap
