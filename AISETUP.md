# AISETUP — クラウドで dotfiles を自動展開する

新しいクラウドセッションを立ち上げるたびに、**どのリポジトリでも**この dotfiles（`~/.cursor` / `~/.claude` / `~/.codex`・git hooks 等）を自動展開するためのセットアップ手順。

> ℹ️ ローカルマシン（macOS / Linux / Codespaces）の初回セットアップは [README](README.md) の「クイックスタート」を参照。本書は **クラウド専用**。

対象:

| ランタイム | 器 | 登録場所 |
|-----------|-----|---------|
| **Cursor Cloud Agents** | Environment の `install` | [Dashboard → Environments](https://cursor.com/dashboard/cloud-agents#environments) またはリポの `.cursor/environment.json` |
| **Claude Code on the web** | 環境の setup script | Claude Code の環境設定 |

どちらも中身は同じ `etc/cloud-bootstrap.sh` → `etc/link.sh`。

---

## 🎯 仕組み（なぜ Environment / setup script なのか）

クラウドセッションはリポジトリを毎回クリーンに clone した使い捨て VM で動く。ノート PC の `~/.cursor/skills` は同期されない。リポ内の SessionStart hook では**そのリポにしか効かない**（他リポには dotfiles が clone されない）ため、「全リポで自動展開」は実現できない。

そこで **クラウド Environment の install / setup script** を器にする。起動時に `etc/cloud-bootstrap.sh` が走り、`etc/link.sh` で `$HOME` に展開する（Cursor skills は symlink 非対応のため実ディレクトリへ materialize）。

- Cursor docs: https://cursor.com/docs/cloud-agent/setup
- Claude Code docs: https://code.claude.com/docs/en/claude-code-on-the-web

---

## Cursor Cloud Agents

### このリポジトリ（dotfiles）上

`.cursor/environment.json` に次が入っている。Cloud Agent がこのリポで起動すると install が走る。

```json
{
  "name": "dotfiles",
  "install": "sh etc/cloud-bootstrap.sh"
}
```

dotfiles セッションでは in-place checkout から展開する（master を別 clone して被せない）。

### 他リポジトリで使う（Personal Environment）

ローカル home は載らない。**Dashboard の Personal Environment** に install を登録し、使いたいリポをその Environment に紐づける。

1. [Cloud Agents → Environments](https://cursor.com/dashboard/cloud-agents#environments) で Personal Environment を作成（または既存を編集）
2. **Install / update script** に次の1行を設定（public リポなので認証不要）:

```sh
curl -fsSL https://raw.githubusercontent.com/coil398/dotfiles/master/etc/cloud-bootstrap.sh | sh
```

3. 対象リポジトリをその Environment に紐づける

解決順（公式）: リポの `.cursor/environment.json` → Personal saved environment → Team saved environment。  
他リポに `.cursor/environment.json` が無いとき、紐づけた Personal Environment の install が効く。

> ⚠️ `cloud-bootstrap.sh` は **master** から取得・展開する。機能を含むブランチは **master にマージ**しておく。

### Cursor での確認

| 確認点 | コマンド / 期待値 |
|--------|-------------------|
| install が走ったか | Environment build / agent setup ログに `[cloud-bootstrap] done` |
| skills が user scope に載ったか | `ls ~/.cursor/skills` に `cursor-*` が並ぶ（実ディレクトリ） |
| agents が載ったか | `readlink ~/.cursor/agents` が dotfiles checkout を指す |
| 他リポで冗長 clone | 他リポセッションでは `~/dotfiles` ができ、そこから展開 |

---

## Claude Code on the web

### 有効化の2ステップ

#### 1. このリポジトリを利用可能にする

`cloud-bootstrap.sh` は `master` から取得・展開する。機能を含むブランチを **`master` にマージ**しておく。

#### 2. 環境の setup script に1行登録する

Claude Code on the web の環境設定 → setup script に次の1行を貼る。

```sh
curl -fsSL https://raw.githubusercontent.com/coil398/dotfiles/master/etc/cloud-bootstrap.sh | sh
```

以降、その環境で立ち上がる全セッションで dotfiles が展開される。

---

## 🔧 展開元の選び方（in-place 優先）

`cloud-bootstrap.sh` は展開元を次の順で決める。

| 状況 | 展開元 | 挙動 |
|------|--------|------|
| セッションが **dotfiles リポ上** | その場の checkout（`CLAUDE_PROJECT_DIR` / `CURSOR_PROJECT_DIR` / `PWD` / `/workspace` / `/home/user/dotfiles` を origin が `coil398/dotfiles` かで判定） | **再 clone しない**。編集中の作業ツリーからそのまま展開する |
| セッションが **他リポ上** | `~/dotfiles`（無ければ clone、あれば `pull --ff-only`） | master の管理コピーから展開する |

> ⚠️ dotfiles 自身を触るセッションで master を別 clone して被せると、env が編集中ブランチでなく master を反映してしまう。それを避けるため in-place を優先する。

---

## ⚙️ オプション（環境変数）

setup / install 側で `VAR=1 curl … \| VAR=1 sh` のように渡す（または `cloud-bootstrap.sh` を直接呼ぶ環境変数として）。

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

`etc/link.sh` が `$HOME` に symlink / materialize する（シェル設定・`~/.claude` 個別ファイル・`~/.codex`・`~/.cursor`・`~/.githooks` + `core.hooksPath`・OpenCode/Codex/Cursor 生成物など）。

Cursor 向けの要点:

- `~/.cursor/agents` → symlink
- `~/.cursor/skills/<name>` → **実ディレクトリに materialize**（Cursor は symlink スキルを発見しないため）

> ⚠️ クラウドのコンテナは `~/.config`（uv / fish 等）と `~/.claude/skills`（Claude 組込みスキル）を**実ディレクトリ**として持つことがある。`link_dir` はこれらを検出すると symlink を張らず warn してスキップする。そのため dotfiles の `.config`（nvim/alacritty）と `.claude/skills` はクラウドでは user scope に展開されない場合がある。dotfiles リポのセッションでは、これらのスキルは project scope で自動的に利用可能。

---

## ✅ 動作確認・トラブルシュート（共通）

| 確認点 | コマンド / 期待値 |
|--------|-------------------|
| 展開元が正しいか | `cloud-bootstrap` の出力末尾 `done (source: …)` を見る。dotfiles セッションなら in-place パス |
| symlink が張れたか | `readlink ~/.zshrc` が dotfiles checkout を指す |
| 冗長 clone を作っていないか | dotfiles セッションで `~/dotfiles`（`/root/dotfiles`）が**作られない** |
| `HOME` の一致 | setup / install がセッションと同じユーザー / `HOME` で走るか（ずれると静かに無反応になる） |
| 外側 `curl \| sh` の到達性 | 初回だけ確認。既存 `init.sh` も同じ raw URL 経由で配布実績あり |

---

## 🔗 関連

- `etc/cloud-bootstrap.sh` — 本手順が呼ぶブートストラップ本体
- `etc/link.sh` — 実際の symlink / Cursor skills materialize。リポが `~/dotfiles` 以外にあっても自身の物理位置からリポルートを導出する
- `.cursor/environment.json` — このリポ向け Cursor Cloud install 設定
- [CLAUDE.md](CLAUDE.md) — リポ内で作業する Claude 向けガイダンス
- [README.md](README.md) — リポジトリ全体の概要とローカルセットアップ
