# 指示の整理戦略

必要な情報の配達を保ち、原因に対応する最小の変更を選ぶ。

## 配達経路ゲート

外出し・削除・統合の前に確認する。

1. 同一ファイル内の重複なら、追加referenceを作らず固有情報の和集合を1箇所へ統合する。
2. 原本の複写なら、原本の内容と、消費側が必要時に読む手順を確認する。唯一の配達経路なら残す。
3. subagentが実行するcommand、出力contract、必須checkを外出しする場合は、そのagent自身がreferenceを読む明示経路を残す。
4. 常時必要なのが案内だけなら、適用条件と原本へのpointerを残す。
5. safety、権限、data loss、明示的なmodel・独立性に関わる順序は削らない。

## 選択

| 原因 | 修正 |
|---|---|
| 不要な複写・責務越境 | 削除またはowner参照へ置換 |
| 複数mode・長い条件別手順 | 必要時に読むreferenceへ分ける |
| Claude Codeが対応する常時指示 | 必要な場合だけ `@path` import |
| unused entry・broken reference | caller確認後に削除または修復 |
| 同一ファイルの意味的重複 | 固有情報を保って統合 |
| 長い・競合するdescription | 能力と適用条件へ短縮 |
| user scopeのproject前提 | project側へ移すか一般化 |

## Progressive Disclosure

`SKILL.md` には目的、適用条件、必須制約、mode routingを置く。大きなschema、provider別手順、詳細例は `references/`、決定論的な反復処理は `scripts/`、成果物素材は `assets/` を使う。

referenceへのlinkには「いつ読むか」を添える。全referenceの一括load、entrypointとの二重掲載、単用途の短いSkillへの不要な階層追加を避ける。

Claude Codeではinvoked Skill本文が後続turnにも残り、compaction後は各Skill先頭5,000 tokens・合計25,000 tokensの範囲で再添付される。重要なroutingとconstraintをentrypoint前半に置く。

## description

最初に主要用途を置き、何をするかと適用条件を1〜2文で示す。長いtrigger一覧、workflow手順、tool、model、output formatは本文へ置く。近接する依頼が別Skillなら境界を1文だけ加える。

explicit-onlyの意図は文章だけでなく `disable-model-invocation: true` で表す。side effectがあるという理由だけで自動的にexplicit-onlyへ変えず、既存の自然言語起動方針を確認する。

## 固定工程と承認

固定Agent数、round数、全文読込、全testは、それがpreventする具体的な失敗がある場合だけ残す。独立review、Fable panel、writer所有分離など明示された方式は保持する。

承認済みscope内の可逆な実装・検証を途中で止めない。確認は、仕様を変える未解決選択、外部mutation、破壊的操作、実アクセス制御など本当に必要な地点へ限定する。確認が必要でも、依存しない準備は先に完了する。

## 統合の確認

意味的重複を統合するときは、編集前に各箇所の固有情報を「誰が・何を・どの条件で」の単位で列挙する。編集後に全情報点が含まれることを照合し、削除した用語やfieldの残存を検索する。

複雑な配達変更は代表的なrequestまたは独立reviewで確認する。変更が小さく、metadata・link・load経路の確認で十分なら固定workflowを追加しない。
