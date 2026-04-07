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
| `extract_links` | Any URL | classified link map |
| `hackernews` | HN Firebase API | top stories |
| `reddit_fetch` | Reddit JSON API | subreddit name |
| `reddit_search` | Reddit search | query string |
| `npm_fetch` | npm registry | package name |
| `pypi_fetch` | PyPI JSON API | package name |
| `arxiv_search` | arXiv API | research query |
| `wikipedia_fetch` | Wikipedia REST API | article title |
| `wikipedia_search` | Wikipedia search | query string |
| `devto_fetch` | DEV.to API | tag name |
| `devto_search` | DEV.to API | query string |

### AI steps

| Step | What it does |
|---|---|
| `analyze` | Single focused LLM call for synthesis |
| `agent(researcher)` | Multi-turn web research + synthesis |
| `agent(fact_checker)` | Verifies claims with sources |
| `agent(trend_scout)` | Finds emerging trends in a domain |
| `agent(code_reviewer)` | Reviews repo code quality and security |
| `agent(advisor)` | Gives concrete, ranked, actionable recommendations |
| `agent(debate)` | Argues both sides — balanced view with verdict |
| `agent(orchestrator)` | **Spawns subagents** — delegates subtasks autonomously |
| `agent(repo_deep_scanner)` | **Spawns subagents** — deep repo audit |
| `agent(multi_site_scanner)` | **Spawns subagents** — scans multiple URLs |

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
Search arXiv for papers on: LLM agent frameworks
What is the Wikipedia article on: Retrieval-augmented generation
Find DEV.to articles about: python async
Scan all links on: https://docs.anthropic.com/en/home
Research: what is the current state of open source LLM tooling?
What's trending in AI agents right now?
Debate: are LLM agents ready for production?
Recommend: should I use FastAPI or Django for a new Python API?
Orchestrate a full research report on: LLM agent frameworks in 2025
```

---

## Run it

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here
streamlit run app.py
```

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
app.py                          # Streamlit UI (sidebar examples, cache panel, export)
command_layer/
├── decomposer.py               # Breaks command → typed step list (17 step types)
├── executor.py                 # Dispatches steps; checks/writes cache
├── formatter.py                # Synthesizes results into final answer
├── cache.py                    # Session + disk cache (skips live data)
├── agents/
│   └── base.py                 # 9 agents incl. 3 orchestrators that spawn subagents
└── tools/
    ├── github.py               # Repo fetch + search
    ├── github_extras.py        # Issues, releases, contributors
    ├── web.py                  # URL fetch + HTML stripping
    ├── links.py                # Link extractor + classifier
    ├── hackernews.py           # HN top stories
    ├── reddit.py               # Posts + search (no auth)
    ├── npm.py                  # npm registry
    ├── pypi.py                 # PyPI JSON API
    ├── arxiv.py                # arXiv paper search
    ├── wikipedia.py            # Wikipedia REST API
    └── devto.py                # DEV.to articles
```

---

## License

Unlicense — public domain. Do whatever you want with it.
