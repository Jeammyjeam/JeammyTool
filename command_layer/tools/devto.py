import requests

DEVTO_API = "https://dev.to/api"
HEADERS = {"User-Agent": "JeammyTool/1.0"}


def fetch_articles(tag: str, per_page: int = 10) -> list[dict]:
    """Fetch top DEV.to articles by tag — no API key required."""
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
            "published_at": (a.get("published_at") or "")[:10],
            "url": a.get("url"),
            "author": a.get("user", {}).get("name"),
        }
        for a in resp.json()
    ]
