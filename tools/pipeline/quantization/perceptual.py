"""
Perceptual Color Science for Retro Palette Quantization.

This module provides perceptually-accurate color matching and palette extraction,
upgrading from simple RGB Euclidean distance to industry-standard color difference
algorithms (CIEDE2000, CAM02-UCS).

Phase: 0.7 (Foundation)

Key Features:
- CIEDE2000 color difference (most perceptually accurate)
- CAM02-UCS uniform color space
- K-means clustering for optimal palette extraction
- Fallback to RGB when optional dependencies unavailable

Dependencies:
    Required: numpy, pillow
    Optional: colour-science (pip install colour-science)
              colorspacious (pip install colorspacious)

Usage:
    from tools.pipeline.quantization import (
        find_nearest_perceptual,
        extract_optimal_palette,
        PerceptualQuantizer,
    )

    # Find nearest palette color
    palette = [(0, 0, 0), (255, 0, 0), (0, 255, 0), (0, 0, 255)]
    idx = find_nearest_perceptual((128, 64, 32), palette, method='CIEDE2000')

    # Extract optimal palette from image
    palette = extract_optimal_palette(image, num_colors=16)

    # Full quantizer for batch processing
    quantizer = PerceptualQuantizer(method='CIEDE2000')
    indexed_image = quantizer.quantize(image, palette)
"""

import math
from typing import List, Tuple, Optional, Literal
from dataclasses import dataclass

import numpy as np
from PIL import Image

# Optional imports for advanced color science
try:
    import colour
    COLOUR_AVAILABLE = True
except ImportError:
    COLOUR_AVAILABLE = False

try:
    import colorspacious
    COLORSPACIOUS_AVAILABLE = True
except ImportError:
    COLORSPACIOUS_AVAILABLE = False


# Type aliases
RGB = Tuple[int, int, int]
LAB = Tuple[float, float, float]
ColorMethod = Literal['CIEDE2000', 'CAM02-UCS', 'CIELab', 'RGB']


# =============================================================================
# COLOR SPACE CONVERSION
# =============================================================================

def rgb_to_lab(rgb: RGB) -> LAB:
    """
    Convert RGB (0-255) to CIELab color space.

    Uses colour-science if available, otherwise falls back to approximate
    sRGB->XYZ->Lab conversion.

    Args:
        rgb: RGB tuple with values 0-255

    Returns:
        LAB tuple (L: 0-100, a: -128 to 128, b: -128 to 128)
    """
    # Normalize to 0-1
    r, g, b = rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0

    if COLOUR_AVAILABLE:
        # Use colour-science for accurate conversion
        rgb_array = np.array([r, g, b])
        xyz = colour.sRGB_to_XYZ(rgb_array)
        lab = colour.XYZ_to_Lab(xyz)
        return (float(lab[0]), float(lab[1]), float(lab[2]))

    # Fallback: approximate sRGB -> XYZ -> Lab
    # Apply gamma correction
    def linearize(c):
        if c > 0.04045:
            return ((c + 0.055) / 1.055) ** 2.4
        return c / 12.92

    r_lin = linearize(r)
    g_lin = linearize(g)
    b_lin = linearize(b)

    # sRGB to XYZ (D65 illuminant)
    x = r_lin * 0.4124564 + g_lin * 0.3575761 + b_lin * 0.1804375
    y = r_lin * 0.2126729 + g_lin * 0.7151522 + b_lin * 0.0721750
    z = r_lin * 0.0193339 + g_lin * 0.1191920 + b_lin * 0.9503041

    # Reference white D65
    xn, yn, zn = 0.95047, 1.0, 1.08883

    # XYZ to Lab
    def f(t):
        if t > 0.008856:
            return t ** (1/3)
        return (903.3 * t + 16) / 116

    fx = f(x / xn)
    fy = f(y / yn)
    fz = f(z / zn)

    L = 116 * fy - 16
    a = 500 * (fx - fy)
    b_val = 200 * (fy - fz)

    return (L, a, b_val)


