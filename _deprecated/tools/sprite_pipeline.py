#!/usr/bin/env python3
"""
Multi-Step AI Sprite Processing Pipeline for NES

A robust pipeline that processes AI-generated sprite sheets into NES-compatible
CHR format using multiple AI passes and proven algorithms.

Pipeline Steps:
1. DETECT: AI analyzes sprite sheet structure (rows, frames, types)
2. SEGMENT: Content-based sprite extraction with tight bounds
3. PALETTE: Extract dominant colors and map to NES palette
4. SCALE: High-quality downscaling to NES dimensions
5. INDEX: Convert to 4-color indexed with optimal palette
6. CHR: Generate NES CHR tiles with validation

Requirements:
    pip install pillow google-generativeai python-dotenv numpy scikit-learn

Usage:
    python tools/sprite_pipeline.py gfx/ai_output/player.png -o gfx/processed/player
"""

import os
import sys
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Tuple, Optional, Dict
from PIL import Image
import numpy as np
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# NES CONSTANTS
# =============================================================================

# Full NES palette (64 colors) - RGB values
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

# Common NES color names for AI prompts
NES_COLOR_NAMES = {
    0x0F: "black", 0x00: "dark_gray", 0x10: "gray", 0x20: "white", 0x30: "bright_white",
    0x01: "dark_blue", 0x11: "blue", 0x21: "light_blue", 0x31: "pale_blue",
    0x02: "dark_indigo", 0x12: "indigo", 0x22: "light_indigo", 0x32: "pale_indigo",
    0x03: "dark_violet", 0x13: "violet", 0x23: "light_violet", 0x33: "pale_violet",
    0x04: "dark_purple", 0x14: "purple", 0x24: "magenta", 0x34: "pale_magenta",
    0x05: "dark_red", 0x15: "red", 0x25: "pink", 0x35: "pale_pink",
    0x06: "dark_orange", 0x16: "red_orange", 0x26: "orange", 0x36: "pale_orange",
    0x07: "dark_brown", 0x17: "brown", 0x27: "tan", 0x37: "cream",
    0x08: "dark_olive", 0x18: "olive", 0x28: "yellow", 0x38: "pale_yellow",
    0x09: "dark_green", 0x19: "green", 0x29: "lime", 0x39: "pale_lime",
    0x0A: "dark_grass", 0x1A: "grass", 0x2A: "light_green", 0x3A: "pale_green",
    0x0B: "dark_teal", 0x1B: "teal", 0x2B: "aqua", 0x3B: "pale_aqua",
    0x0C: "dark_cyan", 0x1C: "cyan", 0x2C: "light_cyan", 0x3C: "pale_cyan",
}

# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class SpriteFrame:
    """Represents a single sprite frame"""
    id: int
    x: int
    y: int
    width: int
    height: int
    sprite_type: str = "unknown"
    action: str = "unknown"
    description: str = ""
    frame_index: int = 0
    palette: List[int] = field(default_factory=list)

@dataclass
class SpriteSheet:
    """Represents an analyzed sprite sheet"""
    path: str
    width: int
    height: int
    frames: List[SpriteFrame] = field(default_factory=list)
    rows: List[Tuple[int, int]] = field(default_factory=list)  # (y_start, y_end)
    dominant_colors: List[Tuple[int, int, int]] = field(default_factory=list)

# =============================================================================
# STEP 1: SPRITE DETECTION (Content-based + AI metadata)
# =============================================================================

