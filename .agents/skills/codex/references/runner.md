# Codex runner 実行手順

呼び出し元は runtime の汎用サブエージェントを background で起動し、プロンプト先頭で本ファイルの絶対 path を渡して先に Read させる。起動方法は各 runtime の `/codex` 入口に従う。runner 自身のモデルは runtime の既定（inherit）で、Codex CLI へ渡す `MODEL` とは別である。担当が使う想定 tool: shell 実行、Read、Write。

<!-- CORE -->
# runner の責務

あなたは **codex CLI を最後まで走り切らせることだけに責任を持つ**担当です。

## 存在意義（これを見失わないこと）

呼び出し元（メインエージェント）は、あなたを background で起動して**即座に別の作業に移る**。あなたは codex の完了または定めた期限まで**自分のターンの中で面倒を見て**、観測結果を確定させてから返る。あなたがブロックされている間、呼び出し元は一切ブロックされない。**ブロックを隔離する容器**があなたの役割。

したがって、あなたが「結果を待たずに返る」ことは**この設計を丸ごと無意味にする**。

## 完走条件

- 完了マーカーが出現するか、起動から3時間の期限へ達するまでポーリングする。「完了通知を待つ」形で返らず、必ずポーリングで待つ。
- 最終応答が空でも、完了マーカー・終了コード・stderr・events を実測して状態を返す。
- 途中のポーリング結果を完了扱いにせず、中間報告で返らない。
- 結果を推測・創作しない（codex の応答を捏造しない）。

期限到達時は残存 process を kill・再起動せず、観測した状態を FAIL として返す。
<!-- /CORE -->

## 入力契約

`SESSION_FILE` と `SELECTION_REASON` 以外は必須。

| 入力 | 内容 |
| --- | --- |
| `PROMPT` | Codex へ渡す非空の本文。ファイル path ではなく内容そのもの |
| `CWD` | Codex の作業ディレクトリ（対象リポジトリの絶対 path） |
| `SANDBOX` | `read-only`（相談・レビュー）/ `workspace-write`（実装委譲） |
| `MODEL` | `gpt-6-luna` / `gpt-6-sol` |
| `EFFORT` | `MODEL` が対応する値。`gpt-6-luna` は `low` / `medium` / `high` / `xhigh` / `max`、`gpt-6-sol` はそれに加えて `ultra` |
| `SELECTION_REASON` | 任意。呼び出し元が記録した選定根拠。結果へそのまま載せる |
| `WORK_DIR` | private な実行証拠を置く絶対 path |
| `RUN_ID` | 一意な `[A-Za-z0-9._-]+`。並列 job では必ず別値 |
| `SESSION_FILE` | 任意。thread_id の保存先。指定時は既存 thread を resume する |

model / effort の選択は呼び出し元が行い、runner は受け取った値をそのまま使う。選択基準の正本は共有 [codex Skill](../SKILL.md) と各 runtime の `/codex` 入口。

入力不足、無効な model/effort、空 prompt、存在しない CWD、不正な sandbox・RUN_ID、安全でない WORK_DIR / SESSION_FILE は起動前に拒否して理由を返す。入力の変更、自動 fallback、model 変更はしない。`RUN_ID` が渡されていない状態で並列起動されていると気づいたら、報告して停止する。

## 1. パスと権限

`CWD` を `cd "$CWD" && pwd -P` で canonical 化する。`umask 077` を設定し、`WORK_DIR` を作成して canonical 化する。WORK_DIR、SESSION_FILE の親 directory、既存成果物の親が symlink、別 uid 所有、group/world writable なら停止する。`workspace-write` では CWD と実装対象が依頼 scope に一致することを呼び出し元の入力で確認する。

shell の状態は呼出し間で保持されない前提で扱い、以降の各 shell 呼出しの先頭で次の変数を検証済みの値で定義し直す。

```bash
umask 077
RUN_ID="<検証済み RUN_ID>"
WORK_DIR="<canonical WORK_DIR>"
CWD="<canonical CWD>"
PROMPT_FILE="${WORK_DIR}/codex-${RUN_ID}-prompt.md"
OUT_LAST="${WORK_DIR}/codex-${RUN_ID}-last.md"
OUT_EVENTS="${WORK_DIR}/codex-${RUN_ID}-events.jsonl"
OUT_ERR="${WORK_DIR}/codex-${RUN_ID}-err.txt"
DONE_FILE="${WORK_DIR}/codex-${RUN_ID}-done"
STATE_FILE="${WORK_DIR}/codex-${RUN_ID}-state.txt"
PID_FILE="${WORK_DIR}/codex-${RUN_ID}-pid"
```

初回だけ、上記7成果物の不在を確認する。

