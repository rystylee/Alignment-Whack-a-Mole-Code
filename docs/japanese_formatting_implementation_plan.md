# 日本語縦書き小説整形プログラム 実装計画書

本ドキュメントは、`postprocess/japanese_formatter.py` の実装計画と技術仕様を定義します。

---

## 1. プロジェクト概要

### 1.1 目的
生成された日本語小説テキストを、縦書き出版に適した形式に自動整形する

### 1.2 実装状況（2026-05-11時点）
- ✅ **フェーズ1（基本整形）**: 完全実装済み（4ルール）
- ✅ **フェーズ2（中級処理）**: 完全実装済み（3ルール）
- ❌ **フェーズ3（高度な処理）**: 未実装（7ルール以上）
- ✅ **テスト**: 43個のユニットテストすべて成功

### 1.3 スコープ
- 入力: テキストファイル(.txt)
- 出力: 整形済みテキストファイル(.txt)
- 対象: 日本語の小説・物語文

### 1.4 実装ファイル
```
postprocess/
└── japanese_formatter.py  # メインスクリプト（Phase 1 & 2実装済み）
tests/
└── test_japanese_formatter.py  # ユニットテスト（43テスト）
```

---

## 2. 技術スタック

### 2.1 必須ライブラリ

#### フェーズ1 (基本整形)
```python
# 標準ライブラリのみ
import re
import unicodedata
import argparse
from pathlib import Path
```

#### フェーズ2 (中級処理)
```python
# 形態素解析
import MeCab  # または
from sudachipy import tokenizer, dictionary

# 文字正規化
import jaconv
```

#### フェーズ3 (高度な処理)
```python
# 固有表現認識
import spacy  # ja_ginza

# NLP補助
from fugashi import Tagger
```

### 2.2 推奨依存関係
```toml
# pyproject.toml または requirements.txt
[dependencies]
jaconv = "^0.3"  # 文字正規化
mecab-python3 = "^1.0"  # 形態素解析(オプション)
unidic-lite = "^1.0"  # MeCab辞書(軽量版)
```

---

## 3. アーキテクチャ設計

### 3.1 クラス構成

