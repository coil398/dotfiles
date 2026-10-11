# Codex Native Runtime Supplement

This supplement is loaded only by Codex through the generated
`.codex/AGENTS.md`. Runtime-neutral guidance comes from
`.agents/global-instructions.md` and is delivered before this supplement.

## Task Execution And Autonomy

Use the shared `依頼・範囲・承認` rules for completion, approval,
scope and verification. They apply to Codex work as well as other runtimes.

## Conditional References

These documents are generated next to this file under `~/.codex/`:

- After a concrete user correction reveals a reusable rule, read
  `~/.codex/user-feedback-protocol.md` and record it in the right source.
- When starting or operating an HMR dev server, read `~/.codex/dev-server.md`.

## Codex Commander and Planning

The main/root agent owns planning and acceptance under the shared
subagent operation rules (`~/.agents/skills/pir2/references/subagent-operation.md`). Model and reasoning defaults come from
`.codex/config.base.toml`; use the effective runtime settings. Delegate
implementation and fixes to a writing child instead of editing directly; give
tightly coupled changes to one child.

## Codex Subagent Default

Use the built-in `default`, `worker`, or `explorer` according to the task.
General evaluation can use `default`; it need not be forced into an explorer.
Give the child the physical path of the relevant execution Skill/reference
and the current task. Expertise belongs in those shared sources, not in a
custom role for each profession or model.

Routine child model and effort are configured once in `.codex/config.base.toml`
under `[agents]`: `default_subagent_model` and
`default_subagent_reasoning_effort`. Do not repeat those defaults in ordinary
Agent definitions or specialist Skills.

For difficult independent work, the parent may explicitly choose
`model="gpt-6.1-sol"` with `reasoning_effort="medium"`. Reserve
`gpt-6.1-sol` / `max` for an explicit high-risk or unusually difficult
exception. Routine specialist work uses the configured Luna / `max` default.
Use a script for deterministic handoff, command launch, and result collection;
if those tasks need an agent, choose Luna / `low`. A difficult task may use Sol
from the start; do not require a failed Luna attempt first.
Missing inputs, permissions and environment failures are not reasons to
change models without fixing those causes.

Use the actual published spawn interface. Every new V2 child must receive
`fork_turns="none"` explicitly, regardless of model or effort. Parent-history
forks, including partial history, are not part of this workflow. The parent
owns a self-contained message: objective, target and version, necessary
background, established facts versus hypotheses and unknowns, exclusive
ownership, constraints, acceptance criteria, and physical Skill/reference
paths. Children read the relevant expertise from its source. Resolve missing
inputs by supplying the specific facts or source paths, not by copying the
parent conversation. Independent reviewers receive requirements and target
evidence, not the writer's conversation. Continuing the same child's own task
with `followup_task` is separate from giving a new child parent history.

This is the required invocation policy, not a configuration-enforced ban.
The published V2 interface defaults omitted `fork_turns` to `all`; do not
claim a configuration-enforced ban without a supported runtime setting. Do not add unsupported fork keys, replace this with
`usage_hint_text` and claim enforcement, or install an argument-rewriting
hook. Report that enforcement requirement as unsupported when applicable.
History selection does not select the model: apply the configured defaults
and exposed model/effort arguments independently. A custom definition's fixed
model/effort can override spawn values. Keep a short preset only for an actual
missing runtime capability or required fixed execution condition; do not
silently substitute another model if selection fails.

The configured `max_concurrent_threads_per_session` is an initial ceiling for
child work, not a universal or mandatory worker count. Before each wave,
inspect the active Codex configuration and live collaboration state, then use
the lower of the configured ceiling and currently available capacity. A
completed child does not by itself prove that a slot has been released; reuse
an actually available thread with `followup_task` when the API exposes it.
Never invent a close/release API or spawn beyond observed capacity.

Give each unit an objective, exclusive file ownership, constraints,
interfaces, and acceptance criteria. Only delegate further when the parent
authorizes it.
Check the effective definition and observed execution separately. A saved
configuration or the child's own claim does not prove the model that ran.

## Concrete Work Delegation

Use native collaboration for scoped work, following the shared subagent
operation rules (`~/.agents/skills/pir2/references/subagent-operation.md`): give each child its objective, confirmed facts, exclusive
ownership, constraints, exit criteria, focused checks, forbidden scope and
return items. For exploration-only work, state that nothing may be edited and
pass the physical path of the shared `research/references/explorer.md`.
Children do not spawn other agents, commit, push or discard existing changes.
Treat returns as self-reports; accept from `git status`, the target diff and
check output. Deterministic transformations, builds, and test launches belong
in scripts.

Distinguish missing inputs, permissions and simple mistakes from unresolved
reasoning. Resolve the former at their source; reassign the latter when
another reasoning approach is needed. Accept work from actual diffs and
relevant check results.

## Retrospectives

Run a retrospective when the user requests one or the active workflow explicitly requires it. Do not append an unsolicited retrospective suggestion to an ordinary final answer.

Consult the available official `openai-docs` skill for OpenAI
model/API specifications; if unavailable, use official documentation directly.
Codex configuration work does not expand into application API migration.
API features are not Codex configuration keys, and Responses API Multi-agent
does not provide this runtime's cross-model role routing.
