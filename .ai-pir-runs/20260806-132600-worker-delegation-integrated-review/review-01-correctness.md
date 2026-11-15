VERDICT: PASS

### 担当 role
correctness

### 判断根拠
- バグ・正確性: `RUN_DIR` に `plan.md` / `implementation-*.md` は存在しなかったため、呼び出し元指定どおり `git diff HEAD` と untracked の `.codex/skills/worker-delegation/**` / `.codex/skills/pir2/references/worker-observability.md` をレビュー境界とした。`.codex/skills/worker-delegation/scripts/run-worker.sh:54-69` は `--actor luna|terra` だけを受け付け、未知 actor は exit 2 で停止する。`.codex/skills/worker-delegation/scripts/run-worker.sh:71-88` は `--cwd`、task、requirements、output、`- R<number>:` 要件、既存 output の検証を Codex 起動前に行う。`.codex/skills/worker-delegation/scripts/run-worker.sh:114-122` は選択済み actor に対応する固定 model で `codex exec` を呼び、`codex exec --help` でも `-o/--output-last-message` と stdin `-` が有効な CLI 仕様であることを確認した。`sh -n .codex/skills/worker-delegation/scripts/run-worker.sh`、`bash -n etc/test-codex-contracts.sh`、`.codex/skills/worker-delegation/scripts/run-worker.sh --help` は成功。不正 actor と必須引数不足は期待どおり exit 2 で停止した。
- パフォーマンス: 変更は workflow 文書、runner、契約テストであり、実行時のデータ処理・DB クエリ・ループ処理は追加されていない。runner の追加処理は引数検証、短い prompt 生成、単一 `codex exec` 起動に限定され、旧 `run-luna-max.sh` と同等の定数時間処理に actor 分岐を追加しただけである。`etc/test-codex-contracts.sh:68-77` の全ファイル grep は契約テスト専用で通常 workflow 実行経路ではないため、ユーザー操作時の性能退行には該当しない。
- リグレッション: 旧 `.codex/skills/luna-max-worker/scripts/run-luna-max.sh` と新 `.codex/skills/worker-delegation/scripts/run-worker.sh` を比較し、既存の `--cwd`、`--task-file`、`--requirements-file`、`--output-file`、空ファイル拒否、`- R<number>:` 要件、既存 output 拒否、`workspace-write`、`model_reasoning_effort="max"`、Sol acceptance 非依存の説明は維持されている。新仕様として `--actor luna|terra` が追加され、`.codex/skills/worker-delegation/SKILL.md:13-28`、`.codex/skills/pir2/SKILL.md:263-271`、`AI-WORKFLOW-SPEC.md:81-106` で Luna 既定、実測時のみ Terra、Terra 後のみ Sol 直実行、自動 fallback 禁止、reviewer/tester 独立が一貫して接続されている。`rg -n "luna-max-worker|run-luna-max"` は `etc/test-codex-contracts.sh` 自身を除いてヒットなし。`git diff --check HEAD` も問題なし。

### 良好点
- runner が actor を `luna|terra` の明示入力に限定し、モデル選択を runner 内の単一 case に閉じているため、自動 fallback 経路がコード上に存在しない。
- `.codex/skills/pir2/references/worker-observability.md` は actor attempt、Sol acceptance、reviewer/tester verdict を別 TSV に分離しており、worker 自己申告を acceptance / 品質判定へ混入させない構造になっている。
- `etc/test-codex-contracts.sh` は旧 worker パス不在、旧参照消滅、workflow 接続、brainstorm/pir2async 境界、shared core への worker routing 漏洩、default sync の native overlay 保持を機械的に検査している。

### 次のアクション
なし
