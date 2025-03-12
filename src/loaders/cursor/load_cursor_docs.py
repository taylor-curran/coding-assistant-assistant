# src/loaders/cursor/load_cursor_docs.py
from bs4 import BeautifulSoup
from prefect import flow

from src.utils.network import fetch, fetch_rendered
from src.loaders.models.models import DocsPage, CodeAssistantCompany

BASE_URL = "https://docs.cursor.com"
SITEMAP_URL = f"{BASE_URL}/sitemap.xml"
