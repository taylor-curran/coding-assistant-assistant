# src/utils/network.py

from playwright.sync_api import sync_playwright
import httpx
import re
from prefect import task

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; BlogLoader/1.0; +https://example.com)"
}


@task
def fetch(url: str) -> str:
    """
    Fetches the raw HTML (or XML) content for a given URL using httpx.
    Raises an error if the response status is not 200.
    """
    with httpx.Client(headers=HEADERS, timeout=30) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.text


@task
def fetch_rendered(url: str) -> str:
    """
    Fetches the rendered HTML content for a given URL using Playwright.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        content = page.content()  # Gets the fully rendered HTML
        browser.close()
        return content


if __name__ == "__main__":
    rendered_html = fetch_rendered.fn(
        "https://codeium.com/blog/amazon-codewhisperer-review"
    )
    assert re.search(r"<h1.*?>", rendered_html)
    print("Rendered HTML fetched successfully.")
