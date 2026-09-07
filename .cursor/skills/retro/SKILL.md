---
name: "retro"
description: "実際の作業結果からパターンを汎化し、次回に役立つ改善を提案する。振り返り・ふりかえり・retrospective・改善サイクル・エージェント定義の見直し・パターン分析に使う。`--meta` と `--dream` はユーザーが明示した場合だけ使う。ユーザーが /retro と入力したら使う。"
argument-hint: "[--meta] [--dream] [対象プロジェクトのパス]"
---

<!-- Cursor native overlay: Cursor の Task 起動方式だけを定義する -->

# Retro — Cursor の親向け振り返り

親が実際の作業結果を整理し、独立した分析に利益があるときだけ Cursor の標準 `Task` を使います。親が対象、入力、保存、承認、統合、最終判断を持ちます。Cursor の runtime 設定で利用できる標準起動値を使い、model や effort をこの Skill に固定しません。

## 0. モードと入力

`$ARGUMENTS` は Cursor の構造化された引数・フラグとして解釈します。raw 文字列しか受け取れない場合も、引用を認識する parser を使い、shell の word splitting、glob、`eval` で再解釈しません。`--dream` は `--meta` より優先し、対象を省略した場合は現在の対象を使います。

親は対象プロジェクトと、今回使うログ・差分・計画・検証結果を実在確認します。`PROJECT_MEMORY_DIR`、`RUN_DIR`、`REGISTRY_PATH`、`OBSERVATION_LOG_PATH`、`EXPERIMENTAL_PATH`、`RETRO_REPORT_PATH` は、親が明示し実在確認できたものだけを渡します。Cursor の home 配下、sanitized 名、未生成の report は推測しません。回数や verdict も実測値が渡された場合だけ扱い、未指定を 0 / PASS としません。

## 1. 分析担当の選択

通常モードでは `Task` を必要なときだけ一体起動します。起動時には親が確認済みの対象版、所有範囲、入力 path、変更禁止範囲、返却方法と、実在する次の reference path を明示します。

- 通常: loaded native Skill directory から `../../../.agents/skills/retro/references/retrospector.md` を解決し、実在確認した path
- `--meta`: loaded native Skill directory から `../../../.agents/skills/retro/references/meta-retrospector.md` を解決し、実在確認した path
- `--dream`: loaded native Skill directory から `../../../.agents/skills/retro/references/meta-retrospector.md` を解決し、実在確認した path

reference は上記の shared path が実在しない場合だけ、親が確認した別配置の絶対 path を使います。対象リポジトリ内の同名 path や home 配下の候補は推測しません。子には親用の再委任手順を渡さず、子が report・memory・registry を保存しないことを明示します。標準 `Task` が使えない場合、独立分析が依頼の必須条件なら未実行として返し、親の直接確認だけで完了扱いにしません。それ以外では親が同じ範囲を直接確認できます。

## 2. モード別の範囲

- 通常モード: 手戻り、見逃し、不要な確認、再利用できる学び、残るリスクを根拠付きで整理する。
- `--meta`: ユーザーが明示した workflow 骨格の改善候補だけを整理する。通常の振り返りから骨格変更へ拡張しない。
- `--dream`: 親が渡した既存 registry の重複、陳腐化、統合時のデータ損失リスクを整理する。registry の自動削除・上書き・移動は行わない。

Task の結果は親へ返します。親が保存を必要と判断した場合だけ、明示された専有 path と既存の保存方針に従います。提案と適用、registry の読取と更新、バックアップと復元を同じ操作として扱いません。承認が必要な変更は、対象、影響、rollback を提示して親またはユーザーの判断を待ちます。

## 3. 結果

親は確認できた事実、学び、改善候補、残るリスク、未確認範囲を提示します。report を実際に保存した場合だけ path を示します。子や親は未確認を指摘なし・成功として扱わず、追加 Task、未指定 path、権限変更、commit、push を行いません。
