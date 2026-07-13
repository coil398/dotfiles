# Instruction file 肥大化リファクタリング チェックリスト

instruction file（CLAUDE.md / agents/*.md / skills/**/SKILL.md）の肥大化を判定するための観点と検出方法。検出のみで終わらず、判定ごとに整理戦略を選択して実際にリファクタするための判断基準。

公式基準の引用と URL は `~/.agents/skills/instruction-refactor/references/official-criteria.md` を参照。整理戦略の詳細は `~/.agents/skills/instruction-refactor/references/strategies.md` を参照。

## 判定 1: 公式定量基準・スキーマ制約

| 種別 | 上限 / 制約 | 由来 | 違反時 |
|---|---|---|---|
| `SKILL.md` 行数 | **500 行**（soft cap） | Codex doc | references/ 外出し推奨 |
| `description`（フィールド本体） | **1,024 文字** | agentskills.io 標準 | **ロード不可（バリデーションエラー）** |
| `description + when_to_use`（listing 表示） | 1,536 文字（truncate point） | Codex 固有 | 一覧表示で切り捨て |
| `name` 文字数 | 64 文字 | 標準 | ロード不可 |
| `name` と親ディレクトリ名 | **一致必須** | agentskills.io 標準 | **ロード不可** |

肥大化検出では `description` の主基準を **1,024 文字**（厳しい方）にする。1,536 は listing 表示上の別概念。各出典 URL と frontmatter フィールド一覧（標準 + Codex 拡張）は `~/.agents/skills/instruction-refactor/references/official-criteria.md` を参照。