def lab_to_rgb(lab: LAB) -> RGB:
    """
    Convert CIELab to RGB (0-255).

    Args:
        lab: LAB tuple (L: 0-100, a/b: approximately -128 to 128)

    Returns:
        RGB tuple with values 0-255, clamped to valid range
    """
    L, a, b_val = lab

    if COLOUR_AVAILABLE:
        lab_array = np.array([L, a, b_val])
        xyz = colour.Lab_to_XYZ(lab_array)
        rgb = colour.XYZ_to_sRGB(xyz)
        # Clamp and convert to 0-255
        rgb = np.clip(rgb, 0, 1) * 255
        return (int(rgb[0]), int(rgb[1]), int(rgb[2]))

    # Fallback: Lab -> XYZ -> sRGB
    # Reference white D65
    xn, yn, zn = 0.95047, 1.0, 1.08883

    fy = (L + 16) / 116
    fx = a / 500 + fy
    fz = fy - b_val / 200

    def f_inv(t):
        if t > 0.206893:
            return t ** 3
        return (116 * t - 16) / 903.3

    x = xn * f_inv(fx)
    y = yn * f_inv(fy)
    z = zn * f_inv(fz)

    # XYZ to sRGB
    r_lin = x * 3.2404542 + y * -1.5371385 + z * -0.4985314
    g_lin = x * -0.9692660 + y * 1.8760108 + z * 0.0415560
    b_lin = x * 0.0556434 + y * -0.2040259 + z * 1.0572252

    # Apply gamma
    def gamma(c):
        if c > 0.0031308:
            return 1.055 * (c ** (1/2.4)) - 0.055
        return 12.92 * c

    r = gamma(r_lin)
    g = gamma(g_lin)
    b = gamma(b_lin)

    # Clamp and convert to 0-255
    r = int(max(0, min(255, r * 255)))
    g = int(max(0, min(255, g * 255)))
    b = int(max(0, min(255, b * 255)))

    return (r, g, b)


# =============================================================================
# COLOR DISTANCE CALCULATIONS
# =============================================================================

def calculate_color_distance(
    c1: RGB,
    c2: RGB,
    method: ColorMethod = 'CIEDE2000'
) -> float:
    """
    Calculate perceptual color distance between two RGB colors.

    Args:
        c1: First RGB color (0-255)
        c2: Second RGB color (0-255)
        method: Distance calculation method:
            - 'CIEDE2000': Most perceptually accurate (requires colour-science)
            - 'CAM02-UCS': Uniform color space (requires colorspacious)
            - 'CIELab': Simple Euclidean in Lab space
            - 'RGB': Fast Euclidean in RGB space (least accurate)

    Returns:
        Distance value (lower = more similar)
    """
    if method == 'RGB':
        # Simple RGB Euclidean (fastest, least accurate)
        dr = c1[0] - c2[0]
        dg = c1[1] - c2[1]
        db = c1[2] - c2[2]
        return math.sqrt(dr*dr + dg*dg + db*db)

    if method == 'CIEDE2000' and COLOUR_AVAILABLE:
        # Industry standard for perceptual color difference
        lab1 = rgb_to_lab(c1)
        lab2 = rgb_to_lab(c2)
        return float(colour.delta_E(
            np.array(lab1),
            np.array(lab2),
            method='CIE 2000'
        ))

    if method == 'CAM02-UCS' and COLORSPACIOUS_AVAILABLE:
        # Uniform color space - good for palette design
        rgb1_norm = [c / 255.0 for c in c1]
        rgb2_norm = [c / 255.0 for c in c2]
        return float(colorspacious.deltaE(
            rgb1_norm, rgb2_norm,
            input_space="sRGB1"
        ))

    # Fallback to CIELab Euclidean
    lab1 = rgb_to_lab(c1)
    lab2 = rgb_to_lab(c2)
    dL = lab1[0] - lab2[0]
    da = lab1[1] - lab2[1]
    db = lab1[2] - lab2[2]
    return math.sqrt(dL*dL + da*da + db*db)


