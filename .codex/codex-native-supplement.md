# Codex Native Runtime Supplement

This supplement is loaded only by Codex through the generated
`.codex/AGENTS.md`. Runtime-neutral guidance remains in the repository-root
`AGENTS.md`.

## Codex Commander and Planning

The main/root Sol is the Codex commander and defaults to
`model = "gpt-5.6-sol"` with `model_reasoning_effort = "high"`. It owns user
dialogue, exploration and findings integration, design, planning, task and
requirements definition, scope, dependencies, file ownership, delegation,
acceptance measurement, review/test orchestration, aggregation, and final
judgment. The main/root Sol does not perform concrete repository
implementation.

Planning is owned by the main/root Sol and is not delegated to a planning
subagent. Workers receive bounded task and requirements inputs from the
commander; they do not redefine the plan, scope, or acceptance criteria.

## Codex Subagent Default

Every Codex subagent starts at `model = "gpt-5.6-luna"` with
`model_reasoning_effort = "max"`, regardless of role name. This applies to
read-only exploration, implementation, review, testing, documentation, and
direct `/codex` consultation, including role TOMLs and explicit
`spawn_agent` calls. The worker-delegation contract defines the actor/effort
ladder, promotion policy, valid combinations, and runner behavior.

## Concrete Work Delegation

Concrete repository implementation in Codex uses the native
`.codex/skills/worker-delegation/SKILL.md` contract and its runner. That skill
is the sole SSOT for the worker actor/effort ladder, promotion policy, valid
actor/effort combinations, and runner/execution contract.
