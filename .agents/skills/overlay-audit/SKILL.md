---
name: overlay-audit
description: >-
  起動ディレクトリと dotfiles のスキル配置・エージェント定義を点検する。判定の正は
  etc/audit-skill-agent-layout.py。スキル SSOT、Claude symlink、Cursor の model/role、
  overlay の name==フォルダ、古いロール別名バナーを見る。「overlay 点検」「スキル配置」
  「エージェント定義は共通か」「.agents に寄ってる？」「layout audit」「/overlay-audit」で使う。
argument-hint: "[起動ディレクトリ]"
---

# /overlay-audit — スキル / エージェント配置点検

起動したリポジトリと `~/dotfiles` の両方を見る。修正はしない。報告だけする。
**あるべき形と合否はスクリプトが正**。このファイルに判定を増やさない。

## 方針（判定の正はスクリプト）

- **スキル本体**は `.agents/skills`。Claude は `.claude/skills` から symlink。Cursor / Codex は `.agents/skills` を直接読む。overlay 複製は任意。
- **エージェント定義**は各ランタイムの発見ディレクトリに置く。`model` の実名は揃えない。
- **Cursor agent**: `model` は `inherit` か公式モデル ID。仕事分類は `role: coding` / `role: reasoning`（`model` に書かない）。
- **Cursor overlay スキル**: フォルダ名 == frontmatter `name`。実行時注意があるなら inherit/role 契約文を含む。`ベンダーモデル名` や `role=reasoning|coding` は FAIL。
- **本文 lockstep**は、生成物が lockstep を名乗っているときだけ必須。Cursor seed（既存を上書きしない）と Codex native overlay は本文一致を要求しない。

## 手順

1. エンジンを実行する（引数なしなら cwd + dotfiles）:

```bash
python3 "$HOME/dotfiles/etc/audit-skill-agent-layout.py"
```

dotfiles が `~/dotfiles` 以外なら、スキル実体から根を取る:

```bash
SKILL_FILE="$HOME/.agents/skills/overlay-audit/SKILL.md"
SKILL_DIR="$(cd -P "$(dirname "$SKILL_FILE")" 2>/dev/null && pwd)"
DOT_DIR="$(cd -P "$SKILL_DIR/../../.." 2>/dev/null && pwd)"
python3 "$DOT_DIR/etc/audit-skill-agent-layout.py" --cwd "$(pwd)" --dotfiles "$DOT_DIR"
```

2. 出力は `LEVEL<TAB>repo<TAB>topic<TAB>message`。`SUMMARY fails=N` の N が FAIL 件数。スクリプトは FAIL があると exit 1。

3. ユーザーへの報告は次の順。生ログを貼らず、リポごとに要約する。

| 節 | 中身 |
|---|---|
| 対象 | cwd の git root と dotfiles パス |
| スキル | `.agents` 件数、Claude が symlink か実体か、Claude-only、overlay の有無 |
| Cursor スキル | `name==folder`、実行時注意の inherit/role、古いバナー |
| エージェント | 3 系統の件数、欠け、Cursor `model`/`role` |
| 本文 | identical / vocab-only / substantive / generated-stale / native-overlay |
| 生成器 | `sync-codex.py --check` の成否。dotfiles の `sync-codex.sh` は agents を再生成しないこと、Cursor seed は既存を上書きしないことを事実として書く |

4. FAIL は「壊れている生成物」だけを直す提案にする。WARN（Claude スキルが実ディレクトリ、native overlay の本文差）は方針どおりなら提案に含めない。直すならユーザーが明示したときだけ。

## やらないこと

- ファイルを Edit / 再生成しない（点検専用）
- overlay を byte 一致させろと要求しない
- `SYNC_CODEX_LEGACY_MIRROR=1` を勝手に走らせない
- 判定ルールをこの SKILL.md に増やす（直すのは `etc/audit-skill-agent-layout.py`）
