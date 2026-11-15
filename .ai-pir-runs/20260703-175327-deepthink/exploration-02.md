## 探索レポート: 既存多エージェント・オーケストレーションフローとの比較による epic の逸脱/欠落点抽出

### 関連ファイル一覧

| ファイルパス | 役割・内容 | 変更の必要性 |
|------------|-----------|------------|
| `.claude/skills/epic/SKILL.md` | 比較対象本体。Phase 1（分割）→ 1.5（ユーザー確認）→ 2（ネスト pir2 実行）→ 3（統合確認＋メタ retro）の4フェーズ。試験実装 | 参照のみ（本調査は改善点抽出が目的で編集は行っていない） |
| `.claude/agents/epic-planner.md` | 比較対象本体。分割戦略のみを担当するエージェント定義（実装詳細・オーケストレーションは持たない） | 参照のみ |
| `.claude/skills/pir2/SKILL.md` | 比較基準1（本体）。13ステップの制御フロー、ループ・ゲート・状態管理の集大成 | 参照のみ |
| `.claude/skills/pir2/references/fan-out-gate.md` | reviewer 並列起動の Fan-Out Gate 仕様（観点マッピング・違反検出・リカバリ） | 参照のみ |
| `.claude/skills/pir2/references/plan-choice-gate.md` | プラン複数案時のユーザー確認ゲート（字義解釈確認・v2→v3切替確認を含む） | 参照のみ |
| `.claude/skills/pir2/references/exploration-loop.md` | 能動的再探索ループ（最大5回、EXPLORATION_NEEDED 収束判定） | 参照のみ |
| `.claude/skills/pir2/references/continuation-gate.md` | OUTER_LOOP_COUNT 上限到達時の続行可否4条件ゲート | 参照のみ |
| `.claude/skills/pir2/references/next-steps-queue.md` | 中断・再開のための checkbox 状態管理プロトコル | 参照のみ |
| `.claude/skills/pir2/references/retrospector-prompt.md` | retrospector 起動仕様（必須パラメータ一覧） | 参照のみ |
| `.claude/skills/pir2/references/run-dir-base.md` | RUN_DIR/成果物置き場の基底パス SSOT（中間ファイル vs 最終成果物の docs/ マップ） | 参照のみ |
| `.claude/skills/pir2/references/implementation-delegation.md` | 単一/shard/sequential/main の実装 actor 判定と再実装ルール | 参照のみ |
| `.claude/skills/pir2/references/handoff-cleanup.md` | handoff.md の完了判定・削除・残置ロジック | 参照のみ |
| `.claude/skills/pir2/references/team-member-prompts.md` | pir2async 専用チームメンバープロンプト定義 | 参照のみ |
| `.claude/skills/pir2/references/destructive-change-check.md` | pir2 専用の2軸（破壊性/動作変更）機械チェックとマトリクス | 参照のみ |
| `.claude/skills/pir2/references/feedback-conflict-gate.md` | 直前 feedback との自己照合ゲート | 参照のみ |
| `.claude/skills/pir2/references/refactor-advisor-gate.md` | refactor-advisor 起動〜適用〜退行検知の一連プロトコル | 参照のみ |
| `.claude/skills/pir2/references/tester-prompt.md` | TEST_SCOPE 構築ロジックと tester 起動仕様 | 参照のみ |
| `.claude/skills/pir2/references/experimental.md` | 試験実装レジストリ（4実験: shards/sequential/explorer-nesting/epic 自身）。**epic 自身の実験エントリが既に登録済み** | 参照のみ |
| `.claude/skills/pir2async/SKILL.md` | 比較基準2。Agent Teams 版（implementer+reviewer チーム化） | 参照のみ |
| `.claude/skills/pir2codex/SKILL.md` | 比較基準3。Implement のみ Codex 差し替え版 | 参照のみ |
| `.claude/skills/deepthink/SKILL.md` | 比較基準4。探索→熟考→統合→ゲートの反復ワークフロー（rubric による客観停止条件・ハードキャップ4ラウンド） | 参照のみ |
| `.claude/skills/research/SKILL.md` | 比較基準5。調査→集約→思考→仮説の直線ワークフロー（ループはthinker差し戻しの最大2回のみ） | 参照のみ |
| `~/.claude/pir-handoff.md` | handoff.md のライフサイクル詳細プロトコル（プロジェクト単位1ファイル・resume モード判定） | 参照のみ |
| `~/.claude/agents/retrospector.md`（該当箇所のみ） | retrospector が期待する入力パラメータ名（`PROJECT_MEMORY_DIR` / `RUN_DIR`）の確認 | 参照のみ |

