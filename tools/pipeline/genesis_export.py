"""
Genesis/SGDK Export Module - VDP-Ready Asset Generation.

This module provides comprehensive export functions for Sega Genesis/Mega Drive
game development using SGDK (Sega Genesis Development Kit). It handles the
conversion of standard image assets into hardware-specific formats that can be
directly loaded into the Genesis VDP (Video Display Processor).

Key Features:
    - Collision data export (AABB hitboxes/hurtboxes, per-pixel masks)
    - 4bpp tile export with deduplication (20-40% VRAM savings)
    - H/V flip mirror detection for additional tile optimization
    - VDP-ready formats: SAT entries, CRAM palettes, tilemap attributes
    - Cross-platform tile flip support (Genesis, NES, SNES, GameBoy)
    - Complete sprite bundle export (tiles + palette + SAT + header)

Genesis Hardware Reference:
    - VRAM: 64KB total
    - Tiles: 8x8 pixels, 4bpp (32 bytes each)
    - Sprites: Up to 80 total, 20 per scanline
    - Sprite sizes: 8x8 to 32x32 (1x1 to 4x4 tiles)
    - Palettes: 4 × 16 colors (64 total), 9-bit BGR
    - SAT entry: 8 bytes per sprite

VDP Memory Formats:
    - Tile data: 4bpp packed (2 pixels per byte, high nibble first)
    - CRAM palette: 0000BBB0GGG0RRR0 (9-bit BGR, word-aligned)
    - Tilemap entry: Priority|Palette|VFlip|HFlip|TileIndex (16-bit)
    - SAT entry: Y|Size/Link|Attributes|X (8 bytes, big-endian)

Usage Examples:
    >>> from pipeline.genesis_export import export_collision_header
    >>> export_collision_header(sprites, "out/collision_data.h")

    >>> from pipeline.genesis_export import export_genesis_tilemap_optimized
    >>> result = export_genesis_tilemap_optimized(img, "level.bin", use_mirroring=True)
    >>> print(f"Saved {result['stats'].savings_percent:.1f}% VRAM")

    >>> from pipeline.genesis_export import export_vdp_ready_sprite
    >>> export_vdp_ready_sprite(player_img, "out/player", palette_index=0)

Phase Implementation:
    - Phase 0.6: Basic Genesis 4bpp tile export
    - Phase 2.0.3: Tile deduplication with H/V flip mirror detection
    - Phase 2.1.2: VDP-ready export (SAT, CRAM, tilemap attributes)
"""

import os
from typing import List, Optional, Dict, TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime

if TYPE_CHECKING:
    from PIL import Image

from .platforms import SpriteInfo


# =============================================================================
# TILE MIRRORING DATA STRUCTURES (Phase 2.0.3)
# =============================================================================

@dataclass
class TileMatch:
    """
    Result of tile matching with flip state for VDP tilemap entries.

    When deduplicating tiles, a tile may match an existing unique tile
    either exactly or as a flipped variant. This class tracks which
    unique tile was matched and what flip transformation is needed.

    The flip flags directly correspond to VDP tilemap entry bits:
        - Bit 11: Horizontal flip
        - Bit 12: Vertical flip

    Attributes:
        index: Index of the matching tile in the unique tiles list.
        h_flip: True if tile needs horizontal flip to match.
        v_flip: True if tile needs vertical flip to match.

    Example:
        >>> match = TileMatch(index=5, h_flip=True, v_flip=False)
        >>> vdp_entry = match.to_vdp_flags(palette=2, priority=True)
    """
    index: int
    h_flip: bool
    v_flip: bool

    def to_vdp_flags(self, palette: int = 0, priority: bool = False) -> int:
        """
        Convert to Genesis VDP tilemap entry format.

        VDP Tilemap Entry (16-bit):
            Bit 15: Priority (0 = low, 1 = high)
            Bits 14-13: Palette index (0-3)
            Bit 12: Vertical flip
            Bit 11: Horizontal flip
            Bits 10-0: Tile index

        Returns:
            16-bit VDP tilemap entry
        """
        entry = self.index & 0x7FF  # 11-bit tile index
        if self.h_flip:
            entry |= (1 << 11)
        if self.v_flip:
            entry |= (1 << 12)
        entry |= (palette & 0x3) << 13
        if priority:
            entry |= (1 << 15)
        return entry


@dataclass
class TileOptimizationStats:
    """
    Statistics from tile deduplication with mirror optimization.

    Tracks how many tiles were deduplicated and how, allowing you to
    measure VRAM savings from the optimization process. Typical savings
    range from 20-40% on symmetric or repetitive tilesets.

    Attributes:
        total_tiles: Total tiles in the original image.
        unique_tiles: Number of unique tiles after deduplication.
        exact_matches: Tiles that matched another tile exactly.
        h_flip_matches: Tiles that matched with horizontal flip.
        v_flip_matches: Tiles that matched with vertical flip.
        hv_flip_matches: Tiles that matched with both flips (180° rotation).
    """
    total_tiles: int
    unique_tiles: int
    exact_matches: int
    h_flip_matches: int
    v_flip_matches: int
    hv_flip_matches: int

    @property
    def compression_ratio(self) -> float:
        """How many times smaller the unique tileset is."""
        return self.total_tiles / self.unique_tiles if self.unique_tiles > 0 else 1.0

    @property
    def savings_percent(self) -> float:
        """Percentage of tiles saved via deduplication."""
        if self.total_tiles == 0:
            return 0.0
        return 100.0 * (1.0 - self.unique_tiles / self.total_tiles)

    @property
    def mirror_savings(self) -> int:
        """Total tiles saved by mirror detection (not exact matches)."""
        return self.h_flip_matches + self.v_flip_matches + self.hv_flip_matches


# =============================================================================
# TILE FLIP OPERATIONS
# =============================================================================

def flip_tile_h(tile_bytes: bytes) -> bytes:
    """
    Flip a Genesis 4bpp tile horizontally.

    Genesis tile format: 8x8 pixels, 4bpp packed (2 pixels per byte).
    Each row is 4 bytes. High nibble is left pixel, low nibble is right pixel.

    To flip horizontally:
    1. Reverse byte order within each row
    2. Swap nibbles within each byte

    Args:
        tile_bytes: 32-byte Genesis tile data

    Returns:
        32-byte horizontally flipped tile
    """
    if len(tile_bytes) != 32:
        raise ValueError(f"Genesis tile must be 32 bytes, got {len(tile_bytes)}")

    result = bytearray(32)

    for row in range(8):
        row_start = row * 4
        for col in range(4):
            # Get byte from opposite side of row
            src_byte = tile_bytes[row_start + (3 - col)]
            # Swap nibbles (pixel order within byte)
            result[row_start + col] = ((src_byte & 0x0F) << 4) | ((src_byte >> 4) & 0x0F)

    return bytes(result)


def flip_tile_v(tile_bytes: bytes) -> bytes:
    """
    Flip a Genesis 4bpp tile vertically.

    To flip vertically, reverse the row order (rows are 4 bytes each).

    Args:
        tile_bytes: 32-byte Genesis tile data

    Returns:
        32-byte vertically flipped tile
    """
    if len(tile_bytes) != 32:
        raise ValueError(f"Genesis tile must be 32 bytes, got {len(tile_bytes)}")

    result = bytearray(32)

    for row in range(8):
        src_row = 7 - row  # Reverse row order
        src_start = src_row * 4
        dst_start = row * 4
        result[dst_start:dst_start + 4] = tile_bytes[src_start:src_start + 4]

    return bytes(result)


def flip_tile_hv(tile_bytes: bytes) -> bytes:
    """
    Flip a Genesis 4bpp tile both horizontally and vertically.

    Equivalent to 180-degree rotation.

    Args:
        tile_bytes: 32-byte Genesis tile data

    Returns:
        32-byte flipped tile (both axes)
    """
    return flip_tile_h(flip_tile_v(tile_bytes))


# =============================================================================
# TILE MATCHING WITH MIRROR DETECTION
# =============================================================================

