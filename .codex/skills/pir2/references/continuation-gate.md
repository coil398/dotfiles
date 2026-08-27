# 続行可能ゲート（OUTER_LOOP_COUNT 上限到達時のみ）

PIR² 系スキル（/pir2, /pir2async）共通の続行可能ゲート仕様。tester FAIL の OUTER_LOOP 上限到達時に発動する。

## 発動条件

`OUTER_LOOP_COUNT == 3` に達した時点で、`{RUN_DIR}/test-{最新}.md` と `{RUN_DIR}/implementation-{最新}.md` を Read して以下の 4 条件を判定する:

- **(i)** 残 FAIL の根本原因が `test-*.md` に明示されているか（仮説でなく root cause 確定文言）
- **(ii)** worker の `task.md` / `requirements.md` に落とせる修正方針が単一に絞り込まれているか（複数案ぶら下がりでない）
- **(iii)** 修正の影響範囲が限定的か（変更は 3 ファイル以下、または設計層をまたがない）
- **(iv)** 過去ループで根本原因の二転三転が収束したか（連続する 2 つの `test-*.md` で同じ root cause が指摘されている）

**4 条件すべて満たす場合のみ**、以下のフォーマットでユーザーに続行可否を尋ねる:

```
## OUTER_LOOP 上限到達 -- 続行ゲート

OUTER_LOOP_COUNT=3 に到達しました。以下を検出しました:

- 残 FAIL の根本原因: <test-*.md からの引用>
- 修正方針: <implementation-*.md または直近 test-*.md からの引用>
- 影響範囲: <変更見込みファイル数 / 設計層>
- 過去ループでの収束: <連続2回同一 root cause>

続行 (Y) すると、4 条件がすべて成立している場合に限り OUTER_LOOP_COUNT を 4 に進め、もう 1 周だけ worker + reviewer + tester ループを回します。
移行 (N) するとここで overall FAIL の hard stop とし、追加 correction を作らず、成功完了・walkthrough・retrospect へ進みません。

続行しますか？ [Y/N]
```

## 運用ルール

- 4 条件のうち 1 条件でも不足する場合は Y/N ゲートを出さず、overall FAIL の hard stop とする。追加 correction、成功完了、walkthrough、retrospect へ進めない
- ユーザーが N を選んだ場合も overall FAIL の hard stop とし、追加 correction、成功完了、walkthrough、retrospect へ進めない
- **Auto mode でも本ゲートは必ずユーザー応答を待つ**（仕様変更判断ゲートのため Auto mode 例外）
- ゲート発火と判定結果は `{RUN_DIR}/user-decisions.md` に追記する
- ゲートを 1 サイクル中に通過できるのは最大 1 回のみ。OUTER_LOOP_COUNT=4 の追加周回で再 FAIL したら、追加 correction を作らず overall FAIL の hard stop とし、成功完了、walkthrough、retrospect へ進めない