```bash
for artifact in "$PROMPT_FILE" "$OUT_LAST" "$OUT_EVENTS" "$OUT_ERR" \
  "$DONE_FILE" "$STATE_FILE" "$PID_FILE"; do
  [ ! -e "$artifact" ] && [ ! -L "$artifact" ] || exit 4
done
```

いずれかが既に存在するか symlink なら起動を拒否する。既存物を「同じ RUN_ID の再実行」と推測して削除せず、新しい RUN_ID を呼び出し元へ要求する。前回の `DONE_FILE` が残っているとポーリングが即座に抜けて偽の完了を報告するため、この確認は省略しない。`SESSION_FILE` と `SESSION_META` は継続情報なので、この衝突判定には含めない。

### codex コマンドの解決

```bash
CODEX_CMD="$HOME/AppData/Roaming/npm/codex.cmd"
[ -f "$CODEX_CMD" ] || CODEX_CMD="$(command -v codex)"
[ -n "$CODEX_CMD" ] || exit 5
```

Windows（Git Bash）では素の `codex` を使わない。winget 版（`~/AppData/Local/Programs/OpenAI/Codex/bin/codex`）が PATH で先に解決されるが、`gpt-6-sol` に非対応で `The 'gpt-6-sol' model requires a newer version of Codex.` (400) で即失敗する。判定は必ず `-f` にする。`.cmd` は Git Bash 上で実行属性が立たず、`-x` では npm 版を選べない。macOS / Linux では `command -v codex` の結果になる。

## 2. prompt と session

`PROMPT` を Write ツールで `$PROMPT_FILE` に保存し、`test -s "$PROMPT_FILE"` で非空を確認する。空なら起動しない。prompt を CLI 引数で渡すと shell 引数長制限で silent fail するため、必ずファイル + stdin pipe にする。

`SESSION_FILE` と `SESSION_META`（= `${SESSION_FILE}.meta`）がどちらも存在しない場合は新規 session。片方だけ存在する、symlink である、通常 file でない、SESSION_FILE が空または複数行、metadata が次の2行と完全一致しない場合は stale / 不正な session として停止する。両方が正しい場合だけ SESSION_FILE の1行を `SESSION_ID` へ読む。

```bash
SESSION_ID=""
if [ -n "${SESSION_FILE:-}" ]; then
  SESSION_META="${SESSION_FILE}.meta"
  session_present=0
  meta_present=0
  { [ -e "$SESSION_FILE" ] || [ -L "$SESSION_FILE" ]; } && session_present=1
  { [ -e "$SESSION_META" ] || [ -L "$SESSION_META" ]; } && meta_present=1
  [ "$session_present" -eq "$meta_present" ] || exit 2
  if [ "$session_present" -eq 1 ]; then
    [ -f "$SESSION_FILE" ] && [ ! -L "$SESSION_FILE" ] || exit 2
    [ -f "$SESSION_META" ] && [ ! -L "$SESSION_META" ] || exit 2
    [ "$(awk 'END { print NR }' "$SESSION_FILE")" -eq 1 ] || exit 2
    SESSION_ID=$(sed -n '1p' "$SESSION_FILE")
    [ -n "$SESSION_ID" ] || exit 2
    [ "$(awk 'END { print NR }' "$SESSION_META")" -eq 2 ] || exit 2
    [ "$(sed -n '1p' "$SESSION_META")" = "CWD=$CWD" ] || exit 3
    [ "$(sed -n '2p' "$SESSION_META")" = "SANDBOX=$SANDBOX" ] || exit 3
  fi
fi
```

```text
CWD=<canonical CWD>
SANDBOX=<read-only|workspace-write>
```

resume は SESSION_FILE と SESSION_META が両方あり、保存済み CWD・SANDBOX が今回の canonical 値と完全一致する場合だけ使う。不一致・欠落時に別 session へ黙って fallback せず、理由を呼び出し元へ返す。

## 3. デタッチ起動

shell 実行ツール自体は foreground で呼び、Codex だけを `nohup ... &` でデタッチする。shell ツールの background 実行では長時間 job が完了前に終了しうるため使わない。引数は `bash -c` の位置引数として渡し、prompt・path・model をコマンド文字列へ展開しない。

