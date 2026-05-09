# Instruction file 肥大化への整理戦略

公式・著名エンジニアの推奨を踏まえた整理戦略。問題種別ごとに採用すべき戦略を示す。

公式の引用と URL は `~/.claude/skills/instruction-audit/references/official-criteria.md` を参照。

## 戦略 1: Ruthlessly prune（容赦なく削る）

> "Keep it concise. For each line, ask: 'Would removing this cause Claude to make mistakes?' If not, cut it."
>
> 出典: Claude Code best-practices

最も基本的な戦略。各行について「これを消したら Claude が間違うか？」を自問する。No なら削除。

適用する場面:

- 判定 1: 公式上限超過
- 判定 2a: 責務越境（実装詳細を削除）
- 判定 2b: SSOT 逸脱（抜粋を削除し参照のみに）
- 判定 2d: 二重説明（片方を削除）

## 戦略 2: Progressive Disclosure（段階的開示）

skill のオンデマンドロード設計を活用する:

1. セッション開始時: `name` + `description` のみがプリロードされる
2. Claude が関連性を判断時: `SKILL.md` 全文がロードされる
3. 必要に応じて: `SKILL.md` から参照される追加ファイルがロードされる

ファイル構造:

```text
my-skill/
├── SKILL.md                 # 本体（500 行以内）
├── references/<topic>.md    # 詳細リファレンス、オンデマンド
├── scripts/<task>.<ext>     # 決定論的処理（Claude が exec）
└── assets/<file>            # テンプレート・固定アセット
```

適用する場面:

- 判定 1: SKILL.md 500 行超過
- 判定 2c: DRY 違反（共通骨格を `references/` に集約 + 両方から参照）

実装ガイド:

- 共通骨格を別 skill 配下の `references/` に置き、別 skill から `~/.claude/skills/<owner>/references/<file>.md` で参照する形は OK（公式が明示的に推奨はしていないが、パスベースの Read で動作する）
- SKILL.md 本体には「詳細プロトコル: `<path>` を参照」と書き、要点だけ残す

## 戦略 3: Import (`@path`)

> "If you have an `AGENTS.md` file, you can source it in your `CLAUDE.md` using `@AGENTS.md` to maintain a single source of truth."
>
> 出典: Anthropic Docs（Simon Willison が引用）

CLAUDE.md / AGENTS.md レベルでのモジュール分割に有効。

```markdown
See @README.md for project overview and @package.json for available npm commands.

# Additional Instructions
- Git workflow: @docs/git-instructions.md
- Personal overrides: @~/.claude/my-project-instructions.md
```

適用する場面:

- CLAUDE.md が肥大化し始めたが完全に消すわけにはいかない情報がある
- 階層メモリ（user / project / local）の使い分け

## 戦略 4: 階層メモリの使い分け

「常時ロード不要だが場面では必要」な情報は `skills/` に切り出すのが推奨。

> "CLAUDE.md is loaded every session, so only include things that apply broadly. For domain knowledge or workflows that are only relevant sometimes, use skills instead."
>
> 出典: Claude Code best-practices

`~/.claude/CLAUDE.md` には以下のみを残す:

- 全プロジェクトで常時必要な振る舞い・規約
- ファイル横断のルール（命名・git・書式）
- エージェント・スキルの呼び出し方針

ドメイン特化の手順・テンプレート・チェックリストは skill 化する。

## 戦略 5: 棚卸し（dead code 削除）

> Armin Ronacher (Flask 作者): "Agentic Coding Things That Didn't Work" (2025-07-30)
> 多数作成したスラッシュコマンドのほとんどを未使用化のため **削除した** と報告

定期的に「使われていない」コマンド・スキル・観点を棚卸しして削除する。`pir_skill_log.md` / `pir_planner_log.md` などのログから「最近 N 回起動されていない skill」「触れられていない agent 観点」を抽出する。

適用する場面:

- 全体棚卸しの定期メンテ（数ヶ月に 1 回）
- skill 数が増えすぎて管理コストが目立ち始めたとき

## 戦略選択フローチャート

1. **公式上限超過？**（SKILL.md > 500 行 等）
   - YES → 戦略 2 (Progressive Disclosure)
2. **DRY 違反？**（複数ファイルでセクションが字句同一）
   - YES → 戦略 2 (共通骨格を references に外出し)
3. **SSOT 逸脱 / 責務越境 / 二重説明？**
   - YES → 戦略 1 (Ruthlessly prune)
4. **CLAUDE.md / AGENTS.md レベルの分割？**
   - YES → 戦略 3 (Import) + 戦略 4 (階層メモリ)
5. **全体的に膨らんでいるが具体的な悪さが見えない？**
   - YES → 戦略 5 (棚卸し)

## アンチパターン

- **「将来の拡張性」だけを理由に references/ を切る**: 現時点で具体的に分割が必要という根拠がなければ、既存パターンに合わせて単一ファイル構成で始める
- **SSOT を切らずに references を増やす**: 共通骨格を出した先がさらに別の SSOT と重複していたら根本解決にならない
- **削減と称して必要な指示まで消す**: "Would removing this cause Claude to make mistakes?" の自問を必ず行う
- **削減後に動作確認をしない**: 大規模リファクタは `/pir2` 経由でレビューを通す

## 大規模リファクタは `/pir2` 経由

5 ファイル以上に影響する整理を行う場合、独断せず `/pir2` で planner → reviewer のレビューを通すことを推奨。`instruction-audit` 自体は **検出と提案までが本分** であり、複雑な構造変更は PIR² の品質保証を経由する設計。
