import os
import json
import hashlib
import time
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any
from abc import ABC, abstractmethod
from PIL import Image

from .platforms import PLATFORM_SPECS, PlatformConfig, BoundingBox, SpriteInfo, CollisionMask

# =============================================================================
# AI GENERATION PROVIDERS (Phase 3.6)
# =============================================================================
# Unified generation interface supporting multiple AI backends with fallback.
# Used by GenerativeResizer for sprite variants and AIAnimationGenerator for animations.
#
# Available providers:
#   - pollinations: Free, 30+ models, animation support (default)
#   - pixie_haus: Pixel-perfect, palette constraints (requires PIXIE_HAUS_API_KEY)
#   - sd_local: Local Stable Diffusion WebUI (requires http://127.0.0.1:7860)
#
# Fallback order: pollinations -> pixie_haus -> sd_local
# =============================================================================
try:
    from .ai_providers import (
        get_generation_provider,
        generate_with_fallback,
        GenerationConfig,
        GenerationResult,
        NoProvidersAvailableError,
    )
    AI_PROVIDERS_AVAILABLE = True
except ImportError:
    AI_PROVIDERS_AVAILABLE = False

# =============================================================================
# AI PROVIDER ABSTRACTION (Vision/Analysis)
# =============================================================================

class AIProvider(ABC):
    """Abstract base class for AI providers"""

    @abstractmethod
    def analyze_sprites(self, img: Image.Image, sprite_count: int,
                       sprite_positions: List[Dict]) -> Dict[str, Any]:
        """Analyze sprite sheet and return semantic labels"""
        pass

    def analyze_prompt(self, img: Image.Image, prompt: str) -> Dict[str, Any]:
        """Generic analysis with custom prompt (optional implement)"""
        return {}

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def available(self) -> bool:
        pass


class GeminiProvider(AIProvider):
    """Google Gemini AI provider"""

    def __init__(self):
        self._client = None
        self._available = False
        self._init()

    def _init(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return

        try:
            from google import genai
            self._client = genai.Client(api_key=api_key)
            self._available = True
        except ImportError:
            print("      [WARN] google-genai not installed")
        except Exception as e:
            print(f"      [WARN] Gemini init failed: {e}")

    @property
    def name(self) -> str:
        return "Gemini"

    @property
    def available(self) -> bool:
        return self._available

    def analyze_sprites(self, img: Image.Image, sprite_count: int,
                       sprite_positions: List[Dict]) -> Dict[str, Any]:
        if not self._available:
            return {}

        from google.genai import types
        import tempfile

        positions_text = "\\n".join([
            f"  Sprite {p['id']}: at ({p['x']}, {p['y']}), size {p['w']}x{p['h']}"
            for p in sprite_positions
        ])

        prompt = f"""Analyze this sprite sheet for "NEON SURVIVORS", a synthwave/cyberpunk NES game.

I detected {sprite_count} sprites at these positions:
{positions_text}

For EACH sprite, identify:
1. type: player, enemy, boss, item, projectile, vfx, ui
2. action: idle, walk, run, jump, attack, hurt, die, shoot
3. description: Short description like "synthwave_hero_idle" or "glitch_enemy_run"

Return JSON ONLY (no markdown):
{{"sprites": [
  {{"id": 1, "type": "player", "action": "idle", "description": "synthwave_hero_idle"}},
  {{"id": 2, "type": "player", "action": "run", "description": "synthwave_hero_run"}}
]}}

Use snake_case for descriptions. Match IDs to my sprite numbers."""

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            img.save(tmp.name)
            tmp_path = tmp.name

        try:
            with open(tmp_path, 'rb') as f:
                image_bytes = f.read()

            image_part = types.Part.from_bytes(data=image_bytes, mime_type='image/png')

            response = self._client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[prompt, image_part]
            )

            text = response.text.strip()
            # Clean up response
            if '```' in text:
                text = text.split('```')[1]
                if text.startswith('json'):
                    text = text[4:]
                text = text.strip()

            return json.loads(text)

        except Exception as e:
            error_str = str(e)
            if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str:
                print(f"      [RATE LIMIT] Gemini quota exceeded")
            else:
                print(f"      [ERROR] Gemini: {e}")
            return {}
        finally:
            os.unlink(tmp_path)


class OpenAIProvider(AIProvider):
    """OpenAI GPT-4 Vision provider"""

    def __init__(self):
        self._client = None
        self._available = False
        self._init()

    def _init(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return

        try:
            import openai
            self._client = openai.OpenAI(api_key=api_key)
            self._available = True
        except ImportError:
            pass
        except Exception as e:
            print(f"      [WARN] OpenAI init failed: {e}")

    @property
    def name(self) -> str:
        return "OpenAI"

    @property
    def available(self) -> bool:
        return self._available

    def analyze_sprites(self, img: Image.Image, sprite_count: int,
                       sprite_positions: List[Dict]) -> Dict[str, Any]:
        if not self._available:
            return {}

        import base64
        from io import BytesIO

        # Convert image to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_b64 = base64.b64encode(buffer.getvalue()).decode()

        positions_text = "\\n".join([
            f"  Sprite {p['id']}: at ({p['x']}, {p['y']}), size {p['w']}x{p['h']}"
            for p in sprite_positions
        ])

        prompt = f"""Analyze this sprite sheet for "NEON SURVIVORS", a synthwave NES game.

Detected {sprite_count} sprites:
{positions_text}

Return JSON with sprite labels:
{{"sprites": [{{"id": 1, "type": "player", "action": "idle", "description": "synthwave_hero_idle"}}]}}"""

        try:
            response = self._client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
                    ]
                }],
                max_tokens=1000
            )

            text = response.choices[0].message.content.strip()
            if '```' in text:
                text = text.split('```')[1].replace('json', '').strip()

            return json.loads(text)

        except Exception as e:
            print(f"      [ERROR] OpenAI: {e}")
            return {}


class AnthropicProvider(AIProvider):
    """Anthropic Claude provider"""

    def __init__(self):
        self._client = None
        self._available = False
        self._init()

    def _init(self):
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            return

        try:
            import anthropic
            self._client = anthropic.Anthropic(api_key=api_key)
            self._available = True
        except ImportError:
            pass
        except Exception as e:
            print(f"      [WARN] Anthropic init failed: {e}")

    @property
    def name(self) -> str:
        return "Anthropic"

    @property
    def available(self) -> bool:
        return self._available

    def analyze_sprites(self, img: Image.Image, sprite_count: int,
                       sprite_positions: List[Dict]) -> Dict[str, Any]:
        if not self._available:
            return {}

        import base64
        from io import BytesIO

        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_b64 = base64.b64encode(buffer.getvalue()).decode()

        positions_text = "\\n".join([
            f"  Sprite {p['id']}: at ({p['x']}, {p['y']}), size {p['w']}x{p['h']}"
            for p in sprite_positions
        ])

        prompt = f"""Analyze this sprite sheet for "NEON SURVIVORS", a synthwave NES game.

Detected {sprite_count} sprites:
{positions_text}

Return JSON only:
{{"sprites": [{{"id": 1, "type": "player", "action": "idle", "description": "synthwave_hero_idle"}}]}}"""

        try:
            response = self._client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img_b64}},
                        {"type": "text", "text": prompt}
                    ]
                }]
            )

            text = response.content[0].text.strip()
            if '```' in text:
                text = text.split('```')[1].replace('json', '').strip()

            return json.loads(text)

        except Exception as e:
            print(f"      [ERROR] Anthropic: {e}")
            return {}


class GroqProvider(AIProvider):
    """Groq - Ultra-fast inference with Llama 4 vision models"""

    def __init__(self):
        self._client = None
        self._available = False
        self._init()

    def _init(self):
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            return

        try:
            from groq import Groq
            self._client = Groq(api_key=api_key)
            self._available = True
        except ImportError:
            pass
        except Exception as e:
            print(f"      [WARN] Groq init failed: {e}")

    @property
    def name(self) -> str:
        return "Groq"

    @property
    def available(self) -> bool:
        return self._available

    def analyze_sprites(self, img: Image.Image, sprite_count: int,
                       sprite_positions: List[Dict]) -> Dict[str, Any]:
        if not self._available:
            return {}

        import base64
        from io import BytesIO

        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_b64 = base64.b64encode(buffer.getvalue()).decode()

        positions_text = "\\n".join([
            f"  Sprite {p['id']}: at ({p['x']}, {p['y']}), size {p['w']}x{p['h']}"
            for p in sprite_positions
        ])

        prompt = f"""Analyze this sprite sheet for "NEON SURVIVORS", a synthwave NES game.

Detected {sprite_count} sprites:
{positions_text}

Return JSON only (no markdown):
{{"sprites": [{{"id": 1, "type": "player", "action": "idle", "description": "synthwave_hero_idle"}}]}}"""

        try:
            response = self._client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
                    ]
                }],
                temperature=0.7,
                max_completion_tokens=1024
            )

            text = response.choices[0].message.content.strip()
            if '```' in text:
                text = text.split('```')[1].replace('json', '').strip()

            return json.loads(text)

        except Exception as e:
            error_str = str(e)
            if '429' in error_str or 'rate' in error_str.lower():
                print(f"      [RATE LIMIT] Groq quota exceeded")
            else:
                print(f"      [ERROR] Groq: {e}")
            return {}


class GrokProvider(AIProvider):
    """xAI Grok - Vision models with X platform integration"""

    def __init__(self):
        self._client = None
        self._available = False
        self._init()

    def _init(self):
        api_key = os.getenv('XAI_API_KEY')
        if not api_key:
            return

        try:
            import openai
            # xAI uses OpenAI-compatible API
            self._client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.x.ai/v1"
            )
            self._available = True
        except ImportError:
            pass
        except Exception as e:
            print(f"      [WARN] Grok/xAI init failed: {e}")

    @property
    def name(self) -> str:
        return "Grok"

    @property
    def available(self) -> bool:
        return self._available

    def analyze_sprites(self, img: Image.Image, sprite_count: int,
                       sprite_positions: List[Dict]) -> Dict[str, Any]:
        if not self._available:
            return {}

        import base64
        from io import BytesIO

        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_b64 = base64.b64encode(buffer.getvalue()).decode()

        positions_text = "\\n".join([
            f"  Sprite {p['id']}: at ({p['x']}, {p['y']}), size {p['w']}x{p['h']}"
            for p in sprite_positions
        ])

        prompt = f"""Analyze this sprite sheet for "NEON SURVIVORS", a synthwave NES game.

Detected {sprite_count} sprites:
{positions_text}

Return JSON only (no markdown):
{{"sprites": [{{"id": 1, "type": "player", "action": "idle", "description": "synthwave_hero_idle"}}]}}"""

        try:
            response = self._client.chat.completions.create(
                model="grok-2-vision-1212",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
                    ]
                }],
                max_tokens=1000
            )

            text = response.choices[0].message.content.strip()
            if '```' in text:
                text = text.split('```')[1].replace('json', '').strip()

            return json.loads(text)

        except Exception as e:
            print(f"      [ERROR] Grok: {e}")
            return {}


