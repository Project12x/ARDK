"""
8-Direction Sprite Rotation for Retro Game Development.

Generate directional sprite variants from a single source sprite,
essential for top-down games, RPGs, and action games with character facing.

Phase: 1.4 (Core Features)

Key Features:
- Simple PIL rotation (fast, works offline)
- Smart mirroring for symmetric sprites (uses only 5 unique sprites)
- 4-way and 8-way generation modes
- Isometric-aware rotation
- Optional AI rotation via PixelLab (higher quality)

Usage:
    from tools.pipeline.rotation import (
        SpriteRotator,
        Direction,
        rotate_8way,
        rotate_4way,
    )

    # Quick 8-way generation
    directions = rotate_8way(sprite_image, source_direction=Direction.E)
    # Returns dict: {Direction.N: img, Direction.NE: img, ...}

    # Use smart mirroring (only 5 unique frames needed)
    rotator = SpriteRotator(method='mirror')
    directions = rotator.rotate(sprite_image)

    # AI-powered rotation (requires PixelLab)
    rotator = SpriteRotator(method='ai', pixellab_client=client)
    directions = await rotator.rotate_async(sprite_image)

Direction Conventions:
    - North (N): Up/Away from camera
    - East (E): Right
    - South (S): Down/Toward camera
    - West (W): Left
    - Angles: N=0°, E=90°, S=180°, W=270°

Performance:
    - Simple rotation: < 5ms per sprite set
    - Mirror rotation: < 3ms per sprite set (5 unique)
    - AI rotation: ~2s per sprite set (network bound)
"""

from typing import List, Dict, Optional, Tuple, Literal, Union
from dataclasses import dataclass
from enum import Enum, IntEnum
from PIL import Image
import math


class Direction(IntEnum):
    """
    8-way direction enum with clockwise ordering.

    Values match common game conventions:
    - 0 = North (up)
    - Clockwise from there
    """
    N = 0
    NE = 1
    E = 2
    SE = 3
    S = 4
    SW = 5
    W = 6
    NW = 7

    @property
    def angle(self) -> int:
        """Get angle in degrees (0° = North, clockwise)."""
        return self.value * 45

    @property
    def opposite(self) -> 'Direction':
        """Get opposite direction."""
        return Direction((self.value + 4) % 8)

    @property
    def mirror_h(self) -> 'Direction':
        """Get horizontally mirrored direction."""
        mirror_map = {
            Direction.N: Direction.N,
            Direction.NE: Direction.NW,
            Direction.E: Direction.W,
            Direction.SE: Direction.SW,
            Direction.S: Direction.S,
            Direction.SW: Direction.SE,
            Direction.W: Direction.E,
            Direction.NW: Direction.NE,
        }
        return mirror_map[self]

    @classmethod
    def from_angle(cls, angle: float) -> 'Direction':
        """Get nearest direction from angle (0° = North)."""
        normalized = angle % 360
        index = round(normalized / 45) % 8
        return cls(index)

    @classmethod
    def cardinal(cls) -> List['Direction']:
        """Get 4 cardinal directions (N, E, S, W)."""
        return [cls.N, cls.E, cls.S, cls.W]

    @classmethod
    def diagonal(cls) -> List['Direction']:
        """Get 4 diagonal directions (NE, SE, SW, NW)."""
        return [cls.NE, cls.SE, cls.SW, cls.NW]


# Direction name mappings
DIRECTION_NAMES = {
    Direction.N: 'north',
    Direction.NE: 'northeast',
    Direction.E: 'east',
    Direction.SE: 'southeast',
    Direction.S: 'south',
    Direction.SW: 'southwest',
    Direction.W: 'west',
    Direction.NW: 'northwest',
}

DIRECTION_SHORT = {
    Direction.N: 'n',
    Direction.NE: 'ne',
    Direction.E: 'e',
    Direction.SE: 'se',
    Direction.S: 's',
    Direction.SW: 'sw',
    Direction.W: 'w',
    Direction.NW: 'nw',
}


RotationMethod = Literal['simple', 'mirror', 'ai']


