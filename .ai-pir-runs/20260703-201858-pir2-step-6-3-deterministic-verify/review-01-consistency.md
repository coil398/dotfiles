VERDICT: FAIL

### 担当 role
consistency

### 判断根拠

#### 命名規則・構造の一貫性
- 新規 reference `deterministic-completion-check.md` の命名・粒度は既存 `destructive-change-check.md`（`*-check.md` 命名・「概要→判定項目→判定結果の書き出し→運用/スキップ条件→完了後」の章立て）と実際に Read して比較し、章立て（適用対象actor→検証の情報源→pre-set/post-set→集合照合規則→NO_OP免除→判定結果の書き出し→失敗パス→スキップ条件→完了後）が同型であることを確認した。命名・粒度は既存慣習に合致する。
- pir2 SKILL.md の `### 6-3` 挿入位置（`### 6-2` と `### 完了後` の間）は plan 指定どおりで、既存の 6-0/6-1/6-2 という hyphen 番号の H3 サブ見出し体系に連番で追従しており違和感はない。ただし next-steps-queue.md 側で 6-3 だけが独立 checkbox を持つ設計（後述「同一ロジックの全適用箇所の網羅性」参照）は、既存の「decimal 番号（5.6/5.7/5.8/6.5/7.5 等）＝独立 H2＋独立 checkbox」「hyphen 番号（6-0/6-1/6-2）＝親 H2 と checkbox 共有」という暗黙の構造対応から逸脱している（Medium、問題一覧参照）。
- pir2codex SKILL.md の 6-1 bullet1/3 書き換え・6-3 用 pre-set 追記は既存フォーマット（`#### 見出し` + 箇条書き）に忠実で、実装完了レポートフォーマット（`~/.claude/agents/implementer.md`）への参照の仕方も pir2 側と同一。
- 一方で、旧「git diff で実体検証（必須）」という ad hoc な言い回しが、正式にリネームされた「決定論的完了検証（6-3）」に統一されないまま pir2codex SKILL.md の 3 箇所（153・182・277 行目）に残存していることを grep で確認した（詳細後述、High）。

#### 同一ロジックの全適用箇所の網羅性
- **PHANTOM_RETRY_COUNT の配線**: pir2 SKILL.md の step6 init（269行目）・step12（546行目）の両方、pir2codex SKILL.md の step6 init（108行目）・step12（287行目）の両方に出現することを `grep -n` で確認した。片側漏れなし。
- **next-steps-queue.md の checkbox 追加**: 「ステップ 6: implementer 起動」直後に「ステップ 6-3」checkbox が1行追加されていることを確認した。
- **implementation-delegation.md の相互参照ノート**: 「shard 統合確認」節（67行目）・「unit 統合確認」節（114行目）の両方に、plan 付録の文言と完全一致する相互参照ノートが挿入されていることを diff で確認した。review-fix shard の統合確認（同ファイル 118-134行目）には同ノートが無いが、plan の「配線しない（follow-up 候補）」に明記された意図的スコープ外であり、欠落ではない。
- **旧 "git diff 実体検証" 表現の不完全な置換（High・新規欠陥）**: pir2codex SKILL.md の「wrapper 返り後のスキル本体の処理（共通）」bullet1 は正式に「決定論的完了検証（6-3・必須）」に書き換えられた（176行目）。しかし同じロジックを指す旧来の ad hoc な言い回しが、少なくとも次の 3 箇所に取り残されている（`grep -n "git diff" .claude/skills/pir2codex/SKILL.md` で確認）:
  - 153行目「wrapper Agent への指示テンプレート」: 「wrapper 自身はファイル検証しない（呼び出し元が **git diff で検証する**）」
  - 182行目「6-1a: codex-single」: 「wrapper を1体起動 → **git diff 検証** → threadId 保持 → implementation-{IMPL_INDEX}.md を Write」
  - 277行目「ステップ12 最終サマリー」の「### 変更ファイル」直下: 「[implementation レポートから抜粋。**git diff で実体検証済み**であることを明記]」
  - このうち 277 行目は、直後（284-287行目）に新設された「### 決定論的完了検証（6-3）」ブロックと同一の情報を古い言い回しで重複記載しており、読み手には「git diff の素朴チェック」と「決定論的完了検証（6-3）」が別物であるかのように誤読させる。
  - plan の実装ステップ11・テスト検証手順は「旧 `git diff --name-only HEAD` という**文字列**が残っていないか」を grep で確認する設計だったため、意味は同じだが表現が異なるこれら3箇所を検出できなかった（実装完了レポートの自己検証コメント3でも「置換漏れなし」と誤って結論している）。なお 202行目「6-2: inner-loop の再実装」の「git diff 検証」は plan で明示的に「変更しない（6-2 の既存 git diff 検証は軽量自己チェックとして据え置く）」とスコープ外にされており、これは正当な残存で問題ではない。