---

### 比較観点別の詳細表

#### 1. ループのハードキャップと収束条件

| 観点 | pir2 / pir2async / deepthink の実装 | epic の対応 | 差分（逸脱/欠落/新規） |
|---|---|---|---|
| 再探索ループ | `exploration-loop.md`: `REPLAN_COUNT` 0開始、**上限5回**。収束判定は planner 返り値の `### EXPLORATION_NEEDED` セクションの有無で機械判定 | Phase1 で epic-planner が自前で explorer をネスト起動して自己解決するのが原則。それでも topic が残れば Phase1.5 のゲートでユーザー提示。「epic 本体は追加で epic-planner を再起動してもよいが、ハードキャップは pir2 ステップ4.5に倣い最大5回」と明記 | **部分的に踏襲**。ただし epic 側は「倣う」とだけ書かれ、`REPLAN_COUNT` 相当の変数名・収束判定の機械的手順（どのセクションを見て収束/継続を判定するか）が SKILL.md 本文に明記されていない。exploration-loop.md のような独立プロトコルファイルを持たず、口頭参照のみ |
| レビュー内側ループ | pir2 `INNER_LOOP_COUNT`（**上限3回**）。7-4 で FAIL 判定→修正→Fan-Out Gate 再起動 | 該当なし（epic 自体は reviewer を持たない。各ネスト pir2 が内部で持つ） | epic レベルでは不要な概念（レイヤーが異なる）。ただし epic は「各サブ pir2 が FAIL 上限に達したまま完了したケース」をどう扱うか未定義（後述7.参照） |
| テスト外側ループ | pir2 `OUTER_LOOP_COUNT`（**上限3回**）+ `continuation-gate.md`（4条件全て満たせば1回だけ続行可、Auto mode でも必ずユーザー応答を待つ） | 該当なし（同上、各サブ pir2 内部の話） | 同上 |
| 熟考ループ | deepthink `DEEPEN_COUNT`（**ハードキャップ4ラウンド**）。上限到達時は「PASSを捏造せず未達項目つき暫定結論として正直に報告」という明示ポリシー | epic の Phase2（DAG順ネスト pir2実行）自体には反復ループが存在しない（DAG を1周するだけ）。Phase3の統合確認で問題が見つかった場合「統合修正用のサブタスクを1本追加起動」とあるが、**この統合修正が再び問題を生んだ場合の上限・打ち切り条件が皆無** | **明確な欠落**。deepthink の「ハードキャップ到達→正直に未達を報告」に相当する設計が epic の Phase3 にない。統合修正サブタスクの追加は理論上無限に繰り返せてしまう（stop 条件・カウンタ・ユーザーへの「これ以上続けるか」ゲートがどこにも定義されていない） |
| 全体再試行（epicレベル） | pir2系は単一フローなので「全体リトライ」概念自体がない（フェーズが1本道でループは各内側だけ） | epic は複数サブ pir2 から成るため「1つのサブタスクが完全に失敗した場合、epic 全体としてどう振る舞うか」という概念が本質的に必要だが、**SKILL.md のどこにも定義されていない**（後述7.も参照） | **新規に必要な欠落**。既存パターンの直接の焼き直しでは埋まらない、epic 固有の未解決点 |

#### 2. fan-out 宣言の転用可否

