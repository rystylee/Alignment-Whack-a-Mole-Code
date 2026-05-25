"""
Markup formatting rules for English text
"""

import re

from ..formatting_rule import FormattingRule


class MarkupConverter(FormattingRule):
    """
    Detect and handle Markdown-style markup

    Detects:
    - _text_ (italic markup)
    - *text* (bold/italic markup)
    - **text** (bold markup)

    Note: This is primarily a detection rule that warns about markup
    without automatically removing it, as the intent may vary.
    """

    def __init__(self):
        super().__init__("markup", priority=13)
        self.warnings = []

    def apply(self, text: str) -> str:
        """
        Detect Markdown-style markup and warn

        Returns original text unchanged (non-destructive)
        """
        self.warnings = []
        lines = text.split("\n")

        for line_num, line in enumerate(lines, 1):
            # Detect _text_ (underscore italic)
            underscore_pattern = r"_([^_\s][^_]*[^_\s]|[^_\s])_"
            underscore_matches = re.finditer(underscore_pattern, line)
            for match in underscore_matches:
                self.warnings.append((line_num, f"Underscore markup detected: {match.group(0)}"))
                self.log_change(line_num, f"Detected: {match.group(0)}", "Consider: plain text or formatting")

            # Detect *text* or **text** (asterisk markup)
            asterisk_pattern = r"\*+([^\*\s][^\*]*[^\*\s]|[^\*\s])\*+"
            asterisk_matches = re.finditer(asterisk_pattern, line)
            for match in asterisk_matches:
                self.warnings.append((line_num, f"Asterisk markup detected: {match.group(0)}"))
                self.log_change(line_num, f"Detected: {match.group(0)}", "Consider: plain text or formatting")

        return text  # Non-destructive: return original text

    def get_warnings(self) -> list:
        """Get list of warnings"""
        return self.warnings
