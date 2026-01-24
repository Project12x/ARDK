import os
import time
import hashlib
from typing import List, Tuple, Optional, Dict, Any
from PIL import Image, ImageDraw, ImageChops
import numpy as np

from .platforms import PlatformConfig, NESConfig, GenesisConfig, SNESConfig, GameBoyConfig
from .ai import AIAnalyzer, GenerativeResizer

# Import new advanced tile optimizer
from .optimization.tile_optimizer import (
    TileOptimizer as AdvancedTileOptimizer,
    OptimizedTileBank,
    TileReference,
)


class TileOptimizer:
    """
    Advanced Tile Optimization Engine.
    Handles deduplication, mirroring detection, and map generation.

    COMPATIBILITY WRAPPER: This class maintains backward compatibility with
    the old API while using the new AdvancedTileOptimizer internally.
    """
    def __init__(self, tile_width: int = 8, tile_height: int = 8,
                 allow_mirror_x: bool = False, allow_mirror_y: bool = False):
        self.w = tile_width
        self.h = tile_height
        self.mirror_x = allow_mirror_x
        self.mirror_y = allow_mirror_y

        # Use new advanced optimizer internally
        self._optimizer = AdvancedTileOptimizer(
            tile_width=tile_width,
            tile_height=tile_height,
            allow_mirror_x=allow_mirror_x,
            allow_mirror_y=allow_mirror_y,
        )

    def optimize(self, img: Image.Image) -> Tuple[List[Image.Image], List[Dict[str, Any]], int]:
        """
        Slice image into tiles and optimize.
        Returns: (unique_tiles, tile_map, unique_count)
        tile_map is a list of dicts: {'index': int, 'flip_x': bool, 'flip_y': bool}

        NOTE: This method uses the new AdvancedTileOptimizer internally and
        converts the result to the old API format for backward compatibility.
        """
        # Use new optimizer
        result = self._optimizer.optimize_image(img)

        # Convert tile_map from TileReference objects to old dict format
        tile_map = []
        for tile_ref in result.tile_map:
            tile_map.append({
                'index': tile_ref.index,
                'flip_x': tile_ref.flip_h,
                'flip_y': tile_ref.flip_v,
            })

        return result.unique_tiles, tile_map, len(result.unique_tiles)

