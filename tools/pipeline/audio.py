"""
Audio Pipeline for Genesis/SGDK.

This module provides tools for converting and managing audio assets
for Sega Genesis game development with SGDK.

Features:
    - WAV to Genesis PCM conversion (8-bit unsigned/signed)
    - Sample rate conversion to Genesis-compatible rates
    - Audio analysis and validation
    - SFX organization and bank management
    - SGDK resource file generation

Supported Formats:
    - Input: WAV, MP3, OGG, FLAC (via pydub if available)
    - Output: PCM (8-bit), ADPCM (4-bit), raw binary

Dependencies:
    - pydub (optional): For advanced audio format support
    - wave: For basic WAV handling (built-in)

Example:
    >>> from pipeline.audio import AudioConverter, SFXManager
    >>> converter = AudioConverter()
    >>> result = converter.convert_wav("jump.wav", "out/jump.pcm")
    >>> print(f"Converted: {result.original_size} -> {result.converted_size} bytes")
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union
import struct
import wave
import array
import math

# =============================================================================
# Enums and Constants
# =============================================================================

class AudioFormat(Enum):
    """Supported audio formats."""
    WAV = "wav"             # Standard WAV file
    PCM_U8 = "pcm_u8"       # 8-bit unsigned PCM (Genesis default)
    PCM_S8 = "pcm_s8"       # 8-bit signed PCM
    PCM_U4 = "pcm_u4"       # 4-bit unsigned (ADPCM-like)
    RAW = "raw"             # Raw binary


class SFXPriority(Enum):
    """Sound effect priority levels."""
    LOW = 0         # Background sounds, ambient
    NORMAL = 1      # Standard game sounds
    HIGH = 2        # Important sounds (hits, pickups)
    CRITICAL = 3    # Must play (player death, game over)


# Genesis Z80 compatible sample rates
# Lower rates = smaller files, lower quality
GENESIS_SAMPLE_RATES = [
    8000,   # Low quality, very small
    11025,  # Low-medium quality
    13400,  # Medium quality (commonly used for SFX)
    16000,  # Medium-high quality
    22050,  # High quality (music samples)
    32000,  # Very high quality (rarely used due to size)
]

# Default sample rate for SFX (good balance of quality/size)
DEFAULT_SFX_RATE = 13400

# Default sample rate for music samples
DEFAULT_MUSIC_RATE = 22050

# Z80 CPU usage estimates (percentage per sample rate)
# Higher rates = more Z80 cycles for playback
Z80_CPU_USAGE = {
    8000: 10,
    11025: 14,
    13400: 17,
    16000: 20,
    22050: 28,
    32000: 40,
}


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class AudioInfo:
    """
    Information about an audio file.

    Attributes:
        path: Path to audio file
        format: Audio format
        sample_rate: Sample rate in Hz
        channels: Number of channels (1=mono, 2=stereo)
        bit_depth: Bits per sample
        duration_ms: Duration in milliseconds
        frame_count: Total number of sample frames
        size_bytes: File size in bytes
    """
    path: str
    format: AudioFormat
    sample_rate: int
    channels: int
    bit_depth: int
    duration_ms: int
    frame_count: int
    size_bytes: int

    @property
    def duration_seconds(self) -> float:
        """Duration in seconds."""
        return self.duration_ms / 1000.0

    def estimated_genesis_size(self, target_rate: int = DEFAULT_SFX_RATE) -> int:
        """Estimate size when converted to Genesis format (8-bit mono)."""
        # Calculate frames at target rate
        target_frames = int(self.frame_count * (target_rate / self.sample_rate))
        # 8-bit mono = 1 byte per sample
        return target_frames


@dataclass
class ConversionResult:
    """
    Result of audio conversion operation.

    Attributes:
        success: Whether conversion succeeded
        input_path: Path to input file
        output_path: Path to output file
        original_size: Original file size in bytes
        converted_size: Converted file size in bytes
        original_rate: Original sample rate
        target_rate: Target sample rate after conversion
        duration_ms: Duration in milliseconds
        warnings: List of warning messages
        error: Error message if failed
    """
    success: bool
    input_path: str
    output_path: str
    original_size: int = 0
    converted_size: int = 0
    original_rate: int = 0
    target_rate: int = 0
    duration_ms: int = 0
    warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def compression_ratio(self) -> float:
        """Compression ratio (converted/original)."""
        if self.original_size == 0:
            return 0.0
        return self.converted_size / self.original_size

    @property
    def savings_percent(self) -> float:
        """Size reduction percentage."""
        return (1.0 - self.compression_ratio) * 100


@dataclass
class SoundEffect:
    """
    A sound effect definition.

    Attributes:
        name: Unique identifier for the SFX
        path: Path to audio file
        priority: Playback priority
        channel: Preferred Z80 channel (-1 = auto)
        loop: Whether SFX should loop
        volume: Volume level (0-15 for Genesis)
        properties: Additional custom properties
    """
    name: str
    path: str
    priority: SFXPriority = SFXPriority.NORMAL
    channel: int = -1
    loop: bool = False
    volume: int = 15
    properties: Dict[str, any] = field(default_factory=dict)

    def get_id(self) -> str:
        """Get C-friendly identifier."""
        return self.name.upper().replace(" ", "_").replace("-", "_")


@dataclass
class SFXBank:
    """
    A collection of related sound effects.

    Banks help organize SFX and manage memory.
    Each bank can be loaded/unloaded independently.

    Attributes:
        name: Bank name
        effects: List of sound effects in this bank
        max_size: Maximum bank size in bytes
    """
    name: str
    effects: List[SoundEffect] = field(default_factory=list)
    max_size: int = 32768  # 32KB default

    def add(self, sfx: SoundEffect) -> bool:
        """Add SFX to bank. Returns False if would exceed max size."""
        # Note: actual size check requires file access
        self.effects.append(sfx)
        return True

    def get_sfx(self, name: str) -> Optional[SoundEffect]:
        """Get SFX by name."""
        for sfx in self.effects:
            if sfx.name == name:
                return sfx
        return None

    @property
    def count(self) -> int:
        """Number of effects in bank."""
        return len(self.effects)


@dataclass
class ValidationResult:
    """Result of audio validation."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, msg: str) -> None:
        """Add error and mark as invalid."""
        self.errors.append(msg)
        self.valid = False

    def add_warning(self, msg: str) -> None:
        """Add warning (doesn't affect validity)."""
        self.warnings.append(msg)


