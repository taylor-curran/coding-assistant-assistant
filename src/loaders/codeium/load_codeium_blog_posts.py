# src/loaders/codeium/load_codeium_blog_posts.py

from bs4 import BeautifulSoup
import json
from src.loaders.models.models import BlogPost, CodeAssistantCompany
from src.utils.network import fetch, fetch_rendered
from prefect import flow, task

BASE_URL = "https://codeium.com"
SITEMAP_URL = f"{BASE_URL}/sitemap.xml"


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


def extract_title(soup: BeautifulSoup) -> str:
    """
    Extracts the main title from a parsed blog post HTML. The main title is assumed to be the first <h1> element without an <a> tag.
    If no such element is found, the first <h1> element is used as a fallback.

    :param soup: The parsed HTML of the blog post.
    :return: The main title as a string.
    """
    h1_elements = soup.find_all("h1")
    main_title = None
    for h1 in h1_elements:
        # If the h1 does not contain an <a> tag, we assume it’s the main title.
        if not h1.find("a"):
            main_title = h1.get_text(strip=True)
            break

    if main_title:
        print("Main Title:", main_title)
    else:
        print("Main Title not found; using first h1 as fallback.")
        main_title = h1_elements[0].get_text(strip=True)

    return main_title


def extract_published_date(soup: BeautifulSoup) -> str:
    """
    Extracts the published date from a parsed blog post HTML by searching for a "datePublished" field in any JSON-LD script tags.

    :param soup: The parsed HTML of the blog post.
    :return: The published date as a string, or None if not found.
    """
    scripts = soup.find_all("script", type="application/ld+json")
    date_published = None
    for script in scripts:
        try:
            data = json.loads(script.string)
        except (json.JSONDecodeError, TypeError):
            continue

        # Handle cases where data might be a list or a dictionary.
        if isinstance(data, dict):
            if "datePublished" in data:
                date_published = data["datePublished"]
                break
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and "datePublished" in item:
                    date_published = item["datePublished"]
                    break
            if date_published:
                break

    if date_published:
        return date_published
    else:
        return None


def extract_content(soup: BeautifulSoup) -> str:
    """
    Extracts the content from a parsed blog post HTML.

    :param soup: The parsed HTML of the blog post.
    :return: The content of the blog post as a plain text string.
    """
    content_container = soup.find("div", class_="prose")
    if content_container:
        # Option 1: Extract plain text (all paragraphs, headings, etc.)
        content_text = content_container.get_text(separator="\n", strip=True)

        return content_text
    else:
        return None


@task
def parse_blog_post(html: str, url: str) -> BlogPost:
    """
    Parses the blog post HTML to extract the title, publication date, and content.
    """

    soup = BeautifulSoup(html, "html.parser")

    title = extract_title(soup)

    date = extract_published_date(soup)

    content = extract_content(soup)

    blog_post = BlogPost(
        url=url,
        title=title,
        date=date,
        content=content,
        company=CodeAssistantCompany.CODEIUM_ENTERPRISE,
    )

    return blog_post


@flow(log_prints=True)
def fetch_and_parse_codeium_blog_posts(limit: int = 5) -> None:
    """
    Fetches blog post URLs from the sitemap, then for each URL:
      - Fetches the raw HTML.
      - Parses the HTML to extract the title and publication date.
      - Prints the extracted information as JSON.
    """
    urls = get_blog_post_urls_from_sitemap()
    print(f"Found {len(urls)} blog post URLs in sitemap.")

    if limit is None:
        limit = len(urls)

    blog_posts = []

    for url in list(reversed(urls))[:limit]:
        html = fetch_rendered(url)
        blog_post = parse_blog_post(html, url)
        blog_posts.append(blog_post)

    for blog_post in blog_posts:
        blog_post.unique_id = f"{blog_post.company.value}_{blog_post.url}"

    # print sanity checkers
    if limit < 3:
        print(blog_posts[0].model_dump_json(indent=2))
        print("\n")
    else:
        for blog_post in blog_posts[:3]:
            print(blog_post.model_dump_json(indent=2))
            print("\n")

    return blog_posts


if __name__ == "__main__":
    fetch_and_parse_codeium_blog_posts(limit=4)
