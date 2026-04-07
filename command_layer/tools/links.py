"""
Link extractor — fetches a URL and returns all outbound links,
classified by type (repo, docs, article, site, etc.).
"""

import re
import requests
from urllib.parse import urljoin, urlparse

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JeammyTool/1.0)"}
MAX_LINKS = 60


def _classify(url: str) -> str:
    u = url.lower()
    if "github.com" in u:
        return "repo"
    if any(x in u for x in ("docs.", "/docs/", "documentation", "readthedocs")):
        return "docs"
    if any(x in u for x in ("arxiv.org", "paper", "research", ".pdf")):
        return "paper"
    if any(x in u for x in ("npm", "pypi", "crates.io", "pkg.go")):
        return "package"
    if any(x in u for x in ("twitter.com", "x.com", "linkedin", "youtube", "medium.com")):
        return "social"
    return "link"


def extract_links(url: str) -> dict:
    """Fetch a URL and return all unique outbound links with classification."""
    resp = requests.get(url.strip(), headers=HEADERS, timeout=15)
    resp.raise_for_status()

    base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    raw_links = re.findall(r'href=["\']([^"\'#\s]+)["\']', resp.text)

    seen, links = set(), []
    for raw in raw_links:
        full = raw if raw.startswith("http") else urljoin(base, raw)
        parsed = urlparse(full)
        if parsed.scheme not in ("http", "https"):
            continue
        if full in seen:
            continue
        seen.add(full)
        links.append({"url": full, "type": _classify(full)})
        if len(links) >= MAX_LINKS:
            break

    # Group by type
    by_type: dict[str, list[str]] = {}
    for lnk in links:
        by_type.setdefault(lnk["type"], []).append(lnk["url"])

    return {
        "source_url": url,
        "total_links": len(links),
        "by_type": by_type,
    }
