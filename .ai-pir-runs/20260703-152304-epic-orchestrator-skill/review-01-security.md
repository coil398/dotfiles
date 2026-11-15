VERDICT: FAIL

### 担当 role
security

### レビュー対象
- `/Users/kawasetakumi/dotfiles/.claude/skills/epic/SKILL.md`（新規、実在確認済み）
- `/Users/kawasetakumi/dotfiles/.claude/agents/epic-planner.md`（新規、実在確認済み）
- `CLAUDE.md` 追記分（`git diff CLAUDE.md` で確認）
- `.claude/skills/pir2/references/experimental.md` 追記分（`git diff` で確認）
- `.gitignore` 追記分（`/.ai-pir-runs/` 追加）

比較対象として `.claude/skills/pir2/SKILL.md`、`.claude/skills/pir2/references/{destructive-change-check.md, plan-choice-gate.md, fan-out-gate.md, implementation-delegation.md}`、`.claude/agents/planner.md`、`.claude/settings.json` / `.claude/settings.local.json`、`.claude/hooks/foreign-ssot-guard.sh` を Read した。

> ℹ️ 本レビュー実行時点で `.claude/skills/epic/SKILL.md`（139行）・`.claude/agents/epic-planner.md`（144行）は実在し、`CLAUDE.md` / `experimental.md` の差分も反映済みであることを `Read` と `git diff` で確認した（実装完了後の状態）。

---

### 判断根拠

#### 1. セキュリティ（OWASP / インジェクション等）

**bash injection（ステップ1）**: 対象コードは以下。

```bash
TASK="$ARGUMENTS"
case "$TASK" in
  "--codex "*) SUBTASK_SKILL="pir2codex"; TASK="${TASK#--codex }" ;;
  "--codex")   SUBTASK_SKILL="pir2codex"; TASK="" ;;
esac
run_feature="$(printf '%s' "$TASK" | tr -c 'a-zA-Z0-9' '-' | sed -E 's/-+/-/g; s/^-//; s/-$//' | cut -c1-32)"
```

