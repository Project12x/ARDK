"""
VGM/XGM Tools for Genesis Audio Pipeline.

This module provides tools for working with VGM (Video Game Music) files
and converting them to SGDK's XGM format for Sega Genesis development.

VGM Format:
    VGM is a standard format for storing video game music data. For Genesis,
    it captures YM2612 (FM) and SN76489 (PSG) chip commands.

XGM Format:
    XGM is SGDK's optimized music format designed for efficient playback
    on Genesis hardware. It supports:
    - 6 FM channels (YM2612)
    - 4 PSG channels (SN76489)
    - Up to 4 PCM sample channels

Workflow:
    1. Compose in Furnace Tracker (recommended, open source)
    2. Export as VGM (Genesis/Mega Drive target)
    3. Validate: check for Genesis compatibility
    4. Convert: VGM → XGM using xgmtool
    5. Include in SGDK project

Dependencies:
    - xgmtool: SGDK's VGM→XGM converter (must be in PATH or specified)
    - No Python dependencies for VGM parsing (pure Python)

Example:
    >>> from pipeline.vgm import XGMToolWrapper, validate_vgm
    >>>
    >>> # Validate first
    >>> errors = validate_vgm("music.vgm")
    >>> if errors:
    ...     print(f"Validation failed: {errors}")
    ...
    >>> # Convert to XGM
    >>> wrapper = XGMToolWrapper()
    >>> result = wrapper.convert("music.vgm", "music.xgm")
    >>> print(f"Converted: {result.output_path}")
"""

from dataclasses import dataclass, field
from enum import Enum, IntFlag
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union
import struct
import subprocess
import shutil


# =============================================================================
# VGM Constants
# =============================================================================

# VGM file signature
VGM_SIGNATURE = b'Vgm '

# Minimum VGM version for reliable Genesis support
MIN_VGM_VERSION = 0x150  # Version 1.50

# Genesis chip clocks (NTSC)
YM2612_CLOCK_NTSC = 7670453      # ~7.67 MHz
SN76489_CLOCK_NTSC = 3579545     # ~3.58 MHz

# Genesis chip clocks (PAL)
YM2612_CLOCK_PAL = 7600489       # ~7.60 MHz
SN76489_CLOCK_PAL = 3546893      # ~3.55 MHz


class VGMChip(IntFlag):
    """Chips that can be present in a VGM file."""
    NONE = 0
    SN76489 = 1         # PSG (Genesis)
    YM2612 = 2          # FM (Genesis)
    YM2413 = 4          # OPLL (Master System)
    YM2151 = 8          # OPM (Arcade)
    YM2203 = 16         # OPN (PC-88)
    YM2608 = 32         # OPNA (PC-98)
    YM2610 = 64         # OPNB (Neo Geo)
    RF5C68 = 128        # PCM (Sega CD)
    UNKNOWN = 256


# =============================================================================
# VGM Header Parsing
# =============================================================================

@dataclass
class VGMHeader:
    """
    Parsed VGM file header.

    Contains metadata about the VGM file including version, chip clocks,
    and timing information.
    """
    signature: bytes
    eof_offset: int
    version: int
    sn76489_clock: int
    ym2612_clock: int
    gd3_offset: int
    total_samples: int
    loop_offset: int
    loop_samples: int
    rate: int               # Playback rate (usually 60 or 50)
    data_offset: int        # Offset to VGM data
    ym2151_clock: int = 0
    ym2203_clock: int = 0
    ym2608_clock: int = 0
    ym2610_clock: int = 0

    @property
    def version_string(self) -> str:
        """Get version as human-readable string (e.g., '1.71').

        VGM uses BCD (binary-coded decimal) format, so 0x171 = 1.71
        """
        major = (self.version >> 8) & 0xFF
        minor = self.version & 0xFF
        # Convert minor from BCD: 0x71 -> 71
        minor_tens = (minor >> 4) & 0x0F
        minor_ones = minor & 0x0F
        return f"{major}.{minor_tens}{minor_ones}"

    @property
    def duration_seconds(self) -> float:
        """Get total duration in seconds."""
        return self.total_samples / 44100.0

    @property
    def loop_duration_seconds(self) -> float:
        """Get loop duration in seconds."""
        return self.loop_samples / 44100.0

    @property
    def has_loop(self) -> bool:
        """Check if VGM has loop point."""
        return self.loop_offset > 0


