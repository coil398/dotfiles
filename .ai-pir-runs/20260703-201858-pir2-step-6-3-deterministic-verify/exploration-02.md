## 探索レポート: pir2 新ステップ 6-3「決定論的完了検証」の設計・既存参照関係確認

### 関連ファイル一覧

| ファイルパス | 役割・内容 | 変更の必要性 |
|------------|-----------|------------|
| `.claude/skills/pir2/SKILL.md` | メインスキル。ステップ 6（実装フェーズ）定義 | 参照・変更予定 |
| `.claude/skills/pir2codex/SKILL.md` | pir2 の Codex 実装版。ステップ 6 の差分本体がセクション 6-1 | 参照・変更可能性 |
| `.claude/skills/pir2async/SKILL.md` | pir2 のチーム実装版。unit 統合確認として似た検証が既存 | 参照のみ |
| `.claude/agents/implementer.md` | 実装エージェント。実装完了レポートフォーマット定義あり | 参照のみ |
| `.claude/skills/pir2/references/implementation-delegation.md` | shard / unit の統合確認ロジック | 参照のみ |
| `.claude/skills/pir2/references/destructive-change-check.md` | 類似の多軸チェックロジック（reference の粒度参考） | 参照のみ |
| `.claude/skills/pir2/references/` | 17 個の reference ファイル群。最小 13 行～最大 279 行 | 参照のみ |

### 既存パターン・規約

#### 1. pir2 SKILL.md ステップ 6 の現在の構成

- **6-0**: 実装 actor 決定（implementer-subagent / implementer-shards / implementer-sequential / main）
- **6-1**: implementer 起動（プロンプト + `IMPL_INDEX` 渡し）
- **6-2**: 統合確認（shards / sequential の場合のみ。全 `implementation-{IMPL_INDEX}-*.md` を Read + git diff で競合・命名不整合・未接続を確認）
- **6.5**: 実装者の未解決事項ユーザー確認
- **その後**: ステップ 7（レビュー）へ

**重要**: 現在、6-1 と 6-2 の間に「申告 vs 実体の照合」という決定論的検証が **明示的には記載されていない**。6-2 は "shards/sequential のときだけ" という限定条件付き。

#### 2. pir2codex SKILL.md での既存検証

ステップ 6-1「Codex wrapper Agent の起動」の「wrapper 返り後のスキル本体の処理」セクション（SKILL.md Line 170-174）に：

```markdown
1. **git diff で実体検証（必須）**: `git diff --stat HEAD` / `git diff --name-only HEAD` を実行し、Codex が実際にファイルを変更したかを確認する。Codex の自己申告を信じない...
```

→ **Codex では既に「自己申告 vs git diff 実体検証」が必須化されている**。この検証は **pir2codex のメイン Claude（スキル本体）が 6-1 直後に実施**する責務として明記されている。

#### 3. pir2async での類似検証

ステップ 4.85（チーム実装フェーズ）の「unit 統合確認」として：
```
全 unit 完了後、スキル本体が delegation.md「unit 統合確認」（全 `implementation-{IMPL_INDEX}-unit-*.md` を Read + `git diff` で命名不整合・重複抽象・未接続を確認）を実施
```

→ unit 完了後に `git diff` と実装レポート内容の照合がある。

#### 4. implementer.md の変更ファイル報告フォーマット（必須）

implementer.md Line 90-105 で固定フォーマット定義：

```markdown
## 実装完了レポート

### 変更ファイル一覧
- `path/to/file1` — [変更内容の概要]
- `path/to/file2` — [変更内容の概要]
...

### 実装概要
[何を実装したか1〜3文で]

### 注意点・未解決事項
[レビュワーに伝えるべきこと（なければ「なし」）]
```

**「変更ファイル一覧」は `###` レベルの固定見出し**。これが 6-3 で機械 grep の対象となる。

#### 5. references ディレクトリの命名・粒度慣習

