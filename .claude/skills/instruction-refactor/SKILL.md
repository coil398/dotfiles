---
name: instruction-refactor
description: 既存の CLAUDE.md / agents / skills の肥大化を Anthropic 公式基準（SKILL.md ≤ 500 行、bloat warning）と構造的悪さ（責務越境 / SSOT 逸脱 / DRY 違反 / 二重説明）の観点で検出し、Progressive Disclosure / 共通骨格の references 外出し / SSOT 参照への置換などで実際に整理する（検出だけで終わらない）。「instruction file 整理」「肥大化リファクタ」「skill の長さ大丈夫？」「定期メンテ」「棚卸し」「audit」「instruction bloat」「.claude/ 整理」「CLAUDE.md 削って」といった要望や、agents / skills を編集した直後の整合性確認にも使う。コードのリファクタ提案を出す refactor-advisor とは対象が違う（こちらは instruction file 専用、向こうはソースコード専用）。ユーザーがこれらに該当することを明示的に名指ししなくても積極的に使う。ユーザーが /instruction-refactor と入力したら必ずこのスキルを使う。
argument-hint: [--scope=user|project|all] [--no-implement] [path]
---

# Instruction Refactor — instruction file 肥大化リファクタリング

CLAUDE.md / agents/*.md / skills/**/SKILL.md を **Anthropic 公式基準** と **構造的悪さ**（責務越境 / SSOT 逸脱 / DRY 違反 / 二重説明）の観点で検出し、Progressive Disclosure / 共通骨格の references 外出し / SSOT 参照への置換などで実際に整理します。**検出だけで終わらせず、改善実施までを 1 セットとするスキル** です。

> ℹ️ コードのリファクタ提案を出す `refactor-advisor` とは対象が違います（こちらは instruction file 専用、向こうはソースコード専用）。

このスキル本体（= メイン Claude）がオーケストレーターとなり、`explorer` を `Agent` ツールで起動して測定・分析を行い、改善は本体が直接 Edit/Write で実施します。

判断基準・整理戦略・公式引用は `references/` 配下にオンデマンドで切り出してあり、SKILL.md 本体は薄く保つ設計です。

引数: $ARGUMENTS

---

## ステップ 1: 引数解釈

`$ARGUMENTS` を bash で解釈し、スコープ・実装フラグ・対象パスを分離してください:

```bash
ARGS="$ARGUMENTS"
SCOPE="user"
IMPLEMENT="true"
TARGET_PATH=""

for token in $ARGS; do
  case "$token" in
    --scope=*) SCOPE="${token#--scope=}" ;;
    --no-implement) IMPLEMENT="false" ;;
    --user) SCOPE="user" ;;
    --project) SCOPE="project" ;;
    --all) SCOPE="all" ;;
    *)
      if [ -z "$TARGET_PATH" ]; then
        TARGET_PATH="$token"
      fi
      ;;
  esac
done

echo "SCOPE=$SCOPE"
echo "IMPLEMENT=$IMPLEMENT"
echo "TARGET_PATH=${TARGET_PATH:-（指定なし、SCOPE 全体を対象）}"
```

スコープのデフォルトはユーザースコープ（`~/.claude/` 配下）。プロジェクト固有の `.claude/` 配下を含めたい場合は `--scope=project` または `--scope=all` を指定する。

---

## ステップ 2: 対象ファイルの探索と測定（公式定量基準の照合）

`explorer` エージェントを `Agent` ツールで起動して測定を委譲してください:

