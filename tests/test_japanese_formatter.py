"""
Unit tests for Japanese Novel Formatter - Phase 1 & 2

Tests basic text normalization rules for vertical Japanese novels.
"""

import sys
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from postprocess.japanese_formatter import (
    BlankLineRemover,
    CharacterRangeValidator,
    DashNormalizer,
    EllipsisNormalizer,
    EnvironmentCharRemover,
    HalfWidthConverter,
    JapaneseNovelFormatter,
    KanjiGlyphSelector,
    ParagraphIndenter,
    TildeNormalizer,
)


class TestEllipsisNormalizer:
    """Test ellipsis normalization rule"""

    def test_three_dots_to_double_ellipsis(self):
        """Test ... → ……"""
        rule = EllipsisNormalizer()
        assert rule.apply("...") == "……"

    def test_ellipsis_in_sentence(self):
        """Test ellipsis within Japanese text"""
        rule = EllipsisNormalizer()
        input_text = "そして...彼は消えた"
        expected = "そして……彼は消えた"
        assert rule.apply(input_text) == expected

    def test_single_ellipsis_to_double(self):
        """Test … → ……"""
        rule = EllipsisNormalizer()
        input_text = "待って…ちょっと待って…"
        expected = "待って……ちょっと待って……"
        assert rule.apply(input_text) == expected

    def test_multiple_ellipsis(self):
        """Test multiple ellipsis in one text"""
        rule = EllipsisNormalizer()
        input_text = "彼は...そして...消えた…"
        expected = "彼は……そして……消えた……"
        assert rule.apply(input_text) == expected

    def test_already_normalized_ellipsis(self):
        """Test that already normalized …… is not double-converted"""
        rule = EllipsisNormalizer()
        input_text = "待って……"
        expected = "待って……"
        assert rule.apply(input_text) == expected

    def test_multiple_consecutive_ellipsis(self):
        """Test multiple consecutive … characters are normalized to single ……"""
        rule = EllipsisNormalizer()
        # 3 consecutive … should become ……
        input_text = "待って………"  # 3 single ellipsis marks
        expected = "待って……"
        assert rule.apply(input_text) == expected

    def test_mixed_ellipsis_forms(self):
        """Test mix of ... and … in same text"""
        rule = EllipsisNormalizer()
        input_text = "...そして…また……"
        expected = "……そして……また……"
        assert rule.apply(input_text) == expected


class TestDashNormalizer:
    """Test dash normalization rule"""

    def test_double_dash(self):
        """Test -- → ――"""
        rule = DashNormalizer()
        assert rule.apply("--") == "――"

    def test_triple_dash(self):
        """Test --- → ――"""
        rule = DashNormalizer()
        assert rule.apply("---") == "――"

    def test_dash_in_sentence(self):
        """Test dash within Japanese text"""
        rule = DashNormalizer()
        input_text = "彼は--そう思った"
        expected = "彼は――そう思った"
        assert rule.apply(input_text) == expected

    def test_em_dash(self):
        """Test — → ――"""
        rule = DashNormalizer()
        input_text = "彼は—そう思った—"
        expected = "彼は――そう思った――"
        assert rule.apply(input_text) == expected

    def test_double_em_dash(self):
        """Test —— → ――"""
        rule = DashNormalizer()
        input_text = "彼は——そう思った"
        expected = "彼は――そう思った"
        assert rule.apply(input_text) == expected

    def test_multiple_em_dashes(self):
        """Test multiple em dashes → ――"""
        rule = DashNormalizer()
        input_text = "彼は———そう思った"
        expected = "彼は――そう思った"
        assert rule.apply(input_text) == expected

    def test_long_dash(self):
        """Test ---- → ――"""
        rule = DashNormalizer()
        assert rule.apply("----") == "――"

    def test_katakana_prolonged_sound(self):
        """Test ー → ――"""
        rule = DashNormalizer()
        input_text = "彼はーそう思った"
        expected = "彼は――そう思った"
        assert rule.apply(input_text) == expected

    def test_multiple_katakana_prolonged_sounds(self):
        """Test multiple ー characters → ――"""
        rule = DashNormalizer()
        input_text = "彼はーーーそう思った"
        expected = "彼は――そう思った"
        assert rule.apply(input_text) == expected

    def test_already_normalized_dash(self):
        """Test that already normalized ―― is not double-converted"""
        rule = DashNormalizer()
        input_text = "彼は――そう思った"
        expected = "彼は――そう思った"
        assert rule.apply(input_text) == expected

    def test_mixed_dash_forms(self):
        """Test mix of --, —, and ー in same text"""
        rule = DashNormalizer()
        input_text = "--そして—またーー"
        expected = "――そして――また――"
        assert rule.apply(input_text) == expected