def find_tile_match(tile_bytes: bytes,
                    unique_tiles: List[bytes],
                    tile_lookup: Dict[bytes, int] = None,
                    check_mirrors: bool = True) -> Optional[TileMatch]:
    """
    Check if tile matches any unique tile, including flipped variants.

    Checks in order: exact match, H-flip, V-flip, H+V-flip.
    Returns immediately on first match for efficiency.

    Args:
        tile_bytes: 32-byte tile to match
        unique_tiles: List of unique tile data
        tile_lookup: Optional dict mapping tile bytes -> index (for O(1) lookup)
        check_mirrors: Whether to check flipped variants

    Returns:
        TileMatch with index and flip flags, or None if no match
    """
    # Use lookup dict if provided, otherwise build one
    if tile_lookup is None:
        tile_lookup = {t: i for i, t in enumerate(unique_tiles)}

    # Check exact match first (most common case)
    if tile_bytes in tile_lookup:
        return TileMatch(
            index=tile_lookup[tile_bytes],
            h_flip=False,
            v_flip=False
        )

    if not check_mirrors:
        return None

    # Check H-flip
    h_flipped = flip_tile_h(tile_bytes)
    if h_flipped in tile_lookup:
        return TileMatch(
            index=tile_lookup[h_flipped],
            h_flip=True,
            v_flip=False
        )

    # Check V-flip
    v_flipped = flip_tile_v(tile_bytes)
    if v_flipped in tile_lookup:
        return TileMatch(
            index=tile_lookup[v_flipped],
            h_flip=False,
            v_flip=True
        )

    # Check H+V flip (180° rotation)
    hv_flipped = flip_tile_hv(tile_bytes)
    if hv_flipped in tile_lookup:
        return TileMatch(
            index=tile_lookup[hv_flipped],
            h_flip=True,
            v_flip=True
        )

    return None


def _extract_tile_4bpp(pixels: List[int], width: int,
                        tx: int, ty: int) -> bytes:
    """
    Extract a single 8x8 tile from pixel data as Genesis 4bpp format.

    Args:
        pixels: Flat list of palette indices
        width: Image width in pixels
        tx: Tile X coordinate (in tiles)
        ty: Tile Y coordinate (in tiles)

    Returns:
        32-byte Genesis tile data
    """
    tile_bytes = bytearray()

    for row in range(8):
        for col in range(0, 8, 2):
            px1 = tx * 8 + col
            px2 = tx * 8 + col + 1
            py = ty * 8 + row

            # Get palette indices (clamp to 0-15 for 4bpp)
            idx1 = pixels[py * width + px1] & 0x0F
            idx2 = pixels[py * width + px2] & 0x0F

            # Pack two 4-bit values (high nibble first)
            tile_bytes.append((idx1 << 4) | idx2)

    return bytes(tile_bytes)


def export_collision_header(sprites: List[SpriteInfo], output_path: str,
                           sprite_name: str = "sprite") -> bool:
    """
    Generate a C header file with collision data for SGDK.

    Args:
        sprites: List of SpriteInfo objects with collision data
        output_path: Path to output .h file
        sprite_name: Base name for the collision arrays (e.g., "player", "enemy")

    Returns:
        bool: True if successful, False otherwise

    Output format:
        - SpriteCollision struct with hitbox/hurtbox offsets
        - Const arrays for each sprite type's collision data
    """
    # Filter sprites that have collision data
    sprites_with_collision = [s for s in sprites if s.collision]

    if not sprites_with_collision:
        print(f"      [WARN] No sprites with collision data to export")
        return False

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Generate header guard from filename
    filename = os.path.basename(output_path).upper().replace('.', '_').replace('-', '_')
    guard_name = f"_{filename}_"

    # Build header content
    lines = [
        f"// Auto-generated collision data for SGDK",
        f"// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"// Source: unified_pipeline.py collision analysis",
        f"//",
        f"// Sprites processed: {len(sprites_with_collision)}",
        f"",
        f"#ifndef {guard_name}",
        f"#define {guard_name}",
        f"",
        f"#include <genesis.h>",
        f"",
        f"// =============================================================================",
        f"// COLLISION DATA STRUCTURE",
        f"// =============================================================================",
        f"",
        f"/**",
        f" * Collision box offsets relative to sprite origin (top-left).",
        f" * ",
        f" * hitbox:  Area that DEALS damage (weapon, projectile core)",
        f" * hurtbox: Area that RECEIVES damage (body, vulnerable region)",
        f" * ",
        f" * All values are in pixels, signed to allow negative offsets.",
        f" */",
        f"typedef struct {{",
        f"    s8 hitbox_x;      // Hitbox X offset from sprite origin",
        f"    s8 hitbox_y;      // Hitbox Y offset from sprite origin",
        f"    u8 hitbox_w;      // Hitbox width",
        f"    u8 hitbox_h;      // Hitbox height",
        f"    s8 hurtbox_x;     // Hurtbox X offset from sprite origin",
        f"    s8 hurtbox_y;     // Hurtbox Y offset from sprite origin",
        f"    u8 hurtbox_w;     // Hurtbox width",
        f"    u8 hurtbox_h;     // Hurtbox height",
        f"}} SpriteCollision;",
        f"",
    ]

    # Group sprites by type for organized output
    sprites_by_type = {}
    for sprite in sprites_with_collision:
        sprite_type = sprite.sprite_type or "unknown"
        if sprite_type not in sprites_by_type:
            sprites_by_type[sprite_type] = []
        sprites_by_type[sprite_type].append(sprite)

    # Generate collision arrays for each type
    lines.append(f"// =============================================================================")
    lines.append(f"// COLLISION DATA ARRAYS")
    lines.append(f"// =============================================================================")
    lines.append(f"")

    for sprite_type, type_sprites in sprites_by_type.items():
        # Sanitize type name for C identifier
        c_type_name = _sanitize_c_identifier(sprite_type)
        array_name = f"collision_{sprite_name}_{c_type_name}"

        lines.append(f"// {sprite_type.title()} collision data ({len(type_sprites)} frames)")
        lines.append(f"const SpriteCollision {array_name}[{len(type_sprites)}] = {{")

        for i, sprite in enumerate(type_sprites):
            col = sprite.collision
            hitbox = col.hitbox
            hurtbox = col.hurtbox

            # Format collision entry
            entry = (f"    {{ {hitbox.x:3}, {hitbox.y:3}, {hitbox.width:3}, {hitbox.height:3}, "
                    f"{hurtbox.x:3}, {hurtbox.y:3}, {hurtbox.width:3}, {hurtbox.height:3} }}")

            # Add comment with sprite info
            comment = f"// frame {sprite.frame_index}: {sprite.action}"
            if col.confidence < 0.5:
                comment += " (low confidence)"

            if i < len(type_sprites) - 1:
                lines.append(f"{entry}, {comment}")
            else:
                lines.append(f"{entry}  {comment}")

        lines.append(f"}};")
        lines.append(f"")

    # Generate frame count defines
    lines.append(f"// =============================================================================")
    lines.append(f"// FRAME COUNTS")
    lines.append(f"// =============================================================================")
    lines.append(f"")

    for sprite_type, type_sprites in sprites_by_type.items():
        c_type_name = _sanitize_c_identifier(sprite_type).upper()
        define_name = f"COLLISION_{sprite_name.upper()}_{c_type_name}_COUNT"
        lines.append(f"#define {define_name} {len(type_sprites)}")

    lines.append(f"")
    lines.append(f"#endif // {guard_name}")
    lines.append(f"")

    # Write file
    try:
        with open(output_path, 'w') as f:
            f.write('\n'.join(lines))
        print(f"      [EXPORT] Collision header: {output_path}")
        return True
    except Exception as e:
        print(f"      [ERROR] Failed to write collision header: {e}")
        return False


