# Anthropic 公式の肥大化に関する基準と引用

調査時点: 2026-05-09

## SKILL.md の行数上限（唯一の定量基準）

> "Keep `SKILL.md` under 500 lines. Move detailed reference material to separate files."

出典: [Extend Claude with skills](https://code.claude.com/docs/en/skills)

これが Anthropic 公式が出している唯一の **定量** 基準。500 行を超える `SKILL.md` は references/ に外出しするのが推奨。

## description + when_to_use の文字数

> "Put the key use case first: the combined `description` and `when_to_use` text is **truncated at 1,536 characters** in the skill listing to reduce context usage."

出典: [Extend Claude with skills](https://code.claude.com/docs/en/skills)

## name フィールドの上限

`name` フィールドは最大 **64 文字**。

出典: [Extend Claude with skills](https://code.claude.com/docs/en/skills)

## skill 再添付バジェット（compaction 後）

> "Auto-compaction carries invoked skills forward within a token budget. [...] Claude Code re-attaches the most recent invocation of each skill after the summary, **keeping the first 5,000 tokens of each**. Re-attached skills share **a combined budget of 25,000 tokens**."

出典: [Extend Claude with skills](https://code.claude.com/docs/en/skills)

長い skill は compaction 後に先頭 5,000 トークンしか保持されない。後半に重要情報を置くと失われる。

## CLAUDE.md 肥大化の警告（強い断言）

> "**Bloated CLAUDE.md files cause Claude to ignore your actual instructions!**"
> "If Claude keeps doing something you don't want despite having a rule against it, the file is probably too long and the rule is getting lost."

出典: [Best practices for Claude Code](https://code.claude.com/docs/en/best-practices)

CLAUDE.md には数値基準は提示されていないが、肥大化が「指示を無視させる」という強い因果関係が明示されている。

## CLAUDE.md 設計の Do / Don't

| 含めるべき（✅） | 含めるべきでない（❌） |
|---|---|
| Claude が推測できない Bash コマンド | Claude がコードを読めば分かること |
| デフォルトと異なるコードスタイル | 標準言語規約 |
| リポジトリ etiquette（ブランチ命名等） | 頻繁に変わる情報 |
| アーキテクチャ上の意思決定 | 長い説明・チュートリアル |
| 非自明な動作・gotcha | ファイルごとのコードベース説明 |

出典: [Best practices for Claude Code](https://code.claude.com/docs/en/best-practices)

## subagent 設計指針（数値基準なし）

> "Design focused subagents with single, clear responsibilities rather than trying to make one subagent do everything, which improves performance and makes subagents more predictable."

出典: [Create custom subagents](https://code.claude.com/docs/en/sub-agents)

「1 エージェント 1 責務」の原則。数値基準はないが、責務が複数になっていれば肥大化のシグナル。

## context rot（参考、肥大化が悪い理由の理論的裏付け）

> "Context rot: as the number of tokens in the context window increases, **the model's ability to accurately recall information from that context decreases**."
> "Context, therefore, must be treated as **a finite resource with diminishing marginal returns**."

出典: [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) (2025-09-29)

## 階層メモリの使い分け（肥大化を分散する公式手段）

| 配置先 | 用途 |
|---|---|
| `~/.claude/CLAUDE.md` | 全プロジェクト共通のルール |
| `./CLAUDE.md` | プロジェクトルート。git commit してチームで共有 |
| `./CLAUDE.local.md` | 個人用の上書き（.gitignore に追加） |
| 親ディレクトリ | モノレポで root + サブディレクトリ両方が自動読み込み |
| 子ディレクトリ | そのディレクトリのファイルを扱うときだけオンデマンド |

出典: [Best practices for Claude Code](https://code.claude.com/docs/en/best-practices)

> "CLAUDE.md is loaded every session, so only include things that apply broadly. For domain knowledge or workflows that are only relevant sometimes, use skills instead. Claude loads them on demand without bloating every conversation."

## 著名エンジニアの裏付け（参考）

- **Armin Ronacher** (Flask 作者): 多数作成したスラッシュコマンドのほとんどを未使用化のため **削除した**。"long sessions lead to forgotten context from the beginning"。出典: [Agentic Coding Things That Didn't Work](https://lucumr.pocoo.org/2025/7/30/things-that-didnt-work/) (2025-07-30)
- **Simon Willison**: `@AGENTS.md` import による SSOT 維持を Anthropic Docs から紹介。出典: [A quote from Claude Docs](https://simonwillison.net/2025/Oct/25/claude-docs/) (2025-10-25)
- **"Lost in the Middle"** ([arxiv 2307.03172](https://arxiv.org/abs/2307.03172)): 長文中盤の想起率は冒頭・末尾比で 30% 以上低下する U 字曲線
