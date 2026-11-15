## プランレポート: pir2 新ステップ「6-3: 決定論的完了検証」の追加 + pir2codex への共通 reference 化（v2・決定確定版）

### 概要
implementer / Codex の自己申告した変更ファイル集合と実 git delta（unstaged + untracked）を純 bash で集合照合し、PHANTOM_CLAIM（捏造）を hard fail・UNDECLARED_CHANGE（未申告変更）を warn として決定論検出する検証ロジックを、新規 reference `deterministic-completion-check.md` に **pir2 / pir2codex 共通プロトコル**として切り出す。pir2 は新ステップ 6-3（初回実装点 6-1 直後の1箇所のみ）でこの reference を参照し、pir2codex は既存 6-1「git diff で実体検証（必須）」をこの reference 参照に**書き換えて重複を解消**する。PHANTOM 検出時は実装 actor（implementer / Codex）を1回だけ再実行（検証レポート逐語注入）→ 再失敗なら reviewer を起動せずユーザーゲート。全て決定論・純 bash・context O(1)。既存の shard/sequential 統合確認（`implementation-delegation.md`）の「デフォルト actor（pir2）および Codex actor（pir2codex）への一般化」として位置づける。

> このプランは v1（`PLAN_STRATEGY_CHANGED=true` で再策定）を上書きする。差分の本体は **決定2=(B) pir2codex 共通化**（v1 では (A) スコープ外だった）。決定1=(A)（配線点 6-1 のみ）・決定3=(A)（implementer.md へ NO_OP マーカー）は確定どおり据え置き。

### 適用される既存ルール（ステップ 1.5 照合結果）
- 照合した参照元（Read 済み）:
  - `/Users/kawasetakumi/dotfiles/CLAUDE.md`（プロジェクト直下）
  - `/Users/kawasetakumi/.claude/CLAUDE.md`（グローバル。system-reminder で全文ロード済み）
  - `/Users/kawasetakumi/.claude/projects/-Users-kawasetakumi-dotfiles/memory/MEMORY.md`（feedback 目次。全項目 permission/settings-drift/cd 複合系で本タスク領域に直接該当なし）
  - `/Users/kawasetakumi/dotfiles/.claude/skills/pir2/SKILL.md`・`/Users/kawasetakumi/dotfiles/.claude/skills/pir2codex/SKILL.md`
  - `/Users/kawasetakumi/dotfiles/.claude/agents/implementer.md`
  - `/Users/kawasetakumi/dotfiles/.claude/skills/pir2/references/{next-steps-queue,implementation-delegation}.md`
  - 設計 SSOT: `/Users/kawasetakumi/dotfiles/.ai-pir-runs/20260703-190750-Fable5/position-1.md` §1-3/§1-4