- **model**: `haiku`（広く浅い列挙が中心）
- **プロンプトに含めるパラメータ**:
  - `SCOPE`（user / project / all）
  - `TARGET_PATH`（指定があれば、ない場合はスコープ全体）
  - 「以下を測定してレポートを返してください:
    1. SCOPE に応じた対象ファイルを Glob で列挙する
       - `user`: `~/.claude/CLAUDE.md`, `~/.claude/agents/*.md`, `~/.claude/skills/**/SKILL.md`
       - `project`: `${PWD}/.claude/CLAUDE.md`, `${PWD}/.claude/agents/**/*.md`, `${PWD}/.claude/skills/**/SKILL.md`
       - `all`: 両方
    2. 各ファイルの行数を `wc -l` で計測
    3. 各 SKILL.md の `description` 文字数を計測
    4. 公式定量基準・スキーマ制約の違反を検出（SKILL.md > 500 行 / description > 1,024 文字 = ロード不可 / description + when_to_use > 1,536 文字 = listing 切り捨て / name > 64 文字 / name と親ディレクトリ名の不一致 = ロード不可）
    5. 平均からの外れ値を検出（同種ファイルの中央値 × 3 以上を外れ値とみなす）
    6. 計測結果を表形式で返す」
  - 「判断基準は `~/.claude/skills/instruction-refactor/references/official-criteria.md` を Read して使うこと」

返ってきたレポートに肥大化候補が **0 件** なら、ステップ 4 で「肥大化なし」と報告してステップ 5・6 をスキップする。

---

## ステップ 3: 構造的悪さの判定（責務越境 / SSOT 逸脱 / DRY 違反 / 二重説明）

ステップ 2 で「肥大化が疑われる」と判定されたファイル群について、`explorer` エージェントを再度起動して構造的悪さを判定してください:

- **model**: `sonnet`（深い読解が必要）
- **プロンプトに含めるパラメータ**:
  - 対象ファイルの絶対パス一覧（ステップ 2 の結果から）
  - 「`~/.claude/skills/instruction-refactor/references/checklist.md` の判定 2（責務越境 / SSOT 逸脱 / DRY 違反 / 二重説明）と判定 3（description 適切性）と判定 4（グローバル汎用性）に従い、各ファイルの構造的悪さを検出してください。検出した場合は『該当箇所の行範囲』『種別』『理由』『推奨整理戦略』を報告してください」
  - 「整理戦略の詳細は `~/.claude/skills/instruction-refactor/references/strategies.md` を参照すること」
  - SCOPE に応じた SSOT ファイル一覧を渡す（例: `/skill-creator` の SKILL.md / `~/.claude/agents/reviewer.md` / `~/.claude/CLAUDE.md` 等。判定 2b の SSOT 逸脱検出に使う）

DRY 違反を疑う場合は、対象ファイル群を pairwise で比較して連続 5 行以上の重複を検出するよう指示する。

**`TARGET_PATH` に単一ファイルが指定された場合**は、判定 2d を「意味的重複クラスタリング」として重点実行するよう explorer に指示する: 「対象ファイルを通読し、意味的に重複する段落 / ルール / 手順をクラスタにグルーピングし、各クラスタについて『重複箇所の行範囲一覧』『各箇所の固有差分の有無』『統合先の推奨』を報告してください。字句一致だけでなく言い換え・パラフレーズによる重複も拾うこと」。これは単一ドキュメントを加筆し続けて生じた重複の正規化（戦略 6）が目的。

---

## ステップ 4: ユーザーへのレポート提示

以下のフォーマットでレポートを表示してください:

```
## Instruction Refactor レポート

### スコープ
[user / project / all]、対象 N ファイル

### 公式上限超過・スキーマ違反（判定 1）
- [ファイルパス]: N 行（公式上限 500 行を X% 超過）
- [ファイルパス]: description M 文字（フィールド上限 1,024 文字を超過 = ロード不可 / または listing truncate 1,536 文字を超過）
- [ファイルパス]: name が親ディレクトリ名と不一致（`<name>` vs `<dir>` = ロード不可）
（なければ「なし」）

### 平均外れ値（判定 1 派生）
- [ファイルパス]: N 行（同種ファイル中央値の M 倍）
（なければ「なし」）

### 構造的悪さ（判定 2）
- [ファイルパス] L[行範囲]: 種別 = 責務越境 / 理由: [...] / 推奨戦略: [...]
- [ファイルパス] L[行範囲]: 種別 = SSOT 逸脱（参照先: [SSOT パス]） / 理由: [...]
- [ファイル A] と [ファイル B] L[行範囲]: 種別 = DRY 違反 / 重複行数: N / 推奨戦略: [...]
- [ファイルパス]: 種別 = 意味的重複クラスタ / 重複箇所: L[範囲1], L[範囲2], … / 固有差分: あり/なし / 統合先: L[範囲] / 推奨戦略: 戦略 6
（なければ「なし」）

### description / name 不適切（判定 3）
- [ファイルパス]: pushy パターン未準拠（自然言語トリガー語句が N 個、推奨 3〜5）
（なければ「なし」）

### グローバル汎用性違反（判定 4、ユーザースコープのみ）
- [ファイルパス] L[行]: プロジェクト固有名 `<名前>` を検出
（なければ「なし」）

### 推奨整理戦略
[戦略選択フローチャートに従い、優先度順に提示。strategies.md 参照]
```

---

## ステップ 5: 改善ゲート（IMPLEMENT=true の場合のみ）

`IMPLEMENT=false`（`--no-implement` 指定）の場合はステップ 5・6 をスキップしてレポートのみで終了する。

`IMPLEMENT=true` の場合、ユーザーに以下の選択肢を提示して応答を待つ:

```
検出の結果、N 件の改善候補があります。どう進めますか？

- all: すべての候補を改善する
- 1,3,5: 番号指定で部分改善
- none: 改善せずレポートのみで終了
- pir2: 改善作業を /pir2 で進める（5 ファイル以上の影響なら推奨）
```

---

## ステップ 6: 改善実施（all / 番号指定の場合のみ）

`pir2` が選ばれた場合は `Skill` ツールで `pir2` を起動し、本スキルでの実施は終了する。

`all` または番号指定の場合、メイン Claude が直接 Edit/Write で修正する。`references/strategies.md` の戦略選択フローチャートに従って整理戦略を適用:

- 公式上限超過 → 戦略 2 (Progressive Disclosure、`references/` への外出し)
- DRY 違反 → 戦略 2 (共通骨格を 1 ファイルに集約、両方から参照)
- SSOT 逸脱・責務越境 → 戦略 1 (抜粋を削除し参照のみに)
- 二重説明 / 意味的重複 → 戦略 6 (和集合で 1 箇所に統合 → 統合前の各 assertion が統合後に全部入っているか **情報点包含チェック** → diff 提示してから確定。要約・圧縮はしない)
- description 不適切 → ユーザーに `/skill-creator` の Description Optimization 実行を提案
- プロジェクト固有名混入 → プロジェクトスコープに移すか、本文ではなく参照に変える

実施後、変更前後の行数を比較してサマリーをユーザーに提示:

```
## Instruction Refactor 完了サマリー

### 変更ファイル
- [ファイルパス]: Before X 行 → After Y 行（Z 行削減）

### 新規 references/
- [ファイルパス]: N 行

### 達成した整理
- 公式 500 行ライン: N ファイル超過 → M ファイル超過
- DRY 違反: N 箇所 → 0
- SSOT 逸脱: N 件 → 0

### 次のステップ
- git commit で変更を保存（個別 git add でファイルを指定）
- /skill-creator の Description Optimization が必要な skill: ...
- (5 ファイル以上に影響した場合): /pir2 でレビューを通すことを検討
```

---

## 注意事項

- **CORE セクションは触らない**: `agents/*.md` の `<!-- CORE -->` で囲まれたセクションは変更禁止（retrospector のメタモードでもユーザー承認が必要)
- **削除する前に SSOT が存在することを確認**: 抜粋を消す前に、参照先 SSOT を Read して同等以上の情報があることを必ず確認
- **大きな構造変更は `/pir2` へ**: 5 ファイル以上に影響する大規模リファクタは独断せず `/pir2` 経由でレビューを通す
- **本スキル自身もリファクタ対象**: SKILL.md と `references/` も他の skill と同じ基準でリファクタ対象に含める（自己言及性）
