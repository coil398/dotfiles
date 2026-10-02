---
name: "pipeline-improve"
description: >-
  稼働中パイプラインの改善ループ。durable 実測で失敗型を確定し、deepthink(Fable)・
  swe-2 等の独立モデル腕に仮説を競わせ、lab A/B で収束形状を比較してから本番へ
  port する。「パイプラインを改善して」「収束しないループを直して」「A/Bで
  改善を測って」「lab で試してから本番に」「改善して安定化」といった依頼で使う。
  ユーザーが /pipeline-improve と入力したら使う。
---

<!-- Cursor thin entry; the shared skill remains the source of truth. -->
SHARED_SKILL_PATH=../../../.agents/skills/pipeline-improve/SKILL.md

Read the shared skill at `SHARED_SKILL_PATH` relative to this entry file, then follow its instructions.
If relative resolution is unavailable, read the checked-out source at `/home/coil398/dotfiles/.agents/skills/pipeline-improve/SKILL.md`.
The shared skill's references/, scripts/, and other assets remain at that source path and are not copied here.