- 適用されるルール一覧:
  - **グローバルファイルの汎用性ルール** — 新規 reference・SKILL.md・implementer.md はグローバルスコープ。プロジェクト固有名を混入させない。bash は汎用（`git` / `comm` / `sed` / `sort` のみ）→ 本プランは汎用のみで構成
  - **自動 restore 禁止（Git ルール）** — PHANTOM 検出時の補償は「`git diff` 全 hunk をユーザー提示 + 人間判断」に限定。`git restore` / `git checkout -- <file>` を検証パスに一切書かない → 失敗パスのユーザーゲートに反映
  - **Bash で cd 複合コマンドを書かない（MEMORY.md feedback）** — reference の bash は `git -C "$PROJECT_ROOT"` を使い `cd <dir> && ...` を書かない → 付録A に反映済み
  - **問題の迂回禁止・ブラインドリトライ禁止** — 「初回検証 FAIL → 検証レポート逐語注入して再実行1回 → 2回目失敗で停止（計2回でユーザーゲート）」＝原因特定済みの1回リトライで非衝突 → 失敗パスに反映
  - **後方互換・dead code 温存禁止** — (a) 6-3 追加で既存 6-2（shard/unit 統合確認）を dead 化させない（別レイヤーとして相互参照で棲み分け）。(b) pir2codex 6-1 の旧「git diff --name-only HEAD 実体検証」は共通 reference 参照に**置換**し、旧記述を dead に残さない → 実装ステップ11 で明示
  - **スコープ厳守** — 6-3 追加 + pir2/pir2codex の 6-1 配線 + implementer.md NO_OP マーカー + 波及（next-steps 初期テンプレ・両 SKILL.md step12）のみ。hook・epic 境界契約・fan-out・review-fix/test-fix への配線・台帳スキーマには一切手を出さない → 実装ステップを該当範囲に限定
  - **既存構造パターンからの逸脱には事前確認** — reference 化の粒度・`*-check.md` 命名・`### 6-3` サブ見出し配置は既存慣習に完全準拠（逸脱なし）
  - **ユーザー発話の字義範囲解釈** — 決定1〜3 は確定済み。字義を超える拡張（7-4/8-2 への配線・pir2async への展開・6-2 inner-loop の書き換え）は独断で倒さず、follow-up として next-steps に残すに留める
  - **自動生成ファイルの扱い** — implementer.md（`.claude/agents/*.md`）は OpenCode/Codex 同期の SSOT。Edit すると PostToolUse hook が `.codex/agents/implementer.toml` 等を自動再生成する。生成物は手編集しない。**SKILL.md / references/*.md は sync SSOT 外**なので副作用なし（注意点・リスク参照）
- 違反検出の有無: 違反なし（本プランは上記ルールに沿って構成済み）

### 既存パターン照合結果
- 対象1: **reference の命名・粒度** — 既存 `*-check.md`（`destructive-change-check.md` 96 行）が「複数軸の機械チェック + bash + 書き出しフォーマット + ユーザーゲート」の直接の粒度先例。新規 `deterministic-completion-check.md`（`*-check.md` パターン）に切り出し、両 SKILL.md 側は「詳細プロトコル: `path` を参照。要点: …」の定型で締める。→ **合致**
- 対象2: **ステップ番号体系** — `6-0`/`6-1`/`6-2` は `## ステップ 6:` 配下の `###` サブ見出し連番。`### 6-3: 決定論的完了検証` を `### 6-2`（pir2 SKILL.md 現 296-302 行）直後・`### 完了後`（現 304 行）直前に挿入。番号体系上 6-3 は必然的に 6.5 より先に実行される（捏造の可能性がある注意点を土台にユーザー判断を積まない設計意図と整合）。→ **合致**
- 対象3: **変更ファイル報告見出し** — `implementer.md` 95 行に `### 変更ファイル一覧` 固定見出し。各行 `` - `path` — 概要 ``。**pir2codex も同フォーマットでスキル本体が implementation-*.md を Write する**（pir2codex SKILL.md 174 行「implementer.md フォーマットに合わせて書き出す」）。したがって抽出 bash は両 workflow で同一。→ **合致**（Codex free-form 報告の正規化仕様のみ reference に追記）
- 対象4: **ユーザーゲートの様式** — `continuation-gate.md` / `destructive-change-check.md` の「発動条件 → 提示フォーマット → 運用ルール（Auto mode 例外・記録先 `user-decisions.md`）」3段構成に倣う。→ **合致**

### 構造投資領域・状態機械・対称ペア・index 判定（該当性）
- **構造投資領域**: reference 群（17+ ファイル）は「発動条件→bash→フォーマット→運用ルール」の同型ドキュメント・ファミリー（N≥3）。6-3 はその N+1 番目として既存書き味で追加（逸脱なし）
- **状態機械での表現確認**: 該当なし（ワークフロー定義文書の追加で、状態機械の遷移変更ではない）
- **対称ペア配置対称性チェック**: 部分該当。pir2 ↔ pir2codex は「Claude 実装 ↔ Codex 実装」の対称ワークフローペア。今回は**両側に同一 reference を配線**して対称性を取る（片側だけに検証を入れない）。配置は既存慣習どおり `pir2/references/` 配下に共通 reference を1点新設し、pir2codex からもフルパス参照（pir2codex は既に多数の pir2 reference をフルパス参照する既存慣習）
- **index 必要性判定**: 該当なし（DB スキーマ変更なし）

### v1 判断白紙化チェック（3.3・`PLAN_STRATEGY_CHANGED=true`）

決定2 が (A)→(B) に切り替わったため、v1 の各判断を v2 前提で白紙化して再評価した。

| # | v1 判断 | v2 前提変化 | v2 再評価結果 | 採用案 |
|---|---|---|---|---|
| 1 | reference 冒頭を「PIR² スキル（/pir2）のステップ 6-3」と限定 | pir2codex 6-1 からも参照される | pir2 専用枠は誤り。「pir2 6-3 / pir2codex 6-1 の共通プロトコル」に一般化が必要 | **共通プロトコル化**（付録A の見出し・前文を修正） |
| 2 | 適用対象 actor = implementer-subagent/shards/sequential + `main` スキップ | pir2codex には `main` が無く全て Codex（codex-single/shards/sequential） | actor リストに codex 系を追加。`main` スキップは pir2 のみ。pir2codex は常時適用 | **actor リスト拡張** |
| 3 | 検証の情報源 = implementation-*.md の `### 変更ファイル一覧` | pir2codex は Codex free-form 報告 → スキル本体が同フォーマットで正規化 Write | 抽出 bash は同一（implementation-*.md 経由）。Codex 報告の正規化仕様を追記すれば両立 | **正規化仕様セクション追加**（bash 本体は不変） |
| 4 | 実集合 = `git diff --name-only`（unstaged）+ untracked | pir2codex 旧検証は `git diff --name-only HEAD`（staged+unstaged・**untracked 含まず**） | SSOT §1-3-2 の unstaged+untracked に統一。untracked（Codex 新規作成）の検知が**増える**＝strictly better。staged は Codex apply_patch が stage しない前提で対象外 | **SSOT 準拠に統一**（pir2codex 旧 HEAD 比較を置換） |
| 5 | 失敗パス「implementer を再実行」 | pir2codex は Codex codex-reply / 新セッション | actor 非依存に一般化 | **再実行を actor 非依存化** |
| 6 | PHANTOM_RETRY_COUNT の init/report は pir2 SKILL.md のみ | pir2codex にも 6-3 相当が入る | pir2codex ステップ6 init + ステップ12 サマリーにも波及が必要 | **pir2codex にも配線** |
| 7 | 決定1=配線点 6-1 のみ | 変化なし（確定） | 変化なし。pir2codex 側も対称に 6-1（初回実装）のみ配線し、6-2 inner-loop の既存 git diff 検証は据え置き | **6-1 のみ（両 workflow 対称）** |
| 8 | 決定3=implementer.md へ NO_OP マーカー | 変化なし（確定） | NO_OP は Codex 実装でも成立（Codex が「編集不要」報告→スキル本体が implementation-*.md に `NO_OP_JUSTIFIED` を書く）ため reference の NO_OP 節を actor 非依存記述に | **implementer.md 追記 + NO_OP 節を actor 非依存化** |
| 9 | pir2codex = スコープ外 | (B) で共通化スコープ内 | pir2codex 6-1「git diff で実体検証（必須）」を共通 reference 参照に書き換え。重複解消 | **pir2codex 6-1 書き換え** |

> 後付け正当化のサイン点検: 「pir2codex を触ると破壊変更だから避けたい」は成立しない（6-1 の実体検証 bullet を reference 参照に差し替えるだけで、既存フローは温存＝dead code を残さない置換）。「v1 でスコープ外と決めたから」も v2 前提（ユーザーが (B) を明示選択）で無効。

### 実装ステップ

> グループ A（pir2 側）とグループ B（pir2codex 側）に分けて記載。1 は共通の新規 reference で両グループが依存する。

#### グループ A: pir2 側

1. **新規 reference の作成**: `/Users/kawasetakumi/dotfiles/.claude/skills/pir2/references/deterministic-completion-check.md` を新規 Write。内容は本プラン末尾「付録A: reference 全文ドラフト」を**逐語で**書き出す（implementer は独自の簡略化・フォールバック追加をしない）。付録A は pir2 / pir2codex 共通プロトコルとして generalize 済み。

2. **pir2 SKILL.md — ステップ 6 冒頭カウンタ初期化に `PHANTOM_RETRY_COUNT` を追加**: `/Users/kawasetakumi/dotfiles/.claude/skills/pir2/SKILL.md` 現 269 行を以下に変更:
   ```
   `INNER_LOOP_COUNT = 0`、`OUTER_LOOP_COUNT = 0`、`PHANTOM_RETRY_COUNT = 0` から開始してください。
   ```

3. **pir2 SKILL.md — 6-1 に pre-set 記録の指示を追加**: `### 6-1: implementer 起動`（現 279-294 行）の implementer 起動プロンプト列挙の**直前**に、以下を追加（`IMPLEMENTATION_ACTOR` が `main` 以外のときのみ実行）:
   ```
   > **6-3 用 pre-set 記録（`IMPLEMENTATION_ACTOR` が `main` 以外のとき、implementer 起動の直前に必ず実行）**: 決定論的完了検証（6-3）の基準スナップショットとして、implementer 起動前の作業ツリー dirty 集合を記録する。手順は `~/.claude/skills/pir2/references/deterministic-completion-check.md`「pre-set 記録」を参照。`main` 実装時は 6-3 自体を適用しないため記録も不要。shard/sequential 時も pre-set はこの1回（並列/直列起動の直前）のみ記録する。
   ```

4. **pir2 SKILL.md — 新ステップ 6-3 の挿入**: `### 6-2: 統合確認`（現 296-302 行、末尾「implementer から実装要約を受け取ってください。」）と `### 完了後`（現 304 行）の**間**に、以下を挿入:
   ```
   ### 6-3: 決定論的完了検証（`IMPLEMENTATION_ACTOR` が `main` 以外のとき必須）

   詳細プロトコル: `~/.claude/skills/pir2/references/deterministic-completion-check.md` を参照（適用対象 actor / pre-set・post-set 記録 bash / 集合照合規則 PHANTOM_CLAIM・UNDECLARED_CHANGE・NO_OP 免除 / 判定結果書き出し / 失敗パスのユーザーゲート）。本 reference は pir2 6-3 と pir2codex 6-1 の共通プロトコル。

   要点: implementer 完了報告（および 6-2 統合確認）の直後、reviewer 起動（ステップ7）より前に、`implementation-{IMPL_INDEX}*.md` の `### 変更ファイル一覧` から抽出した申告集合 CLAIMED と、6-1 で記録した pre-set からの git delta を純 bash で集合照合する。**PHANTOM_CLAIM（申告したが実際は dirty でないファイルがある／編集想定タスクなのに申告も変更も空で `NO_OP_JUSTIFIED` 宣言なし）は hard fail**。検出時は検証レポート `{RUN_DIR}/verify-{IMPL_INDEX}.md` を逐語注入して implementer を **1 回だけ**再実行（`IMPL_INDEX` と `PHANTOM_RETRY_COUNT` をインクリメント）し再検証する。**2 回目も PHANTOM なら reviewer を起動せずユーザーゲート**（捏造の上にレビューを積まない）。UNDECLARED_CHANGE（申告外の dirty。formatter/生成物副作用等）は warn として `{RUN_DIR}/verify-{IMPL_INDEX}.md` に記録し報告に含めるが**非ブロッキング**。`IMPLEMENTATION_ACTOR=main` は自己申告境界が存在しないため本ステップをスキップする。

   #### 完了後
   ステップ 5.6-2 に従い `{RUN_DIR}/next-steps.md` の「ステップ 6-3」checkbox を `[x]` に更新する（PHANTOM 再実行で `IMPL_INDEX` が増えた場合も最初の 1 回のみマークし、詳細は「中断・再開ログ」に追記）。`main` でスキップした場合も `[x]`（「main のためスキップ」と付記）。
   ```

5. **next-steps-queue.md — 初期テンプレートに checkbox 追加**: `/Users/kawasetakumi/dotfiles/.claude/skills/pir2/references/next-steps-queue.md` 現 22 行（`- [ ] ステップ 6: implementer 起動 (IMPL_INDEX=01)`）の**直後**に 1 行追加:
   ```
   - [ ] ステップ 6-3: 決定論的完了検証（main 実装時はスキップ）
   ```
   （このテンプレートは pir2 / pir2codex 共通。pir2codex では 6-1 内で実施し、完了後に本 checkbox を `[x]` 化する）

6. **implementation-delegation.md — 相互参照ノート追加**: `/Users/kawasetakumi/dotfiles/.claude/skills/pir2/references/implementation-delegation.md` の「shard 統合確認」節（現 57-65 行、`5. 問題がなければ reviewer へ進む` の直後）と「unit 統合確認」節（現 103-110 行、`4. 問題がなければ reviewer へ進む` の直後）のそれぞれに、以下の相互参照を追加:
   ```
   > ℹ️ ここ（6-2）は shard/unit 境界の **LLM 層の整合レビュー**（命名不整合・重複抽象・未接続の検出）。申告集合 vs 実 git diff の **決定論的 claim-vs-diff 集合照合**（PHANTOM_CLAIM / UNDECLARED_CHANGE）は 6-3（`~/.claude/skills/pir2/references/deterministic-completion-check.md`）が担い、デフォルト actor（pir2 の implementer-subagent）および Codex actor（pir2codex）を含む全実装 actor に適用する。6-3 は本節（shard/sequential 限定）の「一般化」であり、両者は別レイヤーで補完し合う。
   ```

7. **pir2 SKILL.md — ステップ12 最終サマリーに検証結果ブロック追加**: 現 527-530 行の「### レビュー結果」ブロック（末尾は現 530 行 `- [主な指摘事項があれば記載]`）の**直後**・現 532 行「### リファクタ提案」の**直前**に以下を挿入:
   ```
   ### 決定論的完了検証（6-3）
   - PHANTOM_CLAIM: [検出なし / 検出→再実行1回で解消 / 検出→再失敗でユーザーエスカレーション / main のためスキップ]
   - UNDECLARED_CHANGE: [なし / N 件（非ブロッキング・{RUN_DIR}/verify-*.md に記録）]
   - PHANTOM_RETRY_COUNT: [回数]
   ```

8. **implementer.md へ NO_OP_JUSTIFIED マーカー追記（決定3=A）**: `/Users/kawasetakumi/dotfiles/.claude/agents/implementer.md`「実装完了レポートのフォーマット」（現 90-105 行）のコードブロック（現 105 行 ` ``` ` で閉じる）の**直後**に、付録B の 1 段落を追記する。**この編集は `.claude/agents/*.md`＝OpenCode/Codex 同期 SSOT なので PostToolUse hook が `.codex/agents/implementer.toml` 等を自動再生成する**（注意点・リスク参照）。

#### グループ B: pir2codex 側（決定2=B の本体）

9. **pir2codex SKILL.md — ステップ 6 冒頭カウンタ初期化に `PHANTOM_RETRY_COUNT` を追加**: `/Users/kawasetakumi/dotfiles/.claude/skills/pir2codex/SKILL.md` 現 108 行を以下に変更:
   ```
   `INNER_LOOP_COUNT = 0`、`OUTER_LOOP_COUNT = 0`、`PHANTOM_RETRY_COUNT = 0` から開始してください。
   ```

10. **pir2codex SKILL.md — 6-1 に pre-set 記録の指示を追加**: `### 6-1: Codex wrapper Agent の起動（共通プロトコル）` の本文（現 127-135 行）の直後・`#### wrapper Agent への指示テンプレート`（現 137 行）の**直前**に、以下の小見出し＋指示を挿入:
    ```
    #### wrapper 起動前の pre-set 記録（決定論的完了検証 6-3 用・必須）

    Codex wrapper（6-1a/6-1b/6-1c いずれか）を起動する **前** に、決定論的完了検証（共通プロトコル `~/.claude/skills/pir2/references/deterministic-completion-check.md`「pre-set 記録」）の基準スナップショットを記録する。codex-shards の並列起動時・codex-sequential の直列起動時も、pre-set はこの1回（初回起動の直前）のみ記録する。pir2codex には `main` actor が存在しない（全て Codex）ため本記録は常時実行する。
    ```

11. **pir2codex SKILL.md — 6-1「wrapper 返り後のスキル本体の処理」の実体検証を共通 reference 参照に置換**: 現 170-174 行の `#### wrapper 返り後のスキル本体の処理（共通）` の bullet 1・bullet 3 を以下に**書き換える**（重複解消。旧「git diff --stat/--name-only HEAD 実体検証」を dead に残さない）:
    - bullet 1（現 172 行）を次に置換:
      ```
      1. **決定論的完了検証（6-3・必須）**: 共通プロトコル `~/.claude/skills/pir2/references/deterministic-completion-check.md` に従い、Codex の申告変更ファイル集合（CLAIMED）と 6-1 pre-set からの実 git delta（unstaged + untracked）を集合照合し、PHANTOM_CLAIM（hard fail）/ UNDECLARED_CHANGE（warn）を判定する。Codex の自己申告を信じない（CLAUDE.md「ツール結果の捏造の絶対禁止」と同根。Codex も自己申告しうる）。PHANTOM 検出時の再実行1回→再失敗ユーザーゲートも同 reference の「失敗パス」に従う（再実行は Codex codex-reply または新セッション）。プラン外への波及（プラン範囲逸脱）の意味的判断は決定論層の対象外で、後段 reviewer（ステップ7）が拾う。
      ```
    - bullet 3（現 174 行）を次に置換（正規化の明示を追加）:
      ```
      3. **implementation レポートを Write**: `{RUN_DIR}/implementation-{IMPL_INDEX}.md`（shard 時 `-{SHARD_ID}`、unit 時 `-unit-{UNIT_ID}`）に、Codex の変更ファイル一覧＋実装概要＋注意点を `~/.claude/agents/implementer.md`「実装完了レポートのフォーマット」に合わせて書き出す。**Codex の変更ファイル報告（markdown 構造未指定）は、`deterministic-completion-check.md`「Codex 報告の正規化」に従って `### 変更ファイル一覧` の `` - `<リポ相対パス>` — <概要> `` 行に整形して書く**（6-3 の抽出 bash が pir2 と同一に機能するため）。Codex が「編集不要」と報告した場合は `### 注意点・未解決事項` に `NO_OP_JUSTIFIED: <理由>` を明記する（6-3 の NO_OP 免除）。
      ```
    - bullet 2（threadId 保持・現 173 行）は**変更しない**。

12. **pir2codex SKILL.md — ステップ12 最終サマリーに検証結果ブロック追加**: 現 275-278 行の「### レビュー結果」ブロック（末尾は現 278 行 `- [主な指摘事項]`）の**直後**・現 280 行「### リファクタ提案（refactor-advisor）」の**直前**に以下を挿入:
    ```
    ### 決定論的完了検証（6-3）
    - PHANTOM_CLAIM: [検出なし / 検出→再実行1回で解消 / 検出→再失敗でユーザーエスカレーション]
    - UNDECLARED_CHANGE: [なし / N 件（非ブロッキング・{RUN_DIR}/verify-*.md に記録）]
    - PHANTOM_RETRY_COUNT: [回数]
    ```

> **pir2codex 6-2（inner-loop 再実装・現 196-199 行）は変更しない**。決定1=(A) 最小スコープに従い、初回実装点（6-1）のみ共通 reference を配線する。6-2 の既存「返り後に git diff 検証」は軽量自己チェックとして据え置く（pir2 で 7-4/8-2 に 6-3 を配線しないのと対称）。

### USER_DECISION_REQUIRED
- **なし**。決定1（配線点 6-1 のみ）/ 決定2（pir2codex 共通化 = B）/ 決定3（NO_OP マーカー = A）は確定済み。本 v2 再策定で新たに人間判断を要する新規論点は発生していない（pir2codex 側の配線は決定1・決定2 の帰結として一意に定まる — 初回実装点のみ・共通 reference 参照・正規化仕様追記）。

### 全適用箇所リスト（今回の配線先。決定1=(A) により初回実装点のみ）
- 共通 reference: `.claude/skills/pir2/references/deterministic-completion-check.md`（新規）
- pir2 配線先: `.claude/skills/pir2/SKILL.md` — 6-1 pre-set（現 279 行付近）/ 6-3 挿入（現 296-304 行の間）/ step6 init（269 行）/ step12（527-532 行の間）
- pir2codex 配線先: `.claude/skills/pir2codex/SKILL.md` — 6-1 pre-set（現 127-137 行の間）/ 6-1 返り後処理の bullet1・bullet3 置換（現 170-174 行）/ step6 init（108 行）/ step12（275-280 行の間）
- 波及: `.claude/skills/pir2/references/next-steps-queue.md`（22 行直後）/ `.claude/skills/pir2/references/implementation-delegation.md`（57-65・103-110 行）/ `.claude/agents/implementer.md`（105 行直後）
- **配線しない（follow-up 候補）**: pir2 7-4/8-2/6.5-2(C)/refactor-advisor-gate、pir2codex 6-2 inner-loop、pir2async・debug・ir

### テスト・検証方法
本タスクはワークフロー定義文書（SKILL.md / references / agent 定義）の編集で、プロジェクトに自動テストスイートはない。役割分担に従い分離する。
- **追加/更新が必要なテストファイル**: なし（テストスイート非対象のリポジトリ）
- **implementer が自己検証すべき項目**（静的検証・存在確認のみ。テスト実行は含めない）:
  - 新規 `deterministic-completion-check.md` が Write されたことを Read で確認（見出し構成が付録A と一致・pir2/pir2codex 両対応の記述があること）
  - reference 内の bash スニペットを一時ファイルに落として `bash -n <tmpfile>` で構文エラー 0 を確認（`comm` / `sed` / `git` の引用崩れ検知）
  - 両 SKILL.md の 6-3/6-1 参照リンク（`~/.claude/skills/pir2/references/deterministic-completion-check.md`）が実在パスを指すことを `test -f` で確認
  - `PHANTOM_RETRY_COUNT` が pir2 SKILL.md の（step6 init・step12）両方、および pir2codex SKILL.md の（step6 init・step12）両方に出現することを `grep -c` で確認（片側漏れ検知）
  - next-steps-queue.md 初期テンプレートに「ステップ 6-3」checkbox 行が 1 件追加されたことを `grep` で確認
  - implementation-delegation.md の shard 統合確認・unit 統合確認の両節に相互参照ノートが入ったことを `grep` で確認
  - pir2codex SKILL.md 現 170-174 行の旧「git diff --stat HEAD / git diff --name-only HEAD 実体検証」表現が**残っていない**ことを `grep -n 'git diff --name-only HEAD' SKILL.md` 等で確認（置換漏れ＝dead code 温存の検知）
  - implementer.md 編集後、PostToolUse hook が `.codex/agents/implementer.toml` を再生成したことを `git status` で確認（生成物 diff は手編集しない）
- **tester が実行する最小スコープのテストコマンド**: なし（動作テスト対象コードなし）。tester には任意で「reference 内 bash スニペットを実データ（本 run の `implementation-*.md` と `git` 出力）に対して 1 回ドライラン実行し、PHANTOM/UNDECLARED の集合照合が期待どおり空リストを返すか」の確認のみ最小スコープで申し送る。

### 注意点・リスク
- **pir2codex の実集合定義変更（HEAD 比較 → unstaged+untracked）**: pir2codex 旧 6-1 は `git diff --name-only HEAD`（staged+unstaged・untracked を含まない）。共通 reference は SSOT §1-3-2 の `git diff --name-only`（unstaged）+ `git ls-files --others --exclude-standard`（untracked）に統一する。結果、**Codex が新規作成した untracked ファイルの検知が増える（strictly better）**一方、staged 集合は対象外になる。Codex（apply_patch）は通常 stage しないため実害はないが、この差は意図的な設計変更である旨を reviewer に申し送る。
- **implementer.md 編集の同期副作用（実装ステップ8）**: `.claude/agents/implementer.md` は OpenCode/Codex 同期 SSOT。Edit で PostToolUse hook が `.codex/agents/implementer.toml`（リポ内）と `~/.config/opencode/agents/implementer.md`（リポ外・git 非追跡）を自動再生成する。リポ内 `.codex/agents/implementer.toml` の diff は**想定内**。手編集禁止。**SKILL.md / references/*.md は sync SSOT 外**なので副作用は発生しない（実装ステップ 1-7・9-12 は sync を誘発しない）。
- **pre-set のスナップショット規則**: pre-set/post-set は `git diff --name-only`＋untracked。`.ai-pir-runs/` は `.gitignore` 済みなので RUN_DIR 内の中間ファイルは untracked 集合に混入せず自己汚染しない。pir2 起動時点で既に dirty なファイルは pre-set に入るため delta から自然に除外される。
- **UNDECLARED の非ブロッキング性**: formatter・lockfile・コード生成物の副産物が申告外 dirty として出るのは正常。UNDECLARED は warn 止まり（hard fail は PHANTOM のみ）。偽陽性で実験を殺さない非対称検証（設計 SSOT の反論3 応答）に忠実。
- **6-2 と 6-3 の非重複性**: 6-2（shard/sequential 限定・LLM 層の境界整合レビュー）と 6-3（全実装 actor・決定論層の集合照合）は検証対象が異なる別レイヤー。相互参照ノートで棲み分けを明示し dead code 化・重複を回避。
- **Codex 正規化の失敗耐性**: Codex 報告が空・パス抽出不能の場合、スキル本体が `### 変更ファイル一覧` を「なし」で書くと 6-3 は「claimed 空」判定になる。実際に Codex が変更していれば delta 非空 → UNDECLARED（warn）で拾える。実際に変更していなければ PHANTOM（NO_OP 宣言なし）で hard fail。どちらも検証網に掛かる（正規化失敗が sink しない）。
- **パス正規化**: 申告集合の path は絶対パス混入に備え `sed -E "s|^$PROJECT_ROOT/||"` でリポ相対に正規化してから `comm` 照合する（付録A に反映済み）。

### スキル本体への追加調査依頼 / follow-up（next-steps 相当・本 run では実施しない）
- 6-3 を再実装ポイント（pir2 7-4/8-2/6.5-2(C)/refactor-advisor-gate、pir2codex 6-2）へ一般化する案。
- pir2async・debug・ir の同型 implementer→reviewer 境界への 6-3 展開要否（explorer-01/02 が未調査と申し送り済み）。展開時は別途 explorer 起動を推奨。

### EXPLORATION_NEEDED
- なし（挿入位置・pre-set 配線点・pir2codex 6-1 実体検証箇所・Codex 報告フォーマット・reference 命名・implementer フォーマット・両 SKILL.md の step6/step12 構造はすべて exploration-01/02 と本プランの補助 Read で確定済み）。

---

## 付録A: `references/deterministic-completion-check.md` 全文ドラフト（implementer は逐語で Write）

> 下記の 4 バッククォート ` ````markdown ` フェンスの**内側全体**を、そのまま新規ファイルとして Write する（内側の 3 バッククォート bash ブロックは実ファイルではそのまま 3 バッククォートで書く）。`PROJECT_ROOT` / `RUN_DIR` / `IMPL_INDEX` はスキル本体がステップ1・6 で確定済みの変数を使う。

````markdown
# 決定論的完了検証（共通プロトコル: pir2 6-3 / pir2codex 6-1）

PIR² 系スキルの実装完了検証。実装 actor（Claude implementer / Codex）の **自己申告した変更ファイル集合** と **実 git の変更集合** を純 bash で集合照合し、捏造（PHANTOM_CLAIM）と未申告変更（UNDECLARED_CHANGE）を決定論検出する機械ゲート。

- **/pir2**: ステップ「6-3: 決定論的完了検証」として、implementer 完了報告の直後・reviewer 起動（ステップ7）より前にスキル本体が実施する。
- **/pir2codex**: ステップ 6-1「wrapper 返り後のスキル本体の処理」の実体検証としてスキル本体が実施する（Codex は自己申告しうるため）。

