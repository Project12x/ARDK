#!/usr/bin/env python3
"""
Unified Retro Sprite Processing Pipeline for NEON SURVIVORS
Version 6.0 - Modularized Refactor
"""
import os
import argparse
import sys
import json
import time
from datetime import datetime
from dataclasses import asdict
from typing import Dict, Any, List

# Ensure we can import from local tools
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
from PIL import Image, ImageDraw

from pipeline.platforms import PlatformConfig, PLATFORMS, PLATFORM_SPECS, NESConfig, SpriteInfo, BoundingBox, CollisionMask
from pipeline.ai import AIAnalyzer, GenerativeResizer, ConsensusEngine
from pipeline.processing import SpriteConverter, PaletteExtractor, FloodFillBackgroundDetector, TileOptimizer
from pipeline.genesis_export import (
    export_collision_header, export_collision_masks, export_collision_json,
    generate_debug_overlay, export_genesis_tiles, export_genesis_tilemap
)

ASSET_CATEGORIES = {
    'player': {'prefixes': ['player', 'hero', 'char'], 'size': 32},
    'enemy': {'prefixes': ['enemy', 'boss', 'mob'], 'size': 32},
    'background': {'prefixes': ['bg', 'background', 'level', 'map', 'stage'], 'size': 0}, # 0 = variable/fullscreen
    'ui': {'prefixes': ['ui', 'hud', 'font', 'text'], 'size': 8},
    'item': {'prefixes': ['item', 'pickup', 'icon', 'powerup'], 'size': 16},
    'vfx': {'prefixes': ['vfx', 'effect', 'explosion'], 'size': 16},
    'misc': {'prefixes': [], 'size': 16}
}

