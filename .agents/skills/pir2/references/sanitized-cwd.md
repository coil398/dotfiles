# `~/.ai-runs` の置き場規則と予約手順

この文書は、全 runtime と全 Skill が一時的な実行履歴・作業記録・`handoff.md` を置く共通領域 `~/.ai-runs` の構造と予約手順を定めます。

## ルートの場所と責務

- ルートは `$HOME/.ai-runs`（実ディレクトリ、mode `0700`、symlink 不可）とする。
- 置いてよいものは、消してよい一時的な実行履歴・作業ファイル（計画、レビュー結果、runner 入出力ログ）と、未完了タスクの再開用 `handoff.md` のみに限定する。
- `~/.ai-runs` 直下にファイルを直接置くこと、およびバケットを介さず自由名ディレクトリを作ることを禁止する。
- `~/.ai-runs` 配下に対象リポジトリの clone、丸ごとコピー、ビルドキャッシュ（`.venv`、`node_modules`、`target` 等）を置くことを禁止する。隔離作業ツリーが必要な場合は `git worktree` で `${TMPDIR:-/tmp}` 等に作成し、作業完了時に `git worktree remove` で除去する。対象が常設の作業枠を持つrepository（`git config agent.slotOnly` がtrue）なら、worktreeを作らず枠を借りる。
- 実験観測ログなどの恒久記録は `~/.ai-runs` に置かず、`${XDG_STATE_HOME:-$HOME/.local/state}/ai-workflow/experimental-observations.md` を使う。

## ディレクトリ階層と命名規則（2階層固定）

```text
~/.ai-runs/
  ├── <sanitized_cwd>/                     # 通常作業の project バケット
  │     ├── handoff.md                     # 未完了タスクがある場合のみ（完了時は RUN_DIR/handoff-completed.md へ移動）
  │     └── <YYYYMMDD-HHMMSS>-<slug>/      # 個別 run ディレクトリ（衝突時は末尾 -1, -2 ...）
  └── _bench/                              # ベンチマーク専用バケット
        └── <YYYYMMDD-HHMMSS>-<slug>/      # bench 実行単位ディレクトリ
```

- **project バケット名 (`<sanitized_cwd>`)**: `PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd -P)"` を物理パス解決し、`printf '%s' "$PROJECT_ROOT" | sed 's|[^a-zA-Z0-9]|-|g'` で ASCII 英数字以外をすべて `-` に置換する（例: `-home-user-dotfiles`）。
- **`_bench` バケット**: 正規化式は `_` も `-` に置換するため、正規の `<sanitized_cwd>` に `_` は含まれない。`_bench` を第1階層に置き、通常の project 履歴と保持期間を分離する。
- **run ディレクトリ名 (`<YYYYMMDD-HHMMSS>-<slug>`)**: ローカル時刻 `date +%Y%m%d-%H%M%S` と英小文字・数字・ハイフン最大40文字の `<slug>` をハイフンで繋ぐ（例: `20261116-001530-pir2-clean-ai-runs`）。
- 親から検証済みの `RUN_DIR` や `HANDOFF_PATH` を受け取った場合は、再計算・再予約しない。

## 予約手順

手書きのワンライナーで作成せず、同じ package の [`scripts/reserve-run-dir.sh`](../scripts/reserve-run-dir.sh) を実行して予約する。

```sh
sh <pir2-package>/scripts/reserve-run-dir.sh --cwd <DIR> --slug <SLUG> [--bucket _bench] [--run-root <DIR>]
```

- 必須引数: `--cwd <DIR>`（既存ディレクトリ）、`--slug <SLUG>`（作業内容の短い名前）。
- 任意引数: `--bucket _bench`（ベンチマーク専用バケットを指定）、`--run-root <DIR>`（テスト等でのルート上書き。通常は省略し `$HOME/.ai-runs` を使う）。
- スクリプトは `umask 077`（mode `0700`）と排他 `mkdir` で `RUN_DIR` を作成し、`PROJECT_ROOT`・`RUN_ROOT`・`PROJECT_RUN_ROOT`・`RUN_DIR`・`HANDOFF_PATH` を `KEY=VALUE` 形式で標準出力へ返す。

## runner の `WORK_DIR` 規則

`agy`、`codex`、`harness-run`、`colab` などの runner へ `--work-dir` を渡す際は次の規則に従う。

- 親の `RUN_DIR` が既にある場合: `--work-dir "$RUN_DIR"` を渡す（各 runner は `agy-<RUN_ID>-*` 等の prefix 付きで出力するため同居でき、run 単位で管理・掃除される）。
- 親の `RUN_DIR` がない単発呼び出しの場合: `scripts/reserve-run-dir.sh` で `~/.ai-runs/<sanitized_cwd>/<YYYYMMDD-HHMMSS>-<slug>` を予約し、その `RUN_DIR` を `--work-dir` に渡す。同一依頼の継続呼び出しでは同じ `RUN_DIR` を再利用する。

## 安全境界と掃除

- `RUN_ROOT`、`PROJECT_RUN_ROOT`、`RUN_DIR` は実体ディレクトリとし、symlink を辿って別の保存先へ書き込まない。
- `RUN_ROOT`、`PROJECT_RUN_ROOT`、`RUN_DIR` は `PROJECT_ROOT` の外側にあること。
- `HANDOFF_PATH` を読み書きする前に、実体の通常ファイル（symlink 不可）であることを確認する。
- 同じ対象について異なる規則で作られた既存ディレクトリが並存する場合、自動マージ・上書き・削除はしない。
- 掃除は `bin/clean-ai-runs` が行う（通常バケット 14日/20件、`_bench` 3日/5件、直近6時間以内の active run と `handoff.md` を保護）。
