from urllib.parse import urljoin
import httpx
from bs4 import BeautifulSoup

class CodeiumBlogLoader:
    BASE_URL = "https://codeium.com"
    SITEMAP_URL = "https://codeium.com/sitemap.xml"  # Assuming the sitemap is here

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; CodeiumBlogLoader/1.0; +https://codeium.com)"
        }

    def fetch(self, url: str) -> str:
        """Fetches the raw HTML or XML for a given URL."""
        with httpx.Client(headers=self.headers, timeout=30) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.text

    def get_blog_post_urls_from_sitemap(self) -> list:
        """Parses the sitemap XML to extract URLs that include '/blog/'."""
        sitemap_xml = self.fetch(self.SITEMAP_URL)
        soup = BeautifulSoup(sitemap_xml, "xml")
        urls = []
        for loc in soup.find_all("loc"):
            url = loc.get_text()
            if "/blog/" in url:
                urls.append(url)
        return urls

    def fetch_blog_posts(self, count: int = 3) -> None:
        """Fetches and prints raw HTML for the first 'count' blog posts from the sitemap."""
        urls = self.get_blog_post_urls_from_sitemap()
        print(f"Found {len(urls)} blog post URLs in sitemap.")
        for url in urls[:count]:
            html = self.fetch(url)
            print(f"--- Blog post: {url} ---")
            print(html[:500])  # Print the first 500 characters for inspection
            print("...\n")

def main():
    loader = CodeiumBlogLoader()
    loader.fetch_blog_posts()

if __name__ == "__main__":
    main()
