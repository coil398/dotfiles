---
name: "retro"
description: "retrospector を単体で実行してパターンを汎化しエージェント定義を改善する。振り返り・ふりかえり・retrospective・改善サイクル・エージェント定義の見直し・パターン分析をしたいときに使う。`--meta` フラグでワークフロー骨格を改善するメタ自己改善モードを、`--dream` フラグで pir_pattern_registry を統合・整理する Dreaming モードを起動できる。ユーザーが /retro と入力したら必ずこのスキルを使う。"
argument-hint: "[--meta] [--dream] [対象プロジェクトのパス]"
---

# Retro — パターン汎化・エージェント改善

実在し、呼び出し元が今回の範囲として渡したログ・差分・検証結果からパターンを汎化し、エージェント定義の改善を提案します。このスキル本体（= メイン Codex）がオーケストレーターとなり、選択した role（`retrospector` または `meta-retrospector`）を Codex collaboration API の `spawn_agent`（`agent_type` は選択した role 名）で起動します。モデル指定は呼び出し側で行わず、対応する `.codex/agents/*.toml` の role 定義に委ねます。subagent 内からのネスト起動は行わず、起動責任はスキル本体に集約されます。
`--meta`（または `meta`）フラグが指定された場合、ワークフロー骨格そのものを改善するメタ自己改善モードを起動します。

引数: $ARGUMENTS

---

## ステップ 0a: 引数解釈

`$ARGUMENTS` はランタイムが提供する構造化された引数・フラグとして解釈し、メタモードフラグと対象プロジェクトパスを分離してください。shell の word splitting や glob 展開で再解釈してはいけません。対象パスは単一の引数要素として保持し、空白・glob 文字を含む場合も文字列全体を変更せずに扱います。

ランタイムから受け取る値を次のように確定します（値は配列要素または同等の構造化フィールドから取得し、平坦な文字列を未引用の shell loop で再分割しません）:

- `META_MODE`: 独立した `--meta` または `meta` 要素があれば `true`
- `DREAM_MODE`: 独立した `--dream` または `dream` 要素があれば `true`
- `PROJECT_PATH`: フラグ以外の対象パス要素。指定がなければ `pwd -P` を対象プロジェクトとして使う

ランタイムが構造化引数を提供できず、呼び出し元が raw `$ARGUMENTS` しか渡せない場合は、呼び出し元で引用を認識する parser を使って上記の3値へ変換してから処理します。引用を無視した Bash 展開、未引用の `$PROJECT_PATH`、`eval` は使用しません。

- `DREAM_MODE=true` の場合は meta-retrospector を Dreaming モードで起動する（最優先。`--meta` と同時指定された場合も Dreaming を優先）
- `META_MODE=true` の場合はステップ0b・1・2を実行する
- `META_MODE=false` かつ `DREAM_MODE=false` の場合は通常モードとしてステップ0b・1・2を実行する（プロセスは retrospector 側で分岐）

---

## ステップ 0b: メモリパスの解決

`PROJECT_PATH` の実体を対象として確認してください（指定がなければ現在のディレクトリ）。メモリ保存先は対象パスから導出せず、親が明示した既存の実体あるディレクトリだけを使います。未指定または不存在の場合は `PROJECT_MEMORY_DIR` を空のまま渡し、該当ログの読込・書込をスキップしてください。ディレクトリ作成、ホーム配下の候補探索、sanitize 名の推測は行いません。

```bash
PROJECT_ROOT="${PROJECT_PATH:-$(pwd -P)}"
[ -d "$PROJECT_ROOT" ] || {
  echo "PROJECT_ROOT must be an existing directory: $PROJECT_ROOT" >&2
  exit 1
}
PROJECT_ROOT="$(cd -P -- "$PROJECT_ROOT" && pwd -P)" || exit 1

PROJECT_MEMORY_DIR="${PROJECT_MEMORY_DIR:-}"
if [ -n "$PROJECT_MEMORY_DIR" ] && [ -d "$PROJECT_MEMORY_DIR" ]; then
  PROJECT_MEMORY_DIR="$(cd -P -- "$PROJECT_MEMORY_DIR" && pwd -P)" || PROJECT_MEMORY_DIR=""
else
  PROJECT_MEMORY_DIR=""
fi
echo "PROJECT_ROOT=$PROJECT_ROOT"
echo "PROJECT_MEMORY_DIR=${PROJECT_MEMORY_DIR:-<未指定>}"
```

`PROJECT_MEMORY_DIR` が指定されていても、そこに存在するファイルだけを読みます。親が指定していないメモリ・ログ・registry の代替パスを作ったり推測したりしません。

---

## ステップ 1: agent 選択と起動

`DREAM_MODE` / `META_MODE` の値に応じて起動する agent を選択する:

- `DREAM_MODE=true`: `meta-retrospector` を起動（Dreaming モード。registry の統合・整理。最優先）
- `META_MODE=true`: `meta-retrospector` を起動（メタ自己改善専任）
- いずれも `false` または未指定: `retrospector` を起動（通常モード専任）

スキル本体（メイン Codex）だけが `list_agents` と `spawn_agent` を実行します。選択した agent role を `spawn_agent`（`agent_type="retrospector"` または `agent_type="meta-retrospector"`）で起動し、subagent には追加委譲を許可しません。モデル引数は指定せず、対応する `.codex/agents/*.toml` の role 定義に委ねます。

