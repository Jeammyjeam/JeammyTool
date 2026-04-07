"""
AI Command Layer — Streamlit UI
Goal → Decompose → Execute → Result
"""

import json
import streamlit as st
from command_layer.decomposer import decompose
from command_layer.executor import execute_step
from command_layer.formatter import format_result
from command_layer import cache

st.set_page_config(page_title="AI Command Layer", layout="wide")

st.title("AI Command Layer")
st.caption("Goal → Tasks → Execution → Result")

EXAMPLES = [
    # GitHub
    "Analyze GitHub repo: anthropics/anthropic-sdk-python",
    "Deep audit repo: anthropics/anthropic-sdk-python",
    "Compare repos: anthropics/anthropic-sdk-python vs openai/openai-python",
    "Find the best Python repos for web scraping",
    # News & social
    "What's on Hacker News today?",
    "What are people saying about AI agents on Reddit?",
    # Packages
    "Evaluate the npm package: express",
    "Evaluate the PyPI package: httpx",
    # Research & knowledge
    "Search arXiv for papers on: LLM agent frameworks",
    "What is the Wikipedia article on: Retrieval-augmented generation",
    "Find DEV.to articles about: python async",
    # Web
    "Scan all links on: https://docs.anthropic.com/en/home",
    # Agents
    "Research: what is the current state of open source LLM tooling?",
    "What's trending in AI agents right now?",
    "Debate: are LLM agents ready for production?",
    "Recommend: should I use FastAPI or Django for a new Python API?",
    "Orchestrate a full research report on: LLM agent frameworks in 2025",
]

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Examples")
    for example in EXAMPLES:
        if st.button(example, key=f"ex_{hash(example)}", use_container_width=True):
            st.session_state["command_value"] = example
            st.rerun()

    st.divider()
    st.markdown("### Cache")
    stats = cache.stats()
    st.caption(f"{stats['entries']} entries cached")
    if st.button("Clear cache", use_container_width=True):
        cache.clear()
        st.success("Cache cleared")

# ── Main ─────────────────────────────────────────────────────────────────────
command = st.text_input(
    "Enter your command",
    value=st.session_state.get("command_value", ""),
    placeholder="e.g. Analyze GitHub repo: owner/repo",
)

run = st.button("Execute", type="primary", disabled=not command.strip())

ICONS = {
    "github_fetch": "📦",
    "github_search": "🔍",
    "github_issues": "🐛",
    "github_releases": "🏷️",
    "github_contributors": "👥",
    "web_fetch": "🌐",
    "extract_links": "🔗",
    "hackernews": "🔶",
    "reddit_fetch": "🟠",
    "reddit_search": "🟠",
    "npm_fetch": "📦",
    "pypi_fetch": "🐍",
    "arxiv_search": "📄",
    "wikipedia_fetch": "📖",
    "wikipedia_search": "📖",
    "devto_fetch": "✍️",
    "devto_search": "✍️",
    "analyze": "🧠",
    "agent": "🤖",
}

JSON_TYPES = {
    "github_fetch", "github_search", "github_issues", "github_releases",
    "github_contributors", "web_fetch", "extract_links", "hackernews",
    "reddit_fetch", "reddit_search", "npm_fetch", "pypi_fetch",
    "arxiv_search", "wikipedia_fetch", "wikipedia_search",
    "devto_fetch", "devto_search",
}

if run and command.strip():
    st.divider()

    # 1. Decompose
    with st.status("Decomposing command into tasks...", expanded=True) as status:
        try:
            steps = decompose(command)
            status.update(label=f"Task plan ready — {len(steps)} steps", state="complete")
        except Exception as e:
            status.update(label="Decomposition failed", state="error")
            st.error(f"Could not decompose command: {e}")
            st.stop()

    # Show plan
    st.markdown("### Task Plan")
    for step in steps:
        icon = ICONS.get(step["type"], "▶")
        label = step["type"]
        if step["type"] == "agent":
            agent_name = step.get("agent", "?")
            spawns = agent_name in ("orchestrator", "repo_deep_scanner", "multi_site_scanner")
            label = f"agent({agent_name})" + (" ⚡ spawns subagents" if spawns else "")
        st.markdown(f"{icon} **{step['id']}** `{label}` — {step['description']}")

    st.divider()

    # 2. Execute
    st.markdown("### Execution")
    results = {}
    error_occurred = False

    for step in steps:
        step_id = step["id"]
        # Check cache before showing spinner
        cached_result = cache.get(step["type"], step.get("input", ""))
        if cached_result is not None:
            results[step_id] = cached_result
            st.success(f"⚡ {step['description']} *(from cache)*")
            continue

        with st.status(f"Running: {step['description']}", expanded=False) as step_status:
            try:
                result = execute_step(step, results)
                results[step_id] = result
                step_status.update(label=f"Done: {step['description']}", state="complete")
            except Exception as e:
                step_status.update(label=f"Failed: {step['description']}", state="error")
                st.error(f"Step {step_id} failed: {e}")
                error_occurred = True
                break

    if error_occurred:
        st.stop()

    # 3. Format
    st.divider()
    with st.status("Generating final answer...", expanded=False) as fmt_status:
        try:
            final = format_result(command, steps, results)
            fmt_status.update(label="Answer ready", state="complete")
        except Exception as e:
            fmt_status.update(label="Formatting failed", state="error")
            st.error(f"Could not format result: {e}")
            st.stop()

    # 4. Result + export
    st.markdown("## Result")
    st.markdown(final)

    # Export as markdown
    export_md = f"# {command}\n\n{final}"
    st.download_button(
        label="Download as Markdown",
        data=export_md,
        file_name="result.md",
        mime="text/markdown",
    )

    # Raw outputs
    with st.expander("Raw step outputs"):
        for step in steps:
            step_id = step["id"]
            st.markdown(f"**{step_id}** — {step['description']}")
            raw = results.get(step_id, "")
            lang = "json" if step["type"] in JSON_TYPES else "markdown"
            st.code(raw[:2000] + ("..." if len(raw) > 2000 else ""), language=lang)
