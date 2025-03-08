import json
from requests_html import HTMLSession
from bs4 import BeautifulSoup


def main():
    """
    Example script to extract the title, datePublished, and content from a Codeium blog post.

    This script uses requests-html to fetch the page and execute JavaScript, then uses BeautifulSoup
    to parse the HTML and extract the desired elements.

    :return: None
    """
    url = "https://codeium.com/blog/amazon-codewhisperer-review"
    session = HTMLSession()
    r = session.get(url)

    # Render the page to execute JavaScript (adjust sleep as needed)
    r.html.render(sleep=10)

    # Get the fully rendered HTML
    rendered_html = r.html.html

    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(rendered_html, "html.parser")

    # Print all <h1> elements' text
    h1_elements = soup.find_all("h1")
    for h1 in h1_elements:
        print(h1.get_text(strip=True))

    # Extract datePublished from JSON-LD script tags
    scripts = soup.find_all("script", type="application/ld+json")
    date_published = None
    for script in scripts:
        try:
            data = json.loads(script.string)
        except (json.JSONDecodeError, TypeError):
            continue

        # Handle cases where data might be a list or a dictionary.
        if isinstance(data, dict):
            if "datePublished" in data:
                date_published = data["datePublished"]
                break
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and "datePublished" in item:
                    date_published = item["datePublished"]
                    break
            if date_published:
                break

    if date_published:
        print("Date Published:", date_published)
    else:
        print("datePublished not found.")

    content_container = soup.find("div", class_="prose")
    if content_container:
        # Option 1: Extract plain text (all paragraphs, headings, etc.)
        content_text = content_container.get_text(separator="\n", strip=True)
        print("Content Text:\n", content_text)

        # Option 2: Extract the inner HTML if you need the markup.
        content_html = content_container.decode_contents()
        print("Content HTML:\n", content_html)
    else:
        print("Content container not found.")


if __name__ == "__main__":
    main()
