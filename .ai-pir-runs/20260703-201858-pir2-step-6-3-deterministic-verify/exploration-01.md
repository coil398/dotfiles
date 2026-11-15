## 探索レポート: pir2 SKILL.md 新ステップ「6-3: 決定論的完了検証」の挿入設計確定

前提として以下の設計 SSOT を読了済み:
- `docs/deepthink/20260703-190750-Fable5.md` §1-3・§1-4（設計の本体・血肉）
- `.ai-pir-runs/20260703-190750-Fable5/position-1.md` §1-3・§1-4（同内容の position 版・逐語一致）
- `.ai-pir-runs/20260703-190750-Fable5/exploration-01.md`（Fable5 内の先行探索。挿入点アンカーの一次確定はこちらで既に行われている）

本探索はその先行探索が扱わなかった **6.5 との前後関係** と **implementer 再起動の全ボトルネック** を実ファイルで詰め、planner が迷わない粒度まで詳細化するもの。

---

### 関連ファイル一覧

| ファイルパス | 役割・内容 | 変更の必要性 |
|---|---|---|
| `.claude/skills/pir2/SKILL.md` | pir2 全ステップ定義。ステップ6(6-0/6-1/6-2)・6.5・7・7.5・8 が今回の挿入対象 | 変更あり |
| `.claude/agents/implementer.md` | 実装完了レポートのフォーマット定義（`### 変更ファイル一覧` 見出し） | 参照のみ（既存フォーマットが機械抽出可能かの確認対象） |
| `.claude/skills/pir2/references/implementation-delegation.md` | shard/sequential/main actor 判定・shard 統合確認・review-fix shard・再実装ルール | 参照のみ（既存 git 突合先例。6-3 の「一般化」の直接の根拠） |
| `.claude/skills/pir2/references/refactor-advisor-gate.md` | refactor-advisor 起動〜適用〜再 reviewer フロー | 参照のみ（implementer 再起動ポイントの1つとして関与） |
| `.claude/skills/pir2/references/continuation-gate.md` | OUTER_LOOP_COUNT 上限到達時のユーザーゲート様式（38行の小型 reference） | 参照のみ（6-3 の失敗時ユーザーゲート様式の類似テンプレート候補） |
| `.claude/skills/pir2/references/destructive-change-check.md` | 2軸マトリクス判定＋ Write テンプレート＋軽量化ユーザーゲート様式（96行） | 参照のみ（6-3 reference file の書き味の参考） |
| `.claude/skills/pir2/references/next-steps-queue.md` | `{RUN_DIR}/next-steps.md` の初期 checkbox テンプレート（5.6-1） | 変更の必要性あり（後述） |
| `.claude/pir2-protocol.md` | pir2 系スキル共通の内部プロトコル集約先（43行） | 参照のみ（`git diff`/決定論/phantom/捏造 のいずれの語も現状ゼロ件。今回のトピックは未収録で衝突なし） |

---

### 既存パターン・規約

- **references/ 切り出しの粒度閾値は低い**: `handoff-cleanup.md`(13行) / `retrospector-prompt.md`(26行) / `exploration-loop.md`(30行) / `continuation-gate.md`(38行) と、10〜40行程度の小さいロジックでも SKILL.md 直書きせず reference ファイルに切り出す慣習が確立している。SKILL.md 側は必ず「詳細プロトコル: `path` を参照（要約）。要点: [1-2段落]」の定型文で締める。6-3 もこのパターンに従うのが既存慣習との整合性が最も高い。
- **bash スニペットは reference ファイル内に書いてよい**（`run-dir-base.md` 52-68行に Step0 標準 Bash が実例としてそのまま書かれている）。6-3 の git 集合照合ロジック（pre-set 記録・delta 計算）も reference ファイル内に bash で書ける。
- **ユーザーゲートのテンプレート様式**: `continuation-gate.md`・`destructive-change-check.md` は共に「発動条件の箇条書き→```コードブロックのユーザー提示フォーマット```→運用ルール（Auto mode 例外・記録先）」の3段構成。6-3 の失敗時ユーザーゲートもこの様式に倣うのが自然。
- **ループカウンタの管理規約**: `INNER_LOOP_COUNT`/`OUTER_LOOP_COUNT` はステップ6冒頭（SKILL.md 269行）で `= 0` 初期化され、ステップ12 最終サマリー（529/540/543行）で必ず報告される。新しいループカウンタ（後述の PHANTOM 再実行カウンタ）を導入するならこの2箇所（初期化・最終サマリー）両方に反映が要る。

