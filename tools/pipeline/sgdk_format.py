"""
SGDK Sprite Formatter

Converts any sprite image to SGDK-compliant format:
- Resize to target dimensions (max 32×32)
- Convert alpha channel to magenta transparency
- Quantize to 16 colors with palette control
- Arrange into sprite sheets (≥128px width)
- Validate before rescomp

Usage:
    from pipeline.sgdk_format import SGDKFormatter, format_for_sgdk

    # Single sprite conversion
    formatter = SGDKFormatter()
    result = formatter.format_sprite(img, (32, 32))

    # Or one-shot convenience function
    validation = format_for_sgdk("input.png", "output.png")
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
from PIL import Image
import os


@dataclass
class ValidationResult:
    """Result of SGDK format validation."""
    is_valid: bool
    errors: List[str]      # Blocking issues
    warnings: List[str]    # Potential problems

    def __str__(self) -> str:
        lines = []
        if self.errors:
            lines.append("ERRORS:")
            for e in self.errors:
                lines.append(f"  ✗ {e}")
        if self.warnings:
            lines.append("WARNINGS:")
            for w in self.warnings:
                lines.append(f"  ⚠ {w}")
        if self.is_valid:
            lines.append("✓ Validation passed")
        return "\n".join(lines)

    def __bool__(self) -> bool:
        return self.is_valid


class SGDKFormatter:
    """Converts sprites to SGDK-compliant format."""

    # SGDK Constants
    TRANSPARENCY_COLOR = (255, 0, 255)  # Magenta
    MAX_COLORS = 16
    MIN_SHEET_WIDTH = 128
    MAX_SPRITE_SIZE = 32
    TILE_SIZE = 8

    # Valid sprite dimensions (must be tile-aligned)
    VALID_SIZES = [8, 16, 24, 32]

    def __init__(self, target_palette: List[Tuple[int, int, int]] = None):
        """
        Initialize formatter.

        Args:
            target_palette: Optional 16-color palette to force.
                           Index 0 should be transparency color.
        """
        self.target_palette = target_palette
        if target_palette and len(target_palette) > 0:
            if target_palette[0] != self.TRANSPARENCY_COLOR:
                # Ensure magenta is first
                filtered = [c for c in target_palette if c != self.TRANSPARENCY_COLOR]
                self.target_palette = [self.TRANSPARENCY_COLOR] + filtered[:15]

    def format_sprite(self, img: Image.Image,
                      target_size: Tuple[int, int] = (32, 32),
                      maintain_aspect: bool = True) -> Image.Image:
        """
        Convert a single sprite to SGDK-ready format.

        Args:
            img: Input image (any format)
            target_size: Target dimensions (width, height)
            maintain_aspect: If True, fit within target maintaining ratio

        Returns:
            SGDK-compliant indexed PNG
        """
        # Step 1: Resize to target dimensions
        img = self._resize_sprite(img, target_size, maintain_aspect)

        # Step 2: Convert alpha to magenta
        img = self._alpha_to_magenta(img)

        # Step 3: Quantize to 16 colors
        img = self._quantize_colors(img)

        # Step 4: Convert to indexed mode
        img = self._to_indexed(img)

        return img

    def create_sprite_sheet(self, sprites: List[Image.Image],
                            frames_per_row: int = 4,
                            frame_size: Tuple[int, int] = None) -> Image.Image:
        """
        Arrange sprites into SGDK-compliant sprite sheet.

        Args:
            sprites: List of sprite images
            frames_per_row: Frames per row in sheet
            frame_size: Force specific frame size (auto-detect if None)

        Returns:
            Sprite sheet image (≥128px width, indexed PNG)
        """
        if not sprites:
            raise ValueError("No sprites provided")

        # Determine frame size
        if frame_size is None:
            max_w = max(s.width for s in sprites)
            max_h = max(s.height for s in sprites)
            # Round up to valid SGDK size
            frame_w = self._round_to_valid_size(max_w)
            frame_h = self._round_to_valid_size(max_h)
        else:
            frame_w, frame_h = frame_size

        # Calculate sheet dimensions
        num_frames = len(sprites)
        cols = min(frames_per_row, num_frames)
        rows = (num_frames + cols - 1) // cols

        sheet_width = cols * frame_w
        sheet_height = rows * frame_h

        # Ensure minimum width for SGDK palette storage
        if sheet_width < self.MIN_SHEET_WIDTH:
            # Pad to minimum width
            sheet_width = self.MIN_SHEET_WIDTH

        # Create sheet with magenta background
        sheet = Image.new('RGB', (sheet_width, sheet_height), self.TRANSPARENCY_COLOR)

        # Place sprites
        for i, sprite in enumerate(sprites):
            col = i % cols
            row = i // cols
            x = col * frame_w
            y = row * frame_h

            # Center sprite in frame if smaller
            offset_x = (frame_w - sprite.width) // 2
            offset_y = (frame_h - sprite.height) // 2

            # Convert sprite to RGB if needed for pasting
            if sprite.mode == 'RGBA':
                # Create temp RGB with magenta bg
                temp = Image.new('RGB', sprite.size, self.TRANSPARENCY_COLOR)
                temp.paste(sprite, (0, 0), sprite)
                sheet.paste(temp, (x + offset_x, y + offset_y))
            elif sprite.mode == 'P':
                # Convert indexed to RGB first
                rgb_sprite = sprite.convert('RGB')
                sheet.paste(rgb_sprite, (x + offset_x, y + offset_y))
            else:
                sheet.paste(sprite, (x + offset_x, y + offset_y))

        # Quantize entire sheet to unified palette
        sheet = self._quantize_colors(sheet)
        sheet = self._to_indexed(sheet)

        return sheet

    def validate_for_rescomp(self, img: Image.Image,
                             sprite_width: int = None,
                             sprite_height: int = None) -> ValidationResult:
        """
        Pre-flight validation before passing to rescomp.

        Args:
            img: Image to validate
            sprite_width: Expected sprite frame width
            sprite_height: Expected sprite frame height

        Returns:
            ValidationResult with errors and warnings
        """
        errors = []
        warnings = []

        # Check minimum width
        if img.width < self.MIN_SHEET_WIDTH:
            errors.append(
                f"Width {img.width}px < minimum {self.MIN_SHEET_WIDTH}px "
                "for palette storage"
            )

        # Check color mode
        if img.mode == 'RGBA':
            errors.append("Image has alpha channel - must use magenta transparency")
        elif img.mode not in ('P', 'RGB'):
            warnings.append(
                f"Unexpected color mode '{img.mode}' - "
                "should be 'P' (indexed) or 'RGB'"
            )

        # Check color count for indexed images
        if img.mode == 'P':
            # Count unique color indices used
            colors = set(img.getdata())
            if len(colors) > self.MAX_COLORS:
                errors.append(f"Too many colors: {len(colors)} > {self.MAX_COLORS}")

        # Check for magenta transparency in RGB mode
        if img.mode == 'RGB':
            pixels = list(img.getdata())
            has_magenta = self.TRANSPARENCY_COLOR in pixels
            if not has_magenta:
                warnings.append(
                    "No magenta pixels found - sprite may have no transparency"
                )

        # Check tile alignment
        if sprite_width:
            if img.width % sprite_width != 0:
                warnings.append(
                    f"Sheet width {img.width} not evenly divisible "
                    f"by sprite width {sprite_width}"
                )
            if sprite_width not in self.VALID_SIZES:
                errors.append(
                    f"Sprite width {sprite_width} not valid - "
                    f"must be one of {self.VALID_SIZES}"
                )

        if sprite_height:
            if img.height % sprite_height != 0:
                warnings.append(
                    f"Sheet height {img.height} not evenly divisible "
                    f"by sprite height {sprite_height}"
                )
            if sprite_height not in self.VALID_SIZES:
                errors.append(
                    f"Sprite height {sprite_height} not valid - "
                    f"must be one of {self.VALID_SIZES}"
                )

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def _resize_sprite(self, img: Image.Image,
                       target_size: Tuple[int, int],
                       maintain_aspect: bool) -> Image.Image:
        """Resize sprite to target dimensions."""
        target_w, target_h = target_size

        # Clamp to max sprite size
        target_w = min(target_w, self.MAX_SPRITE_SIZE)
        target_h = min(target_h, self.MAX_SPRITE_SIZE)

        # Round to valid sizes
        target_w = self._round_to_valid_size(target_w)
        target_h = self._round_to_valid_size(target_h)

        if maintain_aspect:
            # Calculate scale to fit within target
            scale = min(target_w / img.width, target_h / img.height)
            new_w = max(1, int(img.width * scale))
            new_h = max(1, int(img.height * scale))

            # Resize using nearest neighbor (preserves pixel art)
            resized = img.resize((new_w, new_h), Image.Resampling.NEAREST)

            # Create canvas with magenta background
            canvas = Image.new(
                'RGBA',
                (target_w, target_h),
                (*self.TRANSPARENCY_COLOR, 255)
            )

            # Center sprite
            offset_x = (target_w - new_w) // 2
            offset_y = (target_h - new_h) // 2

            if resized.mode == 'RGBA':
                canvas.paste(resized, (offset_x, offset_y), resized)
            else:
                canvas.paste(resized, (offset_x, offset_y))

            return canvas
        else:
            return img.resize((target_w, target_h), Image.Resampling.NEAREST)

    def _alpha_to_magenta(self, img: Image.Image) -> Image.Image:
        """Convert alpha channel to magenta transparency."""
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # Create RGB image with magenta background
        rgb = Image.new('RGB', img.size, self.TRANSPARENCY_COLOR)

        # Composite: where alpha is low, magenta shows through
        pixels = img.load()
        rgb_pixels = rgb.load()

        for y in range(img.height):
            for x in range(img.width):
                r, g, b, a = pixels[x, y]
                if a < 128:  # Threshold for transparency
                    rgb_pixels[x, y] = self.TRANSPARENCY_COLOR
                else:
                    rgb_pixels[x, y] = (r, g, b)

        return rgb

    def _quantize_colors(self, img: Image.Image) -> Image.Image:
        """Reduce image to 16 colors."""
        if img.mode != 'RGB':
            img = img.convert('RGB')

        if self.target_palette:
            # Use provided palette
            return self._quantize_to_palette(img, self.target_palette)
        else:
            # Auto-quantize, preserving magenta
            return self._auto_quantize(img)

    def _quantize_to_palette(self, img: Image.Image,
                             palette: List[Tuple[int, int, int]]) -> Image.Image:
        """Quantize image to specific palette."""
        # Create palette image
        pal_img = Image.new('P', (1, 1))
        flat_palette = []
        for color in palette[:16]:
            flat_palette.extend(color)
        # Pad to 256 colors (PIL requirement)
        flat_palette.extend([0] * (768 - len(flat_palette)))
        pal_img.putpalette(flat_palette)

        # Quantize to palette
        return img.quantize(palette=pal_img, dither=Image.Dither.NONE)

    def _auto_quantize(self, img: Image.Image) -> Image.Image:
        """Auto-quantize preserving magenta as index 0."""
        # First, check if magenta is present
        pixels = list(img.getdata())
        has_magenta = self.TRANSPARENCY_COLOR in pixels

        # Quantize to 15 colors (leaving room for magenta)
        num_colors = 15 if has_magenta else 16

        try:
            quantized = img.quantize(colors=num_colors, dither=Image.Dither.NONE)
        except Exception:
            # Fallback: use median cut
            quantized = img.quantize(colors=num_colors, method=Image.Quantize.MEDIANCUT)

        # If we need to ensure magenta is in palette, rebuild it
        if has_magenta:
            # Get current palette
            old_palette = quantized.getpalette()
            if old_palette:
                # Check if magenta already in palette
                magenta_in_palette = False
                for i in range(num_colors):
                    idx = i * 3
                    if idx + 2 < len(old_palette):
                        color = (old_palette[idx], old_palette[idx+1], old_palette[idx+2])
                        if color == self.TRANSPARENCY_COLOR:
                            magenta_in_palette = True
                            break

                if not magenta_in_palette:
                    # Prepend magenta to palette
                    new_palette = list(self.TRANSPARENCY_COLOR)
                    # Take first 15 colors from old palette
                    new_palette.extend(old_palette[:45])
                    # Pad to 768
                    new_palette.extend([0] * (768 - len(new_palette)))
                    quantized.putpalette(new_palette)

        return quantized

    def _to_indexed(self, img: Image.Image) -> Image.Image:
        """Ensure image is in indexed mode."""
        if img.mode == 'P':
            return img
        return img.quantize(colors=self.MAX_COLORS, dither=Image.Dither.NONE)

    def _round_to_valid_size(self, size: int) -> int:
        """Round up to nearest valid SGDK sprite size."""
        for valid in self.VALID_SIZES:
            if size <= valid:
                return valid
        return self.MAX_SPRITE_SIZE


# =============================================================================
# RESOURCE FILE GENERATION
# =============================================================================

def generate_res_file(sprite_name: str,
                      sheet_path: str,
                      frame_width: int,
                      frame_height: int,
                      output_path: str,
                      compression: str = "FAST",
                      palette_index: int = 0) -> None:
    """
    Generate SGDK resource definition file.

    Args:
        sprite_name: Name for the sprite (e.g., "player")
        sheet_path: Relative path to sprite sheet from res/ folder
        frame_width: Width of each frame in pixels
        frame_height: Height of each frame in pixels
        output_path: Path to write .res file
        compression: SGDK compression (NONE, FAST, BEST)
        palette_index: Which palette slot to use (0-3)
    """
    # Calculate tile dimensions (SGDK uses tiles, not pixels)
    tiles_w = frame_width // 8
    tiles_h = frame_height // 8

    content = f"""// Auto-generated SGDK resource definition