| 観点 | 実装 | epic の対応 | 差分 |
|---|---|---|---|
| fan-out-gate.md の設計 | reviewer 5観点専用。「観点マッピング」セクションが `correctness/consistency/quality/security/architecture` の5つに固定され、`reviewer.md` の role マッピングを直接参照する内容になっている。「reviewer 起動パラメータ」節も reviewer 固有の `REVIEWER_ROLE` / `REVIEW_INDEX` を前提とした具体仕様 | epic SKILL.md 3-1「独立サブタスクの並列 fan-out」で「pir2 の Fan-Out Gate 慣習に倣い」「宣言テンプレは pir2 ステップ7-2A の型を流用します（`fan-out-gate.md` を参照）」と記載 | **型（フォーマット）のみの転用であり、内容は転用不可**。fan-out-gate.md 自体は reviewer 専用の観点マッピング・起動パラメータを含み、epic のサブタスク起動用に一般化されたテンプレートではない。epic は実質的に「宣言テンプレの見た目」だけ真似ており、epic 専用の宣言仕様（起動体数=独立集合サイズ、対象=サブタスク Ti、モデル=opus 固定等）を独自に SKILL.md 3-1 に手書きしている。**pir2async の 5-2A も同型の"自己コミットメント宣言"パターンを持っており、これで3つ目の実装（reviewer 5並列 / impl-review チーム N+1並列 / epic サブタスクN並列）が同じ「起動直前の自己コミットメント文」構造を持つに至っている。これは fan-out 宣言というパターンを純粋な**汎用プロトコル（起動体数を宣言し、それと一致する数の Agent を同一 function_calls ブロックで起動する）として `references/` に切り出す価値がある構造投資領域**（下記「既存パターン・規約」参照）。現状は3箇所に類似記述が重複しており、epic はこの重複の3件目という位置づけ |
| 違反検出とリカバリ | fan-out-gate.md に「違反パターンと検出」「違反検出時のリカバリ」の専用節がある（ブロック分割・体数不足・観点削減・宣言省略の4パターンを明示し、リカバリ手順3ステップを定義） | epic SKILL.md 3-1 には違反検出・リカバリの記載が一切ない（「宣言してください」だけで終わる） | **欠落**。pir2 / pir2async は両方とも「違反時どうするか」まで定義済みだが、epic は宣言テンプレの型だけ借りて違反時のリカバリ手順を持たない |

#### 3. 中断・再開（resume）

| 観点 | 実装 | epic の対応 | 差分 |
|---|---|---|---|
| プロジェクト単位の resume | pir2/pir2async/pir2codex: `$HANDOFF_PATH = ${PROJECT_ROOT}/.ai-pir-runs/handoff.md`（**run 非依存・プロジェクトに1ファイル**）。起動時に `引継い`/`続き`/`resume`/`handoff` 等のキーワードで `RESUME_MODE` を判定し、`resume`/`passive-notice`/`new` の3分岐で挙動を変える | **epic には resume 機構が一切存在しない**。SKILL.md 内に `HANDOFF_PATH` の文字列すら登場しない | **完全な欠落**。epic は Phase1→1.5→2→3 と複数ターン・長時間にまたがる設計だが（SKILL.md 冒頭でも「3階層ネスト構造」「深さバジェット制約」を明記するほど重厚なフロー）、ユーザーとの対話中断後に「前回どこまで進んだか」を復元する仕組みがない。特に Phase2（DAG順にネスト pir2 を複数回起動）は1回のセッションで完結しない可能性が高いタスク粒度（「大規模タスク」対象）であるにもかかわらず、この機構が欠けているのは pir2 系との際立った逸脱 |
| 次に何をすべきかの状態管理 | pir2/pir2async: `next-steps-queue.md` により `{RUN_DIR}/next-steps.md` に checkbox リストを Write。**ユーザー会話で1ターン以上中断した後、次の判断前に必ずこのファイルを Read する**運用を明記（pir_pattern_registry の実際の失敗パターン「スキル本体が次にすべきことを失念する」への対策として導入された経緯） | epic は `{EPIC_RUN_DIR}/epic-runs.md`（ステップ3-5、Ti→サブRUN_DIR対応表）を持つが、これは**観測可能性の記録**であり、「次にすべきステップ」を示す checkbox キューではない | **欠落**。next-steps.md 相当の epic 版（例: `epic-next-steps.md` に「Phase1 完了」「Phase1.5 確認待ち」「T3 起動待ち（依存: T1,T2完了）」等の checkbox）が無く、中断復帰時に epic 本体が「今 DAG のどこまで進んだか」を確実に参照する手段がない。epic-runs.md はあくまで完了報告用の記録であり、未完了の待機状態は表現できない設計 |
| サブフローレベルの resume | （該当なし。pir2 自体がプロジェクト単位の主体） | 各ネスト pir2（L1ランナー）はそれぞれ独立した `${PROJECT_ROOT}/.ai-pir-runs/handoff.md` を読み書きする設計になる（pir2 SKILL.md をそのまま Read させて実行させるため） | **潜在的な設計上の懸念（新規発見）**: `handoff.md` は「プロジェクト単位で1ファイル」（`run-dir-base.md` 明記）。epic の Phase2 3-1「独立サブタスクの並列 fan-out」で複数のネスト pir2 を**同一メッセージ内で並列起動**した場合、それらは全て**同一の `${PROJECT_ROOT}/.ai-pir-runs/handoff.md`** を読み書きしようとする。pir2 SKILL.md 側は単一起動を前提に設計されており、複数ネスト pir2 の並列書き込み競合（後勝ち上書き）が起きうる。epic 側にはこの競合を回避する記述がどこにも無い（epic-planner の「共有リソース競合」は同一ファイル・外部状態のみ言及しており、handoff.md というメタ状態ファイルの競合は考慮対象に入っていない） |

