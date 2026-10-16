---
name: wsl-windows
description: >-
  WSLからWindows側のファイル・プロセス・Git・CLIを操作するときの手順。
  対象やコマンドがWindows側の環境に関わる作業で使う。
---

# WSL ↔ Windows

Linux 側のコマンドを Windows パスへそのまま投げない。先にホスト層を判定する。

## いつ読むか

次のいずれかならこの Skill を適用する。毎回の確認質問は不要。

- cwd または対象 path が `/mnt/c` / `/mnt/d` / `C:\` を含む
- `git` / `tasklist` / `powershell.exe` / Windows 上の CLI を作業ツリーに対して使う
- Unity CLI（`unity open` / `unity status` / `unity command` / Editor が死んだ・応答しない）
- 「Windows 側を操作」「WSL からホストのプロセス」などホスト横断の依頼

プロジェクトに操作用 wrapper がある場合は **その wrapper が正**。wrapper が無い、または wrapper が公式 CLI に委譲しているときは、下の Unity CLI 手順を使う。

## ホスト判定

```bash
grep -qiE '(microsoft|wsl)' /proc/version
```

真なら以降は WSL。macOS / 素の Linux の手順をそのまま使わない。

## Git

`/mnt/c/...` 配下のリポジトリに **Linux `git` を使わない**。status / fetch / pull が NTFS で数分ハングする。

```bash
GIT="/mnt/c/Program Files/Git/cmd/git.exe"
"$GIT" -C 'C:\Users\<Name>\Documents\<repo>' status -sb
"$GIT" -C 'C:\Users\<Name>\Documents\<repo>' fetch --prune origin
"$GIT" -C 'C:\Users\<Name>\Documents\<repo>' pull --ff-only
```

- `-C` には **Windows パス**を渡す（`C:\...`）。`/mnt/c/...` を git.exe に渡さない
- ハングしたら待たずに打ち切る。同じ Linux git を再試行しない
- 同期の工程（保全 commit / 競合 / push）は `git-sync` の範囲。ここは **Windows 上でどの git を使うか**だけ

非TTY の `git merge --continue` が Vim の入力待ちになる場合、`--continue --no-edit` は使わない（`--continue` は追加引数を受け付けない）。既存の `WSLENV` を保った per-command bridge で `GIT_EDITOR=true` を Windows `git.exe` に渡し、同じ環境で `git var GIT_EDITOR` が `true` を返すことを確認してから、対象リポジトリの既存 guard 経由で続行する。global/local Git 設定と hooks は変更せず、後の fresh shell で一時環境が残らず `core.editor` も変更されていないことを確かめる。

## パス

Windows プログラムへ渡す path は `wslpath -w`。表示・ログは `echo` ではなく `printf '%s\n'`。`echo "C:\Users\..."` は `\U` が潰れて `C:sers` になる。

```bash
WIN_PROJECT=$(wslpath -w /mnt/c/Users/Name/Documents/repo)
printf '%s\n' "$WIN_PROJECT"
# C:\Users\Name\Documents\repo
```

逆は `wslpath -u 'C:\Users\Name\Documents\repo'`。変数に入れた path を CLI へ渡すときは `"$WIN_PROJECT"` のまま。中身は正しい。壊れるのは表示だけ、とは限らないのでログ確認も `printf`。

## 共有中の Windows ログ

別プロセスが書き込み中のログを読むとき、`File.ReadAllLines` が sharing violation になる場合は、読み取り専用の `FileStream` を `FileShare.ReadWrite` 明示で開く。必要な event と metadata だけを取り出し、ログ全文や secret を出力しない。

## 実行ファイルのスタブ

`/mnt/c/Users/.../AppData/Local/Microsoft/WindowsApps/*.exe` は **0-byte の App Execution Alias** であることが多い。`command -v` がこれを返しても実体ではない。

使う前に `[ -s "$path" ]` を確認する。空なら却下して実体を探す。`where.exe <name>` の結果から WindowsApps を除外する。`unity doctor` の `check.path-duplicates` が WindowsApps を first に出すのはこの症状。

## PowerShell 5.1 から Windows コマンドを調べる

PowerShell 5.1 の `$ErrorActionPreference = 'Stop'` は、native executable の stderr を `NativeCommandError` として扱い、process exit code を読む前に script を止めることがある。stderr が出たことと native process の exit code が nonzero であることは別に判定する。

- stdout と stderr を別々に保存し、直接 `&` で起動するなら狭い範囲だけ `$ErrorActionPreference = 'Continue'` にして、実行直後に `$LASTEXITCODE` を退避する。前の設定値は `finally` で戻す。
- `Start-Process` を使う場合は `-RedirectStandardOutput` / `-RedirectStandardError` と `-PassThru` を指定し、完了後に返された process の `ExitCode` を読む。`2>&1` で stream を混ぜると stderr と exit code を別々に確認しにくい。
- GUI executable の `--help` が終了しない場合は `Start-Process -PassThru` で起動 PID を記録し、その要求で起動した process だけを対象にする。bounded wait の後も残っていればその PID だけを停止し、起動前から存在した同名 UI process は維持する。process 名だけで一括終了しない。

## Unity CLI

Unity CLIをWSLから操作するときは、詳細な状態判定・起動・待機手順を[Unity CLI reference](references/unity-cli.md)で確認する。プロジェクトに操作用wrapperがある場合はその手順を優先する。

## 待たない

`/mnt/c` 上の `git status`・再帰コピー・全ファイル grep は完了しない前提で上限を付ける。2 分以上動かない同一コマンドは打ち切り、Windows 側ツール（`git.exe` / `rg.exe` / `unity.exe`）へ切り替える。同じ Linux コマンドの再試行はしない。

例外: Unity の **STARTING** 待ちは 10 分まで許す。これは NTFS ハングではなく import / compile 待ち。
