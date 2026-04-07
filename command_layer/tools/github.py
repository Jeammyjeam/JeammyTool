import base64
import requests

GITHUB_API = "https://api.github.com"
HEADERS = {"Accept": "application/vnd.github.v3+json"}
README_LIMIT = 4000  # chars


def fetch_repo(repo_path: str) -> dict:
    """Fetch repository metadata and README from GitHub public API."""
    repo_path = repo_path.strip().strip("/")

    resp = requests.get(f"{GITHUB_API}/repos/{repo_path}", headers=HEADERS, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    readme_content = ""
    readme_resp = requests.get(
        f"{GITHUB_API}/repos/{repo_path}/readme", headers=HEADERS, timeout=10
    )
    if readme_resp.status_code == 200:
        encoded = readme_resp.json().get("content", "")
        readme_content = base64.b64decode(encoded).decode("utf-8", errors="ignore")
        readme_content = readme_content[:README_LIMIT]

    license_name = None
    if data.get("license"):
        license_name = data["license"].get("name")

    return {
        "full_name": data.get("full_name"),
        "description": data.get("description"),
        "stars": data.get("stargazers_count"),
        "forks": data.get("forks_count"),
        "open_issues": data.get("open_issues_count"),
        "language": data.get("language"),
        "topics": data.get("topics", []),
        "license": license_name,
        "homepage": data.get("homepage"),
        "archived": data.get("archived", False),
        "created_at": data.get("created_at"),
        "last_push": data.get("pushed_at"),
        "default_branch": data.get("default_branch"),
        "readme": readme_content,
    }
