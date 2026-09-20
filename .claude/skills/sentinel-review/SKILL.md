---
name: sentinel-review
description: Dockerfile・Compose・Terraform・GitHub Actionsの差分または指定pathをread-onlyで検査し、Finding schemaで結果を返す。
---

# sentinel-review

ユーザが `/sentinel-review` を呼んだとき、対象スコープを決定し、
該当する `sentinel-iac` サブエージェントを起動して、
結果を Finding スキーマに正規化した Markdown レポートとして返す。

## 引数

- `<path>` (任意): 対象パス。指定すればそのパス以下が対象。
- `--diff <base>..<head>` (任意): 差分の base..head を明示。
- `--severity-min <level>` (任意, 既定 `low`): この閾値未満の Finding は出さない (`info` は別途常に折りたたみ)。

引数を取らない場合は `git status` と `git diff` から変更ファイルを拾う。

## 手順

1. **対象スコープを決定**
   - `<path>` 指定があればそのパス以下を対象（Glob 展開、ただし `.gitignore` 尊重）。
   - `--diff` 指定があれば `git diff --name-only <base>..<head>` で対象ファイル列挙。
   - どちらも無ければ `git status --porcelain` と `git diff --name-only` で変更ファイルを取得。
   - 対象が 0 件なら「対象なし」と表示して終了。

2. **起動するサブエージェントを選ぶ**
   - Phase 1 では **sentinel-iac のみ**。
   - 対象ファイルに以下のいずれかが含まれる場合のみ起動する:
     - `Dockerfile`, `*.dockerfile`
     - `docker-compose*.yml`, `docker-compose*.yaml`, `compose*.yml`, `compose*.yaml`
     - `*.tf`
     - `.github/workflows/*.yml`, `.github/workflows/*.yaml`
   - 含まれなければ「IaC 対象ファイルなし」と表示してスキップ。

3. **サブエージェントを起動** (Agent ツール, `subagent_type=sentinel-iac`)
   - 入力として「対象ファイルの相対パス一覧」を渡す。
   - `sentinel-iac` 定義の出力契約とFindingスキーマに従うよう明示する。

4. **応答をパース**
   - 応答末尾の ` ```json ... ``` ` ブロックを 1 個だけ取り出して JSON.parse 相当の解釈を行う。
   - パースに失敗した場合は当該エージェントを **失敗・未確認** とし、Finding 件数を 0 と確定しない。
     サマリに「sentinel-iac の応答が解釈できず、対象は未確認」と明記する。

5. **Finding を正規化・統合**
   - 次の規則で正規化する:
     - `detector_id + path + start_line` で重複統合
     - 未知の `category` は `misc` に倒す
     - スキーマに合わない Finding は出力対象から外し、件数と「一部未確認」をサマリに記録
   - `severity` 降順、次に `priority` 降順で並び替え。
   - `--severity-min` 未満は出力対象から外す。

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

- このスキルと配下のサブエージェントは **行動上 read-only** とし、利用可能なツールに書き込み能力があっても対象ファイルを変更しない。
  実効権限は active settings とツール定義で確認し、指示文だけから権限が無いと断定しない。修正は `suggested_patch` の提示で止める。
- 攻撃手順や PoC コードは生成しない。Finding の `rationale` は原理レベルの説明にとどめる。
- 外部ネット呼び出しは行わない。

## 完了の判定

- 自リポジトリで `/sentinel-review` を実行すると、
  対象 IaC ファイルがあれば Finding 入りの Markdown が、
  なければ「対象なし」が返ること。
- sentinel-iac の応答が壊れていてもスキル全体は落ちず、サマリに失敗と未確認範囲を記録し、0 Finding や安全確認済みと判定しないこと。
