---
name: codex
description: Codex runtimeで、明示された問いへのread-onlyな第二意見を返す。`/codex`またはCodexへの相談依頼に使い、調査や実装には使わない。
argument-hint: "[bounded consultation]"
---

# /codex — consultation router

`/codex <相談内容>` に対し、標準子を一体だけread-only相談担当として起動する。親が問い、範囲、入力、結果の照合を所有し、相談結果を受入判断として扱わない。

## 経路

- 証拠収集や仮説形成が主目的なら `/research` を使う。
- コードやリポジトリの変更が必要なら `worker-delegation` を使う。
- 同じ相談の未解決点は、新しい担当を起動せず `followup_task` で同じ担当へ返す。
- 複数の独立した確認が必要な広い問いは、親が分割と統合を持ち、このSkillの単一相談経路へ押し込まない。

## 起動契約

Codex Native Runtime Supplement と実効設定に従って `spawn_agent` を呼び、すべての新規相談で `fork_turns="none"` を指定する。親は自己完結したpromptへ次を含める。

- 対象repo、版、具体的なファイルまたはbounded scope
- 一つの主な問いと必要な入力
- 読み取りだけを行い、編集・作成・削除・stage・commit・push・破壊的git操作をしないこと
- `ANSWER`、`EVIDENCE`、`RISKS`、`NEXT_CHECKS` を返し、不足は `BLOCKED` とすること

このread-only境界はprompt上の契約であり、filesystemの能力分離ではない。親は返却されたpath、主張、コマンドを実際の対象と照合する。難しい独立推論で別の公開model・effortを選ぶ場合も、選択と起動値はCodex Native Runtime Supplementに従い、固定モデルをこのSkillへ複製しない。

このSkill自身は実装、patch、具体的な変更の委譲、相談結果だけによるPASS判定を行わない。
