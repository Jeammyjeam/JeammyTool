"""
Decomposer: uses Claude to break a command into typed executable steps.
"""

import json
import anthropic

client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are a task decomposer for an AI command layer.
Given a user command, produce a minimal list of concrete steps to execute it.

── Data tools ───────────────────────────────────────────────────────────────
- "github_fetch"        — one repo metadata + README. input: "owner/repo"
- "github_search"       — search repos. input: query string
- "github_issues"       — repo issues. input: "owner/repo"
- "github_releases"     — repo releases. input: "owner/repo"
- "github_contributors" — top contributors. input: "owner/repo"
- "github_trending"     — trending repos. input: "language:since" (e.g. "python:daily") or ""
- "web_fetch"           — fetch a URL. input: full URL
- "extract_links"       — all outbound links from a URL. input: full URL
- "hackernews"          — top HN stories. input: "top"
- "reddit_fetch"        — subreddit posts. input: subreddit name
- "reddit_search"       — search Reddit. input: query
- "npm_fetch"           — npm package. input: package name
- "pypi_fetch"          — PyPI package. input: package name
- "arxiv_search"        — research papers. input: search query
- "wikipedia_fetch"     — Wikipedia article. input: article title
- "wikipedia_search"    — search Wikipedia. input: query
- "devto_fetch"         — DEV.to articles by tag. input: tag
- "stackoverflow_search"— Stack Overflow questions. input: query

── LLM ──────────────────────────────────────────────────────────────────────
- "analyze"             — single LLM synthesis call. input: instruction.

── Agents (autonomous, multi-turn) ──────────────────────────────────────────
- "agent" — spawns a specialized agent. include "agent" field:
  • "researcher"         — web research + synthesis
  • "fact_checker"       — verifies claims with sources
  • "trend_scout"        — finds emerging trends
  • "code_reviewer"      — code quality + security review
  • "advisor"            — ranked actionable recommendations
  • "debate"             — argues both sides + verdict
  • "orchestrator"       — SPAWNS SUBAGENTS for complex multi-topic tasks
  • "repo_deep_scanner"  — SPAWNS SUBAGENTS for deep repo audit
  • "multi_site_scanner" — SPAWNS SUBAGENTS to scan multiple URLs

── Routing ──────────────────────────────────────────────────────────────────
Single repo            → github_fetch + analyze
Deep repo audit        → github_fetch + github_issues + github_releases + agent(repo_deep_scanner)
Compare two repos      → two github_fetch + analyze
Find repos             → github_search + analyze
Trending repos         → github_trending + analyze
npm package            → npm_fetch + analyze
PyPI package           → pypi_fetch + analyze
URL                    → web_fetch + analyze
Multiple URLs          → extract_links OR agent(multi_site_scanner)
HN today               → hackernews + analyze
Reddit topic           → reddit_fetch OR reddit_search + analyze
Research papers        → arxiv_search + analyze
Explain/what is X      → wikipedia_fetch OR wikipedia_search + analyze
Dev articles           → devto_fetch + analyze
Stack Overflow Q       → stackoverflow_search + analyze
What's trending in X   → github_trending + agent(trend_scout)
Open-ended research    → agent(researcher)
Fact-check claims      → agent(fact_checker)
Recommend / advise     → relevant data steps + agent(advisor)
Both sides / debate    → agent(debate)
Complex multi-topic    → agent(orchestrator)

── Step format ──────────────────────────────────────────────────────────────
{"id":"step_1","type":"...","description":"...","input":"...","agent":"...","depends_on":[]}

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
    return json.loads(text)
