"""
Sprite Mirroring Utility for Genesis/SGDK

Splits symmetric sprites into minimal tile sets that can be reconstructed
using SGDK's hardware H-flip and V-flip flags.

Usage:
    from pipeline.sprite_mirror_util import (
        analyze_symmetry,
        split_for_mirroring,
        create_mirrored_sprite,
    )
    
    # Analyze symmetry of a sprite
    symmetry = analyze_symmetry(image)  # Returns 'radial', 'horizontal', 'vertical', or 'none'
    
    # Split sprite for mirroring (returns minimal quadrant/half)
    minimal_img, mirror_type = split_for_mirroring(image)
    
    # Create full sprite from minimal tiles with mirroring
    full_img = create_mirrored_sprite(quadrant_img, 'radial')
"""

from PIL import Image
from typing import Tuple, Literal, Optional

MirrorType = Literal['radial', 'horizontal', 'vertical', 'none']


def analyze_symmetry(img: Image.Image, tolerance: int = 5) -> MirrorType:
    """
    Analyze image symmetry to determine best mirroring strategy.
    
    Args:
        img: PIL Image to analyze
        tolerance: Color difference tolerance (0-255) for matching
        
    Returns:
        'radial' - symmetric both H and V (use 1/4 tiles)
        'horizontal' - symmetric left-right (use 1/2 tiles)
        'vertical' - symmetric top-bottom (use 1/2 tiles)
        'none' - not symmetric
    """
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    width, height = img.size
    pixels = img.load()
    
    h_symmetric = True
    v_symmetric = True
    
    def colors_match(c1: Tuple, c2: Tuple) -> bool:
        return all(abs(a - b) <= tolerance for a, b in zip(c1, c2))
    
    # Check horizontal symmetry (left mirrors right)
    for y in range(height):
        for x in range(width // 2):
            left = pixels[x, y]
            right = pixels[width - 1 - x, y]
            if not colors_match(left, right):
                h_symmetric = False
                break
        if not h_symmetric:
            break
    
    # Check vertical symmetry (top mirrors bottom)
    for y in range(height // 2):
        for x in range(width):
            top = pixels[x, y]
            bottom = pixels[x, height - 1 - y]
            if not colors_match(top, bottom):
                v_symmetric = False
                break
        if not v_symmetric:
            break
    
    if h_symmetric and v_symmetric:
        return 'radial'
    elif h_symmetric:
        return 'horizontal'
    elif v_symmetric:
        return 'vertical'
    else:
        return 'none'


def split_for_mirroring(img: Image.Image, 
                        force_type: Optional[MirrorType] = None) -> Tuple[Image.Image, MirrorType]:
    """
    Split sprite into minimal tiles for mirroring.
    
    Args:
        img: Full sprite image
        force_type: Force a specific mirror type (or auto-detect if None)
        
    Returns:
        Tuple of (minimal_image, mirror_type)
        - For 'radial': returns top-left quadrant (1/4 size)
        - For 'horizontal': returns left half (1/2 size)
        - For 'vertical': returns top half (1/2 size)
        - For 'none': returns full image unchanged
    """
    mirror_type = force_type or analyze_symmetry(img)
    width, height = img.size
    
    if mirror_type == 'radial':
        # Return top-left quadrant
        return img.crop((0, 0, width // 2, height // 2)), mirror_type
    elif mirror_type == 'horizontal':
        # Return left half
        return img.crop((0, 0, width // 2, height)), mirror_type
    elif mirror_type == 'vertical':
        # Return top half
        return img.crop((0, 0, width, height // 2)), mirror_type
    else:
        return img.copy(), 'none'


def create_mirrored_sprite(minimal_img: Image.Image, 
                           mirror_type: MirrorType) -> Image.Image:
    """
    Create full sprite from minimal tiles using mirroring.
    
    Args:
        minimal_img: The minimal tile set (quadrant or half)
        mirror_type: Type of mirroring to apply
        
    Returns:
        Full reconstructed sprite
    """
    w, h = minimal_img.size
    
    if mirror_type == 'radial':
        # Quadrant -> Full (4x size)
        full = Image.new(minimal_img.mode, (w * 2, h * 2))
        
        # Top-left: original
        full.paste(minimal_img, (0, 0))
        
        # Top-right: H-flip
        full.paste(minimal_img.transpose(Image.FLIP_LEFT_RIGHT), (w, 0))
        
        # Bottom-left: V-flip
        full.paste(minimal_img.transpose(Image.FLIP_TOP_BOTTOM), (0, h))
        
        # Bottom-right: H+V flip
        full.paste(minimal_img.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.FLIP_TOP_BOTTOM), (w, h))
        
        return full
        
    elif mirror_type == 'horizontal':
        # Left half -> Full (2x width)
        full = Image.new(minimal_img.mode, (w * 2, h))
        full.paste(minimal_img, (0, 0))
        full.paste(minimal_img.transpose(Image.FLIP_LEFT_RIGHT), (w, 0))
        return full
        
    elif mirror_type == 'vertical':
        # Top half -> Full (2x height)
        full = Image.new(minimal_img.mode, (w, h * 2))
        full.paste(minimal_img, (0, 0))
        full.paste(minimal_img.transpose(Image.FLIP_TOP_BOTTOM), (0, h))
        return full
        
    else:
        return minimal_img.copy()


def process_sprite_sheet(input_path: str, 
                         output_path: str,
                         frame_width: int,
                         frame_height: int,
                         force_type: Optional[MirrorType] = None) -> dict:
    """
    Process a sprite sheet, splitting each frame for optimal mirroring.
    
    Args:
        input_path: Path to input sprite sheet
        output_path: Path to save minimal sprite sheet
        frame_width: Width of each frame in pixels
        frame_height: Height of each frame in pixels
        force_type: Force mirror type for all frames
        
    Returns:
        Dict with stats about processing
    """
    img = Image.open(input_path)
    
    if img.mode == 'P':
        # Preserve palette
        palette = img.getpalette()
        img_rgb = img.convert('RGB')
    else:
        palette = None
        img_rgb = img if img.mode == 'RGB' else img.convert('RGB')
    
    total_width, total_height = img.size
    cols = total_width // frame_width
    rows = total_height // frame_height
    
    stats = {
        'frames': cols * rows,
        'original_tiles': 0,
        'minimal_tiles': 0,
        'types': {}
    }
    
    # Determine output size based on mirror type of first frame
    first_frame = img_rgb.crop((0, 0, frame_width, frame_height))
    detected_type = force_type or analyze_symmetry(first_frame)
    
    if detected_type == 'radial':
        out_frame_w, out_frame_h = frame_width // 2, frame_height // 2
    elif detected_type == 'horizontal':
        out_frame_w, out_frame_h = frame_width // 2, frame_height
    elif detected_type == 'vertical':
        out_frame_w, out_frame_h = frame_width, frame_height // 2
    else:
        out_frame_w, out_frame_h = frame_width, frame_height
    
    # Create output image
    out_img = Image.new('RGB', (out_frame_w * cols, out_frame_h * rows))
    
    for row in range(rows):
        for col in range(cols):
            x = col * frame_width
            y = row * frame_height
            
            frame = img_rgb.crop((x, y, x + frame_width, y + frame_height))
            minimal, mtype = split_for_mirroring(frame, force_type)
            
            out_x = col * out_frame_w
            out_y = row * out_frame_h
            out_img.paste(minimal, (out_x, out_y))
            
            # Stats
            orig_tiles = (frame_width // 8) * (frame_height // 8)
            min_tiles = (minimal.size[0] // 8) * (minimal.size[1] // 8)
            stats['original_tiles'] += orig_tiles
            stats['minimal_tiles'] += min_tiles
            stats['types'][mtype] = stats['types'].get(mtype, 0) + 1
    
    # Convert back to indexed if original was indexed
    if palette and img.mode == 'P':
        out_indexed = Image.new('P', out_img.size)
        out_indexed.putpalette(palette)
        # Convert RGB to indexed by nearest color
        for y in range(out_img.height):
            for x in range(out_img.width):
                rgb = out_img.getpixel((x, y))
                # Find nearest palette color
                best_idx = 0
                best_dist = float('inf')
                for i in range(16):
                    pr, pg, pb = palette[i*3:i*3+3]
                    dist = abs(rgb[0]-pr) + abs(rgb[1]-pg) + abs(rgb[2]-pb)
                    if dist < best_dist:
                        best_dist = dist
                        best_idx = i
                out_indexed.putpixel((x, y), best_idx)
        out_img = out_indexed
    
    out_img.save(output_path)
    
    stats['savings_percent'] = round(
        100 * (1 - stats['minimal_tiles'] / stats['original_tiles']), 1
    ) if stats['original_tiles'] > 0 else 0
    
    return stats


# =============================================================================
# CLI
# =============================================================================
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python sprite_mirror_util.py <image_path> [frame_width] [frame_height]")
        print("  Analyzes sprite symmetry and optionally processes for mirroring")
        sys.exit(1)
    
    path = sys.argv[1]
    img = Image.open(path)
    
    if len(sys.argv) >= 4:
        # Process sprite sheet
        fw = int(sys.argv[2])
        fh = int(sys.argv[3])
        out_path = path.replace('.png', '_minimal.png')
        stats = process_sprite_sheet(path, out_path, fw, fh)
        print(f"Processed: {stats['frames']} frames")
        print(f"Original tiles: {stats['original_tiles']}")
        print(f"Minimal tiles: {stats['minimal_tiles']}")
        print(f"Savings: {stats['savings_percent']}%")
        print(f"Mirror types: {stats['types']}")
        print(f"Saved to: {out_path}")
    else:
        # Just analyze
        symmetry = analyze_symmetry(img)
        print(f"Image: {path}")
        print(f"Size: {img.size}")
        print(f"Symmetry: {symmetry}")
        
        if symmetry == 'radial':
            print("=> Can use 1/4 tiles with H+V mirroring (75% savings)")
        elif symmetry == 'horizontal':
            print("=> Can use 1/2 tiles with H mirroring (50% savings)")
        elif symmetry == 'vertical':
            print("=> Can use 1/2 tiles with V mirroring (50% savings)")
        else:
            print("=> No symmetry detected, full tiles needed")
