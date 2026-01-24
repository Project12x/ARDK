"""
PixelLab Generation Safeguards Module

Provides:
- Generation caching (avoid re-generating on decode failure)
- Result persistence (save raw JSON before processing)
- Budget enforcement
- Dry-run mode support
- Mirror optimization for 5-direction sprites
"""

import os
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field, asdict
from PIL import Image

logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class SafetyConfig:
    """Configuration for generation safeguards."""
    max_generations_per_run: int = 5
    max_cost_per_run: float = 0.50
    require_confirmation: bool = True
    cache_dir: str = ".pixellab_cache"
    dry_run: bool = False

# Default config
DEFAULT_SAFETY = SafetyConfig()

# =============================================================================
# CACHE MANAGEMENT
# =============================================================================

class GenerationCache:
    """
    Caches generation results to prevent re-generating on decode failure.
    
    Cache structure:
    .pixellab_cache/
      {prompt_hash}/
        request.json      # Original request params
        response.json     # Raw API response
        images/           # Decoded images (if successful)
    """
    
    def __init__(self, cache_dir: str = ".pixellab_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _hash_prompt(self, description: str, width: int, height: int) -> str:
        """Generate cache key from generation parameters."""
        key = f"{description}|{width}x{height}"
        return hashlib.md5(key.encode()).hexdigest()[:12]
    
    def get_cache_path(self, description: str, width: int, height: int) -> Path:
        """Get the cache directory for a specific generation."""
        hash_key = self._hash_prompt(description, width, height)
        return self.cache_dir / hash_key
    
    def has_cached_response(self, description: str, width: int, height: int) -> bool:
        """Check if we have a cached response (can retry decode without re-gen)."""
        cache_path = self.get_cache_path(description, width, height)
        return (cache_path / "response.json").exists()
    
    def has_cached_images(self, description: str, width: int, height: int) -> bool:
        """Check if we have fully decoded cached images (skip entirely)."""
        cache_path = self.get_cache_path(description, width, height)
        images_dir = cache_path / "images"
        return images_dir.exists() and len(list(images_dir.glob("*.png"))) > 0
    
    def save_request(self, description: str, width: int, height: int, 
                     request_params: Dict) -> Path:
        """Save request parameters before generation."""
        cache_path = self.get_cache_path(description, width, height)
        cache_path.mkdir(parents=True, exist_ok=True)
        
        request_file = cache_path / "request.json"
        with open(request_file, 'w') as f:
            json.dump({
                "description": description,
                "width": width,
                "height": height,
                "params": request_params,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)
        
        logger.info(f"Cached request to {cache_path}")
        return cache_path
    
    def save_response(self, description: str, width: int, height: int,
                      response: Dict) -> Path:
        """Save raw API response immediately after generation."""
        cache_path = self.get_cache_path(description, width, height)
        cache_path.mkdir(parents=True, exist_ok=True)
        
        response_file = cache_path / "response.json"
        with open(response_file, 'w') as f:
            json.dump(response, f, indent=2)
        
        logger.info(f"Cached response to {response_file}")
        return response_file
    
    def load_response(self, description: str, width: int, height: int) -> Optional[Dict]:
        """Load cached response for retry decode."""
        cache_path = self.get_cache_path(description, width, height)
        response_file = cache_path / "response.json"
        
        if response_file.exists():
            with open(response_file, 'r') as f:
                return json.load(f)
        return None
    
    def save_images(self, description: str, width: int, height: int,
                    images: Dict[str, Image.Image]) -> Path:
        """Save decoded images to cache."""
        cache_path = self.get_cache_path(description, width, height)
        images_dir = cache_path / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        
        for direction, img in images.items():
            img_path = images_dir / f"{direction}.png"
            img.save(img_path)
        
        logger.info(f"Cached {len(images)} images to {images_dir}")
        return images_dir
    
    def load_images(self, description: str, width: int, height: int) -> Optional[Dict[str, Image.Image]]:
        """Load cached images."""
        cache_path = self.get_cache_path(description, width, height)
        images_dir = cache_path / "images"
        
        if not images_dir.exists():
            return None
        
        images = {}
        for img_path in images_dir.glob("*.png"):
            direction = img_path.stem
            images[direction] = Image.open(img_path)
        
        return images if images else None

# =============================================================================
# BUDGET TRACKING
# =============================================================================

@dataclass
class BudgetTracker:
    """Tracks generation cost and count for the current run."""
    max_generations: int = 5
    max_cost: float = 0.50
    generations_used: int = 0
    cost_used: float = 0.0
    
    def can_generate(self) -> bool:
        """Check if we have budget remaining."""
        return (self.generations_used < self.max_generations and 
                self.cost_used < self.max_cost)
    
    def record_generation(self, cost: float = 0.0):
        """Record a generation."""
        self.generations_used += 1
        self.cost_used += cost
        logger.info(f"Budget: {self.generations_used}/{self.max_generations} gens, "
                    f"${self.cost_used:.4f}/${self.max_cost:.2f}")
    
    def get_remaining(self) -> Dict:
        """Get remaining budget."""
        return {
            "generations": self.max_generations - self.generations_used,
            "cost": self.max_cost - self.cost_used
        }

# =============================================================================
# MIRROR OPTIMIZATION
# =============================================================================

# Direction mappings for mirror optimization
# Key: direction to generate, Value: None (unique) or direction to mirror from
DIRECTION_MIRRORS = {
    "south": None,           # Unique
    "south-west": None,      # Unique
    "west": None,            # Unique
    "north-west": None,      # Unique
    "north": None,           # Unique
    "north-east": "north-west",  # Mirror
    "east": "west",              # Mirror
    "south-east": "south-west",  # Mirror
}

def get_unique_directions() -> List[str]:
    """Get list of directions that need to be generated (not mirrored)."""
    return [d for d, mirror in DIRECTION_MIRRORS.items() if mirror is None]

def get_mirrored_directions() -> Dict[str, str]:
    """Get mapping of directions that can be mirrored."""
    return {d: m for d, m in DIRECTION_MIRRORS.items() if m is not None}

def apply_mirror_optimization(images: Dict[str, Image.Image]) -> Dict[str, Image.Image]:
    """
    Create mirrored versions for east-facing directions.
    
    Args:
        images: Dict with at least the 5 unique directions
        
    Returns:
        Dict with all 8 directions (5 unique + 3 mirrored)
    """
    result = images.copy()
    
    for target_dir, source_dir in get_mirrored_directions().items():
        if source_dir in images and target_dir not in result:
            # Create horizontally flipped version
            result[target_dir] = images[source_dir].transpose(Image.FLIP_LEFT_RIGHT)
            logger.debug(f"Created {target_dir} by mirroring {source_dir}")
    
    return result

# =============================================================================
# DRY RUN
# =============================================================================

def estimate_cost(num_characters: int, directions_per_char: int = 8) -> Dict:
    """
    Estimate API cost for a generation run.
    
    Based on observed costs:
    - 8-direction character: ~$0.008-0.015
    - Single sprite: ~$0.002-0.005
    """
    cost_per_8dir = 0.012  # Average
    cost_per_single = 0.003
    
    if directions_per_char == 8:
        total = num_characters * cost_per_8dir
    elif directions_per_char == 5:
        total = num_characters * cost_per_8dir * 0.625  # 5/8 of cost
    else:
        total = num_characters * cost_per_single
    
    return {
        "estimated_cost_usd": total,
        "generations": num_characters,
        "note": "Estimates based on observed API costs"
    }

def dry_run_report(assets: List[Dict], config: SafetyConfig) -> str:
    """
    Generate a dry-run report showing what would be generated.
    
    Args:
        assets: List of asset definitions
        config: Safety configuration
        
    Returns:
        Formatted report string
    """
    lines = [
        "=" * 60,
        "DRY RUN REPORT",
        "=" * 60,
        "",
        f"Assets to generate: {len(assets)}",
        f"Budget limit: {config.max_generations_per_run} generations / ${config.max_cost_per_run:.2f}",
        "",
        "Planned generations:",
    ]
    
    total_est_cost = 0.0
    for i, asset in enumerate(assets, 1):
        asset_type = asset.get("type", "single")
        name = asset.get("name", "unknown")
        desc = asset.get("description", "")[:40]
        
        if asset_type == "8way":
            est = estimate_cost(1, 8)
        elif asset_type == "5way":
            est = estimate_cost(1, 5)
        else:
            est = estimate_cost(1, 1)
        
        total_est_cost += est["estimated_cost_usd"]
        lines.append(f"  {i}. [{asset_type}] {name}: ~${est['estimated_cost_usd']:.4f}")
        lines.append(f"      \"{desc}...\"")
    
    lines.extend([
        "",
        "-" * 60,
        f"ESTIMATED TOTAL: ${total_est_cost:.4f}",
        "",
        "NO API CALLS MADE (dry-run mode)",
        "=" * 60,
    ])
    
    return "\n".join(lines)
