# src/loaders/cursor/load_cursor_changelog.py


from bs4 import BeautifulSoup
import json
from src.loaders.models.models import ChangeLog, CodeAssistantCompany
from src.utils.network import fetch, fetch_rendered

CURSOR_CHANGELOG_URL = "https://www.cursor.com/changelog"
