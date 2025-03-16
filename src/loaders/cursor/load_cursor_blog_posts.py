# src/loaders/cursor/load_cursor_blog_posts.py

from bs4 import BeautifulSoup
import json
from prefect import flow, task
from src.utils.network import fetch, fetch_rendered
from src.loaders.models.models import BlogPost, CodeAssistantCompany

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


# Parse the blog post HTML to extract the title, publication date, and content


@task
def parse_blog_post(html: str, url: str) -> BlogPost:
    """
    Parses the blog post HTML to extract the title, publication date, and content.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Extract title - using the most reliable methods
    title = "Unknown Title"

    # Check for meta title (most reliable based on observed data)
    meta_title = soup.find("meta", property="og:title") or soup.find(
        "meta", attrs={"name": "twitter:title"}
    )
    if meta_title and meta_title.get("content"):
        title = meta_title.get("content")
    # Fallback to h1 if needed
    elif soup.find("h1"):
        title = soup.find("h1").get_text(strip=True)

    # Extract publication date - simplified approach
    date = None

    # Look for time elements (most common pattern)
    time_element = soup.find("time")
    if time_element:
        if time_element.get("datetime"):
            date = time_element.get("datetime")
        else:
            date = time_element.get_text(strip=True)

    # Extract content - simplified to most common pattern
    # Prioritize article tag (common in blog layouts)
    content_container = soup.find("article")

    # Fallback to main if article not found
    if not content_container:
        content_container = soup.find("main")

    # Extract text content
    if content_container:
        # Remove navigation elements, comments, etc.
        for element in content_container.find_all(["nav", "footer", "script", "style"]):
            element.decompose()
        content = content_container.get_text(separator="\n", strip=True)
    else:
        # Last resort: get content from body
        body = soup.find("body")
        if body:
            for element in body.find_all(
                ["nav", "header", "footer", "script", "style"]
            ):
                element.decompose()
            content = body.get_text(separator="\n", strip=True)
        else:
            content = "Content not found"

    blog_post = BlogPost(
        url=url,
        title=title,
        date=date,
        content=content,
        company=CodeAssistantCompany.CURSOR_ENTERPRISE,
    )

    return blog_post


@flow(log_prints=True)
def fetch_and_parse_cursor_blog_posts(limit: int = 5) -> list[BlogPost]:
    """
    Fetches blog post URLs from the sitemap, then for each URL:
      - Fetches the raw HTML.
      - Parses the HTML to extract the title and publication date.
      - Prints the extracted information as JSON.

    Returns:
        A list of BlogPost objects.
    """
    urls = get_blog_post_urls_from_sitemap()
    print(f"Found {len(urls)} blog post URLs in sitemap.")

    # Use the last 'limit' posts (most recent)
    if limit is None:
        limit = len(urls)

    blog_posts = []

    for url in list(reversed(urls))[:limit]:
        print(f"Processing: {url}")
        html = fetch_rendered(url)
        blog_post = parse_blog_post(html, url)
        blog_posts.append(blog_post)

    # Add unique identifiers
    for blog_post in blog_posts:
        blog_post.unique_id = f"{blog_post.company.value}_{blog_post.url}"

    # Print some blog posts for verification
    if limit < 3:
        print(blog_posts[0].model_dump_json(indent=2))
        print("\n")
    else:
        for blog_post in blog_posts[:3]:
            print(blog_post.model_dump_json(indent=2))
            print("\n")

    return blog_posts


if __name__ == "__main__":
    fetch_and_parse_cursor_blog_posts(2)
