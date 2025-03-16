# src/loaders/cursor/dev/load_cursor_blog_posts_backup.py

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
    
    # Extract title - try multiple approaches to find the title
    title = "Unknown Title"
    
    # First look for the main h1
    title_element = soup.find("h1")
    if title_element:
        title = title_element.get_text(strip=True)
    
    # If that fails, look for typical title classes/patterns
    if title == "Unknown Title":
        # Try looking for structured data
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and "headline" in data:
                    title = data["headline"]
                    break
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "headline" in item:
                            title = item["headline"]
                            break
                    if title != "Unknown Title":
                        break
            except (json.JSONDecodeError, TypeError):
                continue
    
    # Check for common title patterns
    if title == "Unknown Title":
        meta_title = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "twitter:title"})
        if meta_title and meta_title.get("content"):
            title = meta_title.get("content")
    
    # Extract publication date
    # First try to find it in JSON-LD structured data
    date = None
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, dict) and "datePublished" in data:
                date = data["datePublished"]
                break
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "datePublished" in item:
                        date = item["datePublished"]
                        break
                if date:
                    break
        except (json.JSONDecodeError, TypeError):
            continue
    
    # If not found in JSON-LD, look for time elements
    if not date:
        time_element = soup.find("time")
        if time_element and time_element.get("datetime"):
            date = time_element.get("datetime")
        elif time_element:
            date = time_element.get_text(strip=True)
    
    # Extract content
    # Try to find the main content container
    content_container = soup.find("article") or soup.find("div", class_="prose")
    
    # If not found, look for common content containers
    if not content_container:
        content_container = (
            soup.find("div", class_=lambda x: x and any(cls in x for cls in ["blog-content", "post-content", "article-content"]))
            or soup.find("main")
        )
    
    # Extract text content
    if content_container:
        # Remove navigation elements, comments, etc.
        for element in content_container.find_all(["nav", "footer", "script", "style"]):
            element.decompose()
            
        content = content_container.get_text(separator="\n", strip=True)
    else:
        # Fallback: get content from body
        body = soup.find("body")
        if body:
            for element in body.find_all(["nav", "header", "footer", "script", "style"]):
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
