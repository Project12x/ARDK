#!/usr/bin/env python3
"""
AI Code Optimization Advisor for NES Development

Analyzes 6502 assembly code and provides:
1. Cycle count estimates
2. Optimization suggestions
3. Memory usage analysis
4. Common pattern detection
5. Performance bottleneck identification

Uses Gemini AI for intelligent code analysis and suggestions.

Usage:
    python tools/ai_code_optimizer.py src/game/main.asm
    python tools/ai_code_optimizer.py --analyze-function update_player src/*.asm
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

try:
    from google import genai
    from google.genai import types
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

# 6502 instruction cycle counts (base cycles, not including page crossing)
INSTRUCTION_CYCLES = {
    # Load/Store
    'lda': {'imm': 2, 'zp': 3, 'zpx': 4, 'abs': 4, 'absx': 4, 'absy': 4, 'indx': 6, 'indy': 5},
    'ldx': {'imm': 2, 'zp': 3, 'zpy': 4, 'abs': 4, 'absy': 4},
    'ldy': {'imm': 2, 'zp': 3, 'zpx': 4, 'abs': 4, 'absx': 4},
    'sta': {'zp': 3, 'zpx': 4, 'abs': 4, 'absx': 5, 'absy': 5, 'indx': 6, 'indy': 6},
    'stx': {'zp': 3, 'zpy': 4, 'abs': 4},
    'sty': {'zp': 3, 'zpx': 4, 'abs': 4},

    # Arithmetic
    'adc': {'imm': 2, 'zp': 3, 'zpx': 4, 'abs': 4, 'absx': 4, 'absy': 4, 'indx': 6, 'indy': 5},
    'sbc': {'imm': 2, 'zp': 3, 'zpx': 4, 'abs': 4, 'absx': 4, 'absy': 4, 'indx': 6, 'indy': 5},
    'cmp': {'imm': 2, 'zp': 3, 'zpx': 4, 'abs': 4, 'absx': 4, 'absy': 4, 'indx': 6, 'indy': 5},
    'cpx': {'imm': 2, 'zp': 3, 'abs': 4},
    'cpy': {'imm': 2, 'zp': 3, 'abs': 4},

    # Increment/Decrement
    'inc': {'zp': 5, 'zpx': 6, 'abs': 6, 'absx': 7},
    'dec': {'zp': 5, 'zpx': 6, 'abs': 6, 'absx': 7},
    'inx': {'impl': 2},
    'iny': {'impl': 2},
    'dex': {'impl': 2},
    'dey': {'impl': 2},

    # Logical
    'and': {'imm': 2, 'zp': 3, 'zpx': 4, 'abs': 4, 'absx': 4, 'absy': 4, 'indx': 6, 'indy': 5},
    'ora': {'imm': 2, 'zp': 3, 'zpx': 4, 'abs': 4, 'absx': 4, 'absy': 4, 'indx': 6, 'indy': 5},
    'eor': {'imm': 2, 'zp': 3, 'zpx': 4, 'abs': 4, 'absx': 4, 'absy': 4, 'indx': 6, 'indy': 5},
    'bit': {'zp': 3, 'abs': 4},

    # Shift
    'asl': {'acc': 2, 'zp': 5, 'zpx': 6, 'abs': 6, 'absx': 7},
    'lsr': {'acc': 2, 'zp': 5, 'zpx': 6, 'abs': 6, 'absx': 7},
    'rol': {'acc': 2, 'zp': 5, 'zpx': 6, 'abs': 6, 'absx': 7},
    'ror': {'acc': 2, 'zp': 5, 'zpx': 6, 'abs': 6, 'absx': 7},

    # Branch (base cycles, +1 if taken, +2 if page cross)
    'bcc': {'rel': 2},
    'bcs': {'rel': 2},
    'beq': {'rel': 2},
    'bne': {'rel': 2},
    'bmi': {'rel': 2},
    'bpl': {'rel': 2},
    'bvc': {'rel': 2},
    'bvs': {'rel': 2},

    # Jump/Call
    'jmp': {'abs': 3, 'ind': 5},
    'jsr': {'abs': 6},
    'rts': {'impl': 6},
    'rti': {'impl': 6},

    # Stack
    'pha': {'impl': 3},
    'pla': {'impl': 4},
    'php': {'impl': 3},
    'plp': {'impl': 4},

    # Transfer
    'tax': {'impl': 2},
    'tay': {'impl': 2},
    'txa': {'impl': 2},
    'tya': {'impl': 2},
    'tsx': {'impl': 2},
    'txs': {'impl': 2},

    # Flags
    'clc': {'impl': 2},
    'sec': {'impl': 2},
    'cli': {'impl': 2},
    'sei': {'impl': 2},
    'cld': {'impl': 2},
    'sed': {'impl': 2},
    'clv': {'impl': 2},

    # Other
    'nop': {'impl': 2},
    'brk': {'impl': 7},
}

@dataclass
class CodeBlock:
    """A block of code for analysis"""
    name: str
    start_line: int
    end_line: int
    lines: List[str]
    estimated_cycles: int = 0
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

@dataclass
class AnalysisResult:
    """Complete analysis result"""
    filename: str
    total_instructions: int
    estimated_cycles: int
    zeropage_usage: int
    blocks: List[CodeBlock]
    global_issues: List[str] = field(default_factory=list)
    global_suggestions: List[str] = field(default_factory=list)


class AICodeOptimizer:
    """AI-powered code optimization advisor"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.client = None

        if HAS_GEMINI and self.api_key:
            self.client = genai.Client(api_key=self.api_key)

    def analyze_file(self, filepath: str) -> AnalysisResult:
        """Analyze an assembly file"""

        with open(filepath, 'r') as f:
            content = f.read()
            lines = content.split('\n')

        result = AnalysisResult(
            filename=Path(filepath).name,
            total_instructions=0,
            estimated_cycles=0,
            zeropage_usage=0,
            blocks=[]
        )

        # Find code blocks (procedures)
        blocks = self._find_code_blocks(lines)

        for block in blocks:
            self._analyze_block(block)
            result.blocks.append(block)
            result.total_instructions += len([l for l in block.lines if self._is_instruction(l)])
            result.estimated_cycles += block.estimated_cycles

        # Count zeropage usage
        result.zeropage_usage = self._count_zeropage(lines)

        # Global analysis
        result.global_issues = self._find_global_issues(lines)

        # AI-powered suggestions if available
        if self.client and len(content) < 50000:
            ai_suggestions = self._ai_analyze(content)
            result.global_suggestions.extend(ai_suggestions)

        return result

    def _find_code_blocks(self, lines: List[str]) -> List[CodeBlock]:
        """Find procedure blocks in code"""

        blocks = []
        current_block = None

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Start of procedure
            if stripped.startswith('.proc '):
                name = stripped.split()[1] if len(stripped.split()) > 1 else 'unknown'
                current_block = CodeBlock(name=name, start_line=i, end_line=i, lines=[])

            # End of procedure
            elif stripped == '.endproc':
                if current_block:
                    current_block.end_line = i
                    blocks.append(current_block)
                    current_block = None

            # Add line to current block
            if current_block:
                current_block.lines.append(line)

            # Also detect label-style procedures
            elif ':' in stripped and not stripped.startswith(';'):
                label = stripped.split(':')[0].strip()
                if label and not label.startswith('.') and not label.startswith('@'):
                    # Might be a procedure start
                    pass  # Could add detection logic here

        return blocks

    def _analyze_block(self, block: CodeBlock):
        """Analyze a single code block"""

        cycles = 0
        branch_count = 0
        jsr_count = 0

        for line in block.lines:
            stripped = line.strip().lower()

            # Skip comments and directives
            if not stripped or stripped.startswith(';') or stripped.startswith('.'):
                continue

            # Remove comments
            if ';' in stripped:
                stripped = stripped.split(';')[0].strip()

            # Parse instruction
            parts = stripped.split()
            if not parts:
                continue

            # Handle labels
            if ':' in parts[0]:
                parts = parts[1:] if len(parts) > 1 else []

            if not parts:
                continue

            opcode = parts[0]
            operand = parts[1] if len(parts) > 1 else ''

            # Count cycles
            if opcode in INSTRUCTION_CYCLES:
                mode = self._get_addressing_mode(operand)
                if mode in INSTRUCTION_CYCLES[opcode]:
                    cycles += INSTRUCTION_CYCLES[opcode][mode]
                else:
                    # Default to most common
                    cycles += min(INSTRUCTION_CYCLES[opcode].values())

            # Track patterns
            if opcode.startswith('b') and opcode != 'bit' and opcode != 'brk':
                branch_count += 1
            if opcode == 'jsr':
                jsr_count += 1

        block.estimated_cycles = cycles

        # Add issues based on analysis
        if cycles > 1000:
            block.issues.append(f"High cycle count ({cycles}) - may cause frame timing issues")

        if branch_count > 10:
            block.issues.append(f"Many branches ({branch_count}) - consider restructuring")

        if jsr_count > 5:
            block.issues.append(f"Many JSR calls ({jsr_count}) - consider inlining hot paths")

        # Add suggestions
        self._add_pattern_suggestions(block)

    def _get_addressing_mode(self, operand: str) -> str:
        """Determine addressing mode from operand"""

        if not operand:
            return 'impl'

        operand = operand.lower()

        if operand.startswith('#'):
            return 'imm'
        if operand.startswith('(') and operand.endswith(',x)'):
            return 'indx'
        if operand.startswith('(') and operand.endswith('),y'):
            return 'indy'
        if operand.startswith('(') and operand.endswith(')'):
            return 'ind'
        if operand.endswith(',x'):
            # Could be zpx or absx
            base = operand[:-2]
            if self._is_zeropage(base):
                return 'zpx'
            return 'absx'
        if operand.endswith(',y'):
            base = operand[:-2]
            if self._is_zeropage(base):
                return 'zpy'
            return 'absy'
        if operand == 'a':
            return 'acc'

        # Zeropage vs absolute
        if self._is_zeropage(operand):
            return 'zp'
        return 'abs'

    def _is_zeropage(self, operand: str) -> bool:
        """Check if operand is likely a zeropage address"""

        # Numeric
        if operand.startswith('$'):
            try:
                val = int(operand[1:], 16)
                return val < 256
            except:
                pass

        if operand.isdigit():
            return int(operand) < 256

        # Common zeropage variable names
        zp_hints = ['temp', 'ptr', 'counter', 'index', 'frame', 'button']
        return any(hint in operand.lower() for hint in zp_hints)

    def _is_instruction(self, line: str) -> bool:
        """Check if line is an instruction"""

        stripped = line.strip().lower()
        if not stripped or stripped.startswith(';') or stripped.startswith('.'):
            return False

        if ';' in stripped:
            stripped = stripped.split(';')[0].strip()

        parts = stripped.split()
        if parts and ':' in parts[0]:
            parts = parts[1:] if len(parts) > 1 else []

        if not parts:
            return False

        return parts[0] in INSTRUCTION_CYCLES

    def _add_pattern_suggestions(self, block: CodeBlock):
        """Add suggestions based on detected patterns"""

        code = '\n'.join(block.lines).lower()

        # Pattern: repeated loads
        if code.count('lda') > 5 and code.count('sta') > 5:
            block.suggestions.append("Consider using X/Y registers to reduce LDA/STA pairs")

        # Pattern: division by power of 2
        if 'jsr div' in code or 'jsr divide' in code:
            block.suggestions.append("Check if division can be replaced with LSR shifts")

        # Pattern: multiplication
        if 'jsr mul' in code or 'jsr mult' in code:
            block.suggestions.append("Check if multiplication can use ASL/ADD for small constants")

        # Pattern: slow indirect indexed
        if code.count('(') > 3:
            block.suggestions.append("Heavy indirect addressing - consider restructuring data")

        # Pattern: pushing/pulling in loop
        if 'pha' in code and 'pla' in code:
            if '@' in code or 'loop' in code:
                block.suggestions.append("PHA/PLA in loop - consider using registers instead")

    def _count_zeropage(self, lines: List[str]) -> int:
        """Count zeropage variable declarations"""

        count = 0
        in_zeropage = False

        for line in lines:
            stripped = line.strip().lower()

            if '.segment "zeropage"' in stripped:
                in_zeropage = True
            elif '.segment' in stripped:
                in_zeropage = False

            if in_zeropage and '.res' in stripped:
                # Extract reservation count
                match = re.search(r'\.res\s+(\d+)', stripped)
                if match:
                    count += int(match.group(1))

        return count

    def _find_global_issues(self, lines: List[str]) -> List[str]:
        """Find global code issues"""

        issues = []
        code = '\n'.join(lines)

        # Check for common issues
        if 'jsr FamiToneUpdate' not in code and 'famitone' in code.lower():
            issues.append("FamiTone included but FamiToneUpdate not called?")

        if '$2007' in code:
            # VRAM access
            vram_reads = code.count('lda $2007')
            vram_writes = code.count('sta $2007')
            if vram_reads > 0:
                issues.append(f"Direct VRAM reads ({vram_reads}) - ensure vblank timing")
            if vram_writes > 100:
                issues.append(f"Many VRAM writes ({vram_writes}) - consider buffering")

        if 'cli' in code and 'sei' not in code:
            issues.append("CLI without SEI - interrupts may cause issues")

        return issues

    def _ai_analyze(self, code: str) -> List[str]:
        """Use AI for advanced optimization suggestions"""

        prompt = f"""Analyze this 6502 NES assembly code for optimization opportunities.

Focus on:
1. Cycle-critical sections (NMI handlers, raster effects)
2. Memory access patterns
3. Register usage efficiency
4. Common NES-specific optimizations
5. Potential bugs or timing issues

Code:
```
{code[:8000]}  # Truncate for API
```

Return 3-5 specific, actionable optimization suggestions.
Each suggestion should reference specific code patterns you see.
Format as a JSON array of strings.
"""

        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[prompt]
            )

            text = response.text

            if '```json' in text:
                text = text.split('```json')[1].split('```')[0]
            elif '```' in text:
                text = text.split('```')[1].split('```')[0]
            elif '[' in text:
                # Try to extract JSON array
                start = text.find('[')
                end = text.rfind(']') + 1
                text = text[start:end]

            suggestions = json.loads(text.strip())
            return suggestions if isinstance(suggestions, list) else []

        except Exception as e:
            print(f"AI analysis failed: {e}")
            return []

    def analyze_function(self, filepath: str, function_name: str) -> Optional[CodeBlock]:
        """Analyze a specific function"""

        with open(filepath, 'r') as f:
            lines = f.read().split('\n')

        blocks = self._find_code_blocks(lines)

        for block in blocks:
            if block.name == function_name:
                self._analyze_block(block)

                # Detailed AI analysis for single function
                if self.client:
                    code = '\n'.join(block.lines)
                    suggestions = self._ai_analyze(code)
                    block.suggestions.extend(suggestions)

                return block

        return None