#### 4. 成果物の永続化

| 観点 | 実装 | epic の対応 | 差分 |
|---|---|---|---|
| 最終成果物の docs/ 配置規約 | `run-dir-base.md` に明記のマップ表: `pir2`/`pir2async`/`pir2codex` → `docs/plans/`、`research` → `docs/research/`、`deepthink` → `docs/deepthink/`、`reviewer`/`review-pr`/`refactor-advisor` → `docs/reviews/`、`debug` → `docs/debug/`。**中間ファイル（RUN_DIR配下）と最終成果物（docs/配下・git追跡）を明確に分離**する設計原則が全ワークフロー共通 | epic-planner の成果物 `epic-plan.md` は `{EPIC_RUN_DIR}/epic-plan.md`（= `${PROJECT_ROOT}/.ai-pir-runs/<run>-epic-<feature>/epic-plan.md`）のみに書き出される。SKILL.md にも epic-planner.md にも **`docs/` へのコピーに関する記述が一切ない** | **明確な欠落**。`run-dir-base.md` のマップ表に `epic` 自体の行が存在しない（表は pir2系/research/deepthink/reviewer系/debug/ir のみ列挙）。epic-plan.md は epic 全体の設計判断（分割戦略・DAG・USER_DECISION_REQUIRED）を含む「人が読むべき最終成果物」に相当する性質を持つにもかかわらず、`.ai-pir-runs/`（git 追跡外・`.gitignore` 対象）にしか残らない。run 終了後に epic-plan.md を参照したい/レビューしたいというニーズに対して、他ワークフローと同水準の永続化が提供されていない。整合させるなら `docs/epics/YYYY-MM-DD-<feature>.md` 相当を新設し `run-dir-base.md` の表にも追記すべき箇所 |
| 各サブ pir2 の最終成果物 | 各ネスト pir2 自身は通常運転通り `docs/plans/YYYY-MM-DD-<feature>.md` を書く（pir2 ステップ5がそのまま動くため） | 特に epic 側からの追加指示なし。ネスト pir2 が pir2 SKILL.md をそのまま実行するため自動的に担保される | 差分なし（ここは pir2 の既存機構にフリーライドできている） |

#### 5. retrospector 統合

| 観点 | 実装 | epic の対応 | 差分 |
|---|---|---|---|
| 必須渡しパラメータ | `retrospector-prompt.md` 記載の必須項目: `PROJECT_MEMORY_DIR`・`PROJECT_ROOT`・`RUN_DIR`・`META_MODE=false`・`INNER_LOOP_COUNT`・`OUTER_LOOP_COUNT`・`REPLAN_COUNT`・`PLAN_STRATEGY_CHANGED`・`EXPERIMENTAL_PATH`・`OBSERVATION_LOG_PATH`・`{RUN_DIR}/review-*.md`/`test-*.md` パス一覧・最終 VERDICT・ワークフロー種別。retrospector.md 本体（N1 節）も `PROJECT_MEMORY_DIR` 配下の `pir_*_log.md` 群と `RUN_DIR` を明示的に期待する実装になっている | epic ステップ4「Phase 3」: 「`retrospector` を `Agent` ツールで起動し、`ワークフロー種別: epic` と `experimental.md` の epic 実験セクション観測を依頼してください（起動仕様は `retrospector-prompt.md` を参照）」とだけ記載 | **必須パラメータの大半が epic 側で明示されていない**。特に `PROJECT_MEMORY_DIR` が epic ステップ4で一度も言及されない（ステップ1で `PROJECT_MEMORY_DIR` 自体は算出しているが、Phase3 のretrospector起動プロンプトに含める、という記述が無い）。retrospector.md N1 はこのパラメータが無いとプロジェクトログ (`pir_planner_log.md` 等)を読めず、通常モードの前提が崩れる。また `INNER_LOOP_COUNT`/`OUTER_LOOP_COUNT`/`REPLAN_COUNT`/`PLAN_STRATEGY_CHANGED` はそもそも epic レベルには存在しない概念（各ネスト pir2 内部にのみ存在）ため、「epic 全体としてこれらの集約値をどう作って retrospector に渡すか」が未定義（例えば「サブ pir2 のうち何本が REPLAN_COUNT>0だったか」のような集約統計が本来 retrospector にとって有用だが、epic はそれを収集する仕組みを持たない） |
| model 切替条件 | `retrospector-prompt.md`: `INNER_LOOP_COUNT==0 かつ OUTER_LOOP_COUNT==0` なら `sonnet`、それ以外は `opus` | epic は model 指定の記載なし | **未定義**。epic レベルでは INNER/OUTER_LOOP_COUNT に相当する量がないため、この判定式をそのまま使えない。epic 独自の切替基準（例: 「1つでもサブ pir2 がFAIL上限に達したら opus」等）が必要だが定義されていない |
| 実験観測の指示 | 他ワークフローは `experimental.md` の該当実験（shards/sequential/explorer-nesting）を汎用的に観測させる（ワークフロー横断で共通） | epic は自身の実験 `epic-orchestrator-nested-pir2` の観測を明示的に依頼 | epic 固有の実験が既に `experimental.md` に登録済みであることは確認できた（Started: 2026-07-03、Metrics/Adoption Criteria/Rejection Criteria まで整備済み）。この点は他ワークフロー同様の型に**正しく追従できている**数少ない箇所 |

