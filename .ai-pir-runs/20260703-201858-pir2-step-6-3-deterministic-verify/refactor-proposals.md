PROPOSALS: 8件

### 対象

W1 実装（pir2 ステップ 6-3「決定論的完了検証」新設 + pir2codex 共通 reference 化）。主対象は新規 `.claude/skills/pir2/references/deterministic-completion-check.md`（2026-07-03 21:50 版 = review-02-correctness の Medium 2件を事後修正した最新状態）と `pir2/SKILL.md`・`pir2codex/SKILL.md`・`next-steps-queue.md`・`implementation-delegation.md`・`agents/implementer.md`。

> ℹ️ 前提事実: reference は review-02-correctness（21:49）の後 21:50 に更新されており、同レビューの Medium 2件（3b `~user` 形式・3c `$PROJECT_ROOT` アンカリング）は**既に修正済み**（3b は `/*|~*)`、3c は `*) expanded="$PROJECT_ROOT/$p"` を現物で確認）。本提案はその修正後の状態を起点とする。

---

### 提案一覧

#### [M-1] `deterministic-completion-check.md:51-62` — post-set ブロック冒頭に pre.list 存在ガードを追加

- **(a) 現状**: post-set 記録・delta 計算ブロックは `comm -13 "$RUN_DIR/verify-${PRE_IMPL_INDEX}-pre.list" ...` を無条件に実行する。6-1 の pre-set 記録をオーケストレータが忘れた場合（本ゲートで最も起こりやすい手順ミス。pir2 SKILL.md:281 の blockquote 注記 1 箇所だけが頼り）、`comm` は「No such file or directory」で失敗するが **リダイレクトが空の delta.list を作ってしまう**ため、後段は「delta 空」として進む。PHANTOM 照合（claimed-trackable vs post）は生き残るが、**UNDECLARED 検出が無言で無効化**され、ゲートが「壊れたまま PASS 風の出力を出す」計器になる。
- **(b) 改善案**: post-set ブロック先頭に 1 行ガードを追加する:
  ```bash
  # 0. pre-set 存在確認（6-1 での記録漏れを silent 劣化させない）
  [ -f "$RUN_DIR/verify-${PRE_IMPL_INDEX}-pre.list" ] || echo "ERROR: pre-set 未記録（verify-${PRE_IMPL_INDEX}-pre.list なし）。delta/UNDECLARED が計算不能。6-1 の pre-set 記録手順に戻って原因を確認せよ（今から記録しても post と同一になり delta は空＝無意味）" >&2
  ```
  オーケストレータ（スキル本体）はこのメッセージを Bash 結果で受け取り、手順を巻き戻すか PHANTOM 照合のみの縮退運転かをユーザーに提示する。
- **(c) 効果**: 「決定論ゲート」の入力健全性を決定論的に守る。設計 SSOT（Fable5.md）が本ゲートを accident meter と位置づける以上、計器自身の未較正状態（基準スナップショット欠落）は fail-loud にすべきで、これは hook の fail-open 原則（計器が壊れてもワークフローは止めない）と矛盾しない — ワークフローは止めず、劣化を**可視化**するだけ。
- **(d) コスト/リスク**: 追記 2 行のみ。既存経路の挙動変更なし（ファイルが在れば no-op）。機能退行リスクなし。
- **(e) 優先度**: 高（Medium）。**今やるべき**。

#### [M-2] `pir2/SKILL.md:413` × `pir2codex/SKILL.md:204` × reference — inner-loop 再実装時の 6-3 適用スコープを明文化し reference に一元化

- **(a) 現状**: 3 つの記述が噛み合っていない。
  1. **pir2codex/SKILL.md:204** は「決定論的完了検証 6-3 は**初回実装点（6-1）のみ**適用するスコープのため、ここ（6-2 inner-loop）では対象外」と明示し、「6-2/6-3 のレイヤー分離は reference **冒頭**を参照」と誘導する。
  2. しかし **reference 冒頭（1-8行）**にあるのは「shard/unit 統合確認（LLM層）と claim-vs-diff 照合（決定論層）は別レイヤー」の話であって、「**inner-loop 再実装には適用しない**」というタイミングスコープはどこにも書かれていない（参照先に参照させた内容が無い）。
  3. **pir2/SKILL.md 7-4 手順3（:413）**の再実装フローは 6-3 再適用にも pre-set 再記録にも言及がなく、字義上は「再実装 → 直接 reviewer 再起動」。一方**本 run の実運用**は逆で、review-fix ラウンド（implementation-02）に対して pre-set 再記録（`verify-02-pre.list` 21:24）と 6-3 再適用（`verify-02.md` 21:38）を実施している。つまり pir2 は「字義=適用しない・実運用=適用した」、pir2codex は「明示=適用しない」という三すくみ。
