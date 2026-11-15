VERDICT: FAIL

### 担当 role
architecture

### レビュー対象（実ファイルを Read 済み）
- `.claude/skills/epic/SKILL.md`（新規、143行）
- `.claude/agents/epic-planner.md`（新規、144行）
- `CLAUDE.md`（追記3箇所、`git diff` で全行 `+` のみ確認済み）
- `.claude/skills/pir2/references/experimental.md`（末尾に `epic-orchestrator-nested-pir2` 実験追記、`git diff --stat` で削除行なし確認済み）

比較対象として `~/.claude/pir2-protocol.md`、`.claude/agents/planner.md`（CORE含む全文）、`.claude/skills/pir2/SKILL.md`（ステップ見出し一覧・ステップ7周辺）、`.claude/skills/pir2/references/{fan-out-gate,plan-choice-gate,retrospector-prompt,implementation-delegation}.md`、既存 `pir2-explorer-nesting` 実験セクションを Read した。

---

### 判断根拠（担当観点別）

#### 1. 責務逸脱（最重要・High 判定の根拠）

epic-planner と epic 本体の責務分離自体は明確に実装されている。

- `epic-planner.md` の CORE は「分割は『分割レベル』に徹すること…具体的なファイル×関数×変更内容・実装ステップ列・コードレベル設計は出さないこと」「planner / implementer / reviewer / tester の起動…はスキル本体（メイン Claude）に集約する設計のため、あなたは起動しない」と明記しており、`tools` にも Edit がなく Write のみ（コード編集不可）。「エピック分割レポートフォーマット」に `IMPLEMENTATION_SHARDS`/`IMPLEMENTATION_UNITS`/実装ステップ列が存在しないことも実ファイルで確認した。分割レベルへの責務限定は妥当に実装されている。

一方で、epic 全体の中核メカニズム — `subagent_type=general-purpose` に `~/.claude/skills/${SUBTASK_SKILL}/SKILL.md` を Read させ「あなたはこのサブタスクの PIR² オーケストレーターです…最後まで実行してください」と指示する方式（SKILL.md ステップ3-0、`Agent ネスト起動方式の技術整合性` 節）— は、**サブエージェント（L1 = ネスト pir2 ランナー）に、implementer/reviewer/tester の起動・ループ管理・VERDICT 集約・ループカウンタ（`INNER_LOOP_COUNT`/`OUTER_LOOP_COUNT`/`REPLAN_COUNT`）の SSOT という、完全な制御オーケストレーション責務を持たせる設計**である。

これは `~/.claude/CLAUDE.md`「エージェント呼び出しプロトコル（PIR² 系）」節の以下の文言と文面上直接に矛盾する:

> 「PIR² では制御フロー（implementer/reviewer/tester の起動・ループ管理・VERDICT 集約・ユーザー確認ゲート）をスキル本体（= メイン Claude）に集約する設計を維持する…サブからのネスト起動は read-only の探索（explorer）に限り、planner/implementer/reviewer に許可する。**サブエージェント（planner 等）に制御オーケストレーション責務を持たせてはならない。**」

plan.md および実装（SKILL.md 冒頭・CLAUDE.md 追記）は、この矛盾のうち「ユーザー対話不可」の部分（Phase 1.5 / 3-4 の bubble-up 機構）だけを明示的に手当てしているが、**「制御オーケストレーション責務そのものをサブエージェントに持たせてはならない」という、より広い禁止規定との整合性は SKILL.md にも CLAUDE.md 追記にも一言も書かれていない**。

私自身の分析では、この禁止規定の根拠（括弧内: 「ループカウンタの SSOT・サブはユーザー対話不可・観測可能性のため」）は、epic の設計でも実質的に満たされている（各ネスト pir2 は自分のスコープ内でループカウンタを完結させており、ユーザー対話は bubble-up され、観測可能性は `EPIC_RUN_DIR`/`epic-runs.md` で担保される）と考える。つまり epic の設計は禁止規定の**趣旨**には反していない可能性が高い。しかし、それを**明文で正当化・reconcile する記述が実装のどこにも存在しない**のは、以下の理由で放置できない設計ギャップである:

- 禁止規定は全 PIR² 系スキル横断で最も強い断定表現（「持たせてはならない」）で書かれた設計原則であり、epic はその原則が直接適用される唯一の例外的ケースを実装しているにもかかわらず、例外である理由を書き残していない
- 将来 retrospector やユーザーがこの禁止規定を読んだとき、「epic は違反しているのか、正当な例外なのか」を判別する記述が存在せず、ガバナンスの一貫性が損なわれる
- 逆に、この前例を根拠に「サブエージェントへの制御責務付与」が別の文脈でも安易に正当化される波及リスクがある（reconcile 文がないと歯止めが効かない）

**担当外観点との切り分け**: これは「grep で pir2/SKILL.md との文言不一致を見つける」consistency の話ではなく、「エージェント間の責務境界が既存の設計原則と構造的に整合しているか」という architecture 固有の判断であるため、担当領域内として扱う。

→ Critical/High 判定基準の「責務逸脱: クラス・モジュールが本来の責務と異なる処理を抱え込んでいないか…問題があれば High として報告する」に該当。**High**。

#### 2. レイヤリング

- epic → pir2 の参照は一方向（`grep -rn "epic" .claude/skills/pir2/` の結果、`experimental.md`（観測ログ用の記述）以外に epic への参照は無し）。pir2 側が epic を知る必要はなく、逆流参照は存在しない。
- epic が pir2 の `references/*.md`（`plan-choice-gate.md` / `fan-out-gate.md` / `retrospector-prompt.md` / `sanitized-cwd.md` / `run-dir-base.md`）を再利用する設計自体は、これらのファイルが既に `/pir2`, `/pir2async`, `/debug`, `/ir`, `/reviewer`, `/review-pr`, `/writing-plan` など複数スキル共通の SSOT として運用されている実績（pir2-protocol.md で明記）があるため、「private な実装詳細への不正参照」ではなく「既存の共有インフラ層への正当な参照」と評価できる。feedback_no_redundant_skills（重複 references を作らない）にも整合する。
- ただし、`references/*.md` への参照とは別に、**pir2/SKILL.md 本体の特定ステップ番号（`ステップ 7-2A` / `ステップ 4.5` / `ステップ 6.5` / `ステップ 12`）を直接引用**している箇所が複数ある（SKILL.md ステップ2「pir2 ステップ 4.5 に倣い最大 5 回」、ステップ3-1「pir2 ステップ 7-2A の型を流用」、ステップ3-4「6.5 未解決事項」、ステップ5「pir2 ステップ 12 の型」）。実在は `grep -n "^## ステップ"` で全件確認済みで**現状は正しい**が、これは `references/*.md`（安定した共有インフラ）とは異なり、pir2 の内部実装（SKILL.md 本体のステップ採番）という、より変動しやすい層への直接結合である。pir2 側がステップ番号を将来リナンバーした場合、epic 側はビルド時検証の仕組みがないためサイレントに陳腐化する。レイヤリング上、「安定した公開契約（references/）」と「変動しやすい内部詳細（SKILL.md 本体の採番）」への依存が epic 側で区別されずに混在している点は改善余地がある。**Medium**。

#### 3. 循環依存

- `grep -rn "epic" .claude/skills/pir2/` の結果、`experimental.md` の観測記述以外に pir2 → epic の参照は存在しない。`retrospector.md` も `ワークフロー種別` を汎用文字列パラメータとして受け取るだけで epic 固有の分岐を持たない（`grep -n "ワークフロー種別\|workflow" retrospector.md` で確認）。循環依存は検出されなかった。**問題なし**。

#### 4. 抽象粒度