#### 6. ユーザーゲート設計

| 観点 | 実装 | epic の対応 | 差分 |
|---|---|---|---|
| プラン選択肢確認 | pir2 ステップ4.6「`plan-choice-gate.md`」: 検出トリガー4種（複数案・USER_DECISION_REQUIRED・スコープ縮小・外部依存不足）→ 確認フォーマット（推奨案の透明化必須）→ 別案時は「別案の字義解釈確認」（拡張解釈と字義解釈を分けて確認）→ 承認後 `PLAN_STRATEGY_CHANGED=true` で再起動、さらに**v2提示後の方針変更**には「v2→v3切替の真意確認」という3軸（影響範囲/変更対象/既存維持対象）の追加確認まで存在 | epic ステップ2.5「Phase 1.5」: `plan-choice-gate.md` に「倣う」とし、epic-plan.md の全文（サブタスク一覧＋依存グラフ＋各pir2タスク記述）を提示して承認を得る、とだけ記載。「ユーザーが分割方針を変えた場合は epic-planner を再起動」で終わる | **簡略化された対応関係**。トリガーの検出（epic-planner がどう「複数案」「スコープ縮小」等を判定するか）は epic-planner.md 6.「既存ルール照合」に「USER_DECISION_REQUIRED の発行条件は planner.md と同じ姿勢で判断する」と記載されており概念としては引き継がれている。しかし pir2 側の**「別案の字義解釈確認」「v2→v3切替の真意確認」という2段階の予防ゲート**（ユーザーの拡張解釈による過剰スコープ変更を防ぐ CLAUDE.md「ユーザー発話の字義範囲解釈」原則の実装）が epic 側には一切引用・言及されていない。epic は「大規模タスク分割」というより字義解釈の齟齬が起きやすい（サブタスク境界の増減は影響が大きい）性質の判断を扱うにもかかわらず、この保護機構を継承していない |
| 未解決事項確認（実装後） | pir2 ステップ6.5: implementer 返り値の「未解決事項の有無」で(a)(b)(c)分類→(A)(B)(C)の選択肢提示→`user-decisions.md` に記録 | epic ステップ3-4「ユーザーゲートの epic 本体への委譲（bubble-up）」: ネスト pir2 内部でこのゲートに到達したら「保守的デフォルトを選び、`{サブRUN_DIR}/deferred-decisions.md` に記録し、`DEFERRED_USER_DECISIONS` に列挙」→ epic 本体がサブ pir2 完了ごとに集約し「本質的にブロッキングなものはユーザーに提示」「軽微なものは Phase3 サマリーで一括報告」 | **対応関係はあるが判断基準が曖昧**。「本質的にブロッキングなもの」と「軽微なもの」の判定基準が epic SKILL.md のどこにも定義されていない（pir2 の6.5-1のような(a)(b)(c)分類ロジックの epic 版が存在しない）。何を epic 本体が「ブロッキング」と判断するかが epic 本体の主観に委ねられており、pir2 の明示的分類フローと比べ機械的な判定基準を欠く |
| 続行可能ゲート | pir2 `continuation-gate.md`: OUTER_LOOP上限到達時に4条件（root cause確定/修正方針単一/影響範囲限定/根本原因収束）を**全て満たす場合のみ**ゲートを開く、という厳格な発動条件 | epic には该当なし（前述1.のとおり Phase3 の統合修正に上限・続行判断ゲートがない） | 前述1.と同根の欠落 |
| Auto mode 例外の明記 | pir2/deepthink/research とも「本ゲートは Auto mode でも必ずユーザー応答を待つ」と明記 | epic ステップ2.5「Auto mode でも例外なし」と明記（分割確認ゲートについては継承済み） | Phase1.5 のみは明記あり。しかし bubble-up されたブロッキング判断（3-4）の提示についてはAuto mode例外の明記がない |

