# Cursor run directory

PIR²系の長時間runで外部artifactが必要な場合だけ、この手順で専有`RUN_DIR`を予約する。`CURSOR_SKILLS_DIR`はロード済みSkillの実体から解決し、対象repoやHOMEからSkillの所在を推測しない。

`PROJECT_MEMORY_DIR`のbucket名はCursor harnessと同じく、canonical `PROJECT_ROOT`のASCII英数字以外を`-`へ置換して作る。親から検証済みの値を受け取った場合は再計算しない。

`PROJECT_ROOT` と `PROJECT_MEMORY_DIR` は対象アプリケーションの文脈ですが、`RUN_DIR` は対象 repo の外側にある実行 artifact 用の領域です。Cursor の PIR² は必要な run だけ、次の手順で `RUN_DIR` を一度だけ予約します。native collaboration やメインの直接実装で report が不要な場合は、この run directory 自体を作成する必要はありません。

`RUN_ROOT` と project bucket の親は実体のある directory で、symlink を辿って別の保存先へ向けてはいけません。存在しない親は `umask 077` のもとで `mkdir` し、既存の run path や symlink を再利用せず、候補ごとに排他的な `mkdir` が成功した path を採用します。

```bash
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd -P)"
PROJECT_ROOT="$(CDPATH='' cd -- "$PROJECT_ROOT" && pwd -P)"
sanitized_cwd="$(printf '%s' "$PROJECT_ROOT" | sed 's|[^a-zA-Z0-9]|-|g')"
PROJECT_MEMORY_DIR="${HOME:?HOME is required}/.cursor/projects/${sanitized_cwd}/memory"
run_ts="$(date +%Y%m%d-%H%M%S)"
run_feature="$(printf '%s' "${ARGUMENTS-}" | tr -c 'a-zA-Z0-9' '-' | sed -E 's/-+/-/g; s/^-//; s/-$//' | cut -c1-40)"
[ -n "$run_feature" ] || run_feature="task"

RUN_ROOT="${HOME:?HOME is required}/.ai-pir-runs"
if [ -L "$RUN_ROOT" ]; then
  printf '%s\n' "RUN_ROOT must not be a symlink: $RUN_ROOT" >&2
  exit 1
fi
if [ -e "$RUN_ROOT" ] && [ ! -d "$RUN_ROOT" ]; then
  printf '%s\n' "RUN_ROOT exists but is not a directory: $RUN_ROOT" >&2
  exit 1
fi
if [ ! -e "$RUN_ROOT" ]; then
  (umask 077; mkdir "$RUN_ROOT") 2>/dev/null || {
    [ -d "$RUN_ROOT" ] && [ ! -L "$RUN_ROOT" ] || exit 1
  }
fi
[ -d "$RUN_ROOT" ] && [ ! -L "$RUN_ROOT" ] || exit 1
RUN_ROOT="$(CDPATH='' cd -- "$RUN_ROOT" && pwd -P)"

case "$RUN_ROOT" in
  "$PROJECT_ROOT"|"$PROJECT_ROOT"/*)
    printf '%s\n' "RUN_ROOT must be outside PROJECT_ROOT: $RUN_ROOT" >&2
    exit 1
    ;;
esac

PROJECT_RUN_ROOT="${RUN_ROOT}/${sanitized_cwd}"
if [ -e "$PROJECT_RUN_ROOT" ] || [ -L "$PROJECT_RUN_ROOT" ]; then
  [ -d "$PROJECT_RUN_ROOT" ] && [ ! -L "$PROJECT_RUN_ROOT" ] || exit 1
else
  (umask 077; mkdir "$PROJECT_RUN_ROOT") || {
    [ -d "$PROJECT_RUN_ROOT" ] && [ ! -L "$PROJECT_RUN_ROOT" ] || exit 1
  }
fi
PROJECT_RUN_ROOT="$(CDPATH='' cd -- "$PROJECT_RUN_ROOT" && pwd -P)"

RUN_PREFIX="${PROJECT_RUN_ROOT}/${run_ts}-${run_feature}"
run_collision=0
while :; do
  RUN_DIR="$RUN_PREFIX"
  [ "$run_collision" -eq 0 ] || RUN_DIR="${RUN_PREFIX}-${run_collision}"
  if (umask 077; mkdir "$RUN_DIR") 2>/dev/null; then
    break
  fi
  [ -e "$RUN_DIR" ] || [ -L "$RUN_DIR" ] || exit 1
  run_collision=$((run_collision + 1))
done
[ -d "$RUN_DIR" ] && [ ! -L "$RUN_DIR" ] || exit 1

HANDOFF_PATH="${PROJECT_RUN_ROOT}/handoff.md"
if [ "${USE_HANDOFF:-false}" = true ]; then
  if [ -L "$HANDOFF_PATH" ] || { [ -e "$HANDOFF_PATH" ] && [ ! -f "$HANDOFF_PATH" ]; }; then
    printf '%s\n' "HANDOFF_PATH must be a regular non-symlink file: $HANDOFF_PATH" >&2
    exit 1
  fi
fi
echo "PROJECT_ROOT=$PROJECT_ROOT" "PROJECT_MEMORY_DIR=$PROJECT_MEMORY_DIR" "RUN_ROOT=$RUN_ROOT" "RUN_DIR=$RUN_DIR" "HANDOFF_PATH=$HANDOFF_PATH"
```

`HANDOFF_PATH` を Read または Write する場合は、親 `PROJECT_RUN_ROOT` が上記の実体 directory であることと、`HANDOFF_PATH` 自体が symlink でないことを確認します。既存 handoff の確認が不要な run では、ファイルを作成・更新しません。run の終了時に `RUN_DIR` を自動削除せず、必要な記録の保持と cleanup は呼び出し元の判断に委ねます。

この手順はrun pathとhandoffの安全境界だけを定める。
