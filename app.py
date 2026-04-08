"""
AI Command Layer — Streamlit UI
Goal → Decompose → Execute → Result

For Vercel/web deployment, see api/index.py (FastAPI).
"""

import streamlit as st
from command_layer.decomposer import decompose
from command_layer.executor import execute_step, _execution_waves
from command_layer.formatter import format_result
from command_layer import cache

st.set_page_config(page_title="AI Command Layer", layout="wide")
st.title("AI Command Layer")
st.caption("Goal → Decompose → Execute → Result")

EXAMPLES = [
    "Analyze GitHub repo: anthropics/anthropic-sdk-python",
    "Deep audit repo: anthropics/anthropic-sdk-python",
    "Compare repos: anthropics/anthropic-sdk-python vs openai/openai-python",
    "What's trending on GitHub today?",
    "Find the best Python repos for web scraping",
    "What's on Hacker News today?",
    "What are people saying about AI agents on Reddit?",
    "Evaluate the npm package: express",
    "Evaluate the PyPI package: httpx",
    "Search arXiv for: LLM agent frameworks",
    "What is: Retrieval-augmented generation (Wikipedia)",
    "Find DEV.to articles about: python async",
    "Stack Overflow: how to use asyncio in Python",
    "Scan links on: https://docs.anthropic.com/en/home",
    "Research: current state of open source LLM tooling",
    "What's trending in AI agents right now?",
    "Debate: are LLM agents ready for production?",
    "Recommend: FastAPI vs Django for a new Python API",
    "Orchestrate a full research report on: LLM agent frameworks in 2025",
]

ICONS = {
    "github_fetch": "📦", "github_search": "🔍", "github_issues": "🐛",
    "github_releases": "🏷️", "github_contributors": "👥", "github_trending": "📈",
    "web_fetch": "🌐", "extract_links": "🔗",
    "hackernews": "🔶", "reddit_fetch": "🟠", "reddit_search": "🟠",
    "npm_fetch": "📦", "pypi_fetch": "🐍",
    "arxiv_search": "📄", "wikipedia_fetch": "📖", "wikipedia_search": "📖",
    "devto_fetch": "✍️", "stackoverflow_search": "💬",
    "analyze": "🧠", "agent": "🤖",
}

JSON_TYPES = {
    "github_fetch", "github_search", "github_issues", "github_releases",
    "github_contributors", "github_trending", "web_fetch", "extract_links",
    "hackernews", "reddit_fetch", "reddit_search", "npm_fetch", "pypi_fetch",
    "arxiv_search", "wikipedia_fetch", "wikipedia_search", "devto_fetch",
    "stackoverflow_search",
}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Examples")
    for example in EXAMPLES:
        if st.button(example, key=f"ex_{hash(example)}", use_container_width=True):
            st.session_state["cmd"] = example
            st.rerun()
    st.divider()
    st.markdown("### Cache")
    stats = cache.stats()
    st.caption(f"{stats['entries']} entries cached")
    if st.button("Clear cache", use_container_width=True):
        cache.clear()
        st.success("Cleared")

# ── Main ──────────────────────────────────────────────────────────────────────
command = st.text_input(
    "Enter your command",
    value=st.session_state.get("cmd", ""),
    placeholder="e.g. Analyze GitHub repo: owner/repo",
)

if st.button("Execute", type="primary", disabled=not command.strip()):
    st.divider()

    # 1. Decompose
    with st.status("Decomposing command into tasks...", expanded=True) as s:
        try:
            steps = decompose(command)
            s.update(label=f"Plan ready — {len(steps)} steps", state="complete")
        except Exception as e:
            s.update(label="Decomposition failed", state="error")
            st.error(str(e))
            st.stop()

    # Show plan
    st.markdown("### Task Plan")
    waves = _execution_waves(steps)
    for wi, wave in enumerate(waves):
        parallel = len(wave) > 1
        for step in wave:
            icon = ICONS.get(step["type"], "▶")
            label = step["type"]
            if step["type"] == "agent":
                name = step.get("agent", "?")
                spawns = name in ("orchestrator", "repo_deep_scanner", "multi_site_scanner")
                label = f"agent({name})" + (" ⚡ spawns subagents" if spawns else "")
            parallel_tag = " `parallel`" if parallel else ""
            st.markdown(f"{icon} **{step['id']}** `{label}`{parallel_tag} — {step['description']}")

    st.divider()

    # 2. Execute (wave by wave, parallel within wave)
    st.markdown("### Execution")
    results: dict = {}
    error_occurred = False

    for wave in waves:
        if len(wave) == 1:
            step = wave[0]
            from_cache = cache.get(step["type"], step.get("input", "")) is not None
            if from_cache:
                results[step["id"]] = execute_step(step, results)
                st.success(f"⚡ {step['description']} *(cached)*")
            else:
                with st.status(f"Running: {step['description']}", expanded=False) as ss:
                    try:
                        results[step["id"]] = execute_step(step, results)
                        ss.update(label=f"Done: {step['description']}", state="complete")
                    except Exception as e:
                        ss.update(label=f"Failed: {step['description']}", state="error")
                        st.error(str(e))
                        error_occurred = True
                        break
        else:
            # Show parallel badge
            st.info(f"Running {len(wave)} steps in parallel...")
            with st.status(f"Parallel: {', '.join(s['id'] for s in wave)}", expanded=False) as ss:
                snapshot = dict(results)
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                    futures = {pool.submit(execute_step, s, snapshot): s for s in wave}
                    for fut in concurrent.futures.as_completed(futures):
                        s = futures[fut]
                        try:
                            results[s["id"]] = fut.result()
                        except Exception as e:
                            results[s["id"]] = f"[error: {e}]"
                ss.update(label=f"Done: {', '.join(s['id'] for s in wave)}", state="complete")

        if error_occurred:
            break

    if error_occurred:
        st.stop()

    # 3. Format
    st.divider()
    with st.status("Generating final answer...", expanded=False) as s:
        try:
            final = format_result(command, steps, results)
            s.update(label="Answer ready", state="complete")
        except Exception as e:
            s.update(label="Formatting failed", state="error")
            st.error(str(e))
            st.stop()

    # 4. Result
    st.markdown("## Result")
    st.markdown(final)
    st.download_button(
        "Download as Markdown",
        data=f"# {command}\n\n{final}",
        file_name="result.md",
        mime="text/markdown",
    )

    with st.expander("Raw step outputs"):
        for step in steps:
            st.markdown(f"**{step['id']}** — {step['description']}")
            raw = results.get(step["id"], "")
            lang = "json" if step["type"] in JSON_TYPES else "markdown"
            st.code(raw[:2000] + ("..." if len(raw) > 2000 else ""), language=lang)
