## position（ROUND 1）: /epic（＋ネスト多エージェント機構）の完成形ワークフロー設計

> 統合ソース: `deliberation-1-01.md`（fable-solo が「第一原理・機序 / 反証・レッドチーム / 二次波及・境界条件 / 設計統合」の4レンズを内省網羅した完成形設計 1本）。今回は deliberation が1本のため、統合の主眼は (a) 設計本体の非痩せ転記、(b) rubric 8基準へのカバレッジ検証、(c) 前回 M1–M12・4対立・C1–C4 へのトレーサビリティ確認。

---

### 結論（現時点の最良の答え）

**epic の「完璧」は堅牢化でなく計器化である。** 委譲型オーケストレータは各層（L0 epic 本体 / L1 ネスト pir2 ランナー / L2 pir2 配下の専門サブ）の return を **claim（自己申告）として扱い、ground truth（同一 working tree の git）を各境界の受け手がローカルで引いて決定論照合する** — この **claims-up ＋ evidence-local-pull** を背骨に、Phase 0/1/1.5/2/3 ＋ L0↔L1↔L2 境界契約を1本の実行フローとして設計する。

- **アーキ**: L1（fresh-context の pir2 ランナー）を**恒久採用**（対立#1 の B）。制御純度の懸念は「L1 を信頼せず、L1 の外側=L0 境界に L1 が偽装できない git 検証を置く」ことで外側から充足。Option A（L0 直接統率）は per-node の inline フォールバック **A-lite** に降格して生存（C1 是正を兼ねる）。
- **検証は二重の決定論ゲート**: L2→L1 は **pir2 新ステップ 6-3**（共通層。observed 失敗2件は素の pir2 で起きたため epic 専用にしない）、L1→L0 は **epic 3-2**（L1 の集約 claim を起動前ベースラインとの delta で照合）。各境界に別の「信頼できない語り手」がいるため冗長でない。コストは境界あたり bash 数行・context O(1)。
- **破壊的操作は可逆性で二分**: 可逆判断→保守的デフォルト＋deferred（非ブロッキング）／不可逆（destructive-change-check.md フラグ a-e）かつ Phase 1.5 事前承認範囲外→L1 は完了させず `STATUS: ABORTED_PENDING_DECISION` で早期 return。可逆性は恣意性のない客観境界。
- **移行は段階ゲート付き**: 今すぐ作るのは W0〜W3（文書衛生＋pir2 6-3＋境界契約一式＋log-only hook）のみ。重い物（fan-out・floor 値・OTel）は全て観測ゲート **G1/G2** の背後。**設計の厚さと構築の厚さを分離**した。
- **条件付き結論であることの明示**: 対立#1 の「B 恒久」は無条件断定でなく、**G1 dry-run で L1 の契約遵守が是正1回を挟んで連続2回不履行なら A-lite 常用化をユーザー上程**という反証トリガ内蔵の「トリガが発火しない限りの恒久」。P5（L1 が SKILL.md 全文を自律オーケストレーションできる）は**未実証**で、この結論の可変部。

---

### 設計本体（痩せさせない転記 — gate と最終レポートの土台）

#### §0. アーキテクチャ総括 — 3層と信頼モデル

```
L0: epic 本体（メイン Claude）      … ユーザー対話の一極・DAG 進行・境界検証・台帳
L1: ネスト pir2 ランナー（fresh）    … /pir2 全13ステップの自律オーケストレーション（信頼しない語り手）
L2: explorer/planner/implementer/… … pir2 配下の専門サブ（信頼しない語り手）
共有 ground truth: 同一 working tree の git ＋ {RUN_DIR}/{EPIC_RUN_DIR} のファイル群
```

各層の return は claim。検証は「claim が越境する境界」ごとに、その境界の受け手がローカルの ground truth（git / `test -f` / hook が書いた metrics ファイル）を引いて決定論照合する。**LLM 判断は検証経路に挟まない。** 検証3層構成:

| 層 | 担い手 | 捕捉する誤り |
|---|---|---|
| 決定論 | git 集合照合・artifact 存在・tool_use floor（hook） | 行為の捏造（phantom claim）・ゾンビ成功 |
| LLM 判定 | reviewer（L2）・Phase 3 境界レビュー（L0） | 結論の質・結合整合 |
| 人間 | Phase 1.5 ゲート・失敗時ゲート・DEFERRED 集約 | 方針・不可逆判断 |

#### §1. L0↔L1↔L2 境界契約（背骨）

**1-1. 起動契約（L0→L1）— epic SKILL.md 3-0（83-87行）を置換.** 起動プロンプトに必須項目として明示: ① `SUBTASK_ID`/タスク記述/完了条件、② `EPIC_RUN_DIR`＋サブ RUN_DIR 命名規約（`run-dir-base.md` SSOT・`cut -c1-40` 統一=C4 非再導入）、③ **`HANDOFF_PATH` を `{サブRUN_DIR}/handoff.md` に上書き**（プロジェクト単位デフォルト禁止=F10 競合の構造的排除=M9）、④ 先行サブタスクの**検証済み**成果（RUN_DIR＋PASS 済み変更ファイルリスト）、⑤ return 契約（1-2 の必須見出し）、⑥ ゲートポリシー（可逆→保守デフォルト＋deferred／破壊フラグ a-e かつ事前承認外→`ABORTED_PENDING_DECISION` 即 return）、⑦ ループ上限＋再実行時の非冪等性注記（「前回試行の部分差分が working tree に残存。explorer で現状把握から」）。

