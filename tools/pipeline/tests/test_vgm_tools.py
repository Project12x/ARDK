"""
Tests for VGM/XGM tools.

Tests VGM parsing, validation, XGM conversion, and WOPN bank handling.
"""

import pytest
import struct
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from pipeline.vgm.vgm_tools import (
    # Constants
    VGM_SIGNATURE,
    MIN_VGM_VERSION,
    YM2612_CLOCK_NTSC,
    SN76489_CLOCK_NTSC,
    VGMChip,
    # Header parsing
    VGMHeader,
    VGMInfo,
    parse_vgm_header,
    detect_vgm_chips,
    validate_vgm,
    get_vgm_info,
    estimate_xgm_size,
    # XGM conversion
    XGMConversionResult,
    XGMToolWrapper,
    # WOPN parsing
    WOPNOperator,
    WOPNPatch,
    WOPNBank,
    WOPNParser,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for test files."""
    return tmp_path


@pytest.fixture
def valid_vgm_header():
    """Create a valid VGM header for Genesis (version 1.71)."""
    header = bytearray(0x100)  # Ensure enough space

    # Signature (0x00)
    header[0:4] = VGM_SIGNATURE

    # EOF offset (0x04) - relative to 0x04
    struct.pack_into('<I', header, 0x04, 0x1000)

    # Version (0x08) - 1.71
    struct.pack_into('<I', header, 0x08, 0x171)

    # SN76489 clock (0x0C) - NTSC PSG
    struct.pack_into('<I', header, 0x0C, SN76489_CLOCK_NTSC)

    # YM2413 clock (0x10) - Not used for Genesis
    struct.pack_into('<I', header, 0x10, 0)

    # GD3 offset (0x14)
    struct.pack_into('<I', header, 0x14, 0x800)

    # Total samples (0x18) - 2 seconds at 44100Hz
    struct.pack_into('<I', header, 0x18, 88200)

    # Loop offset (0x1C)
    struct.pack_into('<I', header, 0x1C, 0x100)

    # Loop samples (0x20)
    struct.pack_into('<I', header, 0x20, 44100)

    # Rate (0x24) - 60Hz NTSC
    struct.pack_into('<I', header, 0x24, 60)

    # SN76489 feedback/shift (0x28) - skip

    # YM2612 clock (0x2C) - Genesis FM
    struct.pack_into('<I', header, 0x2C, YM2612_CLOCK_NTSC)

    # YM2151 clock (0x30) - Not used
    struct.pack_into('<I', header, 0x30, 0)

    # VGM data offset (0x34) - relative to 0x34
    struct.pack_into('<I', header, 0x34, 0x0C)  # Data starts at 0x40

    return bytes(header)


@pytest.fixture
def valid_vgm_file(temp_dir, valid_vgm_header):
    """Create a valid VGM file."""
    vgm_path = temp_dir / "test.vgm"

    with open(vgm_path, 'wb') as f:
        f.write(valid_vgm_header)
        # Add some dummy VGM data
        f.write(b'\x66')  # End of data command

    return vgm_path


@pytest.fixture
def invalid_vgm_file(temp_dir):
    """Create an invalid VGM file (wrong signature)."""
    vgm_path = temp_dir / "invalid.vgm"

    with open(vgm_path, 'wb') as f:
        f.write(b'NotVgm!!')
        f.write(b'\x00' * 100)

    return vgm_path


@pytest.fixture
def old_version_vgm_file(temp_dir):
    """Create a VGM file with old version (1.00)."""
    header = bytearray(0x100)

    header[0:4] = VGM_SIGNATURE
    struct.pack_into('<I', header, 0x04, 0x1000)
    struct.pack_into('<I', header, 0x08, 0x100)  # Version 1.00
    struct.pack_into('<I', header, 0x0C, SN76489_CLOCK_NTSC)
    struct.pack_into('<I', header, 0x2C, YM2612_CLOCK_NTSC)

    vgm_path = temp_dir / "old.vgm"
    with open(vgm_path, 'wb') as f:
        f.write(header)

    return vgm_path


@pytest.fixture
def no_fm_vgm_file(temp_dir):
    """Create a VGM file without YM2612 (PSG only)."""
    header = bytearray(0x100)

    header[0:4] = VGM_SIGNATURE
    struct.pack_into('<I', header, 0x04, 0x1000)
    struct.pack_into('<I', header, 0x08, 0x171)  # Version 1.71
    struct.pack_into('<I', header, 0x0C, SN76489_CLOCK_NTSC)
    struct.pack_into('<I', header, 0x2C, 0)  # No YM2612!
    struct.pack_into('<I', header, 0x34, 0x0C)

    vgm_path = temp_dir / "psg_only.vgm"
    with open(vgm_path, 'wb') as f:
        f.write(header)

    return vgm_path


# =============================================================================
# VGMChip Tests
# =============================================================================

class TestVGMChip:
    """Tests for VGMChip flag enum."""

    def test_chip_flags_are_distinct(self):
        """Each chip flag should be a unique bit."""
        chips = [VGMChip.SN76489, VGMChip.YM2612, VGMChip.YM2413,
                 VGMChip.YM2151, VGMChip.YM2203, VGMChip.YM2608, VGMChip.YM2610]

        for i, chip1 in enumerate(chips):
            for chip2 in chips[i+1:]:
                assert chip1 & chip2 == 0, f"{chip1} overlaps with {chip2}"

    def test_chip_combination(self):
        """Chips can be combined with bitwise OR."""
        genesis = VGMChip.SN76489 | VGMChip.YM2612

        assert genesis & VGMChip.SN76489
        assert genesis & VGMChip.YM2612
        assert not (genesis & VGMChip.YM2151)

    def test_none_is_zero(self):
        """VGMChip.NONE should be zero."""
        assert VGMChip.NONE == 0


# =============================================================================
# VGM Header Parsing Tests
# =============================================================================

class TestParseVGMHeader:
    """Tests for parse_vgm_header function."""

    def test_parse_valid_header(self, valid_vgm_file):
        """Should parse a valid VGM header."""
        header = parse_vgm_header(valid_vgm_file)

        assert header.signature == VGM_SIGNATURE
        assert header.version == 0x171
        assert header.sn76489_clock == SN76489_CLOCK_NTSC
        assert header.ym2612_clock == YM2612_CLOCK_NTSC
        assert header.total_samples == 88200
        assert header.rate == 60

    def test_version_string(self, valid_vgm_file):
        """Version should be formatted as string."""
        header = parse_vgm_header(valid_vgm_file)
        assert header.version_string == "1.71"

    def test_duration_seconds(self, valid_vgm_file):
        """Duration should be calculated from samples."""
        header = parse_vgm_header(valid_vgm_file)
        assert abs(header.duration_seconds - 2.0) < 0.01

    def test_loop_duration_seconds(self, valid_vgm_file):
        """Loop duration should be calculated from samples."""
        header = parse_vgm_header(valid_vgm_file)
        assert abs(header.loop_duration_seconds - 1.0) < 0.01

    def test_has_loop(self, valid_vgm_file):
        """Has loop property should detect loop offset."""
        header = parse_vgm_header(valid_vgm_file)
        assert header.has_loop is True

    def test_invalid_signature_raises(self, invalid_vgm_file):
        """Invalid VGM should raise ValueError."""
        with pytest.raises(ValueError, match="Not a valid VGM"):
            parse_vgm_header(invalid_vgm_file)

    def test_missing_file_raises(self, temp_dir):
        """Missing file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            parse_vgm_header(temp_dir / "nonexistent.vgm")

    def test_old_version_parses(self, old_version_vgm_file):
        """Old version VGM should still parse."""
        header = parse_vgm_header(old_version_vgm_file)
        assert header.version == 0x100
        assert header.version_string == "1.00"


# =============================================================================
# VGM Chip Detection Tests
# =============================================================================

class TestDetectVGMChips:
    """Tests for detect_vgm_chips function."""

    def test_detect_genesis_chips(self, valid_vgm_file):
        """Should detect both Genesis chips."""
        header = parse_vgm_header(valid_vgm_file)
        chips = detect_vgm_chips(header)

        assert chips & VGMChip.SN76489
        assert chips & VGMChip.YM2612

    def test_detect_psg_only(self, no_fm_vgm_file):
        """Should detect PSG-only VGM."""
        header = parse_vgm_header(no_fm_vgm_file)
        chips = detect_vgm_chips(header)

        assert chips & VGMChip.SN76489
        assert not (chips & VGMChip.YM2612)

    def test_detect_no_chips(self):
        """Should return NONE for empty header."""
        header = VGMHeader(
            signature=VGM_SIGNATURE,
            eof_offset=0,
            version=0x171,
            sn76489_clock=0,
            ym2612_clock=0,
            gd3_offset=0,
            total_samples=0,
            loop_offset=0,
            loop_samples=0,
            rate=60,
            data_offset=0x40,
        )

        chips = detect_vgm_chips(header)
        assert chips == VGMChip.NONE


# =============================================================================
# VGM Validation Tests
# =============================================================================

class TestValidateVGM:
    """Tests for validate_vgm function."""

    def test_valid_genesis_vgm(self, valid_vgm_file):
        """Valid Genesis VGM should return no errors."""
        errors = validate_vgm(valid_vgm_file)
        assert errors == []

    def test_missing_file(self, temp_dir):
        """Missing file should return error."""
        errors = validate_vgm(temp_dir / "missing.vgm")
        assert len(errors) == 1
        assert "not found" in errors[0].lower()

    def test_invalid_signature(self, invalid_vgm_file):
        """Invalid VGM should return error."""
        errors = validate_vgm(invalid_vgm_file)
        assert len(errors) >= 1

    def test_old_version_warning(self, old_version_vgm_file):
        """Old version should return warning."""
        errors = validate_vgm(old_version_vgm_file)
        assert any("version" in e.lower() for e in errors)

    def test_no_fm_chip_error(self, no_fm_vgm_file):
        """VGM without YM2612 should return error."""
        errors = validate_vgm(no_fm_vgm_file)
        assert any("ym2612" in e.lower() for e in errors)


# =============================================================================
# VGM Info Tests
# =============================================================================

class TestGetVGMInfo:
    """Tests for get_vgm_info function."""

    def test_get_info_valid_file(self, valid_vgm_file):
        """Should return complete info for valid VGM."""
        info = get_vgm_info(valid_vgm_file)

        assert info.path == valid_vgm_file
        assert info.is_genesis_compatible is True
        assert info.chips & VGMChip.YM2612
        assert info.file_size > 0
        assert info.errors == []

    def test_get_info_invalid_file(self, invalid_vgm_file):
        """Should return info with errors for invalid VGM."""
        info = get_vgm_info(invalid_vgm_file)

        assert info.is_genesis_compatible is False
        assert len(info.errors) > 0

    def test_get_info_warnings_for_no_loop(self, temp_dir):
        """Should warn if no loop point."""
        # Create VGM without loop
        header = bytearray(0x100)
        header[0:4] = VGM_SIGNATURE
        struct.pack_into('<I', header, 0x04, 0x1000)
        struct.pack_into('<I', header, 0x08, 0x171)
        struct.pack_into('<I', header, 0x0C, SN76489_CLOCK_NTSC)
        struct.pack_into('<I', header, 0x1C, 0)  # No loop
        struct.pack_into('<I', header, 0x2C, YM2612_CLOCK_NTSC)
        struct.pack_into('<I', header, 0x34, 0x0C)

        vgm_path = temp_dir / "noloop.vgm"
        with open(vgm_path, 'wb') as f:
            f.write(header)

        info = get_vgm_info(vgm_path)
        assert any("loop" in w.lower() for w in info.warnings)


# =============================================================================
# XGM Size Estimation Tests
# =============================================================================

class TestEstimateXGMSize:
    """Tests for estimate_xgm_size function."""

    def test_estimate_size(self, valid_vgm_file):
        """Should estimate XGM size from VGM info."""
        info = get_vgm_info(valid_vgm_file)
        estimate = estimate_xgm_size(info)

        # XGM is typically 60-80% of VGM size
        assert estimate > 0
        assert estimate < info.file_size


# =============================================================================
# XGM Conversion Tests
# =============================================================================

class TestXGMToolWrapper:
    """Tests for XGMToolWrapper class."""

    def test_initialization_default(self):
        """Should initialize with default path."""
        wrapper = XGMToolWrapper()
        assert wrapper.exe is not None

    def test_initialization_custom_path(self):
        """Should accept custom xgmtool path."""
        wrapper = XGMToolWrapper("/custom/path/xgmtool")
        assert wrapper.exe == "/custom/path/xgmtool"

    def test_is_available_when_missing(self):
        """Should return False when xgmtool not installed."""
        wrapper = XGMToolWrapper("/nonexistent/xgmtool")
        assert wrapper.is_available() is False

    def test_convert_missing_input(self, temp_dir):
        """Should return error for missing input file."""
        wrapper = XGMToolWrapper()
        result = wrapper.convert(temp_dir / "missing.vgm")

        assert result.success is False
        assert "not found" in result.errors[0].lower()

    @patch('pipeline.vgm.vgm_tools.subprocess.run')
    def test_convert_success(self, mock_run, valid_vgm_file, temp_dir):
        """Should convert VGM to XGM successfully."""
        output_path = temp_dir / "output.xgm"

        # Mock successful conversion
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Conversion complete",
            stderr=""
        )

        # Create fake output file
        with open(output_path, 'wb') as f:
            f.write(b'XGM\x00' + b'\x00' * 100)

        wrapper = XGMToolWrapper("xgmtool")
        result = wrapper.convert(valid_vgm_file, output_path)

        assert result.success is True
        assert result.output_path == output_path
        assert result.input_size > 0
        assert result.output_size > 0

    @patch('pipeline.vgm.vgm_tools.subprocess.run')
    def test_convert_failure(self, mock_run, valid_vgm_file, temp_dir):
        """Should handle conversion failure."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error: Invalid VGM"
        )

        wrapper = XGMToolWrapper("xgmtool")
        result = wrapper.convert(valid_vgm_file)

        assert result.success is False
        assert any("failed" in e.lower() for e in result.errors)

    @patch('pipeline.vgm.vgm_tools.subprocess.run')
    def test_convert_timeout(self, mock_run, valid_vgm_file):
        """Should handle timeout."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("xgmtool", 60)

        wrapper = XGMToolWrapper("xgmtool")
        result = wrapper.convert(valid_vgm_file)

        assert result.success is False
        assert any("timed out" in e.lower() for e in result.errors)

    @patch('pipeline.vgm.vgm_tools.subprocess.run')
    def test_convert_xgmtool_not_found(self, mock_run, valid_vgm_file):
        """Should handle xgmtool not found."""
        mock_run.side_effect = FileNotFoundError()

        wrapper = XGMToolWrapper("xgmtool")
        result = wrapper.convert(valid_vgm_file)

        assert result.success is False
        assert any("not found" in e.lower() for e in result.errors)

    @patch('pipeline.vgm.vgm_tools.subprocess.run')
    def test_convert_with_options(self, mock_run, valid_vgm_file, temp_dir):
        """Should pass options to xgmtool."""
        output_path = temp_dir / "output.xgm"

        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        with open(output_path, 'wb') as f:
            f.write(b'\x00' * 100)

        wrapper = XGMToolWrapper("xgmtool")
        wrapper.convert(valid_vgm_file, output_path, optimize=True, timing="pal", verbose=True)

        # Check that options were passed
        call_args = mock_run.call_args[0][0]
        assert "-o" in call_args
        assert "-p" in call_args
        assert "-v" in call_args

    @patch('pipeline.vgm.vgm_tools.subprocess.run')
    def test_batch_convert(self, mock_run, temp_dir):
        """Should convert multiple files."""
        # Create test VGM files
        vgm_files = []
        for i in range(3):
            vgm_path = temp_dir / f"test{i}.vgm"

            header = bytearray(0x100)
            header[0:4] = VGM_SIGNATURE
            struct.pack_into('<I', header, 0x08, 0x171)
            struct.pack_into('<I', header, 0x0C, SN76489_CLOCK_NTSC)
            struct.pack_into('<I', header, 0x2C, YM2612_CLOCK_NTSC)
            struct.pack_into('<I', header, 0x34, 0x0C)

            with open(vgm_path, 'wb') as f:
                f.write(header)

            # Create expected output
            with open(temp_dir / f"test{i}.xgm", 'wb') as f:
                f.write(b'\x00' * 50)

            vgm_files.append(vgm_path)

        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        wrapper = XGMToolWrapper("xgmtool")
        results = wrapper.batch_convert(vgm_files)

        assert len(results) == 3
        for result in results:
            assert result.success is True


