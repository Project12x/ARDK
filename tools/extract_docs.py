#!/usr/bin/env python3
"""
ARDK Documentation Extractor

Extracts structured documentation from C headers and assembly files,
generating markdown API reference.

Usage:
    python tools/extract_docs.py src/hal/hal.h -o docs/api/hal.md
    python tools/extract_docs.py src/hal/ -o docs/api/ --recursive
    python tools/extract_docs.py --all  # Process all ARDK sources
"""

import re
import argparse
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime


# =============================================================================
# Data Structures
# =============================================================================

@dataclass
class DocParam:
    """Function parameter documentation."""
    name: str
    description: str


@dataclass
class DocFunction:
    """Documented function or macro."""
    name: str
    signature: str
    brief: str = ""
    description: str = ""
    params: List[DocParam] = field(default_factory=list)
    returns: str = ""
    notes: List[str] = field(default_factory=list)
    platforms: List[str] = field(default_factory=list)
    see_also: List[str] = field(default_factory=list)
    example: str = ""
    source_file: str = ""
    line_number: int = 0


@dataclass
class DocType:
    """Documented type (struct, enum, typedef)."""
    name: str
    kind: str  # struct, enum, typedef
    brief: str = ""
    members: List[Tuple[str, str]] = field(default_factory=list)  # (name, description)


@dataclass
class DocMacro:
    """Documented macro."""
    name: str
    definition: str
    brief: str = ""
    params: List[str] = field(default_factory=list)


@dataclass
class DocSection:
    """A documentation section (grouped items)."""
    title: str
    description: str = ""
    functions: List[DocFunction] = field(default_factory=list)
    types: List[DocType] = field(default_factory=list)
    macros: List[DocMacro] = field(default_factory=list)


@dataclass
class DocFile:
    """Complete documentation for a file."""
    name: str
    path: str
    brief: str = ""
    description: str = ""
    sections: List[DocSection] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    platform_notes: List[str] = field(default_factory=list)


# =============================================================================
# Parsers
# =============================================================================