**1-2. return 契約（L1→L0）— 機械 grep 可能な必須リテラル見出し（M1）.** pir2 ステップ12 サマリーが既にほぼ全フィールドを持つ（F1）ため実質はフォーマット固定化:

```
### EPIC_TELEMETRY
- SUBTASK_ID: T3
- STATUS: COMPLETED | ABORTED_PENDING_DECISION | FAILED
- FINAL_PHASE: explore|plan|implement|review|test|retro|complete
- VERDICTS: review=PASS|FAIL|N/A, test=PASS|FAIL|N/A
- LOOPS: INNER=n, OUTER=n, REPLAN=n
- CLAIMED_FILES: <改行区切りリスト or "none">
- ARTIFACTS: <サブ RUN_DIR 内の主要成果物パス（純分析タスク用）>
- RUN_DIR: <絶対パス>
### DEFERRED_USER_DECISIONS
<リスト or "なし">
```

> **M1 の正直なスコープ**: return テレメトリは「完了したが内容が偽/矛盾」（事象Y/X 型の事後検知）に効く。**L1 が return しないフリーズには原理的に効かない** — フリーズ検知は台帳 timestamp＋ハートビート mtime の外形診断（§8）が担う。

**1-3. L0 検証パイプライン（L1 return 受領直後）— epic SKILL.md 3-2（93-95行）に新設（M2/M12）.** 受領ごとに以下をこの順で（全て決定論・context O(1)）:

1. **契約存在チェック**: 必須見出しを grep。欠落→サブ RUN_DIR 成果物（walkthrough/summary/next-steps.md）を Read して再構成（artifact system が第二の情報源=return 切り詰め耐性）。再構成不能→失敗パス。契約違反は台帳に記録（G1 較正データ）。
2. **git 集合照合（C経路・最重要）**: 起動前 `pre-{Ti}.list`（`git diff --name-only`＋untracked）と `post-{Ti}.list` の差 `delta` を計算し —
   - `CLAIMED_FILES ⊆ post`（各 claimed が実際に dirty）違反＝**PHANTOM_CLAIM（捏造シグネチャ・hard fail）**
   - `delta ⊆ CLAIMED_FILES` 違反＝**UNDECLARED_CHANGE（warn。formatter 副作用等ありうるため非ブロッキング台帳記録＋報告に含める。他ノードの宣言書込集合と交差する場合のみブロッキング）**
   - CLAIMED_FILES=none かつ delta 非空→UNDECLARED。none かつ編集想定タスク→PHANTOM 扱い（`NO_OP_JUSTIFIED` 宣言時は免除）
3. **artifact 存在チェック**: ARTIFACTS 各パスを `test -f`（純分析タスクでも検証が空洞化しない）
4. **floor チェック（B経路・hook 稼働時のみ）**: `{cwd}/.ai-pir-runs/subagent-metrics.jsonl` から該当 agent_id 行を読み役割別 floor と突合
5. **STATUS 不変条件（M12）**: `STATUS=COMPLETED` ⇒ `review=PASS ∧ test∈{PASS,N/A}` でなければ done 扱いしない
6. **台帳追記（M3/M9）**: VERIFY 結果を epic-runs.md に1行イベントとして追記

> **失敗パス**: PHANTOM_CLAIM / floor 違反 / STATUS 不整合 → **再実行1回まで**、検証レポートを逐語注入（原因=不一致が特定済みなのでブラインドリトライ禁止と非衝突）。2回目失敗→`NODE_FAILED` 台帳記録＋**ユーザーゲート**: (a) 手動調査 / (b) 当該ノードスキップし依存下流ブロック（独立ノードは続行可）/ (c) epic 中止。補償は `git diff` 全 hunk をユーザー提示（**自動 restore は絶対にしない**=CLAUDE.md git ルール＝人間ゲート付き補償）。

**1-4. L2→L1 境界 — pir2 SKILL.md 新ステップ「6-3: 決定論的完了検証」（共通層・M2 の本丸）.** epic 専用でなく **pir2 共通層**に置く（観測失敗2件は epic 外の素の pir2 で発生。計器は共通層にないと当の失敗を捕まえられない）。挿入位置=pir2 ステップ 6-1（implementer 完了）と 7（reviewer 起動）の間（exp-01 確定アンカー）。pir2 本体が implementer 起動前に pre-set を記録し、完了報告後に `implementation-{NN}.md` の変更ファイルリストと git delta を 1-3 節 2. と同一規則で照合。PHANTOM_CLAIM→implementer 再実行1回→再失敗なら **reviewer を起動せずユーザーへ**（捏造の上にレビューを積まない＝事象X の「implementer claim と reviewer verdict の矛盾に解決経路なし→19分迷走」の連鎖を入口で切断）。既存の shard/sequential 統合確認（`implementation-delegation.md` 57-65/103-110行）の「デフォルト actor への一般化」と位置づけ相互参照（新規発明でなく既存先例の一般化）。

