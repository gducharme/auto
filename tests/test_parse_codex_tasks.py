import pathlib
from auto.html_utils import parse_codex_tasks


def test_parse_codex_tasks():
    html = pathlib.Path("tests/fixtures/dom.html").read_text()
    tasks = parse_codex_tasks(html)
    assert len(tasks) == 6
    statuses = [t["status"] for t in tasks]
    assert statuses.count("Merged") == 2
    assert statuses.count("Open") == 1
    assert sum(1 for t in tasks if not t["code"]) == 3
