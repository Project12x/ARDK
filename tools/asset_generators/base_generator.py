"""
Base Asset Generator - Foundation for all AI-powered asset generators.

Provides:
- Abstract base class for generators
- Pollinations.ai client with model selection
- Generation flags for optimization control
- Common utilities for image processing
- Integration with per-platform system limits
"""

import os
import json
import hashlib
import time
import logging
import urllib.request
import urllib.error
import base64
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from io import BytesIO
from pathlib import Path

# Configure logging
logger = logging.getLogger('PollinationsClient')

try:
    from PIL import Image
    import numpy as np
except ImportError:
    raise ImportError("PIL and numpy required: pip install pillow numpy")

# Import comprehensive platform limits
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from configs.platform_limits import (
    PlatformLimits, get_platform_limits, get_recommended_frames,
    supports_chr_animation, get_animation_banks, validate_asset_for_platform,
    NES_LIMITS, GENESIS_LIMITS, SNES_LIMITS, GAMEBOY_LIMITS,
    PlatformTier
)
from configs.api_keys import get_api_key, POLLINATIONS_API_KEY, BFL_API_KEY

# Import modular model and prompt systems
from .model_config import (
    ModelConfig, ModelTier, get_model_config, get_task_models,
    get_model_for_task, get_endpoint_for_model, get_img2img_models,
    get_txt2img_models, ECONOMY_CONFIG, QUALITY_CONFIG, PRECISION_CONFIG,
)
from .prompt_system import (
    PromptBuilder, get_platform_prompt, get_available_platforms,
    get_platform_info, PLATFORM_CONSTRAINTS,
)
from .pixellab_client import (
    PixelLabClient, GenerationResult as PixelLabResult,
    create_sprite, create_animation,
    CameraView, Direction, Outline, Shading, Detail,
)


# =============================================================================
# Pollinations.ai Model Policy
# =============================================================================
# "Best model for each task" - optimized for retro game asset generation

MODEL_MAP = {
    'image_generation': 'flux',           # Best pixel-art output, clean edges
    'sprite_detection': 'gemini-fast',    # Fast bounding box detection
    'palette_extraction': 'openai-large', # Best color understanding
    'animation_analysis': 'gemini',       # Frame timing, motion detection
    'layout_analysis': 'gemini-large',    # Complex sheet parsing
    'general': 'openai',                  # Fallback for misc tasks
}

# Pollinations API endpoints
POLLINATIONS_IMAGE_URL = "https://image.pollinations.ai/prompt/{prompt}"
POLLINATIONS_CHAT_URL = "https://gen.pollinations.ai/v1/chat/completions"

# Free image hosting for img2img (Pollinations requires image URL, not base64)
# catbox.moe is reliable and free
IMAGE_HOST_URL = "https://catbox.moe/user/api.php"

# Pollinations API endpoints
# gen.pollinations.ai is the correct endpoint for img2img
POLLINATIONS_GEN_URL = "https://gen.pollinations.ai/image/{prompt}"

# BFL (Black Forest Labs) API for Flux Kontext - precise dimensions
# Docs: https://docs.bfl.ml/kontext/kontext_image_editing
BFL_API_URL = "https://api.bfl.ai/v1/flux-kontext-pro"

# Available img2img models
# TESTED 2026-01-13 (FINAL):
#
# Pollinations (gen.pollinations.ai) - content preservation:
# | Model        | Content | Dimensions | Notes                              |
# |--------------|---------|------------|------------------------------------|
# | gptimage     | YES     | ~1024      | Best content preservation          |
# | gptimage-lg  | YES     | ~1024      | Higher quality, same behavior      |
# | nanobanana   | YES     | 1024x1024  | Good alternative                   |
#
# BFL Kontext (api.bfl.ml) - precise dimensions:
# | Model        | Content | Dimensions | Notes                              |
# |--------------|---------|------------|------------------------------------|
# | flux-kontext | YES     | EXACT      | Requires BFL API key               |
#
# Strategy: gptimage for content, resize for aspect ratio
#           OR BFL Kontext for precise dimensions (when key available)
#
IMG2IMG_MODELS = {
    'edit': 'gptimage-large',             # Content preservation on gen.pollinations.ai
    'upscale': 'gptimage-large',          # Upscale with content preservation
    'enhance': 'gptimage-large',          # Detail enhancement
    'stylize': 'gptimage-large',          # Style transfer with preservation
    'pixel_art': 'flux',                  # Flux Schnell - best for pixel art generation (t2i)
    'fast': 'turbo',                      # SDXL Turbo - very fast for prototypes (t2i)
    'detail': 'gptimage',                 # GPTimage also works well
    'preserve_content': 'gptimage',       # Alternative content-preserving model
}

# Platform-specific display resolutions and aspect ratios
PLATFORM_RESOLUTIONS = {
    # 8-bit platforms
    'nes':     {'width': 256, 'height': 240, 'aspect': '16:15'},
    'sms':     {'width': 256, 'height': 192, 'aspect': '4:3'},
    'gb':      {'width': 160, 'height': 144, 'aspect': '10:9'},
    'gbc':     {'width': 160, 'height': 144, 'aspect': '10:9'},
    'c64':     {'width': 320, 'height': 200, 'aspect': '8:5'},

    # 16-bit platforms
    'genesis': {'width': 320, 'height': 224, 'aspect': '10:7'},
    'snes':    {'width': 256, 'height': 224, 'aspect': '8:7'},
    'pce':     {'width': 256, 'height': 224, 'aspect': '8:7'},

    # 32-bit platforms
    'gba':     {'width': 240, 'height': 160, 'aspect': '3:2'},

    # Generic tiers
    '8bit':    {'width': 256, 'height': 240, 'aspect': '16:15'},
    '16bit':   {'width': 320, 'height': 224, 'aspect': '10:7'},
    '32bit':   {'width': 320, 'height': 240, 'aspect': '4:3'},
}

# Pixel art style prompts per platform tier
PIXEL_ART_STYLE_PROMPTS = {
    '8bit': """8-bit pixel art style with chunky pixels and limited palette.
Sharp edges, no anti-aliasing, no gradients. Retro NES/SMS game aesthetic.""",

    '16bit': """16-bit pixel art style with clean pixels and richer colors.
Genesis/SNES game aesthetic. Sharp pixels, subtle dithering allowed.
No smooth gradients or photorealistic shading.""",

    '32bit': """32-bit pixel art style with detailed sprites but still pixel-based.
GBA game aesthetic. Clean pixels, more colors, but maintain retro feel.
No anti-aliasing or soft blending.""",
}


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class GenerationFlags:
    """Flags controlling asset generation and optimization."""

    # Tile optimization
    use_h_flip: bool = True           # Allow horizontal flip matching
    use_v_flip: bool = True           # Allow vertical flip matching
    detect_symmetry: bool = True      # Analyze tiles for symmetry
    deduplicate_tiles: bool = True    # Merge identical tiles

    # Background options
    seamless_loop: bool = True        # Ensure seamless horizontal loop
    generate_collision: bool = False  # Generate collision data

    # Animation options
    animation_set: str = 'standard'   # minimal, standard, full

    # Parallax options
    parallax_preset: str = 'standard_3layer'
    width_screens: int = 2            # Background width in screens

    # Generation style
    style_override: Optional[str] = None  # Override platform style


