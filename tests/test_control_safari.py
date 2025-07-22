from auto.cli import automation as tasks
from pathlib import Path
import json
import shutil


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


def test_control_safari(monkeypatch, capsys):
    controller = DummyController()
    monkeypatch.setattr(tasks, "SafariController", lambda: controller)
    monkeypatch.setattr(tasks, "fetch_dom_html", lambda url=None: "<html></html>")

    key_inputs = iter(["0", "6", "9"])  # open, fetch_dom, quit
    text_inputs = iter(
        [
            "demo_test",
            "https://example.com",
        ]
    )
    monkeypatch.setattr(tasks, "_read_key", lambda: next(key_inputs))
    monkeypatch.setattr("builtins.input", lambda _: next(text_inputs))

    tasks.control_safari()

    captured = capsys.readouterr()

    assert ("open", "https://example.com") in controller.calls

    test_dir = Path("tests/fixtures/demo_test")
    assert (test_dir / "1.html").exists()
    log = json.loads((test_dir / "commands.json").read_text())
    assert log[0] == ["open", "https://example.com"]
    assert log[1] == ["fetch_dom", str(test_dir / "1.html")]

    out = captured.out
    assert "Command log:" in out

    shutil.rmtree(test_dir)


def test_control_safari_run_js_file(monkeypatch, tmp_path):
    controller = DummyController()
    monkeypatch.setattr(tasks, "SafariController", lambda: controller)
    js_path = tmp_path / "helper.js"
    js_code = "console.log('hello');"
    js_path.write_text(js_code)

    key_inputs = iter(["4", "9"])  # run_js_file, quit
    text_inputs = iter(
        [
            "demo_js",
            str(js_path),
        ]
    )
    monkeypatch.setattr(tasks, "_read_key", lambda: next(key_inputs))
    monkeypatch.setattr("builtins.input", lambda _: next(text_inputs))

    tasks.control_safari()

    assert ("run_js", js_code) in controller.calls
    shutil.rmtree(Path("tests/fixtures/demo_js"))


def test_control_safari_run_applescript_file(monkeypatch, tmp_path):
    controller = DummyController()
    monkeypatch.setattr(tasks, "SafariController", lambda: controller)

    script_path = tmp_path / "helper.scpt"
    script_path.write_text('say "hello"')

    calls = []

    def fake_run(cmd, capture_output=True, text=True):
        calls.append(cmd)
        from subprocess import CompletedProcess

        return CompletedProcess(cmd, 0, stdout="OK", stderr="")

    monkeypatch.setattr(tasks.subprocess, "run", fake_run)

    key_inputs = iter(["5", "9"])  # run_applescript_file, quit
    text_inputs = iter(
        [
            "demo_scpt",
            str(script_path),
        ]
    )
    monkeypatch.setattr(tasks, "_read_key", lambda: next(key_inputs))
    monkeypatch.setattr("builtins.input", lambda _: next(text_inputs))

    tasks.control_safari()

    assert calls == [["osascript", str(script_path)]]
    shutil.rmtree(Path("tests/fixtures/demo_scpt"))


def test_control_safari_llm_query(monkeypatch):
    controller = DummyController()
    monkeypatch.setattr(tasks, "SafariController", lambda: controller)
    monkeypatch.setattr(tasks, "query_llm", lambda prompt: "pong")

    key_inputs = iter(["8", "9"])  # llm_query, quit
    text_inputs = iter(
        [
            "demo_llm",
            "ping?",
        ]
    )
    monkeypatch.setattr(tasks, "_read_key", lambda: next(key_inputs))
    monkeypatch.setattr("builtins.input", lambda _: next(text_inputs))

    tasks.control_safari()

    test_dir = Path("tests/fixtures/demo_llm")
    log = json.loads((test_dir / "commands.json").read_text())
    assert log == [["llm_query", "ping?", "pong"]]
    shutil.rmtree(test_dir)


def test_control_safari_abort(monkeypatch):
    controller = DummyController()
    monkeypatch.setattr(tasks, "SafariController", lambda: controller)
    monkeypatch.setattr(tasks, "fetch_dom_html", lambda url=None: "<html></html>")

    key_inputs = iter(["a"])  # abort
    text_inputs = iter([
        "demo_abort",
    ])
    monkeypatch.setattr(tasks, "_read_key", lambda: next(key_inputs))
    monkeypatch.setattr("builtins.input", lambda _: next(text_inputs))

    tasks.control_safari()

    test_dir = Path("tests/fixtures/demo_abort")
    assert not test_dir.exists()
