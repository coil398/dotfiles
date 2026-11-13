# harness-run bench

Pythonの実装課題を同じ条件で実行し、公開テストと非公開テストで採点します。実行には`python3`、`uv`、`git`と対象runnerが必要です。

## Fixture

```text
fixtures/<name>/
  task.md
  fixture.json
  workspace/             # package・docs・公開テスト
  private/
    tests/test_<area>.py  # 分野別の非公開テスト
    reference/           # 許可対象の正解実装（workspaceと同じ相対path）
    calibration.md       # fixture担当の検証記録
```

`fixture.json`の形式は次のとおりです。

```json
{
  "name": "example",
  "axes": ["difficulty", "complexity"],
  "suite": "capability",
  "allowed": ["pkg/", "docs/NOTES.md"],
  "public_tests": ["tests/"],
  "grading_timeout_s": 300,
  "uv_with": ["example-package==1.0.0"]
}
```

`axes`は負荷の種類を表すlistで、`difficulty`・`complexity`・`volume`を使います。複数軸を持つfixtureは各軸に含めます。`suite`は実行セットの分類です。

| suite | fixture |
|---|---|
| `capability` | `reference_scope`, `toml_edit_batch`, `tagged_regex`, `incremental_sat`, `bulk_ops`, `record_codecs` |
| `efficiency` | `inventory`（smoke）, `ledger`, `stream_frames` |
| `archived` | `scheduler`, `config_layers`, `catalog_query`, `sync_replay`, `policy_refactor`, `temporal_join` |
| `conventions` | `conv_billing`, `conv_shopkit`, `conv_jobs`（AGENTS.mdの規約遵守。`conv_*`分野が規約、他が挙動。`briefs/<fixture>.md`は親が渡す規約抜粋で、`brief=<bench>/briefs/{task}.md`で使う） |

`allowed`は末尾が`/`ならdirectory内、それ以外は完全一致のfileです。各非公開テストfileが1分野で、parametrizeを展開したcase数を分野間で揃えます。既存のinventory・ledger・schedulerでは公開テストを同名の1分野にコピーしています。

`uv_with`は省略可能な追加依存packageのlistです。各要素を追加の`--with`引数として、公開・非公開テストとreferenceの採点に渡します。採点は`--offline`で実行するため、pytestと追加依存はローカルのuv cacheから解決できる必要があります。fixtureの`task.md`にも追加依存を含む実行commandを記載します。

実装者の作業directoryには`workspace/`の内容だけをコピーし、Gitのbaselineを作ります。`task.md`は別pathのpromptとしてrunnerに渡します。終了後、非公開テストを投入する前にbaselineとの差分を調べます。採点には新しいdirectoryを作り、原本の`workspace/`に許可対象の最終変更・追加・削除だけを反映して、`private/tests/`を`tests_hidden/`へコピーします。公開テストは原本を使います。

これは作業directoryから非公開テストを除く構成です。同一ユーザーがhost上の別pathを読むことを防ぐアクセス隔離ではありません。

## 採点と結果

起動時に選択fixtureのreferenceを各1回採点し、公開・非公開の全通過を確認します。失敗時はモデル呼出し前に停止し、ログのpathを表示します。referenceのJUnitから分野ごとのcase数を確定します。正規表現による関数数は使いません。

公開・非公開テストは別々に、採点directoryのrootで次の形式により実行します。

```bash
uv run --offline -q --no-project --with pytest python -m pytest -q tests/ --junitxml=public.xml
uv run --offline -q --no-project --with pytest python -m pytest -q tests_hidden --junitxml=hidden.xml
```

