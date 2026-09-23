# サブエージェントの書き込み権限

サブエージェントへ書き込みを伴う作業を委譲する前、または権限promptの挙動を調べるときに読む。

- `general-purpose` の子は親セッションの権限設定をそのまま使う。起動時にtoolや書き込み範囲を絞る手段はない。
- activeなClaude Codeのuser・project・local settingsを確認し、`permissions.allow`と`deny`を実際のtool名・path patternで評価する。`Edit`の許可から`Write`の許可を推測しない。
- sourceを編集する子には、親が排他的なfile ownershipを与える。必要な権限がなければ、対象projectの`.claude/settings.local.json`でそのprojectだけに限定したruleを使う。
- `Edit(*)`、`Write(*)`、home全体など、globalな無制限許可を追加しない。
- 読み取り専用の担当は指示による境界で守る。プロンプトで編集禁止と書いてよい出力pathを明示し、返却後に親が`git status`とdiffで確認する。