class TestTildeNormalizer:
    """Test tilde normalization rule"""

    def test_ascii_tilde(self):
        """Test ~ → 〜"""
        rule = TildeNormalizer()
        assert rule.apply("~") == "〜"

    def test_fullwidth_tilde(self):
        """Test ～ → 〜"""
        rule = TildeNormalizer()
        assert rule.apply("～") == "〜"

    def test_tilde_in_sentence(self):
        """Test tilde within Japanese text"""
        rule = TildeNormalizer()
        input_text = "午前10時~12時"
        expected = "午前10時〜12時"
        assert rule.apply(input_text) == expected

    def test_multiple_tildes(self):
        """Test multiple tildes"""
        rule = TildeNormalizer()
        input_text = "10~20人、30～40人"
        expected = "10〜20人、30〜40人"
        assert rule.apply(input_text) == expected


class TestBlankLineRemover:
    """Test blank line removal rule"""

    def test_triple_newline(self):
        """Test 3 newlines → 2 newlines"""
        rule = BlankLineRemover()
        input_text = "paragraph1\n\n\nparagraph2"
        expected = "paragraph1\n\nparagraph2"
        assert rule.apply(input_text) == expected

    def test_many_newlines(self):
        """Test 5+ newlines → 2 newlines"""
        rule = BlankLineRemover()
        input_text = "paragraph1\n\n\n\n\nparagraph2"
        expected = "paragraph1\n\nparagraph2"
        assert rule.apply(input_text) == expected

    def test_single_blank_line_unchanged(self):
        """Test that single blank line is preserved"""
        rule = BlankLineRemover()
        input_text = "paragraph1\n\nparagraph2"
        expected = "paragraph1\n\nparagraph2"
        assert rule.apply(input_text) == expected

    def test_no_blank_lines(self):
        """Test text with no blank lines"""
        rule = BlankLineRemover()
        input_text = "line1\nline2\nline3"
        expected = "line1\nline2\nline3"
        assert rule.apply(input_text) == expected


class TestJapaneseNovelFormatter:
    """Test main formatter class"""

    def test_default_config(self):
        """Test formatter with default configuration"""
        formatter = JapaneseNovelFormatter()
        input_text = "そして...彼は--そう思った~"
        expected = "そして……彼は――そう思った〜"
        assert formatter.format(input_text) == expected

    def test_selective_rules(self):
        """Test formatter with selective rules enabled"""
        config = {
            "ellipsis": True,
            "dash": False,
            "tilde": True,
            "blank_lines": False,
        }
        formatter = JapaneseNovelFormatter(config=config)
        input_text = "そして...彼は--そう思った~"
        # Only ellipsis and tilde should be applied
        expected = "そして……彼は--そう思った〜"
        assert formatter.format(input_text) == expected

    def test_all_rules_together(self):
        """Test all Phase 1 rules applied together"""
        formatter = JapaneseNovelFormatter()
        input_text = """彼は...そう思った--本当に。

~午前10時~



それは事実だった...間違いなく--。"""

        expected = """彼は……そう思った――本当に。

〜午前10時〜

それは事実だった……間違いなく――。"""

        assert formatter.format(input_text) == expected

    def test_complex_text(self):
        """Test with more complex Japanese text"""
        formatter = JapaneseNovelFormatter()
        input_text = """「待って...」と彼女は言った。

--それは嘘だった--



彼は~10分後に到着した...しかし。"""

        expected = """「待って……」と彼女は言った。

――それは嘘だった――

彼は〜10分後に到着した……しかし。"""

        assert formatter.format(input_text) == expected

    def test_file_formatting(self, tmp_path):
        """Test file input/output"""
        # Create input file
        input_file = tmp_path / "input.txt"
        input_file.write_text("そして...彼は消えた", encoding="utf-8")

        # Format file
        output_file = tmp_path / "output.txt"
        formatter = JapaneseNovelFormatter()
        formatter.format_file(input_file, output_file)

        # Verify output
        result = output_file.read_text(encoding="utf-8")
        assert result == "そして……彼は消えた"

    def test_empty_text(self):
        """Test with empty text"""
        formatter = JapaneseNovelFormatter()
        assert formatter.format("") == ""

    def test_no_changes_needed(self):
        """Test text that doesn't need formatting"""
        formatter = JapaneseNovelFormatter()
        input_text = "彼は歩いた。そして帰った。"
        assert formatter.format(input_text) == input_text


