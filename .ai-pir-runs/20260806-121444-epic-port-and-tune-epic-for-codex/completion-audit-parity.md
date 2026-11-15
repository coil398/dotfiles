## 完成監査: Claude legacy workflows/assets parity audit for Codex

### 関連ファイル一覧

| ファイルパス | 役割・内容 | 変更の必要性 |
|------------|-----------|------------|
| `.claude/agents/codex-runner.md` | codex CLI を最後まで走らせる専任エージェント。`/codex` と `pir2codex` の実行基盤 | 変更あり |
| `.claude/skills/pir2codex/SKILL.md` | Plan→Review→Retrospect は Claude、Implement だけ Codex に差し替える実験版ワークフロー | 変更あり |
| `.claude/skills/pir2/references/deterministic-completion-check.md` | 実装完了報告と git 差分を集合照合する決定論的ゲート | 変更あり |
| `.claude/skills/pir2/references/verify-deterministic-check.sh` | 上記ゲートの bash 自動検証スクリプト | 変更あり |
| `.claude/skills/pir2/references/run-dir-base.md` | RUN_DIR の基底パス SSOT。`PROJECT_ROOT/.ai-pir-runs` への移行方針を明記 | 参照のみ |
| `.claude/skills/walkthrough/references/html-mode.md` | `/walkthrough --html` の HTML 版仕様 SSOT | 任意 |
| `.claude/skills/walkthrough/references/html-template.html` | `/walkthrough --html` の生成テンプレート | 任意 |
| `.codex/skills/codex/SKILL.md` | Codex 相談スキル。`codex-runner` 前提の利用手順を定義 | 参照のみ |
| `.codex/skills/pir2/SKILL.md` | Codex 実装版 PIR²。`codex-runner` と決定論的完了検証を組み込む | 参照のみ |
| `.codex/skills/worker-delegation/SKILL.md` | Sol/Luna/Terra の作業委譲契約。Codex 側の実作業委譲基盤 | 変更あり |
| `.codex/skills/pir2/references/final-summary-template.md` | Codex 側の最終サマリー整形テンプレート | 参照のみ |
| `.codex/skills/pir2/references/worker-observability.md` | Codex 実行の観測性補強。Claude 側には未移植 | 任意 |
| `.claude/agent-delegation.md` / `.codex/agent-delegation.md` | 探索委譲の共通ガイド。Codex 版は生成物として同期済み | 参照のみ |
| `.claude/agents/*` / `.codex/agents/*` | Claude の markdown エージェント定義と Codex の toml オーバーレイ | 参照のみ |

### 既存パターン・規約

- 命名規約: Claude 側は `*.md` のエージェント/スキル/参考資料、Codex 側は `*.toml` の native overlay と `SKILL.md` の組み合わせが基本。
- ディレクトリ構造: `*.skills/*/references/` に重い手順・検証・テンプレートを分離し、`SKILL.md` は入口とオーケストレーションに集中する。
- コードスタイル: Codex 側は生成アダプタと native overlay を分離し、生成物は手編集しない前提。Claude 側は運用上の詳細を厚めに持つ。
- 共通ユーティリティ: `pir2` 配下の references は手順 SSOT として再利用され、`codex`/`pir2codex` でも同じ抽象を流用する設計。
- **構造投資領域 (structurally-invested area)**:
  - `codex` / `pir2` / `pir2codex` / `worker-delegation` / `walkthrough` は、実行プロトコル・検証・成果物生成が複数ファイルに分散した重い領域。
  - `pir2` は references 群が特に厚く、`deterministic-completion-check`、`exploration-loop`、`plan-choice-gate`、`feedback-conflict-gate`、`tester-prompt` など、N+1 追加を前提にした構造になっている。
  - `walkthrough` も `html-mode` / `html-template` を持つため、HTML 版を増やすなら同系列として追加するのが自然。

### 影響範囲

- 直接影響: `.claude/agents/codex-runner.md`、`.claude/skills/pir2codex/SKILL.md`、`.claude/skills/pir2/references/deterministic-completion-check.md`、`.claude/skills/pir2/references/verify-deterministic-check.sh`
- 間接影響: `.codex/skills/pir2/SKILL.md` の実装フロー、`worker-delegation` の actor ladder、`walkthrough` の HTML 出力導線、`etc/sync-codex.sh`

### 依存関係

- インポート関係: `pir2codex` は `pir2` references を前提にしつつ、実装主体を `codex-runner` に委譲する。
- 被参照関係: `codex-runner` は `/codex` と `pir2codex` の両方から基盤として参照される想定だが、Codex 側には同等の native 実装がない。

### 補足情報

- Claude 側でしか確認できなかった実用資産は、主に「codex CLI を最後まで完走させる runner」「Codex 実装版 PIR²」「決定論的完了検証の bash 監査」「walkthrough の HTML 版テンプレート」の 4 系統。
- `.codex/skills/pir2/SKILL.md` は `final-summary-template.md` と `worker-observability.md` を追加しており、Claude 側より実行時観測と報告整形が強い。逆に Claude 側の `pir2codex` は Codex 実装のための専用 orchestrator として残っている。
- `run-dir-base.md` は Claude 側に単独ファイルとして残るが、Codex 側の `pir2` では内容が `SKILL.md` に吸収されているため、機能は部分移植済みとみなせる。
- `walkthrough/references/html-mode.md` と `html-template.html` は Codex 側に未移植だが、これは Codex の主要ワークフローに必須ではなく、UI/閲覧性の拡張に近い。
- 比較は `.claude/agents` / `.claude/skills` / `.agents/skills` と `.codex/agents` / `.codex/skills` の実ファイルを列挙して差分確認した。`design-review` はユーザー指定どおり編集対象から外し、監査対象にも含めていない。

### 参照した外部ソース

なし

### 呼び出し元への依頼

- must-port now: `.claude/agents/codex-runner.md` 相当の Codex-native agent か同等の実行基盤を用意しないと、`pir2codex` の「Codex 実装を最後まで回す」部分が Claude 専有のまま残る。
- must-port now: `.claude/skills/pir2codex/SKILL.md` の Codex 版を `.codex/skills/` に持ち込むか、Codex 側の `pir2` に統合する方針を決めるべき。
- must-port now: `deterministic-completion-check.md` と `verify-deterministic-check.sh` の検証ロジックを Codex 側にも持たせるべき。現状は Claude 側の SSOT に依存している。
- optional: `walkthrough --html` の HTML テンプレートは Codex へ移植する優先度は低いが、閲覧性改善を狙うなら追加候補。
- intentional Claude-only: `pir2codex` の実験用運用や `codex-runner` の Claude サブエージェント実装は、Codex-native に完全同型で持つよりも、Claude 側のオーケストレーションとして残す判断もあり得る。
