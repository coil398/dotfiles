## エピック分割レポート: Codex 共通 Sol/Luna/Terra 実行層 v3

### 概要
Codex の個別 epic だけでなく、Codex native workflow 全体で共通して使う実作業委譲層を導入する。Sol が対話・調査・判断・計画・分解・完了要件・昇格・最終判定を所有し、具体実作業は単一パッケージ `worker-delegation`（仮称）を通じて既定 Luna Max へ委譲、Sol の実測で能力不足・要件未達・判断不足を確認した場合のみ Terra、さらに明示条件で Sol 直実行へ昇格する。既存 `.codex/skills/luna-max-worker/**` の task/requirements/runner は新パッケージへ吸収し、恒久互換 wrapper は併存させず、全参照同時更新による完全置換を推奨案とする。

### 全体探索サマリー
初回探索では epic / pir2 / agents / sync/config の境界を確認し、追加探索では Luna worker の固定実行核と GPT-5.6 model routing 参照を確認した。v3 追加探索では、実作業 actor を持つ Codex native workflow が少なくとも `pir2`, `ir`, `debug`, `writing-plan`, `epic`, `pir2async` であり、`brainstorm` は設計専用で直接実作業へ接続しないことを棚卸しした。

探索レポート:
- `/Users/kawasetakumi/dotfiles/.ai-pir-runs/20260806-121444-epic-port-and-tune-epic-for-codex/epic-exploration-assets.md`
- `/Users/kawasetakumi/dotfiles/.ai-pir-runs/20260806-121444-epic-port-and-tune-epic-for-codex/epic-exploration-model-routing.md`
- `/Users/kawasetakumi/dotfiles/.ai-pir-runs/20260806-121444-epic-port-and-tune-epic-for-codex/epic-exploration-workflow-routing.md`

確認済み前提:
- `origin/master=0be01cd` はローカルと一致し、未取得の追加版はない。
- 昨日の `.codex/skills/luna-max-worker/**` が既存核であり、新規の重複 Luna skill は作らない。v3 の推奨案は、この核を `worker-delegation` へ吸収し、旧 `luna-max-worker` 参照を同時に置換すること。
- 進行中 T1 の `.codex/skills/epic/**` 骨格変更は維持する。

### サブタスク一覧
- T1: Codex epic スキル本体の基本 runtime 骨格を確定する（進行中維持）
  - 担当範囲: Codex epic skill overlay / `.codex/skills/epic/**`
  - 想定成果物: Claude 固有残骸、`pir2codex`、固定 gpt-5.5、深い general-purpose runner 前提を除いた Codex native epic skill の基本骨格
  - 依存: none
  - 共有リソース: `.codex/skills/epic/**`
- T2: `worker-delegation` 共通実行パッケージを設計する
  - 担当範囲: 既存 Luna worker 核の吸収先となる Codex native 共通パッケージ / `.codex/skills/luna-max-worker/**`、新規 `worker-delegation`（仮称）資産、必要な Codex native reference
  - 想定成果物: 旧 `luna-max-worker` の task/requirements/runner を吸収し、Luna Max 既定委譲、Sol acceptance 実測、Terra 昇格条件、Sol 直実行条件、worker 自己申告非採用、reviewer/tester 別系統を一契約にまとめた共通実行パッケージ
  - 依存: none
  - 共有リソース: `.codex/skills/luna-max-worker/**`、新規 `worker-delegation`（仮称）配下、必要な新規 `.codex/skills/**/references/**`
- T3: PIR² 実装フェーズを共通実行層へ接続する
  - 担当範囲: Codex PIR² workflow / `.codex/skills/pir2/**`
  - 想定成果物: PIR² の探索・計画・破壊的変更チェック・レビュー・テスト・振り返りは Sol が所有し、具体実装 actor だけを共通 Sol/Luna/Terra ladder へ委譲する接続
  - 依存: T2
  - 共有リソース: `.codex/skills/pir2/**`