class PollinationsProvider(AIProvider):
    """Pollinations.ai - 30+ models including GPT-5, Gemini, Claude via unified API"""

    def __init__(self, api_key: str = None, model: str = "openai"):
        # Try direct key, then environment variable
        self._api_key = api_key or os.getenv('POLLINATIONS_API_KEY')
        self._available = bool(self._api_key)
        self._model = model  # openai, openai-large, claude-hybridspace, gemini, etc.

    @property
    def name(self) -> str:
        return "Pollinations"

    @property
    def available(self) -> bool:
        return self._available

    def _extract_json(self, text: str) -> Dict:
        """Extract JSON from potentially messy AI response"""
        import re

        # Try direct parse first
        try:
            return json.loads(text)
        except:
            pass

        # Remove markdown code blocks
        if '```' in text:
            parts = text.split('```')
            for part in parts:
                part = part.strip()
                if part.startswith('json'):
                    part = part[4:].strip()
                if part.startswith('{'):
                    try:
                        return json.loads(part)
                    except:
                        pass

        # Find JSON object in text
        match = re.search(r'\{[\s\S]*"sprites"[\s\S]*\}', text)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass

        # Try to fix common issues
        text = text.strip()
        if text.startswith('{') and text.endswith('}'):
            # Fix trailing commas
            text = re.sub(r',(\s*[}\]])', r'\1', text)
            try:
                return json.loads(text)
            except:
                pass

        return {}

    def analyze_sprites(self, img: Image.Image, sprite_count: int,
                       sprite_positions: List[Dict]) -> Dict[str, Any]:
        import base64
        from io import BytesIO
        import urllib.request
        import urllib.error

        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_b64 = base64.b64encode(buffer.getvalue()).decode()

        # Limit positions to avoid token limits
        positions_text = "\\n".join([
            f"  Sprite {p['id']}: at ({p['x']}, {p['y']}), size {p['w']}x{p['h']}"
            for p in sprite_positions[:10]  # Limit to first 10
        ])
        if len(sprite_positions) > 10:
            positions_text += f"\\n  ... and {len(sprite_positions) - 10} more sprites"

        prompt = f"""Analyze this sprite sheet for "NEON SURVIVORS", a synthwave NES game.

Detected {sprite_count} sprites (showing first 10):
{positions_text}

For each sprite, identify type (player/enemy/item/vfx), action (idle/run/attack), and frame index if part of an animation.

Return ONLY valid JSON, no explanation:
{{"sprites": [{{"id": 1, "type": "player", "action": "idle", "frame_index": 1, "description": "hero_idle_1"}}]}}"""

        payload = {
            "model": self._model,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
                ]
            }]
        }

        return self._call_api(payload)

    def analyze_prompt(self, img: Image.Image, prompt: str) -> Dict[str, Any]:
        """Generic analysis with custom prompt"""
        import base64
        from io import BytesIO

        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_b64 = base64.b64encode(buffer.getvalue()).decode()

        payload = {
            "model": self._model,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
                ]
            }]
        }

        text = self._call_api(payload, raw_response=True)
        return self._extract_json(text)

    def analyze_palette(self, img: Image.Image, nes_colors_desc: str, num_colors: int = 4) -> Optional[List[int]]:
        """Use vision to analyze image and suggest optimal NES palette"""
        import base64
        from io import BytesIO

        buffer = BytesIO()
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.save(buffer, format='JPEG', quality=85)
        img_b64 = base64.b64encode(buffer.getvalue()).decode()

        prompt = f"""Look at this image and pick {num_colors} NES colors that match it best.
Return JSON only: {{"palette": ["$XX", "$XX", "$XX", "$XX"], "reason": "brief"}}

Available NES colors:
{nes_colors_desc}

Pick dark to light: first should be black/dark for shadows, last should be brightest."""

        payload = {
            "model": self._model,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                ]
            }],
            "max_tokens": 500
        }

        result = self._call_api(payload, raw_response=True)
        if result:
            # Parse palette from response
            import re
            json_match = re.search(r'\{[^}]+\}', result)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                    if 'palette' in data:
                        palette = []
                        for color_str in data['palette']:
                            hex_val = color_str.replace('$', '').replace('0x', '')
                            palette.append(int(hex_val, 16))
                        if len(palette) == num_colors:
                            reason = data.get('reason', 'AI selected')
                            print(f"      [Pollinations] Palette: {', '.join(f'${c:02X}' for c in palette)}")
                            print(f"      [Pollinations] Reason: {reason}")
                            return palette
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"      [Pollinations] Failed to parse palette: {e}")
        return None

    def _call_api(self, payload: dict, raw_response: bool = False):
        """Make API call to Pollinations"""
        import urllib.request
        import urllib.error

        try:
            headers = {'Content-Type': 'application/json'}
            if self._api_key:
                headers['Authorization'] = f'Bearer {self._api_key}'

            req = urllib.request.Request(
                "https://gen.pollinations.ai/v1/chat/completions",
                data=json.dumps(payload).encode('utf-8'),
                headers=headers,
                method='POST'
            )

            print(f"      [Pollinations] Requesting {payload.get('model')}...")
            with urllib.request.urlopen(req, timeout=90) as response:
                result = json.loads(response.read().decode('utf-8'))
                print(f"      [Pollinations] Response received ({len(str(result))} bytes)")

            text = result.get('choices', [{}])[0].get('message', {}).get('content', '').strip()

            if raw_response:
                return text

            parsed = self._extract_json(text)
            if parsed and parsed.get('sprites'):
                return parsed

            return {}

        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"      [RATE LIMIT] Pollinations rate limited")
            else:
                print(f"      [ERROR] Pollinations HTTP {e.code}: {e.reason}")
            return {} if not raw_response else None
        except Exception as e:
            print(f"      [ERROR] Pollinations: {e}")
            return {}

class GenerativeResizer:
    """
    AI-powered asset generator that creates platform-specific variants.

    Acts as a SOURCE GENERATOR. Output must be processed by SpriteConverter
    to ensure platform compliance (palette quantization, tile alignment, etc.).

    Uses ai_providers module for generation with automatic fallback:
    - Pollinations (free, default) -> Pixie.haus (paid) -> SD Local (free)

    For animation generation, use AIAnimationGenerator instead.

    Usage:
        >>> analyzer = AIAnalyzer()
        >>> resizer = GenerativeResizer("genesis", analyzer)
        >>> resizer.generate_variant("input.png", "output.png")
    """
    def __init__(self, platform_name: str, analyzer: 'AIAnalyzer'):
        self.platform = platform_name
        self.analyzer = analyzer
        self.specs = PLATFORM_SPECS.get(platform_name, {})
        self.prompt_template = self.specs.get("ai_prompt", "Pixel art style")
        
    def generate_variant(self, input_path: str, output_path: str,
                         preferred_provider: str = None) -> bool:
        """
        Generates a variant of the input image using AI style transfer/img2img.

        Uses a fallback chain of providers:
        1. Pollinations (default, free)
        2. Pixie.haus (pixel-perfect, requires API key)
        3. Stable Diffusion Local (free, requires local WebUI)

        Args:
            input_path: Path to source image
            output_path: Path to save generated image
            preferred_provider: Override default provider order ('pollinations', 'pixie_haus', 'sd_local')
        """
        if not self.specs:
            print(f"      [Generative] No specs found for {self.platform}, skipping generation.")
            return False

        print(f"      [Generative] Analyzing input for semantic context...")
        # 1. Analyze Input (using existing Vision capability)
        description = self.analyzer.analyze_image(input_path, "Describe this sprite's character and action in 10 words.")
        if not description:
            description = "A retro game character"

        # 2. Construct Prompt
        full_prompt = f"{self.prompt_template}. Subject: {description}. Ensure sprites are centered and grid-aligned."
        print(f"      [Generative] Prompt: {full_prompt}")

        width = self.specs["resolution"]["width"]
        height = self.specs["resolution"]["height"]
        seed = 42

        # 3. Try generation with fallback chain
        # First try Pollinations URL (primary, always available)
        if preferred_provider is None or preferred_provider == 'pollinations':
            if self._try_pollinations_generation(full_prompt, width, height, seed, output_path):
                return True
            print(f"      [Generative] Pollinations failed, trying fallback providers...")

        # 4. Fallback to ai_providers registry
        if AI_PROVIDERS_AVAILABLE:
            return self._try_provider_fallback(
                full_prompt, width, height, seed, output_path,
                preferred_provider
            )
        else:
            print(f"      [Generative] No fallback providers available")
            return False

    def _try_pollinations_generation(self, prompt: str, width: int, height: int,
                                      seed: int, output_path: str) -> bool:
        """Try generation via Pollinations URL endpoint."""
        import urllib.request
        import urllib.parse

        try:
            encoded_prompt = urllib.parse.quote(prompt)
            image_url = f"https://gen.pollinations.ai/image/{encoded_prompt}?width={width}&height={height}&seed={seed}&model=flux"

            print(f"      [Generative] Requesting from Pollinations...")

            req = urllib.request.Request(image_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=60) as response:
                data = response.read()

            with open(output_path, 'wb') as f:
                f.write(data)

            print(f"      [Generative] Success via Pollinations! Saved to {output_path}")
            return True

        except Exception as e:
            print(f"      [Generative] Pollinations error: {e}")
            return False

    def _try_provider_fallback(self, prompt: str, width: int, height: int,
                                seed: int, output_path: str,
                                preferred: str = None) -> bool:
        """Try generation via ai_providers fallback chain."""
        try:
            # Build config for the generation
            config = GenerationConfig(
                width=width,
                height=height,
                seed=seed,
                platform=self.platform,
                max_colors=self.specs.get("max_colors", 16),
            )

            # Use fallback chain
            result = generate_with_fallback(
                prompt=prompt,
                config=config,
                preferred=preferred
            )

            if result.success and result.image:
                # Save the generated image
                result.image.save(output_path)
                print(f"      [Generative] Success via {result.provider}! Saved to {output_path}")
                if result.warnings:
                    for w in result.warnings:
                        print(f"      [Generative] Warning: {w}")
                return True
            else:
                errors = result.errors or ["Unknown error"]
                print(f"      [Generative] Fallback chain failed: {', '.join(errors)}")
                return False

        except NoProvidersAvailableError as e:
            print(f"      [Generative] No providers available: {e}")
            return False
        except Exception as e:
            print(f"      [Generative] Fallback error: {e}")
            return False

    def simplify_for_tiling(self, input_path: str, output_path: str, max_tiles: int) -> bool:
        """
        AI Fallback: Simplify image to reduce unique tile count.
        Asks AI to reduce high-frequency noise and enforce repetitive patterns.
        """
        if not self.specs:
             return False
             
        try:
            # 1. Analyze (Briefly)
            desc = self.analyzer.analyze_image(input_path, "Describe the scene and main repetitive elements.")
            if not desc: desc = "A retro game background"
            
            # 2. Construct Prompt for Simplification
            prompt = (
                f"{self.prompt_template}. "
                f"Subject: {desc}. "
                f"CRITICAL: The image must fit into {max_tiles} unique 8x8 tiles. "
                "Reduce high-frequency noise. Make textures simple and repetitive. "
                "Use solid colors where possible. "
                "Ensure strict grid alignment."
            )
            print(f"      [AI-Optimize] Prompt: {prompt}")
            
            # 3. Call Img2Img via GenerativeResizer mechanism
            original_template = self.prompt_template
            self.prompt_template = prompt 
            # Recurse into generate_variant but with the new prompt
            result = self.generate_variant(input_path, output_path)
            self.prompt_template = original_template # Restore
            
            return result
        except Exception as e:
             print(f"      [AI-Optimize] Failed: {e}")
             return False

