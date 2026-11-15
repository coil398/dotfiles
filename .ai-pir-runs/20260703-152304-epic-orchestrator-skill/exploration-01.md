## 探索レポート: epic スキル骨格型の精密抽出

### 関連ファイル一覧

| ファイルパス | 役割・内容 | 参考対象 |
|------------|-----------|---------|
| `/Users/kawasetakumi/dotfiles/.claude/skills/pir2/SKILL.md` | フルスケール PIR² フロー（11 step 以上）| 大規模ワークフローの frontmatter・ステップ採番・references 参照パターン |
| `/Users/kawasetakumi/dotfiles/.claude/skills/pir2codex/SKILL.md` | 下位バリアント（pir2 の Implement 差し替え版） | バリアント frontmatter・既存ステップ参照の書式・差分構造 |
| `/Users/kawasetakumi/dotfiles/.claude/skills/ir/SKILL.md` | 軽量スキル（2 step フロー） | 短いスキルの frontmatter・簡潔な本文構成 |
| `/Users/kawasetakumi/dotfiles/.claude/skills/research/SKILL.md` | 特化ワークフロー（4 フェーズ）| 異なる目的のスキル frontmatter・RUN_DIR 関連の最小化 |

### 【frontmatter の型】三種類スキル比較

#### pir2 の frontmatter（フルスケール、11 フェーズ以上）
```yaml
---
name: pir2
description: コーディングタスクを Plan → Implement → Review → Retrospect の4フェーズで実行する。複雑なタスク・設計が必要なタスク・品質保証が重要なタスク、大きな機能追加・リファクタリング・アーキテクチャ変更に使う。「ちゃんと作りたい」「しっかり実装して」「品質重視で」といった要望にも対応する。ユーザーが /pir2 と入力したら必ずこのスキルを使う。
argument-hint: [タスクの説明]
---
```
**特徴**:
- `description`: 用途明記 + ユーザーインボイス例（「〜といった要望」）
- `argument-hint`: 引数種別を簡潔に示す（正規スキル必須）

**ファイルパス**: `/Users/kawasetakumi/dotfiles/.claude/skills/pir2/SKILL.md` line 1-5

#### pir2codex の frontmatter（バリアント、下位フェーズ差し替え版）
```yaml
---
name: pir2codex
description: PIR² の Codex 実装版。Plan→Review→Retrospect は Claude のまま、Implement フェーズだけ Codex（mcp__codex__codex）に差し替えた実験的ワークフロー。Codex 実装の品質を通常 /pir2 と比較するために使う。大きく結合した実装は IMPLEMENTATION_UNITS による直列 fresh セッション化に対応。ユーザーが /pir2codex と入力したら必ずこのスキルを使う。
argument-hint: [タスクの説明]
---
```
**特徴**:
- `description` で親スキル（pir2）との関係を明記（「PIR² の Codex 実装版」「Implement フェーズだけ差し替え」）
- 実験的ワークフロー・比較目的も一文で明示

**ファイルパス**: `/Users/kawasetakumi/dotfiles/.claude/skills/pir2codex/SKILL.md` line 1-5

#### ir の frontmatter（軽量スキル、2 フェーズ）
```yaml
---
name: ir
description: 軽量な Implement → Review の2フェーズワークフロー。タスクが明確で小さい場合に使う。バグ修正・小機能追加・設定変更・ファイル修正など、計画不要で「サクッとやって」「これ直して」「簡単な変更」といった要望に対応する。ユーザーが /ir と入力したら必ずこのスキルを使う。
argument-hint: [タスクの説明]
---
```
**特徴**:
- `description` で利用シーン・ユースケース例を具体的に（バグ修正・小機能追加）
- 軽量スキルは entry condition を明確に

**ファイルパス**: `/Users/kawasetakumi/dotfiles/.claude/skills/ir/SKILL.md` line 1-5

#### research の frontmatter（特化ワークフロー）
```yaml
---
name: research
description: 研究テーマ・問いを 調査 → 集約 → 思考 → 仮説 の流れで掘り下げる研究ワークフロー。Web とローカルの両方を調べ、事実を集約し、構造分析してから検証可能な仮説を立てる。「研究して」「調べて考えて仮説立てて」「〜について深く掘り下げて」「〜って本当なのか検証したい」「〜の原因を調べて仮説を立てて」といった要望に対応する。コードの実装・バグ修正・デバッグが目的のとき（それは /pir2 や /debug）ではなく、テーマそのものの探究・分析・仮説形成が目的のときに使う。ユーザーが /research と入力したら必ずこのスキルを使う。
argument-hint: [研究テーマ・問い]
---
```
**特徴**:
- 4 フェーズの明示（調査 → 集約 → 思考 → 仮説）
- 非対象用途を明記（「コードの実装・バグ修正・デバッグが目的のときではなく」）
- `argument-hint` が異なる（`[研究テーマ・問い]`）

