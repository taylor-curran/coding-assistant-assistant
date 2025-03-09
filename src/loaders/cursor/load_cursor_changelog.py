# src/loaders/cursor/load_cursor_changelog.py


from bs4 import BeautifulSoup
from src.loaders.models.models import ChangeLog, CodeAssistantCompany
from src.utils.network import fetch, fetch_rendered
import re

# TODO: Determine how to impute date data

CURSOR_CHANGELOG_URL = "https://www.cursor.com/en/changelog"


def parse_changelog(html: str) -> list[ChangeLog]:
    soup = BeautifulSoup(html, "html.parser")
    changelogs = []
    version_regex = re.compile(
        r"^\d+\.\d+\.x$"
    )  # matches strings like "0.46.x", "0.45.x", etc.

    # Loop over each version update which is inside an <article>
    for article in soup.find_all("article"):
        # --- Extract the version using a regex ---
        # Look for any <p> whose text matches our version pattern.
        version_tag = article.find(
            lambda tag: tag.name == "p"
            and tag.get_text(strip=True)
            and version_regex.match(tag.get_text(strip=True))
        )
        version = version_tag.get_text(strip=True) if version_tag else ""

        # --- Extract the title ---
        # The title is in the <h2> tag.
        title_tag = article.find("h2")
        title = title_tag.get_text(" ", strip=True) if title_tag else ""

        # --- Remove the version (and title if desired) from a copy of the article ---
        # This avoids duplicating the version text when we gather the changes.
        article_copy = BeautifulSoup(str(article), "html.parser").article
        if article_copy:
            # Remove any container that holds the version text.
            for tag in article_copy.find_all(
                lambda t: t.name in ["div", "p", "h2"]
                and version_regex.match(t.get_text(strip=True) or "")
            ):
                tag.decompose()

        # --- Extract changes ---
        # Use the cleaned-up article copy to get all remaining text.
        changes = article_copy.get_text(separator="\n", strip=True)

        # Create the ChangeLog instance
        changelog = ChangeLog(
            version=version,
            title=title,
            date=None,  # No date available on the page
            changes=f"{title}\n{changes}",
            company=CodeAssistantCompany.CURSOR_ENTERPRISE,
        )
        changelogs.append(changelog)

    version_list = [changelog.version for changelog in changelogs]

    for i, changelog in enumerate(list(reversed(changelogs))):
        changelog.index = i

    # TODO: I could impute version from title
    # TODO: I could also impute date from some older titles

    for changelog in changelogs:
        print(f"Version: {changelog.version}")
        print(f"Title: {changelog.title}")
        print(f"Date: {changelog.date}")
        print("\n")

    return changelogs


def fetch_and_parse_cursor_changelog() -> None:
    html = fetch_rendered(CURSOR_CHANGELOG_URL)

    changelogs = parse_changelog(html)

    print(f"Found {len(changelogs)} changelogs.")

    for changelog in changelogs[:2]:
        # Print the changelog model as JSON (Pydantic V2).
        print(changelog.model_dump_json(indent=2))
        print("\n")

    return changelogs


if __name__ == "__main__":
    fetch_and_parse_cursor_changelog()
