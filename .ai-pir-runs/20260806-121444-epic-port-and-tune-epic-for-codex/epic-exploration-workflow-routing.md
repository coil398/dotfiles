## 探索レポート: Codex native workflow の routing と actor 境界

### 関連ファイル一覧

| ファイルパス | 役割・内容 | 変更の必要性 |
|------------|-----------|------------|
| [/Users/kawasetakumi/dotfiles/.codex/skills/luna-max-worker/SKILL.md](/Users/kawasetakumi/dotfiles/.codex/skills/luna-max-worker/SKILL.md) | Sol→Luna Max の委譲契約、完了要件、要件適合の最終判定ルール | 参照のみ |
| [/Users/kawasetakumi/dotfiles/.codex/skills/pir2/SKILL.md](/Users/kawasetakumi/dotfiles/.codex/skills/pir2/SKILL.md) | Plan→Implement→Review→Test→Retrospect の主ワークフロー。探索・計画・実装・レビュー・テストの分業と再探索ループ | 参照のみ |
| [/Users/kawasetakumi/dotfiles/.codex/skills/ir/SKILL.md](/Users/kawasetakumi/dotfiles/.codex/skills/ir/SKILL.md) | 小タスク向けの Implement→Review 軽量フロー。implementer と reviewer の境界が明示される | 参照のみ |
| [/Users/kawasetakumi/dotfiles/.codex/skills/debug/SKILL.md](/Users/kawasetakumi/dotfiles/.codex/skills/debug/SKILL.md) | 探索→診断→計画→実装→レビューのバグ修正フロー。探索不足時の再探索と、症状起点の診断要件を持つ | 参照のみ |
| [/Users/kawasetakumi/dotfiles/.codex/skills/epic/SKILL.md](/Users/kawasetakumi/dotfiles/.codex/skills/epic/SKILL.md) | 大規模タスク分割と wave 実行の上位オーケストレーション。PIR² を子タスクへ波及させる | 参照のみ |
| [/Users/kawasetakumi/dotfiles/.codex/skills/writing-plan/SKILL.md](/Users/kawasetakumi/dotfiles/.codex/skills/writing-plan/SKILL.md) | 実装計画作成と記録のワークフロー。planning と review/test の接続点を持つ | 参照のみ |
| [/Users/kawasetakumi/dotfiles/.codex/skills/brainstorm/SKILL.md](/Users/kawasetakumi/dotfiles/.codex/skills/brainstorm/SKILL.md) | 要件曖昧時の設計対話・論点整理の前段 | 参照のみ |
| [/Users/kawasetakumi/dotfiles/.codex/skills/reviewer/SKILL.md](/Users/kawasetakumi/dotfiles/.codex/skills/reviewer/SKILL.md) | 差分レビューの多観点並列起動。correctness / consistency / quality / security / architecture を扱う | 参照のみ |
| [/Users/kawasetakumi/dotfiles/.codex/skills/tester/SKILL.md](/Users/kawasetakumi/dotfiles/.codex/skills/tester/SKILL.md) | 動作検証専任。既存テストとアドホック確認を実行 | 参照のみ |
| [/Users/kawasetakumi/dotfiles/.codex/skills/codex/SKILL.md](/Users/kawasetakumi/dotfiles/.codex/skills/codex/SKILL.md) | Codex CLI への相談ルート。codex-runner に長時間実行を隔離する | 参照のみ |
| [/Users/kawasetakumi/dotfiles/.codex/skills/pir2async/SKILL.md](/Users/kawasetakumi/dotfiles/.codex/skills/pir2async/SKILL.md) | PIR² の team 化・並列化実験ルート。通常 pir2 の境界確認用 | 参照のみ |
| [/Users/kawasetakumi/dotfiles/.codex/agents/implementer.toml](/Users/kawasetakumi/dotfiles/.codex/agents/implementer.toml) | 実作業 actor の Codex native 定義。model / effort / 入力契約 | 参照のみ |
| [/Users/kawasetakumi/dotfiles/.codex/agents/reviewer.toml](/Users/kawasetakumi/dotfiles/.codex/agents/reviewer.toml) | レビュー actor の Codex native 定義。品質観点の役割が明示 | 参照のみ |
| [/Users/kawasetakumi/dotfiles/.codex/agents/tester.toml](/Users/kawasetakumi/dotfiles/.codex/agents/tester.toml) | テスト actor の Codex native 定義。実行順序と判定が明示 | 参照のみ |
| [/Users/kawasetakumi/dotfiles/.codex/agents/planner.toml](/Users/kawasetakumi/dotfiles/.codex/agents/planner.toml) | 計画 actor の Codex native 定義。 | 参照のみ |
| [/Users/kawasetakumi/dotfiles/.codex/agents/epic-planner.toml](/Users/kawasetakumi/dotfiles/.codex/agents/epic-planner.toml) | epic 分割専任の planning actor | 参照のみ |
| [/Users/kawasetakumi/dotfiles/.codex/agents/gate.toml](/Users/kawasetakumi/dotfiles/.codex/agents/gate.toml) | deepthink の十分性判定 actor | 参照のみ |
| [/Users/kawasetakumi/dotfiles/.codex/agents/synthesizer.toml](/Users/kawasetakumi/dotfiles/.codex/agents/synthesizer.toml) | deepthink の統合 actor | 参照のみ |
| [/Users/kawasetakumi/dotfiles/.codex/agents/tech-validator.toml](/Users/kawasetakumi/dotfiles/.codex/agents/tech-validator.toml) | 技術選定時の外部一次ソース確認 actor | 参照のみ |
| [/Users/kawasetakumi/dotfiles/.codex/config.base.toml](/Users/kawasetakumi/dotfiles/.codex/config.base.toml) | Codex の既定 model / sandbox / agents 制約の土台 | 参照のみ |
| [/Users/kawasetakumi/dotfiles/etc/sync-codex.sh](/Users/kawasetakumi/dotfiles/etc/sync-codex.sh) | Codex 生成物の同期ルールと、.codex/agents / .codex/skills の扱い | 参照のみ |
| [/Users/kawasetakumi/dotfiles/etc/seed-codex-overlay.sh](/Users/kawasetakumi/dotfiles/etc/seed-codex-overlay.sh) | missing-only seed で Codex native overlay を作る補助 | 参照のみ |
| [/Users/kawasetakumi/dotfiles/etc/test-codex-contracts.sh](/Users/kawasetakumi/dotfiles/etc/test-codex-contracts.sh) | overlay 存在と non-destructive seed を検査する契約テスト | 参照のみ |
| [/Users/kawasetakumi/dotfiles/AGENTS.md](/Users/kawasetakumi/dotfiles/AGENTS.md) | shared core / native overlay 方針、レビュー規約、コマンド提示規約 | 参照のみ |
| [/Users/kawasetakumi/dotfiles/AI-WORKFLOW-SPEC.md](/Users/kawasetakumi/dotfiles/AI-WORKFLOW-SPEC.md) | shared core + native overlays の全体アーキテクチャ SSOT | 参照のみ |

