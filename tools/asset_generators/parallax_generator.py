"""
Parallax Generator - Multi-layer scrolling background generation.

Features:
- Layer presets for common parallax configurations
- Per-layer width based on scroll speed
- Separate CHR banks per layer
- HAL config generation for hal_parallax.h integration
- Scanline-accurate layer boundaries
"""

import os
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

try:
    from PIL import Image, ImageDraw
    import numpy as np
except ImportError:
    raise ImportError("PIL and numpy required: pip install pillow numpy")

from .base_generator import (
    AssetGenerator, GeneratedAsset, GenerationFlags,
    PlatformConfig, get_nes_config
)
from .background_generator import BackgroundGenerator, ScrollingBackground

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from tile_optimizers.tile_deduplicator import TileDeduplicator


# =============================================================================
# Layer Presets
# =============================================================================

LAYER_PRESETS = {
    'simple_2layer': [
        {'name': 'sky', 'speed': 0.25, 'height_pct': 0.4,
         'description': 'Distant sky, clouds, or stars'},
        {'name': 'ground', 'speed': 1.0, 'height_pct': 0.6,
         'description': 'Ground level where gameplay occurs'},
    ],

    'standard_3layer': [
        {'name': 'far_bg', 'speed': 0.25, 'height_pct': 0.3,
         'description': 'Distant background (mountains, sky)'},
        {'name': 'mid_bg', 'speed': 0.5, 'height_pct': 0.35,
         'description': 'Middle distance (buildings, trees)'},
        {'name': 'foreground', 'speed': 1.0, 'height_pct': 0.35,
         'description': 'Foreground where player moves'},
    ],

    'city_4layer': [
        {'name': 'sky', 'speed': 0.0, 'height_pct': 0.2,
         'description': 'Static sky with gradient or stars'},
        {'name': 'distant_buildings', 'speed': 0.2, 'height_pct': 0.25,
         'description': 'Distant skyscrapers, silhouettes'},
        {'name': 'near_buildings', 'speed': 0.5, 'height_pct': 0.25,
         'description': 'Closer buildings with some detail'},
        {'name': 'street', 'speed': 1.0, 'height_pct': 0.3,
         'description': 'Street level with neon signs'},
    ],

    'nature_3layer': [
        {'name': 'sky_mountains', 'speed': 0.15, 'height_pct': 0.35,
         'description': 'Sky and distant mountains'},
        {'name': 'trees', 'speed': 0.4, 'height_pct': 0.3,
         'description': 'Forest treeline'},
        {'name': 'ground', 'speed': 1.0, 'height_pct': 0.35,
         'description': 'Ground with grass and rocks'},
    ],

    'space_2layer': [
        {'name': 'stars', 'speed': 0.1, 'height_pct': 1.0,
         'description': 'Star field background'},
        {'name': 'nebula', 'speed': 0.3, 'height_pct': 1.0,
         'description': 'Colorful nebula overlay'},
    ],

    'underwater_3layer': [
        {'name': 'deep_water', 'speed': 0.1, 'height_pct': 0.4,
         'description': 'Deep dark water with light rays'},
        {'name': 'mid_water', 'speed': 0.35, 'height_pct': 0.3,
         'description': 'Floating particles, distant fish'},
        {'name': 'sea_floor', 'speed': 1.0, 'height_pct': 0.3,
         'description': 'Ocean floor with coral and rocks'},
    ],
}


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class ParallaxLayer:
    """A single parallax layer."""

    name: str
    index: int
    scroll_speed: float  # 0.0 = static, 1.0 = full speed

    # Dimensions
    y_start: int  # Scanline start
    y_end: int    # Scanline end
    width_pixels: int
    height_pixels: int

    # Generated data
    image: Optional[Image.Image] = None
    chr_data: Optional[bytes] = None
    tilemap: Optional[List[int]] = None
    palette: Optional[List[int]] = None

    # CHR bank assignment
    chr_bank: int = 0

    # Metadata
    description: str = ""
    tile_count: int = 0

    @property
    def height(self) -> int:
        return self.y_end - self.y_start


