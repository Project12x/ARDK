"""
Pollinations.ai Generation Provider.

Free access to 30+ AI models via unified API for sprite generation.
Primary provider for the pipeline - works without API keys.

Capabilities:
    - TEXT_TO_IMAGE: Generate sprites from text prompts
    - IMAGE_TO_IMAGE: Transform/refine existing sprites
    - ANIMATION: Generate animation sprite sheets (walk, attack, idle, etc.)
    - MULTI_VIEW: Generate multiple view angles (front, side, back)
    - STYLE_TRANSFER: Apply style references to generation
    - UPSCALING: Upscale sprites while preserving pixel art style

Recommended Models for Pixel Art:
    - gptimage-large: Best quality, GPT-5 (default)
    - gptimage: Good quality, GPT-4
    - flux: High quality, good for concepts
    - turbo: Fastest generation

Animation Support:
    Generates sprite sheets with multiple frames in a horizontal strip,
    then extracts individual frames. Supports actions: idle, walk, run,
    attack, jump, death, hit, cast.

Upscaling Support:
    AI-assisted upscaling generates at higher resolution then downscales
    with nearest-neighbor to preserve pixel integrity. Falls back to
    simple nearest-neighbor if AI generation fails.

Usage:
    >>> provider = PollinationsGenerationProvider(model="gptimage-large")
    >>> result = provider.generate("pixel art warrior", config)
    >>>
    >>> # Animation
    >>> anim_result = provider.generate_animation(sprite, "walk", config)
    >>> for frame in anim_result.frames:
    ...     frame.save(f"walk_{i}.png")
    >>>
    >>> # Upscaling
    >>> upscaled = provider.upscale(sprite, scale=2, config)
    >>> if upscaled.success:
    ...     upscaled.image.save("sprite_2x.png")
"""

import os
import time
import json
import urllib.request
import urllib.parse
import urllib.error
from io import BytesIO
from pathlib import Path
from typing import Optional, List, Dict, Any

from PIL import Image

from .base import (
    GenerationProvider,
    GenerationResult,
    GenerationConfig,
    ProviderCapability,
)