| ファイル名パターン | 粒度・用途 | 行数範囲 | 例 |
|---|---|---|---|
| `*-gate.md` | 判定ロジック・ゲート処理 | 38-89 行 | `continuation-gate.md`, `plan-choice-gate.md` |
| `*-check.md` | チェック・検証ロジック | 96 行 | `destructive-change-check.md` |
| `*-loop.md` | ループ・再実行ロジック | 30 行 | `exploration-loop.md` |
| `*-queue.md` | キュー・状態管理 | 62 行 | `next-steps-queue.md` |
| `*-cleanup.md` | クリーンアップ・後処理 | 13 行 | `handoff-cleanup.md` |
| `*-templates.md` | テンプレート・フォーマット集 | 43 行 | `walkthrough-templates.md` |
| `*-prompt.md` | プロンプト指定・仕様 | 26-90 行 | `retrospector-prompt.md`, `tester-prompt.md` |

新規「決定論的完了検証」には `deterministic-completion-check.md` が適切（`*-check.md` パターン に該当、粒度は 50～120 行程度が想定）。

#### 6. 既存参照構造での SKILL.md 内参照形式

- ステップ内で「詳細プロトコル: `~/.claude/skills/pir2/references/<name>.md` を参照」と記載
- 要点をスキル本文に簡潔に書き、詳細を reference ファイルに委譲
- SKILL.md 行数肥大化を抑止、SSOT 分離

### 影響範囲

#### 直接影響

1. **pir2 SKILL.md ステップ 6 新ステップ 6-3 追加**
   - 位置: 現在のステップ 6-2 と ステップ 6.5 の間に挿入
   - 内容: implementer 완료 報告 수령 직후、`implementation-{IMPL_INDEX}.md`「변更ファイル一覧」セクションと `git diff` を照合する 決定論的검증
   - 플러그-인은 다음과 같이 복사하기:
     ```
     ## ステップ 6-3: 決定論的完了検証

     詳細プロトコル: `~/.claude/skills/pir2/references/deterministic-completion-check.md` を参照。
     
     要点: implementer からの実装完了レポート ...（2〜3文の簡潔説明）
     ```

2. **pir2 新 reference ファイル追加**
   - パス: `.claude/skills/pir2/references/deterministic-completion-check.md`
   - 内容: 
     - 検証の目的（implementer 自己申告と実体 git diff の乖離検知）
     - 検証手順（`{RUN_DIR}/implementation-{IMPL_INDEX}.md` の「変更ファイル一覧」を抽出 → git diff と比較 → 不一致検出時の対応フロー）
     - 機械処理可能な形式指定（セクション名の固定化確認）
     - スキップ条件・例外

#### 間接影響

1. **pir2codex SKILL.md**
   - 現状: 6-1「wrapper 返り後のスキル本体の処理」内に「git diff 実体検証」が既に書かれている
   - 改修方針: 
     - pir2 に 6-3 が追加された場合、pir2codex の 6-1 の該当部分を「→ ステップ 6-3 で統合的に検証」へ参照切替
     - または、pir2codex の 6-1 を reference に統一し、pir2 / pir2codex / pir2async で共通化
   - **判断**: pir2codex は現状「自前で git diff 実体検証」をしているため、6-3 追加後に **参照先を reference ファイルに切り替えるか、またはそのまま 6-1 内に温存するか** を決める必要あり

2. **pir2async SKILL.md**
   - 現状: unit 統合確認として類似検証が既に実装
   - 改修不要（チーム実装フェーズの特殊性のため独自実装のまま）

3. **implementer.md**
   - 直接の変更不要（変更ファイル一覧フォーマットは既に固定）
   - 間接的な影響: 6-3 で implementer.md のフォーマット前提が明確化される

### 依存関係

#### インポート関係

- pir2 SKILL.md → 新 reference「deterministic-completion-check.md」
- pir2 SKILL.md → implementer.md（実装完了レポートフォーマット確認用・read-only）
- 新 reference → `~/.claude/skills/pir2/references/implementation-delegation.md`（shard/unit 統合確認ロジックとの関連性）

#### 被参照関係

