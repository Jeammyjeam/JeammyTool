import requests

NPM_REGISTRY = "https://registry.npmjs.org"
WEEKLY_DOWNLOADS_API = "https://api.npmjs.org/downloads/point/last-week"


def fetch_package(package_name: str) -> dict:
    """Fetch npm package metadata and weekly download count."""
    package_name = package_name.strip().lstrip("@").replace(" ", "-")

    resp = requests.get(f"{NPM_REGISTRY}/{package_name}/latest", timeout=10)
    resp.raise_for_status()
    data = resp.json()

    # Weekly downloads
    downloads = None
    try:
        dl_resp = requests.get(f"{WEEKLY_DOWNLOADS_API}/{package_name}", timeout=10)
        if dl_resp.status_code == 200:
            downloads = dl_resp.json().get("downloads")
    except Exception:
        pass

    return {
        "name": data.get("name"),
        "version": data.get("version"),
        "description": data.get("description"),
        "license": data.get("license"),
        "homepage": data.get("homepage"),
        "repository": (data.get("repository") or {}).get("url"),
        "keywords": data.get("keywords", []),
        "dependencies": list((data.get("dependencies") or {}).keys()),
        "weekly_downloads": downloads,
        "maintainers": [m.get("name") for m in (data.get("maintainers") or [])],
    }
