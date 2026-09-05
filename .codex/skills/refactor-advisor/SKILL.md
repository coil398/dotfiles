---
name: "refactor-advisor"
description: "refactor-advisor エージェントにローカルの差分・ファイルを対象としたリファクタリング提案を出させる。reviewer の Critical/High 判定とは別に、Medium/Low 相当の「直したら良くなる改善余地」を提案させる。「リファクタ提案して」「改善余地ある？」「refactor」といった要望に使う。/pir2 ワークフローでは、必要な reviewer 確認が完了し、別担当に分離する価値がある場合だけ親が起動する。このスキルは PIR² 外で単体起動するためのルート。ユーザーが /refactor-advisor と入力したら必ずこのスキルを使う。"
argument-hint: "[対象範囲の指定（例: ファイルパス、ブランチ名、コミット範囲。省略時は未コミットの差分）]"
---

# Refactor Advisor — リファクタリング提案

refactor-advisor エージェントにリファクタリング提案を出させます。親（このスキルを起動したメイン Codex）が、分離して提案させる価値と実行時容量を確認したうえで、必要なら `agent_type="refactor-advisor"` を起動します。refactor-advisor は単一の役割（Medium/Low 相当の改善提案）を担当しますが、起動数・モデル・再実行をこのスキルで固定しません。

**対象範囲**: $ARGUMENTS

> ℹ️ このスキルは `refactor-advisor` の **単体起動ルート**です。`/pir2` ワークフロー内でも、必要な reviewer 観点の確認が完了し、提案を別担当に分離する実益がある場合だけ親が起動します。本スキルは PIR² 外でリファクタ提案だけ欲しい場合（既に書き終わったコードに「直したら良くなる改善余地」を出してほしいだけのとき）に使ってください。

---

## ステップ 0: メモリパスと artifact path の判断

読み込み済みの本 `SKILL.md` の実体から親の親を `CODEX_SKILLS_DIR` として確定し、対象リポジトリと分離します。対象リポジトリの実体を確認してください。成果物を保存する場合だけ、親が安全確認した artifact root 配下の実体ディレクトリと、親が指定した未使用の report path を使用します。保存しない場合は `RUN_DIR` を作成せず、未指定の path を推測しません。

```text
PROJECT_ROOT = 対象リポジトリの実体
PROJECT_MEMORY_DIR = 親またはランタイムが明示した場合だけ、その実在する保存先
RUN_DIR = 保存が有益で、親が安全に予約した場合だけ、その実体のある保存先
REPORT_PATH = 親が指定した RUN_DIR 配下の未使用 path（指定時だけ保存）
```

保存する場合の `RUN_DIR` の root、実体確認、symlink 拒否、一意な新規 path の確保は `${CODEX_SKILLS_DIR}/pir2/references/sanitized-cwd.md` と `${CODEX_SKILLS_DIR}/worker-delegation/SKILL.md` の契約に従います。

`/refactor-advisor` は handoff 連携を行わないため、`HANDOFF_PATH` / `RESUME_MODE` は不要です。

---

## ステップ 1: 対象範囲の特定

`$ARGUMENTS` に応じて対象を決定する:

- 指定なし: `git diff --name-only HEAD` で未コミットの差分を取得
- ファイルパス: 指定されたファイルをそのまま対象とする
- ブランチ名: `git diff --name-only <branch>...HEAD` でブランチとの差分を取得
- コミット範囲（例: `HEAD~3..HEAD`）: `git diff --name-only <range>` で差分を取得

対象ファイルが 0 件の場合はユーザーに「対象がないため refactor-advisor は起動しません」と報告して終了する（提案ゼロ件の起動は無駄なので）。

---

## ステップ 2: refactor-advisor 起動

親が必要性と実行時容量を確認した場合だけ、`refactor-advisor` role を起動してください。提案を分離する実益がない場合は起動せず、親自身が差分を確認しても構いません。

起動パラメータ:

- model は `.codex/agents/refactor-advisor.toml` の role 定義に委ね、呼び出し側では上書きしないでください。
- プロンプトに以下をすべて含める:
  - `PROJECT_MEMORY_DIR=[ステップ0で取得したパス]`
  - `RUN_DIR=[親が保存を選んだ場合だけ、ステップ0で安全に予約した path]`
  - `REVIEW_INDEX=[親が指定した識別子。未指定なら渡さない]`
  - `REPORT_PATH=[親が指定した RUN_DIR 配下の未使用 path。保存不要なら渡さない]`
  - 対象ファイル一覧（ステップ1で確定したもの）
  - 差分の取得コマンド（ステップ1で使用したものと同じ git diff コマンド。`--name-only` を外したもの）
  - 「上記の差分コマンドで対象を確認し、変更されたファイルを Read してリファクタ提案を出してください。plan.md / implementation-*.md は caller が実在 path を渡した場合だけ Read し、未指定なら推測しない。REPORT_PATH が指定された場合だけ、その親 directory と未使用性を確認して提案レポートを書き出し、指定がなければ PROPOSALS 数 + 提案全文または要約をチャットで返してください」

> ⚠️ caller が plan/report path を渡した場合だけ実在性を確認して Read します。単体起動で未指定の plan.md / implementation-*.md を推測・必須化せず、差分と対象ファイルから提案を作成してください。

---

## ステップ 3: 結果の提示

refactor-advisor の実際の返却と、保存を指定した場合だけ存在する `REPORT_PATH` を Read し、提案リストをユーザーに提示する。未生成の report path や固定 index を補完しない。

### ユーザーへの提示フォーマット

```
## リファクタリング提案

### PROPOSALS
[N]件（Medium: [M]件 / Low: [L]件）

### 書き出し先
[保存した場合だけ実在する REPORT_PATH]

### 提案一覧（要約）
- [M|L] `ファイル:行` — [タイトル]（根拠: 既存先例 or ガードレール充足の要点 1 行）
...

### 除外した候補
[N]件（refactor-advisor がガードレールで除外したもの。詳細はファイル参照）
```

提案が 0 件の場合は `PROPOSALS: 0件` を明記し、refactor-advisor が出した「除外メモ」「言語イディオム上のコメント」があれば併せて転記する。

> ℹ️ このスキルは提案を自動適用しません。提案を実装に反映したい場合は、ユーザーまたは親が候補と scope を明示し、`/ir` や `/pir2` で実装・影響した観点の review/test を別途選びます。固定 report path、全 reviewer、refactor-advisor の無条件再実行を完了条件にしません。
