# AI Workflow Architecture Spec

_Status: Adopted_
_Last updated: 2026-08-13_

## Purpose

This repository supports Claude Code, Codex, OpenCode, and Cursor workflows without forcing them into identical runtime behavior.

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
| `.codex/<name>.config.toml` | Hand-written Codex named profile selected explicitly by a launcher | Native source |
| `.codex/agents/**` | Codex custom agents | Native overlay |
| `.codex/skills/**` | Codex-specific skills and adapted skill snapshots | Native overlay |
| `.codex/skills/worker-delegation/**` | Codex-native concrete-work runner and actor contract | Native overlay |
| `~/.config/opencode/**` | OpenCode config and adapter layer | Adapter/native layer |
| `.cursor/rules/**` | Cursor rules generated from `AGENTS.md` | Generated adapter |
| `.cursor/mcp.json` | Cursor MCP config generated from `mcp-servers.json` | Generated adapter |
| `.cursor/agents/**` | Cursor custom subagents | Native overlay |
| `.cursor/skills/**` | Cursor-specific skills | Native overlay |

## Rules

1. Do not require `.claude/**`, `.agents/**`, `.codex/**`, `.cursor/**`, and OpenCode files to match byte-for-byte.
2. Put cross-runtime intent in `AGENTS.md` or `.agents/skills/**`.
3. Put runtime mechanics in native overlays.
4. Treat `.codex/AGENTS.md` and `.codex/config.toml` as generated files.
5. Treat `.codex/agents/**` and `.codex/skills/**` as Codex-native editable overlays.
6. Do not generate `.claude/**` from Codex, OpenCode, or Cursor sources.
7. When a runtime-specific rule becomes broadly useful, promote the portable part into the shared core and keep only the adapter/runtime details native.
8. Treat `.cursor/rules/**` and `.cursor/mcp.json` as generated files. Treat `.cursor/agents/**` and `.cursor/skills/**` as Cursor-native editable overlays.
9. Cursor shared Rules must be a **summary + pointer to `AGENTS.md`**, not a full copy (avoids double-load with repo `AGENTS.md`).
10. Codex named profiles are native runtime overlays. Their source is `.codex/<name>.config.toml`, `etc/link-codex-runtime.sh` owns the corresponding `~/.codex/<name>.config.toml` runtime link, and a dedicated launcher selects the profile with `-p <name>`. Profiles are opt-in; the ordinary generated/default Codex configuration remains unchanged.

## Work-unit delegation contract

Portable work-unit delegation behavior is owned by `AGENTS.md` under `Subagent Operation`; this architecture records only the ownership boundary between root/main orchestration and concrete unit execution.
Codex-specific repository-changing mechanics remain owned by `.codex/skills/worker-delegation/SKILL.md`.

## sync-codex.sh Contract

Default `bash etc/sync-codex.sh` does:

- Generate `.codex/config.toml`.
- Generate `.codex/AGENTS.md`.
- Generate Codex-readable copies of shared support documents such as `.codex/format.md`, `.codex/pir-handoff.md`, `.codex/ui-ux-principles.md`, and related protocol docs.

Default `bash etc/sync-codex.sh` does **not**:

- Regenerate `.codex/agents/*.toml` from `.claude/agents/*.md`.
- Regenerate `.codex/skills/**` from `.agents/skills/**`.

The default sync therefore preserves Codex-native overlays, including
`.codex/skills/worker-delegation/**`. The worker package is not a shared-skill
seed and its actor/model routing is not copied into `AGENTS.md` or `.agents/**`.

Legacy mirror regeneration is available only as an explicit operation:

```bash
SYNC_CODEX_LEGACY_MIRROR=1 bash etc/sync-codex.sh
```

Use the legacy mode only when intentionally refreshing old mirror snapshots. It is not the normal maintenance path.

## worker-delegation contract