class UnifiedPipeline:
    """
    Main pipeline with AI-enhanced semantic labeling.
    Supports multiple retro platforms: NES, Genesis, SNES, Amiga, PC Engine.
    """

    def __init__(self, target_size: int = 32, palette: List[int] = None,
                 use_ai: bool = True, ai_provider: str = None,
                 filter_text: bool = True, platform: str = 'nes',
                 consensus_mode: bool = False, output_format: str = 'ca65',
                 mode: str = 'default', strict: bool = False,
                 collision: bool = False, offline_mode: bool = False):
        self.platform_name = platform.upper()
        self.platform = PLATFORMS.get(platform.lower(), NESConfig)
        self.output_format = output_format
        self.use_ai = use_ai
        self.mode = mode
        self.strict = strict
        self.collision_enabled = collision  # Enable AI collision mask generation
        self.offline_mode = offline_mode    # Use fallback strategies instead of AI

        # Optimization flags
        self.optimize_tiles = True # Default for now if platform supports it?
        self.max_tiles = self.platform.mmc3_banking_mode.get('bg_bank_size', 256) if self.platform.mmc3_banking_mode else 256
        self.reserved_status_height = self.platform.reserved_status_bar_height
        self.target_size = target_size # Keep original target_size argument
        self.forced_palette = palette
        self.filter_text = filter_text

        # Initialize AI analyzer (with offline_mode for fallback-only operation)
        if use_ai or mode == 'generative' or collision:
            self.ai_analyzer = AIAnalyzer(ai_provider, offline_mode=offline_mode)
        else:
            self.ai_analyzer = None

        self.consensus_mode = consensus_mode
        self.consensus_engine = ConsensusEngine(self.ai_analyzer) if use_ai and consensus_mode and not offline_mode else None

        # Initialize Helpers
        self.sprite_converter = SpriteConverter()
        self.palette_extractor = PaletteExtractor()
        self.bg_detector = FloodFillBackgroundDetector()
        self.detector = self.bg_detector  # Alias used by detect methods

    def process(self, input_path: str, output_dir: str, category: str = None) -> Dict[str, Any]:
        print(f"\n{'='*60}")
        print("  Retro Sprite Pipeline v6.0 - ARDK Foundation")
        print(f"{'='*60}\n")
        
        # Generative Mode Handling
        if self.mode == 'generative':
            gen_resizer = GenerativeResizer(self.platform_name, self.ai_analyzer)
            # Create a variant path
            base_name = os.path.basename(input_path)
            name_no_ext = os.path.splitext(base_name)[0]
            gen_output = os.path.join(output_dir, f"{name_no_ext}_gen.png")
            
            if gen_resizer.generate_variant(input_path, gen_output):
                # SWAP input_path to the generated asset for subsequent processing
                print(f"      [Pipeline] Swapping input to generated asset: {gen_output}")
                input_path = gen_output
            else:
                if self.strict:
                    print(f"      [Pipeline] STRICT MODE: Generation failed, aborting.")
                    return {}
                print(f"      [Pipeline] Generation failed, falling back to original.")

        print(f"  Platform: {self.platform_name}")
        print(f"  Input:    {input_path}")
        print(f"  Output:   {output_dir}")
        print(f"  Size:     {self.target_size}x{self.target_size}")
        print(f"  Colors:   {self.platform.colors_per_palette} per palette")
        print(f"  Format:   {self.platform.output_extension}")
        if self.ai_analyzer and self.ai_analyzer.available:
            mode_str = "CONSENSUS" if self.consensus_mode else "STANDARD"
            print(f"  AI:       {self.ai_analyzer.provider_name} [{mode_str}]")
        else:
            print(f"  AI:       Disabled")
        print(f"{'='*60}\n")

        os.makedirs(output_dir, exist_ok=True)

        # Stage 1: Load and preprocess
        print("[1/6] Loading image...")
        img = Image.open(input_path).convert('RGBA')
        print(f"      Size: {img.size[0]}x{img.size[1]}")

        # Stage 1.1: PixelLab intelligent resize (v2 API) for oversized images
        if getattr(self, 'pixellab_resize', False) and (img.width > 128 or img.height > 128):
            print(f"      [PixelLab v2] Image is oversized, using AI resize...")
            try:
                from asset_generators.pixellab_client import PixelLabClient, resize_to_genesis
                client = PixelLabClient()
                palette_name = None
                if hasattr(self, 'forced_palette') and self.forced_palette:
                    # Try to reverse-lookup palette name (not always available)
                    pass  # Use None, SGDKFormatter will handle palette
                resized = resize_to_genesis(
                    client, img,
                    target_width=self.target_size,
                    target_height=self.target_size,
                    palette_name=palette_name,
                )
                if resized:
                    img = resized.convert('RGBA')
                    print(f"      [PixelLab v2] Resized to {img.width}x{img.height}")
                    print(f"      [PixelLab v2] Cost: ${client.get_session_cost():.4f}")
                else:
                    print(f"      [PixelLab v2] Resize failed, using standard processing")
            except ImportError as e:
                print(f"      [PixelLab v2] Not available: {e}")

        # Stage 1.5: MMC3 Status Bar Crop (if applicable)
        status_bar_img = None
        if self.reserved_status_height > 0:
            print(f"      [MMC3] Reserving {self.reserved_status_height}px for status bar.")
            # Assume status bar is at top? Or Bottom? Usually top or bottom. Let's assume Top for now or configurable.
            # User said: "40 pixel high status bar in the background layer"
            # We crop the MAIN content area for processing.
            # Let's assume Status Bar is at TOP.
            status_bar_img = img.crop((0, 0, img.width, self.reserved_status_height))
            img = img.crop((0, self.reserved_status_height, img.width, img.height))
            print(f"      [MMC3] Main content cropped to {img.size}")

        # Stage 1.6: Tile Optimization & Smart Downscaling
        if self.optimize_tiles:
            optimizer = TileOptimizer(
                self.platform.tile_width, 
                self.platform.tile_height,
                self.platform.allow_mirroring_x,
                self.platform.allow_mirroring_y
            )
            
            # Initial Check
            u_tiles, t_map, u_count = optimizer.optimize(img)
            print(f"      [Optimization] Initial Unique Tiles: {u_count} (Limit: {self.max_tiles})")
            
            if u_count > self.max_tiles:
                print(f"      [Optimization] EXCEEDS LIMIT via algorithmic deduplication.")
                
                if self.use_ai:
                    print(f"      [Optimization] Engaging AI Smart Downscaling...")
                    gen_resizer = GenerativeResizer(self.platform_name, self.ai_analyzer)
                    
                    # Create optimized temp file
                    opt_input = input_path # Or temp file
                    base_name = os.path.basename(input_path)
                    opt_output = os.path.join(output_dir, f"{os.path.splitext(base_name)[0]}_optimized.png")
                    
                    if gen_resizer.simplify_for_tiling(input_path, opt_output, self.max_tiles):
                        print(f"      [Optimization] AI generated simplified variant.")
                        # Load new image
                        img = Image.open(opt_output).convert('RGBA')
                        if self.reserved_status_height > 0:
                             img = img.crop((0, self.reserved_status_height, img.width, img.height))
                        
                        # Re-optimize
                        u_tiles, t_map, u_count = optimizer.optimize(img)
                        print(f"      [Optimization] Post-AI Unique Tiles: {u_count}")
                    else:
                        print("      [Optimization] AI failed to simplify.")
                
                if u_count > self.max_tiles and self.strict:
                    print(f"      [ERROR] Still exceeds tile limit ({u_count}/{self.max_tiles}). Strict mode aborting.")
                    return {}
            
            # Verify we didn't just break the image? No, we proceed with whatever we have.
            # We should probably store the optimized tile map for export key?
            # For now, we continue pipeline, but the pipeline itself (Slice->Quantize) needs to respect this.
            # Actually, the standard pipeline creates tiles sequentially.
            # We might want to REPLACE the standard Slicing logic later or specifically export the NAMETABLE here.
            
            # Export Nametable if valid
            if u_count <= self.max_tiles:
                 nametable_path = os.path.join(output_dir, "background.nametable")
                 # We would write binary nametable here (requires more complex logic for attributes)
                 print(f"      [Optimization] Optimization successful. Ready for export.")

        # Preprocess: Remove AI watermarks/text from edges
        img = self._preprocess_remove_text(img)

        # Stage 2: Extract palette
        print("\n[2/6] Extracting unified palette...")
        if self.forced_palette:
            palette = self.forced_palette
            print(f"      Using forced palette: {self._fmt_palette(palette)}")
        else:
            # Try AI-powered palette extraction first, fall back to algorithmic
            if self.ai_analyzer and self.ai_analyzer.available:
                palette = self.palette_extractor.extract_with_ai(
                    img, self.ai_analyzer, self.platform.colors_per_palette)
            else:
                palette = self.palette_extractor.extract_from_image(
                    img, self.platform.colors_per_palette)
                print(f"      Extracted from image: {self._fmt_palette(palette)}")

        converter = SpriteConverter(platform=self.platform, palette=palette)

        if category == 'background':
            print("\n[3/6] Processing full-screen background (Tiled)...")
            
            # 1. Index the whole image
            # We assume the input image is already 256x240 or we scale it?
            # For now, let's assume input is correct or we scale to screen size?
            # NES screen is 256x240. If image is different, we should probably resize nicely.
            target_w = self.platform.screen_width
            target_h = self.platform.screen_height
            
            if img.width != target_w or img.height != target_h:
                print(f"      Resizing background {img.width}x{img.height} -> {target_w}x{target_h} (Bespoke/Cover)")
                img = converter.scale_image(img, target_w, target_h, fit_mode='COVER')
                
            indexed = converter.index_sprite(img)
            
            # 2. Generate Nametable + deduplicated tiles
            if not hasattr(self.platform, 'generate_background_data'):
                print("      [ERROR] Platform does not support full-screen background generation!")
                return {'success': False, 'error': 'Platform not supported'}
                
            nametable_data, chr_data = self.platform.generate_background_data(indexed)
            
            # 3. Save Artifacts
            bg_name = os.path.splitext(os.path.basename(input_path))[0]
            
            # Save raw files
            with open(os.path.join(output_dir, f"{bg_name}.nam"), 'wb') as f:
                f.write(nametable_data)
            with open(os.path.join(output_dir, f"{bg_name}.chr"), 'wb') as f:
                f.write(chr_data)
            indexed.save(os.path.join(output_dir, f"{bg_name}_indexed.png"))
            
            print(f"      Created: {bg_name}.nam ({len(nametable_data)} bytes)")
            print(f"      Created: {bg_name}.chr ({len(chr_data)} bytes)")
            
            # 4. Save Metadata
            metadata = {
                'source': input_path,
                'category': 'background',
                'platform': self.platform_name,
                'width': target_w,
                'height': target_h,
                'palette_hex': self._fmt_palette(palette),
                'unique_tiles': len(chr_data) // 16,
                'nametable_file': f"{bg_name}.nam",
                'chr_file': f"{bg_name}.chr"
            }
             
            with open(os.path.join(output_dir, 'metadata.json'), 'w') as f:
                json.dump(metadata, f, indent=2)
                
            print(f"\n{'='*60}")
            print("  Background Processing Complete!")
            return {'success': True, 'metadata': metadata}

        # Stage 3: Detect sprites
        print("\n[3/6] Detecting sprites...")
        bboxes = self.detector.detect(img)
        print(f"      Found {len(bboxes)} raw regions")

        # Filter out text-like regions (optional but enabled by default)
        if self.filter_text:
            bboxes = self.detector.filter_text_regions(img, bboxes)
            print(f"      After text filter: {len(bboxes)} sprites")
        else:
            print(f"      Text filtering disabled")

        if not bboxes:
            if self.ai_analyzer and self.ai_analyzer.available:
                print("      [WARN] No sprites detected algorithmically. Falling back to specific AI detection request.")
                # We will proceed with an empty list, and hope the AI finds them.
                # Adding a dummy 'whole image' bbox might confuse it if the prompts expects 'detected sprites'.
                # Let's trust the refined prompt logic or specific handling below.
            else:
                print("      [ERROR] No sprites detected after filtering!")
                return {'success': False, 'error': 'No sprites detected'}

        # Create sprite info with default labels
        inferred_type = category or self._infer_type(input_path)
        sprites = []
        for i, bbox in enumerate(bboxes):
            sprites.append(SpriteInfo(
                id=i + 1,
                bbox=bbox,
                sprite_type=inferred_type,
                action="frame",
                frame_index=i + 1,
                description=f"{inferred_type}_frame_{i+1}"
            ))

        # Stage 4: AI Semantic Analysis (and Bound Correction)
        print("\n[4/6] AI semantic analysis & bound correction...")
        analysis_raw = {} 
        
        if self.ai_analyzer and self.ai_analyzer.available:
            if self.consensus_mode and self.consensus_engine:
                analysis = self.consensus_engine.resolve(img, sprites, output_dir)
            else:
                analysis = self.ai_analyzer.analyze(img, sprites)
            analysis_raw = analysis # Save for debug
            
            # Check failure flag
            self.ai_failed = analysis.get('ai_failed', False)
            
            # --- AI BOUNDING BOX TRUST LOGIC ---
            # If AI returns bounding boxes, we use them to OVERRIDE the algorithmic detection.
            # This is crucial because AI "sees" the whole sprite (including internal blacks)
            # whereas algorithm might chop it up.
            
            ai_sprites_data = analysis.get('sprites', [])
            if ai_sprites_data:
                print(f"      [AI-Trust] AI returned {len(ai_sprites_data)} sprites. TRUSTING AI BOUNDS.")
                
                new_sprites = []
                for ai_s in ai_sprites_data:
                    # Parse AI bounds (safely)
                    try:
                        # Depending on model, it might return 'bbox': [x,y,w,h] or objects
                        # The base provider standardizes this, but let's be safe.
                        if 'bbox' in ai_s:
                            ax, ay, aw, ah = ai_s['bbox']
                            # Clamp to image
                            ax = max(0, ax)
                            ay = max(0, ay)
                            aw = min(img.width - ax, aw)
                            ah = min(img.height - ay, ah)
                            
                            # Create new sprite info
                            # Note: reusing ID/Action/Desc from AI directly
                            new_s = SpriteInfo(
                                id=ai_s.get('id', len(new_sprites)+1),
                                bbox=BoundingBox(ax, ay, aw, ah),
                                sprite_type=ai_s.get('type', 'sprite'),
                                action=ai_s.get('action', 'idle'),
                                description=ai_s.get('description', 'ai_detected')
                            )
                            new_sprites.append(new_s)
                    except Exception as e:
                        print(f"      [WARN] Failed to process AI sprite data: {e}")
                
                # If we successfully parsed AI sprites, replace the algorithmic ones
                if new_sprites:
                    sprites = new_sprites
                    print(f"      [AI-Trust] Defined {len(sprites)} sprites from AI Analysis.")
                else:
                    print("      [AI-Trust] Could not parse AI bounds, falling back to algorithmic detection.")
                    # Apply labels to algorithmic sprites as fallback
                    sprites = self.ai_analyzer.apply_labels(sprites, analysis)
            else:
                print("      [WARN] AI analysis returned no results, using defaults")
        else:
            print("      Skipped (AI not available)")
            
        # SAVE DEBUG ARTIFACTS
        self._save_debug_artifacts(output_dir, img, sprites, analysis_raw)

        # Stage 4.5: Collision Analysis (optional)
        if self.collision_enabled:
            print("\n[4.5/6] AI collision analysis...")
            sprites = self._analyze_collision_masks(img, sprites, output_dir)

        # Stage 5: Convert sprites
        print(f"\n[5/6] Converting {len(sprites)} sprites...")
        results = []

        ext = converter.output_extension
        # --- BESPOKE: FILE-LEVEL TARGET SIZE ---
        current_target_size = self.target_size
        if self.platform_name == 'NES':
             max_dim = 0
             for s in sprites:
                 max_dim = max(max_dim, s.bbox.width, s.bbox.height)
             
             if max_dim > 48:
                 current_target_size = 32
                 print(f"      [Auto-Resize] Max Dimension {max_dim}px -> Boss Tier (32x32) for ALL sprites.")
             elif max_dim > 16:
                 current_target_size = 16
                 print(f"      [Auto-Resize] Max Dimension {max_dim}px -> Standard Tier (16x16) for ALL sprites.")
             else:
                 current_target_size = 16 # Default to 16x16 container for tiny sprites

        for sprite in sprites:
            
            cropped = img.crop(sprite.bbox.crop_box())
            scaled = converter.scale_sprite(cropped, current_target_size)
            indexed = converter.index_sprite(scaled)
            tile_data = converter.generate_tile_data(indexed)

            # Use description for filename
            filename = f"sprite_{sprite.id:02d}_{sprite.description}"

            scaled.save(os.path.join(output_dir, f"{filename}_scaled.png"))
            indexed.save(os.path.join(output_dir, f"{filename}_indexed.png"))

            tile_path = os.path.join(output_dir, f"{filename}{ext}")
            with open(tile_path, 'wb') as f:
                f.write(tile_data)

            results.append({
                'sprite': sprite,
                'tile_path': tile_path,
                'tile_size': len(tile_data)
            })

            print(f"      Sprite {sprite.id}: {sprite.bbox.width}x{sprite.bbox.height} -> "
                  f"{self.target_size}x{self.target_size} [{sprite.description}]")

        # Stage 6: Create combined tile bank
        combined_name = f"sprites{ext}"
        print(f"\n[6/6] Creating combined {self.platform_name} tile bank...")
        combined = bytearray()
        for r in results[:32]:
            with open(r['tile_path'], 'rb') as f:
                combined.extend(f.read())

        # Pad to standard bank size (platform-specific)
        bank_size = 8192 if self.platform_name == "NES" else len(combined)
        while len(combined) < bank_size:
            combined.append(0)

        combined_path = os.path.join(output_dir, combined_name)
        with open(combined_path, 'wb') as f:
            f.write(combined)
        print(f"      Created: {combined_name} ({len(combined)} bytes)")

        # Export collision data (if enabled)
        if self.collision_enabled:
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            collision_header_path = os.path.join(output_dir, f"{base_name}_collision.h")
            collision_json_path = os.path.join(output_dir, f"{base_name}_collision.json")
            collision_masks_path = os.path.join(output_dir, f"{base_name}_collision_masks.h")

            export_collision_header(sprites, collision_header_path, base_name)
            export_collision_json(sprites, collision_json_path)
            export_collision_masks(sprites, collision_masks_path, base_name)

            # Generate debug overlay showing collision boxes
            debug_overlay_path = os.path.join(output_dir, "debug", f"{base_name}_collision_debug.png")
            generate_debug_overlay(sprites, input_path, debug_overlay_path)

        # Save metadata
        metadata = {
            'source': input_path,
            'timestamp': datetime.now().isoformat(),
            'platform': self.platform_name,
            'target_size': self.target_size,
            'colors_per_palette': self.platform.colors_per_palette,
            'bits_per_pixel': self.platform.bits_per_pixel,
            'tile_format': self.platform.output_extension,
            'unified_palette': palette,
            'palette_hex': self._fmt_palette(palette),
            'ai_provider': self.ai_analyzer.provider_name if self.ai_analyzer else None,
            'ai_failed': getattr(self, 'ai_failed', False),
            'sprites_count': len(sprites),
            # HAL Tier information
            'tier': self.platform.get_tier_info(),
            'tier_warnings': self.platform.validate_sprite_count(len(sprites)),
            'collision_enabled': self.collision_enabled,
            'sprites': [
                {
                    'id': r['sprite'].id,
                    'type': r['sprite'].sprite_type,
                    'action': r['sprite'].action,
                    'description': r['sprite'].description,
                    'frame': r['sprite'].frame_index,
                    'bbox': asdict(r['sprite'].bbox),
                    'tile_file': os.path.basename(r['tile_path']),
                    'tile_size': r['tile_size'],
                    'collision': r['sprite'].collision.to_dict() if r['sprite'].collision else None
                }
                for r in results
            ]
        }

        with open(os.path.join(output_dir, 'metadata.json'), 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"\n{'='*60}")
        print("  Processing Complete!")
        print(f"{'='*60}")
        print(f"  Platform: {self.platform_name}")
        print(f"  Tier:     {self.platform.hal_tier_name}")
        print(f"  Sprites:  {len(results)}")
        print(f"  Palette:  {self._fmt_palette(palette)}")

        # Tier validation warnings
        tier_warnings = self.platform.validate_sprite_count(len(results))
        if tier_warnings:
            print(f"\n  {'!'*50}")
            print("  TIER WARNINGS:")
            for warning in tier_warnings:
                print(f"    - {warning}")
            print(f"  {'!'*50}")
            print(f"\n  Suggested tier: {self.platform.suggest_tier(len(results))}")

        # Platform-specific output hints
        if self.platform_name == "NES":
            print(f"\n  For NES game_main.asm:")
            print(f"    .byte ${palette[0]:02X}, ${palette[1]:02X}, ${palette[2]:02X}, ${palette[3]:02X}")
        elif self.platform_name == "Genesis":
            print(f"\n  For Genesis palette (CRAM format):")
            print(f"    dc.w ${palette[0]:03X}, ${palette[1]:03X}, ${palette[2]:03X}, ${palette[3]:03X}")
        elif self.platform_name == "SNES":
            print(f"\n  For SNES palette (CGRAM format):")
            print(f"    .word ${palette[0]:04X}, ${palette[1]:04X}, ${palette[2]:04X}, ${palette[3]:04X}")

        return {'success': True, 'metadata': metadata, 'palette': palette}

    def process_batch(self, input_dir: str, output_dir: str) -> Dict[str, Any]:
        print(f"\n{'='*60}")
        print("  NEON SURVIVORS - Batch Processing")
        print(f"{'='*60}")

        assets = []
        for f in os.listdir(input_dir):
            if f.lower().endswith('.png'):
                category = self._categorize(f)
                assets.append({
                    'filename': f,
                    'path': os.path.join(input_dir, f),
                    'category': category,
                    'size': ASSET_CATEGORIES.get(category, {}).get('size', 32)
                })

        print(f"  Found {len(assets)} assets\n")

        by_cat = {}
        for a in assets:
            cat = a['category']
            if cat not in by_cat:
                by_cat[cat] = []
            by_cat[cat].append(a)

        for cat, items in sorted(by_cat.items()):
            print(f"  [{cat}] {len(items)} files")

        results = {'success': 0, 'failed': 0}

        for i, asset in enumerate(assets):
            print(f"\n[{i+1}/{len(assets)}] {asset['filename']}")

            out_path = os.path.join(output_dir, asset['category'],
                                    Path(asset['filename']).stem)

            self.target_size = asset['size']

            try:
                result = self.process(asset['path'], out_path, asset['category'])
                if result['success']:
                    results['success'] += 1
                else:
                    results['failed'] += 1
            except Exception as e:
                print(f"  [ERROR] {e}")
                results['failed'] += 1

        print(f"\n{'='*60}")
        print(f"  Batch Complete: {results['success']} success, {results['failed']} failed")
        print(f"{'='*60}")

        return results

    def _categorize(self, filename: str) -> str:
        lower = filename.lower()
        for cat, config in ASSET_CATEGORIES.items():
            for prefix in config['prefixes']:
                if lower.startswith(prefix):
                    return cat
        return 'misc'

    def _infer_type(self, path: str) -> str:
        return self._categorize(os.path.basename(path))

    def _fmt_palette(self, palette: List[int]) -> str:
        return ', '.join(f'${c:02X}' for c in palette)

    def _preprocess_remove_text(self, img: Image.Image) -> Image.Image:
        """
        Remove AI-generated text labels from image by cropping margins.
        """
        width, height = img.size

        # Crop margins where AI text labels typically appear
        # Top: 10% (labels like "SYNTHWAVE BACKGROUND")
        # Bottom: 10% (watermarks, credits)
        # Sides: 2% (edge artifacts)
        top_crop = int(height * 0.10)
        bottom_crop = int(height * 0.90)
        left_crop = int(width * 0.02)
        right_crop = int(width * 0.98)

        cropped = img.crop((left_crop, top_crop, right_crop, bottom_crop))
        new_width, new_height = cropped.size

        print(f"      Cropped: {width}x{height} -> {new_width}x{new_height} (AI text labels removed)")

        return cropped

    def _save_debug_artifacts(self, output_dir: str, img: Image.Image, sprites: List[SpriteInfo], ai_raw: Dict):
        """Save debug images and JSON to help diagnostics"""
        debug_dir = os.path.join(output_dir, "debug")
        os.makedirs(debug_dir, exist_ok=True)
        
        # 1. Save Raw AI JSON
        with open(os.path.join(debug_dir, "ai_response_raw.json"), 'w') as f:
            json.dump(ai_raw, f, indent=2)
            
        # 2. Save Visual Bounding Boxes
        try:
            debug_img = img.copy()
            draw = ImageDraw.Draw(debug_img)
            
            for s in sprites:
                x, y, w, h = s.bbox.x, s.bbox.y, s.bbox.width, s.bbox.height
                # Draw green box
                draw.rectangle([x, y, x+w, y+h], outline=(0, 255, 0, 255), width=2)
                # Draw ID
                draw.text((x, y-10), str(s.id), fill=(0, 255, 0, 255))
                
            debug_img.save(os.path.join(debug_dir, "debug_ai_bounds.png"))
            print(f"      [DEBUG] Saved debug artifacts to {debug_dir}")
        except Exception as e:
            print(f"      [DEBUG] Failed to save debug image: {e}")

    def _analyze_collision_masks(self, img: Image.Image, sprites: List[SpriteInfo],
                                  output_dir: str) -> List[SpriteInfo]:
        """
        Generate collision data for each detected sprite using AI vision analysis.

        This method crops each sprite individually and sends it to the AI analyzer
        to determine appropriate hitbox and hurtbox collision boundaries.

        Args:
            img: Full source image
            sprites: List of detected sprites with bounding boxes
            output_dir: Output directory for debug artifacts

        Returns:
            Updated list of sprites with collision data attached
        """
        if not self.ai_analyzer or not self.ai_analyzer.available:
            print("      [WARN] AI analyzer not available for collision detection")
            return sprites

        total = len(sprites)
        success = 0
        failed = 0

        for i, sprite in enumerate(sprites):
            print(f"      [{i+1}/{total}] Analyzing collision for {sprite.sprite_type} "
                  f"frame {sprite.frame_index}...")

            try:
                # Crop individual sprite from source image
                sprite_img = img.crop(sprite.bbox.crop_box())

                # Get AI collision analysis
                collision_data = self.ai_analyzer.analyze_collision(
                    sprite_img,
                    sprite_type=sprite.sprite_type,
                    use_cache=True
                )

                if collision_data and 'hitbox' in collision_data and 'hurtbox' in collision_data:
                    # Create CollisionMask from AI response
                    hitbox = BoundingBox.from_dict(collision_data['hitbox'])
                    hurtbox = BoundingBox.from_dict(collision_data['hurtbox'])

                    # Check if we need pixel mask (low confidence or boss type)
                    pixel_mask = None
                    mask_type = "aabb"

                    confidence = collision_data.get('confidence', 0.8)
                    if confidence < 0.7 or sprite.sprite_type == 'boss':
                        print(f"            Generating pixel mask (confidence: {confidence:.2f})")
                        pixel_mask = self.ai_analyzer.generate_pixel_mask(sprite_img)
                        mask_type = "pixel"

                    sprite.collision = CollisionMask(
                        hitbox=hitbox,
                        hurtbox=hurtbox,
                        pixel_mask=pixel_mask,
                        mask_type=mask_type,
                        confidence=confidence,
                        reasoning=collision_data.get('reasoning', '')
                    )

                    success += 1
                    print(f"            Hitbox: {hitbox.width}x{hitbox.height} @ ({hitbox.x},{hitbox.y})")
                    print(f"            Hurtbox: {hurtbox.width}x{hurtbox.height} @ ({hurtbox.x},{hurtbox.y})")
                else:
                    failed += 1
                    print(f"            [WARN] Invalid collision data returned")

            except Exception as e:
                failed += 1
                print(f"            [ERROR] Collision analysis failed: {e}")

        print(f"\n      Collision analysis complete: {success} success, {failed} failed")
        return sprites


