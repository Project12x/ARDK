#!/usr/bin/env python3
"""
=============================================================================
ARDK - Unified Build System
ardk_build.py - Cross-platform build orchestration
=============================================================================

Builds ARDK projects for multiple target platforms from a single codebase.

Features:
  - Single command builds for any/all platforms
  - Asset pipeline integration (calls unified_pipeline.py)
  - Dependency tracking (only rebuild what changed)
  - Parallel builds for multiple targets
  - Validation of platform constraints

Usage:
  python ardk_build.py                    # Build default platform (NES)
  python ardk_build.py --platform genesis # Build for Genesis
  python ardk_build.py --all              # Build all platforms
  python ardk_build.py --clean            # Clean build artifacts
  python ardk_build.py --validate         # Validate without building

Configuration:
  Project settings in ardk_project.json (auto-generated if missing)

=============================================================================
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import hashlib
import shutil


# =============================================================================
# Platform Definitions
# =============================================================================

@dataclass
class PlatformConfig:
    """Configuration for a target platform."""
    name: str
    tier: str  # MINIMAL, STANDARD, EXTENDED
    family: str  # 6502, z80, 68k, 65816, arm
    toolchain: str  # cc65, sgdk, pvsneslib, devkitarm
    assembler: str
    linker: str
    c_compiler: Optional[str]
    rom_extension: str
    defines: List[str] = field(default_factory=list)
    include_paths: List[str] = field(default_factory=list)
    link_config: Optional[str] = None


# =============================================================================
# CPU Family Definitions
# =============================================================================

FAMILY_6502 = {
    "name": "6502",
    "asm_hal": "src/hal/asm/hal_6502.inc",
    "endian": "little",
    "word_size": 8,
    "platforms": ["nes", "c64", "pce", "atari2600", "atari7800"]
}

FAMILY_Z80 = {
    "name": "z80",
    "asm_hal": "src/hal/asm/hal_z80_gb.inc",
    "endian": "little",
    "word_size": 8,
    "platforms": ["gb", "gbc", "sms", "gg", "msx"]
}

FAMILY_68K = {
    "name": "68k",
    "asm_hal": "src/hal/asm/hal_68k.inc",
    "endian": "big",
    "word_size": 16,
    "platforms": ["genesis", "amiga", "neogeo", "x68000"]
}

FAMILY_65816 = {
    "name": "65816",
    "asm_hal": "src/hal/asm/hal_6502.inc",  # Uses 6502 base with extensions
    "endian": "little",
    "word_size": 16,
    "platforms": ["snes"]
}

FAMILY_ARM = {
    "name": "arm",
    "asm_hal": None,  # ARM uses C primarily
    "endian": "little",
    "word_size": 32,
    "platforms": ["gba", "nds"]
}

FAMILIES = {
    "6502": FAMILY_6502,
    "z80": FAMILY_Z80,
    "68k": FAMILY_68K,
    "65816": FAMILY_65816,
    "arm": FAMILY_ARM
}


# =============================================================================
# Platform Configurations
# =============================================================================

PLATFORMS: Dict[str, PlatformConfig] = {
    # --- 6502 Family (Primary: NES) ---
    "nes": PlatformConfig(
        name="NES",
        tier="MINIMAL",
        family="6502",
        toolchain="cc65",
        assembler="ca65",
        linker="ld65",
        c_compiler="cc65",
        rom_extension=".nes",
        defines=["PLATFORM_NES", "HAL_TIER=0", "HAL_PLATFORM_ID=0x0100"],
        include_paths=["src/hal", "src/hal/nes", "src/hal/asm"],
        link_config="nes.cfg"
    ),
    "c64": PlatformConfig(
        name="C64",
        tier="MINIMAL",
        family="6502",
        toolchain="cc65",
        assembler="ca65",
        linker="ld65",
        c_compiler="cc65",
        rom_extension=".prg",
        defines=["PLATFORM_C64", "HAL_TIER=0", "HAL_PLATFORM_ID=0x0101"],
        include_paths=["src/hal", "src/hal/c64", "src/hal/asm"],
        link_config="c64.cfg"
    ),
    "pce": PlatformConfig(
        name="PCE",
        tier="STANDARD",
        family="6502",
        toolchain="huc",
        assembler="pceas",
        linker="pceas",
        c_compiler="huc",
        rom_extension=".pce",
        defines=["PLATFORM_PCE", "HAL_TIER=1", "HAL_PLATFORM_ID=0x0102"],
        include_paths=["src/hal", "src/hal/pce", "src/hal/asm"],
        link_config="pce.cfg"
    ),

    # --- Z80 Family (Primary: Game Boy) ---
    "gb": PlatformConfig(
        name="GameBoy",
        tier="MINIMAL",
        family="z80",
        toolchain="rgbds",
        assembler="rgbasm",
        linker="rgblink",
        c_compiler=None,  # Assembly preferred
        rom_extension=".gb",
        defines=["PLATFORM_GB", "HAL_TIER=0", "HAL_PLATFORM_ID=0x0200"],
        include_paths=["src/hal", "src/hal/gb", "src/hal/asm"],
        link_config="gb.ld"
    ),
    "gbc": PlatformConfig(
        name="GBC",
        tier="MINIMAL",
        family="z80",
        toolchain="rgbds",
        assembler="rgbasm",
        linker="rgblink",
        c_compiler=None,
        rom_extension=".gbc",
        defines=["PLATFORM_GBC", "HAL_TIER=0", "HAL_PLATFORM_ID=0x0201"],
        include_paths=["src/hal", "src/hal/gbc", "src/hal/asm"],
        link_config="gbc.ld"
    ),
    "sms": PlatformConfig(
        name="SMS",
        tier="MINIMAL",
        family="z80",
        toolchain="devkitsms",
        assembler="wla-z80",
        linker="wlalink",
        c_compiler="sdcc",
        rom_extension=".sms",
        defines=["PLATFORM_SMS", "HAL_TIER=0", "HAL_PLATFORM_ID=0x0202"],
        include_paths=["src/hal", "src/hal/sms", "src/hal/asm"],
        link_config="sms.cfg"
    ),

    # --- 68000 Family (Primary: Genesis) ---
    "genesis": PlatformConfig(
        name="Genesis",
        tier="STANDARD",
        family="68k",
        toolchain="sgdk",
        assembler="m68k-elf-as",
        linker="m68k-elf-ld",
        c_compiler="m68k-elf-gcc",
        rom_extension=".bin",
        defines=["PLATFORM_GENESIS", "HAL_TIER=1", "HAL_PLATFORM_ID=0x0300"],
        include_paths=["src/hal", "src/hal/genesis", "src/hal/asm"],
        link_config="genesis.ld"
    ),
    "neogeo": PlatformConfig(
        name="NeoGeo",
        tier="EXTENDED",
        family="68k",
        toolchain="ngdevkit",
        assembler="m68k-neogeo-elf-as",
        linker="m68k-neogeo-elf-ld",
        c_compiler="m68k-neogeo-elf-gcc",
        rom_extension=".neo",
        defines=["PLATFORM_NEOGEO", "HAL_TIER=2", "HAL_PLATFORM_ID=0x0303"],
        include_paths=["src/hal", "src/hal/neogeo", "src/hal/asm"],
        link_config="neogeo.ld"
    ),
    "amiga": PlatformConfig(
        name="Amiga",
        tier="EXTENDED",
        family="68k",
        toolchain="vbcc",
        assembler="vasmm68k_mot",
        linker="vlink",
        c_compiler="vc",
        rom_extension=".adf",
        defines=["PLATFORM_AMIGA", "HAL_TIER=2", "HAL_PLATFORM_ID=0x0301"],
        include_paths=["src/hal", "src/hal/amiga", "src/hal/asm"],
        link_config="amiga.ld"
    ),

    # --- 65816 Family ---
    "snes": PlatformConfig(
        name="SNES",
        tier="STANDARD",
        family="65816",
        toolchain="pvsneslib",
        assembler="wla-65816",
        linker="wlalink",
        c_compiler="816-tcc",
        rom_extension=".sfc",
        defines=["PLATFORM_SNES", "HAL_TIER=1", "HAL_PLATFORM_ID=0x0400"],
        include_paths=["src/hal", "src/hal/snes", "src/hal/asm"],
        link_config="snes.cfg"
    ),

    # --- ARM Family ---
    "gba": PlatformConfig(
        name="GBA",
        tier="EXTENDED",
        family="arm",
        toolchain="devkitarm",
        assembler="arm-none-eabi-as",
        linker="arm-none-eabi-ld",
        c_compiler="arm-none-eabi-gcc",
        rom_extension=".gba",
        defines=["PLATFORM_GBA", "HAL_TIER=2", "HAL_PLATFORM_ID=0x0500"],
        include_paths=["src/hal", "src/hal/gba"],
        link_config="gba.ld"
    ),
}


# =============================================================================
# Project Configuration
# =============================================================================

DEFAULT_PROJECT_CONFIG = {
    "name": "ARDK Project",
    "version": "0.1.0",
    "default_platform": "nes",
    "platforms": ["nes"],
    "source_dirs": ["src/game", "src/hal"],
    "asset_dirs": ["gfx/sprites", "gfx/tiles", "sfx", "music"],
    "output_dir": "build",
    "hal_common": ["src/hal/hal_common.c", "src/hal/entity.c"],
    "game_sources": [],
    "asset_pipeline": {
        "sprite_size": 32,
        "palette_mode": "auto",
        "ai_labeling": True
    }
}


def load_project_config(project_root: Path) -> dict:
    """Load or create project configuration."""
    config_path = project_root / "ardk_project.json"

    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
            # Merge with defaults for any missing keys
            for key, value in DEFAULT_PROJECT_CONFIG.items():
                if key not in config:
                    config[key] = value
            return config
    else:
        # Create default config
        print(f"Creating default project config: {config_path}")
        with open(config_path, 'w') as f:
            json.dump(DEFAULT_PROJECT_CONFIG, f, indent=2)
        return DEFAULT_PROJECT_CONFIG.copy()


# =============================================================================
# Build System
# =============================================================================

class ARDKBuilder:
    """Main build orchestrator."""

    def __init__(self, project_root: Path, config: dict):
        self.root = project_root
        self.config = config
        self.output_dir = project_root / config["output_dir"]
        self.cache_dir = self.output_dir / ".cache"
        self.file_hashes: Dict[str, str] = {}
        self._load_cache()

    def _load_cache(self):
        """Load file hash cache for incremental builds."""
        cache_file = self.cache_dir / "hashes.json"
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                self.file_hashes = json.load(f)

    def _save_cache(self):
        """Save file hash cache."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = self.cache_dir / "hashes.json"
        with open(cache_file, 'w') as f:
            json.dump(self.file_hashes, f, indent=2)

    def _hash_file(self, path: Path) -> str:
        """Calculate MD5 hash of a file."""
        if not path.exists():
            return ""
        with open(path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def _file_changed(self, path: Path) -> bool:
        """Check if file has changed since last build."""
        key = str(path.relative_to(self.root))
        current_hash = self._hash_file(path)
        cached_hash = self.file_hashes.get(key, "")

        if current_hash != cached_hash:
            self.file_hashes[key] = current_hash
            return True
        return False

    def clean(self, platform: Optional[str] = None):
        """Clean build artifacts."""
        if platform:
            platform_dir = self.output_dir / platform
            if platform_dir.exists():
                shutil.rmtree(platform_dir)
                print(f"Cleaned: {platform_dir}")
        else:
            if self.output_dir.exists():
                shutil.rmtree(self.output_dir)
                print(f"Cleaned: {self.output_dir}")

        # Clear cache
        self.file_hashes = {}
        self._save_cache()

    def validate(self, platform: str) -> bool:
        """Validate project can build for platform."""
        if platform not in PLATFORMS:
            print(f"ERROR: Unknown platform '{platform}'")
            print(f"Available: {', '.join(PLATFORMS.keys())}")
            return False

        plat = PLATFORMS[platform]

        # Check toolchain availability
        toolchain_found = shutil.which(plat.assembler) is not None
        if not toolchain_found:
            print(f"WARNING: Toolchain not found: {plat.toolchain}")
            print(f"  Assembler '{plat.assembler}' not in PATH")
            # Don't fail - might be running validation only

        # Check required directories
        for source_dir in self.config["source_dirs"]:
            dir_path = self.root / source_dir
            if not dir_path.exists():
                print(f"ERROR: Source directory not found: {dir_path}")
                return False

        # Check HAL files exist
        hal_config = self.root / f"src/hal/{platform}/hal_config.h"
        if not hal_config.exists():
            print(f"ERROR: HAL config not found: {hal_config}")
            return False

        print(f"Validation passed for {plat.name}")
        return True

    def process_assets(self, platform: str) -> bool:
        """Run asset pipeline for platform."""
        pipeline_script = self.root / "tools" / "unified_pipeline.py"
        if not pipeline_script.exists():
            print("WARNING: unified_pipeline.py not found, skipping assets")
            return True

        plat = PLATFORMS[platform]
        output_dir = self.output_dir / platform / "assets"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Process each asset directory
        for asset_dir in self.config["asset_dirs"]:
            asset_path = self.root / asset_dir
            if not asset_path.exists():
                continue

            # Find all PNG files
            for png_file in asset_path.glob("**/*.png"):
                if not self._file_changed(png_file):
                    continue

                print(f"Processing: {png_file.name}")
                cmd = [
                    sys.executable,
                    str(pipeline_script),
                    str(png_file),
                    "-o", str(output_dir),
                    "--platform", platform,
                ]

                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"Asset pipeline error: {result.stderr}")
                    return False

        return True

    def build(self, platform: str, skip_assets: bool = False) -> bool:
        """Build project for specified platform."""
        if not self.validate(platform):
            return False

        plat = PLATFORMS[platform]
        platform_output = self.output_dir / platform
        platform_output.mkdir(parents=True, exist_ok=True)

        print(f"\n{'='*60}")
        print(f"Building {self.config['name']} for {plat.name}")
        print(f"Tier: {plat.tier} | Family: {plat.family}")
        print(f"{'='*60}\n")

        # Process assets
        if not skip_assets:
            print("Processing assets...")
            if not self.process_assets(platform):
                return False

        # For now, just report what would be built
        # Full compilation requires platform-specific toolchain integration
        print(f"\nBuild configuration for {plat.name}:")
        print(f"  Toolchain: {plat.toolchain}")
        print(f"  Assembler: {plat.assembler}")
        print(f"  C Compiler: {plat.c_compiler or 'N/A'}")
        print(f"  Defines: {', '.join(plat.defines)}")
        print(f"  Output: {platform_output / (self.config['name'] + plat.rom_extension)}")

        # Save cache
        self._save_cache()

        print(f"\n✓ Build preparation complete for {plat.name}")
        return True

    def build_all(self, skip_assets: bool = False) -> bool:
        """Build for all configured platforms."""
        success = True
        for platform in self.config["platforms"]:
            if not self.build(platform, skip_assets):
                success = False
        return success


