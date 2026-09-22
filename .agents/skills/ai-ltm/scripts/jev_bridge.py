#!/usr/bin/env python3
"""Optional adapter from ai-ltm to the independently runnable jev-hooks package."""

from __future__ import annotations

import argparse
from collections import Counter
import importlib
import json
import math
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Mapping, Optional


MAX_ANNOTATED_CANDIDATES = 5
MAX_QUERY_CHARS = 1200
MAX_SUMMARY_CHARS = 1200
MAX_CONTEXT_CHARS = 1200
MAX_TAGS_CHARS = 300


def _env(environ: Optional[Dict[str, str]]) -> Dict[str, str]:
    return os.environ if environ is None else environ


def _has_api_key(environ: Optional[Dict[str, str]]) -> bool:
    value = _env(environ).get("TYPESAFE_API_KEY")
    return isinstance(value, str) and bool(value.strip())


def _hooks_source(environ: Optional[Dict[str, str]]) -> Optional[Path]:
    env = _env(environ)
    configured = env.get("JEV_HOOKS_ROOT")
    if configured:
        root = Path(configured).expanduser().resolve()
    else:
        root = Path(__file__).resolve().parents[4] / "jev-hooks"
    if (root / "src" / "jev_hooks" / "memory.py").is_file():
        return root / "src"
    if (root / "jev_hooks" / "memory.py").is_file():
        return root
    return None


def _load_memory(environ: Optional[Dict[str, str]]) -> Any:
    """Return the optional core module; never import it without an API key."""
    if not _has_api_key(environ):
        return None
    source = _hooks_source(environ)
    if source is None:
        return None
    source_text = str(source)
    if source_text not in sys.path:
        sys.path.insert(0, source_text)
    try:
        module = importlib.import_module("jev_hooks.memory")
    except Exception:  # Optional package import is an isolated fallback boundary.
        return None
    module_path = getattr(module, "__file__", None)
    if not module_path:
        return None
    try:
        Path(module_path).resolve().relative_to(source.resolve())
    except ValueError:
        # A different installed package with the same name is not this bridge.
        return None
    return module


def _report_skip(reason: str) -> None:
    print(f"ai-ltm Jev bridge skipped: {reason}", file=sys.stderr)


def _same_items(before: List[Any], after: Any) -> bool:
    if not isinstance(after, list) or len(before) != len(after):
        return False
    try:
        key = lambda value: json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return Counter(map(key, before)) == Counter(map(key, after))
    except (TypeError, ValueError):
        return False


def _clip_text(value: Any, limit: int) -> str:
    if not isinstance(value, str):
        return ""
    return value if len(value) <= limit else value[: max(0, limit - 1)] + "…"


def _annotation_input(item: Mapping[str, Any]) -> Dict[str, Any]:
    score = item.get("score")
    if score is None:
        score = item.get("combined_score", item.get("vector_score", item.get("fts_score")))
    try:
        score = float(score) if not isinstance(score, bool) else math.nan
    except (TypeError, ValueError, OverflowError):
        score = math.nan
    if not math.isfinite(score):
        score = None
    return {
        "summary": _clip_text(item.get("summary"), MAX_SUMMARY_CHARS),
        "context": _clip_text(item.get("context"), MAX_CONTEXT_CHARS),
        "tags": _clip_text(item.get("tags"), MAX_TAGS_CHARS),
        "score": score,
    }


def _valid_annotations(before: List[Dict[str, Any]], after: Any) -> bool:
    if not isinstance(after, list) or len(before) != len(after):
        return False
    for original, annotated in zip(before, after):
        if not isinstance(annotated, Mapping):
            return False
        if set(annotated) != set(original) | {"jev_annotation"}:
            return False
        if any(annotated.get(key) != value for key, value in original.items()):
            return False
        if not isinstance(annotated.get("jev_annotation"), Mapping):
            return False
    return True


