# サブエージェントの権限と技術選定

サブエージェントへ書込可能なunitを委譲する前、または権限promptの挙動を調べるときに読む。

## Edit / Write

- activeなClaude Codeのuser・project・local settingsを確認し、`permissions.allow`と`deny`を実際のtool名・path patternで評価する。`Edit`の許可から`Write`の許可を推測しない。
- sourceを編集するsubagentには、親がexclusive file ownershipを与える。必要な権限がなければ、対象projectの`.claude/settings.local.json`でそのprojectだけに限定したruleを使う。
- `Edit(*)`、`Write(*)`、home全体など、globalな無制限許可を追加しない。
- read-only agentは設定やファイルを変更せず、観測結果と未確認事項を親へ返す。

## tech-validator

ライブラリ・frameworkの追加、更新、置換、候補比較では`tech-validator`を使い、公式一次情報と現行versionを確認する。既存依存を決まった方法で使うだけの実装や、選定済みの方針に再選定を挟まない。