CLAUDE.md「ツール結果の捏造の絶対禁止」の機構化。既存の shard/sequential 統合確認（`implementation-delegation.md`「shard 統合確認」「unit 統合確認」）は shard/unit 境界の LLM 層レビューだが、本ゲートはその **デフォルト actor（pir2 の implementer-subagent）および Codex actor（pir2codex）への一般化**であり、claim-vs-diff の集合一致という決定論層を担う。両者は別レイヤーで補完し合う（新規発明ではなく既存先例の一般化）。

## 適用対象 actor

- **適用する（/pir2）**: `implementer-subagent` / `implementer-shards` / `implementer-sequential`（いずれもサブエージェントが `implementation-{IMPL_INDEX}*.md` に自己申告を書く＝telephone-game 境界がある）
- **適用する（/pir2codex）**: `codex-single` / `codex-shards` / `codex-sequential`（Codex が自己申告し、スキル本体が implementation-*.md に正規化 Write する）。pir2codex には `main` actor が存在しないため常時適用。
- **スキップする**: `/pir2` の `IMPLEMENTATION_ACTOR=main`（スキル本体が直接編集。自己申告境界が存在しないため照合対象がない）

## 検証の情報源

- **申告集合 CLAIMED**: `{RUN_DIR}/implementation-{IMPL_INDEX}*.md` の `### 変更ファイル一覧` セクションの各 `` - `path` `` 行
  - subagent / codex-single: `implementation-{IMPL_INDEX}.md`
  - shards: `implementation-{IMPL_INDEX}-*.md`（全 shard の和集合）
  - sequential: `implementation-{IMPL_INDEX}-unit-*.md`（全 unit の和集合）
