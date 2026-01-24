#!/usr/bin/env python3
"""
Combine multiple CHR files into a single 8KB CHR bank
"""

import sys
import os

def combine_chr_files(output_path, *input_paths):
    """
    Combine multiple CHR files into one.
    Each input is concatenated in order.
    Pads to 8KB (8192 bytes) if needed.
    """
    combined_data = bytearray()

    print(f"Combining CHR files into: {output_path}")
    print("=" * 60)

    for input_path in input_paths:
        if not os.path.exists(input_path):
            print(f"WARNING: {input_path} not found, skipping")
            continue

        with open(input_path, 'rb') as f:
            data = f.read()
            combined_data.extend(data)
            print(f"  Added {input_path}: {len(data)} bytes ({len(data)//16} tiles)")

    # Calculate how many tiles we have
    total_tiles = len(combined_data) // 16
    print()
    print(f"Total: {len(combined_data)} bytes ({total_tiles} tiles)")

    # Pad to 8KB if needed (512 tiles)
    target_size = 8192  # 8KB = 512 tiles
    if len(combined_data) < target_size:
        padding_needed = target_size - len(combined_data)
        combined_data.extend(bytes(padding_needed))
        print(f"Padded with {padding_needed} bytes to reach 8KB")
    elif len(combined_data) > target_size:
        print(f"WARNING: Combined size ({len(combined_data)} bytes) exceeds 8KB!")
        print(f"Truncating to 8KB...")
        combined_data = combined_data[:target_size]

    # Write combined file
    with open(output_path, 'wb') as f:
        f.write(combined_data)

    print("=" * 60)
    print(f"[OK] Created {output_path}: {len(combined_data)} bytes")
    print()
    print("Tile Layout:")
    tiles_per_chr = 256  # 4KB = 256 tiles
    current_tile = 0

    for i, input_path in enumerate(input_paths):
        if os.path.exists(input_path):
            chr_size = os.path.getsize(input_path)
            chr_tiles = chr_size // 16
            print(f"  ${current_tile:02X}-${current_tile + chr_tiles - 1:02X}: {os.path.basename(input_path)} ({chr_tiles} tiles)")
            current_tile += chr_tiles

    if current_tile < 512:
        print(f"  ${current_tile:02X}-$1FF: Empty/padding ({512 - current_tile} tiles)")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python combine_chr.py <output.chr> <input1.chr> [input2.chr] ...")
        print()
        print("Example:")
        print("  python tools/combine_chr.py src/game/assets/sprites.chr \\")
        print("    src/game/assets/player.chr \\")
        print("    src/game/assets/items.chr \\")
        print("    src/game/assets/enemies.chr")
        sys.exit(1)

    output_file = sys.argv[1]
    input_files = sys.argv[2:]

    combine_chr_files(output_file, *input_files)
