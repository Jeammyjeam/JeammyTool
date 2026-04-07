import requests

HN_API = "https://hacker-news.firebaseio.com/v0"
TOP_N = 15


def fetch_top_stories(limit: int = TOP_N) -> list[dict]:
    """Fetch top Hacker News stories with title, score, and URL."""
    ids = requests.get(f"{HN_API}/topstories.json", timeout=10).json()
    stories = []
    for story_id in ids[: min(limit, TOP_N)]:
        item = requests.get(f"{HN_API}/item/{story_id}.json", timeout=10).json()
        if item and item.get("type") == "story":
            stories.append(
                {
                    "title": item.get("title"),
                    "url": item.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                    "score": item.get("score"),
                    "comments": item.get("descendants", 0),
                    "by": item.get("by"),
                }
            )
    return stories
