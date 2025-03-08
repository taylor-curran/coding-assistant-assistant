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
        Parses the blog post HTML and extracts title and publication date.
        
        Returns:
            BlogPost: A Pydantic model with title and date information
        """
        soup = BeautifulSoup(html, "html.parser")
        
        # Extract title using a more robust approach
        title = (
            soup.find("h1").get_text(strip=True) 
            if soup.find("h1") 
            else "Title Not Found"
        )
        
        # Extract date with fallback options
        time_tag = soup.find("time")
        date = "Date Not Found"
        if time_tag:
            date = (
                time_tag.get("datetime") or 
                time_tag.get_text(strip=True)
            )
        
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