@dataclass
class GeneratedAsset:
    """Result of asset generation."""

    name: str
    image: Image.Image
    palette: List[int]
    metadata: Dict[str, Any] = field(default_factory=dict)
    chr_data: Optional[bytes] = None
    tile_map: Optional[List[int]] = None
    warnings: List[str] = field(default_factory=list)


@dataclass
class PlatformConfig:
    """
    Platform-specific configuration for asset generation.

    This class provides a unified interface for generators to access platform
    constraints. It can be created directly or from comprehensive PlatformLimits.
    """

    name: str
    tier: str                         # MINIMAL, STANDARD, EXTENDED

    # Tile constraints
    tile_width: int = 8
    tile_height: int = 8
    max_tiles_per_bank: int = 256
    max_chr_banks: int = 2
    bits_per_pixel: int = 2           # 2bpp = 4 colors, 4bpp = 16 colors

    # Color constraints
    colors_per_palette: int = 4
    max_palettes: int = 4
    max_palettes_sprite: int = 4
    total_system_colors: int = 64

    # Sprite constraints
    max_sprites: int = 64
    max_sprites_per_scanline: int = 8
    sprite_sizes: List[Tuple[int, int]] = field(
        default_factory=lambda: [(8, 8), (16, 16)]
    )

    # Screen dimensions
    screen_width: int = 256
    screen_height: int = 240
    visible_height: int = 224         # NTSC safe area

    # Background layers
    background_layers: int = 1
    supports_parallax: bool = True
    max_parallax_layers: int = 3
    parallax_method: str = "scanline_irq"

    # Animation capabilities
    supports_chr_animation: bool = True
    max_animation_frames: int = 4
    animation_banks_available: int = 16
    recommended_frames: Dict[str, int] = field(default_factory=lambda: {
        'idle': 2, 'walk': 4, 'run': 4, 'attack': 3,
        'hurt': 2, 'death': 3, 'jump': 2,
    })

    # Memory constraints
    vram_size: int = 2048
    max_prg_rom: int = 524288         # With common mapper
    max_chr_rom: int = 262144

    # Optimization
    enable_flip_optimization: bool = True
    hardware_h_flip: bool = True
    hardware_v_flip: bool = True

    # Generation style
    prompt_style: str = "8-bit pixel art"
    resampling: str = "NEAREST"       # NEAREST, LANCZOS, BILINEAR

    # Reference to full limits (optional, for detailed queries)
    _full_limits: Optional[Any] = field(default=None, repr=False)

    def get_recommended_frame_count(self, animation_name: str) -> int:
        """Get recommended frame count for an animation type."""
        return self.recommended_frames.get(animation_name.lower(), 2)

    def validate_tile_count(self, count: int) -> Tuple[bool, str]:
        """Check if tile count is within limits."""
        if count > self.max_tiles_per_bank:
            return False, f"Tile count ({count}) exceeds limit ({self.max_tiles_per_bank})"
        if count > self.max_tiles_per_bank * 0.9:
            return True, f"Warning: Tile count ({count}) near limit"
        return True, ""

    def validate_sprite_count(self, count: int) -> Tuple[bool, str]:
        """Check if sprite count is within limits."""
        if count > self.max_sprites:
            return False, f"Sprite count ({count}) exceeds limit ({self.max_sprites})"
        return True, ""

    def validate_color_count(self, count: int, is_sprite: bool = False) -> Tuple[bool, str]:
        """Check if color count is within palette limits."""
        max_colors = self.colors_per_palette * (
            self.max_palettes_sprite if is_sprite else self.max_palettes
        )
        if count > max_colors:
            return False, f"Color count ({count}) exceeds limit ({max_colors})"
        return True, ""

    def can_animate_chr(self, frame_count: int) -> Tuple[bool, str]:
        """Check if CHR animation with given frames is supported."""
        if not self.supports_chr_animation:
            return False, f"{self.name} does not support CHR bank animation"
        if frame_count > self.max_animation_frames:
            return False, f"Frame count ({frame_count}) exceeds limit ({self.max_animation_frames})"
        if frame_count > self.animation_banks_available:
            return False, f"Not enough animation banks ({self.animation_banks_available} available)"
        return True, ""


def platform_config_from_limits(limits: PlatformLimits) -> PlatformConfig:
    """
    Create a PlatformConfig from comprehensive PlatformLimits.

    This bridges the detailed hardware limits to the generator interface.
    """
    # Determine prompt style based on tier
    tier_styles = {
        PlatformTier.MINIMAL: "8-bit pixel art, limited palette, chunky pixels, no anti-aliasing",
        PlatformTier.MINIMAL_PLUS: "8-bit pixel art, slightly more colors, clean edges",
        PlatformTier.STANDARD: "16-bit pixel art, vibrant colors, detailed sprites",
        PlatformTier.STANDARD_PLUS: "16-bit pixel art, rich colors, smooth gradients",
        PlatformTier.EXTENDED: "32-bit pixel art, full color, high detail",
    }

    # Determine resampling based on tier
    resampling = "NEAREST" if limits.tier in (PlatformTier.MINIMAL, PlatformTier.MINIMAL_PLUS) else "LANCZOS"

    return PlatformConfig(
        name=limits.name,
        tier=limits.tier.name,

        # Tiles
        tile_width=limits.tiles.tile_width,
        tile_height=limits.tiles.tile_height,
        max_tiles_per_bank=limits.tiles.max_tiles_per_bank,
        max_chr_banks=limits.tiles.max_banks_total,
        bits_per_pixel=limits.tiles.bits_per_pixel,

        # Colors
        colors_per_palette=limits.palettes.colors_per_palette,
        max_palettes=limits.palettes.max_palettes_bg,
        max_palettes_sprite=limits.palettes.max_palettes_sprite,
        total_system_colors=limits.palettes.total_system_colors,

        # Sprites
        max_sprites=limits.sprites.max_sprites_total,
        max_sprites_per_scanline=limits.sprites.max_sprites_per_scanline,
        sprite_sizes=limits.sprites.sprite_sizes,

        # Screen
        screen_width=limits.backgrounds.screen_width,
        screen_height=limits.backgrounds.screen_height,
        visible_height=limits.backgrounds.visible_height,

        # Background
        background_layers=limits.backgrounds.background_layers,
        supports_parallax=limits.backgrounds.supports_parallax,
        max_parallax_layers=limits.backgrounds.background_layers + 2,  # Layers + IRQ splits
        parallax_method=limits.backgrounds.parallax_method,

        # Animation
        supports_chr_animation=limits.animations.supports_chr_animation,
        max_animation_frames=limits.animations.max_animation_frames,
        animation_banks_available=limits.animations.animation_banks_available,
        recommended_frames=limits.animations.recommended_frames.copy(),

        # Memory
        vram_size=limits.memory.vram_size,
        max_prg_rom=limits.memory.extended_prg_rom,
        max_chr_rom=limits.memory.extended_chr_rom,

        # Optimization
        enable_flip_optimization=limits.tiles.hardware_h_flip or limits.tiles.hardware_v_flip,
        hardware_h_flip=limits.tiles.hardware_h_flip,
        hardware_v_flip=limits.tiles.hardware_v_flip,

        # Style
        prompt_style=tier_styles.get(limits.tier, "pixel art"),
        resampling=resampling,

        # Reference
        _full_limits=limits,
    )