#### 7. サブエージェント失敗時の回復

| 観点 | 実装 | epic の対応 | 差分 |
|---|---|---|---|
| reviewer/tester の無応答・FAIL 収束不能時 | pir2: `INNER_LOOP_COUNT>=3` で強制的に次段へ移行し「失敗として記録」。`OUTER_LOOP_COUNT>=3` で `continuation-gate.md` の4条件ゲートを開き、満たさなければ無条件で次へ進み VERDICT:FAIL を確定。**いずれも「進めなくなって停止する」ことがなく、必ずどこかのステップへ抜けるフォールバック経路が保証されている** | **epic には同種のフォールバック経路が定義されていない**。ネスト pir2 が最終的に VERDICT:FAIL のまま完了した場合、epic 本体がその結果をどう扱うか（別サブタスクとして起動されている後続タスクに進んでよいか、DAG全体を止めるか、ユーザーに確認するか）が SKILL.md のどこにも書かれていない | **重大な欠落**。DAG上、あるサブタスク Ti が FAIL で終わった場合、Ti に依存する後続 Tj をどう扱うか（進める/止める/ユーザーに聞く）の判断ルールが皆無。pir2系の「必ず先へ抜けられる」設計原則が epic の DAG 実行には引き継がれていない |
| Agent 起動自体の失敗（深さバジェット枯渇等） | deepthink `fable-solo` は「起動失敗時は `opus-panel` にフォールバックし、その旨をサマリーに記録する」という**具体的なフォールバック先**を明記 | epic 3-3「深さバジェット管理」: 「L2 での `Agent` 起動が深さ超過で拒否された場合は、その pir2 は `IMPLEMENTATION_ACTOR=main`／直接探索の inline モードにフォールバックして完遂すること」とネスト pir2 ランナーに指示する形で**フォールバック先自体は明記されている** | **ここは pir2/deepthink 相当の設計をむしろ持っている数少ない箇所**。ただし「ネスト pir2 ランナーに指示する」形であり、実際にランナー（L1、`general-purpose` + SKILL.md Read 方式）がこの指示を確実に守れるかどうかは検証されていない（epic-planner.md や experimental.md にも「深さバジェット超過が運用を破綻させていないか」を Rejection Criteria として観測対象に含めている＝epic 側もこの点をリスクとして自覚している） |
| Codex 実装失敗（pir2codexの類例） | pir2codex 6-1「wrapper 返り後のスキル本体の処理」: 「Codex の自己申告を信じない」「git diff で実体検証（必須）」「変更が空・プラン外への波及がある場合は対処（再実行 or ユーザー確認）」と、**外部実行主体の結果を鵜呑みにしない検証プロトコル**が明記されている | epic 3-0「ネスト pir2 の起動方式」には、L1ランナー（`general-purpose`）の報告を検証する記述がない（「返り値から得た『作業ディレクトリ』パス・変更ファイル一覧」を注入するとあるだけで、それが実在するか git diff で検証する、という記述はない） | **欠落**。pir2codex が確立した「サブエージェントの自己申告を信じず git diff で検証する」原則（CLAUDE.md「ツール結果の捏造の絶対禁止」とも整合する設計）が、epic の L1ランナー報告の扱いには反映されていない。epic は L1（`general-purpose` に SKILL.md を Read させる間接的な実行方式）という pir2codex 以上に「本当にちゃんとステップを踏んだか」を検証しにくい構造を採用しているにもかかわらず、この検証ステップが無い |

---

### 既存パターン・規約

