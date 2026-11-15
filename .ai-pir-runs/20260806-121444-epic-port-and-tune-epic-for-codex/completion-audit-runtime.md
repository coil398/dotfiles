## Runtime Integrity Audit

### 対象
`.codex/skills/**` / `.codex/agents/**` の参照整合性、実行スクリプトの静的健全性、古い `luna-max-worker` / `pir2codex` / `.cursor` 前提残存の確認。

### 実施した確認

- `rg -n` で以下の残存を横断検索
  - `luna-max-worker`
  - `pir2codex`
  - `.cursor/`
  - `~/.cursor`
  - `.claude/`
  - `Claude` / `Cursor`
  - `SYNC_CODEX_LEGACY_MIRROR`
  - `generated`
  - `AUTO-GENERATED`
- `bash -n` で `etc/*.sh`, `etc/install/**/*.sh`, `bin/*`, `.agents/skills/**/*.sh`, `.codex/skills/**/*.sh` を構文検査
- `python3 -c 'ast.parse(...)'` で `.agents/skills/ai-ltm/scripts/*.py` と `.codex/skills/ai-ltm/scripts/*.py` を静的解析
- `etc/test-codex-contracts.sh`, `etc/test-cursor-contracts.sh`, `etc/test-all-contracts.sh` を読んで、既存契約テストのカバレッジを確認

### 主要な発見

1. `.codex/AGENTS.md` は明示的な生成物ヘッダ付きで、`etc/sync-codex.sh` 由来であることが確認できた。
2. `AGENTS.md` / `AI-WORKFLOW-SPEC.md` / `README.md` / `CLAUDE.md` の間で、Codex / Cursor / Claude の責務分離は概ね一貫していた。
3. `etc/test-codex-contracts.sh` は `luna-max-worker` の削除確認、`worker-delegation` への置換、`codex-runner` の非存在確認、`check-shared-drift.sh` の実行まで含んでいた。
4. `etc/test-cursor-contracts.sh` は `.cursor/mcp.json` の生成条件、`.cursor/rules/shared-agents.mdc` の要約化、`cursor-*` 命名規約、`link.sh` の実体化挙動まで検証していた。
5. `etc/test-all-contracts.sh` は cursor / codex / drift の集約実行を行い、少なくとも契約テストの入口としては整理されていた。
6. Python スクリプト 4 本は AST 解析を通過した。

### 関連ファイル一覧

