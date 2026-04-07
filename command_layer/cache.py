"""
Simple result cache — avoids re-fetching the same data within a session.
Keys on (step_type, input). Thread-safe for Streamlit's execution model.
"""

import hashlib
import json
import threading
from pathlib import Path

_lock = threading.Lock()
_memory: dict[str, str] = {}

# Optional: persist cache to disk across runs
CACHE_FILE = Path(".jeammytool_cache.json")

# Step types that are safe to cache (deterministic, not time-sensitive)
CACHEABLE = {
    "github_fetch",
    "github_search",
    "github_issues",
    "github_releases",
    "github_contributors",
    "npm_fetch",
    "pypi_fetch",
    "arxiv_search",
    "wikipedia_fetch",
    "wikipedia_search",
    "web_fetch",
    "extract_links",
    "devto_fetch",
}

# Step types that should NOT be cached (live data)
NOT_CACHEABLE = {"hackernews", "reddit_fetch", "reddit_search", "agent", "analyze"}


def _key(step_type: str, input_str: str) -> str:
    raw = f"{step_type}::{input_str.strip().lower()}"
    return hashlib.md5(raw.encode()).hexdigest()


def _load_disk() -> None:
    """Load persisted cache from disk into memory."""
    global _memory
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE) as f:
                _memory.update(json.load(f))
        except Exception:
            pass


def _save_disk() -> None:
    """Persist in-memory cache to disk."""
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(_memory, f)
    except Exception:
        pass


# Load on import
_load_disk()


def get(step_type: str, input_str: str) -> str | None:
    if step_type in NOT_CACHEABLE:
        return None
    k = _key(step_type, input_str)
    with _lock:
        return _memory.get(k)


def set(step_type: str, input_str: str, result: str) -> None:
    if step_type not in CACHEABLE:
        return
    k = _key(step_type, input_str)
    with _lock:
        _memory[k] = result
        _save_disk()


def clear() -> None:
    with _lock:
        _memory.clear()
        if CACHE_FILE.exists():
            CACHE_FILE.unlink()


def stats() -> dict:
    with _lock:
        return {"entries": len(_memory), "file": str(CACHE_FILE)}
