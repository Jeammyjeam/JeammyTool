"""
Executor: runs each step in the task plan.
Features: caching, retry with backoff, parallel execution for independent steps.
"""

import json
import time
import anthropic
from concurrent.futures import ThreadPoolExecutor, as_completed

from . import cache
from .tools.github import fetch_repo, search_repos
from .tools.github_extras import fetch_issues, fetch_releases, fetch_contributors
from .tools.github_trending import fetch_trending
from .tools.web import fetch_url
from .tools.links import extract_links
from .tools.hackernews import fetch_top_stories
from .tools.reddit import fetch_subreddit, search_reddit
from .tools.npm import fetch_package as npm_fetch
from .tools.pypi import fetch_package as pypi_fetch
from .tools.arxiv import search_papers
from .tools.wikipedia import fetch_summary, search_wikipedia
from .tools.devto import fetch_articles as devto_fetch
from .tools.stackoverflow import search_questions
from .agents.base import run_agent

client = anthropic.Anthropic()

MAX_RETRIES = 3
BACKOFF_BASE = 2  # seconds


def _retry(fn, step_type: str):
    """Run fn with exponential backoff retry. Non-retriable errors raised immediately."""
    last_exc = None
    for attempt in range(MAX_RETRIES):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            # Don't retry on bad inputs or auth errors
            msg = str(exc).lower()
            if any(x in msg for x in ("404", "invalid", "not found", "unauthorized", "403")):
                raise
            if attempt < MAX_RETRIES - 1:
                wait = BACKOFF_BASE ** attempt
                time.sleep(wait)
    raise last_exc


def _resolve(step: dict, context: dict) -> str:
    text = step.get("input", "")
    for sid, result in context.items():
        text = text.replace(f"{sid}.result", result)
    return text


def _dispatch(step_type: str, raw_input: str, step: dict, context: dict) -> str:
    """Route step to the correct tool. All I/O goes through here."""

    # ── GitHub ───────────────────────────────────────────────────────────────
    if step_type == "github_fetch":
        return json.dumps(_retry(lambda: fetch_repo(raw_input.strip()), step_type), indent=2)
    if step_type == "github_search":
        return json.dumps(_retry(lambda: search_repos(raw_input), step_type), indent=2)
    if step_type == "github_issues":
        return json.dumps(_retry(lambda: fetch_issues(raw_input.strip()), step_type), indent=2)
    if step_type == "github_releases":
        return json.dumps(_retry(lambda: fetch_releases(raw_input.strip()), step_type), indent=2)
    if step_type == "github_contributors":
        return json.dumps(_retry(lambda: fetch_contributors(raw_input.strip()), step_type), indent=2)
    if step_type == "github_trending":
        # input format: "language:since" or just "language" or empty
        parts = raw_input.strip().split(":")
        lang = parts[0].strip() if parts else ""
        since = parts[1].strip() if len(parts) > 1 else "daily"
        return json.dumps(_retry(lambda: fetch_trending(lang, since), step_type), indent=2)

    # ── Web ──────────────────────────────────────────────────────────────────
    if step_type == "web_fetch":
        return json.dumps(_retry(lambda: fetch_url(raw_input.strip()), step_type), indent=2)
    if step_type == "extract_links":
        return json.dumps(_retry(lambda: extract_links(raw_input.strip()), step_type), indent=2)

    # ── News & Social ────────────────────────────────────────────────────────
    if step_type == "hackernews":
        return json.dumps(fetch_top_stories(), indent=2)
    if step_type == "reddit_fetch":
        return json.dumps(_retry(lambda: fetch_subreddit(raw_input.strip()), step_type), indent=2)
    if step_type == "reddit_search":
        return json.dumps(_retry(lambda: search_reddit(raw_input), step_type), indent=2)

    # ── Packages ─────────────────────────────────────────────────────────────
    if step_type == "npm_fetch":
        return json.dumps(_retry(lambda: npm_fetch(raw_input.strip()), step_type), indent=2)
    if step_type == "pypi_fetch":
        return json.dumps(_retry(lambda: pypi_fetch(raw_input.strip()), step_type), indent=2)

    # ── Research & Knowledge ─────────────────────────────────────────────────
    if step_type == "arxiv_search":
        return json.dumps(_retry(lambda: search_papers(raw_input), step_type), indent=2)
    if step_type == "wikipedia_fetch":
        return json.dumps(_retry(lambda: fetch_summary(raw_input.strip()), step_type), indent=2)
    if step_type == "wikipedia_search":
        return json.dumps(_retry(lambda: search_wikipedia(raw_input), step_type), indent=2)
    if step_type == "devto_fetch":
        return json.dumps(_retry(lambda: devto_fetch(raw_input.strip()), step_type), indent=2)
    if step_type == "stackoverflow_search":
        return json.dumps(_retry(lambda: search_questions(raw_input), step_type), indent=2)

    # ── LLM ──────────────────────────────────────────────────────────────────
    if step_type == "analyze":
        dep_ctx = "".join(
            f"\n\n[{d}]:\n{context[d]}"
            for d in step.get("depends_on", []) if d in context
        )
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2048,
            thinking={"type": "adaptive"},
            messages=[{"role": "user", "content": (
                f"Task: {step['description']}\n"
                f"Instruction: {raw_input}"
                f"{dep_ctx}"
            )}],
        )
        return next(b.text for b in response.content if b.type == "text")

    # ── Agents ───────────────────────────────────────────────────────────────
    if step_type == "agent":
        agent_name = step.get("agent", "researcher")
        dep_ctx = "".join(
            f"\n\n[Data from {d}]:\n{context[d][:3000]}"
            for d in step.get("depends_on", []) if d in context
        )
        return run_agent(agent_name, f"{raw_input}{dep_ctx}")

    return f"[unknown step type: {step_type}]"


