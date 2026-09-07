---
name: "dotfiles-autosync"
description: "dotfiles本体を、ユーザーの明示依頼に限って中央 engine で保全commit、no-rebase merge、adapter再生成、submodule整合、pushまで同期する。自然言語トリガー例: 「dotfilesを同期して」／「dotfilesの変更を保全して」／「adapterを再生成して同期して」／「dotfilesをpushして」。スキル・プラグインの更新確認は別の check-updates の責務であり、このスキルはdotfiles本体だけを扱う。ユーザーが /dotfiles-autosync と入力したら使う。"
argument-hint: "[dotfiles の Git top-level]"
---

# Dotfiles Autosync

dotfiles リポジトリ自身を、ユーザーが明示的に依頼したときだけ同期します。対象 root、既存 upstream、実行結果を親が確認し、失敗時も復旧して完了まで進めます。スキルの実装は runtime ごとに複製せず、中央 engine の etc/dotfiles-autosync.sh に集約します。

## 責任と読者

親が dotfiles の root、既存 upstream、今回許可された commit・merge・生成・push の範囲、完了条件を確定する。親はロードした Skill の実体から `etc/dotfiles-autosync.sh` の物理 path を解決し、engine の実測 marker と復旧情報を統合する。engine 以外の子や別の司令塔へ同期工程を再起動させない。

read-only の preflight や結果確認を委任する場合は、親が確認済みの Skill/engine path、対象、変更禁止範囲、返却形式を担当へ渡し、担当自身に必要な本文を Read させる。担当は観測結果だけを親へ返す。engineの副作用は同期依頼に含まれ、既存の個別path・バックアップ境界に従う。保存・commit・pushの結果確認と未反映範囲の報告は親が持つ。

## 中央 engine の解決と起動

engineはdirty pathを一括収集するため、親は起動・再実行の前に親repoと各submoduleのstaged/unstaged/untracked内容を確認する。秘密・一時バックアップ・ユーザーが除外したpathは、共有 `git-sync` のpath限定退避手順で保全し、engineの収集対象から外す。除外物はengine完了後に復元し、その保持状態を報告する。秘密検出hookの有無にこの事前確認を依存させない。

親は現在ロードしたこの SKILL.md の実体 path を runtime から受け取り、SKILL_FILE として確定します。home の固定 path、別の dotfiles checkout、未確認の fallback を補ってはいけません。次のコマンドは、ロード済み Skill が dotfiles checkout 内にあることを確認して、その checkout の中央 engine を明示 root に対して起動します。

~~~bash
SKILL_FILE="<runtime が渡したロード済み SKILL.md の実体 path>"
[ -f "$SKILL_FILE" ] &&
SKILL_DIR="$(cd -P "$(dirname "$SKILL_FILE")" 2>/dev/null && pwd)" &&
DOTFILES_ROOT="$(cd -P "$SKILL_DIR/../../.." 2>/dev/null && pwd)" &&
[ -f "$DOTFILES_ROOT/etc/dotfiles-autosync.sh" ] ||
  { printf 'dotfiles-autosync: loaded source has no engine: %s\n' "$DOTFILES_ROOT/etc/dotfiles-autosync.sh" >&2; exit 1; }
bash "$DOTFILES_ROOT/etc/dotfiles-autosync.sh" "${1:-$DOTFILES_ROOT}"
~~~

上記の解決に失敗したら、親は指定対象のGit top-levelとスキル配置を調べ、同じdotfiles checkoutの共有原本とengineの実在を確認して起動する。候補を実在確認できない場合だけ未実行理由を報告する。

## engine が行う処理

中央 engine は次を順番に実行します。

- Git root、既存の upstream、branch、未完了操作を preflight する
- recursive submodule を深い階層から、dirty path の個別 stage・cached diff 確認・保全 commit・fetch・git pull --no-rebase --no-edit・push する
- 親 dotfiles の tracked/staged/untracked 変更を保全 commit する
- 親を no-rebase merge し、git submodule sync/update と Codex/OpenCode/Cursor/Antigravity の adapter generator を実行する
- 生成物と submodule pointer の差分だけを個別 stage・cached diff 確認・commit し、clean/behind 0 を確認して push する

## 同期範囲と親の復旧

同期依頼には通常のWIP保全、実コンテンツ・gitlink競合の統合、生成物・ホーム配備コピー・リンクの更新、検証、commit・pushを含む。`git-sync` から対象dotfilesの同期を引き継いだ場合も、このengineの起動を再確認しない。

親は同じ共有skills内の [git-sync/SKILL.md](../git-sync/SKILL.md) の「失敗を解消して再開する」「継続できない場合」を読み、共通の復旧・承認境界として適用する。engineはエラーをmarkerと非ゼロ終了で返す。親はそれを復旧の開始点として扱い、通常の失敗でユーザーへ作業を返さない。

このengineは既存upstreamから取り込み、`origin/<local branch>`へpushする。親は起動前に双方の送り先が対象dotfilesの意図したものか確認する。ホーム配備はengineのgeneratorとは別に親が実行する。統合後の原本に対して `bash etc/link.sh --codex-cursor-only`、または必要なruntimeの既存配備関数を使い、終了コードと配備後の実体を確認する。配備で原本差分が生じた場合はそれも保全してengineで再同期する。

- `AUTOSYNC_CONFLICT:<label>:kind=content|gitlink` / `CONTENT_CONFLICT`: 共通祖先と双方の変更を読んで統合し、必要な検証と進行中Git操作の完了後にengineを再実行する。gitlinkはsubmodule内で統合・pushしてから親を更新する。
- hook・generator・配備不一致: 原因を修正し、既存のバックアップ付き配備関数で必要なホームコピーも更新する。再生成と失敗した検証を通してengineへ戻る。
- preflight失敗: path・upstream・進行中操作を実測し、今回の同期に属する不整合を解消して再実行する。別作業の状態を破棄しない。
- fetch/push失敗: 通信・認証・リモート更新の原因を区別し、条件を直して再開する。既にpush済みのsubmoduleや保全commitを巻き戻さない。

engineはGitのstderrを表示しない。fetch/push失敗のmarkerだけで原因を推測せず、`git ls-remote`による到達・認証確認、取得済みcommitの祖先比較、確定したpush先への `git push --dry-run`、利用可能なhookログで診断する。診断の生ログは秘密を除いて報告する。dry-runで受信hookの成功までは保証できないため、そこは実pushの結果と区別する。

engineに復旧のためのskip gateや無条件retryを追加しない。root/branch/進行中操作とmarkerから未完了工程を確認して復旧する。成功後はengineの最終marker、remoteとの一致、作業ツリー、配備の整合を実測して報告する。

/check-updates はスキル・プラグインの更新確認を行う別機能です。このスキルの dotfiles 本体同期に暗黙に含めません。
