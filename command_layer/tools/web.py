import re
import requests

TEXT_LIMIT = 5000  # chars
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JeammyTool/1.0)"}


def fetch_url(url: str) -> dict:
    """Fetch a URL and return cleaned text content."""
    resp = requests.get(url.strip(), headers=HEADERS, timeout=15)
    resp.raise_for_status()

    content_type = resp.headers.get("content-type", "")
    if "text/html" not in content_type and "text/plain" not in content_type:
        return {"url": url, "content": f"[Non-text content: {content_type}]", "status": resp.status_code}

    text = resp.text

    # Strip HTML tags
    text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return {
        "url": url,
        "status": resp.status_code,
        "content_type": content_type,
        "content": text[:TEXT_LIMIT],
    }