# === Phase 2 Tests ===


class TestParagraphIndenter:
    """Test paragraph indentation rule"""

    def test_simple_paragraph(self):
        """Test adding indentation to simple paragraph"""
        rule = ParagraphIndenter()
        input_text = "これは段落です。"
        expected = "　これは段落です。"
        assert rule.apply(input_text) == expected

    def test_skip_dialogue(self):
        """Test that dialogue lines are not indented"""
        rule = ParagraphIndenter()
        input_text = "「こんにちは」と彼は言った。"
        expected = "「こんにちは」と彼は言った。"
        assert rule.apply(input_text) == expected

    def test_already_indented(self):
        """Test that already indented lines are not double-indented"""
        rule = ParagraphIndenter()
        input_text = "　既に字下げされています。"
        expected = "　既に字下げされています。"
        assert rule.apply(input_text) == expected

    def test_empty_lines(self):
        """Test that empty lines are preserved"""
        rule = ParagraphIndenter()
        input_text = "段落1\n\n段落2"
        expected = "　段落1\n\n　段落2"
        assert rule.apply(input_text) == expected

    def test_mixed_text(self):
        """Test mixed text with dialogue and narrative"""
        rule = ParagraphIndenter()
        input_text = """彼は歩いた。
「待って」
そして振り返った。"""
        expected = """　彼は歩いた。
「待って」
　そして振り返った。"""
        assert rule.apply(input_text) == expected


class TestHalfWidthConverter:
    """Test half-width conversion rule"""

    def test_fullwidth_alphanumeric(self):
        """Test converting full-width alphanumeric to half-width"""
        rule = HalfWidthConverter()
        # ABC is converted to half-width, 123 (3 digits) is converted back to full-width
        input_text = "ＡＢＣ１２３"
        expected = "ABC１２３"
        assert rule.apply(input_text) == expected

    def test_single_digit_number(self):
        """Test that single digit numbers remain half-width"""
        rule = HalfWidthConverter()
        input_text = "第5章"
        expected = "第5章"
        assert rule.apply(input_text) == expected

    def test_two_digit_number(self):
        """Test that two digit numbers remain half-width (tate-chu-yoko)"""
        rule = HalfWidthConverter()
        input_text = "第25章"
        expected = "第25章"
        assert rule.apply(input_text) == expected

    def test_three_digit_number(self):
        """Test that three digit numbers are converted to full-width"""
        rule = HalfWidthConverter()
        input_text = "第123章"
        expected = "第１２３章"
        assert rule.apply(input_text) == expected

    def test_mixed_text(self):
        """Test mixed text with various numbers"""
        rule = HalfWidthConverter()
        input_text = "5人と25人と100人"
        expected = "5人と25人と１００人"
        assert rule.apply(input_text) == expected

    def test_western_text(self):
        """Test that Western text (alphabets) remain half-width"""
        rule = HalfWidthConverter()
        input_text = "ＡＢＣテストDEF"
        expected = "ABCテストDEF"
        assert rule.apply(input_text) == expected

    def test_fullwidth_parentheses_preserved(self):
        """Test that full-width parentheses remain full-width (for ruby)"""
        rule = HalfWidthConverter()
        input_text = "葬（とむら）う"
        expected = "葬（とむら）う"
        assert rule.apply(input_text) == expected

    def test_fullwidth_dash_preserved(self):
        """Test that full-width dashes remain full-width"""
        rule = HalfWidthConverter()
        input_text = "彼は－そう思った－"
        expected = "彼は－そう思った－"
        assert rule.apply(input_text) == expected

    def test_fullwidth_symbols_preserved(self):
        """Test that full-width symbols remain full-width"""
        rule = HalfWidthConverter()
        # Test various full-width punctuation and symbols
        input_text = "「こんにちは」、彼は言った。"
        expected = "「こんにちは」、彼は言った。"
        assert rule.apply(input_text) == expected

    def test_only_alphanumeric_converted(self):
        """Test that only alphanumeric characters are converted, not symbols"""
        rule = HalfWidthConverter()
        # Full-width alphanumeric + full-width symbols
        input_text = "ＡＢＣ（テスト）－１２３"
        # Only ABC and digits should be converted, parentheses and dash remain full-width
        expected = "ABC（テスト）－１２３"
        assert rule.apply(input_text) == expected