**ファイルパス**: `/Users/kawasetakumi/dotfiles/.claude/skills/research/SKILL.md` line 1-5

---

### 【本文構造の型】見出し採番と references 外出しパターン

#### pir2 のステップ採番規則

**パターン**:
- 最上位：`# PIR² — Plan → Implement → Review → Retrospect` （見出し色識別用、1 スキルに 1 個）
- 2 レベル見出し（`##`）：ステップ番号を振る
  - `## ステップ 1: プロジェクトメモリパスと RUN_DIR の確定`
  - `## ステップ 2: ブレインストーミング（状況に応じて実施）`
  - `## ステップ 3: 探索フェーズ（explorer）`
  - ...（最大 13 ステップ）

- 3 レベル見出し（`###`）：各ステップ内のサブセクション
  - `### 起動ルール`
  - `### プロンプトに必ず含めるパラメータ`
  - `### 既存パターン逸脱の事前申告`

- 4 レベル見出し（`####`）：さらに細分化（例：Fan-Out Gate の違反パターン）

**ファイルパス引用**: `/Users/kawasetakumi/dotfiles/.claude/skills/pir2/SKILL.md` line 15-563

#### references への外出しパターン

**ルール（pir2）**:
1. **長い詳細プロトコル**は `~/.claude/skills/pir2/references/*.md` に分離
2. **本文は要点のみ残す** + `詳細プロトコル: <path>` 参照を明記

**具体例**:

```markdown
## ステップ 4.5: 能動的再探索ループ（最大5回）

詳細プロトコル: `~/.claude/skills/pir2/references/exploration-loop.md` を参照（収束判定ロジック / ループ本体 / 既存パターン逸脱の事前申告タイミング）。

要点: planner の返り値要約に `### EXPLORATION_NEEDED` の `- topic` が残る間、追加探索 → planner 再起動を最大 5 回繰り返す。...
```

**ファイルパス引用**: `/Users/kawasetakumi/dotfiles/.claude/skills/pir2/SKILL.md` line 150-155

3. **references ファイル一覧**（実際に存在するもの）:
   - `sanitized-cwd.md` — PROJECT_MEMORY_DIR 計算用の SSOT
   - `run-dir-base.md` — RUN_DIR の基底パス定義
   - `implementation-delegation.md` — implementer / shards / sequential / main の判定
   - `exploration-loop.md` — 再探索ループの収束判定
   - `plan-choice-gate.md` — ユーザー確認フロー
   - `destructive-change-check.md` — 破壊的変更判定
   - `feedback-conflict-gate.md` — feedback との矛盾検出
   - `fan-out-gate.md` — reviewer 並列起動の宣言・検出フォーマット
   - `tester-prompt.md` — tester 起動仕様
   - `retrospector-prompt.md` — retrospector 起動仕様
   - `refactor-advisor-gate.md` — リファクタ提案のゲート
   - `continuation-gate.md` — テスト上限時の続行判定
   - `walkthrough-templates.md` — ウォークスルーのフォーマット
   - `next-steps-queue.md` — checkbox キュー管理
   - `handoff-cleanup.md` — handoff.md の後処理
   - `team-member-prompts.md` — チーム実行時の Agent プロンプト

**ファイル物理配置**: `/Users/kawasetakumi/dotfiles/.claude/skills/pir2/references/*.md` （全 16 個）

---

### 【下位スキルの差分構造】pir2codex が pir2 を参照する書式

#### 参照パターン 1: 「完全に同一」型

```markdown
## ステップ 3: 探索フェーズ（explorer）

**/pir2 のステップ 3 と同一**。コードベース探索はメイン Claude が直接行わず、必ず `explorer` を `Agent` ツールで起動（最低1体、独立領域なら最大3体並列、haiku/sonnet/opus 使い分け）。プロンプトに含めるパラメータ・調査観点・git 操作禁止の明示・既存 agent 流用時のロール境界再注入は /pir2 ステップ3に従う。
```

**特徴**:
- 冒頭に `**/pir2 のステップ N と同一**` と明記
- 具体的な詳細（パラメータ・注意点）を箇条書きで簡潔に再掲
- 長い内容は参照先ファイルに委譲（「/pir2 ステップ 3 に従う」）

**ファイルパス引用**: `/Users/kawasetakumi/dotfiles/.claude/skills/pir2codex/SKILL.md` line 54-57

#### 参照パターン 2: 「差分あり」型（Implement フェーズ）

```markdown
## ステップ 6: 実装（Codex）★ pir2codex の差分本体

