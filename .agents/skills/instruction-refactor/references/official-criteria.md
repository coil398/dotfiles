# 指示監査の仕様と出典

仕様上の制約、推奨目安、runtime 固有の挙動を区別する。サイズだけで性能やロード成否を断定せず、対象 runtime の公式資料と実際の validator を照合する。

## 共通形式

[Agent Skills specification](https://agentskills.io/specification) の基準:

| 対象 | 制約・目安 |
|---|---|
| `name` | 1〜64文字、小文字英数字とハイフン。先頭・末尾・連続ハイフンなし、親ディレクトリ名と一致 |
| `description` | 1〜1,024文字。何をするか・いつ使うかを示す |
| `compatibility` | 任意。指定する場合は1〜500文字 |
| `SKILL.md` 本文 | 500行未満・5,000 tokens未満を推奨。ロード上限ではない |
| 補助資料 | 必要な場面で読み、参照は skill の実体から解決する |

標準には任意の `license`、`metadata`、実験的な `allowed-tools` もある。runtime の拡張フィールドを、標準にないという理由だけで削除しない。標準違反と、実際に観測したロード失敗は分けて報告する。

## Codex

[Build skills](https://learn.chatgpt.com/docs/build-skills) は、起動時に名前・説明・path を提示し、採用時に本文を読む段階的開示を説明している。初期一覧は context window の最大2%、不明時は8,000文字の予算を使い、数が多いと説明を短縮し、場合によってはスキルを省略する。この一覧予算を本文の上限と混同しない。

[Rethinking skills and prompts for GPT-6 Astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra) を、発火条件と指示の必要性を見直す根拠として使う。短い説明で適用範囲を区切り、複数モードの詳細は必要なときだけ読む。モデルごとの違いがあるため、共有スキルを読む他のモデルに必要な具体的手順も確認する。

## Claude Code

[Extend Claude with skills](https://code.claude.com/docs/en/skills) にある `description + when_to_use` の1,536文字の一覧短縮と、compaction 後の各スキル先頭5,000 tokens・合計25,000 tokensの再添付予算は **Claude Code 固有**。Codex の制約として適用しない。`argument-hint` などの拡張も、対象 runtime の対応を確認する。

## 常時指示と判断の根拠

AGENTS.md に置くのは、その適用範囲で行動を変える制約・非自明な情報である。毎回すべての設計文書を読ませる指示、既に満たした承認を求め直す指示、変更の実害に関係しない検証は、必要な場面と終了条件へ限定する。出典は上記 OpenAI 記事と、対象 runtime の公式資料を使う。

古いモデルへの助言や別 runtime の仕様を現行の必須条件へ読み替えない。数値・対応フィールド・読み込み挙動が判断を左右するときは、その公式ページまたはローカル実装を再確認する。