- **実集合**: 作業ツリーの dirty 集合 = `git diff --name-only`（unstaged 変更）＋ `git ls-files --others --exclude-standard`（untracked）。staged 集合は対象外（implementer / Codex はステージング操作をしない前提。設計 SSOT §1-3-2 準拠）。

### Codex 報告の正規化（/pir2codex のみ）

Codex は「変更ファイル一覧」を **markdown 構造未指定の free-form** で報告する。スキル本体は implementation-*.md を Write する際、Codex 報告から各パスを抽出し以下で正規化して `` - `<リポ相対パス>` — <概要> `` 行として `### 変更ファイル一覧` に書き出す（これにより下記の抽出 bash が /pir2 と同一に機能する）:

- git status 風プレフィックス（`M ` / `A ` / `D ` / `?? ` / `R old -> new` 等）を除去する。rename（`R old -> new`）は **new path** を採用する。
- 先頭の箇条書き記号（`- ` / `* ` / `1. `）・囲みバッククォート・引用符を除去する。
- 絶対パスは `$PROJECT_ROOT/` を剥がしてリポ相対にする。
- 1 行 1 パス・重複除去する。概要が取れない場合は `— (Codex 報告より)` 等のプレースホルダで可（照合はパスのみ使う）。
- Codex が「編集不要（no-op）」と報告した場合は `### 変更ファイル一覧` を「なし」とし、`### 注意点・未解決事項` に `NO_OP_JUSTIFIED: <理由>` を明記する。