class AIAnimationGenerator:
    """
    AI-powered animation frame generator.

    Generates animation frames from a single sprite or text description,
    using available AI providers with automatic fallback.

    Integrates with:
    - ai_providers module for generation (Pollinations, Pixie.haus, SD Local)
    - animation.py for SGDK-compatible output (sprite sheets, metadata, headers)

    Usage:
        >>> from pipeline.ai import AIAnimationGenerator
        >>> gen = AIAnimationGenerator(platform="genesis")
        >>> result = gen.generate_animation("knight warrior", "walk", frames=6)
        >>> if result['success']:
        ...     result['sheet'].save("knight_walk.png")
    """

    SUPPORTED_ACTIONS = ['idle', 'walk', 'run', 'attack', 'jump', 'death', 'hit', 'cast']

    def __init__(self,
                 platform: str = "genesis",
                 preferred_provider: str = None,
                 output_dir: str = None):
        """
        Initialize the animation generator.

        Args:
            platform: Target platform (genesis, nes, snes, gameboy)
            preferred_provider: Preferred AI provider (pollinations, pixie_haus, sd_local)
            output_dir: Default output directory for generated files
        """
        self.platform = platform
        self.preferred_provider = preferred_provider
        self.output_dir = Path(output_dir) if output_dir else None

        # Platform-specific settings
        self._platform_config = PLATFORM_SPECS.get(platform, {})

        # Lazy-load provider
        self._provider = None

    def _get_provider(self):
        """Get the generation provider (lazy initialization)."""
        if self._provider is None:
            if AI_PROVIDERS_AVAILABLE:
                from .ai_providers import get_generation_provider, ProviderCapability
                try:
                    self._provider = get_generation_provider(
                        name=self.preferred_provider,
                        capability=ProviderCapability.ANIMATION
                    )
                except Exception:
                    # Fallback to any available provider
                    self._provider = get_generation_provider()
            else:
                raise RuntimeError("ai_providers module not available")
        return self._provider

    def generate_animation(self,
                          description: str,
                          action: str,
                          frames: int = None,
                          width: int = 32,
                          height: int = 32,
                          seed: int = None,
                          source_sprite: 'Image.Image' = None) -> Dict[str, Any]:
        """
        Generate animation frames from a description or source sprite.

        Args:
            description: Text description of the character/sprite
            action: Animation action (idle, walk, run, attack, jump, death, hit, cast)
            frames: Number of frames (auto-selected based on action if None)
            width: Frame width in pixels
            height: Frame height in pixels
            seed: Random seed for reproducibility
            source_sprite: Optional source sprite for style reference

        Returns:
            Dict with:
            - success: bool
            - frames: List[Image] - individual animation frames
            - sheet: Image - combined sprite sheet
            - metadata: dict - animation metadata
            - errors: List[str] - error messages if failed
        """
        from PIL import Image

        # Validate action
        action_lower = action.lower()
        if action_lower not in self.SUPPORTED_ACTIONS:
            return {
                'success': False,
                'frames': [],
                'errors': [f"Unsupported action: {action}. Supported: {self.SUPPORTED_ACTIONS}"]
            }

        # Auto-select frame count based on action
        if frames is None:
            frame_counts = {
                'idle': 4, 'walk': 6, 'run': 6, 'attack': 4,
                'jump': 4, 'death': 4, 'hit': 2, 'cast': 4
            }
            frames = frame_counts.get(action_lower, 4)

        try:
            provider = self._get_provider()

            # Build generation config
            if AI_PROVIDERS_AVAILABLE:
                from .ai_providers import GenerationConfig

                config = GenerationConfig(
                    width=width,
                    height=height,
                    platform=self.platform,
                    max_colors=self._platform_config.get('max_colors', 16),
                    seed=seed,
                    animation_frames=frames,
                    animation_action=action_lower,
                )

                # Generate animation frames
                if source_sprite:
                    result = provider.generate_animation(source_sprite, action_lower, config)
                else:
                    # Create a dummy source (provider will use description)
                    # First generate a single frame, then animate it
                    single_result = provider.generate(description, config)
                    if not single_result.success:
                        return {
                            'success': False,
                            'frames': [],
                            'errors': single_result.errors
                        }
                    result = provider.generate_animation(single_result.image, action_lower, config)

                if result.success and result.frames:
                    # Assemble sprite sheet
                    sheet = self._assemble_sheet(result.frames)

                    # Build metadata
                    metadata = {
                        'action': action_lower,
                        'frame_count': len(result.frames),
                        'frame_width': width,
                        'frame_height': height,
                        'frame_durations': result.frame_durations or [100] * len(result.frames),
                        'provider': result.provider,
                        'platform': self.platform,
                    }

                    return {
                        'success': True,
                        'frames': result.frames,
                        'sheet': sheet,
                        'metadata': metadata,
                        'errors': [],
                    }
                else:
                    return {
                        'success': False,
                        'frames': [],
                        'errors': result.errors or ["Animation generation failed"]
                    }
            else:
                return {
                    'success': False,
                    'frames': [],
                    'errors': ["AI providers not available"]
                }

        except Exception as e:
            return {
                'success': False,
                'frames': [],
                'errors': [str(e)]
            }

    def generate_animation_bundle(self,
                                  description: str,
                                  action: str,
                                  sprite_name: str,
                                  output_dir: str = None,
                                  **kwargs) -> Dict[str, str]:
        """
        Generate a complete animation bundle: frames + sheet + metadata + SGDK header.

        Integrates with animation.py for full pipeline output.

        Args:
            description: Character description
            action: Animation action
            sprite_name: Base name for output files
            output_dir: Output directory (uses instance default if None)
            **kwargs: Additional args passed to generate_animation()

        Returns:
            Dict with paths to generated files:
            - sheet: path to sprite sheet PNG
            - json: path to metadata JSON
            - header: path to SGDK C header
        """
        # Import animation.py integration functions
        from .animation import generate_animation_bundle as _gen_bundle

        output_path = Path(output_dir or self.output_dir or ".")
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate frames
        result = self.generate_animation(description, action, **kwargs)

        if not result['success']:
            raise RuntimeError(f"Animation generation failed: {result['errors']}")

        # Use animation.py to create the full bundle
        return _gen_bundle(
            frames=result['frames'],
            name=action,
            output_dir=str(output_path),
            sprite_name=sprite_name,
            duration=result['metadata'].get('frame_durations', [100])[0] // 16,  # Convert ms to Genesis ticks
        )

    def generate_multi_animation(self,
                                description: str,
                                actions: List[str],
                                sprite_name: str,
                                output_dir: str = None,
                                **kwargs) -> Dict[str, str]:
        """
        Generate multiple animations for a character.

        Args:
            description: Character description
            actions: List of actions (e.g., ['idle', 'walk', 'attack'])
            sprite_name: Base name for output files
            output_dir: Output directory
            **kwargs: Additional args passed to generate_animation()

        Returns:
            Dict with paths to combined output files
        """
        from .animation import generate_multi_animation_bundle as _gen_multi

        output_path = Path(output_dir or self.output_dir or ".")
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate frames for each action
        animations = {}
        for action in actions:
            result = self.generate_animation(description, action, **kwargs)
            if result['success']:
                animations[action] = result['frames']
            else:
                print(f"Warning: Failed to generate {action}: {result['errors']}")

        if not animations:
            raise RuntimeError("All animation generations failed")

        # Use animation.py to create combined bundle
        return _gen_multi(
            animations=animations,
            output_dir=str(output_path),
            sprite_name=sprite_name,
        )

    def _assemble_sheet(self, frames: List['Image.Image']) -> 'Image.Image':
        """Assemble frames into a horizontal sprite sheet."""
        from PIL import Image

        if not frames:
            raise ValueError("No frames to assemble")

        frame_w = frames[0].width
        frame_h = frames[0].height

        sheet = Image.new('RGBA', (frame_w * len(frames), frame_h), (0, 0, 0, 0))

        for i, frame in enumerate(frames):
            if frame.mode != 'RGBA':
                frame = frame.convert('RGBA')
            sheet.paste(frame, (i * frame_w, 0))

        return sheet

    @staticmethod
    def get_supported_actions() -> List[str]:
        """Get list of supported animation actions."""
        return AIAnimationGenerator.SUPPORTED_ACTIONS.copy()


