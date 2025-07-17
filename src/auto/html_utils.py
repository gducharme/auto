from __future__ import annotations

from typing import List

from bs4 import BeautifulSoup


def extract_links_with_green_span(html: str) -> List[str]:
    """Return hrefs for anchors containing a ``text-green-500`` span."""
    soup = BeautifulSoup(html, "html.parser")
    links: List[str] = []
    for a in soup.find_all("a", href=True):
        if a.find("span", class_="text-green-500"):
            links.append(a["href"])
    return links
