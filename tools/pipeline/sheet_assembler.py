"""
Sprite Sheet Assembly and Dissection Module.

This module provides:
1. SpriteSheetAssembler: Bin-packing algorithm for optimal sprite sheet creation
2. SheetDissector: AI-powered sprite boundary detection using vision models

Supports multiple AI providers for intelligent sprite detection:
- Pollinations.ai (free tier)
- Google Gemini
- Groq (Llama 4 vision)
- OpenAI GPT-4o
- Anthropic Claude
- xAI Grok
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any, Union
from pathlib import Path
from enum import Enum
import json
import math
import os

# Lazy imports for optional dependencies
PIL_Image = None


def _ensure_pil():
    """Lazy import PIL."""
    global PIL_Image
    if PIL_Image is None:
        from PIL import Image
        PIL_Image = Image
    return PIL_Image


# =============================================================================
# Data Structures
# =============================================================================

@dataclass
class FramePlacement:
    """A single frame's position within a sprite sheet."""
    name: str
    x: int
    y: int
    width: int
    height: int
    hotspot_x: int = 0
    hotspot_y: int = 0
    source_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON export."""
        return {
            'name': self.name,
            'x': self.x,
            'y': self.y,
            'w': self.width,
            'h': self.height,
            'hx': self.hotspot_x,
            'hy': self.hotspot_y,
            'source': self.source_path,
            **self.metadata
        }


@dataclass
class SheetLayout:
    """Complete layout of a sprite sheet."""
    width: int
    height: int
    frames: List[FramePlacement] = field(default_factory=list)
    padding: int = 0
    power_of_2: bool = True

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON export."""
        return {
            'width': self.width,
            'height': self.height,
            'padding': self.padding,
            'power_of_2': self.power_of_2,
            'frame_count': len(self.frames),
            'frames': [f.to_dict() for f in self.frames]
        }


@dataclass
class DetectedSprite:
    """A sprite detected by AI vision analysis."""
    x: int
    y: int
    width: int
    height: int
    label: Optional[str] = None
    confidence: float = 1.0
    animation_group: Optional[str] = None
    frame_index: Optional[int] = None

    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        """Return (left, top, right, bottom) for PIL cropping."""
        return (self.x, self.y, self.x + self.width, self.y + self.height)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'label': self.label,
            'confidence': self.confidence,
            'animation_group': self.animation_group,
            'frame_index': self.frame_index
        }


class PackingAlgorithm(Enum):
    """Available bin-packing algorithms."""
    SHELF = "shelf"              # Simple shelf algorithm (fast)
    SHELF_BEST_FIT = "shelf_bf"  # Shelf with best-fit heuristic
    MAXRECTS = "maxrects"        # MaxRects algorithm (better packing)
    ROW = "row"                  # Simple row-by-row (for uniform sizes)


# =============================================================================
# Sprite Sheet Assembler
# =============================================================================