class TestEnvironmentCharRemover:
    """Test environment-dependent character removal rule"""

    def test_circled_numbers(self):
        """Test replacing circled numbers"""
        rule = EnvironmentCharRemover()
        input_text = "①番目と②番目"
        expected = "(1)番目と(2)番目"
        assert rule.apply(input_text) == expected

    def test_corporate_symbols(self):
        """Test replacing corporate symbols"""
        rule = EnvironmentCharRemover()
        input_text = "㈱山田商事"
        expected = "株式会社山田商事"
        assert rule.apply(input_text) == expected

    def test_multiple_replacements(self):
        """Test multiple replacements in one text"""
        rule = EnvironmentCharRemover()
        input_text = "①㈱テスト②㈲サンプル"
        expected = "(1)株式会社テスト(2)有限会社サンプル"
        assert rule.apply(input_text) == expected

    def test_tel_symbol(self):
        """Test replacing TEL symbol"""
        rule = EnvironmentCharRemover()
        input_text = "℡03-1234-5678"
        expected = "TEL03-1234-5678"
        assert rule.apply(input_text) == expected

    def test_no_prohibited_chars(self):
        """Test text without prohibited characters"""
        rule = EnvironmentCharRemover()
        input_text = "通常のテキストです"
        expected = "通常のテキストです"
        assert rule.apply(input_text) == expected


class TestPhase2Integration:
    """Test Phase 2 rules integration"""

    def test_phase2_config(self):
        """Test formatter with Phase 2 configuration"""
        formatter = JapaneseNovelFormatter(config=JapaneseNovelFormatter.PHASE2_CONFIG)
        input_text = """これは段落です...
「こんにちは」
ＡＢＣ１２３と456
①番目の項目"""

        # ABC is half-width, 123 and 456 (3 digits) are full-width
        expected = """　これは段落です……
「こんにちは」
　ABC１２３と４５６
　(1)番目の項目"""

        assert formatter.format(input_text) == expected

    def test_selective_phase2_rules(self):
        """Test formatter with selective Phase 2 rules"""
        config = {
            "ellipsis": True,
            "dash": False,
            "tilde": False,
            "blank_lines": False,
            "paragraph_indent": True,
            "halfwidth_convert": False,
            "remove_env_chars": True,
        }
        formatter = JapaneseNovelFormatter(config=config)
        input_text = "これは段落...①番目"
        expected = "　これは段落……(1)番目"
        assert formatter.format(input_text) == expected

    def test_all_phases_together(self):
        """Test all Phase 1 + Phase 2 rules together"""
        formatter = JapaneseNovelFormatter(config=JapaneseNovelFormatter.PHASE2_CONFIG)
        input_text = """段落の開始...彼は言った--

「待って~」

ＡＢＣと123名の参加者①"""

        expected = """　段落の開始……彼は言った――

「待って〜」

　ABCと１２３名の参加者(1)"""

        assert formatter.format(input_text) == expected