- epic-planner の抽象粒度（DAG ＋ WHAT ＋ 境界のみ、ファイル×関数レベルは出さない）は、モチベーション（「実装詳細を抱えるとコンテキストが肥大し context 大きすぎで漏れる問題が epic-planner に再現する」）に対して適切な設計。過剰な抽象化（実装1つしかないのに interface を切る等のアンチパターン）も、過小な抽象化（具象直接依存の多発）も見当たらない。
- 一点、**深さバジェット抑制（SKILL.md ステップ3-3）が、`planner.md` の CORE に明記された固定的な権限（「`Agent` ツールで explorer をネスト起動できる…プラン策定中に広域探索が必要なら自分で explorer を起動してよい」）を、L1（ネスト pir2 ランナー）が追加するプロンプト指示だけで抑制する設計になっている**。CORE セクションは「変更禁止」と明記された、エージェント定義の不変契約であり、そこに書かれた権限をプロンプトレベルの一時指示で上書きする際の優先順位関係（CORE の宣言的権限 vs 呼び出し時の抑制指示、どちらが実効的に優先されるか）が SKILL.md にも planner.md にもどこにも明文化されていない。抽象化の観点で言えば、「L2 頭打ち」という epic 固有の制約が、既存エージェント定義（planner.md CORE）の抽象契約に対する **例外条件** として正式に組み込まれておらず、実行時のプロンプト伝達に依存する脆弱な抑制になっている。抽象粒度・契約設計としては Medium 相当の改善余地。**Medium**。

#### 5. 状態機械 SSOT の遵守

- epic は状態機械を導入する設計ではない（Phase 遷移は DAG に基づく単純な順序実行であり、状態×イベントの組合せ管理を意図した状態機械ではない）。該当領域なし。**非適用**。

---

### 参考: レビュー依頼の6項目への回答（上記判断根拠の要約）

| # | 依頼項目 | 評価 | 詳細 |
|---|---------|------|------|
| 1 | 責務分離（epic-planner が実装詳細を出さない） | 妥当（実装確認済み） | 「責務逸脱」参照。CORE・出力フォーマットとも実装ステップ/SHARDS/UNITS を含まない |
| 2 | context 分離設計の妥当性 | 妥当 | Ti タスク記述（WHAT+境界）のみ渡し、各サブ pir2 が自前 explore で復元する設計を SKILL.md ステップ3-0/3-2 で実装確認。先行成果の注入も working tree 経由＋明示パスの二重化で担保 |
| 3 | 3階層ネスト構造の健全性・「制御はスキル本体に集約」との整合性 | **未解決の矛盾あり（High）** | 「責務逸脱」参照。禁止規定の趣旨は満たしていそうだが、reconcile する記述が皆無 |
| 4 | 既存 references への依存の妥当性・結合度 | 一部懸念（Medium） | `references/*.md` の再利用自体は正当（既存の共有 SSOT）。ただし `retrospector-prompt.md` は `INNER_LOOP_COUNT`/`OUTER_LOOP_COUNT`/`REPLAN_COUNT`/`RUN_DIR` という pir2 単体実行前提のパラメータ契約を持ち、epic 本体にはこれらの概念自体が存在しない（epic は Phase 1 再起動上限5回・DAG 直列/並列という別の制御モデル）。SKILL.md ステップ4は「起動仕様は retrospector-prompt.md を参照と明記」するだけで、この不整合を一切調整していない。またステップ番号直接参照の脆弱性は「レイヤリング」参照 |
| 5 | 試験実装としての位置づけ | 妥当（実装確認済み） | experimental.md に既存3実験と同一構成（Status〜Observation Log）で起票済み。SKILL.md 末尾「試験実装の位置づけ」・CLAUDE.md 追記末尾にも明記。恒久機能と誤認させる記述はない |
| 6 | 共有ステート競合を依存グラフに吸収する設計の妥当性 | 条件付き妥当（Medium） | epic-planner の「暗黙依存」検出は WHAT レベルの粗粒度分析に基づくため、各サブ pir2 の詳細 planner が後で決定する実ファイルとの食い違いを事前には検出できない構造的盲点がある。ただし plan は「非重複性が曖昧なら直列に倒す」という保守的バイアスと、Rejection Criteria（「結合点の不整合が単一 pir2 運用より増え…」）での事後監視を明記しており、無策ではない。また pir2 の既存 `implementer-shards`（最大3体並列、同一 working tree に書き込み）も同種の非分離リスクを受容している既存パターンであり、epic はその延長線上にある（新規に導入されたリスクではない） |

