from urllib.parse import urljoin
import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel

# Define a simple Pydantic model for a blog post.
class BlogPost(BaseModel):
    title: str
    date: str
    # You can add more fields later (e.g., content, tags) as needed.

class CodeiumBlogLoader:
    # Base URL for Codeium; used to resolve relative URLs if needed.
    BASE_URL = "https://codeium.com"
    # URL for the sitemap; this is assumed to contain all site URLs.
    SITEMAP_URL = "https://codeium.com/sitemap.xml"

    def __init__(self):
        # Set custom headers to mimic a real browser.
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; CodeiumBlogLoader/1.0; +https://codeium.com)"
        }

    def fetch(self, url: str) -> str:
        """
        Fetches the raw HTML (or XML) content for a given URL.
        Uses httpx.Client to send a GET request with custom headers.
        Raises an error if the response has a non-200 status.
        """
        with httpx.Client(headers=self.headers, timeout=30) as client:
            response = client.get(url)
            response.raise_for_status()  # Raise an error for bad responses.
            return response.text

    def get_blog_post_urls_from_sitemap(self) -> list:
        """
        Parses the sitemap XML and extracts all URLs that include '/blog/'.
        Returns a list of blog post URLs.
        """
        sitemap_xml = self.fetch(self.SITEMAP_URL)
        # Use the 'xml' parser for BeautifulSoup to parse the sitemap.
        soup = BeautifulSoup(sitemap_xml, "xml")
        urls = []
        # Loop through all <loc> tags in the sitemap.
        for loc in soup.find_all("loc"):
            url = loc.get_text()
            # If the URL contains '/blog/', consider it a blog post URL.
            if "/blog/" in url:
                urls.append(url)
        return urls

    def parse_blog_post(self, html: str) -> BlogPost:
        """
        Parses the blog post HTML and extracts:
          - Title: Expected to be in an <h1> tag.
          - Date: Expected to be in a <time> tag (using the 'datetime' attribute if available).
        Returns a BlogPost Pydantic model instance with the extracted data.
        """
        soup = BeautifulSoup(html, "html.parser")

        # --- Extract the Title ---
        # We assume the main title is contained in an <h1> tag.
        title_tag = soup.find("h1")
        if title_tag:
            title = title_tag.get_text(strip=True)
        else:
            title = "Title Not Found"

        # --- Extract the Publication Date ---
        # We look for a <time> tag which might have a 'datetime' attribute.
        time_tag = soup.find("time")
        if time_tag:
            # If the <time> tag has a 'datetime' attribute, use that.
            # Otherwise, fall back to the tag's text.
            date = time_tag.get("datetime") if time_tag.has_attr("datetime") else time_tag.get_text(strip=True)
        else:
            date = "Date Not Found"

        # Return a BlogPost model with the extracted data.
        return BlogPost(title=title, date=date)

    def fetch_and_parse_blog_posts(self, count: int = 3) -> None:
        """
        Fetches blog post URLs from the sitemap, then for each blog post:
          - Fetches the raw HTML.
          - Parses the HTML to extract the title and publication date.
          - Prints the extracted information as JSON using the BlogPost Pydantic model.
        The parameter 'count' controls how many blog posts to process.
        """
        urls = self.get_blog_post_urls_from_sitemap()
        print(f"Found {len(urls)} blog post URLs in sitemap.")

        # Process only the first 'count' URLs.
        for url in urls[:count]:
            html = self.fetch(url)
            blog_post = self.parse_blog_post(html)
            print(f"--- Blog post: {url} ---")
            # Use model_dump_json (Pydantic V2) to print the model as JSON.
            print(blog_post.model_dump_json(indent=2))
            print("\n")

def main():
    loader = CodeiumBlogLoader()
    loader.fetch_and_parse_blog_posts()

if __name__ == "__main__":
    main()