- **(b) 改善案**: reference に `## 適用タイミング` 節（「適用対象 actor」節の直後）を新設し、「初回実装点のみ / inner-loop 再実装にも適用（その場合 fix ラウンド直前の dirty 集合で pre-set を再記録）」の**どちらかを SSOT として宣言**、pir2 7-4 手順3 と pir2codex 6-2 の両方からそこを参照させる。どちらの仕様にするかは判断が要る:
  - **(案i) inner-loop にも適用**: 再実装も implementer/Codex の自己申告境界を持つため telephone-game 検出の意味は初回と同じ。本 run の実運用（verify-02）と一致。ただし pir2codex 6-2 の明示除外と決定1=(A)「初回実装点のみ」の字義を変えることになる。
  - **(案ii) 初回のみ（pir2codex に揃える）**: 決定1=(A) の最小スコープに忠実。pir2 側 7-4 に「再実装では 6-3 を再適用しない」と明記し、本 run の verify-02 は「明文化前のドッグフーディング拡大適用」として整理。
  仕様選択はユーザーゲートで確定させること（refactor-advisor は機能仕様を決めない。ここでの提案は「非対称・参照切れを明文化で解消する」まで）。
- **(c) 効果**: 次回 run のオーケストレータが inner-loop で 6-3 を「やる/やらない」を場当たりで判断する余地を消す。resume 時の next-steps checkbox（6-3 独立 checkbox）との整合も一意になる。pir2codex:204 の「参照先に内容が無い」dangling reference も解消。
- **(d) コスト/リスク**: ドキュメントのみ。案i を選ぶ場合は決定1=(A) の適用範囲解釈の更新であり、experimental.md の観測条件への影響を確認すること。
- **(e) 優先度**: 高（Medium）。**今やるべき**（ただし仕様選択のユーザー確認込み）。

#### [M-3] `deterministic-completion-check.md:95-110`（3c） — `test -f` の残存限界を明記（architecture reviewer 委任分）

- **(a) 現状**: 3c は untrackable 申告の存在確認（`test -f`）を行うが、「**実在する** gitignore 対象/リポ外ファイルを『編集した』と虚偽申告するが実際は無変更」のケースは `test -f` が真を返すため無シグナルで素通りする。この限界は doc 内に書かれていない。
- **(b) 改善案**: 3c のコメントまたは直後に 1 文追加: 「`test -f` は存在確認のみであり、対象ファイルが**このラウンドで実際に変更されたか**（内容ハッシュ等）は検証しない。既存実ファイルへの虚偽申告はここでは検出できない（設計 SSOT `docs/deepthink/20260703-190750-Fable5.md` 残存限界④＝既 dirty ファイルへの虚偽申告と同根。内容ハッシュ突合は較正フェーズの拡張候補）」。
- **(c) 効果**: Fable5.md 成功基準5「残存限界の正直な開示」の一貫性。将来この doc だけを読む編集者が 3c を「untrackable の捏造も検出できる」と過大評価して依存するのを防ぐ。review-02-architecture:25 が「refactor-advisor で拾う程度で良い」と明示委任した項目。
- **(d) コスト/リスク**: 文言追加のみ。ゼロ。
- **(e) 優先度**: 中（Medium）。**今やるべき**。

#### [M-4] `references/verify-deterministic-check.sh` の新設 — reference 内 bash の機械検証（構文 + scratch-repo E2E）

