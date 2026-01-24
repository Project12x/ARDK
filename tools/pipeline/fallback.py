"""
Fallback Strategies for Offline Mode (Phase 0.7)

When AI providers are unavailable (--offline mode or API failures),
these heuristic-based methods provide reasonable sprite labeling
based on position, size, and image analysis.

Usage:
    from pipeline.fallback import FallbackAnalyzer

    analyzer = FallbackAnalyzer()
    labels = analyzer.analyze_sprites(img, sprites)
"""

import os
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
from PIL import Image
import math

from .platforms import SpriteInfo, BoundingBox, CollisionMask


class FallbackAnalyzer:
    """
    Heuristic-based sprite analyzer for offline mode.

    Uses position, size, and simple image features to guess sprite types.
    Not as accurate as AI, but works without network access.
    """

    # Size-based type hints (width, height ranges)
    SIZE_HINTS = {
        'tiny': (0, 12),      # 8-12px: likely projectiles, particles
        'small': (12, 20),    # 12-20px: items, pickups, small enemies
        'medium': (20, 40),   # 20-40px: standard sprites, player, enemies
        'large': (40, 64),    # 40-64px: bosses, large enemies
        'huge': (64, 256),    # 64+: UI elements, backgrounds, big bosses
    }

    # Position-based hints (normalized 0-1)
    POSITION_HINTS = {
        'top': (0.0, 0.3),    # Top third: UI, HUD, health bars
        'middle': (0.3, 0.7), # Middle: gameplay sprites
        'bottom': (0.7, 1.0), # Bottom: ground items, shadows
    }

    def __init__(self, filename_hints: bool = True):
        """
        Initialize fallback analyzer.

        Args:
            filename_hints: Use filename patterns to infer types
        """
        self.filename_hints = filename_hints

    def analyze_sprites(self, img: Image.Image, sprites: List[SpriteInfo],
                       filename: str = None) -> Dict[str, Any]:
        """
        Analyze sprites using heuristics instead of AI.

        Args:
            img: Source sprite sheet image
            sprites: List of detected SpriteInfo objects
            filename: Original filename for hints

        Returns:
            Dict with sprite analysis results matching AI format
        """
        results = {'sprites': []}

        # Extract filename hints if available
        file_type_hint = None
        if filename and self.filename_hints:
            file_type_hint = self._extract_filename_hints(filename)

        # Get image dimensions for position normalization
        img_width, img_height = img.size

        # Analyze each sprite
        for sprite in sprites:
            sprite_result = self._analyze_single_sprite(
                sprite, img_width, img_height, file_type_hint
            )
            results['sprites'].append(sprite_result)

        # Post-process: Look for animation sequences
        results = self._detect_animation_sequences(results, sprites)

        return results

    def _analyze_single_sprite(self, sprite: SpriteInfo,
                               img_width: int, img_height: int,
                               file_type_hint: Optional[str]) -> Dict[str, Any]:
        """Analyze a single sprite using heuristics."""
        bbox = sprite.bbox

        # Determine size category
        size_category = self._get_size_category(bbox.width, bbox.height)

        # Determine position category
        center_y = (bbox.y + bbox.height / 2) / img_height
        pos_category = self._get_position_category(center_y)

        # Infer sprite type based on size and position
        sprite_type = self._infer_type(size_category, pos_category, file_type_hint)

        # Infer action based on sprite characteristics
        action = self._infer_action(sprite, size_category)

        # Generate description
        description = f"{sprite_type}_{action}_{sprite.id}"

        return {
            'id': sprite.id,
            'type': sprite_type,
            'action': action,
            'description': description,
            'confidence': 0.5,  # Lower confidence for heuristics
            'method': 'fallback_heuristic',
            'size_category': size_category,
        }

    def _get_size_category(self, width: int, height: int) -> str:
        """Categorize sprite by size."""
        max_dim = max(width, height)

        for category, (min_size, max_size) in self.SIZE_HINTS.items():
            if min_size <= max_dim < max_size:
                return category
        return 'medium'

    def _get_position_category(self, normalized_y: float) -> str:
        """Categorize sprite by vertical position."""
        for category, (min_y, max_y) in self.POSITION_HINTS.items():
            if min_y <= normalized_y < max_y:
                return category
        return 'middle'

    def _infer_type(self, size_category: str, pos_category: str,
                    file_hint: Optional[str]) -> str:
        """Infer sprite type from size, position, and filename hints."""
        # Filename hint takes priority
        if file_hint:
            return file_hint

        # Size-based inference
        if size_category == 'tiny':
            return 'projectile'
        elif size_category == 'small':
            return 'item'
        elif size_category == 'large' or size_category == 'huge':
            return 'boss'

        # Position-based inference for medium sprites
        if pos_category == 'top':
            return 'ui'
        elif pos_category == 'bottom':
            return 'item'

        # Default for medium middle sprites
        return 'character'

    def _infer_action(self, sprite: SpriteInfo, size_category: str) -> str:
        """Infer action based on sprite characteristics."""
        bbox = sprite.bbox

        # Aspect ratio can hint at action
        aspect = bbox.width / bbox.height if bbox.height > 0 else 1.0

        if aspect > 1.3:
            # Wide sprites often indicate movement/running
            return 'run'
        elif aspect < 0.7:
            # Tall sprites might be jumping or falling
            return 'jump'

        # Size-based action hints
        if size_category == 'tiny':
            return 'fly'
        elif size_category == 'small':
            return 'idle'

        return 'idle'

    def _extract_filename_hints(self, filename: str) -> Optional[str]:
        """Extract type hints from filename patterns."""
        name_lower = filename.lower()

        # Common filename patterns
        patterns = {
            'player': ['player', 'hero', 'char', 'protagonist', 'main'],
            'enemy': ['enemy', 'mob', 'monster', 'baddie', 'foe'],
            'boss': ['boss', 'big', 'giant', 'mega'],
            'item': ['item', 'pickup', 'powerup', 'collect', 'coin', 'gem'],
            'projectile': ['bullet', 'shot', 'projectile', 'missile', 'laser'],
            'vfx': ['effect', 'vfx', 'particle', 'explosion', 'spark'],
            'ui': ['ui', 'hud', 'icon', 'button', 'menu', 'font'],
            'background': ['bg', 'background', 'tile', 'level', 'map'],
        }

        for sprite_type, keywords in patterns.items():
            for keyword in keywords:
                if keyword in name_lower:
                    return sprite_type

        return None

    def _detect_animation_sequences(self, results: Dict[str, Any],
                                    sprites: List[SpriteInfo]) -> Dict[str, Any]:
        """Detect and label animation sequences based on sprite layout."""
        if len(sprites) < 2:
            return results

        # Group sprites by row (similar Y position)
        rows = {}
        tolerance = 8  # Pixels

        for sprite, result in zip(sprites, results['sprites']):
            row_y = sprite.bbox.y // tolerance
            if row_y not in rows:
                rows[row_y] = []
            rows[row_y].append((sprite, result))

        # Label sprites in rows as animation frames
        for row_sprites in rows.values():
            if len(row_sprites) >= 2:
                # Sort by X position
                row_sprites.sort(key=lambda x: x[0].bbox.x)

                # Check if sprites are similar size (animation frames)
                widths = [s[0].bbox.width for s in row_sprites]
                heights = [s[0].bbox.height for s in row_sprites]

                width_var = max(widths) - min(widths)
                height_var = max(heights) - min(heights)

                if width_var <= 4 and height_var <= 4:
                    # Likely animation sequence
                    base_type = row_sprites[0][1]['type']

                    # Assign frame indices and animation actions
                    for frame_idx, (sprite, result) in enumerate(row_sprites):
                        result['frame_index'] = frame_idx
                        result['total_frames'] = len(row_sprites)
                        result['is_animation'] = True

                        # Refine action based on frame count
                        if len(row_sprites) >= 6:
                            result['action'] = 'walk'
                        elif len(row_sprites) >= 4:
                            result['action'] = 'run'
                        elif len(row_sprites) == 2:
                            result['action'] = 'idle'

        return results

    def generate_collision(self, sprite: SpriteInfo) -> CollisionMask:
        """
        Generate a basic collision mask using heuristics.

        Default strategy: hitbox is inner 70%, hurtbox is inner 90%.
        """
        bbox = sprite.bbox

        # Calculate hitbox (inner 70%)
        hit_margin_x = int(bbox.width * 0.15)
        hit_margin_y = int(bbox.height * 0.15)
        hitbox = BoundingBox(
            x=hit_margin_x,
            y=hit_margin_y,
            width=max(1, bbox.width - 2 * hit_margin_x),
            height=max(1, bbox.height - 2 * hit_margin_y)
        )

        # Calculate hurtbox (inner 90%)
        hurt_margin_x = int(bbox.width * 0.05)
        hurt_margin_y = int(bbox.height * 0.05)
        hurtbox = BoundingBox(
            x=hurt_margin_x,
            y=hurt_margin_y,
            width=max(1, bbox.width - 2 * hurt_margin_x),
            height=max(1, bbox.height - 2 * hurt_margin_y)
        )

        return CollisionMask(
            hitbox=hitbox,
            hurtbox=hurtbox,
            pixel_mask=None,
            mask_type='aabb',
            confidence=0.4  # Lower confidence for heuristic
        )


def get_fallback_labels(sprites: List[SpriteInfo],
                        img: Image.Image,
                        filename: str = None) -> Dict[str, Any]:
    """
    Convenience function for quick fallback labeling.

    Args:
        sprites: List of detected sprites
        img: Source image
        filename: Original filename for hints

    Returns:
        AI-compatible analysis result dict
    """
    analyzer = FallbackAnalyzer()
    return analyzer.analyze_sprites(img, sprites, filename)


def apply_fallback_collision(sprites: List[SpriteInfo]) -> List[SpriteInfo]:
    """
    Apply heuristic collision masks to all sprites.

    Args:
        sprites: List of sprites to process

    Returns:
        Same list with collision masks added
    """
    analyzer = FallbackAnalyzer()

    for sprite in sprites:
        if sprite.collision is None:
            sprite.collision = analyzer.generate_collision(sprite)

    return sprites
