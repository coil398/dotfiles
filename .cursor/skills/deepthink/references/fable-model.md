# Fable 5.1 — 明示モデル契約

このreferenceは、Cursorの`/deepthink`が必ず使うFable 5.1のモデル識別子と推論量を示します。親は熟考Taskを委任する前にこのreferenceをReadして起動指定を確定し、`/deepthink`の熟考担当は親から受け取った指定を使います。親の直接回答や別モデルへ置き換えません。Cursorの`deepplan`で独立した熟考・統合・十分性確認を委任するときも、この契約を使い、各Taskに同じFable指定を渡します。親が計画・統合・十分性確認を直接行う場合はTask用のモデル指定を追加しません。共有本文へruntime固有の起動APIを持ち込みません。

| 実行環境 | 起動時の指定 |
|---|---|
| Claude Code | `claude-fable-5-1` と `effort: medium` |
| Cursor | `claude-fable-5-1[effort=medium]` を Task 起動時に指定し、agent frontmatter は `inherit` |
| その他 | その環境が公開する正式な識別子へ明示的に対応付ける。未確認の別名は使わない |

短名や旧版を使わず、指定が実際に受理されることを起動結果で確認します。`medium`を既定とし、`low` / `high` / `max`はユーザーまたは親が明示した場合だけ選びます。Fable指定が受理されなかった場合は、親の直接回答、別方式、別モデルへ黙って切り替えず`INCOMPLETE`として理由と再開条件を返します。

熟考方式の`single`は一つの独立Fableコンテキスト、`panel`は複数の独立Fableコンテキストを意味します。`single`ではFable担当を1体、`panel`では必要な数のFable担当を起動します。担当の失敗を別方式や別モデルで隠さず、親が再実行の要否を判断します。