---

### 影響範囲

- **直接影響**: `.claude/skills/pir2/SKILL.md` のステップ6（6-0〜6-2・完了後）、ステップ6.5、ステップ7-4、ステップ8-2、`refactor-advisor-gate.md` 7.5-5。新規 reference ファイル1点の新設。
- **間接影響**: `next-steps-queue.md` の 5.6-1 初期テンプレート（新規 checkbox 行の追加が必要）。ステップ12 最終サマリーのテンプレート（新規ループカウンタを追加するなら反映要）。`pir2async`（team-member-prompts.md）や `debug`/`ir` 等の姉妹スキルは今回のタスクスコープ外（SKILL.md は `pir2` のみが対象と依頼されている）だが、同型の implementer→reviewer 境界を持つため将来的な波及候補として認識しておく価値がある。

---

## 確定してほしい問いへの回答

### 問い1: 挿入位置の確定

**現在の実際の行番号・構造**（`.claude/skills/pir2/SKILL.md`、今回 Read で確認）:

```
267  ## ステップ 6: 実装（implementer）
269  `INNER_LOOP_COUNT = 0`、`OUTER_LOOP_COUNT = 0` から開始
271  ### 6-0: 実装 actor の決定
279  ### 6-1: implementer 起動
296  ### 6-2: 統合確認（`implementer-shards` / `implementer-sequential` 時）
302    最終行「implementer から実装要約を受け取ってください。」
304  ### 完了後（next-steps.md checkbox 更新）
308  ---
310  ## ステップ 6.5: 実装者の未解決事項ユーザー確認（該当時のみ）
314-349  6.5-1〜6.5-3
347  6.5-4: スキップ条件
353  ### 完了後
357  ---
359  ## ステップ 7: レビューループ（reviewer ハイブリッド並列、最大3回）
```

**確定事実**: 番号 `6-3` は Step 6 内部の `6-0`/`6-1`/`6-2` と同じハイフン付きサブ見出し（`###`）の連番であり、既存の `## ステップ 6.5`（ドット付き・独立トップ見出し）とは命名体系が異なる。この命名体系の違いから、**`6-3` は Step 6 内部の `### 6-2` の直後・`### 完了後`（304-306行）の直前に挿入する `###` サブセクションとして確定できる**（Step 6.5 の前後どちらに置くかという曖昧さは、番号体系自体が解消している。`6-3` は必然的に `6.5` より先に実行される）。

これは設計側（Fable5 exploration-01, 65行）が「6-1 と 7 の間」と書いた表現とも整合する（6.5 を明示的に議論していないが、6-3 という命名が Step 6 の内部連番である以上、6.5 より手前に来ることは命名の帰結として一意に決まる）。

**意味的な裏付け（推測・設計判断の補助線）**: 6-3 の目的は「implementer の claim が捏造でないか」の決定論検証。もし 6.5（未解決事項のユーザー確認）より後ろに置くと、捏造された可能性のある `implementation-{IMPL_INDEX}.md` の「注意点・未解決事項」記述をベースにユーザーに A/B/C 判断を仰いでしまう（土台が汚染された状態での対話）。6-3 を先に実行して PHANTOM_CLAIM を弾いてから 6.5 に進む方が、事象X型（捏造の上に判断を積む）を入口で防ぐという設計意図（position-1.md 74行）に忠実。この点は SKILL.md の番号体系がすでに強制している。

**次に必要な確認（planner が決めるべき点）**: 6-3 は「Step 6 の一部」として `## ステップ 6:` の見出し配下に留めるか、独立した `## ステップ 6-3:` トップ見出しにするか。既存の `6-0`/`6-1`/`6-2` は全て `## ステップ 6:` 配下の `###` サブ見出しなので、一貫性を取るなら `### 6-3: 決定論的完了検証` として Step 6 の内部に留めるのが最も既存規約に忠実（本レポートはこちらを推奨するが、決定は planner に委ねる）。

---

### 問い2: pre-set 記録の配線点

