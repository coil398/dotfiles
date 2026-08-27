# AISETUP — クラウドで dotfiles を自動展開する

Claude Code on the web / Cursor Cloud Agents で**新しいクラウドセッションを立ち上げるたびに、どのリポジトリでも**この dotfiles（シェル設定・`~/.claude` / `~/.codex` / `~/.cursor` スキル・git hooks 等）を自動展開するためのセットアップ手順。

> ℹ️ ローカルマシン（macOS / Linux / Codespaces）の初回セットアップは [README](README.md) の「クイックスタート」を参照。本書は **クラウド専用**。

共通の実行体は `etc/cloud-bootstrap.sh`。登録先だけがランタイムごとに違う。

| ランタイム | 登録先 |
|-----------|--------|
| Claude Code on the web | 環境の **setup script** |
| Cursor Cloud Agents | 環境の **`install`**（任意で `start` も） |

docs:

- Claude: https://code.claude.com/docs/en/claude-code-on-the-web
- Cursor: https://cursor.com/docs/cloud-agent/setup

---

## 🎯 仕組み（なぜ環境の bootstrap なのか）

クラウドセッションはリポジトリを毎回クリーンに clone した使い捨てコンテナで動く。リポ内の SessionStart hook / project skill だけでは**そのリポにしか効かない**（他リポには dotfiles が clone されない）ため、「全リポで自動展開」は実現できない。

そこで **環境の bootstrap コマンド**に `etc/cloud-bootstrap.sh` を載せ、セッション（または Build）準備時に `etc/link.sh` で `$HOME` へ展開する。

Cursor ではスキルは `~/.cursor/skills/<name>/` に**実ディレクトリとして materialize** される（symlink だと Cursor が発見しない）。`link.sh` がこれを行う。

---

## ⏭️ 有効化（共通の1行）

登録するまでは動かない。機能を含むブランチを **`master` にマージ**しておく（マージ前は下記 URL が 404 になり、clone 側にも修正が乗らない）。

dotfiles は public リポなので認証不要。登録するコマンドはどちらも同じ:

```sh
curl -fsSL https://raw.githubusercontent.com/coil398/dotfiles/master/etc/cloud-bootstrap.sh | sh
```

---

## Claude Code on the web

環境設定 → **setup script** に上記1行を貼る。以降、その環境で立ち上がる全セッションで dotfiles が展開される。

---

## Cursor Cloud Agents

### 前提（環境はリポ単位）

Cursor の環境設定は **リポジトリ（または multi-repo グループ）単位**で解決される。グローバルに「全リポ一括」の setup script はない。解決順は次の通り（先勝ち）:

1. そのリポの `.cursor/environment.json`
2. 個人の saved environment
3. チームの saved environment

そのため「手元からさっと任意リポで使う」ときは、対象リポの環境 `install` に上記1行を足す（または既存 `install` の先頭／末尾に並べる）。

### 推奨: 個人 environment の `install` に1行足す

