---
name: deepthink
description: 特定の状況・問いを多エージェントで深く深く考え抜くワークフロー。オーケストレーター（スキル本体, Opus）が探索しまくり、複数の思考エージェント（deliberator）に多様なレンズで熟考させ、synthesizer が1本に統合し、gate が成功基準（rubric）に照らして客観的に十分性を判定する。満たすまで（必要なら追加探索を挟みつつ）ループし、gate が全基準の充足を客観的に確認できたら終了する。「じっくり考えたい」「深く考えて」「考え抜いて」「多角的に検討して」「結論を出したいが難しい」「意思決定を詰めたい」「〜すべきか徹底的に考えて」「腹落ちする答えがほしい」といった要望に対応する。単なる調査や仮説出し（それは /research）、コード実装・バグ修正・デバッグ（それは /pir2, /debug, /ir）ではなく、答えの出しにくい状況・問いをループで深掘りして客観的に十分な結論へ到達させたいときに使う。ユーザーが /deepthink と入力したら必ずこのスキルを使う。
argument-hint: [深く考えたい状況・問い]
---

# Deepthink — 探索 → 熟考 → 統合 → ゲート（十分まで反復）

多エージェント熟考ワークフローを実行します。このスキル本体（= メイン Claude, Opus）が**オーケストレーター**となり、explorer（探索）→ 集約 + rubric 確定（オーケストレーター自身）→ deliberator（熟考・複数並列）→ synthesizer（統合）→ gate（十分性判定）を `Agent` ツールで起動・制御します。gate が FAIL を返す限り、不足の種類に応じて追加探索を挟むか再熟考させ、**gate が rubric の全基準の充足を客観的に確認して PASS を出すまでループ**します。制御フロー（起動・ループ管理・VERDICT 集約・ユーザー確認ゲート）はスキル本体に集約し、サブからのネスト起動は read-only の探索（explorer）に限ります。

**状況・問い**: $ARGUMENTS

各フェーズのモデル割当:

| フェーズ | 担当 | モデル |
|---------|------|--------|
| 探索 | explorer（最大4体並列） | `sonnet` |
| 集約 + rubric 確定 | オーケストレーター（スキル本体） | `opus`（= メインセッション） |
| 熟考 | deliberator（既定3体並列） | `opus`（既定） |
| 統合 | synthesizer | `opus` |
| ゲート（十分性判定） | gate | `opus` |

> ℹ️ `/deepthink` は探究・熟考ワークフローであり、handoff 連携・プロジェクトメモリ追記は行いません（`HANDOFF_PATH` / `PROJECT_MEMORY_DIR` は不要）。

## 思考モデルのモード（THINKER_MODE）

熟考フェーズの deliberator の構成を切り替える:

| モード | 構成 | 選択条件 |
|--------|------|----------|
| `opus-panel`（既定・唯一） | `opus` の deliberator を**複数体並列**（既定3体、多様なレンズ） | 常にこのモード。多様な視点を並列で得て synthesizer が統合する |

- `fable-solo` モードは廃止（Fable 5 がサブスクリプションから削除予定のため 2026-07-16 廃止）。`$ARGUMENTS` に `fable` / `--fable` が含まれていても無視し、`opus-panel` で実行する。

---

## ステップ 0: RUN_DIR の確定

以下の Bash で `PROJECT_ROOT` / `RUN_DIR` を確定し、以降のすべてのステップで使用してください（基底パスの SSOT は `~/.claude/skills/pir2/references/run-dir-base.md`）:

```bash
PROJECT_ROOT="$(pwd)"
run_ts="$(date +%Y%m%d-%H%M%S)"
run_feature="$(printf '%s' "$ARGUMENTS" | tr -c 'a-zA-Z0-9' '-' | sed -E 's/-+/-/g; s/^-//; s/-$//' | cut -c1-40)"
[ -z "$run_feature" ] && run_feature="deepthink"
RUN_DIR="${PROJECT_ROOT}/.ai-pir-runs/${run_ts}-${run_feature}"
mkdir -p "$RUN_DIR"
# 中間ファイルを git 追跡から外す（git リポジトリのときのみ）
if git -C "$PROJECT_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  grep -qxF '/.ai-pir-runs/' "${PROJECT_ROOT}/.gitignore" 2>/dev/null || echo '/.ai-pir-runs/' >> "${PROJECT_ROOT}/.gitignore"
fi
echo "PROJECT_ROOT=$PROJECT_ROOT"
echo "RUN_DIR=$RUN_DIR"
```