class FloodFillBackgroundDetector:
    """
    Robust background removal using Edge-Initiated Flood Fill.
    
    Instead of assuming "black = transparent" (which kills internal black pixels),
    this finds the background color by sampling image corners/edges, then
    performs a flood-fill from the outside in.
    
    Any pixel NOT reached by the flood-fill is considered "Content", 
    preserving internal blacks.
    """
    
    def __init__(self, tolerance: int = 10):
        self.tolerance = tolerance

    def detect_background_color(self, img: Image.Image) -> Optional[Tuple[int, int, int]]:
        """
        Sample 4 corners to find dominant background color.
        Returns None if corners strongly disagree (Full Frame Background).
        """
        pixels = img.load()
        w, h = img.size
        
        # Sample just the 4 extreme corners
        # If the image is a spritesheet on a background, all 4 corners should resolve to same color
        # If it's a full-frame painting, they will differ.
        corners = [
            (0, 0), (w-1, 0), (0, h-1), (w-1, h-1)
        ]
        
        samples = []
        for x, y in corners:
            r, g, b, a = pixels[x, y]
            # Treat transparent as a valid "color" (0,0,0,0) or ignore?
            # If completely transparent, that IS the background.
            if a == 0:
                samples.append((0, 0, 0, 0))
            else:
                samples.append((r, g, b, 255))
        
        if not samples:
            return None

        # Check consistency
        first = samples[0]
        disagreements = 0
        for s in samples[1:]:
            # Simple Euclidean distance check
            dist = sum(abs(v1 - v2) for v1, v2 in zip(first, s))
            if dist > 30: # Tolerance
                disagreements += 1
                
        # If corners are too different, we assume it's NOT a solid background
        if disagreements > 1:
            print("      [SmartBg] Corners differ significantly. Assuming FULL FRAME background.")
            return None
            
        # Return average or most common
        from collections import Counter
        most_common = Counter(samples).most_common(1)[0][0]
        return most_common[:3] if len(most_common) > 3 else most_common

    def get_content_mask(self, img: Image.Image) -> Image.Image:
        """
        Returns a 1-bit mask image where 1=Content, 0=Background.
        Uses flood fill from edges to identify background.
        """
        w, h = img.size
        
        # 1. Detect background color logic
        bg_color = self.detect_background_color(img)
        
        if bg_color is None:
            # Full frame background - everything is content!
            return Image.new('1', (w, h), 1)

        # 2. Flood fill from corners using PIL ImageDraw
        # We start with a blank (transparent) canvas, paste image, fill background used corners?
        # Actually easier: Create a mask initialized to 1 (Content). 
        # Flood fill on a temp image from (0,0) with 0 (Background)
        
        scratch = img.copy()
        
        # Convert bg_color to fill target (r,g,b,0) effectively clearing it
        # Actually, we want to start flood fill at (0,0) and fill with TRANSPARENCY
        # IF (0,0) matches the bg_color within tolerance.
        
        # To be safe, let's flood fill on top of a known surface
        # Use ImageDraw.floodfill
        
        # We fill with (0,0,0,0) (Transparent)
        # Any pixel matching the start pixel within tolerance gets wiped.
        
        try:
            ImageDraw.floodfill(scratch, (0, 0), (0, 0, 0, 0), thresh=self.tolerance)
            ImageDraw.floodfill(scratch, (w-1, 0), (0, 0, 0, 0), thresh=self.tolerance)
            ImageDraw.floodfill(scratch, (0, h-1), (0, 0, 0, 0), thresh=self.tolerance)
            ImageDraw.floodfill(scratch, (w-1, h-1), (0, 0, 0, 0), thresh=self.tolerance)
        except Exception as e:
            print(f"      [SmartBg] Flood fill failed: {e}")
            return Image.new('1', (w, h), 1)

        # Now, anything that is (0,0,0,0) is BACKGROUND.
        # Anything else is CONTENT.
        
        # Extract alpha channel
        scratch_alpha = scratch.split()[3]
        
        # Create mask: 1 where alpha > 0, else 0
        mask = scratch_alpha.point(lambda x: 1 if x > 0 else 0, mode='1')
        
        return mask


    def detect(self, img: Image.Image) -> List[BoundingBox]:
        """Detect sprite bounding boxes using flood-fill mask"""
        # Get content mask
        mask = self.get_content_mask(img)
        
        # Use simple finding of disconnected components on the mask
        # For now, let's stick to the row-scanning logic but operating on the MASK
        # rather than raw pixels. This is much safer.
        
        w, h = mask.size
        mask_pixels = mask.load()
        
        # Scan for rows with content
        rows = []
        in_content = False
        start_y = 0
        
        for y in range(h):
            has_content = False
            for x in range(w):
                if mask_pixels[x, y]:
                    has_content = True
                    break
            
            if has_content and not in_content:
                in_content = True
                start_y = y
            elif not has_content and in_content:
                in_content = False
                if (y - start_y) > 4: # Min height filter
                    rows.append((start_y, y))
                    
        # Find sprites in rows
        sprites = []
        for y1, y2 in rows:
            in_sprite = False
            start_x = 0
            for x in range(w):
                # Check column for content within row
                col_has_content = False
                for y in range(y1, y2):
                    if mask_pixels[x, y]:
                        col_has_content = True
                        break
                
                if col_has_content and not in_sprite:
                    in_sprite = True
                    start_x = x
                elif not col_has_content and in_sprite:
                    in_sprite = False
                    if (x - start_x) > 4: # Min width
                        # Get exact tight bounds for this chunk
                        sprites.append(self._get_tight_bounds(mask, start_x, y1, x - start_x, y2 - y1))
                        
        return [s for s in sprites if s is not None]

    def _get_tight_bounds(self, mask: Image.Image, x: int, y: int, w: int, h: int) -> Optional[BoundingBox]:
        pixels = mask.load()
        min_x, max_x = x + w, x
        min_y, max_y = y + h, y
        found = False
        
        for py in range(y, y + h):
            for px in range(x, x + w):
                if pixels[px, py]:
                    found = True
                    min_x = min(min_x, px)
                    max_x = max(max_x, px)
                    min_y = min(min_y, py)
                    max_y = max(max_y, py)
                    
        if found:
            return BoundingBox(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)
        return None

    def filter_text_regions(self, img: Image.Image, bboxes: List[BoundingBox]) -> List[BoundingBox]:
        """Wrap the original text filter (it was fine), or use a simplified one."""
        # For now, just pass through - AI labeling will handle text rejection better
        return bboxes

