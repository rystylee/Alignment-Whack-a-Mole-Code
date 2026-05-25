"""
Blank line formatting rules for English text
"""

import re

from ..formatting_rule import FormattingRule


class BlankLineNormalizer(FormattingRule):
    """
    Normalize blank lines and detect duplicate paragraphs

    Transformations:
    - 3+ consecutive newlines → 2 newlines (1 blank line)
    - Remove leading/trailing blank lines from document

    Detection (non-destructive):
    - Duplicate paragraphs (warns without removing)
    """

    def __init__(self):
        super().__init__("blank_lines", priority=4)
        self.duplicate_paragraphs = []

    def apply(self, text: str) -> str:
        """
        Normalize blank lines and detect duplicate paragraphs
        """
        self.duplicate_paragraphs = []

        # First, detect duplicate paragraphs
        self._detect_duplicates(text)

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

        # Remove leading and trailing blank lines
        text = text.strip()

        return text

    def _detect_duplicates(self, text: str):
        """
        Detect duplicate paragraphs in the text

        A paragraph is defined as text between blank lines.
        Warns about exact duplicates without removing them.
        """
        # Split text into paragraphs (separated by blank lines)
        paragraphs = re.split(r"\n\s*\n", text)

        # Track seen paragraphs with their line numbers
        seen = {}
        current_line = 1

        for para in paragraphs:
            para = para.strip()
            if not para:
                current_line += 1
                continue

            # Skip very short paragraphs (likely not duplicates)
            if len(para) < 20:
                current_line += para.count("\n") + 2  # +2 for blank line
                continue

            if para in seen:
                # Found duplicate
                original_line = seen[para]
                self.duplicate_paragraphs.append((original_line, current_line, para[:50] + "..."))
                self.log_change(current_line, f"Duplicate of line {original_line}", f"First 50 chars: {para[:50]}...")
            else:
                seen[para] = current_line

            current_line += para.count("\n") + 2  # +2 for blank line

    def get_duplicate_warnings(self) -> list:
        """Get list of duplicate paragraph warnings"""
        return self.duplicate_paragraphs