- **命名規約**: `RUN_DIR` / `EPIC_RUN_DIR` のように基底変数名にプレフィックスを付けるのは pir2 系共通の慣習（`RUN_DIR`, 一部 `HANDOFF_PATH`）を踏襲。epic は独自に `EPIC_RUN_DIR` を新設しており、命名自体は一貫性がある
- **ディレクトリ構造**: 中間ファイル = `${PROJECT_ROOT}/.ai-pir-runs/<run>/*.md`（git追跡外）、最終成果物 = `${PROJECT_ROOT}/docs/<kind>/*.md`（git追跡）という2層構造が全ワークフロー共通の設計原則（`run-dir-base.md` がSSOT）。epic はこの原則の**後半（docs/への永続化）を実装していない**（前述4.参照）
- **参照ファイルへの委譲パターン（DRY）**: pir2 は SKILL.md 本体を薄くし、詳細を `references/*.md`（現在15ファイル）に切り出す設計を徹底しており、SKILL.md 側は「詳細プロトコル: `~/.claude/skills/pir2/references/xxx.md` を参照」という定型文で誘導する。pir2codex も「通常/pir2と同一のステップは~を SSOT として参照します（DRY・二重管理回避）」と明言し、差分（Codex実装部分）だけを厚く書く設計。epic は「epic 専用の `references/` は作りません（既存の `pir2/references/*.md` を参照する）」と明記しており、この DRY 原則自体は正しく継承している。ただし fan-out-gate.md のように「型だけ流用・内容はreviewer固有で使えない」ファイルを"参照"としているケースがあり、DRY の見た目を保ちつつ実質的には epic 側で独自ロジックを SKILL.md 本文に書き下ろしている箇所がある（2.参照）
- **構造投資領域（structurally-invested area）**: 「起動直前の自己コミットメント宣言」パターン（Fan-Out Gate 型のテンプレート）が pir2 ステップ7-2A（reviewer 5並列）、pir2async ステップ5-2A（impl-review チーム N+1並列）、deepthink ステップ4-a（deliberator N並列）、epic ステップ3-1（サブタスク並列）の**計4箇所**で反復出現している。いずれも「起動体数を明示的に宣言 → 同一 function_calls ブロックで一致数起動 → 違反時はやり直し」という同一構造。3個以上のクラスファミリーとして存在するため、**epic 改善の選択肢の一つとして「fan-out宣言の汎用プロトコルを `references/fan-out-declaration.md`（仮）として抽象化し、reviewer固有の観点マッピングを持つ現行 `fan-out-gate.md` とは分離する」という案を検討候補に含めるべき**（現状は reviewer 専用ファイルへの参照が3ワークフローで再利用されつつ、実体は各ワークフローがSKILL.md本文に手書きで型を複製している状態）
- **試験実装レジストリのパターン**: `experimental.md` は4件の実験（shards/sequential/explorer-nesting/epic自身）が全て同一のサブ構造（Hypothesis / Implementation / Quality Guardrails / Metrics / Adoption Criteria / Rejection Criteria / Evidence Summary / Observation Log）を持つ。epic のエントリ（`epic-orchestrator-nested-pir2`）はこの型に正しく追従できている
- **共通ユーティリティ**: `run-dir-base.md`, `sanitized-cwd.md`, `exploration-loop.md`, `plan-choice-gate.md`, `retrospector-prompt.md`, `handoff-cleanup.md`, `next-steps-queue.md` が「PIR²系スキル共通」を謳って複数ワークフローから参照される設計になっている。epic はこのうち `run-dir-base.md`（Step1でSSOT明記） と `fan-out-gate.md`／`plan-choice-gate.md`／`retrospector-prompt.md`（部分的・宣言的にのみ）を参照しているが、`exploration-loop.md`／`next-steps-queue.md`／`handoff-cleanup.md`／`continuation-gate.md` は**参照すらされていない**（前述1.3.6.7参照）

---

### 影響範囲

本調査は改善点抽出のための比較調査であり、コード変更を行っていない。仮に epic 改善を実施する場合の想定影響範囲:

- **直接影響**: `.claude/skills/epic/SKILL.md`（Phase3の上限ゲート追加・retrospector起動パラメータ追加・docs/永続化追加・resume機構追加・fan-out違反リカバリ追加等）、`.claude/agents/epic-planner.md`（USER_DECISION_REQUIRED判定基準の明確化）
- **間接影響**: `.claude/skills/pir2/references/run-dir-base.md`（epic の docs/ マッピング行を追加するなら表を更新）、`.claude/skills/pir2/references/experimental.md`（epic 実験セクションの Implementation/Quality Guardrails に新設ゲートを反映）、`CLAUDE.md`（`.claude/` 概観の epic 説明に新機構を反映する場合）

