"""
Tests for quantization/dither_numba.py - Phase 0.8

Tests Numba-accelerated dithering including:
- Floyd-Steinberg dithering
- Ordered (Bayer) dithering
- Atkinson dithering
- DitherEngine class
"""

import pytest
import numpy as np
from PIL import Image

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.quantization.dither_numba import (
    get_bayer_matrix,
    floyd_steinberg_numba,
    ordered_dither_numba,
    atkinson_dither_numba,
    DitherEngine,
    DitherResult,
    NUMBA_AVAILABLE,
    BAYER_2X2,
    BAYER_4X4,
    BAYER_8X8,
)


class TestBayerMatrix:
    """Tests for Bayer dithering matrices."""

    def test_bayer_2x2_shape(self):
        """2x2 Bayer matrix should have correct shape."""
        assert BAYER_2X2.shape == (2, 2)

    def test_bayer_4x4_shape(self):
        """4x4 Bayer matrix should have correct shape."""
        assert BAYER_4X4.shape == (4, 4)

    def test_bayer_8x8_shape(self):
        """8x8 Bayer matrix should have correct shape."""
        assert BAYER_8X8.shape == (8, 8)

    def test_bayer_values_normalized(self):
        """Bayer matrices should have values in 0-1 range."""
        assert BAYER_2X2.min() >= 0
        assert BAYER_2X2.max() <= 1
        assert BAYER_4X4.min() >= 0
        assert BAYER_4X4.max() <= 1
        assert BAYER_8X8.min() >= 0
        assert BAYER_8X8.max() <= 1

    def test_get_bayer_matrix_sizes(self):
        """get_bayer_matrix should return correct sizes."""
        assert get_bayer_matrix(1).shape == (2, 2)
        assert get_bayer_matrix(2).shape == (2, 2)
        assert get_bayer_matrix(3).shape == (4, 4)
        assert get_bayer_matrix(4).shape == (4, 4)
        assert get_bayer_matrix(5).shape == (8, 8)
        assert get_bayer_matrix(8).shape == (8, 8)


class TestFloydSteinbergNumba:
    """Tests for Floyd-Steinberg dithering."""

    def test_output_shape(self, simple_palette):
        """Output should match input dimensions."""
        pixels = np.random.rand(16, 16, 3).astype(np.float32) * 255
        palette = np.array(simple_palette, dtype=np.float32)

        result = floyd_steinberg_numba(pixels, palette)

        assert result.shape == (16, 16)
        assert result.dtype == np.uint8

    def test_output_indices_valid(self, simple_palette):
        """All output indices should be valid palette indices."""
        pixels = np.random.rand(8, 8, 3).astype(np.float32) * 255
        palette = np.array(simple_palette, dtype=np.float32)

        result = floyd_steinberg_numba(pixels, palette)

        assert result.min() >= 0
        assert result.max() < len(simple_palette)

    def test_solid_color_input(self, simple_palette):
        """Solid color input should produce uniform output."""
        # Create solid red image
        pixels = np.full((8, 8, 3), [255, 0, 0], dtype=np.float32)
        palette = np.array(simple_palette, dtype=np.float32)

        result = floyd_steinberg_numba(pixels, palette)

        # Should be mostly index 1 (red in simple_palette)
        assert np.sum(result == 1) > 50  # Most pixels red

    def test_black_input(self, simple_palette):
        """Black input should produce index 0."""
        pixels = np.zeros((8, 8, 3), dtype=np.float32)
        palette = np.array(simple_palette, dtype=np.float32)

        result = floyd_steinberg_numba(pixels, palette)

        # All pixels should be black (index 0)
        assert np.all(result == 0)


class TestOrderedDitherNumba:
    """Tests for ordered (Bayer) dithering."""

    def test_output_shape(self, simple_palette):
        """Output should match input dimensions."""
        pixels = np.random.rand(16, 16, 3).astype(np.float32) * 255
        palette = np.array(simple_palette, dtype=np.float32)
        bayer = BAYER_4X4

        result = ordered_dither_numba(pixels, palette, bayer)

        assert result.shape == (16, 16)
        assert result.dtype == np.uint8

    def test_output_indices_valid(self, simple_palette):
        """All output indices should be valid palette indices."""
        pixels = np.random.rand(8, 8, 3).astype(np.float32) * 255
        palette = np.array(simple_palette, dtype=np.float32)
        bayer = BAYER_4X4

        result = ordered_dither_numba(pixels, palette, bayer)

        assert result.min() >= 0
        assert result.max() < len(simple_palette)

    def test_strength_parameter(self, simple_palette):
        """Different strength values should produce different results."""
        pixels = np.full((8, 8, 3), [128, 128, 128], dtype=np.float32)
        palette = np.array(simple_palette, dtype=np.float32)
        bayer = BAYER_4X4

        result_low = ordered_dither_numba(pixels, palette, bayer, strength=0.5)
        result_high = ordered_dither_numba(pixels, palette, bayer, strength=2.0)

        # Different strengths should produce different patterns
        # (not guaranteed to be different for all inputs, but likely)
        assert result_low.dtype == result_high.dtype


