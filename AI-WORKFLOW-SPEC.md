# AI Workflow Architecture Spec

_Status: Adopted_
_Last updated: 2026-06-23_

## Purpose

This repository supports Claude Code, Codex, and OpenCode workflows without forcing them into identical runtime behavior.

The adopted architecture is **shared core + native overlays**:

- Shared rules and reusable workflow ideas live in common files.
- Runtime-specific behavior lives in that runtime's native files.
- Sync scripts generate only adapter/config files that are mechanically safe to generate.
- Strict byte-for-byte sync between runtimes is not the default.

## Ownership

| Area | Role | Source type |
|---|---|---|
| `AGENTS.md` | Shared global guidance for Codex/OpenCode adapters | Shared core |
| `.agents/skills/**` | Shared skill core | Shared core |
| `mcp-servers.json` | MCP server registry | Shared config |
| `.claude/**` | Claude Code native agents, skills, hooks, settings | Native source |
| `.codex/AGENTS.md` | Codex guidance generated from `AGENTS.md` | Generated adapter |
| `.codex/config.toml` | Codex config generated from base config and MCP registry | Generated adapter |
| `.codex/config.base.toml` | Hand-written Codex base config | Native source |
| `.codex/agents/**` | Codex custom agents | Native overlay |
| `.codex/skills/**` | Codex-specific skills and adapted skill snapshots | Native overlay |
| `~/.config/opencode/**` | OpenCode config and adapter layer | Adapter/native layer |

## Rules

1. Do not require `.claude/**`, `.agents/**`, `.codex/**`, and OpenCode files to match byte-for-byte.
2. Put cross-runtime intent in `AGENTS.md` or `.agents/skills/**`.
3. Put runtime mechanics in native overlays.
4. Treat `.codex/AGENTS.md` and `.codex/config.toml` as generated files.
5. Treat `.codex/agents/**` and `.codex/skills/**` as Codex-native editable overlays.
6. Do not generate `.claude/**` from Codex or OpenCode sources.
7. When a runtime-specific rule becomes broadly useful, promote the portable part into the shared core and keep only the adapter/runtime details native.

## sync-codex.sh Contract

Default `bash etc/sync-codex.sh` does:

- Generate `.codex/config.toml`.
- Generate `.codex/AGENTS.md`.
- Generate Codex-readable copies of shared support documents such as `.codex/format.md`, `.codex/pir-handoff.md`, and related protocol docs.

Default `bash etc/sync-codex.sh` does **not**:

- Regenerate `.codex/agents/*.toml` from `.claude/agents/*.md`.
- Regenerate `.codex/skills/**` from `.agents/skills/**`.

Legacy mirror regeneration is available only as an explicit operation:

```bash
SYNC_CODEX_LEGACY_MIRROR=1 bash etc/sync-codex.sh
```

Use the legacy mode only when intentionally refreshing old mirror snapshots. It is not the normal maintenance path.

## Review Policy

Reviewers should classify files before judging drift:

- Generated adapters: `.codex/AGENTS.md`, `.codex/config.toml`, OpenCode generated config/docs.
- Shared core: `AGENTS.md`, `.agents/skills/**`, `mcp-servers.json`.
- Native overlays: `.claude/**`, `.codex/agents/**`, `.codex/skills/**`.

Valid findings:

- A generated adapter changed without a corresponding source/script change.
- A broadly reusable rule is trapped in only one native overlay.
- A runtime-specific mechanism is written into shared core when it should stay native.
- A native overlay claims generated ownership or has stale generated markers.

Invalid findings:

- `.claude/**` and `.codex/**` differ merely because the runtimes operate differently.
- `.codex/agents/**` or `.codex/skills/**` do not match `.claude/**` or `.agents/**` byte-for-byte.

## Migration State

Completed:

- `sync-codex.sh` no longer rewrites `.codex/agents/**` or `.codex/skills/**` by default.
- `.codex/agents/*.toml` were adopted as Codex-native overlays from the legacy sync snapshot.
- `.codex/skills/*/.codex-generated-from-shared` markers were removed.
- `AGENTS.md` and `AGENTS.override.md` now document the shared-core/native-overlay policy.

Open items:

- Decide whether OpenCode should also move from generated agents to native overlays.
- Decide whether `.codex/skills/**` should remain full skill snapshots or only contain Codex-specific overrides.
- Add a drift checker that detects "shared rule trapped in one runtime" instead of strict textual mismatch.
