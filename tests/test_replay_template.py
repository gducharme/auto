import shutil
from pathlib import Path

from auto.cli import automation as tasks

class DummyController:
    def __init__(self):
        self.calls = []

    def open(self, url):
        self.calls.append(("open", url))
        return "OK"

    def click(self, selector):
        self.calls.append(("click", selector))
        return "OK"

    def fill(self, selector, text):
        self.calls.append(("fill", selector, text))
        return "OK"

    def run_js(self, code):
        self.calls.append(("run_js", code))
        return "OK"

    def close_tab(self):
        self.calls.append(("close_tab",))
        return "OK"

def test_replay_template_variable(monkeypatch, tmp_path):
    src = Path("tests/fixtures/open_var")
    dst = tmp_path / "tests" / "fixtures" / "open_var"
    shutil.copytree(src, dst)
    monkeypatch.chdir(tmp_path)

    controller = DummyController()
    monkeypatch.setattr(tasks, "SafariController", lambda: controller)
    monkeypatch.setenv("SKIP_SLOW_PRINT", "1")

    url = "https://example.com/post1"
    inputs = iter(["n"])  # do not continue recording
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    tasks.replay("open_var", post_id=url)

    assert ("open", url) in controller.calls
