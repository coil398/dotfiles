VERDICT: PASS

### 担当 role
quality

### 前提条件について（前回レビューとの差異）

同一パスに存在する前回の `review-01-quality.md`（16:15 時点）は、実装が未着手の状態（`.claude/skills/epic/SKILL.md` / `.claude/agents/epic-planner.md` が存在せず、`CLAUDE.md` / `experimental.md` の追記も未反映）に対して VERDICT: FAIL を返していた。今回のレビュー時点では `implementation-01.md`（16:49 生成）が存在し、`git status --porcelain` で以下が確認できた:

```
M .claude/skills/pir2/references/experimental.md
M .gitignore
M CLAUDE.md
?? .claude/agents/epic-planner.md
?? .claude/skills/epic/
```

4 ファイルの実体が揃っていることを自分の `Read` / `git diff` で確認したうえで、実体テキストに対する quality レビューを行った（前回レポートの内容は本レポートには引き継がず、独立に判定した）。

### 判断根拠

- **保守性（局所スコープ）**: `.claude/skills/epic/SKILL.md`（143行）と `.claude/agents/epic-planner.md`（145行）はいずれも単一ファイルで完結し、循環的複雑度が高い箇所やマジックナンバーはない。Step 1 の bash スニペット（`--codex` パース・`EPIC_RUN_DIR` 確定）はケース文が明快で、コメントも適切。ただし以下の2点を軽微な問題として検出した（詳細は「問題一覧」参照）:
  - pir2 の具体的なステップ番号（`ステップ 1` `ステップ 4.5` `ステップ 6.5` `ステップ 7-2A` `ステップ 12` `ステップ 3`）への直接参照が SKILL.md 内に6箇所ある。ただし `grep -n "ステップ [0-9]" .claude/skills/pir2/references/*.md` で確認した通り、pir2 の既存 `references/*.md`（`plan-choice-gate.md` の「PIR² 系スキル（/pir2）のステップ 4.6。」、`next-steps-queue.md` の「ステップ 5.6」等）も同じ慣習で pir2 SKILL.md のステップ番号をハードコードしており、これは epic が単独で持ち込んだアンチパターンではなく **既に定着した pir2 エコシステムの慣習**である。とはいえ、epic はこの依存表面を新たに1ファイル分増やす形になるため、pir2 側のステップ再採番時に追従漏れが起きるリスクは残る。既存慣習を踏襲した実装として妥当だが、将来のリスクとして Medium で記録する。
  - Step 3-0（launch 手順の説明）と末尾「Agent ネスト起動方式の技術整合性」節が、`subagent_type=general-purpose` + `Read` ベース起動 + `model=opus` 必須という同じ技術的事実をほぼ同内容で二重に記述している（後者は「理由はステップ 3-0 参照」と一部のみ差分参照している）。plan.md 側で「本文冒頭の前提サマリー」と「独立した技術整合性小節」の両方を明示的に要求している（会話の必須要求）ため意図的な設計であり、実装はその指示に忠実。実行者（メイン Claude）が通読する上で軽微な冗長税にはなるが、致命的ではないため Low とする。
- **テストの質**: 本タスクはドキュメント著述であり、plan.md・実装レポートともに「テストスイートなし・静的検証のみ」と明記されている。`implementation-01.md` の自己検証項目（frontmatter の `---` 対チェック、CORE タグの対チェック、3前提の grep 確認、`model=opus` 明記の grep 確認、PostToolUse hook 発火による OpenCode 側生成物の存在確認、`git diff` による既存本文無改変の確認、グローバル固有名混入なしの grep 確認）は、コード実装のテストに相当する静的検証としては十分に具体的で、実データ（grep/stat/git diff の実行結果）に基づいている。「配列を返すAPIのテストで1件のみ」のような対象外の観点はそもそも該当しない。
- **データアクセスの重複**: 該当なし（データアクセス層の変更を含まないドキュメント著述タスクのため対象外）。
- **スコープ逸脱・不要な追加実装**: `git status --porcelain` で変更ファイルを機械的に列挙し、plan.md の「修正対象ファイル一覧」（新規: `.claude/skills/epic/SKILL.md`, `.claude/agents/epic-planner.md`／追記: `CLAUDE.md`, `.claude/skills/pir2/references/experimental.md`）と1件ずつ照合した。`M .gitignore`（`/.ai-pir-runs/` 追加1行）のみ plan.md の4ファイルリストに含まれない差分だったため、原因を追跡した。RUN_DIR 名 `20260703-152304-epic-orchestrator-skill` は epic 自身の `EPIC_RUN_DIR` 命名パターン（`${run_ts}-epic-${run_feature}` で `-epic-` を二重に含む形）ではなく、pir2 自身の `run-dir-base.md` の標準 RUN_DIR パターンと一致する。つまり本タスク自体が `/pir2`（この epic スキルを作るための pir2 ワークフロー自体）として実行されており、その pir2 自身のステップ1（RUN_DIR 確定）が実行時に `.gitignore` へ `/.ai-pir-runs/` を追記した副産物であると判断できる。implementer 自身も `implementation-01.md` で同じ推論に基づき「本 implementer が Bash で実行したものではない」と明記しており、整合する。よって `.gitignore` の差分は本 implementer のスコープ逸脱ではない。それ以外の4ファイルはいずれも plan.md 記載の変更内容と一致しており、余分な追加実装（プラン外のフォールバック処理・代替マッピング・防御的バリデーション等）は確認できなかった。
- **グローバル汎用性（最重要・quality 観点として追加確認）**: `.claude/skills/epic/SKILL.md` / `.claude/agents/epic-planner.md` に対し `grep -n "Unity\|Figma\|GORM\|util/\|Godot\|Blender"` を実行し、ヒットなし（exit code 1）を確認した。`CLAUDE.md` 追記分・`experimental.md` 追記分についても同様に確認し、ヒットしたのは今回の diff に含まれない既存の `/unity-mcp-skill` 表行（無関係の既存エントリ）のみだった。会話中の Unity/Figma の例示は成果物に一切混入していない。プロジェクト固有のクラス名・テーブル名・API 名の混入も確認できなかった。
- **DRY / references 再利用**: `find .claude/skills/epic -type f` の結果は `SKILL.md` 1ファイルのみで、`references/` サブディレクトリは作成されていない（plan.md「変更不要」節の指示通り）。epic/SKILL.md 内で参照されている pir2 側ファイル（`sanitized-cwd.md` / `run-dir-base.md` / `plan-choice-gate.md` / `fan-out-gate.md` / `retrospector-prompt.md` / `continuation-gate.md`）は `ls .claude/skills/pir2/references/` で全て実在を確認した。重複した説明文を epic 側に書き起こさず、パス参照で済ませている箇所がほとんどであり、`feedback_no_redundant_skills` の「既存スキルでカバーできる用途を別スキルに切り出さない」方針にも適合している（plan.md が確認した非重複 capability 判定にも矛盾しない）。
- **書式ルール**: `.claude/skills/epic/SKILL.md` は `#`（1個のみ、タイトル）→ `##`（ステップ見出し）→ `###`（サブステップ 3-0〜3-5）の階層を正しく踏襲しており、pir2 本体 SKILL.md と同じ見出し慣習。bash コードブロックは ` ```bash ` で言語タグ付き。`> ⚠️` の引用バッジ（`model=opus` は必須です）も format.md のバッジ規約（注意・制約）に合致した使い方。`---` 区切り線の使用頻度（11箇所 / 13見出し程度）も pir2 本体（27箇所 / 約35見出し）と比例的に整合している。`.claude/agents/epic-planner.md` は既存 `planner.md` と同じ構造（`#` タイトルなし → frontmatter → CORE ブロック → `## 役割` `## 入力` `## プロセス` ... の直接開始）で、既存エージェント定義ファイル群の慣習と一致している。

