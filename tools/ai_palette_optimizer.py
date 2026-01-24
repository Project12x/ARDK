#!/usr/bin/env python3
"""
AI Palette Optimizer for NES Development

Analyzes images and optimizes palettes for NES constraints:
1. Reduces colors to NES palette (54 colors)
2. Finds optimal 4-color palettes for sprites/backgrounds
3. Groups tiles by shared palette for efficient CHR banking
4. Suggests palette swaps for animations
5. Generates palette data for assembly

Uses Gemini AI for intelligent color grouping and suggestions.

Usage:
    python tools/ai_palette_optimizer.py sprite_sheet.png
    python tools/ai_palette_optimizer.py --batch gfx/ai_output/
"""

import os
import sys
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    from google import genai
    from google.genai import types
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

# Full NES palette (54 colors, NTSC)
# Format: (R, G, B)
NES_PALETTE = [
    # Row 0x
    (84, 84, 84),     # 0x00 - Dark gray
    (0, 30, 116),     # 0x01 - Dark blue
    (8, 16, 144),     # 0x02 - Blue
    (48, 0, 136),     # 0x03 - Purple
    (68, 0, 100),     # 0x04 - Dark magenta
    (92, 0, 48),      # 0x05 - Dark red
    (84, 4, 0),       # 0x06 - Brown
    (60, 24, 0),      # 0x07 - Orange-brown
    (32, 42, 0),      # 0x08 - Olive
    (8, 58, 0),       # 0x09 - Dark green
    (0, 64, 0),       # 0x0A - Green
    (0, 60, 0),       # 0x0B - Green
    (0, 50, 60),      # 0x0C - Teal
    (0, 0, 0),        # 0x0D - Black
    (0, 0, 0),        # 0x0E - Black (mirror)
    (0, 0, 0),        # 0x0F - Black (mirror)

    # Row 1x (medium brightness)
    (152, 150, 152),  # 0x10 - Gray
    (8, 76, 196),     # 0x11 - Blue
    (48, 50, 236),    # 0x12 - Blue
    (92, 30, 228),    # 0x13 - Blue-purple
    (136, 20, 176),   # 0x14 - Magenta
    (160, 20, 100),   # 0x15 - Pink-red
    (152, 34, 32),    # 0x16 - Red
    (120, 60, 0),     # 0x17 - Orange
    (84, 90, 0),      # 0x18 - Yellow-green
    (40, 114, 0),     # 0x19 - Green
    (8, 124, 0),      # 0x1A - Green
    (0, 118, 40),     # 0x1B - Green
    (0, 102, 120),    # 0x1C - Cyan
    (0, 0, 0),        # 0x1D - Black
    (0, 0, 0),        # 0x1E - Black
    (0, 0, 0),        # 0x1F - Black

    # Row 2x (bright)
    (236, 238, 236),  # 0x20 - White
    (76, 154, 236),   # 0x21 - Light blue
    (120, 124, 236),  # 0x22 - Blue
    (176, 98, 236),   # 0x23 - Purple
    (228, 84, 236),   # 0x24 - Magenta
    (236, 88, 180),   # 0x25 - Pink
    (236, 106, 100),  # 0x26 - Salmon
    (212, 136, 32),   # 0x27 - Orange
    (160, 170, 0),    # 0x28 - Yellow
    (116, 196, 0),    # 0x29 - Yellow-green
    (76, 208, 32),    # 0x2A - Green
    (56, 204, 108),   # 0x2B - Sea green
    (56, 180, 204),   # 0x2C - Cyan
    (60, 60, 60),     # 0x2D - Dark gray
    (0, 0, 0),        # 0x2E - Black
    (0, 0, 0),        # 0x2F - Black

    # Row 3x (light/pastel)
    (236, 238, 236),  # 0x30 - White
    (168, 204, 236),  # 0x31 - Light blue
    (188, 188, 236),  # 0x32 - Lavender
    (212, 178, 236),  # 0x33 - Light purple
    (236, 174, 236),  # 0x34 - Light magenta
    (236, 174, 212),  # 0x35 - Light pink
    (236, 180, 176),  # 0x36 - Peach
    (228, 196, 144),  # 0x37 - Tan
    (204, 210, 120),  # 0x38 - Light yellow
    (180, 222, 120),  # 0x39 - Light green
    (168, 226, 144),  # 0x3A - Mint
    (152, 226, 180),  # 0x3B - Light sea green
    (160, 214, 228),  # 0x3C - Light cyan
    (160, 162, 160),  # 0x3D - Light gray
    (0, 0, 0),        # 0x3E - Black
    (0, 0, 0),        # 0x3F - Black
]

