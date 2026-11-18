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
- When you are the root agent and plan to start child agents, read `~/.codex/root-delegation.md` first.

## OpenAI Specifications

Consult the available official `openai-docs` skill for OpenAI
model/API specifications; if unavailable, use official documentation directly.
Codex configuration work does not expand into application API migration.