---

### 問題一覧

- **High** `.claude/skills/epic/SKILL.md`（「Agent ネスト起動方式の技術整合性」節、ステップ3-0）／`.claude/agents/epic-planner.md` — ネスト pir2 ランナー（L1）に implementer/reviewer/tester の起動・ループ管理・VERDICT 集約・ループカウンタ SSOT という完全な制御オーケストレーション責務を持たせる設計が、`~/.claude/CLAUDE.md`「エージェント呼び出しプロトコル（PIR² 系）」の「サブエージェント（planner 等）に制御オーケストレーション責務を持たせてはならない」という断定的禁止規定と文面上矛盾しているにもかかわらず、SKILL.md にも CLAUDE.md 追記にもこの矛盾を reconcile する記述が一切ない。禁止規定の根拠（ループカウンタ SSOT・ユーザー非対話・観測可能性）は epic の bubble-up 機構と per-run 独立性により実質的に満たされている可能性が高いが、それを正式に例外として明文化しない限り、将来の retrospector・レビュー・他スキルからの類推適用でガバナンスの一貫性が崩れる。 → `.claude/skills/epic/SKILL.md` の「Agent ネスト起動方式の技術整合性」節、または `CLAUDE.md` のエピックオーケストレーション追記に、以下の趣旨の reconcile 文を追加する: 「ネスト pir2 ランナー(L1) は自身のサブスコープに限定して『スキル本体』として振る舞う。既存禁止規定『サブエージェントに制御オーケストレーション責務を持たせてはならない』は単一 pir2 実行内での責務分散防止（ループカウンタ SSOT の分裂・観測不能化）を意図したものであり、L1 が独立した pir2 実行の唯一の制御主体として完結して機能し、ユーザー対話とループカウンタの epic レベル集約が bubble-up 機構で担保される本設計は、禁止規定の趣旨に反しない例外として扱う」。

- **Medium** `.claude/skills/epic/SKILL.md` ステップ4（Phase 3）— `~/.claude/skills/pir2/references/retrospector-prompt.md` を「起動仕様は参照と明記」するだけで再利用しているが、同ファイルが要求するパラメータ（`INNER_LOOP_COUNT` / `OUTER_LOOP_COUNT` / `REPLAN_COUNT` / `RUN_DIR`）は単一 pir2 実行の制御モデルに固有の概念で、epic 本体自身の制御モデル（Phase 1 再起動上限5回・DAG 直列/並列・`EPIC_RUN_DIR`）には存在しない。 → SKILL.md ステップ4に「epic 本体からの retrospector 起動時は `RUN_DIR` の代わりに `EPIC_RUN_DIR` を渡し、`INNER_LOOP_COUNT`/`OUTER_LOOP_COUNT`/`REPLAN_COUNT` は N/A（該当なし）として明示する」等のパラメータ対応表を追記する。

- **Medium** `.claude/skills/epic/SKILL.md` ステップ2・3-1・3-4・5 — pir2/SKILL.md 本体の特定ステップ番号（`4.5` / `7-2A` / `6.5` / `12`）を直接引用しており、`references/*.md`（安定した共有 SSOT 層）への参照とは異なり、pir2 側の内部実装詳細（ステップ採番）に直接結合している。現状は全て実在を確認したが、pir2/SKILL.md が将来リナンバーされた場合にビルド時検証なくサイレントに陳腐化するリスクがある。 → 可能な箇所は `references/*.md` 経由の参照に寄せる、または「pir2/SKILL.md のステップ番号は将来変更されうるため epic 側の参照箇所は retrospector 等で定期的に照合すること」と明記する。

