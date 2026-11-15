VERDICT: PASS

### 担当 role
architecture

### 再レビュー対象
- `implementation-02.md`（review-fix レポート）
- `git diff HEAD -- .claude/skills/pir2/SKILL.md .claude/skills/pir2codex/SKILL.md .claude/skills/pir2/references/next-steps-queue.md` の実差分
- 新規 `.claude/skills/pir2/references/deterministic-completion-check.md` の全文 Read（untracked のため diff ではなく実ファイル全体を確認）

### 前回 High-1（pir2codex の検証順序）再確認 — 解消済み
`pir2codex/SKILL.md` の diff を確認した。「wrapper 返り後のスキル本体の処理（共通・順序厳守）」見出しの直下に「決定論的完了検証（6-3）は `implementation-{IMPL_INDEX}*.md` の『### 変更ファイル一覧』を情報源とするため、その報告ファイルを Write してから検証する順序でなければならない（先に検証すると CLAIMED が常に空になり誤判定する）」という明示の順序制約文が追加され、手順が「1. implementation レポートを Write → 2. 決定論的完了検証（6-3） → 3. threadId を保持」に組み替わっている（旧: 検証→threadId保持→Write）。6-1a の要約行も「wrapper を1体起動 → implementation-{IMPL_INDEX}.md を Write → 決定論的完了検証（6-3） → threadId 保持」に更新されており、旧順序の記述（「git diff 検証 → threadId 保持 → Write」）は残っていない（grep で確認、`git diff --name-only HEAD` の旧表現は消えている）。CLAIMED の唯一の情報源であるレポートファイルが検証実行時点で必ず存在する順序になっており、pir2codex 固有の「検証が常に誤判定する」構造的欠陥は解消されている。6-2（inner-loop 再実装）側の記述も新順序（Write → 軽量自己チェック）に整合しており、6-2/6-3 の別レイヤー・別スコープという区分（決定1=A の温存）も明記が維持されている。

### 前回 High-2（pre-set 据え置きと retry index の破綻）再確認 — 解消済み
新規 reference のpre-set 記録節（35-47行）で `PRE_IMPL_INDEX="$IMPL_INDEX"` を pre-set 記録時点に固定し、post-set/delta 計算節（60-62行）で `comm -13 "$RUN_DIR/verify-${PRE_IMPL_INDEX}-pre.list" "$RUN_DIR/verify-${IMPL_INDEX}-post.list"` と、pre 側だけ `PRE_IMPL_INDEX` を、post/delta 側は現在の `IMPL_INDEX` を参照するよう変数を分離した。CLAIMED 抽出（67-75行）も `for idx in "$PRE_IMPL_INDEX" "$IMPL_INDEX"` で両ラウンドの implementation レポートを累積（前ラウンドの正当な申告が再実行後に UNDECLARED として誤検知されるのを防ぐ設計）。失敗パス（177-180行）の自然言語記述「再起動後、pre-set は `verify-${PRE_IMPL_INDEX}-pre.list`（初回起動時点のスナップショット）を据え置きで参照し続け、post-set / delta は新しい `IMPL_INDEX` で再計算する」は、この bash 実装と完全に整合している。前回指摘した「pre.list も post.list も同一の `${IMPL_INDEX}` 変数を使うため、リトライ後に pre.list が指すべきファイルが存在しない」という構造的矛盾は解消された。なお `PRE_IMPL_INDEX`/`IMPL_INDEX` はいずれも既存の `INNER_LOOP_COUNT`/`OUTER_LOOP_COUNT`/`PHANTOM_RETRY_COUNT` と同種の「スキル本体（オーケストレーティング Claude）がターン間で保持する名目上の変数」であり、実際の bash セッション変数として永続化される前提ではない（`RUN_DIR`/`PROJECT_ROOT` など既存記法と同じ扱い）。この点は本 reference 全体の既存記法パターンであり、今回の修正が新たにこの前提を破ってはいない。

### 前回 High-3（3b 除外条件の広さ）再確認 — 設計判断として妥当・残存限界を Medium として記載
前回、reviewer（自分）は「除外を `{RUN_DIR}/handoff.md` 相当・`$PROJECT_MEMORY_DIR/` 配下の2パターンに限定すべき」と提案したが、ユーザーの必須修正指示は代わりに「3b の広い除外条件（絶対パス全般・gitignore 対象全般）は維持したまま、3c として `test -f` による実体存在確認を追加し、存在しない申告を `claimed-untrackable-missing.list` に warn 記録する（PHANTOM の hard fail 対象にはしない）」という別設計を採用した（`implementation-02.md`「注意点・未解決事項」に明記済み）。

