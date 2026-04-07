import requests

PYPI_API = "https://pypi.org/pypi"


def fetch_package(package_name: str) -> dict:
    """Fetch PyPI package metadata."""
    package_name = package_name.strip().lower().replace(" ", "-")

    resp = requests.get(f"{PYPI_API}/{package_name}/json", timeout=10)
    resp.raise_for_status()
    data = resp.json()

    info = data.get("info", {})
    releases = data.get("releases", {})

    # Get the latest 5 versions
    recent_versions = sorted(releases.keys(), reverse=True)[:5]

    return {
        "name": info.get("name"),
        "version": info.get("version"),
        "summary": info.get("summary"),
        "license": info.get("license"),
        "author": info.get("author"),
        "home_page": info.get("home_page"),
        "project_urls": info.get("project_urls", {}),
        "keywords": info.get("keywords"),
        "requires_python": info.get("requires_python"),
        "classifiers": info.get("classifiers", [])[:10],
        "recent_versions": recent_versions,
        "total_versions": len(releases),
    }
