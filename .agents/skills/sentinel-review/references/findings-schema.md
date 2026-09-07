# Sentinel Finding schema

`sentinel-iac`は、担当するIaCの危険設定を検出した結果を、返答末尾のJSONブロック1個で返す。`sentinel-review`親がこのschemaに照合して正規化・重複排除・表示する。評価者はファイルを編集せず、IaC以外のカテゴリをFindingにしない。

## 対象と検出器

対象はDockerfile、docker-compose/Compose YAML、Terraform、`.github/workflows/*.yml|yaml`である。1ファイル512KBを超える場合は関連箇所だけを読む。

| 対象 | 検出 | severity | detector_id |
|---|---|---|---|
| Dockerfile | `USER root`、または`USER`なし | high | `iac.dockerfile.root_user` |
| Dockerfile | `FROM image:latest`またはタグなし | medium | `iac.dockerfile.latest_tag` |
| Dockerfile | URLを指定した`ADD` | medium | `iac.dockerfile.remote_add` |
| Compose | `privileged: true` | high | `iac.compose.privileged` |
| Compose | `/`、`/etc`、`/var/run/docker.sock`等のhost mount | high | `iac.compose.host_mount` |
| Compose | `network_mode: host` | medium | `iac.compose.host_network` |
| Terraform | S3 ACLの`public-read`/`public-read-write` | high | `iac.terraform.s3_public` |
| Terraform | IAMの`Action="*"`と`Resource="*"`の組み合わせ | high | `iac.terraform.iam_wildcard` |
| Terraform | 管理port（22/3389/5432/3306）への`0.0.0.0/0` | high | `iac.terraform.sg_world_admin_port` |
| GitHub Actions | `pull_request_target`、checkout、head SHA checkoutの危険な組合せ | critical | `ci.gh_actions.prt_checkout_fork` |
| GitHub Actions | 第三者actionのbranch/tag pin（`actions/*`/`github/*`を除く） | medium | `ci.gh_actions.unpinned_third_party` |

## JSON契約

検出ゼロでも`findings`と`skipped`を持つJSONを返す。未知の値や必須フィールドの欠落は親が不適合件数として記録し、黙って成功扱いにしない。

```json
{
  "findings": [
    {
      "id": "iac.dockerfile.root_user::Dockerfile::1",
      "detector_id": "iac.dockerfile.root_user",
      "category": "iac",
      "title": "Dockerfile が root ユーザで実行されている",
      "severity": "high",
      "priority": "soon",
      "confidence": "high",
      "rationale": "USER ディレクティブが無いコンテナは root として実行される。",
      "evidence": [
        {
          "path": "Dockerfile",
          "start_line": 1,
          "end_line": 15,
          "snippet": "FROM python:3.11\n..."
        }
      ],
      "impact": {
        "scope": "コンテナ内全プロセス",
        "data_at_risk": ["internal_only"],
        "exploitability": "コンテナ脱出と組み合わせると影響大"
      },
      "remediation": {
        "summary": "非 root ユーザを作成して USER で切り替える。",
        "steps": ["RUN useradd -r -u 1001 appuser を追加", "Dockerfile 末尾に USER appuser を追加"],
        "suggested_patch": null,
        "alternatives": []
      },
      "recurrence_checklist": ["新規 Dockerfile レビュー時に USER ディレクティブの有無を確認"],
      "references": [],
      "source": {"agent": "sentinel-iac", "method": "deterministic"}
    }
  ],
  "skipped": []
}
```

必須Finding項目は`id`、`detector_id`、`category`、`title`、`severity`、`priority`、`confidence`、`rationale`、`evidence`、`impact`、`remediation`、`source`である。`evidence`には相対`path`、正の`start_line`/`end_line`、最小限の`snippet`を置く。`remediation.suggested_patch`は任意だが、実際に適用する操作ではなく提案である。

`category`はIaCを使用する。secret、code、depsは別担当であり、見つけてもFindingや`skipped`へ入れない。親は重複を`detector_id + path + start_line`で統合し、severity降順、priority降順で表示する。`severity-min`未満は出力から除外しても、除外件数をサマリへ残す。
