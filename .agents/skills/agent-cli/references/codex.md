# Codex CLI (`codex`)

## 非対話実行

```bash
codex exec -C /path/to/repo 'task'                          # ワンショット（alias: e）
codex exec -m <model> -s workspace-write -C /repo 'task'
codex exec --skip-git-repo-check 'task'                     # git repo 外
echo 'task' | codex exec -C /repo -                         # stdin から prompt
codex exec resume <thread_id> 'follow-up'                   # 同一 thread に継続
codex exec resume --last 'follow-up'
codex review                                                # 非対話コードレビュー
```

- stdin がパイプなら読み込む。prompt 引数と併用すると `<stdin>` ブロックとして追記される
- `-C/--cd`: 作業 root。`-s/--sandbox`: `read-only` / `workspace-write` /
  `danger-full-access`。`--add-dir` で書き込み範囲追加。`--worktree` で隔離
- `--ephemeral`: セッションをディスクに残さない（使い捨て委譲に向く）

## 出力を機械処理する

- `--json`: stdout が **JSONL イベントストリーム**になる
- `-o` / `--output-last-message <FILE>`: 最終メッセージをファイルへ
- `--output-schema <FILE>`: 最終応答の JSON Schema を強制（構造化委譲に最適）
- `--color never`: パイプ時は自動で off になるが明示も可

## 設定のその場上書き

```bash
codex exec -c model='"gpt-6.1-sol"' -c model_reasoning_effort='"medium"' -c approval_policy='"never"' 'task'
```

`-c key=value` で `~/.codex/config.toml` の任意キーを dotted path で上書き。
hermetic にしたい場合:

- `--ignore-user-config`: `config.toml` を読まない（auth は `CODEX_HOME` を使う）
- `--ignore-rules`: execpolicy `.rules` を読まない
- `--strict-config`: 不明フィールドで落ちる

## resume のcwd

**`codex exec resume` には `-s` / `-C` が無い**。resume は元 thread の
sandbox / cwd を引き継ぎます。

```bash
codex exec resume <id> -c sandbox_mode='"workspace-write"' 'follow-up'
```

この例のように、resume は元threadの cwd を使います。別のcwdを指定する引数はありません。`-s` を付けると
パースエラーになる。

## 完了通知と終了状態

- background実行が利用できる呼出元では完了通知を待つ。通知後に最終応答と成果物を確認し、継続的なpollはしない
- 終了分類: exit code 非 0 = 基本 retryable ではない、signal 終了・
  wall-clock timeout は retryable、cancel は非 retryable
- temp dir 配下だと `WARNING: ... could not create PATH aliases` が出る
  ことがある（処理自体は続行）
- レート上限（~80%）に達すると **無音で終了する**ケースが観測されている。
  出力が空なら rate limit を疑う
- `codex exec` / `resume` を使う。

## 診断・管理

```bash
codex doctor           # 環境・認証・runtime 診断
codex login status     # 認証状態
codex cloud list --json # Codex Cloud のタスク一覧
codex apply            # 直近の diff を git apply
codex exec --help      # フラグの正本（version で変わる）
```

定型の codex 委譲フロー（runner が thread_id と完了を管理する方式）は
`codex` Skill が正本。ここは CLI 単体の勘所だけ。
