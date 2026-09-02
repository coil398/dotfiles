# Fable model contract（deepthink / deepplan）

## ピンする ID

| ランタイム | 指定 |
|---|---|
| Claude Code `Agent` / agent frontmatter | `claude-fable-5-1` |
| Cursor `Task` / agent frontmatter | `claude-fable-5-1[effort=high]` |
| OpenCode（sync 生成） | `anthropic/claude-fable-5-1` |

短名 `fable` / `fable5` は **最新へ自動追随しない**（`claude-fable-5` のまま残る経路がある）。必ず `claude-fable-5-1` をピンする。

## effort — high vs medium

Anthropic Effort docs（Fable 5.1）の公式:

- **開始点は `high`（製品デフォルト）**。省略時と同じ挙動。
- **`xhigh` / `max`**: capability-sensitive な agentic / coding で上げる。
- **`medium` / `low`**: routine または latency 重視のとき、**evals で品質が保たれると確認してから**下げる。

一般表では `medium` は「速度・コスト・性能のバランス」だが、Fable 5.1 向け推奨は「まず high」が上書きする。What's new でも **Fable 5→5.1 の改善幅は高い effort で最大**と明記。

| 値 | deepthink / deepplan / 重い設計 | いつ選ぶか |
|---|---|---|
| `high`（既定） | **これ** | 熟考・統合・ゲート・重いプラン。公式開始点 |
| `xhigh` / `max` | 明示時のみ | `--effort=max` 等。コスト・レイテンシ大 |
| `medium` | **既定にしない** | コスト削減で、かつ自前 eval で品質維持が取れたあと |
| `low` | 使わない | 単純サブエージェント向け |

Cursor では `claude-fable-5-1[effort=high]`。Claude Code frontmatter は `model: claude-fable-5-1` + `effort: high`。

## 起動体数

Fable 系の deliberator は **必ず 1 体**（`fable-single`）。panel 並列にしない。
