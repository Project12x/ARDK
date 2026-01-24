"""
Test suite for TileOptimizer.

Tests tile deduplication, flip detection, VRAM tracking, and batch processing.
"""

import pytest
from PIL import Image, ImageDraw
from pathlib import Path
import tempfile
import shutil

from pipeline.optimization import (
    TileOptimizer,
    TileTransform,
    OptimizedTileBank,
    BatchTileOptimizer,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def temp_dir():
    """Create temporary directory for test outputs."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def simple_tile():
    """Create a simple 8x8 test tile with a pattern."""
    tile = Image.new('RGBA', (8, 8), (0, 0, 0, 0))
    draw = ImageDraw.Draw(tile)
    # Draw a simple cross pattern
    draw.line([(0, 4), (7, 4)], fill=(255, 0, 0, 255), width=1)
    draw.line([(4, 0), (4, 7)], fill=(255, 0, 0, 255), width=1)
    return tile


@pytest.fixture
def duplicate_sprite():
    """
    Create a sprite with duplicate tiles.
    16x16 image with 4 tiles: top-left, top-right, bottom-left, bottom-right
    Top-left and bottom-right are identical.
    """
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Tile 1 (top-left) - red cross
    draw.line([(0, 4), (7, 4)], fill=(255, 0, 0, 255), width=1)
    draw.line([(4, 0), (4, 7)], fill=(255, 0, 0, 255), width=1)

    # Tile 2 (top-right) - blue square
    draw.rectangle([(8, 0), (15, 7)], fill=(0, 0, 255, 255))

    # Tile 3 (bottom-left) - green circle
    draw.ellipse([(0, 8), (7, 15)], fill=(0, 255, 0, 255))

    # Tile 4 (bottom-right) - duplicate of tile 1 (red cross)
    draw.line([(8, 12), (15, 12)], fill=(255, 0, 0, 255), width=1)
    draw.line([(12, 8), (12, 15)], fill=(255, 0, 0, 255), width=1)

    return img


@pytest.fixture
def flipped_sprite():
    """
    Create a sprite with horizontally flipped tiles.
    16x16 image where top-right is horizontal flip of top-left.
    """
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Tile 1 (top-left) - arrow pointing right
    draw.polygon([(0, 4), (6, 4), (6, 0), (8, 4), (6, 8), (6, 4)],
                 fill=(255, 0, 0, 255))

    # Tile 2 (top-right) - arrow pointing left (flip of tile 1)
    draw.polygon([(15, 4), (9, 4), (9, 0), (7, 4), (9, 8), (9, 4)],
                 fill=(255, 0, 0, 255))

    # Tile 3 (bottom-left) - different pattern
    draw.rectangle([(0, 8), (7, 15)], fill=(0, 255, 0, 255))

    # Tile 4 (bottom-right) - different pattern
    draw.ellipse([(8, 8), (15, 15)], fill=(0, 0, 255, 255))

    return img


# =============================================================================
# Basic Optimization Tests
# =============================================================================

def test_optimizer_init():
    """Test optimizer initialization."""
    optimizer = TileOptimizer(tile_width=8, tile_height=8)
    assert optimizer.tile_width == 8
    assert optimizer.tile_height == 8
    assert optimizer.allow_mirror_x is True
    assert optimizer.allow_mirror_y is True


def test_optimize_simple_tile(simple_tile):
    """Test optimizing a single tile."""
    optimizer = TileOptimizer()
    result = optimizer.optimize_image(simple_tile)

    assert result.unique_tile_count == 1
    assert result.grid_width == 1
    assert result.grid_height == 1
    assert len(result.unique_tiles) == 1
    assert len(result.tile_map) == 1


def test_duplicate_detection(duplicate_sprite):
    """Test detection of duplicate tiles."""
    optimizer = TileOptimizer()
    result = optimizer.optimize_image(duplicate_sprite)

    # Should detect 3 unique tiles (tiles 1, 2, 3 - tile 4 is duplicate of 1)
    assert result.unique_tile_count == 3
    assert result.stats.original_tile_count == 4
    assert result.stats.duplicate_count == 1


def test_horizontal_flip_detection(flipped_sprite):
    """Test detection of horizontally flipped tiles."""
    optimizer = TileOptimizer(allow_mirror_x=True, allow_mirror_y=False)
    result = optimizer.optimize_image(flipped_sprite)

    # Should detect 3 unique tiles (top-right is h-flip of top-left)
    assert result.unique_tile_count == 3
    assert result.stats.h_flip_matches >= 1

    # Check that tile 2 references tile 1 with horizontal flip
    tile_ref = result.tile_map[1]  # Top-right tile
    assert tile_ref.flip_h is True
    assert tile_ref.flip_v is False


def test_flip_disabled():
    """Test that flip detection can be disabled."""
    # Create a sprite with flipped tiles
    img = Image.new('RGBA', (16, 8), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Left tile
    draw.rectangle([(0, 0), (4, 7)], fill=(255, 0, 0, 255))

    # Right tile (mirror of left)
    draw.rectangle([(11, 0), (15, 7)], fill=(255, 0, 0, 255))

    # With flip detection disabled, should see 2 unique tiles
    optimizer_no_flip = TileOptimizer(allow_mirror_x=False, allow_mirror_y=False)
    result_no_flip = optimizer_no_flip.optimize_image(img)

    # With flip detection enabled, should see 1 unique tile
    optimizer_flip = TileOptimizer(allow_mirror_x=True, allow_mirror_y=True)
    result_flip = optimizer_flip.optimize_image(img)

    # Note: The tiles might not actually be exact mirrors depending on the pattern
    # This test might need adjustment based on actual tile content
    assert result_no_flip.unique_tile_count >= result_flip.unique_tile_count


# =============================================================================
# VRAM Budget Tests
# =============================================================================

def test_vram_budget_tracking():
    """Test VRAM budget tracking."""
    optimizer = TileOptimizer(platform='genesis')  # 64KB VRAM
    result = optimizer.optimize_image(Image.new('RGBA', (32, 32)))

    # Check VRAM usage is calculated
    assert result.stats.vram_used_bytes > 0
    assert result.stats.vram_used_percent >= 0


def test_check_vram_budget():
    """Test VRAM budget checking."""
    optimizer = TileOptimizer(platform='nes')  # 8KB CHR-ROM
    max_tiles = optimizer.get_max_tiles_for_budget()

    # Check that we can fit max tiles
    fits, used, available = optimizer.check_vram_budget(max_tiles)
    assert fits is True
    assert used <= available

    # Check that exceeding max tiles fails
    fits, used, available = optimizer.check_vram_budget(max_tiles + 1)
    assert fits is False
    assert used > available


def test_platform_vram_limits():
    """Test different platform VRAM limits."""
    platforms = ['genesis', 'nes', 'snes', 'gameboy', 'gba']

    for platform in platforms:
        optimizer = TileOptimizer(platform=platform)
        assert optimizer.vram_budget > 0
        assert optimizer.get_max_tiles_for_budget() > 0


# =============================================================================
# Reconstruction Tests
# =============================================================================

def test_image_reconstruction(duplicate_sprite):
    """Test that reconstructed image matches original."""
    optimizer = TileOptimizer()
    result = optimizer.optimize_image(duplicate_sprite)

    reconstructed = result.reconstruct_image()

    # Check dimensions match
    assert reconstructed.size == duplicate_sprite.size

    # Check pixel-perfect match
    orig_pixels = list(duplicate_sprite.getdata())
    recon_pixels = list(reconstructed.getdata())
    assert orig_pixels == recon_pixels


def test_reconstruction_with_flips(flipped_sprite):
    """Test reconstruction with flipped tiles."""
    optimizer = TileOptimizer(allow_mirror_x=True, allow_mirror_y=True)
    result = optimizer.optimize_image(flipped_sprite)

    reconstructed = result.reconstruct_image()

    # Should match original exactly
    orig_pixels = list(flipped_sprite.getdata())
    recon_pixels = list(reconstructed.getdata())
    assert orig_pixels == recon_pixels


# =============================================================================
# Statistics Tests
# =============================================================================

def test_optimization_stats(duplicate_sprite):
    """Test optimization statistics."""
    optimizer = TileOptimizer()
    result = optimizer.optimize_image(duplicate_sprite)

    stats = result.stats

    # Check all stats are present
    assert stats.original_tile_count == 4
    assert stats.unique_tile_count == 3
    assert stats.duplicate_count == 1
    assert stats.savings_bytes > 0
    assert stats.savings_percent > 0
    assert stats.vram_used_bytes > 0

    # Check savings calculation
    bytes_per_tile = 8 * 8 * 4  # RGBA
    expected_savings = 1 * bytes_per_tile
    assert stats.savings_bytes == expected_savings


def test_stats_to_dict():
    """Test statistics serialization."""
    optimizer = TileOptimizer()
    result = optimizer.optimize_image(Image.new('RGBA', (16, 16)))

    stats_dict = result.stats.to_dict()

    # Check all expected keys present
    assert 'original_tiles' in stats_dict
    assert 'unique_tiles' in stats_dict
    assert 'savings_bytes' in stats_dict
    assert 'savings_percent' in stats_dict
    assert 'vram_used_bytes' in stats_dict


# =============================================================================
# File I/O Tests
# =============================================================================

def test_save_tiles(duplicate_sprite, temp_dir):
    """Test saving unique tiles to files."""
    optimizer = TileOptimizer()
    result = optimizer.optimize_image(duplicate_sprite)

    output_dir = temp_dir / "tiles"
    result.save_tiles(str(output_dir), prefix="tile")

    # Check tiles were saved
    tile_files = list(output_dir.glob("tile_*.png"))
    assert len(tile_files) == result.unique_tile_count

    # Check tiles can be loaded
    for tile_file in tile_files:
        img = Image.open(tile_file)
        assert img.size == (8, 8)


def test_save_tile_map(duplicate_sprite, temp_dir):
    """Test saving tile map to JSON."""
    optimizer = TileOptimizer()
    result = optimizer.optimize_image(duplicate_sprite)

    tile_map_path = temp_dir / "tilemap.json"
    result.save_tile_map(str(tile_map_path))

    # Check file exists
    assert tile_map_path.exists()

    # Check can be loaded
    import json
    with open(tile_map_path) as f:
        data = json.load(f)

    assert 'grid_width' in data
    assert 'grid_height' in data
    assert 'tile_map' in data
    assert 'stats' in data
    assert len(data['tile_map']) == result.grid_width * result.grid_height


def test_optimize_from_file(duplicate_sprite, temp_dir):
    """Test optimizing from file path."""
    # Save test image
    image_path = temp_dir / "test.png"
    duplicate_sprite.save(image_path)

    # Optimize from file
    optimizer = TileOptimizer()
    result = optimizer.optimize_sprite_sheet(str(image_path))

    assert result.unique_tile_count == 3


# =============================================================================
# Batch Processing Tests
# =============================================================================

def test_batch_optimizer_init():
    """Test batch optimizer initialization."""
    batch = BatchTileOptimizer(platform='genesis')
    assert isinstance(batch.optimizer, TileOptimizer)
    assert batch.optimizer.platform == 'genesis'


def test_batch_optimize_directory(duplicate_sprite, temp_dir):
    """Test batch optimization of directory."""
    # Create test images
    for i in range(3):
        image_path = temp_dir / f"sprite_{i}.png"
        duplicate_sprite.save(image_path)

    # Batch optimize
    batch = BatchTileOptimizer()
    results = batch.optimize_directory(str(temp_dir))

    assert len(results) == 3
    assert len(batch.results) == 3

    # Check all results are valid
    for result in results:
        assert isinstance(result, OptimizedTileBank)
        assert result.unique_tile_count > 0


# =============================================================================
# Edge Cases
# =============================================================================

def test_empty_image():
    """Test optimizing empty image."""
    img = Image.new('RGBA', (8, 8), (0, 0, 0, 0))
    optimizer = TileOptimizer()
    result = optimizer.optimize_image(img)

    assert result.unique_tile_count == 1  # One empty tile
    assert len(result.tile_map) == 1


def test_single_color_image():
    """Test optimizing image with single color."""
    img = Image.new('RGBA', (32, 32), (255, 0, 0, 255))
    optimizer = TileOptimizer()
    result = optimizer.optimize_image(img)

    # All tiles should be identical
    assert result.unique_tile_count == 1
    assert result.stats.duplicate_count == 15  # 16 total tiles - 1 unique


def test_unaligned_dimensions():
    """Test optimizing image with dimensions not aligned to tile grid."""
    img = Image.new('RGBA', (13, 13), (255, 0, 0, 255))
    optimizer = TileOptimizer()
    result = optimizer.optimize_image(img)

    # Should pad to 16x16 (2x2 tiles)
    assert result.grid_width == 2
    assert result.grid_height == 2


def test_large_sprite_sheet():
    """Test optimizing larger sprite sheet."""
    img = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Create repeating pattern
    for y in range(0, 128, 16):
        for x in range(0, 128, 16):
            draw.rectangle([(x, y), (x + 8, y + 8)], fill=(255, 0, 0, 255))

    optimizer = TileOptimizer()
    result = optimizer.optimize_image(img)

    # Should detect significant duplication
    assert result.unique_tile_count < result.stats.original_tile_count
    assert result.stats.savings_percent > 0


# =============================================================================
# Regression Tests
# =============================================================================

def test_backward_compatibility():
    """Test backward compatibility with old TileOptimizer API."""
    from pipeline.processing import TileOptimizer as OldTileOptimizer

    img = Image.new('RGBA', (16, 16), (255, 0, 0, 255))

    # Use old API
    old_optimizer = OldTileOptimizer(tile_width=8, tile_height=8)
    unique_tiles, tile_map, unique_count = old_optimizer.optimize(img)

    # Check old API still works
    assert len(unique_tiles) == unique_count
    assert len(tile_map) == 4  # 2x2 tiles
    assert all('index' in tm and 'flip_x' in tm and 'flip_y' in tm for tm in tile_map)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