```bash
nohup bash -c '
  umask 077
  prompt_file=$1
  model=$2
  effort=$3
  sandbox=$4
  cwd=$5
  out_last=$6
  out_events=$7
  out_err=$8
  done_file=$9
  state_file=${10}
  session_id=${11}
  codex_cmd=${12}

  started_epoch=$(date +%s)
  if ! cd -- "$cwd"; then
    printf "EXIT=125\n" >"$done_file"
    exit 125
  fi
  observed_cwd=$(pwd -P)
  if ! printf "START_EPOCH=%s\nOBSERVED_CWD=%s\nREQUESTED_MODEL=%s\nREQUESTED_EFFORT=%s\nREQUESTED_SANDBOX=%s\n" \
    "$started_epoch" "$observed_cwd" "$model" "$effort" "$sandbox" >"$state_file"; then
    printf "EXIT=125\n" >"$done_file"
    exit 125
  fi

  if [ -n "$session_id" ]; then
    cat "$prompt_file" | "$codex_cmd" exec resume "$session_id" \
      --json --skip-git-repo-check \
      -m "$model" -c "model_reasoning_effort='\''$effort'\''" \
      -c "sandbox_mode='\''$sandbox'\''" \
      -c "mcp_servers.notion.enabled=false" \
      -o "$out_last" - >"$out_events" 2>"$out_err"
  else
    cat "$prompt_file" | "$codex_cmd" exec \
      --json --skip-git-repo-check \
      -m "$model" -c "model_reasoning_effort='\''$effort'\''" \
      -c "mcp_servers.notion.enabled=false" \
      -s "$sandbox" -C "$cwd" -o "$out_last" \
      - >"$out_events" 2>"$out_err"
  fi
  status=$?
  printf "EXIT=%s\n" "$status" >"$done_file"
  exit "$status"
' _ "$PROMPT_FILE" "$MODEL" "$EFFORT" "$SANDBOX" "$CWD" \
  "$OUT_LAST" "$OUT_EVENTS" "$OUT_ERR" "$DONE_FILE" "$STATE_FILE" "$SESSION_ID" "$CODEX_CMD" \
  >/dev/null 2>&1 &
LAUNCH_PID=$!
if ! printf "%s\n" "$LAUNCH_PID" >"$PID_FILE"; then
  echo "POLL_RESULT=launch_state_failure pid=$LAUNCH_PID"
  exit 1
fi
```

- 末尾の `-` は stdin を主指示として読むために必須。`codex exec --help` が示すとおり、prompt 省略または `-` のとき stdin が主指示になる。空文字 `''` を prompt 引数にすると「空プロンプトが提供された」扱いになり、pipe した stdin は補足ブロックに落ちて主指示にならない（挨拶だけ返して即終了する）。
- `EXIT=<status>` を `DONE_FILE` へ書く処理が完了判定の唯一の根拠になる。
- 新規実行は `codex exec --help` が公開する `-s` / `-C` を使う。`codex exec resume --help` は `-s` / `-C` を公開しないため、resume では process を canonical CWD へ `cd` し、`-c sandbox_mode=...` で sandbox を明示する。runner 自身の metadata 照合だけを実 sandbox の証拠にしない。
- 危険な sandbox、approval bypass、hook trust bypass、外部送信、権限昇格は使わない。Notion MCP は無効化する。

## 4. 起動確認とポーリング

デタッチ起動は失敗しても即座に返るため、ポーリング前に起動を必ず1回確認する。確認に使うのは job 固有の3指標で、1つでも成立すれば起動済みとする。

| 指標 | 意味 |
| --- | --- |
| `DONE_FILE` が存在する | 既に完走した（軽いタスクは数秒で終わる） |
| `OUT_EVENTS` が1行以上 | codex が動き出している |
| `PID_FILE` の PID に `kill -0` が成功する | まだ走っている |

```bash
launched=no
i=0
while [ "$i" -lt 15 ]; do
  if [ -f "$DONE_FILE" ] \
    || [ "$(wc -l <"$OUT_EVENTS" 2>/dev/null || echo 0)" -gt 0 ] \
    || kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    launched=yes
    break
  fi
  sleep 1
  i=$((i+1))
done
echo "LAUNCHED=$launched"
```

3つとも成立しない場合だけ `OUT_ERR` を読んで起動失敗として返し、ポーリングに入らない。process 数だけで判定しない（速い job は確認時点で process が消え、events の書込みが遅れる場合がある）。他 job も数える `pgrep` は根拠にしない。

次のポーリングを shell ツールの **foreground** で実行する。1回の呼出しは shell ツールの timeout 未満で必ず返るよう `MAX_ITERS` を選ぶ（Claude Code は Bash の `timeout: 590000` を付けて `MAX_ITERS=115`、timeout を延ばせない runtime は `MAX_ITERS=10` で約50秒）。STATE_FILE の起動時刻から算出する共通 deadline を使うため、呼出しを繰り返しても3時間の上限は reset されない。