### 問題一覧

- Medium `.claude/skills/epic/SKILL.md`（複数箇所: L24, L65, L71, L85/91, L99, L117, L123） — pir2 の具体的なステップ番号（1 / 4.5 / 6.5 / 7-2A / 3 / 12）への直接参照が6箇所ある。pir2 SKILL.md 側で将来ステップの挿入・削除・番号変更が起きた場合、epic 側の参照が静かに陳腐化する（既存 `references/*.md` も同じ慣習を採用しているため epic 固有の新規アンチパターンではないが、依存表面が1ファイル増える）。→ 対応は必須ではないが、将来 pir2 のステップ番号をリファクタする際に「epic/SKILL.md も参照更新対象に含める」ことを `experimental.md` の該当実験の Quality Guardrails または Metrics 欄に一言追記しておくと、次回 pir2 リファクタ時の見落としを防げる（軽微な予防策であり、実装のやり直しは不要）。
- Low `.claude/skills/epic/SKILL.md`（ステップ 3-0 と「Agent ネスト起動方式の技術整合性」節） — `subagent_type=general-purpose` + Read ベース起動 + `model=opus` 必須という同一の技術的事実がほぼ同内容で2箇所に記述されている。plan.md が明示的に要求した設計（会話の必須要求）であるため妥当だが、将来epic を拡張する際にこの2箇所を同時に更新し忘れるリスクがわずかにある。対応は任意（現状で実害はない）。

### 担当外で気づいた点（参考）

- なし（consistency / correctness / security / architecture の各観点はそれぞれ別 reviewer が担当しており、quality の守備範囲外の指摘は今回発見しなかった）。

### 良好点

- グローバル汎用性ルールを厳格に遵守しており、会話中の具体例（Unity/Figma）が成果物に一切混入していない点は明確な良好点。
- `epic-planner.md` の CORE セクションで「実装詳細を抱えるとコンテキストが肥大し『context 大きすぎで漏れる』があなたに再現するため」と、責務境界を設定した理由まで明記しており、将来の維持者が「なぜ分割レベルに留めているか」を理解しやすい。
- `.claude/skills/epic/references/` を新設せず既存 pir2 references を再利用した判断は、`feedback_no_redundant_skills`（既存スキルでカバーできる用途を別スキルに切り出さない）の精神を単一スキル新設の枠内でも徹底しており、DRY の観点で模範的。
- `implementation-01.md` の自己検証が推測ではなく実データ（grep/stat/git diff の実行結果）に基づいて記述されている点は、`~/.claude/CLAUDE.md`「ツール結果の捏造の絶対禁止」の精神にも合致し、quality の「テストの質」相当の観点からも評価できる。

### 次のアクション

PASS のため対応必須事項なし。任意対応として、`.claude/skills/pir2/references/experimental.md` の `epic-orchestrator-nested-pir2` 実験セクションの Quality Guardrails 欄に「pir2 SKILL.md のステップ再採番時は `.claude/skills/epic/SKILL.md` の参照箇所（ステップ 1/4.5/6.5/7-2A/3/12）も同時更新対象に含める」旨を一言追記することを推奨する（Medium 指摘の予防策、必須ではない）。