# Common NES color names
NES_COLOR_NAMES = {
    0x0F: 'black',
    0x00: 'dark_gray',
    0x10: 'gray',
    0x20: 'white',
    0x30: 'white',
    0x16: 'red',
    0x26: 'light_red',
    0x27: 'orange',
    0x28: 'yellow',
    0x1A: 'green',
    0x2A: 'light_green',
    0x12: 'blue',
    0x22: 'light_blue',
    0x2C: 'cyan',
    0x24: 'magenta',
    0x14: 'purple',
}

@dataclass
class PaletteResult:
    """Result of palette optimization"""
    colors_rgb: List[Tuple[int, int, int]]  # 4 colors
    colors_nes: List[int]                    # NES palette indices
    coverage: float                          # % of pixels well-matched
    error: float                             # Average color error

@dataclass
class ImageAnalysis:
    """Complete image palette analysis"""
    filename: str
    width: int
    height: int
    unique_colors: int
    suggested_palettes: List[PaletteResult]
    ai_suggestions: List[str] = field(default_factory=list)


class AIPaletteOptimizer:
    """AI-powered palette optimizer for NES"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.client = None

        if HAS_GEMINI and self.api_key:
            self.client = genai.Client(api_key=self.api_key)

    def find_nearest_nes_color(self, rgb: Tuple[int, int, int]) -> Tuple[int, int]:
        """Find nearest NES palette color to given RGB"""

        r, g, b = rgb
        best_idx = 0x0F  # Default to black
        best_dist = float('inf')

        for idx, nes_rgb in enumerate(NES_PALETTE):
            # Skip duplicate blacks
            if idx in (0x0E, 0x1D, 0x1E, 0x1F, 0x2E, 0x2F, 0x3E, 0x3F):
                continue

            nr, ng, nb = nes_rgb
            # Weighted distance (human eye more sensitive to green)
            dist = (r - nr) ** 2 * 0.3 + (g - ng) ** 2 * 0.59 + (b - nb) ** 2 * 0.11

            if dist < best_dist:
                best_dist = dist
                best_idx = idx

        return best_idx, best_dist

    def analyze_image(self, image_path: str) -> ImageAnalysis:
        """Analyze image and suggest optimal palettes"""

        if not HAS_PIL:
            raise RuntimeError("PIL/Pillow required for image analysis")

        img = Image.open(image_path).convert('RGB')

        analysis = ImageAnalysis(
            filename=Path(image_path).name,
            width=img.width,
            height=img.height,
            unique_colors=0,
            suggested_palettes=[]
        )

        # Count colors
        pixels = list(img.getdata())
        color_counts = Counter(pixels)
        analysis.unique_colors = len(color_counts)

        # Find best 4-color palettes
        palettes = self._find_optimal_palettes(color_counts, num_palettes=4)
        analysis.suggested_palettes = palettes

        # AI suggestions
        if self.client:
            self._ai_analyze_palette(analysis, image_path, img)

        return analysis

    def _find_optimal_palettes(self, color_counts: Dict[Tuple, int],
                                num_palettes: int = 4) -> List[PaletteResult]:
        """Find optimal 4-color palettes using k-means-like clustering"""

        # Get all colors sorted by frequency
        sorted_colors = sorted(color_counts.items(), key=lambda x: -x[1])
        total_pixels = sum(color_counts.values())

        results = []

        # Strategy 1: Most common colors
        top_colors = [c[0] for c in sorted_colors[:16]]
        nes_colors = [(self.find_nearest_nes_color(c)[0], c) for c in top_colors]

        # Group by similar NES colors
        unique_nes = {}
        for nes_idx, rgb in nes_colors:
            if nes_idx not in unique_nes:
                unique_nes[nes_idx] = rgb

        # Create palette from most common unique NES colors
        if len(unique_nes) >= 3:
            palette_nes = list(unique_nes.keys())[:3]
            palette_nes.insert(0, 0x0F)  # Black for transparency

            palette_rgb = [NES_PALETTE[i] for i in palette_nes]

            # Calculate coverage
            matched = 0
            total_error = 0
            for color, count in color_counts.items():
                best_match = min(palette_rgb, key=lambda p: sum((a-b)**2 for a, b in zip(color, p)))
                error = sum((a-b)**2 for a, b in zip(color, best_match))
                total_error += error * count
                if error < 2000:  # Threshold for "good match"
                    matched += count

            result = PaletteResult(
                colors_rgb=palette_rgb,
                colors_nes=palette_nes,
                coverage=matched / total_pixels,
                error=total_error / total_pixels
            )
            results.append(result)

        # Strategy 2: Brightness-based grouping
        bright_colors = [(c, sum(c)/3) for c in color_counts.keys()]
        bright_colors.sort(key=lambda x: x[1])

        # Group into 4 brightness levels
        quarter = len(bright_colors) // 4
        if quarter > 0:
            representatives = [
                bright_colors[quarter // 2][0],        # Dark
                bright_colors[quarter + quarter // 2][0],  # Medium dark
                bright_colors[2 * quarter + quarter // 2][0],  # Medium light
                bright_colors[3 * quarter + quarter // 2][0],  # Light
            ]

            palette_nes = [self.find_nearest_nes_color(c)[0] for c in representatives]
            palette_nes[0] = 0x0F  # Force black for transparency

            palette_rgb = [NES_PALETTE[i] for i in palette_nes]

            matched = 0
            total_error = 0
            for color, count in color_counts.items():
                best_match = min(palette_rgb, key=lambda p: sum((a-b)**2 for a, b in zip(color, p)))
                error = sum((a-b)**2 for a, b in zip(color, best_match))
                total_error += error * count
                if error < 2000:
                    matched += count

            result = PaletteResult(
                colors_rgb=palette_rgb,
                colors_nes=palette_nes,
                coverage=matched / total_pixels,
                error=total_error / total_pixels
            )
            results.append(result)

        # Strategy 3: Hue-based (for colorful images)
        # ... additional strategies could be added

        # Sort by coverage
        results.sort(key=lambda x: -x.coverage)

        return results[:num_palettes]

    def _ai_analyze_palette(self, analysis: ImageAnalysis, image_path: str, img: Image.Image):
        """Use AI for palette suggestions"""

        # Resize for API
        max_size = 512
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        import io
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()

        prompt = """Analyze this sprite/image for NES palette optimization.

