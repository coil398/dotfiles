---
name: "deepthink"
description: "特定の状況・問いを多エージェントで深く深く考え抜くワークフロー。オーケストレーター（スキル本体）が探索し、複数の思考エージェント（deliberator）に多様なレンズで熟考させ、synthesizer が1本に統合し、gate が成功基準（rubric）に照らして客観的に十分性を判定する。満たすまで（必要なら追加探索を挟みつつ）ループし、gate が全基準の充足を客観的に確認できたら終了する。「じっくり考えたい」「深く考えて」「考え抜いて」「多角的に検討して」「結論を出したいが難しい」「意思決定を詰めたい」「〜すべきか徹底的に考えて」「腹落ちする答えがほしい」といった要望に対応する。単なる調査や仮説出し（それは /research）、コード実装・バグ修正・デバッグ（それは /pir2, /debug, /ir）ではなく、答えの出しにくい状況・問いをループで深掘りして客観的に十分な結論へ到達させたいときに使う。ユーザーが /deepthink と入力したら必ずこのスキルを使う。"
argument-hint: "[深く考えたい状況・問い]"
---

<!-- Codex native overlay: seeded from .agents/skills; edit here for Codex mechanics -->

# Deepthink — 探索 → 熟考 → 統合 → ゲート（十分まで反復）

多エージェント熟考ワークフローを実行します。このスキル本体（= メイン Codex）が**オーケストレーター**となり、explorer（探索）→ 集約 + rubric 確定（オーケストレーター自身）→ deliberator（熟考・複数並列）→ synthesizer（統合）→ gate（十分性判定）を Codex collaboration API で起動・制御します。gate が FAIL を返す限り、不足の種類に応じて追加探索を挟むか再熟考させ、**gate が rubric の全基準の充足を客観的に確認して PASS を出すまでループ**します。制御フロー（起動・ループ管理・VERDICT 集約・ユーザー確認ゲート）はスキル本体に集約し、サブからのネスト起動は read-only の探索（explorer）に限ります。

**状況・問い**: $ARGUMENTS

各フェーズの担当 role（モデルは各 role 定義が所有）:

| フェーズ | 担当 role |
|---------|------------|
| 探索 | explorer（最大4体並列） |
| 集約 + rubric 確定 | オーケストレーター（スキル本体） |
| 熟考 | deliberator（既定3体並列 / solo は1体） |
| 統合 | synthesizer |
| ゲート（十分性判定） | gate |

> ℹ️ `/deepthink` は探究・熟考ワークフローであり、handoff 連携・プロジェクトメモリ追記は行いません（`HANDOFF_PATH` / `PROJECT_MEMORY_DIR` は不要）。

## 思考モデルのモード（THINKER_MODE）

熟考フェーズの deliberator の構成を切り替える:

| モード | 構成 | 選択条件 |
|--------|------|----------|
| `panel`（既定） | deliberator を**複数体並列**（既定3体、多様なレンズ） | 既定。多様な視点を並列で得て synthesizer が統合する |
| `solo` | deliberator を**1体**（全レンズを1体で内省的に網羅） | `$ARGUMENTS` に `--solo` が含まれるとき。単一 role に長考させたいとき |

- 既定は `panel`（確実に動く構成）。`$ARGUMENTS` から `--solo` フラグを検出したら `solo` に切り替え、フラグ語はタスク文言から除外する。
- **role configuration mismatch は blocker**: `agent_type` が未登録、対応する `.codex/agents/<role>.toml` が不正・不在、または role 設定の解決に失敗した場合は configuration-wide mismatch として扱い、同じ broken role をさらに起動しない。`panel` への切替、モデル指定の変更、別 role による代替も行わず、証拠とともに停止理由をサマリーへ記録する。
- **`panel` retry の条件**: `solo` の deliberator 1体の単一起動だけが、タイムアウトや一時的な transport failure などの transient failure で失敗し、`deliberator` role の設定が有効で共有設定に影響していないことを確認できた場合に限り、`panel` を再試行できる。設定不整合・設定解決失敗・原因不明の失敗では再試行せず blocker とする。

---

## ステップ 0: RUN_DIR の確定

以下の Bash で `PROJECT_ROOT` / `RUN_DIR` を確定し、以降のすべてのステップで使用してください（artifact root の SSOT は `${HOME}/.ai-pir-runs`）:

```bash
PROJECT_ROOT="$(pwd)"
PROJECT_ROOT_REAL="$(pwd -P)"
run_ts="$(date +%Y%m%d-%H%M%S)"
run_feature="$(printf '%s' "$ARGUMENTS" | tr -c 'a-zA-Z0-9' '-' | sed -E 's/-+/-/g; s/^-//; s/-$//' | cut -c1-40)"
[ -z "$run_feature" ] && run_feature="deepthink"
# RUN_DIR is an external artifact root. Refuse symlinks and non-directories so
# workflow output cannot be redirected into the repository (or another path).
RUN_ROOT="${HOME}/.ai-pir-runs"
if [ -L "$RUN_ROOT" ]; then
  printf '%s\n' "RUN_ROOT must not be a symlink: $RUN_ROOT" >&2
  exit 1
fi
if [ -e "$RUN_ROOT" ] && [ ! -d "$RUN_ROOT" ]; then
  printf '%s\n' "RUN_ROOT exists but is not a directory: $RUN_ROOT" >&2
  exit 1
fi
mkdir -p "$RUN_ROOT"
if [ ! -d "$RUN_ROOT" ] || [ -L "$RUN_ROOT" ]; then
  printf '%s\n' "RUN_ROOT is not a real directory: $RUN_ROOT" >&2
  exit 1
fi
RUN_ROOT_REAL="$(cd "$RUN_ROOT" && pwd -P)"
case "$RUN_ROOT_REAL" in
  "$PROJECT_ROOT_REAL"|"$PROJECT_ROOT_REAL"/*)
    printf '%s\n' "RUN_ROOT must be outside PROJECT_ROOT: $RUN_ROOT_REAL" >&2
    exit 1
    ;;
esac
RUN_DIR="${RUN_ROOT}/${run_ts}-${run_feature}"
if [ -e "$RUN_DIR" ] || [ -L "$RUN_DIR" ]; then
  printf '%s\n' "RUN_DIR already exists or is a symlink: $RUN_DIR" >&2
  exit 1
fi
if ! (umask 077 && mkdir "$RUN_DIR"); then
  printf '%s\n' "RUN_DIR reservation failed (existing path or race): $RUN_DIR" >&2
  exit 1
fi
if [ ! -d "$RUN_DIR" ] || [ -L "$RUN_DIR" ]; then
  printf '%s\n' "RUN_DIR is not a real directory: $RUN_DIR" >&2
  exit 1
fi
echo "PROJECT_ROOT=$PROJECT_ROOT"
echo "RUN_DIR=$RUN_DIR"
```

> RUN_DIR は repository 外の中間 artifact 専用です。このワークフローが生成する探索・熟考成果物は repository の concrete implementation ではありません。実装変更が必要になった場合は、別途 `/pir2` などの実装ワークフローへ委譲してください。

以降の各subagentへのプロンプトには必ず `RUN_DIR=[パス]` を含めてください。

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

## ステップ 2: 探索フェーズ（explorer）

状況・問いを独立したサブ問いに分割し、`list_agents` で実行中の体数を確認したうえで、`spawn_agent` に `agent_type="explorer"` を渡して調査を委譲します。**メイン Codex が直接 Glob/Grep/Read/WebSearch/WebFetch で調べてはいけません**（`AGENTS.md (shared SSOT)`「コードベース探索の委譲」）。

### 起動ルール

- **最低1体起動**（問いの規模にかかわらず初回探索は必須）
- **最大4体並列**: 独立したサブ問い（観点・情報源・対象）に分割できるなら並列起動する
- **モデル指定はしない**（`explorer` role の `.codex/agents/explorer.toml` に委ねる）
- **情報源は Web + ローカルの両方**

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

## ステップ 3: 集約 + rubric 確定 + ユーザーゲート（オーケストレーター）

### 3-1: 集約（サブに委譲せず、スキル本体自身が行う）

全 `{RUN_DIR}/exploration-*.md` を Read し、スキル本体（メイン Codex）が探索結果を熟考の土台となる背景ブリーフに統合し、`{RUN_DIR}/context.md` に Write する:

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

### 4-a: 熟考（deliberator 並列）

並列起動の前に、自己コミットメントとして **Fan-Out Gate 宣言**をターン本文に書く:

```
> **Fan-Out Gate（deliberator）**
> - THINKER_MODE = [panel | solo]
> - LENS_SET = [<レンズをカンマ区切りで全列挙>]
> - 起動体数 = <N>（panel は len(LENS_SET)、solo は 1）
> - 同一 collaboration 呼び出しブロックに <N> 個の `spawn_agent` を並べる（1体ずつ・後追い起動は違反）
```