- **(a) 現状**: 本 reference の bash 3 ブロックは、correctness reviewer が 2 ラウンドとも scratch git repo を**手動で**作ってエンドツーエンド実行して初めて FIX-1/FIX-5 の解消を確認できた（review-02-correctness:9-17）。また `.claude/settings.json` の shellcheck-hook は `*.sh` のみ対象で、**md 内 fenced bash は lint されない盲点**がある。今後この bash を編集するたびに同じ手動シミュレーションを再発明することになる。
- **(b) 改善案**: 既存先例 `references/verify-sanitized-cwd.sh`（「揺れを検出したら exit 1。pre-commit / CI 組み込み可」）と同型のスクリプトを新設する。**二重管理を避けるため bash を複製せず、md から fenced bash ブロックを抽出して実行する**:
  1. `awk`/`sed` で `deterministic-completion-check.md` の ```` ```bash ```` ブロックを抽出 → `bash -n` + `shellcheck -s bash`（構文・静的検査）
  2. scratch git repo を mktemp に作り、correctness reviewer が手動でやった代表シナリオを固定フィクスチャ化して実行: (α) tilde/絶対/相対パスの 3b 分類、(β) `.ai-pir-runs/` 相当の gitignore 対象申告の 3c PROJECT_ROOT アンカー存在判定、(γ) PHANTOM retry 2 ラウンド（PRE_IMPL_INDEX 据え置き + CLAIMED 累積）で phantom/undeclared がともに空になること
  期待結果と不一致なら exit 1。
- **(c) 効果**: プロジェクトメモリの原則「ルールには機械検出を併設する」（`feedback_rule_with_enforcement.md`、`sanitized-cwd.md:117` が参照）に沿う。今回のレビューで実際に 2 回発生した「bash 編集 → 手動 scratch-repo 再検証」のコストを恒久削減し、将来の W3/W4（hook 連携）で bash を触るときの退行検知にもなる。
- **(d) コスト/リスク**: スクリプト 1 本の新規作成・維持コスト。md のブロック構成（ブロック数・順序）に依存するため、reference 大改編時はスクリプト側の追従が必要（verify-sanitized-cwd.sh も同種の前提脆弱性を冒頭コメントで明示しており、同じ流儀で書けばよい）。
- **(e) 優先度**: 中（Medium）。**W2 以降に回す**（W1 の完了条件ではない。今回 run の next-steps / 設計 SSOT の follow-up に登録して次サイクルで実装するのが適切。決定1=(A) の最小スコープを今回 diff で膨らませない）。

#### [L-1] `deterministic-completion-check.md:157-174` — verify-{IMPL_INDEX}.md テンプレートに検証条件の自己記述行を追加

- **(a) 現状**: テンプレートは actor / CLAIMED 件数 / delta 件数 / 判定 / 3 リストの内容のみ。**PRE_IMPL_INDEX（どの pre-set を基準にしたか）・CLAIMED の情報源（どのラウンドの implementation-*.md を累積したか）・PHANTOM_RETRY_COUNT** が出力されないため、PHANTOM 再実行後の verify レポートは単体で検証条件を復元できない。実例として本 run の `verify-01.md` は「## 経緯」を自由記述で即興追加して補っており、定型欄の不足が場当たり記述を誘発している。
- **(b) 改善案**: テンプレート冒頭のメタ行に 3 行追加:
  ```markdown
  - PRE_IMPL_INDEX: <NN>（pre-set 基準スナップショット）
  - CLAIMED 情報源: <implementation-{PRE_IMPL_INDEX}*.md, implementation-{IMPL_INDEX}*.md>
  - PHANTOM_RETRY_COUNT: <N>
  ```
- **(c) 効果**: run の事後監査（retrospector / 設計 SSOT G2 の較正メトリクス収集）が verify md 単体で完結する。固定 key-value 行は将来の hook Stage A（log-only 計測、W3）が grep/jq で拾いやすい形でもあり、追加フォーマット発明なしで布石になる。ステップ12 サマリー（pir2 SKILL.md:542-545）と同じ項目名（PHANTOM_RETRY_COUNT）を使い用語も揃う。
- **(d) コスト/リスク**: テンプレート行追加のみ。ゼロ。
- **(e) 優先度**: 低（Low）。今やってよい。

#### [L-2] `deterministic-completion-check.md:84` — 3b の `~*` を `"~"*` にクォート統一

- **(a) 現状**: 3b の case は `/*|~*)`（unquoted）。bash では `~*` の tilde-prefix（login name `*`）が不正なため word は不変で**動作は正しい**が、これは bash の展開規則の細部に依存した書き方で、同一ファイル内の 3c（:102-106）が `"~"` / `"~"/*` とクォート済みなのと表記が不統一。review-02-correctness:32 も任意対応として `"~"*` を提案済み。
- **(b) 改善案**: `/*|"~"*)` に変更（意味は同一。先頭が文字通り `~` の任意文字列にマッチし、tilde 展開の考慮自体が不要になる）。
- **(c) 効果**: 「なぜここは unquoted で安全なのか」を読者が毎回検証する認知コストを消す。3b/3c 間の表記統一。
- **(d) コスト/リスク**: 意味不変のクォート追加。correctness reviewer の実機検証済み分類が変わらないことは `case "~user/foo" in "~"*)` の 1 行確認で再検証できる。
- **(e) 優先度**: 低（Low）。今やってよい。

#### [L-3] `deterministic-completion-check.md:66` — コメント「同じファイルを1回読むだけ」の事実修正（meta-accuracy）

- **(a) 現状**: CLAIMED 抽出のコメントに「通常（再実行なし）は PRE_IMPL_INDEX == IMPL_INDEX で同じファイルを**1回読むだけ**」とあるが、実装の `for idx in "$PRE_IMPL_INDEX" "$IMPL_INDEX"` は両者が同値でも 2 回ループして同一ファイルを **2 回**読む（`sort -u` で重複除去され結果は同一）。説明文と実装の主張が食い違う（review-02-correctness:53 の担当外指摘と同一。実装側は正しいので**説明文側を直す**）。
- **(b) 改善案**: 「通常（再実行なし）は PRE_IMPL_INDEX == IMPL_INDEX で同じファイルを 2 回読むが `sort -u` で重複除去され結果は 1 回分と同一」に修正。
- **(c) 効果**: 将来の編集者が「1回のはずなのに2回読んでいる＝バグでは」と誤診してループに手を入れる事故を防ぐ。
- **(d) コスト/リスク**: コメント修正のみ。ゼロ。
- **(e) 優先度**: 低（Low）。今やってよい。

#### [L-4] `pir2/SKILL.md:281` — pre-set 記録指示の記述形式を pir2codex と対称化（architecture reviewer 委任分）

- **(a) 現状**: 同一手順の記述形式が、pir2 は 6-1 内のインライン blockquote（:281）、pir2codex は独立 h4 見出し `#### wrapper 起動前の pre-set 記録（決定論的完了検証 6-3 用・必須）`（:137）と非対称。review-02-architecture:29,43 が Low として指摘し「refactor-advisor / 次回サイクルで拾う程度」と委任した項目。
- **(b) 改善案**: pir2 側も `#### 6-1 用 pre-set 記録（決定論的完了検証 6-3 用・必須）` の独立 h4 に昇格させ、既存の 7-2A「起動宣言（Fan-Out Gate）」のような「起動前の必須前処理は独立見出し」パターンに揃える。
- **(c) 効果**: 対称ワークフローペア（pir2 / pir2codex）の書き味の一貫性。resume 時・目次スキャン時の視認性（blockquote は読み飛ばされやすい。M-1 で指摘した「pre-set 記録忘れ」の発生確率を下げる構造的対策でもあり、M-1 のガードと事前/事後で補完する）。
- **(d) コスト/リスク**: 見出し化のみ。機能変化なし。
- **(e) 優先度**: 低（Low）。任意（W2 以降でも可）。

---

### 除外した候補（参考）

- `deterministic-completion-check.md:42-44,53-55` — pre-set/post-set の dirty 集合取得 `{ git diff --name-only; git ls-files --others --exclude-standard; } | sort -u` の関数化・ヘルパー化 → **除外**。理由は 3 点: (1) bash ブロック内の出現は **2 箇所**（:22 の散文は定義説明であり実装重複ではない）で DRY 3 箇所ルール未満。(2) **致命的な実行環境制約**: この bash はオーケストレータ Claude の Bash ツールで都度実行され、**シェル状態（関数定義）はツール呼び出し間で持ち越せない**。pre-set（implementer 起動前）と post-set（完了後）は必ず別ターン・別シェルなので、共通関数を定義しても post-set 側では未定義になる。共有するには別ファイル `.sh` に切り出して両ブロックで source する構造になり、instruction-doc の「逐語コピペで動く」自己完結性を壊す。(3) 2 箇所が**バイト同一である**こと自体が「pre と post は同じ定義の dirty 集合である」という照合の前提を明示する仕様表現になっており、抽象化するとむしろ照合可能性が下がる。
- `set -euo pipefail` の一括付与（呼び出し元から明示された検討依頼） → **除外（付けない方が良い）**。CLAIMED 抽出パイプラインの `grep -E '^- *\`'` は申告 0 件（`NO_OP_JUSTIFIED` の正当な運用パス）で exit 1 を返すため、`pipefail` はこの**正常系をエラーに変えてしまう**。また `-e` はブロック単位実行では途中失敗時に空 `.list` が残る問題（M-1 の対象）を防げず、`-u` が守りたい「変数未設定」はそもそもオーケストレータがターン間で名目変数（`PRE_IMPL_INDEX` 等）を文字列展開して埋め込む前提なので効果が薄い。「偽陽性で実験を殺さない非対称検証」（reference:136）の設計原則とも逆行する。守るべき不変条件は M-1 のような**対象を絞った明示ガード**で個別に張るのが適切。
- `deterministic-completion-check.md:92-93` — `sort -u -o` の in-place 2 行の除去（現状 3b ループの入力 claimed.list は sort -u 済みで、追記順が入力順を保つため両出力は既にソート済み・重複なし＝厳密には no-op） → **除外（温存が妥当）**。この 2 行は「後段 comm の sorted 前提を、ループ実装の変更に依存せず保証する」防御的正規化であり、除去は将来編集（例: 3b に分類を追加して出力順が乱れる）で PHANTOM 照合を静かに壊す退行リスクを買うだけで利得がない。
- verify 結果の JSONL / 機械可読フォーマット出力の先行追加（hook Stage A/B・W3/W4 への布石として） → **除外（スコープ逸脱）**。決定1=(A) は初回実装点のみの最小配線であり、メトリクス schema（`subagent-metrics.jsonl` の `{ts, agent_id, ...}`）は設計 SSOT 上 W3 で hook と同時に設計される項目。今ここで独自 schema を発明すると W3 で二重定義になる。現行テンプレートの固定 key-value 行（L-1 で強化）が grep/jq 可読なので布石としては十分。
- `comm` パイプラインの簡素化（呼び出し元の検討依頼） → **除外（現状が最小）**。`comm -13`（delta = post − pre）/ `comm -23`（phantom, undeclared）はいずれも 1 コマンド 1 集合演算で、これ以上の簡素化は `grep -vxFf` 等への置き換えになり、sorted 前提が不要になる代わりに大集合での性能特性と「集合演算である」ことの自己文書性を失う。tmp 変数命名（`p` / `expanded` / `idx`）も doc 内スコープ 10 行以内の慣用名で改名は churn のみ。

---

### メモ

- **将来拡張への構造適合性（呼び出し元の観点5への回答）**: reference は「適用対象 actor」「検証の情報源」「pre-set」「照合規則」「失敗パス」「スキップ条件」が節単位で直交分離されており、7-4/8-2 への配線追加（決定1 の (B) 側）は「適用タイミング節（M-2 で新設提案）に挿入点を 1 行足し、各 SKILL.md から節参照を張る」だけで済む形になっている。構造変更は不要と判断する。
- **reviewer 指摘との重複について**: M-3 / L-4 は review-02-architecture が、L-2 / L-3 は review-02-correctness が「任意・blocking でない」として明示的に本エージェントへ委任 or 参考記載した項目の正式提案化であり、意図的な再掲（重複を恐れず出す方針に従う）。
- **スキル本体への注意**: review-02-correctness の Medium 2 件（3b `~user`・3c cwd 依存）は reference の 21:50 更新で**修正済み**であることを現物確認した。ユーザーゲート提示時に「correctness の残 Medium は対応済み」と添えると再説明の往復を防げる。