| ファイルパス | 役割・内容 | 変更の必要性 |
|---|---|---|
| [AGENTS.md](/Users/kawasetakumi/dotfiles/AGENTS.md) | 共有ルール SSOT | 参照のみ |
| [AGENTS.override.md](/Users/kawasetakumi/dotfiles/AGENTS.override.md) | リポジトリ固有の上書き | 参照のみ |
| [AI-WORKFLOW-SPEC.md](/Users/kawasetakumi/dotfiles/AI-WORKFLOW-SPEC.md) | ワークフローの確定仕様 | 参照のみ |
| [README.md](/Users/kawasetakumi/dotfiles/README.md) | 運用説明とリンク一覧 | 参照のみ |
| [CLAUDE.md](/Users/kawasetakumi/dotfiles/CLAUDE.md) | Claude 側の運用 SSOT | 参照のみ |
| [.codex/AGENTS.md](/Users/kawasetakumi/dotfiles/.codex/AGENTS.md) | Codex 生成物 | 参照のみ |
| [.codex/agents/*.toml](/Users/kawasetakumi/dotfiles/.codex/agents) | Codex native overlay 群 | 参照のみ |
| [.codex/skills/**](/Users/kawasetakumi/dotfiles/.codex/skills) | Codex native skill 群 | 参照のみ |
| [etc/sync-codex.sh](/Users/kawasetakumi/dotfiles/etc/sync-codex.sh) | Codex 生成元同期 | 参照のみ |
| [etc/sync-cursor.sh](/Users/kawasetakumi/dotfiles/etc/sync-cursor.sh) | Cursor 生成元同期 | 参照のみ |
| [etc/link.sh](/Users/kawasetakumi/dotfiles/etc/link.sh) | home 側リンク/実体化 | 参照のみ |
| [etc/check-shared-drift.sh](/Users/kawasetakumi/dotfiles/etc/check-shared-drift.sh) | 共有物の drift 検出 | 参照のみ |
| [etc/test-codex-contracts.sh](/Users/kawasetakumi/dotfiles/etc/test-codex-contracts.sh) | Codex 契約テスト | 参照のみ |
| [etc/test-cursor-contracts.sh](/Users/kawasetakumi/dotfiles/etc/test-cursor-contracts.sh) | Cursor 契約テスト | 参照のみ |
| [etc/test-all-contracts.sh](/Users/kawasetakumi/dotfiles/etc/test-all-contracts.sh) | 契約テスト集約 | 参照のみ |
| [.agents/skills/ai-ltm/scripts/*.py](/Users/kawasetakumi/dotfiles/.agents/skills/ai-ltm/scripts) | Python 補助スクリプト | 参照のみ |
| [.codex/skills/ai-ltm/scripts/*.py](/Users/kawasetakumi/dotfiles/.codex/skills/ai-ltm/scripts) | Python 補助スクリプト | 参照のみ |

### 既存パターン・規約

- 生成物はヘッダで明示し、元 SSOT と sync script を書く。
- Codex は `.codex/agents/*.toml` と `.codex/skills/*` を native overlay として扱い、`.agents` との byte-for-byte 一致を要求しない。
- Cursor は `.cursor/skills/cursor-*` 命名を前提にし、`link.sh` で real directory 化する。
- `worker-delegation` は Codex 側の明示的な worker contract で、旧 `luna-max-worker` は契約上も参照上も除去対象。
- `pir2codex` は現行仕様では一部文書・残留 allowlist にのみ現れ、共有 core ではなく移行/互換の文脈に閉じている。

### 影響範囲

- 直接影響
  - `.codex/AGENTS.md` / `.codex/agents/*.toml` / `.codex/skills/*`
  - `etc/sync-codex.sh` / `etc/sync-cursor.sh` / `etc/link.sh`
  - `etc/test-codex-contracts.sh` / `etc/test-cursor-contracts.sh` / `etc/test-all-contracts.sh`
- 間接影響
  - `README.md` / `AGENTS.md` / `AI-WORKFLOW-SPEC.md` / `CLAUDE.md`
  - `.agents/skills/**` の共通 core と、`~/.claude` / `~/.cursor` 側の実体化先

### 依存関係

- インポート関係
  - Bash スクリプト群は `etc/util.sh`, `etc/load.sh`, `etc/link.sh`, `etc/sync-*.sh` を相互参照
  - `ai-ltm` の Python 補助は `vector_search.py` と `merge_conflict.py` に集約
- 被参照関係
  - `worker-delegation` は `.codex/skills/debug|ir|pir2|writing-plan` から参照
  - `check-updates` は `.agents/skills/check-updates` と `.codex/skills/check-updates` の両方から参照
  - `pir2` 系参照は `.agents/skills/pir2/references/*` と `.codex/skills/pir2/references/*` に分布

### 補足情報

- `etc/test-codex-contracts.sh` の契約には、`luna-max-worker` の実体削除、`worker-delegation` への置換、`codex-runner` 非存在が含まれており、旧 worker 前提はかなり潰れている。
- `etc/test-cursor-contracts.sh` は Cursor 側の生成物と実体化挙動を検証しているため、`.cursor` 前提の残骸は主に文書やコメントのレベルで残る可能性がある。
- `rg` では `pir2codex` が `AI-WORKFLOW-SPEC.md` / `CLAUDE.md` / 一部 `.codex` ドキュメントにまだ現れる。これは完全削除ではなく、互換・履歴・allowlist 文脈の残存と見える。
- `python3 -m py_compile` は `__pycache__` 書き込みで失敗したため、代替として `ast.parse` に切り替えた。解析対象の 4 本は通過。
- 参照文字列の全件を機械的に「存在/不存在」判定するには、Markdown 中の相対パスが文脈依存であるため誤検出が多い。今回は実際に読んだ契約テストと主要 SSOT を優先して監査した。

### 参照した外部ソース

なし

### 呼び出し元への依頼

- `pir2codex` を完全に削除したいのか、履歴・互換説明として残すのかは方針確認が必要。
- `.codex/skills/**` と `.agents/skills/**` の参照整合を厳密に機械化するなら、追加で専用の静的チェッカーを implementer に回すとよい。
