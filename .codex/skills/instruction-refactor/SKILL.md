---
name: "instruction-refactor"
description: "CLAUDE.md・agent・skill の肥大化、責務越境、SSOT逸脱、重複を測定し、Progressive Disclosure と参照化で整理する。『instruction file整理』『skillが長い』『棚卸し』『.codex整理』や /instruction-refactor で使う。"
argument-hint: "[--scope=user|project|all] [--no-implement] [path]"
---

# Instruction Refactor

instruction file を公式定量基準と構造上の問題から測定し、配達経路を壊さず整理します。コードを対象にする `refactor-advisor` とは別です。

Astra parent（`gpt-6-astra` / `high`）が対象範囲、測定の統合、整理方針、受入条件、最終判断を所有します。列挙・測定・横断比較は explorer へ委譲できます。小さく密結合した整理は Astra が直接実装し、独立した通常作業は [worker-delegation](../worker-delegation/SKILL.md) の worker（Luna Max）へ渡します。構造、SSOT、広範な影響分析など推論中心の難所は expert / expert_max（Sol High/Max）を最初から選べます。Terra は同種 workload で実測上の利点がある場合だけの例外です。

判断基準、整理戦略、公式引用は `references/` を必要な時だけ読みます。

参照先は対象リポジトリではなく、読込済みの本 `SKILL.md` の実体から解決します。親はその絶対パスを `THIS_SKILL_PATH` として確定し、`SKILL_DIR="$(cd "$(dirname "$THIS_SKILL_PATH")" && pwd -P)"`、`CODEX_SKILLS_DIR="$(cd "$SKILL_DIR/.." && pwd -P)"` を使います。以下の `references/...` は `$SKILL_DIR` 相対です。

## 0. run-state

```bash
ARGS="${ARGUMENTS-}"
PROJECT_ROOT="$(pwd -P)"
if git -C "$PROJECT_ROOT" rev-parse --show-toplevel >/dev/null 2>&1; then
  PROJECT_ROOT="$(git -C "$PROJECT_ROOT" rev-parse --show-toplevel)"
  PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd -P)"
fi
sanitized_cwd="$(printf '%s' "$PROJECT_ROOT" | sed 's|[^a-zA-Z0-9]|-|g')"
PROJECT_MEMORY_DIR="${HOME}/.codex/projects/${sanitized_cwd}/memory"
run_ts="$(date +%Y%m%d-%H%M%S)"
run_feature="$(printf '%s' "$ARGS" | tr -c 'a-zA-Z0-9' '-' | sed -E 's/-+/-/g; s/^-//; s/-$//' | cut -c1-40)"
[ -z "$run_feature" ] && run_feature="instruction-refactor"
RUN_ROOT="${HOME}/.ai-pir-runs"
for run_parent in "$RUN_ROOT" "$RUN_ROOT/$sanitized_cwd"; do
  if [ -e "$run_parent" ] || [ -L "$run_parent" ]; then
    [ -d "$run_parent" ] && [ ! -L "$run_parent" ] || exit 1
  else
    (umask 077; mkdir "$run_parent") || exit 1
  fi
done
RUN_PREFIX="${RUN_ROOT}/${sanitized_cwd}/${run_ts}-${run_feature}"
RUN_DIR="$RUN_PREFIX"
RUN_COLLISION=0
while ! (umask 077; mkdir "$RUN_DIR") 2>/dev/null; do
  [ -e "$RUN_DIR" ] || [ -L "$RUN_DIR" ] || exit 1
  RUN_COLLISION=$((RUN_COLLISION + 1))
  RUN_DIR="${RUN_PREFIX}-${RUN_COLLISION}"
done
echo "PROJECT_ROOT=$PROJECT_ROOT"
echo "PROJECT_MEMORY_DIR=$PROJECT_MEMORY_DIR"
echo "RUN_DIR=$RUN_DIR"
```

sanitized-cwd は `${CODEX_SKILLS_DIR}/pir2/references/sanitized-cwd.md` を SSOT とします。native collaboration と Astra の直接実装では runner 用台帳、固定 fixture、canonical implementation report を作りません。明示的な runner と artifact/provenance が必要な job だけ `${CODEX_SKILLS_DIR}/worker-delegation/SKILL.md` の既存契約を使います。

## 1. 引数と対象

`$ARGUMENTS` から次を解釈します。

- `--scope=user|project|all`。短縮形 `--user` / `--project` / `--all` も同じ
- デフォルトは `user`
- `--no-implement` は測定とレポートだけ
- 位置引数は対象パス1つ。2つ目以降は警告して無視