Concrete implementation work in Codex uses the native
`.codex/skills/worker-delegation/SKILL.md` contract and its executable
`scripts/run-worker.sh` runner. The actor ladder and its evidence ledger are
deliberately owned by the Sol commander:

This is the default for **concrete repository-changing implementation across
Codex workflows**. It covers changes to repository-owned files, including
Codex-native overlays. Sol retains planning, scope, task/requirements,
orchestration, acceptance measurement, and final judgment. Temporary
task/requirements inputs, run ledgers, handoff/next-step state, and other
non-repository orchestration artifacts remain separate Sol-owned workflow
state; they are not a substitute for worker implementation evidence.

The parent/main Sol is commander only. It owns user dialogue, exploration,
design decisions, scope, task/requirements, actor and effort selection,
delegation, acceptance measurement, aggregation, review/test orchestration,
and final judgment; it never performs concrete repository implementation.
Concrete implementation is performed by an explicit worker subagent.

Every Codex subagent starts with `model = "gpt-5.6-luna"` and
`model_reasoning_effort = "max"`, independent of role name. This covers
read-only exploration, planning, implementation, review, testing, documentation
and other material-writing work, as well as the explicit `spawn_agent` used by
`/codex` consultation. The role overlays and generation scripts must therefore
not introduce role-based lower efforts or stronger-model defaults.

The actor ladder in the native
`.codex/skills/worker-delegation/SKILL.md` is the sole SSOT for model
promotion. It is **Luna Max → measured Terra High → evidence-only Terra Max →
exceptional Sol High worker → evidence-only Sol Max**. Terra High is allowed
only after sufficiently specified inputs and Sol's measured evidence of Luna
capability or local-reasoning insufficiency in the diff, verification,
reproduction, or counterexample. Terra Max additionally requires documented
multi-stage causality, design contradiction, cross-module invariants,
security/data-integrity risk, or Terra High insufficiency. Sol High is allowed
only after measured Terra insufficiency, and Sol Max only after
highest-complexity/high-risk evidence or documented Sol High insufficiency.

No runner or worker may automatically fall back, change actor, or increase
effort. Requirements or input ambiguity/insufficiency, permissions,
environment/tool or CLI failure, external state, and worker startup failure are
not promotion evidence; they return control to the commander for resolution.
The main/root Sol remains on its existing commander default and is not changed
by this worker ladder.

The Codex main/parent commander defaults to `model = "gpt-5.6-sol"` with
`model_reasoning_effort = "high"`. High is the normal commander setting because
the main Sol performs judgment, planning, acceptance, and reviewer/tester
aggregation; it does not perform concrete implementation. `gpt-5.6-sol` Max
is evidence-only for an exceptional Sol worker and is never the main default.
Luna/Terra model pins belong to the worker-delegation runner, not this main
config.

The optional-stage ladder is **Luna Max → measured Terra High → evidence-only
Terra Max → exceptional Sol High worker → evidence-only Sol Max**:

- **Luna Max default worker** is the default worker.
- **measured Terra escalation (Terra High)** is the normal measured escalation only after sufficiently
  specified inputs and measured Luna capability or local-reasoning
  insufficiency.
- **Terra Max** is allowed only when Sol records at least one of
  multi-stage causality, design contradiction, cross-module invariants,
  security/data-integrity risk, or documented Terra High insufficiency. The
  same-cause Terra Max attempt is limited to one.
- **Sol High worker** is exceptional and allowed only after measured Terra
  capability or local-reasoning insufficiency. This is a worker invoked by the
  commander, never implementation by the parent/main Sol.
- **Sol Max** is allowed only for highest-complexity/high-risk evidence or
  documented Sol High insufficiency, and at most once for the same cause.

Not every stage is mandatory. Terra Max and Sol Max are evidence-only and are
not routine final stages. Requirements ambiguity, input insufficiency,
environment/tool failure, permissions, and external-state failure return
control to the commander and do not justify stronger model/effort. The runner
executes exactly the explicit actor and effort: there is no automatic
fallback, actor selection, or effort escalation.

