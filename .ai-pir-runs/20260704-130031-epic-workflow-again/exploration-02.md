## 探索レポート: /epic 移行パス上の現在位置とW2要否判断

### 関連ファイル一覧

| ファイルパス | 役割・内容 | 変更の必要性 |
|------------|-----------|------------|
| `docs/deepthink/20260703-190750-Fable5.md` | 完成形設計本体。§0–§8 に L0↔L1↔L2 境界契約・移行パス W0→W1→W2→W3→G1→W4→G2→W5 を定義 | 参照のみ |
| `docs/deepthink/20260704-002417-review-w0w1-6-3.md` | W0+W1 の深レビュー。「修正してコミット」勧告・must-fix 3点・R1–R13 残存限界台帳 | 参照のみ |
| `.claude/skills/epic/SKILL.md` | 現行 `/epic` 本体。Fable5 設計より前の"素の"設計（W2 未反映） | 変更あり（W2着手時） |
| `.claude/agents/epic-planner.md` | 現行 epic-planner。分割レポートに Fable5 §3 の追加要件（hard-cap・DAG形状制約・破壊的分類 a-e・完了条件の型）が未実装 | 変更あり（W2着手時） |
| `.claude/skills/pir2/SKILL.md`（6-1〜6-3節） | W1（6-3 決定論的完了検証）実装済み。pre-set/post-set 記録・PHANTOM_CLAIM/UNDECLARED_CHANGE 判定 | 参照のみ |
| `.claude/skills/pir2/references/deterministic-completion-check.md` | 6-3 の共通プロトコル本体（W1） | 参照のみ |
| `.claude/skills/pir2/references/experimental.md` | `epic-orchestrator-nested-pir2`（現行epic の実験登録）と `pir2-deterministic-completion-check`（W1 の実験登録）の2エントリ | 参照のみ |
| `~/.claude/pir-handoff.md` | HANDOFF_PATH のデフォルト仕様（プロジェクト単位 `${PROJECT_ROOT}/.ai-pir-runs/handoff.md`・RUN_DIR スコープでない） | 参照のみ |
| `.claude/settings.json` / `.claude/lib/` | `SubagentStop` hook・`subagent-metrics.jsonl` の有無を確認（W3 実装確認用） | 参照のみ |

### 既存パターン・規約

- RUN_DIR 計算パターン（`run-dir-base.md` SSOT・`cut -c1-40` 統一）は pir2/epic 共通で踏襲されている
- Agent ネスト起動は epic 3-0 で `subagent_type=general-purpose` + `model=opus` 固定という規約が既に存在（W2 着手前から）
- 実験登録は `experimental.md` に `Status: Active` + `Evidence Summary` + `Adoption/Rejection Criteria` の型で統一されている（epic 用と 6-3 用で既に2件独立登録済み）

### 影響範囲

本タスクは調査・意思決定材料の提示のみが目的であり、実装・編集は行っていない。以下は「今後 W2 に着手する場合の影響範囲」の参考情報:

- 直接影響（着手時）: `.claude/skills/epic/SKILL.md`（3-0/3-4/3-5 の置換・Phase0新設）、`.claude/agents/epic-planner.md`（Phase1追加要件）、`experimental.md`（epic 実験の Metrics 更新）
- 間接影響: `pir2/SKILL.md` 6-3 は W1 で既に共通層実装済みのため W2 側からは変更不要（L1→L0 境界と L2→L1 境界は別レイヤー）

### 依存関係

- epic SKILL.md 3-0（L0→L1 起動）→ pir2 SKILL.md 全体（ネスト実行）→ pir2 内 6-3（L2→L1、W1 実装済み）
- HANDOFF_PATH: pir2 SKILL.md 側の既定値がプロジェクト単位・非 RUN_DIR スコープ（`pir-handoff.md` 確認）。epic 3-0 は現状この既定値を上書きする指示を一切持たない

---

## 補足情報（核心の分析）

### 1. 移行パス上の現在位置

