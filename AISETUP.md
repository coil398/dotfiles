# AISETUP — Claude Code on the web（クラウド）で dotfiles を自動展開する

Claude Code on the web で**新しいクラウドセッションを立ち上げるたびに、どのリポジトリでも**この dotfiles（シェル設定・`~/.claude` / `~/.codex`・git hooks 等）を自動展開するためのセットアップ手順。

> ℹ️ ローカルマシン（macOS / Linux / Codespaces）の初回セットアップは [README](README.md) の「クイックスタート」を参照。本書は **Claude Code on the web（クラウド）専用**。

---

## 🎯 仕組み（なぜ setup script なのか）

クラウドセッションはリポジトリを毎回クリーンに clone した使い捨てコンテナで動く。リポ内の SessionStart hook では**そのリポにしか効かない**（他リポには dotfiles が clone されない）ため、「全リポで自動展開」は実現できない。

そこで **環境の setup script**（Claude Code on the web の環境設定に登録するスクリプト）を器にする。setup script がセッション起動時に `etc/cloud-bootstrap.sh` を実行し、dotfiles を `etc/link.sh` で `$HOME` に展開する。

docs: https://code.claude.com/docs/en/claude-code-on-the-web

---

## ⏭️ 有効化の2ステップ

登録するまでは動かない。順に行う。

### 1. このリポジトリを利用可能にする

`cloud-bootstrap.sh` は `master` から取得・展開する。機能を含むブランチを **`master` にマージ**しておく（マージ前は下記 URL が 404 になり、clone 側にも修正が乗らない）。

### 2. 環境の setup script に1行登録する

Claude Code on the web の環境設定 → setup script に次の1行を貼る。dotfiles は public リポなので認証不要。

```sh
curl -fsSL https://raw.githubusercontent.com/coil398/dotfiles/master/etc/cloud-bootstrap.sh | sh
```

以降、その環境で立ち上がる全セッションで dotfiles が展開される。

---

## 🔧 展開元の選び方（in-place 優先）

`cloud-bootstrap.sh` は展開元を次の順で決める。

| 状況 | 展開元 | 挙動 |
|------|--------|------|
| セッションが **dotfiles リポ上** | その場の checkout（`CLAUDE_PROJECT_DIR` / `PWD` / `/home/user/dotfiles` を origin が `coil398/dotfiles` かで判定） | **再 clone しない**。編集中の作業ツリーからそのまま展開する |
| セッションが **他リポ上** | `~/dotfiles`（無ければ clone、あれば `pull --ff-only`） | master の管理コピーから展開する |

> ⚠️ dotfiles 自身を触るセッションで master を別 clone して被せると、env が編集中ブランチでなく master を反映してしまう。それを避けるため in-place を優先する。

---

## ⚙️ オプション（環境変数）

setup script 側で `VAR=1 curl … | VAR=1 sh` のように渡す（または `cloud-bootstrap.sh` を直接呼ぶ環境変数として）。

| 変数 | 既定 | 用途 |
|------|------|------|
| `DOTFILES_INSTALL` | `0` | `1` で `install.sh` も実行し apt/prebuilt tools（zsh, nvim, ripgrep, gitleaks 等）を入れる。**sudo 必要**・展開より重い |
| `DOTFILES_DIR` | 自動判定 | 展開元 checkout を明示指定（判定と clone をスキップ） |
| `DOTFILES_REPO_URL` | public HTTPS remote | clone 元 URL |
| `DOTFILES_BRANCH` | `master` | clone するブランチ |

例（tools も入れる）:

```sh
curl -fsSL https://raw.githubusercontent.com/coil398/dotfiles/master/etc/cloud-bootstrap.sh | DOTFILES_INSTALL=1 sh
```

---

## 📋 展開されるもの／スキップされるもの

`etc/link.sh` が `$HOME` に symlink を張る（シェル設定・`~/.claude` 個別ファイル・`~/.codex`・`~/.githooks` + `core.hooksPath`・OpenCode/Codex/Cursor 生成物など）。

> ⚠️ クラウドのコンテナは `~/.config`（uv / fish 等）と `~/.claude/skills`（Claude 組込みスキル）を**実ディレクトリ**として持つ。`link_dir` はこれらを検出すると symlink を張らず warn してスキップする（`~/.config/.config` のようなネスト symlink 生成やコンテナ状態の破壊を避けるため）。そのため dotfiles の `.config`（nvim/alacritty）と `.claude/skills` はクラウドでは user scope に展開されない。dotfiles リポのセッションでは、これらのスキルは project scope で自動的に利用可能。

---

## ✅ 動作確認・トラブルシュート

| 確認点 | コマンド / 期待値 |
|--------|-------------------|
| 展開元が正しいか | `cloud-bootstrap` の出力末尾 `done (source: …)` を見る。dotfiles セッションなら in-place パス |
| symlink が張れたか | `readlink ~/.zshrc` が dotfiles checkout を指す |
| 冗長 clone を作っていないか | dotfiles セッションで `~/dotfiles`（`/root/dotfiles`）が**作られない** |
| `HOME` の一致 | setup script がセッションと同じユーザー / `HOME` で走るか（ずれると静かに無反応になる）。初回展開後 `readlink ~/.zshrc` で確認 |
| 外側 `curl \| sh` の到達性 | 初回だけ確認。既存 `init.sh` も同じ raw URL 経由で配布実績あり |

---

## 🔗 関連

- `etc/cloud-bootstrap.sh` — 本手順が呼ぶブートストラップ本体
- `etc/link.sh` — 実際の symlink 展開。リポが `~/dotfiles` 以外にあっても自身の物理位置からリポルートを導出する
- [CLAUDE.md](CLAUDE.md) — リポ内で作業する Claude 向けガイダンス
- [README.md](README.md) — リポジトリ全体の概要とローカルセットアップ