- T4: 軽量実装 workflow 群を共通実行層へ接続する
  - 担当範囲: Codex lightweight workflow overlays / `.codex/skills/ir/**`, `.codex/skills/debug/**`, `.codex/skills/writing-plan/**`
  - 想定成果物: 各 workflow の既存オーケストレーションを保ちつつ、`implementer` 直接起動箇所を共通 Sol/Luna/Terra ladder へ置換・参照する接続
  - 依存: T2
  - 共有リソース: `.codex/skills/ir/**`, `.codex/skills/debug/**`, `.codex/skills/writing-plan/**`
- T5: epic と planner 系の接続を v3 共通実行層へ合わせる
  - 担当範囲: Codex epic overlay と epic-planner / `.codex/skills/epic/**`, `.codex/agents/epic-planner.toml`
  - 想定成果物: 進行中 T1 の epic 骨格を維持し、実作業 actor の詳細を共通実行層参照へ寄せ、epic-planner が Luna 委譲可能な所有範囲・完了要件・昇格トリガーを出せる契約
  - 依存: T1, T2
  - 共有リソース: `.codex/skills/epic/**`, `.codex/agents/epic-planner.toml`
- T6: 実験的/設計専用 workflow の扱いを整理する
  - 担当範囲: Codex experimental/design workflows / `.codex/skills/pir2async/**`, `.codex/skills/brainstorm/**`
  - 想定成果物: `pir2async` を初期導入対象にするか縮退/後回しにするかの Codex native 方針、`brainstorm` は実装禁止・設計専用として共通実行層へ直接接続しない方針
  - 依存: T2
  - 共有リソース: `.codex/skills/pir2async/**`, `.codex/skills/brainstorm/**`
- T7: 観測・テレメトリ・記録仕様を共通実行層へ合わせる
  - 担当範囲: Codex workflow references / `.codex/skills/pir2/references/**`, 必要な観測ドキュメント
  - 想定成果物: Luna 実行数、Terra 昇格数、Sol 直実行数、Sol acceptance FAIL、reviewer FAIL、tester FAIL、昇格理由、worker 自己申告との不一致を記録できる観測仕様
  - 依存: T3, T4, T5, T6
  - 共有リソース: `.codex/skills/pir2/references/**`, `docs/epic-observation-checklist.md` または新規 Codex workflow 観測文書
- T8: sync/config/contract test と native overlay 仕様を整合させる
  - 担当範囲: Codex adapter / seed / contract / config 仕様 / `etc/sync-codex.sh`, `etc/seed-codex-overlay.sh`, `etc/test-codex-contracts.sh`, `.codex/config.base.toml`, `AI-WORKFLOW-SPEC.md`
  - 想定成果物: `worker-delegation` が Codex native overlay 内に閉じ、shared core へ Codex model 名を押し込まず、旧 `luna-max-worker` 参照が残らず、既存 overlay を default sync で上書きしないことを検証できる契約
  - 依存: T2, T3, T4, T5, T6
  - 共有リソース: `etc/sync-codex.sh`, `etc/seed-codex-overlay.sh`, `etc/test-codex-contracts.sh`, `.codex/config.base.toml`, `AI-WORKFLOW-SPEC.md`, 生成される `.codex/AGENTS.md` / `.codex/config.toml`
- T9: 統合確認と全 workflow 契約検証を行う
  - 担当範囲: Codex native workflow 全体 / T1〜T8 の成果
  - 想定成果物: Sol 司令塔、Luna 既定実作業、Terra/Sol 明示昇格、Sol acceptance 実測、reviewer/tester 分離、各 workflow 接続、sync/config contract の統合確認結果
  - 依存: T7, T8
  - 共有リソース: リポジトリ全体の検証状態、`.ai-pir-runs/**` の実行記録、必要に応じた generated adapter 出力

### 依存グラフ（DAG）
```text
T1 (進行中維持) ─┐
                 ├─ T5 ─┐
T2 ─┬─ T3 ───────┤      │
    ├─ T4 ───────┤      ├─ T7 ─┐
    ├─ T5 ───────┘      │      ├─ T9
    └─ T6 ──────────────┘      │
                 T2,T3,T4,T5,T6 ── T8 ─┘
```