対象は次です。

- user: `~/.codex/AGENTS.md`、`~/.codex/agents/**/*.toml`、`~/.codex/skills/**/SKILL.md`、`~/.agents/skills/**/SKILL.md`、`~/.claude/CLAUDE.md`、`~/.claude/agents/**/*.md`、`~/.claude/skills/**/SKILL.md`、`~/.cursor/agents/**/*.md`、`~/.cursor/skills/**/SKILL.md`
- project: `${PROJECT_ROOT}/AGENTS.md`、`${PROJECT_ROOT}/CLAUDE.md`、`${PROJECT_ROOT}/.claude/CLAUDE.md`、`${PROJECT_ROOT}/.claude/agents/**/*.md`、`${PROJECT_ROOT}/.claude/skills/**/SKILL.md`、`${PROJECT_ROOT}/.agents/skills/**/SKILL.md`、`${PROJECT_ROOT}/.codex/AGENTS.md`、`${PROJECT_ROOT}/.codex/agents/**/*.toml`、`${PROJECT_ROOT}/.codex/skills/**/SKILL.md`、`${PROJECT_ROOT}/.cursor/agents/**/*.md`、`${PROJECT_ROOT}/.cursor/skills/**/SKILL.md`
- all: 両方

列挙は上記の明示 root 内に実在する対象だけに限定し、同じ実体 path は1件に正規化します。生成物は直接編集せず、生成元 SSOT と adapter を特定します。明示パスがある場合は scope 内のその対象だけを変更候補にしますが、重複・SSOT・消費経路の判断に必要な関連ファイルは read-only で調べます。

## 2. 定量測定

`references/official-criteria.md` を読み、対象を `rg --files` / Glob で列挙して次を測定します。独立した user / project の列挙は別 explorer へ並列委譲できますが、単一の小さい対象は Astra が直接測定して構いません。

1. 各ファイルの行数
2. SKILL.md の description 文字数
3. SKILL.md > 500 行
4. description > 1,024 文字、description + when_to_use > 1,536 文字
5. name > 64 文字、name と親ディレクトリ名の不一致
6. 同種ファイルの中央値 × 3 以上の外れ値

測定担当の返却先を `{RUN_DIR}/measurement.md` とし、小さい直接測定でも Astra が同じパスへ作成します。後段の構造判定と最終レポートはこの実在する report を入力にします。定量違反が0件でも構造判定は省略しません。

## 3. 構造判定

`references/checklist.md` と `references/strategies.md` を読み、対象ファイル全件に対して次を判定します。

- 責務越境、SSOT 逸脱、連続5行以上の横断重複、意味的な二重説明
- description の適切性
- user scope に混入した project-specific な固有名
- instruction の消費側が参照先 SSOT を実際に読むか

規模が大きい横断比較は1体の explorer に `{RUN_DIR}/measurement.md`、対象ファイル一覧、scope に対応する SSOT 一覧、判定基準を渡します。返却先は常に `{RUN_DIR}/structure.md` とし、Astra が直接判定する小さい対象でも同じパスへ記録します。後段はこの report を読みます。単一ファイルでは意味的に重複する段落をクラスタ化し、行範囲、固有差分、統合先を報告します。

user scope の固有名判定は全件 grep を独立して行い、履歴・memory と照合して一般ツール名と project-specific leak を区別します。適用後は同じ候補語パターンを全対象へ再実行します。

## 4. レポート

`{RUN_DIR}/measurement.md` と `{RUN_DIR}/structure.md` を統合し、次を提示します。

```markdown
## Instruction Refactor レポート

### スコープ
[user / project / all]、対象 N ファイル

### 公式上限・スキーマ違反
- [path]: [行数 / description / name の違反と閾値]

### 外れ値
- [path]: N 行（中央値の M 倍）

### 構造上の問題
- [path] L[範囲]: [責務越境 / SSOT逸脱 / 重複 / 二重説明] — [理由と整理戦略]

### description / name
- [path]: [問題]

### グローバル汎用性
- [path] L[行]: project-specific な `<名前>`

### 推奨整理
- [優先度、対象、戦略、維持する配達経路]
```

各節が0件なら「なし」と記載します。`--no-implement` ならここで終了し、実装成功とは扱いません。

## 5. 整理の実施

