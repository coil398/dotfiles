---
name: wsl-windows
description: >-
  WSL から Windows のファイル・プロセス・Git・Unity CLI を扱うときの実行規則。
  `/mnt/c` 上の Linux git、WindowsApps の 0-byte スタブ、Editor と CLI の取り違え、
  NTFS 越しのハングを防ぐ。Editor の状態（DEAD / STARTING / READY）ごとの対処、
  unity open / status / command を含む。ユーザーが /wsl-windows と入力したら使う。
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

## パス

Windows プログラムへ渡す path は `wslpath -w`。表示・ログは `echo` ではなく `printf '%s\n'`。`echo "C:\Users\..."` は `\U` が潰れて `C:sers` になる。

```bash
WIN_PROJECT=$(wslpath -w /mnt/c/Users/Name/Documents/repo)
printf '%s\n' "$WIN_PROJECT"
# C:\Users\Name\Documents\repo
```

逆は `wslpath -u 'C:\Users\Name\Documents\repo'`。変数に入れた path を CLI へ渡すときは `"$WIN_PROJECT"` のまま。中身は正しい。壊れるのは表示だけ、とは限らないのでログ確認も `printf`。

## 実行ファイルのスタブ

`/mnt/c/Users/.../AppData/Local/Microsoft/WindowsApps/*.exe` は **0-byte の App Execution Alias** であることが多い。`command -v` がこれを返しても実体ではない。

使う前に `[ -s "$path" ]` を確認する。空なら却下して実体を探す。`where.exe <name>` の結果から WindowsApps を除外する。`unity doctor` の `check.path-duplicates` が WindowsApps を first に出すのはこの症状。

## Unity CLI

ここは **Unity CLI**（`unity.exe`）の話。Editor のコマンドライン引数（`-batchmode` / `-quit` / `-executeMethod` を Editor バイナリへ直渡し）とは別物。

インストール済み CLI のコマンド表はバイナリの `--help` が正。知らないサブコマンドは推測せず `"$UNITY" <cmd> --help` を見る。機械処理は `--json`。

### 三層

| 層 | 実体 | 用途 |
|---|---|---|
| CLI | `%LOCALAPPDATA%\Unity\bin\unity.exe` | プロジェクトを開く、接続中 Editor に命令、batch 起動、診断 |
| Editor | Hub 配下 `Editor\Unity.exe` | GUI。CLI の代用にしない。Store alias も不可 |
| プロジェクト wrapper | リポジトリ内のスクリプト | あるなら **そちらが正**。生の CLI / Editor を直叩きしない |

CLI は Editor に話しかけるクライアント。`status` は観察だけで起動しない。起動は `open`。

### バイナリ

```bash
UNITY="/mnt/c/Users/<Name>/AppData/Local/Unity/bin/unity.exe"
[ -s "$UNITY" ] || { printf 'unity CLI missing or 0-byte stub\n'; exit 1; }
```

`command -v unity` / `command -v Unity.exe` を信じない。

### WSL からの呼び方

```bash
WIN_PROJECT=$(wslpath -w /mnt/c/Users/<Name>/Documents/<project>)
UNITY="/mnt/c/Users/<Name>/AppData/Local/Unity/bin/unity.exe"

"$UNITY" --non-interactive --no-banner --version
"$UNITY" --non-interactive --no-banner --json editors running
"$UNITY" --non-interactive --no-banner --json status --project-path "$WIN_PROJECT"
```

- エージェントは `--non-interactive`。path は Windows 形式。`/mnt/c/...` を `--project-path` に渡さない
- cwd が `/mnt/c` のとき `open` / `run` の省略引数（カレントディレクトリ）に頼らない
- `networkingMode=mirrored` の WSL2 では `127.0.0.1` は Windows localhost と同じ。NAT のままなら Editor に届かない

### 観察の順番

信号を 1 本だけで断定しない。この順で取る。

