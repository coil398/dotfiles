# 探索レポート: 新スキル `/epic` と新エージェント `epic-planner` の追加位置特定

## 調査対象

- `/Users/kawasetakumi/dotfiles/CLAUDE.md`：スキル/エージェント一覧の位置と追記フォーマット
- `/Users/kawasetakumi/dotfiles/etc/link.sh`：シンボリックリンク戦略
- `/Users/kawasetakumi/dotfiles/etc/sync-opencode.sh`：OpenCode sync の SSOT リスト
- `/Users/kawasetakumi/dotfiles/etc/sync-codex.sh`：Codex sync の SSOT リスト
- `/Users/kawasetakumi/dotfiles/.claude/settings.json`：登録の必要性

---

## 1. CLAUDE.md 追記位置（精密指定）

### (a) スキル一覧表

| 項目 | 詳細 |
|------|------|
| **位置** | `/Users/kawasetakumi/dotfiles/CLAUDE.md` 行 245〜269 |
| **表構成** | Markdown 表形式：`\| スキル \| 用途 \|` |
| **現在の最終行** | 269行：`\| \`/deepthink\` \| 探索 → 熟考（複数並列）→ 統合 → ゲートを rubric 充足まで反復する多エージェント熟考ワークフロー \|` |
| **追記位置** | **269行の下（新行 270行）に追加** |
| **追記内容** | `\| \`/epic\` \| <用途説明> \|` |

**例記載**（用途説明はタスク定義に合わせて調整）：
```markdown
| `/epic` | エピック/大規模タスクの多段階オーケストレーション |
```

### (b) エージェント定義一覧表

| 項目 | 詳細 |
|------|------|
| **位置** | `/Users/kawasetakumi/dotfiles/CLAUDE.md` 行 219〜235 |
| **表構成** | Markdown 表形式：`\| ファイル \| 役割 \|` |
| **現在の最終行** | 235行：`\| \`gate.md\` \| position を成功基準（rubric）に客観照合し VERDICT: PASS/FAIL を返す十分性ゲート（/deepthink、Opus） \|` |
| **追記位置** | **235行の下（新行 236行）に追加** |
| **追記内容** | `\| \`epic-planner.md\` \| <役割説明> \|` |

**例記載**（役割説明はタスク定義に合わせて調整）：
```markdown
| `epic-planner.md` | 大規模エピックのタスク分解とマイルストーン設計 |
```

### (c) PIR² ワークフロー説明セクション（pir2 系に含まれる場合のみ）

| 項目 | 詳細 |
|------|------|
| **位置** | `/Users/kawasetakumi/dotfiles/CLAUDE.md` 行 203〜215 |
| **セクション名** | `### PIR² ワークフロー (\`/pir2\`)` |
| **フェーズ構成記述** | 211〜215行：スキル本体 → planner → retrospector の3エージェント列挙 |

**判定**：
- `/epic` が PIR² フロー内で **独立したワークフロー** なら、本セクション追記は **不要**（別節を新規作成）
- `/epic` が PIR² フロー内に **統合される** なら、211〜215行のフェーズ構成に `epic-planner` を言及追加

### (d) PIR² ワークフロー図

| 項目 | 詳細 |
|------|------|
| **判定** | CLAUDE.md には **図の記載なし**。フェーズ構成は (c) の 211〜215行で **テキスト記述のみ** |
| **追記要否** | PIR² フロー図を新規追加する場合のみ。本調査では対象外 |

---

## 2. link.sh での自動リンク

### 戦略確認

**ファイル**: `/Users/kawasetakumi/dotfiles/etc/link.sh` 行 71〜75

```bash
for claude_dir in agents skills lib hooks; do
    if [ -d "$DOT_DIRECTORY/.claude/$claude_dir" ]; then
        link_dir "$DOT_DIRECTORY/.claude/$claude_dir" "$HOME/.claude/$claude_dir"
    fi
done
```

### 判定

| 対象ファイル | 配置パターン | 自動リンク | 改修要否 |
|---|---|---|---|
| **エージェント** `epic-planner.md` | `.claude/agents/epic-planner.md` | ✅ YES | ❌ 不要 |
| **スキル** `SKILL.md` | `.claude/skills/epic/SKILL.md` | ✅ YES | ❌ 不要 |

**根拠**：
- 71行の `for claude_dir in agents skills lib hooks` ループで、`.claude/agents/` ディレクトリと `.claude/skills/` ディレクトリ **全体** が symlink 対象
- `link_dir()` 関数（34〜44行）により、対象ディレクトリ配下の全ファイルが `$HOME/.claude/` にリンクされる
- **新規ファイル追加時も自動で拾われる**（ループはディレクトリ単位、ファイル単位ではない）