共通プロンプトパラメータ（どの agent にも含める）:
- `PROJECT_MEMORY_DIR`（親が提示し、実在確認できた場合のみ。未指定なら空）
- `PROJECT_ROOT`（ステップ0bで取得したパス）
- `META_MODE=[true|false]`（ステップ0aで決定した値）
- `DREAM_MODE=[true|false]`（ステップ0aで決定した値）
- `CODEX_SKILLS_DIR`（今回ロードしたこの Skill の実体ディレクトリの親。対象プロジェクトから導出しない）
- `EXPERIMENTAL_PATH`（親が上記の実体から `${CODEX_SKILLS_DIR}/pir2/references/experimental.md` として解決し、実在する通常ファイルである場合のみ。不存在なら渡さず、実験評価を skip）
- `OBSERVATION_LOG_PATH`（親が明示した専有保存先で、実在確認できた場合のみ。未指定なら渡さず、観測書込を skip。ホームディレクトリから推測しない）
- `REGISTRY_PATH`（親が明示した既存 registry の通常ファイルのみ。未指定・不存在なら registry の読込・更新を行わない）
- `BACKUP_ROOT`（meta/Dreaming で親が明示した安全なバックアップ保存先のみ。未指定なら変更を適用しない）
- `RETRO_REPORT_PATH`（親が指定した未使用の出力 path と、その実体ある安全な親 directory。未指定ならファイルを作らず、結果を会話へ返す）
- `RUN_DIR`、`INNER_LOOP_COUNT`、`OUTER_LOOP_COUNT`、`VERDICT`（呼び出し元が実測して明示した場合だけ。未指定時に `0`・`MANUAL`・未生成 report を補完しない）

`CODEX_SKILLS_DIR` は、今回ロードした `SKILL.md` の実体ディレクトリを基点に親ディレクトリとして確定し、次のように実在確認します。対象プロジェクトの `.codex/skills` やホームディレクトリから同名ファイルを探してはいけません。

```bash
CODEX_SKILLS_DIR="${CODEX_SKILLS_DIR:?parent must provide the loaded Skill root}"
[ -d "$CODEX_SKILLS_DIR" ] || {
  echo "CODEX_SKILLS_DIR must be an existing directory: $CODEX_SKILLS_DIR" >&2
  exit 1
}
CODEX_SKILLS_DIR="$(cd -P -- "$CODEX_SKILLS_DIR" && pwd -P)" || exit 1
experimental_candidate="${CODEX_SKILLS_DIR}/pir2/references/experimental.md"
if [ -f "$experimental_candidate" ]; then
  EXPERIMENTAL_PATH="$experimental_candidate"
else
  EXPERIMENTAL_PATH=""
fi
```

読み取り path は親が提示した実在する対象だけを使い、書き込み path は専有先・実体ある親 directory・親の所有範囲を確認してから使います。role は親が渡した専有書込先（実結果の report、明示された観測 log、承認済みの registry/backup）以外へ書き込みません。既存 sandbox、backup、破壊保全、未承認の権限変更禁止を維持し、commit/push や保存先の新規推測は行いません。

追加メッセージ（agent / モード別）:
- `retrospector`（通常モード）: 「これは手動トリガーの振り返りです。親から渡された実在するログ・差分・計画・検証結果だけを読み、未生成の artifact を補完せず、再利用できる学び・改善・残るリスクを返してください。`EXPERIMENTAL_PATH` が渡され実在する場合だけ読み、Active な実験の観測更新が必要か判断してください。`REGISTRY_PATH` が渡された場合だけ、今回の実結果に基づく必要な更新をその専有先へ記録してください。`OBSERVATION_LOG_PATH` が渡された場合だけ、今回の実結果に基づく観測をその専有先へ記録してください。追加 agent の起動、未指定 path の探索、未承認の変更・commit/push は行わないでください。」
- `meta-retrospector`（メタモード）: 「これはメタ自己改善モードの手動トリガーです。親から渡された実在する `REGISTRY_PATH` の未処理フラグだけを読み、未指定・不存在ならその事実を返してください。変更案は提示して親またはユーザーの承認を待ち、承認後も親が指定した `BACKUP_ROOT` と個別ファイルだけを対象にします。保存先・権限・commit/push を推測または拡張しないでください。」
- `meta-retrospector`（Dreaming モード）: 「これは registry の Dreaming 統合モードです。Dreaming プロセス（D1〜D5）の分析だけを行い、親から渡された実在する `REGISTRY_PATH` の全内容を対象にします。`BACKUP_ROOT`、ユーザー承認、対象 path が揃わない場合は統合・上書きせず、必要条件を返してください。重複・陳腐化の候補とデータ損失リスクを報告し、自動削除・未指定 path の生成・権限変更は行わないでください。」

---

## ステップ 2: 結果の提示

retrospector の実際の出力（通常モードなら振り返りレポート、メタモードならメタ自己改善レポート）だけをユーザーに提示してください。`RETRO_REPORT_PATH` が実際に生成された場合だけその path を示し、未生成の report や未確認の verdict を補完しません。既にユーザーが承認した範囲は再確認せず、その範囲内の継続処理だけを親が role に渡します。

メタモード実行時に meta-retrospector からユーザー承認を求める問いかけが含まれていた場合、親（スキル本体）がユーザーの応答を確認し、承認された対象だけを同じ role に差し戻して処理を継続してください。subagent 自身に再起動・追加委譲をさせません。
