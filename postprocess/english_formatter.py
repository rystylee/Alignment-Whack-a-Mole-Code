#!/usr/bin/env python3
"""
English Novel Formatter

This module provides text formatting for English novels.
Implements smart quotes, dash normalization, dialogue formatting, and typography validation.
"""

import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .english_rules import (
    ApostropheNormalizer,
    BlankLineNormalizer,
    DashNormalizer,
    DialogueFormatter,
    EllipsisNormalizer,
    EncodingValidator,
    MarkupConverter,
    ParagraphStyleValidator,
    SmartQuoteConverter,
    TypographyValidator,
)
from .formatting_rule import FormattingRule

# Configure logging
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")


class EnglishNovelFormatter:
    """
    Main formatter class for English novels

    Applies configurable formatting rules to text files.
    Supports Phase 1, Phase 2, and Phase 3 rules.
    """

    # Default configuration for Phase 1 (basic typography)
    DEFAULT_CONFIG = {
        "smart_quotes": True,
        "ellipsis": True,
        "dash": True,
        "blank_lines": True,
        "apostrophe_check": True,
    }

    # Configuration for Phase 2 (includes Phase 1 + dialogue formatting)
    PHASE2_CONFIG = {
        # Phase 1 rules
        "smart_quotes": True,
        "ellipsis": True,
        "dash": True,
        "blank_lines": True,
        "apostrophe_check": True,
        # Phase 2 rules
        "dialogue_format": True,
        "paragraph_style_check": True,
        "markup_warn": True,
    }

    # Configuration for Phase 3 (includes Phase 1 + 2 + validation)
    PHASE3_CONFIG = {
        # Phase 1 rules
        "smart_quotes": True,
        "ellipsis": True,
        "dash": True,
        "blank_lines": True,
        "apostrophe_check": True,
        # Phase 2 rules
        "dialogue_format": True,
        "paragraph_style_check": True,
        "markup_warn": True,
        # Phase 3 rules
        "typography_validate": True,
        "encoding_validate": True,
    }

    def __init__(self, config: Optional[Dict[str, bool]] = None, verbose: bool = False):
        """
        Initialize formatter with configuration

        Args:
            config: Configuration dict with rule toggles.
                   If None, uses default config (all Phase 1 rules enabled).
            verbose: Enable verbose logging of changes
        """
        self.config = config if config is not None else self.DEFAULT_CONFIG.copy()
        self.verbose = verbose
        self.rules: List[FormattingRule] = []
        self._setup_rules()

    def _setup_rules(self):
        """Initialize and register all formatting rules"""
        # All available rules (Phase 1 + Phase 2 + Phase 3)
        available_rules = {
            # Phase 1 rules (priority 1-10)
            "smart_quotes": SmartQuoteConverter(),
            "ellipsis": EllipsisNormalizer(),
            "dash": DashNormalizer(),
            "blank_lines": BlankLineNormalizer(),
            "apostrophe_check": ApostropheNormalizer(),
            # Phase 2 rules (priority 11-20)
            "dialogue_format": DialogueFormatter(),
            "paragraph_style_check": ParagraphStyleValidator(),
            "markup_warn": MarkupConverter(),
            # Phase 3 rules (priority 90-99)
            "typography_validate": TypographyValidator(),
            "encoding_validate": EncodingValidator(),
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
        # Reset change logs for all rules
        for rule in self.rules:
            rule.reset_changes()

        result = text
        for rule in self.rules:
            result = rule.apply(result)
        return result

    def print_change_summary(self):
        """Print a summary of all changes made by rules"""
        total_changes = sum(len(rule.changes) for rule in self.rules)

        if total_changes == 0:
            print("\n✓ No changes made")
        else:
            print("\n" + "=" * 60)
            print("FORMATTING SUMMARY")
            print("=" * 60)

            for rule in self.rules:
                print(rule.get_change_summary())
                if self.verbose and rule.changes:
                    for detail in rule.get_detailed_changes():
                        print(detail)

            print("-" * 60)
            print(f"Total changes: {total_changes}")
            print("=" * 60)

        # Print validation warnings
        self._print_validation_warnings()

    def _print_validation_warnings(self):
        """Print validation warnings from validator rules"""
        # Collect warnings from all rules that have get_warnings() method
        all_warnings = []

        for rule in self.rules:
            if hasattr(rule, "get_warnings"):
                warnings = rule.get_warnings()
                if warnings:
                    all_warnings.append((rule.name, warnings))

        if not all_warnings:
            return

        # Print warnings section
        print("\n" + "=" * 60)
        print("VALIDATION WARNINGS")
        print("=" * 60)

        for rule_name, warnings in all_warnings:
            print(f"\n{rule_name.upper()}:")
            for line_num, message in warnings[:10]:  # Limit to first 10 warnings per rule
                print(f"  Line {line_num}: {message}")

            if len(warnings) > 10:
                print(f"  ... and {len(warnings) - 10} more warning(s)")

        print("=" * 60)

    def write_log_file(self, log_path: Path, input_path: Path, output_path: Path):
        """
        Write detailed change log to a file

        Args:
            log_path: Path to log file
            input_path: Path to input file
            output_path: Path to output file
        """
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("English Novel Formatter - Change Log\n")
            f.write("=" * 60 + "\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Input file: {input_path}\n")
            f.write(f"Output file: {output_path}\n")
            f.write("=" * 60 + "\n\n")

            # Write enabled rules
            f.write("Enabled Rules:\n")
            for rule in self.rules:
                f.write(f"  - {rule.name} (priority: {rule.priority})\n")
            f.write("\n")

            # Write detailed changes
            total_changes = sum(len(rule.changes) for rule in self.rules)

            if total_changes == 0:
                f.write("No changes made.\n")
            else:
                f.write("Detailed Changes:\n")
                f.write("-" * 60 + "\n\n")

                for rule in self.rules:
                    if rule.changes:
                        f.write(f"{rule.get_change_summary()}\n")
                        for change in rule.changes:
                            f.write(f"  Line {change['line']}:\n")
                            f.write(f"    Before: {change['before']}\n")
                            f.write(f"    After:  {change['after']}\n")
                        f.write("\n")

                f.write("-" * 60 + "\n")
                f.write(f"Total changes: {total_changes}\n")

            # Write validation warnings
            self._write_validation_warnings(f)

            f.write("\n" + "=" * 60 + "\n")
            f.write("End of log\n")
            f.write("=" * 60 + "\n")

    def _write_validation_warnings(self, f):
        """
        Write validation warnings to log file

        Args:
            f: File object to write to
        """
        # Collect warnings from all rules
        all_warnings = []

        for rule in self.rules:
            if hasattr(rule, "get_warnings"):
                warnings = rule.get_warnings()
                if warnings:
                    all_warnings.append((rule.name, warnings))

        if not all_warnings:
            return

        # Write warnings section
        f.write("\n" + "=" * 60 + "\n")
        f.write("Validation Warnings\n")
        f.write("=" * 60 + "\n")

        for rule_name, warnings in all_warnings:
            f.write(f"\n{rule_name.upper()}:\n")
            f.write(f"Total warnings: {len(warnings)}\n\n")

            for line_num, message in warnings:
                f.write(f"  Line {line_num}: {message}\n")

            f.write("\n")

        f.write("-" * 60 + "\n")

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
        description="Format English novels with smart quotes, dashes, and typography validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Format single file with Phase 1 rules
  %(prog)s input.txt -o output.txt

  # Format with Phase 2 rules (includes Phase 1 + dialogue formatting)
  %(prog)s input.txt -o output.txt --phase 2

  # Format with Phase 3 rules (includes Phase 1 + 2 + validation)
  %(prog)s input.txt -o output.txt --phase 3

  # Enable specific rules only
  %(prog)s input.txt --smart-quotes --dash -o output.txt

  # Dry run (show changes without writing)
  %(prog)s input.txt --dry-run
        """,
    )

    parser.add_argument("input", type=str, nargs="+", help="Input text file(s) to format")

    parser.add_argument("-o", "--output", type=str, help="Output file or directory (required unless --dry-run)")

    parser.add_argument("--dry-run", action="store_true", help="Show formatted output without writing files")

    parser.add_argument(
        "--phase",
        type=int,
        choices=[1, 2, 3],
        help="Enable all rules up to phase N (1: basic, 2: dialogue, 3: validation)",
    )

    # Rule toggle options (Phase 1)
    rule_group = parser.add_argument_group("formatting rules (Phase 1)")
    rule_group.add_argument("--smart-quotes", action="store_true", help='Enable smart quote conversion (" → " ")')
    rule_group.add_argument("--ellipsis", action="store_true", help="Enable ellipsis normalization (... → …)")
    rule_group.add_argument("--dash", action="store_true", help="Enable dash normalization (-- → —)")
    rule_group.add_argument("--blank-lines", action="store_true", help="Enable blank line normalization")
    rule_group.add_argument("--apostrophe-check", action="store_true", help="Enable apostrophe validation")

    # Phase 2 rule options
    phase2_group = parser.add_argument_group("formatting rules (Phase 2)")
    phase2_group.add_argument("--dialogue-format", action="store_true", help="Enable dialogue formatting")
    phase2_group.add_argument("--paragraph-style-check", action="store_true", help="Enable paragraph style validation")
    phase2_group.add_argument("--markup-warn", action="store_true", help="Enable markdown markup detection")

    # Phase 3 rule options
    phase3_group = parser.add_argument_group("formatting rules (Phase 3)")
    phase3_group.add_argument("--typography-validate", action="store_true", help="Enable typography validation")
    phase3_group.add_argument("--encoding-validate", action="store_true", help="Enable encoding validation")

    # Logging options
    log_group = parser.add_argument_group("logging options")
    log_group.add_argument("--verbose", action="store_true", help="Show detailed changes for each rule")
    log_group.add_argument(
        "--log-file", action="store_true", default=True, help="Write detailed log to file (default: enabled)"
    )
    log_group.add_argument("--no-log-file", action="store_true", help="Disable log file writing")

    return parser.parse_args()


def main():
    """Main entry point for CLI"""
    args = parse_arguments()

    # Validate arguments
    if not args.dry_run and not args.output:
        print("Error: --output is required unless --dry-run is specified")
        return 1

    # Build configuration
    has_specific_rules = (
        args.smart_quotes
        or args.ellipsis
        or args.dash
        or args.blank_lines
        or args.apostrophe_check
        or args.dialogue_format
        or args.paragraph_style_check
        or args.markup_warn
        or args.typography_validate
        or args.encoding_validate
    )

    if has_specific_rules:
        # Use specific rules only
        config = {
            # Phase 1 rules
            "smart_quotes": args.smart_quotes,
            "ellipsis": args.ellipsis,
            "dash": args.dash,
            "blank_lines": args.blank_lines,
            "apostrophe_check": args.apostrophe_check,
            # Phase 2 rules
            "dialogue_format": args.dialogue_format,
            "paragraph_style_check": args.paragraph_style_check,
            "markup_warn": args.markup_warn,
            # Phase 3 rules
            "typography_validate": args.typography_validate,
            "encoding_validate": args.encoding_validate,
        }
    elif args.phase == 3:
        # Enable all Phase 3 rules
        config = EnglishNovelFormatter.PHASE3_CONFIG.copy()
    elif args.phase == 2:
        # Enable all Phase 2 rules
        config = EnglishNovelFormatter.PHASE2_CONFIG.copy()
    else:
        # Default: enable all Phase 1 rules
        config = EnglishNovelFormatter.DEFAULT_CONFIG.copy()

    # Determine if log file should be written
    write_log = args.log_file and not args.no_log_file and not args.dry_run

    # Initialize formatter
    formatter = EnglishNovelFormatter(config=config, verbose=args.verbose)

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

        # Print summary
        formatter.print_change_summary()

        # Write log file if enabled
        if write_log:
            log_file = output_file.parent / f"{output_file.name}.log"
            formatter.write_log_file(log_file, input_file, output_file)
            print(f"\n✓ Log written to: {log_file}")

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

                # Print summary for dry run
                formatter.print_change_summary()
            else:
                # Write to output directory
                if not output_path or not output_path.is_dir():
                    print("Error: Multiple input files require --output to be a directory")
                    return 1

                output_file = output_path / input_file.name
                print(f"\nFormatting: {input_file} → {output_file}")
                formatter.format_file(input_file, output_file)

                # Print summary for this file
                formatter.print_change_summary()

                # Write log file if enabled
                if write_log:
                    log_file = output_file.parent / f"{output_file.name}.log"
                    formatter.write_log_file(log_file, input_file, output_file)
                    print(f"✓ Log written to: {log_file}")

        if not args.dry_run:
            print(f"\n{'='*60}")
            print(f"✓ Formatted {len(expanded_paths)} file(s)")
            print(f"{'='*60}")

    return 0


if __name__ == "__main__":
    exit(main())