**結論**: **link.sh 改修不要。ファイル配置のみで自動リンク。**

---

## 3. OpenCode/Codex Sync での自動抽出

### 3-1. OpenCode 互換（sync-opencode.sh）

**SSOT リスト**: `/Users/kawasetakumi/dotfiles/etc/sync-opencode.sh` 行 4〜9

```bash
# SSOT:
#   - $DOT_DIR/mcp-servers.json          (MCP servers)
#   - $DOT_DIR/.claude/settings.json     (permissions)
#   - $DOT_DIR/AGENTS.md                 (shared global instructions)
#   - $DOT_DIR/.agents/skills/*          (shared skill definitions)
#   - $DOT_DIR/.claude/agents/*.md       (agent definitions)
```

### 判定

| 対象ファイル | SSOT パターン | 自動抽出 | 手動追加 |
|---|---|---|---|
| **エージェント** `.claude/agents/epic-planner.md` | `.claude/agents/*.md` ✅ | ✅ YES | ❌ 不要 |
| **スキル** `.claude/skills/epic/SKILL.md` | `.agents/skills/*` ⚠️ | 条件付 | ℹ️ 下記参照 |

**スキルの選択肢**：
1. `.claude/skills/epic/` 配下に配置 → OpenCode では同期 **されない**（`.agents/skills/*` パターン外）
2. `.agents/skills/epic/` に配置 → OpenCode では自動同期 ✅（`.agents/skills/*` パターン内）

**hook 発火**: `/Users/kawasetakumi/dotfiles/.claude/settings.json` 行 143〜159
- PostToolUse hook が `Edit|Write|MultiEdit` 全件にマッチ
- `sync-opencode-hook.sh` により SSOT パスマッチで自動再生成

**結論**: 
- **エージェント** `epic-planner.md` → 自動抽出 ✅
- **スキル** → `.agents/skills/epic/` に配置すれば自動抽出 ✅

---

### 3-2. Codex 互換（sync-codex.sh）

**SSOT リスト**: `/Users/kawasetakumi/dotfiles/etc/sync-codex.sh` 行 4〜15

```bash
# SSOT:
#   - $DOT_DIR/mcp-servers.json          (MCP servers)
#   - $DOT_DIR/AGENTS.md                 (shared global instructions)
#   - $DOT_DIR/.agents/skills/*          (shared skill definitions)
#   - $DOT_DIR/.claude/format.md         (referenced instructions)
#   - ...
#   - $DOT_DIR/.claude/agents/*.md       (legacy mirror input only; disabled by default)
```

### 判定

| 対象ファイル | SSOT パターン | 自動抽出 | 注記 |
|---|---|---|---|
| **エージェント** `.claude/agents/epic-planner.md` | `.claude/agents/*.md` ⚠️ | ❌ NO | デフォルト disabled |
| **スキル** `.agents/skills/epic/` | `.agents/skills/*` ✅ | ✅ YES | 共有スキル化の場合のみ |

**重要**: `/Users/kawasetakumi/dotfiles/etc/sync-codex.sh` 行 32〜36
```bash
# Native overlay policy:
#   Strict mirroring of .claude/agents and .agents/skills into .codex is disabled
#   by default. .agents/skills is the shared core, while .codex/agents and
#   .codex/skills are Codex-native overlays. Set SYNC_CODEX_LEGACY_MIRROR=1 only
#   when intentionally regenerating the old mirror snapshots.
```

**つまり**：
- `.claude/agents/epic-planner.md` は Codex 側に自動ミラーされない（legacy mirror disabled）
- Codex で `epic-planner` を使いたい場合、**手動で `.codex/agents/` 配下に Codex ネイティブ定義を作成する必要あり**

**結論**：
- **エージェント** → OpenCode のみ自動抽出。Codex では legacy mirror disabled
- **スキル** → `.agents/skills/epic/` に配置で OpenCode/Codex 共通自動抽出 ✅

---

## 4. settings.json での登録要否

**ファイル**: `/Users/kawasetakumi/dotfiles/.claude/settings.json` 行 1〜229

### セクション確認

| セクション | 用途 | スキル/エージェント登録の必要性 |
|---|---|---|
| `env` | 環境変数 | ❌ 不要 |
| `permissions` | 権限 allow/deny | ❌ 不要 |
| `model` | デフォルトモデル | ❌ 不要 |
| `hooks` | PreToolUse / PostToolUse / Stop | ❌ 不要 |
| `statusLine` | ステータス表示 | ❌ 不要 |
| `enabledPlugins` | プラグイン有効化（188〜199行） | ❌ 不要 |
| `extraKnownMarketplaces` | 外部スキル供給源（201〜213行） | ❌ 不要（内部スキル） |