# =============================================================================
# CLI
# =============================================================================

def parse_palette(s: str) -> List[int]:
    parts = s.replace('$', '').replace(' ', '').split(',')
    return [int(p, 16) for p in parts]


def _handle_pixellab_8dir(args, pipeline, palette):
    """Handle --pixellab-8dir: Generate 8 directional sprites from input."""
    try:
        from asset_generators.pixellab_client import (
            PixelLabClient, generate_genesis_8_directions
        )
        from PIL import Image
    except ImportError as e:
        print(f"[Error] PixelLab client not available: {e}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print("  PixelLab v2: 8-Direction Generation")
    print(f"{'='*60}\n")

    # Load reference image
    ref_img = Image.open(args.input)
    print(f"  Input: {args.input} ({ref_img.width}x{ref_img.height})")

    # Get palette name if using --force-palette
    palette_name = args.force_palette if hasattr(args, 'force_palette') else None

    # Generate 8 directions
    client = PixelLabClient()
    directions = generate_genesis_8_directions(
        client,
        ref_img,
        width=args.sprite_size,
        height=args.sprite_size,
        palette_name=palette_name,
    )

    if not directions:
        print("[Error] 8-direction generation failed")
        sys.exit(1)

    # Save outputs
    os.makedirs(args.output, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(args.input))[0]
    direction_names = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

    for i, (img, dir_name) in enumerate(zip(directions, direction_names)):
        out_path = os.path.join(args.output, f"{base_name}_{dir_name}.png")
        img.save(out_path)
        print(f"  Saved: {out_path}")

    # Create sprite sheet (8x1)
    sheet_width = args.sprite_size * 8
    sheet_height = args.sprite_size
    sheet = Image.new('RGBA', (sheet_width, sheet_height), (255, 0, 255, 0))
    for i, img in enumerate(directions):
        sheet.paste(img, (i * args.sprite_size, 0))

    sheet_path = os.path.join(args.output, f"{base_name}_8dir_sheet.png")
    sheet.save(sheet_path)
    print(f"  Sprite sheet: {sheet_path}")
    print(f"\n  Session cost: ${client.get_session_cost():.4f}")


def _handle_pixellab_tileset(args, pipeline, palette):
    """Handle --pixellab-tileset: Generate seamless tileset."""
    try:
        from asset_generators.pixellab_client import (
            PixelLabClient, generate_genesis_tileset
        )
    except ImportError as e:
        print(f"[Error] PixelLab client not available: {e}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print("  PixelLab v2: Tileset Generation")
    print(f"{'='*60}\n")

    # Use input as description if it's not a file path
    description = args.input
    if os.path.exists(args.input):
        # Use filename as description hint
        description = os.path.splitext(os.path.basename(args.input))[0].replace('_', ' ')

    print(f"  Description: {description}")

    # Get palette name
    palette_name = args.force_palette if hasattr(args, 'force_palette') else None

    # Tile size (16 for Genesis is common)
    tile_size = 16 if args.sprite_size <= 16 else 32

    # Generate tileset
    client = PixelLabClient()
    tileset = generate_genesis_tileset(
        client,
        description,
        tile_size=tile_size,
        palette_name=palette_name,
    )

    if not tileset:
        print("[Error] Tileset generation failed")
        sys.exit(1)

    # Save output
    os.makedirs(args.output, exist_ok=True)
    safe_name = description.replace(' ', '_')[:32]
    out_path = os.path.join(args.output, f"{safe_name}_tileset.png")
    tileset.save(out_path)
    print(f"  Saved: {out_path} ({tileset.width}x{tileset.height})")
    print(f"\n  Session cost: ${client.get_session_cost():.4f}")


def main():
    parser = argparse.ArgumentParser(
        description='Retro Sprite Pipeline v5.2 - 13 Retro Platforms Support',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # NES (default platform)
    python unified_pipeline.py player.png -o output/
    python unified_pipeline.py player.png -o output/ --platform nes

    # Sega Genesis / Megadrive
    python unified_pipeline.py player.png -o output/ --platform genesis
    python unified_pipeline.py player.png -o output/ --platform megadrive

    # Super Nintendo / Super Famicom
    python unified_pipeline.py player.png -o output/ --platform snes

    # PC Engine / TurboGrafx-16
    python unified_pipeline.py player.png -o output/ --platform pce

    # Commodore Amiga
    python unified_pipeline.py player.png -o output/ --platform amiga

    # With AI labeling
    python unified_pipeline.py player.png -o output/ --ai groq --platform genesis

    # Force specific palette (platform-specific format)
    python unified_pipeline.py player.png -o output/ --palette 0F,24,2C,30 --platform nes

    # Batch process for multiple platforms
    python unified_pipeline.py --batch gfx/ai_output/ -o gfx/processed/nes/ --platform nes
    python unified_pipeline.py --batch gfx/ai_output/ -o gfx/processed/genesis/ --platform genesis

Supported Platforms:
    nes, famicom       - Nintendo Entertainment System (2bpp, 4 colors, .chr)
    genesis, megadrive - Sega Genesis/Megadrive (4bpp, 16 colors, .bin)
    snes, sfc          - Super Nintendo (4bpp, 16 colors, .bin)
    pce, turbografx    - PC Engine/TurboGrafx-16 (4bpp, 16 colors, .bin)
    amiga              - Commodore Amiga (4bpp planar, 16 colors, .raw)

AI Providers (set API key in .env or environment):
    GROQ_API_KEY        - Groq (fastest, Llama 4 vision)
    GEMINI_API_KEY      - Google Gemini
    OPENAI_API_KEY      - OpenAI GPT-4 Vision
    ANTHROPIC_API_KEY   - Anthropic Claude
    XAI_API_KEY         - xAI Grok Vision
""")

    parser.add_argument('input', nargs='?', help='Input PNG file')
    parser.add_argument('-o', '--output', required=True, help='Output directory')
    parser.add_argument('--batch', help='Batch process directory')
    parser.add_argument('--platform', '-p', type=str, default='nes',
                       choices=list(PLATFORMS.keys()),
                       help='Target platform (default: nes). See --help for full list.')
    parser.add_argument('--size', type=int, default=32, help='Target sprite size')
    parser.add_argument('--palette', type=str, help='Force palette (e.g., 0F,24,2C,30)')
    parser.add_argument('--category', help='Asset category hint')
    parser.add_argument('--ai', type=str,
                       choices=['groq', 'gemini', 'openai', 'anthropic', 'grok', 'xai', 'pollinations'],
                       help='Preferred AI provider')
    parser.add_argument('--no-ai', action='store_true', help='Disable AI analysis')
    parser.add_argument('--no-text-filter', action='store_true',
                       help='Disable text/label filtering (keep all detected regions)')
    parser.add_argument('--consensus', action='store_true',
                       help='Enable multi-model consensus validation (slow but accurate)')
    parser.add_argument('--format', type=str, default='ca65',
                       help='Output assembly format (e.g., ca65, asm68k, wla-dx)')
    parser.add_argument('--mode', choices=['default', 'generative'], default='default', help="Pipeline mode")
    parser.add_argument('--strict', action='store_true', help="Enforce strict hardware limits on AI output")
    parser.add_argument('--optimize', action='store_true', help="Enable advanced tile optimization (deduplication/mirroring)")
    parser.add_argument('--reserved-height', type=int, default=0, help="Reserved height for status bar (MMC3 split)")
    parser.add_argument('--collision', action='store_true',
                       help="Enable AI collision mask generation (hitbox/hurtbox analysis)")

    # SGDK/Genesis-specific validation flags (Phase 0.4)
    parser.add_argument('--validate-only', action='store_true',
                       help="Run SGDK validation checks without processing (pre-flight check)")
    parser.add_argument('--force-palette', type=str, metavar='NAME',
                       help="Force a predefined Genesis palette (e.g., player_warm, enemy_cool)")
    parser.add_argument('--generate-res', action='store_true',
                       help="Generate SGDK resources.res file for sprites")
    parser.add_argument('--sprite-size', type=int, choices=[8, 16, 24, 32], default=32,
                       help="Target SGDK sprite size (default: 32)")
    parser.add_argument('--offline', action='store_true',
                       help="Offline mode - skip all AI calls, use fallback strategies")

    # PixelLab v2 API integration (Phase 1)
    parser.add_argument('--pixellab-resize', action='store_true',
                       help="Use PixelLab AI resize for oversized images (v2 API)")
    parser.add_argument('--pixellab-8dir', action='store_true',
                       help="Generate 8-directional sprites from input (v2 API)")
    parser.add_argument('--pixellab-tileset', action='store_true',
                       help="Process input as tileset with seamless tiles (v2 API)")
    parser.add_argument('--pixellab-v2', action='store_true',
                       help="Prefer v2 API for PixelLab operations")
    args = parser.parse_args()

    # Handle --offline mode: disable AI
    use_ai = not args.no_ai and not args.offline
    if args.offline:
        print("[Offline Mode] AI features disabled, using fallback strategies")

    # Handle --force-palette for Genesis
    palette = None
    if args.force_palette:
        try:
            from pipeline.palettes import get_genesis_palette
            palette = get_genesis_palette(args.force_palette)
            if palette is None:
                from pipeline.palettes import GENESIS_PALETTES
                print(f"[Error] Unknown palette: {args.force_palette}")
                print(f"        Available: {', '.join(GENESIS_PALETTES.keys())}")
                sys.exit(1)
            print(f"[Palette] Using Genesis palette: {args.force_palette}")
        except ImportError:
            print("[Warning] Genesis palettes not available, using --palette if provided")
            palette = parse_palette(args.palette) if args.palette else None
    elif args.palette:
        palette = parse_palette(args.palette)

    # Handle --validate-only for SGDK pre-flight checks
    if args.validate_only:
        if not args.input:
            print("[Error] --validate-only requires an input file")
            sys.exit(1)
        try:
            from pipeline.sgdk_format import validate_sgdk_sprite
            from PIL import Image
            img = Image.open(args.input)
            result = validate_sgdk_sprite(img)
            print(f"\n{'='*60}")
            print(f"  SGDK Validation Report: {args.input}")
            print(f"{'='*60}\n")
            print(f"  Valid: {'YES' if result.valid else 'NO'}")
            print(f"  Size: {img.size[0]}x{img.size[1]}")
            if result.warnings:
                print(f"\n  Warnings:")
                for w in result.warnings:
                    print(f"    - {w}")
            if result.errors:
                print(f"\n  Errors:")
                for e in result.errors:
                    print(f"    - {e}")
            if result.valid:
                print(f"\n  [OK] Sprite is SGDK-compatible")
            else:
                print(f"\n  [FAIL] Sprite needs processing before SGDK import")
            sys.exit(0 if result.valid else 1)
        except ImportError as e:
            print(f"[Error] SGDK validation module not available: {e}")
            sys.exit(1)

    # Use --sprite-size for Genesis, --size for others (backward compat)
    target_size = args.sprite_size if args.platform.lower() in ('genesis', 'megadrive') else args.size

    pipeline = UnifiedPipeline(
        target_size=target_size,
        palette=palette,
        use_ai=use_ai,
        ai_provider=args.ai,
        filter_text=not args.no_text_filter,
        platform=args.platform,
        consensus_mode=args.consensus,
        output_format=args.format,
        mode=args.mode,
        strict=args.strict,
        collision=args.collision,
        offline_mode=args.offline
    )

    # Apply advanced optimization flags
    pipeline.optimize_tiles = args.optimize
    pipeline.reserved_status_height = args.reserved_height

    # Store flags for later use
    pipeline.generate_res = args.generate_res
    pipeline.pixellab_v2 = args.pixellab_v2
    pipeline.pixellab_resize = args.pixellab_resize
    pipeline.pixellab_8dir = args.pixellab_8dir
    pipeline.pixellab_tileset = args.pixellab_tileset

    # PixelLab v2 special modes (before normal processing)
    if args.pixellab_8dir and args.input:
        _handle_pixellab_8dir(args, pipeline, palette)
        return
    if args.pixellab_tileset and args.input:
        _handle_pixellab_tileset(args, pipeline, palette)
        return

    if args.batch:
        pipeline.process_batch(args.batch, args.output)
    elif args.input:
        # Infer category if not provided
        category = args.category or pipeline._infer_type(args.input)
        result = pipeline.process(args.input, args.output, category)

        # Generate .res file if requested
        if args.generate_res and result and args.platform.lower() in ('genesis', 'megadrive'):
            try:
                from pipeline.sgdk_format import generate_res_file
                res_content = generate_res_file(
                    os.path.basename(args.input).replace('.png', ''),
                    args.output
                )
                res_path = os.path.join(args.output, 'resources.res')
                with open(res_path, 'w') as f:
                    f.write(res_content)
                print(f"\n[SGDK] Generated {res_path}")
            except ImportError as e:
                print(f"[Warning] Could not generate .res file: {e}")
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