# =============================================================================
# CLI
# =============================================================================

# =============================================================================
# Family Information Display
# =============================================================================

def list_families():
    """Display all CPU families and their platforms."""
    print("\n" + "=" * 60)
    print("ARDK CPU Family Groupings")
    print("=" * 60)

    for family_id, family in FAMILIES.items():
        print(f"\n{family['name'].upper()} Family")
        print("-" * 40)
        print(f"  Word Size: {family['word_size']}-bit")
        print(f"  Endian: {family['endian']}")
        if family['asm_hal']:
            print(f"  ASM HAL: {family['asm_hal']}")

        print(f"\n  Platforms:")
        for plat_id in family['platforms']:
            if plat_id in PLATFORMS:
                p = PLATFORMS[plat_id]
                print(f"    - {p.name:12} (Tier: {p.tier})")
            else:
                print(f"    - {plat_id:12} (not configured)")

    print("\n" + "=" * 60)
    print("Primary Targets: NES (6502), Genesis (68K), Game Boy (Z80)")
    print("=" * 60 + "\n")


def show_migration_paths(source: str):
    """Show migration paths from a source platform."""
    if source not in PLATFORMS:
        print(f"ERROR: Unknown platform '{source}'")
        return

    src = PLATFORMS[source]
    family = FAMILIES.get(src.family)

    print(f"\n" + "=" * 60)
    print(f"Migration Paths from {src.name}")
    print("=" * 60)

    if family:
        print(f"\nSame Family ({family['name']}):")
        for plat_id in family['platforms']:
            if plat_id != source and plat_id in PLATFORMS:
                p = PLATFORMS[plat_id]
                difficulty = "Easy" if p.tier == src.tier else "Moderate"
                print(f"  -> {p.name:12} [{difficulty}] - Shares ASM HAL")

    print(f"\nCross-Family (requires rewrite):")
    for other_fam_id, other_fam in FAMILIES.items():
        if other_fam_id != src.family:
            primary = other_fam['platforms'][0] if other_fam['platforms'] else None
            if primary and primary in PLATFORMS:
                p = PLATFORMS[primary]
                print(f"  -> {p.name:12} [Hard] - Different CPU architecture")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="ARDK Unified Build System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                      Build for default platform
  %(prog)s --platform genesis   Build for Genesis
  %(prog)s --all                Build for all platforms
  %(prog)s --clean              Clean all build artifacts
  %(prog)s --validate           Validate without building
  %(prog)s --list-families      Show CPU family groupings
  %(prog)s --migration nes      Show migration paths from NES
        """
    )

    parser.add_argument(
        "--platform", "-p",
        choices=list(PLATFORMS.keys()),
        help="Target platform"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Build for all configured platforms"
    )
    parser.add_argument(
        "--clean", "-c",
        action="store_true",
        help="Clean build artifacts"
    )
    parser.add_argument(
        "--validate", "-v",
        action="store_true",
        help="Validate configuration without building"
    )
    parser.add_argument(
        "--skip-assets",
        action="store_true",
        help="Skip asset processing"
    )
    parser.add_argument(
        "--project", "-P",
        type=Path,
        default=Path.cwd(),
        help="Project root directory"
    )
    parser.add_argument(
        "--list-families", "-l",
        action="store_true",
        help="List all CPU families and platforms"
    )
    parser.add_argument(
        "--migration", "-m",
        type=str,
        metavar="PLATFORM",
        help="Show migration paths from specified platform"
    )

    args = parser.parse_args()

    # Handle family info commands first (no project needed)
    if args.list_families:
        list_families()
        return 0

    if args.migration:
        show_migration_paths(args.migration)
        return 0

    # Find project root (look for ardk_project.json or src/hal)
    project_root = args.project.resolve()
    if not (project_root / "src" / "hal").exists():
        # Try parent directories
        for parent in project_root.parents:
            if (parent / "src" / "hal").exists():
                project_root = parent
                break

    # Load config
    config = load_project_config(project_root)
    builder = ARDKBuilder(project_root, config)

    # Execute command
    if args.clean:
        builder.clean(args.platform)
        return 0

    if args.validate:
        platform = args.platform or config["default_platform"]
        return 0 if builder.validate(platform) else 1

    if args.all:
        return 0 if builder.build_all(args.skip_assets) else 1

    platform = args.platform or config["default_platform"]
    return 0 if builder.build(platform, args.skip_assets) else 1


if __name__ == "__main__":
    sys.exit(main())