# =============================================================================
# Pollinations API Client
# =============================================================================

class PollinationsClient:
    """Client for Pollinations.ai API with model selection."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize client with optional API key."""
        # Priority: passed key > env var > config file
        self.api_key = api_key or os.environ.get('POLLINATIONS_API_KEY', '') or POLLINATIONS_API_KEY
        self._cache_dir = Path('.cache/pollinations')
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def get_model(self, task: str) -> str:
        """Get best model for a given task."""
        return MODEL_MAP.get(task, MODEL_MAP['general'])

    def generate_image(
        self,
        prompt: str,
        width: int = 512,
        height: int = 512,
        seed: Optional[int] = None,
        model: str = 'flux',
    ) -> Image.Image:
        """Generate image via Pollinations image API."""

        # Build URL with parameters
        encoded_prompt = urllib.request.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        url += f"?width={width}&height={height}&model={model}&nologo=true"
        if seed is not None:
            url += f"&seed={seed}"

        # Check cache
        cache_key = hashlib.md5(url.encode()).hexdigest()
        cache_path = self._cache_dir / f"{cache_key}.png"
        if cache_path.exists():
            return Image.open(cache_path)

        # Fetch image
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'ARDK-AssetGenerator/1.0'
            })
            with urllib.request.urlopen(req, timeout=120) as response:
                image_data = response.read()

            # Save to cache
            with open(cache_path, 'wb') as f:
                f.write(image_data)

            return Image.open(BytesIO(image_data))

        except Exception as e:
            raise RuntimeError(f"Image generation failed: {e}")

    def analyze_image(
        self,
        image: Image.Image,
        prompt: str,
        task: str = 'general',
    ) -> str:
        """Analyze image with vision model."""

        model = self.get_model(task)

        # Convert image to base64
        buffer = BytesIO()
        if image.mode not in ('RGB', 'RGBA'):
            image = image.convert('RGB')
        image.save(buffer, format='PNG')
        img_b64 = base64.b64encode(buffer.getvalue()).decode()

        # Build request
        payload = {
            "model": model,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/png;base64,{img_b64}"
                    }}
                ]
            }],
            "max_tokens": 2000,
        }

        headers = {
            'Content-Type': 'application/json',
        }
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        try:
            req = urllib.request.Request(
                POLLINATIONS_CHAT_URL,
                data=json.dumps(payload).encode('utf-8'),
                headers=headers,
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read().decode('utf-8'))

            return result.get('choices', [{}])[0].get('message', {}).get('content', '')

        except Exception as e:
            raise RuntimeError(f"Image analysis failed: {e}")

    def chat(
        self,
        prompt: str,
        task: str = 'general',
    ) -> str:
        """Send chat request (non-vision)."""

        model = self.get_model(task)

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2000,
        }

        headers = {
            'Content-Type': 'application/json',
        }
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        try:
            req = urllib.request.Request(
                POLLINATIONS_CHAT_URL,
                data=json.dumps(payload).encode('utf-8'),
                headers=headers,
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))

            return result.get('choices', [{}])[0].get('message', {}).get('content', '')

        except Exception as e:
            raise RuntimeError(f"Chat request failed: {e}")

    # =========================================================================
    # IMG2IMG Methods - Transform existing images with AI
    # =========================================================================

    def _upload_image_temp(self, image: Image.Image) -> Optional[str]:
        """
        Upload image to temporary hosting to get a URL.

        Uses catbox.moe which is free and reliable.
        Files are kept indefinitely unless deleted.

        Returns:
            URL to the hosted image, or None if upload fails
        """
        try:
            # Convert to PNG bytes
            buffer = BytesIO()
            if image.mode not in ('RGB', 'RGBA'):
                image = image.convert('RGBA')
            image.save(buffer, format='PNG', optimize=True)
            image_data = buffer.getvalue()

            # catbox.moe multipart form data
            boundary = '----WebKitFormBoundary' + hashlib.md5(str(id(image)).encode()).hexdigest()[:16]

            body = b'\r\n'.join([
                f'--{boundary}'.encode(),
                b'Content-Disposition: form-data; name="reqtype"',
                b'',
                b'fileupload',
                f'--{boundary}'.encode(),
                b'Content-Disposition: form-data; name="fileToUpload"; filename="sprite.png"',
                b'Content-Type: image/png',
                b'',
                image_data,
                f'--{boundary}--'.encode(),
                b''
            ])

            req = urllib.request.Request(
                IMAGE_HOST_URL,
                data=body,
                headers={
                    'Content-Type': f'multipart/form-data; boundary={boundary}',
                    'User-Agent': 'ARDK-AssetGenerator/1.0'
                },
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=60) as response:
                url = response.read().decode('utf-8').strip()
                print(f"    Uploaded to: {url}")
                return url

        except Exception as e:
            print(f"    Image upload failed: {e}")
            return None

    def img2img_edit(
        self,
        image: Image.Image,
        edit_prompt: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        model: str = 'gptimage',
    ) -> Image.Image:
        """
        Edit an image using AI img2img.

        Uses gen.pollinations.ai with models that support image input:
        - gptimage: Cheap, good for general edits
        - gptimage-large: Higher quality, more expensive
        - nanobanana: Gemini-based, good quality but limited rate
        - seedream: ByteDance, good quality

        Args:
            image: Source image to edit
            edit_prompt: What changes to make
            width: Output width (default: source width)
            height: Output height (default: source height)
            model: Model to use (gptimage, gptimage-large, nanobanana, seedream)

        Returns:
            Edited image with enhancements
        """
        width = width or image.width
        height = height or image.height

        # Clamp dimensions to reasonable limits
        max_dim = 1280
        if width > max_dim or height > max_dim:
            scale = max_dim / max(width, height)
            width = int(width * scale)
            height = int(height * scale)

        # Use img2img models that support image input
        valid_models = ('gptimage', 'gptimage-large', 'nanobanana', 'seedream')
        use_model = model if model in valid_models else 'gptimage'
        return self.img2img_enhance(image, edit_prompt, width, height, model=use_model, use_ai=True)

    def _calculate_aspect_ratio(self, width: int, height: int) -> str:
        """
        Calculate aspect ratio string from dimensions.

        Returns simplified ratio like "4:3", "16:9", etc.
        """
        from math import gcd
        divisor = gcd(width, height)
        w_ratio = width // divisor
        h_ratio = height // divisor

        # Simplify common ratios
        common_ratios = {
            (4, 3): "4:3",      # NES, most 8-bit
            (16, 9): "16:9",    # Modern widescreen
            (16, 10): "16:10",  # Some monitors
            (3, 2): "3:2",      # Photos
            (1, 1): "1:1",      # Square
            (5, 4): "5:4",      # Some monitors
            (10, 7): "10:7",    # ~Genesis 320x224
            (31, 28): "31:28",  # Genesis exact
        }

        # Check if close to common ratio
        if (w_ratio, h_ratio) in common_ratios:
            return common_ratios[(w_ratio, h_ratio)]

        # Return exact ratio
        return f"{w_ratio}:{h_ratio}"

    def img2img_enhance(
        self,
        image: Image.Image,
        enhancement_prompt: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        strength: float = 0.75,
        model: str = 'gptimage',
        use_ai: bool = True,
    ) -> Image.Image:
        """
        Upscale/enhance an image using AI img2img.

        Uses gen.pollinations.ai with gptimage model which properly supports
        image input modality. The model preserves content concepts while
        adding detail and enhancing quality.

        Args:
            image: Source image to transform
            enhancement_prompt: What changes to make
            width: Output width (default: source width)
            height: Output height (default: source height)
            strength: Unused (kept for compatibility)
            model: Model to use (gptimage, gptimage-large, nanobanana, seedream)
            use_ai: Set False for algorithmic-only upscale

        Returns:
            Enhanced image at target dimensions
        """
        width = width or image.width
        height = height or image.height

        if not use_ai:
            # SAFE: Algorithmic upscale - preserves content perfectly
            print(f"    Upscale (algorithmic): {image.width}x{image.height} -> {width}x{height}")
            if image.width != width or image.height != height:
                return image.resize((width, height), Image.LANCZOS)
            return image

        # Calculate aspect ratio for API
        aspect_ratio = self._calculate_aspect_ratio(width, height)
        print(f"    AI img2img ({model}): {image.width}x{image.height} -> {width}x{height} (aspect: {aspect_ratio})...")

        # Upload source image to catbox.moe
        image_url = self._upload_image_temp(image)
        if not image_url:
            print(f"    Upload failed, falling back to algorithmic")
            return image.resize((width, height), Image.LANCZOS)

        # Build prompt - keep it short for URL length
        prompt = enhancement_prompt

        encoded_prompt = urllib.request.quote(prompt)

        # CRITICAL: Use gen.pollinations.ai for gptimage img2img
        # Tested 2026-01-13: gen.pollinations.ai does actual img2img (content preservation)
        # image.pollinations.ai ignores the image param for most models
        # Note: Dimensions may be ignored - we resize after
        base_url = f"https://gen.pollinations.ai/image/{encoded_prompt}"

        # Build query string - don't encode the image URL (it's already a valid URL)
        params = [
            f"model={model}",
            f"width={width}",
            f"height={height}",
            f"nologo=true",
            f"image={image_url}",  # Don't URL-encode the image URL
        ]

        # Add API token as query param (more reliable than header for some endpoints)
        if self.api_key:
            params.append(f"token={self.api_key}")

        url = f"{base_url}?{'&'.join(params)}"

        headers = {'User-Agent': 'ARDK-AssetGenerator/1.0', 'Accept': 'image/*'}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        req = urllib.request.Request(url, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=180) as response:
                content_type = response.headers.get('Content-Type', '')
                result_data = response.read()

            if 'image' not in content_type:
                print(f"    API returned non-image ({content_type}), falling back")
                return image.resize((width, height), Image.LANCZOS)

            result = Image.open(BytesIO(result_data))
            print(f"    AI returned: {result.width}x{result.height}")

            # Resize to target dimensions if API returned different size
            if result.width != width or result.height != height:
                print(f"    Resizing to target: {width}x{height}")
                result = result.resize((width, height), Image.LANCZOS)

            return result

        except Exception as e:
            print(f"    AI img2img failed: {e}, falling back to algorithmic")
            return image.resize((width, height), Image.LANCZOS)

    def img2img_bfl_kontext(
        self,
        image: Image.Image,
        prompt: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        aspect_ratio: Optional[str] = None,
    ) -> Optional[Image.Image]:
        """
        Use BFL (Black Forest Labs) Flux Kontext API for precise img2img.

        Requires BFL_API_KEY to be set. Returns None if key not available.
        BFL Kontext preserves content AND respects exact dimensions.

        Args:
            image: Source image
            prompt: Enhancement/edit prompt
            width: Target width (or use aspect_ratio)
            height: Target height (or use aspect_ratio)
            aspect_ratio: Alternative to w/h (e.g., "16:9", "4:3")

        Returns:
            Enhanced image at exact dimensions, or None if unavailable
        """
        if not BFL_API_KEY:
            logger.warning("BFL Kontext: No API key configured")
            return None

        width = width or image.width
        height = height or image.height
        start_time = time.time()

        logger.info(f"BFL Kontext: {image.width}x{image.height} -> {width}x{height}")
        logger.debug(f"Prompt: {prompt[:100]}...")

        # Convert image to base64 (BFL requires base64, not URLs)
        logger.debug("Converting image to base64...")
        buffer = BytesIO()
        img_to_encode = image.convert('RGB') if image.mode != 'RGB' else image
        img_to_encode.save(buffer, format='PNG')
        import base64
        b64_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        image_data = f"data:image/png;base64,{b64_data}"
        logger.debug(f"Base64 length: {len(image_data)} chars")

        # Build request per BFL docs: https://docs.bfl.ml/kontext/kontext_image_editing
        # Note: BFL Kontext does NOT support width/height, only aspect_ratio
        # We'll resize the output to exact dimensions after receiving it

        # Calculate aspect ratio from target dimensions
        if aspect_ratio:
            ar = aspect_ratio
        else:
            # Calculate aspect ratio string from dimensions
            from math import gcd
            g = gcd(width, height)
            ar = f"{width // g}:{height // g}"

        payload = {
            "prompt": prompt,
            "input_image": image_data,  # BFL requires base64, not URLs
        }
        # BFL Kontext matches input dimensions (rounded to 32). Only add aspect_ratio if overriding.
        if aspect_ratio:
            payload["aspect_ratio"] = ar

        logger.debug(f"BFL Request payload: {json.dumps(payload, indent=2)}")
        data = json.dumps(payload).encode('utf-8')

        headers = {
            'Content-Type': 'application/json',
            'accept': 'application/json',
            'x-key': BFL_API_KEY,
        }

        req = urllib.request.Request(BFL_API_URL, data=data, headers=headers, method='POST')

        try:
            logger.debug(f"POST {BFL_API_URL}")
            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read().decode('utf-8'))
            logger.debug(f"BFL Response: {json.dumps(result, indent=2)}")

            # BFL returns a task ID and polling_url - poll for result
            if 'id' in result:
                task_id = result['id']
                logger.info(f"BFL task submitted: {task_id}")
                # Use polling_url from response, or construct from id
                result_url = result.get('polling_url', f"https://api.bfl.ai/v1/get_result?id={task_id}")

                for poll_count in range(90):  # Wait up to 90 seconds
                    time.sleep(1)
                    poll_req = urllib.request.Request(result_url, headers={'x-key': BFL_API_KEY})
                    with urllib.request.urlopen(poll_req, timeout=30) as poll_resp:
                        poll_result = json.loads(poll_resp.read().decode('utf-8'))
                        status = poll_result.get('status', 'Unknown')

                        if poll_count % 5 == 0:  # Log every 5 seconds
                            logger.debug(f"Poll {poll_count}: status={status}")

                        if status == 'Ready':
                            img_url = poll_result.get('result', {}).get('sample')
                            if img_url:
                                logger.debug(f"Result URL: {img_url}")
                                img_req = urllib.request.Request(img_url)
                                with urllib.request.urlopen(img_req, timeout=60) as img_resp:
                                    result_img = Image.open(BytesIO(img_resp.read()))
                                    elapsed = time.time() - start_time

                                    # Resize to exact target dimensions if needed
                                    if result_img.width != width or result_img.height != height:
                                        logger.debug(f"Resizing {result_img.width}x{result_img.height} -> {width}x{height}")
                                        result_img = result_img.resize((width, height), Image.LANCZOS)

                                    logger.info(f"BFL Kontext SUCCESS: {result_img.width}x{result_img.height} in {elapsed:.1f}s")
                                    return result_img
                        elif poll_result.get('status') == 'Error':
                            error_msg = poll_result.get('error', 'Unknown error')
                            elapsed = time.time() - start_time
                            logger.error(f"BFL Kontext error after {elapsed:.1f}s: {error_msg}")
                            return None

            elapsed = time.time() - start_time
            logger.error(f"BFL Kontext timeout after {elapsed:.1f}s (60 polls)")
            return None

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"BFL Kontext failed after {elapsed:.1f}s: {e}")
            return None

    def img2img_multi_model(
        self,
        image: Image.Image,
        prompt: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        models: Optional[List[str]] = None,
        save_dir: Optional[Path] = None,
        prefix: str = "variant",
    ) -> Dict[str, Any]:
        """
        Run img2img through multiple models for comparison.

        Generates alternates from different AI sources to help identify
        the best model for each task. Useful for dimension testing and
        style comparison.

        Args:
            image: Source image
            prompt: Enhancement/transformation prompt
            width: Target width
            height: Target height
            models: List of models to try (default: kontext, gptimage, seedream)
            save_dir: Directory to save results (optional)
            prefix: Filename prefix for saved variants

        Returns:
            Dict with:
                - 'results': {model_name: {'image': Image, 'actual_size': (w,h), 'success': bool}}
                - 'best_dimensions': model that best matched requested dimensions
                - 'summary': text summary of results
        """
        width = width or image.width
        height = height or image.height

        # Default models to test (img2img capable on gen.pollinations.ai)
        if models is None:
            # gptimage-large: best content preservation
            # nanobanana: good alternative
            # Note: These preserve content but ignore dimensions (we resize after)
            models = ['gptimage-large', 'nanobanana']

        start_time = time.time()
        logger.info(f"Multi-model img2img: {len(models)} models, target {width}x{height}")
        logger.debug(f"Models: {models}")
        logger.debug(f"Aspect ratio: {self._calculate_aspect_ratio(width, height)}")

        # Upload image once for all models
        logger.debug("Uploading source image...")
        image_url = self._upload_image_temp(image)
        if not image_url:
            logger.error("Multi-model img2img: Image upload failed")
            return {
                'results': {},
                'best_dimensions': None,
                'summary': 'Upload failed'
            }
        logger.debug(f"Uploaded: {image_url}")

        results = {}
        encoded_prompt = urllib.request.quote(prompt)

        # Rate limit delay between requests (seconds)
        request_delay = 3.0

        for i, model in enumerate(models):
            # Add delay between requests to avoid rate limiting
            if i > 0:
                logger.debug(f"Waiting {request_delay}s to avoid rate limit...")
                time.sleep(request_delay)

            logger.info(f"Trying model: {model}")

            # Select endpoint based on model
            # flux-kontext MUST use image.pollinations.ai to work correctly
            if model in ('flux-kontext', 'kontext'):
                base_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
            else:
                base_url = f"https://gen.pollinations.ai/image/{encoded_prompt}"

            params = [
                f"model={model}",
                f"width={width}",
                f"height={height}",
                f"nologo=true",
                f"image={image_url}",
            ]

            # Add API token as query param
            if self.api_key:
                params.append(f"token={self.api_key}")

            url = f"{base_url}?{'&'.join(params)}"

            headers = {'User-Agent': 'ARDK-AssetGenerator/1.0', 'Accept': 'image/*'}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'

            req = urllib.request.Request(url, headers=headers)

            try:
                with urllib.request.urlopen(req, timeout=180) as response:
                    content_type = response.headers.get('Content-Type', '')
                    result_data = response.read()

                if 'image' not in content_type:
                    logger.warning(f"{model}: Non-image response ({content_type})")
                    results[model] = {'success': False, 'error': 'non-image response'}
                    continue

                result_img = Image.open(BytesIO(result_data))
                actual_w, actual_h = result_img.width, result_img.height

                # Check dimension match
                dim_match = actual_w == width and actual_h == height
                aspect_match = abs(actual_w/actual_h - width/height) < 0.1

                if dim_match:
                    logger.info(f"{model}: {actual_w}x{actual_h} [EXACT MATCH]")
                elif aspect_match:
                    logger.info(f"{model}: {actual_w}x{actual_h} [aspect OK]")
                else:
                    logger.info(f"{model}: {actual_w}x{actual_h} [aspect: {self._calculate_aspect_ratio(actual_w, actual_h)}]")

                # Resize to target
                if actual_w != width or actual_h != height:
                    result_img = result_img.resize((width, height), Image.LANCZOS)

                results[model] = {
                    'success': True,
                    'image': result_img,
                    'actual_size': (actual_w, actual_h),
                    'requested_size': (width, height),
                    'dimension_match': dim_match,
                    'aspect_match': aspect_match,
                }

                # Save if directory provided
                if save_dir:
                    save_dir = Path(save_dir)
                    save_dir.mkdir(parents=True, exist_ok=True)
                    save_path = save_dir / f"{prefix}_{model}.png"
                    result_img.save(save_path)
                    results[model]['saved_path'] = str(save_path)

            except Exception as e:
                logger.error(f"{model}: FAILED - {e}")
                results[model] = {'success': False, 'error': str(e)}

        # Determine best model for dimensions
        best_dim = None
        for model, data in results.items():
            if data.get('success') and data.get('dimension_match'):
                best_dim = model
                break
        if not best_dim:
            for model, data in results.items():
                if data.get('success') and data.get('aspect_match'):
                    best_dim = model
                    break

        # Summary
        elapsed = time.time() - start_time
        successful = [m for m, d in results.items() if d.get('success')]
        summary = f"Tested {len(models)} models. "
        summary += f"Success: {len(successful)}/{len(models)}. "
        if best_dim:
            summary += f"Best for dimensions: {best_dim}"
        else:
            summary += "No model matched dimensions exactly."

        logger.info(f"Multi-model complete in {elapsed:.1f}s: {summary}")

        return {
            'results': results,
            'best_dimensions': best_dim,
            'summary': summary,
        }

    def img2img_upscale(
        self,
        image: Image.Image,
        target_platform: str,
        scale: int = 2,
        add_detail: bool = True,
        use_zimage: bool = True,
    ) -> Image.Image:
        """
        Upscale image with AI-added detail appropriate for target platform.

        Uses zimage (Z-Image Turbo) which has built-in 2x upscaling,
        or flux for generation-based upscaling.

        Args:
            image: Source image
            target_platform: Target platform name (genesis, snes, etc.)
            scale: Scale factor (2 or 4)
            add_detail: Whether to add detail (vs just resize)
            use_zimage: Use zimage model (has 2x upscale built-in)

        Returns:
            Upscaled image with added detail
        """
        target_width = image.width * scale
        target_height = image.height * scale

        if not add_detail:
            # Simple algorithmic upscale
            return image.resize(
                (target_width, target_height),
                Image.NEAREST
            )

        # Analyze source for content understanding
        analysis = self._quick_analyze(image)

        # Platform-specific detail prompt
        detail_prompts = {
            'genesis': 'Add 16-bit style shading and highlights, expand to 16 colors per tile, keep clean pixel edges',
            'megadrive': 'Add 16-bit style shading and highlights, expand to 16 colors per tile, keep clean pixel edges',
            'snes': 'Add SNES-style gradients and detail, richer color palette, smooth shading',
            'gba': 'Add GBA-style detail with 15-bit color depth, more color gradients',
            'bitmap': 'Add detail and smooth gradients, no tile constraints',
            'default': 'Add more detail and shading while maintaining pixel art style',
        }

        detail_prompt = detail_prompts.get(target_platform.lower(), detail_prompts['default'])

        full_prompt = f"""Upscale and enhance this pixel art for {target_platform}:

ORIGINAL: {analysis}
SIZE: {image.width}x{image.height} to {target_width}x{target_height}

ENHANCEMENT: {detail_prompt}

CRITICAL REQUIREMENTS:
- Maintain exact composition and layout
- Same subject, same pose, same elements
- Add detail and color depth appropriate for {target_platform}
- Clean pixel edges, no anti-aliasing to background
- Pixel art style throughout
"""

        # Use img2img_edit to actually transform the source image
        # kontext works best for image transformation
        model = 'kontext'

        # Use the proper img2img API that passes the actual image
        return self.img2img_edit(
            image=image,
            edit_prompt=full_prompt,
            width=target_width,
            height=target_height,
            model=model,
        )

    def img2img_tile_enhance(
        self,
        tile: Image.Image,
        source_colors: int,
        target_colors: int,
        context: str = "",
    ) -> Image.Image:
        """
        Enhance a single tile, expanding its color palette.

        Args:
            tile: 8x8 tile image
            source_colors: Colors in source (e.g., 4 for NES)
            target_colors: Colors in target (e.g., 16 for Genesis)
            context: What this tile represents

        Returns:
            Enhanced tile with expanded palette
        """
        # For very small tiles, generate at larger size and downscale
        gen_size = max(64, tile.width * 4)

        prompt = f"""Enhance this {tile.width}x{tile.height} pixel art tile:

CONTEXT: {context or 'game tile'}
COLORS: Expand from {source_colors} colors to {target_colors} colors

ADD:
- Subtle shading gradients
- Highlight details
- More color variation

PRESERVE:
- Original shapes and patterns
- Pixel art style
- Tile-ability (seamless edges if applicable)

DO NOT:
- Add anti-aliasing
- Change the basic design
- Add elements not in original
"""

        result = self.generate_image(
            prompt=prompt,
            width=gen_size,
            height=gen_size,
            model='flux',
        )

        # Downscale to target tile size
        return result.resize(
            (tile.width, tile.height),
            Image.NEAREST
        )

    def img2img_style_transfer(
        self,
        image: Image.Image,
        target_style: str,
        preserve_content: float = 0.8,
    ) -> Image.Image:
        """
        Transfer image to a different pixel art style.

        Args:
            image: Source image
            target_style: Target style (e.g., '8-bit NES', '16-bit Genesis')
            preserve_content: How much to preserve original (0-1)

        Returns:
            Style-transferred image
        """
        analysis = self._quick_analyze(image)

        prompt = f"""Convert this pixel art to {target_style} style:

ORIGINAL: {analysis}

TARGET STYLE: {target_style}

REQUIREMENTS:
- Recreate the same scene/subject in {target_style} style
- Preserve {preserve_content:.0%} of original composition
- Apply authentic {target_style} color palette and limitations
- Clean pixel edges, proper pixel art technique

OUTPUT: {image.width}x{image.height} pixels
"""

        return self.generate_image(
            prompt=prompt,
            width=image.width,
            height=image.height,
            model='flux',
        )

    def _quick_analyze(self, image: Image.Image) -> str:
        """
        Quick analysis of image content for img2img context.

        Returns a brief description of the image.
        """
        try:
            prompt = """Describe this pixel art image in 1-2 sentences.
Focus on: subject matter, main colors, composition.
Be specific but brief."""

            response = self.analyze_image(image, prompt, task='sprite_detection')

            # Clean up response
            response = response.strip()
            if len(response) > 200:
                response = response[:200] + '...'

            return response

        except Exception:
            # Fallback to basic analysis
            colors = image.convert('RGB').getcolors(maxcolors=256)
            if colors:
                dominant = sorted(colors, key=lambda x: x[0], reverse=True)[0][1]
                return f"Pixel art image, {image.width}x{image.height}, dominant color RGB{dominant}"
            return f"Pixel art image, {image.width}x{image.height}"

    def _detailed_analyze(self, image: Image.Image) -> str:
        """
        Detailed analysis of image for accurate style transfer.

        Returns a comprehensive description that can guide faithful regeneration.
        """
        try:
            prompt = """Analyze this pixel art image in detail for recreation. Describe:

1. SUBJECT: What is shown (characters, objects, scene elements)
2. COMPOSITION: Layout, positioning, framing (left/right/center, foreground/background)
3. COLOR PALETTE: List the main colors used (be specific: "neon pink", "dark purple", etc.)
4. STYLE: Pixel art style (chunky/detailed, shading type, outline style)
5. MOOD/ATMOSPHERE: Overall feeling (cyberpunk, retro, etc.)
6. KEY DETAILS: Any notable elements (glows, patterns, text to remove)

Be very specific so the image can be faithfully recreated."""

            response = self.analyze_image(image, prompt, task='palette_extraction')
            return response.strip()

        except Exception as e:
            print(f"Detailed analysis failed: {e}")
            return self._quick_analyze(image)

    def preprocess_remove_text(self, image: Image.Image, use_ai_detection: bool = True) -> Image.Image:
        """
        Remove AI-generated text labels from image.

        Two-step approach:
        1. Use AI VISION to detect text regions (coordinates, not generation)
        2. Crop to exclude those regions algorithmically

        Falls back to margin cropping if AI detection fails.

        Args:
            image: Source image
            use_ai_detection: Use AI to detect text regions (default True)

        Returns:
            Image with text removed
        """
        width, height = image.size

        # Skip for small/already-processed images
        if max(width, height) < 512:
            print(f"    Text removal: skipped (image already small: {width}x{height})")
            return image

        if use_ai_detection:
            try:
                print(f"    Detecting text regions via AI vision...")
                # Use vision API to DETECT text (not generate!)
                text_regions = self._detect_text_regions(image)

                if text_regions:
                    print(f"    Found {len(text_regions)} text regions")
                    # Calculate crop bounds to exclude text
                    cropped = self._crop_excluding_text(image, text_regions)
                    print(f"    Cropped to: {cropped.width}x{cropped.height}")
                    return cropped
                else:
                    print(f"    No text detected, keeping original")
                    return image

            except Exception as e:
                print(f"    AI text detection failed: {e}, using fallback crop")

        # Fallback: Crop margins where AI text labels typically appear
        top_crop = int(height * 0.08)
        bottom_crop = int(height * 0.92)
        left_crop = int(width * 0.02)
        right_crop = int(width * 0.98)

        cropped = image.crop((left_crop, top_crop, right_crop, bottom_crop))
        print(f"    Text removal (fallback crop): {width}x{height} -> {cropped.width}x{cropped.height}")

        return cropped

    def _detect_text_regions(self, image: Image.Image) -> List[Dict]:
        """
        Use AI vision to detect text regions in the image.

        Returns list of regions with approximate bounds.
        """
        prompt = """Analyze this image for any text, labels, watermarks, or annotations.

For each text element found, describe:
1. Location (top/middle/bottom and left/center/right)
2. Approximate percentage from edges (e.g., "top 10%", "bottom 5%")
3. The text content if readable

Output as JSON array:
[{"location": "top", "edge_percent": 10, "text": "EXAMPLE LABEL"}, ...]

If no text is found, output: []"""

        try:
            response = self.analyze_image(image, prompt, task='general')

            # Parse JSON from response
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                import json
                regions = json.loads(json_match.group())
                return regions
        except Exception as e:
            print(f"      Text detection parse error: {e}")

        return []

    def _crop_excluding_text(self, image: Image.Image, text_regions: List[Dict]) -> Image.Image:
        """
        Crop image to exclude detected text regions.
        """
        width, height = image.size

        # Calculate crop bounds based on text locations
        top_crop = 0
        bottom_crop = height
        left_crop = 0
        right_crop = width

        for region in text_regions:
            location = region.get('location', '').lower()
            edge_pct = region.get('edge_percent', 10) / 100.0

            if 'top' in location:
                top_crop = max(top_crop, int(height * edge_pct))
            if 'bottom' in location:
                bottom_crop = min(bottom_crop, int(height * (1 - edge_pct)))
            if 'left' in location:
                left_crop = max(left_crop, int(width * edge_pct))
            if 'right' in location:
                right_crop = min(right_crop, int(width * (1 - edge_pct)))

        # Ensure valid bounds
        if right_crop <= left_crop or bottom_crop <= top_crop:
            # Invalid bounds, use default margin crop
            top_crop = int(height * 0.08)
            bottom_crop = int(height * 0.92)
            left_crop = int(width * 0.02)
            right_crop = int(width * 0.98)

        return image.crop((left_crop, top_crop, right_crop, bottom_crop))

    def batch_img2img(
        self,
        images: List[Image.Image],
        prompt: str,
        **kwargs,
    ) -> List[Image.Image]:
        """
        Apply img2img transformation to a batch of images.

        Args:
            images: List of images to transform
            prompt: Transformation prompt
            **kwargs: Additional arguments for img2img_enhance

        Returns:
            List of transformed images
        """
        results = []
        for img in images:
            try:
                result = self.img2img_enhance(img, prompt, **kwargs)
                results.append(result)
            except Exception as e:
                print(f"Warning: Failed to transform image: {e}")
                results.append(img)  # Keep original on failure
        return results


