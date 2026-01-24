"""
Animation Metadata Extraction for SGDK/Genesis Sprite Pipelines.

This module auto-detects frame sequences from sprite sheets and generates
SGDK-ready animation definitions.

Phase 1.1 of the ARDK Pixel Pipeline.

Features:
    - Parse filename patterns (idle_01, walk_02, attack_03)
    - Detect animation sequences from spatial arrangement
    - Generate frame timing metadata
    - Mark loop points (one-shot vs looping)
    - Export SGDK AnimationFrame structs

Usage:
    from pipeline.animation import (
        AnimationExtractor,
        AnimationFrame,
        AnimationSequence,
        export_sgdk_animations,
    )

    # From sprite names
    extractor = AnimationExtractor()
    sequences = extractor.extract_from_names(['idle_01', 'idle_02', 'walk_01'])

    # From spatial layout (row-major sprite sheet)
    sequences = extractor.extract_spatial(
        sprite_count=12,
        frames_per_row=4,
        anim_names=['idle', 'walk', 'attack']
    )

    # Export to SGDK C header
    export_sgdk_animations(sequences, 'animations.h')
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
from pathlib import Path
import re
import json


class AnimationPattern(Enum):
    """Pattern used to detect animation frames."""
    PREFIX_NUMBER = "prefix_##"     # idle_01, idle_02
    SPATIAL = "spatial"             # Left-to-right, top-to-bottom
    AI = "ai"                       # AI-assisted grouping (future)


# Default timing by action type (frames per sprite at 60fps)
# These values are tuned for Genesis/SGDK games
DEFAULT_TIMING: Dict[str, int] = {
    'idle': 10,      # Slow breathing, ~6 frames = 1 second cycle
    'walk': 6,       # Medium pace walking
    'run': 4,        # Fast running
    'attack': 3,     # Quick strikes
    'hit': 2,        # Very fast reaction/flinch
    'hurt': 2,       # Damage reaction
    'death': 8,      # Dramatic death sequence
    'die': 8,        # Alias for death
    'jump': 5,       # Jump arc
    'fall': 5,       # Falling animation
    'land': 3,       # Landing recovery
    'shoot': 3,      # Shooting/firing
    'cast': 6,       # Spell casting
    'charge': 4,     # Charging up
    'default': 6,    # Fallback for unknown types
}

# Actions that should NOT loop (play once then return to idle)
ONE_SHOT_ACTIONS = frozenset([
    'attack', 'hit', 'hurt', 'death', 'die', 'shoot', 'cast', 'land'
])


@dataclass
class AnimationFrame:
    """
    A single frame in an animation sequence.

    Attributes:
        sprite_index: Index of this frame in the sprite sheet (0-based)
        duration: How many game frames to display this (1 frame = 1/60s on Genesis)
        hotspot_x: X offset of the pivot/origin point from top-left
        hotspot_y: Y offset of the pivot/origin point from top-left
    """
    sprite_index: int
    duration: int
    hotspot_x: int = 0
    hotspot_y: int = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'sprite_index': self.sprite_index,
            'duration': self.duration,
            'hotspot_x': self.hotspot_x,
            'hotspot_y': self.hotspot_y,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'AnimationFrame':
        """Create from dictionary."""
        return cls(
            sprite_index=data['sprite_index'],
            duration=data['duration'],
            hotspot_x=data.get('hotspot_x', 0),
            hotspot_y=data.get('hotspot_y', 0),
        )


@dataclass
class AnimationSequence:
    """
    A named sequence of animation frames.

    Attributes:
        name: Animation name (e.g., 'idle', 'walk', 'attack')
        frames: List of AnimationFrame objects
        loop: True to loop continuously, False for one-shot
    """
    name: str
    frames: List[AnimationFrame] = field(default_factory=list)
    loop: bool = True

    @property
    def frame_count(self) -> int:
        """Number of frames in this animation."""
        return len(self.frames)

    @property
    def total_duration(self) -> int:
        """Total duration in game frames (at 60fps)."""
        return sum(f.duration for f in self.frames)

    @property
    def duration_seconds(self) -> float:
        """Total duration in seconds (assuming 60fps)."""
        return self.total_duration / 60.0

    def get_frame_at_time(self, game_frame: int) -> AnimationFrame:
        """
        Get the animation frame at a given game frame.

        If looping, wraps around. If one-shot, clamps to last frame.
        """
        if not self.frames:
            raise ValueError(f"Animation '{self.name}' has no frames")

        total = self.total_duration
        if self.loop:
            game_frame = game_frame % total
        else:
            game_frame = min(game_frame, total - 1)

        elapsed = 0
        for frame in self.frames:
            elapsed += frame.duration
            if game_frame < elapsed:
                return frame

        return self.frames[-1]

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'frames': [f.to_dict() for f in self.frames],
            'loop': self.loop,
            'frame_count': self.frame_count,
            'total_duration': self.total_duration,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'AnimationSequence':
        """Create from dictionary."""
        return cls(
            name=data['name'],
            frames=[AnimationFrame.from_dict(f) for f in data['frames']],
            loop=data.get('loop', True),
        )


class AnimationExtractor:
    """
    Extract animation sequences from sprite sheets.

    Supports multiple detection patterns:
    - PREFIX_NUMBER: Parse 'prefix_##' naming (idle_01, idle_02)
    - SPATIAL: Row-major layout with specified frames per row
    """

    def __init__(self, default_duration: int = 6):
        """
        Initialize the extractor.

        Args:
            default_duration: Default frame duration when type is unknown
        """
        self.default_duration = default_duration
        self._timing = DEFAULT_TIMING.copy()

    def set_timing(self, action: str, duration: int) -> None:
        """Override timing for a specific action type."""
        self._timing[action.lower()] = duration

    def get_timing(self, action: str) -> int:
        """Get timing for an action type."""
        return self._timing.get(action.lower(), self.default_duration)

    def extract_from_names(
        self,
        sprite_names: List[str],
        custom_timing: Optional[Dict[str, int]] = None
    ) -> List[AnimationSequence]:
        """
        Extract animations from sprite names using prefix_## pattern.

        Recognizes patterns like:
        - 'idle_01', 'idle_02', 'idle_03' -> AnimationSequence('idle', 3 frames)
        - 'walk01', 'walk02' -> AnimationSequence('walk', 2 frames)
        - 'attack_1', 'attack_2' -> AnimationSequence('attack', 2 frames)

        Args:
            sprite_names: List of sprite names/filenames (without extension)
            custom_timing: Optional dict to override default timing

        Returns:
            List of AnimationSequence objects, sorted by name

        Example:
            >>> extractor = AnimationExtractor()
            >>> names = ['idle_01', 'idle_02', 'walk_01', 'walk_02', 'walk_03']
            >>> sequences = extractor.extract_from_names(names)
            >>> [s.name for s in sequences]
            ['idle', 'walk']
        """
        timing = {**self._timing, **(custom_timing or {})}
        groups: Dict[str, List[Tuple[int, int]]] = {}

        # Pattern matches: prefix + optional separator + number
        # Examples: idle_01, walk01, attack-1, run_001
        pattern = re.compile(r'^(.+?)[-_]?(\d+)$')

        for idx, name in enumerate(sprite_names):
            # Strip file extension if present
            name_clean = Path(name).stem if '.' in name else name

            match = pattern.match(name_clean)
            if match:
                prefix = match.group(1).lower()
                frame_num = int(match.group(2))

                if prefix not in groups:
                    groups[prefix] = []
                groups[prefix].append((idx, frame_num))

        sequences = []
        for prefix, frames in sorted(groups.items()):
            # Sort by frame number to ensure correct order
            frames.sort(key=lambda x: x[1])

            # Determine timing and loop behavior
            duration = timing.get(prefix, self.default_duration)
            loop = prefix not in ONE_SHOT_ACTIONS

            seq = AnimationSequence(
                name=prefix,
                frames=[
                    AnimationFrame(sprite_index=idx, duration=duration)
                    for idx, _ in frames
                ],
                loop=loop
            )
            sequences.append(seq)

        return sequences

    def extract_spatial(
        self,
        sprite_count: int,
        frames_per_row: int,
        anim_names: Optional[List[str]] = None,
        default_loop: bool = True
    ) -> List[AnimationSequence]:
        """
        Extract animations assuming row-major sprite sheet layout.

        Each row of the sprite sheet is treated as one animation.

        Args:
            sprite_count: Total number of sprites in the sheet
            frames_per_row: How many frames per animation row
            anim_names: Optional list of animation names for each row
            default_loop: Default loop setting when name doesn't indicate one-shot

        Returns:
            List of AnimationSequence objects

        Example:
            >>> extractor = AnimationExtractor()
            >>> # 12 sprites: 3 rows of 4 frames each
            >>> sequences = extractor.extract_spatial(12, 4, ['idle', 'walk', 'attack'])
            >>> [(s.name, s.frame_count) for s in sequences]
            [('idle', 4), ('walk', 4), ('attack', 4)]
        """
        sequences = []
        num_anims = sprite_count // frames_per_row

        for i in range(num_anims):
            # Determine name
            if anim_names and i < len(anim_names):
                name = anim_names[i]
            else:
                name = f"anim_{i}"

            # Determine timing and loop
            name_lower = name.lower()
            duration = self._timing.get(name_lower, self.default_duration)

            if name_lower in ONE_SHOT_ACTIONS:
                loop = False
            else:
                loop = default_loop

            start_idx = i * frames_per_row
            seq = AnimationSequence(
                name=name,
                frames=[
                    AnimationFrame(
                        sprite_index=start_idx + j,
                        duration=duration
                    )
                    for j in range(frames_per_row)
                ],
                loop=loop
            )
            sequences.append(seq)

        return sequences

    def extract_from_grid(
        self,
        rows: int,
        cols: int,
        anim_names: Optional[List[str]] = None,
        row_major: bool = True
    ) -> List[AnimationSequence]:
        """
        Extract animations from a grid-based sprite sheet.

        Args:
            rows: Number of rows in the sprite sheet
            cols: Number of columns in the sprite sheet
            anim_names: Optional names for each animation
            row_major: If True, each row is an animation. If False, each column.

        Returns:
            List of AnimationSequence objects
        """
        total_sprites = rows * cols
        if row_major:
            return self.extract_spatial(total_sprites, cols, anim_names)
        else:
            # Column-major: transpose the logic
            sequences = []
            for col in range(cols):
                if anim_names and col < len(anim_names):
                    name = anim_names[col]
                else:
                    name = f"anim_{col}"

                name_lower = name.lower()
                duration = self._timing.get(name_lower, self.default_duration)
                loop = name_lower not in ONE_SHOT_ACTIONS

                frames = [
                    AnimationFrame(
                        sprite_index=row * cols + col,
                        duration=duration
                    )
                    for row in range(rows)
                ]

                seq = AnimationSequence(name=name, frames=frames, loop=loop)
                sequences.append(seq)

            return sequences


def export_sgdk_animations(
    sequences: List[AnimationSequence],
    output_path: str,
    sprite_name: str = "sprite",
    include_guard: Optional[str] = None
) -> None:
    """
    Generate SGDK-compatible C header with animation data.

    Args:
        sequences: List of AnimationSequence objects to export
        output_path: Path to write the .h file
        sprite_name: Base name for generated symbols (e.g., 'player' -> anim_player_idle)
        include_guard: Custom include guard name (auto-generated if None)

    Output format:
        const AnimationFrame anim_player_idle[] = {
            { 0, 10, 16, 32 },  // sprite 0, 10 ticks, hotspot (16,32)
            { 1, 10, 16, 32 },
        };
        const Animation animation_player_idle = {
            anim_player_idle, 2, TRUE
        };
    """
    if include_guard is None:
        guard_name = Path(output_path).stem.upper().replace('-', '_').replace('.', '_')
        include_guard = f"_{guard_name}_H_"

    lines = [
        "// Auto-generated animation data",
        "// Generated by ARDK Pipeline (animation.py)",
        "//",
        f"// Sprite: {sprite_name}",
        f"// Animations: {len(sequences)}",
        "",
        f"#ifndef {include_guard}",
        f"#define {include_guard}",
        "",
        "#include <genesis.h>",
        "",
    ]

    # Generate forward declarations
    lines.append("// Animation declarations")
    for seq in sequences:
        c_name = f"{sprite_name}_{seq.name}".lower()
        lines.append(f"extern const AnimationFrame anim_{c_name}[];")
        lines.append(f"extern const Animation animation_{c_name};")
    lines.append("")

    # Generate frame data
    for seq in sequences:
        c_name = f"{sprite_name}_{seq.name}".lower()
        loop_str = "loop" if seq.loop else "one-shot"

        lines.append(f"// Animation: {seq.name} ({seq.frame_count} frames, {loop_str}, {seq.duration_seconds:.2f}s)")
        lines.append(f"const AnimationFrame anim_{c_name}[] = {{")

        for i, frame in enumerate(seq.frames):
            comment = f"// frame {i}"
            lines.append(
                f"    {{ {frame.sprite_index}, {frame.duration}, "
                f"{frame.hotspot_x}, {frame.hotspot_y} }},  {comment}"
            )

        lines.append("};")
        lines.append(
            f"const Animation animation_{c_name} = {{ "
            f"anim_{c_name}, {seq.frame_count}, {'TRUE' if seq.loop else 'FALSE'} "
            f"}};"
        )
        lines.append("")

    # Animation count define
    lines.append(f"#define {sprite_name.upper()}_ANIM_COUNT {len(sequences)}")
    lines.append("")

    # Animation enum for easy indexing
    lines.append(f"// Animation indices for {sprite_name}")
    lines.append(f"typedef enum {{")
    for i, seq in enumerate(sequences):
        enum_name = f"ANIM_{sprite_name.upper()}_{seq.name.upper()}"
        lines.append(f"    {enum_name} = {i},")
    lines.append(f"}} {sprite_name.capitalize()}AnimIndex;")
    lines.append("")

    lines.append(f"#endif // {include_guard}")
    lines.append("")

    # Write file
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def export_animations_json(
    sequences: List[AnimationSequence],
    output_path: str
) -> None:
    """
    Export animation data as JSON for use with other tools.

    Args:
        sequences: List of AnimationSequence objects
        output_path: Path to write the .json file
    """
    data = {
        'version': '1.0',
        'generator': 'ARDK Pipeline (animation.py)',
        'animation_count': len(sequences),
        'animations': [seq.to_dict() for seq in sequences],
    }

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def load_animations_json(json_path: str) -> List[AnimationSequence]:
    """
    Load animation data from JSON file.

    Args:
        json_path: Path to the .json file

    Returns:
        List of AnimationSequence objects
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return [AnimationSequence.from_dict(anim) for anim in data['animations']]