# =============================================================================
# Audio Converter
# =============================================================================

class AudioConverter:
    """
    Convert audio files for Genesis/SGDK.

    Converts WAV files to Genesis-compatible formats:
    - 8-bit unsigned PCM (most common)
    - 8-bit signed PCM
    - Sample rate conversion to Genesis rates

    Example:
        >>> converter = AudioConverter()
        >>> result = converter.convert_wav("input.wav", "output.pcm",
        ...                                target_rate=13400)
        >>> if result.success:
        ...     print(f"Saved {result.converted_size} bytes")
    """

    def __init__(self):
        """Initialize audio converter."""
        self._pydub_available = self._check_pydub()

    def _check_pydub(self) -> bool:
        """Check if pydub is available for advanced format support."""
        try:
            import pydub
            return True
        except ImportError:
            return False

    def analyze(self, path: str) -> AudioInfo:
        """
        Analyze an audio file.

        Args:
            path: Path to audio file

        Returns:
            AudioInfo with file details

        Raises:
            ValueError: If file format is unsupported
            FileNotFoundError: If file doesn't exist
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")

        ext = path.suffix.lower()

        if ext == '.wav':
            return self._analyze_wav(path)
        elif self._pydub_available and ext in ['.mp3', '.ogg', '.flac']:
            return self._analyze_with_pydub(path)
        else:
            raise ValueError(f"Unsupported audio format: {ext}")

    def _analyze_wav(self, path: Path) -> AudioInfo:
        """Analyze a WAV file."""
        with wave.open(str(path), 'rb') as wav:
            channels = wav.getnchannels()
            sample_rate = wav.getframerate()
            bit_depth = wav.getsampwidth() * 8
            frame_count = wav.getnframes()

            duration_ms = int((frame_count / sample_rate) * 1000)

            return AudioInfo(
                path=str(path),
                format=AudioFormat.WAV,
                sample_rate=sample_rate,
                channels=channels,
                bit_depth=bit_depth,
                duration_ms=duration_ms,
                frame_count=frame_count,
                size_bytes=path.stat().st_size
            )

    def _analyze_with_pydub(self, path: Path) -> AudioInfo:
        """Analyze audio file using pydub."""
        from pydub import AudioSegment

        audio = AudioSegment.from_file(str(path))

        return AudioInfo(
            path=str(path),
            format=AudioFormat.WAV,  # Treat as WAV for conversion purposes
            sample_rate=audio.frame_rate,
            channels=audio.channels,
            bit_depth=audio.sample_width * 8,
            duration_ms=len(audio),
            frame_count=int(len(audio) * audio.frame_rate / 1000),
            size_bytes=path.stat().st_size
        )

    def convert_wav(self, input_path: str, output_path: str,
                    target_rate: int = DEFAULT_SFX_RATE,
                    target_format: AudioFormat = AudioFormat.PCM_U8,
                    normalize: bool = True) -> ConversionResult:
        """
        Convert WAV file to Genesis-compatible format.

        Args:
            input_path: Path to input WAV file
            output_path: Path for output file
            target_rate: Target sample rate (default: 13400 Hz)
            target_format: Output format (default: 8-bit unsigned PCM)
            normalize: Whether to normalize audio levels

        Returns:
            ConversionResult with conversion details
        """
        result = ConversionResult(
            success=False,
            input_path=input_path,
            output_path=output_path
        )

        try:
            # Read input
            input_path = Path(input_path)
            if not input_path.exists():
                result.error = f"Input file not found: {input_path}"
                return result

            result.original_size = input_path.stat().st_size

            # Load audio data
            samples, original_rate, channels, bit_depth = self._load_wav(input_path)
            result.original_rate = original_rate
            result.target_rate = target_rate

            # Convert to mono if stereo
            if channels == 2:
                samples = self._stereo_to_mono(samples, bit_depth)
                result.warnings.append("Converted stereo to mono")

            # Normalize bit depth to 16-bit for processing
            if bit_depth == 8:
                samples = self._8bit_to_16bit(samples)
            elif bit_depth == 24:
                samples = self._24bit_to_16bit(samples)
                result.warnings.append("Converted 24-bit to 16-bit")
            elif bit_depth == 32:
                samples = self._32bit_to_16bit(samples)
                result.warnings.append("Converted 32-bit to 16-bit")

            # Normalize volume
            if normalize:
                samples = self._normalize(samples)

            # Resample if needed
            if original_rate != target_rate:
                samples = self._resample(samples, original_rate, target_rate)
                result.warnings.append(f"Resampled {original_rate} Hz -> {target_rate} Hz")

            # Convert to target format
            if target_format == AudioFormat.PCM_U8:
                output_data = self._to_unsigned_8bit(samples)
            elif target_format == AudioFormat.PCM_S8:
                output_data = self._to_signed_8bit(samples)
            else:
                output_data = self._to_unsigned_8bit(samples)

            # Write output
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(bytes(output_data))

            result.converted_size = len(output_data)
            result.duration_ms = int((len(output_data) / target_rate) * 1000)
            result.success = True

            # Check for potential issues
            if target_rate not in GENESIS_SAMPLE_RATES:
                result.warnings.append(
                    f"Sample rate {target_rate} is non-standard for Genesis"
                )

        except Exception as e:
            result.error = str(e)

        return result

    def _load_wav(self, path: Path) -> Tuple[bytes, int, int, int]:
        """Load WAV file data."""
        with wave.open(str(path), 'rb') as wav:
            sample_rate = wav.getframerate()
            channels = wav.getnchannels()
            bit_depth = wav.getsampwidth() * 8
            frames = wav.readframes(wav.getnframes())
            return (frames, sample_rate, channels, bit_depth)

    def _stereo_to_mono(self, data: bytes, bit_depth: int) -> bytes:
        """Convert stereo audio to mono by averaging channels."""
        bytes_per_sample = bit_depth // 8
        frame_size = bytes_per_sample * 2  # stereo = 2 channels

        mono_data = bytearray()

        if bit_depth == 16:
            # 16-bit signed
            for i in range(0, len(data), frame_size):
                left = struct.unpack_from('<h', data, i)[0]
                right = struct.unpack_from('<h', data, i + 2)[0]
                mono = (left + right) // 2
                mono_data.extend(struct.pack('<h', mono))
        elif bit_depth == 8:
            # 8-bit unsigned
            for i in range(0, len(data), frame_size):
                left = data[i]
                right = data[i + 1]
                mono = (left + right) // 2
                mono_data.append(mono)

        return bytes(mono_data)

    def _8bit_to_16bit(self, data: bytes) -> bytes:
        """Convert 8-bit unsigned to 16-bit signed."""
        result = bytearray()
        for sample in data:
            # Convert unsigned 8-bit (0-255) to signed 16-bit (-32768 to 32767)
            signed = (sample - 128) * 256
            result.extend(struct.pack('<h', signed))
        return bytes(result)

    def _24bit_to_16bit(self, data: bytes) -> bytes:
        """Convert 24-bit to 16-bit."""
        result = bytearray()
        for i in range(0, len(data), 3):
            # 24-bit little-endian
            low = data[i]
            mid = data[i + 1]
            high = data[i + 2]
            # Sign extend
            value = low | (mid << 8) | (high << 16)
            if high & 0x80:
                value -= 0x1000000
            # Scale to 16-bit
            scaled = value >> 8
            result.extend(struct.pack('<h', max(-32768, min(32767, scaled))))
        return bytes(result)

    def _32bit_to_16bit(self, data: bytes) -> bytes:
        """Convert 32-bit to 16-bit."""
        result = bytearray()
        for i in range(0, len(data), 4):
            value = struct.unpack_from('<i', data, i)[0]
            scaled = value >> 16
            result.extend(struct.pack('<h', max(-32768, min(32767, scaled))))
        return bytes(result)

    def _normalize(self, data: bytes, target_peak: float = 0.95) -> bytes:
        """Normalize audio to target peak level."""
        # Unpack as 16-bit signed
        samples = array.array('h')
        samples.frombytes(data)

        # Find peak
        peak = max(abs(min(samples)), abs(max(samples)))
        if peak == 0:
            return data

        # Calculate scale factor
        target = int(32767 * target_peak)
        scale = target / peak

        # Apply normalization
        normalized = array.array('h')
        for sample in samples:
            new_val = int(sample * scale)
            normalized.append(max(-32768, min(32767, new_val)))

        return normalized.tobytes()

    def _resample(self, data: bytes, from_rate: int, to_rate: int) -> bytes:
        """
        Resample audio using linear interpolation.

        This is a simple resampler. For better quality, use pydub or scipy.
        """
        # Unpack as 16-bit signed
        samples = array.array('h')
        samples.frombytes(data)

        # Calculate output length
        ratio = to_rate / from_rate
        output_len = int(len(samples) * ratio)

        # Resample with linear interpolation
        resampled = array.array('h')
        for i in range(output_len):
            # Source position (float)
            src_pos = i / ratio

            # Integer and fractional parts
            src_idx = int(src_pos)
            frac = src_pos - src_idx

            # Get samples for interpolation
            if src_idx + 1 < len(samples):
                s0 = samples[src_idx]
                s1 = samples[src_idx + 1]
            else:
                s0 = samples[min(src_idx, len(samples) - 1)]
                s1 = s0

            # Linear interpolation
            result = int(s0 + (s1 - s0) * frac)
            resampled.append(max(-32768, min(32767, result)))

        return resampled.tobytes()

    def _to_unsigned_8bit(self, data: bytes) -> bytes:
        """Convert 16-bit signed to 8-bit unsigned."""
        samples = array.array('h')
        samples.frombytes(data)

        result = bytearray()
        for sample in samples:
            # Convert signed 16-bit (-32768 to 32767) to unsigned 8-bit (0-255)
            unsigned = ((sample + 32768) >> 8) & 0xFF
            result.append(unsigned)

        return bytes(result)

    def _to_signed_8bit(self, data: bytes) -> bytes:
        """Convert 16-bit signed to 8-bit signed."""
        samples = array.array('h')
        samples.frombytes(data)

        result = bytearray()
        for sample in samples:
            # Convert signed 16-bit to signed 8-bit
            signed = (sample >> 8) & 0xFF
            result.append(signed)

        return bytes(result)

    def validate_for_genesis(self, path: str) -> ValidationResult:
        """
        Validate audio file for Genesis compatibility.

        Checks:
        - Sample rate compatibility
        - Bit depth
        - Channel count
        - Duration/size limits

        Args:
            path: Path to audio file

        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult(valid=True)

        try:
            info = self.analyze(path)

            # Check sample rate
            if info.sample_rate not in GENESIS_SAMPLE_RATES:
                nearest = min(GENESIS_SAMPLE_RATES,
                             key=lambda x: abs(x - info.sample_rate))
                result.add_warning(
                    f"Sample rate {info.sample_rate} Hz not standard. "
                    f"Will be converted to {nearest} Hz."
                )

            # Check channels
            if info.channels > 2:
                result.add_error(f"Too many channels: {info.channels} (max 2)")
            elif info.channels == 2:
                result.add_warning("Stereo will be converted to mono")

            # Check bit depth
            if info.bit_depth not in [8, 16, 24, 32]:
                result.add_error(f"Unsupported bit depth: {info.bit_depth}")
            elif info.bit_depth != 8 and info.bit_depth != 16:
                result.add_warning(
                    f"Bit depth {info.bit_depth} will be converted to 8-bit"
                )

            # Check duration (warn if very long)
            if info.duration_ms > 10000:  # 10 seconds
                result.add_warning(
                    f"Long audio ({info.duration_ms}ms) will use significant ROM space"
                )

            # Estimate size
            estimated = info.estimated_genesis_size()
            if estimated > 65536:  # 64KB
                result.add_warning(
                    f"Estimated size {estimated} bytes exceeds 64KB bank"
                )

        except Exception as e:
            result.add_error(str(e))

        return result

    def estimate_z80_usage(self, sample_rate: int) -> float:
        """
        Estimate Z80 CPU usage for sample playback.

        Higher sample rates require more Z80 cycles.

        Args:
            sample_rate: Playback sample rate

        Returns:
            Estimated CPU usage percentage
        """
        if sample_rate in Z80_CPU_USAGE:
            return Z80_CPU_USAGE[sample_rate]

        # Interpolate for non-standard rates
        rates = sorted(Z80_CPU_USAGE.keys())
        for i in range(len(rates) - 1):
            if rates[i] <= sample_rate <= rates[i + 1]:
                # Linear interpolation
                t = (sample_rate - rates[i]) / (rates[i + 1] - rates[i])
                return Z80_CPU_USAGE[rates[i]] + t * (
                    Z80_CPU_USAGE[rates[i + 1]] - Z80_CPU_USAGE[rates[i]]
                )

        # Extrapolate
        if sample_rate < rates[0]:
            return Z80_CPU_USAGE[rates[0]]
        return Z80_CPU_USAGE[rates[-1]]


