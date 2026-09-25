---
name: jev
description: Jev hooks の運用を支援する。「Jevの状態を診断」「利用量や費用を確認」「モードを変更」「判定を評価」「配備や不具合を調査」といった依頼で使う。該当する依頼では明示的なスキル名がなくても使い、ユーザーが /jev と入力したら必ず使う。
---

# Jev hooks の管理

診断、利用量と推定費用の確認、モード設定、判定の評価、配備と不具合調査を行う。現行 CLI、設定、評価、配備の詳細は [`jev-hooks/README.md`](../../../jev-hooks/README.md) を正本として参照する。

## CLI の場所と基本操作

作業対象の dotfiles リポジトリを特定してから CLI を呼ぶ。スキルファイルの物理パスを解決し、そのパスが `.agents/skills/jev/SKILL.md` なら親階層からリポジトリ root を得る。配置先がリンクの場合もリンク先を解決する。必要なら `jev-hooks/jev.py` を含むリポジトリを確認する。固定の `cwd` や `HOME` から root を推測しない。

```sh
python3 <dotfiles-root>/jev-hooks/jev.py doctor
python3 <dotfiles-root>/jev-hooks/jev.py usage --days 30
python3 <dotfiles-root>/jev-hooks/jev.py usage --days 30 --cwd .
python3 <dotfiles-root>/jev-hooks/jev.py usage --days 30 --json
python3 <dotfiles-root>/jev-hooks/jev.py usage --days 30 --html <output-path>
```

`usage` の日数指定は `--days 30` のようにフラグと値を分ける。費用は既知モデルに対する推定値で、未知モデルの呼び出しは別に表示する。単価設定が必要な場合は README の現行手順と `JEV_HOOKS_INPUT_USD_PER_MILLION` を確認する。

`usage --cwd PATH` は任意の作業ディレクトリに帰属する記録だけを集計する。`.` はコマンドを実行したディレクトリとして解決され、オプションを省略すると全体を表示する。`doctor` は実行中プロセスのcwdに帰属する過去30日の件数と直近policy判定を表示する。判定のmodeは記録時点の値であり、現在の機能有効状態を示すものではない。旧記録などcwdがNULLの行は特定のrepoへ割り当てず、cwd別集計に含めない。cwdはローカルmetadataで、APIへ送るstateには自動追加しない。

## 設定と秘密情報

既定の設定ファイルは `~/.config/jev-hooks/config.json`。`JEV_HOOKS_CONFIG` があればそのパスを使う。環境変数は設定ファイルより優先され、モードは `JEV_HOOKS_MODE=on|observe|off` で指定できる。

モードや他の設定を変更するときは、依頼されたキーだけを更新し、既存の他の値を保って JSON を一時ファイル経由で atomically 書き換える。`TYPESAFE_API_KEY` は環境変数からのみ読み、秘密ファイルを探したり source したりしない。キーの値を保存・表示・ログ出力しない。キーが無い場合 `hook.sh` は Python を起動せず、記録も行わない。

## 判定・記憶関連コマンド

CLI の `skills` は stdin JSON の `query` と任意の `cwd`、`memory-annotate` と `memory-rerank` は `query` と `results`、`memory-classify` は `summary` と `context` を受け取る。スキーマや実行手順は README と CLI の実装で確認する。

`memory-annotate`、`memory-rerank`、`memory-classify` は記憶内容を外部 Jev へ送る。READMEの送信範囲とユーザーの承認範囲を守る。既に承認された接続や実行を毎回確認し直さない。ai-ltm recallは候補を保持して任意の注記を付け、採否はmainが決める。送信先や範囲を拡張する場合はその変更への承認を確認する。

## 評価・配備・障害調査

評価では README の方法に従い、診断と usage の実測をもとに既知費用・未知費用・判定結果を分けて報告する。配備や障害調査では README の該当手順と参照先の公式仕様を確認し、診断結果、実施した操作、未確認事項を明確にする。設定変更が明示的に依頼されている場合は、同じ変更について再承認を求めず実行する。
