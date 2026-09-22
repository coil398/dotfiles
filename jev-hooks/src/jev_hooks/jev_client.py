"""Thin synchronous client for the TypeSafe System One endpoint.

Request/response shapes follow https://docs.typesafe.ai/api :

    POST /v1/systemone  {"state": ..., "model": ..., "questions": {...}}
    -> {"model": ..., "answers": {id: {"type":"choice","choice":..,
        "probabilities": {...}, "confidence": ..}}, "usage": {...}}

One attempt, bounded by ``timeout_s``. No retries: this runs inside a Stop
hook and must return quickly; failures are reported as codes for fail-open.
"""

from __future__ import annotations

import json
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional

from . import VERSION


class JevError(Exception):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class ChoiceAnswer:
    choice: str
    probabilities: Dict[str, float]
    confidence: float

    def as_log(self) -> Dict[str, Any]:
        return {
            "choice": self.choice,
            "confidence": round(self.confidence, 3),
            "probabilities": {k: round(v, 3) for k, v in self.probabilities.items()},
        }


@dataclass(frozen=True)
class JevResult:
    answers: Dict[str, ChoiceAnswer]
    usage: Dict[str, Any] = field(default_factory=dict)
    model: str = ""
    elapsed_ms: int = 0


def _float01(value: Any, what: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise JevError("API_BAD_RESPONSE", f"{what} is not a number")
    f = float(value)
    if f != f or f < -1e-6 or f > 1 + 1e-6:
        raise JevError("API_BAD_RESPONSE", f"{what} out of range")
    return min(1.0, max(0.0, f))


def validate_response(body: Any, questions: Mapping[str, Mapping[str, Any]]) -> JevResult:
    if not isinstance(body, dict):
        raise JevError("API_BAD_RESPONSE", "body is not an object")
    answers = body.get("answers")
    if not isinstance(answers, dict):
        raise JevError("API_BAD_RESPONSE", "answers missing")
    parsed: Dict[str, ChoiceAnswer] = {}
    for qid, question in questions.items():
        ans = answers.get(qid)
        if not isinstance(ans, dict):
            raise JevError("API_BAD_RESPONSE", f"answer {qid} missing")
        if ans.get("type") != "choice":
            raise JevError("API_BAD_RESPONSE", f"answer {qid} has type {ans.get('type')!r}")
        options = list(question.get("criteria", {}).keys())
        choice = ans.get("choice")
        if not isinstance(choice, str) or choice not in options:
            raise JevError("API_BAD_RESPONSE", f"answer {qid} choice not among options")
        probs_raw = ans.get("probabilities")
        if not isinstance(probs_raw, dict):
            raise JevError("API_BAD_RESPONSE", f"answer {qid} probabilities missing")
        probs: Dict[str, float] = {}
        for opt in options:
            probs[opt] = _float01(probs_raw.get(opt, 0.0), f"{qid}.probabilities.{opt}")
        total = sum(probs.values())
        if total < 0.9 or total > 1.1:
            raise JevError("API_BAD_RESPONSE", f"answer {qid} probabilities do not sum to 1")
        confidence = _float01(ans.get("confidence"), f"{qid}.confidence")
        parsed[qid] = ChoiceAnswer(choice=choice, probabilities=probs, confidence=confidence)
    usage = body.get("usage") if isinstance(body.get("usage"), dict) else {}
    model = body.get("model") if isinstance(body.get("model"), str) else ""
    return JevResult(answers=parsed, usage=usage, model=model)


def ask(
    *,
    api_url: str,
    api_key: str,
    model: str,
    state: Any,
    questions: Mapping[str, Mapping[str, Any]],
    timeout_s: float,
    opener: Optional[Any] = None,
) -> JevResult:
    payload = json.dumps({"state": state, "model": model, "questions": dict(questions)}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        api_url,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": f"jev-hooks/{VERSION}",
        },
    )
    started = time.monotonic()
    open_fn = opener or urllib.request.urlopen
    try:
        with open_fn(req, timeout=timeout_s) as resp:
            raw = resp.read(2_000_000)
    except urllib.error.HTTPError as exc:
        status = exc.code
        if status in (401, 403):
            raise JevError("API_AUTH", f"http {status}") from exc
        if status == 429:
            raise JevError("API_RATE_LIMIT", "http 429") from exc
        if status >= 500:
            raise JevError("API_SERVER_ERROR", f"http {status}") from exc
        raise JevError("API_HTTP_ERROR", f"http {status}") from exc
    except socket.timeout as exc:
        raise JevError("API_TIMEOUT", f"{timeout_s}s") from exc
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        if isinstance(reason, socket.timeout) or "timed out" in str(reason).lower():
            raise JevError("API_TIMEOUT", f"{timeout_s}s") from exc
        raise JevError("API_NETWORK", reason.__class__.__name__) from exc
    except (OSError, ValueError) as exc:
        raise JevError("API_NETWORK", exc.__class__.__name__) from exc
    elapsed_ms = int((time.monotonic() - started) * 1000)
    try:
        body = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise JevError("API_BAD_RESPONSE", "invalid json") from exc
    result = validate_response(body, questions)
    return JevResult(answers=result.answers, usage=result.usage, model=result.model, elapsed_ms=elapsed_ms)