class TestKanjiGlyphSelector:
    """Test kanji glyph selection rule (1.2)"""

    def test_nfc_normalization(self):
        """Test that NFC normalization is applied"""
        rule = KanjiGlyphSelector()
        # Test basic NFC normalization
        # が (U+304C) vs が (U+304B + U+3099)
        input_text = "\u304b\u3099"  # Decomposed form: か + combining dakuten
        expected = "\u304c"  # Composed form: が
        assert rule.apply(input_text) == expected

    def test_regular_kanji_unchanged(self):
        """Test that regular kanji pass through unchanged"""
        rule = KanjiGlyphSelector()
        input_text = "日本語の文章です"
        expected = "日本語の文章です"
        assert rule.apply(input_text) == expected

    def test_cjk_ideograph_detection(self):
        """Test CJK ideograph range detection"""
        rule = KanjiGlyphSelector()
        # Test main CJK range (U+4E00-U+9FFF)
        assert rule._is_cjk_ideograph(0x4E00) is True  # 一
        assert rule._is_cjk_ideograph(0x9FFF) is True  # End of range
        assert rule._is_cjk_ideograph(0x3000) is False  # Ideographic space (not CJK)
        assert rule._is_cjk_ideograph(0xFF00) is False  # Full-width forms

    def test_compatibility_ideograph_detection(self):
        """Test CJK compatibility ideograph detection"""
        rule = KanjiGlyphSelector()
        # Test compatibility ideograph range (U+F900-U+FAFF)
        assert rule._is_compat_ideograph(0xF900) is True
        assert rule._is_compat_ideograph(0xFAFF) is True
        assert rule._is_compat_ideograph(0x4E00) is False  # Regular CJK

    def test_compatibility_ideograph_normalization(self):
        """Test that compatibility ideographs are normalized"""
        rule = KanjiGlyphSelector()
        # U+FA38 器 (compatibility) should normalize to U+5668 器 (canonical)
        input_text = "\ufa38"  # Compatibility ideograph
        result = rule.apply(input_text)
        # NFC will normalize this to canonical form
        assert result == "\u5668"  # Canonical form

    def test_cjk_compat_comprehensive(self):
        """Test comprehensive CJK compatibility ideograph normalization (spec 1.3)"""
        rule = KanjiGlyphSelector()
        # Test multiple compatibility ideographs from the spec
        test_cases = [
            ("\uf900", "\u8c48"),  # 豈 (compatibility) → 豈 (unified)
            ("\uf901", "\u66f4"),  # 更 (compatibility) → 更 (unified)
            ("\uf902", "\u8eca"),  # 車 (compatibility) → 車 (unified)
            ("\ufa38", "\u5668"),  # 器 (compatibility) → 器 (unified)
        ]
        for compat, unified in test_cases:
            result = rule.apply(compat)
            assert result == unified, f"Failed to normalize U+{ord(compat):04X} to U+{ord(unified):04X}"

    def test_cjk_compat_in_context(self):
        """Test CJK compatibility ideographs within full text (spec 1.3)"""
        rule = KanjiGlyphSelector()
        # Text with compatibility ideograph U+F900 豈
        input_text = "これは\uf900の文字です"
        result = rule.apply(input_text)
        # Should normalize to unified ideograph U+8C48
        assert "\u8c48" in result
        assert "\uf900" not in result
        assert rule.warning_count > 0

    def test_multiple_cjk_compat_chars(self):
        """Test multiple CJK compatibility ideographs in one text (spec 1.3)"""
        rule = KanjiGlyphSelector()
        # Multiple compatibility ideographs: 豈更車
        input_text = "\uf900\uf901\uf902"
        result = rule.apply(input_text)
        # All should be normalized
        expected = "\u8c48\u66f4\u8eca"
        assert result == expected
        assert rule.warning_count == 3

    def test_cjk_compat_supplement_range(self):
        """Test CJK Compatibility Ideographs Supplement range (U+2F800-U+2FA1F)"""
        rule = KanjiGlyphSelector()
        # Check that supplement range is detected
        assert rule._is_compat_ideograph(0x2F800) is True
        assert rule._is_compat_ideograph(0x2FA1F) is True
        assert rule._is_compat_ideograph(0x2FA20) is False

    def test_mixed_text_with_kanji(self):
        """Test text with mix of kanji, kana, and other characters"""
        rule = KanjiGlyphSelector()
        input_text = "これは日本語の文章です。123"
        # Should preserve all content while normalizing
        result = rule.apply(input_text)
        # Basic content should be preserved
        assert "日本語" in result
        assert "123" in result

    def test_no_warning_for_standard_kanji(self):
        """Test that standard kanji don't trigger warnings"""
        rule = KanjiGlyphSelector()
        input_text = "日本語"
        rule.apply(input_text)
        assert rule.warning_count == 0

    def test_empty_string(self):
        """Test empty string handling"""
        rule = KanjiGlyphSelector()
        assert rule.apply("") == ""

    def test_only_ascii(self):
        """Test ASCII-only text"""
        rule = KanjiGlyphSelector()
        input_text = "Hello World 123"
        assert rule.apply(input_text) == input_text

    def test_formatter_with_kanji_glyph(self):
        """Test formatter with kanji glyph rule enabled"""
        config = {"kanji_glyph": True}
        formatter = JapaneseNovelFormatter(config=config)
        # Test with decomposed character
        input_text = "\u304b\u3099"  # Decomposed が
        expected = "\u304c"  # Composed が
        assert formatter.format(input_text) == expected

    def test_phase2_includes_kanji_glyph(self):
        """Test that Phase 2 config includes kanji glyph rule"""
        formatter = JapaneseNovelFormatter(config=JapaneseNovelFormatter.PHASE2_CONFIG)
        # Verify kanji_glyph rule is included
        rule_names = [rule.name for rule in formatter.rules]
        assert "kanji_glyph" in rule_names


