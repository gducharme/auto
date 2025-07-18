import json

from auto.automation import workflow


class DummyController:
    def __init__(self):
        self.opened = []
        self.js = []

    def open(self, url):
        self.opened.append(url)
        return "OK"

    def run_js(self, code):
        self.js.append(code)
        return "OK"


def test_workflow_progress(monkeypatch, tmp_path):
    monkeypatch.setattr(workflow, "SafariController", DummyController)
    monkeypatch.setattr(workflow, "fetch_dom", lambda: "<html></html>")
    monkeypatch.setattr(
        workflow, "parse_codex_tasks", lambda html: [{"status": "Open"}]
    )
    monkeypatch.setattr(
        workflow,
        "extract_links_with_green_span",
        lambda html: ["https://github.com/pull/1"],
    )

    monkeypatch.setattr(workflow, "WORKFLOW_DIR", tmp_path)

    # first run creates the state file and fetches DOM
    state = workflow.execute("test")
    assert state == workflow.WorkflowState.PARSE_TASKS
    data = json.loads((tmp_path / "test.json").read_text())
    assert data["state"] == "PARSE_TASKS"
    assert "dom" in data

    # second run parses tasks
    state = workflow.execute("test")
    assert state == workflow.WorkflowState.OPEN_PR
    data = json.loads((tmp_path / "test.json").read_text())
    assert data["state"] == "OPEN_PR"
    assert data["pr_url"] == "https://github.com/pull/1"

    # third run opens PR
    state = workflow.execute("test")
    assert state == workflow.WorkflowState.MERGE_PR
    data = json.loads((tmp_path / "test.json").read_text())
    assert data["state"] == "MERGE_PR"

    # fourth run merges and cycles back to fetch
    state = workflow.execute("test")
    assert state == workflow.WorkflowState.FETCH_DOM
    data = json.loads((tmp_path / "test.json").read_text())
    assert data["state"] == "FETCH_DOM"
