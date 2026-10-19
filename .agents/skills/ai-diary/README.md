# ai-diary

複数のAI runtimeで使える、AIが日記を書くスキル。

セッション中の会話を振り返り、AIの一人称視点で日記風のテキストを生成・保存する。技術ログではなく、出来事の流れや気づき・感想を自然な文章で綴る。

## インストール

利用するruntimeの共有Skill配置へこのリポジトリを配置する:

```bash
# ユーザースコープ（全プロジェクト共通）
git clone https://github.com/coil398/ai-diary.git ~/.agents/skills/ai-diary

# プロジェクトスコープ（特定プロジェクトのみ）
git clone https://github.com/coil398/ai-diary.git .agents/skills/ai-diary
```

## 使い方

対応runtimeのセッション中に以下のように呼び出す:

```
/ai-diary
```

「日記を書いて」「今日の感想を振り返って」など、日記や感想の依頼でも使う。作業結果からの改善提案は `/retro` を使う。

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

これでスキルは `~/ai-diary/YYYY-MM-DD.md` に書き込むが、実体は `$REPO/ai-diary/` にある。Git への同期は、今回の依頼または既存 setup で明示的に有効化されている場合だけ行う。

### 3. Obsidian Vault 連携

上記の特殊ケース。Vault が git 管理されていれば、そのまま連携できる:

```bash
VAULT=~/ObsidianVault
mkdir -p "$VAULT/ai-diary"
ln -s "$VAULT/ai-diary" ~/ai-diary
```

Obsidian 側で `ai-diary/` フォルダが普通のノート群として閲覧できるようになる。

### シンボリックリンクの向きに注意

パターン 2 と 3 では「実体はリポジトリ内、`~/ai-diary` がそこへのリンク」という向きにする。

```bash
# 正しい
ln -s <repo>/ai-diary ~/ai-diary

# 間違い（git がリンク先の中身を追跡できない）
ln -s ~/ai-diary <repo>/ai-diary
```

逆向きにすると git がリンクそのものだけを追跡し、日記ファイルはリポジトリに入らないため、この向きを使う。

## Git 同期

保存先の実体（シンボリックリンクならリンク先）が git リポジトリの作業ツリー内にあっても、日記の書き込みだけでは `pull`、`commit`、`push` を行わない。同期が今回の依頼または既存 setup で明示的に有効化されている場合だけ、親が対象 repository、branch、対象ファイルを確定して既存の同期手段へ渡す。保存先が git の管轄外にある場合はそのまま書き込む。

## トラブルシュート

### 日記ファイルが消えた

復旧時は対象リポジトリとファイルの履歴を確認し、承認範囲と Git 同期の条件に従う。詳細は [SKILL.md の Git 同期手順](SKILL.md#6-git-同期明示された場合だけ) を参照する。

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