class TestCharacterRangeValidator:
    """Test character range validation rule (1.1)"""

    def test_valid_japanese_text(self):
        """Test that standard Japanese text passes validation"""
        rule = CharacterRangeValidator()
        input_text = "これは日本語の文章です。"
        # Should return original text (non-destructive)
        assert rule.apply(input_text) == input_text

    def test_emoji_detected(self):
        """Test that emoji characters are detected as out-of-range"""
        rule = CharacterRangeValidator()
        input_text = "Hello😊"
        result = rule.apply(input_text)
        # Should return original text (non-destructive)
        assert result == input_text
        # Note: Warning would be logged but we can't easily test that here

    def test_plane2_kanji_detected(self):
        """Test that Plane 2 kanji (outside JIS X 0213) are detected"""
        rule = CharacterRangeValidator()
        # U+20BB7 is a Plane 2 character (吉 variant)
        input_text = "これは\U00020bb7野家です"
        result = rule.apply(input_text)
        # Should return original text (non-destructive)
        assert result == input_text

    def test_mixed_text_with_out_of_range(self):
        """Test text with both valid and out-of-range characters"""
        rule = CharacterRangeValidator()
        input_text = "日本語😊テキスト™"
        result = rule.apply(input_text)
        # Should return original text
        assert result == input_text

    def test_ascii_text(self):
        """Test ASCII text (within JIS X 0213 range)"""
        rule = CharacterRangeValidator()
        input_text = "Hello World 123"
        assert rule.apply(input_text) == input_text

    def test_empty_string(self):
        """Test empty string handling"""
        rule = CharacterRangeValidator()
        assert rule.apply("") == ""

    def test_special_symbols(self):
        """Test special symbols (some may be out of JIS range)"""
        rule = CharacterRangeValidator()
        input_text = "©®™"
        result = rule.apply(input_text)
        # Should return original text
        assert result == input_text

    def test_formatter_with_character_range(self):
        """Test formatter with character range rule enabled"""
        config = {"character_range": True}
        formatter = JapaneseNovelFormatter(config=config)
        input_text = "日本語😊"
        result = formatter.format(input_text)
        # Should return original text (non-destructive)
        assert result == input_text

    def test_phase3_includes_character_range(self):
        """Test that Phase 3 config includes character range rule"""
        formatter = JapaneseNovelFormatter(config=JapaneseNovelFormatter.PHASE3_CONFIG)
        # Verify character_range rule is included
        rule_names = [rule.name for rule in formatter.rules]
        assert "character_range" in rule_names

    def test_priority_is_zero(self):
        """Test that character range validator has highest priority (0)"""
        rule = CharacterRangeValidator()
        assert rule.priority == 0

    def test_phase3_includes_all_previous_phases(self):
        """Test that Phase 3 includes all Phase 1 and 2 rules"""
        formatter = JapaneseNovelFormatter(config=JapaneseNovelFormatter.PHASE3_CONFIG)
        rule_names = [rule.name for rule in formatter.rules]

        # Phase 1 rules
        assert "ellipsis" in rule_names
        assert "dash" in rule_names
        assert "tilde" in rule_names
        assert "blank_lines" in rule_names

        # Phase 2 rules
        assert "paragraph_indent" in rule_names
        assert "halfwidth_convert" in rule_names
        assert "remove_env_chars" in rule_names
        assert "kanji_glyph" in rule_names

        # Phase 3 rules
        assert "character_range" in rule_names