ここが通常 /pir2 との唯一の実質差分です。implementer サブエージェント（Claude）の代わりに **Codex セッション（`mcp__codex__codex`）が実装**します。

### 6-0: 実装 actor の決定（Codex 版マッピング）

通常 /pir2 と同じ判定ロジック（`~/.claude/skills/pir2/references/implementation-delegation.md`）で actor を決めるが、**実装主体は Claude implementer ではなく Codex セッション**になる。マッピング:

| /pir2 の actor | pir2codex での実体 |
|---|---|
| `implementer-subagent` | **codex-single**: Codex 1 セッション |
| `implementer-shards` | **codex-shards**: 独立 shard ごとに Codex セッション（最大3） |
| `implementer-sequential` | **codex-sequential**: unit ごとに新しい Codex セッション |
| `main` | **codex-single に倒す** |
```

**特徴**:
- `★ pir2codex の差分本体` というマーク付き
- 「通常 /pir2 と同じ判定ロジック（参照 URL）」で親との関係を明記
- 差分内容を表で明確化
- 親ステップ再掲と差分部分の明確な分離

**ファイルパス引用**: `/Users/kawasetakumi/dotfiles/.claude/skills/pir2codex/SKILL.md` line 106-125

#### 参照パターン 3: 「同じステップを reference で参照」型

```markdown
## ステップ 7: レビューループ（reviewer ハイブリッド並列、最大3回）

**/pir2 のステップ 7 と同一**（reviewer は Claude のまま＝Codex 実装を Claude が異種レビュー）。`REVIEWER_SET` 決定（デフォルト全5観点）→ **7-2A Fan-Out Gate 宣言 → 7-2B 並列発火**（詳細: `~/.claude/skills/pir2/references/fan-out-gate.md`）→ 7-3 VERDICT 集約 → 7-4 判定。

7-4 で FAIL かつ `INNER_LOOP_COUNT < 3` の場合の再実装は **ステップ 6-2（Codex codex-reply / codex-single）** で行う...
```

**特徴**:
- 冒頭に親スキルとの同一性を宣言
- 部分的な差分（「reviewer は Claude のまま」「再実装は Codex」）を括弧書きで注記
- `詳細: <reference>` で共有 SSOT を指す

**ファイルパス引用**: `/Users/kawasetakumi/dotfiles/.claude/skills/pir2codex/SKILL.md` line 213-218

---

### 【Agent ツール起動パターン】各スキルでのサブエージェント起動書式

#### ステップ冒頭での起動宣言（pir2 例）

```markdown
## ステップ 3: 探索フェーズ（explorer）

コードベース探索はメイン Claude が **直接** Glob/Grep/Read で行ってはならない。必ず `explorer` エージェントを `Agent` ツールで起動し、調査を委譲してください。

### 起動ルール

- **最低1体起動**: タスクの規模にかかわらず初回探索は必須
- **最大3体並列**: 調査領域が独立している場合のみ並列起動
- **モデル使い分け**:
  - `haiku`: 広く浅い調査...
```

**特徴**:
- 「直接行ってはならない」と禁止を明示
- 「Agent ツール」で具体的なツール名を明記
- 起動前に「ルール」セクションで制約・条件を列挙
- 並列起動時の条件（領域独立性など）を明確化

**ファイルパス引用**: `/Users/kawasetakumi/dotfiles/.claude/skills/pir2/SKILL.md` line 78-92

#### プロンプト必須パラメータの列挙（pir2 ステップ 3）

```markdown
### プロンプトに必ず含めるパラメータ
- `PROJECT_MEMORY_DIR=[パス]`
- `RUN_DIR=[パス]`
- `EXPLORATION_INDEX=NN`（初回=`01`、並列起動時はスキル本体が `01`/`02`/`03` と割り振る）
- 「探索レポート本体は `{RUN_DIR}/exploration-{NN}.md` に書き出し、チャットには要約のみ返してください」
- 「探索フェーズではタスクのコード実装を行わず、`git add` / `git commit` などリポジトリ状態を変更する git 操作も一切行わないでください。実装が必要だと判明したら探索レポートの『呼び出し元への依頼』に回してください」（explorer は `Write` / `Bash` を持つため、明示しないと探索の延長で実装・コミットまで踏み込むロール逸脱が起こりうる）
```

**特徴**:
- **必須パラメータをカンマ項目で列挙**（タスク本体・パス・Index・出力指示が最小セット）
- `EXPLORATION_INDEX` のような**序数管理の初期値・インクリメント規則**を明記
- **役割境界の厳守**を括弧書き理由付きで説示（ロール逸脱防止）

**ファイルパス引用**: `/Users/kawasetakumi/dotfiles/.claude/skills/pir2/SKILL.md` line 93-99

#### Fan-Out Gate（並列起動の自己コミット）

```markdown
### 7-2A: 起動宣言（Fan-Out Gate — 並列発火の直前に必ず書く）

