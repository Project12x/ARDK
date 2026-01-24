"""
Pipeline Bridge - Integrates unified_pipeline components into HAL Demo.

This module bridges the advanced sprite processing tools from tools/unified_pipeline.py
into the HAL demo's asset build process, enabling:
- Multi-AI consensus sprite detection
- FloodFill-based background removal
- Tier system palette management
- Model-per-task optimization

Usage:
    from pipeline_bridge import (
        detect_sprites_consensus,
        detect_background_smart,
        get_nes_palette_config,
        get_best_model,
    )
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any

# Add tools directory to path for imports
TOOLS_DIR = Path(__file__).parent.parent.parent / 'tools'
sys.path.insert(0, str(TOOLS_DIR))

try:
    from PIL import Image
    import numpy as np
except ImportError:
    raise ImportError("PIL and numpy required: pip install pillow numpy")


# =============================================================================
# Model Selection (from base_generator.py MODEL_MAP)
# =============================================================================

MODEL_MAP = {
    'image_generation': 'flux',           # Best pixel-art output, clean edges
    'sprite_detection': 'gemini-fast',    # Fast bounding box detection
    'palette_extraction': 'openai-large', # Best color understanding
    'animation_analysis': 'gemini',       # Frame timing, motion detection
    'layout_analysis': 'gemini-large',    # Complex sheet parsing
    'general': 'openai',                  # Fallback for misc tasks
}


def get_best_model(task: str) -> str:
    """Get the optimal model for a specific task."""
    return MODEL_MAP.get(task, MODEL_MAP['general'])


# =============================================================================
# NES Palette from tier_system.py
# =============================================================================

# NES Master Palette (2C02 NTSC, commonly used approximation)
NES_MASTER_PALETTE = [
    # Row 0 (Grays + Dark Colors)
    (0x7C, 0x7C, 0x7C), (0x00, 0x00, 0xFC), (0x00, 0x00, 0xBC), (0x44, 0x28, 0xBC),
    (0x94, 0x00, 0x84), (0xA8, 0x00, 0x20), (0xA8, 0x10, 0x00), (0x88, 0x14, 0x00),
    (0x50, 0x30, 0x00), (0x00, 0x78, 0x00), (0x00, 0x68, 0x00), (0x00, 0x58, 0x00),
    (0x00, 0x40, 0x58), (0x00, 0x00, 0x00), (0x00, 0x00, 0x00), (0x00, 0x00, 0x00),
    # Row 1 (Midtones)
    (0xBC, 0xBC, 0xBC), (0x00, 0x78, 0xF8), (0x00, 0x58, 0xF8), (0x68, 0x44, 0xFC),
    (0xD8, 0x00, 0xCC), (0xE4, 0x00, 0x58), (0xF8, 0x38, 0x00), (0xE4, 0x5C, 0x10),
    (0xAC, 0x7C, 0x00), (0x00, 0xB8, 0x00), (0x00, 0xA8, 0x00), (0x00, 0xA8, 0x44),
    (0x00, 0x88, 0x88), (0x00, 0x00, 0x00), (0x00, 0x00, 0x00), (0x00, 0x00, 0x00),
    # Row 2 (Highlights)
    (0xF8, 0xF8, 0xF8), (0x3C, 0xBC, 0xFC), (0x68, 0x88, 0xFC), (0x98, 0x78, 0xF8),
    (0xF8, 0x78, 0xF8), (0xF8, 0x58, 0x98), (0xF8, 0x78, 0x58), (0xFC, 0xA0, 0x44),
    (0xF8, 0xB8, 0x00), (0xB8, 0xF8, 0x18), (0x58, 0xD8, 0x54), (0x58, 0xF8, 0x98),
    (0x00, 0xE8, 0xD8), (0x78, 0x78, 0x78), (0x00, 0x00, 0x00), (0x00, 0x00, 0x00),
    # Row 3 (Pastels)
    (0xFC, 0xFC, 0xFC), (0xA4, 0xE4, 0xFC), (0xB8, 0xB8, 0xF8), (0xD8, 0xB8, 0xF8),
    (0xF8, 0xB8, 0xF8), (0xF8, 0xA4, 0xC0), (0xF0, 0xD0, 0xB0), (0xFC, 0xE0, 0xA8),
    (0xF8, 0xD8, 0x78), (0xD8, 0xF8, 0x78), (0xB8, 0xF8, 0xB8), (0xB8, 0xF8, 0xD8),
    (0x00, 0xFC, 0xFC), (0xF8, 0xD8, 0xF8), (0x00, 0x00, 0x00), (0x00, 0x00, 0x00),
]

# NES palette indices mapped to RGB for quick lookup
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


def get_nearest_nes_color(
    color: Tuple[int, int, int],
    method: str = "weighted_luminance",
) -> int:
    """
    Find the nearest NES palette index for an RGB color.

    Args:
        color: RGB tuple (r, g, b)
        method: "euclidean", "weighted_luminance", or "perceptual"

    Returns:
        NES palette index (0x00-0x3F)
    """
    best_idx = 0x0F  # Default to black
    min_dist = float('inf')

    for idx, nes_rgb in NES_PALETTE_RGB.items():
        if method == "euclidean":
            dist = sum((a - b) ** 2 for a, b in zip(color, nes_rgb))
        elif method == "weighted_luminance":
            # Weight by human luminance perception
            dist = (
                0.299 * (color[0] - nes_rgb[0]) ** 2 +
                0.587 * (color[1] - nes_rgb[1]) ** 2 +
                0.114 * (color[2] - nes_rgb[2]) ** 2
            )
        else:  # perceptual
            # Simplified CIE76-inspired
            dist = sum((a - b) ** 2 for a, b in zip(color, nes_rgb))

        if dist < min_dist:
            min_dist = dist
            best_idx = idx

    return best_idx


def get_nes_palette_config() -> Dict[str, Any]:
    """Get NES platform palette configuration."""
    return {
        'bits_per_channel': 6,
        'total_palette_colors': 64,
        'colors_per_subpalette': 4,
        'num_subpalettes': 4,
        'transparent_index': 0,
        'hardware_palette': NES_MASTER_PALETTE,
    }


# =============================================================================
# FloodFill Background Detector (from unified_pipeline.py)
# =============================================================================

class FloodFillBackgroundDetector:
    """
    Robust background removal using Edge-Initiated Flood Fill.

    Instead of assuming "black = transparent" (which kills internal black pixels),
    this finds the background color by sampling image corners/edges, then
    performs a flood-fill from the outside in.

    Any pixel NOT reached by the flood-fill is considered "Content",
    preserving internal blacks.
    """

    def __init__(self, tolerance: int = 15):
        self.tolerance = tolerance

    def detect_background_color(self, img: Image.Image) -> Optional[Tuple[int, int, int]]:
        """
        Sample 4 corners to find dominant background color.
        Returns None if corners strongly disagree (Full Frame Background).
        """
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        pixels = img.load()
        w, h = img.size

        # Sample just the 4 extreme corners
        corners = [
            (0, 0), (w-1, 0), (0, h-1), (w-1, h-1)
        ]

        samples = []
        for x, y in corners:
            pixel = pixels[x, y]
            if len(pixel) == 4:
                r, g, b, a = pixel
            else:
                r, g, b = pixel
                a = 255

            # Treat transparent as a valid "color" or note it
            if a < 128:
                samples.append(None)  # Transparent corner
            else:
                samples.append((r, g, b))

        # Filter out transparent corners
        solid_samples = [s for s in samples if s is not None]

        if not solid_samples:
            # All corners transparent - background IS transparent
            return None

        if len(solid_samples) < 2:
            # Only 1 solid corner, unreliable
            return solid_samples[0] if solid_samples else None

        # Check consistency
        first = solid_samples[0]
        disagreements = 0
        for s in solid_samples[1:]:
            # Simple Manhattan distance check
            dist = abs(first[0] - s[0]) + abs(first[1] - s[1]) + abs(first[2] - s[2])
            if dist > 45:  # Tolerance for corner variance
                disagreements += 1

        # If corners are too different, assume full-frame (no solid BG)
        if disagreements > 1:
            print("      [SmartBg] Corners differ significantly. Assuming complex background.")
            return None

        # Return the most common or average color
        from collections import Counter
        most_common = Counter(solid_samples).most_common(1)[0][0]
        return most_common

    def get_content_mask(self, img: Image.Image) -> Image.Image:
        """
        Returns a binary mask image where white=Content, black=Background.
        Uses flood fill from edges to identify background.
        """
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        w, h = img.size
        pixels = np.array(img)

        # Detect background color
        bg_color = self.detect_background_color(img)

        if bg_color is None:
            # Full frame content (all white mask)
            return Image.new('L', (w, h), 255)

        # Create visited array and mask
        visited = np.zeros((h, w), dtype=bool)
        mask = np.ones((h, w), dtype=np.uint8) * 255  # Start as all content

        # Flood fill from all edges
        from collections import deque
        queue = deque()

        # Add all edge pixels to queue
        for x in range(w):
            queue.append((x, 0))
            queue.append((x, h-1))
        for y in range(h):
            queue.append((0, y))
            queue.append((w-1, y))

        bg_r, bg_g, bg_b = bg_color

        while queue:
            x, y = queue.popleft()

            if x < 0 or x >= w or y < 0 or y >= h:
                continue
            if visited[y, x]:
                continue

            visited[y, x] = True

            r, g, b, a = pixels[y, x]

            # Check if this pixel matches background
            if a < 128:
                # Transparent = background
                mask[y, x] = 0
                # Add neighbors
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    queue.append((x + dx, y + dy))
            else:
                dist = abs(int(r) - bg_r) + abs(int(g) - bg_g) + abs(int(b) - bg_b)
                if dist <= self.tolerance:
                    # Background pixel
                    mask[y, x] = 0
                    # Add neighbors
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        queue.append((x + dx, y + dy))
                # Else: content pixel, don't expand

        return Image.fromarray(mask, mode='L')


def detect_background_smart(img: Image.Image, tolerance: int = 15) -> Optional[Tuple[int, int, int]]:
    """
    Convenience function to detect background color using FloodFillBackgroundDetector.

    Args:
        img: PIL Image
        tolerance: Color distance tolerance for matching

    Returns:
        RGB tuple of background color, or None if no solid background detected
    """
    detector = FloodFillBackgroundDetector(tolerance=tolerance)
    return detector.detect_background_color(img)


def get_content_mask(img: Image.Image, tolerance: int = 15) -> Image.Image:
    """
    Get a binary mask of content (sprite) vs background.

    Args:
        img: PIL Image
        tolerance: Color distance tolerance

    Returns:
        PIL Image in mode 'L' where 255=content, 0=background
    """
    detector = FloodFillBackgroundDetector(tolerance=tolerance)
    return detector.get_content_mask(img)


# =============================================================================
# Multi-Model Sprite Detection (Simplified Consensus)
# =============================================================================

import json
import base64
import urllib.request
import urllib.error
from io import BytesIO

POLLINATIONS_API_KEY = "sk_pHTAsUugsKvRUwFfxzOnpStVkpROBgzM"


def _call_vision_api(img: Image.Image, prompt: str, model: str) -> Optional[str]:
    """Call Pollinations vision API with specified model."""
    buffer = BytesIO()
    if img.mode != 'RGB':
        img_rgb = img.convert('RGB')
    else:
        img_rgb = img
    img_rgb.save(buffer, format='JPEG', quality=85)
    img_b64 = base64.b64encode(buffer.getvalue()).decode()

    payload = {
        "model": model,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
            ]
        }],
        "max_tokens": 2000
    }

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {POLLINATIONS_API_KEY}'
    }

    try:
        req = urllib.request.Request(
            "https://gen.pollinations.ai/v1/chat/completions",
            data=json.dumps(payload).encode('utf-8'),
            headers=headers,
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode('utf-8'))

        return result.get('choices', [{}])[0].get('message', {}).get('content', '')
    except Exception as e:
        print(f"      [AI ERROR] {model}: {e}")
        return None


def _parse_bbox_response(response: str) -> Optional[Dict[str, int]]:
    """Parse bounding box JSON from AI response."""
    if not response:
        return None

    import re
    # Try to find JSON object
    json_match = re.search(r'\{[^}]+\}', response)
    if json_match:
        try:
            data = json.loads(json_match.group())
            if all(k in data for k in ['x', 'y', 'width', 'height']):
                return data
        except json.JSONDecodeError:
            pass
    return None


def _calculate_iou(b1: Dict[str, int], b2: Dict[str, int]) -> float:
    """Calculate Intersection over Union for two bounding boxes."""
    x_left = max(b1['x'], b2['x'])
    y_top = max(b1['y'], b2['y'])
    x_right = min(b1['x'] + b1['width'], b2['x'] + b2['width'])
    y_bottom = min(b1['y'] + b1['height'], b2['y'] + b2['height'])

    if x_right < x_left or y_bottom < y_top:
        return 0.0

    intersection = (x_right - x_left) * (y_bottom - y_top)
    area1 = b1['width'] * b1['height']
    area2 = b2['width'] * b2['height']

    if area1 + area2 == 0:
        return 0.0

    union = area1 + area2 - intersection
    return intersection / union


def detect_sprite_consensus(
    img: Image.Image,
    sprite_type: str = "character sprite",
    models: List[str] = None,
    min_agreement: int = 2,
    iou_threshold: float = 0.5,
) -> Optional[Dict[str, int]]:
    """
    Detect sprite location using multi-model consensus.

    Queries multiple AI models and returns a bounding box only if
    at least `min_agreement` models agree (based on IoU threshold).

    Args:
        img: PIL Image containing sprite sheet
        sprite_type: Description of what to find
        models: List of model names to query (default: gemini-fast, openai-large, gemini)
        min_agreement: Minimum models that must agree
        iou_threshold: IoU threshold to consider boxes as "agreeing"

    Returns:
        Consensus bounding box dict or None if no agreement
    """
    if models is None:
        models = ['gemini-fast', 'openai-large', 'gemini']

    prompt = f"""Analyze this sprite sheet image. Find the FIRST COMPLETE {sprite_type}.

