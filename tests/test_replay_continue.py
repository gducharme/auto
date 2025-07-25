import json
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


def test_replay_continue(monkeypatch, tmp_path):
    src = Path("tests/fixtures/facebook")
    dst = tmp_path / "tests" / "fixtures" / "facebook"
    shutil.copytree(src, dst)
    monkeypatch.chdir(tmp_path)

    controller = DummyController()
    monkeypatch.setattr(tasks, "SafariController", lambda: controller)
    monkeypatch.setattr(tasks, "fetch_dom_html", lambda url=None: "<html></html>")
    monkeypatch.setenv("SKIP_SLOW_PRINT", "1")

    key_inputs = iter(["6", "b"])  # fetch_dom then quit
    monkeypatch.setattr(tasks, "_read_key", lambda: next(key_inputs))
    inputs = iter(["y"])  # continue recording
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    tasks.replay("facebook")

    commands = json.loads((dst / "commands.json").read_text())
    assert (dst / "3.html").exists()
    assert len(commands) == 13
    assert commands[-1] == ["fetch_dom", "tests/fixtures/facebook/4.html"]


def test_replay_initial_vars(monkeypatch, tmp_path):
    src = Path("tests/fixtures/facebook")
    dst = tmp_path / "tests" / "fixtures" / "facebook"
    shutil.copytree(src, dst)
    monkeypatch.chdir(tmp_path)

    controller = DummyController()
    monkeypatch.setattr(tasks, "SafariController", lambda: controller)
    monkeypatch.setattr(tasks, "fetch_dom_html", lambda url=None: "<html></html>")
    monkeypatch.setenv("SKIP_SLOW_PRINT", "1")

    recorded = {}

    def fake_menu(controller, test_dir, commands, step, variables):
        recorded.update(variables)
        return commands, step, True

    monkeypatch.setattr(tasks, "_interactive_menu", fake_menu)

    inputs = iter(["y"])  # continue recording
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    tasks.replay("facebook", post_id="42", network="testnet")

    assert recorded["post_id"] == "42"
    assert recorded["network"] == "testnet"
    assert recorded["name"] == "facebook"
