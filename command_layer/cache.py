"""
Session + disk cache — avoids redundant API calls.
Caches deterministic tools; skips live/agent data.
"""

import hashlib
import json
import threading
from pathlib import Path

_lock = threading.Lock()
_memory: dict[str, str] = {}
CACHE_FILE = Path(".jeammytool_cache.json")

# Deterministic tools safe to cache
CACHEABLE = {
    "github_fetch", "github_search", "github_issues", "github_releases",
    "github_contributors", "npm_fetch", "pypi_fetch", "arxiv_search",
    "wikipedia_fetch", "wikipedia_search", "web_fetch", "extract_links",
    "devto_fetch", "stackoverflow_search", "github_trending",
}

# Live/non-deterministic — never cache
NOT_CACHEABLE = {"hackernews", "reddit_fetch", "reddit_search", "agent", "analyze"}


def _key(step_type: str, inp: str) -> str:
    raw = f"{step_type}::{inp.strip().lower()}"
    return hashlib.md5(raw.encode()).hexdigest()


def _load() -> None:
    global _memory
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE) as f:
                _memory.update(json.load(f))
        except Exception:
            pass


def _save() -> None:
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(_memory, f)
    except Exception:
        pass


_load()


def get(step_type: str, inp: str) -> str | None:
    if step_type in NOT_CACHEABLE:
        return None
    with _lock:
        return _memory.get(_key(step_type, inp))


def put(step_type: str, inp: str, result: str) -> None:
    if step_type not in CACHEABLE:
        return
    with _lock:
        _memory[_key(step_type, inp)] = result
        _save()


def clear() -> None:
    with _lock:
        _memory.clear()
        if CACHE_FILE.exists():
            CACHE_FILE.unlink()


def stats() -> dict:
    with _lock:
        return {"entries": len(_memory)}
