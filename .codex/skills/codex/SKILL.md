---
name: codex
description: Codex runtimeで read-only の bounded second opinion を返す相談ルーター。ユーザーが「codexに聞いて」「codexに相談」「second opinion from codex」と依頼したとき、または `/codex` と入力したときに使う。調査は `/research`、具体的な変更は `worker-delegation` に回し、実装しない。
argument-hint: "[bounded consultation]"
---

# /codex — consultation router

`/codex <相談内容>` is a compatibility layer for obtaining a bounded,
read-only second opinion in the Codex runtime. It returns evidence and advice
for the caller to verify; it does not edit the target repository.

## Route by intent

- **Bounded second opinion**: call `spawn_agent` directly with one consultant
  and a read-only consultation prompt. Use the normal Codex child defaults from
  [Codex Native Runtime Supplement](../../codex-native-supplement.md); when the
  question requires difficult independent reasoning, the parent may select a
  different published model and effort at spawn time. Every new consultation
  uses `fork_turns="none"`; do not attach full or partial parent history. Do not use a custom role merely to encode a
  model. The prompt must name `PROJECT_ROOT`, the exact files or bounded scope,
  one primary question, and the required response format. It must say to inspect
  only and not edit, create, delete, stage, commit, push, or perform destructive
  git operations.
- **Continuation of the same consultation**: when the first response leaves a
  bounded question unresolved, call `followup_task` for the same consultant.
  Pass the prior conclusion, the remaining question, and the same read-only
  constraints. Do not start a second consultant merely to repeat the same
  question.
- **Broad or deep multi-perspective deliberation**: keep the question with the
  parent and split only concrete independent checks among standard Codex
  children when that improves evidence.
- **Evidence collection or hypothesis formation**: route to the existing
  `/research` skill.
- **Concrete implementation or repository change**: route to
  `worker-delegation`. This skill never implements, fixes, or delegates a
  concrete repository change through consultation.

## Lightweight consultation contract

Use the collaboration API directly. A representative bounded request is:

Choose a fresh unique suffix for `task_name` for every consultation. Use the
`codex_consultation_<unique_id>` naming pattern, replacing `<unique_id>` with
lowercase letters, digits, and underscores only. Always set
`fork_turns="none"`, including when model and reasoning effort are omitted.
The parent supplies the complete bounded task context and necessary evidence
paths; missing information is supplemented explicitly, not by a history fork.

```text
spawn_agent(
  # Replace 20260806_001 with a fresh lowercase/digit/underscore-only suffix.
  task_name="codex_consultation_20260806_001",
  fork_turns="none",
  # model and reasoning_effort are selected by the parent from the Codex supplement.
  message="""
    PROJECT_ROOT: /absolute/path/to/project
    SCOPE: the exact files or one review question
    QUESTION: one bounded question

    READ_ONLY_CONSULTATION: inspect the stated scope only. Do not modify,
    create, delete, stage, commit, push, or perform destructive git actions.
    Return a short structured response with ANSWER, EVIDENCE, RISKS, and
    NEXT_CHECKS. Mark missing information as BLOCKED instead of guessing.
  """
)
```

`READ_ONLY_CONSULTATION` is a policy/prompt-based boundary, not capability isolation:
it asks the consultant not to write, but it does not enforce filesystem sandbox permissions.
The caller must verify any path, claim, or command in the response against the actual
repository. A consultation response is never an acceptance decision. This direct
consultation route has no automatic fallback or effort escalation; any measured
escalation follows the model-selection rules in the Codex supplement and the
execution boundaries in `worker-delegation`.

For a follow-up, retain the consultant identity and use the same bounded
contract:

```text
followup_task(
  # Use the task name (or canonical task name) returned by the spawn call.
  target="codex_consultation_20260806_001",
  message="""
    Continue the read-only consultation for the unresolved question: ...
    Re-check only the stated scope; do not modify repository files.
  """
)
```

If the question becomes broad or multi-perspective, keep the final framing and
integration with the parent, using standard children only for concrete
independent checks. Evidence-seeking and implementation-oriented requests go
to `/research` or `worker-delegation` according to the route table above.

## Hard boundary

This skill is consultation-only. It must not implement a plan, apply a patch,
run a concrete change on the caller's behalf, or claim PASS from a consultant's
self-report. Concrete changes belong to `worker-delegation`; the caller owns
the final diff and verification.