class ContentDetector:
    """Reliable content-based sprite detection"""

    def __init__(self, brightness_threshold: int = 30, min_sprite_size: int = 16):
        self.brightness_threshold = brightness_threshold
        self.min_sprite_size = min_sprite_size

    def detect(self, img: Image.Image) -> List[BoundingBox]:
        img = img.convert('RGBA')
        rows = self._detect_content_rows(img)

        sprites = []
        for y_start, y_end in rows:
            row_sprites = self._detect_sprites_in_row(img, y_start, y_end)
            sprites.extend(row_sprites)

        return sprites

    def _detect_content_rows(self, img: Image.Image) -> List[Tuple[int, int]]:
        pixels = img.load()
        width, height = img.size

        row_has_content = []
        for y in range(height):
            has_content = False
            for x in range(0, width, 4):
                r, g, b, a = pixels[x, y]
                if self._is_content(r, g, b, a):
                    has_content = True
                    break
            row_has_content.append(has_content)

        rows = []
        in_content = False
        content_start = 0
        gap_count = 0
        max_gap = 15

        for y, has_content in enumerate(row_has_content):
            if has_content:
                if not in_content:
                    content_start = y
                    in_content = True
                gap_count = 0
            else:
                if in_content:
                    gap_count += 1
                    if gap_count > max_gap:
                        if y - gap_count - content_start >= self.min_sprite_size:
                            rows.append((content_start, y - gap_count))
                        in_content = False

        if in_content and height - content_start >= self.min_sprite_size:
            rows.append((content_start, height - 1))

        return rows

    def _detect_sprites_in_row(self, img: Image.Image, y_start: int, y_end: int) -> List[BoundingBox]:
        pixels = img.load()
        width = img.size[0]

        sprites = []
        in_sprite = False
        sprite_start = 0
        gap_count = 0
        max_gap = 12

        for x in range(width):
            has_content = False
            for y in range(y_start, min(y_end + 1, img.size[1])):
                r, g, b, a = pixels[x, y]
                if self._is_content(r, g, b, a):
                    has_content = True
                    break

            if has_content:
                if not in_sprite:
                    sprite_start = x
                    in_sprite = True
                gap_count = 0
            else:
                if in_sprite:
                    gap_count += 1
                    if gap_count > max_gap:
                        sprite_end = x - gap_count
                        if sprite_end - sprite_start >= self.min_sprite_size:
                            tight = self._get_tight_bounds(img, sprite_start, y_start,
                                                          sprite_end - sprite_start, y_end - y_start)
                            if tight:
                                sprites.append(tight)
                        in_sprite = False

        if in_sprite:
            sprite_end = width - gap_count
            if sprite_end - sprite_start >= self.min_sprite_size:
                tight = self._get_tight_bounds(img, sprite_start, y_start,
                                              sprite_end - sprite_start, y_end - y_start)
                if tight:
                    sprites.append(tight)

        return sprites

    def _get_tight_bounds(self, img: Image.Image, x: int, y: int, w: int, h: int) -> Optional[BoundingBox]:
        pixels = img.load()
        img_w, img_h = img.size

        min_x, max_x = img_w, 0
        min_y, max_y = img_h, 0

        for py in range(max(0, y), min(img_h, y + h)):
            for px in range(max(0, x), min(img_w, x + w)):
                r, g, b, a = pixels[px, py]
                if self._is_content(r, g, b, a):
                    min_x = min(min_x, px)
                    max_x = max(max_x, px)
                    min_y = min(min_y, py)
                    max_y = max(max_y, py)

        if min_x < max_x and min_y < max_y:
            return BoundingBox(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)
        return None

    def _is_content(self, r: int, g: int, b: int, a: int) -> bool:
        if a < 128:
            return False
        return (r > self.brightness_threshold or
                g > self.brightness_threshold or
                b > self.brightness_threshold)

    def filter_text_regions(self, img: Image.Image, bboxes: List[BoundingBox]) -> List[BoundingBox]:
        """
        Filter out regions that look like text labels, not actual sprites.

        Text heuristics:
        - Very wide aspect ratio (width/height > 3)
        - Low fill density (text has lots of gaps)
        - Small height (< 50px typically for labels)
        - Positioned at top/bottom edges (label placement)
        """
        filtered = []
        img_width, img_height = img.size
        pixels = img.load()

        for bbox in bboxes:
            # Calculate aspect ratio
            aspect = bbox.width / max(bbox.height, 1)

            # Calculate fill density (how much content vs empty space)
            content_pixels = 0
            total_pixels = bbox.width * bbox.height

            for y in range(bbox.y, min(bbox.y + bbox.height, img_height)):
                for x in range(bbox.x, min(bbox.x + bbox.width, img_width)):
                    r, g, b, a = pixels[x, y]
                    if self._is_content(r, g, b, a):
                        content_pixels += 1

            fill_density = content_pixels / max(total_pixels, 1)

            # Text detection heuristics
            is_text = False
            reasons = []

            # Very wide aspect ratio with small height is likely text
            if aspect > 3.5 and bbox.height < 50:
                is_text = True
                reasons.append(f"wide_aspect={aspect:.1f}")

            # Low fill density with extreme aspect ratio
            if fill_density < 0.15 and aspect > 2.5:
                is_text = True
                reasons.append(f"sparse_text_density={fill_density:.2f}")

            # Very short regions at top or bottom edges
            if bbox.height < 45 and aspect > 2.0:
                if bbox.y < 60 or bbox.y > img_height - 80:
                    is_text = True
                    reasons.append("edge_positioned_text")

            # Really small height regardless of other factors
            if bbox.height < 20 and bbox.width > 40:
                is_text = True
                reasons.append("very_short_label")

            # Tiny artifacts or debris (too small to be useful sprites)
            if bbox.width < 30 and bbox.height < 30:
                is_text = True
                reasons.append(f"tiny_artifact_{bbox.width}x{bbox.height}")

            # Very short and wide (button-like labels)
            if bbox.height < 40 and bbox.width > bbox.height * 2.5:
                is_text = True
                reasons.append("short_wide_label")

            if is_text:
                print(f"      [FILTERED] Text-like region at ({bbox.x}, {bbox.y}) "
                      f"{bbox.width}x{bbox.height}: {', '.join(reasons)}")
            else:
                filtered.append(bbox)

        return filtered