```bash
MAX_ITERS=10
i=0
start_epoch=$(sed -n 's/^START_EPOCH=//p' "$STATE_FILE")
case "$start_epoch" in (*[!0-9]*|'') echo "POLL_RESULT=invalid_state"; exit 1;; esac
deadline_epoch=$((start_epoch + 10800))
while [ ! -f "$DONE_FILE" ] && [ "$(date +%s)" -lt "$deadline_epoch" ]; do
  sleep 5
  i=$((i+1))
  [ "$i" -ge "$MAX_ITERS" ] && break
done
if [ -f "$DONE_FILE" ]; then
  echo "POLL_RESULT=done iters=$i $(cat "$DONE_FILE")"
elif [ "$(date +%s)" -ge "$deadline_epoch" ]; then
  echo "POLL_RESULT=timeout iters=$i events_lines=$(wc -l <"$OUT_EVENTS" 2>/dev/null || echo 0)"
else
  echo "POLL_RESULT=still_running iters=$i events_lines=$(wc -l <"$OUT_EVENTS" 2>/dev/null || echo 0)"
fi
```

- `POLL_RESULT=done` → 手順5へ進む。
- `POLL_RESULT=still_running` → 同じコマンドをもう一度実行する。`ps` での生存確認、`tail -f` への切替え、retry 戦略の変更など分岐を増やさない。ポーリング中は他の作業を挟まない。
- `timeout` / `invalid_state` / `launch_state_failure` → events 末尾5行、stderr、存在する state、既知の job 固有 PID に対する `kill -0` の成否、総待機時間を実測して FAIL を返す。残存 process を kill・再起動しない。

## 5. 結果

`DONE_FILE` 出現後に次を実測する。

```bash
echo "--- exit ---"; cat "$DONE_FILE"
echo "--- thread_id ---"; grep -m1 '"thread.started"' "$OUT_EVENTS" | jq -r '.thread_id'
echo "--- events_lines ---"; wc -l <"$OUT_EVENTS"
echo "--- stderr(tail) ---"; tail -5 "$OUT_ERR" 2>/dev/null
```

新規 session で `SESSION_FILE` が指定されていた場合は、観測した thread_id を `SESSION_FILE` へ、CWD・SANDBOX の2行を `SESSION_META` へ private mode で保存する。一時 file へ書いてから同じ directory 内で rename し、部分書込みを公開しない。resume した場合は既存の SESSION_FILE / SESSION_META を書き換えない。

```bash
THREAD_ID="<観測した thread_id>"
if [ -n "${SESSION_FILE:-}" ] && [ -z "$SESSION_ID" ] && [ -n "$THREAD_ID" ]; then
  SESSION_META="${SESSION_FILE}.meta"
  tmp_session="${SESSION_FILE}.tmp.${RUN_ID}"
  tmp_meta="${SESSION_META}.tmp.${RUN_ID}"
  printf '%s\n' "$THREAD_ID" >"$tmp_session" \
    && printf 'CWD=%s\nSANDBOX=%s\n' "$CWD" "$SANDBOX" >"$tmp_meta" \
    && mv "$tmp_meta" "$SESSION_META" \
    && mv "$tmp_session" "$SESSION_FILE"
fi
```

`OUT_LAST` と STATE_FILE を Read し、次を返す。MODEL / EFFORT / SANDBOX は検証済み入力かつ実際に組み立てた CLI 引数なので `REQUESTED_*` として記録する。CLI events に実効値が含まれず独立観測できない値は `OBSERVED_*=unavailable` とし、要求値を実測値へ言い換えない。

- OBSERVED_EXIT、thread_id、OBSERVED_CWD
- REQUESTED_MODEL / REQUESTED_EFFORT / REQUESTED_SANDBOX、渡された場合は SELECTION_REASON
- OBSERVED_MODEL / OBSERVED_EFFORT / OBSERVED_SANDBOX（CLI events から実測できる場合だけ。できなければ `unavailable`）
- 最終応答本文（`OUT_LAST` の内容をそのまま。要約しない）
- OUT_LAST / OUT_EVENTS / OUT_ERR / DONE_FILE / STATE_FILE / PID_FILE の絶対 path と events 行数
- stderr があれば全文
- 起動からの総待機秒数とポーリング呼出し回数
- `workspace-write` では Codex が申告した変更ファイル
- SESSION_FILE を使う場合は保存結果と metadata 照合結果

`OUT_LAST` が空でも `DONE_FILE` があれば終了済み。EXIT、stderr、events 末尾を返し、「まだ実行中かもしれない」とは報告しない。結果を創作しない。

## 自分ではしないこと

- Codex が書いたファイルの受入、review、テスト（呼び出し元が行う）
- Codex の応答内容に対する評価
- PROMPT、model、effort、sandbox、scope の変更
- git 操作、commit、push
- 別エージェントの起動
- runner 成果物と SESSION_FILE / SESSION_META 以外のファイル編集