```
docs/deepthink/20260703-190750-Fable5.md の移行パス:
  W0 → W1 → W2 → W3 → G1 → W4 → G2 → W5

現在位置（本探索で実ファイル確認済み）:
  ┌─────────────────────────────────────────────────────────┐
  │ W0 citation衛生            ✅ 実装済み・commit a10aa8e     │
  │ W1 pir2 6-3（共通層）       ✅ 実装済み・commit a10aa8e     │
  │   └ レビュー: 20260704-002417 で「修正してコミット」PASS   │
  │      （must-fix 3点は experimental.md 登録内容と整合済み） │
  │ ─────────────────────────────────────────────────────── │
  │ epic/SKILL.md + epic-planner.md（"素の" epic 基盤）        │
  │   ✅ 実装済み・commit a10aa8e（W1 と同一コミット）          │
  │   ※ Fable5 設計より前の設計。§1-1〜§8 の契約要素は不在      │
  │   ※ experimental.md に epic-orchestrator-nested-pir2      │
  │      として別途登録済み（Evidence Summary は全項目 0）     │
  │ ─────────────────────────────────────────────────────── │
  │ W2 epic境界契約一式          ❌ 未着手（本探索で確認）       │
  │   （§1-1起動契約/§1-2 return契約/§1-3 L0検証パイプライン/   │
  │    §2 Phase0/§8台帳/epic-planner Phase1追加要件）          │
  │ W3 hook Stage A             ❌ 未着手                       │
  │   （settings.json に SubagentStop 記述なし、               │
  │    .claude/lib/ に subagent-verify-hook.sh 等なしを確認）  │
  │ G1 1-unit epic dry-run      ⏸️ 未実施（本問いの対象）        │
  │ W4/G2/W5                   ❌ 未着手                        │
  └─────────────────────────────────────────────────────────┘
```

> ⚠️ Fable5 §6 の移行パス表は「現 epic → 完成形」という表題を持つが、実ファイル調査の結果、この「現 epic」（base skeleton）自体も W0/W1 と**同一コミット（a10aa8e）で新規追加されたばかり**である。つまり現在地は「W1 完了直後・W2 着手前」であり、Fable5 が想定していた「既存の epic に W2 を足す」という素材はすでに揃っている状態。

> 📝 レビュー報告（`20260704-002417`）は「W0/W1 分割コミット」を must-fix 隣接の推奨事項として挙げていたが、実際のコミット a10aa8e は base epic + W0 + W1 を**1コミットに束ねて**いる。本探索の主目的（W2要否判断）には直接影響しないが、事実として記録しておく。

### 2. G1 の4観測項目 — 「今可能」/「W2前提」仕分け表

| # | 観測項目 | 今の epic（W2なし）で観測可能か | 理由（実ファイル確認済み事実） |
|---|---------|------------------------------|--------------------------------|
| ① | L1 契約遵守 | **部分的にのみ可能（別物）** | 現行 epic 3-0 は「pir2 SKILL.md を Read して自律遂行せよ」という素朴な指示のみで、Fable5 §1-1 起動契約の7項目（`SUBTASK_ID`/完了条件・サブRUN_DIR命名規約・HANDOFF_PATH上書き・先行成果注入・§1-2 return契約・ゲートポリシー・ループ上限）は**プロンプトに一切存在しない**（epic/SKILL.md 実読了で確認）。よって「正式契約への遵守」は測定不能。観測できるのは**P5**（L1がpir2 SKILL.md全文を自律オーケストレーションできるか）の**素の挙動**のみ |
| ② | Agent 同期/非同期 | **完全に可能** | Agent ツールのネスト起動ランタイム特性であり、epic 側のプロンプト内容と無関係。現行 epic 3-0 で既に Agent ネスト起動が行われているため、そのまま観測できる |
| ③ | hook データ妥当性 | **不可能** | W3（hook Stage A）が未実装。`.claude/settings.json` に `SubagentStop` エントリなし、`.claude/lib/` に該当スクリプトなしを実ファイルで確認。観測対象そのものが存在しない |
| ④ | HANDOFF 上書き遵守 | **不可能** | 現行 epic 3-0 に HANDOFF_PATH 上書き指示が存在しない（grep 確認）。L1（ネスト pir2）は自分自身の pir2 SKILL.md ステップ1 の既定値 `HANDOFF_PATH="${PROJECT_ROOT}/.ai-pir-runs/handoff.md"`（プロジェクト単位・非 RUN_DIR スコープ）をそのまま使う。遵守すべき契約自体が無いので「遵守」を測る対象がない |

**中央裁定**: 4項目中、完全に W2 非依存で観測できるのは **② のみ**。① は「劣化版」（設計した契約でなく素の pir2 自律性）しか観測できず、③④ は W2/W3 の実装が前提で**原理的に観測不可**。

### 3. W2 なし dry-run で得られるもの / 得られないもの

#### 得られるもの