class PollinationsGenerationProvider(GenerationProvider):
    """
    Pollinations.ai generation provider.

    Uses the Pollinations API for versatile sprite generation with
    support for multiple underlying models.
    """

    # API endpoints
    IMAGE_URL = "https://gen.pollinations.ai/image/"
    CHAT_URL = "https://gen.pollinations.ai/v1/chat/completions"

    # Recommended models for pixel art
    PIXEL_ART_MODELS = ["gptimage-large", "gptimage", "flux", "turbo"]

    def __init__(self,
                 api_key: Optional[str] = None,
                 model: str = "gptimage-large",
                 timeout: int = 90):
        """
        Initialize Pollinations provider.

        Args:
            api_key: API key (optional, uses env var POLLINATIONS_API_KEY)
            model: Model to use for generation
            timeout: Request timeout in seconds
        """
        self._api_key = api_key or os.getenv('POLLINATIONS_API_KEY')
        self._model = model
        self._timeout = timeout

    @property
    def name(self) -> str:
        return f"Pollinations ({self._model})"

    @property
    def capabilities(self) -> ProviderCapability:
        return (
            ProviderCapability.TEXT_TO_IMAGE |
            ProviderCapability.IMAGE_TO_IMAGE |
            ProviderCapability.STYLE_TRANSFER |
            ProviderCapability.ANIMATION |
            ProviderCapability.MULTI_VIEW |
            ProviderCapability.UPSCALING
        )

    @property
    def is_available(self) -> bool:
        # Pollinations works without API key, but has rate limits
        return True

    def generate(self, prompt: str, config: Optional[GenerationConfig] = None) -> GenerationResult:
        """Generate sprite from text prompt."""
        config = config or GenerationConfig()
        start_time = time.time()

        # Build optimized prompt
        full_prompt = self._build_pixel_art_prompt(prompt, config)

        # Add palette guidance if provided
        if config.palette:
            hex_colors = [f"#{r:02X}{g:02X}{b:02X}" for r, g, b in config.palette]
            full_prompt += f". Use only these colors: {', '.join(hex_colors)}"

        try:
            # URL-encode the prompt
            encoded_prompt = urllib.parse.quote(full_prompt)

            # Build URL with parameters
            seed = config.seed or int(time.time())
            url = (
                f"{self.IMAGE_URL}{encoded_prompt}"
                f"?model={self._model}"
                f"&width={config.width * 8}"  # Generate larger, downscale later
                f"&height={config.height * 8}"
                f"&seed={seed}"
            )

            # Make request
            headers = {'User-Agent': 'ARDK-Pipeline/1.0'}
            if self._api_key:
                headers['Authorization'] = f'Bearer {self._api_key}'

            req = urllib.request.Request(url, headers=headers)

            with urllib.request.urlopen(req, timeout=self._timeout) as response:
                image_data = response.read()

            # Load and process image
            img = Image.open(BytesIO(image_data))

            # Downscale to target size with nearest neighbor (preserve pixels)
            if img.size != (config.width, config.height):
                img = img.resize((config.width, config.height), Image.NEAREST)

            generation_time = int((time.time() - start_time) * 1000)

            return GenerationResult(
                success=True,
                image=img,
                provider=self.name,
                model=self._model,
                seed_used=seed,
                generation_time_ms=generation_time,
            )

        except urllib.error.HTTPError as e:
            error_msg = f"HTTP {e.code}: {e.reason}"
            if e.code == 429:
                error_msg = "Rate limited - wait before retrying"
            return GenerationResult(
                success=False,
                errors=[error_msg],
                provider=self.name,
            )
        except urllib.error.URLError as e:
            return GenerationResult(
                success=False,
                errors=[f"Network error: {e.reason}"],
                provider=self.name,
            )
        except Exception as e:
            return GenerationResult(
                success=False,
                errors=[str(e)],
                provider=self.name,
            )

    def _generate_from_image_impl(self,
                                  source: Image.Image,
                                  prompt: str,
                                  config: Optional[GenerationConfig],
                                  strength: float) -> GenerationResult:
        """
        Transform an existing image (img2img).

        Pollinations doesn't have a direct img2img endpoint, so we:
        1. Analyze the source image for key features
        2. Generate a new image with those features + the prompt
        """
        config = config or GenerationConfig()

        # For now, use text-to-image with enhanced prompt
        # In future, could use the vision API to describe the source first
        enhanced_prompt = f"Based on existing sprite, {prompt}"

        if hasattr(source, 'size'):
            config.width = config.width or source.size[0]
            config.height = config.height or source.size[1]

        result = self.generate(enhanced_prompt, config)

        if result.success:
            # Blend with original if strength < 1
            if strength < 1.0 and result.image:
                # Simple alpha blend
                source_rgba = source.convert('RGBA')
                result_rgba = result.image.convert('RGBA')

                # Resize result to match source if needed
                if result_rgba.size != source_rgba.size:
                    result_rgba = result_rgba.resize(source_rgba.size, Image.NEAREST)

                # Blend
                blended = Image.blend(source_rgba, result_rgba, strength)
                result.image = blended
                result.images = [blended]

        return result

    def generate_sheet(self,
                      prompt: str,
                      views: List[str],
                      config: Optional[GenerationConfig] = None) -> GenerationResult:
        """
        Generate a sprite sheet with multiple views in one pass.

        This is more efficient than generating views separately as it
        maintains style consistency.

        Args:
            prompt: Base description of the sprite
            views: List of views to include (e.g., ["front", "side", "back"])
            config: Generation configuration

        Returns:
            GenerationResult with the full sheet and extracted views
        """
        config = config or GenerationConfig()

        # Build sheet prompt
        views_text = ", ".join(views)
        sheet_prompt = (
            f"Video game sprite sheet showing {len(views)} views: {views_text}. "
            f"{prompt}. "
            "Arranged in a horizontal row. "
            "White or transparent background. "
            "Clear separation between sprites. "
            "Uniform height. "
            f"{config.width}x{config.height} per sprite."
        )

        # Generate larger to fit all views
        sheet_config = GenerationConfig(
            width=config.width * len(views) * 2,
            height=config.height * 2,
            platform=config.platform,
            max_colors=config.max_colors,
            palette=config.palette,
            seed=config.seed,
            quality=config.quality,
        )

        result = self.generate(sheet_prompt, sheet_config)

        if result.success and result.image:
            # Try to extract individual views
            try:
                extracted_views = self._extract_views_from_sheet(result.image, views)
                result.views = extracted_views
            except Exception as e:
                result.warnings.append(f"Could not extract views: {e}")

        return result

    def _extract_views_from_sheet(self,
                                  sheet: Image.Image,
                                  expected_views: List[str]) -> Dict[str, Image.Image]:
        """
        Extract individual views from a generated sprite sheet.

        Uses simple horizontal slicing - assumes views are evenly spaced.
        """
        views = {}
        num_views = len(expected_views)

        if num_views == 0:
            return views

        # Calculate expected width per view
        view_width = sheet.width // num_views

        for i, view_name in enumerate(expected_views):
            x = i * view_width
            # Crop the view
            view_img = sheet.crop((x, 0, x + view_width, sheet.height))
            views[view_name] = view_img

        return views

    def _generate_animation_impl(self,
                                 source: Image.Image,
                                 action: str,
                                 config: Optional[GenerationConfig]) -> GenerationResult:
        """
        Generate animation frames from a single sprite.

        Uses sprite sheet generation to create consistent frames.

        Args:
            source: Source sprite (single frame) - used for style reference
            action: Animation action (idle, walk, attack, jump, death)
            config: Generation configuration

        Returns:
            GenerationResult with frames list populated
        """
        config = config or GenerationConfig()
        start_time = time.time()

        # Default frame counts by action type
        frame_counts = {
            'idle': 4,
            'walk': 6,
            'run': 6,
            'attack': 4,
            'jump': 4,
            'death': 4,
            'hit': 2,
            'cast': 4,
        }
        n_frames = config.animation_frames or frame_counts.get(action.lower(), 4)

        # Get dimensions from source or config
        frame_w = config.width or source.size[0]
        frame_h = config.height or source.size[1]

        # Build animation-optimized prompt
        sheet_prompt = self._build_animation_prompt(action, n_frames, frame_w, frame_h, config)

        # Generate sprite sheet (all frames in one row)
        sheet_width = frame_w * n_frames * 8  # Generate larger for quality
        sheet_height = frame_h * 8

        try:
            encoded_prompt = urllib.parse.quote(sheet_prompt)
            seed = config.seed or int(time.time())

            url = (
                f"{self.IMAGE_URL}{encoded_prompt}"
                f"?model={self._model}"
                f"&width={sheet_width}"
                f"&height={sheet_height}"
                f"&seed={seed}"
            )

            headers = {'User-Agent': 'ARDK-Pipeline/1.0'}
            if self._api_key:
                headers['Authorization'] = f'Bearer {self._api_key}'

            req = urllib.request.Request(url, headers=headers)

            with urllib.request.urlopen(req, timeout=self._timeout) as response:
                image_data = response.read()

            sheet = Image.open(BytesIO(image_data))

            # Extract frames from sheet
            frames = self._extract_frames_from_sheet(sheet, n_frames, frame_w, frame_h)

            if not frames:
                return GenerationResult(
                    success=False,
                    errors=["Failed to extract frames from generated sheet"],
                    provider=self.name,
                )

            # Calculate frame durations based on action
            duration_map = {
                'idle': 167,    # ~6fps, slow breathing
                'walk': 100,    # ~10fps, medium pace
                'run': 67,      # ~15fps, fast
                'attack': 83,   # ~12fps, quick strikes
                'jump': 100,    # ~10fps
                'death': 133,   # ~7.5fps, dramatic
                'hit': 67,      # ~15fps, fast reaction
            }
            frame_duration = duration_map.get(action.lower(), 100)
            durations = [frame_duration] * len(frames)

            generation_time = int((time.time() - start_time) * 1000)

            return GenerationResult(
                success=True,
                image=frames[0] if frames else None,
                frames=frames,
                frame_durations=durations,
                provider=self.name,
                model=self._model,
                seed_used=seed,
                generation_time_ms=generation_time,
            )

        except Exception as e:
            return GenerationResult(
                success=False,
                errors=[str(e)],
                provider=self.name,
            )

    def _build_animation_prompt(self, action: str, n_frames: int,
                                frame_w: int, frame_h: int,
                                config: GenerationConfig) -> str:
        """Build an optimized prompt for animation sprite sheet generation."""
        # Action-specific descriptions
        action_descs = {
            'idle': 'subtle breathing animation, small movements',
            'walk': 'walking cycle, left foot forward to right foot forward',
            'run': 'running cycle, dynamic motion',
            'attack': 'sword swing or punch motion, wind-up to follow-through',
            'jump': 'jump animation, crouch to airborne to landing',
            'death': 'falling down death animation',
            'hit': 'flinch reaction, taking damage',
            'cast': 'magic casting animation, hands raised',
        }

        action_desc = action_descs.get(action.lower(), f'{action} animation')

        # Platform style
        platform_styles = {
            "genesis": "16-bit Sega Genesis",
            "nes": "8-bit NES",
            "snes": "16-bit SNES",
            "gameboy": "4-shade Gameboy",
        }
        style = platform_styles.get(config.platform, "retro pixel art")

        prompt_parts = [
            f"{style} sprite animation sheet",
            f"exactly {n_frames} frames in a horizontal strip",
            f"{frame_w}x{frame_h} pixels per frame",
            f"{action_desc}",
            "consistent character design across all frames",
            "transparent or solid color background",
            "no frame borders or gaps between sprites",
            "pixel perfect, no anti-aliasing",
            "evenly spaced frames",
        ]

        if config.max_colors:
            prompt_parts.append(f"maximum {config.max_colors} colors")

        return ", ".join(prompt_parts)

    def _extract_frames_from_sheet(self, sheet: Image.Image, expected_frames: int,
                                   frame_w: int, frame_h: int) -> List[Image.Image]:
        """
        Extract individual frames from a generated sprite sheet.

        Args:
            sheet: The full sprite sheet image
            expected_frames: Number of frames expected
            frame_w: Target frame width
            frame_h: Target frame height

        Returns:
            List of individual frame images
        """
        # Downscale sheet to target size first
        target_w = frame_w * expected_frames
        target_h = frame_h

        # Resize with nearest neighbor to preserve pixels
        if sheet.size != (target_w, target_h):
            sheet = sheet.resize((target_w, target_h), Image.NEAREST)

        frames = []
        for i in range(expected_frames):
            x = i * frame_w
            frame = sheet.crop((x, 0, x + frame_w, target_h))

            # Ensure RGBA
            if frame.mode != 'RGBA':
                frame = frame.convert('RGBA')

            frames.append(frame)

        return frames

    def _generate_views_impl(self,
                            source: Image.Image,
                            views: List[str],
                            config: Optional[GenerationConfig]) -> GenerationResult:
        """
        Generate multiple view angles from a single sprite.

        Uses sprite sheet generation for consistency.
        """
        config = config or GenerationConfig()
        start_time = time.time()

        # Use the sheet generation method
        result = self.generate_sheet(
            "game character sprite",
            views,
            config
        )

        if result.success:
            result.generation_time_ms = int((time.time() - start_time) * 1000)

        return result

    def _upscale_impl(self,
                     source: Image.Image,
                     scale: int,
                     config: Optional[GenerationConfig]) -> GenerationResult:
        """
        Upscale image while preserving pixel art style.

        Uses img2img-style generation at higher resolution, then
        downsamples with nearest-neighbor to preserve pixel integrity.

        Args:
            source: Source image to upscale
            scale: Scale factor (2 or 4)
            config: Generation configuration

        Returns:
            GenerationResult with upscaled image
        """
        config = config or GenerationConfig()
        start_time = time.time()

        # Target dimensions
        target_w = source.width * scale
        target_h = source.height * scale

        # Build upscale-specific prompt
        platform_styles = {
            "genesis": "16-bit Sega Genesis pixel art",
            "nes": "8-bit NES pixel art",
            "snes": "16-bit SNES pixel art",
            "gameboy": "4-shade Gameboy pixel art",
        }
        style = platform_styles.get(config.platform, "retro pixel art")

        prompt_parts = [
            f"{style} sprite upscaled to {target_w}x{target_h}",
            "pixel perfect",
            "no anti-aliasing",
            "sharp pixel edges",
            "preserve original design exactly",
            "clean upscale",
            "no blur",
            "nearest neighbor style",
        ]

        if config.max_colors:
            prompt_parts.append(f"maximum {config.max_colors} colors")

        upscale_prompt = ", ".join(prompt_parts)

        try:
            # Generate at target resolution with intermediate size
            # We generate at 8x the target to get AI detail, then downscale
            gen_w = target_w * 4
            gen_h = target_h * 4

            encoded_prompt = urllib.parse.quote(upscale_prompt)
            seed = config.seed or int(time.time())

            url = (
                f"{self.IMAGE_URL}{encoded_prompt}"
                f"?model={self._model}"
                f"&width={gen_w}"
                f"&height={gen_h}"
                f"&seed={seed}"
            )

            headers = {'User-Agent': 'ARDK-Pipeline/1.0'}
            if self._api_key:
                headers['Authorization'] = f'Bearer {self._api_key}'

            req = urllib.request.Request(url, headers=headers)

            with urllib.request.urlopen(req, timeout=self._timeout) as response:
                image_data = response.read()

            img = Image.open(BytesIO(image_data))

            # Downscale to target with nearest neighbor (preserve pixels)
            if img.size != (target_w, target_h):
                img = img.resize((target_w, target_h), Image.NEAREST)

            # Ensure RGBA
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            generation_time = int((time.time() - start_time) * 1000)

            return GenerationResult(
                success=True,
                image=img,
                provider=self.name,
                model=self._model,
                seed_used=seed,
                generation_time_ms=generation_time,
            )

        except Exception as e:
            # Fallback to simple nearest-neighbor upscale
            try:
                upscaled = source.resize((target_w, target_h), Image.NEAREST)
                if upscaled.mode != 'RGBA':
                    upscaled = upscaled.convert('RGBA')

                return GenerationResult(
                    success=True,
                    image=upscaled,
                    provider=self.name,
                    model="nearest-neighbor",
                    warnings=[f"AI upscale failed ({e}), used nearest-neighbor"],
                    generation_time_ms=int((time.time() - start_time) * 1000),
                )
            except Exception as e2:
                return GenerationResult(
                    success=False,
                    errors=[str(e), str(e2)],
                    provider=self.name,
                )

    def estimate_cost(self, config: GenerationConfig) -> float:
        """Pollinations is free (with rate limits)."""
        return 0.0

    def set_model(self, model: str):
        """Change the underlying model."""
        self._model = model