#### §2. Phase 0 — 初期化・resume 判定・ベースライン記録

（現行 SKILL.md 初期化ステップ相当を拡張。実挿入行は実装時 Read で確定 — exp-01 は 3-0 以降のみ行番号確定）

1. `EPIC_RUN_DIR` 確定（`run-dir-base.md` SSOT・`cut -c1-40`）
2. **resume 判定（M9）**: 未完了台帳があれば**記憶でなく台帳＋git で**状態再構成（各 Ti の台帳 status と git 実状態=claimed が dirty かを突合）→ 再開プランを**ユーザー提示・承認後に再開**。無言 auto-resume 禁止（事象X は resume 直後に発生）
3. **ベースライン記録**: `git rev-parse HEAD`＋`git status --porcelain` を `{EPIC_RUN_DIR}/state/baseline.txt` に保存。dirty 開始は台帳明記（M2 集合算術の前提）
4. **計器レベル判定**: SubagentStop hook 設定済みか確認し `INSTRUMENTS: FULL | GIT_ONLY` を台帳記録（hook 未導入でも C経路＋artifact で成立する**グレースフルデグラデーション**）

#### §3. Phase 1 — epic-planner（分割・DAG）追加要件（epic-planner.md へ）

分割レポートに必須列を追加: ① **サブタスク数 hard-cap**（M4。初期値≤5 仮置き・G2 較正、根拠が無いことを明記）、② **DAG 形状制約（M10）**: tree/線形のみ、fan-in（合流）は自動採用せず `USER_DECISION_REQUIRED`（merge 意味論未実装）、③ **推定書込集合（M11）**: 交差可能性あり→依存辺として直列化（既存「暗黙依存」直列化の入力を明文化。fan-out 解禁後は非交差宣言が並列の必要条件）、④ **破壊的分類（M7）**: 各 Ti を destructive-change-check.md フラグ a-e で事前分類、⑤ **完了条件の型**: 編集想定（CLAIMED_FILES 必須）or 分析想定（ARTIFACTS 必須）を指定（検証の空洞化防止）。

#### §4. Phase 1.5 — 分割確認ゲート（既存 2.5 / 69-77行 を拡張）

既存（plan-choice-gate 準拠・ブロッキング・L0 専任）に追加提示: ① **破壊的サブタスクの事前明示承認**（M7 前半。承認範囲は L1 が 5.7 を通過でき、範囲外の破壊操作だけが早期 return になる）、② **並列化プラン**: 直列既定 or opt-in 5条件を満たす場合のみ幅≤2 提案、③ **統合検証コマンド**（Phase 3 決定論バックストップ用。epic は汎用スキルでコマンドをハードコードできないため唯一の決定論的置き場）、④ timeout 挙動: 対話セッションのユーザー入力待ちで自然ブロック＝timeout-block は自明充足、無人運転は非サポート明記。

#### §5. Phase 2 — DAG 実行ループ（3-0〜3-5 の完成形。既定は直列・DAG 順）

- **2a. 起動前**: 台帳に `NODE_START`（Ti, timestamp, HEAD, pre_dirty 数）、`state/pre-{Ti}.list` 保存
- **2b. 起動**: §1-1 起動契約で L1 を Agent 起動（実行モードはプラットフォーム既定に任せる。強制同期 env 不採用）
- **2c. return 受領**: §1-3 検証パイプライン → `NODE_DONE(verified)` / `NODE_FAILED` / `NODE_ABORTED`
- **2d. ABORTED_PENDING_DECISION 時**: L0 がユーザーゲートを開き承認内容を注入して同ノード再起動（設計どおりの往復・DECISION 記録）。**A-lite（inline フォールバック=C1 是正の実定義）**: 深さバジェット超過時 or L1 が契約履行不能時、L0 が当該1ノードに限り pir2 SKILL.md を直接実行（ユーザー宣言後に移行・`FALLBACK_INLINE` 記録）
- **2e. deferred 集約＋矛盾検出**: ノード完了ごと DEFERRED を集約し、**依存下流の起動前に**蓄積 deferred 間の同一ファイル/トピック矛盾を照合（矛盾→下流起動前ユーザーゲート）
- **2f. fan-out（end-state・opt-in 時のみ）**: 幅≤2。バックグラウンド起動で L0 非ブロック、サブ RUN_DIR の next-steps.md mtime をハートビート観測。**並列時は git 集合算術が壊れる**（両 L1 が同時に tree を汚し delta 帰属が不定）→ 帰属規則を「`delta ∩ 宣言書込集合(Ti) = CLAIMED(Ti)`、全宣言集合外の delta はアラート」に切替（書込非交差が並列前提だから成立。副産物で M11 のランタイム検知が M2 の自然拡張で入手）

