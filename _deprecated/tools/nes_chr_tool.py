#!/usr/bin/env python3
"""
NES CHR Tool - Pixel-Perfect CHR Generation for NES/Famicom
Part of the Agentic Retro Development Kit (ARDK)

This tool generates NES CHR files with precise control over tile ordering,
ensuring sprites render correctly in-game.

Features:
- Sprite sheet processing with automatic sprite detection
- 16x16 metasprite support with correct tile ordering (TL, TR, BL, BR)
- 8x8 single tile support
- NES palette enforcement (4 colors per sprite)
- Assembly include file generation with tile indices
- Background tile sheet support

Tile Ordering for 16x16 Metasprites:
    Source Image:       Output Tiles:
    +----+----+         Tile N+0: Top-Left
    | TL | TR |         Tile N+1: Top-Right
    +----+----+         Tile N+2: Bottom-Left
    | BL | BR |         Tile N+3: Bottom-Right
    +----+----+

Usage:
    python nes_chr_tool.py sprites.png -o sprites.chr --mode sprites
    python nes_chr_tool.py background.png -o background.chr --mode background
    python nes_chr_tool.py sheet.png -o output/ --mode sheet --sprite-size 16x16
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass, field
from PIL import Image
import numpy as np

# NES Master Palette (2C02 PPU)
NES_PALETTE = {
    0x00: (84, 84, 84),    0x01: (0, 30, 116),    0x02: (8, 16, 144),    0x03: (48, 0, 136),
    0x04: (68, 0, 100),    0x05: (92, 0, 48),     0x06: (84, 4, 0),      0x07: (60, 24, 0),
    0x08: (32, 42, 0),     0x09: (8, 58, 0),      0x0A: (0, 64, 0),      0x0B: (0, 60, 0),
    0x0C: (0, 50, 60),     0x0D: (0, 0, 0),       0x0E: (0, 0, 0),       0x0F: (0, 0, 0),
    0x10: (152, 150, 152), 0x11: (8, 76, 196),    0x12: (48, 50, 236),   0x13: (92, 30, 228),
    0x14: (136, 20, 176),  0x15: (160, 20, 100),  0x16: (152, 34, 32),   0x17: (120, 60, 0),
    0x18: (84, 90, 0),     0x19: (40, 114, 0),    0x1A: (8, 124, 0),     0x1B: (0, 118, 40),
    0x1C: (0, 102, 120),   0x1D: (0, 0, 0),       0x1E: (0, 0, 0),       0x1F: (0, 0, 0),
    0x20: (236, 238, 236), 0x21: (76, 154, 236),  0x22: (120, 124, 236), 0x23: (176, 98, 236),
    0x24: (228, 84, 236),  0x25: (236, 88, 180),  0x26: (236, 106, 100), 0x27: (212, 136, 32),
    0x28: (160, 170, 0),   0x29: (116, 196, 0),   0x2A: (76, 208, 32),   0x2B: (56, 204, 108),
    0x2C: (56, 180, 204),  0x2D: (60, 60, 60),    0x2E: (0, 0, 0),       0x2F: (0, 0, 0),
    0x30: (236, 238, 236), 0x31: (168, 204, 236), 0x32: (188, 188, 236), 0x33: (212, 178, 236),
    0x34: (236, 174, 236), 0x35: (236, 174, 212), 0x36: (236, 180, 176), 0x37: (228, 196, 144),
    0x38: (204, 210, 120), 0x39: (180, 222, 120), 0x3A: (168, 226, 144), 0x3B: (152, 226, 180),
    0x3C: (160, 214, 228), 0x3D: (160, 162, 160), 0x3E: (0, 0, 0),       0x3F: (0, 0, 0),
}

@dataclass
class Sprite:
    """Represents a detected sprite in the sheet"""
    name: str
    x: int
    y: int
    width: int
    height: int
    tiles: List[int] = field(default_factory=list)  # Tile indices after processing
    palette: List[int] = field(default_factory=list)  # NES palette indices used

@dataclass
class CHROutput:
    """Output from CHR generation"""
    chr_data: bytes
    sprites: List[Sprite]
    tile_count: int
    palette_used: List[int]


def rgb_to_nes_index(r: int, g: int, b: int) -> int:
    """Find closest NES palette color to given RGB"""
    min_dist = float('inf')
    best_idx = 0x0F  # Default to black

    for idx, (pr, pg, pb) in NES_PALETTE.items():
        dist = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2
        if dist < min_dist:
            min_dist = dist
            best_idx = idx

    return best_idx


def quantize_to_nes_palette(img: Image.Image, palette_indices: Optional[List[int]] = None) -> Tuple[Image.Image, List[int]]:
    """
    Quantize image to NES palette (max 4 colors for sprites).

    Args:
        img: Source image (RGBA or RGB)
        palette_indices: Optional fixed palette to use (4 NES color indices)

    Returns:
        Tuple of (indexed image with values 0-3, list of NES palette indices used)
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    pixels = np.array(img)
    height, width = pixels.shape[:2]

    # Collect unique colors (ignoring fully transparent)
    colors_found = {}
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[y, x]
            if a < 128:  # Transparent
                continue
            nes_idx = rgb_to_nes_index(r, g, b)
            if nes_idx not in colors_found:
                colors_found[nes_idx] = 0
            colors_found[nes_idx] += 1

    # If palette provided, use it; otherwise select top 3 colors + transparent
    if palette_indices:
        palette = palette_indices[:4]
    else:
        # Sort by frequency, take top 3
        sorted_colors = sorted(colors_found.items(), key=lambda x: -x[1])
        palette = [0x0F]  # Index 0 is always transparent (black)
        for idx, _ in sorted_colors[:3]:
            if idx != 0x0F:
                palette.append(idx)
        while len(palette) < 4:
            palette.append(0x0F)

    # Create indexed image
    indexed = Image.new('L', (width, height), 0)
    indexed_pixels = indexed.load()

    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[y, x]
            if a < 128:
                indexed_pixels[x, y] = 0  # Transparent = index 0
            else:
                nes_idx = rgb_to_nes_index(r, g, b)
                # Find closest palette entry
                if nes_idx in palette:
                    indexed_pixels[x, y] = palette.index(nes_idx)
                else:
                    # Find closest in palette
                    nes_rgb = NES_PALETTE[nes_idx]
                    min_dist = float('inf')
                    best = 0
                    for i, pal_idx in enumerate(palette):
                        pal_rgb = NES_PALETTE[pal_idx]
                        dist = sum((a - b) ** 2 for a, b in zip(nes_rgb, pal_rgb))
                        if dist < min_dist:
                            min_dist = dist
                            best = i
                    indexed_pixels[x, y] = best

    return indexed, palette


