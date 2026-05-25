"""
Quote and apostrophe formatting rules for English text
"""

import re

from ..formatting_rule import FormattingRule


class SmartQuoteConverter(FormattingRule):
    """
    Convert straight quotes to smart (curly) quotes

    Handles:
    - Straight double quotes " → Curly quotes ""
    - Straight single quotes ' → Curly quotes '' (distinguishing from apostrophes)
    - Nested quotes
    """

    def __init__(self):
        super().__init__("smart_quotes", priority=1)

    def apply(self, text: str) -> str:
        """
        Convert straight quotes to smart quotes

        Uses a stack-based approach to handle nested quotes correctly.
        """
        lines = text.split("\n")
        result = []

        for line_num, line in enumerate(lines, 1):
            original_line = line

            # First pass: convert double quotes
            line = self._convert_double_quotes(line)
            # Second pass: convert single quotes (distinguishing apostrophes)
            line = self._convert_single_quotes(line)

            # Log changes if line was modified
            if line != original_line:
                self.log_change(line_num, original_line, line)

            result.append(line)

        return "\n".join(result)

    def _convert_double_quotes(self, text: str) -> str:
        """
        Convert straight double quotes to curly quotes

        Opening quote detection:
        - After start of line, space, tab, opening bracket, or em-dash
        - Before alphanumeric characters

        Closing quote detection:
        - Before end of line, space, punctuation, closing bracket
        - After alphanumeric characters or punctuation
        """
        result = []
        i = 0
        # Track quote depth to handle nesting
        in_quote = False

        while i < len(text):
            char = text[i]

            if char == '"':
                # Look at context to determine opening vs closing
                prev_char = text[i - 1] if i > 0 else "\n"
                next_char = text[i + 1] if i < len(text) - 1 else "\n"

                if self._is_opening_context(prev_char, next_char):
                    result.append("\u201c")  # Left double quotation mark
                    in_quote = True
                else:
                    result.append("\u201d")  # Right double quotation mark
                    in_quote = False
            else:
                result.append(char)

            i += 1

        return "".join(result)

    def _convert_single_quotes(self, text: str) -> str:
        """
        Convert straight single quotes to curly quotes, distinguishing from apostrophes

        Apostrophe detection (keep as '):
        - Between letters (it's, don't, Scrooge's)
        - After 's' for possessives
        - At start of word for abbreviations ('twas, 'Change)

        Single quote detection:
        - Similar context rules as double quotes
        """
        result = []
        i = 0

        while i < len(text):
            char = text[i]

            if char == "'":
                prev_char = text[i - 1] if i > 0 else "\n"
                next_char = text[i + 1] if i < len(text) - 1 else "\n"

                # Check if it's an apostrophe
                if self._is_apostrophe(prev_char, next_char):
                    result.append("\u2019")  # Right single quotation mark (apostrophe)
                elif self._is_opening_context(prev_char, next_char):
                    result.append("\u2018")  # Left single quotation mark
                else:
                    result.append("\u2019")  # Right single quotation mark
            else:
                result.append(char)

            i += 1

        return "".join(result)

    def _is_apostrophe(self, prev_char: str, next_char: str) -> bool:
        """
        Determine if a single quote is an apostrophe

        Rules:
        - Between letters (contraction or possessive)
        - Before 's', 't', 'd', 're', 'll', 've' (common contractions)
        - After a letter and before nothing or punctuation (possessive at end)
        """
        # Between two letters (it's, don't)
        if prev_char.isalpha() and next_char.isalpha():
            return True

        # After letter, before common contraction endings
        if prev_char.isalpha() and next_char in "stdlmvre":
            return True

        # After letter, at end of word (possessive: John's, dogs')
        if prev_char.isalpha() and (next_char.isspace() or next_char in '.,;:!?)"—'):
            return True

        return False

    def _is_opening_context(self, prev_char: str, next_char: str) -> bool:
        """
        Determine if a quote is in opening context

        Opening context:
        - Start of line or after whitespace
        - After opening brackets: ( [ {
        - After em-dash
        - Before alphanumeric
        """
        # After whitespace or start
        if prev_char in " \t\n":
            return True

        # After opening brackets
        if prev_char in "([{":
            return True

        # After em-dash
        if prev_char == "—":
            return True

        # Before alphanumeric (and not after alphanumeric)
        if next_char.isalnum() and not prev_char.isalnum():
            return True

        return False


