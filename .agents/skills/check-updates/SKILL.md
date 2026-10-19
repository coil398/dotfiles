---
name: "check-updates"
description: "明示されたディレクトリ内の独立した git clone を確認し、clean な fast-forward だけを適用する。マーケットプレース・プラグイン・Skillのupstream取込み確認に使う。Skill本文の編集・作成は skill-creator または instruction-refactor を使う。"
argument-hint: "[更新対象root ...]"
---

# Check Updates：スキル・プラグイン更新チェック

明示された root の中にある、独立した git clone の upstream 更新を確認します。

## 責任と読者

親が更新対象 root、現在の upstream、許可された副作用、完了条件を確定する。親はこの Skill と同じ package の `scripts/check-updates.sh` を実体 path から解決して直接実行し、標準出力の marker と終了コードをそのまま結果として統合する。この短い定型操作自体は子を起動しない。`git-sync` が同期後処理をbackground担当へ委任する場合は、その担当がこのscriptを実行し、さらに子を起動しない。

スクリプトを読み取り担当へ渡す必要がある場合は、親が実在確認した Skill/script の物理 path、明示 root、変更禁止範囲、返却形式を渡し、担当自身に Read させる。担当は観測結果だけを親へ返し、repository・report・記憶を保存しない。更新の実行、失敗時の未反映範囲、結果の報告は親が持つ。

## 実行契約

- 更新対象 root は呼び出し元が引数で明示する。ホームディレクトリ、現在の作業ディレクトリ、dotfiles、submodule、別 runtime の配置を暗黙に探索しない。
- 各 root 自体、または root から 3 階層以内にある `.git` を持つディレクトリだけを対象にする。通常ファイル、管理対象ディレクトリ、さらに深い階層は変更しない。
- 探索中のディレクトリ symlink は canonical target が指定 root の配下にある場合だけ対象にする。root 外を指す symlink は追跡せず、`SKIPPED_EXTERNAL_SYMLINK:` として報告する。
- superproject が管理する git submodule は独立 clone ではないため対象外にする。同じ clone が複数 root から見えても一度だけ確認する。
- 現在の branch に設定された upstream tracking branch を使う。固定した `main` / `master` や固定 remote は使わない。
- clean な fast-forward だけを自動適用する。merge commit、rebase、stash、commit、push、`merge --abort` は実行しない。
- dirty、local ahead、diverged、upstream 未設定、fetch 失敗、fast-forward 失敗は状態を保持して理由を出力し、non-zero で終了する。
- dotfiles 本体やその submodule の同期は、このスキルではなく `/dotfiles-autosync` が行う。

## 実行手順

親はロードした本 `SKILL.md` の実体を絶対パスとして確定し、その親ディレクトリを `SKILL_DIR` に設定します。root は実在する更新対象だけを引数に渡します。

```bash
THIS_SKILL_PATH="<ロード済み SKILL.md の絶対パス>"; SKILL_DIR="$(builtin cd -P "$(dirname "$THIS_SKILL_PATH")" 2>/dev/null && pwd -P)" && bash "$SKILL_DIR/scripts/check-updates.sh" "<更新対象root-1>" "<更新対象root-2>"
```

root が存在しない場合は `INVALID_ROOT` になり、呼び出し元の入力を修正してください。スクリプトの標準出力を解析し、対象数・更新数・各失敗理由を報告します。

scriptが出力する主なmarker・error:

- `ERROR:`：更新対象rootの引数がない場合のusage error（標準エラー出力）。
- `CHECKED:` / `UPDATED_COUNT:` / `ERRORS:`：確認したrepo数、更新数、失敗数。`ERRORS: 0` は失敗なし。
- `UPDATED:` / `UP_TO_DATE:`：fast-forward完了 / fetch後もlocalとupstreamが同一。
- `DIRTY:` / `AHEAD:` / `DIVERGED:`：local状態を保持して更新を見送った。
- `NO_UPSTREAM:` / `FETCH_FAILED:` / `FAST_FORWARD_FAILED:`：更新できなかった理由。
- `STATUS_FAILED:` / `COMPARE_FAILED:`：Git状態取得 / upstreamとの比較の失敗。
- `INVALID_ROOT:`：rootの不存在または解決失敗。対象repoがない場合は `CHECKED: 0` / `UPDATED_COUNT: 0` / `ERRORS: 0` です。
- `SKIPPED_MANAGED_REPO:`：root自体が管理対象repoのため内部を再帰探索しなかった。
- `SKIPPED_EXTERNAL_SYMLINK:` / `SKIPPED_SYMLINK:`：root外symlink / 解決できないsymlinkを追跡しなかった。

終了コードが non-zero の場合、更新済み repo があっても失敗した repo と理由を併記してください。
