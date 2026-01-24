"""
Animated Tile Generator - Generate animated background tiles.

Features:
- Generate tile animation sequences (water, fire, lights, etc.)
- Per-tile animation with configurable frame counts
- CHR bank animation support for NES
- Seamless tile animation loops
- Integration with background generator for animated backgrounds
"""

import os
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFilter
    import numpy as np
except ImportError:
    raise ImportError("PIL and numpy required: pip install pillow numpy")

from .base_generator import (
    AssetGenerator, GeneratedAsset, GenerationFlags,
    PlatformConfig, get_nes_config
)

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from tile_optimizers.tile_deduplicator import TileDeduplicator


# =============================================================================
# Animation Presets
# =============================================================================

TILE_ANIMATION_PRESETS = {
    'water': {
        'frames': 4,
        'speed_ms': 150,
        'description': 'Flowing water with wave movement',
        'style_hint': 'horizontal wave pattern, blue tones, subtle motion',
    },
    'water_deep': {
        'frames': 4,
        'speed_ms': 200,
        'description': 'Deep water with slow undulation',
        'style_hint': 'darker blue, slower vertical movement, depth',
    },
    'lava': {
        'frames': 4,
        'speed_ms': 120,
        'description': 'Flowing lava/magma',
        'style_hint': 'red-orange glow, bubbling, bright spots',
    },
    'fire': {
        'frames': 4,
        'speed_ms': 80,
        'description': 'Flickering fire/flames',
        'style_hint': 'yellow-orange-red gradient, upward flicker',
    },
    'torch': {
        'frames': 3,
        'speed_ms': 100,
        'description': 'Wall torch flame',
        'style_hint': 'small flame, warm glow, mounted bracket',
    },
    'waterfall': {
        'frames': 4,
        'speed_ms': 100,
        'description': 'Vertical waterfall',
        'style_hint': 'vertical flow, white foam, blue water',
    },
    'neon_sign': {
        'frames': 2,
        'speed_ms': 500,
        'description': 'Flickering neon sign',
        'style_hint': 'bright color, slight flicker/buzz effect',
    },
    'neon_glow': {
        'frames': 4,
        'speed_ms': 200,
        'description': 'Pulsing neon glow',
        'style_hint': 'color pulse, synthwave aesthetic',
    },
    'stars': {
        'frames': 4,
        'speed_ms': 300,
        'description': 'Twinkling stars',
        'style_hint': 'dark background, bright points that vary',
    },
    'computer_screen': {
        'frames': 2,
        'speed_ms': 400,
        'description': 'CRT monitor with changing display',
        'style_hint': 'green/blue text lines, scanlines, flicker',
    },
    'electric': {
        'frames': 4,
        'speed_ms': 60,
        'description': 'Electric sparks/arcs',
        'style_hint': 'white-blue jagged lines, random paths',
    },
    'pulse': {
        'frames': 4,
        'speed_ms': 150,
        'description': 'Generic pulsing/glowing effect',
        'style_hint': 'brightness variation, smooth transition',
    },
    'conveyor': {
        'frames': 4,
        'speed_ms': 100,
        'description': 'Moving conveyor belt',
        'style_hint': 'horizontal stripes moving, metal surface',
    },
    'fan': {
        'frames': 4,
        'speed_ms': 50,
        'description': 'Spinning fan blades',
        'style_hint': 'rotating blades, motion blur at edges',
    },
}


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class AnimatedTile:
    """A single animated tile with multiple frames."""

    name: str
    preset: str
    frames: List[Image.Image]
    frame_count: int
    speed_ms: int
    palette: List[int]

    # Tile position (if part of a tileset)
    tile_x: int = 0
    tile_y: int = 0

    # CHR data for each frame
    chr_frames: List[bytes] = field(default_factory=list)

    @property
    def total_chr_size(self) -> int:
        return sum(len(f) for f in self.chr_frames)