**確定事実（設計側の要求）**: position-1.md 1-4「pir2 本体が implementer 起動前に pre-set を記録し、完了報告後に...git delta を...照合」— pre-set（`git diff --name-only` ＋ untracked 一覧）は **implementer が起動される直前** に毎回記録する必要がある。

**確定事実（実ファイル調査: implementer (再)起動ポイントの全件列挙）**: SKILL.md 全文 grep の結果、implementer が (再) 起動される箇所は以下の **5 箇所**:

| # | 箇所 | 行番号 | 起動契機 | IMPL_INDEX 扱い |
|---|---|---|---|---|
| 1 | 6-1 | 279-294 | 初回実装 | `IMPL_INDEX=01` |
| 2 | 6.5-2 (C) | 328 | ユーザーが「追加指示で再実装」選択 | インクリメント |
| 3 | 7-4 (3) | 403 | reviewer FAIL（単一 or review-fix shard） | インクリメント |
| 4 | 8-2 (4) | 445 | tester FAIL | インクリメント |
| 5 | refactor-advisor-gate.md 7.5-5 | 61-64 | リファクタ提案適用 | インクリメント |

**重要な未解決点（planner が判断すべき最重要論点）**: position-1.md の設計文は挿入位置を「6-1 と 7 の間」と一点だけ名指ししているが、上表のとおり implementer は Step 7（reviewer 起動）に到達する前に **5 箇所すべてで (再) 起動されうる**。かつ #3・#4・#5 はいずれも「implementer 完了 → Step 7 の reviewer 起動（7-2A/7-2B）」という**同型の境界**を通る（7-4-(4) は同じ Step 7 内の再起動、8-2-(4)-(5) は「ステップ7に戻る」と明記、refactor-advisor-gate 7.5-5 の 3. も「Fan-Out Gate で reviewer 再起動」と明記）。

したがって、6-3 の「pre-set 記録 → 完了後照合」を**文字通り 6-1 の 1 箇所だけに適用するか**（＝初回実装のみ捏造検知、以降の再実装ループは無防備）、**Step 7 起動直前という境界の性質で一般化し 5 箇所すべてに適用するか**（＝ position-1.md 1-4 が「共通層に置く。epic 専用でなく」と述べた一般化の趣旨により合致）は、設計文からは一意に読み取れず、planner が明示的に決めるべき分岐点。本レポートは後者（5箇所すべてへの一般化）を推奨材料として提示するが、確定は行わない。

- 一般化する場合、6-3 の reference ファイルに「pre-set 記録は implementer が (再) 起動されるたび（6-1・6.5-2(C)・7-4-(3)・8-2-(4)・refactor-advisor-gate 7.5-5 のいずれか）に必ず実行する」という汎用手順として書き、各起動箇所（SKILL.md 5箇所 + refactor-advisor-gate.md 1箇所）にはその手順への参照を1行ずつ追記する構成が最小差分になる。
- 6-1 のみに限定する場合、SKILL.md への変更は 6-1/6-2 と新設 6-3 の周辺のみに閉じ、他4箇所は無変更で済む（実装コストは低いが、捏造保護の実効性は初回実装にしか及ばない）。

**もう1点の未解決点**: 6.5-2 (C) 実行後、SKILL.md 本文には「再試行する」としか書かれておらず、その後どのステップに進むか（6.5 自体を再度実行し直すのか、Step 7 に直接進むのか）が明記されていない。6-3 を 6.5-2 (C) 後にも適用するなら、このフロー自体の曖昧さも同時に解消が必要になる（6-3 タスクの副次的な巻き込み事項として planner に共有）。

---

### 問い3: implementer の変更ファイル報告形式

**確定事実**: `.claude/agents/implementer.md` 90-105行の「実装完了レポートのフォーマット」に、以下の固定見出しが既に存在する:

```
### 変更ファイル一覧
- `path/to/file1` — [変更内容の概要]
- `path/to/file2` — [変更内容の概要]
```

各行は `` - `path` — [概要] `` の形式で、バッククォート区切りのパスが機械抽出可能（`grep -oE '` \`[^`]+\` '` 等で抽出できる形）。この見出しは shard 実行時（`implementation-{IMPL_INDEX}-{SHARD_ID}.md`）・sequential unit 実行時（`implementation-{IMPL_INDEX}-unit-{UNIT_ID}.md`）でも implementer.md の同一プロセス定義（90-105行）が適用されるため、同一フォーマットが踏襲される（`implementer.md` はレポートフォーマットを actor 種別で分岐させていない）。