# =============================================================================
# PALETTE & NES CONVERSION
# =============================================================================

class PaletteExtractor:
    """Extract optimal NES palette from image using AI + perceptual analysis"""

    # NES Master Palette RGB values
    NES_PALETTE_RGB = {
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

    def _rgb_to_brightness(self, r, g, b):
        """Calculate perceptual brightness"""
        return 0.299 * r + 0.587 * g + 0.114 * b

    def _color_distance(self, c1, c2):
        """Perceptual color distance"""
        # Cast to int to avoid numpy uint8 overflow
        return ((int(c1[0]) - int(c2[0])) ** 2 + (int(c1[1]) - int(c2[1])) ** 2 + (int(c1[2]) - int(c2[2])) ** 2) ** 0.5

    def _find_closest_nes_color(self, r, g, b):
        """Find closest NES palette color to RGB"""
        min_dist = float('inf')
        best_idx = 0x0F
        for idx, (pr, pg, pb) in self.NES_PALETTE_RGB.items():
            dist = self._color_distance((r, g, b), (pr, pg, pb))
            if dist < min_dist:
                min_dist = dist
                best_idx = idx
        return best_idx

    def extract_from_image(self, img: Image.Image, num_colors: int = 4) -> List[int]:
        """
        Extract optimal NES palette by finding dominant image colors.

        Strategy:
        1. Sample image colors extensively
        2. Find dominant RGB colors using weighted clustering
        3. Map dominant colors to closest NES equivalents
        4. Ensure brightness spread (dark, mid, light) for good gradients
        """
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        pixels = np.array(img)
        height, width = pixels.shape[:2]

        # Build histogram of RGB colors (quantized to reduce noise)
        color_counts = {}
        total_sampled = 0

        # Sample pixels in a grid pattern for good coverage
        for y in range(0, height, max(1, int(height ** 0.5) // 8)):
            for x in range(0, width, max(1, int(width ** 0.5) // 8)):
                r, g, b, a = pixels[y, x]
                if a < 128:  # Skip transparent
                    continue

                total_sampled += 1

                # Quantize to 4-bit per channel (reduces noise while keeping color info)
                qr, qg, qb = (r >> 4) << 4, (g >> 4) << 4, (b >> 4) << 4
                key = (qr, qg, qb)

                # Weight by saturation - more saturated colors are more important
                max_c = max(r, g, b)
                min_c = min(r, g, b)
                saturation = (max_c - min_c) / max(max_c, 1)
                weight = 1.0 + saturation * 2.0  # Saturated colors count more

                color_counts[key] = color_counts.get(key, 0) + weight

        if not color_counts:
            # Fallback to default
            print("      [Palette] No colors sampled, using default")
            return [0x0F, 0x16, 0x27, 0x30]  # Black, red, orange, white

        # Sort by weighted frequency
        sorted_colors = sorted(color_counts.items(), key=lambda x: -x[1])

        # Take top N dominant colors (more than we need to have options)
        top_colors = sorted_colors[:min(20, len(sorted_colors))]

        # Map each dominant color to its closest NES equivalent and score it
        nes_color_scores = {}
        for (qr, qg, qb), weight in top_colors:
            nes_idx = self._find_closest_nes_color(qr, qg, qb)

            # Skip true blacks (let's pick them separately)
            if nes_idx in [0x0D, 0x0E, 0x1D, 0x1E, 0x1F, 0x2E, 0x2F, 0x3E, 0x3F]:
                nes_idx = 0x0F  # Map to canonical black

            # Accumulate scores (how much of the image this NES color represents)
            if nes_idx not in nes_color_scores:
                nes_color_scores[nes_idx] = {
                    'score': 0,
                    'brightness': self._rgb_to_brightness(*self.NES_PALETTE_RGB.get(nes_idx, (0,0,0)))
                }
            nes_color_scores[nes_idx]['score'] += weight

        # Now select palette with good brightness distribution
        # We need: 1 dark, 1-2 mid, 1 bright
        palette = []

        # Group candidates by brightness tier
        dark_candidates = []   # brightness < 60
        mid_candidates = []    # brightness 60-160
        bright_candidates = [] # brightness > 160

        for nes_idx, data in nes_color_scores.items():
            brightness = data['brightness']
            score = data['score']

            if brightness < 60:
                dark_candidates.append((nes_idx, score, brightness))
            elif brightness < 160:
                mid_candidates.append((nes_idx, score, brightness))
            else:
                bright_candidates.append((nes_idx, score, brightness))

        # Sort each tier by score (highest first)
        dark_candidates.sort(key=lambda x: -x[1])
        mid_candidates.sort(key=lambda x: -x[1])
        bright_candidates.sort(key=lambda x: -x[1])

        # Strategy: pick best from each tier, then fill remaining slots with next best

        # 1. Always include a dark color (index 0 should be darkest for transparency)
        if dark_candidates:
            palette.append(dark_candidates[0][0])
        else:
            palette.append(0x0F)  # Black fallback

        # 2. Pick best mid-tone colors (these carry most of the image detail)
        for candidate in mid_candidates[:2]:  # Up to 2 mid-tones
            if len(palette) >= num_colors:
                break
            if candidate[0] not in palette:
                palette.append(candidate[0])

        # 3. Pick a bright color for highlights
        if len(palette) < num_colors and bright_candidates:
            for candidate in bright_candidates:
                if candidate[0] not in palette:
                    palette.append(candidate[0])
                    break

        # 4. Fill remaining slots from all candidates by score
        all_remaining = [(idx, score, br) for idx, score, br in
                         dark_candidates + mid_candidates + bright_candidates
                         if idx not in palette]
        all_remaining.sort(key=lambda x: -x[1])

        for candidate in all_remaining:
            if len(palette) >= num_colors:
                break
            palette.append(candidate[0])

        # 5. If still not enough, add sensible defaults
        default_fills = [0x10, 0x2D, 0x30, 0x0F]  # Gray, light gray, white, black
        for fill in default_fills:
            if len(palette) >= num_colors:
                break
            if fill not in palette:
                palette.append(fill)

        # Sort palette by brightness (dark to light) for consistent ordering
        def get_brightness(idx):
            r, g, b = self.NES_PALETTE_RGB.get(idx, (0, 0, 0))
            return self._rgb_to_brightness(r, g, b)

        palette = sorted(palette[:num_colors], key=get_brightness)

        # Log what we picked
        palette_desc = ', '.join(f'${c:02X}' for c in palette)
        print(f"      [Palette] Extracted: {palette_desc}")

        return palette

    def extract_with_ai(self, img: Image.Image, analyzer: 'AIAnalyzer', num_colors: int = 4) -> List[int]:
        """
        Extract palette using AI analysis.
        Uses Hybrid approach: Finds dominant colors algorithmically, then asks AI to map them.
        """
        # 1. Find dominant colors algorithmically (Quantization)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
            
        # Downsample for speed
        thumb = img.copy()
        thumb.thumbnail((128, 128))
        
        # Quantize to find top N colors using PIL's FastOctree
        # We ask for, say, 8 colors to capture the sprite details well
        dominant_rgbs = []
        try:
            q_img = thumb.quantize(colors=8, method=2) # 2=FastOctree
            p = q_img.getpalette() # [r,g,b, r,g,b, ...]
            
            if p:
                # Chunk into triplets
                raw_colors = [p[i:i+3] for i in range(0, len(p), 3)][:8]
                for c in raw_colors:
                    # Deduplicate tuples
                    ct = tuple(c)
                    if ct not in dominant_rgbs: 
                        dominant_rgbs.append( ct )
        except Exception:
            # Fallback
             pass
        
        # If quantization failed or returned nothing, rely on pure AI (send whole image)
        if not dominant_rgbs:
             return self._extract_pure_ai(thumb, analyzer, num_colors)

        # Format for AI
        color_list_str = ", ".join([f"RGB{c}" for c in dominant_rgbs])
        
        # 2. Ask AI to map these to NES
        prompt = (
            f"I have an NES sprite. The dominant colors in the image are: {color_list_str}. "
            f"Please map these specific RGB values to the nearest {num_colors} NES palette colors (hex codes $00-$3F). "
            "The first color must be the background (transparency) color (usually $0F Black or $00 Gray). "
            "Return JSON: {\"palette\": [\"$0F\", \"$16\", ...], \"reason\": \"...\"}"
        )
        
        print(f"      [HybridPalette] Dominant RGBs: {color_list_str}")
        
        # We pass the image too, so it gets context of WHICH color is background
        result = analyzer.analyze_prompt(thumb, prompt)
        
        if result and 'palette' in result:
             # Validate we got what we asked for
             pal = result['palette']
             if isinstance(pal, list) and len(pal) > 0:
                 # Ensure we have ints, not hex strings
                 clean_pal = []
                 for c in pal:
                     if isinstance(c, int):
                         clean_pal.append(c)
                     elif isinstance(c, str):
                         # Handle "$0F", "0x0F", "0F"
                         c_clean = c.replace('$', '').replace('0x', '').strip()
                         try:
                             clean_pal.append(int(c_clean, 16))
                         except ValueError:
                             pass
                 
                 if len(clean_pal) > 0:
                     return clean_pal
             
        # Fallback to pure algorithmic
        print("      [HybridPalette] AI failed, falling back to algorithmic extraction.")
        return self.extract_from_image(img, num_colors)

    def _extract_pure_ai(self, img: Image.Image, analyzer: 'AIAnalyzer', num_colors: int) -> List[int]:
        """Legacy method: Ask AI to look at image and guess colors"""
        prompt = (
            f"Analyze this NES sprite and extract the optimal {num_colors}-color palette. "
            "The first color must be the background (transparency) color. "
            "Select colors from the standard NES palette (hex codes $00-$3F). "
             "Return JSON: {\"palette\": [\"$0F\", \"$16\", ...], \"reason\": \"...\"}"
        )
        # Use simple analyze_prompt wrapper
        result = analyzer.analyze_prompt(img, prompt)
        return result.get('palette', self.extract_from_image(img, num_colors))

    def _build_nes_color_description(self) -> str:
        """Build NES palette description for AI prompts"""
        nes_colors_desc = []
        for idx in [0x0F, 0x00, 0x10, 0x2D, 0x30,  # Grays
                    0x01, 0x02, 0x11, 0x12, 0x21, 0x22, 0x31,  # Blues
                    0x05, 0x06, 0x15, 0x16, 0x25, 0x26,  # Reds
                    0x09, 0x0A, 0x19, 0x1A, 0x29, 0x2A,  # Greens
                    0x03, 0x13, 0x23, 0x24,  # Purples/Magentas
                    0x0C, 0x1C, 0x2C, 0x3C,  # Cyans
                    0x07, 0x17, 0x27, 0x37]:  # Oranges/Yellows
            r, g, b = self.NES_PALETTE_RGB.get(idx, (0, 0, 0))
            brightness = self._rgb_to_brightness(r, g, b)
            if brightness < 50:
                level = "dark"
            elif brightness < 120:
                level = "medium"
            else:
                level = "bright"
            nes_colors_desc.append(f"${idx:02X}: RGB({r},{g},{b}) [{level}]")
        return chr(10).join(nes_colors_desc)

    def _try_openai_compatible_palette(self, provider, img: Image.Image,
                                        nes_colors_desc: str, num_colors: int) -> Optional[List[int]]:
        """Try palette extraction with OpenAI-compatible provider"""
        import io
        import base64
        import re

        prompt = f"""Analyze this image and recommend the best {num_colors}-color NES palette.

The NES can only display {num_colors} colors per sprite (including transparent/black).
Choose colors that:
1. Capture the dominant mood/theme of the image
2. Provide good contrast (dark, mid-tone, and light)
3. Work well for dithering gradients

Available NES colors:
{nes_colors_desc}

Respond with ONLY a JSON object like:
{{"palette": ["$XX", "$XX", "$XX", "$XX"], "reason": "brief explanation"}}

The first color should be dark (for shadows/transparency).
Order from dark to light."""

        try:
            buffer = io.BytesIO()
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(buffer, format='JPEG', quality=85)
            img_base64 = base64.b64encode(buffer.getvalue()).decode()

            response = provider.client.chat.completions.create(
                model=getattr(provider, 'model', 'gpt-4o-mini'),
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {
                            "url": f"data:image/jpeg;base64,{img_base64}"
                        }}
                    ]
                }],
                max_tokens=200
            )
            result = response.choices[0].message.content

            # Parse JSON response
            json_match = re.search(r'\{[^}]+\}', result)
            if json_match:
                data = json.loads(json_match.group())
                if 'palette' in data:
                    palette = []
                    for color_str in data['palette']:
                        hex_val = color_str.replace('$', '').replace('0x', '')
                        palette.append(int(hex_val, 16))
                    if len(palette) == num_colors:
                        reason = data.get('reason', 'AI selected')
                        print(f"      [AI Palette] Selected: {self._format_palette(palette)}")
                        print(f"      [AI Palette] Reason: {reason}")
                        return palette
        except Exception as e:
            print(f"      [AI Palette] {provider.name} error: {e}")

        return None

    def _format_palette(self, palette: List[int]) -> str:
        return ', '.join(f'${c:02X}' for c in palette)


class SpriteConverter:
    """
    Platform-agnostic sprite converter.
    Handles scaling, color indexing, and tile data generation for any platform.
    """

    def __init__(self, platform: PlatformConfig = None, palette: List[int] = None):
        self.platform = platform or NESConfig
        self.palette = palette or self.platform.default_palette
        self.palette_rgb = self.platform.get_palette_rgb(self.palette)
        self.colors = self.platform.colors_per_palette

    def scale_sprite(self, img: Image.Image, target_size: int) -> Image.Image:
        """Scale sprite to target size, preserving aspect ratio.

        Uses platform-specific resampling:
        - LANCZOS: Smooth downscaling for high-color platforms (SNES, Amiga, etc.)
        - NEAREST: Pixelated look for authentic retro platforms (C64, CGA, NES)
        
        BESPOKE UPDATE:
        - Integers scales (e.g. 0.5x, 0.25x) force NEAREST to preserve pixel art.
        - Fractional scales force LANCZOS to minimize aliasing.
        """
    def scale_image(self, img: Image.Image, target_w: int, target_h: int, fit_mode: str = 'CONTAIN') -> Image.Image:
        """Scale image to target dims, preserving aspect ratio.
        
        Args:
            fit_mode: 'CONTAIN' (Letterbox) or 'COVER' (Crop to Aspect)
        
        BESPOKE LOGIC:
        - Checks for integer scaling ratios.
        - Applies NEAREST for integer scales (Pixel Art).
        - Applies LANCZOS for fractional scales (Downsampling).
        """
        w, h = img.size
        
        # Calculate Scale Factors
        scale_w = target_w / w
        scale_h = target_h / h
        
        if fit_mode == 'COVER':
            scale = max(scale_w, scale_h)
            print(f"      [Smart-Resize] Mode: COVER (Scale: {scale:.2f}x)")
        else:
            scale = min(scale_w, scale_h)
            
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))

        # Check for Integer Scale
        is_integer_scale = False
        if scale < 1.0:
            inv_scale = 1.0 / scale
            if abs(inv_scale - round(inv_scale)) < 0.05:
                is_integer_scale = True

        # Platform Resampling
        resample_mode = getattr(self.platform, 'resample_mode', 'LANCZOS')
        
        if self.platform.__name__ == 'NESConfig':
            if is_integer_scale:
                resample = Image.NEAREST
                print(f"      [Smart-Resize] Integer scale ({scale:.2f}x) -> NEAREST")
            else:
                resample = Image.LANCZOS
                print(f"      [Smart-Resize] Fractional scale ({scale:.2f}x) -> LANCZOS")
        elif resample_mode == "NEAREST":
            resample = Image.NEAREST
        else:
            resample = Image.LANCZOS

        scaled = img.resize((new_w, new_h), resample)

        # Create Canvas
        result = Image.new('RGBA', (target_w, target_h), (0, 0, 0, 0))
        
        # Center Position
        paste_x = (target_w - new_w) // 2
        paste_y = (target_h - new_h) // 2
        
        if fit_mode == 'COVER':
            # For COVER, we might need to crop if we exceeded bounds
            # The paste logic above handles negative offsets correctly for PIL?
            # PIL paste with negative offset crops the source image? 
            # No, PIL paste expects top-left coordinate. if negative, it pastes off-canvas.
            # But the canvas is target_size-limited, so it crops automatically?
            # Let's verify: result.paste(bigger_img, (-10, -10)) -> pastes top-left at -10,-10, so we see the center.
            # Yes, standard behavior.
            pass
            
        result.paste(scaled, (paste_x, paste_y))

        return result

    def scale_sprite(self, img: Image.Image, target_size: int) -> Image.Image:
        """Wrapper for square targets"""
        return self.scale_image(img, target_size, target_size)

    def index_sprite(self, img: Image.Image) -> Image.Image:
        """Convert RGBA image to indexed palette image with platform-appropriate dithering"""
        indexed = Image.new('P', img.size)

        # Build palette data for PIL
        pal_data = []
        for rgb in self.palette_rgb:
            pal_data.extend(rgb)
        pal_data.extend([0] * (768 - len(pal_data)))
        indexed.putpalette(pal_data)

        src_pixels = img.load()
        dst_pixels = indexed.load()

        # Get dithering settings from platform config
        dither_method = getattr(self.platform, 'dither_method', 'none')
        dither_matrix_size = getattr(self.platform, 'dither_matrix_size', 4)
        dither_strength = getattr(self.platform, 'dither_strength', 1.0)

        # Bayer matrices for ordered dithering
        BAYER_2X2 = np.array([[0, 2], [3, 1]]) / 4.0 - 0.5
        BAYER_4X4 = np.array([
            [ 0,  8,  2, 10],
            [12,  4, 14,  6],
            [ 3, 11,  1,  9],
            [15,  7, 13,  5]
        ]) / 16.0 - 0.5
        BAYER_8X8 = np.array([
            [ 0, 32,  8, 40,  2, 34, 10, 42],
            [48, 16, 56, 24, 50, 18, 58, 26],
            [12, 44,  4, 36, 14, 46,  6, 38],
            [60, 28, 52, 20, 62, 30, 54, 22],
            [ 3, 35, 11, 43,  1, 33,  9, 41],
            [51, 19, 59, 27, 49, 17, 57, 25],
            [15, 47,  7, 39, 13, 45,  5, 37],
            [63, 31, 55, 23, 61, 29, 53, 21]
        ]) / 64.0 - 0.5

        # Select Bayer matrix
        if dither_matrix_size == 2:
            bayer = BAYER_2X2
        elif dither_matrix_size == 8:
            bayer = BAYER_8X8
        else:
            bayer = BAYER_4X4

        # Error diffusion buffer for Floyd-Steinberg
        if dither_method == 'floyd':
            error = np.zeros((img.height + 1, img.width + 1, 3), dtype=np.float32)

        # Quantize colors to palette with dithering
        max_color = min(self.colors, len(self.palette_rgb))
        dither_scale = 64.0 * dither_strength

        for y in range(img.height):
            for x in range(img.width):
                r, g, b, a = src_pixels[x, y]

                if a < 128:
                    dst_pixels[x, y] = 0  # Transparent = color 0
                    continue

                # Apply dithering adjustment
                if dither_method == 'ordered':
                    # Ordered (Bayer) dithering
                    threshold = bayer[y % bayer.shape[0], x % bayer.shape[1]]
                    r = max(0, min(255, r + threshold * dither_scale))
                    g = max(0, min(255, g + threshold * dither_scale))
                    b = max(0, min(255, b + threshold * dither_scale))
                elif dither_method == 'floyd':
                    # Floyd-Steinberg error diffusion
                    r = max(0, min(255, r + error[y, x, 0]))
                    g = max(0, min(255, g + error[y, x, 1]))
                    b = max(0, min(255, b + error[y, x, 2]))

                # Find closest palette color
                min_dist = float('inf')
                best_idx = 0
                for i, pal_rgb in enumerate(self.palette_rgb[:max_color]):
                    dist = (r - pal_rgb[0])**2 + (g - pal_rgb[1])**2 + (b - pal_rgb[2])**2
                    if dist < min_dist:
                        min_dist = dist
                        best_idx = i
                dst_pixels[x, y] = best_idx

                # Distribute error for Floyd-Steinberg
                if dither_method == 'floyd':
                    pr, pg, pb = self.palette_rgb[best_idx]
                    err_r, err_g, err_b = r - pr, g - pg, b - pb
                    if x + 1 < img.width:
                        error[y, x + 1] += [err_r * 7/16, err_g * 7/16, err_b * 7/16]
                    if y + 1 < img.height:
                        if x > 0:
                            error[y + 1, x - 1] += [err_r * 3/16, err_g * 3/16, err_b * 3/16]
                        error[y + 1, x] += [err_r * 5/16, err_g * 5/16, err_b * 5/16]
                        if x + 1 < img.width:
                            error[y + 1, x + 1] += [err_r * 1/16, err_g * 1/16, err_b * 1/16]

        return indexed

    def generate_tile_data(self, indexed: Image.Image) -> bytes:
        """Generate platform-specific tile data"""
        return self.platform.generate_tile_data(indexed)

    @property
    def output_extension(self) -> str:
        """Get platform-specific output file extension"""
        return self.platform.output_extension


# Legacy alias for backward compatibility
NESConverter = SpriteConverter


# =============================================================================
# UNIFIED PIPELINE
# =============================================================================

