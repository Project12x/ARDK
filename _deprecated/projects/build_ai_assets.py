#!/usr/bin/env python3
"""
Build AI Assets for HAL Demo v5.0
Uses multi-model consensus and smart background detection via pipeline_bridge.

Features:
- Multi-AI consensus for sprite detection (2+ models must agree)
- FloodFill-based background detection (preserves internal blacks)
- AI-optimized palette extraction
- Model-per-task optimization
- Debug output for troubleshooting
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'tools'))

from PIL import Image, ImageDraw
import numpy as np
from pathlib import Path

# Import our pipeline bridge with all the advanced features
from pipeline_bridge import (
    detect_sprite_consensus,
    detect_background_smart,
    get_content_mask,
    extract_palette_ai,
    get_best_model,
    get_nearest_nes_color,
    process_sprite_with_consensus,
    NES_PALETTE_RGB,
    FloodFillBackgroundDetector,
)

# =============================================================================
# NES CHR Conversion
# =============================================================================

def get_palette_rgb(palette):
    """Get RGB tuples for a palette of NES indices."""
    return [NES_PALETTE_RGB.get(c, (0, 0, 0)) for c in palette]


def find_closest_color(r, g, b, palette_rgb, exclude_zero=True):
    """Find closest palette index for an RGB color."""
    min_dist = float('inf')
    best_idx = 1 if exclude_zero else 0
    start_idx = 1 if exclude_zero else 0

    for idx in range(start_idx, len(palette_rgb)):
        pr, pg, pb = palette_rgb[idx]
        dist = (int(r) - int(pr))**2 + (int(g) - int(pg))**2 + (int(b) - int(pb))**2
        if dist < min_dist:
            min_dist = dist
            best_idx = idx
    return best_idx


def is_transparent_pixel(r, g, b, a, bg_color=None, threshold=30):
    """Detect if a pixel should be transparent."""
    if a < 128:
        return True

    if bg_color is not None:
        bg_r, bg_g, bg_b = bg_color
        dist = abs(int(r) - int(bg_r)) + abs(int(g) - int(bg_g)) + abs(int(b) - int(bg_b))
        if dist < threshold:
            return True

    return False


def auto_contrast(img):
    """Auto-level image to enhance contrast for dark sprites."""
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    arr = np.array(img, dtype=np.float32)
    rgb = arr[:, :, :3]
    alpha = arr[:, :, 3]

    mask = alpha > 128
    if not np.any(mask):
        return img

    visible_rgb = rgb[mask]
    min_val = np.min(visible_rgb)
    max_val = np.max(visible_rgb)

    if max_val - min_val < 100:
        if max_val > min_val:
            rgb = (rgb - min_val) * (255.0 / (max_val - min_val))
            rgb = np.clip(rgb, 0, 255)
            arr[:, :, :3] = rgb

    return Image.fromarray(arr.astype(np.uint8), 'RGBA')


def image_to_chr_16x16(img, palette, bg_color=None):
    """Convert a 16x16 image to NES CHR format (4 tiles)."""
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    if img.size != (16, 16):
        img = img.resize((16, 16), Image.NEAREST)

    img = auto_contrast(img)
    palette_rgb = get_palette_rgb(palette)
    pixels = np.array(img)
    chr_data = bytearray()

    # Tile order: TL (0,0), TR (8,0), BL (0,8), BR (8,8)
    for tile_x, tile_y in [(0, 0), (8, 0), (0, 8), (8, 8)]:
        plane0, plane1 = [], []
        for row in range(8):
            p0_byte, p1_byte = 0, 0
            for col in range(8):
                r, g, b, a = pixels[tile_y + row, tile_x + col]
                if is_transparent_pixel(r, g, b, a, bg_color):
                    color_idx = 0
                else:
                    color_idx = find_closest_color(r, g, b, palette_rgb, exclude_zero=True)
                p0_byte |= ((color_idx & 1) << (7 - col))
                p1_byte |= (((color_idx >> 1) & 1) << (7 - col))
            plane0.append(p0_byte)
            plane1.append(p1_byte)
        chr_data.extend(plane0)
        chr_data.extend(plane1)

    return chr_data


def image_to_chr_32x32(img, palette, bg_color=None):
    """Convert a 32x32 image to NES CHR format (16 tiles in 4x4 grid).

    NES CHR Format: Each 8x8 tile = 16 bytes (8 bytes plane0 + 8 bytes plane1)
    32x32 = 16 tiles = 256 bytes

    Tile layout (row-major as expected by hal_demo.asm):
    $00 $01 $02 $03
    $04 $05 $06 $07
    $08 $09 $0A $0B
    $0C $0D $0E $0F
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    if img.size != (32, 32):
        img = img.resize((32, 32), Image.LANCZOS)

    img = auto_contrast(img)
    palette_rgb = get_palette_rgb(palette)
    pixels = np.array(img)
    chr_data = bytearray()

    # Process 4x4 grid of 8x8 tiles in row-major order
    for tile_row in range(4):
        for tile_col in range(4):
            tile_x = tile_col * 8
            tile_y = tile_row * 8
            plane0, plane1 = [], []

            for row in range(8):
                p0_byte, p1_byte = 0, 0
                for col in range(8):
                    r, g, b, a = pixels[tile_y + row, tile_x + col]
                    if is_transparent_pixel(r, g, b, a, bg_color):
                        color_idx = 0
                    else:
                        color_idx = find_closest_color(r, g, b, palette_rgb, exclude_zero=True)
                    p0_byte |= ((color_idx & 1) << (7 - col))
                    p1_byte |= (((color_idx >> 1) & 1) << (7 - col))
                plane0.append(p0_byte)
                plane1.append(p1_byte)

            chr_data.extend(plane0)
            chr_data.extend(plane1)

    return chr_data


