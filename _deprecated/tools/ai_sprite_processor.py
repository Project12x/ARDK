#!/usr/bin/env python3
"""
AI-Accelerated Sprite Processor for NES Development

Uses Gemini Vision API for intelligent sprite extraction and analysis.
Processes AI-generated sprite sheets into NES-compatible CHR format.

Requirements:
    pip install pillow google-generativeai python-dotenv

Environment Variables:
    GEMINI_API_KEY - Your Gemini API key
    GROQ_API_KEY   - (Optional) Your Groq API key for text processing

Usage:
    python tools/ai_sprite_processor.py gfx/ai_output/player.png --output gfx/processed/player
"""

import os
import sys
import json
import hashlib
import argparse
from pathlib import Path
from PIL import Image, ImageDraw
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# NES Palette (subset - full palette has 64 colors)
NES_PALETTE = {
    0x0F: (0, 0, 0),           # Black
    0x00: (84, 84, 84),        # Dark Gray
    0x10: (0, 0, 168),         # Blue
    0x1C: (0, 228, 252),       # Cyan
    0x24: (252, 56, 228),      # Magenta
    0x30: (252, 252, 252),     # White
    0x16: (204, 76, 56),       # Red
    0x26: (252, 152, 56),      # Orange
    0x28: (252, 188, 0),       # Yellow
    0x1A: (0, 180, 0),         # Green
}