---

### 依存関係

- **インポート関係（epic → 既存資産）**: epic SKILL.md は `run-dir-base.md`（RUN_DIR算出）、`plan-choice-gate.md`（Phase1.5の型）、`fan-out-gate.md`（3-1の宣言型）、`retrospector-prompt.md`（Phase3の起動仕様参照）、`sanitized-cwd.md`（PROJECT_MEMORY_DIR算出）、`~/.claude/skills/pir2/SKILL.md` および `~/.claude/skills/pir2codex/SKILL.md`（ネスト起動対象そのもの）に依存する。epic-planner.md は `explorer.md`（ネスト起動対象）と `planner.md`（USER_DECISION_REQUIRED判定基準の準拠先）に依存する
- **被参照関係**: `CLAUDE.md` の「エピックオーケストレーション」節が epic/epic-planner を紹介。`experimental.md` の `epic-orchestrator-nested-pir2` セクションが epic を実験対象として追跡している。他ワークフローから epic への参照は無い（epic が最上位オーケストレーター）

---

### 補足情報

- **視覚情報との整合性チェック**: 本タスクにはユーザー提供のスクリーンショット等の視覚的一次情報は含まれていないため、本チェック項目は該当なし
- **「存在しない」型結論のチェック手順**: 本調査で「epic に○○が存在しない」と結論した項目（resume機構・next-steps相当・docs永続化・fan-out違反リカバリ・DAG失敗回復パス・retrospector必須パラメータ渡し）については、いずれも (1) `.claude/skills/epic/SKILL.md` 全文（143行）を通読、(2) `.claude/agents/epic-planner.md` 全文（144行）を通読、(3) grep により `EPIC_RUN_DIR|HANDOFF_PATH|next-steps|handoff|continuation-gate|PROJECT_MEMORY_DIR` 等のキーワードが epic 側ファイルに出現するか確認、の3段階で行った。検索した keyword: `handoff`, `HANDOFF_PATH`, `next-steps`, `continuation-gate`, `PROJECT_MEMORY_DIR`, `RUN_DIR`（EPIC_RUN_DIRとの混同有無）, `docs/`, `REPLAN_COUNT`, `INNER_LOOP_COUNT`, `OUTER_LOOP_COUNT`。いずれも epic SKILL.md / epic-planner.md 本文中に該当箇所が見つからなかったことを確認した上で「欠落」と記載している
- **新規に発見したリスク（比較観点外だが重要）**: `handoff.md` は「プロジェクト単位で1ファイル」という pir2 設計（`run-dir-base.md`・`pir-handoff.md` 明記）であるため、epic の Phase2 で複数ネスト pir2 を**並列**起動した場合、全ネスト pir2 が同一の `${PROJECT_ROOT}/.ai-pir-runs/handoff.md` を読み書きしようとし、後勝ち上書きによる情報消失が起こりうる。これは pir2 側の設計が「単一起動」を前提にしているために生じる、epic 固有の新規リスクであり、epic-planner.md の「共有リソース競合」判定（同一ファイル・外部状態）の対象にも明示的に含まれていない
- **retrospector 統合の実務的懸念**: epic Phase3 のretrospector起動記述には `PROJECT_MEMORY_DIR` を渡す指示が欠けているため、このまま実行すると retrospector.md N1（プロジェクトログ読み込み）が空振りし、通常モードの前提（`pir_planner_log.md` 等の既存ログ参照）が機能しない可能性が高い

---

### 呼び出し元への依頼

- 本レポートは deepthink の熟考材料としての比較調査であり、実装は伴わない。epic 改善案の実装が必要と判断された場合は、対象ファイル（`.claude/skills/epic/SKILL.md` / `.claude/agents/epic-planner.md` / 必要なら `run-dir-base.md`）の編集をスキル本体経由で implementer 相当のフローに回すことを推奨する
- 「fan-out宣言の汎用プロトコル抽象化（`fan-out-gate.md` から reviewer 非依存部分を切り出す）」は複数ワークフロー（pir2/pir2async/deepthink/epic）に影響する横断的リファクタになるため、着手する場合は影響範囲確認のため追加 explorer（各ワークフローでの fan-out 記述箇所の全件列挙）の並列起動を検討してほしい
