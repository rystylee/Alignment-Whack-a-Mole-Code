"""
Unit tests for Japanese Novel Formatter - Phase 1

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
    JapaneseNovelFormatter,
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
