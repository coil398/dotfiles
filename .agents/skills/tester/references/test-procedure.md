# Test procedure

この手順は、親から渡された対象・受入条件・`TEST_SCOPE`に対して、実測可能な検証を組み立てるためのもの。テスト実行者は結果を親へ返し、親が明示的に許可したlocal/ephemeralのtest outputとlocal fixtureだけを生成・変更できる。対象実装・既存データ・既存fixture・report・記憶は変更しない。

## 判定

- `COVERAGE: complete` は、受入条件と必要な実動作確認を終えた状態。
- `COVERAGE: partial` は一部確認済みだが、必須範囲に未確認が残る状態。
- `COVERAGE: none` は対象の確認を実施できていない状態。
- `VERDICT: FAIL` は実行した検証の失敗または期待外の挙動がある場合。
- `VERDICT: INCOMPLETE` は失敗を確認していなくても、必須検証が未実施で合格と判断できない場合。
- `VERDICT: PASS` は要求された検証が通り、必要な動作確認が完了した場合。
- 対象がないため実行しない場合だけ`NOT_APPLICABLE`を使い、取得失敗や未導入をこの値にしない。

## フェーズ1: 既存テスト

1. `TEST_SCOPE`が渡された場合は列挙されたコマンドを基本とし、根拠なく省略・置換・full suite追加をしない。
2. `TEST_SCOPE`がなければ`package.json`、`Makefile`、`pyproject.toml`、`go.mod`等を読み、プロジェクト標準のテストコマンドを実測して選ぶ。Pythonでは既存の`pyproject.toml`/`uv.lock`があればuvを優先する。
3. テスト失敗は即座にFAILとして返し、コマンド・終了結果・関連ログを示す。
4. 成功後も、差分からcorrectness、security、data loss、runtime、データ整合性、回帰に追加検証が必要と分かった場合は、具体的な追加コマンドと未検証範囲を親へ返す。隣接packageやfull suiteを波及根拠なしに要求しない。

## フェーズ1.5: IaCの静的検証

変更ファイルにbicep、Terraform、CloudFormation/k8s YAML、Dockerfile等がある場合だけ、対応する静的検証を選ぶ。IaCのapply/deployは行わない。

- bicep: `az bicep build --file ...`
- Terraform: 対象ディレクトリでbackendを使わない`terraform init -backend=false`と`terraform validate`
- CloudFormation: `cfn-lint`
- k8s manifest: `kubectl --dry-run=client`または`kubeval`
- Dockerfile: `hadolint`、または重さを確認したうえでbuild

ツールが未導入なら`command -v`の結果、skip理由、CI等で必要な確認を未確認欄に残す。新規ファイルのentrypoint、param、module、output、unused paramも変更ファイルと周辺実装から照合する。未導入だけでFAILにせず、受入に必須な検証が残る場合はINCOMPLETEにする。

## フェーズ2: アドホック動作確認

静的・構文・設定確認で要件を測れないruntime変更だけ、許可された環境で実装を動かす。

- APIは起動して実際のリクエストとレスポンスを確認する。
- CLIは実コマンドの出力・終了コードを確認する。
- ライブラリは最小の呼び出しで正常・異常・境界を確認する。
- UIやEditorは、許可された実行記録・画像・操作結果を証拠にする。

テストデータ、local fixture、test outputの生成・追加・変更は、明示的に許可されたlocal/ephemeral環境と所有範囲に限る。権限・保持方針が不明なら投入・生成せず、必要な入力と未確認範囲を返す。secret、個人情報、機密データは要約・マスクする。テストデータやfixtureのクリーンアップは自己判断で実行しない。

配列を返すAPIは1件だけの応答で成功とせず、複数要素・空・境界を意味のあるassertionで確認する。推測できる範囲は先に安全に試してから質問する。DB削除などの破壊的操作は、明示承認と許可された環境がなければ実行しない。大量ログは要約する。

## フェーズ3: 実行不能時の静的代替

テストランナーやパッケージマネージャがPATHにない場合、再インストールを前提にせず、可能な範囲で以下を実施する。

1. 言語標準のparser/ASTで変更した実装・テストを構文確認する。
2. 新シンボル・フィールド・引数・error typeと旧APIの痕跡を変更領域で照合する。
3. parametrize、Cartesian product、if/match/dispatchの入力と期待値を机上追跡する。
4. mock/spyのID、メッセージ、引数tupleを実装側の生成値と照合する。
5. 親がbase/headを指定した場合だけ`git diff <base>..<head> --stat`等でscopeを照合する。未指定のbaseを推測しない。

静的代替で検出できないruntime例外、I/O副作用、並行性、データ整合性は未確認として返す。静的検証だけで受入条件を測れる場合は、その根拠を明記してPASSにできる。

## 差分境界と累積ログ

`git status`/`git diff`には本タスク、先行差分、副次的変更が混在し得る。親が渡した`TASK_SCOPE_FILES`、ownership、diff baselineを一次境界とし、一覧外を直ちにFAILの根拠にしない。実装者が誤って変更したと特定できる場合だけscope侵食として扱う。callerが渡したplan/reportは絶対pathと実在を確認し、未指定の補助資料やmemory pathを推測しない。

Editor.logやCI等の累積ログは、末尾の古いエラーを最新状態とみなさない。最新のcompile/buildサイクル開始マーカー以降だけを確認し、変更ファイルの現在内容と照合する。過去サイクルのエラーだけでFAILにしない。

## 返却

```text
COVERAGE: complete | partial | none
VERDICT: PASS | FAIL | INCOMPLETE | NOT_APPLICABLE

対象: repo・版・差分・受入条件
確認範囲:
- 実行したコマンドと結果
- 動作確認した入力・期待値・実際の値

未確認:
- 範囲、理由、必要な入力または操作

副作用:
- テストデータ投入・外部状態変更・保存の有無
```

レポート保存は親が行う。テスト実行者は`REPORT_PATH`が渡されてもそこへ書き込まず、実行結果を親へ返す。`PROJECT_MEMORY_DIR`や保存先を推測しない。親は未実行の確認や未起動担当を成功として補完しない。