- 並列実行可能グループ: `{T1, T2}` → `{T3, T4, T5, T6}` → `{T7, T8}` → `{T9}`
- 直列辺: `T1 → T5`, `T2 → T3`, `T2 → T4`, `T2 → T5`, `T2 → T6`, `T3 → T7`, `T4 → T7`, `T5 → T7`, `T6 → T7`, `T2 → T8`, `T3 → T8`, `T4 → T8`, `T5 → T8`, `T6 → T8`, `T7 → T9`, `T8 → T9`
- 暗黙依存（共有リソース競合による直列化）: `T1 → T5` は `.codex/skills/epic/**` の進行中編集との衝突回避。`T2 → T3/T4/T5/T6` は共通契約未確定のまま各 workflow へ接続しないため。`T7/T8 → T9` は観測仕様と sync/config contract の最終照合のため。

### 各 pir2 へ渡すタスク記述（WHAT と境界のみ）
- T1: "進行中の `.codex/skills/epic/**` 基本骨格更新を維持し、Codex native epic の runtime 骨格を確定してください。他者の編集を戻さず、共通 Sol/Luna/Terra 実行層の詳細は後続 T5 に委ねてください。触ってよい範囲は `.codex/skills/epic/**`。"
- T2: "既存 `.codex/skills/luna-max-worker/**` の task/requirements/runner を吸収し、単一 `worker-delegation`（仮称）として Codex native workflow 共通の Sol/Luna/Terra 実行層契約を作ってください。新規の重複 Luna skill は作らず、恒久互換 wrapper も併存させず、Luna 既定、Sol acceptance 実測、Luna 自動 fallback 禁止、Terra/Sol 明示昇格、reviewer/tester 分離を一契約として表現してください。触ってよい範囲は `.codex/skills/luna-max-worker/**`、新規 `worker-delegation`（仮称）配下、必要な Codex native reference。shared core へ Codex model 名を入れないでください。"
- T3: "`.codex/skills/pir2/**` の実装 actor 接続を、T2 の共通実行層へ合わせてください。Sol が探索・計画・ゲート・完了要件・acceptance・review/test を所有し、具体実装だけ Luna→Terra→Sol ladder に委譲する WHAT を満たしてください。触ってよい範囲は `.codex/skills/pir2/**`。"
- T4: "`.codex/skills/ir/**`, `.codex/skills/debug/**`, `.codex/skills/writing-plan/**` の実装 actor 接続を、T2 の共通実行層へ合わせてください。各 workflow の既存の軽量性・診断・記録責務は保ち、実作業 actor だけを共通契約参照へ寄せてください。"
- T5: "進行中 T1 の epic 骨格と T2 の共通実行層を接続し、`.codex/agents/epic-planner.toml` が共通実行層向けの所有範囲・完了要件・昇格条件を分割成果物に出せるよう整合してください。触ってよい範囲は `.codex/skills/epic/**` と `.codex/agents/epic-planner.toml`。"
- T6: "`.codex/skills/pir2async/**` と `.codex/skills/brainstorm/**` の扱いを整理してください。`brainstorm` は設計専用として実作業層へ直接接続しない方針を保ち、`pir2async` は初期導入対象・縮退・後回しのいずれかを Codex native 方針として明確にしてください。"
- T7: "T3〜T6 の workflow 接続を前提に、共通実行層の観測・記録仕様を整えてください。Luna/Terra/Sol actor 選択、昇格理由、Sol acceptance 実測結果、reviewer/tester 結果を追跡できる WHAT を満たしてください。触ってよい範囲は `.codex/skills/pir2/references/**` と必要な Codex workflow 観測ドキュメント。"
- T8: "T2〜T6 の変更が Codex native overlay 方針、sync/seed/contract/config と矛盾しないよう整合してください。触ってよい範囲は `etc/sync-codex.sh`, `etc/seed-codex-overlay.sh`, `etc/test-codex-contracts.sh`, `.codex/config.base.toml`, `AI-WORKFLOW-SPEC.md`、必要な generated adapter 出力。旧 `luna-max-worker` 参照の残存検出、`worker-delegation` 存在確認、default sync で native overlays を上書きしない契約を含めてください。"
- T9: "T1〜T8 の成果を横断して、Codex 全 workflow 共通実行層として Sol 司令塔、Luna 既定実作業、Terra/Sol 明示昇格、Sol acceptance 実測、reviewer/tester 分離、各 workflow 接続、sync/config contract の整合を検証してください。触ってよい範囲は検証記録と、統合不整合に限る最小修正。"