class SpriteSheetAssembler:
    """
    Pack individual sprite frames into optimized sprite sheets.

    Features:
    - Multiple bin-packing algorithms
    - Power-of-2 dimensions (VRAM friendly)
    - Configurable padding
    - Hotspot/pivot point support
    - Metadata export (JSON and C header)

    Example:
        assembler = SpriteSheetAssembler(max_width=256, max_height=256)
        assembler.add_frame(idle_0, "idle_0", hotspot=(16, 32))
        assembler.add_frame(idle_1, "idle_1", hotspot=(16, 32))
        sheet, layout = assembler.assemble()
        assembler.export_metadata(layout, "output/sprites.json")
    """

    def __init__(
        self,
        max_width: int = 256,
        max_height: int = 256,
        padding: int = 0,
        power_of_2: bool = True,
        algorithm: PackingAlgorithm = PackingAlgorithm.SHELF_BEST_FIT,
        background_color: Tuple[int, int, int, int] = (0, 0, 0, 0),
    ):
        """
        Initialize the assembler.

        Args:
            max_width: Maximum sheet width
            max_height: Maximum sheet height
            padding: Pixels between frames (useful for filtering)
            power_of_2: Constrain dimensions to powers of 2
            algorithm: Packing algorithm to use
            background_color: RGBA background color (default transparent)
        """
        self.max_width = max_width
        self.max_height = max_height
        self.padding = padding
        self.power_of_2 = power_of_2
        self.algorithm = algorithm
        self.background_color = background_color

        # Frames to pack: (image, name, hotspot, metadata)
        self._frames: List[Tuple[Any, str, Tuple[int, int], Dict]] = []

    def add_frame(
        self,
        image: 'PIL_Image.Image',
        name: str,
        hotspot: Optional[Tuple[int, int]] = None,
        source_path: Optional[str] = None,
        **metadata
    ) -> None:
        """
        Add a frame to be packed.

        Args:
            image: PIL Image of the frame
            name: Unique name for this frame
            hotspot: (x, y) pivot point relative to frame
            source_path: Original file path (for metadata)
            **metadata: Additional metadata to store
        """
        if hotspot is None:
            # Default hotspot: bottom center
            hotspot = (image.width // 2, image.height)

        meta = {'source': source_path, **metadata}
        self._frames.append((image, name, hotspot, meta))

    def add_frames_from_directory(
        self,
        directory: Union[str, Path],
        pattern: str = "*.png",
        hotspot: Optional[Tuple[int, int]] = None,
    ) -> int:
        """
        Add all matching frames from a directory.

        Args:
            directory: Path to directory
            pattern: Glob pattern for files
            hotspot: Default hotspot for all frames

        Returns:
            Number of frames added
        """
        Image = _ensure_pil()
        directory = Path(directory)
        count = 0

        for filepath in sorted(directory.glob(pattern)):
            img = Image.open(filepath).convert('RGBA')
            self.add_frame(
                img,
                name=filepath.stem,
                hotspot=hotspot,
                source_path=str(filepath)
            )
            count += 1

        return count

    def clear(self) -> None:
        """Remove all pending frames."""
        self._frames.clear()

    def assemble(self) -> Tuple['PIL_Image.Image', SheetLayout]:
        """
        Pack all frames into an optimal sprite sheet.

        Returns:
            Tuple of (sheet_image, SheetLayout)
        """
        Image = _ensure_pil()

        if not self._frames:
            raise ValueError("No frames to assemble")

        # Choose packing algorithm
        if self.algorithm == PackingAlgorithm.ROW:
            layout = self._pack_row()
        elif self.algorithm == PackingAlgorithm.SHELF:
            layout = self._pack_shelf(best_fit=False)
        elif self.algorithm == PackingAlgorithm.SHELF_BEST_FIT:
            layout = self._pack_shelf(best_fit=True)
        elif self.algorithm == PackingAlgorithm.MAXRECTS:
            layout = self._pack_maxrects()
        else:
            layout = self._pack_shelf(best_fit=True)

        # Adjust to power of 2 if requested
        if self.power_of_2:
            layout.width = self._next_power_of_2(layout.width)
            layout.height = self._next_power_of_2(layout.height)

        # Create the sheet image
        sheet = Image.new('RGBA', (layout.width, layout.height), self.background_color)

        # Place each frame
        for i, placement in enumerate(layout.frames):
            img, _, _, _ = self._frames[i]
            sheet.paste(img, (placement.x, placement.y))

        return sheet, layout

    def _pack_row(self) -> SheetLayout:
        """Simple row-by-row packing (best for uniform sizes)."""
        placements = []
        x, y = self.padding, self.padding
        row_height = 0
        max_width_used = 0

        for img, name, hotspot, meta in self._frames:
            w, h = img.width, img.height

            # Check if we need a new row
            if x + w + self.padding > self.max_width:
                x = self.padding
                y += row_height + self.padding
                row_height = 0

            # Check if we exceeded height
            if y + h + self.padding > self.max_height:
                raise ValueError(
                    f"Frames don't fit in {self.max_width}x{self.max_height} sheet"
                )

            placements.append(FramePlacement(
                name=name,
                x=x, y=y,
                width=w, height=h,
                hotspot_x=hotspot[0], hotspot_y=hotspot[1],
                source_path=meta.get('source'),
                metadata={k: v for k, v in meta.items() if k != 'source'}
            ))

            x += w + self.padding
            row_height = max(row_height, h)
            max_width_used = max(max_width_used, x)

        return SheetLayout(
            width=max_width_used,
            height=y + row_height + self.padding,
            frames=placements,
            padding=self.padding,
            power_of_2=self.power_of_2
        )

    def _pack_shelf(self, best_fit: bool = True) -> SheetLayout:
        """
        Shelf bin-packing algorithm.

        Frames are sorted by height (tallest first) and placed on "shelves".
        With best_fit=True, tries to find the best shelf for each frame.
        """
        # Sort frames by height (descending) for better packing
        indexed_frames = list(enumerate(self._frames))
        indexed_frames.sort(key=lambda x: x[1][0].height, reverse=True)

        # Shelves: [(y_start, height, x_cursor)]
        shelves: List[List[int]] = []
        placements: List[Optional[FramePlacement]] = [None] * len(self._frames)

        for orig_idx, (img, name, hotspot, meta) in indexed_frames:
            w, h = img.width, img.height
            placed = False

            if best_fit:
                # Find best fitting shelf (smallest height that fits)
                best_shelf = None
                best_waste = float('inf')

                for shelf_idx, (sy, sh, sx) in enumerate(shelves):
                    # Check if frame fits
                    if h <= sh and sx + w + self.padding <= self.max_width:
                        waste = sh - h  # Height waste
                        if waste < best_waste:
                            best_waste = waste
                            best_shelf = shelf_idx

                if best_shelf is not None:
                    sy, sh, sx = shelves[best_shelf]
                    placements[orig_idx] = FramePlacement(
                        name=name,
                        x=sx, y=sy,
                        width=w, height=h,
                        hotspot_x=hotspot[0], hotspot_y=hotspot[1],
                        source_path=meta.get('source'),
                        metadata={k: v for k, v in meta.items() if k != 'source'}
                    )
                    shelves[best_shelf][2] = sx + w + self.padding
                    placed = True

            if not placed:
                # Try to fit on existing shelf (first fit)
                for shelf_idx, (sy, sh, sx) in enumerate(shelves):
                    if h <= sh and sx + w + self.padding <= self.max_width:
                        placements[orig_idx] = FramePlacement(
                            name=name,
                            x=sx, y=sy,
                            width=w, height=h,
                            hotspot_x=hotspot[0], hotspot_y=hotspot[1],
                            source_path=meta.get('source'),
                            metadata={k: v for k, v in meta.items() if k != 'source'}
                        )
                        shelves[shelf_idx][2] = sx + w + self.padding
                        placed = True
                        break

            if not placed:
                # Create new shelf
                if shelves:
                    new_y = shelves[-1][0] + shelves[-1][1] + self.padding
                else:
                    new_y = self.padding

                if new_y + h + self.padding > self.max_height:
                    raise ValueError(
                        f"Frames don't fit in {self.max_width}x{self.max_height} sheet"
                    )

                shelves.append([new_y, h, self.padding + w + self.padding])
                placements[orig_idx] = FramePlacement(
                    name=name,
                    x=self.padding, y=new_y,
                    width=w, height=h,
                    hotspot_x=hotspot[0], hotspot_y=hotspot[1],
                    source_path=meta.get('source'),
                    metadata={k: v for k, v in meta.items() if k != 'source'}
                )

        # Calculate final dimensions
        max_width = max(p.x + p.width for p in placements) + self.padding
        max_height = max(p.y + p.height for p in placements) + self.padding

        return SheetLayout(
            width=max_width,
            height=max_height,
            frames=placements,
            padding=self.padding,
            power_of_2=self.power_of_2
        )

    def _pack_maxrects(self) -> SheetLayout:
        """
        MaxRects bin-packing algorithm.

        More complex but achieves better packing density.
        Uses the "Best Short Side Fit" heuristic.
        """
        # Sort by area (largest first)
        indexed_frames = list(enumerate(self._frames))
        indexed_frames.sort(key=lambda x: x[1][0].width * x[1][0].height, reverse=True)

        # Free rectangles (initially the whole sheet)
        free_rects = [(self.padding, self.padding,
                       self.max_width - self.padding,
                       self.max_height - self.padding)]

        placements: List[Optional[FramePlacement]] = [None] * len(self._frames)

        for orig_idx, (img, name, hotspot, meta) in indexed_frames:
            w, h = img.width + self.padding, img.height + self.padding

            # Find best rectangle (Best Short Side Fit)
            best_rect = None
            best_short_side = float('inf')
            best_idx = -1

            for rect_idx, (rx, ry, rw, rh) in enumerate(free_rects):
                if w <= rw and h <= rh:
                    short_side = min(rw - w, rh - h)
                    if short_side < best_short_side:
                        best_short_side = short_side
                        best_rect = (rx, ry, rw, rh)
                        best_idx = rect_idx

            if best_rect is None:
                raise ValueError(
                    f"Frame '{name}' ({img.width}x{img.height}) doesn't fit"
                )

            rx, ry, rw, rh = best_rect

            # Place the frame
            placements[orig_idx] = FramePlacement(
                name=name,
                x=rx, y=ry,
                width=img.width, height=img.height,
                hotspot_x=hotspot[0], hotspot_y=hotspot[1],
                source_path=meta.get('source'),
                metadata={k: v for k, v in meta.items() if k != 'source'}
            )

            # Split the rectangle
            del free_rects[best_idx]

            # Right remainder
            if rw - w > 0:
                free_rects.append((rx + w, ry, rw - w, rh))

            # Bottom remainder
            if rh - h > 0:
                free_rects.append((rx, ry + h, w, rh - h))

            # Merge overlapping free rectangles (simplified)
            free_rects = self._merge_rects(free_rects)

        # Calculate final dimensions
        max_width = max(p.x + p.width for p in placements) + self.padding
        max_height = max(p.y + p.height for p in placements) + self.padding

        return SheetLayout(
            width=max_width,
            height=max_height,
            frames=placements,
            padding=self.padding,
            power_of_2=self.power_of_2
        )

    def _merge_rects(self, rects: List[Tuple]) -> List[Tuple]:
        """Remove fully contained rectangles."""
        result = []
        for i, r1 in enumerate(rects):
            contained = False
            for j, r2 in enumerate(rects):
                if i != j:
                    # Check if r1 is contained in r2
                    if (r1[0] >= r2[0] and r1[1] >= r2[1] and
                        r1[0] + r1[2] <= r2[0] + r2[2] and
                        r1[1] + r1[3] <= r2[1] + r2[3]):
                        contained = True
                        break
            if not contained:
                result.append(r1)
        return result

    @staticmethod
    def _next_power_of_2(n: int) -> int:
        """Return the next power of 2 >= n."""
        if n <= 0:
            return 1
        return 1 << (n - 1).bit_length()

    def export_metadata(
        self,
        layout: SheetLayout,
        output_path: str,
        format: str = "json"
    ) -> None:
        """
        Export frame metadata.

        Args:
            layout: SheetLayout from assemble()
            output_path: Output file path
            format: "json" or "c_header"
        """
        output_path = Path(output_path)

        if format == "json":
            with open(output_path, 'w') as f:
                json.dump(layout.to_dict(), f, indent=2)

        elif format == "c_header":
            self._export_c_header(layout, output_path)

        else:
            raise ValueError(f"Unknown format: {format}")

    def _export_c_header(self, layout: SheetLayout, output_path: Path) -> None:
        """Generate C header with frame data."""
        name = output_path.stem.upper()

        lines = [
            f"// Auto-generated sprite sheet metadata",
            f"// Sheet size: {layout.width}x{layout.height}",
            f"// Frame count: {len(layout.frames)}",
            f"",
            f"#ifndef _{name}_SHEET_H_",
            f"#define _{name}_SHEET_H_",
            f"",
            f"#include <genesis.h>",
            f"",
            f"#define {name}_SHEET_WIDTH {layout.width}",
            f"#define {name}_SHEET_HEIGHT {layout.height}",
            f"#define {name}_FRAME_COUNT {len(layout.frames)}",
            f"",
            f"typedef struct {{",
            f"    u16 x, y;           // Position in sheet",
            f"    u8 w, h;            // Frame dimensions",
            f"    s8 hx, hy;          // Hotspot offset",
            f"}} FrameInfo;",
            f"",
            f"const FrameInfo {name.lower()}_frames[{name}_FRAME_COUNT] = {{",
        ]

        for frame in layout.frames:
            lines.append(
                f"    {{ {frame.x}, {frame.y}, {frame.width}, {frame.height}, "
                f"{frame.hotspot_x}, {frame.hotspot_y} }},  // {frame.name}"
            )

        lines.extend([
            f"}};",
            f"",
            f"#endif // _{name}_SHEET_H_",
            f""
        ])

        with open(output_path, 'w') as f:
            f.write('\n'.join(lines))


# =============================================================================
# AI-Powered Sheet Dissector
# =============================================================================

class AIProvider(Enum):
    """Supported AI providers for vision analysis."""
    POLLINATIONS = "pollinations"
    GEMINI = "gemini"
    GROQ = "groq"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    XAI = "xai"


class SheetDissector:
    """
    AI-powered sprite sheet dissector.

    Uses vision AI models to intelligently detect sprite boundaries,
    identify animation groups, and extract frames with semantic labels.

    Supports multiple AI providers:
    - Pollinations.ai (free tier, default)
    - Google Gemini
    - Groq (Llama 4 vision)
    - OpenAI GPT-4o
    - Anthropic Claude
    - xAI Grok

    Example:
        dissector = SheetDissector(provider=AIProvider.GEMINI)
        sprites = dissector.analyze(sheet_image)
        frames = dissector.extract_frames(sheet_image, sprites)
    """

    # API endpoints
    ENDPOINTS = {
        AIProvider.POLLINATIONS: "https://text.pollinations.ai/",
        AIProvider.GEMINI: "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
        AIProvider.GROQ: "https://api.groq.com/openai/v1/chat/completions",
        AIProvider.OPENAI: "https://api.openai.com/v1/chat/completions",
        AIProvider.ANTHROPIC: "https://api.anthropic.com/v1/messages",
        AIProvider.XAI: "https://api.x.ai/v1/chat/completions",
    }

    # Environment variable names for API keys
    API_KEY_VARS = {
        AIProvider.POLLINATIONS: "POLLINATIONS_API_KEY",
        AIProvider.GEMINI: "GEMINI_API_KEY",
        AIProvider.GROQ: "GROQ_API_KEY",
        AIProvider.OPENAI: "OPENAI_API_KEY",
        AIProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
        AIProvider.XAI: "XAI_API_KEY",
    }

    def __init__(
        self,
        provider: AIProvider = AIProvider.POLLINATIONS,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        fallback_providers: Optional[List[AIProvider]] = None,
    ):
        """
        Initialize the dissector.

        Args:
            provider: Primary AI provider to use
            api_key: API key (or reads from environment)
            model: Specific model to use (provider-dependent)
            fallback_providers: List of fallback providers if primary fails
        """
        self.provider = provider
        self.api_key = api_key or os.environ.get(self.API_KEY_VARS.get(provider, ""))
        self.model = model
        self.fallback_providers = fallback_providers or []

        # Default models per provider
        self._default_models = {
            AIProvider.POLLINATIONS: "openai",  # Uses OpenAI via Pollinations
            AIProvider.GEMINI: "gemini-2.5-flash",
            AIProvider.GROQ: "meta-llama/llama-4-scout-17b-16e-instruct",  # Llama 4 vision
            AIProvider.OPENAI: "gpt-4o-mini",
            AIProvider.ANTHROPIC: "claude-3-5-haiku-20241022",
            AIProvider.XAI: "grok-2-vision-1212",
        }

    def analyze(
        self,
        sheet_image: 'PIL_Image.Image',
        context: Optional[str] = None,
        expected_frame_size: Optional[Tuple[int, int]] = None,
    ) -> List[DetectedSprite]:
        """
        Analyze a sprite sheet to detect individual sprites.

        Uses AI vision to identify:
        - Sprite boundaries
        - Animation groups (idle, walk, attack, etc.)
        - Frame ordering
        - Semantic labels

        Args:
            sheet_image: PIL Image of the sprite sheet
            context: Optional context (e.g., "16-bit RPG character")
            expected_frame_size: Hint for expected frame dimensions

        Returns:
            List of DetectedSprite objects
        """
        import base64
        from io import BytesIO

        Image = _ensure_pil()

        # Convert image to base64
        buffer = BytesIO()
        sheet_image.save(buffer, format='PNG')
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        # Build the prompt
        prompt = self._build_analysis_prompt(
            sheet_image.width,
            sheet_image.height,
            context,
            expected_frame_size
        )

        # Try primary provider, then fallbacks
        providers_to_try = [self.provider] + self.fallback_providers
        last_error = None

        for provider in providers_to_try:
            try:
                response = self._call_vision_api(provider, image_base64, prompt)
                sprites = self._parse_response(response)
                return sprites
            except Exception as e:
                last_error = e
                continue

        raise RuntimeError(f"All AI providers failed. Last error: {last_error}")

    def _build_analysis_prompt(
        self,
        width: int,
        height: int,
        context: Optional[str],
        expected_size: Optional[Tuple[int, int]],
    ) -> str:
        """Build the vision analysis prompt."""
        prompt = f"""Analyze this sprite sheet image ({width}x{height} pixels).

Your task is to identify all individual sprite frames and their boundaries.

"""
        if context:
            prompt += f"Context: {context}\n\n"

        if expected_size:
            prompt += f"Expected frame size hint: approximately {expected_size[0]}x{expected_size[1]} pixels\n\n"

        prompt += """For each sprite frame, provide:
1. Bounding box: x, y, width, height (in pixels)
2. Label: descriptive name (e.g., "idle_0", "walk_1", "attack_2")
3. Animation group: the action category (e.g., "idle", "walk", "run", "attack", "hurt", "die")
4. Frame index: the frame number within its animation group (0, 1, 2, etc.)
5. Confidence: how confident you are (0.0 to 1.0)

Important:
- Detect the ACTUAL sprite boundaries, not a fixed grid
- Sprites may have different sizes
- Look for transparent/empty space between sprites
- Group related frames into animation sequences
- Order frames left-to-right, top-to-bottom by default

Return JSON array:
[
    {
        "x": 0,
        "y": 0,
        "width": 32,
        "height": 32,
        "label": "idle_0",
        "animation_group": "idle",
        "frame_index": 0,
        "confidence": 0.95
    },
    ...
]

Return ONLY the JSON array, no other text."""

        return prompt

    def _call_vision_api(
        self,
        provider: AIProvider,
        image_base64: str,
        prompt: str
    ) -> str:
        """Call the vision API for the specified provider."""
        import urllib.request
        import urllib.error

        api_key = self.api_key
        if provider != self.provider:
            # Get API key for fallback provider
            api_key = os.environ.get(self.API_KEY_VARS.get(provider, ""))

        model = self.model or self._default_models.get(provider)

        if provider == AIProvider.POLLINATIONS:
            return self._call_pollinations(image_base64, prompt, model)
        elif provider == AIProvider.GEMINI:
            return self._call_gemini(image_base64, prompt, model, api_key)
        elif provider == AIProvider.GROQ:
            return self._call_openai_compatible(
                self.ENDPOINTS[AIProvider.GROQ],
                image_base64, prompt, model, api_key
            )
        elif provider == AIProvider.OPENAI:
            return self._call_openai_compatible(
                self.ENDPOINTS[AIProvider.OPENAI],
                image_base64, prompt, model, api_key
            )
        elif provider == AIProvider.ANTHROPIC:
            return self._call_anthropic(image_base64, prompt, model, api_key)
        elif provider == AIProvider.XAI:
            return self._call_openai_compatible(
                self.ENDPOINTS[AIProvider.XAI],
                image_base64, prompt, model, api_key
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def _call_pollinations(
        self,
        image_base64: str,
        prompt: str,
        model: str
    ) -> str:
        """Call Pollinations.ai API using OpenAI-compatible endpoint."""
        import urllib.request

        # Use OpenAI-compatible endpoint for vision
        url = "https://text.pollinations.ai/openai"

        payload = {
            "model": model or "openai",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        }
                    }
                ]
            }],
            "max_tokens": 4096
        }

        data = json.dumps(payload).encode('utf-8')
        headers = {
            'Content-Type': 'application/json',
        }

        # Add API key if available
        api_key = self.api_key or os.environ.get("POLLINATIONS_API_KEY", "")
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'

        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result['choices'][0]['message']['content']

    def _call_gemini(
        self,
        image_base64: str,
        prompt: str,
        model: str,
        api_key: str
    ) -> str:
        """Call Google Gemini API."""
        import urllib.request

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": image_base64
                        }
                    }
                ]
            }]
        }

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=data,
            headers={'Content-Type': 'application/json'}
        )

        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result['candidates'][0]['content']['parts'][0]['text']

    def _call_openai_compatible(
        self,
        endpoint: str,
        image_base64: str,
        prompt: str,
        model: str,
        api_key: str
    ) -> str:
        """Call OpenAI-compatible API (OpenAI, Groq, xAI)."""
        import urllib.request

        payload = {
            "model": model,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        }
                    }
                ]
            }],
            "max_tokens": 4096
        }

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            endpoint,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'Accept': 'application/json',
            }
        )

        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result['choices'][0]['message']['content']

    def _call_anthropic(
        self,
        image_base64: str,
        prompt: str,
        model: str,
        api_key: str
    ) -> str:
        """Call Anthropic Claude API."""
        import urllib.request

        payload = {
            "model": model,
            "max_tokens": 4096,
            "messages": [{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_base64
                        }
                    },
                    {"type": "text", "text": prompt}
                ]
            }]
        }

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            self.ENDPOINTS[AIProvider.ANTHROPIC],
            data=data,
            headers={
                'Content-Type': 'application/json',
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01'
            }
        )

        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result['content'][0]['text']

    def _parse_response(self, response: str) -> List[DetectedSprite]:
        """Parse AI response into DetectedSprite objects."""
        # Try to extract JSON from response
        response = response.strip()

        # Handle markdown code blocks
        if response.startswith('```'):
            lines = response.split('\n')
            # Remove first and last lines (```json and ```)
            json_lines = []
            in_block = False
            for line in lines:
                if line.startswith('```'):
                    in_block = not in_block
                    continue
                if in_block:
                    json_lines.append(line)
            response = '\n'.join(json_lines)

        # Parse JSON
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON array in response
            import re
            match = re.search(r'\[[\s\S]*\]', response)
            if match:
                data = json.loads(match.group())
            else:
                raise ValueError(f"Could not parse AI response as JSON: {response[:200]}...")

        # Convert to DetectedSprite objects
        sprites = []
        for item in data:
            sprites.append(DetectedSprite(
                x=int(item.get('x', 0)),
                y=int(item.get('y', 0)),
                width=int(item.get('width', 0)),
                height=int(item.get('height', 0)),
                label=item.get('label'),
                confidence=float(item.get('confidence', 1.0)),
                animation_group=item.get('animation_group'),
                frame_index=item.get('frame_index')
            ))

        return sprites

    def extract_frames(
        self,
        sheet_image: 'PIL_Image.Image',
        sprites: List[DetectedSprite],
        padding: int = 0,
    ) -> List[Tuple['PIL_Image.Image', DetectedSprite]]:
        """
        Extract individual frames from the sheet.

        Args:
            sheet_image: The original sprite sheet
            sprites: List of detected sprites from analyze()
            padding: Extra pixels to include around each sprite

        Returns:
            List of (frame_image, sprite_info) tuples
        """
        Image = _ensure_pil()

        frames = []
        for sprite in sprites:
            # Calculate crop box with padding
            left = max(0, sprite.x - padding)
            top = max(0, sprite.y - padding)
            right = min(sheet_image.width, sprite.x + sprite.width + padding)
            bottom = min(sheet_image.height, sprite.y + sprite.height + padding)

            frame = sheet_image.crop((left, top, right, bottom))
            frames.append((frame, sprite))

        return frames

    def dissect_to_directory(
        self,
        sheet_image: 'PIL_Image.Image',
        output_dir: Union[str, Path],
        context: Optional[str] = None,
        expected_frame_size: Optional[Tuple[int, int]] = None,
    ) -> Dict[str, Any]:
        """
        Complete dissection: analyze and save frames to directory.

        Args:
            sheet_image: The sprite sheet image
            output_dir: Directory to save extracted frames
            context: Optional context hint
            expected_frame_size: Expected frame dimensions hint

        Returns:
            Dictionary with extraction results and metadata
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Analyze the sheet
        sprites = self.analyze(sheet_image, context, expected_frame_size)

        # Extract frames
        frames = self.extract_frames(sheet_image, sprites)

        # Save frames
        saved_files = []
        animations = {}

        for frame_img, sprite in frames:
            # Generate filename
            if sprite.label:
                filename = f"{sprite.label}.png"
            else:
                filename = f"frame_{sprite.x}_{sprite.y}.png"

            filepath = output_dir / filename
            frame_img.save(filepath)
            saved_files.append(str(filepath))

            # Group by animation
            group = sprite.animation_group or "unknown"
            if group not in animations:
                animations[group] = []
            animations[group].append(sprite.to_dict())

        # Save metadata
        metadata = {
            'source_dimensions': {
                'width': sheet_image.width,
                'height': sheet_image.height
            },
            'frame_count': len(sprites),
            'animations': animations,
            'frames': [s.to_dict() for s in sprites]
        }

        metadata_path = output_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        return {
            'frames': saved_files,
            'metadata_path': str(metadata_path),
            'animations': animations,
            'sprite_count': len(sprites)
        }


# =============================================================================
# Grid-Based Fallback Dissector
# =============================================================================

class GridDissector:
    """
    Simple grid-based sprite sheet dissector.

    Use this when:
    - Sprites are arranged in a uniform grid
    - No AI API is available
    - Fast processing is needed
    """

    def __init__(
        self,
        frame_width: int,
        frame_height: int,
        padding: int = 0,
        margin: int = 0,
    ):
        """
        Initialize grid dissector.

        Args:
            frame_width: Width of each frame
            frame_height: Height of each frame
            padding: Space between frames
            margin: Space around sheet edges
        """
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.padding = padding
        self.margin = margin

    def dissect(
        self,
        sheet_image: 'PIL_Image.Image',
        trim_empty: bool = True,
        alpha_threshold: int = 10,
    ) -> List[Tuple['PIL_Image.Image', DetectedSprite]]:
        """
        Extract frames from a grid-based sprite sheet.

        Args:
            sheet_image: The sprite sheet
            trim_empty: Skip completely transparent frames
            alpha_threshold: Max alpha sum to consider "empty"

        Returns:
            List of (frame_image, DetectedSprite) tuples
        """
        Image = _ensure_pil()

        frames = []
        y = self.margin
        row = 0

        while y + self.frame_height <= sheet_image.height - self.margin:
            x = self.margin
            col = 0

            while x + self.frame_width <= sheet_image.width - self.margin:
                # Crop frame
                frame = sheet_image.crop((
                    x, y,
                    x + self.frame_width,
                    y + self.frame_height
                ))

                # Check if empty
                is_empty = False
                if trim_empty:
                    if frame.mode == 'RGBA':
                        alpha = frame.split()[3]
                        if sum(alpha.getdata()) < alpha_threshold:
                            is_empty = True

                if not is_empty:
                    sprite = DetectedSprite(
                        x=x, y=y,
                        width=self.frame_width,
                        height=self.frame_height,
                        label=f"frame_{row}_{col}",
                        frame_index=len(frames)
                    )
                    frames.append((frame, sprite))

                x += self.frame_width + self.padding
                col += 1

            y += self.frame_height + self.padding
            row += 1

        return frames


# =============================================================================
# Convenience Functions
# =============================================================================

def assemble_sheet(
    frames: List['PIL_Image.Image'],
    names: Optional[List[str]] = None,
    output_path: Optional[str] = None,
    max_width: int = 256,
    max_height: int = 256,
    padding: int = 0,
    power_of_2: bool = True,
) -> Tuple['PIL_Image.Image', SheetLayout]:
    """
    Convenience function to assemble frames into a sprite sheet.

    Args:
        frames: List of PIL Images
        names: Optional list of frame names
        output_path: Optional path to save sheet
        max_width: Maximum sheet width
        max_height: Maximum sheet height
        padding: Pixels between frames
        power_of_2: Use power-of-2 dimensions

    Returns:
        Tuple of (sheet_image, SheetLayout)
    """
    assembler = SpriteSheetAssembler(
        max_width=max_width,
        max_height=max_height,
        padding=padding,
        power_of_2=power_of_2
    )

    for i, frame in enumerate(frames):
        name = names[i] if names else f"frame_{i}"
        assembler.add_frame(frame, name)

    sheet, layout = assembler.assemble()

    if output_path:
        sheet.save(output_path)
        # Also save metadata
        meta_path = Path(output_path).with_suffix('.json')
        assembler.export_metadata(layout, str(meta_path))

    return sheet, layout


def dissect_sheet(
    sheet_image: 'PIL_Image.Image',
    output_dir: Optional[str] = None,
    use_ai: bool = True,
    provider: AIProvider = AIProvider.POLLINATIONS,
    frame_width: Optional[int] = None,
    frame_height: Optional[int] = None,
    context: Optional[str] = None,
) -> List[Tuple['PIL_Image.Image', DetectedSprite]]:
    """
    Convenience function to dissect a sprite sheet.

    Args:
        sheet_image: The sprite sheet image
        output_dir: Optional directory to save frames
        use_ai: Use AI-powered detection (True) or grid-based (False)
        provider: AI provider to use
        frame_width: Frame width (required if use_ai=False)
        frame_height: Frame height (required if use_ai=False)
        context: Context hint for AI analysis

    Returns:
        List of (frame_image, DetectedSprite) tuples
    """
    if use_ai:
        dissector = SheetDissector(provider=provider)
        sprites = dissector.analyze(
            sheet_image,
            context=context,
            expected_frame_size=(frame_width, frame_height) if frame_width else None
        )
        frames = dissector.extract_frames(sheet_image, sprites)
    else:
        if not frame_width or not frame_height:
            raise ValueError("frame_width and frame_height required for grid dissection")
        dissector = GridDissector(frame_width, frame_height)
        frames = dissector.dissect(sheet_image)

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        for frame_img, sprite in frames:
            filename = f"{sprite.label or f'frame_{sprite.x}_{sprite.y}'}.png"
            frame_img.save(output_dir / filename)

    return frames
