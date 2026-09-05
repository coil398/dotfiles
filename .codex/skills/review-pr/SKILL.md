---
name: "review-pr"
description: "PR・リモートブランチ単位でコードレビューする。PR番号・PRのURL・リモートブランチ名を渡されたとき、「PR確認して」「PRレビュー」「review this PR」「gh pr の差分を見て」といった要望に使う。ローカルの未コミット差分・ファイル指定のレビューは /reviewer を使うこと。ユーザーが /review-pr と入力したら必ずこのスキルを使う。"
argument-hint: "[PR番号, ブランチ名, またはファイルパス]"
---

# Review PR — コードレビュー

変更差分をレビューします。このスキル本体（= メイン Codex）がオーケストレーターとなり、`list_agents` で実行中の体数と利用可能な容量を確認してから `spawn_agent` で `agent_type="reviewer"` を、correctness / consistency / quality / security / architecture のうち実害に対応する観点だけ選んで並列起動します。subagentから別の制御 role を起動せず、起動責任はスキル本体に集約します。

**対象**: $ARGUMENTS（PR番号、ブランチ名、またはファイルパス。省略時はステージング済み・未ステージの差分）

---

## ステップ 0: プロジェクトメモリパスと artifact path の判断

読み込み済みの本 `SKILL.md` の実体から親の親を `CODEX_SKILLS_DIR` として確定し、対象リポジトリ内の skill 配置を仮定しません。

対象リポジトリの実体を確認し、`PROJECT_MEMORY_DIR` と成果物保存の要否を決めてください。`RUN_DIR` は、複数 reviewer が同じ差分を参照する必要があるなど、後続の統合・再現に実益がある場合だけ、親が安全確認した artifact root 配下の実体ディレクトリとして予約します。保存が不要なら `RUN_DIR` を作成せず、reviewer にも渡しません。既存の path、symlink、固定 index を再利用せず、親が指定した未使用 path だけを使います。

```text
PROJECT_ROOT = 対象リポジトリの実体
PROJECT_MEMORY_DIR = ランタイムが明示した場合だけ、その実在する保存先
RUN_DIR = 共有 artifact が必要で、親が安全に予約した場合だけ、その実体のある保存先
```

`RUN_DIR` を予約する場合の root、実体確認、symlink 拒否、一意な新規 path の確保は `${CODEX_SKILLS_DIR}/pir2/references/sanitized-cwd.md` と `${CODEX_SKILLS_DIR}/worker-delegation/SKILL.md` の契約に従います。`RUN_DIR` は reviewer ごとの report path を暗黙に生成するためのものではなく、親が渡した未使用 path を使うための親ディレクトリです。

`/review-pr` は handoff 連携を行わないため、`HANDOFF_PATH` / `RESUME_MODE` は不要です。

---

## ステップ 1: 差分の取得

まず `$ARGUMENTS` から `--reviewers=<roles>` と `--all-reviewers` フラグを**抽出して除去**し、残りを対象指定として扱う。次に残り部分に応じて差分を取得する:

- **PR番号が指定された場合**: `gh pr diff <番号>` で差分を取得する
- **ブランチ名が指定された場合**: `git diff <ブランチ名>...HEAD` で差分を取得する
- **ファイルパスが指定された場合**: 該当ファイルを Read する
- **引数なし**: `git diff HEAD` でステージング済み＋未ステージの差分を取得する

親が対象差分を確認し、広域探索が必要な場合は独立性と分離価値に応じて read-only explorer へ具体的な問いを渡します。追加探索だけを理由に実装やリモート変更を行いません。

取得した差分は、複数 reviewer に同じ内容を渡すことが後続の統合・再現に有益で、親が `RUN_DIR` と未使用の `DIFF_PATH` を指定した場合だけ、その path に Write で保存してください。保存しない場合は差分を直接渡すか、親が指定した既存の実在 path を Read します。未指定の path や `{RUN_DIR}/diff.patch` を推測・固定せず、変更ファイル一覧は実際の差分から取得します。

---

## ステップ 2: レビュー（reviewer role のハイブリッド並列）

### 2-1: REVIEWER_SET 決定（非 planner 系：自動選定がデフォルト）

`REVIEWER_SET` を決定する:

1. **ユーザーフラグ**: ステップ 1 で抽出した `--reviewers=<roles>` があればカンマ区切りを観点集合として採用（未知 role は無視）。`--all-reviewers` があれば全 5 観点。両方指定時は `--reviewers=` を優先
2. **フラグ未指定時の自動選定**（以下を上から評価）:
   1. `correctness` は常に含める
   2. 変更ファイル一覧にコード拡張子が含まれる（ドキュメント・設定のみでない） → `consistency` を追加
   3. 取得した差分または PR タイトル/本文に**セキュリティ関連語句**（認証 / 認可 / auth / token / secret / password / credential / SQL / XSS / CSRF / シリアライズ / 外部API / ユーザー入力 / validate / sanitize / 権限 / 暗号 / crypto / 脆弱性）が含まれる → `security` を追加
   4. 差分に**新規ファイル追加**（`diff --git a/dev/null` or `new file mode`）、または変更ファイルが 2 つ以上の異なるトップレベルディレクトリにまたがる → `architecture` を追加
   5. 差分に**新規関数・メソッド・クラスの追加**、または**差分行数 > 20 行** → `quality` を追加
   6. **判断に迷う**場合は、迷いの原因となる具体的なリスク観点だけを追加し、理由を記録する。diff を取得できない・対象を確定できない場合は全観点へ機械的に拡張せず、対象確定を blocker として報告する
