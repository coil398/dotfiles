# refactor-advisor 提案ゲート

PIR² 系スキル（/pir2）の refactor-advisor 実行と任意適用フロー。reviewer 全員 PASS 後に **直列で 1 回のみ** 実行する設計（無限リファクタループ防止）。

## 起動条件

`REVIEWER_SET` の every reviewer が `VERDICT: PASS` を返し、未解決の
Critical / High がない全体 VERDICT PASS の場合のみ実行する。reviewer の
retry-cap hard stop はこのゲートへ入らず、refactor-advisor、tester、成功完了の
いずれにも進まない。

## 7.5-1: refactor-advisor を実行

subagent が利用可能なら `spawn_agent` に `agent_type="refactor-advisor"` を渡して `refactor-advisor` を **1 体だけ起動** する。モデル引数は指定せず、`${PROJECT_ROOT}/.codex/agents/refactor-advisor.toml` の role 定義に委ねる。利用できない場合は Sol orchestrator が read-only で同じ観点の提案レポートを作る（reviewer は全員 PASS で確定済み）:

- **モデル指定**: 呼び出し側では上書きしない（上記の role 定義を使用）
- **プロンプト**:
  - `PROJECT_MEMORY_DIR=[パス]`
  - `RUN_DIR=[パス]`
  - `REVIEW_INDEX=[最新 REVIEW_INDEX]`（reviewer の最新値をそのまま使う）
  - `{RUN_DIR}/plan.md` のパス
  - `{RUN_DIR}/implementation-{最新 IMPL_INDEX}.md` のパス
  - 「リファクタ提案レポート本体は `{RUN_DIR}/refactor-{REVIEW_INDEX}.md` に書き出し、チャットには PROPOSALS 数 + 要約のみ返してください」

## 7.5-2: 提案の存在確認

1. `{RUN_DIR}/refactor-{最新 REVIEW_INDEX}.md` を Read する
2. 冒頭の `PROPOSALS: N件` の N を確認する
3. `N == 0` の場合はスキップしてテストフェーズへ進む
4. `N >= 1` の場合は 7.5-3 へ

## 7.5-3: ユーザーへの提示

提案一覧をユーザーに提示する。**リスク情報（機能退行の可能性、golden カバレッジ等）はユーザーの適用判断に必須なので必ず含める**。フォーマット:

```
## リファクタ提案（refactor-advisor、Medium/Low）

N 件の改善候補があります:

1. [M|L] `ファイル名:行番号` — 提案タイトル
   現状: [要約]
   提案: [改善後の形]
   根拠: [既存先例、改善理由]
   リスク: [機能退行リスクの有無、golden カバレッジの状況]

2. [M|L] ...

適用する？
- all: 全件適用
- 1,3 のように番号カンマ区切り: 指定候補のみ適用
- none: 何も適用しない（そのままテストフェーズへ）
- custom: 個別にコメント書き換えたい等
```

## 7.5-4: ユーザー選択の処理

- **none**: テストフェーズへ進む
- **all / 番号指定**: 選択された候補を実装修正へ渡す（7.5-5 へ）
- **custom**: ユーザーから追加指示を受け取り、それを実装修正へ渡す（7.5-5 へ）

## 7.5-5: リファクタ適用

1. `IMPL_INDEX` をインクリメント
2. リファクタ適用は `${PROJECT_ROOT}/.codex/skills/worker-delegation/SKILL.md` の actor ladder に従う具体実装として扱い、`worker-delegation` の shard 並列は使わない。Sol orchestrator が修正用 `task.md` / `requirements.md` を作成し、まず Luna Max worker を明示起動する。Luna の capability/local-reasoning insufficiency を実測できた場合だけ Terra High、許可された証拠がある場合だけ Terra Max（一原因につき一度）、その後に測定済み Terra insufficiency がある場合だけ Sol High worker、highest-complexity/high-risk evidence または documented Sol High insufficiency がある場合だけ Sol Max worker（一原因につき一度）へ明示昇格する。各段は条件付きで、全段を必ず実行しない。Sol orchestrator は対象リポジトリを実装・修正しない:
   - task には「リファクタ提案の適用。機能要件変更なし。退行させないこと」を明示する
   - `{RUN_DIR}/refactor-{最新}.md` のパスと **選択された候補番号** を使う
   - `requirements.md` には適用候補、機能要件不変、許可ファイル、必要な検証コマンドを `R<number>` として列挙する
   - Terra/Sol の effort を上げる根拠に requirements / environment / permission / external/CLI failure を使わず、全 attempt に `automatic_fallback=no`、実際の actor/model/effort、evidence-backed escalation reason を記録する
   - implementation レポートには「適用した候補 / スキップした候補 / 理由」を記録し、Sol は report ではなく差分とコマンド出力で acceptance を実測する
3. 修正完了後、**Fan-Out Gate（SKILL.md 7-2A の宣言 → 7-2B の並列レビュー）** で reviewer のみ同じ REVIEWER_SET で再レビュー（`REVIEW_INDEX` をインクリメント、退行検知のため。refactor-advisor は再実行しない = 2 周目のゲートを開かず無限ループ防止。**再レビュー時も Fan-Out Gate を省略しないこと**）
4. 再 reviewer で 1 role でも non-PASS、未報告、判定不能、または未解決の Critical / High が出た場合は、SKILL.md 7-4 の FAIL フローに合流して差し戻しループを回す。`INNER_LOOP_COUNT` は継続インクリメントし、上限到達時は overall FAIL、未解決事項の報告、ユーザーの判断を求める hard stop になる。tester、成功完了、または refactor-advisor の再実行へ進めない。差し戻し成功後に再度 7.5 に戻ることはしない（refactor-advisor は初回 PASS 時の 1 回のみ）
5. 同じ `REVIEWER_SET` の every reviewer が PASS を返し、未解決の Critical / High がない場合だけテストフェーズへ進む
