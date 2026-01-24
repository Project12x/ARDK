"""
Provider-Agnostic Style Consistency System.

Design Principles:
1. StyleProfile is provider-agnostic (portable JSON)
2. StyleAdapters translate to provider-specific params
3. Automatic adapter selection based on active provider
4. Graceful degradation when style features unsupported

Usage:
    from pipeline.style import StyleManager, StyleProfile

    manager = StyleManager()

    # Capture style from reference
    style = manager.capture_style(reference_img, "my_style")
    manager.save_style(style, include_reference=True)

    # Apply style to generation
    params = manager.apply_style(style, "pixellab", {"prompt": "warrior sprite"})
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from PIL import Image, ImageFilter
import json
from enum import Enum
from colorsys import rgb_to_hsv
from collections import Counter


class OutlineStyle(str, Enum):
    """Outline style options (provider-agnostic)."""
    BLACK = "black"           # Single-color black outline
    COLORED = "colored"       # Outline matches nearby colors
    SELECTIVE = "selective"   # Outline only on high-contrast edges
    NONE = "none"             # No outline (lineless)


class ShadingLevel(str, Enum):
    """Shading complexity (provider-agnostic)."""
    FLAT = "flat"             # No shading, solid colors
    SIMPLE = "simple"         # 2-3 shading levels
    MODERATE = "moderate"     # Standard pixel art shading
    DETAILED = "detailed"     # Rich shading gradients


class DetailLevel(str, Enum):
    """Overall detail level (provider-agnostic)."""
    LOW = "low"               # Chunky, minimal detail (8-bit style)
    MEDIUM = "medium"         # Standard detail
    HIGH = "high"             # Fine detail (16-bit style)


@dataclass
class StyleProfile:
    """
    Provider-agnostic style definition.

    Stores style characteristics that can be translated to any AI provider's
    specific parameters via StyleAdapters.
    """
    name: str

    # Color palette (up to 16 for retro platforms)
    palette: List[Tuple[int, int, int]] = field(default_factory=list)

    # Visual style parameters
    outline_style: OutlineStyle = OutlineStyle.BLACK
    shading_level: ShadingLevel = ShadingLevel.MODERATE
    detail_level: DetailLevel = DetailLevel.MEDIUM

    # Reference image (for visual style matching)
    reference_image_path: Optional[str] = None
    _reference_image: Optional[Image.Image] = field(default=None, repr=False)

    # Measured characteristics (auto-extracted)
    contrast: float = 0.7
    saturation: float = 0.6
    dither_pattern: str = "none"  # "none", "bayer", "floyd"

    # Platform hint (affects style translation)
    target_platform: str = "genesis"

    # Provider-specific overrides (escape hatch)
    provider_overrides: Dict[str, Dict] = field(default_factory=dict)

    @property
    def reference_image(self) -> Optional[Image.Image]:
        """Lazy-load reference image from path."""
        if self._reference_image is None and self.reference_image_path:
            path = Path(self.reference_image_path)
            if path.exists():
                self._reference_image = Image.open(path)
        return self._reference_image

    @reference_image.setter
    def reference_image(self, img: Image.Image):
        self._reference_image = img

    def to_dict(self) -> Dict:
        """Serialize to JSON-compatible dict (excludes image data)."""
        return {
            'name': self.name,
            'palette': [list(c) for c in self.palette],
            'outline_style': self.outline_style.value,
            'shading_level': self.shading_level.value,
            'detail_level': self.detail_level.value,
            'reference_image_path': self.reference_image_path,
            'contrast': self.contrast,
            'saturation': self.saturation,
            'dither_pattern': self.dither_pattern,
            'target_platform': self.target_platform,
            'provider_overrides': self.provider_overrides,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'StyleProfile':
        """Deserialize from dict."""
        return cls(
            name=data['name'],
            palette=[tuple(c) for c in data.get('palette', [])],
            outline_style=OutlineStyle(data.get('outline_style', 'black')),
            shading_level=ShadingLevel(data.get('shading_level', 'moderate')),
            detail_level=DetailLevel(data.get('detail_level', 'medium')),
            reference_image_path=data.get('reference_image_path'),
            contrast=data.get('contrast', 0.7),
            saturation=data.get('saturation', 0.6),
            dither_pattern=data.get('dither_pattern', 'none'),
            target_platform=data.get('target_platform', 'genesis'),
            provider_overrides=data.get('provider_overrides', {}),
        )

    def save(self, path: str) -> None:
        """Save style profile to JSON file."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str) -> 'StyleProfile':
        """Load style profile from JSON file."""
        with open(path) as f:
            data = json.load(f)
        return cls.from_dict(data)


