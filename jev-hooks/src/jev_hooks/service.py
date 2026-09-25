"""Fail-open service boundary around configuration, redaction and one Jev call."""

from __future__ import annotations

import json
import math
import sys
import re
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from . import jev_client, logbook
from .config import Config, load_config, resolve_api_key
from .jev_client import JevError, JevResult
from .redact import clip, redact
from .telemetry import record_event

_SENSITIVE_NAME = re.compile(
    r"(?i)(?:api[_-]?key|apikey|secret|token|passw(?:or)?d|pwd|credential|private[_-]?key|authorization|auth)"
)
_MAX_STATE_DEPTH = 24
_MAX_STATE_NODES = 20_000


@dataclass(frozen=True)
class Evaluation:
    status: str
    reason: str
    result: Optional[JevResult] = None


class _StateBudget:
    def __init__(self, limit: int) -> None:
        self.remaining = max(0, limit)
        self.nodes = 0


def _clip_utf8(text: str, limit: int) -> str:
    raw = text.encode("utf-8", errors="replace")
    if len(raw) <= limit:
        return text
    marker = " …[truncated]… "
    marker_bytes = marker.encode("utf-8")
    if limit <= len(marker_bytes):
        return raw[:limit].decode("utf-8", errors="ignore")
    head_budget = int((limit - len(marker_bytes)) * 0.7)
    tail_budget = limit - len(marker_bytes) - head_budget
    head = raw[:head_budget].decode("utf-8", errors="ignore")
    tail = raw[-tail_budget:].decode("utf-8", errors="ignore") if tail_budget else ""
    return head + marker + tail


def _clean_state_value(value: Any, budget: _StateBudget, depth: int = 0) -> Any:
    budget.nodes += 1
    if budget.nodes > _MAX_STATE_NODES:
        return "[truncated]"
    if depth >= _MAX_STATE_DEPTH:
        return "[depth limit]"
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, str):
        clean = redact(value)
        clean = _clip_utf8(clean, budget.remaining)
        budget.remaining = max(0, budget.remaining - len(clean.encode("utf-8", errors="replace")))
        return clean
    if isinstance(value, Mapping):
        out: Dict[str, Any] = {}
        for raw_key, raw_value in value.items():
            if budget.nodes >= _MAX_STATE_NODES or budget.remaining <= 0:
                break
            key = _clip_utf8(redact(str(raw_key)), min(256, budget.remaining))
            budget.remaining = max(0, budget.remaining - len(key.encode("utf-8", errors="replace")))
            if _SENSITIVE_NAME.search(key):
                out[key] = "[REDACTED]"
            else:
                out[key] = _clean_state_value(raw_value, budget, depth + 1)
            if len(out) >= 10_000:
                break
        if len(out) < len(value):
            out["_truncated"] = True
        return out
    if isinstance(value, (list, tuple)):
        out = []
        for item in value:
            if budget.nodes >= _MAX_STATE_NODES or budget.remaining <= 0 or len(out) >= 10_000:
                out.append("[truncated]")
                break
            out.append(_clean_state_value(item, budget, depth + 1))
        return out
    if isinstance(value, (bytes, bytearray)):
        return _clean_state_value(bytes(value).decode("utf-8", errors="replace"), budget, depth + 1)
    try:
        return _clean_state_value(str(value), budget, depth + 1)
    except Exception:
        return "[unsupported value]"