class SpriteDetector:
    """Detects and segments sprites from sprite sheets"""

    def __init__(self, brightness_threshold: int = 30):
        self.brightness_threshold = brightness_threshold

    def detect_rows(self, img: Image.Image) -> List[Tuple[int, int]]:
        """Detect horizontal rows containing sprites"""
        pixels = img.load()
        width, height = img.size

        row_has_content = []
        for y in range(height):
            has_content = False
            for x in range(0, width, 4):
                r, g, b = pixels[x, y][:3]
                if r > self.brightness_threshold or g > self.brightness_threshold or b > self.brightness_threshold:
                    has_content = True
                    break
            row_has_content.append(has_content)

        # Find contiguous content regions
        rows = []
        in_content = False
        content_start = 0
        gap_count = 0
        max_gap = 15  # Allow gaps for internal details

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
                        rows.append((content_start, y - gap_count))
                        in_content = False

        if in_content:
            rows.append((content_start, height - 1))

        return rows

    def detect_sprites_in_row(self, img: Image.Image, y_start: int, y_end: int,
                               min_width: int = 20) -> List[Tuple[int, int, int, int]]:
        """Detect individual sprites within a row"""
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
                r, g, b = pixels[x, y][:3]
                if r > self.brightness_threshold or g > self.brightness_threshold or b > self.brightness_threshold:
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
                        if sprite_end - sprite_start >= min_width:
                            # Get tight bounds
                            tight = self._get_tight_bounds(img, sprite_start, y_start,
                                                          sprite_end - sprite_start, y_end - y_start)
                            if tight:
                                sprites.append(tight)
                        in_sprite = False

        if in_sprite:
            sprite_end = width - gap_count
            if sprite_end - sprite_start >= min_width:
                tight = self._get_tight_bounds(img, sprite_start, y_start,
                                              sprite_end - sprite_start, y_end - y_start)
                if tight:
                    sprites.append(tight)

        return sprites

    def _get_tight_bounds(self, img: Image.Image, x: int, y: int, w: int, h: int) -> Optional[Tuple[int, int, int, int]]:
        """Get tight bounding box around actual content"""
        pixels = img.load()
        img_w, img_h = img.size

        min_x, max_x = img_w, 0
        min_y, max_y = img_h, 0

        for py in range(max(0, y), min(img_h, y + h)):
            for px in range(max(0, x), min(img_w, x + w)):
                r, g, b = pixels[px, py][:3]
                if r > self.brightness_threshold or g > self.brightness_threshold or b > self.brightness_threshold:
                    min_x = min(min_x, px)
                    max_x = max(max_x, px)
                    min_y = min(min_y, py)
                    max_y = max(max_y, py)

        if min_x < max_x and min_y < max_y:
            return (min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)
        return None

    def detect_all(self, img: Image.Image) -> List[SpriteFrame]:
        """Detect all sprites in image"""
        rows = self.detect_rows(img)

        frames = []
        frame_id = 1

        for row_idx, (y_start, y_end) in enumerate(rows):
            sprites = self.detect_sprites_in_row(img, y_start, y_end)

            for sprite_idx, (x, y, w, h) in enumerate(sprites):
                frame = SpriteFrame(
                    id=frame_id,
                    x=x, y=y, width=w, height=h,
                    frame_index=sprite_idx
                )
                frames.append(frame)
                frame_id += 1

        return frames

# =============================================================================
# STEP 2: PALETTE EXTRACTION
# =============================================================================

