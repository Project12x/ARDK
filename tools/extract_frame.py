#!/usr/bin/env python3
"""
Extract a single 32x32 sprite frame from player_rad_90s.png and convert to NES CHR.

The sprite sheet has:
- Row 1 (IDLE): 6 frames at y~32-90
- Row 2 (RUN SIDE): 6 frames at y~212-280
- Row 3 (SHOOT): 2 frames at y~372-440

Each frame is approximately 64x64 pixels (scaled 2x from 32x32).
"""

from PIL import Image
import sys
import os

# NES palette mapping - map RGB colors to palette indices
# Based on the source image: Black(bg), Magenta, Cyan, White
NES_PALETTE = {
    (0, 0, 0): 0,        # Black/transparent
    (255, 0, 255): 1,    # Magenta
    (0, 255, 255): 2,    # Cyan
    (255, 255, 255): 3,  # White
}

def find_closest_color(rgb, palette):
    """Find the closest palette color for a given RGB value."""
    r, g, b = rgb[:3]  # Handle RGBA

    # Direct match first
    if (r, g, b) in palette:
        return palette[(r, g, b)]

    # Threshold-based mapping
    brightness = (r + g + b) / 3

    # Very dark = black (0)
    if brightness < 40:
        return 0

    # Check for magenta (high R, low G, high B)
    if r > 150 and g < 100 and b > 150:
        return 1  # Magenta

    # Check for cyan (low R, high G, high B)
    if r < 100 and g > 150 and b > 150:
        return 2  # Cyan

    # Very bright = white (3)
    if brightness > 200:
        return 3

    # Default to closest by brightness
    if brightness < 85:
        return 0
    elif brightness < 170:
        return 1  # or 2
    else:
        return 3

def extract_and_convert(input_path, output_chr, frame_x=0, frame_y=212, frame_w=64, frame_h=64, target_size=32):
    """
    Extract a sprite frame and convert to NES CHR format.

    Args:
        input_path: Path to source sprite sheet
        output_chr: Path to output CHR file
        frame_x, frame_y: Top-left corner of frame in source image
        frame_w, frame_h: Size of frame in source image
        target_size: Target sprite size (32 for 32x32)
    """
    print(f"Loading {input_path}...")
    img = Image.open(input_path).convert('RGBA')

    print(f"Source image size: {img.size}")
    print(f"Extracting frame at ({frame_x}, {frame_y}) size {frame_w}x{frame_h}")

    # Crop the frame
    frame = img.crop((frame_x, frame_y, frame_x + frame_w, frame_y + frame_h))

    # Resize to target size
    frame = frame.resize((target_size, target_size), Image.NEAREST)

    # Save debug PNG
    debug_png = output_chr.replace('.chr', '_debug.png')
    frame.save(debug_png)
    print(f"Saved debug PNG: {debug_png}")

    # Convert to indexed colors
    indexed = Image.new('P', (target_size, target_size))
    indexed.putpalette([
        0, 0, 0,         # 0: Black
        255, 0, 255,     # 1: Magenta
        0, 255, 255,     # 2: Cyan
        255, 255, 255,   # 3: White
    ] + [0] * (256 - 4) * 3)

    # Map each pixel
    for y in range(target_size):
        for x in range(target_size):
            rgb = frame.getpixel((x, y))
            idx = find_closest_color(rgb, NES_PALETTE)
            indexed.putpixel((x, y), idx)

    # Save indexed PNG
    indexed_png = output_chr.replace('.chr', '_indexed.png')
    indexed.save(indexed_png)
    print(f"Saved indexed PNG: {indexed_png}")

    # Convert to CHR format
    binary_data = bytearray()
    pixels = indexed.load()

    # Process in 8x8 tiles (4x4 grid for 32x32 sprite)
    for tile_y in range(0, target_size, 8):
        for tile_x in range(0, target_size, 8):
            plane0 = []
            plane1 = []

            for row in range(8):
                p0_byte = 0
                p1_byte = 0
                for col in range(8):
                    color = pixels[tile_x + col, tile_y + row]
                    bit0 = color & 1
                    bit1 = (color >> 1) & 1
                    p0_byte |= (bit0 << (7 - col))
                    p1_byte |= (bit1 << (7 - col))

                plane0.append(p0_byte)
                plane1.append(p1_byte)

            binary_data.extend(plane0)
            binary_data.extend(plane1)

    # Write CHR file
    with open(output_chr, 'wb') as f:
        f.write(binary_data)

    print(f"Wrote {len(binary_data)} bytes to {output_chr}")
    print(f"Contains {len(binary_data) // 16} tiles")

    return binary_data

def create_sprites_chr(frames_data, output_path, total_size=8192):
    """
    Create a full 8KB sprites.chr from multiple frames.
    """
    combined = bytearray()
    for frame in frames_data:
        combined.extend(frame)

    # Pad to 8KB
    while len(combined) < total_size:
        combined.append(0)

    with open(output_path, 'wb') as f:
        f.write(combined)

    print(f"Created {output_path} ({len(combined)} bytes)")

if __name__ == "__main__":
    # Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_img = os.path.join(base_dir, "gfx", "ai_output", "player_rad_90s.png")
    output_dir = os.path.join(base_dir, "gfx", "processed", "manual")
    sprites_chr = os.path.join(base_dir, "src", "game", "assets", "sprites.chr")

    os.makedirs(output_dir, exist_ok=True)

    img = Image.open(input_img)
    print(f"Image size: {img.size}")

    # ACTUAL SPRITE LOCATIONS (found by scanning):
    # RUN row sprites are ~96x88 pixels each
    # Sprite 1: bbox=(45, 220, 141, 308)
    # Sprite 2: bbox=(206, 220, 310, 308)
    # etc.

    # These are ACTUAL bounding boxes from the image
    run_sprites = [
        (45, 220, 141, 308),   # Run frame 1
        (206, 220, 310, 308),  # Run frame 2
        (319, 220, 415, 308),  # Run frame 3 (trimmed)
        (467, 220, 563, 308),  # Run frame 4 (trimmed)
    ]

    frames = []

    for i, (x1, y1, x2, y2) in enumerate(run_sprites):
        output_chr = os.path.join(output_dir, f"run_frame_{i+1}.chr")
        w = x2 - x1
        h = y2 - y1
        print(f"\n--- Extracting RUN frame {i+1} at ({x1}, {y1}) size {w}x{h} ---")
        frame_data = extract_and_convert(input_img, output_chr,
                                         frame_x=x1, frame_y=y1,
                                         frame_w=w, frame_h=h,
                                         target_size=32)
        frames.append(frame_data)

    # Create combined sprites.chr
    print(f"\n--- Creating sprites.chr ---")
    create_sprites_chr(frames, sprites_chr)

    print("\nDone! Now rebuild the ROM with compile.bat")
