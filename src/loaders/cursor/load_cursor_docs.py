# src/loaders/cursor/load_cursor_docs.py
from bs4 import BeautifulSoup

from src.loaders.models.models import CodeAssistantCompany, DocsPage
from src.utils.network import fetch

BASE_URL = "https://docs.cursor.com"
SITEMAP_URL = f"{BASE_URL}/sitemap.xml"

# TODO: Implement cursor docs parsing and load functions