- pir2codex SKILL.md が参照する可能性あり（6-1 の実体検証ロジック）
- pir2async SKILL.md から参照される可能性あり（unit 統合確認との共通化打診時）
- retrospector が観測する可能性あり（experimental.md にロジック変更フラグを記録する必要があるか判定）

### 補足情報

#### 発見した設計上の考慮事項

1. **pir2codex との差分管理**
   - pir2codex は現在「6-1 内で wrapper 経由の git diff 実体検証」を実施
   - pir2 に 6-3 が追加されると、二重管理リスクが生じる
   - **方針確定が必須**: 
     - (A) pir2 の 6-3 を reference 化し、pir2codex も 6-1 から 6-3 reference に切り替える → 共通化
     - (B) pir2codex は 6-1 に温存、pir2 のみ 6-3 を別途追加 → 異なるフェーズで実施（pir2 は post-implementer、pir2codex は post-wrapper）
     - (C) pir2codex では 6-1 内実装を「pir2 の 6-3 と同役」として参照記載 → reference 統一化とは別のアプローチ

2. **Codex の自己申告可能性**
   - pir2codex SKILL.md Line 172 に「Codex の自己申告を信じない（CLAUDE.md『ツール結果の捏造の絶対禁止』と同根。Codex も自己申告しうる）」と明記
   - **検証ロジック**: wrapper が Codex から受け取った「変更ファイル一覧」を検証対象に含める必要あり
   - 新 reference では、Codex 報告の検証も念頭に入れた汎用化が望ましい

3. **機械処理への最小限要件**
   - 6-3 が機械 grep で差分を検出するには、implementer.md の「変更ファイル一覧」見出しが **固定フォーマット（`###` + 日本語「変更ファイル一覧」）** である必要がある
   - 現状 implementer.md で確認: Line 95 に `### 変更ファイル一覧` で固定 ✓
   - Codex 報告も同一フォーマットで返す必要あり（pir2codex の wrapper 仕様で「Codex の報告（変更ファイル一覧＋概要）」と書かれているが、具体的な markdown 構造の指定がない → reference で明確化すべき）

4. **スキップ条件の判定**
   - pir2 単一 implementer の場合: 6-2（統合確認）がスキップされる（shards/sequential のときだけ）→ 6-3 は常時実施可？
   - pir2async unit: unit 統合確認は常時実施（unit 完了後）
   - 方針: 6-3 は**常時実施** のステップとして設計（違いは検証の責務主体：implementer 自己検証 vs スキル本体による最終検証）

5. **Codex/asyncとの構造的差異**
   - pir2: implementer 完了報告 → 本体が検証
   - pir2codex: wrapper 経由の自己申告 → 本体が検証（現在 6-1 内）
   - pir2async: unit 単位の完了 → 本体が統合検証
   
   **観察**: 実施箇所が異なるのは、責務主体（Claude implementer vs Codex vs Team）の差に起因。新 reference は「申告 vs 実体照合」という **概念的な共通性** を抽象化し、各ワークフローが状況に応じて参照可能な形で設計すべき。

### 参照した外部ソース

なし（コードベース内 SSOT のみの確認）

### 呼び出し元への依頼

1. **概念確定が必須**
   - 新ステップ 6-3 を「pir2 専用」とするか、「pir2/pir2codex/pir2async で段階的に共通化対象にするか」をユーザー / planner 経由で確定してから設計開始
   - 特に pir2codex との重複を避けるための方針決定

2. **pir2codex への影響判定**
   - 方針 (A) 共通化する場合: pir2codex SKILL.md のステップ 6-1 内の実体検証ロジックを削除・reference 参照に切替（中程度の変更）
   - 方針 (B) / (C) の場合: pir2codex は現状のまま温存（変更なし）

3. **reference ファイル設計の詳細化**
   - Codex 報告フォーマットの具体化（wrapper が Codex から受け取った報告を markdown で正規化する仕様）
   - git diff 出力のパース・正規化アルゴリズム（複数ファイル、削除・追加・修正の混在への対応）
   - 不一致検出時のスキル本体への自動フォールバック指示の明確化
