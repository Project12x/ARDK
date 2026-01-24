"""
Collision Visualization and Debug Tools.

This module provides tools for visualizing, debugging, and exporting collision
data for sprites. It helps developers verify that AI-generated or manually
defined collision boxes are correctly positioned relative to sprite artwork.

Key Features:
    - Render collision boxes overlaid on sprites (hitbox, hurtbox, trigger)
    - Generate scaled debug images for visual inspection
    - Export animated GIFs showing collision boxes per animation frame
    - Create debug sprite sheets with collision overlays for in-game testing
    - Color-coded visualization (red=hitbox, green=hurtbox, blue=trigger)

Why Use This Module:
    - Verify AI-generated collision data is accurate
    - Debug collision issues without running the game
    - Create documentation images showing hitbox/hurtbox placement
    - Generate debug assets for in-game collision visualization

Usage:
    >>> from pipeline.collision_editor import CollisionVisualizer
    >>> from pipeline.platforms import SpriteInfo, BoundingBox
    >>>
    >>> # Create visualizer
    >>> viz = CollisionVisualizer()
    >>>
    >>> # Render single sprite with collision overlay
    >>> overlay = viz.render_overlay(sprite_image, hitbox, hurtbox, scale=4)
    >>> overlay.save("debug_sprite.png")
    >>>
    >>> # Generate animated GIF with collision boxes
    >>> viz.render_animation(frames, collision_list, "debug_anim.gif", fps=10)
    >>>
    >>> # Export debug sprite sheet
    >>> viz.export_debug_sheet(sprite_infos, sprite_sheet, "debug_sheet.png")

Color Scheme:
    - Hitbox (damage dealing): Red with 50% transparency
    - Hurtbox (damage receiving): Green with 50% transparency
    - Trigger (interaction zones): Blue with 50% transparency
    - Sprite outline: White dashed line

Phase Implementation:
    - Phase 2.2.3: Collision visualization and debug tools
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import Image as PIL_Image

# Optional PIL import
try:
    from PIL import Image, ImageDraw
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


@dataclass
class CollisionBox:
    """
    A collision box with position, size, and type.

    This is a simplified representation for visualization purposes.
    Can be created from SpriteInfo collision data or manually defined.

    Attributes:
        x: X offset from sprite origin (top-left).
        y: Y offset from sprite origin (top-left).
        width: Box width in pixels.
        height: Box height in pixels.
        box_type: Type of collision ("hitbox", "hurtbox", "trigger").
        label: Optional label for the box (shown in debug output).
    """
    x: int
    y: int
    width: int
    height: int
    box_type: str = "hitbox"
    label: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any], box_type: str = "hitbox") -> 'CollisionBox':
        """Create CollisionBox from dictionary (e.g., from JSON)."""
        return cls(
            x=data.get('x', 0),
            y=data.get('y', 0),
            width=data.get('width', data.get('w', 8)),
            height=data.get('height', data.get('h', 8)),
            box_type=box_type,
            label=data.get('label', '')
        )


class CollisionVisualizer:
    """
    Visualize collision boxes overlaid on sprite artwork.

    This class provides methods for rendering collision data as colored
    overlays on sprite images, useful for debugging and documentation.

    Color Configuration:
        Default colors use semi-transparent fills with solid outlines:
        - Hitbox: Red (damage dealing zones)
        - Hurtbox: Green (vulnerable zones)
        - Trigger: Blue (interaction zones)

    Example:
        >>> viz = CollisionVisualizer()
        >>>
        >>> # Customize colors if needed
        >>> viz.colors['hitbox'] = (255, 100, 0, 128)  # Orange hitbox
        >>>
        >>> # Render with 4x scale for visibility
        >>> overlay = viz.render_overlay(sprite, hitbox, hurtbox, scale=4)
        >>> overlay.save("debug.png")
    """

    def __init__(self):
        """Initialize visualizer with default color scheme."""
        # RGBA colors for different collision types
        # Format: (R, G, B, A) where A is 0-255 transparency
        self.colors = {
            'hitbox': (255, 0, 0, 128),      # Red, 50% transparent
            'hurtbox': (0, 255, 0, 128),     # Green, 50% transparent
            'trigger': (0, 0, 255, 128),     # Blue, 50% transparent
            'outline': (255, 255, 255, 255), # White, solid
            'sprite_outline': (200, 200, 200, 180),  # Light gray
        }

        # Outline colors (solid versions for borders)
        self.outline_colors = {
            'hitbox': (255, 0, 0, 255),
            'hurtbox': (0, 255, 0, 255),
            'trigger': (0, 0, 255, 255),
        }

    def render_overlay(
        self,
        sprite: 'PIL_Image.Image',
        hitbox: Optional[CollisionBox] = None,
        hurtbox: Optional[CollisionBox] = None,
        trigger: Optional[CollisionBox] = None,
        scale: int = 4,
        show_sprite_outline: bool = True,
        show_labels: bool = True,
    ) -> Optional['PIL_Image.Image']:
        """
        Render sprite with collision boxes overlaid.

        Creates a scaled-up image with semi-transparent collision boxes
        drawn on top of the sprite artwork. Useful for debugging and
        documentation.

        Args:
            sprite: PIL Image of the sprite (any size).
            hitbox: Optional hitbox collision data.
            hurtbox: Optional hurtbox collision data.
            trigger: Optional trigger zone collision data.
            scale: Scale factor for output image (default 4x).
            show_sprite_outline: Draw outline around sprite bounds.
            show_labels: Draw text labels on collision boxes.

        Returns:
            PIL Image with collision overlay, or None if PIL unavailable.

        Example:
            >>> hitbox = CollisionBox(x=8, y=4, width=16, height=24, box_type="hitbox")
            >>> hurtbox = CollisionBox(x=4, y=0, width=24, height=32, box_type="hurtbox")
            >>> overlay = viz.render_overlay(sprite_img, hitbox, hurtbox, scale=4)
        """
        if not HAS_PIL:
            print("[WARN] PIL not available, cannot render overlay")
            return None

        # Scale up the sprite
        orig_w, orig_h = sprite.size
        scaled_w = orig_w * scale
        scaled_h = orig_h * scale

        # Use nearest neighbor for pixel-perfect scaling
        scaled_sprite = sprite.resize((scaled_w, scaled_h), Image.NEAREST)

        # Convert to RGBA if needed
        if scaled_sprite.mode != 'RGBA':
            scaled_sprite = scaled_sprite.convert('RGBA')

        # Create overlay layer
        overlay = Image.new('RGBA', (scaled_w, scaled_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Draw sprite outline if requested
        if show_sprite_outline:
            draw.rectangle(
                [0, 0, scaled_w - 1, scaled_h - 1],
                outline=self.colors['sprite_outline'],
                width=1
            )

        # Draw collision boxes (hurtbox first so hitbox draws on top)
        boxes = [
            (hurtbox, 'hurtbox'),
            (trigger, 'trigger'),
            (hitbox, 'hitbox'),
        ]

        for box, box_type in boxes:
            if box is None:
                continue

            # Scale box coordinates
            x1 = box.x * scale
            y1 = box.y * scale
            x2 = (box.x + box.width) * scale - 1
            y2 = (box.y + box.height) * scale - 1

            # Draw filled rectangle
            fill_color = self.colors.get(box_type, self.colors['hitbox'])
            draw.rectangle([x1, y1, x2, y2], fill=fill_color)

            # Draw outline
            outline_color = self.outline_colors.get(box_type, (255, 255, 255, 255))
            draw.rectangle([x1, y1, x2, y2], outline=outline_color, width=2)

            # Draw label if requested
            if show_labels and box.label:
                # Simple label at top-left of box
                label_y = max(0, y1 - 12)
                draw.text((x1 + 2, label_y), box.label, fill=outline_color)

        # Composite overlay onto scaled sprite
        result = Image.alpha_composite(scaled_sprite, overlay)

        return result

    def render_sprite_info_overlay(
        self,
        sprite: 'PIL_Image.Image',
        sprite_info: Any,  # SpriteInfo from platforms.py
        scale: int = 4,
    ) -> Optional['PIL_Image.Image']:
        """
        Render overlay using SpriteInfo collision data.

        Convenience method that extracts collision boxes from a SpriteInfo
        object (as produced by the pipeline's collision detection).

        Args:
            sprite: PIL Image of the sprite.
            sprite_info: SpriteInfo object with collision attribute.
            scale: Scale factor for output.

        Returns:
            PIL Image with collision overlay, or None.
        """
        hitbox = None
        hurtbox = None

        if hasattr(sprite_info, 'collision') and sprite_info.collision:
            collision = sprite_info.collision

            # Extract hitbox
            if hasattr(collision, 'hitbox') and collision.hitbox:
                hb = collision.hitbox
                hitbox = CollisionBox(
                    x=getattr(hb, 'x', 0),
                    y=getattr(hb, 'y', 0),
                    width=getattr(hb, 'width', 8),
                    height=getattr(hb, 'height', 8),
                    box_type='hitbox'
                )

            # Extract hurtbox
            if hasattr(collision, 'hurtbox') and collision.hurtbox:
                hb = collision.hurtbox
                hurtbox = CollisionBox(
                    x=getattr(hb, 'x', 0),
                    y=getattr(hb, 'y', 0),
                    width=getattr(hb, 'width', 8),
                    height=getattr(hb, 'height', 8),
                    box_type='hurtbox'
                )

        return self.render_overlay(sprite, hitbox, hurtbox, scale=scale)

    def render_animation(
        self,
        frames: List['PIL_Image.Image'],
        collisions: List[Tuple[Optional[CollisionBox], Optional[CollisionBox]]],
        output_path: str,
        fps: int = 10,
        scale: int = 4,
        loop: bool = True,
    ) -> bool:
        """
        Generate animated GIF with collision boxes per frame.

        Creates an animated GIF showing how collision boxes change
        throughout an animation sequence.

        Args:
            frames: List of PIL Images (animation frames).
            collisions: List of (hitbox, hurtbox) tuples per frame.
                        Use None for frames without collision data.
            output_path: Path to save the GIF.
            fps: Frames per second (default 10).
            scale: Scale factor for output.
            loop: Whether GIF should loop (default True).

        Returns:
            True if successful, False otherwise.

        Example:
            >>> frames = [frame1, frame2, frame3, frame4]
            >>> collisions = [
            ...     (hitbox1, hurtbox1),
            ...     (hitbox2, hurtbox2),
            ...     (hitbox3, hurtbox3),  # Attack frame with larger hitbox
            ...     (hitbox4, hurtbox4),
            ... ]
            >>> viz.render_animation(frames, collisions, "attack_debug.gif")
        """
        if not HAS_PIL:
            print("[WARN] PIL not available, cannot render animation")
            return False

        if not frames:
            print("[WARN] No frames provided")
            return False

        # Pad collisions if shorter than frames
        while len(collisions) < len(frames):
            collisions.append((None, None))

        # Render each frame with collision overlay
        rendered_frames = []
        for i, frame in enumerate(frames):
            hitbox, hurtbox = collisions[i] if i < len(collisions) else (None, None)

            overlay = self.render_overlay(
                frame, hitbox, hurtbox, scale=scale, show_labels=False
            )

            if overlay:
                # Convert to P mode for GIF (with transparency handling)
                if overlay.mode == 'RGBA':
                    # Create background and composite
                    bg = Image.new('RGBA', overlay.size, (32, 32, 32, 255))
                    overlay = Image.alpha_composite(bg, overlay)
                    overlay = overlay.convert('RGB')

                rendered_frames.append(overlay)

        if not rendered_frames:
            print("[WARN] No frames rendered")
            return False

        # Calculate frame duration in milliseconds
        duration = int(1000 / fps)

        # Save as GIF
        try:
            rendered_frames[0].save(
                output_path,
                save_all=True,
                append_images=rendered_frames[1:],
                duration=duration,
                loop=0 if loop else 1,
            )
            print(f"[EXPORT] Animation GIF: {output_path}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save GIF: {e}")
            return False

    def export_debug_sheet(
        self,
        sprites: List[Any],  # List of SpriteInfo or similar
        sheet_image: 'PIL_Image.Image',
        output_path: str,
        scale: int = 2,
        columns: int = 8,
    ) -> bool:
        """
        Export a debug sprite sheet with collision boxes visible.

        Creates a new sprite sheet image with all collision boxes rendered
        as overlays. Useful for importing into the game engine for visual
        debugging during development.

        Args:
            sprites: List of sprite info objects with position and collision data.
            sheet_image: Original sprite sheet image.
            output_path: Path to save the debug sheet.
            scale: Scale factor for output (default 2x).
            columns: Sprites per row in output (default 8).

        Returns:
            True if successful, False otherwise.

        Example:
            >>> # After running collision detection
            >>> sprites = pipeline.detect_sprites(sheet)
            >>> viz.export_debug_sheet(sprites, sheet, "debug_sheet.png")
        """
        if not HAS_PIL:
            print("[WARN] PIL not available, cannot export debug sheet")
            return False

        if not sprites:
            print("[WARN] No sprites provided")
            return False

        # Extract individual sprite images and render overlays
        rendered_sprites = []

        for sprite in sprites:
            # Get sprite bounds
            if hasattr(sprite, 'bbox'):
                bbox = sprite.bbox
                x = getattr(bbox, 'x', 0)
                y = getattr(bbox, 'y', 0)
                w = getattr(bbox, 'width', 32)
                h = getattr(bbox, 'height', 32)
            else:
                # Fallback: try direct attributes
                x = getattr(sprite, 'x', 0)
                y = getattr(sprite, 'y', 0)
                w = getattr(sprite, 'width', 32)
                h = getattr(sprite, 'height', 32)

            # Crop sprite from sheet
            try:
                sprite_img = sheet_image.crop((x, y, x + w, y + h))
            except Exception:
                continue

            # Render with collision overlay
            overlay = self.render_sprite_info_overlay(sprite_img, sprite, scale=scale)

            if overlay:
                rendered_sprites.append(overlay)

        if not rendered_sprites:
            print("[WARN] No sprites rendered")
            return False

        # Calculate output sheet dimensions
        sprite_w = rendered_sprites[0].width
        sprite_h = rendered_sprites[0].height
        rows = (len(rendered_sprites) + columns - 1) // columns
        sheet_w = columns * sprite_w
        sheet_h = rows * sprite_h

        # Create output sheet
        debug_sheet = Image.new('RGBA', (sheet_w, sheet_h), (32, 32, 32, 255))

        # Paste rendered sprites
        for i, sprite_overlay in enumerate(rendered_sprites):
            row = i // columns
            col = i % columns
            x = col * sprite_w
            y = row * sprite_h
            debug_sheet.paste(sprite_overlay, (x, y))

        # Save
        try:
            debug_sheet.save(output_path)
            print(f"[EXPORT] Debug sheet: {output_path} ({len(rendered_sprites)} sprites)")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save debug sheet: {e}")
            return False

    def create_legend(
        self,
        width: int = 200,
        height: int = 100,
        scale: int = 1,
    ) -> Optional['PIL_Image.Image']:
        """
        Create a legend image explaining the color coding.

        Useful for including in documentation or debug outputs.

        Args:
            width: Legend width in pixels.
            height: Legend height in pixels.
            scale: Scale factor.

        Returns:
            PIL Image with legend, or None.
        """
        if not HAS_PIL:
            return None

        img = Image.new('RGBA', (width * scale, height * scale), (32, 32, 32, 255))
        draw = ImageDraw.Draw(img)

        items = [
            ('hitbox', 'Hitbox (damage)', self.colors['hitbox']),
            ('hurtbox', 'Hurtbox (vulnerable)', self.colors['hurtbox']),
            ('trigger', 'Trigger (interact)', self.colors['trigger']),
        ]

        y_offset = 10 * scale
        box_size = 20 * scale
        text_offset = 30 * scale

        for box_type, label, color in items:
            # Draw color box
            draw.rectangle(
                [10 * scale, y_offset, 10 * scale + box_size, y_offset + box_size],
                fill=color,
                outline=self.outline_colors.get(box_type, (255, 255, 255, 255)),
                width=2
            )

            # Draw label (using default font)
            draw.text(
                (10 * scale + text_offset, y_offset + 2 * scale),
                label,
                fill=(255, 255, 255, 255)
            )

            y_offset += box_size + 10 * scale

        return img


def render_collision_debug(
    sprite: 'PIL_Image.Image',
    hitbox: Optional[Dict[str, int]] = None,
    hurtbox: Optional[Dict[str, int]] = None,
    scale: int = 4,
) -> Optional['PIL_Image.Image']:
    """
    Quick function to render collision debug overlay.

    Convenience wrapper around CollisionVisualizer for simple use cases.

    Args:
        sprite: PIL Image of the sprite.
        hitbox: Dict with x, y, width, height for hitbox.
        hurtbox: Dict with x, y, width, height for hurtbox.
        scale: Scale factor (default 4x).

    Returns:
        PIL Image with overlay, or None.

    Example:
        >>> overlay = render_collision_debug(
        ...     sprite_img,
        ...     hitbox={'x': 8, 'y': 4, 'width': 16, 'height': 24},
        ...     hurtbox={'x': 4, 'y': 0, 'width': 24, 'height': 32}
        ... )
        >>> overlay.save("debug.png")
    """
    viz = CollisionVisualizer()

    hit = CollisionBox.from_dict(hitbox, 'hitbox') if hitbox else None
    hurt = CollisionBox.from_dict(hurtbox, 'hurtbox') if hurtbox else None

    return viz.render_overlay(sprite, hit, hurt, scale=scale)


def export_collision_debug_image(
    sprite_path: str,
    output_path: str,
    hitbox: Optional[Dict[str, int]] = None,
    hurtbox: Optional[Dict[str, int]] = None,
    scale: int = 4,
) -> bool:
    """
    Load sprite, render collision overlay, and save to file.

    Complete pipeline for generating debug images from file paths.

    Args:
        sprite_path: Path to sprite image file.
        output_path: Path to save debug image.
        hitbox: Hitbox data as dict.
        hurtbox: Hurtbox data as dict.
        scale: Scale factor.

    Returns:
        True if successful, False otherwise.

    Example:
        >>> export_collision_debug_image(
        ...     "sprites/player.png",
        ...     "debug/player_collision.png",
        ...     hitbox={'x': 8, 'y': 4, 'width': 16, 'height': 24}
        ... )
    """
    if not HAS_PIL:
        print("[ERROR] PIL required for collision debug export")
        return False

    try:
        sprite = Image.open(sprite_path)
        overlay = render_collision_debug(sprite, hitbox, hurtbox, scale)

        if overlay:
            overlay.save(output_path)
            print(f"[EXPORT] Collision debug: {output_path}")
            return True
        return False
    except Exception as e:
        print(f"[ERROR] Failed to export collision debug: {e}")
        return False
