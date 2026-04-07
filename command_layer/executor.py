"""
Executor: runs each step in the task plan.
Dispatches to the right tool/agent based on step type.
Results are cached where safe to avoid redundant API calls.
"""

import json
import anthropic
from . import cache
from .tools.github import fetch_repo, search_repos
from .tools.github_extras import fetch_issues, fetch_releases, fetch_contributors
from .tools.web import fetch_url
from .tools.links import extract_links
from .tools.hackernews import fetch_top_stories
from .tools.reddit import fetch_subreddit, search_reddit
from .tools.npm import fetch_package as npm_fetch_package
from .tools.pypi import fetch_package as pypi_fetch_package
from .tools.arxiv import search_papers
from .tools.wikipedia import fetch_summary, search_wikipedia
from .tools.devto import fetch_articles as devto_fetch_articles, search_articles as devto_search_articles
from .agents.base import run_agent

client = anthropic.Anthropic()


def _resolve_input(step: dict, context: dict) -> str:
    """Replace step_N.result placeholders with actual results."""
    text = step.get("input", "")
    for step_id, result in context.items():
        text = text.replace(f"{step_id}.result", result)
    return text


def execute_step(step: dict, context: dict) -> str:
    """Execute a single step and return its result as a string."""
    step_type = step["type"]
    raw_input = _resolve_input(step, context)

    # Cache check
    cached = cache.get(step_type, raw_input)
    if cached is not None:
        return cached

    result = _dispatch(step_type, raw_input, step, context)

    # Cache write
    cache.set(step_type, raw_input, result)
    return result


def _dispatch(step_type: str, raw_input: str, step: dict, context: dict) -> str:
    """Route step type to the correct tool/agent."""

    # ── GitHub ──────────────────────────────────────────────────────────────
    if step_type == "github_fetch":
        return json.dumps(fetch_repo(raw_input.strip()), indent=2)

    elif step_type == "github_search":
        return json.dumps(search_repos(raw_input), indent=2)

    elif step_type == "github_issues":
        return json.dumps(fetch_issues(raw_input.strip()), indent=2)

    elif step_type == "github_releases":
        return json.dumps(fetch_releases(raw_input.strip()), indent=2)

    elif step_type == "github_contributors":
        return json.dumps(fetch_contributors(raw_input.strip()), indent=2)

    # ── Web ─────────────────────────────────────────────────────────────────
    elif step_type == "web_fetch":
        return json.dumps(fetch_url(raw_input.strip()), indent=2)

    elif step_type == "extract_links":
        return json.dumps(extract_links(raw_input.strip()), indent=2)

    # ── News & Social ────────────────────────────────────────────────────────
    elif step_type == "hackernews":
        return json.dumps(fetch_top_stories(), indent=2)

    elif step_type == "reddit_fetch":
        return json.dumps(fetch_subreddit(raw_input.strip()), indent=2)

    elif step_type == "reddit_search":
        return json.dumps(search_reddit(raw_input), indent=2)

    # ── Packages ─────────────────────────────────────────────────────────────
    elif step_type == "npm_fetch":
        return json.dumps(npm_fetch_package(raw_input.strip()), indent=2)

    elif step_type == "pypi_fetch":
        return json.dumps(pypi_fetch_package(raw_input.strip()), indent=2)

    # ── Research & Knowledge ─────────────────────────────────────────────────
    elif step_type == "arxiv_search":
        return json.dumps(search_papers(raw_input), indent=2)

    elif step_type == "wikipedia_fetch":
        return json.dumps(fetch_summary(raw_input.strip()), indent=2)

    elif step_type == "wikipedia_search":
        return json.dumps(search_wikipedia(raw_input), indent=2)

    elif step_type == "devto_fetch":
        return json.dumps(devto_fetch_articles(raw_input.strip()), indent=2)

    elif step_type == "devto_search":
        return json.dumps(devto_search_articles(raw_input), indent=2)

    # ── LLM ──────────────────────────────────────────────────────────────────
    elif step_type == "analyze":
        dep_context = ""
        for dep_id in step.get("depends_on", []):
            if dep_id in context:
                dep_context += f"\n\n[{dep_id} result]:\n{context[dep_id]}"

        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2048,
            thinking={"type": "adaptive"},
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Task: {step['description']}\n"
                        f"Instruction: {raw_input}"
                        f"{dep_context}"
                    ),
                }
            ],
        )
        return next(b.text for b in response.content if b.type == "text")

    # ── Agents ───────────────────────────────────────────────────────────────
    elif step_type == "agent":
        agent_name = step.get("agent", "researcher")
        dep_context = ""
        for dep_id in step.get("depends_on", []):
            if dep_id in context:
                dep_context += f"\n\n[Data from {dep_id}]:\n{context[dep_id][:3000]}"
        return run_agent(agent_name, f"{raw_input}{dep_context}")

    return f"[unknown step type: {step_type}]"


def execute_pipeline(steps: list[dict], on_step_done=None) -> dict:
    """
    Execute all steps in dependency order.
    Calls on_step_done(step, result, from_cache) after each step if provided.
    """
    results: dict[str, str] = {}
    executed: set[str] = set()
    remaining = list(steps)

    while remaining:
        progress = False
        for step in list(remaining):
            if all(dep in executed for dep in step.get("depends_on", [])):
                step_id = step["id"]
                raw_input = step.get("input", "")
                from_cache = cache.get(step["type"], raw_input) is not None
                result = execute_step(step, results)
                results[step_id] = result
                executed.add(step_id)
                remaining.remove(step)
                if on_step_done:
                    on_step_done(step, result, from_cache)
                progress = True
        if not progress:
            break

    return results
