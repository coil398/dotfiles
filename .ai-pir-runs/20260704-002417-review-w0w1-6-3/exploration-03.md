# 探索レポート: 6-3（決定論的完了検証）の全 run 必須ゲート化 — システミックな影響と外部ベストプラクティス評価

## 関連ファイル一覧

| ファイルパス | 役割・内容 | 変更の必要性 |
|---|---|---|
| `.claude/skills/pir2/references/deterministic-completion-check.md`（279行・未コミット/untracked） | 6-3 の共通プロトコル本体。pre-set/post-set/CLAIMED抽出/PHANTOM・UNDECLARED判定/NO_OP免除/失敗パスを定義 | 参照のみ（本タスクは調査） |
| `.claude/skills/pir2/references/verify-deterministic-check.sh`（385行・未コミット/untracked） | 上記 reference 内の bash ブロックを抽出して構文検証＋6シナリオの scratch-repo E2E テストを行う dev-time 自己検証スクリプト。**SKILL.md のランタイム経路からは一切参照されず**、手動実行前提 | 参照のみ |
| `.claude/skills/pir2/SKILL.md`（M・279行の一部を占める6-1〜6-3節） | /pir2 本体。6-1「pre-set 記録」・6-3「決定論的完了検証」をワークフロー必須ステップとして配線 | 参照のみ |
| `.claude/skills/pir2codex/SKILL.md`（M） | /pir2codex 本体。6-1 wrapper 起動前後に pre-set/6-3 を配線。全 actor（`main` なし）に常時適用 | 参照のみ |
| `.claude/agents/implementer.md`（M・90-107行「実装完了レポートのフォーマット」） | CLAIMED の一次情報源となる `### 変更ファイル一覧` の markdown 記法を規定。`git add`/ステージング禁止の明示的記述は**存在しない**（grep 0件） | 参照のみ |
| `.claude/skills/pir2/references/experimental.md`（M） | 実験追跡レジストリ。`pir2-implementer-shards-and-review-fix-shards` / `pir2-implementer-sequential-units` / `pir2-explorer-nesting` / `epic-orchestrator-nested-pir2` の4件が Status/Adoption/Rejection criteria付きで追跡されている一方、**6-3 に該当するエントリは存在しない**（全文検索で確認） | 参照のみ |
| `.claude/skills/pir2/references/sanitized-cwd.md`（118行）/`verify-sanitized-cwd.sh`（76行） | 同型と自称される既存先例。分量比較の基準として参照 | 参照のみ |
| `docs/deepthink/20260703-190750-Fable5.md` | `/epic` 完成形設計の熟考レポート（Fable5）。6-3 は「W1（最初に作る・最高レバレッジ）」として本レポートの結論から直接導出された。残存限界①〜⑥・trust モデル（claims-up + evidence-local-pull）の設計原典 | 参照のみ |
| `.ai-pir-runs/20260703-201858-pir2-step-6-3-deterministic-verify/{plan,user-decisions,review-01〜04-*,refactor-proposals,implementation-01〜05,verify-*}.md` | 6-3 を実装した実際の /pir2 run の全成果物。決定1〜3（配線点・pir2codex統合・NO_OP実現）、reviewer 4ラウンドの指摘・修正履歴、refactor-advisor の8提案 | 参照のみ |

> **構造投資領域**: 該当なし（本タスクは新規コード追加ではなく既存ゲート設計の系統的レビュー調査のため、3個以上並ぶクラスファミリー探索は対象外）。

## 既存パターン・規約

- 決定論的検証は「reference.md（プロトコル定義） + verify-*.sh（dev-time 自己検証）」という**2ファイル1組パターン**を踏襲（`sanitized-cwd.md`/`verify-sanitized-cwd.sh` が先例）。ただし verify-*.sh はいずれも**ランタイムのフックや CI に配線されておらず**、`.githooks/pre-commit` と `.claude/settings.json` の hooks を grep しても一致 0 件（後述）。
- 実験的機能は通常 `experimental.md` に `Status: Active` + Hypothesis/Implementation/Quality Guardrails/Metrics/Adoption Criteria/Rejection Criteria/Evidence Summary の定型フォーマットで追跡され、retrospector が毎 run 観測する運用が確立している（shards・sequential・explorer-nesting・epic の4件で一貫）。**6-3 はこの運用の外側**に置かれ、SKILL.md 上は「必須ステップ」として最初から確定的に配線されている。
- ユーザー確認ゲート（Auto mode でも必須）は「仕様変更判断」を要する箇所に限定配置される規約（destructive-change-check・plan-choice-gate・continuation-gate 等と同型）。6-3 の失敗パスもこの規約に沿い、2回目 PHANTOM でユーザーゲートを開く設計になっている。

