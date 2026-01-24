"""
Unified Pipeline - Main Orchestrator.

This is the core pipeline class that:
1. Detects input type (PNG, Aseprite, Prompt)
2. Routes to appropriate handler
3. Enforces safeguards at every step
4. Emits events for GUI progress

Usage:
    from tools.pipeline.core import Pipeline, PipelineConfig

    # Create pipeline
    config = PipelineConfig(
        platform='genesis',
        safeguards=SafeguardConfig(dry_run=False),
    )
    pipeline = Pipeline(config)

    # Process image
    result = pipeline.process('sprite.png', 'output/')

    # Process Aseprite file
    result = pipeline.process('character.ase', 'output/')

    # Generate from prompt
    result = pipeline.generate('warrior with sword', 'output/')
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import asdict
from datetime import datetime

from PIL import Image

from .config import PipelineConfig, InputType
from .safeguards import Safeguards, SafeguardViolation, DryRunActive
from .events import (
    EventEmitter, EventType, ProgressEvent, StageEvent,
    ConsoleEventHandler
)

logger = logging.getLogger(__name__)


# Stage definitions
STAGES = [
    ("input", "Input Detection & Loading"),
    ("preprocess", "Preprocessing"),
    ("palette", "Palette Extraction"),
    ("detect", "Sprite Detection"),
    ("analyze", "AI Analysis"),
    ("convert", "Platform Conversion"),
    ("export", "Export & Bank Creation"),
]


class Pipeline:
    """
    Unified Pipeline with enforced safeguards.

    This class orchestrates the entire asset processing pipeline:
    1. Input detection (PNG, Aseprite, Prompt)
    2. Preprocessing (remove watermarks, crop, etc.)
    3. Palette extraction (AI-enhanced or algorithmic)
    4. Sprite detection (flood-fill + AI refinement)
    5. Platform conversion (Genesis, NES, etc.)
    6. Export (tile banks, metadata, SGDK resources)

    Safeguards are ALWAYS enforced:
    - Budget limits (cannot generate more than max_generations)
    - Dry-run mode (default ON, must be explicitly disabled)
    - Caching (always saves before processing)
    - Validation (checks inputs before processing)
    """

    def __init__(
        self,
        config: PipelineConfig,
        event_emitter: Optional[EventEmitter] = None
    ):
        """
        Initialize pipeline.

        Args:
            config: PipelineConfig with all settings
            event_emitter: Optional EventEmitter for progress updates
        """
        self.config = config

        # Initialize safeguards (ALWAYS)
        self.safeguards = Safeguards(config.safeguards)

        # Initialize event emitter
        self.events = event_emitter or EventEmitter()
        if not event_emitter:
            # Default console handler for CLI
            self.events.on_all(ConsoleEventHandler(verbose=config.verbose))

        # Lazy-load heavy modules
        self._platform_config = None
        self._ai_analyzer = None
        self._aseprite_exporter = None
        self._pixellab_client = None

    @property
    def platform_config(self):
        """Lazy-load platform configuration."""
        if self._platform_config is None:
            from ..platforms import PLATFORMS
            self._platform_config = PLATFORMS.get(
                self.config.platform.lower()
            )
        return self._platform_config

    @property
    def ai_analyzer(self):
        """Lazy-load AI analyzer."""
        if self._ai_analyzer is None and not self.config.offline_mode:
            from ..ai import AIAnalyzer
            self._ai_analyzer = AIAnalyzer(
                self.config.ai_provider,
                offline_mode=self.config.offline_mode
            )
        return self._ai_analyzer

    @property
    def aseprite_exporter(self):
        """Lazy-load Aseprite exporter."""
        if self._aseprite_exporter is None:
            from ..integrations.aseprite import AsepriteExporter
            self._aseprite_exporter = AsepriteExporter()
        return self._aseprite_exporter

    @property
    def pixellab_client(self):
        """Lazy-load PixelLab client."""
        if self._pixellab_client is None:
            # Check safeguards before creating client
            self.safeguards.check_dry_run("PixelLab client creation")
            self.safeguards.check_budget()

            # Import and create client
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "asset_generators"))
            from pixellab_client import PixelLabClient
            self._pixellab_client = PixelLabClient(
                max_calls=self.config.safeguards.max_generations_per_run
            )
        return self._pixellab_client

    def _detect_input_type(self, input_path: str) -> InputType:
        """Detect the type of input."""
        p = Path(input_path)

        if not p.exists():
            # Could be a prompt
            if len(input_path) > 10 and ' ' in input_path:
                return InputType.PROMPT
            return InputType.UNKNOWN

        if p.is_dir():
            return InputType.DIRECTORY

        suffix = p.suffix.lower()
        if suffix in ['.ase', '.aseprite']:
            return InputType.ASEPRITE
        elif suffix in ['.png', '.jpg', '.jpeg', '.gif']:
            return InputType.PNG

        return InputType.UNKNOWN

    def _emit_stage(self, stage_idx: int, stage_name: str, complete: bool = False):
        """Emit a stage event."""
        total = len(STAGES)
        if complete:
            self.events.emit_stage_complete(stage_name, stage_idx + 1, total)
        else:
            self.events.emit_stage_start(stage_name, stage_idx + 1, total)

    def _emit_progress(self, percent: float, message: str, stage: str = ""):
        """Emit a progress event."""
        self.events.emit_progress(percent, message, stage)

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def process(
        self,
        input_path: str,
        output_dir: str,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process an asset (PNG or Aseprite file).

        Args:
            input_path: Path to input file (PNG, ASE, or directory)
            output_dir: Output directory
            category: Asset category hint (player, enemy, etc.)

        Returns:
            Result dictionary with success status and metadata
        """
        # Validate inputs
        self.safeguards.validate_input(input_path)
        self.safeguards.validate_output(output_dir)

        # Detect input type
        input_type = self._detect_input_type(input_path)

        if input_type == InputType.PROMPT:
            return self.generate(input_path, output_dir)
        elif input_type == InputType.ASEPRITE:
            return self._process_aseprite(input_path, output_dir, category)
        elif input_type == InputType.PNG:
            return self._process_image(input_path, output_dir, category)
        elif input_type == InputType.DIRECTORY:
            return self.process_batch(input_path, output_dir)
        else:
            return {
                "success": False,
                "error": f"Unknown input type: {input_path}"
            }

    def generate(
        self,
        prompt: str,
        output_dir: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate assets from a text prompt.

        Args:
            prompt: Text description of what to generate
            output_dir: Output directory
            **kwargs: Additional generation options

        Returns:
            Result dictionary
        """
        # Validate
        self.safeguards.validate_prompt(prompt)
        self.safeguards.validate_output(output_dir)

        # Check safeguards
        try:
            self.safeguards.check_dry_run("AI generation")
            self.safeguards.check_budget()
        except DryRunActive:
            # Return dry-run report
            return {
                "success": True,
                "dry_run": True,
                "report": self.safeguards.generate_dry_run_report([
                    {"type": "generate", "name": prompt[:50]}
                ])
            }

        # Check confirmation
        if not self.safeguards.require_confirmation("generate"):
            return {
                "success": False,
                "confirmation_required": True,
                "message": f"Confirm generation: {prompt[:50]}..."
            }

        # Perform generation
        return self._generate_with_pixellab(prompt, output_dir, **kwargs)

    def process_batch(
        self,
        input_dir: str,
        output_dir: str
    ) -> Dict[str, Any]:
        """
        Process a batch of assets from a directory.

        Args:
            input_dir: Directory containing input files
            output_dir: Output directory

        Returns:
            Result dictionary with per-file results
        """
        self.safeguards.validate_output(output_dir)

        input_path = Path(input_dir)
        if not input_path.is_dir():
            return {"success": False, "error": f"Not a directory: {input_dir}"}

        # Find all processable files
        files = []
        for ext in ['*.png', '*.ase', '*.aseprite']:
            files.extend(input_path.glob(ext))

        results = {"success": True, "files": [], "failed": 0, "succeeded": 0}

        for i, file_path in enumerate(files):
            self._emit_progress(
                (i / len(files)) * 100,
                f"Processing {file_path.name}...",
                "batch"
            )

            file_output = Path(output_dir) / file_path.stem
            result = self.process(str(file_path), str(file_output))

            results["files"].append({
                "file": str(file_path),
                "success": result.get("success", False),
            })

            if result.get("success"):
                results["succeeded"] += 1
            else:
                results["failed"] += 1

        return results

    def confirm(self):
        """Confirm the current operation (for interactive use)."""
        self.safeguards.confirm()

    def get_status(self) -> Dict[str, Any]:
        """Get current pipeline and safeguard status."""
        return {
            "platform": self.config.platform,
            "safeguards": self.safeguards.get_status(),
            "offline_mode": self.config.offline_mode,
        }

    # =========================================================================
    # INTERNAL PROCESSING METHODS
    # =========================================================================

    def _process_image(
        self,
        input_path: str,
        output_dir: str,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a PNG image through the full pipeline."""
        os.makedirs(output_dir, exist_ok=True)

        # Stage 0: Input
        self._emit_stage(0, STAGES[0][1])
        img = Image.open(input_path).convert('RGBA')
        self._emit_stage(0, STAGES[0][1], complete=True)

        # Stage 1: Preprocess
        self._emit_stage(1, STAGES[1][1])
        img = self._preprocess_image(img)
        self._emit_stage(1, STAGES[1][1], complete=True)

        # Stage 2: Palette
        self._emit_stage(2, STAGES[2][1])
        palette = self._extract_palette(img)
        self._emit_stage(2, STAGES[2][1], complete=True)

        # Stage 3: Detect
        self._emit_stage(3, STAGES[3][1])
        sprites = self._detect_sprites(img, category)
        self._emit_stage(3, STAGES[3][1], complete=True)

        # Stage 4: Analyze
        if self.ai_analyzer and not self.config.offline_mode:
            self._emit_stage(4, STAGES[4][1])
            sprites = self._analyze_sprites(img, sprites)
            self._emit_stage(4, STAGES[4][1], complete=True)

        # Stage 5: Convert
        self._emit_stage(5, STAGES[5][1])
        results = self._convert_sprites(img, sprites, palette, output_dir)
        self._emit_stage(5, STAGES[5][1], complete=True)

        # Stage 6: Export
        self._emit_stage(6, STAGES[6][1])
        metadata = self._export_results(results, palette, output_dir, input_path)
        self._emit_stage(6, STAGES[6][1], complete=True)

        return {"success": True, "metadata": metadata, "palette": palette}

    def _process_aseprite(
        self,
        input_path: str,
        output_dir: str,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process an Aseprite file."""
        from ..integrations.aseprite import (
            parse_aseprite_json,
            frames_to_animation_sequences
        )

        os.makedirs(output_dir, exist_ok=True)

        # Check if Aseprite CLI is available
        if self.aseprite_exporter.is_available():
            # Export via CLI
            self.events.emit(StageEvent(
                type=EventType.ASEPRITE_EXPORT,
                stage_name="Exporting from Aseprite",
                stage_index=0,
                total_stages=2,
            ))

            export_result = self.aseprite_exporter.export_sheet(
                input_path,
                output_dir,
                sheet_type=self.config.aseprite.sheet_type,
                scale=self.config.aseprite.scale,
                trim=self.config.aseprite.trim,
            )

            if not export_result.success:
                return {"success": False, "error": export_result.error}

            # Parse the exported JSON
            metadata = parse_aseprite_json(str(export_result.json_path))

        else:
            # Look for pre-exported JSON
            json_path = Path(input_path).with_suffix('.json')
            if not json_path.exists():
                return {
                    "success": False,
                    "error": "Aseprite not available and no pre-exported JSON found"
                }

            metadata = parse_aseprite_json(str(json_path))

        # Convert to animation sequences
        if self.config.aseprite.convert_to_sequences:
            sequences = frames_to_animation_sequences(metadata)

            # Export sequences
            from ..animation import export_sgdk_animations
            export_sgdk_animations(sequences, output_dir)

        return {
            "success": True,
            "metadata": {
                "frame_count": len(metadata.frames),
                "tags": [t.name for t in metadata.tags],
                "layers": [l.name for l in metadata.layers],
            }
        }

    def _generate_with_pixellab(
        self,
        prompt: str,
        output_dir: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate assets using PixelLab API."""
        os.makedirs(output_dir, exist_ok=True)

        gen_config = self.config.generation
        width = kwargs.get('width', gen_config.width)
        height = kwargs.get('height', gen_config.height)

        # Check cache first
        cache_key = self.safeguards.cache.get_cache_key(prompt, width, height)

        if self.safeguards.cache.has_cached_result(cache_key):
            self.events.emit(StageEvent(
                type=EventType.GENERATION_CACHED,
                stage_name="Loading from cache",
                stage_index=0,
                total_stages=1,
            ))
            images = self.safeguards.cache.load_images(cache_key)
            if images:
                # Save to output
                for name, img in images.items():
                    img.save(Path(output_dir) / f"{name}.png")
                return {
                    "success": True,
                    "cached": True,
                    "images": list(images.keys())
                }

        # Generate via PixelLab
        self.events.emit(StageEvent(
            type=EventType.GENERATION_START,
            stage_name="AI Generation",
            stage_index=0,
            total_stages=1,
            data={"prompt": prompt[:50]}
        ))

        # Cache request before calling API
        self.safeguards.cache.save_request(cache_key, {
            "prompt": prompt,
            "width": width,
            "height": height,
            "config": asdict(gen_config),
        })

        if gen_config.generate_8_directions:
            result = self.pixellab_client.create_character_8_directions(
                description=prompt,
                width=width,
                height=height,
                outline=gen_config.outline,
                shading=gen_config.shading,
                detail=gen_config.detail,
                view=gen_config.view,
                max_poll_attempts=gen_config.max_poll_attempts,
                poll_interval=gen_config.poll_interval,
            )
        else:
            result = self.pixellab_client.generate_image_v2(
                description=prompt,
                width=width,
                height=height,
                no_background=True,
            )

        if not result.success:
            return {"success": False, "error": result.error}

        # Record generation
        self.safeguards.record_generation(result.cost_usd)

        # Cache and save images
        if result.images:
            directions = result.metadata.get("directions", [])
            images = {}
            for i, img in enumerate(result.images):
                name = directions[i] if i < len(directions) else f"frame_{i}"
                images[name] = img
                img.save(Path(output_dir) / f"{name}.png")

            self.safeguards.cache.save_images(cache_key, images)

            # Apply mirror optimization if configured
            if gen_config.use_mirror_optimization and gen_config.generate_8_directions:
                from ...asset_generators.generation_safeguards import apply_mirror_optimization
                images = apply_mirror_optimization(images)
                for name, img in images.items():
                    img.save(Path(output_dir) / f"{name}.png")

        elif result.image:
            result.image.save(Path(output_dir) / "sprite.png")
            self.safeguards.cache.save_images(cache_key, {"sprite": result.image})

        self.events.emit(StageEvent(
            type=EventType.GENERATION_COMPLETE,
            stage_name="Generation complete",
            stage_index=1,
            total_stages=1,
            data={"cost": result.cost_usd}
        ))

        return {
            "success": True,
            "cost_usd": result.cost_usd,
            "images": result.metadata.get("directions", ["sprite"]),
        }

    # =========================================================================
    # PROCESSING STAGE HELPERS
    # =========================================================================

    def _preprocess_image(self, img: Image.Image) -> Image.Image:
        """Preprocess image (remove watermarks, crop, etc.)."""
        width, height = img.size

        # Crop margins for AI watermarks
        top = int(height * 0.10)
        bottom = int(height * 0.90)
        left = int(width * 0.02)
        right = int(width * 0.98)

        return img.crop((left, top, right, bottom))

    def _extract_palette(self, img: Image.Image) -> List[int]:
        """Extract palette from image."""
        from ..processing import PaletteExtractor

        extractor = PaletteExtractor()
        colors = self.config.processing.colors_per_palette

        if self.config.processing.forced_palette:
            return self.config.processing.forced_palette

        if self.config.processing.palette_name:
            from ..palettes import get_genesis_palette
            return get_genesis_palette(self.config.processing.palette_name)

        if self.ai_analyzer and not self.config.offline_mode:
            return extractor.extract_with_ai(img, self.ai_analyzer, colors)

        return extractor.extract_from_image(img, colors)

    def _detect_sprites(
        self,
        img: Image.Image,
        category: Optional[str]
    ) -> List[Any]:
        """Detect sprites in image."""
        from ..processing import FloodFillBackgroundDetector
        from ..platforms import SpriteInfo, BoundingBox

        detector = FloodFillBackgroundDetector()
        bboxes = detector.detect(img)

        if self.config.processing.filter_text:
            bboxes = detector.filter_text_regions(img, bboxes)

        # Convert to SpriteInfo
        sprites = []
        inferred_type = category or 'sprite'

        for i, bbox in enumerate(bboxes):
            sprites.append(SpriteInfo(
                id=i + 1,
                bbox=bbox,
                sprite_type=inferred_type,
                action="frame",
                frame_index=i + 1,
                description=f"{inferred_type}_frame_{i+1}"
            ))

        return sprites

    def _analyze_sprites(
        self,
        img: Image.Image,
        sprites: List[Any]
    ) -> List[Any]:
        """AI analysis of sprites."""
        if not self.ai_analyzer or not self.ai_analyzer.available:
            return sprites

        analysis = self.ai_analyzer.analyze(img, sprites)
        return self.ai_analyzer.apply_labels(sprites, analysis)

    def _convert_sprites(
        self,
        img: Image.Image,
        sprites: List[Any],
        palette: List[int],
        output_dir: str
    ) -> List[Dict[str, Any]]:
        """Convert sprites to platform format."""
        from ..processing import SpriteConverter

        converter = SpriteConverter(
            platform=self.platform_config,
            palette=palette
        )

        results = []
        target_size = self.config.processing.target_size
        ext = self.platform_config.output_extension

        for sprite in sprites:
            cropped = img.crop(sprite.bbox.crop_box())
            scaled = converter.scale_sprite(cropped, target_size)
            indexed = converter.index_sprite(scaled)
            tile_data = converter.generate_tile_data(indexed)

            filename = f"sprite_{sprite.id:02d}_{sprite.description}"
            tile_path = Path(output_dir) / f"{filename}{ext}"

            scaled.save(Path(output_dir) / f"{filename}_scaled.png")
            indexed.save(Path(output_dir) / f"{filename}_indexed.png")

            with open(tile_path, 'wb') as f:
                f.write(tile_data)

            results.append({
                'sprite': sprite,
                'tile_path': str(tile_path),
                'tile_size': len(tile_data),
            })

        return results

    def _export_results(
        self,
        results: List[Dict],
        palette: List[int],
        output_dir: str,
        input_path: str
    ) -> Dict[str, Any]:
        """Export final results and metadata."""
        import json

        ext = self.platform_config.output_extension

        # Create combined tile bank
        combined = bytearray()
        for r in results[:32]:
            with open(r['tile_path'], 'rb') as f:
                combined.extend(f.read())

        combined_path = Path(output_dir) / f"sprites{ext}"
        with open(combined_path, 'wb') as f:
            f.write(combined)

        # Create metadata
        metadata = {
            'source': input_path,
            'timestamp': datetime.now().isoformat(),
            'platform': self.config.platform.upper(),
            'target_size': self.config.processing.target_size,
            'palette': palette,
            'sprites_count': len(results),
            'sprites': [
                {
                    'id': r['sprite'].id,
                    'type': r['sprite'].sprite_type,
                    'description': r['sprite'].description,
                    'tile_file': Path(r['tile_path']).name,
                    'tile_size': r['tile_size'],
                }
                for r in results
            ]
        }

        with open(Path(output_dir) / 'metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)

        # Generate SGDK .res file if requested
        if self.config.export.generate_res_file and self.config.platform == 'genesis':
            self._generate_res_file(results, output_dir)

        return metadata

    def _generate_res_file(self, results: List[Dict], output_dir: str):
        """Generate SGDK resources.res file."""
        from ..sgdk_resources import SGDKResourceGenerator

        gen = SGDKResourceGenerator()

        for r in results:
            sprite = r['sprite']
            gen.add_sprite(
                name=sprite.description.upper(),
                path=r['tile_path'],
                width=self.config.processing.target_size // 8,
                height=self.config.processing.target_size // 8,
            )

        res_path = str(Path(output_dir) / 'resources.res')
        gen.generate(res_path)
