"""
Validation rules for English text typography
"""

import re
import unicodedata

from ..formatting_rule import FormattingRule


class TypographyValidator(FormattingRule):
    """
    Validate typography quality

    Checks for:
    - Remaining straight quotes " '
    - Consecutive spaces
    - Space-hyphen-space (should use em-dash)
    - Hyphen in number ranges (should use en-dash)

    Note: This is a non-destructive validation rule (warnings only)
    """

    def __init__(self):
        super().__init__("typography_validation", priority=98)
        self.warnings = []

    def apply(self, text: str) -> str:
        """
        Validate typography and warn about issues

        Returns original text unchanged (non-destructive)
        """
        self.warnings = []
        lines = text.split("\n")

        for line_num, line in enumerate(lines, 1):
            # Check for straight double quotes
            if '"' in line:
                count = line.count('"')
                self.warnings.append((line_num, f"Straight double quote detected ({count} occurrence(s))"))
                self.log_change(line_num, 'Straight quote: "', 'Should use: " or "')

            # Check for straight single quotes (excluding apostrophes in contractions)
            # This pattern looks for standalone single quotes, not in middle of words
            straight_single = re.finditer(r"(?<!\w)'(?!\w)|(?:^|(?<=\s))'(?=\w)|(?<=\w)'(?=\s|$|[^\w])", line)
            for match in straight_single:
                self.warnings.append((line_num, f"Straight single quote detected at position {match.start()}"))
                self.log_change(line_num, "Straight quote: '", "Should use: ' or '")

            # Check for consecutive spaces (2 or more)
            consecutive_spaces = re.finditer(r"  +", line)
            for match in consecutive_spaces:
                count = len(match.group(0))
                self.warnings.append((line_num, f"{count} consecutive spaces detected"))
                self.log_change(line_num, f"{count} spaces", "Should use: single space")

            # Check for space-hyphen-space (should use em-dash)
            if re.search(r"\s-\s", line):
                self.warnings.append((line_num, "Space-hyphen-space detected (consider em-dash)"))
                self.log_change(line_num, " - ", "Consider: —")

            # Check for hyphen in number ranges (should use en-dash)
            number_range = re.finditer(r"(\d+)-(\d+)", line)
            for match in number_range:
                self.warnings.append((line_num, f"Hyphen in number range: {match.group(0)} (should use en-dash)"))
                self.log_change(line_num, match.group(0), match.group(0).replace("-", "–"))

        return text  # Non-destructive: return original text

    def get_warnings(self) -> list:
        """Get list of warnings"""
        return self.warnings


class EncodingValidator(FormattingRule):
    """
    Validate text encoding and character usage

    Checks for:
    - Non-ASCII characters (beyond common punctuation)
    - Control characters
    - Platform-dependent characters
    - Unusual Unicode characters

    Note: This is a non-destructive validation rule (warnings only)
    """

    # Common acceptable non-ASCII characters for English text
    ACCEPTABLE_CHARS = {
        # Smart quotes and apostrophes
        """,
        """,
        "'",
        "'",
        # Dashes
        "—",  # Em dash
        "–",  # En dash
        # Other punctuation
        "…",  # Ellipsis
        "°",  # Degree symbol
        # Common currency and symbols
        "£",
        "€",
        "¥",
        "©",
        "®",
        "™",
        "§",
        "†",
        "‡",
        # Common accented letters for foreign words
        "é",
        "è",
        "ê",
        "ë",
        "á",
        "à",
        "â",
        "ä",
        "í",
        "ì",
        "î",
        "ï",
        "ó",
        "ò",
        "ô",
        "ö",
        "ú",
        "ù",
        "û",
        "ü",
        "ñ",
        "ç",
        "É",
        "È",
        "Ê",
        "Ë",
        "Á",
        "À",
        "Â",
        "Ä",
        "Í",
        "Ì",
        "Î",
        "Ï",
        "Ó",
        "Ò",
        "Ô",
        "Ö",
        "Ú",
        "Ù",
        "Û",
        "Ü",
        "Ñ",
        "Ç",
        "æ",
        "œ",
        "Æ",
        "Œ",
    }

    def __init__(self):
        super().__init__("encoding_validation", priority=99)
        self.warnings = []
        self.unusual_chars = []

    def apply(self, text: str) -> str:
        """
        Validate encoding and character usage

        Returns original text unchanged (non-destructive)
        """
        self.warnings = []
        self.unusual_chars = []
        lines = text.split("\n")

        for line_num, line in enumerate(lines, 1):
            for col_num, char in enumerate(line, 1):
                code_point = ord(char)

                # Check for control characters (except tab and newline)
                if code_point < 32 and char not in "\t\n":
                    char_name = unicodedata.name(char, "UNKNOWN")
                    self.warnings.append(
                        (line_num, f"Control character at col {col_num}: U+{code_point:04X} ({char_name})")
                    )
                    self.unusual_chars.append((line_num, col_num, char))
                    self.log_change(line_num, f"Control char at col {col_num}", f"U+{code_point:04X}")

                # Check for non-ASCII characters outside acceptable set
                elif code_point > 127:
                    if char not in self.ACCEPTABLE_CHARS:
                        char_name = unicodedata.name(char, "UNKNOWN")

                        # Skip if it's a normal space or basic punctuation
                        if code_point in [0xA0, 0x2000, 0x2001, 0x2002, 0x2003]:
                            # Non-breaking space or other space variants
                            self.warnings.append(
                                (
                                    line_num,
                                    f"Special space at col {col_num}: U+{code_point:04X} ({char_name})",
                                )
                            )
                        else:
                            # Other unusual characters
                            self.warnings.append(
                                (
                                    line_num,
                                    f"Non-ASCII character at col {col_num}: U+{code_point:04X} '{char}' ({char_name})",
                                )
                            )

                        self.unusual_chars.append((line_num, col_num, char))
                        self.log_change(
                            line_num, f"Unusual char at col {col_num}: '{char}'", f"U+{code_point:04X} ({char_name})"
                        )

        return text  # Non-destructive: return original text

    def get_warnings(self) -> list:
        """Get list of warnings"""
        return self.warnings

    def get_unusual_chars(self) -> list:
        """Get list of unusual characters with positions"""
        return self.unusual_chars
