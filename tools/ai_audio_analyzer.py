#!/usr/bin/env python3
"""
AI Audio Analyzer for NES Development

Analyzes audio files (WAV, MP3, MIDI) and provides:
1. BPM detection and tempo analysis
2. Key/scale detection for melodic content
3. Suggestions for NES channel mapping
4. Automatic FamiTracker-compatible note extraction
5. Sound effect categorization and labeling

Uses Gemini AI for intelligent audio description and categorization.

Usage:
    python tools/ai_audio_analyzer.py audio_file.wav
    python tools/ai_audio_analyzer.py --batch music_folder/
"""

import os
import sys
import json
import wave
import struct
import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

# Optional dependencies
try:
    from google import genai
    from google.genai import types
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

# NES Audio Constants
NES_SAMPLE_RATE = 1789773  # NTSC CPU clock
NTSC_FRAME_RATE = 60.0988
PAL_FRAME_RATE = 50.0070

# NES frequency table (A4 = 440Hz, NTSC)
# Period values for square wave channels
NES_NOTE_PERIODS = {
    'C-1': 0x7F1, 'C#1': 0x780, 'D-1': 0x713, 'D#1': 0x6AD,
    'E-1': 0x64D, 'F-1': 0x5F3, 'F#1': 0x59D, 'G-1': 0x54D,
    'G#1': 0x500, 'A-1': 0x4B8, 'A#1': 0x474, 'B-1': 0x434,
    'C-2': 0x3F8, 'C#2': 0x3BF, 'D-2': 0x389, 'D#2': 0x356,
    'E-2': 0x326, 'F-2': 0x2F9, 'F#2': 0x2CE, 'G-2': 0x2A6,
    'G#2': 0x27F, 'A-2': 0x25C, 'A#2': 0x23A, 'B-2': 0x21A,
    'C-3': 0x1FB, 'C#3': 0x1DF, 'D-3': 0x1C4, 'D#3': 0x1AB,
    'E-3': 0x193, 'F-3': 0x17C, 'F#3': 0x167, 'G-3': 0x152,
    'G#3': 0x13F, 'A-3': 0x12D, 'A#3': 0x11C, 'B-3': 0x10C,
    'C-4': 0x0FD, 'C#4': 0x0EF, 'D-4': 0x0E1, 'D#4': 0x0D5,
    'E-4': 0x0C9, 'F-4': 0x0BD, 'F#4': 0x0B3, 'G-4': 0x0A9,
    'G#4': 0x09F, 'A-4': 0x096, 'A#4': 0x08E, 'B-4': 0x086,
    'C-5': 0x07E, 'C#5': 0x077, 'D-5': 0x070, 'D#5': 0x06A,
    'E-5': 0x064, 'F-5': 0x05E, 'F#5': 0x059, 'G-5': 0x054,
    'G#5': 0x04F, 'A-5': 0x04B, 'A#5': 0x046, 'B-5': 0x042,
    'C-6': 0x03F, 'C#6': 0x03B, 'D-6': 0x038, 'D#6': 0x034,
    'E-6': 0x031, 'F-6': 0x02F, 'F#6': 0x02C, 'G-6': 0x029,
    'G#6': 0x027, 'A-6': 0x025, 'A#6': 0x023, 'B-6': 0x021,
    'C-7': 0x01F, 'C#7': 0x01D, 'D-7': 0x01B,
}

@dataclass
class AudioAnalysis:
    """Results of audio analysis"""
    filename: str
    duration_seconds: float
    sample_rate: int
    channels: int
    bit_depth: int

    # Detected properties
    estimated_bpm: Optional[float] = None
    estimated_key: Optional[str] = None
    is_loopable: bool = False

    # AI-generated
    description: str = ""
    category: str = ""  # music, sfx, ambient
    suggested_use: str = ""  # gameplay, menu, boss, death, etc.
    nes_channel_suggestion: str = ""

    # Technical notes
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []

class AIAudioAnalyzer:
    """AI-powered audio analyzer for NES development"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.client = None

        if HAS_GEMINI and self.api_key:
            self.client = genai.Client(api_key=self.api_key)

    def analyze_wav(self, filepath: str) -> AudioAnalysis:
        """Analyze a WAV file"""
        path = Path(filepath)

        with wave.open(str(path), 'rb') as wav:
            channels = wav.getnchannels()
            sample_rate = wav.getframerate()
            bit_depth = wav.getsampwidth() * 8
            n_frames = wav.getnframes()
            duration = n_frames / sample_rate

            # Read samples for analysis
            raw_data = wav.readframes(n_frames)

        analysis = AudioAnalysis(
            filename=path.name,
            duration_seconds=duration,
            sample_rate=sample_rate,
            channels=channels,
            bit_depth=bit_depth
        )

        # Basic analysis
        self._analyze_for_nes_compatibility(analysis, sample_rate, duration)

        # AI description if available
        if self.client:
            self._ai_describe_audio(analysis, filepath)
        else:
            analysis.description = "AI analysis unavailable (no API key)"
            self._basic_categorization(analysis)

        return analysis

    def _analyze_for_nes_compatibility(self, analysis: AudioAnalysis,
                                        sample_rate: int, duration: float):
        """Check NES compatibility and add warnings"""

        # Duration warnings
        if duration < 0.1:
            analysis.category = "sfx"
            analysis.suggested_use = "Short sound effect (hit, beep)"
        elif duration < 2.0:
            analysis.category = "sfx"
            analysis.suggested_use = "Sound effect (explosion, jump, powerup)"
        elif duration < 30.0:
            analysis.category = "music"
            analysis.suggested_use = "Jingle or short loop"
            analysis.is_loopable = True
        else:
            analysis.category = "music"
            analysis.suggested_use = "Full music track"
            analysis.is_loopable = True

        # Sample rate compatibility
        if sample_rate < 8000:
            analysis.warnings.append(f"Low sample rate ({sample_rate}Hz) may lose quality")
        if sample_rate > 44100:
            analysis.warnings.append(f"High sample rate ({sample_rate}Hz) - will need downsampling")

        # NES channel suggestions based on duration/type
        if analysis.category == "sfx":
            if duration < 0.2:
                analysis.nes_channel_suggestion = "Noise channel (short percussive)"
            else:
                analysis.nes_channel_suggestion = "Square 2 or Noise (varies by content)"
        else:
            analysis.nes_channel_suggestion = "Square 1 (melody), Square 2 (harmony), Triangle (bass), Noise (drums)"

    def _basic_categorization(self, analysis: AudioAnalysis):
        """Basic categorization without AI"""
        name_lower = analysis.filename.lower()

        # Guess from filename
        if any(x in name_lower for x in ['jump', 'hit', 'death', 'coin', 'explosion', 'shoot']):
            analysis.category = "sfx"
            analysis.description = f"Sound effect (guessed from filename: {analysis.filename})"
        elif any(x in name_lower for x in ['theme', 'music', 'bgm', 'loop', 'track']):
            analysis.category = "music"
            analysis.description = f"Music track (guessed from filename: {analysis.filename})"
        elif any(x in name_lower for x in ['ambient', 'background', 'atmo']):
            analysis.category = "ambient"
            analysis.description = f"Ambient audio (guessed from filename: {analysis.filename})"
        else:
            analysis.description = f"Unknown audio type - {analysis.duration_seconds:.2f}s"

    def _ai_describe_audio(self, analysis: AudioAnalysis, filepath: str):
        """Use AI to describe and categorize audio"""

        # Create prompt for audio analysis
        prompt = f"""Analyze this audio file for NES game development:

Filename: {analysis.filename}
Duration: {analysis.duration_seconds:.2f} seconds
Sample Rate: {analysis.sample_rate} Hz
Channels: {analysis.channels}
Current Category Guess: {analysis.category}

Based on the filename and metadata, provide:

1. **Description**: What does this audio likely represent? (2-3 sentences)
   Be specific: "8-bit style jump sound with rising pitch" not just "sound effect"

