VERDICT: FAIL

### 担当 role
consistency

### 判断根拠
- 命名規則・構造の一貫性: `luna-max-worker` から `worker-delegation` へのパッケージ名変更は、`.codex/skills/worker-delegation/SKILL.md:2`、`agents/openai.yaml:2`、`scripts/run-worker.sh:6`、`AI-WORKFLOW-SPEC.md:30` で一致している。旧 `luna-max-worker` / `run-luna-max` 参照は、削除対象と `etc/test-codex-contracts.sh` 自身を除く `rg` で検出されなかった。`debug` / `ir` / `pir2` / `writing-plan` / `epic` は `worker-delegation` と `run-worker.sh --actor luna` への接続に揃っている。一方、Codex-native overlay の共通 reference 参照先が一部だけ `.codex/skills/...` に更新され、`pir2async` と sanitized-cwd SSOT / 検証スクリプトが旧 shared / Claude パスを指したまま残っているため、一貫性に High 問題がある。
- 同一ロジックの全適用箇所の網羅性: `sanitized-cwd` 参照コメントは `pir2` / `debug` / `ir` / `writing-plan` で `.codex/skills/pir2/references/sanitized-cwd.md` 系へ更新されているが、同じ 9 ファイル横展開対象のうち `pir2async` / `reviewer` / `review-pr` / `refactor-advisor` / `retro` は旧 `~/.agents/skills/...` のまま残っている。さらに SSOT 本体 `.codex/skills/pir2/references/sanitized-cwd.md` は参照側一覧と実行例を `~/.agents/skills/...` のまま保持し、併設検証スクリプトは `.claude/skills/...` を検査している。Codex overlay 内の SSOT と検査対象が、今回の `.codex` 移行差分と同期していない。
- 類似ファイル群への波及網羅性: 明示対象の concrete workflow (`debug` / `ir` / `pir2` / `writing-plan`) と `epic` / `brainstorm` / `pir2async` の worker 境界追加は概ね波及している。`brainstorm` は設計専用、`pir2async` は実験隔離として `AI-WORKFLOW-SPEC.md:98-102` と整合しており、`scripts/run-worker.sh` へ接続しないことも `etc/test-codex-contracts.sh:113-118` で検査されている。ただし、同じ Codex overlay の共通参照パス更新が `pir2async` と sanitized-cwd 系で未波及のため、この観点でも High 問題に該当する。

### 問題一覧
- High `.codex/skills/pir2async/SKILL.md:29` — Codex-native workflow 移行で `pir2` / `debug` / `ir` / `writing-plan` は共通 reference を `.codex/skills/pir2/references/...` へ寄せているが、`pir2async` は `~/.agents/skills/pir2/references/...` を 9 箇所（29, 126, 153, 247, 291, 316, 344, 368, 378 行）残している。`pir2async` は worker ladder へ接続しない実験隔離であっても、Codex overlay として読む共通 reference の置き場所は他 workflow と同じ Codex-native パスに揃えるべき。→ `pir2async` 内の共通 reference 参照を `${PROJECT_ROOT}/.codex/skills/pir2/references/<file>.md` に更新する。
- High `.codex/skills/pir2/references/sanitized-cwd.md:49` — 同ファイルは `.codex/skills/pir2/references/sanitized-cwd.md` 自身が SSOT であるにもかかわらず、参照側一覧を `~/.agents/skills/...` のまま列挙し、検証スクリプト実行例も `~/.agents/skills/pir2/references/verify-sanitized-cwd.sh` のまま残している。併設の `.codex/skills/pir2/references/verify-sanitized-cwd.sh:5` も SSOT を `~/.claude/...` とし、検査対象を `${HOME}/.claude/skills/...` に固定しているため、今回更新した Codex overlay 9 ファイルの揺れを検出できない。→ `sanitized-cwd.md` の参照側一覧と実行例を `.codex/skills/...` に更新し、`verify-sanitized-cwd.sh` も dotfiles / `.codex/skills/...` を検査対象にする。必要なら `reviewer` / `review-pr` / `refactor-advisor` / `retro` の同コメントも合わせて更新する。

### 良好点
- `worker-delegation` パッケージ名、runner 名、actor 名 `luna|terra`、model routing の保持場所は `AI-WORKFLOW-SPEC.md`、skill、runner、contract test で概ね揃っている。
- `brainstorm` は設計専用、`pir2async` は実験隔離という責務境界が明文化され、通常 concrete workflow だけが `run-worker.sh` に接続する構造になっている。

### 次のアクション
1. `pir2async` の共通 reference 参照を Codex-native パスへ統一する。
2. `sanitized-cwd.md` と `verify-sanitized-cwd.sh` を Codex overlay の SSOT / 検証対象に合わせる。
3. `rg -n "~/.agents/skills/pir2/references|~/.claude/skills/pir2/references" .codex/skills/pir2 .codex/skills/pir2async .codex/skills/debug .codex/skills/ir .codex/skills/writing-plan .codex/skills/reviewer .codex/skills/review-pr .codex/skills/refactor-advisor .codex/skills/retro` で旧参照の残存を再確認する。
