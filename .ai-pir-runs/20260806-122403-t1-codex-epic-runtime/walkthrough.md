# ウォークスルー

1. Phase 0 が repository-local run と Sol 単一 writer の観測テーブルを初期化する。
2. Phase 1 で epic-planner を助言者として使い、Sol が探索根拠と DAG を最終判定する。
3. Phase 1.5 で必ずユーザー承認を得る。
4. Phase 2 は完了要件と所有範囲を共通 worker-routing へ渡し、Sol が実測する。品質レビューとテストは worker から分離する。
5. Phase 3〜4 で統合点と全 Ti の acceptance / quality を照合し、Sol が最終 VERDICT を出す。
