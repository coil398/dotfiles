# 指示監査の仕様と出典

仕様上の制約、推奨、runtime固有挙動を分ける。数値や対応fieldが判断を左右するときは現行の公式資料を再確認する。

## Agent Skills標準

[Agent Skills specification](https://agentskills.io/specification):

| 対象 | 制約・目安 |
|---|---|
| `name` | 1〜64文字、小文字英数字とhyphen。先頭・末尾・連続hyphenなし、親directory名と一致 |
| `description` | 1〜1,024文字。何をするか・いつ使うかを示す |
| `compatibility` | 任意。指定時は1〜500文字 |
| `SKILL.md`本文 | 500行未満・5,000 tokens未満を推奨 |
| supporting resource | 必要な場面で読み、Skillの実体から参照を解決 |

任意の `license`、`metadata`、実験的な `allowed-tools` もある。runtime拡張fieldを、標準にないという理由だけで削除しない。

## Claude Code

[Extend Claude with skills](https://code.claude.com/docs/en/skills) では次を確認する。

- `description + when_to_use` は一覧で1,536文字まで。主要用途を先頭に置く。
- full Skill本文はinvoke時にloadされ、後続turnにも残る。
- compaction後は各Skill先頭5,000 tokens、全Skill合計25,000 tokensの範囲で再添付される。
- supporting fileは必要な場面で読む。root Skillは概要とnavigationへ絞り、500行未満を推奨する。
- `disable-model-invocation: true` は明示起動専用、`user-invocable: false` はmodel専用、`context: fork` はsubagent contextで実行する。
- `model`、`effort`、`background`、`paths`、`allowed-tools` などClaude Code固有fieldは、実際の意図とversion対応を確認する。

[Claude Code best practices](https://code.claude.com/docs/en/best-practices) は、常時loadのCLAUDE.mdに、推測できないcommand、defaultと異なる規約、architecture判断、非自明なgotchaを置き、codeから分かる説明・長いtutorial・頻繁に変わる情報を置かないよう勧める。

[Create custom subagents](https://code.claude.com/docs/en/sub-agents) は、agentを単一で明確な責務へ絞ることを勧める。agent本文に一律の数値上限はない。

## Astra記事の使い方

[Rethinking skills and prompts for GPT-6 Astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra) は、短く判別できるdescription、必要時だけ読むreference、過剰なrecipe・常時読込・承認停止・重複検証の見直しを勧める。

この記事はAstra向けの根拠であり、Claude、Sol、Lunaへ機械的に適用しない。Claude固有のSkill lifecycle、Task/Agent機構、explicit invocation、Fable、独立性、実行証跡、安全順序を別に評価する。