// Generated by unified_pipeline.py
//
// Sprite: {sprite_name}
// Frame size: {frame_width}x{frame_height} pixels ({tiles_w}x{tiles_h} tiles)
// Compression: {compression}

SPRITE spr_{sprite_name} "{sheet_path}" {tiles_w} {tiles_h} {compression} {palette_index}
"""

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, 'w') as f:
        f.write(content)


def generate_tileset_res(tileset_name: str,
                         image_path: str,
                         output_path: str,
                         compression: str = "FAST") -> None:
    """
    Generate SGDK resource definition for a tileset.

    Args:
        tileset_name: Name for the tileset
        image_path: Relative path to tileset image
        output_path: Path to write .res file
        compression: SGDK compression
    """
    content = f"""// Auto-generated SGDK tileset resource
// Generated by unified_pipeline.py

TILESET ts_{tileset_name} "{image_path}" {compression}
"""

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, 'w') as f:
        f.write(content)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def format_for_sgdk(input_path: str,
                    output_path: str,
                    sprite_size: Tuple[int, int] = (32, 32),
                    palette: List[Tuple[int, int, int]] = None) -> ValidationResult:
    """
    One-shot conversion of any image to SGDK format.

    Args:
        input_path: Path to source image
        output_path: Path for output PNG
        sprite_size: Target sprite dimensions
        palette: Optional palette to force

    Returns:
        ValidationResult
    """
    formatter = SGDKFormatter(target_palette=palette)

    img = Image.open(input_path)
    formatted = formatter.format_sprite(img, sprite_size)

    # Validate
    result = formatter.validate_for_rescomp(formatted, sprite_size[0], sprite_size[1])

    if result.is_valid or not result.errors:
        # Save even with warnings
        formatted.save(output_path)
        print(f"  [SGDK] Saved: {output_path}")

    return result


def validate_sgdk_sprite(image_path: str,
                         sprite_width: int = None,
                         sprite_height: int = None) -> ValidationResult:
    """
    Validate an existing image for SGDK compatibility.

    Args:
        image_path: Path to image file
        sprite_width: Expected frame width (optional)
        sprite_height: Expected frame height (optional)

    Returns:
        ValidationResult
    """
    img = Image.open(image_path)
    formatter = SGDKFormatter()
    return formatter.validate_for_rescomp(img, sprite_width, sprite_height)


# =============================================================================
# CLI ENTRY POINT (for standalone testing)
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python sgdk_format.py <input.png> [output.png] [width] [height]")
        print("\nValidates and converts an image to SGDK-compliant format.")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    # Parse optional size
    width = int(sys.argv[3]) if len(sys.argv) > 3 else 32
    height = int(sys.argv[4]) if len(sys.argv) > 4 else 32

    if output_file:
        # Convert
        result = format_for_sgdk(input_file, output_file, (width, height))
        print(result)
    else:
        # Validate only
        result = validate_sgdk_sprite(input_file, width, height)
        print(result)

    sys.exit(0 if result.is_valid else 1)