class AIUpscaler:
    """
    AI-powered sprite upscaler with platform-aware requantization.

    Upscales sprites using AI providers while maintaining platform constraints
    (color limits, palette). Automatically requantizes the result to ensure
    hardware compatibility.

    Features:
    - AI-assisted upscaling (2x, 4x) via Pollinations, Pixie.haus, or SD Local
    - Automatic requantization to platform color limits
    - Perceptual color matching (CIEDE2000) for best quality
    - Optional dithering for smooth gradients
    - Fallback to nearest-neighbor if AI fails

    Fallback chain: pollinations -> pixie_haus -> sd_local -> nearest-neighbor

    Usage:
        >>> from pipeline.ai import AIUpscaler
        >>> upscaler = AIUpscaler(platform="genesis")
        >>> result = upscaler.upscale("sprite.png", scale=2)
        >>> if result['success']:
        ...     result['image'].save("sprite_2x.png")

        >>> # With requantization to specific palette
        >>> palette = [(0,0,0), (255,0,0), (0,255,0), (0,0,255)]
        >>> result = upscaler.upscale_and_requantize("sprite.png", scale=2, palette=palette)
    """

    SUPPORTED_SCALES = [2, 4]

    def __init__(self,
                 platform: str = "genesis",
                 preferred_provider: str = None,
                 output_dir: str = None,
                 quantize_method: str = 'CIEDE2000'):
        """
        Initialize the upscaler.

        Args:
            platform: Target platform (genesis, nes, snes, gameboy)
            preferred_provider: Preferred AI provider (pollinations, pixie_haus, sd_local)
            output_dir: Default output directory
            quantize_method: Color matching method for requantization
                            (CIEDE2000, CAM02-UCS, CIELab, RGB)
        """
        self.platform = platform
        self.preferred_provider = preferred_provider
        self.output_dir = Path(output_dir) if output_dir else None
        self.quantize_method = quantize_method

        # Platform-specific settings
        self._platform_config = PLATFORM_SPECS.get(platform, {})

        # Lazy-load provider and quantizer
        self._provider = None
        self._quantizer = None

    def _get_provider(self):
        """Get the upscaling provider (lazy initialization)."""
        if self._provider is None:
            if AI_PROVIDERS_AVAILABLE:
                from .ai_providers import get_generation_provider, ProviderCapability
                try:
                    self._provider = get_generation_provider(
                        name=self.preferred_provider,
                        capability=ProviderCapability.UPSCALING
                    )
                except Exception:
                    # Fallback to any available provider
                    self._provider = get_generation_provider()
            else:
                raise RuntimeError("ai_providers module not available")
        return self._provider

    def _get_quantizer(self):
        """Get the perceptual quantizer (lazy initialization)."""
        if self._quantizer is None:
            try:
                from .quantization.perceptual import PerceptualQuantizer
                self._quantizer = PerceptualQuantizer(method=self.quantize_method)
            except ImportError:
                self._quantizer = None
        return self._quantizer

    def upscale(self,
                source: 'Image.Image | str',
                scale: int = 2,
                seed: int = None) -> Dict[str, Any]:
        """
        Upscale a sprite using AI.

        Args:
            source: Source image (PIL Image or file path)
            scale: Scale factor (2 or 4)
            seed: Random seed for reproducibility

        Returns:
            Dict with:
            - success: bool
            - image: PIL Image (upscaled)
            - provider: str (provider used)
            - warnings: List[str]
            - errors: List[str]
        """
        # Validate scale
        if scale not in self.SUPPORTED_SCALES:
            return {
                'success': False,
                'errors': [f"Unsupported scale: {scale}. Supported: {self.SUPPORTED_SCALES}"]
            }

        # Load source image if path
        if isinstance(source, (str, Path)):
            try:
                source = Image.open(source)
            except Exception as e:
                return {
                    'success': False,
                    'errors': [f"Failed to load image: {e}"]
                }

        try:
            provider = self._get_provider()

            # Build generation config
            if AI_PROVIDERS_AVAILABLE:
                from .ai_providers import GenerationConfig

                config = GenerationConfig(
                    width=source.width * scale,
                    height=source.height * scale,
                    platform=self.platform,
                    max_colors=self._platform_config.get('max_colors', 16),
                    seed=seed,
                )

                # Perform upscaling
                result = provider.upscale(source, scale, config)

                if result.success and result.image:
                    return {
                        'success': True,
                        'image': result.image,
                        'provider': result.provider,
                        'model': result.model,
                        'generation_time_ms': result.generation_time_ms,
                        'warnings': result.warnings or [],
                        'errors': [],
                    }
                else:
                    return {
                        'success': False,
                        'errors': result.errors or ["Upscale failed"]
                    }
            else:
                return {
                    'success': False,
                    'errors': ["AI providers not available"]
                }

        except Exception as e:
            # Fallback to nearest-neighbor
            try:
                upscaled = source.resize(
                    (source.width * scale, source.height * scale),
                    Image.NEAREST
                )
                return {
                    'success': True,
                    'image': upscaled,
                    'provider': "nearest-neighbor",
                    'model': "nearest-neighbor",
                    'warnings': [f"AI upscale failed ({e}), used nearest-neighbor"],
                    'errors': [],
                }
            except Exception as e2:
                return {
                    'success': False,
                    'errors': [str(e), str(e2)]
                }

    def requantize(self,
                   image: 'Image.Image',
                   palette: List[Tuple[int, int, int]] = None,
                   max_colors: int = None,
                   dither: bool = False) -> Dict[str, Any]:
        """
        Requantize an image to a target palette or color count.

        Args:
            image: Source image to requantize
            palette: Target palette (RGB tuples). If None, extracts optimal palette.
            max_colors: Maximum colors (used if palette is None)
            dither: Apply Floyd-Steinberg dithering

        Returns:
            Dict with:
            - success: bool
            - image: PIL Image (requantized)
            - palette: List[RGB] (palette used)
            - error_sum: float (quantization error)
        """
        max_colors = max_colors or self._platform_config.get('max_colors', 16)

        try:
            quantizer = self._get_quantizer()

            if quantizer:
                # Use perceptual quantizer
                if palette:
                    result = quantizer.quantize(image, palette, dither=dither)
                else:
                    result = quantizer.quantize_with_extraction(
                        image,
                        num_colors=max_colors,
                        dither=dither
                    )

                # Convert indexed image back to RGBA for further processing
                rgba_image = result.image.convert('RGBA')

                return {
                    'success': True,
                    'image': rgba_image,
                    'indexed_image': result.image,
                    'palette': result.palette,
                    'error_sum': result.error_sum,
                }
            else:
                # Fallback to PIL quantization
                if palette:
                    # Create palette image for reference
                    pal_img = Image.new('P', (1, 1))
                    flat_pal = []
                    for r, g, b in palette:
                        flat_pal.extend([r, g, b])
                    flat_pal.extend([0] * (768 - len(flat_pal)))
                    pal_img.putpalette(flat_pal)

                    # Quantize to palette
                    quantized = image.convert('RGB').quantize(
                        colors=len(palette),
                        palette=pal_img,
                        dither=Image.Dither.FLOYDSTEINBERG if dither else Image.Dither.NONE
                    )
                else:
                    # Auto-quantize
                    quantized = image.convert('RGB').quantize(
                        colors=max_colors,
                        dither=Image.Dither.FLOYDSTEINBERG if dither else Image.Dither.NONE
                    )

                # Extract palette from result
                pal_data = quantized.getpalette()
                result_palette = []
                for i in range(min(max_colors, 256)):
                    idx = i * 3
                    if idx + 2 < len(pal_data):
                        result_palette.append((pal_data[idx], pal_data[idx+1], pal_data[idx+2]))

                return {
                    'success': True,
                    'image': quantized.convert('RGBA'),
                    'indexed_image': quantized,
                    'palette': result_palette,
                    'error_sum': 0.0,  # Unknown without perceptual quantizer
                }

        except Exception as e:
            return {
                'success': False,
                'errors': [str(e)]
            }

    def upscale_and_requantize(self,
                               source: 'Image.Image | str',
                               scale: int = 2,
                               palette: List[Tuple[int, int, int]] = None,
                               max_colors: int = None,
                               dither: bool = False,
                               seed: int = None,
                               output_path: str = None) -> Dict[str, Any]:
        """
        Upscale a sprite and requantize to platform constraints.

        This is the primary method for Phase 3.2 - combines AI upscaling
        with palette requantization in a single operation.

        Args:
            source: Source image (PIL Image or file path)
            scale: Scale factor (2 or 4)
            palette: Target palette (RGB tuples). If None, extracts optimal palette.
            max_colors: Maximum colors (used if palette is None)
            dither: Apply Floyd-Steinberg dithering
            seed: Random seed for AI upscaling
            output_path: Optional path to save result

        Returns:
            Dict with:
            - success: bool
            - image: PIL Image (final result)
            - upscaled_image: PIL Image (before requantization)
            - palette: List[RGB] (palette used)
            - provider: str (AI provider used)
            - warnings: List[str]
            - errors: List[str]
        """
        # Step 1: Upscale
        upscale_result = self.upscale(source, scale, seed)

        if not upscale_result['success']:
            return upscale_result

        upscaled_image = upscale_result['image']
        warnings = upscale_result.get('warnings', [])

        # Step 2: Requantize
        requant_result = self.requantize(
            upscaled_image,
            palette=palette,
            max_colors=max_colors,
            dither=dither
        )

        if not requant_result['success']:
            requant_result['upscaled_image'] = upscaled_image
            requant_result['provider'] = upscale_result.get('provider', 'unknown')
            return requant_result

        final_image = requant_result['image']

        # Step 3: Save if output path provided
        if output_path:
            try:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                final_image.save(str(output_path))
            except Exception as e:
                warnings.append(f"Failed to save output: {e}")

        return {
            'success': True,
            'image': final_image,
            'upscaled_image': upscaled_image,
            'indexed_image': requant_result.get('indexed_image'),
            'palette': requant_result['palette'],
            'error_sum': requant_result.get('error_sum', 0.0),
            'provider': upscale_result.get('provider', 'unknown'),
            'model': upscale_result.get('model', 'unknown'),
            'warnings': warnings,
            'errors': [],
        }

    def batch_upscale(self,
                      sources: List['Image.Image | str'],
                      scale: int = 2,
                      requantize: bool = True,
                      palette: List[Tuple[int, int, int]] = None,
                      max_colors: int = None,
                      dither: bool = False,
                      show_progress: bool = True) -> List[Dict[str, Any]]:
        """
        Batch upscale multiple sprites.

        Args:
            sources: List of source images (PIL Images or file paths)
            scale: Scale factor (2 or 4)
            requantize: Whether to requantize after upscaling
            palette: Shared palette for all sprites (optional)
            max_colors: Maximum colors (used if palette is None)
            dither: Apply dithering
            show_progress: Print progress

        Returns:
            List of result dicts (same format as upscale_and_requantize)
        """
        results = []
        total = len(sources)

        for i, source in enumerate(sources):
            if show_progress:
                print(f"  Upscaling {i+1}/{total}...")

            if requantize:
                result = self.upscale_and_requantize(
                    source, scale, palette, max_colors, dither
                )
            else:
                result = self.upscale(source, scale)

            results.append(result)

            if show_progress and result['success']:
                provider = result.get('provider', 'unknown')
                print(f"    ✓ Success via {provider}")
            elif show_progress:
                print(f"    ✗ Failed: {result.get('errors', ['Unknown'])}")

        return results

    @staticmethod
    def get_supported_scales() -> List[int]:
        """Get list of supported scale factors."""
        return AIUpscaler.SUPPORTED_SCALES.copy()