## 影響範囲

- **直接影響**: `IMPLEMENTATION_ACTOR` が `main` 以外（`implementer-subagent`/`implementer-shards`/`implementer-sequential` および pir2codex の全 actor）となる**全ての /pir2・/pir2codex run**。epic 経由か単体起動かを問わない全域適用。
- **間接影響**: reviewer 起動（ステップ7）の可否がこのゲートの通過に依存するため、実装〜レビューのリードタイム全体に影響。再実装ループ（7-4 review-fix・8-2 test-fix）は明示的にスコープ外（決定1=(A)）だが、次節で述べる理由からこの境界設計自体がシステミックな論点になる。

## 依存関係

- **インポート関係**: 6-3 は `implementer.md`「実装完了レポートのフォーマット」の markdown 記法（` - \`path\` — 概要` 形式・`NO_OP_JUSTIFIED:` マーカー）に一方向依存。フォーマットが変われば `grep -E '^- *\`'` / `sed -E` 抽出が無警告で壊れる可能性がある。
- **被参照関係**: `pir2/SKILL.md` 6-3 節・`pir2codex/SKILL.md` 6-1 節から `deterministic-completion-check.md` を共通 reference として参照（DRY設計、2026-07-03 決定2(B)で意図的に統合）。

---

## ローカル観点分析（負荷・リスク・コスト＋具体シナリオ）

### 観点1: 通常 run（捏造なし）への負荷

| 項目 | 内容 |
|---|---|
| **実行コストそのもの** | `git diff --name-only` × 2 + `git ls-files --others` × 2 + `check-ignore` ループ + `test -f` ループ。いずれも軽量・O(ファイル数)。**性能負荷は無視できる**。 |
| **オーケストレーション負荷（本質的コスト）** | reference 内の bash は3ブロック計 **124行**（pre-set 10行・post-set/CLAIMED抽出/判定 98行・NO_OP 16行）で、`awk` の状態機械によるフェンス除去・`case`/`esac` による3分岐・`while read` ループを含む非自明な POSIX shell。**この bash を呼び出す単一の実行可能スクリプトはランタイム経路に存在しない**（`verify-deterministic-check.sh` は reference 自身の comment で「編集したら実行すること」という dev-time 専用ツールと明記されており、SKILL.md のどのステップからも参照されていない。`grep -rn "verify-deterministic-check.sh" .claude/skills/` で reference 内の1箇所のみヒット）。したがって実運用では**オーケストレータ（メイン Claude）自身が reference の markdown を Read し、bash ブロックを都度コピー・変数代入して Bash ツールで実行する**という手作業に頼っている。ここでの転記ミス（フラグの脱落・変数名の取り違え等）は verify レポート自体を汚染しうるが、それを検知する機構はない（verify レポートもオーケストレータ自身が書く自己申告）。 |
| **手順の逐次性への依存** | pre-set は「implementer 起動の**前**」に必ず記録される前提。SKILL.md はこれを別見出し（pir2codex）またはインラインの blockquote（pir2、意図的に非対称。refactor-advisor が Low 指摘済み・`.ai-pir-runs/20260703-201858-.../refactor-proposals.md` L-4）で指示するのみで、**同一 function_calls ブロックに pre-set の Bash 呼び出しと implementer の Agent 起動を並べてしまう手順ミス**を構造的に防ぐ機構はない。pre-set 記録漏れ自体は post-set 側の「手順0」ガード（`[ -f pre.list ] || echo ERROR`）で fail-loud 検知されるが、**pre-set と実装が競合実行された場合**（記録漏れではなく、記録タイミングが遅れて implementer の初期編集を巻き込む場合）は検知できない（delta が不当に縮小し、その分だけ UNDECLARED_CHANGE の検出力が静かに落ちる）。 |
| **新規に増える状態変数・慣習例外** | `PRE_IMPL_INDEX`（`IMPL_INDEX` とは別に据え置く必要がある値）、`PHANTOM_RETRY_COUNT`。next-steps.md では「6-3 は独立した checkbox を持つ（既存の『hyphen番号は親ステップとcheckboxを共有する』という慣習からの意図的な例外）」と SKILL.md 自身が明記しており、**確立済みの命名規約に対する例外が1つ増えている**（将来の他ステップ追加時に「これも例外か？」を都度判断させるコスト）。 |
| **govern性の一貫性の欠如（重要）** | `experimental.md` を全文検索したが、6-3（`deterministic-completion-check`）に対応する `Status: Active` エントリは**存在しない**。同日（2026-07-03）に設計・着手された `epic-orchestrator-nested-pir2` は Hypothesis/Adoption Criteria/Rejection Criteria/Evidence Summary が定義され retrospector 観測対象になっているのに対し、6-3 は **全 run 必須のハードフェイルゲートとして経験的検証なしに一発本採用**されている。しかも Fable5.md 自身が「W1（pir2 6-3）は epic 不採用でも素の pir2 の資産として残る」と明記しており、**epic の実験的位置づけとは独立に、素の /pir2・/pir2codex という最も利用頻度の高い経路に無条件で恒久機能として編入された**ことになる。これは「新規性・リスクの割に実験トラック外」という統治上の非対称であり、既存の「実験は Active として追跡し、3回以上の実行蓄積後にユーザー判断で恒久化する」という確立済みプロセス（shards/sequential/nesting/epic の4件が例外なく踏んでいる）からの逸脱である。 |
| **複雑性の増大率（先例比較）** | `deterministic-completion-check.md`（279行）は「同型」と称する `sanitized-cwd.md`（118行）の**約2.4倍**、`verify-deterministic-check.sh`（385行）は `verify-sanitized-cwd.sh`（76行）の**約5倍**。位置づけの説明（「同型」）に反して実際の保守面積は大きく拡大している。 |