- `raw_score`はhidden passed / referenceのhidden totalです。分野別にもpassed・total・failed・errors・skipped・scoreを保存します。失敗・error・skip・未収集は加点しません。
- 範囲外変更または公開テスト改変はinvalidです。`eligible_score`はinvalidなら0、それ以外はraw scoreです。
- `success`はrunnerの正常完走、公開テスト全通過、hidden満点、validのすべてを満たす場合です。runner timeoutでも残った成果物を採点し、statusはtimeoutのまま保存します。
- `--budget-s SEC`指定時、`within_budget`はrunnerが正常完走し、`eligible_score`が1.0で、agentのwall timeが予算以下の場合にtrueです。予算超過でも品質点は保持し、runner timeoutは予算内完遂に数えません。未指定時の`budget_s`と`within_budget`はnullです。
- hidden JUnitのfailure messageに`TimeoutExpired`または`timed out`を含むcaseは、分野別の`perf_timeout`に数えます。得点は0のままです。採点command全体のtimeoutは採点infra失敗として扱います。
- 採点コマンドの起動失敗・timeout・JUnit取得失敗などは`grading_infra_failure`として区別し、scoreをnullにします。成果物によるcollection errorは0点として分母を維持します。
- `axes`はtrial開始時のfixture分類を保存します。結果の軸別集計では保存済み分類を使います。
- `duration_s`はagent実行のwall time、`grading_duration_s`は採点時間です。usageと`effort_applied`も保存します。

`results.jsonl`と各trialの`result.json`に結果を保存します。各trialの`public.stdout`・`public.stderr`・`hidden.stdout`・`hidden.stderr`・JUnit XML、起動時の`reference/`ログ、`bench.log`で処理を確認できます。

`summary.md`は構成×fixtureごとの平均eligible、full-pass率、予算内完遂（件数/trial数）、invalid数、timeout数、採点infra失敗数、wall・requests・total_tokensの中央値、計測欠測数、効率と分野別平均raw score・`perf_timeout`合計を載せます。予算未指定の予算内完遂は`-`表示です。overallの得点はfixture平均の単純平均です。nullの得点は平均から除外し、infra失敗数を別表示します。

軸別行は対象fixture一覧、採点済み／予定trial数、得点欠測数、未取得trial数、invalid・timeout・grading infra件数、wall・tokens中央値とそれぞれの欠測数を表示します。予定数はfixture数×`--repeat`です。得点とfull-pass率は、fixture内の採点済みtrial平均を求めてからfixture間で単純平均します。infraのnullは両方の平均から除外し、全trial欠測のfixtureも平均から除外します。timeoutの部分点は得点に含め、full-passには数えません。複数軸の行は重複するため合算しません。overallの得点は各fixtureを1回だけ数えます。

`volume`の満点area数／全area数は、各trialのareaを合計し、`score == 1`だけを満点として数えます。nullのareaも分母に含め、area欠測数を表示します。これはfixtureを等しく重み付けした軸別得点とは別の観測値です。wall・tokens中央値は対象trialの観測値をまとめて求め、nullは除外します。未取得trialは計測欠測数に混ぜず別表示します。

`total_tokens = total_input + output`とし、reasoningは再加算しません。欠測は0にせず、中央値では除外して欠測数を表示します。効率は`Σeligible_score / Σtotal_tokens × 100000`です。得点かtokensが欠測する行を含む集計では効率を欠測表示にします。

### マトリックス

`summary.md`の「マトリックス」は`difficulty`・`complexity`・`volume`・`overall`ごとに、行を`harness:model[:flags]`、列をeffortにした表を載せます。flagが異なる構成は別行です。列は結果にある適用effortだけを`low`・`medium`・`high`・`xhigh`・`max`の順で並べ、それ以外の値は末尾に名前順で並べます。

セルは`0.82 (67%) · 410k tok · 95s`の形式です。得点とfull-pass率（百分率）は、採点済みtrialのfixture内平均を求めてからfixture間で単純平均します。overallは各fixtureを1回だけ数えます。tokensとwallは対象trial全体の中央値です。fixture別の表も同じ行・列で、平均eligibleだけを表示します。未実行セルは空欄、得点や計測の欠測は`-`です。