# =============================================================================
# WOPN Operator Tests
# =============================================================================

class TestWOPNOperator:
    """Tests for WOPNOperator dataclass."""

    def test_operator_creation(self):
        """Should create operator with all parameters."""
        op = WOPNOperator(
            detune=3,
            multiple=5,
            total_level=40,
            rate_scaling=1,
            attack_rate=31,
            decay_1_rate=15,
            decay_2_rate=8,
            release_rate=7,
            sustain_level=5,
            am_enable=True,
            ssg_eg=0,
        )

        assert op.detune == 3
        assert op.multiple == 5
        assert op.total_level == 40
        assert op.am_enable is True


# =============================================================================
# WOPN Patch Tests
# =============================================================================

class TestWOPNPatch:
    """Tests for WOPNPatch dataclass."""

    @pytest.fixture
    def sample_patch(self):
        """Create a sample FM patch."""
        ops = [
            WOPNOperator(3, 1, 35, 0, 31, 10, 5, 8, 3, False, 0),
            WOPNOperator(0, 2, 40, 1, 28, 12, 6, 7, 4, True, 0),
            WOPNOperator(1, 4, 45, 0, 25, 14, 7, 6, 5, False, 0),
            WOPNOperator(2, 1, 30, 2, 31, 8, 4, 10, 2, False, 0),
        ]

        return WOPNPatch(
            name="TestBass",
            algorithm=4,
            feedback=5,
            operators=ops,
            lfo_sensitivity=0,
            note_offset=0,
        )

    def test_patch_creation(self, sample_patch):
        """Should create patch with operators."""
        assert sample_patch.name == "TestBass"
        assert sample_patch.algorithm == 4
        assert sample_patch.feedback == 5
        assert len(sample_patch.operators) == 4

    def test_to_tfi_format(self, sample_patch):
        """Should export to TFI format."""
        tfi_data = sample_patch.to_tfi()

        # TFI: 2 header bytes + 4 ops × 11 bytes = 46 bytes
        assert len(tfi_data) == 46
        assert tfi_data[0] == 4  # Algorithm
        assert tfi_data[1] == 5  # Feedback


