# src/loaders/codeium/load_codeium_changelog.py

from src.utils.network import fetch_rendered, fetch
from src.loaders.models.models import ChangeLog, CodeAssistantCompany
from prefect import task, flow
from bs4 import BeautifulSoup

CODEIUM_CHANGELOG_URL = "https://codeium.com/changelog"


@task
def parse_changelog(html: str) -> list[ChangeLog]:
    """
    Parse the HTML from the Codeium changelog page into a list of ChangeLog models.

    The function loops over each version update which is inside a div with aria-label="changelog-layout",
    extracting the version, title, and changes text. The version and date are extracted using a regex,
    and the title is in an <h2> tag. The changes text is gathered by removing any containers that hold the
    version text from a copy of the article, and then using the cleaned-up article copy to get all remaining
    text.

    The function returns a list of ChangeLog models.
    """
    soup = BeautifulSoup(html, "html.parser")
    changelog_entries = []

    # Each changelog entry is contained in a div with aria-label="changelog-layout"
    containers = soup.find_all(attrs={"aria-label": "changelog-layout"})

    for container in containers:
        # --- Extract Version and Date from the header ---
        header = container.find("header", class_="mb-5 flex flex-col gap-2 md:hidden")
        if header:
            header_divs = header.find_all("div")
            if len(header_divs) >= 2:
                # Example header text: "v 1.4.3"
                version_text = header_divs[0].get_text(strip=True)
                # Remove the leading "v" if present
                version = version_text.lstrip("v").strip()
                date = header_divs[1].get_text(strip=True)
            else:
                version = ""
                date = ""
        else:
            version = ""
            date = ""

        # --- Extract Title and Changes from the article ---
        article = container.find("article")
        title = ""
        changes = ""
        if article:
            prose_div = article.find("div", class_=lambda x: x and "prose" in x)
            if prose_div:
                # Get all h2 tags inside the prose block
                h2_tags = prose_div.find_all("h2")
                # Heuristic: if two or more h2 tags exist, choose the second one as the title.
                if len(h2_tags) >= 2:
                    title_tag = h2_tags[1]
                elif h2_tags:
                    title_tag = h2_tags[0]
                else:
                    title_tag = None

                if title_tag:
                    title = title_tag.get_text(strip=True)
                    # For the changes, get all sibling elements after the chosen title
                    changes_parts = []
                    for sibling in title_tag.find_next_siblings():
                        text = sibling.get_text(separator="\n", strip=True)
                        if text:
                            changes_parts.append(text)
                    changes = "\n".join(changes_parts)
                else:
                    # Fallback if no h2 is found: use the entire prose text.
                    changes = prose_div.get_text(separator="\n", strip=True)

        changelog = ChangeLog(
            version=version,
            title=title,
            date=date,
            changes=f"{title}\n{changes}",
            company=CodeAssistantCompany.CODEIUM_ENTERPRISE,
        )
        changelog_entries.append(changelog)

    return changelog_entries


@flow(log_prints=True)
def fetch_and_parse_codeium_changelog() -> list[ChangeLog]:
    """
    Fetches the raw HTML from the Codeium changelog page, parses it into a list of ChangeLog models,
    assigns indices to each, and prints the first two and last two ChangeLogs as JSON for sanity checking.
    Returns the list of ChangeLog models.
    """
    html = fetch_rendered(CODEIUM_CHANGELOG_URL)

    changelogs = parse_changelog(html)

    # assign index after reversing the list
    for i, changelog in enumerate(list(reversed(changelogs))):
        changelog.index = i

    for changelog in changelogs:
        changelog.unique_id = f"{changelog.company.value}_{changelog.version}"

    # Print sanity checkers
    for changelog in changelogs[:2]:
        print(changelog.model_dump_json(indent=2))
        print("\n")

    return changelogs


if __name__ == "__main__":
    fetch_and_parse_codeium_changelog()