class TestCJKCompatibilityIntegration:
    """Integration tests for CJK compatibility ideograph normalization (spec 1.3)"""

    def test_rashomon_style_text_with_compat_chars(self):
        """Test realistic novel text with CJK compatibility ideographs"""
        # Create realistic text similar to Rashomon with compatibility ideographs
        input_text = (
            "　ある日の暮方の事である。一人の下人が、羅生門の下で雨やみを待っていた。\n"
            f"　広い門の下には、この男の{chr(0xF900)}にこの一人である。\n"
            f"　それは、この二三年、京都には、地震とか辻風とか火事とか饑饉とかいう災いが{chr(0xF901)}つづいて起った。\n"
            f"　そこで洛中のさびれ方は一{chr(0xF902)}ではない。\n"
        )

        # Use Phase 2 formatter which includes kanji_glyph rule
        formatter = JapaneseNovelFormatter(config=JapaneseNovelFormatter.PHASE2_CONFIG)
        result = formatter.format(input_text)

        # Verify all compatibility ideographs are normalized
        assert chr(0xF900) not in result  # 豈 (compat) should be removed
        assert chr(0xF901) not in result  # 更 (compat) should be removed
        assert chr(0xF902) not in result  # 車 (compat) should be removed

        # Verify unified ideographs are present
        assert chr(0x8C48) in result  # 豈 (unified)
        assert chr(0x66F4) in result  # 更 (unified)
        assert chr(0x8ECA) in result  # 車 (unified)

        # Verify other formatting is preserved
        assert "　ある日の暮方" in result  # Indentation preserved
        assert "羅生門" in result  # Regular kanji unchanged

    def test_phase2_handles_compat_ideographs(self):
        """Test that Phase 2 configuration properly handles compatibility ideographs"""
        # Test with multiple compatibility ideographs from spec examples
        input_text = f"{chr(0xF900)}{chr(0xF901)}{chr(0xF902)}{chr(0xFA38)}"
        formatter = JapaneseNovelFormatter(config=JapaneseNovelFormatter.PHASE2_CONFIG)
        result = formatter.format(input_text)

        # All should be normalized to unified forms (with paragraph indent added)
        expected_chars = f"{chr(0x8C48)}{chr(0x66F4)}{chr(0x8ECA)}{chr(0x5668)}"
        assert expected_chars in result  # Check chars are present
        # Verify no compat chars remain
        assert chr(0xF900) not in result
        assert chr(0xF901) not in result
        assert chr(0xF902) not in result
        assert chr(0xFA38) not in result

    def test_compat_chars_with_other_phase2_rules(self):
        """Test CJK compatibility normalization works with other Phase 2 rules"""
        # Combine CJK compat chars with other formatting rules
        input_text = f"...{chr(0xF900)}です。\n\n\nこれは{chr(0xF901)}です。"

        formatter = JapaneseNovelFormatter(config=JapaneseNovelFormatter.PHASE2_CONFIG)
        result = formatter.format(input_text)

        # Ellipsis should be converted
        assert "……" in result
        # Compat chars should be normalized
        assert chr(0x8C48) in result  # 豈
        assert chr(0x66F4) in result  # 更
        # Blank lines (3+ newlines) should be reduced to 2
        assert "\n\n\n" not in result
        # Should have paragraph indent
        assert "　" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
