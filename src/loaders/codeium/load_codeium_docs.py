# src/loaders/codeium/load_codeium_docs.py
from bs4 import BeautifulSoup
from prefect import flow

from src.utils.network import fetch
from src.utils.network import fetch

BASE_URL = "https://docs.codeium.com"
SITEMAP_URL = f"{BASE_URL}/sitemap.xml"


# model this off of get_blog_post_urls_from_sitemap()
def get_doc_pages_from_sitemap():
    sitemap_xml = fetch(SITEMAP_URL)
    soup = BeautifulSoup(sitemap_xml, "xml")
    urls = []
    for loc in soup.find_all("loc"):
        url = loc.get_text()
        if "/blog/" in url:
            urls.append(url)
    return urls


@flow(log_prints=True)
def fetch_and_parse_codeium_docs():
    pass


# TODO: Load codeium docs