CLAUDE.md / agents/*.md は公式に数値基準なし。代わりに「肥大化警告」が明示されている: "Bloated CLAUDE.md files cause Claude to ignore your actual instructions"。

検出方法:

- `wc -l` で各ファイルの行数を計測
- `SKILL.md` で 500 行を超えるものを抽出
- 各 SKILL.md の `description` 文字数を計測し **1,024 超過**を抽出（`when_to_use` があれば合算が 1,536 超過かも併せて確認）
- 各 SKILL.md の `name` が **親ディレクトリ名と一致するか**照合
- 標準外フィールドを見つけても、`official-criteria.md` のフィールド一覧（標準 + Codex 拡張）に載っていれば誤検出扱いにしない
- CLAUDE.md / agents/*.md は同種ファイルの平均からの外れ値（**平均の 3 倍以上**）を抽出

## 判定 2: 構造的悪さ（4 類型）

### 2a. 責務越境

「提案するだけ」「観察するだけ」と明記されている agent / skill が、実装詳細（hook 雛形 sh、テンプレート全文、公式仕様の抜粋）を内包していないか。

検出方法:

- agent 定義の役割記述（role / responsibility）を Read
- 同ファイル内に「提案のみ」「自分では編集しない」「観察のみ」等の宣言があるか確認
- それと同時に sh / json / フルテンプレートが書かれているなら **責務越境** の疑い

### 2b. SSOT 逸脱

別のファイルが SSOT として管理しているはずの情報を抜粋・複写していないか。

代表的な SSOT:

- `/skill-creator`: スキル作成テンプレート、Writing Style、description 最適化
- `AGENTS.md (shared SSOT)`: グローバル汎用性ルール、Git ルール、書式ルール、エージェント関連ルール
- `~/.cursor/agents/reviewer.md`: 観点マッピング、Fan-Out Gate プロトコル
- `~/.cursor/agents/refactor-advisor.md`: 言語イディオムガードレール
- Codex 公式 doc: hook 仕様、settings.json スキーマ、permissions、skills 構造

検出方法: SSOT を Read → 監査対象ファイルが類似内容を含むか grep 確認。

> ⚠️ **配達経路の確認（性能保全）**: SSOT 逸脱に見えても、その内容を消費する agent が当該 SSOT を**実際に Read する手順を持っているか**を grep で確認する。読む手順が無ければ inline コピーが唯一の配達経路であり、prune すると消費側に情報が届かず性能が落ちる。詳細は `strategies.md` の「性能保全ゲート」判定 2 を参照。

### 2c. DRY 違反

複数ファイルにほぼ字句同一のセクションがコピーされていないか（特に PIR² 系スキル群、複数の reviewer 系スキル間）。

検出方法:

- 監査対象群を pairwise で比較
- 連続 5 行以上の重複 + セクション見出しの対応 → DRY 違反候補
- 解消策: 共通の `references/` に外出しして両方から参照

### 2d. 二重説明 / 意味的重複（加筆による重複の正規化）

同じファイル内で同じ手順・概念・ルールを 2 回以上説明していないか。**字句が一致していなくても、意味的に同じことを述べている段落・箇条書き・ルールのクラスタ**を対象にする（典型: 単一ドキュメントを加筆し続けるうちに、別のセクションで同じことを書き始めるケース）。

検出方法:

- ファイルを通読し、意味的に重複する段落 / ルール / 手順を **クラスタにグルーピング**する（同じことを述べている箇所をまとめる）
- 字句一致（キーワード・コードブロックの再登場）だけでなく、言い換え・パラフレーズによる重複も拾う
- 各クラスタについて、箇所間に **固有の差分情報があるか** を判定する（差分があれば統合時に和集合を取る / なければ単純に 1 箇所へ集約）

正規化（統合）戦略は `~/.agents/skills/instruction-refactor/references/strategies.md` の「戦略 6: 意味的重複の統合（正規化）」を参照。これは要約・圧縮（情報を削る）ではなく、重複を 1 箇所に集約して情報量を保つ lossless な効率化。

## 判定 3: スキルの description 適切性

skill-creator のガイドに準拠しているか:

- 自然言語トリガー語句が **3〜5 個** 列挙されているか
- 「明示的に名指ししなくても発火」の指示があるか
- 「`/<name>` と入力したら必ずこのスキルを使う」の指示があるか

検出方法: フロントマターの `description` を Read → pushy パターンに準拠しているか確認。

## 判定 4: グローバル汎用性ルール（ユーザースコープのみ・全ファイル専用スイープ必須）

`~/.cursor/agents/*.md` / `~/.agents/skills/**/SKILL.md`（および `skills/**/references/*.md`）にプロジェクト固有名（クラス名・テーブル名・カラム名・API エンドポイント名・具体フレームワーク/ORM 名・特定の make ターゲット名・特定プロジェクトの絶対パス・ドメイン固有エンティティ名）が混入していないか。

> ⚠️ **判定 2（構造読解）のついでに拾うと取りこぼす**（構造 explorer がたまたま精読したファイルだけを見るため）。判定 4 は **対象ファイル全件を対象にした独立の grep スイープ**として実行する。1 ファイルもスイープ対象から外さない。

検出方法（2 段階・cross-reference 必須）:

1. **候補抽出（全ファイル横断 grep）** — 固有名になりやすいパターンを全件に grep する:
   - make ターゲット: `make [a-z]+`（`build` / `lint` / `test` / `codegen` 等の汎用語を除いた固有ターゲット名）
   - DB カラム / エンティティ: `[a-z]+_id`、業務 / ゲーム / 教育ドメインの固有名詞
   - 具体フレームワーク / ORM を事実前提化した記述: `GORM` / `AutoMigrate` / `ActiveRecord` 等
   - 特定プロジェクトの絶対パス・固有ディレクトリ（`util/` 等）、会社 / クライアント / サービス固有名
2. **project-specific 判定（記憶や雰囲気で決めない）** — 候補語を**ユーザーの実プロジェクトと照合**して generic か leak かを確定する:
   - `~/.cursor/history.jsonl` を grep し、候補語が実コマンド・実 make ターゲット・実パスとして登場するか確認
   - `~/.cursor/memories/*/memory/` を grep し、候補語がドメイン語・テーブル名として登場するか確認
   - 登場すれば **leak（NG）**。複数エコシステム共通の一般ツール（`protoc` / `sqlc` / `jest` / `pytest` / `go test`）・明示的仮名（`XxxService`）・公開技術定数（Azure 公開ロール名・Unity 公開エンジン用語）は generic（OK）
   - generic だがドメイン特化 skill に移すのが望ましいものは「移動提案」に留める（leak ではない）

> ℹ️ **適用後に機械 grep で残存ゼロを最終確認**: 構造 explorer / privacy スイープが「クリーン」と報告しても部分スイープの取りこぼしがありうる。リファクタ適用後に候補語パターンを**全件へ再 grep し残存ゼロ**を確認する（機械確認で人/AI の見落としを塞ぐ）。

汎用化は固有名 → 架空の仮名 or 汎用語への置換、またはプロジェクトスコープへ移動（戦略 8）。詳細は `AGENTS.md (shared SSOT)` の「グローバルファイルの汎用性ルール」を参照。

## 整理戦略の選択

検出された問題種別 → 整理戦略の対応は `~/.agents/skills/instruction-refactor/references/strategies.md` の「戦略選択フローチャート」が **SSOT**。検出後はそちらを参照して戦略を選ぶ。

> ℹ️ 旧来この節にあった対応表は二重管理（および「二重説明 → 片方削除」のような戦略 6 と矛盾する記述）を解消するため strategies.md に一本化した。
