"""
Tests for rotation.py - Phase 1.4

Tests 8-direction sprite rotation including:
- Direction enum
- SpriteRotator (simple, mirror, ai methods)
- Helper functions (rotate_8way, rotate_4way)
- Animation frame rotation
"""

import pytest
from PIL import Image
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.rotation import (
    Direction,
    IsometricDirection,
    SpriteRotator,
    RotationConfig,
    RotationResult,
    rotate_8way,
    rotate_4way,
    generate_direction_sheet,
    batch_rotate,
    rotate_animation_frames,
    generate_animation_sheets,
    rotate_isometric,
    DIRECTION_NAMES,
    DIRECTION_SHORT,
)


class TestDirection:
    """Tests for Direction enum."""

    def test_direction_values(self):
        """Direction values should be 0-7."""
        assert Direction.N.value == 0
        assert Direction.NE.value == 1
        assert Direction.E.value == 2
        assert Direction.SE.value == 3
        assert Direction.S.value == 4
        assert Direction.SW.value == 5
        assert Direction.W.value == 6
        assert Direction.NW.value == 7

    def test_direction_angles(self):
        """Direction angles should be multiples of 45."""
        assert Direction.N.angle == 0
        assert Direction.E.angle == 90
        assert Direction.S.angle == 180
        assert Direction.W.angle == 270

    def test_direction_opposite(self):
        """opposite should return 180° away."""
        assert Direction.N.opposite == Direction.S
        assert Direction.E.opposite == Direction.W
        assert Direction.NE.opposite == Direction.SW

    def test_direction_mirror_h(self):
        """mirror_h should flip E↔W."""
        assert Direction.E.mirror_h == Direction.W
        assert Direction.W.mirror_h == Direction.E
        assert Direction.NE.mirror_h == Direction.NW
        assert Direction.N.mirror_h == Direction.N  # N/S unchanged

    def test_from_angle(self):
        """from_angle should return nearest direction."""
        assert Direction.from_angle(0) == Direction.N
        assert Direction.from_angle(90) == Direction.E
        assert Direction.from_angle(45) == Direction.NE
        assert Direction.from_angle(360) == Direction.N  # Wrap

    def test_cardinal(self):
        """cardinal should return N, E, S, W."""
        cardinal = Direction.cardinal()
        assert len(cardinal) == 4
        assert Direction.N in cardinal
        assert Direction.E in cardinal
        assert Direction.S in cardinal
        assert Direction.W in cardinal

    def test_diagonal(self):
        """diagonal should return NE, SE, SW, NW."""
        diagonal = Direction.diagonal()
        assert len(diagonal) == 4
        assert Direction.NE in diagonal
        assert Direction.SE in diagonal


class TestDirectionNames:
    """Tests for direction name mappings."""

    def test_all_directions_have_names(self):
        """All directions should have full names."""
        for d in Direction:
            assert d in DIRECTION_NAMES

    def test_all_directions_have_short_names(self):
        """All directions should have short names."""
        for d in Direction:
            assert d in DIRECTION_SHORT

    def test_name_examples(self):
        """Spot check some names."""
        assert DIRECTION_NAMES[Direction.N] == 'north'
        assert DIRECTION_SHORT[Direction.NE] == 'ne'


class TestSpriteRotator:
    """Tests for SpriteRotator class."""

    @pytest.fixture
    def test_sprite(self):
        """Create simple test sprite."""
        img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
        # Draw an arrow pointing right (E)
        pixels = img.load()
        for y in range(12, 20):
            for x in range(8, 24):
                pixels[x, y] = (255, 0, 0, 255)
        return img

    def test_init_default(self):
        """Default method should be mirror."""
        rotator = SpriteRotator()
        assert rotator.method == 'mirror'

    def test_init_custom_method(self):
        """Custom method should be stored."""
        rotator = SpriteRotator(method='simple')
        assert rotator.method == 'simple'

    def test_rotate_returns_result(self, test_sprite):
        """rotate should return RotationResult."""
        rotator = SpriteRotator(method='simple')
        result = rotator.rotate(test_sprite)

        assert isinstance(result, RotationResult)
        assert len(result.directions) == 8

    def test_rotate_all_directions_present(self, test_sprite):
        """All 8 directions should be in result."""
        rotator = SpriteRotator(method='simple')
        result = rotator.rotate(test_sprite)

        for d in Direction:
            assert d in result.directions
            assert isinstance(result.directions[d], Image.Image)

    def test_rotate_4way(self, test_sprite):
        """4-way mode should only return cardinal directions."""
        rotator = SpriteRotator(method='simple')
        result = rotator.rotate(test_sprite, directions_4way=True)

        assert len(result.directions) == 4
        assert Direction.N in result.directions
        assert Direction.E in result.directions
        assert Direction.NE not in result.directions

    def test_rotate_simple_method(self, test_sprite):
        """Simple method should produce 8 unique sprites."""
        rotator = SpriteRotator(method='simple')
        result = rotator.rotate(test_sprite)

        assert result.unique_count == 8
        assert result.method == 'simple'

    def test_rotate_mirror_method(self, test_sprite):
        """Mirror method should produce 5 unique sprites."""
        rotator = SpriteRotator(method='mirror')
        result = rotator.rotate(test_sprite)

        assert result.unique_count == 5
        assert result.method == 'mirror'

    def test_source_direction_affects_output(self, test_sprite):
        """Different source direction should produce different results."""
        rotator = SpriteRotator(method='simple')

        result_e = rotator.rotate(test_sprite, source_direction=Direction.E)
        result_n = rotator.rotate(test_sprite, source_direction=Direction.N)

        # The sprite facing E and N should produce different outputs
        # Check that at least one direction differs
        img_e = result_e.directions[Direction.E]
        img_n = result_n.directions[Direction.E]

        # They shouldn't be identical
        assert list(img_e.getdata()) != list(img_n.getdata())


