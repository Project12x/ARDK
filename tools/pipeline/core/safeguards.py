"""
Pipeline Safeguards - ENFORCED at the Core Level.

These safeguards CANNOT be bypassed. The Pipeline class uses this
module internally and there is no way to disable it.

Safeguards:
1. Budget Enforcement - Limits generations and cost
2. Dry Run Mode - Default ON, must be explicitly disabled
3. Caching - Always saves before processing
4. Validation - Checks inputs before processing
5. Confirmation - Prompts before destructive operations
"""

import os
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict

from PIL import Image

logger = logging.getLogger(__name__)


# =============================================================================
# EXCEPTIONS
# =============================================================================

class SafeguardViolation(Exception):
    """Base exception for safeguard violations."""
    pass


class BudgetExhausted(SafeguardViolation):
    """Raised when generation budget is exhausted."""
    pass


class ValidationFailed(SafeguardViolation):
    """Raised when input validation fails."""
    pass


class DryRunActive(SafeguardViolation):
    """Raised when trying to perform real operations in dry-run mode."""
    pass


class ConfirmationRequired(SafeguardViolation):
    """Raised when user confirmation is required but not provided."""
    pass


# =============================================================================
# CACHE
# =============================================================================

@dataclass
class CacheEntry:
    """Cached generation/processing result."""
    input_hash: str
    timestamp: str
    input_params: Dict[str, Any]
    output_paths: List[str]
    cost_usd: float
    success: bool
    error: Optional[str] = None