def extract_8x8_tile(indexed_img: Image.Image, x: int, y: int) -> bytes:
    """
    Extract a single 8x8 tile from indexed image in NES CHR format.

    NES CHR format: 16 bytes per tile
    - Bytes 0-7: Bit plane 0 (low bit of each pixel)
    - Bytes 8-15: Bit plane 1 (high bit of each pixel)
    """
    pixels = indexed_img.load()
    width, height = indexed_img.size

    plane0 = bytearray(8)
    plane1 = bytearray(8)

    for row in range(8):
        for col in range(8):
            px = x + col
            py = y + row

            if px < width and py < height:
                color = pixels[px, py] & 0x03
            else:
                color = 0

            if color & 1:
                plane0[row] |= (0x80 >> col)
            if color & 2:
                plane1[row] |= (0x80 >> col)

    return bytes(plane0 + plane1)


def process_16x16_metasprite(indexed_img: Image.Image, x: int, y: int) -> List[bytes]:
    """
    Extract a 16x16 metasprite as 4 tiles in correct order.

    Order: Top-Left, Top-Right, Bottom-Left, Bottom-Right
    This matches how NES games typically arrange metasprite tiles.
    """
    tiles = []

    # Top-Left (0, 0)
    tiles.append(extract_8x8_tile(indexed_img, x, y))
    # Top-Right (8, 0)
    tiles.append(extract_8x8_tile(indexed_img, x + 8, y))
    # Bottom-Left (0, 8)
    tiles.append(extract_8x8_tile(indexed_img, x, y + 8))
    # Bottom-Right (8, 8)
    tiles.append(extract_8x8_tile(indexed_img, x + 8, y + 8))

    return tiles