@dataclass
class VGMInfo:
    """
    Complete information about a VGM file.

    Includes header data plus derived information about
    chips used and Genesis compatibility.
    """
    path: Path
    header: VGMHeader
    chips: VGMChip
    is_genesis_compatible: bool
    file_size: int
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


def parse_vgm_header(path: Union[str, Path]) -> VGMHeader:
    """
    Parse VGM file header.

    Args:
        path: Path to VGM file

    Returns:
        VGMHeader with parsed data

    Raises:
        ValueError: If file is not a valid VGM
    """
    path = Path(path)

    with open(path, 'rb') as f:
        # Read signature
        sig = f.read(4)
        if sig != VGM_SIGNATURE:
            raise ValueError(f"Not a valid VGM file: {path}")

        # Read header fields
        eof_offset = struct.unpack('<I', f.read(4))[0]
        version = struct.unpack('<I', f.read(4))[0]
        sn76489_clock = struct.unpack('<I', f.read(4))[0]
        ym2413_clock = struct.unpack('<I', f.read(4))[0]  # Not used for Genesis
        gd3_offset = struct.unpack('<I', f.read(4))[0]
        total_samples = struct.unpack('<I', f.read(4))[0]
        loop_offset = struct.unpack('<I', f.read(4))[0]
        loop_samples = struct.unpack('<I', f.read(4))[0]

        # Version 1.01+ fields
        rate = 0
        if version >= 0x101:
            rate = struct.unpack('<I', f.read(4))[0]
        else:
            f.read(4)  # Skip

        # Skip SN76489 feedback/shift
        f.read(4)

        # YM2612 clock (offset 0x2C)
        ym2612_clock = struct.unpack('<I', f.read(4))[0]

        # YM2151 clock (offset 0x30)
        ym2151_clock = struct.unpack('<I', f.read(4))[0]

        # Data offset (version 1.50+)
        if version >= 0x150:
            data_offset = struct.unpack('<I', f.read(4))[0]
            if data_offset:
                data_offset += 0x34  # Relative to offset 0x34
            else:
                data_offset = 0x40  # Default for 1.50
        else:
            data_offset = 0x40

        # Additional chip clocks for version 1.51+
        ym2203_clock = 0
        ym2608_clock = 0
        ym2610_clock = 0

        if version >= 0x151 and f.tell() < data_offset:
            f.seek(0x44)
            if f.tell() + 4 <= data_offset:
                ym2203_clock = struct.unpack('<I', f.read(4))[0]
            if f.tell() + 4 <= data_offset:
                ym2608_clock = struct.unpack('<I', f.read(4))[0]
            if f.tell() + 4 <= data_offset:
                ym2610_clock = struct.unpack('<I', f.read(4))[0]

    return VGMHeader(
        signature=sig,
        eof_offset=eof_offset,
        version=version,
        sn76489_clock=sn76489_clock,
        ym2612_clock=ym2612_clock,
        gd3_offset=gd3_offset,
        total_samples=total_samples,
        loop_offset=loop_offset,
        loop_samples=loop_samples,
        rate=rate or 60,  # Default to 60Hz
        data_offset=data_offset,
        ym2151_clock=ym2151_clock,
        ym2203_clock=ym2203_clock,
        ym2608_clock=ym2608_clock,
        ym2610_clock=ym2610_clock,
    )


def detect_vgm_chips(header: VGMHeader) -> VGMChip:
    """
    Detect which sound chips are used in a VGM file.

    Args:
        header: Parsed VGM header

    Returns:
        VGMChip flags indicating present chips
    """
    chips = VGMChip.NONE

    if header.sn76489_clock > 0:
        chips |= VGMChip.SN76489
    if header.ym2612_clock > 0:
        chips |= VGMChip.YM2612
    if header.ym2151_clock > 0:
        chips |= VGMChip.YM2151
    if header.ym2203_clock > 0:
        chips |= VGMChip.YM2203
    if header.ym2608_clock > 0:
        chips |= VGMChip.YM2608
    if header.ym2610_clock > 0:
        chips |= VGMChip.YM2610

    return chips