def export_collision_masks(sprites: List[SpriteInfo], output_path: str,
                          sprite_name: str = "sprite") -> bool:
    """
    Generate a C header file with per-pixel collision masks for SGDK.

    Only exports masks for sprites that have pixel_mask data (typically bosses
    or sprites with irregular shapes).

    Args:
        sprites: List of SpriteInfo objects with collision data
        output_path: Path to output .h file
        sprite_name: Base name for the mask arrays

    Returns:
        bool: True if successful (or no masks to export), False on error
    """
    # Filter sprites that have pixel masks
    sprites_with_masks = [
        s for s in sprites
        if s.collision and s.collision.pixel_mask and s.collision.mask_type == "pixel"
    ]

    if not sprites_with_masks:
        print(f"      [INFO] No pixel collision masks to export")
        return True  # Not an error, just nothing to export

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Generate header guard
    filename = os.path.basename(output_path).upper().replace('.', '_').replace('-', '_')
    guard_name = f"_{filename}_"

    lines = [
        f"// Auto-generated per-pixel collision masks for SGDK",
        f"// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"// Source: unified_pipeline.py collision analysis",
        f"//",
        f"// These are 1-bit masks where each bit represents a pixel.",
        f"// Bits are packed MSB-first, 8 pixels per byte, row-major order.",
        f"//",
        f"// Sprites with masks: {len(sprites_with_masks)}",
        f"",
        f"#ifndef {guard_name}",
        f"#define {guard_name}",
        f"",
        f"#include <genesis.h>",
        f"",
    ]

    # Generate mask arrays
    for sprite in sprites_with_masks:
        col = sprite.collision
        mask_data = col.pixel_mask

        # Calculate dimensions
        width = sprite.bbox.width
        height = sprite.bbox.height
        bytes_per_row = (width + 7) // 8

        # Sanitize name
        c_name = _sanitize_c_identifier(f"{sprite.sprite_type}_{sprite.action}_{sprite.frame_index}")
        array_name = f"collision_mask_{sprite_name}_{c_name}"

        lines.append(f"// {sprite.sprite_type} {sprite.action} frame {sprite.frame_index}")
        lines.append(f"// Dimensions: {width}x{height} pixels, {bytes_per_row} bytes/row")
        lines.append(f"const u8 {array_name}[{len(mask_data)}] = {{")

        # Format mask data as hex bytes with row comments
        for row in range(height):
            row_start = row * bytes_per_row
            row_end = row_start + bytes_per_row
            row_bytes = mask_data[row_start:row_end]

            hex_values = ', '.join(f'0x{b:02X}' for b in row_bytes)

            # Generate ASCII representation of row
            ascii_repr = ''
            for byte_idx, byte_val in enumerate(row_bytes):
                for bit in range(8):
                    pixel_x = byte_idx * 8 + bit
                    if pixel_x < width:
                        ascii_repr += '#' if (byte_val >> (7 - bit)) & 1 else '.'

            if row < height - 1:
                lines.append(f"    {hex_values},  // row {row:2}: {ascii_repr}")
            else:
                lines.append(f"    {hex_values}   // row {row:2}: {ascii_repr}")

        lines.append(f"}};")
        lines.append(f"#define {array_name.upper()}_WIDTH {width}")
        lines.append(f"#define {array_name.upper()}_HEIGHT {height}")
        lines.append(f"#define {array_name.upper()}_BYTES_PER_ROW {bytes_per_row}")
        lines.append(f"")

    lines.append(f"#endif // {guard_name}")
    lines.append(f"")

    # Write file
    try:
        with open(output_path, 'w') as f:
            f.write('\n'.join(lines))
        print(f"      [EXPORT] Collision masks: {output_path}")
        return True
    except Exception as e:
        print(f"      [ERROR] Failed to write collision masks: {e}")
        return False


def export_collision_json(sprites: List[SpriteInfo], output_path: str) -> bool:
    """
    Export collision data as JSON for non-C workflows or debugging.

    Args:
        sprites: List of SpriteInfo objects
        output_path: Path to output .json file

    Returns:
        bool: True if successful
    """
    import json

    sprites_with_collision = [s for s in sprites if s.collision]

    if not sprites_with_collision:
        print(f"      [WARN] No sprites with collision data to export")
        return False

    # Build JSON structure
    data = {
        "generated": datetime.now().isoformat(),
        "sprite_count": len(sprites_with_collision),
        "sprites": []
    }

    for sprite in sprites_with_collision:
        sprite_data = sprite.to_dict()
        data["sprites"].append(sprite_data)

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    try:
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"      [EXPORT] Collision JSON: {output_path}")
        return True
    except Exception as e:
        print(f"      [ERROR] Failed to write collision JSON: {e}")
        return False


def _sanitize_c_identifier(name: str) -> str:
    """
    Convert an arbitrary string to a valid C identifier.

    C identifiers must:
    - Contain only alphanumeric characters and underscores
    - Not start with a digit
    - Not be empty

    Args:
        name: The input string (e.g., filename, sprite name).

    Returns:
        A lowercase C-safe identifier string.

    Examples:
        >>> _sanitize_c_identifier("player-sprite")
        'player_sprite'
        >>> _sanitize_c_identifier("32x32_enemy")
        '_32x32_enemy'
    """
    result = ''
    for char in name:
        if char.isalnum() or char == '_':
            result += char
        else:
            result += '_'

    if result and result[0].isdigit():
        result = '_' + result

    if not result:
        result = 'unnamed'

    return result.lower()


# =============================================================================
# DEBUG AND VISUALIZATION UTILITIES
# =============================================================================

def generate_debug_overlay(sprites: List[SpriteInfo], img_path: str, output_path: str) -> bool:
    """
    Generate a debug image showing collision boxes overlaid on sprites.

    Args:
        sprites: List of SpriteInfo with collision data
        img_path: Path to original sprite sheet image
        output_path: Path to save debug overlay image

    Returns:
        bool: True if successful
    """
    from PIL import Image, ImageDraw

    try:
        img = Image.open(img_path).convert('RGBA')
    except Exception as e:
        print(f"      [ERROR] Could not open image: {e}")
        return False

    draw = ImageDraw.Draw(img)

    # Colors for visualization
    HITBOX_COLOR = (255, 0, 0, 180)      # Red, semi-transparent
    HURTBOX_COLOR = (0, 255, 0, 180)     # Green, semi-transparent
    BBOX_COLOR = (255, 255, 0, 100)      # Yellow, more transparent

    for sprite in sprites:
        if not sprite.collision:
            continue

        bbox = sprite.bbox
        col = sprite.collision

        # Draw sprite bounding box (yellow)
        draw.rectangle(
            [bbox.x, bbox.y, bbox.x + bbox.width - 1, bbox.y + bbox.height - 1],
            outline=BBOX_COLOR,
            width=1
        )

        # Draw hurtbox (green) - offset from sprite origin
        hurtbox = col.hurtbox
        hx = bbox.x + hurtbox.x
        hy = bbox.y + hurtbox.y
        draw.rectangle(
            [hx, hy, hx + hurtbox.width - 1, hy + hurtbox.height - 1],
            outline=HURTBOX_COLOR,
            width=2
        )

        # Draw hitbox (red) - offset from sprite origin
        hitbox = col.hitbox
        hx = bbox.x + hitbox.x
        hy = bbox.y + hitbox.y
        draw.rectangle(
            [hx, hy, hx + hitbox.width - 1, hy + hitbox.height - 1],
            outline=HITBOX_COLOR,
            width=2
        )

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    try:
        img.save(output_path)
        print(f"      [EXPORT] Debug overlay: {output_path}")
        return True
    except Exception as e:
        print(f"      [ERROR] Failed to save debug overlay: {e}")
        return False


# =============================================================================
# GENESIS 4BPP TILE EXPORT (Phase 0.6)
# =============================================================================