def image_to_chr_8x8(img, palette, bg_color=None):
    """Convert an 8x8 image to NES CHR format."""
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    if img.size != (8, 8):
        img = img.resize((8, 8), Image.NEAREST)

    img = auto_contrast(img)
    palette_rgb = get_palette_rgb(palette)
    pixels = np.array(img)
    plane0, plane1 = [], []

    for row in range(8):
        p0_byte, p1_byte = 0, 0
        for col in range(8):
            r, g, b, a = pixels[row, col]
            if is_transparent_pixel(r, g, b, a, bg_color):
                color_idx = 0
            else:
                color_idx = find_closest_color(r, g, b, palette_rgb, exclude_zero=True)
            p0_byte |= ((color_idx & 1) << (7 - col))
            p1_byte |= (((color_idx >> 1) & 1) << (7 - col))
        plane0.append(p0_byte)
        plane1.append(p1_byte)

    chr_data = bytearray()
    chr_data.extend(plane0)
    chr_data.extend(plane1)
    return chr_data


def verify_quadrant_content(img, bg_color=None):
    """Check each 8x8 quadrant has visible pixels."""
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    w, h = img.size
    pixels = np.array(img)

    quadrants = [
        ("TL", 0, 0),
        ("TR", w//2, 0),
        ("BL", 0, h//2),
        ("BR", w//2, h//2)
    ]

    empty = []
    for name, qx, qy in quadrants:
        has_content = False
        for y in range(qy, min(qy + h//2, h)):
            for x in range(qx, min(qx + w//2, w)):
                r, g, b, a = pixels[y, x]
                if not is_transparent_pixel(r, g, b, a, bg_color):
                    has_content = True
                    break
            if has_content:
                break
        if not has_content:
            empty.append(name)

    return empty


def pad_to_square(img, bg_color=None):
    """Pad an image to square dimensions, preserving aspect ratio.

    Centers the content in a square canvas with transparent background.
    """
    w, h = img.size
    if w == h:
        return img

    # Make square with the larger dimension
    size = max(w, h)

    # Create square canvas (transparent)
    if bg_color:
        square = Image.new('RGBA', (size, size), (*bg_color, 0))
    else:
        square = Image.new('RGBA', (size, size), (0, 0, 0, 0))

    # Center the original image
    x_offset = (size - w) // 2
    y_offset = (size - h) // 2
    square.paste(img, (x_offset, y_offset))

    return square


def save_debug_sprite(img, path, show_grid=True):
    """Save sprite with tile grid overlay for debugging."""
    debug = img.copy().convert('RGBA')

    if show_grid and img.width >= 8 and img.height >= 8:
        draw = ImageDraw.Draw(debug)
        for x in range(0, img.width + 1, 8):
            draw.line([(x, 0), (x, img.height - 1)], fill=(255, 0, 0, 200), width=1)
        for y in range(0, img.height + 1, 8):
            draw.line([(0, y), (img.width - 1, y)], fill=(255, 0, 0, 200), width=1)

    debug.save(path)


def create_procedural_nes_background(palette):
    """Create a procedural NES-style background designed for minimal tiles.

    NES games like Mega Man, Metroid, and Castlevania use clever tile reuse:
    - Repeating patterns (grids, bricks, pipes)
    - Gradient strips (sky to horizon)
    - Simple geometric shapes

    This creates a synthwave/cyberpunk grid that fits NES constraints naturally.

    Returns: (nametable_data, chr_data)
    """
    palette_rgb = get_palette_rgb(palette)

    # =========================================================================
    # DEFINE TILE SET (Only ~20-30 unique tiles needed for good background)
    # =========================================================================

    # Helper to create an 8x8 indexed tile
    def make_tile(pattern):
        """pattern is 8 strings of 8 chars, each char is '0'-'3' for palette index"""
        tile = np.zeros((8, 8), dtype=np.uint8)
        for y, row in enumerate(pattern):
            for x, c in enumerate(row):
                tile[y, x] = int(c)
        return tile

    # Tile definitions (0=black, 1=dark, 2=mid, 3=bright)
    tiles = {}

    # Tile 0: Solid black (empty space)
    tiles['black'] = make_tile([
        '00000000',
        '00000000',
        '00000000',
        '00000000',
        '00000000',
        '00000000',
        '00000000',
        '00000000',
    ])

    # Tile 1: Horizontal grid line (top)
    tiles['grid_h_top'] = make_tile([
        '33333333',
        '00000000',
        '00000000',
        '00000000',
        '00000000',
        '00000000',
        '00000000',
        '00000000',
    ])

    # Tile 2: Vertical grid line (left)
    tiles['grid_v_left'] = make_tile([
        '30000000',
        '30000000',
        '30000000',
        '30000000',
        '30000000',
        '30000000',
        '30000000',
        '30000000',
    ])

    # Tile 3: Grid intersection
    tiles['grid_cross'] = make_tile([
        '33333333',
        '30000000',
        '30000000',
        '30000000',
        '30000000',
        '30000000',
        '30000000',
        '30000000',
    ])

    # Tile 4: Solid dark (dark fill)
    tiles['dark'] = make_tile([
        '11111111',
        '11111111',
        '11111111',
        '11111111',
        '11111111',
        '11111111',
        '11111111',
        '11111111',
    ])

    # Tile 5: Stars (small dots for sky)
    tiles['stars1'] = make_tile([
        '00000000',
        '00300000',
        '00000000',
        '00000030',
        '00000000',
        '03000000',
        '00000000',
        '00000000',
    ])

    # Tile 6: Stars variant
    tiles['stars2'] = make_tile([
        '00000300',
        '00000000',
        '00030000',
        '00000000',
        '00000000',
        '00000030',
        '00000000',
        '00300000',
    ])

    # Tile 7: Gradient top (mostly black with hint)
    tiles['grad_top'] = make_tile([
        '00000000',
        '00000000',
        '00000000',
        '00000000',
        '00000000',
        '00000000',
        '10000001',
        '11000011',
    ])

    # Tile 8: Gradient middle
    tiles['grad_mid'] = make_tile([
        '11100111',
        '11111111',
        '11111111',
        '22222222',
        '22222222',
        '22222222',
        '22222222',
        '22222222',
    ])

    # Tile 9: Building top
    tiles['building_top'] = make_tile([
        '00000000',
        '00000000',
        '11111111',
        '11111111',
        '11111111',
        '11111111',
        '11111111',
        '11111111',
    ])

    # Tile 10: Building middle with window
    tiles['building_win'] = make_tile([
        '11111111',
        '11233211',
        '11233211',
        '11111111',
        '11111111',
        '11233211',
        '11233211',
        '11111111',
    ])

    # Tile 11: Building solid
    tiles['building_solid'] = make_tile([
        '11111111',
        '11111111',
        '11111111',
        '11111111',
        '11111111',
        '11111111',
        '11111111',
        '11111111',
    ])

    # Tile 12: Neon line horizontal
    tiles['neon_h'] = make_tile([
        '00000000',
        '00000000',
        '00000000',
        '22222222',
        '33333333',
        '22222222',
        '00000000',
        '00000000',
    ])

    # Tile 13: Ground/platform top
    tiles['ground_top'] = make_tile([
        '33333333',
        '22222222',
        '11111111',
        '11111111',
        '11111111',
        '11111111',
        '11111111',
        '11111111',
    ])

    # Tile 14: Ground solid
    tiles['ground'] = make_tile([
        '11111111',
        '11111111',
        '11111111',
        '11111111',
        '11111111',
        '11111111',
        '11111111',
        '11111111',
    ])

    # Tile 15: Perspective grid line (for synthwave sun effect)
    tiles['sun_line'] = make_tile([
        '00022000',
        '00022000',
        '00022000',
        '00022000',
        '00022000',
        '00022000',
        '00022000',
        '00022000',
    ])

    # Tile 16: Sun center
    tiles['sun_center'] = make_tile([
        '00222200',
        '02333320',
        '23333332',
        '23333332',
        '23333332',
        '23333332',
        '02333320',
        '00222200',
    ])

    # Tile 17: Sun edge left
    tiles['sun_left'] = make_tile([
        '00000022',
        '00000233',
        '00002333',
        '00023333',
        '00023333',
        '00002333',
        '00000233',
        '00000022',
    ])

    # Tile 18: Sun edge right
    tiles['sun_right'] = make_tile([
        '22000000',
        '33200000',
        '33320000',
        '33332000',
        '33332000',
        '33320000',
        '33200000',
        '22000000',
    ])

    # Convert tiles to CHR format
    def tile_to_chr(tile_indices):
        plane0, plane1 = [], []
        for row in range(8):
            p0_byte, p1_byte = 0, 0
            for col in range(8):
                idx = tile_indices[row, col]
                p0_byte |= ((idx & 1) << (7 - col))
                p1_byte |= (((idx >> 1) & 1) << (7 - col))
            plane0.append(p0_byte)
            plane1.append(p1_byte)
        return bytes(plane0 + plane1)

    # Build CHR data from tile definitions
    tile_names = list(tiles.keys())
    chr_data = bytearray()
    tile_index_map = {}

    for i, name in enumerate(tile_names):
        tile_index_map[name] = i
        chr_data.extend(tile_to_chr(tiles[name]))

    # =========================================================================
    # BUILD NAMETABLE (32x30 grid = 960 bytes)
    # Layout: Sky (rows 0-8), Sun (rows 9-14), Grid floor (rows 15-29)
    # =========================================================================

    nametable = bytearray(960)

    for ty in range(30):
        for tx in range(32):
            idx = ty * 32 + tx

            if ty < 6:
                # Sky with stars
                if (tx + ty) % 7 == 0:
                    nametable[idx] = tile_index_map['stars1']
                elif (tx + ty * 2) % 11 == 0:
                    nametable[idx] = tile_index_map['stars2']
                else:
                    nametable[idx] = tile_index_map['black']

            elif ty < 9:
                # Gradient to horizon
                nametable[idx] = tile_index_map['grad_top']

            elif ty == 9:
                # Sun row (center)
                if tx == 14:
                    nametable[idx] = tile_index_map['sun_left']
                elif tx == 15 or tx == 16:
                    nametable[idx] = tile_index_map['sun_center']
                elif tx == 17:
                    nametable[idx] = tile_index_map['sun_right']
                else:
                    nametable[idx] = tile_index_map['grad_mid']

            elif ty < 12:
                # Below sun - neon horizon line
                if ty == 10:
                    nametable[idx] = tile_index_map['neon_h']
                else:
                    nametable[idx] = tile_index_map['dark']

            else:
                # Grid floor (synthwave perspective grid)
                # Grid lines every 4 tiles
                is_grid_v = (tx % 4 == 0)
                is_grid_h = (ty % 3 == 0)

                if is_grid_v and is_grid_h:
                    nametable[idx] = tile_index_map['grid_cross']
                elif is_grid_v:
                    nametable[idx] = tile_index_map['grid_v_left']
                elif is_grid_h:
                    nametable[idx] = tile_index_map['grid_h_top']
                else:
                    nametable[idx] = tile_index_map['black']

    # Attribute table (64 bytes) - all palette 0
    attr_table = bytearray(64)

    unique_count = len(tiles)
    print(f"      Procedural tiles: {unique_count}/256 (designed for NES)")
    print(f"      Layout: Sky + Sun + Synthwave Grid")

    return bytes(nametable) + bytes(attr_table), bytes(chr_data)


def create_background_data(img_path, palette):
    """Create NES background data: CHR tiles + nametable.

    NES Hardware Constraints (per nesdev.org):
    - Screen: 256x240 pixels = 32x30 tiles = 960 tiles total
    - Pattern table: 256 unique 8x8 tiles maximum (4KB)
    - Nametable: 960 bytes (tile indices) + 64 bytes (attribute table) = 1024 bytes
    - CHR format: 2bpp planar (16 bytes per 8x8 tile)

    Tile Reduction Strategy (NO BLUR):
    1. Posterize - Reduce color levels before quantization
    2. Block average - Average each 8x8 tile region for uniformity
    3. Similarity matching - Match tiles within a threshold, not just exact
    4. Flip detection - Reuse flipped versions of existing tiles

    Returns: (nametable_data, chr_data)
    """
    if not img_path.exists():
        print("      WARNING: Background not found, using procedural")
        return create_procedural_nes_background(palette)

    img = Image.open(img_path).convert('RGB')
    w, h = img.size

    # Crop text labels (AI often adds text at top/bottom)
    img = img.crop((0, int(h * 0.1), w, int(h * 0.95)))

    # Resize to NES screen dimensions: 256x240
    img = img.resize((256, 240), Image.LANCZOS)

    # =========================================================================
    # NES TILE REDUCTION: Posterize + Block Average (NO BLUR)
    # AI images have too much gradient detail. These techniques reduce unique
    # tiles while keeping sharp edges (unlike blur which makes everything muddy).
    # =========================================================================

    # Step 1: Posterize - reduce to fewer color levels per channel
    # This reduces subtle gradients that create many unique tiles
    posterize_levels = 8  # 8 levels per channel = 512 possible colors
    pixels = np.array(img, dtype=np.float32)
    pixels = np.floor(pixels / (256 / posterize_levels)) * (256 / posterize_levels)
    pixels = np.clip(pixels, 0, 255).astype(np.uint8)

    # Step 2: Block-level color averaging
    # For each 8x8 tile region, find the dominant colors and simplify
    # This creates more uniform tiles that will deduplicate better
    for ty in range(30):
        for tx in range(32):
            y_start, x_start = ty * 8, tx * 8
            block = pixels[y_start:y_start+8, x_start:x_start+8].reshape(-1, 3)

            # Find unique colors in this block
            unique_colors = np.unique(block, axis=0)

            # If more than 4 colors (NES limit per tile), reduce them
            if len(unique_colors) > 4:
                # Simple k-means-style reduction: cluster to 4 colors
                from scipy.cluster.vq import kmeans2
                try:
                    centroids, labels = kmeans2(block.astype(float), 4, minit='++')
                    centroids = np.clip(centroids, 0, 255).astype(np.uint8)
                    new_block = centroids[labels].reshape(8, 8, 3)
                    pixels[y_start:y_start+8, x_start:x_start+8] = new_block
                except:
                    # If clustering fails, just posterize more aggressively
                    block_post = np.floor(block / 64) * 64
                    pixels[y_start:y_start+8, x_start:x_start+8] = block_post.reshape(8, 8, 3)

    img = Image.fromarray(pixels, 'RGB')

    palette_rgb = get_palette_rgb(palette)

    # Quantize to 4 colors
    pixels = np.array(img)
    indexed = np.zeros((240, 256), dtype=np.uint8)

    for y in range(240):
        for x in range(256):
            r, g, b = int(pixels[y, x, 0]), int(pixels[y, x, 1]), int(pixels[y, x, 2])
            best_idx = 0
            best_dist = float('inf')
            for i, (pr, pg, pb) in enumerate(palette_rgb):
                dist = (r - pr)**2 + (g - pg)**2 + (b - pb)**2
                if dist < best_dist:
                    best_dist = dist
                    best_idx = i
            indexed[y, x] = best_idx

    # =========================================================================
    # TILE GENERATION WITH SIMILARITY + FLIP OPTIMIZATION
    # Strategy:
    # 1. Exact match - reuse identical tiles
    # 2. Similarity match - if tiles differ by only a few pixels, reuse
    # 3. Flip match - check H/V/HV flipped versions
    # This is essential for fitting AI images into 256 tile limit.
    # =========================================================================

    def tile_to_chr(tile_indices):
        """Convert 8x8 tile (indices 0-3) to NES CHR format (16 bytes)."""
        plane0, plane1 = [], []
        for row in range(8):
            p0_byte, p1_byte = 0, 0
            for col in range(8):
                idx = tile_indices[row, col]
                p0_byte |= ((idx & 1) << (7 - col))
                p1_byte |= (((idx >> 1) & 1) << (7 - col))
            plane0.append(p0_byte)
            plane1.append(p1_byte)
        return bytes(plane0 + plane1)

    def flip_tile_h(tile):
        """Flip tile horizontally."""
        return np.fliplr(tile)

    def flip_tile_v(tile):
        """Flip tile vertically."""
        return np.flipud(tile)

    def flip_tile_hv(tile):
        """Flip tile both horizontally and vertically (180 degree rotation)."""
        return np.flipud(np.fliplr(tile))

    def tiles_are_similar(tile1, tile2, threshold=8):
        """Check if two tiles are similar enough to merge.

        threshold = max number of different pixels allowed (out of 64).
        8 pixels = 12.5% difference tolerance.
        """
        diff = np.sum(tile1 != tile2)
        return diff <= threshold

    def find_similar_tile(tile_indices, unique_tile_data, threshold=8):
        """Find a similar tile in the existing set.

        Returns tile index if found, None otherwise.
        """
        for existing_idx, existing_tile in unique_tile_data.items():
            if tiles_are_similar(tile_indices, existing_tile, threshold):
                return existing_idx
            # Also check flipped versions
            if tiles_are_similar(tile_indices, flip_tile_h(existing_tile), threshold):
                return existing_idx
            if tiles_are_similar(tile_indices, flip_tile_v(existing_tile), threshold):
                return existing_idx
            if tiles_are_similar(tile_indices, flip_tile_hv(existing_tile), threshold):
                return existing_idx
        return None

    # Collect all tiles with deduplication, similarity matching, AND flip detection
    unique_tiles = {}  # chr_bytes -> tile_index
    unique_tile_data = {}  # tile_index -> tile_indices (for similarity checking)
    tile_map = {}  # (ty, tx) -> tile_index
    chr_data = bytearray()

    # Stats for reporting
    exact_reuse = 0
    similar_reuse = 0
    flip_reuse = 0

    # Similarity threshold - start tight, loosen if we overflow
    similarity_threshold = 4  # Start with 4 different pixels allowed

    for ty in range(30):
        for tx in range(32):
            tile_y, tile_x = ty * 8, tx * 8
            tile_indices = indexed[tile_y:tile_y+8, tile_x:tile_x+8].copy()
            tile_chr = tile_to_chr(tile_indices)

            # First check: exact match
            if tile_chr in unique_tiles:
                tile_map[(ty, tx)] = unique_tiles[tile_chr]
                exact_reuse += 1
                continue

            # Second check: flipped exact matches
            found_flip = False
            for flip_func, name in [(flip_tile_h, 'h'), (flip_tile_v, 'v'), (flip_tile_hv, 'hv')]:
                variant = flip_func(tile_indices)
                variant_chr = tile_to_chr(variant)
                if variant_chr in unique_tiles:
                    # NES BG tiles don't have flip flags, but we found a match
                    # Store the original tile if we have room
                    if len(unique_tiles) < 256:
                        idx = len(unique_tiles)
                        unique_tiles[tile_chr] = idx
                        unique_tile_data[idx] = tile_indices
                        tile_map[(ty, tx)] = idx
                        chr_data.extend(tile_chr)
                        flip_reuse += 1
                    else:
                        tile_map[(ty, tx)] = unique_tiles[variant_chr]
                    found_flip = True
                    break

            if found_flip:
                continue

            # Third check: similarity match (only if approaching limit)
            if len(unique_tiles) > 200:
                similar_idx = find_similar_tile(tile_indices, unique_tile_data, similarity_threshold)
                if similar_idx is not None:
                    tile_map[(ty, tx)] = similar_idx
                    similar_reuse += 1
                    continue

            # No match found - add as new tile
            if len(unique_tiles) < 256:
                idx = len(unique_tiles)
                unique_tiles[tile_chr] = idx
                unique_tile_data[idx] = tile_indices
                tile_map[(ty, tx)] = idx
                chr_data.extend(tile_chr)
            else:
                # Over 256 - try harder with looser similarity
                similar_idx = find_similar_tile(tile_indices, unique_tile_data, threshold=16)
                if similar_idx is not None:
                    tile_map[(ty, tx)] = similar_idx
                    similar_reuse += 1
                else:
                    # Last resort - map to most common tile
                    tile_map[(ty, tx)] = 0

    # Build nametable (960 bytes) - THIS IS THE KEY PART
    nametable = bytearray(960)
    for ty in range(30):
        for tx in range(32):
            nametable[ty * 32 + tx] = tile_map[(ty, tx)]

    # Attribute table (64 bytes) - use palette 0 everywhere
    attr_table = bytearray(64)

    unique_count = len(unique_tiles)
    print(f"      Unique tiles: {unique_count}/256 (NES limit)")
    if unique_count >= 256:
        print(f"      WARNING: Tile overflow - some tiles may be approximated")
    print(f"      Tile reuse: {exact_reuse} exact, {flip_reuse} flip, {similar_reuse} similar")
    print(f"      Total reuse: {960 - unique_count} positions ({100*(960-unique_count)/960:.1f}%)")

    return bytes(nametable) + bytes(attr_table), bytes(chr_data)


def _process_ai_background(indexed, palette_rgb):
    """Process an already-indexed background image into CHR/NAM."""

    def tile_to_chr(tile_indices):
        plane0, plane1 = [], []
        for row in range(8):
            p0_byte, p1_byte = 0, 0
            for col in range(8):
                idx = tile_indices[row, col]
                p0_byte |= ((idx & 1) << (7 - col))
                p1_byte |= (((idx >> 1) & 1) << (7 - col))
            plane0.append(p0_byte)
            plane1.append(p1_byte)
        return bytes(plane0 + plane1)

    # Deduplicate tiles
    unique_tiles = {}
    tile_map = {}
    chr_data = bytearray()

    for ty in range(30):
        for tx in range(32):
            tile = indexed[ty*8:(ty+1)*8, tx*8:(tx+1)*8]
            tile_bytes = tile.tobytes()
            tile_chr = tile_to_chr(tile)

            if tile_chr in unique_tiles:
                tile_map[(ty, tx)] = unique_tiles[tile_chr]
            else:
                idx = len(unique_tiles)
                unique_tiles[tile_chr] = idx
                tile_map[(ty, tx)] = idx
                chr_data.extend(tile_chr)

    # Build nametable
    nametable = bytearray(960)
    for ty in range(30):
        for tx in range(32):
            nametable[ty * 32 + tx] = tile_map[(ty, tx)]

    attr_table = bytearray(64)

    print(f"      Final tiles: {len(unique_tiles)}/256")
    return bytes(nametable) + bytes(attr_table), bytes(chr_data)


# =============================================================================
# Main Processing
# =============================================================================

def main():
    base_dir = Path(__file__).parent
    output_dir = base_dir / 'assets' / 'processed'
    debug_dir = output_dir / 'debug'
    output_dir.mkdir(parents=True, exist_ok=True)
    debug_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  HAL Demo - AI Asset Builder v5.0")
    print("  Multi-AI Consensus + Smart Background Detection")
    print("=" * 60)

    gfx_dir = base_dir.parent.parent / 'gfx' / 'ai_output'
    sprite_chr = bytearray()

    # === PLAYER SPRITE ===
    print("\n[1/4] Processing player sprite...")
    player_path = gfx_dir / 'player_rad_90s.png'
    if player_path.exists():
        player_img = Image.open(player_path).convert('RGBA')

        print("      Using consensus detection...")

        # Use smart background detection
        bg_color = detect_background_smart(player_img, tolerance=20)
        if bg_color:
            print(f"      Background: RGB{bg_color}")
        else:
            print("      Background: transparent/complex")

        # Use consensus to find sprite
        bbox = detect_sprite_consensus(
            player_img,
            sprite_type="idle character sprite",
            models=['gemini-fast', 'openai-large', 'gemini'],
            min_agreement=2,
            iou_threshold=0.4
        )

        if bbox:
            # Extract the region
            x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']
            img_w, img_h = player_img.size
            x = max(0, min(x, img_w - 1))
            y = max(0, min(y, img_h - 1))
            w = min(w, img_w - x)
            h = min(h, img_h - y)

            player_region = player_img.crop((x, y, x + w, y + h))
            player_region.save(debug_dir / 'player_region.png')

            # Get content mask for precise extraction
            content_mask = get_content_mask(player_region, tolerance=25)
            content_mask.save(debug_dir / 'player_mask.png')

            # Pad to square to preserve aspect ratio, then scale to 32x32
            player_square = pad_to_square(player_region, bg_color)
            player_32 = player_square.resize((32, 32), Image.LANCZOS)
        else:
            print("      Consensus failed, using fallback...")
            # Fallback to full content mask approach
            content_mask = get_content_mask(player_img, tolerance=25)
            mask_arr = np.array(content_mask)

            rows = np.any(mask_arr > 0, axis=1)
            cols = np.any(mask_arr > 0, axis=0)

            if np.any(rows) and np.any(cols):
                y_min, y_max = np.where(rows)[0][[0, -1]]
                x_min, x_max = np.where(cols)[0][[0, -1]]
                player_region = player_img.crop((x_min, y_min, x_max + 1, y_max + 1))
                # Pad to square to preserve aspect ratio
                player_square = pad_to_square(player_region, bg_color)
                player_32 = player_square.resize((32, 32), Image.LANCZOS)
            else:
                player_32 = player_img.resize((32, 32), Image.LANCZOS)

        # Extract palette using AI
        print("      Extracting palette...")
        palette = extract_palette_ai(player_32, num_colors=4)
        if not palette:
            palette = [0x0F, 0x24, 0x2C, 0x30]  # Default synthwave
            print(f"      Using default: {', '.join(f'${c:02X}' for c in palette)}")

        # Save outputs
        player_32.save(output_dir / 'player.png')
        save_debug_sprite(player_32, debug_dir / 'player_grid.png', show_grid=True)

        # Convert to CHR: 32x32 = 16 tiles ($00-$0F)
        player_chr = image_to_chr_32x32(player_32, palette, bg_color=bg_color)
        sprite_chr.extend(player_chr)
        player_palette = palette  # Track for manifest
        print(f"      Player: 32x32 -> 16 tiles, {len(player_chr)} bytes")
    else:
        print("      WARNING: Player file not found")
        sprite_chr.extend([0] * 256)  # 16 tiles * 16 bytes each
        player_palette = [0x0F, 0x24, 0x2C, 0x30]  # Default

    # === ENEMY SPRITE ===
    print("\n[2/4] Processing enemy sprite...")
    enemy_path = gfx_dir / 'enemies_synthwave.png'
    if enemy_path.exists():
        enemy_img = Image.open(enemy_path).convert('RGBA')

        print("      Using consensus detection...")

        bg_color = detect_background_smart(enemy_img, tolerance=20)
        if bg_color:
            print(f"      Background: RGB{bg_color}")
        else:
            print("      Background: transparent/complex")

        bbox = detect_sprite_consensus(
            enemy_img,
            sprite_type="enemy creature or skull sprite",
            models=['gemini-fast', 'openai-large', 'gemini'],
            min_agreement=2,
            iou_threshold=0.4
        )

        if bbox:
            x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']
            img_w, img_h = enemy_img.size
            x = max(0, min(x, img_w - 1))
            y = max(0, min(y, img_h - 1))
            w = min(w, img_w - x)
            h = min(h, img_h - y)

            enemy_region = enemy_img.crop((x, y, x + w, y + h))
            enemy_region.save(debug_dir / 'enemy_region.png')

            # Pad to square to preserve aspect ratio, then scale to 32x32
            enemy_square = pad_to_square(enemy_region, bg_color)
            enemy_32 = enemy_square.resize((32, 32), Image.LANCZOS)
        else:
            print("      Consensus failed, using fallback...")
            content_mask = get_content_mask(enemy_img, tolerance=25)
            mask_arr = np.array(content_mask)

            rows = np.any(mask_arr > 0, axis=1)
            cols = np.any(mask_arr > 0, axis=0)

            if np.any(rows) and np.any(cols):
                y_min, y_max = np.where(rows)[0][[0, -1]]
                x_min, x_max = np.where(cols)[0][[0, -1]]
                enemy_region = enemy_img.crop((x_min, y_min, x_max + 1, y_max + 1))
                # Pad to square to preserve aspect ratio
                enemy_square = pad_to_square(enemy_region, bg_color)
                enemy_32 = enemy_square.resize((32, 32), Image.LANCZOS)
            else:
                enemy_32 = enemy_img.resize((32, 32), Image.LANCZOS)

        # Extract palette
        print("      Extracting palette...")
        palette = extract_palette_ai(enemy_32, num_colors=4)
        if not palette:
            palette = [0x0F, 0x24, 0x2C, 0x2A]  # Magenta, Cyan, Green
            print(f"      Using default: {', '.join(f'${c:02X}' for c in palette)}")

        enemy_32.save(output_dir / 'enemy.png')
        save_debug_sprite(enemy_32, debug_dir / 'enemy_grid.png', show_grid=True)

        # Convert to CHR: 32x32 = 16 tiles ($10-$1F)
        enemy_chr = image_to_chr_32x32(enemy_32, palette, bg_color=bg_color)
        sprite_chr.extend(enemy_chr)
        enemy_palette = palette  # Track for manifest
        print(f"      Enemy: 32x32 -> 16 tiles, {len(enemy_chr)} bytes")
    else:
        print("      WARNING: Enemy file not found")
        sprite_chr.extend([0] * 256)  # 16 tiles * 16 bytes each
        enemy_palette = [0x0F, 0x24, 0x2C, 0x30]  # Default

    # === BULLET SPRITE ===
    # ASM expects TILE_BULLET_START=$20 with 16 tiles, using center 2x2 (tiles $05,$06,$09,$0A)
    # We need to create a 32x32 image where the bullet is in the center 16x16 region
    print("\n[3/4] Processing projectile sprite...")
    items_path = gfx_dir / 'items_projectiles.png'
    if items_path.exists():
        items_img = Image.open(items_path).convert('RGBA')

        print("      Using consensus for projectile detection...")

        bg_color = detect_background_smart(items_img, tolerance=20)
        if bg_color:
            print(f"      Background: RGB{bg_color}")

        bbox = detect_sprite_consensus(
            items_img,
            sprite_type="small projectile or bullet sprite",
            models=['gemini-fast', 'openai-large'],
            min_agreement=1,
            iou_threshold=0.3
        )

        if bbox and bbox['width'] < 200 and bbox['height'] < 200:
            x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']
            bullet_region = items_img.crop((x, y, x + w, y + h))
            # Scale detected region to 16x16 (center content)
            bullet_16 = bullet_region.resize((16, 16), Image.LANCZOS)
        else:
            print("      Using fallback for projectile...")
            # Create simple projectile in center
            bullet_16 = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
            # Draw a small energy ball in center
            for by in range(5, 11):
                for bx in range(5, 11):
                    dist = ((bx - 8)**2 + (by - 8)**2) ** 0.5
                    if dist < 3:
                        bullet_16.putpixel((bx, by), (255, 100, 200, 255))
                    elif dist < 4:
                        bullet_16.putpixel((bx, by), (200, 50, 150, 255))

        # Create 32x32 canvas with bullet centered
        # Tiles $05,$06,$09,$0A are at pixel positions (8,8)-(24,24)
        bullet_32 = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
        bullet_32.paste(bullet_16, (8, 8))  # Center the 16x16 in the 32x32

        bullet_palette = [0x0F, 0x24, 0x2C, 0x30]
        print(f"      Palette: {', '.join(f'${c:02X}' for c in bullet_palette)}")

        bullet_32.save(output_dir / 'bullet.png')
        save_debug_sprite(bullet_32, debug_dir / 'bullet_grid.png', show_grid=True)

        # Convert to CHR: 32x32 = 16 tiles ($20-$2F)
        bullet_chr = image_to_chr_32x32(bullet_32, bullet_palette, bg_color=bg_color)
        sprite_chr.extend(bullet_chr)
        print(f"      Bullet: 32x32 -> 16 tiles, {len(bullet_chr)} bytes (content in center)")
    else:
        print("      WARNING: Items file not found")
        sprite_chr.extend([0] * 256)  # 16 tiles * 16 bytes each
        bullet_palette = [0x0F, 0x24, 0x2C, 0x30]  # Default

    # Pad sprite CHR to 8KB
    while len(sprite_chr) < 8192:
        sprite_chr.append(0)
    sprite_chr = sprite_chr[:8192]

    # === BACKGROUND ===
    print("\n[4/4] Processing background tiles...")
    bg_path = gfx_dir / 'background_cyberpunk.png'
    if bg_path.exists():
        bg_img = Image.open(bg_path).convert('RGBA')
        print("      Extracting background palette...")
        palette = extract_palette_ai(bg_img, num_colors=4)
        if palette:
            print(f"      Palette: {', '.join(f'${c:02X}' for c in palette)}")
        else:
            palette = [0x0F, 0x03, 0x1C, 0x2C]
            print(f"      Using default: {', '.join(f'${c:02X}' for c in palette)}")

        # Generate both nametable and CHR data
        bg_nam, bg_chr = create_background_data(bg_path, palette)
        bg_palette = palette  # Track for manifest
    else:
        print("      WARNING: Background not found")
        bg_nam = bytearray([0] * 1024)
        bg_chr = bytearray([0] * 4096)
        bg_palette = [0x0F, 0x03, 0x1C, 0x2C]  # Default

    # Pad CHR to 8KB
    bg_chr = bytearray(bg_chr)
    while len(bg_chr) < 8192:
        bg_chr.append(0)
    bg_chr = bytes(bg_chr[:8192])
    print(f"      Background CHR: {len(bg_chr)} bytes")
    print(f"      Background NAM: {len(bg_nam)} bytes (960 NT + 64 AT)")

    # Write output files
    with open(output_dir / 'sprites.chr', 'wb') as f:
        f.write(sprite_chr)
    print(f"\n      Wrote: sprites.chr ({len(sprite_chr)} bytes)")

    with open(output_dir / 'background.chr', 'wb') as f:
        f.write(bg_chr)
    print(f"      Wrote: background.chr ({len(bg_chr)} bytes)")

    with open(output_dir / 'background.nam', 'wb') as f:
        f.write(bg_nam)
    print(f"      Wrote: background.nam ({len(bg_nam)} bytes)")

    # Write manifest with palette info
    manifest = {
        'version': '5.2',
        'player': {
            'file': 'player.png',
            'size': '32x32',
            'tiles': '$00-$0F (16 tiles)',
            'palette': player_palette,
        },
        'enemy': {
            'file': 'enemy.png',
            'size': '32x32',
            'tiles': '$10-$1F (16 tiles)',
            'palette': enemy_palette,
        },
        'bullet': {
            'file': 'bullet.png',
            'size': '32x32 (content centered in 16x16)',
            'tiles': '$20-$2F (16 tiles, uses center $25,$26,$29,$2A)',
            'palette': bullet_palette,
        },
        'background': {
            'file': 'background.chr',
            'palette': bg_palette,
        },
        'features': [
            'multi-ai-consensus',
            'floodfill-background',
            'ai-palette-extraction',
            '32x32-metasprites',
        ]
    }

    import json
    with open(output_dir / 'manifest.json', 'w') as f:
        json.dump(manifest, f, indent=2)

    # Generate ASM include file with palette data
    asm_palette = f"""; =============================================================================
; Auto-generated palette data from build_ai_assets.py v5.2
; DO NOT EDIT - This file is regenerated on each asset build
; =============================================================================

; Background palettes
BG_PALETTE_0:
    .byte ${bg_palette[0]:02X}, ${bg_palette[1]:02X}, ${bg_palette[2]:02X}, ${bg_palette[3]:02X}
BG_PALETTE_1:
    .byte $0F, $01, $11, $21  ; Blue ramp
BG_PALETTE_2:
    .byte $0F, $06, $16, $26  ; Red ramp
BG_PALETTE_3:
    .byte $0F, $0A, $1A, $2A  ; Green ramp

; Sprite palettes
SPR_PALETTE_0:  ; Player
    .byte ${player_palette[0]:02X}, ${player_palette[1]:02X}, ${player_palette[2]:02X}, ${player_palette[3]:02X}
SPR_PALETTE_1:  ; Enemy
    .byte ${enemy_palette[0]:02X}, ${enemy_palette[1]:02X}, ${enemy_palette[2]:02X}, ${enemy_palette[3]:02X}
SPR_PALETTE_2:  ; Bullet
    .byte ${bullet_palette[0]:02X}, ${bullet_palette[1]:02X}, ${bullet_palette[2]:02X}, ${bullet_palette[3]:02X}
SPR_PALETTE_3:  ; Effects
    .byte $0F, $19, $29, $39
"""
    with open(output_dir / 'palettes.inc', 'w') as f:
        f.write(asm_palette)
    print(f"      Wrote: palettes.inc")

    print("\n" + "=" * 60)
    print("  Asset Build Complete!")
    print("=" * 60)
    print(f"\n  CHR Layout (sprites.chr):")
    print(f"    $00-$0F: Player 32x32 metasprite (16 tiles)")
    print(f"    $10-$1F: Enemy 32x32 metasprite (16 tiles)")
    print(f"    $20-$2F: Bullet (16 tiles, center 4 used)")
    print(f"\n  Palettes Used:")
    print(f"    Player:  {', '.join(f'${c:02X}' for c in player_palette)}")
    print(f"    Enemy:   {', '.join(f'${c:02X}' for c in enemy_palette)}")
    print(f"    Bullet:  {', '.join(f'${c:02X}' for c in bullet_palette)}")
    print(f"    BG:      {', '.join(f'${c:02X}' for c in bg_palette)}")
    print(f"\n  Debug images saved to: {debug_dir}")


if __name__ == '__main__':
    main()
