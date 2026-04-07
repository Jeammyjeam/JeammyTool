import requests

REDDIT_API = "https://www.reddit.com"
HEADERS = {"User-Agent": "JeammyTool/1.0 (research bot)"}
POST_LIMIT = 15


def fetch_subreddit(subreddit: str, sort: str = "hot", limit: int = POST_LIMIT) -> list[dict]:
    """Fetch top posts from a subreddit (no auth required)."""
    sort = sort if sort in ("hot", "top", "new", "rising") else "hot"
    url = f"{REDDIT_API}/r/{subreddit}/{sort}.json"
    resp = requests.get(url, headers=HEADERS, params={"limit": limit}, timeout=10)
    resp.raise_for_status()
    posts = resp.json().get("data", {}).get("children", [])
    return [
        {
            "title": p["data"].get("title"),
            "score": p["data"].get("score"),
            "comments": p["data"].get("num_comments"),
            "url": p["data"].get("url"),
            "permalink": f"https://reddit.com{p['data'].get('permalink')}",
            "flair": p["data"].get("link_flair_text"),
            "author": p["data"].get("author"),
        }
        for p in posts
        if p.get("kind") == "t3"
    ]


def search_reddit(query: str, subreddit: str = "all", limit: int = 10) -> list[dict]:
    """Search Reddit posts."""
    url = f"{REDDIT_API}/r/{subreddit}/search.json"
    resp = requests.get(
        url,
        headers=HEADERS,
        params={"q": query, "limit": limit, "sort": "relevance", "t": "month"},
        timeout=10,
    )
    resp.raise_for_status()
    posts = resp.json().get("data", {}).get("children", [])
    return [
        {
            "title": p["data"].get("title"),
            "score": p["data"].get("score"),
            "subreddit": p["data"].get("subreddit"),
            "url": p["data"].get("url"),
            "permalink": f"https://reddit.com{p['data'].get('permalink')}",
        }
        for p in posts
        if p.get("kind") == "t3"
    ]
