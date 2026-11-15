# 探索レポート 01

## 確認済み事実

- `.codex/skills/epic/SKILL.md` は Codex native overlay だが、存在しない `pir2codex`、`Agent` / `Read` / `Write` といった別 runtime の操作名、`~/.agents` 参照が残る。
- `.codex/config.base.toml` の現行 `max_depth = 1` は、旧 epic の L0→L1→L2 必須契約と衝突する。
- Codex で利用できる連携 API は `spawn_agent` / `followup_task` / `send_message` / `wait_agent` / `list_agents`。`spawn_agent` は `agent_type`、`fork_turns`、安定した `task_name` を受け取る。
- 現在のツール説明上の同時実行上限はルートを含む7スロット。他タスクと共有なので、空きは実行時判定が必要。
- `.codex/skills/pir2/SKILL.md` は subagent 不可時の `IMPLEMENTATION_ACTOR=main` を契約化済み。
- `.codex/agents/epic-planner.toml` に `epic-planner` role が実在する。下位 PIR² ランナー専用 role はないため `default` を使うのが実行可能な契約。
- Codex overlay は default sync で shared core から再生成されず、個別に保守する上位仕様と整合する。

## 推論と設計結論

- 深さ設定を前提にせず、子ランナーが subagent 起動できなければ同じランナー内で PIR² フェーズを完遂するべき。
- 並列子が共通の `epic-runs.md` を書くと競合するため、マッピングは親 epic の単一 writer とするべき。
- 子の本質的なユーザー判断は `WAITING_USER` として親に戻し、親が対話後 `followup_task` で同じ子を再開するのが、状態とコンテキストを保つ最小コストの経路。

## EXPLORATION_NEEDED

なし。
