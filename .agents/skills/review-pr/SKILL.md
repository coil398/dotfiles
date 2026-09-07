---
name: "review-pr"
description: PR・リモートブランチ単位でコードレビューする。PR番号・PRのURL・リモートブランチ名を渡されたとき、「PR確認して」「PRレビュー」「review this PR」「gh pr の差分を見て」といった要望に使う。ローカルの未コミット差分・ファイル指定のレビューはreviewerを使う。ユーザーが /review-pr と入力したら必ず使う。
argument-hint: "[PR番号、ブランチ名、またはファイルパス]"
---

# Review PR — コードレビュー

PRまたは指定されたremote branchの差分を取得します。取得を別Taskへ切り出す場合はreaderとして結果を返し、同じ親が`reviewer/SKILL.md`を読み、取得済み入力をその手順へ渡します。`review-pr`は別の`reviewer`親を起動しません。観点の選択・配分・独立性・評価・統合・最終判定は`reviewer/SKILL.md`が担当し、評価基準と結果の意味は親が渡す`code-review-guidance`と`result-contract`を使います。

**対象**: `$ARGUMENTS`（PR番号、ブランチ名、またはファイルパス。省略時は現在のstaged・unstaged差分）

---

## ステップ 0: プロジェクトメモリパスと RUN_DIR の確定

対象repoの実体、PR番号またはbranchのremote、base/head、取得時点を確認する。成果物を保存する場合だけ、親またはruntimeが渡した実在の`RUN_DIR`と`REPORT_PATH`を使用する。特定runtimeのhomeやmemory pathを推測しない。

```text
PROJECT_ROOT = 対象リポジトリの実体
RUN_DIR = 親またはランタイムが明示した場合だけ、その実在する保存先
REPORT_PATH = 親が明示した場合だけ、そのRUN_DIR配下の保存先
```

`/review-pr` は handoff 連携を行わないため、`HANDOFF_PATH` / `RESUME_MODE` は不要です。

---

## ステップ 1: 差分の取得

まず `$ARGUMENTS` から対象指定とレビューオプションを分離する。`--reviewers=<roles>` と `--all-reviewers` は値を変更せず`reviewer`へ渡し、残りの対象指定からrepoとrefを確定して差分を取得する:

- **PR番号が指定された場合**: 対象repoのbase/headを確認し、`gh pr diff <番号>` で差分を取得する
- **ブランチ名が指定された場合**: 確定したremote branchとHEADのrefを確認し、明示したbase/headで差分を取得する
- **ファイルパスが指定された場合**: 該当ファイルを読み取る
- **引数なし**: 対象として明示された現在のstaged・unstaged・untracked差分を取得する

PRの変更をレビューする場合、PRのbase/headに対する差分へ現在のローカル変更を混ぜない。作業ツリーに混在があれば対象を分けて親へ示す。repo、base、headを確定できない、または取得不能な場合は変更なしやNOT_APPLICABLEにせず、未確認として返す。

取得した差分は、複数担当が同じ内容を参照する必要があり、かつ親が実在する保存先を選んだ場合だけ保存します。保存しない場合は、親が差分を直接渡します。変更ファイル一覧は実際の差分から取得します。

---

## ステップ 2: reviewerへの引き渡し

同じ親が`reviewer/SKILL.md`を読み、取得した差分とともに次の入力をその手順へそのまま渡す:

- repo、対象版、PRまたはbranchのbase/head、取得時点、変更ファイル一覧。
- PRの説明・要件・受入条件、ユーザーが指定したレビューオプション、対象外にしたローカル変更。
- 実在する`reviewer/SKILL.md`、`code-review-guidance/SKILL.md`、result-contractの絶対pathと、必要な参照元path/URL。
- 変更禁止範囲、追加取得や権限が必要な事項、保存が許可されている場合の実在する保存先。

`review-pr`自身は観点一覧、未知roleの処理、独立性や担当数、評価結果の判定を複製しない。PR固有の差分取得に失敗した場合は変更なしや`NOT_APPLICABLE`にせず、失敗内容と未確認範囲を同じ親へ返す。取得をreaderへ切り出した場合、readerは取得結果だけを返し、別のreviewer親や後続工程を起動しない。親は取得結果と`reviewer`の結果を欠落なく扱い、結果の`COVERAGE`/`VERDICT`や未確認範囲を書き換えない。親が明示した実在`REPORT_PATH`への保存は既存の保存方針に従って親が行い、取得担当はレビュー対象、記憶、外部状態を変更せず、commit・push・外部投稿を行わない。
