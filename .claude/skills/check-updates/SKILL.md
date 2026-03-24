---
name: check-updates
description: git管理されたスキル・プラグインの更新をチェックし自動pullする。マーケットプレースプラグイン、ユーザースコープ・プロジェクトスコープのgit cloneされたスキルが対象。「更新チェック」「スキル更新」「プラグイン最新？」「update skills」「check for updates」といった要望に対応する。ユーザーが /check-updates と入力したら必ずこのスキルを使う。
argument-hint: [プロジェクトルートのパス]
---

# Check Updates — スキル・プラグイン更新チェック

git 管理されたスキルとプラグインの更新を確認し、自動で pull します。

---

## チェック対象

0. **dotfiles リポジトリ** — `~/.claude/skills` のシンボリックリンク元を辿って検出
1. **マーケットプレースプラグイン** — `~/.claude/plugins/marketplaces/` 配下
2. **インストール済みプラグイン** — `~/.claude/plugins/cache/` 配下
3. **ユーザースコープ skills** — `~/.claude/skills/` 配下の git リポジトリ
4. **プロジェクトスコープ skills** — `<project>/.claude/skills/` 配下の git リポジトリ

dotfiles は `~/.claude/skills` がシンボリックリンク（Unix）または Windows ジャンクションポイントの場合に自動検出される。それ以外は各ディレクトリが `.git` を持つ場合のみチェック対象（自作スキルなど git 管理でないものはスキップ）。

---

## 実行手順

### ステップ 1: スクリプトの実行

このスキルの `scripts/check-updates.sh` を実行してください。

```bash
sh "$(dirname "$(readlink -f ~/.claude/skills/check-updates/SKILL.md)" 2>/dev/null || echo "$HOME/.claude/skills/check-updates")/scripts/check-updates.sh" "$(pwd)"
```

スクリプトの処理:
- 各対象ディレクトリを走査し、`.git` の有無で git リポジトリか判定
- git リポジトリなら `git fetch` → ローカルとリモートの差分チェック
- 差分があれば `git pull origin [main|master]` を自動実行
- 結果サマリーを出力

### ステップ 2: 結果の報告

スクリプト出力を解析し、ユーザーに結果を報告してください。

**すべて最新の場合:**
```
すべてのスキル・プラグインは最新です。(N リポジトリをチェック)
```

**更新があった場合:**
```
## 更新結果

- [label/name]: X commits を pull しました
- ...

チェック: N リポジトリ / 更新: M リポジトリ
```

**エラーがあった場合:**
エラー内容も報告し、対処法を提案してください（ネットワークエラー等）。

### ステップ 3: コンフリクト対応

スクリプト出力に `CONFLICT:` が含まれる場合、pull は自動で `merge --abort` されている。
以下の手順でユーザーに対応を確認すること：

1. コンフリクトが発生したリポジトリとファイルをユーザーに報告する
2. 以下の選択肢を提示する：

```
[label/name] で pull がコンフリクトしました。

コンフリクトファイル:
- [ファイル一覧]

ローカルの未コミット変更:
- [変更ファイル一覧]

どうしますか？
A) ローカル変更を stash してから pull する（stash → pull → stash pop）
B) ローカル変更をコミットしてから pull する（commit → pull）
C) リモートの変更を優先する（ローカル変更を破棄して reset）
D) 今回はスキップする
```

3. ユーザーの選択に応じて実行する：
   - **A**: `git stash` → `git pull origin [branch]` → `git stash pop`。stash pop でコンフリクトした場合はユーザーに報告
   - **B**: 変更内容を確認してコミットメッセージを提案 → ユーザー承認後にコミット → pull
   - **C**: `git checkout .` → `git pull origin [branch]`。**実行前に必ずユーザーに最終確認する**
   - **D**: 何もしない

4. pull 成功後は **自動で push も実行する**（`git push origin [branch]`）。push の要否を確認する必要はない。
