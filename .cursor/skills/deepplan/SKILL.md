---
name: "deepplan"
description: planner の代わりに deepthink 型ループで実装プランを深く策定し、親または呼び出し元が指定した保存先へ計画を返す。探索・熟考・統合・十分性確認を、設計判断の重さと実害に応じて行う。「深いプラン」「deepplan」「しっかり計画してから実装」「設計判断が重い計画」に使う。ユーザーが /deepplan と入力したら必ずこのスキルを使う。/pir2 --deepplan 等からは PLAN_MODE=deepplan として呼ばれる。
argument-hint: "[計画したいタスク]"
---

<!-- Cursor native overlay; edit here for Cursor mechanics -->

> **Cursor 実行時の注意**
> - 子エージェントは `Task` ツール（`subagent_type`）で起動する。Task / subagent の語彙だけを使う
> - メインエージェントがオーケストレーター。VERDICT ループ・必要なユーザー確認・ループカウンタはメインが保持する
> - 別ランタイム専用のチーム lifecycle / hook API は Cursor の実行契約に含めない。必要なら通常の直列 Task 起動へ縮退する
> - Task の `model` は原則省略/`inherit`（親 Auto）。ベンダー名はハードコードしない
> - Cursor agent の `model` は `inherit` か公式モデル ID。仕事の分類は `role: coding|reasoning`
> - **名前付き例外（本スキル）**: deliberator / synthesizer / gate の Task には必ず `claude-fable-5-1[effort=medium]`（または `--effort=…`）を渡す。agent frontmatter は `inherit` のまま。短名 `fable` 禁止。SSOT: `${CURSOR_SKILLS_DIR}/deepthink/references/fable-model.md`。explorer は `inherit`。失敗時のみ inherit + panel

# Deepplan — 深い実装プラン策定（planner 代替）

**タスク**: $ARGUMENTS

## 実行手順

1. 読み込み済みの本 `SKILL.md` の実体パスから、その親ディレクトリの親を `CURSOR_SKILLS_DIR` として確定する。対象リポジトリの `.cursor/skills` や `.agents/skills` を参照元として推測しない。
2. `${CURSOR_SKILLS_DIR}/deepthink/SKILL.md` を **最初に Read** し、deepthink の探索・熟考・統合・十分性確認を、今回の計画に必要な範囲で適用する。deepthink の固定人数・固定ラウンド・artifact の有無を完了条件にしない。
3. 親 Cursor agent が要件、スコープ、所有境界、実装順、受入条件、未解決事項を保持し、熟考の結果を対象コードと照合して計画へ統合する。計画を別の計画担当へ再委譲しない。
4. 実装計画を保存する場合は、呼び出し元または親が指定した安全な実在保存先の今回未使用の path だけを使う。指定がなければチャットへ要約を返し、`{RUN_DIR}/plan.md` などの path を推測して作らない。

deepthink が `Task` を起動する場合は Cursor の `Task(subagent_type=...)` を使い、モデル指定は通常 Auto / `inherit` とします。Fable の名前付き例外は deepthink が指定する deliberator / synthesizer / gate の3役だけに限定し、explorer・メイン・その他の Task に固定モデルを指定しません。Fable 指定の根拠は `${CURSOR_SKILLS_DIR}/deepthink/references/fable-model.md` とし、短名 `fable` や別ランタイムの lifecycle API を発明しません。

計画の内容・未解決事項・必要なユーザー判断は、実在する根拠と親の受入条件に基づいて返します。deepthink の十分性確認が未達の場合、正しさ・安全性・権限・データ損失に関わる事項を完了扱いせず、追加確認または親からのユーザー判断へ戻します。

## 計画に含める内容

- 目的、非目的、対象ファイル、排他的な所有範囲、変更しない範囲
- 既存実装・既存パターンに基づく実装順序と依存関係
- 各ステップの完了条件、必要な focused check、リスクと復旧方法
- 実装前にユーザー判断が必要な設計・scope・権限・外部状態と、その選択肢
- deepthink で解消できなかった不確実性、追加確認の価値、未完了事項

deepplan は実装・レビュー・テストを完了扱いにせず、計画と実際の受入判断を親へ返します。
