#!/usr/bin/env python3
"""
Japanese Novel Formatter - Phase 1 Implementation

This module provides text formatting for Japanese vertical novels.
Implements basic normalization rules for punctuation and spacing.
"""

import argparse
import re
from pathlib import Path
from typing import Dict, List, Optional


class FormattingRule:
    """
    Base class for formatting rules
    """

    def __init__(self, name: str, priority: int):
        """
        Initialize formatting rule

        Args:
            name: Rule identifier
            priority: Execution priority (lower = earlier)
        """
        self.name = name
        self.priority = priority

    def apply(self, text: str) -> str:
        """
        Apply the rule to text

        Args:
            text: Input text

        Returns:
            Transformed text
        """
        raise NotImplementedError(f"Rule {self.name} must implement apply()")


class EllipsisNormalizer(FormattingRule):
    """Normalize ellipsis to 「……」"""

    def __init__(self):
        super().__init__("ellipsis", priority=1)

    def apply(self, text: str) -> str:
        """
        Normalize various ellipsis forms to standard format

        Transformations:
        - ... → ……
        - … → ……

        Note: Use placeholder to avoid cascading replacements
        """
        # Use a temporary placeholder to avoid double conversion
        PLACEHOLDER = "\x00ELLIPSIS\x00"

        # Replace three dots with placeholder
        text = text.replace("...", PLACEHOLDER)
        # Replace single horizontal ellipsis with placeholder
        text = text.replace("…", PLACEHOLDER)
        # Replace all placeholders with double horizontal ellipsis
        text = text.replace(PLACEHOLDER, "……")

        return text


class DashNormalizer(FormattingRule):
    """Normalize dash to 「――」"""

    def __init__(self):
        super().__init__("dash", priority=2)

    def apply(self, text: str) -> str:
        """
        Normalize various dash forms to standard format

        Transformations:
        - -- or --- → ――
        - — (em dash) → ――
        """
        # Replace multiple hyphens with double horizontal bar
        text = re.sub(r"-{2,}", "――", text)
        # Replace em dash with double horizontal bar
        text = text.replace("—", "――")
        return text


class TildeNormalizer(FormattingRule):
    """Normalize tilde to 「〜」"""

    def __init__(self):
        super().__init__("tilde", priority=3)

    def apply(self, text: str) -> str:
        """
        Normalize various tilde forms to standard format

        Transformations:
        - ~ → 〜
        - ～ (full-width tilde) → 〜 (wave dash)
        """
        # Replace ASCII tilde with wave dash
        text = text.replace("~", "〜")
        # Replace full-width tilde with wave dash
        text = text.replace("～", "〜")
        return text


class BlankLineRemover(FormattingRule):
    """Remove excessive blank lines"""

    def __init__(self):
        super().__init__("blank_lines", priority=4)

    def apply(self, text: str) -> str:
        """
        Remove excessive consecutive blank lines

        Transformations:
        - 3+ consecutive newlines → 2 newlines (1 blank line)
        """
        # Replace 3 or more consecutive newlines with exactly 2
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text


# === Phase 2 Rules (Medium) ===


class ParagraphIndenter(FormattingRule):
    """Add full-width space indentation to paragraphs"""

    def __init__(self):
        super().__init__("paragraph_indent", priority=5)

    def apply(self, text: str) -> str:
        """
        Add full-width space indentation to paragraph beginnings

        Rules:
        - Add 「　」(full-width space) at the start of narrative paragraphs
        - Skip dialogue lines (lines starting with 「)
        - Skip lines that already have indentation
        - Skip empty lines
        """
        lines = text.split("\n")
        result = []

        for line in lines:
            # Skip empty lines
            if not line.strip():
                result.append(line)
                continue

            # Skip lines starting with 「 (dialogue)
            if line.strip().startswith("「"):
                result.append(line)
                continue

            # Add indentation if not already present
            if not line.startswith("　"):
                result.append("　" + line)
            else:
                result.append(line)

        return "\n".join(result)


class HalfWidthConverter(FormattingRule):
    """Convert full-width to half-width for specific cases"""

    def __init__(self):
        super().__init__("halfwidth_convert", priority=6)

    def apply(self, text: str) -> str:
        """
        Convert full-width characters to half-width for specific cases

        Rules:
        - Convert full-width alphanumeric to half-width
        - Keep 1-2 digit numbers in half-width (tate-chu-yoko)
        - Convert 3+ digit numbers to full-width
        - Western text (consecutive alphabets) remains half-width
        """
        # First convert all full-width alphanumeric to half-width
        text = self._convert_alphanumeric(text)
        # Then selectively convert 3+ digit numbers back to full-width
        text = self._handle_numbers(text)
        return text

    def _convert_alphanumeric(self, text: str) -> str:
        """
        Convert full-width ASCII characters to half-width

        Converts characters in Unicode range U+FF01-U+FF5E
        (full-width ASCII variants) to their half-width equivalents
        """
        result = []
        for char in text:
            code = ord(char)
            # Full-width ASCII range (0xFF01-0xFF5E)
            if 0xFF01 <= code <= 0xFF5E:
                # Convert to half-width by subtracting offset
                result.append(chr(code - 0xFEE0))
            else:
                result.append(char)
        return "".join(result)

    def _handle_numbers(self, text: str) -> str:
        """
        Keep 1-2 digit numbers half-width, convert 3+ digits to full-width

        This follows the tate-chu-yoko convention where short numbers
        are displayed horizontally in vertical text.
        """

        def replace_numbers(match):
            num = match.group(0)
            if len(num) <= 2:
                # Keep half-width for tate-chu-yoko
                return num
            else:
                # Convert to full-width for longer numbers
                return "".join(chr(ord(c) + 0xFEE0) if "0" <= c <= "9" else c for c in num)

        return re.sub(r"\d+", replace_numbers, text)


