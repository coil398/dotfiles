# PIR² Handoff

最終更新: 2026-07-04 / run: 20260703-201858-pir2-step-6-3-deterministic-verify

## タスク
pir2 に新ステップ「6-3: 決定論的完了検証」を追加し、pir2codex の既存 6-1 git diff 検証も共通 reference 化する（申告変更ファイル vs 実 git delta の集合照合で捏造を hard fail）。

## 背景・決定事項
- 決定1=(A) 配線点 6-1 のみ / 決定2=(B) pir2codex 共通化 / 決定3=(A) implementer.md に NO_OP マーカー。
- 機構の設計 SSOT: docs/deepthink/20260703-190750-Fable5.md §1-3/§1-4。プラン: 本 run の plan.md（付録A に共通 reference 全文ドラフト）。

## 残 TODO
- [x] 1. references/deterministic-completion-check.md 新規 Write（付録A 逐語）<!-- done: 2026-07-03 -->
- [x] 2. pir2 SKILL.md step6 に PHANTOM_RETRY_COUNT 初期化<!-- done: 2026-07-03 -->
- [x] 3. pir2 SKILL.md 6-1 pre-set 記録指示<!-- done: 2026-07-03 -->
- [x] 4. pir2 SKILL.md 6-3 挿入<!-- done: 2026-07-03 -->
- [x] 5. next-steps-queue.md に 6-3 checkbox<!-- done: 2026-07-03 -->
- [x] 6. implementation-delegation.md 相互参照ノート<!-- done: 2026-07-03 -->
- [x] 7. pir2 SKILL.md step12 検証結果ブロック<!-- done: 2026-07-03 -->
- [x] 8. implementer.md に NO_OP_JUSTIFIED マーカー（付録B）<!-- done: 2026-07-03 -->
- [x] 9. pir2codex SKILL.md step6 に PHANTOM_RETRY_COUNT 初期化<!-- done: 2026-07-03 -->
- [x] 10. pir2codex SKILL.md 6-1 pre-set 記録指示<!-- done: 2026-07-03 -->
- [x] 11. pir2codex SKILL.md 6-1 返り後処理 bullet1/bullet3 を共通 reference 参照に置換<!-- done: 2026-07-03 -->
- [x] 12. pir2codex SKILL.md step12 検証結果ブロック<!-- done: 2026-07-03 -->
- [ ] 13. `.codex/agents/implementer.toml` の PostToolUse hook 自動再生成が実装ステップ8（implementer.md 編集）後に発火していないことを確認（mtime 未更新・`git diff` なし・`NO_OP_JUSTIFIED` 文字列が toml に未反映）。原因調査（サブエージェント環境で PostToolUse hook が発火しない設計なのか、単純な未実行か）または手動 `bash etc/sync-codex.sh` 実行が必要。
- [x] 14. refactor-proposals.md L-1: verify-{IMPL_INDEX}.md テンプレートに `PRE_IMPL_INDEX` / CLAIMED 情報源 / `PHANTOM_RETRY_COUNT` / untrackable 件数 / untrackable-missing 件数の行を追加<!-- done: 2026-07-03 -->
- [x] 15. refactor-proposals.md L-2: deterministic-completion-check.md 3b の `case "$p" in /*|~*)` を `/*|"~"*)` にクォート統一<!-- done: 2026-07-03 -->
- [x] 16. refactor-proposals.md L-3: FIX-C（CLAIMED累積撤回）後の食い違いコメント確認 → 該当コメントは現存せず既に解消済みであることを確認（no-op）<!-- done: 2026-07-03 -->
- [x] 17. refactor-proposals.md L-4: pir2 SKILL.md 6-1 の pre-set 記録指示を pir2codex と対称の独立 h4 見出しに昇格<!-- done: 2026-07-03 -->
- [x] 18. refactor-proposals.md M-4: `references/verify-deterministic-check.sh` を新設（```bash ブロックの trim完全一致抽出 + `bash -n` 構文検証 + PHANTOM/UNDECLARED/NO_OP/非ASCII名/フェンス内例示の5フィクスチャ、scratch git repo・`find -delete` 後始末）。reference 冒頭に機械検証の案内を追記<!-- done: 2026-07-03 -->
- [x] 19. sanitized_cwd の epic 登録: `verify-sanitized-cwd.sh` の `SKILL_FILES` に `~/.claude/skills/epic/SKILL.md` を追加（9→10 ファイル）、`sanitized-cwd.md` の consumer 表・件数表記を同期更新<!-- done: 2026-07-03 -->
- [x] 20. Fable5 最終レビュー（review-04-fable.md）Medium M-A + Low 5件対応: (a) pre-set/post-set の `--ignore-submodules=all`→`dirty` 化（submodule pointer bump を post に復元）、(b) 3b の `check-ignore` を終了コード3分岐（0=untrackable/1=trackable/128等=untrackable）に変更しサブモジュール内パス申告を検証不能へ正しく分類、(c) deterministic-completion-check.md の submodule 記述を実挙動に一致させる、(d) 3c の `case` クォート記法を `"~"*` に統一、(e) 手順0 ERROR文とblockquoteに「pre-set再記録+実装actor再実行の両方が必要」を明記、(f) awkフェンス除去の入れ子/4バッククォートフェンス既知limitationをコメント明記、(g) `verify-deterministic-check.sh` に実行ビット付与、(h) 同スクリプトに submodule フィクスチャ（pointer bump=PASS / 内部パス申告=untrackable）を追加。`verify-deterministic-check.sh`（6シナリオ）・`verify-sanitized-cwd.sh`・`shellcheck` すべて実行し PASS/0件を確認済み<!-- done: 2026-07-04 -->

## 既知の問題 / 要確認
- pir2codex 実集合定義が HEAD 比較 → unstaged+untracked に変わる（untracked 検知が増える＝strictly better、staged は Codex 非 stage 前提で対象外）。reviewer に申し送り済み。
- implementer.md 編集は sync SSOT → `.codex/agents/implementer.toml` 自動再生成（手編集しない）想定だったが、本 run では再生成が観測できなかった（残 TODO 13 参照）。

## 関連 artifact
- 最新 plan: .ai-pir-runs/20260703-201858-pir2-step-6-3-deterministic-verify/plan.md