def validate_vgm(path: Union[str, Path]) -> List[str]:
    """
    Validate a VGM file for Genesis compatibility.

    Checks:
    - Valid VGM signature
    - VGM version >= 1.50
    - YM2612 chip present (Genesis FM)
    - No incompatible chips (YM2151, YM2203, etc.)

    Args:
        path: Path to VGM file

    Returns:
        List of error messages (empty if valid)
    """
    path = Path(path)
    errors = []

    if not path.exists():
        return [f"File not found: {path}"]

    try:
        header = parse_vgm_header(path)
    except ValueError as e:
        return [str(e)]
    except Exception as e:
        return [f"Failed to parse VGM: {e}"]

    # Check version
    if header.version < MIN_VGM_VERSION:
        errors.append(
            f"VGM version {header.version_string} < 1.50, may not convert correctly"
        )

    # Check for Genesis chips
    chips = detect_vgm_chips(header)

    if not (chips & VGMChip.YM2612):
        errors.append("No YM2612 (FM) chip data - not a Genesis VGM")

    # Check for incompatible chips
    incompatible = chips & (VGMChip.YM2151 | VGMChip.YM2203 |
                            VGMChip.YM2608 | VGMChip.YM2610)
    if incompatible:
        chip_names = []
        if incompatible & VGMChip.YM2151:
            chip_names.append("YM2151")
        if incompatible & VGMChip.YM2203:
            chip_names.append("YM2203")
        if incompatible & VGMChip.YM2608:
            chip_names.append("YM2608")
        if incompatible & VGMChip.YM2610:
            chip_names.append("YM2610")
        errors.append(f"Incompatible chips detected: {', '.join(chip_names)}")

    return errors


def get_vgm_info(path: Union[str, Path]) -> VGMInfo:
    """
    Get complete information about a VGM file.

    Args:
        path: Path to VGM file

    Returns:
        VGMInfo with all parsed data and validation results
    """
    path = Path(path)
    errors = []
    warnings = []

    try:
        header = parse_vgm_header(path)
        chips = detect_vgm_chips(header)
    except Exception as e:
        # Return minimal info on parse failure
        return VGMInfo(
            path=path,
            header=VGMHeader(
                signature=b'',
                eof_offset=0,
                version=0,
                sn76489_clock=0,
                ym2612_clock=0,
                gd3_offset=0,
                total_samples=0,
                loop_offset=0,
                loop_samples=0,
                rate=0,
                data_offset=0,
            ),
            chips=VGMChip.NONE,
            is_genesis_compatible=False,
            file_size=path.stat().st_size if path.exists() else 0,
            errors=[str(e)],
        )

    # Validation
    validation_errors = validate_vgm(path)
    errors.extend(validation_errors)

    # Warnings
    if header.version < 0x160:
        warnings.append(f"VGM version {header.version_string} is older, consider re-exporting")

    if not header.has_loop:
        warnings.append("No loop point defined - music will not loop")

    if header.duration_seconds > 300:
        warnings.append(f"Long track ({header.duration_seconds:.0f}s) may use significant ROM space")

    # Genesis compatibility
    is_genesis = bool(chips & VGMChip.YM2612) and not validation_errors

    return VGMInfo(
        path=path,
        header=header,
        chips=chips,
        is_genesis_compatible=is_genesis,
        file_size=path.stat().st_size,
        warnings=warnings,
        errors=errors,
    )


def estimate_xgm_size(vgm_info: VGMInfo) -> int:
    """
    Estimate resulting XGM file size.

    This is a rough estimate based on VGM file size and content.
    Actual XGM size depends on optimization passes.

    Args:
        vgm_info: VGM file information

    Returns:
        Estimated XGM size in bytes
    """
    # XGM is typically 60-80% of VGM size due to optimization
    base_estimate = int(vgm_info.file_size * 0.7)

    # PCM samples add overhead
    if vgm_info.chips & VGMChip.RF5C68:
        base_estimate = int(base_estimate * 1.2)

    return base_estimate