# =============================================================================
# STYLE ADAPTERS (Provider-Specific Translation)
# =============================================================================

class StyleAdapter(ABC):
    """Abstract base for provider-specific style adapters."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the AI provider this adapter supports."""
        pass

    @abstractmethod
    def apply_style(self, style: StyleProfile, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply style to generation parameters.

        Args:
            style: StyleProfile to apply
            params: Existing generation parameters

        Returns:
            Updated parameters with style applied
        """
        pass

    def supports_feature(self, feature: str) -> bool:
        """Check if this provider supports a style feature."""
        supported = self.get_supported_features()
        return feature in supported

    @abstractmethod
    def get_supported_features(self) -> List[str]:
        """List features this provider supports."""
        pass


class PixelLabAdapter(StyleAdapter):
    """
    Style adapter for PixelLab API (v1 and v2).

    PixelLab supports:
    - style_image: Reference image for visual style
    - style_options: Fine-grained control (v2)
    - color_image: Palette enforcement
    - outline, shading, detail: Style enums
    """

    @property
    def provider_name(self) -> str:
        return "pixellab"

    def get_supported_features(self) -> List[str]:
        return [
            'reference_image', 'palette', 'outline', 'shading',
            'detail', 'color_image', 'style_options'
        ]

    def apply_style(self, style: StyleProfile, params: Dict[str, Any]) -> Dict[str, Any]:
        params = params.copy()

        # Check for provider-specific overrides
        if 'pixellab' in style.provider_overrides:
            params.update(style.provider_overrides['pixellab'])
            return params

        # Reference image → style_image
        if style.reference_image:
            params['style_image'] = style.reference_image

        # Palette → color_image (create palette swatch)
        if style.palette:
            params['color_image'] = self._create_palette_image(style.palette)

        # Outline style mapping
        outline_map = {
            OutlineStyle.BLACK: "single color black outline",
            OutlineStyle.COLORED: "single color outline",
            OutlineStyle.SELECTIVE: "selective outline",
            OutlineStyle.NONE: "lineless",
        }
        params['outline'] = outline_map.get(style.outline_style, "single color black outline")

        # Shading level mapping
        shading_map = {
            ShadingLevel.FLAT: "flat shading",
            ShadingLevel.SIMPLE: "basic shading",
            ShadingLevel.MODERATE: "medium shading",
            ShadingLevel.DETAILED: "detailed shading",
        }
        params['shading'] = shading_map.get(style.shading_level, "medium shading")

        # Detail level mapping
        detail_map = {
            DetailLevel.LOW: "low detail",
            DetailLevel.MEDIUM: "medium detail",
            DetailLevel.HIGH: "highly detailed",
        }
        params['detail'] = detail_map.get(style.detail_level, "medium detail")

        # v2 style_options (if using v2 with style_image)
        if style.reference_image and params.get('api_version') == 2:
            params['style_options'] = {
                'color_palette': bool(style.palette),
                'outline': style.outline_style != OutlineStyle.NONE,
                'detail': style.detail_level != DetailLevel.LOW,
                'shading': style.shading_level != ShadingLevel.FLAT,
            }

        return params

    def _create_palette_image(self, palette: List[Tuple[int, int, int]]) -> Image.Image:
        """Create a 16x1 palette swatch image for color_image param."""
        swatch = Image.new('RGB', (16, 1))
        for i, color in enumerate(palette[:16]):
            swatch.putpixel((i, 0), color)
        return swatch


class PollinationsAdapter(StyleAdapter):
    """
    Style adapter for Pollinations.ai.

    Pollinations supports:
    - Prompt-based style (keywords in text)
    - img2img with gptimage model
    - Flux for clean pixel art generation
    """

    @property
    def provider_name(self) -> str:
        return "pollinations"

    def get_supported_features(self) -> List[str]:
        return ['prompt_style', 'reference_image_img2img', 'palette_prompt']

    def apply_style(self, style: StyleProfile, params: Dict[str, Any]) -> Dict[str, Any]:
        params = params.copy()

        # Check for provider-specific overrides
        if 'pollinations' in style.provider_overrides:
            params.update(style.provider_overrides['pollinations'])
            return params

        # Build style prompt prefix
        style_keywords = self._build_style_prompt(style)

        if 'prompt' in params:
            params['prompt'] = f"{style_keywords} {params['prompt']}"
        else:
            params['style_prefix'] = style_keywords

        # img2img reference (for gptimage model)
        if style.reference_image:
            params['reference_image'] = style.reference_image
            params['model'] = 'gptimage'  # Content-preserving model

        return params

    def _build_style_prompt(self, style: StyleProfile) -> str:
        """Build prompt prefix from style characteristics."""
        parts = []

        # Platform style
        platform_styles = {
            'genesis': '16-bit Genesis/Mega Drive pixel art style,',
            'megadrive': '16-bit Genesis/Mega Drive pixel art style,',
            'nes': '8-bit NES pixel art style, limited palette,',
            'snes': '16-bit SNES pixel art style, rich colors,',
            'gba': '32-bit GBA pixel art style,',
            'gb': '4-color Game Boy pixel art style,',
            'gbc': '8-bit Game Boy Color pixel art style,',
        }
        parts.append(platform_styles.get(style.target_platform.lower(), 'pixel art style,'))

        # Outline
        outline_prompts = {
            OutlineStyle.BLACK: 'black outlines,',
            OutlineStyle.COLORED: 'colored outlines,',
            OutlineStyle.SELECTIVE: 'selective outlines,',
            OutlineStyle.NONE: 'no outlines, lineless,',
        }
        parts.append(outline_prompts.get(style.outline_style, ''))

        # Shading
        shading_prompts = {
            ShadingLevel.FLAT: 'flat shading, solid colors,',
            ShadingLevel.SIMPLE: 'simple cel shading,',
            ShadingLevel.MODERATE: 'pixel art shading,',
            ShadingLevel.DETAILED: 'detailed shading,',
        }
        parts.append(shading_prompts.get(style.shading_level, ''))

        # Detail
        detail_prompts = {
            DetailLevel.LOW: 'chunky pixels, low detail,',
            DetailLevel.MEDIUM: 'clean pixels,',
            DetailLevel.HIGH: 'fine detail,',
        }
        parts.append(detail_prompts.get(style.detail_level, ''))

        # Palette hint
        if style.palette:
            num_colors = len(style.palette)
            parts.append(f'{num_colors}-color palette,')

        return ' '.join(filter(None, parts))


class BFLKontextAdapter(StyleAdapter):
    """
    Style adapter for BFL (Black Forest Labs) Flux Kontext API.

    Kontext supports:
    - image_url: Reference image for style
    - strength: How much to preserve reference
    - Prompt-based style guidance
    """

    @property
    def provider_name(self) -> str:
        return "bfl"

    def get_supported_features(self) -> List[str]:
        return ['reference_image', 'prompt_style', 'strength']

    def apply_style(self, style: StyleProfile, params: Dict[str, Any]) -> Dict[str, Any]:
        params = params.copy()

        # Check for provider-specific overrides
        if 'bfl' in style.provider_overrides:
            params.update(style.provider_overrides['bfl'])
            return params

        # Reference image (needs to be uploaded/URL)
        if style.reference_image:
            # BFL requires URL - caller must handle upload
            params['needs_image_upload'] = True
            params['_reference_image'] = style.reference_image

        # Style via prompt
        style_prompt = self._build_style_prompt(style)
        if 'prompt' in params:
            params['prompt'] = f"{style_prompt} {params['prompt']}"

        # Strength (how much to preserve style vs follow prompt)
        params['strength'] = style.contrast  # Use contrast as proxy

        return params

    def _build_style_prompt(self, style: StyleProfile) -> str:
        """Build style prompt for BFL."""
        return f"pixel art, {style.target_platform} style, {style.detail_level.value} detail"


# =============================================================================
# STYLE MANAGER
# =============================================================================

class StyleManager:
    """
    Manages style profiles and adapter selection.

    Usage:
        manager = StyleManager()

        # Capture style from reference
        style = manager.capture_style(reference_img, "my_style")
        style.save("styles/my_style.json")

        # Apply style to generation
        adapter = manager.get_adapter("pixellab")
        params = adapter.apply_style(style, {"prompt": "warrior sprite"})
    """

    def __init__(self, styles_dir: str = "styles"):
        self.styles_dir = Path(styles_dir)
        self.styles_dir.mkdir(exist_ok=True)

        # Registered adapters (instance variable, not class variable)
        self._adapters: Dict[str, StyleAdapter] = {}

        # Register default adapters
        self.register_adapter(PixelLabAdapter())
        self.register_adapter(PollinationsAdapter())
        self.register_adapter(BFLKontextAdapter())

    def register_adapter(self, adapter: StyleAdapter) -> None:
        """Register a style adapter for a provider."""
        self._adapters[adapter.provider_name.lower()] = adapter

    def get_adapter(self, provider: str) -> Optional[StyleAdapter]:
        """Get adapter for a provider."""
        return self._adapters.get(provider.lower())

    def list_adapters(self) -> List[str]:
        """List registered adapter names."""
        return list(self._adapters.keys())

    def capture_style(self, img: Image.Image, name: str,
                      platform: str = "genesis") -> StyleProfile:
        """
        Analyze image and capture its style characteristics.

        Args:
            img: Reference sprite image
            name: Style profile name
            platform: Target platform hint

        Returns:
            StyleProfile capturing the style
        """
        # Extract palette
        palette = self._extract_palette(img, max_colors=16,
                                        snap_to_platform=(platform in ('genesis', 'megadrive')))

        # Detect visual characteristics
        outline_style, _outline_color = self._detect_outline(img)
        shading_level = self._detect_shading(img)
        detail_level = self._detect_detail(img)
        contrast = self._measure_contrast(img)
        saturation = self._measure_saturation(img)
        dither = self._detect_dither(img)

        return StyleProfile(
            name=name,
            palette=palette,
            outline_style=outline_style,
            shading_level=shading_level,
            detail_level=detail_level,
            _reference_image=img,
            contrast=contrast,
            saturation=saturation,
            dither_pattern=dither,
            target_platform=platform,
        )

    def save_style(self, style: StyleProfile,
                   include_reference: bool = False) -> str:
        """
        Save style profile to styles directory.

        Args:
            style: Style to save
            include_reference: If True, save reference image alongside JSON

        Returns:
            Path to saved style file
        """
        style_path = self.styles_dir / f"{style.name}.json"

        # Optionally save reference image
        if include_reference and style._reference_image:
            ref_path = self.styles_dir / f"{style.name}_reference.png"
            style._reference_image.save(ref_path)
            style.reference_image_path = str(ref_path)

        style.save(str(style_path))
        return str(style_path)

    def load_style(self, name: str) -> Optional[StyleProfile]:
        """Load a saved style profile by name."""
        style_path = self.styles_dir / f"{name}.json"
        if style_path.exists():
            return StyleProfile.load(str(style_path))
        return None

    def list_styles(self) -> List[str]:
        """List available saved style names."""
        return [p.stem for p in self.styles_dir.glob("*.json")]

    def apply_style(self, style: StyleProfile, provider: str,
                    params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply style using appropriate adapter.

        Args:
            style: Style to apply
            provider: AI provider name
            params: Generation parameters

        Returns:
            Updated parameters with style applied
        """
        adapter = self.get_adapter(provider)
        if adapter:
            return adapter.apply_style(style, params)

        # Fallback: return params unchanged with warning
        print(f"[WARN] No style adapter for provider '{provider}', style not applied")
        return params

    # -------------------------------------------------------------------------
    # Style Analysis Helpers
    # -------------------------------------------------------------------------

    def _extract_palette(self, img: Image.Image, max_colors: int = 16,
                         snap_to_platform: bool = False) -> List[Tuple[int, int, int]]:
        """
        Extract dominant colors from image.

        Args:
            img: Source image
            max_colors: Maximum colors to extract
            snap_to_platform: If True, snap to Genesis color levels

        Returns:
            List of RGB tuples
        """
        # Convert to RGB if needed
        if img.mode != 'RGB':
            if img.mode == 'RGBA':
                # Remove transparency, use magenta as background
                bg = Image.new('RGB', img.size, (255, 0, 255))
                bg.paste(img, mask=img.split()[3])
                img = bg
            else:
                img = img.convert('RGB')

        # Count colors
        pixels = list(img.getdata())

        # Filter out magenta (transparency)
        MAGENTA = (255, 0, 255)
        non_transparent = [p for p in pixels if p != MAGENTA]

        if not non_transparent:
            return [MAGENTA]  # All transparent

        counter = Counter(non_transparent)
        common = counter.most_common(max_colors - 1)

        # Build palette with magenta first (for transparency)
        palette = [MAGENTA]

        for color, _ in common:
            if snap_to_platform:
                color = self._snap_to_genesis_color(color)

            if color not in palette:
                palette.append(color)

            if len(palette) >= max_colors:
                break

        return palette

    def _snap_to_genesis_color(self, color: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """Snap RGB to nearest Genesis-valid color (3 bits per channel)."""
        GENESIS_LEVELS = [0, 36, 72, 109, 145, 182, 218, 255]

        def snap_channel(v: int) -> int:
            return min(GENESIS_LEVELS, key=lambda x: abs(x - v))

        return (snap_channel(color[0]), snap_channel(color[1]), snap_channel(color[2]))

    def _detect_outline(self, img: Image.Image) -> Tuple[OutlineStyle, Optional[Tuple]]:
        """Detect outline style and color."""
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        pixels = img.load()
        edge_colors = []

        # Sample edge pixels
        for x in range(img.width):
            for y in [0, img.height - 1]:
                if pixels[x, y][3] > 128:
                    edge_colors.append(pixels[x, y][:3])

        for y in range(img.height):
            for x in [0, img.width - 1]:
                if pixels[x, y][3] > 128:
                    edge_colors.append(pixels[x, y][:3])

        if not edge_colors:
            return OutlineStyle.NONE, None

        color_counts = Counter(edge_colors)
        most_common = color_counts.most_common(1)[0][0]

        # Detect type
        if most_common == (0, 0, 0):
            return OutlineStyle.BLACK, most_common
        elif len(color_counts) > 3:
            return OutlineStyle.SELECTIVE, most_common
        else:
            return OutlineStyle.COLORED, most_common

    def _detect_shading(self, img: Image.Image) -> ShadingLevel:
        """Detect shading complexity."""
        if img.mode != 'L':
            gray = img.convert('L')
        else:
            gray = img

        # Count unique brightness levels
        levels = set(gray.getdata())

        if len(levels) <= 4:
            return ShadingLevel.FLAT
        elif len(levels) <= 8:
            return ShadingLevel.SIMPLE
        elif len(levels) <= 16:
            return ShadingLevel.MODERATE
        else:
            return ShadingLevel.DETAILED

    def _detect_detail(self, img: Image.Image) -> DetailLevel:
        """Detect detail level based on high-frequency content."""
        if img.mode != 'L':
            gray = img.convert('L')
        else:
            gray = img

        # Simple edge detection proxy
        edges = gray.filter(ImageFilter.FIND_EDGES)
        edge_pixels = list(edges.getdata())

        if not edge_pixels:
            return DetailLevel.MEDIUM

        # Calculate edge density
        edge_density = sum(1 for p in edge_pixels if p > 50) / len(edge_pixels)

        if edge_density < 0.1:
            return DetailLevel.LOW
        elif edge_density < 0.25:
            return DetailLevel.MEDIUM
        else:
            return DetailLevel.HIGH

    def _measure_contrast(self, img: Image.Image) -> float:
        """Measure image contrast (0-1)."""
        if img.mode != 'L':
            gray = img.convert('L')
        else:
            gray = img

        pixels = list(gray.getdata())
        if not pixels:
            return 0.5

        return (max(pixels) - min(pixels)) / 255.0

    def _measure_saturation(self, img: Image.Image) -> float:
        """Measure average saturation (0-1)."""
        if img.mode != 'RGB':
            img = img.convert('RGB')

        pixels = list(img.getdata())
        if not pixels:
            return 0.5

        saturations = [rgb_to_hsv(r/255, g/255, b/255)[1] for r, g, b in pixels]

        return sum(saturations) / len(saturations)

    def _detect_dither(self, img: Image.Image) -> str:
        """Detect dithering pattern."""
        if img.mode != 'RGB':
            img = img.convert('RGB')

        pixels = img.load()
        checkerboard_count = 0

        for y in range(1, img.height - 1):
            for x in range(1, img.width - 1):
                p00 = pixels[x, y]
                p01 = pixels[x + 1, y]
                p10 = pixels[x, y + 1]
                p11 = pixels[x + 1, y + 1]

                if p00 == p11 and p01 == p10 and p00 != p01:
                    checkerboard_count += 1

        total = (img.width - 2) * (img.height - 2)
        ratio = checkerboard_count / total if total > 0 else 0

        if ratio > 0.1:
            return "bayer"
        elif ratio > 0.02:
            return "light"
        return "none"


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def capture_style(img: Image.Image, name: str,
                  platform: str = "genesis") -> StyleProfile:
    """
    Convenience function to capture style from an image.

    Args:
        img: Reference sprite image
        name: Style profile name
        platform: Target platform

    Returns:
        StyleProfile
    """
    manager = StyleManager()
    return manager.capture_style(img, name, platform)


def apply_style(style: StyleProfile, provider: str,
                params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to apply style to generation params.

    Args:
        style: Style to apply
        provider: AI provider name
        params: Generation parameters

    Returns:
        Updated parameters
    """
    manager = StyleManager()
    return manager.apply_style(style, provider, params)


def load_style(name: str, styles_dir: str = "styles") -> Optional[StyleProfile]:
    """
    Convenience function to load a saved style.

    Args:
        name: Style profile name
        styles_dir: Directory containing style files

    Returns:
        StyleProfile or None
    """
    manager = StyleManager(styles_dir)
    return manager.load_style(name)
