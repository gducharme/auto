from __future__ import annotations

from typing import List

from bs4 import BeautifulSoup
import re


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


def parse_codex_tasks(html: str) -> List[dict]:
    """Return task info dictionaries extracted from Codex HTML.

    Each returned dict contains ``text`` with the row text, ``status`` which is
    either ``"Merged"`` or ``"Open"`` (or ``None`` if neither is present), and a
    boolean ``code`` flag indicating whether the row includes code changes.
    """
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("div.task-row-container")
    tasks: List[dict] = []
    for row in rows:
        text = row.get_text(" ", strip=True)
        if "Merged" in text:
            status = "Merged"
        elif "Open" in text:
            status = "Open"
        else:
            status = None
        code = bool(re.search(r"\+[0-9]+", text))
        tasks.append({"text": text, "status": status, "code": code})
    return tasks


def extract_task_row_html(html: str) -> str:
    """Return HTML containing only ``task-row-container`` elements.

    The returned string preserves the nested structure of each row so tests can
    operate on a smaller snapshot without losing DOM complexity.
    """
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("div.task-row-container")
    parts = ["<html>", "<body>"]
    for row in rows:
        parts.append(row.prettify())
    parts.extend(["</body>", "</html>"])
    return "\n".join(parts)