# =============================================================================
# PixelLab / AI Generation Integration
# =============================================================================

def create_sequence_from_frames(
    frames: List['Image.Image'],
    name: str,
    duration: Optional[int] = None,
    loop: Optional[bool] = None,
    hotspot: Optional[Tuple[int, int]] = None,
) -> AnimationSequence:
    """
    Create an AnimationSequence from a list of PIL Image frames.

    This bridges AI-generated frames (from PixelLab, Pollinations, etc.)
    with the animation metadata system.

    Args:
        frames: List of PIL Image objects (animation frames)
        name: Animation name (e.g., 'walk', 'idle', 'attack')
        duration: Frame duration in ticks (auto-detected from name if None)
        loop: Whether animation loops (auto-detected from name if None)
        hotspot: (x, y) pivot point for all frames (default: center-bottom)

    Returns:
        AnimationSequence with frames indexed 0 to len(frames)-1

    Example:
        from asset_generators.pixellab_client import PixelLabClient

        client = PixelLabClient()
        result = client.animate_with_text(
            description="pixel art knight",
            action="walk",
            n_frames=4
        )

        if result.success:
            seq = create_sequence_from_frames(
                result.images,
                name="walk",
                hotspot=(16, 32)  # center-bottom of 32x32 sprite
            )
    """
    name_lower = name.lower()

    # Auto-detect duration from action name
    if duration is None:
        duration = DEFAULT_TIMING.get(name_lower, DEFAULT_TIMING['default'])

    # Auto-detect loop behavior
    if loop is None:
        loop = name_lower not in ONE_SHOT_ACTIONS

    # Default hotspot to center-bottom (common for character sprites)
    if hotspot is None and frames:
        first_frame = frames[0]
        hotspot = (first_frame.width // 2, first_frame.height)

    hx, hy = hotspot or (0, 0)

    anim_frames = [
        AnimationFrame(
            sprite_index=i,
            duration=duration,
            hotspot_x=hx,
            hotspot_y=hy
        )
        for i in range(len(frames))
    ]

    return AnimationSequence(name=name, frames=anim_frames, loop=loop)


def assemble_sprite_sheet(
    frames: List['Image.Image'],
    frames_per_row: Optional[int] = None,
    padding: int = 0,
) -> Tuple['Image.Image', Dict]:
    """
    Assemble individual frames into a horizontal sprite sheet.

    Args:
        frames: List of PIL Image objects (must be same size)
        frames_per_row: Frames per row (default: all in one row)
        padding: Pixels between frames (default: 0)

    Returns:
        Tuple of (sprite_sheet_image, metadata_dict)

    Example:
        sheet, meta = assemble_sprite_sheet(result.images)
        sheet.save("player_walk.png")
        # meta = {'width': 128, 'height': 32, 'frame_width': 32, ...}
    """
    try:
        from PIL import Image
    except ImportError:
        raise ImportError("PIL required: pip install pillow")

    if not frames:
        raise ValueError("No frames provided")

    # Get frame dimensions (assume all same size)
    frame_w = frames[0].width
    frame_h = frames[0].height

    # Calculate sheet dimensions
    if frames_per_row is None:
        frames_per_row = len(frames)

    num_rows = (len(frames) + frames_per_row - 1) // frames_per_row
    sheet_w = frames_per_row * frame_w + (frames_per_row - 1) * padding
    sheet_h = num_rows * frame_h + (num_rows - 1) * padding

    # Create sheet with transparency
    sheet = Image.new('RGBA', (sheet_w, sheet_h), (0, 0, 0, 0))

    # Paste frames
    for i, frame in enumerate(frames):
        row = i // frames_per_row
        col = i % frames_per_row
        x = col * (frame_w + padding)
        y = row * (frame_h + padding)

        # Ensure RGBA
        if frame.mode != 'RGBA':
            frame = frame.convert('RGBA')

        sheet.paste(frame, (x, y))

    metadata = {
        'width': sheet_w,
        'height': sheet_h,
        'frame_width': frame_w,
        'frame_height': frame_h,
        'frame_count': len(frames),
        'frames_per_row': frames_per_row,
        'num_rows': num_rows,
        'padding': padding,
    }

    return sheet, metadata


def generate_animation_bundle(
    frames: List['Image.Image'],
    name: str,
    output_dir: str,
    sprite_name: str = "sprite",
    duration: Optional[int] = None,
    hotspot: Optional[Tuple[int, int]] = None,
) -> Dict[str, str]:
    """
    Generate a complete animation bundle: sprite sheet + metadata + SGDK header.

    This is the main integration point for AI-generated animations.

    Args:
        frames: List of PIL Image objects from AI generation
        name: Animation name (e.g., 'walk', 'idle')
        output_dir: Directory to write output files
        sprite_name: Base name for files (e.g., 'player' -> player_walk.png)
        duration: Frame duration (auto-detected if None)
        hotspot: Pivot point (auto-detected if None)

    Returns:
        Dict with paths to generated files:
        {
            'sheet': 'output/player_walk.png',
            'json': 'output/player_walk.json',
            'header': 'output/player_walk.h',
        }

    Example:
        from asset_generators.pixellab_client import PixelLabClient, generate_genesis_animation

        client = PixelLabClient()
        frames = generate_genesis_animation(client, "knight", action="walk", n_frames=6)

        if frames:
            paths = generate_animation_bundle(
                frames,
                name="walk",
                output_dir="res/sprites",
                sprite_name="player"
            )
            print(f"Generated: {paths}")
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    base_name = f"{sprite_name}_{name}"

    # 1. Create animation sequence metadata
    sequence = create_sequence_from_frames(
        frames, name, duration=duration, hotspot=hotspot
    )

    # 2. Assemble sprite sheet
    sheet, sheet_meta = assemble_sprite_sheet(frames)
    sheet_path = output_path / f"{base_name}.png"
    sheet.save(sheet_path)

    # 3. Export JSON metadata
    json_path = output_path / f"{base_name}.json"
    full_meta = {
        'version': '1.0',
        'generator': 'ARDK Pipeline (animation.py)',
        'sprite_sheet': str(sheet_path.name),
        'sheet': sheet_meta,
        'animations': [sequence.to_dict()],
    }
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(full_meta, f, indent=2)

    # 4. Export SGDK C header
    header_path = output_path / f"{base_name}.h"
    export_sgdk_animations([sequence], str(header_path), sprite_name=sprite_name)

    return {
        'sheet': str(sheet_path),
        'json': str(json_path),
        'header': str(header_path),
    }


def generate_multi_animation_bundle(
    animations: Dict[str, List['Image.Image']],
    output_dir: str,
    sprite_name: str = "sprite",
    combine_sheet: bool = True,
) -> Dict[str, str]:
    """
    Generate a bundle with multiple animations (idle, walk, attack, etc.).

    Args:
        animations: Dict mapping animation names to frame lists
                   e.g., {'idle': [img1, img2], 'walk': [img1, img2, img3, img4]}
        output_dir: Directory to write output files
        sprite_name: Base name for files
        combine_sheet: If True, combine all animations into one sheet

    Returns:
        Dict with paths to generated files

    Example:
        animations = {
            'idle': client.animate_with_text(..., action='idle').images,
            'walk': client.animate_with_text(..., action='walk').images,
            'attack': client.animate_with_text(..., action='attack').images,
        }

        paths = generate_multi_animation_bundle(
            animations,
            output_dir="res/sprites",
            sprite_name="player"
        )
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    sequences = []
    all_frames = []
    frame_offset = 0

    # Build sequences with correct frame offsets
    for anim_name, frames in animations.items():
        if not frames:
            continue

        # Auto-detect hotspot from first frame
        hotspot = (frames[0].width // 2, frames[0].height)
        duration = DEFAULT_TIMING.get(anim_name.lower(), DEFAULT_TIMING['default'])
        loop = anim_name.lower() not in ONE_SHOT_ACTIONS

        anim_frames = [
            AnimationFrame(
                sprite_index=frame_offset + i,
                duration=duration,
                hotspot_x=hotspot[0],
                hotspot_y=hotspot[1]
            )
            for i in range(len(frames))
        ]

        sequences.append(AnimationSequence(name=anim_name, frames=anim_frames, loop=loop))
        all_frames.extend(frames)
        frame_offset += len(frames)

    if not sequences:
        raise ValueError("No valid animations provided")

    # Determine frames per row (use first animation's frame count, or 8 max)
    first_anim_frames = len(list(animations.values())[0])
    frames_per_row = min(first_anim_frames, 8)

    # Assemble combined sheet
    if combine_sheet:
        sheet, sheet_meta = assemble_sprite_sheet(all_frames, frames_per_row=frames_per_row)
        sheet_path = output_path / f"{sprite_name}_sheet.png"
        sheet.save(sheet_path)
    else:
        # Save individual sheets per animation
        sheet_path = output_path / f"{sprite_name}_sheet.png"
        sheet, sheet_meta = assemble_sprite_sheet(all_frames, frames_per_row=frames_per_row)
        sheet.save(sheet_path)

    # Export JSON with all animations
    json_path = output_path / f"{sprite_name}_animations.json"
    full_meta = {
        'version': '1.0',
        'generator': 'ARDK Pipeline (animation.py)',
        'sprite_sheet': str(sheet_path.name),
        'sheet': sheet_meta,
        'animation_count': len(sequences),
        'animations': [seq.to_dict() for seq in sequences],
    }
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(full_meta, f, indent=2)

    # Export combined SGDK header
    header_path = output_path / f"{sprite_name}_animations.h"
    export_sgdk_animations(sequences, str(header_path), sprite_name=sprite_name)

    return {
        'sheet': str(sheet_path),
        'json': str(json_path),
        'header': str(header_path),
        'animation_count': len(sequences),
        'total_frames': len(all_frames),
    }


def split_sprite_sheet(
    sheet_image: 'Image.Image',
    frame_width: int,
    frame_height: int,
    frames_per_row: Optional[int] = None,
    total_frames: Optional[int] = None,
    trim_empty: bool = True,
) -> List['Image.Image']:
    """
    Split a sprite sheet image into individual frames.

    Works with any AI-generated sprite sheet (PixelLab, Pollinations, DALL-E, etc.)
    where frames are arranged in a grid.

    Args:
        sheet_image: PIL Image of the sprite sheet
        frame_width: Width of each frame in pixels
        frame_height: Height of each frame in pixels
        frames_per_row: Frames per row (auto-detected if None)
        total_frames: Total frames to extract (auto-detected if None)
        trim_empty: Skip fully transparent frames

    Returns:
        List of PIL Image objects (individual frames)

    Example:
        # AI generates a sprite sheet
        sheet = pollinations.generate_image(
            "8-frame pixel art walk cycle sprite sheet, 32x32 per frame",
            width=256, height=32
        )

        # Split into frames
        frames = split_sprite_sheet(sheet, frame_width=32, frame_height=32)
        # frames = [img1, img2, img3, img4, img5, img6, img7, img8]
    """
    try:
        from PIL import Image
    except ImportError:
        raise ImportError("PIL required: pip install pillow")

    sheet_w, sheet_h = sheet_image.size

    # Auto-detect frames per row
    if frames_per_row is None:
        frames_per_row = sheet_w // frame_width

    # Calculate total possible frames
    rows = sheet_h // frame_height
    max_frames = frames_per_row * rows

    if total_frames is None:
        total_frames = max_frames

    total_frames = min(total_frames, max_frames)

    frames = []
    for i in range(total_frames):
        row = i // frames_per_row
        col = i % frames_per_row

        x = col * frame_width
        y = row * frame_height

        frame = sheet_image.crop((x, y, x + frame_width, y + frame_height))

        # Convert to RGBA if needed
        if frame.mode != 'RGBA':
            frame = frame.convert('RGBA')

        # Check if frame is empty (fully transparent)
        if trim_empty:
            bbox = frame.getbbox()
            if bbox is None:
                continue  # Skip empty frames

        frames.append(frame)

    return frames


def generate_sprite_sheet_prompt(
    character_desc: str,
    action: str,
    frame_count: int = 4,
    frame_size: int = 32,
    style: str = "pixel art",
    direction: str = "side view",
) -> str:
    """
    Generate an optimized prompt for AI sprite sheet generation.

    Use this with any image model (Pollinations, DALL-E, Midjourney, etc.)
    to request a properly formatted sprite sheet.

    Args:
        character_desc: Character description (e.g., "knight with sword")
        action: Animation action (e.g., "walk", "run", "attack")
        frame_count: Number of frames in the animation
        frame_size: Size of each frame in pixels
        style: Art style description
        direction: View direction

    Returns:
        Optimized prompt string for sprite sheet generation

    Example:
        prompt = generate_sprite_sheet_prompt(
            character_desc="blue slime monster",
            action="idle bounce",
            frame_count=4,
            frame_size=32
        )
        # Returns: "pixel art sprite sheet, 4 frames horizontal strip, ..."

        # Use with any AI:
        sheet = pollinations.generate_image(prompt, width=128, height=32)
        frames = split_sprite_sheet(sheet, 32, 32)
    """
    # Calculate sheet dimensions
    sheet_width = frame_count * frame_size
    sheet_height = frame_size

    prompt_parts = [
        f"{style} sprite sheet",
        f"{frame_count} frames horizontal strip",
        f"{frame_size}x{frame_size} pixels per frame",
        f"{character_desc}",
        f"{action} animation cycle",
        f"{direction}",
        "transparent background",
        "evenly spaced frames",
        "consistent character design across all frames",
        "no frame borders or gaps",
        f"total image size {sheet_width}x{sheet_height}",
    ]

    return ", ".join(prompt_parts)


def generate_animation_from_sheet(
    sheet_image: 'Image.Image',
    name: str,
    frame_width: int,
    frame_height: int,
    output_dir: str,
    sprite_name: str = "sprite",
    frames_per_row: Optional[int] = None,
    total_frames: Optional[int] = None,
    duration: Optional[int] = None,
) -> Dict[str, str]:
    """
    Complete pipeline: AI sprite sheet → split frames → animation bundle.

    This is the main entry point for processing AI-generated sprite sheets
    from any provider (Pollinations, DALL-E, Stable Diffusion, etc.).

    Args:
        sheet_image: PIL Image of sprite sheet from AI
        name: Animation name (e.g., 'walk', 'idle')
        frame_width: Width of each frame
        frame_height: Height of each frame
        output_dir: Directory to write output files
        sprite_name: Base name for files
        frames_per_row: Frames per row (auto-detect if None)
        total_frames: Total frames to extract (auto-detect if None)
        duration: Frame duration in ticks (auto-detect if None)

    Returns:
        Dict with paths to generated files (same as generate_animation_bundle)

    Example:
        from asset_generators.base_generator import PollinationsClient

        pollinations = PollinationsClient()

        # Generate sprite sheet with AI
        prompt = generate_sprite_sheet_prompt("warrior", "walk", 6, 32)
        sheet = pollinations.generate_image(prompt, width=192, height=32)

        # Process into animation bundle
        paths = generate_animation_from_sheet(
            sheet_image=sheet,
            name="walk",
            frame_width=32,
            frame_height=32,
            output_dir="res/sprites",
            sprite_name="player"
        )
        # Creates: player_walk.png, player_walk.json, player_walk.h
    """
    # 1. Split sheet into frames
    frames = split_sprite_sheet(
        sheet_image,
        frame_width=frame_width,
        frame_height=frame_height,
        frames_per_row=frames_per_row,
        total_frames=total_frames,
    )

    if not frames:
        raise ValueError("No frames extracted from sprite sheet")

    # 2. Generate animation bundle from frames
    return generate_animation_bundle(
        frames=frames,
        name=name,
        output_dir=output_dir,
        sprite_name=sprite_name,
        duration=duration,
        hotspot=(frame_width // 2, frame_height),  # Center-bottom
    )


def batch_generate_from_sheets(
    sheets: Dict[str, Tuple['Image.Image', int, int]],
    output_dir: str,
    sprite_name: str = "sprite",
) -> Dict[str, str]:
    """
    Process multiple AI-generated sheets into a combined animation bundle.

    Args:
        sheets: Dict mapping animation names to (sheet_image, frame_width, frame_height)
               e.g., {'walk': (walk_sheet, 32, 32), 'idle': (idle_sheet, 32, 32)}
        output_dir: Directory to write output files
        sprite_name: Base name for files

    Returns:
        Dict with paths to combined output files

    Example:
        pollinations = PollinationsClient()

        # Generate multiple sheets
        sheets = {}
        for action in ['idle', 'walk', 'attack']:
            prompt = generate_sprite_sheet_prompt("knight", action, 4, 32)
            sheet = pollinations.generate_image(prompt, width=128, height=32)
            sheets[action] = (sheet, 32, 32)

        # Process all into combined bundle
        paths = batch_generate_from_sheets(sheets, "res/sprites", "player")
    """
    # Split all sheets into frame lists
    animations = {}
    for anim_name, (sheet, fw, fh) in sheets.items():
        frames = split_sprite_sheet(sheet, fw, fh)
        if frames:
            animations[anim_name] = frames

    if not animations:
        raise ValueError("No valid animations extracted from sheets")

    # Generate combined bundle
    return generate_multi_animation_bundle(
        animations=animations,
        output_dir=output_dir,
        sprite_name=sprite_name,
    )


__all__ = [
    # Enums
    'AnimationPattern',
    # Data classes
    'AnimationFrame',
    'AnimationSequence',
    # Constants
    'DEFAULT_TIMING',
    'ONE_SHOT_ACTIONS',
    # Classes
    'AnimationExtractor',
    # Export functions
    'export_sgdk_animations',
    'export_animations_json',
    'load_animations_json',
    # AI/PixelLab integration (frame-based)
    'create_sequence_from_frames',
    'assemble_sprite_sheet',
    'generate_animation_bundle',
    'generate_multi_animation_bundle',
    # Sprite sheet processing (any AI model)
    'split_sprite_sheet',
    'generate_sprite_sheet_prompt',
    'generate_animation_from_sheet',
    'batch_generate_from_sheets',
]
