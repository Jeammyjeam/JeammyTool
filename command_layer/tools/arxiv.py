"""
arXiv research paper search — free API, no key required.
"""

import re
import requests
import xml.etree.ElementTree as ET

ARXIV_API = "https://export.arxiv.org/api/query"
NS = "http://www.w3.org/2005/Atom"
ARXIV_NS = "http://arxiv.org/schemas/atom"


def search_papers(query: str, max_results: int = 8) -> list[dict]:
    """Search arXiv for papers matching the query."""
    resp = requests.get(
        ARXIV_API,
        params={"search_query": query, "max_results": max_results, "sortBy": "relevance"},
        timeout=15,
    )
    resp.raise_for_status()

    root = ET.fromstring(resp.text)
    papers = []

    for entry in root.findall(f"{{{NS}}}entry"):
        title = (entry.findtext(f"{{{NS}}}title") or "").strip()
        summary = (entry.findtext(f"{{{NS}}}summary") or "").strip()
        published = entry.findtext(f"{{{NS}}}published") or ""
        link = ""
        for lnk in entry.findall(f"{{{NS}}}link"):
            if lnk.get("type") == "text/html":
                link = lnk.get("href", "")
        authors = [
            a.findtext(f"{{{NS}}}name") or ""
            for a in entry.findall(f"{{{NS}}}author")
        ]
        # Extract categories
        categories = [
            c.get("term", "") for c in entry.findall(f"{{{ARXIV_NS}}}primary_category")
        ]

        papers.append(
            {
                "title": title,
                "authors": authors[:4],
                "published": published[:10],
                "summary": summary[:500],
                "url": link,
                "categories": categories,
            }
        )

    return papers