class BackgroundRemover:
    """
    AI-powered background removal with platform-specific transparency handling.

    Removes backgrounds from sprites using multiple methods:
    1. rembg (primary) - Deep learning-based, highest quality
    2. Flood-fill detection - Rule-based, detects solid color backgrounds
    3. Manual threshold - Simple alpha threshold method

    Provides automatic alpha-to-magenta conversion for Genesis/SGDK sprites.

    Features:
    - AI background removal via rembg (u2net models)
    - Fallback to flood-fill for solid color backgrounds
    - Alpha-to-magenta conversion for Genesis compatibility
    - Batch processing support
    - Edge refinement options

    Usage:
        >>> from pipeline.ai import BackgroundRemover
        >>> remover = BackgroundRemover()
        >>>
        >>> # Remove background (returns RGBA with transparency)
        >>> result = remover.remove_background("photo_sprite.png")
        >>> if result['success']:
        ...     result['image'].save("sprite_transparent.png")
        >>>
        >>> # For Genesis/SGDK (magenta transparency)
        >>> result = remover.remove_for_genesis("photo_sprite.png")
        >>> if result['success']:
        ...     result['image'].save("genesis_sprite.png")  # RGB with magenta bg
    """

    # Genesis/SGDK transparency color
    MAGENTA = (255, 0, 255)

    # Default alpha threshold for conversion
    DEFAULT_ALPHA_THRESHOLD = 128

    def __init__(self,
                 method: str = 'auto',
                 model: str = 'u2net',
                 alpha_threshold: int = 128):
        """
        Initialize background remover.

        Args:
            method: Removal method - 'auto', 'rembg', 'flood_fill', 'threshold'
            model: rembg model name (u2net, u2netp, u2net_human_seg, silueta, isnet-general-use)
            alpha_threshold: Threshold for alpha-to-magenta conversion (0-255)
        """
        self.method = method
        self.model = model
        self.alpha_threshold = alpha_threshold

        # Check for rembg availability
        self._rembg_available = None
        self._flood_fill_detector = None

    def _check_rembg(self) -> bool:
        """Check if rembg is available."""
        if self._rembg_available is None:
            try:
                import rembg
                self._rembg_available = True
            except ImportError:
                self._rembg_available = False
        return self._rembg_available

    def _get_flood_fill_detector(self):
        """Get flood fill detector (lazy initialization)."""
        if self._flood_fill_detector is None:
            try:
                from .processing import FloodFillBackgroundDetector
                self._flood_fill_detector = FloodFillBackgroundDetector(tolerance=15)
            except ImportError:
                self._flood_fill_detector = None
        return self._flood_fill_detector

    def remove_background(self,
                          source: 'Image.Image | str',
                          method: str = None,
                          post_process: bool = True) -> Dict[str, Any]:
        """
        Remove background from image, returning RGBA with transparency.

        Args:
            source: Source image (PIL Image or file path)
            method: Override default method ('rembg', 'flood_fill', 'threshold', or 'auto')
            post_process: Apply edge refinement after removal

        Returns:
            Dict with:
            - success: bool
            - image: PIL Image (RGBA with transparency)
            - method_used: str (actual method used)
            - warnings: List[str]
            - errors: List[str]
        """
        method = method or self.method

        # Load source image if path
        if isinstance(source, (str, Path)):
            try:
                source = Image.open(source)
            except Exception as e:
                return {
                    'success': False,
                    'errors': [f"Failed to load image: {e}"]
                }

        # Ensure RGBA
        if source.mode != 'RGBA':
            source = source.convert('RGBA')

        warnings = []

        # Try methods in order based on preference
        if method == 'auto':
            # Try rembg first, then flood_fill
            if self._check_rembg():
                result = self._remove_with_rembg(source)
                if result['success']:
                    result['method_used'] = 'rembg'
                    if post_process:
                        result['image'] = self._refine_edges(result['image'])
                    return result
                else:
                    warnings.extend(result.get('errors', []))

            # Fall back to flood fill
            result = self._remove_with_flood_fill(source)
            if result['success']:
                result['method_used'] = 'flood_fill'
                result['warnings'] = warnings + result.get('warnings', [])
                return result
            else:
                warnings.extend(result.get('errors', []))

            # Last resort: threshold
            result = self._remove_with_threshold(source)
            result['method_used'] = 'threshold'
            result['warnings'] = warnings + ['Fell back to threshold method']
            return result

        elif method == 'rembg':
            if not self._check_rembg():
                return {
                    'success': False,
                    'errors': ['rembg not installed. Install with: pip install rembg']
                }
            result = self._remove_with_rembg(source)
            if result['success'] and post_process:
                result['image'] = self._refine_edges(result['image'])
            return result

        elif method == 'flood_fill':
            return self._remove_with_flood_fill(source)

        elif method == 'threshold':
            return self._remove_with_threshold(source)

        else:
            return {
                'success': False,
                'errors': [f"Unknown method: {method}. Use 'auto', 'rembg', 'flood_fill', or 'threshold'"]
            }

    def _remove_with_rembg(self, img: Image.Image) -> Dict[str, Any]:
        """Remove background using rembg."""
        try:
            from rembg import remove, new_session

            # Create session with specified model
            session = new_session(self.model)

            # Remove background
            result_img = remove(img, session=session)

            return {
                'success': True,
                'image': result_img,
                'method_used': 'rembg',
                'model': self.model,
                'warnings': [],
                'errors': [],
            }

        except Exception as e:
            return {
                'success': False,
                'errors': [f"rembg failed: {e}"]
            }

    def _remove_with_flood_fill(self, img: Image.Image) -> Dict[str, Any]:
        """Remove background using flood fill from corners."""
        try:
            detector = self._get_flood_fill_detector()

            if detector is None:
                return {
                    'success': False,
                    'errors': ['FloodFillBackgroundDetector not available']
                }

            # Get content mask
            mask = detector.get_content_mask(img)

            # Apply mask to image
            result = img.copy()
            result.putalpha(mask.convert('L').point(lambda x: 255 if x else 0))

            return {
                'success': True,
                'image': result,
                'method_used': 'flood_fill',
                'warnings': [],
                'errors': [],
            }

        except Exception as e:
            return {
                'success': False,
                'errors': [f"Flood fill failed: {e}"]
            }

    def _remove_with_threshold(self, img: Image.Image) -> Dict[str, Any]:
        """
        Remove background using simple threshold detection.

        Detects the most common color in corners and marks it as transparent.
        """
        try:
            # Sample corners to find background color
            pixels = img.load()
            w, h = img.size

            corners = [
                pixels[0, 0],
                pixels[w-1, 0],
                pixels[0, h-1],
                pixels[w-1, h-1]
            ]

            # Find most common corner color
            from collections import Counter
            bg_color = Counter(corners).most_common(1)[0][0]

            # Create result with transparent background
            result = img.copy()
            result_pixels = result.load()

            tolerance = 30  # Color matching tolerance

            for y in range(h):
                for x in range(w):
                    pixel = result_pixels[x, y]
                    # Check if pixel matches background color
                    dist = sum(abs(a - b) for a, b in zip(pixel[:3], bg_color[:3]))
                    if dist <= tolerance:
                        result_pixels[x, y] = (pixel[0], pixel[1], pixel[2], 0)

            return {
                'success': True,
                'image': result,
                'method_used': 'threshold',
                'background_color': bg_color[:3],
                'warnings': ['Using simple threshold - may have artifacts'],
                'errors': [],
            }

        except Exception as e:
            return {
                'success': False,
                'errors': [f"Threshold method failed: {e}"]
            }

    def _refine_edges(self, img: Image.Image) -> Image.Image:
        """Apply edge refinement to remove halos and jagged edges."""
        try:
            # Simple edge cleanup: erode alpha slightly then re-expand
            # This helps remove semi-transparent fringes

            # Get alpha channel
            if img.mode != 'RGBA':
                return img

            r, g, b, a = img.split()

            # Threshold alpha to clean up semi-transparency
            a = a.point(lambda x: 255 if x > self.alpha_threshold else 0)

            # Recombine
            return Image.merge('RGBA', (r, g, b, a))

        except Exception:
            return img

    def alpha_to_magenta(self,
                         img: Image.Image,
                         threshold: int = None) -> Image.Image:
        """
        Convert alpha transparency to magenta color key.

        Used for Genesis/SGDK sprites which use magenta (255,0,255) as
        the transparent color instead of alpha channel.

        Args:
            img: RGBA image with transparency
            threshold: Alpha threshold (default: 128)

        Returns:
            RGB image with magenta background
        """
        threshold = threshold if threshold is not None else self.alpha_threshold

        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # Create RGB image with magenta background
        rgb = Image.new('RGB', img.size, self.MAGENTA)
        rgb_pixels = rgb.load()
        src_pixels = img.load()

        for y in range(img.height):
            for x in range(img.width):
                r, g, b, a = src_pixels[x, y]
                if a >= threshold:
                    rgb_pixels[x, y] = (r, g, b)
                # else: stays magenta

        return rgb

    def magenta_to_alpha(self,
                         img: Image.Image,
                         tolerance: int = 10) -> Image.Image:
        """
        Convert magenta color key to alpha transparency.

        Useful for loading Genesis sprites and converting to RGBA.

        Args:
            img: RGB image with magenta transparency
            tolerance: Color matching tolerance

        Returns:
            RGBA image with alpha channel
        """
        if img.mode == 'RGBA':
            # Already has alpha, check if magenta pixels need conversion
            pass
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # Create RGBA result
        rgba = img.convert('RGBA')
        pixels = rgba.load()

        for y in range(rgba.height):
            for x in range(rgba.width):
                r, g, b, a = pixels[x, y]
                # Check if pixel is close to magenta
                dist = abs(r - 255) + abs(g - 0) + abs(b - 255)
                if dist <= tolerance:
                    pixels[x, y] = (r, g, b, 0)  # Make transparent

        return rgba

    def remove_for_genesis(self,
                           source: 'Image.Image | str',
                           method: str = None,
                           output_path: str = None) -> Dict[str, Any]:
        """
        Remove background and convert to Genesis/SGDK format.

        Combines background removal with alpha-to-magenta conversion
        for direct use with SGDK/Genesis sprite compilation.

        Args:
            source: Source image (PIL Image or file path)
            method: Override default method
            output_path: Optional path to save result

        Returns:
            Dict with:
            - success: bool
            - image: PIL Image (RGB with magenta transparency)
            - rgba_image: PIL Image (RGBA version before conversion)
            - method_used: str
            - warnings: List[str]
            - errors: List[str]
        """
        # Step 1: Remove background to get RGBA
        result = self.remove_background(source, method)

        if not result['success']:
            return result

        rgba_image = result['image']
        warnings = result.get('warnings', [])

        # Step 2: Convert alpha to magenta
        try:
            genesis_image = self.alpha_to_magenta(rgba_image)
        except Exception as e:
            return {
                'success': False,
                'rgba_image': rgba_image,
                'errors': [f"Alpha-to-magenta conversion failed: {e}"]
            }

        # Step 3: Save if output path provided
        if output_path:
            try:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                genesis_image.save(str(output_path))
            except Exception as e:
                warnings.append(f"Failed to save output: {e}")

        return {
            'success': True,
            'image': genesis_image,
            'rgba_image': rgba_image,
            'method_used': result.get('method_used', 'unknown'),
            'warnings': warnings,
            'errors': [],
        }

    def batch_remove(self,
                     sources: List['Image.Image | str'],
                     for_genesis: bool = False,
                     method: str = None,
                     show_progress: bool = True) -> List[Dict[str, Any]]:
        """
        Batch process multiple images.

        Args:
            sources: List of source images (PIL Images or file paths)
            for_genesis: If True, output magenta transparency format
            method: Override default method
            show_progress: Print progress

        Returns:
            List of result dicts
        """
        results = []
        total = len(sources)

        for i, source in enumerate(sources):
            if show_progress:
                name = source if isinstance(source, str) else f"image_{i}"
                print(f"  Processing {i+1}/{total}: {name}...")

            if for_genesis:
                result = self.remove_for_genesis(source, method)
            else:
                result = self.remove_background(source, method)

            results.append(result)

            if show_progress and result['success']:
                method_used = result.get('method_used', 'unknown')
                print(f"    ✓ Success via {method_used}")
            elif show_progress:
                print(f"    ✗ Failed: {result.get('errors', ['Unknown'])}")

        return results

    @staticmethod
    def get_available_methods() -> List[str]:
        """Get list of available background removal methods."""
        methods = ['auto', 'flood_fill', 'threshold']
        try:
            import rembg
            methods.insert(1, 'rembg')
        except ImportError:
            pass
        return methods

    @staticmethod
    def get_rembg_models() -> List[str]:
        """Get list of available rembg models."""
        return [
            'u2net',           # General purpose (default)
            'u2netp',          # Lightweight version
            'u2net_human_seg', # Optimized for humans
            'u2net_cloth_seg', # Clothing segmentation
            'silueta',         # Fast and lightweight
            'isnet-general-use', # High quality general purpose
            'isnet-anime',     # Anime/illustration
        ]