#### §6. Phase 3 — 統合検証・集約報告・retro（ステップ4 / 113-115行 を拡張）

① **決定論バックストップ**: Phase 1.5 確定の統合検証コマンドを全サブ結合後に1回実行（exp-03 #7 のギャップ充填。未確定なら「LLM 目視 diff のみ＝劣化モード」を台帳明記）、② 既存 LLM 結合レビュー（境界IF・命名・未接続）継続（3層の第2層）、③ DEFERRED の最終一括報告＋矛盾検出結果、④ **メトリクス収集の実装**（F12 のギャップ充填。experimental.md 定義済みメトリクスを台帳＋jsonl から機械集計）、⑤ retrospector 起動（`PROJECT_MEMORY_DIR` 付与・ループ系 param は `N/A` 明示=前回 C5 最小案継承）。

#### §7. hooks / settings.json 仕様（M2 インフラ・共通層）

**新規** `.claude/lib/subagent-verify-hook.sh`（`lib/` 配置＝link.sh の symlink 対象→ **`cd -P` 必須**、CLAUDE.md 編集注意遵守）＋ settings.json に `SubagentStop` エントリ。

- **Stage A（log-only・先行導入）**: `agent_transcript_path` を jq 解析し tool_use 数・duration を算出、`subagent-metrics.jsonl` に `{ts, agent_id, agent_type, tool_uses, duration_s}` 追記のみ。判定しない。fail-open（jq 不在/transcript 不読→exit 0）・`~/.claude/logs/` にデバッグ退避（F13 既存パターン踏襲）
- **Stage B（block モード・JSONL 実構造検証後に昇格）**: 役割別 floor と突合、違反時のみ `{"decision":"block","reason":"tool_uses=0 で完了主張。実際にツールで作業せよ…"}` を返してサブ本人に再指示（親 context 到達前に足止め）。`stop_hook_active` の one-shot guard で 1詰まり1回に制限（parse-failure-continue-hook loop guard 先例＝ブラインドリトライ禁止整合）
- **floor 表（初期値・G2 較正）**:

| agent_type（matcher） | floor | 根拠 |
|---|---|---|
| explorer | tool_uses ≥ 2（うち Read/Glob/Grep ≥1） | 調査ゼロで探索レポートは書けない（事象Y直撃） |
| implementer | Edit/Write ≥ 1（NO_OP_JUSTIFIED 免除） | 編集ゼロの完了主張＝phantom |
| tester | Bash ≥ 1 | 実行ゼロの検証は成立しない |
| reviewer | Read ≥ 1 | コードを読まないレビュー禁止 |
| general-purpose（L1）・未登録型 | floor なし（logging のみ） | 推論系の正常0を誤検知しない（安全弁） |

- **A経路（PostToolUse matcher=Agent）**: フォアグラウンド時に `totalToolUseCount` 等をクロスチェックとして同 jsonl 追記する**任意補完**。グローバル同期化 env は設定しない（codex background 要件と衝突）

#### §8. 観測性 — 台帳スキーマと OTel

**epic-runs.md（M3/M9 統合台帳・単一 SSOT）**: 人間可読かつ grep 可能な「1イベント1行・固定カラム」（jsonl 併走させない=二重管理回避）:

```
| 2026-07-03T19:30:12 | NODE_START  | T2 | head=abc1234 pre_dirty=3 |
| 2026-07-03T19:48:02 | NODE_RETURN | T2 | status=COMPLETED verdicts=review:PASS,test:PASS loops=1/1/0 |
| 2026-07-03T19:48:05 | VERIFY      | T2 | PASS claimed=4 delta=4 |
```

イベント語彙: `EPIC_START / RESUME_RECONSTRUCTED / PLAN_DONE / GATE_APPROVED / NODE_START / NODE_RETURN / VERIFY / NODE_DONE / NODE_FAILED / NODE_ABORTED / DECISION / DEFER / FALLBACK_INLINE / PHASE3_START / INTEGRATION / EPIC_END`。**フリーズ外形診断手順**（references 文書化）: 台帳の最終 NODE_START からの経過＋当該サブ RUN_DIR の next-steps.md mtime を見て2分で「どのノードのどの phase で止まったか」まで絞る（19分迷走の再演防止。自動 kill 不可の限界も併記）。**OTel（任意層）**: `CLAUDE_CODE_ENABLE_TELEMETRY=1`＋`CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1` で `agent_id`/`parent_agent_id` span（F11）。**台帳が SSOT・OTel は補完**（どの M も OTel に依存させない）。採用具体化時は tech-validator 委譲。

---

### 主要な論拠

