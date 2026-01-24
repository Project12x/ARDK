"""
Pytest fixtures for ARDK Pipeline tests.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from PIL import Image
import numpy as np


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    temp = tempfile.mkdtemp(prefix="ardk_test_")
    yield temp
    shutil.rmtree(temp, ignore_errors=True)


@pytest.fixture
def simple_palette():
    """Basic 4-color palette for testing."""
    return [
        (0, 0, 0),       # Black
        (255, 0, 0),     # Red
        (0, 255, 0),     # Green
        (0, 0, 255),     # Blue
    ]


@pytest.fixture
def genesis_palette():
    """Genesis-style 16-color palette."""
    return [
        (0, 0, 0),       # 0: Transparent/Black
        (32, 32, 32),    # 1: Dark gray
        (64, 64, 64),    # 2: Gray
        (128, 128, 128), # 3: Light gray
        (192, 192, 192), # 4: Near white
        (255, 255, 255), # 5: White
        (255, 0, 0),     # 6: Red
        (0, 255, 0),     # 7: Green
        (0, 0, 255),     # 8: Blue
        (255, 255, 0),   # 9: Yellow
        (255, 0, 255),   # 10: Magenta
        (0, 255, 255),   # 11: Cyan
        (128, 0, 0),     # 12: Dark red
        (0, 128, 0),     # 13: Dark green
        (0, 0, 128),     # 14: Dark blue
        (128, 128, 0),   # 15: Olive
    ]


@pytest.fixture
def test_image_8x8():
    """Simple 8x8 test image with gradient."""
    img = Image.new('RGB', (8, 8))
    pixels = img.load()
    for y in range(8):
        for x in range(8):
            v = int((x + y) / 14 * 255)
            pixels[x, y] = (v, v, v)
    return img


@pytest.fixture
def test_image_32x32():
    """32x32 test image with color regions."""
    img = Image.new('RGB', (32, 32))
    pixels = img.load()
    for y in range(32):
        for x in range(32):
            if x < 16 and y < 16:
                pixels[x, y] = (255, 0, 0)    # Red quadrant
            elif x >= 16 and y < 16:
                pixels[x, y] = (0, 255, 0)    # Green quadrant
            elif x < 16 and y >= 16:
                pixels[x, y] = (0, 0, 255)    # Blue quadrant
            else:
                pixels[x, y] = (255, 255, 0)  # Yellow quadrant
    return img


@pytest.fixture
def test_image_gradient():
    """32x32 smooth gradient for dithering tests."""
    width, height = 32, 32
    img = Image.new('RGB', (width, height))
    pixels = img.load()
    for y in range(height):
        for x in range(width):
            r = int(x / (width - 1) * 255)
            g = int(y / (height - 1) * 255)
            b = 128
            pixels[x, y] = (r, g, b)
    return img


@pytest.fixture
def sample_png_file(temp_dir, test_image_32x32):
    """Create a sample PNG file for testing."""
    path = Path(temp_dir) / "test_sprite.png"
    test_image_32x32.save(path)
    return str(path)