def export_genesis_tiles(indexed_img, output_path: str,
                         generate_header: bool = True) -> dict:
    """
    Export an indexed image as Genesis 4bpp tile data.

    Genesis tile format:
    - 8x8 pixels per tile
    - 4 bits per pixel (16 colors)
    - 32 bytes per tile
    - Packed as 2 pixels per byte (high nibble first)

    Args:
        indexed_img: PIL Image in 'P' mode (indexed colors)
        output_path: Path to output .bin file
        generate_header: Also generate a .h file with tile count defines

    Returns:
        dict: {
            'success': bool,
            'tile_count': int,
            'bytes': int,
            'bin_path': str,
            'header_path': str (if generated)
        }
    """
    from PIL import Image

    result = {
        'success': False,
        'tile_count': 0,
        'bytes': 0,
        'bin_path': output_path,
        'header_path': None
    }

    # Validate image mode
    if indexed_img.mode != 'P':
        print(f"      [ERROR] Image must be indexed (mode 'P'), got '{indexed_img.mode}'")
        return result

    # Get image dimensions
    width, height = indexed_img.size

    # Validate tile alignment
    if width % 8 != 0 or height % 8 != 0:
        print(f"      [WARN] Image size {width}x{height} not tile-aligned, padding to 8px boundary")
        # Pad to tile boundary
        new_width = ((width + 7) // 8) * 8
        new_height = ((height + 7) // 8) * 8
        padded = Image.new('P', (new_width, new_height), 0)
        padded.putpalette(indexed_img.getpalette())
        padded.paste(indexed_img, (0, 0))
        indexed_img = padded
        width, height = indexed_img.size

    # Calculate tile counts
    tiles_x = width // 8
    tiles_y = height // 8
    total_tiles = tiles_x * tiles_y

    # Get pixel data
    pixels = list(indexed_img.getdata())

    # Generate tile data (Genesis 4bpp format)
    tile_data = bytearray()

    for ty in range(tiles_y):
        for tx in range(tiles_x):
            # Process each 8x8 tile
            for row in range(8):
                for col in range(0, 8, 2):
                    # Get pixel coordinates
                    px1 = tx * 8 + col
                    px2 = tx * 8 + col + 1
                    py = ty * 8 + row

                    # Get palette indices (clamp to 0-15)
                    idx1 = pixels[py * width + px1] & 0x0F
                    idx2 = pixels[py * width + px2] & 0x0F

                    # Pack two 4-bit values into one byte (high nibble first)
                    tile_data.append((idx1 << 4) | idx2)

    result['tile_count'] = total_tiles
    result['bytes'] = len(tile_data)

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Write binary tile data
    try:
        with open(output_path, 'wb') as f:
            f.write(tile_data)
        print(f"      [EXPORT] Genesis tiles: {output_path} ({total_tiles} tiles, {len(tile_data)} bytes)")
        result['success'] = True
    except Exception as e:
        print(f"      [ERROR] Failed to write tile data: {e}")
        return result

    # Generate C header if requested
    if generate_header:
        header_path = output_path.replace('.bin', '.h')
        base_name = os.path.splitext(os.path.basename(output_path))[0]

        header_content = _generate_tile_header(base_name, total_tiles, tiles_x, tiles_y)

        try:
            with open(header_path, 'w') as f:
                f.write(header_content)
            print(f"      [EXPORT] Tile header: {header_path}")
            result['header_path'] = header_path
        except Exception as e:
            print(f"      [WARN] Could not write tile header: {e}")

    return result


def export_genesis_tilemap(indexed_img, output_path: str,
                           optimize_duplicates: bool = True) -> dict:
    """
    Export an indexed image as Genesis tilemap with optional tile deduplication.

    Returns separate files for:
    - Unique tiles (.bin)
    - Tilemap indices (.map)
    - C header with defines (.h)

    Args:
        indexed_img: PIL Image in 'P' mode
        output_path: Base path for outputs (will add extensions)
        optimize_duplicates: If True, deduplicate identical tiles

    Returns:
        dict: {
            'success': bool,
            'unique_tiles': int,
            'total_tiles': int,
            'compression_ratio': float,
            'tiles_path': str,
            'map_path': str,
            'header_path': str
        }
    """
    from PIL import Image

    result = {
        'success': False,
        'unique_tiles': 0,
        'total_tiles': 0,
        'compression_ratio': 1.0,
        'tiles_path': None,
        'map_path': None,
        'header_path': None
    }

    if indexed_img.mode != 'P':
        print(f"      [ERROR] Image must be indexed (mode 'P')")
        return result

    width, height = indexed_img.size

    # Pad to tile boundary
    if width % 8 != 0 or height % 8 != 0:
        new_width = ((width + 7) // 8) * 8
        new_height = ((height + 7) // 8) * 8
        padded = Image.new('P', (new_width, new_height), 0)
        padded.putpalette(indexed_img.getpalette())
        padded.paste(indexed_img, (0, 0))
        indexed_img = padded
        width, height = indexed_img.size

    tiles_x = width // 8
    tiles_y = height // 8
    total_tiles = tiles_x * tiles_y
    result['total_tiles'] = total_tiles

    pixels = list(indexed_img.getdata())

    # Extract all tiles
    all_tiles = []
    for ty in range(tiles_y):
        for tx in range(tiles_x):
            tile_bytes = bytearray()
            for row in range(8):
                for col in range(0, 8, 2):
                    px1 = tx * 8 + col
                    px2 = tx * 8 + col + 1
                    py = ty * 8 + row
                    idx1 = pixels[py * width + px1] & 0x0F
                    idx2 = pixels[py * width + px2] & 0x0F
                    tile_bytes.append((idx1 << 4) | idx2)
            all_tiles.append(bytes(tile_bytes))

    # Deduplicate tiles
    if optimize_duplicates:
        unique_tiles = []
        tile_to_index = {}
        tilemap = []

        for tile in all_tiles:
            if tile not in tile_to_index:
                tile_to_index[tile] = len(unique_tiles)
                unique_tiles.append(tile)
            tilemap.append(tile_to_index[tile])
    else:
        unique_tiles = all_tiles
        tilemap = list(range(len(all_tiles)))

    result['unique_tiles'] = len(unique_tiles)
    result['compression_ratio'] = total_tiles / len(unique_tiles) if unique_tiles else 1.0

    # Prepare output paths
    base_path = output_path.rsplit('.', 1)[0]
    tiles_path = f"{base_path}_tiles.bin"
    map_path = f"{base_path}_map.bin"
    header_path = f"{base_path}.h"

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Write unique tiles
    try:
        with open(tiles_path, 'wb') as f:
            for tile in unique_tiles:
                f.write(tile)
        result['tiles_path'] = tiles_path
        print(f"      [EXPORT] Unique tiles: {tiles_path} ({len(unique_tiles)} tiles)")
    except Exception as e:
        print(f"      [ERROR] Failed to write tiles: {e}")
        return result

    # Write tilemap (16-bit indices for SGDK VDP compatibility)
    try:
        with open(map_path, 'wb') as f:
            for idx in tilemap:
                # SGDK tilemap format: 16-bit with palette/priority/flip bits
                # For now, just tile index in low 11 bits
                f.write(idx.to_bytes(2, byteorder='big'))
        result['map_path'] = map_path
        print(f"      [EXPORT] Tilemap: {map_path} ({len(tilemap)} entries)")
    except Exception as e:
        print(f"      [ERROR] Failed to write tilemap: {e}")
        return result

    # Generate header
    base_name = os.path.basename(base_path)
    header_content = _generate_tilemap_header(
        base_name, len(unique_tiles), tiles_x, tiles_y,
        result['compression_ratio']
    )

    try:
        with open(header_path, 'w') as f:
            f.write(header_content)
        result['header_path'] = header_path
        print(f"      [EXPORT] Header: {header_path}")
    except Exception as e:
        print(f"      [WARN] Could not write header: {e}")

    result['success'] = True
    return result


def _generate_tile_header(name: str, tile_count: int,
                         tiles_x: int, tiles_y: int) -> str:
    """Generate a C header for tile data."""
    c_name = _sanitize_c_identifier(name).upper()

    return f"""// Auto-generated Genesis tile data header
// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
// Source: unified_pipeline.py genesis_export

#ifndef _{c_name}_TILES_H_
#define _{c_name}_TILES_H_

#include <genesis.h>

// Tile dimensions
#define {c_name}_TILES_X       {tiles_x}
#define {c_name}_TILES_Y       {tiles_y}
#define {c_name}_TILE_COUNT    {tile_count}
#define {c_name}_TILE_BYTES    ({tile_count} * 32)

// Load tiles from ROM address
// Usage: VDP_loadTileData({c_name}_tiles, TILE_USER_INDEX, {c_name}_TILE_COUNT, DMA);
extern const u32 {c_name}_tiles[{tile_count} * 8];

#endif // _{c_name}_TILES_H_
"""


def _generate_tilemap_header(name: str, unique_tiles: int,
                            map_width: int, map_height: int,
                            compression_ratio: float) -> str:
    """Generate a C header for tilemap data."""
    c_name = _sanitize_c_identifier(name).upper()

    return f"""// Auto-generated Genesis tilemap header
// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
// Source: unified_pipeline.py genesis_export
// Compression ratio: {compression_ratio:.2f}x

#ifndef _{c_name}_H_
#define _{c_name}_H_

#include <genesis.h>

// Map dimensions (in tiles)
#define {c_name}_WIDTH         {map_width}
#define {c_name}_HEIGHT        {map_height}

// Tile counts
#define {c_name}_UNIQUE_TILES  {unique_tiles}
#define {c_name}_TOTAL_TILES   ({map_width} * {map_height})

// Data sizes
#define {c_name}_TILES_BYTES   ({unique_tiles} * 32)
#define {c_name}_MAP_BYTES     ({map_width} * {map_height} * 2)

// External references (link with .bin files)
extern const u32 {c_name}_tiles[];
extern const u16 {c_name}_map[];

// Usage example:
// VDP_loadTileData({c_name}_tiles, TILE_USER_INDEX, {c_name}_UNIQUE_TILES, DMA);
// VDP_setTileMapEx(BG_A, {c_name}_map, TILE_ATTR_FULL(PAL0, FALSE, FALSE, FALSE, TILE_USER_INDEX),
//                  0, 0, 0, 0, {c_name}_WIDTH, {c_name}_HEIGHT, {c_name}_WIDTH, DMA);

#endif // _{c_name}_H_
"""


# =============================================================================
# OPTIMIZED TILEMAP EXPORT WITH MIRROR DETECTION (Phase 2.0.3)
# =============================================================================

def export_genesis_tilemap_optimized(indexed_img, output_path: str,
                                      use_mirroring: bool = True,
                                      palette: int = 0,
                                      priority: bool = False,
                                      base_tile: int = 0) -> dict:
    """
    Enhanced tilemap export with flip flag optimization.

    Detects horizontally and vertically flipped tile duplicates to reduce
    unique tile count. Typically saves 20-40% VRAM on symmetric tilesets.

    VDP Tilemap entry format (16-bit):
        Bit 15: Priority (0 = low, 1 = high)
        Bits 14-13: Palette index (0-3)
        Bit 12: V-flip
        Bit 11: H-flip
        Bits 10-0: Tile index

    Args:
        indexed_img: PIL Image in 'P' mode (indexed colors)
        output_path: Base path for outputs (will add extensions)
        use_mirroring: Enable H/V flip detection for additional savings
        palette: Palette index (0-3) for tilemap entries
        priority: Priority flag for all tilemap entries
        base_tile: Base tile index offset (for VRAM placement)

    Returns:
        dict: {
            'success': bool,
            'stats': TileOptimizationStats,
            'tiles_path': str,
            'map_path': str,
            'header_path': str
        }
    """
    from PIL import Image

    result = {
        'success': False,
        'stats': None,
        'tiles_path': None,
        'map_path': None,
        'header_path': None
    }

    # Validate image mode
    if indexed_img.mode != 'P':
        print(f"      [ERROR] Image must be indexed (mode 'P'), got '{indexed_img.mode}'")
        return result

    width, height = indexed_img.size

    # Pad to tile boundary if needed
    if width % 8 != 0 or height % 8 != 0:
        new_width = ((width + 7) // 8) * 8
        new_height = ((height + 7) // 8) * 8
        padded = Image.new('P', (new_width, new_height), 0)
        padded.putpalette(indexed_img.getpalette())
        padded.paste(indexed_img, (0, 0))
        indexed_img = padded
        width, height = indexed_img.size

    tiles_x = width // 8
    tiles_y = height // 8
    total_tiles = tiles_x * tiles_y

    pixels = list(indexed_img.getdata())

    # Extract all tiles as 4bpp data
    all_tiles = []
    for ty in range(tiles_y):
        for tx in range(tiles_x):
            tile = _extract_tile_4bpp(pixels, width, tx, ty)
            all_tiles.append(tile)

    # Deduplicate with mirror detection
    unique_tiles = []
    tile_lookup = {}  # bytes -> index
    tilemap_entries = []  # List of TileMatch objects

    # Statistics
    exact_matches = 0
    h_flip_matches = 0
    v_flip_matches = 0
    hv_flip_matches = 0

    for tile in all_tiles:
        # Try to find match in existing unique tiles
        match = find_tile_match(tile, unique_tiles, tile_lookup, check_mirrors=use_mirroring)

        if match is not None:
            # Track match type for stats
            if not match.h_flip and not match.v_flip:
                exact_matches += 1
            elif match.h_flip and not match.v_flip:
                h_flip_matches += 1
            elif not match.h_flip and match.v_flip:
                v_flip_matches += 1
            else:
                hv_flip_matches += 1

            # Adjust index for base_tile offset
            tilemap_entries.append(TileMatch(
                index=match.index + base_tile,
                h_flip=match.h_flip,
                v_flip=match.v_flip
            ))
        else:
            # New unique tile
            new_index = len(unique_tiles)
            tile_lookup[tile] = new_index
            unique_tiles.append(tile)

            tilemap_entries.append(TileMatch(
                index=new_index + base_tile,
                h_flip=False,
                v_flip=False
            ))

    # Build statistics
    stats = TileOptimizationStats(
        total_tiles=total_tiles,
        unique_tiles=len(unique_tiles),
        exact_matches=exact_matches,
        h_flip_matches=h_flip_matches,
        v_flip_matches=v_flip_matches,
        hv_flip_matches=hv_flip_matches
    )
    result['stats'] = stats

    # Prepare output paths
    base_path = output_path.rsplit('.', 1)[0]
    tiles_path = f"{base_path}_tiles.bin"
    map_path = f"{base_path}_map.bin"
    header_path = f"{base_path}.h"

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Write unique tiles
    try:
        with open(tiles_path, 'wb') as f:
            for tile in unique_tiles:
                f.write(tile)
        result['tiles_path'] = tiles_path
    except Exception as e:
        print(f"      [ERROR] Failed to write tiles: {e}")
        return result

    # Write tilemap with VDP attributes
    try:
        with open(map_path, 'wb') as f:
            for entry in tilemap_entries:
                vdp_word = entry.to_vdp_flags(palette=palette, priority=priority)
                f.write(vdp_word.to_bytes(2, byteorder='big'))
        result['map_path'] = map_path
    except Exception as e:
        print(f"      [ERROR] Failed to write tilemap: {e}")
        return result

    # Generate enhanced header with mirror stats
    header_content = _generate_optimized_tilemap_header(
        os.path.basename(base_path),
        stats,
        tiles_x, tiles_y,
        use_mirroring
    )

    try:
        with open(header_path, 'w') as f:
            f.write(header_content)
        result['header_path'] = header_path
    except Exception as e:
        print(f"      [WARN] Could not write header: {e}")

    # Print summary
    print(f"      [EXPORT] Optimized tilemap: {tiles_path}")
    print(f"               Unique tiles: {stats.unique_tiles} / {stats.total_tiles} "
          f"(saved {stats.savings_percent:.1f}%)")
    if use_mirroring and stats.mirror_savings > 0:
        print(f"               Mirror matches: H={stats.h_flip_matches}, "
              f"V={stats.v_flip_matches}, HV={stats.hv_flip_matches}")

    result['success'] = True
    return result


def _generate_optimized_tilemap_header(name: str, stats: TileOptimizationStats,
                                        map_width: int, map_height: int,
                                        use_mirroring: bool) -> str:
    """Generate a C header for optimized tilemap with mirror stats."""
    c_name = _sanitize_c_identifier(name).upper()

    mirror_comment = ""
    if use_mirroring:
        mirror_comment = f"""
// Mirror optimization enabled
// - Exact matches:    {stats.exact_matches}
// - H-flip matches:   {stats.h_flip_matches}
// - V-flip matches:   {stats.v_flip_matches}
// - H+V flip matches: {stats.hv_flip_matches}
// - VRAM savings:     {stats.savings_percent:.1f}%"""

    return f"""// Auto-generated Genesis tilemap header (optimized)
// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
// Source: unified_pipeline.py genesis_export
// Compression ratio: {stats.compression_ratio:.2f}x{mirror_comment}

#ifndef _{c_name}_H_
#define _{c_name}_H_

#include <genesis.h>

// Map dimensions (in tiles)
#define {c_name}_WIDTH         {map_width}
#define {c_name}_HEIGHT        {map_height}

// Tile counts
#define {c_name}_UNIQUE_TILES  {stats.unique_tiles}
#define {c_name}_TOTAL_TILES   {stats.total_tiles}

// Data sizes
#define {c_name}_TILES_BYTES   ({stats.unique_tiles} * 32)
#define {c_name}_MAP_BYTES     ({stats.total_tiles} * 2)

// External references (link with .bin files)
extern const u32 {c_name}_tiles[];
extern const u16 {c_name}_map[];

// Usage example:
// VDP_loadTileData({c_name}_tiles, TILE_USER_INDEX, {c_name}_UNIQUE_TILES, DMA);
// VDP_setTileMapEx(BG_A, {c_name}_map, TILE_ATTR_FULL(PAL0, FALSE, FALSE, FALSE, TILE_USER_INDEX),
//                  0, 0, 0, 0, {c_name}_WIDTH, {c_name}_HEIGHT, {c_name}_WIDTH, DMA);

#endif // _{c_name}_H_
"""


# =============================================================================
# CROSS-PLATFORM TILE FLIP FUNCTIONS (NES, SNES, GameBoy, etc.)
# =============================================================================

def flip_tile_2bpp_h(tile_bytes: bytes, tile_size: int = 8) -> bytes:
    """
    Flip a 2bpp tile horizontally (NES/GameBoy format).

    NES/GB tile format: 8x8 pixels, 2bpp planar.
    - 16 bytes per tile
    - Plane 0 (low bits): bytes 0-7
    - Plane 1 (high bits): bytes 8-15

    To flip horizontally, reverse bit order within each byte.

    Args:
        tile_bytes: 16-byte NES/GB tile data
        tile_size: Tile width/height (default 8)

    Returns:
        16-byte horizontally flipped tile
    """
    bytes_per_plane = tile_size

    if len(tile_bytes) != bytes_per_plane * 2:
        raise ValueError(f"NES/GB tile must be {bytes_per_plane * 2} bytes, got {len(tile_bytes)}")

    result = bytearray(len(tile_bytes))

    # Reverse bits in each byte (both planes)
    for i, byte_val in enumerate(tile_bytes):
        # Reverse bits: 76543210 -> 01234567
        reversed_byte = 0
        for bit in range(8):
            if byte_val & (1 << bit):
                reversed_byte |= (1 << (7 - bit))
        result[i] = reversed_byte

    return bytes(result)


def flip_tile_2bpp_v(tile_bytes: bytes, tile_size: int = 8) -> bytes:
    """
    Flip a 2bpp tile vertically (NES/GameBoy format).

    Reverses row order within each plane.

    Args:
        tile_bytes: 16-byte NES/GB tile data
        tile_size: Tile width/height (default 8)

    Returns:
        16-byte vertically flipped tile
    """
    bytes_per_plane = tile_size

    if len(tile_bytes) != bytes_per_plane * 2:
        raise ValueError(f"NES/GB tile must be {bytes_per_plane * 2} bytes, got {len(tile_bytes)}")

    result = bytearray(len(tile_bytes))

    # Reverse row order in plane 0
    for row in range(tile_size):
        result[row] = tile_bytes[tile_size - 1 - row]

    # Reverse row order in plane 1
    for row in range(tile_size):
        result[tile_size + row] = tile_bytes[tile_size + tile_size - 1 - row]

    return bytes(result)


def flip_tile_2bpp_hv(tile_bytes: bytes, tile_size: int = 8) -> bytes:
    """Flip a 2bpp tile both horizontally and vertically."""
    return flip_tile_2bpp_h(flip_tile_2bpp_v(tile_bytes, tile_size), tile_size)


def flip_tile_snes_h(tile_bytes: bytes) -> bytes:
    """
    Flip a SNES 4bpp tile horizontally.

    SNES tile format: 8x8 pixels, 4bpp planar interleaved.
    - 32 bytes per tile
    - Rows interleaved: row0_plane01, row0_plane23, row1_plane01, ...

    Args:
        tile_bytes: 32-byte SNES tile data

    Returns:
        32-byte horizontally flipped tile
    """
    if len(tile_bytes) != 32:
        raise ValueError(f"SNES tile must be 32 bytes, got {len(tile_bytes)}")

    result = bytearray(32)

    # SNES format: bytes 0-15 are bitplanes 0-1, bytes 16-31 are bitplanes 2-3
    # Within each 16-byte section: even bytes are plane 0/2, odd bytes are plane 1/3
    # To flip horizontally, reverse bits in every byte
    for i, byte_val in enumerate(tile_bytes):
        # Reverse bits: 76543210 -> 01234567
        reversed_byte = 0
        for bit in range(8):
            if byte_val & (1 << bit):
                reversed_byte |= (1 << (7 - bit))
        result[i] = reversed_byte

    return bytes(result)


def flip_tile_snes_v(tile_bytes: bytes) -> bytes:
    """
    Flip a SNES 4bpp tile vertically.

    Args:
        tile_bytes: 32-byte SNES tile data

    Returns:
        32-byte vertically flipped tile
    """
    if len(tile_bytes) != 32:
        raise ValueError(f"SNES tile must be 32 bytes, got {len(tile_bytes)}")

    result = bytearray(32)

    # Reverse row order within each 16-byte section
    for section in range(2):  # Bitplanes 0-1, then 2-3
        section_offset = section * 16
        for row in range(8):
            src_row = 7 - row
            # Copy both bytes of the row (plane 0/2 and plane 1/3)
            result[section_offset + row * 2] = tile_bytes[section_offset + src_row * 2]
            result[section_offset + row * 2 + 1] = tile_bytes[section_offset + src_row * 2 + 1]

    return bytes(result)


def flip_tile_snes_hv(tile_bytes: bytes) -> bytes:
    """Flip a SNES tile both horizontally and vertically."""
    return flip_tile_snes_h(flip_tile_snes_v(tile_bytes))


# =============================================================================
# GENERIC CROSS-PLATFORM TILE OPTIMIZATION
# =============================================================================

class TileFormat:
    """Tile format specification for different platforms."""

    # Predefined formats
    GENESIS = 'genesis'  # 4bpp packed, 32 bytes
    NES = 'nes'          # 2bpp planar, 16 bytes
    SNES = 'snes'        # 4bpp planar interleaved, 32 bytes
    GAMEBOY = 'gameboy'  # 2bpp planar, 16 bytes (same as NES)

    TILE_SIZES = {
        GENESIS: 32,
        NES: 16,
        SNES: 32,
        GAMEBOY: 16,
    }

    FLIP_FUNCTIONS = {
        GENESIS: (flip_tile_h, flip_tile_v, flip_tile_hv),
        NES: (flip_tile_2bpp_h, flip_tile_2bpp_v, flip_tile_2bpp_hv),
        SNES: (flip_tile_snes_h, flip_tile_snes_v, flip_tile_snes_hv),
        GAMEBOY: (flip_tile_2bpp_h, flip_tile_2bpp_v, flip_tile_2bpp_hv),
    }


def find_tile_match_multiplatform(tile_bytes: bytes,
                                   unique_tiles: List[bytes],
                                   tile_lookup: Dict[bytes, int] = None,
                                   platform: str = TileFormat.GENESIS,
                                   check_mirrors: bool = True) -> Optional[TileMatch]:
    """
    Cross-platform tile matching with mirror detection.

    Supports Genesis, NES, SNES, and GameBoy tile formats.

    Args:
        tile_bytes: Tile data in platform-specific format
        unique_tiles: List of unique tile data
        tile_lookup: Optional dict for O(1) lookup
        platform: Target platform (TileFormat.GENESIS, etc.)
        check_mirrors: Whether to check flipped variants

    Returns:
        TileMatch with index and flip flags, or None if no match
    """
    if tile_lookup is None:
        tile_lookup = {t: i for i, t in enumerate(unique_tiles)}

    # Check exact match first
    if tile_bytes in tile_lookup:
        return TileMatch(
            index=tile_lookup[tile_bytes],
            h_flip=False,
            v_flip=False
        )

    if not check_mirrors:
        return None

    # Get platform-specific flip functions
    flip_h, flip_v, flip_hv = TileFormat.FLIP_FUNCTIONS.get(
        platform,
        (flip_tile_h, flip_tile_v, flip_tile_hv)  # Default to Genesis
    )

    # Check H-flip
    h_flipped = flip_h(tile_bytes)
    if h_flipped in tile_lookup:
        return TileMatch(
            index=tile_lookup[h_flipped],
            h_flip=True,
            v_flip=False
        )

    # Check V-flip
    v_flipped = flip_v(tile_bytes)
    if v_flipped in tile_lookup:
        return TileMatch(
            index=tile_lookup[v_flipped],
            h_flip=False,
            v_flip=True
        )

    # Check H+V flip
    hv_flipped = flip_hv(tile_bytes)
    if hv_flipped in tile_lookup:
        return TileMatch(
            index=tile_lookup[hv_flipped],
            h_flip=True,
            v_flip=True
        )

    return None


# =============================================================================
# VDP-READY EXPORT FUNCTIONS (Phase 2.1.2)
# =============================================================================

@dataclass
class SpriteAttribute:
    """
    Genesis VDP Sprite Attribute Table (SAT) entry.

    The Genesis VDP uses a linked-list SAT structure where each entry
    defines a hardware sprite's position, size, graphics, and attributes.
    This class represents one such entry and can serialize to the 8-byte
    VDP format for direct hardware upload.

    SAT Entry Memory Layout (8 bytes, big-endian):
        Word 0: Y position + 128 offset (VDP uses offset coordinates)
        Word 1: Size code (bits 10-8) | Link to next sprite (bits 6-0)
        Word 2: Priority(15) | Palette(14-13) | VFlip(12) | HFlip(11) | Tile(10-0)
        Word 3: X position + 128 offset

    Sprite Size Encoding (width_tiles × height_tiles → size code):
        Size = ((width-1) << 2) | (height-1)
        1×1=0, 1×2=1, 1×3=2, 1×4=3, 2×1=4, 2×2=5, 2×3=6, 2×4=7,
        3×1=8, 3×2=9, 3×3=10, 3×4=11, 4×1=12, 4×2=13, 4×3=14, 4×4=15

    Attributes:
        x: X position in screen coordinates (0-320).
        y: Y position in screen coordinates (0-224).
        width_tiles: Width in 8x8 tiles (1-4, max 32 pixels).
        height_tiles: Height in 8x8 tiles (1-4, max 32 pixels).
        tile_index: Base tile index in VRAM (0-2047).
        palette: Palette index (0-3).
        priority: True = render in front of high-priority BG tiles.
        h_flip: Flip sprite horizontally.
        v_flip: Flip sprite vertically.
        link: Index of next sprite in list (0 = end of chain).

    Example:
        >>> attr = SpriteAttribute(x=100, y=80, width_tiles=4, height_tiles=4,
        ...                        tile_index=16, palette=0)
        >>> sat_bytes = attr.to_bytes()  # 8 bytes ready for VDP
    """
    x: int
    y: int
    width_tiles: int
    height_tiles: int
    tile_index: int
    palette: int = 0
    priority: bool = False
    h_flip: bool = False
    v_flip: bool = False
    link: int = 0

    def to_bytes(self) -> bytes:
        """
        Convert to 8-byte VDP SAT entry.

        Returns:
            8 bytes in big-endian format ready for VDP
        """
        # Word 0: Y position (add 128 offset for VDP)
        y_pos = (self.y + 128) & 0x3FF

        # Size encoding: (width-1) << 2 | (height-1)
        size = ((self.width_tiles - 1) & 0x3) << 2 | ((self.height_tiles - 1) & 0x3)

        # Word 1: Size (bits 10-8) | Link (bits 6-0)
        word1 = (size << 8) | (self.link & 0x7F)

        # Word 2: Tile attributes
        # Bit 15: Priority
        # Bits 14-13: Palette
        # Bit 12: V-flip
        # Bit 11: H-flip
        # Bits 10-0: Tile index
        word2 = self.tile_index & 0x7FF
        if self.h_flip:
            word2 |= (1 << 11)
        if self.v_flip:
            word2 |= (1 << 12)
        word2 |= (self.palette & 0x3) << 13
        if self.priority:
            word2 |= (1 << 15)

        # Word 3: X position (add 128 offset for VDP)
        x_pos = (self.x + 128) & 0x3FF

        # Pack as big-endian words
        result = bytearray(8)
        result[0:2] = y_pos.to_bytes(2, 'big')
        result[2:4] = word1.to_bytes(2, 'big')
        result[4:6] = word2.to_bytes(2, 'big')
        result[6:8] = x_pos.to_bytes(2, 'big')

        return bytes(result)

    @classmethod
    def from_sprite_info(cls, sprite: 'SpriteInfo', tile_index: int,
                         palette: int = 0, priority: bool = False) -> 'SpriteAttribute':
        """
        Create SpriteAttribute from SpriteInfo.

        Args:
            sprite: SpriteInfo with position and dimensions
            tile_index: Base tile index in VRAM
            palette: Palette index (0-3)
            priority: High priority flag

        Returns:
            SpriteAttribute ready for VDP
        """
        # Calculate size in tiles (round up to nearest tile)
        width_tiles = (sprite.width + 7) // 8
        height_tiles = (sprite.height + 7) // 8

        # Clamp to valid range (1-4)
        width_tiles = max(1, min(4, width_tiles))
        height_tiles = max(1, min(4, height_tiles))

        return cls(
            x=sprite.x,
            y=sprite.y,
            width_tiles=width_tiles,
            height_tiles=height_tiles,
            tile_index=tile_index,
            palette=palette,
            priority=priority,
        )


def export_sprite_attribute_table(
    sprites: List[SpriteAttribute],
    output_path: str = None,
    auto_link: bool = True,
) -> bytes:
    """
    Generate VDP Sprite Attribute Table data.

    Args:
        sprites: List of SpriteAttribute objects
        output_path: Optional path to write binary file
        auto_link: Automatically set link fields (0 → 1 → 2 → ... → 0)

    Returns:
        SAT data as bytes (8 bytes per sprite)

    Example:
        sprites = [
            SpriteAttribute(x=100, y=80, width_tiles=4, height_tiles=4,
                          tile_index=0, palette=0),
            SpriteAttribute(x=150, y=80, width_tiles=2, height_tiles=2,
                          tile_index=16, palette=1),
        ]
        sat_data = export_sprite_attribute_table(sprites, "out/sprites.sat")
    """
    if not sprites:
        return bytes()

    # Auto-link sprites if requested
    if auto_link:
        for i, sprite in enumerate(sprites):
            if i < len(sprites) - 1:
                sprite.link = i + 1
            else:
                sprite.link = 0  # End of list

    # Build SAT data
    sat_data = bytearray()
    for sprite in sprites:
        sat_data.extend(sprite.to_bytes())

    result = bytes(sat_data)

    # Write to file if path provided
    if output_path:
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(result)

    return result


def export_cram_palette(
    colors: List[tuple],
    output_path: str = None,
    _palette_index: int = 0,
) -> bytes:
    """
    Export palette in Genesis CRAM format.

    Genesis CRAM format: 0000BBB0GGG0RRR0 (9-bit BGR, word-aligned)
    16 colors × 2 bytes = 32 bytes per palette

    Args:
        colors: List of RGB tuples [(r, g, b), ...]
        output_path: Optional path to write binary file
        _palette_index: Reserved for future C header generation (0-3)

    Returns:
        32 bytes of CRAM data (padded if < 16 colors)

    Example:
        colors = [(0,0,0), (255,255,255), (255,0,0), ...]
        cram_data = export_cram_palette(colors, "out/player.pal")
    """
    cram_data = bytearray()

    for i in range(16):
        if i < len(colors):
            r, g, b = colors[i]
        else:
            r, g, b = 0, 0, 0  # Pad with black

        # Convert 8-bit RGB to 3-bit Genesis format
        # Genesis: 0000BBB0GGG0RRR0
        gr = (r >> 5) & 0x7  # 3 bits
        gg = (g >> 5) & 0x7
        gb = (b >> 5) & 0x7

        # Pack as CRAM word
        cram_word = (gb << 9) | (gg << 5) | (gr << 1)
        cram_data.extend(cram_word.to_bytes(2, 'big'))

    result = bytes(cram_data)

    # Write to file if path provided
    if output_path:
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(result)

    return result


def export_tilemap_with_attributes(
    tilemap: List[int],
    _width: int,
    _height: int,
    output_path: str = None,
    palette: int = 0,
    priority: bool = False,
    base_tile: int = 0,
    flip_data: List[tuple] = None,
) -> bytes:
    """
    Export tilemap with full VDP attributes.

    VDP Tilemap entry format (16-bit):
        Bit 15: Priority (0 = low, 1 = high)
        Bits 14-13: Palette index (0-3)
        Bit 12: Vertical flip
        Bit 11: Horizontal flip
        Bits 10-0: Tile index

    Args:
        tilemap: List of tile indices
        _width: Map width in tiles (reserved for row-stride support)
        _height: Map height in tiles (reserved for bounds validation)
        output_path: Optional path to write binary file
        palette: Default palette for all tiles (0-3)
        priority: Default priority for all tiles
        base_tile: Base tile index offset
        flip_data: Optional list of (h_flip, v_flip) per tile

    Returns:
        Tilemap data as bytes (2 bytes per tile, big-endian)

    Example:
        tilemap = [0, 1, 2, 3, 4, 5, ...]  # Tile indices
        map_data = export_tilemap_with_attributes(
            tilemap, width=40, height=28,
            output_path="out/level.map",
            palette=2, priority=False
        )
    """
    map_data = bytearray()

    for i, tile_idx in enumerate(tilemap):
        # Get flip flags if provided
        h_flip = False
        v_flip = False
        if flip_data and i < len(flip_data):
            h_flip, v_flip = flip_data[i]

        # Build VDP tilemap entry
        entry = (tile_idx + base_tile) & 0x7FF  # 11-bit tile index
        if h_flip:
            entry |= (1 << 11)
        if v_flip:
            entry |= (1 << 12)
        entry |= (palette & 0x3) << 13
        if priority:
            entry |= (1 << 15)

        map_data.extend(entry.to_bytes(2, 'big'))

    result = bytes(map_data)

    # Write to file if path provided
    if output_path:
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(result)

    return result


def align_for_dma(data: bytes, alignment: int = 2) -> bytes:
    """
    Pad data to DMA-friendly boundary.

    Genesis DMA works best with word-aligned (2-byte) or
    long-word-aligned (4-byte) data.

    Args:
        data: Input data bytes
        alignment: Alignment boundary (2 for word, 4 for long)

    Returns:
        Padded data with 0x00 bytes

    Example:
        tile_data = bytes([...])  # 33 bytes
        aligned = align_for_dma(tile_data, alignment=4)
        # Returns 36 bytes (padded to next 4-byte boundary)
    """
    remainder = len(data) % alignment
    if remainder == 0:
        return data

    padding = alignment - remainder
    return data + bytes([0x00] * padding)


def export_vdp_ready_sprite(
    sprite_image,  # PIL Image
    output_base: str,
    palette_colors: List[tuple] = None,
    palette_index: int = 0,
    priority: bool = False,
) -> dict:
    """
    Complete VDP-ready export: tiles + palette + SAT entry.

    Generates all data needed to display a sprite on Genesis without
    any runtime conversion.

    Args:
        sprite_image: PIL Image (indexed 'P' mode recommended)
        output_base: Base path for output files (no extension)
        palette_colors: Optional palette to use (extracts from image if None)
        palette_index: VDP palette slot (0-3)
        priority: High priority flag for SAT

    Returns:
        dict: {
            'success': bool,
            'tiles_path': str,      # Binary tile data
            'palette_path': str,    # CRAM palette data
            'sat_path': str,        # Sprite attribute entry
            'header_path': str,     # C header with definitions
            'tile_count': int,
            'width_tiles': int,
            'height_tiles': int,
        }

    Example:
        result = export_vdp_ready_sprite(
            player_img,
            output_base="out/player",
            palette_index=0
        )
        # Creates: player_tiles.bin, player.pal, player.sat, player.h
    """
    from PIL import Image

    result = {
        'success': False,
        'tiles_path': None,
        'palette_path': None,
        'sat_path': None,
        'header_path': None,
        'tile_count': 0,
        'width_tiles': 0,
        'height_tiles': 0,
    }

    # Convert to indexed if needed
    if sprite_image.mode != 'P':
        sprite_image = sprite_image.convert('P', palette=Image.ADAPTIVE, colors=16)

    width, height = sprite_image.size

    # Pad to tile boundary
    width_tiles = (width + 7) // 8
    height_tiles = (height + 7) // 8
    padded_w = width_tiles * 8
    padded_h = height_tiles * 8

    if width != padded_w or height != padded_h:
        padded = Image.new('P', (padded_w, padded_h), 0)
        padded.putpalette(sprite_image.getpalette())
        padded.paste(sprite_image, (0, 0))
        sprite_image = padded

    result['width_tiles'] = width_tiles
    result['height_tiles'] = height_tiles
    result['tile_count'] = width_tiles * height_tiles

    # Extract palette if not provided
    if palette_colors is None:
        pal_data = sprite_image.getpalette()
        if pal_data:
            palette_colors = [
                (pal_data[i*3], pal_data[i*3+1], pal_data[i*3+2])
                for i in range(16)
            ]
        else:
            palette_colors = [(0, 0, 0)] * 16

    # Create output directory
    output_dir = os.path.dirname(output_base)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Export tiles
    pixels = list(sprite_image.getdata())
    tiles_data = bytearray()

    for ty in range(height_tiles):
        for tx in range(width_tiles):
            tile = _extract_tile_4bpp(pixels, padded_w, tx, ty)
            tiles_data.extend(tile)

    tiles_path = f"{output_base}_tiles.bin"
    with open(tiles_path, 'wb') as f:
        f.write(align_for_dma(bytes(tiles_data), 4))
    result['tiles_path'] = tiles_path

    # Export palette
    palette_path = f"{output_base}.pal"
    export_cram_palette(palette_colors, palette_path, palette_index)
    result['palette_path'] = palette_path

    # Export SAT entry
    sprite_attr = SpriteAttribute(
        x=0, y=0,
        width_tiles=min(width_tiles, 4),
        height_tiles=min(height_tiles, 4),
        tile_index=0,
        palette=palette_index,
        priority=priority,
    )
    sat_path = f"{output_base}.sat"
    export_sprite_attribute_table([sprite_attr], sat_path)
    result['sat_path'] = sat_path

    # Generate header
    header_path = f"{output_base}.h"
    name = os.path.basename(output_base)
    c_name = _sanitize_c_identifier(name).upper()

    header = f"""// Auto-generated VDP-ready sprite data
// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
// Source: genesis_export.py (Phase 2.1.2)

#ifndef _{c_name}_H_
#define _{c_name}_H_

#include <genesis.h>

// Sprite dimensions
#define {c_name}_WIDTH          {width}
#define {c_name}_HEIGHT         {height}
#define {c_name}_WIDTH_TILES    {width_tiles}
#define {c_name}_HEIGHT_TILES   {height_tiles}
#define {c_name}_TILE_COUNT     {result['tile_count']}

// Tile data size (32 bytes per tile)
#define {c_name}_TILES_BYTES    ({result['tile_count']} * 32)

// VDP configuration
#define {c_name}_PALETTE        PAL{palette_index}

// External data references
extern const u32 {c_name.lower()}_tiles[];
extern const u16 {c_name.lower()}_palette[16];

// Load sprite to VRAM
// tile_base: Starting tile index in VRAM
static inline void {c_name.lower()}_load(u16 tile_base) {{
    VDP_loadTileData({c_name.lower()}_tiles, tile_base, {c_name}_TILE_COUNT, DMA);
    PAL_setPalette({c_name}_PALETTE, {c_name.lower()}_palette);
}}

// Create sprite (call after loading tiles)
// Returns sprite index, or -1 if SAT full
static inline s16 {c_name.lower()}_create(s16 x, s16 y, u16 tile_base) {{
    return SPR_addSprite(&{c_name.lower()}_def, x, y,
        TILE_ATTR(PAL{palette_index}, {'TRUE' if priority else 'FALSE'}, FALSE, FALSE));
}}

#endif // _{c_name}_H_
"""

    with open(header_path, 'w') as f:
        f.write(header)
    result['header_path'] = header_path

    result['success'] = True
    return result