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
0a. **dotfiles のサブモジュール** — dotfiles リポジトリ内の git submodule を自動検出・更新。更新があれば親リポの submodule ポインタを commit & push し（`.codex/` ミラーも再生成して同梱）、submodule 作業ツリーと親リポの記録の乖離を残さない
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

出力に含まれる主なマーカーの扱い:
- `UPDATED:` / `SUBMODULE_INIT:` — 通常の更新・初期化として報告
- `SUBMODULE_POINTER:` — submodule 更新に伴い親リポ（dotfiles）の submodule ポインタを commit & push した旨を報告
- `SUBMODULE_POINTER_PUSH_FAILED:` — ポインタは commit 済みだが push に失敗。リモートが進んでいる等が原因。ユーザーに `git -C <dotfiles> push` を促す

**エラーがあった場合:**
エラー内容も報告し、対処法を提案してください（ネットワークエラー等）。

### ステップ 3: ローカル変更があった場合（基本はさっさとマージ）

スクリプト出力に `CONFLICT:` が含まれる場合、pull は自動で `merge --abort` されている（未コミット変更 or 分岐が原因で pull が止まった状態）。

> ✅ **方針: 基本はさっさとマージで通す。merge/rebase の選択や stash/commit の選択をいちいち聞かない。実コンテンツ衝突が出て初めてユーザーに指示を仰ぐ。**

#### 3-1. まずローカルに何が入っているか報告する（必須・即判断のため）

選択肢を出すより先に、ユーザーが状況を即把握できるよう**ローカル変更の中身**を報告する：

```bash
git -C <repo> status -sb                                   # 未コミット変更 + ahead/behind
git -C <repo> diff --stat                                  # 未コミット変更の差分サマリー
git -C <repo> log --oneline @{u}..HEAD                     # local 独自コミット（ahead 分）
```

報告フォーマット例：

```
[label/name]: local ahead N / behind M
未コミット変更:
  path/a.json  | +12 -3
  path/b.toml  | +1 -1
local 独自コミット: <hash> <subject> ...
→ マージで統合します
```

#### 3-2. 自動マージを実行（確認なしで進めてよい）

1. 未コミット変更があれば**個別に** `git add <file>` でステージ（`git add -A` / `git add .` は禁止）→ `git commit -m "chore(<repo>): ローカル変更を退避（リモート統合前）"` で退避コミット
2. `git pull origin <branch> --no-rebase --no-edit` でマージ
   - `pull.rebase` 未設定リポジトリは `fatal: Need to specify how to reconcile divergent branches` で止まるため、**`--no-rebase` を必ず明示**する
   - rebase は既定では使わない（履歴を保つマージが既定。ユーザーが明示的に rebase を求めたときだけ `--rebase`）
3. クリーンにマージできたら 3-4 の push へ。**ここまでユーザーへの確認は不要**

#### 3-3. 実コンテンツ衝突が出たとき（ここで初めて指示を仰ぐ）

マージで `CONFLICT (content):` が出たファイルがある場合のみ、ユーザーに対応を確認する：

1. 衝突した各ファイルを Read し、HEAD 側 / リモート側の差分を提示する
2. 解決方針を**表で**提案する（local 採用 / remote 採用 / 両方残す / マシン固有値はこのマシンの値）
   - **auto-generated ファイルのマシン固有値**（絶対パス等）は現在のマシンに合う側を既定提案にする
   - 別キー・別セクションが同一行で衝突しているだけなら「両方残す」を既定提案にする
3. ユーザー承認後に解決 → **コンフリクトしたファイルだけ** `git add` → `git commit --no-edit`（rebase 中なら `git rebase --continue`）
4. ローカル変更を破棄したい場合のみ `git checkout .` / `git reset` を使うが、**破棄は実行前に必ず最終確認**する

#### 3-4. push

統合が成功したら **自動で push も実行する**（`git push origin <branch>`）。push の要否を確認する必要はない。
