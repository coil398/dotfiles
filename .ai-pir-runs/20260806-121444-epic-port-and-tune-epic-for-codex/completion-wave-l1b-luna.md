ACTOR: luna  
STATUS: completed

変更:
- Worker ladder/runner/metadata/spec/testsを更新
- Terra/Solの努力量をHigh既定・Max明示に対応
- 旧`luna-max-worker`を削除

検証:
- `bash etc/test-codex-contracts.sh` — exit 0、351 passed / 0 failed
- 指定の`bash -n` 2件、`bash -n etc/sync-codex.sh`、`git diff --check` — exit 0
- Codex契約内の`sol-direct`・親Sol直接実装許可 — 該当なし

BLOCKERS: none

`.agents/**`、`.claude/**`、stage/commit/pushは変更していません。Solによる最終判定をお願いします。