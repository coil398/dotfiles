---
name: "check-updates"
description: "明示されたディレクトリ内の独立した git clone の upstream 更新を確認し、clean な fast-forward だけを適用する。マーケットプレース・プラグイン・スキルの更新確認、更新チェック、スキル更新、プラグイン最新？、update skills、check for updates に対応する。ユーザーが /check-updates と入力したら必ずこのスキルを使う。"
argument-hint: "[更新対象root ...]"
---

# Check Updates — スキル・プラグイン更新チェック

明示された root の中にある、独立した git clone の upstream 更新を確認します。

## 実行契約

- 更新対象 root は呼び出し元が引数で明示する。ホームディレクトリ、現在の作業ディレクトリ、dotfiles、submodule、別 runtime の配置を暗黙に探索しない。
- 各 root 自体、または root から 3 階層以内にある `.git` を持つディレクトリだけを対象にする。通常ファイル、管理対象ディレクトリ、さらに深い階層は変更しない。
- superproject が管理する git submodule は独立 clone ではないため対象外にする。同じ clone が複数 root から見えても一度だけ確認する。
- 現在の branch に設定された upstream tracking branch を使う。固定した `main` / `master` や固定 remote は使わない。
- clean な fast-forward だけを自動適用する。merge commit、rebase、stash、commit、push、`merge --abort` は実行しない。
- dirty、local ahead、diverged、upstream 未設定、fetch 失敗、fast-forward 失敗は状態を保持して理由を出力し、non-zero で終了する。
- dotfiles 本体やその submodule の同期が必要な場合は、このスキルではなく `/dotfiles-autosync` を明示的に依頼する。

## Claude Code でのチェック対象

次の root は呼び出し元が実在するものだけを引数に渡します。列挙は入力候補の説明であり、自動探索の指示ではありません。

- `$HOME/.claude/plugins/marketplaces`
- `$HOME/.claude/plugins/cache`
- `$HOME/.claude/skills`
- `<project>/.claude/skills`

各 root 自体、または root から 3 階層以内にある独立 clone が対象です。通常の管理ディレクトリ、通常ファイル、superproject の submodule は対象外です。

## 実行手順

### ステップ 1: スクリプトの実行

ユーザーが `/check-updates <更新対象root ...>` と入力した場合、指定された root をそのままスクリプトへ渡します。root を指定しない場合は、スクリプトの Usage と non-zero 終了を報告し、root を勝手に補いません。

ロードした本 `SKILL.md` の実体を絶対パスとして確定し、その親ディレクトリを `SKILL_DIR` に設定して、同梱スクリプトを呼び出します。

```bash
THIS_SKILL_PATH="<ロード済み SKILL.md の絶対パス>"; SKILL_DIR="$(cd -P "$(dirname "$THIS_SKILL_PATH")" && pwd -P)"; bash "$SKILL_DIR/scripts/check-updates.sh" "<更新対象root-1>" "<更新対象root-2>"
```

root の引数は、空白を含む場合もそれぞれ引用します。スクリプトは対象 root を全て走査してから、独立 clone の状態確認と更新を行います。

スクリプトの処理は次のとおりです。

1. 引数で渡された root を検証し、root 自体または 3 階層以内の独立 clone を一度だけ収集する。
2. 各 clone の作業ツリーが clean であることを確認する。dirty なら fetch も更新も行わない。
3. 現在 branch の upstream tracking branch を解決して fetch する。upstream が未設定、fetch が失敗した場合は状態を保持する。
4. ahead / behind を比較し、behind のみの clean clone に `merge --ff-only` を適用する。merge commit、rebase、stash、commit、push は行わない。
5. 全対象の結果、件数、失敗理由を標準出力へ出し、失敗が一件でもあれば non-zero を返す。

### ステップ 2: 結果の報告

標準出力を解析し、チェック対象数、更新数、各対象の状態、失敗理由を報告します。更新済みの対象と失敗した対象が同時にある場合も、両方を記載します。

主なマーカーは次のとおりです。

- `UPDATED:` — clean な clone を upstream へ fast-forward した。
- `UP_TO_DATE:` — fetch 後も local と upstream が同一だった。
- `DIRTY:` — 未コミット変更を保持して fetch/update を見送った。
- `AHEAD:` — local 固有コミットを保持して更新を見送った。push はしない。
- `DIVERGED:` — local と upstream が分岐しているため保持した。
- `NO_UPSTREAM:` — tracking branch が無いため保持した。
- `FETCH_FAILED:` — upstream の fetch に失敗したため保持した。
- `FAST_FORWARD_FAILED:` — fast-forward に失敗したため保持した。
- `SKIPPED_MANAGED_REPO:` — root 自体が管理対象 repo のため、内部を再帰探索しなかった。
- `CHECKED:` / `UPDATED_COUNT:` / `ERRORS:` — 全体件数と終了状態。

**すべて最新の場合:**

```
すべての指定 root 内のスキル・プラグイン clone は最新です。(N リポジトリをチェック)
```

`UPDATED:` がある場合は、対象名と fast-forward された commit 数を記載します。終了コードが non-zero の場合は、更新済み対象があっても失敗対象と理由を併記します。

### ステップ 3: 保全されたローカル変更の報告

`DIRTY:`、`AHEAD:`、`DIVERGED:`、`NO_UPSTREAM:`、`FETCH_FAILED:`、`FAST_FORWARD_FAILED:` がある場合、その対象の状態を保持したまま次の読み取り専用情報を確認して報告します。

```bash
git -C <repo> status -sb
git -C <repo> diff --stat
git -C <repo> log --oneline @{u}..HEAD
```

このスキルから merge、rebase、stash、commit、push、rollback、衝突解消を追加実行しません。dotfiles 本体またはその submodule を扱う場合は `/dotfiles-autosync` の契約に切り替えます。upstream 未設定や分岐の解消が必要なら、状態・対象・必要な次の操作を報告して止めます。

### ステップ 4: 更新後の確認

`UPDATED:` の対象について、報告前に取り込み範囲と変更内容を軽量確認します。実行前の `HEAD` を取得できる場合は、次を使います。

```bash
git -C <repo> log --oneline <old>..<new>
git -C <repo> diff --stat <old>..<new>
```

設定、権限、hook、破壊的操作に関係する変更や、追従が必要な点があれば要約します。実行前の hash が記録されていない場合は、確認できた範囲と未確認であることを明記します。

## ClaudeSessionStart の扱い

SessionStart には更新 root が明示されないため、このスキルを自動起動しません。更新確認はユーザーが root を指定した `/check-updates` で開始します。他の SessionStart 以外の hook はそれぞれの契約に従います。
