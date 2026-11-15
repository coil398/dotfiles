---
name: agy-coding
description: 調査・設計・実装・テストなどのコーディング作業を Antigravity CLI（agy）へ委譲するときに使う。Carbonが調査と計画、Hydrogenが実装、Carbonが差分とテストの最終確認を行う。
---

# コーディング作業の agy 委譲

呼び出し元はコードを自分で書かない。`agy` に調査・計画・実装・確認を委譲し、git操作、PR、受入判定は呼び出し元が行う。

## 流れ

1. Gemini 4 Carbon が対象を調査し、計画を書く（`--model gemini-4-carbon-high`、`--mode plan`）。
2. Gemini 4 Hydrogen が計画どおり実装し、計画で指定した確認を行う（`--model gemini-4-hydrogen-high`、`--mode auto` または `accept-edits`）。
3. Carbon が差分とテスト結果を確認する。指摘があれば Hydrogen が直し、Carbon が再確認する。
4. Argon は使わない。

## 計画の受け渡し

Carbon の PROMPT で計画ファイルの絶対pathを指定し、そこに計画だけを書かせる。Hydrogen の PROMPT に同じpathを含め、その計画を読んで実装するよう指示する。計画ファイルが対象リポジトリの外にあるときは `--add-dir` でそのディレクトリを足す。

計画から実装へ、実装から確認へは新しい起動にする。`--continue` は直近セッションを再開するため、直前が確認側だと実装セッションに戻らない。Hydrogen の修正続きだけ、実装セッションの conversation id を `--conversation` で指定して再開してよい。

## 起動

非対話は `-p`（`--print`）。使える model id は `agy models`、フラグは `agy --help` で確認する。この流れの推論量は model id の suffix（`-high`）で指定する。`--effort` はあるが、標準の流れでは足さない。

`--print-timeout` の省略時は `0` で、ターン完了まで待つ。制限する場合だけ値を付ける。

無人で編集させるときは `--mode auto` または `--mode accept-edits` を付ける。ツール承認もすべて自動にする場合だけ `--dangerously-skip-permissions` を付ける。確認・計画の Carbon には `--mode plan` を明示し、編集させない。

```bash
PLAN="/absolute/path/to/plan.md"

agy -p --model gemini-4-carbon-high --mode plan \
  "対象を調査し、実装計画を ${PLAN} に書く。実装のための編集はしない。"

agy -p --model gemini-4-hydrogen-high --mode auto \
  "計画ファイル ${PLAN} を読んで実装し、計画で指定した確認を行う。commit と push はしない。"

agy -p --model gemini-4-carbon-high --mode plan \
  "計画 ${PLAN} と作業ディレクトリの差分・テスト結果を確認し、指摘を具体的に返す。編集はしない。"
```

指摘があるときは、その内容と計画pathを渡して Hydrogen を再度起動する。直したら Carbon で再確認する。

## 規則

- agy の認証・token ファイルを読まない、コピーしない。
- 呼び出し元はコードを書かない。
- commit、push、PR、最終受入は呼び出し元が行う。agy に git の更新操作を許可しない。
- 無人の `agy` を高い頻度でループしない。