以降の各サブエージェントへのプロンプトには必ず `RUN_DIR=[パス]` を含めてください。

---

## ステップ 1: 問いの framing と rubric ドラフト（オーケストレーター）

深く考えるには「何をもって十分か」を先に決める必要があります。スキル本体が状況・問いを分解し、**この熟考が満たすべき成功基準（rubric）のドラフト**を `{RUN_DIR}/rubric.md` に Write します。

rubric の各基準は、**gate が客観的に照合できる形**で書く（主観の入りにくい停止条件にするため）:

- ❌ 曖昧: 「深く考えられている」「十分に検討されている」
- ✅ 客観照合可能: 「主要な選択肢が N 個以上列挙され、各々の利点・欠点が根拠つきで示されている」「〈想定される最有力の反論〉に対して応答している」「結論が依拠する前提が明示され、それが崩れる条件が述べられている」「トレードオフが定量または具体で示されている」

rubric.md のフォーマット:

```markdown
## 成功基準（rubric）: [状況・問い]

### この熟考のゴール
[何に答えを出すのか。1〜2文]

### スコープ / 制約
- [考える範囲。考えない範囲。前提として与えられている条件]

### 充足基準（gate はこれを一項目ずつ客観照合する）
| # | 基準 | 充足の判定方法（何があれば充足か） |
|---|------|-----------------------------------|
| 1 | ... | ... |
| 2 | ... | ... |
```

> ℹ️ この時点の rubric は**ドラフト**。探索（ステップ2）で問題の実像が見えたら、ステップ3で確定させる。

---

## ステップ 2: 探索フェーズ（explorer, Sonnet）

状況・問いを独立したサブ問いに分割し、`explorer` エージェントを `Agent` ツールで起動して調査を委譲します。**メイン Claude が直接 Glob/Grep/Read/WebSearch/WebFetch で調べてはいけません**（`~/.claude/CLAUDE.md`「コードベース探索の委譲」）。

### 起動ルール

- **最低1体起動**（問いの規模にかかわらず初回探索は必須）
- **最大4体並列**: 独立したサブ問い（観点・情報源・対象）に分割できるなら並列起動する
- **model: `sonnet`**（全 explorer 共通）
- **情報源は Web + ローカルの両方**
- **Figma / Notion / Slack 等、MCP 経由の外部ツールへのアクセスが必要なサブ問いには `explorer` ではなく `general-purpose`（または該当ツールを持つ専用サブエージェント）を割り当てる**。`explorer` の標準ツールセットには `mcp__notion__*` / `mcp__slack__*` / `mcp__plugin_figma_*` が含まれておらず、これらが要るサブ問いを `explorer` に投げると探索自体が失敗する（WebFetch でのアクセスも認証壁で失敗することが多い）。サブ問いを切る時点で「これはコード/Web調査か、それとも特定の外部ツールが要るか」を先に判定し、後者なら `general-purpose`（全ツール保有）を選ぶか、対象ツールに応じた専用探索サブエージェント（例: プロジェクトに `notion-source-researcher` / `slack-source-researcher` / `figma-source-researcher` があればそちら）を使う。判定を誤り `explorer` が外部ツール不足で失敗した場合は、同じサブ問いを `general-purpose` で再割り当てして再実行する（オーケストレーターが自分で代替取得して埋め合わせるのではなく、まず正しいエージェントで再委譲する）。

### プロンプトに必ず含めるパラメータ

- `RUN_DIR=[パス]`
- `EXPLORATION_INDEX=NN`（初回=`01`、並列起動時は `01`/`02`/… と割り振る）
- 「探索レポート本体は `{RUN_DIR}/exploration-{NN}.md` に書き出し、チャットには要約のみ返してください」
- 「これは熟考のための調査です。実装・ファイル編集・`git` 状態変更は行わないでください。調査に徹し、外部の一次情報は必ず参照 URL を添え、記憶や推測で結論を埋めないでください」

### プロンプトに必ず含める調査観点