### 適用される既存ルール
- 照合した参照元: `AGENTS.md`, `AI-WORKFLOW-SPEC.md`, `.codex/skills/luna-max-worker/**`, `.codex/skills/pir2/**`, `.codex/skills/ir/**`, `.codex/skills/debug/**`, `.codex/skills/writing-plan/**`, `.codex/skills/epic/**`, `.codex/skills/brainstorm/**`, `.codex/skills/pir2async/**`, `.codex/skills/codex/**`, `.codex/agents/implementer.toml`, `.codex/agents/reviewer.toml`, `.codex/agents/tester.toml`, `.codex/config.base.toml`, `etc/sync-codex.sh`, `etc/seed-codex-overlay.sh`, `etc/test-codex-contracts.sh`
- 適用ルール一覧:
  - `.codex/agents/**` と `.codex/skills/**` は Codex native overlay であり、Claude/shared core との厳密一致を要求しない。
  - Codex model 名と GPT-5.6 family の責任分離は Codex native overlay 内に閉じる。
  - `.agents/skills/**` shared core へ Codex 固有 model routing を押し込まない。
  - 既存 `.codex/skills/luna-max-worker/**` の task/requirements/runner を `worker-delegation` へ吸収し、新規の重複 Luna skill や恒久互換 wrapper を作らない。
  - Luna は具体化済み作業だけを実行し、自動 fallback しない。昇格は Sol が実測根拠を持って明示する。
  - Sol acceptance と reviewer/tester 品質評価を分離する。
  - 共有リソース競合があるサブタスクは暗黙依存で直列化する。
  - ユーザーの既存未コミット変更は戻さない。現在見えている未追跡 `.claude/skills/design-review` は本エピック範囲外として触らない。

### 注意点・リスク
- 進行中 T1 が `.codex/skills/epic/**` を触っているため、T5 は T1 完了後に起動する。
- `implementer.toml` は既存 gpt-5.5 実装エージェントとして詳細規則を持つため、すぐ削除せず、共通実行層への移行後の残存用途を T9 で確認する必要がある。
- `pir2async` は implementer + reviewer チームを前提にしており、Luna worker ladder と構造が衝突しやすい。T6 で初期接続対象から外す判断もありうるが、これはスコープ縮小ではなく実験 workflow の隔離として扱う。
- `luna-max-worker` は foreground 実行・Luna 固定・output file 既存拒否など安全規則を持つ。共通実行層でこの安全規則を弱めないこと。
- `.codex/config.base.toml` の既定 model は Terra だが、これは Sol セッション既定であり、実作業既定 actor を Luna にする契約と混同しない。
- `luna-max-worker` から `worker-delegation` への rename/吸収は削除を伴うため、全参照同時更新と契約テストが必須。恒久 wrapper を置かない方針なので、参照漏れは即 runtime 破断につながる。
- remote 昨日 commit `0be01cd` と一致している前提では未取得の追加版に配慮する必要はないが、昨日追加された `.codex/skills/luna-max-worker/**` を短期間で rename/吸収するため、差分レビューでは「意図した移行」だと明示する必要がある。

### EXPLORATION_NEEDED（ネスト探索でも解消しなかった場合のみ）
なし。