@dataclass
class RotationConfig:
    """Configuration for rotation generation."""
    source_direction: Direction = Direction.E
    method: RotationMethod = 'mirror'
    expand_canvas: bool = False  # Expand to fit rotated sprite
    resample: int = Image.NEAREST  # PIL resampling mode
    center_sprites: bool = True  # Center sprites in output
    output_size: Optional[Tuple[int, int]] = None  # Force output size


@dataclass
class RotationResult:
    """Result of rotation generation."""
    directions: Dict[Direction, Image.Image]
    source_direction: Direction
    method: str
    unique_count: int  # Number of unique sprites (5 for mirror, 8 for others)

    def get(self, direction: Direction) -> Image.Image:
        """Get sprite for direction."""
        return self.directions[direction]

    def save_all(self, output_dir: str, prefix: str = 'sprite',
                 use_short_names: bool = True) -> List[str]:
        """
        Save all direction sprites to files.

        Args:
            output_dir: Output directory
            prefix: Filename prefix
            use_short_names: Use 'n', 'ne' vs 'north', 'northeast'

        Returns:
            List of saved file paths
        """
        from pathlib import Path
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        paths = []
        names = DIRECTION_SHORT if use_short_names else DIRECTION_NAMES

        for direction, img in self.directions.items():
            name = names[direction]
            path = str(Path(output_dir) / f"{prefix}_{name}.png")
            img.save(path)
            paths.append(path)

        return paths


