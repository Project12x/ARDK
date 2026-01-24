"""
Performance Budget Calculator for Genesis/Mega Drive.

This module analyzes sprite layouts and asset sizes against Genesis hardware
limits, helping developers identify potential performance issues before runtime.

Genesis VDP Hardware Limits:
    - 80 sprites maximum on screen
    - 20 sprites maximum per scanline (horizontal line)
    - 320 pixels maximum sprite coverage per scanline
    - ~168 bytes DMA transfer capacity per scanline during vblank
    - 40 scanlines available during vblank at 60Hz (NTSC)

Key Features:
    - Scanline violation detection (>20 sprites on same Y position)
    - DMA budget estimation for tile/palette uploads
    - Visual heatmap generation showing sprite density
    - Optimization suggestions for fixing violations

Usage:
    from pipeline.performance import PerformanceBudgetCalculator, PerformanceReport

    calculator = PerformanceBudgetCalculator()

    # Analyze sprite positions
    sprites = [
        {'x': 100, 'y': 50, 'width': 32, 'height': 32},
        {'x': 150, 'y': 52, 'width': 16, 'height': 16},
        # ... more sprites
    ]
    report = calculator.analyze_sprite_layout(sprites)

    # Check for violations
    if report.scanline_violations:
        print(f"Violations on scanlines: {report.scanline_violations}")
        for suggestion in calculator.suggest_optimizations(report):
            print(f"  - {suggestion}")

    # Generate visual heatmap
    heatmap = calculator.generate_heatmap(sprites, 320, 224)
    heatmap.save("sprite_density.png")

Integration with Pipeline:
    The calculator works with SpriteInfo objects from the pipeline:

    from pipeline import PerformanceBudgetCalculator
    from pipeline.platforms import SpriteInfo

    # After sprite detection
    sprites_for_analysis = [
        {'x': s.bbox.x, 'y': s.bbox.y,
         'width': s.bbox.width, 'height': s.bbox.height}
        for s in detected_sprites
    ]
    report = calculator.analyze_sprite_layout(sprites_for_analysis)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

# Optional PIL import for heatmap generation
try:
    from PIL import Image, ImageDraw
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class SeverityLevel(Enum):
    """Severity levels for performance warnings.

    Attributes:
        INFO: Informational message, no action needed.
        WARNING: Potential issue, may cause minor problems.
        ERROR: Definite issue, will cause visible glitches.
        CRITICAL: Severe issue, game may crash or become unplayable.
    """
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ScanlineInfo:
    """Information about sprite usage on a single scanline.

    Attributes:
        scanline: The Y coordinate (scanline number, 0-223 for Genesis).
        sprite_count: Number of sprites overlapping this scanline.
        pixel_count: Total horizontal pixels covered by sprites.
        sprites: List of sprite indices that overlap this scanline.
    """
    scanline: int
    sprite_count: int
    pixel_count: int
    sprites: List[int] = field(default_factory=list)


@dataclass
class PerformanceWarning:
    """A specific performance warning with context.

    Attributes:
        severity: How serious the issue is (INFO to CRITICAL).
        category: Type of issue (scanline, dma, memory, etc.).
        message: Human-readable description of the issue.
        scanline: Affected scanline (if applicable).
        value: The problematic value (e.g., sprite count).
        limit: The hardware limit being exceeded.
    """
    severity: SeverityLevel
    category: str
    message: str
    scanline: Optional[int] = None
    value: Optional[int] = None
    limit: Optional[int] = None


@dataclass
class PerformanceReport:
    """Complete performance analysis report.

    This dataclass contains all the information from analyzing a sprite
    layout against Genesis hardware limits.

    Attributes:
        sprites_total: Total number of sprites analyzed.
        sprites_per_scanline: Mapping of scanline → sprite count.
        scanline_violations: List of scanlines exceeding 20 sprites.
        scanline_details: Detailed info for each problematic scanline.
        pixel_violations: Scanlines exceeding 320 sprite pixels.
        dma_bytes: Total bytes that would need DMA transfer.
        dma_time_lines: Estimated scanlines needed for DMA.
        vblank_budget_used: Percentage of vblank DMA budget used.
        warnings: List of all performance warnings.
        passed: True if no ERROR or CRITICAL issues found.
    """
    sprites_total: int
    sprites_per_scanline: Dict[int, int]
    scanline_violations: List[int]
    scanline_details: List[ScanlineInfo] = field(default_factory=list)
    pixel_violations: List[int] = field(default_factory=list)
    dma_bytes: int = 0
    dma_time_lines: float = 0.0
    vblank_budget_used: float = 0.0
    warnings: List[PerformanceWarning] = field(default_factory=list)
    passed: bool = True

    def summary(self) -> str:
        """Generate a human-readable summary of the report."""
        lines = [
            "=" * 50,
            "GENESIS PERFORMANCE REPORT",
            "=" * 50,
            f"Total Sprites: {self.sprites_total} / 80 ({self.sprites_total * 100 // 80}%)",
            f"Scanline Violations: {len(self.scanline_violations)}",
            f"Pixel Violations: {len(self.pixel_violations)}",
            f"DMA Budget: {self.dma_bytes} bytes ({self.vblank_budget_used:.1f}% of vblank)",
            "-" * 50,
        ]

        if self.scanline_violations:
            lines.append("SCANLINE VIOLATIONS (>20 sprites):")
            for scanline in self.scanline_violations[:10]:  # Show first 10
                count = self.sprites_per_scanline.get(scanline, 0)
                overflow = count - 20
                lines.append(f"  Line {scanline}: {count} sprites (+{overflow} overflow)")
            if len(self.scanline_violations) > 10:
                lines.append(f"  ... and {len(self.scanline_violations) - 10} more")

        if self.warnings:
            lines.append("")
            lines.append("WARNINGS:")
            for warning in self.warnings:
                icon = {"info": "ℹ", "warning": "⚠", "error": "✗", "critical": "☠"}
                lines.append(f"  {icon.get(warning.severity.value, '•')} [{warning.category}] {warning.message}")

        lines.append("=" * 50)
        lines.append(f"STATUS: {'PASS' if self.passed else 'FAIL'}")
        lines.append("=" * 50)

        return "\n".join(lines)


class PerformanceBudgetCalculator:
    """Analyze sprite layouts against Genesis VDP hardware limits.

    The Genesis VDP has strict limits on how many sprites can appear
    on screen and especially on a single scanline. Exceeding these
    limits causes sprites to flicker or disappear entirely.

    Hardware Limits:
        - MAX_SPRITES (80): Maximum sprites in Sprite Attribute Table
        - MAX_SPRITES_PER_LINE (20): Maximum sprites on one scanline
        - MAX_PIXELS_PER_LINE (320): Maximum sprite pixel width per line
        - DMA_BYTES_PER_LINE (168): DMA transfer rate per scanline
        - VBLANK_LINES (40): Available scanlines during vblank

    Example:
        calculator = PerformanceBudgetCalculator()

        sprites = [
            {'x': 10, 'y': 100, 'width': 32, 'height': 32},
            {'x': 50, 'y': 102, 'width': 16, 'height': 16},
        ]

        report = calculator.analyze_sprite_layout(sprites)
        print(report.summary())

        if report.scanline_violations:
            heatmap = calculator.generate_heatmap(sprites, 320, 224)
            heatmap.save("density.png")
    """

    # Genesis hardware limits
    MAX_SPRITES = 80
    MAX_SPRITES_PER_LINE = 20
    MAX_PIXELS_PER_LINE = 320
    DMA_BYTES_PER_LINE = 168  # ~168 bytes per scanline during active display
    VBLANK_LINES = 40  # ~40 scanlines available during vblank (NTSC)

    # Screen dimensions
    SCREEN_WIDTH = 320
    SCREEN_HEIGHT = 224

    def __init__(self,
                 max_sprites: int = None,
                 max_per_line: int = None,
                 screen_height: int = None):
        """Initialize the calculator with optional custom limits.

        Args:
            max_sprites: Override MAX_SPRITES (default 80).
            max_per_line: Override MAX_SPRITES_PER_LINE (default 20).
            screen_height: Override screen height for analysis (default 224).
        """
        self.max_sprites = max_sprites or self.MAX_SPRITES
        self.max_per_line = max_per_line or self.MAX_SPRITES_PER_LINE
        self.screen_height = screen_height or self.SCREEN_HEIGHT

    def analyze_sprite_layout(self,
                              sprites: List[Dict[str, Any]],
                              screen_height: int = None) -> PerformanceReport:
        """Analyze sprite positions for hardware limit violations.

        Examines each scanline to count how many sprites overlap it,
        detecting violations of the 20-sprite-per-scanline limit.

        Args:
            sprites: List of sprite dicts with 'x', 'y', 'width', 'height' keys.
                     Can also include 'name' for better error messages.
            screen_height: Screen height for analysis (default 224).

        Returns:
            PerformanceReport with all analysis results.

        Example:
            sprites = [
                {'x': 0, 'y': 100, 'width': 16, 'height': 16, 'name': 'bullet_0'},
                {'x': 20, 'y': 100, 'width': 16, 'height': 16, 'name': 'bullet_1'},
            ]
            report = calculator.analyze_sprite_layout(sprites)
        """
        height = screen_height or self.screen_height

        # Track sprites per scanline
        sprites_per_scanline: Dict[int, int] = {}
        pixels_per_scanline: Dict[int, int] = {}
        sprites_on_scanline: Dict[int, List[int]] = {}

        # Analyze each sprite's scanline coverage
        for idx, sprite in enumerate(sprites):
            y = sprite.get('y', 0)
            h = sprite.get('height', 8)
            w = sprite.get('width', 8)

            # For each scanline this sprite covers
            for scanline in range(max(0, y), min(height, y + h)):
                sprites_per_scanline[scanline] = sprites_per_scanline.get(scanline, 0) + 1
                pixels_per_scanline[scanline] = pixels_per_scanline.get(scanline, 0) + w

                if scanline not in sprites_on_scanline:
                    sprites_on_scanline[scanline] = []
                sprites_on_scanline[scanline].append(idx)

        # Find violations
        scanline_violations = []
        pixel_violations = []
        scanline_details = []
        warnings = []

        for scanline in sorted(sprites_per_scanline.keys()):
            count = sprites_per_scanline[scanline]
            pixels = pixels_per_scanline.get(scanline, 0)

            if count > self.max_per_line:
                scanline_violations.append(scanline)
                overflow = count - self.max_per_line

                scanline_details.append(ScanlineInfo(
                    scanline=scanline,
                    sprite_count=count,
                    pixel_count=pixels,
                    sprites=sprites_on_scanline.get(scanline, [])
                ))

                warnings.append(PerformanceWarning(
                    severity=SeverityLevel.ERROR,
                    category="scanline",
                    message=f"Scanline {scanline}: {count} sprites ({overflow} will flicker/disappear)",
                    scanline=scanline,
                    value=count,
                    limit=self.max_per_line
                ))

            if pixels > self.MAX_PIXELS_PER_LINE:
                pixel_violations.append(scanline)

                warnings.append(PerformanceWarning(
                    severity=SeverityLevel.WARNING,
                    category="pixels",
                    message=f"Scanline {scanline}: {pixels}px sprite width (may cause issues)",
                    scanline=scanline,
                    value=pixels,
                    limit=self.MAX_PIXELS_PER_LINE
                ))

        # Check total sprite count
        total_sprites = len(sprites)
        if total_sprites > self.max_sprites:
            warnings.append(PerformanceWarning(
                severity=SeverityLevel.CRITICAL,
                category="total",
                message=f"Total sprites ({total_sprites}) exceeds maximum ({self.max_sprites})",
                value=total_sprites,
                limit=self.max_sprites
            ))
        elif total_sprites > self.max_sprites * 0.8:
            warnings.append(PerformanceWarning(
                severity=SeverityLevel.WARNING,
                category="total",
                message=f"Sprite count ({total_sprites}) approaching limit ({self.max_sprites})",
                value=total_sprites,
                limit=self.max_sprites
            ))

        # Determine pass/fail
        passed = not any(
            w.severity in (SeverityLevel.ERROR, SeverityLevel.CRITICAL)
            for w in warnings
        )

        return PerformanceReport(
            sprites_total=total_sprites,
            sprites_per_scanline=sprites_per_scanline,
            scanline_violations=scanline_violations,
            scanline_details=scanline_details,
            pixel_violations=pixel_violations,
            warnings=warnings,
            passed=passed
        )

    def estimate_dma_time(self,
                          tile_bytes: int,
                          palette_bytes: int = 0) -> Tuple[float, PerformanceReport]:
        """Estimate DMA transfer time in scanlines.

        The Genesis can transfer approximately 168 bytes per scanline
        during vblank. This method calculates how many scanlines a
        DMA transfer would consume.

        Args:
            tile_bytes: Total bytes of tile data to transfer.
            palette_bytes: Total bytes of palette data (optional).

        Returns:
            Tuple of (scanlines_needed, PerformanceReport).

        Example:
            # 64 tiles × 32 bytes each = 2048 bytes
            lines, report = calculator.estimate_dma_time(2048)
            print(f"DMA will take {lines:.1f} scanlines")
        """
        total_bytes = tile_bytes + palette_bytes
        scanlines_needed = total_bytes / self.DMA_BYTES_PER_LINE
        vblank_percentage = (scanlines_needed / self.VBLANK_LINES) * 100

        warnings = []
        passed = True

        if scanlines_needed > self.VBLANK_LINES:
            warnings.append(PerformanceWarning(
                severity=SeverityLevel.CRITICAL,
                category="dma",
                message=f"DMA exceeds vblank: {scanlines_needed:.1f} lines needed, {self.VBLANK_LINES} available",
                value=int(scanlines_needed),
                limit=self.VBLANK_LINES
            ))
            passed = False
        elif scanlines_needed > self.VBLANK_LINES * 0.75:
            warnings.append(PerformanceWarning(
                severity=SeverityLevel.WARNING,
                category="dma",
                message=f"DMA uses {vblank_percentage:.0f}% of vblank ({scanlines_needed:.1f}/{self.VBLANK_LINES} lines)",
                value=int(scanlines_needed),
                limit=self.VBLANK_LINES
            ))

        report = PerformanceReport(
            sprites_total=0,
            sprites_per_scanline={},
            scanline_violations=[],
            dma_bytes=total_bytes,
            dma_time_lines=scanlines_needed,
            vblank_budget_used=vblank_percentage,
            warnings=warnings,
            passed=passed
        )

        return scanlines_needed, report

    def generate_heatmap(self,
                         sprites: List[Dict[str, Any]],
                         width: int = None,
                         height: int = None,
                         scale: int = 2) -> Optional['Image.Image']:
        """Generate visual heatmap showing sprite density per scanline.

        Creates an image where each row is colored based on sprite count:
        - Green (0-10): Safe, plenty of headroom
        - Yellow (11-15): Caution, getting busy
        - Orange (16-19): Near limit, consider optimizing
        - Red (20+): OVERFLOW - sprites will flicker/disappear

        Args:
            sprites: List of sprite dicts with position/size info.
            width: Output image width (default 320).
            height: Output image height (default 224).
            scale: Scale factor for output image (default 2x).

        Returns:
            PIL Image with heatmap visualization, or None if PIL unavailable.

        Example:
            heatmap = calculator.generate_heatmap(sprites)
            if heatmap:
                heatmap.save("sprite_density.png")
        """
        if not HAS_PIL:
            return None

        width = width or self.SCREEN_WIDTH
        height = height or self.screen_height

        # First, analyze the layout
        report = self.analyze_sprite_layout(sprites, height)

        # Create base image (dark gray background)
        img = Image.new('RGB', (width * scale, height * scale), (32, 32, 32))
        draw = ImageDraw.Draw(img)

        # Color gradient function: maps sprite count to color
        # Uses a traffic-light scheme: green=safe, yellow=caution, orange=warning, red=overflow
        def get_color(count: int) -> Tuple[int, int, int]:
            if count == 0:
                return (32, 32, 32)  # Dark gray - no sprites
            elif count <= 10:
                # Green gradient (safe)
                intensity = int(100 + (count / 10) * 155)
                return (0, intensity, 0)
            elif count <= 15:
                # Yellow gradient (caution)
                progress = (count - 10) / 5
                return (int(200 + progress * 55), int(200 - progress * 50), 0)
            elif count <= 19:
                # Orange gradient (near limit)
                progress = (count - 15) / 4
                return (255, int(150 - progress * 100), 0)
            else:
                # Red (overflow!)
                overflow = min(count - 20, 10)
                intensity = 255 - (overflow * 10)
                return (255, 0, 0)

        # Draw scanline colors
        for scanline in range(height):
            count = report.sprites_per_scanline.get(scanline, 0)
            color = get_color(count)

            y_start = scanline * scale
            y_end = y_start + scale
            draw.rectangle([0, y_start, width * scale - 1, y_end - 1], fill=color)

        # Optionally draw sprite outlines
        for sprite in sprites:
            x = sprite.get('x', 0) * scale
            y = sprite.get('y', 0) * scale
            w = sprite.get('width', 8) * scale
            h = sprite.get('height', 8) * scale

            # Draw outline in white with transparency effect
            outline_color = (200, 200, 200)
            draw.rectangle([x, y, x + w - 1, y + h - 1], outline=outline_color)

        # Draw legend
        legend_x = 10
        legend_y = 10
        legend_items = [
            ((0, 150, 0), "0-10: Safe"),
            ((220, 180, 0), "11-15: Caution"),
            ((255, 100, 0), "16-19: Near Limit"),
            ((255, 0, 0), "20+: OVERFLOW"),
        ]

        for i, (color, label) in enumerate(legend_items):
            y_pos = legend_y + i * 14
            draw.rectangle([legend_x, y_pos, legend_x + 10, y_pos + 10], fill=color)
            # Note: Text requires a font; for simplicity we skip text labels
            # In a full implementation, we'd use ImageFont

        return img

    def suggest_optimizations(self, report: PerformanceReport) -> List[str]:
        """Generate optimization suggestions based on analysis results.

        Provides actionable advice for fixing performance violations.

        Args:
            report: PerformanceReport from analyze_sprite_layout().

        Returns:
            List of human-readable optimization suggestions.

        Example:
            report = calculator.analyze_sprite_layout(sprites)
            for suggestion in calculator.suggest_optimizations(report):
                print(f"• {suggestion}")
        """
        suggestions = []

        # Scanline violations
        if report.scanline_violations:
            # Find the worst offender
            worst_scanline = max(
                report.scanline_violations,
                key=lambda s: report.sprites_per_scanline.get(s, 0)
            )
            worst_count = report.sprites_per_scanline.get(worst_scanline, 0)
            overflow = worst_count - self.max_per_line

            suggestions.append(
                f"Scanline {worst_scanline} has {worst_count} sprites. "
                f"Stagger Y positions by 1-2 pixels to spread across multiple lines."
            )

            if overflow > 5:
                suggestions.append(
                    f"Consider combining small sprites into larger composite sprites "
                    f"to reduce sprite count."
                )

            # Check if violations are clustered
            if len(report.scanline_violations) > 10:
                min_line = min(report.scanline_violations)
                max_line = max(report.scanline_violations)
                suggestions.append(
                    f"Violations cluster between lines {min_line}-{max_line}. "
                    f"Consider redesigning this scene section."
                )

        # Total sprite count issues
        if report.sprites_total > self.max_sprites * 0.8:
            suggestions.append(
                f"Sprite count ({report.sprites_total}) is {report.sprites_total * 100 // self.max_sprites}% of limit. "
                f"Consider using tile-based backgrounds instead of sprites for static elements."
            )

        # DMA issues
        if report.dma_time_lines > self.VBLANK_LINES * 0.5:
            suggestions.append(
                f"DMA uses {report.vblank_budget_used:.0f}% of vblank. "
                f"Consider using compressed tile data or streaming tiles over multiple frames."
            )

        if report.dma_time_lines > self.VBLANK_LINES:
            suggestions.append(
                f"DMA EXCEEDS vblank budget! Split uploads across multiple frames "
                f"or use double-buffering for tile data."
            )

        # Pixel coverage issues
        if report.pixel_violations:
            suggestions.append(
                f"Some scanlines have >320px of sprite width. "
                f"This may cause visual glitches on certain emulators/hardware."
            )

        # General suggestions if issues found
        if not report.passed:
            suggestions.append(
                "Consider using sprite multiplexing (cycling which sprites are visible each frame) "
                "if you need more sprites than hardware allows."
            )

        if not suggestions:
            suggestions.append("No performance issues detected. Layout is within hardware limits.")

        return suggestions

    def analyze_from_sprite_infos(self,
                                   sprite_infos: List[Any],
                                   screen_height: int = None) -> PerformanceReport:
        """Convenience method to analyze SpriteInfo objects from the pipeline.

        Converts pipeline SpriteInfo objects to the dict format expected
        by analyze_sprite_layout().

        Args:
            sprite_infos: List of SpriteInfo objects (from platforms.py).
            screen_height: Screen height for analysis (default 224).

        Returns:
            PerformanceReport with analysis results.
        """
        sprites = []
        for info in sprite_infos:
            sprite_dict = {
                'x': getattr(info, 'x', 0) if hasattr(info, 'x') else 0,
                'y': getattr(info, 'y', 0) if hasattr(info, 'y') else 0,
                'width': getattr(info, 'width', 8) if hasattr(info, 'width') else 8,
                'height': getattr(info, 'height', 8) if hasattr(info, 'height') else 8,
            }

            # Try to get position from bbox if available
            if hasattr(info, 'bbox'):
                bbox = info.bbox
                if hasattr(bbox, 'x'):
                    sprite_dict['x'] = bbox.x
                if hasattr(bbox, 'y'):
                    sprite_dict['y'] = bbox.y
                if hasattr(bbox, 'width'):
                    sprite_dict['width'] = bbox.width
                if hasattr(bbox, 'height'):
                    sprite_dict['height'] = bbox.height

            # Include name if available
            if hasattr(info, 'name'):
                sprite_dict['name'] = info.name

            sprites.append(sprite_dict)

        return self.analyze_sprite_layout(sprites, screen_height)


# Convenience function for quick analysis
def analyze_sprite_performance(sprites: List[Dict[str, Any]],
                               screen_height: int = 224) -> PerformanceReport:
    """Quick analysis of sprite layout for Genesis hardware limits.

    This is a convenience function that creates a calculator and runs analysis.

    Args:
        sprites: List of sprite dicts with 'x', 'y', 'width', 'height'.
        screen_height: Screen height (default 224 for Genesis).

    Returns:
        PerformanceReport with analysis results.

    Example:
        sprites = [{'x': 0, 'y': 100, 'width': 16, 'height': 16}]
        report = analyze_sprite_performance(sprites)
        print(report.summary())
    """
    calculator = PerformanceBudgetCalculator()
    return calculator.analyze_sprite_layout(sprites, screen_height)