class EnvironmentCharRemover(FormattingRule):
    """Remove environment-dependent characters"""

    # List of prohibited environment-dependent characters
    PROHIBITED_CHARS = {
        "①",
        "②",
        "③",
        "④",
        "⑤",
        "⑥",
        "⑦",
        "⑧",
        "⑨",
        "⑩",
        "㈱",
        "㈲",
        "㈹",
        "№",
        "㏍",
        "℡",
    }

    # Mapping of environment-dependent characters to standard replacements
    REPLACEMENT_MAP = {
        "①": "(1)",
        "②": "(2)",
        "③": "(3)",
        "④": "(4)",
        "⑤": "(5)",
        "⑥": "(6)",
        "⑦": "(7)",
        "⑧": "(8)",
        "⑨": "(9)",
        "⑩": "(10)",
        "㈱": "株式会社",
        "㈲": "有限会社",
        "㈹": "代表",
        "№": "No.",
        "㏍": "K.K.",
        "℡": "TEL",
    }

    def __init__(self):
        super().__init__("remove_env_chars", priority=7)

    def apply(self, text: str) -> str:
        """
        Replace environment-dependent characters with standard equivalents

        Replaces circled numbers, corporate symbols, and other
        environment-dependent characters that may not display
        correctly across different systems or fonts.
        """
        result = text
        for char, replacement in self.REPLACEMENT_MAP.items():
            result = result.replace(char, replacement)
        return result


class JapaneseNovelFormatter:
    """
    Main formatter class for vertical Japanese novels

    Applies configurable formatting rules to text files.
    Supports Phase 1 and Phase 2 rules.
    """

    # Default configuration for Phase 1
    DEFAULT_CONFIG = {
        "ellipsis": True,
        "dash": True,
        "tilde": True,
        "blank_lines": True,
    }

    # Configuration for Phase 2 (includes Phase 1)
    PHASE2_CONFIG = {
        # Phase 1 rules
        "ellipsis": True,
        "dash": True,
        "tilde": True,
        "blank_lines": True,
        # Phase 2 rules
        "paragraph_indent": True,
        "halfwidth_convert": True,
        "remove_env_chars": True,
    }

    def __init__(self, config: Optional[Dict[str, bool]] = None):
        """
        Initialize formatter with configuration

        Args:
            config: Configuration dict with rule toggles.
                   If None, uses default config (all Phase 1 rules enabled).
        """
        self.config = config if config is not None else self.DEFAULT_CONFIG.copy()
        self.rules: List[FormattingRule] = []
        self._setup_rules()

    def _setup_rules(self):
        """Initialize and register all formatting rules"""
        # All available rules (Phase 1 + Phase 2)
        available_rules = {
            # Phase 1 rules
            "ellipsis": EllipsisNormalizer(),
            "dash": DashNormalizer(),
            "tilde": TildeNormalizer(),
            "blank_lines": BlankLineRemover(),
            # Phase 2 rules
            "paragraph_indent": ParagraphIndenter(),
            "halfwidth_convert": HalfWidthConverter(),
            "remove_env_chars": EnvironmentCharRemover(),
        }

        # Register enabled rules
        for rule_name, rule_instance in available_rules.items():
            if self.config.get(rule_name, False):
                self.rules.append(rule_instance)

        # Sort rules by priority
        self.rules.sort(key=lambda r: r.priority)

    def format(self, text: str) -> str:
        """
        Apply all enabled formatting rules

        Args:
            text: Input text string

        Returns:
            Formatted text string
        """
        result = text
        for rule in self.rules:
            result = rule.apply(result)
        return result

    def format_file(self, input_path: Path, output_path: Path):
        """
        Format a text file

        Args:
            input_path: Path to input text file
            output_path: Path to output text file
        """
        # Read input file
        text = input_path.read_text(encoding="utf-8")

        # Apply formatting
        formatted = self.format(text)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write output file
        output_path.write_text(formatted, encoding="utf-8")


