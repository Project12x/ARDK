"""
PixelLab API Client - Professional Pixel Art Generation.

PixelLab is purpose-built for pixel art game assets with:
- Exact dimension control (16-400px)
- Outline, shading, detail style controls
- View/direction for multi-directional sprites
- Skeleton-based animation
- Text-driven animation (v1 and v2)
- Rotation between views
- 8-direction sprite generation (v2)
- Intelligent pixel art resizing (v2)
- Tileset generation (v2)
- Inpainting for edits
- Color palette enforcement

API Reference:
- v1: https://api.pixellab.ai/v1/docs
- v2: https://api.pixellab.ai/v2/llms.txt

Usage:
    from asset_generators.pixellab_client import PixelLabClient

    client = PixelLabClient()

    # Generate a sprite (v2)
    sprite = client.generate_image_v2(
        description="robot enemy with red eyes",
        width=64, height=64,
    )

    # Generate 8-directional sprites (v2)
    sprites = client.generate_8_rotations(reference_image, width=32, height=32)

    # Intelligently resize pixel art (v2)
    resized = client.resize(large_sprite, target_width=32, target_height=32)

    # Generate tileset (v2)
    tileset = client.create_tileset(description="grass terrain", tile_size=16)

    # Animate a character (v2)
    frames = client.animate_with_text_v2(
        description="robot character",
        action="walk",
        reference_image=sprite,
        n_frames=4,
    )
"""

import json
import base64
import urllib.request
import urllib.error
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union
from io import BytesIO
from pathlib import Path
from enum import Enum
import os

try:
    from PIL import Image
except ImportError:
    raise ImportError("PIL required: pip install pillow")

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from configs.api_keys import PIXELLAB_API_KEY

# Configure logging
logger = logging.getLogger('PixelLabClient')

# =============================================================================
# Constants
# =============================================================================

PIXELLAB_API_V1 = "https://api.pixellab.ai/v1"
PIXELLAB_API_V2 = "https://api.pixellab.ai/v2"
PIXELLAB_API_BASE = PIXELLAB_API_V1  # Default to v1 for backward compat

# Pricing per operation (USD) - approximate ranges
PIXELLAB_PRICING = {
    # v1 endpoints
    'pixflux': (0.00793, 0.0132),
    'bitforge': (0.0071, 0.01285),
    'inpaint': (0.00716, 0.01285),
    'rotate': (0.01057, 0.01091),
    'animate_skeleton': (0.0136, 0.01572),
    'animate_text': 0.015,
    'estimate_skeleton': (0.00511, 0.00516),
    # v2 endpoints (approximate)
    'generate_v2': (0.008, 0.015),
    'animate_text_v2': (0.012, 0.02),
    'resize': (0.005, 0.01),
    '8_rotations': (0.08, 0.12),  # 8 images
    'tileset': (0.10, 0.15),      # Multiple tiles
}


# =============================================================================
# Enums (matching API)
# =============================================================================

class CameraView(str, Enum):
    """Camera view angle."""
    SIDE = "side"
    LOW_TOP_DOWN = "low top-down"
    HIGH_TOP_DOWN = "high top-down"


class Direction(str, Enum):
    """Subject facing direction (8-directional)."""
    NORTH = "north"
    NORTH_EAST = "north-east"
    EAST = "east"
    SOUTH_EAST = "south-east"
    SOUTH = "south"
    SOUTH_WEST = "south-west"
    WEST = "west"
    NORTH_WEST = "north-west"


class Outline(str, Enum):
    """Outline style (official API values)."""
    SINGLE_COLOR_BLACK = "single color black outline"
    SINGLE_COLOR_OUTLINE = "single color outline"
    SELECTIVE_OUTLINE = "selective outline"
    LINELESS = "lineless"


class Shading(str, Enum):
    """Shading detail level (official API values)."""
    FLAT = "flat shading"
    SIMPLE = "basic shading"
    MODERATE = "medium shading"
    DETAILED = "detailed shading"
    HIGHLY_DETAILED = "highly detailed shading"


class Detail(str, Enum):
    """Overall detail level (official API values)."""
    LOW = "low detail"
    MEDIUM = "medium detail"
    HIGH = "highly detailed"


class OutlineV2(str, Enum):
    """v2 API outline styles."""
    THIN = "thin"
    MEDIUM = "medium"
    THICK = "thick"
    NONE = "none"


class ShadingV2(str, Enum):
    """v2 API shading styles."""
    SOFT = "soft"
    HARD = "hard"
    FLAT = "flat"
    NONE = "none"


class AnimationTemplate(str, Enum):
    """Pre-built animation templates for animate-character endpoint."""
    IDLE = "breathing-idle"
    IDLE_FIGHT = "fight-stance-idle-8-frames"
    WALK = "crouched-walking"
    CROUCH = "crouching"
    PUNCH = "cross-punch"
    KICK = "flying-kick"
    BACKFLIP = "backflip"
    DRINK = "drinking"
    DEATH = "falling-back-death"
    FIREBALL = "fireball"


class SkeletonLabel(str, Enum):
    """Skeleton joint labels."""
    NOSE = "NOSE"
    NECK = "NECK"
    RIGHT_SHOULDER = "RIGHT_SHOULDER"
    LEFT_SHOULDER = "LEFT_SHOULDER"
    RIGHT_ELBOW = "RIGHT_ELBOW"
    LEFT_ELBOW = "LEFT_ELBOW"
    RIGHT_ARM = "RIGHT_ARM"
    LEFT_ARM = "LEFT_ARM"
    RIGHT_HIP = "RIGHT_HIP"
    LEFT_HIP = "LEFT_HIP"
    RIGHT_KNEE = "RIGHT_KNEE"
    LEFT_KNEE = "LEFT_KNEE"
    RIGHT_LEG = "RIGHT_LEG"
    LEFT_LEG = "LEFT_LEG"
    RIGHT_EYE = "RIGHT_EYE"
    LEFT_EYE = "LEFT_EYE"
    RIGHT_EAR = "RIGHT_EAR"
    LEFT_EAR = "LEFT_EAR"


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class Keypoint:
    """Skeleton keypoint with position and label."""
    x: float
    y: float
    label: str
    z_index: int = 0


@dataclass
class GenerationResult:
    """Result of a PixelLab generation."""
    success: bool
    image: Optional[Image.Image] = None
    images: Optional[List[Image.Image]] = None  # For animations
    cost_usd: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SkeletonResult:
    """Result of skeleton estimation."""
    success: bool
    keypoints: List[Keypoint] = field(default_factory=list)
    cost_usd: float = 0.0
    error: Optional[str] = None


# =============================================================================
# PixelLab Client
# =============================================================================

