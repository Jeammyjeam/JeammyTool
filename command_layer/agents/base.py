"""
Agent runner — spawns specialized Claude agents via the Agent SDK.
Each agent has a role, toolset, and system prompt.
"""

import anyio
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

# Agent registry: name → config
REGISTRY = {
    "researcher": {
        "description": "Researches topics by searching the web and reading pages",
        "system_prompt": (
            "You are a research analyst. Use web search and page fetching to gather "
            "current, accurate information. Synthesize findings into a clear, structured "
            "report with sources. Be thorough but concise."
        ),
        "allowed_tools": ["WebSearch", "WebFetch"],
        "max_turns": 10,
    },
    "fact_checker": {
        "description": "Verifies claims and finds supporting or contradicting evidence",
        "system_prompt": (
            "You are a fact-checker. For each claim given, search for evidence that "
            "supports or contradicts it. Return a verdict (Confirmed / Unconfirmed / False) "
            "with sources for each claim."
        ),
        "allowed_tools": ["WebSearch", "WebFetch"],
        "max_turns": 8,
    },
    "trend_scout": {
        "description": "Finds what is trending and emerging in a given domain",
        "system_prompt": (
            "You are a trend analyst. Search for the latest news, discussions, and releases "
            "in the given domain. Identify patterns, emerging tools, and notable shifts. "
            "Return a structured trends report."
        ),
        "allowed_tools": ["WebSearch", "WebFetch"],
        "max_turns": 10,
    },
    "code_reviewer": {
        "description": "Reviews code quality, security, and architecture from a repo",
        "system_prompt": (
            "You are a senior code reviewer. Given repository data and code snippets, "
            "assess: code quality, security risks, architecture decisions, maintainability, "
            "and test coverage signals. Be specific and actionable."
        ),
        "allowed_tools": ["WebSearch", "WebFetch"],
        "max_turns": 6,
    },
}


async def _run_async(agent_name: str, prompt: str) -> str:
    config = REGISTRY.get(agent_name, REGISTRY["researcher"])
    result_text = f"[agent '{agent_name}' produced no output]"

    async for message in query(
        prompt=prompt,
        options=ClaudeAgentOptions(
            system_prompt=config["system_prompt"],
            allowed_tools=config["allowed_tools"],
            max_turns=config["max_turns"],
        ),
    ):
        if isinstance(message, ResultMessage):
            result_text = message.result

    return result_text


def run_agent(agent_name: str, prompt: str) -> str:
    """Synchronous entry point — runs the async agent and returns the result."""
    return anyio.run(_run_async, agent_name, prompt)


def list_agents() -> dict:
    """Return agent names and their descriptions."""
    return {name: cfg["description"] for name, cfg in REGISTRY.items()}
