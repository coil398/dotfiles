## 実装完了レポート

### 変更ファイル一覧
- `.claude/skills/pir2/references/deterministic-completion-check.md` — must-fix #1: 実集合（pre-set/post-set 両方）に `git diff --cached --name-only`（staged 変更）を union で追加し「staged は対象外」の記述を撤回。追加理由（R1 是正）と副作用（pre-existing-staged への虚偽申告が新規 fail-open FN として R6 に合流すること）を明記。must-fix #3: 「## 既知の残存限界（R1〜R13）」節を新設し、position-3.md の台帳を方向つき（fail-open/fail-closed）・頻度・3層割付・理由で完全転記し、fable 追加の (g)(h)(i) と「6-3 は completion verifier でなく phantom-claim floor」の再ラベルを明記。冒頭の機械検証 blockquote のフィクスチャ数を「6シナリオ」→「8シナリオ」に更新
- `.claude/skills/pir2/references/verify-deterministic-check.sh` — must-fix #1 の DoD 強化: フィクスチャを2本追加（(a) staged申告 = `git add` 後に申告した変更が PHANTOM 化しないこと、(b) pre-existing-staged = pir2 開始前から staged 済みのファイルが delta に誤混入しないこと＝pre/post 対称性）。ヘッダコメント・最終サマリ echo の「6シナリオ」記述を「8シナリオ」に更新
- `.claude/skills/pir2/references/experimental.md` — must-fix #2: `## Experiment: pir2-deterministic-completion-check` を既存実験と同一書式で新規追加（Status: Active / Started: 2026-07-04 / Hypothesis / Implementation / Quality Guardrails / Metrics(a)(b)(c) / Adoption Criteria / Rejection・Rollback トリガ / Evidence Summary / Observation Log）
- `.claude/agents/implementer.md` — 補助対応: ガイドライン節に「申告した変更ファイルを自分で `git add`（stage）しないこと（規律。実害は union 化により無いが規律として明記）」を1行追加

### 実装概要
深レビュー（Fable5・position-3.md）が指摘したコミット前 must-fix 3点を実装した。(1) 実集合の pre/post 両側に `git diff --cached --name-only` を union 追加し、`git add` した瞬間に正当な申告が PHANTOM 化する fail-closed FP（R1/R4）を塞ぐと同時に、この修正が pre-existing-staged への虚偽申告を新規 fail-open FN（R6 合流）に転換する副作用を明記した。フィクスチャを2本追加し `verify-deterministic-check.sh` の DoD に含めた。(2) `experimental.md` に 6-3 を Active 実験として登録し、観測項目 (a)(b)(c) と rollback トリガ（観測窓10run・FP比率50%超で hard-fail→warn 降格検討）を明記した。(3) `deterministic-completion-check.md` に R1〜R13 の残存限界台帳と (g)(h)(i) の追加注記、および「6-3 は phantom-claim floor（file-set 存在の1次元のみ検証）」の再ラベルを明記した。

### 注意点・未解決事項
- `verify-deterministic-check.sh`（8フィクスチャ）と `verify-sanitized-cwd.sh` を実行し、いずれも全 PASS を確認済み（"OK: 8 fixture scenarios ... all matched expected判定" / "OK: 10 SKILL.md files all use the SSOT sanitize regex"）。`shellcheck` も警告0件。
- `git diff --name-only HEAD` および `git status --porcelain` で全変更ファイルを確認し、今回のタスクで編集したのは指定4ファイル（`deterministic-completion-check.md` / `verify-deterministic-check.sh` / `experimental.md` / `implementer.md`）のみであることを確認した。他に表示される差分（`.claude/settings.json`, `CLAUDE.md`, `.claude/skills/epic/**` 等）は本 run の先行ラウンド（W0/epic 関連）由来の既存差分であり、本タスクでは一切触れていない。
- `experimental.md` の rollback トリガの数値（観測窓10 run・FP比率50%超）はプロンプトが "N" とプレースホルダで示していた箇所を、既存の他実験の Adoption/Rejection Criteria の書きぶり（「3回以上」等の具体的閾値を明記する慣例）に倣い、保守的な具体値として設定した。ユーザー判断で調整の余地がある旨をここに明記する。
- must-fix #1 は「偽陰性ゼロ」ではなく「fail-closed FP を fail-open FN（pre-existing-staged・R6合流）に転換する」ものであることを、`deterministic-completion-check.md` 本文とフィクスチャコメントの両方で正確に記述した（fable の訂正1を反映）。
