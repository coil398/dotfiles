---
name: "dotfiles-autosync"
description: "dotfiles本体を、ユーザーの明示依頼に限って中央 engine で保全commit、no-rebase merge、adapter再生成、submodule整合、pushまで同期する。自然言語トリガー例: 「dotfilesを同期して」／「dotfilesの変更を保全して」／「adapterを再生成して同期して」／「dotfilesをpushして」。スキル・プラグインの更新確認は別の check-updates の責務であり、このスキルはdotfiles本体だけを扱う。ユーザーが /dotfiles-autosync と入力したら使う。"
argument-hint: "[dotfiles の Git top-level]"
---

# Dotfiles Autosync

dotfiles リポジトリ自身を、ユーザーが明示的に依頼したときだけ同期します。対象 root、既存 upstream、実行結果、停止後の復旧情報を親が確認します。スキルの実装は runtime ごとに複製せず、中央 engine の etc/dotfiles-autosync.sh に集約します。

## 責任と読者

親が dotfiles の root、既存 upstream、今回許可された commit・merge・生成・push の範囲、完了条件を確定する。親はロードした Skill の実体から `etc/dotfiles-autosync.sh` の物理 path を解決し、engine の実測 marker と復旧情報を統合する。engine 以外の子や別の司令塔へ同期工程を再起動させない。

read-only の preflight や結果確認を委任する場合は、親が確認済みの Skill/engine path、対象、変更禁止範囲、返却形式を担当へ渡し、担当自身に必要な本文を Read させる。担当は観測結果だけを親へ返す。engine が行う副作用は親の明示承認と既存の個別 path・バックアップ境界に従い、保存・commit・push の最終責任と未反映範囲の報告は親が持つ。

## 中央 engine の解決と起動

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

SKILL_FILE が実在しない、または DOTFILES_ROOT/etc/dotfiles-autosync.sh が無い場合は状態を変えずに停止します。runtime が source path を渡せない場合は engine を推測して実行せず、親へ未実行理由を返します。

## engine が行う処理

中央 engine は次を順番に実行します。

- Git root、既存の upstream、branch、未完了操作を preflight する
- recursive submodule を深い階層から、dirty path の個別 stage・cached diff 確認・保全 commit・fetch・git pull --no-rebase --no-edit・push する
- 親 dotfiles の tracked/staged/untracked 変更を保全 commit する
- 親を no-rebase merge し、git submodule sync/update と Codex/OpenCode/Cursor/Antigravity の adapter generator を実行する
- 生成物と submodule pointer の差分だけを個別 stage・cached diff 確認・commit し、clean/behind 0 を確認して push する

commit、merge、生成物更新、submodule 更新、push は明示的な副作用です。ローカル WIP や通常の divergent branch は保全して統合します。実コンテンツまたは gitlink の conflict だけは自動判断せず conflict state を残してユーザーの解決を待ちます。hook、認証、network、push、preflight、generator の失敗は破棄・自動再試行せず、marker と復旧情報を出して停止します。

/check-updates はスキル・プラグインの更新確認を行う別機能です。このスキルの dotfiles 本体同期に暗黙に含めません。
