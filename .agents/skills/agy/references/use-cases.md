# agy 用途別カタログ

この文書はagyに依頼する仕事の選択と受け渡しに使います。親は用途を選び、該当節と必要な専門資料の実体絶対pathをPROMPTへ含めます。runner経由のagyは渡された節と専門資料を自分で読み、親のSkill読込状態には依存しません。

## 用途一覧

| 用途 | 目的 | 配分 | 担当agyの参照 |
|---|---|---|---|
| [アーキテクチャ検討](#アーキテクチャ検討) | 実装前の構造・責務・依存を検討する | `consult` | [pre-implementation.md](../../code-review-guidance/references/pre-implementation.md)と必要な専門観点 |
| [独立レビュー](#独立レビュー) | 差分を要件・実装の両面から独立評価する | `consult` | [code-review-guidance/SKILL.md](../../code-review-guidance/SKILL.md)、観点別手順、[result-contract.md](../../code-review-guidance/references/result-contract.md) |
| [一般相談・第二意見](#一般相談・第二意見) | 明確な問いに根拠付きで回答する | `consult`、軽い問いは`consult_light` | 必要に応じ[explorer.md](../../research/references/explorer.md)等 |
| [分析・仮説](#分析・仮説) | 事実、推測、代替説明、反証条件を分ける | `consult` | [thinker.md](../../research/references/thinker.md)、[hypothesizer.md](../../research/references/hypothesizer.md)、必要に応じ[explorer.md](../../research/references/explorer.md) |
| [範囲を決めた実装](#範囲を決めた実装) | 割当範囲を実装しfocused checkを行う | `implement`、難所は`implement_hard` | 必要な専門手順 |
| [debug](#debug) | 症状を実測し、原因を特定して、許可された場合に最小修正と再確認を行う | 調査のみは`consult`、修正を含めば`implement` | 必要な探索reference、[test-procedure.md](../../tester/references/test-procedure.md)、[result-contract.md](../../code-review-guidance/references/result-contract.md) |
| [テスト・動作検証](#テスト・動作検証) | 受入条件を実測し、確認範囲を返す | `implement` | [test-procedure.md](../../tester/references/test-procedure.md)と[result-contract.md](../../code-review-guidance/references/result-contract.md) |

画面の見た目を確認するUI確認は、runner経由のagyで画面証拠を扱う経路を用意していないため、このカタログでは扱いません。

## アーキテクチャ検討

実装全体へ波及する構造・責務境界・依存・移行方法の案を、具体的な失敗経路や反例から検討します。実装や最終受入は行いません。

- 親が渡す: repoと対象版、要件、確認済み事実、親の暫定案、検討対象、重要な制約。
- agyが返す: 守る条件と適用箇所、`path:line`等の根拠、破った場合の不利益、確認方法、反例、未決定。
- 読む: [pre-implementation.md](../../code-review-guidance/references/pre-implementation.md)と今回の判断に必要な[architecture](../../code-review-guidance/references/architecture.md)等の観点別reference。親用のPIR²進行・配分手順は渡しません。

## 独立レビュー

指定された差分を要件と実装の両面から調べ、具体的で再現可能な欠陥を探します。先行レビューの結論を受け取らず、独立に評価します。

- 親が渡す: repo、base/headまたは差分、対象版、要件・受入条件、対象scope、重点観点、関連資料。実装者の会話や別評価者の結論は渡しません。
- agyが返す: `COVERAGE` / `VERDICT`、根拠付き指摘、未確認範囲、担当外の重要事項（ある場合）。
- 読む: [code-review-guidance/SKILL.md](../../code-review-guidance/SKILL.md)にある観点別referenceの対応表から選んだ資料と、[result-contract.md](../../code-review-guidance/references/result-contract.md)。レビュー進行と結果統合は親が所有します。

## 一般相談・第二意見

明確な問いに対して対象資料や実装を読み、根拠を付けて回答します。調査・仮説形成が主目的なら、親は`research` Skillで問いと調査範囲を定めます。

- 親が渡す: 問い、対象と版、関係するfile・資料、確認済みの事実、答えに必要な判断。
- agyが返す: `ANSWER`、`EVIDENCE`、`RISKS`、`NEXT_CHECKS`。不足情報が回答を妨げる場合は`BLOCKED`を含めます。
- 読む: コード・資料の探索には[explorer.md](../../research/references/explorer.md)、技術資料の比較には[tech-validator.md](../../research/references/tech-validator.md)など、問いに必要な担当referenceだけを選びます。親用の`research/SKILL.md`は渡しません。

## 分析・仮説

具体的な問いに関するコード・記録・資料を調べ、確認事実、推測、複数の説明、反証可能性を分けます。調査・仮説形成自体が依頼の中心なら、親は`/research`を使って問いと範囲を定めます。

- 親が渡す: 問い、対象と版、調査範囲、観測事実、必要な根拠と反証条件。
- agyが返す: 根拠、不確実性、代替仮説、反証条件、次の確認。
- 読む: 分析には[thinker.md](../../research/references/thinker.md)、仮説には[hypothesizer.md](../../research/references/hypothesizer.md)、資料の探索には[explorer.md](../../research/references/explorer.md)を必要な範囲で読みます。親用の`research/SKILL.md`は渡しません。

## 範囲を決めた実装

明示された要件を割当scope内で実装し、受入条件に直結するfocused checkを行います。計画・所有範囲・最終受入は親が持ちます。

- 親が渡す: repoと対象版、目的、所有・許可範囲、変更禁止範囲、依存、受入条件、実行するfocused check。
- agyが返す: 変更file、実施した確認と結果、未確認・阻害要因。
- 読む: 作業に必要な専門手順だけを渡します。一般実装に親用の進行Skillを渡しません。

## debug

症状・再現条件・期待結果から始め、実測、失敗層、根本原因を確認します。親が調査のみか修正まで含むかを決め、調査のみは`plan`、修正を含む場合は`auto`で起動します。原因が未確定なら、修正済みとせず、観測事実・仮説・不足情報や阻害要因を区別して返します。

- 親が渡す: 症状、再現手順と期待結果、対象repo/version、許可scope、調査のみか修正を含むか、禁止範囲、受入条件と可能なら確認コマンド。
- agyが行う: ログ・再現・コードから実際の失敗層と原因を調べ、許可された場合だけ原因に対応する最小修正を行います。修正を含む場合は元の再現確認と根本原因に対応する回帰確認を行います。
- agyが返す: 実測した事実と根拠、失敗層、確定した原因または未確定の仮説、変更した場合は実差分と確認結果、未確認や阻害要因。推測だけで原因確定・修正済みと扱いません。
- 読む: 必要なコード・資料探索には[explorer.md](../../research/references/explorer.md)、確認には[test-procedure.md](../../tester/references/test-procedure.md)と[result-contract.md](../../code-review-guidance/references/result-contract.md)を使います。親用の[debug/SKILL.md](../../debug/SKILL.md)全体を担当へ渡しません。

## テスト・動作検証

指定された受入条件を実測するため、既存テストや必要な動作確認を選んで実行し、確認範囲を記録します。commandを実行するため`auto`で起動し、変更を許可しない場合はPROMPTで編集禁止を明示します。

- 親が渡す: repoと対象版、受入条件、`TEST_SCOPE`、許可された環境と出力先、必要な通常導線。
- agyが返す: 実行コマンドと結果、受入条件との対応、未確認範囲、副作用。
- 読む: [test-procedure.md](../../tester/references/test-procedure.md)と[result-contract.md](../../code-review-guidance/references/result-contract.md)。親用の`tester/SKILL.md`は渡しません。

## モデルと推論量

次の表がagy依頼で使う用途別標準配分の唯一の正本です。effortはmodel idに含まれます。標準から外す判断は親が行い、runnerは選び直しません。

| 配分 | model id | mode | 適用 |
|---|---|---|---|
| `consult` | `gemini-4-carbon-high` | `plan` | アーキテクチャ検討、独立レビュー、相談・第二意見、分析・仮説、調査のみのdebug |
| `consult_light` | `gemini-4-carbon-medium` | `plan` | 根拠の範囲が狭い軽い相談 |
| `implement` | `gemini-4-hydrogen-high` | `auto` | 範囲を決めた実装、修正を含むdebug、テスト・動作検証 |
| `implement_hard` | `gemini-4-hydrogen-xhigh` | `auto` | 難所や高リスクの実装 |

使えるmodel idは`agy models`で確認します。

## 入力・返却の受け渡し

- 用途節に書かれた入力だけで不足する対象版、scope、制約、受入条件は親がPROMPTで補います。
- 専門資料は必要なものだけ選び、その実体絶対pathを渡します。専門本文の再掲や親用の進行Skillをagyへ渡しません。
- 相談、アーキテクチャ事前検討、レビュー、検証はそれぞれ既存原本の返却規則を使います。アーキテクチャ検討にレビューの合否契約を適用しません。
- runnerの完了状態は[runner reference](runner.md)で確認します。実際の受入は用途ごとの返却だけでなく、親による対象diff・証拠との照合で決まります。
