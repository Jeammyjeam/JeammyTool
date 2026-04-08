"""
Stack Overflow search — free API, no key required (rate-limited to ~300 req/day).
"""

import requests

SO_API = "https://api.stackexchange.com/2.3"


def search_questions(query: str, limit: int = 8) -> list[dict]:
    """Search Stack Overflow questions by keyword."""
    resp = requests.get(
        f"{SO_API}/search/advanced",
        params={
            "order": "desc",
            "sort": "votes",
            "q": query,
            "site": "stackoverflow",
            "pagesize": limit,
            "filter": "withbody",
        },
        timeout=10,
    )
    resp.raise_for_status()
    items = resp.json().get("items", [])
    return [
        {
            "title": q.get("title"),
            "score": q.get("score"),
            "answers": q.get("answer_count"),
            "accepted": q.get("is_answered"),
            "views": q.get("view_count"),
            "tags": q.get("tags", []),
            "url": q.get("link"),
            "body_preview": (q.get("body") or "")[:400],
        }
        for q in items
    ]
