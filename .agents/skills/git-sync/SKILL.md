---
name: git-sync
description: >-
  明示された Git リポジトリを、既存の upstream に対して fetch・pull・競合確認・push する。
  スキルやプラグインの更新は別の依頼として扱う。自然言語トリガー例: 「git sync」「同期して」
  「pullしてpush」「リモートと揃えて」。ユーザーが /git-sync と入力したら使う。
argument-hint: "[リポジトリルート。省略時は cwd]"
---

# /git-sync — 明示対象リポジトリの同期

ユーザーが同期を依頼した対象リポジトリだけを、そこに設定済みの upstream と同期します。対象の確定、既存 upstream の確認、ローカル変更の保全、結果の報告を親が持ちます。スキル・プラグインの更新はこの手順に含めず、別途依頼された場合にその専用スキルへ渡します。

## 責任と読者

これは親が対象を確定して直接実行する同期手順である。親はロードしたこの Skill、対象 repository の既存規則、preflight の実測値を読み、commit・pull・push の承認境界と完了条件を保持する。短い対象の preflight を理由に別の司令塔や子を起動しない。

read-only の確認を委任する場合は、親が確認済みの対象 path、対象版、必要な本文の物理 path、変更禁止範囲、返却形式を渡し、担当自身に資料を Read させる。担当は status/upstream/競合の観測だけを親へ返し、commit・push・report保存・記憶追記を行わない。Git の副作用、失敗時の状態保持、未反映範囲の統合と報告は親が行う。

## 1. 対象と承認

引数はランタイムの構造化された引数として解釈します。対象を省略した場合は呼び出し元が渡した現在のディレクトリを使い、未引用の shell word splitting や glob 展開で再解釈しません。指定された path を実体化して Git top-level を確認し、リポジトリ外なら停止して報告します。

同期には fetch、pull、必要な commit、push が含まれます。今回の依頼または既存 setup で明示された対象と操作範囲をそのまま使い、同じ承認を繰り返し求めません。依頼に含まれない別リポジトリ、skill/plugin clone、remote 設定変更は操作しません。

## 2. preflight

対象の Git root、branch、設定済み upstream、remote URL、進行中操作、作業ツリーを実測します。

```bash
ROOT="<runtime が確定した対象 path>"
ROOT="$(cd -P "$ROOT" && pwd)"
GIT_ROOT="$(git -C "$ROOT" rev-parse --show-toplevel)"
BRANCH="$(git -C "$GIT_ROOT" symbolic-ref --quiet --short HEAD)"
UPSTREAM="$(git -C "$GIT_ROOT" rev-parse --abbrev-ref --symbolic-full-name '@{upstream}')"
REMOTE="${UPSTREAM%%/*}"
REMOTE_BRANCH="${UPSTREAM#*/}"
git -C "$GIT_ROOT" remote get-url "$REMOTE"
git -C "$GIT_ROOT" status -sb
git -C "$GIT_ROOT" status --short
git -C "$GIT_ROOT" log --oneline -5
```

detached HEAD、upstream 未設定、upstream remote 不在、未完了の merge/rebase/cherry-pick/revert がある場合は、状態を変えずに停止します。`origin/<branch>` や別 remote を推測して採用しません。

## 3. ローカル変更

作業ツリーが dirty なら path ごとに一覧を表示します。依頼で対象 path と保全 commit が明示されている場合だけ、その path を個別に stage して commit できます。依頼に含まれない WIP、untracked、秘密情報、一時ファイルは stage・commit せず、pull の前に停止して未反映範囲を報告します。`git add -A`、`git add .`、blind stash、reset、checkout による破棄は行いません。

個別 commit が必要な場合は、対象を再確認し、`git diff --cached` / `git diff --cached --stat` を確認してから既存のメッセージ規約で commit します。空の変更は commit しません。

## 4. fetch と pull

既存 upstream の remote と branch を使って fetch します。

```bash
git -C "$GIT_ROOT" fetch "$REMOTE" "$REMOTE_BRANCH"
git -C "$GIT_ROOT" status -sb
```

作業ツリーが clean で、upstream に取り込み対象がある場合だけ pull します。リポジトリの `AGENTS.md` / `CLAUDE.md` が線形履歴を要求する場合は `git pull --rebase "$REMOTE" "$REMOTE_BRANCH"`、それ以外は `git pull --no-rebase --no-edit "$REMOTE" "$REMOTE_BRANCH"` を使います。`pull.rebase` の暗黙設定や、別 remote の自動選択に依存しません。

## 5. 競合

生成物や機械的に再現できるファイルは、確認済みの生成手順で再生成して解決します。意味のあるコンテンツの競合は、各 path の ours/theirs、採用理由、失われる情報、復元手順を示してユーザー判断を待ちます。解決時も競合 path だけを stage し、進行中操作を対応する Git コマンドで続行します。`reset --hard`、強制 checkout、未確認の片側採用はしません。

## 6. push

pull と競合処理が成功し、対象 repository が clean であることを確認してから、既存 upstream へ push します。push の承認が今回の依頼または既存 setup に含まれている場合は再確認しません。

```bash
git -C "$GIT_ROOT" push "$REMOTE" "HEAD:$REMOTE_BRANCH"
```

force push、remote の新設、tracking 設定の変更は行いません。push 失敗時は成功扱いにせず、作成済み local commit、remote、branch、未反映範囲を報告します。

## 7. 報告

実際に確認した値だけを報告します。

```text
## git sync 結果
- repository: <実在する Git root>
- branch: <branch>
- upstream: <remote>/<branch>
- fetch: ok | failed (<reason>)
- local commit: <hash> <subject> | なし
- pull: rebase|merge / clean|conflicted|not-run (<reason>)
- push: ok | failed (<reason>) | not-run (<reason>)
- status: <git status -sb の実測結果>
- 未反映: <実際に残った path または なし>
```

## 禁則

- 依頼範囲外の repository、skill/plugin clone、remote を操作しない
- upstream が無いときに `origin/<branch>` を仮定しない
- dirty path を一律 commit しない
- `git add -A` / `git add .`、秘密ファイルの commit、force push をしない
- 確認なしに local 変更を破棄しない
- remote URL、branch、pull 方針、git config を勝手に変更しない
