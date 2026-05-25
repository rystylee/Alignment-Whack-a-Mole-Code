#!/usr/bin/env python3
"""
Japanese Novel Formatter - Phase 1 Implementation

This module provides text formatting for Japanese vertical novels.
Implements basic normalization rules for punctuation and spacing.
"""

import argparse
import logging
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .formatting_rule import FormattingRule

# Configure logging
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")


class EllipsisNormalizer(FormattingRule):
    """Normalize ellipsis to 「……」"""

    def __init__(self):
        super().__init__("ellipsis", priority=1)

    def apply(self, text: str) -> str:
        """
        Normalize various ellipsis forms to standard format

        Transformations:
        - ... → ……
        - …+ (one or more) → ……

        Note: Multiple consecutive ellipsis characters are normalized to a single ……
        This prevents double conversion of already normalized text.
        """
        lines = text.split("\n")
        result = []

        for line_num, line in enumerate(lines, 1):
            original_line = line

            # Replace three dots with double horizontal ellipsis
            line = line.replace("...", "……")
            # Replace one or more consecutive horizontal ellipsis with double horizontal ellipsis
            # This handles both single … and already normalized …… (or more)
            line = re.sub(r"…+", "……", line)

            # Log changes if line was modified
            if line != original_line:
                self.log_change(line_num, original_line, line)

            result.append(line)

        return "\n".join(result)


class DashNormalizer(FormattingRule):
    """Normalize dash to 「――」"""

    def __init__(self):
        super().__init__("dash", priority=2)

    def apply(self, text: str) -> str:
        """
        Normalize various dash forms to standard format

        Transformations:
        - -- or --- → ――
        - —+ (one or more em dashes) → ――
        - ー+ (one or more katakana prolonged sound marks) → ――

        Note: Multiple consecutive dash/prolonged sound characters are normalized to a single ――
        This prevents double conversion of already normalized text.
        """
        lines = text.split("\n")
        result = []

        for line_num, line in enumerate(lines, 1):
            original_line = line

            # Replace multiple hyphens with double horizontal bar
            line = re.sub(r"-{2,}", "――", line)
            # Replace one or more consecutive em dashes with double horizontal bar
            # This handles both single — and already normalized —— (or more)
            line = re.sub(r"—+", "――", line)
            # Replace one or more consecutive katakana prolonged sound marks with double horizontal bar
            # This handles both single ー and already normalized ーー (or more)
            line = re.sub(r"ー+", "――", line)

            # Log changes if line was modified
            if line != original_line:
                self.log_change(line_num, original_line, line)

            result.append(line)

        return "\n".join(result)


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
        lines = text.split("\n")
        result = []

        for line_num, line in enumerate(lines, 1):
            original_line = line

            # Replace ASCII tilde with wave dash
            line = line.replace("~", "〜")
            # Replace full-width tilde with wave dash
            line = line.replace("～", "〜")

            # Log changes if line was modified
            if line != original_line:
                self.log_change(line_num, original_line, line)

            result.append(line)

        return "\n".join(result)


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
        # Find and log all instances of excessive blank lines
        lines = text.split("\n")
        blank_count = 0
        blank_start_line = 0

        for line_num, line in enumerate(lines, 1):
            if line == "":
                if blank_count == 0:
                    blank_start_line = line_num
                blank_count += 1
            else:
                if blank_count >= 3:
                    # Log the reduction of blank lines
                    self.log_change(
                        blank_start_line,
                        f"{blank_count} consecutive blank lines",
                        "2 consecutive blank lines (1 blank line)",
                    )
                blank_count = 0

        # Check last section
        if blank_count >= 3:
            self.log_change(
                blank_start_line,
                f"{blank_count} consecutive blank lines",
                "2 consecutive blank lines (1 blank line)",
            )

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

        for line_num, line in enumerate(lines, 1):
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
                modified_line = "　" + line
                self.log_change(line_num, line, modified_line)
                result.append(modified_line)
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
        lines = text.split("\n")
        result = []

        for line_num, line in enumerate(lines, 1):
            original_line = line

            # First convert all full-width alphanumeric to half-width
            line = self._convert_alphanumeric(line)
            # Then selectively convert 3+ digit numbers back to full-width
            line = self._handle_numbers(line)

            # Log changes if line was modified
            if line != original_line:
                self.log_change(line_num, original_line, line)

            result.append(line)

        return "\n".join(result)

    def _convert_alphanumeric(self, text: str) -> str:
        """
        Convert full-width alphanumeric characters to half-width

        Converts only alphanumeric characters (0-9, A-Z, a-z) from full-width
        to half-width. All punctuation and symbols remain full-width as per
        Japanese typesetting rules.

        Rules:
        - Convert: ０-９ (U+FF10-U+FF19), Ａ-Ｚ (U+FF21-U+FF3A), ａ-ｚ (U+FF41-U+FF5A)
        - Keep full-width: All punctuation and symbols (brackets, dashes, etc.)
        """
        result = []
        for char in text:
            code = ord(char)
            # Only convert full-width alphanumeric characters
            # 0-9: U+FF10-U+FF19, A-Z: U+FF21-U+FF3A, a-z: U+FF41-U+FF5A
            if (
                0xFF10 <= code <= 0xFF19  # Full-width digits
                or 0xFF21 <= code <= 0xFF3A  # Full-width uppercase
                or 0xFF41 <= code <= 0xFF5A
            ):  # Full-width lowercase
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
        lines = text.split("\n")
        result = []

        for line_num, line in enumerate(lines, 1):
            original_line = line

            # Replace environment-dependent characters
            for char, replacement in self.REPLACEMENT_MAP.items():
                line = line.replace(char, replacement)

            # Log changes if line was modified
            if line != original_line:
                self.log_change(line_num, original_line, line)

            result.append(line)

        return "\n".join(result)