`effort_applied`があればその値で列に分類し、なければ構成の要求effortを使います。要求と適用が異なるセルには`[high→max]`のように表示します。同じ適用effortに到達した要求値は同じセルに集約します。

`matrix.json`にも同じ集計を保存します。`efforts`は列順、`axes`と`fixtures`は表のlistで、それぞれ`name`と`rows`を持ちます。各行の`model`が行名、`cells`がeffortからセルへのmapです。未実行セルはnullです。セルは`score`、fixture平均の`full_pass`（0〜1）、`trials`・`scored`・`score_missing`、中央値の`total_tokens`・`wall_s`と欠測数の`tokens_missing`・`wall_missing`、変換一覧の`effort_mappings`を持ちます。

## 実行

```bash
python3 bench.py --config codex:model:medium --config pi:model:high:minimal --tasks inventory,ledger --repeat 2 --seed 3 --budget-s 900 --out /tmp/bench
python3 bench.py --self-check --tasks inventory,ledger,scheduler --out /tmp/bench-self-check
python3 bench.py --config pi:model:high --suite capability --out /tmp/bench-capability
python3 bench.py --config pi:model:high --suite efficiency --out /tmp/bench-efficiency
python3 bench.py --report-only /tmp/bench-low /tmp/bench-high --out /tmp/bench-matrix
```

`--config`は`harness:model:effort[:flag,flag]`形式で繰り返せます。harnessは`codex`・`pi`・`omp`・`opencode`・`dsh`、flagは`minimal`・`context`・`brief=ABS_PATH`・`dsh-patch=PATH`です。`context`は`minimal`と併用し、`--keep-context-files`を渡してpi/ompにAGENTS.md/CLAUDE.mdだけを自動読込させます。`brief=ABS_PATH`は絶対pathのfile内容、空行、`task.md`の順で依頼文を組み立てます。pathに`{task}`を含めるとfixture名へ置換され、fixtureごとのbriefを使えます。`{task}`なしのbriefは設定の解析時に存在を検証し、`{task}`ありは試行時に検証します。読めないbriefはその試行の`invocation_error`になります。flagは構成キーの一部なので、flagが異なる構成はmatrixの別行になります。例: `pi:openai-codex/gpt-6-astra:medium:minimal,brief=/abs/brief.md`。`--timeout`はagentの制限秒数（既定900）です。`--budget-s`は任意の正の有限秒数で、wall timeの集計判定に使います。この値自体はrunnerを停止させません。

`--report-only RESULTS_DIR...`は各directoryの`results.jsonl`を結合し、`--out`へ`summary.md`と`matrix.json`を再生成します。構成・fixture・軸は保存済み結果から取得し、モデル呼出し・reference採点・fixture読込みは行いません。effortやtimeoutが異なるrunをまとめられます。同じ入力directoryの重複指定は1回だけ読み、異なるdirectoryの全レコードは独立trialとして集計します。再集計時の予定trial数には取得済み件数を使います。入力の`results.jsonl`は書き換えません。`--config`は不要です。

`--tasks`省略時は`fixtures/*/fixture.json`を探索し、`--suite NAME`に一致するfixtureを名前順に選択します。suiteは`capability`（既定）・`efficiency`・`archived`・`conventions`です。`--tasks`を指定した場合はsuiteに関係なく列挙されたfixtureを実行します。`--seed N`はrepeatごとの構成順を決定的にshuffleし、同じrepeat内のfixtureには同じ構成順を使います。実行は直列です。`--self-check`はモデルを呼ばず、referenceと未変更baselineの得点表を表示して`self-check.md`へ保存します。

テスト用の`BENCH_RUNNER_OVERRIDE`はPython scriptのpathです。runnerの代わりに`python script prompt_path workspace_path`を呼び、stdout末尾のJSONをharness-run形式の結果として読みます。overrideでは`--timeout`を外側の実行時間制限にも使います。

```bash
uv run -q --no-project --with pytest python -m pytest -q .agents/skills/harness-run/bench/tests
```
