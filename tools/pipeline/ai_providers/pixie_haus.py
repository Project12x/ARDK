"""
Pixie.haus Generation Provider.

Pixie.haus is specialized for pixel-perfect sprite generation with:
- Built-in color palette quantization
- Nearest-neighbor scaling
- Platform-specific presets (NES, Genesis, SNES, GB)
- Background removal tailored for games

API Documentation: https://api.pixie.haus/docs
"""

import os
import time
import json
from io import BytesIO
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from PIL import Image

from .base import (
    GenerationProvider,
    GenerationResult,
    GenerationConfig,
    ProviderCapability,
)


class PixieHausProvider(GenerationProvider):
    """
    Pixie.haus generation provider.

    Specialized for pixel-perfect sprite generation with platform
    awareness and built-in quantization.
    """

    BASE_URL = "https://api.pixie.haus/v1"

    # Platform presets mapping to Pixie.haus palette modes
    PLATFORM_PALETTES = {
        "genesis": "genesis",
        "nes": "nes",
        "snes": "snes",
        "gameboy": "gameboy",
        "gameboy_color": "gbc",
    }

    def __init__(self, api_key: Optional[str] = None, timeout: int = 120):
        """
        Initialize Pixie.haus provider.

        Args:
            api_key: API key (required, from env PIXIE_HAUS_API_KEY)
            timeout: Request timeout in seconds
        """
        self._api_key = api_key or os.getenv('PIXIE_HAUS_API_KEY')
        self._timeout = timeout
        self._client = None

        if self._api_key:
            try:
                import httpx
                self._client = httpx.Client(
                    base_url=self.BASE_URL,
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    timeout=timeout,
                )
            except ImportError:
                pass  # httpx not installed

    @property
    def name(self) -> str:
        return "Pixie.haus"

    @property
    def capabilities(self) -> ProviderCapability:
        return (
            ProviderCapability.TEXT_TO_IMAGE |
            ProviderCapability.IMAGE_TO_IMAGE |
            ProviderCapability.UPSCALING |
            ProviderCapability.PALETTE_CONSTRAINT |
            ProviderCapability.PIXEL_PERFECT |
            ProviderCapability.ANIMATION |
            ProviderCapability.MULTI_VIEW
        )

    @property
    def is_available(self) -> bool:
        return bool(self._api_key and self._client)

    def generate(self, prompt: str, config: Optional[GenerationConfig] = None) -> GenerationResult:
        """Generate a pixel-perfect sprite."""
        if not self.is_available:
            return GenerationResult(
                success=False,
                errors=["Pixie.haus not configured (missing API key or httpx)"],
                provider=self.name,
            )

        config = config or GenerationConfig()
        start_time = time.time()

        # Build request payload
        payload = {
            "prompt": prompt,
            "width": config.width,
            "height": config.height,
            "pixel_perfect": True,
            "max_colors": config.max_colors,
        }

        # Add palette mode if platform is known
        if config.platform in self.PLATFORM_PALETTES:
            payload["palette_mode"] = self.PLATFORM_PALETTES[config.platform]

        # Add explicit palette if provided
        if config.palette:
            payload["palette"] = [
                f"#{r:02X}{g:02X}{b:02X}"
                for r, g, b in config.palette
            ]

        if config.seed is not None:
            payload["seed"] = config.seed

        # Add style reference if provided
        if config.style_reference:
            style_b64 = self._image_to_base64(config.style_reference)
            if style_b64:
                payload["style_image"] = style_b64

        try:
            response = self._client.post("/generate", json=payload)
            response.raise_for_status()

            # Parse response
            data = response.json()
            image_data = data.get("image")

            if not image_data:
                return GenerationResult(
                    success=False,
                    errors=["No image in response"],
                    provider=self.name,
                    raw_response=data,
                )

            # Decode image
            import base64
            img_bytes = base64.b64decode(image_data)
            img = Image.open(BytesIO(img_bytes))

            generation_time = int((time.time() - start_time) * 1000)

            return GenerationResult(
                success=True,
                image=img,
                provider=self.name,
                model="pixie-sprite",
                seed_used=data.get("seed"),
                generation_time_ms=generation_time,
                cost_usd=data.get("cost", 0.0),
                raw_response=data,
            )

        except Exception as e:
            error_msg = str(e)
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                error_msg = e.response.text
            return GenerationResult(
                success=False,
                errors=[error_msg],
                provider=self.name,
            )

    def _generate_from_image_impl(self,
                                  source: Image.Image,
                                  prompt: str,
                                  config: Optional[GenerationConfig],
                                  strength: float) -> GenerationResult:
        """Transform an existing image."""
        if not self.is_available:
            return GenerationResult(
                success=False,
                errors=["Pixie.haus not configured"],
                provider=self.name,
            )

        config = config or GenerationConfig()
        start_time = time.time()

        payload = {
            "prompt": prompt,
            "image": self._image_to_base64(source),
            "strength": strength,
            "width": config.width or source.size[0],
            "height": config.height or source.size[1],
            "pixel_perfect": True,
            "max_colors": config.max_colors,
        }

        if config.platform in self.PLATFORM_PALETTES:
            payload["palette_mode"] = self.PLATFORM_PALETTES[config.platform]

        if config.palette:
            payload["palette"] = [f"#{r:02X}{g:02X}{b:02X}" for r, g, b in config.palette]

        try:
            response = self._client.post("/img2img", json=payload)
            response.raise_for_status()

            data = response.json()
            image_data = data.get("image")

            if not image_data:
                return GenerationResult(
                    success=False,
                    errors=["No image in response"],
                    provider=self.name,
                )

            import base64
            img_bytes = base64.b64decode(image_data)
            img = Image.open(BytesIO(img_bytes))

            generation_time = int((time.time() - start_time) * 1000)

            return GenerationResult(
                success=True,
                image=img,
                provider=self.name,
                model="pixie-img2img",
                generation_time_ms=generation_time,
                cost_usd=data.get("cost", 0.0),
            )

        except Exception as e:
            return GenerationResult(
                success=False,
                errors=[str(e)],
                provider=self.name,
            )

    def _generate_animation_impl(self,
                                 source: Image.Image,
                                 action: str,
                                 config: Optional[GenerationConfig]) -> GenerationResult:
        """Generate animation frames from a single sprite."""
        if not self.is_available:
            return GenerationResult(
                success=False,
                errors=["Pixie.haus not configured"],
                provider=self.name,
            )

        config = config or GenerationConfig()
        start_time = time.time()

        # Pixie.haus animate endpoint
        payload = {
            "image": self._image_to_base64(source),
            "action": action,
            "frames": config.animation_frames or 4,
            "pixel_perfect": True,
        }

        if config.platform in self.PLATFORM_PALETTES:
            payload["palette_mode"] = self.PLATFORM_PALETTES[config.platform]

        try:
            response = self._client.post("/animate", json=payload)
            response.raise_for_status()

            data = response.json()
            frames_data = data.get("frames", [])

            if not frames_data:
                return GenerationResult(
                    success=False,
                    errors=["No frames in response"],
                    provider=self.name,
                )

            import base64
            frames = []
            for frame_b64 in frames_data:
                img_bytes = base64.b64decode(frame_b64)
                frames.append(Image.open(BytesIO(img_bytes)))

            generation_time = int((time.time() - start_time) * 1000)

            return GenerationResult(
                success=True,
                image=frames[0] if frames else None,
                frames=frames,
                frame_durations=data.get("durations", [100] * len(frames)),
                provider=self.name,
                model="pixie-animate",
                generation_time_ms=generation_time,
                cost_usd=data.get("cost", 0.0),
            )

        except Exception as e:
            return GenerationResult(
                success=False,
                errors=[str(e)],
                provider=self.name,
            )

    def _generate_views_impl(self,
                            source: Image.Image,
                            views: List[str],
                            config: Optional[GenerationConfig]) -> GenerationResult:
        """Generate multiple view angles from a single sprite."""
        if not self.is_available:
            return GenerationResult(
                success=False,
                errors=["Pixie.haus not configured"],
                provider=self.name,
            )

        config = config or GenerationConfig()
        start_time = time.time()

        # Pixie.haus rotate endpoint
        payload = {
            "image": self._image_to_base64(source),
            "views": views,
            "pixel_perfect": True,
        }

        if config.platform in self.PLATFORM_PALETTES:
            payload["palette_mode"] = self.PLATFORM_PALETTES[config.platform]

        try:
            response = self._client.post("/rotate", json=payload)
            response.raise_for_status()

            data = response.json()
            views_data = data.get("views", {})

            if not views_data:
                return GenerationResult(
                    success=False,
                    errors=["No views in response"],
                    provider=self.name,
                )

            import base64
            result_views = {}
            for view_name, view_b64 in views_data.items():
                img_bytes = base64.b64decode(view_b64)
                result_views[view_name] = Image.open(BytesIO(img_bytes))

            generation_time = int((time.time() - start_time) * 1000)

            return GenerationResult(
                success=True,
                image=list(result_views.values())[0] if result_views else None,
                views=result_views,
                provider=self.name,
                model="pixie-rotate",
                generation_time_ms=generation_time,
                cost_usd=data.get("cost", 0.0),
            )

        except Exception as e:
            return GenerationResult(
                success=False,
                errors=[str(e)],
                provider=self.name,
            )

    def _upscale_impl(self,
                     source: Image.Image,
                     scale: int,
                     config: Optional[GenerationConfig]) -> GenerationResult:
        """Upscale image while preserving pixel art style."""
        if not self.is_available:
            return GenerationResult(
                success=False,
                errors=["Pixie.haus not configured"],
                provider=self.name,
            )

        config = config or GenerationConfig()
        start_time = time.time()

        payload = {
            "image": self._image_to_base64(source),
            "scale": scale,
            "preserve_palette": True,
        }

        try:
            response = self._client.post("/upscale", json=payload)
            response.raise_for_status()

            data = response.json()
            image_data = data.get("image")

            if not image_data:
                return GenerationResult(
                    success=False,
                    errors=["No image in response"],
                    provider=self.name,
                )

            import base64
            img_bytes = base64.b64decode(image_data)
            img = Image.open(BytesIO(img_bytes))

            generation_time = int((time.time() - start_time) * 1000)

            return GenerationResult(
                success=True,
                image=img,
                provider=self.name,
                model="pixie-upscale",
                generation_time_ms=generation_time,
                cost_usd=data.get("cost", 0.0),
            )

        except Exception as e:
            return GenerationResult(
                success=False,
                errors=[str(e)],
                provider=self.name,
            )

    def _image_to_base64(self, img) -> Optional[str]:
        """Convert image to base64 string."""
        import base64

        if isinstance(img, (str, Path)):
            with open(img, 'rb') as f:
                return base64.b64encode(f.read()).decode()
        elif isinstance(img, Image.Image):
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            return base64.b64encode(buffer.getvalue()).decode()
        return None

    def estimate_cost(self, config: GenerationConfig) -> float:
        """Estimate cost for generation (Pixie.haus pricing)."""
        # Base cost per generation
        base_cost = 0.01

        # Animation costs more
        if config.animation_frames > 1:
            base_cost *= config.animation_frames * 0.5

        # Multi-view costs more
        if config.views > 1:
            base_cost *= config.views * 0.5

        return base_cost
