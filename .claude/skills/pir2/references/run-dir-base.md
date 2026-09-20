# RUN_DIR base path — SSOT（成果物置き場の基底パス）

PIR² 系ワークフロー（`pir2` / `pir2async` / `pir2codex` / `debug` / `ir` / `reviewer` / `review-pr` / `refactor-advisor` / `writing-plan` / `research`）の成果物置き場の**基底パスの唯一の正典**。

- 基底パスの SSOT = **本ファイル**。
- Claude の project memory パスを導出する sanitize 正規表現の SSOT = `sanitized-cwd.md`。RUN_DIR の基底には sanitize を使わない。

---

## 原則: プロジェクトローカル

成果物は **カレントプロジェクト配下**に置く。これにより対象プロジェクトとの対応と git 管理範囲が明確になる。

### 中間受け渡しファイル（サブエージェント間 / 作業ファイル）

```
RUN_DIR = ${PROJECT_ROOT}/.ai-pir-runs/${run_ts}-${run_feature}
```

- `PROJECT_ROOT` = スキル起動時のカレント（`$(pwd)`）。
- **sanitized-cwd は不要**（PROJECT_ROOT 自体がプロジェクト固有なので `<sanitized-cwd>` セグメントを挟まない）。
- **git 追跡外**にする（中間ファイルはコミット対象でない）。Step0 で `.gitignore` に `/.ai-pir-runs/` が無ければ追記する。
- `handoff.md` は **RUN_DIR の親 = `${PROJECT_ROOT}/.ai-pir-runs/handoff.md`（プロジェクト単位で 1 ファイル・run 非依存）**。RUN_DIR 配下に置くと、次回起動時に `$HANDOFF_PATH` を発見できない。配置・ライフサイクルの SSOT は `~/.claude/pir-handoff.md`。

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
| `deepthink` | 熟考レポート | `docs/deepthink/` |
| `pir2` / `pir2async` / `pir2codex` | `plan.md` | `docs/plans/` |
| `writing-plan` | `plan.md`（実装記録） | `docs/plans/` |
| `reviewer` | レビュー結果 | `docs/reviews/` |
| `review-pr` | PR レビュー結果 | `docs/reviews/` |
| `refactor-advisor` | リファクタ提案 | `docs/reviews/` |
| `debug` | 診断レポート（`plan.md` 相当があれば） | `docs/debug/` |
| `ir` | （最終成果物はコード変更。docs コピーなし） | — |

`plan.md` など人が読む最終成果物は `docs/` 配下、中間受け渡しファイルは `.ai-pir-runs/` 配下に置く。

---

## Step0 の標準 Bash（コピー元・全スキル共通）

```bash
PROJECT_ROOT="$(pwd)"
run_ts="$(date +%Y%m%d-%H%M%S)"
# run_feature をファイル名に使える短い文字列へ正規化する
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

`PROJECT_ROOT` が git リポジトリでない場合も RUN_DIR は作成できるが、`.gitignore` 追記は上記 `if` によりスキップする。`PROJECT_ROOT` 配下へ書き込めない場合はその事実を報告し、実際の利用権限があると確認できるときだけ `${HOME}/.ai-pir-runs/${run_ts}-${run_feature}` を代替先にする。アクセス拒否を隠さず、保存先に依存しない作業は継続する。
