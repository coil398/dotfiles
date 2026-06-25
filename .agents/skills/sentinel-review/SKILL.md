---
name: "sentinel-review"
description: "変更差分または指定パスを、カテゴリ別のセキュリティ専用subagentで並列レビューする。Phase 1 は sentinel-iac のみを起動し、IaC ファイル (Dockerfile / docker-compose / Terraform / GitHub Actions) の危険設定だけを検出する。"
---

# sentinel-review

AI-sentinel-lens のメインスキル。

ユーザが `/sentinel-review` を呼んだとき、対象スコープを決定し、
カテゴリ別の sentinel-* subagentを並列起動して、
結果を Finding スキーマに正規化した Markdown レポートとして返す。

設計の根拠は [`docs/design/`](../../../docs/design/) を参照。

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

2. **起動するsubagentを選ぶ**
   - Phase 1 では **sentinel-iac のみ**。
   - 対象ファイルに以下のいずれかが含まれる場合のみ起動する:
     - `Dockerfile`, `*.dockerfile`
     - `docker-compose*.yml`, `docker-compose*.yaml`, `compose*.yml`, `compose*.yaml`
     - `*.tf`
     - `.github/workflows/*.yml`, `.github/workflows/*.yaml`
   - 含まれなければ「IaC 対象ファイルなし」と表示してスキップ。

3. **subagentを起動** (Codex subagent, `subagent_type=sentinel-iac`)
   - 入力として「対象ファイルの相対パス一覧」を渡す。
   - 出力契約 (`docs/design/04-prompts-and-redaction.md` の 4.2) と
     Finding スキーマ (`docs/design/03-findings-schema.md`) を厳守するよう明示する。

4. **応答をパース**
   - 応答末尾の ` ```json ... ``` ` ブロックを 1 個だけ取り出して JSON.parse 相当の解釈を行う。
   - パースに失敗した場合は当該エージェントの結果を 0 件扱いにし、
     サマリに「sentinel-iac の応答が解釈できませんでした」と明記する（黙って欠落させない）。

5. **Finding を正規化・統合**
   - `docs/design/03-findings-schema.md` の 3.4 に従って:
     - `detector_id + path + start_line` で重複統合
     - 未知の `category` は `misc` に倒す
     - スキーマに合わない Finding は捨てる（捨てた件数をサマリに記録）
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

- このスキルおよび配下のsubagentは **書き込み権限を持たない**。
  修正は `suggested_patch` の提示で止める。適用したい場合はユーザが本体 Claude に Edit を依頼する。
- 攻撃手順や PoC コードは生成しない。Finding の `rationale` は原理レベルの説明にとどめる。
- 外部ネット呼び出しは Phase 1 では一切行わない（`sentinel-deps` を実装する Phase 6 でのみ限定的に許可）。

## Phase 1 完了の判定

- 自リポジトリで `/sentinel-review` を実行すると、
  対象 IaC ファイルがあれば Finding 入りの Markdown が、
  なければ「対象なし」が返ること。
- sentinel-iac の応答が壊れていてもスキル全体は落ちず、サマリに失敗を記録すること。
