## 実装完了レポート

### 変更ファイル一覧
- `.claude/skills/pir2/references/deterministic-completion-check.md` — L-1（`verify-{IMPL_INDEX}.md` テンプレートに `PRE_IMPL_INDEX` / CLAIMED 情報源 / `PHANTOM_RETRY_COUNT` / untrackable 件数 / untrackable-missing 件数の行を追加）、L-2（3b の `case "$p" in /*|~*)` を `/*|"~"*)` にクォート統一）、M-4（reference 冒頭に機械検証スクリプトへの案内を追記）
- `.claude/skills/pir2/SKILL.md` — L-4（6-1 の pre-set 記録指示を、既存の blockquote 形式から pir2codex `#### wrapper 起動前の pre-set 記録（決定論的完了検証 6-3 用・必須）` と対称の独立 h4 見出し `#### implementer 起動前の pre-set 記録（決定論的完了検証 6-3 用・必須）` に昇格）
- `.claude/skills/pir2/references/verify-deterministic-check.sh`（新規） — M-4。`deterministic-completion-check.md` 内の全 ```bash ブロックを「行を trim して完全一致」で抽出し `bash -n` 構文検証、加えて mktemp -d の scratch git repo で PHANTOM / UNDECLARED / NO_OP / 非ASCIIファイル名 / フェンス内例示の5フィクスチャを実行して期待判定と一致するか assert する。後始末は `trap ... EXIT` + `find -mindepth 1 -delete`（`rm -rf` 不使用）
- `.claude/skills/pir2/references/verify-sanitized-cwd.sh` — sanitized_cwd の epic 登録。`SKILL_FILES` 配列に `${HOME}/.claude/skills/epic/SKILL.md` を追加し、ヘッダコメントを「PIR² 系 9 SKILL.md」→「10 SKILL.md」に更新
- `.claude/skills/pir2/references/sanitized-cwd.md` — sanitized_cwd の epic 登録。冒頭のスキル列挙・consumer 表（pwd 系の採用スキル欄）・参照側ファイル一覧（9→10 ファイル、epic を #10 として追加）・更新手順内の件数表記・検証スクリプト節の件数表記・成功時出力例をすべて 9→10 に同期更新
- `.ai-pir-runs/handoff.md` — 完了した項目14〜19として今回の refactor 対応（L-1/L-2/L-3/L-4/M-4/epic 登録）を `[x]` 追記（gitignore 対象のため `git diff` には現れない）
- `~/.claude/projects/-Users-kawasetakumi-dotfiles/memory/pir_implementer_log.md` — 今回の気づき（md 内 fenced bash 抽出の落とし穴と fixture 設計の教訓）を追記

### 実装概要
`{RUN_DIR}/refactor-proposals.md` の L-1〜L-4・M-4、および保留していた sanitized_cwd の epic 登録をすべて実装した。L-1/L-2 は `deterministic-completion-check.md` の記述強化（検証結果テンプレートへのメタ情報追加、クォート表記統一）。L-3 は事前調査の結果、指摘対象の「複数ラウンド読む」旨の食い違いコメントが既に FIX-C で解消済みで現存しないことを確認したため無編集（詳細は下記）。L-4 は pir2/SKILL.md の pre-set 記録指示を pir2codex 側と対称な見出し構造に統一した。M-4 は新規スクリプト `verify-deterministic-check.sh` を作成し、reference 内の bash 3 ブロックを「フェンス行を trim して完全一致させる」方式で正しく抽出（`awk '/^```/{c=!c;next} !c'` のような埋め込み ``` を誤って閉じフェンスと誤認する落とし穴を回避）した上で構文検証 + 5シナリオの E2E フィクスチャを実装し、実行して全て PASS することを確認した。epic の sanitized_cwd 登録も verify-sanitized-cwd.sh / sanitized-cwd.md の両方で完了し、検証スクリプトで 10 ファイル全 OK を確認した。

### 注意点・未解決事項

- **L-3 は no-op**: refactor-proposals.md L-3 が指摘する「CLAIMED 抽出コメントの『通常は同じファイルを1回読むだけ』という記述と、実装の `for idx in PRE_IMPL_INDEX IMPL_INDEX` ループが2回読んでいる実態との食い違い」は、reference の現行版（review-02-correctness 後の FIX-C=CLAIMED累積の撤回を経た版）では該当コメントも該当ループも既に存在しない（CLAIMED 抽出は `for f in "$RUN_DIR"/implementation-${IMPL_INDEX}*.md` の単一 glob のみで、`PRE_IMPL_INDEX` を使った二重ループは無い）。`grep -n "1回\|２回\|2 回\|2回"` で該当コメントが存在しないことを確認済み。プランに書かれた対象がこのラウンド開始時点で既に解消されていたための正当な no-op であり、対象箇所を編集していない。
- **M-4 のフィクスチャは reference のブロック構成（```bash が正確に3個・pre-set/post-set/NO_OP の順）に依存する**設計とした（コスト/リスク項目(d)で明示されていた前提脆弱性どおり）。ブロック数が3以外だった場合はフィクスチャを安全にスキップし警告を出す実装にしてあるが、reference を大改編する際はスクリプト側も追従修正が必要（`verify-sanitized-cwd.sh` と同種の前提）。
- **フィクスチャの実効性を手動で検証済み**: 素朴な抽出（行内のどこかに ``` があれば境界とみなす方式）に一時的に差し替えて実行し、実際に block 3 が `bash -n` の構文エラー（`unexpected end of file`）で検出されることを確認した上で正式な「trim完全一致」方式に戻した（scratchpad 上の使い捨てコピーで検証、リポジトリには反映していない）。
- **M-2 / M-3（reviewer 委任分）は今回のスコープ外**であり意図的に触れていない。両方とも現行 reference には未反映（M-2 の「適用タイミング」節は実は別ラウンドで既に反映済みだったが、これは本ラウンドの作業ではなく事前確認で判明した既存状態）。M-3（3c の `test -f` 残存限界コメント）は未反映のまま。呼び出し元の指示が L-1〜L-4・M-4 に限定されていたため対応していない。
- `verify-deterministic-check.sh` は shellcheck clean（`bash --version` が macOS既定の3.2系であることを確認し、`mapfile`/`readarray` 等の bash4+ 専用機能は使わず `while read` ループのみで実装した）。
