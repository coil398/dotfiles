# Fable 5.1 model contract（deepthink / deepplan）

## ピンする ID

| ランタイム | 指定 |
|---|---|
| Claude Code `Agent` / agent frontmatter | `claude-fable-5-1` + `effort: medium`（既定） |
| Cursor `Task` / agent frontmatter | `claude-fable-5-1[effort=medium]` |
| OpenCode（sync 生成） | `anthropic/claude-fable-5-1` |

短名 `fable` / `fable5` は **最新へ自動追随しない**（`claude-fable-5` のまま残る経路がある）。必ず `claude-fable-5-1` をピンする。

## effort — Fable 5.1 は慎重に選ぶ

**Fable 5.1 では `high` を既定にしない。** トークン消費が増える一方で、実務では品質が上がらない・むしろ落ちることがある。`low` / `medium` で十分なことが多い。

| 値 | deepthink / deepplan / Fable エージェント | いつ選ぶか |
|---|---|---|
| `medium`（既定） | **これ** | 通常の熟考・統合・ゲート・深いプラン |
| `low` | 明示時 | 軽い問い・レイテンシ/コスト優先。`--effort=low` |
| `high` | **既定にしない** | `medium` で不足したことが実測できたときだけ。`--effort=high` |
| `xhigh` / `max` | 明示時のみ | さらに足りないときだけ。`--effort=max`。コスト・レイテンシ最大 |

Cursor では Task 起動時に `claude-fable-5-1[effort=medium]` を渡す（agent frontmatter は `inherit` のまま。SSOT は本ファイル + `/deepthink` `/deepplan` overlay）。Claude Code frontmatter は `model: claude-fable-5-1` + `effort: medium`。

フラグ上書き（タスク文言から除外）: `--effort=low` / `--effort=medium` / `--effort=high` / `--effort=max`。

## 起動体数

Fable 系の deliberator は **必ず 1 体**（`fable-single`）。panel 並列にしない。
