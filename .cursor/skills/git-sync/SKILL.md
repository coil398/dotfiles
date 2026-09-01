---
name: git-sync
description: >-
  カレントリポジトリをリモートと同期する（fetch → pull → コンフリクト解消 → push）。
  先に /check-updates でスキル・プラグインも更新する。
  「git sync」「同期して」「pullしてpush」「リモートと揃えて」「git syncして」で使う。
  ユーザーが /git-sync と入力したら必ずこのスキルを使う。
argument-hint: "[リポジトリルート。省略時は cwd]"
---

<!-- Cursor native overlay: seeded from .agents/skills; edit here for Cursor mechanics -->

> **Cursor 実行時の注意**
> - 子エージェントは `Task` ツール（`subagent_type`）で起動する。Claude の `Agent` ツール語彙は使わない
> - メインエージェントがオーケストレーター。VERDICT ループ・ユーザー確認ゲート・ループカウンタはメインが保持する
> - Claude 専用機能（`TeamCreate` / Agent Teams / `~/.claude/hooks`）は Cursor では非対応のためスキップする
> - Task の `model` は省略するか `inherit` のみ（親 Auto に従う）。ベンダー名はハードコードしない
> - Cursor agent の `model` は `inherit` か公式モデル ID。仕事の分類は `role: coding|reasoning`

# /git-sync — リポジトリ同期 + スキル更新

カレント（または指定）Git リポジトリをリモートと揃え、あわせてインストール済みスキル／プラグインを更新する。

## 手順

### 1. `/check-updates`（必須・最初）

このスキルの一部として **必ず** `/check-updates` を実行する。省略禁止。

1. `.cursor/skills/check-updates/SKILL.md`（Cursor なら同名スキル）を Read する
2. その手順どおり `scripts/check-updates.sh` を回し、結果を報告する
3. `CONFLICT:` が出たら check-updates 側のマージ方針に従う（実コンテンツ衝突だけユーザー確認）

dotfiles 自体が更新対象になった場合は、check-updates / `/dotfiles-autosync` の結果を待ってから次へ進む。

### 2. 対象リポの preflight

```bash
ROOT="${1:-$(pwd)}"
git -C "$ROOT" rev-parse --show-toplevel
git -C "$ROOT" status -sb
git -C "$ROOT" remote -v
git -C "$ROOT" fetch origin
git -C "$ROOT" status -sb -u
git -C "$ROOT" log --oneline -5
```

- Git リポジトリでなければ停止して報告
- 機密（`.env` / credentials）はステージしない。ユーザーが明示しても警告する

### 3. ローカル変更の保全 commit（dirty なら）

確認なしで進めてよい（実破棄だけは禁止）。

1. `git status` / `git diff --stat` / `git log -5 --oneline` でスタイル把握
2. **個別に** `git add <path>`（`git add -A` / `git add .` は禁止）
3. `.bak*` / 一時バックアップ / 秘密ファイルは除外
4. HEREDOC で commit（メッセージは why 中心、リポジトリの既存スタイルに合わせる）
5. プロジェクト規約で version bump が必要な変更（機能・規約の配信）なら、そのリポの SSOT に従って bump してから commit に含める

空なら commit しない。

### 4. pull

ブランチ名は `git rev-parse --abbrev-ref HEAD`。upstream が無ければ `origin/<branch>` を仮定して set-upstream は push 時に行う。

rebase 前に **未ステージの一時ノイズ**（`live-status.json` 等）で `cannot pull with rebase` になる場合は、意図した変更を commit 済みなら `git stash push -u -m 'git-sync: transient'` → pull → `git stash pop`（衝突したら報告）。behind=0 なら pull を省略して push してよい。

**取り込み方式:**

| リポの約束 | コマンド |
|---|---|
| `AGENTS.md` / `CLAUDE.md` が「線形履歴」「`pull --rebase`」を明示 | `git pull --rebase origin <branch>` |
| それ以外（既定） | `git pull --no-rebase --no-edit origin <branch>` |

`pull.rebase` 未設定で止まるのを避けるため、rebase / no-rebase は **必ず明示**する。

### 5. コンフリクト

方針は `/check-updates` と同じ: **基本はさっさと統合。実コンテンツ衝突だけユーザーに聞く。**

#### rebase 中

1. `git status` で衝突ファイルを列挙
2. 各ファイルを Read し、ours/theirs の差分を表で提案
3. ユーザー承認後に解決 → 衝突ファイルだけ `git add` → `git rebase --continue`
4. 中止が必要なら `git rebase --abort`（破棄になる操作は最終確認）

#### merge 中

1. 同上で解決
2. 衝突ファイルだけ `git add` → `git commit --no-edit`

自動で選んでよい例:

- 生成物・ロックファイルで機械的に再現できるもの → 再生成側
- 絶対パス等マシン固有値 → 今のマシンに合う側
- 別キーが同一箇所で衝突 → 両方残す

### 6. push

統合成功後は **確認なしで push**:

```bash
git push -u origin HEAD
```

force push はしない。ユーザーが明示したときだけ（`main`/`master` への force は拒否して警告）。

### 7. 報告

```
## git sync 結果

### check-updates
- ...

### <repo>
- branch: ...
- pull: rebase|merge / clean|conflicts-resolved
- commit: <hash> <subject> | (なし)
- push: ok | failed (<reason>)
- status: <git status -sb>
```

## 禁則

- `git add -A` / `git add .`
- 秘密ファイルの commit
- 確認なしの `reset --hard` / ローカル変更破棄
- `main`/`master` への force push
- `/check-updates` のスキップ
- git config の変更