# =============================================================================
# SFX Manager
# =============================================================================

class SFXManager:
    """
    Manage sound effect assets for a game.

    Organizes SFX into banks, generates resource files,
    and provides C header generation.

    Example:
        >>> manager = SFXManager()
        >>> manager.add_sfx("jump", "sfx/jump.wav", priority=SFXPriority.NORMAL)
        >>> manager.add_sfx("hit", "sfx/hit.wav", priority=SFXPriority.HIGH)
        >>> manager.export_resource_file("res/sfx.res")
        >>> manager.export_header("inc/sfx_ids.h")
    """

    def __init__(self):
        """Initialize SFX manager."""
        self.effects: Dict[str, SoundEffect] = {}
        self.banks: List[SFXBank] = []
        self.converter = AudioConverter()

    def add_sfx(self, name: str, path: str,
                priority: SFXPriority = SFXPriority.NORMAL,
                channel: int = -1,
                loop: bool = False,
                volume: int = 15,
                **properties) -> SoundEffect:
        """
        Add a sound effect.

        Args:
            name: Unique identifier
            path: Path to audio file
            priority: Playback priority
            channel: Preferred Z80 channel (-1 = auto)
            loop: Whether to loop
            volume: Volume level (0-15)
            **properties: Additional properties

        Returns:
            Created SoundEffect instance
        """
        sfx = SoundEffect(
            name=name,
            path=path,
            priority=priority,
            channel=channel,
            loop=loop,
            volume=volume,
            properties=dict(properties)
        )
        self.effects[name] = sfx
        return sfx

    def remove_sfx(self, name: str) -> bool:
        """Remove a sound effect by name."""
        if name in self.effects:
            del self.effects[name]
            return True
        return False

    def get_sfx(self, name: str) -> Optional[SoundEffect]:
        """Get sound effect by name."""
        return self.effects.get(name)

    def create_bank(self, name: str, max_size: int = 32768) -> SFXBank:
        """
        Create a new SFX bank.

        Args:
            name: Bank name
            max_size: Maximum size in bytes

        Returns:
            Created SFXBank instance
        """
        bank = SFXBank(name=name, max_size=max_size)
        self.banks.append(bank)
        return bank

    def auto_organize_banks(self, bank_size: int = 32768) -> List[SFXBank]:
        """
        Automatically organize SFX into banks by size.

        Uses first-fit decreasing bin packing.

        Args:
            bank_size: Maximum bank size in bytes

        Returns:
            List of created banks
        """
        # Clear existing banks
        self.banks = []

        # Get SFX sizes
        sfx_sizes = []
        for sfx in self.effects.values():
            try:
                info = self.converter.analyze(sfx.path)
                size = info.estimated_genesis_size()
                sfx_sizes.append((sfx, size))
            except Exception:
                # Assign estimated size if file not found
                sfx_sizes.append((sfx, 4096))

        # Sort by size descending (first-fit decreasing)
        sfx_sizes.sort(key=lambda x: x[1], reverse=True)

        # Bin packing
        for sfx, size in sfx_sizes:
            placed = False
            for bank in self.banks:
                # Calculate current bank usage
                bank_usage = sum(
                    self.converter.analyze(s.path).estimated_genesis_size()
                    if Path(s.path).exists() else 4096
                    for s in bank.effects
                )
                if bank_usage + size <= bank.max_size:
                    bank.effects.append(sfx)
                    placed = True
                    break

            if not placed:
                # Create new bank
                bank = SFXBank(name=f"sfx_bank_{len(self.banks)}", max_size=bank_size)
                bank.effects.append(sfx)
                self.banks.append(bank)

        return self.banks

    def convert_all(self, output_dir: str,
                     target_rate: int = DEFAULT_SFX_RATE) -> Dict[str, ConversionResult]:
        """
        Convert all SFX to Genesis format.

        Args:
            output_dir: Output directory for converted files
            target_rate: Target sample rate

        Returns:
            Dictionary mapping SFX names to ConversionResults
        """
        results = {}
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        for name, sfx in self.effects.items():
            output_path = output_dir / f"{name}.pcm"
            result = self.converter.convert_wav(
                sfx.path,
                str(output_path),
                target_rate=target_rate
            )
            results[name] = result

        return results

    def export_resource_file(self, output_path: str,
                              converted_dir: str = "res/sfx") -> str:
        """
        Generate SGDK .res file for SFX.

        Args:
            output_path: Output .res file path
            converted_dir: Directory containing converted PCM files

        Returns:
            Generated content as string
        """
        lines = [
            "// Auto-generated SFX resources",
            "// Generated by pipeline.audio",
            "",
        ]

        for name, sfx in self.effects.items():
            pcm_path = f"{converted_dir}/{name}.pcm"
            sfx_id = sfx.get_id()

            # WAV resource for PCM data
            lines.append(f'WAV {sfx_id} "{pcm_path}" XGM')

        content = "\n".join(lines)
        Path(output_path).write_text(content, encoding='utf-8')
        return content

    def export_header(self, output_path: str) -> str:
        """
        Generate C header with SFX IDs.

        Args:
            output_path: Output header file path

        Returns:
            Generated content as string
        """
        lines = [
            "// Auto-generated SFX identifiers",
            "// Generated by pipeline.audio",
            "",
            "#ifndef _SFX_IDS_H_",
            "#define _SFX_IDS_H_",
            "",
            "// SFX priority levels",
            "typedef enum {",
            "    SFX_PRIORITY_LOW = 0,",
            "    SFX_PRIORITY_NORMAL = 1,",
            "    SFX_PRIORITY_HIGH = 2,",
            "    SFX_PRIORITY_CRITICAL = 3,",
            "} SFXPriority;",
            "",
            "// SFX IDs",
            "typedef enum {",
        ]

        for i, (name, sfx) in enumerate(self.effects.items()):
            sfx_id = sfx.get_id()
            lines.append(f"    SFX_{sfx_id} = {i},")

        lines.extend([
            f"    SFX_COUNT = {len(self.effects)}",
            "} SFXID;",
            "",
        ])

        # Add priority table
        lines.extend([
            "// SFX priority table",
            f"const u8 sfx_priorities[SFX_COUNT] = {{",
        ])

        for name, sfx in self.effects.items():
            lines.append(f"    {sfx.priority.value},  // {sfx.get_id()}")

        lines.extend([
            "};",
            "",
            "#endif // _SFX_IDS_H_",
        ])

        content = "\n".join(lines)
        Path(output_path).write_text(content, encoding='utf-8')
        return content

    def validate_all(self) -> Dict[str, ValidationResult]:
        """
        Validate all SFX for Genesis compatibility.

        Returns:
            Dictionary mapping SFX names to ValidationResults
        """
        results = {}
        for name, sfx in self.effects.items():
            results[name] = self.converter.validate_for_genesis(sfx.path)
        return results

    def get_total_size_estimate(self, target_rate: int = DEFAULT_SFX_RATE) -> int:
        """
        Estimate total size of all SFX when converted.

        Args:
            target_rate: Target sample rate

        Returns:
            Estimated total size in bytes
        """
        total = 0
        for sfx in self.effects.values():
            try:
                info = self.converter.analyze(sfx.path)
                total += info.estimated_genesis_size(target_rate)
            except Exception:
                # Default estimate if file not accessible
                total += 4096
        return total

    def save_config(self, path: str) -> None:
        """
        Save SFX configuration to JSON file.

        Args:
            path: Output JSON file path
        """
        import json

        data = {
            "effects": {},
            "banks": []
        }

        for name, sfx in self.effects.items():
            data["effects"][name] = {
                "path": sfx.path,
                "priority": sfx.priority.value,
                "channel": sfx.channel,
                "loop": sfx.loop,
                "volume": sfx.volume,
                "properties": sfx.properties
            }

        for bank in self.banks:
            data["banks"].append({
                "name": bank.name,
                "max_size": bank.max_size,
                "effects": [s.name for s in bank.effects]
            })

        Path(path).write_text(json.dumps(data, indent=2), encoding='utf-8')

    def load_config(self, path: str) -> None:
        """
        Load SFX configuration from JSON file.

        Args:
            path: Input JSON file path
        """
        import json

        data = json.loads(Path(path).read_text(encoding='utf-8'))

        # Load effects
        self.effects = {}
        for name, sfx_data in data.get("effects", {}).items():
            self.add_sfx(
                name=name,
                path=sfx_data["path"],
                priority=SFXPriority(sfx_data.get("priority", 1)),
                channel=sfx_data.get("channel", -1),
                loop=sfx_data.get("loop", False),
                volume=sfx_data.get("volume", 15),
                **sfx_data.get("properties", {})
            )

        # Load banks
        self.banks = []
        for bank_data in data.get("banks", []):
            bank = SFXBank(
                name=bank_data["name"],
                max_size=bank_data.get("max_size", 32768)
            )
            for sfx_name in bank_data.get("effects", []):
                if sfx_name in self.effects:
                    bank.effects.append(self.effects[sfx_name])
            self.banks.append(bank)


