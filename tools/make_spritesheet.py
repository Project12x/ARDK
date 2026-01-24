#!/usr/bin/env python3
"""
NEON SURVIVORS - Sprite Sheet Assembler
Combines individual sprites into a tile-aligned sprite sheet
ready for CHR conversion with established tools (NEXXT, YY-CHR, etc.)

Supports both RGB output (for manual tools) and indexed PNG output (for img2chr).
Uses project config from .ardk.yaml if available.
"""

from PIL import Image
import json
from pathlib import Path

# Try to load pipeline config and CLI utilities
try:
    from pipeline.core import get_config
    from pipeline.cli_utils import (
        create_parser,
        add_common_args,
        setup_from_args,
        print_config_status,
        print_dry_run_notice,
        VerbosePrinter,
    )
    HAS_CONFIG = True
except ImportError:
    HAS_CONFIG = False

# NES 4-color palette for indexed output
NES_PALETTE = [
    (0, 0, 0),         # 0: Black (transparent)
    (85, 85, 85),      # 1: Dark gray
    (170, 170, 170),   # 2: Light gray
    (255, 255, 255),   # 3: White
]


def quantize_to_palette(color):
    """Map RGB color to nearest 4-color palette index."""
    r, g, b = color[:3]  # Handle both RGB and RGBA

    # Very dark -> black
    if r < 64 and g < 64 and b < 64:
        return 0

    # Very bright -> white
    if r > 200 or g > 200 or b > 200:
        return 3

    # Blue-dominant -> light gray
    if b > g and b > r:
        return 2

    # Default -> dark gray
    return 1


def convert_to_indexed(rgb_sheet):
    """Convert RGB sheet to 4-color indexed PNG."""
    indexed = Image.new('P', rgb_sheet.size)

    # Build palette data (pad to 256 colors)
    palette_data = []
    for color in NES_PALETTE:
        palette_data.extend(color)
    palette_data.extend([0] * (768 - len(palette_data)))
    indexed.putpalette(palette_data)

    # Convert pixels
    rgb_pixels = rgb_sheet.convert('RGB').load()
    indexed_pixels = indexed.load()

    for y in range(rgb_sheet.height):
        for x in range(rgb_sheet.width):
            palette_idx = quantize_to_palette(rgb_pixels[x, y])
            indexed_pixels[x, y] = palette_idx

    return indexed


def get_paths_from_config():
    """Get paths from project config or use defaults."""
    if HAS_CONFIG:
        try:
            config = get_config()
            # Get project root
            project_root = Path(config.project_root) if config.project_root else Path.cwd().parent
            return {
                'sprite_dir': project_root / config.paths.generated,
                'output_dir': project_root / config.paths.generated,
                'asm_dir': project_root / config.paths.asm_output,
            }
        except Exception:
            pass

    # Defaults (relative to tools folder)
    return {
        'sprite_dir': Path("gfx/generated"),
        'output_dir': Path("gfx/generated"),
        'asm_dir': Path("src/game/assets"),
    }