### 観点2: 偽陽性リスクの実運用頻度（実機検証済み）

以下はすべて scratch git repo（`mktemp -d` 相当、プロジェクト実ファイルは一切変更していない）で実際に `git` コマンドを実行して確認した事実であり、推測ではない。

#### (a) 既 dirty ファイルへの申告 — 「稀な境界」ではなく「この repo の現在のデフォルト状態」

設計側もこれを既知の残存限界（Fable5.md「残存限界④」、`review-02-architecture.md`「実在する gitignore 対象/リポ外ファイルを『編集した』と虚偽申告するが実際には何も変更していない」）として認識・受容している。しかし「実運用頻度」の観点で見ると、**この会話の開始時点の `git status` で当該 dotfiles リポは以下の状態**である:

```
M .claude/agents/implementer.md
M .claude/settings.json
M .claude/skills/deepthink/SKILL.md
M .claude/skills/pir2/SKILL.md
M .claude/skills/pir2/references/experimental.md
M .claude/skills/pir2/references/implementation-delegation.md
M .claude/skills/pir2/references/next-steps-queue.md
M .claude/skills/pir2/references/sanitized-cwd.md
M .claude/skills/pir2/references/verify-sanitized-cwd.sh
M .claude/skills/pir2codex/SKILL.md
M .gitignore
M CLAUDE.md
?? .claude/agents/epic-planner.md
?? .claude/skills/epic/
?? .claude/skills/pir2/references/deterministic-completion-check.md
?? .claude/skills/pir2/references/verify-deterministic-check.sh
```

この状態で次に /pir2 を回し、上記いずれかのファイル（例: `CLAUDE.md` や `pir2/SKILL.md`）に対する変更を implementer が申告した場合、その申告の真偽は 6-3 では検証できない（pre.list に既に含まれるファイルは、実際に触れたかどうかに関わらず post.list にも residual に残り続けるため、PHANTOM 判定を無条件に素通りする）。つまり **6-3 の実効検証範囲は「セッション開始時点でクリーンだったファイル」に限定され、この repo の実際の運用パターン（頻繁な並行編集・未コミット WIP の常態化）においては検証対象外領域が常時・相当割合存在する**。これは design が既に受容済みの限界だが、「頻度」でいえば例外ではなく常態に近い。

#### (b) ステージ済み変更の完全な不可視化（新規発見・実機検証）

`deterministic-completion-check.md:33` は「staged 集合は対象外（implementer / Codex はステージング操作をしない前提。設計 SSOT §1-3-2 準拠）」と明記する。この前提の実際の裏付けを実装当時の `plan.md:170` で確認したところ、リスク開示は「**Codex（apply_patch）は通常 stage しないため実害はない**」という **pir2codex 側の Codex actor だけを根拠**にしており、**Claude implementer サブエージェント側の挙動は一度も検証されていない**。`implementer.md` を grep したが `git add` の禁止・ステージング操作の禁止を明示する記述は **0件**であり、implementer は Bash ツールをフル権限で保持する。