その直後、同一メッセージ内に `deliberator` role を `spawn_agent`（`agent_type="deliberator"`）で **N 体同時起動**する。各体に渡すプロンプト:

- `RUN_DIR=[パス]`
- `RUBRIC_PATH={RUN_DIR}/rubric.md`
- `CONTEXT_PATH={RUN_DIR}/context.md`
- `LENS=[割り当てレンズ]`
- `ROUND={ROUND}`
- `DELIB_INDEX=NN`（`01` から）
- （ROUND ≥2）`PRIOR_POSITION_PATH={RUN_DIR}/position-{ROUND-1}.md` と `GATE_PATH={RUN_DIR}/gate-{ROUND-1}.md`
- 状況・問い（$ARGUMENTS）
- 「割り当てレンズで深く推論し、熟考レポート本体は `{RUN_DIR}/deliberation-{ROUND}-{DELIB_INDEX}.md` に書き出し、チャットには要約のみ返してください」

**モデル指定**: `panel` / `solo` ともに `deliberator` role の `.codex/agents/deliberator.toml` に委ね、起動呼び出しでは `model` を上書きしない。`panel` retry は上記の transient failure 条件を満たす場合だけ許可する。

**レンズの割り当て**:

- **ROUND 1（既定3レンズ）**:
  1. `第一原理・機序` — 問いを基礎から組み立てて答えを導く
  2. `反証・レッドチーム` — 導かれつつある答えを攻撃し、対立仮説を steelman する
  3. `二次波及・境界条件` — 帰結・境界・前提が崩れる条件を洗う
- **ROUND ≥2**: 直前の `gate-{ROUND-1}.md` が挙げた **needs-thinking の不足**をレンズに割り当て、思考を不足箇所に照準する（例: 「基準3が未達 → その基準を埋めるレンズ」）。不足が3件未満なら既定レンズで補う。
- `solo` の場合は全レンズを1体のプロンプトに束ねて渡す（「第一原理 / 反証 / 二次波及の3視点を内省的にすべて通せ」）。

問題が特に広い/曖昧なときは panel を4〜5体に増やしてよい（レンズ駆動で増やす。数合わせで増やさない）。

### 4-b: 統合（synthesizer）

`synthesizer` role を `spawn_agent`（`agent_type="synthesizer"`）で1体起動する。モデル引数は指定せず、`.codex/agents/synthesizer.toml` の role 定義に委ねる。プロンプト:

- `RUN_DIR=[パス]`
- `RUBRIC_PATH={RUN_DIR}/rubric.md`
- `CONTEXT_PATH={RUN_DIR}/context.md`
- `ROUND={ROUND}`
- （ROUND ≥2）`PRIOR_POSITION_PATH={RUN_DIR}/position-{ROUND-1}.md`
- 状況・問い
- 「そのラウンドの `{RUN_DIR}/deliberation-{ROUND}-*.md` を全て読み、1本の position に統合してください。position 本体は `{RUN_DIR}/position-{ROUND}.md` に書き出し、チャットには要約のみ返してください」

### 4-c: ゲート（gate）

`gate` role を `spawn_agent`（`agent_type="gate"`）で1体起動する。モデル引数は指定せず、`.codex/agents/gate.toml` の role 定義に委ねる。プロンプト:

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
  1. `gate-{ROUND}.md` に **needs-exploration** の不足があれば、その項目について既存 explorer を再利用できる場合は `followup_task`、できない場合は `spawn_agent`（`agent_type="explorer"`）で追加起動する（`EXPLORATION_INDEX` は既存 `exploration-*.md` の最大値+1）。返ってきた探索を **3-1 の要領で `context.md` に追記集約**する。
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
- **中間成果物**は RUN_DIR（`${HOME}/.ai-pir-runs/...`）に残し、付録にパスを載せる。RUN_DIR は repository 外の artifact 専用であり、concrete implementation の置き場ではない。
- **フォールバック**: `{PROJECT_ROOT}/docs/deepthink/` に最終レポートを書けないときのみ、その旨を伝えて `{RUN_DIR}/deepthink-report.md` に出す。
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
- deliberator 延べ体数: [N]（THINKER_MODE: [panel | solo]）
- 追加探索: [ループ中に探索を挟んだ回数]

### 未解決の対立・残る不確実性
- [あれば。無ければ「特になし」]

### 作業ディレクトリ
{RUN_DIR}
```