def find_nearest_perceptual(
    rgb: RGB,
    palette: List[RGB],
    method: ColorMethod = 'CIEDE2000'
) -> int:
    """
    Find nearest palette color using perceptual color difference.

    Args:
        rgb: Source color (0-255 per channel)
        palette: List of target palette colors
        method: Color distance method (CIEDE2000, CAM02-UCS, CIELab, RGB)

    Returns:
        Index of perceptually nearest color in palette

    Example:
        >>> palette = [(0, 0, 0), (255, 0, 0), (0, 255, 0)]
        >>> find_nearest_perceptual((200, 50, 50), palette)
        1  # Red is closest
    """
    if not palette:
        raise ValueError("Palette cannot be empty")

    min_dist = float('inf')
    best_idx = 0

    for idx, pal_color in enumerate(palette):
        dist = calculate_color_distance(rgb, pal_color, method)
        if dist < min_dist:
            min_dist = dist
            best_idx = idx

    return best_idx


def find_nearest_rgb(rgb: RGB, palette: List[RGB]) -> int:
    """
    Find nearest palette color using simple RGB Euclidean distance.

    Fast fallback when perceptual accuracy isn't critical.

    Args:
        rgb: Source color (0-255)
        palette: List of palette colors

    Returns:
        Index of nearest color
    """
    return find_nearest_perceptual(rgb, palette, method='RGB')


# =============================================================================
# PALETTE EXTRACTION
# =============================================================================

def extract_optimal_palette(
    image: Image.Image,
    num_colors: int = 16,
    method: Literal['kmeans', 'median_cut', 'octree'] = 'kmeans',
    sample_size: int = 10000
) -> List[RGB]:
    """
    Extract optimal palette from image using clustering.

    Uses k-means clustering in Lab color space for perceptually balanced
    palette selection.

    Args:
        image: Source PIL Image
        num_colors: Target palette size (default 16 for Genesis)
        method: Clustering algorithm:
            - 'kmeans': K-means in Lab space (best quality)
            - 'median_cut': Median cut quantization (faster)
            - 'octree': Octree quantization (fastest)
        sample_size: Max pixels to sample (for large images)

    Returns:
        List of RGB tuples representing optimal palette

    Example:
        >>> img = Image.open("sprite.png")
        >>> palette = extract_optimal_palette(img, num_colors=16)
        >>> len(palette)
        16
    """
    # Convert to RGB if needed
    if image.mode != 'RGB':
        image = image.convert('RGB')

    # Get pixel data
    pixels = list(image.getdata())

    # Sample if image is large
    if len(pixels) > sample_size:
        import random
        pixels = random.sample(pixels, sample_size)

    # Remove fully transparent pixels if RGBA
    pixels = [p for p in pixels if len(p) < 4 or p[3] > 128]

    if not pixels:
        # Fallback: return grayscale ramp
        step = 255 // (num_colors - 1) if num_colors > 1 else 255
        return [(i * step, i * step, i * step) for i in range(num_colors)]

    if method == 'kmeans':
        return _extract_kmeans(pixels, num_colors)
    elif method == 'median_cut':
        return _extract_median_cut(pixels, num_colors)
    else:  # octree
        return _extract_octree(image, num_colors)


def _extract_kmeans(pixels: List[RGB], num_colors: int) -> List[RGB]:
    """K-means clustering in Lab space for optimal palette."""
    try:
        from sklearn.cluster import KMeans
        SKLEARN_AVAILABLE = True
    except ImportError:
        SKLEARN_AVAILABLE = False

    if SKLEARN_AVAILABLE:
        # Convert to Lab for perceptually uniform clustering
        lab_pixels = np.array([rgb_to_lab(p[:3]) for p in pixels])

        kmeans = KMeans(n_clusters=num_colors, random_state=42, n_init=10)
        kmeans.fit(lab_pixels)

        # Convert cluster centers back to RGB
        palette = []
        for center in kmeans.cluster_centers_:
            rgb = lab_to_rgb((center[0], center[1], center[2]))
            palette.append(rgb)

        return palette

    # Fallback: simple uniform sampling
    pixels_array = np.array([p[:3] for p in pixels])
    # Take evenly spaced samples
    indices = np.linspace(0, len(pixels_array) - 1, num_colors, dtype=int)
    return [tuple(pixels_array[i]) for i in indices]