## pre-set 記録（実装 actor 起動の直前に実行）

実装 actor（implementer / Codex wrapper）を起動する **前** に、基準スナップショットを記録する（/pir2 の `IMPLEMENTATION_ACTOR=main` のときは記録しない。/pir2codex は常時記録）:

```bash
{ git -C "$PROJECT_ROOT" diff --name-only
  git -C "$PROJECT_ROOT" ls-files --others --exclude-standard
} | sort -u > "$RUN_DIR/verify-${IMPL_INDEX}-pre.list"
```

> 起動時点で既に dirty なファイルはここに含まれ、後段の delta から自然に除外される（この実装 actor 起動での変更だけを delta が表す）。`.ai-pir-runs/` は .gitignore 済みなので RUN_DIR 内の中間ファイルは untracked に混入しない。shard 並列 / unit 直列時も pre-set はこの1回（初回起動の直前）のみ記録する。

## post-set 記録・delta 計算・CLAIMED 抽出（実装 actor 完了後）

```bash
# 1. post-set（完了後の dirty 集合）
{ git -C "$PROJECT_ROOT" diff --name-only
  git -C "$PROJECT_ROOT" ls-files --others --exclude-standard
} | sort -u > "$RUN_DIR/verify-${IMPL_INDEX}-post.list"

# 2. delta = post - pre（この実装 actor 起動で新たに dirty になったファイル）
comm -13 "$RUN_DIR/verify-${IMPL_INDEX}-pre.list" \
        "$RUN_DIR/verify-${IMPL_INDEX}-post.list" \
  > "$RUN_DIR/verify-${IMPL_INDEX}-delta.list"

# 3. CLAIMED 抽出（全 implementation レポートの「### 変更ファイル一覧」→ 次の ### まで）
for f in "$RUN_DIR"/implementation-${IMPL_INDEX}*.md; do
  [ -f "$f" ] || continue
  sed -n '/^### 変更ファイル一覧/,/^### /p' "$f" | grep -E '^- *`'
