#!/usr/bin/env python3
"""
Generate a catalog of all processed sprites

Scans the processed sprite directories and creates:
1. A markdown catalog listing all sprites by category
2. A JSON index for programmatic access
3. A sprite_tiles.inc file for NES assembly

Usage:
    python tools/generate_sprite_catalog.py gfx/processed/batch --output docs/SPRITE_CATALOG.md
"""

import os
import json
import argparse
from pathlib import Path
from collections import defaultdict

def scan_sprite_directories(base_path):
    """Scan processed sprite directories and collect metadata"""

    sprites_by_category = defaultdict(lambda: defaultdict(list))
    all_sprites = []

    base = Path(base_path)

    # Find all metadata.json files
    for metadata_file in base.rglob('metadata.json'):
        try:
            with open(metadata_file) as f:
                metadata = json.load(f)

            sheet_name = metadata_file.parent.name

            for sprite in metadata.get('sprites', []):
                category = f"{sprite['type']}/{sprite.get('action', 'default')}"

                sprite_info = {
                    'sheet': sheet_name,
                    'id': sprite['id'],
                    'type': sprite['type'],
                    'action': sprite.get('action', 'default'),
                    'description': sprite.get('description', 'Unknown'),
                    'chr_file': sprite['chr_file'],
                    'png_file': sprite.get('png_file', ''),
                    'size': sprite['size'],
                    'tiles': sprite['tile_count'],
                    'palette': sprite['palette']
                }

                sprites_by_category[sprite['type']][sprite.get('action', 'default')].append(sprite_info)
                all_sprites.append(sprite_info)

        except Exception as e:
            print(f"Warning: Failed to read {metadata_file}: {e}")

    return sprites_by_category, all_sprites

def generate_markdown_catalog(sprites_by_category, output_path):
    """Generate a markdown catalog document"""

    with open(output_path, 'w') as f:
        f.write("# NEON SURVIVORS - Sprite Catalog\n\n")
        f.write("**Auto-generated sprite catalog from AI processing**\n\n")
        f.write("---\n\n")

        # Summary statistics
        total_sprites = sum(
            len(sprites)
            for actions in sprites_by_category.values()
            for sprites in actions.values()
        )

        f.write("## Summary\n\n")
        f.write(f"- **Total Sprites**: {total_sprites}\n")
        f.write(f"- **Categories**: {len(sprites_by_category)}\n")
        f.write("\n")

        # Table of contents
        f.write("## Table of Contents\n\n")
        for sprite_type in sorted(sprites_by_category.keys()):
            f.write(f"- [{sprite_type.title()}](#{sprite_type})\n")
        f.write("\n---\n\n")

        # Detailed listings
        for sprite_type in sorted(sprites_by_category.keys()):
            f.write(f"## {sprite_type.title()}\n\n")

            actions = sprites_by_category[sprite_type]

            for action in sorted(actions.keys()):
                sprites = actions[action]

                f.write(f"### {action.title()}\n\n")
                f.write(f"**{len(sprites)} sprite(s)**\n\n")

                for sprite in sprites:
                    f.write(f"#### {sprite['description']}\n\n")
                    f.write(f"- **Source**: `{sprite['sheet']}`\n")
                    f.write(f"- **Size**: {sprite['size'][0]}x{sprite['size'][1]} ({sprite['tiles']} tiles)\n")
                    f.write(f"- **Palette**: {', '.join(f'${c:02X}' for c in sprite['palette'])}\n")
                    f.write(f"- **CHR**: `{sprite['chr_file']}`\n")
                    if sprite['png_file']:
                        f.write(f"- **Preview**: `{sprite['png_file']}`\n")
                    f.write("\n")

                f.write("\n")

    print(f"Generated markdown catalog: {output_path}")

def generate_json_index(all_sprites, output_path):
    """Generate a JSON index for programmatic access"""

    index = {
        'version': '1.0',
        'generated': 'auto',
        'total_sprites': len(all_sprites),
        'sprites': all_sprites
    }

    with open(output_path, 'w') as f:
        json.dump(index, f, indent=2)

    print(f"Generated JSON index: {output_path}")

def generate_asm_include(sprites_by_category, output_path):
    """Generate sprite_tiles.inc for NES assembly"""

    with open(output_path, 'w') as f:
        f.write("; =============================================================================\n")
        f.write("; NEON SURVIVORS - Sprite Tile Definitions\n")
        f.write("; Auto-generated from AI sprite processing\n")
        f.write("; =============================================================================\n\n")

        tile_index = 0

        for sprite_type in sorted(sprites_by_category.keys()):
            f.write(f"; {sprite_type.upper()} SPRITES\n")
            f.write(f"; {'-' * 60}\n\n")

            actions = sprites_by_category[sprite_type]

            for action in sorted(actions.keys()):
                sprites = actions[action]

                for sprite in sprites:
                    # Create constant name
                    safe_name = sprite['description'].upper()
                    safe_name = safe_name.replace(' ', '_').replace('-', '_')
                    safe_name = ''.join(c for c in safe_name if c.isalnum() or c == '_')

                    const_name = f"TILE_{sprite_type.upper()}_{action.upper()}_{safe_name}"

                    # Calculate tile layout
                    width_tiles = sprite['size'][0] // 8
                    height_tiles = sprite['size'][1] // 8

                    f.write(f"; {sprite['description']}\n")
                    f.write(f"{const_name}_START = ${tile_index:02X}\n")
                    f.write(f"{const_name}_WIDTH = {width_tiles}  ; {sprite['size'][0]}px\n")
                    f.write(f"{const_name}_HEIGHT = {height_tiles}  ; {sprite['size'][1]}px\n")
                    f.write(f"{const_name}_TILES = {sprite['tiles']}\n")
                    f.write(f"; Palette: {', '.join(f'${c:02X}' for c in sprite['palette'])}\n")
                    f.write("\n")

                    tile_index += sprite['tiles']

            f.write("\n")

    print(f"Generated ASM include: {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Generate sprite catalog from processed sprites')
    parser.add_argument('base_path', help='Base path to processed sprites (e.g., gfx/processed/batch)')
    parser.add_argument('--output', '-o', default='docs/SPRITE_CATALOG.md', help='Output markdown file')
    parser.add_argument('--json', help='Output JSON index file')
    parser.add_argument('--asm', help='Output ASM include file')

    args = parser.parse_args()

    print("Scanning sprite directories...")
    sprites_by_category, all_sprites = scan_sprite_directories(args.base_path)

    if not all_sprites:
        print("No sprites found!")
        return

    print(f"\nFound {len(all_sprites)} sprites in {len(sprites_by_category)} categories")

    # Generate markdown catalog
    output_dir = Path(args.output).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    generate_markdown_catalog(sprites_by_category, args.output)

    # Generate JSON index if requested
    if args.json:
        generate_json_index(all_sprites, args.json)

    # Generate ASM include if requested
    if args.asm:
        generate_asm_include(sprites_by_category, args.asm)

    print("\nCatalog generation complete!")
    print(f"\nSummary by category:")
    for sprite_type, actions in sorted(sprites_by_category.items()):
        count = sum(len(sprites) for sprites in actions.values())
        print(f"  {sprite_type}: {count} sprites")

if __name__ == '__main__':
    main()
