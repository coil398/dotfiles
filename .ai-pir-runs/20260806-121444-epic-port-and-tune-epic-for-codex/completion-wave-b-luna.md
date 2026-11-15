Implemented the owned Codex assets:

- Rewrote `pir2async` with `spawn_agent`, `send_message`, `followup_task`, and `worker-delegation`.
- Added deterministic completion gate and executable verifier.
- Integrated the required gate into `pir2`.
- Added walkthrough HTML mode and self-contained template.

Validation:

- `sh -n` / `bash -n`: exit 0
- Verifier: 3 blocks syntax-valid; all 8 fixtures matched
- No forbidden Claude/runtime references
- Verifier mode: executable (`100755`)
- `git diff --check`: clean
- Nothing staged, committed, or pushed

Caveat: `etc/test-codex-contracts.sh` still contains legacy `pir2async` assertions outside the owned scope; it was not modified.