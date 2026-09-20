---
name: "epic"
description: 大規模タスクを所有範囲の明確なサブタスクへ分割し、依存関係に沿って実装・統合する。複数サブシステムや独立機能を横断する改修に使う。
argument-hint: "[大規模タスクの説明]（先頭に任意で --codex）"
---

# Epic — Cursor native entry

ロード済みの本Skillの親の親を`CURSOR_SKILLS_DIR`とし、共有原本 [../../../.agents/skills/epic/SKILL.md](../../../.agents/skills/epic/SKILL.md) と同packageの `references/decomposition.md` を実体から解決してReadする。別配置では親が実在確認した共有Skillとreferenceの絶対pathを使う。親Cursor agentが探索統合、計画、依存DAG、所有、ユーザー判断、統合、受入を保持する。

## Cursorでの実行

- 子は標準Taskで起動し、modelは省略または`inherit`とする。read-only探索、排他的所有を持つ実装、必要なreview/testだけを分離し、子へ親用Epic工程や別の制御Taskを起動させない。
- 各担当へ対象版、目的、確認済み事実、許可・禁止範囲、依存、完了条件、focused checkと、担当自身が読む専門Skill/referenceの実体pathを渡す。独立単位だけを並列化し、共有契約・生成物・lockfile・同一ファイルを扱う単位は直列化する。
- 後続担当や再開に記録が必要な場合だけ `${CURSOR_SKILLS_DIR}/pir2/references/sanitized-cwd.md` をReadして専有run directoryを予約する。短いrunに計画・report・台帳を要求しない。
- `--codex`は先頭の明示フラグとしてだけ扱い、実装担当をcodex-runnerへ差し替える。計画、scope、DAG、統合、受入は親に残し、Codex CLIのmodel・sandbox・証跡・待機は `${CURSOR_SKILLS_DIR}/codex/SKILL.md` のbridge契約に従う。

親は各担当の返却をstatus、diff、実在する成果物、確認結果と照合する。reviewer/testerが必要なら共有原本の手順へ接続し、評価者には担当referenceの実体pathだけを渡す。未生成report、未起動Task、自己申告を成功条件にしない。
