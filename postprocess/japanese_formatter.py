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


class JapaneseNovelFormatter:
    """
    Main formatter class for vertical Japanese novels

    Applies configurable formatting rules to text files.
    Supports Phase 1 basic normalization rules.
    """

    # Default configuration for Phase 1
    DEFAULT_CONFIG = {
        "ellipsis": True,
        "dash": True,
        "tilde": True,
        "blank_lines": True,
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
        # Phase 1 rules
        available_rules = {
            "ellipsis": EllipsisNormalizer(),
            "dash": DashNormalizer(),
            "tilde": TildeNormalizer(),
            "blank_lines": BlankLineRemover(),
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
        description="Format Japanese vertical novels - Phase 1",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Format single file
  %(prog)s input.txt -o output.txt

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

    # Rule toggle options
    rule_group = parser.add_argument_group("formatting rules")
    rule_group.add_argument("--ellipsis", action="store_true", help="Enable ellipsis normalization (... → ……)")
    rule_group.add_argument("--dash", action="store_true", help="Enable dash normalization (-- → ――)")
    rule_group.add_argument("--tilde", action="store_true", help="Enable tilde normalization (~ → 〜)")
    rule_group.add_argument("--blank-lines", action="store_true", help="Enable blank line removal")

    parser.add_argument("--all", action="store_true", help="Enable all Phase 1 rules (default if no rules specified)")

    return parser.parse_args()


def main():
    """Main entry point for CLI"""
    args = parse_arguments()

    # Validate arguments
    if not args.dry_run and not args.output:
        print("Error: --output is required unless --dry-run is specified")
        return 1

    # Build configuration
    # If specific rules are specified, enable only those
    # Otherwise, enable all rules (Phase 1 default)
    if args.ellipsis or args.dash or args.tilde or args.blank_lines:
        config = {
            "ellipsis": args.ellipsis,
            "dash": args.dash,
            "tilde": args.tilde,
            "blank_lines": args.blank_lines,
        }
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