- **claims-up ＋ evidence-local-pull（対立#3 の第三解の背骨）** (D-01 第一原理レンズ / P2): L0/L1/L2 は同一 working tree を共有するため L2 のファイル操作は L0 から `git diff --name-only` 一発で直接観測できる。前回対立#3 の「L0 は L2 の操作を直接見られない」は**ファイル副作用に関する限り誤った前提**だった。上に運ぶのは軽量 claim（ファイル名・カウンタ・VERDICT）だけ、証拠は各境界の検証者が git から O(1) で引く＝ context を証拠が一切上らない。summary-up vs evidence-up の対立を構造的に解消。
- **Option B 恒久＋A-lite 降格（対立#1）** (D-01 機序レンズ / F2): Option A のコストは N 比例の構造コスト（pir2 約23ステップ×N・最大5ブロッキングゲート×N・6ループカウンタ×N を L0 単一 context で並行管理）。決定打は機序 — 恐れている失敗クラス（捏造）は「context 圧・resume 真空→穴埋め」で起きる（事象X 機序）。A は L0 の context 圧を構造的に増大＝**守ろうとしている失敗の発生確率を上げる向きの設計**。D-03 の A 寄り論拠「脆弱な L1 の上に信頼性を積むと不信頼性を継承する」への応答: 本設計は L1 の上に積まず L1 の**外側**（L0 境界）に L1 が偽装できない git 検証を置く（継承論は L0 が L1 の self-report を信頼する場合のみ成立し、本設計はそれを禁止）。
- **二重の決定論検証は冗長でない** (D-01 設計統合レンズ / F3/F7): 各境界に別の信頼できない語り手がいる（L0 境界の語り手は L1 自身）。git 集合照合は hook も LLM も不要の純 bash で完全可能（F3）。shard/sequential actor には既に統合確認の決定論チェック先例がある（F7）ため 6-3 は新規発明でなく既存先例の一般化。
- **可逆性による破壊操作の二分（M7 の解）** (D-01 二次波及レンズ / F9): F9 の破壊ゲート格下げは「L1 はユーザーと対話できない」制約由来。ブロッキング一時停止は不可だが「完了させず制御を L0 に返す」は可能（pir2 EXPLORATION_NEEDED と同型）。可逆性は恣意性のない客観境界で、誤 ABORT の頻度を「計画時に予見できなかった不可逆操作」だけに構造的に限定できる。
- **設計の厚さ≠構築の厚さ（YAGNI への応答）** (D-01 反証レンズ / §12): end-state の大半は構築物でなく決定トリガの宣言。今すぐ作るのは W0〜W3 のみで、重い物は全て観測ゲート G1/G2 の背後。W0〜W3 は**ハッピーパスにブロッキングゲートを1つも足さない**（検証は不一致時のみ作用・台帳は非ブロック・直列既定はゲート数を減らす向き）。検証ゲートは完走確率を下げるのでなく**沈黙の破損を可視の失敗に変換する**＝実験の目的が観測である以上、失敗率でなく検出率の増加。

---

### 統合の過程（採否）

- **採用した骨格**: fable-solo の 4レンズ内省が既に「実行順に追える1本のフロー」に到達しているため、§0〜§8 の設計本体をフェーズ粒度のまま position 本体に転記（要約に潰さない）。5段推論（段1 claims-up 原則 → 段2 対立#1 → 段3 対立#2/#3/#4 → 段4 M7 → 段5 統合）の決着ロジックを「主要な論拠」に保持。
- **退けた/留保した論点**:
  - `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` によるグローバル強制同期は**不採用**（env がセッション全域に効き、CLAUDE.md「codex MCP 相談は background Agent 経由必須」を破壊するクロス SSOT 違反）。よって M2 主経路は SubagentStop（B経路・実行モード非依存）とし、PostToolUse メトリクス（A経路）はフォアグラウンド時の補完クロスチェックに格下げ。ただし「env の codex 波及」は**強い推論だが実機未確認**（残課題に保持）。
  - fan-in merge の実装は**作らない**（需要が出るまで=YAGNI。予約実装を dead code として温存しない）。fan-in が必要な分割は `USER_DECISION_REQUIRED`。
  - 内容ハッシュ突合（既 dirty ファイルへの虚偽申告検出）は較正フェーズの拡張候補として今は入れない。
- **前回からの変化**: ROUND 1 のため `PRIOR_POSITION_PATH` なし。ただし前回 deepthink position（`20260703-175327-deepthink`）に対する上積みが明示されており、統合として引き継ぐ — 前回の「時間軸付き両論（試験=B、恒久時に A 再評価）」を**「B が恒久・A は per-node A-lite 降格。A のコストは N 比例ゆえ恒久・大規模ほど A 不利」へ更新（前回の直感と逆）**。前回未提出だった「フェーズ単位仕様・対立決着・実装可能性評価・移行パス」の4点を今回の探索3本（exp-01/02/03）の確定事実 F1–F13 で充填。

---

### 未解決の対立 / 設計上の未決（潰さない）

> 前回の4対立は本 deliberation で**決着（または客観的決定トリガ付き）** に至った（§9 決着表）。今回 deliberator が1本のためレンズ間の食い違いはないが、**決着が前提に依存する箇所・未検証で設計が依存する点**を「潰さない未決」として明示する。

