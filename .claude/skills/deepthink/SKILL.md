---
name: deepthink
description: 判断に迷う重要な論点を独立した熟考担当に検討させ、結論と未解決点を整理する。選択肢の比較や設計判断に確信を持てない場合に使う。要件をユーザーと決める場合は brainstorm、計画作成は deepplan。
argument-hint: "[深く考えたい状況・論点] [--panel | --opus-panel]"
---

# Deepthink：Claude Code

**状況・論点**: $ARGUMENTS

共有 package の path は、本 Skill の実体から `../../../.agents/skills/deepthink/` を解決して使います。以下の共有 path はすべてこの解決結果を基準にします。

共有原本 `../../../.agents/skills/deepthink/SKILL.md` を最初にReadし、その手順（方式、rubric、探索、熟考ループ、ユーザーへ返す判断、結果と保存）に従います。続けて `../../../.agents/skills/deepthink/references/model.md` をReadし、モデル指定を確定します。本ファイルは Claude Code 固有の起動方法だけを書きます。

## 担当の起動

- 熟考・統合・十分性確認の担当は `Agent({ subagent_type: "general-purpose", model?, prompt })` で起動します。`model` は既定で `"fable"` とし、ユーザーが別のモデルを名前で指定した場合は model.md の Claude Code 行の識別子を渡します。effortは指定せず、`settings.json` の `modelSettings` に従います。panel では全担当に同じモデルを使い、同じメッセージ内で並べて同時に起動します。
- `--opus-panel` はユーザーが Opus 5.5 と panel を指名したものとして扱い、起動する全担当を `model: "opus"` にします。
- プロンプト先頭に「次の手順ファイルを先にReadし、その範囲だけ行う: <path>」と `SKILL_PATH=<path>` を置き、`../../../.agents/skills/deepthink/references/{deliberator,synthesizer,gate}.md` を解決し、実在を確認した絶対pathを渡します。
- single の熟考担当には `deliberator.md` を `SKILL_PATH` とし、`gate.md` の実在を確認した絶対pathも渡します。Claude Code では担当が起動した探索担当のチャットの返答が担当へ届かないため、担当は探索担当を起動しません。共有原本「必要な探索」の、runtime が担当からの探索担当起動を許さない場合の手順に従い、担当は framing と探索単位・各単位の問いを返して止まり、自分ではファイルを読みません。親はその単位どおりに `.claude/CLAUDE.md`「調査と設計」の起動方法（`subagent_type: "explorer"`）で探索担当を同じメッセージ内で並列に起動し、`../../../.agents/skills/research/references/explorer.md` の絶対pathを渡します。結果は単位を削らず統合せず、`SendMessage` で同じ熟考担当へ渡して熟考を続けさせます。追加探索の要求にも同じ手順で応えます。
- panel の探索担当は `.claude/CLAUDE.md`「調査と設計」の起動方法で親が起動し、本 Skill の実体から `../../../.agents/skills/research/references/explorer.md` を解決した絶対pathを渡します。小さく密結合な確認は親が直接行ってかまいません。
- 全担当のプロンプトに「対象コード・設定・git・記憶を変更しない。結果はチャットで返す」を含めます。