def _bounded_state(state: Any, limit: Any) -> Any:
    try:
        max_bytes = int(limit)
    except (TypeError, ValueError, OverflowError):
        max_bytes = 1_500_000
    max_bytes = max(1, min(max_bytes, 20_000_000))
    cleaned = _clean_state_value(state, _StateBudget(max_bytes))
    try:
        encoded = json.dumps(cleaned, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError, RecursionError):
        encoded = json.dumps({"_note": "state could not be represented safely"}, ensure_ascii=False)
    if len(encoded.encode("utf-8")) <= max_bytes:
        return cleaned
    if max_bytes < 128:
        return 0

    # A compact marker keeps the API payload valid JSON while making the cap strict.
    preview = _clip_utf8(redact(encoded), max(0, max_bytes // 8))
    reduced: Any = {"_note": "state exceeded configured byte limit", "_preview": preview}
    while len(json.dumps(reduced, ensure_ascii=False, separators=(",", ":")).encode("utf-8")) > max_bytes:
        preview = _clip_utf8(preview, max(0, len(preview.encode("utf-8")) // 2))
        reduced = {"_note": "state exceeded configured byte limit", "_preview": preview}
        if not preview:
            break
    return reduced


def _safe_questions(questions: dict) -> dict:
    # Preserve question/option identifiers, but scrub dynamic rubrics as well as state.
    cleaned = {}
    for qid, question in questions.items():
        item = dict(question)
        if "instructions" in item:
            item["instructions"] = _bounded_state(item["instructions"], 32_000)
        criteria = item.get("criteria")
        if isinstance(criteria, dict):
            item["criteria"] = {option: _bounded_state(rubric, 8_000) for option, rubric in criteria.items()}
        cleaned[qid] = item
    return cleaned


def _elapsed_ms(started: float) -> int:
    return max(0, int((time.monotonic() - started) * 1000))


def _emit(
    cfg: Config,
    *,
    policy_id: Any,
    status: str,
    reason: str,
    api_attempted: bool,
    runtime: Any,
    event: Any,
    model: Any = "",
    usage: Any = None,
    elapsed_ms: Any = None,
    environ: Optional[Mapping[str, Any]] = None,
    cwd: Optional[Path | str] = None,
) -> None:
    try:
        recorded = record_event(
            cfg.state_path(),
            policy_id=policy_id,
            runtime=runtime,
            event=event,
            model=model or cfg.model,
            status=status,
            reason=reason,
            api_attempted=api_attempted,
            usage=usage,
            elapsed_ms=elapsed_ms,
            environ=environ,
            cwd=cwd,
        )
        if not recorded:
            sys.stderr.write("jev-hooks: 利用量を記録できません。このイベントは費用集計に含まれません\n")
    except Exception:
        # Metrics are best-effort and may never change Stop behavior.
        pass


def _load_cfg(cfg: Optional[Config], environ: Optional[Mapping[str, Any]]) -> Config:
    return cfg if cfg is not None else load_config(None if environ is None else dict(environ))


def evaluate(
    policy_id: str,
    state: Any,
    questions: dict,
    *,
    cfg: Optional[Config] = None,
    environ: Optional[dict] = None,
    runtime: str = "manual",
    event: str = "",
    session_id: str = "",
    turn_id: str = "",
    ask_fn: Optional[Callable[..., JevResult]] = None,
    timeout_s: Optional[float] = None,
    cwd: Optional[Path | str] = None,
) -> Evaluation:
    """Evaluate one state, returning skips/errors instead of raising to a hook."""
    del session_id, turn_id  # identifiers are intentionally not persisted
    started = time.monotonic()
    config: Optional[Config] = cfg
    attempted = False
    model: Any = ""
    try:
        config = _load_cfg(cfg, environ)
        model = config.model
        if config.mode == "off":
            return Evaluation("skipped", "mode_off")

        api_key, _source = resolve_api_key(None if environ is None else dict(environ))
        if not api_key:
            _emit(config, policy_id=policy_id, status="skipped", reason="api_key_missing", api_attempted=False,
                  runtime=runtime, event=event, model=model, environ=environ, cwd=cwd)
            return Evaluation("skipped", "api_key_missing")

        try:
            timeout = float(config.api_timeout_s)
            total_timeout = float(config.total_timeout_s)
        except (TypeError, ValueError, OverflowError):
            timeout = 3.0
            total_timeout = 5.0
        if not math.isfinite(timeout) or timeout <= 0:
            timeout = 3.0
        if not math.isfinite(total_timeout) or total_timeout <= 0:
            total_timeout = 5.0
        limits = [timeout, total_timeout]
        if timeout_s is not None:
            try:
                requested = float(timeout_s)
                if math.isfinite(requested) and requested > 0:
                    limits.append(requested)
            except (TypeError, ValueError, OverflowError):
                pass
        effective_timeout = min(limits)
        safe_state = _bounded_state(state, config.max_transcript_bytes)
        call = ask_fn or jev_client.ask
        attempted = True
        result = call(
            api_url=config.api_url,
            api_key=api_key,
            model=config.model,
            state=safe_state,
            questions=_safe_questions(questions),
            timeout_s=effective_timeout,
        )
        if not isinstance(result, JevResult):
            raise JevError("API_BAD_RESPONSE", "client returned an invalid result")
        model = result.model or config.model
        _emit(config, policy_id=policy_id, status="ok", reason="evaluated", api_attempted=True,
              runtime=runtime, event=event, model=model, usage=result.usage,
              elapsed_ms=_elapsed_ms(started), environ=environ, cwd=cwd)
        # Keep typed decisions inspectable in observe mode, without request text.
        logbook.append(config.state_path(), {
            "ts": logbook.now_iso(), "policy_id": str(policy_id), "runtime": runtime,
            "event": event, "mode": config.mode, "api_model": model,
            "answers": {qid: answer.as_log() for qid, answer in result.answers.items()},
        }, config.log_max_bytes, cwd=cwd)
        return Evaluation("ok", "evaluated", result)
    except Exception as exc:
        reason = exc.code if isinstance(exc, JevError) and isinstance(exc.code, str) else "API_FAILURE"
        if config is None:
            try:
                config = Config()
            except Exception:
                config = None
        if config is not None:
            _emit(config, policy_id=policy_id, status="error", reason=reason, api_attempted=attempted,
                  runtime=runtime, event=event, model=model, elapsed_ms=_elapsed_ms(started) if attempted else None,
                  environ=environ, cwd=cwd)
        return Evaluation("error", reason)


def record_skip(
    policy_id: str,
    reason: str,
    *,
    cfg: Optional[Config] = None,
    environ: Optional[dict] = None,
    runtime: str = "manual",
    event: str = "",
    session_id: str = "",
    turn_id: str = "",
    cwd: Optional[Path | str] = None,
) -> None:
    """Record one local gate without making a request; never raises."""
    del session_id, turn_id
    try:
        config = _load_cfg(cfg, environ)
        if config.mode == "off":
            return
        _emit(config, policy_id=policy_id, status="skipped", reason=str(reason), api_attempted=False,
              runtime=runtime, event=event, model=config.model, environ=environ, cwd=cwd)
    except Exception:
        pass