@dataclass
class ParallaxSet:
    """Complete parallax background set."""

    name: str
    layers: List[ParallaxLayer]
    total_height: int
    base_width: int

    # Platform info
    platform: str = "NES"

    # Metadata
    preset_name: str = ""
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    @property
    def layer_count(self) -> int:
        return len(self.layers)

    @property
    def total_chr_size(self) -> int:
        return sum(len(layer.chr_data) for layer in self.layers if layer.chr_data)


# =============================================================================
# Parallax Generator
# =============================================================================

class ParallaxGenerator(AssetGenerator):
    """Generate multi-layer parallax backgrounds."""

    def __init__(
        self,
        platform: Optional[PlatformConfig] = None,
        api_key: Optional[str] = None,
    ):
        """Initialize parallax generator."""
        platform = platform or get_nes_config()
        super().__init__(platform, api_key)

        # Background generator for each layer
        self.bg_generator = BackgroundGenerator(platform, api_key)

    def generate(self, description: str, **kwargs) -> GeneratedAsset:
        """Generate parallax set and return as asset."""
        preset = kwargs.get('preset', 'standard_3layer')
        width_screens = kwargs.get('width_screens', 2)

        parallax = self.generate_parallax_set(
            description=description,
            preset=preset,
            width_screens=width_screens,
        )

        # Combine layers into single preview image
        combined = self._create_preview_image(parallax)

        return GeneratedAsset(
            name=parallax.name,
            image=combined,
            palette=[],  # Multiple palettes in layers
            metadata={
                'type': 'parallax',
                'layer_count': parallax.layer_count,
                'preset': preset,
                'layers': [l.name for l in parallax.layers],
            },
            warnings=parallax.warnings,
        )

    def optimize(self, asset: GeneratedAsset) -> GeneratedAsset:
        """Parallax optimization is done per-layer during generation."""
        return asset

    # -------------------------------------------------------------------------
    # Main Generation Methods
    # -------------------------------------------------------------------------

    def generate_parallax_set(
        self,
        description: str,
        preset: str = 'standard_3layer',
        width_screens: int = 2,
        custom_layers: Optional[List[Dict]] = None,
    ) -> ParallaxSet:
        """
        Generate a complete parallax background set.

        Args:
            description: Scene description
            preset: Preset name from LAYER_PRESETS
            width_screens: Base width in screens
            custom_layers: Optional custom layer definitions

        Returns:
            ParallaxSet with all layers generated
        """
        # Get layer config
        layer_configs = custom_layers or LAYER_PRESETS.get(preset, LAYER_PRESETS['standard_3layer'])

        # Validate layer count against platform
        if len(layer_configs) > self.platform.max_parallax_layers:
            layer_configs = layer_configs[:self.platform.max_parallax_layers]

        # Calculate layer dimensions
        total_height = self.platform.screen_height
        layers = []

        y_pos = 0
        for idx, cfg in enumerate(layer_configs):
            layer_height = int(total_height * cfg['height_pct'])

            # Adjust width based on scroll speed
            # Slower layers can be narrower (they scroll less)
            layer_width = self._calculate_layer_width(
                width_screens,
                cfg['speed'],
            )

            layer = ParallaxLayer(
                name=cfg['name'],
                index=idx,
                scroll_speed=cfg['speed'],
                y_start=y_pos,
                y_end=y_pos + layer_height,
                width_pixels=layer_width,
                height_pixels=layer_height,
                chr_bank=idx % self.platform.max_chr_banks,
                description=cfg.get('description', ''),
            )

            layers.append(layer)
            y_pos += layer_height

        # Generate each layer
        for layer in layers:
            self._generate_layer(layer, description)

        # Check for warnings
        warnings = []
        total_tiles = sum(l.tile_count for l in layers)
        max_total = self.platform.max_tiles_per_bank * self.platform.max_chr_banks
        if total_tiles > max_total * 0.9:
            warnings.append(f"Total tiles ({total_tiles}) approaching limit ({max_total})")

        # Create name
        name = self._sanitize_name(description)

        return ParallaxSet(
            name=name,
            layers=layers,
            total_height=total_height,
            base_width=self.platform.screen_width * width_screens,
            platform=self.platform.name,
            preset_name=preset,
            description=description,
            metadata={
                'layer_configs': layer_configs,
                'width_screens': width_screens,
            },
            warnings=warnings,
        )

    def _generate_layer(
        self,
        layer: ParallaxLayer,
        scene_description: str,
    ) -> None:
        """Generate a single parallax layer."""

        # Build layer-specific prompt
        prompt = self._build_layer_prompt(layer, scene_description)

        # Generate image
        raw_image = self.client.generate_image(
            prompt=prompt,
            width=layer.width_pixels,
            height=layer.height_pixels,
            model='flux',
        )

        # Post-process
        processed = self._postprocess_layer(raw_image, layer)

        # Create deduplicator for this layer
        deduplicator = TileDeduplicator(
            tile_width=self.platform.tile_width,
            tile_height=self.platform.tile_height,
            enable_h_flip=self.platform.enable_flip_optimization,
            enable_v_flip=self.platform.enable_flip_optimization,
        )

        # Optimize tiles
        optimized = deduplicator.optimize(processed)

        # Extract palette
        palette = self._extract_palette_ai(
            processed,
            num_colors=self.platform.colors_per_palette
        )

        # Store results
        layer.image = processed
        layer.chr_data = deduplicator.generate_chr(optimized)
        layer.tilemap = deduplicator.generate_tilemap(optimized)
        layer.palette = palette
        layer.tile_count = optimized.unique_count

    def _build_layer_prompt(
        self,
        layer: ParallaxLayer,
        scene_description: str,
    ) -> str:
        """Build prompt for a specific parallax layer."""

        style = self._build_style_prompt()

        depth_hint = ""
        if layer.scroll_speed == 0:
            depth_hint = "Static background layer - simple, low detail"
        elif layer.scroll_speed < 0.3:
            depth_hint = "Very distant - use atmospheric haze, simple silhouettes"
        elif layer.scroll_speed < 0.6:
            depth_hint = "Middle distance - some detail but not too sharp"
        else:
            depth_hint = "Foreground - can have more detail"

        prompt = f"""[ARDK_PARALLAX_LAYER]
Generate parallax layer: {layer.name}
Scene: {scene_description}

LAYER INFO:
- Layer {layer.index + 1} of parallax set
- Scroll speed: {layer.scroll_speed}x (1.0 = camera speed)
- Purpose: {layer.description}

DEPTH: {depth_hint}

STYLE: {style}

DIMENSIONS: {layer.width_pixels}x{layer.height_pixels} pixels

TECHNICAL REQUIREMENTS:
- Must tile horizontally (seamless left-right loop)
- Limited palette ({self.platform.colors_per_palette} colors)
- Clean pixel edges, no anti-aliasing
- Tile-aligned edges ({self.platform.tile_width}x{self.platform.tile_height} grid)

OPTIMIZATION:
- Use flat colors for distant layers
- Repeating patterns help reduce tile count
- Simpler = fewer unique tiles
"""
        return prompt

    def _calculate_layer_width(
        self,
        base_screens: int,
        scroll_speed: float,
    ) -> int:
        """
        Calculate layer width based on scroll speed.

        Slower layers can be narrower since they scroll less.
        """
        base_width = self.platform.screen_width * base_screens

        if scroll_speed == 0:
            # Static layer only needs one screen
            return self.platform.screen_width
        elif scroll_speed < 0.5:
            # Slow layers can be proportionally narrower
            factor = max(0.5, scroll_speed * 2)
            width = int(base_width * factor)
        else:
            # Fast layers need full width
            width = base_width

        # Round to tile boundary
        width = (width // self.platform.tile_width) * self.platform.tile_width
        return max(self.platform.screen_width, width)

    def _postprocess_layer(
        self,
        image: Image.Image,
        layer: ParallaxLayer,
    ) -> Image.Image:
        """Post-process a generated layer image."""

        # Ensure RGB mode
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Resize to exact dimensions
        if image.size != (layer.width_pixels, layer.height_pixels):
            image = self._resize_image(image, (layer.width_pixels, layer.height_pixels))

        # Ensure seamless horizontal tiling
        image = self._make_seamless(image)

        # Quantize to platform colors
        total_colors = self.platform.colors_per_palette
        quantized = image.quantize(colors=total_colors, method=Image.MEDIANCUT)

        return quantized.convert('RGB')

    def _make_seamless(self, image: Image.Image) -> Image.Image:
        """Make image seamlessly tileable horizontally."""
        arr = np.array(image)
        height, width = arr.shape[:2]

        blend_width = self.platform.tile_width

        if width < blend_width * 4:
            return image

        # Create gradient blend
        blend_mask = np.linspace(0, 1, blend_width).reshape(1, -1, 1)

        left = arr[:, :blend_width].astype(float)
        right = arr[:, -blend_width:].astype(float)

        blended = (right * (1 - blend_mask) + left * blend_mask)

        result = arr.copy()
        result[:, :blend_width] = blended.astype(np.uint8)

        return Image.fromarray(result)

    # -------------------------------------------------------------------------
    # Preview and Output
    # -------------------------------------------------------------------------

    def _create_preview_image(self, parallax: ParallaxSet) -> Image.Image:
        """Create a combined preview image of all layers."""

        # Use widest layer width
        width = max(l.width_pixels for l in parallax.layers)

        # Create combined image
        combined = Image.new('RGB', (width, parallax.total_height))

        y_pos = 0
        for layer in parallax.layers:
            if layer.image:
                # Tile layer image to fill width if needed
                if layer.image.width < width:
                    tiled = Image.new('RGB', (width, layer.height_pixels))
                    for x in range(0, width, layer.image.width):
                        tiled.paste(layer.image, (x, 0))
                    combined.paste(tiled, (0, y_pos))
                else:
                    combined.paste(layer.image, (0, y_pos))
            y_pos += layer.height_pixels

        return combined

    def save_parallax_set(
        self,
        parallax: ParallaxSet,
        output_dir: str,
    ) -> Dict[str, str]:
        """
        Save parallax set to files.

        Creates:
        - Per-layer CHR and tilemap files
        - Combined metadata.json
        - HAL parallax config include file
        - Preview image
        """
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        created_files = {}

        # Create subdirectories
        (out_path / "layers").mkdir(exist_ok=True)
        (out_path / "tilemaps").mkdir(exist_ok=True)
        (out_path / "preview").mkdir(exist_ok=True)

        # Save each layer
        for layer in parallax.layers:
            # CHR data
            chr_path = out_path / "layers" / f"layer_{layer.index}_{layer.name}.chr"
            if layer.chr_data:
                with open(chr_path, 'wb') as f:
                    f.write(layer.chr_data)
                created_files[f'layer_{layer.index}_chr'] = str(chr_path)

            # Tilemap
            map_path = out_path / "tilemaps" / f"layer_{layer.index}.bin"
            if layer.tilemap:
                with open(map_path, 'wb') as f:
                    f.write(bytes(layer.tilemap))
                created_files[f'layer_{layer.index}_tilemap'] = str(map_path)

            # Layer preview
            if layer.image:
                preview_path = out_path / "preview" / f"layer_{layer.index}_{layer.name}.png"
                layer.image.save(preview_path)
                created_files[f'layer_{layer.index}_preview'] = str(preview_path)

        # Combined preview
        combined = self._create_preview_image(parallax)
        combined_path = out_path / "preview" / "combined.png"
        combined.save(combined_path)
        created_files['combined_preview'] = str(combined_path)

        # Metadata JSON
        metadata = {
            'name': parallax.name,
            'description': parallax.description,
            'platform': parallax.platform,
            'preset': parallax.preset_name,
            'total_height': parallax.total_height,
            'base_width': parallax.base_width,
            'layer_count': parallax.layer_count,
            'layers': [
                {
                    'name': l.name,
                    'index': l.index,
                    'scroll_speed': l.scroll_speed,
                    'y_start': l.y_start,
                    'y_end': l.y_end,
                    'width': l.width_pixels,
                    'height': l.height_pixels,
                    'chr_bank': l.chr_bank,
                    'tile_count': l.tile_count,
                    'palette': l.palette,
                }
                for l in parallax.layers
            ],
        }
        metadata_path = out_path / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        created_files['metadata'] = str(metadata_path)

        # HAL config include
        hal_config_path = out_path / "hal_parallax_config.inc"
        self._write_hal_config(parallax, hal_config_path)
        created_files['hal_config'] = str(hal_config_path)

        return created_files

    def _write_hal_config(self, parallax: ParallaxSet, path: Path) -> None:
        """Write HAL parallax configuration include file."""

        # Build layer definitions
        layer_defs = []
        for layer in parallax.layers:
            layer_defs.append(f"""
; Layer {layer.index}: {layer.name}
PARALLAX_LAYER{layer.index}_Y_START    = {layer.y_start}
PARALLAX_LAYER{layer.index}_Y_END      = {layer.y_end}
PARALLAX_LAYER{layer.index}_SPEED      = {int(layer.scroll_speed * 256)}  ; Fixed-point 8.8
PARALLAX_LAYER{layer.index}_CHR_BANK   = {layer.chr_bank}
PARALLAX_LAYER{layer.index}_WIDTH      = {layer.width_pixels}
""")

        content = f"""; =============================================================================
; {parallax.name} - HAL Parallax Configuration
; Generated by ARDK Parallax Generator
; =============================================================================
; Preset: {parallax.preset_name}
; Platform: {parallax.platform}
; =============================================================================

; Global settings
PARALLAX_LAYER_COUNT = {parallax.layer_count}
PARALLAX_TOTAL_HEIGHT = {parallax.total_height}
PARALLAX_BASE_WIDTH = {parallax.base_width}

; Layer definitions
{"".join(layer_defs)}

; Layer table for runtime lookup
parallax_layer_y_starts:
    .byte {", ".join(str(l.y_start) for l in parallax.layers)}

parallax_layer_y_ends:
    .byte {", ".join(str(l.y_end) for l in parallax.layers)}

parallax_layer_speeds:
    .byte {", ".join(str(int(l.scroll_speed * 256)) for l in parallax.layers)}

parallax_layer_chr_banks:
    .byte {", ".join(str(l.chr_bank) for l in parallax.layers)}

; External data references
; Layer CHR data should be loaded into appropriate CHR banks
; Tilemaps should be loaded into nametable regions
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
        return name or 'parallax'


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    """Command-line interface for parallax generation."""
    import argparse

    # List available presets
    preset_help = "Layer preset. Available: " + ", ".join(LAYER_PRESETS.keys())

    parser = argparse.ArgumentParser(
        description='Generate multi-layer parallax backgrounds'
    )
    parser.add_argument('description', help='Scene description')
    parser.add_argument('-o', '--output', required=True, help='Output directory')
    parser.add_argument('--preset', default='standard_3layer', help=preset_help)
    parser.add_argument('--width-screens', type=int, default=2,
                       help='Base width in screens (default: 2)')
    parser.add_argument('--platform', choices=['nes', 'genesis', 'snes'],
                       default='nes', help='Target platform')
    parser.add_argument('--list-presets', action='store_true',
                       help='List available presets and exit')

    args = parser.parse_args()

    if args.list_presets:
        print("Available parallax presets:\n")
        for name, layers in LAYER_PRESETS.items():
            print(f"  {name}:")
            for layer in layers:
                print(f"    - {layer['name']}: speed={layer['speed']}, "
                      f"height={int(layer['height_pct']*100)}%")
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
    generator = ParallaxGenerator(platform=platform)

    print(f"Generating parallax set: {args.description}")
    print(f"Platform: {platform.name}")
    print(f"Preset: {args.preset}")
    print(f"Base width: {args.width_screens} screens")
    print()

    # Generate
    parallax = generator.generate_parallax_set(
        description=args.description,
        preset=args.preset,
        width_screens=args.width_screens,
    )

    # Save
    files = generator.save_parallax_set(parallax, args.output)

    print(f"Generation complete!")
    print(f"Layers: {parallax.layer_count}")
    print(f"Total CHR size: {parallax.total_chr_size} bytes")
    print()
    print("Layer summary:")
    for layer in parallax.layers:
        print(f"  {layer.index}. {layer.name}: {layer.tile_count} tiles, "
              f"speed={layer.scroll_speed}, y={layer.y_start}-{layer.y_end}")
    print()
    print("Created files:")
    for name, path in files.items():
        print(f"  {name}: {path}")

    if parallax.warnings:
        print("\nWarnings:")
        for w in parallax.warnings:
            print(f"  - {w}")


if __name__ == '__main__':
    main()
