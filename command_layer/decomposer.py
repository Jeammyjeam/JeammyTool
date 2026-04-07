"""
Decomposer: turns a user command into a list of executable steps.
Uses Claude to produce a structured task plan.
"""

import json
import anthropic

client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are a task decomposer for an AI command layer.
Given a user command, produce a minimal list of concrete steps to execute it.

Available step types:
- "github_fetch"    — fetches one GitHub repo metadata + README. "input" must be "owner/repo".
- "github_search"   — searches GitHub repos. "input" is the search query (e.g. "python scraping sort:stars").
- "web_fetch"       — fetches and reads any URL. "input" must be a full URL (https://...).
- "hackernews"      — fetches current top Hacker News stories. "input" is ignored (use "top").
- "npm_fetch"       — fetches npm package metadata. "input" is the package name.
- "pypi_fetch"      — fetches PyPI package metadata. "input" is the package name.
- "analyze"         — single LLM call for analysis/synthesis. "input" is the instruction.
- "agent"           — spawns a specialized autonomous agent for complex multi-step tasks.
                      "input" is the detailed task prompt. "agent" field selects the agent:
                        • "researcher"    — web research + synthesis
                        • "fact_checker"  — verifies claims with sources
                        • "trend_scout"   — finds emerging trends in a domain
                        • "code_reviewer" — reviews repo code quality and security

Routing rules:
- Single repo analysis → github_fetch + analyze
- Compare two repos → two github_fetch + analyze
- Find/search/discover repos → github_search + analyze
- Evaluate npm package → npm_fetch + analyze
- Evaluate PyPI package → pypi_fetch + analyze
- URL/webpage analysis → web_fetch + analyze
- "What's on HN / Hacker News" → hackernews + analyze
- Open-ended research question → agent(researcher)
- "What's trending in X" → agent(trend_scout)
- Fact-checking / verify claims → agent(fact_checker)
- Deep code/repo audit → github_fetch + agent(code_reviewer)
- Use "analyze" for simple synthesis; use "agent" when multi-step autonomous research is needed.

Step format:
- "id": "step_1", "step_2", etc. (sequential)
- "type": one of the types above
- "description": what this step does
- "input": the input string
- "agent": (only for "agent" type) the agent name
- "depends_on": list of step IDs this needs first (empty array if none)

Output ONLY a valid JSON array. No markdown, no explanation."""


def decompose(command: str) -> list[dict]:
    """Break a command into an ordered list of executable steps."""
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Command: {command}"}],
    )

    text = next(b.text for b in response.content if b.type == "text")
    steps = json.loads(text)
    return steps