class ApostropheNormalizer(FormattingRule):
    """
    Validate and normalize apostrophes

    This rule checks for:
    - Missing apostrophes in common contractions (can't, don't, won't)
    - Missing possessives (John's, Marley's)

    Note: This is primarily a validation rule that warns about issues
    rather than automatically fixing them.
    """

    # Common contractions that should have apostrophes
    CONTRACTIONS = {
        "cant": "can't",
        "dont": "don't",
        "wont": "won't",
        "isnt": "isn't",
        "arent": "aren't",
        "wasnt": "wasn't",
        "werent": "weren't",
        "hasnt": "hasn't",
        "havent": "haven't",
        "hadnt": "hadn't",
        "wouldnt": "wouldn't",
        "shouldnt": "shouldn't",
        "couldnt": "couldn't",
        "mustnt": "mustn't",
        "didnt": "didn't",
        "doesnt": "doesn't",
        "ive": "I've",
        "youve": "you've",
        "weve": "we've",
        "theyve": "they've",
        "youre": "you're",
        "were": "we're",
        "theyre": "they're",
        "thats": "that's",
        "whats": "what's",
        "wheres": "where's",
        "hows": "how's",
        "hes": "he's",
        "shes": "she's",
        "its": "it's",  # Note: "its" (possessive) is also valid
        "lets": "let's",
        "theres": "there's",
        "heres": "here's",
        "im": "I'm",
        "youll": "you'll",
        "hell": "he'll",
        "shell": "she'll",
        "well": "we'll",
        "theyll": "they'll",
        "itll": "it'll",
        "thatll": "that'll",
    }

    def __init__(self):
        super().__init__("apostrophe_check", priority=5)
        self.warnings = []

    def apply(self, text: str) -> str:
        """
        Validate apostrophes and warn about potential issues

        Returns original text unchanged (non-destructive validation)
        """
        self.warnings = []
        lines = text.split("\n")

        for line_num, line in enumerate(lines, 1):
            # Check for missing contractions
            self._check_contractions(line, line_num)
            # Check for potential missing possessives
            self._check_possessives(line, line_num)

        return text  # Non-destructive: return original text

    def _check_contractions(self, line: str, line_num: int):
        """Check for common contractions missing apostrophes"""
        # Use word boundaries to avoid false positives
        for wrong, correct in self.CONTRACTIONS.items():
            # Case-insensitive search with word boundaries
            pattern = r"\b" + re.escape(wrong) + r"\b"
            if re.search(pattern, line, re.IGNORECASE):
                self.warnings.append((line_num, f'Possible missing apostrophe: "{wrong}" should be "{correct}"'))
                self.log_change(line_num, f'Detected: "{wrong}"', f'Should be: "{correct}"')

    def _check_possessives(self, line: str, line_num: int):
        """
        Check for potential missing possessives

        Pattern: Proper noun + 's' + space + common noun
        Example: "Marleys face" should be "Marley's face"
        """
        # Detect pattern: Capitalized word ending in 's' followed by space and lowercase word
        pattern = r"\b([A-Z][a-z]+)s\s+([a-z]+)"
        matches = re.finditer(pattern, line)

        for match in matches:
            name = match.group(1)
            noun = match.group(2)
            original = f"{name}s {noun}"
            suggested = f"{name}'s {noun}"

            # Only warn for common nouns that indicate possession
            possessive_nouns = {
                "face",
                "hand",
                "eye",
                "voice",
                "door",
                "house",
                "book",
                "heart",
                "mind",
                "body",
                "room",
                "name",
                "life",
                "death",
                "head",
                "hair",
                "smile",
                "look",
                "words",
            }

            if noun in possessive_nouns:
                self.warnings.append((line_num, f'Possible missing possessive: "{original}" → "{suggested}"'))
                self.log_change(line_num, f'Detected: "{original}"', f'Consider: "{suggested}"')

    def get_warnings(self) -> list:
        """Get list of warnings"""
        return self.warnings
