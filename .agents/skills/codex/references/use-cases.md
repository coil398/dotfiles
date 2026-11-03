# Codex 用途別カタログ

この文書はCodexに依頼する仕事の選択と受け渡しに使います。親は用途を選び、該当節と必要な専門資料の実体絶対pathをPROMPTへ含めます。runner経由のCodexは渡された節と専門資料を自分で読み、親のSkill読込状態や同名Skillの自動発見には依存しません。runner経由では子を起動できず、共有`codex` SkillもCodex runtimeで無効化されています。

## 用途一覧

| 用途 | 目的 | 配分 | 担当Codexの参照 |
|---|---|---|---|
| [アーキテクチャ検討](#アーキテクチャ検討) | 実装前の構造・責務・依存を検討する | `architecture` | [pre-implementation.md](../../code-review-guidance/references/pre-implementation.md)と必要な専門観点 |
| [独立レビュー](#独立レビュー) | 差分を要件・実装の両面から独立評価する | `review` | [code-review-guidance/SKILL.md](../../code-review-guidance/SKILL.md)、観点別手順、[result-contract.md](../../code-review-guidance/references/result-contract.md) |
| [一般相談・第二意見](#一般相談・第二意見) | 明確な問いに根拠付きで回答する | `worker` | 必要に応じ[explorer.md](../../research/references/explorer.md)等 |
| [範囲を決めた実装](#範囲を決めた実装) | 割当範囲を実装しfocused checkを行う | 通常`worker`、条件統合が難しければ`expert` | 引継ぎ時は[implementation-delegation.md](../../pir2/references/implementation-delegation.md) |
| [分析・仮説](#分析・仮説) | 事実、推測、代替説明、反証条件を分ける | 通常`worker`、難度に応じ`expert`等 | [thinker.md](../../research/references/thinker.md)、[hypothesizer.md](../../research/references/hypothesizer.md)、必要に応じ[explorer.md](../../research/references/explorer.md) |
| [テスト・動作検証](#テスト・動作検証) | 受入条件を実測し、確認範囲を返す | `worker` | [test-procedure.md](../../tester/references/test-procedure.md)と[result-contract.md](../../code-review-guidance/references/result-contract.md) |

## アーキテクチャ検討

実装全体へ波及する構造・責務境界・依存・移行方法の案を、具体的な失敗経路や反例から検討します。実装や最終受入は行いません。

- 親が渡す: repoと対象版、要件、確認済み事実、親の暫定案、検討対象、重要な制約。
- Codexが返す: 守る条件と適用箇所、`path:line`等の根拠、破った場合の不利益、確認方法、反例、未決定。
- 読む: [pre-implementation.md](../../code-review-guidance/references/pre-implementation.md)と今回の判断に必要な[architecture](../../code-review-guidance/references/architecture.md)等の観点別reference。親用のPIR²進行・配分手順は渡しません。

## 独立レビュー

指定された差分を要件と実装の両面から調べ、具体的で再現可能な欠陥を探します。先行レビューの結論を受け取らず、独立に評価します。

- 親が渡す: repo、base/headまたは差分、対象版、要件・受入条件、対象scope、重点観点、関連資料。実装者の会話や別評価者の結論は渡しません。
- Codexが返す: `COVERAGE` / `VERDICT`、根拠付き指摘、未確認範囲、担当外の重要事項（ある場合）。
- 読む: [code-review-guidance/SKILL.md](../../code-review-guidance/SKILL.md)にある観点別referenceの対応表から選んだ資料と、[result-contract.md](../../code-review-guidance/references/result-contract.md)。レビュー進行と結果統合は親が所有します。

## 一般相談・第二意見

明確な問いに対して対象資料や実装を読み、根拠を付けて回答します。調査・仮説形成が主目的なら、親は`research` Skillで問いと調査範囲を定めます。

- 親が渡す: 問い、対象と版、関係するfile・資料、確認済みの事実、答えに必要な判断。
- Codexが返す: `ANSWER`、`EVIDENCE`、`RISKS`、`NEXT_CHECKS`。不足情報が回答を妨げる場合は`BLOCKED`を含めます。
- 読む: コード・資料の探索には[explorer.md](../../research/references/explorer.md)、技術資料の比較には[tech-validator.md](../../research/references/tech-validator.md)など、問いに必要な担当referenceだけを選びます。親用の`research/SKILL.md`は渡しません。

## 範囲を決めた実装

明示された要件を割当scope内で実装し、受入条件に直結するfocused checkを行います。計画・所有範囲・最終受入は親が持ちます。

- 親が渡す: repoと対象版、目的、所有・許可範囲、変更禁止範囲、依存、受入条件、実行するfocused check。
- Codexが返す: 変更file、実施した確認と結果、未確認・阻害要因。
- 読む: 既定実装担当からの引継ぎなら[implementation-delegation.md](../../pir2/references/implementation-delegation.md)で条件を確認します。一般実装に親用の進行Skillを渡しません。

## 分析・仮説

具体的な問いに関するコード・記録・資料を調べ、確認事実、推測、複数の説明、反証可能性を分けます。調査・仮説形成自体が依頼の中心なら、親は`/research`を使って問いと範囲を定めます。

- 親が渡す: 問い、対象と版、調査範囲、観測事実、必要な根拠と反証条件。
- Codexが返す: 根拠、不確実性、代替仮説、反証条件、次の確認。
- 読む: 分析には[thinker.md](../../research/references/thinker.md)、仮説には[hypothesizer.md](../../research/references/hypothesizer.md)、資料の探索には[explorer.md](../../research/references/explorer.md)を必要な範囲で読みます。親用の`research/SKILL.md`は渡しません。

## テスト・動作検証

指定された受入条件を実測するため、既存テストや必要な動作確認を選んで実行し、確認範囲を記録します。

- 親が渡す: repoと対象版、受入条件、`TEST_SCOPE`、許可された環境と出力先、必要な通常導線。
- Codexが返す: 実行コマンドと結果、受入条件との対応、未確認範囲、副作用。
- 読む: [test-procedure.md](../../tester/references/test-procedure.md)と[result-contract.md](../../code-review-guidance/references/result-contract.md)。親用の`tester/SKILL.md`は渡さず、テスト実行者が判定契約に基づく実測を返します。設計判断や原因分析はテスト起動の軽量化と分けます。

## モデルと推論量

次の表がCodex依頼で使う用途別標準配分の唯一の正本です。標準から外す判断は親が行い、runnerは選び直しません。

| 配分 | model / effort | 適用 |
|---|---|---|
| `worker` | `gpt-6-luna` / 作業別目安 | 一般相談、実装、分析、テスト・動作検証 |
| `architecture` / `review` | `gpt-6-astra` / `medium` | アーキテクチャ検討と独立レビュー |
| `expert` | `gpt-6.1-sol` / `medium` | Astra対象外の難しい独立作業、複数条件の統合 |
| `expert_max` | `gpt-6.1-sol` / `max` | 特に高リスクの根本原因・設計に限る例外 |
| `implementation handoff` | `gpt-6.1-sol` / `high` | 既定実装担当の引継ぎ。条件は[implementation-delegation SSOT](../../pir2/references/implementation-delegation.md#既定の実装担当)に従う |

通常の`worker`のeffortは、機械的な置換・参照付け替え・定型編集で`medium`、新しい設計を伴う実装で`high`、難所や高リスクの作業で`max`を目安にします。アーキテクチャ検討と独立レビューは常に対応するAstra配分を使い、`expert` / `expert_max`で置き換えません。とくに高リスクの根本原因分析などで`expert_max`を例外として選べます。model名とCLIで利用可能なeffortの確認方法は共有Skillの[model と effort](../SKILL.md#model-と-effort)に従います。

## 入力・返却の受け渡し

- 用途節に書かれた入力だけで不足する対象版、scope、制約、受入条件は親がPROMPTで補います。
- 専門資料は必要なものだけ選び、その実体絶対pathを渡します。専門本文の再掲や親用の進行Skillを担当Codexへ渡しません。
- 相談、アーキテクチャ事前検討、レビュー、検証はそれぞれ既存原本の返却規則を使います。アーキテクチャ検討にレビューの合否契約を適用しません。
- runnerの完了状態は[runner reference](runner.md)で確認します。実際の受入は用途ごとの返却だけでなく、親による対象diff・証拠との照合で決まります。
