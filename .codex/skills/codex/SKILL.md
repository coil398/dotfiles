---
name: codex
description: Codex runtimeで read-only の bounded second opinion を返す相談ルーター。ユーザーが「codexに聞いて」「codexに相談」「second opinion from codex」と依頼したとき、または `/codex` と入力したときに使う。広い熟考は `/deepthink`、調査は `/research`、具体的な変更は `worker-delegation` に回し、実装しない。
argument-hint: "[bounded consultation]"
---

# /codex — consultation router

`/codex <相談内容>` is a compatibility layer for obtaining a bounded,
read-only second opinion in the Codex runtime. It returns evidence and advice
for the caller to verify; it does not edit the target repository.

## Route by intent

- **Bounded second opinion**: call `spawn_agent` directly with one consultant,
  an explicit `model = "gpt-5.6-luna"`, an explicit
  `reasoning_effort = "max"`, and a read-only consultation prompt. All Codex
  consultations start at Luna Max, regardless of the question's apparent
  size. The prompt
  must name `PROJECT_ROOT`, the exact files or bounded scope, one primary
  question, and the required response format. It must say to inspect only and
  not edit, create, delete, stage, commit, push, or perform destructive git
  operations.
- **Continuation of the same consultation**: when the first response leaves a
  bounded question unresolved, call `followup_task` for the same consultant.
  Pass the prior conclusion, the remaining question, and the same read-only
  constraints. Do not start a second consultant merely to repeat the same
  question.
- **Broad or deep multi-perspective deliberation**: route to the existing
  `/deepthink` skill.
- **Evidence collection or hypothesis formation**: route to the existing
  `/research` skill.
- **Concrete implementation or repository change**: route to
  `worker-delegation`. This skill never implements, fixes, or delegates a
  concrete repository change through consultation.

## Lightweight consultation contract

Use the collaboration API directly. A representative bounded request is:

Choose a fresh unique suffix for `task_name` for every consultation. Use the
`codex_consultation_<unique_id>` naming pattern, replacing `<unique_id>` with
lowercase letters, digits, and underscores only. Set `fork_turns="none"`
explicitly when passing the model or reasoning effort.

```text
spawn_agent(
  # Replace 20260806_001 with a fresh lowercase/digit/underscore-only suffix.
  task_name="codex_consultation_20260806_001",
  fork_turns="none",
  model="gpt-5.6-luna",
  reasoning_effort="max",
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
consultation route has no automatic Terra/Sol fallback or effort escalation; any
measured escalation follows the actor ladder in `worker-delegation`.

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

If the question becomes broad, multi-perspective, evidence-seeking, or
implementation-oriented, stop this route and hand it to `/deepthink`,
`/research`, or `worker-delegation` according to the route table above.

## Hard boundary

This skill is consultation-only. It must not implement a plan, apply a patch,
run a concrete change on the caller's behalf, or claim PASS from a consultant's
self-report. Concrete changes belong to `worker-delegation`; the caller owns
the final diff and verification.