class CDocParser:
    """Parse documentation from C header files."""

    # File header pattern
    FILE_HEADER = re.compile(
        r'/\*\s*\n'
        r'\s*\*\s*=+\s*\n'
        r'\s*\*\s*ARDK.*?\n'
        r'\s*\*\s*(\S+)\s*-\s*(.*?)\n'
        r'\s*\*\s*=+\s*\n'
        r'(.*?)'
        r'\s*\*\s*=+\s*\n'
        r'\s*\*/',
        re.DOTALL
    )

    # Section banner pattern
    SECTION_BANNER = re.compile(
        r'/\*\s*=+\s*\n'
        r'\s*\*\s*(.*?)\n'
        r'(?:\s*\*\s*\n)?'
        r'(?:\s*\*\s*(.*?)\n)?'
        r'\s*\*\s*=+\s*\*/',
        re.DOTALL
    )

    # Doc comment pattern (/** ... */)
    DOC_COMMENT = re.compile(
        r'/\*\*\s*\n(.*?)\*/\s*\n',
        re.DOTALL
    )

    # Function declaration pattern
    FUNC_DECL = re.compile(
        r'^(\w[\w\s\*]+?)\s+(\w+)\s*\((.*?)\)\s*;',
        re.MULTILINE
    )

    # Macro definition pattern
    MACRO_DEF = re.compile(
        r'^#define\s+(\w+)(?:\((.*?)\))?\s+(.*?)(?:\\\n.*?)*$',
        re.MULTILINE
    )

    # Struct/enum pattern
    TYPE_DEF = re.compile(
        r'typedef\s+(struct|enum)\s*\{([^}]*)\}\s*(\w+)\s*;',
        re.DOTALL
    )

    def parse(self, content: str, filename: str) -> DocFile:
        """Parse a C header file."""
        doc = DocFile(name=Path(filename).stem, path=filename)

        # Parse file header
        header_match = self.FILE_HEADER.search(content)
        if header_match:
            doc.brief = header_match.group(2).strip()
            doc.description = self._clean_comment(header_match.group(3))

        # Find all doc comments and their following declarations
        current_section = DocSection(title="API Reference")

        lines = content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]

            # Check for section banner
            if '/* ==' in line or '/* --' in line:
                banner_text = self._extract_banner(lines, i)
                if banner_text:
                    if current_section.functions or current_section.types or current_section.macros:
                        doc.sections.append(current_section)
                    current_section = DocSection(
                        title=banner_text[0],
                        description=banner_text[1] if len(banner_text) > 1 else ""
                    )

            # Check for doc comment
            if '/**' in line:
                doc_text, end_line = self._extract_doc_comment(lines, i)
                if doc_text:
                    # Look for declaration after comment
                    decl_line = end_line + 1
                    while decl_line < len(lines) and not lines[decl_line].strip():
                        decl_line += 1

                    if decl_line < len(lines):
                        decl = lines[decl_line]

                        # Function declaration
                        func_match = self.FUNC_DECL.match(decl)
                        if func_match:
                            func = self._parse_function_doc(doc_text, func_match)
                            func.line_number = decl_line + 1
                            func.source_file = filename
                            current_section.functions.append(func)

                        # Macro
                        elif decl.startswith('#define'):
                            macro = self._parse_macro(decl, doc_text)
                            if macro:
                                current_section.macros.append(macro)

                    i = end_line

            i += 1

        # Add final section
        if current_section.functions or current_section.types or current_section.macros:
            doc.sections.append(current_section)

        # Parse types
        for match in self.TYPE_DEF.finditer(content):
            type_doc = DocType(
                name=match.group(3),
                kind=match.group(1),
                members=self._parse_struct_members(match.group(2))
            )
            if doc.sections:
                doc.sections[0].types.append(type_doc)

        return doc

    def _extract_doc_comment(self, lines: List[str], start: int) -> Tuple[str, int]:
        """Extract a doc comment starting at given line."""
        text = []
        i = start

        while i < len(lines):
            line = lines[i]
            if '/**' in line:
                # Start of comment
                after = line.split('/**')[1]
                if '*/' in after:
                    text.append(after.split('*/')[0])
                    return '\n'.join(text), i
                text.append(after)
            elif '*/' in line:
                text.append(line.split('*/')[0])
                return '\n'.join(text), i
            elif line.strip().startswith('*'):
                text.append(line.strip()[1:].strip())
            i += 1

        return '\n'.join(text), i

    def _extract_banner(self, lines: List[str], start: int) -> Optional[List[str]]:
        """Extract section banner text."""
        text = []
        i = start
        in_banner = False

        while i < len(lines):
            line = lines[i]
            if '====' in line or '----' in line:
                if in_banner:
                    return text if text else None
                in_banner = True
            elif in_banner and '*/' in line:
                return text if text else None
            elif in_banner and line.strip().startswith('*'):
                cleaned = line.strip()[1:].strip()
                if cleaned:
                    text.append(cleaned)
            i += 1

        return None

    def _parse_function_doc(self, doc_text: str, match: re.Match) -> DocFunction:
        """Parse function documentation."""
        return_type = match.group(1).strip()
        name = match.group(2)
        params_str = match.group(3)

        func = DocFunction(
            name=name,
            signature=f"{return_type} {name}({params_str})"
        )

        # Parse doc tags
        for line in doc_text.split('\n'):
            line = line.strip()
            if line.startswith('@brief'):
                func.brief = line[6:].strip()
            elif line.startswith('@param'):
                parts = line[6:].strip().split(None, 1)
                if len(parts) >= 2:
                    func.params.append(DocParam(parts[0], parts[1]))
                elif parts:
                    func.params.append(DocParam(parts[0], ""))
            elif line.startswith('@return'):
                func.returns = line[7:].strip()
            elif line.startswith('@note'):
                func.notes.append(line[5:].strip())
            elif line.startswith('@platform'):
                func.platforms.append(line[9:].strip())
            elif line.startswith('@see'):
                func.see_also.extend(line[4:].strip().split(','))
            elif line.startswith('@example'):
                func.example = line[8:].strip()
            elif not line.startswith('@') and line and not func.brief:
                func.brief = line

        return func

    def _parse_macro(self, decl: str, doc_text: str) -> Optional[DocMacro]:
        """Parse macro definition."""
        match = self.MACRO_DEF.match(decl)
        if not match:
            return None

        macro = DocMacro(
            name=match.group(1),
            definition=match.group(3).strip() if match.group(3) else "",
            params=match.group(2).split(',') if match.group(2) else []
        )

        for line in doc_text.split('\n'):
            line = line.strip()
            if not line.startswith('@') and line:
                macro.brief = line
                break

        return macro

    def _parse_struct_members(self, body: str) -> List[Tuple[str, str]]:
        """Parse struct/enum members."""
        members = []
        for line in body.split('\n'):
            line = line.strip()
            if line and not line.startswith('/*'):
                # Try to extract member name and any inline comment
                if '//' in line or '/*' in line:
                    parts = re.split(r'//|/\*', line, 1)
                    member = parts[0].strip().rstrip(';,')
                    comment = parts[1].strip().rstrip('*/')
                    members.append((member, comment))
                else:
                    member = line.rstrip(';,')
                    if member:
                        members.append((member, ""))
        return members

    def _clean_comment(self, text: str) -> str:
        """Clean comment block text."""
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            if line.startswith('*'):
                line = line[1:].strip()
            if line and not line.startswith('='):
                lines.append(line)
        return '\n'.join(lines)