reviewer 並列起動メッセージを送信する **直前のターン本文中** に、以下のテンプレートを必ず生成すること。このテンプレートが本文に出現していないターンで Agent 起動を発火させた場合は、ステップ完了判定を取り消して 7-2A からやり直す。

> **Fan-Out Gate（reviewer）**
> - REVIEWER_SET = [<観点をカンマ区切りで全列挙>]
> - 起動体数 = <N>（= len(REVIEWER_SET)、必ず一致）
> - 同一 function_calls ブロックに <N> 個の Agent 起動を並べる
> - 1 体ずつ起動・後追い起動・観点削減はいずれも違反

このブロックは「起動直前の自己コミットメント」であり、ユーザーへの報告ではなく自分の手癖（1 体ずつ逐次起動する癖）を止めるためのフェンスとして機能する。再レビュー時（7-4 からの差し戻し時）にも毎回この宣言を書くこと。
```

**特徴**:
- テンプレートは引用符（`> **Fan-Out Gate...**`）で視覚的に分離
- 「`function_calls` ブロックに <N> 個を並べる」と具体的な配置指示
- 違反パターンを4項目で列挙（逐次起動・観点削減など）
- **再起動時も必須**（毎回宣言）
- 自己コミットメント説示（手癖制御用フェンス）

**ファイルパス引用**: `/Users/kawasetakumi/dotfiles/.claude/skills/pir2/SKILL.md` line 370-381

#### 並列発火の直後（同一メッセージ内）

```markdown
### 7-2B: 並列発火（同一メッセージ内）

直前ターンで宣言した REVIEWER_SET の各観点について、同一の `<function_calls>` ブロック内に Agent ツール呼び出しを **N 個** 並べて 1 メッセージで同時送信する。各体は `REVIEWER_ROLE` を変えて担当観点を分割する。

