# 指示監査チェックリスト

依頼された範囲と実害に関係する観点を使う。全面監査では対象全件を確認する。

## 形式とサイズ

- Skillのfrontmatterが先頭から始まり、nameとdirectory、description、Claude Code拡張fieldが正しいか。
- `wc -l` とdescription文字数を測る。500行はSkill本文の推奨で、load不能の境界ではない。
- 同種ファイル中央値の3倍以上は読解優先度の目安にとどめ、欠陥と断定しない。
- 相対参照がSkillの実体から解決でき、必要なasset・script・referenceが存在するか。
- symlink、submodule、managed copy、生成物を実体ownerと区別する。

## 責務・SSOT・重複

- 評価だけのagentが実装や外部操作まで担当していないか。
- 常時指示、親workflow、専門手順、agent出力契約のownerが混ざっていないか。
- 原本の複写を削る前に、消費側が必要時に原本を読む経路があるか。
- 対象群を横断し、連続した字句一致だけでなく、同じ意味の規則・template・停止条件も確認する。
- 同じruntimeで必要な配達用複写と、古くなる二重管理を区別する。

## 発火条件

descriptionを本文と近接Skillへ照合する。

- 何をするかと、いつ使うかが短く判別できるか。
- database、review、UIなど広い関連語だけで専門Skillを起動しないか。
- trigger語の長い列挙、本文手順、tool一覧、marketing説明を詰め込んでいないか。
- explicit-only、auto activation、近接Skillとの境界が実際の意図と一致するか。
- Claude Codeの `disable-model-invocation`、`user-invocable`、`context: fork` を文章上の自己申告で代用していないか。

## load・工程・終了

- 常時loadされるCLAUDE.mdやimportに、特定workflowだけの手順がないか。
- 複数modeの全referenceを無条件に読ませていないか。
- 小さな依頼にも固定Agent数、固定round、全repo読込、全testを要求していないか。
- 既に許可された工程を再承認させる、最初の実装で止める、必要な修正を未完了で返す指示がないか。
- correctness、security、data loss、明示的な独立性を守る工程は、単なる過剰手順と区別する。
- 説明・監査だけの依頼を実装へ広げていないか。

## Claude固有の保持事項

- Agent / Agent Teamsの実際の起動方式、nested Agentの可否、foreground/backgroundが現行仕様と一致するか。
- model指定、Fable、single/panel、独立reviewを別modelや通常委譲へ機械的に置換していないか。
- `<!-- CORE -->` 領域を明示承認なしに変更していないか。
- subagentへ渡す入力、専有file、結果契約、証跡が外出しで欠落しないか。

## user scopeの汎用性

1. 特定projectの絶対path、会社・service・class・table・endpoint・固有commandを候補抽出する。
2. 利用範囲・履歴・ownerと照合し、公開技術名や仮名を区別する。
3. 確認できない候補は未確認とする。
4. 修正後に再検索し、残る候補の用途を説明する。
