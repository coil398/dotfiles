# harness-run bench

実装委譲の既定候補を比べるベンチです。同じ課題を `codex-run.py`（ベースライン）と `harness-run.py`（pi / omp / opencode / dsh）で実行し、成否・時間・リクエスト数・入力量を揃えた形で集計します。標準ライブラリのみで動きます。

## 構成

- `fixtures/inventory/`: 単一ファイルの修正課題（`inventory.py`、テスト `test_inventory.py`）。
- `fixtures/ledger/`: 複数ファイルのパッケージ修正課題（`ledger/` のみ変更可、テスト `tests/test_ledger.py`）。
- `fixtures/scheduler/`: 依存関係・資源制約・再試行を扱うジョブスケジューラの修正課題（`scheduler/` のみ変更可、テスト `tests/test_scheduler.py`）。
- 各fixtureの `task.md` がそのまま prompt になります。試行ごとにfixtureを一時dirへコピーして `git init` し、`task.md` はworkspaceに入れません。
- 試行後、benchが自分でテスト（`uv run -q --no-project --with pytest python -m pytest -q`）を実行して判定します。担当の自己申告は使いません。

## 実行例

`--config` は `harness:model:effort[:flags]` です。flags はカンマ区切りで `minimal`（`--minimal-context`）と `dsh-patch=PATH`（`--dsh-patch`）が使えます。

```bash
B=/home/coil398/dotfiles/.agents/skills/harness-run/bench/bench.py
OUT=/tmp/bench-out   # 既存の results.jsonl があると拒否されます

# Codex baseline
python3 $B --config codex:gpt-6-luna:medium --repeat 3 --out $OUT
# Pi (Codexサブスク) と最小context
python3 $B --config pi:openai-codex/gpt-6-luna:medium --config pi:openai-codex/gpt-6-luna:medium:minimal --repeat 3 --out $OUT
# omp / opencode
python3 $B --config omp:openai-codex/gpt-6-luna:medium --config opencode:openai/gpt-6.1-sol:medium --out $OUT
# dsh + OpenCode Go の DeepSeek（overlayでprovider/modelを指定）
python3 $B --config dsh:opencode-go/deepseek-v4.1-flash:high:dsh-patch=/path/to/overlay.yml --tasks ledger --out $OUT
```

他に `--tasks inventory,ledger`（既定は全課題）、`--timeout SEC`（試行ごと、既定900）があります。試行は直列に実行します（時間の比較を乱さないため）。

## 結果の読み方

出力先に `results.jsonl`（試行ごと）、`summary.md`（構成×課題の表）、`trials/`（workspaceとrunner成果物）が作られます。

- 成功: runnerが `completed`、benchのテストが通る、テストを触っていない、許可path外を変更していない、の全てを満たした試行です。
- 時間・req・入力/req・総入力・uncached・cache率・出力は skipped を除く試行の中央値です。
- 入力は `total_input`（非cache + cache read + cache write）、`input_uncached`、`cache_read` に正規化します。Codexの `input_tokens` は cached 込み、pi/omp/opencode/dsh は非cache分のみを返すため、runner側で揃えた値を使います。reasoningは出力に含まれます。
- Codexのreq数は `thread/tokenUsage/updated` イベントの回数です。
- `auth_not_ready` と runner 不在は失敗ではなく skipped として表示します。`invocation_error` は設定ミスとして失敗に数えます。
- costはカタログ単価による推定でサブスクの実課金ではないため、表に含めません。

## 注意

- benchが試行を打ち切るときは、runnerへSIGTERMを送って子harnessのprocess groupを止めさせ、残りをSIGKILLします。

- 課題は小さく、モデル間の性能差は出にくいです。差を見るなら `ledger` を使い、`--repeat` を3回以上にして中央値と失敗の内訳を見ます。
- 認証が前提です（例: `pi auth check --provider openai-codex`）。Codexサブスク構成はrunner側で `OPENAI_API_KEY` を外し、未ログインなら skipped になります。dshは `apiKeyEnv` に対応する環境変数（`opencode-go` は `OPENCODE_GO_API_KEY`）が必要で、未設定なら dsh の `MISSING_CREDENTIAL` により skipped になります。
- 実行は実際にモデルを呼びます。Codex枠やAPI枠を消費するため、`--repeat` と構成数を控えめに始めてください。