# =============================================================================
# Abstract Base Generator
# =============================================================================

class AssetGenerator(ABC):
    """Abstract base class for all asset generators."""

    def __init__(
        self,
        platform: PlatformConfig,
        api_key: Optional[str] = None,
    ):
        """Initialize generator with platform config."""
        self.platform = platform
        self.client = PollinationsClient(api_key)
        self.flags = GenerationFlags()

    def set_flags(self, flags: GenerationFlags) -> None:
        """Set generation flags."""
        self.flags = flags

    @abstractmethod
    def generate(self, description: str, **kwargs) -> GeneratedAsset:
        """Generate asset from description. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def optimize(self, asset: GeneratedAsset) -> GeneratedAsset:
        """Optimize asset for platform. Must be implemented by subclasses."""
        pass

    # -------------------------------------------------------------------------
    # Common Utilities
    # -------------------------------------------------------------------------

    def _build_style_prompt(self) -> str:
        """Build platform-specific style prompt."""
        if self.flags.style_override:
            return self.flags.style_override
        return self.platform.prompt_style

    def _get_resampling_filter(self):
        """Get PIL resampling filter for platform."""
        filters = {
            'NEAREST': Image.NEAREST,
            'LANCZOS': Image.LANCZOS,
            'BILINEAR': Image.BILINEAR,
        }
        return filters.get(self.platform.resampling, Image.NEAREST)

    def _resize_image(
        self,
        image: Image.Image,
        size: Tuple[int, int],
    ) -> Image.Image:
        """Resize image using platform-appropriate filter."""
        return image.resize(size, self._get_resampling_filter())

    def _extract_palette_ai(
        self,
        image: Image.Image,
        num_colors: int = 4,
    ) -> List[int]:
        """Use AI to extract optimal palette for image."""

        prompt = f"""Analyze this image for retro game palette optimization.

