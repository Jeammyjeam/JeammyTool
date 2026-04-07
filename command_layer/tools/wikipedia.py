"""
Wikipedia REST API — free, no key required.
"""

import requests

WIKI_API = "https://en.wikipedia.org/api/rest_v1"
WIKI_SEARCH = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "JeammyTool/1.0"}


def fetch_summary(title: str) -> dict:
    """Fetch the summary of a Wikipedia article by title."""
    title_encoded = title.strip().replace(" ", "_")
    resp = requests.get(
        f"{WIKI_API}/page/summary/{title_encoded}",
        headers=HEADERS,
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "title": data.get("title"),
        "description": data.get("description"),
        "extract": data.get("extract", "")[:3000],
        "url": data.get("content_urls", {}).get("desktop", {}).get("page"),
    }


def search_wikipedia(query: str, limit: int = 5) -> list[dict]:
    """Search Wikipedia and return article summaries."""
    resp = requests.get(
        WIKI_SEARCH,
        headers=HEADERS,
        params={
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": limit,
            "format": "json",
        },
        timeout=10,
    )
    resp.raise_for_status()
    results = resp.json().get("query", {}).get("search", [])

    articles = []
    for r in results[:3]:  # fetch summaries for top 3
        try:
            summary = fetch_summary(r["title"])
            articles.append(summary)
        except Exception:
            articles.append({"title": r["title"], "extract": r.get("snippet", "")})

    return articles
