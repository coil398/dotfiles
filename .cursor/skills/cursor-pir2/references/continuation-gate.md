# 続行可能ゲート（OUTER_LOOP_COUNT 上限到達時のみ）

PIR² 系スキル（/pir2, /pir2async）共通の続行可能ゲート仕様。tester FAIL の OUTER_LOOP 上限到達時に発動する。

## 発動条件

`OUTER_LOOP_COUNT == 3` に達した時点で、`{RUN_DIR}/test-{最新}.md` と `{RUN_DIR}/implementation-{最新}.md` を Read して以下の 4 条件を判定する:

- **(i)** 残 FAIL の根本原因が `test-*.md` に明示されているか（仮説でなく root cause 確定文言）
- **(ii)** implementer に渡せる修正方針が単一に絞り込まれているか（複数案ぶら下がりでない）
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

続行 (Y) すると OUTER_LOOP_COUNT は 4 に進み、もう 1 周だけ implementer + reviewer + tester ループを回します。
移行 (N) するとここで打ち切り、次ステップへ進んで現状の VERDICT: FAIL を確定します。

続行しますか？ [Y/N]
```

## 運用ルール

- 1 条件でも満たさない場合はゲートを出さず、従来通り次ステップへ無条件移行する
- ユーザーが N を選んだ場合も次ステップへ移行
- **Auto mode でも本ゲートは必ずユーザー応答を待つ**（仕様変更判断ゲートのため Auto mode 例外）
- ゲート発火と判定結果は `{RUN_DIR}/user-decisions.md` に追記する
- ゲートを 1 サイクル中に通過できるのは最大 1 回のみ（OUTER_LOOP_COUNT=4 で再 FAIL したら無条件に次ステップへ）
