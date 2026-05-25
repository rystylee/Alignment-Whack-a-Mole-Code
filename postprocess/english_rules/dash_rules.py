"""
Dash formatting rules for English text
"""

import re

from ..formatting_rule import FormattingRule


class DashNormalizer(FormattingRule):
    """
    Normalize dashes for English text

    Transformations:
    - -- → — (em dash, no spaces)
    - Remove spaces around em dashes: word — word → word—word
    - Number ranges: 1999-2003 → 1999–2003 (en dash)
    - Preserve hyphens in compound words: well-known

    Style: Chicago Manual of Style (em-dash without spaces)
    """

    def __init__(self):
        super().__init__("dash", priority=3)

    def apply(self, text: str) -> str:
        """
        Normalize dashes according to English typography standards
        """
        lines = text.split("\n")
        result = []

        for line_num, line in enumerate(lines, 1):
            original_line = line

            # First, convert double hyphens to em-dash
            line = re.sub(r"--", "—", line)

            # Remove spaces around em-dashes (Chicago style)
            line = re.sub(r"\s*—\s*", "—", line)

            # Convert number ranges to en-dash
            # Pattern: digit(s) - digit(s)
            line = re.sub(r"(\d+)\s*-\s*(\d+)", r"\1–\2", line)

            # Convert page ranges: pp. 12-15 → pp. 12–15
            line = re.sub(r"\bpp\.\s*(\d+)\s*-\s*(\d+)", r"pp. \1–\2", line)

            # Log changes if line was modified
            if line != original_line:
                self.log_change(line_num, original_line, line)

            result.append(line)

        return "\n".join(result)
