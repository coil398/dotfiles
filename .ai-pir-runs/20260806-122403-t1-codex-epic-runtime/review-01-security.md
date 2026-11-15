VERDICT: PASS

# security

- 破壊的 git 操作、無断 commit、既存変更の破棄を禁止している。
- 所有範囲と禁止範囲を worker-routing の必須入力としている。
- 権限不足と破壊的操作を worker に独断させず、Sol の制御に戻す。

Critical / High の問題なし。