[Cloud Agents dashboard](https://cursor.com/dashboard/cloud-agents#environments) で対象リポの個人 environment を開き、`install` に次を入れる（プロジェクト固有の依存インストールがあるなら**その前後に並べる**）:

```sh
curl -fsSL https://raw.githubusercontent.com/coil398/dotfiles/master/etc/cloud-bootstrap.sh | sh
```

例（Node リポ）:

```json
{
  "install": "curl -fsSL https://raw.githubusercontent.com/coil398/dotfiles/master/etc/cloud-bootstrap.sh | sh\nnpm ci"
}
```

> ⚠️ 対象リポに **committed な** `.cursor/environment.json` があると、それが個人／チーム saved environment より優先される。その場合はファイル側の `install` に同じ行を追記するか、セッション内で一度だけ上記 curl を手動実行する。

### Builds 利用時の置き場所

Environment Builds が有効なとき、`install` は **Build 作成時**に走り、成功したディスク状態がスナップショットされる。新規エージェント起動のたびに `install` は再実行されない。

| 置き場所 | 向いている用途 |
|----------|----------------|
| `install` | スキル・設定を Build に焼き込む（起動が速い。dotfiles 更新後は Build し直し） |
| `start` | 毎回 `master` を pull して最新スキルを載せたい（起動が少し重い） |

普段は `install` だけで足りる。スキルを頻繁に master へ載せ替えるなら、同じ1行を `start` にも置く（`cloud-bootstrap.sh` は冪等）。

### 今すぐ1回だけ試す

環境を触らず、起動済みエージェントのシェルで上記 curl を実行すれば、そのセッションだけ展開できる。確認:

```sh
ls ~/.cursor/skills/pir2/SKILL.md
readlink ~/.cursor/rules/shared-agents.mdc
```

新しいエージェントではスキル一覧に載る（既に動いているセッションは起動時にスキルを解決していることがあるので、確認は新規起動が確実）。

### multi-repo で dotfiles を同居させる別解

環境作成時に対象リポと `coil398/dotfiles` の両方を選ぶと、エージェント VM に両方 clone される。その場合は curl ではなく、clone 済みパスから `etc/link.sh` を呼んでもよい（パスは環境のレイアウトに合わせる）。手軽さでは curl 1行の方が勝つ。

---

## 🔧 展開元の選び方（in-place 優先）

`cloud-bootstrap.sh` は展開元を次の順で決める。

| 状況 | 展開元 | 挙動 |
|------|--------|------|
| セッションが **dotfiles リポ上** | その場の checkout（`CLAUDE_PROJECT_DIR` / `PWD` / `/workspace` / `/home/user/dotfiles` を origin が `coil398/dotfiles` かで判定） | **再 clone しない**。編集中の作業ツリーからそのまま展開する |
| セッションが **他リポ上** | `~/dotfiles`（無ければ clone、あれば `pull --ff-only`） | master の管理コピーから展開する |

> ⚠️ dotfiles 自身を触るセッションで master を別 clone して被せると、env が編集中ブランチでなく master を反映してしまう。それを避けるため in-place を優先する。

---

## ⚙️ オプション（環境変数）

setup / install 側で `VAR=1 curl … | VAR=1 sh` のように渡す（または `cloud-bootstrap.sh` を直接呼ぶ環境変数として）。

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

`etc/link.sh` が `$HOME` に symlink を張る（シェル設定・`~/.claude` 個別ファイル・`~/.codex`・`~/.githooks` + `core.hooksPath`・OpenCode/Codex/Cursor 生成物など）。Cursor スキルは `~/.cursor/skills/*` へ materialize（実ディレクトリ）。

> ⚠️ クラウドのコンテナは `~/.config`（uv / fish 等）と `~/.claude/skills`（Claude 組込みスキル）を**実ディレクトリ**として持つことがある。`link_dir` はこれらを検出すると symlink を張らず warn してスキップする（ネスト symlink やコンテナ状態の破壊を避けるため）。そのため dotfiles の `.config`（nvim/alacritty）と `.claude/skills` はクラウドでは user scope に展開されないことがある。dotfiles リポのセッションでは、これらのスキルは project scope で利用可能。Cursor の `~/.cursor/skills` は materialize 経路なので、他リポでも user scope で使える。

---

## ✅ 動作確認・トラブルシュート

| 確認点 | コマンド / 期待値 |
|--------|-------------------|
| 展開元が正しいか | `cloud-bootstrap` の出力末尾 `done (source: …)` を見る。dotfiles セッションなら in-place パス |
| symlink / skills が載ったか | `readlink ~/.zshrc` が dotfiles checkout を指す。Cursor なら `ls ~/.cursor/skills/pir2` |
| 冗長 clone を作っていないか | dotfiles セッションで `~/dotfiles` が**作られない** |
| `HOME` の一致 | bootstrap がセッションと同じユーザー / `HOME` で走るか（ずれると静かに無反応になる） |
| Cursor で個人 env が効かない | リポに `.cursor/environment.json` が無いか確認（あればそちらが勝つ） |
| Cursor Builds 後に古いスキルのまま | `install` のみだと Build 時点の状態。再 Build するか `start` にも同じ1行を足す |
| 外側 `curl \| sh` の到達性 | 初回だけ確認。既存 `init.sh` も同じ raw URL 経由で配布実績あり |

---

## 🔗 関連

- `etc/cloud-bootstrap.sh` — 本手順が呼ぶブートストラップ本体
- `etc/link.sh` — 実際の symlink / Cursor skill materialize。リポが `~/dotfiles` 以外にあっても自身の物理位置からリポルートを導出する
- [CLAUDE.md](CLAUDE.md) — リポ内で作業する Claude 向けガイダンス
- [README.md](README.md) — リポジトリ全体の概要とローカルセットアップ