class PaletteExtractor:
    """Extracts and maps colors to NES palette"""

    def __init__(self):
        # Build reverse lookup for NES colors
        self.nes_colors = [(idx, rgb) for idx, rgb in NES_PALETTE_RGB.items()]

    def extract_dominant_colors(self, img: Image.Image, num_colors: int = 4) -> List[Tuple[int, int, int]]:
        """Extract dominant colors using k-means clustering with synthwave color bias"""
        # Convert to numpy array
        pixels = np.array(img.convert('RGB'))
        pixels = pixels.reshape(-1, 3)

        # Filter out near-black (background) and very dark anti-aliased pixels
        brightness = np.sum(pixels, axis=1)
        mask = brightness > 100  # Higher threshold to skip dark anti-aliasing

        foreground = pixels[mask]

        if len(foreground) < num_colors:
            # Fallback to common synthwave palette
            return [(0, 0, 0), (255, 0, 255), (0, 255, 255), (255, 255, 255)]

        # Use k-means with more clusters to find distinct colors
        from sklearn.cluster import KMeans
        n_clusters = min(8, len(foreground))  # Use more clusters
        kmeans = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
        kmeans.fit(foreground)

        # Get cluster centers and their sizes
        centers = kmeans.cluster_centers_.astype(int)
        labels = kmeans.labels_
        cluster_sizes = [np.sum(labels == i) for i in range(n_clusters)]

        # Categorize colors as magenta, cyan, white, or other
        categorized = []
        for i, center in enumerate(centers):
            r, g, b = center
            size = cluster_sizes[i]

            # Classify by color channel dominance
            is_magenta = r > 150 and g < 100 and b > 150
            is_cyan = r < 100 and g > 150 and b > 150
            is_white = r > 200 and g > 200 and b > 200

            if is_magenta:
                categorized.append(('magenta', tuple(center), size))
            elif is_cyan:
                categorized.append(('cyan', tuple(center), size))
            elif is_white:
                categorized.append(('white', tuple(center), size))
            else:
                categorized.append(('other', tuple(center), size))

        # Pick best representative for each category
        result = [(0, 0, 0)]  # Start with black

        # Find best magenta
        magentas = [c for c in categorized if c[0] == 'magenta']
        if magentas:
            best = max(magentas, key=lambda x: x[2])
            result.append(best[1])
        else:
            result.append((228, 84, 236))  # Default NES magenta $24

        # Find best cyan
        cyans = [c for c in categorized if c[0] == 'cyan']
        if cyans:
            best = max(cyans, key=lambda x: x[2])
            result.append(best[1])
        else:
            result.append((56, 180, 204))  # Default NES cyan $2C

        # Find best white
        whites = [c for c in categorized if c[0] == 'white']
        if whites:
            best = max(whites, key=lambda x: x[2])
            result.append(best[1])
        else:
            result.append((236, 238, 236))  # Default NES white $30

        return result[:num_colors]

    def map_to_nes(self, rgb: Tuple[int, int, int]) -> int:
        """Map RGB color to nearest NES palette color"""
        min_dist = float('inf')
        best_idx = 0x0F

        for nes_idx, nes_rgb in self.nes_colors:
            dist = sum((a - b) ** 2 for a, b in zip(rgb, nes_rgb))
            if dist < min_dist:
                min_dist = dist
                best_idx = nes_idx

        return best_idx

    def create_nes_palette(self, dominant_colors: List[Tuple[int, int, int]]) -> List[int]:
        """Create 4-color NES palette from dominant colors"""
        # Always start with black for transparency
        palette = [0x0F]

        # Map remaining colors with special handling for common synthwave colors
        for rgb in dominant_colors[1:4]:  # Skip first (black)
            r, g, b = rgb

            # Direct mapping for common synthwave colors
            if r > 200 and g < 50 and b > 200:
                # Bright magenta -> $24
                nes_idx = 0x24
            elif r < 50 and g > 200 and b > 200:
                # Bright cyan -> $2C
                nes_idx = 0x2C
            elif r > 220 and g > 220 and b > 220:
                # White -> $30
                nes_idx = 0x30
            else:
                # Use normal mapping
                nes_idx = self.map_to_nes(rgb)

            if nes_idx not in palette:
                palette.append(nes_idx)

        # Ensure we have exactly 4 colors
        while len(palette) < 4:
            for fallback in [0x30, 0x20, 0x10]:
                if fallback not in palette:
                    palette.append(fallback)
                    break

        return palette[:4]

    def classify_pixel(self, r: int, g: int, b: int, palette_rgb: List[Tuple[int, int, int]]) -> int:
        """Classify a pixel to the nearest palette color (0-3)"""
        # Very dark = transparent (0)
        if r < 40 and g < 40 and b < 40:
            return 0

        # Find closest palette color
        min_dist = float('inf')
        best_idx = 0

        for idx, pal_rgb in enumerate(palette_rgb):
            dist = (r - pal_rgb[0])**2 + (g - pal_rgb[1])**2 + (b - pal_rgb[2])**2
            if dist < min_dist:
                min_dist = dist
                best_idx = idx

        return best_idx