- `$ARGUMENTS` の全使用箇所はダブルクォートで囲われている（`"$ARGUMENTS"` / `"$TASK"`）。unquoted 展開は1箇所もない（ask 1 の懸念点は該当なし）。
- `case "$TASK" in ... esac` はクォート済み変数へのグロブパターンマッチであり、TASK の中身がシェルコードとして再解釈されることはない。
- `TASK="${TASK#--codex }"` はパラメータ展開（プレフィックス除去）のみで、eval 等は介在しない。
- `run_feature` の生成は `printf '%s' "$TASK" | tr -c 'a-zA-Z0-9' '-' | ...` で英数字とダッシュのみに正規化しており、`EPIC_RUN_DIR` へのパストラバーサル（`../` 等）は原理的に生成不能。`SUBTASK_SKILL` はユーザー入力から一切導出されずリテラル `"pir2"` / `"pir2codex"` の2値のみ取りうる（`~/.claude/skills/${SUBTASK_SKILL}/SKILL.md` 参照パスへの注入経路なし）。
- このパターンは `pir2` / `pir2codex` / `debug` / `ir` / `research` / `writing-plan` / `review-pr` / `reviewer` / `refactor-advisor` / `deepthink` の全既存スキルが採用している `run_feature="$(printf '%s' "$ARGUMENTS" | tr -c 'a-zA-Z0-9' '-' | sed ...)"` と完全に同一の慣習であり、epic 固有の新規リスクは確認できなかった。
- **参考（本観点内の情報提供）**: `$ARGUMENTS` が Claude Code 側でどのように SKILL.md のプロンプトへ展開されるか（プロンプト構築時の文字列置換か、実行時の実 env var か）は本レビューの検証範囲外。もし前者（プロンプト文字列置換）であれば、TASK 文字列中に `"` や `` ` `` や `$()` を含む入力が理論上コンテキスト注入の起点になりうるが、これは epic 固有ではなく `$ARGUMENTS` を使う全既存スキルに共通する既存アーキテクチャ上の性質であり、今回の新規追加が悪化させたものではない。Low informational として後述の「担当外で気づいた点」に記載。

判定: epic のクォート・サニタイズは確認した限り正しく、既存慣習との整合も取れている。**この項目単独では High/Critical なし**。

#### 2. 認可・認証（destructive-change-check の bubble-up ゲート未区分 — High）

`.claude/skills/epic/SKILL.md` ステップ 3-4（103行目）:

> ネスト pir2 ランナーには「pir2 内部のユーザー確認ゲート（plan-choice-gate / 6.5 未解決事項 / continuation-gate 等）に到達したら、ユーザーには聞けないので**保守的デフォルト**を選び、その決定点を `{サブ RUN_DIR}/deferred-decisions.md` に記録し、返り値要約の `DEFERRED_USER_DECISIONS` に列挙すること」と指示...epic 本体はサブ pir2 完了ごとに `DEFERRED_USER_DECISIONS` を集約し、判断が本質的にブロッキングなものはユーザーに提示します（軽微なものは Phase 3 サマリーで一括報告）。

`.claude/skills/pir2/references/destructive-change-check.md` を Read して確認したところ、この参照ファイルは pir2 のステップ 5.7 として存在し、明記されている:

> 破壊的変更フラグまたは動作変更フラグが ON のときに「reviewer 観点を減らしたい」「tester を省略したい」「フルスイートをスキップしたい」と判断したくなった場合、**スキル本体の独断は禁止**。必ずユーザーに確認する。**Auto mode でもこのユーザー確認は省略不可**。CORE:COMMON「auto mode でも取り消し困難な操作は確認必須」原則と同じ扱い。

問題点:

1. epic ステップ 3-4 の列挙（plan-choice-gate / 6.5 未解決事項 / continuation-gate）は「等」で締められており、`destructive-change-check` がこの「保守的デフォルト＋事後報告」の対象に含まれるのか、それとも例外的に即時ユーザー確認が必要な区分として扱われるのかが**明示されていない**。標準 pir2 では destructive-change-check・plan-choice-gate ともに「Auto mode でも省略不可」と明記された最も強いブロッキングゲートだが、epic の bubble-up 指示はこれらを他の軽量なゲート（6.5 未解決事項等）と同列に扱い、一律「保守的デフォルトを選んで先に進む」処理に流し込んでいる。
2. 「判断が本質的にブロッキングなものはユーザーに提示する」「軽微なものは Phase 3 サマリーで一括報告」の**判定基準が定義されていない**。epic 本体（LLM）の主観的判断に委ねられており、客観的なルーブリック（例:「destructive-change-check の破壊的変更フラグ ON は無条件でブロッキング扱いとする」）が欠落している。
3. **タイミングの問題**: この確認は「サブ pir2 完了ごとに」行われる。ネスト pir2 は explorer→planner→implementer→reviewer→tester まで自律的に完走してから初めて epic 本体に結果を返す設計であり、破壊的操作（既存ファイル削除・OpenAPI フィールド削除・golden ファイル書き換え等）はこの時点で**すでに working tree 上で実行済み**である。「ユーザーに提示する」のタイミングが実質的に「実行後の事後承認（rubber-stamp）」になっており、ask 4 が懸念する「破壊的操作がユーザー承認なく走る」の構造的な抜け穴に該当する。
4. 緩和要因: (a) epic パイプライン全体を通じて `git commit` を行う指示は一切存在しない（grep で確認済み。ステップ 3-2 にも「ネスト pir2 は自前でコミットしないため」と明記）ため、変更は最終的にユーザーが `git diff` でレビューしてコミットするまで可逆である。(b) Phase 1.5（ステップ 2.5）は「サブタスク一覧＋依存グラフ＋各 pir2 タスク記述」の事前承認を Auto mode でも必須としており、Phase 2 着手前の集合的な人間ゲートは機能している。(c) 本タスクは `experimental.md` で試験実装として明示され、Rejection Criteria に「サブ pir2 のユーザーゲート委譲が機能せず、独断のスコープ縮小・仕様変更が発生する」が観測項目として組み込まれている。

上記緩和要因により Critical ではなく **High** と判定する。ただし、CLAUDE.md の「取り消し困難な操作は確認必須」というグローバル原則を、この epic 設計が特定カテゴリ（destructive-change-check）について客観基準なしに「保守的デフォルト＋事後報告」へ格下げしている点は、実装着手前に是正すべき設計ギャップである。

#### 3. シークレット漏洩

- 2 新規ファイル・2 追記分に API キー・パスワード・トークン・秘密鍵等のハードコードは確認できなかった（純粋なドキュメント著述であり、コード実行結果や環境変数展開が成果物に残る箇所もない）。
- `.claude/agents/epic-planner.md` の Write は PostToolUse hook（sync-opencode/sync-codex）を自動発火させる。生成先 (`~/.config/opencode/agents/epic-planner.md` 等) にも同一内容がそのまま複製されるだけであり、新規のシークレット露出経路は生じない。

問題なし。

#### 4. 依存脆弱性

新規のライブラリ・パッケージ依存は導入されていない（ドキュメント・エージェント定義のみ）。該当なし。

#### 5. グローバルファイル汚染（ask 2、担当観点内の追加確認）

- `.claude/` はグローバル SSOT であり、foreign-ssot-guard（`.claude/hooks/foreign-ssot-guard.sh`）の検査対象パスパターン（`SSOT_PATHS_RE`）は `.claude/agents/` と `.claude/skills/` を含む。今回の新規ファイル2点・CLAUDE.md 追記はこのガードの対象範囲に入る。
- 3 ファイルを全文 Read した結果、Unity/Figma 等の具体プロジェクト名・クラス名・テーブル名・API エンドポイント名の混入は確認できなかった。「サブシステム」「ディレクトリ」「WHAT」「DAG」等の汎用語彙のみで構成されている。plan.md の「変更不要」節・「注意点・リスク」節が明記する「プロジェクト固有名を混入させない」方針が実際に守られている。
- Observation Log セクション（epic-orchestrator-nested-pir2 実験）も、実データは git 管理外の `~/.claude/memory/experimental_observations.md` に逃がす設計になっており、既存の nested-explorer 実験と同一パターンを踏襲している。

問題なし。

#### 6. 自律オーケストレーションの暴走防止（ask 3、担当観点内の追加確認 — Medium）

- **深さバジェット（垂直方向）**: L0→L1→L2 に頭打ちし、L3 相当（L2 配下 sub-agent のさらなる explorer ネスト）は抑制、深さ超過拒否時は `IMPLEMENTATION_ACTOR=main` の inline フォールバックへ切替える設計になっている。`IMPLEMENTATION_ACTOR=main` は `~/.claude/skills/pir2/references/implementation-delegation.md` で定義済みの正規の fallback 値であり、存在しない用語の参照ではない（grep で確認）。この軸は妥当に設計されている。
- **サブタスク数（水平方向）の上限が未定義**: `epic-planner.md` の「分割の粒度指針」は「過度な細粒度化は並列運用コストが逆転するので避ける」という定性的ガイドラインのみで、サブタスク総数・DAG サイズに対する**数値上限が一切ない**。`epic-planner` の再起動（EXPLORATION_NEEDED ループ）には「最大5回」の明示キャップがあるのに対し（SKILL.md 65行目で確認）、生成される DAG のノード数自体には歯止めがない。大規模タスクの記述次第では epic-planner が多数のサブタスクを生成し、各サブタスクがそれぞれ explorer/planner/implementer/reviewer/tester を内包するフル pir2 サイクルを起動するため、理論上リソース消費が乗算的に増大する（OWASP API4:2023 Unrestricted Resource Consumption に類する懸念）。
- **緩和要因**: Phase 1.5（ステップ 2.5）で「サブタスク一覧＋依存グラフ」が Auto mode でも必須の事前承認対象になっており、Phase 2 着手前にユーザーが目視でサブタスク数を確認できる人間ゲートが存在する。したがって完全に無人でのリソース枯渇は起こりにくい。
- 判定: Critical/High には至らないが、防御多層化の観点で数値上限（例:「サブタスク数が N を超える場合は分割粒度の見直しを提案してからユーザー確認を挟む」）を明記することを推奨。**Medium**。

#### 7. 深さバジェット超過時の安全性（ask 5、担当観点内の追加確認 — Medium/Low）

- SKILL.md 3-3 は「L2 での `Agent` 起動が深さ超過で拒否された場合」を前提に inline フォールバックを指示しているが、L3 以深での実プラットフォーム挙動（クリーンな reject か、不明瞭な失敗・ハングか）は plan 自身が「未確認」と明記している。フォールバックはプロンプトレベルの指示であり、プラットフォームが「拒否」を検知可能な形で返さない場合（例: サイレントタイムアウト）、中途半端な状態で停止するリスクは技術的に排除されていない。
- 緩和要因: `experimental.md` の Rejection Criteria に「ネスト深さ超過でサブ pir2 が起動・完遂できない事象が頻発する」が明示的に観測対象として組み込まれており、初回実行時の検証事項として扱う設計になっている（plan 内でも明示）。試験実装としての運用姿勢は妥当。
- 判定: 実運用で検証されるまでの暫定リスクとして **Medium/Low**（VERDICT には計上せず、本観点内の情報提供として記載。次アクションに推奨事項として含める）。

---

### 問題一覧

- **High** `.claude/skills/epic/SKILL.md:103`（ステップ 3-4） — 破壊的変更ゲート（`destructive-change-check.md`。pir2 では「Auto mode でも省略不可」と明記）が、bubble-up 指示の「保守的デフォルト＋事後報告（軽微なら Phase 3 一括報告）」対象に含まれるか明示されておらず、「本質的にブロッキング」/「軽微」の客観判定基準もない。ネスト pir2 は破壊的操作を実行完了してから epic 本体に結果を返す設計のため、実質的に「実行後の事後承認」になり、ユーザー承認前に破壊的操作（既存ファイル削除・スキーマ破壊的変更等）が working tree 上で完了しうる。
  → 修正方法: ステップ 3-4 に「`destructive-change-check.md` の破壊的変更フラグ or 動作変更フラグが ON になった場合は、無条件で『本質的にブロッキング』として扱い、そのネスト pir2 の完了直後（Phase 3 サマリーへの遅延禁止）に epic 本体がユーザーへ提示する」旨を明記する。可能であれば「本質的にブロッキング」判定を epic-planner の DAG 設計段階で予見できるものは Phase 1.5 の事前承認に含める（実装詳細を出さない epic-planner の設計方針とは別に、「このサブタスクは破壊的変更を伴う可能性が高い」というフラグだけでも Phase 1.5 の提示内容に含めることを検討）。

### 担当外で気づいた点（参考）

- `.claude/skills/epic/SKILL.md:32`（`$ARGUMENTS` の展開メカニズム） — Claude Code の `$ARGUMENTS` 展開が実行時 env var ではなく SKILL.md プロンプト文字列へのテキスト置換である場合、TASK 中の `"` / `` ` `` / `$()` がコンテキスト注入の起点になりうる理論上の懸念がある。ただし epic 固有ではなく `$ARGUMENTS` を使う pir2 系スキル全体（10 ファイル以上）に共通する既存アーキテクチャ上の性質であり、epic が新規に導入・悪化させたものではないため VERDICT には算入しない。family 全体で検証する価値はある（別タスクとして提起を推奨）。
- `.claude/skills/epic/SKILL.md`（ステップ4） — Phase 3 の統合修正サブタスク追加（「問題があれば統合修正用のサブタスクを1本追加起動する」）に明示的な回数上限がない。統合修正自体が新たな結合問題を生んだ場合の反復を止める仕組みが記述されていない（Low、correctness/quality 領域寄りの論点でもあるため参考記載に留める）。