**確定事実（呼び出し元への返り値との差）**: implementer.md 107-124行「呼び出し元への返り値フォーマット」では、チャットに返る要約には「変更ファイル件数（代表3件まで列挙）」のみが含まれ、**全件リストは呼び出し元の要約には現れない**。したがって 6-3 の照合ロジックは、要約テキストではなく **`{RUN_DIR}/implementation-{IMPL_INDEX}.md`（または `-{SHARD_ID}.md` / `-unit-{UNIT_ID}.md`）本体を Read して「### 変更ファイル一覧」セクションから全件抽出する**必要がある（既存の shard/sequential/review-fix shard 統合確認も同じく「全 `implementation-*.md` を Read」という手順を取っており、この点は既存パターンと完全に整合）。

**未解決点**: `IMPLEMENTATION_ACTOR=main`（スキル本体が直接実装する fallback）の場合、implementer.md のシステムプロンプトが適用されず、`implementation-{IMPL_INDEX}.md` 相当のレポートを書くという規定が `implementation-delegation.md` のどこにも存在しない（14行に「スキル本体が直接実装する」とあるのみ）。この場合、6-3 が要求する「CLAIMED_FILES」の情報源が存在しない。main actor は「サブエージェントの自己申告」という telephone-game 境界自体が発生しない（スキル本体自身が編集した）ため、6-3 の適用対象から除外する（＝サブエージェント経由の actor のみに 6-3 を適用）のが自然な解釈だが、これも planner が明示的に決定・SKILL.md に明記すべき事項。

---

### 問い4: 既存先例（一般化の根拠）

**確定事実**: `implementation-delegation.md` に以下の既存 git 突合先例が存在する（いずれもデフォルト actor=`implementer-subagent` には現状適用されていない）:

- **shard 統合確認**（57-65行）: 「全 shard 完了後...1. 全 `implementation-{IMPL_INDEX}-*.md` を Read → 2. `git diff` で shard 外ファイル編集がないことを確認 → 3. 同一ファイル競合、命名不整合、重複抽象、未接続の実装を確認 → 4. 問題があれば `implementer-subagent` に戻して統合修正 → 5. 問題がなければ reviewer へ進む」
- **unit 統合確認**（103-110行）: shard 版とほぼ同型（対象が unit 境界の整合性チェック）
- **review-fix shard 統合確認**（128行）: reviewer FAIL 後の shard 修正時にも同型の確認が明記されている

**一般化の論拠**: これら3つの既存先例は共通して「①全レポートを Read → ② `git diff` で実ファイル変更を機械確認 → ③ 問題があれば単一 implementer に戻す」という構造を持つが、**目的は shard/unit の境界整合性チェック**（shard 外編集・命名不整合・未接続実装の検出）であり、「claimed 集合 vs 実 diff 集合の完全一致（PHANTOM_CLAIM/UNDECLARED_CHANGE の判定）」という M2/6-3 が指す形とは検証対象が異なる（Fable5 exploration-01, 63行の確定事実と同じ結論）。かつ、これらの既存確認は **`implementer-shards`/`implementer-sequential` 使用時のみ**発動し、デフォルトの `implementer-subagent`（単一 implementer、最も頻度が高い実行形態）には一切適用されない。

したがって「6-3 の一般化」は、①検証観点を「境界整合性」から「claim-vs-diff の集合一致」に拡張し、②適用範囲をデフォルト actor（`implementer-subagent`）にも広げる、という2軸の一般化と位置づけられる。これは新規発明ではなく、既存パターンの2方向拡張として位置づけ可能（position-1.md 1-4「既存の shard/sequential 統合確認の...デフォルト actor への一般化」という表現と正確に一致）。

---

### 問い5: reference 化 vs SKILL.md 直書き

**確定事実（粒度慣習）**: 既存 references は 13行（`handoff-cleanup.md`）から 279行（`experimental.md`）まで幅があるが、10〜100行程度のロジックは軒並み reference に切り出されており、SKILL.md 直書きの判断基準は「複数ステップから参照される汎用ロジックか」「bash/判定条件を伴う複雑さがあるか」で、行数の下限は事実上存在しない。

