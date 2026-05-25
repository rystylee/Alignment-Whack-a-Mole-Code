# English Text Formatter Specification

## 概要

英語小説テキストの組版品質を向上させるための後処理フォーマッタ仕様書

## 制作方針

ソース文章の文体・表現・表記スタイルを尊重し、本フォーマッタはあくまで文字化けの防止・タイポグラフィの改善・最低限の組版品質の確保を目的とする。文章表現に干渉するような変更は行わない。

---

## ソーステキストの分析結果

### 対象テキスト
- ファイル: `a_christmas_carol_generated.txt`
- ジャンル: 英語小説（クラシック文学）

### 現状の特徴

#### 1. 引用符のスタイル
- **現状**: ストレートクォート（`"`）を使用
- **問題**: タイポグラフィとして不適切
- **対応**: カーリークォート（スマートクォート）`""` への変換が必要
- **使用例**:
  - 会話文: `"Bah!" said Scrooge, "Humbug!"`
  - アポストロフィ: `Scrooge's`, `'Change`

#### 2. ダッシュの使用
- **現状**: エムダッシュ（`—`）を正しく使用
- **スタイル**: 前後にスペースなし（例：`spot—say Saint Paul's`）
- **評価**: 正しい用法、維持すべき

#### 3. 省略記号
- **現状**: テキスト内にほぼ見当たらない
- **対応**: `...` が出現した場合、Unicode `…` に統一

#### 4. 段落スタイル
- **現状**: インデントなし、1行空けのブロックスタイル
- **評価**: 一貫性あり、維持すべき
- **会話文**: 独立段落として記述

#### 5. 会話文のフォーマット
- Dialogue tag はカンマで繋がれている
  - 正: `"Bah!" said Scrooge, "Humbug!"`
- 感嘆符・疑問符の後はカンマ不要
  - 正: `"Uncle!" pleaded the nephew.`
  - 誤: `"Uncle!," pleaded the nephew.`

#### 6. 数字の表記
- **小さい数字**: スペルアウト（例：`one coal`, `seven-years'`）
- **大きな数字**: 一部スペルアウト（例：`twenty times`, `fifty cooks`）
- **序数詞**: スペルアウト（例：`first time`）
- **評価**: 既に適切に処理されている

#### 7. 検出された問題点

| 問題 | 例 | 優先度 |
|------|-----|--------|
| ストレートクォート | `"text"` → `"text"` | 高 |
| 重複段落 | lines 50-59 と 39-48 が同一 | 中 |
| イタリック表記 | `_Scrooge_` | 低 |
| 所有格の欠落 | `Marleys face` → `Marley's face` | 高 |
| 不完全な文 | line 1173: `"Green body and yellow tail` | - |

---

## デフォルト設定

ソーステキストの分析と一般的な英語組版の慣習に基づき、以下のデフォルト設定を採用：

| 設定項目 | デフォルト値 | 根拠 |
|----------|-------------|------|
| 引用符スタイル | ダブルカーリークォート `""` | 米国式、最も一般的 |
| 三点リーダー | Unicode `…` | 現代的な標準 |
| 段落スタイル | ブロックスタイル（1行空け） | ソーステキストに合わせる |
| 句読点位置 | 米国式（クォート内） | 米国出版物の標準 |
| エムダッシュ | 前後スペースなし | シカゴマニュアル準拠 |
| エンダッシュ | 範囲表記のみ | 数字・日付の範囲 |

---

## 処理ルール詳細

### Phase 1: 基本正規化（優先度 1-10）

#### 1. SmartQuoteConverter (priority=1) ⭐ 最優先

**目的**: タイポグラフィの改善

**処理内容**:
- ストレートダブルクォート `"` → カーリークォート `"` `"`
- ストレートシングルクォート `'` → カーリーシングル `'` `'`（アポストロフィと区別）
- 文脈解析による開始・終了の判定