IMPORTANT: Return the FULL sprite bounds, including the entire character.
Sprites in this sheet may be 60-150 pixels in size.
IGNORE any text labels - only find the actual sprite graphic.

Return ONLY a JSON object with the bounding box:
{{"x": <left>, "y": <top>, "width": <width>, "height": <height>}}

The coordinates should capture the ENTIRE sprite, not just a portion.
Return ONLY the JSON, no other text."""

    print(f"      [Consensus] Querying {len(models)} models...")

    # Collect responses from each model
    responses = {}
    for model in models:
        print(f"        - {model}...", end=" ")
        response = _call_vision_api(img, prompt, model)
        bbox = _parse_bbox_response(response)
        if bbox:
            # Validate size
            if bbox['width'] >= 30 and bbox['height'] >= 30:
                responses[model] = bbox
                print(f"OK ({bbox['width']}x{bbox['height']})")
            else:
                print(f"too small ({bbox['width']}x{bbox['height']})")
        else:
            print("failed")

    if not responses:
        print("      [Consensus] All models failed!")
        return None

    # If only one model succeeded, use it but warn
    if len(responses) == 1:
        model, bbox = list(responses.items())[0]
        print(f"      [Consensus] Only {model} succeeded - using without consensus")
        return bbox

    # Find agreeing boxes using IoU clustering
    boxes = list(responses.values())
    model_names = list(responses.keys())

    # Check pairwise IoU and find largest agreeing cluster
    best_cluster = []
    best_avg_box = None

    for i, b1 in enumerate(boxes):
        cluster = [i]
        for j, b2 in enumerate(boxes):
            if i != j:
                iou = _calculate_iou(b1, b2)
                if iou >= iou_threshold:
                    cluster.append(j)

        if len(cluster) >= min_agreement and len(cluster) > len(best_cluster):
            best_cluster = cluster
            # Average the boxes in the cluster
            avg_x = sum(boxes[k]['x'] for k in cluster) // len(cluster)
            avg_y = sum(boxes[k]['y'] for k in cluster) // len(cluster)
            avg_w = sum(boxes[k]['width'] for k in cluster) // len(cluster)
            avg_h = sum(boxes[k]['height'] for k in cluster) // len(cluster)
            best_avg_box = {'x': avg_x, 'y': avg_y, 'width': avg_w, 'height': avg_h}

    if best_avg_box:
        agreeing_models = [model_names[i] for i in best_cluster]
        print(f"      [Consensus] {len(best_cluster)} models agree: {agreeing_models}")
        print(f"      [Consensus] Result: x={best_avg_box['x']}, y={best_avg_box['y']}, "
              f"{best_avg_box['width']}x{best_avg_box['height']}")
        return best_avg_box

    # No consensus - use largest box as fallback
    print(f"      [Consensus] No agreement (IoU < {iou_threshold}) - using largest box")
    largest = max(boxes, key=lambda b: b['width'] * b['height'])
    return largest


def detect_sprites_consensus(
    img: Image.Image,
    sprite_type: str = "character sprite",
    models: List[str] = None,
) -> List[Dict[str, int]]:
    """
    Detect multiple sprites using consensus.

    Currently returns a list with single sprite for compatibility.
    Future: extend to detect multiple sprites.
    """
    bbox = detect_sprite_consensus(img, sprite_type, models)
    if bbox:
        return [bbox]
    return []


# =============================================================================
# AI Palette Extraction (using optimal model)
# =============================================================================

def extract_palette_ai(
    img: Image.Image,
    num_colors: int = 4,
) -> Optional[List[int]]:
    """
    Use AI to extract optimal NES palette for image.

    Uses openai-large model which has best color understanding.

    Args:
        img: PIL Image to analyze
        num_colors: Number of palette colors (including transparent)

    Returns:
        List of NES palette indices, or None on failure
    """
    model = get_best_model('palette_extraction')  # openai-large

    prompt = f"""Analyze the dominant colors in this sprite/image for NES conversion.