done \
  | sed -E 's/^- *`([^`]+)`.*/\1/' \
  | sed -E "s|^$PROJECT_ROOT/||" \
  | sort -u > "$RUN_DIR/verify-${IMPL_INDEX}-claimed.list"

# 4. PHANTOM 候補 = claimed に在るが post に無い（申告したが実際は dirty でない）
comm -23 "$RUN_DIR/verify-${IMPL_INDEX}-claimed.list" \
        "$RUN_DIR/verify-${IMPL_INDEX}-post.list" \
  > "$RUN_DIR/verify-${IMPL_INDEX}-phantom.list"

# 5. UNDECLARED 候補 = delta に在るが claimed に無い（実際に変わったが申告に無い）
comm -23 "$RUN_DIR/verify-${IMPL_INDEX}-delta.list" \
        "$RUN_DIR/verify-${IMPL_INDEX}-claimed.list" \
  > "$RUN_DIR/verify-${IMPL_INDEX}-undeclared.list"
```

## 集合照合規則（判定）

| 条件 | 判定 | 扱い |
|---|---|---|
| `phantom.list` が非空（申告したが実際は dirty でないファイルがある） | **PHANTOM_CLAIM** | hard fail |
| `claimed.list` が空 かつ `delta.list` が空 かつ NO_OP 免除なし（編集想定タスクなのに何も申告せず何もしていない） | **PHANTOM_CLAIM** | hard fail |
| `undeclared.list` が非空（申告外の dirty） | **UNDECLARED_CHANGE** | warn（非ブロッキング） |
| `claimed.list` が空 かつ `delta.list` が非空 | **UNDECLARED_CHANGE** | warn（非ブロッキング） |
| 上記いずれも該当せず | **PASS** | reviewer（/pir2 ステップ7）/ 後続処理へ進む |

- PHANTOM_CLAIM と UNDECLARED_CHANGE は同時に成立しうる（PHANTOM が優先＝hard fail）。
- UNDECLARED は formatter・lockfile・コード生成物の副産物で正常に発生しうるため warn 止まり。hard fail は PHANTOM のみ（偽陽性で実験を殺さない非対称検証）。

### NO_OP 免除

`claimed.list` が空 かつ `delta.list` が空のとき、以下で免除判定する:

```bash
if grep -q 'NO_OP_JUSTIFIED' "$RUN_DIR"/implementation-${IMPL_INDEX}*.md 2>/dev/null; then
  NO_OP_JUSTIFIED=1   # 実装 actor が「編集不要」を明示宣言 → PHANTOM 免除・PASS 扱い