| # | 未決の論点 | 現状の立場 | 決着に何が要るか（決定トリガ / 較正ゲート） |
|---|---|---|---|
| U1 | **L1 が SKILL.md 全文を自律オーケストレーションできるか（P5・対立#1 の可変部）** | B 恒久を暫定採用（未実証） | **G1 dry-run**: L1 return に M1 契約の必須見出しが揃うか。起動プロンプト修正を1回挟んで**連続2回契約不履行なら「L1 自律不能」と判定し A-lite 常用化をユーザー上程**（無言切替禁止）。「恒久」は「トリガが発火しない限り」の条件付き |
| U2 | **transcript JSONL の実構造（hook Stage B の jq 式が書けるか）** | 未検証。C経路（git 照合・hook 非依存）で最低限は成立させる設計 | **W3** に「`~/.claude/projects/<sanitized>/*/subagents/*.jsonl` を1件 jq で確認」を検証ステップとして内蔵。確認できれば Stage B へ昇格（W4） |
| U3 | **Agent ネスト起動の同期/非同期実挙動＋ハートビート観測可能性** | バックグラウンド既定（2.1.199）を前提に非ブロック設計。ハートビート mtime 観測は未実証 | **G1** の観測対象（②Agent 同期/非同期の実挙動、⑤バックグラウンド起動時ハートビート mtime）。机上では埋まらない |
| U3' | **`CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` の作用範囲（サブ種別ごとか全域か）** | 「全域＝codex 破壊」を根拠に不採用 | 不採用判断の根拠を確定させたい場合のみ要確認（現設計は不採用のため優先度低。強い推論だが実機未確認） |
| U4 | **事象X（捏造）が epic の L1 ネスト内でも再発するか** | 前回から持ち越し。計器（6-3・3-2 検証）が捕捉する前提 | **G1/G2** でのみ観測可能。計器なしの1回は診断不能で学びゼロ（19分迷走の実証）＝観測に数えられない |
| U5 | **契約のプロンプト強制の限界（L1 が HANDOFF_PATH 上書き等をどこまで忠実に守るか）** | プロンプト強制のみ（Agent return に strict schema 保証なし=exp-03 #4 不可）。欠落時 artifact 再構成が保険 | 恒久的な残存限界。next-steps-queue の checkbox に検証ステップを含めて手順飛ばしを観測可能化するのが現状の上限 |

**内蔵された反証トリガ / 較正ゲート（設計の自己修正機構）**:
- **G1（1-unit epic dry-run, executions 0→1）**: 観測 ①L1 契約遵守（対立#1 トリガ評価）②Agent 同期/非同期 ③hook データ妥当性 ④HANDOFF 上書き遵守。
- **G2（実タスク線形 epic 2-3ノード・additive-only）**: cap/floor 較正・experimental.md メトリクス収集・完走確率とゲート発火率の実測。
- **非対称検証設計（反論3 への応答）**: PHANTOM_CLAIM（捏造シグネチャ）だけ hard fail、UNDECLARED_CHANGE は warn＋他ノード宣言集合との交差時のみブロック（formatter/lockfile 副作用での偽陽性が実験を殺すのを防ぐ）。
- **epic 不要説（対立仮説）**: executions 0 では棄却できない。G1/G2 は「epic が手動 N 回に対して優位か」を測る実験そのもの。epic 廃止判断が出ても **W1（pir2 6-3）と hook は素の pir2 の資産として残る**（投資の大半が epic 不採用時にも回収可能な配置）。

---

### rubric カバレッジ（自己申告）

> gate が一項目ずつ客観照合する前提で、**盛らずに**申告する。本 deliberation は out-of-scope が「実コード実装」であり、成果物は blueprint（設計仕様）まで。よって「充足」は「設計仕様・決着・アンカー・限界の明示が揃っている」を意味し、「実装が動作実証済み」は意味しない（実証は移行パス W/G に内蔵）。

