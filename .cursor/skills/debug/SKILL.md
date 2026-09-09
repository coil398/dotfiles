---
name: "debug"
description: "エラーや不具合を実測し、根本原因を特定して修正する。「動かない」「壊れた」「エラーが出る」「なぜか失敗する」、スタックトレースやログが提示されたときに使う。`--deepplan` で診断プランをdeepplanへ切り替える。ユーザーが /debug と入力したら必ず使う。"
argument-hint: "[症状やエラーメッセージ] [--deepplan]"
---

<!-- Cursor native overlay: seeded from .agents/skills; edit here for Cursor mechanics -->

# Debug — 実測 → 原因特定 → 修正 → 確認

症状: $ARGUMENTS

メイン Cursor agent が症状、根本原因、修正範囲、実装経路、受入を所有します。

## Cursor runtime

- 子エージェントは `Task`（`subagent_type`）で起動します。通常のTaskで `model` は省略するか `inherit` とし、親Autoに従います。Cursor agent定義も `model: inherit` と `role: coding|reasoning` を使い、Codex用モデル名を流用しません。
- named exceptionはdeepplan/deepthinkの deliberator / synthesizer / gate だけです。選択したSkillの指示に従い、Task起動時だけ deepthink の `references/fable-model.md` にある Cursor 識別子を指定します。`[effort=…]` 形式は使いません。
- Taskが利用できない場合や小さく密結合した修正では、メインが直接調査・実装・確認できます。未起動Taskの判定を捏造しません。
- target repository内にSkillがあると仮定しません。読込済みの本SKILL.md実体pathから、その親ディレクトリの親を `CURSOR_SKILLS_DIR` として確定し、参照はそこから解決します。run path が必要な場合は `${CURSOR_SKILLS_DIR}/pir2/references/sanitized-cwd.md` の `sanitized_cwd="$(printf '%s' "$PROJECT_ROOT" | sed 's|[^a-zA-Z0-9]|-|g')"` を使い、親から渡された実在値は再計算しません。

## 1. 症状を実測する

推測を重ねる前に、ログ、エラー出力、再現コマンド、失敗テスト、`git status -sb`、関連する設定とコードを確認します。再現できる場合は変更前の失敗条件と期待結果を記録します。

小さく局所的な症状はメインが直接調査します。独立した複数領域、長い呼び出し経路、外部仕様の裏取りがある場合だけread-onlyの `Task(subagent_type="explorer")` を起動します。explorerには具体的な問い、既知の事実、担当範囲、実装・stage・commit禁止を渡し、モデルはagent定義へ委ねます。reportは後続担当に必要な場合だけ固有pathへ保存します。

外部仕様や更新され得る挙動は一次資料で確認します。再現不能なら、確認済み事実、理論上の経路、不足する観測を分けて示し、防御コード、例外握り潰し、retry、skipを根拠なく追加しません。

## 2. 根本原因と修正条件

メインがログ、再現結果、対象コードを照合し、編集前に次を確定します。

- 失敗している層と症状に至る経路
- 根本原因を示す `file:line` またはコマンド出力
- 成功条件と変更前に失敗する再現確認
- 修正候補のコスト、リスク、増えるartifact
- 選ぶ最小修正、対象/禁止範囲、回帰確認

原因が未確定なら追加観測へ戻ります。入力不足、環境、権限、CLI障害はモデル能力不足として扱いません。repoと依頼から解消できる不足をメインが解消し、安全に決められない仕様・権限だけをユーザーへ確認します。

`--deepplan` / `deepplan` が明示された場合だけ `${CURSOR_SKILLS_DIR}/deepplan/SKILL.md` を実行し、得られたplanを実測結果と再照合します。Fable overrideはdeepplan内の3 roleだけに適用し、メインと他TaskはAuto / `inherit` を維持します。指定がなければメインが必要な粒度の修正計画を直接持ちます。

## 3. リスクと権限

キーワードや変更ファイル数ではなく、具体的な損害可能性から確認の強さを決めます。

- 低リスク: 局所ロジック、文書、非実行設定。対象diffと焦点を絞った再現/回帰確認。
- 中リスク: 公開挙動、複数モジュール、API、生成物、永続化形式。影響境界のreviewまたはtestを追加。
- 高リスク/破壊的: data loss、認証・認可、秘密情報、OS権限、security control、schema migration、互換性破壊、本番/外部操作。実装担当から独立した危険対応reviewと実動作確認、rollback確認。

OS/security/権限、本番・外部状態、不可逆操作を変更する前に、対象、影響、復旧方法を提示してユーザーの明示承認を得ます。レビューとテストの範囲は、実害に対応する shared skill の手順へ渡します。

破壊的影響または動作変更を含む場合は、実装前に `${CURSOR_SKILLS_DIR}/pir2/references/destructive-change-check.md` をReadし、危険に対応する確認を記録します。

## 4. 実装

小さく全体文脈と密結合した修正はメインが直接実装します。所有ファイルと終了条件を分離できる通常修正は `Task(subagent_type="implementer")` へ渡します。

委譲には症状、確認済み原因、排他的所有範囲、維持する制約、終了条件、再現・回帰確認、変更禁止範囲を含めます。実装Taskは別Taskを起動せず、scopeを自己変更しません。

完了後、メインが `git status -sb`、対象diff、実在する変更ファイルを確認し、元の再現コマンドまたは同等確認で症状の解消を実測します。根本原因に対応する焦点を絞った回帰確認も行います。実装者の自己申告や終了コードだけで受け入れません。

## 5. レビューとテスト

最低限、メインが診断、要求、対象diff、確認結果を照合します。reviewer または tester が必要な場合は、同じメインが `${CURSOR_SKILLS_DIR}/reviewer/SKILL.md` または `${CURSOR_SKILLS_DIR}/tester/SKILL.md` を Read してその手順を実行します。別の進行担当を起動せず、症状、根本原因の証拠、対象版、要件、ユーザー指定、実在する差分、必要な確認範囲を渡して選定・配分・判定を委ねます。

shared reviewer が評価者を起動する場合、評価者には reviewer の進行手順を渡さず、`${CURSOR_SKILLS_DIR}/code-review-guidance/SKILL.md` の実体絶対 path と対象に対応する reference だけを渡します。shared tester を起動する場合は `${CURSOR_SKILLS_DIR}/tester/references/test-procedure.md` と結果契約の実体 path を実行担当へ渡し、`TEST_SCOPE`、期待結果、変更禁止範囲を明示します。未生成の plan・report・verdict を前提にしません。

返却が要件未達または未確認を示した場合、メインが指摘を diff・仕様・再現結果と照合して根本原因を特定し、実際の原因に関係する最小修正へ戻します。修正後は影響する確認だけを各 shared skill の手順で再確認し、未確認を成功に変換しません。

同じ呼び出しが2回続けて失敗したら、原因を特定せず3回目を試しません。原因が特定され、変更で成功する合理的根拠がある場合だけ再試行し、それ以外はblockerと選択肢を報告します。続行判断が必要なら `${CURSOR_SKILLS_DIR}/pir2/references/continuation-gate.md` をReadします。回数到達だけで成功扱いにしません。

## 6. 完了報告

次を簡潔に報告します。

- 症状と再現条件、根本原因の証拠
- 実diffで確認した変更ファイル
- 実装経路: メイン直接または実際に使ったTask
- 実行した再現・回帰確認と結果
- 実際に起動したreviewer/testerとVERDICT。未実行なら未実行
- 未確認事項、blocker、実在するartifact/handoff
