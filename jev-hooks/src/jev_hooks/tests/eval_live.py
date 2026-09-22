#!/usr/bin/env python3
"""Live Jev evaluation against anonymized fixtures. Does not write secrets.

    python3 -m jev_hooks.tests.eval_live --live

Without --live this only lists cases. Mock unit tests passing is not accuracy.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from jev_hooks import policy  # noqa: E402
from jev_hooks.codex_hook import evaluate  # noqa: E402
from jev_hooks.config import Config, load_config, resolve_api_key  # noqa: E402
from jev_hooks.tests import rollout_fixture as fx  # noqa: E402
from jev_hooks.tests.eval_cases import ALLOW, CONTINUE, cases  # noqa: E402


def _family(verdict: str) -> str:
    if verdict in (policy.CONTINUE_WORK, policy.CONTINUE_VERIFY):
        return CONTINUE
    return ALLOW


def run_live(timeout_s: float) -> int:
    key, source = resolve_api_key()
    if not key:
        sys.stderr.write("TYPESAFE_API_KEY missing (environment only). Skip live eval.\n")
        return 2
    from dataclasses import replace
    cfg = replace(load_config(), mode="observe", api_timeout_s=timeout_s, total_timeout_s=timeout_s + 2.0)
    env = {"TYPESAFE_API_KEY": key, "HOME": str(Path.home())}
    rows: List[Dict[str, Any]] = []
    false_continue = 0
    false_allow = 0
    skipped = 0
    with tempfile.TemporaryDirectory() as tmp:
        for i, case in enumerate(cases()):
            path = Path(tmp) / f"{case.case_id}.jsonl"
            fx.write(path, case.lines)
            payload = {
                "session_id": f"eval-{i}",
                "turn_id": case.turn_id,
                "transcript_path": str(path),
                "cwd": "/work/sample-app",
                "hook_event_name": "Stop",
                "model": "gpt-6-astra",
                "permission_mode": "default",
                "stop_hook_active": False,
                "last_assistant_message": case.last_assistant_message,
            }
            outcome = evaluate(payload, cfg, environ=env, dry_run=True)
            verdict = outcome.record.get("verdict")
            reason = outcome.record.get("reason_code")
            fam = _family(str(verdict))
            match = fam == case.family
            if reason in (
                "NO_API_KEY",
                "API_AUTH",
                "API_TIMEOUT",
                "API_RATE_LIMIT",
                "API_SERVER_ERROR",
                "API_BAD_RESPONSE",
                "API_NETWORK",
                "API_HTTP_ERROR",
            ):
                skipped += 1
                match = None
            elif not match:
                if fam == CONTINUE:
                    false_continue += 1
                else:
                    false_allow += 1
            rows.append(
                {
                    "case_id": case.case_id,
                    "expected_family": case.family,
                    "expected_verdicts": list(case.expected_verdicts),
                    "verdict": verdict,
                    "reason_code": reason,
                    "answers": outcome.record.get("answers"),
                    "family_match": match,
                    "note": case.note,
                }
            )
    report = {
        "key_source": source,
        "threshold": cfg.confidence_threshold,
        "model": cfg.model,
        "provisional_threshold": True,
        "false_continue": false_continue,
        "false_allow": false_allow,
        "skipped_transport": skipped,
        "cases": rows,
    }
    sys.stdout.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    if skipped:
        return 2
    return 0 if false_continue == 0 and false_allow == 0 else 1


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="call the TypeSafe API")
    parser.add_argument("--timeout", type=float, default=8.0)
    args = parser.parse_args(argv)
    if not args.live:
        for case in cases():
            sys.stdout.write(f"{case.case_id}\t{case.family}\t{case.note}\n")
        return 0
    return run_live(args.timeout)


if __name__ == "__main__":
    sys.exit(main())
