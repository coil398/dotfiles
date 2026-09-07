---
name: "sentinel-review"
description: 変更差分または指定パスのIaC（Dockerfile、docker-compose、Terraform、GitHub Actions）への書き込みを実行せず、共通Finding schemaとredaction基準に従って検査する。必要な確認は標準子の担当ラベルsentinel-iacへ委任する。ユーザーが /sentinel-review と入力したら必ず使う。
---

# sentinel-review

ユーザが `/sentinel-review` を呼んだとき、対象スコープを決定する。必要なIaC確認は標準子の担当ラベル`sentinel-iac`へ委任し、返却されたFindingを親が正規化・統合してMarkdownレポートへ集約する。親が直接確認する場合も同じ資料とFinding形式を使う。

親は入出力の確認と結果集約のため、同directoryの`references/findings-schema.md`の「JSON契約」節と`references/redaction.md`、全体の結果原本`../code-review-guidance/references/result-contract.md`を読む。検出の専門本文は実際の評価者が読む。対象repoに契約文書があると仮定しない。

## 引数

- `<path>` (任意): 対象パス。指定すればそのパス以下が対象。
- `--diff <base>..<head>` (任意): 差分の base..head を明示。
- `--severity-min <level>` (任意, 既定 `low`): この閾値未満の Finding は出さない (`info` は別途常に折りたたみ)。

引数を取らない場合は、親が確定した対象repoの`git status`と`git diff`から変更ファイルを拾う。親が指定したscope、base/head、untrackedの境界を維持する。

## 手順

1. **対象スコープを決定**
   - `<path>` 指定があればそのパス以下を対象（Glob 展開、ただし `.gitignore` 尊重）。
   - `--diff` 指定があれば `git diff --name-only <base>..<head>` で対象ファイル列挙。
   - どちらも無ければ `git status --porcelain` と `git diff --name-only` で変更ファイルを取得。
   - 対象が0件なら、対象なしの理由と`COVERAGE: none`、`VERDICT: NOT_APPLICABLE`を返す。取得失敗やscope不明は対象なしにしない。

2. **検査担当を決める**
   - 対象ファイルに以下のいずれかが含まれる場合のみ、標準子の担当ラベル`sentinel-iac`へ検査を委任する:
     - `Dockerfile`, `*.dockerfile`
     - `docker-compose*.yml`, `docker-compose*.yaml`, `compose*.yml`, `compose*.yaml`
     - `*.tf`
     - `.github/workflows/*.yml`, `.github/workflows/*.yaml`
   - 含まれなければ「IaC 対象ファイルなし」と表示してスキップ。

3. **検査を実行**
   - `sentinel-iac`を利用中runtimeの標準起動機構で起動する。固定modelや固定人数をこのSkillで決めない。
   - 入力として「対象ファイルの相対パス一覧」と、`findings-schema.md`、`redaction.md`の実体絶対pathを渡す。委任された子は受け取った専門資料を自身でReadしてから検査する。
   - 親が直接確認する場合は、親自身が上記2つの専門資料と共有結果原本`../code-review-guidance/references/result-contract.md`をReadする。

4. **応答をパース**
   - 応答末尾の ` ```json ... ``` ` ブロックを 1 個だけ取り出して JSON.parse 相当の解釈を行う。
   - パースに失敗した場合はFinding 0件として表示してよいが、検査完了とは扱わず、`COVERAGE: partial`または`none`、失敗理由、未確認範囲をサマリに明記する。

5. **Finding を正規化・統合**
   - `references/findings-schema.md`に従って:
     - `detector_id + path + start_line` で重複統合
     - 未知の`category`は`misc`に倒し、変換件数を記録する
     - スキーマに合わない Finding は捨てる（捨てた件数をサマリに記録）
   - `severity` 降順、次に `priority` 降順で並び替え。
   - `--severity-min`未満は出力対象から外すが、除外件数をサマリへ記録する。
   - 子が返す固有Finding JSONは保持したまま、親がこの手順でMarkdownへ集約する。全体のCOVERAGE/VERDICTは共有結果原本に従って、取得失敗・未確認・Findingの有無を統合する。

6. **Markdown レポートを出力**
   - 冒頭にサマリ:
     - severity 別件数
     - スキップ/失敗エージェント
     - スキーマ違反で捨てた件数
   - 各 Finding は次の体裁で表示:
     - 見出し: `#### [<SEVERITY>] <title>`
     - 場所、原因、影響、修正案、優先度、信頼度、由来エージェント
     - `suggested_patch` があれば ` ```diff ` ブロック
     - `recurrence_checklist` は `<details>` で折りたたみ
   - `confidence=low` と `severity=info` の Finding は `<details>` で折りたたむ。

## 制約

- このスキルおよび配下のsubagentは **書き込みを実行しない**。技術的にread-onlyであることは、runtimeの実効権限を確認した場合だけ主張する。修正は`suggested_patch`の提示で止める。apply、deploy、workflow実行、外部pushは行わない。
- 攻撃手順や PoC コードは生成しない。Finding の `rationale` は原理レベルの説明にとどめる。
- 外部ネット呼び出し（curl、wget、git fetch等）は行わない。secret、個人情報、長いランダム文字列は`references/redaction.md`に従いマスクする。

## 完了の判定

- 対象repoで `/sentinel-review` を実行すると、
  対象 IaC ファイルがあれば Finding 入りの Markdown が、
  なければ「対象なし」が返ること。
- sentinel-iacの応答が壊れていてもスキル全体は落とさず、サマリに失敗を記録し、未確認をPASSで補完しないこと。
