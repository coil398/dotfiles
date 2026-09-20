"""Configuration and API-key resolution.

Precedence: built-in defaults < config file < environment variables.
The API key is never part of the config file; it comes from the
``TYPESAFE_API_KEY`` environment variable or an ``export TYPESAFE_API_KEY=...``
line in ``~/.zsh_secret``.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

API_KEY_ENV = "TYPESAFE_API_KEY"
SECRET_FILE_NAME = ".zsh_secret"
CONFIG_PATH_ENV = "JEV_STOP_GUARD_CONFIG"
DEFAULT_CONFIG_PATH = "~/.config/jev-stop-guard/config.json"

MODES = ("on", "observe", "off")


@dataclass(frozen=True)
class Config:
    mode: str = "on"
    model: str = "jev-latest"
    api_url: str = "https://api.typesafe.ai/v1/systemone"
    # Provisional default; see README "しきい値" for how to evaluate it.
    confidence_threshold: float = 0.6
    api_timeout_s: float = 3.0
    total_timeout_s: float = 5.0
    max_continuations: int = 2
    max_transcript_bytes: int = 1_500_000
    state_dir: str = "~/.local/state/jev-stop-guard"
    log_max_bytes: int = 1_000_000
    warnings: Tuple[str, ...] = field(default_factory=tuple)
    source_file: Optional[str] = None

    def state_path(self) -> Path:
        return Path(os.path.expanduser(self.state_dir))


ENV_KEYS = {
    "mode": "JEV_STOP_GUARD_MODE",
    "model": "JEV_STOP_GUARD_MODEL",
    "api_url": "JEV_STOP_GUARD_API_URL",
    "confidence_threshold": "JEV_STOP_GUARD_CONFIDENCE_THRESHOLD",
    "api_timeout_s": "JEV_STOP_GUARD_API_TIMEOUT_S",
    "total_timeout_s": "JEV_STOP_GUARD_TOTAL_TIMEOUT_S",
    "max_continuations": "JEV_STOP_GUARD_MAX_CONTINUATIONS",
    "max_transcript_bytes": "JEV_STOP_GUARD_MAX_TRANSCRIPT_BYTES",
    "state_dir": "JEV_STOP_GUARD_STATE_DIR",
    "log_max_bytes": "JEV_STOP_GUARD_LOG_MAX_BYTES",
}

_FIELD_TYPES = {
    "mode": str,
    "model": str,
    "api_url": str,
    "confidence_threshold": float,
    "api_timeout_s": float,
    "total_timeout_s": float,
    "max_continuations": int,
    "max_transcript_bytes": int,
    "state_dir": str,
    "log_max_bytes": int,
}


def _coerce(name: str, raw: Any) -> Any:
    typ = _FIELD_TYPES[name]
    if typ is str:
        if not isinstance(raw, str):
            raise ValueError(f"{name} must be a string")
        return raw.strip()
    if typ is float:
        if isinstance(raw, bool):
            raise ValueError(f"{name} must be a number")
        return float(raw)
    if typ is int:
        if isinstance(raw, bool):
            raise ValueError(f"{name} must be an integer")
        if isinstance(raw, float) and not raw.is_integer():
            raise ValueError(f"{name} must be an integer")
        return int(raw)
    raise ValueError(name)


def _validate(values: Dict[str, Any], warnings: List[str]) -> Dict[str, Any]:
    defaults = Config()
    out = dict(values)
    if out.get("mode") not in MODES:
        warnings.append(f"invalid mode {out.get('mode')!r}; using {defaults.mode!r}")
        out["mode"] = defaults.mode
    if not out.get("model"):
        warnings.append("empty model; using default")
        out["model"] = defaults.model
    if not str(out.get("api_url", "")).startswith(("https://", "http://")):
        warnings.append("api_url must be an http(s) URL; using default")
        out["api_url"] = defaults.api_url
    if not (0.0 <= out.get("confidence_threshold", -1) <= 1.0):
        warnings.append("confidence_threshold must be within [0,1]; using default")
        out["confidence_threshold"] = defaults.confidence_threshold
    for key, lo in (("api_timeout_s", 0.1), ("total_timeout_s", 0.5)):
        if out.get(key, 0) < lo:
            warnings.append(f"{key} too small; using default")
            out[key] = getattr(defaults, key)
    if out["api_timeout_s"] > out["total_timeout_s"]:
        warnings.append("api_timeout_s exceeds total_timeout_s; clamping")
        out["api_timeout_s"] = out["total_timeout_s"]
    if out.get("max_continuations", -1) < 0:
        warnings.append("max_continuations must be >= 0; using default")
        out["max_continuations"] = defaults.max_continuations
    if out.get("max_transcript_bytes", 0) < 10_000:
        warnings.append("max_transcript_bytes too small; using default")
        out["max_transcript_bytes"] = defaults.max_transcript_bytes
    if out.get("log_max_bytes", 0) < 10_000:
        warnings.append("log_max_bytes too small; using default")
        out["log_max_bytes"] = defaults.log_max_bytes
    if not out.get("state_dir"):
        warnings.append("empty state_dir; using default")
        out["state_dir"] = defaults.state_dir
    return out


def load_config(environ: Optional[Dict[str, str]] = None) -> Config:
    env = os.environ if environ is None else environ
    warnings: List[str] = []
    defaults = Config()
    values: Dict[str, Any] = {name: getattr(defaults, name) for name in _FIELD_TYPES}

    path_str = env.get(CONFIG_PATH_ENV) or DEFAULT_CONFIG_PATH
    path = Path(os.path.expanduser(path_str))
    source_file: Optional[str] = None
    if path.is_file():
        source_file = str(path)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("config root must be an object")
            for key, raw in data.items():
                if key not in _FIELD_TYPES:
                    warnings.append(f"unknown config key {key!r} ignored")
                    continue
                try:
                    values[key] = _coerce(key, raw)
                except (TypeError, ValueError) as exc:
                    warnings.append(f"config file: {exc}")
        except (OSError, ValueError) as exc:
            warnings.append(f"config file unreadable ({exc}); using defaults")

    for key, env_name in ENV_KEYS.items():
        raw = env.get(env_name)
        if raw is None or raw == "":
            continue
        try:
            values[key] = _coerce(key, raw)
        except (TypeError, ValueError) as exc:
            warnings.append(f"env {env_name}: {exc}")

    values = _validate(values, warnings)
    return replace(Config(**values), warnings=tuple(warnings), source_file=source_file)


def secret_file_path(environ: Optional[Dict[str, str]] = None) -> Path:
    env = os.environ if environ is None else environ
    home = env.get("HOME") or str(Path.home())
    return Path(home) / SECRET_FILE_NAME


def resolve_api_key(environ: Optional[Dict[str, str]] = None) -> Tuple[Optional[str], str]:
    """Return ``(key, source)``; ``source`` is ``env``, ``secret_file`` or ``missing``."""
    env = os.environ if environ is None else environ
    value = (env.get(API_KEY_ENV) or "").strip()
    if value:
        return value, "env"
    path = secret_file_path(env)
    try:
        if path.is_file():
            for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
                line = raw.strip()
                if line.startswith("export "):
                    line = line[len("export ") :].strip()
                prefix = API_KEY_ENV + "="
                if line.startswith(prefix):
                    value = line[len(prefix) :].strip().strip("'\"")
                    if value:
                        return value, "secret_file"
    except OSError:
        pass
    return None, "missing"