- **reference file 内部での新設ロジック（3b フィルタ）の反映漏れ（High・新規欠陥）**: `verify-01.md` に記載の経緯どおり、初回照合で PHANTOM 誤検出（リポ外・gitignore 対象ファイルの申告）が起き、これを機に reference に「git 検証不能な申告の扱い」節（23行目）と bash ステップ「3b」（69-84行目、`claimed-trackable.list` / `claimed-untrackable.list` を生成）が追加された。この対応自体は正当な設計修正として指示どおり許容する。しかし同じ reference ファイル内で、この新設フィルタが以下の下流セクションに反映されていない:
  - 「判定結果の書き出し」テンプレート（130-143行目）: `CLAIMED: <claimed.list の件数> 件` のままで、trackable/untrackable の内訳を書く欄がない。実際に生成される `claimed-untrackable.list` はこのテンプレートのどこからも参照されない（`grep -n "untrackable" deterministic-completion-check.md` で該当行が生成箇所（71/72/76/79行目）のみで、消費箇所が皆無であることを確認した）。
  - 「失敗パス」節のユーザーゲート文面（156-174行目）も同様に `<claimed.list>` のみを参照し、trackable/untrackable の区別に触れない。
  - 実際の `verify-01.md` はこの欠落を補うため、テンプレートにない独自セクション「## 検証不能として除外（PHANTOM 対象外）」を即興で追加している。これは今回は正しい振る舞いだが、reference file 自体がこの新設ロジックを自己完結的に文書化できていないことを意味し、次回以降の run（特に pir2codex や `main` 実装フォールバックが使えない状況での再実行）が本テンプレートを字義通りに踏襲すると、trackable/untrackable の内訳が verify-*.md から欠落し、なぜ CLAIMED 件数と PHANTOM 判定件数が食い違うのかが読み手に説明されない状態が再発しうる。同一ファイル内で新設した概念が別セクションに伝播していない、という「同一ロジックの全適用箇所の網羅性」観点そのものの欠陥である。

#### 類似ファイル群への波及網羅性
- pir2 ↔ pir2codex の対称ワークフローペアへの配線は両側で確認できた（pre-set 記録・6-3/6-1 決定論的完了検証・step12 検証結果ブロックがいずれも両 SKILL.md に存在）。plan が明記した「配線しない（follow-up 候補）」リスト（pir2 7-4/8-2/6.5-2(C)/refactor-advisor-gate、pir2codex 6-2 inner-loop、pir2async・debug・ir）は今回のスコープ外として妥当に除外されており、`ls .claude/skills/pir2/references/` で列挙した既存 reference 群のうち今回変更が必要な箇所（next-steps-queue.md, implementation-delegation.md）はすべて変更されていることを確認した。他の未変更 reference（continuation-gate.md, fan-out-gate.md 等）は今回のスコープと無関係であり、波及漏れではない。
- next-steps-queue.md の共有チェックボックス文言「ステップ 6-3: 決定論的完了検証（**main 実装時はスキップ**）」は pir2 / pir2codex 共通運用のテンプレートだが、"main" という actor 名は pir2 固有（pir2codex には存在しない）であり、pir2codex 文脈でこのテンプレートを読む者には意味不明瞭になりうる（実害はなく Low）。