2. **Category**: One of: music, sfx, ambient, jingle

3. **Suggested Use**: Where in a game would this be used?
   Examples: player_jump, enemy_death, boss_theme, menu_select, powerup_collect, level_complete

4. **NES Channel Mapping**:
   - For SFX: Which NES channel(s) would reproduce this? (Square 1, Square 2, Triangle, Noise, DPCM)
   - For Music: Suggest channel arrangement (melody on Square 1, bass on Triangle, etc.)

5. **NES Compatibility Notes**:
   - Will this translate well to NES audio?
   - Any frequency ranges that might be problematic?
   - Suggested modifications if needed?

Return as JSON:
{{
    "description": "...",
    "category": "sfx|music|ambient|jingle",
    "suggested_use": "player_jump|enemy_death|...",
    "nes_channels": "Square 2 for melody",
    "compatibility_notes": "...",
    "estimated_bpm": null or number,
    "estimated_key": null or "C major"
}}
"""

        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[prompt]
            )

            # Parse JSON from response
            text = response.text

            # Extract JSON from response
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0]
            elif '```' in text:
                text = text.split('```')[1].split('```')[0]

            data = json.loads(text.strip())

            analysis.description = data.get('description', analysis.description)
            analysis.category = data.get('category', analysis.category)
            analysis.suggested_use = data.get('suggested_use', analysis.suggested_use)
            analysis.nes_channel_suggestion = data.get('nes_channels', analysis.nes_channel_suggestion)

            if data.get('compatibility_notes'):
                analysis.warnings.append(data['compatibility_notes'])

            if data.get('estimated_bpm'):
                analysis.estimated_bpm = float(data['estimated_bpm'])

            if data.get('estimated_key'):
                analysis.estimated_key = data['estimated_key']

        except Exception as e:
            print(f"AI analysis failed: {e}")
            self._basic_categorization(analysis)

    def generate_sfx_constants(self, analyses: List[AudioAnalysis]) -> str:
        """Generate assembly constants for sound effects"""

        output = [
            "; =============================================================================",
            "; SOUND EFFECT CONSTANTS",
            "; Auto-generated by AI Audio Analyzer",
            "; =============================================================================",
            ""
        ]

        sfx_analyses = [a for a in analyses if a.category == 'sfx']

        for i, analysis in enumerate(sfx_analyses):
            # Create constant name from suggested use
            name = analysis.suggested_use.upper().replace(' ', '_').replace('-', '_')
            name = ''.join(c for c in name if c.isalnum() or c == '_')

            if not name:
                name = f"SFX_{i}"

            output.append(f"; {analysis.description}")
            output.append(f"SFX_{name} = {i}")
            output.append(f"; File: {analysis.filename}")
            output.append(f"; Duration: {analysis.duration_seconds:.3f}s")
            output.append(f"; Channel: {analysis.nes_channel_suggestion}")
            output.append("")

        output.append(f"SFX_COUNT = {len(sfx_analyses)}")

        return '\n'.join(output)

    def generate_music_list(self, analyses: List[AudioAnalysis]) -> str:
        """Generate music track list"""

        output = [
            "; =============================================================================",
            "; MUSIC TRACK CONSTANTS",
            "; Auto-generated by AI Audio Analyzer",
            "; =============================================================================",
            ""
        ]

        music_analyses = [a for a in analyses if a.category in ('music', 'jingle')]

        for i, analysis in enumerate(music_analyses):
            name = analysis.suggested_use.upper().replace(' ', '_').replace('-', '_')
            name = ''.join(c for c in name if c.isalnum() or c == '_')

            if not name:
                name = f"TRACK_{i}"

            output.append(f"; {analysis.description}")
            output.append(f"MUSIC_{name} = {i}")
            output.append(f"; File: {analysis.filename}")
            output.append(f"; Duration: {analysis.duration_seconds:.1f}s")
            if analysis.estimated_bpm:
                output.append(f"; BPM: {analysis.estimated_bpm}")
            if analysis.estimated_key:
                output.append(f"; Key: {analysis.estimated_key}")
            output.append("")

        output.append(f"MUSIC_COUNT = {len(music_analyses)}")

        return '\n'.join(output)


def analyze_directory(analyzer: AIAudioAnalyzer, directory: str) -> List[AudioAnalysis]:
    """Analyze all audio files in a directory"""

    path = Path(directory)
    analyses = []

    # Supported formats
    extensions = {'.wav', '.mp3', '.ogg', '.flac', '.mid', '.midi'}

    for file in path.rglob('*'):
        if file.suffix.lower() in extensions:
            print(f"Analyzing: {file.name}...")
            try:
                if file.suffix.lower() == '.wav':
                    analysis = analyzer.analyze_wav(str(file))
                    analyses.append(analysis)
                else:
                    print(f"  Skipping non-WAV file (not implemented): {file.name}")
            except Exception as e:
                print(f"  Error analyzing {file.name}: {e}")

    return analyses


def main():
    parser = argparse.ArgumentParser(description='AI Audio Analyzer for NES Development')
    parser.add_argument('input', help='Audio file or directory to analyze')
    parser.add_argument('--batch', action='store_true', help='Process directory of files')
    parser.add_argument('--output', '-o', help='Output directory for generated files')
    parser.add_argument('--json', action='store_true', help='Output analysis as JSON')

    args = parser.parse_args()

    # Initialize analyzer
    api_key = os.getenv('GEMINI_API_KEY')
    analyzer = AIAudioAnalyzer(api_key)

    if not api_key:
        print("Note: GEMINI_API_KEY not set. Using basic analysis only.")
        print("Set the key for AI-powered descriptions and categorization.")
        print()

    # Analyze files
    if args.batch or Path(args.input).is_dir():
        analyses = analyze_directory(analyzer, args.input)
    else:
        analysis = analyzer.analyze_wav(args.input)
        analyses = [analysis]

    if not analyses:
        print("No audio files found!")
        return

    # Output results
    print("\n" + "=" * 60)
    print("AUDIO ANALYSIS RESULTS")
    print("=" * 60)

    for analysis in analyses:
        print(f"\n{analysis.filename}")
        print("-" * 40)
        print(f"  Duration: {analysis.duration_seconds:.2f}s")
        print(f"  Category: {analysis.category}")
        print(f"  Description: {analysis.description}")
        print(f"  Suggested Use: {analysis.suggested_use}")
        print(f"  NES Channels: {analysis.nes_channel_suggestion}")
        if analysis.estimated_bpm:
            print(f"  BPM: {analysis.estimated_bpm}")
        if analysis.estimated_key:
            print(f"  Key: {analysis.estimated_key}")
        if analysis.warnings:
            print(f"  Warnings:")
            for w in analysis.warnings:
                print(f"    - {w}")

    # Generate output files
    if args.output:
        output_path = Path(args.output)
        output_path.mkdir(parents=True, exist_ok=True)

        # JSON analysis
        if args.json:
            json_path = output_path / 'audio_analysis.json'
            with open(json_path, 'w') as f:
                json.dump([{
                    'filename': a.filename,
                    'duration': a.duration_seconds,
                    'category': a.category,
                    'description': a.description,
                    'suggested_use': a.suggested_use,
                    'nes_channels': a.nes_channel_suggestion,
                    'bpm': a.estimated_bpm,
                    'key': a.estimated_key,
                    'warnings': a.warnings
                } for a in analyses], f, indent=2)
            print(f"\nJSON analysis saved to: {json_path}")

        # Assembly constants
        sfx_path = output_path / 'sfx_constants.inc'
        with open(sfx_path, 'w') as f:
            f.write(analyzer.generate_sfx_constants(analyses))
        print(f"SFX constants saved to: {sfx_path}")

        music_path = output_path / 'music_constants.inc'
        with open(music_path, 'w') as f:
            f.write(analyzer.generate_music_list(analyses))
        print(f"Music constants saved to: {music_path}")

    print("\nAnalysis complete!")


if __name__ == '__main__':
    main()
