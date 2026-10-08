# 熟考担当のモデル指定（deepthink）

`/deepthink` の熟考・統合・十分性確認の担当は、各runtimeのモデル方針（通常は親の選択を継承し、判断の重さに応じて親が明示選択する）に従う。モデルを固定しない。ユーザーがモデルを名前で指定した場合だけ、下の表の識別子で起動する。親は Task を委任する前にこのreferenceをReadして起動指定を確定し、担当は親から受け取った指定を使う。熟考を親の直接回答へ置き換えない。共有本文へ runtime 固有の起動 API を持ち込まない。

## ユーザーが Fable 5.1 を指定したとき

| 実行環境 | 起動時の指定 |
|---|---|
| Claude Code | Agent tool の `model` に `fable`（Agent tool はエイリアスだけを受理する） |
| Cursor | 標準Task（`subagent_type: "generalPurpose"`）の `model` に `claude-fable-5-1-thinking-high`。`claude-fable-5-1[effort=…]` は Task が拒否するので使わない |
| その他 | その環境が公開する正式な識別子へ明示的に対応付ける。未確認の別名は使わない |

## ユーザーが Opus 5.5 を指定したとき（`--opus-panel` を含む）

| 実行環境 | 起動時の指定 |
|---|---|
| Claude Code | Agent tool の `model` に `opus` |
| Cursor | 標準Task（`subagent_type: "generalPurpose"`）の `model` に `claude-opus-5-5-medium`。`[effort=…]` は使わない |
| その他 | その環境が公開する正式な識別子へ明示的に対応付ける。未確認の別名は使わない |

## 確認と失敗時

- Claude Code 以外では短名や旧版を使わない。指定したモデルが受理され、担当がそのモデルで動いたことを起動結果で確認する。Claude Code ではエイリアスの解決先が変わりうるため、担当の transcript に記録された model で確認し、effort は runtime のモデル別設定に従う。Cursor の推論量はモデル ID に含まれ、`[effort=…]` では渡さない
- ユーザーが指定したモデルが受理されなかった場合は、親の直接回答、別方式、別モデルへ黙って切り替えず、`INCOMPLETE` として理由と再開条件を返す

## 方式

熟考方式の `single` は選定したモデルの独立コンテキスト 1 つ、`panel` は複数の独立コンテキストを意味する。`single` では担当を 1 体、`panel` では必要な数の担当を、いずれも同じモデルで起動する。担当の失敗を別方式や別モデルで隠さず、親が再実行の要否を判断する。
