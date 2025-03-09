# src/loaders/cursor/load_cursor_changelog.py


from bs4 import BeautifulSoup
from src.loaders.models.models import ChangeLog, CodeAssistantCompany
from src.utils.network import fetch, fetch_rendered
import re
from typing import List
from prefect import flow, task

# TODO: Determine how to impute date data

CURSOR_CHANGELOG_URL = "https://www.cursor.com/en/changelog"


@task
def parse_changelog(html: str) -> list[ChangeLog]:
    """
    Parse the HTML from the Cursor changelog page into a list of ChangeLog models.

    The function loops over each version update which is inside an <article> tag,
    extracting the version, title, and changes text. The version is extracted using
    a regex, and the title is in an <h2> tag. The changes text is gathered by
    removing any containers that hold the version text from a copy of the article,
    and then using the cleaned-up article copy to get all remaining text.

    The function returns a list of ChangeLog models.
    """
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

    return changelogs


@task
def impute_changelog_missing_data(changelogs: List["ChangeLog"]) -> List["ChangeLog"]:
    # Regex to capture a date in the format (YYYY-MM-DD)
    """
    Modifies a list of ChangeLog models in-place to impute missing date and version fields.

    For each ChangeLog, if the date field is missing, it tries to extract a date from the title.
    If the version field is missing, it first tries to extract from the title, then from the changes text.
    """
    date_regex = re.compile(r"\((\d{4}-\d{2}-\d{2})\)")
    # Regex to capture version strings.
    # This will match versions like:
    #   - v0.1.2-0.1.3
    #   - 0.46.x
    #   - v2
    # It allows an optional leading "v", digits separated by dots (or "x"),
    # and an optional hyphenated second part.
    version_regex = re.compile(r"(v?\d+(?:\.(?:\d+|x))*(?:-\d+(?:\.(?:\d+|x))*)?)")

    for changelog in changelogs:
        # --- Impute Date ---
        # If the date field is missing, try to extract a date from the title.
        if not changelog.date:
            date_match = date_regex.search(changelog.title)
            if date_match:
                changelog.date = date_match.group(1)

        # --- Impute Version ---
        # If the version field is missing, first try to extract from the title.
        if not changelog.version:
            version_match = version_regex.search(changelog.title)
            if version_match:
                changelog.version = version_match.group(1)

        # If still missing, look for a version in the changes text.
        if not changelog.version:
            version_match = version_regex.search(changelog.changes)
            if version_match:
                changelog.version = version_match.group(1)

    return changelogs


@flow(log_prints=True)
def fetch_and_parse_cursor_changelog() -> list[ChangeLog]:
    """
    Fetches the raw HTML for the Cursor changelog page and parses it into a list of ChangeLog models.
    Sanity checks the output by printing the first two and last two ChangeLogs as JSON.
    Returns the list of ChangeLog models.
    """
    html = fetch_rendered(CURSOR_CHANGELOG_URL)

    changelogs = parse_changelog(html)

    print(f"Found {len(changelogs)} changelogs.")

    # assign index after reversing the list
    for i, changelog in enumerate(list(reversed(changelogs))):
        changelog.index = i

    changelogs = impute_changelog_missing_data(changelogs)

    # Print sanity checkers
    for changelog in changelogs[:2]:
        # Print the changelog model as JSON (Pydantic V2).
        print(changelog.model_dump_json(indent=2))
        print("\n")

    for changelog in changelogs[-2:]:
        # Print the changelog model as JSON (Pydantic V2).
        print(changelog.model_dump_json(indent=2))
        print("\n")

    return changelogs


if __name__ == "__main__":
    fetch_and_parse_cursor_changelog()
