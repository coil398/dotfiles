---
name: worker-delegation
description: Astraが具体化した作業を、native collaborationまたは必要なCLI runnerへ委譲するCodex-native契約。担当とmodel・effortは実行時に選び、runnerの例外条件と証跡を保持する。
argument-hint: "[具体化済みの委譲タスク]"
---

# Worker Delegation

このSkillは、親Astraが判断・設計・分割・統合・最終受入を所有し、必要な具体作業を別担当へ渡すための契約です。小さな変更や全体文脈と分離できない密結合の変更は、Astraが直接実装します。workerの自己申告や実行終了だけを受入判定には使いません。native collaboration の標準担当・model・effortは、親がそのruntimeの公開起動値と既存設定から選び、このSkillでは固定しません。

## 経路と担当

通常の実行経路は Codex の native collaboration です。Astraは作業単位ごとに担当、所有ファイル、制約、受入条件を明示して起動し、独立した書き込み単位だけを並列化します。同じファイルを複数担当へ同時に割り当てません。

親は通常の作業をruntimeが提供する標準担当へ渡し、難所は同じruntimeが公開する別のmodel・effortを起動時に明示して選べます。難所の選択は初手から可能で、入力不足、権限、環境、CLI障害をmodel不足とは扱いません。標準経路外の担当を使う場合は、同種 workload の実測根拠と actor・effort を親が明示します。runnerやworkerは自動fallback、自己判断の再試行、actor/effort変更を行いません。

## 委譲内容

native collaboration では、担当ごとに次を短く渡します。

- 目的と既に確認した事実
- 所有するファイルまたは領域（他担当との重複なし）
- 維持する制約、変更してよいインターフェース
- 終了条件と実行すべき焦点を絞った確認
- 変更してはいけない範囲
- 返却する変更ファイル、挙動の変更、実行結果、未確認事項、blocker

委譲担当は指定された範囲だけを編集し、判断の変更やスコープ拡張を親へ戻します。別agent、reviewer、testerを勝手に起動せず、commit、push、既存変更を破棄する操作もしません。権限や安全境界をモデル変更の理由で弱めません。

## 明示CLI runner

runner は通常経路ではなく、親Astraが明示的な CLI 実行、runner-owned artifact/provenance、または物理境界付きの実行証拠を必要とする job にだけ使います。native collaboration で完結する小変更に runner の task/requirements/artifact 手順を強制しません。

参照先は対象リポジトリから導出せず、読み込み済みの本 `SKILL.md` の実体パスから親の親を `CODEX_SKILLS_DIR` として確定した絶対パスを使います。対象リポジトリ内に `.codex/skills` があることを仮定しません。

runner の正規入口は次です。

```sh
bash "${CODEX_SKILLS_DIR}/worker-delegation/scripts/run-worker.sh" --actor luna --effort max --cwd <repo-root> --task-file <task.md> --requirements-file <requirements.md> --output-file <worker-result.md>
```

`worker` は `--actor luna --effort max`、`expert` は `--actor sol --effort high`、`expert_max` は `--actor sol --effort max` に対応します。Terra例外も actor/effort を明示します。QA呼出し側が明示的に選ぶAstra例外は `--actor astra --effort low`（`gpt-6-astra`）です。runnerは選択値をそのままCodexへ渡し、別modelへの自動切替をしません。未知の actor/effort や不正な組合せは起動前に拒否します。

`.codex/` 配下を所有する runner job では、taskの排他的所有範囲に一致する最も狭い `--mutable-path <repo-relative-path>` を必要な数だけ指定できます。これは source-ownership metadata であり、権限昇格ではありません。UID、mode、symlink、`.git`、同一Git root、cwd、出力先の検査は指定範囲にも適用されます。指定しない場合は `.codex/` 全体を identity-pinned として扱います。

runner source 自体を変更する job は他のrunner jobと並列にせず、起動前に private `0700` の実行コピーを固定します。既存の runner の安全境界（canonical Git root/cwd、`.codex` descendant inventory、所有者・書込み権限・symlink検査、出力親の境界、no-replace の raw report/provenance、`--disable hooks`、失敗時のfail-closed）を緩めません。実行時間、同一UIDのTOCTOU限界、限定symlink recovery、provenanceの扱いを含む詳細は [runner-contract.md](references/runner-contract.md)、実装と回帰テストは `scripts/run-worker.sh` と同ディレクトリのテストを正とします。

runner report は未信頼入力です。runnerを使った場合は次の8項目を一意に返します。

```text
ACTOR: luna|terra|sol|astra
ACTUAL_MODEL: 実測したモデル名
ACTUAL_EFFORT: low|high|max
STATUS: completed|blocked|failed
CHANGED_FILES: 実測したリポジトリ相対パス
OBSERVED_RESULTS: 実行した確認と結果
BLOCKERS: none または具体的な blocker
ESCALATION_REASON: none または親Astraが指定した実測理由
```

編集不要の場合は `NO_OP_JUSTIFIED: <理由>` を返します。これは事実の引き渡しであり、acceptance、reviewer、tester のPASSではありません。

## 完了確認と観測

Astraは実際の `git status`、対象差分、変更ファイル、要求された確認コマンドの出力から各受入条件を判定します。reviewer/testerを使う場合はworkerとは別系統で実行し、その判定をworker reportへ混ぜません。

決定論的な pre/post/CLAIMED gate と `record-observation.sh` の台帳は、runnerを選択し、artifact identity・実行モデル・effort・変更集合の実測が必要な job に限って使います。native collaboration、Astraの直接実装、単純な小変更に、8 fixture、canonical report、meta gate、台帳行を一律要求しません。runner jobで適用する場合だけ、[deterministic-completion-check.md](references/deterministic-completion-check.md) と `scripts/record-observation.sh` の共通契約を読み、結果を実測して記録します。reviewer/testerを起動していないのにverdict行を捏造しません。

受入・昇格・Terra例外の理由は親Astraが所有します。全requirementsを実測して満たした場合だけAstraが完了とし、未実行の確認、未対応事項、外部状態のblockerを明記します。

運用比較にはAstraの直接実装も含め、同じ受入条件で親の準備・結果確認、子の作業、差戻し・再試行を合計します。既存のtask reportとruntime logに、task種別、実モデル・effort、担当変更理由、所要時間、検証、手戻り、取得できた利用量を残します。利用量が取得できなければ未計測とし、ゼロや推測の費用削減を記録しません。直接APIを扱う場合だけ通常入力・キャッシュ読出し・書込み・出力を分けます。native/直接作業へrunner台帳を強制せず、新しい計測基盤を受入の前提にしません。
