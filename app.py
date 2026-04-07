"""
AI Command Layer — Streamlit UI
Goal → Decompose → Execute → Result
"""

import streamlit as st
from command_layer.decomposer import decompose
from command_layer.executor import execute_pipeline
from command_layer.formatter import format_result

st.set_page_config(page_title="AI Command Layer", layout="wide")

st.title("AI Command Layer")
st.caption("Goal → Tasks → Execution → Result")

EXAMPLES = [
    "Analyze GitHub repo: anthropics/anthropic-sdk-python",
    "Compare repos: anthropics/anthropic-sdk-python vs openai/openai-python",
    "Find the best Python repos for web scraping",
    "What's on Hacker News today?",
    "Evaluate the npm package: express",
    "Evaluate the PyPI package: httpx",
    "Research: what is the current state of open source LLM tooling?",
    "What's trending in AI agents right now?",
]

st.markdown("**Try an example:**")
cols = st.columns(len(EXAMPLES))
for i, example in enumerate(EXAMPLES):
    if cols[i].button(example, key=f"ex_{i}"):
        st.session_state["command_value"] = example
        st.rerun()

command = st.text_input(
    "Enter your command",
    value=st.session_state.get("command_value", ""),
    placeholder="e.g. Analyze GitHub repo: owner/repo",
)

run = st.button("Execute", type="primary", disabled=not command.strip())

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

    # Show the plan
    st.markdown("### Task Plan")
    ICONS = {
        "github_fetch": "📦",
        "github_search": "🔍",
        "web_fetch": "🌐",
        "hackernews": "🔶",
        "npm_fetch": "📦",
        "pypi_fetch": "🐍",
        "analyze": "🧠",
        "agent": "🤖",
    }
    for step in steps:
        icon = ICONS.get(step["type"], "▶")
        st.markdown(f"{icon} **{step['id']}** ({step['type']}) — {step['description']}")

    st.divider()

    # 2. Execute
    st.markdown("### Execution")
    results = {}
    error_occurred = False

    for step in steps:
        step_id = step["id"]
        label = f"Running: {step['description']}"
        with st.status(label, expanded=False) as step_status:
            try:
                # Execute only this step (pass accumulated results as context)
                from command_layer.executor import execute_step
                result = execute_step(step, results)
                results[step_id] = result
                step_status.update(
                    label=f"Done: {step['description']}", state="complete"
                )
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

    # 4. Show result
    st.markdown("## Result")
    st.markdown(final)

    # Raw outputs (collapsed)
    with st.expander("Raw step outputs"):
        for step in steps:
            step_id = step["id"]
            st.markdown(f"**{step_id}** — {step['description']}")
            raw = results.get(step_id, "")
            json_types = {"github_fetch", "github_search", "web_fetch", "hackernews", "npm_fetch", "pypi_fetch"}
            lang = "json" if step["type"] in json_types else "markdown"
            st.code(raw[:2000] + ("..." if len(raw) > 2000 else ""), language=lang)