scratch repo で実際に検証した結果:

```bash
git mv old.txt new.txt && git add -A
git diff --name-only                       # → 空
git ls-files --others --exclude-standard   # → 空
git diff --cached --name-only              # → new.txt （ここでしか見えない）
```

つまり、implementer が `git add` を一度でも実行すれば（習慣的なコミット前整理、または対象プロジェクトの lint-staged/pre-commit フォーマッタが自動ステージする設定がある場合等）、その変更は 6-3 にとって**完全に存在しないもの**として扱われる。CLAIMED として申告されたファイルは post.list に一切現れないため、**正当な実装が PHANTOM_CLAIM としてハードフェイルする**。しかも再実行しても同じ理由（ステージング）で再度失敗しうるため、2回目の PHANTOM でユーザーエスカレーションに達する現実的な経路がある。

#### (c) 大文字小文字のみのリネームが macOS(APFS 既定) で完全に無音化する（新規発見・実機検証）

環境情報（`Platform: darwin`）を踏まえ、macOS のデフォルトファイルシステム APFS（case-insensitive・case-preserving）上で検証した:

```bash
# Foo.txt を commit 済みの状態から
mv Foo.txt foo.txt
git diff --name-only                       # → 空
git ls-files --others --exclude-standard   # → 空
git status --porcelain                     # → 空
git ls-files                               # → Foo.txt のまま（追跡名は不変）
```

**すべてのシグナルが空**になる。つまり implementer が「命名規約に合わせて大文字小文字だけ直す」リネームを行っても、git 側には一切の痕跡が残らない。この状態で implementer がそのファイルを CLAIMED に含めれば post.list に存在せず、PHANTOM_CLAIM のハードフェイルになる。この failure mode は Fable5.md の残存限界一覧にも、実装当時の review-01〜04（4ラウンド・Medium/Low 計 10件超の指摘履歴）のどこにも一度も言及がない（grep で "staged"/"ステージ"/"大文字小文字"/"case-insensitive"/"APFS" の一致 0件、review-04 の submodule 指摘のみヒット）。**macOS がこのワークフローの主要な実行環境である**ことを踏まえると、(b)(c) はいずれも「稀な境界ケース」というより「この開発環境で高確度に踏まれうる未文書化の盲点」である。

#### 参考: 正しく機能することを確認済みのケース（フェアネスのため明記）

同じ実機検証で、以下は**正しく動作すること**も確認した:

- **ステージしない通常のリネーム**（`mv old new` のみ、`git add` なし）: `git diff --name-only` に `old`（削除扱い）、`git ls-files --others` に `new`（未追跡）が正しく現れ、両者の組み合わせで delta に反映される（`comm` 系の判定は正常に機能する）。
- **mode のみの変更**（`chmod +x`、内容変更なし）: `git diff --name-only` が正しく検知する。
- **単純な削除**: `git diff --name-only` が正しく検知する。

したがって「git diff をオラクルにすること」自体が壊れているわけではなく、**staged 化と case-only rename という2つの特定の盲点に限定される**、という評価が正確である。

### 観点3: 複雑性・保守コスト

