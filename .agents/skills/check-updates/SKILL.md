---
name: "check-updates"
description: "明示されたディレクトリ内の独立した git clone の upstream 更新を確認し、clean な fast-forward だけを適用する。マーケットプレース・プラグイン・スキルの更新確認、更新チェック、スキル更新、プラグイン最新？、update skills、check for updates に対応する。ユーザーが /check-updates と入力したら必ずこのスキルを使う。"
argument-hint: "[更新対象root ...]"
---

# Check Updates — スキル・プラグイン更新チェック

明示された root の中にある、独立した git clone の upstream 更新を確認します。

## 責任と読者

親が更新対象 root、現在の upstream、許可された副作用、完了条件を確定する。親はこの Skill と同じ package の `scripts/check-updates.sh` を実体 path から解決して直接実行し、標準出力の marker と終了コードをそのまま結果として統合する。短い定型操作のために別の親や子を起動しない。

スクリプトを読み取り担当へ渡す必要がある場合は、親が実在確認した Skill/script の物理 path、明示 root、変更禁止範囲、返却形式を渡し、担当自身に Read させる。担当は観測結果だけを親へ返し、repository・report・記憶を保存しない。更新の実行、失敗時の未反映範囲、結果の報告は親が持つ。

## 実行契約

- 更新対象 root は呼び出し元が引数で明示する。ホームディレクトリ、現在の作業ディレクトリ、dotfiles、submodule、別 runtime の配置を暗黙に探索しない。
- 各 root 自体、または root から 3 階層以内にある `.git` を持つディレクトリだけを対象にする。通常ファイル、管理対象ディレクトリ、さらに深い階層は変更しない。
- 探索中のディレクトリ symlink は canonical target が指定 root の配下にある場合だけ対象にする。root 外を指す symlink は追跡せず、`SKIPPED_EXTERNAL_SYMLINK:` として報告する。
- superproject が管理する git submodule は独立 clone ではないため対象外にする。同じ clone が複数 root から見えても一度だけ確認する。
- 現在の branch に設定された upstream tracking branch を使う。固定した `main` / `master` や固定 remote は使わない。
- clean な fast-forward だけを自動適用する。merge commit、rebase、stash、commit、push、`merge --abort` は実行しない。
- dirty、local ahead、diverged、upstream 未設定、fetch 失敗、fast-forward 失敗は状態を保持して理由を出力し、non-zero で終了する。
- dotfiles 本体やその submodule の同期が必要な場合は、このスキルではなく `/dotfiles-autosync` を明示的に依頼する。

## 実行手順

親はロードした本 `SKILL.md` の実体を絶対パスとして確定し、その親ディレクトリを `SKILL_DIR` に設定します。root は実在する更新対象だけを引数に渡します。

```bash
THIS_SKILL_PATH="<ロード済み SKILL.md の絶対パス>"; SKILL_DIR="$(cd -P "$(dirname "$THIS_SKILL_PATH")" && pwd -P)"; bash "$SKILL_DIR/scripts/check-updates.sh" "<更新対象root-1>" "<更新対象root-2>"
```

root が存在しない場合は `INVALID_ROOT` になり、呼び出し元の入力を修正してください。スクリプトの標準出力を解析し、対象数・更新数・各失敗理由を報告します。

主なマーカー:

- `UPDATED:` — upstream への fast-forward が完了した。
- `UP_TO_DATE:` — fetch 後も local と upstream が同一だった。
- `DIRTY:` / `AHEAD:` / `DIVERGED:` — local 状態を保持して更新を見送った。
- `NO_UPSTREAM:` / `FETCH_FAILED:` / `FAST_FORWARD_FAILED:` — 更新できなかった理由。
- `SKIPPED_MANAGED_REPO:` — root 自体が管理対象 repo のため、内部を再帰探索しなかった。
- `SKIPPED_EXTERNAL_SYMLINK:` / `SKIPPED_SYMLINK:` — 指定 root 外を指す symlink、または解決できない symlink を追跡しなかった。

終了コードが non-zero の場合、更新済み repo があっても失敗した repo と理由を併記してください。