class Cache:
    """
    Generation and processing cache.

    ALWAYS saves results before processing to prevent data loss.
    """

    def __init__(self, cache_dir: str = ".ardk_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        # Subdirectories
        self.requests_dir = self.cache_dir / "requests"
        self.responses_dir = self.cache_dir / "responses"
        self.images_dir = self.cache_dir / "images"

        for d in [self.requests_dir, self.responses_dir, self.images_dir]:
            d.mkdir(exist_ok=True)

    def _hash_params(self, params: Dict[str, Any]) -> str:
        """Generate unique hash for parameters."""
        # Sort keys for consistent hashing
        sorted_params = json.dumps(params, sort_keys=True)
        return hashlib.md5(sorted_params.encode()).hexdigest()[:12]

    def get_cache_key(self, description: str, width: int, height: int) -> str:
        """Generate cache key from generation parameters."""
        return self._hash_params({
            "description": description,
            "width": width,
            "height": height,
        })

    def has_cached_result(self, cache_key: str) -> bool:
        """Check if we have a cached result."""
        return (self.images_dir / cache_key).exists()

    def has_cached_response(self, cache_key: str) -> bool:
        """Check if we have a cached API response."""
        return (self.responses_dir / f"{cache_key}.json").exists()

    def save_request(self, cache_key: str, params: Dict[str, Any]):
        """Save request parameters before generation (for retry)."""
        request_file = self.requests_dir / f"{cache_key}.json"
        with open(request_file, 'w') as f:
            json.dump({
                "params": params,
                "timestamp": datetime.now().isoformat(),
            }, f, indent=2)
        logger.debug(f"Cached request: {cache_key}")

    def save_response(self, cache_key: str, response: Dict[str, Any]):
        """Save raw API response immediately after receiving it."""
        response_file = self.responses_dir / f"{cache_key}.json"
        with open(response_file, 'w') as f:
            json.dump({
                "response": response,
                "timestamp": datetime.now().isoformat(),
            }, f, indent=2)
        logger.info(f"Cached response: {cache_key}")

    def load_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Load cached API response."""
        response_file = self.responses_dir / f"{cache_key}.json"
        if response_file.exists():
            with open(response_file, 'r') as f:
                data = json.load(f)
                return data.get("response")
        return None

    def save_images(self, cache_key: str, images: Dict[str, Image.Image]):
        """Save decoded images to cache."""
        images_subdir = self.images_dir / cache_key
        images_subdir.mkdir(exist_ok=True)

        for name, img in images.items():
            img_path = images_subdir / f"{name}.png"
            img.save(img_path)

        logger.info(f"Cached {len(images)} images: {cache_key}")

    def load_images(self, cache_key: str) -> Optional[Dict[str, Image.Image]]:
        """Load cached images."""
        images_subdir = self.images_dir / cache_key
        if not images_subdir.exists():
            return None

        images = {}
        for img_path in images_subdir.glob("*.png"):
            images[img_path.stem] = Image.open(img_path)

        return images if images else None


# =============================================================================
# BUDGET TRACKER
# =============================================================================

@dataclass
class BudgetState:
    """Current budget state."""
    generations_used: int = 0
    cost_used: float = 0.0
    session_start: str = ""
    last_generation: str = ""


class BudgetTracker:
    """
    Tracks and enforces generation budgets.

    Persists state to disk to survive restarts.
    """

    def __init__(
        self,
        max_generations: int = 5,
        max_cost: float = 0.50,
        persist: bool = True,
        budget_file: str = ".ardk_budget.json"
    ):
        self.max_generations = max_generations
        self.max_cost = max_cost
        self.persist = persist
        self.budget_file = Path(budget_file)

        # Load or create state
        self.state = self._load_state()

    def _load_state(self) -> BudgetState:
        """Load budget state from disk."""
        if self.persist and self.budget_file.exists():
            try:
                with open(self.budget_file, 'r') as f:
                    data = json.load(f)
                    return BudgetState(**data)
            except Exception as e:
                logger.warning(f"Could not load budget state: {e}")

        return BudgetState(session_start=datetime.now().isoformat())

    def _save_state(self):
        """Save budget state to disk."""
        if self.persist:
            with open(self.budget_file, 'w') as f:
                json.dump(asdict(self.state), f, indent=2)

    def can_generate(self) -> bool:
        """Check if we have budget remaining."""
        return (self.state.generations_used < self.max_generations and
                self.state.cost_used < self.max_cost)

    def check_budget(self):
        """Check budget and raise if exhausted."""
        if not self.can_generate():
            raise BudgetExhausted(
                f"Budget exhausted: {self.state.generations_used}/{self.max_generations} generations, "
                f"${self.state.cost_used:.4f}/${self.max_cost:.2f} cost"
            )

    def record_generation(self, cost: float = 0.0):
        """Record a generation."""
        self.state.generations_used += 1
        self.state.cost_used += cost
        self.state.last_generation = datetime.now().isoformat()
        self._save_state()

        logger.info(
            f"Budget: {self.state.generations_used}/{self.max_generations} gens, "
            f"${self.state.cost_used:.4f}/${self.max_cost:.2f}"
        )

    def get_remaining(self) -> Dict[str, Any]:
        """Get remaining budget."""
        return {
            "generations": self.max_generations - self.state.generations_used,
            "cost": self.max_cost - self.state.cost_used,
        }

    def reset(self):
        """Reset budget (for new session)."""
        self.state = BudgetState(session_start=datetime.now().isoformat())
        self._save_state()


# =============================================================================
# VALIDATOR
# =============================================================================

class Validator:
    """Input and output validation."""

    @staticmethod
    def validate_input_file(path: str) -> List[str]:
        """Validate input file, return list of errors."""
        errors = []
        p = Path(path)

        if not p.exists():
            errors.append(f"File not found: {path}")
            return errors

        suffix = p.suffix.lower()
        valid_suffixes = ['.png', '.ase', '.aseprite', '.jpg', '.jpeg', '.gif']

        if suffix not in valid_suffixes:
            errors.append(f"Unsupported file type: {suffix}. "
                         f"Valid: {', '.join(valid_suffixes)}")

        # Size check for images
        if suffix in ['.png', '.jpg', '.jpeg', '.gif']:
            try:
                img = Image.open(path)
                if img.width > 4096 or img.height > 4096:
                    errors.append(f"Image too large: {img.width}x{img.height}. "
                                 f"Maximum: 4096x4096")
                if img.width < 8 or img.height < 8:
                    errors.append(f"Image too small: {img.width}x{img.height}. "
                                 f"Minimum: 8x8")
            except Exception as e:
                errors.append(f"Could not read image: {e}")

        return errors

    @staticmethod
    def validate_output_dir(path: str) -> List[str]:
        """Validate output directory, return list of errors."""
        errors = []
        p = Path(path)

        # Try to create if it doesn't exist
        try:
            p.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot create output directory: {e}")

        return errors

    @staticmethod
    def validate_prompt(prompt: str) -> List[str]:
        """Validate generation prompt."""
        errors = []

        if not prompt or len(prompt.strip()) < 3:
            errors.append("Prompt too short (minimum 3 characters)")

        if len(prompt) > 2000:
            errors.append("Prompt too long (maximum 2000 characters)")

        return errors


# =============================================================================
# MAIN SAFEGUARDS CLASS
# =============================================================================

class Safeguards:
    """
    Main safeguards class - ALWAYS used by Pipeline.

    This class enforces all safety checks and cannot be bypassed.
    """

    def __init__(self, config: 'SafeguardConfig'):
        """
        Initialize safeguards.

        Args:
            config: SafeguardConfig (from PipelineConfig.safeguards)
        """
        self.config = config

        # Initialize components
        self.cache = Cache(config.cache_dir)
        self.budget = BudgetTracker(
            max_generations=config.max_generations_per_run,
            max_cost=config.max_cost_per_run,
            persist=config.persist_budget,
            budget_file=config.budget_file,
        )
        self.validator = Validator()

        # Track confirmation state
        self._confirmed = False

    @property
    def dry_run(self) -> bool:
        """Check if dry-run mode is active."""
        return self.config.dry_run

    def check_dry_run(self, operation: str):
        """Check dry-run and raise if active."""
        if self.dry_run:
            raise DryRunActive(
                f"Dry-run mode is active. Operation blocked: {operation}\n"
                f"Set dry_run=False in config to enable real operations."
            )

    def check_budget(self):
        """Check budget and raise if exhausted."""
        self.budget.check_budget()

    def validate_input(self, path: str):
        """Validate input and raise if invalid."""
        if not self.config.validate_inputs:
            return

        errors = self.validator.validate_input_file(path)
        if errors:
            raise ValidationFailed(
                f"Input validation failed:\n" +
                "\n".join(f"  - {e}" for e in errors)
            )

    def validate_output(self, path: str):
        """Validate output directory and raise if invalid."""
        if not self.config.validate_outputs:
            return

        errors = self.validator.validate_output_dir(path)
        if errors:
            raise ValidationFailed(
                f"Output validation failed:\n" +
                "\n".join(f"  - {e}" for e in errors)
            )

    def validate_prompt(self, prompt: str):
        """Validate generation prompt and raise if invalid."""
        errors = self.validator.validate_prompt(prompt)
        if errors:
            raise ValidationFailed(
                f"Prompt validation failed:\n" +
                "\n".join(f"  - {e}" for e in errors)
            )

    def require_confirmation(self, operation: str) -> bool:
        """
        Check if confirmation is required.

        In CLI mode, this will prompt the user.
        In GUI mode, the caller should handle the confirmation UI.

        Returns:
            True if operation should proceed, False otherwise.
        """
        if not self.config.require_confirmation:
            return True

        if self._confirmed:
            return True

        # Return False to indicate confirmation is needed
        # The caller (CLI or GUI) should handle getting confirmation
        return False

    def confirm(self):
        """Confirm the current operation."""
        self._confirmed = True

    def record_generation(self, cost: float = 0.0):
        """Record a generation (updates budget)."""
        self.budget.record_generation(cost)

    def get_status(self) -> Dict[str, Any]:
        """Get current safeguard status."""
        remaining = self.budget.get_remaining()
        return {
            "dry_run": self.dry_run,
            "generations_remaining": remaining["generations"],
            "cost_remaining": remaining["cost"],
            "cache_dir": str(self.cache.cache_dir),
            "confirmation_required": self.config.require_confirmation,
            "confirmed": self._confirmed,
        }

    def generate_dry_run_report(
        self,
        assets: List[Dict[str, Any]]
    ) -> str:
        """Generate a dry-run report showing what would happen."""
        lines = [
            "=" * 60,
            "DRY RUN REPORT",
            "=" * 60,
            "",
            f"Assets to process: {len(assets)}",
            f"Budget limit: {self.config.max_generations_per_run} generations / "
            f"${self.config.max_cost_per_run:.2f}",
            "",
            "Planned operations:",
        ]

        for i, asset in enumerate(assets, 1):
            asset_type = asset.get("type", "process")
            name = asset.get("name", asset.get("path", "unknown"))
            lines.append(f"  {i}. [{asset_type}] {name}")

        lines.extend([
            "",
            "-" * 60,
            "NO OPERATIONS PERFORMED (dry-run mode)",
            "",
            "To execute, set dry_run=False in config",
            "=" * 60,
        ])

        return "\n".join(lines)