- **フォーマット結合**: CLAIMED 抽出は `implementer.md`「実装完了レポートのフォーマット」の ` - \`path\` — 概要` という markdown 記法に一方向依存する。将来 retrospector が implementer.md のレポート様式を改善（例: YAML frontmatter 化、箇条書き記法の変更）した場合、`grep -E '^- *\`'` + `sed -E 's/^- *\`([^\`]+)\`.*/\1/'` は静かに空集合を返し得る。これは「編集想定タスクなのに CLAIMED が空」→ NO_OP 免除なし → **PHANTOM_CLAIM** という形で顕在化するため fail-closed 方向ではあるが、根本原因（フォーマット変更）の診断には手間がかかる。
- **検証自体が非自動化**: `verify-deterministic-check.sh` は `.githooks/pre-commit` にも `.claude/settings.json` の `hooks` にも一切登録されていない（`grep -rln "verify-deterministic-check\|verify-sanitized-cwd"` で両ファイルとも 0 ヒット）。reference 編集時に「実行すること」という運用は完全に人間 or Claude の記憶に依存しており、これ自体が「検証機構が実在するという外観」と「実際に毎回実行される保証」の間にギャップを持つ（外部観点6で詳述する "verification theatre" の一種に近い形態）。同型の `verify-sanitized-cwd.sh` も同じ弱点を持つ既存の先例だが、6-3 側は分量が約5倍に拡大しており、同じ運用リスクの絶対量が増えている。
- **決定1=(A) の境界設計そのものの再検討余地**: 実装当時の user-decisions.md で「決定1 — (A) 6-1 直後の1箇所のみ（最小スコープ）。review-fix(7-4)・test-fix(8-2) の再実装ポイントは対象外（別タスク）」と明示的に確定している。これは意図的でドキュメント化された決定であり見落としではない。しかし今回のシステミック評価の観点では: **review-fix・test-fix の再実装は、reviewer/tester から FAIL を突きつけられた直後の「圧力下での再実装」であり、心理的には最初の平常実装より捏造・手抜きの誘因が強い局面**である（CLAUDE.md の founding incident「download_assets の偽成功報告」も、うまくいかない状況を取り繕う文脈で発生している）。6-3 は「最も穏やかな瞬間（初回実装）」を守り、「最も切迫した瞬間（review/test FAIL 後の再実装）」を意図的に守らない、という非対称なスコープになっている。`refactor-advisor` の提案 M-2（`refactor-proposals.md`）は既にこの非対称を明文化のみで整理する提案を出しており、"仕様選択はユーザーゲートで確定させること" と保留された経緯がある。恒久採用の判断材料としては、この境界を維持するか広げるかは今回の deepthink の論点になり得る。

---

## 外部観点分析（パターン→保証→落とし穴→本件への当たり）

### 観点4: trust-but-verify / 決定論的検証ゲートのパターンと既知の落とし穴