class AISpriteProcessor:
    """
    AI-accelerated sprite processing pipeline

    Workflow:
        1. Analyze sprite sheet with Gemini Vision
        2. Extract individual sprites
        3. Remove backgrounds
        4. Quantize to NES palette
        5. Generate CHR tiles
    """

    def __init__(self, api_key=None, cache_dir='.cache'):
        """
        Initialize processor

        Args:
            api_key: Gemini API key (or loads from GEMINI_API_KEY env var)
            cache_dir: Directory for caching API responses
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set. Either pass api_key or set environment variable.")

        # Configure Gemini with new API
        self.client = genai.Client(api_key=self.api_key)

        # Setup cache
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def analyze_sprite_sheet(self, image_path, use_cache=True):
        """
        Analyze sprite sheet with Gemini Vision

        Args:
            image_path: Path to sprite sheet PNG
            use_cache: Whether to use cached results

        Returns:
            Dict with sprite analysis results
        """
        # Check cache first
        cache_key = hashlib.md5(Path(image_path).read_bytes()).hexdigest()
        cache_file = self.cache_dir / f"analysis_{cache_key}.json"

        if use_cache and cache_file.exists():
            print(f"  [CACHE] Using cached analysis: {cache_file.name}")
            with open(cache_file) as f:
                return json.load(f)

        # Load image
        img = Image.open(image_path)

        # For large images, work with them directly (Gemini can handle up to 4096x4096)
        # But if too large, resize while preserving aspect ratio
        max_size = 2048
        if max(img.size) > max_size:
            scale = max_size / max(img.size)
            new_size = (int(img.size[0] * scale), int(img.size[1] * scale))
            img_for_analysis = img.resize(new_size, Image.LANCZOS)
            print(f"  Resized from {img.size} to {new_size} for analysis")
        else:
            img_for_analysis = img
            scale = 1.0

        # Craft prompt for Gemini
        prompt = f"""
        Analyze this sprite sheet for an NES game (image size: {img_for_analysis.size[0]}x{img_for_analysis.size[1]} pixels).

        IMPORTANT: Provide bounding boxes in PIXELS relative to this image size.

        NES SPRITE CONSTRAINTS:
        - Hardware sprites are 8x8 or 8x16 pixels
        - Game characters typically use 16x16, 16x24, or 24x24 composed of multiple hardware sprites
        - Maximum practical size is about 32x32 pixels (16 hardware sprites)

        TASK: Identify INDIVIDUAL sprite frames, NOT animation strips.
        - If you see a row of similar sprites (animation frames), identify EACH FRAME separately
        - Each sprite should be approximately square-ish (within 1:2 aspect ratio)
        - A 16x48 region is likely 3 separate 16x16 sprites - identify each one

        For each INDIVIDUAL sprite frame, provide:
        1. Bounding box [x, y, width, height] - for ONE sprite frame, not the whole strip
           - Width and height should typically be 16-32 pixels for game sprites
           - If you see a strip of frames, give bbox for just the FIRST frame
        2. Type: player, enemy, boss, npc, item, powerup, weapon, projectile, vfx, decoration, ui
        3. Natural language description: "rad 90s dude idle frame 1", "running frame 2", etc.
        4. Action: idle, walk, run, jump, attack, hurt, die, spin, etc.
        5. frame_size: [width, height] - size of ONE animation frame in pixels
        6. frame_count: number of frames if this is part of an animation strip
        7. frame_direction: "horizontal" or "vertical" - how frames are arranged
        8. Dominant colors (RGB hex)

        EXAMPLE: If you see a 128x32 horizontal strip with 4 character frames:
        {{
          "id": 1,
          "bbox": [0, 0, 32, 32],  // First frame only
          "type": "player",
          "description": "rad 90s dude running",
          "action": "run",
          "frame_size": [32, 32],
          "frame_count": 4,
          "frame_direction": "horizontal",
          "colors": ["#FF00FF", "#00FFFF"]
        }}

        Return ONLY valid JSON:
        {{
          "image_size": [width, height],
          "sprites": [
            {{
              "id": 1,
              "bbox": [x, y, w, h],
              "type": "player",
              "description": "character idle frame 1",
              "action": "idle",
              "frame_size": [16, 16],
              "frame_count": 4,
              "frame_direction": "horizontal",
              "colors": ["#FF00FF", "#00FFFF", "#FFFFFF"]
            }}
          ],
          "notes": "observations about the sprite sheet layout"
        }}

        Focus on identifying individual sprite frames suitable for NES.
        """

        print(f"  [AI] Analyzing sprite sheet with Gemini Vision...")
        try:
            # Upload image and generate content with new API
            # Save image temporarily for upload
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                img.save(tmp.name)
                tmp_path = tmp.name

            try:
                # Save analysis image for debugging
                img_for_analysis.save('debug_analysis_image.png')
                print(f"  Saved analysis image to debug_analysis_image.png ({img_for_analysis.size})")

                # Read image as bytes
                with open(tmp_path, 'rb') as f:
                    image_bytes = f.read()

                # Create image part
                image_part = types.Part.from_bytes(
                    data=image_bytes,
                    mime_type='image/png'
                )

                # Generate content using gemini-2.5-flash (only supported model)
                response = self.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[prompt, image_part]
                )

                # Parse JSON from response
                response_text = response.text.strip()

                # Scale bounding boxes back to original size if we resized
                # (We'll do this after parsing)

                # Remove markdown code blocks if present
                if response_text.startswith('```json'):
                    response_text = response_text[7:]
                if response_text.startswith('```'):
                    response_text = response_text[3:]
                if response_text.endswith('```'):
                    response_text = response_text[:-3]

                analysis = json.loads(response_text.strip())

                # Scale bounding boxes back to original size if needed
                if scale != 1.0:
                    print(f"  Scaling bounding boxes by {1/scale:.2f}x to match original image")
                    for sprite in analysis.get('sprites', []):
                        bbox = sprite['bbox']
                        sprite['bbox'] = [
                            int(bbox[0] / scale),
                            int(bbox[1] / scale),
                            int(bbox[2] / scale),
                            int(bbox[3] / scale)
                        ]

                # Update image_size to original
                analysis['image_size'] = list(img.size)
                analysis['analysis_scale'] = scale

                # Cache results
                with open(cache_file, 'w') as f:
                    json.dump(analysis, f, indent=2)

                print(f"  [OK] Found {len(analysis.get('sprites', []))} sprites")
                return analysis

            finally:
                # Clean up temp file
                os.unlink(tmp_path)

        except Exception as e:
            print(f"  [ERROR] Gemini analysis failed: {e}")
            print(f"  Tip: Free tier has rate limits. Wait a moment and try again.")
            raise

    def has_content(self, img, threshold=0.15, brightness_threshold=10):
        """
        Check if an image region has actual sprite content

        Args:
            img: PIL Image (RGBA)
            threshold: Minimum percentage of non-background pixels (0.0 to 1.0)
            brightness_threshold: Minimum RGB sum to be considered "content"

        Returns:
            Tuple of (has_content: bool, content_percentage: float)
        """
        pixels = img.load()
        width, height = img.size
        content_pixels = 0
        total_pixels = width * height

        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]
                # Consider a pixel "content" if it's not nearly black
                if r > brightness_threshold or g > brightness_threshold or b > brightness_threshold:
                    content_pixels += 1

        percentage = content_pixels / total_pixels
        return percentage >= threshold, percentage

    def scan_for_content_regions(self, img, grid_size=32, min_content=0.20):
        """
        Scan image for regions with actual content (fallback when AI analysis is wrong)

        Args:
            img: PIL Image
            grid_size: Size of grid cells to scan (default 32x32)
            min_content: Minimum content percentage to consider a region valid

        Returns:
            List of (x, y, w, h) bounding boxes for content regions
        """
        width, height = img.size
        content_regions = []

        print(f"    [SCAN] Scanning for content regions ({grid_size}x{grid_size} grid)...")

        for y in range(0, height - grid_size + 1, grid_size):
            for x in range(0, width - grid_size + 1, grid_size):
                region = img.crop((x, y, x + grid_size, y + grid_size))
                has_content, pct = self.has_content(region, threshold=min_content)

                if has_content:
                    content_regions.append((x, y, grid_size, grid_size, pct))

        # Merge adjacent regions into larger sprites
        # For now, just return individual regions sorted by content percentage
        content_regions.sort(key=lambda r: r[4], reverse=True)

        print(f"    [SCAN] Found {len(content_regions)} content regions")
        return [(x, y, w, h) for x, y, w, h, pct in content_regions]

    def find_tight_bounds(self, img, search_x, search_y, search_w, search_h, brightness_threshold=30):
        """
        Find the tight bounding box of actual sprite content within a search region.

        This compensates for AI giving approximate/incorrect coordinates by finding
        where the actual visible pixels are.

        Args:
            img: PIL Image (RGBA)
            search_x, search_y: Top-left of search region
            search_w, search_h: Size of search region
            brightness_threshold: Min RGB value to consider a pixel as content

        Returns:
            Tuple (x, y, w, h) of tight bounds, or None if no content found
        """
        pixels = img.load()
        img_w, img_h = img.size

        # Clamp search region to image bounds
        x1 = max(0, search_x)
        y1 = max(0, search_y)
        x2 = min(img_w, search_x + search_w)
        y2 = min(img_h, search_y + search_h)

        min_x, max_x = img_w, 0
        min_y, max_y = img_h, 0

        for y in range(y1, y2):
            for x in range(x1, x2):
                r, g, b, a = pixels[x, y]
                # Check for non-black content
                if r > brightness_threshold or g > brightness_threshold or b > brightness_threshold:
                    min_x = min(min_x, x)
                    max_x = max(max_x, x)
                    min_y = min(min_y, y)
                    max_y = max(max_y, y)

        if min_x < max_x and min_y < max_y:
            return (min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)
        return None

    def detect_sprite_rows(self, img, brightness_threshold=30):
        """
        Detect horizontal rows containing sprites in a sprite sheet.

        Many sprite sheets have rows of animation frames separated by empty space
        or text labels. This function finds where those rows are.

        Args:
            img: PIL Image
            brightness_threshold: Min RGB to consider content

        Returns:
            List of (y_start, y_end) tuples for each row containing sprites
        """
        pixels = img.load()
        width, height = img.size

        # Scan each row for content
        row_has_content = []
        for y in range(height):
            has_content = False
            for x in range(0, width, 4):  # Sample every 4th pixel for speed
                r, g, b, a = pixels[x, y]
                if r > brightness_threshold or g > brightness_threshold or b > brightness_threshold:
                    has_content = True
                    break
            row_has_content.append(has_content)

        # Find contiguous content regions (with some tolerance for gaps)
        rows = []
        in_content = False
        content_start = 0
        gap_count = 0
        max_gap = 10  # Allow up to 10 rows of gap within a sprite row

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
                        # End of content row
                        rows.append((content_start, y - gap_count))
                        in_content = False

        if in_content:
            rows.append((content_start, height - 1))

        return rows

    def detect_sprites_in_row(self, img, row_y_start, row_y_end, brightness_threshold=30, min_sprite_width=20):
        """
        Detect individual sprites within a horizontal row.

        Args:
            img: PIL Image
            row_y_start, row_y_end: Y bounds of the row
            brightness_threshold: Min RGB for content detection
            min_sprite_width: Minimum sprite width to detect

        Returns:
            List of (x, y, w, h) bounding boxes for sprites in the row
        """
        pixels = img.load()
        width = img.size[0]

        sprites = []
        in_sprite = False
        sprite_start_x = 0
        gap_count = 0
        max_gap = 8  # Allow small gaps within sprite (for internal transparent areas)

        for x in range(width):
            # Check if this column has content in the row
            has_content = False
            for y in range(row_y_start, row_y_end + 1):
                r, g, b, a = pixels[x, y]
                if r > brightness_threshold or g > brightness_threshold or b > brightness_threshold:
                    has_content = True
                    break

            if has_content:
                if not in_sprite:
                    sprite_start_x = x
                    in_sprite = True
                gap_count = 0
            else:
                if in_sprite:
                    gap_count += 1
                    if gap_count > max_gap:
                        # End of sprite
                        sprite_end_x = x - gap_count
                        sprite_w = sprite_end_x - sprite_start_x
                        if sprite_w >= min_sprite_width:
                            # Find tight Y bounds for this specific sprite
                            tight = self.find_tight_bounds(img, sprite_start_x, row_y_start,
                                                          sprite_w, row_y_end - row_y_start + 1)
                            if tight:
                                sprites.append(tight)
                        in_sprite = False

        # Handle sprite at end of row
        if in_sprite:
            sprite_end_x = width - gap_count
            sprite_w = sprite_end_x - sprite_start_x
            if sprite_w >= min_sprite_width:
                tight = self.find_tight_bounds(img, sprite_start_x, row_y_start,
                                              sprite_w, row_y_end - row_y_start + 1)
                if tight:
                    sprites.append(tight)

        return sprites

    def auto_detect_sprites(self, img):
        """
        Automatically detect all sprites in a sprite sheet using content scanning.

        This is a fallback/validation method when AI analysis gives incorrect bounds.

        Args:
            img: PIL Image

        Returns:
            List of (x, y, w, h) bounding boxes for detected sprites
        """
        print("    [AUTO] Auto-detecting sprites by content scan...")

        # Detect sprite rows
        rows = self.detect_sprite_rows(img)
        print(f"    [AUTO] Found {len(rows)} sprite rows")

        all_sprites = []
        for i, (y_start, y_end) in enumerate(rows):
            row_height = y_end - y_start
            print(f"    [AUTO] Row {i+1}: Y={y_start}-{y_end} (height={row_height})")

            sprites = self.detect_sprites_in_row(img, y_start, y_end)
            print(f"    [AUTO]   Found {len(sprites)} sprites in row")
            all_sprites.extend(sprites)

        return all_sprites

    def extract_sprites(self, image_path, analysis):
        """
        Extract individual sprites based on AI analysis with auto-detection fallback.

        Uses AI analysis as guidance but validates and corrects bounds using
        content-based detection. Falls back to pure auto-detection if AI bounds
        are significantly wrong.

        Args:
            image_path: Path to source sprite sheet
            analysis: Analysis results from analyze_sprite_sheet()

        Returns:
            List of (sprite_img, sprite_info) tuples
        """
        img = Image.open(image_path).convert('RGBA')
        extracted = []

        print(f"  [EXTRACT] Extracting sprites...")

        # First, run auto-detection to find actual sprite locations
        auto_sprites = self.auto_detect_sprites(img)
        print(f"  [EXTRACT] Auto-detection found {len(auto_sprites)} sprites")

        # If AI analysis found sprites, try to match them with auto-detected bounds
        ai_sprites = analysis.get('sprites', [])

        if len(auto_sprites) > 0 and len(ai_sprites) > 0:
            # Use auto-detected sprites but enrich with AI metadata
            print(f"  [EXTRACT] Using auto-detected bounds with AI metadata...")

            sprite_id_counter = 1
            for i, (x, y, w, h) in enumerate(auto_sprites):
                # Try to find matching AI sprite info by proximity
                best_match = None
                best_dist = float('inf')

                for ai_sprite in ai_sprites:
                    ai_x, ai_y, ai_w, ai_h = ai_sprite['bbox']
                    # Calculate center distance
                    cx1, cy1 = x + w/2, y + h/2
                    cx2, cy2 = ai_x + ai_w/2, ai_y + ai_h/2
                    dist = ((cx1 - cx2)**2 + (cy1 - cy2)**2)**0.5

                    if dist < best_dist and dist < 200:  # Within 200 pixels
                        best_dist = dist
                        best_match = ai_sprite

                # Create sprite info
                sprite_info = {
                    'id': sprite_id_counter,
                    'bbox': [x, y, w, h],
                    'type': best_match.get('type', 'unknown') if best_match else 'unknown',
                    'action': best_match.get('action', 'unknown') if best_match else 'unknown',
                    'description': best_match.get('description', f'sprite {sprite_id_counter}') if best_match else f'sprite {sprite_id_counter}',
                }

                # Crop the sprite
                sprite_img = img.crop((x, y, x + w, y + h))

                # Resize to NES-friendly size (32x32 target for characters)
                target_size = 32
                if w > target_size or h > target_size:
                    # Scale down while preserving aspect ratio
                    scale = min(target_size / w, target_size / h)
                    new_w = int(w * scale)
                    new_h = int(h * scale)
                    sprite_img = sprite_img.resize((new_w, new_h), Image.LANCZOS)

                    # Pad to 32x32
                    padded = Image.new('RGBA', (target_size, target_size), (0, 0, 0, 0))
                    paste_x = (target_size - new_w) // 2
                    paste_y = (target_size - new_h) // 2
                    padded.paste(sprite_img, (paste_x, paste_y))
                    sprite_img = padded

                # Validate content
                has_content, content_pct = self.has_content(sprite_img)
                if has_content:
                    extracted.append((sprite_img, sprite_info))
                    print(f"    Sprite {sprite_id_counter}: {w}x{h} at ({x},{y}) -> 32x32, {content_pct*100:.1f}% content [{sprite_info['type']}/{sprite_info['action']}]")
                    sprite_id_counter += 1

            return extracted

        # Fallback to original AI-based extraction if auto-detect failed
        print(f"  [EXTRACT] Falling back to AI-guided extraction...")

        sprite_id_counter = 1

        for sprite_info in ai_sprites:
            x, y, w, h = sprite_info['bbox']

            # Check if this is an animation strip that needs splitting
            frame_count = sprite_info.get('frame_count', 1)
            frame_size = sprite_info.get('frame_size', [w, h])
            frame_dir = sprite_info.get('frame_direction', 'horizontal')

            # If frame_count > 1 and we have frame_size, split the strip
            if frame_count > 1 and frame_size:
                fw, fh = frame_size[0], frame_size[1]

                # Ensure frame size is reasonable (at least 8x8, at most 64x64)
                fw = max(8, min(64, fw))
                fh = max(8, min(64, fh))

                # Round to multiple of 8
                fw = ((fw + 7) // 8) * 8
                fh = ((fh + 7) // 8) * 8

                print(f"    Animation strip: {frame_count} frames of {fw}x{fh} ({frame_dir})")

                # Extract each frame
                for frame_idx in range(frame_count):
                    if frame_dir == 'horizontal':
                        fx = x + frame_idx * fw
                        fy = y
                    else:  # vertical
                        fx = x
                        fy = y + frame_idx * fh

                    # Bounds check
                    if fx + fw > img.width or fy + fh > img.height:
                        print(f"      Frame {frame_idx + 1} out of bounds, skipping")
                        continue

                    frame_img = img.crop((fx, fy, fx + fw, fy + fh))

                    # Create frame info
                    frame_info = sprite_info.copy()
                    frame_info['id'] = sprite_id_counter
                    frame_info['bbox'] = [fx, fy, fw, fh]
                    frame_info['description'] = f"{sprite_info.get('description', 'sprite')} frame {frame_idx + 1}"
                    frame_info['frame_index'] = frame_idx
                    frame_info['original_strip_id'] = sprite_info['id']

                    # Validate frame has content
                    has_content, content_pct = self.has_content(frame_img)
                    if has_content:
                        extracted.append((frame_img, frame_info))
                        print(f"      Frame {frame_idx + 1}: {fw}x{fh} at ({fx}, {fy}) - {content_pct*100:.1f}% content")
                        sprite_id_counter += 1
                    else:
                        print(f"      Frame {frame_idx + 1}: SKIPPED (only {content_pct*100:.1f}% content)")

            else:
                # Single sprite or already individual frame
                sprite_img = img.crop((x, y, x + w, y + h))

                # Determine target size (NES-friendly)
                # Prefer common NES sprite sizes: 8x8, 16x16, 16x24, 24x24, 32x32
                target_sizes = [(8, 8), (16, 16), (16, 24), (24, 24), (32, 32), (24, 32), (32, 48)]

                # Find best matching size
                best_size = (16, 16)  # Default
                min_waste = float('inf')

                for tw, th in target_sizes:
                    if tw >= w and th >= h:
                        waste = (tw - w) + (th - h)
                        if waste < min_waste:
                            min_waste = waste
                            best_size = (tw, th)

                # If sprite is larger than our max, scale down or use actual size rounded to 8
                if w > 32 or h > 48:
                    best_size = (((w + 7) // 8) * 8, ((h + 7) // 8) * 8)

                # Resize/pad to target
                w_nes, h_nes = best_size

                # Create padded image
                padded = Image.new('RGBA', (w_nes, h_nes), (0, 0, 0, 0))
                # Center the sprite
                paste_x = (w_nes - sprite_img.width) // 2
                paste_y = (h_nes - sprite_img.height) // 2
                padded.paste(sprite_img, (paste_x, paste_y))

                sprite_info_copy = sprite_info.copy()
                sprite_info_copy['id'] = sprite_id_counter

                # Validate sprite has content
                has_content, content_pct = self.has_content(padded)
                if has_content:
                    extracted.append((padded, sprite_info_copy))
                    print(f"    Sprite {sprite_id_counter}: {w_nes}x{h_nes} ({sprite_info.get('type', 'unknown')}) - {content_pct*100:.1f}% content")
                    sprite_id_counter += 1
                else:
                    print(f"    Sprite SKIPPED: {w_nes}x{h_nes} (only {content_pct*100:.1f}% content)")

        # If AI analysis gave us empty sprites, fall back to content scanning
        if len(extracted) == 0:
            print(f"  [WARN] AI analysis returned no valid sprites, falling back to content scan...")
            content_regions = self.scan_for_content_regions(img, grid_size=32, min_content=0.20)

            # Take up to 20 best content regions
            for i, (x, y, w, h) in enumerate(content_regions[:20]):
                sprite_img = img.crop((x, y, x + w, y + h))
                sprite_info = {
                    'id': i + 1,
                    'type': 'unknown',
                    'action': 'unknown',
                    'description': f'auto-detected sprite {i + 1}',
                    'bbox': [x, y, w, h]
                }
                extracted.append((sprite_img, sprite_info))
                print(f"    Auto-detected sprite {i+1}: {w}x{h} at ({x}, {y})")

        print(f"  [OK] Extracted {len(extracted)} sprites/frames")
        return extracted

    def remove_background(self, img):
        """
        Remove background from sprite using smart edge detection

        Handles dark sprites by analyzing image brightness and using
        adaptive tolerance. For very dark images, uses color clustering
        to distinguish background from content.

        Args:
            img: PIL Image with RGBA

        Returns:
            PIL Image with background removed
        """
        pixels = img.load()
        width, height = img.size

        # Sample edge colors from all four corners and edges
        edge_samples = []
        # Corners
        edge_samples.append(pixels[0, 0][:3])
        edge_samples.append(pixels[width-1, 0][:3])
        edge_samples.append(pixels[0, height-1][:3])
        edge_samples.append(pixels[width-1, height-1][:3])
        # Mid-edges
        edge_samples.append(pixels[width//2, 0][:3])
        edge_samples.append(pixels[width//2, height-1][:3])
        edge_samples.append(pixels[0, height//2][:3])
        edge_samples.append(pixels[width-1, height//2][:3])

        # Calculate average edge color
        avg_r = sum(c[0] for c in edge_samples) // len(edge_samples)
        avg_g = sum(c[1] for c in edge_samples) // len(edge_samples)
        avg_b = sum(c[2] for c in edge_samples) // len(edge_samples)
        edge_color = (avg_r, avg_g, avg_b)
        edge_brightness = (avg_r + avg_g + avg_b) / 3

        # Analyze overall image brightness
        total_brightness = 0
        non_edge_pixels = 0
        unique_colors = set()

        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]
                if a > 0:  # Only count non-transparent pixels
                    brightness = (r + g + b) / 3
                    total_brightness += brightness
                    non_edge_pixels += 1
                    unique_colors.add((r, g, b))

        avg_brightness = total_brightness / max(1, non_edge_pixels)

        print(f"    Background analysis: edge_color={edge_color}, edge_brightness={edge_brightness:.1f}, avg_brightness={avg_brightness:.1f}, unique_colors={len(unique_colors)}")

        # Adaptive tolerance based on image characteristics
        if edge_brightness < 10:
            # Very dark background - use very tight tolerance
            # to avoid removing dark sprite content
            if avg_brightness < 30:
                # Both background AND content are dark - risky situation
                # Use minimum tolerance and check for color variance
                tolerance = 5
                print(f"    [WARN] Very dark image detected - using tight tolerance={tolerance}")
            else:
                # Dark background but brighter content - safe to use moderate tolerance
                tolerance = 15
                print(f"    Dark background detected - using tolerance={tolerance}")
        elif edge_brightness < 50:
            # Moderately dark background
            tolerance = 25
        else:
            # Normal/bright background
            tolerance = 40

        # If the image has very few unique colors (< 10), it might be
        # an AI sprite with limited palette - be more careful
        if len(unique_colors) < 10:
            tolerance = min(tolerance, 15)
            print(f"    Low color variance ({len(unique_colors)} colors) - clamping tolerance to {tolerance}")

        # Flood fill from edges
        to_check = set()
        for x in range(width):
            to_check.add((x, 0))
            to_check.add((x, height-1))
        for y in range(height):
            to_check.add((0, y))
            to_check.add((width-1, y))

        visited = set()
        removed_count = 0

        while to_check:
            x, y = to_check.pop()

            if (x, y) in visited or x < 0 or x >= width or y < 0 or y >= height:
                continue

            visited.add((x, y))

            r, g, b, a = pixels[x, y]
            er, eg, eb = edge_color
            diff = abs(r - er) + abs(g - eg) + abs(b - eb)

            if diff <= tolerance:
                pixels[x, y] = (0, 0, 0, 0)  # Make transparent
                removed_count += 1
                to_check.update([(x+1, y), (x-1, y), (x, y+1), (x, y-1)])

        total_pixels = width * height
        remaining = total_pixels - removed_count
        print(f"    Background removal: removed {removed_count}/{total_pixels} pixels, {remaining} remaining")

        # Safety check: if we removed almost everything, warn the user
        if remaining < total_pixels * 0.05:  # Less than 5% remaining
            print(f"    [WARN] Almost all pixels were removed! Sprite may be too dark or have same color as background.")

        return img

    def map_to_nes_color(self, rgb):
        """
        Map RGB color to nearest NES palette color

        Args:
            rgb: Tuple of (r, g, b)

        Returns:
            NES palette index
        """
        min_dist = float('inf')
        best_idx = 0x30  # Default to white

        for nes_idx, nes_rgb in NES_PALETTE.items():
            dist = sum((a-b)**2 for a, b in zip(rgb[:3], nes_rgb))
            if dist < min_dist:
                min_dist = dist
                best_idx = nes_idx

        return best_idx

    def quantize_to_nes(self, img, num_colors=4):
        """
        Quantize image to NES 4-color palette

        Args:
            img: PIL Image (RGBA)
            num_colors: Number of colors (typically 4 for NES sprites)

        Returns:
            Indexed PIL Image with NES palette
        """
        # Get non-transparent pixels
        pixels = list(img.getdata())
        opaque_pixels = [p[:3] for p in pixels if p[3] > 128]

        if len(opaque_pixels) < num_colors:
            # Not enough colors, use defaults
            nes_colors = [0x0F, 0x24, 0x1C, 0x30]
        else:
            # Use k-means to find dominant colors
            from sklearn.cluster import KMeans
            kmeans = KMeans(n_clusters=num_colors-1, n_init=10)
            kmeans.fit(opaque_pixels)

            # Map cluster centers to NES colors
            nes_colors = [0x0F]  # Black (transparent)
            for center in kmeans.cluster_centers_:
                nes_idx = self.map_to_nes_color(center)
                nes_colors.append(nes_idx)

        # Create indexed image
        indexed_img = Image.new('P', img.size)
        indexed_pixels = []

        for pixel in pixels:
            if pixel[3] < 128:
                indexed_pixels.append(0)  # Transparent
            else:
                # Find closest NES color
                min_dist = float('inf')
                best_idx = 1
                for i, nes_idx in enumerate(nes_colors):
                    if i == 0:
                        continue  # Skip transparent
                    nes_rgb = NES_PALETTE[nes_idx]
                    dist = sum((a-b)**2 for a, b in zip(pixel[:3], nes_rgb))
                    if dist < min_dist:
                        min_dist = dist
                        best_idx = i
                indexed_pixels.append(best_idx)

        indexed_img.putdata(indexed_pixels)

        # Set palette
        palette = []
        for nes_idx in nes_colors:
            palette.extend(NES_PALETTE[nes_idx])
        palette.extend([0, 0, 0] * (256 - num_colors))
        indexed_img.putpalette(palette)

        return indexed_img, nes_colors

    def generate_chr(self, indexed_img):
        """
        Convert indexed PNG to CHR format using established conversion method

        Args:
            indexed_img: Indexed PIL Image (4 colors, dimensions multiple of 8)

        Returns:
            Bytes of CHR data
        """
        # Use the proven png2chr conversion algorithm
        import subprocess
        import tempfile

        # Save indexed PNG temporarily
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_png:
            indexed_img.save(tmp_png.name)
            png_path = tmp_png.name

        with tempfile.NamedTemporaryFile(suffix='.chr', delete=False) as tmp_chr:
            chr_path = tmp_chr.name

        try:
            # Use our proven png2chr.py tool
            result = subprocess.run(
                ['python3', 'tools/png2chr.py', png_path, chr_path],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                print(f"    Warning: png2chr failed, using built-in converter")
                print(f"    Error: {result.stderr}")
                # Fallback to built-in
                return self._generate_chr_builtin(indexed_img)

            # Read generated CHR
            with open(chr_path, 'rb') as f:
                chr_data = f.read()

            return chr_data

        finally:
            # Clean up temp files
            import os
            try:
                os.unlink(png_path)
                os.unlink(chr_path)
            except:
                pass

    def _generate_chr_builtin(self, indexed_img):
        """Fallback built-in CHR converter"""
        width, height = indexed_img.size
        tiles_x = width // 8
        tiles_y = height // 8

        chr_data = bytearray()
        pixels = list(indexed_img.getdata())

        for ty in range(tiles_y):
            for tx in range(tiles_x):
                # Extract 8x8 tile
                tile_pixels = []
                for py in range(8):
                    for px in range(8):
                        x = tx * 8 + px
                        y = ty * 8 + py
                        pixel = pixels[y * width + x]
                        tile_pixels.append(pixel)

                # Encode as CHR (2 bitplanes)
                plane0 = bytearray(8)
                plane1 = bytearray(8)

                for py in range(8):
                    for px in range(8):
                        pixel = tile_pixels[py * 8 + px]
                        if pixel & 1:
                            plane0[py] |= (1 << (7 - px))
                        if pixel & 2:
                            plane1[py] |= (1 << (7 - px))

                chr_data.extend(plane0)
                chr_data.extend(plane1)

        return bytes(chr_data)

    def process(self, input_path, output_dir, sprite_type=None):
        """
        Full processing pipeline

        Args:
            input_path: Path to AI-generated sprite sheet
            output_dir: Output directory for processed assets
            sprite_type: Optional filter (player, enemy, item, etc.)

        Returns:
            Dict with processing results
        """
        print(f"\n{'='*60}")
        print(f"  AI Sprite Processor - Powered by Gemini Vision")
        print(f"{'='*60}")
        print(f"Input:  {input_path}")
        print(f"Output: {output_dir}")
        print()

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Step 1: Analyze with AI
        print("[1/5] Analyzing sprite sheet...")
        analysis = self.analyze_sprite_sheet(input_path)

        # Save analysis
        with open(output_path / 'analysis.json', 'w') as f:
            json.dump(analysis, f, indent=2)

        # Step 2: Extract sprites
        print("\n[2/5] Extracting sprites...")
        extracted = self.extract_sprites(input_path, analysis)

        # Filter by type if specified
        if sprite_type:
            extracted = [(img, info) for img, info in extracted if info['type'] == sprite_type]
            print(f"  Filtered to {len(extracted)} {sprite_type} sprites")

        # Step 3: Process each sprite
        print("\n[3/5] Removing backgrounds...")
        processed = []
        for i, (sprite_img, info) in enumerate(extracted):
            sprite_nobg = self.remove_background(sprite_img)
            processed.append((sprite_nobg, info))

            # Save intermediate
            sprite_nobg.save(output_path / f"sprite_{i+1}_nobg.png")

        # Step 4: Quantize to NES palette
        print("\n[4/5] Quantizing to NES palette...")
        quantized = []
        for i, (sprite_img, info) in enumerate(processed):
            indexed, nes_colors = self.quantize_to_nes(sprite_img)
            quantized.append((indexed, info, nes_colors))

            # Save indexed PNG
            indexed.save(output_path / f"sprite_{i+1}_indexed.png")

            print(f"  Sprite {i+1}: Palette {', '.join(f'${c:02X}' for c in nes_colors)}")

        # Step 5: Generate CHR files with organized folders
        print("\n[5/5] Generating CHR tiles and organizing...")
        chr_outputs = []
        for i, (indexed_img, info, nes_colors) in enumerate(quantized):
            chr_data = self.generate_chr(indexed_img)

            # Create organized folder structure
            sprite_type = info['type']
            action = info.get('action', 'default')
            description = info.get('description', f'sprite_{i+1}')

            # Sanitize description for filename
            safe_desc = description.lower().replace(' ', '_').replace('/', '_')
            safe_desc = ''.join(c for c in safe_desc if c.isalnum() or c == '_')

            # Create subfolder: type/action/
            subfolder = output_path / sprite_type / action
            subfolder.mkdir(parents=True, exist_ok=True)

            # Save files with descriptive names
            chr_path = subfolder / f"{safe_desc}.chr"
            png_path = subfolder / f"{safe_desc}.png"

            with open(chr_path, 'wb') as f:
                f.write(chr_data)

            # Also save the indexed PNG for reference
            indexed_img.save(png_path)

            chr_outputs.append({
                'id': info['id'],
                'type': info['type'],
                'action': action,
                'description': description,
                'chr_file': str(chr_path),
                'png_file': str(png_path),
                'size': indexed_img.size,
                'palette': nes_colors,
                'tile_count': len(chr_data) // 16
            })

            print(f"  [{sprite_type}/{action}] {safe_desc}.chr: {len(chr_data)} bytes ({len(chr_data)//16} tiles)")

        # Save metadata
        metadata = {
            'source': str(input_path),
            'analysis': analysis,
            'sprites': chr_outputs
        }

        with open(output_path / 'metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"\n{'='*60}")
        print(f"  Processing complete!")
        print(f"  Generated {len(chr_outputs)} CHR files")
        print(f"{'='*60}")

        # Show organized structure
        print("\nOrganized sprites by category:")
        by_type = {}
        for spr in chr_outputs:
            key = f"{spr['type']}/{spr['action']}"
            if key not in by_type:
                by_type[key] = []
            by_type[key].append(spr['description'])

        for category, sprites in sorted(by_type.items()):
            print(f"\n  {category}/")
            for desc in sprites:
                print(f"    - {desc}")

        print()
        return metadata


def main():
    parser = argparse.ArgumentParser(
        description='AI-accelerated sprite processor for NES',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Process player sprites
    python tools/ai_sprite_processor.py gfx/ai_output/player.png --output gfx/processed/player

    # Process only enemy sprites from sheet
    python tools/ai_sprite_processor.py gfx/ai_output/enemies.png --output gfx/processed/enemies --type enemy

    # Use cached analysis
    python tools/ai_sprite_processor.py gfx/ai_output/items.png --output gfx/processed/items --cache
        """
    )

    parser.add_argument('input', help='Input sprite sheet PNG')
    parser.add_argument('--output', '-o', required=True, help='Output directory')
    parser.add_argument('--type', '-t', help='Filter by sprite type (player, enemy, item, etc.)')
    parser.add_argument('--api-key', help='Gemini API key (or set GEMINI_API_KEY env var)')
    parser.add_argument('--no-cache', action='store_true', help='Disable API response caching')

    args = parser.parse_args()

    # Check API key
    api_key = args.api_key or os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set")
        print("\nSet environment variable:")
        print("  export GEMINI_API_KEY='your_key_here'")
        print("\nOr create .env file:")
        print("  echo 'GEMINI_API_KEY=your_key_here' > .env")
        sys.exit(1)

    # Process sprites
    try:
        processor = AISpriteProcessor(api_key=api_key)
        results = processor.process(
            args.input,
            args.output,
            sprite_type=args.type
        )

        print("\n[OK] Success! Next steps:")
        print(f"  1. Review sprites in: {args.output}/")
        print(f"  2. Copy CHR files to: src/game/assets/")
        print(f"  3. Update sprite_tiles.inc with tile indices")
        print(f"  4. Rebuild ROM: compile.bat")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
