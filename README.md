# JeammyTool

An AI Command Layer that converts goals into coordinated actions.

**Goal → Decompose → Execute → Result**

---

## How it works

1. You type a command (e.g. *"Analyze GitHub repo: anthropics/anthropic-sdk-python"*)
2. The **Decomposer** breaks it into typed steps
3. The **Executor** runs each step — calling APIs, tools, or agents
4. The **Formatter** synthesizes everything into a clean answer

---

## What it can do

### Data tools (no AI required)

| Tool | Source | Example input |
|---|---|---|
| `github_fetch` | GitHub API | `owner/repo` |
| `github_search` | GitHub search API | `"python scraping sort:stars"` |
| `github_issues` | GitHub API | `owner/repo` |
| `github_releases` | GitHub API | `owner/repo` |
| `github_contributors` | GitHub API | `owner/repo` |
| `web_fetch` | Any URL | `https://...` |
| `extract_links` | Any URL | `https://...` → classified link map |
| `hackernews` | HN Firebase API | top stories |
| `reddit_fetch` | Reddit JSON API | subreddit name |
| `reddit_search` | Reddit search | query string |
| `npm_fetch` | npm registry | package name |
| `pypi_fetch` | PyPI JSON API | package name |

### AI steps

| Step | What it does |
|---|---|
| `analyze` | Single focused LLM call for synthesis |
| `agent(researcher)` | Multi-turn web research agent |
| `agent(fact_checker)` | Verifies claims with sources |
| `agent(trend_scout)` | Finds emerging trends in a domain |
| `agent(code_reviewer)` | Reviews repo code quality and security |
| `agent(orchestrator)` | **Spawns subagents** — delegates subtasks autonomously |
| `agent(repo_deep_scanner)` | **Spawns subagents** — deep repo audit |
| `agent(multi_site_scanner)` | **Spawns subagents** — scans multiple sites |

---

## Example commands

```
Analyze GitHub repo: anthropics/anthropic-sdk-python
Deep audit repo: anthropics/anthropic-sdk-python
Compare repos: anthropics/anthropic-sdk-python vs openai/openai-python
Find the best Python repos for web scraping
What's on Hacker News today?
What are people saying about AI agents on Reddit?
Evaluate the npm package: express
Evaluate the PyPI package: httpx
Scan all links on this site: https://docs.anthropic.com/en/home
Research: what is the current state of open source LLM tooling?
What's trending in AI agents right now?
Orchestrate a full research report on: LLM agent frameworks in 2025
```

---

## Run it

**Local (Streamlit UI):**
```bash
pip install -r requirements-dev.txt
export ANTHROPIC_API_KEY=your_key_here
streamlit run app.py
```

**Vercel (REST API + web UI):**
Deploy this repo on Vercel — it auto-detects `api/index.py` and `vercel.json`.
Set `ANTHROPIC_API_KEY` in your Vercel environment variables.
The web UI is served at `/`, API endpoint at `POST /execute`.

---

## Not locked to Claude

The data tools (GitHub, Reddit, HN, npm, PyPI, web) work completely independently — no AI needed. The AI parts (decompose/analyze/format/agent) can be swapped to any model. The project is not locked to Claude.

To use a local model via [Ollama](https://ollama.com) instead:

```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
# then replace anthropic.Anthropic() calls in decomposer.py, executor.py, formatter.py
```

---

## Project structure

```
app.py                          # Streamlit UI
command_layer/
├── decomposer.py               # Claude breaks command → typed step list
├── executor.py                 # Dispatches each step to the right tool/agent
├── formatter.py                # Synthesizes results into final answer
├── agents/
│   └── base.py                 # Agent registry + subagent orchestration
└── tools/
    ├── github.py               # Repo fetch + search
    ├── github_extras.py        # Issues, releases, contributors
    ├── web.py                  # URL fetch + HTML stripping
    ├── links.py                # Link extractor + classifier
    ├── hackernews.py           # HN top stories
    ├── reddit.py               # Reddit posts + search
    ├── npm.py                  # npm package metadata
    └── pypi.py                 # PyPI package metadata
```

---

## License

Unlicense — public domain. Do whatever you want with it.