# =============================================================================
# WOPN Bank Tests
# =============================================================================

class TestWOPNBank:
    """Tests for WOPNBank dataclass."""

    @pytest.fixture
    def sample_bank(self):
        """Create a sample bank with patches."""
        ops = [WOPNOperator(0, 1, 50, 0, 31, 10, 5, 8, 3, False, 0)] * 4

        patches = [
            WOPNPatch("Piano", 4, 3, ops),
            WOPNPatch("Bass", 7, 5, ops),
            WOPNPatch("Lead", 3, 2, ops),
        ]

        return WOPNBank(
            name="TestBank",
            version=2,
            melodic_patches=patches,
            drum_patches=[],
        )

    def test_bank_creation(self, sample_bank):
        """Should create bank with patches."""
        assert sample_bank.name == "TestBank"
        assert sample_bank.version == 2
        assert len(sample_bank.melodic_patches) == 3
        assert len(sample_bank.drum_patches) == 0

    def test_get_patch_by_index(self, sample_bank):
        """Should get patch by index."""
        patch = sample_bank.get_patch(1)
        assert patch is not None
        assert patch.name == "Bass"

    def test_get_patch_invalid_index(self, sample_bank):
        """Should return None for invalid index."""
        patch = sample_bank.get_patch(999)
        assert patch is None

    def test_find_patch_by_name(self, sample_bank):
        """Should find patch by name."""
        patch = sample_bank.find_patch("Lead")
        assert patch is not None
        assert patch.algorithm == 3

    def test_find_patch_case_insensitive(self, sample_bank):
        """Should find patch case-insensitively."""
        patch = sample_bank.find_patch("PIANO")
        assert patch is not None
        assert patch.name == "Piano"

    def test_find_patch_not_found(self, sample_bank):
        """Should return None if patch not found."""
        patch = sample_bank.find_patch("NotExists")
        assert patch is None


