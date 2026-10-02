---
name: "pipeline-diagnose"
description: >-
  ステージ型パイプラインの run が「止まる」「同じところを回り続ける」「収束しない」
  ときに、durable な成果物とイベント列から原因を特定する診断手順の正本。
  BLOCKED / no_matching_case / 無限リトライ / 全部再生成 / sentinel 固定化のような
  症状を、推測ではなく実測で機構まで掘り下げる。パイプラインの構築・運用方針は
  /pipeline を参照。ユーザーが /pipeline-diagnose と入力したら使う。
---

<!-- Cursor thin entry; the shared skill remains the source of truth. -->
SHARED_SKILL_PATH=../../../.agents/skills/pipeline-diagnose/SKILL.md

Read the shared skill at `SHARED_SKILL_PATH` relative to this entry file, then follow its instructions.
If relative resolution is unavailable, read the checked-out source at `/home/coil398/dotfiles/.agents/skills/pipeline-diagnose/SKILL.md`.
The shared skill's references/, scripts/, and other assets remain at that source path and are not copied here.
