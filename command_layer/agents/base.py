"""
Agent runner — spawns Claude agents via the Agent SDK.
Single agents and orchestrators that spawn subagents.
"""

import anyio
from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition, ResultMessage

# ── Subagents (used inside orchestrators) ────────────────────────────────────

_SUBAGENTS = {
    "web_researcher": AgentDefinition(
        description="Searches the web and reads pages to research a specific subtopic.",
        prompt="You are a focused web researcher. Search thoroughly and return key findings with sources.",
        tools=["WebSearch", "WebFetch"],
    ),
    "repo_analyst": AgentDefinition(
        description="Analyzes a GitHub repository's quality, activity, and purpose.",
        prompt="You are a code analyst. Fetch the repo data, README, and recent activity. Assess quality and usefulness.",
        tools=["WebSearch", "WebFetch"],
    ),
    "link_crawler": AgentDefinition(
        description="Fetches a URL, extracts useful links and content.",
        prompt="Fetch the given URL, read its content, extract important links, and summarize.",
        tools=["WebFetch"],
    ),
    "summarizer": AgentDefinition(
        description="Condenses long content into a structured summary.",
        prompt="Take the provided content and return a clear, structured, bullet-pointed summary.",
        tools=[],
    ),
}

# ── Agent registry ────────────────────────────────────────────────────────────

_AGENTS: dict[str, dict] = {
    "researcher": {
        "description": "Web research + synthesis",
        "system_prompt": "You are a research analyst. Search the web thoroughly, read sources, and synthesize findings into a clear structured report with citations.",
        "allowed_tools": ["WebSearch", "WebFetch"],
        "max_turns": 10,
        "subagents": None,
    },
    "fact_checker": {
        "description": "Verifies claims with sources",
        "system_prompt": "You are a fact-checker. For each claim, search for evidence. Return verdict (Confirmed/Unconfirmed/False) with sources.",
        "allowed_tools": ["WebSearch", "WebFetch"],
        "max_turns": 8,
        "subagents": None,
    },
    "trend_scout": {
        "description": "Finds emerging trends in a domain",
        "system_prompt": "You are a trend analyst. Search for latest news, repos, and discussions in the given domain. Return a structured trends report.",
        "allowed_tools": ["WebSearch", "WebFetch"],
        "max_turns": 10,
        "subagents": None,
    },
    "code_reviewer": {
        "description": "Reviews code quality, security, and architecture",
        "system_prompt": "You are a senior code reviewer. Assess code quality, security risks, architecture, maintainability, and test coverage. Be specific and actionable.",
        "allowed_tools": ["WebSearch", "WebFetch"],
        "max_turns": 6,
        "subagents": None,
    },
    "advisor": {
        "description": "Gives ranked, actionable recommendations from data",
        "system_prompt": "You are a strategic advisor. Given data or a situation, produce clear ranked actionable recommendations. Format: immediate actions, medium-term steps, things to avoid.",
        "allowed_tools": ["WebSearch", "WebFetch"],
        "max_turns": 6,
        "subagents": None,
    },
    "debate": {
        "description": "Argues both sides of a topic with a balanced verdict",
        "system_prompt": "You are a debate analyst. Present: 1) Strongest case FOR with evidence, 2) Strongest case AGAINST with evidence, 3) A nuanced verdict. Use web search for real data.",
        "allowed_tools": ["WebSearch", "WebFetch"],
        "max_turns": 8,
        "subagents": None,
    },
    # ── Orchestrators ─────────────────────────────────────────────────────────
    "orchestrator": {
        "description": "Breaks complex tasks and spawns specialized subagents",
        "system_prompt": (
            "You are a master research orchestrator. Break complex tasks into subtopics. "
            "Spawn specialized subagents: web_researcher for research, repo_analyst for repos, "
            "link_crawler for URLs, summarizer for condensing. Synthesize all into a final answer."
        ),
        "allowed_tools": ["WebSearch", "WebFetch", "Agent"],
        "max_turns": 20,
        "subagents": _SUBAGENTS,
    },
    "repo_deep_scanner": {
        "description": "Deep repo audit spawning multiple subagents",
        "system_prompt": (
            "You are a deep repository auditor. Spawn subagents to: "
            "1) Analyze README and codebase, 2) Check issues/releases, "
            "3) Research community health. Produce a structured audit report."
        ),
        "allowed_tools": ["WebSearch", "WebFetch", "Agent"],
        "max_turns": 20,
        "subagents": {k: _SUBAGENTS[k] for k in ("web_researcher", "repo_analyst", "summarizer")},
    },
    "multi_site_scanner": {
        "description": "Scans multiple sites/URLs and synthesizes findings",
        "system_prompt": (
            "You are a multi-source analyst. For each URL, spawn a link_crawler subagent. "
            "Synthesize findings across all sources into one coherent report."
        ),
        "allowed_tools": ["WebSearch", "WebFetch", "Agent"],
        "max_turns": 20,
        "subagents": {k: _SUBAGENTS[k] for k in ("link_crawler", "web_researcher", "summarizer")},
    },
}


async def _run_async(agent_name: str, prompt: str) -> str:
    config = _AGENTS.get(agent_name, _AGENTS["researcher"])
    options = ClaudeAgentOptions(
        system_prompt=config["system_prompt"],
        allowed_tools=config["allowed_tools"],
        max_turns=config["max_turns"],
        **({"agents": config["subagents"]} if config.get("subagents") else {}),
    )
    result = f"[agent '{agent_name}' produced no output]"
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, ResultMessage):
            result = message.result
    return result


def run_agent(agent_name: str, prompt: str) -> str:
    return anyio.run(_run_async, agent_name, prompt)


def list_agents() -> dict:
    return {name: cfg["description"] for name, cfg in _AGENTS.items()}