Pick exactly {num_colors} NES colors that best represent this image.
First color MUST be $0F (black) for transparency.
Pick colors with good brightness spread (dark, mid, bright).

Available NES colors:
$0F: Black, $00: Dark Gray, $10: Gray, $20/$30: White
$01-$0C: Dark colors (blues, purples, reds, greens, cyans)
$11-$1C: Medium colors
$21-$2C: Bright colors (blues, magentas, reds, greens, cyans)

For synthwave/neon style: prefer $24 (magenta), $2C (cyan), $30 (white)
For natural colors: use greens ($0A, $1A, $2A) and browns ($07, $17)

Return ONLY JSON: {{"palette": ["$0F", "$XX", "$XX", "$XX"], "reason": "brief"}}"""

    print(f"      [AI Palette] Using {model}...")
    response = _call_vision_api(img, prompt, model)

    if not response:
        return None

    import re
    json_match = re.search(r'\{[^}]+\}', response)
    if json_match:
        try:
            data = json.loads(json_match.group())
            if 'palette' in data:
                palette = []
                for color_str in data['palette']:
                    hex_val = color_str.replace('$', '').replace('0x', '')
                    palette.append(int(hex_val, 16))
                if len(palette) == num_colors:
                    print(f"      [AI Palette] Extracted: {', '.join(f'${c:02X}' for c in palette)}")
                    if 'reason' in data:
                        print(f"      [AI Palette] Reason: {data['reason']}")
                    return palette
        except (json.JSONDecodeError, ValueError) as e:
            print(f"      [AI Palette] Parse error: {e}")

    return None


# =============================================================================
# Convenience Functions for build_ai_assets.py
# =============================================================================

def process_sprite_with_consensus(
    img: Image.Image,
    sprite_type: str,
    target_size: int = 16,
    output_dir: Optional[Path] = None,
) -> Tuple[Optional[Image.Image], Optional[Tuple[int, int, int]]]:
    """
    Complete sprite extraction workflow using consensus and smart background detection.

    Args:
        img: Source sprite sheet image
        sprite_type: Description for AI ("player character", "enemy", etc.)
        target_size: Final sprite size
        output_dir: Directory to save debug images (optional)

    Returns:
        Tuple of (extracted_sprite, background_color) or (None, None) on failure
    """
    # 1. Detect background first
    bg_color = detect_background_smart(img, tolerance=20)
    if bg_color:
        print(f"      [SmartBg] Detected: RGB{bg_color}")
    else:
        print(f"      [SmartBg] No solid background detected")

    # 2. Detect sprite using consensus
    bbox = detect_sprite_consensus(img, sprite_type)

    if not bbox:
        print(f"      [Extract] No sprite detected, using fallback")
        # Fallback: use content mask
        mask = get_content_mask(img, tolerance=20)
        mask_arr = np.array(mask)

        # Find bounds of content
        rows = np.any(mask_arr > 0, axis=1)
        cols = np.any(mask_arr > 0, axis=0)

        if not np.any(rows) or not np.any(cols):
            return None, bg_color

        y_min, y_max = np.where(rows)[0][[0, -1]]
        x_min, x_max = np.where(cols)[0][[0, -1]]

        bbox = {
            'x': int(x_min),
            'y': int(y_min),
            'width': int(x_max - x_min + 1),
            'height': int(y_max - y_min + 1)
        }
        print(f"      [Extract] Fallback bounds: {bbox}")

    # 3. Extract region
    x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']

    # Ensure within image bounds
    img_w, img_h = img.size
    x = max(0, min(x, img_w - 1))
    y = max(0, min(y, img_h - 1))
    w = min(w, img_w - x)
    h = min(h, img_h - y)

    region = img.crop((x, y, x + w, y + h))

    # 4. Trim to content (remove background edges)
    if bg_color:
        region = _trim_to_content(region, bg_color, threshold=30)

    # 5. Scale to target size
    result = region.resize((target_size, target_size), Image.NEAREST)

    # 6. Save debug images if requested
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        region.save(output_dir / f"{sprite_type.replace(' ', '_')}_region.png")
        result.save(output_dir / f"{sprite_type.replace(' ', '_')}_{target_size}.png")

    return result, bg_color


def _trim_to_content(
    img: Image.Image,
    bg_color: Tuple[int, int, int],
    threshold: int = 30,
) -> Image.Image:
    """Trim background pixels from edges of image."""
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    pixels = np.array(img)
    h, w = pixels.shape[:2]

    bg_r, bg_g, bg_b = bg_color

    def is_background(r, g, b, a):
        if a < 128:
            return True
        dist = abs(int(r) - bg_r) + abs(int(g) - bg_g) + abs(int(b) - bg_b)
        return dist < threshold

    # Find content bounds
    min_x, min_y = w, h
    max_x, max_y = 0, 0

    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[y, x]
            if not is_background(r, g, b, a):
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)

    if min_x >= max_x or min_y >= max_y:
        return img  # No content found

    # Add small padding
    padding = 1
    min_x = max(0, min_x - padding)
    min_y = max(0, min_y - padding)
    max_x = min(w - 1, max_x + padding)
    max_y = min(h - 1, max_y + padding)

    return img.crop((min_x, min_y, max_x + 1, max_y + 1))


# =============================================================================
# Test / Debug
# =============================================================================

if __name__ == '__main__':
    print("Pipeline Bridge Module")
    print("=" * 50)
    print()
    print("Available functions:")
    print("  - detect_sprite_consensus(img, sprite_type)")
    print("  - detect_background_smart(img)")
    print("  - get_content_mask(img)")
    print("  - extract_palette_ai(img, num_colors)")
    print("  - get_best_model(task)")
    print("  - get_nearest_nes_color(rgb)")
    print("  - process_sprite_with_consensus(img, sprite_type, target_size)")
    print()
    print("Model map:")
    for task, model in MODEL_MAP.items():
        print(f"  {task}: {model}")
