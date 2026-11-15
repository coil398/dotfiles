# Retrospective

- The common worker package should be a Codex-native overlay, not another shared/Claude mirror. Replacing `luna-max-worker` completely avoided two competing actor contracts.
- Sol acceptance must be based on requirements, actual diff, and command output. Worker exit status and self-report remain observational inputs only.
- Model escalation is a policy decision owned by Sol: Luna by default, Terra only for measured capability/local-reasoning insufficiency with sufficient inputs, then Sol-direct only after Terra cannot satisfy the task.
- Independent reviewer/tester gates caught cross-overlay reference drift that worker self-checks and contract tests initially missed. Re-running the same five-role set after remediation closed the loop.
- Codex-native reference verifiers must inspect Codex overlays, derive the repository root from their own location, and remain runnable outside the repository cwd.
- The contract suite intentionally executes default sync to prove native overlays are preserved; in restricted Codex sandboxes this requires an approved write-capable execution path.