@dataclass
class AnimatedTileset:
    """Collection of animated tiles for a background."""

    name: str
    animated_tiles: List[AnimatedTile]
    static_tiles: Optional[Image.Image] = None

    # Combined CHR data
    chr_banks: List[bytes] = field(default_factory=list)
    frame_count: int = 4

    # Animation metadata
    animation_table: List[Dict] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


# =============================================================================
# Animated Tile Generator
# =============================================================================

class AnimatedTileGenerator(AssetGenerator):
    """Generate animated background tiles."""

    def __init__(
        self,
        platform: Optional[PlatformConfig] = None,
        api_key: Optional[str] = None,
    ):
        """Initialize animated tile generator."""
        platform = platform or get_nes_config()
        super().__init__(platform, api_key)

        self.deduplicator = TileDeduplicator(
            tile_width=platform.tile_width,
            tile_height=platform.tile_height,
            enable_h_flip=platform.enable_flip_optimization,
            enable_v_flip=platform.enable_flip_optimization,
        )

    def generate(self, description: str, **kwargs) -> GeneratedAsset:
        """Generate animated tile as GeneratedAsset."""
        preset = kwargs.get('preset', 'water')
        tile = self.generate_animated_tile(description, preset)

        # Use first frame as representative image
        return GeneratedAsset(
            name=tile.name,
            image=tile.frames[0] if tile.frames else Image.new('RGB', (8, 8)),
            palette=tile.palette,
            chr_data=tile.chr_frames[0] if tile.chr_frames else b'',
            metadata={
                'type': 'animated_tile',
                'frame_count': tile.frame_count,
                'speed_ms': tile.speed_ms,
                'preset': preset,
            },
        )

    def optimize(self, asset: GeneratedAsset) -> GeneratedAsset:
        """Optimize is done during generation."""
        return asset

    # -------------------------------------------------------------------------
    # Main Generation Methods
    # -------------------------------------------------------------------------

    def generate_animated_tile(
        self,
        description: str,
        preset: str = 'water',
        frame_count: Optional[int] = None,
        speed_ms: Optional[int] = None,
    ) -> AnimatedTile:
        """
        Generate a single animated tile.

        Args:
            description: What the tile should look like
            preset: Animation preset (water, fire, neon, etc.)
            frame_count: Override frame count from preset
            speed_ms: Override animation speed from preset

        Returns:
            AnimatedTile with all frames generated
        """
        preset_config = TILE_ANIMATION_PRESETS.get(preset, TILE_ANIMATION_PRESETS['pulse'])

        frame_count = frame_count or preset_config['frames']
        speed_ms = speed_ms or preset_config['speed_ms']

        # Build prompt for tile generation
        prompt = self._build_tile_animation_prompt(
            description,
            preset,
            preset_config,
            frame_count,
        )

        # Generate animation strip
        strip_width = self.platform.tile_width * frame_count
        strip_height = self.platform.tile_height

        raw_strip = self.client.generate_image(
            prompt=prompt,
            width=max(256, strip_width * 8),  # Generate larger for quality
            height=max(64, strip_height * 8),
            model='flux',
        )

        # Resize to exact tile dimensions
        raw_strip = raw_strip.resize(
            (strip_width, strip_height),
            Image.NEAREST
        )

        # Split into frames
        frames = self._split_strip_to_frames(raw_strip, frame_count)

        # Ensure frames loop seamlessly
        frames = self._ensure_seamless_loop(frames)

        # Extract unified palette
        palette = self._extract_tile_palette(frames)

        # Convert frames to CHR
        chr_frames = []
        for frame in frames:
            frame_indexed = self._apply_palette(frame, palette)
            chr_data = self._tile_to_chr(frame_indexed)
            chr_frames.append(chr_data)

        # Create name
        name = self._sanitize_name(description)

        return AnimatedTile(
            name=name,
            preset=preset,
            frames=frames,
            frame_count=frame_count,
            speed_ms=speed_ms,
            palette=palette,
            chr_frames=chr_frames,
        )

    def generate_animated_tileset(
        self,
        tile_definitions: List[Dict],
        base_description: str = "",
    ) -> AnimatedTileset:
        """
        Generate a complete animated tileset.

        Args:
            tile_definitions: List of tile specs, each with:
                - name: Tile name
                - preset: Animation preset
                - description: Tile-specific description
                - tile_x, tile_y: Position in tileset (optional)
            base_description: Base scene description for consistency

        Returns:
            AnimatedTileset with all tiles
        """
        animated_tiles = []
        max_frames = 4

        for tile_def in tile_definitions:
            name = tile_def.get('name', 'tile')
            preset = tile_def.get('preset', 'pulse')
            desc = tile_def.get('description', f'{base_description} {name}')

            tile = self.generate_animated_tile(desc, preset)

            # Set position if provided
            tile.tile_x = tile_def.get('tile_x', 0)
            tile.tile_y = tile_def.get('tile_y', 0)

            animated_tiles.append(tile)
            max_frames = max(max_frames, tile.frame_count)

        # Build animation table for runtime
        animation_table = self._build_animation_table(animated_tiles)

        # Combine CHR data into banks
        chr_banks = self._build_chr_banks(animated_tiles, max_frames)

        return AnimatedTileset(
            name=self._sanitize_name(base_description or "tileset"),
            animated_tiles=animated_tiles,
            chr_banks=chr_banks,
            frame_count=max_frames,
            animation_table=animation_table,
            metadata={
                'tile_count': len(animated_tiles),
                'max_frames': max_frames,
            },
        )

    # -------------------------------------------------------------------------
    # Prompt Building
    # -------------------------------------------------------------------------

    def _build_tile_animation_prompt(
        self,
        description: str,
        preset: str,
        preset_config: Dict,
        frame_count: int,
    ) -> str:
        """Build prompt for tile animation generation."""

        style = self._build_style_prompt()

        prompt = f"""[ARDK_ANIMATED_TILE]
Create an animated tile strip: {description}

ANIMATION TYPE: {preset} - {preset_config['description']}

STRIP FORMAT:
- {frame_count} frames arranged horizontally
- Each frame is {self.platform.tile_width}x{self.platform.tile_height} pixels
- Total strip: {self.platform.tile_width * frame_count}x{self.platform.tile_height} pixels

STYLE: {style}

ANIMATION HINTS:
- {preset_config['style_hint']}
- Frame 1 and last frame should connect for seamless loop
- Smooth transition between consecutive frames
- Consistent palette across all frames

TECHNICAL:
- Limited palette ({self.platform.colors_per_palette} colors)
- Clean pixel edges, no anti-aliasing
- Each frame should be tileable (connects to copies of itself)
"""
        return prompt

    # -------------------------------------------------------------------------
    # Frame Processing
    # -------------------------------------------------------------------------

    def _split_strip_to_frames(
        self,
        strip: Image.Image,
        frame_count: int,
    ) -> List[Image.Image]:
        """Split animation strip into individual frames."""
        frame_width = strip.width // frame_count
        frames = []

        for i in range(frame_count):
            x = i * frame_width
            frame = strip.crop((x, 0, x + frame_width, strip.height))
            frames.append(frame)

        return frames

    def _ensure_seamless_loop(
        self,
        frames: List[Image.Image],
    ) -> List[Image.Image]:
        """Ensure animation loops seamlessly from last to first frame."""
        if len(frames) < 2:
            return frames

        # Use AI to verify/fix loop continuity
        first_arr = np.array(frames[0])
        last_arr = np.array(frames[-1])

        # Check similarity between last and first
        diff = np.mean(np.abs(first_arr.astype(float) - last_arr.astype(float)))

        if diff > 50:  # Significant difference
            # Blend last frame toward first
            alpha = 0.3
            blended = (last_arr.astype(float) * (1 - alpha) +
                      first_arr.astype(float) * alpha).astype(np.uint8)
            frames[-1] = Image.fromarray(blended)

        return frames

    def _extract_tile_palette(
        self,
        frames: List[Image.Image],
    ) -> List[int]:
        """Extract unified palette from all animation frames."""

        # Combine all frames for palette extraction
        combined_width = frames[0].width * len(frames)
        combined = Image.new('RGB', (combined_width, frames[0].height))

        for i, frame in enumerate(frames):
            if frame.mode != 'RGB':
                frame = frame.convert('RGB')
            combined.paste(frame, (i * frame.width, 0))

        # Use AI palette extraction
        return self._extract_palette_ai(
            combined,
            num_colors=self.platform.colors_per_palette
        )

    def _apply_palette(
        self,
        image: Image.Image,
        palette: List[int],
    ) -> np.ndarray:
        """Apply palette to image, returning indexed array."""

        if image.mode != 'RGB':
            image = image.convert('RGB')

        arr = np.array(image)
        height, width = arr.shape[:2]

        # Create indexed output
        indexed = np.zeros((height, width), dtype=np.uint8)

        # Simple nearest-color matching
        for y in range(height):
            for x in range(width):
                r, g, b = arr[y, x]
                brightness = (r + g + b) // 3

                # Map to palette index based on brightness
                if brightness < 32:
                    indexed[y, x] = 0
                elif brightness < 96:
                    indexed[y, x] = 1
                elif brightness < 192:
                    indexed[y, x] = 2
                else:
                    indexed[y, x] = 3

        return indexed

    def _tile_to_chr(self, indexed: np.ndarray) -> bytes:
        """Convert indexed tile to CHR format."""

        height, width = indexed.shape

        if self.platform.name == 'NES':
            # NES 2bpp format (16 bytes per 8x8 tile)
            return self._tile_to_2bpp(indexed)
        else:
            # Genesis/SNES 4bpp format
            return self._tile_to_4bpp(indexed)

    def _tile_to_2bpp(self, indexed: np.ndarray) -> bytes:
        """Convert to NES 2bpp CHR format."""
        data = bytearray()

        height, width = indexed.shape
        for tile_y in range(height // 8):
            for tile_x in range(width // 8):
                # Low bitplane
                for row in range(8):
                    byte = 0
                    for col in range(8):
                        y = tile_y * 8 + row
                        x = tile_x * 8 + col
                        if y < height and x < width:
                            byte |= ((indexed[y, x] & 1) << (7 - col))
                    data.append(byte)

                # High bitplane
                for row in range(8):
                    byte = 0
                    for col in range(8):
                        y = tile_y * 8 + row
                        x = tile_x * 8 + col
                        if y < height and x < width:
                            byte |= (((indexed[y, x] >> 1) & 1) << (7 - col))
                    data.append(byte)

        return bytes(data)

    def _tile_to_4bpp(self, indexed: np.ndarray) -> bytes:
        """Convert to 4bpp CHR format."""
        data = bytearray()

        height, width = indexed.shape
        for tile_y in range(height // 8):
            for tile_x in range(width // 8):
                for row in range(8):
                    for plane in range(4):
                        byte = 0
                        for col in range(8):
                            y = tile_y * 8 + row
                            x = tile_x * 8 + col
                            if y < height and x < width:
                                bit = (indexed[y, x] >> plane) & 1
                                byte |= (bit << (7 - col))
                        data.append(byte)

        return bytes(data)

    # -------------------------------------------------------------------------
    # CHR Bank Building
    # -------------------------------------------------------------------------

    def _build_chr_banks(
        self,
        tiles: List[AnimatedTile],
        max_frames: int,
    ) -> List[bytes]:
        """Build CHR banks for animated tiles."""

        banks = []

        for frame_idx in range(max_frames):
            bank_data = bytearray()

            for tile in tiles:
                if frame_idx < len(tile.chr_frames):
                    bank_data.extend(tile.chr_frames[frame_idx])
                else:
                    # Repeat last frame if this tile has fewer frames
                    bank_data.extend(tile.chr_frames[-1])

            banks.append(bytes(bank_data))

        return banks

    def _build_animation_table(
        self,
        tiles: List[AnimatedTile],
    ) -> List[Dict]:
        """Build runtime animation table."""

        table = []

        for tile in tiles:
            table.append({
                'name': tile.name,
                'preset': tile.preset,
                'frame_count': tile.frame_count,
                'speed_ms': tile.speed_ms,
                'tile_x': tile.tile_x,
                'tile_y': tile.tile_y,
            })

        return table

    # -------------------------------------------------------------------------
    # Output Methods
    # -------------------------------------------------------------------------

    def save_animated_tile(
        self,
        tile: AnimatedTile,
        output_dir: str,
    ) -> Dict[str, str]:
        """Save animated tile to files."""

        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        created_files = {}

        # Save each frame CHR
        for i, chr_data in enumerate(tile.chr_frames):
            chr_path = out_path / f"{tile.name}_frame{i}.chr"
            with open(chr_path, 'wb') as f:
                f.write(chr_data)
            created_files[f'frame_{i}_chr'] = str(chr_path)

        # Save frame images
        for i, frame in enumerate(tile.frames):
            img_path = out_path / f"{tile.name}_frame{i}.png"
            frame.save(img_path)
            created_files[f'frame_{i}_png'] = str(img_path)

        # Save animation strip
        strip_width = tile.frames[0].width * len(tile.frames)
        strip = Image.new('RGB', (strip_width, tile.frames[0].height))
        for i, frame in enumerate(tile.frames):
            if frame.mode != 'RGB':
                frame = frame.convert('RGB')
            strip.paste(frame, (i * frame.width, 0))
        strip_path = out_path / f"{tile.name}_strip.png"
        strip.save(strip_path)
        created_files['strip'] = str(strip_path)

        # Save metadata
        metadata = {
            'name': tile.name,
            'preset': tile.preset,
            'frame_count': tile.frame_count,
            'speed_ms': tile.speed_ms,
            'palette': tile.palette,
            'tile_size': [self.platform.tile_width, self.platform.tile_height],
        }
        meta_path = out_path / "metadata.json"
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        created_files['metadata'] = str(meta_path)

        # Save assembly include
        inc_path = out_path / f"{tile.name}.inc"
        self._write_animation_include(tile, inc_path)
        created_files['include'] = str(inc_path)

        return created_files

    def save_animated_tileset(
        self,
        tileset: AnimatedTileset,
        output_dir: str,
    ) -> Dict[str, str]:
        """Save animated tileset to files."""

        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        created_files = {}

        # Save CHR banks
        for i, bank in enumerate(tileset.chr_banks):
            bank_path = out_path / f"{tileset.name}_frame{i}.chr"
            with open(bank_path, 'wb') as f:
                f.write(bank)
            created_files[f'chr_bank_{i}'] = str(bank_path)

        # Save metadata
        metadata = {
            'name': tileset.name,
            'tile_count': len(tileset.animated_tiles),
            'frame_count': tileset.frame_count,
            'animation_table': tileset.animation_table,
            **tileset.metadata,
        }
        meta_path = out_path / "metadata.json"
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        created_files['metadata'] = str(meta_path)

        # Save assembly include
        inc_path = out_path / f"{tileset.name}.inc"
        self._write_tileset_include(tileset, inc_path)
        created_files['include'] = str(inc_path)

        return created_files

    def _write_animation_include(self, tile: AnimatedTile, path: Path) -> None:
        """Write assembly include for animated tile."""

        content = f"""; =============================================================================
; {tile.name} - Animated Tile Data
; Generated by ARDK Animated Tile Generator
; =============================================================================
; Preset: {tile.preset}
; Frames: {tile.frame_count}
; Speed: {tile.speed_ms}ms per frame
; =============================================================================

{tile.name.upper()}_FRAME_COUNT = {tile.frame_count}
{tile.name.upper()}_SPEED_MS = {tile.speed_ms}
{tile.name.upper()}_SPEED_FRAMES = {tile.speed_ms // 16}  ; ~60fps

; Palette
{tile.name.upper()}_PALETTE:
    .byte ${tile.palette[0]:02X}, ${tile.palette[1]:02X}, ${tile.palette[2]:02X}, ${tile.palette[3]:02X}

; Frame data references (each frame is 16 bytes for 8x8 tile)
; .incbin "{tile.name}_frame0.chr"
; .incbin "{tile.name}_frame1.chr"
; etc.
"""

        with open(path, 'w') as f:
            f.write(content)

    def _write_tileset_include(self, tileset: AnimatedTileset, path: Path) -> None:
        """Write assembly include for animated tileset."""

        tile_entries = "\n".join([
            f"    ; {t['name']}: preset={t['preset']}, frames={t['frame_count']}, speed={t['speed_ms']}ms"
            for t in tileset.animation_table
        ])

        content = f"""; =============================================================================
; {tileset.name} - Animated Tileset
; Generated by ARDK Animated Tile Generator
; =============================================================================

{tileset.name.upper()}_TILE_COUNT = {len(tileset.animated_tiles)}
{tileset.name.upper()}_FRAME_COUNT = {tileset.frame_count}

; Animation table
{tile_entries}

; CHR bank references (swap these for animation)
; Frame 0: .incbin "{tileset.name}_frame0.chr"
; Frame 1: .incbin "{tileset.name}_frame1.chr"
; etc.

; Animation update routine should:
; 1. Increment frame counter
; 2. When counter reaches SPEED_FRAMES, advance to next CHR bank
; 3. Wrap back to frame 0 after FRAME_COUNT
"""

        with open(path, 'w') as f:
            f.write(content)

    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------

    def _sanitize_name(self, description: str) -> str:
        """Convert description to valid filename."""
        words = description.lower().split()[:3]
        name = '_'.join(words)
        name = ''.join(c if c.isalnum() or c == '_' else '' for c in name)
        return name or 'tile'


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    """Command-line interface for animated tile generation."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate animated background tiles'
    )
    parser.add_argument('description', help='Tile description')
    parser.add_argument('-o', '--output', required=True, help='Output directory')
    parser.add_argument('--preset', default='water',
                       choices=list(TILE_ANIMATION_PRESETS.keys()),
                       help='Animation preset')
    parser.add_argument('--frames', type=int, help='Override frame count')
    parser.add_argument('--speed', type=int, help='Override speed (ms)')
    parser.add_argument('--platform', choices=['nes', 'genesis', 'snes'],
                       default='nes', help='Target platform')
    parser.add_argument('--list-presets', action='store_true',
                       help='List available presets')

    args = parser.parse_args()

    if args.list_presets:
        print("Available animation presets:")
        print()
        for name, config in TILE_ANIMATION_PRESETS.items():
            print(f"  {name}:")
            print(f"    Frames: {config['frames']}, Speed: {config['speed_ms']}ms")
            print(f"    {config['description']}")
            print()
        return

    # Get platform config
    from .base_generator import get_nes_config, get_genesis_config, get_snes_config

    configs = {
        'nes': get_nes_config,
        'genesis': get_genesis_config,
        'snes': get_snes_config,
    }
    platform = configs[args.platform]()

    # Create generator
    generator = AnimatedTileGenerator(platform=platform)

    print(f"Generating animated tile: {args.description}")
    print(f"Preset: {args.preset}")
    print(f"Platform: {platform.name}")

    # Generate
    tile = generator.generate_animated_tile(
        args.description,
        preset=args.preset,
        frame_count=args.frames,
        speed_ms=args.speed,
    )

    print(f"\nGenerated {tile.frame_count} frames @ {tile.speed_ms}ms")

    # Save
    files = generator.save_animated_tile(tile, args.output)

    print(f"\nCreated files:")
    for name, path in files.items():
        print(f"  {name}: {path}")


if __name__ == '__main__':
    main()
