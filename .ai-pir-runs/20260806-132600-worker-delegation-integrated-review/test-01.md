VERDICT: PASS

### テスト実行結果
- `git diff --check`: PASS。出力なし、whitespace error なし。
- `bash -n etc/sync-codex.sh etc/seed-codex-overlay.sh etc/test-codex-contracts.sh`: PASS。出力なし、3 スクリプトとも bash 構文エラーなし。
- `sh -n .codex/skills/worker-delegation/scripts/run-worker.sh`: PASS。出力なし、POSIX sh 構文エラーなし。
- `.codex/skills/worker-delegation/scripts/run-worker.sh --help`: PASS。終了コード 0。実データ: `Usage: .codex/skills/worker-delegation/scripts/run-worker.sh --actor luna|terra --cwd DIR --task-file FILE --requirements-file FILE --output-file FILE`
- `.codex/skills/worker-delegation/scripts/run-worker.sh --bogus`: PASS。終了コード 2。実データ: `Unknown argument: --bogus` と usage を返した。
- `.codex/skills/worker-delegation/scripts/run-worker.sh --actor luna`: PASS。終了コード 2。実データ: `ERROR: --cwd is required`
- `.codex/skills/worker-delegation/scripts/run-worker.sh --actor bad --cwd . --task-file .codex/skills/worker-delegation/SKILL.md --requirements-file .codex/skills/worker-delegation/SKILL.md --output-file /tmp/worker-out.md`: PASS。終了コード 2。実データ: `ERROR: unknown actor: bad`
- `run-worker.sh` の invalid requirements 確認: PASS。空でない task と `- R<number>:` を含まない requirements を渡し、終了コード 2。実データ: `ERROR: requirements must contain at least one "- R<number>:" criterion`
- `python3` + `tomllib` parse: PASS。`.codex/config.base.toml`、`.codex/config.toml`、`.codex/agents/epic-planner.toml` はすべて parse 成功。実データ: `OK .codex/config.base.toml` / `OK .codex/config.toml` / `OK .codex/agents/epic-planner.toml`
- `bash etc/test-codex-contracts.sh` sandbox 内: FAIL 相当だが権限ブロッカーとして切り分け。72 passed, 1 failed。失敗箇所は `default sync failed: mktemp: mkstemp failed on /Users/kawasetakumi/dotfiles/.codex/config.toml.tmp.7SmzJ0: Operation not permitted`
- `touch .codex/.codex-write-probe`: 権限確認。終了コード 1。実データ: `touch: .codex/.codex-write-probe: Operation not permitted`
- `bash etc/test-codex-contracts.sh` 権限外再実行: PASS。73 passed, 0 failed。`default sync completed`、`default sync preserves Codex native overlays`、`seed does not overwrite explorer.toml`、`seed does not overwrite worker-delegation runner`、`check-shared-drift clean` を確認。

### 動作確認結果
- runner help: 正常系として usage が表示され終了コード 0 になること → 期待通り。
- runner 未知引数: `--bogus` が拒否され usage が stderr に表示され終了コード 2 になること → 期待通り。
- runner 必須引数不足: `--actor luna` のみでは `--cwd is required` で終了コード 2 になること → 期待通り。
- runner 不明 actor: `--actor bad` が `ERROR: unknown actor: bad` で終了コード 2 になること → 期待通り。
- runner requirements 形式不備: `- R<number>:` を含まない requirements が拒否され終了コード 2 になること → 期待通り。
- old package absence: `find .codex/skills -maxdepth 2 -name '*luna-max-worker*' -o -path '.codex/skills/luna-max-worker*'` は出力なし。旧 `.codex/skills/luna-max-worker` 実体は存在しない。
- stale reference absence: 契約テストで `no stale luna-max-worker references` を確認。`etc/test-codex-contracts.sh` と `.ai-pir-runs/**` 以外に旧 worker 参照なし。
- key workflow markers: `debug` / `ir` / `pir2` / `writing-plan` は `worker-delegation`、`scripts/run-worker.sh`、`--actor luna` を含む。`epic` は `.codex/skills/worker-delegation/SKILL.md` を SSOT として参照する。
- non-connected workflows: `brainstorm` は `worker-delegation` へ直接接続せず `scripts/run-worker.sh` を含まない。`pir2async` は実験用 workflow として記述され、`scripts/run-worker.sh` を含まない。
- model routing markers: runner は `luna)` -> `model="gpt-5.6-luna"`、`terra)` -> `model="gpt-5.6-terra"` を持つ。`fallback|フォールバック` の自動 fallback 実装は契約テストで不在確認済み。
- shared core leakage: 契約テストで `.agents/**` への `worker-delegation|run-worker.sh` 漏れなし、`AGENTS.md` に `gpt-5.6-luna` / `gpt-5.6-terra` なしを確認。
- git status: 検証後も既存の未コミット変更は残存。新規テストレポート以外のクリーンアップや DB データ操作は未実施。

### IaC 静的検証
- 変更ファイル一覧に `deploy/*.bicep`、`*.tf`、CloudFormation/k8s manifest、`Dockerfile` は見当たらないため対象外。

### テストデータ
- DB/API を使う実装ではないため投入なし。
- 一時ファイルは `/tmp/worker-runner-invalid.*` に作成して runner invalid requirements 確認にのみ使用。DB データ削除・クリーンアップは未実施。

### 注意
- `{RUN_DIR}/plan.md` と `{RUN_DIR}/implementation-*.md` は存在しなかったため、呼び出し元の手動統合テスト指示と `git status` / `git diff` から検証スコープを補完した。
- sandbox 内では `.codex` 配下への新規ファイル作成が拒否されたため、契約テスト本体は権限外再実行で最終判定した。権限外では同一テストが 73 passed, 0 failed で通過した。

### 次のアクション
なし。