# =============================================================================
# WOPN Parser Tests
# =============================================================================

class TestWOPNParser:
    """Tests for WOPNParser class."""

    @pytest.fixture
    def parser(self):
        """Create WOPN parser."""
        return WOPNParser()

    @pytest.fixture
    def sample_wopn_file(self, temp_dir):
        """Create a sample WOPN file."""
        wopn_path = temp_dir / "test.wopn"

        with open(wopn_path, 'wb') as f:
            # Magic (11 bytes)
            f.write(b'WOPN2-BANK\x00')

            # Version (2 bytes)
            f.write(struct.pack('<H', 2))

            # Melodic banks (2 bytes) - 1 bank
            f.write(struct.pack('<H', 1))

            # Drum banks (2 bytes) - 0 banks
            f.write(struct.pack('<H', 0))

            # Flags (2 bytes)
            f.write(bytes([0, 0]))

            # Write 128 patches (1 bank)
            for i in range(128):
                # Name (32 bytes)
                if i == 0:
                    name = b'TestPatch\x00'
                else:
                    name = b'\x00'
                f.write(name.ljust(32, b'\x00'))

                # Note offset (2 bytes)
                f.write(struct.pack('<h', 0))

                # Alg/FB (1 byte) - alg=4, fb=3
                f.write(bytes([4 | (3 << 3)]))

                # LFO sens (1 byte)
                f.write(bytes([0]))

                # 4 operators × 7 bytes = 28 bytes
                for _ in range(4):
                    f.write(bytes([
                        0x11,  # DT/MUL
                        0x30,  # TL
                        0x1F,  # RS/AR
                        0x0A,  # AM/D1R
                        0x05,  # D2R
                        0x38,  # SL/RR
                        0x00,  # SSG-EG
                    ]))

        return wopn_path

    def test_parser_creation(self, parser):
        """Should create parser."""
        assert parser is not None
        assert parser.MAGIC == b'WOPN2-BANK\x00'

    def test_load_valid_file(self, parser, sample_wopn_file):
        """Should load valid WOPN file."""
        bank = parser.load(sample_wopn_file)

        assert bank.name == "test"
        assert bank.version == 2
        assert len(bank.melodic_patches) >= 1

    def test_load_parses_patch_data(self, parser, sample_wopn_file):
        """Should parse patch parameters correctly."""
        bank = parser.load(sample_wopn_file)

        # Find the named patch
        patch = bank.find_patch("TestPatch")
        assert patch is not None
        assert patch.algorithm == 4
        assert patch.feedback == 3
        assert len(patch.operators) == 4

    def test_load_invalid_file_raises(self, parser, temp_dir):
        """Should raise for invalid file."""
        invalid_path = temp_dir / "invalid.wopn"
        with open(invalid_path, 'wb') as f:
            f.write(b'NotWOPN')

        with pytest.raises(ValueError, match="Not a valid WOPN"):
            parser.load(invalid_path)

    def test_load_missing_file_raises(self, parser, temp_dir):
        """Should raise for missing file."""
        with pytest.raises(FileNotFoundError):
            parser.load(temp_dir / "missing.wopn")

    def test_save_and_reload(self, parser, temp_dir):
        """Should save and reload bank."""
        # Create bank
        ops = [WOPNOperator(1, 2, 50, 0, 31, 10, 5, 8, 3, False, 0)] * 4
        original_bank = WOPNBank(
            name="SaveTest",
            version=2,
            melodic_patches=[
                WOPNPatch("Synth1", 5, 4, ops),
                WOPNPatch("Synth2", 3, 2, ops),
            ],
            drum_patches=[],
        )

        # Save
        save_path = temp_dir / "saved.wopn"
        parser.save(original_bank, save_path)

        assert save_path.exists()

        # Reload
        loaded_bank = parser.load(save_path)

        assert loaded_bank.version == 2
        # At least our patches should be present
        assert loaded_bank.find_patch("Synth1") is not None
        assert loaded_bank.find_patch("Synth2") is not None


