---
name: "overlay-audit"
description: >-
  起動ディレクトリと dotfiles のスキル配置・エージェント定義を点検する。判定の正は
  etc/audit-skill-agent-layout.py。スキル SSOT、Claude symlink、Cursor の model/role、
  overlay の name==フォルダ、古いロール別名バナーを見る。「overlay 点検」「スキル配置」
  「エージェント定義は共通か」「.agents に寄ってる？」「layout audit」「/overlay-audit」で使う。
argument-hint: "[起動ディレクトリ]"
---

<!-- Cursor native overlay: seeded from .agents/skills; edit here for Cursor mechanics -->

> **Cursor 実行時の注意**
> - 子エージェントは `Task` ツール（`subagent_type`）で起動する。Claude の `Agent` ツール語彙は使わない
> - メインエージェントがオーケストレーター。VERDICT ループ・ユーザー確認ゲート・ループカウンタはメインが保持する
> - Cursor で提供されない専用 lifecycle / hook API は使わず、必要な分担は通常の `Task` で行う
> - Task の `model` は省略するか `inherit` のみ（親 Auto に従う）。ベンダー名はハードコードしない
> - Cursor agent の `model` は `inherit` か公式モデル ID。仕事の分類は `role: coding|reasoning`
> - Codex CLI 橋渡し（`/codex` / `codex-runner` / `/pir2codex`）では Codex 側 model ID の明示指定は許可する

# /overlay-audit — スキル / エージェント配置点検

起動したリポジトリと `~/dotfiles` の両方を見る。修正はしない。報告だけする。
**あるべき形と合否はスクリプトが正**。このファイルに判定を増やさない。

## 方針（判定の正はスクリプト）

- **共有スキルの種**は `.agents/skills`。Cursor は優先順位に従い `.cursor/skills` の native overlay（`link.sh` が `~/.cursor/skills` に materialize）を使い、overlay が無い場合だけ共有側を参照する。Claude は `.claude/skills`、Codex は `.agents/skills` を使う。Cursor overlay の本文一致は要求しない。
- **エージェント定義**は各ランタイムの発見ディレクトリに置く。`model` の実名は揃えない。
- **Cursor agent**: `model` は `inherit` か公式モデル ID。仕事分類は `role: coding` / `role: reasoning`（`model` に書かない）。
- **Cursor overlay スキル**: フォルダ名 == frontmatter `name`。実行時注意があるなら inherit/role 契約文を含む。ロールを `model` に書いたバナーと、ベンダー名を Cursor の model 方針に書いた注意書きは FAIL。Cursor 発見用に `.cursor/skills/overlay-audit` を持ち、`link.sh` が `~/.cursor/skills` へ materialize する。ホームコピーが SSOT と食い違ったら FAIL。
- **本文 lockstep**は、生成物が lockstep を名乗っているときだけ必須。Cursor seed（既存を上書きしない）と Codex native overlay は本文一致を要求しない。

## 手順

1. エンジンを実行する（引数なしなら cwd + dotfiles + ホームの Cursor materialize）:

```bash
DOT_DIR="${DOTFILES_ROOT:-$HOME/dotfiles}"
python3 "$DOT_DIR/etc/audit-skill-agent-layout.py" --cwd "$(pwd)" --dotfiles "$DOT_DIR"
```

Cursor は `~/.cursor/skills/overlay-audit`（dotfiles overlay の materialize）からこのスキルを発見する。判定本体は `etc/audit-skill-agent-layout.py` のまま。

2. 出力は `LEVEL<TAB>repo<TAB>topic<TAB>message`。`SUMMARY fails=N` の N が FAIL 件数。スクリプトは FAIL があると exit 1。

3. ユーザーへの報告は次の順。生ログを貼らず、リポごとに要約する。

| 節 | 中身 |
|---|---|
| 対象 | cwd の git root と dotfiles パス |
| スキル | `.agents` 件数、Claude が symlink か実体か、Claude-only、overlay の有無 |
| Cursor スキル | `name==folder`、実行時注意の inherit/role、古いバナー |
| Cursor ホーム | `~/.cursor/agents` が SSOT への symlink か、`~/.cursor/skills` の SKILL.md が SSOT と一致するか |
| エージェント | 3 系統の件数、欠け、Cursor `model`/`role` |
| 本文 | identical / vocab-only / substantive / generated-stale / native-overlay |
| 生成器 | `sync-codex.py --check` の成否。dotfiles の `sync-codex.sh` は agents を再生成しないこと、Cursor seed は既存を上書きしないことを事実として書く |

4. FAIL は「壊れている生成物」だけを直す提案にする。WARN（Claude スキルが実ディレクトリ、native overlay の本文差）は方針どおりなら提案に含めない。直すならユーザーが明示したときだけ。

## やらないこと

- ファイルを Edit / 再生成しない（点検専用）
- overlay を byte 一致させろと要求しない
- `SYNC_CODEX_LEGACY_MIRROR=1` を勝手に走らせない
- 判定ルールをこの SKILL.md に増やす（直すのは `etc/audit-skill-agent-layout.py`）
