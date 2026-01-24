"""
Modular Model Configuration for ARDK Asset Generation.

Provides cost-tiered model selection for Pollinations.ai API:
- ECONOMY: Cheapest models, ~5000 images per pollen
- QUALITY: Mid-tier models with better output
- PRECISION: Best models for critical assets

Usage:
    from asset_generators.model_config import ModelConfig, get_model_config

    config = get_model_config("economy")
    model = config.txt2img_model  # 'flux'

    # Or use quality mode for better results
    config = get_model_config("quality")
    model = config.txt2img_model  # 'gptimage'
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum


class ModelTier(Enum):
    """Model cost/quality tier."""
    ECONOMY = "economy"      # ~0.0002/image (5000 per pollen)
    QUALITY = "quality"      # ~0.03-0.04/image (25-35 per pollen)
    PRECISION = "precision"  # Best quality, highest cost
    PIXELART = "pixelart"    # PixelLab specialist (~$0.01/image)


@dataclass
class ModelConfig:
    """
    Configuration for which models to use at each tier.

    Based on Pollinations.ai pricing (2026-01-13):

    Text-to-Image (cheapest to most expensive):
    - flux:        0.0002/image  (~5000/pollen) - Fast, good pixel art
    - zimage:      0.0002/image  (~5000/pollen) - Fast, 2x upscale built-in
    - turbo:       0.0003/image  (~3300/pollen) - SDXL Turbo
    - seedream:    0.03/image    (~35/pollen)   - Seedream 4.0
    - kontext:     0.04/image    (~25/pollen)   - FLUX.1 Kontext
    - seedream-pro: 0.04/image   (~25/pollen)   - Seedream 4.5 Pro
    - gptimage:    ~2.5/M tokens                - GPT-4o based
    - nanobanana:  ~0.3/M tokens                - Gemini based
    - gptimage-large: ~8.0/M tokens             - GPT-4o high quality

    Image-to-Image (content preservation):
    - gptimage:       Best content preservation
    - gptimage-large: Higher quality, same behavior
    - nanobanana:     Good alternative
    - seedream:       Good, may vary dimensions
    - flux-kontext:   Dimensions exact, may not preserve content well
    """

    tier: ModelTier
    name: str

    # Primary models for each task
    txt2img_model: str
    txt2img_fallback: str

    img2img_model: str
    img2img_fallback: str

    vision_model: str  # For image analysis

    # Model lists for multi-model operations
    txt2img_models: List[str] = field(default_factory=list)
    img2img_models: List[str] = field(default_factory=list)

    # Cost estimates (per image or per 1M tokens)
    estimated_cost_per_image: float = 0.0002

    # Quality flags
    supports_exact_dimensions: bool = False
    content_preservation_quality: str = "good"  # good, excellent, variable


# =============================================================================
# Tier Configurations
# =============================================================================

ECONOMY_CONFIG = ModelConfig(
    tier=ModelTier.ECONOMY,
    name="Economy",

    # Cheapest text-to-image models
    txt2img_model="flux",           # 0.0002/image - Best for pixel art
    txt2img_fallback="turbo",       # 0.0003/image - Fast SDXL

    # Use gptimage for img2img (preserves content, resize after)
    img2img_model="gptimage",
    img2img_fallback="seedream",

    # Cheapest vision model
    vision_model="gemini-fast",

    # Available models for multi-model operations
    txt2img_models=["flux", "turbo", "zimage", "nanobanana"],
    img2img_models=["gptimage", "seedream"],

    estimated_cost_per_image=0.0002,
    supports_exact_dimensions=False,  # flux respects dimensions, others vary
    content_preservation_quality="good",
)

QUALITY_CONFIG = ModelConfig(
    tier=ModelTier.QUALITY,
    name="Quality",

    # Mid-tier models with better output
    txt2img_model="seedream",       # 0.03/image - Good quality
    txt2img_fallback="flux",        # Fallback to cheap

    # Better img2img
    img2img_model="gptimage-large",
    img2img_fallback="gptimage",

    # Better vision
    vision_model="gemini",

    # Available models
    txt2img_models=["seedream", "seedream-pro", "flux", "gptimage"],
    img2img_models=["gptimage-large", "gptimage", "nanobanana"],

    estimated_cost_per_image=0.03,
    supports_exact_dimensions=False,
    content_preservation_quality="excellent",
)

PRECISION_CONFIG = ModelConfig(
    tier=ModelTier.PRECISION,
    name="Precision",

    # Best models regardless of cost
    txt2img_model="gptimage-large",
    txt2img_fallback="seedream-pro",

    # Best content preservation
    img2img_model="gptimage-large",
    img2img_fallback="nanobanana-pro",

    # Best vision analysis
    vision_model="openai-large",

    # All high-quality models
    txt2img_models=["gptimage-large", "gptimage", "seedream-pro", "nanobanana-pro"],
    img2img_models=["gptimage-large", "nanobanana-pro", "gptimage"],

    estimated_cost_per_image=8.0,  # Per 1M tokens equivalent
    supports_exact_dimensions=False,
    content_preservation_quality="excellent",
)

PIXELART_CONFIG = ModelConfig(
    tier=ModelTier.PIXELART,
    name="PixelArt Specialist",

    # PixelLab for pixel art generation
    txt2img_model="pixellab-pixflux",     # $0.008-0.013/image
    txt2img_fallback="flux",               # Fallback to Pollinations

    # PixelLab for edits, Pollinations for general img2img
    img2img_model="pixellab-bitforge",    # $0.007-0.013/image
    img2img_fallback="gptimage",

    # Standard vision
    vision_model="gemini",

    # Available models
    txt2img_models=["pixellab-pixflux", "pixellab-bitforge", "flux"],
    img2img_models=["pixellab-bitforge", "pixellab-inpaint", "gptimage"],

    estimated_cost_per_image=0.01,  # ~$0.01/image average
    supports_exact_dimensions=True,  # PixelLab respects exact dimensions!
    content_preservation_quality="excellent",
)


# Tier lookup
TIER_CONFIGS: Dict[ModelTier, ModelConfig] = {
    ModelTier.ECONOMY: ECONOMY_CONFIG,
    ModelTier.QUALITY: QUALITY_CONFIG,
    ModelTier.PRECISION: PRECISION_CONFIG,
    ModelTier.PIXELART: PIXELART_CONFIG,
}


# =============================================================================
# Task-Specific Model Selection
# =============================================================================

@dataclass
class TaskModels:
    """Models optimized for specific tasks."""

    # Pixel art generation (text-to-image)
    pixel_art: str = "flux"           # Clean edges, good style control

    # General image generation
    general_image: str = "gptimage"   # Good for varied content

    # Sprite detection (vision)
    sprite_detection: str = "gemini-fast"  # Fast bounding box

    # Palette analysis (vision)
    palette_analysis: str = "openai-large"  # Best color understanding

    # Animation analysis (vision)
    animation_analysis: str = "gemini"      # Motion detection

    # Layout parsing (vision)
    layout_parsing: str = "gemini-large"    # Complex sheets

    # Content-preserving img2img
    img2img_preserve: str = "gptimage-large"

    # Fast img2img
    img2img_fast: str = "gptimage"

    # Style transfer
    img2img_style: str = "seedream"


# Default task models (optimized for cost)
ECONOMY_TASKS = TaskModels(
    pixel_art="flux",
    general_image="flux",
    sprite_detection="gemini-fast",
    palette_analysis="gemini-fast",
    animation_analysis="gemini-fast",
    layout_parsing="gemini",
    img2img_preserve="gptimage",
    img2img_fast="gptimage",
    img2img_style="seedream",
)

# Quality task models
QUALITY_TASKS = TaskModels(
    pixel_art="seedream",
    general_image="gptimage",
    sprite_detection="gemini",
    palette_analysis="openai",
    animation_analysis="gemini",
    layout_parsing="gemini-large",
    img2img_preserve="gptimage-large",
    img2img_fast="gptimage",
    img2img_style="gptimage-large",
)

# Precision task models
PRECISION_TASKS = TaskModels(
    pixel_art="gptimage-large",
    general_image="gptimage-large",
    sprite_detection="openai-large",
    palette_analysis="openai-large",
    animation_analysis="gemini-large",
    layout_parsing="openai-large",
    img2img_preserve="gptimage-large",
    img2img_fast="gptimage-large",
    img2img_style="gptimage-large",
)


TIER_TASKS: Dict[ModelTier, TaskModels] = {
    ModelTier.ECONOMY: ECONOMY_TASKS,
    ModelTier.QUALITY: QUALITY_TASKS,
    ModelTier.PRECISION: PRECISION_TASKS,
}


# =============================================================================
# Model Information
# =============================================================================

@dataclass
class ModelInfo:
    """Information about a specific model."""
    name: str
    endpoint: str  # image.pollinations.ai or gen.pollinations.ai
    supports_img2img: bool
    cost_per_image: float  # Approximate cost
    best_for: List[str]    # What tasks it excels at
    dimensions_behavior: str  # "exact", "approximate", "ignored"
    notes: str = ""


MODEL_INFO: Dict[str, ModelInfo] = {
    # Text-to-image models (cheapest)
    "flux": ModelInfo(
        name="Flux Schnell",
        endpoint="image.pollinations.ai",
        supports_img2img=False,
        cost_per_image=0.0002,
        best_for=["pixel_art", "clean_edges", "fast_generation"],
        dimensions_behavior="exact",
        notes="Best for pixel art. Respects exact dimensions.",
    ),
    "zimage": ModelInfo(
        name="Z-Image Turbo",
        endpoint="image.pollinations.ai",
        supports_img2img=False,
        cost_per_image=0.0002,
        best_for=["fast_generation", "upscaling"],
        dimensions_behavior="exact",
        notes="Has built-in 2x upscaling capability.",
    ),
    "turbo": ModelInfo(
        name="SDXL Turbo",
        endpoint="image.pollinations.ai",
        supports_img2img=False,
        cost_per_image=0.0003,
        best_for=["fast_prototypes", "quick_iterations"],
        dimensions_behavior="approximate",
        notes="Very fast, good for rapid prototyping.",
    ),

    # Mid-tier models
    "seedream": ModelInfo(
        name="Seedream 4.0",
        endpoint="gen.pollinations.ai",
        supports_img2img=True,
        cost_per_image=0.03,
        best_for=["quality_images", "style_transfer"],
        dimensions_behavior="approximate",
        notes="Good quality, supports img2img with content preservation.",
    ),
    "kontext": ModelInfo(
        name="FLUX.1 Kontext",
        endpoint="image.pollinations.ai",
        supports_img2img=True,
        cost_per_image=0.04,
        best_for=["exact_dimensions", "editing"],
        dimensions_behavior="exact",
        notes="Use with image.pollinations.ai. May not preserve content well.",
    ),
    "flux-kontext": ModelInfo(
        name="FLUX.1 Kontext (alias)",
        endpoint="image.pollinations.ai",
        supports_img2img=True,
        cost_per_image=0.04,
        best_for=["exact_dimensions", "editing"],
        dimensions_behavior="exact",
        notes="Alias for kontext. Use image.pollinations.ai endpoint.",
    ),
    "seedream-pro": ModelInfo(
        name="Seedream 4.5 Pro",
        endpoint="gen.pollinations.ai",
        supports_img2img=True,
        cost_per_image=0.04,
        best_for=["high_quality", "detailed_images"],
        dimensions_behavior="approximate",
    ),

    # High-tier models
    "gptimage": ModelInfo(
        name="GPT Image 1 Mini",
        endpoint="gen.pollinations.ai",
        supports_img2img=True,
        cost_per_image=2.5,  # Per 1M input tokens
        best_for=["content_preservation", "understanding", "editing"],
        dimensions_behavior="ignored",
        notes="Excellent content preservation but ignores dimensions. Resize after.",
    ),
    "nanobanana": ModelInfo(
        name="NanoBanana",
        endpoint="gen.pollinations.ai",
        supports_img2img=True,
        cost_per_image=0.3,  # Per 1M tokens
        best_for=["img2img", "gemini_quality"],
        dimensions_behavior="approximate",
        notes="Gemini-based. Good for img2img. May have rate limits.",
    ),
    "gptimage-large": ModelInfo(
        name="GPT Image 1.5",
        endpoint="gen.pollinations.ai",
        supports_img2img=True,
        cost_per_image=8.0,  # Per 1M input tokens
        best_for=["highest_quality", "content_preservation", "complex_edits"],
        dimensions_behavior="ignored",
        notes="Best content preservation. Always resize after.",
    ),
    "nanobanana-pro": ModelInfo(
        name="NanoBanana Pro",
        endpoint="gen.pollinations.ai",
        supports_img2img=True,
        cost_per_image=120.0,  # Per 1M output tokens
        best_for=["premium_quality"],
        dimensions_behavior="approximate",
        notes="Premium tier. Very expensive.",
    ),

    # =========================================================================
    # PixelLab Models - Pixel Art Specialists
    # =========================================================================
    "pixellab-pixflux": ModelInfo(
        name="PixelLab Pixflux",
        endpoint="api.pixellab.ai",
        supports_img2img=False,
        cost_per_image=0.01,  # ~$0.008-0.013
        best_for=["pixel_art", "sprites", "exact_dimensions", "style_control"],
        dimensions_behavior="exact",
        notes="Best for pixel art. Up to 400x400. Outline/shading/detail controls.",
    ),
    "pixellab-bitforge": ModelInfo(
        name="PixelLab Bitforge",
        endpoint="api.pixellab.ai",
        supports_img2img=True,
        cost_per_image=0.01,  # ~$0.007-0.013
        best_for=["style_transfer", "inpainting", "pixel_art_edits"],
        dimensions_behavior="exact",
        notes="Style transfer and inpainting. Up to 200x200.",
    ),
    "pixellab-inpaint": ModelInfo(
        name="PixelLab Inpaint",
        endpoint="api.pixellab.ai",
        supports_img2img=True,
        cost_per_image=0.01,
        best_for=["pixel_art_edits", "modifications"],
        dimensions_behavior="exact",
        notes="Edit existing pixel art with masks.",
    ),
    "pixellab-rotate": ModelInfo(
        name="PixelLab Rotate",
        endpoint="api.pixellab.ai",
        supports_img2img=True,
        cost_per_image=0.011,
        best_for=["directional_sprites", "4dir", "8dir"],
        dimensions_behavior="exact",
        notes="Generate multi-directional sprites from single reference.",
    ),
    "pixellab-animate": ModelInfo(
        name="PixelLab Animate",
        endpoint="api.pixellab.ai",
        supports_img2img=True,
        cost_per_image=0.015,
        best_for=["animation", "sprite_sheets", "walk_cycles"],
        dimensions_behavior="exact",
        notes="Text-driven animation generation. Up to 20 frames.",
    ),
}


# =============================================================================
# Helper Functions
# =============================================================================

def get_model_config(tier: str = "economy") -> ModelConfig:
    """
    Get model configuration for a tier.

    Args:
        tier: "economy", "quality", or "precision"

    Returns:
        ModelConfig for the specified tier
    """
    tier_enum = ModelTier(tier.lower())
    return TIER_CONFIGS[tier_enum]


def get_task_models(tier: str = "economy") -> TaskModels:
    """
    Get task-specific models for a tier.

    Args:
        tier: "economy", "quality", or "precision"

    Returns:
        TaskModels for the specified tier
    """
    tier_enum = ModelTier(tier.lower())
    return TIER_TASKS[tier_enum]


def get_model_for_task(task: str, tier: str = "economy") -> str:
    """
    Get the best model for a specific task at a tier.

    Args:
        task: Task name (pixel_art, sprite_detection, img2img_preserve, etc.)
        tier: "economy", "quality", or "precision"

    Returns:
        Model name string
    """
    tasks = get_task_models(tier)
    return getattr(tasks, task, tasks.pixel_art)


def get_model_info(model: str) -> Optional[ModelInfo]:
    """Get information about a specific model."""
    return MODEL_INFO.get(model)


def get_endpoint_for_model(model: str) -> str:
    """
    Get the correct API endpoint for a model.

    Args:
        model: Model name

    Returns:
        Base URL for the model's endpoint
    """
    info = MODEL_INFO.get(model)
    if info:
        return f"https://{info.endpoint}"

    # Default endpoints based on model patterns
    if model in ("flux", "turbo", "zimage", "kontext", "flux-kontext"):
        return "https://image.pollinations.ai"
    else:
        return "https://gen.pollinations.ai"


def get_img2img_models(tier: str = "economy") -> List[str]:
    """
    Get list of img2img capable models for a tier.

    Args:
        tier: "economy", "quality", or "precision"

    Returns:
        List of model names that support img2img
    """
    config = get_model_config(tier)
    return config.img2img_models


def get_txt2img_models(tier: str = "economy") -> List[str]:
    """
    Get list of text-to-image models for a tier.

    Args:
        tier: "economy", "quality", or "precision"

    Returns:
        List of model names for txt2img
    """
    config = get_model_config(tier)
    return config.txt2img_models


def estimate_cost(
    num_images: int,
    tier: str = "economy",
    operation: str = "txt2img"
) -> float:
    """
    Estimate cost for generating images.

    Args:
        num_images: Number of images to generate
        tier: Model tier
        operation: "txt2img" or "img2img"

    Returns:
        Estimated cost in pollen (approximate)
    """
    config = get_model_config(tier)

    # Different costs for different operations
    if operation == "txt2img":
        cost_per = config.estimated_cost_per_image
    else:
        # img2img uses more expensive models typically
        cost_per = config.estimated_cost_per_image * 2

    return num_images * cost_per


def print_tier_summary():
    """Print summary of all tiers and their models."""
    print("ARDK Model Configuration")
    print("=" * 60)
    print()

    for tier in ModelTier:
        config = TIER_CONFIGS[tier]
        tasks = TIER_TASKS[tier]

        print(f"Tier: {config.name.upper()}")
        print(f"  Cost estimate: ~{config.estimated_cost_per_image}/image")
        print()
        print(f"  Text-to-Image:")
        print(f"    Primary:  {config.txt2img_model}")
        print(f"    Fallback: {config.txt2img_fallback}")
        print(f"    All:      {', '.join(config.txt2img_models)}")
        print()
        print(f"  Image-to-Image:")
        print(f"    Primary:  {config.img2img_model}")
        print(f"    Fallback: {config.img2img_fallback}")
        print(f"    All:      {', '.join(config.img2img_models)}")
        print()
        print(f"  Vision: {config.vision_model}")
        print(f"  Content preservation: {config.content_preservation_quality}")
        print()
        print("-" * 60)
        print()


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Model Configuration Info")
    parser.add_argument("--tier", default="economy", help="Tier to show")
    parser.add_argument("--model", help="Show info for specific model")
    parser.add_argument("--summary", action="store_true", help="Show all tiers")
    parser.add_argument("--task", help="Get model for specific task")

    args = parser.parse_args()

    if args.summary:
        print_tier_summary()
    elif args.model:
        info = get_model_info(args.model)
        if info:
            print(f"Model: {info.name}")
            print(f"  Endpoint: {info.endpoint}")
            print(f"  Cost: {info.cost_per_image}")
            print(f"  Supports img2img: {info.supports_img2img}")
            print(f"  Dimensions: {info.dimensions_behavior}")
            print(f"  Best for: {', '.join(info.best_for)}")
            if info.notes:
                print(f"  Notes: {info.notes}")
        else:
            print(f"Unknown model: {args.model}")
    elif args.task:
        model = get_model_for_task(args.task, args.tier)
        print(f"Best model for '{args.task}' at {args.tier} tier: {model}")
    else:
        config = get_model_config(args.tier)
        print(f"Tier: {config.name}")
        print(f"txt2img: {config.txt2img_model}")
        print(f"img2img: {config.img2img_model}")
        print(f"vision:  {config.vision_model}")