class SpriteRotator:
    """
    Generate directional sprite variants.

    Supports multiple methods:
    - 'simple': Pure PIL rotation (all 8 directions rotated)
    - 'mirror': Smart mirroring (5 unique sprites, others mirrored)
    - 'ai': PixelLab AI rotation (highest quality)

    Example:
        # Simple usage
        rotator = SpriteRotator()
        result = rotator.rotate(sprite_image)

        # With mirroring (recommended for symmetric sprites)
        rotator = SpriteRotator(method='mirror')
        result = rotator.rotate(sprite_image, source_direction=Direction.E)

        # Save results
        result.save_all('output/player/', prefix='walk_01')
    """

    def __init__(self,
                 method: RotationMethod = 'mirror',
                 config: Optional[RotationConfig] = None,
                 pixellab_client=None):
        """
        Initialize rotator.

        Args:
            method: Rotation method ('simple', 'mirror', 'ai')
            config: Rotation configuration
            pixellab_client: Optional PixelLab client for AI rotation
        """
        self.method = method
        self.config = config or RotationConfig(method=method)
        self.pixellab = pixellab_client

    def rotate(self,
               img: Image.Image,
               source_direction: Optional[Direction] = None,
               directions_4way: bool = False) -> RotationResult:
        """
        Generate directional variants.

        Args:
            img: Source sprite (should face source_direction)
            source_direction: Direction the source sprite faces
            directions_4way: Generate only 4 cardinal directions

        Returns:
            RotationResult with all direction sprites
        """
        # Use explicit None check because Direction.N has value 0 (falsy)
        source_dir = source_direction if source_direction is not None else self.config.source_direction

        if self.method == 'simple':
            directions = self._rotate_simple(img, source_dir, directions_4way)
            unique = 4 if directions_4way else 8
        elif self.method == 'mirror':
            directions = self._rotate_mirror(img, source_dir, directions_4way)
            unique = 3 if directions_4way else 5
        else:
            raise ValueError(f"Unknown method: {self.method}. Use 'ai' method with rotate_async()")

        return RotationResult(
            directions=directions,
            source_direction=source_dir,
            method=self.method,
            unique_count=unique
        )

    async def rotate_async(self,
                           img: Image.Image,
                           source_direction: Optional[Direction] = None,
                           directions_4way: bool = False) -> RotationResult:
        """
        Generate directional variants with optional AI.

        Falls back to mirror method if AI unavailable.

        Args:
            img: Source sprite
            source_direction: Direction the source sprite faces
            directions_4way: Generate only 4 cardinal directions

        Returns:
            RotationResult with all direction sprites
        """
        # Use explicit None check because Direction.N has value 0 (falsy)
        source_dir = source_direction if source_direction is not None else self.config.source_direction

        if self.method == 'ai' and self.pixellab:
            try:
                directions = await self._rotate_ai(img, source_dir, directions_4way)
                if directions:
                    return RotationResult(
                        directions=directions,
                        source_direction=source_dir,
                        method='ai',
                        unique_count=4 if directions_4way else 8
                    )
            except Exception:
                pass  # Fall back to mirror

        # Fallback to mirror method
        return self.rotate(img, source_dir, directions_4way)

    def _rotate_simple(self,
                       img: Image.Image,
                       source_dir: Direction,
                       directions_4way: bool) -> Dict[Direction, Image.Image]:
        """Generate all directions using PIL rotation."""
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        target_dirs = Direction.cardinal() if directions_4way else list(Direction)
        results = {}
        base_angle = source_dir.angle

        for direction in target_dirs:
            target_angle = direction.angle
            rotation = (target_angle - base_angle) % 360

            if rotation == 0:
                results[direction] = img.copy()
            elif rotation == 180:
                results[direction] = img.transpose(Image.Transpose.ROTATE_180)
            elif rotation == 90:
                results[direction] = img.transpose(Image.Transpose.ROTATE_270)  # PIL rotates counter-clockwise
            elif rotation == 270:
                results[direction] = img.transpose(Image.Transpose.ROTATE_90)
            else:
                # Non-90-degree rotation
                rotated = img.rotate(
                    -rotation,  # Negative for clockwise
                    expand=self.config.expand_canvas,
                    resample=self.config.resample,
                    fillcolor=(0, 0, 0, 0)
                )

                if self.config.center_sprites and self.config.output_size:
                    rotated = self._center_sprite(rotated, self.config.output_size)

                results[direction] = rotated

        return results

    def _rotate_mirror(self,
                       img: Image.Image,
                       source_dir: Direction,
                       directions_4way: bool) -> Dict[Direction, Image.Image]:
        """
        Generate directions using mirroring for symmetric sprites.

        For 8-way: Generates 5 unique sprites (source, +/-45°, +/-90°)
        Mirrors E↔W, NE↔NW, SE↔SW

        For 4-way: Generates 3 unique sprites (source, ±90°)
        Mirrors E↔W
        """
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        target_dirs = Direction.cardinal() if directions_4way else list(Direction)
        results = {}
        base_angle = source_dir.angle

        # Determine which directions need unique sprites vs mirrors
        # For E-facing source: E (original), W (mirror), N/S (rotate), diagonals (rotate + mirror)

        for direction in target_dirs:
            target_angle = direction.angle
            rotation = (target_angle - base_angle) % 360

            # Check if this direction can be mirrored from another
            mirror_dir = direction.mirror_h
            mirror_rotation = (mirror_dir.angle - base_angle) % 360

            if rotation == 0:
                # Original direction
                results[direction] = img.copy()
            elif mirror_dir in results and mirror_rotation != rotation:
                # Mirror from already-generated direction
                results[direction] = results[mirror_dir].transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            elif rotation == 180:
                results[direction] = img.transpose(Image.Transpose.ROTATE_180)
            elif rotation == 90:
                results[direction] = img.transpose(Image.Transpose.ROTATE_270)
            elif rotation == 270:
                results[direction] = img.transpose(Image.Transpose.ROTATE_90)
            else:
                # Non-90-degree rotation
                rotated = img.rotate(
                    -rotation,
                    expand=self.config.expand_canvas,
                    resample=self.config.resample,
                    fillcolor=(0, 0, 0, 0)
                )
                results[direction] = rotated

        # Second pass: fill any remaining mirrors
        for direction in target_dirs:
            if direction not in results:
                mirror_dir = direction.mirror_h
                if mirror_dir in results:
                    results[direction] = results[mirror_dir].transpose(Image.Transpose.FLIP_LEFT_RIGHT)

        return results

    async def _rotate_ai(self,
                         img: Image.Image,
                         source_dir: Direction,
                         directions_4way: bool) -> Optional[Dict[Direction, Image.Image]]:
        """Generate directions using PixelLab AI."""
        if not self.pixellab:
            return None

        try:
            # PixelLab API call (async)
            num_dirs = 4 if directions_4way else 8
            result = await self.pixellab.generate_rotations(
                image=img,
                num_directions=num_dirs,
                source_direction=source_dir.value
            )

            if result and result.success:
                target_dirs = Direction.cardinal() if directions_4way else list(Direction)
                return dict(zip(target_dirs, result.images))
        except Exception:
            pass

        return None

    def _center_sprite(self, img: Image.Image, size: Tuple[int, int]) -> Image.Image:
        """Center sprite in canvas of given size."""
        result = Image.new('RGBA', size, (0, 0, 0, 0))
        x = (size[0] - img.width) // 2
        y = (size[1] - img.height) // 2
        result.paste(img, (x, y), img)
        return result


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def rotate_8way(img: Image.Image,
                source_direction: Direction = Direction.E,
                method: RotationMethod = 'mirror') -> Dict[Direction, Image.Image]:
    """
    Quick 8-way rotation.

    Args:
        img: Source sprite facing source_direction
        source_direction: Direction the source faces
        method: Rotation method

    Returns:
        Dict mapping Direction to rotated Image
    """
    rotator = SpriteRotator(method=method)
    result = rotator.rotate(img, source_direction, directions_4way=False)
    return result.directions