**判定ロジック**:
```
開始クォート（"）:
- 行頭
- スペース・タブの後
- 開き括弧の後: ( [ {
- エムダッシュの後

終了クォート（"）:
- 行末
- 句読点の前: , . ! ? ; :
- 閉じ括弧の前: ) ] }
- スペースの前
```

**アポストロフィの判定**:
```
アポストロフィ（'）:
- 文字と文字の間（所有格・短縮形）: it's, don't, Scrooge's
- 単語の先頭で省略を示す: 'twas, 'Change

クォート（' '）:
- 上記以外の文脈
```

**例**:
```
入力: "Hello," she said. "It's John's book."
出力: "Hello," she said. "It's John's book."
```

#### 2. EllipsisNormalizer (priority=2)

**目的**: 省略記号の統一

**処理内容**:
- `...` または `.. .` または `. . .` → `…`（U+2026）
- 既に `…` の場合はそのまま維持
- 複数連続の省略記号を1つに統一: `……` → `…`

**例**:
```
入力: He said... "Wait."
出力: He said… "Wait."
```

#### 3. DashNormalizer (priority=3)

**目的**: ダッシュの適切な使用

**処理内容**:
- 二重ハイフン `--` → エムダッシュ `—`
- エムダッシュの前後の不要なスペースを削除
- 数字範囲のハイフン → エンダッシュ `–`（例：`1999-2003` → `1999–2003`）
- ハイフン付き複合語はそのまま維持（例：`well-known`）

**スペース処理**:
```
誤: word — word
正: word—word
```

**範囲表記の判定**:
```
パターン: 数字-数字
例: 1999-2003 → 1999–2003
例: pp. 12-15 → pp. 12–15
```

**例**:
```
入力: He ran -- fast -- to the door.
出力: He ran—fast—to the door.

入力: The years 1999-2003 were eventful.
出力: The years 1999–2003 were eventful.
```

#### 4. BlankLineNormalizer (priority=4)

**目的**: 過剰な空行の整理

**処理内容**:
- 3行以上の連続空行 → 2行に削減
- 文書の先頭・末尾の空行を削除

**重複段落検出** (非破壊):
- 完全に同一の段落が複数回出現する場合、警告を出力
- 自動削除はしない（手動確認を推奨）

**例**:
```
入力:
Paragraph 1.


Paragraph 2.

出力:
Paragraph 1.

Paragraph 2.
```

#### 5. ApostropheNormalizer (priority=5)

**目的**: アポストロフィの正規化

**処理内容**:
- 所有格・短縮形のアポストロフィを正しい向きに: `'`
- 明らかに欠落している所有格を検出し警告（自動修正はしない）

**検出パターン**:
```
警告すべきパターン:
- 固有名詞 + s + スペース + 名詞（例: Marleys face）
- 代名詞の短縮形の誤り（例: dont, cant, wont）
```

**例**:
```
入力: Its Johns book. (誤り)
警告: Line X: "Its" should be "It's" or "Johns" should be "John's"
出力: Its Johns book. (変更なし、警告のみ)
```

---

### Phase 2: 会話・段落処理（優先度 11-20）

#### 6. DialogueFormatter (priority=11)

**目的**: 会話文の適切なフォーマット

**処理内容**:
- セリフが独立段落になっているか確認（警告のみ）
- Dialogue tag の句読点チェック
  - 正: `"Text," she said.`
  - 誤: `"Text" she said.`
- 感嘆符・疑問符の後の不要なカンマを削除
  - 誤: `"Stop!," he said.`
  - 正: `"Stop!" he said.`

**検証のみ実施**:
- セリフと地の文の混在を検出し警告
- 自動的な改行挿入はしない

**例**:
```
入力: "Hello" she said.
警告: Line X: Missing comma after dialogue: "Hello" she said.

入力: "Stop!," he shouted.
出力: "Stop!" he shouted.
```

#### 7. ParagraphStyleValidator (priority=12) - 非破壊的

**目的**: 段落スタイルの一貫性チェック

**処理内容**:
- ブロックスタイル（1行空け）とインデントスタイルの混在を検出
- 警告のみ、自動修正はしない

