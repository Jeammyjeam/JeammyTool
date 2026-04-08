"""
DEV.to API — free, no key required for reading articles.
"""

import requests

DEVTO_API = "https://dev.to/api"
HEADERS = {"User-Agent": "JeammyTool/1.0"}
ARTICLE_LIMIT = 10


def fetch_articles(tag: str, per_page: int = ARTICLE_LIMIT) -> list[dict]:
    """Fetch recent top articles from DEV.to by tag."""
    resp = requests.get(
        f"{DEVTO_API}/articles",
        headers=HEADERS,
        params={"tag": tag.strip().lower(), "per_page": per_page, "top": 7},
        timeout=10,
    )
    resp.raise_for_status()
    return [
        {
            "title": a.get("title"),
            "description": a.get("description"),
            "tags": a.get("tag_list", []),
            "reactions": a.get("public_reactions_count"),
            "comments": a.get("comments_count"),
            "published_at": a.get("published_at", "")[:10],
            "url": a.get("url"),
            "author": a.get("user", {}).get("name"),
        }
        for a in resp.json()
    ]


def search_articles(query: str, per_page: int = ARTICLE_LIMIT) -> list[dict]:
    """Search DEV.to articles."""
    resp = requests.get(
        f"{DEVTO_API}/articles/search",
        headers=HEADERS,
        params={"q": query, "per_page": per_page},
        timeout=10,
    )
    # Fallback: dev.to search endpoint may not exist on all versions
    if resp.status_code == 404:
        return fetch_articles(query.split()[0])
    resp.raise_for_status()
    return [
        {
            "title": a.get("title"),
            "description": a.get("description"),
            "url": a.get("url"),
            "author": a.get("user", {}).get("name"),
        }
        for a in resp.json()
    ]
