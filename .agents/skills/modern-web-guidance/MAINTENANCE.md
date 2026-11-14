# modern-web-guidance の保守

このスキルは npm パッケージ `modern-web-guidance` の `skills/modern-web-guidance/` を固定版で取り込んだもので、`SKILL.md` に次の書き換えを当てている。

1. `npx -y modern-web-guidance@latest` を `DISABLE_TELEMETRY=1 npx -y modern-web-guidance@<固定版>` にする。
2. `pnpx modern-web-guidance@latest` を `DISABLE_TELEMETRY=1 pnpx modern-web-guidance@<固定版>` にする。
3. `## Using npx / pnpx` 節の `Runner & Permissions` 行の直前に `Pinned version` 行を置く。

`--skill-version` の値は `skill-version.txt` と一致させ、`LICENSE` はパッケージのものと同一にする。CLI は利用統計を外部へ送り、`install` / `update` は別プロセスで `npx` を起動する。固定版はこれらを人が確かめた版に限る。

## 新しい版へ上げる手順

1. `bash scripts/check-update.sh` を実行する。`MWG_UP_TO_DATE:<版>` なら終了する。`MWG_UPDATE_AVAILABLE:<旧>-><新>`（終了コード 10）なら次へ進む。
2. 出力の変更ファイル一覧、`SKILL.md` の差分、外部通信・プロセス起動・書き込み・利用統計に関わる行の差分を読む。末尾に示される作業ディレクトリの `new/package/skills/modern-web-guidance/` で `modern-web.mjs` と `watchdog/main.js` を読み、通信先・起動するプロセス・書き込み先・利用統計の停止条件（`DISABLE_TELEMETRY`）が増減していないか確かめる。
3. 問題がなければ `bash scripts/check-update.sh --apply <新版>` を実行する。書き換え後の検査（`@latest` が残らない、固定したコマンドを含む、`Pinned version` 行がちょうど1つ）に失敗した場合、原本は変更されない。
4. 固定したコマンドで `DISABLE_TELEMETRY=1 npx -y modern-web-guidance@<新版> search "<query>" --skill-version <skill-version.txt の値>` を1回試す。
5. `git diff` で `SKILL.md`・`skill-version.txt`・`LICENSE` の差分を確かめ、dotfiles を同期する。

`scripts/check-update.sh` は環境変数 `MWG_SKILL_DIR` で対象のスキルディレクトリを変えられる。CLI 自体は実行せず、npm には `npm view` と `npm pack` でだけ通信する。