def detect_sprites_in_sheet(img: Image.Image, sprite_width: int, sprite_height: int) -> List[Tuple[int, int]]:
    """
    Detect sprite positions in a sheet, skipping empty cells.

    Args:
        img: Source image (RGBA)
        sprite_width: Width of each sprite cell
        sprite_height: Height of each sprite cell

    Returns:
        List of (x, y) positions for non-empty sprites
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    pixels = np.array(img)
    height, width = pixels.shape[:2]

    sprites = []

    for sy in range(0, height, sprite_height):
        for sx in range(0, width, sprite_width):
            # Check if this cell has any non-transparent pixels
            has_content = False
            for y in range(sy, min(sy + sprite_height, height)):
                for x in range(sx, min(sx + sprite_width, width)):
                    if pixels[y, x, 3] >= 128:  # Alpha threshold
                        has_content = True
                        break
                if has_content:
                    break

            if has_content:
                sprites.append((sx, sy))

    return sprites


def generate_chr_from_sheet(
    img_path: str,
    sprite_size: Tuple[int, int] = (16, 16),
    palette: Optional[List[int]] = None,
    sprite_names: Optional[List[str]] = None
) -> CHROutput:
    """
    Generate CHR data from a sprite sheet.

    Args:
        img_path: Path to sprite sheet image
        sprite_size: (width, height) of each sprite
        palette: Optional fixed NES palette indices
        sprite_names: Optional names for sprites (in order)

    Returns:
        CHROutput with CHR data and sprite metadata
    """
    img = Image.open(img_path)
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    sprite_w, sprite_h = sprite_size

    # Detect sprites in sheet
    sprite_positions = detect_sprites_in_sheet(img, sprite_w, sprite_h)

    if not sprite_positions:
        raise ValueError("No sprites detected in sheet")

    print(f"Detected {len(sprite_positions)} sprites in sheet")

    # Quantize entire image to NES palette
    indexed, palette_used = quantize_to_nes_palette(img, palette)

    chr_data = bytearray()
    sprites = []
    tile_idx = 0

    for i, (sx, sy) in enumerate(sprite_positions):
        name = sprite_names[i] if sprite_names and i < len(sprite_names) else f"sprite_{i}"

        sprite = Sprite(
            name=name,
            x=sx,
            y=sy,
            width=sprite_w,
            height=sprite_h,
            palette=palette_used
        )

        if sprite_w == 16 and sprite_h == 16:
            # 16x16 metasprite
            tiles = process_16x16_metasprite(indexed, sx, sy)
            for tile_data in tiles:
                chr_data.extend(tile_data)
                sprite.tiles.append(tile_idx)
                tile_idx += 1
        elif sprite_w == 8 and sprite_h == 8:
            # Single 8x8 tile
            tile_data = extract_8x8_tile(indexed, sx, sy)
            chr_data.extend(tile_data)
            sprite.tiles.append(tile_idx)
            tile_idx += 1
        else:
            # Generic size - process as grid of 8x8 tiles
            for ty in range(0, sprite_h, 8):
                for tx in range(0, sprite_w, 8):
                    tile_data = extract_8x8_tile(indexed, sx + tx, sy + ty)
                    chr_data.extend(tile_data)
                    sprite.tiles.append(tile_idx)
                    tile_idx += 1

        sprites.append(sprite)

    # Pad to 8KB bank if needed
    while len(chr_data) < 8192:
        chr_data.extend(bytes(16))  # Empty tile

    return CHROutput(
        chr_data=bytes(chr_data[:8192]),  # Cap at 8KB
        sprites=sprites,
        tile_count=tile_idx,
        palette_used=palette_used
    )


def generate_chr_from_individual_sprites(
    sprite_paths: List[str],
    sprite_names: Optional[List[str]] = None,
    palette: Optional[List[int]] = None
) -> CHROutput:
    """
    Generate CHR data from individual sprite image files.

    Args:
        sprite_paths: List of paths to sprite images
        sprite_names: Optional names for sprites
        palette: Optional fixed NES palette indices

    Returns:
        CHROutput with CHR data and sprite metadata
    """
    chr_data = bytearray()
    sprites = []
    tile_idx = 0
    palette_used = palette or [0x0F, 0x20, 0x10, 0x00]  # Default: black, white, gray, black

    for i, path in enumerate(sprite_paths):
        img = Image.open(path)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        width, height = img.size
        name = sprite_names[i] if sprite_names and i < len(sprite_names) else Path(path).stem

        # Quantize to palette
        indexed, pal = quantize_to_nes_palette(img, palette_used)
        if not palette:
            palette_used = pal  # Use detected palette from first sprite

        sprite = Sprite(
            name=name,
            x=0,
            y=0,
            width=width,
            height=height,
            palette=palette_used
        )

        if width == 16 and height == 16:
            tiles = process_16x16_metasprite(indexed, 0, 0)
            for tile_data in tiles:
                chr_data.extend(tile_data)
                sprite.tiles.append(tile_idx)
                tile_idx += 1
        elif width == 8 and height == 8:
            tile_data = extract_8x8_tile(indexed, 0, 0)
            chr_data.extend(tile_data)
            sprite.tiles.append(tile_idx)
            tile_idx += 1
        else:
            # Process as grid
            for ty in range(0, height, 8):
                for tx in range(0, width, 8):
                    tile_data = extract_8x8_tile(indexed, tx, ty)
                    chr_data.extend(tile_data)
                    sprite.tiles.append(tile_idx)
                    tile_idx += 1

        sprites.append(sprite)
        print(f"  {name}: {width}x{height} -> tiles {sprite.tiles}")

    # Pad to 8KB
    while len(chr_data) < 8192:
        chr_data.extend(bytes(16))

    return CHROutput(
        chr_data=bytes(chr_data[:8192]),
        sprites=sprites,
        tile_count=tile_idx,
        palette_used=palette_used
    )


def generate_assembly_include(output: CHROutput, output_path: str):
    """Generate assembly include file with sprite/tile definitions."""
    lines = [
        "; =============================================================================",
        "; NES CHR Tile Definitions",
        "; Generated by nes_chr_tool.py",
        "; =============================================================================",
        "",
        "; Palette used (NES color indices):",
        f";   Color 0 (transparent): ${output.palette_used[0]:02X}",
        f";   Color 1: ${output.palette_used[1]:02X}",
        f";   Color 2: ${output.palette_used[2]:02X}",
        f";   Color 3: ${output.palette_used[3]:02X}",
        "",
        f"; Total tiles: {output.tile_count}",
        "",
    ]

    for sprite in output.sprites:
        lines.append(f"; {sprite.name} ({sprite.width}x{sprite.height})")

        # Create constants for tile indices
        safe_name = sprite.name.upper().replace(' ', '_').replace('-', '_')

        if len(sprite.tiles) == 1:
            lines.append(f"TILE_{safe_name} = ${sprite.tiles[0]:02X}")
        elif len(sprite.tiles) == 4:
            # 16x16 metasprite
            lines.append(f"TILE_{safe_name}_TL = ${sprite.tiles[0]:02X}")
            lines.append(f"TILE_{safe_name}_TR = ${sprite.tiles[1]:02X}")
            lines.append(f"TILE_{safe_name}_BL = ${sprite.tiles[2]:02X}")
            lines.append(f"TILE_{safe_name}_BR = ${sprite.tiles[3]:02X}")
            lines.append(f"TILE_{safe_name}_BASE = ${sprite.tiles[0]:02X}")
        else:
            for j, tile in enumerate(sprite.tiles):
                lines.append(f"TILE_{safe_name}_{j} = ${tile:02X}")

        lines.append("")

    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))

    print(f"Generated assembly include: {output_path}")


def generate_json_metadata(output: CHROutput, output_path: str):
    """Generate JSON metadata file."""
    data = {
        'tile_count': output.tile_count,
        'palette': [f"${x:02X}" for x in output.palette_used],
        'sprites': []
    }

    for sprite in output.sprites:
        data['sprites'].append({
            'name': sprite.name,
            'width': sprite.width,
            'height': sprite.height,
            'tiles': sprite.tiles,
            'tile_base': sprite.tiles[0] if sprite.tiles else 0
        })

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"Generated JSON metadata: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='NES CHR Tool - Generate pixel-perfect CHR files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a sprite sheet with 16x16 sprites
  python nes_chr_tool.py sprites.png -o sprites.chr --sprite-size 16x16

  # Process individual sprite files
  python nes_chr_tool.py player.png enemy.png bullet.png -o sprites.chr

  # Specify sprite names
  python nes_chr_tool.py sheet.png -o sprites.chr --names player,enemy,bullet

  # Use a specific NES palette
  python nes_chr_tool.py sprites.png -o sprites.chr --palette 0F,16,27,30
        """
    )

    parser.add_argument('inputs', nargs='+', help='Input image(s)')
    parser.add_argument('-o', '--output', required=True, help='Output CHR file')
    parser.add_argument('--sprite-size', default='16x16',
                        help='Sprite size for sheet mode (e.g., 16x16, 8x8, 32x32)')
    parser.add_argument('--names', help='Comma-separated sprite names')
    parser.add_argument('--palette', help='NES palette indices (e.g., 0F,16,27,30)')
    parser.add_argument('--no-asm', action='store_true', help='Skip assembly include generation')
    parser.add_argument('--no-json', action='store_true', help='Skip JSON metadata generation')

    args = parser.parse_args()

    # Parse sprite size
    try:
        w, h = args.sprite_size.lower().split('x')
        sprite_size = (int(w), int(h))
    except:
        print(f"Invalid sprite size: {args.sprite_size}")
        sys.exit(1)

    # Parse palette
    palette = None
    if args.palette:
        try:
            palette = [int(x, 16) for x in args.palette.split(',')]
            if len(palette) != 4:
                print("Palette must have exactly 4 colors")
                sys.exit(1)
        except:
            print(f"Invalid palette format: {args.palette}")
            sys.exit(1)

    # Parse names
    names = args.names.split(',') if args.names else None

    # Process
    print(f"NES CHR Tool")
    print(f"============")

    if len(args.inputs) == 1 and not args.inputs[0].endswith('.png'):
        print(f"Error: Input must be PNG image(s)")
        sys.exit(1)

    if len(args.inputs) == 1:
        # Single file - treat as sprite sheet
        print(f"Processing sprite sheet: {args.inputs[0]}")
        print(f"Sprite size: {sprite_size[0]}x{sprite_size[1]}")
        output = generate_chr_from_sheet(args.inputs[0], sprite_size, palette, names)
    else:
        # Multiple files - individual sprites
        print(f"Processing {len(args.inputs)} individual sprites")
        output = generate_chr_from_individual_sprites(args.inputs, names, palette)

    # Write CHR file
    with open(args.output, 'wb') as f:
        f.write(output.chr_data)
    print(f"Generated CHR: {args.output} ({len(output.chr_data)} bytes, {output.tile_count} tiles)")

    # Generate assembly include
    if not args.no_asm:
        asm_path = str(Path(args.output).with_suffix('.inc'))
        generate_assembly_include(output, asm_path)

    # Generate JSON metadata
    if not args.no_json:
        json_path = str(Path(args.output).with_suffix('.json'))
        generate_json_metadata(output, json_path)

    print(f"\nSprites processed:")
    for sprite in output.sprites:
        print(f"  {sprite.name}: tiles {sprite.tiles}")

    print(f"\nPalette: {', '.join(f'${x:02X}' for x in output.palette_used)}")


if __name__ == '__main__':
    main()