class CharacterRangeValidator(FormattingRule):
    """Validate characters are within JIS X 0213:2004 range"""

    def __init__(self):
        super().__init__("character_range", priority=99)  # Lowest priority - validate after all transformations
        self.logger = logging.getLogger(__name__)
        self.out_of_range_chars = []  # Store out-of-range character information
        self.warnings = []  # Store warnings in standardized format

    def apply(self, text: str) -> str:
        """
        Validate text contains only JIS X 0213:2004 characters

        Strategy:
        1. Test encoding with shift_jisx0213
        2. Collect out-of-range characters with line and column positions
        3. Log detailed warnings
        4. Return original text (non-destructive)

        Returns:
            Original text unchanged (validation only)
        """
        # Reset stored information
        self.out_of_range_chars = []
        self.warnings = []

        # Detect all out-of-range characters with line and column info
        lines = text.split("\n")
        for line_num, line in enumerate(lines, 1):
            for col_num, char in enumerate(line, 1):
                try:
                    char.encode("shift_jisx0213")
                except UnicodeEncodeError:
                    self.out_of_range_chars.append((line_num, col_num, char))

        # Build warnings list
        if self.out_of_range_chars:
            self._build_warnings()
            self._log_warnings(self.out_of_range_chars)

        return text  # Non-destructive: return original text

    def _log_warnings(self, out_of_range: list):
        """
        Log detailed warnings for out-of-range characters

        Args:
            out_of_range: List of (line_num, col_num, character) tuples
        """
        # Get unique characters with their locations
        unique_chars = {}
        for line_num, col_num, char in out_of_range:
            if char not in unique_chars:
                unique_chars[char] = []
            unique_chars[char].append((line_num, col_num))

        self.logger.warning(f"Found {len(out_of_range)} character(s) outside JIS X 0213:2004 range")

        # Log details for each unique character
        for char in sorted(unique_chars.keys(), key=lambda c: ord(c)):
            code_point = ord(char)
            char_name = unicodedata.name(char, "UNKNOWN")
            locations = unique_chars[char]

            # Format locations as "line:column"
            location_strs = [f"line {line}:{col}" for line, col in locations[:5]]

            if len(locations) > 5:
                loc_display = ", ".join(location_strs) + f", ... ({len(locations)} total)"
            else:
                loc_display = ", ".join(location_strs)

            self.logger.warning(f"  U+{code_point:04X} '{char}' ({char_name}) at {loc_display}")

    def _build_warnings(self):
        """
        Build warnings list for standardized warning output

        Converts out_of_range_chars to standardized (line_num, message) format
        """
        # Group by character to create summary messages
        char_locations = {}
        for line_num, col_num, char in self.out_of_range_chars:
            if char not in char_locations:
                char_locations[char] = []
            char_locations[char].append((line_num, col_num))

        # Create warning messages
        for char in sorted(char_locations.keys(), key=lambda c: ord(c)):
            code_point = ord(char)
            char_name = unicodedata.name(char, "UNKNOWN")
            locations = char_locations[char]

            # Use the first occurrence line number as the primary line
            first_line = locations[0][0]

            # Create message with all locations
            location_strs = [f"line {line}:{col}" for line, col in locations[:5]]
            if len(locations) > 5:
                loc_display = ", ".join(location_strs) + f", ... ({len(locations)} total)"
            else:
                loc_display = ", ".join(location_strs)

            message = f"U+{code_point:04X} '{char}' ({char_name}) at {loc_display}"
            self.warnings.append((first_line, message))

    def get_warnings(self):
        """
        Get validation warnings

        Returns:
            List of (line_num, message) tuples
        """
        return self.warnings