6-3 の内容見込み（pre-set 記録手順・delta 計算 bash・PHANTOM_CLAIM/UNDECLARED_CHANGE 判定条件・失敗時ユーザーゲート・NO_OP_JUSTIFIED 免除条件）は `destructive-change-check.md`（96行）や `continuation-gate.md`（38行）に近い複雑さであり、**reference 化が既存慣習と完全に整合する**。加えて、6-3 が「implementer の複数起動ポイント（最大5箇所）から共通参照される」性質を持つ場合（問い2参照）、単一箇所にしか登場しない SKILL.md 直書きより reference 化の方が「1箇所を直せば全参照箇所に反映される」という保守性でも有利。

**推奨（推測・判断材料）**: 新規 reference ファイル名の候補は `deterministic-completion-verify.md`（設計文の「決定論的完了検証」の直訳）。既存の `destructive-change-check.md`（判定→書き出し→ユーザーゲート）と `continuation-gate.md`（発動条件→ユーザー提示フォーマット→運用ルール）の2ファイルの構成をハイブリッドした構成が最も既存パターンに忠実:

1. 発動条件・pre-set 記録手順（bash、全起動ポイント共通）
2. PHANTOM_CLAIM / UNDECLARED_CHANGE / NO_OP_JUSTIFIED の判定条件（destructive-change-check.md 型の箇条書き＋根拠明記）
3. 失敗時ユーザーゲートのフォーマット（continuation-gate.md 型の3段構成）
4. `{RUN_DIR}/verify-{IMPL_INDEX}.md` 等への判定結果書き出しフォーマット
5. 完了後の next-steps.md checkbox 更新への言及

---

### 補足情報（実装時に必要になる周辺変更・planner への申し送り）

1. **`next-steps-queue.md` 5.6-1 の初期テンプレート**（22行）に「ステップ 6: implementer 起動」の checkbox しか無く、6-3 用の checkbox 行が無い。6-3 を独立ステップとして扱うなら、この初期テンプレートに `- [ ] ステップ 6-3: 決定論的完了検証` を追加する変更が必要（実装は自分で行わず、この探索レポート経由で planner/implementer に申し送る）。
2. **ステップ12 最終サマリーのテンプレート**（SKILL.md 515-554行）は `INNER_LOOP_COUNT`/`OUTER_LOOP_COUNT`/`REPLAN_COUNT` を報告するが、6-3 の「再実行1回」用に新しいループカウンタ（例: `PHANTOM_RETRY_COUNT`）を導入するなら、①SKILL.md 269行付近（既存カウンタの初期化箇所）と②515-554行の最終サマリーテンプレートの両方に反映が必要。
3. **CLAUDE.md「問題の迂回禁止」との整合性**: 「同一のツール呼び出し・コマンドが2回続けて失敗したら3回目を試さず止める」というルールと、設計側の「再実行1回→再失敗ならユーザーへ」は数として整合（初回失敗＋再試行1回＝計2回で停止）。この整合性は既存ルールとの矛盾がないことの確認材料として記録しておく。
4. **`main` actor（スキル本体直接実装）の scope 除外の要否**（問い3参照）は、6-3 の適用範囲を確定する上で必須の分岐点。
5. **6.5-2 (C) 後の遷移先が SKILL.md に明記されていない**（問い2参照）ことは、6-3 タスクとは独立した既存の曖昧さだが、6-3 を 6.5 系にも適用する場合は同時に解消が必要になる可能性がある。

---

### 呼び出し元への依頼

- 本タスクは pir2 SKILL.md のみを対象とした調査依頼だったため、姉妹スキル（`pir2async`・`debug`・`ir`）の同型 implementer→reviewer 境界への波及要否は調査していない。将来的に 6-3 相当の仕組みを他スキルにも展開する場合は、別途 explorer による `team-member-prompts.md`（pir2async 用）・`debug`/`ir` の SKILL.md 探索を追加起動することを推奨する。
- 上記「問い2」「問い3」「問い5」で明示した **3つの未確定分岐点**（① implementer 5起動ポイントのうち何箇所に 6-3 を適用するか、② `main` actor を適用対象に含めるか、③ reference ファイル名・構成の最終形）は、実装着手前に planner が明示的にプランへ記載し、既存パターンからの逸脱判断が必要ならユーザー確認（CLAUDE.md「既存構造パターンからの逸脱には事前確認が必要」）に回すべき事項として申し送る。
