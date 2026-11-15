## 実装完了レポート

### 変更ファイル一覧
- `.claude/skills/epic/SKILL.md`（新規作成） — 上位オーケストレーションスキル本体。frontmatter（name/description/argument-hint）、冒頭に「3階層ネスト構造」「深さバジェット制約」「ユーザー対話は epic 本体に集約」の3前提を明記。ステップ1（EPIC_RUN_DIR確定+--codexパース）〜ステップ5（最終サマリー）＋「Agent ネスト起動方式の技術整合性」小節を実装。ステップ3-0と技術整合性小節の両方に `model=opus` を必須明記（general-purpose ランナーが SKILL.md 解釈・ループ制御を担うため）。
- `.claude/agents/epic-planner.md`（新規作成） — エピック分割専任エージェント。frontmatter（name/description/model: opus/tools: Read,Write,Glob,Grep,Bash,Agent）、CORE セクション（`<!-- CORE -->`〜`<!-- /CORE -->`対）で役割宣言・日本語出力・「エピック分割レポートフォーマット」強制・分割レベル徹底（実装詳細は出さない）・explorer ネスト起動許可＋制御エージェント起動禁止を明記。本文にプロセス（入力確認→全体探索→分割粒度指針→依存グラフ生成→タスク記述→既存ルール照合→メモリ記録→ファイル書き出し）と「エピック分割レポートフォーマット」（planner.md の「プランレポートフォーマット」とは別物。実装ステップ・IMPLEMENTATION_SHARDS/UNITS は出さない）を定義。
- `CLAUDE.md`（プロジェクト直下、追記） — 3箇所に追記。(1) エージェント定義一覧表に `epic-planner.md` の行を `gate.md` 行の直後に追加。(2) スキル一覧表に `/epic` の行を `/deepthink` 行の直後に追加。(3) 「### PIR² ワークフロー」セクション末尾（`### エージェント定義` の直前）に新規サブセクション「### エピックオーケストレーション (`/epic`・試験実装)」を挿入。全てテキストアンカーによる Edit で、既存本文は無改変（`git diff` で確認）。
- `.claude/skills/pir2/references/experimental.md`（追記） — ファイル末尾に新規実験セクション `## Experiment: epic-orchestrator-nested-pir2` を追加（Status/Started/Scope/Owner/Recommendation + Hypothesis/Implementation/Quality Guardrails/Metrics/Adoption Criteria/Rejection Criteria/Evidence Summary/Observation Log の統一構成）。既存3実験セクションは無改変（`git diff` で削除行なしを確認）。

### 実装概要
大規模タスク（エピック）を `epic-planner` に分割・依存グラフ化させ、DAG に沿って各サブタスクを `/pir2`（`--codex` 時は `/pir2codex`）としてネスト起動する上位オーケストレーションスキル `/epic` と専任エージェント `epic-planner` を新規作成した。plan.md のステップ1〜4に定義された4ファイル（新規2・追記2）のみを対象とし、既存の pir2/pir2codex/planner.md/experimental.md の frontmatter・CORE・出力フォーマット・起票テンプレートの型を Read で確認したうえで厳密に模写した。位置づけは試験実装であり、恒久採用可否は experimental.md の該当実験を観測して判断する設計。

### 注意点・未解決事項

**(1) `.gitignore` の差分について（スコープ外変更ではない）**

`git status` / `git diff` で `.gitignore` に `/.ai-pir-runs/` が1行追記された差分が確認できるが、これは本 implementer が Bash で実行したものではない。plan.md のステップ1に記載の RUN_DIR 確定ロジック（`git -C "$PROJECT_ROOT" rev-parse ...` による `.gitignore` 追記）は epic SKILL.md 本文中に**記述**しただけで、実行はしていない。この差分は呼び出し元スキル本体が本 run の pir2 ステップ1（RUN_DIR確定）で事前に実行した既存差分と判断される。念のため diff 内容を確認したところ追加1行のみで、plan.md の対象4ファイルへの意図しない波及は含まれていない。

**(2) 静的検証の結果**

- 4ファイルとも Write/Edit が成功し、`git status --porcelain` で新規2件（`.claude/agents/epic-planner.md`, `.claude/skills/epic/`）・変更2件（`CLAUDE.md`, `.claude/skills/pir2/references/experimental.md`）を確認した。
- `.claude/skills/epic/SKILL.md` / `.claude/agents/epic-planner.md` の frontmatter は `---` 対で囲まれ `name` フィールドを持つことを確認した。
- `.claude/agents/epic-planner.md` に `<!-- CORE: このセクションは変更禁止 -->` 〜 `<!-- /CORE -->` の対（`grep -c "CORE"` = 2）が存在することを確認した。
- `.claude/skills/epic/SKILL.md` 冒頭に「3階層ネスト構造」「深さバジェット制約」「ユーザー対話は epic 本体に集約」の3前提が明記されていることを `grep -n` で確認した。
- epic SKILL.md ステップ3-0 と「Agent ネスト起動方式の技術整合性」小節の両方に `model=opus` の必須明記があることを確認した。
- epic-planner.md の Write により PostToolUse hook（sync-opencode）が自動発火し、`~/.config/opencode/agents/epic-planner.md` が Write と同時刻（16:46）に生成されていることを `stat` で確認した。
- `git diff CLAUDE.md` は全行 `+`（追加）のみで既存本文の削除・改変がないことを確認した。同様に `.claude/skills/pir2/references/experimental.md` も `git diff --stat` が `63 insertions(+)` のみ（deletions なし）であることを確認した。
- `etc/link.sh` / `.claude/settings.json` / `etc/sync-opencode.sh` / `etc/sync-codex.sh` を変更していないことを `git diff --name-only` で確認した（plan.md「変更不要」に準拠）。
- グローバル汎用性ルールに従い、新規2ファイルにプロジェクト固有名（Unity/Figma 等）が混入していないことを `grep -in` で確認した（該当なし）。
- テストスイート実行はしていない（本タスクはドキュメント著述でテスト対象なし。plan.md「テスト・検証方法」に明記通り）。
- IaC ファイルの変更はないため IaC 構文検証は対象外。
- 実装完了レポート自体は成果物本体だが、上記4ファイル以外への変更（コード実装・git add/commit）は一切行っていない。

**(3) ランタイム挙動は未検証**

深さバジェット（L2 頭打ち）・general-purpose の Read ベース起動方式が実際に機能するかは、本タスク（指示ドキュメント著述）のスコープ外であり、初回 `/epic` 実行時の検証事項として experimental.md の Observation 対象に委ねた（plan.md の想定通り）。