class AsmDocParser:
    """Parse documentation from assembly files."""

    # Procedure header pattern
    PROC_HEADER = re.compile(
        r';-+\n'
        r'; (\w+)\s*(?:-\s*(.*?))?\n'
        r';?\n?'
        r'((?:;.*\n)*?)'
        r';-+\n'
        r'(?:\.proc\s+\1|MACRO\s+\1)',
        re.MULTILINE
    )

    def parse(self, content: str, filename: str) -> DocFile:
        """Parse an assembly file."""
        doc = DocFile(name=Path(filename).stem, path=filename)
        section = DocSection(title="Procedures and Macros")

        for match in self.PROC_HEADER.finditer(content):
            name = match.group(1)
            brief = match.group(2) or ""
            body = match.group(3) or ""

            func = DocFunction(
                name=name,
                signature=name,
                brief=brief,
                source_file=filename
            )

            # Parse body for INPUT/OUTPUT/CLOBBERS/CYCLES
            current_section = None
            for line in body.split('\n'):
                line = line.lstrip(';').strip()

                if line.startswith('INPUT:'):
                    current_section = 'input'
                elif line.startswith('OUTPUT:'):
                    current_section = 'output'
                elif line.startswith('CLOBBERS:'):
                    current_section = 'clobbers'
                elif line.startswith('CYCLES:'):
                    func.notes.append(f"Cycles: {line[7:].strip()}")
                    current_section = None
                elif current_section == 'input' and '=' in line:
                    parts = line.split('=', 1)
                    func.params.append(DocParam(parts[0].strip(), parts[1].strip()))
                elif current_section == 'output' and '=' in line:
                    func.returns += line + "; "

            section.functions.append(func)

        if section.functions:
            doc.sections.append(section)

        return doc


# =============================================================================
# Markdown Generator
# =============================================================================