def create_sprite_sheet(output_indexed=False, sprite_dir=None, output_dir=None, asm_dir=None):
    """
    Assemble sprites into 128x128 pixel sheet (16x16 tiles)
    This is a standard size for easy CHR conversion

    Args:
        output_indexed: Also output 4-color indexed PNG
        sprite_dir: Override sprite input directory
        output_dir: Override output directory
        asm_dir: Override ASM output directory
    """
    # Get paths from config or use provided overrides
    paths = get_paths_from_config()
    sprite_dir = Path(sprite_dir) if sprite_dir else paths['sprite_dir']
    output_dir = Path(output_dir) if output_dir else paths['output_dir']
    asm_dir = Path(asm_dir) if asm_dir else paths['asm_dir']

    # Create blank sprite sheet (128x128 = 16x16 tiles of 8x8 each)
    sheet_width = 128
    sheet_height = 128
    sheet = Image.new('RGB', (sheet_width, sheet_height), (0, 0, 0))

    # Ensure output directories exist
    output_dir.mkdir(parents=True, exist_ok=True)
    asm_dir.mkdir(parents=True, exist_ok=True)

    # Tile layout map
    # Format: (tile_x, tile_y, width_tiles, height_tiles): sprite_filename
    layout = {
        # Player (16x16 = 2x2 tiles) at top-left
        (0, 0, 2, 2): 'player_rad_dude.png',

        # Enemies
        (2, 0, 1, 1): 'enemy_bit_drone.png',      # Tile $02
        (3, 0, 2, 2): 'enemy_neon_skull.png',     # Tiles $03-$06 (2x2)

        # Pickups and weapons
        (0, 2, 1, 1): 'pickup_xp_gem.png',        # Tile $20 (row 2)
        (1, 2, 1, 1): 'weapon_laser.png',         # Tile $21
    }

    # Tile map for reference
    tile_map = {}

    print("=" * 60)
    print("NEON SURVIVORS - Sprite Sheet Assembly")
    print("=" * 60)
    print()

    # Place each sprite
    for (tile_x, tile_y, w_tiles, h_tiles), filename in layout.items():
        sprite_path = sprite_dir / filename

        if not sprite_path.exists():
            print(f"[WARN] Warning: {filename} not found, skipping")
            continue

        # Load sprite
        sprite = Image.open(sprite_path)

        # Calculate pixel position
        px_x = tile_x * 8
        px_y = tile_y * 8

        # Paste sprite onto sheet
        sheet.paste(sprite, (px_x, px_y))

        # Calculate tile index
        tile_idx = tile_y * 16 + tile_x

        # Store in tile map
        sprite_name = filename.replace('.png', '')
        tile_map[sprite_name] = {
            'tile_index': f'${tile_idx:02X}',
            'position': (tile_x, tile_y),
            'size_tiles': (w_tiles, h_tiles),
            'size_pixels': (w_tiles * 8, h_tiles * 8)
        }

        print(f"[OK] Placed {filename}")
        print(f"  Position: Tile ({tile_x}, {tile_y}) = ${tile_idx:02X}")
        print(f"  Size: {w_tiles}x{h_tiles} tiles ({sprite.width}x{sprite.height} px)")
        print()

    # Save sprite sheet (RGB version)
    output_path = output_dir / "neon_survivors_sheet.png"
    sheet.save(output_path)

    # Also save 4x scaled version for easier viewing/editing
    scaled = sheet.resize((sheet_width * 4, sheet_height * 4), Image.NEAREST)
    scaled_path = output_dir / "neon_survivors_sheet_4x.png"
    scaled.save(scaled_path)

    # Save indexed version if requested
    indexed_path = None
    if output_indexed:
        indexed = convert_to_indexed(sheet)
        indexed_path = output_dir / "neon_survivors_indexed.png"
        indexed.save(indexed_path)

        # Verify color count
        colors = set()
        indexed_pixels = indexed.load()
        for y in range(indexed.height):
            for x in range(indexed.width):
                colors.add(indexed_pixels[x, y])

        print(f"[OK] Indexed version: {indexed_path}")
        print(f"     Colors used: {len(colors)} (max 4)")
        print(f"     Palette indices: {sorted(colors)}")
        print()

    # Save tile map as JSON for reference
    map_path = output_dir / "tile_map.json"
    with open(map_path, 'w') as f:
        json.dump(tile_map, f, indent=2)

    # Generate assembly include file with tile definitions
    asm_path = asm_dir / "sprite_tiles.inc"
    with open(asm_path, 'w') as f:
        f.write("; =============================================================================\n")
        f.write("; NEON SURVIVORS - Sprite Tile Definitions\n")
        f.write("; Auto-generated by make_spritesheet.py\n")
        f.write("; =============================================================================\n\n")

        for sprite_name, data in sorted(tile_map.items()):
            const_name = sprite_name.upper().replace('-', '_')
            tile_hex = data['tile_index']
            f.write(f"TILE_{const_name} = {tile_hex}\n")

        f.write("\n; End of sprite tile definitions\n")

    print("=" * 60)
    print("[OK] Sprite Sheet Assembly Complete!")
    print("=" * 60)
    print()
    print(f"Output files:")
    print(f"  {output_path} (128x128 - RGB for manual editing)")
    print(f"  {scaled_path} (scaled for viewing)")
    if indexed_path:
        print(f"  {indexed_path} (indexed - ready for img2chr)")
    print(f"  {map_path} (tile map reference)")
    print(f"  {asm_path} (ASM constants)")
    print()

    if indexed_path:
        print("Next steps (using img2chr):")
        print(f"  img2chr {indexed_path} sprites.chr")
        print()
    else:
        print("Next steps (using manual tools):")
        print("1. Open neon_survivors_sheet.png in NEXXT or YY-CHR")
        print("2. Set palette to match NES colors:")
        print("   - Color 0: Black (transparent)")
        print("   - Color 1: Magenta ($15)")
        print("   - Color 2: Cyan ($21)")
        print("   - Color 3: White ($30)")
        print("3. Export as sprites.chr (8KB)")
        print()
        print("Tip: Use --indexed flag for img2chr-ready output")
        print()

    print("4. Copy to src/game/assets/sprites.chr")
    print("5. Rebuild ROM with compile.bat")
    print("=" * 60)

    return output_path, tile_map, indexed_path


if __name__ == "__main__":
    if HAS_CONFIG:
        # Use shared CLI utilities
        parser = create_parser("Assemble sprites into a tile-aligned sprite sheet")
        add_common_args(parser)

        # Tool-specific args
        parser.add_argument(
            '--indexed', '-i',
            action='store_true',
            help='Also output 4-color indexed PNG for img2chr'
        )
        parser.add_argument(
            '--sprite-dir',
            metavar='DIR',
            help='Override sprite input directory'
        )
        parser.add_argument(
            '--asm-dir',
            metavar='DIR',
            help='Override ASM output directory'
        )

        args = parser.parse_args()
        config, verbosity = setup_from_args(args)
        vprint = VerbosePrinter(verbosity)

        # Show config status
        print_config_status(config, verbosity)

        # Get output dir from --output or config
        output_dir = args.output if hasattr(args, 'output') and args.output else None

        create_sprite_sheet(
            output_indexed=args.indexed,
            sprite_dir=args.sprite_dir,
            output_dir=output_dir,
            asm_dir=args.asm_dir
        )

        # Dry-run notice
        if config.safeguards.dry_run:
            print_dry_run_notice()
    else:
        # Fallback without pipeline module
        import argparse
        parser = argparse.ArgumentParser(
            description="Assemble sprites into a tile-aligned sprite sheet"
        )
        parser.add_argument('--indexed', '-i', action='store_true',
                           help='Also output 4-color indexed PNG')
        parser.add_argument('--sprite-dir', help='Sprite input directory')
        parser.add_argument('--output-dir', '-o', help='Output directory')
        parser.add_argument('--asm-dir', help='ASM output directory')
        args = parser.parse_args()

        create_sprite_sheet(
            output_indexed=args.indexed,
            sprite_dir=args.sprite_dir,
            output_dir=args.output_dir,
            asm_dir=args.asm_dir
        )
