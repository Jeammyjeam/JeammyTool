"""
Executor: runs each step in the task plan.
Dispatches to GitHub API or Claude based on step type.
"""

import json
import anthropic
from .tools.github import fetch_repo, search_repos
from .tools.web import fetch_url
from .tools.hackernews import fetch_top_stories
from .tools.npm import fetch_package as npm_fetch_package
from .tools.pypi import fetch_package as pypi_fetch_package
from .agents.base import run_agent

client = anthropic.Anthropic()


def _resolve_input(step: dict, context: dict) -> str:
    """Replace 'step_N.result' placeholders in input with actual results."""
    text = step.get("input", "")
    for step_id, result in context.items():
        text = text.replace(f"{step_id}.result", result)
    return text


def execute_step(step: dict, context: dict) -> str:
    """Execute a single step and return its result as a string."""
    step_type = step["type"]

    if step_type == "github_fetch":
        repo_path = step["input"].strip()
        repo_data = fetch_repo(repo_path)
        return json.dumps(repo_data, indent=2)

    elif step_type == "github_search":
        query = _resolve_input(step, context)
        results = search_repos(query)
        return json.dumps(results, indent=2)

    elif step_type == "web_fetch":
        url = _resolve_input(step, context).strip()
        page_data = fetch_url(url)
        return json.dumps(page_data, indent=2)

    elif step_type == "hackernews":
        stories = fetch_top_stories()
        return json.dumps(stories, indent=2)

    elif step_type == "npm_fetch":
        package = _resolve_input(step, context).strip()
        data = npm_fetch_package(package)
        return json.dumps(data, indent=2)

    elif step_type == "pypi_fetch":
        package = _resolve_input(step, context).strip()
        data = pypi_fetch_package(package)
        return json.dumps(data, indent=2)

    elif step_type == "agent":
        agent_name = step.get("agent", "researcher")
        instruction = _resolve_input(step, context)
        dep_context = ""
        for dep_id in step.get("depends_on", []):
            if dep_id in context:
                dep_context += f"\n\n[Data from {dep_id}]:\n{context[dep_id][:3000]}"
        full_prompt = f"{instruction}{dep_context}"
        return run_agent(agent_name, full_prompt)

    elif step_type == "analyze":
        # Build context from dependency results
        dep_context = ""
        for dep_id in step.get("depends_on", []):
            if dep_id in context:
                dep_context += f"\n\n[{dep_id} result]:\n{context[dep_id]}"

        instruction = _resolve_input(step, context)

        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2048,
            thinking={"type": "adaptive"},
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Task: {step['description']}\n"
                        f"Instruction: {instruction}"
                        f"{dep_context}"
                    ),
                }
            ],
        )
        return next(b.text for b in response.content if b.type == "text")

    return f"[unknown step type: {step_type}]"


def execute_pipeline(steps: list[dict], on_step_done=None) -> dict:
    """
    Execute all steps in dependency order.
    Calls on_step_done(step, result) after each step if provided.
    Returns dict of step_id -> result.
    """
    results: dict[str, str] = {}
    executed: set[str] = set()
    remaining = list(steps)

    while remaining:
        progress = False
        for step in list(remaining):
            deps = step.get("depends_on", [])
            if all(dep in executed for dep in deps):
                step_id = step["id"]
                result = execute_step(step, results)
                results[step_id] = result
                executed.add(step_id)
                remaining.remove(step)
                if on_step_done:
                    on_step_done(step, result)
                progress = True
        if not progress:
            # Unresolvable dependency — skip remaining steps
            break

    return results
