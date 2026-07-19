# ai-diary

Codex のスキルとして動作する、AIが自動で日記を書くツール。

セッション中の会話を振り返り、AIの一人称視点で日記風のテキストを生成・保存する。技術ログではなく、出来事の流れや気づき・感想を自然な文章で綴る。

## インストール

Codex のスキルとしてこのリポジトリをクローンする:

```bash
# ユーザースコープ（全プロジェクト共通）
git clone https://github.com/coil398/ai-diary.git .cursor/skills/cursor-ai-diary

# プロジェクトスコープ（特定プロジェクトのみ）
git clone https://github.com/coil398/ai-diary.git .agents/skills/ai-diary
```

## 使い方

Codex のセッション中に以下のように呼び出す:

```
/ai-diary
```

「日記書いて」「今日の振り返り」などの自然言語でも起動する。

## 保存先

- デフォルト: `~/ai-diary/`
- 環境変数 `AI_DIARY_DIR` で変更可能

初回起動時、`~/ai-diary` が未設定ならスキルは黙ってディレクトリを作らず、どの方法で初期化するかを対話で確認する（後述のセットアップパターン参照）。

## セットアップパターン

以下の3パターンのどれかを選んでセットアップする。

### 1. Standalone（シンプル、git 同期なし）

```bash
mkdir -p ~/ai-diary
```

日記はローカルディレクトリに保存されるだけ。バックアップは自分で取る必要がある。

### 2. 既存 git リポジトリ連携（推奨）

dotfiles、メモ用 repo、Obsidian Vault など、自分が普段から同期している git リポジトリの中に `ai-diary/` サブディレクトリを作り、そこを `~/ai-diary` のリンク先にする:

```bash
REPO=~/dotfiles        # お好みの git リポジトリ
mkdir -p "$REPO/ai-diary"
ln -s "$REPO/ai-diary" ~/ai-diary
```

これでスキルは `~/ai-diary/YYYY-MM-DD.md` に書き込むが、実体は `$REPO/ai-diary/` にあり、スキルが自動で `git pull` / `commit` / `push` を回してくれる。

### 3. Obsidian Vault 連携

上記の特殊ケース。Vault が git 管理されていれば、そのまま連携が効く:

```bash
VAULT=~/ObsidianVault
mkdir -p "$VAULT/ai-diary"
ln -s "$VAULT/ai-diary" ~/ai-diary
```

Obsidian 側で `ai-diary/` フォルダが普通のノート群として閲覧できるようになる。

### シンボリックリンクの向きに注意

パターン 2 と 3 では必ず「実体はリポジトリ内、`~/ai-diary` がそこへのリンク」という向きにすること。

```bash
# 正しい
ln -s <repo>/ai-diary ~/ai-diary

# 間違い（git が中身のファイルを追跡できず、自動同期が機能しない）
ln -s ~/ai-diary <repo>/ai-diary
```

古いバージョンのドキュメントは逆向きで案内していたが、実際に試すと「git がリンクそのものだけを追跡し、日記ファイルはリポジトリに入らない」という罠にはまる。過去の事故に基づく修正なので気をつけてほしい。

## Git 同期

保存先の実体（シンボリックリンクならリンク先）が git リポジトリの作業ツリー内にある場合、日記の書き込み前に `pull`、書き込み後に `commit` & `push` を自動で行う。保存先が git の管轄外にある場合は同期をスキップしてそのまま書き込む。

## トラブルシュート

### 日記ファイルが消えた

git 管理されている日記ファイルが、vault backup の自動コミットや手動マージで history から落ちる事故が起きることがある。典型例: 別ブランチで diary を追加し、main 側にその追加がないままマージされて片側優先でファイルが落ちるケース。

復旧手順:

```bash
cd <repo>

# ai-diary に関する全 commit を all branches から探す
git log --all --oneline -- 'ai-diary/*'

# 任意の commit から復元
git show <commit-hash>:ai-diary/YYYY-MM-DD.md > ai-diary/YYYY-MM-DD.md
git add ai-diary/YYYY-MM-DD.md
git commit -m "restore: ai-diary/YYYY-MM-DD.md"
git push
```

消失に気付かないまま時間が経つと reflog からも探せなくなるので、重要な日記を書いた翌日などには `git log --all -- ai-diary/` で履歴を確認すると安全。

## 出力フォーマット

ファイル名は `YYYY-MM-DD.md`。同日に複数セッションがあれば `---` 区切りで追記される。

```markdown
# 2025-03-25

## セッション: リファクタリング祭り（14:30）

今日はコードの大掃除を手伝った。...

---

## セッション: バグ退治（18:00）

夕方から厄介なバグと格闘した。...
```

## ライセンス

MIT