else
  NO_OP_JUSTIFIED=0   # 宣言なし → PHANTOM_CLAIM（hard fail）
fi
```

- /pir2: implementer は編集不要と判断した場合、実装完了レポートの `### 注意点・未解決事項` に `NO_OP_JUSTIFIED: <理由>` を明記する（`~/.claude/agents/implementer.md`「実装完了レポートのフォーマット」参照）。
- /pir2codex: Codex が「編集不要」と報告した場合、スキル本体が implementation-*.md の `### 注意点・未解決事項` に `NO_OP_JUSTIFIED: <理由>` を明記する（上記「Codex 報告の正規化」）。

## 判定結果の書き出し

判定結果を `{RUN_DIR}/verify-{IMPL_INDEX}.md` に書き出す:

```markdown
# 決定論的完了検証（IMPL_INDEX=NN）

- actor: <implementer-subagent / implementer-shards / implementer-sequential / codex-single / codex-shards / codex-sequential>
- CLAIMED: <claimed.list の件数> 件
- delta（実変更）: <delta.list の件数> 件
- 判定: <PASS / PHANTOM_CLAIM / UNDECLARED_CHANGE（warn）>

## PHANTOM（申告したが実体なし）
<phantom.list の内容 or "なし">

## UNDECLARED（実変更だが申告なし）
<undeclared.list の内容 or "なし">
```

