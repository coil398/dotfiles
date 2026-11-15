## 探索レポート: 新規エージェント epic-planner の型・テンプレート抽出

### 関連ファイル一覧

| ファイルパス | 役割・内容 | 参照対象 |
|------------|-----------|---------|
| `.claude/agents/planner.md` | プラン策定専任エージェント。frontmatter、CORE セクション、プランレポートフォーマット、実装規模見積もり決定木の実装例 | 型・フォーマット抽出元 |
| `.claude/agents/explorer.md` | コードベース探索専任エージェント。frontmatter の共通パターン確認用 | 比較参照 |
| `.claude/agents/reviewer.md` | コードレビュー専任エージェント。frontmatter と CORE の共通パターン確認用 | 比較参照 |
| `.claude/skills/pir2/references/experimental.md` | PIR² 実験レジストリ。起票テンプレートと既存実験項目の構造化 | 起票テンプレート抽出元 |

---

## 【1】agent frontmatter の型：原文引用

### 1.1 planner.md frontmatter（`.claude/agents/planner.md` lines 1-14）

```yaml
---
name: planner
description: 実装プラン策定専任エージェント。スキル本体から受け取ったタスク内容と探索レポートをもとに、implementer が迷わず実行できる具体的な実装プランを返す。PIR²ワークフローのプラン策定フェーズで使用する。
model: opus
tools:
  - Read
  - Write
  - Glob
  - Grep
  - Bash
  - WebFetch
  - WebSearch
  - Agent
---
```

### 1.2 explorer.md frontmatter（`.claude/agents/explorer.md` lines 1-12）

```yaml
---
name: explorer
description: コードベース探索専用エージェント。スキル本体（メイン Claude）などのオーケストレーターから呼び出され、Glob・Grep・Read でコードベースを調査し、必要に応じて WebFetch・WebSearch で外部ドキュメント（ライブラリ公式 doc、README、Issue/Discussion 等）の裏取りも行い、構造化された探索レポートを返す。探索範囲が広い場合は呼び出し元のオーケストレーターが explorer を複数体並列起動する。
model: sonnet
tools:
  - Glob
  - Grep
  - Read
  - Write
  - Bash
  - WebFetch
  - WebSearch
---
```

### 1.3 reviewer.md frontmatter（`.claude/agents/reviewer.md` lines 1-11）

```yaml
---
name: reviewer
description: 実装済みコードをレビューするエージェント。VERDICT: PASS/FAILを冒頭に出力し、問題点を構造化フォーマットで返す。/pir2 ワークフローのレビューフェーズおよび /reviewer スキルから使用する。REVIEWER_ROLE で担当観点を切り替え、呼び出し元はこのエージェントを correctness / consistency / quality / security / architecture の5観点から必要なものを選択して 1〜5 体並列で起動する運用（ハイブリッド並列）。
model: sonnet
tools:
  - Read
  - Write
  - Glob
  - Grep
  - Bash
  - Agent
---
```

### 1.4 共通パターン（frontmatter）

- **フィールド構成**: `name` / `description` / `model` / `tools` の 4 要素
- **model の値**: `opus`（オーケストレーター・判断層）または `sonnet`（特化タスク層）
- **tools のパターン**:
  - planner: `Read, Write, Glob, Grep, Bash, WebFetch, WebSearch, Agent`（フル。能動探索 + control なし）
  - explorer: `Glob, Grep, Read, Write, Bash, WebFetch, WebSearch`（control 不可。ネストされる側）
  - reviewer: `Read, Write, Glob, Grep, Bash, Agent`（レビュー＋ネスト探索。control 不可）
- **description**: エージェント名 + 役割 + 使用フェーズ / スキル の 3 層で書く

**epic-planner 向けの型**:

```yaml
---
name: epic-planner
description: [大型タスク分割専任エージェント]。[スキル本体から受け取った大規模タスク と探索レポートをもとに、]実装をどう分割するか・各 shard / unit の最適な粒度・依存順序を決定し、planner が直列実装 unit へ分割できる具体的な分割戦略を返す。PIR² ワークフローの[タスク分割フェーズで使用する]。
model: opus
tools:
  - Read
  - Write
  - Glob
  - Grep
  - Bash
  - Agent
---
```

---

## 【2】CORE セクションの書式：planner.md 原文引用 + epic-planner への応用

### 2.1 planner.md の CORE セクション（`.claude/agents/planner.md` lines 16-21）

```markdown
<!-- CORE: このセクションは変更禁止 -->
あなたはエキスパートのソフトウェアアーキテクトです。スキル本体（メイン Claude）から受け取ったタスク内容と探索レポートをもとに、implementer が迷わず実行できる具体的な実装プランを策定してください。
**すべての出力は日本語で行うこと。**
**最終出力は必ず「プランレポートフォーマット」に従うこと。**
**`Agent` ツールで explorer をネスト起動できる（Claude Code v2.1.172〜）。プラン策定中に広域探索が必要なら自分で explorer を起動してよい（後述「能動探索」）。ただし implementer / reviewer / tester の起動・ループ管理・ユーザー確認ゲートはスキル本体（メイン Claude）に集約する設計のため、あなたは起動しない。プラン策定に集中せよ。**
<!-- /CORE -->
```

### 2.2 reviewer.md の CORE セクション（`.claude/agents/reviewer.md` lines 15-20）

```markdown
<!-- CORE: このセクションは変更禁止 -->
実装済みコードを徹底的にレビューし、構造化されたフォーマットで結果を返してください。
**すべての出力は日本語で行うこと。**
**出力の最初の行は必ず `VERDICT: PASS` または `VERDICT: FAIL` にすること。**
**このレビューはエージェント間通信用であり、人間向けの説明調の文体は不要。最終レポートは構造化フォーマットに従うこと。ただし検証・調査・思考の過程は短絡させず、判定の根拠を必要十分に残すこと（出力の圧縮対象は最終レポートの表現のみで、推論そのものは圧縮しない）。**
**入力 `REVIEWER_ROLE`（`correctness` / `consistency` / `quality` / `security` / `architecture` / `all`）に応じて担当する観点を切り替えること。「レビュー観点」セクションの role マッピングに従い、自分の担当観点のみをレビューする（他観点は別の reviewer が並列で担当している場合があるため重複レビュー不要。今回のタスクで他観点が起動されていない可能性もあるが、それでも自分の担当観点だけをレビューする）。`all` または未指定時は全観点を見る（後方互換）。**
<!-- /CORE -->
```

### 2.3 CORE セクション の構成要素（比較分析）

| 要素 | planner | reviewer | epic-planner 向け |
|------|---------|----------|------------------|
| **冒頭 1 行** | 「あなたはエキスパートの○○です」型の role 宣言 | 「○○を徹底的に△△する」型の動詞宣言 | 「あなたは○○専任エージェントです」型 |
| **出力言語** | `**すべての出力は日本語で行うこと。**` | `**すべての出力は日本語で行うこと。**` | 共通ルール（すべてに必須） |
| **フォーマット強制** | `**最終出力は必ず「プランレポートフォーマット」に従うこと。**` | `**出力の最初の行は必ず `VERDICT: PASS` または...` | 「分割戦略レポートフォーマット」に従うこと |
| **ツール・能動探索** | Agent ツール使用 + explorer ネスト起動の許可・制限明示 | Agent ツール使用 + explorer ネスト起動の許可（読み取り専用） | 同 planner（control 不可） |
| **責務境界** | 「implementer / reviewer / tester の起動はスキル本体に集約」 | 「REVIEWER_ROLE に応じて観点を切り替え」「他観点は別の reviewer が担当」 | 「分割戦略策定のみ。unit ごとの implementer 起動はスキル本体に集約」 |
| **CORE の性質** | 変更禁止。動作制約・責務分界の定義が不変 | 変更禁止。role マッピング・フォーマット要件が不変 | 変更禁止。責務・出力フォーマット要件が不変 |

