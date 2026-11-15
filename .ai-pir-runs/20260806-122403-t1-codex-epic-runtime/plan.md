# T1 Codex native epic runtime 実装計画

## 目標

`.codex/skills/epic/SKILL.md` を、Codex の collaboration API と深さ・同時実行制約の下で実行可能なオーケストレーション契約へ置き換える。

## 確認済みの前提

- Codex native overlay は shared core と別個に編集可能。
- 下位ワークフローは `.codex/skills/pir2/SKILL.md` のみを読ませる。`pir2codex` は存在しない。
- 実行時に使える連携 API は `spawn_agent` / `followup_task` / `send_message` / `wait_agent` / `list_agents`。
- 現在の同時実行上限はルートを含む7スロットだが、利用可能数は実行時に判定する。
- subagent がユーザー対話する前提を置かず、親 epic がゲートを一元化する。

## 実装ステップ

1. frontmatter から `--codex` / `pir2codex` を削除し、Codex native の説明に絞る。
2. エージェント起動を Codex collaboration API の実在するツールと role で記述する。
3. DAG wave scheduler、所有範囲、最小 `fork_turns`、深さ超過時の main fallback、修正ループを契約化する。
4. ユーザー判断は「子で保守的デフォルト」で握りつぶさず、親へチェックポイントとして bubble-up し、`followup_task` で再開できる契約にする。
5. `epic-runs.md` は親の単一 writer とし、各 Ti の agent path / RUN_DIR / state / verdict を記録する。
6. 残留語、参照先、frontmatter、agent type を静的検証する。

## 実装形態

`IMPLEMENTATION_ACTOR=main`。編集対象が1ファイルに閉じ、並列 writer の利点がない。探索は explorer subagent と並行実施。

## EXPLORATION_NEEDED

なし。

## USER_DECISION_REQUIRED

なし。ユーザーは Codex への徹底移植と最適化を明示済み。
