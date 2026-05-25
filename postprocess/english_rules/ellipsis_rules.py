"""
Ellipsis formatting rules for English text
"""

import re

from ..formatting_rule import FormattingRule


class EllipsisNormalizer(FormattingRule):
    """
    Normalize ellipsis to Unicode ellipsis character

    Transformations:
    - ... → … (U+2026)
    - .. . → …
    - . . . → …
    - Multiple consecutive ellipsis → single …
    """

    def __init__(self):
        super().__init__("ellipsis", priority=2)

    def apply(self, text: str) -> str:
        """
        Normalize various ellipsis forms to Unicode ellipsis
        """
        lines = text.split("\n")
        result = []

        for line_num, line in enumerate(lines, 1):
            original_line = line

            # Replace three dots with Unicode ellipsis
            line = line.replace("...", "…")

            # Replace dot-space-dot-space-dot patterns
            line = re.sub(r"\.\s*\.\s*\.", "…", line)

            # Replace multiple consecutive ellipsis with single one
            line = re.sub(r"…+", "…", line)

            # Log changes if line was modified
            if line != original_line:
                self.log_change(line_num, original_line, line)

            result.append(line)

        return "\n".join(result)