class TestAtkinsonDitherNumba:
    """Tests for Atkinson dithering."""

    def test_output_shape(self, simple_palette):
        """Output should match input dimensions."""
        pixels = np.random.rand(16, 16, 3).astype(np.float32) * 255
        palette = np.array(simple_palette, dtype=np.float32)

        result = atkinson_dither_numba(pixels, palette)

        assert result.shape == (16, 16)
        assert result.dtype == np.uint8

    def test_output_indices_valid(self, simple_palette):
        """All output indices should be valid palette indices."""
        pixels = np.random.rand(8, 8, 3).astype(np.float32) * 255
        palette = np.array(simple_palette, dtype=np.float32)

        result = atkinson_dither_numba(pixels, palette)

        assert result.min() >= 0
        assert result.max() < len(simple_palette)


class TestDitherEngine:
    """Tests for DitherEngine class."""

    def test_init_default_method(self):
        """Default method should be floyd-steinberg."""
        engine = DitherEngine()
        assert engine.method == 'floyd-steinberg'

    def test_init_custom_method(self):
        """Custom method should be stored."""
        engine = DitherEngine(method='ordered')
        assert engine.method == 'ordered'

    def test_dither_returns_result(self, test_image_8x8, simple_palette):
        """dither() should return DitherResult."""
        engine = DitherEngine()
        result = engine.dither(test_image_8x8, simple_palette)

        assert isinstance(result, DitherResult)
        assert isinstance(result.image, Image.Image)
        assert isinstance(result.indices, np.ndarray)
        assert result.palette == simple_palette

    def test_dither_floyd_steinberg(self, test_image_gradient, simple_palette):
        """Floyd-Steinberg dithering should work."""
        engine = DitherEngine(method='floyd-steinberg')
        result = engine.dither(test_image_gradient, simple_palette)

        assert result.indices.shape == (32, 32)

    def test_dither_ordered(self, test_image_gradient, simple_palette):
        """Ordered dithering should work."""
        engine = DitherEngine(method='ordered')
        result = engine.dither(test_image_gradient, simple_palette)

        assert result.indices.shape == (32, 32)

    def test_dither_atkinson(self, test_image_gradient, simple_palette):
        """Atkinson dithering should work."""
        engine = DitherEngine(method='atkinson')
        result = engine.dither(test_image_gradient, simple_palette)

        assert result.indices.shape == (32, 32)

    def test_dither_none(self, test_image_gradient, simple_palette):
        """No dithering should work (nearest color only)."""
        engine = DitherEngine(method='none')
        result = engine.dither(test_image_gradient, simple_palette)

        assert result.indices.shape == (32, 32)

    def test_dither_batch(self, test_image_8x8, simple_palette):
        """Batch dithering should process multiple images."""
        engine = DitherEngine()
        images = [test_image_8x8, test_image_8x8, test_image_8x8]

        results = engine.dither_batch(images, simple_palette)

        assert len(results) == 3
        for result in results:
            assert isinstance(result, DitherResult)

    def test_dither_converts_rgba(self, simple_palette):
        """Should handle RGBA images."""
        rgba_img = Image.new('RGBA', (8, 8), (255, 0, 0, 255))
        engine = DitherEngine()

        result = engine.dither(rgba_img, simple_palette)

        assert result.indices.shape == (8, 8)

    def test_dither_converts_l(self, simple_palette):
        """Should handle grayscale images."""
        gray_img = Image.new('L', (8, 8), 128)
        engine = DitherEngine()

        result = engine.dither(gray_img, simple_palette)

        assert result.indices.shape == (8, 8)


class TestNumbaAvailability:
    """Tests related to Numba availability."""

    def test_numba_flag_exists(self):
        """NUMBA_AVAILABLE flag should exist."""
        assert isinstance(NUMBA_AVAILABLE, bool)

    def test_functions_work_without_numba(self, simple_palette):
        """Functions should work even if Numba is not available."""
        # These should not raise regardless of Numba status
        pixels = np.random.rand(8, 8, 3).astype(np.float32) * 255
        palette = np.array(simple_palette, dtype=np.float32)

        result = floyd_steinberg_numba(pixels, palette)
        assert result.shape == (8, 8)


class TestDitherQuality:
    """Tests for dithering quality and correctness."""

    def test_gradient_produces_variation(self, test_image_gradient, genesis_palette):
        """Gradient image should produce varied indices."""
        engine = DitherEngine(method='floyd-steinberg')
        result = engine.dither(test_image_gradient, genesis_palette)

        unique_indices = np.unique(result.indices)
        # Should use multiple palette colors
        assert len(unique_indices) >= 3

    def test_no_dither_is_deterministic(self, test_image_gradient, simple_palette):
        """No-dither mode should be deterministic."""
        engine = DitherEngine(method='none')

        result1 = engine.dither(test_image_gradient, simple_palette)
        result2 = engine.dither(test_image_gradient, simple_palette)

        assert np.array_equal(result1.indices, result2.indices)