```python
# postprocess/japanese_formatter.py

class JapaneseNovelFormatter:
    """
    Main formatter class for vertical Japanese novels
    """

    def __init__(self, config: dict = None):
        """
        Initialize formatter with configuration

        Args:
            config: Configuration dict with rule toggles
        """
        self.config = config or self._default_config()
        self.rules = []
        self._setup_rules()

    def format(self, text: str) -> str:
        """
        Apply all enabled formatting rules

        Args:
            text: Input text string

        Returns:
            Formatted text string
        """
        for rule in self.rules:
            if self.config.get(rule.name, True):
                text = rule.apply(text)
        return text

    def format_file(self, input_path: Path, output_path: Path):
        """
        Format a text file
        """
        text = input_path.read_text(encoding='utf-8')
        formatted = self.format(text)
        output_path.write_text(formatted, encoding='utf-8')


class FormattingRule:
    """
    Base class for formatting rules
    """

    def __init__(self, name: str, priority: int):
        self.name = name
        self.priority = priority

    def apply(self, text: str) -> str:
        """
        Apply the rule to text

        Args:
            text: Input text

        Returns:
            Transformed text
        """
        raise NotImplementedError


# === Phase 1 Rules (Easy) ===

class EllipsisNormalizer(FormattingRule):
    """Normalize ellipsis to 「……」"""

    def apply(self, text: str) -> str:
        # ... → ……
        text = text.replace('...', '……')
        # … → ……
        text = text.replace('…', '……')
        return text


class DashNormalizer(FormattingRule):
    """Normalize dash to 「――」"""

    def apply(self, text: str) -> str:
        # -- or --- → ――
        text = re.sub(r'-{2,}', '――', text)
        # em dash — → ――
        text = text.replace('—', '――')
        return text


class TildeNormalizer(FormattingRule):
    """Normalize tilde to 「〜」"""

    def apply(self, text: str) -> str:
        # ~ → 〜
        text = text.replace('~', '〜')
        # ～ → 〜 (full-width tilde to wave dash)
        text = text.replace('～', '〜')
        return text


class BlankLineRemover(FormattingRule):
    """Remove excessive blank lines"""

    def apply(self, text: str) -> str:
        # Remove 3+ consecutive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text


# === Phase 2 Rules (Medium) ===

class ParagraphIndenter(FormattingRule):
    """Add full-width space indentation to paragraphs"""

    def apply(self, text: str) -> str:
        lines = text.split('\n')
        result = []

        for line in lines:
            # Skip empty lines
            if not line.strip():
                result.append(line)
                continue

            # Skip lines starting with 「 (dialogue)
            if line.strip().startswith('「'):
                result.append(line)
                continue

            # Add indentation if not already present
            if not line.startswith('　'):
                result.append('　' + line)
            else:
                result.append(line)

        return '\n'.join(result)


class HalfWidthConverter(FormattingRule):
    """Convert full-width to half-width for specific cases"""

    def apply(self, text: str) -> str:
        # Convert full-width alphanumeric to half-width
        text = self._convert_alphanumeric(text)
        # Keep 1-2 digit numbers in half-width (tate-chu-yoko)
        text = self._handle_numbers(text)
        return text

    def _convert_alphanumeric(self, text: str) -> str:
        """Convert full-width ASCII to half-width"""
        result = []
        for char in text:
            code = ord(char)
            # Full-width ASCII range (0xFF01-0xFF5E)
            if 0xFF01 <= code <= 0xFF5E:
                result.append(chr(code - 0xFEE0))
            else:
                result.append(char)
        return ''.join(result)

    def _handle_numbers(self, text: str) -> str:
        """Keep 1-2 digit numbers half-width, convert 3+ digits to full-width"""
        def replace_numbers(match):
            num = match.group(0)
            if len(num) <= 2:
                return num  # Keep half-width
            else:
                # Convert to full-width
                return ''.join(chr(ord(c) + 0xFEE0) for c in num)

        return re.sub(r'\d+', replace_numbers, text)


class EnvironmentCharRemover(FormattingRule):
    """Remove environment-dependent characters"""

    # List of prohibited characters
    PROHIBITED_CHARS = {
        '①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩',
        '㈱', '㈲', '㈹', '№', '㏍', '℡',
    }

    REPLACEMENT_MAP = {
        '①': '(1)', '②': '(2)', '③': '(3)', '④': '(4)', '⑤': '(5)',
        '⑥': '(6)', '⑦': '(7)', '⑧': '(8)', '⑨': '(9)', '⑩': '(10)',
        '㈱': '株式会社', '㈲': '有限会社', '㈹': '代表',
        '№': 'No.', '㏍': 'K.K.', '℡': 'TEL',
    }

    def apply(self, text: str) -> str:
        for char, replacement in self.REPLACEMENT_MAP.items():
            text = text.replace(char, replacement)
        return text


# === Phase 3 Rules (Hard) ===

class DialogueFormatter(FormattingRule):
    """Format dialogue with proper line breaks"""

    def __init__(self, name: str, priority: int, use_mecab: bool = False):
        super().__init__(name, priority)
        self.use_mecab = use_mecab
        if use_mecab:
            try:
                import MeCab
                self.tagger = MeCab.Tagger()
            except ImportError:
                self.use_mecab = False

    def apply(self, text: str) -> str:
        """
        Detect dialogue and format with line breaks

        Heuristics:
        - Length > 5 characters
        - Contains verbs or sentence-ending particles
        - Not a single noun (proper noun check)
        """
        # Simple regex-based approach for now
        # TODO: Implement NLP-based detection

        lines = text.split('\n')
        result = []

        for line in lines:
            # Find all quoted text
            quoted_pattern = r'([^「]*)(「[^」]+」)([^「]*)'

            def process_quotes(match):
                before = match.group(1)
                quote = match.group(2)
                after = match.group(3)

                # Check if this is dialogue
                if self._is_dialogue(quote):
                    # Add line breaks
                    parts = []
                    if before.strip():
                        parts.append(before.rstrip())
                    parts.append(quote)
                    if after.strip():
                        parts.append('　' + after.lstrip())
                    return '\n'.join(parts)
                else:
                    # Keep as-is (proper noun, etc.)
                    return match.group(0)

            formatted = re.sub(quoted_pattern, process_quotes, line)
            result.append(formatted)

        return '\n'.join(result)

    def _is_dialogue(self, quoted_text: str) -> bool:
        """
        Determine if quoted text is dialogue or proper noun/emphasis

        Heuristics:
        - Length > 5 characters → likely dialogue
        - Contains punctuation → likely dialogue
        - Length <= 5 and no punctuation → likely proper noun
        """
        content = quoted_text.strip('「」')

        # Length check
        if len(content) <= 5:
            # Check for sentence-ending punctuation
            if any(p in content for p in ['。', '、', '?', '!', '…', '―']):
                return True
            else:
                return False  # Likely proper noun

        return True  # Long text is likely dialogue


class FuriganaAdder(FormattingRule):
    """Add furigana (reading) to difficult kanji"""

    def __init__(self, name: str, priority: int):
        super().__init__(name, priority)
        # Initialize MeCab or other reading engine
        try:
            import MeCab
            self.tagger = MeCab.Tagger()
        except ImportError:
            self.tagger = None

    def apply(self, text: str) -> str:
        """
        Add furigana to difficult kanji

        TODO: Implement kanji difficulty detection
        TODO: Add readings using MeCab
        """
        if not self.tagger:
            return text

        # Placeholder for furigana logic
        return text
```

