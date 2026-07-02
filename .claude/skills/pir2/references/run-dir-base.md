# RUN_DIR base path — SSOT（成果物置き場の基底パス）

PIR² 系ワークフロー（`pir2` / `pir2async` / `pir2codex` / `debug` / `ir` / `reviewer` / `review-pr` / `refactor-advisor` / `writing-plan` / `research`）の成果物置き場の**基底パスの唯一の正典**。

- 基底パスの SSOT = **本ファイル**。
- sanitize 正規表現の SSOT = `sanitized-cwd.md`（ただし後述のとおり **PROJECT_ROOT 基底では sanitize 自体が不要**になったため、`sanitized-cwd.md` は deprecated）。

---

## 原則: プロジェクトローカル

成果物は `~/`（ホーム）直下の隠れ場所に置かず、**カレントプロジェクト配下**に置く。理由: ホーム直下（旧 `~/.ai-pir-runs/<sanitized-cwd>/`）は階層が深く手元から見つけにくく、プロジェクトとの対応も分かりにくいため。

### 中間受け渡しファイル（サブエージェント間 / 作業ファイル）

```
RUN_DIR = ${PROJECT_ROOT}/.ai-pir-runs/${run_ts}-${run_feature}
```

- `PROJECT_ROOT` = スキル起動時のカレント（`$(pwd)`）。
- **sanitized-cwd は不要**（PROJECT_ROOT 自体がプロジェクト固有なので `<sanitized-cwd>` セグメントを挟まない）。
- **git 追跡外**にする（中間ファイルはコミット対象でない）。Step0 で `.gitignore` に `/.ai-pir-runs/` が無ければ追記する。
- `handoff.md` は **RUN_DIR の親 = `${PROJECT_ROOT}/.ai-pir-runs/handoff.md`（プロジェクト単位で 1 ファイル・run 非依存）**。RUN_DIR は run ごとにタイムスタンプで新規作成されるため、handoff を RUN_DIR 配下に置くと resume 機構（`$HANDOFF_PATH` の存在チェックで `RESUME_MODE` を判定）が毎 run 壊れる。旧構造（`${HOME}/.ai-pir-runs/${sanitized_cwd}/handoff.md` = 基底直下・run 非依存）の「基底直下」を保ったまま基底だけ差し替える。配置・ライフサイクルの SSOT は `~/.claude/pir-handoff.md`。

### 最終成果物（人が読むレポート / plan / review）

```
${PROJECT_ROOT}/docs/<kind>/${run_ts}-${run_feature}.md
```

- **git 追跡**（コミット対象・人が読む）。
- `<kind>` はスキル別（下表）。

#### 最終成果物の docs/ マップ

| スキル | 最終成果物 | `<kind>` |
|---|---|---|
| `research` | 研究レポート | `docs/research/` |
| `pir2` / `pir2async` / `pir2codex` | `plan.md` | `docs/plans/` |
| `writing-plan` | `plan.md`（実装記録） | `docs/plans/` |
| `reviewer` | レビュー結果 | `docs/reviews/` |
| `review-pr` | PR レビュー結果 | `docs/reviews/` |
| `refactor-advisor` | リファクタ提案 | `docs/reviews/` |
| `debug` | 診断レポート（`plan.md` 相当があれば） | `docs/debug/` |
| `ir` | （最終成果物はコード変更。docs コピーなし） | — |

> ℹ️ `plan.md` を `docs/plans/` にコピーする既存設計（pir2 / writing-plan）は、基底が PROJECT_ROOT になっても **そのまま有効**（`docs/plans/` は元々プロジェクトローカル）。中間ファイルの基底だけが `~/.ai-pir-runs` → `${PROJECT_ROOT}/.ai-pir-runs` に変わる。

---

## Step0 の標準 Bash（コピー元・全スキル共通）

```bash
PROJECT_ROOT="$(pwd)"
run_ts="$(date +%Y%m%d-%H%M%S)"
# run_feature の sanitize（英数字以外を - に。SSOT は sanitized-cwd.md の正規表現）
run_feature="$(printf '%s' "$ARGUMENTS" | tr -c 'a-zA-Z0-9' '-' | sed -E 's/-+/-/g; s/^-//; s/-$//' | cut -c1-40)"
[ -z "$run_feature" ] && run_feature="<skill-default>"   # 各スキルのデフォルト名
RUN_DIR="${PROJECT_ROOT}/.ai-pir-runs/${run_ts}-${run_feature}"
mkdir -p "$RUN_DIR"
# 中間ファイルを git 追跡から外す（git リポジトリのときのみ）
if git -C "$PROJECT_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  grep -qxF '/.ai-pir-runs/' "${PROJECT_ROOT}/.gitignore" 2>/dev/null || echo '/.ai-pir-runs/' >> "${PROJECT_ROOT}/.gitignore"
fi
echo "PROJECT_ROOT=$PROJECT_ROOT"
echo "RUN_DIR=$RUN_DIR"
```

> ℹ️ `${PROJECT_ROOT}` 基底になったことで、旧 `sanitized_cwd="$(pwd | sed 's|[^a-zA-Z0-9]|-|g')"` 行は**不要**（削除する）。`sanitized-cwd.md` / `verify-sanitized-cwd.sh` は基底が変わったため deprecated。

---

## フォールバック

- `PROJECT_ROOT` が git リポジトリでない → RUN_DIR は作れるが `.gitignore` 追記はスキップする（上記 Bash の `if` が担保）。
- `PROJECT_ROOT` 配下に書き込めない稀なケース → その旨を伝えて旧 `${HOME}/.ai-pir-runs/${run_ts}-${run_feature}` にフォールバックしてよい（例外運用）。

---

## 移行メモ（2026-07-02）

- 旧: `RUN_DIR="${HOME}/.ai-pir-runs/${sanitized_cwd}/${run_ts}-${run_feature}"`（ホーム直下・sanitized-cwd セグメントあり）。
- 新: `RUN_DIR="${PROJECT_ROOT}/.ai-pir-runs/${run_ts}-${run_feature}"`（プロジェクトローカル・sanitize 不要）。
- `settings.json` の `Edit/Write/Read(~/.ai-pir-runs/**)` allow は**残置**（既存ランとの互換・害なし）。プロジェクト配下は通常カレントとして書けるため新規 allow は不要。
- 説明文・擬似コード中の絶対パス例示（`~/.ai-pir-runs/<sanitized-cwd>/...` や表記ゆれ `pir_runs/<run>/`）はすべて `${PROJECT_ROOT}/.ai-pir-runs/<run>/` に統一する。
