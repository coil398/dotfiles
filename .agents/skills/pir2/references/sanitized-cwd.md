# project bucket 名の正規化

共有スキルは、特定ランタイムのホームディレクトリ、メモリ配置、ハーネス用スクリプトを前提にしない。成果物や状態のパスは、現在のランタイムまたは親が明示した実在の値だけを使う。この文書は、path から project bucket 名を導出する場合の正規化式と、導出した path を使うときの安全規則だけを定める。

## 正規化式

```text
sed 's|[^a-zA-Z0-9]|-|g'
```

- ASCII 英数字 (`a-zA-Z0-9`) 以外の **すべての文字**（`/`・`.`・`-`・スペース等）を `-` に置換する
- `/home/user/ghq/github.com/org/repo` は `-home-user-ghq-github-com-org-repo` になる
- 親から検証済みの bucket 名や path を受け取った場合は再計算しない

## 入力ソース

入力ソースは、呼び出し元が path normalization を必要とする場合だけ明示する。

| 系統 | 入力 | 用途 |
|---|---|---|
| **pwd 系** | 呼び出し元が取得した現在ディレクトリの canonical path | 起動時の対象ディレクトリから導出する場合 |
| **target_path 系** | 呼び出し元が渡した対象の canonical path | 現在ディレクトリと異なる対象から導出する場合 |

呼び出し側は、指定した入力の実在性と対象範囲を確認する。正規化を使わない consumer に適用せず、実行環境が path 取得・変換機構を提供する場合はそれを使う。

## 導出した path の安全規則

- bucket 名は、親またはランタイムが明示した実在の base directory の直下だけで使う。base directory を推測して作らない。
- base directory と bucket directory は実体の directory であることを確認し、symlink を辿って別の保存先へ書き込まない。
- run 用の directory は既存 path を再利用せず、排他的な作成が成功した path だけを採用する。
- 同じ対象について異なる正規化規則で作られた既存 directory が並存する場合は、自動マージ・上書き・削除をしない。データ損失の有無を確認し、統合するかは親またはユーザーが判断する。