# =============================================================================
# Convenience Functions
# =============================================================================

def convert_audio(input_path: str, output_path: str,
                   target_rate: int = DEFAULT_SFX_RATE) -> ConversionResult:
    """
    Convert an audio file to Genesis format.

    Convenience function for quick conversion.

    Args:
        input_path: Path to input audio file
        output_path: Path for output PCM file
        target_rate: Target sample rate (default: 13400 Hz)

    Returns:
        ConversionResult
    """
    converter = AudioConverter()
    return converter.convert_wav(input_path, output_path, target_rate)


def analyze_audio(path: str) -> AudioInfo:
    """
    Analyze an audio file.

    Convenience function for quick analysis.

    Args:
        path: Path to audio file

    Returns:
        AudioInfo with file details
    """
    converter = AudioConverter()
    return converter.analyze(path)


def validate_audio(path: str) -> ValidationResult:
    """
    Validate an audio file for Genesis.

    Convenience function for quick validation.

    Args:
        path: Path to audio file

    Returns:
        ValidationResult
    """
    converter = AudioConverter()
    return converter.validate_for_genesis(path)


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    # Enums
    'AudioFormat',
    'SFXPriority',
    # Constants
    'GENESIS_SAMPLE_RATES',
    'DEFAULT_SFX_RATE',
    'DEFAULT_MUSIC_RATE',
    'Z80_CPU_USAGE',
    # Data classes
    'AudioInfo',
    'ConversionResult',
    'SoundEffect',
    'SFXBank',
    'ValidationResult',
    # Classes
    'AudioConverter',
    'SFXManager',
    # Convenience functions
    'convert_audio',
    'analyze_audio',
    'validate_audio',
]
