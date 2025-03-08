from typing import List
from urllib.parse import urljoin
import json

import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel

class BlogPost(BaseModel):
    title: str
    date: str
    content: str
    tags: List[str]
    link: str


class CodeiumBlogLoader:
    BASE_URL = "https://codeium.com"
    BLOG_URL = "https://codeium.com/blog"

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; CodeiumBlogLoader/1.0; +https://codeium.com)"
        }

    def fetch(self, url: str) -> str:
        with httpx.Client(headers=self.headers, timeout=30) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.text

    def parse_blog_post(self, url: str) -> BlogPost:
        html = self.fetch(url)
        soup = BeautifulSoup(html, "html.parser")

        # Extract title (try h1, h2, or h3)
        title_tag = soup.find("h1") or soup.find("h2") or soup.find("h3")
        title = title_tag.get_text(strip=True) if title_tag else "No Title"

        # Extract publication date (from a <time> tag)
        time_tag = soup.find("time")
        date = (
            time_tag.get("datetime")
            if time_tag and time_tag.has_attr("datetime")
            else (time_tag.get_text(strip=True) if time_tag else "Unknown Date")
        )

        # Extract main content; adjust the selector as needed
        content_div = soup.find("div", class_="post-content")
        if not content_div:
            content_div = soup.find("article")
        content = content_div.get_text(separator="\n", strip=True) if content_div else "No Content"

        # Extract tags; assumes tags are in an element with class "tags"
        tags_container = soup.find(class_="tags")
        tags = [tag.get_text(strip=True) for tag in tags_container.find_all("a")] if tags_container else []

        return BlogPost(title=title, date=date, content=content, tags=tags, link=url)

    def load_blog_posts(self) -> List[BlogPost]:
        html = self.fetch(self.BLOG_URL)
        soup = BeautifulSoup(html, "html.parser")
        post_urls = set()

        # Try to find blog post URLs within <article> tags first
        for article in soup.find_all("article"):
            a_tag = article.find("a", href=True)
            if a_tag:
                full_url = urljoin(self.BASE_URL, a_tag["href"])
                post_urls.add(full_url)

        # Fallback: find any link that includes "/blog/" but isn’t the main page
        if not post_urls:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "/blog/" in href and href.rstrip("/") != self.BLOG_URL.rstrip("/"):
                    full_url = urljoin(self.BASE_URL, href)
                    post_urls.add(full_url)

        blog_posts = []
        for url in post_urls:
            try:
                post = self.parse_blog_post(url)
                blog_posts.append(post)
            except Exception as e:
                print(f"Error parsing {url}: {e}")
        return blog_posts


def main():
    loader = CodeiumBlogLoader()
    posts = loader.load_blog_posts()
    for post in posts:
        # Use model_dump() to convert the model to a dict,
        # then pretty-print it using json.dumps with indent
        print(json.dumps(post.model_dump(), indent=2))


if __name__ == "__main__":
    main()
