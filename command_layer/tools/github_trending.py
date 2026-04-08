"""
GitHub Trending — scrapes the public trending page (no API key required).
"""

import re
import requests

TRENDING_URL = "https://github.com/trending"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JeammyTool/1.0)"}


def fetch_trending(language: str = "", since: str = "daily", limit: int = 15) -> list[dict]:
    """Fetch trending GitHub repos for a language and time range."""
    url = TRENDING_URL
    if language:
        url += f"/{language.lower().replace(' ', '-')}"
    resp = requests.get(url, headers=HEADERS, params={"since": since}, timeout=15)
    resp.raise_for_status()
    html = resp.text

    # Extract repo articles
    repos = []
    articles = re.findall(r'<article[^>]*class="[^"]*Box-row[^"]*"[^>]*>(.*?)</article>', html, re.DOTALL)
    for article in articles[:limit]:
        # Repo name
        name_match = re.search(r'href="/([^/]+/[^/"]+)"[^>]*>\s*([^<]+)\s*/\s*([^<]+)', article)
        full_name = name_match.group(1).strip() if name_match else ""

        # Description
        desc_match = re.search(r'<p[^>]*class="[^"]*col-9[^"]*"[^>]*>\s*(.*?)\s*</p>', article, re.DOTALL)
        description = re.sub(r'\s+', ' ', desc_match.group(1)).strip() if desc_match else ""

        # Stars
        star_match = re.search(r'svg[^>]*octicon-star.*?</svg>\s*([\d,]+)', article, re.DOTALL)
        stars = int(star_match.group(1).replace(',', '')) if star_match else 0

        # Stars today
        today_match = re.search(r'([\d,]+)\s+stars today', article)
        stars_today = int(today_match.group(1).replace(',', '')) if today_match else 0

        # Language
        lang_match = re.search(r'itemprop="programmingLanguage"[^>]*>\s*([^<]+)\s*<', article)
        lang = lang_match.group(1).strip() if lang_match else ""

        if full_name:
            repos.append({
                "full_name": full_name,
                "description": description,
                "language": lang,
                "stars": stars,
                "stars_today": stars_today,
                "url": f"https://github.com/{full_name}",
            })

    return repos
