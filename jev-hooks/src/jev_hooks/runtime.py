"""Fail-open adapters for the advisory Jev lifecycle guards."""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, Mapping, Optional

from . import guards
from .config import Config, load_config

_KNOWN_RUNTIMES = {"claude", "codex", "cursor", "grok"}
_MAX_OUTPUT_CONTEXT_CHARS = 1_600


def _event(runtime_name: str, payload: Mapping[str, Any]) -> Any:
    if runtime_name == "grok":
        return payload.get("hookEventName")
    return payload.get("hook_event_name") or payload.get("hookEventName")


def _skill_suggestion(prompt: Any, *, runtime_name: str, payload: Mapping[str, Any], environ: Optional[Dict[str, str]], cfg: Config) -> str:
    if not isinstance(prompt, str) or not prompt.strip():
        return ""
    # An explicitly invoked skill remains the user's choice; Jev only fills gaps.
    if prompt.lstrip().startswith("/"):
        return ""
    from .skills import select_skills

    workspace = payload.get("cwd")
    if not isinstance(workspace, str):
        roots = payload.get("workspace_roots")
        workspace = roots[0] if isinstance(roots, list) and roots and isinstance(roots[0], str) else None
    result = select_skills(prompt, cwd=workspace, environ=environ, runtime=runtime_name, cfg=cfg)
    selected = result.get("selected") if isinstance(result, dict) else None
    if not isinstance(selected, list) or not selected:
        return ""
    item = selected[0]
    if not isinstance(item, dict) or not isinstance(item.get("name"), str) or not isinstance(item.get("path"), str):
        return ""
    name = item["name"][:100]
    path = item["path"][:500]
    description = item.get("description") if isinstance(item.get("description"), str) else ""
    description = " ".join(description.split())[:300]
    return (
        "Jevが選んだ関連Skill候補があります。ユーザーの明示指定や禁止事項を優先し、"
        "依頼に合う場合だけ内容を確認してください。\n"
        f"- {name}: {description}\n"
        f"  {path}"
    )[:_MAX_OUTPUT_CONTEXT_CHARS]


def _hook_specific_output(event: str, context: str) -> Dict[str, Any]:
    if not context:
        return {}
    return {"hookSpecificOutput": {"hookEventName": event, "additionalContext": context}}


def evaluate_event(runtime_name: str, payload: Mapping[str, Any], environ: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Evaluate one hook payload and return only a documented advisory output shape."""
    if runtime_name not in _KNOWN_RUNTIMES or not isinstance(payload, Mapping):
        return {}
    try:
        cfg = load_config(environ)
        if cfg.mode == "off":
            return {}
        raw_event = _event(runtime_name, payload)
        event = guards.normalize_event(runtime_name, raw_event)
        if not event or event == "Stop":
            # The established Stop adapters own their existing behavior.
            return {}

        if runtime_name in {"codex", "claude"} and event == "UserPromptSubmit":
            prompt = payload.get("prompt") or payload.get("user_prompt") or payload.get("userPrompt")
            context = _skill_suggestion(prompt, runtime_name=runtime_name, payload=payload, environ=environ, cfg=cfg)
            if cfg.mode == "observe":
                return {}
            return _hook_specific_output("UserPromptSubmit", context)

        # Cursor's documented preToolUse response schema controls permission and
        # has no documented non-blocking additional-context field. Do not emit
        # an invented field or an implicit allow decision from a permission hook.
        if runtime_name == "cursor" and event in {"PreToolUse", "UserPromptSubmit", "SubagentStop"}:
            return {}

        context = guards.advise_event(runtime_name, raw_event, payload, cfg=cfg, environ=environ)
        if cfg.mode == "observe" or not context:
            return {}

        if runtime_name in {"codex", "claude"}:
            if event == "SubagentStop":
                # Codex documents systemMessage for this event, but does not
                # promise that it is delivered to the model as added context.
                # Claude documents systemMessage as a user-visible warning; its
                # SubagentStop additionalContext would keep the subagent running.
                return {"systemMessage": f"Jev助言（ユーザー向け表示）: {context}"}
            # Claude documents additionalContext without a permission decision
            # for PreToolUse, PostToolUse and PostToolUseFailure.
            return _hook_specific_output(event, context)
        if runtime_name == "cursor":
            # Cursor documents additional_context for postToolUse events.
            if event in {"PostToolUse", "PostToolUseFailure"}:
                return {"additional_context": context[:_MAX_OUTPUT_CONTEXT_CHARS]}
            return {}
        # Grok documents passive stdout as ignored; keep its runtime observe-only.
        return {}
    except Exception:
        # New advisory hooks must never affect the existing action on failure.
        return {}


def _read_payload(stdin: Any, limit: int) -> Dict[str, Any]:
    try:
        raw = stdin.read(limit + 1)
        if isinstance(raw, bytes):
            if len(raw) > limit:
                return {}
            raw = raw.decode("utf-8")
        elif len(raw.encode("utf-8")) > limit:
            return {}
        data = json.loads(raw) if raw.strip() else {}
    except (OSError, UnicodeDecodeError, ValueError, TypeError):
        return {}
    return data if isinstance(data, dict) else {}


def run_hook(runtime_name: str, stdin: Any, stdout: Any, environ: Optional[Dict[str, str]] = None) -> int:
    """Read a bounded JSON hook payload, emit an advisory response, and always exit successfully."""
    try:
        cfg = load_config(environ)
        payload = _read_payload(stdin, max(10_000, min(cfg.max_transcript_bytes, 2_000_000)))
        output = evaluate_event(runtime_name, payload, environ=environ)
        stdout.write(json.dumps(output, ensure_ascii=False, separators=(",", ":")))
        stdout.flush()
    except Exception:
        try:
            stdout.write("{}")
            stdout.flush()
        except Exception:
            pass
    return 0


def main(runtime_name: str, argv: Optional[list[str]] = None) -> int:
    del argv
    return run_hook(runtime_name, sys.stdin, sys.stdout)
