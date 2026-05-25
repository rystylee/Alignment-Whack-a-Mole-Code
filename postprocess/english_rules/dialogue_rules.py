"""
Dialogue and paragraph formatting rules for English text
"""

import re

from ..formatting_rule import FormattingRule


class DialogueFormatter(FormattingRule):
    """
    Format dialogue text according to English conventions

    Checks:
    - Dialogue tag punctuation: "Text," she said. ✓
    - Remove unnecessary comma after ! or ?: "Stop!," he said. → "Stop!" he said.
    - Warn about dialogue mixed with narrative on same line

    Note: This is primarily a validation and correction rule
    """

    # Common dialogue verbs for detection
    DIALOGUE_VERBS = {
        "said",
        "says",
        "asked",
        "asks",
        "replied",
        "replies",
        "answered",
        "answers",
        "whispered",
        "whispers",
        "shouted",
        "shouts",
        "cried",
        "cries",
        "murmured",
        "murmurs",
        "muttered",
        "mutters",
        "exclaimed",
        "exclaims",
        "announced",
        "announces",
        "declared",
        "declares",
        "continued",
        "continues",
        "added",
        "adds",
        "responded",
        "responds",
        "remarked",
        "remarks",
        "observed",
        "observes",
        "noted",
        "notes",
        "stated",
        "states",
        "urged",
        "urges",
        "pleaded",
        "pleads",
        "begged",
        "begs",
        "demanded",
        "demands",
        "commanded",
        "commands",
        "ordered",
        "orders",
        "suggested",
        "suggests",
        "proposed",
        "proposes",
        "agreed",
        "agrees",
        "disagreed",
        "disagrees",
        "protested",
        "protests",
        "objected",
        "objects",
        "complained",
        "complains",
        "grumbled",
        "grumbles",
        "sighed",
        "sighs",
        "laughed",
        "laughs",
        "chuckled",
        "chuckles",
        "smiled",
        "smiles",
        "grinned",
        "grins",
        "frowned",
        "frowns",
        "scowled",
        "scowls",
        "thought",
        "thinks",
        "wondered",
        "wonders",
        "mused",
        "muses",
        "pondered",
        "ponders",
        "recalled",
        "recalls",
        "remembered",
        "remembers",
    }

    def __init__(self):
        super().__init__("dialogue_format", priority=11)
        self.warnings = []

    def apply(self, text: str) -> str:
        """
        Format dialogue text and validate dialogue formatting
        """
        self.warnings = []
        lines = text.split("\n")
        result = []

        for line_num, line in enumerate(lines, 1):
            original_line = line

            # Fix: Remove comma after ! or ?
            # Pattern: "Text!," he said → "Text!" he said
            # Support both straight quotes (") and smart quotes (")
            line = re.sub(r'([!?]),(["\u201d])\s+', r"\1\2 ", line)

            # Warn about potential issues (but don't auto-fix)
            self._check_dialogue_tags(original_line, line_num)

            # Log changes if line was modified
            if line != original_line:
                self.log_change(line_num, original_line, line)

            result.append(line)

        return "\n".join(result)

    def _check_dialogue_tags(self, line: str, line_num: int):
        """
        Check for dialogue tag issues

        Patterns to detect:
        - "Text" she said. (missing comma)
        - Mixed dialogue and narrative without proper separation
        """
        # Pattern 1: Closing quote followed by dialogue verb directly
        # "Hello" said → should be "Hello," said
        pattern1 = r'["\u201d]\s+([a-z]+)(?:\s|\.)'

        # Pattern 2: Closing quote followed by pronoun + verb
        # "Hello" she said → should be "Hello," she said
        pattern2 = r'["\u201d]\s+([a-z]+)\s+([a-z]+)'

        # Check pattern 1: direct verb
        for match in re.finditer(pattern1, line):
            verb = match.group(1)
            if verb in self.DIALOGUE_VERBS:
                self.warnings.append((line_num, f"Missing comma after dialogue: {match.group(0).strip()}"))
                return  # Found one, no need to check further

        # Check pattern 2: pronoun + verb
        for match in re.finditer(pattern2, line):
            verb = match.group(2)  # Second word is the verb
            if verb in self.DIALOGUE_VERBS:
                self.warnings.append((line_num, f"Missing comma after dialogue: {match.group(0).strip()}"))
                return  # Found one, no need to check further

    def get_warnings(self) -> list:
        """Get list of warnings"""
        return self.warnings


class ParagraphStyleValidator(FormattingRule):
    """
    Validate paragraph style consistency

    Checks for:
    - Mix of indented and block-style paragraphs
    - Inconsistent spacing between paragraphs

    Note: This is a non-destructive validation rule
    """

    def __init__(self):
        super().__init__("paragraph_style", priority=12)
        self.warnings = []
        self.stats = {
            "indented_paras": 0,
            "block_paras": 0,
            "total_paras": 0,
        }

    def apply(self, text: str) -> str:
        """
        Validate paragraph style consistency

        Returns original text unchanged (non-destructive)
        """
        self.warnings = []
        self.stats = {"indented_paras": 0, "block_paras": 0, "total_paras": 0}

        # Split into paragraphs
        paragraphs = re.split(r"\n\s*\n", text)
        self.stats["total_paras"] = len([p for p in paragraphs if p.strip()])

        for para in paragraphs:
            if not para.strip():
                continue

            # Check if paragraph starts with indent (space or tab)
            # Must check BEFORE stripping whitespace
            if para and para[0] in " \t":
                self.stats["indented_paras"] += 1
            else:
                self.stats["block_paras"] += 1

        # Warn if there's a significant mix of styles
        if self.stats["indented_paras"] > 0 and self.stats["block_paras"] > 0:
            indent_percent = (self.stats["indented_paras"] / self.stats["total_paras"]) * 100
            block_percent = (self.stats["block_paras"] / self.stats["total_paras"]) * 100

            # Only warn if neither style is clearly dominant (both > 20%)
            if 20 < indent_percent < 80:
                self.warnings.append(
                    (
                        1,
                        f"Mixed paragraph styles detected: {self.stats['indented_paras']} indented, "
                        f"{self.stats['block_paras']} block-style",
                    )
                )
                self.log_change(
                    1,
                    f"Indented: {indent_percent:.1f}%, Block: {block_percent:.1f}%",
                    "Consider using consistent style",
                )

        return text  # Non-destructive: return original text

    def get_warnings(self) -> list:
        """Get list of warnings"""
        return self.warnings

    def get_stats(self) -> dict:
        """Get paragraph statistics"""
        return self.stats