---

## 4. 実装フェーズ

### フェーズ1: 基本整形 (1-2日) ✅ **実装完了 (2026-05-11)**

**実装ルール**:
- ✅ 三点リーダーの統一 (`EllipsisNormalizer`)
- ✅ ダッシュの統一 (`DashNormalizer`)
- ✅ 波ダッシュの統一 (`TildeNormalizer`)
- ✅ 段落間の空行削除 (`BlankLineRemover`)

**成果物**:
```python
# Basic usage
formatter = JapaneseNovelFormatter(config={
    'ellipsis': True,
    'dash': True,
    'tilde': True,
    'blank_lines': True,
})

formatted_text = formatter.format(input_text)
```

**テスト**:
```python
def test_ellipsis_normalization():
    formatter = JapaneseNovelFormatter()
    input_text = "そして...彼は消えた"
    expected = "そして……彼は消えた"
    assert formatter.format(input_text) == expected
```

---

### フェーズ2: 中級処理 (2-4週間) ✅ **実装完了 (2026-05-11)**

**実装ルール**:
- ✅ 段落の字下げ (`ParagraphIndenter`)
- ✅ 半角/全角の変換 (`HalfWidthConverter`)
- ✅ 環境依存文字の排除 (`EnvironmentCharRemover`)

**追加依存関係**:
```bash
# フェーズ2では標準ライブラリのみ使用（追加依存なし）
# フェーズ3以降で形態素解析が必要な場合に以下を追加:
# uv add jaconv mecab-python3 unidic-lite
```

**成果物**:
```python
formatter = JapaneseNovelFormatter(config={
    # Phase 1
    'ellipsis': True,
    'dash': True,
    # Phase 2
    'paragraph_indent': True,
    'halfwidth_convert': True,
    'remove_env_chars': True,
})
```

---

### フェーズ3: 高度な処理 (4-8週間以上) ❌ **未実装**

**実装ルール**:
- ❌ セリフの自動検出と改行
- ❌ 場面転換の検出
- ❌ 読み仮名の自動付与

**追加依存関係**:
```bash
uv add spacy
python -m spacy download ja_core_news_sm
```

**成果物**:
```python
formatter = JapaneseNovelFormatter(config={
    # All phases
    'dialogue_format': True,
    'scene_break_detect': True,
    'furigana_add': True,
})
```

---

## 5. 設定ファイル

### 5.1 YAML設定 (オプション)

