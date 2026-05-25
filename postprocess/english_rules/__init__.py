"""
English formatting rules for novels
"""

from .blank_line_rules import BlankLineNormalizer
from .dash_rules import DashNormalizer
from .dialogue_rules import DialogueFormatter, ParagraphStyleValidator
from .ellipsis_rules import EllipsisNormalizer
from .markup_rules import MarkupConverter
from .quote_rules import ApostropheNormalizer, SmartQuoteConverter
from .validators import EncodingValidator, TypographyValidator

__all__ = [
    "SmartQuoteConverter",
    "ApostropheNormalizer",
    "DashNormalizer",
    "EllipsisNormalizer",
    "BlankLineNormalizer",
    "DialogueFormatter",
    "ParagraphStyleValidator",
    "MarkupConverter",
    "TypographyValidator",
    "EncodingValidator",
]
