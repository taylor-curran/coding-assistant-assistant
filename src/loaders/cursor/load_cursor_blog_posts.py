# src/loaders/cursor/load_cursor_blog_posts.py

from bs4 import BeautifulSoup
from prefect import flow, task
from src.utils.network import fetch

BASE_URL = "https://www.cursor.com"
SITEMAP_URL = f"{BASE_URL}/sitemap.xml"


@task
def get_blog_post_urls_from_sitemap() -> list:
    """
    Parses the sitemap XML and extracts all canonical blog post URLs.
    For Cursor, we filter for URLs that include '/en/blog/' to avoid duplicates.
    Returns a list of blog post URLs.
    """
    sitemap_xml = fetch(SITEMAP_URL)
    soup = BeautifulSoup(sitemap_xml, "xml")
    urls = []
    for loc in soup.find_all("loc"):
        url = loc.get_text()
        # Filter for blog URLs in the English locale
        if "/blog/" in url and "/en/" in url:
            urls.append(url)
    return urls


# TODO: Parse the blog post HTML to extract the title, publication date, and content


@flow(log_prints=True)
def fetch_and_parse_cursor_blog_posts(limit: int = 5) -> None:
    """
    Fetches blog post URLs from the sitemap, then for each URL:
      - Fetches the raw HTML.
      - Parses the HTML to extract the title and publication date.
      - Prints the extracted information as JSON.
    """
    urls = get_blog_post_urls_from_sitemap()
    print(f"Found {len(urls)} blog post URLs in sitemap.")
    for url in urls:
        print(url)

    return urls


if __name__ == "__main__":
    fetch_and_parse_cursor_blog_posts()