```yaml
# config/formatting_rules.yaml

# Phase 1: Basic formatting
basic:
  ellipsis: true
  dash: true
  tilde: true
  blank_lines: true

# Phase 2: Medium complexity
medium:
  paragraph_indent: true
  halfwidth_convert: true
  remove_env_chars: true

# Phase 3: Advanced
advanced:
  dialogue_format: false  # Disabled by default
  scene_break_detect: false
  furigana_add: false

# Custom replacements
replacements:
  "...": "……"
  "--": "――"
  "~": "〜"
```

---

## 6. CLI インターフェース

```bash
# Basic usage
python postprocess/japanese_formatter.py input.txt -o output.txt

# With config file
python postprocess/japanese_formatter.py input.txt -c config.yaml -o output.txt

# Enable specific rules
python postprocess/japanese_formatter.py input.txt --ellipsis --dash --indent

# Batch processing
python postprocess/japanese_formatter.py data_generated/*.txt -o formatted/
```

### 6.1 引数仕様

```python
import argparse

parser = argparse.ArgumentParser(description='Format Japanese vertical novels')
parser.add_argument('input', type=str, help='Input text file(s)')
parser.add_argument('-o', '--output', type=str, help='Output file or directory')
parser.add_argument('-c', '--config', type=str, help='Config YAML file')
parser.add_argument('--phase', type=int, choices=[1, 2, 3],
                    help='Enable all rules up to phase N')
parser.add_argument('--dry-run', action='store_true',
                    help='Show changes without writing')
```

---

## 7. テスト戦略

### 7.1 ユニットテスト

```python
# tests/test_japanese_formatter.py

import pytest
from postprocess.japanese_formatter import (
    JapaneseNovelFormatter,
    EllipsisNormalizer,
    DashNormalizer,
)

class TestBasicFormatting:
    def test_ellipsis_single(self):
        rule = EllipsisNormalizer('ellipsis', 1)
        assert rule.apply('...') == '……'

    def test_ellipsis_in_sentence(self):
        rule = EllipsisNormalizer('ellipsis', 1)
        input_text = 'そして...彼は消えた'
        expected = 'そして……彼は消えた'
        assert rule.apply(input_text) == expected

    def test_dash_double(self):
        rule = DashNormalizer('dash', 1)
        assert rule.apply('彼は--そう') == '彼は――そう'
```

### 7.2 統合テスト

```python
def test_full_formatting_phase1():
    formatter = JapaneseNovelFormatter(phase=1)
    input_text = Path('tests/fixtures/input.txt').read_text()
    expected = Path('tests/fixtures/expected_phase1.txt').read_text()
    assert formatter.format(input_text) == expected
```

### 7.3 テストデータ

```
tests/
├── fixtures/
│   ├── input.txt              # 元データ
│   ├── expected_phase1.txt    # フェーズ1期待出力
│   ├── expected_phase2.txt    # フェーズ2期待出力
│   └── expected_phase3.txt    # フェーズ3期待出力
└── test_japanese_formatter.py
```

---

## 8. パフォーマンス考慮事項

### 8.1 処理速度
- 正規表現のコンパイル済みキャッシュを使用
- 大きなファイルはチャンク処理

### 8.2 メモリ使用量
- ストリーミング処理オプションの提供
- 行ごとの処理で大容量ファイルに対応

```python
def format_large_file(input_path: Path, output_path: Path):
    """Process large files line by line"""
    with input_path.open('r', encoding='utf-8') as infile, \
         output_path.open('w', encoding='utf-8') as outfile:
        for line in infile:
            formatted = formatter.format(line)
            outfile.write(formatted)
```

---

## 9. 今後の拡張

### 9.1 機械学習モデルの導入
- セリフ vs 固有名詞の分類モデル
- 場面転換検出モデル
- 読み仮名推定モデル

### 9.2 GUI版の開発
- ブラウザベースのプレビュー機能
- リアルタイム整形プレビュー

### 9.3 他フォーマット対応
- EPUB入力対応
- Markdown出力対応

---

## 10. 関連ドキュメント

- [ルール仕様書](./japanese_formatting_spec.md)
- [データ分析結果](./japanese_formatting_analysis.md)
