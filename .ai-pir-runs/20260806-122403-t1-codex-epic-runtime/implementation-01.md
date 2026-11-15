# 実装完了レポート

## 変更ファイル

- `.codex/skills/epic/SKILL.md` — Codex native epic runtime 契約を再設計。

## 実装概要

- Sol をユーザー対話、判断、計画、DAG、完了要件、実測、最終判定の常駐責任者にした。
- Codex collaboration API、安定 task name、最小 `fork_turns`、利用可能 slot 判定、独立 wave を契約化した。
- 具体作業は全 workflow 共通 worker-routing へ渡す接続点に留め、現行 fallback の核を `.codex/skills/luna-max-worker/**` とした。
- worker の自己申告と Sol acceptance、独立 reviewer / tester の品質判定を分離した。
- 存在しない下位スキル、別 runtime のツール記述、ホーム配下 shared overlay 参照を除去した。

## 注意点・未解決事項

- epic 固有ではない共通 worker-routing 契約の実体化は後続タスク。epic 側の入出力接続点は定義済み。
- 現行 fallback は `luna-max-worker` の契約に従い、判断不足や runner 失敗は Sol へ戻す。