- 問いに関する既知の事実・定説・データ（一次情報の出典つき）
- 対立する見解・論争点・未解決の問い
- 関連する先行事例・類似ケース（ローカルの資料・コードにあれば含める）
- 情報の確実性（一次ソースか二次ソースか、どこまで裏が取れているか）

---

## ステップ 3: 集約 + rubric 確定 + ユーザーゲート（オーケストレーター, Opus）

### 3-1: 集約（サブに委譲せず、スキル本体自身が行う）

全 `{RUN_DIR}/exploration-*.md` を Read し、スキル本体（メイン Claude, Opus）が探索結果を熟考の土台となる背景ブリーフに統合し、`{RUN_DIR}/context.md` に Write する:

- 重複して報告された事実は1つにまとめる
- 出典のある事実と、出典が弱い/推測混じりの情報を仕分ける
- explorer 間で食い違う記述は「対立点」として明示する（潰さない）
- **情報密度を落とさない**: 熟考対象がコードや構造化データ（設定・スキーマ・SQL等）に及ぶ場合、プロセ要約だけで済ませず、該当箇所の実データを**逐語（verbatim）**で埋め込む（コードなら実際の関数実装をコードブロックで、データなら実際の値を）。理由: `deliberator` は「新規情報の収集は行わない」契約だが `Read`/`Bash` ツールを保有しており、材料が要約止まりだと自力でファイルを再探索しに行き、explorer/investigator の調査と二重作業になる。オーケストレーターがこの集約時点で十分な生データを埋め込むことで、deliberator は本来の「推論」に専念できる。目安: 「deliberator がこの記述だけで判断でき、元ファイルを開かずに済むか？」を自問し、否なら該当箇所を逐語引用で補う

`context.md` のフォーマット:

```markdown
## 背景ブリーフ（context）: [状況・問い]

### 確定的な事実（出典あり）
- [事実] — 出典: [URL / ファイルパス]

### 不確実・出典が弱い情報
- [情報] — [なぜ不確実か]

### 探索で見えた対立・論点
- [論点]: [どう割れているか]

### まだ埋まっていない空白
- [分かっていないこと]

### 詳細資料（逐語抜粋）
[コード/データが絡む熟考では、根拠となる関数の実装・実際のSQL・実際の設定値等をここにコードブロックで逐語収録する。「〜という実装がある（パス:行）」という要約止まりで済ませない]

\`\`\`[言語]
[実際のコード / データを逐語で貼る]
\`\`\`
```

### 3-2: rubric の確定

探索で問題の実像が変わっていれば、`{RUN_DIR}/rubric.md` を更新して基準を確定する（基準の追加・具体化・スコープ修正）。

### 3-3: ユーザーゲート（1回）

rubric（= **この熟考をこう判定します**という宣言）と context の要点を提示し、熟考ループに入る前に1回だけユーザー判断を受け取る。**rubric が客観的な停止条件になるため、ここでユーザーに承認してもらうことが「客観判定」の正当性を担保する**:

- **(A) この rubric で熟考へ進む**: ステップ4へ
- **(B) rubric / スコープを調整**: 基準・範囲を直してから熟考へ
- **(C) 追加探索**: 不足観点を指定してもらい、ステップ2に戻って explorer を追加起動

ユーザーの選択と（あれば）追加指示を `{RUN_DIR}/user-decisions.md` に追記する（なければ作成）。

> 本ゲートは熟考の物差しを決める分岐なので、対話実行では Auto mode でもユーザー応答を待つ。ただし応答が得られない無人実行（cron / CI / 上位エージェントからの自動起動 / smoke test 等）と判明した場合は、デッドロックを避けるため既定 **(A)** で継続し、`user-decisions.md` に「無人実行のため (A) を自動選択」と記録する。以降の熟考ループはゲートを挟まず自律で進める。

---

## ステップ 4: 熟考ループ（deliberator → synthesizer → gate、gate PASS まで反復）

`DEEPEN_COUNT` を `0` から数える。**ハードキャップ = 4 ラウンド**（`DEEPEN_COUNT` 0〜3）。各ラウンド `ROUND = DEEPEN_COUNT + 1` で以下を回す。

### 4-a: 熟考（deliberator 並列, Opus）

並列起動の前に、自己コミットメントとして **Fan-Out Gate 宣言**をターン本文に書く:

```
> **Fan-Out Gate（deliberator）**
> - THINKER_MODE = opus-panel
> - LENS_SET = [<レンズをカンマ区切りで全列挙>]
> - 起動体数 = <N>（= len(LENS_SET)）
> - 同一 function_calls ブロックに <N> 個の Agent 起動を並べる（1体ずつ・後追い起動は違反）
```

その直後、同一メッセージ内に `deliberator` を `Agent` ツールで **N 体同時起動**する。各体に渡すプロンプト:

- `RUN_DIR=[パス]`
- `RUBRIC_PATH={RUN_DIR}/rubric.md`
- `CONTEXT_PATH={RUN_DIR}/context.md`
- `LENS=[割り当てレンズ]`
- `ROUND={ROUND}`
- `DELIB_INDEX=NN`（`01` から）
- （ROUND ≥2）`PRIOR_POSITION_PATH={RUN_DIR}/position-{ROUND-1}.md` と `GATE_PATH={RUN_DIR}/gate-{ROUND-1}.md`
- 状況・問い（$ARGUMENTS）
- 「割り当てレンズで深く推論し、熟考レポート本体は `{RUN_DIR}/deliberation-{ROUND}-{DELIB_INDEX}.md` に書き出し、チャットには要約のみ返してください」

**モデル指定**: 各 deliberator を `model: opus` で起動する。

**レンズの割り当て**:

- **ROUND 1（既定3レンズ）**:
  1. `第一原理・機序` — 問いを基礎から組み立てて答えを導く
  2. `反証・レッドチーム` — 導かれつつある答えを攻撃し、対立仮説を steelman する
  3. `二次波及・境界条件` — 帰結・境界・前提が崩れる条件を洗う
- **ROUND ≥2**: 直前の `gate-{ROUND-1}.md` が挙げた **needs-thinking の不足**をレンズに割り当て、思考を不足箇所に照準する（例: 「基準3が未達 → その基準を埋めるレンズ」）。不足が3件未満なら既定レンズで補う。
問題が特に広い/曖昧なときは4〜5体に増やしてよい（レンズ駆動で増やす。数合わせで増やさない）。

### 4-b: 統合（synthesizer, Opus）

`synthesizer` を `Agent` ツールで1体起動する。プロンプト:

- `RUN_DIR=[パス]`
- `RUBRIC_PATH={RUN_DIR}/rubric.md`
- `CONTEXT_PATH={RUN_DIR}/context.md`
- `ROUND={ROUND}`
- （ROUND ≥2）`PRIOR_POSITION_PATH={RUN_DIR}/position-{ROUND-1}.md`
- 状況・問い
- 「そのラウンドの `{RUN_DIR}/deliberation-{ROUND}-*.md` を全て読み、1本の position に統合してください。position 本体は `{RUN_DIR}/position-{ROUND}.md` に書き出し、チャットには要約のみ返してください」

### 4-c: ゲート（gate, Opus）

`gate` を `Agent` ツールで1体起動する。プロンプト:

- `RUN_DIR=[パス]`
- `RUBRIC_PATH={RUN_DIR}/rubric.md`
- `CONTEXT_PATH={RUN_DIR}/context.md`
- `POSITION_PATH={RUN_DIR}/position-{ROUND}.md`
- `ROUND={ROUND}`
- 状況・問い
- 「position を rubric に一項目ずつ客観照合し、`VERDICT: PASS/FAIL` と不足の分類（needs-thinking / needs-exploration）を返してください。ゲートレポート本体は `{RUN_DIR}/gate-{ROUND}.md` に書き出してください」

### 4-d: 分岐

gate の返り値1行目の VERDICT で分岐する:

- **`VERDICT: PASS`** → 熟考は rubric の全基準を客観的に満たした。**ステップ5へ**。
- **`VERDICT: FAIL` かつ `DEEPEN_COUNT < 3`**:
  1. `gate-{ROUND}.md` に **needs-exploration** の不足があれば、その項目について `explorer` を追加起動する（`EXPLORATION_INDEX` は既存 `exploration-*.md` の最大値+1）。返ってきた探索を **3-1 の要領で `context.md` に追記集約**する。
  2. needs-thinking の不足は、次ラウンドの deliberator が `GATE_PATH` と `PRIOR_POSITION_PATH` を入力に再熟考して埋める（4-a のレンズ割り当てで照準）。
  3. `DEEPEN_COUNT += 1` して 4-a に戻る。