### 問題一覧
- High `~/.claude/skills/pir2/references/deterministic-completion-check.md:69-96,130-143,156-174` — 新設された「git 検証不能な申告（3b: claimed-trackable / claimed-untrackable フィルタ）」ロジックが同一ファイル内の「判定結果の書き出し」テンプレートおよび「失敗パス」ユーザーゲート文面に反映されていない。`claimed-untrackable.list` は生成されるが最終出力のどこからも参照されない。 → 「判定結果の書き出し」テンプレートに `- CLAIMED（git 追跡可能）: <claimed-trackable.list の件数> 件（検証不能で除外: <claimed-untrackable.list の件数> 件）` 相当の行と、`## 検証不能として除外（PHANTOM 対象外）` セクション（`verify-01.md` が実際に書いた内容を正式なテンプレートとして採用）を追加する。「失敗パス」のユーザーゲート文面にも同様の内訳を反映する。
- High `.claude/skills/pir2codex/SKILL.md:153,182,277` — 6-1 の実体検証ロジックを「決定論的完了検証（6-3）」に正式リネームしたにもかかわらず、旧来の ad hoc な「git diff 検証」「git diff で検証する」「git diff で実体検証済み」という言い回しが3箇所に残存し、特に277行目は直後の新設「### 決定論的完了検証（6-3）」ブロックと内容が重複・矛盾する。plan の grep 検証（`git diff --name-only HEAD` という完全一致文字列のみ）ではこの言い換え箇所を検出できなかった。 → 153行目・182行目・277行目の「git diff」を「決定論的完了検証（6-3）」または「6-3 の決定論的完了検証」に統一する。特に277行目は新設ブロックと重複するため、削除するか新設ブロックへの参照に置き換える。
- Medium `.claude/skills/pir2/SKILL.md:306-313` / `.claude/skills/pir2/references/next-steps-queue.md:23` — 新設 `### 6-3` は 6-0/6-1/6-2 と同じ H3 サブ見出し階層にありながら、next-steps-queue.md で独立した checkbox item を持ち、独自の `#### 完了後`（H4）を持つ。既存の「decimal 番号 = 独立 checkbox（5.6/5.7/6.5/7.5 等）」「hyphen 番号 = 親と checkbox 共有（6-0/6-1/6-2）」という暗黙の構造規則から6-3だけが逸脱する。resume 時の追跡粒度向上を意図した設計と解釈できるため Critical/High とはしないが、将来の同種サブステップ追加時に規則が曖昧化する。 → 意図的な設計選択であることを reference か SKILL.md にコメントとして明記するか、次回の instruction-refactor で番号体系の使い分けルールを明文化する。
- Low `.claude/skills/pir2/references/deterministic-completion-check.md:100-106` — 「集合照合規則」テーブルで PHANTOM 判定行は `claimed-trackable.list` を使い、UNDECLARED_CHANGE 判定行は（フィルタ前の）`claimed.list` を使う、という使い分けがテーブル単体からは根拠不明（bash 側のコメント「delta は全て in-repo・非 ignore なので比較相手は full claimed でよい」は把握したが、テーブルには注記がない）。機能的には等価であることを確認済みだが、可読性のため脚注を追加するとよい。
- Low `.claude/skills/pir2/references/next-steps-queue.md:23` — 共有テンプレートの checkbox 文言「main 実装時はスキップ」が pir2codex 文脈では意味を持たない actor 名を含む。実害なし。

### 担当外で気づいた点（参考）
- `.ai-pir-runs/20260703-201858-pir2-step-6-3-deterministic-verify/verify-01.md:9` — PHANTOM 誤検出からの偽陽性修正の経緯・reviewer への申し送りは correctness/reference-fidelity 観点で妥当性検証が必要（今回は consistency 観点のため深追いしていない）。
- `git status` で確認できる並行差分（`.claude/settings.json`, `.claude/skills/deepthink/SKILL.md`, `.claude/skills/pir2/references/experimental.md`, `.gitignore`, `CLAUDE.md`, `.claude/agents/epic-planner.md`, `.claude/skills/epic/SKILL.md`）は implementer が自己申告（implementation-01.md 注意点2）で明示的に「自分のタスクではない」と切り分けており、CLAIMED にも含めていない。本セッション由来ではないと判断し、consistency の問題一覧には含めていない（参考情報として記録）。

### 良好点
- pir2 / pir2codex 双方の PHANTOM_RETRY_COUNT 配線・next-steps-queue.md checkbox・implementation-delegation.md 相互参照ノートは plan 付録の文言と逐語一致し、grep による欠落確認も通過している。
- verify-01.md がドッグフーディングで発見した偽陽性（gitignore・リポ外パスの誤検出）に対する現場対応は妥当で、reviewer への申し送りも明示的。

### 次のアクション
1. `~/.claude/skills/pir2/references/deterministic-completion-check.md` の「判定結果の書き出し」テンプレート（130-143行目）と「失敗パス」ユーザーゲート文面（156-174行目）に、3b フィルタで生成される trackable/untrackable の内訳（`claimed-untrackable.list` の内容・件数）を反映するセクションを追加する。`verify-01.md` が実際に書いた「## 検証不能として除外（PHANTOM 対象外）」を正式テンプレートとして採用するのが最小差分。
2. `.claude/skills/pir2codex/SKILL.md` の153・182・277行目に残る旧「git diff 検証/実体検証」という言い回しを「決定論的完了検証（6-3）」に統一する。277行目は新設「### 決定論的完了検証（6-3）」ブロックと重複するため、削除または簡潔な参照に置き換える。
3. 上記2点を修正後、`grep -rn "git diff" .claude/skills/pir2codex/SKILL.md` を再実行し、6-2（意図的スコープ外）以外に「git diff」の素朴表現が残っていないことを確認する。
4. Medium/Low の指摘（6-3 checkbox 独立性の意図明記、next-steps-queue.md の "main" 文言）は任意対応でよいが、対応する場合は implementer に個別指示すること。
