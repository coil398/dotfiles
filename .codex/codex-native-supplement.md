# Codex Native Runtime Supplement

This supplement is loaded only by Codex through the generated
`.codex/AGENTS.md`. Runtime-neutral guidance comes from
`.agents/global-instructions.md` and is delivered before this supplement.

## Task Execution And Autonomy

When `CODEX_DELEGATED_BY_RUNNER=1` is present in the environment, the runner
owns the outer coordination and this Codex process is its assigned implementer.
Complete the assigned task directly without applying root-agent delegation
rules or starting child agents. This also applies to read-only consultation.
A Codex child likewise performs its assigned work directly. Native delegated Codex
processes may start only the read-only `explorer` agent for useful fact-finding; an
`explorer` does not start other agents. Runner-launched Codex processes have
multi-agent tools disabled. Delegated children do not commit, push, or discard
existing changes.

## Conditional References

These documents are generated next to this file under `~/.codex/`:

- After a concrete user correction reveals a reusable rule, read
  `~/.codex/user-feedback-protocol.md` and record it in the right source.
- When starting or operating an HMR dev server, read `~/.codex/dev-server.md`.

## Codex Commander and Planning

The main/root agent (the session the user talks to directly) owns planning
and acceptance under the shared subagent operation rules
(`~/.agents/skills/pir2/references/subagent-operation.md`). Model and reasoning
defaults come from `.codex/config.base.toml`; use the effective runtime
settings. The main/root agent delegates implementation and fixes to a writing
child instead of editing directly, and gives tightly coupled changes to one
child. A delegated Codex (runner-launched or a child) does not apply this
paragraph: it does the work itself.

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

Use the custom `explorer` agent for read-only exploration.
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

Do not start more child work than the configured concurrency ceiling or the
runtime can currently support.

Give each unit an objective, exclusive file ownership, constraints,
interfaces, acceptance criteria, the delegated role, and physical Skill/reference
paths. State that the recipient performs the assigned work directly and starts
no agent other than a read-only `explorer`.
Check the effective definition and observed execution separately. A saved
configuration or the child's own claim does not prove the model that ran.

## Concrete Work Delegation

Use native collaboration for scoped work, following the shared subagent
operation rules (`~/.agents/skills/pir2/references/subagent-operation.md`): give each child its objective, confirmed facts, exclusive
ownership, constraints, exit criteria, focused checks, forbidden scope and
return items. For exploration-only work, state that nothing may be edited and
pass the physical path of the shared `research/references/explorer.md`.
Treat returns as self-reports; accept from `git status`, the target diff and
check output. Deterministic transformations, builds, and test launches belong
in scripts.

Distinguish missing inputs, permissions and simple mistakes from unresolved
reasoning. Resolve the former at their source; reassign the latter when
another reasoning approach is needed. Accept work from actual diffs and
relevant check results.

## OpenAI Specifications

Consult the available official `openai-docs` skill for OpenAI
model/API specifications; if unavailable, use official documentation directly.
Codex configuration work does not expand into application API migration.