両案を設計判断として比較評価した:

- **reviewer 提案（allowlist 限定）の欠点**: `deterministic-completion-check.md` は pir2/pir2codex 共通のグローバル SSOT であり、あらゆるプロジェクト・将来のワークフロー（例: epic 系列が新しい bookkeeping パス規約を持つ場合）に恒久適用される。allowlist を2パターンに限定すると、将来新設される正当な untrackable bookkeeping パス（新しい memory ログの命名規則、別スキルの中間ファイル等）が誤って PHANTOM 扱いされ hard fail する。これは reference 自身が明記する設計原則「偽陽性で実験を殺さない非対称検証」（132-134行）および CLAUDE.md のグローバルファイル汎用性ルール（プロジェクト固有・ワークフロー固有の具体パスをグローバル SSOT に埋め込まない）の両方に反する。allowlist は「見逃しを減らす」代わりに「正当な実装を止める」という別のコストを生む。
- **採用案（3c: 存在確認+warn）の効果と限界**: 3c は「存在しないパスへの虚偽申告」（例: LLM が実際には作成していないメモリログパスを幻覚的に申告する）を warn として可視化する点で、3b 単体（無条件除外・シグナル皆無）より前進している。ただし `test -f` は**存在確認のみ**であり、**その実装 actor 起動でこの内容が実際に変更されたか**は確認できない。したがって「実在する gitignore 対象ファイル（例: 既存の `.env`）を『編集した』と虚偽申告するが実際には何も変更していない」ケースは、`test -f` が真を返すため何のシグナルも残らず素通りする、という残存穴が具体的に存在する。これは前回指摘の懸念が完全には解消されていないことを意味する。
- **残存穴の深刻度判定**: この残存穴は、設計 SSOT（`docs/deepthink/20260703-190750-Fable5.md` 残存限界 ④「既 dirty ファイルへの虚偽申告は `git diff --name-only` では検出不能（内容ハッシュ突合は較正フェーズの拡張候補）」・⑥「hook は fail-open（事故の計器であって攻撃への防御ではない）」）が git 追跡対象ファイルについて既に明示的に受容している残存限界と**同型**である（対象が「既に git 管理下で dirty だったファイル」か「git 管理外・gitignore 対象ファイル」かの違いのみで、「内容が実際に変更されたかまでは検証しない」という限界の本質は同一）。設計 SSOT はこの種の限界を「内容ハッシュ比較は将来拡張候補・現行スコープ外」として明示的に容認しており、本ゲート自体が単一ユーザー環境での偶発捏造検知（accident meter）を目的とし、悪意ある攻撃者からの防御を目的としていないと明言している。したがって今回の残存穴を Critical/High として扱うのは、既に受容済みの設計方針に対して過大要求になる。**Medium**（ドキュメント上の正直な限界開示の一貫性の問題）として記載するに留める。
- **改善提案（Medium・任意）**: `deterministic-completion-check.md` の 3c 節に、Fable5.md 残存限界④と同型の一文（例:「`test -f` は存在確認のみであり、対象ファイルがこのラウンドで実際に変更されたか（内容ハッシュ等）は検証しない。既存の実ファイルへの虚偽申告はこの限りでは検出できない（Fable5.md 残存限界④と同根、将来拡張候補）」）を明記すると、設計全体の「残存限界の正直な開示」という一貫した哲学（Fable5.md 成功基準5）に沿う。ただしこれは記述の完全性向上であり、機構自体の欠陥ではないため VERDICT には影響しない。

