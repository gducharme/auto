from __future__ import annotations

from bs4 import BeautifulSoup

from .automation.safari import SafariController
from .html_utils import extract_links_with_green_span


def fetch_dom(url: str = "https://chatgpt.com/codex") -> str:
    """Return the full DOM tree for ``url`` using Safari."""
    controller = SafariController()
    controller.open(url)
    return controller.run_js("document.documentElement.outerHTML")


def count_link_states(html: str) -> tuple[int, int]:
    """Return counts for merged and active links from ``html``."""
    soup = BeautifulSoup(html, "html.parser")
    merged = 0
    for a in soup.find_all("a", href=True):
        if not a.find("span", class_="text-green-500"):
            continue
        container_text = a.parent.get_text(" ", strip=True).lower()
        if "merged" in container_text:
            merged += 1
    active = len(extract_links_with_green_span(html))
    return merged, active