NES constraints:
- 4 colors per sprite palette (including transparent)
- 54 total colors available
- Sprites use 4 palettes (16 colors total, but grouped in 4s)

For this image, suggest:

1. **Primary Colors**: What 3 main colors (plus transparent) would best represent this image?
   Use NES color names: black, dark_gray, gray, white, red, orange, yellow, green, blue, cyan, magenta, purple, pink, brown

2. **Color Priority**: Which colors are most important to preserve?

3. **Palette Sharing**: If this is a sprite sheet with multiple sprites, could any sprites share palettes?

4. **Animation Potential**: Could palette cycling/swapping create animation effects?
   Example: Cycling blues for water shimmer, reds for fire flicker

5. **Optimization Tips**: Any specific advice for reducing this to 4 colors while preserving the look?

Return JSON:
{
    "suggested_palette": ["black", "color1", "color2", "color3"],
    "color_priority": ["most important", "second", "third"],
    "sharing_advice": "...",
    "animation_ideas": ["...", "..."],
    "tips": ["...", "..."]
}"""

        try:
            image_part = types.Part.from_bytes(data=image_bytes, mime_type='image/png')

            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[prompt, image_part]
            )

            text = response.text

            if '```json' in text:
                text = text.split('```json')[1].split('```')[0]
            elif '```' in text:
                text = text.split('```')[1].split('```')[0]

            data = json.loads(text.strip())

            if data.get('suggested_palette'):
                analysis.ai_suggestions.append(f"Suggested palette: {', '.join(data['suggested_palette'])}")

            if data.get('animation_ideas'):
                for idea in data['animation_ideas'][:2]:
                    analysis.ai_suggestions.append(f"Animation: {idea}")

            if data.get('tips'):
                for tip in data['tips'][:3]:
                    analysis.ai_suggestions.append(f"Tip: {tip}")

        except Exception as e:
            print(f"AI analysis failed: {e}")

    def convert_image(self, image_path: str, palette: PaletteResult,
                      output_path: str = None) -> Image.Image:
        """Convert image to use specified palette"""

        if not HAS_PIL:
            raise RuntimeError("PIL/Pillow required")

        img = Image.open(image_path).convert('RGB')

        # Create palette mapping
        def map_to_palette(rgb):
            best_idx = 0
            best_dist = float('inf')
            for idx, pal_rgb in enumerate(palette.colors_rgb):
                dist = sum((a - b) ** 2 for a, b in zip(rgb, pal_rgb))
                if dist < best_dist:
                    best_dist = dist
                    best_idx = idx
            return best_idx

        # Convert pixels
        pixels = list(img.getdata())
        new_pixels = []
        for rgb in pixels:
            idx = map_to_palette(rgb)
            new_pixels.append(palette.colors_rgb[idx])

        # Create new image
        new_img = Image.new('RGB', img.size)
        new_img.putdata(new_pixels)

        if output_path:
            new_img.save(output_path)

        return new_img

    def generate_assembly(self, palette: PaletteResult, name: str = "sprite") -> str:
        """Generate assembly palette data"""

        lines = [
            f"; Palette: {name}",
            f"; Coverage: {palette.coverage * 100:.1f}%",
            f"; Colors: {', '.join(f'${c:02X}' for c in palette.colors_nes)}",
            f"palette_{name}:",
            f"    .byte ${palette.colors_nes[0]:02X}, ${palette.colors_nes[1]:02X}, ${palette.colors_nes[2]:02X}, ${palette.colors_nes[3]:02X}",
        ]

        return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='AI Palette Optimizer for NES')
    parser.add_argument('input', nargs='?', help='Image file to analyze')
    parser.add_argument('--batch', action='store_true', help='Process directory')
    parser.add_argument('--convert', action='store_true', help='Convert image to palette')
    parser.add_argument('--output', '-o', help='Output file/directory')

    args = parser.parse_args()

    if not args.input:
        parser.print_help()
        return

    api_key = os.getenv('GEMINI_API_KEY')
    optimizer = AIPaletteOptimizer(api_key)

    if not api_key:
        print("Note: GEMINI_API_KEY not set. Using basic analysis only.")
        print()

    if args.batch or Path(args.input).is_dir():
        # Batch processing
        input_path = Path(args.input)
        for img_file in input_path.glob('*.png'):
            print(f"\nAnalyzing: {img_file.name}")
            try:
                analysis = optimizer.analyze_image(str(img_file))
                print(f"  Unique colors: {analysis.unique_colors}")
                if analysis.suggested_palettes:
                    best = analysis.suggested_palettes[0]
                    print(f"  Best palette: {', '.join(f'${c:02X}' for c in best.colors_nes)}")
                    print(f"  Coverage: {best.coverage * 100:.1f}%")
            except Exception as e:
                print(f"  Error: {e}")
    else:
        # Single file
        print(f"Analyzing: {args.input}")
        analysis = optimizer.analyze_image(args.input)

        print(f"\nImage: {analysis.filename}")
        print(f"Size: {analysis.width}x{analysis.height}")
        print(f"Unique colors: {analysis.unique_colors}")

        print("\nSuggested Palettes:")
        for i, palette in enumerate(analysis.suggested_palettes):
            nes_hex = ', '.join(f'${c:02X}' for c in palette.colors_nes)
            print(f"\n  Palette {i + 1}:")
            print(f"    NES colors: {nes_hex}")
            print(f"    Coverage: {palette.coverage * 100:.1f}%")
            print(f"    Error: {palette.error:.0f}")

        if analysis.ai_suggestions:
            print("\nAI Suggestions:")
            for suggestion in analysis.ai_suggestions:
                print(f"  * {suggestion}")

        # Convert if requested
        if args.convert and analysis.suggested_palettes:
            best_palette = analysis.suggested_palettes[0]
            output_path = args.output or args.input.replace('.png', '_nes.png')
            optimizer.convert_image(args.input, best_palette, output_path)
            print(f"\nConverted image saved to: {output_path}")

            # Generate assembly
            asm = optimizer.generate_assembly(best_palette, Path(args.input).stem)
            asm_path = args.output.replace('.png', '.inc') if args.output else args.input.replace('.png', '_palette.inc')
            with open(asm_path, 'w') as f:
                f.write(asm)
            print(f"Palette data saved to: {asm_path}")


if __name__ == '__main__':
    main()
