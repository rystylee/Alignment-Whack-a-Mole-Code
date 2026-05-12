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
    DashNormalizer,
    EllipsisNormalizer,
    EnvironmentCharRemover,
    HalfWidthConverter,
    JapaneseNovelFormatter,
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

    def test_long_dash(self):
        """Test ---- → ――"""
        rule = DashNormalizer()
        assert rule.apply("----") == "――"


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