class TilesetGenerator:
    """
    AI-powered tileset generation with coherence and auto-tile support.

    Generates coherent tilesets from text prompts using multiple AI providers.
    Supports auto-tile layouts (Wang/blob tiles) for seamless level building.

    Features:
    - Multi-provider support (Pollinations, Pixie.haus, SD Local)
    - Coherent tile generation with edge matching
    - Auto-tile layout (16-tile Wang/blob format)
    - Platform-specific palettes and constraints
    - Collision metadata generation
    - Batch generation with progress

    Auto-tile format (16 tiles):
        0: All empty    4: L only       8: T only      12: T+L
        1: R only       5: L+R          9: T+R         13: T+L+R
        2: B only       6: L+B         10: T+B         14: All filled
        3: R+B          7: L+R+B       11: T+R+B       15: Center

    Usage:
        >>> from pipeline.ai import TilesetGenerator
        >>> generator = TilesetGenerator(platform="genesis")
        >>>
        >>> # Generate simple tileset
        >>> result = generator.generate_tileset(
        ...     "stone brick wall",
        ...     tile_size=16,
        ...     tile_count=16
        ... )
        >>> if result['success']:
        ...     result['tileset_image'].save("stone_tiles.png")
        >>>
        >>> # Generate auto-tile set (Wang tiles)
        >>> result = generator.generate_autotile(
        ...     "grass terrain",
        ...     tile_size=16,
        ...     edge_type="blob"
        ... )
    """

    # Standard tile sizes
    TILE_SIZES = [8, 16, 24, 32]

    # Auto-tile layouts
    AUTOTILE_16 = 'wang_16'      # 16-tile Wang/blob layout
    AUTOTILE_47 = 'rpgmaker_47'  # RPG Maker 47-tile format
    AUTOTILE_SIMPLE = 'simple_4' # 4-corner tiles only

    def __init__(self,
                 platform: str = "genesis",
                 preferred_provider: str = None,
                 coherence_method: str = 'guided',
                 output_dir: str = None):
        """
        Initialize tileset generator.

        Args:
            platform: Target platform (genesis, nes, snes, gameboy)
            preferred_provider: Preferred AI provider (pollinations, pixie_haus, sd_local)
            coherence_method: Method for ensuring tile coherence
                            ('guided' uses descriptive prompts, 'seed' uses same seed,
                             'reference' uses first tile as style reference)
            output_dir: Default output directory
        """
        self.platform = platform
        self.preferred_provider = preferred_provider
        self.coherence_method = coherence_method
        self.output_dir = Path(output_dir) if output_dir else None

        # Platform-specific settings
        self._platform_config = PLATFORM_SPECS.get(platform, {})

        # Lazy-load provider
        self._provider = None

    def _get_provider(self):
        """Get the generation provider (lazy initialization)."""
        if self._provider is None:
            if AI_PROVIDERS_AVAILABLE:
                from .ai_providers import get_generation_provider, ProviderCapability
                try:
                    self._provider = get_generation_provider(
                        name=self.preferred_provider,
                        capability=ProviderCapability.TEXT_TO_IMAGE
                    )
                except Exception:
                    # Fallback to any available provider
                    self._provider = get_generation_provider()
            else:
                raise RuntimeError("ai_providers module not available")
        return self._provider

    def generate_tileset(self,
                         description: str,
                         tile_size: int = 16,
                         tile_count: int = 16,
                         tiles_per_row: int = 4,
                         seed: int = None,
                         style: str = None,
                         output_path: str = None) -> Dict[str, Any]:
        """
        Generate a coherent tileset from a description.

        Args:
            description: Description of the tileset theme (e.g., "stone brick wall")
            tile_size: Size of each tile in pixels
            tile_count: Total number of tiles to generate
            tiles_per_row: Number of tiles per row in output sheet
            seed: Random seed for reproducibility
            style: Optional style hint (medieval, sci-fi, pixel-art, etc.)
            output_path: Optional path to save tileset image

        Returns:
            Dict with:
            - success: bool
            - tileset_image: PIL Image (complete tileset sheet)
            - tiles: List[Image] (individual tiles)
            - tile_count: int
            - provider: str
            - warnings: List[str]
            - errors: List[str]
        """
        if tile_size not in self.TILE_SIZES:
            return {
                'success': False,
                'errors': [f"Unsupported tile size: {tile_size}. Use {self.TILE_SIZES}"]
            }

        try:
            provider = self._get_provider()

            # Build coherent prompts for each tile
            tile_prompts = self._build_tileset_prompts(
                description, tile_count, style
            )

            # Generate tiles with coherence strategy
            tiles = []
            warnings = []
            used_seed = seed or int(time.time())

            if AI_PROVIDERS_AVAILABLE:
                from .ai_providers import GenerationConfig

                for i, prompt in enumerate(tile_prompts):
                    # Use same base seed for coherence
                    tile_seed = used_seed + i if self.coherence_method == 'seed' else None

                    config = GenerationConfig(
                        width=tile_size,
                        height=tile_size,
                        platform=self.platform,
                        max_colors=self._platform_config.get('max_colors', 16),
                        seed=tile_seed,
                    )

                    result = provider.generate(prompt, config)

                    if result.success and result.image:
                        tiles.append(result.image)
                    else:
                        warnings.extend(result.errors or [f"Tile {i} generation failed"])
                        # Create placeholder
                        placeholder = Image.new('RGBA', (tile_size, tile_size), (128, 128, 128, 255))
                        tiles.append(placeholder)

            if not tiles:
                return {
                    'success': False,
                    'errors': ['No tiles generated']
                }

            # Assemble tileset sheet
            tileset_image = self._assemble_tileset_sheet(
                tiles, tiles_per_row, tile_size
            )

            # Save if output path provided
            if output_path:
                try:
                    output_path = Path(output_path)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    tileset_image.save(str(output_path))
                except Exception as e:
                    warnings.append(f"Failed to save output: {e}")

            return {
                'success': True,
                'tileset_image': tileset_image,
                'tiles': tiles,
                'tile_count': len(tiles),
                'tile_size': tile_size,
                'provider': provider.name,
                'seed': used_seed,
                'warnings': warnings,
                'errors': [],
            }

        except Exception as e:
            return {
                'success': False,
                'errors': [str(e)]
            }

    def generate_autotile(self,
                          description: str,
                          tile_size: int = 16,
                          layout: str = 'wang_16',
                          seed: int = None,
                          style: str = None,
                          output_path: str = None) -> Dict[str, Any]:
        """
        Generate an auto-tile set for seamless level building.

        Auto-tiles (Wang tiles / blob tiles) allow automatic terrain edge
        matching. Generates 16 tiles covering all possible neighbor combinations.

        Args:
            description: Terrain description (e.g., "grass", "water", "stone")
            tile_size: Size of each tile in pixels
            layout: Auto-tile layout type ('wang_16', 'rpgmaker_47', 'simple_4')
            seed: Random seed for reproducibility
            style: Optional style hint
            output_path: Optional path to save tileset

        Returns:
            Dict with same format as generate_tileset, plus:
            - layout: str (layout type used)
            - autotile_map: Dict (tile index -> neighbor pattern)
        """
        if layout == 'wang_16':
            tile_count = 16
            autotile_map = self._get_wang_16_map()
        elif layout == 'rpgmaker_47':
            return {
                'success': False,
                'errors': ['RPG Maker 47-tile format not yet implemented']
            }
        elif layout == 'simple_4':
            tile_count = 4
            autotile_map = {
                0: {'neighbors': 'none', 'desc': 'isolated'},
                1: {'neighbors': 'horizontal', 'desc': 'left-right'},
                2: {'neighbors': 'vertical', 'desc': 'top-bottom'},
                3: {'neighbors': 'all', 'desc': 'filled'},
            }
        else:
            return {
                'success': False,
                'errors': [f"Unknown layout: {layout}"]
            }

        # Build prompts for auto-tile variations
        tile_prompts = self._build_autotile_prompts(
            description, autotile_map, style
        )

        # Generate tileset
        result = self.generate_tileset(
            description,
            tile_size=tile_size,
            tile_count=tile_count,
            tiles_per_row=4,
            seed=seed,
            style=style,
            output_path=output_path
        )

        if result['success']:
            result['layout'] = layout
            result['autotile_map'] = autotile_map

        return result

    def _build_tileset_prompts(self,
                               description: str,
                               tile_count: int,
                               style: str = None) -> List[str]:
        """Build coherent prompts for tileset generation."""
        base_prompt_parts = [
            f"{description}",
            "pixel art tile",
            f"retro {self.platform} style",
        ]

        if style:
            base_prompt_parts.append(f"{style} style")

        base_prompt_parts.extend([
            "seamless",
            "tileable",
            "consistent lighting",
            "top-down view",
        ])

        base_prompt = ", ".join(base_prompt_parts)

        # Generate variations for different tiles
        prompts = []
        variations = [
            "center tile",
            "edge variation",
            "corner piece",
            "alternate pattern",
        ]

        for i in range(tile_count):
            variation = variations[i % len(variations)]
            prompt = f"{base_prompt}, {variation}"
            prompts.append(prompt)

        return prompts

    def _build_autotile_prompts(self,
                                description: str,
                                autotile_map: Dict,
                                style: str = None) -> List[str]:
        """Build prompts for auto-tile generation with edge matching."""
        prompts = []

        for tile_idx, tile_info in autotile_map.items():
            neighbors = tile_info.get('desc', '')
            edge_desc = tile_info.get('edges', '')

            prompt_parts = [
                f"{description} terrain tile",
                f"pixel art",
                f"retro {self.platform} style",
            ]

            if style:
                prompt_parts.append(f"{style} style")

            # Add neighbor-specific description
            if neighbors:
                prompt_parts.append(f"{neighbors} configuration")

            if edge_desc:
                prompt_parts.append(edge_desc)

            prompt_parts.extend([
                "seamless edges",
                "tileable",
                "consistent lighting",
                "top-down view",
            ])

            prompts.append(", ".join(prompt_parts))

        return prompts

    def _get_wang_16_map(self) -> Dict:
        """Get Wang/blob 16-tile autotile mapping."""
        return {
            0:  {'neighbors': 'none', 'desc': 'isolated', 'edges': 'all empty'},
            1:  {'neighbors': 'right', 'desc': 'right only', 'edges': 'right filled'},
            2:  {'neighbors': 'bottom', 'desc': 'bottom only', 'edges': 'bottom filled'},
            3:  {'neighbors': 'right+bottom', 'desc': 'right and bottom', 'edges': 'right+bottom filled'},
            4:  {'neighbors': 'left', 'desc': 'left only', 'edges': 'left filled'},
            5:  {'neighbors': 'left+right', 'desc': 'horizontal', 'edges': 'left+right filled'},
            6:  {'neighbors': 'left+bottom', 'desc': 'left and bottom', 'edges': 'left+bottom filled'},
            7:  {'neighbors': 'left+right+bottom', 'desc': 'bottom filled', 'edges': 'bottom sides filled'},
            8:  {'neighbors': 'top', 'desc': 'top only', 'edges': 'top filled'},
            9:  {'neighbors': 'top+right', 'desc': 'top and right', 'edges': 'top+right filled'},
            10: {'neighbors': 'top+bottom', 'desc': 'vertical', 'edges': 'top+bottom filled'},
            11: {'neighbors': 'top+right+bottom', 'desc': 'right filled', 'edges': 'right sides filled'},
            12: {'neighbors': 'top+left', 'desc': 'top and left', 'edges': 'top+left filled'},
            13: {'neighbors': 'top+left+right', 'desc': 'top filled', 'edges': 'top sides filled'},
            14: {'neighbors': 'all', 'desc': 'all neighbors', 'edges': 'all sides filled'},
            15: {'neighbors': 'center', 'desc': 'center fill', 'edges': 'fully surrounded'},
        }

    def _assemble_tileset_sheet(self,
                                tiles: List[Image.Image],
                                tiles_per_row: int,
                                tile_size: int) -> Image.Image:
        """Assemble individual tiles into a tileset sheet."""
        tile_count = len(tiles)
        rows = (tile_count + tiles_per_row - 1) // tiles_per_row

        sheet_width = tiles_per_row * tile_size
        sheet_height = rows * tile_size

        sheet = Image.new('RGBA', (sheet_width, sheet_height), (0, 0, 0, 0))

        for i, tile in enumerate(tiles):
            row = i // tiles_per_row
            col = i % tiles_per_row

            x = col * tile_size
            y = row * tile_size

            # Ensure tile is correct size
            if tile.size != (tile_size, tile_size):
                tile = tile.resize((tile_size, tile_size), Image.NEAREST)

            sheet.paste(tile, (x, y))

        return sheet

    def generate_with_collision(self,
                                description: str,
                                tile_size: int = 16,
                                tile_count: int = 16,
                                **kwargs) -> Dict[str, Any]:
        """
        Generate tileset with automatic collision detection.

        Analyzes generated tiles to determine solid/passable regions.

        Returns:
            Same as generate_tileset, plus:
            - collision_map: List[Dict] (per-tile collision data)
        """
        result = self.generate_tileset(
            description, tile_size, tile_count, **kwargs
        )

        if not result['success']:
            return result

        # Generate collision data for each tile
        collision_map = []
        for i, tile in enumerate(result['tiles']):
            collision = self._detect_tile_collision(tile)
            collision_map.append({
                'tile_index': i,
                'solid': collision['solid'],
                'passable_region': collision['passable_region'],
            })

        result['collision_map'] = collision_map
        return result

    def _detect_tile_collision(self, tile: Image.Image) -> Dict:
        """
        Detect collision data from tile appearance.

        Simple heuristic: bright/opaque = solid, dark/transparent = passable.
        """
        pixels = list(tile.getdata())
        total = len(pixels)

        solid_count = 0
        for pixel in pixels:
            if len(pixel) == 4:
                r, g, b, a = pixel
                # Bright and opaque = solid
                brightness = (r + g + b) / 3
                if brightness > 128 and a > 200:
                    solid_count += 1
            else:
                r, g, b = pixel
                brightness = (r + g + b) / 3
                if brightness > 128:
                    solid_count += 1

        solid_ratio = solid_count / total if total > 0 else 0

        return {
            'solid': solid_ratio > 0.6,
            'passable_region': 'full' if solid_ratio < 0.3 else 'partial' if solid_ratio < 0.7 else 'none'
        }

    def batch_generate(self,
                       descriptions: List[str],
                       tile_size: int = 16,
                       tile_count: int = 16,
                       show_progress: bool = True,
                       **kwargs) -> List[Dict[str, Any]]:
        """
        Batch generate multiple tilesets.

        Args:
            descriptions: List of tileset descriptions
            tile_size: Size of each tile
            tile_count: Number of tiles per set
            show_progress: Print progress
            **kwargs: Additional args for generate_tileset

        Returns:
            List of result dicts
        """
        results = []
        total = len(descriptions)

        for i, desc in enumerate(descriptions):
            if show_progress:
                print(f"  Generating tileset {i+1}/{total}: {desc}...")

            result = self.generate_tileset(
                desc, tile_size, tile_count, **kwargs
            )

            results.append(result)

            if show_progress and result['success']:
                provider = result.get('provider', 'unknown')
                print(f"    ✓ Success via {provider}")
            elif show_progress:
                print(f"    ✗ Failed: {result.get('errors', ['Unknown'])}")

        return results

    @staticmethod
    def get_supported_layouts() -> List[str]:
        """Get list of supported auto-tile layouts."""
        return [
            TilesetGenerator.AUTOTILE_16,
            TilesetGenerator.AUTOTILE_47,
            TilesetGenerator.AUTOTILE_SIMPLE,
        ]

    @staticmethod
    def get_tile_sizes() -> List[int]:
        """Get list of supported tile sizes."""
        return TilesetGenerator.TILE_SIZES.copy()


