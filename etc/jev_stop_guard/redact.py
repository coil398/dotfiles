"""Best-effort secret scrubbing and size bounding for text sent to Jev.

This removes obvious secret shapes (well-known token prefixes, private key
blocks, ``KEY=value`` assignments with sensitive names, bearer tokens). It is
not a guarantee of complete redaction; the hook also limits *what* is sent
(see README) so that tool output bodies are mostly excluded.
"""

from __future__ import annotations

import re

REDACTED = "[REDACTED]"

_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*\Z", re.S),
    # OpenAI / Anthropic / Stripe style prefixes.
    re.compile(r"\b(?:sk|rk|pk)-(?:[A-Za-z0-9]+-)*[A-Za-z0-9_]{16,}\b"),
    # GitHub.
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    # Slack.
    re.compile(r"\bxox[abeprs]-[A-Za-z0-9-]{10,}\b"),
    # AWS access key id.
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    # Google API key.
    re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b"),
    # Notion / Figma.
    re.compile(r"\b(?:ntn|secret)_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bfigd_[A-Za-z0-9_-]{20,}\b"),
    # JWT.
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    # Authorization headers.
    re.compile(r"(?i)\b(bearer|basic)\s+[A-Za-z0-9._~+/=-]{16,}"),
    # Long hex blobs (sha256-sized or larger); 40-hex git SHAs are left alone.
    re.compile(r"\b[A-Fa-f0-9]{64,}\b"),
]

# NAME=value / NAME: value with a sensitive-looking name. Keep the name.
_ASSIGN = re.compile(
    r"(?i)\b([A-Z0-9_.-]*(?:api[_-]?key|apikey|secret|token|passw(?:or)?d|pwd|credential|private[_-]?key|auth)[A-Z0-9_.-]*)"
    r"(\s*[=:]\s*)([\"']?)([^\s\"',;]{6,})(\3)"
)


def redact(text: str) -> str:
    if not text:
        return text
    out = text
    for pattern in _PATTERNS:
        out = pattern.sub(REDACTED, out)
    out = _ASSIGN.sub(lambda m: f"{m.group(1)}{m.group(2)}{m.group(3)}{REDACTED}{m.group(5)}", out)
    return out


def clip(text: str, limit: int, marker: str = " …[truncated]… ") -> str:
    """Bound ``text`` to ``limit`` characters keeping head and tail."""
    if text is None:
        return ""
    if len(text) <= limit:
        return text
    if limit <= len(marker) + 2:
        return text[:limit]
    keep = limit - len(marker)
    head = int(keep * 0.7)
    tail = keep - head
    return text[:head] + marker + text[-tail:]


def scrub(text: str, limit: int) -> str:
    return clip(redact(text or ""), limit)
