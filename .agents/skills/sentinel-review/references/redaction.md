# Sentinel redaction and safety

Findingの証拠は、再現に必要な最小範囲だけを返す。攻撃手順、PoC、exploitコード、未承認の外部アクセス、実データの無加工出力を行わない。

## マスクするもの

- API key、password、private key、token、cookie、署名、credential、個人情報。
- 環境変数・secret manager・CI secretの値と、長いランダム文字列。
- URLの認証情報、query token、署名付きURL、内部ホスト名や識別子で不要なもの。
- `evidence.snippet`、`rationale`、`remediation`、ログ要約に偶然含まれる秘匿値。

値そのものが検出対象なら、種別と存在を説明し、`<REDACTED>`へ置換する。短い固定値でも認証・個人情報として使われ得る場合は露出させない。snippetは数行に制限し、周辺の安全な構文だけを残す。

## 権限と副作用

- `sentinel-review`と`sentinel-iac`はread-onlyで、修正は`suggested_patch`の提示で止める。
- `apply`、`deploy`、`terraform init`（backendを含む実行）、Docker buildによる外部push、GitHub workflow実行は検査のために行わない。必要な確認条件を親へ返す。
- 外部ネットワーク呼び出し（curl、wget、git fetch等）や本番・外部状態への操作を行わない。
- パース失敗や資料不足はFinding 0件と同一視しない。親の結果で未確認・失敗として記録する。

## 親の集約

親はschema不適合件数、agentの失敗・skip、未確認範囲をサマリへ残す。`confidence=low`と`severity=info`は折りたたんで表示できるが、存在を削除しない。スキーマ準拠は内容の正しさを保証しないため、根拠・成立条件・影響を親が照合する。