### 2.4 epic-planner 向けの CORE テンプレート案

```markdown
<!-- CORE: このセクションは変更禁止 -->
あなたは大型タスク分割エキスパートです。スキル本体（メイン Claude）から受け取った大規模タスク内容と探索レポートをもとに、実装を効率よく分割できる具体的な分割戦略を策定してください。
**すべての出力は日本語で行うこと。**
**最終出力は必ず「分割戦略レポートフォーマット」に従うこと。**
**`Agent` ツールで explorer をネスト起動できる（Claude Code v2.1.172〜）。分割戦略策定中に関連パターン・既存実装の再確認が必要なら自分で explorer を起動してよい（後述「能動探索」）。ただし planner / implementer / reviewer / tester の起動・ループ管理・ユーザー確認ゲートはスキル本体（メイン Claude）に集約する設計のため、あなたは起動しない。分割戦略の策定に集中せよ。**
<!-- /CORE -->
```

---

## 【3】出力フォーマットの型：planner.md のプランレポートフォーマット構造

### 3.1 planner.md プランレポートフォーマット 骨子（`.claude/agents/planner.md` lines 332-414）

```markdown
## プランレポート: [タスク名]

### 概要
[変更の目的と全体像を1〜2文で]

### 実装ステップ
1. [ステップ名]: `path/to/file` — [変更内容の具体的な指示]
2. ...

### IMPLEMENTATION_SHARDS（試験実装・完全に独立した実装 shard がある場合のみ）
- SHARD_ID: SHARD_A
  - 目的: [この shard が実装する範囲]
  - 許可ファイル/ディレクトリ: [この shard が触ってよいパス]
  - 禁止ファイル/ディレクトリ: [触ってはいけないパス]
  - 依存する shard: [none または他の SHARD_ID]
  - 想定成果物: `{RUN_DIR}/implementation-{IMPL_INDEX}-{SHARD_ID}.md`
- ...

### IMPLEMENTATION_UNITS（試験実装・大きいが結合していて直列分割する場合のみ）
- UNIT_ID: UNIT_1
  - 目的: [この unit が実装する範囲]
  - 主対象ファイル: [この unit が主に触るパス]
  - 依存する先行 unit: [none または先行 UNIT_ID]
  - 想定成果物: `{RUN_DIR}/implementation-{IMPL_INDEX}-unit-{UNIT_ID}.md`
- ...

### 適用される既存ルール（必須）
- 照合した参照元: [...]
- 適用されるルール一覧:
  - [ルール名] — [本プランでどう適用したか、または「該当なし」]
- 違反検出の有無: [...]

### 既存パターン照合結果
- 対象: [型/ディレクトリ/スキーマフィールド等]
- 既存の慣例: [grep で確認した既存パターンの要約]
- 今回のプランの整合性: [合致している / 逸脱している]

### 既存パターン逸脱の事前申告（該当する場合のみ）
- 逸脱内容: [...]
- 逸脱理由: [...]
- 既存パターンに合わせた代替案: [...]
- **スキル本体への依頼**: [...]

### USER_DECISION_REQUIRED（複数案・スコープ縮小・外部依存ギャップを含む場合は必須）
- 判断要請の理由: [...]
- 選択肢:
  - (A) [案 A の概要] — [影響範囲・前提・トレードオフ]
  - (B) [...]
- 推奨案: [...]
- **スキル本体への依頼**: [...]

### 全適用箇所リスト（該当する場合のみ）
- [ロジック名/バリアント名]
  - `path/to/file1:function_name` — [適用内容]
  - `path/to/file2:function_name` — [...]

### テスト・検証方法
- **追加/更新が必要なテストファイル**: [...]
- **implementer が自己検証すべき項目**: [...]
- **tester が実行する最小スコープのテストコマンド**: [...]

### 注意点・リスク
- [セキュリティ・パフォーマンス・後方互換性への影響]

### スキル本体への追加調査依頼（該当する場合のみ）
- [探索レポートで不足していた情報]

### EXPLORATION_NEEDED（プラン策定に不足している情報がある場合のみ）
- [topic]: [具体的な調査観点]
```