def format_report(result: AnalysisResult) -> str:
    """Format analysis result as readable report"""

    lines = [
        "=" * 60,
        f"CODE ANALYSIS REPORT: {result.filename}",
        "=" * 60,
        "",
        f"Total Instructions: {result.total_instructions}",
        f"Estimated Cycles: {result.estimated_cycles}",
        f"Zeropage Usage: {result.zeropage_usage} bytes",
        f"Procedures Found: {len(result.blocks)}",
        "",
    ]

    if result.global_issues:
        lines.append("GLOBAL ISSUES:")
        for issue in result.global_issues:
            lines.append(f"  ! {issue}")
        lines.append("")

    if result.global_suggestions:
        lines.append("AI SUGGESTIONS:")
        for suggestion in result.global_suggestions:
            lines.append(f"  * {suggestion}")
        lines.append("")

    lines.append("-" * 60)
    lines.append("PROCEDURE ANALYSIS:")
    lines.append("-" * 60)

    for block in result.blocks:
        lines.append(f"\n{block.name} (lines {block.start_line}-{block.end_line})")
        lines.append(f"  Estimated cycles: {block.estimated_cycles}")

        if block.issues:
            for issue in block.issues:
                lines.append(f"  ! {issue}")

        if block.suggestions:
            for suggestion in block.suggestions:
                lines.append(f"  * {suggestion}")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='AI Code Optimization Advisor')
    parser.add_argument('files', nargs='+', help='Assembly files to analyze')
    parser.add_argument('--analyze-function', '-f', help='Analyze specific function')
    parser.add_argument('--output', '-o', help='Output report file')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    api_key = os.getenv('GEMINI_API_KEY')
    optimizer = AICodeOptimizer(api_key)

    if not api_key:
        print("Note: GEMINI_API_KEY not set. Using basic analysis only.")
        print()

    results = []

    for filepath in args.files:
        if not Path(filepath).exists():
            print(f"File not found: {filepath}")
            continue

        if args.analyze_function:
            block = optimizer.analyze_function(filepath, args.analyze_function)
            if block:
                print(f"\nFunction: {block.name}")
                print(f"Estimated cycles: {block.estimated_cycles}")
                print("\nIssues:")
                for issue in block.issues:
                    print(f"  ! {issue}")
                print("\nSuggestions:")
                for suggestion in block.suggestions:
                    print(f"  * {suggestion}")
        else:
            print(f"Analyzing: {filepath}")
            result = optimizer.analyze_file(filepath)
            results.append(result)

            report = format_report(result)
            print(report)

    if args.output and results:
        with open(args.output, 'w') as f:
            if args.json:
                json.dump([{
                    'filename': r.filename,
                    'total_instructions': r.total_instructions,
                    'estimated_cycles': r.estimated_cycles,
                    'zeropage_usage': r.zeropage_usage,
                    'blocks': [{
                        'name': b.name,
                        'cycles': b.estimated_cycles,
                        'issues': b.issues,
                        'suggestions': b.suggestions
                    } for b in r.blocks],
                    'global_issues': r.global_issues,
                    'global_suggestions': r.global_suggestions
                } for r in results], f, indent=2)
            else:
                for result in results:
                    f.write(format_report(result))
                    f.write('\n\n')

        print(f"\nReport saved to: {args.output}")


if __name__ == '__main__':
    main()
