## [2026-07-03] プラン選択肢ユーザー確認（ステップ4.6）

### 決定1 — 6-3 の配線点
**(A) 6-1 直後の1箇所のみ**（最小スコープ）。review-fix(7-4)・test-fix(8-2) の再実装ポイントは対象外（別タスク）。

### 決定2 — pir2codex の扱い
**(B) reference 共通化**（planner 推奨(A) ではなく別案を選択）。6-3 のロジックを `references/deterministic-completion-check.md` に切り出し、pir2 の新 6-3 と pir2codex の既存 6-1 git diff 実体検証の**両方**を同一 reference に寄せて重複検証を解消する。→ pir2codex SKILL.md もスコープに含む。`PLAN_STRATEGY_CHANGED=true`。

### 決定3 — NO_OP 免除の実現
**(A) implementer.md に `NO_OP_JUSTIFIED` マーカー追記**。implementer が「変更不要が正当」なとき宣言でき、6-3 が自動で免除判定する。

### 字義解釈確認
決定2(B) の字義: 「共通 reference 作成 ＋ pir2 6-3 と pir2codex 既存 6-1 検証の両方をそこに配線して重複解消」。pir2codex の Codex 報告フォーマット（変更ファイル一覧の markdown 構造が未指定）を reference 側で正規化仕様として明記する。それ以外の pir2codex ロジックは触らない。