### 判定

スキルとエージェントの登録は settings.json では行わない。理由：
1. Claude Code はスキル・エージェントを **ディレクトリ構造 + SKILL.md/.md ファイルの配置** で自動認識
2. settings.json は **権限・hooks・プラグイン有効化** の制御のみ
3. スキル/エージェント固有の登録機構なし

**結論**: **settings.json への登録不要。** ファイル配置のみで十分。

---

## 5. 実装手順フロー図

```
┌─ ユーザーが /epic と epic-planner を追加予定
│
├─ 【CLAUDE.md 編集】
│  ├─ L.245-269 スキル表に追加（L.270)
│  └─ L.219-235 エージェント表に追加（L.236)
│
├─ 【ファイル配置】
│  ├─ .claude/agents/epic-planner.md  ← エージェント定義ファイル
│  │
│  └─ スキル配置の判定：
│     ├─ Claude Code のみ → .claude/skills/epic/SKILL.md
│     └─ 汎用（OpenCode/Codex 共用） → .agents/skills/epic/SKILL.md
│
├─ 【link.sh】
│  └─ 改修不要 ✅（自動リンク発火）
│
├─ 【OpenCode sync】
│  ├─ エージェント → 自動抽出 ✅
│  └─ スキル → .agents/skills/epic/ なら自動抽出 ✅
│
├─ 【Codex sync】
│  ├─ エージェント → legacy mirror disabled（手動対応が必要な場合あり）
│  └─ スキル → .agents/skills/epic/ なら自動抽出 ✅
│
└─ 【settings.json】
   └─ 登録不要 ✅
```

---

## 補足：スキル配置の選択肢

### `.claude/skills/epic/SKILL.md`（Claude Code 特化）

| 特性 | 詳細 |
|---|---|
| **OpenCode** | 同期されない ❌ |
| **Codex** | legacy mirror disabled、手動対応必要 |
| **推奨** | Claude Code 固有機能（Agent ツール等）を活用する場合 |

### `.agents/skills/epic/SKILL.md`（ポータブル・汎用）

| 特性 | 詳細 |
|---|---|
| **OpenCode** | 自動同期 ✅ |
| **Codex** | 自動同期 ✅ |
| **Claude Code** | `.agents/skills/**` パターンで自動認識 ✅ |
| **推奨** | 複数ツール対応が必要な場合 |

---

## 結論サマリ

### 【CLAUDE.md 追記位置】

| 対象 | 追記行番号 | フォーマット |
|---|---|---|
| **(a) スキル表** | **L.270（新規行）** | `\| \`/epic\` \| <用途> \|` |
| **(b) エージェント表** | **L.236（新規行）** | `\| \`epic-planner.md\` \| <役割> \|` |
| **(c) PIR² セクション** | **L.203-215** | PIR² フロー統合の有無で判定（独立スキルなら不要） |

### 【link.sh】

**結論**: **改修不要** ✅
- 自動リンク発火（line 71-75 のループで自動拾い）

### 【OpenCode/Codex sync】

| 対象 | OpenCode | Codex | 手動追加 |
|---|---|---|---|
| **エージェント** | ✅ 自動 | ⚠️ disabled | ❌ 不要（OpenCode） / ⚠️ Codex 検討 |
| **スキル** `.agents/skills/*` | ✅ 自動 | ✅ 自動 | ❌ 不要 |
| **スキル** `.claude/skills/*` | ❌ | ⚠️ disabled | SSOT リスト編集不要 |

### 【settings.json】

**結論**: **登録不要** ✅
- スキル・エージェント登録機構なし
- ファイル配置とディレクトリ構造で自動認識

---

## 参照した外部ソース

| 項目 | ファイルパス | 確認内容 |
|---|---|---|
| CLAUDE.md | `/Users/kawasetakumi/dotfiles/CLAUDE.md` | スキル/エージェント一覧表の位置（L.219-269） |
| link.sh | `/Users/kawasetakumi/dotfiles/etc/link.sh` | シンボリックリンク戦略（L.71-75） |
| sync-opencode.sh | `/Users/kawasetakumi/dotfiles/etc/sync-opencode.sh` | OpenCode SSOT リスト（L.4-9） |
| sync-codex.sh | `/Users/kawasetakumi/dotfiles/etc/sync-codex.sh` | Codex SSOT と legacy mirror disabled 記述（L.4-36） |
| settings.json | `/Users/kawasetakumi/dotfiles/.claude/settings.json` | 登録機構確認（L.1-229） |