The reviewer and tester are separate Sol-controlled gates after acceptance:
reviewer owns quality (correctness, security, regression, maintainability),
tester owns runtime behavior, and neither worker self-reports nor runner
completion is an acceptance, reviewer, or tester PASS.

The deterministic completion protocol is a common worker-delegation SSOT at
`.codex/skills/worker-delegation/references/deterministic-completion-check.md`,
with its verifier at
`.codex/skills/worker-delegation/scripts/verify-deterministic-check.sh`. Every
concrete worker job and correction in `debug`, `ir`, `writing-plan`,
`instruction-refactor`, `pir2`, and `pir2async` records a pre-set immediately
before launch, then runs the canonical post-set/delta/CLAIMED gate immediately
after the worker report and before Sol acceptance, reviewer, or tester. A
`PHANTOM_CLAIM` is a hard failure that returns to a correction worker;
`UNDECLARED_CHANGE` is a recorded warning. The verifier report and
pre/post/delta paths are part of acceptance evidence. Workflow files reference
this SSOT and only add their own index/order fields; they do not copy the full
protocol. The common verifier retains all eight PHANTOM/UNDECLARED/NO_OP,
non-ASCII, fenced-example, submodule, staged-claim, and pre-existing-staged
fixtures.

For those six workflows, successful completion requires every role in the
fixed `REVIEWER_SET` to return `VERDICT: PASS` before a separate
`spawn_agent(agent_type="tester")` using `.codex/agents/tester.toml` is
started. Each tester run has a `TEST_INDEX` and `${RUN_DIR}/test-${TEST_INDEX}.md`
report containing actual verification, including appropriate static/config
validation for documentation-only changes. A tester FAIL creates a concrete
correction task/requirements, uses the same Luna-first adaptive ladder, reruns
the deterministic gate, reruns every reviewer (including prior PASS roles),
then reruns tester. Retry-cap exhaustion is overall FAIL and a user-decision
hard stop; it can never be reported as successful completion.

The canonical worker report schema is exactly:
`ACTOR`, `ACTUAL_MODEL`, `ACTUAL_EFFORT`, `STATUS`, `CHANGED_FILES`,
`OBSERVED_RESULTS`, `BLOCKERS`, and `ESCALATION_REASON`. The runner injects the
expected actor/model/effort into the worker prompt. Task-scoped checks are
allowed, but independent tester verdicts remain separate and workers never
claim acceptance or PASS.

Codex implementation workflows `debug`, `epic`, `instruction-refactor`, `ir`,
`pir2`, `pir2async`, and `writing-plan` connect their concrete work to this
contract.
Reviewer/tester execution remains a separate quality/runtime gate after Sol
acceptance and never becomes worker self-acceptance. `brainstorm` is
**design-only** and does not start implementation workers. `pir2async` is
experimental, but every concrete repository implementation and correction it
performs uses the shared worker-delegation ladder
`Luna Max -> measured Terra High -> evidence-only Terra Max -> exceptional Sol
High worker -> evidence-only Sol Max`; normal implementation uses `pir2`.

The runner exposes only explicit `luna`, `terra`, and `sol` actors. It maps
them exactly to `gpt-5.6-luna`, `gpt-5.6-terra`, and `gpt-5.6-sol`; `luna`
accepts Max only and defaults to Max, while `terra` and `sol` default to High
and accept explicit High or Max. The selected effort is forwarded unchanged
as `-c model_reasoning_effort="..."`. Unknown actors, unknown efforts, and
invalid combinations return exit 2 before Codex is invoked. The shared
`.agents/**` core must not acquire these Codex-native worker pins or runner
references.