Platform constraints:
- Maximum {num_colors} colors (including transparent at index 0)
- Need good brightness spread (dark, mid, bright)

Suggest the best {num_colors} NES palette colors.
First color MUST be $0F (black) for transparency.

Available NES colors:
$0F: Black, $00: Dark Gray, $10: Gray, $20/$30: White
$01-$0C: Dark colors (blues, purples, reds, greens, cyans)
$11-$1C: Medium colors
$21-$2C: Bright colors

Return ONLY a JSON object:
{{"palette": ["$0F", "$XX", "$XX", "$XX"], "reason": "brief explanation"}}
"""

        try:
            response = self.client.analyze_image(
                image, prompt, task='palette_extraction'
            )

            # Parse JSON from response
            import re
            json_match = re.search(r'\{[^}]+\}', response)
            if json_match:
                data = json.loads(json_match.group())
                if 'palette' in data:
                    palette = []
                    for color_str in data['palette']:
                        hex_val = color_str.replace('$', '').replace('0x', '')
                        palette.append(int(hex_val, 16))
                    if len(palette) == num_colors:
                        return palette

        except Exception:
            pass

        # Fallback to default synthwave palette
        return [0x0F, 0x24, 0x2C, 0x30][:num_colors]

    def _detect_sprites_ai(
        self,
        image: Image.Image,
        sprite_type: str = "sprite",
    ) -> List[Dict[str, int]]:
        """Use AI to detect sprite locations in image."""

        prompt = f"""Analyze this sprite sheet image. Find all {sprite_type} sprites.