### 3.2 epic-planner 向けの「分割戦略レポートフォーマット」テンプレート案

```markdown
## 分割戦略レポート: [タスク名]

### 概要
[タスクの規模・複雑度と分割方針を 1〜2 文で]

### 分割判定
- タスク規模: [小さい実装 / 大きい実装]
- 分割必要性: [不要 / IMPLEMENTATION_SHARDS 候補 / IMPLEMENTATION_UNITS 候補]
- 理由: [判定根拠]

### 推奨分割戦略
（以下のいずれか 1 つ）

#### パターン A: 分割しない（単一 implementer）
- 理由: [小さい実装 / 計画不成熟 / その他]

#### パターン B: IMPLEMENTATION_SHARDS（並列分割）
- 分割基準: [独立した実装単位の境界]
- SHARD 一覧:
  - SHARD_A:
    - 目的: [実装範囲]
    - 許可ファイル: [...]
    - 禁止ファイル: [...]
    - 依存 shard: none
  - SHARD_B:
    - 目的: [...]
    - ...
- 統合方法: [全 shard 完了後の統合確認手順]
- リスク: [shard 境界の重複・衝突可能性]

#### パターン C: IMPLEMENTATION_UNITS（直列分割）
- 分割基準: [順序依存のある実装単位の切り分け]
- UNIT 一覧:
  - UNIT_1:
    - 目的: [実装範囲]
    - 主対象ファイル: [...]
    - 先行依存: none
  - UNIT_2:
    - 目的: [...]
    - 主対象ファイル: [...]
    - 先行依存: UNIT_1
  - ...
- unit 間の接続点: [先行 unit の実装成果をどう流用するか]
- リスク: [unit 間の命名・抽象のドリフト]

### 適用される既存分割ルール
- 照合対象: [`experimental.md` の既存実験 / 過去 retro の分割パターン]
- 適用ルール: [...]

### USER_DECISION_REQUIRED（複数案がある場合）
- 判断要請の理由: [分割戦略が複数並列で成立する理由]
- 選択肢:
  - (A) [分割戦略 A] — [メリット / デメリット]
  - (B) [分割戦略 B] — [...]
- 推奨案: [...]

### 注意点・リスク
- [分割による並列化コスト・運用複雑性]
- [unit 間境界での不整合リスク]

### EXPLORATION_NEEDED（該当する場合のみ）
- [...]
```

---

## 【4】experimental.md の起票テンプレート

### 4.1 既存実験項目の構造化フォーマット確認

#### 4.1.1 pir2-implementer-sequential-units（`.claude/skills/pir2/references/experimental.md` lines 89-157）