## 失敗パス（PHANTOM_CLAIM 検出時）

1. `PHANTOM_RETRY_COUNT` を確認する。
2. **1 回目の PHANTOM（`PHANTOM_RETRY_COUNT == 0`）**: `IMPL_INDEX` と `PHANTOM_RETRY_COUNT` をインクリメントし、実装 actor を **1 回だけ**再実行する。再実行プロンプトに `{RUN_DIR}/verify-{直前 IMPL_INDEX}.md`（検証レポート）のパス／全文を渡し、「申告したが実際には変更されていない以下のファイルを実際に編集せよ、または申告を実体に一致させよ」と**原因を逐語注入**する（ブラインドリトライではない＝原因が特定済み）。
   - /pir2: implementer サブエージェントを再起動。
   - /pir2codex: Codex を `codex-reply`（同 threadId で実装文脈を保つ）または新 Codex セッションで再実行。
   - 再起動後、pre-set は据え置き（同じ基準で再照合）し post-set から再計算する。`INNER_LOOP_COUNT` は増やさない（reviewer FAIL ループとは別系統）。
3. **2 回目も PHANTOM（`PHANTOM_RETRY_COUNT >= 1`）**: **reviewer を起動せず**、以下のユーザーゲートを開く（捏造の上にレビューを積まない）。CLAUDE.md「ブラインドリトライ禁止」（初回＋再試行1回＝計2回で停止）と整合。

### ユーザーゲート（2 回目 PHANTOM 時）

```
## 決定論的完了検証 FAIL — PHANTOM_CLAIM（再実行1回後も未解消）

実装（implementer / Codex）が変更したと申告したが、実際の git 作業ツリーに反映されていないファイルを検出しました。

- 申告集合（CLAIMED）: <claimed.list>
- 実変更集合（delta）: <delta.list>
- 申告のみで実体なし（PHANTOM）: <phantom.list>

以下の実 git 変更を参考にしてください（自動巻き戻しは行いません）:
<git -C "$PROJECT_ROOT" diff の要約（--stat）>

続行方法を選んでください:
- (A) 手動調査してから再開: git diff を確認し原因を特定。追加指示付きで実装 actor を再起動（IMPL_INDEX++）するか手動修正 → 検証を再実行【推奨】
- (B) PHANTOM を承知でそのまま reviewer へ進む（申告漏れ/検証の偽陽性とユーザーが判断した場合のみ）
- (C) ワークフローを中止

[A / B / C]
```

- **補償は `git diff` 全 hunk のユーザー提示のみ。`git restore` / `git checkout -- <file>` による自動巻き戻しは絶対にしない**（CLAUDE.md Git ルール）。PHANTOM は「申告ファイルが dirty でない」状態なので巻き戻す対象自体がなく、提示するのは実際に dirty な変更の実体。
- **Auto mode でも本ゲートはユーザー応答を待つ**（仕様変更判断ゲートのため Auto mode 例外）。
- ゲート発火と選択は `{RUN_DIR}/user-decisions.md` に追記する。

## スキップ条件

- /pir2 の `IMPLEMENTATION_ACTOR=main` のときは本ステップ全体をスキップ（pre-set 記録・照合ともに不要）。next-steps.md の「ステップ 6-3」checkbox は「main のためスキップ」と付記して `[x]` にする。
- /pir2codex はスキップ条件なし（全 actor が Codex 経由で自己申告境界を持つため常時適用）。

## 完了後

/pir2 では ステップ 5.6-2 に従い `{RUN_DIR}/next-steps.md` の「ステップ 6-3」checkbox を `[x]` に更新する。PHANTOM 再実行で `IMPL_INDEX` が増えた場合も最初の 1 回のみマークし、詳細は「中断・再開ログ」に追記する。/pir2codex では 6-1 完了後の checkbox 更新に含める。
````

---

## 付録B: implementer.md への追記（決定3=(A)）

`/Users/kawasetakumi/dotfiles/.claude/agents/implementer.md`「実装完了レポートのフォーマット」（現 90-105 行）のコードブロック（現 105 行の ` ``` ` で閉じる）の**直後**に、以下の 1 段落を追記する:

```
> **無編集完了（no-op）時**: プラン内容が既に満たされている等でコード変更が一切不要と判断した場合は、`### 変更ファイル一覧` を「なし」とし、`### 注意点・未解決事項` に `NO_OP_JUSTIFIED: <理由>` を明記すること。これはスキル本体の決定論的完了検証（pir2 ステップ 6-3 / `~/.claude/skills/pir2/references/deterministic-completion-check.md`）が「申告も変更も空」を捏造（PHANTOM_CLAIM）と誤判定しないための免除マーカー。理由なく変更ゼロで完了報告してはならない。
```

（この追記は `.claude/agents/*.md`＝OpenCode/Codex 同期 SSOT のため、Edit 後に PostToolUse hook が `.codex/agents/implementer.toml` 等を自動再生成する。生成物は手編集しない。）