- **Medium** `.claude/skills/epic/SKILL.md` ステップ3-3（深さバジェット管理） — `planner.md` の CORE（変更禁止セクション）に明記された「explorer をネスト起動できる」という固定権限を、L1 が追加するプロンプト指示だけで抑制する設計になっており、CORE 記載の宣言的権限とプロンプトレベルの抑制指示の優先順位関係がどこにも明文化されていない。 → `planner.md`（および `implementer.md`/`reviewer.md`）の CORE 外の本文、または pir2-explorer-nesting 実験セクションに「呼び出し元から明示的に explorer ネスト起動を抑制する指示を受けた場合はそれに従う」旨の一文を追加し、抑制指示が CORE 記載の権限に優先することを正式な契約として明文化する。

- **Medium** `.claude/agents/epic-planner.md`（プロセス「4. 依存グラフ生成」）／`.claude/skills/epic/SKILL.md` ステップ3-1 — 共有ステート競合の検出が epic-planner の WHAT レベル粗粒度分析（a-priori）のみに依存しており、各サブ pir2 の詳細 planner が後で決定する実ファイルとの食い違いを検出するランタイム機構が存在しない。並列 fan-out で「独立」と判定されたサブタスクが、実際の実装段階で共有ファイルに触れる可能性を構造的に排除できない。plan.md は「非重複性が曖昧なら直列に倒す」という保守的バイアスと Rejection Criteria での事後監視を明記しており、pir2 の既存 `implementer-shards` も同種のリスクを受容済みのため Critical/High には格上げしないが、experimental.md の Metrics（「サブタスク境界の結合不整合の発生回数」）が実測されるまでは残存リスクとして明示すべき。 → 対応不要（既に Rejection Criteria で監視対象化されているため）だが、初回 `/epic` 実行時にこの失敗モードが顕在化したら即座に Rejection 判定候補として扱う運用を SKILL.md 側にも一言追記すると良い。

### 担当外で気づいた点（参考）

- `.gitignore:69`（推定） — `/.ai-pir-runs/` の1行追記は implementer 自身が「Bash で実行したものではない」と注意点(1)で報告している。スコープ逸脱の疑いがあるが、quality（スコープ逸脱担当）が `git diff --name-only HEAD` で正式に扱うべき領域のため architecture としては言及に留める。

### 良好点

- epic-planner の CORE・出力フォーマットが「分割レベル」に厳密に限定されており、実装ステップ・SHARDS/UNITS を一切含まない設計は、モチベーション（planner 1体への context 肥大回避）に対して的確に実装されている。
- Phase 1.5／3-4 のユーザーゲート bubble-up 機構（`DEFERRED_USER_DECISIONS`）は「サブエージェントはユーザー対話不可」という既存原則を正しく踏襲しており、epic 固有の新規リスク（サブ pir2 の独断スコープ縮小）に対する具体的な防御になっている。
- experimental.md の起票が既存3実験（`pir2-implementer-shards-and-review-fix-shards` 等）と完全に同一の構成（Status〜Observation Log）で書かれており、`git diff --stat` で削除行なしを確認済み。試験実装としての位置づけが恒久機能と誤認されない形で明示されている。

### 次のアクション

1. **（High・必須）** `.claude/skills/epic/SKILL.md` の「Agent ネスト起動方式の技術整合性」節（または CLAUDE.md のエピックオーケストレーション追記）に、L1（ネスト pir2 ランナー）への制御オーケストレーション責務付与が既存 CLAUDE.md の禁止規定とどう整合するかを明示的に reconcile する文を追加する。上記「問題一覧」の該当項目に具体的な文言案を記載済み。
2. **（Medium・推奨）** `retrospector-prompt.md` 再利用時のパラメータ対応表（`EPIC_RUN_DIR`→`RUN_DIR` 代替、`INNER_LOOP_COUNT` 等は N/A）を SKILL.md ステップ4に追記する。
3. **（Medium・推奨）** pir2/SKILL.md ステップ番号への直接参照箇所について、リナンバー時の陳腐化リスクを緩和する一文を追加する。
4. **（Medium・推奨）** planner.md 等 CORE 記載の explorer ネスト起動権限と、epic からの抑制指示の優先順位関係を正式に明文化する。
5. 上記1が最も優先度が高い（High 唯一の項目であり、VERDICT FAIL の直接原因）。2〜4 は次回サイクルでの改善で許容範囲。