def execute_step(step: dict, context: dict) -> str:
    """Execute one step, checking and writing cache."""
    step_type = step["type"]
    raw_input = _resolve(step, context)

    hit = cache.get(step_type, raw_input)
    if hit is not None:
        return hit

    result = _dispatch(step_type, raw_input, step, context)
    cache.put(step_type, raw_input, result)
    return result


def _execution_waves(steps: list[dict]) -> list[list[dict]]:
    """Group steps by wave — steps in the same wave have no mutual dependencies."""
    done, waves, remaining = set(), [], list(steps)
    while remaining:
        wave = [s for s in remaining if all(d in done for d in s.get("depends_on", []))]
        if not wave:
            break
        waves.append(wave)
        done.update(s["id"] for s in wave)
        for s in wave:
            remaining.remove(s)
    return waves


def execute_pipeline(steps: list[dict], on_step_done=None) -> dict:
    """
    Execute steps wave by wave. Steps within a wave run in parallel (threads).
    Calls on_step_done(step, result, from_cache) after each step.
    """
    results: dict[str, str] = {}

    for wave in _execution_waves(steps):
        if len(wave) == 1:
            # Single step — no threading overhead
            step = wave[0]
            raw_input = step.get("input", "")
            from_cache = cache.get(step["type"], raw_input) is not None
            result = execute_step(step, results)
            results[step["id"]] = result
            if on_step_done:
                on_step_done(step, result, from_cache)
        else:
            # Parallel execution for independent steps in this wave
            snapshot = dict(results)
            wave_results: dict[str, str] = {}

            with ThreadPoolExecutor(max_workers=min(len(wave), 4)) as pool:
                futures = {pool.submit(execute_step, step, snapshot): step for step in wave}
                for future in as_completed(futures):
                    step = futures[future]
                    raw_input = step.get("input", "")
                    from_cache = cache.get(step["type"], raw_input) is not None
                    try:
                        result = future.result()
                    except Exception as exc:
                        result = f"[error: {exc}]"
                    wave_results[step["id"]] = result
                    if on_step_done:
                        on_step_done(step, result, from_cache)

            results.update(wave_results)

    return results