class KanjiGlyphSelector(FormattingRule):
    """Select appropriate Japanese kanji glyphs"""

    # CJK Unified Ideographs main blocks (Unicode ranges)
    CJK_RANGES = [
        (0x4E00, 0x9FFF),  # CJK Unified Ideographs (main block)
        (0x3400, 0x4DBF),  # CJK Unified Ideographs Extension A
        (0x20000, 0x2A6DF),  # CJK Unified Ideographs Extension B
        (0x2A700, 0x2B73F),  # CJK Unified Ideographs Extension C
        (0x2B740, 0x2B81F),  # CJK Unified Ideographs Extension D
        (0x2B820, 0x2CEAF),  # CJK Unified Ideographs Extension E
        (0x2CEB0, 0x2EBE0),  # CJK Unified Ideographs Extension F
        (0x30000, 0x3134F),  # CJK Unified Ideographs Extension G
        (0x31350, 0x323AF),  # CJK Unified Ideographs Extension H
        (0x2EBF0, 0x2EE5F),  # CJK Unified Ideographs Extension I
    ]

    # CJK Compatibility Ideographs (often need normalization)
    CJK_COMPAT_RANGES = [
        (0xF900, 0xFAFF),  # CJK Compatibility Ideographs
        (0x2F800, 0x2FA1F),  # CJK Compatibility Ideographs Supplement
    ]

    def __init__(self):
        super().__init__("kanji_glyph", priority=8)
        self.warning_count = 0
        self.logger = logging.getLogger(__name__)
        self.warnings = []  # Store warnings in standardized format
        self.compat_ideographs = []  # Store compatibility ideograph information

    def apply(self, text: str) -> str:
        """
        Normalize kanji glyphs to prefer Japanese forms

        Process:
        1. Detect CJK compatibility ideographs (before normalization)
        2. Apply Unicode NFC normalization (preserves Japanese glyphs)
        3. Log warnings for non-standard characters

        Note: NFC (Normalization Form Canonical Composition) is used
        instead of NFKC to preserve semantic distinctions while
        normalizing to canonical Japanese glyphs.
        """
        # Reset stored information
        self.warning_count = 0
        self.warnings = []
        self.compat_ideographs = []

        # First, check for compatibility ideographs BEFORE normalization
        # Also track line numbers for warnings
        lines = text.split("\n")
        for line_num, line in enumerate(lines, 1):
            for char in line:
                code_point = ord(char)

                # Check if character is in CJK compatibility ranges
                if self._is_compat_ideograph(code_point):
                    # Get the canonical decomposition
                    decomposed = unicodedata.decomposition(char)
                    if decomposed:
                        self.warning_count += 1
                        # Get the normalized character
                        normalized_char = unicodedata.normalize("NFC", char)
                        self.compat_ideographs.append((line_num, char, code_point, normalized_char))
                        self.logger.warning(
                            f"CJK compatibility ideograph detected: U+{code_point:04X} '{char}' "
                            f"→ normalized to U+{ord(normalized_char):04X} '{normalized_char}'"
                        )

        # Build warnings list
        if self.compat_ideographs:
            self._build_warnings()

        if self.warning_count > 0:
            self.logger.info(f"Total kanji normalization warnings: {self.warning_count}")

        # Apply NFC normalization to ensure canonical form
        # NFC preserves semantic meaning while normalizing variants
        return unicodedata.normalize("NFC", text)

    def _is_cjk_ideograph(self, code_point: int) -> bool:
        """Check if a code point is a CJK ideograph"""
        for start, end in self.CJK_RANGES:
            if start <= code_point <= end:
                return True
        return False

    def _is_compat_ideograph(self, code_point: int) -> bool:
        """Check if a code point is a CJK compatibility ideograph"""
        for start, end in self.CJK_COMPAT_RANGES:
            if start <= code_point <= end:
                return True
        return False

    def _build_warnings(self):
        """
        Build warnings list for standardized warning output

        Converts compat_ideographs to standardized (line_num, message) format
        """
        for line_num, char, code_point, normalized_char in self.compat_ideographs:
            message = (
                f"CJK compatibility ideograph U+{code_point:04X} '{char}' "
                f"→ normalized to U+{ord(normalized_char):04X} '{normalized_char}'"
            )
            self.warnings.append((line_num, message))

    def get_warnings(self):
        """
        Get validation warnings

        Returns:
            List of (line_num, message) tuples
        """
        return self.warnings


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
        "kanji_glyph": True,
    }

    # Configuration for Phase 3 (includes Phase 1 + 2)
    PHASE3_CONFIG = {
        # Phase 1 rules
        "ellipsis": True,
        "dash": True,
        "tilde": True,
        "blank_lines": True,
        # Phase 2 rules
        "paragraph_indent": True,
        "halfwidth_convert": True,
        "remove_env_chars": True,
        "kanji_glyph": True,
        # Phase 3 rules
        "character_range": True,
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
            # Phase 1 rules
            "ellipsis": EllipsisNormalizer(),
            "dash": DashNormalizer(),
            "tilde": TildeNormalizer(),
            "blank_lines": BlankLineRemover(),
            # Phase 2 rules
            "paragraph_indent": ParagraphIndenter(),
            "halfwidth_convert": HalfWidthConverter(),
            "remove_env_chars": EnvironmentCharRemover(),
            "kanji_glyph": KanjiGlyphSelector(),
            # Phase 3 rules
            "character_range": CharacterRangeValidator(),
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
            f.write("Japanese Novel Formatter - Change Log\n")
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
        "--phase",
        type=int,
        choices=[1, 2, 3],
        help="Enable all rules up to phase N (1: basic, 2: medium, 3: advanced)",
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
    phase2_group.add_argument("--kanji-glyph", action="store_true", help="Enable kanji glyph selection (1.2)")

    # Phase 3 rule options
    phase3_group = parser.add_argument_group("formatting rules (Phase 3)")
    phase3_group.add_argument("--character-range", action="store_true", help="Enable character range validation (1.1)")

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
    # Priority: specific rules > phase flag > default (Phase 1)
    has_specific_rules = (
        args.ellipsis
        or args.dash
        or args.tilde
        or args.blank_lines
        or args.paragraph_indent
        or args.halfwidth_convert
        or args.remove_env_chars
        or args.kanji_glyph
        or args.character_range
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
            "kanji_glyph": args.kanji_glyph,
            # Phase 3 rules
            "character_range": args.character_range,
        }
    elif args.phase == 3:
        # Enable all Phase 3 rules (includes Phase 1 + 2)
        config = JapaneseNovelFormatter.PHASE3_CONFIG.copy()
    elif args.phase == 2:
        # Enable all Phase 2 rules (includes Phase 1)
        config = JapaneseNovelFormatter.PHASE2_CONFIG.copy()
    else:
        # Default: enable all Phase 1 rules
        config = JapaneseNovelFormatter.DEFAULT_CONFIG.copy()

    # Determine if log file should be written
    write_log = args.log_file and not args.no_log_file and not args.dry_run

    # Initialize formatter
    formatter = JapaneseNovelFormatter(config=config, verbose=args.verbose)

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