# =============================================================================
# XGM Conversion
# =============================================================================

@dataclass
class XGMConversionResult:
    """Result of VGM to XGM conversion."""
    success: bool
    input_path: Path
    output_path: Optional[Path]
    input_size: int
    output_size: int
    compression_ratio: float    # output/input
    pcm_channels: int           # Number of PCM channels used
    fm_channels: int            # Number of FM channels used (max 6)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""


class XGMToolWrapper:
    """
    Wrapper for SGDK's xgmtool VGM→XGM converter.

    xgmtool is part of SGDK and must be available in PATH or specified.
    Download SGDK from: https://github.com/Stephane-D/SGDK

    Example:
        >>> wrapper = XGMToolWrapper()
        >>> result = wrapper.convert("music.vgm", "music.xgm")
        >>> if result.success:
        ...     print(f"Converted to {result.output_path}")
        ...     print(f"Size: {result.output_size} bytes")

        >>> # With optimization
        >>> result = wrapper.convert("music.vgm", optimize=True, timing="ntsc")
    """

    def __init__(self, xgmtool_path: Optional[str] = None):
        """
        Initialize wrapper.

        Args:
            xgmtool_path: Path to xgmtool executable (default: search PATH)
        """
        self.exe = xgmtool_path or self._find_xgmtool()

    def _find_xgmtool(self) -> str:
        """Find xgmtool in PATH or common locations."""
        # Try PATH first
        exe = shutil.which("xgmtool")
        if exe:
            return exe

        # Try common SGDK locations
        common_paths = [
            Path.home() / "SGDK" / "bin" / "xgmtool.exe",
            Path("C:/SGDK/bin/xgmtool.exe"),
            Path("/opt/sgdk/bin/xgmtool"),
            Path.home() / ".sgdk" / "bin" / "xgmtool",
        ]

        for p in common_paths:
            if p.exists():
                return str(p)

        # Default to just "xgmtool" and hope for the best
        return "xgmtool"

    def is_available(self) -> bool:
        """Check if xgmtool is available."""
        try:
            result = subprocess.run(
                [self.exe],
                capture_output=True,
                timeout=5
            )
            # xgmtool returns non-zero with no args, but that's ok
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def convert(self,
                input_path: Union[str, Path],
                output_path: Optional[Union[str, Path]] = None,
                *,
                optimize: bool = True,
                timing: str = "ntsc",
                verbose: bool = False) -> XGMConversionResult:
        """
        Convert VGM file to XGM format.

        Args:
            input_path: Path to input VGM file
            output_path: Path for output XGM file (default: same name with .xgm)
            optimize: Run VGM optimization pass
            timing: "ntsc" (60Hz) or "pal" (50Hz)
            verbose: Include verbose output

        Returns:
            XGMConversionResult with status and metadata
        """
        input_path = Path(input_path)

        if output_path is None:
            output_path = input_path.with_suffix('.xgm')
        else:
            output_path = Path(output_path)

        # Validate input
        if not input_path.exists():
            return XGMConversionResult(
                success=False,
                input_path=input_path,
                output_path=None,
                input_size=0,
                output_size=0,
                compression_ratio=1.0,
                pcm_channels=0,
                fm_channels=0,
                errors=[f"Input file not found: {input_path}"],
            )

        # Build command
        cmd = [self.exe, str(input_path), str(output_path)]

        if optimize:
            cmd.append("-o")

        if timing == "pal":
            cmd.append("-p")

        if verbose:
            cmd.append("-v")

        # Run xgmtool
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 1 minute timeout
            )

            stdout = result.stdout
            stderr = result.stderr

            # Parse warnings from output
            warnings = []
            for line in stderr.split('\n'):
                line = line.strip()
                if line and 'warning' in line.lower():
                    warnings.append(line)

            # Check success
            if result.returncode != 0:
                return XGMConversionResult(
                    success=False,
                    input_path=input_path,
                    output_path=None,
                    input_size=input_path.stat().st_size,
                    output_size=0,
                    compression_ratio=1.0,
                    pcm_channels=0,
                    fm_channels=0,
                    warnings=warnings,
                    errors=[f"xgmtool failed with code {result.returncode}"],
                    stdout=stdout,
                    stderr=stderr,
                )

            # Get output size
            if output_path.exists():
                output_size = output_path.stat().st_size
            else:
                return XGMConversionResult(
                    success=False,
                    input_path=input_path,
                    output_path=None,
                    input_size=input_path.stat().st_size,
                    output_size=0,
                    compression_ratio=1.0,
                    pcm_channels=0,
                    fm_channels=0,
                    errors=["Output file not created"],
                    stdout=stdout,
                    stderr=stderr,
                )

            input_size = input_path.stat().st_size
            ratio = output_size / input_size if input_size > 0 else 1.0

            return XGMConversionResult(
                success=True,
                input_path=input_path,
                output_path=output_path,
                input_size=input_size,
                output_size=output_size,
                compression_ratio=ratio,
                pcm_channels=4,  # XGM supports up to 4 PCM
                fm_channels=6,   # YM2612 has 6 FM channels
                warnings=warnings,
                stdout=stdout,
                stderr=stderr,
            )

        except subprocess.TimeoutExpired:
            return XGMConversionResult(
                success=False,
                input_path=input_path,
                output_path=None,
                input_size=input_path.stat().st_size if input_path.exists() else 0,
                output_size=0,
                compression_ratio=1.0,
                pcm_channels=0,
                fm_channels=0,
                errors=["xgmtool timed out"],
            )
        except FileNotFoundError:
            return XGMConversionResult(
                success=False,
                input_path=input_path,
                output_path=None,
                input_size=input_path.stat().st_size if input_path.exists() else 0,
                output_size=0,
                compression_ratio=1.0,
                pcm_channels=0,
                fm_channels=0,
                errors=[f"xgmtool not found at: {self.exe}"],
            )
        except Exception as e:
            return XGMConversionResult(
                success=False,
                input_path=input_path,
                output_path=None,
                input_size=input_path.stat().st_size if input_path.exists() else 0,
                output_size=0,
                compression_ratio=1.0,
                pcm_channels=0,
                fm_channels=0,
                errors=[f"Conversion failed: {e}"],
            )

    def batch_convert(self,
                      input_paths: List[Union[str, Path]],
                      output_dir: Optional[Union[str, Path]] = None,
                      **kwargs) -> List[XGMConversionResult]:
        """
        Convert multiple VGM files to XGM.

        Args:
            input_paths: List of VGM file paths
            output_dir: Directory for output files (default: same as input)
            **kwargs: Additional arguments passed to convert()

        Returns:
            List of XGMConversionResult for each file
        """
        results = []

        for input_path in input_paths:
            input_path = Path(input_path)

            if output_dir:
                output_path = Path(output_dir) / input_path.with_suffix('.xgm').name
            else:
                output_path = None

            result = self.convert(input_path, output_path, **kwargs)
            results.append(result)

        return results


