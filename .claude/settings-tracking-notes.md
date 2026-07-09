# Claude Code グローバル設定と dotfiles 追跡ガイド

`/doctor` 診断（2026-07-09）で判明した、`~/.claude/settings.json` の扱いに関する方針メモ。

## 構造の前提

`~/dotfiles`（branch `master` / remote `github.com:coil398/dotfiles`）が `~/.claude/` を **symlink で管理**している。

| 種別 | 例 | 追跡すべきか |
|---|---|---|
| 宣言的 config（config-as-code） | `CLAUDE.md`, `agents/`, `skills/`, `*-protocol.md` 等 | ✅ 追跡する（symlink 済） |
| アプリ管理の可動状態 | `settings.json`, `settings.local.json` | ❌ 追跡しない（推奨） |

## なぜ settings.json を追跡しないか

`settings.json` は **Claude Code がアプリ側で常時書き換える mutable file**（`/model`・`/config`・プラグイン切替・auto mode 等でその都度上書き）。

- アプリが直接書き込むため **symlink が壊れて実ファイル化**しやすい。実際 `~/.claude/settings.json` は symlink が外れて実ファイル化し、dotfiles 追跡コピー（`~/dotfiles/.claude/settings.json`）と**双方向にドリフト**していた。
  - live 側: LSP 無効化・フック matcher の編集
  - tracked 側: `model` キー削除・`advisorModel` 再配置
  - → どちらも相手の上位互換でなく、単純コミットするとどちらかが失われる
- マシン固有値（model, effortLevel, tui, plugin トグル）を含み、クロスマシン同期にも不向き。

> 💡 宣言的な config-as-code（CLAUDE.md / agents / skills）だけ追跡し、マシン状態は追跡しないのが原則。

## 追跡から外す手順（実行したくなったとき）

dotfiles には他の未コミット変更（`CLAUDE.md`, `skills/pir2/references/experimental.md` 等）が同居しうるので、**個別 stage して `git diff --cached` で確認**してから push する（`git add -A`/`.` は使わない）。

```bash
# settings.local.json は clean だが settings.json は working 変更あり。--cached は index==HEAD なら -f 不要
git -C ~/dotfiles rm --cached .claude/settings.json .claude/settings.local.json

# .gitignore にリポルート基準で追記（既存の /.claude/hooks/... と同形式）
#   /.claude/settings.json
#   /.claude/settings.local.json
git -C ~/dotfiles add .gitignore

git -C ~/dotfiles diff --cached --stat   # settings 2件 + .gitignore のみか確認
git -C ~/dotfiles commit -m "chore(claude): stop tracking app-managed settings.json"
git -C ~/dotfiles push origin master
```

`git rm --cached` は working ファイルを消さない（index からのみ除外）。残る `~/dotfiles/.claude/settings.json` は ignore された孤児になるので、不要なら手で削除してよい。live 設定は別実体の `~/.claude/settings.json`。

## もし追跡を維持したい場合（非推奨）

tracked コピーに live の編集を jq 等でマージして commit/push する。ただし **アプリの書き換えでドリフトが再発する**ため、恒久運用には向かない。同期したいなら live ファイルではなく手書きの最小テンプレを別途持つ。

## 今セッションで live（`~/.claude/settings.json`）に適用済みの修正

| 変更 | 内容 | 戻し方 |
|---|---|---|
| 未使用 LSP プラグイン無効化 | `enabledPlugins` の `rust-analyzer-lsp@claude-plugins-official` と `pyright-lsp@claude-plugins-official` を `false`（Go/TS 環境で導入来0回） | `true` に戻す or `/plugin` |
| SessionStart フック高速化 | `check-updates` フックの matcher を `null` → `"startup"` | matcher を `null`（または削除） |

## 遅いフックの根本原因（参考）

`check-updates` の SessionStart フックが `~/.claude/skills/check-updates/scripts/check-updates.sh` を実行し、**8 リポに git 操作（ネットワーク）** を行うため **~48秒/回**（最悪 124秒）。matcher が `null` だと `startup`/`compact`/`resume`/`clear` の**全 SessionStart で発火**し、特に **自動 compact が 95回**発火して毎回 ~48秒ブロックしていた。matcher を `startup` のみに絞ることで、新規起動時の1回だけに限定した。
