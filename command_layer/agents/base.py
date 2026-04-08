"""
Agent runner — spawns Claude agents via the Agent SDK.
Supports both single agents and orchestrators that spawn subagents.
"""

import anyio
from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AgentDefinition,
    ResultMessage,
)

# ── Subagent definitions (reused inside orchestrators) ─────────────────────

_SUBAGENTS = {
    "web_researcher": AgentDefinition(
        description="Searches the web and reads pages to research a specific subtopic.",
        prompt="You are a focused web researcher. Search thoroughly for the given subtopic and return key findings with sources.",
        tools=["WebSearch", "WebFetch"],
    ),
    "repo_analyst": AgentDefinition(
        description="Analyzes a GitHub repository's quality, activity, and purpose.",
        prompt="You are a code analyst. Given a GitHub repo URL or name, fetch its data, README, and recent activity. Assess quality and usefulness.",
        tools=["WebSearch", "WebFetch"],
    ),
    "link_crawler": AgentDefinition(
        description="Fetches a URL and extracts useful links and content.",
        prompt="Fetch the given URL, read its content, extract important links, and summarize what you find.",
        tools=["WebFetch"],
    ),
    "summarizer": AgentDefinition(
        description="Condenses long content into a structured summary.",
        prompt="You are a summarizer. Take the provided content and return a clear, structured, bullet-pointed summary.",
        tools=[],
    ),
}

# ── Single-agent registry ───────────────────────────────────────────────────

_AGENTS: dict[str, dict] = {
    "researcher": {
        "description": "Researches topics via web search and reading pages",
        "system_prompt": (
            "You are a research analyst. Search the web thoroughly, read sources, "
            "and synthesize findings into a clear structured report with citations."
        ),
        "allowed_tools": ["WebSearch", "WebFetch"],
        "max_turns": 10,
        "subagents": None,
    },
    "fact_checker": {
        "description": "Verifies claims and finds supporting or contradicting evidence",
        "system_prompt": (
            "You are a fact-checker. For each claim, search for evidence. "
            "Return verdict (Confirmed / Unconfirmed / False) with sources."
        ),
        "allowed_tools": ["WebSearch", "WebFetch"],
        "max_turns": 8,
        "subagents": None,
    },
    "trend_scout": {
        "description": "Finds what is trending and emerging in a domain",
        "system_prompt": (
            "You are a trend analyst. Search for the latest news, repos, discussions, "
            "and releases in the given domain. Identify patterns and emerging tools. "
            "Return a structured trends report."
        ),
        "allowed_tools": ["WebSearch", "WebFetch"],
        "max_turns": 10,
        "subagents": None,
    },
    "code_reviewer": {
        "description": "Reviews code quality, security, and architecture",
        "system_prompt": (
            "You are a senior code reviewer. Assess code quality, security risks, "
            "architecture decisions, maintainability, and test coverage signals. "
            "Be specific and actionable."
        ),
        "allowed_tools": ["WebSearch", "WebFetch"],
        "max_turns": 6,
        "subagents": None,
    },
    "advisor": {
        "description": "Gives concrete, actionable recommendations based on the data provided",
        "system_prompt": (
            "You are a strategic advisor. Given data, findings, or a situation, produce "
            "clear, ranked, actionable recommendations. Be direct. No fluff. "
            "Format as: immediate actions, medium-term steps, things to avoid."
        ),
        "allowed_tools": ["WebSearch", "WebFetch"],
        "max_turns": 6,
        "subagents": None,
    },
    "debate": {
        "description": "Argues both sides of a topic for a balanced view",
        "system_prompt": (
            "You are a balanced debate analyst. For the given topic, present: "
            "1) The strongest case FOR it with evidence, "
            "2) The strongest case AGAINST it with evidence, "
            "3) A nuanced verdict. Use web search to find real arguments and data."
        ),
        "allowed_tools": ["WebSearch", "WebFetch"],
        "max_turns": 8,
        "subagents": None,
    },
    # ── Orchestrators: agents that spawn subagents ──────────────────────────
    "orchestrator": {
        "description": "Master orchestrator — decomposes complex tasks and spawns specialized subagents",
        "system_prompt": (
            "You are a master research orchestrator. Break complex tasks into subtopics. "
            "Use the Agent tool to spawn specialized subagents for each part — "
            "web_researcher for research, repo_analyst for GitHub repos, "
            "link_crawler for URLs, summarizer for condensing content. "
            "Synthesize all subagent results into a final comprehensive answer."
        ),
        "allowed_tools": ["WebSearch", "WebFetch", "Agent"],
        "max_turns": 20,
        "subagents": _SUBAGENTS,
    },
    "repo_deep_scanner": {
        "description": "Deep-scans a repo: spawns subagents to check issues, releases, contributors, and code quality",
        "system_prompt": (
            "You are a deep repository auditor. Given a GitHub repo, spawn subagents to: "
            "1) Analyze the README and codebase, "
            "2) Check recent issues and releases, "
            "3) Research community and ecosystem health. "
            "Use web_researcher and repo_analyst subagents. "
            "Produce a structured audit report with strengths, risks, and a verdict."
        ),
        "allowed_tools": ["WebSearch", "WebFetch", "Agent"],
        "max_turns": 20,
        "subagents": {
            "web_researcher": _SUBAGENTS["web_researcher"],
            "repo_analyst": _SUBAGENTS["repo_analyst"],
            "summarizer": _SUBAGENTS["summarizer"],
        },
    },
    "multi_site_scanner": {
        "description": "Scans multiple sites/links and synthesizes findings across all of them",
        "system_prompt": (
            "You are a multi-source analyst. For each URL or site given, spawn a "
            "link_crawler subagent to read it. Then synthesize findings across all sources "
            "into a single coherent report. Highlight patterns, contradictions, and key takeaways."
        ),
        "allowed_tools": ["WebSearch", "WebFetch", "Agent"],
        "max_turns": 20,
        "subagents": {
            "link_crawler": _SUBAGENTS["link_crawler"],
            "web_researcher": _SUBAGENTS["web_researcher"],
            "summarizer": _SUBAGENTS["summarizer"],
        },
    },
}


async def _run_async(agent_name: str, prompt: str) -> str:
    config = _AGENTS.get(agent_name, _AGENTS["researcher"])

    options = ClaudeAgentOptions(
        system_prompt=config["system_prompt"],
        allowed_tools=config["allowed_tools"],
        max_turns=config["max_turns"],
    )

    # Attach subagents if this agent spawns others
    if config.get("subagents"):
        options = ClaudeAgentOptions(
            system_prompt=config["system_prompt"],
            allowed_tools=config["allowed_tools"],
            max_turns=config["max_turns"],
            agents=config["subagents"],
        )

    result_text = f"[agent '{agent_name}' produced no output]"
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, ResultMessage):
            result_text = message.result

    return result_text


def run_agent(agent_name: str, prompt: str) -> str:
    """Synchronous entry point for running an agent."""
    return anyio.run(_run_async, agent_name, prompt)


def list_agents() -> dict:
    return {name: cfg["description"] for name, cfg in _AGENTS.items()}