3. 決定した `REVIEWER_SET` をユーザー提示に含める

### 2-2A: 起動前確認（選定観点と実効容量を確定する）

reviewer を起動する前に、選定した観点、各観点を追加した根拠、実行時の空き枠を確認する。起動数を固定値に合わせるための gate や、観点数の不一致を理由にしたやり直しは行わない。

> **Review dispatch check**
> - REVIEWER_SET = [<実害に対応する観点だけを列挙>]
> - 起動数 = <実際に起動する数>
> - 独立観点は、実効容量が許す同一 wave に並べる。容量不足なら wave を分け、観点を削減しない

この確認は選定根拠と実効容量を記録するためのものであり、固定人数を満たすためのフェンスではない。

### 2-2B: 並列発火（同一メッセージ内）

選定した REVIEWER_SET の独立観点について、実効容量が許す範囲で同一の collaboration 呼び出しブロックに `spawn_agent` を並べて起動する。容量が足りない場合は wave を分けるか、利用可能な既存 thread を `followup_task` で再利用し、リスク観点を黙って削減しない。各体は `REVIEWER_ROLE` を変えて担当観点を分割する。

必要な詳細は `${CODEX_SKILLS_DIR}/pir2/references/fan-out-gate.md` を参照。

確認漏れとして扱うのは、選定根拠・実効容量・未実施観点の理由が記録されていない場合だけとする。起動を複数 wave に分けたこと自体や、固定数に達しないことは違反ではない。

各体の起動パラメータ:

- `agent_type="reviewer"`（model は `.codex/agents/reviewer.toml` の role 定義に委ね、呼び出し側では上書きしない）
- プロンプト（共通。`REVIEWER_ROLE` のみ変える）:
  - `PROJECT_MEMORY_DIR=[ステップ0で取得したパス]`
  - `RUN_DIR` と `REPORT_PATH`（保存を選んだ場合だけ、安全な親dirと担当ごとの未使用pathを渡す）
  - `REVIEW_INDEX=[親が指定した識別子]`（再レビュー時を含め、親が指定しない場合は渡さず、番号を推測しない）
  - `REVIEWER_ROLE=[correctness|consistency|quality|security|architecture]`（体ごとに変える。REVIEWER_SET に含まれる観点のみ）
  - 変更ファイル一覧
  - 差分ファイルのパス: `[親が DIFF_PATH を指定して保存した場合だけ、その実在 path]`
  - 「これはコードレビューです。実装は行わず、レビューのみ行ってください。plan.md / implementation-*.md は caller が実在 path を渡した場合だけ Read し、未指定なら推測しない。差分は inline または親が指定した実在 path から確認し、変更されたファイルの現状も必要に応じて Read してください。後続の統合・再現にファイルが必要で親が未使用の report path を指定した場合だけ、指定 path の親 directory と未使用性を確認してレポートを書き出し、そうでなければ VERDICT + 要約 + 必要な根拠をチャットで返してください」

---

## ステップ 3: 結果の統合・提示

起動した reviewer の実際の VERDICT と、保存した場合だけ存在するレポートをユーザーに提示する。未起動の担当や未生成の成果物を補完しない:

### VERDICT 集約

- **全体 VERDICT = PASS**: 起動した全担当が `VERDICT: PASS` で、必要な確認が未実施でない
- **全体 VERDICT = FAIL**: 1体でも `VERDICT: FAIL`

### ユーザーへの提示フォーマット

```
## PR レビュー完了

### 対象
[PR番号 / ブランチ名 / ファイルパス]

### 全体 VERDICT
[PASS|FAIL]

### REVIEWER_SET
[起動した観点のカンマ区切り、例: correctness,consistency,security]

### 観点別 VERDICT
（REVIEWER_SET に含まれる観点のみ。例）
- correctness: [PASS|FAIL] — [保存した場合だけ実在する path]
- consistency: [PASS|FAIL] — [保存した場合だけ実在する path]
- security: [PASS|FAIL] — [保存した場合だけ実在する path]

### 主な指摘事項（Critical / High のみ）
- [深刻度] `ファイル:行` — [問題の要約]（出典: [ROLE]）
```

各 reviewer のチャット返却と、保存した場合だけ実在する report を Read して、Critical / High の問題一覧を統合してユーザーに提示する。Medium / Low は後続判断に役立つ場合だけ要約し、存在しない report path や固定 index を補完しない。
