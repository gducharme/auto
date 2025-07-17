from __future__ import annotations

from typing import List

from bs4 import BeautifulSoup


def extract_links_with_green_span(html: str) -> List[str]:
    """Return hrefs for anchors containing a ``text-green-500`` span.

    Links are ignored when the surrounding element also includes the word
    ``Merged``. This matches the structure of GitHub's pull request list where
    merged PRs show a ``Merged`` badge next to the link.
    """
    soup = BeautifulSoup(html, "html.parser")
    links: List[str] = []
    for a in soup.find_all("a", href=True):
        if not a.find("span", class_="text-green-500"):
            continue

        container_text = a.parent.get_text(" ", strip=True).lower()
        if "merged" in container_text:
            continue

        links.append(a["href"])
    return links