### 既存パターン・規約

- 命名規約: 実作業 actor は `implementer` / `reviewer` / `tester` / `planner` のように役割名をそのまま使い、solver 側は `Sol` としてオーケストレーター責務を持つ。Luna 系は `luna-max-worker` として「実行担当」を明示する。
- ディレクトリ構造: 共有 core は `AGENTS.md` と `.agents/skills/**`、Codex 固有の運用は `.codex/agents/**` と `.codex/skills/**` に分離される。生成物は `etc/sync-codex.sh`、seed は `etc/seed-codex-overlay.sh`、契約テストは `etc/test-codex-contracts.sh` が担う。
- コードスタイル: 役割境界は「誰が判断するか」「誰が実作業するか」「誰が検証するか」を分けて記述する。`reviewer` と `tester` は実装の自己申告を信用せず、実体差分や実行結果で判定する。
- 共通ユーティリティ: `RUN_DIR` / `PROJECT_MEMORY_DIR` / sanitized-cwd の解決、`plan.md` / `exploration-*.md` / `implementation-*.md` / `review-*.md` / `test-*.md` の記録ファイル群、`sync-codex.sh` の生成契約が共通基盤。
- **構造投資領域 (structurally-invested area)**: `pir2` / `ir` / `debug` / `writing-plan` / `epic` / `reviewer` / `tester` は、Plan→Implement→Review→Test かその部分集合を持つため、同一の共通 routing と記録契約を押し込む価値が高い。特に `pir2` と `debug` は exploration→planning→implementation→review/test のファイル流儀がほぼ同型。

### 影響範囲

- 直接影響: `pir2` のステップ構成、`debug` の探索→計画→実装→レビュー流れ、`ir` の簡易実装ループ、`epic` の wave への下位分割、`writing-plan` の plan 記録、`reviewer` / `tester` の境界、`luna-max-worker` の委譲契約。
- 間接影響: `AGENTS.md` の shared core 規約、`AI-WORKFLOW-SPEC.md` の overlay 方針、`.codex/config.base.toml` の既定 model、`sync-codex.sh` / `seed-codex-overlay.sh` / `test-codex-contracts.sh` の生成・契約チェック。

