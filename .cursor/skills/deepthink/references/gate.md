# Deepthink gate — 十分性確認の契約

親が渡した rubric、context、positionを一項目ずつ照合します。positionを書き換えたり新規調査したりせず、根拠の有無、論理の穴、未対応の反論、過大主張、未確認範囲を判定します。

最初の行は `VERDICT: PASS`、`VERDICT: FAIL`、または `INCOMPLETE` とします。PASSは全rubricが根拠つきで充足し、重大な欠陥がない場合だけです。FAILでは不足を `needs-thinking`（推論不足）または `needs-exploration`（資料不足）に分類し、次に確認する具体的な問いを返します。途中終了、資料未取得、権限不足、Skill未読は、コードや結論の欠陥と区別して `INCOMPLETE` と報告します。

```markdown
VERDICT: PASS | FAIL | INCOMPLETE
## ゲート判定
### rubric 照合
| # | 基準 | 充足 / 部分 / 未達 | position の根拠 |
|---|---|---|---|
### 批判的点検
- 論理の穴:
- 未対応の反論:
- 過大主張:
### FAIL の不足と次の確認
| 不足 | 分類 | 次の問い |
|---|---|---|
```