class PixelLabClient:
    """
    Client for PixelLab API.

    Provides access to professional pixel art generation with:
    - Pixflux: High-quality text-to-pixel art (up to 400x400)
    - Bitforge: Style transfer and inpainting (up to 200x200)
    - Animation: Skeleton-based and text-driven animation
    - Rotation: Multi-directional sprite generation
    - Inpainting: Edit existing pixel art
    """

    # Session lock file for preventing multiple concurrent sessions
    LOCK_FILE = Path(__file__).parent.parent / ".pixellab_session.lock"
    
    def __init__(self, api_key: Optional[str] = None, max_calls: int = 1):
        """
        Initialize PixelLab client.

        Args:
            api_key: PixelLab API key. If not provided, uses PIXELLAB_API_KEY.
            max_calls: Maximum API calls per session (default 1 for safety).
        """
        self.api_key = api_key or PIXELLAB_API_KEY
        if not self.api_key:
            logger.warning("PixelLab API key not set. Set PIXELLAB_API_KEY environment variable.")

        self._session_cost = 0.0
        self._call_count = 0
        self._max_calls = max_calls
        
        # Check for existing session lock
        if self.LOCK_FILE.exists():
            with open(self.LOCK_FILE, 'r') as f:
                lock_info = f.read().strip()
            logger.error(f"[PIXELLAB SAFEGUARD] Another session is active: {lock_info}")
            logger.error(f"[PIXELLAB SAFEGUARD] Delete {self.LOCK_FILE} if this is stale.")
            raise RuntimeError(f"PixelLab session lock exists: {self.LOCK_FILE}")
        
        # Create session lock
        with open(self.LOCK_FILE, 'w') as f:
            f.write(f"PID={os.getpid()}, max_calls={max_calls}")
        logger.info(f"[PIXELLAB] Session started. Max calls: {max_calls}")
    
    def __del__(self):
        """Clean up session lock on destruction."""
        try:
            if hasattr(self, 'LOCK_FILE') and self.LOCK_FILE.exists():
                self.LOCK_FILE.unlink()
                logger.info("[PIXELLAB] Session lock released.")
        except Exception:
            pass
    
    def close(self):
        """Explicitly release session lock."""
        if self.LOCK_FILE.exists():
            self.LOCK_FILE.unlink()
            logger.info("[PIXELLAB] Session closed, lock released.")

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string (no data URI prefix)."""
        buffer = BytesIO()
        # Ensure RGBA for transparency support
        if image.mode not in ('RGB', 'RGBA'):
            image = image.convert('RGBA')
        image.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    def _base64_to_image(self, b64_string: Union[str, Dict[str, Any]]) -> Image.Image:
        """Convert base64 string (or dict containing it) to PIL Image."""
        # Handle dict input (API inconsistencies)
        if isinstance(b64_string, dict):
            # Try common keys
            if "base64" in b64_string:
                b64_string = b64_string["base64"]
            elif "image" in b64_string:
                val = b64_string["image"]
                b64_string = val["base64"] if isinstance(val, dict) and "base64" in val else val
            else:
                raise ValueError(f"Could not find base64 string in dict: {b64_string.keys()}")

        # Remove data URI prefix if present
        if b64_string.startswith('data:'):
            b64_string = b64_string.split(',', 1)[1]
        image_data = base64.b64decode(b64_string)
        return Image.open(BytesIO(image_data))

    def _decode_image_response(
        self,
        response: Dict[str, Any],
        default_width: int = 32,
        default_height: int = 32,
    ) -> Tuple[List[Image.Image], List[str], float]:
        """
        Centralized image extraction from any PixelLab API response.
        
        Handles all response formats:
        - Dict keyed by direction: {"south": {...}, "west": {...}}
        - List of images: [{"base64": ...}, ...]
        - Single image: {"base64": ..., "type": ...}
        - Image types: "rgba_bytes" (raw RGBA) or "base64" (PNG/JPEG)
        
        Args:
            response: API response dict (after _make_request unwrapping)
            default_width: Fallback width for rgba_bytes decoding
            default_height: Fallback height for rgba_bytes decoding
            
        Returns:
            Tuple of (images_list, direction_names, cost_usd)
        """
        images = []
        directions = []
        
        # Extract usage/cost
        usage = response.get("usage", {})
        cost = float(usage.get("usd", 0)) if isinstance(usage, dict) else 0
        
        # Helper to decode a single image dict
        def decode_single(img_info: Dict) -> Optional[Image.Image]:
            img_type = img_info.get("type", "base64")
            b64_data = img_info.get("base64", "")
            img_width = img_info.get("width", default_width)
            img_height = img_info.get("height", default_height)
            
            if not b64_data:
                return None
            
            try:
                raw_bytes = base64.b64decode(b64_data)
                
                if img_type == "rgba_bytes":
                    # Raw RGBA pixel data
                    return Image.frombytes('RGBA', (img_width, img_height), raw_bytes)
                else:
                    # PNG/JPEG encoded
                    return Image.open(BytesIO(raw_bytes))
            except Exception as e:
                logger.warning(f"Failed to decode image: {e}")
                return None
        
        # Try to find images in response
        images_data = response.get("images", response.get("image", None))
        
        if images_data is None:
            # Maybe single image at top level
            if "base64" in response:
                img = decode_single(response)
                if img:
                    images.append(img)
                    directions.append("single")
                    
        elif isinstance(images_data, dict):
            # Dict keyed by direction (south, west, etc.)
            direction_order = [
                "south", "south-west", "west", "north-west",
                "north", "north-east", "east", "south-east"
            ]
            for dir_name in direction_order:
                if dir_name in images_data:
                    img = decode_single(images_data[dir_name])
                    if img:
                        images.append(img)
                        directions.append(dir_name)
                        
        elif isinstance(images_data, list):
            # List of images
            for i, img_data in enumerate(images_data):
                if isinstance(img_data, dict):
                    img = decode_single(img_data)
                elif isinstance(img_data, str):
                    # Plain base64 string
                    img = self._base64_to_image(img_data)
                else:
                    img = None
                    
                if img:
                    images.append(img)
                    directions.append(f"frame_{i}")
        
        logger.debug(f"Decoded {len(images)} images from response")
        return images, directions, cost


    def _make_request(
        self,
        endpoint: str,
        payload: Dict[str, Any] = None,
        method: str = 'POST',
        api_version: int = 1,
    ) -> Dict[str, Any]:
        """
        Make API request to PixelLab.

        Args:
            endpoint: API endpoint (e.g., '/generate-image-pixflux')
            payload: Request payload (optional for GET)
            method: HTTP method
            api_version: API version (1 or 2)

        Returns:
            Response JSON as dict
        """
        # SAFEGUARD: Check call counter
        if self._call_count >= self._max_calls:
            logger.error(f"[PIXELLAB SAFEGUARD] Call limit reached: {self._call_count}/{self._max_calls}")
            logger.error(f"[PIXELLAB SAFEGUARD] Endpoint was: {endpoint}")
            logger.error(f"[PIXELLAB SAFEGUARD] Payload: {json.dumps(payload, indent=2) if payload else 'None'}")
            raise RuntimeError(f"PixelLab call limit exceeded: {self._call_count}/{self._max_calls}")
        
        self._call_count += 1
        logger.info(f"[PIXELLAB] API call {self._call_count}/{self._max_calls}: {endpoint}")
        logger.debug(f"[PIXELLAB] Payload: {json.dumps(payload, indent=2) if payload else 'None'}")
        
        if not self.api_key:
            raise ValueError("PixelLab API key not configured")

        base_url = PIXELLAB_API_V2 if api_version == 2 else PIXELLAB_API_V1
        url = f"{base_url}{endpoint}"

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'Accept': 'application/json',
        }

        data = json.dumps(payload).encode('utf-8') if payload else None

        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=180) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                # v2 API wraps everything in {"success": true, "data": {...}, "usage": {...}}
                # Unwrap for consistent handling
                if api_version == 2 and isinstance(result, dict):
                    if result.get("success") is False:
                        error = result.get("error", "Unknown error")
                        raise RuntimeError(f"PixelLab v2 API error: {error}")
                    # Unwrap data but preserve usage at top level
                    if "data" in result:
                        unwrapped = result["data"]
                        if isinstance(unwrapped, dict):
                            unwrapped["usage"] = result.get("usage", {})
                            return unwrapped
                    # Some endpoints return data directly
                    return result
                    
                return result
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else str(e)
            logger.error(f"PixelLab API error {e.code}: {error_body}")
            raise RuntimeError(f"PixelLab API error {e.code}: {error_body}")
        except Exception as e:
            logger.error(f"PixelLab request failed: {e}")
            raise

    def get_balance(self) -> float:
        """Get current credit balance in USD (subscription generations are separate)."""
        if not self.api_key:
            return 0.0

        url = f"{PIXELLAB_API_BASE}/balance"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Accept': 'application/json',
        }

        req = urllib.request.Request(url, headers=headers, method='GET')

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                # API returns {"usd": X} per official docs
                return float(result.get('usd', result.get('balance', 0)))
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return 0.0

    # =========================================================================
    # Image Generation
    # =========================================================================

    def generate_image_pixflux(
        self,
        description: str,
        width: int = 64,
        height: int = 64,
        outline: Union[str, Outline] = Outline.SINGLE_COLOR_BLACK,
        shading: Union[str, Shading] = Shading.DETAILED,
        detail: Union[str, Detail] = Detail.MEDIUM,
        view: Union[str, CameraView] = CameraView.SIDE,
        direction: Union[str, Direction] = Direction.SOUTH,
        isometric: bool = False,
        no_background: bool = True,
        init_image: Optional[Image.Image] = None,
        init_image_strength: int = 300,
        color_image: Optional[Image.Image] = None,
        negative_description: Optional[str] = None,
        text_guidance_scale: float = 8.0,
        seed: Optional[int] = None,
    ) -> GenerationResult:
        """
        Generate pixel art using Pixflux model.

        Best for: High-quality generation up to 400x400 pixels.

        Args:
            description: Text prompt describing the image
            width: Image width (16-400)
            height: Image height (16-400)
            outline: Outline style
            shading: Shading detail level
            detail: Overall detail level
            view: Camera view angle
            direction: Subject facing direction
            isometric: Use isometric projection
            no_background: Transparent background
            init_image: Starting image for consistency
            init_image_strength: How much to follow init_image (0-500)
            color_image: Image to extract palette from
            negative_description: What to avoid
            text_guidance_scale: How closely to follow text (1-20)
            seed: Random seed for reproducibility

        Returns:
            GenerationResult with image and cost
        """
        # Validate dimensions
        if not (16 <= width <= 400 and 16 <= height <= 400):
            return GenerationResult(success=False, error="Dimensions must be 16-400px")
        if width * height < 32 * 32:
            return GenerationResult(success=False, error="Minimum area is 32x32 pixels")

        # Build payload
        payload = {
            "description": description,
            "image_size": {"width": width, "height": height},
            "outline": outline.value if isinstance(outline, Outline) else outline,
            "shading": shading.value if isinstance(shading, Shading) else shading,
            "detail": detail.value if isinstance(detail, Detail) else detail,
            "view": view.value if isinstance(view, CameraView) else view,
            "direction": direction.value if isinstance(direction, Direction) else direction,
            "isometric": isometric,
            "no_background": no_background,
            "text_guidance_scale": text_guidance_scale,
        }

        if init_image:
            payload["init_image"] = self._image_to_base64(init_image)
            payload["init_image_strength"] = init_image_strength

        if color_image:
            payload["color_image"] = self._image_to_base64(color_image)

        if negative_description:
            payload["negative_description"] = negative_description

        if seed is not None:
            payload["seed"] = seed

        logger.info(f"PixelLab Pixflux: {width}x{height} - {description[:50]}...")

        try:
            result = self._make_request("/generate-image-pixflux", payload)

            # Parse response per official API: {"image": {"base64": "..."}, "usage": {"usd": X}}
            image_data = result.get("image", {})
            image_b64 = image_data.get("base64") if isinstance(image_data, dict) else image_data
            usage = result.get("usage", {})
            cost = float(usage.get("usd", 0)) if isinstance(usage, dict) else 0
            self._session_cost += cost

            if image_b64:
                image = self._base64_to_image(image_b64)
                logger.info(f"PixelLab Pixflux success: {image.width}x{image.height}, ${cost:.4f}")
                return GenerationResult(
                    success=True,
                    image=image,
                    cost_usd=cost,
                    metadata={"model": "pixflux", "seed": seed},
                )
            else:
                return GenerationResult(success=False, error="No image in response")

        except Exception as e:
            return GenerationResult(success=False, error=str(e))

    def generate_image_bitforge(
        self,
        description: str,
        width: int = 64,
        height: int = 64,
        style_image: Optional[Image.Image] = None,
        style_strength: float = 50.0,
        inpainting_image: Optional[Image.Image] = None,
        mask_image: Optional[Image.Image] = None,
        outline: Union[str, Outline] = Outline.SINGLE_COLOR_BLACK,
        shading: Union[str, Shading] = Shading.DETAILED,
        detail: Union[str, Detail] = Detail.MEDIUM,
        view: Union[str, CameraView] = CameraView.SIDE,
        direction: Union[str, Direction] = Direction.SOUTH,
        isometric: bool = False,
        no_background: bool = True,
        skeleton_keypoints: Optional[List[Keypoint]] = None,
        skeleton_guidance_scale: float = 2.0,
        text_guidance_scale: float = 8.0,
        seed: Optional[int] = None,
    ) -> GenerationResult:
        """
        Generate pixel art using Bitforge model with style transfer.

        Best for: Style transfer, inpainting, smaller images (up to 200x200).

        Args:
            description: Text prompt
            width: Image width (16-200)
            height: Image height (16-200)
            style_image: Reference image for style transfer
            style_strength: Style transfer intensity (0-100)
            inpainting_image: Original image for inpainting
            mask_image: Mask for inpainting (white = edit area)
            outline, shading, detail: Style parameters
            view, direction: Camera settings
            isometric: Isometric projection
            no_background: Transparent background
            skeleton_keypoints: Optional pose guidance
            skeleton_guidance_scale: Skeleton adherence (0-5)
            text_guidance_scale: Text adherence (1-20)
            seed: Random seed

        Returns:
            GenerationResult with image and cost
        """
        # Validate dimensions
        if not (16 <= width <= 200 and 16 <= height <= 200):
            return GenerationResult(success=False, error="Bitforge dimensions must be 16-200px")

        payload = {
            "description": description,
            "image_size": {"width": width, "height": height},
            "outline": outline.value if isinstance(outline, Outline) else outline,
            "shading": shading.value if isinstance(shading, Shading) else shading,
            "detail": detail.value if isinstance(detail, Detail) else detail,
            "view": view.value if isinstance(view, CameraView) else view,
            "direction": direction.value if isinstance(direction, Direction) else direction,
            "isometric": isometric,
            "no_background": no_background,
            "text_guidance_scale": text_guidance_scale,
        }

        if style_image:
            payload["style_image"] = self._image_to_base64(style_image)
            payload["style_strength"] = style_strength

        if inpainting_image:
            payload["inpainting_image"] = self._image_to_base64(inpainting_image)
        if mask_image:
            payload["mask_image"] = self._image_to_base64(mask_image)

        if skeleton_keypoints:
            payload["skeleton_keypoints"] = [
                {"x": kp.x, "y": kp.y, "label": kp.label, "z_index": kp.z_index}
                for kp in skeleton_keypoints
            ]
            payload["skeleton_guidance_scale"] = skeleton_guidance_scale

        if seed is not None:
            payload["seed"] = seed

        logger.info(f"PixelLab Bitforge: {width}x{height} - {description[:50]}...")

        try:
            result = self._make_request("/generate-image-bitforge", payload)

            image_b64 = result.get("image")
            cost = float(result.get("cost_usd", 0))
            self._session_cost += cost

            if image_b64:
                image = self._base64_to_image(image_b64)
                return GenerationResult(success=True, image=image, cost_usd=cost)
            else:
                return GenerationResult(success=False, error="No image in response")

        except Exception as e:
            return GenerationResult(success=False, error=str(e))

    # Convenience alias
    def generate_image(self, *args, **kwargs) -> GenerationResult:
        """Alias for generate_image_pixflux (default generator)."""
        return self.generate_image_pixflux(*args, **kwargs)

    # =========================================================================
    # Animation
    # =========================================================================

    def animate_with_skeleton(
        self,
        reference_image: Image.Image,
        skeleton_frames: List[List[Keypoint]],
        width: int = 64,
        height: int = 64,
        view: Union[str, CameraView] = CameraView.SIDE,
        direction: Union[str, Direction] = Direction.SOUTH,
        guidance_scale: float = 4.0,
        init_images: Optional[List[Image.Image]] = None,
        color_image: Optional[Image.Image] = None,
    ) -> GenerationResult:
        """
        Generate animation frames using skeleton keypoints.

        Args:
            reference_image: Character reference
            skeleton_frames: List of keypoint lists (one per frame)
            width: Frame width (16-256, must be exact size)
            height: Frame height (16-256, must be exact size)
            view: Camera view
            direction: Subject direction
            guidance_scale: Reference adherence (0-10)
            init_images: Starting frames
            color_image: Palette reference

        Returns:
            GenerationResult with images list (3 frames)
        """
        # Validate dimensions (must be exact sizes)
        valid_sizes = [16, 32, 48, 64, 96, 128, 192, 256]
        if width not in valid_sizes or height not in valid_sizes:
            return GenerationResult(
                success=False,
                error=f"Skeleton animation size must be one of: {valid_sizes}"
            )

        payload = {
            "reference_image": self._image_to_base64(reference_image),
            "image_size": {"width": width, "height": height},
            "skeleton_keypoints": [
                [{"x": kp.x, "y": kp.y, "label": kp.label, "z_index": kp.z_index} for kp in frame]
                for frame in skeleton_frames
            ],
            "view": view.value if isinstance(view, CameraView) else view,
            "direction": direction.value if isinstance(direction, Direction) else direction,
            "guidance_scale": guidance_scale,
        }

        if init_images:
            payload["init_images"] = [self._image_to_base64(img) for img in init_images]

        if color_image:
            payload["color_image"] = self._image_to_base64(color_image)

        logger.info(f"PixelLab Skeleton Animation: {width}x{height}, {len(skeleton_frames)} frames...")

        try:
            result = self._make_request("/animate-with-skeleton", payload)

            images_b64 = result.get("images", [])
            cost = float(result.get("cost_usd", 0))
            self._session_cost += cost

            if images_b64:
                images = [self._base64_to_image(b64) for b64 in images_b64]
                return GenerationResult(success=True, images=images, cost_usd=cost)
            else:
                return GenerationResult(success=False, error="No images in response")

        except Exception as e:
            return GenerationResult(success=False, error=str(e))

    def animate_with_text(
        self,
        description: str,
        action: str,
        reference_image: Image.Image,
        n_frames: int = 4,
        view: Union[str, CameraView] = CameraView.SIDE,
        direction: Union[str, Direction] = Direction.EAST,
        text_guidance_scale: float = 3.0,
        image_guidance_scale: float = 3.0,
        start_frame_index: int = 0,
        seed: Optional[int] = None,
    ) -> GenerationResult:
        """
        Generate animation frames using text description.

        Args:
            description: Character description
            action: Animation action (e.g., "walk", "run", "attack", "idle")
            reference_image: Character reference (will be resized to 64x64)
            n_frames: Number of frames (2-20)
            view: Camera view
            direction: Subject direction
            text_guidance_scale: Text adherence (0-10)
            image_guidance_scale: Reference adherence (0-10)
            start_frame_index: Animation offset
            seed: Random seed

        Returns:
            GenerationResult with images list
        """
        # Text animation is fixed at 64x64
        if n_frames < 2 or n_frames > 20:
            return GenerationResult(success=False, error="n_frames must be 2-20")

        payload = {
            "description": description,
            "action": action,
            "reference_image": self._image_to_base64(reference_image),
            "image_size": {"width": 64, "height": 64},
            "n_frames": n_frames,
            "view": view.value if isinstance(view, CameraView) else view,
            "direction": direction.value if isinstance(direction, Direction) else direction,
            "text_guidance_scale": text_guidance_scale,
            "image_guidance_scale": image_guidance_scale,
            "start_frame_index": start_frame_index,
        }

        if seed is not None:
            payload["seed"] = seed

        logger.info(f"PixelLab Text Animation: {action}, {n_frames} frames...")

        try:
            result = self._make_request("/animate-with-text", payload)

            images_b64 = result.get("images", [])
            cost = float(result.get("cost_usd", 0))
            self._session_cost += cost

            if images_b64:
                images = [self._base64_to_image(b64) for b64 in images_b64]
                return GenerationResult(
                    success=True,
                    images=images,
                    cost_usd=cost,
                    metadata={"action": action, "n_frames": n_frames},
                )
            else:
                return GenerationResult(success=False, error="No images in response")

        except Exception as e:
            return GenerationResult(success=False, error=str(e))

    # =========================================================================
    # Rotation (Multi-Directional Sprites)
    # =========================================================================

    def rotate(
        self,
        from_image: Image.Image,
        width: int = 64,
        height: int = 64,
        from_view: Union[str, CameraView] = CameraView.SIDE,
        to_view: Union[str, CameraView] = CameraView.SIDE,
        from_direction: Union[str, Direction] = Direction.SOUTH,
        to_direction: Union[str, Direction] = Direction.EAST,
        view_change: int = 0,
        direction_change: int = 0,
        image_guidance_scale: float = 3.0,
        color_image: Optional[Image.Image] = None,
    ) -> GenerationResult:
        """
        Rotate a sprite to a different view/direction.

        Great for generating 4 or 8 directional sprites from a single reference.

        Args:
            from_image: Source sprite
            width: Output width (16-200)
            height: Output height (16-200)
            from_view: Original camera view
            to_view: Target camera view
            from_direction: Original facing direction
            to_direction: Target facing direction
            view_change: Tilt degrees (-90 to 90)
            direction_change: Rotation degrees (-180 to 180)
            image_guidance_scale: Reference adherence (0-10)
            color_image: Palette reference

        Returns:
            GenerationResult with rotated image
        """
        if not (16 <= width <= 200 and 16 <= height <= 200):
            return GenerationResult(success=False, error="Rotate dimensions must be 16-200px")

        payload = {
            "from_image": {"base64": self._image_to_base64(from_image)},
            "image_size": {"width": width, "height": height},
            "from_view": from_view.value if isinstance(from_view, CameraView) else from_view,
            "to_view": to_view.value if isinstance(to_view, CameraView) else to_view,
            "from_direction": from_direction.value if isinstance(from_direction, Direction) else from_direction,
            "to_direction": to_direction.value if isinstance(to_direction, Direction) else to_direction,
            "view_change": view_change,
            "direction_change": direction_change,
            "image_guidance_scale": image_guidance_scale,
        }

        if color_image:
            payload["color_image"] = self._image_to_base64(color_image)

        logger.info(f"PixelLab Rotate: {from_direction} -> {to_direction}")

        try:
            result = self._make_request("/rotate", payload)

            image_b64 = result.get("image")
            cost = float(result.get("cost_usd", 0))
            self._session_cost += cost

            if image_b64:
                image = self._base64_to_image(image_b64)
                return GenerationResult(success=True, image=image, cost_usd=cost)
            else:
                return GenerationResult(success=False, error="No image in response")

        except Exception as e:
            return GenerationResult(success=False, error=str(e))

    def generate_directional_sprites(
        self,
        reference_image: Image.Image,
        directions: int = 4,
        width: int = 64,
        height: int = 64,
        from_direction: Union[str, Direction] = Direction.SOUTH,
    ) -> Dict[str, GenerationResult]:
        """
        Generate multi-directional sprites from a single reference.

        Args:
            reference_image: Source sprite (facing from_direction)
            directions: 4 or 8 directions
            width: Output width
            height: Output height
            from_direction: Direction the reference is facing

        Returns:
            Dict mapping direction names to GenerationResults
        """
        if directions == 4:
            target_dirs = [Direction.SOUTH, Direction.EAST, Direction.NORTH, Direction.WEST]
        elif directions == 8:
            target_dirs = list(Direction)
        else:
            return {"error": GenerationResult(success=False, error="directions must be 4 or 8")}

        results = {}

        for to_dir in target_dirs:
            if to_dir.value == (from_direction.value if isinstance(from_direction, Direction) else from_direction):
                # Use original for source direction
                results[to_dir.value] = GenerationResult(
                    success=True,
                    image=reference_image.copy(),
                    cost_usd=0,
                )
            else:
                results[to_dir.value] = self.rotate(
                    from_image=reference_image,
                    width=width,
                    height=height,
                    from_direction=from_direction,
                    to_direction=to_dir,
                )
                time.sleep(0.5)  # Rate limit

        return results

    # =========================================================================
    # Inpainting
    # =========================================================================

    def inpaint(
        self,
        description: str,
        inpainting_image: Image.Image,
        mask_image: Image.Image,
        width: Optional[int] = None,
        height: Optional[int] = None,
        outline: Union[str, Outline] = Outline.SINGLE_COLOR_BLACK,
        shading: Union[str, Shading] = Shading.DETAILED,
        detail: Union[str, Detail] = Detail.MEDIUM,
        view: Union[str, CameraView] = CameraView.SIDE,
        direction: Union[str, Direction] = Direction.SOUTH,
        no_background: bool = True,
        text_guidance_scale: float = 3.0,
        color_image: Optional[Image.Image] = None,
    ) -> GenerationResult:
        """
        Edit pixel art using inpainting.

        Args:
            description: What to generate in masked area
            inpainting_image: Original image
            mask_image: Mask (white = areas to modify)
            width: Output width (16-200, defaults to source)
            height: Output height (16-200, defaults to source)
            outline, shading, detail: Style parameters
            view, direction: Camera settings
            no_background: Transparent background
            text_guidance_scale: Text adherence
            color_image: Palette reference

        Returns:
            GenerationResult with edited image
        """
        width = width or inpainting_image.width
        height = height or inpainting_image.height

        if not (16 <= width <= 200 and 16 <= height <= 200):
            return GenerationResult(success=False, error="Inpaint dimensions must be 16-200px")

        payload = {
            "description": description,
            "inpainting_image": self._image_to_base64(inpainting_image),
            "mask_image": self._image_to_base64(mask_image),
            "image_size": {"width": width, "height": height},
            "outline": outline.value if isinstance(outline, Outline) else outline,
            "shading": shading.value if isinstance(shading, Shading) else shading,
            "detail": detail.value if isinstance(detail, Detail) else detail,
            "view": view.value if isinstance(view, CameraView) else view,
            "direction": direction.value if isinstance(direction, Direction) else direction,
            "no_background": no_background,
            "text_guidance_scale": text_guidance_scale,
        }

        if color_image:
            payload["color_image"] = self._image_to_base64(color_image)

        logger.info(f"PixelLab Inpaint: {width}x{height} - {description[:50]}...")

        try:
            result = self._make_request("/inpaint", payload)

            image_b64 = result.get("image")
            cost = float(result.get("cost_usd", 0))
            self._session_cost += cost

            if image_b64:
                image = self._base64_to_image(image_b64)
                return GenerationResult(success=True, image=image, cost_usd=cost)
            else:
                return GenerationResult(success=False, error="No image in response")

        except Exception as e:
            return GenerationResult(success=False, error=str(e))

    # =========================================================================
    # Skeleton Estimation
    # =========================================================================

    def estimate_skeleton(self, image: Image.Image) -> SkeletonResult:
        """
        Analyze character image to extract skeleton keypoints.

        Args:
            image: Character on transparent background (16-256px)

        Returns:
            SkeletonResult with keypoints list
        """
        # Validate size
        if not (16 <= image.width <= 256 and 16 <= image.height <= 256):
            return SkeletonResult(success=False, error="Image must be 16-256px")

        payload = {
            "image": self._image_to_base64(image),
        }

        logger.info(f"PixelLab Skeleton Estimation: {image.width}x{image.height}")

        try:
            result = self._make_request("/estimate-skeleton", payload)

            keypoints_data = result.get("keypoints", [])
            cost = float(result.get("cost_usd", 0))
            self._session_cost += cost

            keypoints = [
                Keypoint(
                    x=kp.get("x", 0),
                    y=kp.get("y", 0),
                    label=kp.get("label", ""),
                    z_index=kp.get("z_index", 0),
                )
                for kp in keypoints_data
            ]

            return SkeletonResult(success=True, keypoints=keypoints, cost_usd=cost)

        except Exception as e:
            return SkeletonResult(success=False, error=str(e))

    # =========================================================================
    # V2 API: Image Generation
    # =========================================================================

    def generate_image_v2(
        self,
        description: str,
        width: int = 64,
        height: int = 64,
        no_background: bool = True,
        style_image: Optional[Image.Image] = None,
        style_options: Optional[Dict[str, bool]] = None,
        reference_images: Optional[List[Image.Image]] = None,
        seed: Optional[int] = None,
    ) -> GenerationResult:
        """
        Generate pixel art using v2 API (modern text-to-image).

        Args:
            description: Text prompt describing the image (1-2000 chars)
            width: Image width (32, 64, 128, or 256)
            height: Image height (32, 64, 128, or 256)
            no_background: Transparent background
            style_image: Reference image for style matching
            style_options: Dict of style transfer options:
                - color_palette: Copy color palette (default True)
                - outline: Copy outline style (default True)
                - detail: Copy detail level (default True)
                - shading: Copy shading style (default True)
            reference_images: Up to 4 reference images for subject guidance
            seed: Random seed for reproducibility

        Returns:
            GenerationResult with image and cost
        """
        # Validate dimensions (v2 supports 32, 64, 128, 256)
        valid_sizes = [32, 64, 128, 256]
        if width not in valid_sizes:
            # Round to nearest valid size
            width = min(valid_sizes, key=lambda x: abs(x - width))
            logger.warning(f"Width adjusted to nearest valid v2 size: {width}")
        if height not in valid_sizes:
            height = min(valid_sizes, key=lambda x: abs(x - height))
            logger.warning(f"Height adjusted to nearest valid v2 size: {height}")

        payload = {
            "description": description,
            "image_size": {"width": width, "height": height},
        }

        if no_background:
            payload["no_background"] = no_background

        if style_image:
            payload["style_image"] = {"base64": self._image_to_base64(style_image)}
            if style_options:
                payload["style_options"] = style_options

        if reference_images:
            payload["reference_images"] = [
                {"base64": self._image_to_base64(img)}
                for img in reference_images[:4]  # Max 4 references
            ]

        if seed is not None:
            payload["seed"] = seed

        logger.info(f"PixelLab v2 Generate: {width}x{height} - {description[:50]}...")

        try:
            result = self._make_request("/generate-image-v2", payload, api_version=2)

            # Handle various response formats
            image_b64 = None

            # v2 API returns "images" array
            if "images" in result and result["images"]:
                images_data = result["images"]
                if isinstance(images_data, list) and len(images_data) > 0:
                    first_img = images_data[0]
                    if isinstance(first_img, dict):
                        image_b64 = first_img.get("base64")
                    elif isinstance(first_img, str):
                        image_b64 = first_img
            # Fallback: single "image" field
            elif "image" in result:
                image_data = result["image"]
                if isinstance(image_data, dict):
                    image_b64 = image_data.get("base64")
                elif isinstance(image_data, str):
                    image_b64 = image_data

            usage = result.get("usage", {})
            cost = float(usage.get("usd", 0)) if isinstance(usage, dict) else 0
            self._session_cost += cost

            if image_b64:
                image = self._base64_to_image(image_b64)
                return GenerationResult(success=True, image=image, cost_usd=cost)
            else:
                logger.warning(f"V2 response keys: {list(result.keys())}")
                return GenerationResult(success=False, error="No image in response")

        except Exception as e:
            return GenerationResult(success=False, error=str(e))

    # =========================================================================
    # V2 API: Intelligent Resize
    # =========================================================================

    def resize(
        self,
        image: Image.Image,
        target_width: int,
        target_height: int,
    ) -> GenerationResult:
        """
        Intelligently resize pixel art while maintaining aesthetics.

        This is crucial for AI→Genesis conversion when AI generates
        large images (1024x1024) that need to be 32x32.

        Unlike simple downscaling, this uses AI to preserve
        important details and maintain pixel art style.

        Args:
            image: Source image to resize
            target_width: Target width (16-400)
            target_height: Target height (16-400)

        Returns:
            GenerationResult with resized image
        """
        if not (16 <= target_width <= 400 and 16 <= target_height <= 400):
            return GenerationResult(success=False, error="Target dimensions must be 16-400px")

        payload = {
            "image": self._image_to_base64(image),
            "image_size": {"width": target_width, "height": target_height},
        }

        logger.info(f"PixelLab Resize: {image.width}x{image.height} -> {target_width}x{target_height}")

        try:
            result = self._make_request("/resize", payload, api_version=2)

            image_data = result.get("image", {})
            image_b64 = image_data.get("base64") if isinstance(image_data, dict) else image_data
            usage = result.get("usage", {})
            cost = float(usage.get("usd", 0)) if isinstance(usage, dict) else 0
            self._session_cost += cost

            if image_b64:
                image = self._base64_to_image(image_b64)
                return GenerationResult(success=True, image=image, cost_usd=cost)
            else:
                return GenerationResult(success=False, error="No image in response")

        except Exception as e:
            return GenerationResult(success=False, error=str(e))

    # =========================================================================
    # V2 API: 8-Direction Generation
    # =========================================================================

    def generate_8_rotations(
        self,
        reference_image: Image.Image,
        width: int = 32,
        height: int = 32,
    ) -> GenerationResult:
        """
        Generate 8 directional views of a sprite from a single reference.

        Perfect for Genesis/SGDK sprites that need N/NE/E/SE/S/SW/W/NW views.

        Args:
            reference_image: Source sprite (facing any direction)
            width: Output width per sprite
            height: Output height per sprite

        Returns:
            GenerationResult with images list (8 directions)
            Order: N, NE, E, SE, S, SW, W, NW
        """
        # API spec: image_size must be 32-84px
        if not (32 <= width <= 84 and 32 <= height <= 84):
            return GenerationResult(success=False, error="Dimensions must be 32-84px for 8-rotations (API limit)")

        payload = {
            "method": "rotate_character",  # Explicit per API docs
            "reference_image": {
                "type": "base64",
                "base64": self._image_to_base64(reference_image),
                "format": "png"
            },
            "image_size": {"width": width, "height": height},
            "view": "side",  # Match our game perspective
            "no_background": True,
        }

        logger.info(f"PixelLab 8-Rotations: {width}x{height}")

        try:
            result = self._make_request("/generate-8-rotations-v2", payload, api_version=2)
            
            # Check for async job response (may need polling)
            if "background_job_id" in result:
                job_id = result.get("background_job_id")
                logger.info(f"  Async job started: {job_id}")
                
                # Poll for completion
                import time
                for attempt in range(20):  # Max ~100 seconds
                    time.sleep(5)
                    status_result = self._make_request(
                        f"/background-jobs/{job_id}", None, method="GET", api_version=2
                    )
                    status = status_result.get("status", "unknown")
                    logger.debug(f"  Poll {attempt+1}/20: {status}")
                    
                    if status == "completed":
                        result = status_result.get("last_response", status_result)
                        break
                    elif status == "failed":
                        return GenerationResult(success=False, error=f"Job failed: {status_result}")
                else:
                    return GenerationResult(success=False, error="Job timeout")
            
            # Handle response - may be dict by direction (like create_character_8_directions)
            # or list of images
            images_data = result.get("images", {})
            usage = result.get("usage", {})
            cost = float(usage.get("usd", 0)) if isinstance(usage, dict) else 0
            self._session_cost += cost

            images = []
            metadata_dirs = []
            
            if isinstance(images_data, dict):
                # Dict keyed by direction (south, west, etc.)
                direction_order = ["south", "south-west", "west", "north-west", 
                                   "north", "north-east", "east", "south-east"]
                for dir_name in direction_order:
                    if dir_name in images_data:
                        img_info = images_data[dir_name]
                        img_type = img_info.get("type", "base64")
                        b64_data = img_info.get("base64", "")
                        img_width = img_info.get("width", width)
                        img_height = img_info.get("height", height)
                        
                        if b64_data:
                            import base64 as b64mod
                            raw_bytes = b64mod.b64decode(b64_data)
                            
                            if img_type == "rgba_bytes":
                                img = Image.frombytes('RGBA', (img_width, img_height), raw_bytes)
                            else:
                                img = self._base64_to_image(b64_data)
                            
                            images.append(img)
                            metadata_dirs.append(dir_name)
                            
            elif isinstance(images_data, list) and images_data:
                # List format
                for img_data in images_data:
                    if isinstance(img_data, dict):
                        img_type = img_data.get("type", "base64")
                        b64_data = img_data.get("base64", "")
                        img_width = img_data.get("width", width)
                        img_height = img_data.get("height", height)
                        
                        if b64_data:
                            import base64 as b64mod
                            raw_bytes = b64mod.b64decode(b64_data)
                            
                            if img_type == "rgba_bytes":
                                img = Image.frombytes('RGBA', (img_width, img_height), raw_bytes)
                            else:
                                img = self._base64_to_image(b64_data)
                            
                            images.append(img)
                    else:
                        images.append(self._base64_to_image(img_data))
                        
                metadata_dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"][:len(images)]

            if images:
                logger.info(f"  SUCCESS: Got {len(images)} directions")
                return GenerationResult(
                    success=True,
                    images=images,
                    cost_usd=cost,
                    metadata={"directions": metadata_dirs}
                )
            else:
                logger.error(f"  No images in response. Keys: {result.keys() if isinstance(result, dict) else type(result)}")
                return GenerationResult(success=False, error="No images in response")

        except Exception as e:
            logger.error(f"  Exception: {e}")
            return GenerationResult(success=False, error=str(e))

    def create_character_8_directions(
        self,
        description: str,
        width: int = 64,
        height: int = 64,
        outline: str = "medium",
        shading: str = "soft",
        detail: str = "medium",
        view: str = "side",
        max_poll_attempts: int = 30,
        poll_interval: float = 10.0,
    ) -> GenerationResult:
        """
        Create a character with 8 directional views using async job processing.
        
        This is the RELIABLE method for 8-way sprites. Uses /create-character-with-8-directions
        which submits a background job and returns results when complete.
        
        Args:
            description: Text description of character to generate
            width: Output width (32-400px)
            height: Output height (32-400px)
            outline: Outline style (thin, medium, thick, none)
            shading: Shading style (soft, hard, flat, none)
            detail: Detail level (low, medium, high)
            view: Camera view (side, low top-down, high top-down)
            max_poll_attempts: Max polling attempts before timeout
            poll_interval: Seconds between poll attempts
            
        Returns:
            GenerationResult with images dict keyed by direction
            (north, south, east, west, north-east, north-west, south-east, south-west)
        """
        import time
        
        # Validate size
        if not (32 <= width <= 400 and 32 <= height <= 400):
            return GenerationResult(success=False, error="Dimensions must be 32-400px")
        
        payload = {
            "description": description,
            "image_size": {"width": width, "height": height},
            "outline": outline,
            "shading": shading,
            "detail": detail,
            "view": view,
        }
        
        logger.info(f"PixelLab Create 8-Dir Character: {width}x{height}")
        logger.info(f"  Description: {description[:50]}...")
        
        try:
            # Submit job
            result = self._make_request("/create-character-with-8-directions", payload, api_version=2)
            
            job_id = result.get("background_job_id")
            character_id = result.get("character_id")
            
            if not job_id:
                return GenerationResult(success=False, error="No job_id returned from API")
            
            logger.info(f"  Job submitted: {job_id}")
            logger.info(f"  Character ID: {character_id}")
            
            # Poll for completion
            for attempt in range(max_poll_attempts):
                time.sleep(poll_interval)
                
                status_result = self._make_request(
                    f"/background-jobs/{job_id}", 
                    None, 
                    method="GET", 
                    api_version=2
                )
                status = status_result.get("status", "unknown")
                
                logger.debug(f"  Poll {attempt+1}/{max_poll_attempts}: {status}")
                
                if status == "completed":
                    # Extract images from last_response
                    last_response = status_result.get("last_response", {})
                    images_data = last_response.get("images", {})
                    usage = status_result.get("usage", {})
                    cost = float(usage.get("usd", 0)) if isinstance(usage, dict) else 0
                    self._session_cost += cost
                    
                    # Convert base64 images
                    images = []
                    direction_order = ["south", "south-west", "west", "north-west", 
                                       "north", "north-east", "east", "south-east"]
                    metadata_dirs = []
                    
                    for dir_name in direction_order:
                        if dir_name in images_data:
                            img_info = images_data[dir_name]
                            img_type = img_info.get("type", "base64")
                            b64_data = img_info.get("base64", "")
                            img_width = img_info.get("width", width)
                            img_height = img_info.get("height", height)
                            
                            if b64_data:
                                import base64
                                raw_bytes = base64.b64decode(b64_data)
                                
                                if img_type == "rgba_bytes":
                                    # Raw RGBA pixel data
                                    img = Image.frombytes('RGBA', (img_width, img_height), raw_bytes)
                                else:
                                    # PNG/JPEG base64
                                    img = self._base64_to_image(b64_data)
                                    
                                images.append(img)
                                metadata_dirs.append(dir_name)
                    
                    logger.info(f"  SUCCESS: Got {len(images)} directions")
                    return GenerationResult(
                        success=True,
                        images=images,
                        cost_usd=cost,
                        metadata={
                            "directions": metadata_dirs,
                            "character_id": character_id,
                            "job_id": job_id
                        }
                    )
                    
                elif status == "failed":
                    error_msg = status_result.get("error", "Unknown error")
                    return GenerationResult(success=False, error=f"Job failed: {error_msg}")
            
            # Timeout
            return GenerationResult(success=False, error=f"Job timeout after {max_poll_attempts} attempts")
            
        except Exception as e:
            return GenerationResult(success=False, error=str(e))

    # =========================================================================
    # V2 API: Animation
    # =========================================================================

    def animate_with_text_v2(
        self,
        description: str,
        action: str,
        reference_image: Image.Image,
        n_frames: int = 4,
        view: Union[str, CameraView] = CameraView.SIDE,
        direction: Union[str, Direction] = Direction.SOUTH,
        text_guidance_scale: float = 4.0,
        image_guidance_scale: float = 3.0,
        seed: Optional[int] = None,
    ) -> GenerationResult:
        """
        Generate animation frames using v2 text-to-animation.

        Enhanced version with better frame consistency.

        Args:
            description: Character description
            action: Animation action (walk, run, attack, idle, etc.)
            reference_image: Character reference
            n_frames: Number of frames (2-20)
            view: Camera view
            direction: Subject direction
            text_guidance_scale: Text adherence (0-20)
            image_guidance_scale: Reference adherence (0-20)
            seed: Random seed

        Returns:
            GenerationResult with images list
        """
        if n_frames < 2 or n_frames > 20:
            return GenerationResult(success=False, error="n_frames must be 2-20")

        payload = {
            "description": description,
            "action": action,
            "reference_image": self._image_to_base64(reference_image),
            "n_frames": n_frames,
            "view": view.value if isinstance(view, CameraView) else view,
            "direction": direction.value if isinstance(direction, Direction) else direction,
            "text_guidance_scale": text_guidance_scale,
            "image_guidance_scale": image_guidance_scale,
        }

        if seed is not None:
            payload["seed"] = seed

        logger.info(f"PixelLab v2 Animation: {action}, {n_frames} frames")

        try:
            result = self._make_request("/animate-with-text-v2", payload, api_version=2)

            images_data = result.get("images", [])
            usage = result.get("usage", {})
            cost = float(usage.get("usd", 0)) if isinstance(usage, dict) else 0
            self._session_cost += cost

            if images_data:
                images = []
                for img_data in images_data:
                    img_b64 = img_data.get("base64") if isinstance(img_data, dict) else img_data
                    images.append(self._base64_to_image(img_b64))

                return GenerationResult(
                    success=True,
                    images=images,
                    cost_usd=cost,
                    metadata={"action": action, "n_frames": n_frames}
                )
            else:
                return GenerationResult(success=False, error="No images in response")

        except Exception as e:
            return GenerationResult(success=False, error=str(e))

    # =========================================================================
    # V2 API: Tileset Generation
    # =========================================================================

    def create_tileset(
        self,
        description: str,
        tile_size: int = 16,
        style_image: Optional[Image.Image] = None,
    ) -> GenerationResult:
        """
        Generate a top-down tileset with seamless tile connections.

        Args:
            description: Tileset description (e.g., "grass terrain", "stone dungeon")
            tile_size: Size per tile (16 or 32)
            style_image: Reference for style matching

        Returns:
            GenerationResult with tileset image
        """
        if tile_size not in (16, 32):
            return GenerationResult(success=False, error="tile_size must be 16 or 32")

        payload = {
            "description": description,
            "tile_size": {"width": tile_size, "height": tile_size},
        }

        if style_image:
            payload["style_image"] = self._image_to_base64(style_image)

        logger.info(f"PixelLab Tileset: {tile_size}x{tile_size} - {description[:50]}...")

        try:
            result = self._make_request("/create-tileset", payload, api_version=2)

            image_data = result.get("image", {})
            image_b64 = image_data.get("base64") if isinstance(image_data, dict) else image_data
            usage = result.get("usage", {})
            cost = float(usage.get("usd", 0)) if isinstance(usage, dict) else 0
            self._session_cost += cost

            if image_b64:
                image = self._base64_to_image(image_b64)
                return GenerationResult(
                    success=True,
                    image=image,
                    cost_usd=cost,
                    metadata={"tile_size": tile_size}
                )
            else:
                return GenerationResult(success=False, error="No image in response")

        except Exception as e:
            return GenerationResult(success=False, error=str(e))

    # =========================================================================
    # V2 API: Image Editing
    # =========================================================================

    def edit_image(
        self,
        image: Image.Image,
        edit_prompt: str,
        mask_image: Optional[Image.Image] = None,
    ) -> GenerationResult:
        """
        Edit existing pixel art via text prompt.

        Args:
            image: Image to edit
            edit_prompt: Description of desired changes
            mask_image: Optional mask (white = edit, black = keep)

        Returns:
            GenerationResult with edited image
        """
        payload = {
            "image": self._image_to_base64(image),
            "edit_prompt": edit_prompt,
        }

        if mask_image:
            payload["mask_image"] = self._image_to_base64(mask_image)

        logger.info(f"PixelLab Edit: {edit_prompt[:50]}...")

        try:
            result = self._make_request("/edit-image", payload, api_version=2)

            image_data = result.get("image", {})
            image_b64 = image_data.get("base64") if isinstance(image_data, dict) else image_data
            usage = result.get("usage", {})
            cost = float(usage.get("usd", 0)) if isinstance(usage, dict) else 0
            self._session_cost += cost

            if image_b64:
                image = self._base64_to_image(image_b64)
                return GenerationResult(success=True, image=image, cost_usd=cost)
            else:
                return GenerationResult(success=False, error="No image in response")

        except Exception as e:
            return GenerationResult(success=False, error=str(e))

    # =========================================================================
    # Session Management
    # =========================================================================

    def get_session_cost(self) -> float:
        """Get total cost for this session in USD."""
        return self._session_cost

    def reset_session_cost(self):
        """Reset session cost counter."""
        self._session_cost = 0.0


# =============================================================================
# Convenience Functions
# =============================================================================

def create_sprite(
    description: str,
    width: int = 64,
    height: int = 64,
    **kwargs,
) -> Optional[Image.Image]:
    """
    Quick function to create a sprite.

    Args:
        description: Sprite description
        width: Width in pixels
        height: Height in pixels
        **kwargs: Additional args for generate_image_pixflux

    Returns:
        PIL Image or None on failure
    """
    client = PixelLabClient()
    result = client.generate_image_pixflux(
        description=description,
        width=width,
        height=height,
        no_background=True,
        **kwargs,
    )
    return result.image if result.success else None


def create_animation(
    description: str,
    action: str,
    reference_image: Image.Image,
    n_frames: int = 4,
    **kwargs,
) -> Optional[List[Image.Image]]:
    """
    Quick function to create animation frames.

    Args:
        description: Character description
        action: Animation action (walk, run, attack, idle)
        reference_image: Reference sprite
        n_frames: Number of frames
        **kwargs: Additional args for animate_with_text

    Returns:
        List of PIL Images or None on failure
    """
    client = PixelLabClient()
    result = client.animate_with_text(
        description=description,
        action=action,
        reference_image=reference_image,
        n_frames=n_frames,
        **kwargs,
    )
    return result.images if result.success else None


# =============================================================================
# GENESIS/SGDK DEFAULTS
# =============================================================================

# Genesis-optimized generation parameters (v1 API)
GENESIS_DEFAULTS = {
    "width": 32,                    # Native sprite size, not 1024!
    "height": 32,
    "outline": Outline.SINGLE_COLOR_BLACK,
    "shading": Shading.SIMPLE,      # Genesis has limited colors
    "detail": Detail.MEDIUM,
    "no_background": True,          # Transparent for magenta conversion
    "view": CameraView.SIDE,
}

# Genesis-optimized parameters for v2 API
# Note: v2 API uses style_options (booleans) when a style_image is provided
GENESIS_DEFAULTS_V2 = {
    "width": 32,
    "height": 32,
    "no_background": True,
}


def generate_genesis_sprite(
    client: PixelLabClient,
    description: str,
    width: int = 32,
    height: int = 32,
    palette_name: Optional[str] = None,
    use_v2: bool = False,
    style_image: Optional[Image.Image] = None,
    format_for_sgdk: bool = True,
    **kwargs,
) -> Optional[Image.Image]:
    """
    Generate a Genesis/SGDK-compatible sprite.

    Uses PixelLab with Genesis-optimized defaults, then optionally post-processes
    with SGDKFormatter to ensure SGDK compatibility.

    Args:
        client: PixelLabClient instance
        description: Text prompt describing the sprite
        width: Sprite width (8, 16, 24, or 32 - default 32)
        height: Sprite height (8, 16, 24, or 32 - default 32)
        palette_name: Optional palette from genesis_palettes.py
        use_v2: Use v2 API (better quality, slightly higher cost)
        style_image: Reference image for style matching (v2 only)
        format_for_sgdk: If True, apply SGDK palette/format conversion (default True)
        **kwargs: Additional PixelLab parameters

    Returns:
        Sprite image (SGDK-formatted if format_for_sgdk=True), or None on failure

    Example:
        client = PixelLabClient()
        sprite = generate_genesis_sprite(
            client,
            "knight with sword, side view",
            palette_name="player_warm",
            use_v2=True,
        )
        if sprite:
            sprite.save("knight.png")
    """
    # Validate Genesis sprite sizes
    valid_sizes = [8, 16, 24, 32]
    if width not in valid_sizes:
        logger.warning(f"Width {width} not valid for Genesis, using 32")
        width = 32
    if height not in valid_sizes:
        logger.warning(f"Height {height} not valid for Genesis, using 32")
        height = 32

    # Generate via PixelLab (v1 or v2)
    if use_v2:
        # Use v2 API with Genesis defaults
        params = {**GENESIS_DEFAULTS_V2, **kwargs}
        params["width"] = width
        params["height"] = height
        if style_image:
            params["style_image"] = style_image
        result = client.generate_image_v2(description=description, **params)
    else:
        # Use v1 API (pixflux)
        params = {**GENESIS_DEFAULTS, **kwargs}
        params["width"] = width
        params["height"] = height
        result = client.generate_image_pixflux(description=description, **params)

    if not result.success:
        logger.error(f"Genesis sprite generation failed: {result.error}")
        return None

    # Return raw image if SGDK formatting not requested
    if not format_for_sgdk:
        return result.image

    # Post-process with SGDK formatter (optional)
    try:
        # Import here to avoid circular dependency
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))

        from pipeline.sgdk_format import SGDKFormatter
        from pipeline.palettes import get_genesis_palette

        palette = get_genesis_palette(palette_name) if palette_name else None
        formatter = SGDKFormatter(target_palette=palette)

        formatted = formatter.format_sprite(result.image, (width, height))
        return formatted

    except ImportError as e:
        logger.warning(f"SGDK formatter not available, returning raw image: {e}")
        return result.image


def generate_genesis_animation(
    client: PixelLabClient,
    description: str,
    action: str = "walk",
    n_frames: int = 4,
    width: int = 32,
    height: int = 32,
    palette_name: Optional[str] = None,
    reference_image: Optional[Image.Image] = None,
    use_v2: bool = False,
    format_for_sgdk: bool = True,
    **kwargs,
) -> Optional[List[Image.Image]]:
    """
    Generate an animated sprite sequence for Genesis/SGDK.

    Args:
        client: PixelLabClient instance
        description: Text prompt describing the character
        action: Animation action ("walk", "idle", "attack", etc.)
        n_frames: Number of frames (2-10, or 2-20 for v2)
        width: Sprite width
        height: Sprite height
        palette_name: Optional palette from genesis_palettes.py
        reference_image: Reference image for consistency
        use_v2: Use v2 animation API (better consistency, more frames)
        format_for_sgdk: If True, apply SGDK palette/format conversion (default True)
        **kwargs: Additional PixelLab parameters

    Returns:
        List of frames (SGDK-formatted if format_for_sgdk=True), or None on failure
    """
    # Generate animation (v1 or v2)
    if use_v2 and reference_image is not None:
        result = client.animate_with_text_v2(
            description=description,
            action=action,
            n_frames=n_frames,
            reference_image=reference_image,
            **kwargs,
        )
    else:
        result = client.animate_with_text(
            description=description,
            action=action,
            n_frames=n_frames,
            reference_image=reference_image,
            **kwargs,
        )

    if not result.success or not result.images:
        logger.error(f"Genesis animation failed: {result.error}")
        return None

    # Return raw images if SGDK formatting not requested
    if not format_for_sgdk:
        return result.images

    # Post-process each frame (optional)
    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))

        from pipeline.sgdk_format import SGDKFormatter
        from pipeline.palettes import get_genesis_palette

        palette = get_genesis_palette(palette_name) if palette_name else None
        formatter = SGDKFormatter(target_palette=palette)

        formatted_frames = []
        for frame in result.images:
            formatted = formatter.format_sprite(frame, (width, height))
            formatted_frames.append(formatted)

        return formatted_frames

    except ImportError as e:
        logger.warning(f"SGDK formatter not available: {e}")
        return result.images


def generate_genesis_8_directions(
    client: PixelLabClient,
    reference_image: Image.Image,
    width: int = 32,
    height: int = 32,
    palette_name: Optional[str] = None,
    format_for_sgdk: bool = True,
) -> Optional[List[Image.Image]]:
    """
    Generate 8 directional views of a sprite for Genesis/SGDK.

    Perfect for top-down or isometric games needing N/NE/E/SE/S/SW/W/NW views.

    Args:
        client: PixelLabClient instance
        reference_image: Source sprite (facing any direction)
        width: Output width per sprite (8, 16, 24, or 32)
        height: Output height per sprite
        palette_name: Optional palette from genesis_palettes.py
        format_for_sgdk: If True, apply SGDK palette/format conversion (default True)

    Returns:
        List of 8 sprites (N, NE, E, SE, S, SW, W, NW), or None on failure

    Example:
        client = PixelLabClient()
        # First generate a reference sprite
        ref = generate_genesis_sprite(client, "warrior with spear")
        # Then generate 8 directions
        directions = generate_genesis_8_directions(client, ref)
        if directions:
            for i, d in enumerate(["N", "NE", "E", "SE", "S", "SW", "W", "NW"]):
                directions[i].save(f"warrior_{d}.png")
    """
    # Validate sizes
    valid_sizes = [8, 16, 24, 32]
    if width not in valid_sizes:
        logger.warning(f"Width {width} not valid for Genesis, using 32")
        width = 32
    if height not in valid_sizes:
        logger.warning(f"Height {height} not valid for Genesis, using 32")
        height = 32

    # Generate 8 rotations via v2 API
    result = client.generate_8_rotations(
        reference_image=reference_image,
        width=width,
        height=height,
    )

    if not result.success or not result.images:
        logger.error(f"Genesis 8-direction generation failed: {result.error}")
        return None

    # Return raw images if SGDK formatting not requested
    if not format_for_sgdk:
        return result.images

    # Post-process each direction (optional)
    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))

        from pipeline.sgdk_format import SGDKFormatter
        from pipeline.palettes import get_genesis_palette

        palette = get_genesis_palette(palette_name) if palette_name else None
        formatter = SGDKFormatter(target_palette=palette)

        formatted_sprites = []
        for sprite in result.images:
            formatted = formatter.format_sprite(sprite, (width, height))
            formatted_sprites.append(formatted)

        return formatted_sprites

    except ImportError as e:
        logger.warning(f"SGDK formatter not available: {e}")
        return result.images


def resize_to_genesis(
    client: PixelLabClient,
    image: Image.Image,
    target_width: int = 32,
    target_height: int = 32,
    palette_name: Optional[str] = None,
    format_for_sgdk: bool = True,
) -> Optional[Image.Image]:
    """
    Intelligently resize an image to Genesis sprite dimensions.

    Uses PixelLab's AI resize to maintain pixel art aesthetics when
    downsizing large AI-generated images (e.g., 1024x1024 → 32x32).

    Args:
        client: PixelLabClient instance
        image: Source image (any size)
        target_width: Target width (8, 16, 24, or 32)
        target_height: Target height
        palette_name: Optional palette from genesis_palettes.py
        format_for_sgdk: If True, apply SGDK palette/format conversion (default True)

    Returns:
        Resized sprite (SGDK-formatted if format_for_sgdk=True), or None on failure

    Example:
        client = PixelLabClient()
        # You have a 512x512 image from another AI
        large_img = Image.open("ai_generated.png")
        # Resize to Genesis sprite
        sprite = resize_to_genesis(client, large_img, 32, 32, "player_warm")
    """
    # Validate sizes
    valid_sizes = [8, 16, 24, 32]
    if target_width not in valid_sizes:
        logger.warning(f"Width {target_width} not valid for Genesis, using 32")
        target_width = 32
    if target_height not in valid_sizes:
        logger.warning(f"Height {target_height} not valid for Genesis, using 32")
        target_height = 32

    # Intelligent resize via v2 API
    result = client.resize(
        image=image,
        target_width=target_width,
        target_height=target_height,
    )

    if not result.success:
        logger.error(f"Genesis resize failed: {result.error}")
        return None

    # Return raw image if SGDK formatting not requested
    if not format_for_sgdk:
        return result.image

    # Post-process with SGDK formatter (optional)
    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))

        from pipeline.sgdk_format import SGDKFormatter
        from pipeline.palettes import get_genesis_palette

        palette = get_genesis_palette(palette_name) if palette_name else None
        formatter = SGDKFormatter(target_palette=palette)

        formatted = formatter.format_sprite(result.image, (target_width, target_height))
        return formatted

    except ImportError as e:
        logger.warning(f"SGDK formatter not available: {e}")
        return result.image


def generate_genesis_tileset(
    client: PixelLabClient,
    description: str,
    tile_size: int = 16,
    palette_name: Optional[str] = None,
    style_image: Optional[Image.Image] = None,
    format_for_sgdk: bool = True,
) -> Optional[Image.Image]:
    """
    Generate a tileset for Genesis/SGDK.

    Creates a seamless tileset suitable for map backgrounds.

    Args:
        client: PixelLabClient instance
        description: Tileset description (e.g., "grass terrain", "dungeon floor")
        tile_size: Size per tile (16 or 32)
        palette_name: Optional palette from genesis_palettes.py
        style_image: Reference for style matching
        format_for_sgdk: If True, apply SGDK palette/format conversion (default True)

    Returns:
        Tileset image (SGDK-formatted if format_for_sgdk=True), or None on failure
    """
    if tile_size not in (16, 32):
        logger.warning(f"tile_size {tile_size} not ideal for Genesis, using 16")
        tile_size = 16

    result = client.create_tileset(
        description=description,
        tile_size=tile_size,
        style_image=style_image,
    )

    if not result.success:
        logger.error(f"Genesis tileset generation failed: {result.error}")
        return None

    # Return raw image if SGDK formatting not requested
    if not format_for_sgdk:
        return result.image

    # Post-process with SGDK formatter (optional)
    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))

        from pipeline.sgdk_format import SGDKFormatter
        from pipeline.palettes import get_genesis_palette

        palette = get_genesis_palette(palette_name) if palette_name else None
        formatter = SGDKFormatter(target_palette=palette)

        # Format as tileset (don't resize individual tiles)
        formatted = formatter.format_sprite(result.image)
        return formatted

    except ImportError as e:
        logger.warning(f"SGDK formatter not available: {e}")
        return result.image


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PixelLab API Client")
    parser.add_argument("--balance", action="store_true", help="Check account balance")
    parser.add_argument("--test", action="store_true", help="Run test generation (v1 API)")
    parser.add_argument("--test-v2", action="store_true", help="Run test generation (v2 API)")
    parser.add_argument("--test-genesis", action="store_true", help="Test Genesis sprite generation")
    parser.add_argument("--description", default="robot character", help="Test description")
    parser.add_argument("--use-v2", action="store_true", help="Use v2 API for Genesis test")

    args = parser.parse_args()

    client = PixelLabClient()

    if args.balance:
        balance = client.get_balance()
        print(f"Account balance: ${balance:.4f}")

    if args.test:
        print(f"Testing v1 generation: {args.description}")
        result = client.generate_image_pixflux(
            description=args.description,
            width=64,
            height=64,
            no_background=True,
        )
        if result.success:
            print(f"Success! Cost: ${result.cost_usd:.4f}")
            result.image.save("pixellab_test_v1.png")
            print("Saved to pixellab_test_v1.png")
        else:
            print(f"Failed: {result.error}")

    if args.test_v2:
        print(f"Testing v2 generation: {args.description}")
        result = client.generate_image_v2(
            description=args.description,
            width=64,
            height=64,
            no_background=True,
        )
        if result.success:
            print(f"Success! Cost: ${result.cost_usd:.4f}")
            result.image.save("pixellab_test_v2.png")
            print("Saved to pixellab_test_v2.png")
        else:
            print(f"Failed: {result.error}")

    if args.test_genesis:
        print(f"Testing Genesis sprite: {args.description}")
        sprite = generate_genesis_sprite(
            client,
            args.description,
            width=32,
            height=32,
            use_v2=args.use_v2,
        )
        if sprite:
            api_version = "v2" if args.use_v2 else "v1"
            filename = f"genesis_test_{api_version}.png"
            sprite.save(filename)
            print(f"Success! Saved to {filename}")
            print(f"  Size: {sprite.width}x{sprite.height}")
            print(f"  Mode: {sprite.mode}")
            if hasattr(sprite, 'getcolors'):
                colors = sprite.getcolors(maxcolors=256)
                if colors:
                    print(f"  Colors: {len(colors)}")
        else:
            print("Failed to generate Genesis sprite")

    print(f"\nSession total cost: ${client.get_session_cost():.4f}")