def rerank(
    query: str,
    results: List[Dict[str, Any]],
    *,
    environ: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    """Optionally reorder search results, preserving every result and field."""
    if not isinstance(results, list) or len(results) < 2:
        return results
    if not _has_api_key(environ):
        _report_skip("NO_API_KEY")
        return results
    module = _load_memory(environ)
    if module is None:
        _report_skip("JEV_HOOKS_UNAVAILABLE")
        return results
    try:
        ranked = module.rerank(query, results, environ=environ)
    except Exception as exc:  # The optional boundary must preserve base search.
        _report_skip(f"JEV_ERROR:{type(exc).__name__}")
        return results
    if not _same_items(results, ranked):
        _report_skip("INVALID_RERANK_RESULT")
        return results
    return ranked


def annotate(
    query: str,
    results: List[Dict[str, Any]],
    *,
    environ: Optional[Dict[str, str]] = None,
    timeout_s: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """Optionally add advisory annotations without changing candidates or order."""
    if not isinstance(results, list) or not results:
        return results
    if not _has_api_key(environ):
        _report_skip("NO_API_KEY")
        return results
    module = _load_memory(environ)
    if module is None:
        _report_skip("JEV_HOOKS_UNAVAILABLE")
        return results

    count = min(MAX_ANNOTATED_CANDIDATES, len(results))
    candidates = results[:count]
    if any(not isinstance(item, Mapping) or "jev_annotation" in item for item in candidates):
        return results
    safe_candidates = [_annotation_input(item) for item in candidates]
    try:
        annotated = module.annotate(
            _clip_text(query, MAX_QUERY_CHARS),
            safe_candidates,
            environ=environ,
            timeout_s=timeout_s,
        )
    except Exception as exc:  # An optional Jev call must not affect recall results.
        _report_skip(f"JEV_ERROR:{type(exc).__name__}")
        return results
    if _same_items(safe_candidates, annotated):
        return results
    if not _valid_annotations(safe_candidates, annotated):
        _report_skip("INVALID_ANNOTATION_RESULT")
        return results

    merged = []
    for original, labeled in zip(candidates, annotated):
        copy = dict(original)
        copy["jev_annotation"] = dict(labeled["jev_annotation"])
        merged.append(copy)
    return merged + results[count:]


def classify_record(
    summary: str,
    context: str = "",
    *,
    db_path: Optional[str | Path] = None,
    environ: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Optionally classify a proposed record; never write it to memory."""
    if not _has_api_key(environ):
        return {
            "status": "skipped",
            "reason": "NO_API_KEY",
            "destination": "unclear",
            "duplicate_candidates": [],
            "contradiction_candidates": [],
        }
    module = _load_memory(environ)
    if module is None:
        return {
            "status": "skipped",
            "reason": "JEV_HOOKS_UNAVAILABLE",
            "destination": "unclear",
            "duplicate_candidates": [],
            "contradiction_candidates": [],
        }
    try:
        result = module.classify_record(summary, context, db_path=db_path, environ=environ)
    except Exception as exc:  # The optional boundary must not break capture.
        _report_skip(f"JEV_ERROR:{type(exc).__name__}")
        return {
            "status": "skipped",
            "reason": f"JEV_ERROR:{type(exc).__name__}",
            "destination": "unclear",
            "duplicate_candidates": [],
            "contradiction_candidates": [],
        }
    return result if isinstance(result, dict) else {
        "status": "skipped",
        "reason": "INVALID_CLASSIFICATION_RESULT",
        "destination": "unclear",
        "duplicate_candidates": [],
        "contradiction_candidates": [],
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("rerank", "memory-classify"))
    args = parser.parse_args(argv)
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    if args.command == "rerank":
        results = payload.get("results")
        if not isinstance(results, list):
            results = []
        output = rerank(str(payload.get("query") or ""), results)
    else:
        output = classify_record(
            str(payload.get("summary") or ""),
            str(payload.get("context") or ""),
            db_path=payload.get("db_path"),
        )
    sys.stdout.write(json.dumps(output, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
