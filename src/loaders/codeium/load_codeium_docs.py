# src/loaders/codeium/load_codeium_docs.py
from bs4 import BeautifulSoup
from prefect import flow

from src.utils.network import fetch, fetch_rendered
from src.loaders.models.models import DocsPage, CodeAssistantCompany

BASE_URL = "https://docs.codeium.com"
SITEMAP_URL = f"{BASE_URL}/sitemap.xml"


# model this off of get_blog_post_urls_from_sitemap()
def get_doc_pages_from_sitemap():
    sitemap_xml = fetch(SITEMAP_URL)
    soup = BeautifulSoup(sitemap_xml, "xml")
    urls = []
    for loc in soup.find_all("loc"):
        url = loc.get_text()
        urls.append(url)

    return urls


def parse_docs_file(html: str, url: str) -> DocsPage:
    soup = BeautifulSoup(html, "html.parser")

    # Extract the title: Prefer an <h1> tag; if missing, use the <title> element.
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(strip=True)
    elif soup.title:
        title = soup.title.get_text(strip=True)
    else:
        title = "Untitled Document"

    # Try to extract just the main content.
    # Option 1: Look for a container that holds the MDX content.
    content_container = soup.find(attrs={"data-mdx-content": True})
    if content_container:
        content = content_container.get_text(separator="\n", strip=True)
    else:
        # Option 2: If no MDX container, try to extract content from <main>.
        main = soup.find("main")
        if main:
            # Remove navigation elements if they exist.
            navbar = main.find(id="navbar")
            if navbar:
                navbar.decompose()
            content = main.get_text(separator="\n", strip=True)
        else:
            # Fallback: use the entire document body.
            content = soup.get_text(separator="\n", strip=True)

    unique_id = f"{title}-{url}"

    return DocsPage(
        url=url,
        title=title,
        company=CodeAssistantCompany.CODEIUM_ENTERPRISE,
        content=content,
        unique_id=unique_id,
    )


@flow(log_prints=True)
def fetch_and_parse_codeium_docs():
    urls = get_doc_pages_from_sitemap()
    print(f"Found {len(urls)} doc file URLs in sitemap.")

    docs_files = []

    for url in urls:
        print("URL: ")
        print(url)
        html = fetch(url)
        doc_file = parse_docs_file(html, url)
        docs_files.append(doc_file)

    for docs_file in docs_files[:10]:
        print(docs_file.model_dump_json(indent=2))
        print("\n")

    return docs_files


if __name__ == "__main__":
    fetch_and_parse_codeium_docs()