class MarkdownGenerator:
    """Generate markdown from parsed documentation."""

    def generate(self, doc: DocFile) -> str:
        """Generate markdown for a file."""
        md = []

        # Title
        md.append(f"# {doc.name}\n")

        if doc.brief:
            md.append(f"**{doc.brief}**\n")

        if doc.description:
            md.append(f"\n{doc.description}\n")

        # Table of contents
        md.append("\n## Contents\n")
        for section in doc.sections:
            anchor = section.title.lower().replace(' ', '-')
            md.append(f"- [{section.title}](#{anchor})\n")

        # Sections
        for section in doc.sections:
            md.append(f"\n## {section.title}\n")

            if section.description:
                md.append(f"\n{section.description}\n")

            # Types
            if section.types:
                md.append("\n### Types\n")
                for t in section.types:
                    md.append(f"\n#### `{t.name}` ({t.kind})\n")
                    if t.brief:
                        md.append(f"{t.brief}\n")
                    if t.members:
                        md.append("\n| Member | Description |\n|--------|-------------|\n")
                        for name, desc in t.members:
                            md.append(f"| `{name}` | {desc} |\n")

            # Macros
            if section.macros:
                md.append("\n### Macros\n")
                for m in section.macros:
                    params = f"({', '.join(m.params)})" if m.params else ""
                    md.append(f"\n#### `{m.name}{params}`\n")
                    if m.brief:
                        md.append(f"{m.brief}\n")
                    if m.definition:
                        md.append(f"\n```c\n#define {m.name}{params} {m.definition}\n```\n")

            # Functions
            if section.functions:
                md.append("\n### Functions\n")
                for f in section.functions:
                    md.append(f"\n#### `{f.name}`\n")
                    md.append(f"\n```c\n{f.signature}\n```\n")

                    if f.brief:
                        md.append(f"\n{f.brief}\n")

                    if f.params:
                        md.append("\n**Parameters:**\n")
                        for p in f.params:
                            md.append(f"- `{p.name}` - {p.description}\n")

                    if f.returns:
                        md.append(f"\n**Returns:** {f.returns}\n")

                    if f.notes:
                        md.append("\n**Notes:**\n")
                        for note in f.notes:
                            md.append(f"- {note}\n")

                    if f.platforms:
                        md.append("\n**Platform Notes:**\n")
                        for plat in f.platforms:
                            md.append(f"- {plat}\n")

                    if f.see_also:
                        md.append(f"\n**See Also:** {', '.join(f'`{s.strip()}`' for s in f.see_also)}\n")

        # Footer
        md.append(f"\n---\n*Generated from `{doc.path}` on {datetime.now().strftime('%Y-%m-%d')}*\n")

        return ''.join(md)


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Extract documentation from ARDK source files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s src/hal/hal.h -o docs/api/hal.md
  %(prog)s src/hal/ -o docs/api/ --recursive
  %(prog)s --all
        """
    )

    parser.add_argument(
        "input",
        nargs="?",
        help="Input file or directory"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file or directory"
    )
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Process directories recursively"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all ARDK source files"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    c_parser = CDocParser()
    asm_parser = AsmDocParser()
    generator = MarkdownGenerator()

    def process_file(input_path: Path, output_path: Path):
        """Process a single file."""
        if args.verbose:
            print(f"Processing: {input_path}")

        content = input_path.read_text(encoding='utf-8', errors='replace')

        if input_path.suffix in ['.h', '.c']:
            doc = c_parser.parse(content, str(input_path))
        elif input_path.suffix in ['.asm', '.inc', '.s']:
            doc = asm_parser.parse(content, str(input_path))
        else:
            print(f"Skipping unknown file type: {input_path}")
            return

        markdown = generator.generate(doc)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding='utf-8')

        print(f"Generated: {output_path}")

    # Find project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    if args.all:
        # Process all HAL files
        hal_dir = project_root / "src" / "hal"
        output_dir = project_root / "docs" / "api"

        for f in hal_dir.glob("*.h"):
            output_path = output_dir / f"{f.stem}.md"
            process_file(f, output_path)

        for f in hal_dir.glob("*.c"):
            output_path = output_dir / f"{f.stem}.md"
            process_file(f, output_path)

        # Process ASM HAL
        asm_dir = hal_dir / "asm"
        if asm_dir.exists():
            for f in asm_dir.glob("*.inc"):
                output_path = output_dir / f"{f.stem}.md"
                process_file(f, output_path)

    elif args.input:
        input_path = Path(args.input)

        if input_path.is_file():
            if args.output:
                output_path = Path(args.output)
            else:
                output_path = input_path.with_suffix('.md')
            process_file(input_path, output_path)

        elif input_path.is_dir():
            output_dir = Path(args.output) if args.output else input_path

            pattern = "**/*" if args.recursive else "*"
            for f in input_path.glob(pattern):
                if f.suffix in ['.h', '.c', '.asm', '.inc', '.s']:
                    output_path = output_dir / f.relative_to(input_path).with_suffix('.md')
                    process_file(f, output_path)
    else:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