| # | rubric 基準 | 充足 / 部分 / 未達 | 根拠（position のどこが答えているか） |
|---|---|---|---|
| 1 | 完成形フローのフェーズ単位仕様が端から端まで存在 | **充足** | 設計本体 §0（アーキ・信頼モデル）§1（境界契約=起動/return/検証パイプライン/6-3）§2 Phase 0 §3 Phase 1 §4 Phase 1.5 §5 Phase 2（2a–2f を実行順）§6 Phase 3 §7 hook §8 台帳。各フェーズに責務・L0↔L1↔L2 で何を return/検証するか・統合される信頼性機構を記述。改善リストでなく実行順に追える1本のフロー。**正直な留保**: Phase 0 の実挿入行は exp-01 未確定（実装時 Read で足りる）だが仕様内容自体は完備 |
| 2 | 前回4対立に決着（または決定トリガ） | **充足** | §9 決着表＋「主要な論拠」: #1 B 恒久＋反証トリガ（G1 連続2回不履行→上程）/ #2 直列既定＋opt-in 5条件 AND / #3 claims-up＋evidence-local-pull（第三の解で解消）/ #4 台帳ベース部分 resume＋ユーザーゲート、決定論リプレイ・自動 timeout kill は仕様外宣言。両論併記のまま放置なし。#1 は条件付き恒久であることを U1 に明示 |
| 3 | 実在 SSOT アンカー＋鍵機構の実現可能性を根拠で評価 | **充足** | §10 相当のアンカー（本 position 各節に着地点名指し: epic SKILL.md 3-0/3-2/3-5・pir2 6-1→7 間の 6-3・`l1-contract.md` 新規・`epic-planner.md`・`implementation-delegation.md` 相互参照・`.claude/lib/subagent-verify-hook.sh`＋settings.json SubagentStop）＋新規/継承/再利用判定。実現可能性: テレメトリ return=可能（F1）/ git-diff 検証=完全に可能・純 bash（F3）/ hook agent メタデータ=条件付き（B経路 F4 JSONL未検証・A経路 F5 フォアグラウンド限定）。仮定でなく F1–F13 出典で評価。**正直な留保**: hook B経路は「条件付き」評価＝実証はW3/W4に内蔵 |
| 4 | 段階的移行パス（現 epic→完成形）が依存順 | **充足** | §11 相当: W0（citation/文書衛生）→W1（pir2 6-3・最初に作る・最高レバレッジ）→W2（epic 境界契約一式）→W3（hook Stage A＋JSONL確認）→**G1 dry-run**→W4（hook Stage B）→**G2 実タスク**→W5（end-state 解禁群）。前回 instrumentation-now（W0–W3）と end-state（W4–W5）を1本のロードマップに接続。「まず W1」を明示 |
| 5 | 「完璧」が正直に境界づけ | **充足** | §12 相当: 最強 YAGNI 反論を steelman（「executions 0 の機構に完成形設計は机上の失敗モード列挙の再演では」）＋3点応答（設計≠構築の厚さ/ハッピーパスに新ブロッキングゲートなし/計器なしの1回は観測無価値）。**除去できない残存限界6件**を明示: ①#44783 級ハングは親内から検知不能・自動 kill 不可 ②durable resume/Saga 自動補償/ブロッキング HITL は構造的に不可 ③決定論は行為の捏造まで（結論の捏造は LLM/人間層の責務）④集合算術の盲点（既 dirty への虚偽申告は name-only で検出不能）⑤契約はプロンプト強制で strict schema 保証なし ⑥hook は fail-open＝事故の計器であり攻撃への防御でない |
| 6 | 主要トレードオフが具体＋選択と理由（最低3件） | **充足** | 6件（要件3を超過）: ①context 隔離(B) vs 制御純度(A)→B ②フォアグラウンド決定論 vs バックグラウンド耐性→B経路主経路・全域同期 env 不採用 ③直列の診断明瞭性 vs 並列 wall-clock→直列既定 ④ゲート忠実度 vs 自律性→可逆性で二分 ⑤検証二重化 vs 単一点→二重化 ⑥ファイル台帳 vs OTel→台帳 SSOT・OTel 任意補完。各々「採った側＋なぜ」 |
| 7 | CLAUDE.md ルール整合 | **充足** | 6規定を個別照合: 制御責務の所在→**意図的 carve-out として明示（M6・条件文つき）**（L1 制御責務は再帰オーケストレーション、成立条件=境界計器の稼働。ループカウンタはスコープ単位 SSOT で cross-subtask 汚染が構造的に不可能）/ ツール結果捏造禁止→本設計は**その機構化そのもの**、設計自体の限界も捏造せず明示 / ブラインドリトライ禁止→検証 FAIL 再実行1回＋原因逐語注入・2回目は必ずユーザー / 探索委譲→L0 検証は既知パスへの git/`test -f` のみ＝広域探索でなく決定論チェック / dead code 温存禁止→3-5 旧記述は置換・fan-in は需要まで作らない / git restore→補償は diff 全 hunk 提示＋ユーザー判断のみ・自動 restore なし |
| 8 | 前回成果へのトレーサビリティ＋無矛盾（回帰しない） | **充足** | 下記「M1–M12 トレーサビリティ表」で全12項目の着地を明示（silently drop なし）。C1–C4 非再導入を自己点検: C1=inline フォールバックを A-lite として実仕様化（未定義語のまま使わない）/ C2=実験名は pir2-explorer-nesting 表記のみ / C3=epic の運用実績を一切主張せず executions 0 明記 / C4=run-dir 命名は `run-dir-base.md` SSOT・`cut -c1-40` |

---

### M1–M12 トレーサビリティ表（silently drop 確認）