# =============================================================================
# WOPN Bank Parsing
# =============================================================================

@dataclass
class WOPNOperator:
    """
    FM operator parameters for YM2612.

    Each FM voice has 4 operators with these parameters.
    """
    detune: int             # DT (0-7)
    multiple: int           # MUL (0-15)
    total_level: int        # TL (0-127) - volume/attenuation
    rate_scaling: int       # RS (0-3)
    attack_rate: int        # AR (0-31)
    decay_1_rate: int       # D1R (0-31)
    decay_2_rate: int       # D2R (0-31)
    release_rate: int       # RR (0-15)
    sustain_level: int      # SL (0-15)
    am_enable: bool         # AM on/off
    ssg_eg: int             # SSG-EG (0-15)


@dataclass
class WOPNPatch:
    """
    FM instrument patch from WOPN bank.

    Contains algorithm, feedback, and 4 operator definitions.
    """
    name: str
    algorithm: int          # ALG (0-7) - operator connection pattern
    feedback: int           # FB (0-7) - operator 1 self-feedback
    operators: List[WOPNOperator]
    lfo_sensitivity: int = 0    # AMS/FMS
    note_offset: int = 0        # Transpose

    def to_tfi(self) -> bytes:
        """Export to TFI format (common FM instrument format)."""
        # TFI format: ALG, FB, then 4 operators (11 bytes each)
        data = bytearray()
        data.append(self.algorithm)
        data.append(self.feedback)

        for op in self.operators:
            data.append(op.multiple | (op.detune << 4))
            data.append(op.total_level)
            data.append(op.attack_rate | (op.rate_scaling << 6))
            data.append(op.decay_1_rate | (op.am_enable << 7))
            data.append(op.decay_2_rate)
            data.append(op.sustain_level | (op.release_rate << 4))
            data.append(op.ssg_eg)
            # Padding to 11 bytes
            data.extend([0, 0, 0, 0])

        return bytes(data)