# =============================================================================
# STEP 3: SCALING
# =============================================================================

class SpriteScaler:
    """High-quality sprite scaling"""

    def scale_to_nes(self, img: Image.Image, target_size: int = 32) -> Image.Image:
        """Scale sprite to NES dimensions while preserving details"""
        w, h = img.size

        if w <= target_size and h <= target_size:
            # Pad to target size
            result = Image.new('RGBA', (target_size, target_size), (0, 0, 0, 0))
            paste_x = (target_size - w) // 2
            paste_y = (target_size - h) // 2
            result.paste(img, (paste_x, paste_y))
            return result

        # Calculate scale to fit in target while preserving aspect ratio
        scale = min(target_size / w, target_size / h)
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))

        # Use LANCZOS for high-quality downscaling
        scaled = img.resize((new_w, new_h), Image.LANCZOS)

        # Center in target size
        result = Image.new('RGBA', (target_size, target_size), (0, 0, 0, 0))
        paste_x = (target_size - new_w) // 2
        paste_y = (target_size - new_h) // 2
        result.paste(scaled, (paste_x, paste_y))

        return result

# =============================================================================
# STEP 4: INDEXING
# =============================================================================

class SpriteIndexer:
    """Convert RGBA sprites to indexed 4-color"""

    def __init__(self, palette_extractor: PaletteExtractor):
        self.palette_extractor = palette_extractor

    def index_sprite(self, img: Image.Image, nes_palette: List[int]) -> Tuple[Image.Image, List[int]]:
        """Convert sprite to 4-color indexed image"""
        # Get RGB values for NES palette
        palette_rgb = [NES_PALETTE_RGB[idx] for idx in nes_palette]

        # Create indexed image
        indexed = Image.new('P', img.size)

        # Set palette (RGB for each of 4 colors, then pad)
        pal_data = []
        for rgb in palette_rgb:
            pal_data.extend(rgb)
        pal_data.extend([0] * (768 - len(pal_data)))
        indexed.putpalette(pal_data)

        # Convert pixels
        src_pixels = img.load()
        dst_pixels = indexed.load()

        for y in range(img.height):
            for x in range(img.width):
                r, g, b, a = src_pixels[x, y]

                if a < 128:
                    # Transparent -> color 0
                    dst_pixels[x, y] = 0
                else:
                    idx = self.palette_extractor.classify_pixel(r, g, b, palette_rgb)
                    dst_pixels[x, y] = idx

        return indexed, nes_palette

# =============================================================================
# STEP 5: CHR GENERATION
# =============================================================================

class CHRGenerator:
    """Generate NES CHR tiles from indexed images"""

    def generate(self, indexed_img: Image.Image) -> bytes:
        """Convert indexed image to CHR format"""
        width, height = indexed_img.size
        pixels = indexed_img.load()

        chr_data = bytearray()

        # Process 8x8 tiles (left-to-right, top-to-bottom)
        for tile_y in range(0, height, 8):
            for tile_x in range(0, width, 8):
                # Each tile = 16 bytes (8 bytes plane 0, 8 bytes plane 1)
                plane0 = []
                plane1 = []

                for row in range(8):
                    p0_byte = 0
                    p1_byte = 0

                    for col in range(8):
                        x = tile_x + col
                        y = tile_y + row

                        if x < width and y < height:
                            color = pixels[x, y]
                        else:
                            color = 0

                        # Color is 0-3, split into two bit planes
                        bit0 = color & 1
                        bit1 = (color >> 1) & 1

                        p0_byte |= (bit0 << (7 - col))
                        p1_byte |= (bit1 << (7 - col))

                    plane0.append(p0_byte)
                    plane1.append(p1_byte)

                chr_data.extend(plane0)
                chr_data.extend(plane1)

        return bytes(chr_data)

    def validate(self, chr_data: bytes, expected_tiles: int) -> bool:
        """Validate CHR data"""
        expected_bytes = expected_tiles * 16
        return len(chr_data) == expected_bytes

# =============================================================================
# MAIN PIPELINE
# =============================================================================