- **P5（L1の自律オーケストレーション可否）の一次データ**: L1（`model=opus` の general-purpose ランナー）が pir2 SKILL.md 全文（explorer→planner→implementer→reviewer→tester→retrospector の起動・ループ管理・VERDICT集約・ユーザー確認ゲート委譲判断）を実際にこなせるかどうか。これは Fable5 の対立#1（Option A vs B）の反証トリガ判定材料である **U1** に直結する一次情報で、現時点で完全に未実証（Fable5 本文にも「机上では埋まらない」と明記）
- **W1（6-3）が epic 配下でも発火するかの確認**: nested pir2 内部の implementer 完了 → 6-3 決定論的完了検証 → reviewer 起動、という既存フローが「epic から起動された L1」でも正しく辿られるかの実データ
- **Agent 起動の同期/非同期特性（観測項目②）**: これは W2 の有無に関わらず観測可能で、G1 の本来目的の一部をそのまま満たせる
- **現行の緩い委譲指示（3-3 深さバジェット・3-4 DEFERRED_USER_DECISIONS 記録・3-5 Ti→サブRUN_DIRマッピング）への L1 の遵守有無**: これは Fable5 設計の正式契約ではないが、W2 を厳密化する際の実地材料にはなる
- **epic-planner の分割挙動**: ただし「1-unit dry-run」なので分割の質（hard-cap・DAG形状制約等）はほぼ問われない

#### 得られないもの

- **観測項目①の「本来観測したかったもの」**: Fable5 設計の正式契約（EPIC_TELEMETRY見出し・起動契約7項目）への遵守は、契約自体が存在しないため測定不能
- **観測項目③（hookデータ妥当性）**: W3 が無いため原理的に取得不可
- **観測項目④（HANDOFF上書き遵守）**: 契約自体が存在しないため測定対象が存在しない
- **対立#1のG1判定トリガ**「L1契約が是正1回を挟んで連続2回不履行なら A-lite常用化を上程」の判定: 「契約」という観測対象が存在しないため、このトリガ自体が発火し得ない。すなわち **G1 が本来担うはずの U1 判定は、W2なしでは達成できない**
- **§1-3 L0検証パイプラインの実地観測**（L1 return に対する PHANTOM_CLAIM/UNDECLARED_CHANGE 判定・STATUS不変条件チェック）: §1-3 自体が実装されていないため観測不可
- **台帳（epic-runs.md）構造化フォーマットの実証**: 現行 3-5 は「Ti→サブRUN_DIR」の軽量マッピングのみで、Fable5 §8 の `NODE_START/NODE_RETURN/VERIFY/...` イベント語彙は未実装のため実証にならない
- **既存 `experimental.md` の `epic-orchestrator-nested-pir2` エントリの Metrics**（サブタスク数分布・並列fan-out数・深さバジェット超過回数・結合不整合発生回数・DEFERRED発生回数）は Fable5 の G1 観測項目①②③④と**1対1対応しない**。素の dry-run を回すと、まずこの既存 Metrics（Evidence Summary が現在全項目0）が埋まるのであって、Fable5 の G1 が意図した①②③④の観測は**運用者が意識的に見に行かない限り自動的には得られない**

### 結論（推測を含む・明示）

1. **技術的には今すぐ dry-run 可能**: 現行 epic/SKILL.md は既に committed・機能する状態にあり、Bash/Agent 機構上は W2 なしでも 1-unit epic を起動できる。
2. **ただし Fable5 が設計した「G1」そのものは W2 なしでは成立しない**: G1 の4観測項目のうち②のみ完全観測可能、①は別物（劣化版）しか取れず、③④は原理的に観測不可。特に G1 の最重要目的である**対立#1のU1判定トリガ評価**は「契約」という観測対象が無いと判定不能なため、W2 なしの dry-run は Fable5 設計上の G1 を代替できない。
3. **（推測）段階的な価値**: W2 なしで 1 回 dry-run し「L1 が pir2 SKILL.md 全文を自律遂行できるか（P5）」「Agent 起動が同期/非同期か（②）」だけを先に素で観測する、という **"G1 未満の予備観測"** には価値がありうる。W2 の起動契約（§1-1）は7項目の複雑な条件分岐をプロンプトに詰め込む設計であり、「L1（弱いモデルではなく model=opus 固定だが）がこの複雑さに耐えられるか」という前提（Fable5 本文「弱いモデルでは条件分岐が破綻する」の懸念の逆）を、より単純な現行プロンプトでまず素の挙動を見ておくことは、W2 の複雑性が本当に必要かどうかの判断材料にもなりうる。ただしこれは Fable5 が設計した G1 の代替ではなく、**別の（より簡易な）予備実験**として位置づけるべきであり、その旨をユーザーに明示した上で採否を判断してもらうのが妥当と考える（この判断自体は本探索のスコープ外であり、呼び出し元・ユーザー判断に委ねる）。

### 呼び出し元への依頼

- 本探索は W2/W3/G1 の要否判断材料の提示に留めており、実装着手は行っていない。W2 着手を決定する場合は `.claude/skills/epic/SKILL.md` / `.claude/agents/epic-planner.md` の変更を伴うため、実装は implementer に回してほしい
- 「W2 なしの予備 dry-run」を採用するかどうかはユーザー判断が必要な論点（設計上の G1 と等価でないため）。deepthink 本体側で choice として提示することを推奨する