def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Format Japanese vertical novels - Phase 1 & 2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Format single file with Phase 1 rules
  %(prog)s input.txt -o output.txt

  # Format with Phase 2 rules (includes Phase 1)
  %(prog)s input.txt -o output.txt --phase 2

  # Format multiple files to directory
  %(prog)s data_generated/羅生門/*.txt -o formatted/

  # Enable specific rules only
  %(prog)s input.txt --ellipsis --dash -o output.txt

  # Dry run (show changes without writing)
  %(prog)s input.txt --dry-run
        """,
    )

    parser.add_argument("input", type=str, nargs="+", help="Input text file(s) to format")

    parser.add_argument("-o", "--output", type=str, help="Output file or directory (required unless --dry-run)")

    parser.add_argument("--dry-run", action="store_true", help="Show formatted output without writing files")

    parser.add_argument(
        "--phase", type=int, choices=[1, 2], help="Enable all rules up to phase N (1: basic, 2: medium)"
    )

    # Rule toggle options
    rule_group = parser.add_argument_group("formatting rules (Phase 1)")
    rule_group.add_argument("--ellipsis", action="store_true", help="Enable ellipsis normalization (... → ……)")
    rule_group.add_argument("--dash", action="store_true", help="Enable dash normalization (-- → ――)")
    rule_group.add_argument("--tilde", action="store_true", help="Enable tilde normalization (~ → 〜)")
    rule_group.add_argument("--blank-lines", action="store_true", help="Enable blank line removal")

    # Phase 2 rule options
    phase2_group = parser.add_argument_group("formatting rules (Phase 2)")
    phase2_group.add_argument("--paragraph-indent", action="store_true", help="Enable paragraph indentation")
    phase2_group.add_argument("--halfwidth-convert", action="store_true", help="Enable half-width conversion")
    phase2_group.add_argument(
        "--remove-env-chars", action="store_true", help="Enable environment-dependent character removal"
    )

    return parser.parse_args()


def main():
    """Main entry point for CLI"""
    args = parse_arguments()

    # Validate arguments
    if not args.dry_run and not args.output:
        print("Error: --output is required unless --dry-run is specified")
        return 1

    # Build configuration
    # Priority: specific rules > phase flag > default (Phase 1)
    has_specific_rules = (
        args.ellipsis
        or args.dash
        or args.tilde
        or args.blank_lines
        or args.paragraph_indent
        or args.halfwidth_convert
        or args.remove_env_chars
    )

    if has_specific_rules:
        # Use specific rules only
        config = {
            # Phase 1 rules
            "ellipsis": args.ellipsis,
            "dash": args.dash,
            "tilde": args.tilde,
            "blank_lines": args.blank_lines,
            # Phase 2 rules
            "paragraph_indent": args.paragraph_indent,
            "halfwidth_convert": args.halfwidth_convert,
            "remove_env_chars": args.remove_env_chars,
        }
    elif args.phase == 2:
        # Enable all Phase 2 rules (includes Phase 1)
        config = JapaneseNovelFormatter.PHASE2_CONFIG.copy()
    else:
        # Default: enable all Phase 1 rules
        config = JapaneseNovelFormatter.DEFAULT_CONFIG.copy()

    # Initialize formatter
    formatter = JapaneseNovelFormatter(config=config)

    # Process input files
    input_paths = [Path(f) for f in args.input]

    # Expand glob patterns
    expanded_paths = []
    for path in input_paths:
        if path.exists():
            expanded_paths.append(path)
        else:
            # Try glob expansion
            parent = path.parent
            pattern = path.name
            matches = list(parent.glob(pattern))
            expanded_paths.extend(matches)

    if not expanded_paths:
        print(f"Error: No input files found matching: {args.input}")
        return 1

    # Determine output mode
    output_path = Path(args.output) if args.output else None

    # Single file mode
    if len(expanded_paths) == 1 and not args.dry_run:
        input_file = expanded_paths[0]

        if output_path and output_path.is_dir():
            # Output to directory with same filename
            output_file = output_path / input_file.name
        else:
            # Output to specified file
            output_file = output_path

        print(f"Formatting: {input_file} → {output_file}")
        formatter.format_file(input_file, output_file)
        print("✓ Done")

    # Multiple file mode or dry-run
    else:
        for input_file in expanded_paths:
            if args.dry_run:
                # Dry run: print formatted output
                text = input_file.read_text(encoding="utf-8")
                formatted = formatter.format(text)
                print(f"\n{'='*60}")
                print(f"File: {input_file}")
                print(f"{'='*60}")
                print(formatted)
            else:
                # Write to output directory
                if not output_path or not output_path.is_dir():
                    print("Error: Multiple input files require --output to be a directory")
                    return 1

                output_file = output_path / input_file.name
                print(f"Formatting: {input_file} → {output_file}")
                formatter.format_file(input_file, output_file)

        if not args.dry_run:
            print(f"✓ Formatted {len(expanded_paths)} file(s)")

    return 0


if __name__ == "__main__":
    exit(main())
