---
name: "pir2async"
description: "PIR²の実験入口。CursorではチームAPIが利用できないため、同じ引数を通常の /pir2 Taskワークフローへ明示的に縮退して実行する。通常版との差異を誤って捏造しない。ユーザーが /pir2async と入力したら必ず使う。"
argument-hint: "[タスクの説明] [--deepplan]"
---

<!-- Cursor native overlay: seeded from .agents/skills; edit here for Cursor mechanics -->

# PIR² Async — Cursor fallback

タスク: $ARGUMENTS

Cursor runtimeにはチームの作成・直接対話・終了を管理するAPIがありません。本スキルは通常の `/pir2` へ明示的に縮退し、利用不能なチーム手順を模倣しません。

## 実行手順

1. 読込済みの本SKILL.md実体pathから、その親ディレクトリの親を `CURSOR_SKILLS_DIR` として確定します。target repository内の `.cursor/skills` は参照元として仮定しません。
2. `${CURSOR_SKILLS_DIR}/pir2/SKILL.md` を全文 Readします。
3. `$ARGUMENTS` をそのまま渡し、pir2の Plan → Implement → Review → Test → Retrospect を最初から最後まで実行します。
4. 子はpir2の指示どおり `Task`（`subagent_type`）で起動し、通常のTaskで `model` は省略するか `inherit` として親Autoに従います。Codex用モデル名を流用しません。
5. `--deepplan` / `deepplan` がある場合はpir2からdeepplanを実行します。`claude-fable-5-1[effort=…]` overrideは deliberator / synthesizer / gateのTaskだけに限定し、メインと他TaskはAuto / `inherit` を維持します。
6. review/test/再確認、権限確認、破壊的変更の独立検証はpir2のリスク相応ルールをそのまま適用します。縮退を理由に品質・安全境界を弱めません。

## 完了報告

pir2の完了報告に次を追加します。

- requested workflow: `pir2async`
- executed workflow: `pir2`（Cursor fallback）
- fallback reason: Cursor runtimeにチームlifecycle APIがない
- team内対話・team shutdown・async比較指標: 未実行

未実行のチーム連携、reviewer、tester、artifact、VERDICTを作ったことにしません。通常版との品質比較は同一のpir2実行なので成立しないと明記します。