class SpritePipeline:
    """Complete sprite processing pipeline"""

    def __init__(self, use_ai: bool = True):
        self.detector = SpriteDetector()
        self.palette_extractor = PaletteExtractor()
        self.scaler = SpriteScaler()
        self.indexer = SpriteIndexer(self.palette_extractor)
        self.chr_gen = CHRGenerator()
        self.use_ai = use_ai

        # Try to initialize Gemini if available
        self.gemini_client = None
        if use_ai:
            try:
                from google import genai
                api_key = os.getenv('GEMINI_API_KEY')
                if api_key:
                    self.gemini_client = genai.Client(api_key=api_key)
            except Exception as e:
                print(f"  [WARN] Gemini not available: {e}")

    def analyze_with_ai(self, img: Image.Image, img_path: str) -> Optional[Dict]:
        """Use Gemini to analyze sprite sheet structure"""
        if not self.gemini_client:
            return None

        try:
            from google.genai import types
            import tempfile

            # Save image for upload
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                img.save(tmp.name)
                tmp_path = tmp.name

            prompt = """Analyze this sprite sheet and identify the sprite types and actions.

Return JSON with this structure:
{
  "sprite_rows": [
    {"y_range": [start, end], "type": "player", "action": "idle", "frame_count": 6},
    {"y_range": [start, end], "type": "player", "action": "run", "frame_count": 6}
  ],
  "dominant_colors": ["magenta", "cyan", "white"],
  "style": "synthwave/cyberpunk",
  "notes": "any observations"
}

Focus on identifying:
1. What rows contain which animation types (idle, run, attack, etc.)
2. The main colors used
3. The artistic style

Return ONLY valid JSON."""

            with open(tmp_path, 'rb') as f:
                image_bytes = f.read()

            image_part = types.Part.from_bytes(data=image_bytes, mime_type='image/png')

            response = self.gemini_client.models.generate_content(
                model='gemini-2.0-flash',
                contents=[prompt, image_part]
            )

            os.unlink(tmp_path)

            # Parse response
            text = response.text.strip()
            if text.startswith('```'):
                text = text.split('\n', 1)[1]
            if text.endswith('```'):
                text = text.rsplit('\n', 1)[0]

            return json.loads(text)

        except Exception as e:
            print(f"  [WARN] AI analysis failed: {e}")
            return None

    def process(self, input_path: str, output_dir: str, target_size: int = 32) -> Dict:
        """Process sprite sheet through full pipeline"""
        print(f"\n{'='*60}")
        print("  NES Sprite Pipeline")
        print(f"{'='*60}")
        print(f"Input:  {input_path}")
        print(f"Output: {output_dir}")
        print()

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Load image
        img = Image.open(input_path).convert('RGBA')
        print(f"[1/6] Loaded image: {img.size[0]}x{img.size[1]}")

        # Step 1: AI Analysis (optional)
        print(f"\n[2/6] Analyzing sprite sheet...")
        ai_info = None
        if self.use_ai:
            ai_info = self.analyze_with_ai(img, input_path)
            if ai_info:
                print(f"  AI detected: {len(ai_info.get('sprite_rows', []))} animation rows")
                print(f"  Colors: {ai_info.get('dominant_colors', [])}")

        # Step 2: Detect sprites
        print(f"\n[3/6] Detecting sprites...")
        frames = self.detector.detect_all(img)
        print(f"  Found {len(frames)} sprite frames")

        # Enrich with AI info if available
        if ai_info and ai_info.get('sprite_rows'):
            for frame in frames:
                for row_info in ai_info['sprite_rows']:
                    y_range = row_info.get('y_range', [0, 0])
                    if y_range[0] <= frame.y <= y_range[1]:
                        frame.sprite_type = row_info.get('type', 'unknown')
                        frame.action = row_info.get('action', 'unknown')
                        break

        # Step 3: Extract dominant colors from entire sheet
        print(f"\n[4/6] Extracting palette...")
        dominant = self.palette_extractor.extract_dominant_colors(img, num_colors=4)
        nes_palette = self.palette_extractor.create_nes_palette(dominant)

        print(f"  Dominant RGB: {dominant}")
        print(f"  NES Palette: {['$%02X' % c for c in nes_palette]}")
        print(f"  Colors: {[NES_COLOR_NAMES.get(c, 'unknown') for c in nes_palette]}")

        # Process each frame
        print(f"\n[5/6] Processing {len(frames)} frames...")
        results = []

        for frame in frames:
            # Crop sprite
            sprite = img.crop((frame.x, frame.y, frame.x + frame.width, frame.y + frame.height))

            # Scale to NES size
            scaled = self.scaler.scale_to_nes(sprite, target_size)

            # Extract frame-specific palette for better accuracy
            frame_dominant = self.palette_extractor.extract_dominant_colors(scaled, num_colors=3)
            frame_palette = self.palette_extractor.create_nes_palette(frame_dominant)

            # Index to 4 colors
            indexed, palette = self.indexer.index_sprite(scaled, frame_palette)

            # Generate CHR
            chr_data = self.chr_gen.generate(indexed)

            # Save outputs
            safe_name = f"sprite_{frame.id:02d}_{frame.sprite_type}_{frame.action}"

            # Save debug images
            scaled.save(os.path.join(output_dir, f"{safe_name}_scaled.png"))
            indexed.save(os.path.join(output_dir, f"{safe_name}_indexed.png"))

            # Save CHR
            chr_path = os.path.join(output_dir, f"{safe_name}.chr")
            with open(chr_path, 'wb') as f:
                f.write(chr_data)

            frame.palette = palette
            results.append({
                'frame': asdict(frame),
                'chr_path': chr_path,
                'chr_size': len(chr_data),
                'palette': palette
            })

            print(f"  Frame {frame.id}: {frame.width}x{frame.height} -> {target_size}x{target_size}, "
                  f"palette={['$%02X' % c for c in palette]}")

        # Step 6: Create combined sprites.chr
        print(f"\n[6/6] Creating combined CHR file...")

        combined_chr = bytearray()
        for result in results[:4]:  # First 4 frames for animation
            with open(result['chr_path'], 'rb') as f:
                combined_chr.extend(f.read())

        # Pad to 8KB
        while len(combined_chr) < 8192:
            combined_chr.append(0)

        combined_path = os.path.join(output_dir, "sprites.chr")
        with open(combined_path, 'wb') as f:
            f.write(combined_chr)
        print(f"  Created: {combined_path} ({len(combined_chr)} bytes)")

        # Save metadata
        metadata = {
            'source': input_path,
            'target_size': target_size,
            'global_palette': nes_palette,
            'frames': results,
            'ai_analysis': ai_info
        }

        with open(os.path.join(output_dir, 'metadata.json'), 'w') as f:
            json.dump(metadata, f, indent=2)

        # Print recommended palette for game_main.asm
        print(f"\n{'='*60}")
        print("  Processing Complete!")
        print(f"{'='*60}")
        print(f"\nRecommended sprite palette for game_main.asm:")
        print(f"  .byte ${nes_palette[0]:02X}, ${nes_palette[1]:02X}, ${nes_palette[2]:02X}, ${nes_palette[3]:02X}")
        print(f"  ; {', '.join(NES_COLOR_NAMES.get(c, 'unknown') for c in nes_palette)}")

        return metadata


def main():
    parser = argparse.ArgumentParser(description='NES Sprite Processing Pipeline')
    parser.add_argument('input', help='Input sprite sheet PNG')
    parser.add_argument('-o', '--output', required=True, help='Output directory')
    parser.add_argument('--size', type=int, default=32, help='Target sprite size (default: 32)')
    parser.add_argument('--no-ai', action='store_true', help='Disable AI analysis')

    args = parser.parse_args()

    pipeline = SpritePipeline(use_ai=not args.no_ai)
    pipeline.process(args.input, args.output, target_size=args.size)


if __name__ == '__main__':
    main()