- **`VERDICT: FAIL` かつ `DEEPEN_COUNT == 3`**（ハードキャップ到達）→ ループを打ち切る。最新 `position-{ROUND}.md` を **「未達項目つきの暫定結論」**として扱い、ステップ5で **gate が未達とした基準を正直に明示**する。**PASS を捏造しない**（要件未達のまま「十分」と偽らない。ユーザーの指示は「客観的に満たしたら終了」であり、満たせなかったことは満たせなかったと報告する）。

> ℹ️ 熟考ループの内側にユーザーゲートは無い（自律で回す）。ユーザー確認はステップ3の rubric 承認1回のみ。

---

## ステップ 5: 最終熟考レポートの統合（docs/deepthink/）

到達した position・探索・ゲート判定を **1本で完結する熟考レポート**に統合し、プロジェクトローカルの見やすいパスに Write する。

### 自己完結の原則（最重要）

読者が中間ファイル（context / deliberation-* / position-* / gate-*）を一切開かなくても、**この1本だけで結論・論拠・トレードオフ・残る不確実性・十分性の判定まで意思決定できる**ように書く。要約に痩せさせない。結論を最上部に置く（逆ピラミッド）。

### テンプレート

`{RUN_DIR}/context.md` / `position-{最終}.md` / `gate-{最終}.md` を Read し、詳細を転記する:

```markdown
# [状況・問い] 熟考レポート

_作成: YYYY-MM-DD_

> 📌 このファイルは single source of truth。中間成果物を読まなくても、この1本で意思決定できるように書いてある。

## 0. Overview（結論先出し）
- 到達した結論・その確信度・最重要の論拠・残る最大の不確実性を数行で。**ここだけ読めば掴める**ように。
- 十分性: [gate PASS で全 rubric 基準充足 / ハードキャップ到達で未達項目あり（後述）]

## 1. 問い・背景・成功基準
[状況・問い、なぜ考えるのか、rubric（判定に使った成功基準）]

## 2. 探索で分かったこと（context）
[context.md の事実・不確実情報・対立・空白を根拠つきで転記]

## 3. 熟考の到達点（position）
[position の結論・主要な論拠・統合の過程を転記。多様なレンズがどう噛み合ったか]

## 4. 未解決の対立・残る不確実性
[潰しきれなかった対立、依存する前提、崩れる条件、まだ確かめられていないこと]

## 5. rubric 充足状況（gate 判定）
[gate の rubric 照合表を転記。全充足なら PASS の客観根拠、未達があればどの基準がなぜ未達かを明示]

## 付録: 中間成果物のパス / 探索出典
[exploration-* / context / deliberation-* / position-* / gate-* のパス、主要出典 URL、総ラウンド数・deliberator 延べ体数・THINKER_MODE]
```

### 出力先

- **既定**: `{PROJECT_ROOT}/docs/deepthink/{run_ts}-{run_feature}.md`（無ければ作成）。
- **中間成果物**は RUN_DIR（`${PROJECT_ROOT}/.ai-pir-runs/...`）に残し、付録にパスを載せる。
- **フォールバック**: `{PROJECT_ROOT}` が git リポジトリでない・書き込み不可のときのみ、その旨を伝えて `{RUN_DIR}/deepthink-report.md` に出す。
- 保存したら**必ずフルパス**を提示する。

---

## ステップ 6: 最終サマリーの提示

以下をユーザーに提示してください:

```
## Deepthink 完了サマリー

### 問い
[状況・問い]

### 熟考レポート
[プロジェクトローカルのフルパス（ステップ5 の出力先）]

### 到達した結論
[1〜3文。position の結論]

### 十分性（gate 判定）
- 結果: [PASS（全 rubric 基準充足）/ 未達あり（ハードキャップ到達）]
- rubric: 充足 [X] / 部分 [Y] / 未達 [Z]（全 [N] 基準）
- （未達ありの場合）未達の基準: [番号と要点]

### 熟考の規模
- ラウンド数: [N]（gate PASS で終了 / キャップ到達）
- deliberator 延べ体数: [N]（THINKER_MODE: opus-panel）
- 追加探索: [ループ中に探索を挟んだ回数]

### 未解決の対立・残る不確実性
- [あれば。無ければ「特になし」]

### 作業ディレクトリ
{RUN_DIR}
```