def _extract_median_cut(pixels: List[RGB], num_colors: int) -> List[RGB]:
    """Median cut quantization - faster than k-means."""
    # Use PIL's built-in quantization
    from collections import Counter

    # Count unique colors
    color_counts = Counter(p[:3] for p in pixels)

    # If fewer colors than requested, return all
    if len(color_counts) <= num_colors:
        return list(color_counts.keys())

    # Simple median cut implementation
    def median_cut(colors: List[RGB], depth: int) -> List[RGB]:
        if depth == 0 or len(colors) <= 1:
            if colors:
                # Return average color
                avg = [sum(c[i] for c in colors) // len(colors) for i in range(3)]
                return [(avg[0], avg[1], avg[2])]
            return []

        # Find channel with greatest range
        ranges = []
        for i in range(3):
            channel_vals = [c[i] for c in colors]
            ranges.append(max(channel_vals) - min(channel_vals))

        split_channel = ranges.index(max(ranges))

        # Sort by that channel and split
        colors.sort(key=lambda c: c[split_channel])
        mid = len(colors) // 2

        return (
            median_cut(colors[:mid], depth - 1) +
            median_cut(colors[mid:], depth - 1)
        )

    # Calculate depth needed
    depth = int(math.ceil(math.log2(num_colors)))
    unique_colors = list(set(p[:3] for p in pixels))

    palette = median_cut(unique_colors, depth)
    return palette[:num_colors]


def _extract_octree(image: Image.Image, num_colors: int) -> List[RGB]:
    """Octree quantization using PIL's built-in."""
    quantized = image.quantize(colors=num_colors, method=Image.Quantize.MEDIANCUT)
    palette_data = quantized.getpalette()

    if palette_data:
        palette = []
        for i in range(num_colors):
            idx = i * 3
            if idx + 2 < len(palette_data):
                palette.append((palette_data[idx], palette_data[idx+1], palette_data[idx+2]))
        return palette

    return [(0, 0, 0)] * num_colors


# =============================================================================
# QUANTIZER CLASS
# =============================================================================

@dataclass
class QuantizationResult:
    """Result of image quantization."""
    image: Image.Image  # Indexed/quantized image
    palette: List[RGB]  # Colors used
    color_map: np.ndarray  # Index for each pixel
    error_sum: float  # Total quantization error


class PerceptualQuantizer:
    """
    Full perceptual quantization pipeline for retro game sprites.

    Provides:
    - Perceptually-optimal palette extraction
    - Perceptual color matching for quantization
    - Optional dithering support
    - Platform-specific palette constraints

    Example:
        quantizer = PerceptualQuantizer(method='CIEDE2000')

        # Extract palette and quantize
        result = quantizer.quantize_with_extraction(
            image,
            num_colors=16,
            dither=True
        )

        # Or use existing palette
        result = quantizer.quantize(image, genesis_palette)
    """

    def __init__(
        self,
        method: ColorMethod = 'CIEDE2000',
        dither_strength: float = 1.0
    ):
        """
        Initialize quantizer.

        Args:
            method: Color distance method for matching
            dither_strength: Dithering intensity (0.0 to 2.0)
        """
        self.method = method
        self.dither_strength = dither_strength

        # Cache for Lab conversions (expensive)
        self._lab_cache: dict = {}

    def quantize(
        self,
        image: Image.Image,
        palette: List[RGB],
        dither: bool = False
    ) -> QuantizationResult:
        """
        Quantize image to given palette.

        Args:
            image: Source image
            palette: Target palette colors
            dither: Apply Floyd-Steinberg dithering

        Returns:
            QuantizationResult with indexed image and stats
        """
        if image.mode != 'RGB':
            image = image.convert('RGB')

        width, height = image.size
        pixels = np.array(image)
        output = np.zeros((height, width), dtype=np.uint8)
        total_error = 0.0

        if dither:
            output, total_error = self._quantize_dithered(pixels, palette)
        else:
            output, total_error = self._quantize_direct(pixels, palette)

        # Create indexed image
        result_img = Image.new('P', (width, height))
        result_img.putdata(output.flatten().tolist())

        # Set palette
        flat_palette = []
        for color in palette:
            flat_palette.extend(color)
        # Pad to 768 bytes (256 colors * 3)
        flat_palette.extend([0] * (768 - len(flat_palette)))
        result_img.putpalette(flat_palette)

        return QuantizationResult(
            image=result_img,
            palette=palette,
            color_map=output,
            error_sum=total_error
        )

    def _quantize_direct(
        self,
        pixels: np.ndarray,
        palette: List[RGB]
    ) -> Tuple[np.ndarray, float]:
        """Direct quantization without dithering."""
        height, width = pixels.shape[:2]
        output = np.zeros((height, width), dtype=np.uint8)
        total_error = 0.0

        for y in range(height):
            for x in range(width):
                rgb = tuple(pixels[y, x])
                idx = find_nearest_perceptual(rgb, palette, self.method)
                output[y, x] = idx
                total_error += calculate_color_distance(rgb, palette[idx], 'RGB')

        return output, total_error

    def _quantize_dithered(
        self,
        pixels: np.ndarray,
        palette: List[RGB]
    ) -> Tuple[np.ndarray, float]:
        """Floyd-Steinberg dithered quantization."""
        height, width = pixels.shape[:2]
        output = np.zeros((height, width), dtype=np.uint8)
        error_buffer = pixels.astype(np.float32).copy()
        total_error = 0.0

        strength = self.dither_strength

        for y in range(height):
            for x in range(width):
                old_pixel = error_buffer[y, x].copy()
                old_pixel = np.clip(old_pixel, 0, 255)
                rgb = (int(old_pixel[0]), int(old_pixel[1]), int(old_pixel[2]))

                idx = find_nearest_perceptual(rgb, palette, self.method)
                new_pixel = np.array(palette[idx], dtype=np.float32)
                output[y, x] = idx

                # Calculate and distribute error
                quant_error = (old_pixel - new_pixel) * strength
                total_error += np.sum(np.abs(quant_error))

                # Floyd-Steinberg error distribution
                if x + 1 < width:
                    error_buffer[y, x + 1] += quant_error * (7 / 16)
                if y + 1 < height:
                    if x > 0:
                        error_buffer[y + 1, x - 1] += quant_error * (3 / 16)
                    error_buffer[y + 1, x] += quant_error * (5 / 16)
                    if x + 1 < width:
                        error_buffer[y + 1, x + 1] += quant_error * (1 / 16)

        return output, total_error

    def quantize_with_extraction(
        self,
        image: Image.Image,
        num_colors: int = 16,
        dither: bool = False,
        extraction_method: str = 'kmeans'
    ) -> QuantizationResult:
        """
        Extract optimal palette and quantize in one step.

        Args:
            image: Source image
            num_colors: Palette size
            dither: Apply dithering
            extraction_method: Palette extraction algorithm

        Returns:
            QuantizationResult with extracted palette
        """
        palette = extract_optimal_palette(
            image,
            num_colors=num_colors,
            method=extraction_method
        )
        return self.quantize(image, palette, dither=dither)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_available_methods() -> List[str]:
    """Return list of available color distance methods."""
    methods = ['RGB', 'CIELab']

    if COLOUR_AVAILABLE:
        methods.append('CIEDE2000')

    if COLORSPACIOUS_AVAILABLE:
        methods.append('CAM02-UCS')

    return methods


def get_recommended_method() -> ColorMethod:
    """Return best available color distance method."""
    if COLOUR_AVAILABLE:
        return 'CIEDE2000'
    if COLORSPACIOUS_AVAILABLE:
        return 'CAM02-UCS'
    return 'CIELab'
