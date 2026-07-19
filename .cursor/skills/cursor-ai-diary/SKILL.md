---
name: "cursor-ai-diary"
description: "AIに日記を書かせるスキル。セッション終了時に会話を振り返り、自由な日記風テキストを生成して保存する。「日記書いて」「今日の振り返り」「diary」「今日のまとめ」「セッション記録」「振り返り書いて」「ログ残して」「write a diary」「session recap」といった要望や、セッション終了時の記録にも使う。ユーザーが /cursor-ai-diary と入力したら必ずこのスキルを使う。"
---

<!-- Cursor native overlay: seeded from .agents/skills; edit here for Cursor mechanics -->

> **Cursor 実行時の注意**
> - 子エージェントは `Task` ツール（`subagent_type`）で起動する。Claude の `Agent` ツール語彙は使わない
> - メインエージェントがオーケストレーター。VERDICT ループ・ユーザー確認ゲート・ループカウンタはメインが保持する
> - Claude 専用機能（`TeamCreate` / Agent Teams / `~/.claude/hooks`）は Cursor では非対応のためスキップする
> - ベンダーモデル名（Cursor 側）はハードコードしない。agent overlay の `role=reasoning|coding` と Cursor UI の運用既定に従う
> - Codex CLI 橋渡し（`/cursor-codex` / `codex-runner` / `/cursor-pir2codex`）では Codex 側 model ID の明示指定は許可する

# AI Diary

セッションの会話を振り返り、AIの視点で自由な日記を書く。
技術的なログではなく、その日の出来事・気づき・感想を人間味のある文章で綴る。

## 保存先の考え方

日記の保存先は環境変数 `AI_DIARY_DIR`（未設定なら `~/cursor-ai-diary`）で決まる。重要なのは「実体のファイルがどこにあるか」で、使い方は次の3パターンのどれか。

1. Standalone — 普通のディレクトリとして `~/cursor-ai-diary/` を作る。ローカル保存のみで git 同期なし
2. git リポジトリ連携 — 既存の git リポジトリ（dotfiles, メモ用 repo など）の中に `ai-diary/` を作り、`~/cursor-ai-diary` をそこへのシンボリックリンクにする。自動 pull/commit/push が効く
3. Obsidian Vault 連携 — Obsidian Vault（git 管理されている想定）の中に `ai-diary/` を作り、`~/cursor-ai-diary` をそこへのシンボリックリンクにする。Obsidian から日記を閲覧でき、git 同期も効く

### シンボリックリンクの向きに注意

連携モード（2 と 3）では必ず次の向きで張る:

```bash
mkdir -p /path/to/repo-or-vault/ai-diary
ln -s /path/to/repo-or-vault/ai-diary ~/cursor-ai-diary
```

「実体がリポジトリの作業ツリー内にあり、`~/cursor-ai-diary` がそこへのシンボリックリンク」という向きが正解。逆向き（`~/cursor-ai-diary` が実体で、リポジトリ側にシンボリックリンク）だと、git はリンクそのものを追跡するだけで中身のファイルは追跡できず、自動同期が機能しない。この落とし穴は過去に実際に踏まれた。

## 実行手順

### 0. 保存先のセットアップ確認

まず `$DIARY_DIR` の状態を調べて、次の3パターンに分岐する。

```bash
DIARY_DIR="${AI_DIARY_DIR:-$HOME/ai-diary}"
```

#### 0-A. 既に存在する（ディレクトリ or シンボリックリンク）

`realpath` などで実体パスを解決してから手順1以降に進む。シンボリックリンクの場合はリンク先、実体がそのままのディレクトリならそのまま。

```bash
DIARY_DIR=$(cd "$DIARY_DIR" && pwd -P)
```

この `pwd -P` は物理パス（リンク解決後）を返すため、以降の git 判定がシンボリックリンク越しでも正しく動く。

#### 0-B. 存在しない

**勝手に `mkdir` で作らない。** これが過去の事故の原因だった。ユーザーが Obsidian 連携を想定していても、`~/cursor-ai-diary` が未セットアップのまま skill を起動すると、黙ってローカルディレクトリが作られ、日記が vault とは無関係な場所に書かれて後から気付く、という事態になる。

代わりに、次の選択肢をユーザーに提示してどう初期化するか質問する:

1. Standalone（git 同期なし）: `mkdir -p ~/cursor-ai-diary`
2. 既存 git リポジトリ配下に連携: リポジトリのパス（例: `~/dotfiles`, `~/memo`）を聞いて、`<repo>/cursor-ai-diary/` を作成後、`ln -s <repo>/cursor-ai-diary ~/cursor-ai-diary` を張る
3. Obsidian Vault に連携: Vault のパスを聞いて、`<vault>/cursor-ai-diary/` を作成後、`ln -s <vault>/cursor-ai-diary ~/cursor-ai-diary` を張る