Return a JSON array of bounding boxes:
[{{"x": <left>, "y": <top>, "width": <width>, "height": <height>}}, ...]

Exclude any text labels or empty space.
Find individual sprite frames, not animation strips.
"""

        try:
            response = self.client.analyze_image(
                image, prompt, task='sprite_detection'
            )

            # Parse JSON array from response
            import re
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                data = json.loads(json_match.group())
                return [
                    bbox for bbox in data
                    if all(k in bbox for k in ['x', 'y', 'width', 'height'])
                ]

        except Exception:
            pass

        return []

    def _analyze_animation_ai(
        self,
        frames: List[Image.Image],
        anim_name: str,
    ) -> List[int]:
        """Analyze animation frames to suggest timing."""

        # Default timing based on animation type
        DEFAULT_TIMING = {
            'idle': 150,
            'walk': 100,
            'run': 80,
            'attack': 60,
            'hurt': 100,
            'death': 120,
            'jump': 100,
            'fall': 100,
            'special': 80,
        }

        base_ms = DEFAULT_TIMING.get(anim_name, 100)
        return [base_ms] * len(frames)


# =============================================================================
# Convenience Functions - Using Comprehensive Platform Limits
# =============================================================================

def get_nes_config() -> PlatformConfig:
    """Get NES platform configuration from comprehensive limits."""
    return platform_config_from_limits(NES_LIMITS)


def get_genesis_config() -> PlatformConfig:
    """Get Genesis platform configuration from comprehensive limits."""
    return platform_config_from_limits(GENESIS_LIMITS)


def get_snes_config() -> PlatformConfig:
    """Get SNES platform configuration from comprehensive limits."""
    return platform_config_from_limits(SNES_LIMITS)


def get_gameboy_config() -> PlatformConfig:
    """Get Game Boy platform configuration from comprehensive limits."""
    return platform_config_from_limits(GAMEBOY_LIMITS)


def get_platform_config(platform_name: str) -> PlatformConfig:
    """
    Get platform configuration by name.

    Uses the comprehensive PlatformLimits database for accurate hardware specs.

    Args:
        platform_name: Platform identifier (nes, genesis, snes, gb, gameboy)

    Returns:
        PlatformConfig with full system limits
    """
    limits = get_platform_limits(platform_name)
    return platform_config_from_limits(limits)


# Export platform limit helpers for direct access
__all__ = [
    # Classes
    'GenerationFlags', 'GeneratedAsset', 'PlatformConfig',
    'PollinationsClient', 'AssetGenerator',
    # Config functions
    'get_nes_config', 'get_genesis_config', 'get_snes_config',
    'get_gameboy_config', 'get_platform_config',
    'platform_config_from_limits',
    # Re-export limit functions for convenience
    'get_platform_limits', 'get_recommended_frames', 'supports_chr_animation',
    'get_animation_banks', 'validate_asset_for_platform',
    # Constants
    'MODEL_MAP',
    # Model configuration (from model_config.py)
    'ModelConfig', 'ModelTier', 'get_model_config', 'get_task_models',
    'get_model_for_task', 'get_endpoint_for_model', 'get_img2img_models',
    'get_txt2img_models', 'ECONOMY_CONFIG', 'QUALITY_CONFIG', 'PRECISION_CONFIG',
    # Prompt system (from prompt_system.py)
    'PromptBuilder', 'get_platform_prompt', 'get_available_platforms',
    'get_platform_info', 'PLATFORM_CONSTRAINTS',
    # PixelLab client (from pixellab_client.py)
    'PixelLabClient', 'PixelLabResult', 'create_sprite', 'create_animation',
    'CameraView', 'Direction', 'Outline', 'Shading', 'Detail',
]
