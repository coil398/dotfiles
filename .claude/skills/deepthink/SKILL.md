---
name: deepthink
description: 難しい意思決定や論点を、必要な探索・Fable（またはユーザー指名のOpus 5.5）による独立した熟考・統合・十分性確認へ分けて考える。single/panelの方式を使い、親だけで熟考を完了させない。調査はresearch、実装やbug修正はpir2/debugを使う。ユーザーが /deepthink と入力したときに使う。
argument-hint: "[深く考えたい状況・論点] [--panel | --opus-panel]"
---

# Deepthink — Claude Code

**状況・論点**: $ARGUMENTS

共有 package の path は、本 Skill の実体から `../../../.agents/skills/deepthink/` を解決して使います（通常は `~/.agents/skills/deepthink/`）。以下の共有 path はすべてこの解決結果を基準にします。

共有原本 `../../../.agents/skills/deepthink/SKILL.md` を最初にReadし、その手順（方式、rubric、探索、熟考ループ、ユーザーへ返す判断、結果と保存）に従います。続けて `../../../.agents/skills/deepthink/references/fable-model.md` をReadし、Claude Code 行のモデル指定を確定します。本ファイルは Claude Code 固有の起動方法だけを書きます。

## 担当の起動

- 熟考・統合・十分性確認の担当は `Agent({ subagent_type: "general-purpose", model: <fable-model.md の Claude Code 行の識別子>, prompt })` で起動します。既定は `claude-fable-5-1`、ユーザーが Opus 5.5 を指名したときは `claude-opus-5-5` です。panel では全担当に同じ識別子を使い、同じメッセージ内で並べて同時に起動します。
- `--opus-panel` はユーザーが Opus 5.5 と panel を指名したものとして扱い、起動する全担当を `model: "claude-opus-5-5"` にします。
- effort は Agent 呼び出しごとに指定できず、親セッションの値を引き継ぎます。深く考えさせたい場合は、ユーザーが実行前に親で `/effort` を上げます。
- プロンプト先頭に「次の手順ファイルを先にReadし、その範囲だけ行う: <path>」と `SKILL_PATH=<path>` を置き、`../../../.agents/skills/deepthink/references/{deliberator,synthesizer,gate}.md` を解決し、実在を確認した絶対pathを渡します。
- 探索担当は `Agent({ subagent_type: "general-purpose", prompt })` を `model` 省略で起動し（`.claude/CLAUDE.md`「モデルの使い分け」）、本 Skill の実体から `../../../.agents/skills/research/references/explorer.md` を解決した絶対path（通常は `~/.agents/skills/research/references/explorer.md`）を渡します。小さく密結合な確認は親が直接行ってかまいません。
- 全担当のプロンプトに「対象コード・設定・git・記憶を変更しない。結果はチャットで返す」を含めます。