| M | 【今直す必須】内容 | 本設計での着地 | drop? |
|---|---|---|---|
| M1 | L1 境界テレメトリ return | §1-2 return 契約（3-0 置換・`l1-contract.md`）。freeze 非対応の正直なスコープ明示つき | なし |
| M2 | L0 決定論 git 突合＋役割別 tool_use floor | §1-3 L0 検証パイプライン＋§1-4 pir2 6-3＋§7 hook（C経路必須・B経路条件付き・A経路補完） | なし |
| M3 | epic-runs.md に Phase+timestamp | §8 イベント台帳（3-5 置換）。粒度の限界（L0 が書けるのは境界2点、内部 phase は M1 の事後報告）を明示 | なし |
| M4 | ループ・サブタスク数 hard-cap | §3-①（サブタスク cap ≤5 仮置き）＋§5（ノード再実行1回・全体 replan 上限）。値は G2 較正 | なし |
| M5 | 並列 fan-out の #44783 緩和 | §段3 対立#2 決着（直列既定・5条件 opt-in・Bash 制約は幅≤2＋書込非交差＋ハートビートで代替） | なし |
| M6 | L1 制御責務 vs CLAUDE.md の解消/正当化 | §14 carve-out（条件文つき正当化を CLAUDE.md epic 節＋experimental.md に明記） | なし |
| M7 | 破壊的変更の事前ゲート＋timeout-block | §段4 選択的早期 return＋§3-④/§4-① 事前分類・事前承認（5.7 格下げ=F9 の解消） | なし |
| M8 | citation 是正 C1–C7 | W0（C1=A-lite 実定義・C2・C3・C4）。本 position 自体が C1–C4 を非再導入 | なし |
| M9 | resume 台帳 | §2-2 resume 再構成（台帳＋git・人間ゲート）＋§1-1-③ HANDOFF 隔離＋§8 台帳 | なし |
| M10 | DAG fan-in 対応 | §3-②tree/線形制約＋fan-in は `USER_DECISION_REQUIRED`（merge は W5 で需要駆動） | なし |
| M11 | 共有ステート競合の保守直列化 | §3-③書込集合宣言＋直列化。fan-out 解禁後は §5-2f の帰属規則がランタイム検知を兼ねる | なし |
| M12 | サブ失敗回復パス | §1-3 手順5 STATUS 不変条件＋§5 失敗パス（半完成ノードの明示状態・下流ブロック） | なし |

> **silently drop: 0 件。** M1–M12 全項目が設計要素に対応づけられ、各々に「正直なスコープ限界」（M1 の freeze 非対応・M3 の粒度限界・M4 の値較正未了等）が併記されている。

---

### 確信度・前提・残課題

- **全体の確信度: 中〜高** —
  - **高**: C経路（git 集合照合）の実現可能性と設計（F3 直結・純 bash）。挿入点アンカー（exp-01 実ファイル確定、3-0 以降）。対立#3 の解消論理（P2＝同一 working tree 共有は環境の構造的事実）。残存限界の列挙（F11 直結）。
  - **中**: 対立#1「B 恒久」判断（P5 未実証だが反証トリガ内蔵で判断自体は頑健）。hook B経路（JSONL 構造未検証）。対立#2 の5条件の妥当性（ハートビート観測未実証）。floor/cap 初期値（全て仮置き）。
  - **低**: バックグラウンド起動時代の並列 fan-out 実挙動（G1/W5 でしか埋まらない）。
- **依存している前提（崩れると結論が変わる）**:
  - **P2（全層が同一 working tree 共有）**: 崩れると git を共有 ground truth とする M2 集合算術が再設計になる（worktree 分離を W5 でも既定にしない理由）。
  - **P1（サブの完了報告は claim であって ground truth でない）**: 本設計の認識論的前提。
  - **P5（L1 が SKILL.md 全文を自律オーケストレーション可能）**: 未実証。U1 で G1 に反証条件として接続。
  - **P3（初回題材を運用者が線形・additive-only 寄りに選べる）／P4（対話セッション実行・無人運転は対象外）**。
  - 境界: 非 git プロジェクト／git 外副作用（DB・外部 API）主のタスクでは C経路が空洞化し ARTIFACTS 検証と floor だけ残る＝epic の題材選定制約として明記すべき。
- **残る不確実性 / 未解決**: U1–U5（上表）。特に (a) transcript JSONL 実構造（W3 内蔵）、(b) Agent 同期/非同期＋ハートビート観測（G1 内蔵）、(c) 事象X が L1 ネスト内で再発するか（G1/G2 でのみ観測）。いずれも**机上でこれ以上埋まらず、移行パスの観測ゲートに内蔵済み**。
- **追加探索が要る論点（deliberator 集約・いずれも移行パスに内蔵）**:
  1. transcript JSONL の実構造 — `~/.claude/projects/<sanitized>/*/subagents/*.jsonl` を1件 jq で確認（W3 前提。確認できれば hook Stage B の jq 式が書ける）
  2. Agent ネスト起動の同期/非同期実挙動＋ハートビート観測可能性 — G1 dry-run で観測（机上では埋まらない）
  3. `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` の作用範囲 — 不採用判断の根拠確定用（現設計は不採用のため優先度低）
  4. epic SKILL.md の Phase 0 相当（初期化ステップ）の実記述 — exp-01 は 3-0 以降のみ確定、§2 挿入位置は実装時 Read で足りる（explorer 再起動までは不要）