@dataclass
class WOPNBank:
    """
    Collection of FM patches from a WOPN bank file.
    """
    name: str
    version: int
    melodic_patches: List[WOPNPatch]
    drum_patches: List[WOPNPatch]

    def get_patch(self, index: int, drum: bool = False) -> Optional[WOPNPatch]:
        """Get patch by index."""
        patches = self.drum_patches if drum else self.melodic_patches
        if 0 <= index < len(patches):
            return patches[index]
        return None

    def find_patch(self, name: str) -> Optional[WOPNPatch]:
        """Find patch by name (case-insensitive)."""
        name_lower = name.lower()
        for patch in self.melodic_patches + self.drum_patches:
            if patch.name.lower() == name_lower:
                return patch
        return None


class WOPNParser:
    """
    Parser for WOPN instrument bank files.

    WOPN is the format used by OPN2BankEditor and other FM patch tools.
    See: https://github.com/Wohlstand/OPN2BankEditor

    Example:
        >>> parser = WOPNParser()
        >>> bank = parser.load("instruments.wopn")
        >>> print(f"Loaded {len(bank.melodic_patches)} melodic patches")
        >>> bass = bank.find_patch("Bass")
        >>> print(f"Bass algorithm: {bass.algorithm}")
    """

    # WOPN magic bytes
    MAGIC = b'WOPN2-BANK\x00'
    MAGIC_V1 = b'WOPN2-B\x00'

    def load(self, path: Union[str, Path]) -> WOPNBank:
        """
        Load WOPN bank file.

        Args:
            path: Path to .wopn file

        Returns:
            WOPNBank with parsed patches

        Raises:
            ValueError: If file is not valid WOPN
        """
        path = Path(path)

        with open(path, 'rb') as f:
            # Read and validate magic
            magic = f.read(11)

            if magic == self.MAGIC:
                version = 2
            elif magic[:8] == self.MAGIC_V1:
                version = 1
                f.seek(8)
            else:
                raise ValueError(f"Not a valid WOPN bank: {path}")

            # Read header
            if version >= 2:
                file_version = struct.unpack('<H', f.read(2))[0]
            else:
                file_version = 1

            num_melodic_banks = struct.unpack('<H', f.read(2))[0]
            num_drum_banks = struct.unpack('<H', f.read(2))[0]

            # Read flags (version 2+)
            lfo_enabled = False
            lfo_frequency = 0

            if version >= 2 and file_version >= 2:
                flags = f.read(1)[0]
                lfo_enabled = bool(flags & 0x01)
                lfo_frequency = f.read(1)[0]

            # Read patches
            melodic_patches = []
            drum_patches = []

            # Each bank has 128 patches
            for bank_idx in range(num_melodic_banks):
                for patch_idx in range(128):
                    patch = self._read_patch(f, version)
                    if patch:
                        melodic_patches.append(patch)

            for bank_idx in range(num_drum_banks):
                for patch_idx in range(128):
                    patch = self._read_patch(f, version)
                    if patch:
                        drum_patches.append(patch)

        return WOPNBank(
            name=path.stem,
            version=file_version,
            melodic_patches=melodic_patches,
            drum_patches=drum_patches,
        )

    def _read_patch(self, f, version: int) -> Optional[WOPNPatch]:
        """Read a single patch from file."""
        try:
            # Patch name (32 bytes, null-terminated)
            name_bytes = f.read(32)
            name = name_bytes.split(b'\x00')[0].decode('ascii', errors='replace').strip()

            # Skip empty patches
            if not name or name == '\x00' * len(name):
                # Still need to read the rest of the patch data
                f.read(34)  # Remaining patch data
                return None

            # Key offset and other metadata
            note_offset = struct.unpack('<h', f.read(2))[0]  # signed

            # Algorithm and feedback byte
            alg_fb = f.read(1)[0]
            algorithm = alg_fb & 0x07
            feedback = (alg_fb >> 3) & 0x07

            # LFO sensitivity
            lfo_sens = f.read(1)[0]

            # Read 4 operators
            operators = []
            for _ in range(4):
                op_data = f.read(7)
                if len(op_data) < 7:
                    return None

                op = WOPNOperator(
                    detune=(op_data[0] >> 4) & 0x07,
                    multiple=op_data[0] & 0x0F,
                    total_level=op_data[1] & 0x7F,
                    rate_scaling=(op_data[2] >> 6) & 0x03,
                    attack_rate=op_data[2] & 0x1F,
                    am_enable=bool(op_data[3] & 0x80),
                    decay_1_rate=op_data[3] & 0x1F,
                    decay_2_rate=op_data[4] & 0x1F,
                    sustain_level=(op_data[5] >> 4) & 0x0F,
                    release_rate=op_data[5] & 0x0F,
                    ssg_eg=op_data[6] & 0x0F,
                )
                operators.append(op)

            return WOPNPatch(
                name=name,
                algorithm=algorithm,
                feedback=feedback,
                operators=operators,
                lfo_sensitivity=lfo_sens,
                note_offset=note_offset,
            )

        except (struct.error, IndexError):
            return None

    def save(self, bank: WOPNBank, path: Union[str, Path]) -> None:
        """
        Save WOPN bank file.

        Args:
            bank: Bank to save
            path: Output path
        """
        path = Path(path)

        with open(path, 'wb') as f:
            # Write magic
            f.write(self.MAGIC)

            # Write version
            f.write(struct.pack('<H', bank.version))

            # Calculate bank counts (128 patches per bank)
            num_melodic = (len(bank.melodic_patches) + 127) // 128
            num_drum = (len(bank.drum_patches) + 127) // 128

            f.write(struct.pack('<H', max(1, num_melodic)))
            f.write(struct.pack('<H', num_drum))

            # Flags (LFO disabled by default)
            f.write(bytes([0, 0]))

            # Write patches
            self._write_patches(f, bank.melodic_patches, num_melodic * 128)
            self._write_patches(f, bank.drum_patches, num_drum * 128)

    def _write_patches(self, f, patches: List[WOPNPatch], total: int) -> None:
        """Write patches with padding."""
        for i in range(total):
            if i < len(patches):
                self._write_patch(f, patches[i])
            else:
                self._write_empty_patch(f)

    def _write_patch(self, f, patch: WOPNPatch) -> None:
        """Write a single patch."""
        # Name (32 bytes)
        name_bytes = patch.name.encode('ascii', errors='replace')[:31]
        f.write(name_bytes.ljust(32, b'\x00'))

        # Note offset
        f.write(struct.pack('<h', patch.note_offset))

        # Algorithm and feedback
        f.write(bytes([patch.algorithm | (patch.feedback << 3)]))

        # LFO sensitivity
        f.write(bytes([patch.lfo_sensitivity]))

        # Operators
        for op in patch.operators:
            f.write(bytes([
                op.multiple | (op.detune << 4),
                op.total_level,
                op.attack_rate | (op.rate_scaling << 6),
                op.decay_1_rate | (op.am_enable << 7),
                op.decay_2_rate,
                op.sustain_level << 4 | op.release_rate,
                op.ssg_eg,
            ]))

    def _write_empty_patch(self, f) -> None:
        """Write an empty patch placeholder."""
        f.write(b'\x00' * 32)  # Name
        f.write(b'\x00' * 2)   # Note offset
        f.write(b'\x00' * 2)   # Alg/FB, LFO
        f.write(b'\x00' * 28)  # 4 operators × 7 bytes