class TestRotationResult:
    """Tests for RotationResult class."""

    @pytest.fixture
    def result(self, test_image_32x32):
        """Create test result."""
        directions = {d: test_image_32x32.copy() for d in Direction}
        return RotationResult(
            directions=directions,
            source_direction=Direction.E,
            method='simple',
            unique_count=8
        )

    def test_get(self, result):
        """get should return image for direction."""
        img = result.get(Direction.N)
        assert isinstance(img, Image.Image)

    def test_save_all(self, result, temp_dir):
        """save_all should save all directions."""
        paths = result.save_all(temp_dir, prefix='test')

        assert len(paths) == 8
        for path in paths:
            assert Path(path).exists()


class TestRotate8Way:
    """Tests for rotate_8way convenience function."""

    def test_returns_dict(self, test_image_32x32):
        """Should return dict of directions."""
        result = rotate_8way(test_image_32x32)

        assert isinstance(result, dict)
        assert len(result) == 8
        for d in Direction:
            assert d in result


class TestRotate4Way:
    """Tests for rotate_4way convenience function."""

    def test_returns_dict(self, test_image_32x32):
        """Should return dict of 4 directions."""
        result = rotate_4way(test_image_32x32)

        assert isinstance(result, dict)
        assert len(result) == 4
        assert Direction.N in result
        assert Direction.NE not in result


class TestGenerateDirectionSheet:
    """Tests for generate_direction_sheet function."""

    def test_row_layout(self, test_image_32x32):
        """Row layout should be horizontal strip."""
        sheet = generate_direction_sheet(test_image_32x32, layout='row')

        assert sheet.width == 32 * 8  # 8 sprites
        assert sheet.height == 32

    def test_column_layout(self, test_image_32x32):
        """Column layout should be vertical strip."""
        sheet = generate_direction_sheet(test_image_32x32, layout='column')

        assert sheet.width == 32
        assert sheet.height == 32 * 8

    def test_grid_layout(self, test_image_32x32):
        """Grid layout should be 4x2."""
        sheet = generate_direction_sheet(test_image_32x32, layout='grid')

        assert sheet.width == 32 * 4
        assert sheet.height == 32 * 2

    def test_4way_sheet(self, test_image_32x32):
        """4-way sheet should only have 4 sprites."""
        sheet = generate_direction_sheet(
            test_image_32x32,
            directions_4way=True,
            layout='row'
        )

        assert sheet.width == 32 * 4


class TestBatchRotate:
    """Tests for batch_rotate function."""

    def test_batch_multiple_images(self, test_image_32x32):
        """Should rotate multiple images."""
        images = [test_image_32x32.copy() for _ in range(5)]
        results = batch_rotate(images)

        assert len(results) == 5
        for result in results:
            assert isinstance(result, RotationResult)


class TestRotateAnimationFrames:
    """Tests for rotate_animation_frames function."""

    def test_rotates_all_frames(self, test_image_32x32):
        """Should rotate all frames to all directions."""
        frames = [test_image_32x32.copy() for _ in range(4)]
        result = rotate_animation_frames(frames)

        assert len(result) == 8  # 8 directions
        for direction, dir_frames in result.items():
            assert len(dir_frames) == 4  # 4 frames each


class TestGenerateAnimationSheets:
    """Tests for generate_animation_sheets function."""

    def test_generates_sheets(self, test_image_32x32):
        """Should generate sprite sheet per direction."""
        frames = [test_image_32x32.copy() for _ in range(4)]
        sheets = generate_animation_sheets(frames)

        assert len(sheets) == 8
        for direction, sheet in sheets.items():
            assert sheet.width == 32 * 4  # 4 frames horizontal


class TestRotateIsometric:
    """Tests for rotate_isometric function."""

    def test_returns_isometric_directions(self, test_image_32x32):
        """Should return IsometricDirection keys."""
        result = rotate_isometric(test_image_32x32)

        assert len(result) == 8
        for d in IsometricDirection:
            assert d in result


class TestIsometricDirection:
    """Tests for IsometricDirection enum."""

    def test_has_8_values(self):
        """Should have 8 directions."""
        assert len(IsometricDirection) == 8

    def test_se_is_primary(self):
        """SE should be value 0 (primary isometric down)."""
        assert IsometricDirection.SE.value == 0