The runner physically canonicalizes `<cwd>` and requires it to equal the
physical Git top-level. It requires a real, non-symlink `<cwd>/.codex` whose
physical path remains inside that root. A descendant symlink is allowed only
as one verified hop to a current-UID-owned, non-group/world-writable target
inside the same physical Git root; external, broken, nested, and `.git`
targets fail closed. The portable inventory uses Perl core `File::Find`,
`Cwd`, and `Digest::SHA`, then forwards only the canonical `.codex` path as
`--add-dir`. Worker output is restricted to a real, non-symlink parent
physically inside either the canonical cwd or the standard Sol artifact root
`$HOME/.ai-pir-runs`; cwd-local output is independent of artifact-root
availability, while external artifact output requires that standard root to
exist as a real non-symlink directory. Symlink components at or below the
selected root are rejected while harmless physical aliases such as `/var` are
canonicalized.
When PowerShell launches the Git for Windows runner, caller-supplied absolute
paths may use `C:\Users\...`, `C:/Users/...`, or Git Bash's `/c/Users/...`;
the runner normalizes them to the same path before `dirname` or boundary
inspection. WSL is not part of this execution path. Drive-
relative, UNC/double-slash, and ambiguous `.`/`..` spellings fail closed.
Symlink inspection is root-bounded: it starts at the candidate physical leaf
and stops at the selected allowed root, so aliases above that root remain
allowed while a symlink/reparse component at the root or below remains
rejected, including a link whose target resolves back inside the root.
Codex writes to an exclusive temporary file in the selected parent, and the
runner publishes the final report with a same-filesystem no-replace hard link.
Thus a pre-existing or raced final file/symlink is never overwritten. This
narrow `--add-dir` capability supports authorized Codex-native overlay and
generated-adapter changes; it does not change the task's source ownership boundary
or authorize writes to out-of-scope files. The runner does not use
`danger-full-access`, sandbox bypass flags, or `chmod` to widen permissions.

### Runner threat model and limits

The runner's proportional hardening is intended to prevent configuration
mistakes, unsafe symlinks, writes by another UID or an untrusted group, and
detectable accidental races. It sets `umask 077`, requires the current UID to
own the repository root, `.codex`, the selected output allowed root, and the
output parent, rejects group/world writable modes, and scans every `.codex`
descendant without following links. It records each boundary's device/inode,
owner, and mode on first validation, then revalidates the approved symlink inventory, the
descendant scan, and identity/owner/mode immediately before the Codex exec and
immediately after it, whether Codex succeeds or fails. Temporary cleanup is
non-recursive and removes only one temp file when its parent identity still
matches.

This does **not** claim complete TOCTOU protection against a malicious
same-UID host process or a fully untrusted same-UID worker. The Codex CLI
accepts path strings only; the runner cannot pass directory/file-descriptor
capabilities. `openat` or atomic-open techniques therefore cannot completely
solve this path-based boundary, and the runner must not be described as having
complete protection from them. Stronger same-UID isolation requires a separate
UID, an OS sandbox, mount isolation, or a CLI that accepts fd capabilities.

## Review Policy

Reviewers should classify files before judging drift:

- Generated adapters: `.codex/AGENTS.md`, `.codex/config.toml`, OpenCode generated config/docs, `.cursor/rules/**`, `.cursor/mcp.json`.
- Shared core: `AGENTS.md`, `.agents/skills/**`, `mcp-servers.json`.
- Native overlays: `.claude/**`, `.codex/agents/**`, `.codex/skills/**`, `.cursor/agents/**`, `.cursor/skills/**`.

Valid findings:

- A generated adapter changed without a corresponding source/script change.
- A broadly reusable rule is trapped in only one native overlay.
- A runtime-specific mechanism is written into shared core when it should stay native.
- A native overlay claims generated ownership or has stale generated markers.
- Cursor Rules contain a full copy of `AGENTS.md` (should be summary + pointer only).

Invalid findings:

- `.claude/**` and `.codex/**` / `.cursor/**` differ merely because the runtimes operate differently.
- `.codex/agents/**` or `.codex/skills/**` or `.cursor/agents/**` or `.cursor/skills/**` do not match shared sources byte-for-byte.

## sync-opencode.sh Contract

Default `bash etc/sync-opencode.sh` does:

- Generate `~/.config/opencode/opencode.json` from `mcp-servers.json` (excluding `claudeCodeOnly` and `codexOnly`; `openCodeOnly` servers are included), an OpenCode-specific permission policy owned by the script (bash allow-by-default with dangerous-command asks, edit allow, read deny list inherited from `.claude/settings.json#permissions.deny`, and `external_directory: {"~/**": "allow"}` because OpenCode defaults it to ask and "always" approvals are session-scoped, which caused approval fatigue for any out-of-cwd reference; the Claude Code allow allowlist is intentionally not carried over), and `lsp: true` (OpenCode disables LSP when the key is omitted).
- Generate `~/.config/opencode/AGENTS.md`: full copy of shared `AGENTS.md` plus an OpenCode-specific supplement owned by the script itself (tool-name remap table, skill availability classification, compatibility gaps, model alias mapping notes).
- Convert `.claude/agents/*.md` to `~/.config/opencode/agents/<name>.md`: frontmatter reduced to `description` / `mode: subagent` / `model` (bare aliases mapped by `map_model_name`: `sonnet`→`anthropic/claude-sonnet-5`, `opus`→`anthropic/claude-opus-4-8`, `fable`→`anthropic/claude-fable-5`); body copied verbatim. Orphan AUTO-GENERATED agents are removed.
- Support `bash etc/sync-opencode.sh --check` (no write; exit non-zero if generated outputs would change or an orphan agent would be removed).

Default `bash etc/sync-opencode.sh` does **not**:

- Convert agent-frontmatter `tools:` restrictions or per-agent permissions. Bodies claiming tools-based role isolation are not enforced by the runtime; the generated AGENTS.md supplement states this explicitly.
- Create repo-side native overlays (`.opencode/**`). OpenCode stays fully generated under `~/.config/opencode/**`; a native overlay remains deferred until runtime needs diverge.

Contract test: `bash etc/test-opencode-contracts.sh` (live `--check`, fake-HOME fresh sync + idempotency, MCP/permission shape, agent frontmatter + verbatim-body contract, supplement sections, stale-reference regression, orphan cleanup + hand-written protection). It is included in the `etc/test-all-contracts.sh` aggregate runner.

Skills are not registered via an `opencode.json#skills` key. Discovery relies on OpenCode's external-skill autoload of `~/.agents/skills/**` and `~/.claude/skills/**`, backed by the `~/.agents` symlink created by `etc/link.sh`.

## sync-cursor.sh Contract

Default `bash etc/sync-cursor.sh` does:

- Generate `.cursor/rules/shared-agents.mdc` as a **summary + SSOT pointer** to `AGENTS.md` (not a full copy).
- Generate `.cursor/mcp.json` from `mcp-servers.json` (excluding `claudeCodeOnly`, `openCodeOnly`, and `codexOnly` servers). Convert `type: "remote"` entries to url-only objects for Cursor compatibility.
- Support `bash etc/sync-cursor.sh --check` (no write; exit non-zero if generated outputs would change).

Default `bash etc/sync-cursor.sh` does **not**:

- Regenerate `.cursor/agents/**` from `.claude/agents/**`.
- Regenerate `.cursor/skills/**` from `.agents/skills/**`.
- Overwrite existing native overlays (no force-seed path).

One-time seed is available as an explicit operation:

```bash
SYNC_CURSOR_SEED=1 bash etc/sync-cursor.sh
# or
bash etc/seed-cursor-overlay.sh
```

Phase-3 seed set (default in `etc/seed-cursor-overlay.sh`):

