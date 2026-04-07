"""
Extended GitHub tools — issues, releases, contributors, repo file tree.
"""

import requests

GITHUB_API = "https://api.github.com"
HEADERS = {"Accept": "application/vnd.github.v3+json"}


def fetch_issues(repo_path: str, state: str = "open", limit: int = 10) -> list[dict]:
    """Fetch recent issues from a repo."""
    resp = requests.get(
        f"{GITHUB_API}/repos/{repo_path}/issues",
        headers=HEADERS,
        params={"state": state, "per_page": limit, "sort": "updated"},
        timeout=10,
    )
    resp.raise_for_status()
    return [
        {
            "number": i.get("number"),
            "title": i.get("title"),
            "state": i.get("state"),
            "labels": [l["name"] for l in i.get("labels", [])],
            "comments": i.get("comments"),
            "created_at": i.get("created_at"),
            "updated_at": i.get("updated_at"),
            "url": i.get("html_url"),
        }
        for i in resp.json()
        if not i.get("pull_request")  # exclude PRs
    ]


def fetch_releases(repo_path: str, limit: int = 5) -> list[dict]:
    """Fetch recent releases from a repo."""
    resp = requests.get(
        f"{GITHUB_API}/repos/{repo_path}/releases",
        headers=HEADERS,
        params={"per_page": limit},
        timeout=10,
    )
    resp.raise_for_status()
    return [
        {
            "tag": r.get("tag_name"),
            "name": r.get("name"),
            "published_at": r.get("published_at"),
            "prerelease": r.get("prerelease"),
            "body_preview": (r.get("body") or "")[:400],
            "url": r.get("html_url"),
        }
        for r in resp.json()
    ]


def fetch_contributors(repo_path: str, limit: int = 10) -> list[dict]:
    """Fetch top contributors from a repo."""
    resp = requests.get(
        f"{GITHUB_API}/repos/{repo_path}/contributors",
        headers=HEADERS,
        params={"per_page": limit},
        timeout=10,
    )
    resp.raise_for_status()
    return [
        {
            "login": c.get("login"),
            "contributions": c.get("contributions"),
            "profile": c.get("html_url"),
        }
        for c in resp.json()
    ]
