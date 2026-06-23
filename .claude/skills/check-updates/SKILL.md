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

### ステップ 3: コンフリクト対応

スクリプト出力に `CONFLICT:` が含まれる場合、pull は自動で `merge --abort` されている。
コンフリクトは **2 つの層** が独立に絡むので、まず状態を切り分けてから選択肢を出すこと。

#### 3-0. 状態の切り分け（選択肢を出す前に必ず実行）

```bash
git -C <repo> status -sb            # 未コミット変更 + ahead/behind を確認
git -C <repo> rev-list --left-right --count HEAD...@{u}   # local独自 / remote独自 のコミット数
```

これで以下 2 軸を把握する：

- **A 軸: 未コミット変更（dirty tree）** — 退避方法（stash / commit / 破棄）を決める層
- **B 軸: 分岐コミット（ahead N / behind M で両方 >0）** — **統合方法（merge / rebase）を決める層**

> ⚠️ **B 軸が「ahead≥1 かつ behind≥1」なら、本質は単なる pull ではなく merge か rebase の選択**。この選択を必ずユーザーに出すこと（今までこの選択肢を出さず stash/commit/reset の 3 択しか出さなかったのが不備）。ahead=0（local 独自コミットなし）なら統合は fast-forward 相当で merge/rebase の差は出ないため B 軸の質問は省略してよい。

dirty なファイルが分岐側で変更されたファイルと重複する場合は実コンテンツ衝突がほぼ確実に出る（`comm -12 <(git diff --name-only|sort) <(git diff --name-only HEAD..@{u}|sort)` で重複を提示する）。重複が多いときは **stash pop（2-way）より commit 起点（3-way マージ）** を推奨として添える。

#### 3-1. 選択肢の提示

A 軸（dirty tree がある場合）と B 軸（分岐がある場合）を分けて提示する。両方該当する場合は両方聞く。

**A 軸（未コミット変更の退避方法）:**

```
A1) stash してから統合（stash → pull → stash pop）
A2) コミットしてから統合（commit → pull）  ※重複が多いとき推奨
A3) ローカル変更を破棄（reset / checkout）   ※実行前に必ず最終確認
A4) 今回はスキップ
```

**B 軸（分岐コミットの統合方法 — ahead≥1 かつ behind≥1 のときのみ）:**

```
B1) マージ（git pull --no-rebase）    両方の履歴を残しマージコミットを作る
B2) リベース（git pull --rebase）     local 独自コミットを remote の上に再適用（線形履歴）
```

#### 3-2. 実行

- **A1 stash**: `git stash` → `git pull origin <branch> [--no-rebase|--rebase]` → `git stash pop`。pop で衝突したら報告
- **A2 commit**: 変更を**個別に** `git add <file>`（`git add -A` 禁止）→ コミットメッセージを提案・承認 → `git pull origin <branch> [--no-rebase|--rebase]`
- **A3 破棄**: `git checkout .` → `git pull origin <branch>`。**実行前に必ず最終確認**
- **A4**: 何もしない
- B 軸の選択は pull のフラグに反映（B1=`--no-rebase` / B2=`--rebase`）。`pull.rebase` 未設定リポジトリは `fatal: Need to specify how to reconcile divergent branches` で止まるため、**必ず明示フラグを付ける**
- 統合後にコンテンツ衝突が残ったら、各衝突を Read して解決方針（local 採用 / remote 採用 / 両方残す / マシン固有値はこのマシンの値）を表で提示 → 解決 → コンフリクトしたファイルだけ `git add` → merge は `git commit --no-edit` / rebase は `git rebase --continue`
- **auto-generated ファイルのマシン固有値**（絶対パス等）は現在のマシンに合う側を採用する

#### 3-3. push

統合が成功したら **自動で push も実行する**（`git push origin <branch>`）。push の要否を確認する必要はない。