- Agents: phase-2 set plus `codex-runner` (Codex CLI bridge).
- Skills: phase-2 set plus `pir2codex`, `ai-design-system`, `ai-diary`, `ai-ltm`, `unity-mcp-skill`, `codex`.
- Contract test: `bash etc/test-cursor-contracts.sh` (sync `--check`, MCP filter, seed non-destructive, link refuse non-symlink, phase-3 inventory).

Use seed mode only when intentionally creating missing overlays. It is not the normal maintenance path. Existing overlays are never overwritten. `seed-cursor-overlay.sh` ends with an overlay hygiene check (blocks known-bad residues: broken `dotfiles .claude reference:`, `~/.claude/projects`, vendor model pins, Agent-as-launcher wording).

### Cursor skill / agent precedence

When both `.agents/skills/<name>` and `.cursor/skills/<name>` exist:

1. **Cursor runtime** uses `.cursor/skills/<name>` via a **real-directory materialize** into `~/.cursor/skills/<name>` (`link.sh`). Symlinks are intentionally avoided: Cursor does not discover symlinked personal skills under `~/.cursor/skills/` (upstream bug; forum #149693).
2. **`.agents/skills`** remains shared core for Codex/OpenCode and for seed/promote. Do not treat it as the live Cursor skill path.
3. Overlay `SKILL.md` / references must point at `.cursor/skills/...` paths. Cross-runtime shared rules belong in `AGENTS.md` or `.agents/skills` and are promoted intentionally. Edit SSOT in `dotfiles/.cursor/skills`, then re-run `link.sh` to refresh `~/.cursor/skills`.
4. Global Claude protocol files that remain valid via `link.sh` (e.g. `~/.claude/pir-handoff.md`) may be referenced by absolute home path; do not invent non-path “reference:” placeholders.
5. **Slash-menu names**: Cursor overlay directory and frontmatter `name` share the bare skill basename (e.g. folder `.cursor/skills/epic/`, slash `/epic`). Cursor requires `name` to match the parent folder. `.cursor/skills` precedence makes a `cursor-` prefix unnecessary. Maintain with `etc/normalize-cursor-skill-names.sh` (invoked from `seed-cursor-overlay.sh` on new seeds).

`etc/link.sh` links `.cursor/{agents,rules,mcp.json}` as symlinks (refuses to replace non-symlink destinations) and **materializes** `.cursor/skills/*` as real directories under `~/.cursor/skills/`. Never touch `~/.cursor/skills-cursor/`.

## Review Policy (Cursor)

Classify before judging drift:

- Generated adapters: `.cursor/rules/**`, `.cursor/mcp.json`
- Native overlays: `.cursor/agents/**`, `.cursor/skills/**`
- Shared core: `AGENTS.md`, `.agents/skills/**`, `mcp-servers.json`

## Migration State

Completed:

- `sync-codex.sh` no longer rewrites `.codex/agents/**` or `.codex/skills/**` by default.
- `.codex/agents/*.toml` were adopted as Codex-native overlays from the legacy sync snapshot.
- `.codex/skills/*/.codex-generated-from-shared` markers were removed.
- `AGENTS.md` and `AGENTS.override.md` now document the shared-core/native-overlay policy.
- Cursor design adopted: `docs/brainstorm/2026-07-13-cursor-port.md` (Rules=A, native overlays, phase-1 slice).
- `sync-cursor.sh` generates summary Rules + MCP; seed/force paths tightened; phase-1 overlays reduced to explorer/implementer/reviewer + chat.
- Cursor phase 2 (2026-07-13): `seed-cursor-overlay.sh` expanded agents/skills; orchestration overlays (`pir2`, `deepthink`, `epic`, `research`, `pir2async`, `ir`, `debug`, `writing-plan`, `brainstorm`) seeded with Cursor Task/VERDICT notes; Claude-only TeamCreate/hooks skipped; no model pins (role=reasoning|coding only). `deepthink` / `research` / `epic` seed from `.claude/skills` when absent in `.agents/skills`.
- Cursor review FAIL remediations (2026-07-13): removed repo `.codex-runtime/` (auth stays in `~/.codex`); fixed seed path rewrite; Agent→Task / vendor model sweep; epic `PROJECT_MEMORY_DIR` + `.cursor/skills/pir2` refs; hygiene guard; documented skill precedence; partial `/pir2` Task smoke recorded in `docs/plans/2026-07-13-cursor-port.md`.
- Cursor skill naming (2026-08-19): dropped `cursor-` prefix from `.cursor/skills/<name>` / `/<name>` because `.cursor/skills` takes precedence over `.claude` / `.agents`; updated seed/normalize/contracts accordingly.
- Cursor Task model (2026-08-19 / 2026-08-27): Task `model` is omit/`inherit` only (parent Auto). Do not pin vendor slugs or `model=reasoning` as a Task launch arg. Agent overlay `model` is `inherit` or a real model ID; `role: coding|reasoning` is the job class. External-File Protection: add sibling folders via a `.code-workspace` (File → Open Workspace from File), not by opening the JSON as an editor tab.
- Cursor phase 3 (2026-07-15): seeded missing overlays (`ai-design-system`, `ai-diary`, `ai-ltm`, `unity-mcp-skill`, `codex`, `pir2codex`, `codex-runner`); promoted `deepthink` / `research` / `epic` into `.agents/skills`; shared `/codex` SSOT switched to CLI + `codex-runner` (MCP path removed); fixed GNU sed brace bug in seed adapt; epic Cursor overlay reseeded; added `etc/test-cursor-contracts.sh`.

- Remaining follow-up (2026-07-15): `etc/seed-codex-overlay.sh` (agents×6 + skills×4); `etc/check-shared-drift.sh`; OpenCode stays generated; Codex skills stay full snapshots; implement smoke in `docs/plans/2026-07-15-remaining-followup.md`.

Open items:

- None blocking. Optional: longer-running full `/pir2` on an unrelated product repo for soak testing.
- OpenCode: **keep generated agents** from `.claude/agents` via `sync-opencode.sh` (native overlay deferred until runtime needs diverge).
- Codex skills: **keep full skill snapshots** as native overlays; grow with `seed-codex-overlay.sh` (missing-only). Do not re-enable default `SYNC_CODEX_LEGACY_MIRROR`. The `epic` skill is a tracked Codex-native-only overlay and is intentionally excluded from seeding; if that tracked overlay is missing, seeding fails nonzero instead of converting the generic shared/Claude source.
- Drift: **`etc/check-shared-drift.sh`** detects shared skills/agents trapped in one runtime (skill allowlist: `pir2codex`, `design-review`, `overlay-audit`; Codex-agent allowlist: `codex-runner`). `overlay-audit` has a Cursor overlay so `/overlay-audit` is discovered via `~/.cursor/skills`; Codex keeps reading `.agents/skills`. `design-review` is allowlisted because its canonical body is the external design repo SSOT; dotfiles provide only Claude/Codex discovery bootstrap and do not copy the body into Cursor overlay/shared core.

### Codex seed contract

```bash
bash etc/seed-codex-overlay.sh
bash etc/check-shared-drift.sh
```

- Agents seeded: `deliberator`, `epic-planner`, `gate`, `hypothesizer`, `synthesizer`, `thinker` (`codex-runner` omitted).
- Skills seeded from `.agents/skills`: `deepthink`, `research`, `unity-mcp-skill` (`epic` is intentionally excluded because its Codex-native orchestration contract must not be synthesized from the generic source).
- Native-only `epic` contract: `.codex/skills/epic/**` is source-controlled; if the tracked overlay is missing, `seed-codex-overlay.sh` exits nonzero and never treats the generic source as a recovery path.
- Existing overlays are never overwritten.