**判定基準**:
```
インデント検出:
- 行頭にスペースまたはタブがある段落が50%以上

ブロックスタイル検出:
- 段落間に空行がある場合が50%以上
```

#### 8. MarkupConverter (priority=13)

**目的**: Markdown風マークアップの処理

**処理内容**:
- `_text_` → そのまま維持（警告を出力）
- `*text*` → そのまま維持（警告を出力）
- 将来的には設定で削除または適切な Unicode イタリック文字への変換を検討

**例**:
```
入力: The word _italic_ is emphasized.
警告: Line X: Markdown-style markup detected: _italic_
出力: The word _italic_ is emphasized. (変更なし)
```

---

### Phase 3: タイポグラフィ検証（優先度 90-99）

#### 9. TypographyValidator (priority=98) - 非破壊的

**目的**: タイポグラフィの問題を検出

**検証項目**:
1. **ストレートクォートの残存**
   - `"` `'` が残っている場合、警告

2. **ダッシュとハイフンの誤用**
   - スペース + ハイフン + スペース（エムダッシュを使うべき）
   - 日付・範囲でハイフンを使用（エンダッシュを使うべき）

3. **連続スペース**
   - 2つ以上の連続スペースを検出

4. **不適切な改行**
   - 文中の不自然な改行を検出

**例**:
```
警告例:
- Line 42: Straight quote detected: "
- Line 78: Consecutive spaces detected
- Line 105: Consider using em-dash instead of " - "
```

#### 10. EncodingValidator (priority=99) - 非破壊的

**目的**: エンコーディングの問題を検出

**検証項目**:
1. **基本ASCII範囲外の文字**
   - 通常の句読点・引用符・ダッシュ以外の特殊文字を検出
   - Unicode コードポイントとともに報告

2. **プラットフォーム依存文字**
   - 絵文字やその他の特殊記号を検出

3. **制御文字**
   - 印刷不可能な制御文字を検出

**例**:
```
警告例:
- Line 12: Non-ASCII character detected: U+2022 '•' (Bullet)
- Line 45: Unusual character detected: U+00A0 (Non-breaking space)
```

---

## ファイル構成

```
postprocess/
├── formatting_rule.py          # 基底クラス（japanese_formatterと共通化）
├── japanese_formatter.py       # 既存の日本語フォーマッタ
├── english_formatter.py        # 新規：英語テキストフォーマッタ（メインクラス）
└── english_rules/              # 新規：英語用ルール群
    ├── __init__.py
    ├── quote_rules.py          # SmartQuoteConverter, ApostropheNormalizer
    ├── dash_rules.py           # DashNormalizer
    ├── ellipsis_rules.py       # EllipsisNormalizer
    ├── blank_line_rules.py     # BlankLineNormalizer
    ├── dialogue_rules.py       # DialogueFormatter, ParagraphStyleValidator
    ├── markup_rules.py         # MarkupConverter
    └── validators.py           # TypographyValidator, EncodingValidator
```

---

## 実装ステップ

### Step 1: 基底クラスの共通化
- [ ] `FormattingRule` を `formatting_rule.py` として独立
- [ ] `japanese_formatter.py` を新しい基底クラスを使うように修正

### Step 2: Phase 1 ルールの実装
- [ ] `SmartQuoteConverter` - 最優先・最重要
- [ ] `EllipsisNormalizer`
- [ ] `DashNormalizer`
- [ ] `BlankLineNormalizer`
- [ ] `ApostropheNormalizer`

### Step 3: Phase 2 ルールの実装
- [ ] `DialogueFormatter`
- [ ] `ParagraphStyleValidator`
- [ ] `MarkupConverter`

### Step 4: Phase 3 検証ルールの実装
- [ ] `TypographyValidator`
- [ ] `EncodingValidator`

### Step 5: メインフォーマッタの実装
- [ ] `EnglishNovelFormatter` クラス
- [ ] 設定管理システム
- [ ] ログ出力機能