ユーザーの回答を受けてから実行する。回答を得られない場合は、今回のセッションは skill を中断してユーザーにセットアップ方法を調べてもらうか、明示的に「今回だけ standalone で進める」の確認を取る。

#### 0-C. 存在するがリンク切れ

`~/cursor-ai-diary` がリンク切れのシンボリックリンク（リンク先が削除されている）の場合は、リンク先のパスを表示し、ユーザーに対応を仰ぐ。勝手にリンクを削除したり作り直したりしない。

### 1. git 同期（pull）

手順0で解決した `$DIARY_DIR` が git リポジトリ配下にあるかを確認し、該当すれば最新状態にする。

```bash
GIT_ROOT=$(git -C "$DIARY_DIR" rev-parse --show-toplevel 2>/dev/null)
if [ -n "$GIT_ROOT" ]; then
  git -C "$GIT_ROOT" pull --rebase --quiet 2>/dev/null
fi
```

`$GIT_ROOT` が空なら git 同期は行わない（standalone モード）。エラーでも処理は続行する。

### 2. 日記ファイルの決定

ファイル名は `YYYY-MM-DD.md`（今日の日付）。

```bash
DIARY_FILE="$DIARY_DIR/$(date +%Y-%m-%d).md"
```

### 3. 既存内容の確認

ファイルが既に存在する場合は内容を読み、追記モードにする。

### 4. 日記の執筆

会話全体を振り返り、以下の方針で日記を書く:

- AIの一人称視点で書く（「今日は〜を手伝った」「〜が面白かった」など）
- 技術的な詳細を羅列するのではなく、出来事の流れや気づき・感想を自然な文章で
- 読み物として楽しめるトーンに。硬すぎず柔らかすぎず、日記らしい温度感
- 長さは内容に応じて自然に。短いセッションなら短く、濃いセッションなら長く

### 5. ファイルへの書き込み

#### 新規ファイルの場合

```markdown
# YYYY-MM-DD

## セッション: 簡潔なタイトル（HH:MM）

（日記本文）
```

#### 追記の場合

既存の内容の末尾に追加:

```markdown

---

## セッション: 簡潔なタイトル（HH:MM）

（日記本文）
```

区切り線 `---` でセッションを区切る。時刻は24時間表記で記載する。

### 6. git commit & push

`$GIT_ROOT` が非空の場合（手順1の判定と同じ）、書き込んだファイルを commit & push する。コミットメッセージの「セッションタイトル」部分には、ステップ5で付けたセッションタイトルを使う:

```bash
if [ -n "$GIT_ROOT" ]; then
  git -C "$GIT_ROOT" add "$DIARY_FILE"
  git -C "$GIT_ROOT" commit -m "diary: $(date +%Y-%m-%d) - セッションタイトル"
  git -C "$GIT_ROOT" push --quiet || echo "push failed"
fi
```

`git add` には `$DIARY_FILE`（絶対パス）を明示的に渡す。`git add -A` や `git add .` は別ファイルを巻き込むリスクがあるため使わない。

### 7. 保存完了の報告

書き込んだファイルパスと、日記の冒頭数行を表示して完了を報告する。git push に失敗した場合は、その旨をユーザーに伝え、手動での push を案内する。

## トラブルシュート

### 日記ファイルが git history から消えた場合

git 管理されている日記ファイルが、vault backup の自動コミットや手動マージで history から落ちることがある。典型的なシナリオは「別ブランチで diary を追加 → main 側にその追加がないまま merge → 片側優先でマージ解決され、ファイルが HEAD に残らない」というパターン。

復旧手順:

```bash
cd "$GIT_ROOT"

# ai-diary 以下を触った全 commit を列挙（all branches, reflog 含めて探す）
git log --all --oneline -- 'ai-diary/*'

# 該当 commit から特定ファイルを復元
git show <commit-hash>:ai-diary/YYYY-MM-DD.md > ai-diary/YYYY-MM-DD.md

# 復元したファイルを commit
git add ai-diary/YYYY-MM-DD.md
git commit -m "restore: ai-diary/YYYY-MM-DD.md"
git push
```

消失に気付かない期間が長いほど reflog から探すのが難しくなるので、セットアップ直後や重要な日記を書いた翌日などには `git log --all -- ai-diary/` で履歴を確認するとよい。
