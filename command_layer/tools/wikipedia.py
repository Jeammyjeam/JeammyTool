import requests

WIKI_REST = "https://en.wikipedia.org/api/rest_v1"
WIKI_SEARCH = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "JeammyTool/1.0"}


def fetch_summary(title: str) -> dict:
    """Fetch a Wikipedia article summary."""
    resp = requests.get(
        f"{WIKI_REST}/page/summary/{title.strip().replace(' ', '_')}",
        headers=HEADERS, timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "title": data.get("title"),
        "description": data.get("description"),
        "extract": data.get("extract", "")[:3000],
        "url": data.get("content_urls", {}).get("desktop", {}).get("page"),
    }


def search_wikipedia(query: str, limit: int = 3) -> list[dict]:
    """Search Wikipedia and return top article summaries."""
    resp = requests.get(
        WIKI_SEARCH, headers=HEADERS,
        params={"action": "query", "list": "search", "srsearch": query,
                "srlimit": limit, "format": "json"},
        timeout=10,
    )
    resp.raise_for_status()
    results = resp.json().get("query", {}).get("search", [])
    articles = []
    for r in results:
        try:
            articles.append(fetch_summary(r["title"]))
        except Exception:
            articles.append({"title": r["title"], "extract": r.get("snippet", "")})
    return articles