```bash
powershell.exe -NoProfile -Command "Get-Process -Name Unity -ErrorAction SilentlyContinue | Select-Object Id,Path"
"$UNITY" --non-interactive --no-banner --json editors running
"$UNITY" --non-interactive --no-banner --json status --project-path "$WIN_PROJECT"
```

| 信号 | 見ること | 見ないこと |
|---|---|---|
| `Get-Process -Name Unity` | path が `Editor\Unity.exe` か。Hub / CLI は除外 | `tasklist \| grep -i unity \| head`（Hub で埋まる） |
| `editors running --json` | `count` / `pid` / `projectPath` / `hasPipeline` / `reachable` | human 表だけ見て空欄を死と断定 |
| `status --json` | Pipeline に接続できたインスタンス。`success` と `errors[].code` | `STATUS_NO_INSTANCES` を即 DEAD / 即 `pipeline install` |
| `doctor` | CLI 自身の path・スタブ重複・ライセンス | Editor の生存確認 |

`status` の失敗文は「Pipeline を入れろ」と書いてあっても、起動中（`reachable: false`）の定番である。`editors running` で PID があり `hasPipeline: true` なら install しない。待つ。

### 状態 → 対処

先に状態を名前で固定してから手を動かす。状態が変わるまで同じ手を繰り返さない。

| 状態 | 観測 | やる | やるな |
|---|---|---|---|
| **HUB_ONLY** | Hub プロセスだけ。`Get-Process Unity` 空。`editors running` count 0 | **DEAD** と同じ。`open` | Hub を Editor と数える |
| **DEAD** | Editor プロセス無し。`editors running` count 0。`status` も空 | `"$UNITY" --non-interactive --no-banner open "$WIN_PROJECT"`。その後 **STARTING** として待つ | `command` リトライ。`status` 失敗だけで放置。`run`/`build` で代用起動 |
| **STARTING** | Editor PID あり。`reachable: false`。`status` が `STATUS_NO_INSTANCES` | 15s 間隔で `editors running --json` を見る。上限 10 分。`reachable: true` になったら **READY** | 二度目の `open`。`pipeline install`。`command`。`run` |
| **READY** | `reachable: true`。`status` の対象 instance が `state: "ready"` | `list` → `command --timeout`。read-only なら `get_quality_settings` / `console --tail` で疎通確認 | GUI が居るのに `run`/`build`/`-batchmode` |
| **WRONG_PROJECT** | Editor は生きているが `projectPath` が対象と違う | 対象を `open`。既存 Editor は確認なしに殺さない | 別 project へ `command` して対象と錯覚 |
| **NO_PIPELINE** | `reachable` は true 寄り、または起動完了後も `hasPipeline: false` | `pipeline install --project-path "$WIN_PROJECT"`。終わったら待つ | 起動中の `STATUS_NO_INSTANCES` をこれと取り違える |
| **STUCK_STARTING** | **STARTING** が上限超過。プロセスは居るが `reachable` が false のまま | 状況を報告。wrapper があるなら wrapper の復旧に渡す。ユーザーが殺してよいと言うまで Editor を kill しない | 同じ `open` を連打。`run` で lock |
| **LOCK** | GUI が対象 project を開いているのに `run`/`build` したい | `command` 側 | 生 `-batchmode` |
| **STUB_PATH** | `doctor` の `path-duplicates` が WindowsApps を first | `%LOCALAPPDATA%\Unity\bin\unity.exe` を絶対 path で叩く | `unity` を PATH 任せ |
| **CMD_TIMEOUT** | `command` が既定 30s で落ちる | `--timeout` を上げて一回だけ再実行 | 失敗即 `open` |

### 待ち方（STARTING）

```bash
# reachable になるまで待つ。status は待たない（起動中は必ず失敗する）
i=0
while [ "$i" -lt 40 ]; do
  i=$((i+1))
  "$UNITY" --non-interactive --no-banner --json editors running
  sleep 15
done
```