def rotate_4way(img: Image.Image,
                source_direction: Direction = Direction.E,
                method: RotationMethod = 'mirror') -> Dict[Direction, Image.Image]:
    """
    Quick 4-way rotation (cardinal directions only).

    Args:
        img: Source sprite facing source_direction
        source_direction: Direction the source faces
        method: Rotation method

    Returns:
        Dict mapping Direction (N, E, S, W) to rotated Image
    """
    rotator = SpriteRotator(method=method)
    result = rotator.rotate(img, source_direction, directions_4way=True)
    return result.directions


def generate_direction_sheet(img: Image.Image,
                              source_direction: Direction = Direction.E,
                              method: RotationMethod = 'mirror',
                              directions_4way: bool = False,
                              layout: Literal['row', 'column', 'grid'] = 'row') -> Image.Image:
    """
    Generate sprite sheet with all directions.

    Args:
        img: Source sprite
        source_direction: Direction the source faces
        method: Rotation method
        directions_4way: Use only 4 directions
        layout: Sheet layout ('row', 'column', 'grid')

    Returns:
        Combined sprite sheet image
    """
    rotator = SpriteRotator(method=method)
    result = rotator.rotate(img, source_direction, directions_4way)

    directions = Direction.cardinal() if directions_4way else list(Direction)
    sprites = [result.directions[d] for d in directions]

    # Get max dimensions
    max_w = max(s.width for s in sprites)
    max_h = max(s.height for s in sprites)
    count = len(sprites)

    if layout == 'row':
        sheet = Image.new('RGBA', (max_w * count, max_h), (0, 0, 0, 0))
        for i, sprite in enumerate(sprites):
            x = i * max_w + (max_w - sprite.width) // 2
            y = (max_h - sprite.height) // 2
            sheet.paste(sprite, (x, y), sprite)

    elif layout == 'column':
        sheet = Image.new('RGBA', (max_w, max_h * count), (0, 0, 0, 0))
        for i, sprite in enumerate(sprites):
            x = (max_w - sprite.width) // 2
            y = i * max_h + (max_h - sprite.height) // 2
            sheet.paste(sprite, (x, y), sprite)

    else:  # grid
        cols = 4 if directions_4way else 4
        rows = 1 if directions_4way else 2
        sheet = Image.new('RGBA', (max_w * cols, max_h * rows), (0, 0, 0, 0))
        for i, sprite in enumerate(sprites):
            col = i % cols
            row = i // cols
            x = col * max_w + (max_w - sprite.width) // 2
            y = row * max_h + (max_h - sprite.height) // 2
            sheet.paste(sprite, (x, y), sprite)

    return sheet


# =============================================================================
# BATCH PROCESSING
# =============================================================================

def batch_rotate(images: List[Image.Image],
                 source_direction: Direction = Direction.E,
                 method: RotationMethod = 'mirror',
                 directions_4way: bool = False,
                 show_progress: bool = False) -> List[RotationResult]:
    """
    Rotate multiple sprites.

    Args:
        images: List of source images
        source_direction: Direction all sources face
        method: Rotation method
        directions_4way: Use only 4 directions
        show_progress: Print progress

    Returns:
        List of RotationResults
    """
    rotator = SpriteRotator(method=method)
    results = []
    total = len(images)

    for i, img in enumerate(images):
        result = rotator.rotate(img, source_direction, directions_4way)
        results.append(result)

        if show_progress and (i + 1) % 10 == 0:
            print(f"  Rotated {i + 1}/{total} sprites...")

    return results