**パターン**: Anthropic は自社の agent 設計ガイドで、コーディングエージェントの検証について「Outcome verification」「State check」という用語を用い、発話（self-report）ではなく環境の実際の状態（例: フライト予約タスクなら SQL データベースにレコードが存在するか）を確認する設計を推奨している。これは6-3の「implementer/Codex の自己申告ではなく git working tree の実状態を照合する」という設計と構造的に同型であり、**「発話でなく状態を見る」という点で確立されたベストプラクティスに沿っている**（[Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)）。Evaluator-Optimizer パターンの一般原則としても「evaluation criteria should be explicit and ideally machine-checkable」「stopping conditions（最大反復回数）」が明記されており、6-3 の「hard fail は機械可読な集合差分のみ」「再実行1回限定＋2回目でユーザーゲート」という設計はこの原則に合致する（[Anthropic: Building Effective AI Agents](https://www.anthropic.com/research/building-effective-agents)）。

**保証**: 自己申告と実際の挙動の乖離は、理論上のリスクではなく統計的に高頻度な現象であるという外部データがある。Palo Alto Networks Unit 42 の調査（OpenClaw agent-skill registry, 49,943 スキルへの Behavioral Integrity Verification 適用）では、**80.0%のスキルが宣言と実際の挙動に少なくとも1つの不一致を示した**（うち81.1%は開発者の過失・悪意なし、18.9%が敵対的意図を示唆）（[Unit 42: Trust No Skill](https://unit42.paloaltonetworks.com/ai-agent-supply-chain-risks/)）。これは「LLM/エージェントの自己申告は例外的にではなく高い基準率で実態と乖離する」ことの一次データであり、6-3 のような決定論ゲートを設けること自体の妥当性を強く裏付ける。同時に、不一致の大半（81.1%）が悪意でなく凡ミス・記載漏れであるという内訳は、6-3 の非対称設計（PHANTOM=hard fail、UNDECLARED=warn）の設計思想（凡ミスまで一律ハードフェイルにすると経験的に高頻度の false-flag地獄になる）を裏付ける材料にもなる。

**落とし穴**: 
1. **eval saturation / brittle grading**: Anthropic の eval 記事は「厳格すぎる採点基準（rigid grading）が有効な解を不当にペナルティする」「grading bugs や agent harness の制約による false negatives」を明示的な失敗モードとして挙げている。6-3 の PHANTOM 判定はまさにこの形態のリスクを持つ（今回実機確認した staged / case-rename の2件は、この "brittle grading による false negative" の具体例に当たる）。
2. **alert fatigue（アラート疲労）**: セキュリティ運用の文献では「偽陽性率の高さは実務者の信頼を蝕み、本物のシグナルさえ無視されるようになる」("false positives waste developer time, erode trust... desensitization effect... alert fatigue")という定型的パターンが確立している（[Astra: False Positive Triage](https://www.getastra.com/blog/dast/false-positive-triage/), [Xygeni: False Positive Alert](https://xygeni.io/sscs-glossary/what-is-a-false-positive-alert-in-cyber-security/)）。6-3 の失敗パスは2回目 PHANTOM で「(B) PHANTOM を承知でそのまま reviewer へ進む」という bypass 選択肢をユーザーに提示する設計になっており、もし staged/case-rename のような **修正不能な false positive（再実行しても直らない）** が繰り返されれば、ユーザーは経験的に "(B) を選ぶのが正解" と学習し、ゲート自体の信頼性が実質的に空洞化する典型的なアラート疲労経路に入りうる。
3. **Verification Theatre（検証劇場）**: 暗号ライブラリの形式検証における "Verification Theatre" 論（Schneier の "security theater" を意識した用語）は「検証済みという体裁が、実際に検証が機能する保証を伴わない」ギャップを指摘する（[cronokirby: The Verification Theater](https://cronokirby.com/refs/2026-02-the-verification-theater-when-formal-methods-create-false-assurance-in-cryptographic-libraries.html), [IACR ePrint 2026/192](https://eprint.iacr.org/2026/192)）。6-3 自身の自己検証機構（verify-deterministic-check.sh）が CI/hook に配線されずランタイム経路からも独立している事実は、この「体裁と実態のギャップ」に該当しうる形態である。

**本件への当たり**: 6-3 は「発話でなく状態を見る」という点で外部ベストプラクティスに正しく沿っており、パターン選択自体は妥当。ただし (1) hard fail 対象（PHANTOM）を「機械的に完全に正しいオラクル」であるかのように運用しているため、oracle 自体の既知の穴（観点5）が直接 false negative に直結する設計になっている点、(2) 2回失敗時の bypass 選択肢がアラート疲労の入口になりうる点は、外部知見に照らして注意を要する。

### 観点5: git diff / working-tree state を検証 oracle にする健全性と穴

**パターンとしての健全性**: Git 公式ドキュメントで確認した通り、`git diff --name-only` は既定でリネーム検出が無効（`-M`/`--find-renames` を明示しないと働かない）（[git-scm: git-diff](https://git-scm.com/docs/git-diff)）。しかし本ゲートは `-M` を使わず、unstaged なリネームを「旧パスの削除（`git diff --name-only` で検出）＋新パスの未追跡（`git ls-files --others` で検出）」という2経路の組み合わせで自然に捕捉する設計になっており、実機検証（本レポート観点2「参考」）でもこれが正しく機能することを確認した。mode 変更・単純削除も正しく検知される。**したがって「git working tree を検証 oracle にする」という設計判断自体は、少なくとも典型的な unstaged 変更に関しては健全**である。

**既知の穴（本件で実機確認したもの）**:
- **ステージ済み変更**: `git diff`（unstaged のみ）は index と working tree が一致した状態（= ステージ済み）の変更を一切見ない。これは Git の基本仕様であり、6-3 固有のバグではなく「unstaged のみを見る」という設計選択の必然的帰結。ただし、この設計選択の前提（「実装 actor はステージングしない」）が implementer 側で技術的に強制されていない点は、本件固有のギャップである。
- **case-insensitive filesystem 上の大文字小文字変更**: macOS APFS・Windows NTFS（既定設定）はいずれも case-insensitive・case-preserving であり、大文字小文字のみの変更は OS レベルで「同一ファイルの上書き」として扱われ、git の index/working tree 比較のどのレイヤーにも変化が反映されない。これは Git 自体が抱える古典的な既知の落とし穴（"git rename detection on case-insensitive filesystem" は Stack Overflow 等で頻出する既知の話題領域）であり、6-3 固有のバグではなく **git を oracle にする設計全般が引き継ぐ構造的限界**。

**本件への当たり**: この2点は「git 自体の一般的な既知の限界」であって「6-3 の実装バグ」ではない。したがって修正のアプローチは「実装を直す」ではなく「(a) 既知の残存限界として明記する（Fable5.md の残存限界一覧・reference の『検証不能な申告の扱い』節と同じ扱い方に揃える）、(b) 影響が大きいと判断すれば staged 検出（`git diff --cached` も delta に含める設計変更、ただし『実装 actor はステージしない』という前提を諦めることになる）や、大文字小文字変更の別経路検出（例: `git status --porcelain=v1` で `R` フラグの有無を見る、または `core.ignoreCase` の明示的な無効化を implementer 起動前提条件にする）を検討する」のいずれかであり、恒久採用の判断材料として明記すべき事項である。

### 観点6: 「実験的機能に検証インフラを厚く投資する」ことの是非（YAGNI vs 観測可能性）

**一般論**: Martin Fowler の YAGNI 原則は「今使わない機能を作らない」だけでなく「将来の柔軟性のための抽象化・パラメータ化」全般に適用され、「現在の要件を理解しにくくする抽象化は有罪」と明記する。同時に「YAGNIはソフトウェアの健全性を怠ることの正当化ではない」「リファクタリング・テストコード・継続的デリバリーはYAGNI違反ではない、進化的設計に必須の実践だから」とも明記しており、**品質・検証への投資は原則として YAGNI と対立しない**という立場を取る（[Martin Fowler: Yagni](https://martinfowler.com/bliki/Yagni.html)）。

**本件への当たり**: この原則に照らすと、6-3 のような決定論的検証機構を実験段階（epic 試験実装 executions=0）で先行整備すること自体は、YAGNI 違反ではなく「進化的設計を支える健全性投資」として正当化できる。Fable5.md 自身も「epic の『完璧』は堅牢化でなく計器化である」「W1（pir2 6-3）は epic 不採用でも素の pir2 の資産として残る」という設計思想を明示しており、これは「投資が実験結果によらず回収される」という健全な配置である。

一方で Fowler の警句（「現在の要件を理解しにくくする抽象化は有罪」）を裏返すと、**検証インフラ自体の複雑性が実際の欠陥率に見合っているか**は別途問う必要がある。6-3 の直接の動機となった実インシデントは CLAUDE.md に明記された2026-06-13の1件（`download_assets` の偽成功報告＋探索/diff/Editの創作）であり、Fable5.md でも「事象X」「事象Y」として言及される具体的な過去2件が根拠になっている。この「2件の実インシデント」に対して「279行＋385行、3ファイルにまたがるフォーマット結合を持つ機構」を全 run 必須で投入するのは、YAGNI的には「発生実績に見合った最小の対策か、先回りした過剰投資か」という評価軸で恒久採用判断時に問い直す価値がある。特に、観測可能性（instrumentation）を先に入れておくこと自体は一般に推奨される実務（"making observability part of your definition of done"）だが、それは通常「まず log-only で計測し、閾値・実効性を実データで較正してからブロッキング化する」という段階導入を伴う。Fable5.md 自身も hook 部分（M2 の B経路）については「Stage A（log-only）→ 実データ確認 → Stage B（block モード）」という段階導入を明記しているのに対し、**6-3（C経路・git集合照合）は段階導入なしに初回から hard fail でデプロイされている**点は、同じ設計文書内での一貫性という観点でも指摘に値する（hook側は慎重に log-only 先行、git-diff側はいきなり blocking）。

---

## 補足情報

### 「存在しない/未検証」型結論についてのチェック手順の明記

本レポートは「6-3 は experimental.md に追跡されていない」「implementer.md に git add 禁止の記述がない」という2つの否定的結論を含む。いずれも以下の手順で確認済み:
1. `experimental.md` 全文を Read し、4件の既存 Experiment セクション見出し（`pir2-implementer-shards-and-review-fix-shards` / `pir2-implementer-sequential-units` / `pir2-explorer-nesting` / `epic-orchestrator-nested-pir2`）を列挙。`deterministic-completion-check` / `6-3` に該当する見出しが無いことを目視確認。
2. `grep -n "git add\|git commit\|ステージ\|stage" .claude/agents/implementer.md` で 0 ヒットを確認（該当行が一件も返らないことを Bash 実行結果で確認）。
3. `grep -rln "verify-deterministic-check\|verify-sanitized-cwd" .githooks/ .claude/settings.json .claude/hooks/` で 0 ヒットを確認。

### 実機検証サマリー（本レポートの一次証拠）

| シナリオ | 結果 | PHANTOM への影響 |
|---|---|---|
| unstaged 通常編集 | `git diff --name-only` で検知 | 正常動作 |
| unstaged 単純削除 | `git diff --name-only` で検知 | 正常動作 |
| unstaged mode変更（chmod +x） | `git diff --name-only` で検知 | 正常動作 |
| unstaged リネーム（`mv` のみ） | 旧パスが diff、新パスが ls-files に分離して検知 | 正常動作（旧パス未申告分は UNDECLARED warn止まり） |
| **staged リネーム（`git mv && git add`）** | unstaged側・untracked側とも空。`--cached` でのみ見える | **PHANTOM false positive（新規発見）** |
| **case-only リネーム（macOS APFS）** | diff/ls-files/status 全て空。`git ls-files` の追跡名も旧名のまま | **PHANTOM false positive（新規発見）** |
| 埋め込み改行を含むファイル名 | `core.quotePath=false` でも制御文字は常に `\n` エスケープ＋二重引用符で1行に保持される（安全側） | 実害なし（理論上のみ懸念、検証の結果リスク低いと判断） |

### 視覚情報との整合チェック

本タスクにユーザー提供のスクリーンショット・画像等の視覚的一次情報は含まれていない。該当なし。

### リファレンス移植ゲートの該当性

本タスクは既存実装からの移植タスクではない（既存ゲート設計の系統的レビュー調査）。該当なし。

---

## 参照した外部ソース

| ソース種別 | URL | 確認した内容 |
|---|---|---|
| 公式（Anthropic Research） | https://www.anthropic.com/research/building-effective-agents | Evaluator-Optimizer パターンの定義、機械的検証可能性、反復回数の上限（stopping conditions）への言及 |
| 公式（Anthropic Engineering） | https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents | Outcome verification / State check（発話でなく環境状態を検証する設計）、brittle grading による false negative、eval saturation の言及 |
| 公式（Git 公式ドキュメント） | https://git-scm.com/docs/git-diff | `--name-only` の既定リネーム検出無効（`-M`必須）、`--ignore-submodules=dirty` の挙動確認 |
| 一次調査データ（Unit 42 / Palo Alto Networks） | https://unit42.paloaltonetworks.com/ai-agent-supply-chain-risks/ | OpenClaw registry 49,943スキルの BIV 適用結果。80.0%が宣言と挙動の不一致（81.1%は過失、18.9%は敵対的示唆）という定量データ |
| 一次エッセイ（Martin Fowler bliki） | https://martinfowler.com/bliki/Yagni.html | YAGNI原則の適用範囲（抽象化全般）、品質投資（リファクタ・テスト・CD）はYAGNI違反ではないという明記 |
| 二次（セキュリティ実務ブログ・確度中） | https://www.getastra.com/blog/dast/false-positive-triage/ | 偽陽性がもたらす alert fatigue・信頼毀損の一般的パターン |
| 二次（セキュリティ用語解説・確度中） | https://xygeni.io/sscs-glossary/what-is-a-false-positive-alert-in-cyber-security/ | 偽陽性による desensitization（アラート疲労）の定義 |
| 二次（研究者個人ブログ・要約） | https://cronokirby.com/refs/2026-02-the-verification-theater-when-formal-methods-create-false-assurance-in-cryptographic-libraries.html | "Verification Theatre" 概念の要約（元論文の解説記事） |
| 一次（暗号研究プレプリント・IACR ePrint） | https://eprint.iacr.org/2026/192 | Verification Theatre の原典（形式検証の体裁と実態のギャップ） |

> ℹ️ Unit 42・Fowler・Anthropic 公式・git 公式は一次/準一次ソースとして確度高。getastra/xygeni/cronokirby はブログ・要約記事であり確度は中程度（一般論としての裏付けに留め、断定の根拠には単独で使っていない）。

---

## 呼び出し元への依頼

- 本レポートは 6-3 の**設計・運用面**のシステミック分析に限定した。以下は本レポートのスコープ外であり、必要であれば別 explorer / tech-validator への追加委譲を推奨する:
  - `IMPLEMENTATION_SHARDS`/`IMPLEMENTATION_UNITS`（試験実装の並列/直列実装）と 6-3 の相互作用（shard/unit 統合確認後の1回だけ適用という設計）についての独立した深掘りは行っていない（本レポートは主に単一 implementer 経路を対象に実機検証した）。
  - staged-blind-spot・case-rename-blind-spot に対する**具体的な修正案の設計**（例: `git status --porcelain=v1` への切替、`core.ignoreCase` 前提条件の追加等）はこのレポートの範囲外（explorer は実装しない）。恒久採用判断で「直す」方針になった場合は、実装は implementer に委譲すべき。
  - `決定1=(A)`（review-fix/test-fix 再実装を 6-3 スコープ外にする境界）を広げるかどうかは、機能仕様判断でありユーザー確認が必要な論点として明示的に残っている（`refactor-proposals.md` M-2 も同様に保留のまま）。
