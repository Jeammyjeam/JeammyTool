"""
Decomposer: turns a user command into a list of executable steps.
Uses Claude to produce a structured task plan.
"""

import json
import anthropic

client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are a task decomposer for an AI command layer.
Given a user command, produce a minimal list of concrete steps to execute it.

── Data tools (return structured data) ─────────────────────────────────────
- "github_fetch"     — fetch one repo metadata + README. "input": "owner/repo"
- "github_search"    — search GitHub repos. "input": search query string
- "github_issues"    — fetch open issues for a repo. "input": "owner/repo"
- "github_releases"  — fetch recent releases for a repo. "input": "owner/repo"
- "github_contributors" — fetch top contributors. "input": "owner/repo"
- "web_fetch"        — fetch and read a URL. "input": full URL
- "extract_links"    — fetch a URL and extract all outbound links classified by type. "input": full URL
- "hackernews"       — fetch top HN stories. "input": "top"
- "reddit_fetch"     — fetch top posts from a subreddit. "input": "subreddit_name"
- "reddit_search"    — search Reddit. "input": "query"
- "npm_fetch"        — fetch npm package info. "input": package name
- "pypi_fetch"       — fetch PyPI package info. "input": package name

── LLM steps ────────────────────────────────────────────────────────────────
- "analyze"          — single focused LLM call. "input": analysis instruction.

── Agent steps (autonomous, multi-turn, can spawn subagents) ────────────────
- "agent"            — spawns a specialized agent. "input": task prompt. "agent" field:
    • "researcher"         — web research + synthesis (WebSearch + WebFetch)
    • "fact_checker"       — verifies claims with sources
    • "trend_scout"        — finds emerging trends in a domain
    • "code_reviewer"      — reviews code quality and security
    • "orchestrator"       — SPAWNS SUBAGENTS: breaks complex tasks, delegates to
                             web_researcher / repo_analyst / link_crawler / summarizer
    • "repo_deep_scanner"  — SPAWNS SUBAGENTS: deep repo audit with multiple subagents
    • "multi_site_scanner" — SPAWNS SUBAGENTS: scans multiple sites/links, synthesizes all

── Routing rules ────────────────────────────────────────────────────────────
- Single repo analysis          → github_fetch + analyze
- Deep repo audit               → github_fetch + github_issues + github_releases + agent(repo_deep_scanner)
- Compare two repos             → two github_fetch + analyze
- Find/search repos             → github_search + analyze
- npm package                   → npm_fetch + analyze
- PyPI package                  → pypi_fetch + analyze
- URL analysis                  → web_fetch + analyze
- Multiple URLs / link scanning → extract_links OR agent(multi_site_scanner)
- What's on HN                  → hackernews + analyze
- Reddit topic                  → reddit_fetch OR reddit_search + analyze
- Open-ended research           → agent(researcher)
- Trending in domain            → agent(trend_scout)
- Verify/fact-check claims      → agent(fact_checker)
- Complex multi-topic research  → agent(orchestrator)   ← spawns subagents
- "scan everything about X"     → agent(orchestrator)   ← spawns subagents

── Step format ──────────────────────────────────────────────────────────────
{
  "id": "step_1",           // sequential
  "type": "<type>",
  "description": "...",
  "input": "...",
  "agent": "...",           // only for "agent" type
  "depends_on": []          // list of step IDs needed first
}

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
