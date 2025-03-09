# src/loaders/cursor/load_cursor_changelog.py


from bs4 import BeautifulSoup
import json
from src.loaders.models.models import ChangeLog, CodeAssistantCompany
from src.utils.network import fetch, fetch_rendered

CURSOR_CHANGELOG_URL = "https://www.cursor.com/en/changelog"


def parse_changelog(html: str) -> list[ChangeLog]:
    soup = BeautifulSoup(html, "html.parser")
    changelogs = []

    # Each version update is in an <article> tag
    for article in soup.find_all("article"):
        # Extract the version, which is in a <div> with a bunch of classes.
        # (Adjust the class names or use other attributes if needed.)
        version_div = article.find("div", class_="inline-flex items-center font-mono")
        version = version_div.get_text(strip=True) if version_div else ""

        # The title is in the <h2> tag
        title_tag = article.find("h2")
        title = title_tag.get_text(strip=True) if title_tag else ""

        # For the changes, collect all paragraphs and list items.
        # This will include the description and all bullet items.
        changes_parts = []
        for tag in article.find_all(["p", "li"]):
            text = tag.get_text(strip=True)
            if text:
                changes_parts.append(text)
        changes = "\n".join(changes_parts)

        # Create a ChangeLog instance (date is optional; here, we set it to None)
        changelog = ChangeLog(
            version=version,
            date=None,
            changes=f"{title}\n{changes}",
            company=CodeAssistantCompany.CODEIUM_ENTERPRISE,
        )
        changelogs.append(changelog)

    breakpoint()

    return changelogs


def fetch_and_parse_cursor_changelog() -> None:
    html = fetch_rendered(CURSOR_CHANGELOG_URL)

    changelogs = parse_changelog(html)

    print(f"Found {len(changelogs)} changelogs.")

    for changelog in changelogs[5]:
        # Print the changelog model as JSON (Pydantic V2).
        print(changelog.model_dump_json(indent=2))
        print("\n")


if __name__ == "__main__":
    fetch_and_parse_cursor_changelog()