### 前回 Medium（pre-set 記録の配置順序・6-3 の完了後 h4 重複）再確認 — 両方解消
- pir2 SKILL.md: pre-set 記録の指示（旧: implementer 起動宣言文より後方）が「### 6-1: implementer 起動」見出し直下・起動宣言文より**前**に移動済み（diff で確認）。
- pir2codex SKILL.md: 同種の pre-set 記録が「#### wrapper 起動前の pre-set 記録」という独立した h4 見出しとして「wrapper Agent への指示テンプレート」見出しの**前**に新設されており、pir2 のインライン注記より明示性が高い（既存の「7-2A 起動宣言（Fan-Out Gate）」パターンに近い独立サブステップ化）。両ワークフロー間でこの部分の表現形式（pir2=インライン注記／pir2codex=独立見出し）に軽微な非対称があるが、いずれも「起動宣言より前」という機能要件は満たしており、実害はない（Low）。
- 6-3 内部の独自 `#### 完了後`（h4）は削除され、Step6 全体の既存 `### 完了後`（h3）に統合された（`sed -n '260,320p'` で実物確認。h4 の重複は解消。他ステップ（7, 8）と同じ「完了後は末尾に1個」の慣習に整合）。next-steps.md 上で「ステップ6」「ステップ6-3」が独立 checkbox を持つ設計意図（意図的な例外）も注記として明記されている。

### 6-2/6-3 の責務分離維持確認
`implementation-delegation.md` は今回 diff 対象外（未変更）であり、round 1 で追加された相互参照ノート（6-2＝shard/unit 境界の LLM 層レビュー、6-3＝全 actor の決定論層照合という棲み分け）はそのまま温存されている。pir2codex 側の 6-2 inner-loop も「git diff による軽量自己チェック（6-3 は初回実装点のみのスコープで対象外）」という新しい文言に更新されており、6-3 が 6-2 を dead 化させていない。

### 決定1=(A) 最小スコープの維持確認
`git diff --stat HEAD` で今回変更されたのは `.claude/skills/pir2/SKILL.md` と `.claude/skills/pir2codex/SKILL.md` の2ファイルのみ（+新規 untracked `deterministic-completion-check.md` と `next-steps-queue.md` の軽微追記）。7-4/8-2/6.5-2(C)/refactor-advisor-gate・pir2codex 6-2 inner-loop・pir2async/debug/ir への配線は今回も一切追加されていない（決定1=(A) を維持）。implementation-02.md の「注意点・未解決事項」で `git status --porcelain` により今回タスクのスコープ外の並行変更（`.claude/agents/implementer.md` 等）に手を出していないことも確認済みと明記されている。

### 問題一覧
なし（Critical/High 相当の architecture 観点の問題は検出されなかった）。

### 担当外で気づいた点（参考）
- `.claude/skills/pir2/references/deterministic-completion-check.md:84`（Low、担当外＝correctness 領域） — 3b の `case "$p" in /*|"~"|"~"/*)` パターンの bash 構文自体（tilde 判定の quote 方法）は correctness reviewer の確認範囲。architecture としては当該ロジックの配置・責務分離に問題なし。
- `.claude/skills/pir2/SKILL.md`（Low） — pre-set 記録の表現形式が pir2（インライン blockquote）と pir2codex（独立 h4 見出し）で非対称。対称ワークフローペアとしての一貫性を高めるなら、pir2 側も独立見出し化（例: `#### 6-1 用 pre-set 記録`）を検討する余地があるが、機能上の実害はなく任意。

### 良好点
- pre-set/post-set のインデックス分離（`PRE_IMPL_INDEX` 導入）は、既存の `INNER_LOOP_COUNT`/`OUTER_LOOP_COUNT`/`PHANTOM_RETRY_COUNT` と同じ「オーケストレーティング Claude がターン間で保持する名目変数」という既存記法パターンに忠実に拡張されており、新たな抽象を発明せず既存の設計言語で問題を解消している。
- 3c（untrackable 実体確認）は、3b の広い除外を維持しつつ「無条件の抜け穴」に人間可視の warn シグナルを追加するという設計であり、「偽陽性で実験を殺さない非対称検証」という reference 自身の中核原則と、CLAUDE.md のグローバル汎用性ルールの両方を守りながら、前回指摘の一部（幻覚的パス申告の見逃し）を具体的に縮小している。
- pir2codex の検証順序修正は、単に手順を並べ替えるだけでなく「なぜこの順序でなければならないか」という理由文を明記しており（「先に検証すると CLAIMED が常に空になり誤判定する」）、将来の編集者が誤って順序を再度入れ替えるリスクを下げている。

### 次のアクション
なし（PASS）。任意の改善提案（3c への残存限界の明記、pir2/pir2codex 間の pre-set 記述形式の対称化）は blocking ではないため、必要であれば refactor-advisor / 次回サイクルで拾う程度で良い。