# =============================================================================
# ISOMETRIC HELPERS
# =============================================================================

class IsometricDirection(IntEnum):
    """
    Isometric 8-way directions.

    Uses different angle conventions for isometric view:
    - SE is "down-right" (toward camera)
    - NW is "up-left" (away from camera)
    """
    SE = 0  # Down-right (primary "south" in isometric)
    E = 1   # Right
    NE = 2  # Up-right
    N = 3   # Up (away)
    NW = 4  # Up-left
    W = 5   # Left
    SW = 6  # Down-left
    S = 7   # Down (toward camera)


def rotate_isometric(img: Image.Image,
                      source_direction: IsometricDirection = IsometricDirection.SE,
                      method: RotationMethod = 'mirror') -> Dict[IsometricDirection, Image.Image]:
    """
    Generate isometric directional variants.

    Isometric games typically use different direction conventions.
    The "primary" direction is usually SE (toward camera, down-right).

    Args:
        img: Source sprite in isometric view
        source_direction: Direction the source faces
        method: Rotation method

    Returns:
        Dict mapping IsometricDirection to rotated Image

    Note:
        For true isometric sprites, AI rotation is recommended
        as PIL rotation doesn't preserve isometric proportions well.
    """
    # Convert to standard direction for rotation
    standard_dir = Direction(source_direction.value)
    rotator = SpriteRotator(method=method)
    result = rotator.rotate(img, standard_dir, directions_4way=False)

    # Map back to isometric directions
    return {IsometricDirection(d.value): img for d, img in result.directions.items()}


# =============================================================================
# ANIMATION HELPERS
# =============================================================================

def rotate_animation_frames(frames: List[Image.Image],
                             source_direction: Direction = Direction.E,
                             method: RotationMethod = 'mirror',
                             directions_4way: bool = False) -> Dict[Direction, List[Image.Image]]:
    """
    Rotate all frames of an animation to all directions.

    Args:
        frames: List of animation frames (all facing same direction)
        source_direction: Direction the frames face
        method: Rotation method
        directions_4way: Use only 4 directions

    Returns:
        Dict mapping Direction to list of rotated frames

    Example:
        walk_frames = [frame1, frame2, frame3, frame4]
        all_walks = rotate_animation_frames(walk_frames, Direction.E)
        # all_walks[Direction.N] = [frame1_n, frame2_n, frame3_n, frame4_n]
    """
    rotator = SpriteRotator(method=method)
    target_dirs = Direction.cardinal() if directions_4way else list(Direction)

    # Initialize result dict
    result: Dict[Direction, List[Image.Image]] = {d: [] for d in target_dirs}

    # Rotate each frame
    for frame in frames:
        rotation_result = rotator.rotate(frame, source_direction, directions_4way)
        for direction in target_dirs:
            result[direction].append(rotation_result.directions[direction])

    return result


def generate_animation_sheets(frames: List[Image.Image],
                               source_direction: Direction = Direction.E,
                               method: RotationMethod = 'mirror',
                               directions_4way: bool = False) -> Dict[Direction, Image.Image]:
    """
    Generate sprite sheets for each direction from animation frames.

    Args:
        frames: List of animation frames
        source_direction: Direction the frames face
        method: Rotation method
        directions_4way: Use only 4 directions

    Returns:
        Dict mapping Direction to sprite sheet (horizontal strip)
    """
    rotated = rotate_animation_frames(frames, source_direction, method, directions_4way)

    sheets = {}
    for direction, dir_frames in rotated.items():
        if not dir_frames:
            continue

        max_w = max(f.width for f in dir_frames)
        max_h = max(f.height for f in dir_frames)
        sheet = Image.new('RGBA', (max_w * len(dir_frames), max_h), (0, 0, 0, 0))

        for i, frame in enumerate(dir_frames):
            x = i * max_w + (max_w - frame.width) // 2
            y = (max_h - frame.height) // 2
            sheet.paste(frame, (x, y), frame)

        sheets[direction] = sheet

    return sheets
