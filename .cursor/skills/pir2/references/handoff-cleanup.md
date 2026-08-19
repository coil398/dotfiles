# handoff.md 完了判定と後処理

PIR² 系スキル（/pir2, /pir2async, /debug）共通の handoff.md ライフサイクル後処理。

`$HANDOFF_PATH` が存在する場合のみ実行:

1. `$HANDOFF_PATH` を Read し「残 TODO」セクションの `[ ]` と `[x]` を数える
2. 全項目が `[x]` の場合: `Bash(rm "$HANDOFF_PATH")` で削除し、最終サマリーに「🎉 handoff.md 全項目完了 → 削除済み」と記載する
3. 残項目ありの場合: `Edit` で `最終更新` 行を `YYYY-MM-DD HH:MM (run: $(basename $RUN_DIR))` に更新し、最終サマリーに「⏭️ handoff.md に未完 N 項目残置: `$HANDOFF_PATH`」と記載する

`$HANDOFF_PATH` が存在しない場合（`RESUME_MODE=passive-notice` 直後や implementer が一度も走らなかった場合など）はスキップ。

詳細プロトコル: `~/.cursor/pir-handoff.md`