class AIAnalyzer:
    """
    Multi-provider AI analyzer with caching and fallback.
    Pollinations.ai is the primary provider with 30+ vision-capable models.
    """

    # Pollinations API key - loaded from environment/config
    # Do not hardcode keys here - use .env file or environment variables
    DEFAULT_POLLINATIONS_KEY = None

    def __init__(self, preferred_provider: str = None, cache_dir: str = ".cache/ai",
                 pollinations_key: str = None, pollinations_model: str = "openai-large",
                 offline_mode: bool = False):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.offline_mode = offline_mode

        # In offline mode, don't initialize any providers
        if offline_mode:
            self.providers: List[AIProvider] = []
            return

        # Use provided key, env var, or default
        poll_key = pollinations_key or os.getenv('POLLINATIONS_API_KEY') or self.DEFAULT_POLLINATIONS_KEY

        # Initialize providers
        self.providers: List[AIProvider] = []

        # Default model logic: Use 'openai-large' (GPT-5.2) for best vision performance 
        # unless explicitly overridden. 'gemini-fast' was causing issues.
        # Check if model was passed, otherwise default to openai-large
        final_model = pollinations_model if pollinations_model != "openai-large" else "openai-large"

        if preferred_provider:
            # Use specific provider
            provider_key = preferred_provider.lower()
            if provider_key == 'pollinations':
                self.providers = [PollinationsProvider(api_key=poll_key, model=final_model)]
            elif provider_key == 'gemini':
                self.providers = [GeminiProvider()]
            elif provider_key == 'openai':
                self.providers = [OpenAIProvider()]
            elif provider_key == 'anthropic':
                self.providers = [AnthropicProvider()]
            elif provider_key == 'groq':
                self.providers = [GroqProvider()]
            elif provider_key in ('grok', 'xai'):
                self.providers = [GrokProvider()]
            else:
                print(f"      [WARN] Unknown provider: {preferred_provider}")
        else:
            # Auto-detect available providers
            # Pollinations FIRST (most reliable for vision), then others as fallback
            # Default to openai-large for strictly better vision performance
            poll_provider = PollinationsProvider(api_key=poll_key, model="openai-large")
            if poll_provider.available:
                self.providers.append(poll_provider)

            # Add other providers as fallbacks
            for ProviderClass in [GroqProvider, GeminiProvider, OpenAIProvider,
                                  AnthropicProvider, GrokProvider]:
                provider = ProviderClass()
                if provider.available:
                    self.providers.append(provider)

    @property
    def available(self) -> bool:
        return any(p.available for p in self.providers)

    @property
    def provider_name(self) -> str:
        for p in self.providers:
            if p.available:
                return p.name
        return "None"

    def _get_cache_key(self, img: Image.Image) -> str:
        """Generate cache key from image content"""
        import io
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return hashlib.md5(buffer.getvalue()).hexdigest()

    def _load_cache(self, cache_key: str) -> Optional[Dict]:
        """Load cached analysis result"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    data = json.load(f)
                    # Check if cache is recent (24 hours)
                    if 'timestamp' in data:
                        cache_time = datetime.fromisoformat(data['timestamp'])
                        age = datetime.now() - cache_time
                        if age.total_seconds() < 86400:  # 24 hours
                            return data.get('result')
            except Exception:
                pass
        return None

    def _save_cache(self, cache_key: str, result: Dict):
        """Save analysis result to cache"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'result': result
                }, f)
        except Exception:
            pass

    def analyze(self, img: Image.Image, sprites: List['SpriteInfo'],
               use_cache: bool = True, filename: str = None) -> Dict[str, Any]:
        """
        Analyze sprite sheet with AI, with caching and fallback.

        Args:
            img: Sprite sheet image
            sprites: List of detected sprites
            use_cache: Whether to use cached results
            filename: Original filename (used for fallback hints)
        """
        # In offline mode, skip to fallback immediately
        if self.offline_mode:
            print(f"      [OFFLINE] Skipping AI, using fallback analysis...")
            return self._use_fallback(img, sprites, filename)

        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key(img)
            cached = self._load_cache(cache_key)
            if cached:
                print(f"      [CACHE] Using cached AI analysis")
                return cached

        # Prepare sprite positions for prompt
        positions = [
            {'id': s.id, 'x': s.bbox.x, 'y': s.bbox.y, 'w': s.bbox.width, 'h': s.bbox.height}
            for s in sprites
        ]

        # Try providers in order
        result = {}
        for provider in self.providers:
            if not provider.available:
                continue

            print(f"      [AI] Using {provider.name}...")

            # Retry with exponential backoff
            for attempt in range(3):
                result = provider.analyze_sprites(img, len(sprites), positions)
                if result and result.get('sprites'):
                    # Success - cache and return
                    if use_cache:
                        self._save_cache(cache_key, result)
                    return result

                # Rate limit - wait and retry
                if attempt < 2:
                    wait_time = 2 ** attempt
                    print(f"      [RETRY] Waiting {wait_time}s...")
                    time.sleep(wait_time)

            # Provider failed, try next
            print(f"      [WARN] {provider.name} failed, trying next provider...")

        # All providers failed - use fallback if available
        if not result or not result.get('sprites'):
            result = self._use_fallback(img, sprites, filename)

        return result

    def _use_fallback(self, img: Image.Image, sprites: List['SpriteInfo'],
                      filename: str = None) -> Dict[str, Any]:
        """
        Use heuristic fallback when all AI providers fail.

        Returns basic sprite analysis based on size, position, and filename patterns.
        """
        try:
            from .fallback import FallbackAnalyzer
            print(f"      [FALLBACK] Using heuristic-based sprite analysis...")
            analyzer = FallbackAnalyzer()
            result = analyzer.analyze_sprites(img, sprites, filename)
            if result and result.get('sprites'):
                print(f"      [FALLBACK] Labeled {len(result['sprites'])} sprites using heuristics")
            return result
        except ImportError:
            print(f"      [WARN] Fallback module not available")
            return {}

    def analyze_prompt(self, img: Image.Image, prompt: str) -> Dict[str, Any]:
        """Generic analysis using available provider"""
        for provider in self.providers:
            if not provider.available:
                continue
            
            print(f"      [AI] Asking {provider.name}...")
            # Retry logic could be added here similar to analyze()
            try:
                res = provider.analyze_prompt(img, prompt)
                if res:
                    return res
            except Exception as e:
                print(f"      [WARN] {provider.name} failed prompt: {e}")
                
        return {}

    def analyze_parallel(self, img: Image.Image, sprites: List['SpriteInfo'], models: List[str]) -> Dict[str, Dict]:
        """
        Query multiple models in parallel (sequentially for now, but gathering all results).
        """
        results = {}
        
        # Prepare sprite positions once
        positions = [
            {'id': s.id, 'x': s.bbox.x, 'y': s.bbox.y, 'w': s.bbox.width, 'h': s.bbox.height}
            for s in sprites
        ]

        # Map string names to providers
        active_providers = []
        poll_key = os.getenv('POLLINATIONS_API_KEY') or self.DEFAULT_POLLINATIONS_KEY
        
        for model_name in models:
            # Create transient providers for consensus
            # Ideally we'd reuse, but this ensures we get specific models requested
            if 'openai' in model_name or 'gpt' in model_name:
                p = PollinationsProvider(api_key=poll_key, model=model_name)
            elif 'gemini' in model_name:
                p = PollinationsProvider(api_key=poll_key, model=model_name)
            elif 'claude' in model_name:
                p = PollinationsProvider(api_key=poll_key, model=model_name)
            else:
                 p = PollinationsProvider(api_key=poll_key, model=model_name)
            
            # We don't check .available here strictly in loop, but we assume key works if one worked
            active_providers.append((model_name, p))

        print(f"      [Consensus] Querying {len(active_providers)} models: {[m for m, p in active_providers]}")

        for i, (name, provider) in enumerate(active_providers):
            print(f"      [Consensus] ({i+1}/{len(active_providers)}) Asking {name}...")
            
            # Wait to avoid rate limits (User Request: Sequential with waits)
            if i > 0:
                print("      [Consensus] Waiting 2s before next API call...")
                time.sleep(2.0)
                
            try:
                # We do NOT use cache in consensus mode usually, or we use separate cache
                # For now, no cache for consensus
                res = provider.analyze_sprites(img, len(sprites), positions)
                if res and res.get('sprites'):
                    results[name] = res
                else:
                    print(f"      [Consensus] {name} returned empty/invalid result")
            except Exception as e:
                print(f"      [Consensus] {name} failed: {e}")

        return results

    def apply_labels(self, sprites: List[SpriteInfo], analysis: Dict) -> List[SpriteInfo]:
        """Apply AI-generated labels to sprites"""
        ai_sprites = analysis.get('sprites', [])

        for sprite in sprites:
            # Find matching AI label by ID
            for ai_info in ai_sprites:
                if ai_info.get('id') == sprite.id:
                    sprite.sprite_type = ai_info.get('type', sprite.sprite_type)
                    sprite.action = ai_info.get('action', sprite.action)
                    sprite.frame_index = ai_info.get('frame_index', sprite.frame_index)
                    desc = ai_info.get('description', '')
                    if desc:
                        sprite.description = desc
                    break

        return sprites

    def analyze_collision(self, sprite_img: Image.Image, sprite_type: str = "unknown",
                          sprite_width: int = None, sprite_height: int = None,
                          use_cache: bool = True) -> Dict[str, Any]:
        """
        Analyze a single sprite for collision boundaries using vision AI.

        This method sends a cropped sprite image to an AI vision model and asks it
        to identify appropriate hitbox (damage-dealing) and hurtbox (damage-receiving)
        collision boxes based on the sprite's visual content.

        Args:
            sprite_img: PIL Image of the cropped sprite (single frame)
            sprite_type: Type hint for the AI (e.g., "player", "enemy", "projectile")
            sprite_width: Override width (defaults to image width)
            sprite_height: Override height (defaults to image height)
            use_cache: Whether to use cached results

        Returns:
            Dict with collision data:
            {
                "hitbox": {"x": int, "y": int, "w": int, "h": int},
                "hurtbox": {"x": int, "y": int, "w": int, "h": int},
                "confidence": float (0.0-1.0),
                "reasoning": str
            }
        """
        width = sprite_width or sprite_img.width
        height = sprite_height or sprite_img.height

        # Check cache first
        if use_cache:
            cache_key = f"collision_{self._get_cache_key(sprite_img)}"
            cached = self._load_cache(cache_key)
            if cached:
                print(f"      [CACHE] Using cached collision analysis")
                return cached

        # Build collision-specific prompt
        prompt = f"""Analyze this sprite for collision detection in a 2D action game.

Sprite type: {sprite_type}
Sprite dimensions: {width}x{height} pixels

Identify two collision boxes as pixel coordinates relative to the sprite's top-left corner (0,0):

1. HITBOX: The area that deals damage (weapon, fist, projectile core, dangerous part)
   - Should be SMALLER than the full sprite
   - Only include the "dangerous" part that hurts enemies
   - For characters: the weapon or attacking limb
   - For projectiles: the core/center that causes damage
   - For items: can be the same as hurtbox

2. HURTBOX: The area that receives damage (body, vulnerable area)
   - Should cover the main body/mass of the sprite
   - Exclude visual effects: trails, glows, capes, shadows, weapon handles
   - This is where the sprite can BE hit

Return ONLY valid JSON (no markdown, no explanation outside JSON):
{{
    "hitbox": {{"x": <left offset from 0>, "y": <top offset from 0>, "w": <width>, "h": <height>}},
    "hurtbox": {{"x": <left offset from 0>, "y": <top offset from 0>, "w": <width>, "h": <height>}},
    "confidence": <0.0-1.0 how confident you are>,
    "reasoning": "<brief 1-sentence explanation of your box placement>"
}}

Important constraints:
- All values must be integers
- x + w must not exceed {width}
- y + h must not exceed {height}
- Boxes should be tight but not pixel-perfect (allow small margin)
- For idle/standing sprites, hitbox can equal hurtbox
- For attack frames, hitbox should cover the attack area"""

        # Try providers in order
        result = {}
        for provider in self.providers:
            if not provider.available:
                continue

            print(f"      [AI] Analyzing collision with {provider.name}...")

            # Retry with exponential backoff
            for attempt in range(3):
                try:
                    result = provider.analyze_prompt(sprite_img, prompt)

                    # Validate result has required fields
                    if result and 'hitbox' in result and 'hurtbox' in result:
                        # Ensure all required subfields exist
                        hitbox = result.get('hitbox', {})
                        hurtbox = result.get('hurtbox', {})

                        if all(k in hitbox for k in ['x', 'y', 'w', 'h']) and \
                           all(k in hurtbox for k in ['x', 'y', 'w', 'h']):
                            # Clamp values to valid range
                            result['hitbox'] = self._clamp_box(hitbox, width, height)
                            result['hurtbox'] = self._clamp_box(hurtbox, width, height)
                            result.setdefault('confidence', 0.8)
                            result.setdefault('reasoning', '')

                            # Cache and return
                            if use_cache:
                                self._save_cache(cache_key, result)
                            return result

                    print(f"      [WARN] Invalid collision response format, retrying...")

                except Exception as e:
                    print(f"      [WARN] Collision analysis error: {e}")

                # Rate limit - wait and retry
                if attempt < 2:
                    wait_time = 2 ** attempt
                    print(f"      [RETRY] Waiting {wait_time}s...")
                    time.sleep(wait_time)

            # Provider failed, try next
            print(f"      [WARN] {provider.name} failed collision analysis, trying next...")

        # All providers failed - return default boxes (full sprite)
        print(f"      [WARN] All providers failed - using default collision boxes")
        return self._default_collision(width, height, sprite_type)

    def _clamp_box(self, box: Dict[str, int], max_w: int, max_h: int) -> Dict[str, int]:
        """Clamp collision box values to valid sprite bounds."""
        x = max(0, min(int(box.get('x', 0)), max_w - 1))
        y = max(0, min(int(box.get('y', 0)), max_h - 1))
        w = max(1, min(int(box.get('w', max_w)), max_w - x))
        h = max(1, min(int(box.get('h', max_h)), max_h - y))
        return {'x': x, 'y': y, 'w': w, 'h': h}

    def _default_collision(self, width: int, height: int, sprite_type: str) -> Dict[str, Any]:
        """
        Generate default collision boxes when AI analysis fails.
        Uses type-specific heuristics based on common game design patterns.
        """
        # Type-specific defaults
        if sprite_type in ('player', 'enemy', 'npc'):
            # Characters: hitbox is 70% width centered, hurtbox is 80% full
            hb_w = int(width * 0.7)
            hb_h = int(height * 0.8)
            hb_x = (width - hb_w) // 2
            hb_y = int(height * 0.1)

            hurt_w = int(width * 0.8)
            hurt_h = int(height * 0.9)
            hurt_x = (width - hurt_w) // 2
            hurt_y = int(height * 0.05)

        elif sprite_type in ('projectile', 'bullet'):
            # Projectiles: small centered hitbox (50%)
            hb_w = int(width * 0.5)
            hb_h = int(height * 0.5)
            hb_x = (width - hb_w) // 2
            hb_y = (height - hb_h) // 2

            hurt_w, hurt_h = hb_w, hb_h
            hurt_x, hurt_y = hb_x, hb_y

        elif sprite_type in ('item', 'pickup'):
            # Items: 90% of sprite (generous pickup area)
            hb_w = int(width * 0.9)
            hb_h = int(height * 0.9)
            hb_x = (width - hb_w) // 2
            hb_y = (height - hb_h) // 2

            hurt_w, hurt_h = hb_w, hb_h
            hurt_x, hurt_y = hb_x, hb_y

        elif sprite_type == 'boss':
            # Bosses: larger hurtbox for easier hits
            hb_w = int(width * 0.6)
            hb_h = int(height * 0.6)
            hb_x = (width - hb_w) // 2
            hb_y = (height - hb_h) // 2

            hurt_w = int(width * 0.85)
            hurt_h = int(height * 0.85)
            hurt_x = (width - hurt_w) // 2
            hurt_y = (height - hurt_h) // 2

        else:
            # Unknown: conservative 80% box
            hb_w = int(width * 0.8)
            hb_h = int(height * 0.8)
            hb_x = (width - hb_w) // 2
            hb_y = (height - hb_h) // 2

            hurt_w, hurt_h = hb_w, hb_h
            hurt_x, hurt_y = hb_x, hb_y

        return {
            'hitbox': {'x': hb_x, 'y': hb_y, 'w': hb_w, 'h': hb_h},
            'hurtbox': {'x': hurt_x, 'y': hurt_y, 'w': hurt_w, 'h': hurt_h},
            'confidence': 0.3,  # Low confidence for defaults
            'reasoning': f'Default {sprite_type} collision (AI analysis failed)'
        }

    def generate_pixel_mask(self, sprite_img: Image.Image, threshold: int = 128) -> bytes:
        """
        Generate a 1-bit per-pixel collision mask from sprite alpha channel.

        Args:
            sprite_img: PIL Image (must have alpha channel or will use luminance)
            threshold: Alpha value above which pixel is considered solid (0-255)

        Returns:
            bytes: Packed 1-bit mask, 8 pixels per byte, row-major order
        """
        # Convert to RGBA if needed
        if sprite_img.mode != 'RGBA':
            sprite_img = sprite_img.convert('RGBA')

        width, height = sprite_img.size
        pixels = sprite_img.load()

        # Calculate bytes needed (round up to nearest byte per row)
        bytes_per_row = (width + 7) // 8
        mask_data = bytearray(bytes_per_row * height)

        for y in range(height):
            for x in range(width):
                # Check alpha channel
                alpha = pixels[x, y][3]
                if alpha >= threshold:
                    # Set bit for this pixel
                    byte_idx = y * bytes_per_row + (x // 8)
                    bit_idx = 7 - (x % 8)  # MSB first
                    mask_data[byte_idx] |= (1 << bit_idx)

        return bytes(mask_data)


class ConsensusEngine:
    """
    Validates AI results by cross-referencing multiple models.
    """
    def __init__(self, analyzer: AIAnalyzer):
        self.analyzer = analyzer
        self.models = ['openai-large', 'gemini-large', 'claude'] # Default set

    def resolve(self, img: Image.Image, sprites: List['SpriteInfo'], output_dir: str) -> Dict[str, Any]:
        """
        Run consensus logic: query models -> IoU match -> Vote -> Report
        """
        print(f"      [Consensus] Starting multi-model resolution with: {self.models}")
        results_map = self.analyzer.analyze_parallel(img, sprites, self.models)
        
        if not results_map:
            print("      [Consensus] All models failed!")
            return {'sprites': [], 'ai_failed': True}

        # Prepare report
        report_lines = ["Consensus Report", "="*50]
        report_lines.append(f"Models: {self.models}")
        report_lines.append(f"Successful Responses: {list(results_map.keys())}")
        
        # 1. Consolidate Bounding Boxes
        raw_candidates = [] 
        for model, res in results_map.items():
            for s in res.get('sprites', []):
                if 'bbox' in s:
                    # Parse bbox safely
                    bx = s['bbox']
                    if len(bx) == 4:
                        raw_candidates.append({
                            'model': model,
                            'bbox': BoundingBox(*bx),
                            'type': s.get('type', 'unknown'),
                            'data': s
                        })
        
        report_lines.append(f"Total candidates proposed: {len(raw_candidates)}")
        
        # 2. Clustering / Voting (IoU)
        groups = []
        used_indices = set()
        
        for i, c1 in enumerate(raw_candidates):
            if i in used_indices:
                continue
                
            current_group = [c1]
            used_indices.add(i)
            b1 = c1['bbox']
            
            for j, c2 in enumerate(raw_candidates):
                if i == j or j in used_indices:
                    continue
                
                b2 = c2['bbox']
                iou = self._calculate_iou(b1, b2)
                
                if iou > 0.6: # Overlay threshold
                    current_group.append(c2)
                    used_indices.add(j)
            
            groups.append(current_group)

        # 3. Evaluate Groups
        final_ai_sprites = []
        
        for grp in groups:
            # Vote count
            vote_count = len(grp)
            models_in_favor = [c['model'] for c in grp]
            
            # Form consensus box (average)
            avg_x = sum(c['bbox'].x for c in grp) // vote_count
            avg_y = sum(c['bbox'].y for c in grp) // vote_count
            avg_w = sum(c['bbox'].width for c in grp) // vote_count
            avg_h = sum(c['bbox'].height for c in grp) // vote_count
            
            consensus_box = BoundingBox(avg_x, avg_y, avg_w, avg_h)
            
            # Voting Logic
            status = "REJECTED"
            
            # If 2+ models agree, ACCEPT
            if vote_count >= 2:
                status = "ACCEPTED"
            # If only 1 model worked total, request manual review (or accept weakly)
            elif len(results_map) == 1:
                status = "ACCEPTED (Single Model)"
            # If 1 vote but multiple models ran -> REJECT (Hallucination likely)
            else:
                status = "REJECTED (No Consensus)"

            report_lines.append(f"Group @ {consensus_box}")
            report_lines.append(f"  Votes: {vote_count}/{len(self.models)} ({', '.join(models_in_favor)})")
            report_lines.append(f"  Status: {status}")
            
            if "ACCEPTED" in status:
                # Pick most frequent type
                types = [c['type'] for c in grp]
                from collections import Counter
                most_common_type = Counter(types).most_common(1)[0][0]
                
                # Create result entry
                base_data = grp[0]['data'].copy() # Use metadata from first voter
                base_data['type'] = most_common_type
                # Override bbox with consensus
                base_data['bbox'] = [consensus_box.x, consensus_box.y, consensus_box.width, consensus_box.height]
                
                final_ai_sprites.append(base_data)

        # 4. Save Report
        debug_dir = os.path.join(output_dir, "debug")
        os.makedirs(debug_dir, exist_ok=True)
        report_path = os.path.join(debug_dir, "consensus_report.txt")
        try:
            with open(report_path, "w") as f:
                f.write("\n".join(report_lines))
            print(f"      [Consensus] Report saved to {report_path}")
        except Exception as e:
            print(f"      [Warn] Failed to write report: {e}")

        # 5. Save Consensus Result
        return {'sprites': final_ai_sprites, 'ai_failed': len(final_ai_sprites) == 0}

    def _calculate_iou(self, b1: BoundingBox, b2: BoundingBox) -> float:
        x_left = max(b1.x, b2.x)
        y_top = max(b1.y, b2.y)
        x_right = min(b1.x + b1.width, b2.x + b2.width)
        y_bottom = min(b1.y + b1.height, b2.y + b2.height)

        if x_right < x_left or y_bottom < y_top:
            return 0.0

        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        area1 = b1.width * b1.height
        area2 = b2.width * b2.height
        
        # Avoid div by zero
        if area1 + area2 == 0: return 0.0
            
        union_area = area1 + area2 - intersection_area
        return intersection_area / union_area


# =============================================================================
# CONTENT-BASED SPRITE DETECTION
# =============================================================================

# =============================================================================
# CONTENT-BASED SPRITE DETECTION (IMPROVED)
# =============================================================================

