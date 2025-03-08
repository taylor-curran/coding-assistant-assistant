import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel
from requests_html import HTMLSession


# Define a simple Pydantic model for a blog post.
class BlogPost(BaseModel):
    title: str
    date: str
    content: str  # Keeping this for compatibility; set to an empty string if unused.


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


def fetch_rendered(url: str, sleep=5) -> str:
    session = HTMLSession()
    r = session.get(url)

    # Render the page to execute JavaScript (adjust sleep as needed)
    r.html.render(sleep=sleep)

    # Get the fully rendered HTML
    rendered_html = r.html.html

    return rendered_html


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


def extract_title(soup: BeautifulSoup) -> None:
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


def parse_blog_post(html: str) -> BlogPost:
    """
    Parses the blog post HTML to extract the title and publication date.
    Saves the soup content to a debug file.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Save the parsed HTML for debugging.
    with open("src/loaders/soup_debug.html", "w") as f:
        f.write(str(soup))

    title = extract_title(soup)

    # fake date
    date = "2023-01-01"
    content = "123456"

    return BlogPost(title=title, date=date, content=content)


def fetch_and_parse_blog_posts(count: int = 3) -> None:
    """
    Fetches blog post URLs from the sitemap, then for each URL:
      - Fetches the raw HTML.
      - Parses the HTML to extract the title and publication date.
      - Prints the extracted information as JSON.
    """
    urls = get_blog_post_urls_from_sitemap()
    print(f"Found {len(urls)} blog post URLs in sitemap.")

    for url in urls[:count]:
        html = fetch_rendered(url)
        blog_post = parse_blog_post(html)
        # Print the blog post model as JSON (Pydantic V2).
        print(blog_post.model_dump_json(indent=2))
        print("\n")


def main():
    fetch_and_parse_blog_posts()


if __name__ == "__main__":
    main()
