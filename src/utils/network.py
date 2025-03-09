from requests_html import HTMLSession
import httpx

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; BlogLoader/1.0; +https://example.com)"
}


def fetch(url: str) -> str:
    """
    Fetches the raw HTML (or XML) content for a given URL using httpx.
    Raises an error if the response status is not 200.
    """
    with httpx.Client(headers=HEADERS, timeout=30) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.text


def fetch_rendered(url: str, sleep=3) -> str:
    """
    Fetches the rendered HTML content for a given URL using requests_html.
    Uses HTMLSession to execute JavaScript on the page, which is necessary for
    some websites to render their content. Adjust the sleep parameter as
    needed to ensure the JavaScript has enough time to execute.

    :param url: The URL to fetch
    :param sleep: The number of seconds to wait for JavaScript to execute
    :return: The fully rendered HTML content
    """
    session = HTMLSession()
    r = session.get(url)

    # Render the page to execute JavaScript (adjust sleep as needed)
    r.html.render(sleep=sleep)

    # Get the fully rendered HTML
    rendered_html = r.html.html

    return rendered_html
