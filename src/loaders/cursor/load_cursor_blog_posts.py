# src/loaders/cursor/load_cursor_blog_posts.py

import httpx
from bs4 import BeautifulSoup
from requests_html import HTMLSession
import json
from src.loaders.models.models import BlogPost, CodeAssistantCompany


# Global constants.
BASE_URL = "https://codeium.com"
SITEMAP_URL = f"{BASE_URL}/sitemap.xml"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CodeiumBlogLoader/1.0; +https://codeium.com)"
}


def fetch(url: str) -> str:
    """
    Fetches the raw HTML (or XML) content for a given URL using httpx.
    Raises an error if the response status is not 200.
    """
    with httpx.Client(headers=HEADERS, timeout=30) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.text


def get_blog_post_urls_from_sitemap() -> list:
    """
    Parses the sitemap XML and extracts all URLs that include '/blog/'.
    Returns a list of blog post URLs.
    """
    sitemap_xml = fetch(SITEMAP_URL)
    soup = BeautifulSoup(sitemap_xml, "xml")
    urls = []
    for loc in soup.find_all("loc"):
        url = loc.get_text()
        if "/blog/" in url:
            urls.append(url)
    return urls


def fetch_and_parse_cursor_blog_posts(limit: int = 5) -> None:
    """
    Fetches blog post URLs from the sitemap, then for each URL:
      - Fetches the raw HTML.
      - Parses the HTML to extract the title and publication date.
      - Prints the extracted information as JSON.
    """
    urls = get_blog_post_urls_from_sitemap()
    print(f"Found {len(urls)} blog post URLs in sitemap.")


if __name__ == "__main__":
    fetch_and_parse_cursor_blog_posts()
