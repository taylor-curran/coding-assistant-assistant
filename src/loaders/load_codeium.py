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


def parse_blog_post(html: str) -> BlogPost:
    """
    Parses the blog post HTML to extract the title and publication date.
    Saves the soup content to a debug file.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Save the parsed HTML for debugging.
    with open("src/loaders/soup_debug.html", "w") as f:
        f.write(str(soup))

    print('TODO')

    # Extract title from <h1> tag with a fallback.
    title = (
        soup.find("h1").get_text(strip=True) if soup.find("h1") else "Title Not Found"
    )

    # Extract publication date from a <time> tag.
    time_tag = soup.find("time")
    date = "Date Not Found"
    if time_tag:
        date = time_tag.get("datetime") or time_tag.get_text(strip=True)

    # Return the Pydantic model with an empty content field.
    return BlogPost(title=title, date=date, content="")


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
