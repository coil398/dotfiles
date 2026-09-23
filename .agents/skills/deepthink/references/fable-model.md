# 熟考モデル契約（deepthink / deepplan）

このreferenceは、`/deepthink` と `/deepplan` の熟考・統合・十分性確認に使うモデル識別子を示します。親は Task を委任する前にこのreferenceをReadして起動指定を確定し、担当は親から受け取った指定を使います。親の直接回答へ置き換えません。ユーザーが指名していないモデルへ黙って切り替えません。親が計画・統合・十分性確認を直接行う場合は Task 用のモデル指定を追加しません。共有本文へ runtime 固有の起動 API を持ち込みません。

既定は Fable 5.1。ユーザーが Opus 5.5 を指名したときだけ Opus 5.5 を使う。

## Fable 5.1（既定）

| 実行環境 | 起動時の指定 |
|---|---|
| Claude Code | Agent tool の `model` に `claude-fable-5-1` |
| Cursor | 標準Task（`subagent_type: "generalPurpose"`）の `model` に `claude-fable-5-1-thinking-high`。`claude-fable-5-1[effort=…]` は Task が拒否するので使わない |
| その他 | その環境が公開する正式な識別子へ明示的に対応付ける。未確認の別名は使わない |

## Opus 5.5（ユーザーが指名したとき）

| 実行環境 | 起動時の指定 |
|---|---|
| Claude Code | Agent tool の `model` に `claude-opus-5-5` |
| Cursor | 標準Task（`subagent_type: "generalPurpose"`）の `model` に `claude-opus-5-5-medium`。`[effort=…]` は使わない |
| その他 | その環境が公開する正式な識別子へ明示的に対応付ける。未確認の別名は使わない |

短名や旧版を使わず、指定が実際に受理されることを起動結果で確認します。Claude Code の Agent tool は effort を呼び出しごとに指定できず、担当は親セッションの effort を引き継ぐ。Cursor の推論量はモデル ID に含まれ、`[effort=…]` では渡さない。選定したモデルの指定が受理されなかった場合は、親の直接回答、別方式、別モデルへ黙って切り替えず `INCOMPLETE` として理由と再開条件を返します。

熟考方式の `single` は選定したモデルの独立コンテキスト 1 つ、`panel` は複数の独立コンテキストを意味します。`single` では担当を 1 体、`panel` では必要な数の担当を、いずれも同じ選定モデルで起動します。担当の失敗を別方式や別モデルで隠さず、親が再実行の要否を判断します。