# =============================================================================
# Integration Tests
# =============================================================================

class TestVGMToolsIntegration:
    """Integration tests for VGM tools workflow."""

    def test_full_vgm_analysis_workflow(self, valid_vgm_file):
        """Test complete VGM analysis workflow."""
        # Step 1: Validate
        errors = validate_vgm(valid_vgm_file)
        assert errors == [], f"Validation failed: {errors}"

        # Step 2: Get full info
        info = get_vgm_info(valid_vgm_file)
        assert info.is_genesis_compatible

        # Step 3: Estimate conversion
        estimate = estimate_xgm_size(info)
        assert estimate > 0

        # Would normally convert here if xgmtool available

    def test_vgm_to_patch_workflow(self, temp_dir):
        """Test workflow: VGM info -> WOPN bank creation."""
        # Create VGM
        header = bytearray(0x100)
        header[0:4] = VGM_SIGNATURE
        struct.pack_into('<I', header, 0x08, 0x171)
        struct.pack_into('<I', header, 0x0C, SN76489_CLOCK_NTSC)
        struct.pack_into('<I', header, 0x2C, YM2612_CLOCK_NTSC)
        struct.pack_into('<I', header, 0x34, 0x0C)

        vgm_path = temp_dir / "song.vgm"
        with open(vgm_path, 'wb') as f:
            f.write(header)

        # Validate VGM
        info = get_vgm_info(vgm_path)
        assert info.is_genesis_compatible

        # Create associated patch bank
        ops = [WOPNOperator(0, 1, 50, 0, 31, 10, 5, 8, 3, False, 0)] * 4
        bank = WOPNBank(
            name="SongInstruments",
            version=2,
            melodic_patches=[WOPNPatch("SongBass", 4, 3, ops)],
            drum_patches=[],
        )

        # Save bank
        parser = WOPNParser()
        bank_path = temp_dir / "song_instruments.wopn"
        parser.save(bank, bank_path)

        assert bank_path.exists()