JSON の `data.instances[].reachable` が true なら抜ける。10 分超えたら **STUCK_STARTING**。import / compile / domain reload 中は分単位で false のままになる。これは故障ではない。

### 作業セット

```bash
# DEAD → 起動。同じ project が STARTING/READY なら呼ばない
"$UNITY" --non-interactive --no-banner open "$WIN_PROJECT"

# READY になってから
"$UNITY" --non-interactive --no-banner --json list --project-path "$WIN_PROJECT"
"$UNITY" --non-interactive --no-banner command --project-path "$WIN_PROJECT" --timeout 120 -- <name> [args...]
```

`command` の第一引数を省略すると一覧になる。`list` / `command` は Pipeline が Editor 側に入り、かつ **READY** であること。

```bash
"$UNITY" --non-interactive --no-banner pipeline list
"$UNITY" --non-interactive --no-banner pipeline install --project-path "$WIN_PROJECT"
```

install は **NO_PIPELINE** のときだけ。

### `open`

対象プロジェクトを `ProjectVersion.txt` の Editor で開く。Hub レジストリ名、glob、ファイルシステム path を受け付ける。CLI は Editor 起動を待ってブロックすることがある。バックグラウンドにして、待ちは上の STARTING ループで見る。

```bash
"$UNITY" --non-interactive --no-banner open "$WIN_PROJECT"
"$UNITY" --non-interactive --no-banner open "$WIN_PROJECT" --editor-version 6000.0.65f1
```

- `--editor-path` には Editor 本体。CLI 自身の path を渡さない
- 既に同じ project が STARTING/READY なら二重起動しない

### `run` / `build` / `test`（ヘッドレス）

**Editor を batch で spawn** する。GUI が同じ project を開いていると lock する。**READY** なら `command`。閉じている／CI ならこちら。

```bash
"$UNITY" --non-interactive --no-banner run "$WIN_PROJECT" -- -nographics -quit
"$UNITY" --non-interactive --no-banner run "$WIN_PROJECT" --command <name> -- --target StandaloneWindows64
"$UNITY" --non-interactive --no-banner build "$WIN_PROJECT" --target StandaloneWindows64 --execute-method Builder.PerformBuild
"$UNITY" --non-interactive --no-banner test "$WIN_PROJECT" --mode EditMode --output "$WIN_PROJECT\\test-results.xml"
```

`run` / `test` の `--timeout` は Unity プロセスごと殺す。未指定は無効。`--allow-install` で Editor を入れるのは、ユーザーがインストールを依頼したときだけ。

### 診断

```bash
"$UNITY" --non-interactive --no-banner --json doctor
"$UNITY" --non-interactive --no-banner editors -i
"$UNITY" --non-interactive --no-banner --json env
```

### やってはいけないこと

- Editor バイナリや Store alias を CLI の代わりに叩く
- 生きている GUI Editor に `run` / `build` / 生の `-batchmode`
- `STATUS_NO_INSTANCES` を見てすぐ `pipeline install` またはすぐ `open`
- STARTING 中に `command` をリトライし続ける
- wrapper があるリポジトリで生 CLI に逃げて wrapper の復旧を飛ばす
- Linux `git` や Linux 側の再帰コピーを `/mnt/c` のプロジェクトに対して走らせる

`unity mcp` はこの CLI に付属する MCP 入口。Editor 操作の正は CLI コマンド。MCP 経由に切り替えない。MCP スキルが別にロードされているときだけ、そのスキルに従う。

## 待たない

`/mnt/c` 上の `git status`・再帰コピー・全ファイル grep は完了しない前提で上限を付ける。2 分以上動かない同一コマンドは打ち切り、Windows 側ツール（`git.exe` / `rg.exe` / `unity.exe`）へ切り替える。同じ Linux コマンドの再試行はしない。

例外: Unity の **STARTING** 待ちは 10 分まで許す。これは NTFS ハングではなく import / compile 待ち。