```markdown
## Experiment: pir2-implementer-sequential-units

- Status: Active
- Started: 2026-06-26
- Scope: `.claude/skills/pir2/**`, `.claude/agents/planner.md`, `.claude/skills/pir2codex/**`
- Owner: user
- Recommendation: Continue observing

### Hypothesis
[2〜3 段落。実験する理由・期待効果・前提仮説]

### Implementation
[実装方法・運用ルール・ゲート条件]

### Quality Guardrails
[品質保証・コストチェック・逸脱時の切り替え条件]

### Metrics
[観測項目・計測対象]

### Adoption Criteria
[恒久採用に必要な証拠レベル]

### Rejection Criteria
[廃止判定のしきい値]

### Evidence Summary
- Eligible decisions: N
- Sequential executions: N
- Unit-boundary regressions: N
- Recommendation changes: N

### Observation Log
[観測データは別ファイル記録の指示]
```

#### 4.1.2 pir2-implementer-shards-and-review-fix-shards（`.claude/skills/pir2/references/experimental.md` lines 17-87）

同じ構造。主な違いは Scope が異なり、Hypothesis / Implementation / Quality Guardrails / Metrics / Adoption Criteria / Rejection Criteria が異なるが、**セクション構成は統一**。

### 4.2 起票テンプレート骨子

```markdown
## Experiment: [実験名]

- Status: Active
- Started: YYYY-MM-DD
- Scope: `.claude/agents/**`, `.claude/skills/**`, 等の影響範囲
- Owner: user
- Recommendation: Continue observing / (採用・廃止前の初期値は always Continue observing)

### Hypothesis
[実験背景・期待効果・前提仮説を 2〜3 段落で記載]

### Implementation
[実装方法・運用ルール・ゲート条件・制約を列挙]

### Quality Guardrails
[品質保証・コストチェック・逸脱時の自動切り替え条件]

### Metrics
[観測項目の箇条書き。複数行 OK]

### Adoption Criteria
[恒久採用に必要な条件。3〜5 個の AND 条件]

### Rejection Criteria
[廃止判定のトリガー条件。3〜5 個の OR 条件]

### Evidence Summary
- [Metric 1]: N
- [Metric 2]: N
- Recommendation changes: 0

### Observation Log
観測データ（project / run 等プロジェクト固有名を含む実 run の観測）は git 管理外の `~/.claude/memory/experimental_observations.md` の該当実験セクションに記録する。実験定義はこのファイルが SSOT。
```

### 4.3 epic-planner 実験の起票テンプレート（新規実験用）

```markdown
## Experiment: pir2-epic-planner-task-decomposition

- Status: Active
- Started: 2026-07-03
- Scope: `.claude/agents/epic-planner.md`（新規エージェント）, `.claude/skills/pir2/**`, `.claude/agents/planner.md`
- Owner: user
- Recommendation: Continue observing

### Hypothesis
large-scale タスクを専門に分割する epic-planner エージェントを導入すると、planner の判断負荷を減らし、分割戦略が明確に文書化され、implementer が各 unit / shard の目的・境界を明確に理解した上で実装できるようになる。結果として unit 間の不整合・命名ドリフト・未接続実装が減り、review/test ループが短縮される。

### Implementation
- 新規エージェント `.claude/agents/epic-planner.md` を作成
- frontmatter: `name: epic-planner`, `model: opus`, `tools: [Read, Write, Glob, Grep, Bash, Agent]`
- 責務: 大規模タスクの分割戦略策定のみ。implementer 起動はスキル本体に委譲
- 出力フォーマット: 分割戦略レポート（IMPLEMENTATION_SHARDS / IMPLEMENTATION_UNITS / 単一 implementer のいずれかを判定）
- スキル本体（PIR² オーケストレーター）が explorer → epic-planner → planner → implementer の順序で起動

### Quality Guardrails
- epic-planner は分割判定のみ。個別 unit の詳細実装ステップは planner に委譲する
- 分割判定がぶれていないか（同じタスクで回によって分割方針が逆転していないか）を観測
- epic-planner による分割が過度に細粒度化していないか（unit 数が過多＝並列化の運用コストが逆転していないか）を確認

### Metrics
- epic-planner 起動回数
- 推奨分割戦略（単一 / shards / units）の判定結果分布
- planner が受け取った分割戦略の採用率（修正必要性）
- unit / shard 間の不整合・境界衝突の発生回数
- implementer の質問・スコープ逸脱の減少

### Adoption Criteria
- 3 回以上の epic-planner 実行が蓄積されている
- epic-planner による分割判定が planner に採用されている（修正の必要がない）
- unit / shard 間の命名・抽象の不整合が減少している
- review / test ループ数が従来の単一 planner 運用より悪化していない
- ユーザーが恒久採用してよいと判断している

### Rejection Criteria
- epic-planner の分割判定が不安定（判断根拠がぶれている）
- 細粒度化しすぎて unit 数が過多になり、並列化コストが逆転している
- planner が epic-planner の判定を繰り返し修正せざるを得ず、分業が機能していない
- 分割による品質改善が観測されず、運用複雑性だけが増えている

### Evidence Summary
- Epic-planner executions: 0
- Strategy adoptions: 0
- Unit-boundary regressions: 0
- Recommendation changes: 0

### Observation Log
観測データ（project / run 等プロジェクト固有名を含む実 run の観測）は git 管理外の `~/.claude/memory/experimental_observations.md` の該当実験セクションに記録する。実験定義はこのファイルが SSOT。
```

---

## 補足情報

### 4.4 experimental.md への追記時の手順

1. `## Experiment: [名前]` の見出しで新規セクションを追加（既存実験の末尾に追記）
2. メタデータ（Status, Started, Scope, Owner, Recommendation）を記入
3. 5 つの必須セクション（Hypothesis, Implementation, Quality Guardrails, Metrics, Adoption Criteria, Rejection Criteria）を記入
4. Evidence Summary を初期値で記入（全 metric を 0 で初期化）
5. Observation Log セクションを記入（「git 管理外の別ファイルに記録」と明記）

### 4.5 epic-planner frontmatter の最終案

```yaml
---
name: epic-planner
description: 大型タスク分割専任エージェント。スキル本体から受け取った大規模タスク内容と探索レポートをもとに、実装をどう分割するか・各 unit / shard の最適な粒度・依存順序を決定し、分割戦略レポートを返す。PIR²ワークフローの大規模タスク分割フェーズで使用する。
model: opus
tools:
  - Read
  - Write
  - Glob
  - Grep
  - Bash
  - Agent
---
```

### 4.6 epic-planner CORE の最終案

```markdown
<!-- CORE: このセクションは変更禁止 -->
あなたは大型タスク分割エキスパートです。スキル本体（メイン Claude）から受け取った大規模タスク内容と探索レポートをもとに、実装を効率よく分割できる具体的な分割戦略を策定してください。
**すべての出力は日本語で行うこと。**
**最終出力は必ず「分割戦略レポートフォーマット」に従うこと。**
**`Agent` ツールで explorer をネスト起動できる（Claude Code v2.1.172〜）。分割戦略策定中に関連パターン・既存実装の再確認が必要なら自分で explorer を起動してよい（後述「能動探索」）。ただし planner / implementer / reviewer / tester の起動・ループ管理・ユーザー確認ゲートはスキル本体（メイン Claude）に集約する設計のため、あなたは起動しない。分割戦略の策定に集中せよ。**
<!-- /CORE -->
```

---

## 参照ファイル・行番号一覧

| ファイル | セクション | 行範囲 | 内容 |
|---------|-----------|--------|------|
| `.claude/agents/planner.md` | frontmatter | 1-14 | planner フロントマター（型の基準） |
| `.claude/agents/planner.md` | CORE | 16-21 | planner CORE セクション（文体・責務定義） |
| `.claude/agents/planner.md` | プランレポートフォーマット | 332-414 | プラン出力フォーマット構造 |
| `.claude/agents/planner.md` | 実装規模見積もり | 303-309 | 分割決定木（単一 / SHARDS / UNITS） |
| `.claude/agents/explorer.md` | frontmatter | 1-12 | explorer フロントマター（比較参照） |
| `.claude/agents/reviewer.md` | frontmatter | 1-11 | reviewer フロントマター（比較参照） |
| `.claude/agents/reviewer.md` | CORE | 15-20 | reviewer CORE セクション（比較参照） |
| `.claude/skills/pir2/references/experimental.md` | pir2-implementer-sequential-units | 89-157 | 既存実験テンプレート（UNITS 型） |
| `.claude/skills/pir2/references/experimental.md` | pir2-implementer-shards-and-review-fix-shards | 17-87 | 既存実験テンプレート（SHARDS 型） |
