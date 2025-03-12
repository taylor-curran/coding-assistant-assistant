# src/loaders/codeium/load_codeium_docs.py
from bs4 import BeautifulSoup
from prefect import flow

from src.utils.network import fetch, fetch_rendered

BASE_URL = "https://docs.codeium.com"
SITEMAP_URL = f"{BASE_URL}/sitemap.xml"

from enum import Enum
from typing import Optional
from pydantic import BaseModel

class CodeAssistantCompany(str, Enum):
    CODEIUM_ENTERPRISE = "Codeium_Enterprise"
    CURSOR_ENTERPRISE = "Cursor_Enterprise"
    COPILOT_ENTERPRISE = "Copilot_Enterprise"

class DocsPage(BaseModel):
    title: str
    company: CodeAssistantCompany
    content: str
    unique_id: Optional[str] = None

# model this off of get_blog_post_urls_from_sitemap()
def get_doc_pages_from_sitemap():
    sitemap_xml = fetch(SITEMAP_URL)
    soup = BeautifulSoup(sitemap_xml, "xml")
    urls = []
    for loc in soup.find_all("loc"):
        url = loc.get_text()
        urls.append(url)

    return urls


def parse_docs_file(html: str) -> DocsPage:
    soup = BeautifulSoup(html, "html.parser")

    # Debug: print the prettified HTML structure.
    print('Pretty print')
    print(soup.prettify()[:10000])

    # Extract the title: Prefer an <h1> tag; if missing, use the <title> element.
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(strip=True)
    elif soup.title:
        title = soup.title.get_text(strip=True)
    else:
        title = "Untitled Document"

    # Extract the content: try to use <article>, then a <div> with class "content",
    # and finally fallback to the entire body text.
    article = soup.find("article")
    if article:
        content = article.get_text(separator="\n", strip=True)
    else:
        div_content = soup.find("div", class_="content")
        if div_content:
            content = div_content.get_text(separator="\n", strip=True)
        elif soup.body:
            content = soup.body.get_text(separator="\n", strip=True)
        else:
            content = soup.get_text(separator="\n", strip=True)
    
    unique_id = f"{title}"

    return DocsPage(
        title=title,
        company=CodeAssistantCompany.CODEIUM_ENTERPRISE,
        content=content,
        unique_id=unique_id
    )



@flow(log_prints=True)
def fetch_and_parse_codeium_docs():
    urls = get_doc_pages_from_sitemap()
    print(f"Found {len(urls)} doc file URLs in sitemap.")

    docs_files = []

    for url in urls[0:2]:
        print("URL: ")
        print(url)
        html = fetch(url)
        doc_file = parse_docs_file(html)
        docs_files.append(doc_file)

    for docs_file in docs_files[:3]:
            print(docs_file.model_dump_json(indent=2))
            print("\n")


if __name__ == "__main__":
    fetch_and_parse_codeium_docs()