詳細仕様（観点マッピング / 違反パターンと検出 / 違反検出時のリカバリ / reviewer 起動パラメータ）: `~/.claude/skills/pir2/references/fan-out-gate.md` を参照。
```

**特徴**:
- 「直前ターンで宣言した REVIEWER_SET」と前ステップとの明確な依存関係
- 「N 個を並べて 1 メッセージ」という実装指示の具体性
- 詳細は reference に外出し（fan-out-gate.md）

**ファイルパス引用**: `/Users/kawasetakumi/dotfiles/.claude/skills/pir2/SKILL.md` line 382-389

---

### 【ir（軽量スキル）の比較】本文をコンパクトに

**ステップ採番**: `ステップ 0 → ステップ 1 → ステップ 2 → ステップ 3 → ステップ 4`（5 ステップ）

**ステップ 0 の役割**:
- ステップ 1 へ進む前の下準備（RUN_DIR 確定のみ）
- pir2 の「ステップ 1: プロジェクトメモリパスと RUN_DIR の確定」に相当するが、`HANDOFF_PATH` / `RESUME_MODE` を削ぎ落とした軽量版

**ファイルパス引用**: `/Users/kawasetakumi/dotfiles/.claude/skills/ir/SKILL.md` line 15-41

**ステップ 1-4 の構成**:
- ステップ 1: implementer 起動（1 体のみ、planner なし）
- ステップ 2: reviewer 起動（自動選定ロジック付き）
  - 2-1: REVIEWER_SET 決定（フラグパース → 観点の自動判定ロジック）
  - 2-2A: Fan-Out Gate 宣言
  - 2-2B: 並列発火
- ステップ 3: レビューループ（最大 2 回）
- ステップ 4: 最終サマリー

**比較表**:

| 属性 | pir2 | pir2codex | ir |
|-----|------|-----------|-----|
| ステップ数 | 13（+ 0.5 つの細分） | 13（pir2 を参照） | 5 |
| フロー名 | 「PIR²」 | 「PIR² Codex」 | 「IR」 |
| planner 有無 | あり（Opus） | あり（Opus） | **なし** |
| implementer 数 | 可変（1 or shard or sequential） | 可変（Codex 版） | 固定 1 体 |
| reviewer 観点選定 | 固定（全 5 観点） | 固定（全 5 観点） | **自動判定**（コード変更判定・セキュ判定など） |
| references | 16 個別ファイル | 参照（pir2 指向） | **なし**（本体に記載） |
| tester ループ | あり（OUTER_LOOP） | あり（OUTER_LOOP） | **なし** |
| retrospector | あり | あり | **なし** |
| handoff 対応 | あり | あり | **なし** |

**ファイルパス引用**: `/Users/kawasetakumi/dotfiles/.claude/skills/ir/SKILL.md` 全体

---

### 【research スキルの特殊構成】非コード・独立フロー型

**ステップ採番**: `ステップ 0 → ステップ 1 → ステップ 2（-2.2 ゲート付き） → ステップ 3 → ステップ 4 → ウォークスルー`

**特殊点**:
1. **RUN_DIR のみ**（PROJECT_MEMORY_DIR 不要、handoff 非対応）
2. **ステップ 0**: RUN_DIR 確定だけ（pir2 の ステップ 1 からカットダウン）
3. **ステップ 2**: 「集約 + 調査結果ゲート」として 2 段に分割
   - 2-1: オーケストレーター自身が探索結果を集約（サブに委譲しない）
   - 2-2: ユーザーゲート（A: 進む / B: 追加調査 / C: 方向修正）
4. **無人実行対応**: ゲートで応答がない場合の既定値（デッドロック回避）を明記

**モデル割当の表示**（table 形式）:

```markdown
| フェーズ | 担当 | モデル |
|---------|------|--------|
| 調査 | explorer（最大3体並列） | `sonnet` |
| 集約 | オーケレーター（スキル本体） | `opus`（= メインセッション） |
| 思考 | thinker | `fable` |
| 仮説 | hypothesizer | `opus` |
```

**ファイルパス引用**: `/Users/kawasetakumi/dotfiles/.claude/skills/research/SKILL.md` line 13-20

---

### 補足情報

#### ファイル物理配置規則

1. **メイン SKILL.md**: スキルごとに `.claude/skills/<name>/SKILL.md` に配置（1 ファイル = 1 スキル）
2. **references サブディレクトリ**: 大規模スキル（pir2）のみ `references/` を持つ
   - pir2 が 16 個の reference ファイルを持つ
   - pir2codex・ir・research は reference を持たず（共有 reference は pir2 指向）
3. **参照方法**: 本文から `~/.claude/skills/pir2/references/<name>.md` を明示参照（相対パスでなく絶対パス）

#### frontmatter 文体の統一性

**共通パターン**:
- `description` はタスク説明 + 利用シーン例 + ユーザーインボイス + entry condition
- `argument-hint` は引数種別を括弧付きで記載
- すべてのスキルで「ユーザーが /name と入力したら必ずこのスキルを使う」と明記

#### ステップ見出しの命名規則

**採番**:
- **通し番号**: `ステップ N:` （pir2）vs `ステップ 0:` で下準備を 0 から始める（ir・research）
- **副見出し**: 小数第一位を使う（`4.5: 能動的再探索ループ` = ステップ 4 の内部ステップ）
- **マーク**: pir2codex の差分ステップに `★` を付与（視覚的区別）

#### Agent 起動時の必須明示項目

**すべてのスキルで共通**:
1. 「〜エージェントを `Agent` ツールで起動」と具体的に
2. `PROJECT_MEMORY_DIR=[パス]` と `RUN_DIR=[パス]` の必須性を明記
3. INDEX（`EXPLORATION_INDEX=01` / `REVIEW_INDEX=01` など）の初期値・インクリメント規則
4. **出力ファイルパス指定**（`{RUN_DIR}/exploration-{INDEX}.md` 形式で Write 先を明示）
5. **ロール境界の厳守**（実装禁止・git 操作禁止など）を括弧理由付きで注記

#### 再レビュー・再実装時の Fan-Out Gate 再使用

pir2 と ir の両者で：
- ステップ 7（pir2）/ ステップ 3（ir）で再レビューループが発生する
- **毎回 Fan-Out Gate を宣言に戻す**（7-2A を繰り返す）
- 観点セット（REVIEWER_SET）は初回選定を維持（途中追加・削除禁止）

---

### 呼び出し元への依頼（該当する場合のみ）

**なし**。本探索は調査と型抽出に限定し、実装・git 操作は不実施。抽出結果をもとに epic SKILL.md の骨格を別途 implementer にて実装してください。
