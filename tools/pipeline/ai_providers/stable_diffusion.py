"""
Local Stable Diffusion Generation Provider.

Supports local Stable Diffusion installations via:
- Automatic1111 WebUI API (http://127.0.0.1:7860)
- ComfyUI API (http://127.0.0.1:8188)
- SD.Next API

Benefits:
- No API costs (after hardware)
- Full control over models and settings
- Custom fine-tuned models for pixel art
- Privacy (no data leaves local machine)

Recommended Models for Pixel Art:
- stable-diffusion-xl-base with LoRA for pixel art
- sd-1.5 fine-tuned on sprite datasets
- Custom checkpoints trained on Genesis/NES sprites
"""

import os
import time
import json
import base64
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


class StableDiffusionLocalProvider(GenerationProvider):
    """
    Local Stable Diffusion provider.

    Connects to a local SD WebUI instance (Automatic1111, ComfyUI, etc.)
    for cost-free, fully customizable generation.
    """

    def __init__(self,
                 api_url: str = "http://127.0.0.1:7860",
                 checkpoint: Optional[str] = None,
                 timeout: int = 300,
                 api_type: str = "auto"):
        """
        Initialize local SD provider.

        Args:
            api_url: URL of the local SD API
            checkpoint: Model checkpoint to use (None = current)
            timeout: Request timeout in seconds
            api_type: "auto", "a1111", or "comfyui"
        """
        self._api_url = api_url.rstrip('/')
        self._checkpoint = checkpoint
        self._timeout = timeout
        self._api_type = api_type
        self._is_available = None  # Lazy check

    @property
    def name(self) -> str:
        model = self._checkpoint or "default"
        return f"SD Local ({model})"

    @property
    def capabilities(self) -> ProviderCapability:
        return (
            ProviderCapability.TEXT_TO_IMAGE |
            ProviderCapability.IMAGE_TO_IMAGE |
            ProviderCapability.UPSCALING |
            ProviderCapability.INPAINTING
        )

    @property
    def is_available(self) -> bool:
        if self._is_available is None:
            self._is_available = self._check_availability()
        return self._is_available

    def _check_availability(self) -> bool:
        """Check if local SD is running and accessible."""
        try:
            import urllib.request
            import urllib.error

            # Try to connect to the API
            req = urllib.request.Request(
                f"{self._api_url}/sdapi/v1/sd-models",
                headers={'User-Agent': 'ARDK-Pipeline/1.0'},
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except Exception:
            return False

    def generate(self, prompt: str, config: Optional[GenerationConfig] = None) -> GenerationResult:
        """Generate sprite using local Stable Diffusion."""
        if not self.is_available:
            return GenerationResult(
                success=False,
                errors=["Local Stable Diffusion not available. Start the WebUI first."],
                provider=self.name,
            )

        config = config or GenerationConfig()
        start_time = time.time()

        # Build pixel art optimized prompt
        full_prompt = self._build_pixel_art_prompt(prompt, config)

        # Standard SD parameters
        payload = {
            "prompt": full_prompt,
            "negative_prompt": config.negative_prompt or (
                "blurry, realistic, photo, 3d render, anti-aliasing, "
                "smooth edges, gradient, soft focus"
            ),
            "width": self._round_to_multiple(config.width * 4, 64),  # Generate larger
            "height": self._round_to_multiple(config.height * 4, 64),
            "steps": config.steps or 20,
            "cfg_scale": config.cfg_scale or 7.0,
            "sampler_name": "Euler a",
        }

        if config.seed is not None:
            payload["seed"] = config.seed
        else:
            payload["seed"] = -1  # Random

        # Use specific checkpoint if configured
        if self._checkpoint:
            payload["override_settings"] = {
                "sd_model_checkpoint": self._checkpoint
            }

        try:
            result = self._call_api("/sdapi/v1/txt2img", payload)

            if not result or "images" not in result:
                return GenerationResult(
                    success=False,
                    errors=["No images in response"],
                    provider=self.name,
                    raw_response=result,
                )

            # Decode first image
            img_data = base64.b64decode(result["images"][0])
            img = Image.open(BytesIO(img_data))

            # Downscale to target size with nearest neighbor
            if img.size != (config.width, config.height):
                img = img.resize((config.width, config.height), Image.NEAREST)

            generation_time = int((time.time() - start_time) * 1000)

            # Extract seed from info
            info = json.loads(result.get("info", "{}"))
            seed_used = info.get("seed")

            return GenerationResult(
                success=True,
                image=img,
                provider=self.name,
                model=self._checkpoint or "unknown",
                seed_used=seed_used,
                generation_time_ms=generation_time,
                raw_response=result,
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
        """Transform existing image using img2img."""
        if not self.is_available:
            return GenerationResult(
                success=False,
                errors=["Local SD not available"],
                provider=self.name,
            )

        config = config or GenerationConfig()
        start_time = time.time()

        full_prompt = self._build_pixel_art_prompt(prompt, config)

        # Encode source image
        buffer = BytesIO()
        source.save(buffer, format='PNG')
        source_b64 = base64.b64encode(buffer.getvalue()).decode()

        payload = {
            "init_images": [source_b64],
            "prompt": full_prompt,
            "negative_prompt": config.negative_prompt or "blurry, realistic",
            "width": source.size[0],
            "height": source.size[1],
            "steps": config.steps or 20,
            "cfg_scale": config.cfg_scale or 7.0,
            "denoising_strength": strength,
            "sampler_name": "Euler a",
        }

        if config.seed is not None:
            payload["seed"] = config.seed

        try:
            result = self._call_api("/sdapi/v1/img2img", payload)

            if not result or "images" not in result:
                return GenerationResult(
                    success=False,
                    errors=["No images in response"],
                    provider=self.name,
                )

            img_data = base64.b64decode(result["images"][0])
            img = Image.open(BytesIO(img_data))

            generation_time = int((time.time() - start_time) * 1000)

            return GenerationResult(
                success=True,
                image=img,
                provider=self.name,
                model=self._checkpoint or "unknown",
                generation_time_ms=generation_time,
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
        """Upscale using SD upscaler."""
        if not self.is_available:
            return GenerationResult(
                success=False,
                errors=["Local SD not available"],
                provider=self.name,
            )

        start_time = time.time()

        buffer = BytesIO()
        source.save(buffer, format='PNG')
        source_b64 = base64.b64encode(buffer.getvalue()).decode()

        payload = {
            "image": source_b64,
            "upscaler_1": "R-ESRGAN 4x+",  # Common upscaler
            "upscaling_resize": scale,
        }

        try:
            result = self._call_api("/sdapi/v1/extra-single-image", payload)

            if not result or "image" not in result:
                # Fallback: use basic nearest-neighbor upscale
                upscaled = source.resize(
                    (source.width * scale, source.height * scale),
                    Image.NEAREST
                )
                return GenerationResult(
                    success=True,
                    image=upscaled,
                    provider=self.name,
                    model="nearest-neighbor",
                    warnings=["SD upscaler failed, used nearest-neighbor"],
                )

            img_data = base64.b64decode(result["image"])
            img = Image.open(BytesIO(img_data))

            generation_time = int((time.time() - start_time) * 1000)

            return GenerationResult(
                success=True,
                image=img,
                provider=self.name,
                model="R-ESRGAN 4x+",
                generation_time_ms=generation_time,
            )

        except Exception as e:
            # Fallback to basic upscale
            upscaled = source.resize(
                (source.width * scale, source.height * scale),
                Image.NEAREST
            )
            return GenerationResult(
                success=True,
                image=upscaled,
                provider=self.name,
                warnings=[f"SD upscaler error ({e}), used nearest-neighbor"],
            )

    def _call_api(self, endpoint: str, payload: dict) -> Optional[dict]:
        """Make API call to local SD."""
        import urllib.request
        import urllib.error

        url = f"{self._api_url}{endpoint}"
        data = json.dumps(payload).encode('utf-8')

        req = urllib.request.Request(
            url,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'ARDK-Pipeline/1.0',
            },
            method='POST',
        )

        with urllib.request.urlopen(req, timeout=self._timeout) as response:
            return json.loads(response.read().decode('utf-8'))

    def _round_to_multiple(self, value: int, multiple: int) -> int:
        """Round up to nearest multiple (SD requires certain dimensions)."""
        return ((value + multiple - 1) // multiple) * multiple

    def get_available_models(self) -> List[str]:
        """Get list of available SD models/checkpoints."""
        if not self.is_available:
            return []

        try:
            import urllib.request

            req = urllib.request.Request(
                f"{self._api_url}/sdapi/v1/sd-models",
                headers={'User-Agent': 'ARDK-Pipeline/1.0'},
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                models = json.loads(response.read().decode('utf-8'))
                return [m.get('model_name', m.get('title', '')) for m in models]
        except Exception:
            return []

    def get_available_samplers(self) -> List[str]:
        """Get list of available samplers."""
        if not self.is_available:
            return []

        try:
            import urllib.request

            req = urllib.request.Request(
                f"{self._api_url}/sdapi/v1/samplers",
                headers={'User-Agent': 'ARDK-Pipeline/1.0'},
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                samplers = json.loads(response.read().decode('utf-8'))
                return [s.get('name', '') for s in samplers]
        except Exception:
            return []

    def set_checkpoint(self, checkpoint: str):
        """Change the active checkpoint/model."""
        if not self.is_available:
            return

        try:
            import urllib.request

            payload = {"sd_model_checkpoint": checkpoint}
            data = json.dumps(payload).encode('utf-8')

            req = urllib.request.Request(
                f"{self._api_url}/sdapi/v1/options",
                data=data,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'ARDK-Pipeline/1.0',
                },
                method='POST',
            )
            urllib.request.urlopen(req, timeout=60)
            self._checkpoint = checkpoint
        except Exception as e:
            print(f"Failed to set checkpoint: {e}")

    def estimate_cost(self, config: GenerationConfig) -> float:
        """Local SD is free (electricity cost not calculated)."""
        return 0.0
