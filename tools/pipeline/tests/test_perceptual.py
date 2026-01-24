"""
Tests for quantization/perceptual.py - Phase 0.7

Tests perceptual color science functions including:
- RGB to LAB conversion
- Color distance calculations
- find_nearest_perceptual
- extract_optimal_palette
"""

import pytest
import numpy as np
from PIL import Image

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.quantization.perceptual import (
    rgb_to_lab,
    lab_to_rgb,
    calculate_color_distance,
    find_nearest_perceptual,
    find_nearest_rgb,
    COLOUR_AVAILABLE,
    COLORSPACIOUS_AVAILABLE,
)


class TestRgbToLab:
    """Tests for RGB to LAB color conversion."""

    def test_black_conversion(self):
        """Black should convert to L=0."""
        lab = rgb_to_lab((0, 0, 0))
        assert lab[0] == pytest.approx(0, abs=1)  # L is near 0

    def test_white_conversion(self):
        """White should convert to L=100."""
        lab = rgb_to_lab((255, 255, 255))
        assert lab[0] == pytest.approx(100, abs=1)  # L is near 100

    def test_gray_conversion(self):
        """Gray should have a/b near 0."""
        lab = rgb_to_lab((128, 128, 128))
        assert abs(lab[1]) < 5  # a near 0
        assert abs(lab[2]) < 5  # b near 0

    def test_red_conversion(self):
        """Red should have positive a."""
        lab = rgb_to_lab((255, 0, 0))
        assert lab[1] > 0  # a is positive for red

    def test_green_conversion(self):
        """Green should have negative a."""
        lab = rgb_to_lab((0, 255, 0))
        assert lab[1] < 0  # a is negative for green


class TestLabToRgb:
    """Tests for LAB to RGB conversion."""

    def test_roundtrip_black(self):
        """Black should roundtrip correctly."""
        rgb = (0, 0, 0)
        lab = rgb_to_lab(rgb)
        result = lab_to_rgb(lab)
        assert result == pytest.approx(rgb, abs=2)

    def test_roundtrip_white(self):
        """White should roundtrip correctly."""
        rgb = (255, 255, 255)
        lab = rgb_to_lab(rgb)
        result = lab_to_rgb(lab)
        assert result == pytest.approx(rgb, abs=2)

    def test_roundtrip_red(self):
        """Red should roundtrip correctly."""
        rgb = (255, 0, 0)
        lab = rgb_to_lab(rgb)
        result = lab_to_rgb(lab)
        assert result[0] > 250  # Red channel high
        assert result[1] < 5    # Green channel low
        assert result[2] < 5    # Blue channel low


class TestColorDistance:
    """Tests for color distance calculations."""

    def test_same_color_zero_distance(self):
        """Same color should have zero distance."""
        c = (128, 64, 32)
        assert calculate_color_distance(c, c, method='RGB') == 0
        assert calculate_color_distance(c, c, method='CIELab') == pytest.approx(0, abs=0.01)

    def test_black_white_max_distance(self):
        """Black and white should have large distance."""
        black = (0, 0, 0)
        white = (255, 255, 255)
        dist = calculate_color_distance(black, white, method='RGB')
        assert dist > 400  # sqrt(255^2 * 3) ≈ 441

    def test_rgb_method_euclidean(self):
        """RGB method should be simple Euclidean."""
        c1 = (0, 0, 0)
        c2 = (3, 4, 0)  # 3-4-5 triangle
        dist = calculate_color_distance(c1, c2, method='RGB')
        assert dist == pytest.approx(5.0, abs=0.01)

    def test_perceptual_vs_rgb(self):
        """Perceptual methods should exist and return floats."""
        c1 = (255, 0, 0)
        c2 = (0, 255, 0)

        rgb_dist = calculate_color_distance(c1, c2, method='RGB')
        lab_dist = calculate_color_distance(c1, c2, method='CIELab')

        assert isinstance(rgb_dist, float)
        assert isinstance(lab_dist, float)
        assert lab_dist > 0

    @pytest.mark.skipif(not COLOUR_AVAILABLE, reason="colour-science not installed")
    def test_ciede2000_available(self):
        """CIEDE2000 should work when colour-science is installed."""
        c1 = (255, 0, 0)
        c2 = (200, 50, 50)
        dist = calculate_color_distance(c1, c2, method='CIEDE2000')
        assert dist > 0

    @pytest.mark.skipif(not COLORSPACIOUS_AVAILABLE, reason="colorspacious not installed")
    def test_cam02_ucs_available(self):
        """CAM02-UCS should work when colorspacious is installed."""
        c1 = (255, 0, 0)
        c2 = (200, 50, 50)
        dist = calculate_color_distance(c1, c2, method='CAM02-UCS')
        assert dist > 0


class TestFindNearestPerceptual:
    """Tests for find_nearest_perceptual function."""

    def test_exact_match(self, simple_palette):
        """Exact color match should return correct index."""
        assert find_nearest_perceptual((0, 0, 0), simple_palette) == 0
        assert find_nearest_perceptual((255, 0, 0), simple_palette) == 1
        assert find_nearest_perceptual((0, 255, 0), simple_palette) == 2
        assert find_nearest_perceptual((0, 0, 255), simple_palette) == 3

    def test_close_color_match(self, simple_palette):
        """Close colors should match the nearest palette entry."""
        # Dark red should match red
        idx = find_nearest_perceptual((200, 50, 50), simple_palette, method='RGB')
        assert idx == 1  # Red

        # Dark green should match green
        idx = find_nearest_perceptual((50, 200, 50), simple_palette, method='RGB')
        assert idx == 2  # Green

    def test_empty_palette_raises(self):
        """Empty palette should raise ValueError."""
        with pytest.raises(ValueError, match="empty"):
            find_nearest_perceptual((128, 128, 128), [])

    def test_single_color_palette(self):
        """Single color palette should always return 0."""
        palette = [(100, 100, 100)]
        assert find_nearest_perceptual((0, 0, 0), palette) == 0
        assert find_nearest_perceptual((255, 255, 255), palette) == 0

    def test_all_methods_work(self, simple_palette):
        """All color distance methods should work."""
        color = (128, 64, 32)

        for method in ['RGB', 'CIELab']:
            idx = find_nearest_perceptual(color, simple_palette, method=method)
            assert 0 <= idx < len(simple_palette)


class TestFindNearestRgb:
    """Tests for find_nearest_rgb shortcut function."""

    def test_same_as_rgb_method(self, simple_palette):
        """Should be equivalent to find_nearest_perceptual with RGB method."""
        color = (128, 64, 32)

        rgb_idx = find_nearest_rgb(color, simple_palette)
        perceptual_idx = find_nearest_perceptual(color, simple_palette, method='RGB')

        assert rgb_idx == perceptual_idx


class TestOptionalDependencies:
    """Tests related to optional dependencies."""

    def test_fallback_works_without_colour(self):
        """Functions should work even without colour-science."""
        # These should not raise even without optional deps
        lab = rgb_to_lab((128, 128, 128))
        assert len(lab) == 3

        rgb = lab_to_rgb(lab)
        assert len(rgb) == 3

    def test_distance_fallback(self):
        """Color distance should fall back gracefully."""
        c1 = (255, 0, 0)
        c2 = (0, 255, 0)

        # Should not raise, even if optional deps missing
        dist = calculate_color_distance(c1, c2, method='CIEDE2000')
        assert dist > 0