`--no-implement` でなければ、明確に検出でき、要求範囲内で、既存 SSOT と配達経路を保てる整理はレポート後に実施します。候補が複数あることだけを理由に停止しません。互いに排他的な設計案、scope を変える選択、情報損失の判断、外部・本番・破壊的操作が必要な場合だけ、差分と影響を示してユーザー判断を待ちます。任意の追加リファクタや refactor-advisor 提案は適用前にユーザー承認を得ます。

整理前に `references/strategies.md` の性能保全ゲートを適用します。次を満たさない候補は変更せず、「性能保全のため見送り」とレポートします。

- 削除対象と同等以上の SSOT が実在する
- 消費する agent / skill がその SSOT を読む手順を持つ
- subagent へ渡す query、出力形式、必須チェックが配達経路から消えない
- 意味的重複の統合では各箇所の固有情報の和集合を保持できる

戦略の選択は `references/strategies.md` を正とします。公式超過・DRY は参照化、SSOT 逸脱・責務越境は正しい所有先への移動、意味的重複は情報点包含チェック付きの統合、description は `/skill-creator` の最適化、固有名混入は適切な scope への移動または参照化を基本にします。

### 実装経路

Astra は密結合度、難度、所有境界から直接実装、worker、expert / expert_max を選びます。委譲時は候補、確認済み事実、排他的所有範囲、維持する制約、変更禁止範囲、終了条件、焦点を絞った確認、返却事項を短く渡します。独立したファイルだけを並列化し、共有インターフェースや同じファイルの変更は直列化します。

Astra は `git status -sb`、対象 diff、実在する変更ファイル、候補ごとの確認結果から受入を判定します。worker の自己申告や終了コードだけを根拠にしません。入力不足、要件未決定、権限、環境、CLI failure は actor の能力不足ではありません。実測した capability / local-reasoning 不足がある場合だけ expert へ切り替え、自動 fallback は行いません。

明示的な runner job だけ、その job に必要な raw/canonical report、pre/post/CLAIMED、provenance、既存 ledger schema を worker-delegation の SSOT に従って使います。通常の native/direct job に未生成 index、artifact、固定8 fixtureを要求しません。runner の security、権限、path、fail-closed の検査は省略しません。

## 6. リスクに応じた確認

変更が影響する挙動と失敗時の実害から確認を選びます。

- 対象 diff、frontmatter、Markdown、参照先の存在、name / description / 行数を確認する
- 生成元を変えた場合は必要な adapter を再生成し、対応する生成物を確認する
- 削除・統合した語句は同一ファイルと対象全件を再 grep し、意図しない残骸または消失がないことを確認する
- SSOT 移動では消費側からの到達性と情報点包含を確認する
- OS / security / 権限、実行経路、データ損失へ影響する場合は対応する安全・回帰検証を必ず行う

reviewer は実リスクのある観点だけを使います。たとえば挙動・配達経路は correctness、SSOT・生成経路は consistency / architecture、権限・秘密情報・実行設定は security です。複数の独立観点は並列化できます。全5観点の固定、Fan-Out 宣言、観点数不一致による完了取消は行いません。

テストは影響する挙動を検証する既存 check、構文・設定検証、必要な回帰テストを選びます。文書だけの小変更に独立 tester や無関係な全テストを一律要求しません。独立判定が具体的な実害を検出できる変更では tester を使います。

FAIL 時は根本原因と影響範囲を特定して修正し、影響を受けた観点・検証だけを再実行します。以前 PASS した無関係な reviewer / tester を機械的に全再実行しません。安全に進められない同一 blocker が続く場合は実測結果と必要な判断をユーザーへ返します。

本番変更、外部送信、破壊的操作、OS / security / 権限境界の変更には別途必要な明示承認を得ます。

## 7. 完了サマリー

変更前後を再測定し、次を提示します。

```markdown
## Instruction Refactor 完了サマリー

### 変更ファイル
- [path]: Before X 行 → After Y 行

### 新規 references
- [path]: N 行

### 達成した整理
- 500行超過: N → M
- DRY違反: N → M
- SSOT逸脱: N → M
- 配達経路: [維持を確認した内容]

### 確認
- [実行した測定・レビュー・テストと結果]
- 未確認事項: [なければ「なし」]
```

## 不変条件

- `agents/*.md` の `<!-- CORE -->` 内はユーザー承認なしに変更しない
- 生成物は手書きせず、生成元 SSOT と adapter を変更する
- dead code を削除した後は同じキーワードを対象全体で再検索する
- 大きな構造変更は作業単位と所有範囲を明確にし、必要なら `/pir2` を使う
- 本スキルと `references/` も同じ基準の対象に含める