### Step 6: テストとドキュメント
- [ ] `a_christmas_carol_generated.txt` を使用したテスト
- [ ] 変更内容の検証
- [ ] README の作成
- [ ] 使用例の追加

---

## 技術的な課題と対処方針

### 1. スマートクォート変換の複雑性

**課題**:
- 開始クォート vs 終了クォートの判定
- アポストロフィ vs シングルクォートの判定
- 入れ子のクォート処理（`"He said, 'Hello.'"`）

**対処方針**:
- **スタックベースの実装**を採用
- クォートのネストレベルを追跡
- 文脈（前後の文字）を分析して判定
- エッジケースは警告を出力して手動確認を促す

### 2. Dialogue tag の検出

**課題**:
- `"Text," she said.` のパターン認識
- 複数行にわたるセリフの処理
- Action beat との区別（`"Text." She stood up.`）

**対処方針**:
- **正規表現 + 文脈解析**
- 一般的な dialogue verb のリストを使用（said, asked, replied, etc.）
- 曖昧なケースは警告のみで変更しない

### 3. 重複段落の検出

**課題**:
- 完全一致の検出
- 類似段落（わずかな違い）の扱い

**対処方針**:
- ハッシュ値による完全一致検出
- 類似度検出は将来の拡張として保留
- 検出結果は警告のみ、自動削除はしない

### 4. 数字のスペルアウト

**課題**:
- 範囲の判定（1-99 は簡単だが、文脈依存のケースがある）
- 序数詞の処理（1st, 2nd → first, second）
- 日付・統計との区別

**対処方針**:
- **現時点では実装を保留**
- ソーステキストは既に適切にスペルアウトされている
- 将来的には `inflect` ライブラリの活用を検討

---

## 設定例

### デフォルト設定（Phase 1）
```python
DEFAULT_CONFIG = {
    "smart_quotes": True,           # スマートクォート変換
    "ellipsis_style": "unicode",    # "unicode" (…) or "dots" (...)
    "dash_normalize": True,         # ダッシュ正規化
    "blank_lines": True,            # 空行正規化
    "apostrophe_check": True,       # アポストロフィ検証
}
```

### Phase 2 設定（会話・段落処理を含む）
```python
PHASE2_CONFIG = {
    **DEFAULT_CONFIG,
    "dialogue_format": True,        # 会話文フォーマット検証
    "paragraph_style_check": True,  # 段落スタイル検証
    "markup_warn": True,            # マークアップ警告
}
```

### Phase 3 設定（全検証を含む）
```python
PHASE3_CONFIG = {
    **PHASE2_CONFIG,
    "typography_validate": True,    # タイポグラフィ検証
    "encoding_validate": True,      # エンコーディング検証
}
```

---

## 使用例（予定）

```bash
# 基本的な使用
python postprocess/english_formatter.py input.txt -o output.txt

# Phase 2 まで実行
python postprocess/english_formatter.py input.txt -o output.txt --phase 2

# 詳細ログを表示
python postprocess/english_formatter.py input.txt -o output.txt --verbose

# ログファイルに出力
python postprocess/english_formatter.py input.txt -o output.txt --log format.log

# カスタム設定
python postprocess/english_formatter.py input.txt -o output.txt \
  --ellipsis-style dots \
  --no-dialogue-format
```

---

## 参考資料

### タイポグラフィ標準
- The Chicago Manual of Style (17th Edition)
- The Elements of Typographic Style by Robert Bringhurst
- Butterick's Practical Typography

### 引用符とダッシュの使い方
- [Smartquotes.js - Quote Types](https://smartquotes.js.org/)
- [Em Dash, En Dash, and Hyphen: Differences and When to Use](https://www.grammarly.com/blog/dash/)
- [Quotation Marks: American vs. British](https://www.thepunctuationguide.com/quotation-marks.html)

### Unicode標準
- [Unicode Standard](https://www.unicode.org/standard/standard.html)
- [Unicode Punctuation](https://unicode-table.com/en/blocks/general-punctuation/)

---

## 更新履歴

- 2026-05-22: 初版作成（ソーステキスト分析とルール策定）
