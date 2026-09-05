# sanitized-cwd 計算プロトコル（SSOT）

PIR² 系スキル（pir2 / pir2async / debug / ir / reviewer / review-pr / writing-plan / refactor-advisor / retro）の `PROJECT_MEMORY_DIR` 導出に使う **sanitize 正規表現の SSOT**。Cursor harness の sanitize ロジックと一致させる必要があるため、変更時はこのファイルのみを更新し、参照側 9 ファイルに横展開する。

Cursor-native SSOT path: `${CURSOR_SKILLS_DIR}/pir2/references/sanitized-cwd.md`

`CURSOR_SKILLS_DIR` は、読み込み済みの本 `SKILL.md` の実体パスから親の親として解決します。対象アプリケーションの `PROJECT_ROOT` とは別の場所であり、対象 repo 内の固定配置を参照先として仮定しません。

---

## 正規表現 SSOT

```text
sed 's|[^a-zA-Z0-9]|-|g'
```

意図:
- Cursor の `PROJECT_MEMORY_DIR`（`~/.cursor/projects/<sanitized-cwd>/memory`）を導出するときの sanitize ロジックと一致させる
- ASCII 英数字 (`a-zA-Z0-9`) 以外の **すべての文字**（`/`・`.`・`-`・スペース等）を `-` に置換する
- これにより `/home/user/ghq/github.com/org/repo` → `-home-user-ghq-github-com-org-repo` のような変換になる

---

## 入力ソース（呼び出し側で選択する）

入力ソースは利用箇所によって 2 系統存在する:

| 系統 | 入力 | 採用スキル | 用途 |
|---|---|---|---|
| **pwd 系** | `pwd` の出力 | pir2 / pir2async / debug / ir / reviewer / review-pr / writing-plan / refactor-advisor | スキル起動時の現在ディレクトリを sanitize して `PROJECT_MEMORY_DIR` を導出 |
| **target_path 系** | `$target_path` 変数 | retro | `/retro` トリガーから渡された対象ディレクトリパスを sanitize（current dir と異なる場合がある） |

利用箇所のコード例:

```bash
# pwd 系（pir2 等）
sanitized_cwd="$(pwd | sed 's|[^a-zA-Z0-9]|-|g')"

# target_path 系（retro）
sanitized_cwd="$(echo "$target_path" | sed 's|[^a-zA-Z0-9]|-|g')"
```

**両系統で sed 正規表現 `[^a-zA-Z0-9]|-|g` は完全に一致する**。揺れさせてはならない。

---

## Cursor の run directory

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

この手順は Cursor PIR² の run path と handoff の安全境界だけを定めます。runner の schema、provenance、台帳、report 形式は追加せず、明示的に runner を選んだ job の既存契約へ委ねます。

---

## 参照側のファイル一覧

このリファレンスを参照する 9 ファイル（各ファイルで sed 式は同一・入力ソースは上記表の通り）:

| # | ファイル | 入力系統 |
|---|---|---|
| 1 | `${CURSOR_SKILLS_DIR}/pir2/SKILL.md` | pwd 系 |
| 2 | `${CURSOR_SKILLS_DIR}/pir2async/SKILL.md` | pwd 系 |
| 3 | `${CURSOR_SKILLS_DIR}/debug/SKILL.md` | pwd 系 |
| 4 | `${CURSOR_SKILLS_DIR}/ir/SKILL.md` | pwd 系 |
| 5 | `${CURSOR_SKILLS_DIR}/reviewer/SKILL.md` | pwd 系 |
| 6 | `${CURSOR_SKILLS_DIR}/review-pr/SKILL.md` | pwd 系 |
| 7 | `${CURSOR_SKILLS_DIR}/writing-plan/SKILL.md` | pwd 系 |
| 8 | `${CURSOR_SKILLS_DIR}/refactor-advisor/SKILL.md` | pwd 系 |
| 9 | `${CURSOR_SKILLS_DIR}/retro/SKILL.md` | target_path 系 |

---

## Cursor harness 仕様変更時の更新手順

Cursor harness の sanitize ロジックが変わった（例: `.` を残す、ハッシュ化に変わる、等）場合の更新手順:

1. **本ファイルの「正規表現 SSOT」セクションを更新する**（最初に SSOT を直す）
2. **検証スクリプトを実行**して、9 ファイル全てに同一式が存在することを確認:
   ```bash
   bash "${CURSOR_SKILLS_DIR}/pir2/references/verify-sanitized-cwd.sh"
   ```
3. スクリプトが揺れを検出したら、対象ファイルの sed 式を SSOT に合わせて修正する
4. 既存 `~/.cursor/projects/` 配下の旧ディレクトリ（旧 sanitize 規則で作られたもの）は **手動でマージ判断**する。retrospector N1.5「プロジェクトメモリディレクトリ整合性チェック」が並存検知を担う

---

## 検証スクリプト（機械検出）

「ルールを書いたら機械検出も同時に作る」原則（feedback_rule_with_enforcement）に従い、9 ファイルの sed 式が SSOT と一致していることを検証するスクリプトを併設する。

スクリプトパス: `${CURSOR_SKILLS_DIR}/pir2/references/verify-sanitized-cwd.sh`

実行方法:

```bash
bash "${CURSOR_SKILLS_DIR}/pir2/references/verify-sanitized-cwd.sh"
```

成功時の出力例:
```
OK: 9 SKILL.md files all use the SSOT sanitize regex [^a-zA-Z0-9]|-|g
```

失敗時の出力例:
```
NG: 1 file deviates from SSOT sanitize regex
  - ${CURSOR_SKILLS_DIR}/foo/SKILL.md: expected [^a-zA-Z0-9]|-|g, found [^a-zA-Z0-9_]|-|g
```

CI/pre-commit に組み込む際は exit code 1 で停止させる設計（スクリプト内で `exit 1` を返す）。

---

## 既存の並存ディレクトリへの対処

過去の Cursor 旧版が `.` を残す sanitize ロジックを使っていた時期があり、`~/.cursor/projects/` 配下に `github-com` 形式と `github.com` 形式の両方が並存している場合がある。

- **retrospector N1.5** が並存検知を担い、警告レポート挿入 + レジストリ自動フラグ化を行う（`~/.cursor/agents/retrospector.md` 参照）
- 自動マージは **行わない**（データ損失リスク）。ユーザー判断でマージするときは古い方の `feedback_*.md` / `MEMORY.md` / `pir_*_log.md` を新しい方に手動マージする
- 現状の式 `[^a-zA-Z0-9]|-|g` は harness 現行版と一致しており、新規ディレクトリは正しく現行系統に集約される

---

## 関連リファレンス

- `~/.cursor/agents/retrospector.md` の N1.5「プロジェクトメモリディレクトリ整合性チェック」
- `~/.cursor/projects/<sanitized-cwd>/memory/feedback_rule_with_enforcement.md`（ルールには機械検出を併設する原則）