### 良好点

- ステップ1の bash はすべての `$ARGUMENTS`/`TASK` 使用箇所でダブルクォートが徹底されており、既存 pir2 系スキルと同一のサニタイズパターン（英数字+ダッシュのみへの正規化）を踏襲している。`SUBTASK_SKILL` はユーザー入力から導出されない固定リテラルのみを取るため、`~/.claude/skills/${SUBTASK_SKILL}/SKILL.md` への参照パスにインジェクション余地がない。
- epic パイプライン全体を通じて `git commit` / `git push` / `git add` の指示が一切なく（ネスト pir2 も「自前でコミットしない」と明記）、全ての変更が最終的にユーザーレビュー前の working tree に留まる設計になっている。これは「取り消し困難な操作」を実質的に緩和する重要な安全設計。
- Phase 1.5（サブタスク一覧＋DAG のユーザー承認ゲート）が Auto mode でも例外なしと明記されており、無人暴走の一次的な歯止めとして機能する。
- グローバル SSOT の汚染防止（プロジェクト固有名の不使用）が徹底されており、foreign-ssot-guard の検査観点からも問題は見当たらない。
- `IMPLEMENTATION_ACTOR=main` 等、既存 pir2 の正規の技術用語を誤用なく引用しており、深さバジェット超過時のフォールバック指示自体は既存語彙に忠実。

### 次のアクション

1. **（High・必須）** `.claude/skills/epic/SKILL.md` ステップ 3-4 に、`destructive-change-check.md` の破壊的変更フラグ／動作変更フラグが ON の場合は無条件で「本質的にブロッキング」として扱う旨を明記し、Phase 3 での事後一括報告の対象から明示的に除外する。「本質的にブロッキング」と「軽微」の判定基準（少なくとも destructive-change-check・plan-choice-gate の複数案提示ケースは無条件ブロッキング）を客観的に記述する。
2. **（Medium・推奨）** `epic-planner.md`「分割の粒度指針」に、サブタスク総数の目安上限（例: 一定数を超えたら分割粒度の見直しを提案してからユーザー確認を挟む）を追記し、水平方向の暴走防止を深さバジェットと対称に整備する。
3. **（Medium/Low・推奨）** Phase 3 の統合修正サブタスク追加に反復回数の上限（例: 最大1〜2回、それでも解消しなければユーザーに判断を委ねる）を明記する。
4. 上記修正後、再レビューでは destructive-change-check の扱いが実際に「無条件ブロッキング」として反映されているかを重点的に確認する。
