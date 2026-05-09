# Instruction file 肥大化リファクタリング チェックリスト

instruction file（CLAUDE.md / agents/*.md / skills/**/SKILL.md）の肥大化を判定するための観点と検出方法。検出のみで終わらず、判定ごとに整理戦略を選択して実際にリファクタするための判断基準。

公式基準の引用と URL は `~/.claude/skills/instruction-refactor/references/official-criteria.md` を参照。整理戦略の詳細は `~/.claude/skills/instruction-refactor/references/strategies.md` を参照。

## 判定 1: 公式定量基準

| 種別 | 上限 | 出典 |
|---|---|---|
| `SKILL.md` | **500 行** | Anthropic 公式 skills doc |
| `description + when_to_use` | 1,536 文字 (truncate point) | Anthropic 公式 skills doc |
| `name` | 64 文字 | Anthropic 公式 skills doc |

CLAUDE.md / agents/*.md は公式に数値基準なし。代わりに「肥大化警告」が明示されている: "Bloated CLAUDE.md files cause Claude to ignore your actual instructions"。

検出方法:

- `wc -l` で各ファイルの行数を計測
- `SKILL.md` で 500 行を超えるものを抽出
- CLAUDE.md / agents/*.md は同種ファイルの平均からの外れ値（**平均の 3 倍以上**）を抽出

## 判定 2: 構造的悪さ（4 類型）

### 2a. 責務越境

「提案するだけ」「観察するだけ」と明記されている agent / skill が、実装詳細（hook 雛形 sh、テンプレート全文、公式仕様の抜粋）を内包していないか。

検出方法:

- agent 定義の役割記述（role / responsibility）を Read
- 同ファイル内に「提案のみ」「自分では編集しない」「観察のみ」等の宣言があるか確認
- それと同時に sh / json / フルテンプレートが書かれているなら **責務越境** の疑い

### 2b. SSOT 逸脱

別のファイルが SSOT として管理しているはずの情報を抜粋・複写していないか。

代表的な SSOT:

- `/skill-creator`: スキル作成テンプレート、Writing Style、description 最適化
- `~/.claude/CLAUDE.md`: グローバル汎用性ルール、Git ルール、書式ルール、エージェント関連ルール
- `~/.claude/agents/reviewer.md`: 観点マッピング、Fan-Out Gate プロトコル
- `~/.claude/agents/refactor-advisor.md`: 言語イディオムガードレール
- Claude Code 公式 doc: hook 仕様、settings.json スキーマ、permissions、skills 構造

検出方法: SSOT を Read → 監査対象ファイルが類似内容を含むか grep 確認。

### 2c. DRY 違反

複数ファイルにほぼ字句同一のセクションがコピーされていないか（特に PIR² 系スキル群、複数の reviewer 系スキル間）。

検出方法:

- 監査対象群を pairwise で比較
- 連続 5 行以上の重複 + セクション見出しの対応 → DRY 違反候補
- 解消策: 共通の `references/` に外出しして両方から参照

### 2d. 二重説明

同じファイル内で同じ手順・概念を 2 回以上説明していないか（典型: 定義セクションと実行セクションで同内容を書く）。

検出方法: ファイル内で同じキーワード・コードブロックが複数の見出し下に登場 → 統合 or 片方を参照に。

## 判定 3: スキルの description 適切性

skill-creator のガイドに準拠しているか:

- 自然言語トリガー語句が **3〜5 個** 列挙されているか
- 「明示的に名指ししなくても発火」の指示があるか
- 「`/<name>` と入力したら必ずこのスキルを使う」の指示があるか

検出方法: フロントマターの `description` を Read → pushy パターンに準拠しているか確認。

## 判定 4: グローバル汎用性ルール（ユーザースコープのみ）

`~/.claude/agents/*.md` / `~/.claude/skills/**/SKILL.md` にプロジェクト固有名（クラス名・テーブル名・API エンドポイント名・具体的なフレームワーク名・特定のディレクトリパス）が混入していないか。

検出方法: 対象ファイルから `GORM`, `util/`, 特定のクラス名サフィックス（`*Usecase`, `*Repository` などの仮名は OK だが具体名は NG）を grep。

詳細は `~/.claude/CLAUDE.md` の「グローバルファイルの汎用性ルール」を参照。

## 整理戦略の選択

検出された問題ごとに整理戦略を選ぶ。詳細は `~/.claude/skills/instruction-refactor/references/strategies.md` を参照。

| 問題種別 | 推奨戦略 |
|---|---|
| 公式上限超過 | Progressive Disclosure（references/ への外出し） |
| DRY 違反 | 共通骨格を 1 箇所に集約 + 参照 |
| SSOT 逸脱 | 抜粋を削除し参照のみに |
| 責務越境 | 実装詳細を削除し SSOT を参照 |
| 二重説明 | 片方を削除し参照に |
| description 不適切 | `/skill-creator` の Description Optimization を提案 |
| プロジェクト固有名混入 | プロジェクトスコープに移すか、本文ではなく参照に変える |