### 依存関係

- インポート関係: `pir2` / `debug` / `reviewer` / `ir` / `writing-plan` は `explorer`、`planner`、`implementer`、`reviewer`、`tester`、`retrospector`、`tech-validator` などの agent 名と `RUN_DIR` / `PROJECT_MEMORY_DIR` を共有前提にしている。`epic` はさらに `epic-planner` と `luna-max-worker` を下位に持つ。
- 被参照関係: `luna-max-worker` は `reviewer` を別途使う前提で品質を分離している。`pir2` は `brainstorm` / `explorer` / `planner` / `implementer` / `reviewer` / `tester` / `retrospector` を連続接続する。`debug` は探索結果をそのまま実装せず、必ず診断→計画を挟む。`epic` は子 PIR² に all-in しつつ、親 epic が統合確認を持つ。

### 補足情報

- 実作業 actor を持つものは明確に分離されている。`luna-max-worker` は「Luna Max が実作業」、`pir2` / `ir` / `debug` は「implementer が実装」、`reviewer` は「レビュー専任」、`tester` は「検証専任」、`epic` は「Ti 単位で PIR² を wave 実行」という構図。
- 共通 routing の最小統合点は、`Sol` が判断・設計・最終判定を持ち、`Luna Max` を既定の具体作業 actor とし、能力不足や要件未達時にのみ `Terra` へ昇格し、最終的には `Sol` が要件充足を実測する、という 3 層 ladder である。`luna-max-worker` はこの ladder のうち「Sol→Luna」の委譲規約を単独で明文化している。`epic` の本文には `Terra` が明記されているが、`luna-max-worker` 自体には Terra 昇格ロジックは無いので、ここは上位 orchestration に押し上げるべき。
- コピペ回避の接続点は、`RUN_DIR` / `PROJECT_MEMORY_DIR` / sanitized-cwd / `plan.md` / `exploration-*.md` / `implementation-*.md` / `review-*.md` / `test-*.md` の共通ファイル名群と、`reviewer` / `tester` の Fan-Out Gate だが、これは実装の重複というより「起動契約」の重複。共通化するなら shared helper ではなく SSOT 参照化が適切。
- shared core に押し込むべきでないもの: `gpt-5.6-luna` / `gpt-5.6-terra` / `gpt-5.5` / `gpt-5.4-mini` のようなモデル固定、`workspace-write` / `read-only` のような runtime 固有の sandbox、`reviewer` の Fan-Out Gate のような UI/agent 実行都合の手順。これらは runtime 別の native overlay に残すべき。
- 共有リソース競合: `.codex/agents/*.toml` と `.codex/skills/*` は Codex native overlay だが、`AGENTS.md` と `.agents/skills/**` は shared core なので、ここに runtime 固有の model pin や実装 actor 詳細を戻さない。`etc/sync-codex.sh` のデフォルトは `.codex/agents/*.toml` / `.codex/skills/**` を再生成しないため、overlay は non-destructive seed 前提で扱う必要がある。
- 棚卸し観点のチェック結果: actor を持つ実作業 skill は `luna-max-worker`, `pir2`, `ir`, `debug`, `epic`, `writing-plan`, `reviewer`, `tester`, `codex`。actor を持たない、または主に判断・前段整理に寄るものは `brainstorm`, `planner`, `epic-planner`, `gate`, `synthesizer`, `thinker`, `deliberator`, `refactor-advisor`, `tech-validator`。

### 参照した外部ソース（外部ドキュメント調査を行った場合のみ）

| ソース種別 | URL | 確認した内容 |
|-----------|-----|------------|
| なし | - | 今回はローカル SSOT のみを調査し、外部一次ソースは参照していない |

### 呼び出し元への依頼（該当する場合のみ）

- `Sol → Luna Max → Terra → Sol` の routing は、`luna-max-worker` 単体ではなく、`pir2` / `debug` / `epic` の上位 orchestration にもまたがるため、共通実行層としては「最小共通の actor ladder SSOT」を別ファイルに切り出す設計を検討してほしい。
- `reviewer` / `tester` / `implementer` の境界は十分明確だが、`pir2`・`debug`・`ir` での記録ファイル命名と resume / handoff 周りは重複が大きいので、共通化候補として planner へ渡してほしい。
